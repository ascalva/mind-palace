---
type: finding
id: finding-0076
status: open             # open → routed → resolved | promoted
created: 2026-07-14
updated: 2026-07-14
links:
  - core/ingest/mint_ids.py
  - scripts/mint_ids.py
  - core/stores/catalog.py
  - docs/build-plans/bp-034/plan.md
ftype: spec-defect       # blocker | spec-defect | question | discovery
origin_plan: bp-034
route: builder           # codebase | spec-fidelity → builder resolves
resolution: null
---

# `mint_ids.py --dry-run` is not fully side-effect-free against a pre-bp-031 catalog

## What

Item 13's contract (and the integration test `test_preview_lists_only_no_id_notes_and_mutates_nothing`)
says `preview()` / `--dry-run` opens no write handle and mutates nothing. Observed during the LIVE
bp-034 mint (2026-07-14, owner-run): the FIRST `--dry-run` against the legacy corpus **wrote to the live
`vault_catalog.sqlite`** — it added the `doc_id` column and backfilled `doc_id = source_path`.

Cause: `preview()` itself is pure-read, but it takes a `VaultSync`, and `VaultCatalog.__post_init__`
unconditionally runs `_migrate()` on open (bp-031's idempotent `ALTER TABLE … ADD COLUMN doc_id` +
backfill). So the *observable* effect of `mint_ids.py --dry-run` includes a schema migration whenever the
on-disk catalog predates bp-031. The integration test never caught this because its catalog is born at
HEAD schema (`doc_id` already in `_DDL`), so `_migrate` is a no-op there.

## Why it matters

Benign in THIS case — verified during the run: the pre-bp-031 daemon (`5a08cd4`) uses **named-column**
INSERTs, so the added nullable column does not break it (no `OperationalError`, no corruption), and the
migration was inevitable at deploy anyway. But it is a genuine contract gap: "dry-run mutates nothing"
is false against a legacy store, and a future store whose `_migrate` is *not* backfill-benign could make
`--dry-run` a surprising mutation. It also means the deploy-coupling window (finding-0066) is entered by
a *dry-run*, not just the `--confirm` run — worth documenting.

## Re-entry condition

Not parked (bp-034 is sealed; the live migration succeeded). Address opportunistically: either (a) narrow
the contract wording in `mint_ids.py` / the plan to "opens no write handle in `preview()`; the enclosing
`VaultSync` may run store `_migrate` on open" (accept-and-document), or (b) give `preview()` a read-only
catalog-open path that skips `_migrate` (stronger, more work). Recommend (a) — the schema-forward on open
is bp-031's intended, idempotent behavior; the fix is honest documentation, not code.

## Routing

`spec-fidelity` → builder. Non-blocking, informational; no active build. Batched by the orchestrator for
the next relevant build touching `mint_ids.py`/ingest, or closed as accept-and-document at `/triage`.
