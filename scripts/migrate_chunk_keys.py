#!/usr/bin/env python
"""Re-key the derived vector index to doc-scoped content ids (ingest-identity §4; build plan 1c).

    uv run scripts/migrate_chunk_keys.py            # DRY RUN (report only)
    uv run scripts/migrate_chunk_keys.py --apply    # re-key rows in place

The row-id scheme changed from `{note_digest}:{chunk_index}` to `{source_path}:{chunk_hash}` —
stable across a note's versions (unchanged chunk keeps its point), distinct across documents (§7).
This migration RE-KEYS the note rows in place: it recomputes each row's id from its
`(source_path, text)` and writes that id and nothing else, so no vector moves, nothing is
re-embedded, and the raw store and catalog are untouched. It is scoped to the note lane (PLN-6):
the plane's occupancies take their key in one transaction, a table that predates the plane re-keys
its note records, and no code row, atom, supersession edge or cache entry is read or written
(issue #37: the old reset and re-add deleted every code atom and every superseded version).
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
    from ops.lifecycle.inventory import refusal

    cfg = get_config()
    pending = refusal(cfg, "the re-key") if apply else None    # a pending reset refuses writers
    if pending is not None:
        print(pending)
        return 1
    store = open_vector_store(cfg)
    total, changing = rekey_preview(store)
    print(f"note rows: {total}; ids to re-key: {changing}")
    if not apply:
        print("DRY RUN: nothing changed. Re-run with --apply to re-key note rows in place "
              "(ids only; no vector, atom, edge or code row moves; raw and catalog untouched).")
        return 0

    read, changed = rekey_store(store)
    print(f"APPLIED: re-keyed {changed} of {read} note rows to doc-scoped ids, in place.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
