"""Supervisor integration (BUILD-SPEC §13; roadmap §7), all deterministic (warm=False, no
Ollama): tier grouping minimizes swaps; the foreground check gates heavy tiers; the RAM
ceiling defers rather than crashes; a handler failure is isolated; checkpointed jobs yield
and resume at job boundaries.

bp-110 adds the DISPATCH SEAM at the bottom of the file. Everything above it is untouched, and
that is the point: `worker_mode` defaults to `inproc` and the new `Supervisor` fields are
additive and defaulted, so every test written before the seam existed must still pass with no
edit. If one of them ever needs editing to stay green, the change was not additive and the
"no behaviour change at landing" claim is false (bp-110 §7 Item 3's falsifier)."""

import dataclasses
import inspect
from collections.abc import Callable

import pytest

from config.loader import load_config
from scheduler.presence import Presence
from scheduler.queue import DEFERRED, DONE, FAILED, QUEUED, JobQueue
from scheduler.supervisor import HEAVY_TIERS, SUBPROCESS, Supervisor
from scheduler.worker import SELFTEST_ANSWER_KIND, Batch
from tests.fixtures.power import on_ac, on_battery, unreadable
from tests.fixtures.secrets import fake_vault
from tests.unit.test_loader_reconcile import loader_for


def _loader(cfg=None):
    # bp-107: hermetic `ps()`. The loader measures residency at construction (finding-0199), so a
    # real client would make these tests read the developer's live Ollama. Assertions unchanged.
    return loader_for(cfg)


def _present(active: bool) -> Presence:
    # idle 0s => owner present; idle huge => idle. Threshold is 300s.
    return Presence(idle_probe=lambda: 0.0 if active else 10_000.0)


def _supervisor(tmp_path, handlers, *, active=False, loader=None, secrets=None, power=None,
                queue=None):
    return Supervisor(
        queue=queue or JobQueue(tmp_path / "q.db"),
        loader=loader or _loader(),
        handlers=handlers,
        presence=_present(active),
        # bp-154: `Supervisor.power` fails CLOSED by default (an unreadable battery reads as
        # discharging), so a default-constructed supervisor here would decide heavy-tier dispatch
        # from whatever the host's battery is doing — or, on CI, from the absence of `pmset`.
        # Injecting an on-AC sensor restores each test's intended subject, exactly as `_present`
        # already does for HID idle time. The power tests at the bottom of the file inject their
        # own; injecting `on_ac()` into one of THOSE would hide the feature (Item 5's falsifier).
        power=power or on_ac(),
        warm=False,
        secrets=secrets,
    )


def test_runs_jobs_in_order_and_records_results(tmp_path):
    order: list[int] = []

    def _record(j):
        order.append(j.id)
        return "done"

    sup = _supervisor(tmp_path, {"x": _record})
    sup.loader.ensure_pinned(warm=False)
    a = sup.queue.enqueue("x", "routine", 16384)
    b = sup.queue.enqueue("x", "routine", 16384)
    assert sup.run() == 2
    assert order == [a.id, b.id]
    assert sup.queue.get(a.id).state == DONE and sup.queue.get(a.id).result == "done"


def test_groups_same_tier_to_minimize_swaps(tmp_path):
    sup = _supervisor(tmp_path, {"k": lambda j: None}, active=False)
    sup.loader.ensure_pinned(warm=False)
    sup.queue.enqueue("k", "routine", 16384)
    sup.queue.enqueue("k", "synthesis", 32768)
    sup.queue.enqueue("k", "routine", 16384)
    sup.run()
    # The two routine jobs run back-to-back; only one swap (to synthesis) is incurred.
    assert sup.swaps == 1


def test_foreground_gates_heavy_tiers(tmp_path):
    ran = []
    sup = _supervisor(tmp_path, {"k": lambda j: ran.append(j.tier)}, active=True)
    sup.loader.ensure_pinned(warm=False)
    sup.queue.enqueue("k", "routine", 16384)
    syn = sup.queue.enqueue("k", "synthesis", 32768)
    assert sup.run() == 1
    assert ran == ["routine"]                          # synthesis gated while present
    assert sup.queue.get(syn.id).state == QUEUED       # left for a trough


def test_ceiling_breach_defers_job(tmp_path):
    cfg = dataclasses.replace(
        load_config(), resources=dataclasses.replace(load_config().resources, usable_ram_gb=5.0)
    )
    ld = _loader(cfg)
    ld.ensure_pinned(warm=False)                       # 2.7 GB of a 5 GB budget
    sup = Supervisor(queue=JobQueue(tmp_path / "q.db"), loader=ld,
                     handlers={"k": lambda j: None}, presence=_present(False), power=on_ac(),
                     warm=False)
    j = sup.queue.enqueue("k", "synthesis", 32768)     # 2.7 + 17 > 5 -> refused
    sup.run()
    deferred = sup.queue.get(j.id)
    assert deferred.state == DEFERRED
    assert deferred.error is not None and "ceiling" in deferred.error


def test_handler_exception_fails_job_not_loop(tmp_path):
    ran = []

    def boom(_j):
        raise ValueError("kaboom")

    sup = _supervisor(tmp_path, {"boom": boom, "ok": lambda j: ran.append(j.id)})
    sup.loader.ensure_pinned(warm=False)
    bad = sup.queue.enqueue("boom", "routine", 16384)
    good = sup.queue.enqueue("ok", "routine", 16384)
    assert sup.run() == 2                               # the loop survived the failure
    assert sup.queue.get(bad.id).state == FAILED
    assert sup.queue.get(good.id).state == DONE and ran == [good.id]


def test_checkpointed_job_yields_and_resumes(tmp_path):
    calls: list[object] = []
    handlers: dict[str, Callable[..., str | None]] = {}
    sup = _supervisor(tmp_path, handlers, active=False)

    def stepper(j):
        calls.append(j.checkpoint)
        if j.checkpoint is None:
            sup.queue.checkpoint(j.id, "step-2")        # yield at the boundary
            return None
        return "finished"

    handlers["dream"] = stepper
    sup.loader.ensure_pinned(warm=False)
    j = sup.queue.enqueue("dream", "synthesis", 32768)
    sup.run()
    assert calls == [None, "step-2"]
    assert sup.queue.get(j.id).state == DONE and sup.queue.get(j.id).result == "finished"


def test_mint_token_returns_a_token_scoped_to_the_role(tmp_path):
    vault = fake_vault(**{"oura-daily-aggregates": "42 steps"})
    sup = _supervisor(tmp_path, {}, secrets=vault)
    minted = sup.mint_token("dreamer", ttl="5m")
    assert vault.minted == [("dreamer", "5m")]
    assert vault.read_secret("oura-daily-aggregates", minted.token) == "42 steps"
    # The accessor is the audit handle, minted alongside, and resolves back to the role.
    assert vault.role_for_accessor(minted.accessor) == "dreamer"


def test_mint_token_without_a_wired_backend_raises(tmp_path):
    sup = _supervisor(tmp_path, {})
    with pytest.raises(RuntimeError):
        sup.mint_token("dreamer")


# ==============================================================================================
# bp-110 Item 3 — the dispatch seam, behind `worker_mode`
# ==============================================================================================


def _answer(query: str) -> str:
    """The one place the expected answer text is written, so the parallel-run proof compares two
    dispatch paths rather than two copies of a string."""
    return f"answer({query})"


def test_the_same_job_lands_the_same_rows_in_BOTH_dispatch_modes(tmp_path):
    """⚑ Item 3's acceptance: THE PARALLEL-RUN PROOF.

    The same job, with `ambassador_task`'s shape — payload `{"query": …}`, pure compute, returns
    text, writes nothing (`dn-supervision-and-liveness` §2.3: "already exactly the target shape")
    — is run once `inproc` and once `subprocess`, and the rows that reach the landing sink must be
    identical. Both paths funnel through the SAME sink, so this compares dispatch, not two
    hand-written expectations.

    ⚑ On the kind: the plan names the production `ambassador_task` handler as the proof lane. Its
    compute half cannot move in THIS plan — `core/librarian/librarian.py:33,36` imports `RawStore`
    and `VectorStore` at module level, which reds Item 5's tier-4 ratchet, and both that file and
    `scheduler/interface.py` are outside bp-110's write_scope (§5: "owns the seam and NO lane").
    Moving them would be the finding-0191 failure repeated inside the plan written to prevent it.
    So the proof runs on a bring-up kind carrying that exact shape; finding-0227 records the
    mechanism and hands the lane migration to bp-113/bp-114.
    """
    query = "what did I conclude about supervision"
    landed_inproc: list[dict[str, object]] = []
    landed_subprocess: list[dict[str, object]] = []

    def inproc_handler(job):
        text = _answer(job.payload["query"])
        landed_inproc.append({"text": text})           # lands in-process, as today
        return text

    def lander(job, batch: Batch) -> None:
        landed_subprocess.extend(batch.rows)           # lands in the SUPERVISOR — single-writer

    def unused_compute(job, ctx):                      # the worker runs its own registered half
        raise AssertionError("the compute half must run in the WORKER, not here")
        yield  # pragma: no cover

    # --- mode 1: inproc (today's path, the default) ---
    a = _supervisor(tmp_path / "inproc", {SELFTEST_ANSWER_KIND: inproc_handler})
    a.loader.ensure_pinned(warm=False)
    ja = a.queue.enqueue(SELFTEST_ANSWER_KIND, "routine", 16384, payload={"query": query})
    assert a.run() == 1
    assert a.queue.get(ja.id).state == DONE

    # --- mode 2: subprocess (the seam) ---
    b = _supervisor(tmp_path / "sub", {})
    b.worker_mode = SUBPROCESS
    b.compute[SELFTEST_ANSWER_KIND] = (unused_compute, lander)
    b.loader.ensure_pinned(warm=False)
    jb = b.queue.enqueue(SELFTEST_ANSWER_KIND, "routine", 16384, payload={"query": query})
    assert b.run() == 1
    assert b.queue.get(jb.id).state == DONE

    # THE PROOF: identical rows reached the landing sink by two different dispatch paths.
    assert landed_subprocess == landed_inproc == [{"text": _answer(query)}]


def test_with_the_flag_OFF_a_kind_with_a_compute_half_still_runs_in_process(tmp_path):
    """The default is not merely untested — it is asserted. A registered compute half is inert
    until `worker_mode` is flipped, so registering one can never change behaviour by itself."""
    ran: list[str] = []
    def _inproc(job):
        ran.append("inproc")
        return "ok"

    sup = _supervisor(tmp_path, {SELFTEST_ANSWER_KIND: _inproc})
    sup.compute[SELFTEST_ANSWER_KIND] = (
        lambda j, c: (_ for _ in ()).throw(AssertionError("dispatched out-of-process, flag OFF")),
        lambda j, b: None,
    )
    sup.loader.ensure_pinned(warm=False)
    j = sup.queue.enqueue(SELFTEST_ANSWER_KIND, "routine", 16384, payload={"query": "q"})
    assert sup.run() == 1
    assert ran == ["inproc"] and sup.queue.get(j.id).result == "ok"


def test_an_UNMIGRATED_kind_runs_in_process_even_with_the_flag_ON(tmp_path):
    """The seam is gated on BOTH the mode and a registered compute half. An unmigrated kind must
    not be routed through a protocol it was never written for just because a sibling lane
    migrated — that is what makes migration per-lane and reversible (note §4)."""
    ran: list[str] = []
    def _inproc(job):
        ran.append("inproc")
        return "ok"

    sup = _supervisor(tmp_path, {"unmigrated": _inproc})
    sup.worker_mode = SUBPROCESS
    sup.compute[SELFTEST_ANSWER_KIND] = (lambda j, c: iter(()), lambda j, b: None)
    sup.loader.ensure_pinned(warm=False)
    j = sup.queue.enqueue("unmigrated", "routine", 16384)
    assert sup.run() == 1
    assert ran == ["inproc"] and sup.queue.get(j.id).state == DONE


def test_a_worker_that_dies_fails_the_job_not_the_loop(tmp_path):
    """The in-process guarantee, extended: "a handler that raises must not take down the loop"
    must hold for a worker that dies too, or the split traded one liveness bug for another."""
    from scheduler.worker import SELFTEST_RAISE_KIND

    ran: list[int] = []
    def _ok(job):
        ran.append(job.id)
        return "fine"

    sup = _supervisor(tmp_path, {"ok": _ok})
    sup.worker_mode = SUBPROCESS
    sup.compute[SELFTEST_RAISE_KIND] = (lambda j, c: iter(()), lambda j, b: None)
    sup.loader.ensure_pinned(warm=False)
    bad = sup.queue.enqueue(SELFTEST_RAISE_KIND, "routine", 16384)
    good = sup.queue.enqueue("ok", "routine", 16384)
    assert sup.run() == 2                                  # the loop survived the worker's death
    failed = sup.queue.get(bad.id)
    assert failed.state == FAILED and "ValueError" in (failed.error or "")
    assert sup.queue.get(good.id).state == DONE and ran == [good.id]


def test_the_ceiling_gate_still_refuses_BEFORE_any_worker_is_spawned(tmp_path):
    """§2.7 / §3 Q6: `ensure_tier` runs at `tick`'s top, ahead of the seam, so the RAM-ceiling
    refusal point is unchanged by the split. A ceiling-breaching job must be DEFERRED without a
    subprocess ever existing — if it spawned first, the worker's own RSS would be a new consumer
    admitted past the gate that exists to refuse it."""
    cfg = dataclasses.replace(
        load_config(), resources=dataclasses.replace(load_config().resources, usable_ram_gb=5.0)
    )
    ld = _loader(cfg)
    ld.ensure_pinned(warm=False)
    sup = Supervisor(queue=JobQueue(tmp_path / "q.db"), loader=ld, handlers={},
                     presence=_present(False), power=on_ac(), warm=False)
    sup.worker_mode = SUBPROCESS
    sup.compute[SELFTEST_ANSWER_KIND] = (
        lambda j, c: (_ for _ in ()).throw(AssertionError("spawned past the ceiling gate")),
        lambda j, b: (_ for _ in ()).throw(AssertionError("landed past the ceiling gate")),
    )
    j = sup.queue.enqueue(SELFTEST_ANSWER_KIND, "synthesis", 32768)   # 2.7 + 17 > 5 -> refused
    sup.run()
    deferred = sup.queue.get(j.id)
    assert deferred.state == DEFERRED and "ceiling" in (deferred.error or "")


# --- the `[scheduler]` config section must not be silently dropped ----------------------------


def test_the_scheduler_section_round_trips_through_an_overlay(tmp_path, monkeypatch):
    """⚑ Item 3's third acceptance clause. `_overlay` merges by section NAME and `Config` has no
    catch-all, so a `[scheduler]` block with no dataclass behind it VANISHES silently — the
    bp-102 / finding-0174 mechanism. This proves the section is schema'd by writing a real overlay
    and reading the values back.

    The overlay is monkeypatched to a tmp file rather than written to `config/`: bp-123 renamed
    the per-machine overlay `local.toml` -> `ouroboros.toml` (the plan predates that and says
    `local.toml`), and `_refuse_on_legacy_overlay` now RAISES if a `local.toml` exists. Writing
    either real file would either trip that guard or mutate the live instance's config.
    """
    from core.kernel.config import loader as cfgmod

    overlay = tmp_path / "ouroboros.toml"
    overlay.write_text(
        '[scheduler]\n'
        'worker_mode = "subprocess"\n'
        'batch_deadline_s = 90.0\n'
        'escalation_grace_s = 15.0\n'
        'lease_ttl_s = 45.0\n'
        '[scheduler.job_budgets]\n'
        'dream = 1800.0\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(cfgmod, "_INSTANCE_OVERLAY", overlay)
    monkeypatch.setattr(cfgmod, "_LEGACY_OVERLAY", tmp_path / "absent-local.toml")
    monkeypatch.setattr(cfgmod, "LEVERS_OVERLAY", tmp_path / "absent-levers.toml")

    sch = cfgmod.load_config().scheduler
    assert sch.worker_mode == "subprocess"
    assert sch.batch_deadline_s == 90.0
    assert sch.escalation_grace_s == 15.0
    assert sch.lease_ttl_s == 45.0
    # Per-KIND, because that is the shape `JobQueue.job_budgets` already consumes (finding-0228).
    assert sch.job_budgets == {"dream": 1800.0}


def test_the_shipped_defaults_change_nothing(tmp_path):
    """The whole section is defined, and every default is today's behaviour: in-process dispatch,
    no deadline, no budget, no lease. finding-0178's status quo is preserved exactly."""
    sch = load_config().scheduler
    assert sch.worker_mode == "inproc"
    assert (sch.batch_deadline_s, sch.lease_ttl_s) == (0.0, 0.0)
    assert sch.job_budgets == {}                       # empty => `claim()` stamps a NULL deadline


def test_the_config_default_matches_the_supervisors_default(tmp_path):
    """Two homes for one default is a drift bug waiting to happen; assert they agree."""
    sup = _supervisor(tmp_path, {})
    assert sup.worker_mode == load_config().scheduler.worker_mode == "inproc"


# ==============================================================================================
# bp-110 Item 4 — one model in flight (dn-supervision-and-liveness §2.7)
# ==============================================================================================


def test_with_no_worker_out_the_model_rule_blocks_nothing(tmp_path):
    """The rule is inert until a model-using job is actually out — otherwise it would be a
    permanent serialization of the queue dressed up as a safety property."""
    sup = _supervisor(tmp_path, {})
    assert sup.model_blocked_tiers() == frozenset()


def test_while_a_model_job_is_out_only_its_own_tier_and_the_pinned_tier_stay_claimable(tmp_path):
    """⚑ Item 4's acceptance. With a synthesis job out to a worker, the next `claim()` must
    return only a job sharing its `load_key` or a model-free (pinned-tier) one. A SECOND
    model-using job stays QUEUED."""
    sup = _supervisor(tmp_path, {"k": lambda j: "ok"})
    sup.loader.ensure_pinned(warm=False)
    sup._in_flight_key = ("synthesis", 32768)          # a synthesis job is out to a worker

    blocked = sup.model_blocked_tiers()
    assert "synthesis" not in blocked                  # its own tier stays claimable
    assert sup._pinned_tier not in blocked             # landing/housekeeping is never blocked
    assert "stretch" in blocked                        # any OTHER model tier is refused

    same = sup.queue.enqueue("k", "synthesis", 32768)
    other = sup.queue.enqueue("k", "stretch", 32768)
    claimed = sup.queue.claim(blocked_tiers=sup.blocked_tiers() | sup.model_blocked_tiers())
    assert claimed is not None and claimed.id == same.id
    assert sup.queue.get(other.id).state == QUEUED     # the second model job waits


def test_the_second_model_job_is_dispatched_once_the_first_lands(tmp_path):
    """The rule defers, it never drops: clearing the in-flight key releases the held tier."""
    sup = _supervisor(tmp_path, {"k": lambda j: "ok"})
    sup.loader.ensure_pinned(warm=False)
    sup._in_flight_key = ("synthesis", 32768)
    other = sup.queue.enqueue("k", "stretch", 32768)
    assert sup.queue.claim(blocked_tiers=sup.model_blocked_tiers()) is None

    sup._in_flight_key = None                          # the worker landed
    claimed = sup.queue.claim(blocked_tiers=sup.model_blocked_tiers())
    assert claimed is not None and claimed.id == other.id


def test_the_foreground_gate_is_not_overloaded_by_the_model_rule(tmp_path):
    """Item 4's invariant: `blocked_tiers()` keeps its meaning. Two different reasons to refuse a
    tier must stay separately readable, or a later reader cannot tell which rule refused a job."""
    sup = _supervisor(tmp_path, {}, active=False)      # owner idle => foreground gate open
    sup._in_flight_key = ("synthesis", 32768)
    assert sup.blocked_tiers() == frozenset()          # the foreground gate says nothing
    assert sup.model_blocked_tiers() != frozenset()    # the model rule says plenty


def test_a_crashed_worker_does_not_strand_the_model_gate_closed(tmp_path):
    """A guard that fails closed forever is its own outage. The in-flight key is cleared in a
    `finally`, so a worker that dies mid-dispatch releases the tier it was holding."""
    from scheduler.worker import SELFTEST_RAISE_KIND

    sup = _supervisor(tmp_path, {})
    sup.worker_mode = SUBPROCESS
    sup.compute[SELFTEST_RAISE_KIND] = (lambda j, c: iter(()), lambda j, b: None)
    sup.loader.ensure_pinned(warm=False)
    sup.queue.enqueue(SELFTEST_RAISE_KIND, "synthesis", 32768)
    sup.run()
    assert sup._in_flight_key is None                  # released despite the worker's death
    assert sup.model_blocked_tiers() == frozenset()


# ==============================================================================================
# bp-154 Item 2 — the power axis, as its OWN predicate (dn-supervision-and-liveness A1)
# ==============================================================================================


def test_the_heavy_lanes_are_shed_while_discharging(tmp_path):
    """⚑ Item 2's acceptance. On battery, `power_blocked_tiers()` sheds exactly the existing heavy
    set — READ, never reshaped, so there is one shed vocabulary rather than two (A1's parked
    selector decision)."""
    sup = _supervisor(tmp_path, {}, power=on_battery(55.0))
    # Non-vacuity, twice over: the shed set is not empty (an empty `HEAVY_TIERS` would make every
    # assertion below trivially true), and 55% is well above the floor, so what refuses here is the
    # DISCHARGING rule and not the floor.
    assert HEAVY_TIERS == frozenset({"synthesis", "stretch"})
    assert sup.power.below_floor() is False
    assert sup.power_blocked_tiers() == HEAVY_TIERS


def test_on_AC_the_power_axis_refuses_nothing(tmp_path):
    """The rule is not a permanent shed dressed up as a safety property: plugged in, it says
    nothing at all."""
    sup = _supervisor(tmp_path, {}, power=on_ac())
    assert sup.power_blocked_tiers() == frozenset()


def test_an_unreadable_battery_sheds_the_heavy_lanes(tmp_path):
    """⚑ Fail closed, at the supervisor's altitude rather than only the sensor's (A1.7's named
    falsifier: "the sensor fails open"). A host that cannot read `pmset` at all — CI, a non-macOS
    worker, a failed exec — refuses heavy work rather than dispatching it blind."""
    sup = _supervisor(tmp_path, {}, power=unreadable())
    assert sup.power.state() is None                   # precondition: genuinely unreadable
    assert sup.power_blocked_tiers() == HEAVY_TIERS


@pytest.mark.parametrize("discharging", [True, False])
@pytest.mark.parametrize("active", [True, False])
def test_the_foreground_gate_is_byte_identical_under_every_power_state(tmp_path, active,
                                                                      discharging):
    """⚑ Item 2's invariant, and A1.1's one load-bearing pin. `blocked_tiers()` is THE FOREGROUND
    GATE and nothing else: its answer is a function of presence alone, unchanged by the power axis
    under all four combinations. Two different reasons to refuse a tier, conflated into one
    predicate, is how a reader later cannot tell which rule refused a job."""
    power = on_battery(55.0) if discharging else on_ac()
    sup = _supervisor(tmp_path, {}, active=active, power=power)
    assert sup.blocked_tiers() == (HEAVY_TIERS if active else frozenset())
    # ... and the power predicate is independently correct at the same time, so the two rules are
    # provably separate answers rather than one answer read twice.
    assert sup.power_blocked_tiers() == (HEAVY_TIERS if discharging else frozenset())


def test_the_power_rule_is_not_folded_into_the_foreground_gate(tmp_path):
    """The pin, read off the SOURCE — behaviour alone cannot distinguish "a separate predicate"
    from "one predicate that happens to agree today", and it is the shape, not the answer, that
    A1.1 fixes. Each of the three predicates reads its own sensor and no other's."""
    foreground = inspect.getsource(Supervisor.blocked_tiers).split('"""')[-1]
    power = inspect.getsource(Supervisor.power_blocked_tiers).split('"""')[-1]
    # Non-vacuity: the token IS findable by this search where it legitimately appears, so its
    # absence from `blocked_tiers`'s body is evidence and not an artifact of a search that matches
    # nothing anywhere.
    assert "self.power." in inspect.getsource(Supervisor)
    assert "self.power." not in foreground and "self.presence." in foreground
    assert "self.presence." not in power and "self.power." in power
