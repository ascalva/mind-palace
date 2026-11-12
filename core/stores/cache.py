"""The shared cache: content-addressed entries one instance leaves and another takes back
(dn-instance-lifecycle §6.3 to §6.6).

One place, `~/.mind-palace/cache`, shared by every instance of the machine's user, under the home
root and outside every instance's root and every checkout:

    LAYOUT                       the layout's version
    raw/<aa>/<digest>            a raw object, the raw store's own layout
    vectors/<key>/atoms.sqlite   atom id -> the vector as the plane returns it; <key> names the
                                 embedder, its fields in vectors/<key>/key.json
    sources/<source>/<file>      a downloaded source file, with sources/<source>/MANIFEST
    purged.sqlite                the digests a purge erased; nothing enters under one again
    uses.sqlite                  when each entry was last put or taken, for retention

An entry holds no path, no title and no class: a raw object is named by its digest, a vector by
its atom id, the hash of its text, and the text is not stored with the vector. The address is the
whole trust decision: a raw object is checked against its digest when it is taken, and a mismatch
is refused and the entry deleted. Which content may enter is decided by the instance that fills
the cache (`ops/lifecycle/destroy.py`), by an allow-list of open sources; this module stores and
returns entries, refuses a purged digest, and erases what a purge names.

Reading never creates the cache: a lookup in a cache that does not exist finds nothing. The
location is a constant of the code (`cache_home`), as the instances' home is; the tests pass a
temporary directory to the constructor.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import time
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

LAYOUT = 1
RETENTION_DAYS = 180
_BATCH = 400


def cache_home() -> Path:
    """The shared cache's one location, under the home root every instance's home is under."""
    return Path.home() / ".mind-palace" / "cache"


def vector_key(model: str, template: str, dim: int, backend: str) -> tuple[str, dict[str, Any]]:
    """The vector namespace's key: the plane's geometry (model, document template, dimension)
    with the runtime backend that served it, hashed. A vector is reused only under the same key,
    so two geometries never mix (falsifier LCF-6 names when the key would need the model file)."""
    fields: dict[str, Any] = {"model": model, "template": template, "dim": int(dim),
                              "backend": backend}
    digest = hashlib.sha256(json.dumps(fields, sort_keys=True).encode("utf-8")).hexdigest()
    return digest[:24], fields


def key_of(cfg: Any) -> tuple[str, dict[str, Any]]:
    """An instance's vector key: its configured geometry and embedding backend."""
    e = cfg.embedding
    return vector_key(e.model, e.document_template, e.dim, cfg.runtime.embedding_backend)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _batches(items: Sequence[str]) -> Iterable[Sequence[str]]:
    for i in range(0, len(items), _BATCH):
        yield items[i:i + _BATCH]


def _ro(path: Path) -> sqlite3.Connection | None:
    """A read-only connection to `path`, or None when it does not exist (nothing is created)."""
    if not path.is_file():
        return None
    return sqlite3.connect(f"file:{path}?mode=ro", uri=True)


@dataclass(frozen=True)
class CacheSize:
    entries: int
    bytes: int


@dataclass(frozen=True)
class ForgetReport:
    raw_removed: bool
    vectors_removed: int


@dataclass
class Cache:
    """The cache under `root`. Every write takes the entry whole (write, then rename) and is
    idempotent; every read checks what it returns."""

    root: Path

    # ── plumbing ───────────────────────────────────────────────────────────────────────────

    @property
    def exists(self) -> bool:
        return self.root.is_dir()

    def _ensure(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        layout = self.root / "LAYOUT"
        if not layout.exists():
            layout.write_text(f"{LAYOUT}\n", encoding="utf-8")

    def _db(self, name: str, ddl: str) -> sqlite3.Connection:
        self._ensure()
        conn = sqlite3.connect(str(self.root / name))
        conn.executescript(ddl)
        return conn

    def _uses(self) -> sqlite3.Connection:
        return self._db("uses.sqlite", "CREATE TABLE IF NOT EXISTS uses (kind TEXT NOT NULL, "
                        "id TEXT NOT NULL, last REAL NOT NULL, PRIMARY KEY (kind, id));")

    def _touch(self, kind: str, ids: Iterable[str], *, now: float | None = None) -> None:
        ids = list(ids)
        if not ids or not self.exists:
            return
        at = time.time() if now is None else now
        conn = self._uses()
        try:
            with conn:
                conn.executemany("INSERT OR REPLACE INTO uses (kind, id, last) VALUES (?, ?, ?)",
                                 [(kind, i, at) for i in ids])
        finally:
            conn.close()

    def _purged_db(self) -> sqlite3.Connection:
        return self._db("purged.sqlite", "CREATE TABLE IF NOT EXISTS purged (digest TEXT "
                        "PRIMARY KEY, at REAL NOT NULL);")

    # ── purged digests ─────────────────────────────────────────────────────────────────────

    def purged(self) -> set[str]:
        conn = _ro(self.root / "purged.sqlite")
        if conn is None:
            return set()
        try:
            return {str(r[0]) for r in conn.execute("SELECT digest FROM purged")}
        finally:
            conn.close()

    def is_purged(self, digest: str) -> bool:
        return digest in self.purged()

    # ── raw objects ────────────────────────────────────────────────────────────────────────

    def _raw_path(self, digest: str) -> Path:
        return self.root / "raw" / digest[:2] / digest

    def has_raw(self, digest: str) -> bool:
        return self._raw_path(digest).is_file()

    def raw_digests(self) -> set[str]:
        d = self.root / "raw"
        if not d.is_dir():
            return set()
        return {p.name for p in d.glob("*/*") if p.is_file() and not p.name.endswith(".tmp")}

    def raw(self, digest: str) -> bytes | None:
        """The raw object `digest`, checked against its address; None when the cache lacks it. An
        entry whose bytes do not hash to its name is refused and deleted."""
        p = self._raw_path(digest)
        if not p.is_file():
            return None
        data = p.read_bytes()
        if _sha256(data) != digest:
            p.unlink(missing_ok=True)
            return None
        self._touch("raw", [digest])
        return data

    def put_raw(self, digest: str, data: bytes) -> bool:
        """Store a raw object under its digest; False when it is held already, purged, or its
        bytes are not the digest's."""
        if _sha256(data) != digest or self.is_purged(digest):
            return False
        p = self._raw_path(digest)
        if p.is_file():
            self._touch("raw", [digest])
            return False
        self._ensure()
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_name(p.name + ".tmp")
        tmp.write_bytes(data)
        tmp.replace(p)
        self._touch("raw", [digest])
        return True

    # ── vectors ────────────────────────────────────────────────────────────────────────────

    def _vector_dir(self, key: str) -> Path:
        return self.root / "vectors" / key

    def vector_keys(self) -> list[str]:
        d = self.root / "vectors"
        return sorted(p.name for p in d.iterdir() if p.is_dir()) if d.is_dir() else []

    def vectors(self, key: str, atom_ids: Sequence[str]) -> dict[str, list[float]]:
        """The cached vectors of these atoms under `key`; an atom the cache lacks is absent."""
        conn = _ro(self._vector_dir(key) / "atoms.sqlite")
        if conn is None or not atom_ids:
            if conn is not None:
                conn.close()
            return {}
        out: dict[str, list[float]] = {}
        try:
            for batch in _batches(list(dict.fromkeys(atom_ids))):
                marks = ", ".join("?" for _ in batch)
                for aid, blob in conn.execute(
                        f"SELECT atom_id, vector FROM atoms WHERE atom_id IN ({marks})",
                        list(batch)):
                    out[str(aid)] = np.frombuffer(blob, dtype=np.float64).tolist()
        finally:
            conn.close()
        self._touch(f"vector:{key}", out)
        return out

    def vector_ids(self, key: str) -> set[str]:
        conn = _ro(self._vector_dir(key) / "atoms.sqlite")
        if conn is None:
            return set()
        try:
            return {str(r[0]) for r in conn.execute("SELECT atom_id FROM atoms")}
        finally:
            conn.close()

    def put_vectors(self, key: str, fields: Mapping[str, Any],
                    vectors: Mapping[str, Sequence[float]]) -> int:
        """Store vectors under `key` (its fields written beside them); returns those added."""
        if not vectors:
            return 0
        self._ensure()
        d = self._vector_dir(key)
        d.mkdir(parents=True, exist_ok=True)
        meta = d / "key.json"
        if not meta.exists():
            meta.write_text(json.dumps(dict(fields), sort_keys=True), encoding="utf-8")
        conn = sqlite3.connect(str(d / "atoms.sqlite"))
        try:
            conn.execute("CREATE TABLE IF NOT EXISTS atoms (atom_id TEXT PRIMARY KEY, "
                         "dim INTEGER NOT NULL, vector BLOB NOT NULL)")
            added = 0
            with conn:
                for aid, vec in vectors.items():
                    arr = np.asarray(list(vec), dtype=np.float64)
                    cur = conn.execute("INSERT OR IGNORE INTO atoms (atom_id, dim, vector) "
                                       "VALUES (?, ?, ?)", [aid, int(arr.size), arr.tobytes()])
                    added += cur.rowcount
        finally:
            conn.close()
        self._touch(f"vector:{key}", vectors)
        return added

    def view(self, key: str) -> VectorCache:
        return VectorCache(self, key)

    # ── downloaded source files ────────────────────────────────────────────────────────────

    def _source_dir(self, source: str) -> Path:
        if not source or "/" in source or source.startswith("."):
            raise ValueError(f"not a source name: {source!r}")
        return self.root / "sources" / source

    def source_manifest(self, source: str) -> list[dict[str, Any]]:
        f = self._source_dir(source) / "MANIFEST"
        if not f.is_file():
            return []
        return list(json.loads(f.read_text(encoding="utf-8")))

    def sources(self) -> list[str]:
        d = self.root / "sources"
        return sorted(p.name for p in d.iterdir() if p.is_dir()) if d.is_dir() else []

    def put_source_files(self, source: str, base: Path, files: Sequence[str]) -> int:
        """Copy `files` (relative to `base`) into the source's namespace, each named in its
        MANIFEST with its size, SHA-256 and when it was fetched; returns the files added."""
        if not files:
            return 0
        self._ensure()
        d = self._source_dir(source)
        manifest = {m["file"]: m for m in self.source_manifest(source)}
        added = 0
        for rel in files:
            if rel.startswith("/") or ".." in Path(rel).parts:
                raise ValueError(f"a source file is relative to its source: {rel!r}")
            src = base / rel
            sha = _file_sha256(src)
            if rel in manifest and manifest[rel]["sha256"] == sha:
                continue
            dest = d / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            tmp = dest.with_name(dest.name + ".tmp")
            shutil.copyfile(src, tmp)
            tmp.replace(dest)
            manifest[rel] = {"file": rel, "size": src.stat().st_size, "sha256": sha,
                             "fetched": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                                      time.gmtime(src.stat().st_mtime))}
            added += 1
        (d / "MANIFEST").write_text(json.dumps(sorted(manifest.values(),
                                                      key=lambda m: m["file"]), indent=1),
                                    encoding="utf-8")
        self._touch("source", [source])
        return added

    def take_source(self, source: str, dest: Path) -> int:
        """Copy the source's cached files into `dest`, each one whose size and SHA-256 match its
        manifest row; a file that does not match is refused and its entry deleted. Returns the
        files copied. Files `dest` already holds are left as they are."""
        d = self._source_dir(source)
        copied = 0
        for m in self.source_manifest(source):
            src, out = d / m["file"], dest / m["file"]
            if out.exists() or not src.is_file():
                continue
            if src.stat().st_size != int(m["size"]) or _file_sha256(src) != m["sha256"]:
                src.unlink(missing_ok=True)
                continue
            out.parent.mkdir(parents=True, exist_ok=True)
            tmp = out.with_name(out.name + ".tmp")
            shutil.copyfile(src, tmp)
            tmp.replace(out)
            copied += 1
        if copied:
            self._touch("source", [source])
        return copied

    # ── erasure ────────────────────────────────────────────────────────────────────────────

    def forget(self, digest: str, atom_ids: Iterable[str]) -> ForgetReport:
        """What a purge of `digest` owes the cache (§6.6): the raw object, and the vector of every
        atom of its chunks under every key, deleted; the digest recorded, so no fill puts it back.
        The atoms are deleted and not recorded, since an atom's text may be held by an open item
        whose content is public."""
        atoms = list(dict.fromkeys(atom_ids))
        raw_removed = False
        p = self._raw_path(digest)
        if p.is_file():
            p.unlink()
            raw_removed = True
        removed = 0
        for key in self.vector_keys():
            f = self._vector_dir(key) / "atoms.sqlite"
            if not f.is_file() or not atoms:
                continue
            conn = sqlite3.connect(str(f))
            try:
                with conn:
                    for batch in _batches(atoms):
                        marks = ", ".join("?" for _ in batch)
                        removed += conn.execute(
                            f"DELETE FROM atoms WHERE atom_id IN ({marks})", list(batch)).rowcount
            finally:
                conn.close()
        conn = self._purged_db()
        try:
            with conn:
                conn.execute("INSERT OR IGNORE INTO purged (digest, at) VALUES (?, ?)",
                             [digest, time.time()])
        finally:
            conn.close()
        return ForgetReport(raw_removed=raw_removed, vectors_removed=removed)

    # ── retention and reporting ────────────────────────────────────────────────────────────

    def sizes(self) -> dict[str, CacheSize]:
        """The cache's size by namespace: raw, each vector key, each source."""
        out: dict[str, CacheSize] = {}

        def size_of(paths: Iterable[Path]) -> CacheSize:
            files = [p for p in paths if p.is_file()]
            return CacheSize(len(files), sum(p.stat().st_size for p in files))

        out["raw"] = size_of((self.root / "raw").glob("*/*"))
        for key in self.vector_keys():
            n = len(self.vector_ids(key))
            f = self._vector_dir(key) / "atoms.sqlite"
            out[f"vectors/{key}"] = CacheSize(n, f.stat().st_size if f.is_file() else 0)
        for source in self.sources():
            m = self.source_manifest(source)
            out[f"sources/{source}"] = CacheSize(len(m), sum(int(e["size"]) for e in m))
        return out

    def stale(self, *, days: int = RETENTION_DAYS,
              now: float | None = None) -> dict[str, list[str]]:
        """The entries not put or taken for `days`, by kind: what a prune would remove."""
        at = time.time() if now is None else now
        cutoff = at - days * 86400
        conn = _ro(self.root / "uses.sqlite")
        last: dict[tuple[str, str], float] = {}
        if conn is not None:
            try:
                last = {(str(k), str(i)): float(t)
                        for k, i, t in conn.execute("SELECT kind, id, last FROM uses")}
            finally:
                conn.close()

        def old(kind: str, ident: str) -> bool:
            return last.get((kind, ident), 0.0) < cutoff

        out: dict[str, list[str]] = {"raw": sorted(d for d in self.raw_digests()
                                                   if old("raw", d))}
        for key in self.vector_keys():
            out[f"vector:{key}"] = sorted(a for a in self.vector_ids(key)
                                          if old(f"vector:{key}", a))
        out["source"] = [s for s in self.sources() if old("source", s)]
        return out

    def prune(self, *, days: int = RETENTION_DAYS, now: float | None = None) -> int:
        """Remove the entries not put or taken for `days`; returns how many."""
        stale = self.stale(days=days, now=now)
        removed = 0
        for digest in stale["raw"]:
            self._raw_path(digest).unlink(missing_ok=True)
            removed += 1
        for kind, ids in stale.items():
            if not kind.startswith("vector:") or not ids:
                continue
            f = self._vector_dir(kind.split(":", 1)[1]) / "atoms.sqlite"
            conn = sqlite3.connect(str(f))
            try:
                with conn:
                    for batch in _batches(ids):
                        marks = ", ".join("?" for _ in batch)
                        removed += conn.execute(
                            f"DELETE FROM atoms WHERE atom_id IN ({marks})", list(batch)).rowcount
            finally:
                conn.close()
        for source in stale["source"]:
            shutil.rmtree(self._source_dir(source), ignore_errors=True)
            removed += 1
        return removed


@dataclass(frozen=True)
class VectorCache:
    """The cache's vectors under one key: what the vector drain looks an atom up in before it
    calls the embedder (§6.5)."""

    cache: Cache
    key: str

    def vectors(self, atom_ids: Sequence[str]) -> dict[str, list[float]]:
        return self.cache.vectors(self.key, atom_ids)


def with_cache(stores: Any, cfg: Any, cache: Cache | None = None) -> Any:
    """Give the writer's stores their two reuse paths (§6.5), and return them: the raw store
    looks a miss up in the cache by digest, and, in an instance that embeds, the vector drain
    looks an atom up under the instance's embedder key before it calls the embedder. The cache is
    the shared one unless given. Idempotent."""
    shared = cache if cache is not None else Cache(cache_home())
    raw = getattr(stores, "raw", None)
    if raw is not None and getattr(raw, "fallback", "absent") is None:
        raw.fallback = shared.raw
    if cfg.embedding.enabled and getattr(stores, "cache", None) is None:
        stores.cache = shared.view(key_of(cfg)[0])
    return stores


def same_volume_free(path: Path) -> int:
    """Free bytes on the volume that holds `path` (or its nearest existing parent)."""
    p = path
    while not p.exists() and p != p.parent:
        p = p.parent
    st = os.statvfs(p)
    return st.f_bavail * st.f_frsize
