"""The attestation ledger's output-hash table (core/attestation/store.py).

The producer lookups read a side table, one row for each element of each record's
`output_hashes`, written by a trigger on the ledger. Laws, over generated ledgers (records sharing
hashes, naming a hash twice, naming none, appended twice, appended in a deferred block that
commits or dies):

1. after any sequence of appends the table is a scan of the ledger, element for element;
2. each of the four lookups answers what the scan answers: `producers_of`, `producers_by_output`
   (against the json_each statement it replaced, kept here with its temporary table renamed and
   a commit added, since the original left its transaction open), and `attested_by` and
   `already_attested` through `core/ingest/landing.py` (against the same functions over a store
   that has only the scan);
3. a ledger the old code wrote gets the table on its first open, and from then on every append,
   by this class or by any other writer of the table, writes its rows in its own statement;
4. a ledger the old code wrote, opened while another connection holds its write lock, by a
   process that cannot write it, or when it is full, opens at once and answers every lookup from
   the records, as the old code did, until the table exists.
"""

from __future__ import annotations

import json
import sqlite3
import tempfile
from pathlib import Path
from typing import Any

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from core.attestation import Attestation, AttestationStore, StoreAttestor
from core.ingest.landing import already_attested, attested_batch, attested_by

HASHES = [f"h{i}" for i in range(6)]
ACTIONS = ["capture", "ingest_note", "dream_pass"]

record = st.tuples(st.sampled_from(ACTIONS), st.lists(st.sampled_from(HASHES), max_size=4),
                   st.lists(st.sampled_from(HASHES), max_size=2), st.integers(0, 3))
step = st.one_of(st.tuples(st.just("append"), record),
                 st.tuples(st.just("again")),
                 st.tuples(st.just("deferred"), st.lists(record, min_size=1, max_size=3),
                           st.booleans()))
SETTINGS = settings(deadline=None, max_examples=80,
                    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large])


def _att(action: str, outputs: list[str], inputs: list[str], stamp: int) -> Attestation:
    return Attestation.create(timestamp=f"2026-11-11T00:00:0{stamp}", agent_role="role",
                              action=action, constitution_fingerprint="F",
                              input_hashes=inputs, output_hashes=outputs)


def run(store: AttestationStore, steps: list[Any]) -> None:
    last: Attestation | None = None
    for s in steps:
        if s[0] == "append":
            last = store.append(_att(*s[1]))
        elif s[0] == "again" and last is not None:
            store.append(last)                          # a re-emission: a no-op
        elif s[0] == "deferred":
            _, records, dies = s
            try:
                with store.deferred():
                    for r in records:
                        last = store.append(_att(*r))
                    if dies:
                        raise RuntimeError("the block dies before its commit")
            except RuntimeError:
                last = None


def scan(store: AttestationStore) -> set[tuple[str, str, str, int]]:
    return {(h, a.id, a.action, pos) for a in store.all() for pos, h in
            enumerate(a.output_hashes)}


def table(store: AttestationStore) -> set[tuple[str, str, str, int]]:
    return {(str(h), str(i), str(a), int(p)) for h, i, a, p in store._conn.execute(
        "SELECT hash, att_id, action, pos FROM output_hashes")}


def old_producers_by_output(store: AttestationStore,
                            hashes: set[str]) -> dict[str, list[tuple[str, str]]]:
    """The statement the table replaced: one json_each pass over every record (its temporary
    table renamed, and committed, which the original was not)."""
    out: dict[str, list[tuple[str, str]]] = {h: [] for h in hashes}
    if not hashes:
        return out
    conn = store._conn
    conn.execute("CREATE TEMP TABLE IF NOT EXISTS wanted_old (h TEXT PRIMARY KEY)")
    conn.execute("DELETE FROM wanted_old")
    conn.executemany("INSERT OR IGNORE INTO wanted_old VALUES (?)", [(h,) for h in hashes])
    rows = conn.execute("SELECT j.value, a.action, a.id FROM attestations a, "
                        "json_each(a.payload_json, '$.output_hashes') j "
                        "WHERE j.value IN (SELECT h FROM wanted_old)").fetchall()
    conn.execute("DELETE FROM wanted_old")
    conn.commit()
    for h, action, att_id in rows:
        out[str(h)].append((str(action), str(att_id)))
    return {h: sorted(ps) for h, ps in out.items()}


class ScanOnly:
    """A ledger with the old lookups alone: the producers by a decode of every record."""

    def __init__(self, store: AttestationStore) -> None:
        self.store = store

    def producers_of(self, hashes: set[str]) -> set[str]:
        return {a.id for a in self.store.all() if hashes & set(a.output_hashes)}

    def get(self, att_id: str) -> Attestation | None:
        return self.store.get(att_id)


def assert_lookups_agree(store: AttestationStore) -> None:
    new = StoreAttestor(store)
    old: Any = type("A", (), {"store": ScanOnly(store)})()
    for size in (0, 1, 2, 3):
        for i in range(len(HASHES) - size + 1):
            hs = set(HASHES[i:i + size]) | ({"absent"} if size == 3 else set())
            assert store.producers_of(hs) == ScanOnly(store).producers_of(hs)
            assert store.producers_by_output(hs) == old_producers_by_output(store, hs)
            assert attested_batch(new, hs) == old_producers_by_output(store, hs)
    for h in [*HASHES, "absent", ""]:
        for action in ACTIONS:
            assert attested_by(new, action, h) == attested_by(old, action, h)
            assert already_attested(new, action, h) == already_attested(old, action, h)


@SETTINGS
@given(steps=st.lists(step, min_size=1, max_size=10))
def test_the_table_is_a_scan_of_the_ledger_and_the_lookups_agree(steps: list[Any]) -> None:
    with tempfile.TemporaryDirectory() as d:
        store = AttestationStore(Path(d) / "att.sqlite")
        run(store, steps)
        assert table(store) == scan(store)
        assert_lookups_agree(store)
        store.close()


_OLD_DDL = """
CREATE TABLE IF NOT EXISTS attestations (
    id           TEXT PRIMARY KEY,
    timestamp    TEXT NOT NULL,
    agent_role   TEXT NOT NULL,
    action       TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    signature    TEXT NOT NULL,
    signer       TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS att_role_ts ON attestations(agent_role, timestamp);
"""


def _old_append(conn: sqlite3.Connection, att: Attestation) -> None:
    """An append as the code before the table made it (and as any other writer of the table)."""
    conn.execute("INSERT OR IGNORE INTO attestations VALUES (?, ?, ?, ?, ?, ?, ?)",
                 [att.id, att.timestamp, att.agent_role, att.action,
                  json.dumps(att.to_dict(), separators=(",", ":")), att.signature, att.signer])
    conn.commit()


@SETTINGS
@given(records=st.lists(record, max_size=8), later=st.lists(record, max_size=4))
def test_a_ledger_the_old_code_wrote_gets_its_table_on_first_open(records: list[Any],
                                                                   later: list[Any]) -> None:
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "att.sqlite"
        conn = sqlite3.connect(str(path))
        conn.executescript(_OLD_DDL)
        for r in records:
            _old_append(conn, _att(*r))
        conn.close()
        store = AttestationStore(path)                       # the migration
        assert table(store) == scan(store)
        assert_lookups_agree(store)
        raw = sqlite3.connect(str(path))
        for r in later:                                      # a writer of the table alone
            _old_append(raw, _att(*r))
        raw.close()
        assert table(store) == scan(store)
        assert_lookups_agree(store)
        store.close()


def test_an_append_that_dies_leaves_neither_its_record_nor_its_rows(tmp_path: Path) -> None:
    store = AttestationStore(tmp_path / "att.sqlite")
    kept = store.append(_att("capture", ["h1"], ["h1"], 0))
    with pytest.raises(RuntimeError), store.deferred():
        store.append(_att("capture", ["h2", "h2"], ["h2"], 1))
        raise RuntimeError("died after the record, before the commit")
    assert {a.id for a in store.all()} == {kept.id}
    assert table(store) == {("h1", kept.id, "capture", 0)}
    assert store.producers_of({"h2"}) == set()


def test_a_record_that_names_a_hash_twice_is_its_producer_once_and_listed_twice(
        tmp_path: Path) -> None:
    store = AttestationStore(tmp_path / "att.sqlite")
    a = store.append(_att("capture", ["h1", "h1"], ["h1"], 0))
    assert store.producers_of({"h1"}) == {a.id}
    assert store.producers_by_output({"h1"}) == {"h1": [("capture", a.id), ("capture", a.id)]}
    assert attested_by(StoreAttestor(store), "capture", "h1") == [a.id]
    assert store.producers_by_output({"h1"}) == old_producers_by_output(store, {"h1"})


def test_the_lookup_is_a_seek_of_the_table(tmp_path: Path) -> None:
    store = AttestationStore(tmp_path / "att.sqlite")
    plan = " ".join(str(r[3]) for r in store._conn.execute(
        "EXPLAIN QUERY PLAN SELECT att_id FROM output_hashes WHERE hash IN (?)", ["h"]))
    assert "SEARCH output_hashes USING PRIMARY KEY (hash=?)" in plan


def _old_ledger(path: Path, records: list[Any]) -> list[Attestation]:
    conn = sqlite3.connect(str(path))
    conn.executescript(_OLD_DDL)
    atts = [_att(*r) for r in records]
    for a in atts:
        _old_append(conn, a)
    conn.close()
    return atts


OLD = [("capture", ["h1", "h2"], ["h1"], 0), ("capture", ["h2", "h2"], ["h2"], 1),
       ("ingest_note", ["h3"], ["h1", "h3"], 2), ("dream_pass", [], ["h4"], 3)]


def test_a_ledger_opened_while_another_holds_its_lock_answers_from_the_records(
        tmp_path: Path) -> None:
    """The migration does not wait for the lock: the ledger opens at once, the lookups pass over
    the records (also inside a deferred block, whose own appends they see), and the first lookup
    after the lock is free, outside a transaction, makes the table."""
    import time

    path = tmp_path / "att.sqlite"
    _old_ledger(path, OLD)
    raw = sqlite3.connect(str(path), isolation_level=None)
    raw.execute("BEGIN IMMEDIATE")                       # another connection's write lock
    t0 = time.perf_counter()
    store = AttestationStore(path)
    assert time.perf_counter() - t0 < 2 and not store._has_outputs()
    assert_lookups_agree(store)
    raw.execute("ROLLBACK")
    raw.close()
    with store.deferred():
        new = store.append(_att("capture", ["h5"], ["h5"], 3))
        assert store.producers_of({"h5"}) == {new.id}     # the block's own append, by the scan
        assert not store._has_outputs()                  # not made inside the block
    assert store.producers_by_output({"h5"}) == {"h5": [("capture", new.id)]}
    assert store._has_outputs() and table(store) == scan(store)
    assert_lookups_agree(store)
    store.close()


def test_a_ledger_this_process_cannot_write_opens_and_answers_from_the_records(
        tmp_path: Path) -> None:
    import os
    import stat

    path = tmp_path / "att.sqlite"
    atts = _old_ledger(path, OLD)
    os.chmod(path, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    try:
        store = AttestationStore(path)
        assert not store._has_outputs()
        assert store.producers_of({"h2"}) == {atts[0].id, atts[1].id}
        assert_lookups_agree(store)
        store.close()
    finally:
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)


def test_a_ledger_whose_migration_fails_opens_and_answers_from_the_records(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A full file (SQLite refuses its next page, as a full disk refuses a write): the migration
    is rolled back, the ledger opens and answers every lookup from the records, as the old code
    did, and does not try the migration again until it is opened again; an append fails, as any
    write to a full file does. The next open makes the table."""
    path = tmp_path / "att.sqlite"
    atts = _old_ledger(path, OLD)
    connect = sqlite3.connect

    def full(*args: Any, **kwargs: Any) -> sqlite3.Connection:
        conn = connect(*args, **kwargs)
        (pages,) = conn.execute("PRAGMA page_count").fetchone()
        conn.execute(f"PRAGMA max_page_count = {pages}")         # not one page more
        return conn

    monkeypatch.setattr(sqlite3, "connect", full)
    store = AttestationStore(path)
    assert not store._has_outputs() and not store._conn.in_transaction
    ran: list[str] = []
    store._conn.set_trace_callback(ran.append)
    assert store.producers_of({"h2"}) == {atts[0].id, atts[1].id}
    assert_lookups_agree(store)
    assert not any("BEGIN IMMEDIATE" in s for s in ran)        # not tried again
    store._conn.set_trace_callback(None)
    with pytest.raises(sqlite3.OperationalError, match="full"):
        store.append(_att("capture", [f"x{i}" for i in range(2000)], ["h1"], 0))
    assert not store._has_outputs() and store.count() == len(OLD)
    store.close()
    monkeypatch.undo()
    again = AttestationStore(path)
    assert again._has_outputs() and table(again) == scan(again)
    assert_lookups_agree(again)
    again.close()
