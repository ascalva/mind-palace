"""A stream source: items in sequence, written by an edge reader, landed a batch past a cursor
(dn-corpus-instance §5.2; dn-ingress-language §E2).

A stream lives in one directory, the handoff between an edge reader and the lander (the edge
writes it with `edge/corpus/stream.py` and imports nothing of core; this module only reads it).
Its edge reader appends items, each a JSON object on one line with a sequence number (`seq`, from
1, strictly increasing), an `id` (the item's identity within the source, the last component of its
path), its `content` and its `title`; the reader writes them in part files under `stream/` and
names a part in `stream/manifest.json` only once the part is whole, so a reader of the stream
never sees a part being written. The lander records the last
`seq` it landed in `cursor.json` beside the stream, once the plan that read the batch has landed
(the cursor of §E2): `read_items(d, after=cursor, limit=b)` is then the next batch, and a batch
interrupted before its cursor was written is read again, whole, by the next request. Reading is
pure and bounded: a part above the handoff cap is refused, a line above the record cap is
refused, and nothing here touches the network.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

STREAM = "stream"
MANIFEST = "manifest.json"
CURSOR = "cursor.json"
MAX_PART_BYTES = 256 << 20           # a part the lander reads (the handoff cap)
MAX_LINE_BYTES = (32 << 20) + (64 << 10)   # an item under the item cap, escaped, and its fields
_PART = re.compile(r"part-(\d{12})\.jsonl")
_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,199}")


class StreamError(ValueError):
    """A stream that cannot be read as one: a missing or malformed manifest, a part out of
    order, a line that is not an item."""


@dataclass(frozen=True)
class Part:
    file: str
    first: int
    last: int
    items: int
    bytes: int


def item_id_ok(item_id: str) -> bool:
    """Whether an item id is one path component the writer takes: letters, digits, `.`, `_`, `:`
    and `-`, at most 200 characters, not starting with a separator."""
    return bool(_ID.fullmatch(item_id)) and ".." not in item_id


def _atomic_json(path: Path, obj: Mapping[str, Any]) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(dict(obj), ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


def manifest(d: Path) -> list[Part]:
    """The whole parts of the stream in `d`, in order; none when it has no manifest yet."""
    f = d / STREAM / MANIFEST
    if not f.is_file():
        return []
    try:
        doc = json.loads(f.read_text(encoding="utf-8"))
        parts = [Part(str(p["file"]), int(p["first"]), int(p["last"]), int(p["items"]),
                      int(p["bytes"])) for p in doc.get("parts", [])]
    except (ValueError, KeyError, TypeError) as e:
        raise StreamError(f"{f}: not a stream manifest ({e})") from None
    expect = 1
    for p in parts:
        if not _PART.fullmatch(p.file) or p.first != expect or p.last < p.first \
                or p.items != p.last - p.first + 1:
            raise StreamError(f"{f}: part {p.file} breaks the sequence at {expect}")
        expect = p.last + 1
    return parts


def last_seq(d: Path) -> int:
    """The last sequence number the stream's whole parts hold (0 for an empty stream)."""
    parts = manifest(d)
    return parts[-1].last if parts else 0


def cursor(d: Path) -> int:
    """The last sequence number landed (0 before the first batch)."""
    f = d / CURSOR
    if not f.is_file():
        return 0
    try:
        return int(json.loads(f.read_text(encoding="utf-8"))["seq"])
    except (ValueError, KeyError, TypeError) as e:
        raise StreamError(f"{f}: not a cursor ({e})") from None


def write_cursor(d: Path, seq: int) -> None:
    """Record that every item up to `seq` has landed: written once the plan that read them has
    landed, never before (a batch interrupted earlier is read again, whole)."""
    if seq < cursor(d):
        raise StreamError(f"{d}: the cursor moves forward only ({cursor(d)} > {seq})")
    _atomic_json(d / CURSOR, {"seq": seq,
                              "at": datetime.now(UTC).isoformat(timespec="seconds")})


def _lines(path: Path) -> Iterator[dict[str, Any]]:
    size = path.stat().st_size
    if size > MAX_PART_BYTES:
        raise StreamError(f"{path}: {size} bytes, more than a part may have")
    with path.open("rb") as fh:
        for raw in fh:
            if len(raw) > MAX_LINE_BYTES:
                raise StreamError(f"{path}: a line of {len(raw)} bytes")
            doc = json.loads(raw)
            if not isinstance(doc, dict):
                raise StreamError(f"{path}: a line that is not an object")
            yield doc


def read_items(d: Path, *, after: int = 0, limit: int | None = None) -> list[dict[str, Any]]:
    """The items with `seq > after`, in order, at most `limit` of them, read only from the parts
    that hold them. Each is checked: its `seq` the next in order, an `id` the writer takes, a
    string `content`."""
    out: list[dict[str, Any]] = []
    want = after + 1
    for p in manifest(d):
        if p.last < want:
            continue
        if limit is not None and len(out) >= limit:
            break
        for doc in _lines(d / STREAM / p.file):
            seq = doc.get("seq")
            if not isinstance(seq, int) or isinstance(seq, bool):
                raise StreamError(f"{p.file}: an item without a sequence number")
            if seq < want:
                continue
            if seq != want:
                raise StreamError(f"{p.file}: item {seq} where {want} was due")
            item_id = doc.get("id")
            if not isinstance(item_id, str) or not item_id_ok(item_id):
                raise StreamError(f"{p.file}: item {seq} has no id the writer takes")
            if not isinstance(doc.get("content"), str):
                raise StreamError(f"{p.file}: item {seq} has no content")
            out.append(doc)
            want += 1
            if limit is not None and len(out) >= limit:
                break
    return out
