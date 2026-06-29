"""Router + watchdog — the pinned tiny model's role, done in rules first (BUILD-SPEC §9, §13).

RULES FIRST (roadmap §8): the scheduler is rule-capable by design and the tiny router model
is an *enhancement*, not a single point of failure — so Phase 3 ships a deterministic
rule-based router with a seam for the model router and a fall-back-to-rules path. The router
*decides* role/tier/window; deterministic code *acts* (loads, assembles, dispatches) — model
advises, code acts (Invariant 3).

The watchdog reads system vitals (the reactive tier, §9) and raises flags only when a
threshold is crossed; those become high-priority jobs the supervisor dispatches next, at the
following job boundary (roadmap §7) — never a mid-generation interrupt.
"""

from __future__ import annotations

from dataclasses import dataclass

from config.loader import Config
from core.stores.telemetry import TelemetryReader
from scheduler.queue import (
    PRIORITY_BACKGROUND,
    PRIORITY_INTERACTIVE,
    PRIORITY_REACTIVE,
)

# kind -> tier (rules). Unknown kinds default to the routine tier.
_ROUTINE_KINDS = frozenset({"librarian", "query", "assistant", "chat", "converse"})
# `ambassador_task` = the Ambassador's DELEGATED heavy work (the "→ queue" of task→gate→queue):
# a deep grounded synthesis run, trough-gated like dreaming, so the conversation never blocks on it.
_SYNTHESIS_KINDS = frozenset(
    {"curate", "dream", "synthesize", "research", "compact", "ambassador_task"}
)
_ROUTER_KINDS = frozenset({"route", "classify", "watchdog"})
# Kinds that run on the always-pinned tier (config.pinned_model.tier). Two reasons a kind pins:
#   * embed-only maintenance (`vault_sync`) needs NO chat model — pinning makes `ensure_tier` a
#     no-op so the worker slot is never evicted (enqueued at BACKGROUND, see scheduler/vault_sync);
#   * the conversational front door (`ambassador`) must be ALWAYS-WARM + low-latency — it uses the
#     small pinned chat model and delegates heavy work (ambassador-as-reasoning-agent.md §2b).
# Both default to PRIORITY_REACTIVE (responsive); the vault_sync enqueue overrides to BACKGROUND.
_PINNED_KINDS = frozenset({"vault_sync", "ambassador"})


@dataclass(frozen=True)
class Plan:
    kind: str
    tier: str
    num_ctx: int
    priority: int


@dataclass(frozen=True)
class Flag:
    metric: str
    value: float
    threshold: float
    note: str


@dataclass
class Router:
    config: Config

    def tier_for(self, kind: str) -> str:
        if kind in _ROUTER_KINDS or kind in _PINNED_KINDS:
            return self.config.pinned_model.tier
        if kind in _SYNTHESIS_KINDS:
            return "synthesis"
        return "routine"   # default; covers _ROUTINE_KINDS and anything unrecognized

    def _default_priority(self, tier: str) -> int:
        if tier == self.config.pinned_model.tier:
            return PRIORITY_REACTIVE
        if tier in ("synthesis", "stretch"):
            return PRIORITY_BACKGROUND
        return PRIORITY_INTERACTIVE

    def plan(self, kind: str, *, priority: int | None = None) -> Plan:
        """Resolve a job kind to (tier, window, priority) from the rules + the model lineup.
        The window is the model's configured load-time `num_ctx` (§13); same-window jobs
        batch together to avoid reloads."""
        tier = self.tier_for(kind)
        model = self.config.model_for_tier(tier)
        pr = priority if priority is not None else self._default_priority(tier)
        return Plan(kind=kind, tier=tier, num_ctx=model.num_ctx, priority=pr)


@dataclass
class Watchdog:
    reader: TelemetryReader
    min_available_gb: float = 2.0   # raise a flag if memory headroom drops below this

    def check(self) -> list[Flag]:
        """Read the latest vitals and return any crossed thresholds. Deterministic; escalates
        to a model only by enqueuing a job, which the supervisor dispatches by priority."""
        flags: list[Flag] = []
        avail = self.reader.latest("mem.available_gb")
        if avail is not None and avail < self.min_available_gb:
            flags.append(Flag("mem.available_gb", avail, self.min_available_gb,
                              "low memory headroom"))
        return flags
