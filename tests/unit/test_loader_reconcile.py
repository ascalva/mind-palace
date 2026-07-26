"""finding-0199's three reproduced phases, as tests (bp-107).

The memory ceiling (non-negotiable #8) used to be checked against a belief nobody reconciled:
`TwoSlotLoader._resident` started EMPTY on every construction while Ollama — a separate process
that outlives the supervisor — kept holding models. All three consequences were REPRODUCED LIVE on
2026-07-25 (`dn-local-model-runtime` §2.1 B), so these are not hypotheses:

  (i)   false-absent    — a fresh loader believed 1 model / 6.6 GB while `ollama ps` held 2.
  (ii)  guard-pass on a real breach — `_check_ceiling` passed 23.0 <= 24.0 while the TRUE
        prospective was 25.7 GB, because the eviction loop iterated an empty dict and therefore
        never told Ollama to drop anything.
  (iii) false-resident  — a 0.0 ms stale early-return skipped a load that was really needed after
        Ollama's own 30-minute keep-alive timer had evicted the worker.

Each phase below is asserted twice over: the loader's books, AND what the fake server is really
holding afterwards. The second is the one that matters — the defect was never that the arithmetic
was wrong, it was that the arithmetic was about the wrong world.

This module is also the home of `FakeOllama`, the stateful residency stand-in the other five
loader-touching test files now construct with. `tests/fixtures/` would be its natural home but is
outside bp-107's `write_scope`; importing a helper from a sibling test module follows the existing
precedent of `tests/quality/test_diffusion_clusterer.py` -> `tests.quality.test_dreamer_quality`.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import cast

import pytest

from config.loader import Config, load_config
from core.models.loader import _MEASURED_NON_REGISTRY_GB, ReconcileReport, TwoSlotLoader
from core.models.ollama_client import OllamaClient, OllamaError
from core.models.registry import MemoryCeilingError, Registry

PINNED = "qwen3.5:2b"        # 2.7 GB declared, pinned (keep_alive=-1, never timer-evicted)
ROUTINE = "qwen3.5:9b"       # 6.6 GB declared
SYNTHESIS = "qwen3.6:27b"    # 17.0 GB declared
STRETCH = "qwen3.6:35b-a3b"  # 23.0 GB declared, evicts_pinned
EMBEDDER = "qwen3-embedding:4b"  # 10.0 GB MEASURED @ ctx 40960, not in the registry at all
FOREIGN = "some-other-model:7b"  # no registry entry, no measurement -> uncostable


class FakeOllama:
    """A stateful stand-in for the residency surface of `OllamaClient` (`ps`/`load`/`unload`).

    Stateful on purpose. A stub that only answered `ps()` from a frozen list could not show the
    thing bp-107 actually fixes: that the evictions the ceiling arithmetic *assumes* now really
    happen. `held` is the ground truth the assertions care about.
    """

    def __init__(self, resident: Iterable[str] = (), *,
                 ps_error: BaseException | None = None) -> None:
        self.held: list[str] = list(resident)
        self.loads: list[tuple[str, int | None, str | int]] = []
        self.unloads: list[str] = []
        self.ps_calls: int = 0
        self._ps_error = ps_error

    # --- the residency surface the loader talks to ---
    def ps(self) -> list[str]:
        self.ps_calls += 1
        if self._ps_error is not None:
            raise self._ps_error
        return list(self.held)

    def load(self, model: str, *, num_ctx: int | None = None,
             keep_alive: str | int = "30m") -> None:
        self.loads.append((model, num_ctx, keep_alive))
        if model not in self.held:
            self.held.append(model)

    def unload(self, model: str) -> None:
        self.unloads.append(model)
        if model in self.held:
            self.held.remove(model)

    # --- test-side manipulation, deliberately NOT part of the client surface ---
    def timer_evict(self, model: str) -> None:
        """Ollama's own keep-alive timer dropping a worker, with no notification to the palace.
        Distinct from `unload` so a test can tell "we asked" from "it just happened"."""
        self.held.remove(model)

    def loaded_names(self) -> list[str]:
        return [name for name, _, _ in self.loads]


def loader_for(cfg: Config | None = None, client: FakeOllama | None = None) -> TwoSlotLoader:
    """A hermetic `TwoSlotLoader`. Hermetic matters now: the loader probes `ps()` at construction,
    so a loader built on a real `OllamaClient` would read whatever the DEVELOPER's Ollama happens
    to be holding — green in CI, differently-green on the owner's machine. The five carried test
    files switched to this for exactly that reason, without losing an assertion."""
    cfg = cfg or load_config()
    client = client if client is not None else FakeOllama()
    return TwoSlotLoader(
        config=cfg, client=cast("OllamaClient", client), registry=Registry(cfg)
    )


def held_gb(cfg: Config, held: Iterable[str]) -> float:
    """What the fake server is REALLY holding, in GB — registry constants plus the measured
    non-registry carve-out. This is the number the guard exists to bound."""
    cost = {m.name: m.resident_gb for m in cfg.models}
    cost |= _MEASURED_NON_REGISTRY_GB
    return sum(cost[n] for n in held)


# --- Item 1: reconcile() measures, and says what it could not cost -----------------------------

def test_reconcile_costs_known_names_and_reports_the_uncostable_rest() -> None:
    cfg = load_config()
    fake = FakeOllama([PINNED, EMBEDDER, FOREIGN])
    ld = loader_for(cfg, fake)

    report = ld.last_reconcile
    assert report.reconciled is True
    # 2.7 (registry) + 10.0 (measured carve-out); FOREIGN contributes nothing but is NAMED.
    assert report.known_gb == pytest.approx(2.7 + 10.0)
    assert report.unknown == (FOREIGN,)
    assert report.complete is False, "a name we could not cost must not read as full accounting"
    # The embedder is costed but is NOT a registry model: it never enters the two-slot algebra.
    assert ld.resident_models() == [PINNED]
    assert ld.external_resident_gb() == pytest.approx(10.0)
    assert ld.uncostable_resident() == (FOREIGN,)


def test_reconcile_of_an_empty_server_is_the_one_complete_case() -> None:
    ld = loader_for(client=FakeOllama([]))
    report = ld.last_reconcile
    assert (report.reconciled, report.known_gb, report.unknown) == (True, 0.0, ())
    assert report.complete is True
    assert ld.resident_models() == []


def test_reconcile_never_raises_and_a_failed_probe_reports_unreconciled() -> None:
    fake = FakeOllama([PINNED], ps_error=OllamaError("connection refused"))
    ld = loader_for(client=fake)          # construction must survive an unreachable Ollama
    report = ld.reconcile()               # and an explicit call must not raise either
    assert report.reconciled is False
    assert report.complete is False, "unreconciled can never be complete"
    assert ld.resident_models() == [], "a failed probe is not evidence about residency"


def test_complete_is_structurally_unable_to_claim_more_than_it_knows() -> None:
    """Item 1's falsifier, closed by construction rather than by spot checks."""
    for reconciled in (True, False):
        for unknown in ((), (FOREIGN,), (FOREIGN, EMBEDDER)):
            r = ReconcileReport.measure(reconciled=reconciled, known_gb=1.0, unknown=unknown)
            assert r.complete == (reconciled and not unknown)
            if r.unknown:
                assert r.complete is False


# --- Item 2, phase (i): false-absent ------------------------------------------------------------

def test_phase_i_a_fresh_loader_sees_what_ollama_really_holds() -> None:
    """Reproduced: the loader believed 1 model / 6.6 GB while `ollama ps` held 2."""
    cfg = load_config()
    fake = FakeOllama([PINNED, ROUTINE])          # the staged pre-crash state
    ld = loader_for(cfg, fake)                    # a NEW supervisor's loader

    assert set(ld.resident_models()) == {PINNED, ROUTINE}, "the books show 2, not 0"
    assert ld.resident_gb() == pytest.approx(2.7 + 6.6)
    assert fake.ps_calls == 1, "measured at construction, before anything asks it to load"


# --- Item 2, phase (ii): the guard-pass on a real breach ----------------------------------------

def test_phase_ii_the_reproduced_breach_state_is_no_longer_reachable() -> None:
    """The measured case: fresh loader, Ollama holding pinned(2.7) + routine(6.6), then a stretch
    load. The old guard summed 23.0 <= 24.0 and passed, while the TRUE post-state was 25.7 GB
    (stretch + the really-resident pinned) — because the eviction loop iterated an empty dict and
    so never targeted the real 2b.

    It cannot happen now, and note WHY: not because the arithmetic changed, but because the
    evictions the arithmetic assumes are now actually issued. The ceiling's prediction became
    true instead of hopeful.
    """
    cfg = load_config()
    fake = FakeOllama([PINNED, ROUTINE])
    ld = loader_for(cfg, fake)

    ld.ensure(STRETCH)                                    # warm: real client calls on the fake

    assert set(fake.unloads) == {PINNED, ROUTINE}, "the real 2b and 9b were told to go"
    assert fake.held == [STRETCH], "the server really holds only the stretch model"
    assert held_gb(cfg, fake.held) == pytest.approx(23.0)
    # The reproduced breach, spelled out: 23.0 + 2.7 = 25.7 > 24.0 is what USED to be left behind.
    assert held_gb(cfg, fake.held) <= cfg.resources.usable_ram_gb
    assert 23.0 + 2.7 > cfg.resources.usable_ram_gb, "the old outcome would have breached"


def test_phase_ii_the_guard_now_refuses_a_breach_it_used_to_admit() -> None:
    """The same defect where the two-slot algebra CANNOT evict the other consumer: the embedder
    is not a registry model, so no eviction rule reaches it and its cost must be charged.

      old: prospective = {27b} = 17.0 <= 24.0            -> ADMITTED, real outcome 29.7 GB
      new: prospective = {2b, 27b} = 19.7, + 10.0 measured = 29.7 > 24.0 -> REFUSED

    This is finding-0174's arithmetic made visible (10.0 GB @ ctx 40960, not the 2.5 GB it
    assumed). It is not fixed here — the declared `resident_gb` constants are untouched — but it
    is no longer invisible to the guard.
    """
    cfg = load_config()
    fake = FakeOllama([PINNED, EMBEDDER])
    ld = loader_for(cfg, fake)

    with pytest.raises(MemoryCeilingError) as exc:
        ld.ensure_tier("synthesis")

    assert "29.7" in str(exc.value) and "24.0" in str(exc.value)
    # Refused, never half-applied: nothing loaded, nothing unloaded, books untouched.
    assert fake.loads == [] and fake.unloads == []
    assert fake.held == [PINNED, EMBEDDER]
    assert ld.resident_models() == [PINNED]
    # ...and the state the old guard would have admitted really was over the ceiling.
    assert held_gb(cfg, [PINNED, EMBEDDER, SYNTHESIS]) == pytest.approx(29.7)


def test_the_ceiling_error_stays_compatible_with_the_supervisor_defer_path() -> None:
    """`Supervisor.tick` catches `MemoryCeilingError` and defers with `f"ceiling: {e}"`
    (`scheduler/supervisor.py:72-74`). Type and message shape must survive bp-107."""
    fake = FakeOllama([PINNED, EMBEDDER])
    ld = loader_for(client=fake)
    with pytest.raises(MemoryCeilingError) as exc:
        ld.ensure_tier("synthesis")
    assert isinstance(exc.value, RuntimeError)
    assert f"ceiling: {exc.value}".startswith("ceiling: would use")


# --- Item 2, phase (iii): false-resident --------------------------------------------------------

def test_phase_iii_an_externally_evicted_model_is_no_longer_early_returned() -> None:
    """Reproduced: `ensure` returned in 0.0 ms on a stale belief, skipping a needed load."""
    cfg = load_config()
    fake = FakeOllama([PINNED, ROUTINE])
    ld = loader_for(cfg, fake)
    assert ROUTINE in ld.resident_models()      # believed resident, and it really was

    fake.timer_evict(ROUTINE)                   # the 30-minute keep-alive timer, unannounced
    ld.ensure(ROUTINE)

    assert fake.loaded_names() == [ROUTINE], "the needed load actually happened"
    assert ROUTINE in fake.held
    assert ROUTINE in ld.resident_models()


def test_idempotence_survives_and_is_now_grounded_in_measurement() -> None:
    """The early-return did not die, it stopped being stale: a genuinely resident model is still
    a no-op, and now that claim is measured rather than remembered."""
    fake = FakeOllama([PINNED])
    ld = loader_for(client=fake)
    before = ld.resident_models()
    ld.ensure_pinned()
    assert ld.resident_models() == before
    assert fake.loads == [], "no redundant load for a really-resident model"


# --- Item 2: the fail-closed rule, and the carve-out that keeps it from bricking the daemon -----

def test_an_uncostable_resident_name_fails_non_pinned_loads_closed() -> None:
    cfg = load_config()
    fake = FakeOllama([FOREIGN])
    ld = loader_for(cfg, fake)
    assert ld.uncostable_resident() == (FOREIGN,)

    with pytest.raises(MemoryCeilingError) as exc:
        ld.ensure_tier("routine")
    assert FOREIGN in str(exc.value) and "partial accounting" in str(exc.value)
    assert fake.loads == [] and fake.held == [FOREIGN], "refused, not half-applied"


def test_the_pinned_model_is_always_admitted_by_the_fail_closed_rule() -> None:
    """bp-107 §10's first stop condition: refusing the router converts a memory guard into an
    availability outage. Uncostable residency must never do that."""
    fake = FakeOllama([FOREIGN])
    ld = loader_for(client=fake)
    ld.ensure_pinned()
    assert PINNED in fake.held
    assert fake.loaded_names() == [PINNED]
    assert PINNED in ld.resident_models()


def test_the_embedder_carve_out_keeps_worker_loads_available() -> None:
    """Without the carve-out the embedder — permanently absent from the registry — would be an
    unknown name forever, and every system that has ever embedded would refuse every worker load.
    Costed, it is a budget charge instead of a veto."""
    cfg = load_config()
    fake = FakeOllama([PINNED, EMBEDDER])
    ld = loader_for(cfg, fake)
    assert ld.uncostable_resident() == (), "the configured embedder is costed, not unknown"

    ld.ensure_tier("routine")                             # 2.7 + 6.6 + 10.0 = 19.3 <= 24.0
    assert ROUTINE in fake.held
    assert held_gb(cfg, fake.held) == pytest.approx(19.3)


def test_a_failed_probe_degrades_instead_of_refusing() -> None:
    """Parked decision: an unreachable Ollama already fails every load, so refusing adds nothing
    but a brick risk. Startup must survive it."""
    fake = FakeOllama(ps_error=OllamaError("connection refused"))
    ld = loader_for(client=fake)
    assert ld.last_reconcile.reconciled is False

    ld.ensure_tier("routine")                # no refusal: degraded to today's belief
    assert ROUTINE in fake.loaded_names()


def test_an_unmeasured_embedder_is_named_not_silently_costed_at_zero() -> None:
    """If the configured embedder has no measurement, honesty beats convenience: it is reported
    in `unknown` (fail-closed) rather than costed at 0.0, which is the finding-0174 failure mode
    re-created one level down. Re-entry for the registry fix is recorded in bp-107 §11."""
    cfg = load_config()
    assert cfg.embedding.model in _MEASURED_NON_REGISTRY_GB, "today's embedder IS measured"
    fake = FakeOllama(["some-future-embedder:8b"])
    ld = loader_for(cfg, fake)
    assert ld.uncostable_resident() == ("some-future-embedder:8b",)
    assert ld.external_resident_gb() == 0.0
    assert ld.last_reconcile.complete is False
