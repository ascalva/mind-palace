"""CLI entry for the harness report generator (dn-evaluation-harness §2.7, bp-044).

The thin I/O boundary around `eval.harness.report`: it opens the configured stores (the eval-results
store E1, the run ledger E2, the telemetry cost ledger), stamps the date (the RENDERER reads no
clock — determinism; the boundary stamps it, §6), builds the ONE report model, and writes
`report.md` + `report.json` into `data/reports/<date>-<topic>/`.

    uv run python -m scripts.report --topic sigma-ab
    uv run python -m scripts.report --topic nightly --date 2026-07-16 --out data/reports

Model-free, read-only over the stores, no network — a local file drop (∉ MIRROR_READABLE).
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime

from eval.harness.report import build_report, write_report


def _default_date() -> str:
    """Today, UTC — stamped at the boundary (never in the renderer, which stays clock-free)."""
    return datetime.now(UTC).date().isoformat()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a harness report (markdown + JSON).")
    parser.add_argument("--topic", required=True, help="report topic (dir slug component)")
    parser.add_argument("--date", default=None,
                        help="ISO date to stamp (default: today UTC). Passed to the renderer.")
    parser.add_argument("--out", default="data/reports", help="report root (default: data/reports)")
    args = parser.parse_args(argv)

    # Lazy store opens — kept out of import so the module stays dependency-light and the isolation
    # scan sees no ingest coupling at import time (the store modules' own precedent).
    from core.stores.runledger import open_run_ledger
    from core.stores.telemetry import open_store
    from eval.harness.store import open_eval_store

    date = args.date or _default_date()
    eval_store = open_eval_store()
    run_ledger = open_run_ledger()
    telemetry_store = open_store()
    try:
        report = build_report(
            args.topic, date,
            eval_store=eval_store, run_ledger=run_ledger, telemetry=telemetry_store.reader(),
        )
        out_dir = write_report(report, root=args.out)
    finally:
        eval_store.close()
        run_ledger.close()
        telemetry_store.close()
    print(out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
