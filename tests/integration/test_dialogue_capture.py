"""Dialogue capture → `authored-dialogue` (Track B / the capture loop).

Proves the owner's messages land in the corpus through the SAME pipeline as vault notes
(parametrized provenance), are mirror-readable (the owner's own words), retrievable on a later
search, idempotent on content, and attested.
"""

from core.attestation.attestor import StoreAttestor
from core.attestation.store import AttestationStore
from core.ingest.dialogue import DialogueCapture
from core.ingest.index import semantic_search
from core.provenance import MIRROR_READABLE, Provenance
from core.stores.catalog import VaultCatalog
from core.stores.rawstore import RawStore
from core.stores.vectorstore import VectorStore
from tests.fixtures.fakes import HashingEmbedder

DIM = 32


def _capture(tmp_path):
    att_store = AttestationStore(":memory:")
    cap = DialogueCapture(
        raw=RawStore(tmp_path / "raw"),
        store=VectorStore(tmp_path / "v.lance", dim=DIM),
        embedder=HashingEmbedder(DIM),
        catalog=VaultCatalog(tmp_path / "c.sqlite"),
        attestor=StoreAttestor(att_store),
    )
    return cap, att_store


def test_capture_lands_as_authored_dialogue(tmp_path):
    cap, att_store = _capture(tmp_path)
    digest = cap.capture("I felt anxious about the deadline today", conversation="c1")

    assert cap.raw.exists(digest)                                   # raw is kept (sacred)
    dialogue_rows = cap.store.all_rows(provenances={Provenance.AUTHORED_DIALOGUE})
    assert dialogue_rows and all(
        r["provenance"] == "authored-dialogue" for r in dialogue_rows
    )
    # It is mirror-readable (the owner's own words) — surfaces in a mirror-scoped scan.
    assert any(r["digest"] == digest for r in cap.store.all_rows(provenances=MIRROR_READABLE))
    # the catalog records it as authored-dialogue, under a dialogue/<conversation>/... path
    entries = cap.catalog.active_entries()
    assert entries and all(e.provenance == "authored-dialogue" for e in entries)
    assert entries[0].source_path.startswith("dialogue/c1/")
    # attested as a capture
    assert [a.action for a in att_store.all()] == ["capture"]
    assert digest in att_store.all()[0].input_hashes


def test_captured_dialogue_is_retrievable(tmp_path):
    cap, _ = _capture(tmp_path)
    cap.capture("my notes on distributed systems and consensus", conversation="c1")
    cap.capture("a grocery list: milk, eggs, bread", conversation="c1")
    hits = semantic_search("distributed consensus", cap.embedder, cap.store, k=1,
                           provenances=MIRROR_READABLE)
    assert hits and "consensus" in hits[0]["text"]                  # the right turn surfaces
    assert hits[0]["provenance"] == "authored-dialogue"


def test_capture_is_idempotent_on_content(tmp_path):
    cap, _ = _capture(tmp_path)
    d1 = cap.capture("exactly the same words", conversation="c1")
    rows_after_first = len(cap.store.all_rows(provenances={Provenance.AUTHORED_DIALOGUE}))
    d2 = cap.capture("exactly the same words", conversation="c1")
    assert d1 == d2                                                 # same content → same digest
    # delete-then-index keeps it at one set of vector rows (no duplicate ids)
    assert len(cap.store.all_rows(provenances={Provenance.AUTHORED_DIALOGUE})) == rows_after_first
