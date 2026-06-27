"""Live gate: a model responds through the sealed core (requires Ollama + pulled model).

Marked `live` and skipped automatically when Ollama is down or the pinned model is not
pulled. Run with: pytest -m live
"""

import pytest

from core import runtime
from core.models import build_model_server

pytestmark = pytest.mark.live

PINNED = "qwen3.5:2b"


def _ollama_up() -> bool:
    try:
        return bool(build_model_server().version())
    except Exception:
        return False


@pytest.mark.skipif(not _ollama_up(), reason="Ollama not running on loopback")
def test_model_responds_through_sealed_core():
    core = runtime.bootstrap()  # seals the process, then wires services
    assert len(core.constitution_fingerprint) == 64
    if PINNED not in core.models.client.list_models():
        pytest.skip(f"{PINNED} not pulled")
    agent = core.make_agent("trivial", "You are a terse Phase 0 test agent.", tier="router")
    out, check = agent.respond("Reply with exactly the word: ready", think=False)
    assert out.strip()           # the sealed core reached the LOCAL model and got text
    assert check.passed
    assert PINNED in core.models.loader.resident_models()
