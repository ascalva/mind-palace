"""Logseq parse, vault scoping, chunking, pipeline dedup, and the provenance firewall."""

from core.ingest.chunk import chunk_text
from core.ingest.logseq import iter_vault, parse_note
from core.ingest.pipeline import ingest_note, ingest_vault
from core.provenance import MIRROR_READABLE, Provenance
from core.stores.rawstore import RawStore


def _vault(tmp_path):
    v = tmp_path / "vault"
    (v / "logseq" / "bak").mkdir(parents=True)
    (v / "assets").mkdir()
    (v / "Daily.md").write_text(
        "type:: journal\n\nFelt #anxious today. See [[Coping]] and #[[deep work]].\n\nSecond block."
    )
    (v / "Coping.md").write_text("Breathing helps. Linked from [[Daily]].")
    (v / "logseq" / "bak" / "Daily.md").write_text("OLD BACKUP — must be excluded")
    (v / "assets" / "note.md").write_text("asset — must be excluded")
    return v


def test_iter_vault_excludes_housekeeping_dirs(tmp_path):
    v = _vault(tmp_path)
    assert {p.name for p in iter_vault(v)} == {"Daily.md", "Coping.md"}


def test_parse_extracts_explicit_layer(tmp_path):
    v = _vault(tmp_path)
    note = parse_note(v / "Daily.md", v)
    assert note.title == "Daily"
    assert {"anxious", "deep work"} <= note.tags
    assert "Coping" in note.links
    assert note.properties.get("type") == "journal"


def test_chunking_covers_text_with_indices():
    text = "\n\n".join(f"Block {i} " + "x" * 300 for i in range(5))
    chunks = chunk_text(text, max_chars=500, overlap_chars=50)
    assert len(chunks) > 1
    assert all(c.text for c in chunks)
    assert [c.index for c in chunks] == list(range(len(chunks)))


def test_pipeline_dedups_and_tags_authored(tmp_path):
    v = _vault(tmp_path)
    (v / "CopingCopy.md").write_text((v / "Coping.md").read_text())  # identical content
    raw = RawStore(tmp_path / "raw")
    records = ingest_vault(v, raw)
    by_title = {r.title: r for r in records}
    assert by_title["Daily"].provenance is Provenance.AUTHORED
    # identical content shares one raw object; exactly one of the two copies is is_new
    coping_digest = by_title["Coping"].digest
    assert by_title["CopingCopy"].digest == coping_digest
    assert sum(1 for r in records if r.digest == coping_digest and r.is_new) == 1


def test_ingest_handles_non_utf8(tmp_path):
    v = tmp_path / "vault"
    v.mkdir()
    p = v / "Smart.md"
    p.write_bytes(b"Smart quote: it\x92s fine. Caf\xe9.")  # cp1252 bytes, invalid UTF-8
    note = parse_note(p, v)
    assert "Caf" in note.text                 # decoded tolerantly for the derived layer
    assert note.raw_bytes == p.read_bytes()   # verbatim original bytes preserved (§8)
    rec = ingest_note(note, RawStore(tmp_path / "raw"))
    assert rec.chunks                          # ingests without raising


def test_mirror_firewall_is_authored_only():
    # design-notes/observed-data-and-the-assistant-tier.md — the mirror reads authored only.
    assert MIRROR_READABLE == frozenset({Provenance.AUTHORED})
    assert Provenance.OBSERVED not in MIRROR_READABLE
