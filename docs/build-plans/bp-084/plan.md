---
type: build-plan
id: bp-084
status: proposed
design_ref:
  - docs/design-notes/inner-outer-core.md
contract: builder
write_scope:
  - core/temporal/boundary.py
  - core/temporal/complex.py
  - core/temporal/acquire.py
  - core/integrator.py
  - core/integrator_math.py
  - core/recursion_ops.py
  - core/rings.py
  - tests/unit/test_inner_ring.py
  - tests/unit/test_temporal_complex.py
  - tests/unit/test_temporal_operators.py
  - tests/unit/test_temporal_view.py
  - tests/unit/test_integrator.py
  - tests/unit/test_rotation_report.py
  - tests/integration/test_temporal_isolation.py
  - tests/integration/test_temporal_view_live.py
  - tests/integration/test_integrator_wiring.py
  - tests/integration/test_dialogue_ops.py
  - tests/integration/test_edge_partition.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 320k
  actual: null
depends_on: [bp-083]
parallelizable_with: []
created: 2026-07-21
updated: 2026-07-21
links:
  - docs/design-notes/inner-outer-core.md
  - docs/build-plans/bp-065/plan.md
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — S1: the temporal math enters the ring (math↔persistence splits, map +7 → 36)

> Graduated from ratified `dn-inner-outer-core` §2.6b / §3 (owner-ruled 2026-07-20T22:55Z: *"I
> would want the temporal math in the inner core"*). The SECOND licensed plan, **strictly after M0
> (bp-083)**. Shape pinned to bp-065 precedent: **the pure builder takes data; the store-reading
> acquisition seam moves one ring outward — the machinery calls core, core returns data.** No
> behavior change, no new mathematics. Acceptance is mechanical: the seven named modules enter the
> computed fixed point, forcing a +7 diff in `core/rings.py`.

## 0. Mode & provenance

Investigation and planning produced this; implementation proceeds item-by-item on owner approval.
`proposed → ready` stays owner-only, by hand. Preempts nothing sequenced. **Hard prerequisite:
M0 (bp-083) sealed** — S1's whole acceptance is a diff against the `INNER` map bp-083 creates.

## 1. Objective

Relocate the four store-reading seams off `core/temporal/{boundary,complex}.py`,
`core/integrator.py`, and `core/recursion_ops.py` — one ring outward — so that the seven modules
`core.integrator`, `core.recursion_ops`, `core.temporal` (pkg), `core.temporal.boundary`,
`core.temporal.complex`, `core.temporal.operators`, `core.temporal.superconnection` enter the
computed inner fixed point (map +7 → 36), with byte-identical behavior.

## 2. Context manifest

Read whole, in order:

1. `docs/design-notes/inner-outer-core.md` §2.6b — the ruling, the four grounded seams (verbatim
   line cites below), the +7 computed preview (36 strict / 49 lax, gap 13), the DRY obligation,
   falsifier F10.
2. `docs/build-plans/bp-065/plan.md` — the math/acquisition split precedent: clean break, no alias
   wrappers, P4 no-silent-change discipline.
3. `core/temporal/boundary.py` — whole; the seam is `supersession_poset(version_store, doc_ids)`
   at `:114-117` reading `VersionStore.history`; the pure core `poset_from_chains(chains)` at `:98`
   already exists; `from core.stores.versions import VersionStore` at `:25` is the import to shed.
4. `core/temporal/complex.py` — whole; `build_citation_complex(ref_store, ...)` at `:59`; the
   store import `from core.stores.reference_edges import ReferenceEdgeStore` at `:34` to shed; the
   flag-complex math already delegates to inner `core/complex/hodge` at `:33` (the safe direction).
5. `core/integrator.py` — whole; `import sqlite3` at `:32`; store-type imports at `:38-39`; the
   raw `ledger: sqlite3.Connection` dataclass field at `:136`; the lazy store opens at `:223-224`.
6. `core/recursion_ops.py` — whole; `import sqlite3` at `:53`; `from core.stores.derived import
   DerivedStore` at `:62`.
7. `tests/unit/test_inner_ring.py` + `core/rings.py` (from bp-083) — the ratchet S1's +7 lands
   against.

## 3. Investigation & grounding

Touches existing code; grounded at HEAD (`d08da37`) — every seam re-verified this graduation:

- **Q1 — boundary.py seam.** CONFIRMED: `poset_from_chains` (`:98`, pure, store-free) and
  `supersession_poset` (`:114-117`, reads `VersionStore.history`) are already split within the
  module; the store touch is the wrapper + the `:25` import. The relocation moves the wrapper out;
  the pure poset stays and `boundary.py` sheds `:25`.
- **Q2 — complex.py seam.** CONFIRMED: one function, `build_citation_complex(ref_store, ...)`
  (`:59`); the store import is `:34`. The math (`boundary_1/2`, `edge_index`, `harmonic_basis` from
  `core.complex.hodge`, `:33`) is inner-safe already.
- **Q3 — integrator.py seam.** CONFIRMED: `import sqlite3` (`:32`), store imports (`:38-39`), and
  a `ledger: sqlite3.Connection` field on a dataclass beside gauge math (`:136`). The split extracts
  the pure gauge math into an inner-eligible module (`core/integrator_math.py`, proposed) and leaves
  the ledger-holding acquisition part in `core/integrator.py` (outer). Lazy opens at `:223-224`.
- **Q4 — recursion_ops.py seam.** CONFIRMED at grounding (beyond the capsule): `import sqlite3`
  (`:53`) AND `from core.stores.derived import DerivedStore` (`:62`). The seam includes BOTH.
- **Q5 — where do the seams land? (the one open placement.)** The note pins the *direction*
  (outward, still core), not exact homes. Proposed: the two temporal wrappers →
  `core/temporal/acquire.py` (new, outer — reads the two stores, calls the inner pure builders);
  integrator's pure gauge math → `core/integrator_math.py` (new, inner), the ledger/witness
  machinery stays in `core/integrator.py` (outer); recursion_ops' persistence → **audit
  `core/stores/*` first (§2.6b DRY obligation)** before minting anything. The code does not settle
  whether an existing store already covers recursion_ops' inline sqlite — that audit is Item 4's
  first act, and Stop-and-raise fires if a new persistence module seems needed (owner
  reuse-before-reimplement rule).

**Additional risks:** F10 — if a named module fails to enter the fixed point after its seam
sheds, a coupling exists beyond the audited seams (stop, file finding, re-ground). Import cycles:
the outer `acquire`/`integrator` modules import the inner pure modules (safe direction); the inner
modules must import neither (assertion B2 catches a regression).

## 4. Reconciliation

- **Committed code corrected (called out, carried by items — not slipped in):** four modules lose
  store-reading responsibility. Each is a **banner-on-correction** in the moved code's docstring:
  *"the store-reading seam relocated to `<outer home>` (bp-084, inner-ring promotion); this module
  is now inner — it takes data, it does not acquire it."*
- **Importers repointed, no alias wrappers (bp-065 clean-break):** every caller of a moved symbol
  is repointed in the same commit. `core/temporal/atlas.py`, `eval/harness/*`, and the tests in
  write_scope import the moved wrappers; each import line moves to the new home. No compatibility
  shim (`boundary.supersession_poset` re-export) — the owner's no-alias rule.
- `core/rings.py` — **cross-reference-on-extension**: the +7 lands as an `INNER` diff; the module
  comment notes S1 as the first promotion wave.

## 5. Write scope

The four seam-source files; the two proposed new outer/inner homes (`core/temporal/acquire.py`,
`core/integrator_math.py`); `core/rings.py` (the forced +7 diff); `tests/unit/test_inner_ring.py`
(the ratchet asserts the new membership). **Retrofit test files carried because they pin the
moved import surface** (findings 0071/0072/0075/0084): the unit tests
`test_temporal_complex`, `test_temporal_operators`, `test_temporal_view`, `test_integrator`,
`test_rotation_report`, and the integration tests `test_temporal_isolation`,
`test_temporal_view_live`, `test_integrator_wiring`, `test_dialogue_ops`, `test_edge_partition` —
all import one or more moved symbols and redden on the clean-break repoint. Deliberately OUT of
scope: `core/stores/**` (S1 reuses, never rewrites the store layer — the DRY audit reads it), the
outer ratchet test, the denylist. A store rewrite is a different plan.

## 6. Interfaces pinned inline

**The moved seams — signatures preserved exactly (zero behavior change):**
```python
# core/temporal/boundary.py:98  (STAYS — inner, pure)
def poset_from_chains(chains: dict[str, list[int]]) -> SupersessionPoset: ...
# core/temporal/boundary.py:114 (MOVES → core/temporal/acquire.py — outer)
def supersession_poset(version_store: VersionStore, doc_ids: list[str]) -> SupersessionPoset: ...
# core/temporal/complex.py:59   (MOVES → core/temporal/acquire.py — outer)
def build_citation_complex(ref_store: ReferenceEdgeStore, *, ...) -> ...: ...
# core/integrator.py:136        (the ledger field stays with the OUTER acquisition part)
    ledger: sqlite3.Connection
```
**The expected promotion set (§2.6b, Appendix A post-S1) — S1's acceptance:** exactly
`core.integrator`, `core.recursion_ops`, `core.temporal`, `core.temporal.boundary`,
`core.temporal.complex`, `core.temporal.operators`, `core.temporal.superconnection` enter `INNER`;
map becomes 36 strict / 49 lax; packaging-debt gap unchanged at 13.

## 7. Items

Ordered by blast radius (read-only sensing → reversible writes; nothing irreversible/external).

### Item 3 — DRY audit + seam-home decision (read-only)
- **Objective:** confirm no existing `core/stores/*` already covers recursion_ops' inline sqlite
  and integrator's ledger; decide the exact homes (`acquire.py` / `integrator_math.py` / an
  existing store).
- **Files:** none written (a reading pass recorded in the journal).
- **Acceptance test:** the journal records, per seam, the chosen home + the DRY finding ("no
  existing store covers X" with a `path:line`, or "reuse `stores.Y`").
- **Falsifier:** a new persistence module is proposed while an existing store already covers it ⇒
  the owner's reuse rule is breached — stop-and-raise instead.
- **Invariant(s):** no writes.
- **Touches stored data?** No. **Parallelizable?** No. **Depends on:** bp-083.

### Item 4 — relocate the temporal seams (boundary + complex)
- **Objective:** move `supersession_poset` and `build_citation_complex` to `core/temporal/acquire.py`
  (outer); shed `:25`/`:34` store imports from the now-inner modules; repoint importers.
- **Files:** `core/temporal/boundary.py`, `core/temporal/complex.py`, `core/temporal/acquire.py`
  (new), plus the temporal test files repointed.
- **Acceptance test:** `uv run pytest tests/unit/test_temporal_complex.py tests/unit/test_temporal_operators.py
  tests/unit/test_temporal_view.py tests/integration/test_temporal_isolation.py` green; the two
  modules import no `core.stores.*`.
- **Falsifier (F10):** `core.temporal.boundary`/`.complex`/`.operators`/`.superconnection`/`temporal`
  fail to enter the computed set after the shed ⇒ residual coupling; stop, file finding.
- **Invariant(s):** byte-identical behavior (same data out); `test_temporal_isolation`'s
  safe-direction pin (`core/complex/**` never imports temporal) still holds.
- **Touches stored data?** No (reads only, unchanged). **Parallelizable?** No. **Depends on:** Item 3.

### Item 5 — split the integrator + recursion_ops persistence out
- **Objective:** extract integrator's pure gauge math to `core/integrator_math.py` (inner); leave
  the `ledger`/witness acquisition in `core/integrator.py` (outer); relocate recursion_ops'
  sqlite + `stores.derived` seam per Item 3's decision; repoint importers.
- **Files:** `core/integrator.py`, `core/integrator_math.py` (new), `core/recursion_ops.py`, the
  integrator test files repointed.
- **Acceptance test:** `uv run pytest tests/unit/test_integrator.py tests/unit/test_rotation_report.py
  tests/integration/test_integrator_wiring.py` green; `core.integrator_math` and
  `core.recursion_ops` import no sqlite3 / `core.stores.*`.
- **Falsifier (F10):** `core.integrator`/`core.recursion_ops` fail to enter the computed set.
- **Invariant(s):** the C-coverage / integrator wiring behavior is unchanged (the launcher still
  wires the same object); zero behavior change.
- **Touches stored data?** No. **Parallelizable?** No. **Depends on:** Item 4.

### Item 6 — force the +7 map diff, prove membership
- **Objective:** update `core/rings.py`'s `INNER` to the recomputed 36-member set; assertion 1
  forces the diff.
- **Files:** `core/rings.py`, `tests/unit/test_inner_ring.py` (only if the assertion needs the new
  known-membership additions to its honesty guard — else untouched).
- **Acceptance test:** `uv run pytest tests/unit/test_inner_ring.py` green with exactly the seven
  added; the full local CI gate (ruff + check_imports + mypy floors + ops.type_gate + pytest green
  gate) green; the outer ratchet count unchanged.
- **Falsifier (F10):** any of the seven missing, or any eighth unexpectedly present.
- **Invariant(s):** map monotonic (grows only; §2.4-D4); outer ratchet untouched (every moved
  import is core-internal, none among the 19).
- **Touches stored data?** No. **Parallelizable?** No. **Depends on:** Item 5.

## 8. Math carried explicitly

- **The supersession poset / citation complex / gauge math** — unchanged objects; S1 relocates
  *where they are called from*, never *what they compute*. *measures:* (unchanged). *valid when:*
  the pure builder receives exactly the data the old wrapper read. *fails its keep if:* any
  acceptance test's output differs from pre-split (P4 no-silent-change: the relocated seams must
  produce identical data).

## 9. Non-goals

No new mathematics. No behavior change. No store-layer rewrite (reuse only). No physical
`core/kernel/` move (M2). No touch to the P9 store-typed View pair (`chat_events`, `dreams_view` —
parked, their store imports are load-bearing types, not relocatable seams). No outer-ratchet change.

## 10. Stop-and-raise conditions

- A new persistence module seems needed while a `core/stores/*` already covers it ⇒ **stop**
  (owner reuse rule; the §2-manifest DRY obligation).
- A named module won't enter the fixed point after its seam sheds ⇒ **stop** (F10): coupling
  beyond the audited seams; file a finding, re-ground — never force `INNER` to include a
  still-impure module.
- Any acceptance test output differs from pre-split ⇒ **stop**: this is not zero-behavior-change.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| P9 store-typed View vocabulary (`chat_events`, `dreams_view`) | stays outer | relocate store types inward (load-bearing signature types, not seams — a design question with the TYPE_CHECKING stance) | S1 seal proves the pattern AND a follow-on wants them; decide P6 first |
| recursion_ops persistence home | Item 3's DRY audit decides | invent a new store (may duplicate an existing one) | audit shows no store covers it |
| sigma_star/conductance graph-math split | named, NOT licensed here | do it in S1 (entangled with the graph `__init__` packaging remedy + Track-2) | graduates separately |

## 12. Dependency & ordering summary

Items strictly sequential: 3 → 4 → 5 → 6. **Depends on bp-083 (M0)** — hard. Not parallelizable
with anything (it writes `core/rings.py`, which bp-083 owns first, and repoints core-wide imports).
Blast radius: read-only audit → in-core relocations (reversible, zero-behavior) → the map diff.
The outer ratchet neither gates nor is gated by S1 (every moved import is core-internal).
