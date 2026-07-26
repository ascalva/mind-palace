"""The backend-agnostic inference seam (`dn-local-model-runtime` §2.6 P1).

One protocol, two implementations: `OllamaClient` — today's default, unchanged — and
`LlamaServerClient`, which speaks llama.cpp's OpenAI-compatible surface. Everything above this
line (the `Embedder`, the `ModelServer`, every ingest lane) names a *capability*, never a vendor.

**Why the seam exists at all.** It is the whole reversibility story of the runtime migration
(note §2.6): with inference reached through a protocol, rolling back any later phase is a config
flip rather than a revert, and a third backend (MLX, parked) becomes a cheap experiment instead
of a refactor. Nothing observable changes when this module lands — that is the acceptance bar,
not a caveat.

**Deliberately three methods.** `ps`, `load`, `unload` and `list_models` are NOT here. Those are
*residency-manager* operations that exist only because Ollama owns residency; under note §2.3
residency becomes child-process existence and they have no llama.cpp counterpart. A protocol
carrying them would force one implementation to lie four times. The residency manager keeps
talking to `OllamaClient` concretely (`core/models/loader.py`) until its successor replaces the
question outright.

**`healthy()` rather than `version()`.** llama-server's readiness is a 503→200 transition while
the model loads (note §2.1 G measured it); a version string cannot express "up but not ready",
and a caller that reads "responded" as "ready" would dispatch into a loading server.

**Stdlib-only binds the seam, not just one client.** The rule is stated in full on
`core/models/ollama_client.py:3-6` and is reproduced here as a property of *every* implementation
of this protocol: a sealed-core inference client must not import a network-capable third-party
package (CONVENTIONS). `urllib` is permitted because each request targets a `127.0.0.1` literal
(no DNS) that the egress guard `core.sealing` allows, and the static import firewall
(`ops/import_lint.py`, `NETWORK_ALLOWLIST`) audits the exception by filename. See that docstring
for the reasoning rather than a second copy of it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from core.kernel.constitution import Message

if TYPE_CHECKING:  # pragma: no cover - typing-only, avoids a config import at module load
    from core.kernel.config import Config

__all__ = ["InferenceClient", "Message", "build_inference_client"]


@runtime_checkable
class InferenceClient(Protocol):
    """Backend-agnostic local inference. Implementations: `OllamaClient` (default) and
    `LlamaServerClient`. Deliberately EXCLUDES ps/load/unload/list_models — those are
    residency-manager operations that exist only because Ollama owns residency; under
    `dn-local-model-runtime` §2.3 residency becomes child-process existence and they have no
    counterpart. A protocol that included them would force one implementation to lie.

    `runtime_checkable` buys an honest but *shallow* `isinstance` — method presence only, never
    signatures. It is used as a test ratchet; the real conformance check is mypy's.
    """

    def embed(self, model: str, inputs: list[str], *,
              keep_alive: str | int | None = None) -> list[list[float]]:
        """Batch-embed `inputs`. One vector per input, order preserved."""
        ...

    def chat(self, model: str, messages: list[Message], *,
             num_ctx: int | None = None, temperature: float | None = None,
             keep_alive: str | int | None = None, think: bool | None = None) -> str:
        """Single-shot, non-streaming chat. Returns the assistant text."""
        ...

    def healthy(self) -> bool:
        """Up AND ready to serve — not merely reachable. See the module docstring."""
        ...


def build_inference_client(config: Config, *, tier: str | None = None) -> InferenceClient:
    """The PER-ROLE selector (`dn-local-model-runtime` §4): `tier=None` is the embedding role,
    a tier name reads the `[runtime] chat_backend` per-tier override. Per role, not global —
    that is what makes the embedder cutover (P4) a real, independently reversible step.

    Defaults return `OllamaClient` for every role, so this changes nothing at landing. Flipping
    is the owner's, in `config/local.toml`, at P4/P5 — never here (plan §9).
    """
    # Imported here, not at module scope: the protocol must not drag its implementations into
    # every importer, and `llama_server_client` is inert unless a role is actually flipped.
    from core.models.llama_server_client import LlamaServerClient
    from core.models.ollama_client import OllamaClient

    runtime = config.runtime
    backend = runtime.embedding_backend if tier is None else runtime.chat_backend_for(tier)
    if backend == "ollama":
        return OllamaClient(config.ollama)
    if backend == "llamacpp":
        return LlamaServerClient()
    raise ValueError(
        f"unknown inference backend {backend!r} for role {tier or 'embedding'!r} "
        f"(expected 'ollama' or 'llamacpp')"
    )
