# Journal — bp-039 `CQ-scope`: the capability-scope typing layer (`core/scope.py` + `req()` on the five Views)

> The fresh-agent contract: a new session with only `plan.md` + this journal + the write-scope files
> must continue without re-asking. Checkpoint at every semantic boundary (criterion closed, commit,
> finding filed). Status flips are the orchestrator's, by hand.

## 2026-07-15 — GRADUATED (proposed), awaiting owner `proposed→ready` blessing

- Graduated by the orchestrator (opus, self-driven) from **ratified** `dn-capability-scope` §3
  Consequence 1 (owner ratified all three fable notes by hand this session; blessing flip committed
  first at `3f5591d`). The note licenses exactly ONE plan — the scope typing layer — and this is it.
- **Grounding done in-session** (one Explore subagent, to keep main context small — the >150k-context
  cost driver). Confirmed with `path:line` citations:
  - **No existing `Scope`/read-scope type** (§3 Q1) — the note's "Views carry no explicit scope type"
    holds. Five factories: `MirrorView.project` (`core/mirror.py:72`), `ReferenceView.over`
    (`core/reference_view.py:60`), `TemporalView.over` (`core/temporal_view.py:109`), `OpsView.over`
    (`core/ops_view.py:77`), `EffectView.admit` (`ops/effects.py:194`) — all frozen dataclasses w/
    classmethod factories → `SCOPE` attaches as a class constant, no factory/read touch.
  - **`core/` is flat** → new file is `core/scope.py` (not `core/query/scope.py`).
  - **The `W_world` reconciliation (§3 Q3 / §4):** the note's `NONE < SENSING < …` is NOT
    `ReversibilityClass` (`ops/effects.py:47-56`, which is `SENSING(0) < REVERSIBLE < IRREVERSIBLE`,
    no NONE). `NONE` is `ApprovalStrength.NONE`, a different enum. **Decision:** `core/scope.py`
    defines a NEW pure `WorldReach: NONE<SENSING<REVERSIBLE<IRREVERSIBLE`; the `ReversibilityClass →
    WorldReach` bridge is authored **ops-side** (`world_reach()` in `ops/effects.py`), preserving
    ops→core so `core/scope.py` imports nothing from ops. `ReversibilityClass` stays unchanged.
  - **SLICE anchor shared** (§3 Q4): `_resolve_default_commit` (`core/reference_view.py:111`), both
    Views route through it — the commit SHA IS the consistent cut; the type states it, changes nothing.
  - **`CoherenceReport` is `Inv`** (§3 Q5): `core/temporal_view.py:56-70` — count + two anchors, no
    division. Item 4's audit target.
  - Flagged: two MORE View-shaped types NOT in the note's five — `ObservedView` (`core/sensing.py:190`)
    + `DreamsView` (`core/dreams_view.py:44`) — scoped OUT (§9, §11).
- **Key scoping decisions (the graduation judgment):**
  1. **`req()` is a DECLARATION, not enforcement wiring** — a `SCOPE` class constant per View from the
     §2.4 table, guarded by a declared-vs-actual test. No live caller passes a granted scope, so reads
     stay **bit-identical** (the whole-plan falsifier). Wiring `minted = meet(parent, template)` into
     `factory.grant` is behavior change → **parked** (§11).
  2. **ONE plan, four blast-radius-ordered items:** Item 1 new `core/scope.py` (lowest radius) → Item 2
     property/law tests → Item 3 the five View retrofits + ops bridge (touches existing code) → Item 4
     Inv/Rate markers (independently approvable — the deferrable one; owner may drop it to the R1
     velocity build at `proposed→ready`). Items are tightly coupled (all read the same-session
     `core/scope.py`) — splitting into separate PLANS would force interface-inference, so they are
     items, not plans. Confidence it fits one Opus session: high (bp-037 precedent, same character).
- **Cost estimate:** opus 240k (bigger than bp-037's 180k — more distinct pieces — but same
  deterministic pure-typing, test-pinned, no-live-model character; self-driven lands ~0.5–0.8×). No
  fable (design banked/ratified), no xhigh.
- **Not started** — no code written; `proposed`. Owner blesses `proposed→ready` by hand, then
  `/build bp-039`. Budget note: week at 92% (relayed this session) — the BUILD is a separate session;
  right-size at build time (self-driven if week still tight, else consider delegation w/ pre-flight
  budget gate).

## 2026-07-15 — BUILD started (self-driven); Items 1 + 2 GREEN

- Owner blessed `proposed→ready` by hand; flipped `ready→in-progress` (`51d72f2`→build), active-plan
  pointer set. Read the §2 manifest: `ops/effects.py` + all five View files in full for exact forms.
- **Item 1 CLOSED — `core/scope.py`** (the pure algebra). `Scope=(Σ,E,T,A)` frozen dataclass +
  the four component lattices: `StratumScope` (downset of the refinement forest R; `of()` auto-closes
  downward — a grant over `reference` pulls in `reference_repo`; `top()`=R∖𝔇), `EdgeScope` ({F,D}),
  `TimeScope`=(`Clock`,`Window`) with the **partial** meet, `Authority`=`Privilege`×W_Σ(0/1)×`WorldReach`.
  `WorldReach` carries the **NONE floor** (§4 reconciliation — the code's `ReversibilityClass` is
  SENSING-floored; bridge stays ops-side, added in Item 3). `Tier` is `field(compare=False)` — a
  min-composed annotation, excluded from `==`/⊑ (so the lattice laws hold on the four coords). Firewall
  `Ideal`s + `admissible` (`DENYLIST_IDEAL`={FOUNDATION}); `SliceError` on cut-less multi-stratum point
  windows (COMMIT clock / explicit `cut` satisfies it); `common_refinement` clock poset (N parked →
  cross-clock meets raise `NoCommonClockError`). `DEPLOYED_WORLD_CEILING=NONE` (finding-0011). Pure-core:
  imports only stdlib — nothing from ops/edge/stores. **mypy core/scope.py: 0 errors.**
- **BUG caught + fixed mid-build:** `Scope.join` (a widening) used `window.meet` (narrows) for its
  time coord → broke the absorption law. Added `Window.join` (convex-hull widening; ALL annihilator,
  EMPTY identity, opaque→ALL) and switched `Scope.join` to it. Absorption now holds.
- **Item 2 CLOSED — `tests/unit/test_scope.py`** (24 tests, all green). Lattice laws (idempotent/
  commutative/associative/absorption) over an ENUMERATED population on ONE clock (COMMIT, int-bounded
  windows = clean lattice; no randomness); `a⊑b ⟺ meet(a,b)==a`; **delegation monotonicity** (`meet(parent,
  template)⊑parent` for every pair, + a wider-template-can't-widen-child witness — non-negotiable #6);
  cross-clock meet raises (both TimeScope + Scope level); SLICE rule (rejects cut-less multi-stratum
  point; COMMIT/explicit-cut satisfy; single-stratum needs none); firewall-ideal admissibility (denylist
  + a general curated-firewall); Σ downward closure; Authority min/max-per-chain; WorldReach NONE floor;
  W_Σ∈{0,1} guard; tier min-composition + compare=False; `req_admissible`=⊑.
- Next: **Item 3** (the five View `SCOPE` constants + the ops-side `world_reach` bridge — the ONLY
  items touching existing code; bit-identical reads the falsifier) → **Item 4** (Inv/Rate markers).

## 2026-07-15 — Items 3 + 4 GREEN; gate legs 1–4 pass; leg 5 (pytest) running

- **Item 3 CLOSED — the `req()` retrofit.** One `SCOPE: ClassVar[Scope]` per View, verbatim from the
  §2.4 table (verified against actual disposition): MirrorView (mirror_authored, {}, projection_event,
  read/0/NONE, STRUCTURAL); ReferenceView (reference_repo, {F}, commit, …, STATIC_GUARD); TemporalView
  (reference_repo, {F,D}, commit, …, STATIC_GUARD — the only View carrying D); OpsView (ops, {},
  last_write, …, STATIC_GUARD); EffectView (world, {}, now, read/0/world_reach(ceiling), STRUCTURAL).
  The ops-side `world_reach()` bridge added to `ops/effects.py` (ops→core; `ReversibilityClass`
  unchanged). `tests/unit/test_view_scopes.py` (11 tests) — table-match + disposition guards +
  `DEPLOYED_WORLD_CEILING is NONE` + SCOPE-is-a-ClassVar-not-a-field.
- **FALSIFIER FIRED (as designed) → finding-0084 (spec-fidelity, resolved).** The public `SCOPE`
  ClassVar tripped `test_reference_view.py:82`'s EXACT-public-surface assertion (its sibling
  `test_ops_view.py:34` uses the robust `public & FORBIDDEN == ∅` pattern and passed untouched). Reads
  are bit-identical (every read-VALUE assertion passes unchanged); only the surface ENUMERATION saw the
  new read-only constant. Resolution: widened write_scope by ONE file (`tests/unit/test_reference_view.py`,
  warrant finding-0084, recorded in the plan diff), added `"SCOPE"` to the expected set (no-mutator
  guarantee preserved). The layering-correct design REQUIRES the public class attr (EffectView.SCOPE
  must live ops-side; a core registry can't hold it without inverting ops→core), so the constant is
  correct — the exact-set assertion + the one-file write_scope miss were the defect.
- **Item 4 CLOSED — Inv/Rate result markers.** `Inv[T]`/`Rate[T]` (PEP 695, matching `core/provenance.py`
  house style) + Rule CLOCK (`rate_under` — a Rate on κ needs a scope clocked on κ, else
  `ClockMismatchError`; a Rate is unconstructable without its clock). Audit: `CoherenceReport` is Inv
  (count + two anchors, structurally NO float/ratio field). 4 tests in test_scope.py.
- **BIT-IDENTICAL READS PROVEN:** all pre-existing View suites green (test_mirror, test_ops_view,
  test_reference_view [w/ the one finding-0084 line], test_temporal_view, test_effects,
  test_temporal_view_live). New: test_scope.py (28) + test_view_scopes.py (11) = 39.
- **GATE (5-leg, run separately):** LEG 1 ruff — PASS (StrEnum + PEP695 generics to match house style;
  full E501 reflow pass). LEG 2 `mypy core agents eval ops scheduler scripts` — **0 issues, 187 files**
  (186→187, the new core/scope.py). LEG 3 argless mypy — **69, HELD** (new test files added zero type
  errors — the tooth held, no re-baseline). LEG 4 ops.type_gate — OK (core/scope.py imports no ops;
  tier-2 membership + bare-ignore scan clean). LEG 5 pytest -q — RUNNING (background).
- **Doc-debt (optional, NOT owed):** `site/api/core.md` could gain `::: core.scope` for API-doc
  completeness — but reference_view/temporal_view are themselves absent there (precedent), an
  unreferenced module doesn't break the `pages` build (stays green), and the file is out of write_scope.
  Left for a future docs sweep.
- Next: await leg 5 green → orchestrator flips `in-progress→complete`, seals with cost.actual.

## 2026-07-15 — AWAITING leg 5 (full pytest, background)

- All four items committed (`f9897b5`); gate legs 1–4 GREEN. Leg 5 (`pytest -q`, full suite ~1140
  tests) running in the background — buffers until done. **Re-entry for a fresh agent:** on leg-5
  green, flip bp-039 `in-progress→complete` (orchestrator, non-blessing), clear `.claude/state/active-plan`,
  and seal with `cost.actual` (get fresh /usage). If leg 5 shows a failure OTHER than the two known-flaky
  live dream e2e (`test_dream_v2_live`/`test_dreaming_live`, TimeoutError on a loaded box — the only
  tolerated ones), fix forward before completing. No item is open; only the final gate confirmation
  and the status flip remain.

## 2026-07-15 — SEALED · bp-039 COMPLETE (leg 5 green, all falsifiers held)

- **LEG 5 GREEN — pytest 1177 passed / 8 skipped, exit 0** (1138→1177 = +39 new; even the two
  known-flaky live dream e2e passed this run). All FIVE gate legs green. Zero failures.
- **Orchestrator flipped `in-progress→complete`** (non-blessing), cleared `.claude/state/active-plan`,
  set `completed: 2026-07-15`. cost.actual sealed: opus, self-driven, ~130k est (~0.54× — pending
  owner /usage to price dollars/week precisely; next-session relay).
- **All plan falsifiers held:** bit-identical reads (existing View suites unmodified but for the one
  finding-0084 line); cross-clock T-meet raises (never guesses); delegation monotone (meet(parent,
  template) ⊑ parent, every pair — #6); SLICE rejects cut-less multi-stratum point; denylist FOUNDATION
  ungrantable; `core/scope.py` imports nothing from ops (layering held — bridge ops-side).
- **The note's §3 Consequence 1 is DISCHARGED:** the scope typing layer exists. Consequences 2–4 are
  now expressible (delegation law testable — wiring parked §11; instruments declare Inv/Rate(κ) at
  graduation — R1 velocity is the first Rate customer; the fable geometry units consume T's clocks).
- **Open follow-ons (parked, not owed):** CS-a (materialize N), the factory.grant wiring, the sensor
  write-dual, ObservedView/DreamsView scope (§11); optional `site/api/core.md` `::: core.scope` stub.
- Fresh-agent test: PASSES — plan + this journal + write-scope files fully reconstruct the build.
