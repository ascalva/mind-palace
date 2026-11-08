"""arXiv metadata with abstracts and version dates: OAI-PMH, and arXiv's query API beside it.

    python -m edge.corpus.arxiv --out <root>/arxiv --budget-mb 51 \
        --twins <root>/openalex/meta/items.jsonl --category physics.soc-ph --category cs.SI

Two ways in, under the same terms (the metadata, abstracts included, are CC0; the e-prints are not
fetched) and the same manners (one request at least three seconds after the last, on one
connection, a server's `Retry-After` honoured):

- **OAI-PMH** (`--oai`): `ListRecords` with `metadataPrefix=arXivRaw` (every version's date),
  over datestamp windows of one month, newest first, kept when a category matches.
  `export.arxiv.org/oai2` redirects to `oaipmh.arxiv.org/oai`. On 2026-11-07 that endpoint
  answered neither a category set nor a one-day window inside its gateway's three-minute
  first-byte limit (503 every time), so this path is kept for when it answers;
- **the query API** (`export.arxiv.org/api/query`, the default): first the **twins**, the arXiv
  records of the OpenAlex works whose locations name an arXiv id (`--twins`, the OpenAlex reader's
  metadata), two hundred ids to a request, a seeded sample of them up to `--twins-share` of the
  budget; then the newest records of `--category`, a thousand to a request, to the budget. The API
  answers with a record's first and latest versions (`published`, `updated`, the latest version
  number in its id), so a chain's intermediate dates are not known on this path.

An item is a record's title and abstract; its metadata carry the arXiv id, the first version's
date, the versions' dates as known, the version count, the categories and the DOI.
"""

from __future__ import annotations

import argparse
import gzip
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any

from edge.corpus.common import Fetcher, FetchError, read_state, tidy, write_state
from edge.corpus.stream import StreamWriter

OAI = "https://oaipmh.arxiv.org/oai"
NS = {"oai": "http://www.openarchives.org/OAI/2.0/", "raw": "http://arxiv.org/OAI/arXivRaw/"}
CATEGORIES = ("physics.soc-ph", "cs.SI", "nlin.AO")


def _date(text: str) -> str:
    try:
        return parsedate_to_datetime(text).date().isoformat()
    except (TypeError, ValueError):
        try:
            return datetime.fromisoformat(text[:10]).date().isoformat()
        except ValueError:
            return ""


def records(xml: bytes) -> tuple[list[dict[str, Any]], str, str]:
    """The records of a response, its resumption token, and its error code if any."""
    root = ET.fromstring(xml)
    err = root.find("oai:error", NS)
    if err is not None:
        return [], "", str(err.get("code") or "error")
    out = []
    for rec in root.iterfind(".//oai:record", NS):
        head = rec.find("oai:header", NS)
        if head is not None and head.get("status") == "deleted":
            continue
        meta = rec.find("oai:metadata/raw:arXivRaw", NS)
        if meta is None:
            continue

        def text(tag: str, m: ET.Element = meta) -> str:
            el = m.find(f"raw:{tag}", NS)
            return (el.text or "").strip() if el is not None and el.text else ""
        versions = []
        for v in meta.iterfind("raw:version", NS):
            d = v.find("raw:date", NS)
            versions.append({"v": v.get("version"), "date": _date((d.text or "") if d is not None
                                                                  else "")})
        out.append({"id": text("id"), "title": re.sub(r"\s+", " ", text("title")),
                    "abstract": text("abstract"), "categories": text("categories").split(),
                    "doi": text("doi"), "license": text("license"), "versions": versions})
    tok = root.find(".//oai:resumptionToken", NS)
    return out, (tok.text or "").strip() if tok is not None and tok.text else "", ""


def months(first: str, last: str) -> list[tuple[str, str]]:
    """Calendar months from `last` back to `first` (YYYY-MM), as (from, until) day pairs."""
    y, m = map(int, last.split("-"))
    fy, fm = map(int, first.split("-"))
    out = []
    while (y, m) >= (fy, fm):
        nxt = (y + (m == 12), m % 12 + 1)
        end = (datetime(nxt[0], nxt[1], 1).date().toordinal() - 1)
        out.append((f"{y:04d}-{m:02d}-01", datetime.fromordinal(end).date().isoformat()))
        y, m = (y - (m == 1), (m - 2) % 12 + 1)
    return out


def harvest(out: Path, budget: int, categories: list[str], windows: list[tuple[str, str]], *,
            interval: float) -> None:
    f = Fetcher(interval, timeout=300.0, retries=8)
    w = StreamWriter(out)
    raw = out / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    state_path = out / "state.json"
    state = read_state(state_path)
    keep = set(categories)
    seen = int(state.get("seen", 0))
    try:
        for lo, hi in windows:
            if w.text_bytes >= budget:
                break
            key = f"{lo}_{hi}"
            if state.get(f"done:{key}"):
                continue
            token = str(state.get(f"token:{key}", ""))
            page = int(state.get(f"page:{key}", 0))
            while w.text_bytes < budget:
                cache = raw / f"{key}-{page:04d}.xml.gz"
                if cache.is_file():
                    body = gzip.decompress(cache.read_bytes())
                else:
                    params = ({"verb": "ListRecords", "resumptionToken": token} if token else
                              {"verb": "ListRecords", "metadataPrefix": "arXivRaw",
                               "from": lo, "until": hi})
                    body = f.get(OAI, params)
                    cache.write_bytes(gzip.compress(body))
                recs, token, err = records(body)
                if err == "badResumptionToken":           # expired: start the window again
                    cache.unlink(missing_ok=True)
                    token, page = "", 0
                    continue
                if err and err != "noRecordsMatch":
                    raise FetchError(f"arxiv {key}: OAI error {err}")
                seen += len(recs)
                for r in recs:
                    aid = r["id"]
                    item = aid.replace("/", "_")
                    if not aid or not r["abstract"] or w.has(item) \
                            or not keep.intersection(r["categories"]):
                        continue
                    first = r["versions"][0]["date"] if r["versions"] else ""
                    w.append(item, r["title"], f"{r['title']}\n\n{tidy(r['abstract'])}", meta={
                        "arxiv_id": aid, "date": first,
                        "versions": [v["date"] for v in r["versions"]],
                        "categories": r["categories"], "doi": r["doi"],
                        "license": r["license"], "window": key})
                    if w.text_bytes >= budget:
                        break
                page += 1
                state[f"token:{key}"], state[f"page:{key}"], state["seen"] = token, page, seen
                w.close_part()
                write_state(state_path, state)
                if page % 10 == 0 or not token:
                    print(f"arxiv: {key} page {page}, {seen} records read, {len(w.ids)} kept, "
                          f"{w.text_bytes / 1e6:.1f} MB", flush=True)
                if not token:
                    state[f"done:{key}"] = True
                    write_state(state_path, state)
                    cache_dir_prune(raw, key)
                    break
    finally:
        w.close()
        state["done"] = w.text_bytes >= budget
        write_state(state_path, state)
    print(f"arxiv: {len(w.ids)} records, {w.text_bytes / 1e6:.1f} MB, {f.requests} requests")


def cache_dir_prune(raw: Path, key: str) -> None:
    """A finished window's responses are in the stream; its cached pages are dropped."""
    for p in raw.glob(f"{key}-*.xml.gz"):
        p.unlink(missing_ok=True)


API = "https://export.arxiv.org/api/query"
ATOM = {"a": "http://www.w3.org/2005/Atom", "x": "http://arxiv.org/schemas/atom"}


def api_entries(xml: bytes) -> list[dict[str, Any]]:
    """The entries of an API answer: id without its version, the version count, the first and
    latest versions' dates, title, abstract, categories (primary first) and DOI."""
    root = ET.fromstring(xml)
    out = []
    for e in root.iterfind("a:entry", ATOM):
        raw = (e.findtext("a:id", "", ATOM) or "").rsplit("/abs/", 1)[-1]
        m = re.fullmatch(r"(.+?)v(\d+)", raw)
        if not m:
            continue
        cats = [c.get("term", "") for c in e.iterfind("a:category", ATOM)]
        prim = e.find("x:primary_category", ATOM)
        if prim is not None and prim.get("term") in cats:
            cats.remove(prim.get("term", ""))
            cats.insert(0, prim.get("term", ""))
        first = (e.findtext("a:published", "", ATOM) or "")[:10]
        last = (e.findtext("a:updated", "", ATOM) or "")[:10]
        n = int(m.group(2))
        out.append({"id": m.group(1), "versions_n": n,
                    "versions": [first] + ([last] if n > 1 and last else []),
                    "title": re.sub(r"\s+", " ", e.findtext("a:title", "", ATOM) or "").strip(),
                    "abstract": (e.findtext("a:summary", "", ATOM) or "").strip(),
                    "categories": [c for c in cats if c],
                    "doi": (e.findtext("x:doi", "", ATOM) or "").strip()})
    return out


_ARXIV_ID = re.compile(r"\d{4}\.\d{4,5}|[a-z][a-z.-]*(?:\.[A-Z]{2})?/\d{7}")


def fetch_ids(f: Fetcher, ids: list[str]) -> list[dict[str, Any]]:
    """The records of `ids` through the API; a slice the API refuses (an id it does not take) is
    split in halves until the refused id stands alone and is dropped."""
    if not ids:
        return []
    try:
        return api_entries(f.get(API, {"id_list": ",".join(ids), "max_results": len(ids)}))
    except FetchError as e:
        if "HTTP 400" not in str(e):
            raise
        if len(ids) == 1:
            return []
        half = len(ids) // 2
        return fetch_ids(f, ids[:half]) + fetch_ids(f, ids[half:])


def harvest_api(out: Path, budget: int, twins: Path | None, categories: list[str], *,
                twins_share: float, interval: float, seed: int = 0) -> None:
    import json
    import random

    f = Fetcher(interval, timeout=120.0, retries=8)
    w = StreamWriter(out)
    state_path = out / "state.json"
    state = read_state(state_path)

    def take(r: dict[str, Any], why: str) -> None:
        item = r["id"].replace("/", "_")
        if not r["abstract"] or w.has(item):
            return
        w.append(item, r["title"], f"{r['title']}\n\n{tidy(r['abstract'])}", meta={
            "arxiv_id": r["id"], "date": r["versions"][0] if r["versions"] else "",
            "versions": r["versions"], "versions_n": r["versions_n"],
            "categories": r["categories"], "doi": r["doi"], "via": why})
    try:
        if twins is not None and twins.is_file():
            ids = sorted({str(json.loads(line).get("arxiv") or "") for line in
                          twins.open(encoding="utf-8")} - {""})
            ids = [i for i in ids if _ARXIV_ID.fullmatch(i)]
            random.Random(seed).shuffle(ids)
            start = int(state.get("twins_done", 0))
            for i in range(start, len(ids), 200):
                if w.text_bytes >= twins_share * budget:
                    break
                for r in fetch_ids(f, ids[i:i + 200]):
                    take(r, "twin")
                state["twins_done"] = i + 200
                w.close_part()
                write_state(state_path, state)
                print(f"arxiv: twins {i + 200}/{len(ids)}, {len(w.ids)} records, "
                      f"{w.text_bytes / 1e6:.1f} MB", flush=True)
        query = " OR ".join(f"cat:{c}" for c in categories)
        start = int(state.get("search_done", 0))
        while w.text_bytes < budget:
            body = f.get(API, {"search_query": query, "sortBy": "submittedDate",
                               "sortOrder": "descending", "start": start, "max_results": 1000})
            got = api_entries(body)
            if not got:
                break
            for r in got:
                take(r, "category")
                if w.text_bytes >= budget:
                    break
            start += len(got)
            state["search_done"] = start
            w.close_part()
            write_state(state_path, state)
            print(f"arxiv: {query} {start}, {len(w.ids)} records, "
                  f"{w.text_bytes / 1e6:.1f} MB", flush=True)
    finally:
        w.close()
        state["done"] = True
        write_state(state_path, state)
    print(f"arxiv: {len(w.ids)} records, {w.text_bytes / 1e6:.1f} MB, {f.requests} requests")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--budget-mb", type=float, default=51.0)
    ap.add_argument("--category", dest="categories", action="append", default=None)
    ap.add_argument("--first", default="2007-01", help="the oldest month harvested (YYYY-MM)")
    ap.add_argument("--last", default=datetime.now().strftime("%Y-%m"))
    ap.add_argument("--interval", type=float, default=3.0)
    ap.add_argument("--oai", action="store_true", help="OAI-PMH datestamp windows")
    ap.add_argument("--twins", type=Path, default=None,
                    help="the OpenAlex reader's metadata, whose arXiv ids are fetched first")
    ap.add_argument("--twins-share", type=float, default=0.6)
    a = ap.parse_args()
    if a.oai:
        harvest(a.out, int(a.budget_mb * 1e6), a.categories or list(CATEGORIES),
                months(a.first, a.last), interval=max(3.0, a.interval))
    else:
        harvest_api(a.out, int(a.budget_mb * 1e6), a.twins, a.categories or list(CATEGORIES),
                    twins_share=a.twins_share, interval=max(3.0, a.interval))


if __name__ == "__main__":
    main()
