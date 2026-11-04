"""Latency of the query algebra's sentences on the live palace, against plain vector RAG.

    uv run python eval/query_bench.py [--n 20]

For each sentence: the first (cold) call — stores open lazily, once per process — and the median
of `n` warm calls, through the same `Ambassador.query` the MCP's one command calls (no HTTP). The
`near` sentence is split into its parts: the query embedding, the raw vector top-k (what plain RAG
does), and the algebra's own overhead (compiling = sorts, scopes, the plan; the universe; the
rendering). A sentence this universe cannot answer yet is recorded by its refusal, never skipped.
A synthetic sweep shows how `diffuse`'s free-energy kernel scales with the number of notes (it
inverts an n×n matrix per call). Read-only: nothing is written but the query log.
"""

from __future__ import annotations

import argparse
import os
import statistics
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))  # repo root on path
os.chdir(ROOT)  # config and data paths resolve against the repo root


def _timed(fn: Callable[[], Any], n: int) -> tuple[float, float, Any]:
    t0 = time.perf_counter()
    out = fn()
    cold = time.perf_counter() - t0
    warm = []
    for _ in range(n):
        t0 = time.perf_counter()
        fn()
        warm.append(time.perf_counter() - t0)
    return cold, statistics.median(warm), out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--n", type=int, default=20)
    a = ap.parse_args(argv)

    from core.sealing import seal

    seal()
    from agents.ambassador.mcp import Ambassador
    from core.kernel.provenance import MIRROR_READABLE
    from core.kernel.recursion import DEFAULT_GAMMA
    from core.query import free_energy_distances

    amb = Ambassador()
    eng = amb.engine
    query = "recursion and self-reference"
    notes = [r["source_path"] for r in eng._get("vectors").project(["source_path", "provenance"])
             if r["provenance"] == "authored-solo"]
    note = sorted(set(notes))[0]
    code_ref = "core/query.py"
    edge = next(iter(eng._get("edges").all()), None)

    rows: list[tuple[str, float, float, str]] = []

    def bench(label: str, sentence: str) -> None:
        try:
            cold, warm, out = _timed(lambda: amb.query(sentence), a.n)
        except Exception as e:   # a refusal is a result of the bench, not a crash of it
            rows.append((label, float("nan"), float("nan"), f"{type(e).__name__}: {str(e)[:60]}"))
            return
        rows.append((label, cold, warm, f"{len(out.get('hits', []))} hits"))

    bench("near    mirror k=8", f'top 8 near "{query}"')
    bench("near    curated k=8", 'top 8 near "Kaplansky direct finiteness" over curated')
    bench("diffuse β=1 k=5", f'top 5 diffuse S from "{note}" beta 1.0')
    bench("hybrid  β=1 k=5", f'top 5 (near "{query}" and diffuse S from "{note}" beta 1.0)')
    bench("trace   forward", f'trace "{note}"')
    bench("relate", f'relate "{note}"')
    bench("read", f'read "{note}"')
    for depth in (1, 2, 3):
        bench(f"reach   depth={depth}", f'reach F from "{code_ref}" depth {depth}')
    if edge is not None:
        bench("witness", f'witness "{edge.edge_id}"')

    # SEARCH, decomposed: embedding / raw top-k (plain RAG) / algebra overhead
    emb, store = eng._get("embedder"), eng._get("vectors")
    _, t_embed, vec = _timed(lambda: emb.embed_query(query), a.n)
    _, t_topk, _ = _timed(lambda: store.search(vec, k=8, provenances=MIRROR_READABLE), a.n)
    t_search = next(r[2] for r in rows if r[0].startswith("near    mirror"))

    print(f"store: {store.count()} vector rows · curated {eng._get('curated').count()} rows · "
          f"n={a.n} warm calls per sentence\n")
    print(f"{'sentence':32} {'cold ms':>9} {'warm ms':>9}  result")
    for label, cold, warm, note_text in rows:
        print(f"{label:32} {cold * 1e3:9.1f} {warm * 1e3:9.1f}  {note_text}")
    print(f"\n`near` decomposed (warm medians): query embedding {t_embed * 1e3:.1f} ms · raw "
          f"vector top-k {t_topk * 1e3:.1f} ms (plain RAG = these two) · algebra overhead "
          f"{max(t_search - t_embed - t_topk, 0) * 1e3:.1f} ms")

    print("\n`diffuse` kernel scaling (synthetic σ-backbone, density 6%):")
    rng = np.random.default_rng(0)
    for n in (38, 200, 500, 1000, 2000):
        w = rng.random((n, n))
        w = np.where(w > 0.94, w, 0.0)
        w = np.triu(w, 1) + np.triu(w, 1).T
        t0 = time.perf_counter()
        free_energy_distances(w, beta=1.0, z=DEFAULT_GAMMA)
        print(f"  n={n:5}  {(time.perf_counter() - t0) * 1e3:9.1f} ms")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
