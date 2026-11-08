"""Embedding adapter (BUILD-SPEC §8 derived layer).

Wraps the local embedding model. Documents are embedded plain; queries are wrapped in the
model's instruction format (Qwen3-Embedding is instruction-aware on the query side, which
materially improves retrieval). Embeddings are a regenerable derived representation —
re-embed from the raw store if the model changes (§8).

An input the embedding server cannot take whole is cut, not refused. The server answers an input
longer than its physical batch with an error rather than truncating it, and a chunk's budget of
characters does not bound its tokens (a run of symbols or of another script takes several tokens a
character: one comment of 1,145 characters took 2,951 tokens, past a batch of 2,048). So every
request goes through `embed_fitting`: a refused batch goes in halves until the refused text is
alone, and that text is cut, by bisection on its characters, to a prefix the server takes and
refuses one character longer, as an embedding model truncates an input at its maximum length. That
prefix is the longest the server takes when a prefix's token count grows with its length, as it
does but for a tokenizer's merges. The embedder counts its cuts, and the ingress's receipt
and the drain's report say how many a landing made. Any other failure is raised.
"""

from __future__ import annotations

import threading
from collections import deque
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from core.kernel.config import Config, EmbeddingConfig
from core.models.inference import InferenceClient

# The embedding server's refusal of an input longer than its physical batch.
TOO_LARGE = "too large to process"


def refused_for_length(e: Exception) -> bool:
    """Whether an embedding error is the server's refusal of an input for its length."""
    return TOO_LARGE in str(e).lower()


def embed_fitting(embed: Callable[[list[str]], list[list[float]]], texts: Sequence[str]
                  ) -> tuple[list[list[float]], list[tuple[int, int]]]:
    """The vectors of `texts` by `embed`, one request when the server takes it. When it refuses
    the request for an input's length, the texts go in halves until the refused text is alone, and
    that text is cut by bisection on its characters to a prefix the server takes and refuses one
    character longer (the longest it takes when token counts grow with the prefix); the cut is a
    function of the text and the server, so the same text is always cut the same way.
    Returns the vectors and each cut as `(characters, characters kept)`. Any other error is
    raised: nothing guesses past an embedder that fails."""
    try:
        return [[float(x) for x in v] for v in embed(list(texts))], []
    except Exception as e:      # noqa: BLE001 - a refusal for length is handled, the rest raised
        if not refused_for_length(e):
            raise
    if len(texts) > 1:
        half = len(texts) // 2
        left, lcuts = embed_fitting(embed, texts[:half])
        right, rcuts = embed_fitting(embed, texts[half:])
        return left + right, lcuts + rcuts
    text = texts[0]
    lo, hi, best = 0, len(text), None
    while hi - lo > 1:
        mid = (lo + hi) // 2
        try:
            vector = embed([text[:mid]])[0]
        except Exception as e:  # noqa: BLE001 - as above
            if not refused_for_length(e):
                raise
            hi = mid
            continue
        lo, best = mid, [float(x) for x in vector]
    if best is None:
        raise RuntimeError(f"the embedder refuses every prefix of a {len(text)}-character text")
    return [best], [(len(text), lo)]


@dataclass
class Embedder:
    # bp-115: this annotation was the LAST place the corpus pipeline named a vendor. Widening it
    # from `OllamaClient` to the protocol is what makes the runtime migration reversible — the
    # embedder cutover becomes a config flip rather than an edit here. The widening is strictly
    # more permissive, so every existing construction site and test stub still satisfies it, and
    # `Embedder`'s public surface below is byte-identical (30+ test files depend on it).
    client: InferenceClient
    config: EmbeddingConfig

    def __post_init__(self) -> None:
        # the texts this embedder cut to fit the server (`embed_fitting`): how many since it was
        # built, and the last hundred as (characters, characters kept). Instance state, not fields,
        # so the dataclass's fields and public surface stay what the lanes depend on.
        self.cut: int = 0
        self.last_cuts: deque[tuple[int, int]] = deque(maxlen=100)
        self._lock = threading.Lock()

    @property
    def dim(self) -> int:
        return self.config.dim

    def _documents(self, texts: list[str]) -> list[list[float]]:
        template = self.config.document_template
        if template != "{text}":
            texts = [template.format(text=t) for t in texts]
        return self.client.embed(self.config.model, texts)

    def _queries(self, texts: list[str]) -> list[list[float]]:
        # The model family's query format; Qwen3-Embedding's is "Instruct: <task>\nQuery: <text>".
        return self.client.embed(self.config.model, [
            self.config.query_template.format(instruction=self.config.query_instruction, text=t)
            for t in texts])

    def _record(self, cuts: list[tuple[int, int]]) -> None:
        if cuts:
            with self._lock:
                self.cut += len(cuts)
                self.last_cuts.extend(cuts)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        vectors, cuts = embed_fitting(self._documents, texts)
        self._record(cuts)
        return vectors

    def embed_query(self, text: str) -> list[float]:
        vectors, cuts = embed_fitting(self._queries, [text])
        self._record(cuts)
        return vectors[0]


def build_embedder(config: Config | None = None) -> Embedder:
    from core.kernel.config import get_config
    from core.models.inference import build_inference_client

    cfg = config or get_config()
    # The embedding ROLE picks its own backend (`[runtime] embedding_backend`), independently of
    # the chat tiers — that is what makes the embedder cutover a real, separately reversible step
    # (dn-local-model-runtime §2.6 P4). Default is `ollama`, so this returns exactly what it
    # returned before bp-115.
    return Embedder(client=build_inference_client(cfg), config=cfg.embedding)
