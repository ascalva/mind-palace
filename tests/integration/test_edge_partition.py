"""The E_geom ⊔ E_disp partition is structural — build plan Item 7 (the-edge-model.md §4).

The balance math (signed Laplacian / frustration, curvature, clustering) reads `A_geom` — assembled
from the `EdgeStore` (`authority = geometry`) alone. The two DISPOSITIONAL stores — note-version
`supersedes` (`core/stores/versions.py`) and claim `supersede` (`core/recursion_ops.py`) — are
`E_disp`, and `build_complex` holds no handle to either, so none can reach `A_signed`/`L`. This is
the acceptance test: adding a version row AND a claim-op over the same authored nodes
leaves every frustration / curvature / clustering result bit-identical. If one moves, `E_disp` has
leaked into `A_geom` and must be fixed at the store boundary. Deterministic; no model, no network.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pytest

from core.complex.balance import frustration
from core.complex.build import build_complex
from core.complex.curvature import forman
from core.complex_types import EdgeSign
from core.dreaming.cluster import cluster_notes, note_centroids
from core.mirror import MirrorView
from core.provenance import Provenance
from core.recursion_ops import ClaimOpStore, Supersede, apply_operations
from core.stores.derived import DerivedStore
from core.stores.edges import CONTRADICTS, EdgeStore
from core.stores.versions import VersionStore


class _Rows:
    def __init__(self, rows: list[dict[str, Any]]):
        self._rows = rows

    def all_rows(self, *, provenances=None) -> list[dict[str, Any]]:
        if provenances is None:
            return list(self._rows)
        allowed = {Provenance(p).value for p in provenances}
        return [r for r in self._rows if r.get("provenance") in allowed]


def _row(digest: str, vec: list[float]) -> dict[str, Any]:
    return {"digest": digest, "title": digest, "vector": vec, "text": digest,
            "provenance": Provenance.AUTHORED_SOLO.value}


def _two_theme_view() -> MirrorView:
    photo = [1.0, 1, 1, 1, 0, 0, 0, 0]
    synth = [0.0, 0, 0, 0, 1, 1, 1, 1]
    rng = np.random.default_rng(0)
    rows = [_row(f"p{i}", list(np.array(photo) + rng.normal(0, 0.03, 8))) for i in range(4)]
    rows += [_row(f"s{i}", list(np.array(synth) + rng.normal(0, 0.03, 8))) for i in range(4)]
    return MirrorView.project(_Rows(rows))


def test_dispositional_edges_never_reach_the_balance_math(tmp_path):
    view = _two_theme_view()
    edges = EdgeStore(tmp_path / "edges.sqlite")
    edges.add("p0", "s0", sign=EdgeSign.CONTRADICT, rel_type=CONTRADICTS, w=1.0)  # real frustration
    derived = DerivedStore(tmp_path / "derived.sqlite")

    def measure() -> tuple[float, list[tuple[int, int, int]], dict[tuple[int, int], float],
                          list[tuple[str, ...]]]:
        kx = build_complex(view, edges=edges, derived=derived)
        lam, tris = frustration(kx.A_signed)
        curv = forman(kx.A)
        clusters = [c.digests for c in cluster_notes(note_centroids(view.rows()), threshold=0.5)]
        return lam, tris, curv, clusters

    lam0, tris0, curv0, cl0 = measure()

    # Add dispositional edges over the SAME authored nodes, in BOTH E_disp stores.
    versions = VersionStore(tmp_path / "versions.sqlite")
    versions.record("p0", "p0-digest-v2")          # a note-version supersedes (v1 → v2)
    ops = ClaimOpStore(tmp_path / "claim_ops.sqlite")
    apply_operations([Supersede("p0", "a revised reading of p0", "s0 answered it")],
                     ops_store=ops, derived=derived)
    assert versions.count() == 1 and ops.superseded() == {"p0"}     # the E_disp edges really exist

    lam1, tris1, curv1, cl1 = measure()

    # ... and NONE of the balance / curvature / clustering results moved.
    assert lam0 == pytest.approx(lam1)
    assert tris0 == tris1
    assert curv0 == curv1
    assert cl0 == cl1


def test_build_complex_has_no_handle_to_the_dispositional_stores():
    # Structural: the constructor's signature admits only the geometry EdgeStore and the derivation
    # DerivedStore — nowhere to pass a VersionStore or a ClaimOpStore, so E_disp cannot enter.
    import inspect

    params = set(inspect.signature(build_complex).parameters)
    assert params == {"view", "edges", "derived", "sim_floor"}
