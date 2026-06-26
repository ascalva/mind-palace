"""The scheduler — supervisor, durable queue, foreground check, router/watchdog, and the
deterministic context budgeter (BUILD-SPEC §13; roadmap §7).

One supervisor owns the SQLite queue (single-writer); agents are config time-sharing the
two model slots through it. Scheduling is cooperative and acts at job boundaries; the
budgeter fits every invocation to the active model's window. Rules first — the tiny router
model is an enhancement, not a dependency.
"""

from scheduler.budget import (
    BudgetedContext,
    Budgeter,
    BudgetReport,
    ContextParts,
    estimate_tokens,
    suggest_num_ctx,
)
from scheduler.presence import Presence, macos_idle_seconds
from scheduler.queue import (
    PRIORITY_BACKGROUND,
    PRIORITY_DEFAULT,
    PRIORITY_INTERACTIVE,
    PRIORITY_REACTIVE,
    Job,
    JobQueue,
)
from scheduler.router import Flag, Plan, Router, Watchdog
from scheduler.supervisor import HEAVY_TIERS, Supervisor

__all__ = [
    "HEAVY_TIERS",
    "PRIORITY_BACKGROUND",
    "PRIORITY_DEFAULT",
    "PRIORITY_INTERACTIVE",
    "PRIORITY_REACTIVE",
    "BudgetReport",
    "BudgetedContext",
    "Budgeter",
    "ContextParts",
    "Flag",
    "Job",
    "JobQueue",
    "Plan",
    "Presence",
    "Router",
    "Supervisor",
    "Watchdog",
    "estimate_tokens",
    "macos_idle_seconds",
    "suggest_num_ctx",
]
