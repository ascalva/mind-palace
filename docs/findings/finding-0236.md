---
type: finding
id: finding-0236
status: open
created: 2026-07-27
updated: 2026-07-27
links:
  - docs/design-notes/role-state-and-scoped-handoff.md
  - docs/build-plans/bp-124/plan.md
  - docs/build-plans/bp-126/plan.md
  - docs/build-plans/bp-127/plan.md
  - scripts/handoff.py
  - ops/lifecycle/snapshot.py
ftype: spec-defect
origin_plan: bp-124
route: orchestrator
resolution: null
---

# The queue pane and the idempotence pin cannot both live in the committed rendering — and the age
# display is the same defect wearing a different hat

## What

`dn-role-state-and-scoped-handoff` §2.9 pins two things about the handoff rendering that are in
direct tension the moment the daemon is running:

1. **The idempotence pin:** *"the rendering is a pure function of the artifact tree **excluding
   itself**, and embeds no HEAD sha and no generation timestamp."*
2. **The inputs:** *"the artifact tree …, the readings log, and — when present — a read-only open
   of `data/queue.sqlite`"*, rendered per §2.6 as *"queue depth, RUNNING rows, lease status"*.

`data/queue.sqlite` **is not the artifact tree.** It is gitignored runtime state that a live
supervisor mutates continuously, and it is absent from every worktree by construction — the note
says so itself (§2.6 failure 1). Three consequences, none of which the note reconciles:

- **The pin breaks under a live daemon.** Two regenerations over a *completely unchanged tree*
  differ whenever a job has been enqueued, claimed, or finished between them. That is bp-124
  Item 2's falsifier firing for a reason that has nothing to do with the tree.
- **Clause (e′) would re-arm forever.** bp-126's check 1 blocks a close unless regenerating the
  rendering is a byte-identical no-op. With queue counts in the file, the *daemon* re-arms the
  gate, not the work — the exact circularity §2.10 exists to remove, moved from `mtime` to
  content. The mechanism would be new; the eleven-firings experience would not be.
- **F1a and F1c would contradict each other across checkouts.** A rendering committed from `main`
  (queue present) can never byte-compare equal when regenerated in a worktree (queue absent), so
  the cannot-drift check and the availability check cannot both pass in the same tree.

**⚑ The same defect, second instance: the age display.** §2.5 and §6 pin the MEASURED pane as
rendering *"the latest reading per command **with its age**"* — `suite: … (18h ago)`. An age is a
clock read. A committed artifact carrying one is stale one minute after it is written and is never
its own fixed point, which is precisely what the pin forbids in the same paragraph.

## Why it matters

The pin is the family's keystone: bp-126's clause (e′) and bp-127's F1a are *built on it*. Shipping
a rendering that is idempotent in a test fixture and non-idempotent in the live main checkout would
have satisfied bp-124's written acceptance while making bp-126 unbuildable — a green build that
destroys the next plan. It is also the "structural enforcement" failure class: the property would
have been asserted by a passing test and false in the only environment that matters.

## How bp-124 resolved it (so the resolution is reviewable, not implicit)

`scripts/handoff.py` renders in two modes off one computation — `_View.live`:

| mode | invoked by | queue pane | reading freshness |
|---|---|---|---|
| **tree-pure** | `--write`, `--check`, `--json` | a pointer line naming the live command | the reading's own **timestamp** (data, carried by `readings.md`) |
| **live** | a bare `--role/--track/--plan` render to stdout | the real probe: depth · RUNNING rows · lease, or `queue: unavailable in this checkout` | the computed **age** (`18h ago`) |

The committed artifact is therefore checkout-invariant and clock-free, and every mechanical
acceptance criterion in bp-124 §7 Items 2/3/5 is still discharged — Item 3's `queue: unavailable in
this checkout` and its live rows both land on the stdout path, which is exactly the path F1c
exercises ("the generator must exit 0, rendering `queue: unavailable`").

This is a **choice made by the builder against a gap in the ratified text**, not a reading of it.
It is recorded here so it is reviewed rather than inherited.

## The ask (what the next plans must know)

- **bp-126 (clause (e′)):** compare `--check` against the tree-pure rendering — i.e. shell out to
  `uv run scripts/handoff.py --role orchestrator --check`, which already means that. **Do not**
  re-implement the compare over a live render, and do not "fix" the missing queue counts in the
  committed file by moving the probe back into `--write`.
- **bp-127 (F1a/F1c):** F1a is the tree-pure compare; F1c must assert against the **live** stdout
  render, since that is where the availability line lives.
- **The owner, if the note's text should say this:** it is a ratified note and therefore
  agent-immutable (A8), so correcting §2.9/§2.5 in place is an owner hand-act — the same sitting as
  `finding-0233` (amendment A10) and `finding-0235`. The alternative is to leave the text as-is and
  let this finding carry the correction, which is the default taken.

## Re-entry condition

Not blocking; bp-124 shipped the resolution above. **Re-entry:** at bp-126's build, if clause (e′)
is observed to re-arm after a regen commit, this finding is the first place to look — the cause
will be a volatile value that crept back into the tree-pure rendering. Also re-enter if the owner
wants the live queue figures durably recorded: the right home is a MEASURED row in
`docs/roles/orchestrator/readings.md` (a probe result with its timestamp attached), never the
DERIVED pane.

## Routing

`spec-defect` against a **ratified** design note → **orchestrator**. A builder cannot amend the
note, and the correction is a design statement, not a code fix.
