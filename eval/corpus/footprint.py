"""What stage 1 costs on disk and at the lander (dn-corpus-instance §4, §6; CIF-4).

Measured, not derived: the bytes each store of the instance holds (its files on disk), the text
the streams carry and what `zstd -3` makes of it, the plane's bytes per occupancy as the live
shape holds them (the SQLite relation with its three indexes), and the compact shape the design
targets, built here beside it: one row an item version, integer ids, one index (the primary key),
its atoms numbered contiguously within the item, so the row is (item, version, first atom, atom
count, landed day). CIF-4 is broken by a compact row above 300 bytes or a columnar edge above 24.
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any


def du(path: Path) -> int:
    """Bytes the files under `path` take on disk (blocks allocated, as `du` counts them)."""
    if not path.exists():
        return 0
    if path.is_file():
        return path.stat().st_blocks * 512
    total = 0
    for root, _dirs, files in os.walk(path):
        for f in files:
            try:
                total += os.lstat(os.path.join(root, f)).st_blocks * 512
            except OSError:
                continue
    return total


def text_bytes(sources_root: Path, sources: tuple[str, ...]) -> dict[str, Any]:
    """The streams' item text: UTF-8 bytes, and zstd at level 3 of each source's concatenation."""
    import json
    from compression import zstd

    from core.ingest.stream import manifest

    out: dict[str, Any] = {}
    for s in sources:
        raw = bytearray()
        items = 0
        for p in manifest(sources_root / s):          # the whole parts, as the lander reads
            with (sources_root / s / "stream" / p.file).open(encoding="utf-8") as fh:
                for line in fh:
                    raw += json.loads(line)["content"].encode("utf-8") + b"\n"
                    items += 1
        packed = zstd.compress(bytes(raw), level=3)
        out[s] = {"items": items, "text_bytes": len(raw), "zstd3_bytes": len(packed),
                  "zstd3_ratio": round(len(raw) / max(1, len(packed)), 3)}
    return out


def compact_occupancy(plane: Path, out: Path) -> dict[str, Any]:
    """The item-grain occupancy table, built from the plane's observed relation."""
    src = sqlite3.connect(f"file:{plane}?mode=ro", uri=True)
    rows = src.execute("SELECT source_path, digest, MIN(landed_at), COUNT(*) FROM occ_observed "
                       "GROUP BY source_path, digest ORDER BY source_path").fetchall()
    occs = src.execute("SELECT COUNT(*) FROM occ_observed").fetchone()[0]
    src.close()
    out.unlink(missing_ok=True)
    dst = sqlite3.connect(out)
    dst.execute("CREATE TABLE occ (item INTEGER NOT NULL, version INTEGER NOT NULL, "
                "atom_first INTEGER NOT NULL, atom_count INTEGER NOT NULL, "
                "landed INTEGER NOT NULL, PRIMARY KEY (item, version)) WITHOUT ROWID")
    item_id: dict[str, int] = {}
    version: dict[str, int] = {}
    batch = []
    atom = 0
    for path, _digest, landed, count in rows:
        i = item_id.setdefault(str(path), len(item_id))
        v = version.get(str(path), 0)
        version[str(path)] = v + 1
        day = int(str(landed)[:10].replace("-", ""))
        batch.append((i, v, atom, int(count), day))
        atom += int(count)
    dst.executemany("INSERT INTO occ VALUES (?, ?, ?, ?, ?)", batch)
    dst.commit()
    dst.execute("VACUUM")
    dst.close()
    size = out.stat().st_size
    return {"rows": len(batch), "chunk_occupancies": int(occs), "bytes": size,
            "bytes_per_row": round(size / max(1, len(batch)), 1)}


def plane_bytes(plane: Path) -> dict[str, Any]:
    con = sqlite3.connect(f"file:{plane}?mode=ro", uri=True)
    occs = con.execute("SELECT COUNT(*) FROM occ_observed").fetchone()[0]
    con.close()
    size = plane.stat().st_size + sum(p.stat().st_size for p in plane.parent.glob(
        plane.name + "-*"))
    return {"occupancies": int(occs), "bytes": size,
            "bytes_per_occupancy": round(size / max(1, occs), 1)}
