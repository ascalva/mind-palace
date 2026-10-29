"""Embedder benchmark — retrieval quality, throughput, memory, and the σ transfer.

    uv run python eval/embedder_bench.py [--only NAME ...] [--out PATH]

Each candidate GGUF is served by its own `llama-server --embedding` on 127.0.0.1:8082, one at a
time, then stopped. Measured per candidate:

* retrieval on two public BEIR sets read from local files (SciFact: claims → supporting/refuting
  abstracts; NFCorpus: health questions → documents): nDCG@10 and Recall@10, graded qrels;
* throughput (documents/s and characters/s while embedding the corpora) and peak server RSS —
  the embedder shares the machine with the 27B, so footprint is part of quality here;
* the σ transfer: every pairwise cosine among the palace's own L0 chunks. The palace's thresholds
  (σ = 0.58 for theme clusters, 0.93 for near-duplicates) were calibrated on Qwen3-Embedding-4B,
  so for each candidate this reports the cosine at the SAME quantile of the pair distribution —
  the value that would keep the same fraction of pairs above the line.

Each model gets its own documented prompt format: Qwen embedders take `Instruct: …\\nQuery:…` on
queries and plain documents; EmbeddingGemma-2 takes `task: … | query: …` and `title: … | text: …`.
Datasets live outside the repo (`~/models/bench-data`, downloaded from the BeIR mirrors on
Hugging Face); nothing here touches the network.
"""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
import threading
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root on path

MODELS = Path.home() / "models"
DATA = MODELS / "bench-data"
PORT = 8082
DOC_CHARS = 2000  # documents are cut here (≈ 500 tokens) so every candidate sees the same text
BATCH = 32


@dataclass(frozen=True)
class Candidate:
    name: str
    path: Path
    pooling: str  # llama-server --pooling
    style: str  # "qwen" | "gemma" — the prompt format the model was trained with


CANDIDATES = [  # smallest first, so a long run yields results early; the 4B reference last
    Candidate(
        "embeddinggemma-2-q8",
        MODELS / "embeddinggemma-2/embeddinggemma-2-Q8_0.gguf",
        "mean",
        "gemma",
    ),
    Candidate(
        "qwen3-embedding-0.6b-q8",
        MODELS / "qwen3-embedding/Qwen3-Embedding-0.6B-Q8_0.gguf",
        "last",
        "qwen",
    ),
    Candidate(
        "qwen3-vl-embedding-2b-q8",
        MODELS / "qwen3-vl-embedding/Qwen3-VL-Embedding-2B.Q8_0.gguf",
        "last",
        "qwen",
    ),
    Candidate(
        "qwen3-embedding-4b-q4km",
        MODELS / "qwen3-embedding/Qwen3-Embedding-4B-Q4_K_M.gguf",
        "last",
        "qwen",
    ),
    # measured 2026-10-28: nDCG@10 0.786 / 0.409, 0.9 docs/s, 6.04 GB — too slow and too large
    # to run beside the 27B; kept for completeness, excluded from the default run
    Candidate(
        "qwen3-embedding-8b-q4km",
        MODELS / "qwen3-embedding/Qwen3-Embedding-8B-Q4_K_M.gguf",
        "last",
        "qwen",
    ),
]

QWEN_TASK = {
    "scifact": "Given a scientific claim, retrieve documents that support or refute the claim",
    "nfcorpus": "Given a question, retrieve relevant documents that best answer the question",
}
GEMMA_TASK = {"scifact": "fact checking", "nfcorpus": "question answering"}


def fmt_query(c: Candidate, ds: str, q: str) -> str:
    if c.style == "gemma":
        return f"task: {GEMMA_TASK[ds]} | query: {q}"
    return f"Instruct: {QWEN_TASK[ds]}\nQuery:{q}"


def fmt_doc(c: Candidate, title: str, text: str) -> str:
    text = text[:DOC_CHARS]
    if c.style == "gemma":
        return f"title: {title or 'none'} | text: {text}"
    return f"{title}\n{text}" if title else text


# ── data ────────────────────────────────────────────────────────────────────────────────────────


def load_beir(
    ds: str,
) -> tuple[dict[str, tuple[str, str]], dict[str, str], dict[str, dict[str, int]]]:
    import pyarrow.parquet as pq

    corpus = {
        r["_id"]: (r.get("title") or "", r["text"])
        for r in pq.read_table(DATA / ds / "corpus-00000-of-00001.parquet").to_pylist()
    }
    queries = {
        r["_id"]: r["text"]
        for r in pq.read_table(DATA / ds / "queries-00000-of-00001.parquet").to_pylist()
    }
    qrels: dict[str, dict[str, int]] = {}
    for i, line in enumerate((DATA / ds / "test.tsv").read_text().splitlines()):
        if i == 0:
            continue  # header: query-id corpus-id score
        qid, did, score = line.split("\t")
        if int(score) > 0:
            qrels.setdefault(qid, {})[did] = int(score)
    queries = {q: t for q, t in queries.items() if q in qrels}
    return corpus, queries, qrels


def palace_chunks() -> list[str]:
    from config.loader import load_config
    from core.stores.vectorstore import VectorStore

    cfg = load_config()
    rows = VectorStore(cfg.paths.vector_store, dim=cfg.embedding.dim).all_rows()
    return [str(r["text"]) for r in rows if r.get("text")]


# ── metrics ─────────────────────────────────────────────────────────────────────────────────────


def ndcg_at_10(ranked: list[str], rels: dict[str, int]) -> float:
    dcg = sum((2 ** rels.get(d, 0) - 1) / math.log2(i + 2) for i, d in enumerate(ranked[:10]))
    ideal = sorted(rels.values(), reverse=True)[:10]
    idcg = sum((2**r - 1) / math.log2(i + 2) for i, r in enumerate(ideal))
    return dcg / idcg if idcg else 0.0


def recall_at_10(ranked: list[str], rels: dict[str, int]) -> float:
    return len(set(ranked[:10]) & set(rels)) / len(rels)


# ── the server ──────────────────────────────────────────────────────────────────────────────────


class Server:
    def __init__(self, c: Candidate):
        self.proc = subprocess.Popen(
            [
                "llama-server",
                "-m",
                str(c.path),
                "--embedding",
                "--pooling",
                c.pooling,
                "-c",
                "8192",
                "-np",
                "4",
                "-b",
                "8192",
                "-ub",
                "2048",
                "-fa",
                "on",
                "--host",
                "127.0.0.1",
                "--port",
                str(PORT),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self.peak_rss_kb = 0
        self._stop = threading.Event()
        threading.Thread(target=self._watch_rss, daemon=True).start()
        deadline = time.time() + 180
        while time.time() < deadline:
            if self.proc.poll() is not None:
                raise RuntimeError(
                    f"llama-server exited with {self.proc.returncode} loading {c.name}"
                )
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/health", timeout=2) as r:
                    if r.status == 200:
                        return
            except Exception:
                pass
            time.sleep(1)
        self.close()
        raise RuntimeError(f"{c.name} not healthy after 180 s")

    def _watch_rss(self) -> None:
        while not self._stop.is_set() and self.proc.poll() is None:
            out = subprocess.run(
                ["ps", "-o", "rss=", "-p", str(self.proc.pid)], capture_output=True, text=True
            )
            if out.stdout.strip():
                self.peak_rss_kb = max(self.peak_rss_kb, int(out.stdout.strip()))
            time.sleep(0.5)

    def embed(self, texts: list[str]) -> np.ndarray:
        vecs: list[list[float]] = []
        for i in range(0, len(texts), BATCH):
            body = json.dumps({"input": texts[i : i + BATCH]}).encode()
            req = urllib.request.Request(
                f"http://127.0.0.1:{PORT}/v1/embeddings",
                data=body,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=600) as r:
                rows = sorted(json.loads(r.read())["data"], key=lambda d: d["index"])
            vecs.extend(row["embedding"] for row in rows)
        m = np.asarray(vecs, dtype=np.float32)
        return m / np.linalg.norm(m, axis=1, keepdims=True)

    def close(self) -> None:
        self._stop.set()
        self.proc.terminate()
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            # llama-server can wedge on SIGTERM mid-request (dn-local-model-runtime)
            self.proc.kill()
            self.proc.wait()


# ── one candidate ───────────────────────────────────────────────────────────────────────────────


def run_candidate(c: Candidate, datasets: dict[str, Any], chunks: list[str]) -> dict[str, Any]:
    out: dict[str, Any] = {"name": c.name, "file_gb": round(c.path.stat().st_size / 1e9, 2)}
    t0 = time.perf_counter()
    server = Server(c)
    out["load_s"] = round(time.perf_counter() - t0, 1)
    try:
        docs_total, chars_total, embed_s = 0, 0, 0.0
        for ds, (corpus, queries, qrels) in datasets.items():
            ids = list(corpus)
            texts = [fmt_doc(c, *corpus[d]) for d in ids]
            t = time.perf_counter()
            dmat = server.embed(texts)
            embed_s += time.perf_counter() - t
            docs_total += len(texts)
            chars_total += sum(len(x) for x in texts)
            qids = list(queries)
            qmat = server.embed([fmt_query(c, ds, queries[q]) for q in qids])
            scores = qmat @ dmat.T
            top = np.argsort(-scores, axis=1)[:, :10]
            ranked = [[ids[j] for j in row] for row in top]
            pairs = list(zip(qids, ranked, strict=True))
            out[ds] = {
                "ndcg@10": round(float(np.mean([ndcg_at_10(r, qrels[q]) for q, r in pairs])), 4),
                "recall@10": round(
                    float(np.mean([recall_at_10(r, qrels[q]) for q, r in pairs])), 4
                ),
                "queries": len(qids),
                "docs": len(ids),
                "dim": int(dmat.shape[1]),
            }
        out["docs_per_s"] = round(docs_total / embed_s, 1)
        out["chars_per_s"] = round(chars_total / embed_s)
        if len(chunks) >= 2:
            cmat = server.embed(chunks)
            sims = (cmat @ cmat.T)[np.triu_indices(len(chunks), k=1)]
            out["palace_pairs"] = {"n": int(sims.size), "sims": sims.round(4).tolist()}
    finally:
        out["peak_rss_gb"] = round(server.peak_rss_kb / 1e6, 2)
        server.close()
    return out


def sigma_transfer(
    results: list[dict[str, Any]], reference: str, thresholds: dict[str, float]
) -> None:
    """For each candidate, the cosine at the quantile where the reference model's thresholds
    sit."""
    ref = next((r for r in results if r["name"] == reference and "palace_pairs" in r), None)
    if ref is None:
        return
    ref_sims = np.asarray(ref["palace_pairs"]["sims"])
    for r in results:
        if "palace_pairs" not in r:
            continue
        sims = np.asarray(r["palace_pairs"]["sims"])
        r["sigma_transfer"] = {}
        for label, value in thresholds.items():
            frac_above = float(np.mean(ref_sims >= value))
            r["sigma_transfer"][label] = {
                "reference_value": value,
                "fraction_of_pairs_above": round(frac_above, 4),
                "equivalent": round(float(np.quantile(sims, 1 - frac_above)), 4)
                if frac_above > 0
                else None,
            }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--only", nargs="*", help="candidate names to run (default: all present on disk)"
    )
    ap.add_argument(
        "--out", type=Path, default=Path("docs/experiments/embedder-bench-2026-10-28.json")
    )
    args = ap.parse_args()

    datasets = {ds: load_beir(ds) for ds in ("scifact", "nfcorpus")}
    for ds, (corpus, queries, _) in datasets.items():
        print(f"{ds}: {len(corpus)} docs, {len(queries)} test queries", flush=True)
    chunks = palace_chunks()
    print(f"palace L0 chunks: {len(chunks)}", flush=True)

    results = []
    for c in CANDIDATES:
        if args.only and c.name not in args.only:
            continue
        if not c.path.exists():
            print(f"skip {c.name}: {c.path} missing", flush=True)
            continue
        print(f"\n== {c.name}", flush=True)
        try:
            r = run_candidate(c, datasets, chunks)
        except Exception as e:  # a candidate that cannot load is a result, not a crash
            r = {"name": c.name, "error": f"{type(e).__name__}: {e}"}
        results.append(r)
        print(json.dumps({k: v for k, v in r.items() if k != "palace_pairs"}), flush=True)
        _write(args.out, results)  # after every candidate: an interrupted run keeps its data

    sigma_transfer(results, "qwen3-embedding-4b-q4km", {"sigma": 0.58, "near_dup": 0.93})
    _write(args.out, results)
    print(f"\nwrote {args.out}")
    return 0


def _write(out: Path, results: list[dict[str, object]]) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=1))


if __name__ == "__main__":
    raise SystemExit(main())
