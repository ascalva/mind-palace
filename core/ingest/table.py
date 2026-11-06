"""The palace's table: the sources a script may open, the places it may write, the roles that
speak, the jobs a script may start, and what each role may spend (dn-ingress-language §E2, §E4, §E7,
§E10).

As an operating system has a mount table, owners and permissions, the palace has this table, and
it is the one module where the palace's domain is named: the vault, the curated docs, the
dialogue readers, the strata as places. The language (`core/sentence/script.py`,
`interpret.py`, `script_check.py`) names none of it; a script names a source or a place by a
string the table must know.
"""

from __future__ import annotations

import json
import os
import sys
import unicodedata
from collections.abc import Callable, Collection, Iterator, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any

from core.kernel.clearance import STRATUM_CLASSES
from core.kernel.config import REPO_ROOT, Config
from core.kernel.ingest.logseq import DEFAULT_EXCLUDE_DIRS
from core.kernel.provenance import Provenance
from core.kernel.scope import Clock, Stratum

AUTHORED_SOLO = Provenance.AUTHORED_SOLO.value
AUTHORED_DIALOGUE = Provenance.AUTHORED_DIALOGUE.value
OBSERVED = Provenance.OBSERVED.value
CURATED = Provenance.CURATED.value

MAX_ITEM_BYTES = 16 << 20           # one item a source yields
MAX_HANDOFF_BYTES = 256 << 20       # a structured source's file


@dataclass(frozen=True)
class Source:
    """A source: where it is, how it is read, how its items are labelled, who may open it, and
    which paths are its own (R8)."""

    name: str
    kind: str                                   # "dir" | "file"
    location: Path                              # the directory, or the file
    format: str                                 # "markdown" | "json"
    readers: frozenset[str]
    patterns: tuple[str, ...] = ()              # dir: the scope, relative to the location
    exclude: frozenset[str] = frozenset()       # dir: directories excluded, in any case
    label: str | None = None                    # one label for every item
    items_of: Callable[[Any], Iterator[dict[str, Any]]] | None = None  # json: the item rule
    path_of: Callable[[Mapping[str, Any]], str] | None = None          # json: an item's path
    label_of: Callable[[Mapping[str, Any]], str] | None = None         # json: an item's label
    labels: frozenset[str] = frozenset()        # every label the rule may give
    content_field: str = "content"
    space: str = ""                             # json: the path prefix the source owns
    refresh: tuple[str, ...] | None = None      # an edge process run before the first read
    refresh_timeout: int = 180
    cursor_of: Callable[[Any], int] | None = None   # json: the newest change it saw
    identity: str | None = None                 # the property an item declares its identity in
    title_of: Callable[[Mapping[str, Any]], str] | None = None   # json: an item's title

    def in_scope(self, path: Path) -> bool:
        """Whether a path is one of a directory source's items, existing or not: under the
        location, matching a pattern, in no excluded directory in any case."""
        root = self.location.expanduser().resolve()
        try:
            rel = path.expanduser().resolve().relative_to(root)
        except (ValueError, OSError):
            return False
        if not rel.parts:
            return False
        excluded = {d.casefold() for d in self.exclude}
        if any(part.casefold() in excluded for part in rel.parts):
            return False
        return any(PurePosixPath(rel.as_posix()).full_match(p) for p in self.patterns)

    def spelled(self, path: Path,
                listdir: Callable[[Path], Collection[str]] = os.listdir) -> bool:
        """Whether every component of a path under the location is spelled as the directory
        lists it (a case-insensitive disk opens `PAGES/A.md` for `pages/a.md`; the source names
        it the second way only). `listdir` may be a reader's cache of the listings."""
        here = self.location.expanduser().resolve()
        try:
            rel = path.expanduser().resolve().relative_to(here)
        except (ValueError, OSError):
            return False
        for part in rel.parts:
            try:
                if part not in listdir(here):
                    return False
            except OSError:
                return False
            here = here / part
        return True

    def owns(self, path: str) -> bool:
        """Whether a path lies in this source's own space (R8)."""
        if self.kind == "dir":
            return self.in_scope(Path(path))
        return bool(self.space) and path.startswith(self.space)


@dataclass(frozen=True)
class Place:
    """A place: a stratum, the labels it accepts, whether it keeps version chains, the action
    its attestations record."""

    name: str
    stratum: Stratum
    accepts: frozenset[str]
    versions: bool
    action: str
    clock: Clock = Clock.PROJECTION_EVENT


@dataclass(frozen=True)
class Job:
    """A job a script may start: the queue's kind, the strata it writes (for admission), its
    arguments and their bounds."""

    name: str
    kind: str
    strata: tuple[Stratum, ...]
    fibers: frozenset[str] = frozenset()
    clock: Clock = Clock.PROJECTION_EVENT
    propose: bool = False
    args: Mapping[str, int] = field(default_factory=dict)       # name -> its maximum


@dataclass(frozen=True)
class Role:
    """A role: the path prefixes it may write in each place (R3), its budget (§E10), and the
    labels of the rows it may retire (R7): only the owner's role retires the owner's rows, so no
    agent can take an authored row out of the palace, whatever its source no longer shows."""

    name: str
    prefixes: Mapping[str, tuple[str, ...]]
    budget: int
    retires: frozenset[str] = frozenset({OBSERVED})
    # paths a role only retires, never writes: the first form's stored prefix (`LEGACY_DIALOGUE`)
    retire_only: Mapping[str, tuple[str, ...]] = field(default_factory=dict)


@dataclass(frozen=True)
class Table:
    sources: Mapping[str, Source]
    places: Mapping[str, Place]
    jobs: Mapping[str, Job]
    roles: Mapping[str, Role]
    relations: Mapping[str, tuple[Any, float]]
    interactive: frozenset[str]          # library scripts that run at the interactive tier
    coalescing: Mapping[str, str]        # library script, called bare -> the queue's own kind

    # the checker's view ------------------------------------------------------------------

    def place_accepts(self, place: str) -> frozenset[str] | None:
        p = self.places.get(place)
        return None if p is None else p.accepts

    def job_known(self, job: str) -> bool:
        return job in self.jobs

    def source_readable(self, name: str, role: str) -> bool | None:
        s = self.sources.get(name)
        return None if s is None else role in s.readers

    def source_labels(self, name: str) -> frozenset[str] | None:
        s = self.sources.get(name)
        if s is None:
            return None
        if s.label is not None:
            return frozenset({s.label})
        if s.kind == "dir":
            return frozenset({OBSERVED})         # a directory source with no label: observed
        return s.labels or None                  # a structured source: its rule's range

    # the writer's view -------------------------------------------------------------------

    def owner(self, path: str) -> Source | None:
        """The source whose space a path lies in (R8), if any."""
        for s in self.sources.values():
            if s.owns(path):
                return s
        return None

    def may_write(self, role: str, place: str, path: str) -> bool:
        """R3: the role writes the place only under its prefixes, the path normalized."""
        r = self.roles.get(role)
        if r is None or not normal(path):
            return False
        return any(path.startswith(p) for p in r.prefixes.get(place, ()))

    def may_retire(self, role: str, place: str, path: str) -> bool:
        """R3 for a retire: the role's write prefixes, and the prefixes it only retires."""
        if self.may_write(role, place, path):
            return True
        r = self.roles.get(role)
        if r is None or not normal(path):
            return False
        return any(path.startswith(p) for p in r.retire_only.get(place, ()))


def normal(path: str) -> bool:
    """A path the writer takes: no `.` or `..` or empty component, and no character that is not
    printed as itself (a control character, DEL, a format character such as a bidirectional
    override, a line or paragraph separator), so no path displays as another."""
    if not path or any(unicodedata.category(c) in ("Cc", "Cf", "Zl", "Zp") for c in path):
        return False
    parts = path.split("/")
    inner = parts[1:] if path.startswith("/") else parts
    return all(p not in ("", ".", "..") for p in inner)


def _classes(s: Stratum) -> frozenset[str]:
    return frozenset(str(c) for c in STRATUM_CLASSES[s])


# The places and the jobs depend on no configuration: the compiler reads them to admit a script
# (R1) before any source is opened.
PLACES: Mapping[str, Place] = {
    "mirror_authored": Place("mirror_authored", Stratum.MIRROR_AUTHORED,
                             _classes(Stratum.MIRROR_AUTHORED), versions=True,
                             action="ingest_note"),
    "dialogue": Place("dialogue", Stratum.DIALOGUE, _classes(Stratum.DIALOGUE), versions=False,
                      action="capture"),
    "observed": Place("observed", Stratum.OBSERVED, _classes(Stratum.OBSERVED), versions=False,
                      action="capture"),
    "curated": Place("curated", Stratum.CURATED, _classes(Stratum.CURATED), versions=False,
                     action="ingest_curated"),
}
JOBS: Mapping[str, Job] = {
    "dream": Job("dream", "dream", (Stratum.INTERPRETED,), propose=True),
    "curate": Job("curate", "curate", (Stratum.INTERPRETED,), propose=True),
    "relate": Job("relate", "relate", (Stratum.INTERPRETED,), propose=True, args={"pairs": 50}),
    "code_sync": Job("code_sync", "code_sync", (Stratum.REFERENCE,), clock=Clock.COMMIT),
    "chat_sync": Job("chat_sync", "chat_sync", (Stratum.DIALOGUE_TRANSCRIPT,),
                     fibers=frozenset({"C"}), clock=Clock.COMMIT),
    "code_observe": Job("code_observe", "code_observe", (Stratum.REFERENCE,),
                        fibers=frozenset({"F"}), clock=Clock.COMMIT),
}
# The library scripts the queue treats as its own: those run in the interactive lane (a capture),
# so a role's syncs never hold its captures, and those whose bare call is one of the queue's
# coalescing kinds, so a request for a sync coalesces with the watcher's and the heartbeat's rows.
INTERACTIVE: frozenset[str] = frozenset({"capture"})
COALESCING: Mapping[str, str] = {"sync_vault": "vault_sync", "sync_dialogue": "dialogue_sync"}


# ── the table of this palace ────────────────────────────────────────────────────────────────

def _dialogue_source(cfg: Config, reader: str, argv: tuple[str, ...]) -> Source:
    handoff = cfg.paths.data_dir / "handoff" / "dialogue" / f"{reader}.json"

    def items_of(doc: Any) -> Iterator[dict[str, Any]]:
        for chat in (doc.get("chats", []) if isinstance(doc, dict) else []):
            for turn in chat.get("turns", []):
                ts = turn.get("timestamp")
                yield {"chat_id": str(chat["chat_id"]), "id": str(turn["id"]),
                       "role": str(turn["role"]), "content": str(turn["content"]),
                       # a time of zero or less is no time: the reader did not know it
                       "timestamp": int(ts) if isinstance(ts, (int, float)) and ts > 0 else None,
                       "conversation": f"{reader}/{chat['chat_id']}"}

    def title_of(it: Mapping[str, Any]) -> str:
        """The turn's title, the source's rule as the first form's capture wrote it: its chat,
        its time (its id when the reader gave no time), whose it is."""
        ts = it.get("timestamp")
        when = (datetime.fromtimestamp(ts, UTC).isoformat(timespec="seconds")
                if isinstance(ts, int) else str(it["id"]))
        return f"dialogue/{it['conversation']}/{when} ({it['role']})"

    def cursor_of(doc: Any) -> int:
        chats = doc.get("chats", []) if isinstance(doc, dict) else []
        return max((int(c.get("updated_at") or 0) for c in chats), default=0)

    return Source(
        name=f"dialogue/{reader}", kind="file", location=handoff, format="json",
        readers=frozenset({"cli", "ambassador"}),
        items_of=items_of,
        path_of=lambda it: f"dialogue/{reader}/{it['chat_id']}/{it['id']}",
        label_of=lambda it: AUTHORED_DIALOGUE if it["role"] == "user" else OBSERVED,
        labels=frozenset({AUTHORED_DIALOGUE, OBSERVED}),
        space=f"dialogue/{reader}/",
        refresh=(sys.executable, *argv, "--out", str(handoff)),
        cursor_of=cursor_of, title_of=title_of)


def build_table(cfg: Config) -> Table:
    """This palace's table, from its configuration."""
    from core.relations import RELATIONS

    vault = Path(str(cfg.ingestion.vault.path)).expanduser()
    repo = Path(REPO_ROOT)
    sources = {
        "vault": Source(name="vault", kind="dir", location=vault, format="markdown",
                        readers=frozenset({"cli", "ambassador"}),
                        patterns=(cfg.ingestion.vault.pattern,), exclude=DEFAULT_EXCLUDE_DIRS,
                        label=AUTHORED_SOLO, identity="id"),
        "docs": Source(name="docs", kind="dir", location=repo, format="markdown",
                       readers=frozenset({"cli", "ambassador"}),
                       patterns=("CONSTITUTION.md", "CONVENTIONS.md", "docs/**/*.md"),
                       label=CURATED),
        "dialogue/openwebui": _dialogue_source(
            cfg, "openwebui", ("-m", "edge.openwebui", "--container", "lmtune-webui")),
        "dialogue/opencode": _dialogue_source(cfg, "opencode", ("-m", "edge.opencode_sessions")),
    }

    places, jobs = PLACES, JOBS
    every = {p: ("",) for p in places}
    vault_prefix = str(vault) + "/"
    repo_prefix = str(repo) + "/"
    legacy = (LEGACY_DIALOGUE + "ambassador/",)
    roles = {
        "cli": Role("cli", every, budget=50_000_000_000,
                    retires=frozenset(str(p) for p in Provenance)),
        "ambassador": Role("ambassador", {
            "mirror_authored": (vault_prefix,),
            "dialogue": ("dialogue/openwebui/", "dialogue/opencode/",
                         "dialogue/ingress/ambassador/"),
            "observed": ("dialogue/ingress/ambassador/",),
            "curated": (repo_prefix,),
        }, budget=100_000_000, retires=frozenset({OBSERVED}),
            retire_only={"dialogue": legacy, "observed": legacy}),
    }
    return Table(sources=sources, places=places, jobs=jobs, roles=roles, relations=RELATIONS,
                 interactive=INTERACTIVE, coalescing=COALESCING)


# The first form's stored prefix for the turns a role's commands mint, read and retired but never
# written (identities are permanent): rows under it keep their role's namespace.
LEGACY_DIALOGUE = "dialogue/door/"


def write_cursor(source: Source, doc: Any) -> None:
    """Record the newest change a structured source showed, once a plan that read it has landed
    (the heartbeat reads it to tell a failed sync from a done one)."""
    if source.cursor_of is None:
        return
    mark = source.location.with_suffix(".synced")
    mark.write_text(json.dumps({"latest": source.cursor_of(doc),
                                "at": datetime.now(UTC).isoformat(timespec="seconds")}))
