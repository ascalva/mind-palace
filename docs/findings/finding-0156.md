---
type: finding
id: finding-0156
status: resolved
created: 2026-07-22
updated: 2026-07-22
links:
  - docs/build-plans/bp-092/plan.md               # the plan whose write_scope drifted
  - docs/design-notes/code-ingest-pipeline.md      # the ratified note whose §2/§6 pins moved
  - docs/build-plans/bp-091/plan.md                # K3 — the relocation seal that caused the drift
ftype: spec-fidelity
route: orchestrator            # a plan write_scope edit is orchestrator-single-writer territory
resolution: orchestrator widened bp-092 write_scope to the relocated paths — core/provenance.py→core/kernel/provenance.py (dcd79c6) + carried tests/unit/test_interpreter_versions.py (bfa321b); the φ_code pin was re-pinned same-version as a verified declared refactor (f8b0fa6). Generalized to finding-0157 (add a graduation-time reference-scan rule).
---

# bp-092 write_scope + §2/§6 path pins drifted under the K1/K3 relocation (sealed AFTER graduation)

## What happened

bp-092 (CI-1, the code embed lane) was graduated 2026-07-21. Its write_scope and the
ratified note's §2/§6 interface pins name **pre-relocation** paths. The K1 seal (bp-090,
2026-07-22 01:12) and K3 seal (bp-091, 2026-07-22 01:35) then relocated "the S1 seven" into
`core/kernel/**` — AFTER bp-092 was graduated. The plan foresaw the `core.ingest.*` module
RENAME (§3, "the M1-rider statement: new module stays OUTER, ring-map delta ∅") but NOT that
one write_scope target — `core/provenance.py` — would itself move into the kernel.

## The concrete drift (verified on disk at this worktree's HEAD, synced to main)

| plan/note reference | actual location at HEAD | in write_scope? |
|---|---|---|
| `core/provenance.py` (the enum to extend with `Provenance.CODE`) | **`core/kernel/provenance.py`** | **NO** — blocks the mint |
| `chunk_text` (`core/ingest/chunk.py`) | `core/kernel/ingest/chunk.py` | read-only, fine |
| `derive_chunks`/`ingest_note` (`core/ingest/pipeline.py`) | `core/kernel/ingest/pipeline.py` | read-only, fine |
| `_chunk_row`/`index_amendment` (`core/ingest/index.py`) | `core/ingest/index.py` (stayed outer) | yes (`core/ingest/**`) |
| `VectorStore` (`core/stores/vectorstore.py`) | unchanged (stayed outer) | yes |
| `ops/code_snapshot.py` | unchanged | yes |

**The single blocker:** adding `Provenance.CODE` (the whole lane's structural mint, note §2.3;
plan §6 "Mint rule") requires editing `core/kernel/provenance.py`. `scope-guard --standalone
core/kernel/provenance.py` returns rc=2 (DENY). No route-around is permissible (CLAUDE.md write
discipline; journal-gate catches Bash writes post-hoc). Everything else in bp-092 (ledger
extensions, `core/ingest/code_corpus.py`, the vectorstore `layer` column, `scheduler/**`,
`config/defaults.toml`, tests) IS reachable within the existing write_scope.

## Resolution requested (orchestrator single-writer action)

Widen bp-092 `write_scope`: replace the dead `core/provenance.py` entry with
`core/kernel/provenance.py`. This is a pure relocation-tracking edit — the design intent
(add `Provenance.CODE`, mirror-excluded, structurally minted) is unchanged; only the file's
home moved. No design change, no gate touched. After the widen, Items 2–4 unblock.

## What proceeds meanwhile (no block on the owner)

Item 1 (ledger capture extensions in `ops/code_snapshot.py`) is fully in-scope and enum-independent —
built and tested this session. Item 2's `core/ingest/code_corpus.py` and the vectorstore `layer`
column are written but their green-gate assertions and the `Provenance.CODE` reference PARK on this
widen (re-entry: the write_scope carries `core/kernel/provenance.py`).

## Routing

`spec-fidelity` → orchestrator. It needs a one-line plan-front-matter write_scope edit (builder
cannot edit the plan's own write_scope — CLAUDE.md Roles). Sibling to the standing "relocation seals
must sweep in-flight plans' write_scopes" hygiene question.
</content>
</invoke>
