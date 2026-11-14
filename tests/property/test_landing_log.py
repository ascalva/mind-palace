"""The landing log's laws on the code (dn-temporal-snapshot §3.2, §10; stage SN-1).

The log is the catalog's past: the six writing methods of `VaultCatalog` append to it in the
transaction of the row each writes, and the catalog is its fold. Hypothesis draws a catalog as a
build before the log left it, whose first open writes the genesis, and then sequences of catalog
writes over a few paths, digests, titles and classes, with retires, renames, relabels, re-keys
and both purges among them, and after every write checks that the catalog is the fold of the log,
that every chain verifies, that no row carries `att_head` before SN-2, that a hole keeps none of
the content a purge empties, that every name the log carries is carried by a version that keeps
its content, and that a landing that changes a path's identity is preceded by a `move`. The laws,
as §10 states them for this stage:

* SNP-1, append invariance: the read of a chain at a cut, and each path's last event in it, taken
  after every later write, are the ones taken when the cut was the head, up to the holes a later
  purge leaves (a purge empties rows and keeps their positions, SNP-7); so is the state of a path
  over a class while the class's chains are the ones it had. A relabel moves a chain to another
  class, so a read by class at a past cut follows the chain's class now (§6.3), and across one the
  test compares the path's last event chain by chain.
* SNP-2, monotonicity: the read at an earlier cut is a prefix of the read at a later one.
* SNP-3, composition: the catalog rebuilt from the state at a checkpoint and the delta since is
  the catalog.
* SNP-4, idempotence: the read at the head is the chain, and the state at the head the catalog.
* SNP-5, three reads: at every position of every chain, the genesis's included, the seek by key,
  the closing-stamp read and the fold of the prefix give each path the same row, before and after
  rows are emptied, and no path has two rows alive. The closing-stamp read over a class is the
  contents of the cut (`core/stores/cuts.py`), which replaced SN-1's `heads_at`: its versions are
  the fold's `store` rows that keep their content, and its holes the ones a purge emptied.

Then the stage's own cases: a record that changes nothing, and a store the UNCHANGED check skips,
append nothing; the writer, its batched landing too, and the sync carry the version each landing
is; a change of identity lands after a `move`, and a re-key carries the version; each of the six
writes, killed or failed between the catalog's row and the log's, leaves neither, in a batch too
when its caller goes on, and the batch's other writes commit; the genesis is the catalog,
tombstoned paths included, closes each tombstoned path's `store` and ends at a horizon; a relabel
into a class that has rows changes no row of the log, closed rows and holes included, and every
chain verifies; a history over two chains of a class follows a rule of the prefixes; a purge of an
old version of a live path leaves a hole that the seek and the fold return at a cut where it was
the head, and that the contents of the cut count as a hole and hold as no version, and a purge of
every version of a deleted note leaves no row that names it; `verify` fails
on an edited row and on a hole that keeps any one column of its content; the secret is required
by what appends or seeks a path by its key and by nothing else, and another one is refused; a
statement by path seeks the key index, and a purge by digest walks the log twice.
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
from core.stores.cuts import Cut
from core.stores.landings import (
    LANDING_LOG_KEY,
    Landing,
    LandingLogKeyMismatch,
    LandingLogKeyMissing,
)
from core.stores.versions import RekeyRefusedError
from tests.conftest import LANDING_LOG_TEST_KEY
from tests.fixtures.ingress import palace_at, write_file
from tests.fixtures.landing_writes import WRITES, ready

PATHS = [f"notes/n{i}.md" for i in range(5)]
DIGESTS = [f"d{i}" for i in range(6)]
TITLES = ["one", "two"]
CLASSES = [Provenance.AUTHORED_SOLO, Provenance.CURATED, Provenance.OBSERVED]
IDS = ["id-a", "id-b"]

Row = tuple[str, str, str, bool, str]          # digest, title, class, active, identity

# What a purge empties in a row, as §6.1 lists it (the code's own list is `landings._EMPTY`).
EMPTY = "source_path = NULL, doc_id = NULL, digest = NULL, title = NULL, salt = NULL, at = NULL"
# The columns it empties beside the salt, read off the list above and not off `Landing.content`,
# which `verify` reads: a `content` that left one out would weaken the check and this oracle
# together.
CONTENT = [part.split(" = ")[0] for part in EMPTY.split(", ") if not part.startswith("salt ")]


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


def chain_rows(cat: VaultCatalog) -> list[tuple[Any, ...]]:
    return [tuple(r) for r in cat._conn.execute(
        "SELECT chain, class, secret, key_check FROM landing_chains ORDER BY chain")]


def log_rows(cat: VaultCatalog) -> list[Landing]:
    """Every row of every chain, chain by chain, in order."""
    return [r for ch in chains(cat) for r in cat.read_at(ch, cat.head(ch))]


def alive(row: Landing, c: int) -> bool:
    return row.seq <= c and (row.closed_at is None or row.closed_at > c)


def paths_held(cat: VaultCatalog, cls: Provenance | str,
               cut: dict[int, int] | None = None) -> list[str | None]:
    """The paths of the versions a cut holds over a class, the head when no cut is given, in
    position order: the contents of the cut (`core/stores/cuts.py`)."""
    ev = cat.cuts([str(cls)])
    text = ev.held(Cut.of(cut) if cut is not None else None).columns("source_path")["source_path"]
    return [text[i] for i in range(len(text))]


def emptied(row: Landing) -> bool:
    """A hole as a purge leaves it (§6.1): no salt, and none of the path, the identity, the
    digest, the title or the bookmark (`CONTENT`)."""
    return row.salt is None and all(getattr(row, column) is None for column in CONTENT)


def same_up_to_holes(now: Landing, then: Landing, c: int) -> bool:
    """A row read again after later writes: the same position, kind, key, commitment and hash; the
    same content unless a purge has emptied it since, and then the same version, `att_head` and
    horizon, which a purge keeps; alive at `c` exactly when it was."""
    if (now.seq, now.kind, now.path_key, now.commitment, now.hash) != \
            (then.seq, then.kind, then.path_key, then.commitment, then.hash):
        return False
    if alive(now, c) != alive(then, c):
        return False
    if emptied(now):
        return (now.version, now.att_head, now.horizon) == \
            (then.version, then.att_head, then.horizon)
    return now == Landing(**{**then.__dict__, "closed_at": now.closed_at})


def assert_consistent(cat: VaultCatalog) -> None:
    """After every write: the catalog is the fold of the log; every chain verifies; no row
    carries `att_head` (SN-2 fills it); every row without its salt is a hole as a purge leaves
    it; every name the log carries is carried by a `store` that keeps its content, so a path
    none of whose versions keeps its content is named by no row; and a `store` that follows a
    `store` of its path in the chain, both with their content, keeps that one's identity, since
    a landing that changes it appends a `move` first."""
    assert fold(cat).catalog(classes(cat)) == catalog_rows(cat)
    for ch in chains(cat):
        check = cat.verify(ch)
        assert check.ok, check
    rows = log_rows(cat)
    assert all(r.att_head is None for r in rows)
    assert all(emptied(r) for r in rows if r.hole)
    kept = {r.source_path for r in rows if r.kind == "store" and not r.hole}
    assert {r.source_path for r in rows if r.source_path is not None} <= kept
    before: dict[tuple[int, bytes], Landing] = {}
    for r in rows:
        if r.path_key is None:
            continue
        prev = before.get((r.chain, r.path_key))
        if prev is not None and prev.kind == r.kind == "store" and not (prev.hole or r.hole):
            assert r.doc_id == prev.doc_id, (prev, r)
        before[(r.chain, r.path_key)] = r


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
# A catalog as a build before the log left it: a row a path, active or tombstoned, with its class
# and its identity, the path or a declared one (two paths may hold one, as §2.3's item 8 shows).
legacy = st.lists(st.tuples(st.sampled_from(PATHS), st.sampled_from(DIGESTS),
                            st.sampled_from(TITLES), st.sampled_from(CLASSES), st.booleans(),
                            st.one_of(st.none(), st.sampled_from(IDS))),
                  max_size=5, unique_by=lambda r: r[0])


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


def from_legacy(rows: list[tuple[str, str, str, Provenance, bool, str | None]]) -> VaultCatalog:
    """A catalog holding `rows` and no log, then migrated: the genesis, as the first open of a
    catalog a build before the log wrote writes it."""
    cat = VaultCatalog(Path(":memory:"))
    if rows:
        cat._conn.executemany(
            "INSERT INTO vault_files (source_path, digest, title, provenance, active, updated_at, "
            "doc_id) VALUES (?, ?, ?, ?, ?, '2026-11-01', ?)",
            [(p, d, t, str(c), int(a), doc if doc is not None else p)
             for p, d, t, c, a, doc in rows])
        cat._migrate()
        cat._conn.commit()
        assert chains(cat)
    return cat


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
    """SNP-1: a cut taken earlier reads what it read then, up to the holes a purge left: each
    chain's rows; the state of each path over a class while the class's chains are the ones it
    had; and, for a class a relabel has given other chains since, the path's last event in each
    chain the class had, by its key (a read by class follows the chains' classes now, §6.3)."""
    for ch, c in taken.cut.items():
        now = cat.read_at(ch, c)
        assert len(now) == len(taken.reads[ch])
        assert all(same_up_to_holes(a, b, c) for a, b in zip(now, taken.reads[ch], strict=True))
    for (cls, path), then in taken.states.items():
        if cat.chains(cls) == taken.class_chains[cls]:
            now_state = cat.state_at(cls, path, taken.cut)
            if then is None:
                assert now_state is None
            else:
                assert now_state is not None
                assert same_up_to_holes(now_state, then, taken.cut[then.chain])
            continue
        for ch in taken.class_chains[cls]:          # a relabel gave the class other chains since
            key = cat._log.path_key(ch, path)
            last = next((r for r in reversed(taken.reads[ch]) if r.path_key == key), None)
            seek = cat._log._seek(ch, path, taken.cut[ch])
            assert (seek is None) == (last is None)
            assert seek is None or last is None or same_up_to_holes(seek, last, taken.cut[ch])


def assert_three_reads(cat: VaultCatalog) -> None:
    """SNP-5: at every position of every chain, for every path, the seek by key, the closing-stamp
    read and the fold of the prefix agree, and no path has two rows alive. What the position holds
    over the class, the contents of the cut, is the rows of the fold that are `store`s keeping
    their content, its holes those a purge emptied, and the history of a path is its `store` rows
    in the prefix."""
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
            held = cat.cuts([cls]).held(Cut.of(cut))
            cols = held.columns()
            assert list(zip(cols.ints("chain").tolist(), cols.ints("seq").tolist(),
                            strict=True)) == \
                [(ch, r.seq) for r in prefix if r.kind == "store" and not r.hole and alive(r, c)]
            assert held.holes() == sum(1 for r in prefix
                                       if r.kind == "store" and r.hole and alive(r, c))
            for name in names:
                key = cat._log.path_key(ch, name)
                assert cat.state_at(cls, name, cut) == f.last.get((ch, key))
                assert cat.history_at(cls, name, cut) == \
                    [r for r in prefix if r.path_key == key and r.kind == "store"]


@settings(max_examples=200, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(legacy, ops)
def test_the_catalog_is_the_fold_of_the_log_and_the_laws_hold(
        before: list[tuple[str, str, str, Provenance, bool, str | None]],
        writes: list[tuple[Any, ...]]) -> None:
    """SNP-1 to SNP-5 from a random catalog's genesis over random catalog writes, retires,
    renames, relabels, re-keys and purges among them: the catalog is the fold of the log after
    every write and every chain verifies; a `remove` leaves no row naming its path and a purge
    no row carrying its digest; every cut taken reads after every later write what it read then
    (SNP-1); at the end the reads are prefixes of each other (SNP-2), the catalog is the state at
    any checkpoint continued over the delta (SNP-3), the read at the head is the chain and the
    state at the head the catalog (SNP-4), and the three reads agree at every position (SNP-5)."""
    cat = from_legacy(before)
    assert_consistent(cat)
    taken: list[Taken] = [take(cat)]
    for op in writes:
        apply(cat, op)
        assert_consistent(cat)
        if op[0] == "remove":
            assert all(r.source_path != op[1] for r in log_rows(cat))
        if op[0] == "purge" and cat.active_refs(op[1]) == 0:
            assert all(r.digest != op[1] for r in log_rows(cat))
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


def test_the_sync_carries_the_version_each_landing_is(tmp_path: Path) -> None:
    """`VaultSync.sync_path`, the other lane that keeps version chains: a landing, an edit and a
    revert append versions 1 to 3, and a rename appends version 4 at the same bytes; the log's
    `store` of each carries that number, and the rename's tombstone is a `move`."""
    from typing import cast

    from core.ingest.embed import Embedder
    from core.ingest.sync import VaultSync
    from core.kernel.stores.rawstore import RawStore
    from core.stores.vectorstore import VectorStore
    from core.stores.versions import VersionStore
    from tests.fixtures.embedding import DIM, FakeEmbedder

    vault = tmp_path / "vault"
    vault.mkdir()
    versions = VersionStore(tmp_path / "versions.sqlite")
    cat = VaultCatalog(tmp_path / "catalog.sqlite")
    sync = VaultSync(vault=vault, raw=RawStore(tmp_path / "raw"),
                     store=VectorStore(tmp_path / "v.lance", dim=DIM), catalog=cat,
                     embedder=cast(Embedder, FakeEmbedder()), version_store=versions)
    note = vault / "n.md"
    for text in ("alpha content", "beta content", "alpha content"):
        note.write_text(text, encoding="utf-8")
        sync.rescan()
    note.rename(vault / "m.md")
    sync.rescan()
    (entry,) = cat.active_entries()
    doc = cat.doc_id_for(entry.source_path)
    assert [v.version_seq for v in versions.history(doc)] == [1, 2, 3, 4]
    (chain,) = cat.chains(Provenance.AUTHORED_SOLO)
    rows = cat.read_at(chain, cat.head(chain))
    assert [(Path(str(r.source_path)).name, r.version) for r in rows if r.kind == "store"] == \
        [("n.md", 1), ("n.md", 2), ("n.md", 3), ("m.md", 4)]
    assert [(r.kind, Path(str(r.source_path)).name) for r in rows][-2:] == \
        [("store", "m.md"), ("move", "n.md")]
    assert_consistent(cat)
    cat.close()


def test_a_batched_landing_carries_the_version_each_landing_is(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The writer's other key write: a plan of fresh stores on distinct paths, each naming its own
    identity, landed a stage at a time (`Writer.land_batch`), its keys written in one `deferred()`
    batch. Two notes land, one is edited and the plan lands again; each `store` row of the log
    carries the version the version chain gives that landing."""
    from core.ingest import ingress
    from core.ingest.readers import PalaceView
    from core.ingest.table import build_table
    from core.ingest.writer import Writer
    from core.sentence import ast
    from core.sentence.plan import compile_sentence

    p = palace_at(tmp_path)
    batches: list[int] = []
    land_batch = Writer.land_batch

    def counted(self: Writer, plan: Any) -> Any:
        batches.append(len(plan))
        return land_batch(self, plan)

    monkeypatch.setattr(Writer, "land_batch", counted)
    plan = compile_sentence('do { for n in files(source("vault")) '
                            '{ store n.content in "mirror_authored" } }',
                            ingress.grant_for("cli"), role="cli")
    assert isinstance(plan.term, ast.Do)
    term: ast.Do = plan.term

    def land() -> dict[str, Any]:
        view = PalaceView(build_table(p.cfg), "cli", p.stores.catalog, refresh=False)
        return ingress.perform(term, p.cfg, "cli", stores=p.stores, view=view, batch=True)

    a = write_file(p.vault, "a.md", "alpha\n")
    b = write_file(p.vault, "b.md", "beta\n")
    assert land()["effects"] == {"landed": 2}
    a.write_text("alpha, edited\n", encoding="utf-8")
    assert land()["effects"] == {"landed": 1, "unchanged": 1}
    assert batches == [2, 2]                            # both plans took the batched path
    cat, versions = p.stores.catalog, p.stores.versions
    assert versions is not None
    (chain,) = cat.chains(Provenance.AUTHORED_SOLO)
    rows = cat.read_at(chain, cat.head(chain))
    for note, numbers in ((str(a), [1, 2]), (str(b), [1])):
        assert [r.version for r in rows if r.kind == "store" and r.source_path == note] == \
            [v.version_seq for v in versions.history(cat.doc_id_for(note))] == numbers
    assert_consistent(cat)


def test_a_change_of_identity_moves_first_and_a_rekey_carries_the_version() -> None:
    """A `record` that gives an active path another identity writes a `move` of the one it held
    before the `store`; the owner's re-key writes a `move` and then the path's `store` under the
    new identity with the version it had, or its `retire` when the path is tombstoned."""
    cat = VaultCatalog(Path(":memory:"))
    cat.record("a.md", "d1", "A", version=3)
    cat.record("a.md", "d1", "A", doc_id="id-b", version=3)
    cat.migrate_rekey_doc_id("a.md", "id-c", declaration=owner_declaration())
    cat.tombstone("a.md")
    cat.migrate_rekey_doc_id("a.md", "id-d", declaration=owner_declaration())
    (chain,) = cat.chains(Provenance.AUTHORED_SOLO)
    rows = cat.read_at(chain, cat.head(chain))[2:]      # after the genesis and the horizon
    assert [(r.kind, r.doc_id, r.version, r.digest) for r in rows] == [
        ("store", "a.md", 3, "d1"), ("move", "a.md", None, None), ("store", "id-b", 3, "d1"),
        ("move", "id-b", None, None), ("store", "id-c", 3, "d1"),
        ("retire", "id-c", None, None), ("move", "id-c", None, None),
        ("retire", "id-d", None, None)]
    assert catalog_rows(cat)["a.md"] == ("d1", "A", "authored-solo", False, "id-d")
    assert_consistent(cat)
    assert_three_reads(cat)


_KILL = """
import os, sys
from pathlib import Path
from core.stores import landings
from core.stores.catalog import VaultCatalog
from tests.fixtures.landing_writes import WRITES

method, write = WRITES[sys.argv[2]]
cat = VaultCatalog(Path(sys.argv[1]))
setattr(landings.LandingLog, method, lambda *args, **kwargs: os._exit(9))  # no handler, no rollback
write(cat)
"""


@pytest.mark.parametrize("name", sorted(WRITES))
def test_each_write_killed_or_failed_between_its_two_rows_leaves_neither(
        name: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Each of the six writing methods, its process killed after the catalog's statement and
    before the log's, and then the same write failing there in process: the catalog's rows and the
    log's are what they were, both times. Inside a batch, a failed write whose caller catches the
    error and goes on leaves neither row either, and the batch commits the rest, the write made
    before the failed one and the write made after it, each with its log row."""
    method, write = WRITES[name]
    db = tmp_path / "catalog.sqlite"
    cat = VaultCatalog(db)
    ready(cat)
    catalog, log, log_chains = catalog_rows(cat), all_rows(cat), chain_rows(cat)
    cat.close()

    def unchanged(cat: VaultCatalog) -> None:
        assert (catalog_rows(cat), all_rows(cat), chain_rows(cat)) == (catalog, log, log_chains)
        assert_consistent(cat)

    env = {**os.environ, LANDING_LOG_KEY: LANDING_LOG_TEST_KEY}
    done = subprocess.run([sys.executable, "-c", _KILL, str(db), name], env=env,
                          cwd=Path(__file__).resolve().parents[2], check=False)
    assert done.returncode == 9
    cat = VaultCatalog(db)
    unchanged(cat)

    def boom(*args: Any, **kwargs: Any) -> None:
        raise RuntimeError("between the two rows")

    monkeypatch.setattr(cat._log, method, boom)
    with pytest.raises(RuntimeError):
        write(cat)
    unchanged(cat)
    monkeypatch.undo()
    with cat.deferred():
        cat.record("e.md", "de", "E")                   # the batch's write before the failed one
        monkeypatch.setattr(cat._log, method, boom)
        with pytest.raises(RuntimeError):
            write(cat)                                  # failed, and the caller goes on
        monkeypatch.undo()
        cat.record("c.md", "dc", "C")
    rows = catalog_rows(cat)
    assert {k: v for k, v in rows.items() if k not in ("c.md", "e.md")} == catalog
    assert (rows["e.md"][:2], rows["c.md"][:2]) == (("de", "E"), ("dc", "C"))
    now = {(r[0], r[1]): r for r in all_rows(cat)}
    then = {(r[0], r[1]): r for r in log}
    assert {k: now[k] for k in then} == then
    assert [now[k][4] for k in sorted(now.keys() - then.keys())] == ["e.md", "c.md"]  # the stores
    assert chain_rows(cat) == log_chains
    assert_consistent(cat)
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
    block = cat.read_at(solo, cat.head(solo))[1:-1]
    kinds = [(r.kind, r.source_path) for r in block]
    assert kinds == [("store", "v/a.md"), ("store", "v/b.md"), ("retire", "v/b.md"),
                     ("store", "v/c.md"), ("move", "v/c.md"), ("store", "v/d.md")]
    # a tombstoned path's store is closed at its tombstone, and an active path's is open, so the
    # closing-stamp read at the head serves the active paths alone
    assert [r.closed_at for r in block] == [None, block[2].seq, None, block[4].seq, None, None]
    assert paths_held(cat, Provenance.AUTHORED_SOLO) == ["v/a.md", "v/d.md"]
    assert paths_held(cat, Provenance.CURATED) == []
    state = cat.state_at(Provenance.AUTHORED_SOLO, "v/b.md", heads(cat))
    assert state is not None and state.kind == "retire"
    assert_consistent(cat)
    assert_three_reads(cat)
    head = heads(cat)
    cat.close()
    assert heads(VaultCatalog(db)) == head                  # one genesis: a reopen adds nothing


def test_a_relabel_into_a_class_with_rows_changes_no_row_and_every_chain_verifies() -> None:
    """The relabel rewrites the label of the class's chains and nothing else: no row of the log,
    a closed row and a hole among them, and no chain's id, secret or key check."""
    cat = VaultCatalog(Path(":memory:"))
    cat.record("a.md", "d1", "A", provenance=Provenance.AUTHORED_SOLO)
    cat.record("b.md", "d2", "B", provenance=Provenance.CURATED)
    cat.record("b.md", "d5", "B", provenance=Provenance.CURATED)    # b's first store closed
    cat.record("c.md", "d3", "C", provenance=Provenance.CURATED)
    cat.record("c.md", "d6", "C", provenance=Provenance.CURATED)
    assert cat.remove_digest("d3") == 0                             # c's first store a hole
    rows, before = all_rows(cat), chain_rows(cat)
    log = log_rows(cat)
    assert any(r.closed_at is not None and not r.hole for r in log)
    assert any(r.hole for r in log)
    assert cat.relabel_provenance("curated", "authored-solo") == 2
    assert all_rows(cat) == rows
    assert [(c, s, k) for c, _, s, k in chain_rows(cat)] == [(c, s, k) for c, _, s, k in before]
    assert len(cat.chains(Provenance.AUTHORED_SOLO)) == 2 and cat.chains("curated") == []
    assert_consistent(cat)
    cat.record("b.md", "d4", "B", provenance=Provenance.AUTHORED_SOLO)   # stays in its chain
    state = cat.state_at(Provenance.AUTHORED_SOLO, "b.md", heads(cat))
    assert state is not None and state.chain == 2 and state.digest == "d4"
    assert_consistent(cat)
    assert_three_reads(cat)


def test_a_history_over_two_chains_of_a_class_follows_a_rule_of_the_prefixes() -> None:
    """A path has events in two chains of one class only after it changed class and a relabel
    merged the two classes. Its history over the class is oldest first in each chain, with the
    chains it left first and the one that holds its present last: a rule of the prefixes, not the
    order the versions landed in (d1, d2, d3 here), so across the chains the read at an earlier
    cut is not a prefix of the read at a later one. Chain by chain it is, and the state at the
    head is the path's present."""
    solo = Provenance.AUTHORED_SOLO
    cat = VaultCatalog(Path(":memory:"))
    cat.record("p.md", "d1", "t", provenance=solo)                  # chain 1
    cat.record("p.md", "d2", "t", provenance=Provenance.CURATED)     # leaves 1 for chain 2
    early = heads(cat)
    cat.record("p.md", "d3", "t", provenance=solo)                  # leaves 2, back in 1
    cat.relabel_provenance("curated", "authored-solo")
    assert cat.chains(solo) == [1, 2]
    then = cat.history_at(solo, "p.md", early)
    now = cat.history_at(solo, "p.md", heads(cat))
    assert [r.digest for r in then] == ["d1", "d2"]
    assert [r.digest for r in now] == ["d2", "d1", "d3"]
    assert now[:len(then)] != then
    for ch in (1, 2):
        mine = [r for r in now if r.chain == ch]
        assert [r.seq for r in mine] == sorted(r.seq for r in mine)
        assert mine[:len([r for r in then if r.chain == ch])] == [r for r in then if r.chain == ch]
    state = cat.state_at(solo, "p.md", heads(cat))
    assert state is not None and (state.chain, state.digest) == (1, "d3")
    assert_consistent(cat)
    assert_three_reads(cat)


def test_a_purged_old_version_of_a_live_path_is_a_hole_by_the_three_reads() -> None:
    cat = VaultCatalog(Path(":memory:"))
    for d in ("d1", "d2", "d3"):
        cat.record("live.md", d, "L", version=int(d[1]))
    (chain,) = cat.chains(Provenance.AUTHORED_SOLO)
    at_d2 = next(r.seq for r in cat.read_at(chain, cat.head(chain)) if r.digest == "d2")
    assert cat.active_refs("d2") == 0                    # purge_raw's gate lets it through
    assert cat.remove_digest("d2") == 0                  # no catalog row held it
    cut = {chain: at_d2}
    state = cat.state_at(Provenance.AUTHORED_SOLO, "live.md", cut)
    assert state is not None and state.hole and state.seq == at_d2 and state.kind == "store"
    assert emptied(state) and state.version == 2         # §6.1: the content goes, the count stays
    assert state.path_key == cat._log.path_key(chain, "live.md")
    held = cat.cuts([Provenance.AUTHORED_SOLO]).held(Cut.of(cut))
    assert held.count() == 0 and held.holes() == 1      # no version: the hole, counted as one
    history = cat.history_at(Provenance.AUTHORED_SOLO, "live.md", cut)
    assert [r.digest for r in history] == ["d1", None] and history[-1].hole
    assert fold(cat, cut).last[(chain, state.path_key)] == state
    assert catalog_rows(cat)["live.md"][0] == "d3"
    # the live path keeps its name on its other rows, so the hole stays tied to it
    assert [r.seq for r in log_rows(cat) if r.hole] == [at_d2]
    assert_consistent(cat)
    assert_three_reads(cat)


def test_a_purge_of_every_version_of_a_deleted_note_leaves_no_row_that_names_it(
        tmp_path: Path) -> None:
    """`purge_raw`'s case: a note that declared its identity and changed class, deleted from the
    vault, then each of its digests purged by `remove_digest`. While one of its versions keeps its
    content the path's other rows keep its name; once none does, its `leave` and its `retire` are
    emptied too, so no row names the path or the identity, or carries the date of its delete; the
    holes keep their keys and positions. Another note held one of the digests before: its row of
    that digest is emptied too, as every row of a digest is, and its later version keeps its name
    on its other rows. After a vacuum no byte of the file holds either name of the purged note."""
    db = tmp_path / "catalog.sqlite"
    cat = VaultCatalog(db)
    cat.record("keep.md", "dp1", "K")                   # an earlier version, the bytes of dp1
    cat.record("keep.md", "dk", "K")
    note = "notes/private-topic.md"
    cat.record(note, "dp1", "Private", doc_id="id-private")
    cat.record(note, "dp2", "Private", provenance=Provenance.CURATED)   # a `leave` in chain 1
    cat.tombstone(note)
    assert cat.active_refs("dp1") == cat.active_refs("dp2") == 0
    cat.remove_digest("dp2")
    assert {r.kind for r in log_rows(cat) if r.source_path == note} == {"store", "leave", "retire"}
    assert_consistent(cat)
    cat.remove_digest("dp1")
    rows = log_rows(cat)
    assert all(note not in (r.source_path, r.doc_id) and r.doc_id != "id-private" for r in rows)
    assert all(r.digest != "dp1" for r in rows)          # keep.md's row of it as well
    holes = [r for r in rows if r.hole]
    assert sorted(r.kind for r in holes) == ["leave", "retire", "store", "store", "store"]
    assert all(emptied(r) and r.path_key is not None for r in holes)
    assert cat.get(note) is None and cat.get("keep.md") is not None
    assert_consistent(cat)
    assert_three_reads(cat)
    cat.close()
    with sqlite3.connect(db) as conn:
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchall()
        conn.execute("VACUUM")
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchall()
    data = b"".join(f.read_bytes() for f in tmp_path.glob("catalog.sqlite*"))
    assert b"keep.md" in data
    assert b"private-topic" not in data and b"id-private" not in data


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
        # a salt nulled with the content kept, or the content then rewritten: a row that no
        # purge leaves, so it is not taken for a hole
        ("UPDATE landings SET salt = NULL WHERE chain = ? AND seq = 4", 4, "a hole keeps content"),
        ("UPDATE landings SET salt = NULL, digest = 'forged', title = 'forged' "
         "WHERE chain = ? AND seq = 3", 3, "a hole keeps content"),
        (f"UPDATE landings SET {EMPTY}, at = '2000-01-01T00:00:00' WHERE chain = ? AND seq = 5",
         5, "a hole keeps content"),
    ]
    # a row emptied as a purge empties it but for one column of the content, which it keeps:
    # each column alone is content a hole must not keep
    assert CONTENT == ["source_path", "doc_id", "digest", "title", "at"]
    for kept in CONTENT:
        others = ", ".join(f"{column} = NULL" for column in CONTENT if column != kept)
        edits.append((f"UPDATE landings SET salt = NULL, {others} WHERE chain = ? AND seq = 4",
                      4, "a hole keeps content"))
    for edit, seq, why in edits:
        cat._conn.execute("SAVEPOINT edit")
        cat._conn.execute(edit, [chain])
        check = cat.verify(chain)
        assert not check.ok and check.failed_at == seq and check.why == why
        cat._conn.execute("ROLLBACK TO edit")
        cat._conn.execute("RELEASE edit")
        assert cat.verify(chain).ok
    cat._conn.execute(f"UPDATE landings SET {EMPTY} WHERE chain = ? AND seq = 4", [chain])
    assert cat.verify(chain).ok                          # a hole as a purge leaves it verifies
    cat._conn.execute("DELETE FROM landings WHERE chain = ? AND seq = 3", [chain])
    check = cat.verify(chain)
    assert not check.ok and check.failed_at == 3


def test_without_the_secret_what_appends_or_seeks_a_path_by_its_key_refuses(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The secret keys a path: the genesis, every write that appends a row (a `record` or a
    `tombstone` that changes the map, the re-key), `remove`, which seeks the path's rows by their
    key, and the two reads by path refuse without it and write nothing. A relabel and a purge by
    digest append no row and find their rows without the key, a write that changes nothing
    appends nothing, and the other reads read the rows as they are: none of these needs it."""
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
    cat.record("old.md", "d0", "O")
    cat.tombstone("old.md")
    cat.record("c.md", "d3", "C", provenance=Provenance.CURATED)
    head, log, catalog = heads(cat), all_rows(cat), catalog_rows(cat)
    cat.close()
    monkeypatch.delenv(LANDING_LOG_KEY)
    cat = VaultCatalog(db)                               # an open after the genesis needs none
    (solo,) = cat.chains(Provenance.AUTHORED_SOLO)
    refused = [
        lambda: cat.record("b.md", "d2", "B"),
        lambda: cat.record("a.md", "d9", "A"),
        lambda: cat.tombstone("a.md"),
        lambda: cat.migrate_rekey_doc_id("a.md", "id-new", declaration=owner_declaration()),
        lambda: cat.remove("a.md"),
        lambda: cat.state_at(Provenance.AUTHORED_SOLO, "a.md", head),
        lambda: cat.history_at(Provenance.AUTHORED_SOLO, "a.md", head),
    ]
    for call in refused:
        with pytest.raises(LandingLogKeyMissing):
            call()
    assert (heads(cat), all_rows(cat), catalog_rows(cat)) == (head, log, catalog)
    cat.record("a.md", "d1", "A")                        # changes nothing: appends nothing
    cat.tombstone("nowhere.md")
    assert cat.relabel_provenance("curated", "observed") == 1
    assert cat.remove_digest("d0") == 1                  # old.md: its store and its retire
    assert heads(cat) == head and cat.get("old.md") is None
    assert all(r.source_path != "old.md" for r in log_rows(cat))
    assert cat.read_at(solo, 2) == cat.read_at(solo, cat.head(solo))[:2]
    assert cat.read_between(solo, 1, 3) == cat.read_at(solo, 3)[1:]
    assert paths_held(cat, Provenance.AUTHORED_SOLO, head) == ["a.md"]
    assert cat.chains(Provenance.OBSERVED) and all(cat.verify(c).ok for c in chains(cat))
    assert_consistent(cat)
    cat.close()


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


def test_every_statement_by_path_seeks_the_key_index() -> None:
    """A write or a read of one path touches that path's rows through `landings_path`, never by
    walking the chain: on the corpus's 400,274 rows the planner took the primary key for the
    closing stamp's update, and a landing took 40 ms where it takes tens of microseconds. A
    purge by digest walks the log twice, for the digest and for the names, which have no index;
    it empties the digest's rows by their positions and reaches each path's rows by their key."""
    cat = VaultCatalog(Path(":memory:"))
    for i in range(50):
        cat.record(f"p{i}.md", f"d{i}", "t")
    (chain,) = cat.chains(Provenance.AUTHORED_SOLO)
    cat.tombstone("p5.md")
    seen: list[str] = []
    cat._conn.set_trace_callback(seen.append)
    cat.record("p1.md", "new", "t")
    cat.tombstone("p2.md")
    cat.record("p4.md", "d4", "t", doc_id="another")
    cat.state_at(Provenance.AUTHORED_SOLO, "p1.md", {chain: 30})
    cat.history_at(Provenance.AUTHORED_SOLO, "p1.md", {chain: cat.head(chain)})
    cat.remove("p3.md")
    purge = len(seen)
    cat.remove_digest("d5")                             # p5's only version: its retire as well
    cat._conn.set_trace_callback(None)

    def plan(q: str) -> str:
        return " ".join(str(tuple(r)[-1]) for r in cat._conn.execute("EXPLAIN QUERY PLAN " + q))

    by_path = [q for q in seen if "path_key = " in q]
    assert len(by_path) >= 8
    for q in by_path:
        assert "landings_path" in plan(q), (q, plan(q))
    walks = [q for q in seen[purge:] if q.split(None, 1)[0] in ("SELECT", "UPDATE", "DELETE")
             and "SCAN landings" in plan(q)]
    assert len(walks) == 2, walks
    assert all(r.source_path != "p5.md" for r in log_rows(cat))
