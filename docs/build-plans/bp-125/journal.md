---
type: journal
plan: bp-125
started: null
updated: 2026-07-26
---

# Journal — bp-125 (migrate the live brief into the seat, and re-home its rules)

Minted 2026-07-26 by `/graduate`, decomposing ratified `dn-role-state-and-scoped-handoff`
(blessed `c0abfd1`). Second of four (bp-124…bp-127). **Not started.**

## Pre-build notes for whoever picks this up

- ⚑⚑ **THIS PLAN CANNOT RUN IN A WORKTREE.** Its input, `.claude/state/resume-brief.md`, is
  gitignored (`.claude/state/.gitignore` ignores `*`) and therefore **absent from every fresh
  checkout**. Measured 2026-07-26: the main checkout holds a 498-line / 36,701-byte brief; a
  fresh worktree of `origin/main` holds only `.claude/state/.gitignore`. **Run in the main
  checkout**, or have the orchestrator hand the file over before spawn and say so here. The note
  does not mention this; `docs/findings/finding-0234.md` correction (2) carries it.
- ⚑ **The brief has NO history.** It is gitignored and destructively overwritten — that is
  finding-0175's entire complaint. **Copy it to a scratch path outside the repo before touching
  anything.** A mis-step is unrecoverable.
- ⚑ **The irreversible risk is a wrong DERIVED drop.** A fact classified DERIVED but not actually
  rendered by `scripts/handoff.py` is destroyed, not deduplicated. Item 6's acceptance requires a
  **named replacement source** for every dropped fact, verified by running the generator. Do not
  take the classification on faith.
- **Do not delete anything.** Both `.claude/state/resume-brief.md` and
  `docs/templates/resume-brief.md` survive this plan; `session-brief.sh` still surfaces the
  brief; clause (e) still governs. That is the note's deliberately overlapping window (§4 stage
  (a)) and the double bookkeeping is accepted for its duration. Deleting here would strand
  clause (e) and deadlock every orchestrator close.
- **Do not re-point `session-brief.sh`.** The note's §3 sketch put the re-point in P1; its §4
  puts it at stage (b) with the deletion. §4 is followed — see finding-0234 correction (1). A
  re-point without the clause change means the orchestrator must keep writing a brief it can no
  longer see.
- ⚑ **Do not touch the per-plan journal contract.** Note §1.2 forbids it, and Stop-gate clause
  (f) greps the plan journal's tail for a **verbatim** `## Follow-through` header
  (`.claude/hooks/_lib.py:929-937`). A reworded checkpoint contract could redden every future
  seal. checkpoint gains a seat section; its per-plan text stays byte-identical except for the
  disambiguating edits named in §4.
- **context-economy has three brief references, not one:** the `:65-78` section **and** `:21`
  (the decision rule) **and** `:58-59` (the tier-declaration duty). Editing only the section
  leaves two live references to a soon-to-be-deleted artifact. The tier-declaration duty
  **survives verbatim** in its new home — the rule was never wrong, only its container.
- **A rule already living in `CLAUDE.md` is already home.** `uv run` discipline and the blessing
  gates are there; drop them from the brief rather than copying them into a skill. `CLAUDE.md`
  is deliberately out of `write_scope` — no criterion needs it.
- **Amendment A10 is not attempted here or anywhere in this family.** `agent-workflow.md` is
  ratified and `scope-guard` denies the write before write_scope is even consulted
  (`_lib.py:435-441`). See `docs/findings/finding-0233.md`. Draft the A10 text into this journal
  for the owner to land by hand; do not attempt the edit.

## Owed at seal (orchestrator, not the builder)

- A `## Follow-through` block is required by clause (f).
- The **rule → home** table from Item 9 and the **class census** from Item 6 are the audit trail
  of what was moved and what was dropped. They must survive in this journal, not only in a diff.
- The **capsule marker** question: bp-127's F1b lint scopes to "the latest capsule plus all
  entries after it." If this migration's first entry establishes a capsule marker, **state it
  explicitly here** — bp-127 reads this journal for it (its §3 Q1). If it does not, say that too.
- `finding-0175 → promoted` (Item 11) — confirm the unswept-findings count actually dropped;
  `open`/`routed` are the counted states (`.claude/hooks/_lib.py:971-973`).
- Collateral brief references in `docs/PROGRESS.md`, `docs/PARKING-LOT.md` and
  `docs/book/chapters/02-architecture.tex` are **out of role** for a builder — file them for the
  orchestrator sweep and the next `/scribe`.
