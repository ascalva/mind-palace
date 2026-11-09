"""What every experiment of the study shares: the collections, the embedder and its cache, the
server's tokenizer, document-level retrieval, the metrics and the paired test.

- **Collections.** A collection is documents (an id, a title and the item's bytes as landed),
  queries, and graded relevance. The public sets are written as items `{title}\n\n{text}`, the
  corpus readers' form; the corpus subsample W is read from the corpus instance's catalog and raw
  store, read only (`?immutable=1`, and no store object is opened, so nothing is created there).
- **The embedder.** `Embedder` posts to llama-server's `/v1/embeddings`, `batch` texts a request
  and one request at a time, every request through the store's length fit (`embed_fitting`).
  Before each request it reads the server's `/slots`: a busy slot then is another caller's, since
  this client's previous request has returned. Every vector is cached by the sha256 of its input
  (the template applied), so arms that share a chunk share its vector.
- **Tokens.** `ServerTokenizer` reads `/tokenize` with each token's piece and turns the pieces
  into character spans, so a span of text can be counted, cut at token boundaries, or matched to
  the tokens of a late-chunking pass. Counts are cached like vectors.
- **Retrieval.** A document's score is its best chunk's cosine; the first ten documents by score
  are its ranking (the plane's reading at the document grain). recall@10 and nDCG@10 per query;
  the paired difference against a reference arm is tested by the repository's sign-flip test
  (`eval/predictions/scoring.py::cluster_signflip`, each query its own cluster), and Holm's
  adjustment runs over an experiment's arms.
"""

from __future__ import annotations

import codecs
import hashlib
import json
import math
import random
import sqlite3
import statistics
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import numpy.typing as npt

from core.ingest.embed import embed_fitting
from core.kernel.ingest.logseq import _decode, strip_properties
from eval.predictions.scoring import Pair, cluster_signflip, holm
from eval.two_phase_bench import load_beir, ndcg_at, recall_at

DATA = Path.home() / "models" / "bench-data"
K = 10
DIM = 768
DOC_NONE = "title: none | text: {text}"
DOC_TITLE = "title: {title} | text: {text}"
QUERY_SEARCH = "task: search result | query: {text}"
QUERY_QA = "task: question answering | query: {text}"
QUERY_FACT = "task: fact checking | query: {text}"
MODEL = "embeddinggemma-2-Q8_0"           # the cache's key: one model, one geometry
BOS, EOS = 2, 1                           # the model's special tokens (its GGUF says so)
FLIPS = 20000

F32 = npt.NDArray[np.float32]
I64 = npt.NDArray[np.int64]


# ── collections ──────────────────────────────────────────────────────────────────────────────────

@dataclass
class Collection:
    """Documents as items (id -> title and bytes), queries (id -> text) and graded relevance
    (query -> document -> grade). `families` names each query's family when there are several."""

    name: str
    docs: dict[str, tuple[str, bytes]]
    queries: dict[str, str]
    qrels: dict[str, dict[str, int]]
    families: dict[str, str] = field(default_factory=dict)

    def body(self, doc: str) -> str:
        """The text the landing chunks: the item's bytes decoded, property lines stripped
        (`derive_chunks`'s own derivation)."""
        return strip_properties(_decode(self.docs[doc][1]))

    def subset(self, family: str) -> list[str]:
        return [q for q in self.queries if self.families.get(q, "") == family]


def beir(name: str, root: Path = DATA) -> Collection:
    corpus, queries, qrels = load_beir(root / name)
    docs = {d: (t, f"{t}\n\n{x}".strip().encode("utf-8")) for d, (t, x) in sorted(corpus.items())}
    return Collection(name, docs, queries, qrels, {q: name for q in queries})


def corpus_w(instance: Path, *, articles: int = 600, seed: int = 0,
             per_source: int = 500) -> Collection:
    """W: the Wikipedia articles that are gold for the corpus battery's link families, and
    articles drawn at random to `articles` in all; the link questions (family `link`) and each
    pooled article's title (family `title`). Read only."""
    from eval.corpus.battery import questions
    from eval.corpus.data import SOURCES, load
    from eval.corpus.edges import build, twins

    c = load(instance / "sources", SOURCES)
    rel = build(c)
    tw = twins(rel)
    qs = questions(c, rel, tw, stream_contents(instance, c, set(tw)), per_source=per_source)
    link = [q for q in qs if q.family.startswith("link:")]
    gold = sorted(set().union(*(q.gold for q in link)))
    rng = random.Random(seed)
    others = sorted(set(c.of("wikipedia").tolist()) - set(gold))
    pool = gold + sorted(rng.sample(others, max(0, articles - len(gold))))
    catalog = read_catalog(instance)
    docs: dict[str, tuple[str, bytes]] = {}
    for g in pool:
        path = c.paths[g]
        title, digest = catalog[path]
        docs[path] = (title, raw_bytes(instance, digest))
    queries: dict[str, str] = {}
    qrels: dict[str, dict[str, int]] = {}
    families: dict[str, str] = {}
    for i, q in enumerate(link):
        qid = f"link-{i}"
        queries[qid] = q.text
        qrels[qid] = {c.paths[g]: 1 for g in q.gold}
        families[qid] = "link"
    for path, (title, _) in docs.items():
        qid = f"title-{path}"
        queries[qid] = title
        qrels[qid] = {path: 1}
        families[qid] = "title"
    return Collection("W", docs, queries, qrels, families)


def stream_contents(instance: Path, c: Any, gids: set[int]) -> dict[int, str]:
    """The landed text of some items, read from their streams (stage 1's `_contents`, with the
    instance's root given instead of read from a configuration)."""
    from core.ingest.stream import manifest

    out: dict[int, str] = {}
    want = {c.paths[g]: g for g in gids}
    for s in c.sources:
        root = instance / "sources" / s
        for p in manifest(root):
            with (root / "stream" / p.file).open(encoding="utf-8") as fh:
                for line in fh:
                    doc = json.loads(line)
                    g = want.get(f"corpus/{s}/{doc['id']}")
                    if g is not None:
                        out[g] = str(doc["content"])
    return out


def read_catalog(instance: Path) -> dict[str, tuple[str, str]]:
    """Every active entry of the instance's catalog: path -> (title, digest), read only."""
    con = sqlite3.connect(f"file:{instance / 'data' / 'vault_catalog.sqlite'}?mode=ro&immutable=1",
                          uri=True)
    try:
        return {str(p): (str(t), str(d)) for p, t, d in con.execute(
            "SELECT source_path, title, digest FROM vault_files WHERE active = 1")}
    finally:
        con.close()


def raw_bytes(instance: Path, digest: str) -> bytes:
    """An object of the instance's raw store, read by path (no store object, nothing created)."""
    return (instance / "data" / "raw" / digest[:2] / digest).read_bytes()


# ── the cache ────────────────────────────────────────────────────────────────────────────────────

class Cache:
    """Vectors and token counts by the sha256 of their input, in one SQLite file."""

    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(path), isolation_level=None, timeout=120.0)
        for attempt in range(60):          # two runs may open a new cache at once
            try:
                self.conn.execute("PRAGMA journal_mode=WAL")
                break
            except sqlite3.OperationalError:
                time.sleep(1.0 + attempt)
        self.conn.executescript(
            "CREATE TABLE IF NOT EXISTS vec (key TEXT PRIMARY KEY, v BLOB NOT NULL);"
            "CREATE TABLE IF NOT EXISTS ntok (key TEXT PRIMARY KEY, n INTEGER NOT NULL);")

    @staticmethod
    def key(text: str, salt: str = MODEL) -> str:
        return hashlib.sha256(f"{salt}\x00{text}".encode()).hexdigest()

    def vectors(self, keys: Sequence[str]) -> dict[str, F32]:
        out: dict[str, F32] = {}
        for i in range(0, len(keys), 500):
            batch = list(keys[i:i + 500])
            marks = ",".join("?" for _ in batch)
            for k, v in self.conn.execute(f"SELECT key, v FROM vec WHERE key IN ({marks})",
                                          batch):
                out[str(k)] = np.frombuffer(v, dtype=np.float32).copy()
        return out

    def put_vectors(self, rows: Iterable[tuple[str, F32]]) -> None:
        self.conn.execute("BEGIN")
        self.conn.executemany("INSERT OR REPLACE INTO vec (key, v) VALUES (?, ?)",
                              [(k, np.asarray(v, dtype=np.float32).tobytes()) for k, v in rows])
        self.conn.execute("COMMIT")

    def counts(self, keys: Sequence[str]) -> dict[str, int]:
        out: dict[str, int] = {}
        for i in range(0, len(keys), 500):
            batch = list(keys[i:i + 500])
            marks = ",".join("?" for _ in batch)
            for k, n in self.conn.execute(f"SELECT key, n FROM ntok WHERE key IN ({marks})",
                                          batch):
                out[str(k)] = int(n)
        return out

    def put_counts(self, rows: Iterable[tuple[str, int]]) -> None:
        self.conn.execute("BEGIN")
        self.conn.executemany("INSERT OR REPLACE INTO ntok (key, n) VALUES (?, ?)", list(rows))
        self.conn.execute("COMMIT")


# ── the server ───────────────────────────────────────────────────────────────────────────────────

def post(port: int, path: str, body: dict[str, Any], timeout: float = 600.0) -> Any:
    req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:     # the server's message carries a refusal for length
        raise RuntimeError(f"{e.code}: {e.read().decode('utf-8', 'replace')}") from None


def busy_slots(port: int) -> int | None:
    from eval.two_phase_bench import busy_slots as probe

    return probe(port)


def unit(x: F32) -> F32:
    return (x / np.maximum(np.linalg.norm(x, axis=-1, keepdims=True), 1e-12)).astype(np.float32)


@dataclass
class Ledger:
    """What one phase of embedding cost and met: requests, texts sent, inputs cut to fit, the
    busy slots of other callers seen before each request, and seconds."""

    requests: int = 0
    texts: int = 0
    cut: int = 0
    probes: int = 0
    probes_busy: int = 0
    seconds: float = 0.0

    def summary(self) -> dict[str, Any]:
        return {"requests": self.requests, "texts": self.texts, "cut": self.cut,
                "probes": self.probes, "probes_with_another_caller": self.probes_busy,
                "seconds": round(self.seconds, 1)}


class Embedder:
    """Vectors for full inputs (templates applied by the caller), unit length, float32, cached;
    one stream of `batch` texts a request."""

    def __init__(self, cache: Cache, *, port: int = 8081, batch: int = 64) -> None:
        self.cache, self.port, self.batch = cache, port, batch
        self.ledger = Ledger()

    def _request(self, texts: list[str]) -> list[list[float]]:
        n = busy_slots(self.port)
        if n is not None:
            self.ledger.probes += 1
            self.ledger.probes_busy += int(n > 0)
        out = post(self.port, "/v1/embeddings", {"input": texts, "model": MODEL})
        self.ledger.requests += 1
        self.ledger.texts += len(texts)
        rows = sorted(out["data"], key=lambda d: int(d["index"]))
        return [[float(x) for x in r["embedding"]] for r in rows]

    def vectors(self, inputs: Sequence[str], *, log: Callable[[str], None] | None = None) -> F32:
        keys = [Cache.key(t) for t in inputs]
        have = self.cache.vectors(sorted(set(keys)))
        todo = sorted({k: t for k, t in zip(keys, inputs, strict=True) if k not in have}.items())
        t0 = time.monotonic()
        for i in range(0, len(todo), self.batch):
            group = todo[i:i + self.batch]
            vecs, cuts = embed_fitting(self._request, [t for _, t in group])
            self.ledger.cut += len(cuts)
            rows = [(k, unit(np.asarray(v, dtype=np.float32))) for (k, _), v in
                    zip(group, vecs, strict=True)]
            self.cache.put_vectors(rows)
            have.update(rows)
            if log is not None and (i // self.batch) % 50 == 0:
                log(f"    embedded {i + len(group)} of {len(todo)} new inputs")
        self.ledger.seconds += time.monotonic() - t0
        if not keys:
            return np.zeros((0, DIM), dtype=np.float32)
        return np.stack([have[k] for k in keys]).astype(np.float32)


class ServerTokenizer:
    """The embedder's own tokens of a text, from the server's `/tokenize`, as character spans
    (special tokens left out); counts cached."""

    def __init__(self, cache: Cache, *, port: int = 8081) -> None:
        self.cache, self.port = cache, port
        self._spans: dict[str, list[tuple[int, int]]] = {}

    def spans(self, text: str) -> list[tuple[int, int]]:
        """Each token's `[start, end)` in `text`; a token that completes no character (a byte
        of a character split over several tokens) has an empty span, and the character goes to
        the token that completes it. Kept in memory for the run."""
        if not text:
            return []
        if text not in self._spans:
            self._spans[text] = self._read_spans(text)
        return self._spans[text]

    def _read_spans(self, text: str) -> list[tuple[int, int]]:
        toks = post(self.port, "/tokenize", {"content": text, "add_special": False,
                                             "with_pieces": True})["tokens"]
        dec = codecs.getincrementaldecoder("utf-8")(errors="replace")
        pos, out = 0, []
        for t in toks:
            p = t["piece"]
            s = dec.decode(bytes(p) if isinstance(p, list) else str(p).encode("utf-8"))
            out.append((pos, pos + len(s)))
            pos += len(s)
        if pos != len(text):        # the pieces do not rebuild the text: spread them evenly
            n = len(out)
            out = [(len(text) * i // n, len(text) * (i + 1) // n) for i in range(n)]
        return out

    def ids(self, text: str) -> list[int]:
        return [int(t) for t in post(self.port, "/tokenize",
                                     {"content": text, "add_special": False})["tokens"]]

    def count(self, texts: Sequence[str]) -> list[int]:
        """Each input's tokens, special tokens included (what the server embeds)."""
        keys = [Cache.key(t, salt=f"{MODEL}/ntok") for t in texts]
        have = self.cache.counts(sorted(set(keys)))
        new: list[tuple[str, int]] = []
        for k, t in zip(keys, texts, strict=True):
            if k not in have:
                n = len(post(self.port, "/tokenize", {"content": t, "add_special": True})
                        ["tokens"])
                have[k] = n
                new.append((k, n))
        if new:
            self.cache.put_counts(new)
        return [have[k] for k in keys]


# ── retrieval ────────────────────────────────────────────────────────────────────────────────────

@dataclass
class Chunked:
    """A collection's chunks under one arm: each chunk's text and document, chunks grouped by
    document in document order."""

    texts: list[str]
    doc_of: I64                      # chunk -> document number
    docs: list[str]                  # document number -> id

    @property
    def starts(self) -> I64:
        """The first chunk of each document that has one (for `np.maximum.reduceat`)."""
        return np.flatnonzero(np.r_[True, self.doc_of[1:] != self.doc_of[:-1]]).astype(np.int64)

    def atoms(self) -> int:
        return len(set(self.texts))


def chunked(col: Collection, chunk: Callable[[str, str], list[str]]) -> Chunked:
    """Every document's chunks by `chunk(doc_id, body)`, in document order."""
    texts: list[str] = []
    doc_of: list[int] = []
    docs = list(col.docs)
    for i, d in enumerate(docs):
        for t in chunk(d, col.body(d)):
            texts.append(t)
            doc_of.append(i)
    return Chunked(texts, np.asarray(doc_of, dtype=np.int64), docs)


def rank_documents(qv: F32, cv: F32, ch: Chunked, k: int = K, block: int = 256) -> list[list[str]]:
    """Each query's first `k` documents by their best chunk's cosine."""
    starts = ch.starts
    doc_ids = [ch.docs[int(ch.doc_of[s])] for s in starts]
    out: list[list[str]] = []
    for s in range(0, len(qv), block):
        sims = qv[s:s + block] @ cv.T
        best = np.maximum.reduceat(sims, starts, axis=1)
        kk = min(k, best.shape[1])
        part = np.argpartition(-best, kth=kk - 1, axis=1)[:, :kk]
        vals = np.take_along_axis(best, part, axis=1)
        order = np.take_along_axis(part, np.argsort(-vals, axis=1, kind="stable"), axis=1)
        out.extend([[doc_ids[int(j)] for j in row] for row in order])
    return out


def score(col: Collection, qids: Sequence[str], ranked: Sequence[Sequence[str]]
          ) -> dict[str, list[float]]:
    """recall@10 and nDCG@10 of each query, in `qids` order."""
    return {"recall": [recall_at(r, col.qrels[q]) for q, r in zip(qids, ranked, strict=True)],
            "ndcg": [ndcg_at(r, col.qrels[q]) for q, r in zip(qids, ranked, strict=True)]}


def paired(arm: Sequence[float], ref: Sequence[float], qids: Sequence[str]) -> dict[str, float]:
    """The mean of `arm - ref` over queries, its 95% interval and two-sided p, by the
    repository's sign-flip test, each query its own cluster."""
    ps = [Pair(q, "0", q, float(a) - float(b)) for q, a, b in zip(qids, arm, ref, strict=True)]
    if all(p.d == 0 for p in ps):
        return {"mean": 0.0, "lo": 0.0, "hi": 0.0, "p": 1.0}
    iv = cluster_signflip(ps, flips=FLIPS, seed=0, alpha=0.05)
    return {"mean": iv.mean, "lo": iv.lo, "hi": iv.hi, "p": iv.p_value}


def compare(arms: dict[str, dict[str, list[float]]], ref: str, qids: Sequence[str],
            metrics: Sequence[str] = ("recall", "ndcg")) -> dict[str, Any]:
    """Every arm's mean per metric, and each arm against `ref`: the paired difference, its
    interval, p and Holm's p over the arms."""
    out: dict[str, Any] = {"queries": len(qids), "reference": ref, "arms": {}}
    for name, m in arms.items():
        out["arms"][name] = {mt: round(statistics.fmean(m[mt]), 4) for mt in metrics}
    for mt in metrics:
        others = [a for a in arms if a != ref]
        tests = {a: paired(arms[a][mt], arms[ref][mt], qids) for a in others}
        adj = holm([tests[a]["p"] for a in others]) if others else []
        for a, p_holm in zip(others, adj, strict=True):
            t = tests[a]
            out["arms"][a][f"{mt}_vs_ref"] = {
                "mean": round(t["mean"], 4), "lo": round(t["lo"], 4), "hi": round(t["hi"], 4),
                "p": round(t["p"], 4), "p_holm": round(p_holm, 4),
                "verdict": verdict(t["mean"], t["lo"], p_holm)}
    return out


def verdict(mean: float, lo: float, p_holm: float, margin: float = 0.01) -> str:
    """The record's decision words: better, worse, no worse (the interval's lower end at or
    above -margin), or undecided."""
    if p_holm < 0.05:
        return "better" if mean > 0 else "worse"
    if not math.isnan(lo) and lo >= -margin:
        return "no worse"
    return "undecided"


def float16_bytes(vectors: int, dim: int = DIM) -> int:
    return vectors * dim * 2


def quantiles(xs: Sequence[float]) -> dict[str, float]:
    if not xs:
        return {}
    ys = sorted(xs)
    return {"p50": float(ys[len(ys) // 2]), "p90": float(ys[int(0.9 * (len(ys) - 1))]),
            "max": float(ys[-1]), "mean": round(statistics.fmean(ys), 1)}


def write(path: Path | None, obj: Any) -> None:
    text = json.dumps(obj, indent=1, default=float)
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + "\n")
    print(text)
