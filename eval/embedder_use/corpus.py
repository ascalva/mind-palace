"""The corpus instance's vectors, read only, and experiment 5 on its battery: Matryoshka
truncation of the plane's 1,338,585 float16 atoms, flat and rescored, scored on stage 1's 4,714
questions (docs/experiments/embedder-use-2026-11-08.md).

The vectors are the plane's current occupancies of the observed class joined to their atoms'
float16 vectors (stage 1's `eval/corpus/data.py::load_vectors`), opened with `?immutable=1` so the
read writes nothing beside the plane. The query vectors are the ones stage 1 embedded for these
questions with the live query template, read from its cache when the questions are the same
(their texts' hash names the file), and embedded through the cached `Embedder` otherwise.

The search is exact and blocked: the matrix is cut into row blocks, each block converted to
float32 once and multiplied by every query block, and each query keeps its best candidates across
blocks; so a pass over 1.3 million atoms holds one block in float32, never the whole matrix.
"""

from __future__ import annotations

import hashlib
import sqlite3
import time
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

import numpy as np
import numpy.typing as npt

from eval.embedder_use.common import F32, I64, QUERY_SEARCH, Embedder, compare, unit

Log = Callable[[str], None]
F16 = npt.NDArray[np.float16]


def load_vectors(instance: Path, gid: dict[str, int], ids_out: list[str] | None = None
                 ) -> tuple[F16, list[list[int]]]:
    """The plane's current observed atoms: their float16 vectors as stored, and the items (gids)
    holding each; their atom ids appended to `ids_out` when given. Read only."""
    from core.typedshims.lancedb import connect

    store = instance / "data" / "vectors.lance"
    con = sqlite3.connect(f"file:{store / 'plane.sqlite'}?mode=ro&immutable=1", uri=True)
    try:
        occ = con.execute("SELECT source_path, atom_id FROM occ_observed WHERE current = 1")\
            .fetchall()
    finally:
        con.close()
    by_atom: dict[str, list[int]] = {}
    for path, atom in occ:
        g = gid.get(str(path))
        if g is not None:
            by_atom.setdefault(str(atom), []).append(g)
    table = connect(str(store)).open_table("chunks")
    tab = (table.scan().select(["id", "vector"])
           .where("provenance = '' AND source_path = '' AND digest = ''").limit(0).to_arrow())
    ids = [str(a) for a in tab.column("id").to_pylist()]
    keep = np.asarray([a in by_atom for a in ids], dtype=bool)
    col = tab.column("vector").combine_chunks()
    mat = np.asarray(col.values).reshape(len(tab), -1)
    matrix = np.ascontiguousarray(mat[keep]).astype(np.float16, copy=False)
    holders = [by_atom[a] for a, k in zip(ids, keep, strict=True) if k]
    if ids_out is not None:
        ids_out.extend(a for a, k in zip(ids, keep, strict=True) if k)
    return matrix, holders


def query_vectors(instance: Path, texts: list[str], emb: Embedder | None, log: Log) -> F32:
    """Stage 1's query vectors for these texts when its cache holds them, else embedded."""
    key = hashlib.sha256("\x00".join(texts).encode()).hexdigest()[:16]
    f = instance / "results" / "cache" / f"queries-{key}.npy"
    if f.is_file():
        log(f"query vectors: stage 1's cache ({f.name})")
        return unit(np.load(f).astype(np.float32))
    if emb is None:
        raise SystemExit("no cached query vectors and no embedder to make them")
    log("query vectors: embedding")
    return emb.vectors([QUERY_SEARCH.format(text=t[:2000]) for t in texts], log=log)


def blocked_topk(m: F16, q: F32, k: int, *, dims: int, rows: int = 200000, qblock: int = 1024
                 ) -> tuple[I64, F32]:
    """Each query's `k` best rows of `m` by cosine at the first `dims` coordinates (both sides
    renormalized there, the rows held at float16 as stored), best first."""
    n = m.shape[0]
    qd = unit(q[:, :dims].astype(np.float32))
    best_i = np.full((len(q), k), -1, dtype=np.int64)
    best_s = np.full((len(q), k), -np.inf, dtype=np.float32)
    for r0 in range(0, n, rows):
        block = m[r0:r0 + rows, :dims].astype(np.float32)
        if dims < m.shape[1]:
            block = unit(block).astype(np.float16).astype(np.float32)
        else:
            block = unit(block)
        for q0 in range(0, len(q), qblock):
            sims = qd[q0:q0 + qblock] @ block.T
            kk = min(k, sims.shape[1])
            part = np.argpartition(-sims, kth=kk - 1, axis=1)[:, :kk]
            vals = np.take_along_axis(sims, part, axis=1)
            cand_i = np.concatenate([best_i[q0:q0 + qblock], part + r0], axis=1)
            cand_s = np.concatenate([best_s[q0:q0 + qblock], vals], axis=1)
            top = np.argsort(-cand_s, axis=1, kind="stable")[:, :k]
            best_i[q0:q0 + qblock] = np.take_along_axis(cand_i, top, axis=1)
            best_s[q0:q0 + qblock] = np.take_along_axis(cand_s, top, axis=1)
    return best_i, best_s


def items_of(atoms: Sequence[int], holders: list[list[int]], k: int = 10) -> list[int]:
    out: list[int] = []
    for a in atoms:
        for g in holders[int(a)]:
            if g not in out:
                out.append(g)
        if len(out) >= k:
            break
    return out[:k]


def run_corpus_dims(instance: Path, emb: Embedder | None, log: Log, *, depth: int = 100,
                    rescore: int = 50) -> dict[str, Any]:
    """Experiment 5 on the corpus battery: each question's first ten items, flat at 768, 512, 256
    and 128 dimensions, and rescored with the full vectors from the 50 best atoms at each
    truncation."""
    from eval.corpus.battery import questions
    from eval.corpus.data import SOURCES, load
    from eval.corpus.edges import build, twins
    from eval.embedder_use.common import stream_contents
    from eval.embedder_use.tokens import binary_scores

    c = load(instance / "sources", SOURCES)
    rel = build(c)
    tw = twins(rel)
    qs = questions(c, rel, tw, stream_contents(instance, c, set(tw)), per_source=500)
    qv = query_vectors(instance, [q.text for q in qs], emb, log)
    t0 = time.monotonic()
    m, holders = load_vectors(instance, c.gid)
    log(f"vectors: {m.shape[0]} atoms in {time.monotonic() - t0:.0f} s")
    exact = m
    golds = [q.gold for q in qs]
    results: dict[str, dict[str, list[float]]] = {}
    for d in (768, 512, 256, 128):
        t0 = time.monotonic()
        idx, _ = blocked_topk(m, qv, max(depth, rescore), dims=d)
        results[f"D{d}"] = binary_scores([items_of(row[:depth], holders) for row in idx], golds)
        if d < 768:
            ranked = []
            for qi, row in enumerate(idx):
                cand = row[:rescore]
                fine = exact[cand].astype(np.float32) @ qv[qi]
                fine /= np.maximum(np.linalg.norm(exact[cand].astype(np.float32), axis=1), 1e-12)
                ranked.append(items_of(cand[np.argsort(-fine, kind="stable")], holders))
            results[f"D{d}r"] = binary_scores(ranked, golds)
        log(f"  D{d}: recall {np.mean(results[f'D{d}']['recall']):.4f} "
            f"({time.monotonic() - t0:.0f} s)")
    qids = [f"q{i}" for i in range(len(qs))]
    fams = sorted({q.family for q in qs})
    by_family = {fam: {a: round(float(np.mean([r["recall"][i] for i, q in enumerate(qs)
                                               if q.family == fam])), 4)
                       for a, r in results.items()} for fam in fams}
    return {"atoms": int(m.shape[0]), "questions": len(qs), "depth": depth,
            "rescore_candidates": rescore,
            "bytes_per_vector": {f"D{d}": 2 * d for d in (768, 512, 256, 128)},
            "comparison": compare(results, "D768", qids, metrics=("recall", "ndcg", "hit")),
            "by_family_recall": by_family}
