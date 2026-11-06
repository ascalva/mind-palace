"""Instance identity (DI-2, #25): the `[instance]` section and its id.

The default chain is Ouroboros, the live instance, and it must read exactly as it did before
instances had ids. `FIXTURE` has the shape of Ouroboros's live overlay (the same sections and keys,
no `[instance]` section), and the pin below holds every value this change can reach to what the old
loader computed from the same TOML: each written path is the repo root joined to its TOML value,
each secret name is its committed default. A named overlay must declare an id of its own, and
Ouroboros's id belongs to the default chain alone. Every case runs in a temporary config
directory; the owner's overlay is never read.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

from core.kernel.config import loader

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "instances" / "ouroboros.toml"

# Every path the config names that an instance writes, listed here rather than imported, so the
# pin does not take the loader's word for which paths those are.
WRITTEN = (
    ("paths", "data_dir"), ("paths", "telemetry_db"), ("paths", "raw_store"),
    ("paths", "vector_store"), ("paths", "derived_store"), ("paths", "vault_catalog"),
    ("paths", "attestation_store"), ("paths", "curated_store"),
    ("interface", "handoff_dir"), ("airlock", "handoff_dir"), ("selfmod", "ledger_db"),
    ("effectors", "handoff_dir"), ("effectors", "ledger_db"), ("effectors", "drafts_dir"),
)
SECRETS = {
    ("attestation", "signing_key_secret"): "attestation-signing-key",
    ("attestation", "owner_key_secret"): "attestation-owner-key",
    ("backup", "password_secret"): "restic-password",
    ("backup", "aws_access_key_id_secret"): "backup-aws-access-key-id",
    ("backup", "aws_secret_access_key_secret"): "backup-aws-secret-access-key",
}


def _isolated(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(loader, "_CONFIG_DIR", tmp_path)
    monkeypatch.setattr(loader, "_INSTANCE_OVERLAY", tmp_path / "ouroboros.toml")
    monkeypatch.setattr(loader, "_LEGACY_OVERLAY", tmp_path / "local.toml")
    monkeypatch.setattr(loader, "LEVERS_OVERLAY", tmp_path / "levers.toml")


def _as_ouroboros(monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
                  text: str | None = None) -> loader.Config:
    _isolated(monkeypatch, tmp_path)
    (tmp_path / "ouroboros.toml").write_text(FIXTURE.read_text() if text is None else text)
    return loader.load_config()


def _as_named(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, text: str) -> loader.Config:
    _isolated(monkeypatch, tmp_path)
    overlay = tmp_path / "named.toml"
    overlay.write_text(text)
    monkeypatch.setenv(loader.OVERLAY_ENV, str(overlay))
    return loader.load_config()


def _value(cfg: loader.Config, section: str, key: str) -> object:
    return getattr(getattr(cfg, section), key)


def test_the_default_chain_is_ouroboros_and_reads_as_before(monkeypatch, tmp_path) -> None:
    """The regression pin. Ouroboros's overlay, as shaped on 2026-11-05, loads under the id
    `ouroboros`; every written path is `<repo>/<its TOML value>` (the old `_resolve`), every secret
    name is today's, the backup repository is the overlay's, and the overlay still wins over the
    committed defaults."""
    cfg = _as_ouroboros(monkeypatch, tmp_path)
    assert cfg.instance == loader.InstanceConfig() and cfg.instance.id == "ouroboros"
    assert not cfg.instance.named

    raw = tomllib.loads(loader._DEFAULTS.read_text(encoding="utf-8"))
    loader._deep_merge(raw, tomllib.loads(FIXTURE.read_text(encoding="utf-8")))
    for section, key in WRITTEN:
        assert _value(cfg, section, key) == loader.REPO_ROOT / raw[section][key], (section, key)
    assert cfg.paths.data_dir == loader.REPO_ROOT / "data"
    assert cfg.interface.handoff_dir == loader.REPO_ROOT / "data" / "handoff"
    for (section, key), name in SECRETS.items():
        assert _value(cfg, section, key) == raw[section][key] == name
    assert cfg.backup.repository == "s3:s3.us-east-1.amazonaws.com/example-ouroboros-backups"

    # the overlay's own values arrive, over the defaults
    assert cfg.dreaming.similarity_threshold == 0.785 and cfg.dream_rnd.sigma == 0.785
    assert (cfg.embedding.model, cfg.embedding.dim) == ("embeddinggemma-2", 768)
    assert cfg.runtime.chat_backend_for("synthesis") == "llamacpp"
    assert cfg.ingestion.vault.path == Path("~/.mind-palace/vault/notes").expanduser()
    assert not cfg.ingestion.code.enabled and not cfg.ingestion.transcripts.enabled
    assert cfg.secrets.enabled and cfg.backup.enabled and not cfg.dreaming.scheduled


def test_a_fresh_clone_is_ouroboros_too(monkeypatch, tmp_path) -> None:
    _isolated(monkeypatch, tmp_path)
    cfg = loader.load_config()
    assert cfg.instance.id == loader.OUROBOROS and cfg.paths.data_dir == loader.REPO_ROOT / "data"
    assert loader.load_config(loader._DEFAULTS).instance.id == loader.OUROBOROS


def test_ouroboros_may_restate_its_id_and_nothing_changes(monkeypatch, tmp_path) -> None:
    unstated = _as_ouroboros(monkeypatch, tmp_path)
    restated = _as_ouroboros(monkeypatch, tmp_path,
                             FIXTURE.read_text() + '\n[instance]\nid = "ouroboros"\n')
    assert restated == unstated


@pytest.mark.parametrize("instance", ['id = "bench"', 'id = "ouroboros"\nlevers = "x.toml"'])
def test_the_default_chain_cannot_be_renamed(monkeypatch, tmp_path, instance) -> None:
    """Another id in Ouroboros's overlay would rename the live instance in place, and a key the
    section does not hold would be a setting that looks applied and never took."""
    with pytest.raises(loader.InstanceOverlayError):
        _as_ouroboros(monkeypatch, tmp_path, FIXTURE.read_text() + f"\n[instance]\n{instance}\n")


def test_a_file_read_by_path_is_ouroboros(tmp_path) -> None:
    """`load_config(path)` reads one file verbatim, as Ouroboros. A named instance is loaded from
    its overlay through `MIND_PALACE_OVERLAY`, never by path, so an id in the file refuses."""
    named = tmp_path / "named.toml"
    named.write_text('[instance]\nid = "bench"\n')
    with pytest.raises(loader.InstanceOverlayError, match="bench"):
        loader.load_config(named)


def test_a_named_overlay_must_declare_its_id(monkeypatch, tmp_path) -> None:
    with pytest.raises(loader.InstanceOverlayError, match="declares no instance id"):
        _as_named(monkeypatch, tmp_path, "[dreaming]\nsimilarity_threshold = 0.7\n")
    with pytest.raises(loader.InstanceOverlayError, match="declares no instance id"):
        _as_named(monkeypatch, tmp_path, "[instance]\n")


def test_no_named_overlay_may_claim_ouroboros(monkeypatch, tmp_path) -> None:
    with pytest.raises(loader.InstanceOverlayError, match="default chain"):
        _as_named(monkeypatch, tmp_path, '[instance]\nid = "ouroboros"\n')


@pytest.mark.parametrize("iid", ['"Bench"', '"1x"', '"a.b"', '"a/b"', '""', '"-a"', '"a_b"',
                                 '"' + "x" * 33 + '"', "7", '["a"]'])
def test_an_id_is_one_lowercase_segment(monkeypatch, tmp_path, iid) -> None:
    """Uppercase would let two ids name one directory on APFS; `.` and `/` would let one id read
    as two segments; the rest keeps an id a plain name in a label, an item and a path."""
    with pytest.raises(loader.InstanceOverlayError, match="not an instance id"):
        _as_named(monkeypatch, tmp_path, f"[instance]\nid = {iid}\n")


@pytest.mark.parametrize("iid", ["a", "bench", "a-1", "x" * 32])
def test_a_well_formed_id_is_the_instance(monkeypatch, tmp_path, iid) -> None:
    cfg = _as_named(monkeypatch, tmp_path, f'[instance]\nid = "{iid}"\n')
    assert cfg.instance.id == iid and cfg.instance.named
    assert loader.get_config().instance.id == iid           # surfaced through get_config()


@pytest.mark.parametrize("text", ['[instance]\nid = "bench"\nroot = "/tmp"\n',
                                  'instance = "bench"\n'])
def test_the_instance_section_holds_one_key(monkeypatch, tmp_path, text) -> None:
    with pytest.raises(loader.InstanceOverlayError):
        _as_named(monkeypatch, tmp_path, text)
