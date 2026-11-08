"""Project Gutenberg: English science texts, from a mirror, chosen by the public catalogue.

    python -m edge.corpus.gutenberg --out <root>/gutenberg --budget-mb 108

The catalogue (`www.gutenberg.org/cache/epub/feeds/pg_catalog.csv.gz`, public domain, one request
to the main site, which is what its feeds are for) chooses the texts: type Text, language English,
a Library of Congress class in Q (science), taken by subclass (mathematics, physics, astronomy,
general science, chemistry, natural history, geology, physiology, botany, zoology, microbiology,
anatomy) and within one by ebook number, until the byte budget is spent. The files come from the
mirror `gutenberg.pglaf.org` (the main site is for human readers), one request at least two
seconds after the last. A text whose header marks it copyrighted is skipped, as is one that is not
prose (tables of digits). The licence header and footer are cut, lines are joined into paragraphs,
and the title and authors are prepended. Public domain in the United States.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import io
import re
import sys
from pathlib import Path

from edge.corpus.common import Fetcher, FetchError, read_state, tidy, write_state
from edge.corpus.stream import StreamWriter

CATALOG = "https://www.gutenberg.org/cache/epub/feeds/pg_catalog.csv.gz"
MIRROR = "https://gutenberg.pglaf.org/cache/epub/{n}/pg{n}.txt"
ORDER = ("QA", "QC", "QB", "Q", "QD", "QH", "QE", "QP", "QK", "QL", "QR", "QM")
_START = re.compile(r"\*\*\*\s*START OF (THE|THIS) PROJECT GUTENBERG EBOOK[^*]*\*\*\*", re.I)
_END = re.compile(r"\*\*\*\s*END OF (THE|THIS) PROJECT GUTENBERG EBOOK", re.I)


def body(text: str) -> str | None:
    """A text's body between the licence's markers, its lines joined into paragraphs; None for a
    copyrighted text."""
    head = text[:6000]
    if re.search(r"copyrighted project gutenberg", head, re.I):
        return None
    m, e = _START.search(text), _END.search(text)
    core = text[m.end() if m else 0: e.start() if e else len(text)]
    paras = [" ".join(ln.strip() for ln in p.splitlines() if ln.strip())
             for p in re.split(r"\n\s*\n", core.replace("\r", ""))]
    return tidy("\n\n".join(p for p in paras if p))


def prose(text: str) -> bool:
    letters = sum(c.isalpha() for c in text[:200000])
    return len(text) > 20000 and letters / max(1, min(len(text), 200000)) > 0.6


def subclass(locc: str) -> str:
    first = locc.split(";")[0].strip()
    return first[:2] if first[:2] in ORDER else first[:1]


def run(out: Path, budget: int, interval: float) -> None:
    f = Fetcher(interval)
    w = StreamWriter(out)
    raw = out / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    cat = raw / "pg_catalog.csv.gz"
    if not cat.is_file():
        data = f.get(CATALOG)            # the feed is a gzip file (unless sent decoded)
        cat.write_bytes(data if data[:2] == b"\x1f\x8b" else gzip.compress(data))
    rows = list(csv.DictReader(io.StringIO(gzip.decompress(cat.read_bytes()).decode("utf-8"))))
    chosen = [r for r in rows if r["Type"] == "Text" and r["Language"] == "en"
              and r["LoCC"].startswith("Q")]
    chosen.sort(key=lambda r: (ORDER.index(subclass(r["LoCC"])) if subclass(r["LoCC"]) in ORDER
                               else len(ORDER), int(r["Text#"])))
    state_path = out / "state.json"
    state = read_state(state_path)
    skipped: list[int] = list(state.get("skipped", []))
    try:
        for r in chosen:
            if w.text_bytes >= budget:
                break
            n = int(r["Text#"])
            item = f"pg{n}"
            if w.has(item) or n in skipped:
                continue
            try:
                text = f.get(MIRROR.format(n=n)).decode("utf-8", errors="replace")
            except FetchError as e:
                print(f"gutenberg {n}: {e}", file=sys.stderr)
                skipped.append(n)
                continue
            b = body(text)
            if b is None or not prose(b):
                skipped.append(n)
                continue
            title = " ".join(r["Title"].split())
            authors = r["Authors"].strip()
            head = f"{title}" + (f"\nby {authors}" if authors else "")
            w.append(item, title, f"{head}\n\n{b}", meta={
                "ebook": n, "date": r["Issued"], "authors": authors, "subjects": r["Subjects"],
                "locc": r["LoCC"], "bookshelves": r["Bookshelves"]})
            if len(w.ids) % 10 == 0:
                w.close_part()
                state["skipped"] = skipped
                write_state(state_path, state)
                print(f"gutenberg: {len(w.ids)} books, {w.text_bytes / 1e6:.1f} MB", flush=True)
    finally:
        w.close()
        state["skipped"], state["done"] = skipped, True
        write_state(state_path, state)
    print(f"gutenberg: {len(w.ids)} books, {w.text_bytes / 1e6:.1f} MB, {len(skipped)} skipped")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--budget-mb", type=float, default=108.0)
    ap.add_argument("--interval", type=float, default=2.0)
    a = ap.parse_args()
    run(a.out, int(a.budget_mb * 1e6), max(2.0, a.interval))


if __name__ == "__main__":
    main()
