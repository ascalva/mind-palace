"""The supervisor — one loop owns the queue and the worker slot (BUILD-SPEC §13; roadmap §7).

Cooperative, job-boundary scheduling:
  1. claim the next eligible job (priority; swap-avoidance within a priority band; heavy
     tiers gated while the owner is present — the foreground check);
  2. make its (tier, window) resident via the two-slot loader, which refuses any load that
     would breach the RAM ceiling (Invariant 8) — such a job is deferred, not crashed;
  3. run its handler to completion (or one checkpointed step), counting *worker* swaps
     (the pinned router doing interstitial work never evicts the worker, roadmap §7);
  4. record vitals (queue depth, model-load time) and repeat.

A reactive escalation is simply a high-priority job; it is dispatched at the next boundary,
never as a mid-generation interrupt. A handler that raises must not take down the loop.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from config.secrets_backend import MintedToken, SecretsBackend
from core.models import MemoryCeilingError
from core.models.loader import TwoSlotLoader
from core.stores.telemetry import TelemetryWriter
from scheduler.presence import Presence
from scheduler.queue import RUNNING, Job, JobQueue

# Tiers that must not run while the owner is actively present (BUILD-SPEC §13).
HEAVY_TIERS = frozenset({"synthesis", "stretch"})

Handler = Callable[[Job], "str | None"]


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
    _worker_key: tuple[str, int] | None = None

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
        return HEAVY_TIERS if self.presence.foreground_active() else frozenset()

    def tick(self) -> bool:
        """Dispatch at most one job. Returns False when nothing is runnable right now."""
        job = self.queue.claim(loaded_key=self._worker_key, blocked_tiers=self.blocked_tiers())
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
