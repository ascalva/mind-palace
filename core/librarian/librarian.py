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

Forward seam (Phase 8 airlock, §16): the librarian also emits de-identified research
criteria for the outbound fetchers. Not built here — flagged so the role's scope is clear.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from core.constitution import Message, frame_context
from core.ingest.embed import Embedder
from core.ingest.index import semantic_search
from core.models import ModelServer
from core.provenance import MIRROR_READABLE, Provenance
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
