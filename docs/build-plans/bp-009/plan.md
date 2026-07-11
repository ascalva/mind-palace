---
type: build-plan
id: bp-009
status: complete
design_ref:
  - docs/design-notes/type-system-as-core-audit.md
contract: builder
write_scope:
  - "core/provenance.py"
  - "core/typedshims/**"
  - "tests/**"
  - "docs/findings/**"
  - "docs/build-plans/bp-009/**"
session_budget: 1
depends_on: [bp-006]
parallelizable_with: [bp-007]
created: 2026-07-11
updated: 2026-07-11
links:
  - docs/brainstorms/code-as-sensor-stream.md
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — B-3: the static-shadow spike — `Authored[T]` / `Derived[T]` in the type grammar

> **Every section below is required.** N/A is an accountability act.

## 0. Mode & provenance

Graduated from ratified `type-system-as-core-audit.md`, B-3. A SPIKE: it measures churn
and may legitimately end **parked with evidence** rather than merged — the falsifier is
first-class here. Readiness blessing is the owner's.

## 1. Objective

Express the label-monotonicity static shadow (§2.4) as generic tags in
`core/provenance.py` and measure, on real call sites, whether the tagging pays for
itself.

## 2. Context manifest

1. `docs/design-notes/type-system-as-core-audit.md` — §2.4 (the shadow), B-3 + falsifier.
2. `core/provenance.py` — the Provenance enum, `MIRROR_READABLE`, the promotion comment
   block ("only way to mint INTERPRETED … is DerivedStore").
3. `core/mirror.py` — `MirrorView` (the structural firewall the tags must strengthen,
   never duplicate).
4. `core/stores/derived.py` — `DerivedStore.add` (provenance hardcoded; the mint site).

## 3. Investigation & grounding

- **Q1 — where do provenance values flow as types today?** They don't — provenance is a
  `StrEnum` VALUE on rows (`core/provenance.py:42-59`); enforcement is structural at view
  construction (`MirrorView.__post_init__`, `core/mirror.py:62-70`) and at the mint site
  (`DerivedStore.add`, no provenance param, `core/stores/derived.py:177-216` per the
  2026-07-10 survey). The shadow adds a _compile-time_ lane the runtime checks keep owning.
- **Q2 — is there a promotion call site to constrain?** Not yet — promotion is
  verdict-gated (I1) and unbuilt (recursive-strata parked). The spike therefore tags
  **reads** (what a consumer may accept) rather than promotion; the `promote()` signature
  from §2.4 lands as a typed stub the future implementation must satisfy.
- **Q3 — tagging grain?** The note's open question (four-class axis vs binary). The code
  does not settle it; the axis note's PD-5/a₁ discussion suggests classes stay data.
  **Default: binary `Authored[T]`/`Derived[T]`** — the checker's grammar is unordered
  (note, Open questions), so the four-class order can't be expressed anyway.

**Additional risks or questions surfaced during reading:** variance (the note's "tagging
depth" question) — containers of tagged values get sharp; the spike stops at value-level
tags.

## 4. Reconciliation

- `core/provenance.py` promotion comment ("Promotion _up_ to an authored class is a
  human act") → **cross-ref: extension** — the typed `promote()` stub cites it; no
  behavioral change.

## 5. Write scope

Prose mirror: `core/provenance.py` (tags + stub), shims if generics need them, tests,
findings, own dir. **Out of scope:** every consumer refactor beyond the measured sample
(the spike measures churn on a SAMPLE, it does not convert the codebase); MirrorView
semantics; any promotion implementation.

## 6. Interfaces pinned inline

§2.4 target shape (verbatim from the note):

```python
def promote(x: Derived[T], cap: OwnerVerdict) -> Authored[T]: ...
```

B-3 falsifier (verbatim): _"if tagging requires warranted ignores at more than a handful
of sites, the static-shadow claim is weakened; park the spike with that evidence attached
rather than forcing the encoding."_

Current enum (pinned): `AUTHORED_SOLO, AUTHORED_DIALOGUE, CURATED, INTERPRETED,
DERIVED_STRATUM (reserved), OBSERVED` with `MIRROR_READABLE = frozenset({AUTHORED_SOLO,
AUTHORED_DIALOGUE})` — `core/provenance.py:42-78`.

## 7. Items

### Item 10 — the tags + typed stub

- **Objective:** `Authored[T]`/`Derived[T]` generics + `promote()` stub in
  `core/provenance.py`, unit-tested at the type level (mypy fixtures: accidental
  promotion is a type error).
- **Files:** `core/provenance.py`, `tests/unit/test_provenance_tags.py`.
- **Acceptance test:** a fixture calling `promote(derived_value)` without the capability
  fails mypy; with it, passes; runtime behavior of the module unchanged (ratchet green).
- **Falsifier:** the tags cannot express the constraint without `cast` at the definition
  site itself — park immediately.
- **Invariant(s):** MIRROR_READABLE untouched; no runtime semantics change.
- **Touches stored data?** no **Parallelizable?** no **Depends on:** bp-006

### Item 11 — churn measurement on a real sample

- **Objective:** apply the tags across ONE real seam (recommend: `MirrorView.project` →
  Librarian read path) and count warranted ignores + signature churn.
- **Files:** the sampled seam, journal (the measurement), a finding with the verdict.
- **Acceptance test:** journal table: sites touched, ignores required, checker catches
  demonstrated; finding filed with keep/park recommendation.
- **Falsifier:** the note's own — "more than a handful" of warranted ignores ⇒ park with
  evidence; the spike SUCCEEDS by reporting honestly either way.
- **Invariant(s):** sampled seam behavior unchanged.
- **Touches stored data?** no **Parallelizable?** no **Depends on:** Item 10

## 8. Math carried explicitly

- **Provenance tags as a two-point meet-semilattice** — _measures:_ whether the
  authored/derived distinction survives the type grammar (meet = Derived; promotion is
  the only up-move and demands the capability object). _valid when:_ tags carry no
  order beyond the two points (the four-class axis order is deliberately NOT encoded —
  checker grammar is unordered). _fails its keep if:_ Item 11's churn measurement trips
  the falsifier — then the shadow is wrong-grained and the evidence parks it.

## 9. Non-goals

Codebase-wide tag adoption; four-class tagging; container variance; implementing
promotion; touching DERIVED_STRATUM semantics.

## 10. Stop-and-raise conditions

Tagging forces a change to `MIRROR_READABLE` or any view's runtime check (the shadow must
never weaken the structural layer — spec-defect finding, stop); variance question becomes
load-bearing (owner question, park Item 11's remainder).

## 11. Parked decisions

| Decision      | Default recorded        | Rejected alternatives (why)                   | Re-entry condition                                                                     |
| ------------- | ----------------------- | --------------------------------------------- | -------------------------------------------------------------------------------------- |
| tagging grain | binary Authored/Derived | four-class (order inexpressible in grammar)   | axis-note ratification revisits; or a consumer needs a₂ distinct from a₃ at type level |
| tagging depth | values only             | containers (variance cost before value shown) | Item 11 evidence shows container flows dominate                                        |

## 12. Dependency & ordering summary

bp-006 → this (needs strict-green provenance module). Items 10 → 11. Parallelizable with
bp-007 (disjoint write scope). Independent of bp-008.
