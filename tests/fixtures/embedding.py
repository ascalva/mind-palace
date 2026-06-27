"""A deterministic fake embedder for cold tests — no model, no network.

Identical text → identical vector, so a query for a note's exact text retrieves it and changed
text embeds differently. Used by the vault-sync and purge tests (and anywhere a real embedder
would only add nondeterminism and an Ollama dependency).
"""

from __future__ import annotations

import hashlib

DIM = 8


class FakeEmbedder:
    def _vec(self, text: str) -> list[float]:
        h = hashlib.sha256(text.strip().encode("utf-8")).digest()
        return [b / 255.0 for b in h[:DIM]]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._vec(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vec(text)
