"""Fetch works of one OpenAlex concept into raw gzip pages, resumable by slice and page.

The crawl is polite: one request at a time, a pause between requests, a descriptive User-Agent,
exponential backoff on errors and on HTTP 429. Each page is stored verbatim
under the output directory so an interrupted run resumes.

    uv run python -m eval.scale.fetch_openalex --concept C34947359 \
        --out ~/datasets/openalex/complex-network
"""

from __future__ import annotations

import argparse
import datetime
import gzip
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://api.openalex.org/works"
USER_AGENT = "mind-palace-scale-study (academic research on graph dynamics; https://github.com/ascalva/mind-palace)"
SELECT = "id,publication_date,referenced_works,concepts"


def fetch_json(url: str, retries: int = 6, pause: float = 0.5) -> dict[str, object]:
    """GET one JSON document, retrying with exponential backoff."""
    delay = 2.0
    for attempt in range(retries):
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                body = json.load(resp)
            time.sleep(pause)
            if not isinstance(body, dict):
                raise ValueError("unexpected response")
            return body
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            if isinstance(exc, urllib.error.HTTPError) and exc.code == 429:
                raise RuntimeError("daily rate budget exhausted; resume later") from exc
            if attempt == retries - 1:
                raise
            time.sleep(delay)
            delay *= 2
    raise RuntimeError("unreachable")


def _count(concept: str, lo: str, hi: str) -> int:
    q = urllib.parse.urlencode(
        {"filter": _filter(concept, lo, hi), "per-page": 1, "select": "id"}, safe=":,*"
    )
    meta = fetch_json(f"{API}?{q}").get("meta", {})
    return int(meta["count"]) if isinstance(meta, dict) else 0


def _filter(concept: str, lo: str, hi: str) -> str:
    return f"concepts.id:{concept},from_publication_date:{lo},to_publication_date:{hi}"


def slices(concept: str, first_year: int, last_year: int, cap: int = 9000) -> list[tuple[str, str]]:
    """Date ranges holding at most `cap` works each (basic paging stops at 10000 results)."""
    out: list[tuple[str, str]] = []

    def split(lo: datetime.date, hi: datetime.date) -> None:
        n = _count(concept, lo.isoformat(), hi.isoformat())
        if n == 0:
            return
        if n > cap and hi > lo:
            mid = lo + (hi - lo) // 2
            split(lo, mid)
            split(mid + datetime.timedelta(days=1), hi)
        else:
            out.append((lo.isoformat(), hi.isoformat()))

    for y in range(first_year, last_year + 1):
        split(datetime.date(y, 1, 1), datetime.date(y, 12, 31))
    return out


def crawl(concept: str, out: Path, first_year: int = 1900, last_year: int = 2026,
          per_page: int = 200, max_bytes: int = 2 * 1024**3) -> int:
    """Download every slice with basic page= paging; return the number of pages stored.

    Cursor paging past the first page needs an API key, which this crawl does not have, so
    the field is cut into date ranges small enough for basic paging. A finished page is a file
    `slice-<lo>_<hi>-pNN.json.gz`; a rerun skips the files that exist.
    """
    out.mkdir(parents=True, exist_ok=True)
    plan_path = out / "slices.json"
    if plan_path.exists():
        plan = [tuple(x) for x in json.loads(plan_path.read_text())]
    else:
        plan = slices(concept, first_year, last_year)
        plan_path.write_text(json.dumps(plan))
    stored = 0
    for lo, hi in plan:
        page = 1
        while True:
            f = out / f"slice-{lo}_{hi}-p{page:02d}.json.gz"
            if not f.exists():
                used = sum(p.stat().st_size for p in out.glob("slice-*.json.gz"))
                if used > max_bytes:
                    print("size cap reached")
                    return stored
                query = urllib.parse.urlencode(
                    {"filter": _filter(concept, lo, hi), "select": SELECT,
                     "per-page": per_page, "page": page}, safe=":,*")
                body = fetch_json(f"{API}?{query}")
                results = body.get("results", [])
                if not isinstance(results, list) or not results:
                    break
                with gzip.open(f, "wt") as fh:
                    json.dump(body, fh)
                stored += 1
                if len(results) < per_page:
                    break
            page += 1
        print(lo, hi, "pages", page)
    return stored


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--concept", required=True, help="OpenAlex concept id, e.g. C34947359")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--max-bytes", type=int, default=2 * 1024**3)
    args = ap.parse_args()
    n = crawl(args.concept, args.out.expanduser(), max_bytes=args.max_bytes)
    print(f"{n} pages in {args.out}")


if __name__ == "__main__":
    main()
