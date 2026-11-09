"""The embedder-use study's pure parts (eval/embedder_use/): the token-bounded chunker mirrors the
character chunker, every chunk is a span of its document's text, late chunking's windows and
token owners, document-level ranking, the S stemmer, and the semantic-edge rules on a toy
geometry."""

from __future__ import annotations

import numpy as np

from eval.embedder_use.chunking import (
    char_chunks,
    chunk_spans,
    document_text,
    token_chunks,
)
from eval.embedder_use.common import Chunked, rank_documents, verdict
from eval.embedder_use.edges import _pairs, rules
from eval.embedder_use.late import owner, windows
from eval.embedder_use.tokens import s_stem


def char_spans(text: str) -> list[tuple[int, int]]:
    """A tokenizer of one token a character."""
    return [(i, i + 1) for i in range(len(text))]


BODY = "Title\n\n" + "\n\n".join(
    " ".join(f"w{p}x{i}" for i in range(n)) for p, n in enumerate([3, 40, 7, 120, 2, 15]))


def test_the_token_chunker_packs_blocks_greedily_within_its_budget():
    """With one token a character: no chunk passes the budget, its overlap tail and the joint;
    with no overlap the chunks are the blocks (an oversized one cut in windows) packed in order;
    each chunk after a flush starts with the previous chunk's last tokens; a budget past the
    whole text gives one chunk, the blocks joined."""
    blocks = [b.strip() for b in BODY.split("\n\n")]
    for budget in (40, 80, 200):
        tail = budget // 8
        chunks = token_chunks(BODY, budget, char_spans)
        assert all(len(c) <= budget + tail + 2 for c in chunks)
        for prev, nxt in zip(chunks, chunks[1:], strict=False):
            # the tail is the last `tail` tokens (a joint among them one token of two
            # characters), or the whole previous chunk when it is shorter
            lo = min(tail, len(prev))
            assert any(prev.endswith(nxt[:k]) for k in range(lo, 2 * tail + 1))
        bare = token_chunks(BODY, budget, char_spans, overlap=0)
        assert "".join(bare).replace("\n", "") == "".join(blocks)
        assert all(len(c) <= budget for c in bare)
    assert token_chunks(BODY, 10_000, char_spans) == ["\n\n".join(blocks)]


def test_every_chunk_is_a_span_of_its_documents_text():
    for budget in (40, 80, 200, 1200):
        chunks = char_chunks(BODY, budget)
        doc = document_text(BODY, budget)
        spans = chunk_spans(doc, chunks)
        assert [doc[a:b] for a, b in spans] == chunks
        assert all(s0 <= s1 for (s0, _), (s1, _) in zip(spans, spans[1:], strict=False))


def test_a_chunk_shorter_than_the_overlap_is_carried_whole_into_the_next():
    body = "Hi\n\n" + "x" * 300
    chunks = char_chunks(body, 200)
    assert chunks[0] == "Hi" and chunks[1].startswith("Hi\n\n")
    spans = chunk_spans(document_text(body, 200), chunks)
    assert spans[0][0] == spans[1][0] == 0


def test_late_windows_cover_every_token_and_each_token_has_the_deepest_window():
    assert windows(10, 20, 4) == [(0, 10)]
    ws = windows(100, 30, 10)
    assert ws[0] == (0, 30) and ws[-1][1] == 100 and all(b - a <= 30 for a, b in ws)
    covered = set().union(*(range(a, b) for a, b in ws))
    assert covered == set(range(100))
    own = owner(100, ws)
    for t, w in enumerate(own):
        a, b = ws[w]
        depth = min(t - a, b - 1 - t)
        assert all(min(t - a2, b2 - 1 - t) <= depth for a2, b2 in ws if a2 <= t < b2)


def test_documents_rank_by_their_best_chunk():
    cv = np.asarray([[1, 0], [0, 1], [0.6, 0.8], [0.8, 0.6]], dtype=np.float32)
    ch = Chunked(["a1", "a2", "b1", "c1"], np.asarray([0, 0, 1, 2], dtype=np.int64),
                 ["a", "b", "c"])
    q = np.asarray([[0, 1]], dtype=np.float32)
    assert rank_documents(q, cv, ch, k=3) == [["a", "b", "c"]]
    q = np.asarray([[1, 0]], dtype=np.float32)
    assert rank_documents(q, cv, ch, k=2) == [["a", "c"]]


def test_the_decision_words():
    assert verdict(0.02, 0.01, 0.01) == "better"
    assert verdict(-0.02, -0.03, 0.01) == "worse"
    assert verdict(0.0, -0.005, 0.5) == "no worse"
    assert verdict(-0.01, -0.03, 0.5) == "undecided"


def test_the_s_stemmer_takes_the_first_rule_that_applies():
    assert [s_stem(w) for w in ("queries", "graphes", "graphs", "class", "corpus", "aies",
                                "shoes", "trees")] == \
        ["query", "graphe", "graph", "class", "corpus", "aie", "shoe", "tree"]


def test_the_edge_rules_on_a_toy_geometry():
    """Two tight clusters of different sources and one loose cluster: a global threshold gives
    the loose source no edge, a per-source quantile gives every source edges, mutual neighbours
    are symmetric, and CSLS keeps an edge only where two items are closer than their typical
    neighbours."""
    rng = np.random.default_rng(0)
    centers = rng.normal(size=(3, 16))
    spread = (0.05, 0.05, 0.6)
    pts, src = [], []
    for k, (c, s) in enumerate(zip(centers, spread, strict=True)):
        for _ in range(30):
            pts.append(c + s * rng.normal(size=16))
            src.append(k)
    x = np.asarray(pts, dtype=np.float32)
    x /= np.linalg.norm(x, axis=1, keepdims=True)
    sims = x @ x.T
    np.fill_diagonal(sims, -np.inf)
    order = np.argsort(-sims, axis=1)[:, :50]
    nn = order.astype(np.int64)
    ss = np.take_along_axis(sims, order, axis=1).astype(np.float32)
    have = np.ones(len(x), dtype=bool)
    out = rules(nn, ss, np.asarray(src, dtype=np.int64), have)
    for name in ("G", "GQ", "SQ", "M", "C"):
        i, j = out[name]
        assert np.all(i < j)
    i, j = out["SQ"]
    deg = np.bincount(np.concatenate([i, j]), minlength=len(x))
    assert all(deg[np.asarray(src) == k].sum() > 0 for k in range(3))
    mi, mj = out["M"]
    fwd = {(a, b) for a in range(len(x)) for b in nn[a, :10].tolist()}
    assert all((a, b) in fwd and (b, a) in fwd for a, b in zip(mi.tolist(), mj.tolist(),
                                                               strict=True))
    a, b = _pairs(np.asarray([3, 1, 1, 2], dtype=np.int64),
                  np.asarray([1, 3, 1, -1], dtype=np.int64))
    assert (a.tolist(), b.tolist()) == ([1], [3])
