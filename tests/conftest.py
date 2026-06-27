"""Root test config.

Two jobs:

1. Put the ``tests/`` directory on ``sys.path`` so the shared ``fixtures`` package
   (synthetic corpora, ephemeral stores, attestation helpers) is importable as a
   top-level module from any test, regardless of which category subdirectory the
   test lives in.
2. House cross-cutting fixtures that every category may need.

Per-category markers are NOT applied here — each subdirectory's own ``conftest.py``
applies its marker to the tests collected beneath it (see test-organization.md §3).
The marker *names* are registered in ``pyproject.toml`` so unknown-mark warnings stay
off and ``-m <category>`` selection works.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make `import fixtures.<...>` resolve regardless of the test's location. conftest.py is
# imported before collection, so this runs early enough for every test module.
_TESTS_DIR = Path(__file__).resolve().parent
if str(_TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(_TESTS_DIR))
