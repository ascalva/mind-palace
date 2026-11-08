"""What every corpus reader shares: a polite fetcher and the reductions to the landing form.

The fetcher holds one connection's worth of manners: a minimum interval between requests (the
source's own limit), a generic User-Agent that names the tool and no person, gzip, a bounded
number of retries with exponential backoff on a timeout, a 429 or a 5xx, and a server's
`Retry-After` honoured. The reductions turn markup into prose: HTML (Stack Exchange) and wikitext
(Wikipedia) into paragraphs of plain text, the identifiers the markup carries kept beside.
"""

from __future__ import annotations

import gzip
import html
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import zlib
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

USER_AGENT = "mind-palace-corpus/1.0 (open research corpus reader)"


class FetchError(RuntimeError):
    """A request that failed after its retries, or a source that refused it."""


class Fetcher:
    """GET with manners: at least `interval` seconds between requests, retries with backoff."""

    def __init__(self, interval: float, *, timeout: float = 120.0, retries: int = 6) -> None:
        self.interval = interval
        self.timeout = timeout
        self.retries = retries
        self._last = 0.0
        self.requests = 0

    def _wait(self) -> None:
        gap = self.interval - (time.monotonic() - self._last)
        if gap > 0:
            time.sleep(gap)
        self._last = time.monotonic()

    def get(self, url: str, params: dict[str, Any] | None = None) -> bytes:
        if params:
            url = f"{url}?{urllib.parse.urlencode(params, safe=':,|/*')}"
        delay = max(2.0, self.interval)
        for attempt in range(self.retries):
            self._wait()
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT,
                                                       "Accept-Encoding": "gzip"})
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    body = resp.read()
                    enc = resp.headers.get("Content-Encoding", "")
                self.requests += 1
                if enc == "gzip":
                    body = gzip.decompress(body)
                elif enc == "deflate":
                    body = zlib.decompress(body)
                return body
            except urllib.error.HTTPError as e:
                if e.code not in (429, 500, 502, 503, 504) or attempt == self.retries - 1:
                    raise FetchError(f"GET {url[:160]}: HTTP {e.code}") from e
                after = e.headers.get("Retry-After", "") if e.headers else ""
                wait = float(after) if after.strip().isdigit() else delay
                time.sleep(min(max(wait, delay), 600.0))
            except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
                if attempt == self.retries - 1:
                    raise FetchError(f"GET {url[:160]}: {e}") from e
                time.sleep(delay)
            delay = min(delay * 2, 300.0)
        raise FetchError(f"GET {url[:160]}: retries exhausted")

    def get_json(self, url: str, params: dict[str, Any] | None = None) -> Any:
        return json.loads(self.get(url, params))

    def download(self, url: str, dest: Path, *, chunk: int = 1 << 20) -> int:
        """Stream a file to `dest`, resuming a partial download by a byte range."""
        part = dest.with_name(dest.name + ".part")
        have = part.stat().st_size if part.exists() else 0
        if dest.exists():
            return dest.stat().st_size
        for attempt in range(self.retries):
            self._wait()
            headers = {"User-Agent": USER_AGENT}
            if have:
                headers["Range"] = f"bytes={have}-"
            req = urllib.request.Request(url, headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp, \
                        part.open("ab" if have and resp.status == 206 else "wb") as fh:
                    if resp.status != 206:
                        have = 0
                    while True:
                        buf = resp.read(chunk)
                        if not buf:
                            break
                        fh.write(buf)
                        have += len(buf)
                part.replace(dest)
                self.requests += 1
                return have
            except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
                if attempt == self.retries - 1:
                    raise FetchError(f"download {url}: {e}") from e
                time.sleep(min(2.0 * 2 ** attempt, 120.0))
                have = part.stat().st_size if part.exists() else 0
        raise FetchError(f"download {url}: retries exhausted")


def write_state(path: Path, state: dict[str, Any]) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(path)


def read_state(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


# ── plain text ──────────────────────────────────────────────────────────────────────────────────

_WS = re.compile(r"[ \t ]+")
_BLANKS = re.compile(r"\n{3,}")


def tidy(text: str) -> str:
    """Spaces collapsed, lines stripped, at most one blank line between paragraphs."""
    lines = [_WS.sub(" ", ln).strip() for ln in text.replace("\r", "").split("\n")]
    return _BLANKS.sub("\n\n", "\n".join(lines)).strip()


class _HTMLText(HTMLParser):
    """HTML to paragraphs: block elements break, `<pre>` keeps its lines, links are collected."""

    BLOCKS = frozenset({"p", "div", "br", "li", "ul", "ol", "pre", "blockquote", "h1", "h2", "h3",
                        "h4", "h5", "h6", "tr", "table", "hr"})

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.out: list[str] = []
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self.BLOCKS:
            self.out.append("\n")
        if tag == "li":
            self.out.append("- ")
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.links.append(href)

    def handle_endtag(self, tag: str) -> None:
        if tag in self.BLOCKS:
            self.out.append("\n")

    def handle_data(self, data: str) -> None:
        self.out.append(data)


def html_text(markup: str) -> tuple[str, list[str]]:
    """Prose and the hrefs of an HTML fragment."""
    p = _HTMLText()
    p.feed(markup)
    p.close()
    return tidy("".join(p.out)), p.links


# ── wikitext ────────────────────────────────────────────────────────────────────────────────────

_COMMENT = re.compile(r"<!--.*?-->", re.S)
_REF = re.compile(r"<ref[^>/]*?/>|<ref[^>]*>.*?</ref>", re.S | re.I)
_TAGS_DROP = re.compile(r"<(gallery|math|chem|score|timeline|syntaxhighlight|source|imagemap|"
                        r"mapframe|graph)[^>]*>.*?</\1>", re.S | re.I)
_HTML_TAG = re.compile(r"</?[a-zA-Z][^>]*>")
_TABLE = re.compile(r"^\{\|.*?^\|\}", re.S | re.M)
_EXT_LINK = re.compile(r"\[(?:https?:)?//[^\s\]]+\s+([^\]]+)\]")
_BARE_EXT = re.compile(r"\[(?:https?:)?//[^\s\]]+\]")
_HEADING = re.compile(r"^(=+)\s*(.*?)\s*\1\s*$", re.M)
_QUOTES = re.compile(r"'{2,5}")
_FILE_NS = ("file:", "image:", "media:", "category:")
_SKIP_NS = ("file:", "image:", "media:", "category:", "wikipedia:", "wp:", "help:", "template:",
            "portal:", "special:", "user:", "talk:", "draft:", "module:", "mediawiki:", "book:",
            "wikt:", "wiktionary:", "s:", "q:", "commons:", "meta:", "species:", "d:", ":")
_SECTIONS_END = re.compile(r"^==\s*(References|Notes|Footnotes|Citations|Sources|Bibliography|"
                           r"Further reading|External links|See also)\s*==\s*$", re.M | re.I)


def _templates(text: str) -> list[tuple[int, int]]:
    """The outermost `{{…}}` spans of a text, nesting respected."""
    spans, depth, start, i = [], 0, 0, 0
    n = len(text)
    while i < n - 1:
        two = text[i:i + 2]
        if two == "{{":
            if depth == 0:
                start = i
            depth += 1
            i += 2
            continue
        if two == "}}" and depth:
            depth -= 1
            i += 2
            if depth == 0:
                spans.append((start, i))
            continue
        i += 1
    return spans


def _links(text: str) -> list[tuple[int, int, str, str]]:
    """The `[[target|label]]` links of a text, nesting (a file's caption) respected:
    (start, end, target, label)."""
    out: list[tuple[int, int, str, str]] = []
    i, n = 0, len(text)
    while True:
        i = text.find("[[", i)
        if i < 0 or i >= n:
            return out
        depth, j = 0, i
        while j < n - 1:
            if text[j:j + 2] == "[[":
                depth += 1
                j += 2
            elif text[j:j + 2] == "]]":
                depth -= 1
                j += 2
                if depth == 0:
                    break
            else:
                j += 1
        inner = text[i + 2:j - 2]
        target, _, label = inner.partition("|")
        out.append((i, j, target.strip(), (label or target).strip()))
        i = j


_CITE_FIELD = re.compile(r"\|\s*(doi|arxiv|eprint|title|isbn|url)\s*=\s*([^|}]*)", re.I)
_GUTENBERG = re.compile(r"\{\{\s*gutenberg(?:\s+author)?\s*\|[^}]*?\bno\s*=\s*(\d+)", re.I)


def wikitext(text: str) -> dict[str, Any]:
    """A page's wikitext reduced: its prose (the body before the reference sections, markup
    removed), the article links it makes, the citations it carries (DOI, arXiv id, title), the
    Project Gutenberg ebooks it names, and whether it is a disambiguation or a redirect."""
    redirect = text.lstrip()[:9].lower() == "#redirect"
    cites: list[dict[str, str]] = []
    for a, b in _templates(text):
        t = text[a:b]
        head = t[2:40].strip().lower()
        if head.startswith(("cite", "citation")):
            fields = {k.lower(): v.strip() for k, v in _CITE_FIELD.findall(t)}
            keep = {k: fields[k] for k in ("doi", "arxiv", "eprint", "title") if fields.get(k)}
            if keep:
                cites.append(keep)
    gutenberg = sorted({int(n) for n in _GUTENBERG.findall(text)})
    disamb = bool(re.search(r"\{\{\s*(disambiguation|disambig|dab|hndis|set index)", text, re.I))
    body = text
    m = _SECTIONS_END.search(body)
    if m:
        body = body[:m.start()]
    body = _COMMENT.sub("", body)
    body = _REF.sub("", body)
    body = _TAGS_DROP.sub("", body)
    for a, b in reversed(_templates(body)):
        body = body[:a] + body[b:]
    body = _TABLE.sub("", body)
    links: list[str] = []
    for a, b, target, label in reversed(_links(body)):
        low = target.lower()
        if low.startswith(_FILE_NS):
            body = body[:a] + body[b:]
            continue
        if not low.startswith(_SKIP_NS) and target:
            links.append(target.split("#", 1)[0].strip())
        body = body[:a] + label + body[b:]
    body = _EXT_LINK.sub(r"\1", body)
    body = _BARE_EXT.sub("", body)
    body = _HEADING.sub(r"\2", body)
    body = _QUOTES.sub("", body)
    body = _HTML_TAG.sub("", body)
    body = html.unescape(body)
    body = re.sub(r"^[*#:;]+\s*", "", body, flags=re.M)
    body = re.sub(r"^__\w+__$", "", body, flags=re.M)
    every = {_title(t) for t in links if t}
    return {"text": tidy(body), "links": sorted(every - {""}), "cites": cites,
            "gutenberg": gutenberg, "disambiguation": disamb, "redirect": redirect}


def _title(t: str) -> str:
    """A link target as a page title: underscores as spaces, the first letter upper."""
    t = t.replace("_", " ").strip()
    return (t[:1].upper() + t[1:]) if t else ""
