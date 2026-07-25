---
type: journal
plan: bp-114
started: null
updated: 2026-07-25
---

# Journal — bp-114 (the vault lane split)

Minted 2026-07-25 (session-48) by `/graduate`, decomposing both ratified ops notes
(`dn-supervision-and-liveness` and `dn-local-model-runtime`) in one context. **Not started.**

## Pre-build notes for whoever picks this up

- ⚑ **The widest retrofit surface in the wave: EIGHT integration test files** pin
  `VaultSync`/`index_amendment`. They assert IDENTITY (doc_id binding at first bind only, rename
  continuity, version chains, stable point ids). A weakened assertion there is invisible and
  permanent. Diff every edit and justify each in this journal.
- ⚑ **`raw.add` is a WRITE in the compute half and the note does not say which side owns it**
  (§3 Q3). Default: the SUPERVISOR archives before dispatch. Do NOT hand the worker a `RawStore`
  writer as a convenience — raw is the substrate everything else is re-derivable from.
- ⚑ **Landing order matters and step 5 must stay AFTER step 3** (§6). `sync.py:131-133` explains
  why: the doc_id is resolved after `catalog.record` so the row exists.
- ⚑ **Do NOT upgrade "atomically-ish" to "atomic".** The note is explicit that the split does not
  make the delete->add window atomic; it moves it somewhere signals never interrupt.
- **Item 2's falsifier is a SILENT cost regression**: losing `vec_by_hash` reuse
  (`index.py:77,85`) makes every edited note re-embed wholesale. Record the baseline ratio first.
- **If bp-113 is running in parallel, read its landed landing idiom before writing this one.** Two
  idioms for one protocol is the DRY defect this pair is most exposed to.

## Owed at seal (orchestrator, not the builder)

Findings referenced in §4 Reconciliation are cross-referenced, never edited — a builder may not
edit an existing finding. Record closure evidence here for the orchestrator to apply at seal.
