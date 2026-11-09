"""Chunks by a budget of characters (the live chunker) or of the embedder's tokens, and the spans
a late-chunking pass pools over.

`token_chunks` is `core/kernel/ingest/chunk.py::chunk_text` with lengths counted in the
embedder's own tokens: the same blocks (paragraphs, stripped), the same greedy packing with the
overlap tail counted against the budget, a block longer than the budget split into windows of
whole tokens, and the same joint (a blank line, one token). So the two families of arms differ
only in the unit of the budget.

`document_text` is the text a chunking is a set of spans of: the chunker's blocks joined as it
joins them. Every chunk of `chunk_text` is a contiguous span of it (a chunk is consecutive blocks,
its overlap tail the end of the previous chunk, which ends where the next block's joint begins),
which `chunk_spans` finds and checks.
"""

from __future__ import annotations

from collections.abc import Callable

from core.kernel.ingest.chunk import _blocks, chunk_text

Spans = list[tuple[int, int]]
JOINT = "\n\n"


def char_chunks(body: str, budget: int) -> list[str]:
    """The live chunker at a budget of characters, its overlap one eighth of the budget."""
    return [c.text for c in chunk_text(body, max_chars=budget, overlap_chars=budget // 8)]


def token_chunks(body: str, budget: int, spans: Callable[[str], Spans],
                 overlap: int | None = None) -> list[str]:
    """`chunk_text`'s packing with lengths in tokens; `spans(text)` gives a text's token spans.
    The overlap is one eighth of the budget unless given."""
    tail_n = budget // 8 if overlap is None else overlap
    pieces: list[tuple[str, Spans]] = []
    for raw in body.split(JOINT):
        b = raw.strip()
        if not b:
            continue
        sp = spans(b)
        if len(sp) <= budget:
            pieces.append((b, sp))
            continue
        for i in range(0, len(sp), budget):         # an oversized block: windows of whole tokens
            w = sp[i:i + budget]
            s0, e0 = w[0][0], w[-1][1]
            if e0 > s0:
                pieces.append((b[s0:e0], [(a - s0, z - s0) for a, z in w]))
    chunks: list[str] = []
    cur: str = ""
    cur_sp: Spans = []
    for b, sp in pieces:
        if cur and len(cur_sp) + 1 + len(sp) > budget:
            chunks.append(cur)
            if tail_n:
                tail_sp = cur_sp[-tail_n:]
                t0 = tail_sp[0][0]
                cur, cur_sp = cur[t0:], [(a - t0, z - t0) for a, z in tail_sp]
                cur, cur_sp = _join(cur, cur_sp, b, sp)
            else:
                cur, cur_sp = b, list(sp)
        elif cur:
            cur, cur_sp = _join(cur, cur_sp, b, sp)
        else:
            cur, cur_sp = b, list(sp)
    if cur:
        chunks.append(cur)
    return chunks


def _join(a: str, a_sp: Spans, b: str, b_sp: Spans) -> tuple[str, Spans]:
    off = len(a) + len(JOINT)
    return a + JOINT + b, [*a_sp, (len(a), off), *((s + off, e + off) for s, e in b_sp)]


def document_text(body: str, budget: int) -> str:
    """The text whose spans `chunk_text(body, max_chars=budget)` cuts: its blocks, joined."""
    return JOINT.join(_blocks(body, budget))


def chunk_spans(doc: str, chunks: list[str]) -> Spans:
    """Each chunk's `[start, end)` in `doc`, in order; every chunk must be a span of it, starting
    no earlier than the previous one (a chunk shorter than the overlap is carried whole into the
    next, which then starts where it starts) and ending no earlier."""
    out: Spans = []
    at = end = 0
    for c in chunks:
        i = doc.find(c, at)
        if i < 0 or i + len(c) < end:
            raise ValueError("a chunk is not a span of its document's text")
        out.append((i, i + len(c)))
        at, end = i, i + len(c)
    return out
