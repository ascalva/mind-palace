# ── Family: code lineage — the ledger's version graph as supersession chains (bp-099) ──
# OBJECT:    the D-side lineage reader over the φ_code snapshots ledger — distinct code versions
#            (the backfill's work list), per-commit `git diff-tree` deltas (`commit_diffs`), and the
#            per-path blob supersession chains that feed the store-free temporal poset core.
# INVARIANT: the ledger is the SOLE structural source — this module READS `snapshots`/`files` and
#            DERIVES `commit_diffs` from git, never re-minting or reinterpreting φ_code's truth. It
#            does NOT touch `ops/code_snapshot.py`/`ops/code_sensor.py` (the φ_code interpreter-
#            version pin must stay byte-identical, dn-temporal-code-corpus D4): `commit_diffs` is a
#            NEW additive table (the `open_snapshot_db` migration pattern), new D-side data.
"""Code lineage over the snapshots ledger (dn-temporal-code-corpus D4/D5, bp-099; warrant 0163).

Three readers, all ops-side (core imports nothing outside core; the ledger is φ_code's, ops-owned):

  * `ledger_versions(db)` — the distinct `(path, blob_sha)` version set (the ~1,542 the history
    backfill embeds). Distinct by construction, so the backfill is idempotent per version.
  * `capture_commit_diffs(db, repo, commits)` — the *cheap, uncaptured* per-commit delta that
    finding-0111 named: one `git diff-tree` per commit, **FIRST-PARENT** (renames = delete+add;
    merges follow the first parent so per-path history stays linear), idempotent per commit via a
    marker table, landed in a NEW additive `commit_diffs` table.
  * `supersession_chains(db)` — the per-path `blob(v0) → blob(v1) → …` chains, threaded from
    `commit_diffs` in the ledger's capture order (the `snapshots` rowid walk), handed as plain data
    to the store-free poset core `core.kernel.temporal.boundary.poset_from_chains`.

`commit_diffs` normalizes git's all-zero sha (an add's absent old blob, a delete's absent new blob)
to the empty string `''`, so a real supersession edge is exactly a row with BOTH ends non-empty —
the pair whose endpoints D1/D2 guarantee are resolvable as embedded nodes (D5).
"""

from __future__ import annotations

import sqlite3
import subprocess
from pathlib import Path

_ZERO_SHA = "0" * 40

# `commit_diffs`: one row per changed file per commit (first-parent). Additive — created on the
# snapshots db via this module's own migration (never by editing `code_snapshot.py`). The marker
# table lets an empty-diff commit (a merge with no net first-parent change) be recorded done, so it
# is not re-diffed every pass (mirrors `_code_corpus_backfilled` in code_snapshot.py).
_DDL = """
CREATE TABLE IF NOT EXISTS commit_diffs (
    commit_sha TEXT NOT NULL,
    path       TEXT NOT NULL,
    old_blob   TEXT NOT NULL DEFAULT '',        -- '' = added (no predecessor blob)
    new_blob   TEXT NOT NULL DEFAULT '',        -- '' = deleted (no successor blob)
    PRIMARY KEY (commit_sha, path)
);
CREATE TABLE IF NOT EXISTS _commit_diffs_captured (
    commit_sha TEXT NOT NULL PRIMARY KEY
);
"""


def _ensure_schema(db: sqlite3.Connection) -> None:
    """Additive migration for the lineage tables (the `open_snapshot_db` pattern) — genuinely
    additive: it only CREATEs new tables, never touches an existing φ_code column or row."""
    db.executescript(_DDL)


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True,
                          capture_output=True, text=True).stdout


def ledger_versions(db: sqlite3.Connection) -> list[tuple[str, str]]:
    """The distinct `(path, blob_sha)` code versions in the ledger — the history backfill's work
    list (D1). Distinct by SQL, ordered deterministically (path, blob) for a stable run."""
    return [(str(p), str(b)) for p, b in db.execute(
        "SELECT DISTINCT path, blob_sha FROM files ORDER BY path, blob_sha").fetchall()]


def ledger_commits(db: sqlite3.Connection) -> list[str]:
    """Every commit sha the ledger recorded, in capture order (oldest first — the `rev-list
    --reverse` walk φ_code snapshotted under, reflected in the `snapshots` rowid)."""
    return [str(s) for (s,) in db.execute(
        "SELECT commit_sha FROM snapshots ORDER BY rowid").fetchall()]


def _norm(sha: str) -> str:
    """git's all-zero sha (absent blob on an add/delete) → '' ; a real blob passes through."""
    return "" if not sha or set(sha) == {"0"} else sha


def _first_parent_diff(repo: Path, commit: str) -> list[tuple[str, str, str]]:
    """`(path, old_blob, new_blob)` for every changed `.py` in `commit` vs its FIRST parent (PD-1:
    renames come back as a delete row + an add row because `-M` is deliberately NOT passed; merges
    diff against the first parent only, keeping per-path history linear). A root commit diffs
    against the empty tree (`--root`), so its files appear as adds."""
    parents = _git(repo, "rev-parse", f"{commit}^@").split()
    if parents:
        raw = _git(repo, "diff-tree", "--no-commit-id", "-r", "--no-abbrev",
                   parents[0], commit)
    else:
        raw = _git(repo, "diff-tree", "--no-commit-id", "-r", "--no-abbrev", "--root", commit)
    out: list[tuple[str, str, str]] = []
    for line in raw.splitlines():
        if not line.startswith(":"):
            continue
        meta, _, path = line.partition("\t")
        if not path.endswith(".py"):
            continue
        # ":old_mode new_mode old_blob new_blob status"
        fields = meta.lstrip(":").split()
        if len(fields) < 5:
            continue
        _old_mode, _new_mode, old_blob, new_blob, _status = fields[:5]
        out.append((path, _norm(old_blob), _norm(new_blob)))
    return out


def capture_commit_diffs(db: sqlite3.Connection, repo: Path, commits: list[str]) -> int:
    """Capture first-parent `git diff-tree` deltas for `commits` into `commit_diffs` (D4).
    Idempotent per commit via the `_commit_diffs_captured` marker: an already-captured commit
    (including an empty-diff merge) is skipped, so a re-run — or the incremental sync re-passing the
    same commits — captures nothing new. Returns the number of commits newly captured. The ONLY
    writer of `commit_diffs`; derives from git + the ledger, never re-interpreting φ_code's rows."""
    _ensure_schema(db)
    done = {s for (s,) in db.execute("SELECT commit_sha FROM _commit_diffs_captured")}
    captured = 0
    for sha in commits:
        if sha in done:
            continue
        rows = [(sha, path, old, new) for path, old, new in _first_parent_diff(repo, sha)]
        with db:
            db.executemany(
                "INSERT OR IGNORE INTO commit_diffs VALUES (?,?,?,?)", rows)
            db.execute("INSERT OR IGNORE INTO _commit_diffs_captured VALUES (?)", (sha,))
        captured += 1
    return captured


def supersession_chains(db: sqlite3.Connection) -> dict[str, list[str]]:
    """Per-path blob supersession chains `{path: [blob v0, v1, …]}` in ledger commit order (D4/D5).

    Threaded from `commit_diffs` walked in the `snapshots` capture order (rowid): a path's chain is
    the ordered distinct sequence of its blobs — the initial `old_blob` (if the file pre-existed the
    window) then each `new_blob` as the file evolves; a delete (`new_blob=''`) ends presence without
    adding a version, and a rename's add starts the new path's own chain (PD-1). The result is plain
    data for `core.kernel.temporal.boundary.poset_from_chains` (a chain = a total order; the corpus
    is the disjoint union of chains — a forest, §8). NB the poset core's contract is
    `dict[str, list[int]]` (version_seq, `acquire.py`) and it re-sorts its values, so a temporal
    consumer feeds the commit-order POSITION of each blob (index = version_seq), not the sha
    string; the blob identity for the D5 edge is resolved from `commit_diffs` + the store directly
    (finding filed under bp-099)."""
    _ensure_schema(db)
    rows = db.execute(
        "SELECT cd.path, cd.old_blob, cd.new_blob FROM commit_diffs cd "
        "JOIN snapshots s ON s.commit_sha = cd.commit_sha ORDER BY s.rowid, cd.path").fetchall()
    chains: dict[str, list[str]] = {}
    for path, old_blob, new_blob in rows:
        chain = chains.setdefault(str(path), [])
        if not chain and old_blob:
            chain.append(str(old_blob))
        if new_blob and (not chain or chain[-1] != new_blob):
            chain.append(str(new_blob))
    return {p: c for p, c in chains.items() if c}
