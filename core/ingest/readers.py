"""What a script reads through: the palace's sources and places, opened under the speaking role
(dn-ingress-language §E2, §E3). The view the evaluator is handed (`core.sentence.interpret.Palace`).

Every value a reader yields is labelled here, by the source's rule, never by a script: an item's
content is `Content` with its label and origin, and every string read off it (its path, title,
digest, properties) is an `OStr` with the same, so the type checker's sets are sound at run time
(ING-18). A string is not the item's bytes: stored, it is composed and observed (§E3). The one
string that names something is the property a source declares as its items' identity (`id::` in
the vault), whose origin says so, so a store may take it as the item's identity (R6) and no other
field can pose as one. An entry of a place is the palace's account of a row, and its strings are
observed. A structured source's edge reader runs only when the caller asks (the daemon's own
syncs and the owner's CLI), never for a request a role spoke. A structured source whose rule may
give a label other than the observed one (a dialogue reader's handoff, the inbox's record) is read
only as the daemon trusts it (`core/ingest/files.py`), so no other account plants an item its rule
would label as the owner's. A records source is a directory of such documents; one the table marks
as consumed loses a document once a plan has landed every item it yields.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import re
import subprocess
from collections.abc import Callable, Iterator, Mapping, Sequence
from pathlib import Path
from typing import Any

from core.ingest.files import check_dir, read_bounded, written_by_one
from core.ingest.table import (
    MAX_HANDOFF_BYTES,
    MAX_ITEM_BYTES,
    MAX_RECORD_BYTES,
    Source,
    Table,
    write_cursor,
)
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

_DOCUMENT = re.compile(r"[0-9A-Za-z_-][0-9A-Za-z._-]{0,127}\.json")   # a records source's file


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
        # a records source's documents as read: the file, its identity then, its items' paths
        self._files: dict[str, list[tuple[Path, tuple[int, int], list[str]]]] = {}
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
        if s.kind not in ("file", "records") or s.items_of is None or s.path_of is None \
                or s.label_of is None:
            raise ScriptError(f"items({h.name!r}): a structured source; use files(…)")
        return self._read_items(s)

    def _read_items(self, s: Source) -> list[Record]:
        """A structured source's items, read once an evaluation, each labelled by the source's
        rule, which must give a label in the range the table declares (the checker's sets rest on
        it, ING-18). An item's content past the item cap is still an item, one the writer refuses
        to store (R1), as a directory source's is."""
        assert s.items_of is not None and s.path_of is not None and s.label_of is not None
        if s.name in self._items:
            return self._items[s.name]
        out: list[Record] = []
        if s.kind == "records":
            files: list[tuple[Path, tuple[int, int], list[str]]] = []
            for f, key, doc in self._records(s):
                items = [self._item(s, it) for it in s.items_of(doc)]
                out.extend(items)
                files.append((f, key, [str(r["path"]) for r in items]))
            self._files[s.name] = files
        else:
            doc = self._document(s)
            out = [self._item(s, it) for it in s.items_of(doc)]
            self._docs[s.name] = doc
        self._items[s.name] = out
        return out

    def _document(self, s: Source) -> Any:
        """A structured source's file, refreshed first by its edge reader if the caller asked. A
        source whose rule may give a label other than the observed one (a dialogue reader's: the
        owner's turns) is read only as the daemon trusts it: its directory the daemon's own and
        writable by no other account, the file read through a descriptor that follows no link, a
        regular file of one link that the daemon's account owns and no other may write, under the
        handoff cap. So no account but the daemon's, and the edge readers it runs, can plant a
        turn the rule would label as the owner's."""
        if self._refresh and s.refresh is not None:
            done = subprocess.run(list(s.refresh), cwd=REPO_ROOT, capture_output=True, text=True,
                                  timeout=s.refresh_timeout, env=edge_env())
            if done.returncode != 0:
                raise ScriptError(f"{s.name}: its edge reader failed: "
                                  f"{done.stderr.strip()[-300:]}")
        if not os.path.lexists(s.location):
            raise ScriptError(f"{s.name}: no handoff at {s.location}")
        if _may_author(s):
            why = check_dir(s.location.parent)
            if why is not None:
                raise ScriptError(f"{s.name}: the handoff is refused ({why})")
            try:
                data, st = read_bounded(s.location, MAX_HANDOFF_BYTES)
                why = written_by_one(st)
                if why is not None:
                    raise ValueError(why)
            except (OSError, ValueError) as e:
                raise ScriptError(f"{s.name}: the handoff is refused ({e})") from None
            return json.loads(data.decode("utf-8"))
        size = s.location.stat().st_size
        if size > MAX_HANDOFF_BYTES:
            raise ScriptError(f"{s.name}: {size} bytes, more than a handoff may have")
        return json.loads(s.location.read_text(encoding="utf-8"))

    def _records(self, s: Source) -> list[tuple[Path, tuple[int, int], Any]]:
        """A records source's documents in name order, as the daemon trusts them: its directory
        the daemon's own and writable by no other account, each document read through a
        descriptor that follows no link, a regular file of one link that the daemon's account
        owns and no other may write, under the cap. Anything else refuses the source, so no
        account but the daemon's adds a document. No directory yet is no document."""
        d = s.location
        if not os.path.lexists(d):
            return []
        why = check_dir(d)
        if why is not None:
            raise ScriptError(f"{s.name}: {why}")
        out: list[tuple[Path, tuple[int, int], Any]] = []
        for name in sorted(n for n in os.listdir(d) if _DOCUMENT.fullmatch(n)):
            try:
                data, st = read_bounded(d / name, MAX_RECORD_BYTES)
                why = written_by_one(st)
                if why is not None:
                    raise ValueError(why)
                doc = json.loads(data.decode("utf-8"))
            except (OSError, ValueError) as e:
                raise ScriptError(f"{s.name}: the document {name} is refused ({e})") from None
            out.append((d / name, (st.st_ino, st.st_mtime_ns), doc))
        return out

    def _item(self, s: Source, it: Mapping[str, Any]) -> Record:
        assert s.path_of is not None and s.label_of is not None
        label, path = s.label_of(it), s.path_of(it)
        if s.labels and label not in s.labels:
            raise ScriptError(f"{s.name}: its rule gave {label!r}, outside its labels")
        origin = Origin("item", s.name, path, s.title_of(it) if s.title_of else "")
        fields: dict[str, Any] = {"path": OStr(path, label, origin)}
        for k, v in it.items():
            if k == s.content_field:
                data = str(v).encode("utf-8")
                fields[k] = (Content(b"", label, origin, oversize=len(data))
                             if len(data) > MAX_ITEM_BYTES else Content(data, label, origin))
            elif isinstance(v, str):
                fields[k] = OStr(v, label, origin)
            else:
                fields[k] = v
        return Record(fields)

    def landed(self, outcomes: Sequence[Any] = ()) -> None:
        """A plan that read a structured source has landed: record the source's cursor if the plan
        stored every item it read from it (landed, unchanged, or refused by a rule, which a retry
        would refuse again). A plan that only looked at a source records nothing, so the
        heartbeat never reads a source as synced that was not. A consumed records source loses
        each document every item of which the plan landed or found unchanged, never one an item of
        which was refused, and never one rewritten since it was read: the raw store holds its
        bytes now, and the next read is of what is pending."""
        stored = {o.path for o in outcomes if getattr(o, "effect", "") == "store"}
        whole = {o.path for o in outcomes if getattr(o, "effect", "") == "store"
                 and getattr(o, "status", "") in ("landed", "unchanged")}
        for name, doc in self._docs.items():
            if all(str(r["path"]) in stored for r in self._items.get(name, [])):
                write_cursor(self.table.sources[name], doc)
        for name, files in self._files.items():
            if not self.table.sources[name].consume:
                continue
            for f, key, paths in files:
                if paths and all(p in whole for p in paths):
                    _consume(f, key)

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


def _may_author(s: Source) -> bool:
    """Whether a source's rule may give a label other than the observed one: the range the table
    declares, and an undeclared range counts as one that may."""
    labels = {s.label} if s.label is not None else set(s.labels)
    return not labels or bool(labels - {OBSERVED})


def _consume(f: Path, key: tuple[int, int]) -> None:
    """Remove a landed document, if it is still the file that was read (a rename since replaced
    it: the new one is pending, and stays)."""
    with contextlib.suppress(OSError):
        st = os.lstat(f)
        if (st.st_ino, st.st_mtime_ns) == key:
            f.unlink()


def _exists_as(s: Source, path: str,
               listdir: Callable[[Path], frozenset[str]] | None = None) -> bool:
    """Whether a directory source still has a path, as the source names it."""
    p = Path(path)
    if listdir is None:
        return p.is_file() and s.in_scope(p) and s.spelled(p)
    return p.is_file() and s.in_scope(p) and s.spelled(p, listdir)


def build_view(cfg: Config, table: Table, role: str, catalog: Any, **kw: Any) -> PalaceView:
    return PalaceView(table, role, catalog, **kw)
