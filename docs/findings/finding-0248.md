---
type: finding
id: finding-0248
status: open
created: 2026-07-27
updated: 2026-07-27
links:
  - .claude/hooks/_lib.py                          # cmd_stop_audit clause (f) — the tail extraction
  - .claude/skills/checkpoint/SKILL.md             # §9 — the journal contract it audits
  - docs/templates/build-plan.md                   # the minted shape whose trailing sections defeat it
  - docs/build-plans/bp-126/journal.md             # where it was observed, and self-corrected
  - docs/findings/finding-0246.md                  # the other Stop-gate integrity defect from this wave
  - docs/findings/finding-0249.md                  # the class this belongs to
ftype: codebase
origin_plan: bp-126
route: orchestrator
resolution: null
---

# Clause (f) keys on PHYSICAL FILE POSITION, so any journal with trailing standing sections passes it vacuously

## ⚑ Correction notice — this finding was first filed on a false premise

**As originally filed (2026-07-27) this finding claimed §9 journals are *newest-first*, and that
clause (f) therefore always reads the oldest entry. That premise is wrong and is retracted.**
Journals are **oldest-first**. The observed tail was the pre-build notes simply because those are
the original file body.

**The conclusion survives the retraction, and the true defect is WIDER than first stated.** The
correction is recorded here rather than silently rewritten, because a wrong reason that arrives at
a right conclusion is durable misinformation — and leaving it inside the very finding that reports
`finding-0249`'s class would be an instance of that class.

## The actual defect

Clause (f) verifies that a session's journal carries a fresh entry by extracting the **tail** — the
content after the **last** non-Follow-through `## ` heading — and checking it for the required
shape.

That extraction assumes **the newest entry is physically last in the file**. Clause (f) has no
notion of recency at all; it keys purely on **file position**.

Therefore **any journal whose last `## ` section is not its newest entry satisfies clause (f)
vacuously** — the check reads standing boilerplate and reports that the session did its work.

⚑ **This is not an exotic shape. It is the ordinary shape of a template-minted journal**, which
carries standing sections below the entry area. The defect is a mismatch between what the clause
*measures* (position) and what it *claims* (recency), and it is latent in the default artifact the
templates produce — not a quirk of one ordering convention.

Observed concretely during bp-126: the clause was satisfied by a **backticked mention inside
pre-build notes** — text predating the build entirely, asserting nothing about whether the session
did any work.

## Why this matters

Clause (f) is one of the checks that makes a Stop-gate BLOCK meaningful. A gate that accepts
non-compliant journals is worse than an absent one, because it issues a green verdict that a human
or a downstream agent will read as evidence. The journal contract exists so a fresh agent can
resume from artifacts alone; a clause satisfied by boilerplate certifies precisely the sessions
least likely to meet that bar.

Same failure shape as `finding-0246` (a gate silenced by an ordinary act), and a member of the
class in `finding-0249`: **a check that passes without testing its claim**.

## Scope

**Repo-wide, and broader than any single ordering convention.** bp-126's builder fixed *its own
file* by moving the required block to the physical end, which satisfies the clause as written. It
correctly declined to fix the clause itself — the general defect was outside its items, and
widening scope mid-build is what this wave's discipline forbids. That decision is why this finding
exists: *"pre-existing and outside my scope"* is the case a finding is **for**.

## What is NOT claimed

- Not that any past seal was dishonest. A vacuous pass means those seals were **unverified**, not
  that they were false.
- Not that bp-126 introduced this. It is pre-existing and independent of clause (e) → (e′).
- Not that the fix is obvious. Reading the *first* `## ` heading is not automatically correct
  either. The fix must decide **what makes an entry authoritative** — position, an explicit marker,
  or a timestamp — and enforce that decision, rather than silently assuming a layout.

## Route and re-entry

Routed to the **orchestrator** because it has **no home**: bp-126 holds `.claude/hooks/**` and is
completing, and no `ready` plan carries that surface afterwards — the same homelessness
`finding-0237` and `oq-0059` describe.

**Re-entry condition:** the next plan that puts `.claude/hooks/_lib.py` in `write_scope` inherits
this as a required item.

⚑ **Its acceptance must name the degenerate input and assert the clause REDDENS on it** — a journal
whose newest entry is non-compliant while its trailing standing section is compliant. A fix
verified only by the clause going green would reproduce the defect it repairs, which is the whole
lesson of `finding-0249`.
