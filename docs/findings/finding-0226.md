---
type: finding
id: finding-0226
status: open
created: 2026-07-26
updated: 2026-07-26
links:
  - docs/design-notes/dn-supervision-and-liveness.md   # §2.5 (thread rejection), V5
  - docs/build-plans/bp-110/plan.md                    # §7 Item 1 falsifier, §10 STOP
  - docs/build-plans/bp-110/journal.md                 # Checkpoint 1 — the measurement
  - docs/findings/finding-0169.md                      # the pure-CPU incident V5's load reproduces
ftype: spec-defect
origin_plan: bp-110
route: orchestrator
resolution: null
---

# V5 measured: a pure-CPU thread starves the supervisor loop's THROUGHPUT 2150×, but leaves it
# cycling at ~133 Hz — so "starves the loop" is not a liveness claim, and the thread rejection
# rests on cancellability, not on this number

## What

`dn-supervision-and-liveness` §2.5 rejects the thread execution model in one sentence:

> "**A thread is insufficient.** It restores loop liveness for IO-bound spans, but Python threads
> cannot be cancelled, and a pure-CPU wedge — precisely the finding-0169 incident, 96% CPU — holds
> the GIL and **starves the supervisor loop anyway** (V5 verifies the degree). The mode-4
> power-to-act never arrives."

bp-110 Item 1 took V5 (bp-110 journal, Checkpoint 1). The load is finding-0169's actual shape
(whole-set materialization + a Python-side predicate over 4,000 × 2560-dim rows, on repeat); the
loop is the real `Supervisor.tick()` over a real SQLite-backed `JobQueue`:

```
loop ALONE            :  987958 ticks in 3.0s ->   329318.9 ticks/sec   p50 latency 0.003 ms
loop + pure-CPU thread:     460 ticks in 3.0s ->      153.1 ticks/sec   p50 latency 7.518 ms
degradation           : 2150.4x slower (0.05% of the uncontended rate)  max latency 15.096 ms
(python 3.13.14, GIL enabled, sys.getswitchinterval() = 5.0 ms)
```

The throughput half of the claim is confirmed emphatically — **2150× degradation**, and per-tick
latency clamped at ~7.5 ms ≈ one `switchinterval`, the textbook signature of a loop whose
throughput has stopped being governed by its own work.

**But 153 ticks/sec is not a starved loop in the sense that matters to this note.** The supervisory
duties the note assigns the live loop — renew the §2.6 lease, record vitals, observe a batch
landing, notice a missed deadline — run at the `tick_seconds = 1.0` cadence
(`ops/lifecycle/launcher.py:559`). A loop cycling every 7.5 ms clears a 1 s cadence by **two orders
of magnitude**. A threaded supervisor would therefore have *observed* the finding-0169 wedge
perfectly well. What it could not have done is *stop* it.

So the sentence is true as a throughput statement and false as a liveness statement, and its
placement — as the second of two reasons, joined by "anyway" — reads as though it independently
disqualifies threads. It does not.

## Why it matters

**The ratified decision is unaffected, and bp-110 proceeded with subprocess on that basis.** The
note's own conclusion sentence names the load-bearing leg: *"the mode-4 power-to-act never
arrives."* Python threads cannot be cancelled — a language fact no measurement can move — and that
is exactly what makes the process boundary **tier 3** (SIGKILL is enforced by the OS, an authority
outside the wedge) where an in-process cancel flag would be tier-5 cooperation with the very code
that stopped cooperating. The note also states V5's job precisely as verifying *"the degree"*, a
secondary quantity. Subprocess stands.

What matters is that the note is a **ratified** document that later work quotes as settled fact,
and this is the kind of sentence that gets quoted one clause short. Two concrete ways it could
mislead:

1. **A future liveness/probe design** could cite §2.5 for "a blocked loop cannot emit" and conclude
   a heartbeat is worthless under CPU load. Measured, a heartbeat on the loop *would* survive a
   pure-CPU thread at 133 Hz. The reason bp-105's channels could not emit is the **synchronous
   in-process call** (§2.2) — the handler owns the thread outright — not GIL contention. Those are
   different mechanisms with different remedies, and conflating them would mis-price a detector.
2. **It states the tier ladder's own foot-gun in miniature.** §2 warns that overclaiming a tier is
   "shoot ourselves in the foot without realizing, one level up". "Starves the loop" claims more
   enforcement strength for the subprocess choice than the measurement supports; the honest claim
   ("threads cannot be cancelled, so mode 4's power-to-act never arrives — tier 3 vs tier 5") is
   *stronger*, not weaker, and does not depend on a number at all.

This is a **precision defect in a ratified note's supporting prose, not in its decision.** Nothing
built on it needs to change.

## Re-entry condition

**Not blocking, and nothing is parked on it** — bp-110 built subprocess as ratified, and Item 1's
acceptance (three measurements in the journal) is closed.

Re-enter at whichever comes first:

- **The next amendment or supersession touching `dn-supervision-and-liveness` §2.5** — amend the
  clause to separate the two reasons: threads are disqualified by **non-cancellability** (the
  decisive, tier-level reason), and *additionally* cost ~2150× loop throughput under a pure-CPU
  wedge while remaining live at ~133 Hz (the measured, secondary reason). Cite this finding for the
  number so V5 stops being an open verification item.
- **NEW NOTE 1's detection-lag instrument work (§2.9)**, which is the first consumer that would
  price a heartbeat under load — it must not inherit the reading that GIL contention silences a
  loop. The relevant silencing mechanism is §2.2's synchronous call, and it is unaffected here.

## Routing

`spec-defect` in a **ratified** design note's prose → **orchestrator**. Not a builder's to edit: a
ratified note is agent-immutable (A8), and correcting it is an amendment/supersession at the design
gate, warrant-linked to this finding. No owner *decision* is needed — the correction is mechanical
and the design outcome does not change — so this is a batching item, not an `owner-questions.md`
entry. The builder resolved the immediate question (does the §10 STOP fire? **No** — the premise it
guards is not the premise the decision rests on) and continued.
