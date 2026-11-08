"""The corpus instance as the stage-1 measurements read it: each source's items and metadata, an
integer id for every item, its date, and the chunk vectors the plane holds (read only).

Items come from the streams' metadata (`<root>/<source>/meta/items.jsonl`, written by the edge
readers beside each stream); an item's path is `corpus/<source>/<id>`, its date the source's
(OpenAlex: publication; arXiv: first version; Stack Exchange: creation; Gutenberg: release;
Wikipedia: the page's creation, interpolated from its id, `meta/created.json`). Vectors come from
the instance's plane: the current occupancies (`plane.sqlite`) joined to the atoms' float16 vectors
(the LanceDB table), read through Arrow into one NumPy matrix.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import numpy.typing as npt

SOURCES = ("wikipedia", "openalex", "arxiv", "stackexchange", "gutenberg", "hackernews")
EPOCH = date(1970, 1, 1)


def day(text: str | None) -> int:
    """Days since 1970-01-01 of an ISO date ('' or a bad date: -1)."""
    try:
        return (date.fromisoformat(str(text)[:10]) - EPOCH).days
    except (TypeError, ValueError):
        return -1


@dataclass
class Corpus:
    """Every item of every source, numbered: `gid` is the item's global integer id."""

    root: Path
    sources: tuple[str, ...]
    paths: list[str] = field(default_factory=list)          # gid -> corpus/<source>/<id>
    source_of: list[int] = field(default_factory=list)      # gid -> index into `sources`
    dates: list[int] = field(default_factory=list)          # gid -> days since 1970 (-1: none)
    meta: list[dict[str, Any]] = field(default_factory=list)  # gid -> the reader's metadata
    gid: dict[str, int] = field(default_factory=dict)       # path -> gid

    @property
    def n(self) -> int:
        return len(self.paths)

    def of(self, source: str) -> npt.NDArray[np.int64]:
        k = self.sources.index(source)
        return np.flatnonzero(np.asarray(self.source_of) == k)

    def id_of(self, source: str, item_id: str) -> int | None:
        return self.gid.get(f"corpus/{source}/{item_id}")


def _lines(path: Path) -> Iterator[dict[str, Any]]:
    if not path.is_file():
        return
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                yield json.loads(line)


def titles(root: Path, source: str) -> dict[str, str]:
    """Each item's title, as its stream carries it (the metadata need not repeat it)."""
    from core.ingest.stream import manifest

    out: dict[str, str] = {}
    for p in manifest(root / source):                 # the whole parts, as the lander reads
        with (root / source / "stream" / p.file).open(encoding="utf-8") as fh:
            for line in fh:
                doc = json.loads(line)
                out[str(doc["id"])] = str(doc.get("title") or "")
    return out


def load(root: Path, sources: tuple[str, ...] = SOURCES, *, with_titles: bool = True) -> Corpus:
    """The items the streams hold, numbered source by source in stream order; each item's
    metadata carries its stream title under `title` unless the reader wrote one."""
    c = Corpus(root, sources)
    for k, s in enumerate(sources):
        named = titles(root, s) if with_titles else {}
        created: dict[str, str] = {}
        cf = root / s / "meta" / "created.json"
        if cf.is_file():
            created = json.loads(cf.read_text())
        for m in _lines(root / s / "meta" / "items.jsonl"):
            path = f"corpus/{s}/{m['id']}"
            if path in c.gid:
                continue
            when = m.get("date") or created.get(str(m.get("pageid", "")), "")
            if "title" not in m and str(m["id"]) in named:
                m["title"] = named[str(m["id"])]
            c.gid[path] = len(c.paths)
            c.paths.append(path)
            c.source_of.append(k)
            c.dates.append(day(when))
            c.meta.append(m)
    return c


@dataclass
class Vectors:
    """The plane's current chunk vectors: one row an atom, the items holding it."""

    atom_ids: list[str]
    matrix: npt.NDArray[np.float16]                  # atoms x dim, as stored
    holders: list[list[int]]                         # atom row -> the gids of the items holding it
    item_atoms: dict[int, list[int]]                 # gid -> its atom rows

    def item_means(self, n: int) -> tuple[npt.NDArray[np.float32], npt.NDArray[np.bool_]]:
        """Each item's mean chunk vector, unit length (float32), and which items have one."""
        dim = self.matrix.shape[1]
        out = np.zeros((n, dim), dtype=np.float32)
        have = np.zeros(n, dtype=bool)
        for g, rows in self.item_atoms.items():
            if 0 <= g < n and rows:
                v = self.matrix[rows].astype(np.float32).mean(axis=0)
                nv = float(np.linalg.norm(v))
                if nv > 0:
                    out[g] = v / nv
                    have[g] = True
        return out, have


def load_vectors(cfg: Any, corpus: Corpus) -> Vectors:
    """The current occupancies of the observed class, joined to their atoms' vectors."""
    from core.typedshims.lancedb import connect

    con = sqlite3.connect(f"file:{cfg.paths.vector_store / 'plane.sqlite'}?mode=ro", uri=True)
    try:
        occ = con.execute("SELECT source_path, atom_id FROM occ_observed WHERE current = 1")\
            .fetchall()
    finally:
        con.close()
    by_atom: dict[str, list[int]] = {}
    for path, atom in occ:
        g = corpus.gid.get(str(path))
        if g is not None:
            by_atom.setdefault(str(atom), []).append(g)
    db = connect(str(cfg.paths.vector_store))
    table = db.open_table("chunks")
    tab = (table.scan().select(["id", "vector"])
           .where("provenance = '' AND source_path = '' AND digest = ''").limit(0).to_arrow())
    all_ids = [str(a) for a in tab.column("id").to_pylist()]
    keep = np.asarray([a in by_atom for a in all_ids], dtype=bool)
    col = tab.column("vector").combine_chunks()
    mat = np.asarray(col.values).reshape(len(tab), -1)
    matrix = np.ascontiguousarray(mat[keep]).astype(np.float16, copy=False)
    ids = [a for a, k in zip(all_ids, keep, strict=True) if k]
    del tab, col, mat
    holders = [by_atom[a] for a in ids]
    item_atoms: dict[int, list[int]] = {}
    for row, gs in enumerate(holders):
        for g in gs:
            item_atoms.setdefault(g, []).append(row)
    return Vectors(ids, matrix, holders, item_atoms)
