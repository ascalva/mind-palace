"""Live gate: the supervisor dispatches a real job through the two-slot loader + Ollama
(BUILD-SPEC §13). Uses the pinned tiny model (already warm). Run: pytest -m live."""

import pytest

from config.loader import get_config
from core.models import build_model_server
from core.models.ollama_client import OllamaClient
from scheduler.presence import Presence
from scheduler.queue import DONE, JobQueue
from scheduler.supervisor import Supervisor

pytestmark = pytest.mark.live


def _pinned_present() -> bool:
    try:
        cfg = get_config()
        return cfg.pinned_model.name in OllamaClient(cfg.ollama).list_models()
    except Exception:
        return False


@pytest.mark.skipif(not _pinned_present(), reason="pinned model not pulled")
def test_supervisor_dispatches_a_real_job(tmp_path):
    cfg = get_config()
    # Clean slate: free any models left warm by prior live tests so Ollama isn't mid-swap
    # when we dispatch (otherwise a cold generation can queue behind a load and time out).
    client = OllamaClient(cfg.ollama)
    for name in client.ps():
        client.unload(name)

    server = build_model_server(cfg)
    captured = {}

    def handler(_job):
        text = server.chat("router", [{"role": "user", "content": "Reply with one word: ready"}])
        captured["text"] = text
        return text

    sup = Supervisor(
        queue=JobQueue(tmp_path / "q.db"),
        loader=server.loader,
        handlers={"ping": handler},
        presence=Presence(idle_probe=lambda: 10_000.0),  # idle => nothing gated
    )
    j = sup.queue.enqueue("ping", "router", cfg.pinned_model.num_ctx)
    assert sup.run() == 1
    job = sup.queue.get(j.id)
    assert job.state == DONE, f"job did not complete: {job.error}"
    assert captured["text"].strip()
