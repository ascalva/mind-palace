"""Provenance classes for the data architecture (BUILD-SPEC §8; design-notes/
observed-data-and-the-assistant-tier.md).

Every stored datum carries a provenance class so a query or agent can always distinguish
"the owner wrote this" from "the system inferred this" — and, in a later phase, from
"a third-party system observed this". The mirror (introspection / dreaming) reads
AUTHORED only; that firewall keeps algorithmic exhaust out of the owner's reflection and
out of the behavioral baselines (§15).
"""

from __future__ import annotations

from enum import StrEnum


class Provenance(StrEnum):
    AUTHORED = "authored"        # owner wrote it. Ground truth, immutable, feeds the mirror.
    INTERPRETED = "interpreted"  # system inference over other data. Derived, regenerable, marked.
    # RESERVED — not ingested yet. Third-party behavioral exhaust (Data Portability export,
    # web/social history, sensor streams). Low-trust, ASSISTANT-TIER ONLY, quarantined from
    # the mirror and from behavioral baselines (§15). Lands Phases 3+; defined now so stores
    # and queries are provenance-aware from the start (cf. the dormant sensor schema).
    OBSERVED = "observed"


# What the introspective mirror / dreaming agent is permitted to read (the firewall).
#
# The load-bearing structure is exactly this SET — `MIRROR_READABLE` — not a trust *preorder*
# (gap G8). Earlier drafts asserted a provenance preorder ≼, but no code orders the classes,
# and `INTERPRETED` is a *derived* axis orthogonal to trust (it neither out- nor under-ranks
# `OBSERVED`), so a single trust order would be fiction. Two facts are load-bearing, and both
# are now STRUCTURAL, not ordering-based:
#   1. Mirror-readability is membership in this downward-closed set — enforced by the typed
#      `MirrorView` (core/mirror.py): a non-MR view is unrepresentable (Invariant 6).
#   2. Provenance is invariant under derivation — the only way to mint an INTERPRETED datum is
#      the `DerivedStore`, which has no provenance parameter, so no pipeline can launder
#      observed/interpreted into authored. Promotion *up* to authored is a deliberate human
#      re-tag-from-raw (§8), never automatic.
# A richer trust ordering is deferred until classes that actually need ordering exist (the §1
# provenance-spectrum growth path: auth-solo / auth-dialogue / curated). Until then: a set.
MIRROR_READABLE: frozenset[Provenance] = frozenset({Provenance.AUTHORED})
