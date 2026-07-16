"""Unit tests for the derived causal spine (GC-1, dn-global-event-clock §2.1–§2.2).

Item 1 — enumeration + g1 chains: per-store rowid/version_seq chains, per-doc version chains as
SEPARATE chains, eval events chain-less (position=None, no g1 edges), deterministic event ids.
Item 2 — g2 + g3 + closure + order(): a claim orders AFTER the version whose digest it references;
run→claims recorded program order; reference-less cross-store pairs are CONCURRENT; a forged ref
(no producing event) creates NO edge (dropped, never fabricated).
"""

from __future__ import annotations

from pathlib import Path

from core.complex_types import EdgeSign
from core.stores.edges import EdgeStore
from core.stores.runledger import RunLedger
from core.stores.versions import VersionStore
from core.temporal.spine import Order, Spine, SpineEvent, SpineSources
from eval.harness.store import EvalKey, EvalResultsStore, Reading

_MEM = Path(":memory:")


def _find_ref(spine: Spine, store: str, ident: str) -> SpineEvent:
    """The single event of `store` whose refs contain `ident`."""
    return next(e for e in spine.events() if e.store == store and ident in e.refs)


# ── Item 1 — enumeration + g1 chains ───────────────────────────────────────────────────────────


def test_versions_are_separate_per_doc_chains_in_seq_order() -> None:
    vs = VersionStore(_MEM)
    vs.record("docA", "digA1")          # docA seq 1
    vs.record("docA", "digA2")          # docA seq 2
    vs.record("docB", "digB1")          # docB seq 1 — a DISTINCT chain
    spine = Spine.derive(SpineSources(versions=vs))

    a1 = _find_ref(spine, "versions", "digA1")
    a2 = _find_ref(spine, "versions", "digA2")
    b1 = _find_ref(spine, "versions", "digB1")

    # position = version_seq; event ids deterministic + content-free
    assert (a1.position, a2.position, b1.position) == (1, 2, 1)
    assert a1.event_id == "versions:docA:1"
    assert b1.event_id == "versions:docB:1"

    # within a doc, the chain is a total order by seq
    assert spine.order(a1.event_id, a2.event_id) is Order.BEFORE
    assert spine.order(a2.event_id, a1.event_id) is Order.AFTER
    # across docs there is no g1 tie-break — concurrency is the correct answer
    assert spine.order(a1.event_id, b1.event_id) is Order.CONCURRENT


def test_edges_yield_a_rowid_chain() -> None:
    es = EdgeStore(_MEM)
    e1 = es.add("u1", "v1", sign=EdgeSign.CONTRADICT, rel_type="contradicts")
    e2 = es.add("u2", "v2", sign=EdgeSign.SUPPORT, rel_type="supports")
    spine = Spine.derive(SpineSources(edges=es))

    ev1 = _find_ref(spine, "edges", e1.edge_id)
    ev2 = _find_ref(spine, "edges", e2.edge_id)
    assert (ev1.position, ev2.position) == (1, 2)
    assert spine.order(ev1.event_id, ev2.event_id) is Order.BEFORE


def test_eval_events_are_chainless_no_g1_edges() -> None:
    es = EvalResultsStore(_MEM)
    es.put(Reading(key=EvalKey("spec", "corpusX", "cfg", 1), metric_name="m",
                   value=1.0, type_tag="Inv"))
    spine = Spine.derive(SpineSources(eval=es))

    evs = [e for e in spine.events() if e.store == "eval"]
    assert len(evs) == 1
    assert evs[0].position is None                     # chain-less (DuckDB, no append order)
    # its refs (corpusX/cfg/spec) resolve to no producing event → NO g1 or g2 edges at all
    assert spine.generators() == ()
    assert spine.report().refs_without_producer >= 1


def test_derivation_is_deterministic_run_to_run() -> None:
    vs = VersionStore(_MEM)
    vs.record("doc", "d1")
    vs.record("doc", "d2")
    s1 = Spine.derive(SpineSources(versions=vs))
    s2 = Spine.derive(SpineSources(versions=vs))
    assert s1.events() == s2.events()                  # frozen dataclasses compare by value
    assert s1.generators() == s2.generators()


# ── Item 2 — g2 (reads-from) + g3 (program order) + closure + order() ───────────────────────────


def _seed_run(led: RunLedger, *, support: tuple[str, ...], kind: str = "tension",
              polarity: str = "-") -> str:
    run_id = led.start_run(pipeline="dream_v2", config_fingerprint="cf", corpus_digest="cd",
                           node_count=1, edge_count=0, duration_s=0.1, spectral_stats={})
    led.add_claim(run_id, kind=kind, confidence=0.5, support=support, surface_text="txt",
                  polarity=polarity)
    return run_id


def test_claim_orders_after_the_version_whose_digest_it_references() -> None:
    vs = VersionStore(_MEM)
    vs.record("noteX", "DIG")
    led = RunLedger(_MEM)
    _seed_run(led, support=("DIG",))
    spine = Spine.derive(SpineSources(versions=vs, ledger=led))

    version_ev = _find_ref(spine, "versions", "DIG")
    claim_ev = _find_ref(spine, "runledger", "DIG")    # the claim consumes DIG
    assert spine.order(version_ev.event_id, claim_ev.event_id) is Order.BEFORE
    assert spine.order(claim_ev.event_id, version_ev.event_id) is Order.AFTER


def test_run_before_its_claims_program_order() -> None:
    led = RunLedger(_MEM)
    run_id = led.start_run(pipeline="dream_v2", config_fingerprint="cf", corpus_digest="cd",
                           node_count=1, edge_count=0, duration_s=0.1, spectral_stats={})
    led.add_claim(run_id, kind="tension", confidence=0.5, support=("S1",), surface_text="t1",
                  polarity="-")
    led.add_claim(run_id, kind="theme", confidence=0.5, support=("S2",), surface_text="t2",
                  polarity="+")
    spine = Spine.derive(SpineSources(ledger=led))

    run_ev = _find_ref(spine, "runledger", run_id)
    c1 = _find_ref(spine, "runledger", "S1")
    c2 = _find_ref(spine, "runledger", "S2")
    assert spine.order(run_ev.event_id, c1.event_id) is Order.BEFORE     # run → claim (g3)
    assert spine.order(run_ev.event_id, c2.event_id) is Order.BEFORE     # transitive via c1
    assert spine.order(c1.event_id, c2.event_id) is Order.BEFORE         # claim_1 → claim_2 (g3)


def test_referenceless_cross_store_pair_is_concurrent() -> None:
    vs = VersionStore(_MEM)
    vs.record("doc", "DV")
    es = EdgeStore(_MEM)
    e = es.add("uu", "vv", sign=EdgeSign.SUPPORT, rel_type="supports")   # no shared identifier
    spine = Spine.derive(SpineSources(versions=vs, edges=es))

    v = _find_ref(spine, "versions", "DV")
    edge_ev = _find_ref(spine, "edges", e.edge_id)
    assert spine.order(v.event_id, edge_ev.event_id) is Order.CONCURRENT


def test_forged_ref_is_dropped_never_fabricated() -> None:
    led = RunLedger(_MEM)
    _seed_run(led, support=("GHOST",))                  # GHOST is minted by no event
    spine = Spine.derive(SpineSources(ledger=led))

    ids = {e.event_id for e in spine.events()}
    # every generator edge points between REAL events — none fabricated to a nonexistent producer
    assert all(ed.src in ids and ed.dst in ids for ed in spine.generators())
    assert spine.report().refs_without_producer >= 1    # GHOST (+ cf/cd) reported, not edged


# ── the pinned surface: frontier / restrict / report ───────────────────────────────────────────


def test_frontier_is_per_chain_latest_position() -> None:
    vs = VersionStore(_MEM)
    vs.record("docA", "a1")
    vs.record("docA", "a2")
    vs.record("docB", "b1")
    spine = Spine.derive(SpineSources(versions=vs))
    assert spine.frontier() == {"versions:docA": 2, "versions:docB": 1}


def test_restrict_keeps_only_the_named_stratum() -> None:
    vs = VersionStore(_MEM)                              # mirror
    vs.record("doc", "d")
    es = EdgeStore(_MEM)                                 # interpreted
    es.add("u", "v", sign=EdgeSign.CONTRADICT, rel_type="contradicts")
    spine = Spine.derive(SpineSources(versions=vs, edges=es))

    mirror = spine.restrict("mirror")
    assert {e.store for e in mirror.events()} == {"versions"}
    assert all(e.stratum == "mirror" for e in mirror.events())


def test_report_names_the_unwired_stores() -> None:
    vs = VersionStore(_MEM)
    vs.record("doc", "d")
    rep = Spine.derive(SpineSources(versions=vs)).report()
    assert "versions" in rep.stores_enumerated
    # no-silent-caps (§2.9-5): the stores beyond the core seven are NAMED, never silently absent
    assert set(rep.stores_unwired) == {"proposals", "verdicts", "observations", "telemetry"}
