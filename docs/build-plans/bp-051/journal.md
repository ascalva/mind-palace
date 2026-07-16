# bp-051 journal — GC-1 the spine skeleton

Builder session. Worktree `agent-a04badfa30c454825`, branch (to be set).
Contract: `docs/build-plans/bp-051/plan.md`. Design ref (A8-immutable, CITE never edit):
`docs/design-notes/global-event-clock.md` §2.1 (GC-N1), §2.2 (g1/g2/g3 + store audit),
§2.7 (GC-N8 no-payload), §2.8 (three clauses), §2.9-5 (no silent caps / A-4 chain boundary).

## Frame read (in order)
CONSTITUTION, CLAUDE, CONVENTIONS, plan.md (all sections), design note §2.1–2.2/2.7–2.9,
the g2 exemplar (`core/attestation/{attestor.py:59-69,store.py producers_of}`), and the seven
audited store schemas (versions, runledger, edges, derived, eval, catalog) + `core/scope.py`
Stratum/Clock enums (vocabulary only). All schemas match the note §2.2 audit table — NO
schema drift → no §4 codebase finding needed (confirmed on disk in this worktree's modules).

## Environment facts that shaped the design
- ruff lint = `E,F,I,B,UP` only (no SLF) → reading a store's live `_conn` is lint-clean.
- `core.*` is mypy-STRICT (disallow_untyped_defs/calls, disallow_any_generics, warn_return_any).
- import firewall (`ops/import_lint`) forbids only `edge`/`cloud`/network — `eval` is allowed
  (core already imports `eval.harness.store` in `core/dreaming/shadow.py`). Plan §5 explicitly
  permits reading the eval store via its own class.
- `data/` is gitignored; this worktree has NO `data/` → config paths (REPO_ROOT-anchored to the
  worktree) resolve to non-existent files → `SpineSources.resolve()` yields all-None → the
  real-store acyclicity integrity test runs over an empty spine (passes; mechanism intact).

## Design decisions (grounded)
- **Read mechanism:** spine reads each store through its LIVE handle (`store._conn` SELECTs for
  SQLite; `EvalResultsStore.query()` for DuckDB). Live handle (not a fresh path connection) so
  `:memory:` test stores work and there is zero DuckDB write-lock contention. Never writes.
- **g1 (append chains) by rowid/version_seq — NOT wall (Law C4).** Public `all()`/`runs()` order
  by created_at/started_at/timestamp (wall) → FORBIDDEN as an ordering key; so spine SELECTs order
  by rowid / version_seq / doc_id only. Grep-testable falsifier honored.
  - versions → per-doc chains keyed doc_id, position=version_seq (INSERT-only, stable).
  - runledger runs → rowid chain; claims → g3 (run→c1→c2… program order), position=rowid.
  - edges → rowid chain (INSERT OR REPLACE but no intra-store g2 → cycle-safe).
  - attestations → rowid chain (INSERT OR IGNORE, stable) PLUS g2 DAG.
  - eval, catalog → chain-less, position=None, g2/g3 only.
- **DERIVED store is g2-only (no rowid g1 chain).** It uses INSERT OR REPLACE, which reassigns
  rowid; a re-recorded PARENT can get a higher rowid than its child, so a rowid g1 chain would
  CONFLICT with the g2 derived_from edge → a spurious cycle on real data. §2.2 pins derived order
  as "chain (ties broken by g2, never by wall)". So derived order = the derived_from DAG (content-
  id based, store-guaranteed acyclic). This is the subtle correctness point; documented in-module.
  (Spec-fidelity clarification of §2.2 — builder-resolved, annotated, NOT a blocking finding.)
- **g2** = global `produced_by[identifier] → {event}` join; edge p→e for each ref e consumes that
  some p produces (p≠e). Generalizes `producers_of`. Refs to no producer create NO edge (dropped +
  counted `refs_without_producer` in report) — never fabricated (Item-2 falsifier).
- **Stratum tag (library-level default, per-store; §2.7 vocabulary):** versions/catalog=mirror,
  edges/derived=interpreted, runledger/attestations=ops, eval=eval (its own Σ, §2.9-1). Exact
  per-store map is under-specified by the note (parked Σ-gated wrapper); documented default.
- **Acyclicity is a construction invariant:** `derive()` runs Kahn topo-sort and raises
  `SpineCycleError` on any cycle (§2.8-1 fail-closed). Integrity test = derive over real stores
  (raise ⇒ suite fails ⇒ the plan §10 STOP). Cross-check: seeded mutually-referencing attestations
  ⇒ derive raises (unit teeth).
- **Public surface EXACT** (SpineEvent/Order/Spine/SpineSources per §6). Extensions (allowed):
  `SpineEdge`+`generators()` (tagged direct g1/g2/g3 edges — the calibration handle),
  `producers_of()` (spine-level generalization of the exemplar), `report()`/`SpineReport`
  (no-silent-caps: names the unwired stores proposals/verdicts/observations/telemetry per §2.9-5),
  `SpineSources.resolve()` (lazy config resolver, existing files only), `SpineCycleError`.

## Status — COMPLETE (all three items; green gate clean)
- [x] Item 1 — enumeration + g1 chains. `tests/unit/test_spine.py`: per-doc version chains SEPARATE
      (positions=version_seq), edges rowid chain, eval chain-less (position=None, no g1 edges,
      `generators()==()`), deterministic run-to-run.
- [x] Item 2 — g2 + g3 + closure + order(). claim orders AFTER the version whose digest it
      references; run→claim1→claim2 program order (g3); reference-less cross-store pairs CONCURRENT;
      forged ref dropped (`refs_without_producer≥1`, no fabricated edge).
- [x] Item 3 — integrity teeth (`tests/integrity/test_spine_invariants.py`): acyclicity on the
      config-resolved real stores (empty in this worktree — no `data/`; mechanism intact) AND a
      seeded multi-store graph; forged mutual-attestation cycle ⇒ `derive()` raises `SpineCycleError`
      (fail-closed); chain-embedding (versions/edges/attestations g1 + derived g2 all embed BEFORE);
      §2.8-5 calibration: spine g2 among attestations == `derived_from_ids` edge-for-edge; no-payload
      row shape + no-note-text-leak + grep (no wall ORDER BY, no text-column read).
- [x] Green gate — all 5 legs green: ruff clean; `mypy core agents eval ops scheduler scripts`
      Success (202 files); argless mypy = **69** (baseline; my files add 0); type_gate OK; pytest
      **1307 passed, 10 skipped, 9 deselected**. Spine files alone: 20 passed.

## §4 reconciliation + spec-fidelity notes (builder-resolved, annotated)
- NO schema drift: all seven audited stores match the note §2.2 table on disk → no `codebase`
  finding needed.
- Spec-fidelity clarifications made (documented in-module, NOT blocking findings):
  1. **DERIVED store is g2-only** (no rowid g1) — §2.2 "ties broken by g2, never by wall" +
     INSERT OR REPLACE reassigns rowid (a re-recorded parent would cycle with its g2 child).
  2. **Per-store stratum tags** are a library default (`_STRATUM`): the note under-specifies the
     exact map (Σ-gated wrapper parked, plan §11); refinable at the View layer.
  3. **`frontier()` keys are per-CHAIN** ("<store>:<chain-key>", per-doc for versions) — the pinned
     `dict[str,int]` signature is preserved; "per-store" in the pin is loose (versions is multi-chain
     and the cut discipline §2.4 is per-store chain positions).
- Public surface pinned EXACTLY (SpineEvent/Order/Spine/SpineSources). Additive extensions:
  `SpineEdge`+`generators()`, `producers_of()`, `report()`/`SpineReport`, `SpineSources.resolve()`,
  `SpineCycleError`.
- No findings filed. Nothing stop-and-raised (no real-store cycle: worktree has no `data/`).
