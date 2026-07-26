---
type: finding
id: finding-0220
status: routed
created: 2026-07-26
updated: 2026-07-26
links:
  - docs/build-plans/bp-107/plan.md                    # §6 §7-Item-2 §10 — the three phrasings
  - core/models/loader.py                              # where each ruling is implemented + commented
  - tests/unit/test_loader_reconcile.py                # the phases, as tests
  - tests/property/test_loader_fsm.py                  # the invariant a weakening would hide
  - docs/findings/finding-0199.md                      # the warrant bp-107 closes
  - docs/findings/finding-0174.md                      # the sibling this makes visible, not fixed
  - docs/design-notes/dn-local-model-runtime.md         # §2.3 owns the durable replacement (bp-116)
  - CLAUDE.md                                          # non-negotiable 8 — respect the memory ceiling
ftype: spec-fidelity
origin_plan: bp-107
route: builder
resolution: resolved in-build — all three resolved toward MORE enforcement, implemented + commented at the cited lines; recorded so the readings are auditable and bp-116 inherits them, not re-derived
---

# bp-107's ceiling rules are stated three times, and two of the phrasings would have weakened the guard

## What

Building bp-107 required resolving three places where the plan's own phrasings do not agree. All
three were resolved toward the *more enforcing* reading, per the orchestrator's spawn-time
instruction that a change making the ceiling **less** able to refuse breaching work is a
stop-and-raise. Each is recorded here because the loser of each choice is invisible: nothing in the
suite would have caught the weaker reading.

**1. "The pinned model is never refused" — by the fail-closed rule, or by the arithmetic too?**

- §6 states the rule with a single antecedent: *"unknown names present ⇒ refuse NON-PINNED loads
  ⇒ ALWAYS allow the PINNED model."* Both arrows hang off "unknown names present".
- §10's first stop condition is likewise scoped: *"**The fail-closed rule** would refuse the PINNED
  model … ⇒ STOP."*
- But §7 Item 2's invariant list drops the scope: *"the **pinned model is never refused**."*

Read as a blanket exemption, the pinned model would bypass `_check_ceiling` entirely. **Resolved:
scoped.** `_refuse_uncostable` never refuses the pinned model; the arithmetic ceiling continues to
apply to every model, pinned included, exactly as before bp-107 (`core/models/loader.py`,
`_refuse_uncostable`'s second ⚑). The blanket reading was rejected because (a) it makes the ceiling
strictly less able to refuse, against non-negotiable #8, and (b) the weakening would be
**undetectable**: `tests/property/test_loader_fsm.py` enumerates every reachable state under budgets
24.0 and 5.0, and in neither is a pinned load ever in a breaching position — so the exhaustive
property test would have stayed green over a hole. Note this behaviour is *pre-existing*, not new:
today's loader already raises on `ensure_pinned()` from an in-process `{stretch}` state
(23.0 + 2.7 = 25.7 > 24.0).

**2. Item 2's acceptance wording — "phase (ii) now RAISES" — is not achievable as literally written,
and the falsifier's substance does not require it.**

§7 Item 2 asks that *"the **23.0 ≤ 24.0 pass against a true 25.7 GB** case now RAISES
`MemoryCeilingError`"*. Under the design §6 pins, it does not raise — **it stops being a breach.**
The 25.7 GB arose because the eviction loop iterated an empty `_resident` and therefore never told
Ollama to drop the really-resident pinned model, so the guard's prospective `{stretch} = 23.0` was a
prediction nothing made true. Once `_resident` is measured, the eviction loop targets the real 2b and
9b, `unload` is actually issued, and the post-state really is 23.0 ≤ 24.0. Verified: `fake.unloads ==
{2b, 9b}`, `fake.held == [stretch]`.

Making it *raise* instead would require refusing to credit an eviction the two-slot algebra performs
— i.e. changing `_prospective`, which is simultaneously the FSM test's own refusal oracle and the
thing `test_stretch_evicts_pinned_and_runs_solo` asserts. That is §10's third stop condition (a
carried test made green only by weakening it), so the literal reading is self-defeating.

**Resolved: implement the substance, and prove it two ways.** The falsifier — *"the measured breach
still passes the guard … if `_check_ceiling` still admits 25.7 GB against a 24.0 budget, nothing
shipped"* — is discharged by (ii-a) the 25.7 GB state being unreachable, and (ii-b) a case where the
other consumer genuinely *cannot* be evicted by any two-slot rule, which does raise: with the pinned
model and the embedder resident, `ensure_tier("synthesis")` now refuses at 29.7 > 24.0 where the old
guard admitted at 17.0. Both are in `tests/unit/test_loader_reconcile.py`. Measured against the old
loader, every phase fails as intended — the tests are discriminating, not merely passing.

**3. Does the measured non-registry consumer count against `max_resident_models`?**

The plan does not say. Counting the embedder as a third resident model would refuse **every** worker
load while it is warm — a far larger behaviour change than the plan sanctions, and a
*reinterpretation* of a knob that `dn-local-model-runtime` §2.3 explicitly **replaces** rather than
reinterprets (bp-107 §9's first non-goal forbids pre-empting that). **Resolved: charged in the GB
dimension only**; `max_resident_models` keeps counting registry slots exactly as before
(`_check_ceiling`'s docstring). This is still strictly more enforcing than the old code, which
charged the embedder in neither dimension.

## Why it matters

Each losing reading fails silently and permanently. #8 is inviolable-kernel, and the whole point of
finding-0199 was that a guard can *read* as enforcing while checking the wrong world — so a bp-107
that shipped a blanket pinned exemption, or that reshaped `_prospective` to force a raise, would have
reproduced the finding's own defect while claiming to close it. Recording the rulings also means
bp-116 inherits them: §2.3 replaces this loader, and its author should know that the pinned model's
exemption was deliberately scoped and that `max_resident_models` was deliberately left alone.

## Re-entry condition

Nothing is parked; bp-107 completed all three items. Re-entry is at **bp-116**, which replaces
`TwoSlotLoader` with process-existence residency: ruling 3 dissolves there (the knob is replaced by
per-process budgets), and rulings 1 and 2 must be *restated* in the new shape — a process manager
that spawns the router unconditionally would re-introduce exactly the blanket exemption rejected
here. If the owner's intent was in fact the blanket reading, this finding is the place to say so, and
`_refuse_uncostable` is the one function to change.

## Routing

`spec-fidelity` → **builder**: resolved in-build, annotated here and at each cited code site, and
carried into `docs/build-plans/bp-107/journal.md`. No owner input is required to proceed — but
ruling 1 is a genuine judgement about an inviolable-kernel item, so it is flagged for the seal rather
than buried: if the orchestrator disagrees, it is a one-function change, not a redesign.
