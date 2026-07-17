"""Quality battery for CN-2 σ* (bp-059 item 3) — the abstraction-proximity claim, end-to-end.

Same statistical philosophy as the σ-gate fixtures (bp-057): planted structure with KNOWN cosines
(exact by construction over an orthonormal basis), asserting BOUNDS and RELATIONSHIPS, never exact
floats. Model-free and deterministic. Drives the BUILT `run_connectivity` entry point over a
`MirrorView` + a certified mirror spine, writing to an in-memory `EvalResultsStore` (the dry-run
path — the entry point never writes to a core store).

The fixture: two tight clusters A={a0,a1}, B={b0,b1} (within-cluster cosine 0.95) joined by ONE weak
bridge a0–b0 (cosine 0.5); every other cross cosine ≈ 0.45–0.48. Two observable facts follow:

* **abstraction proximity** — within-cluster σ* (0.95-band) strictly exceeds cross-cluster σ*
  (0.5-band): σ* measures how coarse abstraction must get before two thoughts share a conversation.
* **grid-relativity** — at a LOOSE grid (min 0.4 ≤ 0.5) the bridge is an edge, so the clusters
  connect and the cross pair has a real σ*; at a TIGHT grid (min 0.7 > 0.5) the bridge drops, the
  components split, and the cross pair reports "not connected within grid" (`None`).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from core.graph.sigma_star import cut_fingerprint
from core.mirror import MirrorView
from core.provenance import Provenance
from core.stores.versions import VersionStore
from core.temporal.spine import CutSources, Spine, SpineSources
from eval.harness.connectivity import (
    METRIC_FRAC_CONNECTED,
    METRIC_N_PAIRS,
    ConnEvidence,
    run_connectivity,
)
from eval.harness.store import EvalResultsStore

_MEM = Path(":memory:")


class _Rows:
    def __init__(self, rows: list[dict[str, Any]]):
        self._rows = rows

    def all_rows(self, *, provenances: Any = None) -> list[dict[str, Any]]:
        if provenances is None:
            return list(self._rows)
        allowed = {Provenance(p).value for p in provenances}
        return [r for r in self._rows if r.get("provenance") in allowed]


def _row(digest: str, vec: np.ndarray) -> dict[str, Any]:
    return {"digest": digest, "title": digest, "vector": list(vec), "text": digest,
            "provenance": Provenance.AUTHORED_SOLO.value}


def _bridged_two_cluster_view() -> MirrorView:
    """Two tight clusters joined by one weak bridge, exact cosines over an orthonormal basis:
    within-cluster cos(a0,a1)=cos(b0,b1)=0.95; bridge cos(a0,b0)=0.5; other cross cosines ≈0.45."""
    e = np.eye(6)
    tail = float(np.sqrt(1 - 0.95**2))            # 0.9500² + tail² = 1
    a0 = e[0]
    a1 = 0.95 * e[0] + tail * e[1]
    b0 = 0.5 * e[0] + float(np.sqrt(1 - 0.25)) * e[2]     # cos(a0,b0)=0.5, b0 a unit vector
    b1 = 0.95 * b0 + tail * e[3]                  # cos(b0,b1)=0.95 (e3 ⊥ b0)
    rows = [_row("a0", a0), _row("a1", a1), _row("b0", b0), _row("b1", b1)]
    return MirrorView.project(_Rows(rows))


def _mirror_spine(*, docs: tuple[str, ...] = ("docA", "docB")) -> Spine:
    """A COMMIT-certified mirror spine (test_cuts pattern) — a real mirror frontier for the cut."""
    vs = VersionStore(_MEM)
    for i, d in enumerate(docs):
        vs.record(d, f"DIG{i}")
    return Spine.derive(SpineSources(versions=vs), cut_sources=CutSources(commit_sha="deadbeef"))


def _sigma(pairs: Any, a: str, b: str) -> float | None:
    for p in pairs:
        if {p.a, p.b} == {a, b}:
            return p.sigma_star
    raise AssertionError(f"pair {a},{b} absent from the summary")


# ── the battery ──────────────────────────────────────────────────────────────────────────────────


def test_within_cluster_sigma_star_exceeds_cross_cluster() -> None:
    grid = (0.4, 0.6, 0.8)
    result = run_connectivity(
        view=_bridged_two_cluster_view(), spine=_mirror_spine(), grid=grid,
        eval_store=EvalResultsStore(_MEM), base_fingerprint="cfg-fp",
    )
    within = _sigma(result.pairs, "a0", "a1")
    cross = _sigma(result.pairs, "a0", "b0")
    assert within is not None and cross is not None       # both connect at the loose grid
    assert within > cross                                 # abstraction proximity is measured


def test_grid_relativity_bridge_present_at_loose_absent_at_tight() -> None:
    view = _bridged_two_cluster_view()
    loose = run_connectivity(view=view, spine=_mirror_spine(), grid=(0.4, 0.6),
                             eval_store=EvalResultsStore(_MEM), base_fingerprint="fp")
    tight = run_connectivity(view=view, spine=_mirror_spine(), grid=(0.7, 0.9),
                             eval_store=EvalResultsStore(_MEM), base_fingerprint="fp")
    assert _sigma(loose.pairs, "a0", "b0") is not None    # bridge 0.5 ≥ loose min 0.4: connected
    assert _sigma(tight.pairs, "a0", "b0") is None        # bridge 0.5 < tight min 0.7: split
    assert _sigma(tight.pairs, "a0", "a1") is not None    # within-cluster 0.95 still connects


def test_every_reading_evidence_decodes_to_conn_evidence_with_grid_and_cut() -> None:
    grid = (0.4, 0.6, 0.8)
    spine = _mirror_spine()
    store = EvalResultsStore(_MEM)
    result = run_connectivity(view=_bridged_two_cluster_view(), spine=spine, grid=grid,
                              eval_store=store, base_fingerprint="cfg-fp")
    assert result.readings_written > 0
    expected_cut_fp = cut_fingerprint(spine.cut_at(strata=frozenset({"mirror"})))
    for reading in store.query():
        decoded = json.loads(reading.evidence_ref or "")
        assert decoded["instrument"] == "connectivity/v1"
        assert decoded["grid"] == list(grid)              # the grid is reconstructable
        assert decoded["cut_fingerprint"] == expected_cut_fp   # the history coordinate is pinned
        # and it round-trips through the dataclass
        ev = ConnEvidence(grid=tuple(decoded["grid"]),
                          base_fingerprint=decoded["base_fingerprint"],
                          cut_fingerprint=decoded["cut_fingerprint"])
        assert json.loads(ev.as_ref()) == decoded


def test_put_is_idempotent_a_second_run_writes_zero() -> None:
    grid = (0.4, 0.6, 0.8)
    view = _bridged_two_cluster_view()
    store = EvalResultsStore(_MEM)
    first = run_connectivity(view=view, spine=_mirror_spine(), grid=grid,
                             eval_store=store, base_fingerprint="cfg-fp")
    second = run_connectivity(view=view, spine=_mirror_spine(), grid=grid,
                              eval_store=store, base_fingerprint="cfg-fp")
    assert first.readings_written > 0
    assert second.readings_written == 0                   # every key already present (append-only)


def test_empty_and_singleton_corpora_emit_no_readings_and_note_it() -> None:
    for rows in ([], ["only"]):
        view = MirrorView.project(_Rows(
            [_row(d, np.array([1.0, 0, 0, 0, 0, 0])) for d in rows]
        ))
        store = EvalResultsStore(_MEM)
        result = run_connectivity(view=view, spine=_mirror_spine(), grid=(0.4, 0.8),
                                  eval_store=store, base_fingerprint="fp")
        assert result.readings_written == 0
        assert result.pairs == ()
        assert result.notes and store.query() == []       # noted, nothing written


def test_frac_connected_and_n_pairs_are_always_written() -> None:
    """Even when a run has unconnected pairs, the two always-present aggregates are emitted."""
    grid = (0.4, 0.6, 0.8)
    store = EvalResultsStore(_MEM)
    result = run_connectivity(view=_bridged_two_cluster_view(), spine=_mirror_spine(), grid=grid,
                              eval_store=store, base_fingerprint="fp")
    assert result.aggregates[METRIC_N_PAIRS] == 6.0       # C(4,2)
    assert 0.0 <= result.aggregates[METRIC_FRAC_CONNECTED] <= 1.0
