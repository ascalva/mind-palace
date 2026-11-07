"""Turn raw OpenAlex pages into a `src,dst,t` edge list (src cites dst, t the citing date in days).

Only citations between works of the fetched set are kept: a reference to a work outside the field
is dropped, so the graph is the field's internal citation network.

    uv run python -m eval.scale.openalex_edges ~/datasets/openalex/complex-network
"""

from __future__ import annotations

import datetime
import gzip
import json
import sys
from pathlib import Path

EPOCH = datetime.date(1970, 1, 1)


def _wid(url: str) -> int:
    return int(url.rsplit("/W", 1)[1])


def build(raw_dir: Path) -> tuple[int, int]:
    """Write `edges.csv` and `works.csv` beside the pages; return (works, edges)."""
    works: dict[int, tuple[int, list[int]]] = {}
    for page in sorted(raw_dir.glob("slice-*.json.gz")):
        with gzip.open(page, "rt") as fh:
            body = json.load(fh)
        for r in body["results"]:
            date = r.get("publication_date")
            if not date:
                continue
            day = (datetime.date.fromisoformat(date) - EPOCH).days
            refs = [_wid(x) for x in r.get("referenced_works", [])]
            works[_wid(r["id"])] = (day, refs)
    n_edges = 0
    with (raw_dir / "edges.csv").open("w") as out:
        out.write("src,dst,t\n")
        for w, (day, refs) in works.items():
            for ref in refs:
                if ref in works and ref != w:
                    out.write(f"{w},{ref},{day}\n")
                    n_edges += 1
    with (raw_dir / "works.csv").open("w") as out:
        out.write("id,day,n_refs\n")
        for w, (day, refs) in works.items():
            out.write(f"{w},{day},{len(refs)}\n")
    return len(works), n_edges


if __name__ == "__main__":
    nw, ne = build(Path(sys.argv[1]).expanduser())
    print(f"{nw} works, {ne} in-field citations")
