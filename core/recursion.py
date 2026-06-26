"""Recursion-decay bound for interpreted artifacts (Invariant 10; BUILD-SPEC §8 analogy).

*Interpretation is hypothesis; tame the recursion; evidence decides, not persuasion.*

An interpreted artifact's confidence may not compound with derivational distance from ground
truth — it must **decay**. With derivation depth `d(κ)` (0 = an authored leaf; computed by
`DerivedStore.depth`, well-defined because the derivation graph is acyclic by construction —
gap G2) and a base grounding score `g(κ) ∈ [0, 1]`, the bound is

        c(κ) ≤ γ^{d(κ)} · g(κ),     γ ∈ (0, 1).

Because γ < 1, a self-referential loop loses potency every pass instead of amplifying — the
formal shape of taming "the stack-overflow of a mind thinking only about itself". This module
is the small, pure home of that bound: depth + γ + g make `c` *computable*. The adjudicator
that assigns `g` and ranks claims is a later phase; this is its decay law and the γ bound it
must use.

γ bound (gap G7): γ is held small enough that a depth-3 artifact is *clearly subordinate* to
ground truth — at the default γ = 0.5, depth-3 confidence is capped at 0.125·g (an eighth),
so third-order interpretation cannot out-rank a first-order reading of the same evidence. It
is a declared constant here, not a magic number scattered at call sites; calibrate on the real
corpus before the adjudicator ships.
"""

from __future__ import annotations

# γ ∈ (0,1): the per-depth confidence discount (gap G7). Small enough that depth-3 (γ³=0.125)
# is plainly subordinate to ground truth. A single declared bound, not a scattered literal.
DEFAULT_GAMMA: float = 0.5

# λ ≥ 0: the corroboration bonus in the base confidence c₀(κ) = g·(1 + λ(|Agr(κ)|-1)) — each
# additional *independent* agreeing source nudges confidence up (gap G7). BOUND: small, λ ≤ 0.25,
# so corroboration tilts a tie but never lets agreement masquerade as ground truth — the hard
# ceiling c ≤ γ^d·g still dominates. A declared constant awaiting calibration on the real corpus
# (the adjudicator that consumes it is a later phase); not a magic number at a call site.
DEFAULT_LAMBDA: float = 0.1


def decay_bound(depth: int, *, grounding: float = 1.0, gamma: float = DEFAULT_GAMMA) -> float:
    """The confidence ceiling c ≤ γ^depth · g for an artifact at derivation `depth` with base
    grounding `g` (Invariant 10). Non-increasing in depth for γ ∈ (0,1) and g ≥ 0 — confidence
    strictly decays away from authored ground, never compounds."""
    if not 0.0 < gamma < 1.0:
        raise ValueError(f"gamma must be in (0,1) for the decay to contract, got {gamma}")
    if depth < 0:
        raise ValueError(f"depth must be >= 0, got {depth}")
    if grounding < 0.0:
        raise ValueError(f"grounding must be >= 0, got {grounding}")
    return (gamma ** depth) * grounding
