---
type: journal
plan: bp-116
started: null
updated: 2026-07-25
---

# Journal — bp-116 (P2: the process manager)

Minted 2026-07-25 (session-48) by `/graduate`, decomposing both ratified ops notes
(`dn-supervision-and-liveness` and `dn-local-model-runtime`) in one context. **Not started.**

## Pre-build notes for whoever picks this up

- ⚑ **Item 1 (V-A/V-C/V-D) gates the design's policy, not just its numbers.** If V-A shows
  synthesis/stretch cannot fit even with the embedder stopped, §2.9's falsifier fires and the NOTE
  RETURNS TO THE OWNER. Run with the daemon down and record the free-RAM envelope beside each
  figure, or a later reader cannot tell a measurement from an artefact of pressure.
- ⚑ **`TwoSlotLoader` is UNTOUCHED** (§2.6 P2). It is bp-107's surface and it stays the live path
  until bp-118 flips a role. Two mechanisms coexisting IS the rollback story.
- ⚑ **`resident()` must be a VIEW, never a cache.** If any dict can go stale, finding-0199 has been
  rebuilt one layer up — the entire point of the plan.
- ⚑ **The spawn argv IS the capability.** What is ABSENT (`--model-url`, `-hf`, any download flag)
  matters as much as what is present. Item 4 plants mutations to prove the ratchet catches both.
- **SIGTERM->grace->SIGKILL is REQUIRED, not belt-and-braces** — §2.1 G measured llama-server
  wedging mid-request (>30.9 s, and >3.5 min in a second observation).
- **Nothing reaches tier 1.** Jetsam and crashes keep "residency changed without our decision"
  representable. Say tier 3 in the comments, never tier 1.
- **`psutil` only through `core/typedshims/psutil.py`** — bp-106's warrant is exactly this.

## Owed at seal (orchestrator, not the builder)

Findings referenced in §4 Reconciliation are cross-referenced, never edited — a builder may not
edit an existing finding. Record closure evidence here for the orchestrator to apply at seal.
