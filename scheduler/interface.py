"""Wire the Ambassador / interface gateway into the scheduler (Track B / B1).

The interface substrate (edge gateway, core inbox, the Ambassador) was built but never
*scheduled* — `scheduler/cron.py` had no reference to it. This module is that missing wiring,
and it lives on the SCHEDULER side because it owns the queue: the Ambassador never imports the
scheduler (it stays pure + testable), so the delegation seam (task → gate → queue) and the
completed-result surfacing are injected from here as plain closures over the queue.

Two job kinds (scheduler/router.py):
  * `ambassador`      — the inbox-drain tick: drive `CoreInbox.process_once()` (pinned tier,
                        reactive) — for the scheduled/daemon path.
  * `ambassador_task` — the Ambassador's DELEGATED heavy work: a deep grounded answer on the
                        synthesis tier, run trough-gated by the supervisor, result surfaced later.

`ConversationRuntime` is the in-process driver the CLI (`scripts/talk.py`) and the e2e test use:
owner text → gateway → inbox → Ambassador → reply, with `run_pending_tasks()` standing in for
the supervisor to complete delegated jobs between turns.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from agents.ambassador import DeliveredResult, build_ambassador
from agents.ambassador.policy import topic_of
from config.loader import Config
from core.interface import CoreInbox
from core.librarian import Librarian
from core.stores.rawstore import RawStore
from edge.interface import GatewayChannel, InterfaceGateway, LocalAdapter
from ops.gate import HumanGate
from scheduler.queue import DONE, QUEUED, Job, JobQueue
from scheduler.router import Router

AMBASSADOR_KIND = "ambassador"
AMBASSADOR_TASK_KIND = "ambassador_task"

Handler = Callable[[Job], "str | None"]


# --- handlers (for the supervisor) -----------------------------------------------------------
def ambassador_inbox_handler(inbox: CoreInbox) -> Handler:
    """Drain the core inbox each tick (the scheduled path). The per-message Ambassador reasoning
    happens inside `process_once` via the inbox's handler."""
    def handle(_job: Job) -> str:
        return f"ambassador: processed {inbox.process_once()} message(s)"
    return handle


def ambassador_task_handler(librarian: Librarian) -> Handler:
    """Run one DELEGATED task: a deep grounded answer over the mirror. Returns the answer text,
    which the supervisor stores as the job result for the Ambassador to surface later."""
    def handle(job: Job) -> str:
        query = job.payload.get("query", "")
        return librarian.answer(query).text
    return handle


def enqueue_ambassador_inbox(queue: JobQueue, router: Router) -> Job:
    """Enqueue one inbox-drain tick (pinned tier, reactive)."""
    plan = router.plan(AMBASSADOR_KIND)
    return queue.enqueue(plan.kind, plan.tier, plan.num_ctx, priority=plan.priority)


# --- the delegation seam (task → gate → queue), injected into the Ambassador -----------------
def build_task_delegation(queue: JobQueue, router: Router, *, gate: HumanGate | None = None):
    """Return `(delegate, pending_results)` closures over the queue. `delegate` records the task
    in the gate (the routed-request ledger — visible, never auto-approved) and enqueues the
    delegated job; `pending_results` reads completed jobs back for the conversation. The
    Ambassador holds only these closures — never the queue itself."""
    def delegate(query: str, conversation: str) -> str:
        if gate is not None:
            gate.submit("delegated_task", query, agent="ambassador")   # visible routed request
        plan = router.plan(AMBASSADOR_TASK_KIND)                        # synthesis tier, background
        job = queue.enqueue(plan.kind, plan.tier, plan.num_ctx, priority=plan.priority,
                            payload={"query": query, "conversation": conversation,
                                     "topic": topic_of(query)})
        return str(job.id)

    def pending_results(conversation: str) -> list[DeliveredResult]:
        out: list[DeliveredResult] = []
        for job in queue.list(DONE):
            if job.kind != AMBASSADOR_TASK_KIND or job.result is None:
                continue
            if job.payload.get("conversation") != conversation:
                continue
            out.append(DeliveredResult(ref=str(job.id), topic=job.payload.get("topic", ""),
                                       text=job.result))
        return out

    return delegate, pending_results


# --- the in-process conversation runtime (CLI + e2e) -----------------------------------------
@dataclass
class ConversationRuntime:
    inbox: CoreInbox
    gateway: InterfaceGateway
    adapter: LocalAdapter
    queue: JobQueue
    task_handler: Handler

    def send(self, text: str, *, conversation: str = "default") -> str:
        """Drive one full turn in-process: owner text → reply text (through the real gateway →
        filesystem handoff → core inbox → Ambassador → handoff → gateway path)."""
        self.adapter.receive(text, conversation=conversation)
        self.gateway.submit_inbound()
        self.inbox.process_once()
        self.gateway.deliver_responses()
        return self.adapter.sent[-1].text if self.adapter.sent else ""

    def run_pending_tasks(self) -> int:
        """Complete any queued delegated tasks (the supervisor's job; the CLI calls this between
        turns so a delegated result is ready to surface on the owner's next message)."""
        done = 0
        for job in self.queue.list(QUEUED):
            if job.kind != AMBASSADOR_TASK_KIND:
                continue
            try:
                self.queue.complete(job.id, self.task_handler(job))
            except Exception as e:                       # a task failure must not crash the loop
                self.queue.fail(job.id, repr(e))
            done += 1
        return done


def build_conversation_runtime(config: Config | None = None, *, server=None, embedder=None,
                               store=None, drift=None) -> ConversationRuntime:
    """Wire the full delegating Ambassador + inbox + gateway + queue for in-process use.

    `server`/`embedder`/`store` are injectable (offline CLI + tests). The delegated-task
    librarian runs on the synthesis tier (heavy work) over the SAME store the Ambassador reads,
    so a delegated result lands where the next conversation can find it."""
    from config.loader import get_config
    from core.ingest.embed import build_embedder
    from core.models import build_model_server
    from core.stores.vectorstore import open_vector_store

    cfg = config or get_config()
    server = server or build_model_server(cfg)
    embedder = embedder or build_embedder(cfg)
    store = store if store is not None else open_vector_store(cfg)

    queue = JobQueue(cfg.paths.data_dir / "queue.sqlite")
    router = Router(cfg)
    gate = HumanGate()
    delegate, pending_results = build_task_delegation(queue, router, gate=gate)
    ambassador = build_ambassador(cfg, delegate=delegate, pending_results=pending_results,
                                  server=server, embedder=embedder, store=store, drift=drift)

    handoff = cfg.interface.handoff_dir
    handoff.mkdir(parents=True, exist_ok=True)
    inbox = CoreInbox(handoff=handoff, handler=ambassador.handler)
    adapter = LocalAdapter()
    gateway = InterfaceGateway(adapter=adapter, channel=GatewayChannel(handoff))
    task_librarian = Librarian(server=server, embedder=embedder, store=store, tier="synthesis",
                               raw=RawStore(cfg.paths.raw_store), k=cfg.ambassador.retrieval_k)
    return ConversationRuntime(inbox=inbox, gateway=gateway, adapter=adapter, queue=queue,
                               task_handler=ambassador_task_handler(task_librarian))
