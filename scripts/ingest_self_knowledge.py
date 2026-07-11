#!/usr/bin/env python
"""Ingest the system's own docs as the `curated` self-knowledge graph (Track B / B4). From repo:

    uv run scripts/ingest_self_knowledge.py

So the Ambassador can answer "how do you work?" / "is my data safe?" from the actual white
papers + design notes + Constitution/Conventions — its OWN graph, `curated`, kept OUT of the
authored mirror (the firewall: curated ∉ MIRROR_READABLE). Needs Ollama (real embeddings).

Only prose docs are ingested (no config, no secrets — there are none in the .md tree). Idempotent:
re-run after editing a doc and it re-embeds cleanly.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root on path

from core.sealing import seal


def main() -> int:
    seal()  # structural egress guard first (Invariant 1) — local stores + local Ollama only
    from core.ingest.curated import build_and_ingest_curated

    report = build_and_ingest_curated()
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
