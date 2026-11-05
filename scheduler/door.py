"""The daemon's side of the door (dn-ingest-door D3, D5; dn-door-language §E6, §E7): drain the
spools into the queue, and run the scripts the requests carry under the one writer.

`drain_spool` runs each tick of the serve loop. It makes the spools and drains only the sound
ones (`door.ensure_spools`); every request waiting in one is read as the daemon trusts it
(`door.pending`), compiled under the grant of the role the spool belongs to (the role is the
directory, never a field) and checked under that role, mapped to its kind, lane and payload, and
enqueued; a request the role may not say, or one past its role's share of the queue, is
receipted as refused and dropped. The drain is bounded (`MAX_PER_TICK` requests a tick,
`PER_ROLE` of a role) and nothing in it raises out of it: a request that fails to drain is
receipted, set aside and reported, and the next one is served.

The order of a drain is the door's crash story. For a `script` job the daemon first stages its
own copy of the request (`door.stage`, in `queued/`, which only the daemon writes), then
enqueues the job that names it, then writes the receipt, then removes the writer's file; a bare
call the table maps to one of the queue's own coalescing kinds (`vault_sync`, `dialogue_sync`)
has no copy, the job carrying no request. A crash before the receipt leaves the writer's file to
be drained again; the landing of a door kind is idempotent at the request (`door_handler` skips
a request receipted as landed or refused), while a delegated kind may run twice in that window.
A crash after the receipt leaves a file whose id is seen, which the next tick rejects.

The quotas refuse, they do not hold: `QUOTAS` bounds a role's queued door jobs by lane (the
library scripts the table marks interactive, a capture, and the bulk rest), so a role's syncs
never hold its captures, and a request past its lane's share is refused as busy rather than left
to wait.

`door_handler` is the handler for `script` jobs: it reads the staged request, checks it is the
request that was drained (its sentence's digest and its kind are in the job's payload), compiles
it **again** under the spool's grant (the second check), evaluates its script and lands the plan
through the writer (`door.perform`), and receipts what landed. `library_handler` runs a library
script as the daemon's own job, for the queue's kinds the watcher and the heartbeat enqueue. A
door job a crash left running goes back to the queue (`scheduler.queue`'s requeue set), and runs
again as if it had not started.
"""

from __future__ import annotations

import sys
import time
from collections import Counter
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any, Protocol

from config.loader import Config
from core.ingest import door
from core.sentence import ast
from core.sentence.plan import compile_sentence
from scheduler.queue import _IDEMPOTENT_KINDS, PRIORITY_BACKGROUND, PRIORITY_INTERACTIVE, Job
from scheduler.router import Router

Handler = Callable[[Job], "str | None"]

MAX_PER_TICK = 64             # requests drained a tick: the serve loop keeps its cadence
PER_ROLE = 32                 # of them, at most this many from one role
QUOTAS: Mapping[str, int] = {"interactive": 64, "bulk": 16}   # a role's queued door jobs, by lane
PRUNE_EVERY_S = 3600.0

_last_prune: dict[str, float] = {}


class Enqueues(Protocol):
    """What the drain needs of the queue: `JobQueue.enqueue` and `list`, and a test's recorder."""

    def enqueue(self, kind: str, tier: str, num_ctx: int, *, priority: int = ...,
                payload: dict[str, Any] | None = None) -> Job: ...

    def list(self, state: str | None = None) -> list[Job]: ...


def _stderr(message: str) -> None:
    print(message, file=sys.stderr)


def _door_role(job: Job) -> str | None:
    """The role a queued job was spooled by: the door's own kinds carry `role`, the delegated kinds
    that do not coalesce carry `door`; a coalescing kind is one row however often it is asked."""
    role = job.payload.get("role") if job.kind in door.DOOR_KINDS else job.payload.get("door")
    return str(role) if role else None


def queued_by_lane(queue: Enqueues) -> Counter[tuple[str, str]]:
    """How many door-spooled jobs each (role, lane) has queued."""
    counts: Counter[tuple[str, str]] = Counter()
    for job in queue.list("queued"):
        role = _door_role(job)
        if role is not None:
            counts[(role, str(job.payload.get("lane", "bulk")))] += 1
    return counts


def _maybe_prune(cfg: Config, say: Callable[[str], None]) -> None:
    key, now = str(door.spool_root(cfg)), time.monotonic()
    if now - _last_prune.get(key, -PRUNE_EVERY_S) < PRUNE_EVERY_S:
        return
    _last_prune[key] = now
    try:
        door.prune(cfg)
    except OSError as e:
        say(f"door: pruning failed ({type(e).__name__}: {e})")


def drain_spool(queue: Enqueues, router: Router, cfg: Config, *,
                report: Callable[[str], None] | None = None,
                max_per_tick: int = MAX_PER_TICK, per_role: int = PER_ROLE,
                quotas: Mapping[str, int] = QUOTAS) -> int:
    """Enqueue the waiting requests as the jobs their commands compile to; return how many."""
    say = report or _stderr
    healthy = door.ensure_spools(cfg, report=say)
    _maybe_prune(cfg, say)
    roles = door.waiting(cfg, healthy)
    if not roles:
        return 0                                    # an idle tick reads no queue and no file
    counts = queued_by_lane(queue)
    drained = 0
    for path, request in door.pending(cfg, roles, limit=max_per_tick, per_role=per_role,
                                      report=say):
        try:
            drained += _drain_one(queue, router, cfg, path, request, counts, quotas, say)
        except Exception as e:                      # one request never stops the drain
            say(f"door: request {request.id} of {request.role} could not be drained "
                f"({type(e).__name__}: {e})")
            if path.exists():
                door.reject(path, say, f"{type(e).__name__}: {e}", cfg=cfg,
                            role=request.role)
    return drained


def _drain_one(queue: Enqueues, router: Router, cfg: Config, path: Path, request: door.Request,
               counts: Counter[tuple[str, str]], quotas: Mapping[str, int],
               say: Callable[[str], None]) -> int:
    role, rid = request.role, request.id
    if door.seen(cfg, role, rid):
        door.reject(path, say, "a request id is never reused: this one was drained before")
        return 0
    try:
        plan = compile_sentence(request.sentence, door.grant_for(role), role=role)
        assert isinstance(plan.term, ast.Do)
        kind, payload = door.kind_of(plan.term)
        lane = door.lane_of(plan.term)
    except Exception as e:                          # refused, or not landable: receipt and drop
        door.write_receipt(cfg, door.Receipt(rid, role, "", "refused",
                                             detail={"reason": f"{type(e).__name__}: {e}"}))
        path.unlink(missing_ok=True)
        return 0
    counted = kind in door.DOOR_KINDS or kind not in _IDEMPOTENT_KINDS
    if counted and counts[(role, lane)] >= quotas[lane]:
        door.write_receipt(cfg, door.Receipt(
            rid, role, kind, "refused",
            detail={"reason": f"busy: {counts[(role, lane)]} of the {role} role's {lane} "
                              "requests are queued; ask again when they have landed"}))
        path.unlink(missing_ok=True)
        return 0
    if kind in door.DOOR_KINDS:
        payload = {**payload, "role": role, "request": rid, "digest": request.digest,
                   "lane": lane}
        door.stage(cfg, request)                    # the daemon's copy, before a job names it
    elif kind not in _IDEMPOTENT_KINDS:
        payload = {**payload, "door": role}
    try:
        plan_ = router.plan(kind, priority=PRIORITY_INTERACTIVE if lane == "interactive"
                            else PRIORITY_BACKGROUND)
        job = queue.enqueue(plan_.kind, plan_.tier, plan_.num_ctx, priority=plan_.priority,
                            payload=payload)
    except Exception as e:                          # the queue: receipt, and set the file aside
        reason = f"{type(e).__name__}: {e}"
        say(f"door: request {rid} of {role} failed to enqueue ({reason})")
        door.write_receipt(cfg, door.Receipt(rid, role, kind, "failed",
                                             detail={"reason": reason}))
        door.reject(path, say, reason)          # its `failed` receipt is written above
        return 0
    door.write_receipt(cfg, door.Receipt(rid, role, kind, "queued", job=job.id))
    path.unlink(missing_ok=True)
    if counted:
        counts[(role, lane)] += 1
    return 1


def door_handler(cfg: Config, *, stores: Callable[[], Any] | None = None,
                 library: Callable[[str], Any] | None = None) -> Handler:
    """The handler for `script` jobs. `stores` opens what the writer lands into (once, on first
    use; the daemon's own stores when not given); `library` loads library scripts (the repo's
    `door/` when not given)."""
    opened: dict[str, Any] = {}

    def the_stores() -> Any:
        if "s" not in opened:
            opened["s"] = stores() if stores is not None else door.build_stores(cfg)
        return opened["s"]

    def handle(job: Job) -> str:
        role, rid = str(job.payload.get("role", "")), str(job.payload.get("request", ""))
        kind = ""
        prior = door.read_receipt(cfg, role, rid)
        if prior is not None and prior.state in ("landed", "refused"):
            return f"door: {prior.kind or job.kind} for {role} ({rid}) is {prior.state} already"
        try:
            request = door.read_request(cfg, role, rid)
            # the request that was drained is the one that lands (the review's finding 7)
            if request.digest != str(job.payload.get("digest", "")):
                raise door.IllScopedSentence(
                    f"the queued request {rid} is not the sentence that was drained")
            plan = compile_sentence(request.sentence, door.grant_for(role),     # the second check
                                    role=role)
            assert isinstance(plan.term, ast.Do)
            kind, _ = door.kind_of(plan.term)
            if kind != job.kind:
                raise door.IllScopedSentence(
                    f"the queued request {rid} compiles to {kind}, the job is {job.kind}")
            result = door.perform(plan.term, cfg, role, stores=the_stores(), library=library,
                                  request=rid)
        except Exception as e:
            from core.sentence.interpret import ScriptError

            refused = isinstance(e, door.IllScopedSentence | PermissionError | ScriptError)
            state = "refused" if refused else "failed"
            try:
                door.write_receipt(cfg, door.Receipt(rid, role, kind, state, job=job.id,
                                                     detail={"reason": f"{type(e).__name__}: {e}"}))
                if refused:
                    door.discard_queued(cfg, role, rid)
            except door.IllScopedSentence:
                pass                    # no role or id to receipt under: the job's error is all
            raise
        # a plan whose every effect the writer refused landed nothing: its receipt says so
        effects = result["effects"]
        state = "refused" if effects and set(effects) == {"refused"} else "landed"
        door.write_receipt(cfg, door.Receipt(rid, role, kind, state, job=job.id, detail=result))
        door.discard_queued(cfg, role, rid)
        return f"door: {kind} {state} for {role} ({rid}): {effects}"

    return handle


def door_handlers(cfg: Config, *, stores: Callable[[], Any] | None = None,
                  library: Callable[[str], Any] | None = None) -> dict[str, Handler]:
    """The handler for the door's own kind, for the supervisor's registry."""
    handler = door_handler(cfg, stores=stores, library=library)
    return {kind: handler for kind in sorted(door.DOOR_KINDS)}


def library_handler(cfg: Config, name: str, calls: list[dict[str, Any]], *,
                    stores: Callable[[], Any] | None = None,
                    library: Callable[[str], Any] | None = None) -> Handler:
    """A queue kind run as a library script, the daemon's own job, under the operator's role: the
    watcher's `vault_sync` is `sync_vault`, the dialogue sync is `sync_dialogue` once a reader.
    Each call is compiled and admitted as a request would be; one that fails fails the job after
    the others have run, so the queue shows it, never a summary that says done."""
    from core.sentence.script import quote

    opened: dict[str, Any] = {}

    def the_stores() -> Any:
        if "s" not in opened:
            opened["s"] = stores() if stores is not None else door.build_stores(cfg)
        return opened["s"]

    def handle(_job: Job) -> str:
        done, failed = [], []
        for kwargs in calls:
            args = ", ".join(f"{k}: {quote(v) if isinstance(v, str) else v}"
                             for k, v in kwargs.items())
            text = f"do {name}({args})" if args else f"do {name}"
            try:
                plan = compile_sentence(text, door.grant_for("cli"), role="cli")
                assert isinstance(plan.term, ast.Do)
                done.append(door.perform(plan.term, cfg, "cli", stores=the_stores(),
                                         library=library, refresh=True)["effects"])
            except Exception as e:
                failed.append(f"{text}: {type(e).__name__}: {e}")
        if failed:
            raise RuntimeError("; ".join(failed))
        return f"{name}: {done}"

    return handle


def job_enqueuer(queue: Enqueues, router: Router, *,
                 quotas: Mapping[str, int] = QUOTAS) -> Callable[..., int]:
    """How a script's `run` enqueues a job: its own kind at the background priority, its tier the
    router's; returns the job's id. A coalescing kind folds into the row already waiting, as the
    watcher's and the heartbeat's do. Any other kind is the speaking role's: it carries the role
    and counts against the role's bulk lane, and a start past the lane's share is refused as
    busy, so no request floods the queue (the first form's quotas, which a job a script starts
    would otherwise slip). A request's job is started once: a script job run again after a
    crash finds the job it started and starts no second one."""
    def enqueue(kind: str, args: dict[str, Any], *, role: str, request: str | None = None) -> int:
        if kind in _IDEMPOTENT_KINDS:
            payload = dict(args)
        else:
            if request is not None:
                for j in queue.list():
                    if j.kind == kind and j.payload.get("request") == request:
                        return j.id
            held = queued_by_lane(queue)[(role, "bulk")]
            if held >= quotas["bulk"]:
                raise door.Busy(f"busy: {held} of the {role} role's bulk jobs are queued; ask "
                                "again when they have run")
            payload = {**args, "door": role, "lane": "bulk"}
            if request is not None:
                payload["request"] = request
        plan = router.plan(kind, priority=PRIORITY_BACKGROUND)
        return queue.enqueue(plan.kind, plan.tier, plan.num_ctx, priority=plan.priority,
                             payload=payload).id
    return enqueue


DIALOGUE_SYNC_KIND = "dialogue_sync"
DIALOGUE_READERS = ("openwebui", "opencode")
