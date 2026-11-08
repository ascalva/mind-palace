"""What a sentence costs on the corpus instance as it grows (dn-corpus-instance §6, stage 1's cost
row): wall time, the Python share, and peak memory against N, by the profile's method
(`docs/experiments/profile-2026-11-06.md`).

    MIND_PALACE_OVERLAY=config/instances/corpus.toml \
        uv run python -m eval.corpus.cost probe --out <results>/cost.jsonl

Each sentence runs in a child process of its own (so its peak memory is its own), under a
watchdog that kills it past `--max-rss-gb` or `--timeout`: the median wall of `--reps` unprofiled
runs on a warm engine, then one cProfile run split into compiled time (NumPy and SciPy, LanceDB
and Arrow, SQLite, and a wait on LanceDB's event loop) and Python at all (everything else). N is
read off the plane at the time of the probe: occupancies (chunks) and items. A sentence killed
by the watchdog is a result, recorded with the limit it hit.
"""

from __future__ import annotations

import argparse
import cProfile
import json
import os
import pstats
import resource
import sqlite3
import statistics
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from core.typedshims.psutil import process_rss_or_none

COMPILED = ("numpy", "scipy", "lancedb", "pyarrow", "lance", "sqlite3", "_sqlite3")


def sentences(sample: dict[str, str]) -> list[str]:
    """The probe's sentences, over the observed stratum (the corpus's one place)."""
    q = sample["query"]
    a = sample["anchor"]
    return [
        f'top 10 near "{q}" over observed',
        f'top 10 diffuse S from "{a}" over observed',
        f'reach S from "{a}" depth 2 over observed',
        f'walk from "{a}" via S{{1,2}} depth 2 over observed',
    ]


def split(stats: pstats.Stats) -> dict[str, float]:
    """cProfile's own time by kind: compiled (the categories above, by file or builtin name),
    a wait (`kqueue`/`select`/`poll`, LanceDB's runtime; a socket's receive, the embedder's
    answer to the query), and Python at all."""
    out = {"compiled": 0.0, "wait": 0.0, "python": 0.0}
    for (fname, _line, func), row in stats.stats.items():   # type: ignore[attr-defined]
        tottime = float(row[2])
        name = f"{fname} {func}".lower()
        if any(k in name for k in ("kqueue", "select.", "poll", "control of 'select",
                                   "recv_into", "_socket.socket", "sendall")):
            out["wait"] += tottime              # LanceDB's runtime, or the embedder's answer
        elif any(f"/{k}/" in fname or f"'{k}." in func or k in func for k in COMPILED) \
                or "sqlite3.connection" in name or "sqlite3.cursor" in name:
            out["compiled"] += tottime
        else:
            out["python"] += tottime
    total = sum(out.values()) or 1.0
    return {**{k: round(v, 4) for k, v in out.items()},
            "python_share": round(out["python"] / total, 4)}


def child(sentence: str, reps: int, vector_store: str = "") -> dict[str, Any]:
    """In the child: a warm engine, `reps` unprofiled runs, one profiled run; on a scratch plane
    when `vector_store` names one."""
    from dataclasses import replace

    from core.kernel.config import get_config
    from core.query import OPERATOR, QueryEngine
    from core.sentence.execute import execute
    from core.sentence.plan import compile_sentence
    from core.sentence.universe import build

    cfg = get_config()
    if vector_store:
        cfg = replace(cfg, paths=replace(cfg.paths, vector_store=Path(vector_store)))
    eng = QueryEngine(cfg)
    plan = compile_sentence(sentence, OPERATOR, role="cli")

    def once() -> Any:
        return execute(plan, build(eng, plan))
    answer = once()                                   # warms the engine and the page cache
    walls = []
    for _ in range(reps):
        t0 = time.perf_counter()
        answer = once()
        walls.append(time.perf_counter() - t0)
    prof = cProfile.Profile()
    prof.enable()
    once()
    prof.disable()
    notes = [str(n) for n in getattr(answer, "notes", [])]
    support = next((n for n in notes if n.startswith("the universe is")), "")
    return {"wall_s": round(statistics.median(walls), 4), "walls": [round(w, 4) for w in walls],
            "hits": len(getattr(answer, "hits", [])), "support": support[:160],
            "split": split(pstats.Stats(prof)),
            "peak_rss_mb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss // 2**20}


def n_now(cfg: Any) -> dict[str, int]:
    """The plane's size now: current occupancies (chunks) and the items holding them."""
    con = sqlite3.connect(f"file:{cfg.paths.vector_store / 'plane.sqlite'}?mode=ro", uri=True)
    try:
        chunks, items = con.execute("SELECT COUNT(*), COUNT(DISTINCT source_path) FROM "
                                    "occ_observed WHERE current = 1").fetchone()
    finally:
        con.close()
    return {"chunks": int(chunks), "items": int(items)}


def scratch_plane(cfg: Any, items: int, out: Path, *, seed: int = 0) -> dict[str, Any]:
    """A plane of `items` items drawn at random from those the corpus plane holds vectors for,
    their rows copied with their vectors (nothing embedded): the fixture a smaller corpus would
    be, for the cost against N below the instance's own size."""
    import shutil

    import numpy as np

    from core.stores.vectorstore import VectorStore, fingerprint_of
    from core.typedshims.lancedb import connect

    con = sqlite3.connect(f"file:{cfg.paths.vector_store / 'plane.sqlite'}?mode=ro", uri=True)
    paths = [str(r[0]) for r in con.execute(
        "SELECT DISTINCT source_path FROM occ_observed WHERE current = 1 ORDER BY source_path")]
    rng = np.random.default_rng(seed)
    pick = sorted(rng.choice(len(paths), size=min(items, len(paths)), replace=False).tolist())
    chosen = [paths[i] for i in pick]
    occ: list[tuple[str, str, int, str, str]] = []
    for i in range(0, len(chosen), 500):
        part = chosen[i:i + 500]
        occ += [(str(a), str(b), int(c), str(d), str(e)) for a, b, c, d, e in con.execute(
            "SELECT source_path, digest, chunk_index, atom_id, title FROM occ_observed WHERE "
            f"current = 1 AND source_path IN ({','.join('?' * len(part))})", part)]
    con.close()
    table = connect(str(cfg.paths.vector_store)).open_table("chunks")
    atoms = sorted({o[3] for o in occ})
    payload: dict[str, tuple[str, list[float]]] = {}
    for i in range(0, len(atoms), 400):
        ids = ", ".join("'" + a.replace("'", "''") + "'" for a in atoms[i:i + 400])
        for r in table.scan().select(["id", "text", "vector"]).where(f"id IN ({ids})")\
                .limit(0).to_list():
            vector = cast(list[float], r["vector"])
            payload[str(r["id"])] = (str(r["text"]), [float(x) for x in vector])
    if out.exists():
        shutil.rmtree(out)
    store = VectorStore(path=out, dim=cfg.embedding.dim, embedder=fingerprint_of(cfg))
    rows = [{"id": f"{p}:{a.split(':', 1)[1]}", "digest": d, "title": t, "source_path": p,
             "chunk_index": ci, "provenance": "observed", "text": payload[a][0],
             "vector": payload[a][1]} for p, d, ci, a, t in occ if a in payload]
    for i in range(0, len(rows), 5000):
        store.add(rows[i:i + 5000])
    return {"items": len(chosen), "chunks": len(rows), "anchor": chosen[0] if chosen else ""}


def probe(out: Path, *, reps: int, max_rss_gb: float, timeout: float,
          sample: dict[str, str], vector_store: str = "",
          n: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    from core.kernel.config import get_config

    cfg = get_config()
    n = n or n_now(cfg)
    rows = []
    for s in sentences(sample):
        t0 = time.monotonic()
        proc = subprocess.Popen([sys.executable, "-m", "eval.corpus.cost", "child", s,
                                 "--reps", str(reps), "--vector-store", vector_store],
                                stdout=subprocess.PIPE, text=True, env=os.environ.copy())
        peak, killed = 0.0, ""
        while proc.poll() is None:
            rss = (process_rss_or_none(proc.pid) or 0) / 2**30
            peak = max(peak, rss)
            if rss > max_rss_gb:
                killed = f"rss above {max_rss_gb} GB"
            elif time.monotonic() - t0 > timeout:
                killed = f"over {timeout:.0f} s"
            if killed:
                proc.kill()
                break
            time.sleep(0.2)
        body = proc.stdout.read() if proc.stdout else ""
        row: dict[str, Any] = {"at": datetime.now(UTC).isoformat(timespec="seconds"),
                               "sentence": s, **n, "peak_rss_gb_watch": round(peak, 2)}
        if killed:
            row["killed"] = killed
        else:
            try:
                row.update(json.loads(body.strip().splitlines()[-1]))
            except (ValueError, IndexError):
                row["error"] = body[-300:]
        rows.append(row)
        with out.open("a") as fh:
            fh.write(json.dumps(row) + "\n")
        print(json.dumps(row), flush=True)
    return rows


def lexical_latency(index_dir: Path, queries: list[str], fractions: tuple[float, ...] = (
        0.01, 0.03, 0.1, 0.3, 1.0), seed: int = 0, reps: int = 3) -> list[dict[str, Any]]:
    """The lexical arm's query latency against N: the index restricted to nested random subsets
    of its units (a sub-index, as a smaller corpus would build), the median over `reps` passes of
    each query's top ten, and the index's bytes at each size."""
    import numpy as np

    from core.ingest.lexical import LexicalIndex

    full = LexicalIndex.load(index_dir)
    rng = np.random.default_rng(seed)
    order = rng.permutation(full.units)
    rows = []
    for f in fractions:
        keep = np.sort(order[: max(1, int(round(f * full.units)))])
        sub = LexicalIndex(full.vocab, full.weights[keep].tocsc())
        times = []
        for _ in range(reps):
            t0 = time.perf_counter()
            for q in queries:
                sub.search(q)
            times.append((time.perf_counter() - t0) / max(1, len(queries)))
        nbytes = sub.weights.data.nbytes + sub.weights.indices.nbytes + sub.weights.indptr.nbytes
        rows.append({"fraction": f, "units": int(len(keep)),
                     "median_ms": round(1000 * statistics.median(times), 3),
                     "matrix_bytes": int(nbytes)})
    return rows


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("probe")
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--reps", type=int, default=3)
    p.add_argument("--max-rss-gb", type=float, default=6.0)
    p.add_argument("--timeout", type=float, default=600.0)
    p.add_argument("--query", default="spectral gap of random graphs")
    p.add_argument("--anchor", default="Graph theory")
    p.add_argument("--scratch", type=int, nargs="*", default=[],
                   help="also probe scratch planes of these many items")
    c = sub.add_parser("child")
    c.add_argument("sentence")
    c.add_argument("--reps", type=int, default=3)
    c.add_argument("--vector-store", default="")
    a = ap.parse_args()
    if a.cmd == "child":
        print(json.dumps(child(a.sentence, a.reps, a.vector_store)))
        return
    from core.kernel.config import get_config

    a.out.parent.mkdir(parents=True, exist_ok=True)
    sample = {"query": a.query, "anchor": a.anchor}
    for k in a.scratch:
        d = get_config().instance.root / "results" / "scratch" / f"plane-{k}"
        n = scratch_plane(get_config(), k, d)
        probe(a.out, reps=a.reps, max_rss_gb=a.max_rss_gb, timeout=a.timeout,
              sample={**sample, "anchor": str(n.pop("anchor"))}, vector_store=str(d), n=n)
    if not a.scratch:
        probe(a.out, reps=a.reps, max_rss_gb=a.max_rss_gb, timeout=a.timeout, sample=sample)


if __name__ == "__main__":
    main()
