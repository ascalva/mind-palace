"""H9 — structural snapshots + drift trajectories (core/complex/temporal.py; §5.4).

Proves: the invariants are computed correctly on planted structure; snapshots persist to DuckDB
and read back; trajectories are time-ordered and metric-validated; the latest snapshot's axes
flow into the drift gauge (the A2 wiring end to end).
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pytest

from core.complex.build import build_complex
from core.complex.temporal import SnapshotStore, StructuralSnapshot, compute_snapshot
from core.complex.topology import cosine_distance_matrix
from core.complex_types import EdgeSign
from core.mirror import MirrorView
from core.stores.edges import CONTRADICTS, EdgeStore


def _row(digest: str, vec: list[float]) -> dict[str, Any]:
    return {"digest": digest, "title": digest, "provenance": "authored-solo", "vector": vec}


def _two_domain_view() -> MirrorView:
    rng = np.random.default_rng(0)
    rows = []
    for i in range(4):
        rows.append(_row(f"p{i}", list(np.array([1.0, 0, 0, 0]) + rng.normal(0, .02, 4))))
    for i in range(4):
        rows.append(_row(f"s{i}", list(np.array([0.0, 0, 1.0, 0]) + rng.normal(0, .02, 4))))
    return MirrorView(_rows=tuple(rows))


def _distances(view: MirrorView) -> np.ndarray:
    from core.dreaming.cluster import note_centroids
    notes = note_centroids(view.rows())
    return cosine_distance_matrix(np.asarray([n.vector for n in notes], dtype=np.float64))


def test_compute_snapshot_on_planted_structure():
    view = _two_domain_view()
    kx = build_complex(view, sim_floor=0.5)
    snap = compute_snapshot(kx, distances=_distances(view))
    assert snap.n_nodes == 8
    assert snap.n_components == 2                    # two orthogonal domains ⇒ β₀ = 2
    assert snap.n_blocks_sbm == 2                    # the SBM sees the same two concerns
    assert snap.frustration == pytest.approx(0.0, abs=1e-6)   # all-support ⇒ balanced
    assert snap.mean_forman > 0.0                    # dense clique edges are positively curved
    assert snap.frac_neg_curv == 0.0                 # no bridges planted
    assert snap.persistence_h1 == 0                  # no ring planted
    assert 0.0 <= snap.min_conductance <= 1.0


def test_contradiction_edge_raises_frustration(tmp_path):
    view = _two_domain_view()
    edges = EdgeStore(tmp_path / "edges.sqlite")
    # a contradiction INSIDE a dense clique creates a frustrated triangle ⇒ λ_min > 0
    edges.add("p0", "p1", sign=EdgeSign.CONTRADICT, rel_type=CONTRADICTS)
    frustrated = compute_snapshot(build_complex(view, edges=edges, sim_floor=0.5))
    balanced = compute_snapshot(build_complex(view, sim_floor=0.5))
    assert frustrated.frustration > balanced.frustration
    assert frustrated.persistence_h1 is None         # no distances given ⇒ NULL, not a fake 0


def test_snapshot_store_roundtrip_and_trajectory(tmp_path):
    store = SnapshotStore(tmp_path / "structural.duckdb")
    assert store.latest_structural() is None         # empty store reads honestly
    for t, fr in [("2026-07-01T00:00:00", 0.0), ("2026-07-02T00:00:00", 0.3)]:
        store.write(StructuralSnapshot(taken_at=t, n_nodes=8, n_components=2, fiedler=0.5,
                                       frustration=fr, mean_forman=1.0, frac_neg_curv=0.0,
                                       n_blocks_sbm=2, min_conductance=0.4,
                                       persistence_h1=None))
    assert store.count() == 2
    traj = store.trajectory("frustration")
    assert [v for _, v in traj] == [0.0, 0.3]        # time-ordered — the F4 trajectory input
    assert store.trajectory("persistence_h1") == []  # NULLs are excluded, not faked
    latest = store.latest_structural()
    assert latest == {"frustration": 0.3, "min_conductance": 0.4}
    with pytest.raises(ValueError):
        store.trajectory("drop table")               # column names are allowlisted
    store.close()


def test_latest_structural_feeds_the_drift_gauge(tmp_path):
    # End to end: snapshot → latest_structural → drift_from_report(structural=…) → axes + trip.
    from eval.drift import DriftConfig, drift_from_report
    from eval.golden import GoldenReport, QueryResult
    store = SnapshotStore(tmp_path / "structural.duckdb")
    store.write(StructuralSnapshot(taken_at="2026-07-02T00:00:00", n_nodes=8, n_components=2,
                                   fiedler=0.5, frustration=0.30, mean_forman=1.0,
                                   frac_neg_curv=0.0, n_blocks_sbm=2, min_conductance=0.30,
                                   persistence_h1=0))
    report = GoldenReport(per_query=(
        QueryResult(id="q", retrieved=(), recall_at_k=1.0, overlap=0.40, mean_distance=0.60),
    ))
    baseline = {"recall_at_k": 1.0, "overlap": 0.40, "mean_distance": 0.60,
                "frustration": 0.05, "min_conductance": 0.30}
    cfg = DriftConfig(recall_tol=0.10, overlap_tol=0.10, distance_tol=0.05, theta=1.0,
                      frustration_tol=0.25)
    r = drift_from_report(report, baseline, cfg, intact=True,
                          structural=store.latest_structural())
    assert r.per_axis["frustration"] == pytest.approx(1.0)     # rose 0.25 = one tolerance-unit
    assert r.per_axis["min_conductance"] == 0.0                # at baseline
    assert r.drift == pytest.approx(1.0) and r.within_tolerance
    assert not math.isinf(r.drift)
    store.close()
