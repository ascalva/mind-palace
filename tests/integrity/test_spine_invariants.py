"""Integrity teeth for the derived causal spine (GC-1, dn-global-event-clock §2.8) — non-skippable.

Item 3:
  * **acyclicity** — a cycle in `≼_derived` FAILS the suite (a corrupted/forged reference; §2.8-1,
    fail-closed). Checked against the REAL repo stores (resolved from config) AND a seeded chain,
    plus the falsifier: mutually-referencing attestations make `derive()` raise.
  * **chain-embedding** — every store's g1/g2 chain embeds order-isomorphically in ≼.
  * **no-payload** — a SpineEvent carries exactly (event_id, store, stratum, position, refs); no
    field contains note text; and the module reads no wall-ordering key or store text column (grep).

Item 2 falsifier (§2.8-5): the attestation-DAG restriction of ≼'s g2 generator agrees edge-for-edge
with `derived_from_ids` — the built auto-link is the calibration oracle the generalization matches.
"""

from __future__ import annotations

import re
from dataclasses import fields
from pathlib import Path

import pytest

from core.attestation.attestor import StoreAttestor
from core.attestation.record import Attestation
from core.attestation.store import AttestationStore
from core.complex_types import EdgeSign
from core.stores.derived import DerivedStore
from core.stores.edges import EdgeStore
from core.stores.runledger import RunLedger
from core.stores.versions import VersionStore
from core.temporal import spine as spine_module
from core.temporal.spine import (
    Order,
    Spine,
    SpineCycleError,
    SpineEvent,
    SpineSources,
)

_MEM = Path(":memory:")


# ── acyclicity ─────────────────────────────────────────────────────────────────────────────────


def test_acyclicity_on_the_real_repo_stores() -> None:
    """derive() over the config-resolved real stores must not raise — a cycle is an integrity
    failure (plan §10 STOP). In a fresh worktree (no data/) this resolves to an empty spine; where
    real store files exist it exercises them. Non-skippable either way."""
    spine = Spine.derive(SpineSources.resolve())
    assert isinstance(spine.events(), list)               # constructed ⇒ acyclic


def test_acyclicity_on_a_seeded_multi_store_graph() -> None:
    vs = VersionStore(_MEM)
    vs.record("noteX", "DIG")
    store = AttestationStore(_MEM)
    att = StoreAttestor(store)
    att.emit(agent_role="ingest", action="ingest", input_hashes=["noteX"], output_hashes=["DIG"])
    att.emit(agent_role="dreamer", action="dream", input_hashes=["DIG"], output_hashes=["ART"])
    led = RunLedger(_MEM)
    run_id = led.start_run(pipeline="dream_v2", config_fingerprint="cf", corpus_digest="cd",
                           node_count=1, edge_count=0, duration_s=0.1, spectral_stats={})
    led.add_claim(run_id, kind="tension", confidence=0.5, support=("DIG",), surface_text="t",
                  polarity="-")
    spine = Spine.derive(SpineSources(versions=vs, attestations=store, ledger=led))
    assert spine.events()                                 # non-empty and acyclic


def test_forged_cycle_makes_derive_fail_closed() -> None:
    """Two attestations that each produce the other's input close a cycle in ≼_derived — the
    forged/corrupted-reference case. derive() must fail closed (§2.8-1)."""
    store = AttestationStore(_MEM)
    a = Attestation.create(timestamp="t", agent_role="r", action="x",
                           constitution_fingerprint="f", input_hashes=["H2"], output_hashes=["H1"])
    b = Attestation.create(timestamp="t", agent_role="r", action="x",
                           constitution_fingerprint="f", input_hashes=["H1"], output_hashes=["H2"])
    store.append(a)
    store.append(b)
    with pytest.raises(SpineCycleError):
        Spine.derive(SpineSources(attestations=store))


# ── chain-embedding ──────────────────────────────────────────────────────────────────────────--


def _find_ref(spine: Spine, store: str, ident: str) -> SpineEvent:
    return next(e for e in spine.events() if e.store == store and ident in e.refs)


def test_every_store_chain_embeds_order_isomorphically() -> None:
    # versions (g1 per-doc), edges (g1 rowid), attestations (g1 rowid), derived (g2 DAG)
    vs = VersionStore(_MEM)
    vs.record("d", "v1")
    vs.record("d", "v2")
    vs.record("d", "v3")
    es = EdgeStore(_MEM)
    e1 = es.add("a", "b", sign=EdgeSign.CONTRADICT, rel_type="contradicts")
    e2 = es.add("c", "d", sign=EdgeSign.SUPPORT, rel_type="supports")
    store = AttestationStore(_MEM)
    att = StoreAttestor(store)
    at1 = att.emit(agent_role="r", action="x", input_hashes=["seed"], output_hashes=["o1"])
    at2 = att.emit(agent_role="r", action="x", input_hashes=["o1"], output_hashes=["o2"])
    ds = DerivedStore(_MEM)
    parent = ds.add(kind="dream", summary="s", subjects=("t1",), derived_from=("LEAF",))
    child = ds.add(kind="finding", summary="s2", subjects=("t2",), derived_from=(parent.id,))
    spine = Spine.derive(
        SpineSources(versions=vs, edges=es, attestations=store, derived=ds)
    )

    # versions: v1 ≺ v2 ≺ v3 (positions strictly increasing along ≼)
    vev = [_find_ref(spine, "versions", f"v{i}") for i in (1, 2, 3)]
    assert [e.position for e in vev] == [1, 2, 3]
    assert spine.order(vev[0].event_id, vev[2].event_id) is Order.BEFORE
    # edges rowid chain
    assert spine.order(_find_ref(spine, "edges", e1.edge_id).event_id,
                       _find_ref(spine, "edges", e2.edge_id).event_id) is Order.BEFORE
    # attestations rowid chain + g2 DAG
    assert spine.order(next(iter(spine.producers_of({at1.id}))),
                       next(iter(spine.producers_of({at2.id})))) is Order.BEFORE
    # derived g2 DAG: parent ≺ child
    assert spine.order(next(iter(spine.producers_of({parent.id}))),
                       next(iter(spine.producers_of({child.id})))) is Order.BEFORE


# ── the §2.8-5 calibration oracle: spine g2 vs the attestation DAG ──────────────────────────────


def test_attestation_dag_agrees_edge_for_edge_with_derived_from_ids() -> None:
    store = AttestationStore(_MEM)
    att = StoreAttestor(store)
    att.emit(agent_role="ingest", action="ingest", input_hashes=["nX"], output_hashes=["D"])
    att.emit(agent_role="dreamer", action="dream", input_hashes=["D"], output_hashes=["A"])
    att.emit(agent_role="curator", action="curate", input_hashes=["A"], output_hashes=["F"])
    spine = Spine.derive(SpineSources(attestations=store))

    att_ids = {e.event_id for e in spine.events() if e.store == "attestations"}
    spine_g2 = {(ed.src, ed.dst) for ed in spine.generators()
                if ed.gen == "g2" and ed.src in att_ids and ed.dst in att_ids}

    def ev_of(att_id: str) -> str:
        return next(iter(spine.producers_of({att_id})))

    expected: set[tuple[str, str]] = set()
    for a in store.all():
        for parent in a.derived_from_ids:
            expected.add((ev_of(parent), ev_of(a.id)))

    assert expected                                       # the seed IS a chain (guard the oracle)
    assert spine_g2 == expected                           # generalization == the built exemplar


# ── no-payload (§2.7 GC-N8) ──────────────────────────────────────────────────────────────────--


def test_spine_event_is_metadata_only_row_shape() -> None:
    assert [f.name for f in fields(SpineEvent)] == \
        ["event_id", "store", "stratum", "position", "refs"]


def test_no_note_text_leaks_into_any_event_field() -> None:
    ds = DerivedStore(_MEM)
    ds.add(kind="dream", summary="TOPSECRET_BODY", subjects=("Secret Title",),
           data={"note": "TOPSECRET_BODY"}, derived_from=("LEAF",))
    led = RunLedger(_MEM)
    run_id = led.start_run(pipeline="dream_v2", config_fingerprint="cf", corpus_digest="cd",
                           node_count=1, edge_count=0, duration_s=0.1, spectral_stats={"k": 1.0})
    led.add_claim(run_id, kind="tension", confidence=0.5, support=("S",),
                  surface_text="TOPSECRET_CLAIM", polarity="-")
    spine = Spine.derive(SpineSources(derived=ds, ledger=led))

    blob = repr(spine.events())
    for secret in ("TOPSECRET_BODY", "Secret Title", "TOPSECRET_CLAIM"):
        assert secret not in blob


_SRC = Path(spine_module.__file__).read_text(encoding="utf-8")


def test_module_never_orders_by_a_wall_column() -> None:
    """Law C4, grep-testable: every ORDER BY is over rowid / version_seq / an identity key — never
    a wall timestamp (created_at / started_at / updated_at / at / timestamp)."""
    allowed = {"rowid", "doc_id, version_seq", "source_path"}
    clauses = [c.strip() for c in re.findall(r"ORDER BY ([^\"']+)", _SRC)]
    assert clauses                                        # sanity: the SELECTs are present
    assert all(c in allowed for c in clauses), f"a wall/other ordering key slipped in: {clauses}"


def test_module_reads_no_store_text_column() -> None:
    """No-payload (§2.7): the module SELECTs no note-text / summary / synthesis column."""
    for text_col in ("surface_text", "summary", "subjects", "spectral_stats",
                     "payload_json", "title"):
        assert text_col not in _SRC, f"spine reads a text/payload column {text_col!r}"
