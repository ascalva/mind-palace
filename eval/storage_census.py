"""How much the vector stores repeat themselves, and how the palace's language is distributed.

    uv run python eval/storage_census.py [--json data/eval/storage-census.json]

Two measurements behind docs/brainstorms/shared-vectors.md (the owner's direction: one stored
vector per unique chunk, shared by every document and stratum that uses it):

1. Duplicate chunks. Rows are doc-scoped today (`id = source_path:chunk_hash`), so the same text in
   two documents is embedded and stored twice. For each store and stratum this counts rows, unique
   texts, duplicate rows, and the vector bytes a content-addressed table would not store; then
   the texts shared ACROSS strata (the links a shared table would make for free).
2. Word frequencies per stratum (Zipf's law). Rank-frequency is fitted two ways over the top ranks:
   a power law (a straight line on log-log axes) and an exponential (a straight line on semi-log
   axes), with R² for each, plus the maximum-likelihood exponent of the frequency distribution
   (Clauset, Shalizi & Newman 2009, discrete approximation, x_min chosen by the KS distance).

Reads the stores read-only under the seal; prints counts and shapes only. No private text is
printed: duplicated passages are shown for the curated (public) store alone.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

_WORD = re.compile(r"[a-z]+(?:'[a-z]+)?")
TOP_RANKS = 2000   # fit over the head and body; the far tail is all hapaxes (frequency 1)


def _rows(store: Any) -> list[dict[str, Any]]:
    """Every record row's stratum and text, never a vector (A3): the physical rows that carry a
    class (code, and prose not yet on the plane), plus the plane's current occupancies joined to
    their atom's text. Classless physical rows are the shared atoms themselves — not records."""
    from core.kernel.clearance import MAINTENANCE_READ

    rows = [r for r in store.project(["id", "provenance", "layer", "source_path", "text"],
                                     clearance=MAINTENANCE_READ) if r.get("provenance")]
    occ = store.plane.reader(MAINTENANCE_READ).occupancies()
    ids = sorted({o.atom_id for o in occ})
    text: dict[str, str] = {}
    for i in range(0, len(ids), 400):
        where = "id IN (" + ", ".join("'" + a.replace("'", "''") + "'"
                                      for a in ids[i:i + 400]) + ")"
        text.update({str(r["id"]): str(r["text"]) for r in store.project(
            ["id", "text"], clearance=MAINTENANCE_READ, where=where)})
    rows += [{"id": f"{o.source_path}:{o.atom_id.split(':', 1)[1]}",
              "provenance": o.provenance.value, "layer": o.atom_id.split(":", 1)[0],
              "source_path": o.source_path, "text": text[o.atom_id]}
             for o in occ if o.atom_id in text]
    return rows


def plane(store: Any, dim: int) -> dict[str, Any]:
    """The shared plane's own reading (A3, D6): atoms stored vs current occupancies per class, and
    what the vectors cost with sharing against what they would cost without it."""
    from core.kernel.clearance import MAINTENANCE_READ
    from core.stores.vectorstore import ELEMENT_BYTES

    gauges = store.plane.reader(MAINTENANCE_READ).gauges()
    atoms = len(store.plane.atoms.ids())
    occ = sum(g.occupancies for g in gauges.values())
    width = dim * ELEMENT_BYTES[store.vector_precision()]      # A4: the bytes as stored
    return {"atoms": atoms, "occupancies": occ, "precision": store.vector_precision(),
            "dedup_factor": round(occ / atoms, 4) if atoms else 0.0,
            "vector_mb": round(atoms * width / 1e6, 2),
            "vector_mb_without_sharing": round(occ * width / 1e6, 2),
            "per_class": {k.value: {"occupancies": g.occupancies, "atoms": g.atoms,
                                    "documents": g.documents, "embeds_avoided": g.embeds_avoided}
                          for k, g in gauges.items() if g.occupancies}}


def _stratum(row: dict[str, Any], store: str) -> str:
    """curated (papers), code, or the prose provenance: authored-solo (the owner's notes, the
    mirror), authored-dialogue and observed (conversations)."""
    return "curated" if store == "curated" else str(row.get("provenance") or "unknown")


def duplicates(rows_by_store: dict[str, list[dict[str, Any]]],
               width: dict[str, int]) -> dict[str, Any]:
    """Duplicate chunks per stratum and across strata; `width` is each store's bytes per
    stored vector (A4: its dimension times its precision's element size)."""
    out: dict[str, Any] = {"per_stratum": {}, "cross_strata": {}}
    where: dict[str, set[str]] = defaultdict(set)
    seen_text: dict[str, str] = {}
    for store, rows in rows_by_store.items():
        groups: dict[str, Counter[str]] = defaultdict(Counter)
        for r in rows:
            h = hashlib.sha256(str(r["text"]).encode("utf-8")).hexdigest()
            stratum = _stratum(r, store)
            groups[stratum][h] += 1
            where[h].add(stratum)
            if store == "curated":
                seen_text.setdefault(h, str(r["text"]))
        for stratum, counts in groups.items():
            rows_n, unique = sum(counts.values()), len(counts)
            dup = rows_n - unique
            top = []
            if stratum == "curated":
                top = [{"copies": n, "text": " ".join(seen_text[h].split())[:90]}
                       for h, n in counts.most_common(5) if n > 1]
            out["per_stratum"][stratum] = {
                "rows": rows_n, "unique_texts": unique, "duplicate_rows": dup,
                "duplicate_pct": round(100 * dup / max(rows_n, 1), 2),
                "vector_mb_avoidable": round(dup * width[store] / 1e6, 2), "most_copied": top}
    multi = [s for s in where.values() if len(s) > 1]
    pairs: Counter[str] = Counter(" + ".join(sorted(s)) for s in multi)
    out["cross_strata"] = {"texts_in_several_strata": len(multi), "by_strata": dict(pairs)}
    return out


def _r2(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    slope, icept = np.polyfit(x, y, 1)
    resid = y - (slope * x + icept)
    return float(slope), float(1 - resid.var() / y.var())


def _mle_alpha(freqs: np.ndarray) -> tuple[float, int, float]:
    """Discrete power-law exponent α of P(f) ∝ f^-α by maximum likelihood (Clauset et al. 2009,
    eq. 3.7's approximation), x_min chosen to minimize the KS distance."""
    best = (math.nan, 1, math.inf)
    for xmin in sorted({int(v) for v in np.unique(freqs) if v <= np.percentile(freqs, 99)})[:60]:
        tail = freqs[freqs >= xmin].astype(float)
        if len(tail) < 50:
            break
        alpha = 1 + len(tail) / np.sum(np.log(tail / (xmin - 0.5)))
        xs = np.sort(tail)
        emp = np.arange(1, len(xs) + 1) / len(xs)
        fit = 1 - (xs / xmin) ** (1 - alpha)
        ks = float(np.max(np.abs(emp - fit)))
        if ks < best[2]:
            best = (float(alpha), xmin, ks)
    return best


def zipf(texts_by_stratum: dict[str, list[str]]) -> dict[str, Any]:
    out = {}
    for stratum, texts in texts_by_stratum.items():
        counts = Counter(w for t in texts for w in _WORD.findall(t.lower()))
        if len(counts) < 200:
            continue
        f = np.array(sorted(counts.values(), reverse=True), dtype=float)
        r = np.arange(1, len(f) + 1, dtype=float)
        n = min(TOP_RANKS, len(f))
        s_pow, r2_pow = _r2(np.log(r[:n]), np.log(f[:n]))
        _, r2_exp = _r2(r[:n], np.log(f[:n]))
        alpha, xmin, ks = _mle_alpha(f)
        out[stratum] = {
            "tokens": int(f.sum()), "vocabulary": len(f),
            "hapax_pct": round(100 * float((f == 1).sum()) / len(f), 1),
            "zipf_slope_loglog": round(s_pow, 3), "r2_power_law": round(r2_pow, 4),
            "r2_exponential": round(r2_exp, 4),
            "mle_alpha": round(alpha, 3), "mle_xmin": xmin, "ks": round(ks, 4),
            "rank_freq": [int(v) for v in f[:TOP_RANKS]],   # for plotting; counts only, no words
        }
    return out


def vocabulary(texts_by_stratum: dict[str, list[str]]) -> dict[str, float]:
    """How much of each stratum's vocabulary (words used at least twice) another stratum also uses:
    the "common language" a shared token layer would link on."""
    vocab = {k: {w for w, n in Counter(w for t in v for w in _WORD.findall(t.lower())).items()
                 if n >= 2} for k, v in texts_by_stratum.items()}
    return {f"{a} in {b}": round(len(va & vocab[b]) / max(len(va), 1), 3)
            for a, va in vocab.items() for b in vocab if a != b and len(va) >= 100}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--json", type=Path, default=ROOT / "data" / "eval" / "storage-census.json")
    a = ap.parse_args(argv)
    from core.sealing import seal

    seal()
    from core.kernel.config import get_config
    from core.stores.curated_store import open_curated_store
    from core.stores.vectorstore import ELEMENT_BYTES, open_vector_store

    cfg = get_config()
    stores = {"vectors": open_vector_store(cfg), "curated": open_curated_store(cfg)}
    rows = {name: _rows(st) for name, st in stores.items()}
    precision = {name: st.vector_precision() for name, st in stores.items()}
    width = {name: cfg.embedding.dim * ELEMENT_BYTES[p] for name, p in precision.items()}
    dups = duplicates(rows, width)
    texts: dict[str, list[str]] = defaultdict(list)
    for store, rs in rows.items():
        for r in rs:
            texts[_stratum(r, store)].append(str(r["text"]))
    report = {"plane": {name: plane(st, cfg.embedding.dim) for name, st in stores.items()},
              "duplicates": dups, "zipf": zipf(texts), "shared_vocabulary": vocabulary(texts),
              "vector_bytes": {"dim": cfg.embedding.dim, "precision": precision, "mb": round(
                  sum(len(rows[name]) * width[name] for name in rows) / 1e6, 1)}}
    a.json.parent.mkdir(parents=True, exist_ok=True)
    a.json.write_text(json.dumps(report, indent=1))
    for stratum, d in dups["per_stratum"].items():
        print(f"{stratum:18} {d['rows']:>8} rows  {d['unique_texts']:>8} unique  "
              f"{d['duplicate_pct']:>6}% duplicate  {d['vector_mb_avoidable']:>7} MB avoidable")
        for t in d["most_copied"]:
            print(f"{'':20}×{t['copies']}: {t['text']}")
    print("across strata:", dups["cross_strata"])
    print("shared vocabulary:", report["shared_vocabulary"])
    print("vectors as stored:", report["vector_bytes"])
    for name, pl in report["plane"].items():
        print(f"plane {name:8} {pl['atoms']:>8} atoms for {pl['occupancies']:>8} occupancies "
              f"({pl['dedup_factor']}x) · {pl['vector_mb']} MB vs "
              f"{pl['vector_mb_without_sharing']} MB unshared")
    for stratum, z in report["zipf"].items():
        print(f"{stratum:18} {z['tokens']:>9} words, vocab {z['vocabulary']:>6}, hapax "
              f"{z['hapax_pct']}% · log-log slope {z['zipf_slope_loglog']} (R² {z['r2_power_law']})"
              f" vs exponential R² {z['r2_exponential']} · MLE α {z['mle_alpha']} "
              f"(x_min {z['mle_xmin']}, KS {z['ks']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
