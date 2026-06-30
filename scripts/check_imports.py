#!/usr/bin/env python3
"""CLI for the static import-graph firewall lint (Invariant 2).

Exits non-zero if any module under core/ imports a networked zone (edge/cloud) or a
networking primitive outside the audited loopback allowlist. Wired into CI; also asserted
in tests/test_import_firewall.py. See ops/import_lint.py for the rules.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root on path

from ops.import_lint import main

if __name__ == "__main__":
    raise SystemExit(main())
