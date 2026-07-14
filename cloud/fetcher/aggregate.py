"""Broad public aggregation + evidence ranking for the cloud fetcher (BUILD-SPEC §16).

"Dumb outside / smart inside": this does the broad public gather; the personalization against
private notes stays in the sealed core. Here we:
  * query each requested source (default: all of them),
  * de-duplicate by DOI (then by normalized title),
  * bias the ordering toward systematic reviews / meta-analyses / guidelines,
  * flag preprints as not-yet-vetted,
  * drop records with no resolvable identifier (honesty: a citation must resolve, §III.1).

Pure function of (criteria, fetch) so it is unit-testable with a fake fetch. The result dict
is exactly what gets written to S3 `results/<id>.json` and read back by the core.

The EMBED-tail keys `open_access` + `full_text` (bp-029) ride through untouched — each paper is
its source's normalized record, and dedup keeps the whole record — so the core reads the fetched
open-access full text back via `Paper.from_dict` without any change here.
"""

from __future__ import annotations

from collections.abc import Callable

from sources import SOURCES, Fetch

# Ordering bias (cloud-side, coarse). The core re-ranks with private-corpus relevance; this
# just makes the returned list well-ordered on evidence quality even before personalization.
_EVIDENCE_RANK = {
    "systematic-review": 0, "meta-analysis": 0, "guideline": 1, "review": 1,
    "randomized-controlled-trial": 2, "clinical-trial": 3,
    "journal-article": 5, "preprint": 9,
}
_DEFAULT_RANK = 6


def _evidence_rank(paper: dict) -> int:
    if paper.get("is_preprint"):
        return _EVIDENCE_RANK["preprint"]
    return _EVIDENCE_RANK.get(str(paper.get("type", "")), _DEFAULT_RANK)


def _dedup_key(paper: dict) -> str:
    doi = (paper.get("doi") or "").strip().lower()
    if doi:
        return f"doi:{doi}"
    return "title:" + " ".join(str(paper.get("title", "")).lower().split())


def _resolvable(paper: dict) -> bool:
    # A citation that can't resolve is a failure (§III.1). Require a DOI or a canonical URL.
    return bool((paper.get("doi") or "").strip() or (paper.get("url") or "").strip())


def aggregate(
    criteria: dict,
    fetch: Fetch,
    *,
    sources: list[str] | None = None,
    source_table: dict[str, Callable[[dict, Fetch], list[dict]]] | None = None,
) -> dict:
    """Gather, de-dup, evidence-rank. Returns the results payload for S3 `results/`."""
    table = source_table or SOURCES
    chosen = sources or list(table)
    max_results = int(criteria.get("filters", {}).get("max_results", 50))

    gathered: list[dict] = []
    queried: list[str] = []
    for name in chosen:
        client = table.get(name)
        if client is None:
            continue
        try:
            gathered.extend(client(criteria, fetch))
            queried.append(name)
        except Exception:  # noqa: BLE001 — one flaky source must not fail the whole gather
            continue       # the bridge/core sees whatever sources did answer

    # De-duplicate, preferring the higher-evidence record when two sources return the same work.
    best: dict[str, dict] = {}
    for paper in gathered:
        if not _resolvable(paper):
            continue
        key = _dedup_key(paper)
        if key not in best or _evidence_rank(paper) < _evidence_rank(best[key]):
            best[key] = paper

    papers = sorted(
        best.values(),
        key=lambda p: (_evidence_rank(p), -(p.get("year") or 0), str(p.get("title", ""))),
    )[:max_results]

    return {
        "criteria_id": criteria.get("id", ""),
        "papers": papers,
        "sources_queried": queried,
    }
