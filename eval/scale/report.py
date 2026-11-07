"""Markdown tables from the study's CSVs.

    uv run python -m eval.scale.report STUDY_DIR [--epoch-days]

Cut times are read as days since 1970-01-01 and printed as dates.
"""

from __future__ import annotations

import csv
import datetime
import math
import sys
from pathlib import Path

from eval.scale.study import crossing

EPOCH = datetime.date(1970, 1, 1)


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open() as fh:
        return list(csv.DictReader(fh))


def _f(x: str) -> float:
    return float(x) if x not in ("", "nan") else float("nan")


def _date(cut: str) -> str:
    return (EPOCH + datetime.timedelta(days=round(float(cut)))).isoformat()


def cuts_table(study: Path) -> str:
    """Per cut: size, degrees, gamma, relaxation times and the two forms of the SCL-1 window.

    1/gamma is the relaxation time in continuous time and 1/(eps gamma) in lazy steps; T_c =
    2/(gamma delta^2) is the window in continuous time and T = T_c / eps = 2/(eps gamma delta^2) in
    lazy steps, at delta = 10% and eps = 1/2.
    """
    out = ["| cut | N | edges | mean deg | min deg | mean deg / ln N | gamma | 1/gamma "
           "| 1/(eps gamma) | T_c | T |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in _rows(study / "cuts.csv"):
        out.append(
            f"| {_date(r['cut'])} | {r['n']} | {r['m']} | {_f(r['mean_deg']):.2f} | {r['min_deg']} "
            f"| {_f(r['deg_over_logn']):.2f} | {_f(r['gamma']):.4f} "
            f"| {_f(r['relax_cont']):.1f} | {_f(r['relax_lazy']):.1f} "
            f"| {_f(r['window_cont_10pct']):.0f} | {_f(r['window_lazy_10pct']):.0f} |"
        )
    return "\n".join(out)


def curve_table(study: Path, column: str = "width_gamma") -> str:
    """Pooled (N, width) curve per scheme, binned by half-decades of N."""
    rows = _rows(study / "boot.csv")
    out = [f"| scheme | N (geometric mean) | mean deg / ln N | median {column} | points |",
           "|---|---|---|---|---|"]
    for scheme in ("node", "edge"):
        bins: dict[int, list[tuple[float, float, float]]] = {}
        for r in rows:
            if r["scheme"] != scheme or math.isnan(_f(r[column])):
                continue
            n = _f(r["n_mean"])
            bins.setdefault(int(math.floor(2 * math.log10(n))), []).append(
                (n, _f(r["deg_over_logn"]), _f(r[column])))
        for b in sorted(bins):
            pts = bins[b]
            gm = math.exp(sum(math.log(p[0]) for p in pts) / len(pts))
            dl = sum(p[1] for p in pts) / len(pts)
            ws = sorted(p[2] for p in pts)
            out.append(f"| {scheme} | {gm:.0f} | {dl:.2f} | {ws[len(ws) // 2]:.3f} | {len(pts)} |")
    return "\n".join(out)


def crossings(study: Path) -> str:
    rows = _rows(study / "boot.csv")
    out = ["| statistic | scheme | N* (width stays at or below 10% from here up) "
           "| mean deg / ln N there |", "|---|---|---|---|"]
    for column in ("width_gamma", "width_gap1", "width_gap2", "width_gap3", "width_gap4"):
        for scheme in ("node", "edge"):
            pts = [(_f(r["n_mean"]), _f(r[column])) for r in rows if r["scheme"] == scheme]
            n_star = crossing(pts)
            if math.isnan(n_star):
                out.append(f"| {column} | {scheme} | never | |")
                continue
            cand = [r for r in rows if r["scheme"] == scheme and not math.isnan(_f(r["n_mean"]))]
            near = min(cand, key=lambda r: abs(_f(r["n_mean"]) - n_star))
            out.append(f"| {column} | {scheme} | {n_star:.0f} | {_f(near['deg_over_logn']):.2f} |")
    return "\n".join(out)


def hodge_table(study: Path) -> str:
    out = ["| cut | N | triangles | gradient | curl | harmonic | width grad (node 0.7 / edge) "
           "| width curl | width harm |", "|---|---|---|---|---|---|---|---|---|"]
    rows = _rows(study / "hodge.csv")
    by_cut: dict[str, dict[str, dict[str, str]]] = {}
    for r in rows:
        by_cut.setdefault(r["cut"], {})[r["scheme"]] = r
    for cut, d in by_cut.items():
        full = d["full"]
        nd, ed = d.get("node"), d.get("edge")

        def w(col: str, nd: dict[str, str] | None = nd, ed: dict[str, str] | None = ed) -> str:
            if nd is None or ed is None:
                return "n/a"
            return f"{_f(nd[col]):.3f} / {_f(ed[col]):.3f}"

        out.append(
            f"| {_date(cut)} | {full['n']} | {full['triangles']} | {_f(full['grad']):.3f} "
            f"| {_f(full['curl']):.3f} | {_f(full['harm']):.3f} | {w('w_grad')} | {w('w_curl')} "
            f"| {w('w_harm')} |"
        )
    return "\n".join(out)


def hodge_crossings(study: Path) -> str:
    """The scale from which each Hodge energy fraction's 10% width holds, per scheme."""
    rows = [r for r in _rows(study / "hodge.csv") if r["scheme"] in ("node", "edge")]
    out = ["| energy | scheme | N* (width stays at or below 10% from here up) |", "|---|---|---|"]
    for col, name in (("w_grad", "gradient"), ("w_curl", "curl"), ("w_harm", "harmonic")):
        for scheme in ("node", "edge"):
            pts = [(_f(r["n_mean_boot"]), _f(r[col])) for r in rows if r["scheme"] == scheme]
            n_star = crossing(pts)
            shown = "never" if math.isnan(n_star) else f"{n_star:.0f}"
            out.append(f"| {name} | {scheme} | {shown} |")
    return "\n".join(out)


def core_table(study: Path) -> str:
    """Per cut and k: the k-core's size, degrees and gamma, and the bootstrap widths of gamma."""
    cuts = {(r["cut"], r["core"]): r for r in _rows(study / "core_cuts.csv")}
    boots: dict[tuple[str, str], dict[str, float]] = {}
    for r in _rows(study / "core_boot.csv"):
        key = (r["cut"], r["core"])
        label = "edge" if r["scheme"] == "edge" else f"node{r['fraction']}"
        boots.setdefault(key, {})[label] = _f(r["width_gamma"])
    out = ["| cut | k | N | min deg | mean deg / ln N | gamma | 1/gamma | width, edge "
           "| width, node 0.85 | width, node 0.5 |", "|---|---|---|---|---|---|---|---|---|---|"]
    for key, r in cuts.items():
        b = boots.get(key, {})

        def w(label: str, b: dict[str, float] = b) -> str:
            return f"{b[label]:.3f}" if label in b else "n/a"

        out.append(
            f"| {_date(r['cut'])} | {r['core']} | {r['n']} | {r['min_deg']} "
            f"| {_f(r['deg_over_logn']):.2f} | {_f(r['gamma']):.4f} "
            f"| {_f(r['relax_cont']):.1f} "
            f"| {w('edge')} | {w('node0.85')} | {w('node0.5')} |")
    return "\n".join(out)


def core_crossings(study: Path) -> str:
    rows = _rows(study / "core_boot.csv")
    out = ["| k | scheme | N* (width of gamma stays at or below 10%) | min deg / ln N* | "
           "mean deg / ln N there |", "|---|---|---|---|---|"]
    for k in sorted({r["core"] for r in rows}, key=int):
        for scheme, frac in (("edge", None), ("node", "0.85"), ("node", "0.5")):
            sel = [r for r in rows if r["core"] == k and r["scheme"] == scheme
                   and (frac is None or r["fraction"] == frac)]
            pts = [(_f(r["n_mean"]), _f(r["width_gamma"])) for r in sel]
            n_star = crossing(pts)
            label = scheme if frac is None else f"{scheme} {frac}"
            if math.isnan(n_star):
                out.append(f"| {k} | {label} | never | | |")
                continue
            near = min((r for r in sel if not math.isnan(_f(r["n_mean"]))),
                       key=lambda r: abs(_f(r["n_mean"]) - n_star))
            out.append(f"| {k} | {label} | {n_star:.0f} | {int(k) / math.log(n_star):.2f} "
                       f"| {_f(near['deg_over_logn']):.2f} |")
    return "\n".join(out)


def main() -> None:
    study = Path(sys.argv[1]).expanduser()
    for title, body in (("Cuts", cuts_table(study)), ("Crossings", crossings(study)),
                        ("Curve of gamma", curve_table(study)),
                        ("Curve of the second eigengap", curve_table(study, "width_gap2")),
                        ("Hodge", hodge_table(study)),
                        ("Hodge crossings", hodge_crossings(study)),
                        ("Cores", core_table(study)),
                        ("Core crossings", core_crossings(study))):
        print(f"### {title}\n\n{body}\n")


if __name__ == "__main__":
    main()
