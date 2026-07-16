#!/usr/bin/env python
"""Score claim persistence across a COMPLETED σ-sweep night (FB-1, bp-050). From root:

    uv run scripts/fibers.py config/sweeps/dreamer-sigma-ab.toml

The RETENTION consumer dual to `scripts/sweep.py`'s selection. It does NOT drive a sweep (a live
run is the owner/scheduler's act, a non-goal here) — it reads the run ledger + eval store the sweep
already wrote, reconstructs the cell→σ join from the spec's declared grid + the base config
(model-free, §2.4.1), computes per-claim `(pers, hull, gap)`, writes the five `sigma_persistence.*`
aggregate readings into the eval store (keyed per §6, deduped by the store), and renders a report
section under `data/reports/`.

Reads the SAME run ledger `scripts/sweep.py` wrote (`<derived_store>/../dream_runs.sqlite`) and the
configured eval store. Seals the core first (Invariant 1). Optional `--date YYYY-MM-DD` stamps the
report (the renderer reads no clock — determinism); default is today.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root on path


def _parse_args(argv: list[str]) -> tuple[Path, str]:
    """`<spec.toml> [--date YYYY-MM-DD]` → (spec path, date). Fail-closed on a bad shape."""
    if len(argv) not in (2, 4) or (len(argv) == 4 and argv[2] != "--date"):
        print("usage: uv run scripts/fibers.py <spec.toml> [--date YYYY-MM-DD]", file=sys.stderr)
        raise SystemExit(2)
    spec_path = Path(argv[1])
    date = argv[3] if len(argv) == 4 else datetime.now(UTC).date().isoformat()
    return spec_path, date


def main() -> None:
    spec_path, date = _parse_args(sys.argv)

    from core.sealing import seal

    seal()  # structural egress guard first (Invariant 1)

    from config.loader import get_config
    from core.stores.runledger import RunLedger
    from eval.harness.fibers import run_fibers, write_report
    from eval.harness.store import open_eval_store
    from eval.harness.sweep import parse_spec

    spec = parse_spec(spec_path)
    cfg = get_config()

    # The SAME ledger scripts/sweep.py wrote (the completed sweep night's cells).
    ledger = RunLedger(cfg.paths.derived_store.parent / "dream_runs.sqlite")
    eval_store = open_eval_store(cfg)

    result = run_fibers(
        ledger=ledger,
        eval_store=eval_store,
        base_config=cfg,
        lever=spec.lever,
        grid=tuple(float(v) for v in spec.grid()),
    )

    print(f"fibers {spec.name}: lever={spec.lever.name} corpus_ref={result.corpus_ref}")
    reg = result.evidence.lever_registry_hash[:12]
    print(f"  grid m={len(result.evidence.grid)}  registry={reg}…")
    for pipeline in sorted(result.fibers):
        claim_fibers = result.fibers[pipeline]
        agg = result.aggregates.get(pipeline, {})
        summary = ", ".join(f"{name.split('.')[-1]}={value:.4f}" for name, value in agg.items())
        print(f"  [{pipeline}] {len(claim_fibers)} claim(s)  {summary or '(no claims)'}")
    print(f"  eval-store rows written: {result.readings_written}")
    for note in result.notes:
        print(f"  - {note}")

    out_dir = write_report(result, date=date, topic=f"{spec.name}-fibers")
    print(f"  report: {out_dir / 'fibers.md'}")


if __name__ == "__main__":
    main()
