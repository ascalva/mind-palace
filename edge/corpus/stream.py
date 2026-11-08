"""The edge side of a stream: items appended in sequence, a part named in the manifest only once it
is whole (the format `core/ingest/stream.py` reads; the two are tested against each other).

    <dir>/stream/part-<first seq, 12 digits>.jsonl  one item a line: seq, id, title, content
    <dir>/stream/manifest.json                   {"parts": [{file, first, last, items, bytes}]}
    <dir>/meta/items.jsonl                       one metadata record an item, by id

Reopening a stream resumes after its last whole part: a part never named was cut off mid-write
and is removed, and the metadata lines of items past the last whole part are dropped with it.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

PART_BYTES = 32 << 20          # a new part past this many bytes
_PART = re.compile(r"part-(\d{12})\.jsonl")
_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,199}")


def item_id_ok(item_id: str) -> bool:
    """An item id is one path component the lander takes (`core/ingest/stream.py`)."""
    return bool(_ID.fullmatch(item_id)) and ".." not in item_id


def _atomic_json(path: Path, obj: Any) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


class StreamWriter:
    """Append items to a stream, each with the next sequence number, and their metadata beside."""

    def __init__(self, d: Path, *, part_bytes: int = PART_BYTES) -> None:
        self.dir = d
        self.part_bytes = part_bytes
        (d / "stream").mkdir(parents=True, exist_ok=True)
        (d / "meta").mkdir(parents=True, exist_ok=True)
        (d / "FETCHING").write_text(str(os.getpid()))      # the lander waits while it is here
        man = d / "stream" / "manifest.json"
        self.parts: list[dict[str, Any]] = (
            json.loads(man.read_text(encoding="utf-8"))["parts"] if man.is_file() else [])
        self.next_seq = (int(self.parts[-1]["last"]) + 1) if self.parts else 1
        named = {p["file"] for p in self.parts}
        for f in (d / "stream").iterdir():
            if _PART.fullmatch(f.name) and f.name not in named:
                f.unlink()
        self.ids: set[str] = set()
        self.text_bytes = 0
        for p in self.parts:
            with (d / "stream" / p["file"]).open(encoding="utf-8") as fh:
                for line in fh:
                    doc = json.loads(line)
                    self.ids.add(str(doc["id"]))
                    self.text_bytes += len(str(doc["content"]).encode("utf-8"))
        self._trim_meta()
        self._meta = (d / "meta" / "items.jsonl").open("a", encoding="utf-8")
        self._fh: Any = None
        self._file = ""
        self._first = 0
        self._bytes = 0
        self._pending_meta: list[str] = []

    def _trim_meta(self) -> None:
        """Keep only the metadata of items in whole parts (a cut-off part's are dropped)."""
        f = self.dir / "meta" / "items.jsonl"
        if not f.is_file():
            return
        kept = []
        with f.open(encoding="utf-8") as fh:
            for line in fh:
                try:
                    if str(json.loads(line).get("id")) in self.ids:
                        kept.append(line)
                except ValueError:
                    continue
        tmp = f.with_name(f.name + ".tmp")
        tmp.write_text("".join(kept), encoding="utf-8")
        tmp.replace(f)

    def has(self, item_id: str) -> bool:
        return item_id in self.ids

    def append(self, item_id: str, title: str, content: str, meta: dict[str, Any] | None = None,
               **fields: Any) -> int:
        """Append one item; returns its sequence number. An id already in the stream is refused:
        a reader dedupes before it appends."""
        if not item_id_ok(item_id):
            raise ValueError(f"not an item id: {item_id!r}")
        if item_id in self.ids:
            raise ValueError(f"{item_id!r} is in the stream already")
        if self._fh is None:
            self._first = self.next_seq
            self._file = f"part-{self._first:012d}.jsonl"
            self._fh = (self.dir / "stream" / self._file).open("w", encoding="utf-8")
            self._bytes = 0
        seq = self.next_seq
        line = json.dumps({"seq": seq, "id": item_id, "title": title, "content": content,
                           **fields}, ensure_ascii=False) + "\n"
        self._fh.write(line)
        self._bytes += len(line.encode("utf-8"))
        self.text_bytes += len(content.encode("utf-8"))
        self.ids.add(item_id)
        self._pending_meta.append(json.dumps({"id": item_id, **(meta or {})},
                                             ensure_ascii=False) + "\n")
        self.next_seq += 1
        if self._bytes >= self.part_bytes:
            self.close_part()
        return seq

    def close_part(self) -> None:
        """Close the open part, write its items' metadata, and name it in the manifest."""
        if self._fh is None:
            return
        self._fh.flush()
        os.fsync(self._fh.fileno())
        self._fh.close()
        self._fh = None
        self._meta.write("".join(self._pending_meta))
        self._meta.flush()
        self._pending_meta = []
        last = self.next_seq - 1
        self.parts.append({"file": self._file, "first": self._first, "last": last,
                           "items": last - self._first + 1, "bytes": self._bytes})
        _atomic_json(self.dir / "stream" / "manifest.json", {"parts": self.parts})

    def close(self) -> None:
        self.close_part()
        self._meta.close()
        (self.dir / "FETCHING").unlink(missing_ok=True)
