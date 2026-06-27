"""Dream-phase R&D track (R0 interpreter panel + R1 adjudicator) — flag-OFF by default.

Proves the safety spine the charter requires:
  * HARD FLAG BOUNDARY — the entry points refuse to run unless [dream_rnd] enabled is set.
  * inputs are a MirrorView (authored-only firewall); every claim's support is authored.
  * agreement is a CONFIDENCE MULTIPLIER, not a vote — g=0 ⇒ c=0 even with many methods agreeing.
  * outputs are INTERPRETED-only, content-addressed to authored evidence, depth-1 (acyclic).
  * confidence and utility are separate (no combined scalar); the log is deterministic.
  * grounding terminates in authored leaves.
None of this runs in a normal session: the live cron path uses the Phase-7 Dreamer, not these.
"""

import dataclasses

import pytest

from config.loader import load_config
from core.dreaming import DreamRnDDisabledError, run_dream_rnd, run_panel
from core.dreaming.adjudicator import adjudicate
from core.dreaming.interpreters import BRIDGE, CENTRALITY, COMMUNITY, DENSITY, Claim
from core.mirror import MirrorView
from core.provenance import Provenance
from core.selfcheck import grounding_score
from core.stores.derived import DREAM_LOG, DerivedStore

# A small authored graph: two clusters (A, B) held together by a bridge note (g1), plus an
# isolated outlier (z1). 3-D vectors so every interpreter fires deterministically.
ROWS = [
    {"digest": "dA1", "title": "A1", "provenance": "authored", "vector": [1.0, 0.0, 0.0]},
    {"digest": "dA2", "title": "A2", "provenance": "authored", "vector": [0.97, 0.03, 0.0]},
    {"digest": "dB1", "title": "B1", "provenance": "authored", "vector": [0.0, 1.0, 0.0]},
    {"digest": "dB2", "title": "B2", "provenance": "authored", "vector": [0.0, 0.97, 0.03]},
    {"digest": "dG1", "title": "G1", "provenance": "authored", "vector": [0.7, 0.7, 0.0]},
    {"digest": "dZ1", "title": "Z1", "provenance": "authored", "vector": [0.0, 0.0, 1.0]},
]
AUTHORED_DIGESTS = {r["digest"] for r in ROWS}


def _view() -> MirrorView:
    return MirrorView(_rows=tuple(ROWS))


def _on_config():
    cfg = load_config()
    return dataclasses.replace(cfg, dream_rnd=dataclasses.replace(cfg.dream_rnd, enabled=True))


# --- the hard flag boundary -----------------------------------------------------

def test_panel_refuses_when_flag_off():
    # Default config has enabled=false → the R&D engine cannot run in a normal session.
    with pytest.raises(DreamRnDDisabledError):
        run_panel(_view(), config=load_config())


def test_full_run_refuses_when_flag_off(tmp_path):
    with pytest.raises(DreamRnDDisabledError):
        run_dream_rnd(_view(), DerivedStore(tmp_path / "d.sqlite"), config=load_config())


# --- R0: the interpreter panel --------------------------------------------------

def test_panel_runs_multiple_method_specialists():
    claims = run_panel(_view(), config=_on_config())
    methods = {c.method for c in claims}
    assert {COMMUNITY, CENTRALITY, BRIDGE, DENSITY} <= methods   # several lenses fired
    # change_point is a deferred seam — it contributes nothing (never faked).
    assert "change_point" not in methods


def test_every_claim_support_is_authored():
    # The firewall, structural: inputs are a MirrorView, so support can only be authored notes.
    for c in run_panel(_view(), config=_on_config()):
        assert set(c.support) <= AUTHORED_DIGESTS


def test_bridge_finds_the_structural_hole():
    bridges = [c for c in run_panel(_view(), config=_on_config()) if c.method == BRIDGE]
    assert bridges and all(b.data["focus"] == "dG1" for b in bridges)   # G1 is the bridge


# --- R1: the evidence-based adjudicator -----------------------------------------

def test_adjudicator_ranks_by_confidence_with_agreement_as_multiplier():
    claims = run_panel(_view(), config=_on_config())
    entries = adjudicate(claims, authored_digests=AUTHORED_DIGESTS, agreement_jaccard=0.5)
    assert entries == sorted(entries, key=lambda e: -e.confidence)     # confidence-ordered
    top = entries[0]
    # The main theme is corroborated by several distinct methods => higher confidence.
    assert top.agreement >= 3
    assert top.grounding == 1.0 and top.terminates_in_authored
    assert top.confidence == pytest.approx(0.5 * (1 + 0.1 * (top.agreement - 1)))
    # The lone outlier (one method) ranks below the multi-method theme.
    assert entries[-1].agreement < top.agreement
    assert entries[-1].confidence < top.confidence


def test_agreement_cannot_manufacture_confidence_from_no_evidence():
    # Three methods "agree" on a claim whose support resolves to NO authored leaf (g=0).
    # Agreement is a multiplier, not a vote: c = γ·g·(1+λ(n-1)) = 0 when g=0.
    ghost = [Claim(method=m, statement="x", support=("ghost",)) for m in ("m1", "m2", "m3")]
    entries = adjudicate(ghost, authored_digests=AUTHORED_DIGESTS, agreement_jaccard=0.5)
    assert len(entries) == 1 and entries[0].agreement == 3
    assert entries[0].grounding == 0.0
    assert entries[0].confidence == 0.0               # no evidence => no confidence
    assert entries[0].terminates_in_authored is False


def test_grounding_score_penalizes_non_authored_refs():
    assert grounding_score(["dA1", "dA2"], AUTHORED_DIGESTS) == 1.0
    assert grounding_score(["dA1", "interp-id"], AUTHORED_DIGESTS) == 0.5   # chain not closed
    assert grounding_score([], AUTHORED_DIGESTS) == 0.0


# --- storage: INTERPRETED-only, content-addressed, separate axes -----------------

def test_dream_log_is_stored_interpreted_only(tmp_path):
    derived = DerivedStore(tmp_path / "d.sqlite")
    entries = run_dream_rnd(_view(), derived, config=_on_config())
    stored = derived.all(kind=DREAM_LOG)
    assert stored and len(stored) == len(entries)
    for art in stored:
        assert art.provenance is Provenance.INTERPRETED          # structural §8 firewall
        assert set(art.derived_from) <= AUTHORED_DIGESTS         # leaves are authored (G2)
        assert derived.depth(art.id) == 1                        # depth-1 over authored ground
        assert "confidence" in art.data                          # belief axis present
        assert "utility" not in art.data                         # separate axis — never one scalar
        assert set(art.data["evidence"]) <= AUTHORED_DIGESTS     # content-addressed refs


def test_run_is_deterministic(tmp_path):
    a = run_dream_rnd(_view(), DerivedStore(tmp_path / "a.sqlite"), config=_on_config())
    b = run_dream_rnd(_view(), DerivedStore(tmp_path / "b.sqlite"), config=_on_config())
    assert [(e.statement, e.confidence, e.methods) for e in a] == \
           [(e.statement, e.confidence, e.methods) for e in b]


def test_observed_rows_cannot_enter_the_panel():
    # Even if a row source carries observed exhaust, the MirrorView projection drops it before
    # the panel ever sees it (Invariant 6, structural) — so no observed digest reaches a claim.
    class MixedStore:
        def all_rows(self, *, provenances=None):
            rows = ROWS + [{"digest": "OBS", "title": "obs", "provenance": "observed",
                            "vector": [0.5, 0.5, 0.5]}]
            if provenances is None:
                return rows
            allowed = {str(p) for p in provenances}
            return [r for r in rows if r["provenance"] in allowed]

    view = MirrorView.project(MixedStore())
    supports = {d for c in run_panel(view, config=_on_config()) for d in c.support}
    assert "OBS" not in supports
