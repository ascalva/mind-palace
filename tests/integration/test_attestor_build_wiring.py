"""build_curator / build_dreamer / build_vault_sync wire a real Attestor (attestation-layer.md §5).

Each was extended in Step 2 to auto-wire `build_attestor(cfg)` so cron-driven runs attest
without any extra plumbing — but until now nothing constructed them and checked the wiring.
Safe to construct without a live Ollama/model server: `OllamaClient`/`build_model_server`/
`lancedb.connect` are all side-effect-free at construction (no request is made until a chat/
embed call), so this is a wiring check, not a live integration test.
"""

from __future__ import annotations

import dataclasses

from config.loader import get_config
from core.attestation import StoreAttestor
from core.curator import build_curator
from core.dreaming import build_dreamer
from core.ingest.sync import build_vault_sync


def _cfg_in(tmp_path):
    cfg = get_config()
    paths = dataclasses.replace(
        cfg.paths,
        raw_store=tmp_path / "raw",
        vector_store=tmp_path / "v.lance",
        derived_store=tmp_path / "derived.sqlite",
        vault_catalog=tmp_path / "catalog.sqlite",
        attestation_store=tmp_path / "attestations.sqlite",
    )
    vault = dataclasses.replace(cfg.vault, path=tmp_path / "vault")
    return dataclasses.replace(cfg, paths=paths, vault=vault)


def test_build_curator_wires_an_attestor(tmp_path):
    cfg = _cfg_in(tmp_path)
    curator = build_curator(cfg)
    assert isinstance(curator.attestor, StoreAttestor)
    assert curator.attestor.store.path == cfg.paths.attestation_store


def test_build_dreamer_wires_an_attestor(tmp_path):
    cfg = _cfg_in(tmp_path)
    dreamer = build_dreamer(cfg)
    assert isinstance(dreamer.attestor, StoreAttestor)
    assert dreamer.attestor.store.path == cfg.paths.attestation_store


def test_build_vault_sync_wires_an_attestor(tmp_path):
    cfg = _cfg_in(tmp_path)
    sync = build_vault_sync(cfg)
    assert isinstance(sync.attestor, StoreAttestor)
    assert sync.attestor.store.path == cfg.paths.attestation_store


def test_wired_attestors_share_the_configured_store_across_agents(tmp_path):
    # Same config -> same on-disk store path -> in production, attestations from different
    # agents chain together exactly as the fixture-built integrity tests simulate.
    cfg = _cfg_in(tmp_path)
    curator = build_curator(cfg)
    dreamer = build_dreamer(cfg)
    sync = build_vault_sync(cfg)
    assert isinstance(curator.attestor, StoreAttestor)
    assert isinstance(dreamer.attestor, StoreAttestor)
    assert isinstance(sync.attestor, StoreAttestor)
    paths = {curator.attestor.store.path, dreamer.attestor.store.path, sync.attestor.store.path}
    assert paths == {cfg.paths.attestation_store}
