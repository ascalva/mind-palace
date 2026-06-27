"""Deterministic capability metrics + the golden-set harness (BUILD-SPEC §15).

No model needed: the harness is decoupled from retrieval via a stub, so the metric math
and the regression gate are unit-tested cold. The live golden run is test_golden_live.py.
"""

import pytest

from eval.golden import GoldenQuery, evaluate, regressions
from eval.metrics import mean_cosine_distance, recall_at_k, set_overlap


def test_recall_at_k():
    assert recall_at_k({"a"}, ["a", "b", "c"], 3) == 1.0
    assert recall_at_k({"a"}, ["b", "c", "a"], 2) == 0.0      # a falls outside top-2
    assert recall_at_k({"a", "b"}, ["a", "x", "y"], 3) == 0.5
    assert recall_at_k(set(), ["x"], 3) == 1.0               # nothing expected => vacuous


def test_set_overlap_is_jaccard():
    assert set_overlap({"a"}, ["a", "b", "c"], 3) == 1 / 3
    assert set_overlap({"a"}, ["a"], 3) == 1.0
    assert set_overlap({"a"}, ["x", "y"], 3) == 0.0


def test_mean_cosine_distance():
    assert mean_cosine_distance([0.2, 0.4]) == pytest.approx(0.3)
    assert mean_cosine_distance([]) == 0.0


def _stub(mapping):
    def retrieve(query, k):
        return mapping[query][:k]
    return retrieve


def test_evaluate_aggregates_and_passes_equal_baseline():
    golden = (
        GoldenQuery(id="q1", query="sleep", expected=frozenset({"sleep-note"}), k=3),
        GoldenQuery(id="q2", query="garden", expected=frozenset({"garden-note"}), k=3),
    )
    rows = {
        "sleep": [{"title": "sleep-note", "_distance": 0.4}, {"title": "x", "_distance": 0.6}],
        "garden": [{"title": "garden-note", "_distance": 0.3}],
    }
    report = evaluate(golden, _stub(rows))
    assert report.recall_at_k == 1.0
    m = report.as_metrics()
    assert regressions(report, {"recall_at_k": 1.0, "overlap": m["overlap"],
                                "mean_distance": m["mean_distance"]}) == []


def test_regression_detected_on_missed_retrieval():
    golden = (GoldenQuery(id="q1", query="sleep", expected=frozenset({"sleep-note"}), k=3),)
    rows = {"sleep": [{"title": "wrong-note", "_distance": 0.9}]}
    report = evaluate(golden, _stub(rows))
    assert report.recall_at_k == 0.0
    flagged = regressions(report, {"recall_at_k": 1.0, "overlap": 1.0, "mean_distance": 1.0})
    assert "recall_at_k" in flagged
