---
type: track
slug: mathematical-foundations
title: Mathematical foundations — the laws ledger + the Lean ladder
status: active
warrant: null
audit_refs: []
dod:
  - MF-1 laws ledger seeded (docs/LAWS.md) — one row per law naming the TRUE structure, ladder-labeled (labels from dn-research-register §2.3); memberships lands multiset, never Boolean algebra
  - MF-2 laplacian/spectral falsifier batch green or counterexamples filed (direct PSD, nullity = components, isolated-node convention) + the minimal ledger checker (anchors + test ids)
  - MF-3 cut/conductance/curvature falsifier batch green or counterexamples filed (direct Φ(S) + both degenerate conventions; most_negative_edges emission rule)
  - MF-4 formal/ L1 — sibling lake package builds; statements + Plausible attacks; sorry ratchet recorded; zero import coupling with core/ either direction
  - MF-5 lean-action advisory CI green on a real PR with the Mathlib cache hitting
  - MF-6 (entry-gated on MF-4) first L2 discharge batch — Theorem (machine-checked, formal/...) claimable for the discharged laws
backlog_deskcheck: null
links:
  - docs/brainstorms/mathematical-foundations.md
  - docs/design-notes/dn-mathematical-foundations.md
  - docs/design-notes/dn-research-register.md
---
# Track — Mathematical foundations (the laws ledger + the Lean ladder)

The identity card for the mathematical-foundations track, minted alongside its
founding note (the scored-beliefs/erratum-relation precedent; ⚑ the owner renames or
rejects this coordinate at the merge). **Scope:** the mathematical substance of the
palace — which known structure each component is a model of
(structure-instantiation), the laws ledger (`docs/LAWS.md`: statement + arithmetic
domain, claimed structure, anchor, ladder label, falsifier, formal status per law),
the per-family falsifier batches, and the `formal/` Lean ladder (L1 statements → L2
proofs; L3/L4 parked). Members are the artifacts declaring
`track: mathematical-foundations`.

**Not in scope:** the research register (track: workflow — the §2.3 labels are
consumed here, never redefined); `core/` code changes (falsifier batches file
defects, never fix); Cheeger / Ollivier-Ricci formalization (L1 formalizes
definitions and stated laws only); the NOTATION.md refresh (its own surgical PR).

## Relationship to other tracks

`workflow` owns the claim ladder and the register this track writes in — labels flow
one way, from there to here. `erratum-relation`'s operator-algebra DoD rows are
candidate ledger rows once that lane's laws want indexing. `inner-outer-core`'s ring
discipline is the architecture-side analog of MEM-11 (the kernel-never-imports law);
`formal/` extends the same posture: a sibling like `eval/`, zero import coupling with
`core/` in either direction.

**Definition of done:** the dod rows above — the ledger names true structures with
green paired falsifiers or filed counterexamples per family, `formal/` builds with
the sorry ratchet monotone down, the advisory CI job is green on a real PR, and the
first L2 discharge batch lands behind its entry gate.

**Owed deskcheck:** none standing — nothing sealed on this track yet.
