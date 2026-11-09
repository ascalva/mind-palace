"""The study's command line (eval/embedder_use/__init__.py)."""

from __future__ import annotations

import argparse
import sys
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from eval.embedder_use.common import Cache, Collection, Embedder, ServerTokenizer, beir, corpus_w
from eval.embedder_use.common import write as write_json

RETRIEVAL = ("chunks", "context", "prompts", "dims", "late", "carried")


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", file=sys.stderr, flush=True)


def collection(name: str, instance: Path | None) -> Collection:
    if name == "W":
        if instance is None:
            raise SystemExit("W needs --instance (the corpus instance's root, read only)")
        return corpus_w(instance)
    return beir(name)


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m eval.embedder_use", description=__doc__)
    ap.add_argument("experiment",
                    choices=(*RETRIEVAL, "tokens", "corpus-tokens", "corpus-dims", "edges"))
    ap.add_argument("--cache", type=Path, required=True, help="the vector and token cache (dir)")
    ap.add_argument("--instance", type=Path, default=None,
                    help="the corpus instance's root, read only")
    ap.add_argument("--collections", nargs="*", default=None)
    ap.add_argument("--port", type=int, default=8081, help="the embedding server")
    ap.add_argument("--tok-port", type=int, default=8081, help="the server that tokenizes")
    ap.add_argument("--late-port", type=int, default=None,
                    help="a pooling-none server for late chunking (experiment 3)")
    ap.add_argument("--arms", nargs="*", default=None,
                    help="corpus-tokens: only these arms (TA adds stage 1's ASCII tokenizer)")
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args(argv)
    cache = Cache(a.cache / "cache.sqlite")
    emb = Embedder(cache, port=a.port)
    tok = ServerTokenizer(cache, port=a.tok_port)
    out: dict[str, Any] = {"experiment": a.experiment,
                           "started": time.strftime("%Y-%m-%dT%H:%M:%S")}
    if a.experiment in RETRIEVAL:
        from eval.embedder_use import retrieval as r

        default = {"chunks": ["nfcorpus", "W"], "context": ["scifact", "nfcorpus", "W"],
                   "prompts": ["scifact", "nfcorpus", "W"], "dims": ["scifact", "nfcorpus"],
                   "late": ["scifact", "nfcorpus", "W"],
                   "carried": ["scifact", "nfcorpus", "W"]}
        for name in a.collections or default[a.experiment]:
            col = collection(name, a.instance)
            log(f"{a.experiment}: {name}, {len(col.docs)} documents, {len(col.queries)} queries")
            if a.experiment == "chunks":
                out[name] = r.run_chunks(col, emb, tok, log)
            elif a.experiment == "context":
                late_tok = (ServerTokenizer(cache, port=a.late_port)
                            if a.late_port is not None else None)
                out[name] = r.run_context(col, emb, tok, log, late_port=a.late_port,
                                          late_tok=late_tok)
            elif a.experiment == "late":
                if a.late_port is None:
                    raise SystemExit("late needs --late-port (a pooling-none server)")
                out[name] = r.precompute_late(col, ServerTokenizer(cache, port=a.late_port),
                                              a.late_port, log)
            elif a.experiment == "prompts":
                out[name] = r.run_prompts(col, emb, log)
            elif a.experiment == "carried":
                out[name] = r.run_carried(col, emb, log)
            else:
                out[name] = r.run_dims(col, emb, log)
            if a.out is not None:                     # after each collection: a run resumes
                write_json(a.out, out)
    elif a.experiment == "tokens":
        from eval.embedder_use import tokens as tk

        for name in a.collections or ["scifact", "nfcorpus"]:
            out[name] = tk.run_collection(beir(name), log)
            write_json(a.out, out)
    elif a.experiment == "corpus-dims":
        from eval.embedder_use.corpus import run_corpus_dims

        if a.instance is None:
            raise SystemExit("corpus-dims needs --instance")
        out["corpus"] = run_corpus_dims(a.instance, emb, log)
    elif a.experiment == "edges":
        from eval.embedder_use.edges import run_edges

        if a.instance is None:
            raise SystemExit("edges needs --instance")
        out["corpus"] = run_edges(a.instance, log)
    elif a.experiment == "corpus-tokens":
        from eval.embedder_use import tokens as tk

        if a.instance is None:
            raise SystemExit("corpus-tokens needs --instance")
        out["corpus"] = tk.run_corpus(a.instance, log, only=a.arms,
                                      with_counts=not a.arms)
    else:
        raise SystemExit(f"{a.experiment}: not yet wired")
    out["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    write_json(a.out, out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
