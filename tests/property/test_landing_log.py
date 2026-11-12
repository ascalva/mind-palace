"""The landing log's laws on the code (dn-temporal-snapshot §3.2, §10; stage SN-1).

The log is the catalog's past: the six writing methods of `VaultCatalog` append to it in the
transaction of the row each writes, and the catalog is its fold. Hypothesis draws sequences of
catalog writes over a few paths, digests, titles and classes, with retires, renames, relabels,
re-keys and both purges among them, and after every write checks that the catalog is the fold
of the log and that every chain verifies. The laws, as §10 states them for this stage:

* SNP-1, append invariance: the read of a chain at a cut, and the state of every path at it,
  taken after every later write, are the ones taken when the cut was the head, up to the holes a
  later purge leaves (a purge empties rows and keeps their positions, SNP-7).
* SNP-2, monotonicity: the read at an earlier cut is a prefix of the read at a later one.
* SNP-3, composition: the catalog rebuilt from the state at a checkpoint and the delta since is
  the catalog.
* SNP-4, idempotence: the read at the head is the chain, and the state at the head the catalog.
* SNP-5, three reads: at every position of every chain the seek by key, the closing-stamp read
  and the fold of the prefix give each path the same row, before and after rows are emptied, and
  no path has two rows alive.

Then the stage's own cases: a record that changes nothing, and a store the UNCHANGED check
skips, append nothing; a transaction killed between the catalog's row and the log's leaves
neither; the genesis is the catalog, tombstoned paths included, and ends at a horizon; a relabel
into a class that has rows changes no row of the log and every chain verifies; a purge of an old
version of a live path leaves a hole that all three reads return at a cut where it was the head;
`verify` fails on an edited row; the secret is required, and another one is refused.
"""

from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from core.kernel.provenance import Provenance
from core.stores.authored_supersession import owner_declaration
from core.stores.catalog import VaultCatalog
from core.stores.landings import (
    LANDING_LOG_KEY,
    Landing,
    LandingLogKeyMismatch,
    LandingLogKeyMissing,
)
from core.stores.versions import RekeyRefusedError
from tests.conftest import LANDING_LOG_TEST_KEY
from tests.fixtures.ingress import palace_at, write_file

PATHS = [f"notes/n{i}.md" for i in range(5)]
DIGESTS = [f"d{i}" for i in range(6)]
TITLES = ["one", "two"]
CLASSES = [Provenance.AUTHORED_SOLO, Provenance.CURATED, Provenance.OBSERVED]
IDS = ["id-a", "id-b"]

Row = tuple[str, str, str, bool, str]          # digest, title, class, active, identity


# --- the fold of the log, from its rows alone ---------------------------------------------------

@dataclass
class Fold:
    """Each path's last row and last `store` row, chain by chain, keyed by its key in the chain,
    and the name each key carries on its rows that still have one."""

    last: dict[tuple[int, bytes], Landing] = field(default_factory=dict)
    store: dict[tuple[int, bytes], Landing] = field(default_factory=dict)
    names: dict[tuple[int, bytes], str] = field(default_factory=dict)

    def step(self, row: Landing) -> None:
        if row.path_key is None:
            return
        k = (row.chain, row.path_key)
        self.last[k] = row
        if row.kind == "store":
            self.store[k] = row
        if row.source_path is not None:
            self.names[k] = row.source_path

    def catalog(self, classes: dict[int, str]) -> dict[str, Row]:
        """The catalog this fold gives (§3.2): each path's last event in the chain that holds its
        present (the one where its last event is not a `leave`), an active row for a `store`, a
        tombstoned row for a `retire` or a `move` with the digest and title of the path's last
        `store`, and no row when that `store` is a hole."""
        keys: dict[str, list[tuple[int, bytes]]] = {}
        for k, name in self.names.items():
            keys.setdefault(name, []).append(k)
        out: dict[str, Row] = {}
        for name, ks in keys.items():
            present = [k for k in ks if self.last[k].kind != "leave"]
            assert len(present) <= 1, f"{name} has its present in {len(present)} chains"
            if not present:
                continue
            k = present[0]
            last, store = self.last[k], self.store.get(k)
            if last.kind == "store":
                if not last.hole:
                    out[name] = (str(last.digest), str(last.title), classes[k[0]], True,
                                 str(last.doc_id))
            elif store is not None and not store.hole:
                out[name] = (str(store.digest), str(store.title), classes[k[0]], False,
                             str(last.doc_id))
        return out


def chains(cat: VaultCatalog) -> list[int]:
    return cat._log.all_chains()


def classes(cat: VaultCatalog) -> dict[int, str]:
    return {int(r[0]): str(r[1]) for r in cat._conn.execute(
        "SELECT chain, class FROM landing_chains")}


def heads(cat: VaultCatalog) -> dict[int, int]:
    return {ch: cat.head(ch) for ch in chains(cat)}


def fold(cat: VaultCatalog, cut: dict[int, int] | None = None) -> Fold:
    f = Fold()
    for ch in chains(cat):
        for row in cat.read_at(ch, cut.get(ch, 0) if cut is not None else cat.head(ch)):
            f.step(row)
    return f


def rows_of(conn: sqlite3.Connection) -> dict[str, Row]:
    return {str(r[0]): (str(r[1]), str(r[2]), str(r[3]), bool(r[4]), str(r[5]))
            for r in conn.execute(
                "SELECT source_path, digest, title, provenance, active, doc_id FROM vault_files")}


def catalog_rows(cat: VaultCatalog) -> dict[str, Row]:
    return rows_of(cat._conn)


def all_rows(cat: VaultCatalog) -> list[tuple[Any, ...]]:
    return [tuple(r) for r in cat._conn.execute("SELECT * FROM landings ORDER BY chain, seq")]


def alive(row: Landing, c: int) -> bool:
    return row.seq <= c and (row.closed_at is None or row.closed_at > c)


def same_up_to_holes(now: Landing, then: Landing, c: int) -> bool:
    """A row read again after later writes: the same position, kind, key, commitment and hash; the
    same content unless a purge has emptied it since; alive at `c` exactly when it was."""
    if (now.seq, now.kind, now.path_key, now.commitment, now.hash) != \
            (then.seq, then.kind, then.path_key, then.commitment, then.hash):
        return False
    if alive(now, c) != alive(then, c):
        return False
    return now.hole or now == Landing(**{**then.__dict__, "closed_at": now.closed_at})


def assert_consistent(cat: VaultCatalog) -> None:
    """After every write: the catalog is the fold of the log, and every chain verifies."""
    assert fold(cat).catalog(classes(cat)) == catalog_rows(cat)
    for ch in chains(cat):
        check = cat.verify(ch)
        assert check.ok, check


# --- the writes -----------------------------------------------------------------------------------

record_op = st.tuples(st.just("record"), st.sampled_from(PATHS), st.sampled_from(DIGESTS),
                      st.sampled_from(TITLES), st.sampled_from(CLASSES),
                      st.one_of(st.none(), st.sampled_from(IDS)),
                      st.one_of(st.none(), st.integers(1, 9)))
ops = st.lists(st.one_of(
    record_op, record_op, record_op,
    st.tuples(st.just("tombstone"), st.sampled_from(PATHS)),
    st.tuples(st.just("rename"), st.sampled_from(PATHS), st.sampled_from(PATHS)),
    st.tuples(st.just("relabel"), st.sampled_from(CLASSES), st.sampled_from(CLASSES)),
    st.tuples(st.just("purge"), st.sampled_from(DIGESTS)),
    st.tuples(st.just("remove"), st.sampled_from(PATHS)),
    st.tuples(st.just("rekey"), st.sampled_from(PATHS), st.sampled_from(["id-x", "id-y"])),
), min_size=3, max_size=40)


def apply(cat: VaultCatalog, op: tuple[Any, ...]) -> None:
    """One write, as the code's callers make it: a rename lands the new path with the old one's
    identity and then tombstones the old one (the writer and the sync); a purge removes only a
    digest no active path holds (`purge_raw`'s gate)."""
    match op:
        case ("record", path, digest, title, cls, doc_id, version):
            cat.record(path, digest, title, provenance=cls, doc_id=doc_id, version=version)
        case ("tombstone", path):
            cat.tombstone(path)
        case ("rename", old, new):
            held = cat.get(old)
            if old != new and held is not None and held.active and cat.get(new) is None:
                cat.record(new, held.digest, held.title, provenance=Provenance(held.provenance),
                           doc_id=cat.doc_id_for(old))
                cat.tombstone(old)
        case ("relabel", old, new):
            cat.relabel_provenance(str(old), str(new))
        case ("purge", digest):
            if cat.active_refs(digest) == 0:
                cat.remove_digest(digest)
        case ("remove", path):
            cat.remove(path)
        case ("rekey", path, new):
            try:
                cat.migrate_rekey_doc_id(path, new, declaration=owner_declaration())
            except RekeyRefusedError:
                pass


@dataclass
class Taken:
    """A cut taken at the head, with what was read at it then."""

    cut: dict[int, int]
    reads: dict[int, list[Landing]]
    states: dict[tuple[str, str], Landing | None]
    class_chains: dict[str, list[int]]


def take(cat: VaultCatalog) -> Taken:
    cut = heads(cat)
    names = sorted({*PATHS, *catalog_rows(cat)})
    class_chains = {str(c): cat.chains(c) for c in CLASSES}
    return Taken(cut, {ch: cat.read_at(ch, c) for ch, c in cut.items()},
                 {(cls, p): cat.state_at(cls, p, cut) for cls in class_chains
                  for p in names if class_chains[cls]},
                 class_chains)


def assert_unchanged(cat: VaultCatalog, taken: Taken) -> None:
    """SNP-1: a cut taken earlier reads what it read then, up to the holes a purge left."""
    for ch, c in taken.cut.items():
        now = cat.read_at(ch, c)
        assert len(now) == len(taken.reads[ch])
        assert all(same_up_to_holes(a, b, c) for a, b in zip(now, taken.reads[ch], strict=True))
    for (cls, path), then in taken.states.items():
        if cat.chains(cls) != taken.class_chains[cls]:
            continue                    # a relabel gave the class another chain since
        now_state = cat.state_at(cls, path, taken.cut)
        if then is None:
            assert now_state is None
        else:
            assert now_state is not None
            assert same_up_to_holes(now_state, then, taken.cut[then.chain])


def assert_three_reads(cat: VaultCatalog) -> None:
    """SNP-5: at every position of every chain, for every path, the seek by key, the closing-stamp
    read and the fold of the prefix agree, and no path has two rows alive. The heads of the class
    at the position are the rows of the fold that are `store`s, and the history of a path is its
    `store` rows in the prefix."""
    names = sorted({*PATHS, "id-x", "id-y", *catalog_rows(cat)})
    cls_of = classes(cat)
    for ch in chains(cat):
        rows = cat.read_at(ch, cat.head(ch))
        cls = cls_of[ch]
        for c in range(cat.head(ch) + 1):
            prefix = rows[:c]
            f = Fold()
            for row in prefix:
                f.step(row)
            living: dict[bytes, list[Landing]] = {}
            for row in prefix:
                if row.path_key is not None and alive(row, c):
                    living.setdefault(row.path_key, []).append(row)
            assert all(len(rs) == 1 for rs in living.values())
            assert {k: rs[0] for k, rs in living.items()} == \
                {k[1]: r for k, r in f.last.items()}
            cut = {ch: c}
            assert cat.heads_at(cls, cut) == [r for r in prefix if r.kind == "store"
                                              and alive(r, c)]
            for name in names:
                key = cat._log.path_key(ch, name)
                assert cat.state_at(cls, name, cut) == f.last.get((ch, key))
                assert cat.history_at(cls, name, cut) == \
                    [r for r in prefix if r.path_key == key and r.kind == "store"]


@settings(max_examples=200, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(ops)
def test_the_catalog_is_the_fold_of_the_log_and_the_laws_hold(
        writes: list[tuple[Any, ...]]) -> None:
    """SNP-1 to SNP-5 over random catalog writes, retires, renames, relabels, re-keys and purges
    among them: the catalog is the fold of the log after every write and every chain verifies;
    every cut taken reads after every later write what it read then (SNP-1); at the end the
    reads are prefixes of each other (SNP-2), the catalog is the state at any checkpoint
    continued over the delta (SNP-3), the read at the head is the chain and the state at the
    head the catalog (SNP-4), and the three reads agree at every position (SNP-5)."""
    cat = VaultCatalog(Path(":memory:"))
    taken: list[Taken] = []
    for op in writes:
        apply(cat, op)
        assert_consistent(cat)
        taken.append(take(cat))
        for t in taken:
            assert_unchanged(cat, t)
    # SNP-2: every read of a chain is a prefix of the read at its head; SNP-4: a cut at or past
    # the head reads the whole chain
    for ch in chains(cat):
        whole = list(cat._log.rows(ch))
        assert cat.read_at(ch, cat.head(ch)) == cat.read_at(ch, cat.head(ch) + 5) == whole
        for c in range(len(whole) + 1):
            assert cat.read_at(ch, c) == whole[:c]
            assert cat.read_between(ch, c, len(whole)) == whole[c:]
    # SNP-3: the state at each cut taken, continued over the delta since, is the catalog
    for t in taken:
        f = fold(cat, t.cut)
        for ch in chains(cat):
            for row in cat.read_between(ch, t.cut.get(ch, 0), cat.head(ch)):
                f.step(row)
        assert f.catalog(classes(cat)) == catalog_rows(cat)
    # SNP-4: at the head the state of a path over its class's chains is the catalog's row
    present = catalog_rows(cat)
    for cls in {str(c) for c in CLASSES}:
        if not cat.chains(cls):
            continue
        for path in PATHS:
            state = cat.state_at(cls, path, heads(cat))
            entry = present.get(path)
            if entry is not None and entry[2] == cls:
                assert state is not None and not state.hole
                assert (state.kind == "store") == entry[3]
                if entry[3]:
                    assert (state.digest, state.title, state.doc_id) == \
                        (entry[0], entry[1], entry[4])
    assert_three_reads(cat)
    cat.close()


# --- the stage's cases ----------------------------------------------------------------------------

def test_a_record_that_changes_nothing_appends_nothing() -> None:
    cat = VaultCatalog(Path(":memory:"))
    cat.record("a.md", "d1", "A")
    head = heads(cat)
    cat.record("a.md", "d1", "A")
    cat.record("a.md", "d1", "A", version=7)           # the version alone is no change
    assert heads(cat) == head
    cat.record("a.md", "d1", "B")                       # a title is
    assert cat.head(cat.chains(Provenance.AUTHORED_SOLO)[0]) == head[1] + 1
    cat.tombstone("a.md")
    head = heads(cat)
    cat.tombstone("a.md")                               # already tombstoned: nothing changes
    cat.tombstone("nowhere.md")
    assert heads(cat) == head
    assert_consistent(cat)


def test_a_store_the_unchanged_check_skips_appends_nothing(tmp_path: Path) -> None:
    """Through the writer, as the daemon lands a vault: the second sync of the same notes is
    UNCHANGED and the log does not move. The store rows carry the version each landing is, the
    version chain's own number; an edit appends the next; a delete is a `retire` and a rename's
    tombstone a `move`."""
    p = palace_at(tmp_path)
    cat = p.stores.catalog
    a = write_file(p.vault, "a.md", "alpha\n")
    write_file(p.vault, "b.md", "beta\n")
    assert p.run("do sync_vault")["effects"] == {"landed": 2}
    head = heads(cat)
    assert p.run("do sync_vault")["effects"] == {"unchanged": 2}
    assert heads(cat) == head
    a.write_text("alpha, edited\n", encoding="utf-8")
    assert p.run("do sync_vault")["effects"] == {"landed": 1, "unchanged": 1}
    (chain,) = cat.chains(Provenance.AUTHORED_SOLO)
    stores = [r for r in cat.read_at(chain, cat.head(chain))
              if r.kind == "store" and r.source_path == str(a)]
    assert p.stores.versions is not None
    assert [r.version for r in stores] == \
        [v.version_seq for v in p.stores.versions.history(cat.doc_id_for(str(a)))] == [1, 2]
    a.rename(p.vault / "c.md")                          # the same bytes at a new path
    (p.vault / "b.md").unlink()
    p.run("do sync_vault")
    tail = cat.read_between(chain, head[chain], cat.head(chain))
    kinds = {(r.kind, Path(str(r.source_path)).name) for r in tail}
    assert {("move", "a.md"), ("retire", "b.md"), ("store", "c.md")} <= kinds
    assert_consistent(cat)


_KILL = """
import os, sys
from pathlib import Path
from core.stores import landings
from core.stores.catalog import VaultCatalog

cat = VaultCatalog(Path(sys.argv[1]))
real = landings.LandingLog._append

def die(self, chain, kind, **kw):
    if kind == "store":
        os._exit(9)                                     # killed: no handler, no rollback
    return real(self, chain, kind, **kw)

landings.LandingLog._append = die
cat.record("killed.md", "dk", "K")
"""


def test_a_transaction_killed_between_the_two_rows_leaves_neither(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db = tmp_path / "catalog.sqlite"
    cat = VaultCatalog(db)
    cat.record("kept.md", "d0", "K")
    head = heads(cat)
    cat.close()
    env = {**os.environ, LANDING_LOG_KEY: LANDING_LOG_TEST_KEY}
    done = subprocess.run([sys.executable, "-c", _KILL, str(db)], env=env,
                          cwd=Path(__file__).resolve().parents[2], check=False)
    assert done.returncode == 9
    cat = VaultCatalog(db)
    assert cat.get("killed.md") is None
    assert heads(cat) == head
    assert_consistent(cat)
    # and in process: the write that raises after the catalog's row rolls the row back
    def boom(*args: Any, **kwargs: Any) -> None:
        raise RuntimeError("between the two rows")

    monkeypatch.setattr(cat._log, "store", boom)
    with pytest.raises(RuntimeError):
        cat.record("raised.md", "dr", "R")
    assert cat.get("raised.md") is None
    assert heads(cat) == head
    cat.close()


def test_a_deferred_batch_carries_its_log_rows(tmp_path: Path) -> None:
    cat = VaultCatalog(tmp_path / "catalog.sqlite")
    with cat.deferred():
        cat.record("a.md", "d1", "A")
        cat.record("b.md", "d2", "B")
    (chain,) = cat.chains(Provenance.AUTHORED_SOLO)
    head = cat.head(chain)
    with pytest.raises(RuntimeError), cat.deferred():
        cat.record("c.md", "d3", "C")
        cat.tombstone("a.md")
        raise RuntimeError("the batch dies before its end")
    assert cat.get("c.md") is None and cat.get("a.md") is not None
    assert cat.head(chain) == head
    assert_consistent(cat)


def _legacy_catalog(db: Path, rows: list[tuple[str, str, str, str, int, str]]) -> None:
    """A catalog as a build before the log left it: its rows and no log."""
    with sqlite3.connect(db) as conn:
        conn.execute("CREATE TABLE vault_files (source_path TEXT PRIMARY KEY, digest TEXT NOT "
                     "NULL, title TEXT NOT NULL, provenance TEXT NOT NULL DEFAULT "
                     "'authored-solo', active INTEGER NOT NULL DEFAULT 1, updated_at TEXT NOT "
                     "NULL, doc_id TEXT)")
        conn.executemany("INSERT INTO vault_files VALUES (?, ?, ?, ?, ?, '2026-11-01', ?)", rows)


def test_the_genesis_is_the_catalog_and_ends_at_a_horizon(tmp_path: Path) -> None:
    db = tmp_path / "catalog.sqlite"
    _legacy_catalog(db, [
        ("v/a.md", "da", "A", "authored-solo", 1, "v/a.md"),
        ("v/b.md", "db", "B", "authored-solo", 0, "v/b.md"),      # deleted: a retire
        ("v/c.md", "dc", "C", "authored-solo", 0, "v/d.md"),      # renamed away: a move
        ("v/d.md", "dc", "C", "authored-solo", 1, "v/d.md"),
        ("dialogue/x/1", "dx", "X", "authored-dialogue", 1, "dialogue/x/1"),
        ("docs/r.md", "dr", "R", "curated", 0, "docs/r.md"),
    ])
    with sqlite3.connect(db) as conn:
        before = rows_of(conn)
    cat = VaultCatalog(db)
    assert catalog_rows(cat) == before
    assert fold(cat).catalog(classes(cat)) == before
    assert sorted(classes(cat).values()) == ["authored-dialogue", "authored-solo", "curated"]
    for ch in chains(cat):
        rows = cat.read_at(ch, cat.head(ch))
        assert rows[0].kind == "genesis" and rows[-1].kind == "horizon"
        assert rows[-1].horizon == rows[-1].seq == len(rows)
        assert {r.kind for r in rows[1:-1]} <= {"store", "retire", "move"}
        assert cat.verify(ch).ok
    (solo,) = cat.chains(Provenance.AUTHORED_SOLO)
    kinds = [(r.kind, r.source_path) for r in cat.read_at(solo, cat.head(solo))[1:-1]]
    assert kinds == [("store", "v/a.md"), ("store", "v/b.md"), ("retire", "v/b.md"),
                     ("store", "v/c.md"), ("move", "v/c.md"), ("store", "v/d.md")]
    head = heads(cat)
    cat.close()
    assert heads(VaultCatalog(db)) == head                  # one genesis: a reopen adds nothing


def test_a_relabel_into_a_class_with_rows_changes_no_row_and_every_chain_verifies() -> None:
    cat = VaultCatalog(Path(":memory:"))
    cat.record("a.md", "d1", "A", provenance=Provenance.AUTHORED_SOLO)
    cat.record("b.md", "d2", "B", provenance=Provenance.CURATED)
    cat.record("c.md", "d3", "C", provenance=Provenance.CURATED)
    rows = all_rows(cat)
    assert cat.relabel_provenance("curated", "authored-solo") == 2
    assert all_rows(cat) == rows
    assert len(cat.chains(Provenance.AUTHORED_SOLO)) == 2 and cat.chains("curated") == []
    assert_consistent(cat)
    cat.record("b.md", "d4", "B", provenance=Provenance.AUTHORED_SOLO)   # stays in its chain
    state = cat.state_at(Provenance.AUTHORED_SOLO, "b.md", heads(cat))
    assert state is not None and state.chain == 2 and state.digest == "d4"
    assert_consistent(cat)


def test_a_purged_old_version_of_a_live_path_is_a_hole_by_the_three_reads() -> None:
    cat = VaultCatalog(Path(":memory:"))
    for d in ("d1", "d2", "d3"):
        cat.record("live.md", d, "L")
    (chain,) = cat.chains(Provenance.AUTHORED_SOLO)
    at_d2 = next(r.seq for r in cat.read_at(chain, cat.head(chain)) if r.digest == "d2")
    assert cat.active_refs("d2") == 0                    # purge_raw's gate lets it through
    assert cat.remove_digest("d2") == 0                  # no catalog row held it
    cut = {chain: at_d2}
    state = cat.state_at(Provenance.AUTHORED_SOLO, "live.md", cut)
    assert state is not None and state.hole and state.seq == at_d2 and state.kind == "store"
    assert state.path_key == cat._log.path_key(chain, "live.md")
    (head_row,) = cat.heads_at(Provenance.AUTHORED_SOLO, cut)
    assert head_row.hole and head_row.seq == at_d2 and head_row.source_path is None
    history = cat.history_at(Provenance.AUTHORED_SOLO, "live.md", cut)
    assert [r.digest for r in history] == ["d1", None] and history[-1].hole
    assert fold(cat, cut).last[(chain, state.path_key)] == state
    assert catalog_rows(cat)["live.md"][0] == "d3"
    assert_consistent(cat)
    assert_three_reads(cat)


def test_verify_fails_on_an_edited_row() -> None:
    cat = VaultCatalog(Path(":memory:"))
    for d in ("d1", "d2", "d3"):
        cat.record("a.md", d, "A")
    (chain,) = cat.chains(Provenance.AUTHORED_SOLO)
    assert cat.verify(chain).ok
    edits = [
        ("UPDATE landings SET digest = 'forged' WHERE chain = ? AND seq = 4", 4, "the commitment"),
        ("UPDATE landings SET title = 'forged' WHERE chain = ? AND seq = 3", 3, "the commitment"),
        ("UPDATE landings SET commitment = zeroblob(32) WHERE chain = ? AND seq = 5", 5,
         "the commitment"),
        ("UPDATE landings SET hash = zeroblob(32) WHERE chain = ? AND seq = 2", 2, "the hash"),
    ]
    for edit, seq, why in edits:
        cat._conn.execute("SAVEPOINT edit")
        cat._conn.execute(edit, [chain])
        check = cat.verify(chain)
        assert not check.ok and check.failed_at == seq and check.why == why
        cat._conn.execute("ROLLBACK TO edit")
        cat._conn.execute("RELEASE edit")
        assert cat.verify(chain).ok
    cat._conn.execute("UPDATE landings SET salt = NULL WHERE chain = ? AND seq = 4", [chain])
    assert cat.verify(chain).ok                          # an emptied row: the hash still holds
    cat._conn.execute("DELETE FROM landings WHERE chain = ? AND seq = 3", [chain])
    check = cat.verify(chain)
    assert not check.ok and check.failed_at == 3


def test_without_the_secret_the_genesis_and_every_write_refuse(tmp_path: Path,
                                                                monkeypatch: pytest.MonkeyPatch,
                                                                ) -> None:
    db = tmp_path / "catalog.sqlite"
    _legacy_catalog(db, [("a.md", "d1", "A", "authored-solo", 1, "a.md")])
    monkeypatch.delenv(LANDING_LOG_KEY)
    with pytest.raises(LandingLogKeyMissing, match="landing-log-key"):
        VaultCatalog(db)                                 # the migration's genesis refuses
    with sqlite3.connect(db) as conn:
        assert conn.execute("SELECT count(*) FROM landings").fetchone() == (0,)
    monkeypatch.setenv(LANDING_LOG_KEY, "00" * 31)       # too short
    with pytest.raises(LandingLogKeyMissing, match="31 bytes"):
        VaultCatalog(db)
    monkeypatch.setenv(LANDING_LOG_KEY, LANDING_LOG_TEST_KEY)
    cat = VaultCatalog(db)
    head = heads(cat)
    cat.close()
    monkeypatch.delenv(LANDING_LOG_KEY)
    cat = VaultCatalog(db)                               # a read needs no key
    assert cat.read_at(1, 2) == cat.read_at(1, cat.head(1))[:2]
    for write in (lambda: cat.record("b.md", "d2", "B"), lambda: cat.tombstone("a.md"),
                  lambda: cat.remove("a.md")):
        with pytest.raises(LandingLogKeyMissing):
            write()
    kept = cat.get("a.md")
    assert heads(cat) == head and cat.get("b.md") is None and kept is not None and kept.active


def test_another_secret_is_refused(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db = tmp_path / "catalog.sqlite"
    cat = VaultCatalog(db)
    cat.record("a.md", "d1", "A")
    head = heads(cat)
    cat.close()
    monkeypatch.setenv(LANDING_LOG_KEY, "ab" * 32)
    cat = VaultCatalog(db)
    with pytest.raises(LandingLogKeyMismatch):
        cat.record("a.md", "d2", "A")
    kept = cat.get("a.md")
    assert heads(cat) == head and kept is not None and kept.digest == "d1"
