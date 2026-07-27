---
type: finding
id: finding-0246
status: open
created: 2026-07-27
updated: 2026-07-27
links:
  - docs/design-notes/role-state-and-scoped-handoff.md   # §2.10 check 2 — the session-start key
  - docs/design-notes/session-handoff-gate.md            # §2.2-2.3 — the superseded clause (e)
  - .claude/hooks/session-brief.sh                       # the baseline write
  - .claude/hooks/_lib.py                                # clauses (c) and (e′), its two consumers
  - .claude/skills/delegate/SKILL.md                     # the mandated pre-flight budget probe
  - docs/build-plans/bp-126/plan.md
ftype: spec-defect
origin_plan: bp-126
route: orchestrator
resolution: null
---

# A nested `claude -p` clobbers `session-baseline` — so the mandated budget probe silently disarms
# the session-handoff gate, and clause (e′)'s new mtime key makes the same event spuriously arm it

## What

`.claude/state/session-baseline` is written by `session-brief.sh` at **every** SessionStart. A
**nested, one-shot `claude -p …`** run from inside a session is a SessionStart: the hook fires in
the same worktree and overwrites that file. Both of its fields move, and each breaks a different
consumer.

**Found by dogfooding, not by reading — the gate blocked my own close, and then a budget probe made
the block vanish without satisfying it.** Verified twice by direct experiment:

```
before:  mtime 02:04:56   content aaff6ef1        # the parent session's real start
$ claude -p "reply with the single word: ok"      # a nested one-shot; rc 0
after:   mtime 02:09:03   content 69f8c1fb        # == current HEAD
```

Two independent failures follow.

**1. The commits-this-session guard is destroyed → the gate goes SILENT.** The trigger for both (e)
and (e′) is `head_sha != baseline`. The nested run rewrites the *content* to **current HEAD**, so
the parent session's record of where it started is gone and `head_sha == baseline`. The gate then
reports `ALLOW` — not because the session's handoff state is fresh, but because the gate can no
longer see that the session ever committed. Observed live: with the seat journal provably stale
(02:02:49 against a 02:09:03 baseline), `stop-audit` printed `BLOCK: (e′) …` before the probe and
`ALLOW` after it, with **nothing about the seat's state having changed in between**.

**2. The session-start key is moved forward → check 2 spuriously ARMS.** `dn-role-state-and-scoped-handoff`
§2.10 check 2 blocks unless `mtime(seat journal) >= mtime(session-baseline)`. The nested run pushes
that mtime to *now*, so **every narrative entry written before the probe is retroactively "from a
previous session."** A session that had already discharged check 2 correctly is asked to write a
second entry, for no work.

The two failures are ordered by the probe's timing relative to the session's commits, and failure 1
masks failure 2 whenever HEAD has not moved since the probe. That is why it is easy to miss.

## Why it matters

**This is not a hypothetical invocation — it is a mandated one.** The delegation-budget rule
requires a self-serve probe, `claude -p "/usage"`, **before every spawn** and again at seal
(`delegate/SKILL.md`, verified live in `finding-0242`). Any session that follows that rule disarms
its own handoff gate. The more disciplined the session, the more reliably the gate is defeated.

**Failure 1 is pre-existing and affects clause (e) identically** — the `head_sha != baseline`
trigger is unchanged from A9 — so this is not a regression introduced by `bp-126`. It matters more
*now* only because the whole `dn-role-state-and-scoped-handoff` family rests on this gate being the
thing that keeps the seat honest. A gate that any sub-invocation can silence is a weaker guarantee
than the note assumes, and the note assumes it in writing (§2.10's "by construction" claim is about
*dischargeability*, and says nothing about the trigger's integrity).

**Failure 2 is new**, introduced by check 2's dependence on the baseline's **mtime**. Under (e) the
baseline's mtime was never read — only its content — so a nested run could silence the gate but
never spuriously fire it. `bp-126` adds the mtime as a second consumer, and with it a new cry-wolf
path: exactly the failure mode §2.10.3 rules out for MEASURED, arriving through NARRATIVE instead.

There is a third, quieter consequence: `session-baseline` is also clause (c)'s documented sibling
and the SessionStart brief's narration anchor. Anything that reads it inherits the same fragility.

## Why `bp-126` did not fix it

`session-brief.sh` **is** in this plan's `write_scope`, so the fix was reachable — and was
deliberately not taken. Item 13's stated invariant is that *"the baseline write at `:63-65` is
**untouched** (clause (e′) check 2 keys on it, and clause (c)'s consumer chain depends on it)"*.
Changing when the baseline is written changes the meaning of a file with two other consumers, in
the same diff that already replaces a Stop clause and deletes an artifact — precisely the
"mechanical move and trust-boundary change in one plan" shape that is supposed to be split. The
obvious one-line guards are also each wrong in a different direction:

- **"Write only if the file does not exist"** — the baseline would then be pinned at the first
  session ever, and every later session would see `head_sha != baseline` forever.
- **"Write only if HEAD differs from the recorded value"** — fixes failure 2, and makes failure 1
  *worse*: a nested probe taken *after* the parent commits still overwrites the guard, silently.
- **"Skip the write when nested"** — there is no reliable in-band signal for "I am a nested
  invocation" available to the hook today. This is the crux, and it is a design question.

## Re-entry condition

**Re-enter before `bp-127` builds the F2 drill harness** — F2 spawns agents and will invoke the
generator and the gate from inside a session, so it will meet this immediately, and a drill that
silently disarms the gate it is validating would produce a green result that means nothing.

Two candidate directions, both needing a ruling rather than a patch:

- **(a) Make the baseline session-scoped rather than worktree-scoped** — key the file (or a field
  inside it) on the session id the harness already knows, so a nested invocation writes its own
  and never touches its parent's. This fixes both failures at the source and is the only one that
  restores the trigger's integrity.
- **(b) Split the two signals** — keep `session-baseline` as the content guard and give check 2 its
  own session-start marker written once per top-level session. Fixes failure 2 only; failure 1
  survives, and the note should then say plainly that the trigger is defeasible.

Whichever is taken, **the honest interim statement belongs in the record now**: the session-handoff
gate is defeated by any nested `claude` invocation, and always has been.

## Routing

`spec-defect` → **orchestrator**. It needs a decision the builder should not make alone: it changes
the meaning of a file with three consumers, it touches an owner-mandated workflow rule (the budget
probe), and the general lesson — *a per-session marker written by a hook that fires on every
invocation is not per-session* — belongs in the note rather than in one plan's journal. Not a
blocker for `bp-126`: the cutover's own acceptance is unaffected, and the defect predates it in the
half that matters most.
