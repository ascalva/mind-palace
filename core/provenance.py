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
"""

from __future__ import annotations

from enum import StrEnum


class Provenance(StrEnum):
    AUTHORED_SOLO = "authored-solo"          # owner wrote it alone. Ground truth; feeds the mirror.
    AUTHORED_DIALOGUE = "authored-dialogue"  # owner's words to the Ambassador. Authored, mirror-ok
    CURATED = "curated"          # others' words the owner selected (books; self-knowledge graph)
    INTERPRETED = "interpreted"  # system inference over other data. Derived, regenerable, marked.
    # RESERVED — not ingested yet. Third-party behavioral exhaust (Data Portability export,
    # web/social history, sensor streams). Low-trust, ASSISTANT-TIER ONLY, quarantined from
    # the mirror and from behavioral baselines (§15). Defined now so stores and queries are
    # provenance-aware from the start (cf. the dormant sensor schema).
    OBSERVED = "observed"


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
