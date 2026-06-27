"""Live gate: a minted agent inherits the Constitution, responds, and self-evaluates
(BUILD-SPEC §10). Run: pytest -m live."""

import pytest

from config.loader import get_config
from core.factory import AgentFactory, build_default_registry
from core.models import build_model_server
from core.models.ollama_client import OllamaClient

pytestmark = pytest.mark.live


def _routine_present() -> bool:
    try:
        cfg = get_config()
        return cfg.model_for_tier("routine").name in OllamaClient(cfg.ollama).list_models()
    except Exception:
        return False


@pytest.mark.skipif(not _routine_present(), reason="routine model not pulled")
def test_minted_agent_responds_and_self_evaluates():
    cfg = get_config()
    factory = AgentFactory(server=build_model_server(cfg), tools=build_default_registry(None))
    agent = factory.mint("general_conversation")
    text, check = agent.respond("In one sentence, what is a mind palace?")
    assert text.strip()
    assert check.passed                # advisory answer; grounding N/A, subjective deferred
