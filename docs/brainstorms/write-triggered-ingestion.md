# write-triggered-ingestion

## 2026-07-27T17:12:00Z

```capsule
topic: write-triggered-ingestion
date: 2026-07-27

seed (owner, verbatim): |
  "can a file write have a code hook that pings a refresh endpoint? or trigger ingestion?
  ingested the second the write happens, not even claude can intercept the message, are there OS
  triggers/hooks on file writes?"
```

## THE MECHANISM EXISTS — three tiers on this machine

`[INFERENCE — verify each before building]`

| tier | what | character |
|---|---|---|
| **FSEvents** | macOS kernel-level filesystem event stream; `fswatch` and Python `watchdog` both ride it | coalesced, path-granular, cheap |
| **launchd `WatchPaths`** | a job fires when a path changes; already the supervisor's world | no daemon of its own to babysit |
| **git hooks** | `post-commit` / `post-receive` — commit-granular, not write-granular | already used here; the code sensor rides commits today |

⇒ The capability is not in question. What it collides with is.

## ⚑⚑ IT CONTRADICTS RATIFIED DESIGN — this is the finding, not a footnote

`dn-chat-sensor` CS-1 states plainly: **"Sensing runs at session boundaries (batch), never live."**
That is ratified text, and live write-triggered ingestion is its direct negation.

⇒ **This idea cannot be built without amending a ratified note** (owner-hand, A8). Before that,
the reason for the batch rule has to be recovered — it was decided, and a decision that predates
this idea deserves to be read before being overturned. `[INFERENCE]` Plausible reasons, none
verified: coalescing (a build touches hundreds of files), transactional consistency (mid-write
files are half-written), and the single-writer queue.

## ⚑ THE COST IS ALREADY VISIBLE ON THIS MACHINE

The ingest lane is **wedged** right now — one stranded `code_sync` since 2026-07-25 with ~1,766 jobs
queued behind it, on a **single-writer** queue. A live trigger would have been enqueueing into that
wedge for two days.

⇒ **Write-triggered ingestion multiplies event volume against a lane that has already demonstrated
it can stall.** Any design must answer: coalescing window, backpressure, and what happens when the
consumer is down. A trigger with no backpressure is a denial-of-service the system performs on
itself.

## ⚑ THE STRONGEST PART OF THE IDEA IS THE PART HE SAID IN PASSING

> *"not even claude can intercept the message"*

That is not a performance argument — it is an **integrity** argument, and it is the most interesting
thing here. An OS-level trigger observes the write **before any agent can revise, reframe, or
retract it.** The observation is taken out of the observed party's hands.

⇒ This is tamper-evidence, and it lands directly on the week's theme: the corpus currently learns
what happened through *commit bodies an agent authors*, which is the laundering surface
([[the-unchecked-claim]], [[context-load-as-a-feedback-loop]] L5). A kernel-level witness cannot be
edited by the thing it witnesses.

⚑ **And it is the missing half of the owner's own R2 ruling** ([[commit-economy-and-the-succession-path]]):
*decouple the sensor from commit bodies; have it read artifacts and edit events directly.* An FSEvents
witness **is** an edit-event source. The two ideas are one idea, arrived at from different directions
five hours apart.

## THE SHAPE THAT MIGHT SATISFY BOTH

`[INFERENCE — a sketch, not a design]` Split *witnessing* from *ingesting*:

- **The witness is live.** A kernel-level watcher appends `(path, mtime, digest, observed_at)` to an
  append-only event log. Cheap, no model, no embedding, no queue — and un-forgeable by an agent.
- **Ingestion stays batched.** The existing sensor drains the event log at session boundaries, as
  CS-1 requires.

⇒ CS-1 survives untouched (ingestion is still batch), the tamper-evidence property is gained, the
edit-event source R2 wants exists, and the wedge risk is bounded because the live path never
enqueues work. The amendment needed, if any, is smaller than "sense live."

## OPEN

- What does the witness do about **its own** writes — the palace writing to `data/` would witness
  itself. A loop ([[context-load-as-a-feedback-loop]] L5 wearing a new hat). Exclusion set required,
  and it must be structural rather than a denylist that rots.
- Does the witness cover the **vault**? It must not — NN-2, network and private data never share a
  component; a watcher is a component.
- `[INFERENCE]` Degenerate input ([[the-false-success-rule]]): a witness whose exclusion set matches
  everything logs nothing and passes every "no crash" check. The acceptance must assert a known
  write **appears**.
