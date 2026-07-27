---
type: finding
id: finding-0257
status: open
created: 2026-07-27
updated: 2026-07-27
links:
  - docs/design-notes/temporal-retrieval-algebra.md
  - docs/design-notes/erratum-relation.md
  - core/kernel/temporal/operators.py
  - core/temporal_view.py
  - docs/build-plans/bp-130/plan.md
ftype: discovery
origin_plan: orchestrator
route: orchestrator
resolution: null
---

# The temporal algebra is real code with no production caller — so `(I − Ε)` lands on a dead surface

## What

Grounding `dn-erratum-relation` §4 before graduating it established three facts that together
change what a plan against that section can honestly claim.

**1. The algebra was built.** `dn-temporal-retrieval-algebra`'s front matter still reads
`implementation: design-only` (`docs/design-notes/temporal-retrieval-algebra.md:5`). That is
**stale**: bp-032/bp-033 shipped the operators. They exist as executable numpy/scipy:

| symbol | path:line |
|---|---|
| `π_active` | `core/kernel/temporal/operators.py:55` `active_projection` |
| `σ_*` (0-chains) | `:63` `pushforward_0` |
| `σ_*` (1-chains) | `:75` `pushforward_1` |
| `σ^*` | `:112` `pullback_0` |
| `T_active` | `:121` `t_active` |
| `[d,τ]` curvature | `core/kernel/temporal/superconnection.py:40` |

**2. Almost none of it is called.** A repo-wide search excluding `tests/` and
`.claude/worktrees/` finds **zero production callers** for `active_projection`, `pushforward_0`,
`pushforward_1`, `pullback_0`, and `t_active` — only the re-exports at
`core/kernel/temporal/__init__.py:31,37` and `tests/unit/test_temporal_operators.py:21`.
`sigma_node_map` (`:32`) is the sole algebra symbol with a live caller
(`core/temporal_view.py:223`).

**3. The one place the algebra meets a store has no consumer either.** `TemporalView`
(`core/temporal_view.py:158`) is scope-declared, anchor-resolving, read-only — and grep for
`TemporalView|open_coherence|open_rotation` outside `tests/` returns exactly one hit: a *docstring
mention* at `core/temporal/acquire.py:53`. **No production code calls it.**

**The actual retrieval path is algebra-free.** `core/ingest/index.py:122` `semantic_search` →
`core/stores/vectorstore.py:303` `VectorStore.search`, whose active projection is a literal SQL
prefilter — `clauses.append("current = true")` at `:321` — plus
`core/verdict/dispositions.py:101` `retracted()`, applied by `core/dreams_view.py:70`.

## Why it matters

`dn-erratum-relation:188` states: *"The extension is exactly the `(I − Ε)` factor — nothing else
changes."* That sentence is **true of the operator algebra and false as a statement about
observable retrieval behavior**, and the difference is not a quibble:

- A plan that adds `(I − Ε)` to `operators.py` is a ~5-line mathematically-correct change that
  **changes nothing any query returns**, because nothing reads `π_active`.
- A seal reporting "the validity projection is built" would be **literally true and practically
  misleading** — precisely the false-success shape `docs/brainstorms/the-false-success-rule.md`
  names, arrived at without anyone writing a false word.
- A user-visible `π_valid` is a **second SQL predicate** on `VectorStore.search`, not a matrix
  product. The note's "nothing else changes" is right about the algebra and wrong about the wiring
  — those are two different insertion points, and only one of them exists as a live path.

This also touches the standing owner rule *"wiring is part of finishing"* (flag-off ≠ done; the ON
switch must exist as part of the deliverable). The algebra shipped in bp-032/bp-033 without a
consumer, and this finding is the first time that has been written down as a gap rather than
observed and forgotten.

## Re-entry condition

`bp-130` proceeds and lands the factor **unwired**, matching `π_active`'s existing state. It says
so in its §0 rather than letting a seal imply live effect, and its §11 PD-E parks the wiring with
this finding as the carrier.

Re-entry: **when a plan exists that gives `TemporalView` (or the vector-search path) a real
consumer.** At that point `π_valid` is wired in the same act — and per PD-E, the vector-search
route is a genuine blast radius needing its own plan and its own acceptance, not a rider on the
operator change.

Separately: `dn-temporal-retrieval-algebra:5`'s `implementation: design-only` front matter is
**stale and should be corrected** — it is a ratified note, so owner's hand.

## Routing

`discovery` bearing on design ⇒ **route: orchestrator**. Two owner-level questions are batched
rather than blocking:

1. Should `dn-temporal-retrieval-algebra`'s `implementation:` field be amended to reflect that
   bp-032/bp-033 shipped it? (owner-hand; ratified note)
2. Is an unwired operator algebra acceptable as a resting state, or does the "wiring is part of
   finishing" rule apply retroactively to bp-032/bp-033's output — i.e. is a consumer **owed**?

Neither blocks the erratum wave. `bp-130` is honest about what it delivers either way.
