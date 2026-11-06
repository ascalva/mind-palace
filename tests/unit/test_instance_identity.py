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
    ("airlock", "aws_profile"): "mind-palace-bridge",
}


def _isolated(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(loader, "_CONFIG_DIR", tmp_path)
    monkeypatch.setattr(loader, "_INSTANCE_OVERLAY", tmp_path / "ouroboros.toml")
    monkeypatch.setattr(loader, "_LEGACY_OVERLAY", tmp_path / "local.toml")
    monkeypatch.setattr(loader, "LEVERS_OVERLAY", tmp_path / "levers.toml")


def _as_ouroboros(monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
                  text: str | None = None) -> loader.Config:
    _isolated(monkeypatch, tmp_path)
    monkeypatch.delenv(loader.OVERLAY_ENV, raising=False)
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


@pytest.mark.parametrize("iid", ["../x", "Bench", "", "a/b"])
def test_an_instance_config_holds_only_a_well_formed_id(iid) -> None:
    """Any caller, not only the loader: the namespace map is defined on well-formed ids."""
    with pytest.raises(ValueError):
        loader.InstanceConfig(iid)


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


# ── the namespaces derived from the id ───────────────────────────────────────────────────────────

NAMED_BACKUPS = "s3:s3.us-east-1.amazonaws.com/example-instance-backups"


def test_ouroboros_holds_todays_namespaces(monkeypatch, tmp_path) -> None:
    """The pin, on the namespace map: Ouroboros's data dir, spool, lock, levers file, Keychain
    items and launchd labels are the ones it had before instances had ids."""
    cfg = _as_ouroboros(monkeypatch, tmp_path)
    ns = loader.namespaces_of(cfg)
    repo = loader.REPO_ROOT
    assert cfg.instance.root == repo
    assert ns.data_dir == repo / "data" and ns.spool == repo / "data" / "handoff"
    assert ns.supervisor_lock == repo / "data" / "supervisor.lock"
    assert ns.levers == loader.LEVERS_OVERLAY == tmp_path / "levers.toml"
    assert ns.secrets == {*SECRETS.values(), "vault-supervisor-token"}
    assert (cfg.secrets.addr, ns.vault) == ("http://127.0.0.1:8200", "loopback:8200")
    assert ns.labels == {"com.mind-palace.palace", "com.mind-palace.tick"}
    assert ns.backup == "s3:s3.us-east-1.amazonaws.com/example-ouroboros-backups"
    assert ns.sources == {Path("~/.mind-palace/vault/notes").expanduser(),
                          loader.default_transcripts_dir()}
    assert ns.dialogue == {"openwebui", "opencode"} and cfg.instance.dialogue == ("openwebui",
                                                                                 "opencode")
    assert ns.exhaust == cfg.exhaust.path == Path("~/.mind-palace/exhaust").expanduser()


def test_a_named_instance_holds_namespaces_derived_from_its_id(monkeypatch, tmp_path) -> None:
    cfg = _as_named(monkeypatch, tmp_path,
                    f'[instance]\nid = "bench"\n[backup]\nrepository = "{NAMED_BACKUPS}/bench"\n')
    ns = loader.namespaces_of(cfg)
    root = loader.REPO_ROOT / "instances" / "bench"
    assert cfg.instance.root == root
    for section, key in WRITTEN:                    # every written path, under the instance's root
        assert _value(cfg, section, key) == root / loader._read(loader._DEFAULTS)[section][key]
    assert ns.data_dir == root / "data" and ns.spool == root / "data" / "handoff"
    assert ns.supervisor_lock == root / "data" / "supervisor.lock"
    assert ns.levers == root / "levers.toml"
    assert ns.secrets == {f"bench.{name}" for name in (*SECRETS.values(), "vault-supervisor-token")}
    assert ns.labels == {"com.mind-palace.bench.palace", "com.mind-palace.bench.tick"}
    assert cfg.attestation.signing_key_secret == "bench.attestation-signing-key"
    assert ns.backup == f"{NAMED_BACKUPS}/bench"


def test_control_the_pin_tells_ouroboros_from_a_named_instance(monkeypatch, tmp_path) -> None:
    """The same overlay loaded as a named instance differs from Ouroboros in every namespace and
    shares none, so a derivation leaking into the default chain would fail the pin above."""
    ouroboros = loader.namespaces_of(_as_ouroboros(monkeypatch, tmp_path))
    text = FIXTURE.read_text().replace(
        "s3:s3.us-east-1.amazonaws.com/example-ouroboros-backups", f"{NAMED_BACKUPS}/twin").replace(
        "~/.mind-palace/vault/notes", str(tmp_path / "twin-notes"))
    twin = loader.namespaces_of(_as_named(monkeypatch, tmp_path, text.replace(
        "[secrets]\nenabled = true", '[secrets]\nenabled = true\naddr = "http://127.0.0.1:8210"')
        + '\n[instance]\nid = "twin"\n'))
    for field in ("data_dir", "spool", "supervisor_lock", "levers", "exhaust", "sources",
                  "dialogue", "secrets", "labels", "backup", "vault"):
        assert getattr(twin, field) != getattr(ouroboros, field), field
    assert loader.shared(twin, ouroboros) == []
    assert loader.shared(twin, twin) and loader.shared(ouroboros, ouroboros)


@pytest.mark.parametrize("line", ['signing_key_secret = "bench.attestation-signing-key"',
                                  'owner_key_secret = "attestation-owner-key"'])
def test_a_named_overlay_does_not_name_its_secrets(monkeypatch, tmp_path, line) -> None:
    """Even the derived name refuses: the item names are the id's to derive, so an overlay that
    states one is either redundant or a way into another instance's items."""
    with pytest.raises(loader.InstanceOverlayError, match="derived from the instance id"):
        _as_named(monkeypatch, tmp_path, f'[instance]\nid = "bench"\n[attestation]\n{line}\n')


@pytest.mark.parametrize("value", ["/var/elsewhere", "data/../../data", "../data"])
def test_a_named_path_stays_under_its_root(monkeypatch, tmp_path, value) -> None:
    with pytest.raises(loader.InstanceOverlayError, match="leaves the instance's root"):
        _as_named(monkeypatch, tmp_path,
                  f'[instance]\nid = "bench"\n[paths]\ndata_dir = "{value}"\n')


def test_a_named_path_may_move_within_its_root(monkeypatch, tmp_path) -> None:
    cfg = _as_named(monkeypatch, tmp_path, '[instance]\nid = "bench"\n[interface]\n'
                                           'handoff_dir = "data/spool"\n')
    assert cfg.interface.handoff_dir == loader.REPO_ROOT / "instances" / "bench" / "data" / "spool"


@pytest.mark.parametrize("repository", [
    "s3:s3.us-east-1.amazonaws.com/example-ouroboros-backups",          # Ouroboros's, verbatim
    "s3:s3.us-east-1.amazonaws.com/example-ouroboros-backups/bench",    # inside Ouroboros's
    "s3:s3.us-east-1.amazonaws.com/EXAMPLE-ouroboros-backups/bench/",   # the same, spelt otherwise
    f"{NAMED_BACKUPS}/other",                                           # not this instance's
])
def test_a_named_instance_never_writes_ouroboros_repository(monkeypatch, tmp_path,
                                                            repository) -> None:
    """Ouroboros's restic repository is read off its own overlay on this host; a named instance
    that would write to it, or under it, refuses outright."""
    _isolated(monkeypatch, tmp_path)
    (tmp_path / "ouroboros.toml").write_text(FIXTURE.read_text())
    overlay = tmp_path / "named.toml"
    overlay.write_text(f'[instance]\nid = "bench"\n[backup]\nrepository = "{repository}"\n')
    monkeypatch.setenv(loader.OVERLAY_ENV, str(overlay))
    with pytest.raises(loader.InstanceOverlayError):
        loader.load_config()


def test_the_supervisor_lock_is_one_per_instance(monkeypatch, tmp_path) -> None:
    """The lock is scoped to the instance: two instances on one host each hold their own, and a
    second claimant of one instance's lock is refused by the kernel."""
    from ops.lifecycle.lock import SupervisorLock, SupervisorLockHeld

    monkeypatch.setattr(loader, "REPO_ROOT", tmp_path)
    locks = []
    for text in ('[instance]\nid = "one"\n', '[instance]\nid = "two"\n'):
        locks.append(loader.namespaces_of(_as_named(monkeypatch, tmp_path, text)).supervisor_lock)
    locks.append(loader.namespaces_of(_as_ouroboros(monkeypatch, tmp_path, "")).supervisor_lock)
    held = [SupervisorLock(path) for path in locks]
    try:
        for lock in held:
            lock.acquire()                              # three instances, three locks, no refusal
        with pytest.raises(SupervisorLockHeld):
            SupervisorLock(locks[0]).acquire()          # control: one instance's lock is exclusive
    finally:
        for lock in held:
            lock.release()


# ── the sources a named instance reads ──────────────────────────────────────────────────────────


def test_a_named_instance_reads_no_source_it_did_not_declare(monkeypatch, tmp_path) -> None:
    """The committed defaults name Ouroboros's corpus: a vault under ~/.mind-palace, this
    checkout's Claude Code transcripts, the owner's chat applications. None of it reaches a named
    instance; each undeclared source points into its own root, and its agent is off."""
    cfg = _as_named(monkeypatch, tmp_path, '[instance]\nid = "bench"\n')
    root = loader.REPO_ROOT / "instances" / "bench"
    assert (cfg.ingestion.vault.path, cfg.ingestion.vault.enabled) == (root / "vault", False)
    assert (cfg.ingestion.transcripts.transcripts_dir, cfg.ingestion.transcripts.enabled) == (
        root / "transcripts", False)
    assert not cfg.ingestion.code.enabled and cfg.instance.dialogue == ()
    ns = loader.namespaces_of(cfg)
    assert all(p.is_relative_to(root) for p in ns.sources | ns.paths) and not ns.dialogue


def test_a_declared_source_is_read_where_it_lies(monkeypatch, tmp_path) -> None:
    corpus = tmp_path / "corpus"
    cfg = _as_named(monkeypatch, tmp_path, f'[instance]\nid = "bench"\n[ingestion.vault]\n'
                                           f'path = "{corpus}"\nenabled = true\n'
                                           '[ingestion.transcripts]\ntranscripts_dir = "talk"\n')
    assert (cfg.ingestion.vault.path, cfg.ingestion.vault.enabled) == (corpus, True)
    assert cfg.ingestion.transcripts.transcripts_dir == (
        loader.REPO_ROOT / "instances" / "bench" / "talk")         # relative: under the root
    assert cfg.ingestion.transcripts.enabled      # a declared source keeps its agent's default


@pytest.mark.parametrize(("key", "value"), [
    ("[ingestion.vault]\npath", "~/.mind-palace/vault/notes"),        # Ouroboros's vault
    ("[ingestion.vault]\npath", "~/.mind-palace/vault/notes/inbox"),  # inside it
    ("[ingestion.vault]\npath", "~/.mind-palace"),                    # around it
    ("[ingestion.vault]\npath", "REPO/data/raw"),                     # inside Ouroboros's data
    ("[ingestion.transcripts]\ntranscripts_dir", "TRANSCRIPTS"),      # Ouroboros's transcripts
])
def test_a_declared_source_of_ouroboros_refuses(monkeypatch, tmp_path, key, value) -> None:
    """Locations compare as locations: at, inside or around any of Ouroboros's (its sources and
    every path it writes) refuses, read off Ouroboros's own overlay on this host."""
    value = value.replace("REPO", str(loader.REPO_ROOT)).replace(
        "TRANSCRIPTS", str(loader.default_transcripts_dir()))
    _isolated(monkeypatch, tmp_path)
    (tmp_path / "ouroboros.toml").write_text(FIXTURE.read_text())
    overlay = tmp_path / "named.toml"
    overlay.write_text(f'[instance]\nid = "bench"\n{key} = "{value}"\n')
    monkeypatch.setenv(loader.OVERLAY_ENV, str(overlay))
    with pytest.raises(loader.InstanceOverlayError, match="would share"):
        loader.load_config()


@pytest.mark.parametrize("agent", ["vault", "transcripts"])
def test_turning_an_agent_on_without_its_source_refuses(monkeypatch, tmp_path, agent) -> None:
    with pytest.raises(loader.InstanceOverlayError, match="names no"):
        _as_named(monkeypatch, tmp_path,
                  f'[instance]\nid = "bench"\n[ingestion.{agent}]\nenabled = true\n')


# ── the exhaust lane ─────────────────────────────────────────────────────────────────────────────


def test_a_named_instances_lane_derives_from_its_id(monkeypatch, tmp_path) -> None:
    root = loader.REPO_ROOT / "instances" / "bench"
    cfg = _as_named(monkeypatch, tmp_path, '[instance]\nid = "bench"\n')
    assert cfg.exhaust.path == root / "exhaust" == loader.namespaces_of(cfg).exhaust
    moved = _as_named(monkeypatch, tmp_path, '[instance]\nid = "bench"\n[exhaust]\npath = "out"\n')
    assert moved.exhaust.path == root / "out"


@pytest.mark.parametrize("lane", ["~/.mind-palace/exhaust", "/var/elsewhere", "../exhaust"])
def test_a_named_lane_stays_under_its_root(monkeypatch, tmp_path, lane) -> None:
    """Ouroboros's lane is the one the owner reads on his phone as Ouroboros's; a named instance's
    reports never land in it, nor anywhere outside its own root."""
    with pytest.raises(loader.InstanceOverlayError, match="leaves the instance's root"):
        _as_named(monkeypatch, tmp_path, f'[instance]\nid = "bench"\n[exhaust]\npath = "{lane}"\n')


def test_a_named_instances_reports_land_in_its_own_lane(monkeypatch, tmp_path) -> None:
    import importlib.util

    monkeypatch.setattr(loader, "REPO_ROOT", tmp_path)
    cfg = _as_named(monkeypatch, tmp_path, '[instance]\nid = "bench"\n')
    loader.get_config.cache_clear()
    spec = importlib.util.spec_from_file_location(
        "exhaust_report", Path(__file__).resolve().parents[2] / "scripts" / "exhaust_report.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    html = tmp_path / "r.html"
    html.write_text("<p>report</p>")
    dest = module.place_report(html, "bp-1", "slug")
    assert dest.is_relative_to(cfg.exhaust.path / "reports")
    assert dest.is_relative_to(tmp_path / "instances" / "bench")


# ── the Vault ────────────────────────────────────────────────────────────────────────────────────


def test_a_named_instance_that_names_no_vault_has_none(monkeypatch, tmp_path) -> None:
    from config.secrets_backend import build_secrets_backend

    cfg = _as_named(monkeypatch, tmp_path, '[instance]\nid = "bench"\n')
    assert (cfg.secrets.enabled, cfg.secrets.addr) == (False, "")
    assert loader.namespaces_of(cfg).vault == "" and build_secrets_backend(cfg) is None


def test_turning_secrets_on_without_a_vault_refuses(monkeypatch, tmp_path) -> None:
    with pytest.raises(loader.InstanceOverlayError, match="names no addr"):
        _as_named(monkeypatch, tmp_path, '[instance]\nid = "bench"\n[secrets]\nenabled = true\n')


@pytest.mark.parametrize("addr", ["http://127.0.0.1:8200", "http://localhost:8200/",
                                  "http://[::1]:8200", "127.0.0.1:8200"])
def test_no_named_instance_reaches_ouroboros_vault(monkeypatch, tmp_path, addr) -> None:
    """Ouroboros's Vault is the server its overlay names on this host (the committed default):
    a named instance naming it, in any spelling, refuses."""
    _isolated(monkeypatch, tmp_path)
    (tmp_path / "ouroboros.toml").write_text(FIXTURE.read_text())
    overlay = tmp_path / "named.toml"
    overlay.write_text(f'[instance]\nid = "bench"\n[secrets]\nenabled = true\naddr = "{addr}"\n')
    monkeypatch.setenv(loader.OVERLAY_ENV, str(overlay))
    with pytest.raises(loader.InstanceOverlayError, match="Vault server loopback:8200"):
        loader.load_config()


def test_a_named_instances_own_vault_gets_its_own_token(monkeypatch, tmp_path) -> None:
    """Its own server, and its own token item: Ouroboros's token never travels to another Vault."""
    import config.secrets_backend as backend

    cfg = _as_named(monkeypatch, tmp_path, '[instance]\nid = "bench"\n[secrets]\n'
                                           'enabled = true\naddr = "https://127.0.0.1:8210"\n')
    assert loader.namespaces_of(cfg).vault == "loopback:8210"
    asked: list[str] = []
    monkeypatch.setattr("config.loader.get_secret", lambda name, token=None: asked.append(name))
    monkeypatch.setattr(backend, "VaultClient", lambda **kw: kw)
    client = backend.build_secrets_backend(cfg)
    assert asked == ["bench.vault-supervisor-token"]
    assert client == {"addr": "https://127.0.0.1:8210", "kv_mount": "kv", "supervisor_token": None}
