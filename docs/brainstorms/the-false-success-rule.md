# the-false-success-rule

## 2026-07-27T05:30:00Z

```capsule
topic: the-false-success-rule
date: 2026-07-27
status: OWNER AGREED with the skill change (2026-07-27). Not yet written — a skill edit needs a plan.

seed: |
  Owner, on finding-0249's proposal: "I completely agree with the false success skill change."

warrant: docs/findings/finding-0249.md — seven instances in one wave (bp-124→bp-127), five caught
         by execution after a green build, two caught pre-emptively by reading the plan.
```

## THE RULE

For any build-plan item whose deliverable is a **gate, lint, ratchet, or audit**, §7 acceptance must:

1. **Name the degenerate input** — the case on which the check would pass *without testing its claim*.
2. **Assert the check reddens on it.**

⚑ **This is a sharper instrument than the existing named-falsifier rule, not a duplicate of it.**

| instrument | answers |
|---|---|
| named falsifier (existing) | *what does failure look like?* |
| **degenerate input (new)** | *what does a **false success** look like?* |

A falsifier proves the thing can fail. This proves the **check can tell**.

## WHY IT EARNS A RULE — the measured part

Every one of the seven instances has the same structure: **the observable the check consumes is not
causally downstream of the property being claimed.**

- An empty banner still contains the empty string.
- An absent file is still absent when you delete nothing.
- A crash still exits `1`.
- The oldest journal entry is still an entry.
- A silenced gate still returns `ALLOW`.

So each check has an input on which it is trivially satisfied, and **nothing in the ordinary build
loop distinguishes that input from a genuine pass.** Green becomes the evidence for green.

⚑ **Same shape as authority-laundering** in the destructive-loop diagnostic
([[context-load-as-a-feedback-loop]], criterion 4): a result becomes true by being asserted rather
than grounded. There the claim is *who said something*; here it is *whether something was verified*.
Both times, the artifact that should carry evidence carries only its own output.

## THE COMPANION RULE — where a gate is load-bearing, budget for mutation

⚑ **Both surviving mutants across the entire wave were found by mutating and running. Neither was
found by reading.** Both survived careful review by a competent agent — and neither was exotic:

- the builder's own gate, keyed to the re-arming bug it was fixing, masked by the convergence test;
- the `except Exception` fail-open branch, never exercised, so the safety net the whole fix rested on
  was unproven.

> Review establishes that code **reads** correctly. Only mutation establishes that a test would
> **notice** if it stopped being correct.

For a check whose green will be consumed as evidence by a human or a downstream agent, the second
property is the one that matters. Scope the rule to load-bearing gates, not all code — proportionate.

## ⚑ IT GENERALISES PAST TESTS

`finding-0248` was filed on a **false premise** (journals are newest-first; they are oldest-first).
Wrong reason, right conclusion — and the true defect was *wider* than the wrong reason implied.

⇒ *Green becomes evidence for green* has a prose analogue: **plausible becomes evidence for true.**
Same countermeasure both times — **construct the case that would distinguish them, and run it.**

`[INFERENCE]` The prose half may deserve its own treatment in the **finding** and **checkpoint**
skills, not just `build-plan`. Not ruled; the owner agreed to the *gate* rule specifically.

## NEXT

A skill edit is a build, not a capture — `.claude/skills/build-plan/SKILL.md` needs a plan, and this
capsule is its warrant. Also open: `finding-0248` (clause (f) keys on physical file position, so any
journal with trailing standing sections passes vacuously) has no home plan.

## NOT CLAIMED

- Not that the builders were careless — five of seven were caught **by this wave's own machinery**.
  The process worked; the point is that it had to, repeatedly, for the same reason.
- Not that this is novel practice in general. The finding is that **this repo measured its own rate**,
  and the rate is high enough to justify a rule rather than a habit.
