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

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any, Protocol

from core.provenance import MIRROR_READABLE, Provenance

_ALLOWED = frozenset(p.value for p in MIRROR_READABLE)


class RowSource(Protocol):
    """Anything that can yield provenance-filtered rows (the VectorStore, or a test fake)."""

    def all_rows(self, *,
                 provenances: Iterable[Provenance] | None = None) -> list[dict[str, Any]]:
        ...


class NonMirrorRowError(ValueError):
    """A row whose provenance is outside MIRROR_READABLE was offered to a MirrorView."""


@dataclass(frozen=True)
class MirrorView:
    """An authored-only projection of the thought-graph. Every contained row is guaranteed
    `provenance ∈ MIRROR_READABLE` — the *type itself* is the proof. Obtain one via
    `MirrorView.project(store)`; direct construction with non-authored rows raises."""

    _rows: tuple[dict[str, Any], ...] = ()

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
        return cls(_rows=tuple(source.all_rows(provenances=MIRROR_READABLE)))

    def rows(self) -> list[dict[str, Any]]:
        """The authored rows (a fresh list; the view is immutable)."""
        return list(self._rows)

    def __len__(self) -> int:
        return len(self._rows)
