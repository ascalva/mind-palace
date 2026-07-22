# bp-092 journal

## 2026-07-21 — minted (graduation, session-41)

Graduated from ratified dn-code-ingest-pipeline (0c2deae; fable-audited, finding-0147)
per §3. Status: proposed — awaiting the owner's proposed→ready hand-bless. No work
performed. Grounding computed at graduation is recorded in the plan's §3.

## 2026-07-22 — build session (delegated builder, worktree agent-aef072ee)

**Step 0 — bind + sync.** `active-plan` = bp-092 (verified). `git merge --no-edit main` →
"Already up to date" (worktree base already on current main; `core/kernel/**` tree present,
recent `seal(bp-091)` visible). Stayed inside the worktree dir throughout — never the shared
checkout.

**Grounding (whole-file reads).** Plan, journal, ratified note (dn-code-ingest-pipeline),
findings 0146/0147. Machinery at REAL post-K1/K3 locations: `core/kernel/provenance.py` (the
StrEnum, six classes; mirror `OBSERVED` hardcoded mint pattern is `code_observations.py:146-150`),
`core/kernel/ingest/{chunk,pipeline,amend,verify}.py`, `core/ingest/{index,embed}.py` (stayed
outer), `core/stores/vectorstore.py` (outer; 8-col schema, no `layer`), `ops/code_snapshot.py`
(the ledger: symbols carry `lineno` only, no `end_lineno`; `imports` stores only the dotted ROOT;
`#` comments enter no store), `scheduler/{vault_sync,chat_sync,router}.py` + `ops/lifecycle/
launcher.py:311-346` (the KIND registry + housekeeping/catchup enqueue), `config/defaults.toml`.

**BLOCKER found — write_scope drift from K1/K3 (filed finding-0156).** bp-092 was graduated
2026-07-21; K1 (bp-090) + K3 (bp-091) sealed 2026-07-22 01:12–01:35, AFTER graduation, and
relocated `core/provenance.py` → `core/kernel/provenance.py`. Adding `Provenance.CODE` (the
lane's whole structural mint, note §2.3 / plan §6) therefore needs a kernel file that is OUTSIDE
this plan's write_scope. Verified empirically: `bash .claude/hooks/scope-guard.sh --standalone
core/kernel/provenance.py` → rc=2 (DENY). No route-around permissible. Escalated to the
orchestrator for a one-line write_scope widen (`core/provenance.py` → `core/kernel/provenance.py`);
filed finding-0156 (spec-fidelity → orchestrator). Everything else in bp-092 is reachable within
the existing scope. Comment count at HEAD = 3360/254 main-package files (vs audited 3318/247 at
625a058 — real commits since; Item 1 test will self-consistently recount, NOT hardcode 3318).

**Proceeding:** Item 1 (ledger extensions, `ops/code_snapshot.py`) is enum-independent and fully
in-scope — building it now. Items 2–4 park on the widen (re-entry: write_scope carries
`core/kernel/provenance.py`).

### Item 1 — ledger capture extensions — DONE

`ops/code_snapshot.py`, all ADDITIVE (no existing row mutated):
- **`symbols.end_lineno`** (L0a slice boundary): captured in `_walk_defs` from `ast` `end_lineno`;
  additive `ALTER` migration in `open_snapshot_db` (default 0 → backfilled to a real span).
- **`comments` sidecar** (closes finding-0146 defect 2): a stdlib `tokenize` pass (`_comments`),
  each `#` comment attributed to the INNERMOST symbol whose `lineno..end_lineno` span contains it
  (`_innermost_qualname`, smallest span wins), '' = file grain. Tokenize errors → no comments for
  that file, never a snapshot failure. New `comments` table (auto-created by the DDL executescript).
- **`import_records`** (full dotted module + names; CI-3's precondition): `_import_records` — one
  row per imported name, FULL dotted `module`, `name`/`asname`/`level`. The legacy root-only
  `imports` table is UNCHANGED (existing consumers untouched). New `import_records` table.
- **§4 header correction**: the "Deliberately NOT here… stays on the ops side until ratified"
  paragraph rewritten to cite ratification (dn-code-ingest-pipeline, 2026-07-21; warrant 0146) and
  name the CI-1 captures — banner-on-correction, not silent.
- **Backfill**: `backfill_code_corpus(db, repo)` mirrors `backfill_docstrings` exactly — re-parses
  each unique blob once (cached), fills end_lineno + comments + import_records for pre-CI-1 rows,
  mark-guarded by `_code_corpus_backfilled` (idempotent, self-healing on sync).

**Tests** (`tests/unit/test_code_corpus_ledger.py`, 9 passing): span capture; comment innermost-
symbol attribution; full import records (dotted preserved, legacy `imports` set unchanged); the
L0a span+shell PARTITION check (F-CI2 precursor — every line in exactly one bucket); snapshot
roundtrip; **the additivity falsifier** (`_pre_existing_checksum` over files/symbols/imports pre-
existing columns identical before/after a backfill on a regressed-to-pre-CI-1 ledger); and the
acceptance measurement — comment capture reproduces an INDEPENDENT tokenize recount over the pinned
main-package set (self-consistent, floor >3000; HEAD measures 3360/254 vs audited 3318/247 @625a058).
`ruff` + targeted `mypy` clean. **Touches stored data:** the real ledger is absent in this worktree
(`data/` empty); all captures are additive + backfill is mark-guarded, so a live ledger heals on
next sync with zero row mutation (proven by the additivity test on a copy-shaped in-test ledger).

### Scope widen received — Items 2–4 unblocked

Committed Item 1 (dbec242 code, e4f4b93 docs), merged main → picked up plan.md `dcd79c6`
(write_scope now carries `core/kernel/provenance.py`; scope-guard rc=0 confirmed). finding-0156
orchestrator-resolved.

### Item 2 — three chunkers + the CODE mint + the layer column — DONE

- **`Provenance.CODE`** (`core/kernel/provenance.py`): the seventh class, "builder-produced reality
  read from the repo instrument," ∉ MIRROR_READABLE, structurally minted, dreamable-by-grant-only.
  Docstring spectrum + enum comment updated (§4 reconciliation).
- **`core/ingest/code_corpus.py`** (new, outer ring): PURE derivation `derive_code_chunks(path,
  source)` — parses ONCE with φ_code's `parse_source` (same interpreter, not a second parser), so
  chunks are bit-identically re-derivable (F-CI2):
  - **L0a** (`code_ast`): innermost-owner line partition (nested defs own their lines; parent = its
    shell; module shell = the rest) → **every source line in exactly one L0a chunk** (F-CI2
    byte-cover, tested). Header `# {path}:{qualname}{signature}`. Oversized slices split via
    `chunk_text` (honoring the note), byte-cover asserted on the ownership partition (chunk_text is
    lossy, so cover is a line-ownership property, independent of the split — recorded).
  - **L0b** (`code_text`): `chunk_text` over RAW source (the ONE window machinery, NOT
    `derive_chunks` — its Logseq strip must not run on code; tested `== chunk_text(src)`). Line
    coords located best-effort (feeds only the [INFERENCE]-graded M-C8 join — right cost).
  - **L1** (`codedoc`): module + symbol docstrings + comments in source order, coordinate headers,
    `chunk_text`; lands in the note neighbourhood. File-grain coords (windows straddle symbols).
  - **`code_rows()`**: hardcodes `Provenance.CODE` — **NO provenance parameter anywhere** (F-CI1,
    asserted by API introspection). id = `(path, layer, content_hash)`; digest = git blob sha
    (group-by-digest → file = source object, UNCHANGED). Reuses embed/add BELOW the parameter.
- **Vectorstore `layer` + fiber columns** (`core/stores/vectorstore.py`): schema gains
  `layer/qualname/line_start/line_end`. `add()` DEFAULTS them on any legacy 8-key row (transparent
  to every existing caller — the many out-of-scope test row builders keep working), and
  `_migrate_layer_if_needed` reset+rebuilds an old store PRESERVING every note row bit-identically
  (text/digest/vector; count intact — proven by the migration test). `_chunk_row` stamps `prose`.
  **Touches stored data:** reset+rebuild is row-preserving + vector-preserving (no re-embed), so
  `core.ingest.verify` still passes; the real 28-row store migrates in place on first add.

### Item 3 — incremental sync + the scheduler-gated seed — DONE

- **`CodeCorpusSync.sync()`** (`code_corpus.py`): blob-sha-keyed incremental — the store's own set
  of CODE `(source_path, digest)` pairs IS the D-fiber state, so an unchanged file re-embeds
  NOTHING (tested: second sync → `embedded_rows=0`), a changed blob replaces only that path
  (tested), a vanished file is tombstoned (tested). `seed()` = `sync()` on an empty store. HEAD-only
  (PD-B). Embedding runs LOCALLY (no network egress, #1).
- **`scheduler/code_sync.py`**: `code_sync` KIND + handler + `enqueue_code_sync`, mirroring
  vault_sync exactly. Model-less re chat tiers → added to `router._PINNED_KINDS` (pinned, `ensure_
  tier` no-op, never evicts) + BACKGROUND priority (yields to slot-2 heavyweights — the scheduler
  refusal seam; the memory ceiling #8 is enforced by the loader on each embed, as for vault_sync).
- **`config/defaults.toml`** `[code_ingest]` block, `enabled=false` (inert like [exhaust] until a
  schema'd loader consumer lands — the loader is out of scope). NOT auto-wired into launcher
  housekeeping (launcher out of scope) — off-by-default by construction.
- **M-C1 (one-file timing):** the real embed timing PARKS (no live daemon/Ollama in the worktree;
  §7 Item 4 is an idle-window, owner-visible run). Derive-path timing is sub-ms/file (pure parse).

### Item 4 — F-CI5 isolation ratchet DONE; the live seed run PARKED

- **`tests/integration/test_code_vector_isolation.py`** (permanent): F-CI1 (CODE never surfaces via
  the MIRROR_READABLE-default `semantic_search`, and `MirrorView.project` holds zero code rows —
  both tested; the opt-in `provenances={CODE}` DOES reach code) + **F-CI5** (the mirror-path results
  — default search + MirrorView rows — are BIT-IDENTICAL with code rows present vs absent) + the
  layer migration preservation test.
- **PARKED (re-entry: run on the live daemon at idle, owner-visible, per §7 Item 4 / §10):** the
  actual seed RUN over the real repo, and the M-C2 chunk census / M-C8 L0a↔L0b mismatch readings —
  these need Ollama + the real vector store + an idle window and are inherently owner-visible
  execution, not a worktree/CI action. The lane + all instruments are BUILT and green; only the
  live execution + its numeric readings park. Chunk-volume estimate ~7k (±2×) stands from the note.

### The full attestable-green gate (this worktree)

- `uv run ruff check .` → **All checks passed!**
- `uv run mypy core agents eval ops scheduler scripts` → **Success: no issues found in 252 source files**
- `uv run mypy` (argless) tail → **Found 69 errors in 20 files (checked 526 source files)** — == baseline 69 ✓
- `uv run python -m ops.type_gate` → Tier-2 membership OK; bare-ignore scan OK
- `uv run pytest -q -m 'not live and not podman and not needs_vault and not needs_restic' --deselect
  'tests/unit/test_core_self_containment.py::test_core_imports_nothing_outside_core' --cov` →
  **1 failed, 1880 passed, 11 skipped, 21 deselected in 42.33s**. The single failure is
  `test_interpreter_versions.py::test_source_hash_matches_the_pin[phi_code]` — an OUT-OF-SCOPE
  φ_code fingerprint pin that my in-scope Item 1 edit to `ops/code_snapshot.py` flips. It is a
  DECLARED REFACTOR re-pin (same version 1.0.0; observation projection byte-identical — code_sensor
  reads none of the new ledger fields), escalated to the orchestrator with the exact new sha
  (`517f957…c3c558`). After that one-line re-pin the gate is fully green. No other red.

## Follow-through

- **Built?** Yes — Items 1–4 complete: the ledger captures (spans/comments/import_records +
  backfill), `Provenance.CODE`, the three-layer chunkers + structural CODE mint (F-CI1), the
  vectorstore `layer`+fiber columns with a row/vector-preserving migration, blob-sha incremental
  sync + the `code_sync` scheduler KIND + the `[code_ingest]` config, and the F-CI1/F-CI5 isolation
  ratchets. 37 new tests, all green (bp-092 legs).
- **Wired/delivered (or why dormant)?** The lane is a callable ingest entry point + a registered
  scheduler KIND (pinned/BACKGROUND, mirrors vault_sync). DORMANT BY DESIGN: `[code_ingest].enabled
  = false` and NOT auto-enqueued into `build_components` housekeeping (launcher.py is out of this
  plan's write_scope; wiring it in is a deliberate, owner-visible later step — the "seed is one
  owner-visible run" ruling, note §2.7). No daemon change, no restart.
- **Does a consumer use it?** Not yet in production — the seed has not run (parked: live daemon +
  Ollama + idle window, owner-visible). In tests, `CodeCorpusSync` + `semantic_search
  (provenances={CODE})` are the consumers; group-by-digest works on code digests unchanged. The
  ledger `import_records` are minted here for CI-3 (bp-094) to consume.
- **Track state (code-ingest)?** CI-1 code + instruments COMPLETE and green (pending the one
  out-of-scope re-pin). CI-1's live seed run + M-C1/M-C2/M-C8 readings PARK for an owner-visible
  idle run. CI-2 (retrieval proof M-C3/M-C4/M-C5 + node-keyed C reader) and CI-3 (L2b resolver + AST
  edges — its import-record precondition is now minted) remain future plans. CI-4 conditional.
- **Opened a new track/finding?** finding-0156 (spec-fidelity → orchestrator; the K1/K3 write_scope
  relocation drift) — orchestrator-resolved by the write_scope widen. No new track. The φ_code pin
  re-pin is a routine declared-refactor escalation (message to orchestrator), not a finding.

**Ready to deskcheck** — bp-092/CI-1 (the three-layer code embed lane). DONE ≠ sealed: the live
seed run + census readings are the deskcheck's natural subject (park them for an owner-visible idle
run). Status left `ready` for the orchestrator to seal after the φ_code re-pin lands the gate green.
