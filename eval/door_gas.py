"""The door's gas prices, measured (dn-door-language §E10): what each priced operation costs on
fixtures, in units of one evaluation step, so `PRICES` in `core/sentence/interpret.py` is a
measurement and not an assumption.

    uv run python eval/door_gas.py [--notes 200] [--repeat 7]
        [--embed-url http://127.0.0.1:8081 --embed-model embeddinggemma-2]

Hermetic by default: a palace under a temporary directory (its vault, its catalog, its stores),
nothing else opened. With `--embed-url` it also times an embedder on the fixtures' chunks, the one
price nothing in the process can give: a loopback server's OpenAI-compatible `/v1/embeddings`, one
request a note as the landing sends them (`core/ingest/index.py`). It embeds text and stores
nothing.

Each figure is the median of `--repeat` runs on a warm page cache, and each is the evaluator's own
work: what a run costs past its steps, divided by what it read.

- step: a loop over literal lists, its body one `let`; seconds per charged step, the unit.
- item and kib: `files(source("vault"))` over small notes and over large ones, less their steps;
  the per-note time is `item + kib · KiB`, solved from the two.
- entry: `stored(…)` over a catalog of entries, less its steps, per entry.
- effect: a `store` per note against a `let` per note, the difference per note, plus the writer's
  checks of one store found unchanged, twice (the price pass and the landing), timed on
  temporary stores holding the notes already.
- write: the writer's work for one store that lands, its embeds apart (the raw object, the
  plane's rows, the catalog, the attestation), less its checks: the first landing of the notes
  into temporary stores, with an embedder that returns at once, against the second.
- embed (with `--embed-url`): the embedder over the large notes' chunks, per chunk.
- query: not timed. A nested sentence's cost is the read half's, which the read verbs' own bounds
  limit (`docs/query/precedents.md`); pricing the read verbs in this unit is §E10's follow-up.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import tempfile
import time
import urllib.parse
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from core.attestation.attestor import StoreAttestor
from core.attestation.store import AttestationStore
from core.ingest.readers import PalaceView
from core.ingest.table import build_table
from core.ingest.writer import Stores, Writer
from core.kernel.config import get_config
from core.kernel.ingest.pipeline import derive_chunks
from core.kernel.provenance import Provenance
from core.kernel.stores.rawstore import RawStore
from core.sentence.interpret import PRICES, Evaluator, Meter
from core.sentence.script import parse_script
from core.stores.catalog import VaultCatalog
from core.stores.vectorstore import VectorStore
from core.stores.versions import VersionStore

SMALL = 120                    # bytes of a small note
LARGE = 32 * 1024              # bytes of a large note


@dataclass(frozen=True)
class Measured:
    seconds: float             # per operation
    units: int                 # in steps, rounded, at least one

    def row(self, name: str) -> str:
        return f"| `{name}` | {self.units} | {self.seconds * 1e6:.2f} µs | {PRICES[name]} |"


def _config(root: Path) -> Any:
    vault, data = root / "vault", root / "data"
    vault.mkdir(parents=True, exist_ok=True)
    data.mkdir(exist_ok=True)
    base = get_config()
    return replace(base,
                   ingestion=replace(base.ingestion, vault=replace(base.ingestion.vault,
                                                                   path=vault)),
                   paths=replace(base.paths, data_dir=data),
                   interface=replace(base.interface, handoff_dir=data / "handoff"))


def _notes(vault: Path, n: int, size: int) -> None:
    for i in range(n):
        body = f"# note {i}\n\n" + "".join(f"line {i}.{j} of a note, a sentence long.\n"
                                           for j in range(size // 40))
        (vault / f"n{i:05}.md").write_text(body[:size], encoding="utf-8")


def _timed(view: PalaceView, text: str, repeat: int) -> tuple[float, Meter]:
    script = parse_script(text)
    times: list[float] = []
    meter = Meter(10**15)
    for _ in range(repeat):
        meter = Meter(10**15)
        t0 = time.perf_counter()
        Evaluator(view, "cli", meter).run(script)
        times.append(time.perf_counter() - t0)
    return statistics.median(times), meter


def _steps(meter: Meter) -> int:
    return meter.by.get("step", 0) // PRICES["step"]


class _Instant:
    """An embedder that returns at once: the landing's own work, its embeds apart."""

    DIM = 8

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[float(b) / 255 for b in hashlib.sha256(t.encode()).digest()[:self.DIM]]
                for t in texts]


def _landing(cfg: Any, root: Path, notes: int) -> tuple[float, float]:
    """Seconds per store: the writer's checks of one found unchanged, the price pass's and the
    landing's, and the writes of one that lands, its embeds apart. A plan of one store per note,
    landed into temporary stores, then priced and landed again."""
    stores = Stores(raw=RawStore(root / "raw"), plane=VectorStore(root / "vectors",
                                                                  dim=_Instant.DIM),
                    embedder=_Instant(), catalog=VaultCatalog(root / "landing.sqlite"),
                    versions=VersionStore(root / "versions.sqlite"),
                    attestor=StoreAttestor(AttestationStore(root / "att.sqlite")))
    table = build_table(cfg)
    view = PalaceView(table, "cli", stores.catalog, refresh=False)
    plan = Evaluator(view, "cli", Meter(10**15)).run(parse_script(
        'for n in files(source("vault")) { store n.content in "mirror_authored" }'))
    writer = Writer(table, "cli", stores, has=view.has)
    t0 = time.perf_counter()
    first = writer.land(plan)
    t1 = time.perf_counter()
    priced = Writer(table, "cli", stores, has=view.has, meter=Meter(10**15))
    priced.price(plan)
    t2 = time.perf_counter()
    again = writer.land(plan)
    t3 = time.perf_counter()
    assert all(o.status == "landed" for o in first)
    assert all(o.status == "unchanged" for o in again)
    checks = ((t2 - t1) + (t3 - t2)) / notes
    return checks, (t1 - t0) / notes - (t3 - t2) / notes


def _embed_time(url: str, model: str, vault: Path, notes: int) -> float:
    """Seconds per chunk on a loopback embedder, one request a note."""
    host = urllib.parse.urlparse(url).hostname
    if host not in ("127.0.0.1", "localhost", "::1"):
        raise SystemExit(f"--embed-url must be a loopback address, not {host!r}")
    batches = [[c.text for c in derive_chunks(p.read_bytes(), max_chars=1200, overlap_chars=150)]
               for p in sorted(vault.glob("*.md"))[:notes]]
    t0 = time.perf_counter()
    for texts in batches:
        req = urllib.request.Request(url.rstrip("/") + "/v1/embeddings", method="POST",
                                     data=json.dumps({"model": model, "input": texts}).encode(),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as r:
            if len(json.loads(r.read())["data"]) != len(texts):
                raise SystemExit("the embedder answered a different number of vectors")
    return (time.perf_counter() - t0) / sum(len(b) for b in batches)


def measure(notes: int, repeat: int, embed_url: str | None = None,
            embed_model: str = "") -> dict[str, Measured]:
    with tempfile.TemporaryDirectory(prefix="door-gas-") as tmp:
        root = Path(tmp)
        small, large = _config(root / "small"), _config(root / "large")
        _notes(Path(small.ingestion.vault.path), notes, SMALL)
        _notes(Path(large.ingestion.vault.path), notes, LARGE)
        cat = VaultCatalog(root / "small" / "catalog.sqlite")
        for i in range(notes):
            path = str(Path(small.ingestion.vault.path) / f"e{i:05}.md")
            cat.record(path, hashlib.sha256(path.encode()).hexdigest(), f"e{i}",
                       provenance=Provenance.AUTHORED_SOLO)

        def view(cfg: Any) -> PalaceView:
            return PalaceView(build_table(cfg), "cli", cat, refresh=False)

        xs = ", ".join(str(i) for i in range(200))
        loop = f"let xs = [{xs}]\nfor a in xs {{ for b in xs {{ let y = a }} }}"
        t, m = _timed(view(small), loop, repeat)
        step = t / _steps(m)

        def per(t: float, m: Meter, count: int) -> float:
            return (t - _steps(m) * step) / count

        read = 'for n in files(source("vault")) { let d = n.digest }'
        ts, ms = _timed(view(small), read, repeat)
        tl, ml = _timed(view(large), read, repeat)
        per_small, per_large = per(ts, ms, notes), per(tl, ml, notes)
        kib = (per_large - per_small) / ((LARGE - SMALL) / 1024)
        item = per_small - kib * SMALL / 1024

        te, me = _timed(view(small),
                        'for e in stored("mirror_authored", under: source("vault")) '
                        "{ let p = e.path }", repeat)
        entry = per(te, me, notes)

        tw, mw = _timed(view(small), 'for n in files(source("vault")) '
                                     '{ store n.content in "mirror_authored" }', repeat)
        tr, mr = _timed(view(small), 'for n in files(source("vault")) { let c = n.content }',
                        repeat)
        checks, write = _landing(small, root / "small", notes)
        effect = ((tw - tr) - (_steps(mw) - _steps(mr)) * step) / notes + checks

        out = {"step": step, "item": item, "kib": kib, "entry": entry, "effect": effect,
               "write": write}
        if embed_url:
            out["embed"] = _embed_time(embed_url, embed_model, Path(large.ingestion.vault.path),
                                       min(notes, 10))
    return {k: Measured(v, max(1, round(v / step))) for k, v in out.items()}


def main(argv: list[str] | None = None, *, report: Callable[[str], None] = print) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--notes", type=int, default=200)
    ap.add_argument("--repeat", type=int, default=7)
    ap.add_argument("--embed-url", default=None)
    ap.add_argument("--embed-model", default="")
    a = ap.parse_args(argv)
    got = measure(a.notes, a.repeat, a.embed_url, a.embed_model)
    report(f"one step: {got['step'].seconds * 1e6:.3f} µs ({a.notes} notes, median of "
           f"{a.repeat})")
    report("| operation | measured price | measured time | price in force |")
    report("|---|---|---|---|")
    for name in PRICES:
        if name in got:
            report(got[name].row(name))
        else:
            report(f"| `{name}` | not measured | | {PRICES[name]} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
