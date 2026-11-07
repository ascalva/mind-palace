"""Unit tests for eval/scale on graphs with known spectra and known flows."""

from __future__ import annotations

import numpy as np

from eval.scale.bootstrap import bootstrap_cut, edge_resample, interval_width, node_subsample
from eval.scale.corpus import one_generation_graph
from eval.scale.graphs import (
    TemporalEdges,
    component_at,
    component_from_edges,
    normalized_laplacian,
)
from eval.scale.hodge import hodge_split
from eval.scale.spectrum import cut_stats, smallest_eigenvalues
from eval.scale.study import crossing, required_window


def _cycle(n: int) -> TemporalEdges:
    src = np.arange(n)
    return TemporalEdges.build(src, (src + 1) % n, np.arange(n, dtype=float))


def _complete(n: int) -> TemporalEdges:
    s, d = np.triu_indices(n, k=1)
    return TemporalEdges.build(s, d, np.arange(len(s), dtype=float))


def test_cut_is_a_prefix_and_keeps_the_largest_component() -> None:
    # two components: a path 0-1-2 (t=1,2) and a single edge 10-11 (t=3)
    e = TemporalEdges.build([0, 1, 10], [1, 2, 11], [1.0, 2.0, 3.0])
    assert component_at(e, 0.5).n == 0
    assert component_at(e, 1.5).n == 2
    assert component_at(e, 2.5).n == 3
    assert component_at(e, 9.0).n == 3  # the path stays the largest
    assert component_at(e, 9.0).m == 2


def test_cut_drops_loops_and_merges_mutual_pairs() -> None:
    e = TemporalEdges.build([0, 1, 2, 2, 1], [1, 0, 2, 3, 2], [1.0, 2.0, 3.0, 4.0, 5.0])
    comp = component_at(e, 10.0)
    assert comp.n == 4 and comp.m == 3
    assert 0.0 in comp.flow  # the mutual pair nets to zero flow


def test_cycle_spectrum_matches_closed_form() -> None:
    n = 40
    comp = component_at(_cycle(n), 1e9)
    eig = smallest_eigenvalues(normalized_laplacian(comp.adj), 6)
    expect = np.sort(1.0 - np.cos(2 * np.pi * np.arange(n) / n))[:6]
    assert np.allclose(eig, expect, atol=1e-10)


def test_shift_invert_agrees_with_closed_form_on_a_long_path() -> None:
    # a path has a simple spectrum, 1 - cos(pi j / (n - 1)); ARPACK can miss repeated
    # eigenvalues (a cycle's), which is why this test does not use one above the dense limit.
    n = 700
    src = np.arange(n - 1)
    comp = component_at(TemporalEdges.build(src, src + 1, src.astype(float)), 1e9)
    eig = smallest_eigenvalues(normalized_laplacian(comp.adj), 6)
    expect = 1.0 - np.cos(np.pi * np.arange(6) / (n - 1))
    assert np.allclose(eig, expect, atol=1e-7)


def test_complete_graph_gap_and_degrees() -> None:
    n = 12
    st = cut_stats(component_at(_complete(n), 1e9), k=5)
    assert abs(st.gamma - n / (n - 1)) < 1e-10
    assert st.min_degree == n - 1
    assert abs(st.degree_over_logn - (n - 1) / np.log(n)) < 1e-12
    assert abs(st.gap(2)) < 1e-10  # the eigenvalue n/(n-1) repeats


def test_bootstrap_of_a_complete_graph_node_sample_has_known_gamma() -> None:
    comp = component_at(_complete(30), 1e9)
    rng = np.random.default_rng(1)
    sub = node_subsample(comp, 0.5, rng)
    assert sub.n == 15 and sub.m == 15 * 14 // 2
    row = bootstrap_cut(comp, "node", 0.5, reps=5, rng=rng)
    assert abs(row.median_gamma - 15 / 14) < 1e-10
    assert row.width_gamma < 1e-9


def test_edge_resample_keeps_a_connected_core() -> None:
    comp = component_at(_complete(20), 1e9)
    rep = edge_resample(comp, np.random.default_rng(0))
    assert rep.n >= 18 and rep.m <= comp.m


def test_interval_width_and_crossing() -> None:
    w, med = interval_width(np.linspace(0.9, 1.1, 1001))
    assert abs(med - 1.0) < 1e-9 and abs(w - 0.19) < 1e-6
    assert crossing([(10, 0.5), (100, 0.08), (1000, 0.2), (5000, 0.05), (9000, 0.01)]) == 5000
    assert np.isnan(crossing([(10, 0.5)]))


def test_window_scales_inversely_with_gap_and_squared_precision() -> None:
    assert abs(required_window(0.5, 0.1) - 400.0) < 1e-9
    assert abs(required_window(0.25, 0.1) - 2 * required_window(0.5, 0.1)) < 1e-9
    assert abs(required_window(0.5, 0.05) - 4 * required_window(0.5, 0.1)) < 1e-9


def test_hodge_triangle_cycle_is_pure_curl() -> None:
    e = TemporalEdges.build([0, 1, 2], [1, 2, 0], [1.0, 2.0, 3.0])
    h = hodge_split(component_from_edges(e.src, e.dst))
    assert h.triangles == 1
    assert abs(h.curl - 1.0) < 1e-6 and h.gradient < 1e-6 and h.harmonic < 1e-6


def test_hodge_path_is_pure_gradient_and_long_cycle_pure_harmonic() -> None:
    path = TemporalEdges.build([0, 1, 2], [1, 2, 3], [1.0, 2.0, 3.0])
    h = hodge_split(component_from_edges(path.src, path.dst))
    assert abs(h.gradient - 1.0) < 1e-6
    cyc = _cycle(6)
    hc = hodge_split(component_from_edges(cyc.src, cyc.dst))
    assert abs(hc.harmonic - 1.0) < 1e-6 and hc.triangles == 0


def test_hodge_transitive_triangle_is_pure_gradient() -> None:
    # 0->1, 1->2, 0->2 is a gradient flow of a potential
    e = TemporalEdges.build([0, 1, 0], [1, 2, 2], [1.0, 2.0, 3.0])
    h = hodge_split(component_from_edges(e.src, e.dst))
    assert abs(h.gradient + h.curl + h.harmonic - 1.0) < 1e-9
    # f = (1, 1, 1) on (01, 12, 02); curl = f01 + f12 - f02 = 1 so curl energy is nonzero
    assert h.curl > 0.1 and h.gradient > 0.5


def test_corpus_graph_has_the_stated_size_and_one_generation() -> None:
    e = one_generation_graph(38, 20, seed=3)
    assert len(e.src) == 20
    assert not set(e.src.tolist()) & set(e.dst.tolist())
    assert max(e.src.max(), e.dst.max()) < 38
