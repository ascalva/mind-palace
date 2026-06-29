"""The §1 provenance-spectrum split (Track B / B0) — an integrity-tier invariant.

The split turned the single `authored` class into `authored-solo` + `authored-dialogue` and
added `curated`. Because provenance IS the firewall (BUILD-SPEC §8), these properties are
integrity concerns, not mere unit behavior:

  * BOTH authored classes are mirror-readable; CURATED / OBSERVED / INTERPRETED are NOT —
    so the Ambassador's curated self-knowledge can never leak into a mirror-scoped answer;
  * a `MirrorView` cannot be constructed holding a curated row (unrepresentable, like observed);
  * the ingest pipeline is provenance-parametric (dialogue capture + curated ingest ride the
    SAME path as vault notes, not a bespoke writer);
  * the legacy→`authored-solo` relabel migration round-trips and is IDEMPOTENT (run twice = once).
"""

import pytest

from core.ingest.logseq import ParsedNote
from core.ingest.pipeline import ingest_note
from core.mirror import MirrorView, NonMirrorRowError
from core.provenance import MIRROR_READABLE, Provenance
from core.stores.catalog import VaultCatalog
from core.stores.rawstore import RawStore
from core.stores.vectorstore import VectorStore


def test_spectrum_values_round_trip():
    assert Provenance.AUTHORED_SOLO.value == "authored-solo"
    assert Provenance.AUTHORED_DIALOGUE.value == "authored-dialogue"
    assert Provenance.CURATED.value == "curated"
    # The strings survive an enum round-trip (what the stores persist).
    assert Provenance("authored-solo") is Provenance.AUTHORED_SOLO
    assert Provenance("authored-dialogue") is Provenance.AUTHORED_DIALOGUE
    assert Provenance("curated") is Provenance.CURATED


def test_mirror_readable_is_both_authored_classes_and_excludes_curated():
    assert MIRROR_READABLE == frozenset(
        {Provenance.AUTHORED_SOLO, Provenance.AUTHORED_DIALOGUE}
    )
    for p in (Provenance.CURATED, Provenance.OBSERVED, Provenance.INTERPRETED):
        assert p not in MIRROR_READABLE


class _FakeRowSource:
    def __init__(self, rows):
        self.rows = rows
        self.last_provenances = "unset"

    def all_rows(self, *, provenances=None):
        self.last_provenances = provenances
        if provenances is None:
            return list(self.rows)
        allowed = {str(p) for p in provenances}
        return [r for r in self.rows if r["provenance"] in allowed]


def test_mirror_view_keeps_both_authored_classes_drops_the_rest():
    src = _FakeRowSource([
        {"provenance": "authored-solo", "digest": "s"},
        {"provenance": "authored-dialogue", "digest": "d"},
        {"provenance": "curated", "digest": "c"},
        {"provenance": "observed", "digest": "o"},
        {"provenance": "interpreted", "digest": "i"},
    ])
    view = MirrorView.project(src)
    assert {r["provenance"] for r in view.rows()} == {"authored-solo", "authored-dialogue"}


def test_mirror_view_with_a_curated_row_is_unrepresentable():
    # The firewall, structural: curated is others' words — it can never seed the mirror.
    with pytest.raises(NonMirrorRowError):
        MirrorView(_rows=({"provenance": "curated", "digest": "c"},))
    # both authored classes construct fine
    assert len(MirrorView(_rows=(
        {"provenance": "authored-solo", "digest": "s"},
        {"provenance": "authored-dialogue", "digest": "d"},
    ))) == 2


def test_ingest_note_is_provenance_parametric(tmp_path):
    raw = RawStore(tmp_path / "raw")
    note = ParsedNote(source_path="x", title="t", text="hello world", tags=frozenset(),
                      links=frozenset(), properties={}, raw_bytes=b"hello world")
    assert ingest_note(note, raw).provenance is Provenance.AUTHORED_SOLO   # default
    assert ingest_note(note, raw, provenance=Provenance.AUTHORED_DIALOGUE).provenance \
        is Provenance.AUTHORED_DIALOGUE
    assert ingest_note(note, raw, provenance=Provenance.CURATED).provenance is Provenance.CURATED


def _row(digest, provenance):
    return {"id": f"{digest}:0", "digest": digest, "title": digest, "source_path": f"/{digest}",
            "chunk_index": 0, "provenance": provenance, "text": "t", "vector": [1.0, 0.0]}


def test_vectorstore_relabel_is_correct_and_idempotent(tmp_path):
    vs = VectorStore(tmp_path / "v.lance", dim=2)
    vs.add([_row("a", "authored"), _row("b", "authored"), _row("o", "observed")])

    changed = vs.relabel_provenance("authored", "authored-solo")
    assert changed == 2
    provs = sorted(r["provenance"] for r in vs.all_rows())
    assert provs == ["authored-solo", "authored-solo", "observed"]   # observed untouched
    # The relabeled rows are now mirror-readable under the new tag.
    assert len(vs.all_rows(provenances={Provenance.AUTHORED_SOLO})) == 2

    # Idempotent: a second run finds no legacy rows and changes nothing.
    assert vs.relabel_provenance("authored", "authored-solo") == 0
    assert sorted(r["provenance"] for r in vs.all_rows()) == provs


def test_catalog_relabel_is_correct_and_idempotent(tmp_path):
    cat = VaultCatalog(tmp_path / "c.sqlite")
    # Write legacy rows directly (simulating pre-split persistence).
    cat._conn.execute(  # noqa: SLF001
        "INSERT INTO vault_files (source_path, digest, title, provenance, active, updated_at)"
        " VALUES ('p1','d1','t1','authored',1,'t'), ('p2','d2','t2','authored',1,'t')"
    )
    cat._conn.commit()

    assert cat.relabel_provenance("authored", "authored-solo") == 2
    assert {e.provenance for e in cat.active_entries()} == {"authored-solo"}
    assert cat.relabel_provenance("authored", "authored-solo") == 0   # idempotent
    cat.close()
