r"""CN-3/CN-4 instrument: (σ,t) conductance readings — the thin harness over `core.graph`.

**Placement (bp-065, `dn-core-graph-instruments` P1/P2/P5).** The MATHEMATICS — the (σ,t)
profile family, the churn change-of-measure, χ_s/depth-budget, the reconnection scan — lives
in `core/graph/conductance.py` on `core/complex`'s single Laplacian (P3). This module is the
*instrument*: the (σ,t)-extended evidence pin, spec/corpus keying, the aggregate summary, and
the idempotent-by-key eval readings. Every relocated name is re-exported here (P5) so the
bp-060-lineage tests and downstream pins resolve unchanged. Design:
`docs/design-notes/connectivity-instruments.md` CN-3 + CN-4 (RATIFIED; placement amended by
`dn-core-graph-instruments`, warrant finding-0101; built work harvested from bp-060's branch).

**The historical-graph gap (inherited from bp-059).** `MirrorGraph.build` takes no cut and
`MirrorView` has no cut-restriction, so v1 pins to the LATEST certified cut. The Δ-scan +
leave-one-out attribution is fully testable on SYNTHETIC cut-pairs; the real-corpus forward
scan is PARTIAL until the store holds ≥2 forward-sampled cuts with retained edge sets (bp-060
§11) — `run_conductance` reports "no cut pair yet" and NOTES it (a sanctioned partial), never
reconstructing a historical graph.

**Registration (fibers precedent).** As with `connectivity.py`, `conductance.*` readings ship
with `type_tag="Conductance"` unregistered; a bp-054-style companion registers them later.

**Not a recall signal (finding-0096).** The falsifiers are Rayleigh monotonicity, the
degeneracy self-diagnostic, and a synthetic decay-only null — all scale-free STRUCTURAL
checks, never a golden_recall booster.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from dataclasses import dataclass, field, replace

import numpy as np

from core.dreaming.graph import MirrorGraph
from core.graph.conductance import (
    CONDUCTANCE_THRESH,
    ConductanceProfile,
    ReconnectionEvent,
    chi_s,
    chi_s_all,
    churn_weight,
    effective_conductance,
    reconnection_scan,
    sigma_t_profile,
)
from core.graph.sigma_star import ConnIndex, acquire_mirror_cut, cut_fingerprint
from core.mirror import MirrorView
from core.temporal.spine import Spine
from eval.harness.connectivity import ConnEvidence
from eval.harness.store import EvalKey, EvalResultsStore, Reading

__all__ = [
    "CONDUCTANCE_THRESH",     # re-export (core.graph.conductance)
    "METRIC_DEGENERACY",
    "METRIC_FRAC_CONNECTED",
    "METRIC_MEAN",
    "METRIC_N_PAIRS",
    "ConductanceEvidence",
    "ConductanceProfile",     # re-export (core.graph.conductance)
    "ConductanceResult",
    "ReconnectionEvent",      # re-export (core.graph.conductance)
    "chi_s",                  # re-export (core.graph.conductance)
    "chi_s_all",              # re-export (core.graph.conductance)
    "churn_weight",           # re-export (core.graph.conductance)
    "effective_conductance",  # re-export (core.graph.conductance)
    "reconnection_scan",      # re-export (core.graph.conductance)
    "run_conductance",
    "sigma_t_profile",        # re-export (core.graph.conductance)
]

# --- family + instrument constants --------------------------------------------------------------
_INSTRUMENT = "conductance/v1"          # the spec_hash instrument tag (id + version)
_TYPE_TAG = "Conductance"               # the result-typing tag (unregistered; conn precedent)

# The aggregate metric names (the conductance distribution over the pairwise profiles). Unregistered
# by design (connectivity head-note precedent); a bp-054-style companion registers them later.
METRIC_MEAN = "conductance.mean"
METRIC_DEGENERACY = "conductance.degeneracy_diag"
METRIC_FRAC_CONNECTED = "conductance.frac_connected"
METRIC_N_PAIRS = "conductance.n_pairs"


# ── the family evidence pin, extended with the SECOND index (the t-grid) ─────────────────────────


@dataclass(frozen=True)
class ConductanceEvidence:
    """The reconstruction pins recorded in every reading's `evidence_ref`. Wraps bp-059's
    `ConnEvidence` VERBATIM (the σ-grid + the caller's base fingerprint + the certified cut's
    content fingerprint) and ADDS the `t_grid` — because the (σ,t) profile is indexed by BOTH grids,
    so both must be declared in evidence (the CN-1 index discipline; bp-060 §3 risk-b: "declare a
    t-grid in evidence, like the σ-grid; both pinned"). Serialized so a later grid / cut drift stays
    independently detectable."""

    conn: ConnEvidence                # σ-grid + base_fingerprint + cut_fingerprint (bp-059)
    t_grid: tuple[float, ...]         # the second index the (σ,t) profile declares

    def as_ref(self) -> str:
        return json.dumps(
            {
                "instrument": _INSTRUMENT,
                "sigma_grid": list(self.conn.grid),
                "t_grid": list(self.t_grid),
                "base_fingerprint": self.conn.base_fingerprint,
                "cut_fingerprint": self.conn.cut_fingerprint,
            },
            sort_keys=True,
            separators=(",", ":"),
        )


# ── the entry point + the pairwise aggregate + readings ─────────────────────────────────────────


@dataclass
class ConductanceResult:
    """The instrument's verdict. `index` is the CN-1 (grid, cut) coordinate; `evidence` the pins;
    `profiles` the full (σ,t) pairwise report (each carrying `degeneracy_diag` + `chi_s`);
    `reconnections` the verified events (empty in v1 — one cut, no pair — see `notes`);
    `aggregates` the distribution readings written; `readings_written` counts NEW rows (a re-run
    yields 0 — idempotent by key). `notes` records every coverage gap (no silent caps)."""

    index: ConnIndex
    evidence: ConductanceEvidence
    corpus_ref: str
    spec_hash: str
    profiles: tuple[ConductanceProfile, ...]
    reconnections: tuple[ReconnectionEvent, ...]
    aggregates: dict[str, float]
    readings_written: int
    notes: tuple[str, ...] = field(default_factory=tuple)


def _corpus_ref(digests: Sequence[str]) -> str:
    """The corpus coordinate (the store's corpus-growth confound key): a content digest of the node
    set measured — the sorted note digests hashed. Idempotent-by-key: the same notes key identically
    (mirrors `connectivity._corpus_ref`, kept independent to avoid importing a private helper)."""
    payload = "‖".join(sorted(digests))
    return "cond:" + hashlib.sha256(payload.encode()).hexdigest()


def _spec_hash(sigma_grid: Sequence[float], t_grid: Sequence[float]) -> str:
    """`spec_hash = sha256(instrument ‖ (σ-grid, t-grid))` — a DIFFERENT grid keys distinctly (the
    Res(π) discipline; the profile is (σ,t)-indexed so BOTH grids are battery params)."""
    descriptor = json.dumps(
        {"sigma_grid": [float(s) for s in sigma_grid], "t_grid": [float(t) for t in t_grid]},
        sort_keys=True, separators=(",", ":"),
    )
    return hashlib.sha256(f"{_INSTRUMENT}‖{descriptor}".encode()).hexdigest()


def _aggregate(profiles: Sequence[ConductanceProfile]) -> tuple[dict[str, float], tuple[str, ...]]:
    """The conductance distribution summary over the pairwise profiles at the loosest σ. `mean` is
    over CONNECTED pairs only (finite R_eff); `degeneracy_diag`, `frac_connected`, `n_pairs` are
    always present (degeneracy_diag is the single graph-level self-diagnostic every profile shares).
    Returns (aggregates, coverage-notes)."""
    conductances = [1.0 / p.r_eff_loosest for p in profiles if p.connected_at_loosest]
    notes: list[str] = []
    agg: dict[str, float] = {
        METRIC_N_PAIRS: float(len(profiles)),
        METRIC_FRAC_CONNECTED: (len(conductances) / len(profiles)) if profiles else 0.0,
    }
    # degeneracy_diag is stamped identically on every profile (graph-level); read one.
    agg[METRIC_DEGENERACY] = profiles[0].degeneracy_diag if profiles else 0.0
    if conductances:
        agg[METRIC_MEAN] = float(np.mean(conductances))
    else:
        notes.append(
            "no pair connects within the grid — mean omitted "
            "(only degeneracy_diag/frac_connected/n_pairs written)."
        )
    return agg, tuple(notes)


def run_conductance(
    *,
    view: MirrorView,
    spine: Spine,
    sigma_grid: Sequence[float],
    t_grid: Sequence[float],
    eval_store: EvalResultsStore,
    base_fingerprint: str,
) -> ConductanceResult:
    """Build the σ-graph over the CURRENT MirrorView at the loosest grid threshold, acquire the
    latest certified mirror cut (fail-closed via `core.graph.sigma_star.acquire_mirror_cut`),
    compute the (σ,t) profiles with χ_s attached, and write the aggregate readings keyed with the
    `ConnEvidence` ref. Reads only the view + spine; writes only additive, idempotent-by-key eval
    Readings.

    The reconnection forward scan is a **sanctioned partial** (bp-060 §11): v1 has only the latest
    cut (no historical graph — bp-059's parked `MirrorView` downset prerequisite), so it reports
    "no cut pair yet" and NOTES it, never reconstructing a past graph. `reconnection_scan` is
    exercised on synthetic cut-pairs in the quality battery. n≤1 corpora emit no readings and
    note it."""
    sigma_grid = tuple(sorted(float(s) for s in sigma_grid))
    t_grid = tuple(float(t) for t in t_grid)
    if not sigma_grid:
        raise ValueError("run_conductance: empty σ-grid — an instrument must declare its grid")
    if not t_grid:
        raise ValueError("run_conductance: empty t-grid — (σ,t)-indexed, both grids pinned")

    cut = acquire_mirror_cut(spine)                          # fail-closed BEFORE any graph work
    evidence = ConductanceEvidence(
        conn=ConnEvidence(grid=sigma_grid, base_fingerprint=base_fingerprint,
                          cut_fingerprint=cut_fingerprint(cut)),
        t_grid=t_grid,
    )
    index = ConnIndex(grid=sigma_grid, cut=cut)
    spec_hash = _spec_hash(sigma_grid, t_grid)

    graph = MirrorGraph.build(view, sigma=sigma_grid[0])     # loosest grid = densest edges
    digests = [graph.digest(i) for i in range(graph.n)]
    corpus_ref = _corpus_ref(digests)
    partial_note = (
        "reconnection: no cut pair yet — v1 holds only the latest certified cut (no historical "
        "graph; bp-059's MirrorView downset is parked). Synthetic cut-pairs verify the scan."
    )

    if graph.n <= 1:
        return ConductanceResult(
            index=index, evidence=evidence, corpus_ref=corpus_ref, spec_hash=spec_hash,
            profiles=(), reconnections=(), aggregates={}, readings_written=0,
            notes=(f"corpus n={graph.n} ≤ 1: no pairs — no readings emitted (plan §10).",
                   partial_note),
        )

    chi = chi_s_all(spine)
    profiles = tuple(
        replace(p, chi_s=dict(chi))
        for p in sigma_t_profile(graph, sigma_grid=sigma_grid, t_grid=t_grid,
                                 thresh=CONDUCTANCE_THRESH)
    )
    aggregates, agg_notes = _aggregate(profiles)

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

    return ConductanceResult(
        index=index, evidence=evidence, corpus_ref=corpus_ref, spec_hash=spec_hash,
        profiles=profiles, reconnections=(), aggregates=aggregates, readings_written=written,
        notes=agg_notes + (partial_note,),
    )
