# context-load-as-a-feedback-loop

## 2026-07-26T00:00:00Z

```capsule
topic: context-load-as-a-feedback-loop
date: 2026-07-26

seed: |
  Owner, verbatim: "let's track the evolutions of your context load exploded with past and present
  conversations, looping back into itself: a feedback, our first study of a feedback loop, and
  that's useful for us because that's a tool we could then use to help us detect destructive
  feedback loops in the graph, and how to understand what it would take to detangle the knot."

⚑ why THIS instance is worth studying rather than just fixing: |
  We rarely get a complete one. Session-55 produced a feedback loop with **all three parts present
  at once** — a BEFORE measurement, an INTERVENTION already designed and ratified, and a way to
  measure AFTER. Most loops are noticed only after they have already done their damage, with no
  baseline to compare against.

    before        measured tonight (below)
    intervention  `dn-role-state-and-scoped-handoff`, RATIFIED 2026-07-26, graduated to bp-124..127
    after         the same counters, re-taken once those plans land

  That makes it a **calibration subject**, not just a chore — and it is the cheapest possible one:
  no corpus, no market, no money, no counterparty.

## THE MEASUREMENTS (session-54/55, one machine, one day)

| quantity | reading | note |
|---|---|---|
| resume brief, peak | **568 lines** | read at EVERY session start by every agent |
| resume brief, after clearing | **83 lines** | owner instruction, 2026-07-26 |
| stale-gate (clause e) firings | **17 in one session** | each one costs a turn |
| prior sessions' firings | 5 (s-52) · 4 (s-53) | the loop predates tonight |
| self-contradictions introduced | **3**, same line | "nothing is running" under a table of what is running |
| Fable pass context spend | **≈90k tok**, self-attributed to grounding reads | "the 405-line brief, queue.py, board.py, _lib.py, four design notes, skills, PROGRESS tail" |
| `docs/PROGRESS.md` | **5,627 lines** (~70k tok) | grows every session; read for grounding |
| mandatory frame | **~5.8k tok** | CONSTITUTION+CLAUDE+CONVENTIONS — NOT the cost |
| code-sensor ledger | **1,204 → 1,230** in one evening | the corpus ingesting commits about the corpus |

⚑ **CORRECTION (owner-intent audit, 2026-07-27) — the clearing row dates the instruction to when it
was OBEYED, not when it was GIVEN.** The owner first granted it a full day earlier: *"also, I give
you permission to wipe the resume, you don't need a handoff right now"* (`2026-07-26T03:16:25Z`,
session `a73e8b34`, typed while the agent was mid-turn). It was not acted on, and he re-issued it
three times on the evening of 2026-07-26 before it was. ⇒ **The 17 clause-(e) firings measured above
were paid AFTER the intervention was already authorised** — they are the cost of the delay, not the
cost of the loop being undiagnosed. See `docs/brainstorms/owner-intent-audit.md` (L-4).

⚑ **The measurements disagree with the intuition, which is why they matter.** The obvious suspect
is the mandatory frame; it is ~6k tokens and irrelevant. The actual load is **re-derivation** —
agents rediscovering the same ground, and a hand-maintained summary restating what git already holds.

## THE LOOPS, named separately — they are not one loop

- **L1 — the accumulator.** Session writes brief → next session reads brief → does work → appends
  its own record → brief grows. Read cost is paid by every future session; write cost by one.
  **Monotonic: nothing in the cycle removes.**
- **L2 — the tight one, and the expensive one.** Commits land → clause (e) marks the brief stale →
  a turn is spent rewriting it → that turn may commit → stale again. **17 iterations measured.**
- **L3 — the destructive one.** I edit the brief with its previous version already in my context.
  I write a section that supersedes an earlier line and leave both. **The contradiction is then
  authoritative to the next reader — which is me.** Three instances, all the same line.
- **L4 — laundering.** A claim written once ("1 expected failure") is copied into seals as fact,
  never re-verified. It became false and nothing noticed. Related: the brief's `_lib.py:762`
  mis-citation propagated into a *Fable design prompt* before anything caught it.
- **L5 — corpus self-reference.** The code sensor ingests commit bodies at commit time. Tonight's
  ledger grew 26 entries, most of them my own prose about my own work. ⚑ **This is the one that
  reaches the built system rather than the workflow** — see the dreamer note below.

## ⚑⚑ THE DIAGNOSTIC SIGNATURE — the transferable part

A loop is **destructive** (not merely cyclic) when all four hold. Cycles are normal; these make one
amplify:

1. **SELF-MAINTAINED** — the same process both reads and writes the node.
2. **MONOTONIC** — each pass appends; no step in the cycle removes or compresses.
3. **NO EXTERNAL CHECK** — nothing outside the cycle can falsify a claim inside it.
4. **AUTHORITY LAUNDERING** — a statement becomes true by *being in the document*, not by being
   verified. ⚑ **This is the one that does the damage.** (1)-(3) cost tokens; (4) costs correctness.

Note (4) is finding-0222 ("a note is not a control") stated as a graph property rather than a
process complaint — which is what makes it detectable mechanically.

## ⚑ WHAT ACTUALLY BROKE LOOPS TONIGHT — the detangling levers, weakest first

- **CLEAR the accumulator** (568 → 83). ⚑ **Weakest lever: it resets amplitude, not structure.**
  The self-rewrite instruction survives, so it regrows. Useful for buying clean ground, not a fix.
- **A FRESH READER WITH SOURCE ACCESS.** The Fable pass caught the `:762` mis-citation *because it
  read `_lib.py` instead of the brief.* This is the single cheapest real fix observed: **an agent
  outside the cycle, reading the ground truth rather than the summary.** It broke L4 in one pass.
- **A GENERATOR.** A derived fact cannot drift if it is regenerated rather than copied. Kills L1's
  growth and L3's contradiction class outright — you cannot contradict what you do not hand-write.
- **A RATCHET.** A mechanical assertion outside the cycle. Turns (4) from a habit into a control.

⇒ Ranked, the levers are: **make it derived > check it from outside > clear it.** We did the last
one tonight; bp-124..127 do the first two.

## ⚑⚑ WHY THE OWNER'S FRAMING IS RIGHT — this generalizes to the graph, and to the DREAMER

The palace is a citation graph: notes cite notes, findings warrant plans, plans produce journals
that feed findings. **The four-part signature above is computable over that graph** — self-
maintenance is an edge from a node to its own author; monotonicity is length-over-time; the
external check is an in-edge from outside the strongly-connected component; laundering is a claim
with no falsifier edge.

⚑ **And it reaches the built system, not just the workflow.** `dn-synchronic-diachronic-dreamer`
conditions on "what exists" (§2.7's conditioning law — the difference between an opinion and a
confabulation is whether the substrate was real). **The code sensor ingests commit bodies, so the
corpus contains the system's own prose about itself.** A dreamer conditioning on that substrate can
dream about its own dreams. That is L5, and it is a *design* risk with real consequences for the
belief ledger (`dn-scored-beliefs`) — a belief scored against a corpus that contains the belief is
not scored against the world.

open_questions:
  - Is the signature's fourth clause **mechanically detectable**, or does "has no falsifier" require
    judgement? If detectable, it is a ratchet over the graph. If not, it is a review prompt. This is
    the difference between a tool and a checklist, and it is not obvious which it is.
  - What is the right **metric** for L1? Lines is crude. Tokens is better but model-dependent.
    ⚑ "Fraction of an agent's context spent on re-derivation" is the quantity we actually care
    about, and the Fable pass's ≈90k self-attribution suggests it is measurable but only by asking
    the agent — which is a self-report, and self-reports are exactly what this repo distrusts.
  - Does the graph already have the edges needed, or would detection require new ones? The citation
    graph exists; "who wrote this node" may not be an edge at all.
  - ⚑ Is there a **healthy** version of every loop here? Journals are self-maintained, monotonic,
    and largely unchecked — and they are the artifact chain's foundation. So the signature must
    distinguish a journal (append-only *record*, never re-read as authority) from a brief
    (append-only *summary*, re-read as authority every session). **The discriminator is probably
    clause (4), not (1)-(3)** — which is another argument that (4) is the load-bearing one.

next_steps:
  - Hold as a brainstorm; it is the **measurement subject** for bp-124..127, not a separate build.
  - ⚑ RE-TAKE THE COUNTERS after those plans land. The numbers above are the baseline and the whole
    value of this capsule; without an after-reading it is an anecdote.
  - The graph-detection tool is downstream of the spike artifact — "is the signature computable"
    is precisely a spike question, with an inconclusive outcome permitted.
```
