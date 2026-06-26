"""Public-literature source clients for the cloud fetcher (BUILD-SPEC §16).

Runs in AWS Lambda (Zone C), OUTSIDE the sealed core. It sees only **de-identified criteria**
and queries **key-free public APIs** (OpenAlex, Europe PMC, arXiv). It never sees private data.

Stdlib only (`urllib`, `xml`, `json`) so the Lambda zip is dependency-free. The HTTP `fetch`
callable is injected so the aggregation logic is unit-testable without network access.

Each client normalizes to a common record:
    {source, id, title, abstract, year, venue, type, doi, url, is_preprint}
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections.abc import Callable

Fetch = Callable[[str], bytes]

DEFAULT_TIMEOUT_S = 15

# Normalize source publication-type strings to our small evidence vocabulary (matches
# core/research/criteria.ALLOWED_PUBLICATION_TYPES and core/research/rank tiers).
_TYPE_MAP = {
    "systematic review": "systematic-review",
    "meta-analysis": "meta-analysis",
    "meta analysis": "meta-analysis",
    "review": "review",
    "review-article": "review",
    "journal-article": "journal-article",
    "research-article": "journal-article",
    "randomized controlled trial": "randomized-controlled-trial",
    "clinical trial": "clinical-trial",
    "guideline": "guideline",
    "preprint": "preprint",
}


def http_fetch(url: str, *, timeout: int = DEFAULT_TIMEOUT_S) -> bytes:
    """Real network fetch (used only in the Lambda). A generic UA, no owner identifier."""
    req = urllib.request.Request(url, headers={"User-Agent": "mind-palace-research/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 (https public APIs)
        return resp.read()


def _norm_type(raw: str) -> str:
    return _TYPE_MAP.get(raw.strip().lower(), raw.strip().lower())


def _query_string(terms: list[str]) -> str:
    return " ".join(terms).strip()


# --- OpenAlex ---------------------------------------------------------------------------
def openalex(criteria: dict, fetch: Fetch) -> list[dict]:
    terms = criteria.get("terms", [])
    filters = criteria.get("filters", {})
    params = {"search": _query_string(terms), "per-page": min(filters.get("max_results", 50), 100)}
    if filters.get("from_year"):
        params["filter"] = f"from_publication_date:{int(filters['from_year'])}-01-01"
    url = "https://api.openalex.org/works?" + urllib.parse.urlencode(params)
    data = json.loads(fetch(url))
    out: list[dict] = []
    for w in data.get("results", []):
        out.append({
            "source": "openalex",
            "id": str(w.get("id", "")),
            "title": w.get("display_name") or w.get("title") or "",
            "abstract": _openalex_abstract(w.get("abstract_inverted_index")),
            "year": w.get("publication_year"),
            "venue": _openalex_venue(w),
            "type": _norm_type(str(w.get("type", ""))),
            "doi": (w.get("doi") or "").replace("https://doi.org/", ""),
            "url": w.get("id", "") or (w.get("doi") or ""),
            "is_preprint": str(w.get("type", "")).lower() == "preprint",
        })
    return out


def _openalex_abstract(inverted: dict | None) -> str:
    """OpenAlex returns abstracts as an inverted index {word: [positions]}; reconstruct it."""
    if not inverted:
        return ""
    positions: list[tuple[int, str]] = []
    for word, idxs in inverted.items():
        for i in idxs:
            positions.append((i, word))
    positions.sort()
    return " ".join(word for _, word in positions)


def _openalex_venue(work: dict) -> str:
    loc = work.get("primary_location") or {}
    src = loc.get("source") or {}
    return src.get("display_name") or ""


# --- Europe PMC -------------------------------------------------------------------------
def europepmc(criteria: dict, fetch: Fetch) -> list[dict]:
    terms = criteria.get("terms", [])
    filters = criteria.get("filters", {})
    query = _query_string(terms)
    if filters.get("from_year"):
        query += f" AND (FIRST_PDATE:[{int(filters['from_year'])}-01-01 TO 3000-12-31])"
    params = {
        "query": query,
        "format": "json",
        "resultType": "core",
        "pageSize": min(filters.get("max_results", 50), 100),
    }
    base = "https://www.ebi.ac.uk/europepmc/webservices/rest/search?"
    data = json.loads(fetch(base + urllib.parse.urlencode(params)))
    out: list[dict] = []
    for r in data.get("resultList", {}).get("result", []):
        pubtype = str(r.get("pubType", "")).lower()
        is_preprint = (r.get("source") == "PPR") or ("preprint" in pubtype)
        pmid = r.get("pmid") or r.get("id") or ""
        out.append({
            "source": "europepmc",
            "id": str(pmid),
            "title": r.get("title", ""),
            "abstract": r.get("abstractText", ""),
            "year": int(r["pubYear"]) if str(r.get("pubYear", "")).isdigit() else None,
            "venue": r.get("journalTitle", "") or r.get("bookOrReportDetails", ""),
            "type": _norm_type(str(r.get("pubType", "")).split(";")[0]),
            "doi": r.get("doi", ""),
            "url": (f"https://doi.org/{r['doi']}" if r.get("doi")
                    else f"https://europepmc.org/article/{r.get('source', 'MED')}/{pmid}"),
            "is_preprint": is_preprint,
        })
    return out


# --- arXiv (preprints) ------------------------------------------------------------------
_ATOM = "{http://www.w3.org/2005/Atom}"


def arxiv(criteria: dict, fetch: Fetch) -> list[dict]:
    terms = criteria.get("terms", [])
    filters = criteria.get("filters", {})
    query = " ".join(f'all:"{t}"' if " " in t else f"all:{t}" for t in terms)
    params = {"search_query": query, "max_results": min(filters.get("max_results", 50), 100)}
    url = "http://export.arxiv.org/api/query?" + urllib.parse.urlencode(params)
    root = ET.fromstring(fetch(url))
    out: list[dict] = []
    for entry in root.findall(f"{_ATOM}entry"):
        published = entry.findtext(f"{_ATOM}published", default="")
        arxiv_url = entry.findtext(f"{_ATOM}id", default="")
        out.append({
            "source": "arxiv",
            "id": arxiv_url.rsplit("/", 1)[-1],
            "title": " ".join((entry.findtext(f"{_ATOM}title") or "").split()),
            "abstract": " ".join((entry.findtext(f"{_ATOM}summary") or "").split()),
            "year": int(published[:4]) if published[:4].isdigit() else None,
            "venue": "arXiv",
            "type": "preprint",
            "doi": entry.findtext(f"{_ATOM}{{http://arxiv.org/schemas/atom}}doi", default=""),
            "url": arxiv_url,
            "is_preprint": True,   # arXiv is always not-yet-vetted (§16)
        })
    return out


SOURCES: dict[str, Callable[[dict, Fetch], list[dict]]] = {
    "openalex": openalex,
    "europepmc": europepmc,
    "arxiv": arxiv,
}
