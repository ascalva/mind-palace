# bp-130 — journal

## Pre-build notes for whoever picks this up

- ⚑ **Read §0 before anything else. This plan builds a surface with no live consumer, on purpose.**
  `active_projection` (`π_active`) has **zero production callers**; `TemporalView` has **zero
  production consumers**. Your work will be mathematically real and observationally inert. That is
  the honest scope, filed as finding-0257. **Do not "fix" it by wiring `π_valid` into a View** —
  that is §9's non-goal and §10's stop condition, and it moves the inertness one layer out rather
  than removing it.

- ⚑ **The polarity is inverted relative to the operator you are copying.** `active_projection`
  puts `0.0` **on** its named set (superseded); `Ε` puts `1.0` **on** its named set (erratum
  targets). Get this backwards and `π_valid` serves *only* the rows asserted never true — the exact
  inverse of the intent, and it will pass a careless test. Item 1's falsifier is the direct
  assertion `Ε[v,v] == 1.0` and `π_valid[v,v] == 0.0` for a target node `v`. Write it first.

- ⚑ **The commutation identity is the substance; the diagonal-commutation is the decoy.**
  `π_active` and `Ε` commute trivially because both are diagonal (§3 Q4) — that property is free
  and proves nothing. The load-bearing claim is `Ε_{n+1} σ_* == σ_* Ε_n` (§3 Q3), which holds
  **iff σ carries the erratum set consistently** and is genuinely falsifiable. If your test suite
  only asserts the cheap one, you have tested nothing the note claims.

- ⚑ **The empty erratum set makes every property in this plan pass vacuously.** `Ε = 0`,
  `(I − Ε) = I`, `π_valid ≡ π_active`. Item 3 exists solely to make that impossible to ship.
  Use a **non-empty** target set in every fixture, and assert `π_valid ≠ π_active` explicitly.

- **The resurrection test is the note's own falsifier, not a nice-to-have.** Transport a 0-cochain
  *backward* via `pullback_0` to a pre-correction cut, apply `π_valid`, assert the corrected node's
  component is `0.0` — **and** assert it is non-zero under `π_active` alone. Both halves. The
  second is what proves the new factor did the work rather than the fixture being empty.

- **Name-collision trap:** `core/graph/sigma_star.py` is a **different** σ* (an abstraction
  ultrametric over a max spanning tree). Nothing to do with correspondence transport. Do not
  import it; do not "unify" them.

- **Inner ring.** `core/kernel/**` opens no store and imports no config. The erratum target set
  arrives as a `set[str]` parameter. bp-129 produces that set; this plan never reaches for it.

- **Run the mutation campaign; do not reason about it** (finding-0249). Four mutants in Item 3.
  Mutants 1 and 2 are the ones that matter — if either survives, the suite is green and `π_valid`
  demonstrably does nothing.

## Grounding carried in from graduation (verified, 2026-07-27)

- `active_projection` `operators.py:55` · `pushforward_0` `:63` · `pushforward_1` `:75` ·
  `pullback_0` `:112` · `t_active` `:121` · `sigma_node_map` `:32` (the only one with a live
  caller, `core/temporal_view.py:223`).
- `dn-temporal-retrieval-algebra:5` still reads `implementation: design-only` — **stale**;
  bp-032/bp-033 shipped these. Ratified note, so owner's hand; carried by finding-0257.
- The real retrieval path is algebra-free: `core/stores/vectorstore.py:321`'s literal
  `current = true` SQL prefilter, plus `core/verdict/dispositions.py:101` `retracted()`.
- `tests/unit/test_temporal_operators.py` holds **9** tests today.
