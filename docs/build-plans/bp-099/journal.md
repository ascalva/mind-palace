# Journal — bp-099 (the temporal code corpus)

> Alive while the plan is proposed/in-progress; sealed on completion.

## 2026-07-22 — MINTED (Fable design pass → immediate graduation, session-43)

- **State:** `proposed`. Owner-directed one-motion design+graduation ("create the design and
  immediately create the build plan — the design is already there; I will bless, and we build
  immediately"). Design: `dn-temporal-code-corpus` (draft, ratifies at the same blessing sitting).
  **Warrant finding-0163** — owner ruling: PD-B reversed. *"You can't add causal edges if the
  history of the code isn't represented."* The product is a graph that evolves over time;
  HEAD-only embedding + delete-on-change made the integrator's causal chain
  (conversation → commit → code-change-as-supersession-edge) structurally impossible.
- **Grounding done at graduation** (live reads, session-43): the backfill scale is **1,542
  distinct (path, blob_sha) versions / 977 commits** (~6× the HEAD seed that ran clean today);
  the current sync **deletes** superseded rows (`code_corpus.py:238-239` — the load-bearing
  defect); `_migrate_layer_if_needed` is the additive-migration precedent for the `current`
  column; `poset_from_chains` (`core/temporal/boundary.py:99-112`) is store-free and consumed
  as-is; `commit_diffs` capture discharges finding-0111's "cheap, uncaptured" gap **without
  touching** `code_snapshot.py`/`code_sensor.py` (φ_code pin protected by keeping them out of
  write_scope). Three code-does-not-settle items flagged in §3 (Q3 shim update shape, Q5 ledger
  commit ordering, Q6 batching) — builder reads + mirrors, never infers.
- **Scope discipline:** flag-less by design (§3 of the note — finding-0159/0161 lineage: a
  store-model correction ships ON; an off-switch would re-create the defect). The C-side
  densification stays finding-0151's separate Fable pass; this plan builds the D-side substrate
  it composes against.
- **Next action (on owner bless → ready):** `/build bp-099`; Items 1→2→3 (retention schema →
  history backfill → lineage edges). Deploy promptly after seal — the live daemon's old sync
  discards superseded rows until then (recoverable via backfill; still, don't bleed).
- **Blocking:** none. Awaiting `dn-temporal-code-corpus` draft→ratified + bp-099 proposed→ready
  (both owner-only, by hand; `palace bless bp-099` for the plan).

## 2026-07-22 — BUILD session-43: setup + Item 1 CLOSED

- **Setup:** active-plan pointer set; status flipped proposed→in-progress (plan on disk was
  `proposed`, not `ready` as the launch brief said — the bless commit landed for bp-098, not
  bp-099; going to in-progress is not a blessing gate, so proceeding). Read manifest in order:
  finding-0163, dn-temporal-code-corpus, code_corpus.py, vectorstore.py, code_snapshot.py (RO),
  boundary.py (actual path `core/kernel/temporal/boundary.py`, not the plan's `core/temporal/…`),
  typedshims/lancedb.py, acquire.py, code_sync.py, launcher.py, palace.py, the wiring tests.
- **Q3 resolved by reading the shim (`core/typedshims/lancedb.py`):** the LanceDB `VectorTable`
  Protocol exposes NO in-place `update` — only add / delete / to_arrow / search. So keep-and-link
  uses the pinned fallback (read → delete-whole-path → re-add flipped), the `relabel_provenance`
  idiom. Implemented as `VectorStore.supersede_source()` — deletes the WHOLE path then re-lands
  every version with `current=false` (the still-current ones flipped), which sidesteps the id
  collision a version-scoped delete would hit (unchanged chunks keep their content-addressed id
  across versions, so ids are no longer unique once history is retained). Vectors carried through.
- **Item 1 built:**
  - `vectorstore.py`: `+ ("current", pa.bool_())` in `_schema`; `+ "current": True` in
    `_NOTE_LAYER_DEFAULTS`; `_migrate_current_if_needed` (exact `_migrate_layer_if_needed` mirror,
    runs after it in `add()`); `supersede_source()`; `search(..., include_superseded=False)`
    default-filters `current = true`.
  - `code_corpus.py`: `code_rows(..., current=True)`; `_embed_and_land` no longer deletes;
    `sync()` is keep-and-link (changed blob → `supersede_source` then land new current=true;
    vanished path → `supersede_source`, never delete); `CodeSyncReport + superseded_rows/
    parse_failures`; module + class docstrings banner dn-temporal-code-corpus D2.
- **Item 1 acceptance (PASS):** new tests in test_code_corpus.py —
  `test_vanished_file_is_retained_but_marked_superseded` (rows retained, current=false; falsifier:
  never deleted), `test_changed_blob_keeps_and_links_old_version` (both versions retained, same
  ids/vectors), `test_default_search_is_current_view_history_is_opt_in` (D3),
  `test_current_column_additive_migration_preserves_rows` (mirrors the layer migration; vectors/ids
  intact). Rewrote the old `test_deleted_file_is_tombstoned` → keep-and-link semantics.
  `test_code_corpus.py` + `test_code_retrieval.py` + code_mirror + code_vector_isolation: 33 pass.
- **Next:** Item 2 (backfill engine — added `CodeCorpusSync.backfill`; TODO ledger_versions +
  KIND + launcher wiring + palace CLI), Item 3 (commit-diff capture + supersession chains).

## 2026-07-22 — Items 2 & 3 CLOSED · all gates green · SEALED (complete)

- **Item 2 built (history backfill + wiring):**
  - `core/ingest/code_corpus.py`: `CodeCorpusSync.backfill(versions)` — digest-keyed idempotent
    embed of every ledger `(path, blob_sha)`; each lands `current = (blob == HEAD blob)`; parse-fail
    blob → L0b-only + counted (`report.parse_failures`).
  - `ops/code_lineage.py` (NEW): `ledger_versions(db)` (distinct (path,blob) from `files`),
    `ledger_commits(db)` (snapshots rowid order).
  - `scheduler/code_sync.py`: `CODE_BACKFILL_KIND` + `code_backfill_handler` (embeds + captures
    diffs in one job) + `enqueue_code_backfill` — routes via the `code_sync` PINNED plan (router
    `_PINNED_KINDS` is out of write_scope; the backfill is the same species, so it borrows the
    sibling's plan and enqueues under its own KIND — no router edit).
  - `ops/lifecycle/launcher.py`: handler registered unconditionally; `_catchup` incompleteness
    probe (`_code_backfill_incomplete` — compares distinct (path,blob) versions BOTH sides, no
    loop); `Launcher.code_backfill()` durable-queue insert (code_seed's shape).
  - `scripts/palace.py`: `code-backfill` verb + USAGE + docstring.
- **Item 3 built (edges):** `ops/code_lineage.capture_commit_diffs` (first-parent `git diff-tree`,
  explicit `<first_parent> <commit>` — `--first-parent` alone yields nothing on merges/roots;
  `--root` for the root; renames = D+A since `-M` omitted; zero-sha normalized to `''`; idempotent
  per commit via `_commit_diffs_captured` marker; additive `commit_diffs` table via this module's
  own migration — `code_snapshot.py` NOT edited). `supersession_chains(db)` threads per-path blob
  chains in ledger commit order. `poset_from_chains` consumed UNMODIFIED (imported from the REAL
  path `core/kernel/temporal/boundary.py`, not the plan's stale `core/temporal/…`).
- **finding-0166 (spec-fidelity, resolved in-scope):** (1) `poset_from_chains`'s real contract is
  `dict[str,list[int]]` (version_seq) and it re-sorts values — blob-sha chains type-mismatch and
  would lexically reorder; resolved by feeding commit-order POSITIONS (index==version_seq), no core
  edit (stop-and-raise honored). (2) §6's probe shorthand "distinct digests < versions" would loop
  forever (1472<1542 even when complete); resolved by like-to-like (path,blob) comparison. Neither
  changes the note's intent, so no design-note supersession.
- **Acceptance (ALL PASS):** Item 2 — `test_backfill_embeds_history_with_current_flags` (f.py 3
  versions, exactly HEAD current=true, 2 false; broken.py parse-fail counted+embedded; idempotent
  re-run = 0), + wiring tests (KIND registered, catch-up probe =1 incomplete / =0 equal / =0
  disabled, `code_backfill()` = 1 job, `palace --help` lists it). Item 3 —
  `test_capture_commit_diffs_idempotent_and_shapes` (rename D+A, merge first-parent),
  `test_supersession_chains_linear_and_feed_poset` (f.py linear + poset accepts + δ_D²=0 + §8 edge
  invariant), `test_composed_supersession_edge_resolves_to_embedded_nodes` (D5 — a modify row's
  old_blob AND new_blob both resolve to embedded rows).
- **GATES (all green in worktree):** ruff clean · check_imports OK · mypy = 69 (baseline, all in
  pre-existing test files; scripts=0, core=0, my files=0) · type_gate OK · pytest **1919 passed, 11
  skipped, 21 deselected** (bp-098's 5 wiring tests + the 3 provenance-tags tests stay green).
- **Pins verified byte-untouched:** `ops/code_snapshot.py`, `ops/code_sensor.py`,
  `core/kernel/temporal/**`, `core/temporal/**`, `eval/golden/**`, `config/defaults.toml`,
  `CONSTITUTION.md` — none in the diff (φ_code interpreter pin holds; flag-less by design).
- **OWED / next:** DESKCHECK before done (deskcheck-discipline) — show keep-and-link + backfill +
  a resolved supersession edge on the real store. DEPLOY promptly (`palace deploy`, owner-in-loop):
  until deployed, the live daemon's OLD delete+replace sync still discards superseded rows on every
  commit (recoverable via `palace code-backfill`, but bleed). The finding-0151 integrator pass now
  has its complete D-side substrate. Add to docs/DESKCHECK-QUEUE.md (orchestrator).
- **SEALED complete.** Fresh-agent test: plan §6/§7 + this journal + the write-scope files suffice.
