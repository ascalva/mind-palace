"""The dreams reading scope — surfacing the INTERPRETED layer, mirror-not-oracle.

The dreamer + curator write thematic syntheses and housekeeping findings to the `DerivedStore`
(INTERPRETED provenance, BUILD-SPEC §8). Before this, nothing *showed* them to the owner — the
whole dreaming layer ran in the background and stayed invisible (WIRING-AUDIT DANGLING #1). The
Ambassador's DREAMS path reads through here.

Two rules shape it:
  * Read-only, the OpsView move — `DreamsView` binds ONLY the store's read methods as callables;
    it holds no `add`/`reset`, so the Ambassador cannot write the interpreted layer through it
    (assurance tier: static + guard, like `OpsView`; weaker than MirrorView's structural copy,
    and labelled so).
  * Mirror, not oracle (Constitution §III.2, the §8 firewall). A dream is what the SYSTEM
    inferred, never what the owner wrote — so the narration marks it as interpretation, holds it
    loosely, cites the authored notes it spans in [[brackets]], and hands the judgment back. It
    must never read as authored ground truth; that asymmetry is the whole point of keeping the
    interpreted layer separate and provenance-marked.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from core.stores.derived import DREAM, FINDING, Artifact


class ArtifactReads(Protocol):
    """The read slice of a `DerivedStore` this view binds — reads and ONLY reads."""

    def all(self, *, kind: str | None = ..., subkind: str | None = ...) -> list[Artifact]: ...

    def count(self, *, kind: str | None = ...) -> int: ...


class RetractedReads(Protocol):
    """A duck-typed source of RETRACTED subject ids (a `DispositionStore.retracted`)."""

    def retracted(self) -> set[str]: ...


@dataclass(frozen=True)
class DreamsView:
    """Read-only view over the DerivedStore's INTERPRETED artifacts (dreams + findings).

    Construct with `DreamsView.over(store)`; the fields are bound READ callables only — there is
    no mutator (`add`/`reset`) on this type's surface (asserted in tests/integrity)."""

    _all: Callable[..., list[Artifact]]
    _count: Callable[..., int]
    # Optional active-projection filter: a duck-typed source of RETRACTED subject ids (a
    # `DispositionStore.retracted`). When bound, a dream the owner verdicted `wrong`/`noise` is
    # dropped from what is surfaced (§6). None = no verdict layer wired → surfaces every dream.
    _retracted: Callable[[], set[str]] | None = None

    @classmethod
    def over(cls, store: ArtifactReads, *,
             dispositions: RetractedReads | None = None) -> DreamsView:
        """Bind the store's reads (+ an optional `retracted` disposition read).
        The returned view exposes those and only those — the store's `add`/`reset` are unreachable
        through it. Passing `dispositions` makes it the ACTIVE projection: retracted dreams are
        excluded from `recent_dreams`. Omit it to keep the prior behavior byte-identical."""
        return cls(_all=store.all, _count=store.count,
                   _retracted=(dispositions.retracted if dispositions is not None else None))

    # --- reads -------------------------------------------------------------------------------
    def recent_dreams(self, limit: int = 5) -> list[Artifact]:
        """The most recent thematic dreams, newest first (the store orders oldest-first), excluding
        any the owner has RETRACTED by verdict — the active projection (ingest-identity §6)."""
        dreams = self._all(kind=DREAM)[::-1]
        if self._retracted is not None:
            retracted = self._retracted()
            dreams = [d for d in dreams if d.id not in retracted]
        return dreams[:limit]

    def dream_count(self) -> int:
        return self._count(kind=DREAM)

    def finding_count(self) -> int:
        return self._count(kind=FINDING)

    # --- mirror-not-oracle narration ---------------------------------------------------------
    def narrate_recent(self, limit: int = 5) -> str:
        """Reflect recent dreams back in plain language, framed as interpretation the owner
        judges — never as authored fact (§III.2)."""
        dreams = self.recent_dreams(limit)
        if not dreams:
            return (
                "I haven't surfaced any patterns yet. I look for connections across your notes "
                "in the background, and once there's enough there to link up I'll reflect what I "
                "find — nothing to report so far."
            )
        lead = (
            "A few threads I noticed reading back over your notes — this is my read of them, not "
            "anything you wrote, so take them as prompts rather than conclusions:"
        )
        bullets = [f"• {_render(d)}" for d in dreams]
        close = "Do any of those land?"
        findings = self.finding_count()
        if findings:
            close += (
                f" (I've also flagged {findings} note{'s' if findings != 1 else ''} that may be "
                "duplicates or orphans, if you ever want to tidy up.)"
            )
        return "\n".join([lead, "", *bullets, "", close])


def _render(d: Artifact) -> str:
    """One dream as a held-loosely line: the synthesis + the authored notes it spans, cited."""
    spanned = ", ".join(f"[[{s}]]" for s in d.subjects)
    return f"{d.summary}  (across {spanned})" if spanned else d.summary
