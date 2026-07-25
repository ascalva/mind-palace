"""Thin HTTP client for a LOCAL `llama-server` (`dn-local-model-runtime` §2.6 P1).

The second implementation of `core.models.inference.InferenceClient`. It speaks the
OpenAI-compatible surface upstream llama.cpp exposes — `/v1/chat/completions`, `/v1/embeddings`,
`/health` — measured working on b10090 (7347430f4), note §2.1 G, not read from documentation.

Stdlib-only by design, exactly as `core/models/ollama_client.py:3-6` states the rule for the
Ollama channel: the sealed core must not import a network-capable third-party package
(CONVENTIONS). `urllib` is network-capable, but every request here targets a `127.0.0.1`
LITERAL — never a hostname, so no DNS is involved — and the egress guard (`core.sealing`) permits
exactly that and blocks everything else. `core/models/inference.py` states this as a property of
the seam; this file is the second audited exception in `ops/import_lint.py`'s allowlist.

⚑ **This client never spawns a server.** Spawning, readiness-gating, the budget check and the
SIGTERM→grace→SIGKILL stop are the *process manager*'s (note §2.4; bp-116). A client that also
spawned would hold two responsibilities and would break the argv-as-capability story that makes
the spawned server's egress a tier-2 claim. It connects to a port someone else is listening on.

⚑ **Typed errors are kept typed.** llama-server answers a too-long prompt with structured JSON
(`exceed_context_size_error` carrying `n_prompt_tokens` and `n_ctx`) rather than Ollama's opaque
string. That is one of the named concrete wins of the migration (note §2.1 G); flattening it into
a generic message at this boundary would throw away part of the reason for migrating. It surfaces
as `ContextOverflowError`, which carries both numbers as attributes.

⚑ **What is NOT verified here.** Ollama's chat blobs (`qwen3.5:2b/9b`, `qwen3.6:27b`, GGUF arch
`qwen35`) FAIL to load in upstream llama-server (`key qwen35.rope.dimension_sections has wrong
array length; expected 4, got 3` — note §2.1 E). The chat path is therefore exercised against the
WIRE CONTRACT only, never against a loaded chat model; claiming otherwise would be a false
completion claim (plan §7 Item 3 falsifier). Only the embedder blob is portable, and its
cross-runtime cosine floor was measured at 0.999990 (§2.1 F). Real chat verification re-enters at
V-B, when upstream-convention GGUFs are placed.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, cast

from core.kernel.constitution import Message

# llama-server's own default listen port. Kept as a default rather than a `[runtime]` config key
# because ports are per-PROCESS and the note's residency model is three concurrent servers
# (router / worker / embedder, §2.3) — assigning them is the process manager's job (bp-116), which
# passes an explicit port here. Until a role is flipped this default is only ever reached by a
# test or by an owner-launched server, and the default stays `ollama` for every role (plan §9).
DEFAULT_PORT = 8080

# The loopback literal. Never a hostname: the seal permits the literal precisely because no name
# resolution — hence no external lookup — can occur (note §2.4).
LOOPBACK_HOST = "127.0.0.1"


class LlamaServerError(RuntimeError):
    """Any failure talking to the local llama-server."""


class ContextOverflowError(LlamaServerError):
    """The prompt did not fit the server's loaded context window.

    llama-server's context is fixed at spawn (`-c`), so this is a LOUD, fail-closed signal that
    the window was sized wrong for the traffic — which is exactly why note §2.3 right-sizes the
    embedder to 8192 and asks V-D to confirm no embed call can exceed it. The server's own
    numbers are carried as attributes, not flattened into prose.
    """

    def __init__(self, message: str, *, n_prompt_tokens: int | None = None,
                 n_ctx: int | None = None) -> None:
        super().__init__(message)
        self.n_prompt_tokens = n_prompt_tokens
        self.n_ctx = n_ctx


def _as_int(value: Any) -> int | None:
    """The server's numbers, defensively: absent or non-numeric becomes None rather than a
    crash inside error handling (a parse failure while reporting a failure is the worst place
    to raise). warrant(T3): the JSON boundary is untyped by nature."""
    return value if isinstance(value, int) else None


def _typed_error(path: str, status: int, body: bytes) -> LlamaServerError:
    """Map llama-server's structured error body to a specific, catchable exception.

    Shape (note §2.1 G): `{"error": {"type": "...", "message": "...", "n_prompt_tokens": N,
    "n_ctx": M}}`. Both nestings are probed because the field placement is a property of a build
    we pin but do not own; an unparseable body degrades to the generic error rather than masking
    the failure.
    """
    try:
        # warrant(T3): static types end at the JSON boundary; a local server's error body is
        # trusted only as far as the isinstance checks below (runtime validation is PD-2).
        parsed = json.loads(body)
    except (ValueError, TypeError):
        parsed = None
    err = parsed.get("error") if isinstance(parsed, dict) else None
    if not isinstance(err, dict):
        err = parsed if isinstance(parsed, dict) else {}
    message = str(err.get("message") or f"{path} failed with HTTP {status}")
    if err.get("type") == "exceed_context_size_error":
        return ContextOverflowError(
            message,
            n_prompt_tokens=_as_int(err.get("n_prompt_tokens")),
            n_ctx=_as_int(err.get("n_ctx")),
        )
    return LlamaServerError(f"{path} failed (HTTP {status}): {message}")


@dataclass
class LlamaServerClient:
    """An `InferenceClient` over one local llama-server process.

    One server serves ONE model (note §2.1 D: even Ollama is really N single-model servers behind
    a manager), so `model` is passed through for wire compatibility but does not select anything.
    """

    port: int = DEFAULT_PORT
    host: str = LOOPBACK_HOST
    request_timeout_s: float = 120.0      # control-plane ops (health, embed) — fail fast
    generation_timeout_s: float = 600.0   # chat generation — a heavy tier legitimately runs minutes

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    # --- transport ------------------------------------------------------------------
    def _post(self, path: str, payload: dict[str, Any], *,
              timeout: float | None = None) -> dict[str, Any]:
        req = urllib.request.Request(
            f"{self.base_url}{path}",
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(
                req, timeout=timeout or self.request_timeout_s
            ) as resp:
                # warrant(T3): static types end at the JSON boundary; the local server's
                # response shape is trusted here (runtime validation is PD-2).
                return cast("dict[str, Any]", json.loads(resp.read()))
        except urllib.error.HTTPError as e:
            # HTTPError carries the RESPONSE BODY, which is where the typed error lives. Read it
            # before it is discarded — this is the branch that keeps `n_ctx`/`n_prompt_tokens`.
            raise _typed_error(path, e.code, e.read()) from e
        except urllib.error.URLError as e:
            raise LlamaServerError(f"POST {path} failed: {e}") from e

    # --- readiness ------------------------------------------------------------------
    def healthy(self) -> bool:
        """`/health`: 503 while the model loads → 200 when ready (measured, note §2.1 G).

        Returns False rather than raising for BOTH not-ready states — still loading (503) and
        nothing listening (connection refused) — because a readiness probe that throws is a
        readiness probe every caller has to wrap. "Up but not ready" is the state a version
        string could not express, and it is the reason this method exists at all.
        """
        try:
            with urllib.request.urlopen(
                f"{self.base_url}/health", timeout=self.request_timeout_s
            ) as resp:
                return bool(200 <= resp.status < 300)
        except urllib.error.HTTPError:
            return False          # 503 while loading — the documented not-ready signal
        except urllib.error.URLError:
            return False          # not listening at all

    # --- embeddings -----------------------------------------------------------------
    def embed(self, model: str, inputs: list[str], *,
              keep_alive: str | int | None = None) -> list[list[float]]:
        """Batch-embed `inputs` via `/v1/embeddings`. One vector per input, order preserved.

        `keep_alive` is accepted for protocol compatibility and DELIBERATELY IGNORED: it is an
        Ollama residency knob (how long a third party's timer keeps a model warm). Here residency
        is process existence — the model is loaded because we hold the process, and no timer can
        evict it (note §2.3). Silently honoring it would be a lie; erroring on it would break the
        seam. The whole batch goes in one request, as the Ollama client does; client-side batch
        sizing for cancellation granularity is V-E, not this plan's.
        """
        payload: dict[str, Any] = {"model": model, "input": inputs}
        data = self._post("/v1/embeddings", payload)
        # OpenAI shape: {"data": [{"embedding": [...], "index": 0}, ...]}. `index` is respected
        # rather than assumed — order preservation is a contract this client owes its callers,
        # and the embedder's vectors are the one thing P1 must not perturb.
        # warrant(T3): chained .get over Any; trusted local JSON boundary (PD-2).
        rows = cast("list[dict[str, Any]]", data.get("data", []))
        ordered = sorted(rows, key=lambda r: cast(int, r.get("index", 0)))
        return [cast("list[float]", r.get("embedding", [])) for r in ordered]

    # --- inference ------------------------------------------------------------------
    def chat(self, model: str, messages: list[Message], *,
             num_ctx: int | None = None, temperature: float | None = None,
             keep_alive: str | int | None = None, think: bool | None = None) -> str:
        """Single-shot, non-streaming chat via `/v1/chat/completions`.

        ⚑ Wire-contract only — see the module docstring: no upstream-loadable chat blob exists
        yet (§2.1 E), so this path has never been exercised against a real model.

        `num_ctx` is accepted and IGNORED because llama-server fixes its window at spawn (`-c`);
        the process manager sizes it per role (§2.3). That is not a silent truncation: a prompt
        over the window comes back as a typed `ContextOverflowError` carrying both numbers, which
        is louder than Ollama's per-request reload. `keep_alive` is ignored for the reason given
        on `embed`. `think` maps to llama.cpp's `chat_template_kwargs.enable_thinking` (the Qwen3
        hybrid-thinking toggle); that mapping is UNVERIFIED against a loaded model and re-enters
        at V-B with the upstream GGUFs.
        """
        payload: dict[str, Any] = {"model": model, "messages": messages, "stream": False}
        if temperature is not None:
            payload["temperature"] = temperature
        if think is not None:
            payload["chat_template_kwargs"] = {"enable_thinking": think}
        data = self._post(
            "/v1/chat/completions", payload, timeout=self.generation_timeout_s
        )
        # warrant(T3): chained .get over Any; trusted local JSON boundary (PD-2).
        choices = cast("list[dict[str, Any]]", data.get("choices", []))
        if not choices:
            return ""
        return cast(str, choices[0].get("message", {}).get("content", ""))
