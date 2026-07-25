---
type: journal
plan: bp-118
started: null
updated: 2026-07-25
---

# Journal — bp-118 (P4: the embedder cutover)

Minted 2026-07-25 (session-48) by `/graduate`, decomposing both ratified ops notes
(`dn-supervision-and-liveness` and `dn-local-model-runtime`) in one context. **Not started.**

## Pre-build notes for whoever picks this up

- ⚑ **This plan does NOT flip anything. The owner does.** Editing `config/local.toml` crosses a
  gate. The deliverable is a deskcheckable shadow-run report.
- ⚑ **Do not start until bp-117's gate is GREEN.** This is a precondition, not a checklist item.
- ⚑ **Item 4's falsifier would stop the whole wave**: if a mixed scratch store fails the golden
  gate, §2.5's no-re-embed-in-either-direction claim is false and the cutover is a one-way door.
  Exercise the rollback; never assume it.
- ⚑ **A silent fallback would be catastrophic.** If llamacpp fails to start and the code quietly
  uses Ollama, the owner believes a cutover happened that did not — and the shadow evidence would
  be about a configuration that is not running.
- ⚑ **Nothing here may land a vector into `data/vectors.lance`.** The shadow run computes and
  compares in memory. Landing a shadow vector creates the exact mixed store the gate prevents.
- **§3 Q1: the note names the config key two ways.** §4 (`[runtime] embedding_backend`) governs,
  because it is the wiring section and bp-115 built to it. If the owner meant `[embedding]
  backend`, that is a §10 raise.
- **§3 Q3: the QUERY path is not length-bounded by anything.** Only the chunk path is capped.
- **At seal, be honest**: finding-0174 does not close until the owner flips the key.

## Owed at seal (orchestrator, not the builder)

Findings referenced in §4 Reconciliation are cross-referenced, never edited — a builder may not
edit an existing finding. Record closure evidence here for the orchestrator to apply at seal.
