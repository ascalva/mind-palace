"""The A3 migration (ops/plane_migrate.py): a pre-plane store moves onto the shared plane with every
row reconstituted bit for bit, the old directory archived (renamed, never deleted), and a writer
that slips in during the build refusing the swap rather than losing its row."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from core.kernel.clearance import CODE_READ, MAINTENANCE_READ, MIRROR_READ, OBSERVED_READ
from core.stores.vectorstore import TABLE, VectorStore
from core.typedshims.lancedb import connect
from ops import plane_migrate
from ops.plane_migrate import migrate

DIM = 4


def _legacy_schema() -> Any:
    import pyarrow as pa
    fields: list[tuple[str, pa.DataType]] = [
        ("id", pa.string()), ("digest", pa.string()), ("title", pa.string()),
        ("source_path", pa.string()), ("chunk_index", pa.int32()), ("provenance", pa.string()),
        ("text", pa.string()), ("layer", pa.string()), ("qualname", pa.string()),
        ("line_start", pa.int32()), ("line_end", pa.int32()), ("current", pa.bool_()),
        ("vector", pa.list_(pa.float32(), DIM)),
    ]
    return pa.schema(fields)


def _row(path: str, digest: str, idx: int, prov: str, text: str, vec: list[float],
         **extra: Any) -> dict[str, Any]:
    return {"id": f"{path}:{digest}:{idx}", "digest": digest, "title": path, "source_path": path,
            "chunk_index": idx, "provenance": prov, "text": text, "layer": "prose", "qualname": "",
            "line_start": 0, "line_end": 0, "current": True, "vector": vec, **extra}


LEGACY = [
    _row("notes/a.md", "da", 0, "authored-solo", "the shared opening", [1, 0, 0, 0]),
    _row("notes/a.md", "da", 1, "authored-solo", "only in a", [0.5, 0.5, 0, 0]),
    _row("notes/b.md", "db", 0, "authored-solo", "the shared opening", [1, 0, 0, 0]),
    _row("dialogue/c/t1", "same", 0, "authored-dialogue", "ok, do it", [0, 1, 0, 0]),
    _row("dialogue/c/t2", "same", 0, "observed", "ok, do it", [0, 1, 0, 0]),
    _row("papers/p", "v1", 0, "authored-solo", "first draft", [0, 0, 1, 0]),     # an old version
    _row("papers/p", "v2", 0, "authored-solo", "second draft", [0, 0, 0.5, 0.5]),  # its successor
    _row("legacy.md", "dl", 0, "authored", "a retired label", [0.2, 0.2, 0.2, 0.2]),
    {**_row("", "", 0, "code", "def f(): ...", [0, 0, 0, 1]), "id": "code_ast:abc",
     "layer": "code_ast"},
    {**_row("core/x.py", "b1", 0, "code", "def g(): ...", [0.1, 0, 0, 1]), "layer": "code_text"},
]


def _legacy_store(path: Path) -> None:
    db = connect(str(path))
    db.create_table(TABLE, schema=_legacy_schema()).add(LEGACY)


def test_a_pre_plane_store_moves_onto_the_plane_bit_for_bit(tmp_path: Path) -> None:
    store = tmp_path / "data" / "vectors.lance"
    _legacy_store(store)
    assert not VectorStore(store, dim=DIM).plane_enabled()              # precondition
    report = migrate(store, dim=DIM, fingerprint=None, archive_root=tmp_path / "archive")
    assert report.verified and report.swapped, str(report)
    # 3 physical rows (two code, one under the retired 'authored' label); 7 prose rows in 5 docs
    assert (report.code_rows, report.prose_rows, report.documents) == (3, 7, 5)
    assert report.multi_version_paths == ["papers/p"]

    vs = VectorStore(store, dim=DIM)
    assert vs.plane_enabled()
    # sharing happened: 7 prose rows, 5 distinct texts → 5 atoms
    assert report.atoms == 5 == len(vs.plane.atoms.ids())
    # every legacy prose row reconstitutes (current view drops only the superseded draft)
    mirror = {r["id"]: r for r in vs.all_rows(clearance=MIRROR_READ)}
    assert set(mirror) == {"notes/a.md:da:0", "notes/a.md:da:1", "notes/b.md:db:0",
                           "dialogue/c/t1:same:0", "papers/p:v2:0"}
    assert mirror["notes/b.md:db:0"]["vector"] == [1.0, 0.0, 0.0, 0.0]
    assert [r["id"] for r in vs.all_rows(clearance=OBSERVED_READ)] == ["dialogue/c/t2:same:0"]
    history = vs.reader(MIRROR_READ).history("papers/p")
    assert [(h["old_digest"], h["new_digest"]) for h in history] == [("", "v1"), ("v1", "v2")]
    # code and the retired label stayed physical, verbatim
    assert {r["id"] for r in vs.all_rows(clearance=CODE_READ)} == {"code_ast:abc",
                                                                   "core/x.py:b1:0"}
    raw = vs.project(["id", "provenance"], clearance=MAINTENANCE_READ,
                     where="provenance = 'authored'")
    assert [r["id"] for r in raw] == ["legacy.md:dl:0"]
    # the old directory is archived, intact, and still a readable pre-plane store
    archived = Path(report.archive)
    assert archived.parent == tmp_path / "archive"
    assert archived.name.startswith("vectors.lance-pre-a3")
    old = VectorStore(archived, dim=DIM)
    assert not old.plane_enabled() and old.count() == len(LEGACY)
    # idempotent
    assert migrate(store, dim=DIM, fingerprint=None,
                   archive_root=tmp_path / "archive").already_on_plane


def test_a_dry_run_swaps_nothing(tmp_path: Path) -> None:
    store = tmp_path / "vectors.lance"
    _legacy_store(store)
    report = migrate(store, dim=DIM, fingerprint=None, archive_root=tmp_path / "archive",
                     dry_run=True)
    assert report.verified and not report.swapped
    assert not VectorStore(store, dim=DIM).plane_enabled()
    assert Path(report.build).exists() and not (tmp_path / "archive").exists()


def test_a_writer_during_the_build_refuses_the_swap(tmp_path: Path,
                                                    monkeypatch: pytest.MonkeyPatch) -> None:
    store = tmp_path / "vectors.lance"
    _legacy_store(store)
    real = VectorStore.compact

    def compact_and_write(self: VectorStore, **kw: Any) -> Any:
        out = real(self, **kw)
        connect(str(store)).open_table(TABLE).add(
            [_row("notes/late.md", "dz", 0, "authored-solo", "arrived mid-build", [0, 0, 0, 1])])
        return out

    monkeypatch.setattr(VectorStore, "compact", compact_and_write)
    report = migrate(store, dim=DIM, fingerprint=None, archive_root=tmp_path / "archive")
    assert report.refused and not report.swapped
    assert not VectorStore(store, dim=DIM).plane_enabled()            # the live store untouched
    assert VectorStore(store, dim=DIM).count() == len(LEGACY) + 1     # and its new row kept


def test_the_cli_names_its_stores() -> None:
    assert plane_migrate.ARCHIVE_ROOT.name == "mind-palace-archive"


def _two_copies(store: Path, second: list[float]) -> None:
    db = connect(str(store))
    db.create_table(TABLE, schema=_legacy_schema()).add([
        _row("papers/a", "da", 0, "curated", "the same passage", [1.0, 0.0, 0.0, 0.0]),
        _row("papers/b", "db", 0, "curated", "the same passage", second),
    ])


def test_a_shared_text_within_embedder_jitter_gets_one_representative(tmp_path: Path) -> None:
    """Two papers quoting one passage, embedded in different batches: their copies differ in the
    last bits (measured live: cosine >= 0.9999984). The plane keeps ONE vector; the migration
    accepts that, counts it, and reports the worst deviation."""
    store = tmp_path / "curated.lance"
    _two_copies(store, [1.0, 1e-4, 0.0, 0.0])                       # cosine ≈ 1 - 5e-9
    report = migrate(store, dim=DIM, fingerprint=None, archive_root=tmp_path / "archive")
    assert report.verified and report.swapped, str(report)
    assert report.representatives == 1 and report.atoms == 1
    assert report.worst_representative_cos > plane_migrate.REPRESENTATIVE_COS


def test_a_shared_text_with_genuinely_different_vectors_refuses_the_swap(tmp_path: Path) -> None:
    """Same text, vectors that disagree beyond jitter: something other than nondeterminism made
    them (a different embedder, a corrupted row). Never paper over it — no swap."""
    store = tmp_path / "curated.lance"
    _two_copies(store, [0.6, 0.8, 0.0, 0.0])                        # cosine 0.6
    report = migrate(store, dim=DIM, fingerprint=None, archive_root=tmp_path / "archive")
    assert report.mismatches and not report.swapped
    assert not VectorStore(store, dim=DIM).plane_enabled()
