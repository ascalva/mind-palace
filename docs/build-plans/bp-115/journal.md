---
type: journal
plan: bp-115
started: null
updated: 2026-07-25
---

# Journal — bp-115 (P1: the inference client seam)

Minted 2026-07-25 (session-48) by `/graduate`, decomposing both ratified ops notes
(`dn-supervision-and-liveness` and `dn-local-model-runtime`) in one context. **Not started.**

## Pre-build notes for whoever picks this up

- ⚑ **Nothing observable may change.** That is the acceptance bar. Every later phase's rollback
  story rests on this being a pure refactor.
- ⚑ **`Embedder` is ALREADY a backend-neutral facade** (`core/ingest/embed.py:29-34`). Do not build
  a second one. This is also why the supervision worker needs no ordering against this plan.
- ⚑ **Read the protocol OFF the working client, not against llama.cpp** (§7 Item 1 falsifier). If
  `OllamaClient`'s signatures must change to fit, the protocol was designed backwards.
- ⚑ **`ps`/`load`/`unload`/`list_models` are NOT on the protocol** (§3 Q1) — they exist only
  because Ollama owns residency, and forcing `LlamaServerClient` to implement them is four lies.
- ⚑ **Do not touch `core/models/loader.py`** — bp-107 is landing on it and bp-116 replaces it.
- **If ANY existing test needs editing, STOP and investigate** (§10). Widening a concrete
  annotation to a Protocol is strictly more permissive; a red test means something else moved.
- **The chat path cannot be verified against a real model** (§2.1 E — the blobs do not load
  upstream). Saying otherwise in this journal would be a false completion claim.

## Owed at seal (orchestrator, not the builder)

Findings referenced in §4 Reconciliation are cross-referenced, never edited — a builder may not
edit an existing finding. Record closure evidence here for the orchestrator to apply at seal.
