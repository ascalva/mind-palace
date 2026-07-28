# bp-149 — journal

## Pre-build notes for whoever picks this up

- ⚑⚑ **THIS PLAN IS BLOCKED AND NOT STARTABLE until TWO owner amendments land:**
  `docs/design-notes/agent-workflow.md` (§6 hook contracts, §9 note-taking, §2/§10 gate
  wording) and `docs/design-notes/dn-autopilot-and-delegated-blessing.md` (§2.3, the two
  §2.5.3 collisions). Both are **owner hand edits to ratified notes** — no agent performs
  them. Item 44 is the verification, and if either is missing: STOP, report, retire nothing,
  and do not "prepare" the removals in a branch.

- ⚑ **Every item REDUCES enforcement.** The only thing between this plan and a silent loss of
  a bright line is bp-147's clause table in `ops/registry/schema.md` and bp-146's parity
  harness. Believe them only where they say `proved`.

- ⚑ **Removal order is least-protective-first** — inverted from the usual blast-radius rule
  because reduction, not addition, is the act: staleness-nudge → session-brief → gate-guard →
  scope-guard → journal-gate.

- ⚑ **`compaction-marker` stays.** One registration remains at the end (`PreCompact`).

- ⚑ **The deskcheck arm of `gate-guard` is NOT retired.** §2.6's table names no deskcheck
  disposition and §2.5.2 keeps the verdict owner-by-hand and unsigned. If retiring gate-guard
  would drop it as a side effect — STOP.

- ⚑ **The denylist must never be enforced zero times.** Item 48 demonstrates `land()`
  enforcing it BEFORE `scope-guard` is unregistered, and again after.

- **Two commits per hook:** registration removal (the behaviour change), then the dead
  `_lib.py` clause function after a grep proves no consumer remains. `_lib.py` itself
  survives — `scripts/board.py`, `scripts/handoff.py`, and `ops/registry/**` import its
  parser and matcher.

- **First act of Item 44:** record what `OUROBOROS_HOOKS_OFF` is currently set to and what
  that implies about which hooks are actually live. A retirement measured against hooks that
  were already off proves nothing.

- **Every removal commit must cite four things** (invariant 8): the hook, the §2.6 row, the
  parity test node id, and the `schema.md` row marked `proved`.

- **Post-removal demonstrations go in this journal** with the command and its output — not a
  claim. Especially for each journal-gate clause (a, b, b2, c, d, e′, f).

## Entries

_(none yet — this plan is `proposed` AND blocked on two owner amendments; the first entry is
written by the build session, which may not start until Item 44's preconditions hold)_
