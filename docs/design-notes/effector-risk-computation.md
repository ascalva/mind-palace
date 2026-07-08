---
type: design-note
id: dn-effector-risk-computation
status: draft
implementation: partial   # corpus-audit 2026-07 verification
created: 2026-07-04
updated: 2026-07-04
links: []
supersedes: null
superseded_by: null
warrant: null
---

# Effector Risk Computation (Track G)

**Status:** DRAFT — pending codebase reconciliation and owner ratification
**Origin:** Design dialogue, July 2026
**Boundary:** Outbound channel — effects. Governed by the sacred-boundary
principle (`the-sacred-boundary.md`): effects are the write *out of* the core,
symmetric to ingestion, gated by blast radius.
**Reconciles with:** `docs/design-notes/hands-and-the-effector-layer.md` (this is
its quantitative backing — reversibility, inaction cost, graduated port order).

---

## 1. Correction — inaction is not zero-risk

"No action is lowest risk" holds only for *action-induced* risk. Inaction carries
the counterfactual cost of the outcome not achieved, plus the risk of the world
evolving adversarially while the system waits. The honest decomposition is
**action-risk vs inaction-regret**, with the null action as one candidate
carrying its own expected value (the "do nothing and let the world drift"
outcome). Minimizing action-risk alone makes paralysis the dominant strategy —
the failure the owner flagged in noting that risk is sometimes required.

## 2. Formalization — reversibility as reachability contraction

Model reversibility as **contraction of the reachable state set**. An
irreversible action collapses the set of states still reachable afterward
(deleting an un-backed-up file removes "file exists"; sending an email removes
"unsent"; reading a sensor contracts nothing). This is the option-value /
empowerment formalism, and it **derives** the graduated port order rather than
stipulating it:

- read-only sensing → zero contraction;
- reversible writes → contraction bounded by undo-cost;
- irreversible external effects → permanent contraction (human-approval gated).

The port order is simply the ordering by degree of reachability lost — the
quantitative backing for the blast-radius ordering already in
`hands-and-the-effector-layer.md`.

## 3. The load-bearing rule — bright lines are constraints, not terms

The "modified risk-mitigation calculation" is acceptable **only as an interior
method**: inside the feasible region, choose the action maximizing expected value
minus an irreversibility penalty minus an alignment-drift penalty. The bright
lines must be **constraints bounding the feasible set**, never weighted terms
inside that sum.

Reason (exact): expected-value reasoning is the mechanism that *rationalizes*
crossing a bright line. If irreversibility is merely priced, a sufficiently large
outcome gain will always purchase an irreversible action. Therefore:

- **irreversibility above threshold** → hard constraint → routes to the owner
  gate (not payable);
- **projected alignment-drift above threshold** → hard constraint → forbidden;
- scalarize **only within** what remains feasible.

No outcome, however large, may buy its way past the gate. (Sacred-boundary
property 4.)

## 4. Second, independent argument for gating irreversibility

The world-model behind `P(outcome | action)` is weakest exactly for novel
external effects — the region where stakes are highest. The system should gate
irreversibility not because it computed a high magnitude, but because it **cannot
price the risk reliably at all**. The whole calculation is only as trustworthy as
that model. **Gate on unpredictability (model unreliability), not on a computed
magnitude.**

## 5. On "axis drift"

The earlier "axis drift to balance alignment drift" framing is **dropped** — the
owner no longer endorses or recalls the specific construct. What survives is the
**alignment-drift constraint** of §3, which must be an **owner-set weight /
threshold**, never auto-tuned. Auto-tuning the alignment penalty is optimization
over the alignment objective itself, i.e. the self-modification ring-fenced
elsewhere (see `verdict-authority.md` §6).

## 6. Field-guide requirement

Per "formalism must constrain, not decorate," the reachability-contraction
measure and the constrained-optimizer each need a named falsifier in the harness
before adoption (what it measures, what assumptions make it valid, what
observable result shows it is not earning its place). The functional form is a
build-plan specification item, not asserted here.

## 7. Open question (requires reading the code)

- **Q5.** Does any effector-risk computation exist yet (Track G is on-the-
  horizon)? If scaffolding exists, cite it and state whether bright lines are
  currently **priced** (weighted terms) or **gated** (feasible-set constraints).
  If absent, say so — and this note is then scoped in only if Track G work is
  being opened now; otherwise it is parked with the re-entry condition recorded
  in the build plan.

## 8. Reconciliation

Extends and quantifies `docs/design-notes/hands-and-the-effector-layer.md`.
Builder to propose a cross-reference or, if any existing text conflicts, a
partially-superseded banner.
