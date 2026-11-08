"""The vector codes beside the exact float16 vectors (dn-corpus-instance §4.2, §6): written at stage
1 so stage 2 can measure each against exact answers, and previewed here on the battery's titles.

The codes are the quantization bench's (`eval/quantization_bench.py`), computed from the plane's
float16 atoms in the plane's order: int8 at 768 dimensions (per-dimension min-max codes), the
Matryoshka prefix at 256 dimensions in float16 (renormalized) and in int8, and the one-bit sign
code at 768 bits (96 bytes). Each is saved as an array under the instance's `data/codes/`, with the
atom ids in the same order, so its bytes on disk are measured. The preview: for each code, of the
ten atoms exact float16 search returns, how many the code returns flat, and how many it returns
when its top `m` (m = 40) are rescored exactly.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import numpy.typing as npt

F32 = npt.NDArray[np.float32]


def _unit(x: F32) -> F32:
    return (x / np.maximum(np.linalg.norm(x, axis=1, keepdims=True), 1e-12)).astype(np.float32)


def minmax_codes(x: F32) -> tuple[npt.NDArray[np.uint8], F32, F32]:
    lo, hi = x.min(axis=0), x.max(axis=0)
    scale = np.where(hi > lo, (hi - lo) / 255.0, 1.0).astype(np.float32)
    return (np.clip(np.rint((x - lo) / scale), 0, 255).astype(np.uint8),
            lo.astype(np.float32), scale)


def build(matrix: npt.NDArray[np.float16], atom_ids: list[str], out: Path,
          block: int = 200000) -> dict[str, Any]:
    """Every code of the plane's atoms, saved; returns each one's bytes on disk. Two passes a
    block of rows at a time (the per-dimension ranges first, then the codes into memory-mapped
    arrays), so no float32 copy of the whole plane is held; the codes are those of one pass."""
    out.mkdir(parents=True, exist_ok=True)
    n, dim = matrix.shape
    (out / "atom_ids.txt").write_text("\n".join(atom_ids))

    def rows(a: int, b: int) -> tuple[F32, F32]:
        x = _unit(matrix[a:b].astype(np.float32))
        return x, _unit(np.ascontiguousarray(x[:, :256]))
    lo8 = np.full(dim, np.inf, np.float32)
    hi8 = np.full(dim, -np.inf, np.float32)
    lo2 = np.full(256, np.inf, np.float32)
    hi2 = np.full(256, -np.inf, np.float32)
    for a in range(0, n, block):
        x, p = rows(a, min(n, a + block))
        lo8, hi8 = np.minimum(lo8, x.min(axis=0)), np.maximum(hi8, x.max(axis=0))
        lo2, hi2 = np.minimum(lo2, p.min(axis=0)), np.maximum(hi2, p.max(axis=0))
    sc8 = np.where(hi8 > lo8, (hi8 - lo8) / 255.0, 1.0).astype(np.float32)
    sc2 = np.where(hi2 > lo2, (hi2 - lo2) / 255.0, 1.0).astype(np.float32)
    np.savez(out / "int8_768_scale.npz", lo=lo8, scale=sc8)
    np.savez(out / "int8_256_scale.npz", lo=lo2, scale=sc2)
    mm = np.lib.format.open_memmap
    c8 = mm(out / "int8_768.npy", mode="w+", dtype=np.uint8, shape=(n, dim))
    p16 = mm(out / "f16_256.npy", mode="w+", dtype=np.float16, shape=(n, 256))
    c2 = mm(out / "int8_256.npy", mode="w+", dtype=np.uint8, shape=(n, 256))
    bits = mm(out / "bits_768.npy", mode="w+", dtype=np.uint8, shape=(n, (dim + 7) // 8))
    for a in range(0, n, block):
        b = min(n, a + block)
        x, p = rows(a, b)
        c8[a:b] = np.clip(np.rint((x - lo8) / sc8), 0, 255).astype(np.uint8)
        p16[a:b] = p.astype(np.float16)
        c2[a:b] = np.clip(np.rint((p - lo2) / sc2), 0, 255).astype(np.uint8)
        bits[a:b] = np.packbits(x >= 0.0, axis=1)
    for arr in (c8, p16, c2, bits):
        arr.flush()
    del c8, p16, c2, bits
    sizes = {f.name: f.stat().st_size for f in sorted(out.iterdir()) if f.suffix in
             (".npy", ".npz")}
    return {"atoms": n, "dim": dim, "bytes": sizes,
            "bytes_per_vector": {k: round(v / n, 2) for k, v in sizes.items() if n}}


def preview(matrix: npt.NDArray[np.float16], codes: Path, queries: F32, *, k: int = 10,
            m: int = 40, block: int = 200000) -> dict[str, Any]:
    """Recall at k of each code against exact float16 search, flat and rescored at m."""
    q = _unit(queries.astype(np.float32))
    n = matrix.shape[0]

    def scan(score_block: Any) -> npt.NDArray[np.int64]:
        best_v = np.full((len(q), 0), -np.inf, dtype=np.float32)
        best_i = np.zeros((len(q), 0), dtype=np.int64)
        for s in range(0, n, block):
            v = score_block(s, min(n, s + block))
            vv = np.concatenate([best_v, v], axis=1)
            ii = np.concatenate([best_i, np.broadcast_to(np.arange(s, s + v.shape[1]),
                                                         v.shape)], axis=1)
            keep = np.argpartition(-vv, kth=min(m, vv.shape[1]) - 1, axis=1)[:, :m]
            best_v = np.take_along_axis(vv, keep, axis=1)
            best_i = np.take_along_axis(ii, keep, axis=1)
        order = np.argsort(-best_v, axis=1)
        return np.take_along_axis(best_i, order, axis=1)

    exact = scan(lambda a, b: q @ _unit(matrix[a:b].astype(np.float32)).T)[:, :k]
    lo8, sc8 = (np.load(codes / "int8_768_scale.npz")[x] for x in ("lo", "scale"))
    c8 = np.load(codes / "int8_768.npy", mmap_mode="r")
    p16 = np.load(codes / "f16_256.npy", mmap_mode="r")
    lo2, sc2 = (np.load(codes / "int8_256_scale.npz")[x] for x in ("lo", "scale"))
    c2 = np.load(codes / "int8_256.npy", mmap_mode="r")
    bits = np.load(codes / "bits_768.npy", mmap_mode="r")
    q256 = _unit(np.ascontiguousarray(q[:, :256]))
    qsign = np.where(q >= 0, 1.0, -1.0).astype(np.float32)
    schemes = {
        "int8_768": lambda a, b: q @ (c8[a:b].astype(np.float32) * sc8 + lo8).T,
        "f16_256": lambda a, b: q256 @ p16[a:b].astype(np.float32).T,
        "int8_256": lambda a, b: q256 @ (c2[a:b].astype(np.float32) * sc2 + lo2).T,
        "bits_768": lambda a, b: qsign @ (np.unpackbits(bits[a:b], axis=1)[:, :q.shape[1]]
                                          .astype(np.float32) * 2.0 - 1.0).T,
    }
    out: dict[str, Any] = {"queries": len(q), "k": k, "m": m}
    for name, fn in schemes.items():
        cand = scan(fn)
        flat = cand[:, :k]
        resc = []
        for r in range(len(q)):
            vs = q[r] @ _unit(matrix[cand[r]].astype(np.float32)).T
            resc.append(cand[r][np.argsort(-vs)[:k]])
        rs = np.asarray(resc)
        out[name] = {
            "flat": float(np.mean([len(set(flat[r]) & set(exact[r])) / k for r in range(len(q))])),
            f"rescored_m{m}": float(np.mean([len(set(rs[r]) & set(exact[r])) / k
                                             for r in range(len(q))]))}
    return out
