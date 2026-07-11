"""Shared deterministic stand-ins for the model + embedder (no Ollama).

These let the conversational tests (and the offline CLI) exercise the REAL machinery —
retrieval, the budgeter, capture, the stores — with only the two genuinely model-backed
pieces faked. The fakes are deterministic so the suite is stable.
"""

from __future__ import annotations

import hashlib
import math
import re
from collections.abc import Callable

from core.constitution import Message

_WORD = re.compile(r"[a-z0-9']+")


class HashingEmbedder:
    """Lexical hashing embedder: bag-of-words hashed into `dim` buckets, L2-normalized. Cosine
    similarity tracks word overlap, so retrieval returns topically-related chunks — enough to
    drive the conversation tests without a real embedding model. Deterministic."""

    def __init__(self, dim: int = 32):
        self.dim = dim

    def _vec(self, text: str) -> list[float]:
        v = [0.0] * self.dim
        for w in _WORD.findall(text.lower()):
            b = int(hashlib.sha256(w.encode()).hexdigest(), 16) % self.dim
            v[b] += 1.0
        norm = math.sqrt(sum(x * x for x in v))
        if norm == 0.0:
            v[0] = 1.0   # avoid a zero vector (cosine undefined)
            norm = 1.0
        return [x / norm for x in v]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._vec(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vec(text)


class ReplyServer:
    """A ModelServer stand-in. `chat(tier, messages, **kw)` returns `fn(tier, messages)` if a
    function was given, else the canned `reply`. Records every call for assertions."""

    def __init__(
        self, reply: str = "ok", fn: Callable[[str, list[Message]], str] | None = None
    ):
        self.reply = reply
        self.fn = fn
        self.calls: list[tuple[str, list[Message]]] = []

    def chat(self, tier: str, messages: list[Message], **kwargs: object) -> str:
        self.calls.append((tier, messages))
        return self.fn(tier, messages) if self.fn is not None else self.reply
