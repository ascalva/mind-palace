"""Store a vector store's vectors in float16 (dn-vector-membership-store Amendment A4).

    uv run python -m ops.float16_migrate [--store vectors|curated|all] [--dry-run]

Step C measured the change (docs/experiments/vector-quantization-2026-10-30.md): a float16 vector
column returns today's top ten for every query family (recall@10 1.000 in LanceDB) at half the
bytes on disk, and flat search runs faster. This converts a store's one LanceDB table to that
column, in A3's shape — nothing is deleted:

1. BUILD beside the live store (`<store>.f16-build/`): every row of the table, page by page, each
   column as it was and the vector in float16; then the plane's relations (`plane.sqlite`, which
   hold no vectors) copied whole through SQLite's online backup.
2. VERIFY that the build IS the old store, cast: every row reduced to a digest of its non-vector
   columns and its float16 vector bytes, and the two multisets of digests equal — so order,
   duplicates and every column are covered — and the plane database dumping identically. Any
   difference stops here, the live store untouched.
3. SWAP only if the old table's version is still the one read at the start (a writer that slipped
   in is a reason to stop, never to lose its row): the old directory is RENAMED into
   `~/mind-palace-archive/<store>-pre-f16-<UTC>` and the build renamed into its place.

Run it with writers stopped (`mind-palace stack down`): the long-running servers keep the old
store's handles open until they restart. A store already in float16 is left alone; a store not yet
on the shared plane must take `ops.plane_migrate` first.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sqlite3
from collections import Counter
from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path
from typing import Any

import numpy as np

from core.kernel.clearance import MAINTENANCE_READ
from core.stores.plane import PLANE_FILE, Fingerprint
from core.stores.vectorstore import VectorStore, fingerprint_of
from ops.plane_migrate import ARCHIVE_ROOT, _set_aside


@dataclass
class Float16Report:
    store: str
    already_float16: bool = False
    rows: int = 0
    plane_copied: bool = False
    mb_before: float = 0.0
    mb_after: float = 0.0
    mismatches: list[str] = field(default_factory=list)
    swapped: bool = False
    archive: str = ""
    build: str = ""
    refused: str = ""

    @property
    def verified(self) -> bool:
        return not self.mismatches and not self.refused

    def __str__(self) -> str:
        if self.already_float16:
            return f"{self.store}: already float16 — nothing to do"
        head = (f"{self.store}: {self.rows} rows copied in float16"
                f"{' with the plane relations' if self.plane_copied else ''}; "
                f"{self.mb_before:.1f} MB → {self.mb_after:.1f} MB; ")
        if self.refused:
            return head + f"REFUSED: {self.refused}"
        if self.mismatches:
            return head + f"{len(self.mismatches)} MISMATCH(ES), not swapped: {self.mismatches[:3]}"
        return head + (f"swapped; old store archived at {self.archive}" if self.swapped
                       else f"verified, dry run — build left at {self.build}")


def _dir_mb(path: Path) -> float:
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file()) / 1e6


def row_digest(row: dict[str, Any]) -> bytes:
    """A row as a float16 store must hold it: every non-vector column by name and value, then the
    vector's float16 bytes. The same function reads both sides, so on the old row it applies the
    cast and on the new one it is the identity."""
    h = hashlib.sha256()
    for key in sorted(row):
        if key != "vector":
            h.update(f"{key}\0{row[key]!r}\0".encode())
    vector = row.get("vector")
    if vector is not None:
        h.update(np.asarray(vector, dtype=np.float32).astype(np.float16).tobytes())
    return h.digest()


def _row_digests(store: VectorStore) -> Counter[bytes]:
    return Counter(row_digest(r) for page in store.physical_pages(clearance=MAINTENANCE_READ)
                   for r in page)


def _dump_digest(db: Path) -> str:
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        h = hashlib.sha256()
        for line in con.iterdump():
            h.update(line.encode())
        return h.hexdigest()
    finally:
        con.close()


def verify(old: VectorStore, new: VectorStore) -> list[str]:
    """What separates `new` from `old` cast to float16 — empty when the build is exact."""
    problems: list[str] = []
    if new.vector_precision() != "float16":
        problems.append(f"the build stores {new.vector_precision()}, not float16")
    want, got = _row_digests(old), _row_digests(new)
    if want != got:
        missing, extra = sum((want - got).values()), sum((got - want).values())
        problems.append(f"{missing} old rows not reproduced, {extra} rows the old store lacks")
    old_db, new_db = old.path / PLANE_FILE, new.path / PLANE_FILE
    if old_db.exists() != new_db.exists():
        problems.append("the plane database was not carried over")
    elif old_db.exists() and _dump_digest(old_db) != _dump_digest(new_db):
        problems.append("the plane database differs from the original")
    return problems


def migrate(path: Path, *, dim: int, fingerprint: Fingerprint | None,
            archive_root: Path = ARCHIVE_ROOT, dry_run: bool = False) -> Float16Report:
    report = Float16Report(store=path.name)
    old = VectorStore(path, dim=dim, embedder=fingerprint)
    if old.vector_precision() == "float16":
        report.already_float16 = True
        return report
    if not old.plane_enabled():
        report.refused = "not on the shared plane yet — run ops.plane_migrate first"
        return report
    start_version = old.table_version()
    report.mb_before = _dir_mb(path)

    build = path.with_name(path.name + ".f16-build")
    if build.exists():
        _set_aside(build, archive_root, "stale-build")
    new = VectorStore(build, dim=dim, embedder=fingerprint, precision="float16")
    report.build = str(build)

    # 1. the table, page by page, then the plane's relations whole
    for page in old.physical_pages(clearance=MAINTENANCE_READ):
        report.rows += new.copy_in(page)
    if (path / PLANE_FILE).exists():
        src = sqlite3.connect(f"file:{path / PLANE_FILE}?mode=ro", uri=True)
        dst = sqlite3.connect(build / PLANE_FILE)
        try:
            src.backup(dst)
        finally:
            src.close()
            dst.close()
        report.plane_copied = True
    new.compact(older_than=timedelta(0))     # a fresh build has no history worth keeping

    # 2. verify what will be swapped in
    report.mismatches = verify(old, new)
    report.mb_after = _dir_mb(build)
    if report.mismatches or dry_run:
        return report

    # 3. swap — only if nobody wrote to the old store meanwhile
    if old.table_version() != start_version:
        report.refused = (f"the old store changed during the build (version {start_version} → "
                          f"{old.table_version()}); stop the writers and run again")
        return report
    new.plane.close()
    report.archive = str(_set_aside(path, archive_root, "pre-f16"))
    os.rename(build, path)
    report.swapped = True
    return report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--store", choices=("vectors", "curated", "all"), default="all")
    ap.add_argument("--dry-run", action="store_true",
                    help="build and verify beside the live store; swap nothing")
    a = ap.parse_args(argv)
    from core.kernel.config import get_config

    cfg = get_config()
    targets = {"vectors": cfg.paths.vector_store, "curated": cfg.paths.curated_store}
    names = list(targets) if a.store == "all" else [a.store]
    ok = True
    for name in names:
        rep = migrate(targets[name], dim=cfg.embedding.dim, fingerprint=fingerprint_of(cfg),
                      dry_run=a.dry_run)
        print(rep)
        ok = ok and rep.verified
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
