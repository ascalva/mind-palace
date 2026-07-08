---
type: build-plan
id: bp-005
status: in-progress
design_ref: []
contract: builder
write_scope:
  - "docs/design-notes/**"
  - "docs/research/**"
  - "docs/build-plans/bp-005/**"
  - "docs/findings/**"
session_budget: 1
depends_on: []
parallelizable_with: []
created: 2026-07-07
updated: 2026-07-08
re_entry: null   # was parked on the denylist collision; owner lifted docs/design-notes/** from the DENYLIST mid-session, both halves now done
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — Convert remaining design/research notes to front-matter format

## 1. Objective

Every design/research note not already carrying machine front-matter gets the
template block prepended, landing at `status: draft`. Front-matter only — prose
untouched. No archives (owner ruling: zero physical archives). No `ratified` or
`superseded` may be written — done or owner-only.

## 5. Write scope

As front-matter. Out of scope: docs/audits/\*\*, docs/PROGRESS.md, any status
transition to ratified/superseded, any prose edit.

## Addendum (supplied mid-session)

The plan body above (only §1 Objective + §5 Write scope) was incomplete at
`/build` time. Three enrichments and a record-repair instruction arrived mid-run,
after the conversion had begun. Recorded here so the plan in history describes the
run that actually happened; execution detail and results are in `journal.md`.
Same plan, same `write_scope`. Still in force: **no prose edits; no
`ratified`/`superseded` status written anywhere.**

1. **Supersession-marker inventory.** Walk every note in `docs/design-notes/` and
   `docs/research/` (converted or not) and record in the journal every *prose*
   occurrence of a supersession-marker, as `file:line` + exact matched text —
   stems, case-insensitive (`supersed`, `takes precedence`, `authoritative`,
   `corrected`, `replaces`, + judged overruling equivalents like "correct but
   incomplete"). Front-matter `supersedes`/`superseded_by` excluded (trivially
   machine-stripped). Seeds the scrub-pattern file for the supersession-recovery
   evaluation (`supersession-recovery-evaluation.md` §3). Completeness over
   tidiness.

2. **Implementation stamp.** Add to each converted note's front-matter the
   verification audit's verdict verbatim, kebab-cased —
   `implementation: built-wired | present-not-wired | partial | in-flight |
   not-built | design-only | unverified` — sourced from
   `docs/audits/corpus-state-audit-2026-07-verification.md`, with a trailing
   citation comment. No verdict in the audits → `design-only` for
   doctrine/philosophy notes, otherwise omit the field and journal the gap. Never
   guess a verdict.

3. **Created-date source.** For each converted note, journal which source its
   `created:` date came from — the note's own dated header/prose, audit
   chronology, or git first-commit date.

4. **Record repair.** Items 1–3 appended here; a journal entry records that the
   plan body was incomplete at `/build` time and these instructions arrived
   mid-session.

**Note on the run's shape (see `journal.md`).** The design-note half was first
blocked by the `docs/design-notes/**` foundation denylist (Stop-gate caught 30
Bash-prepends; all reverted). The owner then lifted that path from the `DENYLIST`,
and the design notes were converted **with** the item-2 implementation stamps in a
single pass. finding-0024 (which parked the design-note criterion) is deleted —
resolved by the owner's lift, no longer an issue for this work.
