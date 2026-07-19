---
type: finding
id: finding-0097
status: resolved
created: 2026-07-17
updated: 2026-07-17
links:
  - docs/experiments/sigma-sweep-run-1.md          # the run that surfaced it (SE-1)
  - docs/design-notes/sigma-sweep-experiment.md    # FROZEN @ d932670 — SE-1 rules (a)/(b) (the ambiguity)
  - eval/harness/sweep.py                           # the optimizer that emits-on-flat (no carve-out)
ftype: design
origin_plan: dn-sigma-sweep-experiment run 1 (SE-1)
route: orchestrator
resolution: RESOLVED-root-cause by finding-0113 (bp-073 Δ, owner-blessed 2026-07-19). The optimizer's emit-on-flat trigger was the STARVED (flat) objective — a small-corpus artifact, not a real ceiling (finding-0113: input-starvation). At adequate corpus scale the objective discriminates. The residual design question — whether the optimizer should GUARD against a flat objective (refuse-to-emit) as hardening — is a SEPARATE concern (bp-073 §9 non-goal); if wanted, mint a fresh finding. Root cause closed here.
---

# SE-1's decision rules (a) and (b) are NOT mutually exclusive on a perfectly FLAT curve — the plateau-center ≠ default satisfies (a) while "flat within ε" satisfies (b); (b) must govern, and the sweep engine emits a proposal regardless (no flat-curve carve-out)

## What
The FROZEN pre-registration (`d932670`) §2.2 SE-1 gives:
- (a) selection ≠ current default AND plateau width ≥ 3 admissible cells ⇒ the emitted proposal stands;
- (b) curve flat within ε across admissible cells ⇒ oq-0024 retires "insensitive; default stands".

Run 1 produced a **perfectly flat curve** (golden_recall = 1.0 on all 21 cells). On a flat curve the
whole grid is one plateau, so the optimizer's plateau-CENTER is 0.65 ≠ the default 0.62 — which
satisfies **(a)'s literal conditions** (selection ≠ default, plateau ≥ 3). But **(b)'s condition
(flat within ε) also holds**. The two rules overlap; the note does not state a precedence.

Independently, `eval/harness/sweep.py`'s optimizer has **no flat-curve carve-out**: whenever it
selects a value ≠ default with guardrails captured and selfmod enabled, it emits a `ProposedChange`.
So run 1's engine emitted **proposal #1** (`dream_rnd_sigma 0.62→0.65`) mechanically, even though the
curve carries no signal that a move is warranted.

## Resolution (recorded, applied in run 1 — NOT a silent analysis change, §2.3)
**(b) governs a flat curve.** A curve flat within ε carries no evidence that the plateau-center is
better than the incumbent; the plateau-center is a deterministic tie-break artifact, not a signal.
The note frames (b) as "a completion, not a failure" and pre-registered it precisely for this case.
So run 1: oq-0024 RETIRED per (b), default 0.62 stands, and **proposal #1 is DECLINED** (it remains
`proposed` and unblessed in the §14 ledger; the owner may formally reject it).

## Recommendation (re-entry)
A run-2 note update (re-ratified pre-registration) should make the precedence EXPLICIT: rule (b) is
checked FIRST — "if the curve is flat within ε, retire (default stands) regardless of the mechanical
plateau-center." Optionally, teach the optimizer a flat-curve guard (don't emit when the near-optimal
set spans the whole admissible grid within ε), so the engine and the analysis rule agree and no
vacuous proposal is minted. Both are design/direction items for the owner; non-blocking.

## Non-goals
Not a correctness defect — the optimizer's plateau-center + emission logic are working as built; the
gap is that the pre-registration's (a)/(b) precedence was left implicit and the engine has no
flat-curve carve-out. Not re-opening run 1's disposition (correct under this resolution).
