#!/usr/bin/env python
"""Run the frozen golden set against the real embedder (BUILD-SPEC §15). From repo root:

    uv run scripts/eval.py            # print the report vs the baseline
    uv run scripts/eval.py --bless     # re-bless baseline.json (owner-only)

Seals the core (Invariant 1) first, then ingests the golden fixture corpus into a throwaway
store and scores the blessed queries. `--bless` rewrites `baseline.json` — this MOVES the
frozen anchor, so it is a deliberate, owner-only act (Invariant 9), not something an agent does.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root on path

from core.sealing import seal


def _build_retriever(tmp: Path):
    """Ingest the fixture corpus into a temp store and return a (query, k) -> rows fn."""
    from config.loader import get_config
    from core.ingest.embed import build_embedder
    from core.ingest.index import index_records, semantic_search
    from core.ingest.pipeline import ingest_vault
    from core.stores.rawstore import RawStore
    from core.stores.vectorstore import VectorStore
    from eval.golden import CORPUS_DIR

    cfg = get_config()
    raw = RawStore(tmp / "raw")
    store = VectorStore(tmp / "v.lance", dim=cfg.embedding.dim)
    embedder = build_embedder(cfg)
    index_records(ingest_vault(CORPUS_DIR, raw), embedder, store)

    def retrieve(query: str, k: int):
        return semantic_search(query, embedder, store, k=k)

    return retrieve


def main() -> None:
    seal()  # structural egress guard first (Invariant 1)
    from eval.golden import (
        BASELINE_PATH,
        evaluate,
        load_baseline,
        load_golden_set,
        regressions,
    )

    bless = "--bless" in sys.argv[1:]
    with tempfile.TemporaryDirectory() as td:
        report = evaluate(load_golden_set(), _build_retriever(Path(td)))

    for r in report.per_query:
        print(f"  {r.id:12s} recall@k={r.recall_at_k:.3f} overlap={r.overlap:.3f} "
              f"dist={r.mean_distance:.3f}  -> {list(r.retrieved)}")
    metrics = report.as_metrics()
    print(f"\naggregate: {metrics}")

    if bless:
        metrics["distance_tol"] = 0.05  # how far mean_distance may rise before it regresses
        BASELINE_PATH.write_text(json.dumps({"metrics": metrics}, indent=2) + "\n",
                                 encoding="utf-8")
        print(f"\nblessed -> {BASELINE_PATH}")
    else:
        reg = regressions(report, load_baseline())
        print("\nregressions vs baseline:", reg or "none")
        sys.exit(1 if reg else 0)


if __name__ == "__main__":
    main()
