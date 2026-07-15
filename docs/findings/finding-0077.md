---
type: finding
id: finding-0077
status: routed           # open → routed → resolved | promoted  (batched → oq-0023)
created: 2026-07-14
updated: 2026-07-14
links:
  - docs/build-plans/bp-034/plan.md      # §5 Q5b + parked decision 4 (strip props before embedding)
  - core/ingest/index.py                  # _chunk_row / index_amendment — the embedded text
  - core/ingest/logseq.py                 # where properties are (not) stripped from text
  - core/dreaming/cluster.py              # the σ=0.62 similarity graph the dreams cluster over
ftype: direction         # blocker | spec-defect | question | discovery — a measured design regression
origin_plan: bp-034
route: orchestrator       # design/direction → owner-gated follow-on plan
resolution: null
---

# The id:: mint measurably changed the mirror graph — embedding identity metadata pollutes similarity

## What

The bp-034 mint prepends `id:: <uuid4>` to every note. An empirical A/B on the OWNER'S corpus (13 notes),
embedding the pre-mint bytes (from `data/mint_ids_backup/vault`, no id::) and the current bytes (with id::)
through the SAME pipeline + the real `qwen3-embedding:4b` embedder in one run, measured the effect on the
σ=0.62 similarity graph the dreamer clusters over:

```
mirror edges @σ=0.62:   pre-mint = 5      post-mint = 9    (+4 edges, −0)
per-note centroid drift cos(pre,post):  min 0.891  mean 0.953   (NOT all ≥0.99)
max pairwise |Δcos|: 0.169     closest pair to σ: 0.0009
```

Validation: the fresh post-mint embed reproduced the live vector store's 9 edges exactly, so the pre=5
counterfactual is trustworthy. **The migration changed the thematic clustering (5→9 connections), which
drives the dreams.**

Mechanism: every note now begins with the shared literal `"id:: "`, which uniformly lifts pairwise cosine
a little — pushing 4 borderline pairs over σ (hence +4/−0). The random uuid then adds content-free noise
to each note's centroid, worst on short notes (0.891). The graph now partly reflects IDENTITY METADATA,
not note content.

## Why it matters

The similarity graph is load-bearing: it defines theme clusters → dreams → (eventually) the reasoning
complex. Denser-by-artifact clustering means dreams merge notes for reasons unrelated to their meaning.
This is a QUALITY regression on the semantic layer — not a data loss and not a correctness bug (the mint's
identity/rename-stability purpose is achieved and nothing was lost), but a real, measured behavioral
change from pre-migration. It is the reason a "100% consistent with pre-migration behavior" claim is false.

## Re-entry condition

This IS the re-entry condition for bp-034's **parked decision 4** ("strip property lines from embedded
text — deferred; re-entry: a measured retrieval-quality regression from property noise"). Now measured.
No rollback: the fix is additive. A follow-on plan should strip `id::` (and consider all `key::` page-
property lines — they are metadata, not prose) from the DERIVED/embedded text in the ingest path
(`logseq.py`/`index.py`), leaving raw + the authored file byte-identical, then re-embed from raw (§8,
regenerable). Re-embedding restores the content-only graph. Owner rules scope (id:: only vs all props)
at graduation.

## Routing

`direction` → orchestrator. Non-blocking; the migration stands. Batch to owner-questions for the scope
call (id:: only, or all page properties), then graduate a small ingest plan (strip-props-before-embed +
re-embed-from-raw). Until then, the live mirror graph carries the +4-edge artifact — dreams remain valid
but are clustered slightly denser than content alone warrants.
