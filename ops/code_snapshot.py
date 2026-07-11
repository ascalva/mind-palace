"""Per-commit structural snapshot of the code — the build tracking its own shape.

Git already stores the *text* of every commit; what it does not give the evolution study is
the *structure* as queryable data. This module walks a commit's tracked ``*.py`` blobs (the
COMMITTED tree via ``git show``, never the working directory), parses each with ``ast``, and
records the skeleton — symbols (functions/classes with signatures), imports, LOC, per-file
blob hashes — keyed by commit SHA. Diffing two SHAs answers "what changed structurally,"
which git can only answer textually.

A small dedicated SQLite (`data/code_snapshots.sqlite`), the same pattern as the run ledger —
and like the run ledger it is BUILD history, not corpus: `palace reset` guards it. Idempotent
by SHA (re-snapshot is a no-op), so a post-commit hook and a history backfill share one path.

Deliberately NOT here: ingesting snapshots into the knowledge corpus. Source code as a corpus
source class is an open design question (finding-0021 — code is builder-produced reality, not
owner belief; its provenance label is unsettled). This ledger stays on the ops side until that
is ratified.
"""

from __future__ import annotations

import ast
import hashlib
import sqlite3
import subprocess
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from pathlib import Path

_DDL = """
CREATE TABLE IF NOT EXISTS snapshots (
    commit_sha    TEXT PRIMARY KEY,
    committed_at  TEXT NOT NULL,                 -- author date of the commit (git %aI)
    taken_at      TEXT NOT NULL,                 -- when this snapshot ran
    files         INTEGER NOT NULL,
    loc           INTEGER NOT NULL,
    functions     INTEGER NOT NULL,
    classes       INTEGER NOT NULL,
    parse_errors  INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS files (
    commit_sha  TEXT NOT NULL,
    path        TEXT NOT NULL,
    blob_sha    TEXT NOT NULL,                   -- git blob id: content identity across commits
    loc         INTEGER NOT NULL,
    functions   INTEGER NOT NULL,
    classes     INTEGER NOT NULL,
    parse_error INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (commit_sha, path)
);
CREATE TABLE IF NOT EXISTS symbols (
    commit_sha TEXT NOT NULL,
    path       TEXT NOT NULL,
    kind       TEXT NOT NULL,                    -- function | async_function | class
    qualname   TEXT NOT NULL,                    -- dotted within the module (Cls.method)
    lineno     INTEGER NOT NULL,
    signature  TEXT NOT NULL DEFAULT '',         -- unparsed arg list for defs, '' for classes
    PRIMARY KEY (commit_sha, path, qualname, lineno)
);
CREATE TABLE IF NOT EXISTS imports (
    commit_sha TEXT NOT NULL,
    path       TEXT NOT NULL,
    module     TEXT NOT NULL,                    -- imported module (root of the dotted name)
    PRIMARY KEY (commit_sha, path, module)
);
"""


def _utcnow() -> str:
    return datetime.now(UTC).replace(tzinfo=None).isoformat(timespec="seconds")


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True,
                          capture_output=True, text=True).stdout


@dataclass(frozen=True)
class Symbol:
    kind: str
    qualname: str
    lineno: int
    signature: str


@dataclass
class FileShape:
    path: str
    blob_sha: str
    loc: int = 0
    symbols: list[Symbol] = field(default_factory=list)
    imports: set[str] = field(default_factory=set)
    parse_error: bool = False

    @property
    def functions(self) -> int:
        return sum(1 for s in self.symbols if s.kind != "class")

    @property
    def classes(self) -> int:
        return sum(1 for s in self.symbols if s.kind == "class")


def _walk_defs(node: ast.AST, prefix: str, out: list[Symbol]) -> None:
    for child in ast.iter_child_nodes(node):
        if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
            kind = "async_function" if isinstance(child, ast.AsyncFunctionDef) else "function"
            qual = f"{prefix}{child.name}"
            out.append(Symbol(kind, qual, child.lineno, f"({ast.unparse(child.args)})"))
            _walk_defs(child, f"{qual}.", out)
        elif isinstance(child, ast.ClassDef):
            qual = f"{prefix}{child.name}"
            out.append(Symbol("class", qual, child.lineno, ""))
            _walk_defs(child, f"{qual}.", out)


def _module_imports(tree: ast.Module) -> set[str]:
    mods: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            mods.add(node.module.split(".")[0])
    return mods


def parse_source(path: str, blob_sha: str, source: str) -> FileShape:
    shape = FileShape(path=path, blob_sha=blob_sha, loc=source.count("\n") + (0 if source.endswith("\n") or not source else 1))
    try:
        tree = ast.parse(source)
    except SyntaxError:
        shape.parse_error = True
        return shape
    _walk_defs(tree, "", shape.symbols)
    shape.imports = _module_imports(tree)
    return shape


def _py_blobs(repo: Path, rev: str) -> list[tuple[str, str]]:
    """(path, blob_sha) for every tracked .py in the commit's tree."""
    out = []
    for line in _git(repo, "ls-tree", "-r", rev).splitlines():
        meta, path = line.split("\t", 1)
        _mode, otype, sha = meta.split()
        if otype == "blob" and path.endswith(".py"):
            out.append((path, sha))
    return out


def _read_blobs(repo: Path, shas: list[str]) -> dict[str, str]:
    """Blob contents in ONE `git cat-file --batch` call — sizes are bytes, so slice raw
    bytes and decode after (a per-file `git show` at history scale is thousands of forks)."""
    if not shas:
        return {}
    raw = subprocess.run(["git", "-C", str(repo), "cat-file", "--batch"], check=True,
                         input=("\n".join(shas) + "\n").encode(), capture_output=True).stdout
    out: dict[str, str] = {}
    i = 0
    for _ in shas:
        j = raw.index(b"\n", i)
        sha, _otype, size = raw[i:j].split()
        n = int(size)
        out[sha.decode()] = raw[j + 1 : j + 1 + n].decode("utf-8", errors="replace")
        i = j + 1 + n + 1
    return out


def snapshot_commit(db: sqlite3.Connection, repo: Path, rev: str = "HEAD", *,
                    _cache: dict[str, FileShape] | None = None) -> str | None:
    """Snapshot one commit's tree. Idempotent: returns None if the SHA is already recorded.
    `_cache` (blob_sha -> parsed shape) lets a backfill parse each unique blob once ever."""
    cache = _cache if _cache is not None else {}
    sha = _git(repo, "rev-parse", rev).strip()
    if db.execute("SELECT 1 FROM snapshots WHERE commit_sha=?", (sha,)).fetchone():
        return None
    committed_at = _git(repo, "show", "-s", "--format=%aI", sha).strip()
    blobs = _py_blobs(repo, sha)
    fresh = _read_blobs(repo, sorted({b for _, b in blobs if b not in cache}))
    for blob, source in fresh.items():
        cache[blob] = parse_source("", blob, source)
    shapes = [replace(cache[blob], path=path) for path, blob in blobs]
    with db:
        db.execute(
            "INSERT INTO snapshots VALUES (?,?,?,?,?,?,?,?)",
            (sha, committed_at, _utcnow(), len(shapes), sum(s.loc for s in shapes),
             sum(s.functions for s in shapes), sum(s.classes for s in shapes),
             sum(1 for s in shapes if s.parse_error)))
        for s in shapes:
            db.execute("INSERT INTO files VALUES (?,?,?,?,?,?,?)",
                       (sha, s.path, s.blob_sha, s.loc, s.functions, s.classes, int(s.parse_error)))
            db.executemany("INSERT OR IGNORE INTO symbols VALUES (?,?,?,?,?,?)",
                           [(sha, s.path, y.kind, y.qualname, y.lineno, y.signature) for y in s.symbols])
            db.executemany("INSERT OR IGNORE INTO imports VALUES (?,?,?)",
                           [(sha, s.path, m) for m in sorted(s.imports)])
    return sha


def backfill(db: sqlite3.Connection, repo: Path) -> int:
    """Snapshot every commit on the current branch, oldest first. Idempotent."""
    done = 0
    cache: dict[str, FileShape] = {}
    for sha in _git(repo, "rev-list", "--reverse", "HEAD").splitlines():
        if snapshot_commit(db, repo, sha, _cache=cache):
            done += 1
    return done


def open_snapshot_db(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(str(path))
    db.executescript(_DDL)
    return db
