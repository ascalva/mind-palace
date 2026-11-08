"""OpenAlex works with abstracts: the twins of the arXiv sample, then works of chosen topics.

    python -m edge.corpus.openalex --out <root>/openalex --budget-mb 273 \
        [--twins <root>/arxiv/meta/items.jsonl] [--topics T10064 T10720 ...]

Two passes, both through the keyless API (`api.openalex.org/works`), one request at a time at most
four a second (the API allows ten without a key):

- the **twins**: the OpenAlex record of each arXiv record in the arXiv sample, found by its arXiv
  DOI (`10.48550/arxiv.<id>`), fifty to a request; the pair is the redundancy witness of SCL-3
  (dn-corpus-instance §6);
- the **topics**: works whose primary topic is one of `--topics` and which have an abstract, by
  basic `page=` paging over publication-date slices of at most 9,000 works (cursor paging past the
  first page needs a key, which this reader does not have), until the byte budget is spent.

An item is a work's title and its abstract (rebuilt from the inverted index); its metadata carry
the publication date, the DOI, the in-OpenAlex references, the primary topic and the arXiv id
where a location names one. The data are CC0.
"""

from __future__ import annotations

import argparse
import datetime
import gzip
import json
import re
import sys
from pathlib import Path
from typing import Any

from edge.corpus.common import Fetcher, FetchError, read_state, write_state
from edge.corpus.stream import StreamWriter

API = "https://api.openalex.org/works"
SELECT = ("id,doi,display_name,publication_date,abstract_inverted_index,referenced_works,"
          "primary_topic,locations,type,cited_by_count,language")
TOPICS = ("T10064", "T10720", "T11273", "T12592", "T11252", "T11329", "T14299")
_ARXIV = re.compile(r"arxiv\.org/(?:abs|pdf)/([^\s?#v]+(?:v\d+)?)", re.I)
_ARXIV_DOI = re.compile(r"10\.48550/arxiv\.(.+)$", re.I)


def abstract(inv: dict[str, list[int]] | None) -> str:
    """The abstract an inverted index holds, its words back in order."""
    if not inv:
        return ""
    slots: dict[int, str] = {}
    for word, places in inv.items():
        for i in places:
            slots[int(i)] = word
    return " ".join(slots[i] for i in sorted(slots))


def arxiv_of(work: dict[str, Any]) -> str:
    """The arXiv id a work names, by its DOI or a location's landing page; '' if none."""
    doi = str(work.get("doi") or "")
    m = _ARXIV_DOI.search(doi)
    if m:
        return re.sub(r"v\d+$", "", m.group(1))
    for loc in work.get("locations") or []:
        for key in ("landing_page_url", "pdf_url"):
            m = _ARXIV.search(str((loc or {}).get(key) or ""))
            if m:
                return re.sub(r"v\d+$", "", m.group(1).removesuffix(".pdf"))
    return ""


class Reader:
    def __init__(self, out: Path, budget: int, interval: float) -> None:
        self.out = out
        self.budget = budget
        self.f = Fetcher(interval)
        self.w = StreamWriter(out)
        self.raw = out / "raw"
        self.raw.mkdir(parents=True, exist_ok=True)
        self.state_path = out / "state.json"
        self.state = read_state(self.state_path)

    def full(self) -> bool:
        return self.w.text_bytes >= self.budget

    def save(self) -> None:
        self.w.close_part()
        write_state(self.state_path, self.state)

    def page(self, name: str, params: dict[str, Any]) -> dict[str, Any]:
        """One page, kept gzipped under raw/ so a rerun reads it from disk."""
        f = self.raw / f"{name}.json.gz"
        if f.is_file():
            with gzip.open(f, "rt", encoding="utf-8") as fh:
                return dict(json.load(fh))
        body = self.f.get_json(API, params)
        with gzip.open(f, "wt", encoding="utf-8") as fh:
            json.dump(body, fh)
        return dict(body)

    def take(self, work: dict[str, Any], why: str) -> bool:
        wid = str(work.get("id") or "").rsplit("/", 1)[-1]
        if not wid or self.w.has(wid):
            return False
        text = abstract(work.get("abstract_inverted_index"))
        title = str(work.get("display_name") or "").strip()
        if not text or not title:
            return False
        topic = work.get("primary_topic") or {}
        self.w.append(wid, title, f"{title}\n\n{text}", meta={
            "date": work.get("publication_date"), "doi": work.get("doi"),
            "refs": [str(r).rsplit("/", 1)[-1] for r in work.get("referenced_works") or []],
            "topic": str(topic.get("id") or "").rsplit("/", 1)[-1],
            "topic_name": topic.get("display_name"),
            "subfield": ((topic.get("subfield") or {}).get("display_name")),
            "arxiv": arxiv_of(work), "type": work.get("type"),
            "cited_by": work.get("cited_by_count"), "language": work.get("language"),
            "via": why})
        return True

    def twins(self, arxiv_meta: Path) -> None:
        ids = []
        with arxiv_meta.open(encoding="utf-8") as fh:
            for line in fh:
                aid = json.loads(line).get("arxiv_id")
                if aid:
                    ids.append(str(aid))
        start = int(self.state.get("twins_done", 0))
        for i in range(start, len(ids), 50):
            if self.full():
                return
            chunk = ids[i:i + 50]
            dois = "|".join(f"https://doi.org/10.48550/arxiv.{a}" for a in chunk)
            try:
                body = self.page(f"twins-{i:07d}", {"filter": f"doi:{dois}", "select": SELECT,
                                                     "per-page": 50})
            except FetchError as e:
                print(f"openalex twins: {e}", file=sys.stderr)
                continue
            for work in body.get("results", []):
                self.take(work, "twin")
            self.state["twins_done"] = i + 50
            if (i // 50) % 20 == 0:
                self.save()
                print(f"openalex: twins {i + 50}/{len(ids)}, {len(self.w.ids)} works, "
                      f"{self.w.text_bytes / 1e6:.1f} MB", flush=True)
        self.save()

    def count(self, flt: str) -> int:
        body = self.f.get_json(API, {"filter": flt, "per-page": 1, "select": "id"})
        return int(body.get("meta", {}).get("count", 0))

    def slices(self, topic: str) -> list[tuple[str, str]]:
        key = f"slices-{topic}"
        if key in self.state:
            return [tuple(x) for x in self.state[key]]
        out: list[tuple[str, str]] = []

        def flt(lo: str, hi: str) -> str:
            return (f"primary_topic.id:{topic},has_abstract:true,"
                    f"from_publication_date:{lo},to_publication_date:{hi}")

        def split(lo: datetime.date, hi: datetime.date) -> None:
            n = self.count(flt(lo.isoformat(), hi.isoformat()))
            if n == 0:
                return
            if n > 9000 and hi > lo:
                mid = lo + (hi - lo) // 2
                split(lo, mid)
                split(mid + datetime.timedelta(days=1), hi)
            else:
                out.append((lo.isoformat(), hi.isoformat()))

        split(datetime.date(1900, 1, 1), datetime.date(1999, 12, 31))
        for y in range(2000, datetime.date.today().year + 1):
            split(datetime.date(y, 1, 1), datetime.date(y, 12, 31))
        self.state[key] = out
        write_state(self.state_path, self.state)
        return out

    def topic(self, topic: str) -> None:
        for lo, hi in self.slices(topic):
            mark = f"done-{topic}-{lo}"
            if self.state.get(mark):
                continue
            page = 1
            while not self.full():
                params = {"filter": f"primary_topic.id:{topic},has_abstract:true,"
                                    f"from_publication_date:{lo},to_publication_date:{hi}",
                          "select": SELECT, "per-page": 200, "page": page}
                try:
                    body = self.page(f"{topic}-{lo}-p{page:02d}", params)
                except FetchError as e:
                    print(f"openalex {topic} {lo}: {e}", file=sys.stderr)
                    break
                results = body.get("results", [])
                for work in results:
                    self.take(work, topic)
                if len(results) < 200:
                    break
                page += 1
            if self.full():
                self.save()
                return
            self.state[mark] = True
            self.save()
            print(f"openalex: {topic} {lo}..{hi}, {len(self.w.ids)} works, "
                  f"{self.w.text_bytes / 1e6:.1f} MB", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--budget-mb", type=float, default=273.0)
    ap.add_argument("--twins", type=Path, default=None)
    ap.add_argument("--topics", nargs="*", default=list(TOPICS))
    ap.add_argument("--interval", type=float, default=0.25)
    a = ap.parse_args()
    r = Reader(a.out, int(a.budget_mb * 1e6), a.interval)
    try:
        if a.twins is not None and a.twins.is_file():
            r.twins(a.twins)
        for t in a.topics:
            if r.full():
                break
            r.topic(t)
    finally:
        r.state["done"] = r.full()
        r.save()
        r.w.close()
    print(f"openalex: {len(r.w.ids)} works, {r.w.text_bytes / 1e6:.1f} MB, "
          f"{r.f.requests} requests")


if __name__ == "__main__":
    main()
