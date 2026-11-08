"""Stack Exchange posts from the 2024-04-02 archive: questions and answers of a few sites.

    python -m edge.corpus.stackexchange --out <root>/stackexchange --budget-mb 170 \
        --site cstheory --site cs

Each site's archive (`archive.org/download/stackexchange_20240402/<site>.stackexchange.com.7z`,
CC BY-SA 4.0, no account) is downloaded once, resumably, and its `Posts.xml`, `PostLinks.xml` and
`PostHistory.xml` extracted with the system's `bsdtar` into `raw/<site>/`. The sites are taken in
the order given, each in date order, until the byte budget is spent, so a site cut by the budget
is a time cut of it. An item is a post: a question's title, its body and its tags; an answer's body
under its question's title. The metadata carry the post's date, its question (for an answer), its
tags, its links to other posts (duplicates, related), the Wikipedia, arXiv and DOI links in its
body, and the dates of its body's versions (`PostHistory`: the initial body, each edit, each
rollback). The authorship the licence asks to be attributed stays in the archive beside it; the
text is read and held locally, never republished.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import urllib.parse
import xml.etree.ElementTree as ET
from collections import defaultdict
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from edge.corpus.common import Fetcher, html_text, read_state, write_state
from edge.corpus.stream import StreamWriter

ARCHIVE = "https://archive.org/download/stackexchange_20240402"
_WIKI = re.compile(r"en\.(?:m\.)?wikipedia\.org/wiki/([^?#]+)")
_ARXIV = re.compile(r"arxiv\.org/(?:abs|pdf)/([^\s?#]+?)(?:v\d+)?(?:\.pdf)?$")
_DOI = re.compile(r"(?:dx\.)?doi\.org/(10\.\d{4,9}/[^\s?#]+)", re.I)


def rows(path: Path) -> Iterator[dict[str, str]]:
    """The `<row …/>` elements of a dump file, as attribute dictionaries, streamed. A dump holds
    one row a line; the 2024-04-02 files are UTF-16 behind a byte-order mark although their
    declaration says UTF-8, so the encoding is read off the mark, not the declaration."""
    with path.open("rb") as fh:
        mark = fh.read(2)
    encoding = "utf-16" if mark in (b"\xff\xfe", b"\xfe\xff") else "utf-8-sig"
    with path.open(encoding=encoding) as fh:
        for line in fh:
            line = line.strip()
            if line.startswith("<row "):
                yield dict(ET.fromstring(_CHARREF.sub(_charref, line)).attrib)


_CHARREF = re.compile(r"&#(x[0-9a-fA-F]+|[0-9]+);")


def _charref(m: re.Match[str]) -> str:
    """A character reference XML 1.0 admits stays; one it does not (a control character, a
    surrogate) becomes a space, as the dumps carry a few."""
    v = m.group(1)
    code = int(v[1:], 16) if v[0] in "xX" else int(v)
    ok = code in (0x9, 0xA, 0xD) or 0x20 <= code <= 0xD7FF or 0xE000 <= code <= 0xFFFD \
        or 0x10000 <= code <= 0x10FFFF
    return m.group(0) if ok else " "


def classify_links(hrefs: list[str]) -> dict[str, list[str]]:
    wiki, arxiv, doi = set(), set(), set()
    for h in hrefs:
        m = _WIKI.search(h)
        if m:
            t = urllib.parse.unquote(m.group(1)).replace("_", " ").strip()
            if t:
                wiki.add(t[:1].upper() + t[1:])
        m = _ARXIV.search(h)
        if m:
            arxiv.add(m.group(1))
        m = _DOI.search(h)
        if m:
            doi.add(urllib.parse.unquote(m.group(1)).lower())
    return {"wikipedia": sorted(wiki), "arxiv": sorted(arxiv), "doi": sorted(doi)}


def fetch_site(f: Fetcher, out: Path, site: str) -> Path:
    raw = out / "raw" / site
    raw.mkdir(parents=True, exist_ok=True)
    if all((raw / n).is_file() for n in ("Posts.xml", "PostLinks.xml", "PostHistory.xml")):
        return raw
    host = f"{site}.stackexchange.com"
    archive = out / "raw" / f"{host}.7z"
    f.download(f"{ARCHIVE}/{host}.7z", archive)
    subprocess.run(["bsdtar", "-xf", str(archive), "-C", str(raw), "Posts.xml", "PostLinks.xml",
                    "PostHistory.xml"], check=True)
    return raw


def site_items(raw: Path, site: str) -> Iterator[tuple[str, str, str, dict[str, Any]]]:
    """A site's posts in date order: (id, title, content, metadata)."""
    links: dict[str, list[list[str]]] = defaultdict(list)
    for r in rows(raw / "PostLinks.xml"):
        links[r.get("PostId", "")].append([f"{site}-{r.get('RelatedPostId', '')}",
                                           "duplicate" if r.get("LinkTypeId") == "3"
                                           else "related"])
    versions: dict[str, list[str]] = defaultdict(list)
    for r in rows(raw / "PostHistory.xml"):
        if r.get("PostHistoryTypeId") in ("2", "5", "8"):        # initial, edit, rollback body
            versions[r.get("PostId", "")].append(r.get("CreationDate", "")[:10])
    titles: dict[str, str] = {}
    posts = []
    for r in rows(raw / "Posts.xml"):
        kind = r.get("PostTypeId")
        if kind not in ("1", "2") or r.get("DeletionDate"):
            continue
        if kind == "1":
            titles[r["Id"]] = r.get("Title", "")
        posts.append(r)
    posts.sort(key=lambda r: (r.get("CreationDate", ""), int(r["Id"])))
    for r in posts:
        pid, kind = r["Id"], r.get("PostTypeId")
        body, hrefs = html_text(r.get("Body", ""))
        if not body:
            continue
        tags = [t for t in re.split(r"[<>|]", r.get("Tags", "")) if t]
        if kind == "1":
            title = r.get("Title", "").strip()
            content = f"{title}\n\n{body}" + (f"\n\nTags: {', '.join(tags)}" if tags else "")
            parent = ""
        else:
            parent_id = r.get("ParentId", "")
            title = f"Answer to: {titles.get(parent_id, '').strip()}"
            content = f"{title}\n\n{body}"
            parent = f"{site}-{parent_id}"
        meta = {"site": site, "post": int(pid), "kind": "question" if kind == "1" else "answer",
                "date": r.get("CreationDate", "")[:10], "parent": parent, "tags": tags,
                "accepted": f"{site}-{r['AcceptedAnswerId']}" if r.get("AcceptedAnswerId")
                else "", "score": int(r.get("Score", "0") or 0),
                "post_links": links.get(pid, []), "links": classify_links(hrefs),
                "versions": sorted(versions.get(pid, []))}
        yield f"{site}-{pid}", title, content, meta


def run(out: Path, budget: int, sites: list[str], interval: float) -> None:
    f = Fetcher(interval, timeout=600.0)
    w = StreamWriter(out)
    state_path = out / "state.json"
    state = read_state(state_path)
    try:
        for site in sites:
            if w.text_bytes >= budget:
                break
            if state.get(f"done:{site}"):
                continue
            raw = fetch_site(f, out, site)
            n = 0
            for item_id, title, content, meta in site_items(raw, site):
                if w.text_bytes >= budget:
                    break
                if w.has(item_id):
                    continue
                w.append(item_id, title, content, meta=meta)
                n += 1
                if n % 20000 == 0:
                    w.close_part()
                    print(f"stackexchange: {site} {n} posts, {w.text_bytes / 1e6:.1f} MB",
                          flush=True)
            w.close_part()
            state[f"done:{site}"] = w.text_bytes < budget
            write_state(state_path, state)
            print(f"stackexchange: {site} {n} posts, {w.text_bytes / 1e6:.1f} MB", flush=True)
    finally:
        w.close()
        state["done"] = True
        write_state(state_path, state)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--budget-mb", type=float, default=170.0)
    ap.add_argument("--site", dest="sites", action="append", default=None)
    ap.add_argument("--interval", type=float, default=2.0)
    a = ap.parse_args()
    run(a.out, int(a.budget_mb * 1e6), a.sites or ["cstheory", "cs"], a.interval)
    print("stackexchange: done", file=sys.stderr)


if __name__ == "__main__":
    main()
