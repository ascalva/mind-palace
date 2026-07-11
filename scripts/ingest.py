#!/usr/bin/env python
"""(Re)build the knowledge base from the configured vault. Run from the repo root:

    uv run scripts/ingest.py

Seals the core (Invariant 1) before doing any work, then ingests the configured Logseq/
markdown vault into the raw store + LanceDB vectors. Vectors rebuild from raw each run.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root on path

from core.sealing import seal


def main() -> None:
    seal()  # structural egress guard first (Invariant 1)
    from core.ingest.run import run_ingest

    summary = run_ingest()
    print(summary)


if __name__ == "__main__":
    main()
