"""The Librarian — the core RAG query agent over the thought-graph (BUILD-SPEC §9).

The owner's primary interface to their own mind: semantic retrieval over the AUTHORED
corpus (the mirror — defaults to MIRROR_READABLE so observed exhaust can never leak in,
the firewall from design-notes/observed-data-and-the-assistant-tier.md), then grounded
reasoning with the Constitution as the outermost frame (Invariant 6).

Per *mirror, not oracle* (Constitution §III.2) it presents synthesis as a lens on the
owner's own notes, cites only the notes it actually retrieved, and says plainly when the
corpus does not cover the question. Before returning, it runs the Constitution pre-return
check (`core.selfcheck`): the deterministic grounding check verifies every cited note
resolves to a retrieved source.

Airlock seam (Phase 8, §16): the librarian also emits **de-identified research criteria**
for the outbound fetchers (`research_criteria`). The model only *proposes* terms; the
de-identification enforcement lives in `core.research.criteria` (the model advises, code acts).
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass

from core.constitution import Message, frame_context
from core.ingest.embed import Embedder
from core.ingest.index import semantic_search
from core.models import ModelServer
from core.provenance import MIRROR_READABLE, Provenance
from core.research.criteria import ResearchCriteria, deidentify
from core.selfcheck import SelfCheck, Source, SubjectiveJudge, self_evaluate
from core.stores.vectorstore import VectorStore

LIBRARIAN_ROLE = (
    "You are the Librarian of a sealed personal mind-palace: a mirror onto the owner's "
    "own notes, not an oracle.\n\n"
    "Ground every substantive claim in the retrieved notes below. Cite the notes you draw "
    "on by title in double brackets, e.g. [[note title]]. Never cite a note that is not in "
    "the retrieved context, and never invent notes, quotes, facts, or citations.\n\n"
    "When the retrieved notes do not answer the question, say so plainly instead of "
    "guessing. Surface uncertainty. Offer the patterns and options you see and let the "
    "owner draw the conclusions — the judgment is theirs."
)

NO_CONTEXT = "No notes were retrieved for this query; the corpus has nothing on it."

# A model-backed term proposer takes the owner's (possibly personal) question and proposes
# de-identified topical search terms. Its OUTPUT is not trusted: `deidentify()` scrubs it.
TermProposer = Callable[[str], "tuple[str, list[str]]"]   # query -> (topic, terms)

CRITERIA_PROPOSER_ROLE = (
    "You turn a personal question into de-identified literature-search terms. Output ONLY a "
    "short topic label and 3-8 generic medical/scientific search terms. Strip every personal "
    "detail — no names, dates, places, employers, or first-person narrative. Terms must be "
    "generic topical phrases a literature database would understand (e.g. 'migraine "
    "prophylaxis', 'chronic stress'). Reply as: 'topic: <label>' then one term per line."
)

# Minimal stopword set for the deterministic fallback proposer (no model needed).
_STOPWORDS = frozenset(
    "a an the and or but of to in on for with about my our i we me you your is are was were "
    "be been being do does did have has had what which who when where why how should could "
    "would can may might will shall not no yes it this that these those been since from into "
    "over under been them they he she his her their as at by".split()
)
_WORD = re.compile(r"[A-Za-z][A-Za-z'-]+")


def _deterministic_proposer(query: str) -> tuple[str, list[str]]:
    """Model-free fallback: extract topical keywords by frequency/order. Deterministic, so
    the criteria path is testable cold.

    HONESTY: this only does *structural* word extraction — it does NOT understand which words
    are personally sensitive narrative (it would keep "divorce" or a month from a personal
    sentence). `deidentify()` guarantees the structural scrub (no emails/dates/phones/handles
    leave), not semantic de-identification. For real outbound queries prefer
    `model_term_proposer` (better term selection) and/or owner review before emit; richer
    semantic scrubbing (corpus proper-noun denylist / NER) is the documented extension point."""
    words = [w.lower() for w in _WORD.findall(query) if w.lower() not in _STOPWORDS and len(w) > 2]
    seen: dict[str, None] = {}
    for w in words:
        seen.setdefault(w, None)
    terms = list(seen)[:8]
    topic = " ".join(terms[:3]) if terms else "general"
    return topic, terms


@dataclass(frozen=True)
class Retrieval:
    title: str
    source_path: str
    text: str
    distance: float
    provenance: str
    digest: str = ""        # stable content id — the citation identity for grounding (G1)


@dataclass(frozen=True)
class LibrarianAnswer:
    text: str
    sources: tuple[Retrieval, ...]
    check: SelfCheck


def _format_context(retrievals: list[Retrieval]) -> str:
    if not retrievals:
        return NO_CONTEXT
    blocks = [f"[[{r.title}]]\n{r.text}" for r in retrievals]
    return (
        "Retrieved notes (the ONLY evidence you may cite):\n\n"
        + "\n\n---\n\n".join(blocks)
    )


@dataclass
class Librarian:
    server: ModelServer
    embedder: Embedder
    store: VectorStore
    tier: str = "routine"          # foreground RAG runs on the routine model (§9)
    # k = the top-k retrieval depth, Ret_k(q) (WHITEPAPER-TECHNICAL §retrieval). BOUND (gap
    # G7): k ∈ [3, 8] — enough recall to ground an answer, few enough that the budgeter rarely
    # has to trim retrieval (the primary lever, §13) and a wrong note can't crowd the window.
    k: int = 5

    def retrieve(self, query: str, *,
                 provenances: Iterable[Provenance] | None = MIRROR_READABLE) -> list[Retrieval]:
        """Semantic retrieval over the thought-graph. Defaults to the mirror
        (AUTHORED-only); the assistant tier (Phase 3+) may widen `provenances`."""
        rows = semantic_search(query, self.embedder, self.store, k=self.k, provenances=provenances)
        return [
            Retrieval(
                title=r.get("title", ""),
                source_path=r.get("source_path", ""),
                text=r.get("text", ""),
                distance=float(r.get("_distance", 0.0)),
                provenance=r.get("provenance", ""),
                digest=r.get("digest", ""),
            )
            for r in rows
        ]

    def context_for(self, query: str, retrievals: list[Retrieval], *,
                    history: list[Message] | None = None) -> list[Message]:
        """Constitution outermost; role; retrieved grounding; history; the query last."""
        return frame_context(
            LIBRARIAN_ROLE, query, history=history,
            context_blocks=[_format_context(retrievals)],
        )

    def answer(self, query: str, *, history: list[Message] | None = None,
               provenances: Iterable[Provenance] | None = MIRROR_READABLE,
               judge: SubjectiveJudge | None = None,
               think: bool | None = None) -> LibrarianAnswer:
        retrievals = self.retrieve(query, provenances=provenances)
        messages = self.context_for(query, retrievals, history=history)
        output = self.server.chat(self.tier, messages, think=think)
        # The retrieved notes are the only legitimate citation targets; resolve by stable
        # digest so the grounding check is well-posed even if two notes share a title (G1).
        sources = [Source(title=r.title, digest=r.digest) for r in retrievals]
        check = self_evaluate(output, sources=sources, judge=judge)
        return LibrarianAnswer(text=output, sources=tuple(retrievals), check=check)

    def research_criteria(
        self,
        query: str,
        *,
        proposer: TermProposer | None = None,
        from_year: int | None = None,
        publication_types: tuple[str, ...] = (),
        max_results: int = 50,
    ) -> ResearchCriteria:
        """Emit de-identified research criteria for the outbound airlock (§16).

        The proposer (default: the deterministic keyword extractor; or a model-backed one)
        only *suggests* terms — `deidentify()` is the enforcer that scrubs PII and rejects
        free narrative. The corpus never enters this path; only the query's topical terms,
        de-identified, can leave (Invariant 11)."""
        topic, terms = (proposer or _deterministic_proposer)(query)
        return deidentify(topic, terms, from_year=from_year,
                          publication_types=publication_types, max_results=max_results)


def build_librarian(config: object | None = None, *, k: int = 5) -> Librarian:
    """Wire a Librarian against the real configured stores and models."""
    from config.loader import get_config
    from core.ingest.embed import build_embedder
    from core.models import build_model_server
    from core.stores.vectorstore import open_vector_store

    cfg = config or get_config()
    return Librarian(
        server=build_model_server(cfg),
        embedder=build_embedder(cfg),
        store=open_vector_store(cfg),
        k=k,
    )


def model_term_proposer(server: ModelServer, *, tier: str = "routine") -> TermProposer:
    """A richer proposer that asks the local model to suggest de-identified terms.

    The model only advises; its output is still scrubbed by `deidentify()` before anything
    can cross the airlock. Parsing is forgiving — a malformed reply degrades to whatever
    clean terms it yields (and `deidentify` raises if none remain)."""
    def propose(query: str) -> tuple[str, list[str]]:
        messages = frame_context(CRITERIA_PROPOSER_ROLE, query)
        out = server.chat(tier, messages)
        topic = ""
        terms: list[str] = []
        for line in out.splitlines():
            line = line.strip(" -*\t")
            if not line:
                continue
            low = line.lower()
            if low.startswith("topic:"):
                topic = line.split(":", 1)[1].strip()
            else:
                terms.append(line)
        if not topic and terms:
            topic = terms[0]
        return topic or "general", terms
    return propose
