"""Per-commit structural snapshot of the code — the build tracking its own shape.

Git already stores the *text* of every commit; what it does not give the evolution study is
the *structure* as queryable data. This module walks a commit's tracked ``*.py`` blobs (the
COMMITTED tree via ``git show``, never the working directory), parses each with ``ast``, and
records the skeleton — symbols (functions/classes with signatures), docstrings, imports,
LOC, per-file blob hashes — keyed by commit SHA. Diffing two SHAs answers "what changed
structurally," which git can only answer textually. Docstrings ride the SAME AST walk
(`ast.get_docstring`, no second parse) — the Rosetta payload the ratified
`code-observation-projection.md` §2.3 names as the future observation schema's translation
layer; this ledger is its cheap, additive precursor (B-a).

A small dedicated SQLite (`data/code_snapshots.sqlite`), the same pattern as the run ledger —
and like the run ledger it is BUILD history, not corpus: `palace reset` guards it. Idempotent
by SHA (re-snapshot is a no-op), so a post-commit hook and a history backfill share one path.

[cross-ref: correction — banner-on-correction, not silent] The header paragraph that once read
"Deliberately NOT here: ingesting snapshots into the knowledge corpus… stays on the ops side until
that is ratified" is now HISTORY: ratification happened (`dn-code-ingest-pipeline`, 2026-07-21;
warrant finding-0146 — the owner ruled the un-vectorized code corpus a bug). The embed lane
(`core/ingest/code_corpus.py`, bp-092/CI-1) reads code into the vector corpus under a structurally
minted `Provenance.CODE`, mirror-excluded. This ledger is the lane's SOURCE for symbol spans,
inline comments, and import records — so CI-1 adds three additive captures here (all in the
`open_snapshot_db` migration pattern, no existing row mutated): `symbols.end_lineno` (L0a slice
boundaries), a `comments` sidecar (the tokenize pass closing finding-0146 defect 2 — `#` comments
entered NO store before), and an `import_records` table (full dotted module + imported names; the
existing `imports` root table is kept unchanged, and CI-3 consumes the full records to resolve
cross-module `inherits`/`calls`). The ledger itself remains build history, reset-guarded.
"""

from __future__ import annotations

import ast
import io
import re
import sqlite3
import subprocess
import tokenize
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
    parse_errors  INTEGER NOT NULL DEFAULT 0,
    -- commit-header lookup keys (CONVENTIONS §Commits): type(scope): subject, parsed.
    -- Non-conforming headers keep subject with ctype/scope '' — lookup degrades, honestly.
    subject       TEXT NOT NULL DEFAULT '',
    ctype         TEXT NOT NULL DEFAULT '',
    scope         TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS files (
    commit_sha  TEXT NOT NULL,
    path        TEXT NOT NULL,
    blob_sha    TEXT NOT NULL,                   -- git blob id: content identity across commits
    loc         INTEGER NOT NULL,
    functions   INTEGER NOT NULL,
    classes     INTEGER NOT NULL,
    parse_error INTEGER NOT NULL DEFAULT 0,
    docstring   TEXT NOT NULL DEFAULT '',        -- module-level ast.get_docstring, '' if absent
    PRIMARY KEY (commit_sha, path)
);
CREATE TABLE IF NOT EXISTS symbols (
    commit_sha TEXT NOT NULL,
    path       TEXT NOT NULL,
    kind       TEXT NOT NULL,                    -- function | async_function | class
    qualname   TEXT NOT NULL,                    -- dotted within the module (Cls.method)
    lineno     INTEGER NOT NULL,
    signature  TEXT NOT NULL DEFAULT '',         -- unparsed arg list for defs, '' for classes
    docstring  TEXT NOT NULL DEFAULT '',         -- ast.get_docstring verbatim, '' if absent
    -- L0a slice boundary (CI-1): the symbol's last source line (ast end_lineno). Declared LAST so a
    -- fresh file's column order matches a migrated one. 0 only on a pre-CI-1 (un-backfilled) row —
    -- a real span is always end_lineno >= lineno >= 1.
    end_lineno INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (commit_sha, path, qualname, lineno)
);
CREATE TABLE IF NOT EXISTS imports (
    commit_sha TEXT NOT NULL,
    path       TEXT NOT NULL,
    module     TEXT NOT NULL,                    -- imported module (root of the dotted name)
    PRIMARY KEY (commit_sha, path, module)
);
-- CI-1 additive: inline `#` comments — captured by a stdlib `tokenize` pass (the AST drops
-- comment trivia, so this closes finding-0146 defect 2). One row per comment, attributed to the
-- innermost symbol whose lineno..end_lineno span contains it (qualname='' = file grain). Text is
-- the verbatim token (leading '#' included); L1's prose view strips it downstream.
CREATE TABLE IF NOT EXISTS comments (
    commit_sha TEXT NOT NULL,
    path       TEXT NOT NULL,
    lineno     INTEGER NOT NULL,                 -- the comment's source line
    qualname   TEXT NOT NULL DEFAULT '',         -- innermost containing symbol ('' = file grain)
    text       TEXT NOT NULL,                    -- verbatim COMMENT token, e.g. "# note"
    PRIMARY KEY (commit_sha, path, lineno)
);
-- CI-1 additive: FULL import records (the existing `imports` root table is untouched). One row per
-- imported name: `module` is the FULL dotted path (`from a.b.c import x` → 'a.b.c'), `name` the
-- imported name ('' for a plain `import a.b.c`), `asname` the local binding, `level` the relative-
-- import depth (`from . import x` → 1). CI-3 consumes this to map an imported name to its defining
-- module — the cross-module `inherits`/`calls` precondition the root-only table could not serve.
CREATE TABLE IF NOT EXISTS import_records (
    commit_sha TEXT NOT NULL,
    path       TEXT NOT NULL,
    module     TEXT NOT NULL DEFAULT '',         -- full dotted module ('' for `from . import x`)
    name       TEXT NOT NULL DEFAULT '',         -- imported name ('' for whole-module `import x`)
    asname     TEXT NOT NULL DEFAULT '',         -- local binding if aliased
    lineno     INTEGER NOT NULL DEFAULT 0,
    level      INTEGER NOT NULL DEFAULT 0,        -- relative-import level (0 = absolute)
    PRIMARY KEY (commit_sha, path, module, name, level)
);
"""


def _utcnow() -> str:
    return datetime.now(UTC).replace(tzinfo=None).isoformat(timespec="seconds")


# CONVENTIONS §Commits: `type(scope): subject` (optional scope, optional breaking `!`).
_HEADER = re.compile(r"^(\w+)(?:\(([^)]*)\))?!?:\s*(.+)$")


def parse_header(subject: str) -> tuple[str, str]:
    """(ctype, scope) from a conventional-commit subject; ('', '') when non-conforming."""
    m = _HEADER.match(subject)
    return (m.group(1), m.group(2) or "") if m else ("", "")


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True,
                          capture_output=True, text=True).stdout


@dataclass(frozen=True)
class Symbol:
    kind: str
    qualname: str
    lineno: int
    signature: str
    docstring: str = ""                          # ast.get_docstring verbatim, '' if absent
    end_lineno: int = 0                          # ast end_lineno — the L0a slice's last line (CI-1)


@dataclass(frozen=True)
class Comment:
    """One inline `#` comment (CI-1): the tokenize pass's unit. `qualname` is the innermost
    symbol whose lineno..end_lineno contains this line, '' for file grain."""

    lineno: int
    qualname: str
    text: str                                    # verbatim COMMENT token, e.g. "# note"


@dataclass(frozen=True)
class ImportRecord:
    """One imported name (CI-1): `module` is the FULL dotted path, `name` the imported name
    ('' for a whole-module `import x`), `asname` the local binding, `level` the relative depth."""

    module: str
    name: str
    asname: str
    lineno: int
    level: int


@dataclass
class FileShape:
    path: str
    blob_sha: str
    loc: int = 0
    symbols: list[Symbol] = field(default_factory=list)
    imports: set[str] = field(default_factory=set)
    comments: list[Comment] = field(default_factory=list)
    import_records: list[ImportRecord] = field(default_factory=list)
    parse_error: bool = False
    docstring: str = ""                          # module-level ast.get_docstring, '' if absent

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
            out.append(Symbol(kind, qual, child.lineno, f"({ast.unparse(child.args)})",
                               ast.get_docstring(child) or "", child.end_lineno or child.lineno))
            _walk_defs(child, f"{qual}.", out)
        elif isinstance(child, ast.ClassDef):
            qual = f"{prefix}{child.name}"
            out.append(Symbol("class", qual, child.lineno, "", ast.get_docstring(child) or "",
                               child.end_lineno or child.lineno))
            _walk_defs(child, f"{qual}.", out)


def _module_imports(tree: ast.Module) -> set[str]:
    mods: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            mods.add(node.module.split(".")[0])
    return mods


def _import_records(tree: ast.Module) -> list[ImportRecord]:
    """FULL import records (CI-1): one per imported name, dotted module path preserved. `import a.b`
    → module='a.b', name='' ; `from a.b import x as y` → module='a.b', name='x', asname='y' ;
    `from . import x` → module='', name='x', level=1. Deterministic order (source order)."""
    out: list[ImportRecord] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                out.append(ImportRecord(a.name, "", a.asname or "", node.lineno, 0))
        elif isinstance(node, ast.ImportFrom):
            for a in node.names:
                out.append(ImportRecord(node.module or "", a.name, a.asname or "",
                                        node.lineno, node.level))
    return out


def _innermost_qualname(symbols: list[Symbol], lineno: int) -> str:
    """The innermost symbol whose lineno..end_lineno span contains `lineno` — the smallest
    containing span (nested defs win over their parents). '' when no symbol contains the line."""
    containing = [s for s in symbols if s.lineno <= lineno <= s.end_lineno]
    if not containing:
        return ""
    return min(containing, key=lambda s: s.end_lineno - s.lineno).qualname


def _comments(source: str, symbols: list[Symbol]) -> list[Comment]:
    """Inline `#` comments via stdlib `tokenize`, attributed to the innermost containing symbol.
    Tokenize can raise on a source `ast.parse` accepted (rare encoding/continuation cases); on any
    tokenize error the file yields NO comments rather than failing the whole snapshot."""
    out: list[Comment] = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(source).readline):
            if tok.type == tokenize.COMMENT:
                line = tok.start[0]
                out.append(Comment(line, _innermost_qualname(symbols, line), tok.string))
    except (tokenize.TokenError, IndentationError, SyntaxError, ValueError):
        return []
    return out


def parse_source(path: str, blob_sha: str, source: str) -> FileShape:
    loc = source.count("\n") + (0 if source.endswith("\n") or not source else 1)
    shape = FileShape(path=path, blob_sha=blob_sha, loc=loc)
    try:
        tree = ast.parse(source)
    except SyntaxError:
        shape.parse_error = True
        return shape
    shape.docstring = ast.get_docstring(tree) or ""
    _walk_defs(tree, "", shape.symbols)
    shape.imports = _module_imports(tree)
    shape.import_records = _import_records(tree)
    shape.comments = _comments(source, shape.symbols)
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


def list_py_blobs(repo: Path, rev: str = "HEAD") -> list[tuple[str, str]]:
    """(path, blob_sha) for every tracked `.py` in `rev`'s committed tree — the code embed lane's
    enumeration seam (bp-092). Public wrapper over the one blob walk, so the lane reuses φ_code's
    reader (DRY) rather than re-shelling git."""
    return _py_blobs(repo, rev)


def read_py_blobs(repo: Path, shas: list[str]) -> dict[str, str]:
    """blob_sha -> decoded source text, in ONE `git cat-file --batch` (the lane reuses the same
    batched reader the snapshot walk uses). `errors='replace'` on decode, matching φ_code."""
    return _read_blobs(repo, shas)


def snapshot_commit(db: sqlite3.Connection, repo: Path, rev: str = "HEAD", *,
                    _cache: dict[str, FileShape] | None = None) -> str | None:
    """Snapshot one commit's tree. Idempotent: returns None if the SHA is already recorded.
    `_cache` (blob_sha -> parsed shape) lets a backfill parse each unique blob once ever."""
    cache = _cache if _cache is not None else {}
    sha = _git(repo, "rev-parse", rev).strip()
    if db.execute("SELECT 1 FROM snapshots WHERE commit_sha=?", (sha,)).fetchone():
        return None
    header = _git(repo, "show", "-s", "--format=%aI%x09%s", sha).strip()
    committed_at, subject = header.split("\t", 1)
    ctype, scope = parse_header(subject)
    blobs = _py_blobs(repo, sha)
    fresh = _read_blobs(repo, sorted({b for _, b in blobs if b not in cache}))
    for blob, source in fresh.items():
        cache[blob] = parse_source("", blob, source)
    shapes = [replace(cache[blob], path=path) for path, blob in blobs]
    with db:
        db.execute(
            "INSERT INTO snapshots VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (sha, committed_at, _utcnow(), len(shapes), sum(s.loc for s in shapes),
             sum(s.functions for s in shapes), sum(s.classes for s in shapes),
             sum(1 for s in shapes if s.parse_error), subject, ctype, scope))
        for s in shapes:
            db.execute("INSERT INTO files VALUES (?,?,?,?,?,?,?,?)",
                       (sha, s.path, s.blob_sha, s.loc, s.functions, s.classes,
                        int(s.parse_error), s.docstring))
            db.executemany("INSERT OR IGNORE INTO symbols VALUES (?,?,?,?,?,?,?,?)",
                           [(sha, s.path, y.kind, y.qualname, y.lineno, y.signature,
                             y.docstring, y.end_lineno) for y in s.symbols])
            db.executemany("INSERT OR IGNORE INTO imports VALUES (?,?,?)",
                           [(sha, s.path, m) for m in sorted(s.imports)])
            db.executemany("INSERT OR IGNORE INTO comments VALUES (?,?,?,?,?)",
                           [(sha, s.path, c.lineno, c.qualname, c.text) for c in s.comments])
            db.executemany("INSERT OR IGNORE INTO import_records VALUES (?,?,?,?,?,?,?)",
                           [(sha, s.path, r.module, r.name, r.asname, r.lineno, r.level)
                            for r in s.import_records])
    return sha


def backfill(db: sqlite3.Connection, repo: Path) -> int:
    """Snapshot every commit on the current branch, oldest first. Idempotent."""
    done = 0
    cache: dict[str, FileShape] = {}
    for sha in _git(repo, "rev-list", "--reverse", "HEAD").splitlines():
        if snapshot_commit(db, repo, sha, _cache=cache):
            done += 1
    return done


def annotate_headers(db: sqlite3.Connection, repo: Path) -> int:
    """Fill subject/ctype/scope on rows snapshotted before the header columns existed —
    ONE `git log` for all of history, self-healing on every sync (rescan discipline)."""
    blank = [s for (s,) in db.execute("SELECT commit_sha FROM snapshots WHERE subject=''")]
    if not blank:
        return 0
    subjects = dict(line.split("\t", 1) for line in
                    _git(repo, "log", "--format=%H%x09%s").splitlines())
    rows = [(subjects[s], *parse_header(subjects[s]), s) for s in blank if s in subjects]
    with db:
        db.executemany("UPDATE snapshots SET subject=?, ctype=?, scope=? WHERE commit_sha=?", rows)
    return len(rows)


def backfill_docstrings(db: sqlite3.Connection, repo: Path) -> int:
    """Fill docstrings on files/symbols rows recorded before the docstring columns
    existed — re-parses each affected blob ONCE (docstrings aren't derivable from stored
    columns alone, unlike header healing). Idempotent: a row already carrying a non-empty
    docstring, or genuinely undocumented (docstring == '' in the source), is left alone —
    re-running is a no-op once every blob in the ledger has been visited. Self-healing on
    every sync (rescan discipline, same shape as `annotate_headers`)."""
    rows = db.execute(
        "SELECT commit_sha, path, blob_sha FROM files WHERE docstring='' "
        "AND (commit_sha, path) NOT IN (SELECT commit_sha, path FROM _docstring_backfilled)"
    ).fetchall()
    if not rows:
        return 0
    shas = sorted({b for _, _, b in rows})
    blobs = _read_blobs(repo, shas)
    cache: dict[str, FileShape] = {}
    updated = 0
    file_updates: list[tuple[str, str, str]] = []
    symbol_updates: list[tuple[str, str, str, str, int]] = []
    marks: list[tuple[str, str]] = []
    for commit_sha, path, blob_sha in rows:
        if blob_sha not in blobs:
            marks.append((commit_sha, path))   # blob unreachable (pruned/shallow) — mark done
            continue
        if blob_sha not in cache:
            cache[blob_sha] = parse_source(path, blob_sha, blobs[blob_sha])
        shape = cache[blob_sha]
        if shape.docstring:
            file_updates.append((shape.docstring, commit_sha, path))
            updated += 1
        for y in shape.symbols:
            if y.docstring:
                symbol_updates.append((y.docstring, commit_sha, path, y.qualname, y.lineno))
        marks.append((commit_sha, path))
    with db:
        db.executemany(
            "UPDATE files SET docstring=? WHERE commit_sha=? AND path=?", file_updates)
        db.executemany(
            "UPDATE symbols SET docstring=? WHERE commit_sha=? AND path=? "
            "AND qualname=? AND lineno=?", symbol_updates)
        db.executemany(
            "INSERT OR IGNORE INTO _docstring_backfilled VALUES (?,?)", marks)
    return updated


def open_snapshot_db(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(str(path))
    db.executescript(_DDL)
    # pre-header ledgers: additive migration (same pattern as core/stores/derived.py)
    cols = {r[1] for r in db.execute("PRAGMA table_info(snapshots)")}
    for col in ("subject", "ctype", "scope"):
        if col not in cols:
            db.execute(f"ALTER TABLE snapshots ADD COLUMN {col} TEXT NOT NULL DEFAULT ''")
    file_cols = {r[1] for r in db.execute("PRAGMA table_info(files)")}
    if "docstring" not in file_cols:
        db.execute("ALTER TABLE files ADD COLUMN docstring TEXT NOT NULL DEFAULT ''")
    symbol_cols = {r[1] for r in db.execute("PRAGMA table_info(symbols)")}
    if "docstring" not in symbol_cols:
        db.execute("ALTER TABLE symbols ADD COLUMN docstring TEXT NOT NULL DEFAULT ''")
    # CI-1 additive: the L0a slice boundary on pre-CI-1 symbol rows (backfilled to a real span by
    # backfill_code_corpus; 0 until then). Genuinely additive — no existing column is touched.
    if "end_lineno" not in symbol_cols:
        db.execute("ALTER TABLE symbols ADD COLUMN end_lineno INTEGER NOT NULL DEFAULT 0")
    # marks (commit_sha, path) pairs already visited by backfill_docstrings — an
    # undocumented file legitimately carries docstring='' forever; without a mark the
    # backfill would re-scan it on every sync trying to "heal" a row that isn't broken.
    db.execute(
        "CREATE TABLE IF NOT EXISTS _docstring_backfilled ("
        "commit_sha TEXT NOT NULL, path TEXT NOT NULL, "
        "PRIMARY KEY (commit_sha, path))")
    # CI-1: the same mark discipline for the span/comment/import_record backfill. A (commit_sha,
    # path) with no comments/imports is a legitimate no-op forever; the mark stops a re-scan of a
    # row that isn't broken (mirrors _docstring_backfilled exactly).
    db.execute(
        "CREATE TABLE IF NOT EXISTS _code_corpus_backfilled ("
        "commit_sha TEXT NOT NULL, path TEXT NOT NULL, "
        "PRIMARY KEY (commit_sha, path))")
    return db


def backfill_code_corpus(db: sqlite3.Connection, repo: Path) -> int:
    """Fill the CI-1 captures — `symbols.end_lineno`, the `comments` sidecar, and `import_records`
    — on files/symbols recorded before those columns/tables existed. Re-parses each affected blob
    ONCE (cached), same shape as `backfill_docstrings`: idempotent and self-healing on every sync.
    A (commit_sha, path) already visited (marked) is skipped, so a file with zero comments/imports
    is a recorded no-op rather than an every-sync re-scan. Returns files visited this call.

    ADDITIVE by construction: it only UPDATEs `end_lineno` (was 0) and INSERT-OR-IGNOREs new
    `comments`/`import_records` rows — no pre-existing column of any table is mutated."""
    rows = db.execute(
        "SELECT DISTINCT f.commit_sha, f.path, f.blob_sha FROM files f "
        "WHERE (f.commit_sha, f.path) NOT IN (SELECT commit_sha, path FROM _code_corpus_backfilled)"
    ).fetchall()
    if not rows:
        return 0
    shas = sorted({b for _, _, b in rows})
    blobs = _read_blobs(repo, shas)
    cache: dict[str, FileShape] = {}
    span_updates: list[tuple[int, str, str, str, int]] = []
    comment_rows: list[tuple[str, str, int, str, str]] = []
    import_rows: list[tuple[str, str, str, str, str, int, int]] = []
    marks: list[tuple[str, str]] = []
    visited = 0
    for commit_sha, path, blob_sha in rows:
        marks.append((commit_sha, path))
        if blob_sha not in blobs:
            continue                              # blob unreachable (pruned/shallow) — marked done
        if blob_sha not in cache:
            cache[blob_sha] = parse_source(path, blob_sha, blobs[blob_sha])
        shape = cache[blob_sha]
        visited += 1
        for y in shape.symbols:
            span_updates.append((y.end_lineno, commit_sha, path, y.qualname, y.lineno))
        comment_rows.extend(
            (commit_sha, path, c.lineno, c.qualname, c.text) for c in shape.comments)
        import_rows.extend(
            (commit_sha, path, r.module, r.name, r.asname, r.lineno, r.level)
            for r in shape.import_records)
    with db:
        db.executemany(
            "UPDATE symbols SET end_lineno=? WHERE commit_sha=? AND path=? "
            "AND qualname=? AND lineno=?", span_updates)
        db.executemany("INSERT OR IGNORE INTO comments VALUES (?,?,?,?,?)", comment_rows)
        db.executemany("INSERT OR IGNORE INTO import_records VALUES (?,?,?,?,?,?,?)", import_rows)
        db.executemany("INSERT OR IGNORE INTO _code_corpus_backfilled VALUES (?,?)", marks)
    return visited
