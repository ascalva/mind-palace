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
        for key in ("explicit", "with_semantic"):
            e = b.get(key)
            if not e:
                continue
            out.append(f"**{key}**: {e['edges']:,} edges, {e['cross_edges']:,} across sources "
                       f"(share {_f(e['cross_share'])}, the null's {_f(e['null_cross_share'])}); "
                       f"{e['bridges']} community pairs over the null against a false-positive "
                       f"bar of {_f(e['false_positive_bar'], 1)}; CIF-2 (bridges) "
                       f"{'broken' if e['cif2_bridges_broken'] else 'held'}.\n")
            out.append("| source pair | edges | bridges |")
            out.append("|---|---|---|")
            for k, v in sorted(e["by_source_pair"].items()):
                out.append(f"| {k} | {int(v['edges']):,} | {int(v['bridges'])} |")
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
                "| arm: family | n | unscoped 1% | 10% | 100% | scoped 1% | 100% | pending |",
                "|---|---|---|---|---|---|---|---|"]
        for fam, rr in sorted(bat["recall"].items()):
            out.append("| " + " | ".join([
                fam, _f(bat["questions"][fam]), _f(rr.get("unscoped@0.01")),
                _f(rr.get("unscoped@0.1")), _f(rr.get("unscoped@1.0")),
                _f(rr.get("scoped@0.01")), _f(rr.get("scoped@1.0")),
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
        for line in cost.read_text().splitlines():
            c = json.loads(line)
            out.append(f"| `{c['sentence'].split(' \"')[0]}` | {_f(c['items'])} | "
                       f"{_f(c['chunks'])} | {_f(c.get('wall_s'), 2)} | "
                       f"{_f(c.get('peak_rss_mb'))} | "
                       f"{_f((c.get('split') or {}).get('python_share'), 2)} | "
                       f"{c.get('killed', '')} |")
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
