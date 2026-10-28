"""Root test config.

Three jobs:

1. Put the ``tests/`` directory on ``sys.path`` so the shared ``fixtures`` package
   (synthetic corpora, ephemeral stores, attestation helpers) is importable as a
   top-level module from any test, regardless of which category subdirectory the
   test lives in.
2. House cross-cutting fixtures that every category may need.
3. Isolate every test from THIS machine's overlays (``config/ouroboros.toml``,
   ``config/levers.toml``), so the suite tests the shipped defaults exactly as CI does
   (CI has no overlay). A test that needs an overlay patches the two paths itself.

Per-category markers are NOT applied here — each subdirectory's own ``conftest.py``
applies its marker to the tests collected beneath it (see test-organization.md §3).
The marker *names* are registered in ``pyproject.toml`` so unknown-mark warnings stay
off and ``-m <category>`` selection works.
"""

from __future__ import annotations

import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

# Make `import fixtures.<...>` resolve regardless of the test's location. conftest.py is
# imported before collection, so this runs early enough for every test module.
_TESTS_DIR = Path(__file__).resolve().parent
if str(_TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(_TESTS_DIR))


@pytest.fixture(autouse=True)
def _isolate_from_the_instance_overlay(monkeypatch: pytest.MonkeyPatch,
                                       tmp_path_factory: pytest.TempPathFactory) -> Iterator[None]:
    """An instance flip (e.g. `[runtime] chat_backend` on Ouroboros) must not change what the
    deterministic tier asserts. Before this fixture the suite silently read the machine's overlay,
    so it passed only while that overlay happened not to touch what a test depends on."""
    from core.kernel.config import loader

    absent = tmp_path_factory.getbasetemp() / "no-instance-overlay"
    monkeypatch.setattr(loader, "_INSTANCE_OVERLAY", absent / "ouroboros.toml")
    monkeypatch.setattr(loader, "LEVERS_OVERLAY", absent / "levers.toml")
    loader.get_config.cache_clear()
    yield
    loader.get_config.cache_clear()
