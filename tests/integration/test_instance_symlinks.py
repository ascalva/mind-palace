"""A symlink cannot carry a named instance into Ouroboros's state (DI-2).

`shared()` compares where locations really are, every symlink on them resolved, so an instance
root, an intermediate directory or a declared source linked into Ouroboros's state shows as shared
and the load refuses. Each case below loads under a lexical comparison of the paths; the control
shows that a link to somewhere of the instance's own still loads.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from core.kernel.config import loader


def _repo(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    (repo / "config").mkdir(parents=True)
    (repo / "data").mkdir()
    monkeypatch.setattr(loader, "REPO_ROOT", repo)
    monkeypatch.setattr(loader, "_CONFIG_DIR", repo / "config")
    monkeypatch.setattr(loader, "_INSTANCE_OVERLAY", repo / "config" / "ouroboros.toml")
    monkeypatch.setattr(loader, "_LEGACY_OVERLAY", repo / "config" / "local.toml")
    monkeypatch.setattr(loader, "LEVERS_OVERLAY", repo / "config" / "levers.toml")
    monkeypatch.delenv(loader.OVERLAY_ENV, raising=False)
    return repo


def _named(monkeypatch: pytest.MonkeyPatch, repo: Path, text: str = "") -> loader.Config:
    overlay = repo.parent / "bench.toml"
    overlay.write_text('[instance]\nid = "bench"\n' + text)
    monkeypatch.setenv(loader.OVERLAY_ENV, str(overlay))
    return loader.load_config()


def test_a_root_linked_to_the_repo_root_refuses(monkeypatch, tmp_path) -> None:
    """`instances/bench` → the repo root: its data dir reads as `instances/bench/data` and is
    `<repo>/data`, Ouroboros's."""
    repo = _repo(monkeypatch, tmp_path)
    (repo / "instances").mkdir()
    (repo / "instances" / "bench").symlink_to(repo)
    with pytest.raises(loader.InstanceOverlayError, match="would share"):
        _named(monkeypatch, repo)


@pytest.mark.parametrize("link", ["instances", "instances/bench/data"])
def test_an_intermediate_dir_linked_into_ouroboros_data_refuses(monkeypatch, tmp_path,
                                                                 link) -> None:
    """`instances` itself, or the instance's own `data`, linked into Ouroboros's data dir."""
    repo = _repo(monkeypatch, tmp_path)
    (repo / link).parent.mkdir(parents=True, exist_ok=True)
    (repo / link).symlink_to(repo / "data")
    with pytest.raises(loader.InstanceOverlayError, match="would share"):
        _named(monkeypatch, repo)


def test_a_source_linked_to_ouroboros_vault_refuses(monkeypatch, tmp_path) -> None:
    repo = _repo(monkeypatch, tmp_path)
    vault = tmp_path / "vault"
    vault.mkdir()
    (repo / "config" / "ouroboros.toml").write_text(f'[ingestion.vault]\npath = "{vault}"\n')
    corpus = tmp_path / "corpus"
    corpus.symlink_to(vault)
    with pytest.raises(loader.InstanceOverlayError, match="would share"):
        _named(monkeypatch, repo, f'[ingestion.vault]\npath = "{corpus}"\nenabled = true\n')


def test_control_a_root_linked_to_its_own_place_loads(monkeypatch, tmp_path) -> None:
    repo = _repo(monkeypatch, tmp_path)
    own = tmp_path / "volume"
    own.mkdir()
    (repo / "instances").mkdir()
    (repo / "instances" / "bench").symlink_to(own)
    cfg = _named(monkeypatch, repo)
    assert cfg.paths.data_dir == repo / "instances" / "bench" / "data"
    assert loader.shared(loader.namespaces_of(cfg),
                         loader.namespaces_of(loader._ouroboros())) == []
