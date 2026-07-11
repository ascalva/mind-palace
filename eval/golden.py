"""The frozen golden set — a fixed reference for capability drift (BUILD-SPEC §15, Invariant 9).

A genuine fixed point must be reproducible and hand-blessed, so the golden set ships with
its OWN synthetic fixture corpus (`eval/golden/corpus/`) rather than pointing at the
owner's live vault. The vault is private and changes over time, which would make it
useless as a frozen anchor and would leak private content into the repo. The fixture
corpus, the queries (`golden_set.json`), and the blessed baseline (`baseline.json`) are
edited only by the owner, on purpose (Invariant 9 — never auto-modified by any agent).

The harness is decoupled from the model by a `Retriever` callable: (query, k) -> rows,
each row a dict with at least `"title"` and optionally `"_distance"`. This lets the metric
logic be unit-tested with a stub retriever and run live against the real embedder through
the exact same code path.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from eval.metrics import mean_cosine_distance, recall_at_k, set_overlap

GOLDEN_DIR = Path(__file__).resolve().parent / "golden"
CORPUS_DIR = GOLDEN_DIR / "corpus"
GOLDEN_SET_PATH = GOLDEN_DIR / "golden_set.json"
BASELINE_PATH = GOLDEN_DIR / "baseline.json"

# (query, k) -> retrieved rows (each at least {"title": ..., optionally "_distance": ...})
Retriever = Callable[[str, int], Sequence[dict[str, Any]]]


@dataclass(frozen=True)
class GoldenQuery:
    id: str
    query: str
    expected: frozenset[str]
    k: int


@dataclass(frozen=True)
class QueryResult:
    id: str
    retrieved: tuple[str, ...]
    recall_at_k: float
    overlap: float
    mean_distance: float


@dataclass(frozen=True)
class GoldenReport:
    per_query: tuple[QueryResult, ...]

    @property
    def recall_at_k(self) -> float:
        return _mean(r.recall_at_k for r in self.per_query)

    @property
    def overlap(self) -> float:
        return _mean(r.overlap for r in self.per_query)

    @property
    def mean_distance(self) -> float:
        return _mean(r.mean_distance for r in self.per_query)

    def as_metrics(self) -> dict[str, float]:
        return {
            "recall_at_k": round(self.recall_at_k, 4),
            "overlap": round(self.overlap, 4),
            "mean_distance": round(self.mean_distance, 4),
        }


def _mean(xs: Iterable[float]) -> float:
    xs = list(xs)
    return sum(xs) / len(xs) if xs else 0.0


def load_golden_set(path: Path = GOLDEN_SET_PATH) -> tuple[GoldenQuery, ...]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return tuple(
        GoldenQuery(
            id=q["id"],
            query=q["query"],
            expected=frozenset(q["expected"]),
            k=int(q.get("k", 5)),
        )
        for q in data["queries"]
    )


def load_baseline(path: Path = BASELINE_PATH) -> dict[str, float]:
    return json.loads(path.read_text(encoding="utf-8"))["metrics"]


def evaluate(golden: Sequence[GoldenQuery], retriever: Retriever) -> GoldenReport:
    """Run every golden query through `retriever` and compute per-query + mean metrics."""
    results: list[QueryResult] = []
    for gq in golden:
        rows = list(retriever(gq.query, gq.k))
        titles = tuple(r.get("title", "") for r in rows)
        distances = [float(r["_distance"]) for r in rows if "_distance" in r]
        expected = set(gq.expected)
        results.append(
            QueryResult(
                id=gq.id,
                retrieved=titles,
                recall_at_k=recall_at_k(expected, titles, gq.k),
                overlap=set_overlap(expected, titles, gq.k),
                mean_distance=mean_cosine_distance(distances),
            )
        )
    return GoldenReport(per_query=tuple(results))


def regressions(report: GoldenReport, baseline: dict[str, float]) -> list[str]:
    """Metrics that fell below the blessed baseline. recall/overlap are higher-is-better
    (must not drop); mean_distance is lower-is-better (must not rise past its tolerance).
    The capability gate (§15): an approved change must not regress these against the
    frozen anchor."""
    m = report.as_metrics()
    out: list[str] = []
    if m["recall_at_k"] + 1e-9 < baseline["recall_at_k"]:
        out.append("recall_at_k")
    if m["overlap"] + 1e-9 < baseline["overlap"]:
        out.append("overlap")
    distance_tol = baseline.get("distance_tol", 0.05)
    if m["mean_distance"] > baseline["mean_distance"] + distance_tol:
        out.append("mean_distance")
    return out
