"""Stage 1's tables, from the measurements' JSON under the instance's `results/`: the markdown the
experiment report carries, regenerated whenever a measurement is re-run.

    MIND_PALACE_OVERLAY=config/instances/corpus.toml uv run python -m eval.corpus.report
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


def _f(x: Any, nd: int = 3) -> str:
    if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))):
        return "n/a"
    if isinstance(x, float):
        return f"{x:.{nd}f}"
    if isinstance(x, int):
        return f"{x:,}"
    return str(x)


def _load(d: Path, name: str) -> Any:
    f = d / name
    return json.loads(f.read_text()) if f.is_file() else None


def macro_tables(d: Path) -> list[str]:
    out: list[str] = []
    for f in sorted((d / "macro").glob("*.json")):
        m = json.loads(f.read_text())
        name = f.stem
        deg = m.get("degenerate", {})
        if not m.get("cuts"):
            out.append(f"**{name}**: {deg.get('edges', 0):,} edges, {deg.get('nodes', 0):,} "
                       f"nodes in {deg.get('components', 0):,} components, the largest "
                       f"{deg.get('largest', 0):,} nodes: no component reaches the ladder's "
                       "first rung (300), so no macro quantity is defined.\n")
            continue
        out.append(f"**{name}** ({m['edges']:,} edges)\n")
        out.append("| cut N | edges | mean deg | min deg / ln N | gamma | 6-core n | 6-core gamma "
                   "| 10-core n | grad | curl | harm | Hodge on n |")
        out.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
        for c in m["cuts"]:
            comp = c["component"]
            cores = {cr["k"]: cr for cr in c.get("cores", [])}
            h = c.get("hodge", {})
            out.append("| " + " | ".join([
                _f(comp.get("n")), _f(comp.get("m")), _f(comp.get("mean_deg"), 1),
                _f(comp.get("mindeg_over_logn"), 2), _f(comp.get("gamma"), 4),
                _f(cores.get(6, {}).get("n")), _f(cores.get(6, {}).get("gamma"), 4),
                _f(cores.get(10, {}).get("n")), _f(h.get("grad"), 3), _f(h.get("curl"), 3),
                _f(h.get("harm"), 3), _f(h.get("n"))]) + " |")
        x = m.get("crossings", {})
        out.append("")
        out.append("| reading | full | 3-core | 6-core | 10-core |")
        out.append("|---|---|---|---|---|")
        for key in ("width_gamma", "width_gap2", "width_gap3", "width_gap4"):
            out.append(f"| N* of {key.removeprefix('width_')} | " + " | ".join(
                _f(x.get(f"{p}.{key}"), 0) for p in ("full", "core3", "core6", "core10")) + " |")
        out.append(f"| N* of the Hodge widths (grad, curl, harm) | "
                   f"{_f(x.get('hodge.w_grad'), 0)}, {_f(x.get('hodge.w_curl'), 0)}, "
                   f"{_f(x.get('hodge.w_harm'), 0)} | | | |")
        out.append("")
    return out


def tables(d: Path) -> str:
    out: list[str] = ["## Macro quantities", ""]
    out += macro_tables(d)
    b = _load(d, "bridges.json")
    if b:
        out += ["## Bridges", ""]
        for key in ("explicit", "explicit_without_twins", "with_semantic",
                    "with_semantic_without_twins"):
            e = b.get(key)
            if not e:
                continue
            out.append(f"**{key}**: {e['edges']:,} edges, {e['cross_edges']:,} across sources "
                       f"(share {_f(e['cross_share'])}, the null's {_f(e['null_cross_share'])}); "
                       f"{e['bridges']} community pairs over the null against a false-positive "
                       f"bar of {_f(e['false_positive_bar'], 1)}; CIF-2 (bridges) "
                       f"{'broken' if e['cif2_bridges_broken'] else 'held'}.\n")
            out.append("| source pair | edges | bridges | the null's false positives (mean, bar) |")
            out.append("|---|---|---|---|")
            for k, v in sorted(e["by_source_pair"].items()):
                fp = (f"{_f(v.get('false_positive_mean'), 1)}, {_f(v.get('false_positive_bar'), 1)}"
                      if "false_positive_mean" in v else "n/a")
                out.append(f"| {k} | {int(v['edges']):,} | {int(v['bridges'])} | {fp} |")
            out.append("")
        cp = b.get("chunk_pairs")
        if cp:
            pairs = cp["pairs_per_chunk"]
            asked = [s for s, n in cp["asked"].items() if n]
            out.append(f"**semantic chunk pairs**: of {cp['sample']:,} chunks drawn at random, "
                       f"the chunks of other items at cosine {cp['sigma']} or more, per asking "
                       f"chunk, by the asking chunk's source (rows) and the answering chunk's "
                       f"(columns).\n")
            out.append("| asking | " + " | ".join(asked) + " |")
            out.append("|---|" + "---|" * len(asked))
            for a in asked:
                out.append(f"| {a} | " + " | ".join(_f(pairs.get(f"{a}->{t}"), 2) for t in asked)
                           + " |")
            out.append("")
    r = _load(d, "rises.json")
    if r:
        out += ["## Shared rises", "",
                "| reading | value |", "|---|---|",
                f"| communities (sources) | {r['communities']} ({r['sources']}) |",
                f"| rho_w (95% band) | {_f(r['rho_w'])} ({_f(r['rho_w_band'][0])}, "
                f"{_f(r['rho_w_band'][1])}) |",
                f"| rho_b (95% band) | {_f(r['rho_b'])} ({_f(r['rho_b_band'][0])}, "
                f"{_f(r['rho_b_band'][1])}) |",
                f"| at lag 0: rho_w, rho_b | {_f(r['rho_w_lag0'])}, {_f(r['rho_b_lag0'])} |",
                f"| the circular-shift null (band) | {_f(r['rho_null_w'])}, "
                f"{_f(r['rho_null_b'])} ({_f(r['rho_null_band'][0])}, "
                f"{_f(r['rho_null_band'][1])}) |",
                f"| N_eff at m = {_f(r['m_per_source'], 1)}, and its limit | {_f(r['n_eff'], 2)}, "
                f"{_f(r['n_eff_limit'], 2)} |", ""]
    for name, label in (("battery-lexical.json", "lexical arm"),
                        ("battery-arms.json", "three arms")):
        bat = _load(d, name)
        if not bat:
            continue
        out += [f"## Retrieval battery, {label}", "",
                "| arm: family | n | unscoped 1% | 10% | 100% | fall (95% CI) | scoped 1% | "
                "100% | fall (95% CI) | pending |",
                "|---|---|---|---|---|---|---|---|---|---|"]

        def fall(fam: str, scope: str, bat: Any = bat) -> str:
            v = bat.get("drop", {}).get(fam, {}).get(scope)
            return f"{_f(v[0])} ({_f(v[1])}, {_f(v[2])})" if v else "n/a"
        for fam, rr in sorted(bat["recall"].items()):
            out.append("| " + " | ".join([
                fam, _f(bat["questions"][fam]), _f(rr.get("unscoped@0.01")),
                _f(rr.get("unscoped@0.1")), _f(rr.get("unscoped@1.0")), fall(fam, "unscoped"),
                _f(rr.get("scoped@0.01")), _f(rr.get("scoped@1.0")), fall(fam, "scoped"),
                _f(bat.get("pending", {}).get(fam.split(":", 1)[1], 0))]) + " |")
        out.append("")
        for arm, att in bat.get("attribution", {}).items():
            for part in ("all", "twinned"):
                a = att[part]
                out.append(f"*{arm}, {part} ({a['questions']} questions, v(N) = "
                           f"{_f(a['v_full'])})*: " + "; ".join(
                               f"{s} Shapley {_f(a['shapley'][s])}, LOO {_f(a['loo'][s])} "
                               f"(p {_f(a['loo_p_holm'][s], 3)})" for s in a["shapley"]))
                out.append("")
            out.append(f"CIF-10 ({arm}): {'broken' if att['cif10_broken'] else 'held'}.\n")
        if bat.get("embedder"):
            out += ["| family | lexical | semantic | both | LOO of the embedder | Shapley of "
                    "the embedder |", "|---|---|---|---|---|---|"]
            for fam, g in sorted(bat["embedder"].items()):
                out.append(f"| {fam} | {_f(g['lexical'])} | {_f(g['semantic'])} | "
                           f"{_f(g['both'])} | {_f(g['loo_embedder'])} | "
                           f"{_f(g['shapley_embedder'])} |")
            out.append("")
    lat = _load(d, "lexical-latency.json")
    if lat:
        out += ["## Cost against N", "", "| lexical units | median query (ms) | matrix bytes |",
                "|---|---|---|"]
        out += [f"| {r['units']:,} | {r['median_ms']} | {r['matrix_bytes']:,} |" for r in lat]
        out.append("")
    cost = d / "cost.jsonl"
    if cost.is_file():
        out += ["| sentence | items | chunks | wall (s) | peak RSS (MB) | Python share | note |",
                "|---|---|---|---|---|---|---|"]
        latest: dict[tuple[str, int], dict[str, Any]] = {}
        for line in cost.read_text().splitlines():       # the last probe of each sentence and N
            c = json.loads(line)
            latest[(c["sentence"].split(' "')[0], int(c["items"]))] = c
        for c in sorted(latest.values(), key=lambda c: (int(c["items"]), c["sentence"])):
            out.append(f"| `{c['sentence'].split(' \"')[0]}` | {_f(c['items'])} | "
                       f"{_f(c['chunks'])} | {_f(c.get('wall_s'), 2)} | "
                       f"{_f(c.get('peak_rss_mb'))} | "
                       f"{_f((c.get('split') or {}).get('python_share'), 2)} | "
                       f"{c.get('killed', '')} |")
        out.append("")
    bat = _load(d, "battery.json")
    if bat and bat.get("codes"):
        co, pv = bat["codes"], bat.get("codes_preview") or {}
        m = pv.get("m", 40)
        out += ["## Codes for stage 2", "",
                f"{co['atoms']:,} atoms of {co['dim']} dimensions; the preview is recall at "
                f"{pv.get('k', 10)} against exact float16 search on {_f(pv.get('queries'))} title "
                f"queries, flat and rescored exactly from each code's top {m}.", "",
                "| code | bytes a vector | flat | rescored |", "|---|---|---|---|"]
        for k in ("int8_768", "f16_256", "int8_256", "bits_768"):
            r = pv.get(k, {})
            out.append(f"| {k} | {_f(co['bytes_per_vector'].get(k + '.npy'), 1)} | "
                       f"{_f(r.get('flat'))} | {_f(r.get(f'rescored_m{m}'))} |")
        out.append("")
    if bat and bat.get("beir"):
        out += ["## The BEIR control", "",
                "| set | documents | queries | nDCG at 10 | recall at 10 | recall at 10 among the "
                "corpus's atoms |", "|---|---|---|---|---|---|"]
        for name, v in bat["beir"].items():
            out.append(f"| {name} | {v['docs']:,} | {v['queries']:,} | {_f(v['ndcg10'])} | "
                       f"{_f(v['recall10'])} | {_f(v.get('recall10_mixed'))} |")
        out.append("")
    fp = _load(d, "footprint.json")
    if fp:
        out += ["## Footprint", "", "| store | bytes on disk |", "|---|---|"]
        out += [f"| {k} | {v:,} |" for k, v in fp["disk"].items()]
        out.append("")
        out.append(f"Plane occupancy (live shape): {_f(fp['plane']['bytes_per_occupancy'], 1)} "
                   f"B; compact item-grain row: {_f(fp['compact_occupancy']['bytes_per_row'], 1)} "
                   f"B; largest columnar edge: {_f(fp.get('edge_bytes_max'), 2)} B.\n")
    return "\n".join(out)


def main() -> None:
    from core.kernel.config import get_config

    cfg = get_config()
    print(tables(cfg.instance.root / "results"))


if __name__ == "__main__":
    main()
