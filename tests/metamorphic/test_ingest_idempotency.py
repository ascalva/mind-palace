"""Metamorphic: re-ingesting identical content changes nothing (holistic-testing.md §1b).

No ground truth needed — the property is a *relationship* between two ingests of the same
note: same content digest, stored exactly once (content-addressing), second pass not-new.
"""

from __future__ import annotations

from core.ingest.logseq import parse_note
from core.ingest.pipeline import ingest_note
from tests.fixtures.corpus import write_vault
from tests.fixtures.stores import raw_store


def test_same_note_ingested_twice_is_one_raw_object(tmp_path):
    vault = write_vault(tmp_path / "vault", {"Note.md": "A thought worth keeping. [[Link]] #tag"})
    note = parse_note(vault / "Note.md", vault)
    raw = raw_store(tmp_path)

    first = ingest_note(note, raw)
    second = ingest_note(note, raw)

    assert first.digest == second.digest                    # identical content -> identical address
    assert first.is_new is True and second.is_new is False  # stored once, not twice
    assert raw.get(first.digest) == note.raw_bytes          # verbatim bytes round-trip (§8)


def test_digest_is_independent_of_ingest_count(tmp_path):
    vault = write_vault(tmp_path / "vault", {"N.md": "stable content"})
    note = parse_note(vault / "N.md", vault)
    raw = raw_store(tmp_path)
    digests = {ingest_note(note, raw).digest for _ in range(5)}
    assert len(digests) == 1                                # the address never drifts on re-ingest
