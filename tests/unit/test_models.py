"""Two-slot discipline + memory ceiling (BUILD-SPEC §5, Invariant 8).

These exercise the eviction/accounting logic with warm=False, so no live Ollama is
needed — the ceiling is checked before any server call.

bp-107 retrofit: the loader now probes `ps()` at construction (finding-0199 — residency is
measured, not believed), so "no live Ollama is needed" had to become "no live Ollama is
CONSULTED". Built on a real `OllamaClient` these tests would read whatever the developer's Ollama
happens to hold: measured here, `test_ceiling_refuses_breaching_load` errors on its first line and
the FSM oracle diverges as soon as anything is warm. `loader_for` supplies a hermetic client whose
`ps()` is empty, which is exactly the state these tests always assumed. Not one assertion changed.
"""

import dataclasses

import pytest

from config.loader import load_config
from core.models.registry import MemoryCeilingError
from tests.unit.test_loader_reconcile import loader_for


def _loader(cfg=None):
    return loader_for(cfg)


def test_pinned_and_worker_coexist():
    ld = _loader()
    ld.ensure_pinned(warm=False)
    ld.ensure_tier("routine", warm=False)
    assert set(ld.resident_models()) == {"qwen3.5:2b", "qwen3.5:9b"}
    assert ld.resident_gb() <= ld.config.resources.usable_ram_gb


def test_single_worker_slot_evicts_prior_worker():
    ld = _loader()
    ld.ensure_pinned(warm=False)
    ld.ensure_tier("routine", warm=False)
    ld.ensure_tier("synthesis", warm=False)
    assert set(ld.resident_models()) == {"qwen3.5:2b", "qwen3.6:27b"}  # routine evicted


def test_stretch_evicts_pinned_and_runs_solo():
    ld = _loader()
    ld.ensure_pinned(warm=False)
    ld.ensure_tier("stretch", warm=False)
    assert ld.resident_models() == ["qwen3.6:35b-a3b"]  # sole resident


def test_ceiling_refuses_breaching_load():
    cfg = load_config()
    cfg = dataclasses.replace(
        cfg, resources=dataclasses.replace(cfg.resources, usable_ram_gb=5.0)
    )
    ld = _loader(cfg)
    ld.ensure_pinned(warm=False)  # 1.9 <= 5 ok
    with pytest.raises(MemoryCeilingError):
        ld.ensure_tier("synthesis", warm=False)  # 1.9 + 17 > 5 -> refused
    # the refusal must not have loaded the worker
    assert ld.resident_models() == ["qwen3.5:2b"]


def test_idempotent_ensure_is_a_noop():
    ld = _loader()
    ld.ensure_pinned(warm=False)
    before = ld.resident_models()
    ld.ensure_pinned(warm=False)
    assert ld.resident_models() == before
