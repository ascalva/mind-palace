"""The algebra of cuts, measured (dn-temporal-snapshot §4.4, §11; stage SN-1b).

    uv run python -m eval.cut_algebra_bench --catalog COPY [--history 200000] [--repeat 5]
                                            [--batch 10000] [--seed 13] [--out PATH]

COPY is a copy of an instance's catalog file, never a live one: a copy-on-write clone of the file
with its `-wal` and `-shm` beside it (`cp -c`), which the harness migrates in place and then
writes a history into. It refuses the catalog the configuration names. The landing log's secret is
a random one made for the run and dropped with it, as SN-1's harness makes it
(`eval/landing_log_bench.py`, whose timing helpers this one uses).

The measurements, on the copy's largest chain:

1. **Every head.** At the head of the genesis, before any history: SN-1's `heads_at`, a row in
   Python a head, against the contents of the cut (`core/stores/cuts.py`): counted, which builds
   no row, and read as columns, the three a head is named by (its position, its path's key, its
   digest) and the seven a listing shows. The bar is SNF-6's tenth of a second.
2. **A history.** `--history` catalog writes after the genesis, landed through `record` and
   `tombstone` in batches of `--batch`, in a shuffled order: a new version of a held path for half
   of them, a retire of another held path for a quarter, a new path for the rest. Each appends one
   row, so the history is that many positions.
3. **The signed difference.** From the head less 1, 1,000, 100,000 and the whole history, and from
   the bottom, to the head: its counts (one statement), its sizes, its two sides read as columns,
   and its rows sorted into removed, added and replaced; against two of SN-1's `heads_at` calls
   and a set difference of their rows. The two give the same rows.
4. **A family.** Ten cuts spread evenly over the history: the count at each, walked by the
   differences against ten counts; what persisted through all, what existed in any, and the
   sizes of the pairwise differences; and what persisted from the horizon to the head.
5. **The plans.** The statements of what a cut holds, the rows come and the rows gone, as SQLite
   plans them on the copy.

Timings are wall time on whatever else the machine is doing, medians with their ranges over
`--repeat` runs; the load average is recorded at the start, before the history and at the end,
with the versions of Python, SQLite and NumPy.
"""

from __future__ import annotations

import argparse
import functools
import hashlib
import json
import os
import platform
import random
import sqlite3
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root on path

from core.kernel.provenance import Provenance  # noqa: E402
from core.stores.catalog import VaultCatalog  # noqa: E402
from core.stores.cuts import Cut, Evaluation, Text  # noqa: E402
from core.stores.landings import Landing  # noqa: E402
from eval.landing_log_bench import _checkpoint, _timed  # noqa: E402

BAR_S = 0.1                     # SNF-6: every head read in a tenth of a second
THREE = ("path_key", "digest")  # with `seq`, which every read carries: what names a head
LISTING = ("path_key", "source_path", "doc_id", "digest", "title", "version")


def _ms(t: dict[str, float]) -> dict[str, float]:
    return {"median_ms": t["median_us"] / 1e3, "low_ms": t["low_us"] / 1e3,
            "high_ms": t["high_us"] / 1e3, "runs": t["runs"]}


def _rows_a_head(cat: VaultCatalog, cls: str, cut: dict[int, int]) -> list[Landing]:
    """Every head as SN-1 read it (`VaultCatalog.heads_at`): a `Landing` a row."""
    return cat.heads_at(cls, cut)


def _seqs(rows: list[Landing]) -> set[tuple[int, int]]:
    """The versions among SN-1's rows, by their positions: a hole is no version."""
    return {(r.chain, r.seq) for r in rows if not r.hole}


def _pairs(cols: Any) -> set[tuple[int, int]]:
    return set(zip(cols.ints("chain").tolist(), cols.ints("seq").tolist(), strict=True))


def _plan(conn: sqlite3.Connection, run: Callable[[], object]) -> list[str]:
    """How SQLite plans the statements `run` makes, one line a statement."""
    seen: list[str] = []
    conn.set_trace_callback(seen.append)
    try:
        run()
    finally:
        conn.set_trace_callback(None)
    return [" | ".join(str(tuple(r)[-1]) for r in conn.execute("EXPLAIN QUERY PLAN " + q))
            for q in seen]


def every_head(cat: VaultCatalog, ev: Evaluation, chain: int, cls: str,
               repeat: int) -> dict[str, Any]:
    """Every head at the evaluation's head: SN-1's rows against the contents' count and columns."""
    head = ev.head
    out: dict[str, Any] = {"position": head.at(chain)}
    rows = _rows_a_head(cat, cls, head.as_dict())
    held = ev.held(head)
    out["heads"] = len(rows)
    out["heads_at_rows"] = {**_ms(_timed(functools.partial(_rows_a_head, cat, cls,
                                                           head.as_dict()), repeat))}
    out["count"] = _ms(_timed(held.count, repeat))
    out["count_value"] = held.count()
    out["three_columns"] = _ms(_timed(functools.partial(held.columns, *THREE), repeat))
    out["listing_columns"] = _ms(_timed(functools.partial(held.columns, *LISTING), repeat))
    cols = held.columns(*THREE)
    keys, digests = cols["path_key"], cols["digest"]
    assert isinstance(digests, Text) and not isinstance(keys, Text)
    versions = [r for r in rows if not r.hole]
    out["columns_equal_rows"] = (
        _pairs(cols) == _seqs(rows)
        and [bytes(k.tobytes()) for k in keys] == [bytes(r.path_key or b"") for r in versions]
        and [digests[i] for i in range(len(cols))] == [r.digest for r in versions])
    n = max(1, out["heads"])
    for name in ("heads_at_rows", "count", "three_columns", "listing_columns"):
        out[name]["us_a_head"] = out[name]["median_ms"] * 1e3 / n
        out[name]["under_the_bar"] = out[name]["median_ms"] / 1e3 <= BAR_S
    return out


def write_history(cat: VaultCatalog, cls: str, n: int, batch: int,
                  rng: random.Random) -> dict[str, int]:
    """`n` writes after the genesis, each appending one row: a new version of a held path for
    half, a retire of another held path for a quarter, a new path for the rest, shuffled."""
    held = [str(r[0]) for r in cat._conn.execute(
        "SELECT source_path FROM vault_files WHERE provenance = ? AND active = 1 "
        "ORDER BY source_path", [cls])]
    n_new_version, n_retire = n // 2, n // 4
    n_new_path = n - n_new_version - n_retire
    chosen = rng.sample(held, n_new_version + n_retire)
    titles = {str(p): str(t) for p, t in cat._conn.execute(
        "SELECT source_path, title FROM vault_files WHERE provenance = ?", [cls])}
    work: list[tuple[str, str]] = (
        [("version", p) for p in chosen[:n_new_version]]
        + [("retire", p) for p in chosen[n_new_version:]]
        + [("new", f"bench/history/{i:07}.md") for i in range(n_new_path)])
    rng.shuffle(work)
    provenance = Provenance(cls)
    for start in range(0, len(work), batch):
        with cat.deferred():
            for i, (what, path) in enumerate(work[start:start + batch], start):
                digest = hashlib.sha256(f"history {i} {path}".encode()).hexdigest()
                if what == "retire":
                    cat.tombstone(path)
                else:
                    cat.record(path, digest, titles.get(path, f"history {i}"),
                               provenance=provenance)
    return {"new_versions": n_new_version, "retires": n_retire, "new_paths": n_new_path}


def deltas(cat: VaultCatalog, ev: Evaluation, chain: int, cls: str, spans: list[int],
           repeat: int) -> list[dict[str, Any]]:
    """The signed difference ending at the head, over each span, against two reads of every head
    and a set difference."""
    head = ev.head.at(chain)
    out = []
    for span in spans:
        a, b = Cut.of({chain: max(0, head - span)}), ev.head
        d = ev.delta(a, b)
        entry: dict[str, Any] = {"from": a.at(chain), "to": head,
                                 "events_between": ev.between(a, b).count()}
        counts = d.counts()
        entry["removed"], entry["added"], entry["replaced"] = (counts.removed, counts.added,
                                                               counts.replaced)
        entry["holes"] = counts.holes
        entry["counts"] = _ms(_timed(d.counts, repeat))
        entry["sizes"] = _ms(_timed(d.sizes, repeat))
        entry["come_columns"] = _ms(_timed(functools.partial(d.come.columns, *THREE), repeat))
        entry["gone_columns"] = _ms(_timed(functools.partial(d.gone.columns, *THREE), repeat))
        entry["sorted"] = _ms(_timed(functools.partial(d.sorted, *THREE), repeat))

        def baseline(a: Cut = a, b: Cut = b) -> tuple[set[tuple[int, int]],
                                                      set[tuple[int, int]]]:
            ra, rb = _seqs(_rows_a_head(cat, cls, a.as_dict())), _seqs(
                _rows_a_head(cat, cls, b.as_dict()))
            return ra - rb, rb - ra

        entry["two_heads_at_and_a_set_difference"] = _ms(_timed(baseline, repeat))
        gone, come = baseline()
        entry["equal_to_the_baseline"] = (_pairs(d.gone.columns()) == gone
                                          and _pairs(d.come.columns()) == come)
        out.append(entry)
    return out


def family(ev: Evaluation, chain: int, start: int, repeat: int) -> dict[str, Any]:
    """Ten cuts spread evenly from `start` to the head."""
    head = ev.head.at(chain)
    fam = [Cut.of({chain: start + (head - start) * i // 9}) for i in range(10)]
    out: dict[str, Any] = {"positions": [c.at(chain) for c in fam]}
    walked = ev.count_series(fam)
    out["counts"] = list(walked.values)
    out["walked"] = _ms(_timed(functools.partial(ev.count_series, fam), repeat))
    out["ten_counts"] = _ms(_timed(lambda: [ev.held(c).count() for c in fam], repeat))
    out["walked_equals_counted"] = list(walked.values) == [ev.held(c).count() for c in fam]
    persisted, existed = ev.persisted(fam), ev.existed(fam)
    out["persisted"] = {**_ms(_timed(persisted.count, repeat)), "count": persisted.count()}
    out["existed"] = {**_ms(_timed(existed.count, repeat)), "count": existed.count()}
    table = ev.pairwise(fam)
    out["pairwise"] = {**_ms(_timed(functools.partial(ev.pairwise, fam), repeat)),
                       "sizes": [list(row) for row in table.sizes]}
    out["pairwise_equal_to_the_differences"] = all(
        table.sizes[i][j] == ev.delta(fam[i], fam[j]).sizes()[0]
        for i in range(10) for j in range(10))
    span = [fam[0], ev.head]
    kept = ev.persisted(span)
    out["persisted_horizon_to_head"] = {**_ms(_timed(kept.count, repeat)),
                                        "count": kept.count()}
    return out


def measure(db: Path, history: int, repeat: int, batch: int, seed: int) -> dict[str, Any]:
    from core.kernel.config import get_config

    if db.resolve() == Path(get_config().paths.vault_catalog).resolve():
        raise SystemExit("refusing the configured instance's own catalog: give a copy")
    rng = random.Random(seed)
    out: dict[str, Any] = {"catalog_copy": db.name, "load_start": os.getloadavg(),
                           "python": platform.python_version(),
                           "sqlite": sqlite3.sqlite_version, "numpy": np.__version__,
                           "machine": platform.machine(), "history": history,
                           "repeat": repeat, "batch": batch, "seed": seed}
    t0 = time.perf_counter()
    cat = VaultCatalog(db, key=os.urandom(32))
    out["migration_s"] = time.perf_counter() - t0
    chains = {int(c): str(k) for c, k in cat._conn.execute(
        "SELECT chain, class FROM landing_chains ORDER BY chain")}
    big = max(chains, key=cat.head)
    cls = chains[big]
    out["chain"], out["class"] = big, cls
    try:
        ev = cat.cuts([cls])
        horizon = ev.head.at(big)
        out["genesis"] = every_head(cat, ev, big, cls, repeat)
        out["load_before_history"] = os.getloadavg()
        t0 = time.perf_counter()
        out["history_written"] = write_history(cat, cls, history, batch, rng)
        out["history_s"] = time.perf_counter() - t0
        _checkpoint(cat._conn)
        ev = cat.cuts([cls])
        out["after_history"] = every_head(cat, ev, big, cls, repeat)
        head = ev.head.at(big)
        spans = [1, 1_000, 100_000, head - horizon, head]
        out["deltas"] = deltas(cat, ev, big, cls, spans, repeat)
        out["family"] = family(ev, big, horizon, repeat)
        mid = Cut.of({big: head - 1_000})
        out["plans"] = {
            "held": _plan(cat._conn, ev.held().count),
            "come": _plan(cat._conn, ev.delta(mid).come.count),
            "gone": _plan(cat._conn, ev.delta(mid).gone.count),
        }
        out["load_end"] = os.getloadavg()
    finally:
        cat.close()
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--catalog", type=Path, required=True,
                    help="a copy of a catalog file, migrated and written in place")
    ap.add_argument("--history", type=int, default=200_000)
    ap.add_argument("--repeat", type=int, default=5)
    ap.add_argument("--batch", type=int, default=10_000)
    ap.add_argument("--seed", type=int, default=13)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args(argv)
    out = measure(args.catalog, args.history, args.repeat, args.batch, args.seed)
    text = json.dumps(out, indent=2, default=str)
    if args.out:
        args.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
