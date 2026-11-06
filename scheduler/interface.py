"""Wire the Ambassador / interface gateway into the scheduler (Track B / B1).

The interface substrate (edge gateway, core inbox, the Ambassador) was built but never
*scheduled* — `scheduler/cron.py` had no reference to it. This module is that missing wiring,
and it lives on the SCHEDULER side because it owns the queue: the Ambassador never imports the
scheduler (it stays pure + testable), so the delegation seam (task → gate → queue) and the
completed-result surfacing are injected from here as plain closures over the queue.

Three job kinds (scheduler/router.py):
  * `ambassador`      — the inbox-drain tick: drive `CoreInbox.process_once()` (pinned tier,
                        reactive) — for the scheduled/daemon path — then land what the inbox
                        kept, the library script `capture_inbox` under the role `inbox`, through
                        the one writer (dn-ingress-language §E13).
  * `ambassador_task` — the Ambassador's DELEGATED heavy work: a deep grounded answer on the
                        synthesis tier, run trough-gated by the supervisor, result surfaced later.
  * `inbox_capture`   — the inbox's capture alone, for the records another process kept (`talk`
                        beside a live daemon) or a crash left: enqueued by the record directory's
                        watcher and the daemon's catch-up when records wait, coalesced.

`ConversationRuntime` is the in-process driver the CLI (`scripts/talk.py`) and the e2e test use:
owner text → gateway → inbox → Ambassador → reply, with `run_pending_tasks()` standing in for the
supervisor to complete delegated jobs between turns. The daemon is the one writer: with a daemon
live, the runtime keeps what its inbox kept in the record and lands nothing, and the daemon's
`inbox_capture` lands it; with none live, the runtime lands it after each message, the daemon's
stand-in.
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from agents.ambassador import DeliveredResult, build_ambassador
from agents.ambassador.policy import is_research_request, topic_of
from config.loader import Config
from core.ingest import inbox as inbox_mod
from core.ingest.watch import DirectoryWatcher
from core.interface import CoreInbox
from core.kernel.stores.rawstore import RawStore
from core.librarian import Librarian
from core.research.criteria import DeidentificationError
from edge.interface import GatewayChannel, InterfaceGateway, LocalAdapter
from ops.gate import HumanGate
from scheduler.queue import DONE, PRIORITY_INTERACTIVE, Job, JobQueue
from scheduler.research import RESEARCH_KIND
from scheduler.router import Router

AMBASSADOR_KIND = "ambassador"
AMBASSADOR_TASK_KIND = "ambassador_task"
INBOX_CAPTURE_KIND = "inbox_capture"

Handler = Callable[[Job], "str | None"]


# --- handlers (for the supervisor) -----------------------------------------------------------
def ambassador_inbox_handler(inbox: CoreInbox,
                             land: Callable[[], dict[str, Any]] | None = None) -> Handler:
    """Drain the core inbox each tick (the scheduled path), then land what it kept. The
    per-message Ambassador reasoning happens inside `process_once` via the inbox's responder;
    `land` is the inbox's capture (`core.ingest.inbox.land`), run on the supervisor's thread, so
    the one writer lands it. A capture that fails fails the job after the replies went out: the
    records stay, and the next drain lands them."""
    def handle(_job: Job) -> str:
        n = inbox.process_once()
        if land is None:
            return f"ambassador: processed {n} message(s)"
        return f"ambassador: processed {n} message(s); kept: {land()['effects']}"
    return handle


def ambassador_task_handler(librarian: Librarian) -> Handler:
    """Run one DELEGATED task: a deep grounded answer over the mirror. Returns the answer text,
    which the supervisor stores as the job result for the Ambassador to surface later."""
    def handle(job: Job) -> str:
        query = job.payload.get("query", "")
        return librarian.answer(query).text
    return handle


def inbox_capture_handler(cfg: Config, *, stores: Callable[[], Any]) -> Handler:
    """The inbox's capture as the daemon's own job: the library script `capture_inbox` under the
    role `inbox`, landed by the one writer (`core.ingest.inbox.land`). `stores` opens what the
    writer lands into, the daemon's shared stores."""
    def handle(_job: Job) -> str:
        return f"inbox_capture: {inbox_mod.land(cfg, stores=stores())['effects']}"
    return handle


def enqueue_inbox_capture(queue: JobQueue, router: Router) -> Job:
    """Enqueue the inbox's capture at the interactive priority, as a capture is (the owner's words
    are retrievable soon after they are said). The kind coalesces: one row waits however often
    it is asked."""
    plan = router.plan(INBOX_CAPTURE_KIND, priority=PRIORITY_INTERACTIVE)
    return queue.enqueue(plan.kind, plan.tier, plan.num_ctx, priority=plan.priority)


def enqueue_inbox_capture_if_waiting(queue: JobQueue, router: Router, cfg: Config) -> Job | None:
    """The capture, when the inbox's record holds an exchange not yet landed; else nothing."""
    return enqueue_inbox_capture(queue, router) if inbox_mod.waiting(cfg) else None


def build_inbox_watcher(queue: JobQueue, router: Router, cfg: Config) -> DirectoryWatcher:
    """The record directory's watcher: on a change (a record written, by this daemon's inbox or by
    `talk`'s beside it), the capture is enqueued if records wait. A record the capture removes is a
    change too, and finds none waiting, so the watcher does not loop. The directory must exist:
    the daemon makes it at start (`Record.ensure`)."""
    def on_change() -> None:
        enqueue_inbox_capture_if_waiting(queue, router, cfg)

    return DirectoryWatcher(path=inbox_mod.inbox_dir(cfg), on_change=on_change,
                            debounce_s=1.0, poll_interval_s=5.0)


def daemon_live(cfg: Config) -> bool:
    """Whether a daemon is live, read as the launcher's `_refuse_if_live` reads it: the newest run
    in the run ledger is active and its process exists. A live daemon is the one writer."""
    from ops.lifecycle.launcher import _pid_alive
    from ops.lifecycle.runs import open_run_ledger

    runs = open_run_ledger(cfg)
    try:
        run = runs.last()
    finally:
        runs.close()
    return run is not None and run.active and _pid_alive(run.pid)


def enqueue_ambassador_inbox(queue: JobQueue, router: Router) -> Job:
    """Enqueue one inbox-drain tick (pinned tier, reactive)."""
    plan = router.plan(AMBASSADOR_KIND)
    return queue.enqueue(plan.kind, plan.tier, plan.num_ctx, priority=plan.priority)


# --- the delegation seam (task → gate → queue), injected into the Ambassador -----------------
def build_task_delegation(queue: JobQueue, router: Router, *, gate: HumanGate | None = None,
                          librarian: Librarian | None = None):
    """Return `(delegate, pending_results)` closures over the queue. `delegate` records the task
    in the gate (the routed-request ledger — visible, never auto-approved) and enqueues the
    delegated job; `pending_results` reads completed jobs back for the conversation. The
    Ambassador holds only these closures — never the queue itself.

    A research-shaped TASK (external-literature cue, `is_research_request`) routes to the airlock
    `"research"` kind instead of the general `librarian.answer` path — but ONLY the de-identified
    criteria cross into the payload: `research_criteria` scrubs the raw query at THIS boundary
    (Inv 11), the gate ledger records only the scrubbed topic, and no raw conversation text
    reaches the outbound path. Without a `librarian`, the research route is off (mirror only)."""
    def delegate(query: str, conversation: str) -> str:
        if librarian is not None and is_research_request(query):
            try:
                criteria = librarian.research_criteria(query)         # de-identify at the boundary
            except DeidentificationError:
                # No usable de-identified terms — fail CLOSED (nothing emitted) and fall through to
                # the general answer path (§11: default to librarian.answer on doubt). Never crash.
                criteria = None
            if criteria is not None:
                if gate is not None:
                    gate.submit("research_task", criteria.topic, agent="ambassador")  # scrubbed
                plan = router.plan(RESEARCH_KIND)                     # synthesis tier, background
                job = queue.enqueue(plan.kind, plan.tier, plan.num_ctx, priority=plan.priority,
                                    payload={"criteria": criteria.to_request(),
                                             "conversation": conversation, "topic": criteria.topic})
                return str(job.id)
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
            if job.kind not in (AMBASSADOR_TASK_KIND, RESEARCH_KIND) or job.result is None:
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
    research_handler: Handler | None = None   # None => the research path is not wired (CLI offline)
    land: Callable[[], dict[str, Any]] | None = None   # the inbox's capture; None => kept, unlanded
    daemon_live: Callable[[], bool] = lambda: False    # a live daemon lands what the inbox kept

    def send(self, text: str, *, conversation: str = "default") -> str:
        """Drive one full turn in-process: owner text → reply text (through the real gateway →
        filesystem handoff → core inbox → Ambassador → handoff → gateway path), then land what
        the inbox kept, as the daemon's `ambassador` job does, unless a daemon is live: the daemon
        is then the one writer, and its `inbox_capture` lands the record. A capture that fails is
        said and does not stop the conversation: the reply went out, and the record stays for a
        later turn's capture."""
        self.adapter.receive(text, conversation=conversation)
        self.gateway.submit_inbound()
        self.inbox.process_once()
        self.gateway.deliver_responses()
        if self.land is not None and not self.daemon_live():
            try:
                self.land()
            except Exception as e:      # noqa: BLE001 — said, and the record stays
                print(f"inbox: the capture failed this turn ({type(e).__name__}: {e}); what "
                      "was kept lands on a later one", file=sys.stderr)
        return self.adapter.sent[-1].text if self.adapter.sent else ""

    def run_pending_tasks(self) -> int:
        """Complete any queued delegated tasks (the supervisor's job; the CLI calls this between
        turns so a delegated result is ready to surface on the owner's next message). Handles both
        the general `ambassador_task` and — when wired — the airlock `research` kind.

        Each job is CLAIMED first (`JobQueue.claim`, the queue's one constructor of a RUNNING row),
        so it carries the state, attempt count and lease a supervisor's job carries, and a second
        runner on the same queue cannot take it while it runs. Kinds this runtime has no handler
        for are left QUEUED."""
        handlers: dict[str, Handler] = {AMBASSADOR_TASK_KIND: self.task_handler}
        if self.research_handler is not None:
            handlers[RESEARCH_KIND] = self.research_handler
        done = 0
        while (job := self.queue.claim(kinds=frozenset(handlers))) is not None:
            try:
                self.queue.complete(job.id, handlers[job.kind](job))
            except Exception as e:                       # a task failure must not crash the loop
                self.queue.fail(job.id, repr(e))
            done += 1
        return done


def build_conversation_runtime(config: Config | None = None, *, server=None, embedder=None,
                               store=None, drift=None, airlock=None,
                               live: Callable[[], bool] | None = None) -> ConversationRuntime:
    """Wire the full delegating Ambassador + inbox + gateway + queue for in-process use.

    `server`/`embedder`/`store`/`airlock` are injectable (offline CLI + tests). The delegated-task
    librarian runs on the synthesis tier (heavy work) over the SAME store the Ambassador reads,
    so a delegated result lands where the next conversation can find it. The same librarian gives
    the delegate its `research_criteria` (de-identify) seam; `airlock` defaults to the configured
    core-side airlock, and the research trough handler completes research jobs between turns. The
    inbox's capture lands into the same store, in this process, only while no daemon is live
    (`live`, by default the run ledger read as `_refuse_if_live` reads it); with one live, the
    record waits for the daemon's capture."""
    from config.loader import get_config
    from core.attestation import build_attestor
    from core.ingest.embed import build_embedder
    from core.ingest.writer import Stores
    from core.models import build_model_server
    from core.research.airlock import build_airlock
    from core.stores.catalog import VaultCatalog
    from core.stores.vectorstore import open_vector_store
    from core.stores.versions import open_version_store
    from scheduler.cron import research_handler

    cfg = config or get_config()
    server = server or build_model_server(cfg)
    embedder = embedder or build_embedder(cfg)
    store = store if store is not None else open_vector_store(cfg)
    airlock = airlock if airlock is not None else build_airlock(cfg)

    queue = JobQueue(cfg.paths.data_dir / "queue.sqlite")
    router = Router(cfg)
    gate = HumanGate()
    # One librarian serves both the delegate's `research_criteria` (de-identify) seam and the
    # deep `librarian.answer` task path — the synthesis tier; `research_criteria` uses the
    # deterministic proposer (no model call), so the tier is immaterial to it.
    librarian = Librarian(server=server, embedder=embedder, store=store, tier="synthesis",
                          raw=RawStore(cfg.paths.raw_store), k=cfg.ambassador.retrieval_k)
    delegate, pending_results = build_task_delegation(queue, router, gate=gate, librarian=librarian)
    ambassador = build_ambassador(cfg, delegate=delegate, pending_results=pending_results,
                                  server=server, embedder=embedder, store=store, drift=drift)

    handoff = cfg.interface.handoff_dir
    handoff.mkdir(parents=True, exist_ok=True)
    inbox = CoreInbox(handoff=handoff, respond=ambassador.answer,
                      record=inbox_mod.Record.of(cfg).write)
    adapter = LocalAdapter()
    gateway = InterfaceGateway(adapter=adapter, channel=GatewayChannel(handoff))
    stores = Stores(raw=RawStore(cfg.paths.raw_store), plane=store, embedder=embedder,
                    catalog=VaultCatalog(cfg.paths.vault_catalog),
                    versions=open_version_store(cfg), attestor=build_attestor(cfg))
    return ConversationRuntime(inbox=inbox, gateway=gateway, adapter=adapter, queue=queue,
                               task_handler=ambassador_task_handler(librarian),
                               research_handler=research_handler(airlock, embedder, store),
                               land=lambda: inbox_mod.land(cfg, stores=stores),
                               daemon_live=live or (lambda: daemon_live(cfg)))
