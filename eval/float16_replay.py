"""VEC-1's replay: what float16 storage changed in the code corpus, and what the certificate said.

The quantization experiment (docs/experiments/vector-quantization-2026-10-30.md) found one changed
slot in 2,000 on the code corpus's float16 column. This replays every current code row of a vector
store archived before the float16 migration (A4.3 archives one under `~/mind-palace-archive/`) as
a query for its ten nearest other rows, the bench's "self" family, through LanceDB's own kernels:
once against a float32 copy of the rows, the store before A4, and once against a float16 copy, the
store since. For each query it counts the slots the float16 top ten lost and the certificate
`core/kernel/margin.py` computes from the float16 distances (VEC-1, `docs/LAWS.md` XIII).

Two query forms: the float32 row as the bench asked it, and its float16 rounding, as a stored
vector asks in a float16 store. `--include-self` keeps each row's own match in its top ten, the
convention the formal audit of 2026-11-06 used.

Read-only: the archive is copied into a temporary directory outside the repo and read there; the
results are printed and nothing is written into the repo or the archive.

    uv run python -m eval.float16_replay ~/mind-palace-archive/vectors.lance-pre-f16-<UTC>
"""

from __future__ import annotations

import argparse
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any, cast

import numpy as np
import numpy.typing as npt
import pyarrow as pa

from core.kernel.margin import certify
from core.typedshims.lancedb import VectorTable, connect

K = 10


def _code_rows(archive: Path, workdir: Path) -> tuple[list[str], npt.NDArray[np.float32]]:
    """The archive's current code rows, ids and float32 vectors, read from a copy of it."""
    copy = workdir / "archive"
    shutil.copytree(archive, copy)
    rows = (connect(str(copy)).open_table("chunks").scan()
            .select(["id", "vector"]).where("provenance = 'code' AND current = true")
            .limit(0).to_list())
    ids = [str(r["id"]) for r in rows]
    return ids, np.asarray([cast(list[float], r["vector"]) for r in rows], dtype=np.float32)


def _table(workdir: Path, name: str, vectors: npt.NDArray[Any], typ: pa.DataType) -> VectorTable:
    n, dim = vectors.shape
    db = connect(str(workdir / "replay.lance"))
    t = db.create_table(name, schema=pa.schema([("i", pa.int32()), ("vector", pa.list_(typ, dim))]))
    t.add(pa.table({"i": pa.array(np.arange(n, dtype=np.int32)),
                    "vector": pa.FixedSizeListArray.from_arrays(
                        pa.array(np.ascontiguousarray(vectors).ravel(), type=typ), dim)}))
    return t


def _nearest(t: VectorTable, q: list[float], i: int, keep_self: bool) -> list[tuple[int, float]]:
    """The k + 1 nearest rows to query `i`, as (row, distance), its own row dropped unless kept."""
    hits = t.search(q).metric("cosine").select(["i", "_distance"]).limit(K + 2).to_list()
    out = [(int(cast(int, h["i"])), float(cast(float, h["_distance"]))) for h in hits]
    return (out if keep_self else [h for h in out if h[0] != i])[:K + 1]


def replay(archive: Path, *, include_self: bool) -> list[str]:
    lines: list[str] = []
    with tempfile.TemporaryDirectory(prefix="float16-replay-") as tmp:
        work = Path(tmp)
        ids, y = _code_rows(archive, work)
        n = len(ids)
        t32 = _table(work, "f32", y, pa.float32())
        t16 = _table(work, "f16", y.astype(np.float16), pa.float16())
        lines.append(f"{n} current code rows, {y.shape[1]} dimensions; self "
                     f"{'kept' if include_self else 'excluded'}")
        for form, queries in (("float32 queries", y), ("float16 queries", y.astype(np.float16))):
            t0 = time.perf_counter()
            slots = changed = certified = certified_changed = 0
            widest = 0.0
            for i in range(n):
                q = [float(x) for x in queries[i]]
                truth = {j for j, _ in _nearest(t32, q, i, include_self)[:K]}
                got = _nearest(t16, q, i, include_self)
                margin = certify([d for _, d in got], [j for j, _ in got], K, q)
                lost = len(truth - {j for j, _ in got[:K]})
                certified += margin.certified
                if lost:
                    slots += lost
                    changed += 1
                    certified_changed += margin.certified
                    widest = max(widest, margin.gap)
            secs = time.perf_counter() - t0
            lines.append(f"{form}: {slots} of {K * n} slots changed, in {changed} queries; "
                         f"the widest gap among them {widest:.2e}; certified "
                         f"{certified / n:.1%} of all queries and {certified_changed} of the "
                         f"changed ({secs:.0f} s)")
    return lines


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0] if __doc__ else None)
    ap.add_argument("archive", type=Path, help="a vector store archived before the float16 swap")
    ap.add_argument("--include-self", action="store_true",
                    help="keep each row's own match in its top ten (the audit's convention)")
    a = ap.parse_args(argv)
    for line in replay(a.archive.expanduser(), include_self=a.include_self):
        print(line, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
