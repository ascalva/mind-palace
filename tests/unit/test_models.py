"""Two-slot discipline + memory ceiling (BUILD-SPEC §5, Invariant 8).

These exercise the eviction/accounting logic with warm=False, so no live Ollama is
needed — the ceiling is checked before any server call.
"""

import dataclasses

import pytest

from config.loader import load_config
from core.models.loader import TwoSlotLoader
from core.models.ollama_client import OllamaClient
from core.models.registry import MemoryCeilingError, Registry


def _loader(cfg=None):
    cfg = cfg or load_config()
    return TwoSlotLoader(config=cfg, client=OllamaClient(cfg.ollama), registry=Registry(cfg))


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
