# bp-148 — journal

## Pre-build notes for whoever picks this up

- ⚑ **Every edited sentence must be TRUE DURING THE TRANSITION.** The hooks are still live,
  the tree is still authoritative for status, `gate-guard` still denies. Write "record unit
  state in the registry **and** keep the journal's judgement entry", never "instead of". A
  doctrine describing the end state as if it were the present is how an agent gets told to do
  something the guards will deny.

- ⚑ **`.claude/skills/resume/SKILL.md` DOES NOT EXIST.** §2.7's table is wrong about the
  path; the real surface is `.claude/commands/resume.md`. File a `spec-fidelity` finding and
  edit the real file. Do NOT create the skill to make the document true.

- ⚑ **`CLAUDE.md` is paid on every turn.** The note licenses a one-sentence-scale edit and the
  file's own §5 thinness rule binds. This edit must REMOVE more than it adds. Verify the
  line number before editing — the file has moved since the note was written.

- ⚑ **Do not delete the prose `## Follow-through` block** from the checkpoint skill. The
  hook's clause (f) still greps journals for that verbatim header until bp-149, and
  `tests/integration/test_deskcheck_gate.py` pins the behaviour.

- ⚑ **Do not dilute the bare-glob warning** in `docs/templates/build-plan.md`. Adding
  `scope_level` beside it must not soften it — the template is what every future plan is
  minted from, so a defect there is systemic.

- **Cite the existing CORRECTION block, don't re-argue it.** `.claude/skills/context-economy/SKILL.md`
  already retired the `.claude/state/` handoff file for exactly this reason. Two independent
  arguments for one rule drift.

- **Item 43's real falsifier is a real drill, not the test.** Run an actual fresh session
  against a real in-flight unit with only the query + prose, and record honestly whether it
  had to re-ask. If it did, F6's own wording halts the deprecation here and bp-149 must not
  proceed on these rows. Record the transcript summary, not a claim.

- **Regression check:** run `tests/integration/test_deskcheck_gate.py` and record the result
  even though no hook changes.

## Entries

_(none yet — this plan is `proposed`; the first entry is written by the build session)_
