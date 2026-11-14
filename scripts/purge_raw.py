#!/usr/bin/env python
"""Owner-gated TRUE deletion of a note's raw bytes (vault-sync task). Run from the repo root:

    uv run scripts/purge_raw.py <digest> --confirm

A vault delete only TOMBSTONES (derived dropped, raw kept). This removes the raw blob too —
deliberate, irreversible, and refused unless `--confirm` is passed AND the digest is held by
no active note (tombstone it from the vault first). Lists tombstoned digests with `--list`. The
shared cache (`~/.mind-palace/cache`) loses the object and its chunks' vectors as well, and records
the digest so no instance puts it back (dn-instance-lifecycle §6.6). Refused while a reset of the
instance is pending (`data/reset.pending`), as every writer is.
"""

from __future__ import annotations

import sys
from pathlib import Path

from core.stores.vectorstore import open_vector_store

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root on path

from core.sealing import seal


def main(argv: list[str]) -> int:
    seal()  # structural egress guard first (Invariant 1)
    from config.loader import get_config
    from core.ingest.purge import PurgeRefusedError, purge_raw
    from core.kernel.stores.rawstore import RawStore
    from core.stores.cache import Cache, cache_home
    from core.stores.catalog import VaultCatalog

    cfg = get_config()
    listing = "--list" in argv or not argv
    if not listing:
        # a purge beside a pending reset could erase a version the reset's marker names
        from ops.lifecycle.inventory import refusal

        pending = refusal(cfg, "a purge")
        if pending is not None:
            print(pending)
            return 1
    catalog = VaultCatalog(cfg.paths.vault_catalog)

    if listing:
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
            store=open_vector_store(cfg),
            catalog=catalog,
            confirm=confirm,
            cache=Cache(cache_home()),
        )
    except PurgeRefusedError as e:
        print(f"REFUSED: {e}")
        return 1
    print(f"purged {result.digest}: raw_removed={result.raw_removed} "
          f"paths={list(result.paths_removed)} cache: raw_removed={result.cache_raw_removed} "
          f"vectors_removed={result.cache_vectors_removed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
