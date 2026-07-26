"""The worker protocol and the sealed `python -m scheduler.worker` entrypoint.

`dn-supervision-and-liveness` §2.5 decides the execution model: **one worker subprocess per
dispatched job; the compute half runs there and returns bounded batches; the supervisor lands
each batch and owns all clocks.** This module is both ends of that wire — the types, the
worker-side entrypoint, and the supervisor-side driver — deliberately in ONE file (bp-110 §3 Q4).

Why a subprocess with its own `__main__` rather than `multiprocessing` (§3 Q4, decisive):
under `multiprocessing` the worker's import graph **is the parent's**, so the tier-4 ratchet
backing the capability claim would assert nothing. A separate `python -m scheduler.worker` gives
a scoped import graph that `scripts/check_imports.py` can actually walk. The ratchet is only
buildable this way.

Three properties, at the tier each honestly reaches (§2's ladder; overclaiming a tier is the
note's own named foot-gun, so these are stated exactly):

  * **The worker cannot write a store — TIER 2, with a TIER 4 backing.** Capability, not
    discipline: the compute half is handed a `ReadOnlyRows` and nothing else, and in a worker
    process there is no store object in the address space at all. `scripts/check_imports.py`'s
    worker-boundary rule (bp-110 Item 5) re-derives that from the AST rather than trusting this
    docstring. NOT tier 1: the stores are files on a shared disk, and a worker that independently
    opened one could still write — which is exactly what the ratchet forbids reaching for.
  * **The worker is cancellable — TIER 3.** The process boundary makes "stop" a kernel
    operation; SIGKILL is enforced by an authority outside the wedge. An in-process cancel flag
    would be tier-5 cooperation with the very code that stopped cooperating.
  * **The worker is sealed — asserted, never inherited.** See `main` (V4).

⚑ **Nothing here is on by default.** `Supervisor.worker_mode` ships `"inproc"` (note §4) and the
existing `Handler` type is unchanged, so every registered kind keeps running exactly as today.
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import IO, Any, Protocol

from core.sealing import assert_sealed, seal
from scheduler.queue import Job

# ⚑ IMPORT DISCIPLINE FOR THIS MODULE AND EVERYTHING IT REACHES (bp-110 Item 5, tier 4).
# `scripts/check_imports.py --worker` walks this module's transitive first-party import graph and
# fails if any node BINDS a store-opening name (`open_vector_store`, `VectorStore`, `VaultCatalog`,
# `open_derived_store`, `RawStore`, `JobQueue`, …) at module level OR inside a function. Note what
# `from scheduler.queue import Job` does and does not buy: it binds the frozen `Job` RECORD (a
# stdlib-only dataclass) and NOT `JobQueue`, so the queue's writer never becomes reachable here.
# Adding the writer — or a corpus store — to this graph is a build break, by design. A store READ
# is served over the wire by `RowsProxy`, never by opening anything locally.


# --- the compute/land protocol (bp-110 §6, pinned verbatim) ----------------------------------


@dataclass(frozen=True)
class Batch:
    """One bounded unit of computed work, ready to land. `rows` are store-shaped dicts; `token`
    is an opaque resume marker the NEXT batch starts from (None = this job is finished)."""

    rows: tuple[dict[str, Any], ...]
    token: str | None
    items_done: int


class WorkerContext(Protocol):
    """Everything a compute half is allowed to reach. Deliberately thin: the note's §2.3 wording
    is "sources, blobs, and an embedder client, never a `VectorStore`". `rows` is the read half
    that wording is silent about (bp-110 §3 Q3) and is the ONLY store surface exposed."""

    @property
    def rows(self) -> ReadOnlyRows: ...


# The compute half. Registered ALONGSIDE the existing `Handler`, never replacing it.
ComputeHandler = Callable[[Job, "WorkerContext"], "Iterator[Batch]"]

# The landing half — supervisor-side, short, single-writer, never in the worker.
Lander = Callable[[Job, Batch], None]


class ReadOnlyRows(Protocol):
    """The ONLY store surface a compute half ever sees. It exposes reads and cannot express a
    write. It must NOT hold a reachable reference to the writable store — no `._store`, no
    `.__wrapped__`, no closure over the handle that `getattr` or pickling can recover. If the
    writable object is reachable, the capability restriction is decoration, not a capability,
    and the tier-2 claim in §2.3 is false."""

    def all_rows(self, *, provenances: set[str] | None = ...) -> list[dict[str, Any]]: ...
    def rows_for_source(self, source_path: str) -> list[dict[str, Any]]: ...
    def search(self, vector: list[float], k: int) -> list[dict[str, Any]]: ...


class WorkerFailure(RuntimeError):
    """A compute half raised inside the worker, or the worker died. Carries the worker-side
    exception's type and message so the supervisor can `queue.fail` with a real reason instead
    of a timeout — Item 2's "reports a typed failure rather than hanging"."""

    def __init__(self, exc_type: str, message: str, *, traceback_text: str = "") -> None:
        super().__init__(f"{exc_type}: {message}")
        self.exc_type = exc_type
        self.message = message
        self.traceback_text = traceback_text


class WorkerTimeout(WorkerFailure):
    """The worker exceeded its wall-clock deadline and was escalated SIGTERM -> SIGKILL."""

    def __init__(self, seconds: float) -> None:
        super().__init__("WorkerTimeout", f"worker exceeded {seconds}s wall clock")


# --- the wire: length-prefixed JSON lines (§11's parked default, V2-confirmed) ----------------
#
# V2 measured this at a flat ~3.55% of compute across 100/200/500-row batches (bp-110 journal,
# Checkpoint 1), so the format earns its place. JSON — not pickle — is load-bearing, not a taste
# call: pickle would let a live store object cross the boundary, which is precisely the capability
# this design removes (§11, rejected alternatives). The frame is `<byte-length>\n<utf-8 json>` so a
# reader never has to guess where a message ends, and the wire stays inspectable during bring-up.


def _send(stream: IO[bytes], payload: dict[str, Any]) -> None:
    body = json.dumps(payload).encode("utf-8")
    stream.write(b"%d\n%s" % (len(body), body))
    stream.flush()


def _recv(stream: IO[bytes]) -> dict[str, Any] | None:
    """Read one frame. None = the peer closed cleanly (EOF between frames)."""
    header = stream.readline()
    if not header:
        return None
    body = stream.read(int(header.decode("ascii").strip()))
    parsed: dict[str, Any] = json.loads(body.decode("utf-8"))
    return parsed


# --- worker side ------------------------------------------------------------------------------


@dataclass
class RowsProxy:
    """The worker's `ReadOnlyRows`: every read is a request back over the pipe, answered by the
    supervisor from the real store.

    ⚑ This is why the non-leaking requirement in §6 is *structural* here rather than argued. The
    facade cannot leak a writable handle because **no store object exists in this process** —
    there is nothing for `getattr`, pickling, a closure, or `gc.get_referrers` to recover. An
    in-process facade over a live store can never make that claim in Python (a closure cell is
    always reachable via `__closure__`), which is the deeper reason §2.5 puts the compute half in
    a separate process rather than merely wrapping the object. The three verbs below are the whole
    surface the supervisor will answer; there is no write verb to call, and adding one would mean
    adding it to the supervisor's server too.
    """

    stdout: IO[bytes]
    stdin: IO[bytes]
    _next_id: int = 0

    def _ask(self, verb: str, args: dict[str, Any]) -> list[dict[str, Any]]:
        self._next_id += 1
        _send(self.stdout, {"op": "read", "id": self._next_id, "verb": verb, "args": args})
        reply = _recv(self.stdin)
        if reply is None:
            raise WorkerFailure("BrokenPipe", f"supervisor closed the pipe during {verb!r}")
        if reply.get("op") == "read_error":
            raise WorkerFailure(str(reply.get("type", "ReadError")), str(reply.get("message", "")))
        rows: list[dict[str, Any]] = reply["rows"]
        return rows

    def all_rows(self, *, provenances: set[str] | None = None) -> list[dict[str, Any]]:
        return self._ask("all_rows",
                         {"provenances": sorted(provenances) if provenances else None})

    def rows_for_source(self, source_path: str) -> list[dict[str, Any]]:
        return self._ask("rows_for_source", {"source_path": source_path})

    def search(self, vector: list[float], k: int) -> list[dict[str, Any]]:
        return self._ask("search", {"vector": vector, "k": k})


@dataclass(frozen=True)
class _Context:
    """The concrete `WorkerContext` handed to a compute half inside the worker."""

    rows: ReadOnlyRows


# ⚑ The compute registry is STATIC on purpose. A dotted-path handler in the job spec
# (`importlib.import_module(spec["handler"])`) would be the obvious convenience and would make the
# tier-4 ratchet theatre: a static AST walk cannot see a dynamically-imported module, so the worker
# could be handed `core.stores.vectorstore` at runtime and every gate would stay green. Kinds are
# therefore resolved ONLY from names this module statically imports. bp-113/bp-114 register their
# lanes by adding them here (and reddening the ratchet if the lane still reaches for a store).
COMPUTE_HANDLERS: dict[str, ComputeHandler] = {}


def register_compute(kind: str, handler: ComputeHandler) -> None:
    """Register a compute half for `kind`. In-process only — a subprocess worker sees exactly the
    kinds this module statically registers at import (see the note above `COMPUTE_HANDLERS`)."""
    COMPUTE_HANDLERS[kind] = handler


# --- bring-up kinds (proof-only; nothing in production enqueues these) ------------------------
#
# `scheduler/router.py` does not know these kinds and no cron path emits them, so they are
# unreachable from the daemon. They exist because Item 2's acceptance test has to drive a REAL
# subprocess: a synthetic round-trip, a typed failure, a read crossing the boundary, and — the
# one that matters most — a non-loopback connect attempted from INSIDE the worker (V4).

SELFTEST_KIND = "_selftest_batches"
SELFTEST_RAISE_KIND = "_selftest_raise"
SELFTEST_READ_KIND = "_selftest_read"
SELFTEST_EGRESS_KIND = "_selftest_egress"
SELFTEST_ANSWER_KIND = "_selftest_answer"
SELFTEST_SLEEP_KIND = "_selftest_sleep"


def _selftest_batches(job: Job, ctx: WorkerContext) -> Iterator[Batch]:
    """Emit `n` batches of `per` synthetic rows, with a resume token on all but the last."""
    n = int(job.payload.get("batches", 3))
    per = int(job.payload.get("per_batch", 2))
    done = 0
    for b in range(n):
        rows = tuple({"id": f"{job.id}-{b}-{i}", "text": f"batch {b} row {i}"} for i in range(per))
        done += per
        yield Batch(rows=rows, token=(None if b == n - 1 else f"cursor-{b + 1}"), items_done=done)


def _selftest_raise(job: Job, ctx: WorkerContext) -> Iterator[Batch]:
    """Fail after emitting one batch — proves a partial stream still reports a TYPED failure."""
    yield Batch(rows=({"id": "before-the-fall"},), token="cursor-1", items_done=1)
    raise ValueError(job.payload.get("message", "selftest failure"))


def _selftest_read(job: Job, ctx: WorkerContext) -> Iterator[Batch]:
    """Read through the facade and hand the result back — proves reads cross the boundary and
    that the compute half never touches a store."""
    rows = ctx.rows.rows_for_source(str(job.payload.get("source_path", "")))
    yield Batch(rows=tuple(rows), token=None, items_done=len(rows))


def _selftest_egress(job: Job, ctx: WorkerContext) -> Iterator[Batch]:
    """⚑ V4. Attempt a NON-LOOPBACK connect from inside the worker process and report what
    happened. If `main` did not seal, this connect is attempted for real and the row says so —
    which is the only honest way to assert the seal from inside rather than by reading the code."""
    import socket

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2.0)
    try:
        sock.connect(("93.184.216.34", 80))          # a routable literal; never resolved by name
        outcome = "CONNECTED"                        # the failure mode this test exists to catch
    except Exception as e:                           # noqa: BLE001 — the outcome IS the datum
        outcome = f"{type(e).__name__}: {e}"
    finally:
        sock.close()
    yield Batch(rows=({"outcome": outcome, "sealed": _is_sealed_here()},),
                token=None, items_done=1)


def _is_sealed_here() -> bool:
    from core.sealing import is_sealed
    return is_sealed()


def _selftest_answer(job: Job, ctx: WorkerContext) -> Iterator[Batch]:
    """`ambassador_task`'s SHAPE — pure compute, returns text, writes nothing — used as Item 3's
    parallel-run proof lane. Deterministic on purpose: it is the SEAM being proven equivalent
    across modes, and a model call would make the comparison non-deterministic without testing
    anything the seam owns."""
    query = str(job.payload.get("query", ""))
    yield Batch(rows=({"text": f"answer({query})"},), token=None, items_done=1)


def _selftest_sleep(job: Job, ctx: WorkerContext) -> Iterator[Batch]:
    """Sleep past any sane deadline — the target for the wall-clock escalation test."""
    time.sleep(float(job.payload.get("seconds", 30.0)))
    yield Batch(rows=(), token=None, items_done=0)


for _kind, _handler in (
    (SELFTEST_KIND, _selftest_batches),
    (SELFTEST_RAISE_KIND, _selftest_raise),
    (SELFTEST_READ_KIND, _selftest_read),
    (SELFTEST_EGRESS_KIND, _selftest_egress),
    (SELFTEST_ANSWER_KIND, _selftest_answer),
    (SELFTEST_SLEEP_KIND, _selftest_sleep),
):
    register_compute(_kind, _handler)


def _job_from_spec(spec: dict[str, Any]) -> Job:
    """Rebuild the frozen `Job` record from its wire form. Only the record crosses — never a
    queue handle (there is no `JobQueue` in this process to hand it to)."""
    return Job(
        id=int(spec["id"]),
        kind=str(spec["kind"]),
        tier=str(spec["tier"]),
        num_ctx=int(spec["num_ctx"]),
        priority=int(spec["priority"]),
        state=str(spec["state"]),
        payload=dict(spec.get("payload") or {}),
        result=spec.get("result"),
        error=spec.get("error"),
        attempts=int(spec.get("attempts", 0)),
        checkpoint=spec.get("checkpoint"),
        created_at=str(spec.get("created_at", "")),
        started_at=spec.get("started_at"),
        finished_at=spec.get("finished_at"),
        claimed_by_run=spec.get("claimed_by_run"),
        lease_expires_at=spec.get("lease_expires_at"),
    )


def main() -> int:
    """The worker entrypoint. Reads one job spec, streams batches, exits.

    ⚑ V4 — the first two statements are the seal, copied from `core/runtime.py:38-39`, and
    nothing may be inserted above them. macOS spawns rather than forks and `core/sealing.py` is a
    per-process monkeypatch on `socket.socket.connect` (its own docstring says so), so **this
    process starts UNSEALED**. A Zone-A worker with egress breaches non-negotiable #1, and it
    fails SILENTLY — nothing else in the system would notice. This is not defensive; it is the
    invariant.
    """
    seal()           # structural egress guard BEFORE anything else (Invariant 1)
    assert_sealed()

    stdin, stdout = sys.stdin.buffer, sys.stdout.buffer
    spec = _recv(stdin)
    if spec is None:
        return 0
    job = _job_from_spec(spec["job"])
    handler = COMPUTE_HANDLERS.get(job.kind)
    if handler is None:
        _send(stdout, {"op": "error", "type": "KeyError",
                       "message": f"no compute handler for kind {job.kind!r}"})
        return 1
    ctx = _Context(rows=RowsProxy(stdout=stdout, stdin=stdin))
    try:
        for batch in handler(job, ctx):
            _send(stdout, {"op": "batch", "rows": list(batch.rows),
                           "token": batch.token, "items_done": batch.items_done})
    except Exception as e:                           # noqa: BLE001 — every failure is reported
        import traceback
        _send(stdout, {"op": "error", "type": type(e).__name__, "message": str(e),
                       "traceback": traceback.format_exc()})
        return 1
    _send(stdout, {"op": "done"})
    return 0


# --- supervisor side: spawn, serve reads, stream batches ---------------------------------------


def _serve_read(rows: ReadOnlyRows, req: dict[str, Any]) -> dict[str, Any]:
    """Answer ONE read verb from the supervisor's store. The verb set is closed — an unknown verb
    is an error, never a `getattr(store, verb)`, which would turn this server into an arbitrary
    method-call channel and hand the worker back exactly the capability the design removes."""
    verb, args = req.get("verb"), dict(req.get("args") or {})
    try:
        if verb == "all_rows":
            provs = args.get("provenances")
            out = rows.all_rows(provenances=set(provs) if provs else None)
        elif verb == "rows_for_source":
            out = rows.rows_for_source(str(args["source_path"]))
        elif verb == "search":
            out = rows.search(list(args["vector"]), int(args["k"]))
        else:
            return {"op": "read_error", "type": "ValueError",
                    "message": f"unknown read verb {verb!r}"}
    except Exception as e:                           # noqa: BLE001 — a store error must not wedge
        return {"op": "read_error", "type": type(e).__name__, "message": str(e)}
    return {"op": "read_result", "id": req.get("id"), "rows": list(out)}


def _terminate(proc: subprocess.Popen[bytes], grace_s: float) -> None:
    """SIGTERM, wait `grace_s`, SIGKILL — the escalation `dn-supervision-and-liveness` §2.5 aims
    ONLY at the worker, never at the supervisor (killing the supervisor mid-landing is how you
    create the partial write the oq-0035 crux worried about). The discipline is borrowed from
    `core/sandbox/runner.py:65-80` (wall-clock deadline, destroy on expiry, a typed timed-out
    result); the harness is not, because `subprocess.run`'s timeout cannot stream — a streaming
    protocol needs `Popen`. Same discipline, one implementation each, no second timeout harness.
    """
    if proc.poll() is not None:
        return
    try:
        proc.send_signal(signal.SIGTERM)
        proc.wait(timeout=grace_s)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=grace_s)
    except OSError:                                  # already reaped
        pass


def run_batches(job: Job, rows: ReadOnlyRows, *, timeout_s: float = 0.0,
                grace_s: float = 30.0,
                python: str | None = None) -> Iterator[Batch]:
    """Spawn `python -m scheduler.worker` for `job` and yield its batches as they arrive.

    The supervisor stays live throughout: it is reading a pipe, not running the compute. Reads
    requested by the worker are served inline from `rows` — the ONLY thing that crosses back.
    `timeout_s = 0` means no wall-clock bound (today's behaviour, finding-0178's status quo).

    Raises `WorkerFailure` (or `WorkerTimeout`) instead of hanging when the compute half dies.
    """
    argv = [python or sys.executable, "-m", "scheduler.worker"]
    # A worker inherits no vault handle and no secrets: it gets a pruned environment carrying only
    # what the interpreter needs to start. Invariant 10 — secrets are never handed to a subprocess
    # that has no business with them.
    env = {k: v for k, v in os.environ.items()
           if k in ("PATH", "HOME", "LANG", "LC_ALL", "TMPDIR", "PYTHONPATH", "VIRTUAL_ENV")}
    env["PYTHONPATH"] = os.pathsep.join(
        p for p in (env.get("PYTHONPATH", ""), str(_repo_root())) if p
    )
    proc = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, env=env, cwd=str(_repo_root()))
    assert proc.stdin is not None and proc.stdout is not None
    deadline = (time.monotonic() + timeout_s) if timeout_s else None
    try:
        _send(proc.stdin, {"op": "run", "job": _spec_from_job(job)})
        while True:
            if deadline is not None and time.monotonic() > deadline:
                _terminate(proc, grace_s)
                raise WorkerTimeout(timeout_s)
            msg = _recv(proc.stdout)
            if msg is None:
                stderr = (proc.stderr.read().decode("utf-8", "replace") if proc.stderr else "")
                raise WorkerFailure("WorkerDied",
                                    f"worker exited {proc.wait()} without a result",
                                    traceback_text=stderr)
            op = msg.get("op")
            if op == "batch":
                yield Batch(rows=tuple(msg["rows"]), token=msg["token"],
                            items_done=int(msg["items_done"]))
            elif op == "read":
                _send(proc.stdin, _serve_read(rows, msg))
            elif op == "done":
                return
            elif op == "error":
                raise WorkerFailure(str(msg.get("type", "Exception")), str(msg.get("message", "")),
                                    traceback_text=str(msg.get("traceback", "")))
            else:
                raise WorkerFailure("ProtocolError", f"unknown worker op {op!r}")
    finally:
        _terminate(proc, grace_s)
        for stream in (proc.stdin, proc.stdout, proc.stderr):
            if stream is not None:
                stream.close()


def _spec_from_job(job: Job) -> dict[str, Any]:
    return {
        "id": job.id, "kind": job.kind, "tier": job.tier, "num_ctx": job.num_ctx,
        "priority": job.priority, "state": job.state, "payload": job.payload,
        "result": job.result, "error": job.error, "attempts": job.attempts,
        "checkpoint": job.checkpoint, "created_at": job.created_at,
        "started_at": job.started_at, "finished_at": job.finished_at,
        "claimed_by_run": job.claimed_by_run, "lease_expires_at": job.lease_expires_at,
    }


def _repo_root() -> str:
    from pathlib import Path
    return str(Path(__file__).resolve().parent.parent)


if __name__ == "__main__":
    raise SystemExit(main())
