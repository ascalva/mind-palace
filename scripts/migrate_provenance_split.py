#!/usr/bin/env python
"""Relabel legacy `authored` rows to `authored-solo` (the §1 provenance-spectrum split).

    uv run scripts/migrate_provenance_split.py            # DRY RUN (counts only)
    uv run scripts/migrate_provenance_split.py --apply    # mutate the live stores

Track B split `Provenance.AUTHORED` ("authored") into `AUTHORED_SOLO` ("authored-solo") +
`AUTHORED_DIALOGUE`. Rows written before the split carry the literal string `"authored"`,
which is no longer a member of `MIRROR_READABLE`. This relabels them to `"authored-solo"`.

It is SAFE: a same-trust-tier relabel (both values are mirror-readable), not a promotion
across the §8 firewall, so no gate is involved. It is IDEMPOTENT: a second run finds no
`authored` rows and changes nothing. Dry-run is the default; `--apply` is required to write.

BUILD/OWNER BOUNDARY: dry-run + the unit-test fixtures are the builder's job (done). Running
`--apply` against the owner's live `~/.mind-palace` data is a production-data mutation — the
owner runs it, after the nightly restic snapshot is the safety net (runbook → "Provenance
spectrum split migration").
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root on path

from core.sealing import seal

OLD = "authored"
NEW = "authored-solo"


def main(argv: list[str]) -> int:
    seal()  # structural egress guard first (Invariant 1) — this touches local stores only
    from config.loader import get_config
    from core.stores.catalog import VaultCatalog
    from core.stores.vectorstore import VectorStore

    apply = "--apply" in argv
    cfg = get_config()
    store = VectorStore(cfg.paths.vector_store, dim=cfg.embedding.dim)
    catalog = VaultCatalog(cfg.paths.vault_catalog)

    # Dry-run counts: how many rows still carry the legacy tag.
    vec_legacy = sum(1 for r in store.all_rows() if r.get("provenance") == OLD)
    cat_legacy = catalog._conn.execute(  # noqa: SLF001 (admin script, read-only count)
        "SELECT count(*) FROM vault_files WHERE provenance = ?", [OLD]
    ).fetchone()[0]

    print(f"legacy '{OLD}' rows — vectors: {vec_legacy}, catalog: {cat_legacy}")
    if not apply:
        print("DRY RUN — nothing changed. Re-run with --apply to relabel to "
              f"'{NEW}'. (Idempotent; back up first — see the runbook.)")
        return 0

    relabeled_vec = store.relabel_provenance(OLD, NEW)
    relabeled_cat = catalog.relabel_provenance(OLD, NEW)
    catalog.close()
    print(f"APPLIED — relabeled '{OLD}' → '{NEW}'. vectors: {relabeled_vec}, "
          f"catalog: {relabeled_cat}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
