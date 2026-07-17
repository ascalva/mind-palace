"""Unit tests for CN-2 σ*/MST — the PRIMARY structural falsifiers (bp-059 items 1–2).

Item 1 (the CN-1 scaffolding): `ConnEvidence.as_ref()` round-trips (stable JSON); the latest-cut
gate sources the mirror cut via `spine.cut_at(strata=frozenset({"mirror"}))` and lets
`CutCertificateError` PROPAGATE (a stubbed uncertified spine ⇒ the acquisition raises, emits no
reading); `crossing_edges(cut) == []` is asserted (the CN-1 legality tooth); Law C4 holds — the
module reads no clock.

Item 2 (MST + σ*): the two ratified falsifiers — (a) the **ultrametric inequality**
`σ*(A,C) ≥ min(σ*(A,B), σ*(B,C))` on sampled real triples; (b) **MST ≡ union-find**: the MST-derived
σ* equals a direct union-find grid sweep on every pair (two independent computations agree). Plus
grid-relativity (a pair unconnected at the loosest grid reports `None, ()`) and chain realizability
(the reported chain's min-cosine edge grid-snaps to the reported σ*).

Fixtures reuse the sanctioned construction paths: `tests/unit/test_cuts.py`'s injected-cut spine and
`tests/unit/test_complex.py`'s `_Rows` MirrorView source.
"""

from __future__ import annotations

import itertools
import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from core.dreaming.graph import MirrorGraph
from core.graph.sigma_star import (
    MaxSpanningForest,
    acquire_mirror_cut,
    build_max_spanning_tree,
    cut_fingerprint,
    pairwise_sigma_star,
    sigma_star,
)
from core.mirror import MirrorView
from core.provenance import Provenance
from core.stores.versions import VersionStore
from core.temporal.spine import CutCertificateError, CutSources, Spine, SpineSources
from eval.harness.connectivity import ConnEvidence

_MEM = Path(":memory:")


# ── fixtures: a MirrorView over planted vectors + a certified mirror spine ───────────────────────


class _Rows:
    """Provenance-filtering row source for MirrorView.project (see test_complex._Rows)."""

    def __init__(self, rows: list[dict[str, Any]]):
        self._rows = rows

    def all_rows(self, *, provenances: Any = None) -> list[dict[str, Any]]:
        if provenances is None:
            return list(self._rows)
        allowed = {Provenance(p).value for p in provenances}
        return [r for r in self._rows if r.get("provenance") in allowed]


def _row(digest: str, vec: list[float]) -> dict[str, Any]:
    return {"digest": digest, "title": digest, "vector": vec, "text": digest,
            "provenance": Provenance.AUTHORED_SOLO.value}


def _view(rows: list[dict[str, Any]]) -> MirrorView:
    return MirrorView.project(_Rows(rows))


def _two_cluster_view() -> MirrorView:
    """Two tight themes in an 8-dim token space (the test_complex philosophy): within-cluster
    cosines high, cross-cluster cosines low. Deterministic (seeded noise)."""
    photo = np.array([1.0, 1, 1, 1, 0, 0, 0, 0])
    synth = np.array([0.0, 0, 0, 0, 1, 1, 1, 1])
    rng = np.random.default_rng(0)
    rows: list[dict[str, Any]] = []
    for i in range(4):
        rows.append(_row(f"p{i}", list(photo + rng.normal(0, 0.03, 8))))
    for i in range(4):
        rows.append(_row(f"s{i}", list(synth + rng.normal(0, 0.03, 8))))
    return _view(rows)


def _mirror_spine(*, commit: str | None = "deadbeef") -> Spine:
    """A spine whose mirror stratum certifies from an injected commit SHA (test_cuts pattern). A
    mirror cut needs ONLY the COMMIT certificate — no trough/handoff. `commit=None` ⇒ the cut
    refuses. The versions store gives a real mirror chain for the frontier + a down-set."""
    vs = VersionStore(_MEM)
    vs.record("docA", "DIG1")
    vs.record("docB", "DIG2")
    return Spine.derive(SpineSources(versions=vs), cut_sources=CutSources(commit_sha=commit))


# ── item 1: the CN-1 scaffolding ─────────────────────────────────────────────────────────────────


def test_conn_evidence_ref_round_trips_stable_json() -> None:
    ev = ConnEvidence(grid=(0.5, 0.6, 0.7), base_fingerprint="cfg-fp", cut_fingerprint="cut-fp")
    decoded = json.loads(ev.as_ref())
    assert decoded == {
        "instrument": "connectivity/v1",
        "grid": [0.5, 0.6, 0.7],
        "base_fingerprint": "cfg-fp",
        "cut_fingerprint": "cut-fp",
    }
    assert ev.as_ref() == ev.as_ref()                     # sort_keys ⇒ byte-stable


def test_acquire_mirror_cut_sources_commit_and_asserts_no_crossings() -> None:
    spine = _mirror_spine()
    cut = acquire_mirror_cut(spine)
    # the frontier carries the per-doc mirror chains (versions:<doc>), certified by COMMIT
    keys = {k for k, _pos in cut.frontier}
    assert "versions:docA" in keys and "versions:docB" in keys
    assert spine.crossing_edges(cut) == []                # the CN-1 legality tooth
    assert cut_fingerprint(cut) == cut_fingerprint(cut)   # deterministic content hash


def test_uncertified_cut_propagates_and_emits_nothing() -> None:
    """A stubbed uncertified spine (no commit SHA) ⇒ `acquire_mirror_cut` RAISES; no reading
    escapes (item-1 falsifier: never emit at an uncertified cut, never swallow the cert error)."""
    with pytest.raises(CutCertificateError):
        acquire_mirror_cut(_mirror_spine(commit=None))


def test_cut_fingerprint_tracks_the_frontier_not_wall_time() -> None:
    """Two cuts over DIFFERENT mirror histories carry DIFFERENT fingerprints — the hash is over the
    frontier + sourced certificates, never a wall timestamp (Law C4)."""
    a = acquire_mirror_cut(_mirror_spine())
    vs = VersionStore(_MEM)
    vs.record("docA", "DIG1")                              # a shorter history (docB absent)
    b = Spine.derive(SpineSources(versions=vs),
                     cut_sources=CutSources(commit_sha="deadbeef")).cut_at(
        strata=frozenset({"mirror"}))
    assert cut_fingerprint(a) != cut_fingerprint(b)


# ── item 2: the MST + σ* + the two falsifiers ────────────────────────────────────────────────────


def _sigma_star_via_union_find(
    graph: MirrorGraph, a: str, b: str, grid: tuple[float, ...]
) -> float | None:
    """The INDEPENDENT oracle: σ* by a direct union-find grid sweep (never touches the MST). For
    each grid σ, union all edges with cosine ≥ σ; the LARGEST grid σ at which a,b share a component
    IS the grid-snapped σ*. None if they never connect (split at the loosest grid)."""
    digests = [graph.digest(i) for i in range(graph.n)]
    ia, ib = digests.index(a), digests.index(b)
    best: float | None = None
    for sigma in sorted(grid):                             # ascending; keep the largest connecting
        parent = list(range(graph.n))

        def find(x: int, parent: list[int] = parent) -> int:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        for i in range(graph.n):
            for j in range(i + 1, graph.n):
                if float(graph.sim[i, j]) >= sigma:
                    ri, rj = find(i), find(j)
                    if ri != rj:
                        parent[max(ri, rj)] = min(ri, rj)
        if find(ia) == find(ib):
            best = sigma
    return best


def test_mst_equals_union_find_on_every_pair() -> None:
    """Falsifier (b): the MST-derived σ* agrees with the independent union-find sweep on EVERY
    pair — two independent computations of the single-linkage threshold. Disagreement ⇒ a bug."""
    grid = (0.2, 0.4, 0.6, 0.8, 0.95)
    graph = MirrorGraph.build(_two_cluster_view(), sigma=grid[0])
    forest = build_max_spanning_tree(graph)
    digests = [graph.digest(i) for i in range(graph.n)]
    for a, b in itertools.combinations(digests, 2):
        mst = sigma_star(forest, a, b, grid=grid).sigma_star
        oracle = _sigma_star_via_union_find(graph, a, b, grid)
        assert mst == oracle, f"σ*({a},{b}): MST={mst} != union-find={oracle}"


def test_ultrametric_inequality_on_sampled_real_triples() -> None:
    """Falsifier (a): σ*(A,C) ≥ min(σ*(A,B), σ*(B,C)) on real triples (skip when any leg is None).
    Single-linkage σ* is an ultrametric; a violation means the MST/maximin path is wrong."""
    grid = (0.2, 0.4, 0.6, 0.8, 0.95)
    graph = MirrorGraph.build(_two_cluster_view(), sigma=grid[0])
    forest = build_max_spanning_tree(graph)
    digests = [graph.digest(i) for i in range(graph.n)]

    def ss(x: str, y: str) -> float | None:
        return sigma_star(forest, x, y, grid=grid).sigma_star

    checked = 0
    for a, b, c in itertools.permutations(digests, 3):
        ac, ab, bc = ss(a, c), ss(a, b), ss(b, c)
        if ac is None or ab is None or bc is None:
            continue
        assert ac >= min(ab, bc) - 1e-12
        checked += 1
    assert checked > 0                                    # the corpus actually exercised the law


def test_unconnected_pair_reports_not_connected_within_grid() -> None:
    """Two isolated single-node components (orthogonal vectors, no edge at the loosest grid) ⇒ σ* is
    None and the chain is empty — the honest bounded answer, never −∞ or 0."""
    rows = [_row("x", [1.0, 0, 0, 0]), _row("y", [0.0, 1, 0, 0])]
    grid = (0.5, 0.9)
    graph = MirrorGraph.build(_view(rows), sigma=grid[0])
    forest = build_max_spanning_tree(graph)
    ss = sigma_star(forest, "x", "y", grid=grid)
    assert ss.sigma_star is None and ss.chain == ()


def test_realizing_chain_is_a_real_mst_path_whose_bottleneck_snaps_to_sigma_star() -> None:
    """Falsifier (d): the reported chain is an actual tree path (consecutive nodes tree-adjacent)
    and its min-cosine edge grid-snaps to the reported σ*."""
    grid = (0.2, 0.4, 0.6, 0.8, 0.95)
    graph = MirrorGraph.build(_two_cluster_view(), sigma=grid[0])
    forest = build_max_spanning_tree(graph)
    tree_pairs = {
        (u, v) for u in forest.tree_adj for v, _w in forest.tree_adj[u]
    }
    digests = [graph.digest(i) for i in range(graph.n)]
    for a, b in itertools.combinations(digests, 2):
        ss = sigma_star(forest, a, b, grid=grid)
        if ss.sigma_star is None:
            continue
        assert ss.chain[0] == a and ss.chain[-1] == b
        # every consecutive step is a real MST edge …
        idx = forest.index_of
        edge_cosines = []
        for u, v in zip(ss.chain, ss.chain[1:], strict=False):
            assert (idx[u], idx[v]) in tree_pairs
            edge_cosines.append(float(graph.sim[idx[u], idx[v]]))
        # … and the path bottleneck grid-snaps to the reported σ*
        bottleneck = min(edge_cosines)
        snapped = max(g for g in grid if g <= bottleneck + 1e-12)
        assert ss.sigma_star == pytest.approx(snapped)


def test_forest_is_a_forest_when_the_loosest_grid_graph_is_disconnected() -> None:
    """Two clusters with ZERO cross-edges at the loosest grid ⇒ a spanning FOREST (2 components); a
    within-cluster pair connects, a cross-cluster pair is None."""
    rows = [_row("a0", [1.0, 0, 0, 0]), _row("a1", [0.99, 0.14, 0, 0]),
            _row("b0", [0.0, 0, 1, 0]), _row("b1", [0.0, 0, 0.99, 0.14])]
    grid = (0.8, 0.95)
    graph = MirrorGraph.build(_view(rows), sigma=grid[0])
    forest = build_max_spanning_tree(graph)
    assert isinstance(forest, MaxSpanningForest)
    assert len(set(forest.component)) == 2                # two components
    assert sigma_star(forest, "a0", "a1", grid=grid).sigma_star is not None
    assert sigma_star(forest, "a0", "b0", grid=grid).sigma_star is None


def test_all_pairs_summary_covers_every_pair() -> None:
    grid = (0.2, 0.6, 0.95)
    graph = MirrorGraph.build(_two_cluster_view(), sigma=grid[0])
    forest = build_max_spanning_tree(graph)
    pairs = pairwise_sigma_star(forest, grid=grid)
    assert len(pairs) == graph.n * (graph.n - 1) // 2
    # sorted strongest-first: connected (non-None) σ* values are in descending order
    vals = [p.sigma_star for p in pairs if p.sigma_star is not None]
    assert vals == sorted(vals, reverse=True)
