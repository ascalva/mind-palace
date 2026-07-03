# ── Family 2 boundary (regenerable derivation) · symbols in docs/NOTATION.md ──
# OBJECT:    a source object AS the set of its idea-vectors — the fibre of the derived chunk
#            layer over its content-address identity H(raw) ∈ Σ (core/stores/rawstore.py).
#            The set-as-relation's formal home is the derivation hypergraph ℋ (Family 5, future).
# INVARIANT: membership keyed by `digest` ∈ Σ; a source lives at exactly ONE provenance stratum ρ
#            (a mixed-provenance digest raises). NO aggregate is produced — members are the raw
#            idea-vectors; a coarse/note-level vector would be a DERIVED cache, never identity.
# ENFORCED:  structural — grouping is provenance-parametric (SourceId carries ρ as a first-class
#            field, not a convention); any stratum, one machinery, no bespoke path.
"""The source-set: "a source object IS the set of its idea-vectors", as a type (BUILD-SPEC §8).

Embedding is single-scale at chunk grain: `index_records` writes one vector row per chunk, and
nothing stores a note-level vector. The membership relation "these chunk vectors belong to that
source" is therefore already present in the rows (they carry `digest`, the raw-store identity),
but only as an *implicit group-by* re-derived at each call site (`note_centroids`, `note_snippets`).
This module promotes that relation to a **type**, the way `MirrorView` promoted the provenance
projection to a type: a source object is `SourceId` (its content digest at a provenance stratum)
together with `members`, the idea-vectors that constitute it.

Three things it deliberately is NOT:

  * It is **not** a new vector or embedding pass. `vectors()` returns the raw member vectors,
    never a mean. A coarse/note-level vector (centroid or medoids for cheap routing at scale)
    would be a separately-gated DERIVED performance cache carrying its own DERIVED provenance —
    never a source's identity — and is out of scope here.
  * It is **not** a bespoke writer. Grouping is provenance-parametric: an authored-solo note
    today and a curated-external item at another stratum tomorrow use the SAME machinery with a
    different label (mirroring `ingest_note`'s one-pipeline shape, §1). The stratum is a
    first-class field on `SourceId`, not a convention.
  * It is **not** the hypergraph. A source-set is formally a hyperedge over the idea-vector
    vertices (the derivation hypergraph ℋ, Family 5 / companion III); that wiring is a separate
    track — named here, not built.

Flat retrieval is unchanged and remains the default; source-grained retrieval is an explicit
opt-in (`grouped_semantic_search`), so the flat path is provably byte-identical (the recursive-
strata I3 floor-zero posture: the added mode recovers the old behavior exactly when unused).
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any, Protocol

from core.provenance import Provenance


class RowSource(Protocol):
    """Anything that yields provenance-filtered chunk rows — the VectorStore, or a test fake.
    Same shape as `core.mirror.RowSource`; kept local so the store layer doesn't depend on the
    mirror view."""

    def all_rows(self, *,
                 provenances: Iterable[Provenance] | None = None) -> list[dict[str, Any]]:
        ...


class MixedProvenanceError(ValueError):
    """A single source `digest` carried rows of more than one provenance. A source object lives
    at exactly one stratum, so this is a data-integrity error, not a mergeable state — surfaced
    rather than silently picking a label (the firewall discipline: fail closed on ambiguity)."""


@dataclass(frozen=True)
class SourceId:
    """The typed identity of a source object: its raw-store content `digest` (an element of Σ,
    core/stores/rawstore.py) at a provenance `provenance` (its stratum/label).

    Both fields are first-class. Identity is not merely "a digest" but "a digest at a stratum",
    which is what lets the same membership machinery serve every provenance class with no bespoke
    path — a different label through the same type (the provenance-parametric shape of
    `ingest_note`). `digest` is the identity; `provenance` is the stratum it lives in."""

    digest: str
    provenance: Provenance


@dataclass(frozen=True)
class SourceSet:
    """A source object as the set of its member idea-vectors (chunk rows).

    `id` is the typed identity (digest + stratum); `members` are the source's chunk rows in
    `chunk_index` order — the idea-vectors that *constitute* the source. This is a view over
    existing rows: no vector is produced. `vectors()` returns the raw member vectors, never an
    aggregate.

    Whether `members` is the source's *complete* chunk set or a *matched subset* is a property
    of the constructor, not of the type: `source_set` / `source_sets` build complete sets (a
    full scan grouped by digest); `grouped_semantic_search` builds the matched subset (the
    search projection). The type only ever claims "these member idea-vectors of this source"."""

    id: SourceId
    title: str
    members: tuple[dict[str, Any], ...]

    @property
    def digest(self) -> str:
        return self.id.digest

    @property
    def provenance(self) -> Provenance:
        return self.id.provenance

    def vectors(self) -> list[list[float]]:
        """The member idea-vectors — raw, one per chunk, never aggregated. A source's coarse
        vector is intentionally not derivable here (see module docstring)."""
        return [list(m["vector"]) for m in self.members]

    def best_distance(self) -> float | None:
        """The nearest member's cosine distance if these rows came from a search (`_distance`
        present), else None. A read-through over existing row data — no score is stored."""
        ds = [m["_distance"] for m in self.members if "_distance" in m]
        return min(ds) if ds else None

    def __len__(self) -> int:
        return len(self.members)


def group_sources(rows: Iterable[dict[str, Any]]) -> list[SourceSet]:
    """Group flat chunk rows into source objects by `digest` — the membership relation made
    first-class. This is the one grouping path; callers scope by provenance upstream (or not).

    Ordering is deterministic: source order follows first appearance in `rows` (so a distance-
    ranked search result stays ranked by each source's best hit), and members within a source
    are ordered by `chunk_index` (so a complete set reconstructs the note in reading order).

    Every row of a source must share one provenance — a source lives at one stratum — so a
    `digest` spanning provenances raises `MixedProvenanceError` rather than merging strata."""
    grouped: dict[str, list[dict[str, Any]]] = {}
    for r in rows:
        grouped.setdefault(r["digest"], []).append(r)
    out: list[SourceSet] = []
    for digest, members in grouped.items():
        provs = {m["provenance"] for m in members}
        if len(provs) > 1:
            raise MixedProvenanceError(
                f"source {digest!r} spans provenances {sorted(provs)!r}; a source object lives "
                "at exactly one stratum"
            )
        prov = Provenance(next(iter(provs)))
        title = next((m.get("title", "") for m in members), "")
        ordered = tuple(sorted(members, key=lambda m: m.get("chunk_index", 0)))
        out.append(SourceSet(id=SourceId(digest=digest, provenance=prov), title=title,
                             members=ordered))
    return out


def source_sets(store: RowSource, *,
                provenances: Iterable[Provenance] | None = None) -> list[SourceSet]:
    """Every source object in the store, optionally scoped to provenance classes.

    Default is all strata: this is a structural grouping utility, not a mirror read, so it does
    not default to `MIRROR_READABLE`. Pass `provenances=MIRROR_READABLE` for the introspective
    firewall, exactly as with `VectorStore.all_rows`. A non-authored stratum (e.g. `{CURATED}`)
    works through this same call with no bespoke path."""
    return group_sources(store.all_rows(provenances=provenances))


def source_set(store: RowSource, digest: str, *,
               provenances: Iterable[Provenance] | None = None) -> SourceSet | None:
    """The one source object identified by `digest`, or None if absent. Scans then filters
    (single-user corpus scale, the same posture as `VectorStore.all_rows`)."""
    rows = [r for r in store.all_rows(provenances=provenances) if r["digest"] == digest]
    sets = group_sources(rows)
    return sets[0] if sets else None
