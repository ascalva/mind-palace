"""H9 — structural snapshots + drift trajectories (core/complex/temporal.py; §5.4).

Proves: the invariants are computed correctly on planted structure; snapshots persist to DuckDB
and read back; trajectories are time-ordered and metric-validated; the latest snapshot's axes
flow into the drift gauge (the A2 wiring end to end). Also proves the two degree-1 invariants
(design note `dn-edge-dynamics` §2.3, bp-022 Item 6): known β₁ recovered exactly, `distances=None`
degrades honestly, a PRE-EXISTING store file (no new columns) heals additively on open, and the
consumed `structural_axes()` drift contract stays byte-identical (the §3 risk, pinned by test).
"""

from __future__ import annotations

import dataclasses
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


def _ring_view(n: int = 6) -> MirrorView:
    """n notes on a circle: adjacent pairs similar, no chords, no center — one clean β₁ = 1 cycle
    in the flag complex at a σ that keeps only the ring edges (test_structural_panel.py's
    precedent). A long-lived hole with a known persistence."""
    import math as _math
    rows = [
        _row(f"r{i}", [_math.cos(2 * _math.pi * i / n), _math.sin(2 * _math.pi * i / n)])
        for i in range(n)
    ]
    return MirrorView(_rows=tuple(rows))


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
    assert snap.dim_ker_l1 == 0                      # two filled cliques, no cycle ⇒ β1 = 0
    assert snap.harmonic_persistence_total == 0.0    # no thread ⇒ zero persistence, not None


# --- Item 6: the two degree-1 invariants (design note §2.3, plan §6(c,d)) ----------------------

def test_degree1_invariants_match_known_beta1_on_planted_ring():
    """Falsifier (design note L-c, verbatim): a snapshot series recomputed from the same inputs
    differs run-to-run, or any EXISTING invariant's value is perturbed by the new fields. Known
    topology: a 6-note ring at sigma=0.3 keeps exactly the 6 perimeter edges, no chords ⇒ beta1=1
    (cross-checked against bp-021's hodge.py/topology.py independently, tests/unit/test_hodge.py's
    §6(f) harness pattern) — dim_ker_l1 must equal it exactly, and harmonic_persistence_total must
    equal the ring hole's own lifetime (birth=0.5, death=1.5 at these ring coordinates)."""
    view = _ring_view(6)
    kx = build_complex(view, sim_floor=0.3)
    D = _distances(view)
    snap = compute_snapshot(kx, distances=D, hole_min_persistence=0.15,
                            thread_min_persistence=0.15)
    assert snap.dim_ker_l1 == 1                       # the known beta1 of an unfilled hexagon
    assert snap.harmonic_persistence_total == pytest.approx(1.0)  # the ring hole's lifetime
    assert snap.persistence_h1 == 1                   # existing invariant unperturbed by the add

    # determinism: two independent computations agree exactly (no seed, no iterative solver).
    snap2 = compute_snapshot(kx, distances=D, hole_min_persistence=0.15,
                             thread_min_persistence=0.15)
    assert snap2.dim_ker_l1 == snap.dim_ker_l1
    assert snap2.harmonic_persistence_total == snap.harmonic_persistence_total
    assert snap2.persistence_h1 == snap.persistence_h1
    assert snap2.frustration == snap.frustration       # an existing invariant, untouched


def test_degree1_invariants_degrade_to_none_like_persistence_h1():
    """The honest-seam pattern (design note §2.3): distances=None must not crash and must not
    fabricate a zero — both new fields degrade to None exactly like `persistence_h1` already
    does, and no other invariant is perturbed by their absence."""
    view = _two_domain_view()
    kx = build_complex(view, sim_floor=0.5)
    snap = compute_snapshot(kx)   # no distances argument at all
    assert snap.persistence_h1 is None
    assert snap.dim_ker_l1 is None
    assert snap.harmonic_persistence_total is None
    assert snap.n_nodes == 8 and snap.n_components == 2   # unrelated invariants still compute


def test_degree1_invariants_honest_on_degenerate_empty_complex():
    """Degenerate input (n=0) yields honest empties for the new fields too — never a fabricated
    shape (the same n==0 branch `persistence_h1` already takes)."""
    empty_view = MirrorView(_rows=())
    kx = build_complex(empty_view)
    assert kx.n == 0
    snap_no_distances = compute_snapshot(kx)
    assert snap_no_distances.dim_ker_l1 is None
    assert snap_no_distances.harmonic_persistence_total is None
    snap_with_distances = compute_snapshot(kx, distances=np.zeros((0, 0)))
    assert snap_with_distances.dim_ker_l1 == 0
    assert snap_with_distances.harmonic_persistence_total == 0.0


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


def test_snapshot_store_write_and_trajectory_carry_degree1_fields(tmp_path):
    """The two new columns round-trip through write/trajectory exactly like every other
    invariant — `dim_ker_l1`/`harmonic_persistence_total` join `trajectory()`'s allowed set
    (plan §6(d)), NULLs excluded the same way `persistence_h1`'s already are."""
    store = SnapshotStore(tmp_path / "structural.duckdb")
    store.write(StructuralSnapshot(taken_at="2026-07-01T00:00:00", n_nodes=6, n_components=1,
                                   fiedler=0.1, frustration=0.0, mean_forman=0.5,
                                   frac_neg_curv=0.0, n_blocks_sbm=1, min_conductance=0.5,
                                   persistence_h1=1, dim_ker_l1=1,
                                   harmonic_persistence_total=1.0))
    store.write(StructuralSnapshot(taken_at="2026-07-02T00:00:00", n_nodes=6, n_components=1,
                                   fiedler=0.1, frustration=0.0, mean_forman=0.5,
                                   frac_neg_curv=0.0, n_blocks_sbm=1, min_conductance=0.5,
                                   persistence_h1=None, dim_ker_l1=None,
                                   harmonic_persistence_total=None))
    assert [v for _, v in store.trajectory("dim_ker_l1")] == [1.0]   # the None row excluded
    assert [v for _, v in store.trajectory("harmonic_persistence_total")] == [1.0]
    store.close()


def test_preexisting_store_file_heals_additively_on_open(tmp_path):
    """Item 6's stored-data touch (plan §7, 'touches stored data? yes'): a PRE-EXISTING store
    file built on the OLD schema (before bp-022's two columns existed) must open, heal via the
    on-open `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`, read old rows back as None for the new
    fields, and accept new rows carrying real values — additive, NULL-backfilled, reversible by
    column drop (plan §7's dry-run discipline: prove the migration on a fixture before any live
    file is touched — SnapshotStore.__post_init__/open_snapshot_store are never invoked here
    against the real repo path, per the side-effect audit)."""
    import duckdb

    path = tmp_path / "pre_existing.duckdb"
    # Build the fixture with the OLD DDL only (no dim_ker_l1 / harmonic_persistence_total) --
    # exactly what a store file written before this plan merged looks like on disk.
    old_ddl = """
    CREATE SEQUENCE IF NOT EXISTS snapshot_seq;
    CREATE TABLE IF NOT EXISTS structural_snapshots (
        snapshot_id     BIGINT DEFAULT nextval('snapshot_seq'),
        taken_at        TIMESTAMP NOT NULL,
        n_nodes         INTEGER NOT NULL,
        n_components    INTEGER NOT NULL,
        fiedler         DOUBLE NOT NULL,
        frustration     DOUBLE NOT NULL,
        mean_forman     DOUBLE NOT NULL,
        frac_neg_curv   DOUBLE NOT NULL,
        n_blocks_sbm    INTEGER NOT NULL,
        min_conductance DOUBLE NOT NULL,
        persistence_h1  INTEGER
    );
    """
    conn = duckdb.connect(str(path))
    conn.execute(old_ddl)
    conn.execute(
        "INSERT INTO structural_snapshots (taken_at, n_nodes, n_components, fiedler, "
        "frustration, mean_forman, frac_neg_curv, n_blocks_sbm, min_conductance, "
        "persistence_h1) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ["2026-07-01T00:00:00", 6, 1, 0.1, 0.0, 0.5, 0.0, 1, 0.5, 1],
    )
    conn.close()

    # Open through the CURRENT SnapshotStore -- this is the on-open heal, exercised against the
    # fixture file only.
    store = SnapshotStore(path)
    assert store.count() == 1
    # Old row reads back None for the new columns -- healed, not fabricated.
    assert store.trajectory("dim_ker_l1") == []                  # NULL excluded, not faked
    assert store.trajectory("harmonic_persistence_total") == []
    assert [v for _, v in store.trajectory("persistence_h1")] == [1.0]  # old data intact

    # New row after the heal carries real degree-1 values.
    store.write(StructuralSnapshot(taken_at="2026-07-02T00:00:00", n_nodes=6, n_components=1,
                                   fiedler=0.1, frustration=0.0, mean_forman=0.5,
                                   frac_neg_curv=0.0, n_blocks_sbm=1, min_conductance=0.5,
                                   persistence_h1=1, dim_ker_l1=1,
                                   harmonic_persistence_total=1.0))
    assert store.count() == 2
    assert [v for _, v in store.trajectory("dim_ker_l1")] == [1.0]
    store.close()

    # Idempotent: reopening the now-healed file a second time must not error or duplicate columns.
    store2 = SnapshotStore(path)
    assert store2.count() == 2
    store2.close()


def test_structural_axes_byte_identical_to_before_bp022():
    """The drift-axes contract (`eval.drift.Profile` optional fields) is CONSUMED (design note
    §3 risk / plan §6(c)) -- `structural_axes()` must return EXACTLY the same two keys/values it
    did before this plan, regardless of the new fields' presence or values. Falsifier: any change
    to this dict's keys or the values it derives from is an eval-plane behavior change smuggled
    in as an additive observation."""
    snap = StructuralSnapshot(taken_at="2026-07-01T00:00:00", n_nodes=6, n_components=1,
                              fiedler=0.1, frustration=0.42, mean_forman=0.5,
                              frac_neg_curv=0.0, n_blocks_sbm=1, min_conductance=0.77,
                              persistence_h1=1, dim_ker_l1=1, harmonic_persistence_total=3.5)
    axes = snap.structural_axes()
    assert axes == {"frustration": 0.42, "min_conductance": 0.77}
    assert set(axes.keys()) == {"frustration", "min_conductance"}   # exactly two keys, unchanged

    # Varying the new fields alone must not move the axes at all.
    snap_no_threads = dataclasses.replace(snap, dim_ker_l1=None, harmonic_persistence_total=None)
    assert snap_no_threads.structural_axes() == axes
    snap_more_threads = dataclasses.replace(snap, dim_ker_l1=5, harmonic_persistence_total=99.0)
    assert snap_more_threads.structural_axes() == axes
