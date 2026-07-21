"""The isolation twin for `core/temporal/` — bp-032 Item 8 (dn-temporal-retrieval-algebra §2.4:
"two complexes, two homes, one methodology").

`X_cite` reads `reference_edges` and reuses `core/complex/hodge`, but **no instrument moves**: the
balance math (`build_complex` → `A_signed` → frustration/curvature/clustering) cannot observe
whether the citation complex exists. This is the B-c falsifier lifted one level — structurally
(`core/complex/**` never imports `core/temporal`; `build_complex`'s signature is unchanged) and
behaviorally (populating `X_cite` over the same authored nodes leaves every instrument
bit-identical). Deterministic; no model, no network. Twin of `test_reference_edge_isolation.py`.
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path
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
from core.temporal.acquire import build_citation_complex
from core.temporal.complex import dim_ker_L1

_COMPLEX_DIR = Path(inspect.getfile(build_complex)).parent


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


def test_populating_x_cite_moves_no_instrument(tmp_path):
    view = _two_theme_view()
    node_digests = [r["digest"] for r in view.rows()]
    edges = EdgeStore(tmp_path / "edges.sqlite")
    edges.add("p0", "s0", sign=EdgeSign.CONTRADICT, rel_type=CONTRADICTS, w=1.0)
    derived = DerivedStore(tmp_path / "derived.sqlite")

    def measure() -> tuple[float, list[tuple[int, int, int]], dict[tuple[int, int], float],
                          list[tuple[str, ...]]]:
        kx = build_complex(view, edges=edges, derived=derived)
        lam, tris = frustration(kx.A_signed)
        curv = forman(kx.A)
        clusters = [c.digests for c in cluster_notes(note_centroids(view.rows()), threshold=0.5)]
        return lam, tris, curv, clusters

    lam0, tris0, curv0, cl0 = measure()

    # POPULATE X_cite with real doc→doc citation edges over the SAME authored nodes, then BUILD the
    # citation complex and even read an invariant off it — if core/temporal leaked into the balance
    # math, THIS is what would move an instrument.
    ref_store = ReferenceEdgeStore(tmp_path / "reference_edges.sqlite")
    ref_store.add_batch([
        ReferenceEdge.mint(source_kind="corpus", source_ref="p0", target_kind="corpus",
                           target_ref="s0", ref_type="design-ref", commit_sha="c0", source_line=1),
        ReferenceEdge.mint(source_kind="corpus", source_ref="s1", target_kind="corpus",
                           target_ref="p1", ref_type="design-ref", commit_sha="c0", source_line=2),
        ReferenceEdge.mint(source_kind="corpus", source_ref="p2", target_kind="corpus",
                           target_ref="s2", ref_type="design-ref", commit_sha="c0", source_line=3),
    ])
    cx = build_citation_complex(ref_store)
    assert set(cx.nodes) <= set(node_digests)                # citation nodes ARE complex nodes
    _ = dim_ker_L1(cx)                                       # exercise the Hodge reuse

    lam1, tris1, curv1, cl1 = measure()
    assert lam0 == pytest.approx(lam1)
    assert tris0 == tris1
    assert curv0 == curv1
    assert cl0 == cl1


def test_build_complex_signature_unchanged():
    # The isolation invariant `X_cite` must not weaken (reference_edges.py-pinned): build_complex
    # admits only the geometry EdgeStore + DerivedStore — no citation/temporal handle exists.
    params = set(inspect.signature(build_complex).parameters)
    assert params == {"view", "edges", "derived", "sim_floor"}


def test_core_complex_never_imports_core_temporal():
    # Structural, grep-grade: no module under core/complex/ imports core.temporal — the forbidden
    # direction stays forbidden (core/temporal → core/complex/hodge is the ONLY allowed direction).
    offenders = []
    for py in sorted(_COMPLEX_DIR.rglob("*.py")):
        tree = ast.parse(py.read_text(encoding="utf-8"), filename=str(py))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("core.temporal"):
                offenders.append(f"{py.name}: from {node.module}")
            if isinstance(node, ast.Import):
                offenders.extend(f"{py.name}: import {n.name}"
                                 for n in node.names if n.name.startswith("core.temporal"))
    assert offenders == [], f"core/complex must not import core.temporal: {offenders}"
