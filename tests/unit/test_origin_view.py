"""`origin(e)` — the derived provenance-spine view (bp-088 Item 17; dn-agentic-loop §2.4b EX-2).

`origin` answers "which dialogue action minted this durable edge?" as a regenerable two-hop join
`C ∘ commit-keying` over two BUILT stores — no new store, no minted rows. These tests pin:

  1. the join is correct — `origin(ref_edge)` is the causal edge whose `pair_cut_sha` equals the
     reference edge's `commit_sha`;
  2. **F-AL7** — the result is re-derivable from witnesses + commit keys ALONE (reproduced here from
     the raw store rows, so no fact beyond what the rows carry is needed);
  3. it mints nothing — both store counts are unchanged across a call;
  4. the honest empties — an unknown id, an id carrying no commit key, and a commit no causal edge
     witnessed all return `None` (not an error);
  5. the recorded target-kind boundary — `origin` is scoped to reference-edge (X_cite) ids; a
     working-tree C-edge (`pair_cut_sha=''`) carries no commit key to join on.

Real in-memory stores are the fixture (`:memory:`), so the regenerability proof runs against the
actual row shapes — the strongest form of the F-AL7 check.
"""

from __future__ import annotations

import pytest

from core.origin_view import origin
from core.stores.causal_edges import CausalEdge, CausalEdgeStore
from core.stores.reference_edges import ReferenceEdge, ReferenceEdgeStore

_FULL_SHA = "a1b2c3d4e5f60718293a4b5c6d7e8f9012345678"      # the commit that minted the edge
_OTHER_SHA = "ffeeddccbbaa00112233445566778899aabbccdd"     # a commit no causal edge witnessed


@pytest.fixture
def causal_edges() -> CausalEdgeStore:
    """One session's C-edges: a commit-species edge (pair_cut_sha = the full sha) that witnesses the
    minting commit, plus a working-tree file edge (pair_cut_sha='') that must NEVER match a key."""
    store = CausalEdgeStore(path=":memory:")  # type: ignore[arg-type]
    commit_edge = CausalEdge.mint(
        session_id="s-1", event_order=7, kind="C", dst_type="commit", dst="a1b2c3d",
        witness_digest="dig-1", witness_turn=42, pair_cut_sha=_FULL_SHA,
    )
    file_edge = CausalEdge.mint(
        session_id="s-1", event_order=8, kind="C", dst_type="file", dst="core/foo.py",
        witness_digest="dig-1", witness_turn=43, pair_cut_sha="",   # no commit anchor
    )
    store.replace_session("s-1", [commit_edge, file_edge], transcript_digest="dig-1")
    return store


@pytest.fixture
def reference_edges() -> ReferenceEdgeStore:
    """Two reference edges: one minted at the witnessed commit (`_FULL_SHA`) — origin resolves it —
    and one minted at a commit no causal edge witnessed (`_OTHER_SHA`) — origin returns None."""
    store = ReferenceEdgeStore(path=":memory:")  # type: ignore[arg-type]
    at_witnessed = ReferenceEdge.mint(
        source_kind="corpus", source_ref="docs/design-notes/a.md",
        target_kind="corpus", target_ref="docs/design-notes/b.md",
        ref_type="design-ref", commit_sha=_FULL_SHA, source_line=3,
    )
    at_unwitnessed = ReferenceEdge.mint(
        source_kind="code", source_ref="core/x.py",
        target_kind="corpus", target_ref="docs/design-notes/a.md",
        ref_type="note-citation", commit_sha=_OTHER_SHA, source_line=5,
    )
    store.add_batch([at_witnessed, at_unwitnessed])
    return store


def _ref_by_commit(store: ReferenceEdgeStore, commit_sha: str) -> ReferenceEdge:
    return next(r for r in store.all() if r.commit_sha == commit_sha)


def test_origin_resolves_the_minting_causal_edge(causal_edges, reference_edges):
    """The join is correct: origin(ref@commit) is the causal edge whose witnessed commit
    (`pair_cut_sha`) IS that commit — the dialogue action that produced it."""
    ref = _ref_by_commit(reference_edges, _FULL_SHA)
    result = origin(ref.edge_id, causal_edges=causal_edges, reference_edges=reference_edges)
    assert result is not None
    assert result.dst_type == "commit"
    assert result.pair_cut_sha == _FULL_SHA
    assert result.session_id == "s-1" and result.event_order == 7
    assert (result.witness_digest, result.witness_turn) == ("dig-1", 42)


def test_F_AL7_result_is_regenerable_from_witnesses_and_commit_keys_alone(
    causal_edges, reference_edges
):
    """F-AL7, the crux. The SAME result is reproduced from ONLY (a) the reference edge's commit key
    and (b) the causal edges' witnessed commit + witness fields — the raw rows, nothing else. No
    fact the rows do not carry is needed, so the view needs no store (EX-2 holds)."""
    ref = _ref_by_commit(reference_edges, _FULL_SHA)
    result = origin(ref.edge_id, causal_edges=causal_edges, reference_edges=reference_edges)

    # Re-derive by hand from the raw readers — commit-keying (F-side) then the witness (C-side):
    commit_key = next(r.commit_sha for r in reference_edges.all() if r.edge_id == ref.edge_id)
    expected = next(
        CausalEdge(**row) for row in causal_edges.all_edges()
        if row["pair_cut_sha"] == commit_key
    )
    assert result == expected            # byte-identical to the hand join ⇒ no hidden fact needed


def test_origin_mints_nothing(causal_edges, reference_edges):
    """No store, no minted rows: both store counts are unchanged across a call."""
    ref = _ref_by_commit(reference_edges, _FULL_SHA)
    ce_before, re_before = causal_edges.count(), reference_edges.count()
    origin(ref.edge_id, causal_edges=causal_edges, reference_edges=reference_edges)
    assert (causal_edges.count(), reference_edges.count()) == (ce_before, re_before)


def test_origin_is_none_for_an_unwitnessed_commit(causal_edges, reference_edges):
    """A reference edge minted at a commit no causal edge witnessed ⇒ None (an honest empty answer —
    e.g. a pre-integration commit — NOT a falsifier; the join is still fully derivable)."""
    ref = _ref_by_commit(reference_edges, _OTHER_SHA)
    assert origin(ref.edge_id, causal_edges=causal_edges, reference_edges=reference_edges) is None


def test_origin_is_none_for_an_unknown_edge_id(causal_edges, reference_edges):
    """An id that is not a known reference edge carries no commit key ⇒ None. This also records the
    target-kind boundary (§3 Q3): origin is scoped to reference-edge (X_cite) ids — a causal edge's
    own id (a working-tree file/doc endpoint, pair_cut_sha='') is out of domain."""
    assert origin("not-an-edge", causal_edges=causal_edges, reference_edges=reference_edges) is None
    # a causal file-edge's id is likewise not a reference edge ⇒ out of origin's domain
    file_edge_row = next(r for r in causal_edges.all_edges() if r["dst_type"] == "file")
    assert origin(file_edge_row["edge_id"],
                  causal_edges=causal_edges, reference_edges=reference_edges) is None


def test_working_tree_causal_edge_never_matches_a_commit_key(causal_edges, reference_edges):
    """The `pair_cut_sha=''` file edge is present in the store but can never be an origin result — a
    non-empty commit key never equals '' (the boundary is structural, not incidental)."""
    ref = _ref_by_commit(reference_edges, _FULL_SHA)
    result = origin(ref.edge_id, causal_edges=causal_edges, reference_edges=reference_edges)
    assert result is not None and result.pair_cut_sha != ""    # the commit edge, never the file one
