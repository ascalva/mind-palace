"""Structural snapshots — the system watching its own structure evolve (§5.4; H9).

The valuable *temporal* program is not a PDE but a **time series of structural invariants**:
compute β₀, the Fiedler value, frustration, the curvature distribution, the SBM theme count,
the worst community conductance, and the H₁ hole count at each trough pass; watch how they move.
A rising frustration, a community whose conductance is falling, a domain fragmenting — each is a
measurable trajectory. This is exactly the input the drift gauge (A1/A2) and the longitudinal
harness (F4) want.

Wall-clock time τ (the graph actually changing) — NOT diffusion time t (a resolution knob on a
frozen snapshot); keeping them distinct is §5.1's discipline. Snapshots are DuckDB (the telemetry
convention for quantitative time-series), in their own file beside the derived store — derived,
regenerable-in-principle data, never the mirror. Detection only: nothing here alters anything.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import duckdb

import numpy as np
from scipy.sparse.csgraph import connected_components

from config.loader import Config
from core.complex.balance import signed_spectrum
from core.complex.blocks import sbm
from core.complex.build import ReasoningComplex
from core.complex.curvature import forman
from core.complex.cut import min_conductance
from core.complex.spectral import fiedler
from core.complex.topology import long_lived_holes

_DDL = """
CREATE SEQUENCE IF NOT EXISTS snapshot_seq;
CREATE TABLE IF NOT EXISTS structural_snapshots (
    snapshot_id     BIGINT DEFAULT nextval('snapshot_seq'),
    taken_at        TIMESTAMP NOT NULL,
    n_nodes         INTEGER NOT NULL,
    n_components    INTEGER NOT NULL,     -- beta_0
    fiedler         DOUBLE NOT NULL,      -- lambda_2 (algebraic connectivity)
    frustration     DOUBLE NOT NULL,      -- lambda_min(signed L), dissonance proxy
    mean_forman     DOUBLE NOT NULL,      -- mean Forman-Ricci curvature (0 when no edges)
    frac_neg_curv   DOUBLE NOT NULL,      -- fraction of bridge (negative-curvature) edges
    n_blocks_sbm    INTEGER NOT NULL,     -- SBM model-selected theme count
    min_conductance DOUBLE NOT NULL,      -- worst community conductance (alignment)
    persistence_h1  INTEGER               -- long-lived H1 holes; NULL when distances not given
);
"""


@dataclass(frozen=True)
class StructuralSnapshot:
    """One trough pass's structural invariants (the §5.4 / BUILD §1.2 row)."""

    taken_at: str
    n_nodes: int
    n_components: int
    fiedler: float
    frustration: float
    mean_forman: float
    frac_neg_curv: float
    n_blocks_sbm: int
    min_conductance: float
    persistence_h1: int | None = None

    def structural_axes(self) -> dict[str, float]:
        """The A2 drift axes this snapshot feeds (`eval.drift.Profile` optional fields)."""
        return {"frustration": self.frustration, "min_conductance": self.min_conductance}


def _utcnow() -> str:
    return datetime.now(UTC).replace(tzinfo=None).isoformat(timespec="seconds")


def compute_snapshot(kx: ReasoningComplex, *, distances: np.ndarray | None = None,
                     sbm_k_max: int = 8, hole_min_persistence: float = 0.15,
                     taken_at: str | None = None) -> StructuralSnapshot:
    """Compute the invariants on one complex. Deterministic, model-free. `distances` (the
    unthresholded cosine-distance matrix) enables the H₁ count; None records NULL rather than a
    fake zero (the persistence filtration cannot run on the thresholded backbone alone)."""
    n = kx.n
    if n == 0:
        return StructuralSnapshot(taken_at=taken_at or _utcnow(), n_nodes=0, n_components=0,
                                  fiedler=0.0, frustration=0.0, mean_forman=0.0,
                                  frac_neg_curv=0.0, n_blocks_sbm=0, min_conductance=1.0,
                                  persistence_h1=None if distances is None else 0)
    n_comp, _labels = connected_components(kx.A, directed=False)
    lam2, _vec = fiedler(kx.A)
    curv = forman(kx.A)
    vals = list(curv.values())
    mean_forman = float(np.mean(vals)) if vals else 0.0
    frac_neg = float(np.mean([v < 0.0 for v in vals])) if vals else 0.0
    h1: int | None = None
    if distances is not None:
        h1 = len(long_lived_holes(distances, min_persistence=hole_min_persistence))
    return StructuralSnapshot(
        taken_at=taken_at or _utcnow(),
        n_nodes=n,
        n_components=int(n_comp),
        fiedler=float(lam2),
        frustration=signed_spectrum(kx.A_signed),
        mean_forman=mean_forman,
        frac_neg_curv=frac_neg,
        n_blocks_sbm=int(sbm(kx.A, k_max=sbm_k_max).k),
        min_conductance=min_conductance(kx.A),
        persistence_h1=h1,
    )


@dataclass
class SnapshotStore:
    """Append-only DuckDB store of structural snapshots + the trajectory readers the drift
    gauge (A2) and the F4 longitudinal harness consume."""

    path: Path
    _conn: duckdb.DuckDBPyConnection = field(init=False, repr=False)

    def __post_init__(self) -> None:
        import duckdb  # heavy import kept local to construction (telemetry-store convention)
        if str(self.path) != ":memory:":
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = duckdb.connect(str(self.path))
        self._conn.execute(_DDL)

    def write(self, snap: StructuralSnapshot) -> None:
        self._conn.execute(
            "INSERT INTO structural_snapshots (taken_at, n_nodes, n_components, fiedler, "
            "frustration, mean_forman, frac_neg_curv, n_blocks_sbm, min_conductance, "
            "persistence_h1) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [snap.taken_at, snap.n_nodes, snap.n_components, snap.fiedler, snap.frustration,
             snap.mean_forman, snap.frac_neg_curv, snap.n_blocks_sbm, snap.min_conductance,
             snap.persistence_h1],
        )

    def count(self) -> int:
        row = self._conn.execute("SELECT count(*) FROM structural_snapshots").fetchone()
        return int(row[0]) if row else 0

    def trajectory(self, metric: str) -> list[tuple[str, float]]:
        """The time series of one invariant, oldest first — the F4 drift-trajectory input.
        `metric` is validated against the schema (no SQL injection by column name)."""
        allowed = {"n_nodes", "n_components", "fiedler", "frustration", "mean_forman",
                   "frac_neg_curv", "n_blocks_sbm", "min_conductance", "persistence_h1"}
        if metric not in allowed:
            raise ValueError(f"unknown structural metric {metric!r}; one of {sorted(allowed)}")
        rows = self._conn.execute(
            f"SELECT taken_at, {metric} FROM structural_snapshots "
            "WHERE " + metric + " IS NOT NULL ORDER BY taken_at, snapshot_id"
        ).fetchall()
        return [(str(ts), float(v)) for ts, v in rows]

    def latest_structural(self) -> dict[str, float] | None:
        """The most recent snapshot's A2 axes — directly consumable by
        `eval.drift.profile_from_report(structural=...)`. None when no snapshot exists."""
        row = self._conn.execute(
            "SELECT frustration, min_conductance FROM structural_snapshots "
            "ORDER BY taken_at DESC, snapshot_id DESC LIMIT 1"
        ).fetchone()
        if row is None:
            return None
        return {"frustration": float(row[0]), "min_conductance": float(row[1])}

    def close(self) -> None:
        self._conn.close()


def open_snapshot_store(config: Config | None = None) -> SnapshotStore:
    from config.loader import get_config

    cfg = config or get_config()
    # Beside the derived store: interpreted-layer structure, regenerable in principle.
    return SnapshotStore(cfg.paths.derived_store.parent / "structural.duckdb")
