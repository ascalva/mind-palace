"""Items 5 & 6 — the census lens on the panel, and the F-SD9 battery (bp-080;
dn-synchronic-diachronic-dreamer §2.9 ADOPTED, F-SD9).

The lens renders each census claim arrow-literally, in the §2.9 vocabulary (records-not-causes,
witness inline, gauge-immune), behind the R&D flag. Item 6's battery is the ruling's falsifier made
permanent: each planted structure surfaces with its correct witness; the arrowless control emits
ZERO census claims; and a grep of the rendered vocabulary finds NO causal phrasing ("influenced" /
"shaped" / "led to") and NO flux/spectral term.
"""

from __future__ import annotations

import dataclasses

import pytest

from config.loader import load_config
from core.dreaming.interpreters import (
    CENSUS_ASYMMETRY,
    CENSUS_LOOP,
    CENSUS_REACH_BACK,
    census_lens,
    run_census_lens,
)
from core.dreaming.rnd import DreamRnDDisabledError
from core.graph.census import Arc, CensusReading, FirstAuthorship, census
from core.temporal.spine import Certificate, CertifiedCut

# F-SD9's forbidden vocabulary. The banned CAUSAL verbs are exact (§2.9-b endorses the NOUN
# "influence loop" verbatim, so "influence" is allowed — only the causal verb "influenced" is not);
# the flux/spectral terms are substrings (none may leak — the census is combinatorial, ML §2.7b).
CAUSAL_WORDS = ("influenced", "shaped", "led to", "caused", "because", "drove", "made you")
FLUX_SPECTRAL = ("flux", "spectral", "eigen", "gauge", "phase", "curl", "vorticity")


def _cut() -> CertifiedCut:
    return CertifiedCut(
        frontier=(("versions:noteA", 3),),
        certificates=frozenset({Certificate.COMMIT}),
        evidence=("deadbeef",),
    )


def _on_config():
    cfg = load_config()
    return dataclasses.replace(cfg, dream_rnd=dataclasses.replace(cfg.dream_rnd, enabled=True))


# Planted fixtures — the F9-style structures (note §2.9 falsifier) --------------------------------

def _loop_reading() -> CensusReading:
    """A directed 3-cycle: r0 cites r1 cites r2 cites r0."""
    arcs = [Arc("r0", "r1", "e1"), Arc("r1", "r2", "e2"), Arc("r2", "r0", "e3")]
    return census(arcs, {}, _cut())


def _asymmetry_reading() -> CensusReading:
    """An unbalanced diamond: S→T (one revision) vs S→m1→m2→T (three)."""
    arcs = [
        Arc("S", "T", "d0", kind="supersession"),
        Arc("S", "m1", "d1", kind="supersession"),
        Arc("m1", "m2", "d2", kind="supersession"),
        Arc("m2", "T", "d3", kind="supersession"),
    ]
    return census(arcs, {}, _cut())


def _reach_back_reading() -> CensusReading:
    """A retro-citation: A (rank 0) re-cites B (rank 5), younger than A's first authorship."""
    arcs = [Arc("A", "B", "cite1")]
    authorship = {
        "A": FirstAuthorship("A", rank=0, evidence=("A:v1",)),
        "B": FirstAuthorship("B", rank=5, evidence=("B:v1",)),
    }
    return census(arcs, authorship, _cut())


def _control_reading() -> CensusReading:
    """The arrowless control: forward citations to older notes, no cycle, no diamond — empty."""
    arcs = [Arc("X", "Y", "c1"), Arc("Y", "Z", "c2")]
    authorship = {
        "X": FirstAuthorship("X", rank=2), "Y": FirstAuthorship("Y", rank=1),
        "Z": FirstAuthorship("Z", rank=0),
    }
    return census(arcs, authorship, _cut())


# --- Item 5: the lens renders arrow-literally, witness inline, behind the flag --------------------

def test_lens_refuses_when_flag_off():
    # Behind require_rnd_enabled like every panel entry — the arrow narration cannot run in a
    # normal session (it lands BEHIND the flag; bp-080 changes no R&D wiring).
    with pytest.raises(DreamRnDDisabledError):
        run_census_lens(_loop_reading(), config=load_config())


def test_loop_claim_rendered_arrow_literally_with_witness_inline():
    claims = run_census_lens(_loop_reading(), config=_on_config())
    assert len(claims) == 1
    (c,) = claims
    assert c.method == CENSUS_LOOP
    assert c.statement == (
        "r0 cites r1 cites r2 cites r0 — a closed influence loop (witness: e1, e2, e3)"
    )
    assert set(c.support) == {"r0", "r1", "r2"}          # authored members → grounding support
    assert c.data["witness"] == ["e1", "e2", "e3"]       # the exact witness rides in data too
    assert c.data["cut"] == ["deadbeef"]                 # the anchored cut is carried


def test_asymmetry_claim_rendered_as_revision_effort_record():
    claims = run_census_lens(_asymmetry_reading(), config=_on_config())
    assert len(claims) == 1
    (c,) = claims
    assert c.method == CENSUS_ASYMMETRY
    assert c.statement == (
        "this branch took 3 revisions where its sibling took 1 — a revision-effort asymmetry "
        "(witness: d0, d1, d2, d3)"
    )
    assert set(c.support) == {"S", "T", "m1", "m2"}


def test_reach_back_claim_rendered_as_backflow_record():
    claims = run_census_lens(_reach_back_reading(), config=_on_config())
    assert len(claims) == 1
    (c,) = claims
    assert c.method == CENSUS_REACH_BACK
    assert c.statement == (
        "A re-cites B, younger than its own first authorship — a revision-mediated backflow "
        "(witness: cite1, A:v1, B:v1)"
    )
    assert set(c.support) == {"A", "B"}


def test_lens_is_deterministic():
    r = _loop_reading()
    assert census_lens(r, _on_config().dream_rnd) == census_lens(r, _on_config().dream_rnd)


# --- Item 6: the F-SD9 battery — planted structures witnessed, control silent, no causal words ----

def test_battery_each_planted_structure_surfaces_with_its_witness():
    cfg = _on_config()
    loop = run_census_lens(_loop_reading(), config=cfg)
    asym = run_census_lens(_asymmetry_reading(), config=cfg)
    reach = run_census_lens(_reach_back_reading(), config=cfg)
    assert [c.method for c in loop] == [CENSUS_LOOP]
    assert [c.method for c in asym] == [CENSUS_ASYMMETRY]
    assert [c.method for c in reach] == [CENSUS_REACH_BACK]
    # each carries a non-empty, exact witness (the census's whole claim is exactness)
    for claims in (loop, asym, reach):
        assert claims[0].data["witness"]
        assert "witness:" in claims[0].statement


def test_battery_arrowless_control_emits_zero_census_claims():
    # F-SD9's control clause: no planted directed structure ⇒ silence, never filler (§2.9-d).
    assert run_census_lens(_control_reading(), config=_on_config()) == []


def test_battery_no_causal_or_flux_vocabulary_in_any_rendered_claim():
    # F-SD9's language clause: census narration is records-not-causes — no "influenced"/"shaped"/
    # "led to", and no flux/spectral term (there is none to leak — the census is combinatorial).
    cfg = _on_config()
    statements = [
        c.statement
        for reading in (_loop_reading(), _asymmetry_reading(), _reach_back_reading())
        for c in run_census_lens(reading, config=cfg)
    ]
    assert statements
    blob = " ".join(statements).lower()
    for banned in CAUSAL_WORDS:
        assert banned not in blob, f"causal phrasing leaked into a census claim: {banned!r}"
    for banned in FLUX_SPECTRAL:
        assert banned not in blob, f"flux/spectral phrasing leaked into a census claim: {banned!r}"


def test_battery_combined_reading_fires_all_three_families_once_each():
    arcs = [
        Arc("r0", "r1", "e1"), Arc("r1", "r2", "e2"), Arc("r2", "r0", "e3"),
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
    reading = census(arcs, authorship, _cut())
    claims = run_census_lens(reading, config=_on_config())
    assert {c.method for c in claims} == {CENSUS_LOOP, CENSUS_ASYMMETRY, CENSUS_REACH_BACK}
    assert len(claims) == 3
