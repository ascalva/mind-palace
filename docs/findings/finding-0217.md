---
type: finding
id: finding-0217
status: open
created: 2026-07-26
updated: 2026-07-26
links:
  - core/dreaming/charter.py                          # DreamCharter.grant — Σ fully typed, in memory only
  - core/dreaming/adjudicator.py                      # run_dream_rnd — the persisted belief surface; no Σ, no cut, no attestation_id
  - core/dreaming/dreamer.py                          # the attested path — input_hashes = cited evidence, not the visibility set
  - core/attestation/record.py                        # input_hashes/output_hashes — extensional, support-set only
  - core/kernel/mirror.py                             # MirrorView.SCOPE — the class-constant Σ the live path leans on
  - docs/design-notes/synchronic-diachronic-dreamer.md  # §2.2-4 — "every reading pins its gauge fingerprint beside its (σ, t, cut) tuple"
  - docs/brainstorms/dreamer-and-graph-direction.md   # the open question this answers ("check before designing storage")
  - docs/design-notes/scored-beliefs-and-earned-entitlement.md  # the draft note this grounds
ftype: discovery
origin_plan: orchestrator          # 2026-07-26 dispatched fable design pass (scored-beliefs note)
route: orchestrator
resolution: null
---

# A belief's Σ is not recoverable after the fact: the charter is never persisted, and every persisted record carries the support set, not the visibility set

## What

The `dreamer-and-graph-direction` capsule (2026-07-26) asked: does the existing adjudicator
already record enough to reconstruct a belief's Σ after the fact? If yes, the belief ledger is a
read over existing state; if no, it is new bookkeeping. **Checked in code this session: the answer
is NO, on every persistence surface, and the gap is exactly the distinction the ledger exists to
make.**

1. **The `DreamCharter` types Σ completely and persists nothing.** `DreamCharter.grant` is a full
   `Scope` — Σ strata, E, T-window, authority — plus instruments, budget, gauge
   (`core/dreaming/charter.py:155-222`). It is a frozen in-memory record. No charter store exists;
   grep of `core/`, `ops/`, `scheduler/` finds no code path that writes a charter, its digest, or
   its grant anywhere durable.
2. **The persisted belief surface records the support set only.** `run_dream_rnd`
   (`core/dreaming/adjudicator.py:138-167`) writes `DREAM_LOG` artifacts whose `data` carries
   confidence, grounding, agreement, methods, depth, and `evidence` (cited authored digests) —
   **no Σ, no cut, no gauge, no generation, and no `attestation_id`** (the call to `derived.add`
   passes none; `run_dream_rnd` does not even accept an attestor). The `DerivedStore` schema
   (`core/stores/derived.py:49-60`) has nowhere to put a grant except the free-form `data` JSON,
   and nothing puts it there.
3. **Attestations are extensional, not intensional.** The attested path
   (`core/dreaming/dreamer.py:139-149, 221-228`) emits `input_hashes = leaf_digests` /
   `entry.evidence` — the digests the claim **cited**, never the row set the view **held**, and
   never the grant that defined what was holdable. `Attestation` (`core/attestation/record.py`)
   has fields for input/output hashes and parent attestations only; there is no scope field.
4. **The one live path's Σ is recoverable only by convention.** Every live dream today reads a
   `MirrorView`, whose Σ is a class constant (`MirrorView.SCOPE`, `core/kernel/mirror.py:76-82`:
   Σ = {mirror_authored}, point window at ANCHOR). So Σ *can* be reconstructed for existing dreams
   — by asserting "the code was thus at the time," which is reconstruction by convention, not by
   record. The convention breaks at exactly the moment it starts mattering: the first
   charter-parameterized dispatch with owner-declared strata (the entire point of per-grant
   dreaming, dn-cross-strata-dreamer) makes Σ vary per dispatch with no record of which value
   any belief was formed under.

The support-set/visibility-set gap is not a bookkeeping nicety. "Wrong given its Σ" versus "wrong
because Σ was too narrow" is decided by what the dreamer **could see and did not cite** — the
complement of the evidence inside the granted view. The evidence list, which is all any surface
persists, cannot answer it by construction.

Related, narrower observation: `dn-synchronic-diachronic-dreamer` §2.2-4 (ratified) states "every
reading pins its gauge fingerprint beside its `(σ, t, cut)` tuple." The charter holds the gauge;
no persisted artifact or reading pins the tuple (`core/dreaming/conditioning.py` included). Read
honestly, §2.2-4 governs instrument-reading evidence discipline whose consuming plans (bp-080/082
outputs) are in-memory objects, so this is a seam the ledger must close rather than a violated
invariant — but a future plan should not cite §2.2-4 as if the pinning already lands on disk.

## Why it matters

The scored-beliefs design (the draft note this finding grounds) requires the belief record to
carry Σ, the cut, and the occasion — the brainstorm's own constraint is that a ledger without Σ
cannot test "the more you know, the better the view gets." This finding establishes that **the
ledger cannot be built as a read over existing state**: it needs new bookkeeping at emission time
(persist the charter — or its digest plus the grant's coordinates — beside every belief), and it
needs it from the first scored belief, because Σ cannot be back-filled (any retroactive Σ is the
class-constant convention wearing a record's clothes). This also means pre-ledger dreams are
unscorable without smoothing over exactly the distinction the instrument exists to draw — the
draft note makes "no retroactive scoring" a non-goal on this warrant.

## Re-entry condition

The `scored-beliefs-and-earned-entitlement` note ratifies (adopting charter-persistence-at-emission
as the belief record's spine, §2.1 there), or the owner rules a different storage answer at triage.
If the note is rejected, this finding survives it: any future consumer of "which Σ was this dream
formed under" — harness per-grant A/B included — hits the same absence and should land here rather
than rediscover it.

## Routing

`discovery` → orchestrator (design). No builder action: nothing here is a bug in built behavior —
every module honors its own stated contract; the gap is between what the *next* design needs and
what any existing surface records. Batches to the owner with the note's ratification review.
