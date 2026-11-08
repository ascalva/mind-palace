"""Two-phase ingestion against real stores (dn-two-phase-ingestion; ING-19 to ING-21): a lazy
landing is complete without its vector and asks for the drain; the drain lands what a synchronous
landing lands, idempotently, from any interleaving and across a crash; a structural answer is
invariant to the embedding state; `near` ranks pending items by the lexical index and says so; the
pending report; the certificate's candidates; re-embedding on a model change as the same drain;
and what the default and the corpus instances do."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, cast

import numpy as np
import pytest

from core.ingest.derive import drain, pending
from core.ingest.embed import Embedder
from core.kernel.clearance import MIRROR_READ
from core.kernel.config import REPO_ROOT, loader
from core.query import OPERATOR, QueryEngine
from core.sentence import compile_sentence, execute
from core.sentence.universe import build
from core.stores.plane import SharedPlane
from tests.fixtures.embedding import DIM, FakeEmbedder
from tests.fixtures.ingress import EVERY, Palace, palace_at, state_of, write_file
from tests.unit.test_sentence_universe import _Causal, _Chatlog, _Refs

NOTES = {"a.md": "# A\n\nalpha body about spectral gaps\n",
         "b.md": "# B\n\nbeta body about random walks\n",
         "c.md": "# C\n\ngamma body about nothing in particular\n"}


def _land(p: Palace, notes: dict[str, str] = NOTES) -> dict[str, Any]:
    for name, text in notes.items():
        write_file(p.vault, name, text)
    return p.run("do sync_vault")


def _rows(p: Palace) -> list[tuple[str, str]]:
    return sorted((str(r["source_path"]), str(r["digest"]))
                  for r in p.stores.plane.all_rows(clearance=EVERY))


def _engine(p: Palace) -> QueryEngine:
    """A query engine over a palace's stores (the stores the writer landed into), at the fake
    embedder's dimension, the strata it does not have faked empty."""
    from dataclasses import replace

    e = QueryEngine(replace(p.cfg, embedding=replace(p.cfg.embedding, dim=DIM)))
    e._cache.update({
        "vectors": p.stores.plane, "catalog": p.stores.catalog, "embedder": p.stores.embedder,
        "edges": p.stores.edges, "versions": p.stores.versions, "lexical": p.stores.lexical,
        "references": _Refs([]), "causal": _Causal([]), "chatlog": _Chatlog([]),
        "attestations": p.att,
    })
    return e


def _ask(p: Palace, text: str) -> Any:
    plan = compile_sentence(text, OPERATOR)
    return execute(plan, build(_engine(p), plan))


# ── ING-19: an item is complete without its vector ──────────────────────────────────────────────

def test_a_lazy_landing_is_complete_without_its_vector_and_asks_for_the_drain(tmp_path: Path):
    p = palace_at(tmp_path, lazy=True)
    assert _land(p)["effects"] == {"landed": 3}
    entries = {e.source_path: e for e in p.stores.catalog.active_entries()}
    assert len(entries) == 3                                       # the keys are written
    assert all(p.stores.raw.exists(e.digest) for e in entries.values())   # the bytes
    assert p.stores.versions is not None
    assert all(p.stores.versions.current(p.stores.catalog.doc_id_for(path)) is not None
               for path in entries)                                # the version chains
    assert len(p.att.all()) == 3                                   # the attestations
    assert p.stores.lexical is not None
    assert all(p.stores.lexical.holds_current(e.source_path, e.digest)
               for e in entries.values())                          # the lexical units
    assert _rows(p) == []                                          # and no vector
    assert sorted(e.source_path for e in pending(p.stores.catalog, p.stores.plane,
                                                 lexical=p.stores.lexical)) == sorted(entries)
    assert p.jobs == [("embed", {})]                                # one coalescing job a plan
    # UNCHANGED reads the key and the lexical units, not the plane: nothing lands twice, and a
    # plan that lands nothing asks for no drain
    assert p.run("do sync_vault")["effects"] == {"unchanged": 3}
    assert p.jobs == [("embed", {})]


def test_a_lazy_plan_charges_no_embed(tmp_path: Path):
    lazy, sync = palace_at(tmp_path, "lazy", lazy=True), palace_at(tmp_path, "sync")
    assert _land(lazy)["work"] < _land(sync)["work"]


def test_the_lexical_index_is_a_stage_before_the_key(tmp_path: Path):
    """A lazy landing that dies after its lexical units and before its key lands once when run
    again (ING-7 with the units in the rows' place): the key is the last write."""
    p = palace_at(tmp_path, lazy=True)
    record = p.stores.catalog.record
    calls = {"n": 0}

    def dying(*a: Any, **k: Any) -> Any:
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("died before the key")
        return record(*a, **k)

    p.stores.catalog.record = dying   # type: ignore[method-assign]
    write_file(p.vault, "a.md", NOTES["a.md"])
    with pytest.raises(RuntimeError):
        p.run("do sync_vault")
    assert p.stores.catalog.active_entries() == [] and p.stores.lexical is not None
    assert p.stores.lexical.count() == 1                 # the units landed, the key did not
    assert p.run("do sync_vault")["effects"] == {"landed": 1}
    assert p.stores.lexical.count() == 1                 # the units were not written twice


# ── ING-20: the drain converges and is idempotent ───────────────────────────────────────────────

def test_the_drain_lands_what_a_synchronous_landing_lands(tmp_path: Path):
    lazy, sync = palace_at(tmp_path, "lazy", lazy=True), palace_at(tmp_path, "sync")
    _land(lazy)
    _land(sync)
    report = drain(lazy.stores)
    assert (report.items, report.chunks, report.embedded, report.reused) == (3, 3, 3, 0)
    assert state_of(lazy) == state_of(sync)
    assert pending(lazy.stores.catalog, lazy.stores.plane, lexical=lazy.stores.lexical) == []
    again = drain(lazy.stores)
    assert (again.items, again.embedded) == (0, 0)             # idempotent: nothing pending
    assert state_of(lazy) == state_of(sync)


def test_landing_and_draining_interleave_to_one_store(tmp_path: Path):
    """Land a and b, drain, edit a and land c, drain; against land a, b, c (a edited) then drain:
    the same store (ING-20's interleaving)."""
    one, two = palace_at(tmp_path, "one", lazy=True), palace_at(tmp_path, "two", lazy=True)
    _land(one, {"a.md": NOTES["a.md"], "b.md": NOTES["b.md"]})
    drain(one.stores)
    edited = {**NOTES, "a.md": "# A\n\nalpha body, edited\n"}
    _land(one, edited)
    drain(one.stores)
    _land(two, edited)
    drain(two.stores)
    assert state_of(one)["catalog"] == state_of(two)["catalog"]
    assert state_of(one)["rows"] == state_of(two)["rows"]
    assert len(state_of(one)["rows"]) == 3
    assert pending(one.stores.catalog, one.stores.plane, lexical=one.stores.lexical) == []


def test_a_drain_that_dies_inside_the_planes_transaction_converges(tmp_path: Path):
    """The atoms insert before the occupancy transaction (PLN-4); a crash between them leaves the
    item pending and the atoms held, so the next drain embeds nothing and lands the rows."""
    p = palace_at(tmp_path, lazy=True)
    _land(p)
    write_fiber = SharedPlane._write_fiber
    state = {"died": False}

    def dying(self: SharedPlane, conn: Any, f: Any) -> Any:
        if not state["died"]:
            state["died"] = True
            raise RuntimeError("died inside the transaction")
        return write_fiber(self, conn, f)

    SharedPlane._write_fiber = dying   # type: ignore[method-assign]
    try:
        with pytest.raises(RuntimeError):
            drain(p.stores)
    finally:
        SharedPlane._write_fiber = write_fiber   # type: ignore[method-assign]
    assert _rows(p) == []                                           # nothing landed
    assert len(pending(p.stores.catalog, p.stores.plane, lexical=p.stores.lexical)) == 3
    report = drain(p.stores)
    assert (report.items, report.embedded, report.reused) == (3, 0, 3)   # ING-5: atoms reused
    assert len(_rows(p)) == 3


def test_a_drain_commits_as_it_goes_and_reports_each_group(tmp_path: Path):
    p = palace_at(tmp_path, lazy=True)
    _land(p)
    groups: list[list[str]] = []
    report = drain(p.stores, batch=1, landed=lambda paths: groups.append(list(paths)))
    assert report.items == 3 and len(groups) == 3                   # a group per chunk
    assert sorted(path for g in groups for path in g) == sorted(NOTES_PATHS(p))
    q = palace_at(tmp_path, "q", lazy=True)
    _land(q)
    partial = drain(q.stores, max_items=1)
    assert (partial.items, partial.left) == (1, 2)
    assert len(pending(q.stores.catalog, q.stores.plane, lexical=q.stores.lexical)) == 2


def NOTES_PATHS(p: Palace) -> list[str]:
    return [str(p.vault / name) for name in NOTES]


def test_an_empty_item_is_complete_with_nothing_to_derive(tmp_path: Path):
    p = palace_at(tmp_path, lazy=True)
    _land(p, {"props.md": "id:: ID-ONLY\n"})                       # properties only: no chunk
    assert p.stores.catalog.active_entries()[0].source_path.endswith("props.md")
    assert pending(p.stores.catalog, p.stores.plane, lexical=p.stores.lexical) == []
    report = drain(p.stores)
    assert (report.items, report.empty, report.embedded, report.left) == (0, 0, 0, 0)


def test_a_retire_takes_the_lexical_units_with_the_rows(tmp_path: Path):
    p = palace_at(tmp_path, lazy=True)
    _land(p)
    (p.vault / "c.md").unlink()
    assert p.run("do sync_vault")["effects"] == {"unchanged": 2, "retired": 1}
    assert p.stores.lexical is not None
    assert p.stores.lexical.units_of(str(p.vault / "c.md")) == 0
    assert len(pending(p.stores.catalog, p.stores.plane, lexical=p.stores.lexical)) == 2


def test_an_item_the_lexical_index_never_saw_is_pending_and_the_backfill_lands_it(
        tmp_path: Path):
    """An item landed while no lexical index was open (an earlier writer, or an instance that
    embedded synchronously) has no record in the index: it is pending, not taken for an empty
    item, and the drain derives it; the lexical backfill lands its units and records the empty
    item as complete, once."""
    from core.ingest.derive import derive_lexical
    from core.stores.lexical import LexicalStore

    p = palace_at(tmp_path, lazy=True)
    _land(p, {**NOTES, "props.md": "id:: ID-ONLY\n"})               # props.md has no chunk
    p.stores.lexical = LexicalStore(tmp_path / "opened-later.sqlite")
    assert len(pending(p.stores.catalog, p.stores.plane, lexical=p.stores.lexical)) == 4
    report = drain(p.stores)
    assert (report.items, report.empty, report.embedded) == (3, 1, 3)
    lex = derive_lexical(p.stores)
    assert (lex.items, lex.units, lex.empty, lex.left) == (4, 3, 1, 0)
    assert derive_lexical(p.stores).items == 0                     # idempotent
    assert all(p.stores.lexical.holds_current(e.source_path, e.digest)
               for e in p.stores.catalog.active_entries() if not e.source_path.endswith("props.md"))
    assert pending(p.stores.catalog, p.stores.plane, lexical=p.stores.lexical) == []


def test_the_planes_current_versions_are_holds_current_for_every_path(tmp_path: Path):
    """The drain's pending set reads the plane once (`current_versions`); it answers what
    `holds_current` answers path by path, a superseded version and a retired path included."""
    p = palace_at(tmp_path)
    _land(p)
    before = {e.source_path: e.digest for e in p.stores.catalog.active_entries()}
    write_file(p.vault, "a.md", "# A\n\nalpha body, edited\n")
    (p.vault / "c.md").unlink()
    assert p.run("do sync_vault")["effects"] == {"landed": 1, "unchanged": 1, "retired": 1}
    have = p.stores.plane.current_versions(clearance=MIRROR_READ)
    after = {e.source_path: e.digest for e in p.stores.catalog.active_entries()}
    for path, digest in set(before.items()) | set(after.items()):
        assert ((path, digest) in have) == p.stores.plane.holds_current(
            path, digest, clearance=MIRROR_READ)
    assert set(after.items()) <= have
    assert not ({(path, before[path]) for path in before if path.endswith(("a.md", "c.md"))}
                & have)


class _Client:
    """An embedder whose documents are embedded by the given function."""

    def __init__(self, fn: Any) -> None:
        self.embed_documents = fn


def test_a_text_the_embedder_refuses_for_length_is_cut_and_the_drain_converges(tmp_path: Path):
    """The embedding server refuses an input longer than its physical batch rather than truncating
    it, and a chunk's character budget does not bound its tokens. One refused text must not wedge
    the drain: its group goes in halves, the text alone is cut to the longest prefix the server
    takes, and the drain converges, counting the cut; any other failure is raised."""
    from core.ingest.derive import embed_fitting

    p = palace_at(tmp_path, lazy=True)
    _land(p, {**NOTES, "long.md": "# L\n\n" + "y" * 600 + "\n"})
    real = p.stores.embedder.embed_documents
    limit = 300
    asked: list[int] = []

    def refusing(texts: list[str]) -> list[list[float]]:
        asked.append(len(texts))
        if any(len(x) > limit for x in texts):
            raise RuntimeError("input (2951 tokens) is too large to process. increase the "
                               "physical batch size (current batch size: 2048)")
        return real(texts)

    p.stores.embedder.embed_documents = refusing          # type: ignore[method-assign]
    report = drain(p.stores)
    assert (report.items, report.cut) == (4, 1)
    assert pending(p.stores.catalog, p.stores.plane, lexical=p.stores.lexical) == []
    assert drain(p.stores).items == 0
    vectors, cuts = embed_fitting(_Client(refusing), ["a", "b" * 400, "c"])
    assert len(vectors) == 3 and cuts == [(400, limit)]
    assert vectors[1] == [float(x) for x in real(["b" * limit])[0]]

    def down(texts: list[str]) -> list[list[float]]:
        raise ConnectionError("connection refused")

    with pytest.raises(ConnectionError):
        embed_fitting(_Client(down), ["a"])


# ── ING-21: pending-report soundness ────────────────────────────────────────────────────────────

def test_a_structural_answer_is_invariant_to_the_embedding_state(tmp_path: Path):
    p = palace_at(tmp_path, lazy=True)
    _land(p)
    a, b = str(p.vault / "a.md"), str(p.vault / "b.md")
    assert p.run(f'do link(a: "{a}", b: "{b}", relation: "supports")')["effects"] == {"linked": 1}
    before = _ask(p, f'relate "{a}"')
    store = p.stores.edges
    assert store is not None
    edges = [(e.u, e.v, e.rel_type) for e in store.all()]
    catalog = state_of(p)["catalog"]
    drain(p.stores)
    after = _ask(p, f'relate "{a}"')
    assert [h.ref for h in before.hits] == [h.ref for h in after.hits] == [b]
    assert [(e.u, e.v, e.rel_type) for e in store.all()] == edges
    assert state_of(p)["catalog"] == catalog


def test_near_ranks_pending_items_by_the_lexical_index_and_says_so(tmp_path: Path):
    p = palace_at(tmp_path, lazy=True)
    _land(p)
    before = _ask(p, 'near "spectral gaps"')
    assert [h.ref for h in before.hits] == [str(p.vault / "a.md")]   # the term's note alone
    assert before.hits[0].detail["ranked_by"] == "lexical: the vector is pending"
    assert before.hits[0].detail["pending"] == "no vector yet"
    assert any("3 of the clause's 3 nodes are pending" in n for n in before.notes)
    assert any(n.startswith("pending: 3 items landed without a vector yet") for n in before.notes)
    drain(p.stores)
    after = _ask(p, 'near "spectral gaps"')
    assert len(after.hits) == 3                                      # the cosines, every note
    assert all("ranked_by" not in h.detail and "pending" not in h.detail for h in after.hits)
    assert not any("pending" in n for n in after.notes)


def test_a_stale_vector_is_pending_and_never_read(tmp_path: Path):
    p = palace_at(tmp_path, lazy=True)
    _land(p)
    drain(p.stores)
    _land(p, {**NOTES, "a.md": "# A\n\nalpha body, now about tides\n"})   # a new version, no drain
    u = build(_engine(p), compile_sentence('near "tides"', OPERATOR))
    a = str(p.vault / "a.md")
    i = next(i for i, n in enumerate(u.notes) if n["source_path"] == a)
    assert i in u.pending and u.notes[i]["detail"]["pending"] == "the vector is an older version's"
    assert not np.any(u.vectors[i])                                # the old vector is dropped
    answer = execute(compile_sentence('near "tides"', OPERATOR), u)
    assert [h.ref for h in answer.hits][0] == a                      # by the lexical index
    assert answer.hits[0].detail["ranked_by"].startswith("lexical")


def test_without_a_lexical_index_a_pending_item_scores_nothing_and_is_reported(tmp_path: Path):
    p = palace_at(tmp_path, lazy=True)
    _land(p)
    plan = compile_sentence('near "spectral gaps"', OPERATOR)
    u = build(_engine(p), plan)
    assert len(u.pending) == 3
    # the evaluator with no index to rank them by: the pending nodes score nothing and the
    # answer says so; a zero is no guessed vector (the Lean control `zeroRead_changes`)
    from dataclasses import replace
    answer = execute(plan, replace(u, lexical=None))
    assert answer.hits == ()
    assert any("no lexical index is open" in n for n in answer.notes)
    # an engine without the index loads no pending node at all: there is nothing to read them by
    e = _engine(p)
    e._cache["lexical"] = None
    bare = build(e, plan)
    assert len(bare) == 0 and bare.pending == frozenset()


def test_the_default_instance_embeds_synchronously_and_the_corpus_instance_lazily():
    from core.kernel.config import get_config
    assert get_config().embedding.lazy is False                      # the live behaviour, unchanged
    corpus = loader._named_config(Path(REPO_ROOT) / "config" / "instances" / "corpus.toml")
    assert corpus.instance.id == "corpus" and corpus.embedding.lazy is True
    assert (corpus.embedding.batch, corpus.embedding.streams) == (64, 1)
    bench = loader._named_config(Path(REPO_ROOT) / "config" / "instances" / "bench.toml")
    assert bench.embedding.lazy is False


def test_the_batch_policy_refuses_nothing_a_request_can_carry():
    from dataclasses import replace

    from core.kernel.config import get_config
    with pytest.raises(ValueError, match="batch"):
        replace(get_config().embedding, batch=0)
    with pytest.raises(ValueError, match="streams"):
        replace(get_config().embedding, streams=0)


def test_sync_embed_starts_the_embed_job(tmp_path: Path):
    p = palace_at(tmp_path, lazy=True)
    assert p.run("do sync_embed")["effects"] == {"queued": 1}
    assert p.jobs == [("embed", {})]


def test_the_embed_kind_coalesces_and_pins():
    from scheduler.queue import _IDEMPOTENT_KINDS, _REQUEUE_KINDS
    from scheduler.router import _PINNED_KINDS
    assert "embed" in _IDEMPOTENT_KINDS and "embed" in _REQUEUE_KINDS and "embed" in _PINNED_KINDS


# ── the certificate and the re-embedding ───────────────────────────────────────────────────────

def test_the_certificate_is_asserted_over_the_stored_vectors_alone(tmp_path: Path):
    p = palace_at(tmp_path, lazy=True)
    _land(p)
    drain(p.stores, max_items=2)
    waiting = pending(p.stores.catalog, p.stores.plane, lexical=p.stores.lexical)
    assert len(waiting) == 1
    q = cast(Any, p.stores.embedder).embed_query("spectral gaps")
    ranked = p.stores.plane.search_ranked(q, k=3, clearance=MIRROR_READ)
    assert len(ranked.rows) == 2                                    # the pending item is absent
    assert waiting[0].source_path not in {str(r["source_path"]) for r in ranked.rows}
    assert ranked.margin.k == 3 and ranked.margin.gap == float("inf")  # nothing outside the top
    drain(p.stores)
    full = p.stores.plane.search_ranked(q, k=3, clearance=MIRROR_READ)
    assert len(full.rows) == 3 and ranked.margin.bound == full.margin.bound


class _OtherEmbedder(FakeEmbedder):
    """Another identity: the same texts, other vectors."""

    def _vec(self, text: str) -> list[float]:
        h = hashlib.sha256(("other:" + text.strip()).encode("utf-8")).digest()
        return [b / 255.0 for b in h[:DIM]]


def test_reembedding_on_a_model_change_is_the_same_drain(tmp_path: Path):
    p = palace_at(tmp_path, lazy=True)
    _land(p)
    drain(p.stores)
    before = {str(r["source_path"]): list(r["vector"])
              for r in p.stores.plane.all_rows(clearance=EVERY)}
    fixed = (state_of(p)["catalog"], state_of(p)["versions"], state_of(p)["attestations"])
    p.stores.plane.reset()                                          # the identity is forgotten
    assert len(pending(p.stores.catalog, p.stores.plane, lexical=p.stores.lexical)) == 3
    p.stores.embedder = cast(Embedder, _OtherEmbedder())
    report = drain(p.stores)
    assert (report.items, report.embedded) == (3, 3)
    after = {str(r["source_path"]): list(r["vector"])
             for r in p.stores.plane.all_rows(clearance=EVERY)}
    assert set(after) == set(before) and all(after[k] != before[k] for k in after)
    assert (state_of(p)["catalog"], state_of(p)["versions"], state_of(p)["attestations"]) == fixed
