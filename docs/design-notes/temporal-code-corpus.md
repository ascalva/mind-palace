---
type: design-note
id: dn-temporal-code-corpus
track: code-ingest
status: ratified            # draft → ratified → superseded.  draft→ratified is an OWNER-ONLY hand edit.
created: 2026-07-22
updated: 2026-07-22
links:
  - docs/findings/finding-0163.md                      # the warrant — PD-B reversed, owner-ruled
  - docs/findings/finding-0151.md                      # the integrator program this note founds
  - docs/findings/finding-0146.md                      # code is a first-class semantic source
  - docs/findings/finding-0111.md                      # commit-diff capture named cheap + uncaptured
  - docs/design-notes/code-ingest-pipeline.md          # partially superseded (see §6)
supersedes: dn-code-ingest-pipeline §2.7 (delete+replace incremental contract), §548-1 / PD-B (HEAD-only, no historical backfill)   # PARTIAL — the rest of that note stands
warrant: docs/findings/finding-0163.md
---

# Design note — the temporal code corpus

> **⚑ Config surface superseded (owner ruling 2026-07-28).** The TOML section this note names
> moved when the ingestion agents were split one-section-per-agent: **`[code_ingest]` →
> `[ingestion.code]`**, read in Python as `cfg.ingestion.code`. Each agent now carries its own
> `enabled` lever, gating *every* path it uses — watcher, housekeeping, and startup catch-up.
> `integrate` was moved out of the transcript section entirely: it derives from already-ingested
> material rather than ingesting, so it is its own agent type with its own `[integrate]` section.
> Everything below about the *design* stands; only the config names have moved. See
> `config/defaults.toml` → the INGESTION AGENTS banner.

> The code corpus is not a snapshot; it is a graph that evolves over time. Every code version is a
> semantic node; every code change is a supersession edge; the integrator's causal chain
> (conversation → commit → code change) terminates ON those edges. HEAD-only embedding made that
> chain impossible — this note corrects it.

## 0. Provenance & mode

Fable design pass (owner re-tiered, 2026-07-22, session-43), warrant **finding-0163** (owner ruling:
PD-B reversed). Grounding was done live in the ruling session — the version counts, the sync
behavior, and the temporal-machinery seams below were read from the running system, not inferred.
The owner directed design + graduation in one motion; blessing gates unchanged (this note ratifies
by owner hand; the plan flips ready by owner hand).

## 1. Objective

Make the semantic code corpus **version-complete and temporal**:

1. Every historical code version — each distinct `(path, blob_sha)` in the snapshots ledger — is
   embedded as a first-class semantic node (**1,542 versions / 977 commits** measured at HEAD
   `933dc45`; ~6× the ~257-file HEAD seed — trivial cost, finding-0163).
2. The incremental sync **retains** superseded versions instead of deleting them (keep-and-link),
   so the corpus accumulates history from now on instead of destroying it.
3. **Supersession edges** `blob(v) → blob(v+1)` are derivable and traversable, with both endpoints
   resolvable to embedded nodes — realized from the ledger via commit-diff capture + the
   already-built temporal poset machinery.
4. Default retrieval stays **current-view** (searching code must not surface stale versions
   unasked); history is an explicit opt-in.

### 1.2 Out of scope (non-goals — read deliberately at ratification)

- **The integrator's C-side densification** (turn→commit anchoring beyond the existing 78
  commit-anchored edges; blob-tagged writes; the full ComposedGraph) — that remains finding-0151's
  design pass. This note builds the **D-side substrate** that pass composes against. `[ESTABLISHED —
  finding-0151 ruling: a separate proper design pass]`
- **Temporalizing the NOTE corpus** (version retention + supersession for notes). Open question,
  explicitly parked to the integrator pass (finding-0163 §open-questions). `[INFERENCE — code-first
  is the ruled scope; notes were not named in the ruling]`
- **Rename tracking.** A renamed file starts a new path-chain (delete+add), as git defaults. PD-1.
- **Non-Python surfaces; any second embedder; pruning/cold-tier policy** (PD-2) — unchanged parks.
- **No change to the temporal machinery internals** — `poset_from_chains` / `supersession_poset`
  are consumed as-is; if they need modification, that is a stop-and-raise finding, not a drive-by.

## 2. Decisions

### D1 — Embed history: every ledger version is a node (reverses PD-B)

The backfill unit is the ledger's **distinct `(path, blob_sha)`** set (not commits × files — the
403,482 file-rows are overwhelmingly unchanged repeats; the distinct-version count is 1,542).
Each version embeds through the **existing** per-version path: φ_code's `parse_source` → the three
layers (L0a `code_ast` / L0b `code_text` / L1 `codedoc`) → `code_rows` → store. `digest` = blob sha
already (content-addressed), so **backfill is idempotent by construction** — the HEAD versions
already embedded are skipped at zero cost, and re-running the backfill embeds nothing twice.
A blob that fails AST-parse (historical syntax casualty) degrades to L0b windows only, counted in
the report — never a hard stop. `[DERIVED — code_corpus.py's existing digest-keyed discipline]`

### D2 — Keep-and-link: the sync retains superseded versions (reverses the §2.7 delete contract)

Today `CodeCorpusSync.sync()` treats the store's `(source_path, digest)` set as the D-fiber state:
a changed blob **replaces** the path's projection (old rows deleted); a vanished path's rows are
**removed** (`core/ingest/code_corpus.py:238-239`). That actively destroys supersession endpoints
as code evolves — the opposite of an evolving graph. New contract:

- The vector store schema gains a **`current: bool`** column — additive migration, exactly the
  `_migrate_layer_if_needed` precedent (`core/stores/vectorstore.py`): old stores migrate in place,
  rows and vectors intact. Migration default `current=true` is CORRECT only while the store holds
  HEAD-only code rows — therefore the migration lands **before** the backfill runs (build order
  pins this).
- On a changed blob: the old version's rows flip `current=false` (never deleted); the new version's
  rows land `current=true`. On a vanished path: rows flip `current=false`. Note rows (`prose`) are
  untouched — `current` semantics apply to code rows; note rows carry `current=true` as the
  vacuous default.
- **Code does not settle** whether the LanceDB shim exposes an in-place update; if it does not, the
  pinned fallback is read-rows → delete → re-add identical rows with `current=false` (vectors
  carried through the move; per-path row counts are tiny). Builder reads and mirrors; a third
  approach is a finding.

### D3 — Retrieval default: current-view; history is opt-in

Default semantic search filters `current == true` — flat retrieval behavior for every existing
consumer is **unchanged** (stale code never surfaces unasked). A single opt-in parameter
(`include_superseded=True` on the search surface) exposes history to temporal consumers. The
`sourceset` group-by-digest relation is unaffected: a historical version is a distinct digest and
therefore a distinct source object — exactly the right identity. `[DERIVED]`

### D4 — Commit-diff capture + the lineage reader (discharges finding-0111's gap)

Supersession chains are **derived from the ledger, never re-minted** (that half of
dn-code-ingest-pipeline §436-447 stands — no second source of truth, no new edge store). What is
missing is the *cheap, uncaptured* diff: finding-0111 named it. New module **`ops/code_lineage.py`**
(ops-side — core imports nothing outside core; the ledger is φ_code's, ops-owned):

- **`commit_diffs` table** in the snapshots db (additive, `open_snapshot_db` pattern):
  `(commit_sha, path, old_blob, new_blob)` per changed file, captured via `git diff-tree`;
  idempotent per commit; one catch-up pass covers all 977 historical commits (cheap).
- **Chains reader**: per-path `blob(v0) → blob(v1) → …` chains assembled from `commit_diffs`
  (ordered by the commit topology the ledger already records), handed as plain data to the
  store-free poset core `poset_from_chains` (`core/temporal/boundary.py:99-112`) — "a reader
  wiring, no new machinery," exactly as the ratified note promised, now with its consumer arrived.
- **`ops/code_snapshot.py` and `ops/code_sensor.py` are NOT touched** (deliberately out of
  write_scope): `commit_diffs` is new D-side data, not a reinterpretation of any observation
  stream, so the φ_code interpreter-version pin does not flip. `[DERIVED — the pin covers the
  sensor/snapshot source hashes; a sibling module does not alter them]`

### D5 — The realized supersession edge (the integrator's landing surface)

The semantic supersession edge is the pair `(old_blob, new_blob)` from `commit_diffs` **with both
endpoints resolvable by digest in the vector store** (D1/D2 guarantee resolution). The causal path
the owner named — *conversation → commit → code change* — becomes traversable today at the
anchored C-edges (78 `pair_cut_sha` edges), and densifies when finding-0151's pass lands, with no
further store-model change: the substrate is complete after this note. `[DERIVED]`

### D6 — The embedder axis is unchanged — and now covers history

The embedder-version pin stays config-level with reset + re-embed-from-raw on change
(dn-code-ingest-pipeline A7, standing). A future embedder bump re-embeds **all retained versions**,
not just HEAD — cost grows with history but remains thousands of chunks, and the two D-axes
(content changed vs worldview changed) stay unconflated. `[ESTABLISHED]`

## 3. Wiring & enablement (required §)

**How it wires:** keep-and-link is the sync's semantics, not a feature — it is live for every
`code_sync` run at the deploy that carries this build. The backfill wires twice: (a) **startup
catch-up** — `_catchup()` enqueues one backfill job when the store's distinct code-digest count is
below the ledger's distinct-version count (a cheap incompleteness probe; the job self-noops once
complete), and (b) **`palace code-backfill`** — the deliberate immediate trigger, mirroring
`code-seed`'s durable-queue insert. Diff capture rides the same backfill/catch-up job (idempotent
per commit) and thereafter the incremental sync cadence.

**What it takes to flip on: nothing.** No flag. Per the owner's rulings (finding-0159: the switch
is part of finishing; finding-0161: gated-off is a not-yet, defaults are Ouroboros's instantiation
values), a store-model correction ships ON — it is the lane's meaning, not an option. Opt-out does
not exist; turning "history" off would re-create the defect this note removes.

## 4. Risks & falsifiers

- **Shim update capability** (D2) — falsifier: the fallback rewrite loses vectors or ids; test
  pins row-count + vector-identity across a supersession flip.
- **Backfill parse casualties** — falsifier: a hard stop on one bad blob; must degrade per-blob.
- **Retrieval regression** — falsifier: any default query returns a `current=false` row.
- **Store growth** — linear in versions (~6× today, grows at commit rate). Accepted; pruning is
  PD-2 with a named re-entry.
- **Memory ceiling** — backfill is BACKGROUND on the pinned tier under the loader's per-embed
  ceiling, identical to the seed that just ran clean.

## 5. Parked decisions

| PD | Decision | Default recorded | Re-entry condition |
|---|---|---|---|
| PD-1 | rename tracking | rename = delete+add (per-path chains) | a rename-supersession consumer is exhibited |
| PD-2 | history pruning / cold tier | keep everything | store size or query latency measurably hurts |
| PD-3 | note-corpus temporalization | code-only here | the finding-0151 integrator pass decides scope |
| PD-4 | per-row embedder stamp | config-level pin stands (A7) | a mixed-worldview store is ever legitimate |

## 6. Supersession declaration (for the owner's ratification hand)

This note **partially supersedes `dn-code-ingest-pipeline`**: §2.7's delete+replace incremental
contract → keep-and-link (D2); §548-1 / PD-B (HEAD-only, "no named consumer") → reversed (D1;
the consumer is the causal graph itself, finding-0163). The rest of that note — the three-layer
design, φ_code sole-interpreter, the CODE provenance firewall, A7, blob-sha keying — **stands and
is built upon**. At ratification the owner banners those two clauses in the ratified note (owner
hand; agent-immutable surface).
