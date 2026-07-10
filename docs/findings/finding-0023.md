---
type: finding
id: finding-0023
status: routed
created: 2026-07-08
updated: 2026-07-09
links:
  - docs/research/planar_graphs.md
  - docs/research/security-planes.md
  - docs/research/un-represent-ability.md
  - docs/templates/design-note.md
  - docs/build-plans/bp-005/plan.md
ftype: spec-defect
origin_plan: bp-005
route: orchestrator
resolution: null
---

# No template or schema exists for research-note front-matter

> **Triage 2026-07-09 (/triage):** open → routed (orchestrator). This file and bp-005's
> journal were stranded **uncommitted** in the `mp-convert-notes` worktree when the branch
> merged (`66c3e6f → a33ecab` took the 33 notes + plan.md but not these untracked files);
> recovered to main by this sweep. Design-changing spec-defect → **promotion proposed:
> ratify the provisional research-note convention** (a `docs/templates/research-note.md`
> + a line in the artifact-chain spec), batched for the owner at `owner-questions.md`
> **oq-0010**; flips to `promoted` on adoption, and the three `rn-*` headers get their
> cheap reconciliation if the ratified schema differs. Re-entry per §Routing below.

## What
bp-005's objective requires *design/research* notes to carry machine
front-matter, but the template set (`docs/templates/`) defines only
`design-note.md`, `build-plan.md`, `capsule.md`, and `finding.md` — there is no
research-note template, and no spec text (`BUILD-SPEC.md`, `agent-workflow.md`)
defines a `type:`, id prefix, or field set for the three `docs/research/*.md`
notes. So the schema for a first-class corpus artifact is undefined.

To complete bp-005 without blocking (§5), I applied a **provisional convention**,
mirroring the design-note schema:

- `type: research`
- `id: rn-<filename-slug>` (e.g. `rn-security-planes`, `rn-planar_graphs`;
  the slug preserves the filename verbatim, as `dn-` ids do)
- `status: draft`
- `created` / `updated` from git history (first-add / last-commit dates)
- `links: []`, `supersedes: null`, `superseded_by: null`, `warrant: null`

Applied to `planar_graphs.md`, `security-planes.md`, `un-represent-ability.md`.

## Why it matters
Research is a genuine artifact type in the chain (design notes link to
`docs/research/*` as warrants/sources). If tooling grows to key on `type:` or
id-prefix, an unratified convention invented by a builder is a latent
inconsistency. The design layer should either ratify this convention (ideally by
adding a `docs/templates/research-note.md`) or replace it — at which point the
three ids/types get a cheap correction.

Secondary decision recorded here for the same reason: for **all 33 converted notes**
(3 research + 30 design), `updated:` was set to each note's git last-commit date,
not today — a metadata-only migration should not rewrite a note's recency. Same
correction cost if the owner prefers otherwise. (The design notes were converted
after the owner lifted `docs/design-notes/**` from the foundation denylist
mid-session; the earlier denylist-collision finding was resolved by that lift and
deleted.)

## Re-entry condition
Not parked — bp-005 completed under the provisional convention. No criterion is
blocked. This finding is informational-plus-proposal for the reflection sweep.

## Routing
- `spec-defect`, design-changing → the orchestrator. Promote by ratifying the
  research-note convention (a `docs/templates/research-note.md` and/or a line in
  the artifact-chain spec); on adoption this flips to `promoted` and the three
  `rn-*` notes are reconciled to the ratified schema.
