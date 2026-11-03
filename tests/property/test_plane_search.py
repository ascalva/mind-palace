"""The plane's search loop against the exact ranking (`docs/LAWS.md` §VI, PLN-3).

`PlaneReader.search` asks the atom table for the nearest candidates the `held` cache marks, keeps
those a cleared relation holds, and widens the window until it has `k` or the table runs out. The
law (`formal/Palace/Plane.lean::search_eq`): the result is the first `k` atoms, by distance and then
atom id, among those the cache prefilters and a cleared relation holds. Hypothesis draws documents
in every plane class, a clearance, `k`, a query, whether superseded rows count, and a cache that
may be coherent, may claim every class for every atom, or may be wrong per atom in either
direction; the ranking is computed here independently and compared.

The control shows the widening is load-bearing: one round of candidates under a cache that marks
everything returns an uncleared atom, where the loop goes on to find the cleared one.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from core.kernel import clearance as cl
from core.kernel.provenance import Provenance
from core.stores.plane import PLANE_CLASSES, SharedPlane
from tests.fixtures.fakes import HashingEmbedder
from tests.fixtures.plane_fakes import MemoryAtoms, cosine_distance

EMB = HashingEmbedder(16)
VOCAB = ["the owner's plan", "a shared sentence", "lean proofs", "vector atoms", "zipf law",
         "heartbeat tick", "papers about graphs", "model reply"]
CLASS_NAMES = [p.value for p in PLANE_CLASSES]

texts = st.lists(st.sampled_from(VOCAB), min_size=1, max_size=4)
document = st.tuples(st.sampled_from(PLANE_CLASSES), st.lists(texts, min_size=1, max_size=3))
caches = st.one_of(st.just("coherent"), st.just("everything"),
                   st.lists(st.tuples(st.sets(st.sampled_from(CLASS_NAMES)),
                                      st.sets(st.sampled_from(CLASS_NAMES))),
                            min_size=64, max_size=64))


def _land(p: SharedPlane, path: str, cls: Provenance, versions: list[list[str]]) -> None:
    for v, chunk_texts in enumerate(versions):
        p.land([{"source_path": path, "digest": f"{path}@{v}:{'|'.join(chunk_texts)}",
                 "provenance": cls.value, "title": path, "chunk_index": i, "text": t,
                 "vector": EMB.embed_query(t)} for i, t in enumerate(chunk_texts)])


def _corrupt(atoms: MemoryAtoms, cache: str | list[tuple[set[str], set[str]]]) -> None:
    """Leave the cache coherent, mark every class on every atom, or overwrite each atom's `held`
    and `held_ever` with drawn sets, so it may both claim and miss classes."""
    if cache == "coherent":
        return
    ids = sorted(atoms.ids())
    if cache == "everything":
        every = frozenset(CLASS_NAMES)
        atoms.set_held({a: (every, every) for a in ids})
    else:
        atoms.set_held({a: (frozenset(h), frozenset(e)) for a, (h, e) in zip(ids, cache,
                                                                             strict=False)})


def _exact(p: SharedPlane, atoms: MemoryAtoms, c: cl.Clearance[Provenance], q: list[float], k: int,
           superseded: bool) -> list[str]:
    """The first `k` atoms, by distance then id, that the cache prefilters for `c`'s classes and a
    cleared relation holds."""
    col = "held_ever" if superseded else "held"
    wanted = {cls.value for cls in c.classes}
    cleared = {o.atom_id for o in p.reader(c).occupancies(include_superseded=superseded)}
    pool = [a for a in cleared if a in atoms.rows and atoms.rows[a][col] & wanted]
    return sorted(pool, key=lambda a: (cosine_distance(q, atoms.rows[a]["vector"]), a))[:k]


@settings(max_examples=200, deadline=None,
          suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow])
@given(docs=st.lists(document, min_size=1, max_size=6),
       cleared=st.sets(st.sampled_from(PLANE_CLASSES), min_size=1),
       retire=st.lists(st.integers(min_value=0, max_value=5), max_size=2),
       k=st.integers(min_value=1, max_value=8),
       query=st.sampled_from([*VOCAB, "something else entirely"]),
       superseded=st.booleans(), cache=caches)
def test_search_returns_the_first_k_of_the_exact_cleared_ranking(docs, cleared, retire, k, query,
                                                                 superseded, cache):
    """PLN-3: the search loop returns the first `k` atoms of the exact ranking among those the
    cache prefilters and a cleared relation holds, ties by atom id, and its widening rounds
    suffice, whatever the cache holds."""
    c = cl._mint(cleared, "property")
    with tempfile.TemporaryDirectory() as d:
        atoms = MemoryAtoms()
        p = SharedPlane(Path(d), atoms)
        for i, (cls, versions) in enumerate(docs):
            _land(p, f"doc/{i}", cls, versions)
        for i in retire:
            if i < len(docs):
                p.retire(f"doc/{i}")
        _corrupt(atoms, cache)
        q = EMB.embed_query(query)
        hits = p.reader(c).search(q, k=k, include_superseded=superseded)
        assert [h.atom_id for h in hits] == _exact(p, atoms, c, q, k, superseded)


def test_one_round_of_candidates_is_not_enough(tmp_path: Path) -> None:
    """Control: under a cache that marks every class on every atom, the nearest candidate is an
    observed reply the mirror is not cleared for. One round of `k = 1` candidates finds nothing
    cleared; the loop widens and returns the authored note, the exact answer."""
    atoms = MemoryAtoms()
    p = SharedPlane(tmp_path, atoms)
    _land(p, "notes/n", Provenance.AUTHORED_SOLO, [["papers about graphs"]])
    _land(p, "dialogue/t", Provenance.OBSERVED, [["model reply"]])
    _corrupt(atoms, "everything")
    q = EMB.embed_query("model reply")
    mirror = cl.MIRROR_READ
    first_round = atoms.nearest(q, classes=[c.value for c in mirror.classes], superseded=False,
                                limit=1)
    cleared = {o.atom_id for o in p.reader(mirror).occupancies()}
    assert [x.atom_id for x in first_round if x.atom_id in cleared] == []
    hits = p.reader(mirror).search(q, k=1)
    assert [h.atom_id for h in hits] == _exact(p, atoms, mirror, q, 1, False) != []
    assert hits[0].occupancies[0].source_path == "notes/n"


def test_the_ranking_check_rejects_a_search_that_skips_the_widening(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Control: the same comparison fails on a reader whose atom table answers only the first
    round, as a search that never widened would."""
    atoms = MemoryAtoms()
    p = SharedPlane(tmp_path, atoms)
    _land(p, "notes/n", Provenance.AUTHORED_SOLO, [["papers about graphs"]])
    _land(p, "dialogue/t", Provenance.OBSERVED, [["model reply"]])
    _corrupt(atoms, "everything")
    q = EMB.embed_query("model reply")
    exact = _exact(p, atoms, cl.MIRROR_READ, q, 1, False)
    nearest = atoms.nearest
    monkeypatch.setattr(atoms, "nearest", lambda v, *, classes, superseded, limit:
                        nearest(v, classes=classes, superseded=superseded, limit=1))
    assert [h.atom_id for h in p.reader(cl.MIRROR_READ).search(q, k=1)] != exact
