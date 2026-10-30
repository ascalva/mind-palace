# ── Family 1 boundary (labelings & information-flow) · symbols in docs/NOTATION.md ──
# OBJECT:    π_MR — the projection onto the mirror-readable layers MR (family 1).
# INVARIANT: in(Ω) ⊆ π_MR(V); observed/curated is unreachable to introspective agents Ω (I6).
# ENFORCED:  structural — a non-MR view is unrepresentable (MirrorView.__post_init__ raises).
#            Residual G11: guards the *data*, not the store handle.
"""The mirror projection as a TYPE (Invariant 6, BUILD-SPEC §8; gap G3).

I6 — the firewall — requires that introspective agents (the dreamer; the curator's theme /
contradiction scan) read ONLY the mirror-readable provenance classes
(`MIRROR_READABLE = {authored}`), so third-party observed exhaust can never seed a dream or
enter the behavioral baselines (§15). Until now that was a *call-site convention*: remember to
pass `provenances=MIRROR_READABLE` to `all_rows`. The formal-properties catalog (G3) asks to
promote it to **structural**.

`MirrorView` is that promotion. It is the only thing the introspective agents cluster over, and:

  * its sole *normal* constructor, `project`, applies π_MR — it reads the source restricted to
    `MIRROR_READABLE`; and
  * `__post_init__` re-validates every row's provenance and **raises** on a non-authored row,

so a `MirrorView` holding observed (or any non-MR) data **cannot be constructed at all** — not
by `project`, not by hand. Handing an introspective agent non-authored data is therefore
*unrepresentable* (the wrong state cannot be built), the top tier of the assurance hierarchy,
rather than "checked and refused". Functions typed to accept a `MirrorView` inherit the proof.

Note this is the *introspective* read path. The curator's prune scan deliberately reads ALL
provenances (orphaned derived weight is dead regardless of provenance); that is not a mirror
read and correctly does not go through `MirrorView`.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, ClassVar, Protocol

from core.kernel.clearance import MIRROR_READ, Clearance
from core.kernel.provenance import MIRROR_READABLE, Provenance
from core.kernel.scope import (
    ANCHOR,
    Authority,
    Clock,
    EdgeScope,
    Scope,
    Stratum,
    StratumScope,
    Tier,
    TimeScope,
    Window,
)

_ALLOWED = frozenset(p.value for p in MIRROR_READABLE)


class RowSource(Protocol):
    """Anything that yields the rows a clearance admits (the VectorStore, an observation store, a
    test fake). The clearance is REQUIRED: a read states its authority (A3.4)."""

    def all_rows(self, *, clearance: Clearance[Provenance]) -> Sequence[Mapping[str, Any]]:
        ...


class NonMirrorRowError(ValueError):
    """A row whose provenance is outside MIRROR_READABLE was offered to a MirrorView."""


@dataclass(frozen=True)
class MirrorView:
    """An authored-only projection of the thought-graph. Every contained row is guaranteed
    `provenance ∈ MIRROR_READABLE` — the *type itself* is the proof. Obtain one via
    `MirrorView.project(store)`; direct construction with non-authored rows raises."""

    # The declared capability-scope (dn-capability-scope §2.4 table; bp-039 Item 3). A pure
    # DECLARATION — a ClassVar, not a dataclass field, so it touches neither construction nor any
    # read. Σ = mirror_authored (the π_MR refinement); no fibers; a projection-event point window;
    # read-only, no world reach; STRUCTURAL (a non-mirror row is unconstructable — the top tier).
    SCOPE: ClassVar[Scope] = Scope(
        StratumScope.of(Stratum.MIRROR_AUTHORED),
        EdgeScope.bottom(),
        TimeScope(Clock.PROJECTION_EVENT, Window.point(ANCHOR)),
        Authority.read_only(),
        tier=Tier.STRUCTURAL,
    )

    _rows: tuple[Mapping[str, Any], ...] = ()

    def __post_init__(self) -> None:
        # Structural backstop: a MirrorView can NEVER hold a non-authored row, however it was
        # constructed. This is what makes "observed data reaches the mirror" unrepresentable.
        bad = [r.get("provenance") for r in self._rows if r.get("provenance") not in _ALLOWED]
        if bad:
            raise NonMirrorRowError(
                f"MirrorView would hold non-mirror-readable rows (provenance {bad!r}); "
                f"only {sorted(_ALLOWED)} are admissible (Invariant 6)"
            )

    @classmethod
    def project(cls, source: RowSource) -> MirrorView:
        """π_MR — the mirror projection, and the only sanctioned way to build a MirrorView.
        Reads `source` restricted to MIRROR_READABLE; `__post_init__` then re-checks, so even
        a buggy source cannot smuggle a non-authored row past the type (fail-closed)."""
        return cls(_rows=tuple(source.all_rows(clearance=MIRROR_READ)))

    def rows(self) -> list[dict[str, Any]]:
        """The authored rows, as fresh plain dicts (the view itself stays immutable)."""
        return [dict(r) for r in self._rows]

    def __len__(self) -> int:
        return len(self._rows)
