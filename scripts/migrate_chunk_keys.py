#!/usr/bin/env python
"""Re-key the derived vector index to doc-scoped content ids (ingest-identity §4; build plan 1c).

    uv run scripts/migrate_chunk_keys.py            # DRY RUN (report only)
    uv run scripts/migrate_chunk_keys.py --apply    # re-key rows in place

The row-id scheme changed from `{note_digest}:{chunk_index}` to `{source_path}:{chunk_hash}` —
stable across a note's versions (unchanged chunk keeps its point), distinct across documents (§7).
This migration RE-KEYS the existing rows in place: it recomputes each row's id from its
`(source_path, text)` and rewrites the table with the SAME vectors — no re-embedding, no Ollama, and
the raw store and catalog are untouched. Identical chunks in a source coalesce to one point (§3).
Idempotent: a row already under the new key re-keys to itself, so re-running is a no-op.

Why re-key rather than reset + re-ingest: `rescan()` is change-detected against the catalog, so a
reset-vectors + `rescan()` would see every note UNCHANGED (catalog digest == current digest) and
rebuild **nothing** — silently emptying the index. Re-keying reads the derived rows directly, which
is correct, embedding-free, and can't be defeated that way. (Derived is regenerable from raw either
way, §8 — the raw store is the source of truth and is never touched here.)
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root on path


def main(argv: list[str]) -> int:
    apply = "--apply" in argv

    from config.loader import get_config
    from core.ingest.index import rekey_preview, rekey_store
    from core.stores.vectorstore import open_vector_store

    store = open_vector_store(get_config())
    total, changing = rekey_preview(store)
    print(f"vector rows: {total}; ids to re-key: {changing}")
    if not apply:
        print("DRY RUN — nothing changed. Re-run with --apply to re-key rows in place "
              "(same vectors, no re-embed; raw + catalog untouched).")
        return 0

    read, points = rekey_store(store)
    print(f"APPLIED — re-keyed {read} rows to {points} doc-scoped points "
          f"({read - points} duplicate chunks coalesced). Vectors unchanged; raw untouched.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
