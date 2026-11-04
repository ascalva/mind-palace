"""The resolution ledger's defaults — what the elaborator fills in when a sentence leaves a dial
unsaid (dn-query-sentence-algebra §2.7, "precedents" in the second sense).

`docs/query/precedents.md` is the authored record of these defaults and of every ambiguity the
owner has resolved; this dataclass is its executable mirror. A default is a visible part of a
sentence's meaning: change it here and there together, and expect re-run sentences to answer
differently (the measured answer-drift of scoped-context-queries).
"""

from __future__ import annotations

from dataclasses import dataclass

from core.kernel.scope import Stratum
from core.sentence.ast import Direction, Rel


@dataclass(frozen=True)
class Precedents:
    """The defaults in force. Frozen: a sentence compiled under one `Precedents` means one thing."""

    beta: float = 1.0                       # `diffuse`'s temperature: the code's default (RSP-3)
    depth: int = 1                          # `reach`'s hops: `connected_set`'s default
    walk_depth: int = 4                     # `walk`'s longest chain
    walk_limit: int = 200                   # `walk`'s most chains returned
    diffuse_rel: Rel = Rel.S                # `diffuse` with no relation named walks the backbone
    reach_rel: Rel = Rel.F                  # `reach` with no relation named follows citations
    reach_direction: Direction = Direction.BOTH
    trace_direction: Direction = Direction.FORWARD
    strata: tuple[Stratum, ...] = (Stratum.MIRROR_AUTHORED,)   # `near` with no `over`
    k: int = 5                              # hits rendered when the sentence is a field
    read_chunk: int = 0                     # `read` of a paper with no chunk: its start
    read_window: int = 5                    # `read`'s window: chunks of a paper per answer


DEFAULT = Precedents()
