"""Stage 1's measurements on the corpus instance (dn-corpus-instance §6), one subcommand each.

    MIND_PALACE_OVERLAY=config/instances/corpus.toml uv run python -m eval.corpus.stage1 edges
    ... stage1 macro [--only wikipedia.hyperlink ...]
    ... stage1 rises | bridges | battery | attribution | codes | footprint

Each writes its numbers as JSON under the instance's `results/`; nothing here writes a store. The
measurements that need no vector (edges, macro, rises, the explicit bridges) read the streams'
metadata alone and may run while the instance is still ingesting; the others read the plane.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

from core.kernel.config import Config, get_config
from eval.corpus.data import SOURCES, Corpus, load

MACRO = ("wikipedia.hyperlink", "openalex.citation", "stackexchange.link", "stackexchange.answer",
         "stackexchange.version", "arxiv.version")


def _cfg() -> Config:
    cfg = get_config()
    if cfg.instance.id != "corpus":
        raise SystemExit("refusing: set MIND_PALACE_OVERLAY=config/instances/corpus.toml")
    return cfg


def results(cfg: Config) -> Path:
    d = cfg.instance.root / "results"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _clean(x: Any) -> Any:
    """NaN and infinities as None, so the JSON is standard."""
    if isinstance(x, float) and (math.isnan(x) or math.isinf(x)):
        return None
    if isinstance(x, dict):
        return {k: _clean(v) for k, v in x.items()}
    if isinstance(x, list | tuple):
        return [_clean(v) for v in x]
    if hasattr(x, "item") and not isinstance(x, (str, bytes)):
        try:
            return _clean(x.item())
        except (TypeError, ValueError):
            return x
    return x


def write(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(_clean(obj), indent=1))


def corpus(cfg: Config) -> Corpus:
    return load(cfg.ingestion.corpus.root, tuple(cfg.ingestion.corpus.sources) or SOURCES)


def cmd_edges(a: argparse.Namespace) -> None:
    from eval.corpus.edges import build, save

    cfg = _cfg()
    c = corpus(cfg)
    rel = build(c)
    report = save(rel, cfg.paths.data_dir / "edges")
    write(results(cfg) / "edges.json", {"items": c.n, "relations": report})
    for k, v in report.items():
        print(f"{k:34s} {v['edges']:9d} edges  {v['bytes_per_edge']} B/edge")


def _macro_one(name: str, reps: int, max_boot_n: int) -> tuple[str, dict[str, Any]]:
    from eval.corpus.edges import build
    from eval.corpus.macro import curves, degenerate

    cfg = _cfg()
    rel = build(corpus(cfg))[name]
    out = {"degenerate": degenerate(rel)}
    if out["degenerate"].get("largest", 0) >= 300:
        out.update(curves(rel, reps=reps, max_boot_n=max_boot_n,
                          log=lambda m: print(m, flush=True)))
    write(results(cfg) / "macro" / f"{name}.json", out)
    return name, out


def cmd_macro(a: argparse.Namespace) -> None:
    cfg = _cfg()
    (results(cfg) / "macro").mkdir(parents=True, exist_ok=True)
    names = a.only or list(MACRO)
    with ProcessPoolExecutor(max_workers=a.workers) as pool:
        for name, out in pool.map(_macro_one, names, [a.reps] * len(names),
                                  [a.max_boot_n] * len(names)):
            print(name, json.dumps(_clean(out.get("crossings", out.get("degenerate")))),
                  flush=True)


def cmd_rises(a: argparse.Namespace) -> None:
    from eval.corpus.edges import build
    from eval.corpus.rises import measure

    cfg = _cfg()
    c = corpus(cfg)
    out = measure(c, build(c), start=a.start, end=a.end, min_items=a.min_items,
                  per_source=a.per_source)
    write(results(cfg) / "rises.json", out)
    print(json.dumps(_clean({k: v for k, v in out.items() if k != "names"}), indent=1))


def _vectors(cfg: Config, c: Corpus) -> Any:
    from eval.corpus.data import load_vectors

    t0 = time.time()
    vec = load_vectors(cfg, c)
    print(f"vectors: {vec.matrix.shape[0]} atoms in {time.time() - t0:.0f} s", flush=True)
    return vec


def cmd_bridges(a: argparse.Namespace) -> None:
    from eval.corpus.bridges import chunk_pairs, knn, measure
    from eval.corpus.edges import build
    from eval.corpus.rises import partition

    cfg = _cfg()
    c = corpus(cfg)
    rel = build(c)
    part = partition(c, rel)
    out: dict[str, Any] = {"explicit": measure(c, rel, part, reps=a.reps)}
    if not a.explicit_only:
        vec = _vectors(cfg, c)
        x, have = vec.item_means(c.n)
        t0 = time.time()
        i, j, sims = knn(x, have, k=a.k, sigma=a.sigma)
        print(f"semantic: {len(i)} pairs in {time.time() - t0:.0f} s", flush=True)
        out["semantic_k"], out["sigma"] = a.k, a.sigma
        out["with_semantic"] = measure(c, rel, part, semantic=(i, j), reps=a.reps)
        out["chunk_pairs"] = chunk_pairs(c, vec, sigma=a.sigma, sample=a.chunk_sample)
    write(results(cfg) / "bridges.json", out)
    print(json.dumps(_clean({k: {kk: vv for kk, vv in v.items() if kk != "top"}
                             if isinstance(v, dict) else v for k, v in out.items()}), indent=1))


def _embed_queries(cfg: Config, texts: list[str], cache: Path) -> Any:
    """Query vectors through the instance's embedder (its query template), cached by text."""
    import hashlib

    import numpy as np

    from core.ingest.embed import build_embedder

    key = hashlib.sha256("\x00".join(texts).encode()).hexdigest()[:16]
    f = cache / f"queries-{key}.npy"
    if f.is_file():
        return np.load(f)
    emb = build_embedder(cfg)
    vecs = []
    for i in range(0, len(texts), 32):
        for t in texts[i:i + 32]:
            vecs.append(emb.embed_query(t[:2000]))
    arr = np.asarray(vecs, dtype=np.float32)
    np.save(f, arr)
    return arr


def cmd_arms(a: argparse.Namespace) -> None:
    """The battery three ways (lexical, semantic, both), or the lexical arm alone before the
    vectors are in; items still without a vector are pending for the semantic arm."""
    from eval.corpus.battery import Lexical, questions, run_arms
    from eval.corpus.edges import build, twins

    cfg = _cfg()
    c = corpus(cfg)
    rel = build(c)
    tw = twins(rel)
    contents = _contents(cfg, c, set(tw))
    qs = questions(c, rel, tw, contents, per_source=a.per_source)
    lex = Lexical.load(cfg.paths.data_dir / "lexical", c)
    vec = qvec = None
    if not a.lexical_only:
        cache = results(cfg) / "cache"
        cache.mkdir(exist_ok=True)
        qvec = _embed_queries(cfg, [q.text for q in qs], cache)
        vec = _vectors(cfg, c)
    t0 = time.time()
    out = run_arms(c, qs, lex, vec=vec, qvec=qvec, twins=tw)
    out["seconds"] = round(time.time() - t0, 1)
    name = "battery-lexical.json" if a.lexical_only else "battery-arms.json"
    write(results(cfg) / name, out)
    print(json.dumps(_clean({k: v for k, v in out.items() if k != "attribution"}), indent=1))
    for arm, att in out["attribution"].items():
        print(arm, json.dumps(_clean({k: att["all"][k] for k in ("v_full", "shapley", "loo")})))
        print(arm, "twinned", json.dumps(_clean({k: att["twinned"][k]
                                                for k in ("v_full", "shapley", "loo",
                                                          "loo_p_holm")})),
              "cif10_broken", att["cif10_broken"])


def cmd_lexcost(a: argparse.Namespace) -> None:
    from eval.corpus.cost import lexical_latency

    cfg = _cfg()
    c = corpus(cfg)
    rng_titles = [str(c.meta[g].get("title") or "") for g in range(0, c.n, max(1, c.n // 300))]
    rows = lexical_latency(cfg.paths.data_dir / "lexical", [t for t in rng_titles if t][:300])
    write(results(cfg) / "lexical-latency.json", rows)
    for r in rows:
        print(r)


def cmd_battery(a: argparse.Namespace) -> None:
    import numpy as np

    from eval.corpus.battery import Engine, beir_control, questions, run
    from eval.corpus.codes import build as build_codes
    from eval.corpus.codes import preview
    from eval.corpus.edges import build, twins

    cfg = _cfg()
    c = corpus(cfg)
    rel = build(c)
    tw = twins(rel)
    contents = _contents(cfg, c, set(tw))
    qs = questions(c, rel, tw, contents, per_source=a.per_source)
    cache = results(cfg) / "cache"
    cache.mkdir(exist_ok=True)
    qvec = _embed_queries(cfg, [q.text for q in qs], cache)
    vec = _vectors(cfg, c)
    t0 = time.time()
    out = run(c, vec, qs, qvec, twins=tw)
    out["seconds"] = round(time.time() - t0, 1)
    if a.codes:
        codes_dir = cfg.paths.data_dir / "codes"
        out["codes"] = build_codes(vec.matrix, vec.atom_ids, codes_dir)
        titles = np.asarray([i for i, q in enumerate(qs) if q.family.startswith("titles:")])
        pick = titles[np.random.default_rng(0).permutation(len(titles))[:a.code_queries]]
        out["codes_preview"] = preview(vec.matrix, codes_dir, qvec[pick])
    if a.beir:
        from core.ingest.embed import build_embedder

        emb = build_embedder(cfg)
        from eval.embedder_bench import load_beir

        sets = {ds: load_beir(ds) for ds in ("scifact", "nfcorpus")}

        def docs(ts: list[str]) -> list[list[float]]:
            out_v: list[list[float]] = []
            for i in range(0, len(ts), 32):
                out_v.extend(emb.embed_documents(ts[i:i + 32]))
            return out_v

        def queries(ts: list[str]) -> list[list[float]]:
            return [emb.embed_query(t) for t in ts]
        out["beir"] = beir_control(docs, queries, sets, Engine(vec, c))
    write(results(cfg) / "battery.json", out)
    print(json.dumps(_clean({k: v for k, v in out.items() if k != "attribution"}), indent=1))
    print(json.dumps(_clean(out["attribution"]["twinned"]), indent=1))


def _contents(cfg: Config, c: Corpus, gids: set[int]) -> dict[int, str]:
    """The landed text of some items, read from their streams."""
    out: dict[int, str] = {}
    want = {c.paths[g]: g for g in gids}
    from core.ingest.stream import manifest

    for s in c.sources:
        root = cfg.ingestion.corpus.root / s
        for p in manifest(root):
            with (root / "stream" / p.file).open(encoding="utf-8") as fh:
                for line in fh:
                    doc = json.loads(line)
                    g = want.get(f"corpus/{s}/{doc['id']}")
                    if g is not None:
                        out[g] = str(doc["content"])
    return out


def cmd_footprint(a: argparse.Namespace) -> None:
    from eval.corpus.footprint import compact_occupancy, du, plane_bytes, text_bytes

    cfg = _cfg()
    data = cfg.paths.data_dir
    root = cfg.instance.root
    vectors = cfg.paths.vector_store
    out: dict[str, Any] = {
        "text": text_bytes(cfg.ingestion.corpus.root, tuple(cfg.ingestion.corpus.sources)),
        "disk": {"instance": du(root), "sources_dumps_and_streams": du(cfg.ingestion.corpus.root),
                 "raw_store": du(cfg.paths.raw_store),
                 "vectors_lance": du(vectors) - du(vectors / "plane.sqlite"),
                 "plane_sqlite": du(vectors / "plane.sqlite"),
                 "catalog": du(cfg.paths.vault_catalog),
                 "attestations": du(cfg.paths.attestation_store),
                 "edges": du(data / "edges"), "codes": du(data / "codes")},
        "plane": plane_bytes(vectors / "plane.sqlite"),
        "compact_occupancy": compact_occupancy(vectors / "plane.sqlite",
                                               results(cfg) / "compact_occupancy.sqlite"),
    }
    out["cif4_occupancy_broken"] = out["compact_occupancy"]["bytes_per_row"] > 300
    edges = json.loads((results(cfg) / "edges.json").read_text()) \
        if (results(cfg) / "edges.json").is_file() else {}
    big = {k: v for k, v in edges.get("relations", {}).items() if v.get("edges", 0) >= 1000}
    out["edge_bytes_max"] = max((v["bytes_per_edge"] for v in big.values()), default=None)
    out["cif4_edge_broken"] = bool(out["edge_bytes_max"] and out["edge_bytes_max"] > 24)
    write(results(cfg) / "footprint.json", out)
    print(json.dumps(_clean(out), indent=1))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("edges").set_defaults(fn=cmd_edges)
    p = sub.add_parser("macro")
    p.add_argument("--only", nargs="*", default=None)
    p.add_argument("--reps", type=int, default=8)
    p.add_argument("--max-boot-n", type=int, default=40000)
    p.add_argument("--workers", type=int, default=3)
    p.set_defaults(fn=cmd_macro)
    p = sub.add_parser("rises")
    p.add_argument("--start", default="2012-01-01")
    p.add_argument("--end", default="2024-12-31")
    p.add_argument("--min-items", type=int, default=150)
    p.add_argument("--per-source", type=int, default=20)
    p.set_defaults(fn=cmd_rises)
    p = sub.add_parser("bridges")
    p.add_argument("--reps", type=int, default=20)
    p.add_argument("--k", type=int, default=10)
    p.add_argument("--sigma", type=float, default=0.785)
    p.add_argument("--chunk-sample", type=int, default=20000)
    p.add_argument("--explicit-only", action="store_true")
    p.set_defaults(fn=cmd_bridges)
    p = sub.add_parser("battery")
    p.add_argument("--per-source", type=int, default=500)
    p.add_argument("--codes", action="store_true")
    p.add_argument("--code-queries", type=int, default=500)
    p.add_argument("--beir", action="store_true")
    p.set_defaults(fn=cmd_battery)
    sub.add_parser("footprint").set_defaults(fn=cmd_footprint)
    sub.add_parser("lexcost").set_defaults(fn=cmd_lexcost)
    p = sub.add_parser("arms")
    p.add_argument("--per-source", type=int, default=500)
    p.add_argument("--lexical-only", action="store_true")
    p.set_defaults(fn=cmd_arms)
    a = ap.parse_args()
    t0 = time.time()
    a.fn(a)
    print(f"done in {time.time() - t0:.0f} s", file=sys.stderr)


if __name__ == "__main__":
    main()
