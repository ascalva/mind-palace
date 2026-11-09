"""Decision models as generic integrators: typed meaning beside the embedder's similarity.

    uv run python -I -m eval.decision_integrators <benchmark> --out DIR [--arms local,hosted]
        [--scifact DIR] [--corpus DIR]

The embedder gives every text a vector and so a similarity between any two; it cannot say whether
a passage supports a claim or contradicts it. A decision model answers typed questions about
supplied state with probabilities (a Choice among options, a Noul for the probability that a
statement is true, a Score on described levels). This harness measures, on public data with
ground truth, what such questions add (dn-decision-integrators; the record is
docs/experiments/decision-integrators-2026-11-08.md, which declared the arms and falsifiers
before the runs):

- `polarity`: SciFact (AllenAI's original release, claims with SUPPORT and CONTRADICT labels on
  cited abstracts, and claims without evidence): supports, contradicts or says nothing, a Choice
  and its Noul variant, against the embedder's cosine;
- `rerank`: the two integrators composed, on BEIR SciFact and NFCorpus: the embedder ranks the
  collection, a Noul per candidate re-ranks its top 20; nDCG@10 for the embedder, the re-ranked
  and the fused orders. `mining` reads the SciFact run: how precisely the polarity question finds
  the contradicting pairs among the embedder's neighbours;
- `topic`: arXiv items of the corpus instance, a Choice over archives against the embedder's
  kNN (k = 10); `kind`: Stack Exchange posts, question or answer, a Noul; `linking`: which of a
  question's embedder neighbours answers it; `duplicates`: do two questions ask the same thing;
- `discovery`: the question-discovery pilot: candidate questions kept only for the gain they
  measure beyond the embedder and the questions already kept, on rows they were not chosen on;
- `controls`: the context control (the 8192-token tag against tev1's own 2048) and
  repeatability; `report` writes the record's JSON, aggregates only.

Arms: `local` is tev1:0.8b's weights served by Ollama under a tag with an 8192-token window
(LOCAL_MODEL: /v1/systemone has no per-request window, so the tag's Modelfile carries `num_ctx`;
the record says how it was made and measures that it answers as tev1 does); `hosted` is
TypeSafe's Jev, sent through the edge's own process (edge/systemone.py) with a dollar stop. Only
public benchmark text is ever written for the hosted arm: SciFact, BEIR, and the corpus
instance's arXiv and Stack Exchange items, all public sources; nothing here reads a vault, a note
or a dialogue, and the corpus instance is opened read-only.

Every request and its answer are kept in `DIR/answers-<arm>.jsonl` (the cache that keeps a rerun
from asking twice and the record that lets any result be asked again); each benchmark writes
`DIR/result-<benchmark>-<arm>.json`. The embedder is the stack's (127.0.0.1:8081), one stream,
behind the corpus runner's gate (ops/corpus/embedder.py), with vectors cached in DIR.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import sqlite3
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from collections.abc import Callable, Iterable, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import numpy.typing as npt
from scipy.optimize import minimize

from eval import decision_questions as dq

F64 = npt.NDArray[np.float64]
I64 = npt.NDArray[np.int64]

REPO = Path(__file__).resolve().parent.parent
RECORD_JSON = REPO / "docs/experiments/decision-integrators-2026-11-08.json"
BEIR = Path.home() / "models" / "bench-data"  # eval/embedder_bench.py's local BEIR copies

OLLAMA = "http://127.0.0.1:11434/v1/systemone"
LOCAL_MODEL = "tev1-ctx8192"   # FROM tev1:0.8b, PARAMETER num_ctx 8192 (the record, §Models)
BASE_LOCAL_MODEL = "tev1:0.8b"
HOSTED_MODEL = "jev-1.14.0"
PRICE_PER_MTOK = 0.042         # dollars per million input tokens (docs.typesafe.ai/models)
STOP_USD = 1.50                # the hosted arm stops here; the owner's grant is $2 in total
EMBED_PORT = 8081
CHAT_PORT = 8080               # the gate pauses while the chat model serves
EMBED_MODEL = "embeddinggemma-2"
EMBED_BATCH = 64               # the corpus runner's measured default: one stream of 64
DOC_CHARS = 2000               # the embedder sees a document cut here (embedder_bench.DOC_CHARS)
STATE_CHARS = 6000             # the decision model sees a passage cut here (cuts are counted)
SEED = 20261108
TOP = 20                       # the embedder's shortlist the decision model re-ranks
RRF_K = 60                     # reciprocal rank fusion's constant
KNN = 10

POLARITY_LABELS = ["supports", "contradicts", "says_nothing"]
LABEL_OF = {"SUPPORT": 0, "CONTRADICT": 1}


@dataclass(frozen=True)
class Arm:
    name: str
    model: str
    hosted: bool


ARMS = {"local": Arm("local", LOCAL_MODEL, False), "hosted": Arm("hosted", HOSTED_MODEL, True)}


class BudgetStopped(RuntimeError):
    """The hosted arm's ledger reached its stop; what was answered is kept."""


# ── requests and the answer cache ───────────────────────────────────────────────────────────────


def request_key(payload: dict[str, Any]) -> str:
    text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class Answers:
    """Every request sent and what came back, one JSON line each."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.rows: dict[str, dict[str, Any]] = {}
        self.lock = threading.Lock()
        if path.exists():
            for line in path.read_text().splitlines():
                if line.strip():
                    row = json.loads(line)
                    self.rows[row["key"]] = row

    def add(self, row: dict[str, Any]) -> None:
        with self.lock:
            self.rows[row["key"]] = row
            with self.path.open("a") as fh:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")


class Sampler:
    """Samples the machine while a local arm runs: the embedder's busy slots (another caller)
    and the load average, every `every_s` seconds. Latency is reported with this beside it."""

    def __init__(self, every_s: float = 5.0) -> None:
        self.every_s = every_s
        self.samples: list[tuple[int, float]] = []
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def __enter__(self) -> Sampler:
        self._thread.start()
        return self

    def __exit__(self, *exc: object) -> None:
        self._stop.set()
        self._thread.join(timeout=10)

    def _run(self) -> None:
        while not self._stop.wait(self.every_s):
            self.samples.append((embedder_busy(), os.getloadavg()[0]))

    def summary(self) -> dict[str, Any]:
        if not self.samples:
            return {"samples": 0}
        busy = [b for b, _ in self.samples]
        return {"samples": len(self.samples),
                "share_embedder_busy": round(sum(1 for b in busy if b > 0) / len(busy), 3),
                "load_median": round(float(np.median([x for _, x in self.samples])), 2),
                "load_max": round(max(x for _, x in self.samples), 2)}


def embedder_busy() -> int:
    """How many of the stack embedder's slots are processing (another caller), -1 if unknown."""
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{EMBED_PORT}/slots", timeout=3) as r:
            return sum(1 for s in json.loads(r.read()) if s.get("is_processing"))
    except (OSError, ValueError):
        return -1


def _post_local(payload: dict[str, Any]) -> dict[str, Any]:
    req = urllib.request.Request(OLLAMA, data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            body: dict[str, Any] = json.loads(r.read())
            return body
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code}: {e.read()[:300].decode('utf-8', 'replace')}") from e


def ask(arm: Arm, payloads: Sequence[dict[str, Any]], out: Path, *, workers: int = 1,
        label: str = "") -> list[dict[str, Any]]:
    """The answer row for every payload, asking only for those the cache lacks. A row carries
    `response` or `error`; an error is reported as such and never read as an answer."""
    cache = Answers(out / f"answers-{arm.name}.jsonl")
    keys = [request_key(p) for p in payloads]
    missing: dict[str, dict[str, Any]] = {}
    for k, p in zip(keys, payloads, strict=True):
        if k not in cache.rows:
            missing[k] = p
    if missing:
        print(f"[{arm.name}] {label}: asking {len(missing)} of {len(payloads)}", file=sys.stderr)
        if arm.hosted:
            _ask_hosted(missing, cache, out, workers=max(workers, 4))
        else:
            _ask_local(missing, cache, workers=workers)
    return [cache.rows[k] for k in keys]


def _ask_local(missing: dict[str, dict[str, Any]], cache: Answers, *, workers: int) -> None:
    done = [0]
    t_start = time.monotonic()

    def one(item: tuple[str, dict[str, Any]]) -> None:
        key, payload = item
        t0 = time.monotonic()
        row: dict[str, Any] = {"key": key, "payload": payload,
                               "at": datetime.now(UTC).isoformat(timespec="seconds")}
        try:
            row["response"] = _post_local(payload)
        except (RuntimeError, OSError, ValueError) as e:
            row["error"] = str(e)
        row["seconds"] = round(time.monotonic() - t0, 4)
        cache.add(row)
        done[0] += 1
        if done[0] % 500 == 0:
            rate = done[0] / max(1e-6, time.monotonic() - t_start)
            print(f"  {done[0]}/{len(missing)} ({rate:.1f}/s)", file=sys.stderr)

    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        list(pool.map(one, missing.items()))


def _ask_hosted(missing: dict[str, dict[str, Any]], cache: Answers, out: Path, *,
                workers: int) -> None:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%f")
    req_path = out / f"hosted-requests-{stamp}.jsonl"
    resp_path = out / f"hosted-responses-{stamp}.jsonl"
    with req_path.open("w") as fh:
        for key, payload in missing.items():
            fh.write(json.dumps({"key": key, "payload": payload}, ensure_ascii=False) + "\n")
    proc = subprocess.run(
        [sys.executable, "-I", "-m", "edge.systemone", "--requests", str(req_path),
         "--responses", str(resp_path), "--ledger", str(out / "hosted-ledger.json"),
         "--stop-usd", str(STOP_USD), "--price", str(PRICE_PER_MTOK),
         "--workers", str(workers)],
        cwd=REPO,
    )
    if resp_path.exists():
        for line in resp_path.read_text().splitlines():
            r = json.loads(line)
            row = {"key": r["key"], "payload": missing[r["key"]],
                   "at": datetime.now(UTC).isoformat(timespec="seconds"),
                   "seconds": r.get("seconds")}
            row["response" if "response" in r else "error"] = r.get("response", r.get("error"))
            cache.add(row)
    if proc.returncode == 3:
        raise BudgetStopped("the hosted ledger reached its stop")
    if proc.returncode != 0:
        raise RuntimeError(f"edge.systemone exited {proc.returncode}")


def ledger_usd(out: Path) -> float:
    path = out / "hosted-ledger.json"
    return float(json.loads(path.read_text())["usd"]) if path.exists() else 0.0


# ── reading answers ─────────────────────────────────────────────────────────────────────────────


def answer(row: dict[str, Any], qid: str) -> dict[str, Any] | None:
    resp = row.get("response")
    if not isinstance(resp, dict):
        return None
    got = resp.get("answers", {}).get(qid)
    return got if isinstance(got, dict) else None


def noul(row: dict[str, Any], qid: str) -> float:
    got = answer(row, qid)
    return float(got["noul"]) if got is not None else math.nan


def probs(row: dict[str, Any], qid: str, names: Sequence[str]) -> F64:
    """A Choice's probabilities in the order of `names`, or a Score's by level (names are the
    level indices as strings); renormalized, NaN when the answer is missing."""
    got = answer(row, qid)
    if got is None:
        return np.full(len(names), math.nan)
    p = np.array([float(got["probabilities"].get(n, 0.0)) for n in names])
    s = p.sum()
    return p / s if s > 0 else np.full(len(names), 1.0 / len(names))


def tokens(rows: Sequence[dict[str, Any]]) -> F64:
    return np.array([float((r.get("response") or {}).get("usage", {}).get("input_tokens") or 0)
                     for r in rows if "response" in r])


def usage_summary(rows: Sequence[dict[str, Any]], arm: Arm) -> dict[str, Any]:
    tok = tokens(rows)
    secs = np.array([float(r["seconds"]) for r in rows if "response" in r and r.get("seconds")])
    out: dict[str, Any] = {
        "requests": len(rows), "errors": sum(1 for r in rows if "error" in r),
        "input_tokens_per_request": round(float(tok.mean()), 1) if len(tok) else None,
        "hosted_usd_per_million_requests": round(float(tok.mean()) * PRICE_PER_MTOK, 2)
        if len(tok) else None,
    }
    if not arm.hosted and len(secs):
        out["local_seconds_median"] = round(float(np.median(secs)), 4)
        out["local_seconds_p90"] = round(float(np.percentile(secs, 90)), 4)
    if arm.hosted and len(secs):
        out["hosted_seconds_median"] = round(float(np.median(secs)), 3)
    return out


# ── metrics ─────────────────────────────────────────────────────────────────────────────────────


def accuracy(y: I64, p: F64) -> float:
    return float(np.mean(np.argmax(p, axis=1) == y))


def macro_f1(y: I64, pred: I64) -> float:
    """F1 averaged over the classes present in the ground truth (a class never predicted
    scores 0)."""
    scores = []
    for c in np.unique(y):
        tp = float(np.sum((pred == c) & (y == c)))
        fp = float(np.sum((pred == c) & (y != c)))
        fn = float(np.sum((pred != c) & (y == c)))
        scores.append(2 * tp / (2 * tp + fp + fn) if tp + fp + fn else 0.0)
    return float(np.mean(scores))


def brier(y: I64, p: F64) -> float:
    """The multiclass Brier score: the mean over items of the squared distance between the
    probability vector and the one-hot outcome (0 is perfect, 2 the worst)."""
    onehot = np.eye(p.shape[1])[y]
    return float(np.mean(np.sum((p - onehot) ** 2, axis=1)))


def log_loss(y: I64, p: F64, eps: float = 1e-6) -> float:
    return float(-np.mean(np.log(np.clip(p[np.arange(len(y)), y], eps, 1.0))))


def ece(confidence: F64, correct: F64, bins: int = 10) -> tuple[float, list[dict[str, Any]]]:
    """Expected calibration error over equal-width bins of `confidence`, and the reliability
    curve's data: each bin's count, mean confidence and observed rate."""
    edges = np.linspace(0.0, 1.0, bins + 1)
    idx = np.clip(np.digitize(confidence, edges[1:-1], right=True), 0, bins - 1)
    total, table = 0.0, []
    for b in range(bins):
        m = idx == b
        n = int(m.sum())
        if n == 0:
            table.append({"bin": [round(edges[b], 1), round(edges[b + 1], 1)], "n": 0})
            continue
        conf, rate = float(confidence[m].mean()), float(correct[m].mean())
        total += n * abs(conf - rate)
        table.append({"bin": [round(edges[b], 1), round(edges[b + 1], 1)], "n": n,
                      "confidence": round(conf, 4), "observed": round(rate, 4)})
    return total / max(1, len(confidence)), table


def auroc(score: F64, label: I64) -> float:
    """The probability that a positive outranks a negative, ties counted half (Mann-Whitney)."""
    pos, neg = score[label == 1], score[label == 0]
    if len(pos) == 0 or len(neg) == 0:
        return math.nan
    order = np.argsort(np.concatenate([pos, neg]), kind="mergesort")
    ranks = np.empty(len(order))
    allv = np.concatenate([pos, neg])[order]
    i = 0
    while i < len(allv):
        j = i
        while j + 1 < len(allv) and allv[j + 1] == allv[i]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2 + 1
        i = j + 1
    return float((ranks[: len(pos)].sum() - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg)))


def average_precision(score: F64, label: I64) -> float:
    order = np.argsort(-score, kind="mergesort")
    hits = label[order]
    if hits.sum() == 0:
        return math.nan
    prec = np.cumsum(hits) / np.arange(1, len(hits) + 1)
    return float((prec * hits).sum() / hits.sum())


def precision_at(score: F64, label: I64, k: int) -> float:
    order = np.argsort(-score, kind="mergesort")[:k]
    return float(label[order].mean())


def ndcg10(ranked: Sequence[str], rels: dict[str, int]) -> float:
    from eval.embedder_bench import ndcg_at_10  # the bench's own formula, so the control holds

    return ndcg_at_10(list(ranked), rels)


def cluster_ci(stat: Callable[[I64], float], clusters: Sequence[Any], *, b: int = 2000,
               seed: int = SEED) -> list[float]:
    """A 95% percentile interval of `stat` over resampled clusters; `stat` takes item indices."""
    groups: dict[Any, list[int]] = defaultdict(list)
    for i, c in enumerate(clusters):
        groups[c].append(i)
    keys = list(groups)
    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(b):
        pick = rng.integers(0, len(keys), len(keys))
        idx = np.fromiter((i for k in pick for i in groups[keys[k]]), dtype=np.int64)
        v = stat(idx)
        if not math.isnan(v):
            vals.append(v)
    return [round(float(np.percentile(vals, 2.5)), 4), round(float(np.percentile(vals, 97.5)), 4)]


def mean_stat(d: F64) -> Callable[[I64], float]:
    return lambda i: float(d[i].mean())


def auroc_stat(score: F64, label: I64) -> Callable[[I64], float]:
    return lambda i: auroc(score[i], label[i])


def precision_stat(score: F64, label: I64, k: int) -> Callable[[I64], float]:
    return lambda i: precision_at(score[i], label[i], k)


def f1_gap_stat(y: I64, a: F64, b: F64) -> Callable[[I64], float]:
    """Macro-F1 of the argmax of `a` minus that of `b`, on the resampled items."""
    return lambda i: macro_f1(y[i], np.argmax(a[i], axis=1)) - macro_f1(y[i], np.argmax(b[i],
                                                                                         axis=1))


def classification(y: I64, p: F64, names: Sequence[str], clusters: Sequence[Any] | None = None,
                   positive: int | None = None) -> dict[str, Any]:
    """The common table: accuracy, macro-F1, Brier, log loss, top-label ECE and its curve; for a
    binary task (`positive` given) also AUROC and the ECE of the positive class's probability."""
    ok = ~np.isnan(p).any(axis=1)
    y, p = y[ok], p[ok]
    pred = np.argmax(p, axis=1)
    conf = p.max(axis=1)
    e, curve = ece(conf, (pred == y).astype(float))
    out: dict[str, Any] = {
        "n": int(len(y)), "missing": int((~ok).sum()),
        "accuracy": round(accuracy(y, p), 4), "macro_f1": round(macro_f1(y, pred), 4),
        "brier": round(brier(y, p), 4), "log_loss": round(log_loss(y, p), 4),
        "ece": round(e, 4), "reliability": curve,
        "confusion": [[int(np.sum((y == i) & (pred == j))) for j in range(len(names))]
                      for i in range(len(names))],
        "labels": list(names),
    }
    if positive is not None:
        score, lab = p[:, positive], (y == positive).astype(np.int64)
        e2, curve2 = ece(score, lab.astype(float))
        out.update({"auroc": round(auroc(score, lab), 4), "ece_positive": round(e2, 4),
                    "reliability_positive": curve2})
    if clusters is not None:
        cl = [c for c, k in zip(clusters, ok, strict=True) if k]
        out["accuracy_ci"] = cluster_ci(lambda i: accuracy(y[i], p[i]), cl)
        out["macro_f1_ci"] = cluster_ci(lambda i: macro_f1(y[i], pred[i]), cl)
    return out


# ── the embedder ────────────────────────────────────────────────────────────────────────────────


def gemma_query(task: str, text: str) -> str:
    return f"task: {task} | query: {text[:DOC_CHARS]}"


def gemma_doc(title: str, text: str) -> str:
    return f"title: {title or 'none'} | text: {text[:DOC_CHARS]}"


def embed(texts: Sequence[str], out: Path, name: str) -> F64:
    """Unit vectors for `texts` from the stack's embedder, one stream of EMBED_BATCH behind the
    corpus runner's gate, cached in `out` by the texts' digest."""
    h = hashlib.sha256("\x00".join(texts).encode("utf-8")).hexdigest()[:16]
    path = out / f"vectors-{name}-{h}.npy"
    if path.exists():
        cached: F64 = np.load(path)
        return cached
    from core.ingest.embed import Embedder
    from core.kernel.config.loader import EmbeddingConfig
    from core.models.llama_server_client import LlamaServerClient
    from ops.corpus.embedder import Gate, GatedEmbedder

    inner = Embedder(client=LlamaServerClient(port=EMBED_PORT),
                     config=EmbeddingConfig(model=EMBED_MODEL, dim=768, query_instruction=""))
    gate = Gate(chat_port=CHAT_PORT, embed_port=EMBED_PORT)
    gated = GatedEmbedder(inner, gate, streams=1, batch=EMBED_BATCH)
    t0 = time.monotonic()
    print(f"embedding {len(texts)} texts ({name})", file=sys.stderr)
    try:
        m = np.asarray(gated.embed_documents(list(texts)), dtype=np.float64)
    finally:
        gate.close()
    m /= np.linalg.norm(m, axis=1, keepdims=True)
    np.save(path, m)
    print(f"  {time.monotonic() - t0:.0f} s", file=sys.stderr)
    return m


def top_k(q: F64, docs: F64, k: int) -> tuple[I64, F64]:
    sims = q @ docs.T
    idx = np.argsort(-sims, axis=1, kind="stable")[:, :k]
    return idx.astype(np.int64), np.take_along_axis(sims, idx, axis=1)


def knn_probs(vecs: F64, y: I64, n_classes: int, k: int = KNN) -> F64:
    """Leave-one-out kNN: each item's class probabilities are its k nearest others' votes."""
    sims = vecs @ vecs.T
    np.fill_diagonal(sims, -np.inf)
    nn = np.argsort(-sims, axis=1, kind="stable")[:, :k]
    p = np.zeros((len(y), n_classes))
    for i, row in enumerate(nn):
        for j in row:
            p[i, y[j]] += 1.0 / k
    return p


# ── data ────────────────────────────────────────────────────────────────────────────────────────


def cut(text: str, n: int = STATE_CHARS) -> str:
    return text if len(text) <= n else text[:n]


@dataclass(frozen=True)
class Pair:
    split: str
    claim_id: int
    doc_id: int
    label: int  # 0 supports, 1 contradicts, 2 says nothing


def load_scifact(root: Path) -> tuple[dict[int, tuple[str, str]], dict[int, tuple[str, str]],
                                      list[Pair]]:
    """AllenAI's original SciFact release: the corpus, the claims of train and dev, and every
    labelled (claim, cited abstract) pair: SUPPORT, CONTRADICT, or a cited abstract without
    evidence (says nothing). The test split's labels are hidden, so it is not read."""
    corpus = {}
    for line in (root / "corpus.jsonl").read_text().splitlines():
        r = json.loads(line)
        corpus[int(r["doc_id"])] = (str(r["title"]), " ".join(s.strip() for s in r["abstract"]))
    claims: dict[int, tuple[str, str]] = {}
    pairs: list[Pair] = []
    for split in ("train", "dev"):
        for line in (root / f"claims_{split}.jsonl").read_text().splitlines():
            r = json.loads(line)
            cid = int(r["id"])
            claims[cid] = (split, str(r["claim"]))
            evidence = {int(d): {e["label"] for e in es} for d, es in r["evidence"].items()}
            for d, labels in sorted(evidence.items()):
                if len(labels) != 1:
                    raise ValueError(f"claim {cid} doc {d}: mixed labels {labels}")
                pairs.append(Pair(split, cid, d, LABEL_OF[next(iter(labels))]))
            for d in sorted(set(int(x) for x in r["cited_doc_ids"]) - set(evidence)):
                pairs.append(Pair(split, cid, d, 2))
    return corpus, claims, pairs


def load_beir(ds: str) -> tuple[dict[str, tuple[str, str]], dict[str, str],
                                dict[str, dict[str, int]]]:
    from eval import embedder_bench

    return embedder_bench.load_beir(ds)


class Corpus:
    """The corpus instance, read-only: its catalog, its raw store, its sources' records."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.db = sqlite3.connect(f"file:{root / 'data/vault_catalog.sqlite'}?mode=ro", uri=True)

    def texts(self, paths: Sequence[str]) -> dict[str, str]:
        out: dict[str, str] = {}
        for i in range(0, len(paths), 500):
            chunk = list(paths[i:i + 500])
            marks = ",".join("?" * len(chunk))
            for path, digest in self.db.execute(
                f"SELECT source_path, digest FROM vault_files WHERE active = 1 "
                f"AND source_path IN ({marks})", chunk):
                out[path] = (self.root / "data/raw" / digest[:2] / digest).read_text()
        return out

    def meta(self, source: str) -> list[dict[str, Any]]:
        path = self.root / "sources" / source / "meta/items.jsonl"
        return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def post_parts(text: str) -> tuple[str, str]:
    """A stored Stack Exchange post as (first line, body). The first line is a question's title
    or an answer's "Answer to: <title>", and a question ends with a "Tags:" line; both name the
    post's kind, so the body is returned without them."""
    first, _, rest = text.partition("\n\n")
    body = rest.strip()
    lines = body.rsplit("\n\n", 1)
    if len(lines) == 2 and lines[1].startswith("Tags: "):
        body = lines[0].strip()
    elif body.startswith("Tags: ") and "\n" not in body:
        body = ""
    return first.strip(), body


# ── polarity (SciFact) and its feeds: rerank, mining, discovery ─────────────────────────────────


def polarity_state(claim: str, title: str, text: str) -> dict[str, Any]:
    return {"claim": claim, "passage": {"title": title, "text": cut(text)}}


def polarity_payload(arm: Arm, claim: str, title: str, text: str) -> dict[str, Any]:
    return {"model": arm.model, "state": polarity_state(claim, title, text),
            "questions": dq.POLARITY}


def noul_product(s: F64, c: F64) -> F64:
    """The Noul variant's three probabilities from two independent judgments: supports alone,
    contradicts alone, neither; the impossible both is renormalized away."""
    eps = 1e-9
    p = np.stack([s * (1 - c), c * (1 - s), (1 - s) * (1 - c)], axis=1) + eps
    out: F64 = p / p.sum(axis=1, keepdims=True)
    return out


def noul_companion(s: F64, c: F64, a: F64) -> F64:
    """The companion rule: says nothing with 1 - addresses, the rest split by supports and
    contradicts."""
    eps = 1e-9
    share = s / (s + c + eps)
    out: F64 = np.stack([a * share, a * (1 - share), 1 - a], axis=1)
    return out


def polarity_answers(rows: Sequence[dict[str, Any]]) -> dict[str, F64]:
    rel = np.array([probs(r, "relation", POLARITY_LABELS) for r in rows])
    rev = np.array([probs(r, "relation_reversed", POLARITY_LABELS) for r in rows])
    s = np.array([noul(r, "supports") for r in rows])
    c = np.array([noul(r, "contradicts") for r in rows])
    a = np.array([noul(r, "addresses") for r in rows])
    return {"relation": rel, "relation_reversed": rev, "supports": s, "contradicts": c,
            "addresses": a, "product": noul_product(s, c), "companion": noul_companion(s, c, a)}


class SciFactVectors:
    """The embedder's view of SciFact: every abstract as a document, every claim as a query in
    the fact-checking task, exactly as the embedder bench formats them."""

    def __init__(self, out: Path, corpus: dict[int, tuple[str, str]],
                 claims: dict[int, tuple[str, str]]) -> None:
        self.doc_ids = sorted(corpus)
        self.claim_ids = sorted(claims)
        self.docs = embed([gemma_doc(*corpus[d]) for d in self.doc_ids], out, "scifact-docs")
        self.queries = embed([gemma_query("fact checking", claims[c][1]) for c in self.claim_ids],
                             out, "scifact-claims")
        self.doc_row = {d: i for i, d in enumerate(self.doc_ids)}
        self.claim_row = {c: i for i, c in enumerate(self.claim_ids)}

    def cosine(self, claim_id: int, doc_id: int) -> float:
        return float(self.queries[self.claim_row[claim_id]] @ self.docs[self.doc_row[doc_id]])


def fit_logistic(x: F64, y: I64, n_classes: int, l2: float = 1.0) -> Callable[[F64], F64]:
    """Multinomial logistic regression, L2 on the weights (not the intercepts), features
    standardized on the fit rows; returns the predictor."""
    mu, sd = x.mean(axis=0), x.std(axis=0)
    sd[sd < 1e-9] = 1.0
    z = (x - mu) / sd
    n, d = z.shape
    onehot = np.eye(n_classes)[y]

    def unpack(w: F64) -> tuple[F64, F64]:
        return w[: d * n_classes].reshape(d, n_classes), w[d * n_classes:]

    def loss(w: F64) -> tuple[float, F64]:
        coef, b = unpack(w)
        logits = z @ coef + b
        logits -= logits.max(axis=1, keepdims=True)
        p = np.exp(logits)
        p /= p.sum(axis=1, keepdims=True)
        nll = -np.sum(onehot * np.log(np.clip(p, 1e-12, 1.0))) / n
        g = (p - onehot) / n
        grad = np.concatenate([(z.T @ g + l2 * coef / n).ravel(), g.sum(axis=0)])
        return float(nll + 0.5 * l2 * np.sum(coef**2) / n), grad

    res = minimize(loss, np.zeros(d * n_classes + n_classes), jac=True, method="L-BFGS-B")
    coef, b = unpack(res.x)

    def predict(xn: F64) -> F64:
        logits = ((xn - mu) / sd) @ coef + b
        logits -= logits.max(axis=1, keepdims=True)
        p = np.exp(logits)
        out: F64 = p / p.sum(axis=1, keepdims=True)
        return out

    return predict


def run_polarity(args: argparse.Namespace, arm: Arm) -> dict[str, Any]:
    corpus, claims, pairs = load_scifact(args.scifact)
    payloads = [polarity_payload(arm, claims[p.claim_id][1], *corpus[p.doc_id]) for p in pairs]
    with Sampler() as sampler:
        rows = ask(arm, payloads, args.out, workers=args.workers, label="polarity")
    ans = polarity_answers(rows)
    vec = SciFactVectors(args.out, corpus, claims)
    cos = np.array([vec.cosine(p.claim_id, p.doc_id) for p in pairs])
    y = np.array([p.label for p in pairs], dtype=np.int64)
    split = np.array([p.split for p in pairs])
    clusters = [p.claim_id for p in pairs]
    train, dev = split == "train", split == "dev"
    predict = fit_logistic(cos[train, None], y[train], 3)
    prior = np.bincount(y[train], minlength=3) / train.sum()
    result: dict[str, Any] = {"benchmark": "polarity", "arm": arm.name, "model": arm.model,
                              "question_digest": dq.digest(dq.POLARITY),
                              "pairs": {"train": int(train.sum()), "dev": int(dev.sum()),
                                        "by_label": {s: dict(Counter(
                                            POLARITY_LABELS[v] for v in y[split == s]))
                                            for s in ("train", "dev")}},
                              "state_cuts": sum(1 for p in pairs
                                                if len(corpus[p.doc_id][1]) > STATE_CHARS),
                              "usage": usage_summary(rows, arm), "machine": sampler.summary()}
    for name, mask in (("dev", dev), ("train", train)):
        cl = [c for c, m in zip(clusters, mask, strict=True) if m]
        block: dict[str, Any] = {
            "choice": classification(y[mask], ans["relation"][mask], POLARITY_LABELS, cl),
            "choice_reversed": classification(y[mask], ans["relation_reversed"][mask],
                                              POLARITY_LABELS, cl),
            "noul_product": classification(y[mask], ans["product"][mask], POLARITY_LABELS, cl),
            "noul_companion": classification(y[mask], ans["companion"][mask], POLARITY_LABELS,
                                             cl),
            "majority": classification(y[mask], np.tile(prior, (int(mask.sum()), 1)),
                                       POLARITY_LABELS),
        }
        if name == "dev":
            block["embedder_logistic"] = classification(y[mask], predict(cos[mask, None]),
                                                        POLARITY_LABELS, cl)
        ev = mask & (y != 2)
        sc = (y[ev] == 0).astype(np.int64)  # supports (1) against contradicts (0)
        evn = (y[mask] != 2).astype(np.int64)  # evidence either way against nothing
        block["auroc"] = {
            "supports_vs_contradicts": {
                "cosine": round(auroc(cos[ev], sc), 4),
                "cosine_ci": cluster_ci(auroc_stat(cos[ev], sc),
                                        [c for c, m in zip(clusters, ev, strict=True) if m]),
                "choice": round(auroc(ans["relation"][ev, 0] - ans["relation"][ev, 1], sc), 4),
                "nouls": round(auroc(ans["supports"][ev] - ans["contradicts"][ev], sc), 4),
            },
            "evidence_vs_nothing": {
                "cosine": round(auroc(cos[mask], evn), 4),
                "choice": round(auroc(1 - ans["relation"][mask, 2], evn), 4),
                "addresses": round(auroc(ans["addresses"][mask], evn), 4),
            },
        }
        top = np.argmax(ans["relation"][mask], axis=1)
        top_r = np.argmax(ans["relation_reversed"][mask], axis=1)
        block["order_flips"] = round(float(np.mean(top != top_r)), 4)
        if name == "dev":
            m = ~np.isnan(ans["relation"][mask]).any(axis=1)
            yy, pc = y[mask][m], ans["relation"][mask][m]
            pe = predict(cos[mask, None])[m]
            block["choice_minus_embedder_macro_f1_ci"] = cluster_ci(
                f1_gap_stat(yy, pc, pe), [c for c, k in zip(cl, m, strict=True) if k])
        result[name] = block
    result["examples"] = polarity_examples(pairs, claims, corpus, ans, cos)
    return result


def polarity_examples(pairs: Sequence[Pair], claims: dict[int, tuple[str, str]],
                      corpus: dict[int, tuple[str, str]], ans: dict[str, F64],
                      cos: F64) -> list[dict[str, Any]]:
    """A few dev answers to read (public text): the most confident errors of each kind and the
    clearest hits, with the claim and the abstract's title."""
    rel = ans["relation"]
    out: list[dict[str, Any]] = []
    dev = [i for i, p in enumerate(pairs) if p.split == "dev" and not np.isnan(rel[i]).any()]
    def row(i: int, why: str) -> dict[str, Any]:
        p = pairs[i]
        return {"why": why, "claim_id": p.claim_id, "doc_id": p.doc_id,
                "claim": claims[p.claim_id][1], "title": corpus[p.doc_id][0],
                "label": POLARITY_LABELS[p.label],
                "relation": dict(zip(POLARITY_LABELS, np.round(rel[i], 3).tolist(),
                                     strict=True)),
                "nouls": {k: round(float(ans[k][i]), 3)
                          for k in ("supports", "contradicts", "addresses")},
                "cosine": round(float(cos[i]), 3)}
    for true in range(3):
        wrong = [i for i in dev if pairs[i].label == true and int(np.argmax(rel[i])) != true]
        wrong.sort(key=lambda i: -float(rel[i].max()))
        out += [row(i, f"confident error on {POLARITY_LABELS[true]}") for i in wrong[:2]]
        right = [i for i in dev if pairs[i].label == true and int(np.argmax(rel[i])) == true]
        right.sort(key=lambda i: -float(rel[i][true]))
        out += [row(i, f"clear hit on {POLARITY_LABELS[true]}") for i in right[:1]]
    return out


def rerank_orders(emb_rank: Sequence[str], score: dict[str, float]) -> dict[str, list[str]]:
    """The three orders of one shortlist: the embedder's, the decision model's (ties kept in the
    embedder's order), and their reciprocal rank fusion."""
    judged = sorted(emb_rank, key=lambda d: (-score[d], emb_rank.index(d)))
    fused = sorted(emb_rank, key=lambda d: -(1 / (RRF_K + emb_rank.index(d) + 1)
                                             + 1 / (RRF_K + judged.index(d) + 1)))
    return {"embedder": list(emb_rank), "judged": judged, "fused": fused}


def run_rerank(args: argparse.Namespace, arm: Arm) -> dict[str, Any]:
    result: dict[str, Any] = {"benchmark": "rerank", "arm": arm.name, "model": arm.model}
    corpus_sf, claims, pairs = load_scifact(args.scifact)
    for ds in args.collections:
        corpus, queries, qrels = load_beir(ds)
        doc_ids = sorted(corpus)
        if ds == "scifact":
            vec = SciFactVectors(args.out, corpus_sf, claims)
            qids = sorted(queries, key=int)
            qv = vec.queries[[vec.claim_row[int(q)] for q in qids]]
            dv, doc_ids = vec.docs, [str(d) for d in vec.doc_ids]
        else:
            dv = embed([gemma_doc(*corpus[d]) for d in doc_ids], args.out, f"{ds}-docs")
            qids = sorted(queries)
            qv = embed([gemma_query("question answering", queries[q]) for q in qids], args.out,
                       f"{ds}-queries")
        idx, _ = top_k(qv, dv, TOP)
        shortlist = {q: [doc_ids[j] for j in idx[i]] for i, q in enumerate(qids)}
        payloads, where = [], []
        for q in qids:
            for d in shortlist[q]:
                if ds == "scifact":
                    payloads.append(polarity_payload(arm, claims[int(q)][1],
                                                     *corpus_sf[int(d)]))
                else:
                    title, text = corpus[d]
                    payloads.append({"model": arm.model,
                                     "state": {"query": queries[q],
                                               "passage": {"title": title, "text": cut(text)}},
                                     "questions": dq.RELEVANCE})
                where.append((q, d))
        with Sampler() as sampler:
            rows = ask(arm, payloads, args.out, workers=args.workers, label=f"rerank {ds}")
        primary, secondary = ("addresses", "relation") if ds == "scifact" else (
            "answers", "on_subject")
        scores: dict[str, dict[str, dict[str, float]]] = {"primary": defaultdict(dict),
                                                          "secondary": defaultdict(dict)}
        for (q, d), r in zip(where, rows, strict=True):
            p1 = noul(r, primary)
            p2 = (1 - probs(r, "relation", POLARITY_LABELS)[2]) if ds == "scifact" else noul(
                r, secondary)
            scores["primary"][q][d] = -1.0 if math.isnan(p1) else p1
            scores["secondary"][q][d] = -1.0 if math.isnan(p2) else float(p2)
        per: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
        for q in qids:
            for which in ("primary", "secondary"):
                orders = rerank_orders(shortlist[q], scores[which][q])
                for arm_name, order in orders.items():
                    if which == "secondary" and arm_name == "embedder":
                        continue
                    key = arm_name if which == "primary" else f"{arm_name}_secondary"
                    per[key]["ndcg10"].append(ndcg10(order, qrels[q]))
                    per[key]["recall10"].append(
                        len(set(order[:10]) & set(qrels[q])) / len(qrels[q]))
        block: dict[str, Any] = {"queries": len(qids), "shortlist": TOP,
                                 "primary_question": primary,
                                 "secondary_question": secondary,
                                 "coverage_at_20": round(float(np.mean(
                                     [bool(set(shortlist[q]) & set(qrels[q])) for q in qids])), 4),
                                 "usage": usage_summary(rows, arm),
                                 "machine": sampler.summary()}
        base = np.array(per["embedder"]["ndcg10"])
        for key, m in per.items():
            v = np.array(m["ndcg10"])
            block[key] = {"ndcg10": round(float(v.mean()), 4),
                          "recall10": round(float(np.mean(m["recall10"])), 4)}
            if key != "embedder":
                d = v - base
                block[key]["minus_embedder"] = round(float(d.mean()), 4)
                block[key]["minus_embedder_ci"] = cluster_ci(mean_stat(d), list(range(len(d))))
        if ds == "scifact":
            block["mining"] = mining(args, arm, shortlist, rows, where, claims, pairs, vec)
            # post hoc (not declared): BEIR marks a claim's cited abstract relevant even when the
            # release labels it without evidence; split the queries by that label
            evidence = {p.claim_id for p in pairs if p.label != 2}
            for name, keep in (("with_evidence", [int(q) in evidence for q in qids]),
                               ("without_evidence", [int(q) not in evidence for q in qids])):
                mask = np.array(keep)
                block[f"post_hoc_{name}"] = {
                    "queries": int(mask.sum()),
                    **{k: round(float(np.array(per[k]["ndcg10"])[mask].mean()), 4)
                       for k in ("embedder", "judged", "fused")}}
        result[ds] = block
    return result


def mining(args: argparse.Namespace, arm: Arm, shortlist: dict[str, list[str]],
           rows: Sequence[dict[str, Any]], where: Sequence[tuple[str, str]],
           claims: dict[int, tuple[str, str]], pairs: Sequence[Pair],
           vec: SciFactVectors) -> dict[str, Any]:
    """Contradiction mining: every (dev claim, neighbour) pair of the embedder's top 20, ranked
    by the polarity answers; a labelled CONTRADICT pair is a hit, every other pair (supporting,
    cited without evidence, or never cited, which SciFact does not label) is not."""
    label = {(p.claim_id, p.doc_id): p.label for p in pairs}
    dev_claims = {p.claim_id for p in pairs if p.split == "dev"}
    keep = [i for i, (q, _) in enumerate(where) if int(q) in dev_claims]
    sub = [rows[i] for i in keep]
    ans = polarity_answers(sub)
    hit = np.array([int(label.get((int(where[i][0]), int(where[i][1]))) == 1) for i in keep],
                   dtype=np.int64)
    cos = np.array([vec.cosine(int(where[i][0]), int(where[i][1])) for i in keep])
    clusters = [int(where[i][0]) for i in keep]
    rng = np.random.default_rng(SEED)
    rankers = {"choice": ans["relation"][:, 1], "noul": ans["contradicts"],
               "noul_product": ans["product"][:, 1], "cosine": cos,
               "random": rng.random(len(keep))}
    total_contra = sum(1 for p in pairs if p.split == "dev" and p.label == 1)
    out: dict[str, Any] = {"pairs": len(keep), "hits_in_pool": int(hit.sum()),
                           "contradicting_pairs_in_dev": total_contra}
    for name, s in rankers.items():
        s = np.nan_to_num(s, nan=-1.0)
        out[name] = {"average_precision": round(average_precision(s, hit), 4),
                     **{f"precision_at_{k}": round(precision_at(s, hit, k), 4)
                        for k in (10, 25, 50, 100)}}
        out[name]["precision_at_50_ci"] = cluster_ci(precision_stat(s, hit, 50), clusters)
    return out


# ── topic (arXiv), kind, linking and duplicates (Stack Exchange), from the corpus instance ──────


def run_topic(args: argparse.Namespace, arm: Arm) -> dict[str, Any]:
    corpus = Corpus(args.corpus)
    archive_to_option = {a: name for name, (a, _) in dq.ARXIV_ARCHIVES.items()}
    options = list(dq.ARXIV_ARCHIVES)
    by_archive: dict[str, list[str]] = defaultdict(list)
    listed: dict[str, set[int]] = {}  # every option among an item's own cross-lists
    for m in corpus.meta("arxiv"):
        if m.get("categories"):
            archive = str(m["categories"][0]).split(".")[0]
            if archive in archive_to_option:
                by_archive[archive].append(str(m["id"]))
                listed[str(m["id"])] = {options.index(archive_to_option[c.split(".")[0]])
                                        for c in m["categories"]
                                        if c.split(".")[0] in archive_to_option}
    rng = random.Random(SEED)
    items: list[tuple[str, int]] = []
    for archive in sorted(by_archive):
        ids = sorted(by_archive[archive])
        for i in rng.sample(ids, min(args.per_archive, len(ids))):
            items.append((i, options.index(archive_to_option[archive])))
    texts = corpus.texts([f"corpus/arxiv/{i}" for i, _ in items])
    items = [(i, c) for i, c in items if f"corpus/arxiv/{i}" in texts]
    docs = []
    for i, _ in items:
        title, _, abstract = texts[f"corpus/arxiv/{i}"].partition("\n\n")
        docs.append((title.strip(), abstract.strip()))
    questions = dq.FAMILIES["subject_arxiv"]
    payloads = [{"model": arm.model,
                 "state": {"document": {"title": t, "text": cut(a)}}, "questions": questions}
                for t, a in docs]
    with Sampler() as sampler:
        rows = ask(arm, payloads, args.out, workers=args.workers, label="topic")
    y = np.array([c for _, c in items], dtype=np.int64)
    p = np.array([probs(r, "subject", options) for r in rows])
    pr = np.array([probs(r, "subject_reversed", options) for r in rows])
    vecs = embed([gemma_doc(t, a) for t, a in docs], args.out, "arxiv-docs")
    pk = knn_probs(vecs, y, len(options))
    top3 = np.argsort(-np.nan_to_num(p, nan=0.0), axis=1)[:, :3]
    flips = np.argmax(p, axis=1) != np.argmax(pr, axis=1)

    def any_listed(q: F64) -> float:
        """Post hoc (not declared): the top answer is among the item's own cross-lists."""
        top = np.argmax(np.nan_to_num(q, nan=0.0), axis=1)
        return round(float(np.mean([int(top[k]) in listed[i] for k, (i, _) in enumerate(items)])),
                     4)

    return {"benchmark": "topic", "arm": arm.name, "model": arm.model,
            "question_digest": dq.digest(questions), "items": len(items),
            "per_archive": dict(Counter(dq.ARXIV_ARCHIVES[options[c]][0] for _, c in items)),
            "choice": classification(y, p, options),
            "choice_reversed": classification(y, pr, options),
            "choice_top3_accuracy": round(float(np.mean([y[i] in top3[i]
                                                         for i in range(len(y))])), 4),
            "order_flips": round(float(np.mean(flips)), 4),
            "embedder_knn": classification(y, pk, options),
            "post_hoc_accuracy_any_listed_archive": {"choice": any_listed(p),
                                                     "embedder_knn": any_listed(pk)},
            "cross_listed_items": int(sum(len(listed[i]) > 1 for i, _ in items)),
            "choice_minus_knn_accuracy_ci": cluster_ci(
                lambda i: accuracy(y[i], p[i]) - accuracy(y[i], pk[i]), list(range(len(y)))),
            "usage": usage_summary(rows, arm), "machine": sampler.summary()}


def two_class(s: F64) -> F64:
    """A binary probability as the two-column table `classification` reads."""
    out: F64 = np.stack([1 - s, s], axis=1)
    return out


def se_sample(meta: Sequence[dict[str, Any]], kind: str, per_site: int,
              rng: random.Random) -> list[str]:
    by_site: dict[str, list[str]] = defaultdict(list)
    for m in meta:
        if m["kind"] == kind:
            by_site[m["site"]].append(str(m["id"]))
    out: list[str] = []
    for site in sorted(by_site):
        out += rng.sample(sorted(by_site[site]), min(per_site, len(by_site[site])))
    return out


def run_kind(args: argparse.Namespace, arm: Arm) -> dict[str, Any]:
    corpus = Corpus(args.corpus)
    meta = corpus.meta("stackexchange")
    rng = random.Random(SEED)
    ids = se_sample(meta, "question", args.per_site, rng) + se_sample(meta, "answer",
                                                                       args.per_site, rng)
    kind_of = {str(m["id"]): m["kind"] for m in meta}
    texts = corpus.texts([f"corpus/stackexchange/{i}" for i in ids])
    posts = []
    for i in ids:
        t = texts.get(f"corpus/stackexchange/{i}")
        if t is None:
            continue
        _, body = post_parts(t)
        if body:
            posts.append((i, body, int(kind_of[i] == "question")))
    payloads = [{"model": arm.model, "state": {"text": cut(b)}, "questions": dq.KIND}
                for _, b, _ in posts]
    with Sampler() as sampler:
        rows = ask(arm, payloads, args.out, workers=args.workers, label="kind")
    y = np.array([k for _, _, k in posts], dtype=np.int64)
    pq_ = np.array([noul(r, "asks_question") for r in rows])
    kinds = list(dq.KIND_OPTIONS)
    pk = np.array([probs(r, "kind", kinds) for r in rows])
    heur = np.array([float("?" in b) for _, b, _ in posts])
    vecs = embed([gemma_doc("", b) for _, b, _ in posts], args.out, "se-kind")
    knn = knn_probs(vecs, y, 2)[:, 1]
    two = two_class
    return {"benchmark": "kind", "arm": arm.name, "model": arm.model,
            "question_digest": dq.digest(dq.KIND), "posts": len(posts),
            "questions": int(y.sum()), "answers": int(len(y) - y.sum()),
            "noul": classification(y, two(pq_), ["answer", "question"], positive=1),
            "kind_choice_asks": classification(y, two(pk[:, 0]), ["answer", "question"],
                                               positive=1),
            "kind_choice_distribution": {
                "question": dict(zip(kinds, np.round(np.nanmean(pk[y == 1], axis=0), 3).tolist(),
                                     strict=True)),
                "answer": dict(zip(kinds, np.round(np.nanmean(pk[y == 0], axis=0), 3).tolist(),
                                   strict=True))},
            "question_mark": {"auroc": round(auroc(heur, y), 4),
                              "accuracy": round(float(np.mean(heur == y)), 4)},
            "embedder_knn": classification(y, two(knn), ["answer", "question"], positive=1),
            "noul_minus_question_mark_auroc_ci": cluster_ci(
                lambda i: auroc(pq_[i], y[i]) - auroc(heur[i], y[i]), list(range(len(y)))),
            "usage": usage_summary(rows, arm), "machine": sampler.summary()}


def run_linking(args: argparse.Namespace, arm: Arm) -> dict[str, Any]:
    corpus = Corpus(args.corpus)
    meta = corpus.meta("stackexchange")
    answers_of: dict[str, list[str]] = defaultdict(list)
    for m in meta:
        if m["kind"] == "answer" and m.get("parent"):
            answers_of[str(m["parent"])].append(str(m["id"]))
    rng = random.Random(SEED + 1)
    with_answers = sorted(q for q, a in answers_of.items() if a)
    picked = rng.sample(with_answers, 2 * args.questions)
    asked, distract = picked[: args.questions], picked[args.questions:]
    pool = [a for q in asked + distract for a in sorted(answers_of[q])]
    texts = corpus.texts([f"corpus/stackexchange/{i}" for i in asked + pool])
    q_text = {q: post_parts(texts[f"corpus/stackexchange/{q}"])
              for q in asked if f"corpus/stackexchange/{q}" in texts}
    a_body = {a: post_parts(texts[f"corpus/stackexchange/{a}"])[1]
              for a in pool if f"corpus/stackexchange/{a}" in texts}
    pool = [a for a in pool if a_body.get(a)]
    asked = [q for q in asked if q in q_text and q_text[q][1]]
    parent = {a: q for q in asked + distract for a in answers_of[q]}
    qv = embed([gemma_query("question answering", f"{q_text[q][0]}\n\n{q_text[q][1]}")
                for q in asked], args.out, "se-link-questions")
    av = embed([gemma_doc("", a_body[a]) for a in pool], args.out, "se-link-answers")
    idx, _ = top_k(qv, av, KNN)
    payloads, where = [], []
    for i, q in enumerate(asked):
        for j in idx[i]:
            a = pool[j]
            payloads.append({"model": arm.model,
                             "state": {"question": {"title": q_text[q][0],
                                                    "text": cut(q_text[q][1])},
                                       "reply": cut(a_body[a])},
                             "questions": dq.REPLY})
            where.append((q, a))
    with Sampler() as sampler:
        rows = ask(arm, payloads, args.out, workers=args.workers, label="linking")
    score = {k: noul(r, "answers_question") for k, r in zip(where, rows, strict=True)}
    stats: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    covered = 0
    for i, q in enumerate(asked):
        cands = [pool[j] for j in idx[i]]
        truth = {a for a in cands if parent.get(a) == q}
        if not truth:
            continue
        covered += 1
        orders = rerank_orders(cands, {a: (-1.0 if math.isnan(score[(q, a)]) else score[(q, a)])
                                       for a in cands})
        for name, order in orders.items():
            first = next(r for r, a in enumerate(order) if a in truth)
            stats[name]["mrr"].append(1.0 / (first + 1))
            stats[name]["hit1"].append(float(order[0] in truth))
    lab = np.array([int(parent.get(a) == q) for q, a in where], dtype=np.int64)
    sc = np.array([score[k] for k in where])
    e_mrr = np.array(stats["embedder"]["mrr"])
    out: dict[str, Any] = {"benchmark": "linking", "arm": arm.name, "model": arm.model,
                           "question_digest": dq.digest(dq.REPLY), "questions": len(asked),
                           "pool": len(pool), "covered_at_10": covered,
                           "pair_auroc": round(auroc(np.nan_to_num(sc, nan=0.0), lab), 4),
                           "usage": usage_summary(rows, arm), "machine": sampler.summary()}
    for name, m in stats.items():
        v = np.array(m["mrr"])
        out[name] = {"mrr10": round(float(v.mean()), 4),
                     "hit1": round(float(np.mean(m["hit1"])), 4)}
        if name != "embedder":
            d = v - e_mrr
            out[name]["mrr_minus_embedder_ci"] = cluster_ci(mean_stat(d), list(range(len(d))))
    return out


def run_duplicates(args: argparse.Namespace, arm: Arm) -> dict[str, Any]:
    corpus = Corpus(args.corpus)
    meta = corpus.meta("stackexchange")
    is_q = {str(m["id"]) for m in meta if m["kind"] == "question"}
    linked: dict[str, set[str]] = defaultdict(set)
    dup_pairs: set[tuple[str, str]] = set()
    for m in meta:
        for other, how in m.get("post_links", []):
            a, b = str(m["id"]), str(other)
            linked[a].add(b)
            linked[b].add(a)
            if how == "duplicate" and a in is_q and b in is_q and a != b:
                dup_pairs.add((min(a, b), max(a, b)))
    rng = random.Random(SEED + 2)
    pos = rng.sample(sorted(dup_pairs), min(args.pairs, len(dup_pairs)))
    ids = sorted({x for p in pos for x in p})
    texts = corpus.texts([f"corpus/stackexchange/{i}" for i in ids])
    post = {i: post_parts(texts[f"corpus/stackexchange/{i}"]) for i in ids
            if f"corpus/stackexchange/{i}" in texts}
    ids = [i for i in ids if i in post and post[i][1]]
    pos = [p for p in pos if p[0] in post and p[1] in post and post[p[0]][1] and post[p[1]][1]]
    vecs = embed([gemma_doc(post[i][0], post[i][1]) for i in ids], args.out, "se-dup")
    row_of = {i: k for k, i in enumerate(ids)}
    sims = vecs @ vecs.T
    neg = []
    for a, b in pos:
        order = np.argsort(-sims[row_of[a]], kind="stable")
        for j in order:
            c = ids[int(j)]
            if c not in (a, b) and c not in linked[a]:
                neg.append((a, c))
                break
    pairs = [(a, b, 1) for a, b in pos] + [(a, c, 0) for a, c in neg]
    payloads = [{"model": arm.model,
                 "state": {"first": {"title": post[a][0], "text": cut(post[a][1])},
                           "second": {"title": post[b][0], "text": cut(post[b][1])}},
                 "questions": dq.EQUIVALENCE} for a, b, _ in pairs]
    with Sampler() as sampler:
        rows = ask(arm, payloads, args.out, workers=args.workers, label="duplicates")
    y = np.array([k for _, _, k in pairs], dtype=np.int64)
    s = np.array([noul(r, "same_question") for r in rows])
    cos = np.array([float(sims[row_of[a], row_of[b]]) for a, b, _ in pairs])
    # post hoc (not declared): a "hub" is a post in three or more of the sampled duplicate pairs,
    # a canonical question that specific questions are closed against
    degree = Counter(x for p in pos for x in p)
    hub = np.array([int(k == 1 and (degree[a] >= 3 or degree[b] >= 3)) for a, b, k in pairs])
    plain = (y == 0) | (hub == 0)
    post_hoc = {"hub_posts": sum(1 for v in degree.values() if v >= 3),
                "positives_with_a_hub": int(hub.sum()),
                "share_above_half_with_hub": round(float(np.mean(s[hub == 1] > 0.5)), 4)
                if hub.sum() else None,
                "share_above_half_without_hub": round(float(np.mean(
                    s[(y == 1) & (hub == 0)] > 0.5)), 4),
                "auroc_without_hub_positives": round(auroc(s[plain], y[plain]), 4),
                "cosine_auroc_without_hub_positives": round(auroc(cos[plain], y[plain]), 4)}
    return {"benchmark": "duplicates", "arm": arm.name, "model": arm.model,
            "post_hoc_canonical_posts": post_hoc,
            "question_digest": dq.digest(dq.EQUIVALENCE), "positives": len(pos),
            "negatives": len(neg),
            "noul": classification(y, two_class(s), ["different", "same"], positive=1),
            "cosine_auroc": round(auroc(cos, y), 4),
            "noul_minus_cosine_auroc_ci": cluster_ci(
                lambda i: auroc(s[i], y[i]) - auroc(cos[i], y[i]), list(range(len(y)))),
            "usage": usage_summary(rows, arm), "machine": sampler.summary()}


# ── question discovery: keep a question only for the gain it measures on unseen rows ────────────


def candidate_columns(rows: Sequence[dict[str, Any]], qid: str, q: dq.Question) -> F64:
    """A question's answers as feature columns: a Noul's probability; a Score's expected level
    (scaled to [0, 1]) and its spread; a Choice's probabilities but the last."""
    if q["type"] == "noul":
        return np.array([[noul(r, qid)] for r in rows])
    if q["type"] == "score":
        n = len(q["criteria"])
        p = np.array([probs(r, qid, [str(i) for i in range(n)]) for r in rows])
        lv = np.arange(n)
        mean = p @ lv
        sd = np.sqrt(np.clip(p @ lv**2 - mean**2, 0, None))
        out: F64 = np.stack([mean / (n - 1), sd / (n - 1)], axis=1)
        return out
    names = list(q["criteria"])
    return np.array([probs(r, qid, names)[:-1] for r in rows])


def forward_select(base: F64, cands: dict[str, F64], y: I64, fit_rows: I64, check_rows: I64, *,
                   min_gain: float, max_keep: int, n_classes: int = 3) -> dict[str, Any]:
    """Greedy forward selection on check-row log loss: at each step the candidate that lowers it
    most is kept if the fall is at least `min_gain`; at most `max_keep` are kept. The models are
    fit on `fit_rows` only, so a question is judged on rows it was not fit on."""

    def score(cols: Sequence[str]) -> float:
        x = np.hstack([base] + [cands[c] for c in cols])
        predict = fit_logistic(x[fit_rows], y[fit_rows], n_classes)
        return log_loss(y[check_rows], predict(x[check_rows]))

    kept: list[str] = []
    current = score([])
    first = {c: round(current - score([c]), 5) for c in cands}
    path = [{"step": 0, "kept": [], "check_log_loss": round(current, 5)}]
    while len(kept) < max_keep:
        trial = {c: score(kept + [c]) for c in cands if c not in kept}
        if not trial:
            break
        best = min(trial, key=lambda c: trial[c])
        gain = current - trial[best]
        if gain < min_gain:
            path.append({"step": len(kept) + 1, "refused": best, "gain": round(gain, 5)})
            break
        kept.append(best)
        current = trial[best]
        path.append({"step": len(kept), "kept": list(kept), "gain": round(gain, 5),
                     "check_log_loss": round(current, 5)})
    return {"kept": kept, "first_step_gain": first, "path": path}


def shapley(players: Sequence[str], value: Callable[[frozenset[str]], float]) -> dict[str, float]:
    """Exact Shapley values over every coalition (SCL-3's attribution)."""
    from itertools import combinations

    n = len(players)
    memo: dict[frozenset[str], float] = {}

    def v(s: frozenset[str]) -> float:
        if s not in memo:
            memo[s] = value(s)
        return memo[s]

    out = {}
    for p in players:
        others = [q for q in players if q != p]
        total = 0.0
        for k in range(n):
            w = math.factorial(k) * math.factorial(n - k - 1) / math.factorial(n)
            for s in combinations(others, k):
                fs = frozenset(s)
                total += w * (v(fs | {p}) - v(fs))
        out[p] = round(total, 5)
    return out


def run_discovery(args: argparse.Namespace, arm: Arm) -> dict[str, Any]:
    corpus, claims, pairs = load_scifact(args.scifact)
    pol_rows = ask(arm, [polarity_payload(arm, claims[p.claim_id][1], *corpus[p.doc_id])
                         for p in pairs], args.out, workers=args.workers, label="polarity")
    payloads = [{"model": arm.model,
                 "state": polarity_state(claims[p.claim_id][1], *corpus[p.doc_id]),
                 "questions": dq.DISCOVERY} for p in pairs]
    with Sampler() as sampler:
        rows = ask(arm, payloads, args.out, workers=args.workers, label="discovery")
    vec = SciFactVectors(args.out, corpus, claims)
    y = np.array([p.label for p in pairs], dtype=np.int64)
    base = np.array([[vec.cosine(p.claim_id, p.doc_id)] for p in pairs])
    cands = {qid: candidate_columns(rows, qid, q) for qid, q in dq.DISCOVERY.items()}
    cands["relation"] = candidate_columns(pol_rows, "relation", dq.POLARITY["relation"])
    ok = ~np.isnan(np.hstack([base] + list(cands.values()))).any(axis=1)
    train_claims = sorted({p.claim_id for p in pairs if p.split == "train"})
    rng = random.Random(SEED + 3)
    rng.shuffle(train_claims)
    check_claims = set(train_claims[: int(0.4 * len(train_claims))])
    split = np.array(["test" if p.split == "dev" else
                      ("check" if p.claim_id in check_claims else "fit") for p in pairs])
    fit_rows = np.flatnonzero((split == "fit") & ok)
    check_rows = np.flatnonzero((split == "check") & ok)
    test_rows = np.flatnonzero((split == "test") & ok)
    train_rows = np.concatenate([fit_rows, check_rows])
    sel = forward_select(base, cands, y, fit_rows, check_rows, min_gain=args.min_gain,
                         max_keep=args.max_keep)

    def held_out(cols: Sequence[str], with_base: bool = True) -> F64:
        parts = ([base] if with_base else []) + [cands[c] for c in cols]
        x = np.hstack(parts) if parts else np.zeros((len(y), 1))
        return fit_logistic(x[train_rows], y[train_rows], 3)(x[test_rows])

    yt = y[test_rows]
    clusters = [pairs[i].claim_id for i in test_rows]
    arms = {"prior": np.tile(np.bincount(y[train_rows], minlength=3) / len(train_rows),
                             (len(test_rows), 1)),
            "embedder": held_out([]), "embedder_relation": held_out(["relation"]),
            "relation_alone": held_out(["relation"], with_base=False),
            "embedder_kept": held_out(sel["kept"]),
            "embedder_all": held_out(sorted(cands))}
    if sel["kept"]:
        arms["kept_alone"] = held_out(sel["kept"], with_base=False)
    table = {k: classification(yt, p, POLARITY_LABELS, clusters) for k, p in arms.items()}
    gain_ci = cluster_ci(lambda i: log_loss(yt[i], arms["embedder"][i])
                         - log_loss(yt[i], arms["embedder_kept"][i]), clusters)
    players = ["embedder"] + sel["kept"]

    def value(s: frozenset[str]) -> float:
        cols = [c for c in sel["kept"] if c in s]
        p = held_out(cols, with_base="embedder" in s) if (cols or "embedder" in s) else arms[
            "prior"]
        return log_loss(yt, arms["prior"]) - log_loss(yt, p)

    return {"benchmark": "discovery", "arm": arm.name, "model": arm.model,
            "candidates": {qid: {"digest": dq.digest({qid: q}), "type": q["type"]}
                           for qid, q in dq.DISCOVERY.items()} | {
                "relation": {"digest": dq.digest({"relation": dq.POLARITY["relation"]}),
                             "type": "choice"}},
            "rows": {"fit": len(fit_rows), "check": len(check_rows), "test": len(test_rows)},
            "rule": {"min_gain_nats": args.min_gain, "max_keep": args.max_keep,
                     "questions_per_request": len(dq.DISCOVERY)},
            "selection": sel, "held_out": table,
            "kept_gain_over_embedder_nats": round(log_loss(yt, arms["embedder"])
                                                  - log_loss(yt, arms["embedder_kept"]), 4),
            "kept_gain_ci": gain_ci,
            "shapley_nats": shapley(players, value) if len(players) <= 8 else None,
            "usage": usage_summary(rows, arm), "machine": sampler.summary()}


# ── controls ────────────────────────────────────────────────────────────────────────────────────


def run_controls(args: argparse.Namespace, arm: Arm) -> dict[str, Any]:
    """The context control (local): the same polarity requests to tev1:0.8b's own tag (2048
    tokens) and to the 8192-token tag; repeatability (either arm): the same requests sent again,
    bypassing the cache, compared with the first answers."""
    corpus, claims, pairs = load_scifact(args.scifact)
    rng = random.Random(SEED + 4)
    sample = rng.sample([p for p in pairs if p.split == "train"], args.control_n)
    first = ask(arm, [polarity_payload(arm, claims[p.claim_id][1], *corpus[p.doc_id])
                      for p in sample], args.out, workers=1, label="controls")
    out: dict[str, Any] = {"benchmark": "controls", "arm": arm.name, "model": arm.model,
                           "n": len(sample)}

    def compare(a: Sequence[dict[str, Any]], b: Sequence[dict[str, Any]]) -> dict[str, Any]:
        pa, pb = polarity_answers(a), polarity_answers(b)
        ok = ~np.isnan(pa["relation"]).any(axis=1) & ~np.isnan(pb["relation"]).any(axis=1)
        same = np.argmax(pa["relation"][ok], axis=1) == np.argmax(pb["relation"][ok], axis=1)
        dn = np.abs(np.concatenate([pa[k][ok] - pb[k][ok]
                                    for k in ("supports", "contradicts", "addresses")]))
        dc = np.abs(pa["relation"][ok] - pb["relation"][ok]).max(axis=1)
        return {"compared": int(ok.sum()), "choice_agreement": round(float(same.mean()), 4),
                "choice_max_abs_diff_median": round(float(np.median(dc)), 4),
                "choice_max_abs_diff_max": round(float(dc.max()), 4),
                "noul_abs_diff_median": round(float(np.median(dn)), 4),
                "noul_abs_diff_p90": round(float(np.percentile(dn, 90)), 4)}

    # the same payloads asked again under another cache name, so nothing is read from the cache
    twice = Arm(f"{arm.name}-repeat", arm.model, arm.hosted)
    again = ask(twice, [r["payload"] for r in first], args.out, workers=1, label="repeat")
    out["repeatability"] = compare(first, again)
    if not arm.hosted:
        base = Arm("local-2048", BASE_LOCAL_MODEL, False)
        rows_b = ask(base, [polarity_payload(base, claims[p.claim_id][1], *corpus[p.doc_id])
                            for p in sample], args.out, workers=1, label="context control")
        out["context_tag_vs_base"] = compare(first, rows_b)
        out["base_refusals"] = sum(1 for r in rows_b if "error" in r)
    return out


# ── the record ──────────────────────────────────────────────────────────────────────────────────


def run_report(args: argparse.Namespace) -> dict[str, Any]:
    """The record's JSON: every result file's aggregates. The corpus instance's benchmarks
    write aggregates only; the polarity examples are public SciFact text."""
    results: dict[str, Any] = {}
    for path in sorted(args.out.glob("result-*.json")):
        r = json.loads(path.read_text())
        results.setdefault(r["benchmark"], {})[r["arm"]] = r
    record = {"record": "docs/experiments/decision-integrators-2026-11-08.md",
              "generated": datetime.now(UTC).isoformat(timespec="seconds"),
              "questions": dq.manifest(), "hosted_ledger_usd": round(ledger_usd(args.out), 4),
              "results": results}
    RECORD_JSON.write_text(json.dumps(record, indent=1, ensure_ascii=False) + "\n")
    return record


BENCHMARKS: dict[str, Callable[[argparse.Namespace, Arm], dict[str, Any]]] = {
    "polarity": run_polarity, "rerank": run_rerank, "topic": run_topic, "kind": run_kind,
    "linking": run_linking, "duplicates": run_duplicates, "discovery": run_discovery,
    "controls": run_controls,
}


def main(argv: Iterable[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0] if __doc__ else None)
    ap.add_argument("benchmark", choices=[*BENCHMARKS, "report"])
    ap.add_argument("--out", type=Path,
                    default=Path.home() / ".cache" / "mind-palace" / "decision-integrators")
    ap.add_argument("--arms", default="local", help="comma-separated: local, hosted")
    ap.add_argument("--scifact", type=Path, help="the SciFact release's data directory")
    ap.add_argument("--corpus", type=Path, help="the corpus instance's root (read-only)")
    ap.add_argument("--collections", default="scifact,nfcorpus")
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--per-archive", type=int, default=60)
    ap.add_argument("--per-site", type=int, default=100)
    ap.add_argument("--questions", type=int, default=300)
    ap.add_argument("--pairs", type=int, default=200)
    ap.add_argument("--min-gain", type=float, default=0.005)
    ap.add_argument("--max-keep", type=int, default=6)
    ap.add_argument("--control-n", type=int, default=60)
    a = ap.parse_args(list(argv) if argv is not None else None)
    a.collections = [c for c in a.collections.split(",") if c]
    a.out.mkdir(parents=True, exist_ok=True)
    if a.benchmark == "report":
        run_report(a)
        return 0
    for name in a.arms.split(","):
        arm = ARMS[name]
        try:
            result = BENCHMARKS[a.benchmark](a, arm)
        except BudgetStopped as e:
            print(f"[{name}] {e}; ledger ${ledger_usd(a.out):.4f}", file=sys.stderr)
            return 3
        result["finished"] = datetime.now(UTC).isoformat(timespec="seconds")
        if arm.hosted:
            result["hosted_ledger_usd"] = round(ledger_usd(a.out), 4)
        (a.out / f"result-{a.benchmark}-{name}.json").write_text(
            json.dumps(result, indent=1, ensure_ascii=False) + "\n")
        print(f"[{name}] {a.benchmark} written", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
