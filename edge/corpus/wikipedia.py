"""Wikipedia, English, current article prose: a link-connected sample grown from seed articles.

    python -m edge.corpus.wikipedia --out <root>/wikipedia --budget-mb 398

The sample is a snowball over the article link graph: from the seeds, the next articles fetched
are the ones the articles already taken link to most, fifty at a time through the MediaWiki API
(`action=query`, `prop=revisions`, the current wikitext), so the sample's hyperlink graph is dense
enough to have cores. Each article is reduced to its prose before the reference sections, its
title prepended; its links, citations (DOI, arXiv id, title) and Project Gutenberg templates go to
the metadata. Redirects are followed, disambiguation pages and stubs under `--min-chars` skipped.

A page's creation is not in the current revision; page ids are allocated in creation order, so
after the crawl the first revision's time is read for `--anchors` page ids spread over the
sample's range, and every page's creation is interpolated from its id (`meta/created.json`).

Manners: one request at a time, at least one second apart, `maxlag=5`, a generic User-Agent
naming the tool; the text is CC BY-SA 4.0 and GFDL, read and held locally, never republished.
"""

from __future__ import annotations

import argparse
import bisect
import heapq
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from edge.corpus.common import Fetcher, FetchError, read_state, wikitext, write_state
from edge.corpus.stream import StreamWriter

API = "https://en.wikipedia.org/w/api.php"
SEEDS = (
    "Network science", "Complex network", "Graph theory", "Scale-free network",
    "Small-world network", "Random graph", "Social network analysis", "Percolation theory",
    "Statistical mechanics", "Computational complexity theory", "Algorithm", "Machine learning",
    "Graph neural network", "Opinion dynamics", "Evolutionary game theory", "Epidemic model",
    "Community structure", "Centrality", "Spectral graph theory", "Markov chain",
)


def _query(f: Fetcher, titles: list[str]) -> dict[str, Any]:
    return f.get_json(API, {
        "action": "query", "format": "json", "formatversion": "2", "prop": "revisions",
        "rvprop": "content|ids|timestamp", "rvslots": "main", "redirects": "1", "maxlag": "5",
        "titles": "|".join(titles)})


def crawl(out: Path, budget: int, *, min_chars: int, interval: float) -> None:
    f = Fetcher(interval)
    w = StreamWriter(out)
    state_path = out / "state.json"
    state = read_state(state_path)
    tried: set[str] = set(state.get("tried", []))
    votes: Counter[str] = Counter(state.get("votes", {}))
    taken_titles: set[str] = set(state.get("taken", []))
    queue = list(SEEDS) if not state else []
    try:
        while w.text_bytes < budget:
            if queue:
                batch, queue = queue[:50], queue[50:]
            else:
                # the next fifty: the most-linked-to titles not yet tried
                best = heapq.nlargest(50, ((n, t) for t, n in votes.items() if t not in tried))
                batch = [t for _, t in best]
            batch = [t for t in batch if t not in tried]
            if not batch:
                break
            tried.update(batch)
            try:
                doc = _query(f, batch)
            except FetchError as e:
                print(f"wikipedia: {e}", file=sys.stderr)
                continue
            for page in doc.get("query", {}).get("pages", []):
                if page.get("missing") or page.get("invalid") or page.get("ns", 0) != 0:
                    continue
                title = str(page["title"])
                tried.add(title)
                revs = page.get("revisions") or []
                if not revs or title in taken_titles:
                    continue
                rev = revs[0]
                red = wikitext(str(rev.get("slots", {}).get("main", {}).get("content", "")))
                if red["redirect"] or red["disambiguation"] or len(red["text"]) < min_chars:
                    continue
                pid = str(page["pageid"])
                if w.has(pid):
                    continue
                taken_titles.add(title)
                for t in red["links"]:
                    votes[t] += 1
                w.append(pid, title, f"{title}\n\n{red['text']}", meta={
                    "pageid": int(page["pageid"]), "title": title, "revid": rev.get("revid"),
                    "rev_ts": rev.get("timestamp"), "links": red["links"],
                    "cites": red["cites"], "gutenberg": red["gutenberg"]})
                if w.text_bytes >= budget:
                    break
            if f.requests % 20 == 0:
                w.close_part()
                write_state(state_path, {"tried": sorted(tried), "taken": sorted(taken_titles),
                                         "votes": dict(votes)})
                print(f"wikipedia: {len(taken_titles)} articles, "
                      f"{w.text_bytes / 1e6:.1f} MB, {f.requests} requests", flush=True)
    finally:
        w.close()
        write_state(state_path, {"tried": sorted(tried), "taken": sorted(taken_titles),
                                 "votes": dict(votes), "done": w.text_bytes >= budget})
    print(f"wikipedia: done, {len(taken_titles)} articles, {w.text_bytes / 1e6:.1f} MB")


def anchors(out: Path, n: int, *, interval: float) -> None:
    """The creation time of `n` page ids spread over the sample, and every page's interpolated."""
    ids = []
    with (out / "meta" / "items.jsonl").open(encoding="utf-8") as fh:
        for line in fh:
            ids.append(int(json.loads(line)["pageid"]))
    ids.sort()
    f = Fetcher(interval)
    path = out / "meta" / "anchors.json"
    have: dict[str, str] = json.loads(path.read_text()) if path.is_file() else {}
    picks = sorted({ids[round(i * (len(ids) - 1) / max(1, n - 1))] for i in range(n)})
    for pid in picks:
        if str(pid) in have:
            continue
        try:
            doc = f.get_json(API, {"action": "query", "format": "json", "formatversion": "2",
                                   "prop": "revisions", "pageids": str(pid), "rvdir": "newer",
                                   "rvlimit": "1", "rvprop": "timestamp", "maxlag": "5"})
        except FetchError as e:
            print(f"wikipedia anchors: {e}", file=sys.stderr)
            continue
        pages = doc.get("query", {}).get("pages", [])
        if pages and pages[0].get("revisions"):
            have[str(pid)] = str(pages[0]["revisions"][0]["timestamp"])
            path.write_text(json.dumps(have, indent=0))
    xs = sorted((int(k), v) for k, v in have.items())
    keys = [k for k, _ in xs]

    def created(pid: int) -> str:
        from datetime import datetime

        if not xs:
            return ""
        i = bisect.bisect_left(keys, pid)
        if i < len(keys) and keys[i] == pid:
            return xs[i][1][:10]
        lo, hi = xs[max(0, i - 1)], xs[min(len(xs) - 1, i)]
        if lo[0] == hi[0]:
            return lo[1][:10]
        t0 = datetime.fromisoformat(lo[1].replace("Z", "+00:00")).timestamp()
        t1 = datetime.fromisoformat(hi[1].replace("Z", "+00:00")).timestamp()
        frac = min(1.0, max(0.0, (pid - lo[0]) / (hi[0] - lo[0])))
        return datetime.fromtimestamp(t0 + frac * (t1 - t0)).date().isoformat()

    (out / "meta" / "created.json").write_text(json.dumps({str(p): created(p) for p in ids}))
    print(f"wikipedia: {len(have)} anchors, {len(ids)} creations interpolated")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--budget-mb", type=float, default=398.0)
    ap.add_argument("--min-chars", type=int, default=1500)
    ap.add_argument("--interval", type=float, default=1.0)
    ap.add_argument("--anchors", type=int, default=160)
    a = ap.parse_args()
    crawl(a.out, int(a.budget_mb * 1e6), min_chars=a.min_chars, interval=a.interval)
    anchors(a.out, a.anchors, interval=a.interval)


if __name__ == "__main__":
    main()
