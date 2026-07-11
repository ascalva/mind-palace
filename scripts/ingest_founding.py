#!/usr/bin/env python
"""Ingest a founding-corpus manifest — the owner's dated, supersession-linked musings (Item 3).

    uv run scripts/ingest_founding.py <manifest.json>

The manifest is a JSON array; each item is
`{"source_path", "title", "body", "date", "supersedes"?}`. `date` is the musing's RECONSTRUCTED
original date (required — undated is refused); `supersedes` is an earlier item's `source_path` this
one revises (optional). Ingested through the steady-state path as AUTHORED_SOLO — the initial
condition. Needs the live embedder (Ollama).

This is CURATION, not training (founding-corpus.md §1): the weights never move. The founding set is
deliberately biased-coherent and MUST NOT be reused as the Track-L control corpus (§2.3).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root on path


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(__doc__)
        return 2
    from core.ingest.founding import FoundingItem, build_and_ingest_founding

    data = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    items = [
        FoundingItem(source_path=d["source_path"], title=d["title"], body=d["body"],
                     date=d["date"], supersedes=d.get("supersedes"))
        for d in data
    ]
    print(build_and_ingest_founding(items))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
