"""Unit tests for GC-3 certified cuts (dn-global-event-clock §2.4 GC-N3) — the PRIMARY falsifiers.

`tests/integrity/test_cut_soundness.py` runs the crossing-edge tooth on the LIVE stores, which a
fresh worktree lacks (`data/` absent) — there it passes TRIVIALLY. So certificate COMPOSITION, the
REFUSALS, and the hash / ride-in-`Scope.cut` acceptance are exercised HERE, on INJECTED fakes, under
full control.

Item 1 (plan §7):
  * `cut_at` over fakes composes the RIGHT certificate set per strata (mirror→COMMIT;
    ops/interpreted→TROUGH+HANDOFF; eval→TROUGH; the full cross-strata cut → all three).
  * a stratum whose certificate observable is ABSENT (or NOT quiescent / NOT empty) ⇒ REFUSAL with a
    clear message — never a fabricated certificate.
  * a certificate rides from its NAMED OBSERVABLE (commit SHA / trough id / handoff-listing hash),
    never wall-time or inference — the evidence carries the observable.
  * `CertifiedCut` HASHES and rides in `Scope.cut` UNCHANGED (a multi-stratum POINT scope, no
    `SliceError` — the pin: `core/scope.py` is NOT touched).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from core.scope import (
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
from core.stores.derived import DerivedStore
from core.stores.runledger import RunLedger
from core.stores.versions import VersionStore
from core.temporal.spine import (
    Certificate,
    CertifiedCut,
    CutCertificateError,
    CutSources,
    Spine,
    SpineSources,
    TroughState,
)
from eval.harness.store import EvalKey, EvalResultsStore, Reading

_MEM = Path(":memory:")
_QUIESCENT = TroughState(queued=0, running=0, trough_id="trough-abc")


def _four_stratum_sources() -> SpineSources:
    """One event per stratum: versions→mirror, runledger→ops, derived→interpreted, eval→eval. The
    runledger claim CONSUMES the version digest, so a real g2 edge crosses mirror→ops (used by the
    soundness test; harmless here)."""
    vs = VersionStore(_MEM)
    vs.record("docA", "DIG")                                   # mirror; produces DIG
    led = RunLedger(_MEM)                                      # ops
    run_id = led.start_run(pipeline="dream_v2", config_fingerprint="cf", corpus_digest="cd",
                           node_count=1, edge_count=0, duration_s=0.1, spectral_stats={})
    led.add_claim(run_id, kind="tension", confidence=0.5, support=("DIG",), surface_text="t",
                  polarity="-")
    ds = DerivedStore(_MEM)                                    # interpreted
    ds.add(kind="dream", summary="s", subjects=("x",), derived_from=("DIG",))
    es = EvalResultsStore(_MEM)                                # eval (chain-less)
    es.put(Reading(key=EvalKey("s", "c", "cfg", 1), metric_name="m", value=1.0, type_tag="Inv"))
    return SpineSources(versions=vs, ledger=led, derived=ds, eval=es)


def _spine(*, commit: str | None = "deadbeef", trough: TroughState | None = _QUIESCENT,
           handoff: Path | None = None) -> Spine:
    return Spine.derive(
        _four_stratum_sources(),
        cut_sources=CutSources(commit_sha=commit, trough=trough, handoff=handoff),
    )


def _empty_handoff(tmp_path: Path) -> Path:
    """An empty sensing handoff: requests/ and observations/ exist and are empty ⇒ certifies."""
    (tmp_path / "requests").mkdir()
    (tmp_path / "observations").mkdir()
    return tmp_path


# ── certificate COMPOSITION per strata ──────────────────────────────────────────────────────────


def test_mirror_cut_composes_commit_only(tmp_path: Path) -> None:
    cut = _spine(handoff=_empty_handoff(tmp_path)).cut_at(strata=frozenset({"mirror"}))
    assert cut.certificates == frozenset({Certificate.COMMIT})
    assert any(e == "commit:deadbeef" for e in cut.evidence)   # the injected SHA, not wall-time


def test_ops_cut_composes_trough_and_handoff(tmp_path: Path) -> None:
    cut = _spine(handoff=_empty_handoff(tmp_path)).cut_at(strata=frozenset({"ops"}))
    assert cut.certificates == frozenset({Certificate.TROUGH, Certificate.HANDOFF})
    assert any(e == "trough:trough-abc" for e in cut.evidence)  # the scheduler's own trough id


def test_interpreted_cut_composes_trough_and_handoff(tmp_path: Path) -> None:
    cut = _spine(handoff=_empty_handoff(tmp_path)).cut_at(strata=frozenset({"interpreted"}))
    assert cut.certificates == frozenset({Certificate.TROUGH, Certificate.HANDOFF})


def test_eval_cut_composes_trough_only(tmp_path: Path) -> None:
    cut = _spine(handoff=_empty_handoff(tmp_path)).cut_at(strata=frozenset({"eval"}))
    assert cut.certificates == frozenset({Certificate.TROUGH})


def test_full_cross_strata_cut_composes_all_three(tmp_path: Path) -> None:
    """The note's full cut = commit ∧ trough-empty ∧ handoff-empty (§2.4)."""
    strata = frozenset({"mirror", "ops", "interpreted", "eval"})
    cut = _spine(handoff=_empty_handoff(tmp_path)).cut_at(strata=strata)
    assert cut.certificates == frozenset(
        {Certificate.COMMIT, Certificate.TROUGH, Certificate.HANDOFF}
    )
    # frontier keys are per-CHAIN ("<store>:<chain-key>"); the mirror doc + ops chains are present
    keys = {k for k, _pos in cut.frontier}
    assert "versions:docA" in keys and "runledger:run" in keys and "runledger:claim" in keys


def test_frontier_positions_are_the_latest_per_chain(tmp_path: Path) -> None:
    vs = VersionStore(_MEM)
    vs.record("docA", "a1")
    vs.record("docA", "a2")
    vs.record("docB", "b1")
    spine = Spine.derive(SpineSources(versions=vs), cut_sources=CutSources(commit_sha="c0"))
    cut = spine.cut_at(strata=frozenset({"mirror"}))
    fmap = dict(cut.frontier)
    assert fmap["versions:docA"] == 2                          # latest position on docA's chain
    assert fmap["versions:docB"] == 1


# ── REFUSALS — a missing / non-quiescent / non-empty certificate refuses, never fabricates ──────


def test_commit_absent_refuses(tmp_path: Path) -> None:
    spine = _spine(commit=None, handoff=_empty_handoff(tmp_path))
    with pytest.raises(CutCertificateError, match="commit certificate absent"):
        spine.cut_at(strata=frozenset({"mirror"}))


def test_trough_absent_refuses(tmp_path: Path) -> None:
    spine = _spine(trough=None, handoff=_empty_handoff(tmp_path))
    with pytest.raises(CutCertificateError, match="trough certificate absent"):
        spine.cut_at(strata=frozenset({"ops"}))


def test_trough_not_quiescent_refuses(tmp_path: Path) -> None:
    """A NON-empty queue is NOT quiescence — the cut refuses rather than assume no in-flight."""
    busy = TroughState(queued=2, running=1, trough_id="t-busy")
    spine = _spine(trough=busy, handoff=_empty_handoff(tmp_path))
    with pytest.raises(CutCertificateError, match="NOT quiescent"):
        spine.cut_at(strata=frozenset({"ops"}))


def test_handoff_absent_refuses() -> None:
    spine = _spine(handoff=None)
    with pytest.raises(CutCertificateError, match="handoff certificate absent"):
        spine.cut_at(strata=frozenset({"ops"}))


def test_handoff_not_empty_refuses(tmp_path: Path) -> None:
    """An in-flight request in the handoff ⇒ edge↔core flow is live ⇒ the cut refuses."""
    handoff = _empty_handoff(tmp_path)
    (handoff / "requests" / "req-1.json").write_text("{}")
    spine = _spine(handoff=handoff)
    with pytest.raises(CutCertificateError, match="NOT empty"):
        spine.cut_at(strata=frozenset({"ops"}))


def test_unknown_stratum_refuses(tmp_path: Path) -> None:
    spine = _spine(handoff=_empty_handoff(tmp_path))
    with pytest.raises(CutCertificateError, match="unknown strata"):
        spine.cut_at(strata=frozenset({"nonesuch"}))


# ── PROVENANCE — the evidence is the OBSERVABLE, never wall-time ─────────────────────────────────


def test_trough_evidence_tracks_the_scheduler_state_not_wall(tmp_path: Path) -> None:
    """Two cuts taken at DIFFERENT scheduler quiescent states carry DIFFERENT trough evidence — the
    evidence is sourced from the scheduler's OWN state (its trough id), never a wall timestamp."""
    handoff = _empty_handoff(tmp_path)
    cut1 = _spine(trough=TroughState(0, 0, "trough-1"), handoff=handoff).cut_at(
        strata=frozenset({"ops"}))
    cut2 = _spine(trough=TroughState(0, 0, "trough-2"), handoff=handoff).cut_at(
        strata=frozenset({"ops"}))
    assert any("trough-1" in e for e in cut1.evidence)
    assert any("trough-2" in e for e in cut2.evidence)
    assert cut1.evidence != cut2.evidence


def test_handoff_evidence_is_a_deterministic_listing_hash(tmp_path: Path) -> None:
    spine = _spine(handoff=_empty_handoff(tmp_path))
    a = spine.cut_at(strata=frozenset({"ops"}))
    b = spine.cut_at(strata=frozenset({"ops"}))
    assert a.evidence == b.evidence                            # deterministic (same observable)
    assert any(e.startswith("handoff:") for e in a.evidence)


# ── CertifiedCut is HASHABLE and rides in Scope.cut UNCHANGED ────────────────────────────────────


def test_certified_cut_is_hashable(tmp_path: Path) -> None:
    cut = _spine(handoff=_empty_handoff(tmp_path)).cut_at(strata=frozenset({"mirror", "ops"}))
    assert isinstance(cut, CertifiedCut)
    assert hash(cut) == hash(cut)                              # frozen dataclass ⇒ stable hash
    assert len({cut, cut}) == 1                                # usable in a set


def test_certified_cut_rides_in_scope_cut_no_slice_error(tmp_path: Path) -> None:
    """A multi-stratum POINT scope on a non-cut clock needs an explicit cut (the SLICE rule). The
    CertifiedCut satisfies it UNCHANGED — it is the opaque Hashable `Scope.cut` (pin: scope.py
    untouched)."""
    cut = _spine(handoff=_empty_handoff(tmp_path)).cut_at(strata=frozenset({"mirror", "ops"}))
    s = Scope(
        StratumScope.of(Stratum.OPS, Stratum.MIRROR),
        EdgeScope.bottom(),
        TimeScope(Clock.N_S, Window.point(1)),                # N_S ∉ _CUT_CLOCKS ⇒ SLICE needs cut
        Authority.read_only(),
        tier=Tier.STATIC_GUARD,
        cut=cut,
    )
    assert len(s.sigma.strata) > 1                             # SLICE rule was in force
    assert s.cut is cut                                        # rides UNCHANGED


def test_multi_stratum_point_scope_without_the_cut_still_raises() -> None:
    """Control: the SLICE rule genuinely fires here — so the previous test proves the cut satisfied
    it, not that the rule was inert."""
    from core.scope import SliceError

    with pytest.raises(SliceError):
        Scope(
            StratumScope.of(Stratum.OPS, Stratum.MIRROR),
            EdgeScope.bottom(),
            TimeScope(Clock.N_S, Window.point(1)),
            Authority.read_only(),
            tier=Tier.STATIC_GUARD,
        )
