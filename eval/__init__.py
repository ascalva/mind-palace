"""Frozen golden sets, deterministic metrics, baselines, drift (BUILD-SPEC §15).

The capability fixed point: a hand-blessed golden set (queries + a synthetic fixture
corpus) diffed on every relevant change via deterministic metrics (recall@k, set overlap,
cosine distance). The behavioral fixed point (the Constitution pre-return check) lives in
`core.selfcheck`; its small-model judge + baseline-snapshot machinery lands in Phase 10.
"""

from eval.golden import (
    GoldenQuery,
    GoldenReport,
    QueryResult,
    evaluate,
    load_baseline,
    load_golden_set,
    regressions,
)
from eval.metrics import mean_cosine_distance, recall_at_k, set_overlap

__all__ = [
    "GoldenQuery",
    "GoldenReport",
    "QueryResult",
    "evaluate",
    "load_baseline",
    "load_golden_set",
    "mean_cosine_distance",
    "recall_at_k",
    "regressions",
    "set_overlap",
]
