# Builder Prompt — Sacred-Boundary Design Set: Investigate, Reconcile, Plan

**Mode: INVESTIGATION AND PLANNING ONLY. Do not implement anything. Do not
create, edit, move, or delete any file in the repository except the single build
plan named in "Deliverable." Wait for explicit owner approval before any
implementation, and before applying any documentation banner or cross-reference.**

## Context

A design set has been authored describing the core's sacred write-boundary — the
three channels that cross into or out of the core (verdict authorization,
ingestion, effects) and the four properties every such write must satisfy. It was
authored without access to the live codebase. Your job is to ground it against
the actual repository, answer its open questions with citations, and produce an
implementation plan the owner can approve item by item. Everything in the set is
provisional until confirmed against the code.

## Required reading (in this order)

Spine note first:

- `docs/design-notes/the-sacred-boundary.md`

Then the five subsystem notes:

- `docs/design-notes/verdict-authority.md`
- `docs/design-notes/ingest-identity-and-amendment.md`
- `docs/design-notes/dialogue-ingest-and-recursion.md`
- `docs/design-notes/founding-corpus.md`
- `docs/design-notes/effector-risk-computation.md`

Then the existing docs each note reconciles against, and the relevant code:

- `docs/research/security-planes.md`,
  `docs/design-notes/hands-and-the-effector-layer.md`,
  `docs/design-notes/recursive-strata.md`,
  `docs/design-notes/live-adoption-and-longitudinal-harness.md`,
  `docs/design-notes/ambassador-as-reasoning-agent.md`,
  `docs/audits/prompt-integrity-audit.md`;
- the librarian / ingest implementation, the embedding-index layer, the verdict
  store, and any effector-layer scaffolding.

Follow the repository's own reading discipline (re-establish the filesystem
connection if it has dropped; read whole files before citing).

## Part A — Answer the open questions (with `path:line` citations)

**Every claim about the current state of the system must carry a `path:line`
citation.** Where the code does not settle a question, say so explicitly rather
than inferring.

- **Q1 — index keying** (`ingest-identity-and-amendment.md` §8). Chunk-content-
  hash or ingest occurrence? Cite schema and write path. State whether the
  content-addressed-projection model is satisfied, partial, or absent. Touches
  stored data.
- **Q2 — dialogue operations** (`dialogue-ingest-and-recursion.md` §7). What does
  dialogue ingest emit today? Assess the starter vocabulary
  {`supersede`, `attach_defeater`, `record_warrant`} against real exported
  dialogues if any exist; recommend additions only with a cited case. Node or
  edge for warrant? Confirm composition with the I5 population damper, the γ^d
  confidence damper, and the typed edge budgets — cite each enforcement point.
- **Q3 — corpus unit** (`founding-corpus.md` §4). Is steady-state ingest
  operation-emitting or document-emitting? Determine the required founding unit
  to share that path; flag any place a separate founding path fractures the
  provenance model.
- **Q4 — verdict auth** (`verdict-authority.md` §7). Anything TOTP-shaped present?
  Locate the Ambassador↔owner interface; identify the insertion point for Ed25519
  verdict signing + monotonic sequence numbers; confirm reuse of existing
  attestation-signing code.
- **Q5 — effector risk** (`effector-risk-computation.md` §7). Does any risk
  computation exist? Priced (weighted terms) or gated (feasible-set constraints)?
  If absent, say so.
- **Q6 — Track L prerequisites** (`the-sacred-boundary.md` §4). Status of
  provenance migration `--apply` and self-knowledge ingest, with citations.
- **Q7 — version identity / edge keying** (`ingest-identity-and-amendment.md`
  §4A, §8). Is there a version identity independent of content digest? Are
  supersession edges keyed on content digest or version identity? Cite. If
  versions are distinguished only by content digest, the revert case is
  unrepresentable and a version-identity key is a foundational addition to
  coordinate with `--apply`. Also confirm whether a re-ingest of unchanged
  content still logs an *occurrence* per §2, or whether no-op re-saves record
  nothing (dropping the "ingested twice" provenance fact).
- **Q8 — version-history store separation** (`ingest-identity-and-amendment.md`
  §4A Constraint 2, §8). Does the balance-math consumer read the same store that
  holds `supersedes` edges? Exclusion structural or by rel-type filter? Cite the
  consumer's rel-type selection. Confirm `supersedes` and its placeholder sign
  never enter the signed-graph computation.

Then list any **additional questions or risks** discovered during reading that
the design set did not anticipate.

## Part B — Reconciliation proposal (propose only; do not apply)

For each subsystem note, quote the specific existing passage in its home doc that
this design corrects or extends, and propose **either** a cross-reference **or** a
partially-superseded banner — never silent replacement; banner on correction,
cross-reference on extension. Present as proposed diffs in the plan. Do not edit
the docs.

## Part C — Build plan

Produce a phased implementation plan. Constraints:

- **Respect the ordering** in `the-sacred-boundary.md` §4: verdict store → close
  the recursive loop → longitudinal study. Surface any dependency it implies but
  does not name.
- **Phase by blast radius**, tightest-reversible first, mirroring the effector
  port order: verification and read-only changes before schema changes before
  anything that rewrites stored data.
- **Mark each work item as independently parallelizable or not**, so distinct
  builders can be assigned once the plan is approved. State the dependency edges
  between items explicitly.
- Treat these as distinct, independently approvable items, each with an
  acceptance test and a named falsifier (per "formalism must constrain, not
  decorate"):
  1. **Index-keying verification** and — only if Q1 shows a gap — migration to
     content-addressed chunk keys. Touches stored data; highest caution;
     coordinate with provenance migration `--apply`.
  2. **Dialogue-ingest operation vocabulary** — ratify the set, then implement.
     Must compose with I5, γ^d, and the edge budgets.
  3. **Founding-corpus ingest path** — unify with steady-state per Q3 *before*
     any corpus is authored.
  4. **Ed25519 verdict signing** — canonical serialization, monotonic sequence
     numbers, hardware-key custody, Ambassador-as-transport.
  5. **Effector-risk constraint structure** — constraints bounding the feasible
     set, alignment-drift weight owner-set and not auto-tuned. Scope in only if
     Track G is being opened now; otherwise record as parked with a re-entry
     condition.
  6. **Supersession-edge correctness** (`ingest-identity-and-amendment.md` §4A).
     Re-key `supersedes` edges on version identity (not content digest); move
     version history out of the balance-fed semantic edge store into a dedicated
     version structure the balance math cannot read; confirm removed-chunk
     vectors are excluded from the active projection; order by version-seq, no
     cycle guard (record truthful history). Per-chunk supersession edges are
     deferred. Touches stored data if edges are re-keyed or a version-identity
     column is added — coordinate with item 1 and `--apply`.

Dependency edges (state these explicitly in the plan and extend as needed):
item 6 **before** item 2 — claim-`supersede` from the dialogue vocabulary must
not collide with version-`supersedes`, so the store separation in item 6 is a
prerequisite. Items 1 and 6 are the two identity-keying corrections at the ingest
layer; both touch stored data and both coordinate with provenance migration
`--apply` — sequence them together and ahead of any corpus authoring (item 3).
- For every deferred decision, use the parked-decisions protocol: record the
  default, name rejected alternatives with reasons, specify the explicit re-entry
  condition.
- Each item specifies: files to create or change (changed or new only — never
  re-deliver untouched files), the acceptance test, the invariant(s) it must not
  violate, and whether it touches stored data.

## Deliverable

Write the build plan to a **single file**:

`docs/design-notes/build-plans/sacred-boundary-build-plan.md`
(create `build-plans/` only if absent; if the repo has an established location
for build plans, use that and say so).

Contents, in order: (A) answered questions with citations and any new risks;
(B) the reconciliation proposal as proposed diffs; (C) the phased,
independently-approvable, parallelizable-marked build plan with acceptance tests
and parked-decision records.

Then **stop and wait for owner approval.** Implement nothing, and apply no
documentation change, until the owner approves — item by item is acceptable.
