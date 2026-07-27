---
type: finding
id: finding-0248
status: open
created: 2026-07-27
updated: 2026-07-27
links:
  - .claude/hooks/_lib.py                          # cmd_stop_audit clause (f) — the tail extraction
  - .claude/skills/checkpoint/SKILL.md             # §9 — the newest-first journal contract it audits
  - docs/build-plans/bp-126/journal.md             # where it was observed, and self-corrected
  - docs/findings/finding-0246.md                  # the other Stop-gate integrity defect from this wave
  - docs/findings/finding-0249.md                  # the class this belongs to
ftype: codebase
origin_plan: bp-126
route: orchestrator
resolution: null
---

# Clause (f) reads the WRONG END of a newest-first journal, so it has been passing vacuously repo-wide

## What was observed

Stop-gate clause (f) verifies that a session's journal carries a fresh entry. It extracts the
journal's tail — the content following the **last** non-Follow-through `## ` heading — and checks
that for the required shape.

But `§9` journals are written **newest-first**. The last `## ` heading in the file is therefore the
**oldest** entry, not the newest. Clause (f) has been auditing the wrong end of every newest-first
journal in the repository.

Observed concretely during bp-126: the builder's clause (f) check was satisfied by a **backticked
mention inside its own pre-build notes** — text that predates the build entirely and asserts nothing
about whether the session did any work.

## Why this matters more than the individual case

Clause (f) is one of the checks that makes a Stop-gate BLOCK meaningful. A gate that accepts
non-compliant journals is not merely useless — it is **actively harmful**, because it issues a
green verdict that a human or a downstream agent will read as evidence. The journal contract exists
so that a fresh agent can resume from artifacts alone; a clause that passes on the oldest entry in
the file certifies precisely the sessions least likely to satisfy that bar.

This is the same failure shape as `finding-0246` (the gate silenced by a nested SessionStart) and
belongs to the class catalogued in `finding-0249`: **a check that passes without testing its
claim**.

## Scope of the defect

**Repo-wide.** bp-126's builder fixed *its own file* by moving the required block to the physical
end of the journal, which satisfies the clause as currently written. It correctly declined to fix
the clause itself — `.claude/hooks/_lib.py` was in its `write_scope` but the general defect was
outside its items, and widening scope mid-build is exactly what the wave's discipline forbids.

That decision was right, and it is why this finding exists: *"pre-existing and outside my scope"*
is the case a finding is **for**. Until this is filed and homed, the defect lives nowhere but a
transcript — which is the failure mode `finding-0241` was raised about.

## What is NOT claimed

- Not that any specific past seal was dishonest. The clause passing vacuously means those seals
  were **unverified**, not that they were false.
- Not that bp-126 introduced this. It is pre-existing and independent of clause (e) → (e′).
- Not that the fix is obvious. Reading the *first* `## ` heading instead is not automatically
  correct either: the physical-end convention some journals now follow would then break. The fix
  must decide **which end is authoritative** and enforce that decision, rather than silently
  assuming one.

## Route and re-entry

Routed to the **orchestrator** rather than a builder because it currently has **no home**: bp-126
holds `.claude/hooks/**` and is completing, and no `ready` plan carries that surface afterwards.
The same homelessness that `finding-0237` and `oq-0059` describe.

**Re-entry condition:** the next plan that puts `.claude/hooks/_lib.py` in `write_scope` inherits
this as a required item — and its acceptance must be a test that **reddens on a newest-first
journal whose newest entry is non-compliant**, not merely a green run. A fix verified only by the
clause going green would reproduce the defect it repairs.
