---
type: build-plan
id: bp-091
track: inner-outer-core
status: ready
design_ref:
  - docs/design-notes/inner-outer-core.md
contract: builder
write_scope:
  - core/**
  - tests/**
  - eval/**
  - ops/**
  - scheduler/**
  - agents/**
  - scripts/**
  - config/**
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 200k
  actual: null
depends_on:
  - bp-090
parallelizable_with: []
created: 2026-07-21
updated: 2026-07-21
links:
  - docs/design-notes/inner-outer-core.md
  - docs/findings/finding-0148.md
  - docs/build-plans/bp-089/plan.md
  - docs/build-plans/bp-090/plan.md
re_entry: null
supersedes: null
superseded_by: null
warrant: docs/findings/finding-0148.md
---

# Build Plan — K3: the S1 seven join the kernel (M2 wave 2)

> **Every section below is required.** N/A is an accountability act.

## 0. Mode & provenance

Graduated 2026-07-21 from the **ratified** `dn-inner-outer-core` §2.7 (K3 = "the
math-extraction promotions (the S1 seven …), likely the first K-wave after K1"). **Entry
gate:** the §2.7 per-wave stability condition (membership stable across ≥2 sealed plans)
closes for the seven only at **bp-090's seal** (bp-089 minted them; bp-090 is the second
sealed plan that leaves them unchanged) — hence `depends_on: [bp-090]`, hard. Same mode as
bp-090: investigation and planning only; `proposed → ready` is the owner's hand.

## 1. Objective

Relocate the seven S1-promoted modules into `core/kernel/**` (`core.integrator_math`,
`core.recursion_ops`, and `core.temporal` + its four pure math modules), repo-wide repoint,
both ratchets green per commit, zero behavior change.

## 2. Context manifest

1. `docs/design-notes/inner-outer-core.md` — §2.6b (the S1 seven + F10), §2.7 (move contract).
2. `docs/build-plans/bp-090/plan.md` + its journal — the wave-1 mechanics this repeats.
3. `core/rings.py` (post-K1 state) — the seven at their unchanged `core.*` names.
4. `docs/build-plans/bp-089/plan.md` — what S1 actually promoted (integrator_math, NOT
   integrator — the note-§2.6b-preview correction recorded in rings.py:44-49).
5. `tests/unit/test_inner_ring.py` — the per-commit gate.

## 3. Investigation & grounding

- **Q1 — the exact seven** (rings.py:70,75,82-86): `core.integrator_math`,
  `core.recursion_ops`, `core.temporal` (pkg init), `core.temporal.boundary`,
  `core.temporal.complex`, `core.temporal.operators`, `core.temporal.superconnection`.
  **Note the delta vs the note's §2.6b preview:** `core.integrator` stayed OUTER (keeps the
  sqlite `ledger` + acquisition API); the promoted gauge math lives in `core.integrator_math`
  — bp-089's honest landing, already forced through the map diff.
- **Q2 — closure.** AST scan at graduation (`438cef2`): the seven's core-rooted imports all
  resolve inside INNER — closed against kernel-so-far (post-K1 kernel) ∪ K3. Their imports of
  K1 members will already be `core.kernel.*` after bp-090's repoint (the seven are importer
  files in that wave). Recompute at build HEAD (Item 1).
- **Q3 — the temporal package splits** (two homes, §2.7): kernel gets
  `core/kernel/temporal/{__init__,boundary,complex,operators,superconnection}.py` (the
  existing pure init moves); the residue `core/temporal/` keeps `acquire.py` (the S1 seam
  home — store-reading, outer BY DESIGN) and `spine.py` (eval-coupled, outer permanently)
  under a NEW minimal init. `integrator_math.py` and `recursion_ops.py` are single-file
  moves.
- **Q4 — importer surface (recompute at HEAD).** Known consumers at graduation:
  `core/temporal_view.py` (`supersession_poset` via `core.temporal.acquire` — acquire STAYS,
  so only its `boundary`/`operators` imports repoint), `core/integrator.py` (imports the
  gauge math), tests, eval harness readers. Smaller than K1 by an order of magnitude.
- **Q5 — string refs.** Re-grep at HEAD for `"core.temporal…"`/`"core.integrator_math"`/
  `"core.recursion_ops"` strings (patch targets; the bp-090 Item-3 pattern reused).

**Additional risks:** `core.temporal.acquire` imports its sibling math (`boundary`) — after
the move that import crosses homes (`core/temporal/acquire.py` → `core.kernel.temporal.boundary`),
which is outer→inner, the ALLOWED direction (§ direction law). Verify the inner test's
direction check stays green; the reverse (kernel importing acquire) must not exist (it does
not — that was S1's whole point).

## 4. Reconciliation

- `core/rings.py` — the seven rename to `core.kernel.*` in the move commit(s), one
  reviewable diff, `# K3 (bp-091)` docstring note. **[cross-ref: extension]**
- `dn-inner-outer-core` §2.6b preview ("promotes `core.integrator` …") → **[no note edit —
  A8]**: the integrator_math correction is bp-089's recorded landing (rings.py:44-49); this
  plan carries it forward, citing, never editing the ratified text.

## 5. Write scope

Same globs as bp-090 (the repoint reaches the same packages; actual touched set is far
smaller — Q4). Same exclusions verbatim: `test_core_self_containment.py` forbidden
(pillar 2), `ops/import_lint.py` read-only, foundation denylist structural, `docs/**` and
`pyproject.toml` out. `core/temporal/acquire.py` and `core/temporal/spine.py` are edited
ONLY in their import lines (repoint) — their logic is untouchable here.

## 6. Interfaces pinned inline

The §2.7 move-commit contract, the map declaration shape, the full local CI gate, and the
inner-test obligations B1–B3 — **all pinned verbatim in bp-090 §6 and binding here
unchanged.** Additional pin — the S1 seam invariant (dn-inner-outer-core §2.6b): *"the pure
builder takes data; the store-reading acquisition seam moves one ring outward"* — K3 must
not move `acquire.py`/`spine.py` inward, whatever the scanner computes at HEAD.

## 7. Items

### Item 1 — recompute the manifest at build HEAD (read-only)

- **Objective:** fixed point + K3 closure + importer/string greps at HEAD; confirm bp-090
  sealed and the stability window is closed.
- **Files:** `docs/build-plans/bp-091/journal.md`.
- **Acceptance test:** inner test green pre-change; the seven present at `core.*` names;
  bp-090 `status: complete`.
- **Falsifier:** map mismatch (F6) or a K3 closure violation ⇒ stop, finding, re-graduate.
- **Invariant(s):** none touched. **Touches stored data?** no.
- **Parallelizable?** no. **Depends on:** bp-090 sealed.

### Item 2 — the moves (reversible)

- **Objective:** `git mv` the seven (temporal cluster + two leaf modules) with repoint +
  map rename + residue init, per the §6 contract, green per commit.
- **Files:** the seven (old→new), `core/temporal/__init__.py` (new residue),
  `core/kernel/temporal/**`, `core/rings.py`, importer files.
- **Acceptance test:** full suite + both ratchets green; outer count identical to baseline;
  zero old-name imports by grep; `core/kernel/` now holds born-30 ∪ the seven.
- **Falsifier:** outer count moves, or green requires touching `acquire.py`/`spine.py`
  logic ⇒ a coupling S1 missed (the note's F10 shape) — halt, finding.
- **Invariant(s):** no-laundering D1–D4; the §6 seam invariant; zero behavior change.
- **Touches stored data?** no. **Parallelizable?** no. **Depends on:** Item 1.

### Item 3 — string sweep + end-state verification (read-only after sweep)

- **Objective:** the F8 string sweep for the seven; then the full gate audit (bp-090
  Item-4 shape).
- **Files:** grep hits only; journal.
- **Acceptance test:** every §6 gate command exits 0; map == declared; seal checklist done.
- **Falsifier:** any gate red or stale-string failure ⇒ finding, no seal.
- **Invariant(s):** all of §6. **Touches stored data?** no.
- **Parallelizable?** no. **Depends on:** Item 2.

## 8. Math carried explicitly

N/A — pure relocation; the temporal mathematics is unchanged (S1 already proved the split
behavior-identical; this wave moves files only).

## 9. Non-goals

No K2 members. No `acquire.py`/`spine.py` logic changes. No P8 (spectral dependency), P9
(store-typed View vocabulary), or M3 flip. No ratchet/test-domain edits. No behavior change.

## 10. Stop-and-raise conditions

bp-090 not sealed (the stability window is OPEN — do not start). Recompute mismatch (F6).
Outer count delta. Any inward pull of `acquire`/`spine` (§6 seam invariant). Any pillar-
pinned file edit. Mid-build split urge ⇒ spec-defect finding + park.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| merging K3 into K1 as one wave | two waves, K3 gated on bp-090's seal | one mega-wave (violates §2.7's per-wave stability: the seven have only bp-089 behind them at mint time) | none — the ordering IS the design |
| P9 store-typed View vocabulary (`chat_events`, `dreams_view`, one hop out) | untouched | riding promotion attempts here (their imports are load-bearing types, not seams — §2.6b) | P9's own design pass |

## 12. Dependency & ordering summary

Strictly after bp-090 seals (hard gate — stability window + kernel-so-far closure). Items
linear 1→2→3. Conflicts with everything while running; nothing parallel. After this seals,
M2's remaining population is K2 (packaging-debt, remedy-gated) and the M3 flip — both
un-minted by design, each with its stated entry condition (completion-claims honesty:
**the ring program is NOT done when this plan seals**).
