"""F1-variant fixtures for the σ-gate F9 validation (bp-057 Item 2).

Same statistical philosophy as F1 (`test_dreamer_quality.py`): planted structure with KNOWN
cosines + a controlled noise process; tests assert BOUNDS and RELATIONSHIPS, never exact values.
Model-free and deterministic — the corpora are hand-placed unit vectors whose pairwise cosines are
exact by construction, swept through the BUILT `ShadowRunner`/`SweepEngine` (the phase7 community
lens) at an m-cell σ grid; `run_fibers` (bp-050) then produces the `ClaimFiber`s the gate tiers.

Two structures over the σ-range `[0.55, 0.75]` (lever `dream_rnd_sigma`):

* **Planted** — two ISOLATED tight clusters (within-cluster cos ≈ 0.99; every cross cosine 0). Each
  survives the whole grid with ONE identity ⇒ pers = 1.0 ⇒ SETTLED. (criterion ii)

* **Noise = a MORPHING STAR** centred at `nA` with graded edge cosines to nB, nC1..nC4 of
  0.76, 0.72, 0.67, 0.62, 0.57 — each side-node in its OWN orthogonal dimension, so side-nodes never
  inter-connect (max side cosine 0.76·0.72 ≈ 0.547 < σ_lo = 0.55). As σ falls past each threshold
  the connected component centred on `nA` GAINS one node ⇒ a DISTINCT support set (claim identity)
  at every cell ⇒ each noise identity persists on exactly ONE cell (pers = 1/m) ⇒ RETAINED.

The honest multi-scale point: cos(nA,nB) = 0.76 > σ_hi, so `{nA,nB}` is a noise false positive even
at the STRICTEST cell (σ = 0.75) — yet it MORPHS at lower σ, so it is never persistent. Every single
σ therefore carries a noise FP (single-σ precision < 1 at every scale, incl. the strictest), while
persistence-tiering filters all of it — the strong form of criterion (iii).
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from config.loader import get_config
from core.complex.temporal import SnapshotStore
from core.provenance import Provenance
from core.stores.runledger import RunLedger
from eval.drift import DriftConfig
from eval.golden import GoldenQuery
from eval.harness.fibers import ClaimFiber, run_fibers
from eval.harness.store import EvalResultsStore
from eval.harness.sweep import SweepEngine, parse_spec_text
from ops.levers import get_lever

_DIM = 10   # enough orthogonal axes for 2 planted 2-clusters (dims 0-3) + a 6-node star (dims 4-9)


def _unit(components: dict[int, float]) -> list[float]:
    """A vector with the given index→value components (zero elsewhere), normalised to unit length so
    the constructed cosines are exact after the harness re-normalises."""
    v = [0.0] * _DIM
    for i, x in components.items():
        v[i] = x
    norm = math.sqrt(sum(x * x for x in v))
    return [x / norm for x in v]


def _pair(dim_base: int, side_dim: int, cos: float) -> list[float]:
    """A unit vector at angle `arccos(cos)` from `e[dim_base]`, tilted into `e[side_dim]` — so its
    cosine with `e[dim_base]` is exactly `cos` and its cosine with any other basis axis is 0."""
    return _unit({dim_base: cos, side_dim: math.sqrt(max(0.0, 1.0 - cos * cos))})


def _row(digest: str, vec: list[float]) -> dict[str, Any]:
    return {"digest": digest, "title": digest, "provenance": "authored-solo", "vector": vec}


# --- planted: two isolated tight clusters (cos ≈ 0.99 within; orthogonal between + to noise) ---
_PLANTED_COS = 0.99
PLANTED_ROWS: list[dict[str, Any]] = [
    _row("pA1", _unit({0: 1.0})),
    _row("pA2", _pair(0, 1, _PLANTED_COS)),
    _row("pB1", _unit({2: 1.0})),
    _row("pB2", _pair(2, 3, _PLANTED_COS)),
]
PLANTED_DIGESTS: frozenset[str] = frozenset({"pA1", "pA2", "pB1", "pB2"})

# --- noise: the morphing star (graded edge cosines from the centre nA) ---
# cosines chosen strictly BETWEEN the m=5 grid points [0.55,0.60,0.65,0.70,0.75] so edge decisions
# are float-robust (each is ≥ 0.02 from any grid point).
NOISE_ROWS: list[dict[str, Any]] = [
    _row("nA", _unit({4: 1.0})),        # the star centre
    _row("nB", _pair(4, 5, 0.76)),      # > σ_hi ⇒ {nA,nB} present even at the strictest cell
    _row("nC1", _pair(4, 6, 0.72)),     # joins at σ ≤ 0.72
    _row("nC2", _pair(4, 7, 0.67)),     # joins at σ ≤ 0.67
    _row("nC3", _pair(4, 8, 0.62)),     # joins at σ ≤ 0.62
    _row("nC4", _pair(4, 9, 0.57)),     # joins at σ ≤ 0.57 (loosest cell only)
]
NOISE_DIGESTS: frozenset[str] = frozenset({"nA", "nB", "nC1", "nC2", "nC3", "nC4"})

PLANTED_IN_NOISE_ROWS: list[dict[str, Any]] = [*PLANTED_ROWS, *NOISE_ROWS]


class _RowSource:
    """The mirror row source the ShadowRunner projects (matches the bp-050 integration harness)."""

    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows

    def all_rows(self, *, provenances: Any = None) -> list[dict[str, Any]]:
        if provenances is None:
            return list(self._rows)
        allowed = {Provenance(p).value for p in provenances}
        return [r for r in self._rows if r.get("provenance") in allowed]


def _fake_retriever(query: str, k: int) -> list[dict[str, Any]]:
    return [{"title": "A1", "_distance": 0.1}, {"title": "B1", "_distance": 0.2}][:k]


def _spec_text(resolution: int) -> str:
    return f"""
[sweep.f9_sigma_gate]
levers = {{ dream_rnd_sigma = "full" }}
resolution = {resolution}
pipelines = ["phase7"]
corpus = "mirror-snapshot"
seeds = 1
metrics = ["golden_recall", "drift_D"]
objective = "golden_recall"
mode = "propose"
"""


def drive_phase7_sweep(
    rows: list[dict[str, Any]], *, resolution: int = 5
) -> tuple[RunLedger, EvalResultsStore, list[float]]:
    """Sweep `rows` through the BUILT `ShadowRunner` (phase7 lens) over an m=`resolution` σ grid —
    exactly as an overnight sweep leaves the ledger + eval store, in-memory. Returns them + the
    grid."""
    spec = parse_spec_text(_spec_text(resolution))
    ledger = RunLedger(":memory:")
    eval_store = EvalResultsStore(":memory:")
    engine = SweepEngine(
        spec=spec,
        base_config=get_config(),
        eval_store=eval_store,
        ledger=ledger,
        store=_RowSource(rows),
        retriever=_fake_retriever,
        golden=[GoldenQuery(id="q1", query="alpha", expected=frozenset({"A1"}), k=2)],
        baseline={"recall_at_k": 0.5, "overlap": 0.4, "mean_distance": 0.2},
        drift_cfg=DriftConfig(),
        snapshots=SnapshotStore(Path(":memory:")),
    )
    engine.drive()
    return ledger, eval_store, [float(v) for v in spec.grid()]


def phase7_fibers(
    rows: list[dict[str, Any]], *, resolution: int = 5
) -> tuple[tuple[ClaimFiber, ...], RunLedger, list[float]]:
    """Drive the sweep and score every phase7 claim across it → the `ClaimFiber`s (the gate's
    input), plus the ledger (for ground-truth labels + confidence) and the grid."""
    ledger, eval_store, grid = drive_phase7_sweep(rows, resolution=resolution)
    result = run_fibers(
        ledger=ledger, eval_store=eval_store, base_config=get_config(),
        lever=get_lever("dream_rnd_sigma"), grid=grid,
    )
    return result.fibers.get("phase7", ()), ledger, grid


def label_for(support: set[str]) -> str:
    """Ground truth for a community claim by its support membership: TRUE `"planted"` iff support
    is entirely planted-cluster digests; `"noise"` iff it touches any noise digest; else `"other"`
    (planted and noise never share a component, so `"other"` should not occur)."""
    if support and support <= PLANTED_DIGESTS:
        return "planted"
    if support & NOISE_DIGESTS:
        return "noise"
    return "other"


def ledger_labels(ledger: RunLedger) -> dict[str, str]:
    """`claim_id → label` over every phase7 community claim in the ledger (supports read from the
    run ledger — the `ClaimFiber` carries no support of its own)."""
    out: dict[str, str] = {}
    for run in ledger.runs(pipeline="phase7"):
        for c in ledger.claims(run_id=str(run["run_id"])):
            support = set(json.loads(str(c["support_json"])))
            out[str(c["claim_id"])] = label_for(support)
    return out


def ledger_confidence(ledger: RunLedger) -> dict[str, float]:
    """`claim_id → confidence` from the phase7 ledger (0.0 for the un-adjudicated community lens).
    Supplied to `assign_tiers` as the within-tier ordering key; it does NOT enter the tiering (pers)
    and so does not affect the three ship criteria."""
    out: dict[str, float] = {}
    for run in ledger.runs(pipeline="phase7"):
        for c in ledger.claims(run_id=str(run["run_id"])):
            out[str(c["claim_id"])] = float(c["confidence"])
    return out


def single_sigma_precisions(ledger: RunLedger, labels: dict[str, str]) -> list[float]:
    """Surfaced precision at EACH single σ cell (one phase7 run per cell): planted / (planted +
    noise) among that cell's community claims. Cells with no true/noise claim are skipped."""
    precisions: list[float] = []
    for run in ledger.runs(pipeline="phase7"):
        claims = ledger.claims(run_id=str(run["run_id"]))
        tp = sum(1 for c in claims if labels.get(str(c["claim_id"])) == "planted")
        fp = sum(1 for c in claims if labels.get(str(c["claim_id"])) == "noise")
        if tp + fp:
            precisions.append(tp / (tp + fp))
    return precisions
