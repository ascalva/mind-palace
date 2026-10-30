#!/usr/bin/env python
"""Embed local, already-fetched documents into the curated-literature store.

    uv run python scripts/curate_local.py <manifest.json> [--dry-run]

The core-side half of bringing outside literature in by hand (dn-external-grounding §2.2). The
fetch happened elsewhere — a person, or a Zone-C fetcher, put the files under `data/` and wrote
the manifest (a list of {source, id, title, tag, path, url, licence, ...}); this process seals
itself (Invariant 1), reads those text files, and writes `provenance="curated"` rows into the
SEPARATE curated store (`open_curated_store`) — never the mirror — in the row shape of
`core.research.persist.persist_keepers`. Every chunk's title carries the manifest's tag (e.g.
`[unreviewed · OpenAI 2026-10-25] …`), so every search hit says what kind of claim it is.
Idempotent: a document whose text digest is already in the store is skipped. A real run keeps a
ledger record with progress (`core.stores.tasks.job_record`), so the Ambassador's status tool and
the heartbeat can say how far it got.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from core.kernel.clearance import CURATED_READ

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))  # repo root on path
os.chdir(ROOT)  # config and data paths resolve against the repo root

from core.sealing import seal  # noqa: E402

BATCH = 64   # chunks per embedding request


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("manifest", type=Path)
    ap.add_argument("--dry-run", action="store_true", help="count chunks; embed and write nothing")
    args = ap.parse_args(argv)
    seal()  # structural egress guard first (Invariant 1): this reads local files only

    from core.ingest.embed import build_embedder
    from core.kernel.config import get_config
    from core.stores.curated_store import open_curated_store

    cfg = get_config()
    data = (ROOT / "data").resolve()
    docs = json.loads(args.manifest.read_text(encoding="utf-8"))
    store = open_curated_store(cfg)
    have = store.digests(clearance=CURATED_READ)
    if args.dry_run:
        return _embed(args, docs, store, have, data, None, None)
    from core.stores.tasks import job_record

    title = f"curated import: {args.manifest.parent.name}/{args.manifest.name}"
    with job_record(title) as progress:
        return _embed(args, docs, store, have, data, build_embedder(cfg), progress)


def _embed(args: argparse.Namespace, docs: list[dict[str, Any]], store: Any, have: set[str],
           data: Path, embedder: Any, progress: Callable[[str], None] | None) -> int:
    from core.kernel.ingest.chunk import chunk_text
    from core.kernel.provenance import Provenance

    added = skipped = n_chunks = 0
    t0 = time.monotonic()
    for i, d in enumerate(docs, 1):
        if progress is not None:
            progress(f"{i - 1}/{len(docs)} documents · {n_chunks} chunks")
        path = Path(str(d["path"])).resolve()
        if not path.is_relative_to(data):
            raise SystemExit(f"refusing {path}: curated sources must live under {data}")
        text = path.read_text(encoding="utf-8", errors="replace")
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if digest in have:
            skipped += 1
            continue
        chunks = chunk_text(text)
        n_chunks += len(chunks)
        if embedder is None or not chunks:
            continue
        source_path = f"reference:{d['source']}:{d['id']}"   # a curated marker, never a note path
        title = f"[{d['tag']}] {d['title']}"
        vectors: list[list[float]] = []
        for j in range(0, len(chunks), BATCH):
            vectors += embedder.embed_documents([c.text for c in chunks[j:j + BATCH]])
        store.add([
            {
                "id": f"{source_path}:{c.content_hash}",
                "digest": digest,
                "title": title,
                "source_path": source_path,
                "chunk_index": c.index,
                "provenance": Provenance.CURATED.value,
                "text": c.text,
                "vector": vec,
            }
            for c, vec in zip(chunks, vectors, strict=True)
        ])
        have.add(digest)
        added += 1
        if added % 25 == 0:
            rate = n_chunks / max(time.monotonic() - t0, 1e-9)
            print(f"{i}/{len(docs)} documents · {n_chunks} chunks · {rate:.1f} chunks/s",
                  flush=True)
    if progress is not None:
        progress(f"{len(docs)}/{len(docs)} documents · {n_chunks} chunks")
    verb = "would embed" if args.dry_run else "embedded"
    print(f"{verb} {len(docs) - skipped} document(s) as {n_chunks} chunk(s); {skipped} already "
          f"stored; curated store now {store.count()} rows ({time.monotonic() - t0:.0f} s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
