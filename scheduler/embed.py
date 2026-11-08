"""The embed drain as a queue job (dn-two-phase-ingestion D1, D3; ING-20).

Under `[embedding] lazy = true` the writer lands an item complete without its vector and asks for
this job; the drain (`core/ingest/derive.py`) derives the plane rows of every pending item from the
raw store, in the configured batches, through the same stores the writer lands into: one writer
(the supervisor), one job. It first runs the lexical backfill, which lands the units of any item
the lexical index lacks and re-derives the whole index when its tokenizer changed. The kind is
idempotent at the plane, so the queue folds every request into the one row waiting
(`_IDEMPOTENT_KINDS`), and a job a crash left running goes back to the queue and runs again as if
it had not started. It calls the embedder and no chat model, so it
pins (`router._PINNED_KINDS`) and runs at BACKGROUND priority, like `code_sync`.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from config.loader import Config
from core.ingest import ingress
from core.ingest.derive import EMBED_JOB, derive_lexical, drain
from scheduler.queue import PRIORITY_BACKGROUND, Job, JobQueue
from scheduler.router import Router

EMBED_KIND = EMBED_JOB

Handler = Callable[[Job], "str | None"]


def embed_handler(cfg: Config, *, stores: Callable[[], Any] | None = None) -> Handler:
    """The handler for `embed` jobs: the drain over the writer's stores (opened once, on first use;
    the daemon's own when not given), in the configured batches and streams."""
    opened: dict[str, Any] = {}

    def the_stores() -> Any:
        if "s" not in opened:
            opened["s"] = stores() if stores is not None else ingress.build_stores(cfg)
        return opened["s"]

    def handle(_job: Job) -> str:
        # the derived layers in order: the lexical units of any item the index lacks (all of
        # them after a tokenizer change, which resets the index first), then the vectors
        lexical = derive_lexical(the_stores())
        report = drain(the_stores(), batch=cfg.embedding.batch, streams=cfg.embedding.streams)
        lexical_note = f"; lexical: {lexical}" if lexical.items or lexical.rederived else ""
        return f"embed: {report}{lexical_note}"

    return handle


def enqueue_embed(queue: JobQueue, router: Router) -> Job:
    """Enqueue one background drain. The drain is idempotent (a second run finds nothing pending
    and embeds nothing), so duplicate requests fold into the row already waiting."""
    plan = router.plan(EMBED_KIND, priority=PRIORITY_BACKGROUND)
    return queue.enqueue(plan.kind, plan.tier, plan.num_ctx, priority=plan.priority)
