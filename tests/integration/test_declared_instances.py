"""A named instance can reach no instance declared on its host, not only Ouroboros.

The loader checks the instance it loads against Ouroboros and against every other overlay under
the config dir's instances/, each read only for its namespaces, with the same `shared()`. The rule
is on write sets: what one writes may not lie at, inside or around what the other writes or
reads, and names, labels and the Vault host may not collide. So two named instances whose restic
repositories nest refuse, as does a named root linked to another's, two overlays declaring one id,
or a source inside another instance's written state. Two named instances may read one source
neither writes; the default instance's sources stay private. Two disjoint named instances both
load, and an overlay that could never load is left out.
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


@pytest.mark.parametrize("b_source", ["corpus", "corpus/notes"])
def test_two_named_instances_share_one_read_only_corpus(monkeypatch, tmp_path, b_source) -> None:
    """A corpus neither instance writes, declared by both, or one nested in the other's: nothing
    either writes can reach the other through it, so both load."""
    repo = _host(monkeypatch, tmp_path)
    (tmp_path / "corpus" / "notes").mkdir(parents=True)
    a = _declare(repo, "a", f'[instance]\nid = "a"\n[ingestion.vault]\n'
                            f'path = "{tmp_path / "corpus"}"\n')
    b = _declare(repo, "b", f'[instance]\nid = "b"\n[ingestion.vault]\n'
                            f'path = "{tmp_path / b_source}"\n')
    assert _load(monkeypatch, a).ingestion.vault.path == tmp_path / "corpus"
    assert _load(monkeypatch, b).ingestion.vault.path == tmp_path / b_source


@pytest.mark.parametrize("where", ["instances/b/data", "instances/b/data/raw",
                                   "instances/b/exhaust"])
def test_a_named_source_in_another_named_instances_writes_refuses(monkeypatch, tmp_path,
                                                                 where) -> None:
    """A source inside what another instance writes would read that instance's outputs."""
    repo = _host(monkeypatch, tmp_path)
    a = _declare(repo, "a", f'[instance]\nid = "a"\n[ingestion.vault]\npath = "{repo / where}"\n')
    b = _declare(repo, "b", '[instance]\nid = "b"\n')
    for overlay, other in ((a, "'b'"), (b, "'a'")):
        with pytest.raises(loader.InstanceOverlayError,
                           match=f"would share these with {other} [(].*[)]:\n    (read|written) "):
            _load(monkeypatch, overlay)


def test_a_named_source_in_the_default_corpus_still_refuses(monkeypatch, tmp_path) -> None:
    """The default instance's sources are private: no named instance reads at or inside them,
    though Ouroboros writes nothing there."""
    repo = _host(monkeypatch, tmp_path)
    vault = tmp_path / "vault"
    (vault / "notes").mkdir(parents=True)
    (repo / "config" / "ouroboros.toml").write_text(f'[ingestion.vault]\npath = "{vault}"\n')
    for source in (vault, vault / "notes"):
        a = _declare(repo, "a", f'[instance]\nid = "a"\n[ingestion.vault]\npath = "{source}"\n')
        with pytest.raises(loader.InstanceOverlayError,
                           match="would share these with 'ouroboros':\n    read .* and read "):
            _load(monkeypatch, a)
