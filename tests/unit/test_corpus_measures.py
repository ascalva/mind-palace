"""The stage-1 measurement harness on small synthetic corpora (dn-corpus-instance §6): each reading
checked against what it must find, with a control that must not find it."""

from __future__ import annotations

import itertools
import json
import math
import sqlite3
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from eval.corpus import battery, bridges, edges, footprint, macro, rises
from eval.corpus.data import Corpus, day, load
from eval.corpus.edges import Relation


def _corpus(tmp_path: Path, items: dict[str, list[dict[str, Any]]]) -> Corpus:
    for source, metas in items.items():
        d = tmp_path / source / "meta"
        d.mkdir(parents=True, exist_ok=True)
        (d / "items.jsonl").write_text("".join(json.dumps(m) + "\n" for m in metas))
    return load(tmp_path, tuple(items))


def test_relations_and_bridges_resolve_only_within_the_corpus(tmp_path):
    c = _corpus(tmp_path, {
        "wikipedia": [{"id": "1", "title": "Graph theory", "date": "2003-01-01",
                       "links": ["Planar graph", "Elsewhere"],
                       "cites": [{"doi": "10.1/A", "title": "A"}, {"arxiv": "2101.00001"}],
                       "gutenberg": [5]},
                      {"id": "2", "title": "Planar graph", "date": "2004-01-01", "links": []}],
        "openalex": [{"id": "W1", "date": "2020-01-01", "doi": "https://doi.org/10.1/a",
                      "refs": ["W2", "W9"], "arxiv": "2101.00001"},
                     {"id": "W2", "date": "2019-01-01", "refs": []}],
        "arxiv": [{"id": "2101.00001", "arxiv_id": "2101.00001", "date": "2021-01-01",
                   "versions": ["2021-01-01", "2021-03-01"]}],
        "stackexchange": [{"id": "cs-1", "kind": "question", "date": "2015-01-01",
                           "links": {"wikipedia": ["Graph theory"], "arxiv": [], "doi": []},
                           "post_links": [["cs-2", "duplicate"]]},
                          {"id": "cs-2", "kind": "answer", "parent": "cs-1",
                           "date": "2015-02-01", "links": {}}],
        "gutenberg": [{"id": "pg5", "ebook": 5, "date": "1995-01-01"}],
    })
    rel = edges.build(c)
    g = c.gid
    assert rel["wikipedia.hyperlink"].src.tolist() == [g["corpus/wikipedia/1"]]
    assert rel["wikipedia.hyperlink"].t.tolist() == [day("2004-01-01")]     # the later page
    assert rel["openalex.citation"].m == 1                                     # W9 is outside
    assert rel["stackexchange.answer"].m == 1 and rel["stackexchange.link"].m == 1
    assert rel["arxiv.version"].m == 1
    for name in ("wikipedia-openalex", "wikipedia-arxiv", "wikipedia-gutenberg",
                 "stackexchange-wikipedia", "openalex-arxiv"):
        assert rel[f"bridge.{name}"].m == 1, name
    tw = edges.twins(rel)
    assert tw[g["corpus/openalex/W1"]] == g["corpus/arxiv/2101.00001"]
    report = edges.save(rel, tmp_path / "edges")
    assert report["openalex.citation"]["edges"] == 1
    assert np.load(tmp_path / "edges" / "openalex.citation.npy").dtype == np.int32


def test_the_effective_count_is_ci2s():
    finite, limit = rises.n_eff(0.5, 0.0, 4, 1e9)
    assert limit == pytest.approx(8.0) and finite == pytest.approx(8.0, rel=1e-6)
    finite, limit = rises.n_eff(0.5, 0.5, 4, 1e9)
    assert limit == pytest.approx(2.0)                 # as correlated as their members: 1/rho_w
    assert rises.n_eff(0.2, 0.05, 5, 10)[0] < rises.n_eff(0.2, 0.05, 5, 10)[1]


def test_lagged_correlation_finds_a_shifted_copy_and_the_shift_null_does_not():
    rng = np.random.default_rng(0)
    base = rng.standard_normal(400)
    x = np.stack([base, np.roll(base, 3), rng.standard_normal(400)])
    r = rises.lagged_corr(x, 8)
    assert r[0, 1] > 0.95 and r[0, 2] < 0.3
    w, b = rises.rho(r, np.asarray([0, 0, 1], dtype=np.int64))
    assert w > 0.95 and b < 0.3


def test_the_configuration_model_keeps_every_degree():
    rng = np.random.default_rng(1)
    u = rng.integers(0, 200, 2000)
    v = (u + rng.integers(1, 199, 2000)) % 200
    a, b = bridges.configuration(u, v, rng)
    before = np.bincount(np.concatenate([u, v]), minlength=200)
    after = np.bincount(np.concatenate([a, b]), minlength=200)
    assert abs(int(before.sum()) - int(after.sum())) <= 0.1 * before.sum()  # loops, repeats out
    assert np.corrcoef(before, after)[0, 1] > 0.95


def _two_sources(tmp_path: Path, planted: bool
                 ) -> tuple[Corpus, dict[str, Relation], dict[int, str]]:
    n = 120
    c = _corpus(tmp_path, {"a": [{"id": f"a{i}", "date": "2020-01-01"} for i in range(n)],
                           "b": [{"id": f"b{i}", "date": "2020-01-01"} for i in range(n)]})
    rng = np.random.default_rng(2)
    within = []
    for s in (0, n):
        for _ in range(n * 4):
            i, j = rng.integers(0, n, 2)
            if i != j:
                within.append((s + i, s + j, 0))
    # planted: 300 edges concentrated between community a:0 and community b:0; random: 300
    # edges spread over every pair of communities across the two sources
    cross = [(i, n + j, 0) for i in range(30) for j in range(30)][::3] if planted else \
        [(int(rng.integers(0, n)), int(n + rng.integers(0, n)), 0) for _ in range(300)]
    part = {g: (f"a:{g // 30}" if g < n else f"b:{(g - n) // 30}") for g in range(2 * n)}

    def rel(pairs: list[tuple[int, int, int]]) -> Relation:
        arr = np.asarray(pairs, dtype=np.int64)
        return Relation("x", "s", arr[:, 0], arr[:, 1], arr[:, 2])
    return c, {"a.x": rel(within), "bridge.a-b": rel(cross)}, part


def test_planted_bridges_stand_above_the_null_and_random_ones_do_not(tmp_path):
    c, rel, part = _two_sources(tmp_path / "planted", planted=True)
    hit = bridges.measure(c, rel, part, reps=10, z=3.0)
    assert hit["bridges"] >= 1 and not hit["cif2_bridges_broken"]
    assert hit["cross_share"] < hit["null_cross_share"]
    c, rel, part = _two_sources(tmp_path / "random", planted=False)
    miss = bridges.measure(c, rel, part, reps=10, z=3.0)
    assert miss["cif2_bridges_broken"] and miss["bridges"] <= miss["false_positive_bar"]


def test_shapley_splits_a_redundant_pair_and_leave_one_out_misses_it():
    """SCL-3's witness on the harness: two sources each sufficient for every question (the
    twins), a third useless: Shapley a half each, leave-one-out zero for both (CIF-10 held)."""
    c = Corpus(Path("."), ("openalex", "arxiv", "gutenberg"))
    coalitions = [frozenset(s) for r in range(1, 4) for s in itertools.combinations(range(3), r)]
    hits = np.asarray([[bool(s & {0, 1})] * 40 for s in coalitions], dtype=np.bool_)
    qs = [battery.Question("titles:openalex", "q", frozenset({0}), "openalex", f"c{i}")
          for i in range(40)]
    out = battery.attribution(c, qs, coalitions, hits, twins={0: 1, 1: 0})
    tw = out["twinned"]
    assert tw["shapley"]["openalex"] == pytest.approx(0.5)
    assert tw["shapley"]["arxiv"] == pytest.approx(0.5)
    assert tw["shapley"]["gutenberg"] == pytest.approx(0.0)
    assert tw["loo"]["openalex"] == 0.0 and tw["loo"]["arxiv"] == 0.0
    assert sum(tw["shapley"].values()) == pytest.approx(tw["v_full"])     # efficiency
    assert not out["cif10_broken"]


def test_the_engines_top_k_is_brute_force(tmp_path):
    from eval.corpus.data import Vectors

    rng = np.random.default_rng(3)
    m = rng.standard_normal((500, 16)).astype(np.float16)
    c = Corpus(tmp_path, ("s",), paths=[f"corpus/s/{i}" for i in range(500)],
               source_of=[0] * 500, dates=[0] * 500, meta=[{}] * 500,
               gid={f"corpus/s/{i}": i for i in range(500)})
    vec = Vectors([str(i) for i in range(500)], m, [[i] for i in range(500)],
                  {i: [i] for i in range(500)})
    eng = battery.Engine(vec, c)
    q = battery.unit(rng.standard_normal((3, 16)).astype(np.float32))
    sims = eng.sims(q, step=128)
    top = eng.topk(sims, np.arange(500))
    unitm = battery.unit(m.astype(np.float32))
    for r in range(3):
        assert top[r].tolist() == np.argsort(-(unitm @ q[r]))[:10].tolist()
    assert eng.topk(sims, np.arange(0)).shape == (3, 0)


def test_the_dense_solver_agrees_with_the_shift_invert_one():
    from eval.scale.graphs import component_from_edges
    from eval.scale.spectrum import smallest_eigenvalues

    rng = np.random.default_rng(4)
    n = 900
    src = rng.integers(0, n, n * 40)
    dst = rng.integers(0, n, n * 40)
    comp = component_from_edges(src, dst)
    assert comp.degrees().mean() > macro.DENSE_DEGREE
    from eval.scale.graphs import normalized_laplacian
    fast = macro.eigenvalues(comp, 6)
    slow = smallest_eigenvalues(normalized_laplacian(comp.adj), 6)
    assert np.allclose(fast, slow, atol=1e-7)


def test_cuts_follow_the_ladder_and_the_crossing_is_the_scale_studys():
    t = np.arange(40, dtype=np.int64)
    r = Relation("x", "s", np.arange(40, dtype=np.int64), np.arange(1, 41, dtype=np.int64), t)
    cuts = macro.cut_times(r, (5, 20))
    assert [c[0] for c in cuts] == [5, 20, 41] and cuts[0][1] == 3.0
    curve = {"cuts": [{"boot": [{"n_mean": 100, "width_gamma": 0.3},
                                {"n_mean": 1000, "width_gamma": 0.05}]}]}
    assert macro.crossings(curve)["full.width_gamma"] == 1000.0


def test_the_compact_occupancy_is_one_integer_row_an_item_version(tmp_path):
    plane = tmp_path / "plane.sqlite"
    con = sqlite3.connect(plane)
    con.execute("CREATE TABLE occ_observed (source_path TEXT, digest TEXT, chunk_index INT, "
                "atom_id TEXT, row_id TEXT, title TEXT, current INT, landed_at TEXT)")
    rows = [(f"corpus/s/{i}", f"d{i}", k, f"a{i}{k}", "r", "t", 1, "2026-11-07T00:00:00")
            for i in range(200) for k in range(3)]
    con.executemany("INSERT INTO occ_observed VALUES (?, ?, ?, ?, ?, ?, ?, ?)", rows)
    con.commit()
    con.close()
    out = footprint.compact_occupancy(plane, tmp_path / "compact.sqlite")
    assert out["rows"] == 200 and out["chunk_occupancies"] == 600
    assert out["bytes_per_row"] < 300 and not math.isnan(out["bytes_per_row"])
    assert footprint.plane_bytes(plane)["occupancies"] == 600


def test_the_cost_split_counts_compiled_frames_apart_from_python():
    from eval.corpus.cost import split

    Row = tuple[int, int, float, float, dict[str, int]]

    class S:
        stats: dict[tuple[str, int, str], Row] = {
                 ("/x/site-packages/numpy/core.py", 1, "dot"): (1, 1, 2.0, 2.0, {}),
                 ("~", 0, "<method 'execute' of 'sqlite3.Connection' objects>"):
                     (1, 1, 1.0, 1.0, {}),
                 ("/x/core/sentence/universe.py", 9, "add"): (1, 1, 1.0, 1.0, {}),
                 ("~", 0, "<method 'control' of 'select.kqueue' objects>"): (1, 1, 4.0, 4.0, {})}
    out = split(S())   # type: ignore[arg-type]
    assert out["compiled"] == 3.0 and out["python"] == 1.0 and out["wait"] == 4.0
    assert out["python_share"] == pytest.approx(1 / 8)


def test_the_semantic_neighbours_and_chunk_pairs_are_brute_force(tmp_path):
    from eval.corpus.data import Vectors

    rng = np.random.default_rng(3)
    x = rng.normal(size=(40, 8)).astype(np.float32)
    x /= np.linalg.norm(x, axis=1, keepdims=True)
    have = np.ones(40, dtype=bool)
    have[[5, 17]] = False                                  # pending: neither ask nor answer
    i, j, v = bridges.knn(x, have, k=3, sigma=0.2, block=7)
    sim = x @ x.T
    want = set()
    idx = np.flatnonzero(have)
    for a in idx:
        row = [(sim[a, b], b) for b in idx if b != a]
        for s, b in sorted(row, reverse=True)[:3]:
            if s >= 0.2:
                want.add((min(a, b), max(a, b)))
    assert set(zip(i.tolist(), j.tolist(), strict=True)) == want
    assert np.allclose(v, sim[i, j], atol=1e-5)
    m = x.astype(np.float16)
    q = np.asarray([0, 9, 33], dtype=np.int64)
    assert np.allclose(bridges._blocked(m, q, step=6),
                       m[q].astype(np.float32) @ m.astype(np.float32).T, atol=1e-6)
    c = _corpus(tmp_path, {"wikipedia": [{"id": str(n)} for n in range(4)],
                           "arxiv": [{"id": str(n)} for n in range(4)]})
    rows = np.asarray([[1, 0], [1, 0], [0.9, 0.436], [0, 1], [0.1, 0.995]], dtype=np.float16)
    vec = Vectors([f"a{r}" for r in range(5)], rows, [[0], [1], [4], [5], [5]],
                  {0: [0], 1: [1], 4: [2], 5: [3, 4]})
    out = bridges.chunk_pairs(c, vec, sigma=0.8, sample=5, block=2)
    # rows 0, 1, 2 are close to one another; rows 3 and 4 too, but share an item (5); each
    # asking chunk counts its own neighbours
    assert out["asked"] == {"wikipedia": 2, "arxiv": 3}
    assert out["pairs_per_chunk"]["wikipedia->wikipedia"] == 1.0
    assert out["pairs_per_chunk"]["wikipedia->arxiv"] == 1.0
    assert out["pairs_per_chunk"]["arxiv->wikipedia"] == round(2 / 3, 4)
    assert out["pairs_per_chunk"]["arxiv->arxiv"] == 0.0


def test_the_codes_built_by_blocks_are_the_codes_of_one_pass(tmp_path):
    from eval.corpus import codes

    rng = np.random.default_rng(5)
    m = rng.normal(size=(53, 768)).astype(np.float16)
    report = codes.build(m, [f"a{i}" for i in range(53)], tmp_path / "c", block=10)
    x = codes._unit(m.astype(np.float32))
    c8, lo8, sc8 = codes.minmax_codes(x)
    assert np.array_equal(np.load(tmp_path / "c" / "int8_768.npy"), c8)
    p = codes._unit(np.ascontiguousarray(x[:, :256]))
    c2, _, _ = codes.minmax_codes(p)
    assert np.array_equal(np.load(tmp_path / "c" / "int8_256.npy"), c2)
    assert np.array_equal(np.load(tmp_path / "c" / "f16_256.npy"), p.astype(np.float16))
    assert np.array_equal(np.load(tmp_path / "c" / "bits_768.npy"), np.packbits(x >= 0, axis=1))
    assert report["bytes_per_vector"]["bits_768.npy"] < 100        # 96 bytes and a header share
    q = rng.normal(size=(4, 768)).astype(np.float32)
    pv = codes.preview(m, tmp_path / "c", q, k=5, m=20, block=7)
    assert pv["f16_256"]["rescored_m20"] >= pv["f16_256"]["flat"] - 1e-9
    assert all(0.0 <= pv[k]["flat"] <= 1.0 for k in ("int8_768", "f16_256", "int8_256", "bits_768"))
