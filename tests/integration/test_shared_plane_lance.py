"""The shared plane on real LanceDB, through the real writers (dn-vector-membership-store A3.9).

The unit and property tests drive the plane over an in-memory atom table; these drive it the way
the palace does — `DialogueCapture`, `VaultSync`, `purge_raw`, the `held` list columns and their
`array_has_any` prefilter on the LanceDB table — so each falsifier is checked where it can fail.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from core.ingest.dialogue import DialogueCapture
from core.ingest.embed import Embedder
from core.ingest.index import semantic_search
from core.ingest.purge import purge_raw
from core.ingest.sync import VaultSync
from core.kernel.clearance import DIALOGUE_READ, MAINTENANCE_READ, MIRROR_READ, OBSERVED_READ
from core.kernel.provenance import Provenance
from core.kernel.stores.rawstore import RawStore
from core.stores.catalog import VaultCatalog
from core.stores.plane import PLANE_CLASSES, atom_id
from core.stores.vectorstore import VectorStore
from tests.fixtures.fakes import HashingEmbedder

DIM = 32


class CountingEmbedder(HashingEmbedder):
    def __init__(self) -> None:
        super().__init__(DIM)
        self.embedded: list[str] = []

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        self.embedded.extend(texts)
        return super().embed_documents(texts)


def _stores(tmp_path: Path) -> tuple[VectorStore, RawStore, VaultCatalog, CountingEmbedder]:
    return (VectorStore(tmp_path / "v.lance", dim=DIM), RawStore(tmp_path / "raw"),
            VaultCatalog(tmp_path / "c.sqlite"), CountingEmbedder())


def _as_embedder(emb: CountingEmbedder) -> Embedder:
    return cast(Embedder, emb)          # the fake is structural; `Embedder` is nominal


def test_an_owner_turn_and_a_model_turn_with_the_same_words_both_survive(tmp_path: Path) -> None:
    """The defect delete-by-digest had, end to end: both turns survive at their own strata, one
    atom backs both, and the mirror sees the owner's turn and never the model's."""
    store, raw, catalog, emb = _stores(tmp_path)
    cap = DialogueCapture(raw=raw, store=store, embedder=_as_embedder(emb), catalog=catalog)
    cap.capture_turn("ok, do it", conversation="c", turn_id="t1", role="user")
    cap.capture_turn("ok, do it", conversation="c", turn_id="t2", role="assistant")
    assert emb.embedded == ["ok, do it"]                             # embedded once
    assert len(store.plane.atoms.ids()) == 1
    assert [r["source_path"] for r in store.all_rows(clearance=MIRROR_READ)] == [
        "dialogue/c/t1"]
    assert [r["source_path"] for r in store.all_rows(clearance=OBSERVED_READ)] == [
        "dialogue/c/t2"]
    assert sorted(r["source_path"] for r in store.all_rows(clearance=DIALOGUE_READ)) == [
        "dialogue/c/t1", "dialogue/c/t2"]
    hits = semantic_search("ok, do it", _as_embedder(emb), store, k=5)   # the mirror default
    assert [h["source_path"] for h in hits] == ["dialogue/c/t1"]


def test_a_note_edit_reuses_unchanged_chunks_and_records_its_supersession(tmp_path: Path) -> None:
    store, raw, catalog, emb = _stores(tmp_path)
    vault = tmp_path / "vault"
    vault.mkdir()
    sync = VaultSync(vault=vault, raw=raw, store=store, catalog=catalog, embedder=_as_embedder(emb))
    note = vault / "plan.md"
    first, second = "first block about atoms", "second block about the plane"
    note.write_text(f"{first}\n\n{second}")
    sync.rescan()
    assert sorted(emb.embedded) == sorted([f"{first}\n\n{second}"])  # one chunk at this size
    emb.embedded.clear()
    note.write_text(f"{first}\n\n{second}\n\n" + "a new paragraph " * 80)
    sync.rescan()
    rows = store.all_rows(clearance=MIRROR_READ)
    assert {r["source_path"] for r in rows} == {str(note)}           # the parser keys by path
    history = store.reader(MIRROR_READ).history(str(note))
    assert len(history) == 2 and history[1]["old_digest"] == history[0]["new_digest"]
    superseded = store.all_rows(clearance=MIRROR_READ, include_superseded=True)
    assert {r["digest"] for r in superseded} == {h["new_digest"] for h in history}
    assert store.plane.held_drift() == []


def test_purge_removes_private_text_from_the_lance_table(tmp_path: Path) -> None:
    store, raw, catalog, emb = _stores(tmp_path)
    vault = tmp_path / "vault"
    vault.mkdir()
    sync = VaultSync(vault=vault, raw=raw, store=store, catalog=catalog, embedder=_as_embedder(emb))
    (vault / "secret.md").write_text("my private sentence nobody else wrote")
    (vault / "other.md").write_text("an unrelated public line")
    sync.rescan()
    entry = catalog.get(str(vault / "secret.md"))
    assert entry is not None
    digest = entry.digest
    secret_atom = atom_id("my private sentence nobody else wrote")
    assert secret_atom in store.plane.atoms.ids()                   # precondition
    (vault / "secret.md").unlink()
    sync.rescan()                                                    # tombstone: retired, kept
    assert secret_atom in store.plane.atoms.ids()
    purge_raw(digest, raw=raw, store=store, catalog=catalog, confirm=True)
    assert secret_atom not in store.plane.atoms.ids()
    texts = [r["text"] for r in store.project(["text"], clearance=MAINTENANCE_READ)]
    assert "my private sentence nobody else wrote" not in texts
    assert [r["source_path"] for r in store.all_rows(clearance=MIRROR_READ)] == [
        str(vault / "other.md")]


def test_a_corrupted_held_cache_on_lance_cannot_widen_the_mirror(tmp_path: Path) -> None:
    store, raw, catalog, emb = _stores(tmp_path)
    cap = DialogueCapture(raw=raw, store=store, embedder=_as_embedder(emb), catalog=catalog)
    cap.capture_turn("the owner's own words", conversation="c", turn_id="t1", role="user")
    cap.capture_turn("the model's reply about words", conversation="c", turn_id="t2",
                     role="assistant")
    query = emb.embed_query("the model's reply about words")
    before = [r["id"] for r in store.search(query, k=5, clearance=MIRROR_READ)]
    everything = frozenset(c.value for c in PLANE_CLASSES)
    store.plane.atoms.set_held({a: (everything, everything) for a in store.plane.atoms.ids()})
    assert store.plane.held_drift()                                  # precondition: it is wrong
    after = [r["id"] for r in store.search(query, k=5, clearance=MIRROR_READ)]
    assert after == before and all("t2" not in rid for rid in after)
    store.plane.repair()
    assert store.plane.held_drift() == []


def test_two_stores_differing_only_outside_the_mirror_answer_the_mirror_alike(
        tmp_path: Path) -> None:
    """Noninterference on the real table: identical owner notes, plus model replies in one store
    only (sharing the owner's exact words) — every mirror read is the same."""
    readings: list[Any] = []
    for name, replies in (("a", []), ("b", ["shared exact words", "something else entirely"])):
        root = tmp_path / name
        store, raw, catalog, emb = _stores(root)
        cap = DialogueCapture(raw=raw, store=store, embedder=_as_embedder(emb), catalog=catalog)
        cap.capture_turn("shared exact words", conversation="c", turn_id="u1", role="user")
        cap.capture_turn("the owner thinks aloud", conversation="c", turn_id="u2", role="user")
        for i, text in enumerate(replies):
            cap.capture_turn(text, conversation="c", turn_id=f"m{i}", role="assistant")
        q = emb.embed_query("shared exact words")
        readings.append((
            sorted((r["id"], r["text"]) for r in store.all_rows(clearance=MIRROR_READ)),
            [(r["id"], round(float(r["_distance"]), 6))
             for r in store.search(q, k=5, clearance=MIRROR_READ)],
            store.reader(MIRROR_READ).count(), store.reader(MIRROR_READ).rank_frequency(),
        ))
    assert readings[0] == readings[1]
    assert Provenance.OBSERVED not in {Provenance(c) for c in MIRROR_READ.classes}
