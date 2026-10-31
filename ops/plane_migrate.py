"""Move a vector store onto the shared plane (dn-vector-membership-store Amendment A3.8).

    uv run python -m ops.plane_migrate [--store vectors|curated|all] [--dry-run]

One store at a time, and nothing is deleted:

1. BUILD a new store beside the old one (`<store>.a3-build/`). Code rows are copied verbatim, in
   pages. Prose rows land through the real plane, one document at a time and in the order they
   were written, so for a path holding several versions the newest ends current and the rest are
   superseded with their edges.
2. VERIFY by reconstituting every old row from the new store: id, digest, path, chunk index,
   class, title, text and the vector bit for bit (the build keeps the old store's precision, A4).
   Any difference stops here, the live store untouched. One exception, by design: when several rows
   hold the SAME text, the plane keeps one vector for all of them (the atom's first-landed
   representative, D0), so a holder whose own copy was embedded separately — embedders are not
   bit-deterministic across batches — gets the representative. That is accepted only within
   `REPRESENTATIVE_COS` of the row's original vector, and counted; anything wider is a mismatch.
   Measured on the live paper store (2026-10-29): 823 duplicate copies, 107 bit-identical, the
   rest at cosine >= 0.9999984 (distance <= 1.6e-6).
3. SWAP only if the old store's dataset version is still the one read at the start (a writer that
   slipped in is a reason to stop, never to lose its row): the old directory is RENAMED into
   `~/mind-palace-archive/<store>-pre-a3-<UTC>` and the build renamed into its place.

Run it with writers stopped (`mind-palace stack down`, or at least `palace tick pause`): the
long-running servers keep the old store's handles open until they restart.
"""

from __future__ import annotations

import argparse
import math
import os
import shutil
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from core.kernel.clearance import MAINTENANCE_READ
from core.stores.plane import PLANE_CLASSES, Fingerprint
from core.stores.vectorstore import VectorStore, fingerprint_of

ARCHIVE_ROOT = Path.home() / "mind-palace-archive"
_PLANE_VALUES = frozenset(p.value for p in PLANE_CLASSES)
_COMPARED = ("id", "digest", "source_path", "chunk_index", "provenance", "title", "text")
#: A shared atom's representative vector must sit this close to every holder's original copy —
#: about 6x the worst jitter measured between separately embedded copies of one text.
REPRESENTATIVE_COS = 1.0 - 1e-5


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (na * nb)


@dataclass
class MigrationReport:
    store: str
    already_on_plane: bool = False
    code_rows: int = 0
    prose_rows: int = 0
    documents: int = 0
    fibers: int = 0
    atoms: int = 0
    multi_version_paths: list[str] = field(default_factory=list)
    mismatches: list[str] = field(default_factory=list)
    representatives: int = 0                    # holders given their shared atom's vector
    worst_representative_cos: float = 1.0
    swapped: bool = False
    archive: str = ""
    build: str = ""
    refused: str = ""

    @property
    def verified(self) -> bool:
        return not self.mismatches and not self.refused

    def __str__(self) -> str:
        if self.already_on_plane:
            return f"{self.store}: already on the shared plane — nothing to do"
        head = (f"{self.store}: {self.code_rows} code rows copied; {self.prose_rows} prose rows "
                f"in {self.documents} documents ({self.fibers} versions) → {self.atoms} atoms; ")
        if self.refused:
            return head + f"REFUSED: {self.refused}"
        if self.mismatches:
            return head + f"{len(self.mismatches)} MISMATCH(ES), not swapped: {self.mismatches[:3]}"
        tail = f"swapped; old store archived at {self.archive}" if self.swapped else \
            f"verified, dry run — build left at {self.build}"
        multi = f" ({len(self.multi_version_paths)} paths with several versions)" \
            if self.multi_version_paths else ""
        reps = (f"; {self.representatives} holders share a representative vector (worst cosine "
                f"{self.worst_representative_cos:.9f})") if self.representatives else ""
        return head + tail + multi + reps


def _set_aside(path: Path, archive_root: Path, label: str) -> Path:
    """Move `path` into the archive (rename; never delete). Returns where it went."""
    archive_root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    dest = archive_root / f"{path.name}-{label}-{stamp}"
    try:
        os.rename(path, dest)
    except OSError:                         # another volume: copy, then keep the original aside
        shutil.copytree(path, dest)
        os.rename(path, path.with_name(f"{path.name}.{label}-{stamp}"))
    return dest


def _key(r: dict[str, Any]) -> tuple[str, str, int]:
    return (str(r["source_path"]), str(r["digest"]), int(r.get("chunk_index", 0) or 0))


def migrate(path: Path, *, dim: int, fingerprint: Fingerprint | None,
            archive_root: Path = ARCHIVE_ROOT, dry_run: bool = False) -> MigrationReport:
    report = MigrationReport(store=path.name)
    old = VectorStore(path, dim=dim, embedder=fingerprint)
    if old.plane_enabled():
        report.already_on_plane = True
        return report
    start_version = old.table_version()

    build = path.with_name(path.name + ".a3-build")
    if build.exists():
        _set_aside(build, archive_root, "stale-build")
    new = VectorStore(build, dim=dim, embedder=fingerprint, precision=old.vector_precision())
    report.build = str(build)

    # 1a. code (and any row under a retired label) — copied verbatim, page by page
    for page in old.physical_pages(clearance=MAINTENANCE_READ,
                                   where="provenance NOT IN (" + ", ".join(
                                       f"'{v}'" for v in sorted(_PLANE_VALUES)) + ")"):
        new.add(page)
        report.code_rows += len(page)

    # 1b. prose — one document at a time, versions in the order they were written
    prose_where = "provenance IN (" + ", ".join(f"'{v}'" for v in sorted(_PLANE_VALUES)) + ")"
    paths: list[str] = list(dict.fromkeys(
        str(r["source_path"]) for r in old.project(["source_path"], clearance=MAINTENANCE_READ,
                                                   where=prose_where)))
    for doc in paths:
        rows = [r for page in old.physical_pages(
            clearance=MAINTENANCE_READ,
            where=f"{prose_where} AND source_path = '" + doc.replace("'", "''") + "'")
            for r in page]
        by_digest: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for r in rows:
            by_digest[str(r["digest"])].append(r)
        if len(by_digest) > 1:
            report.multi_version_paths.append(doc)
        for fiber_rows in by_digest.values():                 # insertion order: oldest first
            new.add(fiber_rows)
            report.fibers += 1
        report.prose_rows += len(rows)
        report.documents += 1

    # 2. verify — every old row, reconstituted from the new store
    shared_texts: dict[str, int] = defaultdict(int)
    for r in old.project(["text"], clearance=MAINTENANCE_READ, where=prose_where):
        shared_texts[str(r["text"])] += 1
    for page in old.physical_pages(clearance=MAINTENANCE_READ, where=prose_where):
        by_doc: dict[str, dict[tuple[str, str, int], Any]] = {}
        for r in page:
            doc = str(r["source_path"])
            if doc not in by_doc:
                by_doc[doc] = {_key(dict(x)): x for x in new.reader(MAINTENANCE_READ).rows(
                    include_superseded=True, source_path=doc)}
            got = by_doc[doc].get(_key(r))
            if got is None:
                report.mismatches.append(f"missing {_key(r)}")
                continue
            for col in _COMPARED:
                if got[col] != r[col]:
                    report.mismatches.append(f"{_key(r)} {col}: {r[col]!r} → {got[col]!r}")
            if list(got["vector"]) != list(r["vector"]):
                shared = shared_texts.get(str(r["text"]), 0) > 1
                cos = _cosine(list(got["vector"]), list(r["vector"]))
                if shared and cos >= REPRESENTATIVE_COS:
                    report.representatives += 1
                    report.worst_representative_cos = min(report.worst_representative_cos, cos)
                else:
                    report.mismatches.append(f"{_key(r)} vector differs (cosine {cos:.9f})")
    code_new = {str(r["id"]): r for page in new.physical_pages(clearance=MAINTENANCE_READ)
                for r in page if r.get("provenance") not in _PLANE_VALUES
                and (r.get("provenance") or r.get("source_path") or r.get("digest"))}
    code_seen = 0
    for page in old.physical_pages(clearance=MAINTENANCE_READ,
                                   where="provenance NOT IN (" + ", ".join(
                                       f"'{v}'" for v in sorted(_PLANE_VALUES)) + ")"):
        for r in page:
            code_seen += 1
            got = code_new.get(str(r["id"]))
            if got is None or any(got.get(c) != r.get(c) for c in r if c != "vector") \
                    or list(got["vector"]) != list(r["vector"]):
                report.mismatches.append(f"code row {r['id']!r} differs")
    if code_seen != len(code_new):
        report.mismatches.append(f"code rows {code_seen} → {len(code_new)}")

    report.atoms = len(new.plane.atoms.ids())
    drift = new.plane.held_drift()
    if drift:
        report.mismatches.append(f"{len(drift)} atoms with a stale held cache")
    new.compact(older_than=timedelta(0))     # a fresh build has no history worth keeping
    if report.mismatches or dry_run:
        return report

    # 3. swap — only if nobody wrote to the old store meanwhile
    if old.table_version() != start_version:
        report.refused = (f"the old store changed during the build (version {start_version} → "
                          f"{old.table_version()}); stop the writers and run again")
        return report
    new.plane.close()
    report.archive = str(_set_aside(path, archive_root, "pre-a3"))
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

