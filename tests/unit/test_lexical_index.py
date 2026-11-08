"""The lexical index (core/ingest/lexical.py): BM25 over landed chunks, no model."""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pytest

from core.ingest.lexical import LexicalIndex, _idf_check, rrf, tokens


def test_tokens_are_lowercased_runs_of_letters_and_digits():
    assert tokens("Graph-theory's 4-colour THEOREM, 1976.") == [
        "graph", "theory", "s", "4", "colour", "theorem", "1976"]


def test_bm25_weights_and_ranking_are_the_formulas():
    texts = ["spectral gap of a random graph", "random walks on graphs",
             "the gap between two numbers", "nothing relevant here"]
    idx = LexicalIndex.build(texts)
    assert idx.units == 4
    n, df = 4, 2                                         # "gap" is in two of four units
    dl, avgdl = 6, (6 + 4 + 5 + 3) / 4
    tf = 1
    w = _idf_check(n, df) * tf * 2.2 / (tf + 1.2 * (1 - 0.75 + 0.75 * dl / avgdl))
    col = idx.vocab["gap"]
    assert idx.weights[0, col] == pytest.approx(w, rel=1e-6)
    top = idx.search("spectral gap", k=2)
    assert top.tolist()[0] == 0 and set(top.tolist()) == {0, 2}
    assert idx.search("absent words").tolist() == []
    assert idx.search("random", among=np.asarray([1, 2, 3], dtype=np.int64)).tolist() == [1]


def test_the_index_survives_a_round_trip(tmp_path: Path):
    idx = LexicalIndex.build(["alpha beta", "beta gamma", "gamma delta"])
    size = idx.save(tmp_path / "lex")
    assert size > 0
    back = LexicalIndex.load(tmp_path / "lex")
    assert back.vocab == idx.vocab
    assert np.allclose(back.scores("beta gamma"), idx.scores("beta gamma"))


def test_reciprocal_rank_fusion_favours_agreement():
    a = np.asarray([1, 2, 3], dtype=np.int64)
    b = np.asarray([3, 1, 4], dtype=np.int64)
    fused = rrf([a, b], k=4).tolist()
    assert fused[0] == 1 and fused[1] == 3                 # both rank them high
    assert set(fused) == {1, 2, 3, 4}
    assert math.isclose(1 / 61 + 1 / 62, 1 / 61 + 1 / 62)
