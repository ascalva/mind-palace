"""Integrity tooth for GC-3 certified cuts (dn-global-event-clock §2.4 GC-N3, §2.8-4) — the
crossing-edge falsifier, NON-SKIPPABLE.

Item 2 (plan §7):
  * crossing-edge search — a certified cut's down-set `D` has NO edge `(a, b)` with `b ∈ D`, `a ∉ D`
    (an event inside the cut reading from one outside it). For a cut at the current frontier this is
    `[]`; a synthetically CORRUPTED cut (a chain's frontier moved PAST an event that references a
    not-included cross-chain event) is DETECTED.
  * down-set materialization — a chain-less SOURCE (catalog) rides in as a predecessor of the seed;
    a chain-less SINK (eval) is never pulled in — so a real full cut stays down-closed with no false
    crossing.

── VERIFICATION CAVEAT (read before trusting a green run in an isolated worktree) ──
In a delegated worktree `data/` is ABSENT, so `SpineSources.resolve()` yields an EMPTY spine and
every REAL-STORE leg passes TRIVIALLY (exactly how bp-051 shipped a latent 1467-event cycle). The
teeth here are the SEEDED in-memory cases (which run everywhere) plus the unit falsifiers
(`tests/unit/test_cuts.py`, the primary GC-3 falsifiers). The ORCHESTRATOR runs THIS file on main
against the live corpus — that is where the real cross-strata crossing search has teeth.

The crossing search reads only a cut's FRONTIER (not its certificates), so the real-stores leg
builds the cut directly from `Spine.frontier()` — no commit/trough/handoff wiring needed to run it
anywhere. The full frontier is the "current commit+handoff state" the plan names; certificate
SOURCING is exercised in the unit file.
"""

from __future__ import annotations

from pathlib import Path

from core.stores.catalog import VaultCatalog
from core.stores.derived import DerivedStore
from core.stores.runledger import RunLedger
from core.stores.versions import VersionStore
from core.temporal.spine import Certificate, CertifiedCut, Spine, SpineSources
from eval.harness.store import EvalKey, EvalResultsStore, Reading

_MEM = Path(":memory:")


def _cut_at_full_frontier(
    spine: Spine, certs: frozenset[Certificate] = frozenset()
) -> CertifiedCut:
    """A cut whose frontier is EVERY chain's latest position — the "current state" cut. The crossing
    search reads only the frontier, so the certificate set is immaterial here (sourced + tested in
    the unit file); pass whatever."""
    return CertifiedCut(frontier=tuple(sorted(spine.frontier().items())),
                        certificates=certs, evidence=())


def _cross_strata_spine() -> Spine:
    """A version (mirror) whose digest a run-claim (ops) CONSUMES — a real cross-strata g2 edge
    `versions:docX:1 → runledger:claim:1`, the substrate for the corruption falsifier."""
    vs = VersionStore(_MEM)
    vs.record("docX", "DIG")
    led = RunLedger(_MEM)
    run_id = led.start_run(pipeline="dream_v2", config_fingerprint="cf", corpus_digest="cd",
                           node_count=1, edge_count=0, duration_s=0.1, spectral_stats={})
    led.add_claim(run_id, kind="tension", confidence=0.5, support=("DIG",), surface_text="t",
                  polarity="-")
    return Spine.derive(SpineSources(versions=vs, ledger=led))


# ── the crossing-edge tooth (Law §2.4 falsifier) ────────────────────────────────────────────────


def test_honest_cut_has_no_crossing_edges_seeded() -> None:
    """A cut at the current frontier over a cross-strata reads-from edge is down-closed: both the
    producer (version) and the consumer (claim) are inside D, so the g2 edge is internal — no
    crossing."""
    spine = _cross_strata_spine()
    cut = _cut_at_full_frontier(spine)
    assert spine.crossing_edges(cut) == []
    d = spine.downset(cut)
    assert "versions:docX:1" in d and "runledger:claim:1" in d   # the down-set spans both strata


def test_frontier_moved_past_a_referenced_event_is_detected_seeded() -> None:
    """THE FALSIFIER: a certified cut whose ops frontier includes the claim but whose mirror
    frontier was moved BEFORE the version that produced the digest the claim reads — the classic
    "frontier moved past a referenced event". `versions:docX:1` is EXCLUDED (frontier 0) while the
    claim that reads its digest is INCLUDED ⇒ a crossing g2 edge the tooth MUST catch (else the cut
    is unsound and — on real data — merge-blocking)."""
    spine = _cross_strata_spine()
    corrupt = CertifiedCut(
        frontier=(("runledger:claim", 1), ("runledger:run", 1), ("versions:docX", 0)),
        certificates=frozenset({Certificate.COMMIT, Certificate.TROUGH}),
        evidence=("commit:CORRUPT",),
    )
    crossings = spine.crossing_edges(corrupt)
    assert crossings, "a frontier moved past a referenced event MUST be detected as a crossing"
    assert ("versions:docX:1", "runledger:claim:1") in crossings   # the g2 reads-from that crosses
    assert "versions:docX:1" not in spine.downset(corrupt)         # the producer was excluded


def test_out_of_scope_edge_is_not_a_crossing_seeded() -> None:
    """An edge whose EXCLUDED source is on a chain the cut does NOT cover (a stratum out of scope,
    §2.7 GC-N8) is not a crossing — the cut reads only in-scope events. A cut over ops alone drops
    the mirror version entirely (its chain absent from the frontier), so the mirror→ops edge exits
    scope rather than crossing."""
    spine = _cross_strata_spine()
    ops_only = CertifiedCut(
        frontier=(("runledger:claim", 1), ("runledger:run", 1)),   # mirror chain NOT covered
        certificates=frozenset({Certificate.TROUGH, Certificate.HANDOFF}),
        evidence=(),
    )
    assert spine.crossing_edges(ops_only) == []                    # exits scope, not a crossing
    assert "versions:docX:1" not in spine.downset(ops_only)


# ── down-set materialization: chain-less SOURCE rides in, chain-less SINK does not ───────────────


def test_downset_pulls_in_chainless_source_excludes_chainless_sink() -> None:
    """A catalog file (chain-less SOURCE) whose digest a derived artifact (chained) consumes rides
    INTO D as a predecessor; an eval reading (chain-less SINK) never does — so a full cut is
    down-closed with no false crossing on the source→consumer edge."""
    cat = VaultCatalog(_MEM)
    cat.record("notes/x.md", "CATDIG", "X")                        # chain-less source; mints CATDIG
    ds = DerivedStore(_MEM)
    ds.add(kind="dream", summary="s", subjects=("x",), derived_from=("CATDIG",))  # consumes CATDIG
    es = EvalResultsStore(_MEM)
    es.put(Reading(key=EvalKey("s", "c", "cfg", 1), metric_name="m", value=1.0, type_tag="Inv"))
    spine = Spine.derive(SpineSources(catalog=cat, derived=ds, eval=es))
    cut = _cut_at_full_frontier(spine)
    d = spine.downset(cut)
    assert any(e.startswith("derived:") for e in d)                # the chained seed
    assert any(e.startswith("catalog:") for e in d)                # chain-less SOURCE pulled in
    assert not any(e.startswith("eval:") for e in d)               # chain-less SINK excluded
    assert spine.crossing_edges(cut) == []                         # catalog→derived is internal


# ── ON THE REAL STORES (trivial in a worktree; the ORCHESTRATOR runs this on main) ──────────────


def test_certified_cut_has_no_crossing_edges_on_real_stores() -> None:
    """The Item 2 real-stores acceptance: a cut at the current frontier over the LIVE spine has NO
    crossing edge. In a worktree `data/` is absent ⇒ empty spine ⇒ trivial; on main this walks the
    real cross-strata event graph for an unsound frontier (see the module VERIFICATION CAVEAT)."""
    real = Spine.derive(SpineSources.resolve())
    cut = _cut_at_full_frontier(real)
    assert real.crossing_edges(cut) == []


def test_real_full_downset_is_down_closed_on_real_stores() -> None:
    """ON THE REAL STORES: the full-frontier down-set is closed — every generator edge with its
    destination inside D also has its source inside D (over in-scope chains). Trivial in a worktree;
    real on main. This is the crossing search stated positively."""
    real = Spine.derive(SpineSources.resolve())
    cut = _cut_at_full_frontier(real)
    d = real.downset(cut)
    fmap = dict(cut.frontier)
    for edge in real.generators():
        if edge.dst in d and real._chain_of.get(edge.src) in fmap:
            assert edge.src in d, f"edge {edge.src}->{edge.dst} crosses the full cut (unsound)"
