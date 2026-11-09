"""Late chunking (Günther et al. 2024): a document embedded once, each chunk's vector the mean of
its own tokens' embeddings.

The server is a second llama-server with `--embedding --pooling none` (port 8093 by default),
started for the run and stopped after it, never one of the stack's. With pooling off it returns
one 768-dimension vector a token, the output projection applied to each; the mean of every token's
vector of an input is exactly the pooled vector the stack's server returns for it (measured: cosine
1.0, the norms equal), so a chunk's late vector and its independent vector differ only in the
context its tokens saw.

The input is the template's prefix, then the document's text (the chunker's blocks joined, so
every chunk is a span of it), between the model's special tokens, tokenized once as one string. A
document longer than one window is embedded in windows of at most `window` tokens, the prefix and
the special tokens included, consecutive windows overlapping by `overlap` tokens; each token's
vector comes from the window in which it lies farthest from the window's ends. A chunk's vector is
the mean over the tokens whose characters meet its span, normalized.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from eval.embedder_use.common import BOS, EOS, F32, ServerTokenizer, post, unit

WINDOW = 2048
OVERLAP = 256


@dataclass
class LateLedger:
    documents: int = 0
    windows: int = 0
    tokens: int = 0                     # tokens embedded, special tokens included

    def summary(self) -> dict[str, int]:
        return {"documents": self.documents, "windows": self.windows, "tokens": self.tokens}


def windows(n: int, room: int, overlap: int) -> list[tuple[int, int]]:
    """Windows `[a, b)` of at most `room` tokens over `n`, consecutive ones sharing `overlap`;
    the last ends at `n`."""
    if n <= room:
        return [(0, n)]
    stride = max(1, room - overlap)
    out, a = [], 0
    while a + room < n:
        out.append((a, a + room))
        a += stride
    out.append((max(0, n - room), n))
    return out


def owner(n: int, wins: Sequence[tuple[int, int]]) -> list[int]:
    """For each token, the window in which it lies farthest from the window's ends."""
    best = [0] * n
    for t in range(n):
        depth = -1
        for w, (a, b) in enumerate(wins):
            if a <= t < b:
                d = min(t - a, b - 1 - t)
                if d > depth:
                    depth, best[t] = d, w
    return best


def late_vectors(prefix: str, doc: str, spans: Sequence[tuple[int, int]], tok: ServerTokenizer,
                 *, port: int = 8093, window: int = WINDOW, overlap: int = OVERLAP,
                 ledger: LateLedger | None = None) -> F32:
    """The late-chunked vectors of a document's chunks, given as spans of `doc`."""
    text = prefix + doc
    ids = tok.ids(text)
    sp = tok.spans(text)
    if len(ids) != len(sp):
        raise RuntimeError("the server's token ids and pieces disagree")
    first = next((i for i, (_, e) in enumerate(sp) if e > len(prefix)), len(sp))
    head, body_ids, body_sp = ids[:first], ids[first:], sp[first:]
    n = len(body_ids)
    room = window - len(head) - 2
    wins = windows(n, room, overlap)
    own = owner(n, wins)
    emb = np.zeros((n, 768), dtype=np.float64)
    for w, (a, b) in enumerate(wins):
        content = [BOS, *head, *body_ids[a:b], EOS]
        rows = np.asarray(post(port, "/embedding", {"content": content})[0]["embedding"],
                          dtype=np.float64)
        if rows.shape[0] != len(content):
            raise RuntimeError(f"{rows.shape[0]} token vectors for {len(content)} tokens")
        mine = [t for t in range(a, b) if own[t] == w]
        emb[mine] = rows[1 + len(head) + np.asarray(mine) - a]
        if ledger is not None:
            ledger.windows += 1
            ledger.tokens += len(content)
    if ledger is not None:
        ledger.documents += 1
    starts = np.asarray([s - len(prefix) for s, _ in body_sp])
    ends = np.asarray([e - len(prefix) for _, e in body_sp])
    out = np.zeros((len(spans), 768), dtype=np.float32)
    for i, (s, e) in enumerate(spans):
        hit = np.flatnonzero((starts < e) & (ends > s))
        if len(hit):
            out[i] = emb[hit].mean(axis=0)
    return unit(out)
