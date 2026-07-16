"""The evaluation harness (dn-evaluation-harness) — instruments → harness → report over one
substrate. This package is the harness's own machinery: the eval-results store (the keystone), the
metric registry, and (later plans) the report generator. Stores here are their own Σ — outside the
complex, ∉ `MIRROR_READABLE` (§2.10).
"""

from eval.harness.store import EvalKey, EvalResultsStore, Reading, open_eval_store

__all__ = ["EvalKey", "EvalResultsStore", "Reading", "open_eval_store"]
