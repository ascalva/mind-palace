---
type: finding
id: finding-0028
status: routed           # open → routed → resolved | promoted
created: 2026-07-11
updated: 2026-07-12
links:
  - docs/design-notes/type-system-as-core-audit.md # B-3, §2.4 — the claim under test
  - docs/build-plans/bp-009/plan.md # the spike
  - docs/build-plans/bp-009/journal.md # full measurement tables + method
ftype: discovery
origin_plan: bp-009
route: orchestrator      # keep-or-park is a direction call; OwnerVerdict questions are design
resolution: null
---

# B-3 spike verdict: KEEP — the static shadow costs zero warranted ignores on the real seam

## What

bp-009 expressed §2.4's label-monotonicity shadow (`Authored[T]` / `Derived[T]` +
the `promote(x: Derived[T], cap: OwnerVerdict) -> Authored[T]` stub, landed in
`core/provenance.py`) and measured adoption churn on the real introspective read
seam by converting `MirrorView.rows() -> list[Authored[dict[str, Any]]]` in a
throwaway overlay clone (runtime checks and `MIRROR_READABLE` untouched; overlay
discarded, nothing landed outside write scope).

**Measured (full detail in the bp-009 journal):**

- **Warranted ignores: 0. Casts: 0.** The note's falsifier ("more than a handful
  of warranted ignores ⇒ park") is NOT tripped, by a wide margin.
- Converting the ENTIRE MirrorView consumer set — the seam is non-severable, a
  return-type change reaches every caller at once — cost **13 files, +37/−24
  lines**: 1 mint, 3 signatures, ~8 unwrap lines, 3 explicit mints in test
  fixtures. Three consumer files (`graph.py`, `interpreters.py`, `curator.py`)
  needed **zero** changes (pass-through call sites type-check unchanged).
- End state: core mypy 0 errors; repo-wide exact baseline parity (296; 0 new,
  0 resolved); ruff clean; overlay suite 750 passed / 4 skipped.
- **A real accidental-violation caught:** `tests/unit/test_complex.py:114` fed
  hand-built, never-projected rows straight into `note_centroids` — the
  MirrorView-bypass class that no runtime check guards today — and the checker
  flagged it `[arg-type]`. Pinned permanently as
  `tests/unit/test_provenance_tags.py::test_mirror_bypass_is_a_type_error`.
- **The shadow's honest limit, demonstrated live:** two Tier-2 test files fed
  bare rows invisibly to mypy (an untyped fixture returning `Any`; an
  unresolvable `fixtures.corpus` import) and surfaced only at runtime. The
  shadow is exactly as strong as the checked region (§2.1) — strict Tier-1 is
  tight; Tier-2 leaks through `Any`.

## Why it matters

- **The B-3 claim survives its own falsifier on real call sites**: the checker
  now removes the accidental-violation class (clustering un-projected rows) at
  authorship time, at a one-off cost of ~37 lines and zero suppressions. The
  recommendation is **KEEP**: graduate a follow-up conversion item whose
  write_scope covers the 6 core + 7 test files (out of bp-009's scope by design).
- Three riders the keep-decision should weigh:
  1. **The mint is not sealed** — `Authored(...)` is publicly constructible; the
     tag turns silent bypass into an explicit, greppable assertion rather than a
     proof of view-transit. A sole-mint discipline (B-7-adjacent grep gate, or a
     module-private mint owned by `MirrorView`) is an open design choice.
  2. **The encoding is not runtime-free** — a generic tag cannot be erased in
     Python's grammar (`NewType` is non-generic), so `rows()` allocates N small
     frozen wrappers per call. Negligible here, but "zero runtime cost" in §2.4
     applies to the checking, not the values.
  3. **Any-laundering evidence feeds the note's open "Tier-2 flag floor"
     question** — the two laundered feeder sites are concrete input for choosing
     the floor flags (e.g. `disallow_untyped_defs` in tests/fixtures, resolving
     the `fixtures.corpus` import for mypy).
- **OwnerVerdict design questions (unratified I1 taxonomy; placeholder answers
  none of them, recorded in the bp-009 journal):** does the capability unify
  with `core/verdict/` + `core/stores/verdicts.py`; does a verdict name its
  target authored class (AUTHORED_SOLO vs AUTHORED_DIALOGUE); per-value,
  per-artifact, or per-run scope.

## Re-entry condition

Nothing parked in bp-009 itself (both items completed). The conversion re-enters
when the owner graduates a follow-up item scoped to the measured consumer set;
the OwnerVerdict questions re-enter with the I1 verdict-taxonomy ratification
(recursive-strata unpark).

## Routing

`discovery`, route orchestrator: keep-or-park is a direction call on a ratified
note's B-item, and the OwnerVerdict questions are design-level (owner batch if
needed). Nothing here blocks other work — `core/provenance.py`'s tags + stub are
inert additions, landed strict-green on the bp-009 branch.

## Triage disposition (2026-07-12, /triage)

Routed orchestrator; disposition recorded, no owner question minted (non-blocking):

- **KEEP stands.** The B-3 falsifier was not tripped (0 warranted ignores / 0 casts across the
  full non-severable seam) — the note's own decision rule licenses keeping the shadow; the tags
  + `promote()` stub stay landed.
- **The conversion item** (the measured 6-core + 7-test consumer set) queues for the
  type-audit note's next `/graduate` wave — it wants its own scoped plan with `core/**` in
  write_scope, and it naturally pairs with finding-0029's Protocol-at-injection-boundary work
  (same seam family, same write_scope). Blessing `proposed → ready` stays owner-by-hand.
- **The three riders** (sole-mint discipline; the non-erasable wrapper allocation; the Tier-2
  Any-laundering flag floor) travel with that conversion plan's §2 context manifest — they are
  design inputs to it, not separate findings.
- **OwnerVerdict taxonomy questions** stay parked on their named re-entry (the I1
  verdict-taxonomy ratification / recursive-strata unpark).
