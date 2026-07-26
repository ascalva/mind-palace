---
type: finding
status: open
id: finding-0202
created: 2026-07-25
updated: 2026-07-25
links:
  - docs/build-plans/bp-108/plan.md
  - CLAUDE.md
  - docs/templates/build-plan.md
ftype: discovery
origin_plan: bp-108
route: builder
resolution: >
  Resolved for bp-108 by clearing `__pycache__` between every mutation and re-running the
  drill (results changed; the first run's verdict was false). Unresolved GENERALLY — every
  plan in this repo carries "plant the mutation and record that it reddens" as a named
  falsifier, and nothing in the workflow tells a builder that the drill can silently lie.
---

# A mutation drill can silently run the PREVIOUS bytecode — the falsifier says "green" and
# the builder believes it

## What
Named falsifiers in this workflow are routinely discharged by planting a mutation, running
the suite, and recording that it reddens (bp-108 §7 Items 2 and 3 both demand exactly this).
That procedure has a silent failure mode.

CPython invalidates a cached `.pyc` on **(source mtime, source size)** — not on content
hash, by default. A mutation that changes neither is therefore *ignored*: the interpreter
loads the stale bytecode and the drill measures the wrong program. Two of the three
mutations used on `ops/lifecycle/lock.py` are exactly that shape:

| original | mutation | same size? |
|---|---|---|
| `fcntl.flock(fd, fcntl.LOCK_EX \| fcntl.LOCK_NB)` | `fcntl.lockf(fd, ...)` | yes — `flock`/`lockf` are both 5 chars |
| `fcntl.flock(fd, fcntl.LOCK_EX \| fcntl.LOCK_NB)` | `... fcntl.LOCK_SH ...` | yes — `LOCK_EX`/`LOCK_SH` are both 7 chars |

A scripted drill writes the mutation, runs pytest, and restores the original within the same
mtime *second*, so the restore is invisible too. Observed here: after the harness restored a
byte-identical original, the suite reported `1 failed, 14 passed` and kept doing so on
re-run. The source on disk was correct — `inspect.getsource` confirmed it — while the loaded
module was still the mutant. It was only caught by spying on `fcntl.flock` and noticing it
was **never called at all**:

```
a.acquire():
  open(PosixPath('.../supervisor.lock'), flags=514) -> fd 3
b.acquire():
  open(PosixPath('.../supervisor.lock'), flags=514) -> fd 4
 -> GRANT                      # and no flock(...) line anywhere
```

Adding `shutil.rmtree` of every non-`.venv` `__pycache__` before each run fixed it, and the
drill's verdict changed.

## Why it matters
The failure direction is **toward false confidence**, in the one procedure whose entire job
is to prevent false confidence:

* **A mutation that "fails to red" reads as a weak test.** A builder who plants a deletion,
  sees green, and concludes "my test does not pin this" may go and write a *worse* test, or
  file a spurious spec-defect — when in fact the mutation never ran.
* **Worse, and the reason this is filed:** the same mechanism can make a drill report the
  *previous* mutation's result. In the first run here, M3's row was produced with M2 possibly
  resident. The numbers differed so M3 was genuine, but nothing in the procedure would have
  revealed it if they had matched — and "M2 and M3 red the same tests" is precisely the
  result a builder would find unremarkable.
* This is the finding-0187 shape one level up. There, an untested switch was a claim rather
  than a mechanism. Here, an *un-run* mutation makes a test look like a mechanism when the
  drill proved nothing.

The cheap, complete guard is one line at the top of any mutation loop — drop `__pycache__`,
or run with `PYTHONDONTWRITEBYTECODE=1`. The point of filing it is that a builder can only
apply a guard they know about, and this one is invisible until it bites.

## Re-entry condition
Nothing is parked; bp-108 proceeded with the guard in place. Re-entry is for the
orchestrator: decide whether the **checkpoint/build-plan skill** should carry "clear
`__pycache__` (or set `PYTHONDONTWRITEBYTECODE=1`) before every mutation run" as part of the
standard falsifier-drill procedure. A one-line addition to the skill would retire the hazard
repo-wide; without it, the next builder rediscovers it or — much more likely — does not.

## Routing
`discovery`, route `builder` — no design question and no owner input needed; the technical
fact is settled and applied. Surfaced to the orchestrator only for the process half (should
the drill procedure carry the guard), which is a skill edit outside this builder's scope.
