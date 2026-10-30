"""The quantization bench's instruments (eval/quantization_bench.py) — unit tier.

Step C's numbers are only as good as the bench's recall arithmetic, its exact search and its
two-stage rescoring, so those are pinned here on synthetic unit vectors before any store is read:
each control the bench relies on must behave as a control, and each quantizer's error must be the
size its construction says.
"""

from __future__ import annotations

import numpy as np

from eval import quantization_bench as qb


def _unit(n: int, d: int, seed: int) -> qb.F32:
    return qb.normalize(np.random.default_rng(seed).standard_normal((n, d)).astype(np.float32))


def test_recall_counts_shared_members_and_ignores_order() -> None:
    truth = np.array([[1, 2, 3, 4], [5, 6, 7, 8]], dtype=np.int64)
    got = np.array([[4, 3, 9, 8], [8, 7, 6, 5]], dtype=np.int64)
    assert qb.recall(truth, got).tolist() == [0.5, 1.0]


def test_topk_returns_the_largest_scores_best_first() -> None:
    scores = np.array([[0.1, 0.9, 0.5, 0.7]], dtype=np.float32)
    assert qb.topk(scores, 3).tolist() == [[1, 3, 2]]


def test_exact_search_finds_each_stored_vector_first_unless_it_is_excluded() -> None:
    x = _unit(300, 16, 0)
    own = np.arange(20, dtype=np.int64)
    assert qb.search(x[:20], x, 1)[:, 0].tolist() == own.tolist()
    without = qb.search(x[:20], x, 5, exclude=own)
    assert not any(i in row for i, row in zip(own.tolist(), without.tolist(), strict=True))


def test_the_float32_control_scheme_reproduces_the_ground_truth() -> None:
    x, q = _unit(400, 32, 1), _unit(30, 32, 2)
    control = next(qb.numpy_schemes(x, np.random.default_rng(3)))
    assert control.name == "float32"
    assert qb.recall(qb.search(q, x, qb.K), control.run(q, None)).min() == 1.0


def test_rescoring_every_row_is_exact_search() -> None:
    x, q = _unit(200, 16, 4), _unit(25, 16, 5)
    everything = np.tile(np.arange(len(x), dtype=np.int64), (len(q), 1))
    assert qb.recall(qb.search(q, x, qb.K), qb.rescore(q, x, everything, qb.K)).min() == 1.0


def test_rescoring_a_wider_first_stage_never_loses_a_true_neighbour() -> None:
    """With continuous first-stage scores the top-40 contains the top-10, and rescoring in float32
    keeps every true neighbour the wider stage found, so recall can only rise. (Hamming scores tie
    too often for that containment to hold per query; truncated float scores do not tie.)"""
    x, q = _unit(1000, 64, 6), _unit(50, 64, 7)
    truth = qb.search(q, x, qb.K)
    narrow = qb.search(qb.prefix(q, 16), qb.prefix(x, 16), qb.K)
    wide = qb.search(qb.prefix(q, 16), qb.prefix(x, 16), 4 * qb.K)
    assert (qb.recall(truth, qb.rescore(q, x, wide, qb.K)) >= qb.recall(truth, narrow)).all()


def test_sign_codes_rank_by_hamming_distance() -> None:
    a, b = qb.signs(_unit(6, 32, 8)), qb.signs(_unit(9, 32, 9))
    hamming = (a[:, None, :] != b[None, :, :]).sum(axis=2)
    assert np.array_equal(a @ b.T, 32 - 2 * hamming)


def test_int8_error_is_at_most_half_a_step_per_dimension() -> None:
    x = _unit(500, 24, 10)
    step = (x.max(axis=0) - x.min(axis=0)) / 255.0
    assert (np.abs(qb.int8_roundtrip(x) - x) <= step / 2 + 1e-6).all()


def test_full_width_prefix_and_a_full_rotation_lose_nothing() -> None:
    """The Matryoshka controls are sound: keeping every dimension is the identity, and an
    orthonormal rotation preserves every dot product, so a loss at 256 is the 256's own."""
    x, q = _unit(400, 32, 11), _unit(30, 32, 12)
    truth = qb.search(q, x, qb.K)
    assert qb.recall(truth, qb.search(qb.prefix(q, 32), qb.prefix(x, 32), qb.K)).min() == 1.0
    basis = qb.orthonormal(32, 32, np.random.default_rng(13))
    rotated = qb.search(qb.normalize(np.asarray(q @ basis, dtype=np.float32)),
                        qb.normalize(np.asarray(x @ basis, dtype=np.float32)), qb.K)
    assert qb.recall(truth, rotated).min() == 1.0


def test_summary_reports_mean_interval_worst_and_first_hit() -> None:
    r = np.array([1.0] * 30 + [0.5] * 10)
    top1 = np.array([True] * 36 + [False] * 4)
    s = qb.summarize(r, top1, np.random.default_rng(14))
    assert (s["n"], s["recall@10"], s["perfect"], s["min"], s["top1"]) == (40, 0.875, 0.75, 0.5,
                                                                             0.9)
    assert s["ci95"][0] <= 0.875 <= s["ci95"][1]
    assert "ci95" not in qb.summarize(r[:5], top1[:5], np.random.default_rng(15))
