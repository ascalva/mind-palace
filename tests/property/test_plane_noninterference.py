"""Noninterference for the shared plane (dn-vector-membership-store A3.5; Goguen & Meseguer 1982).

The owner's no-leak requirement as a law: for every clearance C, every read under C is a function
of the cleared relations M_C and the atoms they reference — so two planes that differ ONLY in the
relations of classes outside C answer every C-read identically. Hypothesis draws documents in every
plane class over a small shared vocabulary (so atoms really are shared across strata), a clearance
that excludes at least one class, and a mutation confined to the excluded classes: new documents,
new versions, retirements, landed before AND after the cleared ones.

The seeded-leak control proves the property has teeth: a reader whose relation list ignores its
clearance must break it.
"""

from __future__ import annotations

import itertools
import tempfile
from pathlib import Path
from typing import Any

import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from core.kernel import clearance as cl
from core.kernel.provenance import Provenance
from core.kernel.scope import (
    Authority,
    Clock,
    EdgeScope,
    Scope,
    Stratum,
    StratumScope,
    Tier,
    TimeScope,
    Window,
)
from core.stores import plane as plane_mod
from core.stores.plane import PLANE_CLASSES, SharedPlane
from tests.fixtures.fakes import HashingEmbedder
from tests.fixtures.plane_fakes import MemoryAtoms

EMB = HashingEmbedder(16)
VOCAB = ["the owner's plan", "a shared sentence", "lean proofs", "vector atoms", "zipf law",
         "heartbeat tick", "papers about graphs", "model reply"]
QUERIES = [EMB.embed_query(t) for t in [*VOCAB, "something else entirely"]]

texts = st.lists(st.sampled_from(VOCAB), min_size=1, max_size=4)
document = st.tuples(st.sampled_from(PLANE_CLASSES), st.lists(texts, min_size=1, max_size=3))


def _land_doc(p: SharedPlane, path: str, cls: Provenance, versions: list[list[str]],
              tag: str) -> None:
    for v, chunk_texts in enumerate(versions):
        p.land([{"source_path": path, "digest": f"{tag}{v}:{'|'.join(chunk_texts)}",
                 "provenance": cls.value, "title": path, "chunk_index": i, "text": t,
                 "vector": EMB.embed_query(t)} for i, t in enumerate(chunk_texts)])


def _observe(p: SharedPlane, c: cl.Clearance[Provenance], paths: list[str]) -> dict[str, Any]:
    """Everything a reader under `c` can say — the observation the law quantifies over."""
    r = p.reader(c)

    def rows(include_superseded: bool) -> list[tuple[Any, ...]]:
        return sorted(tuple(sorted((k, str(v)) for k, v in row.items()))
                      for row in r.rows(include_superseded=include_superseded))

    def hits(q: list[float], sup: bool) -> list[tuple[Any, ...]]:
        return [(h.atom_id, h.text, h.distance,
                 tuple((o.source_path, o.digest, o.chunk_index, o.provenance.value, o.current)
                       for o in h.occupancies))
                for h in r.search(q, k=3, include_superseded=sup)]

    return {
        "rows": rows(False), "rows_all": rows(True),
        "hits": [hits(q, s) for q in QUERIES for s in (False, True)],
        "search_rows": [[(x["source_path"], x["chunk_index"], x["_distance"])
                         for x in r.search_rows(q, k=4)] for q in QUERIES],
        "count": (r.count(), r.count(include_superseded=True)),
        "gauges": {k.value: (g.occupancies, g.atoms, g.documents) for k, g in r.gauges().items()},
        "freq": (r.rank_frequency(), r.rank_frequency(current_only=True)),
        "history": {p_: [(h["old_digest"], h["new_digest"]) for h in r.history(p_)]
                    for p_ in paths},
        "digests": sorted(o.digest for o in r.occupancies(include_superseded=True)),
    }


def _world(directory: Path, docs: list[tuple[Provenance, list[list[str]]]],
           extra: list[tuple[Provenance, list[list[str]]]], retire: list[int],
           c: cl.Clearance[Provenance]) -> tuple[SharedPlane, list[str]]:
    p = SharedPlane(directory, MemoryAtoms())
    half = len(extra) // 2
    for j, (cls, versions) in enumerate(extra[:half]):            # uncleared, landed before
        _land_doc(p, f"x/{j}", cls, versions, "x")
    paths = []
    for i, (cls, versions) in enumerate(docs):
        path = f"doc/{i}"
        paths.append(path)
        _land_doc(p, path, cls, versions, "d")
    for j, (cls, versions) in enumerate(extra[half:], start=half):  # uncleared, landed after
        _land_doc(p, f"x/{j}", cls, versions, "x")
    for i in retire:
        if 0 <= i < len(extra):
            p.retire(f"x/{i}")
    return p, paths


@settings(max_examples=150, deadline=None,
          suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow])
@given(docs=st.lists(document, min_size=1, max_size=5),
       cleared=st.sets(st.sampled_from(PLANE_CLASSES), min_size=1,
                       max_size=len(PLANE_CLASSES) - 1),
       extra_versions=st.lists(st.lists(texts, min_size=1, max_size=3), min_size=1, max_size=4),
       retire=st.lists(st.integers(0, 3), max_size=2),
       data=st.data())
def test_reads_under_a_clearance_ignore_every_uncleared_relation(docs, cleared, extra_versions,
                                                                 retire, data):
    c = cl._mint(cleared, "property")
    outside = [p for p in PLANE_CLASSES if p not in cleared]
    extra = [(data.draw(st.sampled_from(outside)), v) for v in extra_versions]
    # The clearance sees the cleared documents; the uncleared documents of `docs` stay in BOTH
    # worlds (they are part of the shared state), and `extra` is the mutation, all uncleared.
    with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
        base, paths = _world(Path(a), docs, [], [], c)
        mutated, _ = _world(Path(b), docs, extra, retire, c)
        assert any(cls in cleared for cls, _ in docs) or True     # empty-cleared is still a law
        assert mutated.atoms.ids() >= base.atoms.ids()            # precondition: B ⊇ A physically
        assert _observe(base, c, paths) == _observe(mutated, c, paths)


def test_seeded_leak_breaks_the_law(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Teeth: a reader that reads every relation regardless of its clearance must make a mirror
    observation depend on an observed document — on exactly the kind of world the property draws."""
    mirror = cl.MIRROR_READ
    docs: list[tuple[Provenance, list[list[str]]]] = [(Provenance.AUTHORED_SOLO,
                                                       [["the owner's plan"]])]
    extra: list[tuple[Provenance, list[list[str]]]] = [(Provenance.OBSERVED,
                                                        [["the owner's plan", "model reply"]])]
    honest_a, paths = _world(tmp_path / "a", docs, [], [], mirror)
    honest_b, _ = _world(tmp_path / "b", docs, extra, [], mirror)
    assert _observe(honest_a, mirror, paths) == _observe(honest_b, mirror, paths)

    def leaky_init(self: Any, plane: SharedPlane, clearance: Any) -> None:
        self._plane, self._clearance = plane, cl.MAINTENANCE_READ    # ignores the clearance
        self._tables = tuple((p, plane_mod.OCC[p], plane_mod.SUP[p]) for p in PLANE_CLASSES)

    monkeypatch.setattr(plane_mod.PlaneReader, "__init__", leaky_init)
    assert _observe(honest_a, mirror, paths) != _observe(honest_b, mirror, paths)


def test_every_pair_of_disjoint_reads_is_independent(tmp_path: Path) -> None:
    """Exhaustive over class pairs: landing a document in class y never changes a read that clears
    only class x (x ≠ y) — the property's smallest instances, all of them, not a sample."""
    for x, y in itertools.permutations(PLANE_CLASSES, 2):
        cx = cl._mint({x}, "pair")
        before, paths = _world(tmp_path / f"{x.value}-{y.value}-a", [(x, [["vector atoms"]])], [],
                               [], cx)
        after, _ = _world(tmp_path / f"{x.value}-{y.value}-b", [(x, [["vector atoms"]])],
                          [(y, [["vector atoms", "zipf law"]])], [0], cx)
        assert _observe(before, cx, paths) == _observe(after, cx, paths), (x, y)


# ── BRG-5: delegation cannot leak through the plane ─────────────────────────────────────────────

GRANTABLE = [s for s in Stratum if s is not Stratum.FOUNDATION]


def _scope(strata: set[Stratum]) -> Scope:
    """A read-only scope over `strata`, on one clock with an unbounded window (no SLICE cut)."""
    return Scope(StratumScope.of(*strata), EdgeScope.of("F"), TimeScope(Clock.COMMIT, Window.all()),
                 Authority.read_only(), tier=Tier.STATIC_GUARD)


@settings(max_examples=100, deadline=None,
          suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow])
@given(parent=st.sets(st.sampled_from(GRANTABLE), max_size=5),
       template=st.sets(st.sampled_from(GRANTABLE), max_size=5),
       docs=st.lists(document, min_size=1, max_size=4),
       extra_versions=st.lists(st.lists(texts, min_size=1, max_size=3), min_size=1, max_size=3),
       retire=st.lists(st.integers(0, 2), max_size=2),
       data=st.data())
def test_a_delegated_scope_cannot_read_past_its_parent_through_the_plane(parent, template, docs,
                                                                         extra_versions, retire,
                                                                         data):
    """BRG-5: a delegated scope, `meet(parent, template)`, is cleared (`clearance_of`) for no class
    its parent is not; and on two planes that differ only by writes and retirements in classes the
    parent is not cleared for, landed before and after the shared ones, the parent's reads agree
    and so do the delegate's: delegation composed with noninterference."""
    p_scope = _scope(parent)
    child = p_scope.meet(_scope(template))
    c_parent, c_child = cl.clearance_of(p_scope), cl.clearance_of(child)
    assert c_child.classes <= c_parent.classes
    outside = [c for c in PLANE_CLASSES if c not in c_parent.classes]
    assume(outside)
    extra = [(data.draw(st.sampled_from(outside)), v) for v in extra_versions]
    with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
        base, paths = _world(Path(a), docs, [], [], c_child)
        mutated, _ = _world(Path(b), docs, extra, retire, c_child)
        assert _observe(base, c_parent, paths) == _observe(mutated, c_parent, paths)
        assert _observe(base, c_child, paths) == _observe(mutated, c_child, paths)


def test_the_delegation_check_rejects_a_widening(tmp_path: Path) -> None:
    """Control: a join in place of the meet widens the scope past its parent. The mirror parent
    cannot tell apart two planes that differ by a curated paper; the widened scope can."""
    p_scope = _scope({Stratum.MIRROR})
    widened = p_scope.join(_scope({Stratum.CURATED}))
    c_parent, c_wide = cl.clearance_of(p_scope), cl.clearance_of(widened)
    assert not c_wide.classes <= c_parent.classes
    docs: list[tuple[Provenance, list[list[str]]]] = [(Provenance.AUTHORED_SOLO,
                                                       [["the owner's plan"]])]
    extra: list[tuple[Provenance, list[list[str]]]] = [(Provenance.CURATED,
                                                        [["papers about graphs"]])]
    base, paths = _world(tmp_path / "a", docs, [], [], c_parent)
    mutated, _ = _world(tmp_path / "b", docs, extra, [], c_parent)
    assert _observe(base, c_parent, paths) == _observe(mutated, c_parent, paths)
    assert _observe(base, c_wide, paths) != _observe(mutated, c_wide, paths)
