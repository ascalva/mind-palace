"""The frustration measurement reads the relation edges as the store holds them, a multigraph
(the review of 2026-11-05: it summed parallel edges, so a pair that both supports and contradicts
cancelled to no edge, read as balanced, and its single flips were no-ops)."""

from __future__ import annotations

from core.sentence.execute import Relation, _balanced
from eval.frustration_lift import Edge, frustration, lam_min, measure, nodes_of


def test_a_pair_that_supports_and_contradicts_is_frustrated() -> None:
    edges = [Edge("a", "b", 1.0, 1, "supports"), Edge("a", "b", 0.5, -1, "contradicts")]
    nodes = nodes_of(edges)
    assert not _balanced([Relation(e.u, e.v, e.sign, e.rel_type, e.w) for e in edges])
    fr = frustration(edges, nodes)
    assert fr == (0.5, 1)                              # flip the lighter one
    assert lam_min(edges, nodes) > 1e-9                # the zero mode is lifted
    report = "\n".join(measure(edges))
    assert "balanced: False" in report and "VIOLATES" not in report


def test_a_balanced_triangle_stays_balanced_and_one_flip_frustrates_it() -> None:
    edges = [Edge("a", "b", 1.0, 1, "supports"), Edge("b", "c", 1.0, -1, "contradicts"),
             Edge("a", "c", 1.0, -1, "contradicts")]
    nodes = nodes_of(edges)
    assert frustration(edges, nodes) == (0.0, 0) and abs(lam_min(edges, nodes)) < 1e-9
    report = measure(edges)
    assert all("ok" in line for line in report if line.startswith("   "))
