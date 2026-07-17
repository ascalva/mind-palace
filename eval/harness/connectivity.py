r"""CN-2 instrument: σ* readings over the certified cut — the thin harness over `core.graph`.

**Placement (bp-065, `dn-core-graph-instruments` P1/P2/P5).** The MATHEMATICS — σ*/MST, the
grid snap, the CN-1 index object, the cut acquisition — lives in `core/graph/sigma_star.py`
(graph math is core vocabulary; the arrow is `eval → core.graph`, never the reverse). This
module is the *instrument*: evidence pins, spec/corpus keying, the aggregate summary, and the
idempotent-by-key eval readings. Every relocated name is re-exported here (P5 compatibility
contract — downstream pins and the bp-059 test suites resolve unchanged). Design:
`docs/design-notes/connectivity-instruments.md` CN-1 + CN-2 (RATIFIED; placement amended by
`dn-core-graph-instruments`, warrant finding-0101).

**Registration (fibers precedent, bp-059 §4).** `EvalResultsStore.put()` does NOT gate on
registration (`store.py` imports no registry), and `registry.py` is out of scope. So — exactly
as FB-1 wrote `sigma_persistence.*` before bp-054 registered them (`fibers.py` head-note) —
this instrument emits `sigma_star.*` readings with `type_tag="SigmaStar"` now; registering the
names + the tag vocabulary is a separate future act (a bp-054-style companion). Recorded here
so it never reads as a violation.

**Not a recall signal (finding-0096).** σ* reports thresholds + chains; it does NOT feed
golden_recall or claim a σ-discriminating recall improvement. finding-0096 established
golden_recall saturates at this corpus scale — σ*'s falsifiers are the ultrametric inequality
and MST≡union-find agreement, both scale-free STRUCTURAL checks, never a recall booster.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from dataclasses import dataclass, field
from statistics import mean, median

from core.graph.sigma_star import (
    ConnIndex,
    CrossingEdgeError,
    MaxSpanningForest,
    SigmaStar,
    acquire_mirror_cut,
    build_max_spanning_tree,
    cut_fingerprint,
    pairwise_sigma_star,
    sigma_star,
)
from core.dreaming.graph import MirrorGraph
from core.mirror import MirrorView
from core.temporal.spine import Spine
from eval.harness.store import EvalKey, EvalResultsStore, Reading

__all__ = [
    "METRIC_FRAC_CONNECTED",
    "METRIC_MAX",
    "METRIC_MEAN",
    "METRIC_N_PAIRS",
    "METRIC_P50",
    "ConnEvidence",
    "ConnIndex",            # re-export (core.graph.sigma_star)
    "ConnResult",
    "CrossingEdgeError",    # re-export (core.graph.sigma_star)
    "MaxSpanningForest",    # re-export (core.graph.sigma_star)
    "SigmaStar",            # re-export (core.graph.sigma_star)
    "acquire_mirror_cut",   # re-export (core.graph.sigma_star)
    "build_max_spanning_tree",  # re-export (core.graph.sigma_star)
    "cut_fingerprint",      # re-export (core.graph.sigma_star)
    "pairwise_sigma_star",  # re-export (core.graph.sigma_star)
    "run_connectivity",
    "sigma_star",           # re-export (core.graph.sigma_star)
]

# --- family constants ---------------------------------------------------------------------------
_INSTRUMENT = "connectivity/v1"           # the spec_hash instrument tag (id + version)
_TYPE_TAG = "SigmaStar"                    # the result-typing tag (unregistered; see head-note)

# The aggregate metric names (σ* distribution over the pairwise summary). Unregistered by design
# (see head-note); a bp-054-style companion registers them later.
METRIC_MEAN = "sigma_star.mean"
METRIC_P50 = "sigma_star.p50"
METRIC_MAX = "sigma_star.max"
METRIC_FRAC_CONNECTED = "sigma_star.frac_connected"
METRIC_N_PAIRS = "sigma_star.n_pairs"


@dataclass(frozen=True)
class ConnEvidence:
    """The reconstruction pins recorded in every reading's `evidence_ref` (the `FibersEvidence`
    pattern, copied verbatim): the declared grid, the caller's base fingerprint (config/embedding
    regime), and the certified cut's content fingerprint. Serialized so the number stays
    independently recoverable and a later grid / cut drift is detectable."""

    grid: tuple[float, ...]
    base_fingerprint: str
    cut_fingerprint: str

    def as_ref(self) -> str:
        return json.dumps(
            {
                "instrument": _INSTRUMENT,
                "grid": list(self.grid),
                "base_fingerprint": self.base_fingerprint,
                "cut_fingerprint": self.cut_fingerprint,
            },
            sort_keys=True,
            separators=(",", ":"),
        )


def _corpus_ref(forest: MaxSpanningForest) -> str:
    """The corpus coordinate (the store's corpus-growth confound key): a content digest of the node
    set the reading measured. Deterministic — the sorted note digests hashed. Distinct corpora key
    distinctly; the same notes re-read key identically (idempotent-by-key writes)."""
    payload = "‖".join(sorted(forest.digests))
    return "conn:" + hashlib.sha256(payload.encode()).hexdigest()


def _spec_hash(grid: Sequence[float]) -> str:
    """`spec_hash = sha256(instrument ‖ grid-descriptor)` — instrument id+version, then the
    declared grid (the battery param, `store.py:32`). A different grid keys DISTINCTLY (the Res(π)
    discipline — comparisons across unacknowledged rulers cannot collapse)."""
    descriptor = json.dumps({"grid": list(grid)}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(f"{_INSTRUMENT}‖{descriptor}".encode()).hexdigest()


# ── the entry point + the pairwise summary + readings ───────────────────────────────────────────


@dataclass
class ConnResult:
    """The instrument's verdict. `index` is the CN-1 (grid, cut) coordinate; `evidence` the pins;
    the `pairs` are the full pairwise σ* summary (report artifact); `aggregates` the distribution
    readings written; `readings_written` counts NEW eval-store rows (a re-run yields 0 — the store
    dedups by key). `notes` records every coverage gap (no silent caps)."""

    index: ConnIndex
    evidence: ConnEvidence
    corpus_ref: str
    spec_hash: str
    pairs: tuple[SigmaStar, ...]
    aggregates: dict[str, float]
    readings_written: int
    notes: tuple[str, ...] = field(default_factory=tuple)


def _aggregate(pairs: Sequence[SigmaStar]) -> tuple[dict[str, float], tuple[str, ...]]:
    """The σ* distribution summary over the pairwise readings. mean/p50/max are over CONNECTED pairs
    only (σ* not None); `frac_connected` and `n_pairs` are always present. Returns (aggregates,
    coverage-notes)."""
    connected = [p.sigma_star for p in pairs if p.sigma_star is not None]
    notes: list[str] = []
    agg: dict[str, float] = {
        METRIC_N_PAIRS: float(len(pairs)),
        METRIC_FRAC_CONNECTED: (len(connected) / len(pairs)) if pairs else 0.0,
    }
    if connected:
        agg[METRIC_MEAN] = float(mean(connected))
        agg[METRIC_P50] = float(median(connected))
        agg[METRIC_MAX] = float(max(connected))
    else:
        notes.append(
            "no pair connects within the grid — mean/p50/max omitted "
            "(only frac_connected=0 + n_pairs written)."
        )
    return agg, tuple(notes)


def run_connectivity(
    *,
    view: MirrorView,
    spine: Spine,
    grid: Sequence[float],
    eval_store: EvalResultsStore,
    base_fingerprint: str,
) -> ConnResult:
    """Build the σ-graph over the CURRENT MirrorView at the loosest grid threshold, acquire the
    latest certified mirror cut (fail-closed), compute the pairwise σ* summary, and write the
    aggregate readings keyed with the `ConnEvidence` ref. Reads only the view + spine; writes only
    additive, idempotent-by-key eval Readings (never re-keys, never overwrites). n≤1 corpora emit
    no readings and note it (a sanctioned empty outcome, bp-059 §10)."""
    grid = tuple(sorted(float(g) for g in grid))
    if not grid:
        raise ValueError("run_connectivity: empty σ-grid — an instrument must declare its grid")

    cut = acquire_mirror_cut(spine)                       # fail-closed BEFORE any graph work
    evidence = ConnEvidence(
        grid=grid, base_fingerprint=base_fingerprint, cut_fingerprint=cut_fingerprint(cut)
    )
    index = ConnIndex(grid=grid, cut=cut)

    graph = MirrorGraph.build(view, sigma=grid[0])        # loosest grid = densest edges
    if graph.n <= 1:
        return ConnResult(
            index=index, evidence=evidence,
            corpus_ref=_corpus_ref(build_max_spanning_tree(graph)),
            spec_hash=_spec_hash(grid), pairs=(), aggregates={}, readings_written=0,
            notes=(f"corpus n={graph.n} ≤ 1: no pairs — no readings emitted (plan §10).",),
        )

    forest = build_max_spanning_tree(graph)
    pairs = pairwise_sigma_star(forest, grid=grid)
    aggregates, agg_notes = _aggregate(pairs)
    corpus_ref = _corpus_ref(forest)
    spec_hash = _spec_hash(grid)

    key = EvalKey(spec_hash=spec_hash, corpus_ref=corpus_ref,
                  config_fingerprint=base_fingerprint, seed=0)
    ref = evidence.as_ref()
    written = 0
    for name, value in aggregates.items():
        if eval_store.put(
            Reading(key=key, metric_name=name, value=float(value),
                    type_tag=_TYPE_TAG, evidence_ref=ref)
        ):
            written += 1

    return ConnResult(
        index=index, evidence=evidence, corpus_ref=corpus_ref, spec_hash=spec_hash,
        pairs=pairs, aggregates=aggregates, readings_written=written, notes=agg_notes,
    )
