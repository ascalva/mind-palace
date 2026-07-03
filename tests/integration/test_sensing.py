"""Core side of the sensing handoff (Track G item G3, β = 0).

The sealed core writes de-identified sense requests and reads observations on disk only — no
socket, no import of the edge effector. These pin the outbound firewall (a request cannot carry
note content or a URL; a non-sensing effect cannot even be emitted here) and the inbound tier
(a sensed observation is `observed`-tier by construction — see test_sensing_firewall.py for the
proof it cannot reach the authored mirror).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.provenance import Provenance
from core.research.criteria import DeidentificationError
from core.sensing import (
    ObservedView,
    SensedObservation,
    SenseRequest,
    SensingHandoff,
    sense_request,
)
from ops.effects import (
    ApprovalRef,
    ApprovalStrength,
    CeilingExceededError,
    Effect,
    ReversibilityClass,
    ScopedCapability,
)

_SENSE_CAP = ScopedCapability(scope="sense:fetch")


def _sensing_effect(actuator: str = "sense_fetch") -> Effect:
    return Effect(
        actuator=actuator,
        capability=_SENSE_CAP,
        reversibility=ReversibilityClass.SENSING,
        proposal_att="att-1",
    )


# --- outbound: the request is de-identified and address-free ---------------------------------
def test_emit_writes_only_de_identified_fields(tmp_path: Path):
    handoff = SensingHandoff(handoff=tmp_path)
    req = sense_request("sense_fetch", "open-meteo", ["rain probability"])
    rid = handoff.emit(req, _sensing_effect())

    written = json.loads((tmp_path / "requests" / f"{rid}.json").read_text())
    assert set(written) == {"id", "actuator", "upstream", "terms", "ts"}
    assert written["upstream"] == "open-meteo"     # a NAME, not a URL
    assert written["terms"] == ["rain probability"]


def test_request_cannot_carry_a_url_as_upstream(tmp_path: Path):
    # The confused-deputy answer, structural: `upstream` must be a short allowlist NAME. A URL,
    # host, or path does not match the shape, so a steered reasoner cannot aim the hand.
    for bad in ("https://evil.example", "evil.example/x", "10.0.0.1", "a/b"):
        with pytest.raises(DeidentificationError):
            sense_request("sense_fetch", bad, [])


def test_emit_re_scrubs_terms_at_the_boundary(tmp_path: Path):
    handoff = SensingHandoff(handoff=tmp_path)
    # A hand-built request with a dirty term is refused at emit (defense in depth) — nothing
    # leaks to the requests dir.
    dirty = SenseRequest(
        actuator="sense_fetch", upstream="open-meteo", terms=("call me at a@b.com",)
    )
    with pytest.raises(DeidentificationError):
        handoff.emit(dirty, _sensing_effect())
    assert not list((tmp_path / "requests").glob("*.json"))


def test_sense_request_drops_unsafe_terms_but_refuses_a_total_wipe():
    # Conservative builder: a mix keeps the clean term…
    req = sense_request("sense_fetch", "pubmed", ["migraine", "reach a@b.com"])
    assert req.terms == ("migraine",)
    # …but if terms were proposed and none survive, that is a refusal, not a silent unqueried fetch.
    with pytest.raises(DeidentificationError):
        sense_request("sense_fetch", "pubmed", ["a@b.com", "http://x"])


def test_empty_term_list_is_legal():
    # Many sensors take no query (weather, a status endpoint) — an empty list is fine.
    req = sense_request("sense_fetch", "open-meteo", [])
    assert req.terms == ()


# --- the §4 filtration enforced at the handoff -----------------------------------------------
def test_emit_refuses_a_non_sensing_effect(tmp_path: Path):
    # Admission is EffectView.admit(ceiling=SENSING): an acting-class effect raises before
    # anything reaches the handoff. This is where the β=0 ceiling bites in the live path.
    handoff = SensingHandoff(handoff=tmp_path)
    req = sense_request("sense_fetch", "open-meteo", [])
    acting = Effect(
        actuator="sense_fetch",
        capability=_SENSE_CAP,
        reversibility=ReversibilityClass.REVERSIBLE,
        proposal_att="att",
        approval_ref=ApprovalRef(approver="owner", strength=ApprovalStrength.LIGHT),
    )
    with pytest.raises(CeilingExceededError):
        handoff.emit(req, acting)
    assert not list((tmp_path / "requests").glob("*.json"))


def test_emit_refuses_effect_actuator_mismatch(tmp_path: Path):
    # One effect authorizes one request — the actuators must agree.
    handoff = SensingHandoff(handoff=tmp_path)
    req = sense_request("sense_fetch", "open-meteo", [])
    with pytest.raises(ValueError, match="does not match"):
        handoff.emit(req, _sensing_effect(actuator="other_hand"))


# --- inbound: observations round-trip and are observed-tier ----------------------------------
def test_collect_round_trips_observations(tmp_path: Path):
    handoff = SensingHandoff(handoff=tmp_path)
    (tmp_path / "observations" / "r1.json").write_text(json.dumps({
        "request_id": "r1", "upstream": "open-meteo", "ts": "2026-07-03T00:00:00",
        "body": "{\"rain\": 0.2}", "error": "",
    }))
    got = handoff.collect()
    assert len(got) == 1 and got[0].request_id == "r1"
    assert got[0].body == "{\"rain\": 0.2}"
    # Consumed by default.
    assert handoff.collect() == []


def test_observation_to_row_is_observed_tier_with_no_provenance_parameter():
    # The DerivedStore move: to_row() stamps `observed` with NO parameter, so a sensed result
    # physically cannot claim to be authored.
    obs = SensedObservation(request_id="r2", upstream="pubmed", ts="t", body="hi")
    row = obs.to_row()
    assert row["provenance"] == Provenance.OBSERVED.value
    assert row["source"] == "sense:pubmed"
    import inspect
    assert "provenance" not in inspect.signature(SensedObservation.to_row).parameters


def test_observed_view_holds_only_observed_rows():
    view = ObservedView.from_observations([
        SensedObservation(request_id="a", upstream="u", ts="t", body="x"),
    ])
    assert len(view) == 1
    assert view.rows()[0]["provenance"] == Provenance.OBSERVED.value
