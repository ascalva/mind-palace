"""The landing order (dn-ingest-door D1, D5; DOR-7 `ingest_prefix_converges`, DOR-2
`ingest_idempotent`), at the code's grain: the catalog's digest is the last write, so a run that
dies after the version row and the attestation but before the key is repeated in full by the
next run and lands exactly once; the curated lane has a key now and lands nothing twice."""

from __future__ import annotations

from pathlib import Path
from typing import cast

import pytest

from core.attestation.attestor import StoreAttestor
from core.attestation.store import AttestationStore
from core.ingest.curated import ingest_curated
from core.ingest.dialogue import DialogueCapture
from core.ingest.embed import Embedder
from core.ingest.sync import SyncOutcome, VaultSync
from core.kernel.stores.rawstore import RawStore
from core.stores.catalog import VaultCatalog
from core.stores.vectorstore import VectorStore
from core.stores.versions import VersionStore
from tests.fixtures.embedding import DIM, FakeEmbedder


class _Crash(RuntimeError):
    pass


def _embedder() -> Embedder:
    return cast(Embedder, FakeEmbedder())


def _stores(tmp_path: Path) -> tuple[RawStore, VectorStore, VaultCatalog, AttestationStore]:
    return (RawStore(tmp_path / "raw"), VectorStore(tmp_path / "vectors", dim=DIM),
            VaultCatalog(tmp_path / "catalog.sqlite"), AttestationStore(tmp_path / "att.sqlite"))


def _crash_once(monkeypatch: pytest.MonkeyPatch, catalog: VaultCatalog) -> None:
    """The next `catalog.record` dies, as a crash between the attestation and the key would."""
    real = catalog.record
    state = {"armed": True}

    def record(*args, **kwargs):
        if state["armed"]:
            state["armed"] = False
            raise _Crash("died before the key")
        return real(*args, **kwargs)

    monkeypatch.setattr(catalog, "record", record)


def test_a_vault_run_that_dies_before_the_key_is_repeated_and_lands_once(tmp_path, monkeypatch):
    raw, store, catalog, att_store = _stores(tmp_path)
    versions = VersionStore(tmp_path / "versions.sqlite")
    vault = tmp_path / "vault"
    vault.mkdir()
    sync = VaultSync(vault=vault, raw=raw, store=store, catalog=catalog, embedder=_embedder(),
                     attestor=StoreAttestor(att_store), version_store=versions)
    note = vault / "a.md"
    note.write_text("# A\n\nthe first version\n", encoding="utf-8")
    _crash_once(monkeypatch, catalog)
    with pytest.raises(_Crash):
        sync.sync_path(note)
    # the prefix: landed, the version row and the attestation written, no key
    src = str(note)
    assert [v.version_seq for v in versions.history(src)] == [1]
    assert att_store.count() == 1
    assert catalog.get(src) is None
    # the next run repeats the run in full and lands exactly the uninterrupted run's state
    assert sync.sync_path(note) is SyncOutcome.INDEXED
    assert [v.version_seq for v in versions.history(src)] == [1]      # appended only when new
    assert att_store.count() == 1                                      # attested once per digest
    entry = catalog.get(src)
    assert entry is not None and entry.active
    # and the key makes the third run a no-op
    assert sync.sync_path(note) is SyncOutcome.UNCHANGED
    # an amendment is still a new version, and a revert still a third one (the chain stays linear)
    note.write_text("# A\n\nthe second version\n", encoding="utf-8")
    assert sync.sync_path(note) is SyncOutcome.INDEXED
    note.write_text("# A\n\nthe first version\n", encoding="utf-8")
    assert sync.sync_path(note) is SyncOutcome.INDEXED
    assert [v.version_seq for v in versions.history(src)] == [1, 2, 3]
    # the revert appended a version: an event of its own, attested again though its bytes were
    # attested before (the review of 2026-11-05: reverts had stopped reaching the ops feed)
    assert att_store.count() == 3


def test_a_capture_that_dies_before_the_key_is_repeated_and_attests_once(tmp_path, monkeypatch):
    raw, store, catalog, att_store = _stores(tmp_path)
    cap = DialogueCapture(raw=raw, store=store, embedder=_embedder(), catalog=catalog,
                          attestor=StoreAttestor(att_store))
    _crash_once(monkeypatch, catalog)
    with pytest.raises(_Crash):
        cap.capture_turn("a turn", conversation="c", turn_id="7", role="assistant")
    assert att_store.count() == 1 and catalog.get("dialogue/c/7") is None
    digest, created = cap.capture_turn("a turn", conversation="c", turn_id="7", role="assistant")
    assert created and att_store.count() == 1
    entry = catalog.get("dialogue/c/7")
    assert entry is not None and entry.digest == digest
    assert cap.capture_turn("a turn", conversation="c", turn_id="7", role="assistant") == (
        digest, False)


def test_the_curated_lane_has_a_key_and_lands_nothing_twice(tmp_path):
    raw, store, catalog, att_store = _stores(tmp_path)
    root = tmp_path / "repo"
    (root / "docs").mkdir(parents=True)
    (root / "docs" / "a.md").write_text("# A\n\nalpha\n", encoding="utf-8")
    (root / "docs" / "b.md").write_text("# B\n\nbeta\n", encoding="utf-8")
    paths = [root / "docs" / "a.md", root / "docs" / "b.md"]
    first = ingest_curated(paths, raw, store, _embedder(), catalog, repo_root=root,
                           attestor=StoreAttestor(att_store))
    assert (first.ingested, first.unchanged) == (2, 0) and att_store.count() == 2
    second = ingest_curated(paths, raw, store, _embedder(), catalog, repo_root=root,
                            attestor=StoreAttestor(att_store))
    assert (second.ingested, second.unchanged) == (0, 2) and att_store.count() == 2
    (root / "docs" / "a.md").write_text("# A\n\nalpha, amended\n", encoding="utf-8")
    third = ingest_curated(paths, raw, store, _embedder(), catalog, repo_root=root,
                           attestor=StoreAttestor(att_store))
    assert (third.ingested, third.unchanged) == (1, 1) and att_store.count() == 3


def test_the_curated_lane_lands_again_after_a_plane_reset(tmp_path):
    """The third review's finding 2: `palace reembed --confirm` resets the plane and re-embeds
    only the vault and the dialogue, so the catalog's key alone would call every doc unchanged
    and the documented repair (re-run the curated ingest) would land nothing. The key also asks
    the plane, so the re-run lands the doc, and attests nothing new."""
    raw, store, catalog, att_store = _stores(tmp_path)
    root = tmp_path / "repo"
    (root / "docs").mkdir(parents=True)
    (root / "docs" / "a.md").write_text("# A\n\nalpha\n", encoding="utf-8")
    paths = [root / "docs" / "a.md"]
    first = ingest_curated(paths, raw, store, _embedder(), catalog, repo_root=root,
                           attestor=StoreAttestor(att_store))
    assert first.ingested == 1 and att_store.count() == 1
    store.reset()                                       # what reembed --confirm does first
    again = ingest_curated(paths, raw, store, _embedder(), catalog, repo_root=root,
                           attestor=StoreAttestor(att_store))
    assert (again.ingested, again.unchanged) == (1, 0) and again.chunks > 0
    assert att_store.count() == 1
    steady = ingest_curated(paths, raw, store, _embedder(), catalog, repo_root=root,
                            attestor=StoreAttestor(att_store))
    assert (steady.ingested, steady.unchanged) == (0, 1)


def test_a_receipt_names_exactly_the_attestations_of_what_landed(tmp_path):
    """DOR-6 at the code's grain (the note's §6 falsifier "the receipt over-claiming"): two notes
    and a capture land through the door's `perform` on real stores; each landing names its
    attestations, records whose outputs are exactly the digest it landed, no landing names
    another's, and a re-landing lands nothing and attests nothing twice."""
    from tests.fixtures.door import palace_at, write_file

    p = palace_at(tmp_path)
    write_file(p.vault, "pages/a.md", "# A\n\nthe first note\n")
    write_file(p.vault, "pages/b.md", "# B\n\nthe second note\n")
    receipts = [p.run('do ingest_note(path: "pages/a.md")'),
                p.run('do ingest_note(path: "pages/b.md")'),
                p.run('do capture(text: "remember this", conversation: "tea")', "ambassador")]
    named: list[str] = []
    for r in receipts:
        (landed,) = r["changed"]
        assert landed["status"] == "landed" and len(landed["attestations"]) == 1
        att = p.att.get(landed["attestations"][0])
        assert att is not None and set(att.output_hashes) == {landed["digest"]}
        named += landed["attestations"]
    assert len(set(named)) == 3 and p.att.count() == 3
    again = p.run('do ingest_note(path: "pages/a.md")')
    assert again["effects"] == {"unchanged": 1} and again["changed"] == []
    assert p.att.count() == 3


def _vault_sync(tmp_path: Path) -> tuple[VaultSync, VersionStore, Path]:
    raw, store, catalog, att_store = _stores(tmp_path)
    versions = VersionStore(tmp_path / "versions.sqlite")
    vault = tmp_path / "vault"
    (vault / "pages").mkdir(parents=True)
    sync = VaultSync(vault=vault, raw=raw, store=store, catalog=catalog, embedder=_embedder(),
                     attestor=StoreAttestor(att_store), version_store=versions)
    return sync, versions, vault


def test_one_note_renamed_before_it_is_ingested_alone_keeps_its_identity(tmp_path):
    """The door's `ingest note` lands one path: a note renamed just before (the watcher's rescan
    not yet run) adopts the vanished path's identity, as the rescan would, so its version chain
    continues instead of forking."""
    sync, versions, vault = _vault_sync(tmp_path)
    old = vault / "pages" / "a.md"
    old.write_text("# A\n\nthe same bytes\n", encoding="utf-8")
    assert sync.sync_one(old) is SyncOutcome.INDEXED
    new = vault / "pages" / "renamed.md"
    old.rename(new)
    assert sync.sync_one(new) is SyncOutcome.INDEXED
    assert sync.catalog.doc_id_for(str(new)) == sync.catalog.doc_id_for(str(old)) == str(old)
    assert [v.version_seq for v in versions.history(str(old))] == [1, 2]   # a rename is an event


def test_an_empty_id_property_keeps_one_chain(tmp_path):
    """`id::` present but empty is an identity of its own (the empty string), for every version,
    as the catalog records it: the chain does not split between the path and the empty id."""
    sync, versions, vault = _vault_sync(tmp_path)
    note = vault / "pages" / "e.md"
    note.write_text("id:: \n# E\n\nfirst\n", encoding="utf-8")
    sync.sync_one(note)
    note.write_text("id:: \n# E\n\nsecond\n", encoding="utf-8")
    sync.sync_one(note)
    doc_id = sync.catalog.doc_id_for(str(note))
    assert [v.version_seq for v in versions.history(doc_id)] == [1, 2]


def test_a_path_in_another_case_or_an_excluded_dir_in_any_case_is_out_of_scope(tmp_path):
    from core.ingest.sync import in_vault_scope

    vault = tmp_path / "vault"
    (vault / "pages").mkdir(parents=True)
    (vault / ".recycle").mkdir()
    (vault / "pages" / "a.md").write_text("- a\n")
    (vault / ".recycle" / "x.md").write_text("- x\n")
    assert in_vault_scope(vault, vault / "pages" / "a.md")
    for spelled in (vault / "PAGES" / "a.md", vault / "pages" / "A.md",
                    vault / ".RECYCLE" / "x.md", vault / ".recycle" / "x.md"):
        assert not in_vault_scope(vault, spelled), spelled
