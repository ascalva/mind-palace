"""The supervisor — one loop owns the queue and the worker slot (BUILD-SPEC §13; roadmap §7).

Cooperative, job-boundary scheduling:
  1. claim the next eligible job (priority; swap-avoidance within a priority band; heavy
     tiers gated while the owner is present — the foreground check);
  2. make its (tier, window) resident via the two-slot loader, which refuses any load that
     would breach the RAM ceiling (Invariant 8) — such a job is deferred, not crashed;
  3. dispatch it, in ONE OF TWO MODES (see below), counting *worker* swaps
     (the pinned router doing interstitial work never evicts the worker, roadmap §7);
  4. record vitals (queue depth, model-load time) and repeat.

[banner: correction] Step 3 used to read "run its handler to completion (or one checkpointed
step)", which was the only shape a dispatch could have. `dn-supervision-and-liveness` §2.5 adds a
second, and names why the first is not enough: a synchronous in-process call cannot be budgeted
from outside it, and cannot be observed from the loop it blocks. The two modes are:

  * **`inproc` (the DEFAULT, and the documented behaviour for every unmigrated kind).** Exactly
    as before: `handler(job)` runs to completion or to one checkpointed step, on this thread.
    Nothing about it changes, and no kind moves off it without an owner flipping `worker_mode`
    and a per-lane deskcheck (note §4).
  * **`subprocess`.** The kind's registered COMPUTE half runs in a `python -m scheduler.worker`
    child holding no store handle; it streams bounded batches back and the supervisor lands each
    one itself. The supervisor stays live throughout — it is reading a pipe, not computing — so
    the batch becomes both the fairness unit and the in-band progress signal.

[cross-ref: extension] "A reactive escalation is simply a high-priority job; it is dispatched at
the next boundary, never as a mid-generation interrupt." That remains true, and is about
SCHEDULING. `dn-supervision-and-liveness` §2.5 adds a separate power that must not be confused
with it: a WEDGED WORKER is now killable mid-compute (SIGTERM -> grace -> SIGKILL, a kernel fact
rather than cooperation). Distinguish the two — the split did not introduce preemption. No job is
ever interrupted to run another job; a worker is only ever killed because it overran its own
bound, and the escalation targets ONLY the worker, never the supervisor (killing the supervisor
mid-landing is how you create the partial write oq-0035 worried about).

A handler that raises must not take down the loop. Neither must a worker that dies.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from config.secrets_backend import MintedToken, SecretsBackend
from core.models import MemoryCeilingError
from core.models.loader import TwoSlotLoader
from core.stores.telemetry import TelemetryWriter
from scheduler.presence import Presence
from scheduler.queue import RUNNING, Job, JobQueue
from scheduler.worker import (
    ComputeHandler,
    Lander,
    ReadOnlyRows,
    WorkerFailure,
    run_batches,
)

# Tiers that must not run while the owner is actively present (BUILD-SPEC §13).
HEAVY_TIERS = frozenset({"synthesis", "stretch"})

# The two dispatch modes (`dn-supervision-and-liveness` §2.5). `INPROC` is the default and the
# behaviour of every unmigrated kind; a flip is the owner's, per lane, in config/ouroboros.toml.
INPROC, SUBPROCESS = "inproc", "subprocess"

Handler = Callable[[Job], "str | None"]


class _NoRows:
    """The `ReadOnlyRows` a supervisor with no store wired serves: it answers every verb by
    refusing. Fail-closed — a lane that expected reads gets a typed error naming the missing
    wiring, rather than a silent empty result it would land as if the corpus were empty."""

    def _refuse(self, verb: str) -> list[dict[str, Any]]:
        raise RuntimeError(
            f"worker requested {verb!r} but no `rows` is wired on this Supervisor — "
            "pass `rows=` to serve a compute half that reads"
        )

    def all_rows(self, *, provenances: set[str] | None = None) -> list[dict[str, Any]]:
        return self._refuse("all_rows")

    def rows_for_source(self, source_path: str) -> list[dict[str, Any]]:
        return self._refuse("rows_for_source")

    def search(self, vector: list[float], k: int) -> list[dict[str, Any]]:
        return self._refuse("search")


@dataclass
class Supervisor:
    queue: JobQueue
    loader: TwoSlotLoader
    handlers: dict[str, Handler]
    presence: Presence = field(default_factory=Presence)
    telemetry: TelemetryWriter | None = None
    secrets: SecretsBackend | None = None  # vault-runtime-auth.md; Phase 5 wires per-job use
    warm: bool = True                      # tests pass warm=False (no Ollama calls)
    swaps: int = 0                         # worker-slot model swaps (the cost to minimize)
    # The compute/land registry (bp-110 §6). ADDITIVE AND DEFAULTED, deliberately: every existing
    # construction site (`launcher.py:519`, `scripts/watch.py:95`, and five test sites) keeps
    # working with no edit, which is the falsifier for "this change was additive" — if any of them
    # needed touching, the "no behaviour change at landing" claim would be false.
    compute: dict[str, tuple[ComputeHandler, Lander]] = field(default_factory=dict)
    worker_mode: str = INPROC
    # The ONLY store surface a worker's compute half can reach, served BY THIS PROCESS over the
    # pipe (bp-110 §3 Q3 — the read the note's §2.3 wording is silent about). None = no reads are
    # answerable, which is correct for a lane that needs none. The worker never opens a store; it
    # asks, and this object is what answers.
    rows: ReadOnlyRows | None = None
    _worker_key: tuple[str, int] | None = None
    # The `load_key` of a MODEL-USING job currently out to a worker, or None. Set for the span of
    # an out-of-process dispatch and cleared in a `finally`, so a crashed worker cannot strand the
    # gate closed and wedge the queue — a guard that fails closed forever is its own outage.
    _in_flight_key: tuple[str, int] | None = None

    @property
    def _pinned_tier(self) -> str:
        return self.loader.registry.pinned.tier

    def mint_token(self, role: str, ttl: str = "10m") -> MintedToken:
        """Mint an ephemeral token scoped to `role`'s policy (vault-runtime-auth.md §2). Returns
        the whole `MintedToken`: the supervisor passes `.token` to the agent (Phase 5) and records
        `.accessor` in the action's attestation (the Step-5 join) — it holds minting authority
        only, never reading the secret it mints a token for; that happens later when the agent
        itself calls `get_secret(name, token=...)`."""
        if self.secrets is None:
            raise RuntimeError("no secrets backend wired — mint_token requires [secrets] enabled")
        return self.secrets.mint_token(role, ttl)

    def blocked_tiers(self) -> frozenset[str]:
        """THE FOREGROUND GATE, and nothing else. Deliberately not extended with the
        single-model-in-flight rule (bp-110 §7 Item 4's invariant: "the foreground gate keeps its
        meaning and is not overloaded") — two different reasons to refuse a tier, conflated into
        one predicate, is how a reader later cannot tell which rule refused a job."""
        return HEAVY_TIERS if self.presence.foreground_active() else frozenset()

    def model_blocked_tiers(self) -> frozenset[str]:
        """THE SINGLE-MODEL-IN-FLIGHT RULE, verbatim from `dn-supervision-and-liveness` §2.7:

            At most one in-flight MODEL-USING job. While one is out, the supervisor may dispatch
            only jobs sharing its `load_key` or doing landing/housekeeping.

        Today "≤ 2 resident models" (non-negotiable #8) holds IMPLICITLY because `tick` is serial.
        A supervisor that stays live while a worker computes can claim a second model-using job,
        and `ensure_tier` for job B would evict the model job A is mid-generation on — a failure
        that would look like a model bug, not a scheduler bug. This adds no resident model; it
        prevents one, so ceiling accounting is numerically unchanged.

        The pinned tier is never blocked: it is always resident and the pinned router doing
        interstitial work never evicts the worker slot (the module docstring's step 3), which is
        exactly the "landing/housekeeping" the rule carves out.

        ⚑ **Enforced at the ONE claim site, via `claim`'s existing `blocked_tiers` — no new queue
        API** (Item 4's invariant). Tier accounting, stated honestly per §2.7: this is a dispatch
        guard, **tier 5 with a tier-4 test**, not a capability. The ceiling REFUSAL itself
        (`_check_ceiling`, raising before any load) is untouched by this plan.

        ⚑ **Scope note, so this is not read as stronger than it is.** Under the SYNCHRONOUS
        dispatch this plan ships (`_dispatch_to_worker` streams to completion inside one `tick`),
        the window this guards is currently EMPTY — no second claim can happen while a worker is
        out. The guard ships anyway, with the mechanism that will create the hazard, so that
        concurrency cannot later be introduced without it (§3 Q7: "shipping the split without it
        is a regression"). finding-0229 records that the liveness half of §1's objective needs
        non-blocking dispatch, which needs the serve loop — out of this plan's scope by §5.
        """
        if self._in_flight_key is None:
            return frozenset()
        in_flight_tier = self._in_flight_key[0]
        return frozenset(
            m.tier for m in self.loader.registry.config.models
            if m.tier not in (in_flight_tier, self._pinned_tier)
        )

    def tick(self) -> bool:
        """Dispatch at most one job. Returns False when nothing is runnable right now."""
        job = self.queue.claim(loaded_key=self._worker_key,
                               blocked_tiers=self.blocked_tiers() | self.model_blocked_tiers())
        if job is None:
            return False

        # Make the model resident; the loader refuses ceiling-breaching loads up front.
        try:
            self.loader.ensure_tier(job.tier, warm=self.warm)
        except MemoryCeilingError as e:
            self.queue.defer(job.id, f"ceiling: {e}")
            return True

        # Count a swap only when the *worker* (non-pinned) tier/window changes.
        if job.tier != self._pinned_tier:
            if self._worker_key is not None and job.load_key != self._worker_key:
                self.swaps += 1
            self._worker_key = job.load_key

        # ⚑ THE DISPATCH SEAM. Note where it sits: AFTER `ensure_tier` above, so the ceiling gate
        # still runs before anything is spawned and the refusal point is unchanged (§2.7, bp-110
        # §3 Q6). A kind dispatches out-of-process only when BOTH the mode is flipped AND that
        # kind has a registered compute half — so an unmigrated kind takes the branch below even
        # with the flag on, and cannot be silently routed through a protocol it was never written
        # for.
        if self.worker_mode == SUBPROCESS and job.kind in self.compute:
            return self._dispatch_to_worker(job)

        handler = self.handlers.get(job.kind)
        if handler is None:
            self.queue.fail(job.id, f"no handler for kind {job.kind!r}")
            return True
        try:
            result = handler(job)
        except Exception as e:  # a job failure must never take down the supervisor
            self.queue.fail(job.id, repr(e))
            return True

        # A handler may have checkpointed + re-queued the job itself; only finalize if it
        # is still RUNNING (cooperative yielding, roadmap §7).
        if self.queue.get(job.id).state == RUNNING:
            self.queue.complete(job.id, result)
        self._record()
        return True

    def _dispatch_to_worker(self, job: Job) -> bool:
        """Run `job`'s compute half out-of-process and land each batch HERE.

        The single-writer property is what this method exists to preserve: the worker returns
        rows, never actions, and every store write in the whole path happens on this thread, in
        `lander`. `dn-supervision-and-liveness` §2.3's fifth arrival of "returns data, never
        actions".

        Deliberately NO wall-clock budget is passed (`run_batches`'s `timeout_s` defaults to 0 =
        unbounded). bp-110 §9 is explicit that this plan defines the budget/escalation config keys
        and consumes NONE of them: enforcement is bp-112's, and finding-0224 — whether a lapsed
        lease may license reclamation at all — is OPEN and is bp-112's graduation to rule on.
        Wiring a deadline here would settle that question by side effect, which is exactly the
        move the finding was filed to prevent. So a wedged worker hangs the tick today, precisely
        as a wedged in-process handler does (finding-0178's status quo, unchanged) — what this
        plan buys is that it is now KILLABLE, not that it is yet killed.
        """
        compute_handler, lander = self.compute[job.kind]
        landed = batches = 0
        # §2.7's rule arms here and disarms in the `finally`: while this job is out, no other
        # tier's model may be made resident (see `model_blocked_tiers`).
        self._in_flight_key = job.load_key
        try:
            for batch in run_batches(job, self.rows or _NoRows()):
                lander(job, batch)                     # the supervisor lands — single-writer holds
                landed += len(batch.rows)
                batches += 1
        except WorkerFailure as e:                     # a dead worker must not take down the loop
            self.queue.fail(job.id, repr(e))
            return True
        except Exception as e:                         # nor must a lander that raises
            self.queue.fail(job.id, repr(e))
            return True
        finally:
            self._in_flight_key = None

        # Identical to the in-process path: a compute half may have checkpointed + re-queued the
        # job, so only finalize if it is still RUNNING (cooperative yielding, roadmap §7).
        if self.queue.get(job.id).state == RUNNING:
            self.queue.complete(job.id, f"worker: landed {landed} rows in {batches} batch(es)")
        self._record()
        return True

    def run(self, *, max_ticks: int | None = None) -> int:
        """Drain the queue cooperatively. Returns the number of jobs dispatched. Stops when
        nothing is runnable (e.g. only heavy jobs remain while the owner is present)."""
        n = 0
        while max_ticks is None or n < max_ticks:
            if not self.tick():
                break
            n += 1
        return n

    def _record(self) -> None:
        if self.telemetry is None:
            return
        self.telemetry.record_vital("queue.depth", self.queue.depth(),
                                    unit="jobs", source="scheduler")
        self.telemetry.record_vital("model.load_seconds", self.loader.last_load_seconds,
                                    unit="s", source="scheduler")
