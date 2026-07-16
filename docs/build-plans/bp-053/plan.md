---
type: build-plan
id: bp-053
alias: clock-maps
status: proposed
design_ref:
  - docs/design-notes/global-event-clock.md   # RATIFIED — §2.3 clock laws C1–C4 + GC-N6; §2.9-3 (TG-a prerequisite) (GC-2)
contract: builder
write_scope:
  - core/temporal/spine.py
  - tests/unit/test_clock_maps.py
  - tests/integrity/test_clock_laws.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 200k
depends_on: [bp-051]
parallelizable_with: [bp-054]
created: 2026-07-16
updated: 2026-07-16
links:
  - docs/design-notes/capability-scope-algebra.md   # §2.1 the clock hierarchy this materializes
  - docs/design-notes/velocity-instruments.md       # VI-a — the Rate(κ) customers this gives clocks to
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — GC-2: the clock maps p_κ + N_s (every registered clock, lawful against the spine)

## 0. Mode & provenance
Graduated from RATIFIED `dn-global-event-clock`. Extends bp-051's spine (same file, SEQUENTIAL —
never parallel with it). This is the plan that materializes **N_s** — the standing prerequisite
of the locally-clocked superconnection (TG-a) and per-stratum diachronic anchoring.

## 1. Objective
Implement `p_κ : Ev → I_κ` for each registered `Clock` member against the spine; property-test
the clock laws (C1 monotone, C2 convex fibers, C3 read-clocks borrow the write frontier, C4
wall excluded); verify commit-as-range against the real repo; expose `N_s` restriction with
per-chain proper time (maximal-chain length — the finding-0090-corrected statement).

## 2. Context manifest (read in order)
1. `docs/design-notes/global-event-clock.md` §2.3 (WHOLE — the laws + GC-N6), §2.9-3/-6.
2. `core/temporal/spine.py` as merged by bp-051 (the surface this extends: `Spine.restrict`,
   `frontier`, `SpineEvent.stratum`).
3. `core/scope.py:171-217` — the `Clock` enum + `_FINER_THAN` + `common_refinement` (READ-ONLY
   here; bp-056 owns changes to it).
4. `docs/findings/finding-0090.md` — the proper-time statement this plan must implement
   correctly (per CHAIN, never per stratum).

## 3. Investigation & grounding
- **p_commit:** maps repo-backed events to the last commit at-or-before their position; a
  commit's fiber is the RANGE of events in that bundle — C2 verified against the actual git
  history + versions store (the grain caveat made a test).
- **p_{N_s}:** the restriction of the spine to stratum-tagged events (bp-051's `stratum` tag);
  `proper_time(a, b)` = maximal-chain length in the restriction, exact per chain, with the
  chain-qualification surfaced in the return type (e.g. `(length, chain_complete: bool)`) — the
  finding-0090 discipline, never a bare count sold as proper time.
- **Read-clocks (C3):** `projection_event` / `last_write` / `now` tick by borrowing the observed
  per-store frontier — implemented as a `frontier_at`-style lookup, no event minted.
- **Wall (C4):** structurally excluded — no `p_wall` exists in the module; `Rate(wall)` stays a
  telemetry concern (registry), not a spine clock.

## 4. Reconciliation
`core/scope.py`'s `common_refinement` currently returns None for cross-clock pairs (N parked).
This plan does NOT touch it (bp-056's seam). If a `Clock` member proves to have no lawful p_κ
over the spine (fiber non-convexity in the wild), that is a FINDING (math/design), not a quiet
special case.

## 5. Write scope
The three files in frontmatter. **OUT:** `core/scope.py` (bp-056), all stores, `eval/**`,
denylist.

## 6. Interfaces pinned inline
```python
# extends core/temporal/spine.py — GC-2's additive surface
class Spine:
    def p(self, clock: Clock, event_id: str) -> Hashable          # the coarsening; raises on WALL (C4)
    def fiber(self, clock: Clock, tick: Hashable) -> list[str]    # p_κ⁻¹(tick) — MUST be order-convex (C2)
    def n_s(self, stratum: str) -> "Spine"                        # alias of restrict(); the N_s object
    def proper_time(self, a: str, b: str) -> tuple[int, bool]     # (max-chain length, chain_complete)
    def frontier_at(self, store: str) -> int                      # C3 substrate for read-clocks
```

## 7. Items
### Item 1 — p_κ per registered clock + C-law property tests
- **Acceptance:** `uv run pytest tests/unit/test_clock_maps.py -q` green: for every registered
  clock with a p_κ, randomized event pairs satisfy C1 (`a ≼ b ⇒ p(a) ≤ p(b)`); every sampled
  fiber is order-convex (C2); `p(Clock.WALL, …)` raises (C4); read-clock ticks equal the
  observed frontier (C3).
- **Falsifier:** a non-convex commit fiber on the real repo (the range property broken) — the
  integrity test below catches it on main.
### Item 2 — commit-as-range verification + N_s + proper time
- **Acceptance:** `uv run pytest tests/integrity/test_clock_laws.py -q` green ON THE REAL
  STORES: commit fibers are ranges; `n_s` restrictions partition events by stratum tag;
  `proper_time` returns `chain_complete=False` whenever the two events are not on one chain
  (the finding-0090 test — a per-doc pair across docs must NOT report an exact proper time).
- **Falsifier:** `proper_time` reporting exact on a cross-chain pair (the exact conflation
  finding-0090 corrects); any N_s event missing from N.

## 8. Math carried explicitly
Laws (ratified §2.3, hold verbatim): C1 monotone; C2 `p_κ⁻¹(i)` order-convex; C3 read-clocks
sample the write frontier; C4 wall generates nothing. Proper time = maximal-chain length in the
restriction (exact per chain; identity with event count ONLY on a total chain — finding-0090).

## 9. Non-goals
No cuts (bp-055). No `common_refinement`/T-meet change (bp-056). No Rate re-binning machinery
(GC-N7 — a consumer concern once clocks exist). No new clock members.

## 10. Stop-and-raise
A registered clock with provably non-convex fibers → STOP, file a `math` finding (the law, not
the code, is in question). Any blessing: never.

## 11. Parked decisions
| Decision | Default | Re-entry |
|---|---|---|
| clocks for stores beyond the core seven | unwired, named | a consumer arrives |
| Rate re-binning helper | not built (GC-N7: re-measurement only, X2-bounded) | first cross-clock Rate consumer |

## 12. Dependency & ordering
Depends bp-051 (same file — sequential). Parallel with bp-054 (disjoint). Feeds bp-055 + bp-056
+ every VI-a/φ_coh clock customer. Blast radius: additive read-side.
