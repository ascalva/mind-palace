---
type: journal
plan: bp-119
started: null
updated: 2026-07-25
---

# Journal — bp-119 (P5: the chat tiers (PARKED))

Minted 2026-07-25 (session-48) by `/graduate`, decomposing both ratified ops notes
(`dn-supervision-and-liveness` and `dn-local-model-runtime`) in one context. **Not started.**

## Pre-build notes for whoever picks this up

⚑ **PARKED. DO NOT BLESS `proposed -> ready` until BOTH hold:**
1. **V-B** — upstream-convention GGUFs for the chat lineup are present locally, LOAD on the pinned
   llama.cpp build, and their quant lineage is verified against the Ollama tags (Q4_K_M).
2. **V-A** — 27b/35b true RSS measured at role ctx (bp-116 Item 1).

V-B is **not engineering work**. §2.1 E measured that Ollama's chat blobs fail to load upstream —
`key qwen35.rope.dimension_sections has wrong array length; expected 4, got 3` — for the whole
`qwen35` lineup. Sourcing replacements is an owner/ops action outside the repository, and §2.4
forbids the core from fetching them. No amount of building clears this.

- ⚑ **Item 1's prompt-byte check is the real gate.** Ollama launches its bundled server with
  `--no-jinja --chat-template chatml` (§2.1 D). If the palace's spawn produces different prompt
  bytes, every behavioural comparison is confounded and a golden regression is misattributed.
- ⚑ **A quant mismatch is a MODEL CHANGE** — an owner-stated non-goal, and it invalidates the
  entire equivalence story.
- ⚑ **Take the drift baseline BEFORE the flip, same-runtime.** Comparing post-flip drift against an
  Ollama-era baseline attributes normal corpus drift to the runtime.
- **Generation's bar is NOT string equality** (§2.5): seed-pinned greedy as a determinism sanity
  check, golden + drift for behaviour.
- **Ollama is not retired here.** That is a separate owner decision after a deskcheck.

## Owed at seal (orchestrator, not the builder)

Findings referenced in §4 Reconciliation are cross-referenced, never edited — a builder may not
edit an existing finding. Record closure evidence here for the orchestrator to apply at seal.
