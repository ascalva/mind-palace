"""What a script reads through: the palace's sources and places, opened under the speaking role
(dn-door-language §E2, §E3). The view the evaluator is handed (`core.sentence.interpret.Palace`).

Every value a reader yields is labelled here, by the source's rule, never by a script: an item's
content is `Content` with its label and origin, and every string read off it (its path, title,
digest, properties) is an `OStr` with the same, so a projection keeps its item's label (DOR-13)
and the type checker's sets are sound at run time (DOR-18). An entry of a place is the palace's
account of a row, and its strings are observed.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

from core.ingest.table import MAX_HANDOFF_BYTES, MAX_ITEM_BYTES, Source, Table, write_cursor
from core.kernel.config import REPO_ROOT, Config
from core.kernel.ingest.logseq import parse_note
from core.sentence.interpret import (
    OBSERVED,
    Content,
    Handle,
    Origin,
    OStr,
    Record,
    ScriptError,
)


def edge_env() -> dict[str, str]:
    """The environment an edge reader runs in: launchd's PATH lacks Homebrew's, where podman
    lives (the third review's finding 4)."""
    env = dict(os.environ)
    have = env.get("PATH", "").split(":")
    env["PATH"] = ":".join([*have, *(d for d in ("/opt/homebrew/bin", "/usr/local/bin")
                                     if d not in have)])
    return env


class PalaceView:
    """The palace as one evaluation reads it, under one role. `catalog` is the place's index of
    rows (`VaultCatalog` or a fake); `query` evaluates a read sentence under the role's grant."""

    def __init__(self, table: Table, role: str, catalog: Any, *,
                 query: Callable[[str], list[Record]] | None = None,
                 refresh: bool = True) -> None:
        self.table = table
        self.role = role
        self.catalog = catalog
        self._query = query
        self._refresh = refresh
        self._docs: dict[str, Any] = {}           # structured sources read, by name
        self._items: dict[str, list[Record]] = {}

    # sources -----------------------------------------------------------------------------

    def _source(self, h: Handle) -> Source:
        s = self.table.sources.get(h.name)
        if s is None or self.role not in s.readers:
            raise ScriptError(f"source({h.name!r}): not open to the role {self.role!r}")
        return s

    def open(self, name: str) -> Handle:
        s = self.table.sources.get(name)
        if s is None:
            raise ScriptError(f"source({name!r}): no such source")
        if self.role not in s.readers:
            raise ScriptError(f"source({name!r}): the role {self.role!r} may not open it")
        return Handle(name, str(s.location))

    def files(self, h: Handle) -> Iterator[Record]:
        """The source's items in path order, each read and parsed only when the evaluator asks for
        the next, so the meter stops a read at the item that ran the budget out."""
        s = self._source(h)
        if s.kind != "dir":
            raise ScriptError(f"files({h.name!r}): a directory source; use items(…)")
        seen: dict[str, Path] = {}
        for pattern in s.patterns:
            for p in sorted(s.location.glob(pattern)):
                if p.is_file() and s.in_scope(p):
                    seen.setdefault(str(p), p)
        return (self._markdown(s, p) for _, p in sorted(seen.items()))

    def _named(self, s: Source, path: str) -> Path:
        """A path as the source names its items: under its location as configured."""
        p = Path(path).expanduser()
        if not p.is_absolute():
            p = s.location / p
        try:
            rel = p.resolve().relative_to(s.location.expanduser().resolve())
        except (ValueError, OSError):
            raise ScriptError(f"{path!r} is not in the source {s.name!r}") from None
        return s.location / rel

    def file(self, h: Handle, path: str) -> Record:
        s = self._source(h)
        if s.kind != "dir":
            raise ScriptError(f"file({h.name!r}, …): a directory source")
        p = self._named(s, path)
        if not (p.is_file() and s.in_scope(p) and s.spelled(p)):
            raise ScriptError(f"file({h.name!r}, {path!r}): not an item of the source (its "
                              "pattern, its excluded directories, the disk's spelling)")
        return self._markdown(s, p)

    def exists(self, h: Handle, path: str) -> bool:
        s = self._source(h)
        if s.kind == "dir":
            try:
                p = self._named(s, path)
            except ScriptError:
                return False
            return p.is_file() and s.in_scope(p) and s.spelled(p)
        return any(str(r["path"]) == path for r in self.items(h))

    def has(self, path: str) -> bool:
        """Whether the source that owns a path still has it (R6, R7)."""
        s = self.table.owner(path)
        if s is None:
            return False
        return self.exists(Handle(s.name, str(s.location)), path) if self.role in s.readers \
            else _exists_as(s, path)

    def _markdown(self, s: Source, p: Path) -> Record:
        size = p.stat().st_size
        if size > MAX_ITEM_BYTES:
            raise ScriptError(f"{p}: {size} bytes, more than an item may have ({MAX_ITEM_BYTES})")
        parsed = parse_note(p, s.location)
        label = s.label or OBSERVED
        origin = Origin("item", s.name, str(p), parsed.title)

        def o(v: str) -> OStr:
            return OStr(v, label, origin)

        return Record({
            "path": o(str(p)),
            "content": Content(parsed.raw_bytes, label, origin),
            "digest": o(hashlib.sha256(parsed.raw_bytes).hexdigest()),
            "title": o(parsed.title),
            "properties": Record({k: o(v) for k, v in parsed.properties.items()}),
            "tags": [o(t) for t in sorted(parsed.tags)],
            "links": [o(x) for x in sorted(parsed.links)],
        })

    def items(self, h: Handle) -> list[Record]:
        s = self._source(h)
        if s.kind != "file" or s.items_of is None or s.path_of is None or s.label_of is None:
            raise ScriptError(f"items({h.name!r}): a structured source; use files(…)")
        if h.name in self._items:
            return self._items[h.name]
        if self._refresh and s.refresh is not None:
            done = subprocess.run(list(s.refresh), cwd=REPO_ROOT, capture_output=True, text=True,
                                  timeout=s.refresh_timeout, env=edge_env())
            if done.returncode != 0:
                raise ScriptError(f"{s.name}: its edge reader failed: "
                                  f"{done.stderr.strip()[-300:]}")
        try:
            size = s.location.stat().st_size
        except OSError:
            raise ScriptError(f"{s.name}: no handoff at {s.location}") from None
        if size > MAX_HANDOFF_BYTES:
            raise ScriptError(f"{s.name}: {size} bytes, more than a handoff may have")
        doc = json.loads(s.location.read_text(encoding="utf-8"))
        out: list[Record] = []
        for it in s.items_of(doc):
            label, path = s.label_of(it), s.path_of(it)
            origin = Origin("item", s.name, path, "")
            fields: dict[str, Any] = {"path": OStr(path, label, origin)}
            for k, v in it.items():
                if k == s.content_field:
                    fields[k] = Content(str(v).encode("utf-8"), label, origin)
                elif isinstance(v, str):
                    fields[k] = OStr(v, label, origin)
                else:
                    fields[k] = v
            out.append(Record(fields))
        self._docs[h.name] = doc
        self._items[h.name] = out
        return out

    def landed(self) -> None:
        """A plan that read the structured sources has landed: record each one's cursor."""
        for name, doc in self._docs.items():
            write_cursor(self.table.sources[name], doc)

    # places ------------------------------------------------------------------------------

    def _entries(self, place: str) -> list[Any]:
        p = self.table.places.get(place)
        if p is None:
            raise ScriptError(f"{place!r}: no such place")
        return [e for e in self.catalog.active_entries() if str(e.provenance) in p.accepts]

    def _entry(self, place: str, e: Any) -> Record:
        origin = Origin("entry", place, str(e.source_path), str(e.title))

        def o(v: str) -> OStr:
            return OStr(v, OBSERVED, origin)

        doc_id = getattr(e, "doc_id", None) or self.catalog.doc_id_for(e.source_path)
        return Record({"path": o(str(e.source_path)), "identity": o(str(doc_id)),
                       "digest": o(str(e.digest)), "title": o(str(e.title)),
                       "active": bool(e.active)})

    def stored(self, place: str, prefix: str) -> list[Record]:
        return [self._entry(place, e) for e in self._entries(place)
                if str(e.source_path).startswith(prefix)]

    def entry(self, place: str, name: str) -> Record:
        es = self._entries(place)
        hits = [e for e in es if str(e.source_path) == name] \
            or [e for e in es if str(e.title) == name]
        if not hits:
            raise ScriptError(f"entry({place!r}, {name!r}): no such entry")
        if len(hits) > 1:
            raise ScriptError(f"entry({place!r}, {name!r}): {len(hits)} entries have that title; "
                              "name one by its path")
        return self._entry(place, hits[0])

    def query(self, sentence: str) -> list[Record]:
        if self._query is None:
            raise ScriptError("a nested sentence needs the read half, which is not open here")
        return self._query(sentence)


def _exists_as(s: Source, path: str) -> bool:
    """Whether a directory source still has a path, read by the writer for a role that may not
    open the source (R7 asks whether the source has it, not whether the role may see it)."""
    if s.kind != "dir":
        return False
    p = Path(path)
    return p.is_file() and s.in_scope(p) and s.spelled(p)


def build_view(cfg: Config, table: Table, role: str, catalog: Any, **kw: Any) -> PalaceView:
    return PalaceView(table, role, catalog, **kw)
