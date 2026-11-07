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
   Collection is isolated too (``pytest_configure``), so a constant a test module reads
   from the configuration at import sees the same defaults as the tests that use it.

Per-category markers are NOT applied here — each subdirectory's own ``conftest.py``
applies its marker to the tests collected beneath it (see test-organization.md §3).
The marker *names* are registered in ``pyproject.toml`` so unknown-mark warnings stay
off and ``-m <category>`` selection works.
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest

# Make `import fixtures.<...>` resolve regardless of the test's location. conftest.py is
# imported before collection, so this runs early enough for every test module.
_TESTS_DIR = Path(__file__).resolve().parent
if str(_TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(_TESTS_DIR))


def _absent_overlays(absent: Path) -> dict[str, Path]:
    """The loader's per-machine paths, each pointed under `absent`, a directory holding nothing."""
    return {"_INSTANCE_OVERLAY": absent / "ouroboros.toml",
            "LEVERS_OVERLAY": absent / "levers.toml",
            # Where a named load looks for the other instances declared on the host
            # (instances/*.toml): none, unless a test declares its own.
            "_CONFIG_DIR": absent}


def pytest_configure(config: pytest.Config) -> None:
    """Isolate collection from this machine's overlays, as the fixture below isolates each test.

    pytest imports a test module during collection, before any fixture runs, so a constant the
    module reads from the configuration at import (a vector dimension, a vault path) escapes the
    per-test isolation. On a machine whose overlay changes that value, the constant comes from the
    overlay and the test's configuration from the shipped defaults, and the two disagree; CI, with
    no overlay, never sees it. Pointing the loader at an empty directory here, before collection,
    gives every read in the session the defaults CI reads."""
    from core.kernel.config import loader

    absent = Path(tempfile.mkdtemp(prefix="no-instance-overlay-"))
    config.add_cleanup(lambda: shutil.rmtree(absent, ignore_errors=True))
    for name, path in _absent_overlays(absent).items():
        setattr(loader, name, path)
    os.environ.pop(loader.OVERLAY_ENV, None)                # a shell's instance must not leak in
    loader.get_config.cache_clear()


@pytest.fixture(autouse=True)
def _isolate_from_the_instance_overlay(monkeypatch: pytest.MonkeyPatch,
                                       tmp_path_factory: pytest.TempPathFactory) -> Iterator[None]:
    """An instance flip (e.g. `[runtime] chat_backend` on Ouroboros) must not change what the
    deterministic tier asserts. Before this fixture the suite silently read the machine's overlay,
    so it passed only while that overlay happened not to touch what a test depends on."""
    from core.kernel.config import loader

    absent = tmp_path_factory.getbasetemp() / "no-instance-overlay"
    for name, path in _absent_overlays(absent).items():
        monkeypatch.setattr(loader, name, path)
    monkeypatch.delenv(loader.OVERLAY_ENV, raising=False)   # a shell's instance must not leak in
    loader.get_config.cache_clear()
    yield
    loader.get_config.cache_clear()
