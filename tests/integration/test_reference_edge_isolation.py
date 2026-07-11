"""The B-c falsifier, automated forever — bp-013 Item 8 (code-observation-projection.md §2.5).

The full instrument stack (signed Laplacian / frustration, Forman curvature, clustering) reads
`A`/`A_signed`, both assembled by `build_complex` from a `MirrorView` plus the geometry `EdgeStore`
alone. The Lane-1 reference-edge store (`core/stores/reference_edges.py`) is CROSS-STRATUM and lives
outside the complex: `build_complex` holds no handle to it (no parameter exists) and
`core/complex/**` never imports it. This is the acceptance test — it POPULATES that store with real
reference edges over the SAME authored nodes the instruments run on, then re-measures the entire
stack and asserts every result is bit-identical.

If a single instrument moves when reference edges are added, the B-c falsifier — *"any instrument
result changes when reference edges are added or removed"* (plan §6, verbatim) — has FIRED: a
cross-stratum edge has leaked into `A_signed`/`A`, and the fix belongs at the store boundary, never
here. Deterministic; no model, no network. Structural twin of `test_edge_partition.py`.
"""

from __future__ import annotations

import inspect
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
from core.stores.derived import DerivedStore
from core.stores.edges import CONTRADICTS, EdgeStore
from core.stores.reference_edges import ReferenceEdge, ReferenceEdgeStore


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


def test_reference_edges_never_reach_the_balance_math(tmp_path):
    view = _two_theme_view()
    node_digests = [r["digest"] for r in view.rows()]
    assert node_digests, "fixture must have authored nodes for the edges to span"

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

    # POPULATE the Lane-1 reference-edge store with REAL edges over the SAME authored nodes —
    # both directions, every validated ref_type — using the store's real mint/add_batch API.
    # The corpus endpoint IS a node digest of the complex; if the store were reachable, THESE
    # rows over THESE nodes would be exactly what moves an instrument.
    ref_store = ReferenceEdgeStore(tmp_path / "reference_edges.sqlite")
    planted = [
        ReferenceEdge.mint(direction="code_to_corpus", ref_type="note-citation",
                           commit_sha="c0ffee", code_path="core/recursion.py",
                           qualname="apply_operations", corpus_ref="p0", source_line=12),
        ReferenceEdge.mint(direction="code_to_corpus", ref_type="path-mention",
                           commit_sha="c0ffee", code_path="core/mirror.py",
                           qualname="MirrorView.project", corpus_ref="s0", source_line=7),
        ReferenceEdge.mint(direction="corpus_to_code", ref_type="path-mention",
                           commit_sha="c0ffee", code_path="core/complex/build.py",
                           corpus_ref="p1", source_line=3),
        ReferenceEdge.mint(direction="corpus_to_code", ref_type="path-mention",
                           commit_sha="c0ffee", code_path="core/complex/balance.py",
                           corpus_ref="s3", source_line=41),
    ]
    added = ref_store.add_batch(planted)
    # The store REALLY has rows — mirrors test_edge_partition.py's `versions.count() == 1`.
    assert added == len(planted)
    assert ref_store.count() == len(planted)
    assert {e.corpus_ref for e in ref_store.all()} <= set(node_digests)

    lam1, tris1, curv1, cl1 = measure()

    # ... and NOT ONE balance / curvature / clustering result moved. Any drift IS the B-c
    # falsification (plan §10 stop-and-raise) — the store leaked into A_signed/A.
    assert lam0 == pytest.approx(lam1)
    assert tris0 == tris1
    assert curv0 == curv1
    assert cl0 == cl1


def test_build_complex_has_no_handle_to_the_reference_edge_store():
    # Structural, bp-013-specific: the constructor's signature admits only the geometry EdgeStore
    # and the derivation DerivedStore — there is NOWHERE to pass a ReferenceEdgeStore, so the
    # Lane-1 reference edges cannot reach A_signed by construction. Forever-green guard for THIS
    # store (twin of test_edge_partition's E_disp assertion).
    params = set(inspect.signature(build_complex).parameters)
    assert params == {"view", "edges", "derived", "sim_floor"}
