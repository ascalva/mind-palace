#!/usr/bin/env python
"""The corpus instance's operator commands (dn-corpus-instance): isolation, fetch, ingest, status.

    MIND_PALACE_OVERLAY=config/instances/corpus.toml uv run python scripts/corpus.py isolation
    MIND_PALACE_OVERLAY=config/instances/corpus.toml uv run python scripts/corpus.py fetch wikipedia
    MIND_PALACE_OVERLAY=config/instances/corpus.toml uv run python scripts/corpus.py ingest
    MIND_PALACE_OVERLAY=config/instances/corpus.toml uv run python scripts/corpus.py status

Every command refuses unless the configuration loaded is a named instance with corpus sources, so
none of them can act on the default instance. `isolation` proves, with the loader's own checks
(DI-2, `shared` over `namespaces_of`, locations compared by real path), that the instance shares no
namespace with the default instance of this checkout, with every other instance declared beside it,
and with the live default instance of any checkout named by `--live` (its configuration read, never
written), and writes the proof under the instance's root. `fetch` runs one source's edge reader.
`ingest` is the instance's one writer: it takes the instance's supervisor lock, then lands each
source a batch at a time through `ingress/sync_corpus.palace` (the ingress, role `corpus`),
embedding under the yield policy (`ops/corpus/embedder.py`), until every stream is drained or a
stop condition holds (a stop file, a signal, the disk floor, an embedder error naming Metal or
memory); a run stopped anywhere resumes at the streams' cursors. `status` prints the progress
file.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root on path

from core.kernel.config.loader import (  # noqa: E402
    Config,
    InstanceConfig,
    Namespaces,
    load_config,
    namespaces_of,
    shared,
)

FREE_FLOOR_GB = 25.0          # stop when the disk's free space falls below this
PROGRESS = "progress.json"


def corpus_config() -> Config:
    cfg = load_config()
    if not cfg.instance.named or not cfg.ingestion.corpus.enabled \
            or not cfg.ingestion.corpus.sources:
        raise SystemExit("refusing: the loaded configuration is not a named instance with corpus "
                         "sources (set MIND_PALACE_OVERLAY=config/instances/corpus.toml)")
    return cfg


def live_namespaces(checkout: Path) -> Namespaces:
    """The default instance's namespaces as the checkout `checkout` loads them: the committed
    defaults, then that checkout's own `config/levers.toml` and `config/ouroboros.toml`, every
    relative path against that checkout. Read only: the two overlays are read, nothing is opened
    for writing, and this process's own root is restored before returning."""
    import core.kernel.config.loader as loader

    raw = loader._read(loader._DEFAULTS)
    loader._overlay(raw, checkout / "config" / "levers.toml")
    loader._overlay(raw, checkout / "config" / "ouroboros.toml")
    here = loader.REPO_ROOT
    loader.REPO_ROOT = checkout          # InstanceConfig.root and _resolve read it at call time
    try:
        return namespaces_of(loader._build(raw, InstanceConfig()))
    finally:
        loader.REPO_ROOT = here


def _real(p: Path) -> str:
    return os.path.realpath(p)


def isolation(cfg: Config, live: list[Path]) -> dict[str, Any]:
    """The proof: the corpus instance's namespaces against each other instance's, by `shared`."""
    mine = namespaces_of(cfg)
    import core.kernel.config.loader as loader

    others: list[tuple[str, Namespaces]] = [
        (name, namespaces_of(other)) for name, other in
        loader._declared_instances(Path(os.environ[loader.OVERLAY_ENV]).resolve())]
    for checkout in live:
        others.append((f"the default instance of {checkout}", live_namespaces(checkout)))
    checks = []
    for name, theirs in others:
        both = shared(mine, theirs)
        checks.append({"against": name, "shared": both,
                       "their_data_dir": _real(theirs.data_dir),
                       "their_spool": _real(theirs.spool)})
    # The control: the same check over a written path that is a link into the first other
    # instance's data directory must find it shared, or the check has no power.
    import tempfile
    from dataclasses import replace as _replace

    control: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        link = Path(tmp) / "linked"
        link.symlink_to(others[-1][1].data_dir)
        control = shared(_replace(mine, paths=frozenset({*mine.paths, link})), others[-1][1])
    root = cfg.instance.root
    proof = {
        "at": datetime.now(UTC).isoformat(timespec="seconds"),
        "instance": cfg.instance.id,
        "root": str(root), "root_real": _real(root),
        "written_real": sorted(_real(p) for p in mine.paths),
        "read_real": sorted(_real(p) for p in mine.sources),
        "labels": sorted(mine.labels), "secrets": sorted(mine.secrets),
        "checks": checks,
        "control": {"against": others[-1][0], "linked_written_path_found_shared": control},
        "isolated": all(not c["shared"] for c in checks) and bool(control),
    }
    return proof


def cmd_isolation(a: argparse.Namespace) -> int:
    cfg = corpus_config()
    proof = isolation(cfg, [Path(p).resolve() for p in a.live])
    root = cfg.instance.root
    root.mkdir(parents=True, exist_ok=True)
    (root / "isolation.json").write_text(json.dumps(proof, indent=1))
    print(json.dumps(proof, indent=1))
    return 0 if proof["isolated"] else 1


def cmd_fetch(a: argparse.Namespace) -> int:
    cfg = corpus_config()
    if a.source not in cfg.ingestion.corpus.sources:
        raise SystemExit(f"no corpus source {a.source!r}; the instance declares "
                         f"{', '.join(cfg.ingestion.corpus.sources)}")
    out = cfg.ingestion.corpus.root / a.source
    out.mkdir(parents=True, exist_ok=True)
    argv = [sys.executable, "-m", f"edge.corpus.{a.source}", "--out", str(out), *a.rest]
    return subprocess.call(argv, cwd=Path(__file__).resolve().parent.parent)


# ── the writer ──────────────────────────────────────────────────────────────────────────────────


def free_gb(path: Path) -> float:
    return shutil.disk_usage(path).free / 1e9


class Stop(Exception):
    """A stop condition: the run ends between batches, every stream at its cursor."""


def batch_items(location: Path, target_chunks: int, cap: int) -> int:
    """The items of a source one request lands: about `target_chunks` chunks, read off the
    stream's mean item size (the chunker yields about 1,300 chunks a megabyte, measured), at most
    `cap` and at least one."""
    from core.ingest import stream

    parts = stream.manifest(location)
    items = sum(p.items for p in parts)
    mean = sum(p.bytes for p in parts) / items if items else 1500.0
    per_item = max(1.0, mean * 1.3e-3)
    return max(1, min(cap, int(target_chunks / per_item)))


def fetch_running(location: Path) -> bool:
    """Whether a source's edge reader is still running (its marker names a live process)."""
    mark = location / "FETCHING"
    if not mark.is_file():
        return False
    try:
        os.kill(int(mark.read_text().strip()), 0)
    except (ValueError, ProcessLookupError):
        return False
    except PermissionError:
        return True
    return True


def write_progress(root: Path, doc: dict[str, Any]) -> None:
    tmp = root / (PROGRESS + ".tmp")
    tmp.write_text(json.dumps(doc, indent=1))
    tmp.replace(root / PROGRESS)


def cmd_ingest(a: argparse.Namespace) -> int:
    from core.ingest import stream
    from core.ingest.ingress import build_stores, run_library
    from core.ingest.table import build_table
    from ops.corpus.embedder import EmbedderStopped, Gate, GatedEmbedder
    from ops.lifecycle.lock import SupervisorLock, SupervisorLockHeld

    cfg = corpus_config()
    proof = isolation(cfg, [Path(p).resolve() for p in a.live])
    if not proof["isolated"]:
        print(json.dumps(proof["checks"], indent=1), file=sys.stderr)
        raise SystemExit("refusing: the instance shares a namespace (see the checks above)")
    root = cfg.instance.root
    root.mkdir(parents=True, exist_ok=True)
    (root / "isolation.json").write_text(json.dumps(proof, indent=1))
    cfg.paths.data_dir.mkdir(parents=True, exist_ok=True)
    lock = SupervisorLock(cfg.paths.data_dir / "supervisor.lock")
    try:
        lock.acquire()
    except SupervisorLockHeld:
        raise SystemExit("refusing: another writer holds the corpus instance's supervisor "
                         "lock") from None
    stopping = {"why": ""}

    def on_signal(signum: int, _frame: Any) -> None:
        stopping["why"] = f"signal {signum}"
    signal.signal(signal.SIGTERM, on_signal)
    signal.signal(signal.SIGINT, on_signal)
    stop_file = root / "STOP"
    stores = build_stores(cfg)
    gate = Gate(chat_port=a.chat_port, embed_port=cfg.runtime.port_for("embedding") or 8081,
                log=root / "gate.log")
    stores.embedder = GatedEmbedder(stores.embedder, gate, streams=a.streams, batch=a.embed_batch)
    table = build_table(cfg)
    names = [n for n in (a.only or cfg.ingestion.corpus.sources)]
    started = time.time()
    progress: dict[str, Any] = {"started": datetime.now(UTC).isoformat(timespec="seconds"),
                                "pid": os.getpid(), "state": "running", "sources": {},
                                "batches": 0, "items": 0, "embedded": 0, "seconds": 0.0}
    prior = root / PROGRESS
    if prior.is_file():
        old = json.loads(prior.read_text())
        progress["history"] = old.get("history", []) + [
            {k: old.get(k) for k in ("started", "stopped", "state", "why", "batches", "items",
                                     "embedded", "seconds")}]
    try:
        while True:
            drained = True
            for name in names:
                src = table.sources[f"corpus/{name}"]
                done, last = stream.cursor(src.location), stream.last_seq(src.location)
                progress["sources"][name] = {"cursor": done, "last": last}
                if done >= last:
                    continue
                drained = False
                if stopping["why"] or stop_file.exists():
                    raise Stop(stopping["why"] or "the stop file")
                if free_gb(root) < FREE_FLOOR_GB:
                    raise Stop(f"free disk {free_gb(root):.1f} GB is under the "
                               f"{FREE_FLOOR_GB:.0f} GB floor")
                t0 = time.time()
                before = stores.embedder.embedded
                embed_before = stores.embedder.seconds
                size = batch_items(src.location, a.target_chunks, a.batch)
                receipt = run_library(cfg, "sync_corpus", {"name": name, "batch": size},
                                      role="corpus", stores=stores, refresh=False, batch=True)
                dt = time.time() - t0
                landed = int(receipt["effects"].get("landed", 0))
                progress["batches"] += 1
                progress["items"] += sum(int(v) for v in receipt["effects"].values())
                progress["embedded"] += stores.embedder.embedded - before
                progress["seconds"] = round(time.time() - started, 1)
                timing = dict(receipt.get("timing", {}))
                timing["embed"] = round(stores.embedder.seconds - embed_before, 3)
                for k, v in timing.items():
                    progress.setdefault("timing", {})[k] = round(
                        progress.get("timing", {}).get(k, 0.0) + v, 1)
                progress["sources"][name] = {"cursor": stream.cursor(src.location),
                                             "last": last, "batch_items": size,
                                             "effects": receipt["effects"],
                                             "batch_s": round(dt, 1), "timing": timing}
                progress["gate"] = gate.summary()
                progress["free_gb"] = round(free_gb(root), 1)
                progress["updated"] = datetime.now(UTC).isoformat(timespec="seconds")
                write_progress(root, progress)
                print(f"{name}: +{landed} landed in {dt:.0f} s "
                      f"({stores.embedder.embedded - before} embedded), cursor "
                      f"{progress['sources'][name]['cursor']}/{last} {timing}", flush=True)
                if progress["batches"] % a.compact_every == 0:
                    report = stores.plane.compact(older_than=timedelta(minutes=30))
                    print(f"compacted the vector table: {report}", flush=True)
            if drained:
                fetching = [n for n in names if fetch_running(table.sources[f"corpus/{n}"]
                                                              .location)]
                if not (a.follow and fetching):
                    progress["state"] = "drained"
                    break
                if stopping["why"] or stop_file.exists():
                    raise Stop(stopping["why"] or "the stop file")
                progress["waiting_for"] = fetching
                write_progress(root, progress)
                time.sleep(30)
    except Stop as s:
        progress["state"], progress["why"] = "stopped", str(s)
    except EmbedderStopped as e:
        progress["state"], progress["why"] = "stopped by the embedder", str(e)
    except Exception as e:      # noqa: BLE001 - recorded, then raised: the run resumes at cursors
        progress["state"], progress["why"] = "failed", f"{type(e).__name__}: {e}"
        raise
    finally:
        progress["stopped"] = datetime.now(UTC).isoformat(timespec="seconds")
        progress["seconds"] = round(time.time() - started, 1)
        progress["gate"] = gate.summary()
        write_progress(root, progress)
        gate.close()
        lock.release()
    print(f"ingest: {progress['state']} {progress.get('why', '')}")
    return 0 if progress["state"] in ("drained", "stopped") else 1


def cmd_status(a: argparse.Namespace) -> int:
    cfg = corpus_config()
    p = cfg.instance.root / PROGRESS
    print(p.read_text() if p.is_file() else "no progress yet")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("isolation", help="prove the instance shares no namespace")
    p.add_argument("--live", nargs="*", default=[],
                   help="checkouts whose default instance to check against (read only)")
    p.set_defaults(fn=cmd_isolation)
    p = sub.add_parser("fetch", help="run one source's edge reader")
    p.add_argument("source")
    p.add_argument("rest", nargs=argparse.REMAINDER)
    p.set_defaults(fn=cmd_fetch)
    p = sub.add_parser("ingest", help="the instance's one writer")
    p.add_argument("--live", nargs="*", default=[])
    p.add_argument("--only", nargs="*", default=None, help="these sources, in this order")
    p.add_argument("--batch", type=int, default=2000, help="at most this many items a request")
    p.add_argument("--target-chunks", type=int, default=3000,
                   help="about this many chunks a request")
    p.add_argument("--follow", action="store_true",
                   help="wait for the edge readers still fetching before ending")
    p.add_argument("--streams", type=int, default=1, help="embedder requests in flight")
    p.add_argument("--embed-batch", type=int, default=64, help="texts an embedder request")
    p.add_argument("--chat-port", type=int, default=8080)
    p.add_argument("--compact-every", type=int, default=25, help="batches between compactions")
    p.set_defaults(fn=cmd_ingest)
    p = sub.add_parser("status", help="print the progress file")
    p.set_defaults(fn=cmd_status)
    a = ap.parse_args()
    return int(a.fn(a))


if __name__ == "__main__":
    raise SystemExit(main())
