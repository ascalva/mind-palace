"""The killed walk's component solve returns row for row what the full dense inverse returns, to
rounding (RSP-1 to RSP-5 are about the exact solution; the route is not part of the law)."""

from __future__ import annotations

import numpy as np
import pytest

from core.query import free_energy_distances, free_energy_distances_from


def _backbone(n: int, seed: int, k: int = 8, comps: int = 1) -> np.ndarray:
    """A symmetric k-nearest-neighbour weight matrix over `comps` separate clouds, weights in
    (0.62, 1], a zero diagonal; some nodes isolated when a cloud is small."""
    r = np.random.default_rng(seed)
    w = np.zeros((n, n))
    cuts = np.linspace(0, n, comps + 1).astype(int)
    for lo, hi in zip(cuts[:-1], cuts[1:], strict=True):
        m = hi - lo
        x = r.standard_normal((m, 12)) + 0.4 * r.standard_normal((1, 12))
        x /= np.linalg.norm(x, axis=1, keepdims=True)
        sims = x @ x.T
        np.fill_diagonal(sims, -1)
        for i in range(m):
            for j in np.argsort(-sims[i])[:min(k, m - 1)]:
                v = 0.62 + 0.38 * r.random()
                w[lo + i, lo + j] = w[lo + j, lo + i] = v
    return w


@pytest.mark.parametrize("n,comps", [(100, 1), (100, 3), (1000, 1), (1000, 7)])
@pytest.mark.parametrize("beta", [0.3, 1.0, 4.0])
def test_component_rows_equal_the_full_rows(n: int, comps: int, beta: float) -> None:
    w = _backbone(n, seed=n + comps, comps=comps)
    dense = free_energy_distances(w, beta=beta)
    for source in (0, n // 3, n - 1):
        row = free_energy_distances_from(w, source, beta=beta, method="component")
        assert np.array_equal(np.isinf(row), np.isinf(dense[source]))
        assert np.allclose(row, dense[source], rtol=1e-10, atol=1e-10, equal_nan=True)


def test_degrees_larger_than_the_supports_own_are_honoured() -> None:
    """RSP-5: a support whose complement absorbs, the census degrees above the support's own."""
    w = _backbone(200, seed=5)
    deg = w.sum(axis=1) * (1.0 + np.random.default_rng(1).random(200))
    dense = free_energy_distances(w, beta=1.0, degrees=deg)
    for source in (0, 99, 199):
        row = free_energy_distances_from(w, source, beta=1.0, degrees=deg, method="component")
        assert np.allclose(row, dense[source], rtol=1e-10, atol=1e-10)


def test_an_isolated_source_reaches_nothing() -> None:
    w = _backbone(60, seed=2)
    w[7, :] = w[:, 7] = 0.0
    row = free_energy_distances_from(w, 7, beta=1.0, method="component")
    assert row[7] == 0.0 and np.isinf(np.delete(row, 7)).all()
    assert np.allclose(row, free_energy_distances(w, beta=1.0)[7])


def test_auto_is_the_dense_row_below_the_crossover_and_the_same_walk_above() -> None:
    w = _backbone(60, seed=3)
    assert np.array_equal(free_energy_distances_from(w, 4, beta=1.0),
                          free_energy_distances(w, beta=1.0)[4])      # bitwise: it is that code
    with pytest.raises(ValueError, match="at least the support's own"):
        free_energy_distances_from(w, 4, beta=1.0, degrees=w.sum(axis=1) * 0.5, method="component")


def test_diffuse_returns_the_same_hits_whichever_route_the_support_size_picks(
        monkeypatch: pytest.MonkeyPatch) -> None:
    import importlib

    from core.sentence import Universe, compile_sentence, execute
    from core.sentence.ast import Rel

    ex = importlib.import_module("core.sentence.execute")
    n = 40
    w = _backbone(n, seed=11, k=4, comps=2)
    notes = [{"source_path": f"n{i}.md", "title": f"N{i}", "digest": f"d{i}",
              "provenance": "authored_solo"} for i in range(n)]
    edges: dict[Rel, dict[str, set[str]]] = {Rel.F: {}, Rel.D: {}, Rel.C: {}}

    def universe() -> Universe:
        return Universe(notes, np.eye(n), w, edges, [], lambda t: np.ones(n), lambda a: [],
                        lambda e: None)

    for text in ('top 30 diffuse S from "n0.md"', 'top 30 diffuse S from "n25.md" beta 2'):
        dense = execute(compile_sentence(text), universe())
        monkeypatch.setattr(ex, "COMPONENT_SOLVE_ABOVE", 0)        # every support counts as large
        sparse = execute(compile_sentence(text), universe())
        monkeypatch.undo()
        assert [h.ref for h in dense.hits] == [h.ref for h in sparse.hits]
        got = [h.score or 0.0 for h in sparse.hits]
        assert np.allclose([h.score or 0.0 for h in dense.hits], got, rtol=1e-9, atol=1e-12)
        assert len(dense.hits) > 3
