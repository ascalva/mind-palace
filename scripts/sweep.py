#!/usr/bin/env python
"""Run a declarative sweep spec through the deterministic optimizer (E3a-1b, bp-049). From root:

    uv run scripts/sweep.py config/sweeps/dreamer-sigma-ab.toml

Parses the spec, seals the core (Invariant 1), builds the golden-FIXTURE retriever (the `live`-e2e
pattern — reads the fixture, never the vault; the firewall holds), drives the BUILT `ShadowRunner`
once per (grid value × seed) over ONE shared eval store + ONE shared run ledger, builds the curve,
filters by admissibility, selects the widest near-optimal plateau center, and — when `[selfmod]
enabled` — PROPOSES it into the §14 ledger (PROPOSED only; the owner blesses the apply). With
selfmod off (the default), it prints the selection and emits nothing.

This is the run ENTRY; a real overnight sweep against the live mirror is the owner/scheduler's act.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root on path


def _build_fixture_retriever(tmp: Path):
    """Ingest the golden FIXTURE corpus into a throwaway store and return a (query, k) -> rows fn —
    the guardrail retriever (§3 risk (b)). Reads the fixture, never the vault (firewall intact)."""
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
    if len(sys.argv) != 2:
        print("usage: uv run scripts/sweep.py <spec.toml>", file=sys.stderr)
        sys.exit(2)

    from core.sealing import seal

    seal()  # structural egress guard first (Invariant 1)

    from config.loader import get_config
    from core.stores.runledger import RunLedger
    from core.stores.vectorstore import open_vector_store
    from eval.harness.store import open_eval_store
    from eval.harness.sweep import parse_spec, run_sweep
    from ops.selfmod import build_golden_validator, build_loop

    spec = parse_spec(Path(sys.argv[1]))
    cfg = get_config()

    with tempfile.TemporaryDirectory() as td:
        retriever = _build_fixture_retriever(Path(td))
        eval_store = open_eval_store(cfg)
        ledger = RunLedger(cfg.paths.derived_store.parent / "dream_runs.sqlite")
        # The §14 loop is built ONLY when selfmod is enabled — otherwise the sweep records the
        # selection and emits nothing (never forcing the fail-closed switch, §11).
        loop = None
        if cfg.selfmod.enabled:
            loop = build_loop(build_golden_validator(retriever), config=cfg)

        result = run_sweep(
            spec,
            base_config=cfg,
            eval_store=eval_store,
            ledger=ledger,
            store=open_vector_store(cfg),
            retriever=retriever,
            selfmod_loop=loop,
        )

    print(f"sweep {result.spec_name}: lever={result.lever} objective={spec.objective} "
          f"pipeline={result.select_pipeline}")
    print(f"  grid={list(result.grid)}")
    for p in result.curve:
        flag = "" if p.admissible else "  [INADMISSIBLE]"
        print(f"    σ={p.value}  ȳ={p.mean:.4f}  ±{p.halfwidth:.4f}  n={p.n_seeds}{flag}")
    print(f"  current={result.current}  ε={result.epsilon:.4f}  selected={result.selected}")
    for note in result.notes:
        print(f"  - {note}")
    if result.proposal_emitted:
        print(f"  PROPOSED #{result.proposal_id} — owner blesses the apply (never auto-approved).")


if __name__ == "__main__":
    main()
