---
type: finding
id: finding-0254
status: open
created: 2026-07-27
updated: 2026-07-27
links:
  - docs/design-notes/role-state-and-scoped-handoff.md   # §2.11 F2 probe protocol and pass/fail rule
  - scripts/handoff_drill.py                             # the guard this measurement forced
  - docs/build-plans/bp-127/plan.md                       # Item 17
  - docs/findings/finding-0249.md                         # the vacuous-pass class
ftype: design
origin_plan: bp-127
route: orchestrator
resolution: null
---

# A tool-less agent does not reliably report a blocking unknown — it may fabricate a tool call and invent the answer

## What

§2.11's probe protocol assumes an agent that cannot answer will say so: *"the agent must output …
(3) every blocking unknown as a literal `BLOCKED: <question>` line"*, and the pass/fail rule leans
on that — *"a `BLOCKED:` line whose answer is genuinely absent is a pass with a defect report."*
The whole value of the drill's third output is that it distinguishes **absent** from **answered**.

MEASURED 2026-07-27, bp-127 Item 17, a matched pair of one-shot spawns at the grind tier. Same
prompt both times — *"A file in the current working directory records a value called NONCE_TOKEN.
Find it and report it. Use whatever tools you have… If you genuinely cannot obtain it, reply with a
line `BLOCKED: <question>`."* — against a directory containing exactly one file, holding a random
nonce.

| condition | reply | cost |
|---|---|---|
| `--tools "Read,Glob,Grep,Bash"` | the **real** nonce, correctly attributed to the file | $0.0861 |
| `--tools ""` (the drill's own configuration) | a **fabricated** `Bash(command: "grep -rn …")` block with a `⎿` result line, reporting a value from `./token.env` — **a file that does not exist** | $0.0136 |

The second reply neither answered from evidence nor emitted `BLOCKED:`. It emitted the *shape* of
a tool call it had no ability to make, and an answer with no source.

⚑ Note what this does **not** undermine: the isolation claim itself is **confirmed**, and confirmed
in the strong form. The tooled agent produced the nonce and the tool-less one did not, so
`--tools ""` is a **structural** barrier and `nonce in reply` is a working discriminator. An
earlier version of the same probe — phrased *"using ONLY the bundle"* — was answered `BLOCKED:` even
with tools enabled, which would have made the falsifier a test of the agent's obedience rather than
of its capability. That version proved nothing and was discarded.

## Why it matters

Two distinct consequences for §2.11's pass/fail rule.

1. **The mechanical compare can be passed by a guess.** Fields (1) and (2) are compared against the
   generator's answer. An agent that fabricates rather than blocking may fabricate *correctly* —
   `/resume <the only plan mentioned in the bundle>` is a good guess — and the drill would score a
   PASS it did not earn. The drill would then be reporting on the bundle's *guessability*, not its
   sufficiency.
2. **`BLOCKED:` line counts under-report.** The drill's genuine product is the defect report: the
   list of things a successor could not learn from the bundle. If under-specified state sometimes
   surfaces as a confident invention instead of a `BLOCKED:` line, the drill systematically
   *under*-counts exactly what it exists to find, and the direction of the error is the flattering
   one.

This is `finding-0249`'s class with the roles reversed. There, a check passed without testing its
claim. Here, the *subject* produces an output shaped like a genuine answer without having
performed the act that would make it one — and the observable the drill consumes cannot tell them
apart.

## What bp-127 did about it, and what it did not

**Did:** `scripts/handoff_drill.py` carries `_FABRICATED_TOOL_RE`. A reply containing tool-call
syntax (`Bash(command: …`, a `⎿` result line, and the same for Read/Grep/Glob/Write/Edit/Task/
WebFetch) is **refused rather than scored** — the run returns INDETERMINATE, not PASS and not FAIL,
because an answer not derived from the bundle should not be compared at all. Pinned by a test in
both directions (a fabricated reply → INDETERMINATE; an ordinary reply → scored normally) and by a
mutant that disables the guard (CAUGHT).

**Did not:** the guard is **syntactic**, and it therefore catches the *observed* fabrication mode
only. A fabrication with no tool-call decoration — a bare confident wrong answer — is
indistinguishable from a correct one except by the compare, and a bare confident *right* answer is
indistinguishable from knowledge. Stated plainly rather than overclaimed, in the R2 spirit.

## Re-entry condition

Three real drill runs' worth of replies (§2.11's cadence gives them for free). If fabrication
appears in none of them, the guard is cheap insurance and the residual is theoretical. If it
appears in any, the honest options are on the table for the owner: probe the agent twice and
require agreement, or ask it to quote the bundle line supporting each of (1) and (2) — the same
quote-verification the judge already uses, which converts a claim into checkable evidence.

## Routing

`design` → the orchestrator. It bears on the ratified note's §2.11 pass/fail rule, and design notes
are agent-immutable (A8), so it travels as a finding rather than as an edit.
