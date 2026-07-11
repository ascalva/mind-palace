#!/usr/bin/env python
"""Owner-gated TRUE deletion of a note's raw bytes (vault-sync task). Run from the repo root:

    uv run scripts/purge_raw.py <digest> --confirm

A vault delete only TOMBSTONES (derived dropped, raw kept). This removes the raw blob too —
deliberate, irreversible, and refused unless `--confirm` is passed AND the digest is held by
no active note (tombstone it from the vault first). Lists tombstoned digests with `--list`.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root on path

from core.sealing import seal


def main(argv: list[str]) -> int:
    seal()  # structural egress guard first (Invariant 1)
    from config.loader import get_config
    from core.ingest.purge import PurgeRefusedError, purge_raw
    from core.stores.catalog import VaultCatalog
    from core.stores.rawstore import RawStore
    from core.stores.vectorstore import VectorStore

    cfg = get_config()
    catalog = VaultCatalog(cfg.paths.vault_catalog)

    if "--list" in argv or not argv:
        tombstoned: dict[str, list[str]] = {}
        for entry in catalog._conn.execute(  # noqa: SLF001 (admin script, read-only)
            "SELECT source_path, digest FROM vault_files WHERE active = 0 ORDER BY digest"
        ).fetchall():
            tombstoned.setdefault(entry["digest"], []).append(entry["source_path"])
        if not tombstoned:
            print("no tombstoned notes to purge")
            return 0
        print("tombstoned (purgeable) digests:")
        for digest, paths in tombstoned.items():
            print(f"  {digest}  {paths}")
        return 0

    digest = argv[0]
    confirm = "--confirm" in argv
    try:
        result = purge_raw(
            digest,
            raw=RawStore(cfg.paths.raw_store),
            store=VectorStore(cfg.paths.vector_store, dim=cfg.embedding.dim),
            catalog=catalog,
            confirm=confirm,
        )
    except PurgeRefusedError as e:
        print(f"REFUSED: {e}")
        return 1
    print(f"purged {result.digest}: raw_removed={result.raw_removed} "
          f"paths={list(result.paths_removed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
