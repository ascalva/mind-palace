"""Hacker News through its official API: threads, each story with its whole reply tree.

    python -m edge.corpus.hackernews --out <root>/hackernews --budget-mb 120
    python -m edge.corpus.hackernews --out <root>/hackernews --budget-mb 120 \
        --spread 2012-01-01 2024-12-31

The official API (`hacker-news.firebaseio.com/v0`, documented at github.com/HackerNews/API) serves
one item a request and states no rate limit; this reader keeps to `--rate` requests a second over
a few persistent connections. By default it walks item ids down from `maxitem` a block at a time
and fetches every item of the block. Comments always have larger ids than their story, so once the
walk has passed a story every comment it had is in hand: each story of the block becomes a thread
at once. With `--spread` it samples instead: item ids are drawn uniformly at random in the window's
id range (found by binary search on item time), and a draw that is a live story takes the story
with its whole reply tree, fetched through each item's `kids`; any other draw is dropped, so the
sample is uniform over the window's stories, not weighted by thread size. Both modes write one
stream, and the budget counts every item in it.

A thread is one item (dn-corpus-instance §4.1: the thread is the item and each comment a block):
the story's title, its link's host, its text, then each comment in the order of the reply tree,
a paragraph each, markup removed; dead and deleted items are left out, and no username is kept.
Its metadata carry the story's date, link and host, the counts, the reply tree (each comment's
parent and time) and the Wikipedia, arXiv and DOI links in the story and its comments. The content
carries no open licence: it is read and held locally for this instance's measurements and never
republished; only aggregate measurements leave the instance.
"""

from __future__ import annotations

import argparse
import calendar
import gzip
import http.client
import json
import random
import threading
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from edge.corpus.common import USER_AGENT, html_text, read_state, write_state
from edge.corpus.stackexchange import classify_links
from edge.corpus.stream import StreamWriter

HOST = "hacker-news.firebaseio.com"


class Client:
    """Requests over one persistent connection a thread, at most `rate` a second in all."""

    def __init__(self, rate: float) -> None:
        self.rate = rate
        self._local = threading.local()
        self._lock = threading.Lock()
        self._next = time.monotonic()
        self.requests = 0

    def _conn(self) -> http.client.HTTPSConnection:
        c = getattr(self._local, "conn", None)
        if c is None:
            c = http.client.HTTPSConnection(HOST, timeout=30)
            self._local.conn = c
        return c

    def _pace(self) -> None:
        with self._lock:
            now = time.monotonic()
            wait = self._next - now
            self._next = max(now, self._next) + 1.0 / self.rate
            self.requests += 1
        if wait > 0:
            time.sleep(wait)

    def get(self, path: str) -> Any:
        for attempt in range(6):
            self._pace()
            try:
                c = self._conn()
                c.request("GET", f"/v0/{path}", headers={"User-Agent": USER_AGENT})
                resp = c.getresponse()
                body = resp.read()
                if resp.status == 200:
                    return json.loads(body)
                if resp.status in (429, 500, 502, 503, 504):
                    time.sleep(2.0 * 2 ** attempt)
                    continue
                return None
            except (OSError, http.client.HTTPException, ValueError):
                self._local.conn = None
                time.sleep(1.0 * 2 ** attempt)
        return None


def thread_of(story: dict[str, Any], comments: dict[int, dict[str, Any]]
              ) -> tuple[str, dict[str, Any]]:
    """A story's thread: its content (title, host, text, then each comment in reply-tree order)
    and its metadata (date, link, counts, the reply tree, the links it makes)."""
    title = str(story.get("title") or "").strip()
    url = str(story.get("url") or "")
    host = urllib.parse.urlparse(url).netloc.lower().removeprefix("www.") if url else ""
    parts = [title + (f"\n({host})" if host else "")]
    hrefs = [url] if url else []
    if story.get("text"):
        body, links = html_text(str(story["text"]))
        parts.append(body)
        hrefs += links
    replies: list[list[int]] = []
    order: list[int] = []
    stack = list(reversed([k for k in story.get("kids") or [] if k in comments]))
    while stack:
        cid = stack.pop()
        order.append(cid)
        stack.extend(reversed([k for k in comments[cid].get("kids") or [] if k in comments]))
    for cid in order:
        c = comments[cid]
        body, links = html_text(str(c.get("text") or ""))
        if body:
            parts.append(body)
        hrefs += links
        replies.append([cid, int(c.get("parent") or 0), int(c.get("time") or 0)])
    meta = {"date": time.strftime("%Y-%m-%d", time.gmtime(int(story.get("time") or 0))),
            "time": int(story.get("time") or 0), "url": url, "host": host,
            "score": int(story.get("score") or 0), "comments": len(order),
            "replies": replies, "links": classify_links(hrefs)}
    return "\n\n".join(p for p in parts if p), meta


def run(out: Path, budget: int, *, rate: float, workers: int, block: int) -> None:
    client = Client(rate)
    w = StreamWriter(out)
    raw = out / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    state_path = out / "state.json"
    state = read_state(state_path)
    top = int(state.get("top") or client.get("maxitem.json") or 0)
    low = int(state.get("low", top + 1))
    state["top"] = top
    # comments of stories below the walk wait here; their story is reached later
    pending: dict[int, dict[str, Any]] = {}
    for f in sorted(raw.glob("block-*.jsonl.gz")):
        with gzip.open(f, "rt", encoding="utf-8") as fh:
            for line in fh:
                it = json.loads(line)
                if it.get("type") == "comment":
                    pending[int(it["id"])] = it
    try:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            while w.text_bytes < budget and low > 1:
                hi, lo = low - 1, max(1, low - block)
                items = [it for it in pool.map(lambda i: client.get(f"item/{i}.json"),
                                               range(hi, lo - 1, -1)) if it]
                live = [it for it in items if not it.get("dead") and not it.get("deleted")]
                f = raw / f"block-{lo:09d}.jsonl.gz"
                with gzip.open(f, "wt", encoding="utf-8") as fh:
                    for it in live:
                        if it.get("type") == "comment":
                            fh.write(json.dumps(it) + "\n")
                stories = [it for it in live if it.get("type") == "story"]
                for it in live:
                    if it.get("type") == "comment":
                        pending[int(it["id"])] = it
                for s in sorted(stories, key=lambda x: -int(x["id"])):
                    sid = int(s["id"])
                    tree: dict[int, dict[str, Any]] = {}
                    stack = [k for k in s.get("kids") or []]
                    while stack:
                        k = stack.pop()
                        c = pending.pop(k, None)
                        if c is None:
                            continue
                        tree[k] = c
                        stack.extend(c.get("kids") or [])
                    item_id = f"hn-{sid}"
                    if w.has(item_id) or not s.get("title"):
                        continue
                    content, meta = thread_of(s, tree)
                    w.append(item_id, str(s["title"]), content, meta=meta)
                    if w.text_bytes >= budget:
                        break
                low = lo
                state["low"] = low
                w.close_part()
                write_state(state_path, state)
                print(f"hackernews: ids down to {low}, {len(w.ids)} threads, "
                      f"{w.text_bytes / 1e6:.1f} MB, {client.requests} requests", flush=True)
    finally:
        w.close()
        state["done"] = w.text_bytes >= budget
        write_state(state_path, state)
    print(f"hackernews: {len(w.ids)} threads, {w.text_bytes / 1e6:.1f} MB, "
          f"{client.requests} requests")


def _live(it: Any) -> bool:
    return isinstance(it, dict) and not it.get("dead") and not it.get("deleted")


def _epoch(day: str) -> int:
    return calendar.timegm(time.strptime(day, "%Y-%m-%d"))


def _time_from(client: Any, i: int, top: int, tries: int = 64) -> int | None:
    """The time of the first item at or after id `i` that has one (an id can be empty)."""
    for j in range(i, min(top, i + tries - 1) + 1):
        it = client.get(f"item/{j}.json")
        if isinstance(it, dict) and it.get("time"):
            return int(it["time"])
    return None


def id_at(client: Any, when: int, top: int) -> int:
    """The first item id whose time is at or after `when`: a binary search over [1, top], item
    ids growing with time."""
    lo, hi = 1, top
    while lo < hi:
        mid = (lo + hi) // 2
        t = _time_from(client, mid, top)
        if t is None or t >= when:
            hi = mid
        else:
            lo = mid + 1
    return lo


def _trees(pool: ThreadPoolExecutor, client: Any, stories: dict[int, dict[str, Any]]
           ) -> dict[int, dict[int, dict[str, Any]]]:
    """Each story's live comments, breadth first through `kids`; a dead or deleted comment is
    left out with its replies, as the walk leaves them out."""
    trees: dict[int, dict[int, dict[str, Any]]] = {sid: {} for sid in stories}
    frontier = [(sid, int(k)) for sid, st in stories.items() for k in st.get("kids") or []]
    while frontier:
        got = list(pool.map(lambda p: client.get(f"item/{p[1]}.json"), frontier))
        nxt: list[tuple[int, int]] = []
        for (sid, k), it in zip(frontier, got, strict=True):
            if _live(it) and it.get("type") == "comment" and k not in trees[sid]:
                trees[sid][k] = it
                nxt += [(sid, int(kk)) for kk in it.get("kids") or []]
        frontier = nxt
    return trees


def spread(out: Path, budget: int, *, start: str, end: str, rate: float, workers: int,
           draws: int = 2000, seed: int = 0, max_draws: int | None = None,
           client: Any = None) -> None:
    """Threads sampled uniformly among the stories of [start, end] (see the module's docstring),
    `draws` ids a round, until the budget is spent or `max_draws` ids are drawn (by default four
    times the window's ids, which a window too small for the budget reaches); resumable, the
    seeded draws replayed past the ones already made."""
    client = client if client is not None else Client(rate)
    w = StreamWriter(out)
    state_path = out / "state.json"
    state = read_state(state_path)
    sp = state.setdefault("spread", {"start": start, "end": end, "seed": seed, "drawn": 0})
    if (sp["start"], sp["end"], sp["seed"]) != (start, end, seed):
        w.close()
        raise SystemExit("refusing: this stream's spread sample was drawn with other parameters")
    if "lo" not in sp:
        top = int(client.get("maxitem.json") or 0)
        sp["lo"] = id_at(client, _epoch(start), top)
        sp["hi"] = id_at(client, _epoch(end) + 86400, top)
        write_state(state_path, state)
    lo, hi = int(sp["lo"]), int(sp["hi"])
    limit = max_draws if max_draws is not None else 4 * (hi - lo)
    rng = random.Random(seed)
    for _ in range(int(sp["drawn"])):
        rng.randrange(lo, hi)
    try:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            while w.text_bytes < budget and hi > lo and int(sp["drawn"]) < limit:
                ids = [rng.randrange(lo, hi) for _ in range(draws)]
                got = list(pool.map(lambda i: client.get(f"item/{i}.json"), ids))
                stories = {int(it["id"]): it for it in got
                           if _live(it) and it.get("type") == "story" and it.get("title")
                           and not w.has(f"hn-{int(it['id'])}")}
                trees = _trees(pool, client, stories)
                for sid in sorted(stories):
                    content, meta = thread_of(stories[sid], trees[sid])
                    w.append(f"hn-{sid}", str(stories[sid]["title"]), content, meta=meta)
                    if w.text_bytes >= budget:
                        break
                sp["drawn"] = int(sp["drawn"]) + draws
                w.close_part()
                write_state(state_path, state)
                print(f"hackernews: {sp['drawn']} ids drawn in [{lo}, {hi}), {len(w.ids)} threads, "
                      f"{w.text_bytes / 1e6:.1f} MB, {getattr(client, 'requests', 0)} requests",
                      flush=True)
    finally:
        w.close()
        sp["done"] = w.text_bytes >= budget
        write_state(state_path, state)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--budget-mb", type=float, default=120.0)
    ap.add_argument("--rate", type=float, default=80.0, help="requests a second, in all")
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--block", type=int, default=20000)
    ap.add_argument("--spread", nargs=2, metavar=("START", "END"), default=None,
                    help="sample the stories of these dates (YYYY-MM-DD) instead of walking")
    ap.add_argument("--draws", type=int, default=2000, help="ids drawn a round (--spread)")
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    if a.spread:
        spread(a.out, int(a.budget_mb * 1e6), start=a.spread[0], end=a.spread[1], rate=a.rate,
               workers=a.workers, draws=a.draws, seed=a.seed)
    else:
        run(a.out, int(a.budget_mb * 1e6), rate=a.rate, workers=a.workers, block=a.block)


if __name__ == "__main__":
    main()
