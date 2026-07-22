# ── Family 1 boundary (labelings & information-flow) · symbols in docs/NOTATION.md ──
# OBJECT:    ρ : V → P — the provenance labeling into an *unordered* set;
#            MR = {authored-solo, authored-dialogue} is the load-bearing subset.
# INVARIANT: ρ is invariant under derivation (only human promotion re-tags);
#            mirror-readability = membership in MIRROR_READABLE (I6; the ρ-pin behind I5).
# ENFORCED:  structural — MR-membership via MirrorView; ρ non-launderable (DerivedStore has
#            no provenance param). The trust *preorder* is retired (G8): only the set matters.
"""Provenance classes for the data architecture (BUILD-SPEC §8; design-notes/
observed-data-and-the-assistant-tier.md; the §1 provenance-spectrum growth path).

Every stored datum carries a provenance class so a query or agent can always distinguish
"the owner wrote it" from "the system inferred it" from "a third party observed it" from
"the owner selected someone else's words". The classes do not mix — that separation is the
firewall (BUILD-SPEC §8).

The spectrum (Track B realizes the §1 split that the formal spec already assumes):
  * **authored-solo**     — the owner wrote it alone (notes, journals). Ground truth, feeds
                            the mirror. This is what the single `authored` tag used to mean;
                            existing rows relabel to it (a same-trust-tier relabel, not a
                            promotion across the firewall — both authored classes are
                            mirror-readable).
  * **authored-dialogue** — the owner's own words to the Ambassador. Still authored ground
                            truth ("your words to it are more yours than its words to you"),
                            so it is mirror-readable too — closing the capture loop.
  * **curated**           — others' words the owner selected (books, highlights, and the
                            system's own white papers / design notes = its self-knowledge
                            graph). Lives in its own graph; **never** merged into the authored
                            mirror (curated ∉ MIRROR_READABLE — the same firewall shape as
                            book-dreaming). The Ambassador reads it only via a *deliberate,
                            non-default* `provenances={CURATED}` query.
  * **interpreted**       — system inference. Structurally unforgeable (the derived store has
                            no provenance parameter).
  * **observed**          — third-party behavioral exhaust. Assistant-tier only; never the
                            mirror, never the baselines. Reserved (dormant schema).
  * **code**              — builder-produced reality read from the repo instrument (the code
                            embed lane, dn-code-ingest-pipeline §2.3; warrant finding-0146). ∉
                            MIRROR_READABLE — a `MirrorView` refuses code rows by construction,
                            so the self-model and the §15 baselines never see code. STRUCTURALLY
                            minted: the code lane's row assembly hardcodes CODE with NO provenance
                            parameter anywhere on its API (`core/ingest/code_corpus.py`), so a
                            caller physically cannot launder code into an authored class — the
                            `CodeObservation.to_row` move. Dreamable by DELIBERATE grant only
                            (`provenances={CODE}`, the CURATED precedent; XS-a per-grant,
                            dn-cross-strata-dreamer) — never the default grant.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import final


class Provenance(StrEnum):
    AUTHORED_SOLO = "authored-solo"          # owner wrote it alone. Ground truth; feeds the mirror.
    AUTHORED_DIALOGUE = "authored-dialogue"  # owner's words to the Ambassador. Authored, mirror-ok
    CURATED = "curated"          # others' words the owner selected (books; self-knowledge graph)
    INTERPRETED = "interpreted"  # system inference over other data. Derived, regenerable, marked.
    # RESERVED (recursive-strata.md §4/§8; build plan PD6) — promoted, depth-carrying derived
    # strata: Dreamer outputs that re-enter reasoning as substrate. Self-generated — trusted as to
    # ORIGIN (the attestation chain proves the Dreamer produced them), untrusted as to TRUTH (only
    # owner verdicts confer that) — so NEVER mirror-readable and never confusable with authored K₀.
    # No code consumes it yet: the label (and its future integer stratum `depth`) is reserved now so
    # the recursive Dreamer unparks without a second migration (recursive-strata §8 action 1). A
    # single enum entry — the cheap half of that action; the `depth` field lands with its consumer.
    DERIVED_STRATUM = "derived-stratum"
    # RESERVED — not ingested yet. Third-party behavioral exhaust (Data Portability export,
    # web/social history, sensor streams). Low-trust, ASSISTANT-TIER ONLY, quarantined from
    # the mirror and from behavioral baselines (§15). Defined now so stores and queries are
    # provenance-aware from the start (cf. the dormant sensor schema).
    OBSERVED = "observed"
    # The code embed lane (dn-code-ingest-pipeline §2.3; warrant finding-0146). Builder-produced
    # reality read from the repo instrument — the source, its docstrings, its comments, embedded as
    # a first-class semantic source. ∉ MIRROR_READABLE (below), so it is INVISIBLE to the mirror and
    # the §15 baselines. Structurally minted (no provenance param on `core/ingest/code_corpus.py`),
    # so it is non-launderable like INTERPRETED/OBSERVED. Dreamable only by a deliberate
    # `provenances={CODE}` grant (the CURATED precedent) — Ouroboros dreams over its own code by
    # choice, never by default. Consumed by the code lane; F-CI1 pins the firewall.
    CODE = "code"


# What the introspective mirror / dreaming agent is permitted to read (the firewall).
#
# The load-bearing structure is exactly this SET — `MIRROR_READABLE` — not a trust *preorder*
# (gap G8). No code orders the classes, and `INTERPRETED` is a *derived* axis orthogonal to
# trust, so a single trust order would be fiction. Two facts are load-bearing, both STRUCTURAL:
#   1. Mirror-readability is membership in this set — enforced by the typed `MirrorView`
#      (core/mirror.py): a non-MR view is unrepresentable (Invariant 6). The mirror reads BOTH
#      authored classes (solo + dialogue) and nothing else; in particular CURATED is excluded
#      (others' words never enter the owner's self-reflection or the §15 baselines), matching
#      the formal spec's MIRROR_READABLE = {authored-solo, authored-dialogue}.
#   2. Provenance is invariant under derivation — the only way to mint an INTERPRETED datum is
#      the `DerivedStore`, which has no provenance parameter, so no pipeline can launder
#      curated/observed/interpreted into authored. Promotion *up* to an authored class is a
#      deliberate human re-tag-from-raw (§8), never automatic.
MIRROR_READABLE: frozenset[Provenance] = frozenset(
    {Provenance.AUTHORED_SOLO, Provenance.AUTHORED_DIALOGUE}
)


# ── The static shadow (type-system-as-core-audit.md §2.4; bp-009 spike) ──────────────────
#
# `Authored[T]` / `Derived[T]` lift the authored-vs-derived HALF of the labeling ρ into the
# type grammar, so *accidental* label promotion is a mypy error at authorship time, at zero
# runtime cost. The shadow is STRICTLY WEAKER than the runtime invariant: it sees no values
# and no runtime paths, and a deliberate `cast` defeats it. It strengthens — never replaces
# or duplicates — the structural layer above: `MirrorView` remains the sole authority that
# may mint `Authored` at a read boundary (its runtime re-check is untouched), and
# `DerivedStore` remains the only INTERPRETED mint. What the tags add is REACH: today the
# proof evaporates at `MirrorView.rows()` (downstream consumers accept bare row dicts, so a
# caller that bypasses the view is caught by nothing); a consumer typed to demand
# `Authored[...]` carries the proof to its own signature.
#
# Grain is BINARY by recorded default (bp-009 plan §11): the checker's grammar is unordered,
# so the four-class authorship-distance axis order cannot be expressed as types anyway; the
# classes stay data (the `Provenance` enum above). Depth is VALUES-ONLY (same table):
# `list[Authored[Row]]` — a container of tagged values — is in; `Authored[list[Row]]` is not.
# Together the two points form a meet-semilattice (plan §8): meet = Derived (a function
# mixing any Derived input returns Derived); `promote` below is the ONLY up-move.


@final
@dataclass(frozen=True)
class Authored[T]:
    """A value obtained exclusively from mirror-readable (authored) sources.

    An information-flow label, not a claim the owner typed this exact value: a note centroid
    computed over authored rows is still `Authored[NoteVector]` — what the firewall tracks is
    the provenance CLASS of the sources. `@final`: even deliberate subclass-laundering
    (a `Derived` masquerading via inheritance) is a type error, not just an accident."""

    value: T


@final
@dataclass(frozen=True)
class Derived[T]:
    """A value that transited system inference (the INTERPRETED lane) — or mixed with one.

    The meet of the two-point lattice: any computation touching a `Derived` input yields
    `Derived` output. The only way UP is `promote`, which demands the owner's capability."""

    value: T


@final
class OwnerVerdict:
    """PLACEHOLDER capability token for verdict-gated promotion (I1) — taxonomy UNRATIFIED.

    Deliberately a NOMINAL class, not a Protocol: an empty Protocol is structurally satisfied
    by every object, which would let `promote(d, object())` type-check and vacate the
    capability constraint. `@final` keeps it unforgeable-by-subclass at the type level.

    This class answers NO design questions (recorded in bp-009's journal for /triage):
    whether it unifies with the runtime verdict machinery (`core/verdict/`,
    `core/stores/verdicts.py`), whether a verdict names its target authored class, and its
    scope (per-value / per-artifact / per-run) are all open until the I1 taxonomy ratifies.
    At runtime it confers nothing — `promote` raises regardless."""

    __slots__ = ()


def promote[T](x: Derived[T], cap: OwnerVerdict) -> Authored[T]:
    """The ONLY up-move of the two-point lattice — signature per §2.4, verbatim.

    Extends the promotion comment above `MIRROR_READABLE` ("Promotion *up* to an authored
    class is a deliberate human re-tag-from-raw (§8), never automatic"): at the type level,
    a call site that never received an `OwnerVerdict` cannot even EXPRESS a promotion, so
    the accidental-violation class is removed at authorship time.

    STUB — verdict-gated promotion (I1) is unbuilt (recursive-strata parked) and the verdict
    taxonomy is unratified, so this body deliberately implements NO policy. The typed
    signature is the contract the future implementation must satisfy."""
    raise NotImplementedError(
        "verdict-gated promotion (I1) is not built: the OwnerVerdict taxonomy is unratified "
        "(recursive-strata parked). This stub exists so the type checker constrains call "
        "sites today; it deliberately implements no promotion policy."
    )
