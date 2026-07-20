#!/usr/bin/env python
"""The exhaust report writer — PLACES a self-contained HTML build report into the owner's
outbound exhaust lane (dn-exhaust-lane §2.4).

    uv run scripts/exhaust_report.py <html-file> --plan bp-NNN --slug <slug>
      -> writes <exhaust>/reports/YYYY-MM-DD-bp-NNN-<slug>.html   (date = today)

Placement ONLY. It copies an already-composed report file to its dated name under the
config-pinned exhaust root (`get_config().exhaust.path` — single source of truth), creating
`reports/` as needed. It NEVER composes or rewrites report content — the orchestrator composes
that (single-writer judgment, memory `phone-build-report`); this script only places the file.

It REFUSES a silent overwrite: if the dated target already exists the writer exits 1 and prints
guidance; pass `--force` to replace it deliberately. On success it prints the destination path.

Repo-workflow tooling (dn-exhaust-lane §2.4, the docket.py precedent): stdlib + `config` only,
and it NEVER imports `core` — asserted structurally by the AST test in
`tests/unit/test_exhaust_report.py`. Reading the root through the `config` facade keeps the writer
and the ingest-invariant test pinned to the same source of truth, so they cannot drift.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from datetime import date
from pathlib import Path

from config.loader import get_config


def report_name(plan: str, slug: str, on: date) -> str:
    """The date-sortable, self-describing report filename (note §2.3):
    `YYYY-MM-DD-<bp-id>-<slug>.html`."""
    return f"{on.isoformat()}-{plan}-{slug}.html"


def place_report(
    source: Path,
    plan: str,
    slug: str,
    *,
    force: bool = False,
    on: date | None = None,
) -> Path:
    """Copy `source` to `<exhaust>/reports/<date>-<plan>-<slug>.html` and return the destination.

    Reads the exhaust root from `get_config().exhaust.path` (single source of truth). Creates the
    `reports/` directory as needed. Raises `FileNotFoundError` if the source is missing, and
    `FileExistsError` if the dated target already exists unless `force` is set.
    """
    if not source.is_file():
        raise FileNotFoundError(f"report source not found: {source}")
    reports_dir = get_config().exhaust.path / "reports"
    dest = reports_dir / report_name(plan, slug, on or date.today())
    reports_dir.mkdir(parents=True, exist_ok=True)
    if dest.exists() and not force:
        raise FileExistsError(dest)
    shutil.copyfile(source, dest)
    return dest


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(
        prog="exhaust_report.py",
        description="Place an HTML build report into the exhaust lane's reports/ dir.",
    )
    ap.add_argument("html_file", type=Path, help="the composed report HTML to place")
    ap.add_argument("--plan", required=True, help="the build-plan id, e.g. bp-075")
    ap.add_argument("--slug", required=True, help="a short dash-slug for the filename")
    ap.add_argument(
        "--force", action="store_true", help="replace an existing report at the dated name"
    )
    args = ap.parse_args(argv)
    try:
        dest = place_report(args.html_file, args.plan, args.slug, force=args.force)
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    except FileExistsError as e:
        print(
            f"error: refusing to overwrite an existing report: {e}\n"
            f"       pass --force to replace it.",
            file=sys.stderr,
        )
        return 1
    print(dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
