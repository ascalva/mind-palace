"""A named instance shares nothing with any instance declared on its host, not only Ouroboros.

The loader checks the instance it loads against Ouroboros and against every other overlay under
the config dir's instances/, each read only for its namespaces, with the same `shared()`: real
paths, containment, the canonical Vault host. So two named instances whose restic repositories
nest refuse, as does a named root linked to another's, or two overlays declaring one id; two
disjoint named instances both load, and an overlay that could never load is left out.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from core.kernel.config import loader

BASE = "s3:s3.us-east-1.amazonaws.com/example-instance-backups"


def _host(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    (repo / "config" / "instances").mkdir(parents=True)
    monkeypatch.setattr(loader, "REPO_ROOT", repo)
    monkeypatch.setattr(loader, "_CONFIG_DIR", repo / "config")
    monkeypatch.setattr(loader, "_INSTANCE_OVERLAY", repo / "config" / "ouroboros.toml")
    monkeypatch.setattr(loader, "_LEGACY_OVERLAY", repo / "config" / "local.toml")
    monkeypatch.setattr(loader, "LEVERS_OVERLAY", repo / "config" / "levers.toml")
    monkeypatch.delenv(loader.OVERLAY_ENV, raising=False)
    return repo


def _declare(repo: Path, name: str, text: str) -> Path:
    overlay = repo / "config" / "instances" / f"{name}.toml"
    overlay.write_text(text)
    return overlay


def _load(monkeypatch: pytest.MonkeyPatch, overlay: Path) -> loader.Config:
    monkeypatch.setenv(loader.OVERLAY_ENV, str(overlay))
    return loader.load_config()


def test_two_named_instances_whose_repositories_nest_refuse(monkeypatch, tmp_path) -> None:
    repo = _host(monkeypatch, tmp_path)
    a = _declare(repo, "a", f'[instance]\nid = "a"\n[backup]\nrepository = "{BASE}/a"\n')
    b = _declare(repo, "b", f'[instance]\nid = "b"\n[backup]\nrepository = "{BASE}/a/b"\n')
    for overlay, other in ((a, "'b'"), (b, "'a'")):
        with pytest.raises(loader.InstanceOverlayError, match=f"would share these with {other}"):
            _load(monkeypatch, overlay)


def test_a_named_root_linked_to_another_named_root_refuses(monkeypatch, tmp_path) -> None:
    repo = _host(monkeypatch, tmp_path)
    a = _declare(repo, "a", '[instance]\nid = "a"\n')
    b = _declare(repo, "b", '[instance]\nid = "b"\n')
    (repo / "instances" / "a").mkdir(parents=True)
    (repo / "instances" / "b").symlink_to(repo / "instances" / "a")
    for overlay in (a, b):
        with pytest.raises(loader.InstanceOverlayError, match="would share"):
            _load(monkeypatch, overlay)


def test_two_overlays_declaring_one_id_refuse(monkeypatch, tmp_path) -> None:
    repo = _host(monkeypatch, tmp_path)
    first = _declare(repo, "first", '[instance]\nid = "x"\n')
    _declare(repo, "second", '[instance]\nid = "x"\n')
    with pytest.raises(loader.InstanceOverlayError, match="another overlay declares"):
        _load(monkeypatch, first)


def test_control_two_disjoint_named_instances_both_load(monkeypatch, tmp_path) -> None:
    repo = _host(monkeypatch, tmp_path)
    a = _declare(repo, "a", f'[instance]\nid = "a"\n[backup]\nrepository = "{BASE}/a"\n')
    b = _declare(repo, "b", f'[instance]\nid = "b"\n[backup]\nrepository = "{BASE}/b"\n')
    (repo / "instances" / "a").mkdir(parents=True)
    (repo / "instances" / "b").mkdir(parents=True)
    assert _load(monkeypatch, a).instance.id == "a"
    assert _load(monkeypatch, b).instance.id == "b"


def test_an_overlay_that_could_never_load_is_left_out(monkeypatch, tmp_path) -> None:
    """No readable TOML, no id, an id of Ouroboros's: none of them can run, so none holds a
    namespace that could stop another instance."""
    repo = _host(monkeypatch, tmp_path)
    _declare(repo, "broken", "[instance\nid = ")
    _declare(repo, "unnamed", '[dreaming]\nsimilarity_threshold = 0.7\n')
    _declare(repo, "claims", '[instance]\nid = "ouroboros"\n')
    a = _declare(repo, "a", '[instance]\nid = "a"\n')
    assert _load(monkeypatch, a).instance.id == "a"


def test_two_named_instances_cannot_read_one_corpus(monkeypatch, tmp_path) -> None:
    """Sources count like every other location: a corpus two named instances both declare is
    shared, so neither loads while the other is declared."""
    repo = _host(monkeypatch, tmp_path)
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    a = _declare(repo, "a", f'[instance]\nid = "a"\n[ingestion.vault]\npath = "{corpus}"\n')
    _declare(repo, "b", f'[instance]\nid = "b"\n[ingestion.vault]\npath = "{corpus / "notes"}"\n')
    with pytest.raises(loader.InstanceOverlayError, match="would share these with 'b'"):
        _load(monkeypatch, a)
