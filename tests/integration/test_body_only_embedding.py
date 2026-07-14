"""Body-only embeddings — wiring + invariants (bp-036 Item 14; finding-0077).

`strip_properties` is applied in the ONE raw→chunks derivation (`derive_chunks`/`ingest_note`) so
the vector layer reflects note BODY only. These tests prove the change is SAFE end to end: (a) a
body-only chunk row still passes the retrieval-integrity check (`verify.py` re-derives via the same
stripping `derive_chunks` — no false drop, the load-bearing constraint); (b) the note digest and the
resolved `doc_id`/`id::` identity are unchanged (the strip touches only derived text); (c) links and
titles are unaffected. The empirical pre-vs-post mirror-graph A/B (real embedder) runs separately as
the acceptance MEASUREMENT; here a deterministic fake embedder asserts the invariants offline.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from core.ingest.logseq import parse_note, strip_properties
from core.ingest.sync import VaultSync
from core.ingest.verify import verify_rows_against_raw
from core.stores.catalog import VaultCatalog
from core.stores.rawstore import RawStore
from core.stores.vectorstore import VectorStore
from core.stores.versions import VersionStore
from tests.fixtures.embedding import DIM, FakeEmbedder

_NOTE = (
    "id:: 28f36d5a-727e-441f-b14e-4e9d740da27c\n"
    "date:: 2026-07-11\n"
    "This note is about designing a recursive, self-auditing system.\n"
    "It links to [[note-2026-07-11-000928]] and carries a #systems tag.\n"
)


def _sync(tmp_path: Path) -> VaultSync:
    vault = tmp_path / "vault"
    vault.mkdir()
    return VaultSync(
        vault=vault,
        raw=RawStore(tmp_path / "raw"),
        store=VectorStore(tmp_path / "v.lance", dim=DIM),
        catalog=VaultCatalog(tmp_path / "catalog.sqlite"),
        embedder=FakeEmbedder(),  # type: ignore[arg-type]  # test fixture duck-types Embedder
        version_store=VersionStore(tmp_path / "versions.sqlite"),
    )


def test_stored_chunks_are_body_only_and_pass_integrity(tmp_path: Path):
    # The load-bearing constraint: property lines gone from the vectors, AND every stored row still
    # verifies against raw via derive_chunks (which also strips) — no false drop.
    sync = _sync(tmp_path)
    note = sync.vault / "n.md"
    note.write_text(_NOTE, encoding="utf-8")
    sync.sync_path(note)

    rows = sync.store.all_rows()
    assert rows, "the note should have produced chunk rows"
    for r in rows:
        assert "id::" not in r["text"] and "date::" not in r["text"]   # metadata not in vectors
    # every body-only row re-derives from raw → verified, nothing dropped
    verified, dropped = verify_rows_against_raw(rows, sync.raw)
    assert dropped == []
    assert len(verified) == len(rows)


def test_digest_and_doc_id_unchanged_by_the_strip(tmp_path: Path):
    # The strip shapes only the DERIVED text: the digest is sha256(raw bytes) and identity resolves
    # from the parsed property, both independent of chunking. Identity + rename-stability untouched.
    sync = _sync(tmp_path)
    note = sync.vault / "n.md"
    note.write_text(_NOTE, encoding="utf-8")
    sync.sync_path(note)

    entry = sync.catalog.get(str(note))
    assert entry is not None
    assert entry.digest == hashlib.sha256(_NOTE.encode("utf-8")).hexdigest()   # sha256 of raw bytes
    assert sync.catalog.doc_id_for(str(note)) == "28f36d5a-727e-441f-b14e-4e9d740da27c"


def test_links_and_title_survive_the_strip(tmp_path: Path):
    # Links are parsed from the full text (not the stripped body), and the title comes from the path
    # — neither touches property lines, so a body-only embedding leaves referenceability intact.
    sync = _sync(tmp_path)
    note = sync.vault / "n.md"
    note.write_text(_NOTE, encoding="utf-8")
    parsed = parse_note(note, sync.vault)
    assert "note-2026-07-11-000928" in parsed.links
    assert parsed.title == "n"
    # the [[link]] lives in the BODY, so it survives into the embedded text too
    assert "[[note-2026-07-11-000928]]" in strip_properties(parsed.text)


def test_note_with_no_properties_is_unchanged_by_the_strip(tmp_path: Path):
    # A pure-prose note: the strip is a no-op, so its chunks match the un-stripped path exactly.
    sync = _sync(tmp_path)
    note = sync.vault / "p.md"
    note.write_text("Just prose, no properties, links to [[x]].\n", encoding="utf-8")
    sync.sync_path(note)
    rows = sync.store.all_rows()
    verified, dropped = verify_rows_against_raw(rows, sync.raw)
    assert dropped == [] and len(verified) == len(rows)
