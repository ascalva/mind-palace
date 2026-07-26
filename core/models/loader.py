"""Two-slot model loader (BUILD-SPEC §5).

The model lifecycle's executor: it loads, swaps, and evicts weights while enforcing the
hardware ceiling (Invariant 8). The router *decides* tier/window; this code *does* the
load — model advises, code acts.

Two slots, never more:
  * Slot 1 — the pinned tiny model (router + watchdog), kept warm indefinitely.
  * Slot 2 — a single swappable worker. Loading a worker evicts the prior worker.
A stretch model that declares `evicts_pinned` also evicts the pinned model and runs as
the sole resident for its duration (the documented §5 tradeoff).

The ceiling is checked BEFORE any Ollama call, so breaching work is refused, not
half-applied. The `warm` flag lets the eviction/accounting logic be unit-tested
without a live server.

⚑ **RESIDENCY IS MEASURED, NOT BELIEVED (bp-107, finding-0199).** `_resident` used to be an
in-process dict that started EMPTY on every construction, and nothing reconciled it against what
Ollama — a separate, long-lived process that outlives the supervisor — is actually holding. That
made three states reachable, and all three were REPRODUCED LIVE (`dn-local-model-runtime` §2.1 B,
2026-07-25): *false-absent* (a fresh loader believed 1 model / 6.6 GB while `ollama ps` held 2),
*guard-pass on a real breach* (`_check_ceiling` passed 23.0 ≤ 24.0 while the true prospective was
25.7 GB, because the eviction loop iterated an empty dict and so nothing was ever really unloaded),
and *false-resident* (a 0.0 ms stale early-return skipped a load that was needed after Ollama's own
30-minute keep-alive timer evicted a worker). `reconcile()` now replaces belief with measurement at
construction and before every ceiling check, which is what makes the ceiling an enforcement rather
than an advisory (non-negotiable #8).

⚑ **THE ACCOUNTING IS PARTIAL, AND SAYS SO.** `ps()` returns *names only*, so a resident name with
no registry entry cannot be costed. `ReconcileReport.complete` is the honesty flag; any surface that
prints residency must render "partial" when it is False. Do not let a partial reconcile read as a
full one — a false claim of completeness is the very defect class this closes, one level up.

⚑ **THIS IS THE INTERIM GUARD.** `dn-local-model-runtime` §2.3 replaces this whole class with a
process manager for which residency *is* child-process existence, and the false-absent and
false-resident states lose their representation instead of being detected. That is bp-116. This
buys correctness for the interval between now and then, and deliberately does not pre-empt it:
`max_resident_models` keeps counting exactly what it counted before, and `resident_gb` stays the
declared weights-only constant (finding-0174 is made VISIBLE here, not fixed — see
`_MEASURED_NON_REGISTRY_GB`).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from core.kernel.config import Config, ModelConfig
from core.models.ollama_client import OllamaClient
from core.models.registry import MemoryCeilingError, Registry

# Ceiling-consuming models that are NOT registry entries, at their MEASURED footprint.
#
# ⚑ Exactly one carve-out today, and it is load-bearing: the embedder is not in the registry at all
# (`config/defaults.toml` `[embedding]` declares `model`/`dim`/`query_instruction` — no
# `resident_gb`, no `tier`, not a `[[models]]` entry), so it is permanently unknown. Under the
# rule below, an uncosted embedder would refuse every non-pinned load on any system that has ever
# embedded — a guard converted into an outage. Costing it is what keeps the rule safe (bp-107 §6).
#
# The number is MEASURED, not declared: `ollama ps` reports `qwen3-embedding:4b` at **10.0 GB** at
# its model-default context 40960, and 40960 is what production actually gets because
# `OllamaClient.embed()` passes no `num_ctx` (`core/models/ollama_client.py:109-116`).
# `dn-local-model-runtime` §2.1 C measured it; finding-0174 had assumed ~2.5 GB, so the real
# arithmetic is `23.0 + 10.0 = 33.0` against `usable_ram_gb = 24.0`, not 25.5. **Context, not
# weights, dominates** — which is why this is a per-runtime measurement keyed to a model name and
# NOT a `resident_gb` added to config: a weights-only constant is the wrong shape (§2.3).
#
# The key is only consulted for the CONFIGURED embedder (`_non_registry_gb`), and only under
# Ollama: a `llama-server`-hosted embedder does not appear in `/api/ps` at all, so the 8192-ctx 3.69
# figure from the same measurement session is deliberately absent: it is bp-116/bp-118's number,
# for accounting this loader will not be doing.
_MEASURED_NON_REGISTRY_GB: dict[str, float] = {
    "qwen3-embedding:4b": 10.0,
}


@dataclass(frozen=True)
class ReconcileReport:
    """What one `ps()` measurement could and could NOT account for.

    ⚑ `complete` is a narrow claim: *every resident NAME was costable*. It is emphatically NOT a
    claim that the GB figures are right — they are still the declared weights-only `resident_gb`
    constants, and finding-0174 (declared vs real, context-dominated) remains open until
    `dn-local-model-runtime` §2.3 lands. A caller must read `complete=True` as "nothing resident was
    invisible to the sum", never as "the sum is correct".
    """

    reconciled: bool          # False = the ps() probe failed; accounting is today's belief
    known_gb: float           # resident GB the registry (or a measured carve-out) could cost
    unknown: tuple[str, ...]  # resident names with NO registry entry and no measurement
    complete: bool            # known-and-costed everything <=> not unknown and reconciled

    @classmethod
    def measure(cls, *, reconciled: bool, known_gb: float,
                unknown: tuple[str, ...]) -> ReconcileReport:
        """The ONLY constructor used in anger, so `complete` cannot drift from its definition.
        Item 1's falsifier — "reports `complete=True` while `unknown` is non-empty" — is
        unreachable by construction rather than merely untested."""
        return cls(reconciled=reconciled, known_gb=known_gb, unknown=unknown,
                   complete=reconciled and not unknown)


@dataclass
class TwoSlotLoader:
    config: Config
    client: OllamaClient
    registry: Registry
    _resident: dict[str, ModelConfig] = field(default_factory=dict)
    last_load_seconds: float = 0.0
    # Reconciliation state, all derived from the last successful `ps()` probe.
    _external_gb: float = 0.0          # costed residency OUTSIDE the registry (the embedder)
    _unknown: tuple[str, ...] = ()     # resident names nothing can cost -> fail-closed
    _report: ReconcileReport = field(init=False)  # always set by __post_init__

    def __post_init__(self) -> None:
        # Measure at construction: a fresh supervisor coming up against an Ollama that has held
        # models across runs is exactly the false-absent path (finding-0199). `reconcile()` never
        # raises, so an unreachable Ollama cannot brick startup.
        self.reconcile()

    # --- inspection --------------------------------------------------------------
    def resident_models(self) -> list[str]:
        return list(self._resident)

    def resident_gb(self) -> float:
        """Registry-costed resident GB. Deliberately unchanged in meaning — callers and the
        two-slot algebra both reason over registry models. The ceiling additionally charges
        `external_resident_gb()`; see `_check_ceiling`."""
        return sum(m.resident_gb for m in self._resident.values())

    def external_resident_gb(self) -> float:
        """Ceiling-consuming residency outside the registry (today: the embedder, measured).
        Charged by `_check_ceiling`, reported in `ReconcileReport.known_gb`."""
        return self._external_gb

    def uncostable_resident(self) -> tuple[str, ...]:
        """Resident names nothing can cost. Non-empty => the accounting is partial AND the
        fail-closed rule is active for non-pinned loads."""
        return self._unknown

    @property
    def last_reconcile(self) -> ReconcileReport:
        """The most recent measurement. `complete is False` => any surface that renders residency
        must say PARTIAL. The loader deliberately does not print it: core does not own
        presentation (bp-107 §11)."""
        return self._report

    # --- reconciliation (the ONE Ollama call on the accounting path) --------------
    def reconcile(self) -> ReconcileReport:
        """Replace belief with measurement: ask Ollama what is ACTUALLY resident.

        Called at construction and before every `_check_ceiling`. Never raises — a probe failure
        degrades to today's behaviour and is REPORTED as unreconciled, because Ollama being
        unreachable means no load can succeed anyway (so refusing adds nothing but a brick risk).

        `ps()` is the ONE reconciliation source (`OllamaClient.ps`); no second probe exists, by
        design (bp-107 §9). It returns names only, which is the whole reason this returns a report
        that can say "partial" instead of a number that pretends to be complete.
        """
        try:
            names = list(self.client.ps())
        except Exception:  # noqa: BLE001 - any client failure degrades; see the docstring
            # Deliberately do NOT clear `_unknown`/`_external_gb`: "degrade to today's belief"
            # means keep the last measurement, which is the fail-closed direction. Nor do we clear
            # `_resident` — an unreachable Ollama is not evidence that nothing is loaded.
            self._report = ReconcileReport.measure(
                reconciled=False,
                known_gb=self.resident_gb() + self._external_gb,
                unknown=self._unknown,
            )
            return self._report

        resident: dict[str, ModelConfig] = {}
        external_gb = 0.0
        unknown: list[str] = []
        for name in names:
            try:
                resident[name] = self.registry.by_name(name)
                continue
            except KeyError:
                pass
            measured = self._non_registry_gb(name)
            if measured is None:
                unknown.append(name)
            else:
                external_gb += measured

        self._resident = resident
        self._external_gb = external_gb
        self._unknown = tuple(unknown)
        self._report = ReconcileReport.measure(
            reconciled=True,
            known_gb=sum(m.resident_gb for m in resident.values()) + external_gb,
            unknown=self._unknown,
        )
        return self._report

    def _non_registry_gb(self, name: str) -> float | None:
        """Measured footprint for a resident name the registry cannot cost, or None if there is
        no measurement — in which case the name is reported in `unknown` and says so, rather than
        being silently costed at zero (which is the finding-0174 failure re-created)."""
        if name != self.config.embedding.model:
            return None
        return _MEASURED_NON_REGISTRY_GB.get(name)

    # --- accounting ---------------------------------------------------------------
    #
    # [banner: correction] Was: "accounting (pure-ish, no Ollama calls)". That stopped being true
    # at bp-107 — the accounting path now begins with `reconcile()`, which calls `ps()`. The purity
    # was load-bearing and is NOT abandoned: it is what let `_check_ceiling` be tested without a
    # live server, so reconciliation is a SEPARATE, injectable step (swap the client) and
    # `_check_ceiling` stays a pure function of a dict plus a float. Nothing below this line talks
    # to Ollama; `reconcile()`, above, is the one place that does.
    def _prospective(self, candidate: ModelConfig) -> dict[str, ModelConfig]:
        """The resident set after loading `candidate`, applying the two-slot rules."""
        pinned_name = self.registry.pinned.name
        new = dict(self._resident)
        if candidate.evicts_pinned:
            new.pop(pinned_name, None)
        if not candidate.pinned:
            # Slot 2 holds exactly one worker: drop any existing non-pinned model.
            for name in [n for n in new if n != pinned_name]:
                del new[name]
        new[candidate.name] = candidate
        return new

    def _check_ceiling(self, prospective: dict[str, ModelConfig], *,
                       external_gb: float = 0.0) -> None:
        """Pure: a dict and a float against the configured budget. No client, no state.

        `external_gb` is measured residency the two-slot algebra cannot reason about because it is
        not a registry model (today: the embedder). It is charged in the GB dimension ONLY, and
        NOT against `max_resident_models` — that count keeps meaning exactly what it meant before
        (registry slots). Counting the embedder as a third "resident model" would refuse every
        worker load while it is warm, which is a reinterpretation of `max_resident_models` that
        `dn-local-model-runtime` §2.3 owns (it *replaces* the knob), not this interim guard.
        """
        budget = self.config.resources.usable_ram_gb
        max_n = self.config.resources.max_resident_models
        if len(prospective) > max_n:
            raise MemoryCeilingError(
                f"would hold {len(prospective)} models > max {max_n}: {list(prospective)}"
            )
        total = sum(m.resident_gb for m in prospective.values()) + external_gb
        if total > budget:
            external = f" + {external_gb:.1f} GB measured non-registry" if external_gb else ""
            raise MemoryCeilingError(
                f"would use {total:.1f} GB > usable budget {budget:.1f} GB "
                f"({', '.join(prospective)}{external})"
            )

    def _refuse_uncostable(self, candidate: ModelConfig) -> None:
        """The fail-closed rule (bp-107 §6). While Ollama holds a name we cannot cost, the sum a
        load would be checked against is knowably incomplete, so a NON-PINNED load — itself
        ceiling-consuming — is refused rather than admitted on partial arithmetic.

        ⚑ The PINNED model is ALWAYS admitted by this rule. It is the router and watchdog; the
        system is unusable without it, and refusing it converts a memory guard into an
        availability outage (bp-107 §10's first stop condition).

        ⚑ Scope of the carve-out, stated because the plan's two phrasings differ (see
        finding-0220): this rule never refuses the pinned model, but the ARITHMETIC ceiling still
        applies to every model, pinned included, exactly as it did before bp-107. Exempting the
        pinned model from the arithmetic too would make the ceiling *less* able to refuse
        breaching work, which is the opposite of what non-negotiable #8 asks for, and the
        weakening would be invisible: no reachable state in the FSM property test exercises a
        pinned load that breaches, so nothing would have caught it.
        """
        if candidate.pinned or not self._unknown:
            return
        raise MemoryCeilingError(
            f"partial accounting: cannot cost resident model(s) {', '.join(self._unknown)} — "
            f"refusing non-pinned load of {candidate.name!r} (fail-closed, finding-0199). "
            f"The pinned model is always admitted."
        )

    # --- load / swap -------------------------------------------------------------
    def ensure(self, name: str, *, warm: bool = True) -> ModelConfig:
        """Make `name` resident, swapping/evicting as the two-slot rules require.
        Refuses (raises MemoryCeilingError) before touching Ollama if it would breach
        the ceiling.

        ⚑ Order matters and is the fix. `reconcile()` runs FIRST — before the idempotence
        early-return, which is what killed the false-resident state (a model Ollama's keep-alive
        timer had evicted was still claimed resident and the needed load was skipped), and before
        `_check_ceiling`, which is what killed the false-absent state (the eviction loop below now
        iterates a MEASURED set, so the evictions the ceiling arithmetic assumes actually happen
        instead of being assumed).

        ⚑ `warm=False` does not probe, for the same reason it does not load: it is the
        "no live server" affordance the accounting tests run under (module docstring), and `ps()`
        is a server call. Every production caller is warm=True (`scheduler/supervisor.py:42`);
        construction reconciles regardless, so even a warm=False loader starts from measurement.
        """
        candidate = self.registry.by_name(name)
        if warm:
            self.reconcile()
        if name in self._resident:
            return candidate

        self._refuse_uncostable(candidate)
        prospective = self._prospective(candidate)
        # refuse breaching work up front, charging measured non-registry residency too
        self._check_ceiling(prospective, external_gb=self._external_gb)

        for gone in [n for n in self._resident if n not in prospective]:
            if warm:
                self.client.unload(gone)
            del self._resident[gone]

        keep_alive: str | int = -1 if candidate.pinned else self.config.ollama.default_keep_alive
        t0 = time.monotonic()
        if warm:
            self.client.load(candidate.name, num_ctx=candidate.num_ctx, keep_alive=keep_alive)
        self.last_load_seconds = time.monotonic() - t0
        self._resident[name] = candidate
        return candidate

    def ensure_tier(self, tier: str, *, warm: bool = True) -> ModelConfig:
        return self.ensure(self.registry.by_tier(tier).name, warm=warm)

    def ensure_pinned(self, *, warm: bool = True) -> ModelConfig:
        return self.ensure(self.registry.pinned.name, warm=warm)
