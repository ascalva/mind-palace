---
type: finding
id: finding-0265
status: open
created: 2026-07-27
updated: 2026-07-27
links:
  - docs/brainstorms/owner-intent-audit.md
  - docs/findings/finding-0214.md
ftype: discovery
origin_plan: orchestrator
route: orchestrator
resolution: null
---

# The system's behaviour when its own substrate is degraded is unmeasured: the battery cycle, and sensors when the daemon is down

Two owner instructions, filed together because they are the same subject — **what this system does
when the thing it runs on is degraded** — and two thin findings are worse than one. They are
recovered from `docs/brainstorms/owner-intent-audit.md` (L-6 and L-7), where the search that proved
them absent is recorded.

## What

### (a) The battery-cycle process-management watch — L-6

On `2026-07-26T05:07:33Z` (session `a73e8b34`, row 1074, channel 1):

> *"I'm in laptop mode now, keep an eye on how the OS manages other processes at different phases of
> the battery cycle"*

A baseline was taken in-session; nothing durable holds it. Searched and absent across findings and
brainstorms: `battery cycle`, `laptop mode`.

⚑ **This is a standing sensor request with a proven incident behind it.** On `2026-07-25T03:44:32Z`
(session `9e9dee00`, row 215) the owner reported the machine reaching **~1% battery**, the OS
silently stopping the daemon, and **1,600+ jobs stranded in the queue** — the incident that produced
`bp-100`/`bp-101`/`bp-102`. **That incident is captured; the follow-up instruction to instrument the
thing that caused it is not.** The palace's scheduling model still assumes a plugged-in machine.

### (b) "Sensors may break when the daemon isn't running" — L-7

On `2026-07-25T05:56:44Z` (session `bbc93d80`, queue-row 1034, channel 2):

> *"fyi, keep an eye on things, I'm sure certain sensors may break when the daemon isn't running"*

⚑ **This half is lower-confidence than the rest of this finding, and that is stated deliberately.**
The daemon-down state is discussed in `finding-0214` (self-mod tests read the gitignored overlay)
and its neighbours, but no artifact records this as a **standing watch**, and no sensor-by-sensor
"behaviour when down" inventory exists. The audit flagged it LOST rather than PARTIAL because the
specific claim could not be found anywhere. **If a later sweep finds it absorbed into an existing
artifact, downgrade this half rather than build against it.**

## Why it matters

The supervisor has an **unmeasured environmental input**. Power state is not a variable anywhere in
the scheduling model, yet it has already, once, silently halted the daemon and stranded a
four-figure job backlog. The incident produced plans about *recovering* from the stranding; nothing
produced a sensor for the *cause*.

⚑ The two halves compound. If sensors themselves misbehave while the daemon is down, then the very
window in which the system most needs to know what happened is the window in which its instruments
are least trustworthy — and the battery incident is exactly such a window. A post-hoc reconstruction
of a low-power stall would be built on readings taken while the substrate was degraded.

This is corroborated live and independently of the transcript: the ingest lane is **wedged behind a
stranded job** as of 2026-07-25, and the chat store's coverage stops at `2026-07-25T03:44Z` — within
a minute of the battery incident's own timestamp. The degraded-substrate case is not hypothetical; a
store this finding would want to query is currently missing two days because of one.

## Re-entry condition

Reopens when the Ops track next takes a scheduling or supervisor unit — `bp-111` is the named safe
next ops build — at which point (a) should be considered for inclusion as a power-state sensor
alongside the existing health work. Independently, (b) reopens if any sweep of sub-agent or worktree
transcripts (declared unswept) locates the standing-watch claim in an existing artifact, in which
case this half is downgraded rather than built. Neither half blocks anything today.

## Routing

`discovery` → the orchestrator. It names an unmeasured environmental input to the supervisor and
belongs with the Ops track. It is not a builder-resolvable item: no active plan owns the scheduling
model's inputs, and adding one is a design decision.
