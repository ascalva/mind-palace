"""Destroying a named instance, and what it leaves: the shared cache's open content
(dn-instance-lifecycle §6).

The cache is a channel between instances, so what enters it is fixed here, by an allow-list, and
everything else is refused. An item is **open** when its catalog path lies in the space of an
open-corpus source (`corpus/<name>/`) or a repository source (`code/<name>/`), or its class is
`curated`. Then a raw object enters when a catalog row, active or tombstoned, names its digest at
an open item's path; a vector enters when its atom is held, current or not, by an open item's
occupancy in the plane; and a source file enters when it is a downloaded file of an open-corpus
source (a stream's named parts, its manifest and its items' metadata; never a cursor or a
checkpoint). Nothing of the mirror's notes, the dialogue, an observed item outside an open-corpus
source, or a transcript enters, and no digest a purge recorded. An entry carries no path, title or
class, so it says only that some open item held these bytes, which that item's source holds in
public.

A destroy fills the cache by this selection and then removes the instance's root, without
following a symbolic link out of it. `palace cache fill` is the same fill without the removal.
Both refuse when the configured embedder is not the geometry the plane recorded, so a vector is
filed only under the key of the embedder that made it. The plan counts what a fill would add and
holds no vector; the fill reads the vectors in batches, so neither grows with the plane.

A root is removed only when it holds nothing but the instance's own state: every top-level entry
is one the instance's namespaces name, every entry of its data directory is in the class table,
nothing below it is a git repository, and no other instance declared on this host has its root
at, inside or around it.
"""

from __future__ import annotations

import json
import os
import shutil
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from core.ingest.table import CODE_SPACE, CORPUS
from core.kernel.provenance import Provenance
from core.stores.cache import Cache, key_of, same_volume_free

#: Free space the cache's volume keeps beyond what a fill adds.
FREE_MARGIN = 1 << 30
#: Vectors a fill reads from the plane and writes to the cache at once.
FILL_BATCH = 2048
_CORPUS_SPACE = f"{CORPUS}/"


def is_open(source_path: str, provenance: str) -> bool:
    """Whether an item's content may enter the cache (decision D9)."""
    return (source_path.startswith(_CORPUS_SPACE) or source_path.startswith(CODE_SPACE)
            or provenance == Provenance.CURATED.value)


@dataclass
class FillPlan:
    """What a fill would put in the cache, before any of it is written."""

    raw: list[str] = field(default_factory=list)
    raw_bytes: int = 0
    atoms: list[str] = field(default_factory=list)     # the atoms whose vectors a fill adds
    dim: int = 0
    key: str = ""
    key_fields: dict[str, Any] = field(default_factory=dict)
    sources: dict[str, list[str]] = field(default_factory=dict)
    source_bytes: int = 0
    refused_purged: int = 0

    @property
    def bytes(self) -> int:
        # the cache stores a vector as float64 (`Cache.put_vectors`)
        return self.raw_bytes + self.source_bytes + 8 * self.dim * len(self.atoms)

    def __str__(self) -> str:
        files = sum(len(f) for f in self.sources.values())
        return (f"{len(self.raw)} raw object(s) ({self.raw_bytes:,} bytes), "
                f"{len(self.atoms)} vector(s), {files} source file(s) of "
                f"{len(self.sources)} source(s) ({self.source_bytes:,} bytes); "
                f"{self.refused_purged} purged digest(s) refused")


def _catalog_rows(cfg: Any) -> list[tuple[str, str, str]]:
    """Every catalog row, active or tombstoned: (path, digest, class), read only."""
    path = Path(cfg.paths.vault_catalog)
    if not path.is_file():
        return []
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        return [(str(p), str(d), str(c)) for p, d, c in conn.execute(
            "SELECT source_path, digest, provenance FROM vault_files")]
    finally:
        conn.close()


def _open_atoms(cfg: Any, open_paths: set[str], purged: set[str]) -> set[str]:
    """The atoms an open item's occupancy holds, current or not, in any class, read only."""
    from core.stores.plane import OCC, PLANE_FILE

    db = Path(cfg.paths.vector_store) / PLANE_FILE
    if not db.is_file() or not open_paths:
        return set()
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    atoms: set[str] = set()
    try:
        for occ in OCC.values():
            for path, digest, atom in conn.execute(
                    f"SELECT source_path, digest, atom_id FROM {occ}"):
                if str(path) in open_paths and str(digest) not in purged:
                    atoms.add(str(atom))
    finally:
        conn.close()
    return atoms


def _source_files(base: Path) -> list[str]:
    """A source's downloaded files, relative to its directory: the stream's manifest and the
    parts it names, and the items' metadata. Cursors and checkpoints are not downloads."""
    man = base / "stream" / "manifest.json"
    if not man.is_file():
        return []
    parts = [str(p["file"]) for p in json.loads(man.read_text(encoding="utf-8"))["parts"]]
    files = ["stream/manifest.json", *(f"stream/{f}" for f in parts)]
    if (base / "meta" / "items.jsonl").is_file():
        files.append("meta/items.jsonl")
    return [f for f in files if (base / f).is_file()]


def geometry_refusal(cfg: Any) -> str | None:
    """Why this instance's vectors may not be filed under its configured key, or None: the plane
    recorded another geometry (model, document template, dimension), as it does after a change
    of embedder in the overlay and before `palace reembed`. Read only."""
    from core.stores.plane import PLANE_FILE
    from core.stores.vectorstore import fingerprint_of

    db = Path(cfg.paths.vector_store) / PLANE_FILE
    if not cfg.embedding.enabled or not db.is_file():
        return None
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        row = conn.execute("SELECT value FROM meta WHERE key = 'fingerprint'").fetchone()
    except sqlite3.Error:
        row = None
    finally:
        conn.close()
    mine = fingerprint_of(cfg).as_json()
    if row is not None and str(row[0]) != mine:
        return (f"the plane's vectors came from {row[0]}, and the configured embedder is {mine}; "
                "a fill would file them under the configured embedder's key. Re-embed first "
                "(`palace reembed --confirm`), or restore the configuration")
    return None


def plan_fill(cfg: Any, cache: Cache) -> FillPlan:
    """The fill this instance would make: its open raw objects, the atoms whose vectors it adds,
    and its source files. Counts only; no vector is read."""
    from core.kernel.stores.rawstore import RawStore
    from core.stores.plane import GeometryMismatch

    why = geometry_refusal(cfg)
    if why is not None:
        raise GeometryMismatch(why)

    purged = cache.purged()
    plan = FillPlan()
    rows = _catalog_rows(cfg)
    open_rows = [(p, d) for p, d, c in rows if is_open(p, c)]
    raw = RawStore(Path(cfg.paths.raw_store)) if Path(cfg.paths.raw_store).is_dir() else None
    for digest in sorted({d for _, d in open_rows}):
        if digest in purged:
            plan.refused_purged += 1
            continue
        if raw is not None and raw.exists(digest) and not cache.has_raw(digest):
            plan.raw.append(digest)
            plan.raw_bytes += raw._path(digest).stat().st_size
    if cfg.embedding.enabled:
        atoms = _open_atoms(cfg, {p for p, _ in open_rows}, purged)
        plan.key, plan.key_fields = key_of(cfg)
        plan.atoms = sorted(atoms - cache.vector_ids(plan.key))
        plan.dim = int(cfg.embedding.dim)
    if cfg.ingestion.corpus.enabled:
        root = Path(cfg.ingestion.corpus.root)
        for name in cfg.ingestion.corpus.sources:
            base = root / name
            have = {m["file"]: m["size"] for m in cache.source_manifest(name)}
            files = [f for f in _source_files(base)
                     if have.get(f) != (base / f).stat().st_size]
            if files:
                plan.sources[name] = files
                plan.source_bytes += sum((base / f).stat().st_size for f in files)
    return plan


@dataclass(frozen=True)
class FillReport:
    raw: int
    vectors: int
    source_files: int

    def __str__(self) -> str:
        return (f"{self.raw} raw object(s), {self.vectors} vector(s), "
                f"{self.source_files} source file(s) added")


def fill(cfg: Any, cache: Cache, plan: FillPlan) -> FillReport:
    """Write a plan into the cache."""
    from core.kernel.stores.rawstore import RawStore

    raw = RawStore(Path(cfg.paths.raw_store))
    added_raw = sum(cache.put_raw(d, raw.get(d)) for d in plan.raw)
    added_vec = 0
    if plan.atoms:
        from core.stores.vectorstore import open_vector_store

        atoms = open_vector_store(cfg).plane.atoms
        for i in range(0, len(plan.atoms), FILL_BATCH):
            payload = atoms.payload(plan.atoms[i:i + FILL_BATCH])
            added_vec += cache.put_vectors(plan.key, plan.key_fields,
                                           {a: v for a, (_text, v) in payload.items()})
    files = 0
    root = Path(cfg.ingestion.corpus.root)
    for name, rels in plan.sources.items():
        files += cache.put_source_files(name, root / name, rels)
    return FillReport(raw=int(added_raw), vectors=added_vec, source_files=files)


# ── destroy's refusals ─────────────────────────────────────────────────────────────────────


def _inside(path: Path, root: Path) -> bool:
    return path == root or root in path.parents


def link_out(root: Path) -> Path | None:
    """The first symbolic link under `root` whose target lies outside it, or None."""
    return _scan(root)[0]


def _scan(root: Path) -> tuple[Path | None, Path | None]:
    """One walk of `root`, following no link: the first symbolic link whose target lies outside
    it, and the first `.git` below it (a repository's directory or a worktree's file)."""
    real_root = Path(os.path.realpath(root))
    out: Path | None = None
    git: Path | None = None
    for here, dirs, files in os.walk(root, followlinks=False):
        for name in [*dirs, *files]:
            p = Path(here) / name
            if git is None and name == ".git":
                git = p
            if out is None and p.is_symlink() \
                    and not _inside(Path(os.path.realpath(p)), real_root):
                out = p
        if out is not None and git is not None:
            break
    return out, git


def foreign_entries(cfg: Any) -> list[str]:
    """What the root holds that is not this instance's own state: a top-level entry no path of its
    namespaces lies at or under (`namespaces_of(cfg).paths`, the data directory among them), and
    an entry of its data directory the class table does not name."""
    from core.kernel.config.loader import namespaces_of
    from ops.lifecycle.inventory import unclassified

    root = Path(cfg.instance.root)
    if not root.is_dir():
        return []
    real_root = Path(os.path.realpath(root))
    own: set[str] = set()
    for p in {*namespaces_of(cfg).paths, Path(cfg.paths.data_dir)}:
        real = Path(os.path.realpath(p))
        if real_root in real.parents:
            own.add(real.relative_to(real_root).parts[0])
    out = sorted(e.name + ("/" if e.is_dir() else "") for e in root.iterdir()
                 if e.name not in own)
    data = Path(cfg.paths.data_dir)
    out += [f"{data.name}/{p.name}" for p in unclassified(cfg)]
    return out


def top_entries(root: Path) -> list[str]:
    """The root's top-level entries, for the dry run."""
    if not root.is_dir():
        return []
    return sorted(e.name + ("/" if e.is_dir() and not e.is_symlink() else "")
                  for e in root.iterdir())


def other_roots(cfg: Any) -> list[tuple[str, Path, bool]]:
    """The root of every other instance declared on this host, and whether it is a named one: the
    default instance's (the checkout) and each other overlay's under config/instances/."""
    from core.kernel.config import loader

    out: list[tuple[str, Path, bool]] = []
    for name, other in loader._declared_instances(Path(os.devnull)):
        if other.instance.id != cfg.instance.id:
            out.append((name, Path(other.instance.root), other.instance.named))
    return out


def refusals(cfg: Any, cache: Cache, *, installed: bool, home: Path | None = None) -> list[str]:
    """Why this instance may not be destroyed, empty when it may. The live run and the lock are
    the launcher's to check; these are the configuration's and the disk's."""
    from core.kernel.config import loader

    if not cfg.instance.named:
        return ["the default instance is never destroyed by this command (decision D1)"]
    out: list[str] = []
    root = Path(cfg.instance.root)
    real = Path(os.path.realpath(root))
    home_root = Path(os.path.realpath(home if home is not None
                                      else Path.home() / ".mind-palace"))
    cache_real = Path(os.path.realpath(cache.root))
    if installed:
        out.append(f"a LaunchAgent with its label ({cfg.instance.label('palace')}) is installed; "
                   "remove it first")
    derived = Path(os.path.realpath(Path(loader.REPO_ROOT) / "instances" / cfg.instance.id))
    tree = loader._working_tree_of(real)
    if tree is not None and real != derived:
        out.append(f"its root {root} lies inside the git working tree {tree}")
    if real == home_root:
        out.append(f"its root {root} is the home root itself")
    if _inside(cache_real, real):
        out.append(f"its root {root} holds the cache {cache.root}")
    if _inside(real, cache_real):
        out.append(f"its root {root} lies inside the cache {cache.root}")
    for name, other, other_named in other_roots(cfg):
        other_real = Path(os.path.realpath(other))
        # a derived root lies inside the default instance's, the checkout (§10 item 5)
        if _inside(other_real, real) or (other_named and _inside(real, other_real)):
            out.append(f"its root {root} is at, inside or around the root {other} of the "
                       f"instance {name}")
    if root.is_symlink():
        out.append(f"its root {root} is a symbolic link; destroy the directory it names instead")
    elif root.exists():
        link, git = _scan(root)
        if link is not None:
            out.append(f"{link} is a symbolic link out of the root; remove it first")
        if git is not None:
            out.append(f"{git.parent} below the root is a git repository; move it out first")
        foreign = foreign_entries(cfg)
        if foreign:
            out.append(f"its root {root} holds what is not the instance's own state: "
                       + ", ".join(foreign) + "; move it out first")
    why = geometry_refusal(cfg)
    if why is not None:
        out.append(why)
    return out


def keychain_items(cfg: Any) -> list[str]:
    """The secret item names this instance reads, for the owner to remove by hand."""
    from core.kernel.config.loader import namespaces_of

    return sorted(namespaces_of(cfg).secrets)


def room(cache: Cache, plan: FillPlan) -> str | None:
    """Why the cache's volume cannot take the fill, or None."""
    free = same_volume_free(cache.root)
    if free < plan.bytes + FREE_MARGIN:
        return (f"the cache's volume has {free:,} bytes free; the fill needs {plan.bytes:,} and "
                f"a margin of {FREE_MARGIN:,}")
    return None


def remove_root(root: Path) -> None:
    """Remove the instance's root. `rmtree` unlinks a symbolic link inside it and never follows
    one; a root that is itself a link is refused before this (`refusals`)."""
    if root.is_symlink():
        raise RuntimeError(f"{root} is a symbolic link")
    shutil.rmtree(root)
