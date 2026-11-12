"""The stores under load: a fixed battery run against a copy-on-write clone of an instance's
stores, so a change to a hot path is measured before and after on the same data.

    uv run python -m eval.stress_battery --source DIR --scratch DIR --out FILE
        [--parts keyword,ledger,landing,single,pending,concurrent,stratum,cut,mask]
        [--queries FILE] [--tokenizer legacy|current] [--passes 3] [--fresh 3] [--paths 400]
        [--runs 3]

`--source` is an instance's data directory (`lexical.sqlite`, `attestations.sqlite`,
`vault_catalog.sqlite`, `versions.sqlite`, `vectors.lance/`, `raw/`). It is never opened for
writing: the battery clones the files it needs into `--scratch` with `cp -c` (on APFS a clone
takes no space until it is written) and opens the clones. First it prepares a source of its own:
clones of the stores, the lexical index and the ledger opened once by the code under test, so a
store from before a change is migrated there, once, timed with the load beside it. Every part
then clones the prepared files again, so each part of each code starts from files the cache has
not read, and a part that writes gets fresh clones a run. The battery is the places an earlier
scaling study of the stores (unpublished) found past budget, measured where it is safe to:

- `keyword`: `LexicalStore.search` over a set of title queries, with the class filter the palace
  passes and with none, and the palace's own call shape, a class and a list of `--paths` item
  paths (`scores` and `search`, as `core/sentence/universe.py` calls them); warm (one process, the
  first pass apart, then `--passes`, each pass's time and load kept) and in a fresh process a
  query (`--fresh` repetitions);
- `ledger`: the producers of single digests (`producers_of`, and `already_attested` and
  `attested_by` through `core/ingest/landing.py`) and of a batch of 2,050 (`producers_by_output`,
  `attested_batch`);
- `landing`: synthetic items through the palace's writer (`Writer.land`, batched and lazy, the
  corpus runner's call), in `--runs` fresh processes: three batches of 2,000 new items, then a
  batch landing the third batch's 2,000 paths again with other bytes, which replaces every unit
  that batch made current; items a second, the time of each stage and store call, and the
  lexical index's upkeep of its statistics (`LexicalStore._keep`) where the code has one;
  `single`: three items effect by effect (`batch=False`), the path of every lane but the corpus
  runner's;
- `pending`: `derive.pending`, the drain's pending set, which a lazy instance's sentences read;
- `concurrent`: a lexical index from before the change (the source's own, not the prepared one)
  opened by one process and, `--concurrent-delay` seconds later, by a second that asks one
  query, as a reader opens the index while the first open migrates it;
- not run, each named in the record with its reason: `stratum`, the whole-stratum load of a
  sentence admitting the dialogue stratum (tens of gigabytes on a whole corpus); `cut`, the test
  that a commit's cut holds a citation edge (an instance with no citation store has none to read);
  `mask`, the pending mask of a sentence's nodes (empty on an instance with nothing pending).

A synthetic item is a real item of the instance made new: its bytes with one first line naming the
run and the item, so its digest is new while its text, chunks and terms stay a real item's. Every
timing carries the load average read beside it; every process caps BLAS at four threads and ends
itself past `--max-rss-gb` of resident memory (a thread polls its peak). A query's text and an
item's content never reach the record: a query is named by its id, its count of distinct terms
and its postings, an answer by a digest of it (the answers themselves go to `<out>.answers.json`
beside the record, to compare two runs bit for bit).
"""

from __future__ import annotations

import os


def _cap_threads(value: str | None, cap: int = 4) -> str:
    """At most `cap` threads: a smaller count given stays, a larger one or none becomes `cap`."""
    try:
        n = int(value) if value is not None else cap
    except ValueError:
        n = cap
    return str(min(n, cap) if n >= 1 else cap)


for _var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
             "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_var] = _cap_threads(os.environ.get(_var))

import argparse  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import platform  # noqa: E402
import random  # noqa: E402
import resource  # noqa: E402
import shutil  # noqa: E402
import sqlite3  # noqa: E402
import statistics  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402
import threading  # noqa: E402
import time  # noqa: E402
from collections import defaultdict  # noqa: E402
from collections.abc import Callable, Sequence  # noqa: E402
from datetime import UTC, datetime  # noqa: E402
from functools import partial  # noqa: E402
from pathlib import Path  # noqa: E402
from typing import Any  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

PARTS = ("keyword", "ledger", "landing", "single", "pending", "concurrent", "stratum", "cut",
         "mask")
STORES = ("lexical.sqlite", "attestations.sqlite", "vault_catalog.sqlite", "versions.sqlite",
          "vectors.lance")
ITEMS = 2000                      # a batch, the corpus runner's (`[ingestion.corpus] batch`)
NEW_BATCHES = 3                   # batches of new items a landing process; then one that replaces
ABSENT = 50                       # digests the ledger never saw, added to the batch
CORPUS_OVERLAY = "config/instances/corpus.toml"
NOT_RUN = {
    "stratum": ("not run: a sentence admitting the dialogue stratum loads every row of it with "
                "its vector (`all_rows(DIALOGUE_READ)`, core/sentence/universe.py) and builds "
                "dense n by n matrices over the items; the corpus instance's stage-1 record "
                "(docs/experiments/corpus-stage1-2026-11-07.md) has 4.3 to 4.7 GB at 10,000 "
                "items, and the whole corpus would need tens of GB. It belongs to a bounded "
                "universe, not to this battery"),
    "cut": ("not run: the test that a commit's cut holds a citation edge reads every edge of the "
            "commit (`ReferenceEdgeStore.for_commit`, from core/sentence/universe.py); it needs "
            "a citation store, and an instance without one, as the corpus instance is, has no "
            "edge for it to read"),
    "mask": ("not run: the pending mask of a sentence's nodes (core/sentence/universe.py) "
             "builds the set of pending items again for each node; it is empty when nothing is "
             "pending, as on the corpus instance, where `derive.pending` finds 0 items"),
}


# ── conditions: load, memory, clones ───────────────────────────────────────────────────────────

def load() -> list[float]:
    return [round(x, 2) for x in os.getloadavg()]


def peak_rss_mb() -> float:
    """This process's peak resident set (ru_maxrss: bytes on macOS, kilobytes on Linux)."""
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return round(peak / 1e6 if sys.platform == "darwin" else peak / 1e3, 1)


def guard(max_rss_gb: float) -> None:
    """End the process (exit 75) once its peak resident set passes the cap."""
    cap = max_rss_gb * 1e3

    def watch() -> None:
        while True:
            if peak_rss_mb() > cap:
                sys.stderr.write(f"stress_battery: resident set past {max_rss_gb} GB; ending\n")
                sys.stderr.flush()
                os._exit(75)
            time.sleep(0.02)
    threading.Thread(target=watch, daemon=True).start()


def clone(src: Path, dst: Path) -> None:
    """A copy-on-write clone of a file or a directory (`cp -c` on APFS, a reflink elsewhere when
    the filesystem has one); the SQLite companions of a file come with it."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    flag = ["-c"] if sys.platform == "darwin" else ["--reflink=auto"]
    if src.is_dir():
        subprocess.run(["cp", *flag, "-R", str(src), str(dst)], check=True)
        return
    for suffix in ("", "-wal", "-shm"):
        s = Path(str(src) + suffix)
        if s.exists():
            subprocess.run(["cp", *flag, str(s), str(dst) + suffix], check=True)


def fresh_dir(path: Path) -> Path:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)
    return path


def size(path: Path) -> int:
    """A store's bytes: the file with its write-ahead log."""
    return sum(Path(str(path) + s).stat().st_size for s in ("", "-wal")
               if Path(str(path) + s).exists())


def prepare(a: argparse.Namespace, scratch: Path) -> tuple[Path, dict[str, Any]]:
    """The battery's own source: clones of the source's stores, the lexical index and the ledger
    opened once by the code under test and closed, so a store from before a change is migrated
    here, once, and timed (a code with nothing to migrate opens it at once). The raw objects are
    read in the source, never written."""
    from core.attestation import AttestationStore
    from core.stores.lexical import LexicalStore

    d = fresh_dir(scratch / "source")
    for name in STORES:
        if (a.source / name).exists():
            clone(a.source / name, d / name)
    out: dict[str, Any] = {}
    openers: dict[str, Callable[[Path], Any]] = {
        "lexical.sqlite": lambda p: LexicalStore(p, tokenizer=tokenizer(a.tokenizer)),
        "attestations.sqlite": AttestationStore}
    for name, opener in openers.items():
        path = d / name
        if not path.exists():
            continue
        before = size(path)
        t, ld, store = timed(partial(opener, path))
        # migrated: the statistics counted, or the ledger's output-hash table present
        migrated = bool(store._conn.execute(
            "SELECT 1 FROM meta WHERE key = 'statistics'" if name == "lexical.sqlite" else
            "SELECT 1 FROM sqlite_master WHERE name = 'output_hashes'").fetchone())
        store.close()
        out[name] = {"open_s": t, "load": ld, "load_end": load(), "bytes_before": before,
                     "bytes_after": size(path), "migrated": migrated}
        print(f"prepare {name}: open {t:.2f}s load {ld} migrated {migrated}", flush=True)
    return d, out


def digest(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()[:16]


def summary(times: Sequence[float]) -> dict[str, Any]:
    s = sorted(times)
    return {"n": len(s), "median_s": statistics.median(s), "min_s": s[0], "max_s": s[-1]}


def timed[T](fn: Callable[[], T]) -> tuple[float, list[float], T]:
    ld = load()
    t0 = time.perf_counter()
    value = fn()
    return time.perf_counter() - t0, ld, value


def repeat(fn: Callable[[], Any], passes: int) -> dict[str, Any]:
    """The first call apart (a fresh process's first, the file cache as it is), then `passes`
    warm calls; the answers must not change between calls. Each call's processor time is kept
    beside its wall time: a slow pass whose processor time is as long was slow on the processor,
    not waiting."""
    c0 = time.process_time()
    first, ld, value = timed(fn)
    cpu = [time.process_time() - c0]
    warm, loads, stable = [], [ld], True
    for _ in range(passes):
        c0 = time.process_time()
        dt, ld, again = timed(fn)
        cpu.append(time.process_time() - c0)
        warm.append(dt)
        loads.append(ld)
        stable &= again == value
    return {"first_s": first, "warm": summary(warm) if warm else None, "warm_s": warm,
            "cpu_s": cpu, "load": loads, "stable": stable, "answer": value}


def tokenizer(name: str) -> Any:
    from core.ingest.lexical import LEGACY, TOKENIZER

    return {"legacy": LEGACY, "current": TOKENIZER}[name]


def code_label() -> dict[str, Any]:
    """Which code ran: the checkout's commit when it is one, else the name given."""
    try:
        sha = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True,
                             text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        sha = ""
    return {"git": sha, "label": os.environ.get("STRESS_CODE_LABEL", "")}


def child(args: list[str], max_rss_gb: float) -> dict[str, Any]:
    """Run one measurement in a fresh process of this module; its last line is its record."""
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    proc = subprocess.run([sys.executable, "-m", "eval.stress_battery", "child", *args,
                           "--max-rss-gb", str(max_rss_gb)], cwd=ROOT, env=env,
                          capture_output=True, text=True)
    if proc.returncode != 0:
        return {"error": f"exit {proc.returncode}", "stderr": proc.stderr[-2000:]}
    return dict(json.loads(proc.stdout.strip().splitlines()[-1]))


# ── keyword search ─────────────────────────────────────────────────────────────────────────────

def pick_queries(store: Any, n: int, seed: int) -> list[dict[str, Any]]:
    """Titles of random units (seeded), distinct: the battery's queries when none are given."""
    conn = store._conn
    hi = int(conn.execute("SELECT max(unit_id) FROM units").fetchone()[0] or 0)
    rng = random.Random(seed)
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for _ in range(50 * n):
        if len(out) >= n or hi == 0:
            break
        row = conn.execute("SELECT title FROM units WHERE unit_id = ?",
                           [rng.randint(1, hi)]).fetchone()
        if row is not None and str(row[0]).strip() and str(row[0]) not in seen:
            seen.add(str(row[0]))
            out.append({"qid": f"R{len(out)}", "text": str(row[0])})
    return out


def keyword_shapes(store: Any, klass: Any, paths: list[str]) -> dict[str, Callable[[str], Any]]:
    def hits(found: Any) -> list[list[Any]]:
        return [[h.source_path, h.digest, h.chunk_index, h.provenance, h.score.hex()]
                for h in found]
    return {
        "free-class": lambda t: hits(store.search(t, k=10, classes=[klass])),
        "free-all": lambda t: hits(store.search(t, k=10)),
        "paths-scores": lambda t: sorted([p, s.hex()] for p, s in
                                         store.scores(t, classes=[klass], paths=paths).items()),
        "paths-search": lambda t: hits(store.search(t, k=10, classes=[klass], paths=paths)),
    }


def sample_paths(store: Any, n: int, seed: int) -> list[str]:
    paths = sorted(str(r[0]) for r in store._conn.execute(
        "SELECT DISTINCT source_path FROM versions"))
    return random.Random(seed).sample(paths, min(n, len(paths)))


def part_keyword(a: argparse.Namespace, scratch: Path, answers: dict[str, Any]) -> dict[str, Any]:
    from core.kernel.provenance import Provenance
    from core.stores.lexical import LexicalStore

    d = fresh_dir(scratch / "keyword")
    clone(a.stores / "lexical.sqlite", d / "lexical.sqlite")
    t_open, ld_open, store = timed(lambda: LexicalStore(d / "lexical.sqlite",
                                                        tokenizer=tokenizer(a.tokenizer)))
    klass = Provenance(a.klass)
    queries = (json.loads(a.queries.read_text()) if a.queries
               else pick_queries(store, a.draw, a.seed))
    tok = tokenizer(a.tokenizer)
    meta = {}
    for q in queries:
        terms = sorted(set(tok(q["text"])))
        postings = sum(int(store._conn.execute("SELECT count(*) FROM postings WHERE term = ?",
                                               [t]).fetchone()[0]) for t in terms)
        meta[str(q["qid"])] = {"terms": len(terms), "postings": postings}
    paths = sample_paths(store, a.paths, a.seed)
    shapes = keyword_shapes(store, klass, paths)
    path_qids = {str(x) for x in a.path_qids.split(",")} if a.path_qids else None
    fresh_qids = {str(x) for x in a.fresh_qids.split(",")} if a.fresh_qids else None
    out: dict[str, Any] = {"open_s": t_open, "open_load": ld_open, "queries": meta,
                           "class": a.klass, "tokenizer": tok.identity, "paths": len(paths),
                           "units_current": store.count(), "shapes": {}}
    for name, fn in shapes.items():
        wanted = [q for q in queries if not name.startswith("paths")
                  or path_qids is None or str(q["qid"]) in path_qids]
        rows = {}
        for q in wanted:
            r = repeat(partial(fn, q["text"]), a.passes)
            answers[f"keyword/{name}/{q['qid']}"] = r.pop("answer")
            r["answer"] = digest(answers[f"keyword/{name}/{q['qid']}"])
            rows[str(q["qid"])] = r
            print(f"keyword {name} {q['qid']} first {r['first_s']:.3f}s "
                  f"warm {r['warm']['median_s'] if r['warm'] else 0:.3f}s load {load()}",
                  flush=True)
        out["shapes"][name] = rows
    store.close()
    qfile = d / "queries.json"
    qfile.write_text(json.dumps(queries))
    pfile = d / "paths.json"
    pfile.write_text(json.dumps(paths))
    fresh: dict[str, Any] = {}
    for name in ("free-class", "paths-scores"):
        for q in queries:
            if fresh_qids is not None and str(q["qid"]) not in fresh_qids:
                continue
            if name.startswith("paths") and path_qids is not None \
                    and str(q["qid"]) not in path_qids:
                continue
            reps = [child(["keyword", "--store", str(d / "lexical.sqlite"), "--shape", name,
                           "--qfile", str(qfile), "--qid", str(q["qid"]), "--pfile", str(pfile),
                           "--class", a.klass, "--tokenizer", a.tokenizer], a.max_rss_gb)
                    for _ in range(a.fresh)]
            fresh[f"{name}/{q['qid']}"] = reps
            print(f"keyword fresh {name} {q['qid']} "
                  f"{[round(r.get('query_s', -1), 3) for r in reps]}", flush=True)
    out["fresh"] = fresh
    return out


def child_keyword(a: argparse.Namespace) -> dict[str, Any]:
    from core.kernel.provenance import Provenance
    from core.stores.lexical import LexicalStore

    queries = {str(q["qid"]): q for q in json.loads(Path(a.qfile).read_text())}
    paths = json.loads(Path(a.pfile).read_text())
    t_open, _, store = timed(lambda: LexicalStore(Path(a.store), tokenizer=tokenizer(a.tokenizer)))
    fn = keyword_shapes(store, Provenance(a.klass), paths)[a.shape]
    counted = bool(getattr(store, "_counted", lambda: False)())
    dt, ld, value = timed(lambda: fn(queries[a.qid]["text"]))
    return {"open_s": t_open, "query_s": dt, "load": ld, "load_end": load(),
            "counted_at_query": counted, "answer": digest(value), "peak_rss_mb": peak_rss_mb()}


# ── the attestation ledger ─────────────────────────────────────────────────────────────────────

def part_ledger(a: argparse.Namespace, scratch: Path, answers: dict[str, Any]) -> dict[str, Any]:
    from core.attestation import AttestationStore, StoreAttestor
    from core.ingest.landing import already_attested, attested_batch, attested_by

    d = fresh_dir(scratch / "ledger")
    clone(a.stores / "attestations.sqlite", d / "attestations.sqlite")
    raw = sqlite3.connect(f"file:{d / 'attestations.sqlite'}?mode=ro", uri=True)
    rowids = [int(r[0]) for r in raw.execute("SELECT rowid FROM attestations ORDER BY rowid")]
    action = str(raw.execute("SELECT action FROM attestations GROUP BY action "
                             "ORDER BY count(*) DESC, action LIMIT 1").fetchone()[0])
    rng = random.Random(a.seed)

    def first_output(rowid: int) -> str | None:
        row = raw.execute("SELECT payload_json FROM attestations WHERE rowid = ?",
                          [rowid]).fetchone()
        outs = json.loads(row[0]).get("output_hashes") or []
        return str(outs[0]) if outs else None
    singles = [h for h in (first_output(r) for r in rng.sample(rowids, min(5, len(rowids)))) if h]
    singles += ["0" * 64, "f" * 64]
    batch = {h for h in (first_output(r) for r in rng.sample(rowids, min(ITEMS, len(rowids))))
             if h}
    batch |= {f"{i:064x}" for i in range(1, ABSENT + 1)}
    records = len(rowids)
    raw.close()
    t_open, ld_open, store = timed(lambda: AttestationStore(d / "attestations.sqlite"))
    attestor = StoreAttestor(store)
    out: dict[str, Any] = {"open_s": t_open, "open_load": ld_open, "records": records,
                           "action": action, "singles": {}, "batch": {"digests": len(batch)}}
    calls: dict[str, Callable[[str], Any]] = {
        "producers_of": lambda h: sorted(store.producers_of({h})),
        "already_attested": lambda h: already_attested(attestor, action, h),
        "attested_by": lambda h: attested_by(attestor, action, h),
    }
    for name, fn in calls.items():
        rows = {}
        for i, h in enumerate(singles):
            r = repeat(partial(fn, h), a.passes)
            answers[f"ledger/{name}/{i}"] = r.pop("answer")
            r["answer"] = digest(answers[f"ledger/{name}/{i}"])
            r["present"] = i < len(singles) - 2
            rows[str(i)] = r
        out["singles"][name] = rows
        print(f"ledger {name} {[round(r['first_s'], 4) for r in rows.values()]}", flush=True)
    for name, bfn in (("producers_by_output", lambda: store.producers_by_output(set(batch))),
                      ("attested_batch", lambda: attested_batch(attestor, set(batch)))):
        r = repeat(bfn, a.passes)
        answers[f"ledger/{name}"] = sorted([k, v] for k, v in r.pop("answer").items())
        r["answer"] = digest(answers[f"ledger/{name}"])
        out["batch"][name] = r
        print(f"ledger {name} first {r['first_s']:.4f}s", flush=True)
    store.close()
    return out


# ── the landing ────────────────────────────────────────────────────────────────────────────────

STATS: dict[str, dict[str, float]] = defaultdict(lambda: {"calls": 0, "seconds": 0.0})


class Timed:
    """A store whose public methods are timed and counted; attributes pass through."""

    def __init__(self, obj: Any, name: str) -> None:
        object.__setattr__(self, "_o", obj)
        object.__setattr__(self, "_n", name)

    def __getattr__(self, k: str) -> Any:
        v = getattr(self._o, k)
        if not callable(v) or k.startswith("_") or k == "deferred":
            return v

        def call(*args: Any, **kw: Any) -> Any:
            t0 = time.perf_counter()
            try:
                return v(*args, **kw)
            finally:
                s = STATS[f"{self._n}.{k}"]
                s["calls"] += 1
                s["seconds"] += time.perf_counter() - t0
        return call


def synthetic_items(source: Path, raw: Path, seed: int,
                    n: int) -> list[tuple[str, str, str, bytes]]:
    """`n` real items made new: (source name, new path, title, bytes with a first line naming the
    run and the item), drawn from the catalog in `source`, their bytes read from `raw`."""
    con = sqlite3.connect(f"file:{source / 'vault_catalog.sqlite'}?mode=ro&immutable=1", uri=True)
    rows = con.execute("SELECT source_path, digest, title FROM vault_files "
                       "WHERE active = 1 ORDER BY source_path").fetchall()
    con.close()
    out = []
    for i, (path, dg, title) in enumerate(random.Random(1000 + seed).sample(rows, n)):
        name = str(path).split("/")[1] if "/" in str(path) else "items"
        data = (raw / str(dg)[:2] / str(dg)).read_bytes()
        out.append((name, f"corpus/{name}/stress-s{seed}-{i}", str(title),
                    f"[stress s{seed} i{i}]\n".encode() + data))
    return out


UPKEEP: dict[str, float] = {"calls": 0, "units": 0, "seconds": 0.0}


def time_upkeep(store_class: Any) -> bool:
    """Time the lexical index's upkeep of its statistics (`LexicalStore._keep`) where the code has
    one: the calls that moved them, the units whose currency they moved, and the seconds of every
    call. False for a code without one."""
    keep = getattr(store_class, "_keep", None)
    if keep is None:
        return False

    def timed_keep(self: Any, changes: dict[int, int]) -> None:
        t0 = time.perf_counter()
        try:
            keep(self, changes)
        finally:
            UPKEEP["seconds"] += time.perf_counter() - t0
            if changes:
                UPKEEP["calls"] += 1
                UPKEEP["units"] += len(changes)
    store_class._keep = timed_keep
    return True


def child_landing(a: argparse.Namespace) -> dict[str, Any]:
    """In a fresh process: fresh clones of the stores, then `--batches` plans of `--items` new
    items landed through the writer, batched and lazy (or effect by effect with `--single`), and
    with `--replace` one more plan landing the last plan's paths again with other bytes."""
    os.environ.setdefault("MIND_PALACE_OVERLAY", CORPUS_OVERLAY)
    os.chdir(ROOT)
    from core.attestation import AttestationStore, StoreAttestor
    from core.ingest.ingress import grant_for
    from core.ingest.table import build_table
    from core.ingest.writer import Stores, Writer
    from core.kernel.clearance import classes_of
    from core.kernel.config import load_config
    from core.kernel.stores.rawstore import RawStore
    from core.sentence.interpret import OBSERVED, Content, Meter, Naming, Origin, StoreEff
    from core.stores.catalog import VaultCatalog
    from core.stores.lexical import LexicalStore
    from core.stores.vectorstore import VectorStore, fingerprint_of
    from core.stores.versions import VersionStore

    source = Path(a.source)
    raw = Path(a.raw) if a.raw else source / "raw"
    d = fresh_dir(Path(a.dir))
    t0 = time.perf_counter()
    for name in ("lexical.sqlite", "vault_catalog.sqlite", "attestations.sqlite",
                 "versions.sqlite"):
        clone(source / name, d / name)
    clone(source / "vectors.lance", d / "vectors.lance")
    upkeep = time_upkeep(LexicalStore)
    res: dict[str, Any] = {"clone_s": time.perf_counter() - t0, "load_start": load(),
                           "single": a.single, "upkeep_timed": upkeep, "batches": []}
    cfg = load_config()
    table = build_table(cfg)
    opens = {}
    t, _, lex = timed(lambda: LexicalStore(d / "lexical.sqlite", tokenizer=tokenizer(a.tokenizer)))
    opens["lexical"] = t
    t, _, cat = timed(lambda: VaultCatalog(d / "vault_catalog.sqlite"))
    opens["catalog"] = t
    t, _, led = timed(lambda: AttestationStore(d / "attestations.sqlite"))
    opens["attestations"] = t
    t, _, ver = timed(lambda: VersionStore(d / "versions.sqlite"))
    opens["versions"] = t
    res["open_s"] = opens
    vs = VectorStore(path=d / "vectors.lance", dim=cfg.embedding.dim, embedder=fingerprint_of(cfg))
    ledger: Any = Timed(led, "attestations")
    stores = Stores(raw=Timed(RawStore(d / "raw"), "raw"), plane=Timed(vs, "plane"),
                    embedder=None, catalog=Timed(cat, "catalog"), versions=Timed(ver, "versions"),
                    attestor=StoreAttestor(ledger), edges=None,
                    enqueue=None, lexical=Timed(lex, "lexical"))
    role = "corpus"
    reads = frozenset().union(*(classes_of(s.sigma.strata) for s in grant_for(role).scopes))

    def units(paths: list[str]) -> tuple[int, int]:
        """The unit rows of these paths, and the current ones: by the paths' index, so the count
        reads only the batch's rows."""
        total = current = 0
        for i in range(0, len(paths), 400):
            batch = paths[i:i + 400]
            n, c = lex._conn.execute(
                "SELECT count(*), COALESCE(sum(current), 0) FROM units WHERE source_path IN "
                f"({', '.join('?' for _ in batch)})", batch).fetchone()
            total, current = total + int(n), current + int(c)
        return total, current
    last: list[tuple[str, str, str, bytes]] = []
    for bi in range(a.batches + (1 if a.replace else 0)):
        if bi < a.batches:
            kind, its = "new", synthetic_items(source, raw, a.run * 10 + bi, a.items)
        else:                       # the last batch's paths again, other bytes: each a new version
            kind, its = "replace", [(n, p, t_, b"[replaced]\n" + x) for n, p, t_, x in last]
        last = its
        plan = [StoreEff(path=path, content=Content(data, OBSERVED, Origin("item",
                         f"corpus/{name}", path, title)), place="observed",
                         naming=Naming("own"), title=title) for name, path, title, data in its]
        writer = Writer(table, role, stores, has=lambda _p: True,
                        meter=Meter(table.roles[role].budget), request=None, reads=reads,
                        batch=not a.single, lazy=True)
        paths = [p for _, p, _, _ in its]
        before, (rows0, current0) = led.count(), units(paths)
        STATS.clear()
        kept0 = dict(UPKEEP)
        ld = load()
        t0 = time.perf_counter()
        landed = writer.land(plan)
        dt = time.perf_counter() - t0
        statuses: dict[str, int] = defaultdict(int)
        for o in landed:
            statuses[o.status] += 1
        rows1, current1 = units(paths)
        res["batches"].append({
            "batch": bi, "kind": kind, "items": len(its), "bytes": sum(len(x) for *_, x in its),
            "land_s": dt, "items_per_s": len(its) / dt, "load": ld, "load_end": load(),
            "statuses": dict(statuses), "stages_s": dict(writer.timing),
            "calls": {k: dict(v) for k, v in sorted(STATS.items())},
            "upkeep": ({k: UPKEEP[k] - kept0[k] for k in UPKEEP} if upkeep else None),
            "ledger_grew": led.count() - before, "units_landed": rows1 - rows0,
            "units_current_delta": current1 - current0})
        print(json.dumps({"batch": bi, "kind": kind, "land_s": round(dt, 3),
                          "statuses": dict(statuses), "load": ld}), file=sys.stderr, flush=True)
    if hasattr(lex, "statistics"):
        # the kept class statistics against a count of the units, after the batches
        n, tokens = lex._conn.execute(
            "SELECT count(*), COALESCE(sum(length), 0) FROM units WHERE current = 1").fetchone()
        kept = lex.statistics()
        res["statistics"] = {"kept": [kept.units, kept.tokens], "counted": [int(n), int(tokens)],
                             "equal": (kept.units, kept.tokens) == (int(n), int(tokens))}
    res["peak_rss_mb"] = peak_rss_mb()
    res["load_end"] = load()
    shutil.rmtree(d, ignore_errors=True)
    return res


def part_landing(a: argparse.Namespace, scratch: Path, *, single: bool) -> dict[str, Any]:
    runs = []
    for r in range(1 if single else a.runs):
        args = ["landing", "--source", str(a.stores), "--raw", str(a.source / "raw"),
                "--dir", str(scratch / f"landing-{r}"), "--run", str(r),
                "--tokenizer", a.tokenizer, "--items", str(3 if single else ITEMS),
                "--batches", str(1 if single else NEW_BATCHES)]
        args.append("--single" if single else "--replace")
        rec = child(args, a.max_rss_gb)
        runs.append(rec)
        print(f"{'single' if single else 'landing'} run {r}: "
              f"{[round(b['land_s'], 2) for b in rec.get('batches', [])]} {rec.get('error', '')}",
              flush=True)
    return {"runs": runs}


# ── the drain's pending set ────────────────────────────────────────────────────────────────────

def part_pending(a: argparse.Namespace, scratch: Path) -> dict[str, Any]:
    from core.ingest.derive import pending
    from core.stores.catalog import VaultCatalog
    from core.stores.lexical import LexicalStore
    from core.stores.vectorstore import VectorStore

    d = fresh_dir(scratch / "pending")
    for name in ("lexical.sqlite", "vault_catalog.sqlite"):
        clone(a.stores / name, d / name)
    clone(a.stores / "vectors.lance", d / "vectors.lance")
    cat = VaultCatalog(d / "vault_catalog.sqlite")
    lex = LexicalStore(d / "lexical.sqlite", tokenizer=tokenizer(a.tokenizer))
    plane = VectorStore(path=d / "vectors.lance", dim=a.dim)
    r = repeat(lambda: len(pending(cat, plane, lexical=lex)), a.passes)
    r["pending"] = r.pop("answer")
    lex.close()
    return r


# ── a store opened while another process migrates it ──────────────────────────────────────────

def one_query(a: argparse.Namespace, path: Path) -> dict[str, Any]:
    """The concurrent part's query: the first of `--fresh-qids` among `--queries`, else a title of
    the store read without opening it as a store (an open would migrate it)."""
    if a.queries:
        queries = json.loads(a.queries.read_text())
        wanted = a.fresh_qids.split(",")[0] if a.fresh_qids else None
        return dict(next((q for q in queries if str(q["qid"]) == wanted), queries[0]))
    raw = sqlite3.connect(f"file:{path}?mode=ro&immutable=1", uri=True)
    row = raw.execute("SELECT title FROM units WHERE current = 1 AND title <> '' "
                      "ORDER BY unit_id LIMIT 1").fetchone()
    raw.close()
    return {"qid": "R0", "text": str(row[0]) if row else ""}


def child_open(a: argparse.Namespace) -> dict[str, Any]:
    """In a fresh process: open the lexical index (a migration, when it needs one), then close."""
    from core.stores.lexical import LexicalStore

    t, ld, store = timed(lambda: LexicalStore(Path(a.store), tokenizer=tokenizer(a.tokenizer)))
    counted = bool(getattr(store, "_counted", lambda: False)())
    store.close()
    return {"open_s": t, "load": ld, "load_end": load(), "migrated": counted,
            "peak_rss_mb": peak_rss_mb()}


def part_concurrent(a: argparse.Namespace, scratch: Path) -> dict[str, Any]:
    """A lexical index from before the change (the source's own) opened by a first process and,
    `--concurrent-delay` seconds later, by a second that asks one query with the class filter,
    as a reader opens the index while the first open migrates it."""
    d = fresh_dir(scratch / "concurrent")
    path = d / "lexical.sqlite"
    clone(a.source / "lexical.sqlite", path)
    q = one_query(a, path)
    qfile, pfile = d / "query.json", d / "paths.json"
    qfile.write_text(json.dumps([q]))
    pfile.write_text("[]")
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    ld = load()
    first = subprocess.Popen([sys.executable, "-m", "eval.stress_battery", "child", "open",
                              "--store", str(path), "--tokenizer", a.tokenizer,
                              "--max-rss-gb", str(a.max_rss_gb)], cwd=ROOT, env=env,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    time.sleep(a.concurrent_delay)
    second = child(["keyword", "--store", str(path), "--shape", "free-class", "--qfile",
                    str(qfile), "--qid", str(q["qid"]), "--pfile", str(pfile), "--class",
                    a.klass, "--tokenizer", a.tokenizer], a.max_rss_gb)
    out, err = first.communicate()
    opened = (dict(json.loads(out.strip().splitlines()[-1])) if first.returncode == 0
              else {"error": f"exit {first.returncode}", "stderr": err[-2000:]})
    print(f"concurrent: first {opened.get('open_s', opened.get('error'))} second "
          f"{second.get('open_s', second.get('error'))} {second.get('query_s', '')}", flush=True)
    return {"query": str(q["qid"]), "delay_s": a.concurrent_delay, "load": ld, "first": opened,
            "second": second, "load_end": load()}


# ── the battery ────────────────────────────────────────────────────────────────────────────────

def run(a: argparse.Namespace) -> dict[str, Any]:
    scratch = Path(a.scratch)
    scratch.mkdir(parents=True, exist_ok=True)
    rec: dict[str, Any] = {
        "battery": "stress", "started": datetime.now(UTC).isoformat(timespec="seconds"),
        "code": code_label(), "load_start": load(), "python": platform.python_version(),
        "sqlite": sqlite3.sqlite_version, "machine": platform.machine(),
        "cpus": os.cpu_count(), "args": {k: str(v) for k, v in vars(a).items()}, "parts": {}}
    answers: dict[str, Any] = {}
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    parts = a.parts.split(",")
    for part in parts:
        if part not in PARTS:
            raise SystemExit(f"no part {part!r}; one of {', '.join(PARTS)}")
    a.stores = a.source
    if {"keyword", "ledger", "landing", "single", "pending"} & set(parts):
        a.stores, rec["prepare"] = prepare(a, scratch)
        out.write_text(json.dumps(rec, indent=1))
    for part in parts:
        t0 = time.perf_counter()
        try:
            if part == "keyword":
                res = part_keyword(a, scratch, answers)
            elif part == "ledger":
                res = part_ledger(a, scratch, answers)
            elif part in ("landing", "single"):
                res = part_landing(a, scratch, single=part == "single")
            elif part == "pending":
                res = part_pending(a, scratch)
            elif part == "concurrent":
                res = part_concurrent(a, scratch)
            else:
                res = {"status": NOT_RUN[part]}
        except Exception as exc:  # noqa: BLE001 - a part that fails is a result, recorded
            res = {"error": f"{type(exc).__name__}: {exc}"}
        res["part_s"] = time.perf_counter() - t0
        rec["parts"][part] = res
        rec["peak_rss_mb"] = peak_rss_mb()
        out.write_text(json.dumps(rec, indent=1))
        Path(str(out) + ".answers.json").write_text(json.dumps(answers))
    rec["load_end"] = load()
    rec["finished"] = datetime.now(UTC).isoformat(timespec="seconds")
    out.write_text(json.dumps(rec, indent=1))
    return rec


def main(argv: list[str] | None = None) -> None:
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] == "child":
        ap = argparse.ArgumentParser(prog="stress_battery child")
        ap.add_argument("kind", choices=["keyword", "landing", "open"])
        ap.add_argument("--store")
        ap.add_argument("--shape")
        ap.add_argument("--qfile")
        ap.add_argument("--qid")
        ap.add_argument("--pfile")
        ap.add_argument("--class", dest="klass", default="observed")
        ap.add_argument("--tokenizer", default="current")
        ap.add_argument("--source")
        ap.add_argument("--raw")
        ap.add_argument("--dir")
        ap.add_argument("--run", type=int, default=0)
        ap.add_argument("--items", type=int, default=ITEMS)
        ap.add_argument("--batches", type=int, default=3)
        ap.add_argument("--single", action="store_true")
        ap.add_argument("--replace", action="store_true")
        ap.add_argument("--max-rss-gb", type=float, default=3.8)
        c = ap.parse_args(argv[1:])
        guard(c.max_rss_gb)
        res = {"keyword": child_keyword, "landing": child_landing, "open": child_open}[c.kind](c)
        print(json.dumps(res))
        return
    a = parse(argv)
    guard(a.max_rss_gb)
    run(a)


def parse(argv: list[str]) -> argparse.Namespace:
    """The battery's arguments."""
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", type=Path, required=True,
                    help="an instance's data directory; cloned, never written")
    ap.add_argument("--scratch", type=Path, required=True, help="where the clones go")
    ap.add_argument("--out", type=Path, required=True, help="the JSON record")
    ap.add_argument("--parts", default=",".join(PARTS))
    ap.add_argument("--queries", type=Path, help="a JSON list of {qid, text}; else drawn")
    ap.add_argument("--draw", type=int, default=16, help="titles drawn when no --queries")
    ap.add_argument("--path-qids", default="", help="the queries of the path shapes (all)")
    ap.add_argument("--fresh-qids", default="", help="the queries timed a fresh process each")
    ap.add_argument("--tokenizer", choices=["legacy", "current"], default="current")
    ap.add_argument("--class", dest="klass", default="observed")
    ap.add_argument("--passes", type=int, default=3)
    ap.add_argument("--fresh", type=int, default=3)
    ap.add_argument("--paths", type=int, default=400)
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--dim", type=int, default=768)
    ap.add_argument("--seed", type=int, default=20261111)
    ap.add_argument("--concurrent-delay", type=float, default=5.0,
                    help="seconds between the two opens of the concurrent part")
    ap.add_argument("--max-rss-gb", type=float, default=3.8)
    return ap.parse_args(argv)


if __name__ == "__main__":
    main()
