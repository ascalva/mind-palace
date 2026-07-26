"""ModelServer — the facade agents use to talk to local models.

Combines the registry, the two-slot loader, and the Ollama client so callers say
"chat at the synthesis tier" and the right model is made resident first (model
advises, code acts). Persona/params are passed through at request time.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.kernel.config import Config, get_config
from core.kernel.constitution import Message
from core.models.inference import InferenceClient
from core.models.loader import ModelConfig, TwoSlotLoader
from core.models.ollama_client import OllamaClient
from core.models.registry import Registry


@dataclass
class ModelServer:
    config: Config
    # bp-115: the chat path reaches inference through the protocol, not a vendor class.
    client: InferenceClient
    loader: TwoSlotLoader

    def version(self) -> str:
        """The Ollama server's version string — asked of the LOADER's client, which stays
        concretely `OllamaClient`-typed on purpose (bp-115 §3 Q2: residency-manager operations
        have no llama.cpp counterpart, and `core/models/loader.py` is bp-116's to replace).
        `version()` is deliberately NOT on the inference protocol: llama-server's readiness is a
        503→200 transition that a version string cannot express, so the seam carries `healthy()`
        instead. `build_model_server` hands the same client object to both fields, so this
        returns exactly what `self.client.version()` returned before."""
        return self.loader.client.version()

    def ensure_pinned(self, *, warm: bool = True) -> ModelConfig:
        return self.loader.ensure_pinned(warm=warm)

    def chat(self, tier: str, messages: list[Message], *,
             think: bool | None = None, temperature: float | None = None) -> str:
        model = self.loader.ensure_tier(tier)
        return self.client.chat(
            model.name,
            messages,
            num_ctx=model.num_ctx,
            think=think,
            temperature=temperature,
            keep_alive=self.config.ollama.default_keep_alive,
        )


def build_model_server(config: Config | None = None) -> ModelServer:
    config = config or get_config()
    # Still constructed concretely, and deliberately so: the SAME object is the loader's
    # residency client (which needs ps/load/unload — off the protocol by design) and the chat
    # client. Per-tier `[runtime] chat_backend` dispatch needs one client PER TIER, which is a
    # shape change to this class and belongs to the chat cutover (bp-118/P5), not to the seam.
    # The key is schema'd now so it can never be half-defined and silently dropped (§3 Q7).
    client = OllamaClient(config.ollama)
    registry = Registry(config)
    loader = TwoSlotLoader(config=config, client=client, registry=registry)
    return ModelServer(config=config, client=client, loader=loader)
