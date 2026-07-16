"""Deterministic capability metrics for the frozen golden set (BUILD-SPEC §15).

Pure functions over (expected, retrieved) — no model, no I/O. recall@k, set overlap
(Jaccard), and mean cosine distance. These are the deterministic half of the testing
fixed point: the same queries against the same fixture corpus must score the same way,
so capability drift is measurable against a hand-blessed baseline (Invariant 9).

Absorbed into the evaluation harness (dn-evaluation-harness §2.2): these three functions are the
registered *golden-recall* metric family — their registration lives in `eval/harness/registry.py`
(the single metric namespace). Their signatures are unchanged; this module stays importable and its
callers are untouched. The registry owns *what these metrics are*; this module owns *how they run*.
"""

from __future__ import annotations

from collections.abc import Sequence

__all__ = ["recall_at_k", "set_overlap", "mean_cosine_distance"]


def recall_at_k(expected: set[str], retrieved: Sequence[str], k: int) -> float:
    """Fraction of the expected items present in the top-k retrieved. 1.0 if nothing is
    expected (vacuously satisfied)."""
    if not expected:
        return 1.0
    topk = set(retrieved[:k])
    return len(expected & topk) / len(expected)


def set_overlap(expected: set[str], retrieved: Sequence[str], k: int) -> float:
    """Jaccard overlap between the expected set and the top-k retrieved set."""
    topk = set(retrieved[:k])
    union = expected | topk
    return len(expected & topk) / len(union) if union else 1.0


def mean_cosine_distance(distances: Sequence[float]) -> float:
    """Mean of returned hit distances (LanceDB cosine `_distance`; lower = closer).
    0.0 for an empty result set."""
    distances = list(distances)
    return sum(distances) / len(distances) if distances else 0.0
