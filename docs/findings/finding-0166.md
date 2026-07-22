---
type: finding
id: finding-0166
status: resolved         # open → routed → resolved | promoted
created: 2026-07-22
updated: 2026-07-22
links:
  - docs/build-plans/bp-099/plan.md
  - docs/design-notes/temporal-code-corpus.md
  - core/kernel/temporal/boundary.py       # poset_from_chains — the actual contract
  - ops/code_lineage.py                     # supersession_chains + the catch-up probe helper's sibling
ftype: spec-defect       # two build-time spec nuances, both resolved in-scope (no design change)
origin_plan: bp-099
route: builder           # codebase | spec-fidelity → builder resolves, annotates, continues
resolution: resolved in bp-099 build (session-43) — see below; no design-note change needed
---

# bp-099 build reconciliations: `poset_from_chains`'s int contract, and the catch-up probe must be like-to-like

## What

Two spec/code mismatches surfaced while building bp-099 Items 2–3. Both were resolved IN SCOPE
(no `core/temporal/**` edit, no design-note change) and are recorded here per the annotate-and-continue rule.

1. **`poset_from_chains`'s real contract is `dict[str, list[int]]`, and it RE-SORTS its chain
   values.** The note (D4) and plan (§2 item 6, §6) read as "hand the store-free
   `poset_from_chains` the per-path BLOB chains as-is." But the actual function
   (`core/kernel/temporal/boundary.py:99` — NB the plan's cited path `core/temporal/boundary.py`
   is stale; the module lives under `core/kernel/temporal/`) is typed `dict[str, list[int]]` and
   its body does `ordered = sorted(seqs)`. Its canonical caller (`core/temporal/acquire.py:40`)
   passes integer `version_seq` values. Feeding blob-sha STRINGS therefore (a) type-mismatches, and
   (b) would order each chain LEXICALLY by sha rather than by commit order — silently wrong
   supersession direction for any temporal consumer.

2. **The §6 catch-up shorthand "store distinct code digests < ledger distinct versions" would
   loop forever.** Distinct blob shas (1,472) is strictly less than distinct `(path, blob_sha)`
   versions (1,542) even when the backfill is COMPLETE (identical blobs shared across paths), so a
   literal probe would enqueue a backfill on every startup — exactly the loop the Item-2 falsifier
   forbids.

## Why it matters

(1) A latent correctness bug for the finding-0151 integrator: a lexically-ordered supersession
poset is not the temporal order. (2) An infinite-enqueue loop at every daemon start.

## Resolution (both in-scope, no core edit)

1. `ops/code_lineage.supersession_chains` returns the pinned `dict[str, list[str]]` — blob shas in
   commit order (the useful, correct lineage, and the D5 blob-identity source). A temporal consumer
   feeds `poset_from_chains` the commit-order POSITION of each blob (`index == version_seq`), which
   preserves order AND matches the int contract — a trivial ops-side re-keying, NOT a modification
   of `poset_from_chains` (the stop-and-raise is honored: core is untouched). The blob→embedded-node
   resolution for the D5 edge is done directly against `commit_diffs` + the vector store, not via
   poset element identity. The Item-3 test exercises exactly this path.
2. `ops/lifecycle/launcher._code_backfill_incomplete` compares DISTINCT `(path, blob_sha)` versions
   on BOTH sides (store embedded versions vs `ledger_versions`), so a complete store is exactly
   equal → the probe enqueues nothing. The Item-2 test pins both the incomplete (=1) and the
   equal/disabled (=0) branches — the no-loop guard.

## Re-entry condition

None (resolved). A future note/plan touching the supersession poset should adopt the
`version_seq`-as-position framing rather than "blob chains as-is"; flagged for the finding-0151
integrator pass so its C∘D composition wires the position map, not the raw sha chain.

## Routing

`spec-fidelity` → builder-resolved in bp-099; annotated here + in the journal. No owner action and
no design-note supersession required (the substrate's behavior matches the note's INTENT — every
version a node, every change a resolvable edge; only the mechanical feed shape differs).
