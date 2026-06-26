"""Rank public literature against the private corpus — inside the walls (§16).

"Dumb outside / smart inside": the fetcher does broad public aggregation in the cloud; the
*personalization* — which papers actually matter to THIS owner's notes — happens here, on
the local embedder, where the corpus never has to move (Invariant 11).

The fetched papers are **public, external** literature. They are ranked **transiently** and
are NEVER written into the AUTHORED mirror (that pool is the owner's own writing; mixing in
external papers would corrupt the mirror and the §15 baselines). Ranking produces a reading
list the owner reads; it does not mutate any store.

Two signals, combined deterministically:

  * **Relevance** — cosine similarity of each paper (title + abstract, embedded locally) to
    the centroid of the owner's most-relevant AUTHORED notes for the topic. This is the
    private-corpus personalization, computed without the corpus ever leaving.
  * **Evidence quality** (§16 / Constitution §III.1 honesty) — bias toward systematic
    reviews / meta-analyses / guidelines; flag preprints as *not yet vetted*; flag any paper
    lacking a resolvable identifier. We surface evidence quality, not just a conclusion.

`rank_literature` returns an ordered list; the research advisor *informs*, and final health
decisions defer to a clinician (Invariant 7) — enforced by the Librarian/Constitution frame,
not here.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from core.ingest.embed import Embedder
from core.ingest.index import semantic_search
from core.provenance import MIRROR_READABLE
from core.research.criteria import Paper, ResearchCriteria
from core.stores.vectorstore import VectorStore

# Evidence tiers and their ordering weight. High-evidence syntheses outrank primary studies,
# which outrank preprints (not-yet-vetted). Tuned conservatively; the safe-lever (§14) seam.
_HIGH_EVIDENCE = {"systematic-review", "meta-analysis", "review", "guideline",
                  "systematic review", "meta analysis"}
_PRIMARY_EVIDENCE = {"randomized-controlled-trial", "clinical-trial", "cohort-study",
                     "case-control-study", "clinical trial", "rct"}
_EVIDENCE_WEIGHT = {"high": 0.20, "primary": 0.10, "preprint": -0.15, "other": 0.0}

# Relevance dominates; evidence quality adjusts. Both bounded so neither can dominate alone.
_W_RELEVANCE = 1.0


@dataclass(frozen=True)
class RankedPaper:
    paper: Paper
    relevance: float          # cosine to the owner's relevant-note centroid, in [-1, 1]
    evidence_tier: str        # "high" | "primary" | "preprint" | "other"
    score: float              # combined ordering score
    flags: tuple[str, ...]    # honesty flags surfaced to the owner


def _cosine(a: list[float], b: list[float]) -> float:
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return sum(x * y for x, y in zip(a, b, strict=True)) / (na * nb)


def _centroid(vectors: list[list[float]]) -> list[float] | None:
    if not vectors:
        return None
    dim = len(vectors[0])
    acc = [0.0] * dim
    for v in vectors:
        for i, x in enumerate(v):
            acc[i] += x
    return [x / len(vectors) for x in acc]


def _evidence_tier(paper: Paper) -> str:
    if paper.is_preprint:
        return "preprint"
    t = paper.type.strip().lower()
    if t in _HIGH_EVIDENCE:
        return "high"
    if t in _PRIMARY_EVIDENCE:
        return "primary"
    return "other"


def _flags(paper: Paper, tier: str) -> tuple[str, ...]:
    flags: list[str] = []
    if tier == "preprint":
        flags.append("preprint-not-vetted")  # §16: flag preprints as not-yet-vetted
    # Honesty (§III.1): a citation that can't be resolved is a failure. The core can't make a
    # network call to resolve it, so it checks the identifier is at least PRESENT and
    # well-formed; the source API already returned it, true resolution is the reader's click.
    if not paper.doi and not paper.url:
        flags.append("unresolved-identifier")
    if not paper.abstract.strip():
        flags.append("no-abstract")
    return tuple(flags)


def rank_literature(
    result_papers: list[Paper],
    criteria: ResearchCriteria,
    embedder: Embedder,
    store: VectorStore,
    *,
    k_notes: int = 5,
) -> list[RankedPaper]:
    """Rank public papers against the owner's relevant AUTHORED notes. Pure read; no writes.

    Personalization centroid: retrieve the top-k AUTHORED notes for the topic, re-embed their
    text locally to get vectors, average them. Each paper is scored by cosine to that centroid
    plus an evidence-quality adjustment. If the corpus has nothing on the topic, relevance
    falls back to similarity with the topic query embedding (still fully local)."""
    if not result_papers:
        return []

    query = criteria.topic + " " + " ".join(criteria.terms)

    # The private-corpus centroid — the mirror firewall (AUTHORED-only) holds (Invariant 11).
    note_rows = semantic_search(query, embedder, store, k=k_notes, provenances=MIRROR_READABLE)
    note_texts = [r.get("text", "") for r in note_rows if r.get("text")]
    note_vectors = embedder.embed_documents(note_texts) if note_texts else []
    centroid = _centroid(note_vectors)
    if centroid is None:
        # Corpus silent on the topic — rank by topical relevance to the query alone.
        centroid = embedder.embed_query(query)

    paper_vectors = embedder.embed_documents(
        [f"{p.title}. {p.abstract}".strip() for p in result_papers]
    )

    ranked: list[RankedPaper] = []
    for paper, vec in zip(result_papers, paper_vectors, strict=True):
        relevance = _cosine(vec, centroid)
        tier = _evidence_tier(paper)
        score = _W_RELEVANCE * relevance + _EVIDENCE_WEIGHT[tier]
        ranked.append(RankedPaper(
            paper=paper, relevance=relevance, evidence_tier=tier,
            score=score, flags=_flags(paper, tier),
        ))

    # Deterministic order: score desc, then a stable tiebreak (source id) so equal scores
    # don't reorder run to run.
    ranked.sort(key=lambda r: (-r.score, r.paper.source, r.paper.id))
    return ranked
