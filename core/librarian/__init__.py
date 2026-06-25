"""Zone A — the Librarian: core RAG query agent over the thought-graph (BUILD-SPEC §9).

Semantic retrieval over the AUTHORED mirror + grounded reasoning under the Constitution,
with a deterministic grounding self-check before returning. The de-identified research
criteria seam (§16) lands with the airlock (Phase 8).
"""

from core.librarian.librarian import (
    Librarian,
    LibrarianAnswer,
    Retrieval,
    build_librarian,
)

__all__ = ["Librarian", "LibrarianAnswer", "Retrieval", "build_librarian"]
