"""The inner-ring map — a declaration forced to equal a computation (dn-inner-outer-core §2.4-A).

The inner core is the *founding language* of the system: the mathematics, the algebra, the
sacred-boundary vocabulary — **not** the austere plumbing (the owner's v2 ruling, §2.1). Membership
is **mechanical, never curated**: the inner ring is the maximal import-closed subset of ``core/**``
over the admissible base

    (stdlib ∖ ops.import_lint.NETWORK_MODULES ∖ PLUMBING_STDLIB) ∪ MATH_3P

under STRICT closure semantics (ancestor ``__init__``s counted — §2.3). This module only *declares*
that fixed point; ``tests/unit/test_inner_ring.py`` recomputes it at test time and forces
``INNER`` to equal the computation, both directions (§2.4-B1). ``INNER`` therefore changes only via
a reviewable one-file diff named in a plan's ``write_scope`` — every promotion/demotion is
plan-visible with zero new machinery (the map-monotonicity law, §2.4-D4).

This module is **inner by construction**: stdlib-only, side-effect-free at import, wires no read
path. It names modules (``"core.scope"``), never paths — so an M2 directory move (``core/scope.py``
→ ``core/kernel/scope.py``) is a mechanical rename here, not a re-computation.

The ``INNER`` set below was recomputed at build HEAD (bp-083); it equals the note's Appendix A
expectation of 29 exactly. If ``test_inner_ring_is_the_computed_fixed_point`` ever lands red, the
map — never the test — is stale: recompute at HEAD and edit ``INNER`` to match, never hand-edit
toward green (falsifier F6). See ``tests/unit/test_core_self_containment.py`` — the OUTER ratchet
(19 → 0 over all of ``core/``), a deliberately independent second scanner this file's test mirrors
but does not import (the redundant-sensor DRY exception, §2.4-B).
"""

from __future__ import annotations

# The pinned pure-math third-party libraries admitted into the base (§2.1). numpy/scipy are
# side-effect-free numerics; nothing else third-party is admissible.
MATH_3P: frozenset[str] = frozenset({"numpy", "scipy"})

# The v2 owner-ruled subtraction (§2.1, 2026-07-20T22:08Z): sqlite3 is stdlib, but the sqlite store
# layer is plumbing, not the founding language — subtracted so the ring means *meaning*, not
# import-austerity. This is the predicate's one home-in-core parameter; the network subtraction
# keeps its single home in ``ops.import_lint.NETWORK_MODULES`` (the test's computation sources it
# there). Membership stays computed — the lever is the predicate, not any module's assignment.
PLUMBING_STDLIB: frozenset[str] = frozenset({"sqlite3"})

# The inner ring — the strict-v2 fixed point over ``core/**``, recomputed at build HEAD (bp-083).
# 30 members = Appendix A's 29 + ``core.rings`` itself: this map module is stdlib-only, so it
# computes inner and the ratchet (§2.4-B1, "pure ⇒ the map must claim them") forces it to declare
# itself. That +1 is the only delta from the note's 29-member expectation (Appendix A predates this
# file). Module names, not paths (survives M2 renames).
INNER: frozenset[str] = frozenset({
    "core",
    "core.agent_scope",
    "core.complex",
    "core.complex.balance",
    "core.complex.curvature",
    "core.complex.hodge",
    "core.complex.laplacian",
    "core.complex.support",
    "core.complex_types",
    "core.config",
    "core.config.loader",
    "core.constitution",
    "core.ingest",
    "core.ingest.amend",
    "core.ingest.chunk",
    "core.ingest.logseq",
    "core.ingest.pipeline",
    "core.ingest.verify",
    "core.matching",
    "core.mirror",
    "core.provenance",
    "core.recursion",
    "core.rings",
    "core.scope",
    "core.selfcheck",
    "core.stores",
    "core.stores.rawstore",
    "core.stores.sourceset",
    "core.typedshims",
    "core.velocity_view",
})
