"""Embedding adapter (BUILD-SPEC §8 derived layer).

Wraps the local embedding model. Documents are embedded plain; queries are wrapped in the
model's instruction format (Qwen3-Embedding is instruction-aware on the query side, which
materially improves retrieval). Embeddings are a regenerable derived representation —
re-embed from the raw store if the model changes (§8).
"""

from __future__ import annotations

from dataclasses import dataclass

from core.kernel.config import Config, EmbeddingConfig
from core.models.inference import InferenceClient


@dataclass
class Embedder:
    # bp-115: this annotation was the LAST place the corpus pipeline named a vendor. Widening it
    # from `OllamaClient` to the protocol is what makes the runtime migration reversible — the
    # embedder cutover becomes a config flip rather than an edit here. The widening is strictly
    # more permissive, so every existing construction site and test stub still satisfies it, and
    # `Embedder`'s public surface below is byte-identical (30+ test files depend on it).
    client: InferenceClient
    config: EmbeddingConfig

    @property
    def dim(self) -> int:
        return self.config.dim

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return self.client.embed(self.config.model, texts)

    def embed_query(self, text: str) -> list[float]:
        # Qwen3-Embedding query format: "Instruct: <task>\nQuery: <text>".
        wrapped = f"Instruct: {self.config.query_instruction}\nQuery: {text}"
        return self.client.embed(self.config.model, [wrapped])[0]


def build_embedder(config: Config | None = None) -> Embedder:
    from core.kernel.config import get_config
    from core.models.inference import build_inference_client

    cfg = config or get_config()
    # The embedding ROLE picks its own backend (`[runtime] embedding_backend`), independently of
    # the chat tiers — that is what makes the embedder cutover a real, separately reversible step
    # (dn-local-model-runtime §2.6 P4). Default is `ollama`, so this returns exactly what it
    # returned before bp-115.
    return Embedder(client=build_inference_client(cfg), config=cfg.embedding)
