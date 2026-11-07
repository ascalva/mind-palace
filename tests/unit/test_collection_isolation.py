"""Collection reads the shipped defaults, as every test does (tests/conftest.py).

pytest imports a test module before any fixture runs, so a constant the module reads from the
configuration at import escapes the per-test isolation unless collection is isolated too. This
module's own constants are such reads, taken at its import: the tests compare them with what
the loader and the configuration say inside a test. Without the session hook, the first test
fails everywhere (at import the loader points at this checkout's ``config/ouroboros.toml``), and
the second fails on any machine whose overlay changes the embedding dimension or the vault path.
"""

from __future__ import annotations

from core.kernel.config import REPO_ROOT, get_config, loader

_OVERLAY_AT_IMPORT = loader._INSTANCE_OVERLAY
_DIM_AT_IMPORT = int(get_config().embedding.dim)
_VAULT_AT_IMPORT = str(get_config().ingestion.vault.path)


def test_collection_reads_no_instance_overlay() -> None:
    assert _OVERLAY_AT_IMPORT != REPO_ROOT / "config" / "ouroboros.toml"
    assert not _OVERLAY_AT_IMPORT.exists()


def test_a_constant_read_at_import_matches_the_configuration_of_the_test() -> None:
    cfg = get_config()
    assert _DIM_AT_IMPORT == int(cfg.embedding.dim)
    assert _VAULT_AT_IMPORT == str(cfg.ingestion.vault.path)
