---
type: journal
plan: bp-117
started: null
updated: 2026-07-25
---

# Journal — bp-117 (P3: the equivalence gate)

Minted 2026-07-25 (session-48) by `/graduate`, decomposing both ratified ops notes
(`dn-supervision-and-liveness` and `dn-local-model-runtime`) in one context. **Not started.**

## Pre-build notes for whoever picks this up

⚑ **This is a CUTOVER GATE, and it is the owner's ruling: "first we need to make sure the same
model produces the same results as our baseline" (2026-07-25).** bp-118 and bp-119 depend on its
RESULT being green, not merely on it existing.

- ⚑ **`eval/golden.py` and `eval/golden/**` are FOUNDATION DENYLIST. Read and run, never write.**
  Non-negotiable #9 makes the frozen golden set a fixed point — which is precisely WHY it is the
  right cross-runtime baseline (stable by construction). Item 3 asserts it is byte-unchanged after
  a full run. If making the gate pass would require touching it, STOP immediately (§10).
- ⚑ **Gate on the per-text MINIMUM, not the mean.** §2.5 says "worst case reported, not mean"
  twice. A mean of 0.999999 with one text at 0.998 FAILS. Item 2's falsifier tests exactly this.
- ⚑ **Item 1 before everything.** If within-runtime determinism is not 1.000000, no cross-runtime
  number means anything. §2.1 F measured 1.000000 everywhere.
- **Graduation already answered the note's open stamping question** (§3 Q7): `Attestor.emit`
  (`core/attestation/attestor.py:36-45`) has a FIXED keyword set with no free-form field, so
  backend+build provenance needs a schema change. The parked decision resolves to "a V".
- **The chat half is written but cannot be RUN** (§3 Q6, V-B). Say so in the report.

## Owed at seal (orchestrator, not the builder)

Findings referenced in §4 Reconciliation are cross-referenced, never edited — a builder may not
edit an existing finding. Record closure evidence here for the orchestrator to apply at seal.
