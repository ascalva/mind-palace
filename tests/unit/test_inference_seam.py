"""The backend-agnostic inference seam (bp-115 / `dn-local-model-runtime` §2.6 P1).

P1's acceptance bar is that **nothing observable changes**: every later phase's rollback story
is "flip the config back", which is only true if the seam itself is a pure refactor. These tests
hold that line from four directions — the protocol is read OFF the working client, the widened
annotations stay strictly permissive, the second client speaks the measured wire contract, and
the `[runtime]` section survives the overlay that silently drops unknown sections.

⚑ **One test here is RED pending finding-0200** — `test_ollama_client_satisfies_the_protocol`.
`OllamaClient` needs a three-line `healthy()`, and it lives in `core/models/ollama_client.py`,
which bp-115's `write_scope` does not contain; the finding carries the exact patch. It is written
as a real assertion rather than skipped because it IS §7 Item 1's acceptance criterion, and a
skipped ratchet is not a ratchet. The same gap shows up statically as two mypy `[return-value]` /
`[arg-type]` errors, which no runtime test can see (`isinstance(x, OllamaClient)` is nominal and
passes either way) — that asymmetry is itself worth knowing: the protocol is a STATIC contract
first, and the runtime check is only its shallow shadow.

The llama-server tests run against a STUB HTTP server this module starts on 127.0.0.1 (plan §7
Item 3 sanctions the stub when no binary is configured). What the stub can prove is the client's
half of the contract — request shape, response decoding, error typing, readiness semantics. What
it cannot prove is that a real build behaves as `dn-local-model-runtime` §2.1 G measured; that is
the equivalence harness's job (P3/bp-117), and the chat path additionally cannot be exercised
against a real model at all until upstream-convention GGUFs land (V-B, §2.1 E).
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest

from config.loader import load_config
from core.ingest.embed import Embedder, build_embedder
from core.kernel.config import Config
from core.kernel.config import loader as config_loader
from core.kernel.config.loader import RuntimeConfig
from core.models.inference import InferenceClient, build_inference_client
from core.models.llama_server_client import (
    LOOPBACK_HOST,
    ContextOverflowError,
    LlamaServerClient,
    LlamaServerError,
)
from core.models.ollama_client import Message, OllamaClient

REPO_ROOT = Path(__file__).resolve().parents[2]

# ---------------------------------------------------------------------------------------
# Item 1 — the protocol, and the existing client fits it
# ---------------------------------------------------------------------------------------


def _needs_an_inference_client(client: InferenceClient) -> InferenceClient:
    """A statically-typed hole shaped exactly like every real call site. Passing a concrete
    client through it is what makes mypy check the conformance; the runtime assertions below
    are the shallow companion (`runtime_checkable` sees method NAMES, never signatures)."""
    return client


class _MinimalClient:
    """Exactly the three protocol members and nothing else — the structural ratchet for §3 Q1.

    If `ps`/`load`/`unload`/`list_models` ever creep onto `InferenceClient`, this stops
    satisfying it and the test below goes red. That is the whole point: those are
    residency-MANAGER operations with no llama.cpp counterpart, and a protocol demanding them
    would force one implementation to lie four times.
    """

    def embed(self, model: str, inputs: list[str], *,
              keep_alive: str | int | None = None) -> list[list[float]]:
        return [[0.0] for _ in inputs]

    def chat(self, model: str, messages: list[Message], *,
             num_ctx: int | None = None, temperature: float | None = None,
             keep_alive: str | int | None = None, think: bool | None = None) -> str:
        return ""

    def healthy(self) -> bool:
        return True


def test_ollama_client_satisfies_the_protocol():
    """§7 Item 1's acceptance: `OllamaClient` fits where `InferenceClient` is required, with no
    edit to any existing method body. RED pending finding-0200 (`healthy()` is out of scope)."""
    client = OllamaClient(load_config().ollama)
    assert isinstance(client, InferenceClient)
    assert _needs_an_inference_client(client) is client


def test_llama_server_client_satisfies_the_protocol():
    client = LlamaServerClient()
    assert isinstance(client, InferenceClient)
    assert _needs_an_inference_client(client) is client


def test_the_protocol_demands_nothing_beyond_chat_embed_health():
    """§3 Q1: manager operations stay OFF the seam."""
    assert isinstance(_MinimalClient(), InferenceClient)
    assert _needs_an_inference_client(_MinimalClient()) is not None


def test_manager_operations_are_absent_from_the_protocol():
    for manager_op in ("ps", "load", "unload", "list_models", "version"):
        assert not hasattr(InferenceClient, manager_op), (
            f"{manager_op!r} is a residency-manager operation (§3 Q1) and must not be on the "
            "inference seam — llama.cpp has no counterpart for it"
        )


# ---------------------------------------------------------------------------------------
# Item 2 — the widening is strictly permissive
# ---------------------------------------------------------------------------------------


def test_embedder_public_surface_is_unchanged():
    """§6: 30+ test files and every ingest lane depend on this surface. Widening the `client`
    ANNOTATION must not perturb it."""
    public = {name for name in vars(Embedder) if not name.startswith("_")}
    assert public == {"dim", "embed_documents", "embed_query"}
    assert set(Embedder.__dataclass_fields__) == {"client", "config"}


def test_a_bare_duck_typed_client_still_builds_an_embedder():
    """The permissiveness claim, exercised: a stub that satisfies only the protocol is enough,
    which is why none of the 30+ existing `Embedder(`/`build_embedder` sites needed editing."""
    embedder = Embedder(client=_MinimalClient(), config=load_config().embedding)
    assert embedder.embed_documents(["a", "b"]) == [[0.0], [0.0]]
    assert embedder.embed_documents([]) == []
    assert embedder.dim == load_config().embedding.dim


# ---------------------------------------------------------------------------------------
# Item 3 — LlamaServerClient against a stub speaking the measured wire contract
# ---------------------------------------------------------------------------------------

_EMBED_DIM = 2560  # the measured dimensionality of the portable embedder blob (§2.1 E/F)


class _StubServer(ThreadingHTTPServer):
    """A 127.0.0.1 stand-in for llama-server. `routes` maps a path to (status, body); `seen`
    records what the client actually put on the wire, which is the half of the contract a stub
    CAN prove."""

    routes: dict[str, tuple[int, dict[str, Any]]]
    seen: list[tuple[str, str, dict[str, Any] | None]]


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _reply(self, path: str) -> None:
        assert isinstance(self.server, _StubServer)
        status, payload = self.server.routes[path]
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        assert isinstance(self.server, _StubServer)
        self.server.seen.append(("GET", self.path, None))
        self._reply(self.path)

    def do_POST(self) -> None:
        assert isinstance(self.server, _StubServer)
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        self.server.seen.append(("POST", self.path, json.loads(raw or b"{}")))
        self._reply(self.path)

    def log_message(self, format: str, *args: Any) -> None:
        """Silence the per-request stderr line; the test asserts on `seen`, not on logs."""


@pytest.fixture
def stub() -> Any:
    server = _StubServer((LOOPBACK_HOST, 0), _Handler)
    server.routes = {}
    server.seen = []
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def _client(stub: _StubServer) -> LlamaServerClient:
    return LlamaServerClient(port=stub.server_address[1], request_timeout_s=5.0,
                             generation_timeout_s=5.0)


def _vec(seed: float) -> list[float]:
    return [seed + i * 1e-6 for i in range(_EMBED_DIM)]


def test_embeddings_decode_the_openai_shape_and_preserve_order(stub: _StubServer):
    """`/v1/embeddings` — measured working (§2.1 G). Order preservation is a contract the
    corpus depends on, so the response is ordered by the server's own `index`, deliberately
    NOT by arrival order."""
    stub.routes["/v1/embeddings"] = (200, {"data": [
        {"embedding": _vec(2.0), "index": 1},   # deliberately out of order
        {"embedding": _vec(1.0), "index": 0},
    ]})
    vectors = _client(stub).embed("qwen3-embedding:4b", ["first", "second"])
    assert [len(v) for v in vectors] == [_EMBED_DIM, _EMBED_DIM]
    assert vectors[0][0] == 1.0 and vectors[1][0] == 2.0
    method, path, body = stub.seen[-1]
    assert (method, path) == ("POST", "/v1/embeddings")
    assert body == {"model": "qwen3-embedding:4b", "input": ["first", "second"]}


def test_health_reflects_the_503_to_200_transition(stub: _StubServer):
    """§2.1 G: llama-server answers /health with 503 WHILE LOADING and 200 once ready. This is
    the state a version string cannot express, and the reason `healthy()` exists."""
    stub.routes["/health"] = (503, {"error": {"message": "Loading model"}})
    client = _client(stub)
    assert client.healthy() is False
    stub.routes["/health"] = (200, {"status": "ok"})
    assert client.healthy() is True


def test_health_is_false_when_nothing_is_listening():
    """A readiness probe that raises is one every caller has to wrap. Port 1 on loopback has
    no listener; the seal permits the attempt (loopback) and the connection is refused."""
    assert LlamaServerClient(port=1, request_timeout_s=2.0).healthy() is False


def test_context_overflow_surfaces_typed_not_flattened(stub: _StubServer):
    """⚑ §7 Item 3's named falsifier: *the typed error is flattened into a generic message.*

    §2.1 G names typed JSON errors as one of the concrete wins over Ollama's opaque strings.
    Both numbers must survive AS NUMBERS — a caller that has to regex a message string has been
    handed the Ollama experience under a new name.
    """
    stub.routes["/v1/embeddings"] = (400, {"error": {
        "code": 400,
        "type": "exceed_context_size_error",
        "message": "the request exceeds the available context size, try increasing it",
        "n_prompt_tokens": 9001,
        "n_ctx": 8192,
    }})
    with pytest.raises(ContextOverflowError) as excinfo:
        _client(stub).embed("qwen3-embedding:4b", ["x" * 100_000])
    err = excinfo.value
    assert err.n_prompt_tokens == 9001
    assert err.n_ctx == 8192
    assert isinstance(err, LlamaServerError)          # one catchable family
    assert "exceeds the available context size" in str(err)


def test_an_untyped_error_body_degrades_to_the_generic_error(stub: _StubServer):
    """Defensive, not overclaiming: a build whose error shape differs must still fail loudly
    rather than crash inside error handling or be mistaken for a context overflow."""
    stub.routes["/v1/embeddings"] = (500, {"unexpected": "shape"})
    with pytest.raises(LlamaServerError) as excinfo:
        _client(stub).embed("m", ["x"])
    assert not isinstance(excinfo.value, ContextOverflowError)


def test_chat_speaks_the_openai_wire_contract(stub: _StubServer):
    """⚑ WIRE CONTRACT ONLY. §2.1 E: Ollama's chat blobs (arch `qwen35`) fail to load in
    upstream llama-server, so this path has never been exercised against a real model. Claiming
    otherwise would be a false completion claim (§7 Item 3's second falsifier). Re-entry: V-B.
    """
    stub.routes["/v1/chat/completions"] = (200, {
        "choices": [{"message": {"role": "assistant", "content": "hello"}}]
    })
    messages: list[Message] = [{"role": "user", "content": "hi"}]
    reply = _client(stub).chat("qwen3.5:2b", messages, num_ctx=8192, temperature=0.2,
                               keep_alive="30m", think=False)
    assert reply == "hello"
    _, path, body = stub.seen[-1]
    assert path == "/v1/chat/completions"
    assert body is not None
    assert body["stream"] is False                    # §11: the palace is non-streaming
    assert body["messages"] == messages
    assert body["temperature"] == 0.2
    assert body["chat_template_kwargs"] == {"enable_thinking": False}
    # num_ctx is fixed at spawn (`-c`), keep_alive is an Ollama residency timer — neither has a
    # per-request meaning here, so neither may be smuggled onto the wire.
    assert "num_ctx" not in body and "keep_alive" not in body and "options" not in body


def test_chat_with_no_choices_returns_empty(stub: _StubServer):
    stub.routes["/v1/chat/completions"] = (200, {"choices": []})
    assert _client(stub).chat("m", []) == ""


def test_the_client_binds_a_loopback_literal_and_never_spawns():
    """Two invariants from §7 Item 3, as a source-level ratchet rather than a convention.

    A hostname would mean a DNS lookup, which is the one thing the `127.0.0.1` literal buys us
    (§2.4). A client that spawned would hold two responsibilities and break the
    argv-as-capability story the process manager (bp-116) rests on.
    """
    assert LOOPBACK_HOST == "127.0.0.1"
    assert LlamaServerClient().base_url == "http://127.0.0.1:8080"
    source = (REPO_ROOT / "core" / "models" / "llama_server_client.py").read_text("utf-8")
    for spawner in ("import subprocess", "subprocess.", "os.fork", "os.spawn", "Popen"):
        assert spawner not in source, f"the client must never spawn a server (found {spawner!r})"


# ---------------------------------------------------------------------------------------
# Item 4 — the [runtime] section and the per-role selector
# ---------------------------------------------------------------------------------------


def test_runtime_section_survives_the_local_overlay(tmp_path: Path, monkeypatch: Any):
    """⚑ §7 Item 4's named falsifier: *a `[runtime]` key in `local.toml` is silently ignored.*

    That is finding-0174's exact mechanism — `_overlay` merges by SECTION NAME and `Config` had
    no catch-all, so a section with no dataclass behind it vanished. Constructing
    `RuntimeConfig()` directly would pass while the overlay path stayed broken, so this drives
    the REAL path: `load_config()` with no argument, with both overlay files redirected into
    tmp_path (the owner's actual local.toml must not be able to affect the assertions).
    """
    local = tmp_path / "local.toml"
    local.write_text(
        "[runtime]\n"
        'embedding_backend = "llamacpp"\n'
        'server_binary = "/opt/homebrew/bin/llama-server"\n'
        'pinned_build = "b10090"\n'
        "embed_ctx = 4096\n"
        "grace_s = 9.5\n"
        "\n"
        "[runtime.chat_backend]\n"
        'router = "llamacpp"\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(config_loader, "_LOCAL", local)
    monkeypatch.setattr(config_loader, "LEVERS_OVERLAY", tmp_path / "absent-levers.toml")

    runtime = config_loader.load_config().runtime
    assert runtime.embedding_backend == "llamacpp"
    assert runtime.chat_backend == {"router": "llamacpp"}
    assert runtime.server_binary == "/opt/homebrew/bin/llama-server"
    assert runtime.pinned_build == "b10090"
    assert runtime.embed_ctx == 4096
    assert runtime.grace_s == 9.5


def test_shipped_defaults_are_todays_behaviour():
    """No flip is performed here — flipping is the owner's, per role, at P4/P5 (§9)."""
    runtime = load_config().runtime
    assert runtime.embedding_backend == "ollama"
    assert runtime.chat_backend == {}
    assert runtime.server_binary == ""      # nothing is configured to spawn
    assert runtime.embed_ctx == 8192        # §2.3, down from the model default 40960
    assert runtime.grace_s == 5.0


def test_an_unlisted_tier_stays_on_ollama():
    runtime = RuntimeConfig(chat_backend={"router": "llamacpp"})
    assert runtime.chat_backend_for("router") == "llamacpp"
    assert runtime.chat_backend_for("synthesis") == "ollama"


def _with_runtime(runtime: RuntimeConfig) -> Config:
    import dataclasses

    return dataclasses.replace(load_config(), runtime=runtime)


def test_the_default_backend_is_ollama_backed():
    """§7 Item 4: with defaults, every behaviour is identical to before bp-115. Green at
    runtime; the STATIC half of this claim is the `[return-value]` error finding-0200 carries."""
    assert isinstance(build_inference_client(load_config()), OllamaClient)
    assert isinstance(build_embedder().client, OllamaClient)


def test_the_embedding_role_selects_llamacpp_independently():
    """Per ROLE, not global — that is what makes the embedder cutover (P4) independently
    reversible while every chat tier stays on Ollama."""
    config = _with_runtime(RuntimeConfig(embedding_backend="llamacpp"))
    assert isinstance(build_inference_client(config), LlamaServerClient)
    assert isinstance(build_embedder(config).client, LlamaServerClient)
    assert isinstance(build_inference_client(config, tier="synthesis"), OllamaClient)


def test_a_chat_tier_selects_llamacpp_independently():
    config = _with_runtime(RuntimeConfig(chat_backend={"router": "llamacpp"}))
    assert isinstance(build_inference_client(config, tier="router"), LlamaServerClient)
    assert isinstance(build_inference_client(config, tier="routine"), OllamaClient)


def test_an_unknown_backend_refuses_rather_than_defaulting():
    """Fail loudly. A typo in local.toml that silently fell back to Ollama would reproduce the
    class of bug this whole section exists to end."""
    config = _with_runtime(RuntimeConfig(embedding_backend="mlx"))
    with pytest.raises(ValueError, match="mlx"):
        build_inference_client(config)
