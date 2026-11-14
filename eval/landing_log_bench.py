"""The landing log, measured (dn-temporal-snapshot §11; stage SN-1).

    uv run python -m eval.landing_log_bench --catalog COPY [--batch 10000] [--rounds 5]
                                            [--repeat 200] [--fresh 30000,100000] [--out PATH]

COPY is a copy of an instance's catalog file, never a live one: a copy-on-write clone of the file
with its `-wal` and `-shm` beside it (`cp -c`), which the harness migrates in place. It refuses the
catalog the configuration names. The landing log's secret is a random one made for the run and
dropped with it, so nothing written here can be read by path afterwards, and nothing needs to be.

Five measurements, the first four on the copy's own size:

1. **The migration.** The first open of the catalog with the log: the tables, their indexes and
   the genesis of every class the catalog holds, timed whole; the file's bytes before and after
   (the write-ahead log checkpointed into the file), and the bytes a row of the log takes in the
   table and in each index, from SQLite's `dbstat` table when it is compiled in.
2. **Its check.** Each chain verified from its first row, every commitment recomputed and every
   hash, timed; and the fold of the log compared with the catalog row by row.
3. **The write overhead.** Batches of catalog writes in one transaction each, as a landing batch
   writes its keys (`deferred()`): new paths, and new versions of paths the catalog holds, each
   timed three ways on the same file, the order turned over `--rounds`: `record` as built; the
   same with the log's appending switched off (a patch of `LandingLog.store`), which keeps the
   read of the path's row before the write, the explicit transaction and each write's savepoint
   that SN-1 added; and the write as `record` made it before SN-1 (`f969904e`), the upsert
   alone. The first against the third is what SN-1 adds to a key's write, and the first against
   the second what the log's rows add.
4. **The reads.** `state_at` and `history_at` of one path, the paths drawn from the catalog;
   every head at a tenth of the chain, at its middle and at its head, as the contents of the cut
   (`core/stores/cuts.py`, which replaced SN-1's `heads_at`): counted, the walk without a row
   built, and read as three columns (the position, the path's key, the digest); `read_at` and
   `read_between` of a thousand positions; `head`; and the keyed hash of a path alone. Medians
   with their ranges over `--repeat` (a whole-class read over five).
5. **Every head of a smaller chain.** With `--fresh`, for each size a new catalog beside the copy
   with that many paths of one class, landed through `record` in batches, its paths and titles of
   the corpus's lengths: the contents at its head counted and read as three columns, five times
   each, so the cost a head returned can be read apart from the walk. The file is removed after.

Timings are wall time on whatever else the machine is doing, so the load average is recorded at
the start and the end, and before each fresh chain, with the versions of Python and SQLite.
"""

from __future__ import annotations

import argparse
import contextlib
import functools
import json
import os
import platform
import random
import sqlite3
import statistics
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root on path

from core.kernel.provenance import Provenance  # noqa: E402
from core.stores.catalog import VaultCatalog, _utcnow  # noqa: E402
from core.stores.cuts import Cut  # noqa: E402

# The key's write as `record` made it before SN-1 (`core/stores/catalog.py` at `f969904e`): this
# upsert alone, in the batch's transaction, with no read of the row before it and no log.
_UPSERT_BEFORE = (
    "INSERT INTO vault_files (source_path, digest, title, provenance, active, updated_at, doc_id)"
    " VALUES (?, ?, ?, ?, 1, ?, ?)"
    " ON CONFLICT(source_path) DO UPDATE SET"
    "   digest=excluded.digest, title=excluded.title,"
    "   provenance=excluded.provenance, active=1, updated_at=excluded.updated_at")
ARMS = ("with", "without", "before")   # record as built; its log rows off; the write before SN-1
_THREE = ("path_key", "digest")         # with the position, which every read of rows carries


def _files(db: Path) -> dict[str, int]:
    out = {}
    for suffix in ("", "-wal", "-shm"):
        f = Path(f"{db}{suffix}")
        out[f.name] = f.stat().st_size if f.exists() else 0
    return out


def _checkpoint(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchall()


def _objects(conn: sqlite3.Connection) -> dict[str, int] | None:
    """The bytes each table and index takes, from `dbstat`, or None when SQLite lacks it."""
    try:
        rows = conn.execute("SELECT name, sum(pgsize) FROM dbstat GROUP BY name").fetchall()
    except sqlite3.OperationalError:
        return None
    return {str(name): int(size) for name, size in rows}


def _timed(fn: Callable[[], Any], n: int) -> dict[str, float]:
    """Median, low and high of `n` runs of `fn`, in microseconds."""
    times = []
    for _ in range(n):
        t0 = time.perf_counter()
        fn()
        times.append((time.perf_counter() - t0) * 1e6)
    return {"median_us": statistics.median(times), "low_us": min(times), "high_us": max(times),
            "runs": n}


def _fold(cat: VaultCatalog) -> dict[str, tuple[str, str, str, bool, str]]:
    """The catalog the log gives: each path's last event in the chain where it is not a `leave`,
    an active row for a `store`, a tombstoned one with its last `store`'s digest and title for a
    `retire` or a `move` (dn-temporal-snapshot §3.2)."""
    classes = {int(c): str(k) for c, k in cat._conn.execute(
        "SELECT chain, class FROM landing_chains")}
    last: dict[tuple[int, bytes], Any] = {}
    store: dict[tuple[int, bytes], Any] = {}
    names: dict[tuple[int, bytes], str] = {}
    for chain in classes:
        for row in cat._log.rows(chain):
            if row.path_key is None:
                continue
            k = (chain, row.path_key)
            last[k] = row
            if row.kind == "store":
                store[k] = row
            if row.source_path is not None:
                names[k] = row.source_path
    out: dict[str, tuple[str, str, str, bool, str]] = {}
    for k, name in names.items():
        row, kept = last[k], store.get(k)
        if row.kind == "leave":
            continue
        if row.kind == "store" and not row.hole:
            out[name] = (row.digest, row.title, classes[k[0]], True, row.doc_id)
        elif row.kind in ("retire", "move") and kept is not None and not kept.hole:
            out[name] = (kept.digest, kept.title, classes[k[0]], False, row.doc_id)
    return out


def _catalog(cat: VaultCatalog) -> dict[str, tuple[str, str, str, bool, str]]:
    return {str(r[0]): (str(r[1]), str(r[2]), str(r[3]), bool(r[4]), str(r[5]))
            for r in cat._conn.execute(
                "SELECT source_path, digest, title, provenance, active, doc_id FROM vault_files")}


def _batch(cat: VaultCatalog, records: list[tuple[str, str, str, Provenance]],
           arm: str) -> float:
    """One batch of records in one transaction, as a landing batch writes its keys, by one arm:
    `with`, `record` as built; `without`, the same with the log's appending switched off (the
    read of the row before, the explicit transaction and the savepoints kept); `before`, the
    upsert `record` ran before SN-1, alone. Seconds."""
    if arm == "before":
        conn = cat._conn
        t0 = time.perf_counter()
        try:
            for path, digest, title, cls in records:
                conn.execute(_UPSERT_BEFORE, [path, digest, title, str(cls), _utcnow(), path])
            conn.commit()
        except BaseException:
            conn.rollback()
            raise
        return time.perf_counter() - t0
    switch = (contextlib.nullcontext() if arm == "with"   # the control: no log row appended
              else mock.patch.object(cat._log, "store", lambda *a, **k: None))
    with switch:
        t0 = time.perf_counter()
        with cat.deferred():
            for path, digest, title, cls in records:
                cat.record(path, digest, title, provenance=cls)
        return time.perf_counter() - t0


def _fresh_heads(where: Path, n: int, key: bytes, batch: int) -> dict[str, Any]:
    """A new catalog of `n` paths of one class, landed through `record` in batches, its paths and
    titles about the corpus's lengths (28.6 and 63.8 characters): every head at its head, the
    contents of the cut counted and read as three columns, five times each. The file is removed
    after."""
    db = where / f"fresh-{n}.sqlite"
    for suffix in ("", "-wal", "-shm"):
        Path(f"{db}{suffix}").unlink(missing_ok=True)
    out: dict[str, Any] = {"paths": n, "load_start": os.getloadavg()}
    cat = VaultCatalog(db, key=key)
    try:
        for start in range(0, n, batch):
            with cat.deferred():
                for i in range(start, min(n, start + batch)):
                    cat.record(f"corpus/item-{i:08}-{'p' * 6}.md", f"{i:064x}",
                               f"{'t' * 56} {i:07}", provenance=Provenance.OBSERVED)
        (chain,) = cat.chains(Provenance.OBSERVED)
        head = cat.head(chain)
        held = cat.cuts([Provenance.OBSERVED]).held()
        out["chain_rows"] = head
        out["heads_columns"] = {**_timed(functools.partial(held.columns, *_THREE), 5),
                                "rows": held.count()}
        out["heads_count"] = _timed(held.count, 5)
        past = out["heads_columns"]["median_us"] - out["heads_count"]["median_us"]
        out["us_a_head_past_the_walk"] = past / max(1, out["heads_columns"]["rows"])
    finally:
        cat.close()
        for suffix in ("", "-wal", "-shm"):
            Path(f"{db}{suffix}").unlink(missing_ok=True)
    out["load_end"] = os.getloadavg()
    return out


def measure(db: Path, batch: int, rounds: int, repeat: int, seed: int,
            fresh: tuple[int, ...] = ()) -> dict[str, Any]:
    from core.kernel.config import get_config

    if db.resolve() == Path(get_config().paths.vault_catalog).resolve():
        raise SystemExit("refusing the configured instance's own catalog: give a copy")
    rng = random.Random(seed)
    key = os.urandom(32)
    out: dict[str, Any] = {"catalog_copy": db.name, "load_start": os.getloadavg(),
                           "python": platform.python_version(),
                           "sqlite": sqlite3.sqlite_version, "machine": platform.machine(),
                           "batch": batch, "rounds": rounds, "repeat": repeat, "seed": seed}
    with sqlite3.connect(db) as conn:
        out["catalog_rows"] = {f"{cls} {'active' if a else 'tombstoned'}": n for cls, a, n in
                               conn.execute("SELECT provenance, active, count(*) FROM vault_files "
                                            "GROUP BY provenance, active")}
        out["has_log_before"] = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE name = 'landings'").fetchone() is not None
        _checkpoint(conn)
        out["files_before"] = _files(db)
        out["objects_before"] = _objects(conn)

    t0 = time.perf_counter()
    cat = VaultCatalog(db, key=key)
    out["migration_s"] = time.perf_counter() - t0
    chains = {int(c): str(k) for c, k in cat._conn.execute(
        "SELECT chain, class FROM landing_chains ORDER BY chain")}
    out["chains"] = {str(c): {"class": k, "rows": cat.head(c)} for c, k in chains.items()}
    out["log_rows"] = sum(cat.head(c) for c in chains)
    _checkpoint(cat._conn)
    out["files_after"] = _files(db)
    out["objects_after"] = _objects(cat._conn)
    grown = sum(out["files_after"].values()) - sum(out["files_before"].values())
    out["growth_bytes"] = grown
    out["growth_bytes_a_row"] = grown / out["log_rows"] if out["log_rows"] else None
    objects = out["objects_after"]
    if objects is not None:
        names = ("landings", "landings_path", "landings_doc", "landings_closed", "landing_chains")
        out["bytes_a_row"] = {n: objects.get(n, 0) / out["log_rows"] for n in names}

    # the check: every chain verified, and the fold of the log against the catalog
    out["verify"] = {}
    for chain in chains:
        t0 = time.perf_counter()
        check = cat.verify(chain)
        out["verify"][str(chain)] = {"ok": check.ok, "rows": check.rows,
                                     "commitments": check.commitments,
                                     "seconds": time.perf_counter() - t0}
    t0 = time.perf_counter()
    out["fold_equals_catalog"] = _fold(cat) == _catalog(cat)
    out["fold_seconds"] = time.perf_counter() - t0

    # the reads, on the largest chain
    big = max(chains, key=lambda c: cat.head(c))
    cls = chains[big]
    head = cat.head(big)
    paths = [str(r[0]) for r in cat._conn.execute(
        "SELECT source_path FROM vault_files WHERE provenance = ?", [cls])]
    sample = rng.sample(paths, min(repeat, len(paths)))
    mid = head // 2
    reads: dict[str, Any] = {"chain": big, "class": cls, "head": head}
    it = iter(sample * 2)
    reads["path_key"] = _timed(lambda: cat._log.path_key(big, next(it)), len(sample))
    it = iter(sample * 2)
    reads["state_at_mid"] = _timed(lambda: cat.state_at(cls, next(it), {big: mid}), len(sample))
    it = iter(sample * 2)
    reads["history_at_head"] = _timed(lambda: cat.history_at(cls, next(it), {big: head}),
                                      len(sample))
    starts = [rng.randrange(0, max(1, head - 1000)) for _ in range(repeat)]
    its = iter(starts * 2)
    reads["read_between_1000"] = _timed(lambda: cat.read_between(big, (a := next(its)), a + 1000),
                                        repeat)
    reads["read_at_1000"] = _timed(lambda: cat.read_at(big, 1000), repeat)
    reads["head"] = _timed(lambda: cat.head(big), repeat)
    ev = cat.cuts([cls])
    for name, c in (("tenth", head // 10), ("mid", mid), ("head", head)):
        contents = ev.held(Cut.of({big: c}))
        # every head as the contents of the cut: counted, the walk without a row built, and read
        # as three columns, one buffer a column
        reads[f"heads_count_{name}"] = {**_timed(contents.count, 5), "rows": contents.count()}
        reads[f"heads_columns_{name}"] = _timed(functools.partial(contents.columns, *_THREE), 5)
    out["reads"] = reads

    # the write overhead: new paths, then new versions of held paths, by each arm in turn
    writes: dict[str, Any] = {kind: {arm: [] for arm in ARMS} for kind in ("new", "changed")}
    held = rng.sample(paths, min(batch * rounds * len(ARMS), len(paths)))
    n = 0
    for r in range(rounds):
        for arm in ARMS[r % len(ARMS):] + ARMS[:r % len(ARMS)]:
            new = [(f"bench/r{r}/{arm}/{i:06}.md", f"bench-{r}-{arm}-{i}", f"bench {i}",
                    Provenance(cls)) for i in range(batch)]
            secs = _batch(cat, new, arm)
            writes["new"][arm].append(secs / batch * 1e6)
            changed = [(p, f"changed-{r}-{arm}-{i}", f"changed {i}", Provenance(cls))
                       for i, p in enumerate(held[n:n + batch])]
            n += batch
            secs = _batch(cat, changed, arm)
            writes["changed"][arm].append(secs / len(changed) * 1e6)
    for kind in ("new", "changed"):
        w = writes[kind]
        for arm in ARMS:
            w[f"{arm}_median_us"] = statistics.median(w[arm])
        w["sn1_adds_us"] = w["with_median_us"] - w["before_median_us"]
        w["log_rows_add_us"] = w["with_median_us"] - w["without_median_us"]
    out["writes_us_a_record"] = writes
    out["verify_after_writes"] = all(cat.verify(c).ok for c in cat._log.all_chains())
    _checkpoint(cat._conn)
    out["files_end"] = _files(db)
    out["load_end"] = os.getloadavg()
    cat.close()
    out["fresh_chains"] = [_fresh_heads(db.parent, n, key, batch) for n in fresh]
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--catalog", type=Path, required=True,
                    help="a copy of a catalog file, migrated in place")
    ap.add_argument("--batch", type=int, default=10_000)
    ap.add_argument("--rounds", type=int, default=5)
    ap.add_argument("--repeat", type=int, default=200)
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--fresh", default="",
                    help="sizes of fresh one-class chains to read every head of, comma separated")
    ap.add_argument("--out", type=Path)
    args = ap.parse_args(argv)
    fresh = tuple(int(n) for n in args.fresh.split(",") if n.strip())
    out = measure(args.catalog, args.batch, args.rounds, args.repeat, args.seed, fresh)
    text = json.dumps(out, indent=2, default=str)
    if args.out:
        args.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
