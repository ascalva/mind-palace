"""Two-phase ingestion, measured (dn-two-phase-ingestion §6; ING-19 to ING-21).

    uv run python -m eval.two_phase_bench [--data DIR] [--cap-chars 1200] [--items N]
                                          [--plans 10] [--port 8081] [--out PATH]
                                          [--phases all|landing|lag]

Against a scratch instance, never a live one: a temporary root holds the vault, the stores and the
lexical index, and the configured embedder is the local llama-server on `--port`. The control set
is a public BEIR collection read from local parquet files (SciFact by default, `~/models/
bench-data/scifact`, the embedder bench's), each document a markdown item of its title and text,
cut at `--cap-chars` so every item is one chunk and the embedder's work is a known count. The same
items land twice, in `--plans` requests each, on two scratch palaces:

1. lazily (`[embedding] lazy = true`): the landing writes the raw object, the lexical units, the
   version, the attestation and the key, and no vector; then the drain derives the vectors, in
   groups of 64 chunks, with the time each item's key was written and the time its vector became
   current recorded, so the lag between landing and vector is a distribution, not a guess;
2. synchronously (`lazy = false`): the landing embeds before it keys, as the default instance does.

The retrieval battery is the collection's test queries with graded relevance, scored at recall@10
and nDCG@10 for three arms, each ranking the items by the stores the landing wrote: lexical (the
BM25 index), semantic (the plane), and both (reciprocal rank fusion of the two rankings). The
embedder is a source of the system (dn-scale-and-attribution §3.4): its attribution is the Shapley
value of the value function over the two sources with `v(∅) = 0`, and its leave-one-out reading
`v({lexical, embedder}) − v({lexical})`. The semantic arm is also scored with half the items
pending (the drain stopped halfway), alone and with the lexical fallback `near` uses for pending
items, and VEC-1's certificate (`search_ranked`) is counted at every drain stage. Nothing here
touches a live store; the scratch root is removed at the end unless `--keep`.

A timing is only as good as the conditions it ran under, so the embedder's busy slots are sampled
every five seconds through each landing and drain, with the machine's load average at the phase's
start and end. `--phases landing` runs the timings alone, as a control: lazy, the drain,
synchronous, then lazy again, so drift in the machine shows as a gap between the two lazy runs.
`--phases lag` lands lazily and drains at once, recording each item's lag from key to vector with
nothing run between the two.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import statistics
import sys
import tempfile
import threading
import time
from collections.abc import Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root on path

from core.ingest import ingress  # noqa: E402
from core.ingest.derive import drain, pending  # noqa: E402
from core.ingest.lexical import fuse  # noqa: E402
from core.ingest.readers import PalaceView  # noqa: E402
from core.ingest.table import build_table  # noqa: E402
from core.kernel.clearance import MIRROR_READ  # noqa: E402
from core.kernel.config import get_config  # noqa: E402
from core.kernel.provenance import Provenance  # noqa: E402
from core.query import OPERATOR  # noqa: E402
from core.sentence import ast  # noqa: E402
from core.sentence.plan import compile_sentence  # noqa: E402

DATA = Path.home() / "models" / "bench-data"
GEMMA: dict[str, Any] = {"model": "embeddinggemma-2", "dim": 768,
                         "query_template": "task: search result | query: {text}",
                         "document_template": "title: none | text: {text}"}
K = 10


# ── the control set ─────────────────────────────────────────────────────────────────────────────

def load_beir(d: Path) -> tuple[dict[str, tuple[str, str]], dict[str, str],
                                dict[str, dict[str, int]]]:
    """A BEIR collection from local parquet files: corpus id → (title, text), the test queries,
    and their graded relevance (the embedder bench's reader)."""
    import pyarrow.parquet as pq

    corpus = {str(r["_id"]): (str(r.get("title") or ""), str(r["text"]))
              for r in pq.read_table(d / "corpus-00000-of-00001.parquet").to_pylist()}
    queries = {str(r["_id"]): str(r["text"])
               for r in pq.read_table(d / "queries-00000-of-00001.parquet").to_pylist()}
    qrels: dict[str, dict[str, int]] = {}
    for i, line in enumerate((d / "test.tsv").read_text().splitlines()):
        if i == 0:
            continue
        qid, did, score = line.split("\t")
        if int(score) > 0:
            qrels.setdefault(qid, {})[did] = int(score)
    return corpus, {q: t for q, t in queries.items() if q in qrels}, qrels


def ndcg_at(ranked: Sequence[str], rels: dict[str, int], k: int = K) -> float:
    dcg = sum((2 ** rels.get(d, 0) - 1) / math.log2(i + 2) for i, d in enumerate(ranked[:k]))
    ideal = sorted(rels.values(), reverse=True)[:k]
    idcg = sum((2 ** r - 1) / math.log2(i + 2) for i, r in enumerate(ideal))
    return dcg / idcg if idcg else 0.0


def recall_at(ranked: Sequence[str], rels: dict[str, int], k: int = K) -> float:
    return len(set(ranked[:k]) & set(rels)) / len(rels)


# ── the scratch palace ──────────────────────────────────────────────────────────────────────────

@dataclass
class Scratch:
    root: Path
    cfg: Any
    stores: Any
    keyed_at: dict[str, float]

    @property
    def vault(self) -> Path:
        return self.root / "vault"

    def run(self, text: str) -> dict[str, Any]:
        plan = compile_sentence(text, OPERATOR, role="cli")
        assert isinstance(plan.term, ast.Do)
        view = PalaceView(build_table(self.cfg), "cli", self.stores.catalog, refresh=False)
        return ingress.perform(plan.term, self.cfg, "cli", stores=self.stores, view=view)


def scratch(root: Path, *, lazy: bool, port: int) -> Scratch:
    """A palace under `root` with the stack's embedder: its own vault, data directory and
    stores, nothing of any instance's."""
    vault, data = root / "vault", root / "data"
    vault.mkdir(parents=True)
    data.mkdir()
    base = get_config()
    cfg = replace(
        base,
        ingestion=replace(base.ingestion, vault=replace(base.ingestion.vault, path=vault)),
        paths=replace(base.paths, data_dir=data, raw_store=data / "raw",
                      vector_store=data / "vectors.lance", derived_store=data / "derived.sqlite",
                      vault_catalog=data / "vault_catalog.sqlite",
                      attestation_store=data / "attestations.sqlite",
                      curated_store=data / "research_curated.lance",
                      telemetry_db=data / "telemetry.duckdb"),
        interface=replace(base.interface, handoff_dir=data / "handoff"),
        embedding=replace(base.embedding, lazy=lazy, model=GEMMA["model"], dim=GEMMA["dim"],
                          query_template=GEMMA["query_template"],
                          document_template=GEMMA["document_template"]),
        runtime=replace(base.runtime, embedding_backend="llamacpp", ports={"embedding": port},
                        api_key_env=""),
        attestation=replace(base.attestation, enabled=False),
    )
    stores = ingress.build_stores(cfg)
    keyed_at: dict[str, float] = {}
    record = stores.catalog.record

    def timed(source_path: str, *a: Any, **k: Any) -> Any:
        out = record(source_path, *a, **k)
        keyed_at[source_path] = time.perf_counter()
        return out

    stores.catalog.record = timed
    return Scratch(root, cfg, stores, keyed_at)


def write_items(vault: Path, items: list[tuple[str, str, str]], cap: int) -> None:
    for did, title, text in items:
        body = text[: max(0, cap - len(title) - 4)] if cap else text
        (vault / f"{did}.md").write_text(f"# {title}\n\n{body}\n", encoding="utf-8")


def land_in_plans(s: Scratch, items: list[tuple[str, str, str]], cap: int,
                  plans: int) -> dict[str, Any]:
    """Land the items in `plans` requests of equal size; return the landing's timings."""
    size = max(1, math.ceil(len(items) / plans))
    t0 = time.perf_counter()
    landed = 0
    per_plan: list[float] = []
    for i in range(0, len(items), size):
        write_items(s.vault, items[i:i + size], cap)
        t1 = time.perf_counter()
        out = s.run("do sync_vault")
        per_plan.append(time.perf_counter() - t1)
        landed += out["effects"].get("landed", 0)
    seconds = time.perf_counter() - t0
    chunks = s.stores.lexical.count() if s.stores.lexical is not None else \
        s.stores.plane.plane.reader(MIRROR_READ).count()
    return {"items": landed, "chunks": chunks, "seconds": round(seconds, 2),
            "items_per_s": round(landed / seconds, 1), "chunks_per_s": round(chunks / seconds, 1),
            "plans": len(per_plan), "plan_seconds_median": round(statistics.median(per_plan), 2),
            "plan_seconds": [round(x, 1) for x in per_plan]}


# ── the battery ─────────────────────────────────────────────────────────────────────────────────

def doc_of(path: str) -> str:
    return Path(path).stem


def lexical_ranking(s: Scratch, query: str, k: int = K) -> list[str]:
    assert s.stores.lexical is not None
    hits = s.stores.lexical.search(query, k=3 * k, classes=[Provenance.AUTHORED_SOLO])
    out: list[str] = []
    for h in hits:
        d = doc_of(h.source_path)
        if d not in out:
            out.append(d)
    return out[:k]


def semantic_ranking(s: Scratch, qvec: list[float], k: int = K) -> list[str]:
    rows = s.stores.plane.search(qvec, k=3 * k, clearance=MIRROR_READ)
    out: list[str] = []
    for r in rows:
        d = doc_of(str(r["source_path"]))
        if d not in out:
            out.append(d)
    return out[:k]


def pending_docs(s: Scratch) -> set[str]:
    return {doc_of(e.source_path)
            for e in pending(s.stores.catalog, s.stores.plane, lexical=s.stores.lexical)}


def battery(s: Scratch, queries: dict[str, str], qrels: dict[str, dict[str, int]],
            qvecs: dict[str, list[float]]) -> dict[str, Any]:
    """Recall@10 and nDCG@10 per arm: lexical, semantic, both (RRF), and `near`'s rule with the
    items pending at this stage ranked by the lexical index beside the vectors (`fallback`)."""
    waiting = pending_docs(s)
    scores: dict[str, dict[str, list[float]]] = {
        arm: {"recall": [], "ndcg": []} for arm in ("lexical", "semantic", "both", "fallback")}
    for qid, text in queries.items():
        rels = qrels[qid]
        lex = lexical_ranking(s, text)
        sem = semantic_ranking(s, qvecs[qid])
        both = fuse([lex, sem], k=K)
        # near's rule: the vectors where they exist, the lexical index where they do not, the two
        # parts each on their own scale; the fused list is the hybrid of the two
        lex_pending = [d for d in lex if d in waiting]
        fallback = fuse([sem, lex_pending], k=K) if lex_pending else sem
        for arm, ranked in (("lexical", lex), ("semantic", sem), ("both", both),
                            ("fallback", fallback)):
            scores[arm]["recall"].append(recall_at(ranked, rels))
            scores[arm]["ndcg"].append(ndcg_at(ranked, rels))
    out: dict[str, Any] = {"queries": len(queries), "pending_items": len(waiting)}
    for arm, m in scores.items():
        out[arm] = {k: round(statistics.fmean(v), 4) for k, v in m.items()}
        out[arm]["recall_se"] = round(statistics.pstdev(m["recall"]) / math.sqrt(len(queries)), 4)
    out["per_query"] = {arm: m["recall"] for arm, m in scores.items()}
    return out


def attribution(b: dict[str, Any], metric: str = "recall") -> dict[str, Any]:
    """The embedder and the lexical index as the two sources of retrieval (SCL-3): the Shapley
    value over `v(∅) = 0`, `v({L})`, `v({E})`, `v({L, E})`, and the leave-one-out readings."""
    v_l, v_e, v_le = b["lexical"][metric], b["semantic"][metric], b["both"][metric]
    phi_e = 0.5 * (v_e - 0.0) + 0.5 * (v_le - v_l)
    phi_l = 0.5 * (v_l - 0.0) + 0.5 * (v_le - v_e)
    per_l, per_e, per_le = (b["per_query"][a] for a in ("lexical", "semantic", "both"))
    diffs = [both - lex for both, lex in zip(per_le, per_l, strict=True)]
    se = statistics.pstdev(diffs) / math.sqrt(len(diffs)) if len(diffs) > 1 else 0.0
    return {"metric": metric, "v_empty": 0.0, "v_lexical": v_l, "v_embedder": v_e, "v_both": v_le,
            "shapley_embedder": round(phi_e, 4), "shapley_lexical": round(phi_l, 4),
            "loo_embedder": round(v_le - v_l, 4), "loo_embedder_se": round(se, 4),
            "loo_lexical": round(v_le - v_e, 4),
            "paired": {"embedder_helps": sum(1 for d in diffs if d > 0),
                       "embedder_hurts": sum(1 for d in diffs if d < 0),
                       "same": sum(1 for d in diffs if d == 0)},
            "note": "v is the arm's mean over the queries; the Shapley value over two sources is "
                    "half the marginal from nothing plus half the marginal onto the other"}


def certified_share(s: Scratch, qvecs: dict[str, list[float]]) -> dict[str, Any]:
    """VEC-1's certificate over the stored vectors: the share of ranked reads whose top-10 float16
    storage cannot have changed, and the margin's median gap, at this drain stage."""
    certified, gaps = 0, []
    for q in qvecs.values():
        r = s.stores.plane.search_ranked(q, k=K, clearance=MIRROR_READ)
        certified += int(r.margin.certified)
        if math.isfinite(r.margin.gap):
            gaps.append(r.margin.gap)
    return {"reads": len(qvecs), "certified": certified,
            "certified_share": round(certified / len(qvecs), 4) if qvecs else 0.0,
            "gap_median": round(statistics.median(gaps), 6) if gaps else None,
            "bound": round(s.stores.plane.search_ranked(next(iter(qvecs.values())), k=K,
                                                        clearance=MIRROR_READ).margin.bound, 6)
            if qvecs else None}


# ── the run ─────────────────────────────────────────────────────────────────────────────────────

def busy_slots(port: int) -> int | None:
    """How many of the embedder's slots another caller holds right now (`/slots`), the record of
    the contention a figure was measured under; None when the server does not say."""
    import json as _json
    import urllib.request

    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/slots", timeout=3) as r:
            slots = _json.loads(r.read())
    except Exception:
        return None
    return sum(1 for s in slots if s.get("is_processing"))


class Contention:
    """The embedder's busy slots, sampled every `every` seconds while a phase runs, and the
    machine's one-minute load average at its start and end. `own` is the most slots the phase's
    own requests can hold: none for a lazy landing, one for a synchronous landing (one text per
    request, sent in turn), and unknown for the drain, whose batches the server spreads across its
    slots. A sample above `own` is another caller."""

    def __init__(self, port: int, own: int | None, every: float = 5.0) -> None:
        self.port, self.own, self.every = port, own, every
        self.samples: list[int] = []
        self.load: list[float] = []
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._loop, daemon=True)

    def _loop(self) -> None:
        while not self._stop.is_set():
            n = busy_slots(self.port)
            if n is not None:
                self.samples.append(n)
            self._stop.wait(self.every)

    def __enter__(self) -> Contention:
        self.load.append(round(os.getloadavg()[0], 2))
        self._thread.start()
        return self

    def __exit__(self, *exc: object) -> None:
        self._stop.set()
        self._thread.join()
        self.load.append(round(os.getloadavg()[0], 2))

    def summary(self) -> dict[str, Any]:
        s, own = self.samples, self.own
        other = (round(sum(1 for n in s if n > own) / len(s), 3)
                 if s and own is not None else None)
        return {"slot_samples": len(s), "slots_max": max(s) if s else None,
                "other_caller_share": other, "load_1min": self.load}


def lag_control(base: Path, items: list[tuple[str, str, str]],
                args: argparse.Namespace) -> dict[str, Any]:
    """A lazy landing, then the drain at once: each item's lag from its key to its vector, with
    the contention both ran under."""
    out: dict[str, Any] = {}
    s = scratch(base / "lag", lazy=True, port=args.port)
    with Contention(args.port, own=0) as c:
        out["landing_lazy"] = land_in_plans(s, items, args.cap_chars, args.plans)
    out["landing_lazy"]["contention"] = c.summary()
    print(f"  landing_lazy {out['landing_lazy']}", flush=True)
    vector_at: dict[str, float] = {}

    def landed(paths: Sequence[str]) -> None:
        now = time.perf_counter()
        for path in paths:
            vector_at[path] = now

    with Contention(args.port, own=None) as c:
        d = drain(s.stores, batch=args.batch, landed=landed)
    out["drain"] = {"items": d.items, "chunks": d.chunks, "embedded": d.embedded,
                    "seconds": round(d.seconds, 2),
                    "chunks_per_s": round(d.chunks / d.seconds, 1) if d.seconds else None,
                    "contention": c.summary()}
    lags = [vector_at[p] - s.keyed_at[p] for p in vector_at if p in s.keyed_at]
    out["lag_seconds"] = quantiles(lags)
    out["lag_seconds"]["note"] = ("from an item's key to its vector, every item landed before the "
                                  "drain started and the drain started at once, in drain order")
    print(f"  drain {out['drain']}; lag {out['lag_seconds']}", flush=True)
    return out


def landing_control(base: Path, items: list[tuple[str, str, str]],
                    args: argparse.Namespace) -> dict[str, Any]:
    """The landing timings alone: lazy, the drain, synchronous, lazy again, each with the
    contention it ran under. The ratio of landing times uses the mean of the two lazy runs."""
    out: dict[str, Any] = {}

    def land(key: str, lazy: bool, own: int) -> Scratch:
        s = scratch(base / key, lazy=lazy, port=args.port)
        with Contention(args.port, own=own) as c:
            out[key] = land_in_plans(s, items, args.cap_chars, args.plans)
        out[key]["contention"] = c.summary()
        print(f"  {key} {out[key]}", flush=True)
        return s

    first = land("landing_lazy", True, 0)
    with Contention(args.port, own=None) as c:
        d = drain(first.stores, batch=args.batch)
    out["drain"] = {"items": d.items, "chunks": d.chunks, "embedded": d.embedded,
                    "seconds": round(d.seconds, 2),
                    "chunks_per_s": round(d.chunks / d.seconds, 1) if d.seconds else None,
                    "contention": c.summary()}
    print(f"  drain {out['drain']}", flush=True)
    land("landing_sync", False, 1)
    land("landing_lazy_again", True, 0)
    lazy_s = statistics.fmean([out["landing_lazy"]["seconds"],
                               out["landing_lazy_again"]["seconds"]])
    out["speedup_landing"] = round(out["landing_sync"]["seconds"] / lazy_s, 1)
    return out


def quantiles(xs: Sequence[float]) -> dict[str, float]:
    if not xs:
        return {}
    ys = sorted(xs)

    def pick(q: float) -> float:
        return ys[min(len(ys) - 1, int(q * len(ys)))]

    return {"p50": round(pick(0.5), 2), "p90": round(pick(0.9), 2), "max": round(ys[-1], 2),
            "mean": round(statistics.fmean(ys), 2)}


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default=str(DATA / "scifact"))
    ap.add_argument("--cap-chars", type=int, default=1200)
    ap.add_argument("--items", type=int, default=0, help="at most this many items (0: all)")
    ap.add_argument("--plans", type=int, default=10)
    ap.add_argument("--port", type=int, default=8081)
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--out", default="")
    ap.add_argument("--keep", action="store_true")
    ap.add_argument("--phases", choices=("all", "landing", "lag"), default="all",
                    help="landing: the timings alone (lazy, drain, synchronous, lazy again); "
                         "lag: a lazy landing drained at once")
    args = ap.parse_args(argv)

    corpus, queries, qrels = load_beir(Path(args.data).expanduser())
    items = [(d, t, x) for d, (t, x) in sorted(corpus.items())]
    if args.items:
        items = items[: args.items]
        keep = {d for d, _, _ in items}
        qrels = {q: {d: r for d, r in rels.items() if d in keep} for q, rels in qrels.items()}
        qrels = {q: rels for q, rels in qrels.items() if rels}
        queries = {q: t for q, t in queries.items() if q in qrels}
    base = Path(tempfile.mkdtemp(prefix="two-phase-"))
    report: dict[str, Any] = {"data": str(args.data), "items": len(items), "queries": len(queries),
                              "cap_chars": args.cap_chars, "plans": args.plans,
                              "embedder": GEMMA["model"], "batch": args.batch,
                              "started": time.strftime("%Y-%m-%dT%H:%M:%S"),
                              "embedder_slots_busy": {"start": busy_slots(args.port)}}
    if args.phases in ("landing", "lag"):
        control = landing_control if args.phases == "landing" else lag_control
        try:
            report.update(control(base, items, args))
            report["embedder_slots_busy"]["end"] = busy_slots(args.port)
            report["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        finally:
            if not args.keep:
                shutil.rmtree(base, ignore_errors=True)
        text = json.dumps(report, indent=2)
        if args.out:
            Path(args.out).write_text(text + "\n")
        print(text)
        return 0
    try:
        # 1. the lazy landing: complete without the vector
        lazy = scratch(base / "lazy", lazy=True, port=args.port)
        print("landing lazily …", flush=True)
        report["landing_lazy"] = land_in_plans(lazy, items, args.cap_chars, args.plans)
        report["landing_lazy"]["plane_rows"] = lazy.stores.plane.plane.reader(MIRROR_READ).count()
        report["landing_lazy"]["pending"] = len(pending_docs(lazy))
        print(f"  {report['landing_lazy']}", flush=True)
        qvecs = {q: lazy.stores.embedder.embed_query(t) for q, t in queries.items()}
        print("battery at 0% drained …", flush=True)
        report["battery_0"] = battery(lazy, queries, qrels, qvecs)
        report["certificate_0"] = certified_share(lazy, qvecs)
        # 2. the drain, in two halves, the lag recorded
        vector_at: dict[str, float] = {}

        def landed(paths: Sequence[str]) -> None:
            now = time.perf_counter()
            for p in paths:
                vector_at[p] = now

        half = len(items) // 2
        print("draining the first half …", flush=True)
        d1 = drain(lazy.stores, batch=args.batch, max_items=half, landed=landed)
        report["battery_50"] = battery(lazy, queries, qrels, qvecs)
        report["certificate_50"] = certified_share(lazy, qvecs)
        print("draining the rest …", flush=True)
        d2 = drain(lazy.stores, batch=args.batch, landed=landed)
        d3 = drain(lazy.stores, batch=args.batch)
        chunks = d1.chunks + d2.chunks
        seconds = d1.seconds + d2.seconds
        report["drain"] = {"items": d1.items + d2.items, "chunks": chunks,
                           "embedded": d1.embedded + d2.embedded, "seconds": round(seconds, 2),
                           "chunks_per_s": round(chunks / seconds, 1) if seconds else None,
                           "items_per_s": round((d1.items + d2.items) / seconds, 1) if seconds
                           else None,
                           "second_run": {"items": d3.items, "embedded": d3.embedded}}
        lags = [vector_at[p] - lazy.keyed_at[p] for p in vector_at if p in lazy.keyed_at]
        report["lag_seconds"] = quantiles(lags)
        report["lag_seconds"]["note"] = ("from an item's key to its vector, with every item landed "
                                         "before the drain started, in drain order")
        print(f"  drain {report['drain']}; lag {report['lag_seconds']}", flush=True)
        print("battery at 100% drained …", flush=True)
        report["battery_100"] = battery(lazy, queries, qrels, qvecs)
        report["certificate_100"] = certified_share(lazy, qvecs)
        report["attribution"] = {m: attribution(report["battery_100"], m)
                                 for m in ("recall", "ndcg")}
        # 3. the synchronous landing, for the comparison
        sync = scratch(base / "sync", lazy=False, port=args.port)
        print("landing synchronously …", flush=True)
        report["landing_sync"] = land_in_plans(sync, items, args.cap_chars, args.plans)
        report["landing_sync"]["plane_rows"] = sync.stores.plane.plane.reader(MIRROR_READ).count()
        print(f"  {report['landing_sync']}", flush=True)
        report["speedup_landing"] = round(report["landing_sync"]["seconds"]
                                          / report["landing_lazy"]["seconds"], 1)
        for key in ("battery_0", "battery_50", "battery_100"):
            report[key].pop("per_query", None)
        report["embedder_slots_busy"]["end"] = busy_slots(args.port)
        report["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    finally:
        if args.keep:
            print(f"kept {base}")
        else:
            shutil.rmtree(base, ignore_errors=True)
    text = json.dumps(report, indent=2)
    if args.out:
        Path(args.out).write_text(text + "\n")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
