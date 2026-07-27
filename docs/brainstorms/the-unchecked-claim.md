# the-unchecked-claim

## 2026-07-27T05:50:00Z — a retrospective

```capsule
topic: the-unchecked-claim
date: 2026-07-27
kind: retrospective (no such artifact type exists yet — see OPEN)

seed: |
  Owner, on finding-0248: "so finding-0248 feels like a lesson-learned, could be a well documented
  retrospective, with the intent of hopefully not repeating the same mistake twice."

scope: |
  The MISTAKE half of finding-0248, generalised. ⚑ NOT the defect half — see the fence below.
```

## ⚑ FENCE — 0248 is two things, and only one of them is a retrospective

| half | what it is | what it needs |
|---|---|---|
| **the defect** | clause (f) keys on **physical file position**, so any journal with trailing standing sections passes vacuously | **a plan and a fix — it is LIVE right now**, accepting non-compliant journals repo-wide |
| **the mistake** | it was *filed on a false premise* (journals newest-first; they are oldest-first) | this retrospective |

⇒ **The retrospective is in addition to the fix, never instead of it.** A finding converted into a
lesson stops being routed as work. 0248 still has no home plan.

## THE PATTERN — six instances, and only one is 0248

Every one is a **claim that reached a durable artifact without anything checking it.**

| # | the claim | where it landed | how it was caught |
|---|---|---|---|
| 1 | "§9 journals are newest-first" | `finding-0248`, as its stated reason | re-derived by its own author |
| 2 | "the reference substrate has no `corpus_to_corpus` edges" | the resume brief, as a "known gap" | a Fable agent read the code: **644,785 exist** |
| 3 | "a mutation proves widening to `rc != 0` is caught" | relayed by me to the sub-orchestrator | re-run: **A1 is an equivalent mutant, it survives** |
| 4 | "six rules were dropped as already-home" | a seal, then a report built on it | the seal's **own table** said four |
| 5 | "the gate has 1 expected failure" | copied seal → seal as fact | it had become false; nothing noticed |
| 6 | `_lib.py:762` (mis-cited line) | propagated into a **Fable design prompt** | caught downstream, after spending |

Instances 5 and 6 predate tonight ([[context-load-as-a-feedback-loop]], L4). **Two of these are
mine** (#2, #3) — #2 I wrote into an authoritative file, #3 I amplified by forwarding it.

## ⚑ THE STRUCTURAL DIAGNOSIS — all six share one property

**Every claim cited a SECONDARY source, and the hop went unmarked.**

- #1 assumed the journal's shape instead of opening one.
- #2 cited a **two-week-old capsule about the code** instead of the code. (bp-026 had built the
  edges in between. The capsule was true when written — that is exactly what makes it dangerous.)
- #3 forwarded another agent's sentence without re-running it.
- #4 repeated a table's arithmetic without adding it up.
- #5 copied a previous seal.
- #6 carried a line number nobody re-opened.

⇒ *Green becomes evidence for green* ([[the-false-success-rule]]) has this prose twin:
**plausible becomes evidence for true.** A claim gets **stronger** at each hop — it sheds its
hedges and gains the authority of the document it lands in — while getting **further** from what
made it true. Age alone can falsify it, and nothing re-checks a sentence already written down.

⚑ Same as criterion 4 of the destructive-loop signature: *a statement becomes true by being in the
document.* That criterion was written about this repo's own workflow. It has now been measured in it.

## THE CANDIDATE RULE — cite primary, or mark the hop

`[INFERENCE]` **A claim in a durable artifact either (a) cites its primary source — the code at
`file:line`, the file, the measurement — or (b) is explicitly marked as relayed/unverified.**

The repo already has the machinery: `[INFERENCE]` markers are mandatory in design notes and the
owner reads them at ratification. This extends the same discipline from *reasoning* to *citation*.
A secondary citation is not forbidden — it is **marked**, so the next reader knows the hop exists.

Sharpest single test, and the cheapest: ⚑ **if a claim cites a capsule, seal, finding, or another
agent rather than the thing itself, it is unverified until re-derived.** All six instances would
have been caught by that one question.

## WHAT ACTUALLY CAUGHT THEM — the transferable part

**Not one of the six was caught by re-reading. Every one was caught by re-deriving** — running the
code, opening the file, re-doing the arithmetic, re-running the mutation.

That is the *identical* lesson as the test half: *both surviving mutants in the wave were found by
mutating and running, neither by reading.* ⇒ **One lesson, two surfaces:**

> Review confirms a claim is **plausible**. Only re-derivation confirms it is **true**.

## OPEN

- **`finding-0248`'s defect still needs a home plan.** Unchanged by this capsule.
- **Is `retrospective` a real artifact type?** This is filed as a brainstorm because none exists.
  A retrospective is not a brainstorm (it looks backward at measured events, not forward at ideas)
  and not a finding (it is a class, not an instance). ⚑ Owner's call — a new type touches the
  artifact chain, so it is not an agent's to mint.
- `[INFERENCE]` The candidate rule may belong in the **finding** and **checkpoint** skills, where
  claims enter durable artifacts. The owner agreed to the *gate* rule ([[the-false-success-rule]]);
  **this prose rule is not yet ruled on.**

## NOT CLAIMED

- Not that anyone was careless. Five of six were caught by this system's own machinery, and #1 by
  its own author. The point is that the machinery had to catch them, repeatedly, for one reason.
- Not that secondary citation is bad — it is how work compounds. The defect is the **unmarked** hop.
