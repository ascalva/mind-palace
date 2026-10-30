"""Compressed vectors, measured: recall@10 against float32 for each storage lever (step C).

    uv run python -m eval.quantization_bench [--corpus papers|code|all] [--no-lance] [--out PATH]

Step C of the shared-vectors build plan (docs/brainstorms/shared-vectors.md). The vectors are most
of the palace's bytes — 508.6 MB as float32 at 768 dimensions, 453 MB of it the papers — and the
levers that shrink them are int8 scalar quantization, binary codes with float rescoring, product
quantization (IVF-PQ) and Matryoshka truncation. Each is measured the way it matters to retrieval:
of the ten atoms a query gets back today (exact cosine over float32, what `VectorStore.search`
returns), how many does it still get back? recall@10 with a bootstrap 95% interval, the share of
queries that lose nothing, the worst query, and whether the first hit survives (top-1).

Two engines, on purpose:

* numpy, flat over every vector: each quantizer alone — the information it throws away, with no
  index error mixed in. The dot product of ±1 codes is d − 2·Hamming, so ranking by it IS ranking
  by Hamming distance, and the binary path runs through the same BLAS call as the rest.
* LanceDB, over a scratch copy of the vectors in a temporary directory: what production could
  serve — a float16 vector column searched flat (half the bytes on disk, measured), and the indexes
  IVF_FLAT (partitions alone: the control that separates IVF error from quantization error),
  IVF_PQ, IVF_SQ (int8) and IVF_RQ (RaBitQ) at 1 bit — the native form of binary codes with float
  rescoring — and at the package's 8-bit default, under cosine and dot (the 8-bit rows record a
  defect of lancedb 0.33.0, kept so a later version can be checked against them) — with build
  time, bytes and query latency. The live stores are only read; nothing is indexed in place.

Query families, reported apart (the palace's own queries are still few):

* real — every `palace_search` the Ambassador has issued, read from data/eval/palace-queries.json
  (extracted read-only from OpenCode and Open WebUI; two by 2026-10-30);
* titles — each paper's title, the topical shape of a curated search;
* owner — the owner's own notes and turns (MIRROR_READ), asked of the papers;
* self — stored vectors as queries, the query's own atom excluded: the palace's internal neighbour
  searches (relate, dedupe, neighbors);
* probes — the code lane's golden probes (eval/code_probes.py), on the code corpus.

Controls: float32 against itself (recall 1 by construction: checks the harness); LanceDB flat
against numpy (checks that the ground truth is what the engine returns); and for Matryoshka, the
first-d prefix against the last 256 dimensions, a random d-coordinate subset and a random
orthonormal projection to d, beside each 256-block's share of the corpus variance. If
EmbeddingGemma-2 kept v1's Matryoshka training the prefix clearly beats all three; if not, they
land together — the plan's "verify first", measured rather than read off a model card.

Run it in the live checkout: the gitignored `config/ouroboros.toml` picks the embedder and `data/`
holds the stores. A worktree has neither, and would measure the committed defaults' embedder.

Read-only for the palace. Query vectors are cached in data/eval/quantization-queries.json
(gitignored: it holds the owner's words); --out receives numbers only.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import tempfile
import time
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass
from datetime import date
from importlib.metadata import version
from pathlib import Path
from typing import Any

import numpy as np
import numpy.typing as npt

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))  # repo root on path
K = 10
SEED = 20261030
QUERY_CACHE = Path("data/eval/quantization-queries.json")       # relative to the palace root
REAL_QUERIES = Path("data/eval/palace-queries.json")
_TITLE_TAG = re.compile(r"^\[[^\]]*\]\s*")                      # "[unreviewed · OpenAI <date>] "

F32 = npt.NDArray[np.float32]
F64 = npt.NDArray[np.float64]
I64 = npt.NDArray[np.int64]
Run = Callable[[F32, I64 | None], I64]


# ── the measuring instruments (pure; pinned by tests/unit/test_quantization_bench.py) ──────────

def normalize(x: F32) -> F32:
    """Unit rows (a zero row stays zero), so cosine is a dot product."""
    norms = np.linalg.norm(x, axis=1, keepdims=True)
    return np.asarray(x / np.where(norms == 0.0, 1.0, norms), dtype=np.float32)


def topk(scores: F32, k: int) -> I64:
    """Per row, the column indices of the k largest scores, best first."""
    part = np.argpartition(-scores, k - 1, axis=1)[:, :k]
    order = np.argsort(-np.take_along_axis(scores, part, axis=1), axis=1, kind="stable")
    return np.asarray(np.take_along_axis(part, order, axis=1), dtype=np.int64)


def search(queries: F32, corpus: F32, k: int, exclude: I64 | None = None,
           block: int = 256) -> I64:
    """Exact top-k by dot product, a block of queries at a time. `exclude[i]`, when given, is the
    corpus row query i must not return: how a stored vector asks for its neighbours."""
    out = np.empty((len(queries), k), dtype=np.int64)
    for s in range(0, len(queries), block):
        scores = np.asarray(queries[s:s + block] @ corpus.T, dtype=np.float32)
        if exclude is not None:
            scores[np.arange(len(scores)), exclude[s:s + block]] = -np.inf
        out[s:s + block] = topk(scores, k)
    return out


def rescore(queries: F32, corpus: F32, candidates: I64, k: int, block: int = 64) -> I64:
    """Re-rank each query's candidate rows by exact dot product and keep the best k: the second
    stage of every two-stage scheme. The candidates' own order plays no part."""
    out = np.empty((len(queries), k), dtype=np.int64)
    for s in range(0, len(queries), block):
        cand = candidates[s:s + block]
        scores = np.asarray(np.einsum("qd,qcd->qc", queries[s:s + block], corpus[cand]),
                            dtype=np.float32)
        out[s:s + block] = np.take_along_axis(cand, topk(scores, k), axis=1)
    return out


def recall(truth: I64, got: I64) -> F64:
    """Per query, the share of the true top-k that `got` returned; order within the k ignored."""
    k = truth.shape[1]
    return np.array([len(set(t.tolist()) & set(g.tolist())) / k
                     for t, g in zip(truth, got, strict=True)], dtype=np.float64)


def summarize(r: F64, top1: npt.NDArray[np.bool_], rng: np.random.Generator) -> dict[str, Any]:
    """Mean recall, its bootstrap 95% interval (20 queries or more), the share of perfect queries,
    the worst query, and the share whose first hit survived."""
    out: dict[str, Any] = {"n": len(r), "recall@10": round(float(r.mean()), 4),
                           "perfect": round(float((r == 1.0).mean()), 4),
                           "min": round(float(r.min()), 2), "top1": round(float(top1.mean()), 4)}
    if len(r) >= 20:
        means = rng.choice(r, size=(2000, len(r)), replace=True).mean(axis=1)
        lo, hi = np.percentile(means, [2.5, 97.5])
        out["ci95"] = [round(float(lo), 4), round(float(hi), 4)]
    return out


def float16_roundtrip(x: F32) -> F32:
    return np.asarray(x.astype(np.float16), dtype=np.float32)


def int8_roundtrip(x: F32) -> F32:
    """Per-dimension min–max int8 codes (256 levels across each dimension's range), decoded: what a
    float query is scored against when the store keeps one byte per dimension."""
    lo, hi = x.min(axis=0), x.max(axis=0)
    scale = np.where(hi > lo, (hi - lo) / 255.0, 1.0).astype(np.float32)
    codes = np.clip(np.rint((x - lo) / scale), 0, 255).astype(np.uint8)
    return np.asarray(codes.astype(np.float32) * scale + lo, dtype=np.float32)


def signs(x: F32, center: F32 | None = None) -> F32:
    """1-bit codes as ±1 floats (dot = d − 2·Hamming). `center` subtracts a mean first, so each
    bit splits the corpus closer to evenly."""
    v = x if center is None else x - center
    return np.where(v >= 0.0, 1.0, -1.0).astype(np.float32)


def prefix(x: F32, d: int) -> F32:
    """The first d dimensions, renormalized: Matryoshka truncation."""
    return normalize(np.ascontiguousarray(x[:, :d]))


def orthonormal(dim: int, d: int, rng: np.random.Generator) -> F32:
    """A random d-dimensional orthonormal basis of R^dim, as columns: the projection control."""
    q, _ = np.linalg.qr(rng.standard_normal((dim, d)))
    return np.asarray(q, dtype=np.float32)


@dataclass(frozen=True)
class Scheme:
    name: str
    bytes_per_vector: float           # what the search keeps resident per vector
    note: str
    run: Run


def _flat(rep: F32, encode: Callable[[F32], F32]) -> Run:
    def run(q: F32, exclude: I64 | None) -> I64:
        return search(encode(q), rep, K, exclude)
    return run


def _two_stage(x: F32, rep: F32, encode: Callable[[F32], F32], widen: int) -> Run:
    def run(q: F32, exclude: I64 | None) -> I64:
        return rescore(q, x, search(encode(q), rep, K * widen, exclude), K)
    return run


def _same(q: F32) -> F32:
    return q


def numpy_schemes(x: F32, rng: np.random.Generator) -> Iterator[Scheme]:
    """Every flat scheme over the unit corpus `x`, one representation at a time: each is a
    corpus-sized matrix, so the next is built only once the caller has measured the last."""
    dim = x.shape[1]
    yield Scheme("float32", 4 * dim, "control: the ground truth against itself", _flat(x, _same))
    rep = float16_roundtrip(x)
    yield Scheme("float16", 2 * dim, "half precision", _flat(rep, _same))
    rep = int8_roundtrip(x)
    yield Scheme("int8", dim, "per-dimension min–max codes, float query", _flat(rep, _same))
    yield Scheme("int8 → rescore ×2", dim, "20 int8 candidates rescored in float32",
                 _two_stage(x, rep, _same, 2))
    rep = signs(x)
    yield Scheme("binary", dim / 8, "sign bits, Hamming distance", _flat(rep, signs))
    for widen in (2, 4, 8, 16, 32):
        yield Scheme(f"binary → rescore ×{widen}", dim / 8,
                     f"{K * widen} Hamming candidates rescored in float32 (vectors on disk)",
                     _two_stage(x, rep, signs, widen))
    mean = np.asarray(x.mean(axis=0), dtype=np.float32)

    def centred(v: F32) -> F32:
        return signs(v, mean)

    rep = signs(x, mean)
    yield Scheme("binary, centred", dim / 8, "sign bits of x − corpus mean", _flat(rep, centred))
    for widen in (4, 16):
        yield Scheme(f"binary, centred → rescore ×{widen}", dim / 8,
                     f"{K * widen} candidates rescored in float32",
                     _two_stage(x, rep, centred, widen))
    for d in (512, 256, 128):
        rep = prefix(x, d)

        def cut(v: F32, d: int = d) -> F32:
            return prefix(v, d)

        yield Scheme(f"Matryoshka {d}", 4 * d, f"first {d} dimensions", _flat(rep, cut))
        if d == 256:
            yield Scheme("Matryoshka 256 → rescore ×4", 4 * d,
                         "40 candidates at 256 dimensions rescored at 768",
                         _two_stage(x, rep, cut, 4))
    rep = normalize(np.ascontiguousarray(x[:, -256:]))

    def suffix(v: F32) -> F32:
        return normalize(np.ascontiguousarray(v[:, -256:]))

    yield Scheme("last 256 dimensions", 4 * 256, "control for Matryoshka 256", _flat(rep, suffix))
    idx = np.sort(rng.choice(dim, 256, replace=False))
    rep = normalize(np.ascontiguousarray(x[:, idx]))

    def subset(v: F32) -> F32:
        return normalize(np.ascontiguousarray(v[:, idx]))

    yield Scheme("random 256 coordinates", 4 * 256, "control for Matryoshka 256",
                 _flat(rep, subset))
    basis = orthonormal(dim, 256, rng)
    rep = normalize(np.asarray(x @ basis, dtype=np.float32))

    def project(v: F32) -> F32:
        return normalize(np.asarray(v @ basis, dtype=np.float32))

    yield Scheme("random projection 256", 4 * 256, "control for Matryoshka 256",
                 _flat(rep, project))


# ── query families and their ground truth ───────────────────────────────────────────────────────

@dataclass(frozen=True)
class Family:
    name: str
    queries: F32
    exclude: I64 | None = None        # per query, the corpus row it is (self queries only)

    def head(self, n: int) -> Family:
        return Family(self.name, self.queries[:n],
                      None if self.exclude is None else self.exclude[:n])


def evaluate(run: Run, families: Sequence[Family], truths: dict[str, I64],
             rng: np.random.Generator) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for fam in families:
        got = run(fam.queries, fam.exclude)
        truth = truths[fam.name][:len(got)]
        out[fam.name] = summarize(recall(truth, got), truth[:, 0] == got[:, 0], rng)
    return out


# ── LanceDB: the indexes production could serve ─────────────────────────────────────────────────

@dataclass(frozen=True)
class IndexSpec:
    kind: str
    sub_vectors: int | None
    nprobes: tuple[int, ...]
    refine: tuple[int | None, ...]
    metric: str = "cosine"            # "dot" ranks unit vectors exactly as cosine does
    num_bits: int | None = None       # None: the package default (8)


LANCE_SWEEP: tuple[IndexSpec, ...] = (
    IndexSpec("IVF_FLAT", None, (8, 32, 128), (None,)),
    IndexSpec("IVF_PQ", 96, (8, 32, 128), (None, 5)),
    IndexSpec("IVF_PQ", 48, (32,), (None, 5)),
    IndexSpec("IVF_SQ", None, (8, 32, 128), (None,)),
    IndexSpec("IVF_RQ", None, (8, 32, 128), (None, 5), num_bits=1),
    IndexSpec("IVF_RQ", None, (32,), (None, 5), num_bits=8),
    IndexSpec("IVF_RQ", None, (32,), (None, 5), metric="dot", num_bits=8),
)


def _dir_bytes(path: Path) -> int:
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())


def lance_runs(raw: F32, families: Sequence[Family], truths: dict[str, I64],
               rng: np.random.Generator, workdir: Path) -> list[dict[str, Any]]:
    """The sweep over a scratch copy of the corpus. Each configuration answers every query; its
    recall is scored against the numpy ground truth, its latency is per query, warm."""
    import pyarrow as pa

    from core.typedshims.lancedb import VectorTable, connect

    n, dim = raw.shape
    db = connect(str(workdir / "bench.lance"))

    def load(name: str, values: npt.NDArray[Any], typ: pa.DataType) -> VectorTable:
        fields: list[tuple[str, pa.DataType]] = [("id", pa.string()),
                                                 ("vector", pa.list_(typ, dim))]
        t = db.create_table(name, schema=pa.schema(fields))
        t.add(pa.table({"id": pa.array([str(i) for i in range(n)]),
                        "vector": pa.FixedSizeListArray.from_arrays(
                            pa.array(np.ascontiguousarray(values).ravel(), type=typ), dim)}))
        return t

    table = load("atoms", raw, pa.float32())
    half = load("atoms16", raw.astype(np.float16), pa.float16())
    indices = workdir / "bench.lance" / "atoms.lance" / "_indices"
    partitions = max(2, round(math.sqrt(n)))

    def data_mb(name: str) -> float:
        return round(_dir_bytes(workdir / "bench.lance" / f"{name}.lance" / "data") / 1e6, 1)

    def answer(t: VectorTable, metric: str, vec: F32, limit: int, nprobes: int | None,
               refine: int | None) -> list[int]:
        q = t.search(vec.tolist()).metric(metric)
        if nprobes is not None:
            q = q.nprobes(nprobes)
        if refine is not None:
            q = q.refine_factor(refine)
        return [int(str(h["id"])) for h in q.select(["id", "_distance"]).limit(limit).to_list()]

    def measure(t: VectorTable, label: str, params: dict[str, Any], metric: str = "cosine",
                nprobes: int | None = None, refine: int | None = None) -> dict[str, Any]:
        for v in max(families, key=lambda f: len(f.queries)).queries[:10]:      # warm up
            answer(t, metric, v, K, nprobes, refine)
        latencies: list[float] = []
        per_family: dict[str, dict[str, Any]] = {}
        for fam in families:
            got = np.full((len(fam.queries), K), -1, dtype=np.int64)
            for i, v in enumerate(fam.queries):
                t0 = time.perf_counter()
                ids = answer(t, metric, v, K + (fam.exclude is not None), nprobes, refine)
                latencies.append(time.perf_counter() - t0)
                if fam.exclude is not None:
                    ids = [j for j in ids if j != int(fam.exclude[i])]
                got[i, :min(K, len(ids))] = ids[:K]
            truth = truths[fam.name][:len(got)]
            per_family[fam.name] = summarize(recall(truth, got), truth[:, 0] == got[:, 0], rng)
        ms = np.array(latencies) * 1000.0
        return {"index": label, **params, "metric": metric, "nprobes": nprobes, "refine": refine,
                "latency_ms": {"p50": round(float(np.percentile(ms, 50)), 2),
                               "p95": round(float(np.percentile(ms, 95)), 2)},
                "families": per_family}

    runs = [measure(table, "flat", {"note": "no index: today's search",
                                    "data_mb": data_mb("atoms")}),
            measure(half, "flat float16", {"note": "float16 vector column, no index",
                                           "data_mb": data_mb("atoms16")})]
    for spec in LANCE_SWEEP:
        before = set(indices.iterdir()) if indices.exists() else set()
        t0 = time.perf_counter()
        table.create_index(metric=spec.metric, index_type=spec.kind, num_partitions=partitions,
                           num_sub_vectors=spec.sub_vectors, num_bits=spec.num_bits)
        build_s = time.perf_counter() - t0
        size = sum(_dir_bytes(p) for p in set(indices.iterdir()) - before)
        label = (spec.kind + (f"/{spec.sub_vectors}" if spec.sub_vectors else "")
                 + (f"/{spec.num_bits}-bit" if spec.num_bits else "")
                 + ("" if spec.metric == "cosine" else f" ({spec.metric})"))
        params = {"partitions": partitions, "build_s": round(build_s, 1),
                  "index_mb": round(size / 1e6, 1), "bytes_per_vector": round(size / n, 1)}
        for nprobes in spec.nprobes:
            for refine in spec.refine:
                runs.append(measure(table, label, params, spec.metric, nprobes, refine))
    return runs


# ── the palace side: corpora and queries (read-only) ────────────────────────────────────────────

def paper_corpus(store: Any) -> tuple[F32, list[str]]:
    """Every current paper atom's vector, once per atom (a shared passage is one vector, as the
    plane stores it), read through the curated clearance; and each document's title."""
    from core.kernel.clearance import CURATED_READ
    from core.stores.plane import atom_id

    reader = store.reader(CURATED_READ)
    titles: dict[str, str] = {}
    for o in reader.occupancies():
        titles.setdefault(o.source_path, o.title)
    seen: set[str] = set()
    vectors: list[F32] = []
    for doc in sorted(titles):
        for r in reader.rows(source_path=doc):
            aid = atom_id(str(r["text"]), str(r["layer"]))
            if aid not in seen:
                seen.add(aid)
                vectors.append(np.asarray(r["vector"], dtype=np.float32))
    if not vectors:
        raise SystemExit("the curated store holds no current paper atoms")
    named = [_TITLE_TAG.sub("", t).strip() for t in titles.values()]
    return np.vstack(vectors), [t for t in named if t]


def code_corpus(store: Any) -> F32:
    """The code lane exactly as a code search sees it: physical rows of class code, current."""
    from core.kernel.clearance import CODE_READ

    pages = [np.asarray([r["vector"] for r in page], dtype=np.float32)
             for page in store.physical_pages(clearance=CODE_READ, where="current = true")]
    if not pages:
        raise SystemExit("the vector store holds no current code rows")
    return np.vstack(pages)


def owner_texts(store: Any) -> list[str]:
    from core.kernel.clearance import MIRROR_READ

    return list(dict.fromkeys(str(r["text"]) for r in store.all_rows(clearance=MIRROR_READ)))


def real_texts() -> list[str]:
    if not REAL_QUERIES.exists():
        return []
    data = json.loads(REAL_QUERIES.read_text(encoding="utf-8"))
    return [str(q["text"]) for q in data.get("queries", [])]


def embed_queries(texts: Sequence[str], fingerprint: str,
                  embed: Callable[[str], list[float]]) -> F32:
    """Query vectors through the live embedder's own query path, cached per (model, template, dim)
    so a re-run measures the same queries without re-embedding them."""
    cache: dict[str, Any] = {}
    if QUERY_CACHE.exists():
        cache = json.loads(QUERY_CACHE.read_text(encoding="utf-8"))
    if cache.get("fingerprint") != fingerprint:
        cache = {"fingerprint": fingerprint, "vectors": {}}
    vectors: dict[str, list[float]] = cache["vectors"]
    missing = [t for t in dict.fromkeys(texts) if t not in vectors]
    for t in missing:
        vectors[t] = embed(t)
    if missing:
        QUERY_CACHE.parent.mkdir(parents=True, exist_ok=True)
        QUERY_CACHE.write_text(json.dumps(cache), encoding="utf-8")
    return normalize(np.asarray([vectors[t] for t in texts], dtype=np.float32))


# ── one corpus, end to end ──────────────────────────────────────────────────────────────────────

def bench(name: str, raw: F32, families: list[Family], rng: np.random.Generator,
          lance: bool, lance_self: int) -> dict[str, Any]:
    x = normalize(raw)
    n, dim = x.shape
    norms = np.linalg.norm(raw, axis=1)
    sizes = " · ".join(f"{f.name} {len(f.queries)}" for f in families)
    print(f"\n{name}: {n:,} vectors × {dim} ({4 * dim * n / 1e6:.1f} MB as float32); "
          f"queries: {sizes}", flush=True)
    truths = {f.name: search(f.queries, x, K, f.exclude) for f in families}
    out: dict[str, Any] = {
        "vectors": n, "dim": dim,
        "norms": {"min": round(float(norms.min()), 4), "mean": round(float(norms.mean()), 4),
                  "max": round(float(norms.max()), 4)},
        "queries": {f.name: len(f.queries) for f in families}, "numpy": [], "lancedb": []}
    var = x.var(axis=0)
    out["variance_share_by_256_block"] = [round(float(var[i:i + 256].sum() / var.sum()), 3)
                                          for i in range(0, dim, 256)]
    print(f"  variance share by 256-dimension block: {out['variance_share_by_256_block']}",
          flush=True)
    for scheme in numpy_schemes(x, rng):
        t0 = time.perf_counter()
        result = evaluate(scheme.run, families, truths, rng)
        out["numpy"].append({"scheme": scheme.name, "bytes_per_vector": scheme.bytes_per_vector,
                             "mb": round(scheme.bytes_per_vector * n / 1e6, 1),
                             "note": scheme.note, "families": result})
        cells = "  ".join(f"{f}: {r['recall@10']:.3f}" for f, r in result.items())
        print(f"  {scheme.name:34} {scheme.bytes_per_vector:>6g} B  {cells}  "
              f"[{time.perf_counter() - t0:.1f} s]", flush=True)
    if lance:
        sweep = [f if f.exclude is None else f.head(lance_self) for f in families]
        with tempfile.TemporaryDirectory(prefix="quantization-bench-") as tmp:
            for run in lance_runs(raw, sweep, truths, rng, Path(tmp)):
                out["lancedb"].append(run)
                cells = "  ".join(f"{f}: {r['recall@10']:.3f}" for f, r in run["families"].items())
                knobs = (f"nprobes {run['nprobes']}, refine {run['refine']}"
                         if run["nprobes"] else "")
                print(f"  lance {run['index']:16} {knobs:24} p50 {run['latency_ms']['p50']:>6} ms"
                      f"  {cells}", flush=True)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--corpus", choices=("papers", "code", "all"), default="all")
    ap.add_argument("--self-queries", type=int, default=500,
                    help="stored vectors sampled as neighbour queries, per corpus")
    ap.add_argument("--lance-self", type=int, default=200,
                    help="how many of those the LanceDB sweep also asks")
    ap.add_argument("--no-lance", action="store_true", help="numpy schemes only")
    ap.add_argument("--out", type=Path, default=ROOT / "docs" / "experiments" /
                    f"vector-quantization-{date.today().isoformat()}.json")
    a = ap.parse_args(argv)
    out_path = a.out.resolve()
    os.chdir(ROOT)                        # config and data paths resolve against the repo root
    from core.sealing import seal

    seal()
    from core.ingest.embed import build_embedder
    from core.kernel.config import get_config
    from core.stores.curated_store import open_curated_store
    from core.stores.vectorstore import open_vector_store
    from eval.code_probes import PROBES

    cfg = get_config()
    missing = [p for p in (cfg.paths.curated_store, cfg.paths.vector_store) if not p.exists()]
    if missing:                           # opening a store creates it: refuse before an empty one
        raise SystemExit(f"no store at {', '.join(map(str, missing))} — run the bench in the "
                         "live checkout (its config/ouroboros.toml and data/)")
    emb = build_embedder(cfg)
    fingerprint = f"{cfg.embedding.model}|{cfg.embedding.query_template}|{cfg.embedding.dim}"
    print(f"embedder {fingerprint}", flush=True)
    rng = np.random.default_rng(SEED)
    report: dict[str, Any] = {"date": date.today().isoformat(), "k": K, "seed": SEED,
                              "embedder": fingerprint, "numpy": np.__version__, "corpora": {}}

    def sample_self(raw: F32) -> Family:
        idx = np.sort(rng.choice(len(raw), size=min(a.self_queries, len(raw)), replace=False))
        return Family("self", normalize(raw[idx]), np.asarray(idx, dtype=np.int64))

    if a.corpus in ("papers", "all"):
        t0 = time.perf_counter()
        raw, titles = paper_corpus(open_curated_store(cfg))
        assert raw.shape[1] == cfg.embedding.dim, "store and configured embedder disagree"
        print(f"papers corpus read in {time.perf_counter() - t0:.0f} s", flush=True)
        families = [Family(name, embed_queries(texts, fingerprint, emb.embed_query))
                    for name, texts in (("real", real_texts()), ("titles", titles),
                                        ("owner", owner_texts(open_vector_store(cfg)))) if texts]
        families.append(sample_self(raw))
        report["corpora"]["papers"] = bench("papers", raw, families, rng, not a.no_lance,
                                            a.lance_self)
    if a.corpus in ("code", "all"):
        raw = code_corpus(open_vector_store(cfg))
        probes = Family("probes", embed_queries([p.query for p in PROBES], fingerprint,
                                                emb.embed_query))
        report["corpora"]["code"] = bench("code", raw, [probes, sample_self(raw)], rng,
                                          not a.no_lance, a.lance_self)
    report["lancedb"] = version("lancedb")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=1), encoding="utf-8")
    print(f"\nwrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
