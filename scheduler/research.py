"""The research driver — wire the dormant airlock into a running chain (bp-028, §16).

The pieces existed but nothing drove them: `librarian.research_criteria` (the outbound
de-identify seam), `airlock.emit/collect` (the one-way diode), and `rank_literature` (the
inside-the-walls personalization) had **zero production callers** (bp-028 §3). This module is
the missing orchestration seam:

    research_criteria(query) → airlock.emit → airlock.collect_one → rank_literature → surface

Two invariants shape it and are load-bearing here:

  * **Inv 2 / never-pollute-the-mirror.** The driver never touches the network (only the
    airlock's `requests/` file) and NEVER writes a paper into any store. Ranking is a pure read
    of the mirror; the ranked list is returned **transiently** (persistence is bp-029).
  * **Inv 11 (the corpus never crosses).** What leaves is `ResearchCriteria.to_request()` —
    de-identified topical terms only. `emit()` re-asserts cleanliness at the boundary; the
    driver constructs the outbound request ONLY via `research_criteria`/`deidentify`, never
    from raw query text.

Async reality: `emit()` writes a request that a Zone-C fetcher answers *later*. A single
invocation that emits then collects will find nothing back yet in a live deployment — it
returns `[]` gracefully (never hangs, never raises). The reading list surfaces on a later
collect, once the fetcher has responded.
"""

from __future__ import annotations

from typing import Protocol

from core.ingest.embed import Embedder
from core.research.airlock import ResearchResult
from core.research.criteria import Paper, ResearchCriteria
from core.research.rank import RankedPaper, rank_literature
from core.stores.vectorstore import VectorStore

# `"research"` is ALREADY a synthesis kind (scheduler/router.py:31) — background, trough-gated.
# Naming it here gives the foreground (interface.py) and background (cron.py) seams one source.
RESEARCH_KIND = "research"


class Airlock(Protocol):
    """The core-side airlock surface the driver needs (structural, so tests inject a fake).

    Matches `core.research.airlock.ResearchAirlock`: `emit` writes a de-identified request and
    returns the id; `collect_one` reads (and by default consumes) the keyed literature result."""

    def emit(self, criteria: ResearchCriteria) -> str: ...
    def collect_one(self, criteria_id: str, *, consume: bool = ...) -> ResearchResult | None: ...


class CriteriaProposer(Protocol):
    """The outbound de-identify seam — `Librarian.research_criteria`. The proposer only
    *suggests* terms; `deidentify()` (inside) is the enforcer that scrubs PII (Inv 3, Inv 11)."""

    def research_criteria(self, query: str, **kwargs: object) -> ResearchCriteria: ...


def criteria_from_request(request: dict[str, object]) -> ResearchCriteria:
    """Rebuild a `ResearchCriteria` from its `to_request()` wire form (the enqueue payload).

    Inverse of `ResearchCriteria.to_request()`: the foreground de-identifies at enqueue time and
    stores the de-identified dict; the background handler reconstructs it here. `emit()` will
    still `assert_clean()` on the way out, so a tampered payload cannot leak."""
    filters = request.get("filters") or {}
    assert isinstance(filters, dict)
    return ResearchCriteria(
        topic=str(request["topic"]),
        terms=tuple(request.get("terms", ())),  # type: ignore[arg-type]
        from_year=filters.get("from_year"),
        publication_types=tuple(filters.get("publication_types", ())),
        max_results=int(filters.get("max_results", 50)),
        id=str(request["id"]),
    )


def run_research(
    criteria: ResearchCriteria,
    airlock: Airlock,
    embedder: Embedder,
    store: VectorStore,
    *,
    k_notes: int = 5,
) -> list[RankedPaper]:
    """Emit a de-identified request, collect this criteria's result, rank it — transiently.

    Uses `collect_one(criteria.id)` (not `collect()`): a single-request driver must pick up
    only ITS OWN result, or it would rank another criteria's papers against the wrong query.
    Returns `[]` when no result is back yet (the fetcher is async / absent) — never raises."""
    airlock.emit(criteria)  # re-asserts clean at the outbound boundary (defense in depth)
    result = airlock.collect_one(criteria.id, consume=True)
    if result is None or not result.papers:
        return []
    return rank_literature(list(result.papers), criteria, embedder, store, k_notes=k_notes)


def research_driver(
    query: str,
    *,
    librarian: CriteriaProposer,
    airlock: Airlock,
    embedder: Embedder,
    store: VectorStore,
    k_notes: int = 5,
) -> list[RankedPaper]:
    """End-to-end from a raw query: de-identify → run. The outbound request is built ONLY via
    `research_criteria` (which runs `deidentify`), never from the raw `query` text (Inv 11)."""
    criteria = librarian.research_criteria(query)
    return run_research(criteria, airlock, embedder, store, k_notes=k_notes)


def render_ranked(ranked: list[RankedPaper], *, limit: int = 5) -> str:
    """A plain reading list for the owner — public paper titles + honesty flags, never internals.

    The papers are PUBLIC literature (not the corpus), so titles are safe to surface. Evidence
    tier and flags carry the §16 honesty signal (preprint-not-vetted, unresolved-identifier)."""
    if not ranked:
        return ("I looked, but nothing has come back from the literature search yet — "
                "I'll surface results once they're in.")
    lines = ["Here's what I found in the literature (ranked against your notes):"]
    for r in ranked[:limit]:
        p: Paper = r.paper
        tail = f" [{', '.join(r.flags)}]" if r.flags else ""
        year = f", {p.year}" if p.year else ""
        lines.append(f"- {p.title}{year} — {r.evidence_tier}-evidence{tail}")
    return "\n".join(lines)
