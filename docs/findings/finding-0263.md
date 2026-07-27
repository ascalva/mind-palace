---
type: finding
id: finding-0263
status: open
created: 2026-07-27
updated: 2026-07-27
links:
  - docs/design-notes/dn-autopilot-and-delegated-blessing.md
  - docs/design-notes/agent-workflow.md
  - docs/templates/build-plan.md
  - docs/brainstorms/the-false-success-rule.md
ftype: spec-defect
origin_plan: orchestrator
route: orchestrator
resolution: null
---

# §2.4's P3 predicate reads a machine-readable per-item flag that does not exist — `touches_stored_data` is free prose with ~20 spellings across 111 plans, so P3 built naively passes on every plan

## What

`dn-autopilot-and-delegated-blessing` §2.4 defines eligibility predicate **P3** as:

> `P3 — no stored-data blast` · check: *"every plan item carries `touches_stored_data: false`"* ·
> grounding: *"flag exists per-item [GROUNDED agent-workflow.md:80]"*
> (`docs/design-notes/dn-autopilot-and-delegated-blessing.md:321`)

The grounding citation is accurate about the *concept* and wrong about the *form*.
`docs/design-notes/agent-workflow.md:80` says the per-item body carries *"a
`touches_stored_data` blast-radius flag"* — but it lists it among **body-section** fields
explicitly contrasted with front-matter keys, and the template renders it as prose:
`docs/templates/build-plan.md:111` — `- **Touches stored data?** <yes/no — blast-radius flag; …>`.

**Measured on the tree, 2026-07-27.** 111 of the plans under `docs/build-plans/` carry the
flag. The literal string `touches_stored_data: false` appears in **zero** of them. The prose
form has at least twenty distinct spellings; the most frequent, by count:

| count | text as written |
|---|---|
| 57 | `- **Touches stored data?** No. **Parallelizable?** …` |
| 52 | `- **Touches stored data?** No.` |
| 30 | `- **Touches stored data?** no` |
| 6 | `- **Touches stored data?** Reads only.` |
| 4 | `- **Touches stored data?** No (reads t…` |
| 4 | `- **Touches stored data?** **No.**` |
| 4 | `- **Touches stored data?** Yes — a new …` |
| 3 | `- **Touches stored data?** yes — \`data…` |

(Command: `grep -rhoE '^[-*]?\s*\*\*Touches stored data\?\*\*.{0,12}' docs/build-plans/*/plan.md
| sort | uniq -c | sort -rn`.)

## Why it matters

This is the false-success rule's exact shape
(`docs/brainstorms/the-false-success-rule.md:19-22` — name the degenerate input, assert the
check reddens on it), and P3 has **two** degenerate inputs, both of which pass:

1. **The literal reading.** A checker implementing §2.4's text — "assert no item carries
   `touches_stored_data: true`" over a field spelled `touches_stored_data:` — matches nothing,
   finds no `true`, and returns **PASS on every plan in the repository**, including a plan that
   rewrites the vector store. The check is vacuous, and vacuous in the safe-looking direction.
2. **The naive prose reading.** A checker doing `value.lower().startswith("no")` returns PASS
   on `No (reads the corpus and writes a projection)` and on `Reads only.` — it is reading the
   first two characters of an English sentence and calling it a blast-radius decision.

P3 is one of five **conjunctive** predicates whose joint truth is, per §2.8, *"the
reversibility guarantee"* — *"P1–P4 jointly mean every effect of the run is
uncommitted-to-main, git-tracked, stored-data-free, and live-state-free."* A P3 that cannot
fail makes that conjunction a four-term conjunction wearing a five-term label, and the term it
silently drops is the only one that guards the corpus.

⚑ The predicate is also **printed into the capsule the owner reads** (§2.4: *"their results
are printed in the capsule the owner reads"*). A vacuous PASS is therefore not merely an
un-enforced check — it is a false statement rendered to the owner's phone at the moment he
decides whether to grant.

## Re-entry condition

**Not blocking; the wave proceeds.** `bp-137` (the P1–P5 predicate) is minted now and carries
this finding as its warrant. Its Item 16 resolves the *builder-side* half on its own authority
per the routing rule below: P3 is implemented against a **pinned regex over the §7 item body**
whose captured value must normalize to exactly `no`/`No`/`No.`/`**No.**` — and **anything
else, including every hedged spelling above and an absent flag, fails P3**. Ambiguity resolves
toward refusing eligibility (invariant 7).

Two consequences the builder may **not** settle, which is why this routes to the orchestrator:

- **A large majority of existing plans will not pass P3 as tightened.** That is correct and
  intended — P1–P5 gates *autopilot eligibility*, not repo hygiene — but it must be stated,
  because the obvious "fix" (normalizing 111 historical plans to a strict flag) is a
  100+-file sweep nobody asked for and `bp-137` explicitly forbids it (§9).
- **Whether the flag should become a real front-matter key** (`touches_stored_data: false`,
  per-item, machine-read) is a change to the build-plan template and therefore to
  `dn-agent-workflow` §"Front-matter schemas" — an owner-ratified amendment, not a builder's
  edit. **Re-entry:** raise it with the owner alongside the `oq-0047` ftype ruling
  (`docs/inbox/owner-questions.md:1653`), which is the same class of defect — a vocabulary the
  design record names as machine-readable and no code ever reads.

## Routing

`spec-defect`. The *implementation* half is `spec-fidelity` → the builder settles it inside
`bp-137` against the pinned regex, annotates, continues. The *template/schema* half is
`design` → **orchestrator**, batched to `owner-questions.md` when the owner next sits with the
ftype question. `dn-autopilot-and-delegated-blessing` is ratified and agent-immutable (A8):
§2.4's P3 row changes by a superseding note or an owner-ratified amendment, never by an edit.
