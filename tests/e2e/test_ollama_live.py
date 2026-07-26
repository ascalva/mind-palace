"""Live gate: a model responds through the sealed core (requires Ollama + pulled model).

Marked `live` and skipped automatically when Ollama is down or the pinned model is not
pulled. Run with: pytest -m live
"""

import dataclasses

import pytest

from config.loader import get_config
from core import runtime
from core.models import build_model_server

pytestmark = pytest.mark.live

PINNED = "qwen3.5:2b"


def _ollama_up() -> bool:
    try:
        return bool(build_model_server().version())
    except Exception:
        return False


def _hermetic_cfg(tmp_path):
    """Live Ollama, hermetic stores. The always-on daemon holds the single-writer DuckDB
    lock on data/telemetry.duckdb — and a test must never write production telemetry
    anyway. Only the model channel is shared; every path points at tmp."""
    base = get_config()
    paths = dataclasses.replace(base.paths, data_dir=tmp_path,
                                telemetry_db=tmp_path / "telemetry.duckdb",
                                raw_store=tmp_path / "raw",
                                vector_store=tmp_path / "v.lance",
                                vault_catalog=tmp_path / "cat.sqlite",
                                derived_store=tmp_path / "d.sqlite",
                                attestation_store=tmp_path / "att.sqlite")
    return dataclasses.replace(base, paths=paths)


@pytest.mark.skipif(not _ollama_up(), reason="Ollama not running on loopback")
def test_model_responds_through_sealed_core(tmp_path):
    core = runtime.bootstrap(_hermetic_cfg(tmp_path))  # seals the process, then wires services
    assert len(core.constitution_fingerprint) == 64
    # Through the LOADER's client, not the ModelServer's: `list_models` is a residency-manager
    # operation, deliberately off the inference protocol (bp-115 §3 Q1 — llama.cpp has no
    # counterpart). Same object at runtime; do not "simplify" this back (finding-0205).
    if PINNED not in core.models.loader.client.list_models():
        pytest.skip(f"{PINNED} not pulled")
    agent = core.make_agent("trivial", "You are a terse Phase 0 test agent.", tier="router")
    out, check = agent.respond("Reply with exactly the word: ready", think=False)
    assert out.strip()           # the sealed core reached the LOCAL model and got text
    assert check.passed
    assert PINNED in core.models.loader.resident_models()
