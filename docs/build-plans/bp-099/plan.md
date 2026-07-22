---
type: build-plan
id: bp-099
track: code-ingest
status: complete
design_ref:
  - docs/design-notes/temporal-code-corpus.md
contract: builder
write_scope:
  - core/ingest/code_corpus.py
  - core/stores/vectorstore.py
  - ops/code_lineage.py
  - ops/lifecycle/launcher.py
  - scripts/palace.py
  - scheduler/code_sync.py
  - tests/unit/test_code_ingest_wiring.py
  - tests/unit/test_code_corpus*.py
  - tests/unit/test_code_lineage.py
  - tests/unit/test_vectorstore*.py
session_budget: 2
cost:
  estimate:
    model: opus
    tokens: 250k
  actual:
    model: opus            # opus-4-8[1m], single delegated builder, session-43; tier verified (self-report + harness)
    tokens: ~256k          # harness-measured (builder self-estimate ~215k)
    ratio: 1.02            # vs 250k estimate — well-pinned (interfaces inline in §6); Q3/Q5/Q6 resolved by reading, not iterating
    session_delta: one delegated builder session, all 3 items + gates green on the first structural pass
    notes: 1 spec-fidelity finding (0166; renumbered from the builder's 0164 at merge — id collision with main) filed + resolved in-scope; zero new mypy errors; pins byte-untouched
depends_on:
  - bp-092
  - bp-098
parallelizable_with: []
created: 2026-07-22
updated: 2026-07-22  # complete (build session-43)
links:
  - docs/design-notes/temporal-code-corpus.md
  - docs/findings/finding-0163.md
  - docs/findings/finding-0151.md
  - docs/findings/finding-0111.md
re_entry: null
supersedes: null
superseded_by: null
warrant: docs/findings/finding-0163.md
---

# Build Plan — the temporal code corpus (history embedded · keep-and-link · supersession edges)

> Every section below is required; an inapplicable one is `N/A — <reason>`.

## 0. Mode & provenance

Fable design pass → immediate graduation (owner-directed, 2026-07-22 session-43). Design:
`dn-temporal-code-corpus` (draft; owner ratifies alongside this plan's blessing — the owner stated
intent to bless immediately). **Warrant finding-0163** (owner ruling: PD-B reversed — you cannot
add causal edges if the history of the code isn't represented). Grounding was performed live in
the ruling session against the running system; the measured numbers below are from HEAD `933dc45`.

## 1. Objective

The semantic code corpus becomes version-complete and temporal: all ~1,542 historical
`(path, blob_sha)` versions embedded (D1); the incremental sync retains superseded versions with a
`current` flag instead of deleting them (D2); default retrieval stays current-view with an
`include_superseded` opt-in (D3); `commit_diffs` captured from `git diff-tree` into the snapshots
db and per-path supersession chains exposed through `poset_from_chains` (D4) — so the supersession
edge `blob(v)→blob(v+1)` has both endpoints resolvable as embedded nodes (D5).

## 2. Context manifest

Read these, in order, before any work:

1. `docs/findings/finding-0163.md` — the warrant and the four-part corrected design.
2. `docs/design-notes/temporal-code-corpus.md` — D1–D6 + §3 wiring (flag-less, ON at deploy).
3. `core/ingest/code_corpus.py` — the whole module, especially the sync loop and the
   delete+replace state discipline (`:221-285` — "a changed blob replaces that path's projection; a
   vanished path's rows removed"), `_embed_and_land` (`:249`), `code_rows` (`:193-217`),
   `build_code_corpus_sync` (`:287-310`), and the `read_py_blobs`/`list_py_blobs` imports (`:50`).
4. `core/stores/vectorstore.py` — `_schema` (the 13-col shape incl. `layer`),
   `_migrate_layer_if_needed` (the additive-migration precedent to mirror for `current`),
   `reset` (`:72-77`), the search surface (place the `current` filter), and the typedshims lance
   wrapper (`core/typedshims/lancedb.py`) for what update/delete it exposes.
5. `ops/code_snapshot.py` — READ-ONLY (out of write_scope, D4): `open_snapshot_db` (the additive
   table pattern `commit_diffs` mirrors), the `files` table shape (`commit_sha, path, blob_sha`),
   `list_py_blobs` / `read_py_blobs` signatures (backfill reuse), and the snapshots-table commit
   ordering the chains reader sorts by.
6. `core/temporal/boundary.py:99-112` — `poset_from_chains` (store-free; consumes per-path chains
   as plain data; DO NOT MODIFY) and `core/temporal/acquire.py:31` `supersession_poset` for shape.
7. `scheduler/code_sync.py` — the KIND/handler/enqueue pattern `code_backfill` mirrors exactly.
8. `ops/lifecycle/launcher.py` — `build_components` handlers dict + `_housekeeping`/`_catchup`
   (bp-098's `code_sync` wiring is the template); `Launcher.code_seed()` (`:662-687`, the
   durable-queue CLI insert `code_backfill()` mirrors); `scripts/palace.py` dispatch/USAGE.
9. `tests/unit/test_code_ingest_wiring.py` — the offline `build_components` fixture (`_cfg`) to
   extend; bp-098's five tests must stay green.

## 3. Investigation & grounding

- **Q1 — Scale of the backfill?** Measured (2026-07-22, snapshots db): **977 distinct commits,
  1,542 distinct `(path, blob_sha)` versions, 1,472 distinct blob shas**, 403,482 file-rows (the
  repeats). ~6× the ~257-file HEAD seed that just ran clean. `[ESTABLISHED]`
- **Q2 — Is backfill idempotent for free?** Yes: `digest` = blob sha; the sync/seed path is
  digest-keyed and already skips embedded blobs at zero embeds. Backfill reuses that discipline
  over the ledger's version list. HEAD's rows (already landing from the running seed) are skipped.
  `[ESTABLISHED — code_corpus.py:238-245]`
- **Q3 — What exactly deletes today?** The sync loop replaces a changed path's rows and removes a
  vanished path's rows (module doc + sync body). **Code does not settle** the exact delete call
  shape against the lance shim — read it; whether flip-in-place (update) is available or the
  pinned fallback (read rows → delete → re-add with `current=false`, vectors carried) is required
  is the builder's read-and-mirror decision. A third approach is a finding.
- **Q4 — Where does `current` default TRUE matter?** The migration stamps existing rows
  `current=true`; that is correct now because the store holds only HEAD code rows + note rows.
  Item ordering pins migration (Item 1) strictly before backfill (Item 2). Note rows keep the
  vacuous `current=true` forever. `[DERIVED]`
- **Q5 — How do chains get ordered?** `commit_diffs` rows carry `commit_sha`; the ledger's
  snapshots table already records the commit walk (φ_code's capture order). The chains reader
  orders each path's `(old_blob → new_blob)` links into a chain; a fork/merge producing a
  non-linear per-path history collapses to the first-parent order the ledger recorded. **Code does
  not settle** the ledger's exact commit-ordering column — read `ops/code_snapshot.py` and use
  what the snapshots table provides; do not invent a second ordering.
- **Q6 — Does `git diff-tree` capture suffice for 977 commits?** One subprocess per commit at
  catch-up (or `--stdin` batched — builder's call), then one per new commit incrementally. Renames
  appear as delete+add (PD-1, by design). Merge commits: first-parent diff (`-m` NOT used;
  first-parent keeps chains linear, matching Q5). `[DERIVED]`
- **Q7 — Retrofit surface:** bp-098's five wiring tests (offline `build_components`) must stay
  green; `test_vectorstore*.py` may assert the 13-col schema — carried in write_scope; the
  `_migrate_layer_if_needed` tests are the migration-test template to extend for `current`.

**Additional risks:** the running daemon deployed at `1355872` still runs the OLD delete+replace
sync — every commit landed between now and this plan's deploy discards that path's superseded
rows. Acceptable: the backfill re-embeds any version the ledger holds, so nothing is permanently
lost; but land + deploy this promptly (finding-0163 flagged the same).

## 4. Reconciliation

- `core/ingest/code_corpus.py` sync contract — **[banner: supersession]**: delete+replace →
  keep-and-link per dn-temporal-code-corpus D2 (module docstring updated to cite it).
- `core/stores/vectorstore.py` `_schema` — **[cross-ref: extension]**: + `current` (bool),
  migrated additively exactly like `layer` (comment cites this plan).
- `scheduler/code_sync.py` — **[cross-ref: extension]**: + `CODE_BACKFILL_KIND` +
  handler/enqueue, sibling of `code_sync`.
- `ops/lifecycle/launcher.py` / `scripts/palace.py` — **[cross-ref: extension]**: catch-up
  incompleteness probe + `code-backfill` verb, both mirroring bp-098's shapes.
- `ops/code_lineage.py` — new module; the snapshots db gains `commit_diffs` via its own additive
  migration (the `open_snapshot_db` pattern), **without touching** `code_snapshot.py`/
  `code_sensor.py` (the φ_code interpreter pin must not flip — D4).

## 5. Write scope

Per front-matter. **Deliberately OUT:** `ops/code_snapshot.py`, `ops/code_sensor.py` (pin
protection, D4 — read-only context); `core/temporal/**` (consumed as-is; needing to modify it is
a stop-and-raise); `eval/**`; the golden set; `config/defaults.toml` (no flag exists — §3 of the
note: flag-less by design).

## 6. Interfaces pinned inline

**Schema + migration (mirror `layer`):**
```
_schema: + ("current", pa.bool_())          # code rows: is this blob the path's HEAD projection?
_NOTE_LAYER_DEFAULTS: + "current": True     # note rows: vacuous true, forever
_migrate_current_if_needed(...)             # additive, in-place, rows+vectors preserved
search(..., include_superseded: bool = False)   # default filters current == True
```

**Sync (keep-and-link, D2):**
```
# changed blob:  old rows -> current=false (flip in place, or pinned fallback re-add); new rows land current=true
# vanished path: rows -> current=false
# NEVER a row deletion of a superseded version; report gains counts: superseded=, retained=
```

**Backfill (reuses the existing per-version embed path):**
```
class CodeCorpusSync:
    def backfill(self, versions: Sequence[tuple[str, str]]) -> CodeSyncReport   # (path, blob_sha)
# versions from ops/code_lineage.ledger_versions(db) -> the 1,542 distinct pairs
# read blob: reuse read_py_blobs / git cat-file (read+mirror ops/code_snapshot.py's accessor)
# parse-fail blob -> L0b-only + counted; embedded rows land current = (blob is path's HEAD blob)
```

**Lineage (new `ops/code_lineage.py`):**
```
def capture_commit_diffs(db, repo, commits) -> int      # git diff-tree, first-parent; idempotent per commit
# table commit_diffs(commit_sha TEXT, path TEXT, old_blob TEXT, new_blob TEXT)  [additive migration]
def ledger_versions(db) -> list[tuple[str, str]]        # distinct (path, blob_sha) from files
def supersession_chains(db) -> dict[str, list[str]]     # path -> [blob v0, v1, ...] (ledger order)
# chains feed core.temporal.boundary.poset_from_chains AS-IS (plain data in; core unmodified)
```

**Scheduler + wiring (mirror bp-098 exactly):**
```
CODE_BACKFILL_KIND = "code_backfill"        # scheduler/code_sync.py sibling; BACKGROUND, pinned tier
# launcher: handlers[CODE_BACKFILL_KIND] = code_backfill_handler(build_code_corpus_sync(cfg), <lineage>)
# _catchup(): if store distinct code digests < ledger distinct versions: enqueue_code_backfill(...)
# palace.py: "code-backfill" -> launcher.code_backfill()   (durable-queue insert, code_seed's shape)
```

## 7. Items

### Item 1 — `current` column + keep-and-link sync + current-view retrieval
- **Objective:** D2 + D3 — superseded versions are retained and flagged; default search is
  current-only; `include_superseded` opts in.
- **Files:** `core/stores/vectorstore.py`, `core/ingest/code_corpus.py`, `tests/unit/
  test_vectorstore*.py`, `tests/unit/test_code_corpus*.py`.
- **Acceptance test:** simulate a blob change through `sync()` against a temp store: the old
  version's rows survive with `current=false` (same ids, vectors intact), the new version lands
  `current=true`; a vanished path flips to `current=false`; default `search()` returns no
  `current=false` row; `include_superseded=True` returns both versions. Old-store migration test
  mirrors the `layer` migration test.
- **Falsifier:** any superseded row is deleted; or a default query surfaces a superseded row; or
  the migration touches vectors/ids.
- **Invariant(s):** note rows untouched (vacuous `current=true`); digest stays the blob sha;
  group-by-digest (`sourceset`) semantics unchanged; the memory ceiling untouched.
- **Touches stored data?** Yes — additive migration + flag flips (never deletes content rows).
  **Parallelizable?** No. **Depends on:** none.

### Item 2 — the history backfill (engine + KIND + catch-up + CLI)
- **Objective:** D1 + §3 wiring — all ledger versions embedded; auto-catch-up when incomplete;
  `palace code-backfill` as the deliberate trigger.
- **Files:** `core/ingest/code_corpus.py` (`backfill`), `ops/code_lineage.py`
  (`ledger_versions`), `scheduler/code_sync.py` (KIND/handler/enqueue), `ops/lifecycle/
  launcher.py` (handler + catch-up probe + `code_backfill()`), `scripts/palace.py`,
  `tests/unit/test_code_ingest_wiring.py`.
- **Acceptance test:** against a temp repo/ledger fixture with ≥2 versions of one path: backfill
  embeds both, older lands `current=false`, HEAD version `current=true`; re-run backfills zero
  (idempotent); a parse-fail blob degrades to L0b-only and is counted; `build_components`
  registers `CODE_BACKFILL_KIND`; the catch-up probe enqueues exactly one job iff incomplete;
  `palace.py --help` lists `code-backfill`; `code_backfill()` inserts one job (bp-098's test
  shape).
- **Falsifier:** backfill re-embeds already-present digests (cost blowup); or marks a HEAD blob
  `current=false`; or the catch-up probe enqueues when complete (loop).
- **Invariant(s):** BACKGROUND priority on the pinned tier; single-writer (CLI inserts a job,
  never writes the store); per-embed memory ceiling (loader-enforced, unchanged).
- **Touches stored data?** Yes (adds embeddings; never deletes). **Parallelizable?** No.
  **Depends on:** Item 1.

### Item 3 — commit-diff capture + supersession chains (the edges)
- **Objective:** D4 + D5 — `commit_diffs` captured for all 977 commits + incrementally; per-path
  chains feed `poset_from_chains`; one end-to-end assertion realizes a semantic supersession edge.
- **Files:** `ops/code_lineage.py` (`capture_commit_diffs`, `supersession_chains`),
  `scheduler/code_sync.py` or the backfill handler (diff capture rides the backfill job + sync
  cadence), `tests/unit/test_code_lineage.py`.
- **Acceptance test:** on a temp repo fixture (3 commits, one file evolving, one rename, one
  merge): `capture_commit_diffs` is idempotent per commit; rename appears as delete+add (PD-1);
  merge follows first-parent; `supersession_chains` returns the linear chain;
  `poset_from_chains(chains)` accepts it unmodified (import from `core.temporal.boundary` — no
  core edit); and the composed assertion: for a `commit_diffs` row, BOTH `old_blob` and `new_blob`
  resolve to embedded rows in the Item-2 store — the realized edge of D5.
- **Falsifier:** diff capture reinterprets/duplicates ledger truth (a second source of truth); or
  the φ_code interpreter-version pin flips (proof: `ops/code_snapshot.py`/`code_sensor.py`
  byte-untouched); or `poset_from_chains` needed modification (stop-and-raise instead).
- **Invariant(s):** ledger remains the sole structural source; `core/temporal/**` unmodified;
  chains are plain data into core (self-containment preserved).
- **Touches stored data?** Yes — the snapshots db gains `commit_diffs` (additive).
  **Parallelizable?** With Item 2 after Item 1 (disjoint files except the handler seam — builder
  sequences; not worth two sessions of ceremony). **Depends on:** Item 1 (for the composed
  assertion), Item 2's `ledger_versions` helper (shared module).

## 8. Math carried explicitly

Per-path history is a **chain** (total order) `v₀ < v₁ < … < vₙ` under first-parent commit order;
the corpus-wide supersession structure is the **disjoint union of chains** (a forest of total
orders) — precisely the input contract of `poset_from_chains`, whose covering relations are the
supersession edges `vᵢ → vᵢ₊₁`. Edge count invariant per path: `|edges| = |versions| − 1`;
corpus-wide: `Σ_p (|versions_p| − 1)` — the Item-3 test asserts it on the fixture. Renames break
chain identity by construction (PD-1): the poset stays a forest, never a DAG, until a
rename-tracking consumer reopens PD-1.

## 9. Non-goals

The integrator's C-side densification (finding-0151's Fable pass — this plan builds its D-side
substrate only). Note-corpus temporalization (PD-3). Rename tracking (PD-1). Pruning/cold tier
(PD-2). Any `core/temporal/**` modification. Any change to φ_code / the observation plane / the
interpreter-version pin. Any new flag (§3: flag-less by design). Any second embedder.

## 10. Stop-and-raise conditions

The lance shim supports neither update nor a loss-less delete+re-add (vectors unreadable) — the
store model needs an owner decision. `poset_from_chains` cannot consume the chains as-is (its
contract differs from the note's reading) — do not modify core/temporal; raise. The ledger lacks a
usable commit ordering (Q5 fails) — raise, do not invent one. Any pressure to prune/delete history.

## 11. Parked decisions

Inherited from the note verbatim: PD-1 renames (delete+add), PD-2 pruning (keep everything),
PD-3 notes (code-only), PD-4 per-row embedder stamp (config pin stands). No new parks minted here.

## 12. Dependency & ordering summary

Items 1 → 2 → 3 (schema/retention before backfill lands historical rows; the composed Item-3
assertion needs Items 1+2). `depends_on: bp-092` (the lane), `bp-098` (the wiring pattern +
enable path). Not parallel with other plans (owns the code lane end-to-end). After this plan the
temporal substrate is COMPLETE for finding-0151's integrator pass: every code version is a node,
every change is a resolvable edge, and the causal chain has a place to land. Deploy promptly —
until deployed, the live daemon's old sync still discards superseded rows (recoverable via
backfill, but why bleed).
