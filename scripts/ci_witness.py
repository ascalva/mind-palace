#!/usr/bin/env python
"""Drive the CI witness (ops/ci_witness.py). From the repo root:

    uv run scripts/ci_witness.py check <sha>     # poll the ci run to verdict, attest, rc 0 = green
    uv run scripts/ci_witness.py rotate          # print the by-hand PAT re-mint play (rc 1)

The `release <sha>` verb was retired 2026-07-28 (owner ruling): the release follows the
merge, not the deploy — .github/workflows/release.yml triggers off a green `ci` on main.

Deliberately UNSEALED (ops tier reaches api.github.com; the sealed core never does) — which
is why `palace deploy` invokes this as a subprocess rather than importing it.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ops.ci_witness import check  # noqa: E402


def main(argv: list[str]) -> int:
    if argv and argv[0] == "rotate" and len(argv) == 1:
        from ops.ci_witness import rotate
        return rotate()
    if len(argv) != 2 or argv[0] != "check":
        print(__doc__)
        return 2
    return check(argv[1])


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
