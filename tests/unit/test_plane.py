"""The shared plane (core/stores/plane.py; dn-vector-membership-store Amendment A3).

The owner's words, 2026-10-29: documents that share chunks "have pointers to those vectors in
common"; an edit creates "a supersession edge from the doc … to the updated doc with the new vector
reference set"; and none of it may leak — "accessible records without the correct permission should
be unrepresentable". Each test names the degenerate input that would let it pass vacuously and
asserts the precondition that rules it out (the false-success rule).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import pytest

from core.kernel.clearance import (
    CURATED_READ,
    DIALOGUE_READ,
    MAINTENANCE_READ,
    MIRROR_READ,
    OBSERVED_READ,
)
from core.kernel.provenance import Provenance
from core.stores.plane import (
    OCC,
    PLANE_CLASSES,
    SUP,
    Fingerprint,
    GeometryMismatch,
    MissingVector,
    PlaneError,
    SharedPlane,
    StratumConflict,
    atom_id,
)
from tests.fixtures.fakes import HashingEmbedder
from tests.fixtures.plane_fakes import MemoryAtoms

EMB = HashingEmbedder(32)
SOLO, DIALOGUE, OBSERVED, CURATED = (Provenance.AUTHORED_SOLO, Provenance.AUTHORED_DIALOGUE,
                                     Provenance.OBSERVED, Provenance.CURATED)


def _plane(tmp_path: Path, fp: Fingerprint | None = None) -> SharedPlane:
    return SharedPlane(tmp_path / "plane", MemoryAtoms(), fingerprint=fp)


def _rows(path: str, digest: str, prov: Provenance, texts: list[str], *,
          vectors: bool = True, title: str = "t") -> list[dict[str, Any]]:
    return [{"source_path": path, "digest": digest, "provenance": prov.value, "title": title,
             "chunk_index": i, "text": t, "layer": "prose",
             "vector": EMB.embed_query(t) if vectors else None} for i, t in enumerate(texts)]


def _texts(rows: list[Any]) -> list[tuple[str, int, str]]:
    return sorted((r["source_path"], r["chunk_index"], r["text"]) for r in rows)


# ── sharing ────────────────────────────────────────────────────────────────────────────────────

def test_shared_chunks_are_stored_once_and_each_document_reconstitutes(tmp_path):
    p = _plane(tmp_path)
    a = ["common opening", "shared middle", "only in a"]
    b = ["common opening", "shared middle", "only in b"]
    p.land(_rows("a.md", "da", SOLO, a))
    report = p.land(_rows("b.md", "db", SOLO, b))
    assert report.atoms_inserted == 1 and report.atoms_reused == 2
    assert len(p.atoms.ids()) == 4 < len(a) + len(b)          # precondition: sharing happened
    rows = p.reader(MIRROR_READ).rows()
    assert _texts(rows) == sorted([("a.md", i, t) for i, t in enumerate(a)]
                                  + [("b.md", i, t) for i, t in enumerate(b)])
    for r in rows:
        assert r["vector"] == EMB.embed_query(r["text"]) and r["id"].startswith(r["source_path"])


def test_an_edit_reuses_unchanged_atoms_and_records_the_supersession(tmp_path):
    p = _plane(tmp_path)
    p.land(_rows("n.md", "v1", SOLO, ["x", "y", "z"]))
    r = p.land(_rows("n.md", "v2", SOLO, ["x", "y", "w"]))
    assert (r.atoms_inserted, r.atoms_reused, r.made_current, r.superseded) == (1, 2, 3, 3)
    reader = p.reader(MIRROR_READ)
    assert _texts(reader.rows()) == [("n.md", 0, "x"), ("n.md", 1, "y"), ("n.md", 2, "w")]
    assert {r["digest"] for r in reader.rows(include_superseded=True)} == {"v1", "v2"}
    assert [(h["old_digest"], h["new_digest"]) for h in reader.history("n.md")] == [
        ("", "v1"), ("v1", "v2")]


def test_a_revert_is_two_supersession_edges_and_mints_nothing(tmp_path):
    """C1 at prose grain: A → B → A must leave A current, B superseded, two real supersessions."""
    p = _plane(tmp_path)
    p.land(_rows("n.md", "A", SOLO, ["alpha", "beta"]))
    p.land(_rows("n.md", "B", SOLO, ["alpha", "gamma"]))
    third = p.land(_rows("n.md", "A", SOLO, ["alpha", "beta"]))
    assert third.atoms_inserted == 0
    occ = p.reader(MIRROR_READ).occupancies(include_superseded=True)
    assert {(o.digest, o.current) for o in occ} == {("A", True), ("B", False)}
    edges = [(h["old_digest"], h["new_digest"]) for h in p.reader(MIRROR_READ).history("n.md")]
    assert edges == [("", "A"), ("A", "B"), ("B", "A")]
    assert sum(1 for old, _ in edges if old) == 2
    again = p.land(_rows("n.md", "A", SOLO, ["alpha", "beta"]))       # converged: a no-op
    assert (again.made_current, again.superseded) == (0, 0)
    assert len(p.reader(MIRROR_READ).history("n.md")) == 3


def test_a_changed_derivation_replaces_the_fiber_without_a_false_edge(tmp_path):
    p = _plane(tmp_path)
    p.land(_rows("n.md", "A", SOLO, ["one block of text"]))
    p.land(_rows("n.md", "A", SOLO, ["one block", "of text"]))         # same version, re-chunked
    reader = p.reader(MIRROR_READ)
    assert _texts(reader.rows()) == [("n.md", 0, "one block"), ("n.md", 1, "of text")]
    assert [(h["old_digest"], h["new_digest"]) for h in reader.history("n.md")] == [("", "A")]
    assert p.held_drift() == []


# ── strata ─────────────────────────────────────────────────────────────────────────────────────

def test_identical_turns_survive_each_at_its_own_stratum(tmp_path):
    """The defect delete-by-digest had: the owner says "ok", the model says "ok"; both must survive
    and the mirror must see only the owner's."""
    p = _plane(tmp_path)
    p.land(_rows("dialogue/c/t1", "same", DIALOGUE, ["ok, do it"]))
    p.land(_rows("dialogue/c/t2", "same", OBSERVED, ["ok, do it"]))
    assert len(p.atoms.ids()) == 1                                     # one atom, two holders
    assert [r["source_path"] for r in p.reader(MIRROR_READ).rows()] == ["dialogue/c/t1"]
    assert [r["source_path"] for r in p.reader(OBSERVED_READ).rows()] == ["dialogue/c/t2"]
    assert sorted(r["source_path"] for r in p.reader(DIALOGUE_READ).rows()) == [
        "dialogue/c/t1", "dialogue/c/t2"]
    hit = p.reader(MIRROR_READ).search(EMB.embed_query("ok, do it"), k=5)
    assert [[o.source_path for o in h.occupancies] for h in hit] == [["dialogue/c/t1"]]


def test_a_path_lives_at_exactly_one_stratum(tmp_path):
    p = _plane(tmp_path)
    p.land(_rows("n.md", "v1", SOLO, ["mine"]))
    with pytest.raises(StratumConflict):
        p.land(_rows("n.md", "v2", OBSERVED, ["not mine"]))
    with pytest.raises(StratumConflict):
        p.land(_rows("m.md", "v1", SOLO, ["a"]) + [
            {**_rows("m.md", "v1", OBSERVED, ["b"])[0], "chunk_index": 1}])


def test_code_rows_never_land_in_the_plane(tmp_path):
    with pytest.raises(PlaneError):
        _plane(tmp_path).land(_rows("core/x.py", "b1", Provenance.CODE, ["def f(): ..."]))


def test_relabel_moves_a_whole_class(tmp_path):
    p = _plane(tmp_path)
    p.land(_rows("n.md", "v1", DIALOGUE, ["words"]))
    assert p.relabel(DIALOGUE, SOLO) == 1
    assert p.class_of("n.md") is SOLO and p.reader(OBSERVED_READ).rows() == []
    assert p.held_drift() == []


# ── retire, purge ──────────────────────────────────────────────────────────────────────────────

def test_retire_keeps_history_and_leaves_the_current_view(tmp_path):
    p = _plane(tmp_path)
    p.land(_rows("n.md", "v1", SOLO, ["gone soon"]))
    assert p.retire("n.md") == 1 and p.retire("n.md") == 0
    reader = p.reader(MIRROR_READ)
    assert reader.rows() == [] and len(reader.rows(include_superseded=True)) == 1
    assert reader.search(EMB.embed_query("gone soon"), k=3) == []
    assert len(reader.search(EMB.embed_query("gone soon"), k=3, include_superseded=True)) == 1
    assert [(h["old_digest"], h["new_digest"]) for h in reader.history("n.md")][-1] == ("v1", "")


def test_purge_removes_the_digest_and_only_atoms_nothing_else_holds(tmp_path):
    p = _plane(tmp_path)
    p.land(_rows("private.md", "secret", SOLO, ["my private sentence", "a shared line"]))
    p.land(_rows("other.md", "kept", SOLO, ["a shared line"]))
    private, shared = atom_id("my private sentence"), atom_id("a shared line")
    assert {private, shared} <= p.atoms.ids()                          # precondition
    report = p.purge("secret")
    assert (report.occupancies_deleted, report.atoms_deleted) == (2, 1)
    assert report.supersessions_deleted == 1
    assert private not in p.atoms.ids() and shared in p.atoms.ids()
    assert not p.reader(MAINTENANCE_READ).has_digest("secret")
    assert _texts(p.reader(MIRROR_READ).rows()) == [("other.md", 0, "a shared line")]
    assert p.purge("secret") == type(report)()                         # idempotent, observably
    assert p.held_drift() == []


# ── vectors and geometry ───────────────────────────────────────────────────────────────────────

def test_new_atoms_need_vectors_and_known_atoms_do_not(tmp_path):
    p = _plane(tmp_path)
    with pytest.raises(MissingVector):
        p.land(_rows("n.md", "v1", SOLO, ["never embedded"], vectors=False))
    assert p.atoms.ids() == set() and p.reader(MAINTENANCE_READ).count() == 0
    p.land(_rows("a.md", "da", SOLO, ["embedded once"]))
    assert p.known([atom_id("embedded once"), atom_id("nope")]) == {atom_id("embedded once")}
    r = p.land(_rows("b.md", "db", SOLO, ["embedded once"], vectors=False))
    assert (r.atoms_inserted, r.atoms_reused) == (0, 1)


def test_a_different_embedder_cannot_land_or_search(tmp_path):
    p = _plane(tmp_path, Fingerprint("embeddinggemma-2", "title: none | text: {text}", 32))
    p.land(_rows("n.md", "v1", SOLO, ["words"]))
    other = SharedPlane(tmp_path / "plane", p.atoms,
                        fingerprint=Fingerprint("qwen3-embedding:4b", "{text}", 32))
    with pytest.raises(GeometryMismatch):
        other.land(_rows("m.md", "v1", SOLO, ["more"]))
    with pytest.raises(GeometryMismatch):
        other.reader(MIRROR_READ).search(EMB.embed_query("words"), k=1)
    p.reset()                                                          # a rebuild clears it
    other.land(_rows("m.md", "v1", SOLO, ["more"]))


# ── the boundary ───────────────────────────────────────────────────────────────────────────────

def test_a_corrupted_cache_cannot_widen_a_read_and_repair_restores_it(tmp_path):
    p = _plane(tmp_path)
    p.land(_rows("n.md", "v1", SOLO, ["the owner's note"]))
    p.land(_rows("dialogue/c/t9", "o1", OBSERVED, ["the model's reply about the note"]))
    reader = p.reader(MIRROR_READ)
    q = EMB.embed_query("the model's reply about the note")
    before = [(h.atom_id, [o.source_path for o in h.occupancies]) for h in reader.search(q, k=5)]
    everything = frozenset(c.value for c in PLANE_CLASSES)
    p.atoms.set_held({a: (everything, everything) for a in p.atoms.ids()})   # the worst cache
    assert p.held_drift()                                              # precondition: it IS wrong
    after = [(h.atom_id, [o.source_path for o in h.occupancies]) for h in reader.search(q, k=5)]
    assert after == before and all("t9" not in str(x) for x in after)
    assert p.repair().held_fixed == 2 and p.held_drift() == []


def test_a_reader_never_names_an_uncleared_relation(tmp_path):
    """Structural: trace every statement a mirror reader sends to SQLite; none may name the
    observed, curated or any other uncleared relation. Degenerate input: a reader that ran no SQL
    — so the trace must be non-empty."""
    p = _plane(tmp_path)
    p.land(_rows("n.md", "v1", SOLO, ["note text"]))
    p.land(_rows("dialogue/c/t1", "o1", OBSERVED, ["reply text"]))
    p.land(_rows("papers/x", "c1", CURATED, ["paper text"]))
    seen: list[str] = []
    conn: sqlite3.Connection = p._db()
    conn.set_trace_callback(seen.append)
    try:
        reader = p.reader(MIRROR_READ)
        reader.rows(include_superseded=True)
        reader.search(EMB.embed_query("reply text"), k=5, include_superseded=True)
        reader.history("dialogue/c/t1")
        reader.has_digest("o1")
        reader.count(include_superseded=True)
        reader.gauges()
        reader.rank_frequency()
    finally:
        conn.set_trace_callback(None)
    assert seen
    forbidden = [name for c in PLANE_CLASSES if not MIRROR_READ.admits(c)
                 for name in (OCC[c], SUP[c])]
    leaks = [sql for sql in seen if any(name in sql for name in forbidden)]
    assert leaks == []


def test_gauges_and_frequencies_count_only_what_the_clearance_sees(tmp_path):
    p = _plane(tmp_path)
    p.land(_rows("n.md", "v1", SOLO, ["shared", "solo only"]))
    p.land(_rows("p.md", "c1", CURATED, ["shared", "paper only"]))
    mirror = p.reader(MIRROR_READ)
    assert set(mirror.gauges()) == set(MIRROR_READ.classes)
    assert mirror.gauges()[SOLO].occupancies == 2
    assert mirror.rank_frequency() == [1, 1]                           # curated's holder unseen
    assert p.reader(MAINTENANCE_READ).rank_frequency() == [2, 1, 1]
    assert p.reader(CURATED_READ).has_digest("c1") and not mirror.has_digest("c1")


# ── crash points of a land (PLN-4; dn-ingest-door §9 item 7) ──────────────────────────────────

def _crash_then_share(p: SharedPlane, monkeypatch: pytest.MonkeyPatch) -> tuple[bool, bool]:
    """Land a note, then a new version that dies after its transaction and before its cache step,
    then an uncleared class's note sharing the new chunk. Returns (the new chunk is hidden from the
    cleared reader, the uncleared land changed what the cleared reader finds)."""
    p.land(_rows("n.md", "v1", SOLO, ["kept text"]))

    def dies(conn: sqlite3.Connection, ids: Any) -> int:
        raise RuntimeError("killed between the transaction and the cache step")
    with monkeypatch.context() as m:
        m.setattr(p, "_refresh_held", dies)
        with pytest.raises(RuntimeError):
            p.land(_rows("n.md", "v2", SOLO, ["kept text", "fresh text"]))
    query = EMB.embed_query("fresh text")

    def found() -> list[tuple[str, tuple[tuple[str, str, int], ...]]]:
        return [(h.atom_id, tuple((o.source_path, o.digest, o.chunk_index)
                                  for o in h.occupancies))
                for h in p.reader(MIRROR_READ).search(query, k=3)]
    before = found()
    p.land(_rows("x/o.md", "w1", OBSERVED, ["fresh text"]))     # outside the mirror's clearance
    return atom_id("fresh text") not in {a for a, _ in before}, found() != before


def test_a_land_that_dies_before_its_cache_step_hides_nothing_and_lets_nothing_in(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """PLN-4's crash points on the code (`search_after_crash`): the land writes its cache's
    additions before its transaction, so a crash between the transaction and the cache step leaves
    the new version visible to the cleared reader, and a later write of another class sharing the
    chunk changes nothing it finds. Degenerate input: a crash that leaves no new atom (an edit
    that reuses every chunk), so the new version adds `fresh text`, an atom of its own."""
    p = _plane(tmp_path)
    hidden, changed = _crash_then_share(p, monkeypatch)
    assert p.reader(MIRROR_READ).occupancies(source_path="n.md")[0].digest == "v2", \
        "PRECONDITION: the transaction landed before the crash"
    assert not hidden, "the landed version is not hidden"
    assert not changed, "an uncleared write changes no cleared search"


def test_with_the_cache_written_last_the_crash_hides_and_the_neighbour_reveals(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The control: the land as it was, its cache written only after the transaction
    (`_add_held` a no-op), fails both halves: the crash hides the new chunk from the cleared
    reader, and the uncleared land that shares it brings it back (`drift_interferes`)."""
    p = _plane(tmp_path)
    monkeypatch.setattr(p, "_add_held", lambda cached, gains: 0)
    hidden, changed = _crash_then_share(p, monkeypatch)
    assert hidden and changed


def test_a_refused_land_takes_back_its_cache_additions(tmp_path: Path) -> None:
    """A land refused inside its transaction (a stratum conflict) leaves its new atom dormant and
    the cache exact: the additions written before the transaction are taken back after the
    rollback (`land_of_landAdd_refused`)."""
    p = _plane(tmp_path)
    p.land(_rows("s.md", "v1", SOLO, ["solo text"]))
    with pytest.raises(StratumConflict):
        p.land(_rows("s.md", "v2", OBSERVED, ["observed text"]))
    assert atom_id("observed text") in p.atoms.ids(), "PRECONDITION: the atom was inserted"
    assert p.held_drift() == []


def _relabel_crash_then_rerun(p: SharedPlane, monkeypatch: pytest.MonkeyPatch) -> tuple[bool, bool]:
    """A curated note relabelled to observed, the relabel killed between its transaction and its
    cache step, then run again. Returns (the note's chunk is hidden from the observed reader after
    the crash, and after the re-run)."""
    p.land(_rows("c.md", "v1", CURATED, ["moved text"]))
    query = EMB.embed_query("moved text")

    def hidden() -> bool:
        return atom_id("moved text") not in {h.atom_id for h in
                                             p.reader(OBSERVED_READ).search(query, k=3)}
    assert hidden(), "PRECONDITION: the observed reader cannot see a curated note"

    def dies(conn: sqlite3.Connection, ids: Any) -> int:
        raise RuntimeError("killed between the transaction and the cache step")
    with monkeypatch.context() as m:
        m.setattr(p, "_refresh_held", dies)
        with pytest.raises(RuntimeError):
            p.relabel(CURATED, OBSERVED)
    assert p.class_of("c.md") is OBSERVED, "PRECONDITION: the transaction moved the note"
    after_crash = hidden()
    p.relabel(CURATED, OBSERVED)
    return after_crash, hidden()


def test_a_relabel_that_dies_before_its_cache_step_hides_nothing(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """PLN-4's relabel crash points on the code (`search_after_relabelCrash`): the new class is
    added to the moved atoms' cache before the transaction, so a crash between the transaction and
    the cache step leaves the moved note visible to the new class's reader."""
    hidden_after_crash, hidden_after_rerun = _relabel_crash_then_rerun(_plane(tmp_path),
                                                                       monkeypatch)
    assert not hidden_after_crash and not hidden_after_rerun


def test_with_the_cache_written_last_a_relabel_crash_hides_and_no_rerun_repairs(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The control: the relabel as it was, its cache written only after the transaction
    (`_add_held` a no-op), hides the moved note from the new class after the crash, and running the
    relabel again does not bring it back, the old relation being empty (`relabel_rerun_hides`)."""
    p = _plane(tmp_path)
    monkeypatch.setattr(p, "_add_held", lambda cached, gains: 0)
    hidden_after_crash, hidden_after_rerun = _relabel_crash_then_rerun(p, monkeypatch)
    assert hidden_after_crash and hidden_after_rerun


def test_a_refused_relabel_takes_back_its_cache_additions(tmp_path: Path) -> None:
    """A relabel refused inside its transaction (a path in both classes) leaves the cache exact:
    the additions written before the transaction are taken back after the rollback
    (`relabel_of_addRelabel_clash`)."""
    p = _plane(tmp_path)
    p.land(_rows("c.md", "v1", CURATED, ["only curated"]))
    p.land(_rows("o.md", "w1", OBSERVED, ["observed text"]))
    with sqlite3.connect(tmp_path / "plane" / "plane.sqlite") as raw:   # c.md in both classes
        raw.execute(f"INSERT INTO {OCC[OBSERVED]} SELECT 'c.md', 'x', chunk_index, atom_id, "
                    f"row_id, title, current, landed_at FROM {OCC[OBSERVED]}")
    p.repair()
    assert p.held_drift() == [], "PRECONDITION: the cache starts exact"
    only = atom_id("only curated")
    assert OBSERVED.value not in p.atoms.held([only])[only][1], \
        "PRECONDITION: the relabel's addition would change the curated atom's cache"
    with pytest.raises(StratumConflict):
        p.relabel(CURATED, OBSERVED)
    assert p.held_drift() == []
