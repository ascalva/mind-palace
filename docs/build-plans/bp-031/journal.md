# bp-031 journal

## 2026-07-14 — authored `proposed` (orchestrator, opus/xhigh graduation)

Graduated from `dn-temporal-retrieval-algebra` (ratified `6108dd8`) — the **FIRST** plan of that note's
graduation, per the A6 ruling (note §2.4 / Owner rulings 2026-07-14: rename-stable identity is a HARD
PREREQUISITE, gating the diachronic reader / Result-1 H1 / β\*-over-lineage). Companion plan bp-032
(`core/temporal/` module) `depends_on: bp-031`.

**Grounded pass (citations in §3):**
- The fork point is `sync.py`: identity keyed on `source_path` throughout (`:84,89,99,112`); a rename =
  `handle_deleted(old)` tombstone + `sync_path(new)` fresh seq-1 chain → version continuity lost
  (`supersession-lifecycle.md:287-289`).
- **De-risking discovery #1:** `versions.py` **already** keys on a generic `doc_id` column (`:54,59`);
  today `sync.py:112` just passes `source_path` *as* the doc_id → **the version schema is UNCHANGED**;
  only the value sync resolves changes.
- **De-risking discovery #2:** `logseq.py`'s `_PROP` regex (`:19,64`) already parses `id::` into
  `ParsedNote.properties` → reading an **existing** page id is zero-new-code, zero-vault-mutation.
- Blast radius: `source_path`/catalog/versions referenced across ~20 test files (grep) → contained by
  **behavior-preservation** (backfill `doc_id := source_path`; default resolution to `source_path`).

**One decision is deliberately UNRESOLVED (A4 discipline):** the identity *mechanism* — the note left it
open ("front-matter uuid **or equivalent**", `supersession-lifecycle.md:290`). Routed to the owner as
**oq-0019** (recommended default: existing-`id::` + exact-content rename detection on rescan; **no**
mint-into-vault). The plan is split at that seam: **Item 1 is mechanism-agnostic and buildable on
blessing**; Items 2–3 park on the ruling and proceed after (never-block).

**write_scope lists all three test paths** (finding-0075 discipline — the THIRD recurrence of 0071/0072):
`test_rename_identity.py` (NEW) + `test_version_history.py` + `test_vault_sync.py` (the store/sync homes
that may need a visible-surface touch). The finding-0075 nuance is honored: any OTHER existing test
reddening is a **stop-and-raise** (§10), not a self-widen — Item 1 must be additive.

Estimate opus/300k (live-store migration + a behavior-preservation falsifier needing judgment). Awaiting
the owner-only `proposed → ready` blessing **and** the oq-0019 mechanism ruling. No code written.
