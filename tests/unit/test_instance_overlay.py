"""Instance selection at run time (DI-2, #25): `MIND_PALACE_OVERLAY` names the one overlay a named
instance reads.

A named instance is a different individual, so nothing of Ouroboros's chain may reach it: not the
hand overlay, not the knobs its self-modification loop tuned. A name that resolves to no file
refuses, as the legacy-overlay guard does, because falling back to the committed defaults would
bring the instance up on the wrong embedder silently. Every case runs in a temporary config
directory; the owner's overlay is never read.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from core.kernel.config import loader

BENCH = loader.REPO_ROOT / "config" / "instances" / "bench.toml"


def _isolated(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(loader, "_CONFIG_DIR", tmp_path)
    monkeypatch.setattr(loader, "_INSTANCE_OVERLAY", tmp_path / "ouroboros.toml")
    monkeypatch.setattr(loader, "_LEGACY_OVERLAY", tmp_path / "local.toml")
    monkeypatch.setattr(loader, "LEVERS_OVERLAY", tmp_path / "levers.toml")


def test_a_named_overlay_replaces_the_whole_chain(monkeypatch, tmp_path: Path) -> None:
    """Ouroboros's overlay and levers set σ and the near-dup threshold; the named overlay sets only
    σ. The instance gets its own σ and the committed near-dup default: neither Ouroboros file
    reached it."""
    _isolated(monkeypatch, tmp_path)
    default = loader.load_config().dreaming.near_dup_threshold
    (tmp_path / "ouroboros.toml").write_text(
        "[dreaming]\nsimilarity_threshold = 0.5\nnear_dup_threshold = 0.5\n")
    (tmp_path / "levers.toml").write_text("[dreaming]\nnear_dup_threshold = 0.6\n")
    named = tmp_path / "other.toml"
    named.write_text('[instance]\nid = "other"\n[dreaming]\nsimilarity_threshold = 0.7\n')

    assert loader.load_config().dreaming.similarity_threshold == 0.5   # control: the chain reads
    monkeypatch.setenv(loader.OVERLAY_ENV, str(named))
    d = loader.load_config().dreaming
    assert d.similarity_threshold == 0.7
    assert d.near_dup_threshold == default


def test_a_name_that_is_no_file_refuses(monkeypatch, tmp_path: Path) -> None:
    _isolated(monkeypatch, tmp_path)
    monkeypatch.setenv(loader.OVERLAY_ENV, str(tmp_path / "missing.toml"))
    with pytest.raises(loader.InstanceOverlayError) as e:
        loader.load_config()
    assert loader.OVERLAY_ENV in str(e.value) and "missing.toml" in str(e.value)


def test_an_empty_name_is_the_default_chain(monkeypatch, tmp_path: Path) -> None:
    _isolated(monkeypatch, tmp_path)
    (tmp_path / "ouroboros.toml").write_text("[dreaming]\nsimilarity_threshold = 0.5\n")
    monkeypatch.setenv(loader.OVERLAY_ENV, "")
    assert loader.load_config().dreaming.similarity_threshold == 0.5


def test_a_relative_name_resolves_against_the_repo_root(monkeypatch, tmp_path: Path) -> None:
    _isolated(monkeypatch, tmp_path)
    monkeypatch.setattr(loader, "REPO_ROOT", tmp_path)
    (tmp_path / "inst").mkdir()
    (tmp_path / "inst" / "x.toml").write_text(
        '[instance]\nid = "x"\n[dreaming]\nsimilarity_threshold = 0.66\n')
    monkeypatch.setenv(loader.OVERLAY_ENV, "inst/x.toml")
    assert loader.load_config().dreaming.similarity_threshold == 0.66


def test_the_legacy_guard_is_ouroboros_only(monkeypatch, tmp_path: Path) -> None:
    """The guard refuses over Ouroboros's un-migrated `local.toml`; a named instance does not read
    Ouroboros's files at all, so the same `local.toml` does not stop it."""
    _isolated(monkeypatch, tmp_path)
    (tmp_path / "local.toml").write_text("[dreaming]\nsimilarity_threshold = 0.58\n")
    with pytest.raises(loader.ConfigMigrationError):
        loader.load_config()
    named = tmp_path / "other.toml"
    named.write_text('[instance]\nid = "other"\n')
    monkeypatch.setenv(loader.OVERLAY_ENV, str(named))
    assert loader.load_config().dreaming.similarity_threshold != 0.58


def test_the_bench_instance_has_nothing_to_back_up_sign_fetch_or_tune(monkeypatch,
                                                                       tmp_path: Path) -> None:
    """The committed bench overlay: Ouroboros's embedder on loopback port 8081, and every surface
    that could reach outside the run turned off."""
    _isolated(monkeypatch, tmp_path)
    monkeypatch.setenv(loader.OVERLAY_ENV, str(BENCH))
    c = loader.load_config()
    assert c.instance.id == "bench" and c.instance.named
    assert c.runtime.embedding_backend == "llamacpp"
    assert c.runtime.port_for("embedding") == 8081
    assert (c.embedding.model, c.embedding.dim) == ("embeddinggemma-2", 768)
    assert not any([c.backup.enabled, c.secrets.enabled, c.attestation.enabled,
                    c.selfmod.enabled, c.selfmod.unattended_enabled, c.effectors.enabled])
    assert not any([c.ingestion.vault.enabled, c.ingestion.transcripts.enabled,
                    c.ingestion.code.enabled, c.integrate.enabled, c.dreaming.scheduled])
