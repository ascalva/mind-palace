#!/usr/bin/env python
"""Owner CLI: declare that one vault note supersedes another (ops/supersede.py). From root:

    uv run scripts/supersede.py <old-note> <new-note> [note text...]

Refs are full source_paths or unique filename suffixes (e.g. note-2026-07-11-000843.md).
For the phone flow: the shortcut writes a NEW file per capture, so a correction is a new
document — after it syncs and ingests (~5s while the daemon runs), declare the thread:

    mind-palace supersede note-2026-07-11-000928.md note-2026-07-12-091500.md

Owner-operated only — the store refuses machine callers at its own boundary.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.sealing import seal


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    seal()  # local stores only; nothing here needs any network
    from config.loader import get_config
    from core.stores.authored_supersession import open_authored_supersession_store
    from core.stores.catalog import VaultCatalog
    from ops.supersede import AmbiguousRef, declare

    cfg = get_config()
    try:
        declare(VaultCatalog(cfg.paths.vault_catalog), open_authored_supersession_store(cfg),
                argv[0], argv[1], note=" ".join(argv[2:]))
    except AmbiguousRef as e:
        print(f"refused: {e}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
