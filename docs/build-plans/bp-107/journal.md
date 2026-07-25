---
type: journal
plan: bp-107
started: null
updated: 2026-07-25
---

# Journal — bp-107 (the memory ceiling stops guarding a belief)

Minted 2026-07-25 (session-47) by `/graduate` on `dn-local-model-runtime` §2.8, which rules this
out of the migration wave and asks for it separately and immediately. **Not started.**

## Pre-build notes for whoever picks this up

- **The warrant is MEASURED, not argued.** finding-0199 was reproduced live during the runtime
  design pass — all three phases, including a `_check_ceiling` **pass at 23.0 ≤ 24.0 against a
  true prospective 25.7 GB**. Item 2's falsifier is that exact case. If it still passes, nothing
  shipped.
- **The brick risk is the thing to be careful about.** The embedder is absent from the registry
  entirely, so it is *always* an unknown name. A naïve fail-closed rule refuses every non-pinned
  load on any system that has ever embedded. §6 pins the carve-out; §10 makes "the pinned model
  would be refused" a STOP.
- **The retrofit trap is pre-widened, not discovered.** Constructing a `TwoSlotLoader` will now
  imply a client answering `ps()`, so five existing test files are already in `write_scope` per
  the graduate skill's rule (findings 0071/0072/0075/0084). **Grep before editing** — §3 Q6
  records that the code does not settle which of the four integration files build a loader
  directly.
- **This plan is expected to be superseded**, and that is fine: `dn-local-model-runtime` §2.3
  deletes `_resident` outright when residency becomes child-process existence. bp-107 buys
  correctness for the interval.

## Owed at seal (orchestrator, not the builder)

finding-0199's §"Status of the evidence" still reads *"code-traced, NOT empirically reproduced."*
That is now false — correct it with a banner. A builder may not edit an existing finding, so it is
recorded here rather than done.
