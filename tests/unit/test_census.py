"""Item 4 — the census reader: exact, witnessed, deterministic combinatorial invariants over the
composed assembly's arrow layer at one certified cut (bp-080; dn-synchronic-diachronic-dreamer).

Planted fixtures — a directed 3-cycle, an unbalanced diamond, a retro-citation — each enumerate
with their exact witness; an arrowless control returns empty; two runs at one cut are bit-identical;
every reading records its anchored cut. The census's whole claim is EXACTNESS (§2.3), so every
assertion below pins a witness, never just a count.
"""

from __future__ import annotations

from core.graph.census import (
    INFLUENCE_LOOP,
    REACH_BACK,
    REVISION_ASYMMETRY,
    Arc,
    CensusReading,
    FirstAuthorship,
    census,
    influence_loops,
    reach_backs,
    revision_asymmetries,
)
from core.temporal.spine import Certificate, CertifiedCut


def _cut() -> CertifiedCut:
    """A minimal certified cut fixture (the anchor every reading records). Its internals are not
    under test here — bp-055 certifies cuts; this pins that a reading CARRIES one."""
    return CertifiedCut(
        frontier=(("versions:noteA", 3), ("edges", 7)),
        certificates=frozenset({Certificate.COMMIT}),
        evidence=("deadbeef",),
    )


# --- influence loops: directed cycles ------------------------------------------------------------

def test_directed_three_cycle_enumerated_with_exact_witness():
    arcs = [Arc("a", "b", "e1"), Arc("b", "c", "e2"), Arc("c", "a", "e3")]
    claims = influence_loops(arcs)
    assert len(claims) == 1
    (loop,) = claims
    assert loop.kind == INFLUENCE_LOOP
    assert loop.members == ("a", "b", "c")          # canonicalized to start at the min node
    assert loop.witness == ("e1", "e2", "e3")       # the exact ordered arc set that closes it
    assert loop.detail["length"] == 3


def test_two_cycle_is_a_loop():
    # A mutual citation A cites B, B cites A is a closed loop (length 2) — the smallest one.
    claims = influence_loops([Arc("a", "b", "x"), Arc("b", "a", "y")])
    assert len(claims) == 1
    assert claims[0].members == ("a", "b")
    assert claims[0].witness == ("x", "y")


def test_acyclic_citation_chain_has_no_loop():
    assert influence_loops([Arc("a", "b", "e1"), Arc("b", "c", "e2")]) == []


# --- revision-effort asymmetry: unbalanced diamonds ----------------------------------------------

def test_unbalanced_diamond_enumerated_with_branch_lengths():
    # S → T directly (one revision) and S → m1 → m2 → T (three) — the sibling asymmetry.
    arcs = [
        Arc("S", "T", "d0", kind="supersession"),
        Arc("S", "m1", "d1", kind="supersession"),
        Arc("m1", "m2", "d2", kind="supersession"),
        Arc("m2", "T", "d3", kind="supersession"),
    ]
    claims = revision_asymmetries(arcs)
    assert len(claims) == 1
    (dia,) = claims
    assert dia.kind == REVISION_ASYMMETRY
    assert dia.detail["source"] == "S" and dia.detail["sink"] == "T"
    assert dia.detail["short_revisions"] == 1       # the sibling that took one revision
    assert dia.detail["long_revisions"] == 3        # the branch that took three
    assert dia.detail["short_path"] == ["S", "T"]
    assert dia.detail["long_path"] == ["S", "m1", "m2", "T"]
    assert dia.members == ("S", "T", "m1", "m2")
    assert dia.witness == ("d0", "d1", "d2", "d3")  # both branches' arcs, short then long


def test_balanced_diamond_is_not_an_asymmetry():
    # Two equal-length branches S→a→T and S→b→T — a diamond, but BALANCED: no asymmetry to narrate.
    arcs = [
        Arc("S", "a", "p1"), Arc("a", "T", "p2"),
        Arc("S", "b", "q1"), Arc("b", "T", "q2"),
    ]
    assert revision_asymmetries(arcs) == []


# --- reach-backs: a citation to something younger than the citer ---------------------------------

def test_reach_back_when_cited_is_younger_than_citer():
    # A (first authored early, rank 0) re-cites B (first authored later, rank 5) — a revision-
    # mediated backflow: A could only cite B in a revision, after B came to exist.
    arcs = [Arc("A", "B", "cite1")]
    authorship = {
        "A": FirstAuthorship("A", rank=0, evidence=("A:v1",)),
        "B": FirstAuthorship("B", rank=5, evidence=("B:v1",)),
    }
    claims = reach_backs(arcs, authorship)
    assert len(claims) == 1
    (rb,) = claims
    assert rb.kind == REACH_BACK
    assert rb.members == ("A", "B")
    assert rb.witness == ("cite1", "A:v1", "B:v1")  # the arc + both first-authorship evidences
    assert rb.detail == {"citer": "A", "cited": "B", "citer_rank": 0, "cited_rank": 5}


def test_forward_citation_to_older_note_is_not_a_reach_back():
    # A (rank 5) cites B (rank 0) — B predates A: the ordinary forward citation, no backflow.
    arcs = [Arc("A", "B", "cite1")]
    authorship = {
        "A": FirstAuthorship("A", rank=5, evidence=("A:v1",)),
        "B": FirstAuthorship("B", rank=0, evidence=("B:v1",)),
    }
    assert reach_backs(arcs, authorship) == []


def test_reach_back_needs_both_endpoints_witnessed():
    # A missing first-authorship record for either endpoint yields no claim (the honest seam):
    # the census cannot witness what it was not given.
    arcs = [Arc("A", "B", "cite1")]
    only_a = {"A": FirstAuthorship("A", rank=0, evidence=("A:v1",))}
    assert reach_backs(arcs, only_a) == []


def test_supersession_arc_is_never_a_reach_back():
    # Only citation arcs are re-citations; a supersession pointing at a younger node is not one.
    arcs = [Arc("A", "B", "s1", kind="supersession")]
    authorship = {
        "A": FirstAuthorship("A", rank=0, evidence=("A:v1",)),
        "B": FirstAuthorship("B", rank=5, evidence=("B:v1",)),
    }
    assert reach_backs(arcs, authorship) == []


# --- the reader: anchored, deterministic, silent-when-empty --------------------------------------

def test_census_records_the_anchored_cut():
    cut = _cut()
    reading = census([Arc("a", "b", "e1"), Arc("b", "a", "e2")], {}, cut)
    assert isinstance(reading, CensusReading)
    assert reading.cut is cut                        # the cut is recorded in every reading (Item 4)
    assert reading.claims                            # and the loop surfaced


def test_arrowless_control_returns_zero_claims():
    # No cycle, no unbalanced diamond, only forward citations to older notes — the arrowless control
    # (§2.9 falsifier): the census surfaces NOTHING (silence, never filler).
    arcs = [Arc("X", "Y", "c1"), Arc("Y", "Z", "c2")]
    authorship = {
        "X": FirstAuthorship("X", rank=2, evidence=("X:v1",)),
        "Y": FirstAuthorship("Y", rank=1, evidence=("Y:v1",)),
        "Z": FirstAuthorship("Z", rank=0, evidence=("Z:v1",)),
    }
    reading = census(arcs, authorship, _cut())
    assert reading.claims == ()


def test_empty_census_is_silent():
    reading = census([], {}, _cut())
    assert reading.claims == ()


def test_reading_is_deterministic_across_runs():
    cut = _cut()
    arcs = [
        Arc("a", "b", "e1"), Arc("b", "c", "e2"), Arc("c", "a", "e3"),
        Arc("S", "T", "d0", kind="supersession"),
        Arc("S", "m1", "d1", kind="supersession"),
        Arc("m1", "m2", "d2", kind="supersession"),
        Arc("m2", "T", "d3", kind="supersession"),
        Arc("A", "B", "cite1"),
    ]
    authorship = {
        "A": FirstAuthorship("A", rank=0, evidence=("A:v1",)),
        "B": FirstAuthorship("B", rank=5, evidence=("B:v1",)),
    }
    r1 = census(arcs, authorship, cut)
    r2 = census(list(reversed(arcs)), authorship, cut)   # input order must not matter
    assert r1 == r2
    kinds = {c.kind for c in r1.claims}
    assert kinds == {INFLUENCE_LOOP, REVISION_ASYMMETRY, REACH_BACK}   # all three families fired
