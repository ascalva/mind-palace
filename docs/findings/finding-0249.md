---
type: finding
id: finding-0249
status: open
created: 2026-07-27
updated: 2026-07-27
links:
  - docs/findings/finding-0238.md                  # bp-124's audit — the tautological banner assertion
  - docs/findings/finding-0242.md                  # bp-125's audit — absence proved, coherence not
  - docs/findings/finding-0246.md                  # the gate silenced by an ordinary act
  - docs/findings/finding-0247.md                  # bp-126's audit — the rc==1 collision, N1 survivor
  - docs/findings/finding-0248.md                  # clause (f) reading the wrong end
  - docs/build-plans/bp-127/plan.md                # §2 entries 11 and 13 — two more caught pre-emptively
  - .claude/skills/build-plan/SKILL.md             # where the mutation rule should land
  - docs/brainstorms/context-load-as-a-feedback-loop.md   # the destructive-loop diagnostic this mirrors
ftype: discovery
origin_plan: bp-126
route: orchestrator
resolution: null
---

# A check that passes without testing its claim: SEVEN instances in one wave make it a class, not a run of incidents

## The observation

The role-state wave (bp-124 → bp-127) produced, in a single night, seven distinct instances of the
same defect: **a check that returns green without ever exercising the thing it claims to verify.**

| # | Where | What passed without testing its claim |
|---|---|---|
| 1 | bp-124 | The `GENERATED_BANNER` assertion is **tautological in its own constant** — emptying the banner survives. The pre-existing board test has the identical shape. |
| 2 | bp-125 | Item 10's criterion was `grep -c 'resume-brief' = 0`. It proved **absence**, not **coherence** — a dangling `"say so in the brief"` survived in a live contract file. |
| 3 | bp-126 | Item 14's live-file deletion would have been **"satisfied vacuously"** in a worktree, by the plan's own admission — deleting a file that was never there. |
| 4 | bp-126 | `_handoff_is_stale` keyed on `rc == 1`, which Python also returns for **any unhandled exception** — so a crash read as staleness. |
| 5 | bp-126 | Clause (f) keys on **physical file position**, not recency, so any journal whose last `## ` section is standing boilerplate passes vacuously — the ordinary shape of a template-minted journal (`finding-0248`). |
| 6 | bp-127 | F2's drill **spawns an agent in-tree**, which silences the very gate it is drilling. A green F2 would have proven nothing. |
| 7 | bp-127 | An **unanchored** `## CAPSULE` grep matches the journal's own prose *defining* the marker — linting a fragment while reporting success. |

Instances 6 and 7 were caught **before** they were built, by reading the plan against what the wave
had already learned. The other five were caught by execution — four of them by an independent
auditor, after the builder's own gate had gone green.

## Why this is a class and not a coincidence

Every instance has the same structure: **the observable that the check consumes is not causally
downstream of the property being claimed.** An empty banner still contains the empty string. An
absent file is still absent when you delete nothing. A crash still exits 1. The oldest entry is
still an entry. A silenced gate still returns ALLOW.

Each check therefore has a **degenerate input on which it is trivially satisfied**, and nothing in
the ordinary build loop distinguishes that input from a genuine pass. Green becomes the evidence
for green.

⚑ **This is structurally the same shape as the authority-laundering criterion** in the
destructive-loop diagnostic: a result becomes true by being asserted, rather than by being
grounded. There it is a claim about who said something; here it is a claim about whether something
was verified. In both cases the artefact that should carry evidence carries only its own output.

## The measured lesson — and it is the actionable part

Across this entire wave, **both surviving mutants were found by mutating and running. Neither was
found by reading.** Both survived careful human-grade review by a competent agent:

- bp-126's builder mutated its own gate four ways; **one survived** — keying check 2 to
  `last_commit`, i.e. *the re-arming bug itself*, masked by the convergence test.
- The auditor mutated it eight ways; **one survived** — the `except Exception` fail-open branch was
  never exercised by any test, so the safety net the whole fix depends on was unproven.

Neither is an exotic case. Both are the kind of thing review is *supposed* to catch, and review did
not catch either.

> **Where a gate is load-bearing, budget for mutation.**

Review establishes that code *reads* correctly. Only mutation establishes that a test would
*notice* if it stopped being correct. For a check whose green result will be consumed as evidence
by a human or a downstream agent, the second property is the one that matters.

## ⚑ A postscript that is itself evidence

`finding-0248` — instance 5 above — was **first filed by the orchestrator on a false premise**
(that journals are newest-first; they are oldest-first). The premise was wrong, the conclusion was
right, and the true defect turned out to be **wider** than the wrong reason implied.

That is not the vacuous-pass shape, but it is its close cousin and it belongs in the record: **a
claim that reached a durable artifact without anything checking it.** It was caught the same way
everything else in this wave was caught — by someone re-deriving it rather than re-reading it.

The lesson generalises past tests. *Green becomes evidence for green* has a prose analogue:
**plausible becomes evidence for true.** The countermeasure is the same in both cases — construct
the case that would distinguish them, and run it.

## Proposed action

1. **`.claude/skills/build-plan/SKILL.md`** — for any item whose deliverable is a **gate, lint,
   ratchet, or audit**, require the §7 acceptance to name the **degenerate input** on which the
   check would trivially pass, and to assert the check **reddens** on it. This is a sharper
   instrument than the existing named-falsifier rule: a falsifier says what failure looks like; this
   says what a *false* success looks like.
2. Same file — record the mutation rule above, scoped to load-bearing gates rather than all code,
   so it is proportionate.
3. `finding-0248` is the open instance with no home; it needs a plan.

## What is NOT claimed

- Not that the builders were careless. Five of seven were caught **by this wave's own machinery** —
  independent audit, mutation, and pre-emptive plan reading. The process worked; the point is that
  it had to, repeatedly, for the same reason.
- Not that every check needs mutation. The proposal is deliberately scoped to gates and lints,
  where a false green is consumed as evidence.
- Not that this is novel in general — it is standard test-quality practice. The finding is that
  **this repository has now measured its own rate**, and the rate is high enough to justify making
  it a rule rather than a habit.
