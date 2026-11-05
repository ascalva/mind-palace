"""The daemon's side of the door (dn-ingest-door D3, D5): drain the spools into the queue, and
land the door's own kinds under the one writer.

`drain_spool` runs each tick of the serve loop. It makes the spools and drains only the sound
ones (`door.ensure_spools`); every request waiting in one is read as the daemon trusts it
(`door.pending`), compiled under the grant of the role the spool belongs to (the role is the
directory, never a field), checked as the landing would check it, mapped to its kind and payload,
and enqueued; a request the role may not say, or one past its role's share of the queue, is
receipted as refused and dropped. The drain is bounded (`MAX_PER_TICK` requests a tick, `PER_ROLE`
of a role) and nothing in it raises out of it: a request that fails to drain is receipted, set
aside and reported, and the next one is served.

The order of a drain is the door's crash story. For the door's own kinds the daemon first stages
its own copy of the request (`door.stage`, in `queued/`, which only the daemon writes), then
enqueues the job that names it, then writes the receipt, then removes the writer's file; for the
kinds the queue already had (`vault_sync`, `dream`, …) there is no copy, the job carrying no
request. A crash before the receipt leaves the writer's file to be drained again; the landing of
a door kind is idempotent at the request (`door_handler` skips a request receipted as landed or
refused), while a delegated kind may run twice in that window. A crash after the receipt leaves a
file whose id is seen, which the next tick rejects.

The quotas refuse, they do not hold: `QUOTAS` bounds a role's queued door jobs by lane (the
interactive `capture`, and the bulk rest), so a role's dreams never hold its captures, and a
request past its lane's share is refused as busy rather than left to wait.

`door_handler` is the handler for the door's own kinds: it reads the staged request, checks it is
the request that was drained (its sentence's digest and its kind are in the job's payload),
compiles it **again** under the spool's grant (the second check), performs it, and receipts what
landed. A door job a crash left running goes back to the queue (`scheduler.queue`'s requeue set),
and runs again as if it had not started.
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
Extra = Mapping[str, Callable[[ast.Command, door.Request], dict[str, Any]]]

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


def lane_of(kind: str) -> str:
    """The interactive lane is the model's note to itself (`capture`); everything else is bulk."""
    return "interactive" if kind == "capture" else "bulk"


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
            counts[(role, lane_of(job.kind))] += 1
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
        plan = compile_sentence(request.sentence, door.grant_for(role))
        assert isinstance(plan.term, ast.Do)
        door.check_command(plan.term.command, role)
        kind, payload = door.kind_of(plan.term.command)
    except Exception as e:                          # refused, or not landable: receipt and drop
        door.write_receipt(cfg, door.Receipt(rid, role, "", "refused",
                                             detail={"reason": f"{type(e).__name__}: {e}"}))
        path.unlink(missing_ok=True)
        return 0
    lane = lane_of(kind)
    counted = kind in door.DOOR_KINDS or kind not in _IDEMPOTENT_KINDS
    if counted and counts[(role, lane)] >= quotas[lane]:
        door.write_receipt(cfg, door.Receipt(
            rid, role, kind, "refused",
            detail={"reason": f"busy: {counts[(role, lane)]} of the {role} role's {lane} "
                              "requests are queued; ask again when they have landed"}))
        path.unlink(missing_ok=True)
        return 0
    if kind in door.DOOR_KINDS:
        payload = {**payload, "role": role, "request": rid, "digest": request.digest}
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


def door_handler(cfg: Config, *, landers: door.Landers | None = None,
                 extra: Extra | None = None) -> Handler:
    """The handler for the door's own kinds. `extra` lands the kinds the daemon lands with ops
    machinery (`code_observe`), keyed by kind."""
    extra = dict(extra or {})
    L = landers if landers is not None else door.Landers()

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
            plan = compile_sentence(request.sentence, door.grant_for(role))   # the second check
            assert isinstance(plan.term, ast.Do)
            command = plan.term.command
            kind, _ = door.kind_of(command)
            if kind != job.kind:
                raise door.IllScopedSentence(
                    f"the queued request {rid} compiles to {kind}, the job is {job.kind}")
            result = (extra[kind](command, request) if kind in extra
                      else door.perform(command, cfg, L, role=role))
        except Exception as e:
            refused = isinstance(e, door.IllScopedSentence | PermissionError)
            state = "refused" if refused else "failed"
            try:
                door.write_receipt(cfg, door.Receipt(rid, role, kind, state, job=job.id,
                                                     detail={"reason": f"{type(e).__name__}: {e}"}))
                if refused:
                    door.discard_queued(cfg, role, rid)
            except door.IllScopedSentence:
                pass                    # no role or id to receipt under: the job's error is all
            raise
        door.write_receipt(cfg, door.Receipt(rid, role, kind, "landed", job=job.id,
                                             detail=result))
        door.discard_queued(cfg, role, rid)
        return f"door: {kind} landed for {role} ({rid})"

    return handle


def door_handlers(cfg: Config, *, landers: door.Landers | None = None,
                  extra: Extra | None = None) -> dict[str, Handler]:
    """One handler per door kind, for the supervisor's registry."""
    handler = door_handler(cfg, landers=landers, extra=extra)
    return {kind: handler for kind in sorted(door.DOOR_KINDS)}


DIALOGUE_SYNC_KIND = "dialogue_sync"


def dialogue_sync_handler(sync: Callable[[], int]) -> Handler:
    """`do sync dialogue` as the queue's own kind (coalescing, re-runnable): the dialogue sync
    reads the edge readers' handoff files and captures their turns; an edge reader that failed
    fails the job, so the queue shows it, never a receipt that says landed."""
    def handle(_job: Job) -> str:
        code = sync()
        if code != 0:
            raise RuntimeError(f"dialogue sync: an edge reader failed (exit {code})")
        return "dialogue sync: done"
    return handle
