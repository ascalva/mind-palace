"""The decision-integrator study's instruments, unit tier.

The record's numbers are only as good as the harness's arithmetic (the calibration and ranking
metrics, the polarity rules, the selection rule that keeps a question only for measured gain) and
the guards around the hosted arm (the dollar stop, the key kept out of every repr, a failure that
is never read as an answer). Each is pinned here on synthetic data, before any model is asked.
"""

from __future__ import annotations

import itertools
import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from edge import systemone
from eval import decision_integrators as di
from eval import decision_questions as dq

# ── the questions ───────────────────────────────────────────────────────────────────────────────


def test_a_question_sets_digest_ignores_id_order_but_not_option_order() -> None:
    a = {"x": dq.POLARITY["supports"], "y": dq.POLARITY["relation"]}
    b = {"y": dq.POLARITY["relation"], "x": dq.POLARITY["supports"]}
    assert dq.digest(a) == dq.digest(b)
    reordered = {"x": dq.POLARITY["supports"], "y": dq.POLARITY["relation_reversed"]}
    assert dq.digest(a) != dq.digest(reordered)
    reworded = json.loads(json.dumps(a))
    reworded["x"]["instructions"] += " "
    assert dq.digest(a) != dq.digest(reworded)


def test_every_declared_question_is_well_formed() -> None:
    for family, questions in dq.FAMILIES.items():
        for qid, q in questions.items():
            assert q["type"] in {"noul", "choice", "score"}, (family, qid)
            assert isinstance(q["instructions"], str) and q["instructions"].strip()
            if q["type"] == "choice":
                assert 1 <= len(q["criteria"]) <= 255
            if q["type"] == "score":
                assert 1 <= len(q["criteria"]) <= 10
            if q["type"] == "noul" and "criteria" in q:
                assert set(q["criteria"]) == {"true", "false"}
    assert list(dq.POLARITY["relation_reversed"]["criteria"]) == list(
        reversed(list(dq.POLARITY["relation"]["criteria"])))
    assert len(dq.DISCOVERY) == 20
    assert set(dq.manifest()["families"]) == set(dq.FAMILIES)


# ── the polarity rules ──────────────────────────────────────────────────────────────────────────


def test_the_noul_rules_give_distributions_that_follow_their_inputs() -> None:
    s = np.array([0.95, 0.05, 0.05, 0.5])
    c = np.array([0.05, 0.95, 0.05, 0.5])
    a = np.array([0.95, 0.95, 0.05, 0.5])
    for p in (di.noul_product(s, c), di.noul_companion(s, c, a)):
        assert np.allclose(p.sum(axis=1), 1.0)
        assert np.argmax(p, axis=1)[:3].tolist() == [0, 1, 2]
    assert np.allclose(di.noul_product(np.array([1.0]), np.array([1.0])), 1 / 3)


# ── the metrics ─────────────────────────────────────────────────────────────────────────────────


def test_auroc_counts_pairs_with_ties_as_half() -> None:
    rng = np.random.default_rng(0)
    score = rng.integers(0, 4, 60).astype(float)
    label = rng.integers(0, 2, 60).astype(np.int64)
    pos, neg = score[label == 1], score[label == 0]
    brute = np.mean([1.0 if p > n else 0.5 if p == n else 0.0
                     for p, n in itertools.product(pos, neg)])
    assert di.auroc(score, label) == pytest.approx(brute)


def test_brier_log_loss_and_macro_f1_on_known_cases() -> None:
    y = np.array([0, 1, 2, 2], dtype=np.int64)
    perfect = np.eye(3)[y]
    assert di.brier(y, perfect) == 0.0
    assert di.brier(y, np.full((4, 3), 1 / 3)) == pytest.approx(2 / 3)
    assert di.log_loss(y, np.full((4, 3), 1 / 3)) == pytest.approx(np.log(3))
    pred = np.array([0, 2, 2, 2], dtype=np.int64)  # class 1 missed: F1s 1, 0, 0.8
    assert di.macro_f1(y, pred) == pytest.approx((1 + 0 + 0.8) / 3)


def test_ece_is_zero_when_confidence_matches_the_observed_rate() -> None:
    conf = np.array([0.25] * 4 + [0.75] * 4)
    correct = np.array([1, 0, 0, 0, 1, 1, 1, 0], dtype=float)
    value, curve = di.ece(conf, correct)
    assert value == pytest.approx(0.0)
    assert sum(b["n"] for b in curve) == 8
    value2, _ = di.ece(np.full(4, 0.9), np.zeros(4))
    assert value2 == pytest.approx(0.9)


def test_ranking_metrics_on_a_hand_checked_list() -> None:
    score = np.array([0.9, 0.8, 0.7, 0.6])
    label = np.array([1, 0, 1, 0], dtype=np.int64)
    assert di.average_precision(score, label) == pytest.approx((1 + 2 / 3) / 2)
    assert di.precision_at(score, label, 2) == pytest.approx(0.5)


def test_the_cluster_interval_brackets_its_statistic() -> None:
    v = np.random.default_rng(1).normal(0.3, 1.0, 400)
    lo, hi = di.cluster_ci(lambda i: float(v[i].mean()), [k // 4 for k in range(400)], b=500)
    assert lo < v.mean() < hi


def test_a_failed_request_is_never_read_as_an_answer() -> None:
    failed: dict[str, Any] = {"key": "k", "error": "HTTP 400: prompt too long"}
    assert np.isnan(di.noul(failed, "supports"))
    assert np.isnan(di.probs(failed, "relation", di.POLARITY_LABELS)).all()
    table = di.classification(np.array([0, 1], dtype=np.int64),
                              np.array([[0.9, 0.05, 0.05], [np.nan] * 3]), di.POLARITY_LABELS)
    assert table["n"] == 1 and table["missing"] == 1


# ── the data shapes ─────────────────────────────────────────────────────────────────────────────


def test_a_posts_kind_markers_are_removed_from_its_body() -> None:
    question = ("How do I sort a grid?\n\nI have a grid.\n\nCan I sort it fast?"
                "\n\nTags: sorting, grids")
    answer = "Answer to: How do I sort a grid?\n\nUse a heap.\n\nIt runs in n log n."
    assert di.post_parts(question) == ("How do I sort a grid?",
                                       "I have a grid.\n\nCan I sort it fast?")
    assert di.post_parts(answer) == ("Answer to: How do I sort a grid?",
                                     "Use a heap.\n\nIt runs in n log n.")


def test_rerank_orders_keep_ties_in_the_embedders_order_and_fuse_both() -> None:
    orders = di.rerank_orders(["a", "b", "c", "d"], {"a": 0.1, "b": 0.9, "c": 0.9, "d": 0.5})
    assert orders["embedder"] == ["a", "b", "c", "d"]
    assert orders["judged"] == ["b", "c", "d", "a"]
    assert orders["fused"][0] == "b" and set(orders["fused"]) == {"a", "b", "c", "d"}


# ── question discovery ──────────────────────────────────────────────────────────────────────────


def test_forward_selection_keeps_a_question_with_signal_and_refuses_noise() -> None:
    rng = np.random.default_rng(2)
    n = 900
    y = rng.integers(0, 3, n).astype(np.int64)
    signal = (y[:, None] == np.arange(3)[None, :]).astype(float)[:, :2] * 0.8 + rng.normal(
        0, 0.3, (n, 2))
    base = rng.normal(0, 1, (n, 1))
    cands = {"signal": signal, "noise": rng.normal(0, 1, (n, 1))}
    fit, check = np.arange(0, 500), np.arange(500, n)
    sel = di.forward_select(base, cands, y, fit, check, min_gain=0.005, max_keep=6)
    assert sel["kept"] == ["signal"]
    assert sel["first_step_gain"]["signal"] > 0.1 > sel["first_step_gain"]["noise"]
    assert sel["path"][-1].get("refused") == "noise"


def test_shapley_values_are_efficient_and_credit_each_players_own_gain() -> None:
    gains = {"embedder": 0.3, "q1": 0.2, "q2": 0.0}
    phi = di.shapley(list(gains), lambda s: sum(gains[p] for p in s))
    assert phi == pytest.approx(gains)
    joint = di.shapley(["a", "b"], lambda s: 1.0 if s == {"a", "b"} else 0.0)
    assert joint == pytest.approx({"a": 0.5, "b": 0.5})


# ── the hosted arm's guards (edge/systemone.py) ─────────────────────────────────────────────────


def test_the_key_never_appears_in_a_clients_repr() -> None:
    assert "s3cr3t" not in repr(systemone.Client(key="s3cr3t"))


def _fake(status: int = 200, tokens: int = 1_000_000) -> systemone.Transport:
    def send(payload: dict[str, Any]) -> tuple[int, dict[str, Any], dict[str, str]]:
        if status != 200:
            return status, {"detail": "bad request"}, {}
        return 200, {"answers": {}, "usage": {"input_tokens": tokens, "output_tokens": 0}}, {}
    return send


def test_the_ledger_stops_sending_once_it_reaches_its_stop(tmp_path: Path) -> None:
    ledger = systemone.Ledger(tmp_path / "ledger.json", price_per_mtok=1.0, stop_usd=1.5)
    client = systemone.Client(key="k", transport=_fake())
    lines = [{"key": str(i), "payload": {}} for i in range(5)]
    rows, unsent = systemone.run(lines, client, ledger, workers=1)
    assert len(rows) == 2 and unsent == 3          # $1 after one, $2 after two: then stop
    assert json.loads((tmp_path / "ledger.json").read_text())["usd"] == pytest.approx(2.0)
    again = systemone.Ledger(tmp_path / "ledger.json", price_per_mtok=1.0, stop_usd=1.5)
    assert not again.open()                        # the stop holds across runs


def test_a_refused_request_is_written_as_an_error(tmp_path: Path) -> None:
    ledger = systemone.Ledger(tmp_path / "ledger.json", price_per_mtok=1.0, stop_usd=1.5)
    client = systemone.Client(key="k", transport=_fake(status=422), retries=2)
    rows, unsent = systemone.run([{"key": "a", "payload": {}}], client, ledger, workers=1)
    assert unsent == 0 and "error" in rows[0] and "response" not in rows[0]
    assert ledger.requests == 0
