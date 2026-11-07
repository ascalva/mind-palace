"""The universe builder's batched reads of the citation graph build the same support and the
same F edges as the per-node reads they replaced (`references_from` / `references_to`, kept here
verbatim as the oracle), over random graphs, radii and supports."""

from __future__ import annotations

from collections import deque
from pathlib import Path
from typing import Any, cast

from hypothesis import given, settings
from hypothesis import strategies as st

from core.reference_view import ReferenceView
from core.sentence.ast import Rel
from core.sentence.precedents import Precedents
from core.sentence.universe import _Builder, _Node, is_repo_path
from core.stores.reference_edges import ReferenceEdge, ReferenceEdgeStore

REFS = [f"core/m{i}.py" for i in range(8)] + [f"docs/d{i}.md" for i in range(8)]
NOTES = [f"notes/n{i}.md" for i in range(4)]
ALL = REFS + NOTES
SHA = "c" * 40


def _store(edges: set[tuple[str, str]]) -> ReferenceEdgeStore:
    store = ReferenceEdgeStore(Path(":memory:"))
    store.add_batch(
        ReferenceEdge.mint(source_kind="corpus", source_ref=a, source_detail="",
                           target_kind="corpus", target_ref=b, target_detail="",
                           ref_type="path-mention", commit_sha=SHA, source_line=1 + i)
        for i, (a, b) in enumerate(sorted(edges)))
    return store


def _builder(store: ReferenceEdgeStore, support: int) -> _Builder:
    b = _Builder(cast(Any, None), Precedents(support=support), None)
    b.view = ReferenceView.over(store, commit=SHA)
    b.moves = frozenset({Rel.F})
    return b


def _oracle_seed(b: _Builder, atom: str, radius: int) -> tuple[set[str], bool]:
    """seed_typed's F half as it was: one `references_from` and one `references_to` per node."""
    def cited(n: str) -> set[str]:
        return ({e.target_ref for e in b.view.references_from(n)}
                | {e.source_ref for e in b.view.references_to(n)})
    seen, frontier, budget, cut = {atom}, deque([(atom, 0)]), b.p.support, False
    while frontier:
        node, d = frontier.popleft()
        if d >= radius:
            continue
        for nb in sorted(cited(node)):
            if nb not in seen:
                if len(seen) >= budget:
                    cut = True
                    break
                seen.add(nb)
                frontier.append((nb, d + 1))
    return seen, cut


def _oracle_wire(b: _Builder) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for ref in [n.ref for n in b.nodes.values() if n.stratum == "reference"]:
        for e in b.view.references_from(ref):
            if e.target_ref in b.nodes and e.target_ref != ref:
                out.setdefault(ref, set()).add(e.target_ref)
        for e in b.view.references_to(ref):
            if e.source_ref in b.nodes and e.source_ref != ref:
                out.setdefault(e.source_ref, set()).add(ref)
    for n in b.nodes.values():
        if n.stratum in ("mirror", "dialogue"):
            for e in b.view.references_from(n.ref):
                if e.target_ref in b.nodes:
                    out.setdefault(n.ref, set()).add(e.target_ref)
    return out


@given(edges=st.sets(st.tuples(st.sampled_from(ALL), st.sampled_from(ALL)), max_size=60),
       atom=st.sampled_from(ALL), radius=st.integers(1, 4), support=st.integers(2, 25),
       notes=st.sets(st.sampled_from(NOTES), max_size=3))
@settings(max_examples=200, deadline=None)
def test_batched_bfs_and_wiring_equal_the_per_node_reads(
        edges: set[tuple[str, str]], atom: str, radius: int, support: int, notes: set[str]) -> None:
    store = _store(edges)
    b = _builder(store, support)
    for n in sorted(notes):
        b.add(_Node(n, "mirror", n, "", "authored-solo", None, {}))
    assert all(is_repo_path(x) for x in ALL)
    b.seed_typed(atom, radius, frozenset({Rel.F}))
    want_seen, want_cut = _oracle_seed(b, atom, radius)
    assert set(b.nodes) == want_seen | notes
    assert any("cut at the support" in x for x in b.notes) == want_cut
    b.wire_reference()
    assert b.f_edges == _oracle_wire(b)
