"""What a script reads through: the palace's sources and places, opened under the speaking role
(dn-door-language §E2, §E3). The view the evaluator is handed (`core.sentence.interpret.Palace`).

Every value a reader yields is labelled here, by the source's rule, never by a script: an item's
content is `Content` with its label and origin, and every string read off it (its path, title,
digest, properties) is an `OStr` with the same, so the type checker's sets are sound at run time
(DOR-18). A string is not the item's bytes: stored, it is composed and observed (§E3). The one
string that names something is the property a source declares as its items' identity (`id::` in
the vault), whose origin says so, so a store may take it as the item's identity (R6) and no other
field can pose as one. An entry of a place is the palace's account of a row, and its strings are
observed. A structured source's edge reader runs only when the caller asks (the daemon's own
syncs and the owner's CLI), never for a request a role spoke.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from collections.abc import Callable, Iterator, Sequence
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


class Listing:
    """A directory source's items in path order, listed at once and read one by one: `len` is
    the number of paths listed, which the evaluator pays for before it reads the first."""

    def __init__(self, paths: Sequence[Path], read: Callable[[Path], Record]) -> None:
        self._paths = paths
        self._read = read

    def __len__(self) -> int:
        return len(self._paths)

    def __iter__(self) -> Iterator[Record]:
        return (self._read(p) for p in self._paths)


class PalaceView:
    """The palace as one evaluation reads it, under one role. `catalog` is the place's index of
    rows (`VaultCatalog` or a fake); `query` evaluates a read sentence under the role's grant;
    `refresh` runs a structured source's edge reader before its first read."""

    def __init__(self, table: Table, role: str, catalog: Any, *,
                 query: Callable[[str], list[Record]] | None = None,
                 refresh: bool = False) -> None:
        self.table = table
        self.role = role
        self.catalog = catalog
        self._query = query
        self._refresh = refresh
        self._docs: dict[str, Any] = {}           # structured sources read, by name
        self._items: dict[str, list[Record]] = {}
        self._listings: dict[Path, frozenset[str]] = {}

    def _listdir(self, d: Path) -> frozenset[str]:
        """A directory's names, listed once an evaluation."""
        if d not in self._listings:
            self._listings[d] = frozenset(os.listdir(d))
        return self._listings[d]

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

    def files(self, h: Handle) -> Listing:
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
        return Listing([p for _, p in sorted(seen.items())], lambda p: self._markdown(s, p))

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
        if not (p.is_file() and s.in_scope(p) and s.spelled(p, self._listdir)):
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
            return p.is_file() and s.in_scope(p) and s.spelled(p, self._listdir)
        return any(str(r["path"]) == path for r in self.items(h))

    def has(self, path: str) -> bool:
        """Whether the source that owns a path still has it (R6, R7): asked of the source itself,
        whether or not the speaking role may open it."""
        s = self.table.owner(path)
        if s is None:
            return False
        if s.kind == "dir":
            return _exists_as(s, path, self._listdir)
        return any(str(r["path"]) == path for r in self._read_items(s))

    def _markdown(self, s: Source, p: Path) -> Record:
        label = s.label or OBSERVED
        size = p.stat().st_size
        if size > MAX_ITEM_BYTES:
            # too large to read: still an item of the source, so a sync keeps its path present
            # and retires nothing, and its content one the writer refuses to store (R1)
            origin = Origin("item", s.name, str(p), p.stem)
            return Record({"path": OStr(str(p), label, origin),
                           "content": Content(b"", label, origin, oversize=size),
                           "digest": None, "title": OStr(p.stem, label, origin),
                           "properties": Record({}), "tags": [], "links": []})
        parsed = parse_note(p, s.location)
        origin = Origin("item", s.name, str(p), parsed.title)
        declared = Origin("id", s.name, str(p), parsed.title)

        def o(v: str) -> OStr:
            return OStr(v, label, origin)

        return Record({
            "path": o(str(p)),
            "content": Content(parsed.raw_bytes, label, origin),
            "digest": o(hashlib.sha256(parsed.raw_bytes).hexdigest()),
            "title": o(parsed.title),
            # a blank property is no property; the identity property is the item's declared one
            "properties": Record({k: (OStr(v, label, declared) if k == s.identity else o(v))
                                  for k, v in parsed.properties.items() if v.strip()}),
            "tags": [o(t) for t in sorted(parsed.tags)],
            "links": [o(x) for x in sorted(parsed.links)],
        })

    def items(self, h: Handle) -> list[Record]:
        s = self._source(h)
        if s.kind != "file" or s.items_of is None or s.path_of is None or s.label_of is None:
            raise ScriptError(f"items({h.name!r}): a structured source; use files(…)")
        return self._read_items(s)

    def _read_items(self, s: Source) -> list[Record]:
        """A structured source's items, read once an evaluation: refreshed first by its edge
        reader if the caller asked, each labelled by the source's rule, which must give a label in
        the range the table declares (the checker's sets rest on it, DOR-18)."""
        assert s.items_of is not None and s.path_of is not None and s.label_of is not None
        if s.name in self._items:
            return self._items[s.name]
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
            if s.labels and label not in s.labels:
                raise ScriptError(f"{s.name}: its rule gave {label!r}, outside its labels")
            origin = Origin("item", s.name, path, s.title_of(it) if s.title_of else "")
            fields: dict[str, Any] = {"path": OStr(path, label, origin)}
            for k, v in it.items():
                if k == s.content_field:
                    fields[k] = Content(str(v).encode("utf-8"), label, origin)
                elif isinstance(v, str):
                    fields[k] = OStr(v, label, origin)
                else:
                    fields[k] = v
            out.append(Record(fields))
        self._docs[s.name] = doc
        self._items[s.name] = out
        return out

    def landed(self, outcomes: Sequence[Any] = ()) -> None:
        """A plan that read a structured source has landed: record the source's cursor if the plan
        stored every item it read from it (landed, unchanged, or refused by a rule, which a retry
        would refuse again). A plan that only looked at a source records nothing, so the
        heartbeat never reads a source as synced that was not."""
        stored = {o.path for o in outcomes if getattr(o, "effect", "") == "store"}
        for name, doc in self._docs.items():
            if all(str(r["path"]) in stored for r in self._items.get(name, [])):
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

    def query(self, sentence: str) -> list[Record]:
        if self._query is None:
            raise ScriptError("a nested sentence needs the read half, which is not open here")
        return self._query(sentence)


def _exists_as(s: Source, path: str,
               listdir: Callable[[Path], frozenset[str]] | None = None) -> bool:
    """Whether a directory source still has a path, as the source names it."""
    p = Path(path)
    if listdir is None:
        return p.is_file() and s.in_scope(p) and s.spelled(p)
    return p.is_file() and s.in_scope(p) and s.spelled(p, listdir)


def build_view(cfg: Config, table: Table, role: str, catalog: Any, **kw: Any) -> PalaceView:
    return PalaceView(table, role, catalog, **kw)
