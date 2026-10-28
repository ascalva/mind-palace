"""The llama.cpp cutover on an instance (owner ruling 2026-10-28: "we now use llama cpp").

With every chat tier flipped to `llamacpp`, Ollama must never be asked to load, evict or answer:
the two-slot discipline becomes the server topology (one chat server + one embedder). These pin the
four seams that previously reached Ollama unconditionally — the loader, the model server's chat,
preflight, and the reset set — plus the `[dreaming] scheduled` lever.
"""

from __future__ import annotations

import dataclasses
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, cast

import pytest

from config.loader import Config, load_config
from core.kernel.config.loader import RuntimeConfig
from core.models.llama_server_client import LOOPBACK_HOST
from core.models.loader import TwoSlotLoader
from core.models.ollama_client import OllamaClient
from core.models.registry import Registry
from core.models.server import ModelServer
from ops.lifecycle.preflight import check_ollama
from tests.unit.test_loader_reconcile import FakeOllama

TIERS = ("router", "routine", "synthesis", "stretch")


def _all_llamacpp(**ports: int) -> Config:
    runtime = RuntimeConfig(embedding_backend="llamacpp",
                            chat_backend={t: "llamacpp" for t in TIERS}, ports=dict(ports))
    return dataclasses.replace(load_config(), runtime=runtime)


def test_a_llamacpp_tier_never_asks_ollama_to_load_or_evict():
    fake = FakeOllama()
    loader = TwoSlotLoader(config=_all_llamacpp(), client=cast(OllamaClient, fake),
                           registry=Registry(load_config()))
    assert loader.ensure_tier("synthesis").tier == "synthesis"
    assert loader.ensure_pinned().pinned
    assert fake.loads == [] and fake.unloads == []


def test_an_ollama_tier_still_goes_through_the_loader():
    """The flip is per role: an instance that flips some tiers keeps the old path for the rest."""
    runtime = RuntimeConfig(chat_backend={"synthesis": "llamacpp"})
    cfg = dataclasses.replace(load_config(), runtime=runtime)
    fake = FakeOllama()
    loader = TwoSlotLoader(config=cfg, client=cast(OllamaClient, fake), registry=Registry(cfg))
    loader.ensure_tier("routine")
    assert fake.loaded_names() == [cfg.model_for_tier("routine").name]


class _Recorder:
    def __init__(self) -> None:
        self.calls: list[tuple[str, Any]] = []

    def chat(self, model: str, messages: list[Any], **kw: Any) -> str:
        self.calls.append((model, kw))
        return "ok"


def test_model_server_sends_a_llamacpp_tier_to_its_own_server(monkeypatch: pytest.MonkeyPatch):
    cfg = _all_llamacpp(synthesis=8080)
    built: list[tuple[str | None, _Recorder]] = []

    def fake_build(config: Config, *, tier: str | None = None) -> _Recorder:
        rec = _Recorder()
        built.append((tier, rec))
        return rec

    monkeypatch.setattr("core.models.inference.build_inference_client", fake_build)
    ollama = FakeOllama()
    server = ModelServer(config=cfg, client=cast(Any, _Recorder()),
                         loader=TwoSlotLoader(config=cfg, client=cast(OllamaClient, ollama),
                                              registry=Registry(cfg)))
    assert server.chat("synthesis", [{"role": "user", "content": "hi"}], think=False) == "ok"
    (tier, rec), = built
    assert tier == "synthesis" and rec.calls[0][1]["think"] is False
    assert "num_ctx" not in rec.calls[0][1] and "keep_alive" not in rec.calls[0][1]
    assert ollama.loads == []


class _Health(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self.send_response(200 if self.path == "/health" else 404)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def log_message(self, format: str, *args: Any) -> None:
        pass


@pytest.fixture
def health_port() -> Any:
    server = ThreadingHTTPServer((LOOPBACK_HOST, 0), _Health)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server.server_address[1]
    server.shutdown()
    server.server_close()


def test_preflight_checks_llama_servers_not_ollama_when_no_role_uses_ollama(health_port: int):
    cfg = _all_llamacpp(embedding=health_port, **{t: health_port for t in TIERS})
    check = check_ollama(cfg)
    assert check.name == "inference" and check.ok and check.required


def test_preflight_fails_closed_when_a_llama_server_is_down(health_port: int):
    with ThreadingHTTPServer((LOOPBACK_HOST, 0), _Health) as probe:
        dead = probe.server_address[1]          # bound then closed: nothing listens there
    cfg = _all_llamacpp(embedding=health_port, **{t: dead for t in TIERS})
    check = check_ollama(cfg)
    assert check.required and not check.ok and f":{dead}" in check.detail


def test_dreaming_is_scheduled_by_default_and_the_lever_parses():
    assert load_config().dreaming.scheduled is True


def test_reset_targets_include_the_membership_store(tmp_path: Path):
    """bp-152's relation points into the vector plane; a reset that kept it would leave
    occupancies of atoms that no longer exist."""
    from ops.lifecycle.launcher import Launcher
    from ops.lifecycle.runs import RunLedger

    class _Paths:
        def __init__(self, d: Path) -> None:
            self.data_dir = d
            self.raw_store = d / "raw"
            self.vector_store = d / "vectors.lance"
            self.vault_catalog = d / "vault_catalog.sqlite"
            self.derived_store = d / "derived.sqlite"
            self.attestation_store = d / "attestations.sqlite"

    class _Cfg:
        def __init__(self, d: Path) -> None:
            self.paths = _Paths(d)

    launcher = Launcher(cfg=cast(Config, _Cfg(tmp_path / "data")),
                        runs=cast(RunLedger, None), repo_root=tmp_path)
    assert "memberships.sqlite" in {t.name for t in launcher.reset_targets()}
