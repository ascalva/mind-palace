"""The record's tables from the study's JSON (docs/experiments/embedder-use-2026-11-08.md).

    uv run python -m eval.embedder_use.report RESULTS.json

Each table row is an arm: its mean recall@10 and nDCG@10, and against the reference arm the
mean paired difference with its 95% interval, the Holm-adjusted p and the decision word. Only the
aggregates in the JSON are read; no corpus text is.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def _f(x: Any, nd: int = 3) -> str:
    if x is None:
        return "n/a"
    if isinstance(x, float):
        return f"{x:.{nd}f}"
    if isinstance(x, int):
        return f"{x:,}"
    return str(x)


def _diff(v: dict[str, Any] | None) -> str:
    if not v:
        return "reference"
    return (f"{v['mean']:+.3f} ({v['lo']:+.3f}, {v['hi']:+.3f}), "
            f"p {v['p_holm']:.3f}, {v['verdict']}")


def comparison(cmp: dict[str, Any], costs: dict[str, Any] | None = None,
               metrics: tuple[str, ...] = ("recall", "ndcg")) -> str:
    """A markdown table of one comparison, with each arm's costs when given."""
    head = ["arm"] + [m for m in metrics] + [f"{m} against {cmp['reference']}" for m in metrics]
    if costs:
        head += ["vectors", "MB at float16", "tokens"]
    lines = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for arm, v in cmp["arms"].items():
        row = [arm] + [_f(v[m]) for m in metrics] + [_diff(v.get(f"{m}_vs_ref")) for m in metrics]
        if costs:
            c = costs.get(arm, {})
            row += [_f(c.get("vectors")), _f(c.get("bytes_float16", 0) / 1e6, 1),
                    _f(c.get("tokens"))]
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines) + f"\n\n({cmp['queries']} queries)\n"


def main(argv: list[str]) -> int:
    data = json.loads(Path(argv[0]).read_text())
    for exp, body in data.items():
        if not isinstance(body, dict):
            continue
        print(f"## {exp}\n")
        for name, res in body.items():
            if not isinstance(res, dict) or "comparison" not in res:
                continue
            cmp = res["comparison"]
            if "arms" in cmp:
                print(f"### {name}\n\n{comparison(cmp, res.get('costs'))}")
            else:
                for fam, c in cmp.items():
                    print(f"### {name}: {fam}\n\n{comparison(c, res.get('costs'))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
