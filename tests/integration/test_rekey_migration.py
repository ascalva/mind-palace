"""The chunk-key migration, `rekey_store` (build plan Item 1c; PLN-6, issue #37).

The migration moves note rows from the old `{digest}:{chunk_index}` id to the doc-scoped
`(source_path, chunk_hash)` and must move nothing else. PLN-6 (`formal/Palace/Plane.lean`,
`rekey_keeps`) states what that means: the plane's state is unchanged up to its row ids (every
occupancy, superseded ones included, every supersession edge, every atom and its cached `held`
entry), every row outside the note lane is unchanged (the shed code atoms the membership relation
names, the code records), and every note row ends under its key. The falsifier checks exactly
that on a store with history and both lanes; the control runs the migration as it was written
(`all_rows()`, `reset()`, add back) on the same store and must break it. Deterministic; no model,
no network.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pyarrow as pa
import pytest

from core.ingest import index as index_mod
from core.ingest.index import rekey_preview, rekey_store
from core.kernel.clearance import MAINTENANCE_READ
from core.kernel.ingest.amend import chunk_point_id
from core.kernel.ingest.chunk import Chunk
from core.stores import vectorstore as vs_mod
from core.stores.plane import PLANE_CLASSES
from core.stores.vectorstore import ATOM_ROW_SHED, TABLE, VectorStore
from core.typedshims.lancedb import connect

DIM = 2


def _note(digest: str, idx: int, path: str, text: str, vector: list[float],
          prov: str = "authored-solo") -> dict[str, Any]:
    """A note row under the OLD `{digest}:{chunk_index}` key."""
    return {"id": f"{digest}:{idx}", "digest": digest, "title": path, "source_path": path,
            "chunk_index": idx, "provenance": prov, "text": text, "vector": vector}


def _code_atom(layer: str, text: str, vector: list[float]) -> dict[str, Any]:
    """A shed CODE atom row (D1): no document, its occupancies in the membership relation."""
    return {**ATOM_ROW_SHED, "id": f"{layer}:{len(text):04x}", "title": "",
            "provenance": "code", "text": text, "layer": layer, "current": True,
            "vector": vector}


def _code_record(path: str, layer: str, text: str, vector: list[float]) -> dict[str, Any]:
    """A code row of the per-version model before D1: a document, a blob, a layer of its own."""
    return {"id": f"{path}:{layer}:0", "digest": "blob1", "title": path, "source_path": path,
            "chunk_index": 0, "provenance": "code", "text": text, "layer": layer,
            "qualname": "", "line_start": 1, "line_end": 1, "current": False, "vector": vector}


def _store(tmp_path: Path) -> VectorStore:
    """A plane store holding everything the old migration lost: a note edited once (a superseded
    version, two edges), a note of another class sharing a chunk, two shed code atoms of one text
    (two layers' readings) and two code records of one document with one text (two layers)."""
    store = VectorStore(tmp_path / "v.lance", dim=DIM)
    store.add([_note("v1", 0, "a.md", "hello", [0.1, 0.2]),
               _note("v1", 1, "a.md", "world", [0.3, 0.4])])
    store.add([_note("v2", 0, "a.md", "hello", [0.1, 0.2]),
               _note("v2", 1, "a.md", "again", [0.5, 0.6])])
    store.add([_note("w1", 0, "b.md", "hello", [0.1, 0.2], prov="observed")])
    store.add([_code_atom("code_ast", "def f(): ...", [0.7, 0.1]),
               _code_atom("code_text", "def f(): ...", [0.7, 0.1])])
    store.add([_code_record("core/x.py", "code_ast", "def g(): ...", [0.2, 0.9]),
               _code_record("core/x.py", "code_text", "def g(): ...", [0.2, 0.9])])
    return store


def _canon(row: dict[str, Any]) -> tuple[tuple[str, str], ...]:
    return tuple(sorted((k, str(v)) for k, v in row.items()))


def _observe(store: VectorStore) -> dict[str, Any]:
    """What PLN-6 says a re-key keeps: the plane's state up to row ids, and every physical row
    outside the note lane, bit for bit."""
    reader = store.reader(MAINTENANCE_READ)
    occ = sorted((o.provenance.value, o.source_path, o.digest, o.chunk_index, o.atom_id,
                  o.current, o.title) for o in reader.occupancies(include_superseded=True))
    paths = sorted({o[1] for o in occ})
    atoms = sorted(store.plane.atoms.ids())
    plane_values = {p.value for p in PLANE_CLASSES}
    outside = [r for page in store.physical_pages(clearance=MAINTENANCE_READ) for r in page
               if not (r["provenance"] in plane_values and r["source_path"])]
    return {
        "occupancies": occ,
        "history": {p: [(h["old_digest"], h["new_digest"]) for h in reader.history(p)]
                    for p in paths},
        "atoms": {a: store.plane.atoms.held([a]).get(a) for a in atoms},
        "outside": sorted(_canon(r) for r in outside),
    }


def _under_their_keys(store: VectorStore) -> bool:
    """Every note row carries `chunk_point_id(source_path, chunk)`, computed from its own text."""
    texts = {a: t for a, (t, _) in store.plane.atoms.payload(
        sorted(store.plane.atoms.ids())).items()}
    plane_ok = all(
        o.row_id == chunk_point_id(o.source_path, Chunk(o.chunk_index, texts[o.atom_id]))
        for o in store.reader(MAINTENANCE_READ).occupancies(include_superseded=True))
    records = store.note_records(["id", "source_path", "chunk_index", "text"])
    return plane_ok and all(
        r["id"] == chunk_point_id(r["source_path"], Chunk(r["chunk_index"], r["text"]))
        for r in records)


def _law(before: dict[str, Any], after: dict[str, Any], store: VectorStore) -> bool:
    return before == after and _under_their_keys(store)


def _code(obs: dict[str, Any], path: str) -> int:
    """How many physical CODE rows of `path` ('' for the shed atoms) the observation holds."""
    return sum(1 for r in obs["outside"]
               if ("provenance", "code") in r and ("source_path", path) in r)


def test_the_rekey_moves_only_note_ids_and_keeps_everything_else(tmp_path: Path) -> None:
    """PLN-6 on the code. Degenerate input: a store with no history, no code row and no old id,
    where a reset and re-add keeps everything too. Each is asserted present first."""
    store = _store(tmp_path)
    before = _observe(store)
    assert len(before["history"]["a.md"]) == 2, "PRECONDITION: a.md was edited once"
    assert any(not o[5] for o in before["occupancies"]), "...so a superseded occupancy exists"
    assert _code(before, "") == 2, "...two shed code atoms"
    assert _code(before, "core/x.py") == 2, "...and two code records"
    rows, changing = rekey_preview(store)
    assert (rows, changing) == (5, 5), "every note occupancy carries an old-scheme id"

    assert rekey_store(store) == (rows, changing)
    assert _law(before, _observe(store), store)

    # idempotent: nothing is left to change, and a second run changes nothing
    assert rekey_preview(store) == (rows, 0)
    assert rekey_store(store) == (rows, 0)
    assert _law(before, _observe(store), store)


def _rekey_unscoped(store: VectorStore) -> None:
    """`rekey_store` as it was written: an unscoped read, a full reset, and an add."""
    rows = [dict(r) for r in store.all_rows(clearance=MAINTENANCE_READ)]
    by_new_id: dict[str, dict[str, Any]] = {}
    for r in rows:
        r["id"] = index_mod._row_new_id(r)
        by_new_id[r["id"]] = r
    store.reset()
    store.add(list(by_new_id.values()))


def test_the_unscoped_rekey_breaks_the_law(tmp_path: Path) -> None:
    """The control: the migration as it was, on the same store, fails the falsifier above, in
    each of the ways the model's witnesses name (issue #37)."""
    store = _store(tmp_path)
    before = _observe(store)
    _rekey_unscoped(store)
    after = _observe(store)
    assert not _law(before, after, store)
    assert _code(after, "") == 0, "the shed code atoms are gone"
    assert _code(after, "core/x.py") == 1, "two layers' code records merged under the note key"
    assert all(o[5] for o in after["occupancies"]), "the superseded version is gone"
    assert after["history"]["a.md"] == [("", "v2")], "...and the edge that superseded it"


def test_shared_text_keeps_its_rows_and_its_one_atom(tmp_path: Path) -> None:
    """§3 and §7 on the plane: a chunk repeated in one note is one atom and two occupancies, and
    stays both; two notes sharing a chunk keep two rows under two keys."""
    store = VectorStore(tmp_path / "v.lance", dim=DIM)
    store.add([_note("d1", 0, "a.md", "same", [0.1, 0.2]),
               _note("d1", 1, "a.md", "same", [0.1, 0.2]),
               _note("d2", 0, "b.md", "same", [0.1, 0.2])])
    assert len(store.plane.atoms.ids()) == 1                 # PRECONDITION: one shared atom
    assert rekey_store(store) == (3, 3)
    occ = store.reader(MAINTENANCE_READ).occupancies(include_superseded=True)
    assert sorted((o.source_path, o.chunk_index) for o in occ) == [("a.md", 0), ("a.md", 1),
                                                                  ("b.md", 0)]
    assert {o.row_id for o in occ} == {chunk_point_id("a.md", Chunk(0, "same")),
                                       chunk_point_id("b.md", Chunk(0, "same"))}
    assert len(store.plane.atoms.ids()) == 1


def _legacy_table(path: Path, rows: list[dict[str, Any]]) -> None:
    """A table that predates the plane: no `held` columns, every note row physical."""
    fields: list[tuple[str, pa.DataType]] = [
        ("id", pa.string()), ("digest", pa.string()), ("title", pa.string()),
        ("source_path", pa.string()), ("chunk_index", pa.int32()), ("provenance", pa.string()),
        ("text", pa.string()), ("layer", pa.string()), ("qualname", pa.string()),
        ("line_start", pa.int32()), ("line_end", pa.int32()), ("current", pa.bool_()),
        ("vector", pa.list_(pa.float32(), DIM)),
    ]
    filled = [{"layer": "prose", "qualname": "", "line_start": 0, "line_end": 0,
               "current": True, **r} for r in rows]
    connect(str(path)).create_table(TABLE, schema=pa.schema(fields)).add(filled)


def _code_rows(store: VectorStore) -> list[tuple[tuple[str, str], ...]]:
    return sorted(_canon(r) for r in store.project(
        ["id", "source_path", "text", "layer", "vector"], clearance=MAINTENANCE_READ,
        where="provenance = 'code'"))


def test_a_table_before_the_plane_rekeys_its_note_records_in_place_and_resumes(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The physical half on a table that predates the plane: note records take their keys, a
    repeated chunk of one note merges (§3), code rows are untouched, and a run that dies between
    adding the new rows and deleting the old ones leaves both and is finished by the next run."""
    path = tmp_path / "old.lance"
    _legacy_table(path, [
        _note("d1", 0, "a.md", "hello", [0.1, 0.2]),
        _note("d1", 1, "a.md", "hello", [0.1, 0.2]),         # the same chunk twice (§3)
        _note("d1", 2, "a.md", "world", [0.3, 0.4]),
        _code_atom("code_ast", "def f(): ...", [0.7, 0.1]),
        _code_record("core/x.py", "code_text", "def g(): ...", [0.2, 0.9]),
    ])
    store = VectorStore(path, dim=DIM)
    assert not store.plane_enabled()                         # PRECONDITION: before the plane
    code_before = _code_rows(store)
    assert len(code_before) == 2
    assert rekey_preview(store) == (3, 3)

    def dies(items: Any) -> Any:
        raise RuntimeError("killed between the add and the delete")
    monkeypatch.setattr(vs_mod, "_batched", dies)
    with pytest.raises(RuntimeError):
        rekey_store(store)
    monkeypatch.undo()
    keys = [chunk_point_id("a.md", Chunk(0, "hello")), chunk_point_id("a.md", Chunk(2, "world"))]
    assert sorted(r["id"] for r in store.note_records(["id"])) == sorted(
        ["d1:0", "d1:1", "d1:2", *keys]), "both, never neither"

    assert rekey_store(store) == (5, 3)                      # the old three move; the new two stay
    assert sorted(r["id"] for r in store.note_records(["id"])) == sorted(keys)
    assert rekey_preview(store) == (2, 0)
    assert _code_rows(store) == code_before, "no code row was read or written"
