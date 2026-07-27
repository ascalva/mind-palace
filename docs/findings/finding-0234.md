---
type: finding
id: finding-0234
status: open
created: 2026-07-26
updated: 2026-07-26
links:
  - docs/design-notes/role-state-and-scoped-handoff.md   # the ratified note these three corrections bear on
  - scripts/board.py                                     # :136,162,188,203 — the four globs it actually scans
  - .claude/state/.gitignore                             # why the migration input is unreachable from a worktree
  - docs/build-plans/bp-124/plan.md
  - docs/build-plans/bp-125/plan.md
  - docs/build-plans/bp-126/plan.md
ftype: spec-defect
origin_plan: orchestrator
route: orchestrator
resolution: null
---

# Three claims in `dn-role-state-and-scoped-handoff` that reading the code falsified at graduation

## What

Graduating the note into build plans required grounding its `[DERIVED]` and `[INFERENCE]` claims
against the tree. Three did not survive. None invalidates the note's decisions — the rulings in
§2.3–§2.10 all stand — but each would have produced a defective plan if transcribed, so each is
recorded here and carried by a specific item or constraint rather than inherited silently.

### (1) The note contradicts itself on where the `session-brief.sh` re-point lands

- **§3 Consequences** assigns it to **P1**: *"(P1) the substrate: `docs/roles/` artifacts, the
  generator extension + idempotence pin, the one-time migration of the current brief …,
  `session-brief.sh` re-point"*.
- **§4 Wiring & enablement** assigns it to **P2**: *"(a) P1 merges → the artifacts exist and the
  generator runs, but clause (e) still governs (old brief still written — a deliberately
  overlapping window …); (b) P2 merges → clause (e′) governs, the brief and its template are
  deleted in the same diff, `session-brief.sh` re-points."*

**§4 is right and §3 is wrong**, and the code says why. A re-point without the clause change
leaves clause (e) still blocking on `mtime(.claude/state/resume-brief.md)`
`[GROUNDED .claude/hooks/_lib.py:908-920]` while `session-brief.sh` no longer surfaces that file
— so the orchestrator must keep writing a brief it can no longer read. That is strictly worse than
either endpoint, and it contradicts §4's own description of the overlapping window ("old brief
still written"). §3's split is explicitly labelled `[DERIVED]`; §4 is the operative sequencing
statement.

**Carried by:** the graduation follows §4. The re-point is `bp-126` Item 13, in the same atomic
diff as clause (e′) and the deletion; `bp-125` §9 states the exclusion explicitly.

### (2) The one-time brief migration cannot be performed by a worktree builder

The note assigns *"the one-time migration of the current brief"* to a build plan (§3) without
noting that the input is unreachable from the environment builders normally run in.

`.claude/state/.gitignore` ignores `*` with a single `!.gitignore` exception, and states the
intent: *"Regenerable, per-worktree, never shared"* `[GROUNDED .claude/state/.gitignore]`.
Measured 2026-07-26:

| checkout | `.claude/state/` contents |
|---|---|
| main | `.gitignore`, `docket.md`, **`resume-brief.md` (498 lines, 36,701 bytes)**, `session-baseline` |
| a fresh worktree of `origin/main` | `.gitignore` — **and nothing else** |

A delegated worktree builder would find no brief, and — because the artifact is gitignored and
destructively overwritten — **no history to recover it from**. The failure mode is a builder
reconstructing the brief from `docs/PROGRESS.md` or from memory, which would silently fabricate
the very judgement the migration exists to preserve.

**Carried by:** `bp-125` §0 and §3 Q1 state the execution-mode constraint (main checkout, or the
orchestrator hands the file over before spawn); §10 makes "the brief is not present" the plan's
**first** stop-and-raise, before any other work.

### (3) The orphan check does **not** cover findings and owner questions "for free"

§2.3 states: *"findings and owner questions gain an optional `track:` front-matter key … Additive,
and the existing orphan check covers the new members for free."*

`scripts/board.py` scans exactly four globs — `docs/tracks/*.md`,
`docs/build-plans/*/plan.md`, `docs/design-notes/*.md`, `docs/deskchecks/*.md`
`[GROUNDED scripts/board.py:136,162,188,203]` — and `_build` calls only those scanners
`[GROUNDED scripts/board.py:416-420]`. Neither `docs/findings/` nor
`docs/inbox/owner-questions.md` is ever read. A `track:` key added to a finding would therefore
get **no** coordinate-integrity checking at all: the F-WF1 orphan signal that makes the track
coordinate tier-4 enforceable simply would not see it, and the note's whole reason for reusing the
track coordinate instead of minting a new key vocabulary would be weakened without anyone noticing.

**Carried by:** `bp-124` Item 4 extends the scan surface, which is why `scripts/board.py` **and**
`tests/unit/test_board.py` are in that plan's `write_scope` — a naïve "new files only" scope would
have made the criterion unbuildable. Item 4's falsifier is a no-op check: no finding or oq carries
a `track:` today, so a correct extension must change nothing in `docs/TRACKS.md` beyond the
docstring.

## Why it matters

1. **Each would have produced a defective plan if transcribed.** (1) would have shipped a
   half-cutover that deadlocks nothing but degrades everything; (2) would have burned a delegated
   session that could not start; (3) would have shipped an enforcement claim with no enforcement
   behind it — the "structural enforcement" failure the repo has already booked three times.
2. **All three are the same class:** a `[DERIVED]` or unlabelled claim in a ratified note that
   reading the code falsifies. The note is unusually rigorous about labelling its inferences, and
   these three still slipped — which is the argument for graduation being a *grounded* pass (A4)
   rather than a decomposition, not an argument against the note.
3. **(3) in particular is a live overclaim in a ratified artifact.** Until `bp-124` Item 4 lands,
   anyone reading §2.3 will believe a check exists that does not.

## Re-entry condition

Not blocking — all three are carried by the plans as built (`bp-124` Item 4, `bp-125` §0/§3
Q1/§10, `bp-126` Item 13). This finding is the record that the note's text and the tree disagree.

**Re-entry:** at the deskcheck for this track, confirm (a) `bp-124` Item 4 landed and the orphan
check genuinely covers findings/oqs, and (b) `bp-125` ran in a checkout that actually had the
brief. If the owner wants the note's text corrected rather than annotated, that is a superseding
note or a lettered amendment — **an owner hand-act**, since the note is ratified and
agent-immutable (A8, and see `finding-0233`).

## Routing

`design` → **orchestrator**. These are corrections to a ratified design note, so they cannot be
fixed by a builder and must not be fixed by an edit
`[GROUNDED .claude/hooks/_lib.py:435-441]`. The orchestrator's options:

- **Default (taken):** annotate via this finding; the plans carry the corrected behavior. No owner
  action required for the build to proceed.
- **If the owner prefers the record corrected in place:** batch to
  `docs/inbox/owner-questions.md` as a request for an amendment entry alongside A10
  (`finding-0233`), since both are owner hand-acts on the same ratified surface and would land in
  one sitting.
