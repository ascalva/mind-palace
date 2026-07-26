"""The worker protocol (bp-110 Items 2 and 5) — `dn-supervision-and-liveness` §2.5.

Every test here drives a REAL `python -m scheduler.worker` subprocess. That is the point: the
properties under test (the process is sealed, it holds no store, it dies typed rather than
hanging) are properties of a spawned process, and asserting them in-process would assert nothing
— macOS spawns, so the worker inherits neither the parent's seal nor its import graph.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from scheduler.queue import Job
from scheduler.worker import (
    SELFTEST_EGRESS_KIND,
    SELFTEST_KIND,
    SELFTEST_RAISE_KIND,
    SELFTEST_READ_KIND,
    Batch,
    WorkerFailure,
    WorkerTimeout,
    run_batches,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _job(kind: str, **payload: Any) -> Job:
    return Job(id=1, kind=kind, tier="routine", num_ctx=16384, priority=50, state="running",
               payload=payload, result=None, error=None, attempts=1, checkpoint=None,
               created_at="2026-07-26T00:00:00", started_at=None, finished_at=None)


class FakeRows:
    """A `ReadOnlyRows` the supervisor side serves from. Structural typing — no import needed."""

    def __init__(self, rows: list[dict[str, Any]] | None = None) -> None:
        self.rows = rows or []
        self.calls: list[str] = []

    def all_rows(self, *, provenances: set[str] | None = None) -> list[dict[str, Any]]:
        self.calls.append("all_rows")
        return list(self.rows)

    def rows_for_source(self, source_path: str) -> list[dict[str, Any]]:
        self.calls.append("rows_for_source")
        return [r for r in self.rows if r.get("source_path") == source_path]

    def search(self, vector: list[float], k: int) -> list[dict[str, Any]]:
        self.calls.append("search")
        return list(self.rows)[:k]


# --- Item 2: the round trip -------------------------------------------------------------------


def test_batches_arrive_in_order_with_correct_token_and_items_done():
    got = list(run_batches(_job(SELFTEST_KIND, batches=3, per_batch=2), FakeRows()))
    assert [b.items_done for b in got] == [2, 4, 6]              # monotone, cumulative
    assert [b.token for b in got] == ["cursor-1", "cursor-2", None]   # None = job finished
    assert [len(b.rows) for b in got] == [2, 2, 2]
    assert got[0].rows[0]["text"] == "batch 0 row 0"             # order preserved across the pipe
    assert all(isinstance(b, Batch) for b in got)


def test_a_worker_that_raises_reports_a_typed_failure_rather_than_hanging():
    it = run_batches(_job(SELFTEST_RAISE_KIND, message="kaboom"), FakeRows())
    assert next(it).items_done == 1                              # the partial stream still lands
    with pytest.raises(WorkerFailure) as e:
        next(it)
    assert e.value.exc_type == "ValueError"                      # typed, not a timeout
    assert "kaboom" in e.value.message
    assert "Traceback" in e.value.traceback_text                 # the worker's own stack survives


def test_an_unknown_kind_fails_typed_instead_of_producing_batches():
    with pytest.raises(WorkerFailure) as e:
        list(run_batches(_job("no_such_kind_anywhere"), FakeRows()))
    assert "no compute handler" in str(e.value)


def test_a_read_crosses_the_boundary_and_is_served_by_the_supervisor():
    rows = FakeRows([{"source_path": "/a.md", "text": "keep"},
                     {"source_path": "/b.md", "text": "drop"}])
    got = list(run_batches(_job(SELFTEST_READ_KIND, source_path="/a.md"), rows))
    assert rows.calls == ["rows_for_source"]                     # served in the SUPERVISOR
    assert [r["text"] for r in got[0].rows] == ["keep"]          # answered back into the worker


def test_a_wedged_worker_is_bounded_by_the_wall_clock_and_escalated():
    from scheduler.worker import SELFTEST_SLEEP_KIND
    with pytest.raises(WorkerTimeout):
        list(run_batches(_job(SELFTEST_SLEEP_KIND, seconds=30.0), FakeRows(),
                         timeout_s=1.0, grace_s=2.0))


# --- Item 2's falsifier: V4, the seal, asserted from INSIDE the worker process -----------------


def test_the_worker_process_is_sealed_and_blocks_a_non_loopback_connect():
    """⚑ V4 — the single most serious way this plan can go wrong, and it fails silently.

    macOS uses **spawn**, and `core/sealing.py` is a per-process monkeypatch, so a worker starts
    UNSEALED unless its entrypoint re-applies the guard. This does not read the code: it spawns a
    real worker whose payload attempts a connect to a routable non-loopback literal and asserts
    the guard refused it FROM INSIDE that process.
    """
    got = list(run_batches(_job(SELFTEST_EGRESS_KIND), FakeRows()))
    outcome = got[0].rows[0]
    assert outcome["sealed"] is True, "the worker process did not install the egress guard"
    assert outcome["outcome"].startswith("SealedCoreEgressError"), (
        f"a non-loopback connect was NOT blocked inside the worker: {outcome['outcome']!r} "
        "— a Zone-A process with egress breaches non-negotiable #1"
    )
    assert "CONNECTED" not in outcome["outcome"]


def test_the_seal_is_the_first_thing_the_entrypoint_does():
    """The seal must be the FIRST TWO STATEMENTS (bp-110 §6, `core/runtime.py:38-39`). A guard
    installed after some other call is a guard with a hole in front of it, and the hole would be
    invisible to the runtime test above."""
    import ast

    src = (REPO_ROOT / "scheduler" / "worker.py").read_text(encoding="utf-8")
    fn = next(n for n in ast.walk(ast.parse(src))
              if isinstance(n, ast.FunctionDef) and n.name == "main")
    body = list(fn.body)
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
        body.pop(0)                                              # the docstring is not a statement
    opening: list[str] = []
    for node in body[:2]:
        assert isinstance(node, ast.Expr) and isinstance(node.value, ast.Call), (
            f"statement {node!r} sits in front of the egress guard"
        )
        assert isinstance(node.value.func, ast.Name)
        opening.append(node.value.func.id)
    assert opening == ["seal", "assert_sealed"], f"entrypoint opens with {opening}, not the seal"


def _plant(tmp_path: Path, worker_src: str,
           extra: dict[str, str] | None = None) -> list[Any]:
    """Build a synthetic repo root, drop `worker_src` at `scheduler/worker.py` (plus any extra
    modules), and run the real rule over it. An unresolvable edge is still checked, so a tiny
    tree is enough to exercise the rule without reproducing the repo."""
    from scripts.check_imports import scan_worker_boundary

    (tmp_path / "scheduler").mkdir(parents=True, exist_ok=True)
    (tmp_path / "scheduler" / "worker.py").write_text(worker_src, encoding="utf-8")
    for rel, src in (extra or {}).items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(src, encoding="utf-8")
    return scan_worker_boundary(repo_root=tmp_path)


# --- Item 5: the tier-4 ratchet the capability claim rests on ---------------------------------


def test_the_real_worker_graph_opens_no_store():
    """The ratchet's green state, asserted in the suite as well as the CI gate."""
    from scripts.check_imports import scan_worker_boundary

    assert scan_worker_boundary() == []


def test_the_worker_may_import_the_job_record_but_not_the_queue_writer(tmp_path):
    """The distinction module granularity cannot draw, and the reason the rule reads symbols.
    `Job` is a frozen stdlib-only record and the protocol needs it; `JobQueue` is the single
    writer the whole compute/land split exists to keep in the supervisor."""
    assert _plant(tmp_path, "from scheduler.queue import Job\n") == []
    bad = _plant(tmp_path, "from scheduler.queue import Job, JobQueue\n")
    assert [v.rule for v in bad] == ["worker-store-symbol"]
    assert "JobQueue" in bad[0].imported


def test_a_module_level_store_import_reddens_the_gate(tmp_path):
    """⚑ Item 5's named falsifier: 'adding `from core.stores.vectorstore import
    open_vector_store` to the worker's import graph leaves the gate green.' Plant exactly that."""
    found = _plant(tmp_path, "from core.stores.vectorstore import open_vector_store\n")
    assert found, "a module-level store-opening import left the gate GREEN"
    assert {v.rule for v in found} == {"worker-store-module", "worker-store-symbol"}


def test_a_FUNCTION_LOCAL_store_import_reddens_the_gate(tmp_path):
    """⚑ Item 5's SUBTLER falsifier, and the one with a scar behind it: bp-105's raw `import
    psutil` was FUNCTION-LOCAL and passed every gate in the repo (finding-0198 / bp-106 Item 4
    record it as the exact hole). A rule that only walked module-level imports would reproduce a
    hole we have already been bitten by, so this must red exactly like the module-level case."""
    src = (
        "def compute(job, ctx):\n"
        "    from core.stores.vectorstore import open_vector_store\n"
        "    return open_vector_store()\n"
    )
    found = _plant(tmp_path, src)
    assert found, "a FUNCTION-LOCAL store-opening import left the gate GREEN"
    assert {v.rule for v in found} == {"worker-store-module", "worker-store-symbol"}
    assert all(v.lineno == 2 for v in found)         # reported at the import, inside the function


def test_a_store_reached_TRANSITIVELY_reddens_the_gate(tmp_path):
    """The graph is walked, not just the entrypoint — a lane module that opens a store is caught
    even though `worker.py` itself looks clean. This is what makes the rule survive bp-113/bp-114
    registering real lanes."""
    found = _plant(
        tmp_path,
        "from scheduler.lane import compute\n",
        {"scheduler/lane.py": "from core.kernel.stores.rawstore import RawStore\n"},
    )
    assert found, "a store opened one hop away left the gate GREEN"
    assert [v.path for v in found] == ["scheduler/lane.py", "scheduler/lane.py"]


def test_the_existing_I2_firewall_rules_are_unchanged_and_still_pass():
    """Item 5's invariant: the new rule is added to the existing walker, and the rules that were
    already there keep their meaning and keep passing."""
    from ops.import_lint import scan_core

    assert scan_core() == []


def test_the_worker_does_not_inherit_the_parents_seal_by_default():
    """The control for the test above: a bare `python -c` child of THIS (sealed or unsealed)
    process starts unsealed. If this ever fails, sealing became inheritable and V4's premise —
    the reason `main` must re-seal — would need re-deriving rather than assuming."""
    out = subprocess.run(
        [sys.executable, "-c", "import core.sealing as s; print(s.is_sealed())"],
        capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=60,
    )
    assert out.stdout.strip() == "False", "a spawned process inherited the seal — re-derive V4"
