#!/usr/bin/env python
"""Drive the CI witness (ops/ci_witness.py). From the repo root:

    uv run scripts/ci_witness.py check <sha>     # poll the ci run to verdict, attest, rc 0 = green
    uv run scripts/ci_witness.py release <sha>   # dispatch release.yml (token) or print URL
    uv run scripts/ci_witness.py rotate          # print the by-hand PAT re-mint play (rc 1)

Deliberately UNSEALED (ops tier reaches api.github.com; the sealed core never does) — which
is why `palace deploy` invokes this as a subprocess rather than importing it.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ops.ci_witness import check, release  # noqa: E402


def main(argv: list[str]) -> int:
    if argv and argv[0] == "rotate" and len(argv) == 1:
        from ops.ci_witness import rotate
        return rotate()
    if len(argv) != 2 or argv[0] not in ("check", "release"):
        print(__doc__)
        return 2
    return check(argv[1]) if argv[0] == "check" else release(argv[1])


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
