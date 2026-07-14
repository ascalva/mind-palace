#!/usr/bin/env python
"""Owner-gated id-mint migration (bp-034; oq-0019 B). Run from the repo root, DAEMON DOWN:

    uv run scripts/mint_ids.py --dry-run     # the auditable plan; mutates nothing (do this FIRST)
    uv run scripts/mint_ids.py --confirm     # the real, reversible run (backs up vault + stores)

Mints a durable Logseq `id::` into every vault note lacking a stable id and re-keys that note's
version history from its `source_path` to the minted id, so no lineage forks at the identity switch
(the A6 payoff). Mirrors `scripts/purge_raw.py`: deliberate, offline, fail-closed. It REFUSES unless
`--confirm` is passed AND no live daemon is running (a live watcher would race the re-key —
finding-0066). A vault + version/catalog backup is written before any mutation; `run()` reverses
from it. Default (no flag) is the dry-run.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root on path

from core.sealing import seal


def main(argv: list[str]) -> int:
    seal()  # structural egress guard first (Invariant 1)
    from config.loader import get_config
    from core.ingest.mint_ids import MintRefusedError, preview, run
    from core.ingest.sync import build_vault_sync
    from core.stores.authored_supersession import owner_declaration
    from ops.lifecycle.runs import open_run_ledger

    cfg = get_config()
    sync = build_vault_sync(cfg)

    if "--confirm" not in argv:                          # dry-run is the default (fail-safe)
        plan = preview(sync)
        print(f"mint set ({len(plan.mint_set)} notes lacking a stable id):")
        for sp in plan.mint_set:
            print(f"  MINT  {sp}")
        print(f"re-key plan ({len(plan.rekey)} chains → durable id::):")
        for np in plan.rekey:
            tgt = np.target_id or "<to-be-minted>"
            print(f"  {np.action:11s} {np.source_path}  [{np.current_doc_id}] → {tgt}")
        print(f"skipped (already identified + filed): {len(plan.skipped)}")
        print("\nthis was a DRY RUN — nothing was written. Re-run with --confirm to migrate.")
        return 0

    backup_dir = cfg.paths.data_dir / "mint_ids_backup"
    try:
        report = run(
            sync,
            declaration=owner_declaration(),             # owner authority (owner-operated entry)
            confirm=True,
            backup_dir=backup_dir,
            run_ledger=open_run_ledger(cfg),             # daemon-down gate
        )
    except MintRefusedError as e:
        print(f"REFUSED: {e}")
        return 1
    print(f"migrated: {report}")
    if not report.verified:
        print("WARNING: post-migration verification FAILED (a lineage forked) — restore from "
              f"{report.backup_dir} and investigate before bringing the daemon up.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
