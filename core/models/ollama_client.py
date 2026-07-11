"""Thin HTTP client for the LOCAL Ollama server (BUILD-SPEC §7).

Stdlib-only by design: the sealed core must not import a network-capable third-party
package (CONVENTIONS). `urllib` is network-capable, but every request here targets the
loopback Ollama endpoint, and the egress guard (`core.sealing`) permits exactly that
and blocks everything else. Personas and per-call parameters are injected at REQUEST
time via this API — never baked into a Modelfile (CONVENTIONS / BUILD-SPEC §5).
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, TypedDict, cast

from config.loader import OllamaConfig


class Message(TypedDict):
    """One chat turn, Ollama chat-API shaped. Deliberately duplicated from
    `core.constitution.Message` (structurally identical, so mypy treats them as
    interchangeable) to keep this client standalone; runtime-identical to the
    plain dict it replaced."""

    role: str  # "system" | "user" | "assistant"
    content: str


class OllamaError(RuntimeError):
    """Any failure talking to the local Ollama server."""


@dataclass
class OllamaClient:
    config: OllamaConfig

    def _post(self, path: str, payload: dict[str, Any], *,
              timeout: float | None = None) -> dict[str, Any]:
        req = urllib.request.Request(
            f"{self.config.base_url}{path}",
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(
                req, timeout=timeout or self.config.request_timeout_s
            ) as resp:
                # warrant(T3): static types end at the JSON boundary; the local Ollama
                # server's response shape is trusted here (runtime validation is PD-2).
                return cast("dict[str, Any]", json.loads(resp.read()))
        except urllib.error.URLError as e:
            raise OllamaError(f"POST {path} failed: {e}") from e

    def _get(self, path: str) -> dict[str, Any]:
        try:
            with urllib.request.urlopen(
                f"{self.config.base_url}{path}", timeout=self.config.request_timeout_s
            ) as resp:
                # warrant(T3): as _post — trusted local JSON boundary (PD-2 owns validation).
                return cast("dict[str, Any]", json.loads(resp.read()))
        except urllib.error.URLError as e:
            raise OllamaError(f"GET {path} failed: {e}") from e

    # --- introspection -----------------------------------------------------------
    def version(self) -> str:
        # warrant(T3): .get on dict[str, Any] is Any; trusted local JSON boundary (PD-2).
        return cast(str, self._get("/api/version").get("version", ""))

    def list_models(self) -> list[str]:
        """Names of models available on disk (pullable -> resident)."""
        return [m["name"] for m in self._get("/api/tags").get("models", [])]

    def ps(self) -> list[str]:
        """Names of models currently loaded (resident in memory)."""
        return [m["name"] for m in self._get("/api/ps").get("models", [])]

    # --- model lifecycle ---------------------------------------------------------
    def load(self, model: str, *, num_ctx: int | None = None,
             keep_alive: str | int = "30m") -> None:
        """Warm a model into memory without generating. An empty `/api/generate` with
        keep_alive loads it; num_ctx sets the load-time window (changing it reloads)."""
        payload: dict[str, Any] = {"model": model, "keep_alive": keep_alive}
        if num_ctx is not None:
            payload["options"] = {"num_ctx": num_ctx}
        self._post("/api/generate", payload)

    def unload(self, model: str) -> None:
        """Evict a model now (keep_alive=0)."""
        self._post("/api/generate", {"model": model, "keep_alive": 0})

    # --- embeddings --------------------------------------------------------------
    def embed(self, model: str, inputs: list[str], *,
              keep_alive: str | int | None = None) -> list[list[float]]:
        """Batch-embed `inputs`. Returns one vector per input, order preserved."""
        payload: dict[str, Any] = {"model": model, "input": inputs}
        if keep_alive is not None:
            payload["keep_alive"] = keep_alive
        # warrant(T3): .get on dict[str, Any] is Any; trusted local JSON boundary (PD-2).
        return cast("list[list[float]]", self._post("/api/embed", payload).get("embeddings", []))

    # --- inference ---------------------------------------------------------------
    def chat(self, model: str, messages: list[Message], *,
             num_ctx: int | None = None, temperature: float | None = None,
             keep_alive: str | int | None = None, think: bool | None = None) -> str:
        """Single-shot, non-streaming chat. Returns the assistant text."""
        options: dict[str, Any] = {}
        if num_ctx is not None:
            options["num_ctx"] = num_ctx
        if temperature is not None:
            options["temperature"] = temperature
        payload: dict[str, Any] = {"model": model, "messages": messages, "stream": False}
        if options:
            payload["options"] = options
        if keep_alive is not None:
            payload["keep_alive"] = keep_alive
        if think is not None:  # Qwen3.x hybrid thinking toggle (per-request)
            payload["think"] = think
        # Generation runs on the long timeout — a heavy thinking-model tier legitimately takes
        # minutes; the control-plane default would false-trip on a real synthesis pass.
        data = self._post("/api/chat", payload, timeout=self.config.generation_timeout_s)
        # warrant(T3): chained .get over Any; trusted local JSON boundary (PD-2).
        return cast(str, data.get("message", {}).get("content", ""))
