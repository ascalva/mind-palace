---
type: finding
id: finding-0256
status: open
created: 2026-07-27
updated: 2026-07-27
links:
  - docs/findings/finding-0249.md          # the vacuous-pass class and the mutation rule this refines
  - docs/brainstorms/the-false-success-rule.md
  - scripts/handoff_drill.py               # _SPAWN_FLAGS — the constant that WAS the mechanism
  - .claude/skills/build-plan/SKILL.md     # where the refined mutation guidance belongs
ftype: design
origin_plan: bp-127
route: orchestrator
resolution: null
---

# The mutation rule invites mutating BEHAVIOUR; a constant that IS the mechanism reads as inert and never gets mutated

## What

`finding-0249` established: *where a gate is load-bearing, budget for mutation* — because both
surviving mutants of the preceding wave were found by mutating and running, neither by reading.

`bp-127` honoured that rule seriously: **40 mutants across three campaigns**, which found two of its
own test suites to be vacuous (the F1c suite reported "8 passed" while catching **0 of 5**
property-destroying mutants, because it tested the last commit rather than the working tree).

**And it still shipped its single highest-value surface untested.** `scripts/handoff_drill.py`'s
`_SPAWN_FLAGS` — `("-p", "--safe-mode", "--tools", "", "--no-session-persistence",
"--strict-mcp-config", "--output-format", "json")` — **is** the drill's isolation mechanism.
`--tools ""` is the structural barrier that makes the fresh-agent test a test at all; `--safe-mode`
is what stops the spawn firing `SessionStart` and laundering the gate the drill exists to protect.

The independent pre-merge audit gutted that tuple to `("-p", "--output-format", "json")` and the
suite stayed **green — 120 passed**. `grep -rn "_SPAWN_FLAGS\|--tools\|safe-mode" tests/` returned
nothing.

⚑ **The builder's own diagnosis, asked for directly and worth more than the fix:** it was
**oversight, not a deliberate call** — *"the flag tuple read to me as configuration rather than as
mechanism, so it fell outside the frame I was mutating in."* Its generalization:
**"my campaign's blind spot was that I mutated behaviour and not constants."**

## Why it matters

This is `finding-0249`'s class reproducing **inside the plan written to honour `finding-0249`**, by
an agent that had the rule in front of it, applied it 40 times, and wrote the sentence *a property
is real only where something proves it* — while leaving the constant carrying that property unpinned.

That is not carelessness; it is a **frame defect in the rule as stated**. "Mutate the code" reads as
"mutate the logic". Conditionals, comparisons and branches present themselves as mutable; a tuple of
flags, a regex constant, a threshold, a path, a model name present themselves as *data* — inert,
declarative, obviously-correct-by-inspection. But when the mechanism **is** the datum, mutating the
logic around it proves nothing about it.

The consequence here would have been exactly the plan's own Item 17 falsifier: a future edit
dropping `--tools ""` yields a fully-tooled agent reading the whole repo, **with the suite still
green** — *"every future PASS is meaningless because it manufactures confidence."*

## The concrete residue — three untested surfaces, recorded so they are not rediscovered

Fixed before merge:

- **`_SPAWN_FLAGS` unpinned** → now `test_the_spawn_flags_ARE_the_isolation_mechanism`, asserting
  each flag by index and `--tools` paired with the empty string. Verified against the mutant that
  found it: re-applied → `1 failed, 61 passed`, failing on exactly that test; restored → `62 passed`.

Carried open, none blocking:

- **`--lint` precedence is documented in a comment and pinned by nothing.** The rule *"an actionable
  violation outranks an unanswerable check"* is reachable (journal unreadable + readings
  future-dated returns 3 instead of 1) and untested. No automated consumer yet.
- **⚑ `gate_verdict()` is never exercised for real.** Every containment test monkeypatches it. If
  `_lib.py`'s `stop-audit` dispatch were renamed, `gate_verdict()` would return the same usage
  string on both calls and the verdict compare — the load-bearing half of F2's containment
  invariant — would **silently become vacuous**, with no test noticing. Not broken today (dispatch
  confirmed present). The builder ranks this the highest of the three, and it is the same
  **self-masking** shape as the anchoring guard its own campaign found: two protections hiding each
  other from the mutation frame.
- **`_canon` normalisation-loosening is untested where substring-loosening is caught.** §11's V1
  names *normalisation* alongside fuzzy and substring as the forbidden resolution. Crude punctuation
  widenings die on existing negatives, but one collapsing a **structural** distinction (stripping
  `/` and `-` so `/resume bp-123` canonicalises equal to `resume bp123`) is pinned by nothing. One
  parametrized negative closes it.

## What is NOT claimed

- **Not that the mutation rule is wrong** — it worked, twice, on this very diff, finding defects that
  survived careful review by two competent agents. The claim is that its *scope* is under-specified.
- **Not that every constant deserves a mutant.** The rule must stay proportionate, which is what
  makes the refinement non-trivial: the test is not "is it a constant" but **"does the property the
  check claims live in this datum rather than in the logic around it?"**
- **Not measured:** whether other load-bearing constants in the repo are similarly unpinned. This
  finding names one instance and one mechanism; the sweep is not done.

## Re-entry condition

A plan holding `.claude/skills/build-plan/SKILL.md` — the same surface the false-success rule is
owed on (`docs/brainstorms/the-false-success-rule.md`, owner-agreed and not yet written). **Both
should land together**, because they are the same instrument seen twice: the false-success rule asks
*what does a false success look like*, and this asks *where does the property actually live*.

Proposed wording, one line beside the existing mutation guidance: **"Mutate the constants that carry
the property, not only the logic that reads them. A flag tuple, a regex, a threshold or a path that
IS the mechanism is a mutation target; that it looks like configuration is exactly why it is missed."**

The three surfaces above re-enter with the next plan holding `scripts/handoff_drill.py`.

## Routing

`design` → the orchestrator. Filed at seal by the sub-orchestrator that merged `bp-127`, from its
auditor's mutation campaign and the builder's own answer to a direct question about why the gap
existed. The builder's self-diagnosis is the load-bearing part and is quoted rather than paraphrased.
