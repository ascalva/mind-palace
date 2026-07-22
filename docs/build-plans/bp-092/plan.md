---
type: build-plan
id: bp-092
track: code-ingest
status: ready
design_ref:
  - docs/design-notes/code-ingest-pipeline.md
contract: builder
write_scope:
  - core/ingest/**
  - core/provenance.py
  - core/stores/vectorstore.py
  - ops/code_snapshot.py
  - scheduler/**
  - config/defaults.toml
  - tests/unit/test_code_corpus*.py
  - tests/unit/test_provenance*.py
  - tests/integration/test_code_vector*.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 550k
  actual: null
depends_on: []
parallelizable_with: []
created: 2026-07-21
updated: 2026-07-21
links:
  - docs/design-notes/code-ingest-pipeline.md
  - docs/findings/finding-0146.md
  - docs/findings/finding-0147.md
re_entry: null
supersedes: null
superseded_by: null
warrant: docs/findings/finding-0146.md
---

# Build Plan — CI-1: the code embed lane (L0a + L0b + L1, Provenance.CODE, joins, incremental)

> **Every section below is required.** N/A is an accountability act.

## 0. Mode & provenance

Graduated 2026-07-21 from `dn-code-ingest-pipeline` (ratified `0c2deae`; audited at fable,
finding-0147) §3 CI-1. Investigation/planning only; `proposed → ready` is the owner's hand.

## 1. Objective

Land the three-layer code embed lane — L0a symbol slices, L0b raw-source windows, L1 prose —
into the existing vector store under a structurally-minted `Provenance.CODE`, line-range
joined, blob-sha-keyed incremental, seed run scheduler-gated.

## 2. Context manifest

1. `docs/design-notes/code-ingest-pipeline.md` — §2.1/§2.1b/§2.2/§2.3/§2.7/§2.8 WHOLE.
2. `core/ingest/chunk.py`, `core/ingest/pipeline.py`, `core/ingest/index.py`,
   `core/ingest/amend.py`, `core/ingest/embed.py` — the reused machinery.
3. `core/provenance.py` + `core/stores/vectorstore.py` — the enum + schema being extended.
4. `ops/code_snapshot.py` — the ledger the span/comment capture extends.
5. `core/stores/code_observations.py:146-150` — the hardcoded-mint pattern to copy.
6. `core/ingest/curated.py` — the own-graph precedent.
7. `docs/findings/finding-0147.md` — the audit corrections that BIND this build (§6).

## 3. Investigation & grounding

- **Q1 — the reuse seam is `chunk_text`, NOT `derive_chunks`** (audit correction, note §2.1
  L0b): `derive_chunks` bundles the Logseq `strip_properties` pass (`core/ingest/pipeline.py:
  22-34` → `core/ingest/logseq.py:69-83`) — note-lane-specific; 0 tracked `.py` lines match
  `_PROP` today but the exclusion must be structural. L0b/L1 call
  `chunk_text` (`core/ingest/chunk.py:44-56`) directly.
- **Q2 — the ledger lacks `end_lineno` and comments.** `symbols` DDL carries `lineno` only
  (`ops/code_snapshot.py:60-69`); `#` comments enter no store (`:131-136,158` — AST drops
  trivia). Both land as additive migrations in the `open_snapshot_db` pattern (`:296-318`).
- **Q3 — the row schema has no `layer` or `embedder` column** (`core/stores/vectorstore.py:
  27-37`); extension delivered by reset+rebuild (the note's recorded default; §5-4 offered
  the owner an alternative — none chosen ⇒ rebuild stands). 28 rows today; re-derivable
  bit-identically (`core.ingest.verify`).
- **Q4 — provenance enum has six classes** (`core/provenance.py:44-61`); `CODE` is the
  seventh; `MIRROR_READABLE` (`:78-80`) is untouched.
- **Q5 — group-by-digest works unchanged for blob-sha digests** (`core/stores/sourceset.py`
  invariant: one provenance stratum per digest — all code rows are CODE ✓).
- **Q6 — incremental idiom exists:** `vectorstore.delete(digest=…)` (`:78-86`) +
  `index_amendment`'s reuse-unchanged discipline (`core/ingest/index.py:61-82`).
- **Q7 — no daemon change:** the lane is an ingest entry point; the seed rides the
  scheduler's housekeeping lane (a new queue KIND, the `chat_sync` handler shape,
  `ops/lifecycle/launcher.py:314-327` registry) — `ops/code_sensor.py` is NOT touched
  (CI-3's surface; disjointness is deliberate).
- **Code does not settle:** exact scheduler cadence knob for the seed (config value chosen
  at build, journaled); M-C1's one-file timing decides batch sizes.

**Additional risks surfaced:** bp-090 (K1), if blessed first, renames `core.ingest.*` to
`core.kernel.ingest.*` — this plan's new module stays OUTER (`core/ingest/code_corpus.py`
imports the embedder/LanceDB) so it lives in the residue home either way; expected ring-map
delta **∅** (the M1-rider statement, inner-outer-core §3).

## 4. Reconciliation

- `core/provenance.py` docstring's five-class spectrum → **[cross-ref: extension]**: the
  CODE entry documents "builder-produced reality read from the repo instrument;
  ∉ MIRROR_READABLE; dreamable by named grant only (XS-a)."
- `ops/code_snapshot.py` header "Deliberately NOT here: ingesting snapshots into the
  knowledge corpus… stays on the ops side until that is ratified" (`:17-21`) →
  **[banner: correction]**: ratification happened (`dn-code-ingest-pipeline`, 2026-07-21);
  the header paragraph is updated by this build to cite it — an announced correction to
  committed code, carried by Item 1.

## 5. Write scope

Front matter mirrors §2's surfaces. OUT: `ops/code_sensor.py` + `core/stores/
reference_edges.py` (CI-3's), `core/origin_view.py` (CI-2's), `eval/**` (CI-2's readings),
`core/mirror.py` (untouchable firewall), all foundation-denylist paths. New test files are
plan-specific globs so CI-3 stays disjoint. `config/defaults.toml` only for the seed lane's
config block.

## 6. Interfaces pinned inline

- **Mint rule (§2.3, verbatim obligation):** the code lane's row assembly hardcodes
  `Provenance.CODE`; **no provenance parameter anywhere on its API** (the
  `CodeObservation.to_row` move, `core/stores/code_observations.py:146-150`). It does NOT
  call `ingest_note` (provenance-parametric, a laundering surface); it reuses
  `chunk_text`/`Embedder.embed_documents`/`VectorStore.add` below the parameter.
- **Row schema extension:** existing `_chunk_row` fields (`core/ingest/index.py:27-40`) +
  `layer ∈ {code_ast, code_text, codedoc}` (note rows default `prose`) + the L2a fiber
  coordinates `(path, qualname, line_start, line_end)` carried ON the rows — no edge rows
  minted (the fiber ruling, note §2.4). `digest` = git blob sha.
- **L0a unit (§2.1 as audited):** per-symbol slice at AST boundaries; nested defs own
  symbols; parents embed as SHELLS; the module shell covers preamble + inter-symbol +
  trailing; **every source line in exactly one L0a chunk** (F-CI2's invariant); header
  `# {path}:{qualname}{signature}` prefixed; oversized slices hard-split via `chunk_text`.
- **L1 unit (§2.2):** module docstring + symbol docstrings + tokenize-captured `#` comments,
  source order, coordinate headers, chunked by `chunk_text`.
- **Embedder:** `qwen3-embedding:4b` unchanged (`config/defaults.toml:96-101`); one space or
  no bridge (D2). No second model, ever, in this plan.
- **Falsifiers as tests:** F-CI1 (a CODE row through MirrorView/MIRROR_READABLE-default
  search, or a provenance parameter on the lane's API ⇒ firewall incident); F-CI2 (L0a
  byte-cover fails, or any layer not bit-identically re-derivable from the blob); F-CI5
  (any MIRROR_READABLE-path instrument result changes when code rows are added/removed —
  the `test_reference_edge_isolation` pattern applied to the vector plane).

## 7. Items

### Item 1 — ledger capture extensions (additive migrations; read-side)

- **Objective:** `end_lineno` on symbols + a `comments` sidecar (tokenize pass, innermost
  containing symbol by line range, file grain otherwise) + FULL import records (dotted
  module + imported names — minted here because this is the ledger-migration commit; CI-3
  consumes it) + the §4 header correction.
- **Files:** `ops/code_snapshot.py`, `tests/unit/test_code_corpus_ledger.py` (new).
- **Acceptance test:** migration idempotent on the existing ledger; a fixture file's spans
  byte-cover; comment count for the repo reproduces the audited 3,318 over the pinned
  main-package set.
- **Falsifier:** any existing ledger row changes (this is ADDITIVE; a mutated row means the
  migration is wrong) — compare row counts + a checksum of pre-existing columns.
- **Invariant(s):** snapshot idempotence by sha; φ_code sole-interpreter (the tokenize pass
  rides the same blob walk, `_cache` discipline `:193-208`).
- **Touches stored data?** yes — `data/code_snapshots.sqlite`, additive; dry-run on a copy
  first. **Parallelizable?** no. **Depends on:** none.

### Item 2 — the three chunkers + the CODE mint + the layer column (reversible)

- **Objective:** `core/ingest/code_corpus.py`: L0a/L0b/L1 derivations (pure, blob→chunks,
  bit-identical re-derivable), row assembly with hardcoded CODE + layer + fiber coordinates;
  `Provenance.CODE` enum entry; vectorstore `layer` column via reset+rebuild (note rows
  re-landed `prose`; count 28 preserved).
- **Files:** `core/ingest/code_corpus.py` (new), `core/provenance.py`,
  `core/stores/vectorstore.py`, tests.
- **Acceptance test:** F-CI2 test green (byte-cover + re-derivation); the rebuilt note rows
  verify via `core.ingest.verify`; F-CI1 structural test green (no provenance param exists —
  asserted by API introspection).
- **Falsifier:** F-CI1/F-CI2 as pinned. Rebuild losing or altering any of the 28 note rows'
  text/digest ⇒ the migration path is wrong — halt, restore, finding.
- **Invariant(s):** MIRROR_READABLE untouched; `semantic_search` default unchanged
  byte-identically.
- **Touches stored data?** yes — `data/vectors.lance` reset+rebuild; verify pass mandatory
  before and after. **Parallelizable?** no. **Depends on:** Item 1.

### Item 3 — incremental sync + the seed entry point (reversible; gated execution)

- **Objective:** blob-sha-keyed incremental (walk commits since last sync; changed blobs
  only; `delete(digest)` + re-add; unchanged file = zero embeds) + the scheduler-gated seed
  entry (new queue KIND, housekeeping tier, batch via `embed_documents`); M-C1 one-file
  timing recorded BEFORE any full run.
- **Files:** `core/ingest/code_corpus.py`, `scheduler/**` (one KIND + handler),
  `config/defaults.toml` (lane block, default off), tests.
- **Acceptance test:** two-commit fixture: second sync embeds only changed blobs (counted);
  M-C1 timing in journal; the seed refuses beside a slot-2 heavyweight (scheduler gate
  honored — asserted with the scheduler's existing refusal seam).
- **Falsifier:** an unchanged file re-embedding (the incremental claim fails); a seed batch
  starting while the memory gate says no ⇒ non-negotiable #8 breach — stop, incident.
- **Invariant(s):** #8; the lane is not a resident (no daemon restart required).
- **Touches stored data?** yes (vectors.lance additions). **Parallelizable?** no.
  **Depends on:** Item 2.

### Item 4 — the seed run + M-C2/M-C8 readings + F-CI5 (execution + read-only)

- **Objective:** run the seed (idle window, owner-visible), then: M-C2 chunk census
  (counts/sizes/L0a cover verification), M-C8 L0a↔L0b mismatch distribution, and the F-CI5
  isolation ratchet (MIRROR_READABLE instrument results bit-identical with code rows
  present/absent).
- **Files:** tests + journal (readings recorded; ~7k-row store expected, ±2×).
- **Acceptance test:** F-CI5 test green and permanent; M-C2/M-C8 tables in the journal;
  chunk volume within ±2× of ~7k (outside ⇒ finding, not silent).
- **Falsifier:** F-CI5 fires ⇒ isolation breached — treat as firewall incident (F-AL4
  posture), not a bug; M-C8 degenerate ⇒ F-CI7 → PD-K re-enters (fold L0b), recorded.
- **Invariant(s):** all of §6. **Touches stored data?** yes (the seed).
  **Parallelizable?** no. **Depends on:** Item 3.

## 8. Math carried explicitly

- **L0a↔L0b mismatch (M-C8)** — *measures:* cosine between a symbol vector and the centroid
  of its covering L0b windows. *valid when:* both layers embedded at the same embedder
  version (A7 cut); coverage join computed from row coordinates. *fails its keep if:* the
  distribution is degenerate (F-CI7) — then L0b folds (PD-K) and the instrument is dropped,
  not tuned.

## 9. Non-goals

No resolver/reference work (CI-3). No retrieval-quality claims (CI-2's M-C3/M-C4). No
dreamer grant changes (PD-H; owner-only). No historical backfill (PD-B). No second embedder
(PD-C). No mirror/verdict/effector changes. No `ops/code_sensor.py` edits.

## 10. Stop-and-raise conditions

Any need to touch CI-3's surfaces. The reset+rebuild disturbing note rows. A memory-gate
refusal during the seed (park, resume at idle — never override). Chunk volume >2× estimate.
Any owner-level question on §5-4's migration preference if in-place proves necessary — park
the item, continue others.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| per-row `embedder` stamp | not added; A7 stays corpus-wide config pin | adding now (no consumer; the audit killed the false already-exists claim) | the first consumer needing mixed-version reads; rides a later layer-column-style migration |
| test-file inclusion (PD-A) | include (φ_code parity) | exclude tests (loses spec knowledge) | M-C3 shows test-chunk domination — then a `layer`-side exclusion |
| stored file centroids (PD-E) | computed on read (`note_centroids` pattern) | store them (a DERIVED cache without a hot consumer) | profiling shows centroid computation hot |

## 12. Dependency & ordering summary

Items linear 1→2→3→4. `parallelizable_with: []` — CI-3 (bp-094) is surface-disjoint but
Item 1 mints the import-record migration CI-3 consumes, so bp-094 starts only after this
plan's Item 1 is committed (or after full seal — orchestrator's scheduling call). Sequencing
vs bp-090 (K1): either order (bp-090 §12); not concurrent — write scopes overlap on
`core/ingest/**` and `tests/**`.
