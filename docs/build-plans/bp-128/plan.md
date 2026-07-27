---
type: build-plan
id: bp-128
track: workflow
status: ready
design_ref:
  - docs/design-notes/session-handoff-gate.md
contract: builder
write_scope:
  - .claude/hooks/_lib.py
  - tests/unit/test_stop_audit.py
  - tests/integration/test_journal_gate.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 250k
  actual: null
depends_on: []
parallelizable_with: []
created: 2026-07-27
updated: 2026-07-27
links:
  - docs/findings/finding-0248.md
  - docs/findings/finding-0249.md
  - docs/brainstorms/the-false-success-rule.md
  - .claude/skills/checkpoint/SKILL.md
warrant: docs/findings/finding-0248.md
supersedes: null
superseded_by: null
---

# Build Plan — clause (f) must key on RECENCY, not on physical file position

## 0. Mode & provenance

**Tech-debt correction of committed code**, warranted by `finding-0248` (ftype `codebase`, routed
to the orchestrator, no home plan until this one). Not a graduation: the mechanism it repairs is
already ratified in `dn-session-handoff-gate`; this plan restores the gate to what that note says
it does. Owner authorised the fix directly (2026-07-27): *"you have my permission to fix it, or at
least rule on the fact that it will be fixed."* The ruling was to plan it rather than hand-patch —
see §10.

## 1. Objective

Clause (f) of the Stop-gate audit verifies a session wrote a fresh journal entry. It extracts the
**tail** — content after the **last** non-Follow-through `## ` heading — and checks it for the
required shape. That extraction assumes **the newest entry is physically last in the file**.
Clause (f) has no notion of recency; it keys purely on **file position**.

⇒ **Any journal whose last `## ` section is not its newest entry satisfies clause (f) vacuously.**
That is the ordinary shape of a template-minted journal — standing sections (pre-build notes, owed-
at-seal) trail the entries. Observed live in `docs/build-plans/bp-126/journal.md`, where the check
was satisfied by a **backticked mention inside pre-build notes**.

**Done means:** clause (f) passes only when the journal genuinely gained a compliant fresh entry
this session, and **reddens** on the degenerate input that currently passes it.

### 1.2 Non-goals

- **Not** a rewrite of the journal contract (`.claude/skills/checkpoint/SKILL.md` §9). The contract
  is correct; the *check* is unfaithful to it. `[INFERENCE]` — the owner reads non-goals explicitly
  at blessing, so state the alternative considered: reshaping journals so the newest entry is
  physically last would also close the hole, and is **rejected** because it fixes one file shape
  while leaving the check wrong for every other, and would invalidate every existing journal.
- **Not** a change to clause (e′), (a)–(d), or the `journal-gate` diff audit. Same file, different
  clauses; blast radius stays one clause.
- **Not** a change to `docs/templates/build-plan.md` or any existing journal. The check adapts to
  the artifacts, not the reverse.

## 2. Context manifest

| # | Artifact | Why it is required |
|---|---|---|
| 1 | `.claude/hooks/_lib.py` — `cmd_stop_audit`, clause (f) | the defect and the only production edit |
| 2 | `docs/findings/finding-0248.md` | the warrant; ⚑ read its **correction notice** — first filed on a false premise |
| 3 | `docs/findings/finding-0249.md` | the vacuous-pass class this instance belongs to; carries the mutation rule |
| 4 | `docs/brainstorms/the-false-success-rule.md` | the degenerate-input discipline this plan is the first customer of |
| 5 | `.claude/skills/checkpoint/SKILL.md` §9 | the journal contract clause (f) is auditing — the source of truth for "compliant entry" |
| 6 | `docs/build-plans/bp-126/journal.md` | the live instance; the reproduction case |
| 7 | `docs/design-notes/session-handoff-gate.md` | ratified; what the gate is *supposed* to guarantee |

⚑ **Does core already have this?** Checked: recency-vs-position is a hook-local concern; there is no
existing helper in `_lib.py` for entry extraction to reuse or extend. Confirm at Item 1 rather than
trusting this line.

## 3. Investigation & grounding

The mechanism is **deliberately not pinned** — three candidates, to be grounded before Item 2:

- **(a) Diff-derived.** The `journal-gate` already computes a session diff. If the added lines can
  be attributed to a `## ` section, the fresh entry is identified directly rather than guessed.
- **(b) Heading-timestamped.** §9 entries carry a timestamp in the heading; select the max rather
  than the last. Cheap, but fails on a malformed or missing stamp — **which must fail OPEN**.
- **(c) Standing-section exclusion.** Name the trailing standing sections and skip them. Rejected on
  sight as a denylist that rots, but record why in the journal rather than skipping it silently.

**Q1 — which candidate, and does it hold for a journal whose only entry IS the last section?**
**Q2 — what is the failure mode when recency cannot be determined?** ⚑ It must be **fail-open**.
bp-126 was returned once for exactly this: a clause that fails closed on a tooling error wedges
every close, *including the session trying to fix it*.

## 4. Reconciliation

Clause (f) currently passes on journals that do not comply. Fixing it will make **previously green
journals red**. Establish before Item 3 how many existing plan journals would now fail, and record
the number. If the fix would redden the repo broadly, that is a **stop-and-raise** (§10), not a
thing to absorb quietly.

## 5. Write scope

- `.claude/hooks/_lib.py` — clause (f) only. Every other clause is out of bounds in this diff.
- `tests/unit/test_stop_audit.py` — the degenerate-input and recency tests.
- `tests/integration/test_journal_gate.py` — end-to-end proof against a real journal shape.

⚑ `docs/findings/**` is builder-writable by contract and is where a `codebase` finding is filed —
not listed here, and not needed here.

## 6. Interfaces pinned inline

Clause (f)'s contract, unchanged by this plan: it consumes the plan journal and returns a
BLOCK/ALLOW verdict at Stop. **A BLOCK is a hard deny** — that is why §3 Q2 is load-bearing. The
Follow-through section remains excluded from tail extraction, per the existing behaviour.

## 7. Items

**Item 1 — Ground the mechanism.** Answer §3 Q1/Q2 against the code; record the rejected candidates
and why. *Acceptance:* the journal names the chosen mechanism and its fail-open behaviour, citing
`_lib.py` line numbers. *Falsifier:* if no candidate yields a determinate newest entry for a
single-entry journal, stop and raise — the contract itself is ambiguous.

**Item 2 — Implement, fail-open on indeterminacy.** *Acceptance:* clause (f) identifies the newest
entry by recency, not position. *Falsifier:* the six-mode matrix — genuine-fresh, stale, malformed
heading, missing timestamp, empty journal, single-entry-is-last — with **every** indeterminate mode
resolving to ALLOW. Measure by execution, not by reading.

**Item 3 — ⚑ The degenerate input, named and reddened.** This plan is the first customer of the
false-success rule (`the-false-success-rule.md`), so its acceptance is written in that form.
*Degenerate input:* a journal carrying **trailing standing sections and no fresh entry** — the exact
shape of `bp-126/journal.md` at the moment it passed vacuously. *Acceptance:* clause (f) **reddens**
on it, and the test asserts the redness, not merely that a compliant journal is green.
*Falsifier:* run the test against the **unfixed** clause — it must pass there, proving the test
distinguishes the fix from its absence rather than pinning a constant.

**Item 4 — Mutation pass on the fixed clause.** Per `finding-0249`: where a gate is load-bearing,
budget for mutation. *Acceptance:* ≥4 mutants (invert the recency comparison; drop the fail-open
arm; widen the section match; remove the standing-section handling), each **caught** or explicitly
justified as equivalent. *Falsifier:* a surviving non-equivalent mutant means the tests do not pin
the behaviour — return to Item 3 rather than sealing.

**Item 5 — Reconcile the existing corpus.** Report how many repo journals change verdict (§4).
*Acceptance:* the number is in the journal. *Falsifier:* if it is large enough to require mass
journal edits, stop and raise — that is a scope change, not a fix.

## 8. Math carried explicitly

N/A — no quantity is modelled; the change is a predicate over file structure.

## 9. Non-goals

See §1.2 — the load-bearing ones are stated there so the owner reads them at blessing.

## 10. Stop-and-raise conditions

- **The fix would fail closed on any indeterminate input.** Non-negotiable; bp-126's first return.
- **The reconciliation count is large** (§4/Item 5) — mass-reddening the repo is a decision, not a
  consequence.
- **The journal contract turns out ambiguous** about which entry is newest — that is a `checkpoint`
  skill change and belongs to the owner, not to this builder.

⚑ **Why this is a plan and not a hand-patch.** Clause (f) lives in `_lib.py`, the same file and gate
family where bp-126 was returned **twice** in one night — once for a fail-closed wedge that would
have deadlocked every session close in the repo, including the one trying to repair it. The wave
measured that **both** of its surviving mutants were found by mutating and running, neither by
reading, both after careful review. A Stop-gate edit made without a write_scope, an auditor, or a
mutation campaign is the precise act this repository has now priced. The owner's permission to fix
is honoured by fixing it *properly*, not faster.

## 11. Parked decisions

None. `re_entry: null`.

## 12. Dependency & ordering summary

No dependencies; parallelizable with any plan holding a disjoint scope. ⚑ **Not** parallelizable
with bp-127 in practice — both touch the Stop-gate's behaviour, and bp-127's F2 drill exercises the
close path this clause governs. Order: bp-127 first, or serialize.
