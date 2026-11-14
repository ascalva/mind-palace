---
type: design-note
id: dn-instance-lifecycle
track: deployed-instances
status: draft                  # provenance description, never a gate; the merge is ratification
implementation: built          # part B built §3 to §8; §10 records where the build departs
created: 2026-11-12
updated: 2026-11-14
links:
  - docs/design-notes/dn-temporal-snapshot.md          # §2.2 the inventory this note checks and extends; §2.3 item 7 the reset as it was; §3.2 the landing log (SN-1, merged with #92)
  - core/stores/landings.py                            # the landing log, in the catalog's file: kept whole by the reset, removed with the root by a destroy
  - docs/design-notes/chat-sensor.md                   # CS-1: the transcript retained verbatim before extraction; the chat log a derived layer over raw
  - docs/design-notes/self-sensing.md                  # §2.5: readings rebuilt by re-projection, history ledger-class and kept
  - docs/design-notes/code-observation-projection.md   # §2.4, §2.5: observations and reference edges, corpus-side
  - docs/design-notes/dn-two-phase-ingestion.md        # the vector and the lexical units as derived fields; the drain and the backfill
  - docs/design-notes/dn-palace-lite.md                # `[instance] root`, an instance that embeds nothing, the repository sync
  - docs/design-notes/dn-corpus-instance.md            # the corpus instance, its sources and its one writer
  - docs/design-notes/vector-membership-store.md       # atoms, occupancies, the purge (A3.7)
  - docs/design-notes/dn-embedder-use.md               # the tokenizer's identity and the re-derivation of a stale index
  - docs/design-notes/verdict-authority.md             # the verdict ledger and its applied dispositions
supersedes: null
superseded_by: null
warrant: null
---

# The instance's lifecycle: a reset that rebuilds, a destroy that keeps a cache, the corpus at its own root

> Drafted on the branch `feat/instance-lifecycle`, cut from `origin/main` at `0a5fba27`, and
> rebased onto `8d4dff3d` once pull request #92 had merged (2026-11-12, `ab67880f`), and #89
> after it. Every line cited is a line of the base, `8d4dff3d`, the tree this branch merges onto.
> The claims about code at those lines were read at `0a5fba27` and checked again at the base,
> where these had moved and are cited at their new lines: `perform` and the receipt's timing in
> `core/ingest/ingress.py`, the query log's name in `core/sentence/surface.py`, and in
> `core/ingest/writer.py` the version chains and the two key writes of `Writer.finish` and
> `Writer.link`. This branch changes `writer.py`, and its heal of §5 moves every line after
> `Writer.land` down by 23: at the branch's head the two key writes are at `:475-476` and
> `:489-490`. The landing log, which #92 brought into the base, was read at `8d4dff3d`, and the
> passages about it (§3.6, §4.4 to §4.7, §6.1, §6.2, §6.4, §7, §10 items 16 to 30) name functions
> rather than lines. The note is as built: part B built §3 to §8, and §10 records where the build
> departs from the design, the changes an audit of the build asked for among them, those part C
> made with the landing log in the base, and those two audits of part C asked for. Grades:
> `[ESTABLISHED]` is a fact of the code at the lines cited or of a ratified note; `[DERIVED]` is
> argued here from those; `[INFERENCE]` is a design call with a named falsifier; `[PROPOSED]` is
> a choice this note makes and leaves to the owner (§9).

## 1. Purpose and scope

### 1.1 The owner's decisions

These five bind this note. They are recorded here in this note's words.

1. **A reset loses nothing (2026-11-11).** It clears the derived stores and rebuilds them from the
   raw store; the raw store and every ledger are kept.
2. **A destroy keeps only a cache (2026-11-11).** Destroying an instance removes it, except what
   another instance can take back as a cache.
3. **The corpus lives at its own root (2026-11-11).** The corpus instance's data is at
   `~/.mind-palace/instances/corpus`, outside every checkout. It is a dataset other instances can
   draw on and the fixture for regression and stress runs. It was moved there on 2026-11-11, and
   its old location, `instances/corpus` in the worktree of the corpus's stage 1, is a symbolic link
   to it.
4. **A change replaces what it changes (2026-11-12).** The new reset is the reset: there is no
   switch back to the old behaviour and no old command beside it. Reverting the pull request is
   the rollback.
5. **One definition (2026-11-12).** What a store is and how an operation computes is defined once,
   in the code, and is the same for every instance. What reset and destroy do is not a setting.

### 1.2 What this note decides

1. **Every store an instance writes is in exactly one class (§3):** a ledger, an owner's
   declaration, a derived store with its rebuild, model output, or operational state. The classes
   are one table in the code, and a test fails when a store is opened that the table does not
   name. `[INFERENCE, falsifier LCF-1]`
2. **A reset clears the derived stores and rebuilds them in a fixed order, in its own process,
   under the instance's supervisor lock, and keeps everything else (§4).** The raw store, the
   catalog with the landing log in its file, the attestations, the version chains, the verdicts
   and the queue, which the reset at main removes, are kept. `[DERIVED from decision 1 and §3]` The
   lexical index and the
   authored relation edges, which it leaves today, are rebuilt. `[PROPOSED, D11]`
3. **The chat log is rebuilt from the raw store through a new ledger of retained transcripts
   (§3.4).** Today a kept raw store makes the chat sensor skip every transcript it has seen, so
   nothing would rebuild the chat log. `[ESTABLISHED for the gap; INFERENCE for the ledger,
   falsifier LCF-3]`
4. **Every landing re-derives a stale lexical index before it lands, in the one writer (§5).**
   `[PROPOSED, D12; falsifier LCF-4]`
5. **Destroy applies to a named instance only, is a dry run unless confirmed, and leaves a shared
   cache of raw objects, vectors and downloaded sources at `~/.mind-palace/cache` (§6).** Only the
   open sources' content enters the cache, never a private stratum's, and a purge reaches it.
   `[PROPOSED]`
6. **The corpus instance declares its root, and its stores are read in place, read only, by the
   regression and stress tooling (§7).** `[PROPOSED]`

### 1.3 Out of scope

The landing log itself (`core/stores/landings.py` and the catalog's writing methods, merged with
pull request #92) and the stages after it (dn-temporal-snapshot §12; the algebra of cuts on the
branch `feat/cut-algebra`), which this note reads and does not change; the erasure of what a purge
leaves in the stores it does not reach today (dn-temporal-snapshot §6.1), except the cache this
note adds; backups and migration archives; the curated store's second writer
(`scripts/curate_local.py`), which this note keeps out of the reset (§3.3); and the Keychain items
of a destroyed instance, which §6.2 names and leaves to the owner.

## 2. What exists

### 2.1 The reset at main

`palace reset` (`scripts/palace.py:270-271`) calls `Launcher.reset(confirm=...)`
(`ops/lifecycle/launcher.py:1864-1893`). It refuses while the last run is active and its process
alive (`:1866-1869`), prints its targets, and without `--confirm` removes nothing (`:1877-1881`).
With it, it deletes each target with its `-wal` and `-shm` files (`:1882-1890`) and tells the
operator to export the notes into the vault again and start the daemon, which re-ingests them
(`:1891-1892`). `[ESTABLISHED]`

The targets (`reset_targets`, `:1810-1862`) are the raw store, the vector store, the catalog, the
interpreted artifacts (`derived.sqlite`), the attestations, the queue, the version chains, the
authored supersessions, the verdicts and their dispositions, the code and agent observations, the
reference edges, the chat log, the chat events, the causal edges and the memberships.
`_RESET_GUARD` (`:111-118`) names what an assertion keeps out of the targets: the HashiCorp Vault
storage, the run ledger, the self-modification ledger, the telemetry, the commit ledger
(`code_snapshots.sqlite`), the observation history, the backup staging and the logs.
`[ESTABLISHED]`

So the reset at main is a fresh start: it empties the instance's content and its record of how
the content came to be, and keeps the operational ledgers. Its last purpose stated in the code is
to re-tag every note `authored-solo` on re-ingest (`:1878-1880`). `[ESTABLISHED]`

### 2.2 Where the code contradicts itself

- **Raw is a target, and the chat sensor's design says it is not.** The chat log's module header
  (`core/stores/chatlog.py:41-45`), the chat sensor's (`ops/chat_sensor.py:38-41`) and the
  comment inside `reset_targets` (`launcher.py:1839-1843`) say the chat log is rebuilt by re-ingest
  from the raw store and that raw is never a reset target. Raw is the first target
  (`launcher.py:1815`), and has been since `b8f0d446` (2026-06-29), before the chat sensor existed.
  The raw store holds the only copy of a transcript the CLI has pruned from its directory
  (`ops/chat_sensor.py:12-15`), so the reset at main loses transcripts. `[ESTABLISHED]`
- **With raw kept, nothing rebuilds the chat log either.** The sensor stores each transcript
  first and extracts only when the raw store reports the bytes new (`ops/chat_sensor.py:310-313`).
  After a reset that kept raw, every transcript still on disk is reported unchanged and skipped,
  and a transcript no longer on disk is never read. Nothing records which raw objects are
  transcripts: the sensor writes no catalog row and no attestation (`ops/chat_sensor.py:3-9`).
  `[ESTABLISHED]`
- **The lexical index and the relation edges outlive a reset** (dn-temporal-snapshot §2.3 item 7):
  neither `lexical.sqlite` nor `edges.sqlite` is a target, so after a reset at main both hold rows
  about items that are gone. `[ESTABLISHED]`
- **The authored relation edges are read from the vault's files, not from raw.**
  `RelationDetector.authored` parses `Path(n.source_path)` from disk and skips a note whose file is
  gone (`core/relations.py:123-158`). `[ESTABLISHED]`
- **Re-projection appends to a ledger.** The code sensor's projection of a commit emits an
  attestation (`ops/code_sensor.py:492-500`), so a rebuild through it as written would append to
  the attestation ledger. `[ESTABLISHED]`

### 2.3 A stale lexical index blocks every landing

The lexical index records the tokenizer its units were made by and refuses to land or to score
under another (`core/stores/lexical.py:159-182`, `TokenizerMismatch`). Only the lexical backfill
re-derives it (`core/ingest/derive.py:286-330`), and it runs in the `embed` job
(`scheduler/embed.py:39-48`) and `palace embed` (`launcher.py:1784-1807`). The `embed` job is
enqueued after a landing succeeds (`core/ingest/writer.py:216-219`). So an index left stale by a
tokenizer change refuses the landing whose success would have asked for its repair. This happened
on 2026-11-11, when pull request #90 was deployed: the code instance's index had been made by the
legacy tokenizer, the post-merge hook's `repo-sync` stopped at `LexicalStore.land_many` on every
run, and it was repaired by hand with `palace embed` (2,021 items re-derived in 11 s), after which
a `repo-sync` landed 110 files. `[ESTABLISHED]`

## 3. The inventory

Every store an instance writes, by class. Paths are relative to the instance's data directory
(`cfg.paths.data_dir`; `derived_store.parent` is the same directory under the default paths,
`config/defaults.toml` `[paths]`). This extends dn-temporal-snapshot §2.2, which lists the stores a
sentence can read, with the operational ones, and was checked against the code at `0a5fba27`, and
for the landing log at `8d4dff3d`.

### 3.1 Ledgers: sources of truth, kept

| store | writer | why it is a ledger |
|---|---|---|
| `raw/` (`core/kernel/stores/rawstore.py`) | the writer's derive step (`writer.py:407-412`), the chat sensor (`chat_sensor.py:310`) | the verbatim bytes; every derived store is a function of them; a purge is its one deletion (`rawstore.py:51-61`) |
| `vault_catalog.sqlite` (`core/stores/catalog.py`) | the writer's key (`writer.py:452-453`, `:466-467`), the vault sync, the founding, dialogue and curated landers | the map from path to digest, title, class and identity, with its landing log in the same file (§3.6) |
| the landing log: `landing_chains` and `landings` in `vault_catalog.sqlite` (`core/stores/landings.py`) | the catalog's writing methods, in the transaction of the row each writes, and the genesis at the first open of a catalog with rows and no log (`VaultCatalog._migrate`) | append-only and hash-chained: which digest each path held when; the catalog's rows are its fold (SNP-5). Kept whole with the catalog's file (`LANDING_LOG` in `ops/lifecycle/inventory.py`) |
| `versions.sqlite` (`core/stores/versions.py`) | `Writer.finish` for the place that keeps chains (`writer.py:438-448`) | the version chains of `mirror_authored` |
| `attestations.sqlite` (`core/attestation/store.py`) | the attestor, from the writer and the sensors | append-only, content-addressed; the record of who produced what |
| `chat_retention.sqlite` (new, §3.4) | the chat sensor, at retention | which raw objects are transcripts, in the order they were retained |
| `code_snapshots.sqlite` (`ops/code_snapshot.py`) | the code sensor | the commit ledger; already in `_RESET_GUARD` |
| `observation_history.sqlite` (`core/stores/observation_history.py`) | the code and self sensors, on supersession | superseded generations, whose interpreters no longer exist (self-sensing §2.5); already guarded |
| `reference_edges.sqlite` (`core/stores/reference_edges.py`) | the code sensor's projection | append-only, `INSERT OR IGNORE`; a commit's reading is the union of every projection so far, and the rows carry no extractor version (dn-temporal-snapshot §2.2), so a re-projection under today's extractor would not give the rows back. Kept: decision D3 |
| `query_log.jsonl` (`core/sentence/surface.py:59`) | the sentence surface | the record of what was asked |
| `runs.sqlite`, `selfmod_ledger.sqlite`, `effectors/effects.sqlite` | the launcher, the self-modification gate, the effectors | the system's own runs and acts |

### 3.2 The owner's declarations: never derived, kept

| store | writer |
|---|---|
| `authored_supersessions.sqlite` (`core/stores/authored_supersession.py`) | the owner's declarations, never model output (`authored_supersession.py:150-157`) |
| `verdicts.sqlite` (`core/stores/verdicts.py`) | owner-signed verdicts, verified before they are stored (`verdicts.py:1-9`) |

The reset at main deletes both. A declaration cannot be computed from anything, so neither is a
reset's to clear. `[DERIVED]`

### 3.3 Derived and regenerable: cleared and rebuilt

Each is a function of the ledgers above, computed by code that runs without a model. The rebuild
runs in this order; each step reads only ledgers and the steps before it.

| # | store | rebuilt from | by |
|---|---|---|---|
| 1 | `lexical.sqlite` (`core/stores/lexical.py`) | catalog, raw | `LexicalStore.reset`, then `derive_lexical` (`derive.py:286-330`) |
| 2 | the plane's occupancies and supersession log (`vectors.lance/plane.sqlite`, `core/stores/plane.py`) | catalog, raw, the atom table (§4.2), the cache (§6.5) | a reset of the plane's relations that keeps the atoms, then the drain (`derive.py:183-200`) over every plane class |
| 3 | `code_observations.sqlite` | commit ledger | `CodeSensor.backfill_observations` (`ops/code_sensor.py:827-844`), the attestor off; the reference edges it mints again are already held and are ignored (`reference_edges.py:290`) |
| 4 | `agent_observations.sqlite` | git's first-parent history of the build plans | `SelfSensor.sync` (`ops/self_sensor.py:248-270`), the attestor off |
| 5 | `memberships.sqlite` and the code atoms' occupancy (`core/stores/memberships.py`): replaced by §10 item 1, which keeps it (D14) | commit ledger, git | the code lane's `backfill` over `ledger_versions` (`scheduler/code_sync.py:59-76`), without the job's `capture_commit_diffs`, which appends to the commit ledger |
| 6 | the authored rows of `edges.sqlite` (provenance `authored-solo`) | catalog, raw | `RelationDetector.authored`, changed to parse each active note's raw bytes by its catalog digest instead of its vault file |
| 7 | `chatlog.sqlite` | the retention ledger, raw | a replay of the retention ledger (§3.4) |
| 8 | `chat_events.sqlite` | chat log, raw | `ChatEventProjector.project` (`core/chat_events.py:199-215`) |
| 9 | `causal_edges.sqlite` | chat events, commit ledger | `Integrator.integrate` (`core/integrator.py:97-116`) |
| 10 | `verdict_dispositions.sqlite` | verdicts | `apply_verdict` over every verdict in sequence order (`core/verdict/apply.py:68-77`) |

Then the atoms that no occupancy and no membership holds are dropped, so the atom table holds
exactly what the rebuilt relations name (as built, the plane's occupancies alone, since the
membership store is kept: §10 item 1). Steps 2 and 5 are skipped by an instance that embeds
nothing; steps 3 to 5 by one whose code sensor and code lane are off; steps 7 to 9 by one that
reads no transcripts. A step with nothing to rebuild costs a read of its inputs. As built there is
no step 5 (§10 item 1).

The interpreted rows of `edges.sqlite` stay: they are model output (§3.5). So the reset of that
store deletes the rows of provenance `authored-solo` and keeps the rest, the one derived store
cleared by rows and not by file. `[DERIVED]`

The rebuild writes no ledger, save one case of the landing log: on a catalog that holds rows and
no log yet, the catalog's first open, which the rebuild makes, writes the log's genesis (§3.6). The
derivations above write only their own stores once the attestor is left out (steps 3 and 4) and
the reference edges are found held (step 3). An attestation from the first derivation still names
the same output, since the output is a deterministic function of the same input. `[DERIVED; the
property is P2 in §8, the genesis P17]`

### 3.4 The chat log, and the ledger it needs

The chat log is derived: its rows are a deterministic parse of the transcript's bytes (CS-1, CS-3;
`ops/chat_sensor.py:101-140`), and the session's id is read from the bytes too
(`record["sessionId"]`, `:130`). What is in no store but the chat log is which raw objects are
transcripts and in what order they were retained, and the order matters: the first write of a turn
stands (`chatlog.py:148-166`), and a session that later shows a candidate secret is held at its
state before it (`chat_sensor.py:316-322`), so the chat log is the fold of the retained transcripts
in retention order, not of the newest one. `[ESTABLISHED]`

So the sensor gains a ledger, written at retention, before extraction (CS-1's order):

```sql
CREATE TABLE IF NOT EXISTS retained (
    seq     INTEGER PRIMARY KEY,   -- the retention order
    digest  TEXT NOT NULL UNIQUE,  -- the raw object's SHA-256
    file    TEXT NOT NULL,         -- the transcript's file stem when retained (for the report)
    at      TEXT NOT NULL          -- wall bookmark only
);
```

A transcript whose bytes are new appends a row; the rest of `_ingest` is unchanged. The rebuild
replays the rows in `seq` order through the same parse, guard and `add_batch`, reading the bytes
from the raw store, so it needs no transcript directory. At its first open on an instance that
predates it, the ledger is filled from the chat log: one row per distinct `transcript_digest`,
ordered within a session by the lowest turn the digest wrote. A digest that wrote no row (refused,
empty, unparseable, or grown with no new prose) is not in that seed and changes nothing in a
replay, so the replay of the seed gives back the chat log as it stands. `[DERIVED]`

The rebuilt chat log equals the one before under the same interpreter version and the same guard
patterns. Under a changed guard the replay is the re-derivation the change asks for: a session
refused before may land, or the reverse. `[DERIVED]`

### 3.5 Model output, and what else cannot be computed again exactly: kept

| store | why it is kept |
|---|---|
| `derived.sqlite` (`core/stores/derived.py`) | interpreted artifacts: a model's output over the notes the pass read (dn-temporal-snapshot §2.2). The reset at main deletes it. Decision D4 |
| the interpreted rows of `edges.sqlite` | a model's labels (`core/relations.py:198-210`) or a `link` request's (`writer.py:555-569`). Decision D4 |
| `run_ledger.sqlite`, `dream_runs.sqlite` | dream claims and experiment runs, with the surface text the model wrote |
| `claim_ops.sqlite` | proposals by design a model's (`core/kernel/recursion_ops.py:44-46`) |
| `staging.sqlite` | staged hypotheses, generation-clocked |
| `structural.duckdb` | invariants of the graph as it stood at each dream pass: a measurement of a past state that no ledger holds |
| `research_curated.lance` | its second writer adds rows with no catalog row and no raw object (`scripts/curate_local.py:96-108`), so they cannot be rebuilt. Decision D5 |
| `eval_results.duckdb`, `probes.sqlite` | measurements of the system |

The causal edges are not in this table, though dn-temporal-snapshot §2.3 item 4 shows they are
not a function of their inputs' present state: the integrator resolves a commit against the
ledger as it stands at its pass. They are model-free, every input is kept, and a rebuild gives the
edges an integration over the present ledger gives, which resolves every commit the earlier passes
resolved and possibly more. So they are rebuilt (step 9), and their guarantee is weaker than the
others' (§4.4). Decision D6. `[DERIVED]`

### 3.6 The catalog and its landing log

The catalog is the head of every landed item and the idempotence key (ING-7). Since pull request
#92 its file holds its past as well: the landing log (`core/stores/landings.py`;
dn-temporal-snapshot §3.2, stage SN-1), two tables, `landing_chains` and `landings`, an
append-only, hash-chained record of which digest each path held when. The catalog's writing
methods append to it in the transaction of the row each writes, so the catalog's rows are the
log's fold (SNP-5). The sources the catalog was landed from may be gone, as a transcript may be,
as a dialogue export may be, so the log can be computed from nothing else, and the rows from
nothing but the log. `[ESTABLISHED]`

- **The log is a ledger, and the reset keeps it.** The reset keeps the catalog's file whole, so it
  keeps the log: every row and every chain's head hash, byte for byte, once the log is there (a
  catalog with no log yet gets its genesis, the next items). `[DERIVED; P2]`
- **Nothing in the reset appends to it.** Two rebuild steps open the catalog: those of the
  lexical index and the authored relation edges (`OPENS_CATALOG` in `ops/lifecycle/rebuild.py`).
  Each reads its active rows (`active_entries`) and calls none of its writing methods. The plane
  step reads no catalog row, since it rebuilds from raw what the plane held (§4.2), so it does not
  open the catalog. The heal of §5 reads it through the writer's open stores, as the lexical step
  does. The chat log's replay, the re-projections, the chat events, the causal edges and the
  dispositions do not open it. `[ESTABLISHED; P2, P10, P17]`
- **The one write is the first open's.** `VaultCatalog`'s constructor sets WAL, runs its DDL and
  migration, and on the first open of a catalog that has rows and no log writes the log's genesis
  (`VaultCatalog._migrate`, `LandingLog.genesis`), which needs the instance's landing-log secret:
  `landing-log-key`, or `<id>.landing-log-key` under a named instance, read through the process's
  configuration. So a reset of an instance whose catalog has rows and no log yet writes the genesis
  at the rebuild's first open, after the clearing, as any first open on main does (the daemon's
  start, a sync, a reader), and leaves the catalog's rows as they were. Without the secret that
  open raises `LandingLogKeyMissing`, and by then it has created the log's two empty tables
  (`executescript` commits the DDL before the genesis asks for the key; measured on a scratch
  catalog), so opening the catalog cannot itself be the check. The reset reads the catalog read
  only before anything is written and refuses without the secret (§4.5). With a log already in the
  file the reset needs no secret: it appends no row and seeks no path by its key.
  `[ESTABLISHED for the constructor; DERIVED for the reset; P17]`
- **What stays a follow-up.** The catalog's rows could be rebuilt as the log's fold instead of kept.
  That needs a write of the catalog's table that bypasses its logging methods, which belongs in
  `core/stores/catalog.py`, and it gives a reset nothing while the file is kept whole. The
  version-keyed derived stores could be rebuilt for every version and not only the head: a replay
  of the log's `store` and `retire` rows in chain order gives the lexical units, the plane's
  occupancies and its supersession log of every version landed since the chain began
  (dn-temporal-snapshot §5.2, §5.3 read the same stores as functions of a cut). A genesis records
  each path's head alone, under a horizon (dn-temporal-snapshot §8), so for an instance whose
  catalog predates the log the versions superseded before its genesis are in no ledger but
  `mirror_authored`'s version chains. Both are decision D2. `[DERIVED]`

### 3.7 Operational state: kept, not content

`queue.sqlite`, `tasks.sqlite`, `telemetry.duckdb`, `supervisor.lock`, the ingress spools and
their receipts under the interface handoff directory, `handoff/dialogue/*.json` and their
`.synced` marks, `code/<name>.synced`, `code_sensing_handoff/`, `agent_sensing_handoff/`, the
corpus sources' stream cursors, `logs/`, `backup-staging/`, `mint_ids_backup/`,
`reembed_bodyonly_backup/`, `effectors/drafts/` and the HashiCorp Vault storage in `vault/`.

The reset at main deletes the queue. A queued job may carry an ingress request whose text is only
in the spool's `queued/` file, so deleting the queue loses a landing the operator asked for. The
reset keeps it. Every derived job kind in it (`embed`, `repository_sync`, the code lanes) is
idempotent and finds nothing to do after the rebuild. Decision D7. `[DERIVED]`

## 4. Reset

### 4.1 What it clears and what it keeps

It clears the stores of §3.3, each by its own `reset` method or, for a store with none, by
deleting its file; and the rows of provenance `authored-solo` in `edges.sqlite`. It keeps every
other store of §3, byte for byte, the catalog's file whole with its landing log (§3.6), save the
log's genesis on a catalog that held rows and no log yet. The
classes are one table in `ops/lifecycle/` (the store's path
relative to the data directory, its class, and for a derived store its rebuild step), and
`reset_targets` and `_RESET_GUARD` are replaced by it. `[DERIVED]`

### 4.2 The vectors without the embedder

The atom table is a memo of one function: the embedder's vector of a text, keyed by the text's
hash (`plane.py:113-115`) under the geometry the plane records (`plane.py:154-166`). Keeping it
through a reset loses no derived state and keeps the rebuild from calling the embedder. So the
plane's reset for a lifecycle reset forgets the occupancies and the supersession log and keeps the
atoms and the recorded geometry. The rebuild re-occupies exactly the (path, digest) pairs the plane
held current before the clearing, read once with each occupancy's title and class and kept in the
marker (§4.3), and nothing more: an item a lazy instance landed without its vector stays waiting
for the embed job, so the plane comes back to its state before. Each pair is rebuilt from raw at
the digest the plane held, whether or not that digest is still the catalog's head: a note edited
after it was embedded, and landed again without its vector, comes back at the version the plane
held, and its new version stays with the embed job. Raw keeps every version, and a purge removes
an object's occupancies with it, so a held version can be read when a reset starts. A purge while
a reset is pending is the exception: the marker names the version and the cleared plane no longer
holds it, so the purge removes no occupancy, and the rerun skips the version and counts it (§4.3).
The step reads no catalog row, so it does not open the catalog (§3.6). The drain over those items
finds every atom held (`embed_missing`, `derive.py:146-180`) and embeds nothing; the atoms no
rebuilt row holds are dropped last. The `held` and `current` cache columns of the atom table are
repaired from the rebuilt relations by the plane's existing repair ratchet. A configured embedder that differs from the recorded geometry is
not a reset's business: the reset refuses and names `palace reembed` (§4.5). `[INFERENCE,
falsifier LCF-2]`

### 4.3 What starts the rebuild

The reset runs the rebuild itself, in its own process, after the clearing, under the instance's
supervisor lock (`ops/lifecycle/lock.py`), which the daemon and some of the writers take as well
(below). It writes a marker, `reset.pending` in the data directory, before it clears anything and
removes it when the last step has run. While the marker is there the daemon's start and every
command that lands into the instance or writes a store the reset rebuilds refuse, naming the
reset: the launcher's on-demand verbs, and the scripts that write (`scripts/ingest.py`,
`scripts/corpus.py ingest` and `embed`, `watch`, `purge_raw`, `ingest_self_knowledge`,
`mint_ids`, `migrate_chunk_keys`, `migrate_provenance_split`, `reembed_bodyonly`,
`ingest_founding`, the code and self sensors' `snapshot_code` and `sense_self`, which the
post-commit hook runs on every commit on main and whose failed sync it reports and lets the next
one heal, `verdict.py submit` and `review`, which apply dispositions, `talk`, which lands what the
inbox kept when no daemon is live, and the swap of the plane migrations `ops.plane_migrate` and
`ops.float16_migrate`). `palace destroy` refuses too (§6.1). So nothing starts to land into a
half-rebuilt instance. A test runs each of those scripts under the marker, and a scan of
`scripts/` fails on a script that calls a builder of a landing or of a derived store and is not
among them (§8, P9). Every step is idempotent, so `palace reset --confirm` run again after an
interruption clears the derived stores again and finishes. `[INFERENCE, falsifier LCF-5]`

A writer reads the marker when it starts, so the marker does not stop one that started before
the reset. The lock stops those that take it: the daemon, `repo-sync`, `scripts/ingest.py`,
`scripts/corpus.py ingest` and `embed`, and `watch`. The other writers take none (the launcher's
`vault-sync`, `embed`, `dream`, `relate`, `lanes`, `reembed`, `ingest-chat`, `dialogue-sync` and
`cache fill`, and `purge_raw`, `ingest_self_knowledge`, `mint_ids`, `migrate_chunk_keys`,
`migrate_provenance_split`, `reembed_bodyonly`, `ingest_founding`, `snapshot_code`,
`sense_self`, `verdict.py submit`, `review`, `talk` and the two plane migrations), so a reset
confirmed while one of them runs is not excluded from it, and that writer goes on writing into the
stores the reset clears and rebuilds. Whether they should hold the lock for their whole run is
open question 7. `[ESTABLISHED]`

A rerun finishes only if no step fails the same way every time, so whatever would stop a step
that way is either found before anything is written, the marker included, or tolerated by the
step. As built: a derived store that does not lie under the data directory (a store beside
`derived_store` configured elsewhere) would be refused by the clearing, so the reset finds it
first and refuses; a commit the commit ledger holds that the repository no longer has (a rewrite
and a garbage collection) would fail the code observations' re-projection, so the reset checks
every ledgered commit first and refuses, naming them (§4.5); a retained transcript whose raw
object a purge erased is skipped by the chat log's replay and counted as purged in its report, so
the erasure stands and the reset finishes (§6.6); and a version the plane held whose raw object a
purge erased while the reset was pending is skipped by the plane step and counted the same way
(§4.2). An instance whose commits are gone for good can be reset only once the loss is accepted,
which this note does not design (open question 4). `[DERIVED; P7, P9]`

### 4.4 Its guarantees

- **Nothing is lost.** Every store of §3.1, §3.2, §3.5 and §3.7 is byte for byte what it was:
  a raw object's file, and every row of every table of a kept SQLite or DuckDB file, save the
  landing log's genesis on a catalog that held rows and no log yet (the next item). `[DERIVED]`
- **The landing log is kept, and nothing is appended to it.** Every row of the log and each
  chain's head hash are what they were, since no step writes the catalog (§3.6). On a catalog
  with rows and no log, the rebuild's first open writes its genesis, as any first open does, and
  the catalog's rows stay as they were. `[DERIVED; P2, P17]`
- **The rebuild converges to the state before.** For each derived store but the causal edges, the
  head after the rebuild equals the head before, with the wall-time bookmarks left out
  (`landed_at`, `observed_at`, `created_at`, `at`, `updated_at`; Law C4). The head is: every row of
  the chat log, the chat events, the dispositions, the code and agent observations' current
  readings and the authored relation edges; the current units and their postings, and the
  version records of the current versions, in the lexical index; the current occupancies of each
  plane class with their atoms' vectors; the current memberships (as built, kept and not
  rebuilt: §10 item 1). Two purges are the exceptions: a transcript a purge erased since the last
  rebuild, without which the chat log and the chat events come back, and a version the plane held
  that a purge erased while the reset was pending, without which the plane comes back. `[DERIVED;
  P3, P9]`
- **The head only.** The lexical units and plane occupancies of superseded versions, and the
  plane's supersession log, are rebuilt for the current versions only (and for the versions the
  plane held, §4.2). The landing log names every version landed since its chain began, so a replay
  of it could rebuild them; that replay is a follow-up (§3.6). No query at `8d4dff3d` reads a
  superseded version's lexical units or occupancies: the purge finds them by digest, and the
  migration that re-keys the plane's rows reads them to re-key them (`rekey_store`,
  `core/ingest/index.py`), which a head-only plane leaves nothing to miss. The re-derivation of a
  stale index and the re-embedding after a model change already rebuild the head only. Decision
  D2. `[ESTABLISHED for the readers; DERIVED]`
- **The causal edges equal a fresh integration over the present inputs**, and a reset run twice
  gives the same edges. `[DERIVED; P4]`
- **No embedder call when the atoms are held, and no ledger written** but that genesis.
  `[DERIVED; P2, P8, P17]`
- **A reset of a reset is the reset.** Two resets in a row leave the same state as one. `[P4]`

### 4.5 Its refusals

A live daemon (the last run active and its process the supervisor, `_supervisor_alive`,
`launcher.py:193-244`); the supervisor lock held by another writer; a configured embedder whose
geometry is not the one the plane records; a derived store that does not lie under the data
directory, and a commit the commit ledger holds that the repository no longer has (§4.3); and a
catalog that holds rows and no landing log while the instance's landing-log secret is not in the
environment, since the rebuild's first open of it would write the log's genesis (§3.6). The last
is read before any open (`catalog_without_log`, `landing_log_secret` in
`ops/lifecycle/rebuild.py`), for the steps that open the catalog, and its refusal names the item
the process reads. Each refusal says what to do, and writes nothing, the marker included: the
geometry is read from the plane's record read only (`geometry_mismatch`), not through the plane,
whose open would create its `-wal` and `-shm`, and the run ledger is not opened (§4.6). When a
reset is pending and the embedder has changed, the refusal says to finish the reset under the
embedder the plane was built with and to change the embedder after it, since `palace reembed`
refuses while the marker stands.

### 4.6 Its dry run

As today: without `--confirm` nothing is written. The dry run prints, by class, every store it
would clear with its row count, the rebuild's steps with the count of items each would read, the
stores it keeps, and for the plane the items it re-occupies, the distinct atoms they need and how
many of those the atom table lacks (the embedder is called for those alone), and the items of the
plane's classes whose current version holds no vector, which the reset leaves to the embed job;
the items the plane holds at a version older than the catalog's head are counted among both. When
the catalog holds rows and no landing log, it says the rebuild's first open writes the genesis.

It writes no row of any store, and on an instance at rest it creates, removes and touches no file.
It reads each SQLite store it counts with `read_only` (`ops/lifecycle/inventory.py`): a store at
rest, with no `-wal`, or an empty one a reader left, and no `-journal`, has every committed page
in its main file and is read `immutable=1`, since a `mode=ro` read of a WAL database creates its
`-wal` and `-shm` and rewrites a `-shm` already there. A store whose `-wal` holds frames is read
`mode=ro`, which updates its `-shm`, since `immutable=1` would miss those frames; that is an
instance not at rest. The plane's geometry is read from its record read only, and the atoms the
table lacks are counted through the atom table, which opens no file of the plane's SQLite. The
launcher's run ledger, through which every command asks whether a run is live, is opened only
when a command writes to it and read only before that (`LazyRunLedger`), so the dry run creates
no file under a root that does not exist either. `[ESTABLISHED, measured on a fixture at rest and
through the command; P6, P11]`

### 4.7 The landing log's secret, by command and instance

The secret is read through the process's configuration (`landing_log_key`), so its item is the
instance's own: `landing-log-key` for the default instance, `<id>.landing-log-key` for a named one
selected by `MIND_PALACE_OVERLAY`. `[ESTABLISHED]`

- **A reset** needs it only while the catalog holds rows and no log: the rebuild's first open
  writes the genesis. With the log in the file it needs none. Without it, when it is needed, the
  reset refuses before anything is written and names the item (§4.5). `[ESTABLISHED; P17]`
- **A destroy and a cache fill** need none: they read the catalog read only and remove it, or
  leave it, whole (§6.2). `[ESTABLISHED; P17]`
- **Under a named instance**, `scripts/run_with_secrets.sh` refuses to run, since it places the
  default instance's items, so a reset that needs the secret is run with the instance's own item
  in its environment under its own name (`docs/runbook.md` shows how). The default instance's item
  does not serve a named instance. `[ESTABLISHED; P17]`
- **The corpus** is a named instance whose catalog has rows and no log yet (§7): a reset of it,
  and any landing into it, needs `corpus.landing-log-key` placed first.

## 5. A sync heals a stale lexical index

`Writer.land` (`core/ingest/writer.py:205-219`) is where every landing into the lexical index
passes: the ingress's `perform` (`core/ingest/ingress.py:716-763`) builds a `Writer` for each
request, script and sync, and every command that lands calls it, through the daemon's handlers
(`scheduler/ingress.py:215`, `:273`) or through `run_library` (`repo_sync_now`, `vault_sync_now`,
the inbox at `core/ingest/inbox.py:121`, the corpus runner at `scripts/corpus.py:254`). Outside
the writer only `derive_lexical` writes the index: the older landers (`core/ingest/sync.py`, the
founding, dialogue and curated lanes) do not open it. So the writer heals the index, before it
prices the plan: when `stores.lexical` is
open and `stale`, it runs `derive_lexical(self.stores)`, which resets the index and lands every
active item of the lexical classes again under the current tokenizer, and then lands the plan.
`derive_lexical` is in `core/ingest/derive.py`, which `writer.py` already imports, so no new
dependency; the heal is one more stage of the landing, reported among the writer's timings as
`rederive`, which the receipt carries already (`ingress.py:758-759`). `[INFERENCE, falsifier
LCF-4]`

In `writer.py` it changes `land`, adds `Writer.heal_lexical` and a `cache` field of `Stores` (the
vector cache of §6.5), and imports `derive_lexical` and `LexicalReport` from `derive.py`; it
leaves `finish` as it is, whose two key writes #92 changed. It changes none of `lexical.py` or
`landing.py` (pull request #93 changes them), `ingress.py` or `sync.py`. The heal
reads the catalog's active rows and appends nothing to its landing log: a healing sync's one new
row of the log is its own landing (P10).

## 6. Destroy

### 6.1 Scope and refusals

`palace destroy` (in `scripts/palace.py` and `Launcher.destroy`) acts on the instance the
configuration selects (`MIND_PALACE_OVERLAY`), and only on a named one: the default instance is
refused by this command, whatever its state. Without `--confirm` it is a dry run. It refuses, and
writes nothing, when: the instance is the default one; a run of it is live; another writer holds
its supervisor lock; a LaunchAgent with its label (`cfg.instance.label`) is installed; its root's
real path lies inside a git working tree, is the home root `~/.mind-palace` itself, or holds the
cache; or the free space on the cache's volume is less than what the cache would gain plus a
margin. `[PROPOSED, D1]`

As built, a root is removed only when it holds nothing but the instance's own state, since the
removal takes the whole root: it also refuses a root with a top-level entry no path of the
instance's namespaces lies at or under (`namespaces_of(cfg).paths`), an entry of the data
directory the class table does not name, a `.git` anywhere below it, a root at, inside or around
another declared instance's root (a derived root inside the checkout excepted, §10 item 5), a
source file the cache would take that is a link (§6.4), and a configured embedder that is not the
plane's geometry (§6.5). It refuses while a reset of the instance is pending, as `cache fill`
does: a reset interrupted after its clearing leaves the plane without the occupancies the fill
selects vectors by, so a destroy then would keep none of the instance's vectors (§10 item 28).
The dry run lists the root's top-level entries, and it takes no lock: it probes the supervisor
lock read only, reads the catalog's and the plane's SQLite files through `read_only`, and reads
the launcher's run ledger without opening it (§4.6), so on an instance at rest it creates and
touches no file, run as a command or in-process, and it creates no root that does not exist. The
loader accepts such a root for a named instance; only destroy refuses it.

### 6.2 What it removes, and what it leaves

It fills the cache from the instance (§6.4), then removes the instance's root, the declared one or
`<repo>/instances/<id>`, without following a symbolic link out of it. The catalog's file goes with
the root, and the landing log in it. A destroy reads the catalog's rows read only and never opens
it through `VaultCatalog`, so it needs no landing-log secret, even for a catalog that holds no log
yet. It leaves what is not in the root: the sources the instance read outside it (a declared
vault, a transcript directory, a repository), its overlay in `config/instances/`, which is code,
and its Keychain items (`<id>.<name>`), which the dry run and the result name for the owner to
remove. `<id>.landing-log-key` is among them: the instance's namespaces do not list it
(`namespaces_of(cfg).secrets`), so `keychain_items` adds it. After the destroy it keys nothing but
a copy of the catalog's file kept elsewhere, a backup's for one. `[PROPOSED]`

The sources inside the root go with it: an open-corpus source's directory under the root's
`sources/`, of which the cache keeps the stream files (§6.4) and nothing else. The whole downloads
some edge readers keep under `<source>/raw/` (`edge/corpus/`: arxiv, hackernews, openalex,
gutenberg, stackexchange), the cursors and the state files are removed with nothing kept. The dry
run names the sources it leaves, and those it removes with the count and bytes of their files the
cache does not take. `[ESTABLISHED]`

### 6.3 The cache

One place, `~/.mind-palace/cache`, shared by every instance of the machine's user, under the home
root and outside every instance's root and every checkout. Its layout:

```
~/.mind-palace/cache/
  LAYOUT                      the layout's version
  raw/<aa>/<digest>           the raw store's own layout (`rawstore.py:24-26`)
  vectors/<key>/atoms.sqlite  atom id -> the vector as the plane stores it; <key> names the
                              embedder (§6.5), its fields in vectors/<key>/key.json
  sources/<source>/<file>     downloaded source files, with sources/<source>/MANIFEST
                              (file, size, SHA-256, when fetched)
  purged.sqlite               the digests a purge erased, with the day (§6.6)
  uses.sqlite                 the day each entry was last put or taken, for retention
```

An entry holds no path, no title and no class: a raw object is named by its digest, a vector by
its atom id, which is the hash of its text, and the text is not stored with the vector. The
location is a constant of the code, as the instances' home is; a test passes a temporary
directory to the functions that take the cache's root. Retention: an entry stays until pruned.
`palace cache prune`, a dry run unless confirmed, removes the entries not taken for 180 days, and
`palace cache` reports the cache's size by namespace. `[PROPOSED, D8]`

### 6.4 What may enter the cache

The cache is a channel between instances, so what enters it is fixed in code, by an allow-list,
and everything else is refused. An item is **open** when its catalog path lies in the space of an
open-corpus source (`corpus/<name>/`, `core/ingest/table.py:454-455`) or a repository source
(`code/<name>/`, `:456-457`), or its class is `curated`. Then:

- a raw object enters when some catalog row, active or tombstoned, names its digest at an open
  item's path;
- a vector enters when its atom is held, current or not, by an open item's occupancy or by a code
  membership (as built, by an open item's occupancy only: §10 item 2);
- a source file enters when it is a stream file of an open-corpus source (the stream's manifest
  and the parts it names, and the items' metadata, which `scripts/corpus.py fetch` copies back
  into an empty source), and a plain file of that source: not a symbolic link, not a file with
  another hard link, not one that resolves out of the source's directory (`plain_file` in
  `core/stores/cache.py`). Not a stream cursor, a checkpoint, or a whole download a reader keeps
  under `raw/`, which no reader takes back from the cache.

Nothing else: no raw object of `authored-solo` or `authored-dialogue` (the mirror's notes, the
dialogue), no observed item outside an open-corpus source (the dialogue's model turns, the inbox,
the sensors' readings), no transcript (the chat sensor's raw objects have no catalog row), no raw
object no catalog row names, and no digest in `purged.sqlite`. `[PROPOSED, D9]`

Nothing of the catalog's file enters either. The fill reads the catalog's rows to select by path
and class and writes none of them: no row of the map, no row of the landing log, no chain's half
of the log's key and no part of the instance's secret reaches the cache. The source files are
chosen by name, and a name that is a link would carry other bytes in: the catalog's file, linked
or hard-linked from a stream part inside the root, or a note outside it. So a fill and a destroy
refuse a source file that is not a plain file of its source before they write anything
(`link_refusal` in `ops/lifecycle/destroy.py`), and the cache's own writer refuses it as well
(`Cache.put_source_files`), as `take_source` refuses a name that climbs out on the reading side.
P12 and P17 search every file of a filled cache for each of the log's values and find none, and
P12 links a stream part to the catalog's file, by a symbolic and by a hard link, and to a note,
and finds each refused. `[ESTABLISHED; P12, P17]`

Why sharing an object held by an open item is safe even when a private item holds the same bytes:
a cache entry carries no path, title or class, so it says only that some open item held these
bytes, and the open item's source holds them in public. The same argument covers an atom shared by
a note and a corpus document. What would break it is an entry whose existence says something the
open sources do not, which the allow-list excludes by taking open items alone. `[DERIVED]`

Reading the cache is not restricted by class: a lookup by hash of bytes the reading instance
already holds tells it only that some open item held them. A lookup that finds an entry does
write: it records the day the entry was taken, in `uses.sqlite`, which the prune reads. So when a
private note's chunk has the text of an open chunk, the cache records the day some instance took
that open atom, and nothing of the note: no path, no instance, no time finer than the day.
`purged.sqlite` holds the digest of every object a purge erased, a private note's among them, with
the day; a digest names content only to someone who holds the content, and it must be kept, or a
later fill would put the object back. `[DERIVED]`

### 6.5 How an instance reuses the cache

- **A vector, by atom.** The vector cache's key is the plane's geometry (`Fingerprint`: model,
  document template, dimension) together with the runtime backend that served it
  (`[runtime] embedding_backend`), hashed. `embed_missing` (`derive.py:146-180`) looks up the
  atoms the plane lacks in the cache under the instance's key before it calls the embedder, and
  lands a found vector as if embedded; `DrainReport` counts it as `cached`. A vector is reused only
  under the same key, so a geometry never mixes, provided a vector is filed under the key of the
  embedder that made it: a fill and a destroy refuse unless the configured geometry is the one the
  plane recorded, as a reset does. The plane does not record the backend, so a change of backend
  alone between embedding and a fill files the vectors under the new backend's key; whether to
  record it is open question 5. `[PROPOSED; falsifier LCF-6]`
- **A raw object, by digest.** `RawStore.get` on a miss reads the cache's object, checks that its
  SHA-256 is the digest asked for, and copies it in; a mismatch is refused and the entry deleted.
  The address is the whole trust decision. This is how an instance takes a raw object it has a
  digest for and no bytes: a catalog seeded from another instance's for a fixture (§7), or a
  replay of the landing log (§3.6, a follow-up).
- **A source, by file.** An edge reader of an open-corpus source looks in `cache/sources/<source>/`
  before it downloads, and takes a file whose size and SHA-256 match its manifest row. The entry's
  trust is the trust of the download that filled it, on this machine.
- **Filling without destroying.** `palace cache fill`, a dry run unless confirmed, copies an
  instance's open content into the cache by the same selection as destroy, without removing
  anything. It is how the corpus shares its vectors with the instances that draw on it (§7).

### 6.6 A purge reaches the cache

`purge_raw` (`core/ingest/purge.py:40-62`) gains a step before it deletes the raw object: it reads
the object's bytes, derives its chunks as the landing did, and removes from the cache the raw
object and the vector of every atom of those chunks, under every key; then records the digest in
`purged.sqlite`. Every fill and every destroy refuses a digest recorded there, so no later
instance puts it back. The atoms are deleted and not recorded, since an atom's text may be held by
an open item whose content is public; the cost of deleting one an open item also holds is one
embedding. So the cache is no way around erasure. A transcript can be purged too: it has no
catalog row, so the gate passes, and a later reset's replay of the retention ledger skips its
digest and says so (§4.3). `[PROPOSED, D10]`

## 7. The corpus at its own root

`config/instances/corpus.toml` declares `[instance] root = "~/.mind-palace/instances/corpus"`, as
`config/instances/code.toml` declares its own, and its header says so in place of
`<root>/instances/corpus/`. The loader already refuses a declared root inside a working tree
(`core/kernel/config/loader.py:1187-1210`), so the corpus can no longer land in a checkout. The
sources stay at `sources/` under the root (`[ingestion.corpus] root`), which is where the moved
data has them. The docs that name the old location are updated: `dn-corpus-instance.md` (§3, the
CIF-5 falsifier), the runbook's corpus section, `config/defaults.toml`'s comment and
`scripts/corpus.py`'s usage lines where they name a path; the dated experiment record
`docs/experiments/corpus-stage1-2026-11-07.md` is a record of its day and keeps its text, with
one line under its header saying where the data lives now.

**A shared dataset.** Other instances draw on it in two ways, both read only: in place, through a
read-only open of its stores (SQLite with `immutable=1`, since a `mode=ro` connection to a WAL
database creates its `-wal` and `-shm` files; Lance read-only) for the regression reads; and
through the cache, once the corpus has filled it (`palace cache fill` under the corpus's overlay),
for a stress instance that lands corpus items and takes their vectors by atom and their raw
objects by digest instead of embedding again. Only the corpus's own tooling writes under its
root: `scripts/corpus.py` (its `ingest` and `embed` under the supervisor lock, its `isolation`
and `lexical` beside them) and the stage-1 measurements (`eval/corpus/`, into `results/`), and,
besides them, a confirmed lifecycle command run under its overlay.

**The regression fixture.** A regression run reads fixed numbers off the corpus read only: the
catalog's count of active items, a lexical query's top hits, a `near` query's answer. Part B
reports the first two in the pull request, from a read-only check that the configuration resolves
the corpus to its root and that its stores open.

**Never through `VaultCatalog`.** The corpus's catalog holds 400,274 rows and no landing log yet.
Opening it through `VaultCatalog` would write under the root: the WAL files, the migration, the
log's two tables and a genesis of 400,274 rows, or, without `corpus.landing-log-key`, refuse after
creating the two empty tables (§3.6). So a regression read opens the corpus's SQLite files with
`immutable=1` and its Lance table read only, and never opens the catalog through its class. The
check was run again on the rebased tree, with the landing log in the base and without
`corpus.landing-log-key` in its environment: the configuration resolves `corpus` to
`~/.mind-palace/instances/corpus`; the catalog holds 400,274
rows, all active, in `vault_files` alone; the lexical index holds 1,369,944 units made by the
legacy tokenizer, and the query "superconductivity phase transition" returned the same five hits
as on 2026-11-12, in 17.37 s at a load average of 2.84; the Lance table holds 1,338,585 rows. A
snapshot of the whole root before and after, 389,745 entries (389,417 files, 18,949,782,338
bytes) by type, size and modification time, showed no entry added, removed or changed.
`[ESTABLISHED, measured 2026-11-13]`

**Reset and destroy of the corpus.** The corpus is a named instance, so both apply. A reset needs
`corpus.landing-log-key` placed first, since its first open of the catalog writes the genesis
(§4.7); a destroy needs no secret. The whole root is 18,949,782,338 bytes in 389,417 files; its
raw store is 387,838 objects of 1,003,892,779 bytes, by a snapshot of the root's metadata taken
on 2026-11-13. On disk the raw store takes about twice its bytes, one file per object in whole
blocks: the stage-1 record counts it at 2.0 GB of allocated blocks (`eval/corpus/footprint.py`).
A reset keeps the raw store and the catalog and rebuilds the lexical index and the
plane relations from them; it re-occupies only what the plane held, every atom of which the atom
table holds, so the embedder is not called, and the items still waiting for a vector stay with
the embed job.

A `palace cache fill` would fill the cache with all of it, since every corpus item is open. Its
dry run, on a copy-on-write clone of the root (2026-11-13, 16.3 s at a load average of 2.87, 687
MB resident), plans 387,838 raw objects (1,003,892,779 bytes), 468 source files of the six
sources (1,372,531,168 bytes) and 1,338,585 vectors, which the cache stores as float64
(8,224,266,240 bytes): 10,600,690,187 bytes by the plan's count, which is what the room check
weighs. That count is of bytes, and the disk takes more: the cache stores the raw objects one file
each, as the raw store does, and the vectors in SQLite pages. The fill reads the vectors in
batches, so its memory does not grow with the plane. Its time, and the space it takes on disk,
are not measured.

A destroy of the corpus refuses as the root stands. The root holds entries no namespace of the
instance names: some written at the root by the repository's own corpus tooling (the runner's
`isolation.json`, `gate.log`, `progress.json` and `progress-vectors.json`, and the stage-1
measurements' `results/`), and some by nothing in the repository (`logs/`,
`progress-vectors-backfill3.json`, and `data/lexical-ascii`, which the class table does not name,
since it names the stores the repository's code writes). They would have to be moved out first;
whether the corpus tooling's own files at the root are the instance's state, for a destroy to
remove, is open question 8. A destroy would also remove the readers' whole downloads under
`sources/<source>/raw/` (810 files, 2,598,652,044 bytes, of which stackexchange's archives are
2,393,902,716) and the state files, none of which the cache takes (§6.2). Neither a fill nor a
destroy of the corpus is run by this pull request, and the runbook does not offer the corpus's
fill until its time is measured.

## 8. What the build tests

Each property is a test on fixture palaces under a temporary directory: notes in a vault, a
transcript through the chat sensor, a repository through `repo-sync` and the code lanes, verdicts,
an attestation trail, a model-free stand-in for the embedder that counts its calls. No test opens
a real instance. Lean adds nothing here that the tests cannot check: every property is about the
code's stores on finite fixtures, and the algebra the rebuild rests on (a fold of a log, the
catalog as that fold) is #92's and dn-temporal-snapshot's.

- **P1, the inventory is total.** After a fixture exercises every lane, every path under the data
  directory is in exactly one class of the table, and every `open_*` helper's path is in the table.
- **P2, a reset keeps every ledger.** Every raw object's file and every row of every table of every
  store of §3.1, §3.2, §3.5 and §3.7 is the same before and after a confirmed reset, the attestation
  ledger included, and the landing log's: on a fixture whose log has a genesis and landings, every
  row of the log and each chain's head hash, and every chain still verifies. Two resets, and a
  reset interrupted and finished, append nothing to it either (P4, P9).
- **P3, the rebuild converges.** For each derived store but the causal edges, the head of §4.4
  after a confirmed reset equals the head before, the wall-time bookmarks left out.
- **P4, a reset is idempotent.** Two confirmed resets leave the state one leaves, the causal edges
  included.
- **P5, the chat stores come from raw.** With the transcript directory emptied after the first
  sync, a reset gives back the chat log and the chat events as they were; a fixture with a grown
  session and one held by the guard included.
- **P6, the dry run writes nothing**: no row of any store, and on an instance at rest no file
  created, removed or touched (§4.6); it names every store it would clear.
- **P7, the refusals.** A live run, the lock held, a changed embedder geometry, a ledgered commit
  the repository no longer has, a derived store outside the data directory: each refuses and
  every byte is unchanged, and no marker is written. The live run is held by a ledger of its own,
  as the daemon holds it, so the reset and a fresh launcher's on-demand verb read it from the file
  (`LazyRunLedger.last`), with its frames in the `-wal` and after a checkpoint, and neither opens
  its own ledger; once the run stops, neither refuses.
- **P8, no embedder call.** A reset of an instance whose atoms are held calls the embedder zero
  times.
- **P9, an interrupted reset finishes.** A failure injected at each rebuild step leaves the
  marker; the daemon's start and `repo-sync` refuse; a second `reset --confirm` finishes and P3
  holds. A purge, between the interruption and the rerun, of a version the marker names: the
  rerun skips it, counts it and finishes. A changed embedder while the reset is pending: the
  refusal names the way out, and the reset finishes once the embedder is restored. Every script
  that writes refuses while the marker stands, before it opens anything, run with the builders it
  would reach past the marker replaced by ones that fail at once; a scan of `scripts/` finds every
  script that calls a builder of a landing or of a derived store among them; and the two plane
  migrations refuse their swap and run their dry run.
- **P10, a sync heals a stale index.** A repository landed under the legacy tokenizer, its index
  then opened under the current one: `repo_sync_now` lands where it raised `TokenizerMismatch`
  before, and the index is no longer stale; the same through `Writer.land` for a vault plan. In
  both, the one row the sync adds to the landing log is its own landing's: the heal adds none.
- **P11, destroy's refusals.** The default instance, a live run (held by a ledger of its own, as in
  P7), the lock held, a pending reset, a root in a working tree, a root that is or holds the cache,
  a symbolic link out of the root, a root holding a git repository or a file not the instance's
  own, a root around another instance's, a changed embedder geometry: each refuses and writes
  nothing, and once the pending reset has finished the fill selects every vector the plane held
  before it; the dry run, on an instance at rest (every store
  closed), creates, removes and touches no file, and names the sources it leaves and those it
  removes. Run as commands in a process of their own, on a root at rest whose catalog has an empty
  `-wal` and a `-shm` beside it, the dry runs of `destroy`, `reset` and `cache fill` create,
  remove and touch no file, the run ledger included, and on a root that does not exist none of
  them creates it.
- **P12, destroy keeps exactly the cache's classes.** After a confirmed destroy of a fixture with
  notes, dialogue, a transcript, corpus items and a repository, the root is gone; the cache's raw
  objects are exactly the digests open items named, its vectors exactly the atoms open items or
  code memberships held (as built, open items only: §10 item 2), its sources exactly the open
  sources' downloaded files; no raw object of a note, a dialogue turn or a transcript, and no
  vector only a private item held, is in it; and no file of it holds a value of the landing log (a
  chain's half of the key or its key check, a row's key of its path, commitment or hash), the
  secret, or a table of the catalog's file. A stream part that is a link (a symbolic link to the
  catalog's file, a hard link to it, a symbolic link to a note outside the root) refuses the
  destroy and the fill, writing nothing, and the cache refuses to store it. So does a regular file
  that resolves out of its source: the catalog's file reached through the stream directory linked
  to the data directory, a link that stays inside the root, and through a manifest part that
  climbs out of the stream.
- **P13, a cached vector is reused without the embedder.** A new instance under the same key
  drains an item whose atoms are cached with zero embedder calls, and its vectors equal the cached
  ones byte for byte; under another key it calls the embedder.
- **P14, a raw object is taken by digest and checked.** A cached object is copied in on a miss; a
  corrupted entry is refused and removed.
- **P15, a purge reaches the cache.** After a purge of a digest, the cache holds neither its raw
  object nor any vector of its chunks' atoms, the digest is recorded, and a later fill or destroy
  of an instance holding it does not put it back.
- **P16, the corpus resolves to its root.** Loading the corpus overlay gives
  `~/.mind-palace/instances/corpus` as the root and every data path under it (a configuration test
  with a temporary home; the check of the real stores is the read-only one of §7, run once and
  reported, not a test).
- **P17, the landing log through a reset and a destroy.** The steps that open the catalog, through
  the rebuild's context or through `VaultCatalog` itself, are exactly `OPENS_CATALOG`, and the
  clearing opens it never. On a catalog with rows and no log, a reset without the secret refuses,
  its dry run too, with every row of every store unchanged and no log table created; with the
  secret its dry run still writes nothing, and the confirmed reset writes the genesis at its first
  open, the catalog's rows stay as they were, the log
  holds one `store` for each of them and nothing more, and every chain verifies. Under a named
  instance loaded through its overlay, the item is `<id>.landing-log-key` and the default
  instance's does not serve; a reset of a catalog that has its log needs no secret; a destroy
  needs none, its dry run names the item among those it leaves, and the cache holds no value of
  the log.

## 9. Decisions for the owner

Each is proposed, with the recommendation first.

- **D1, destroy's scope.** Recommended: named instances only, the default instance refused by the
  command whatever its state, a dry run unless confirmed. The alternative, a destroy of the default
  instance behind a second confirmation, would remove the checkout's `data/` and the HashiCorp
  Vault storage in it.
- **D2, a reset rebuilds the head of the version-keyed stores and keeps the catalog's rows.** With
  the landing log in main (#92), the reset keeps the catalog's file whole, the log in it, and
  appends nothing to it (§3.6). What D2 now covers is what the reset does not yet take from the
  log: the lexical units and plane occupancies of superseded versions, and the plane's
  supersession log, are rebuilt for the current versions (and those the plane held) only, and the
  catalog's rows are kept rather than folded from the log. Recommended: accept both for now, and
  make the log's replay a follow-up: every version landed since a chain began rebuilt from the
  log's `store` and `retire` rows, and the catalog's rows as the log's fold through a write of the
  catalog that bypasses its logging methods. The versions superseded before an instance's genesis
  stay head-only, since no ledger but `mirror_authored`'s version chains holds them. The
  alternative is to keep the lexical index and the plane's relations out of the reset until that
  follow-up, which leaves the stale rows of §2.2 in place.
- **D3, the reference edges are a ledger.** Recommended: kept by the reset until their rows carry
  the extractor's version; then the current extractor's rows become derived and the older ones
  stay.
- **D4, model output is kept.** Recommended: the interpreted artifacts, the interpreted relation
  edges, the dream claims, the claim operations, the staged hypotheses and the structural snapshots
  are all kept by the reset. The reset at main deletes the interpreted artifacts.
- **D5, the curated store is kept whole** until its second writer lands through the catalog.
- **D6, the causal edges are rebuilt**, with the weaker guarantee of §4.4, rather than kept.
- **D7, the queue is kept** by the reset, which deletes it at main.
- **D8, where the cache lives and its retention.** Recommended: `~/.mind-palace/cache`, one
  namespace per kind of entry, entries kept until a prune removes those not taken for 180 days,
  pruning a dry run unless confirmed.
- **D9, what may enter the cache.** Recommended: the raw objects, vectors and downloaded files of
  the open-corpus sources, the repository sources and the curated class; never a private stratum's
  content, a transcript, or a digest a purge erased. Code enters because the repository it came
  from already holds it on this machine; an owner who reads a private repository through an
  instance may strike code from the list.
- **D10, a purge reaches the cache**, removing the raw object and its chunks' vectors and recording
  the digest so it never enters again.
- **D11, the lexical index and the authored relation edges become reset targets**, rebuilt from
  raw; the interpreted relation edges stay.
- **D12, a sync re-derives a stale lexical index before it lands**, in the one writer, for every
  command that lands.
- **D13, the corpus's configuration** declares `[instance] root = "~/.mind-palace/instances/corpus"`
  in `config/instances/corpus.toml`.
- **D14, the membership store is kept by the reset**, found in the build (§10 item 1). Recommended:
  keep it, since it holds the code atoms' embedder ledger beside their occupancy and deleting it
  would make the code lane embed every code atom again; `palace code-rebuild` stays what derives
  it. The alternative is the design's step 5, a rebuild through the code lane's backfill, which
  first needs that ledger moved out of the store.

## 10. As built

Part B built §3 to §8 with these departures, each found in the code:

1. **The membership store is kept, not rebuilt (§3.3 step 5).** `memberships.sqlite` holds the code
   atoms' embedder ledger (`MembershipStore.record_atoms`, `known_atoms` by embedder identity)
   beside the occupancy rows, so deleting the file would forget which code atoms the plane holds
   and make the code lane embed them again. It is classed as kept; `palace code-rebuild` remains
   what derives its occupancy. The rebuild runs steps 1 to 4 and 6 to 10.
2. **Code membership vectors do not enter the cache (§6.4).** No reader takes a code atom back from
   the cache (the code lane does not look there), so caching them would store what nothing reads.
   The vectors that enter are the plane's prose atoms held by open items.
3. **The reuse wiring is `with_cache`, not `build_stores` (§6.5).** `core/ingest/ingress.py` was
   being changed by pull request #89 when this was built, so the cache is attached to the writer's
   stores by `core.stores.cache.with_cache` where the drain runs: the embed job, `palace embed`,
   the reset and the corpus runner. A landing through `run_library` alone does not take raw
   objects from the cache. #89 has since merged; wiring the cache through `build_stores` is left
   as a follow-up.
4. **A source is reused when its stream is empty (§6.5).** The reuse is `scripts/corpus.py fetch`
   copying a cached stream, checked file by file against its manifest, into a source that has none
   before the reader resumes it. So the cache takes a source's stream files. Some edge readers also
   keep whole downloads under `raw/`, which the cache does not take, since no reader looks for
   them there; a destroy removes them with the root, and its dry run counts them (§6.2).
5. **A derived root `<repo>/instances/<id>` may be destroyed (§6.1, §6.2).** It lies in a working
   tree but is the gitignored instance directory §6.2 names; any other root in a working tree
   refuses. A root that is itself a symbolic link refuses too.
6. **A rebuild step whose input store is absent writes nothing**: the chat events without a chat
   log, the causal edges without chat events, the agent observations without a repository, so a
   reset creates no empty store an instance never had.
7. **The vector drain keeps only a cached vector of the plane's width**, so a cache filled under a
   key whose geometry the configuration names but the plane does not hold is never landed.
8. **The corpus's lexical index predates the recorded tokenizer.** The read-only check of §7 found
   no `meta` table: by the store's own rule its units are the legacy tokenizer's, so the next
   landing into the corpus re-derives its 1,369,944 units before it lands (§5).

An audit of the build found these, and the build was changed to match the design's guarantees:

9. **The plane step re-occupies what the plane held, not every pending item (§4.2).** Draining every
   pending item embedded a lazy instance's backlog inside the reset. The (path, digest) pairs the
   plane held current are read before the clearing and kept in the marker. A second audit found
   that the step still rebuilt only the pairs that were the catalog's head, so a held note edited
   since it was embedded lost its occupancy; each held pair is now rebuilt at its own digest, with
   the occupancy's title and class.
10. **A step's inputs are checked before the clearing, or tolerated (§4.3).** A pruned ledgered
    commit refuses the reset before anything is written; a purged transcript is skipped by the
    replay.
11. **Destroy removes only the instance's own state (§6.1).** A root holding anything else, a git
    repository below it, or another instance's root refuses; the dry run probes the lock without
    creating it.
12. **A fill files vectors only under the plane's own geometry, and streams them (§6.5, §7).** The
    plan counts atoms; the fill reads and writes 2,048 vectors at a time.
13. **The cache records its uses and purges to the day (§6.4)**, and `take_source` refuses a
    manifest name that is absolute or climbs out of its directory.
14. **`clear` checks that every store it clears lies under the data directory (§4.1)**, the check
    `reset_targets` made before it was replaced.
15. **The corpus is read with `immutable=1` (§7).** The first read-only check opened its SQLite files
    with `mode=ro`, and on a WAL database that creates the `-wal` and `-shm` files: on 2026-11-12 it
    created an empty `lexical.sqlite-wal` and a `lexical.sqlite-shm` under the corpus root and
    touched `vault_catalog.sqlite-shm`, with no row changed. The check was run again with
    `immutable=1`; a snapshot of the data directory and the Lance tree before and after showed no
    entry created, removed or touched.

Part C rebased the branch onto `8d4dff3d`, with the landing log of #92 in the base, and made the
lifecycle correct with it:

16. **The reset keeps the catalog's file whole, its landing log in it, and appends nothing to the
    log (§3.6).** The inventory names the log as a ledger in the catalog's entry (`LANDING_LOG`).
    P2 now checks every row of the log and each chain's head hash, and P4, P9 and P10 that two
    resets, an interrupted one and a healing sync append nothing.
17. **A reset refuses before a genesis it has no secret for (§3.6, §4.5).** Found in the code: the
    steps that open the catalog do so after the clearing, and the constructor's genesis needs
    the secret, so a missing secret would have stopped a reset with its derived stores cleared and
    the marker left; and the constructor without the secret raises after `executescript` has
    created the log's two empty tables, so opening the catalog cannot be the check. The reset reads
    the catalog read only first (`catalog_without_log`) and refuses, naming the item, with nothing
    written. `OPENS_CATALOG` names the steps that open it, and a test records every open.
18. **Destroy names the landing log's item (§6.2).** Found in the code: the instance's namespaces
    (`namespaces_of(cfg).secrets`) do not list `<id>.landing-log-key`, so the dry run did not name
    it among the items a destroy leaves; `keychain_items` adds it.
19. **The lifecycle's SQLite readers create no file (§4.6, §6.1).** Found by a probe on a fixture
    at rest: destroy's dry run created the catalog's and the plane's `-wal` and `-shm` files, since
    its readers opened them `mode=ro`, and P11 passed only because the fixture held its stores open.
    The readers of the destroy and of the reset go through `read_only`, the fixture's own reader
    too, and P11 runs on an instance at rest. The reset's dry run still opened the plane through
    the vector store, until item 25.
20. **The corpus check was run again on the rebased tree, over the whole root (§7)**, never through
    `VaultCatalog`, which on the corpus's catalog would write the log's genesis or refuse.

An audit of part C found these, and the build was changed to match:

21. **The plane step opens no catalog, and skips a held version a purge erased (§3.6, §4.2,
    §4.3).** It read no catalog row and opened the catalog anyway, so a reset whose only
    catalog-opening step was the plane wrote a genesis, or needed the secret, for nothing; it no
    longer opens it, and `OPENS_CATALOG` is the lexical index and the authored relation edges. A
    purge between an interrupted reset and its rerun could erase a version the marker named, and
    every rerun then failed at the plane step with the marker left; the step now skips such a
    version and counts it, as the chat log's replay skips a purged transcript.
22. **Whatever stops a rebuild every time refuses before the marker (§4.3, §4.5).** The check that
    a derived store lies under the data directory ran in the clearing, after the marker was
    written, so a store configured outside it left the marker on every rerun; it now runs with
    the other preflights, and the clearing keeps it as its own guard.
23. **Every script that writes reads the marker (§4.3).** `purge_raw`, `ingest_self_knowledge`,
    `mint_ids`, `scripts/corpus.py embed`, `watch`, `migrate_chunk_keys`,
    `migrate_provenance_split` and `reembed_bodyonly` did not; each now refuses while it stands,
    before it opens anything. The exclusion of a writer that started before the reset is open
    question 7.
24. **A source file that is a link enters no cache (§6.4).** The fill takes source files by name,
    so a stream part linked to the catalog's file inside the root, or to a note outside it, put
    that file into the cache; destroy refused only links out of the root, and `cache fill` none. A
    fill and a destroy now refuse a source file that is not a plain file of its source, and the
    cache's writer refuses one too.
25. **The dry runs write nothing through the command (§4.5, §4.6, §6.1).** The launcher opened its
    run ledger when it was built, so every command, a dry run or a refusal of reset, destroy or
    cache fill included, created `data/runs.sqlite`, and under a root that did not exist created
    the root; a store with an empty `-wal` left by a reader was read `mode=ro`, which rewrote its
    `-shm`; and the reset's geometry check opened the plane. The ledger is now opened at its first
    write and read only before (`LazyRunLedger`), a store whose `-wal` is empty is read
    `immutable=1`, and the geometry is read from the plane's record read only. A test runs the
    three commands in a process of their own.
26. **Destroy's dry run names what it leaves and what it removes (§6.2).** It said it left "its
    sources" while it removed the sources inside the root, whose whole downloads the cache does not
    take; it now names the sources it leaves outside the root, and those it removes with the count
    and bytes of their files the cache does not take. A reset pending under a changed embedder now
    refuses with the way out, since `palace reembed` refuses while the marker stands (§4.5).
27. **Every command that lands or writes a derived store reads the marker (§4.3).** Item 23 left
    out the founding ingest, the code and self sensors' syncs, which the post-commit hook runs on
    every commit on main, and `verdict.py submit`; a search of every entry point under `scripts/`
    and `ops/` found the review REPL, the live talk loop and the swap of the two plane migrations
    as well. A founding item landed while the marker stood kept its active catalog row and lost its
    vectors at the rerun, which re-occupies only the versions the marker names, and the code
    sensor, run under the marker in a test, began syncing the repository's whole history. Each now
    refuses while the marker stands, before it opens anything; the migrations' dry runs, which swap
    nothing, still run. A test runs each script under the marker, with the builders it would reach
    past it replaced by ones that fail at once, and a scan of `scripts/` fails on a script that
    calls a builder of a landing or of a derived store and is not run that way. The scan reads
    `scripts/` alone; the runnable modules under `ops/` were read, and of them only the two
    migrations write a store the reset rebuilds.
28. **A destroy refuses a pending reset (§6.1).** It did not read the marker, so after a reset
    interrupted past its clearing it filled the cache with no vector, the plane holding no
    occupancy, and removed the root, neither its dry run nor its result saying why. It now refuses
    while the marker stands, as `cache fill` does, and once the reset has finished the fill selects
    every vector again.
29. **Two guards had no test (§4.6, §6.4).** The commands' run ledger, read from the file until a
    write opens it, is the live-daemon check of every command that only asks, and the live-run
    tests opened the run through the launcher's own ledger, so they read it through that
    connection; the run is now held by a ledger of its own, as by the daemon. A source file is
    refused when it resolves out of its source, which is the one guard against a regular file
    reached through a directory link inside the root, which destroy's scan allows, or through a
    manifest part that climbs out of the stream; P12 now reaches the catalog's file both ways. Each
    guard was removed in turn, and a test failed.
30. **A test of the tier wrote the checkout's data directory (§3.4).** The chat sensor's wiring
    test built the sensor on the default configuration, so it opened the chat log, the raw store
    and the retention ledger in the checkout's data directory, and seeded the ledger from the chat
    log there. The deploy gate runs the tier in the checkout of the running instance while its
    daemon still runs the code before the ledger, so the test would seed that instance's ledger
    early; a transcript the old daemon retained after it would get no row, since the new daemon's
    start seeds nothing again, and a replay would rebuild its session from a later digest, or not
    at all when the guard holds that one. The test now opens its stores under a temporary
    directory. A seed run at every build, adding the chat log's digests the ledger lacks, would
    close such a gap whatever opened it; it is open question 9.

## Falsifiers

- **LCF-1 (the inventory is not total):** a store written by a lane the fixtures exercise that the
  class table does not name. P1 finds it.
- **LCF-2 (the atoms are not a memo):** a reset whose drain lands a vector that differs from the one
  the plane held for the same atom under the same geometry.
- **LCF-3 (the chat log is not the fold of the retained transcripts):** a fixture whose replay of
  the retention ledger gives a chat log that differs from the one the sensor built.
- **LCF-4 (the heal is not enough):** a landing that still raises `TokenizerMismatch`, or a command
  that lands into an instance without passing `Writer.land`.
- **LCF-5 (the marker leaks):** a writer that starts while `reset.pending` exists and lands, or a
  script under `scripts/` that calls a builder of a landing or of a derived store and is not run
  under the marker by P9. A writer that started before the reset and takes no lock is not
  excluded by the marker (§4.3, open question 7).
- **LCF-6 (the vector key is too coarse):** two instances under the same key whose embedders give
  one text vectors with a cosine below 0.9999; then the key needs the model file's digest.
- **LCF-7 (the rebuild writes the catalog):** a reset of a catalog that has its landing log after
  which the log holds a row it did not hold, or a chain's head hash differs; or a step that opens
  the catalog and is not in `OPENS_CATALOG`. P2 and P17 find it.

## Open questions

1. The vector key names the model and the backend but not the model file. A requantized file under
   the same name would share a key (LCF-6). The llama.cpp backend can report the file it serves;
   whether to put its digest in the key is open until a measurement says the geometry moves.
2. The default instance has no destroy. Whether it needs a command that empties it to a fresh start
   (the reset at main's old purpose) is open; this note gives none, by decision 4.
3. A reset of the corpus re-derives its 1,369,944 lexical units from raw and re-occupies the plane
   over its 1,338,585 stored vectors; its time at that size is not measured here.
4. A commit the commit ledger holds and the repository has lost refuses every reset of the instance
   (§4.3). Whether a reset may then drop that commit's code observations, and on what
   confirmation, is a decision this note leaves open.
5. The plane records its geometry (`Fingerprint`: model, document template, dimension) but not the
   runtime backend that served the embedder, and the vector cache's key names both (§6.5). A
   change of backend alone between embedding and a fill is not caught: the fill files the plane's
   vectors under the new backend's key. Catching it needs the plane to record the backend, as a
   new key of its `meta` table written beside the geometry at the first landing, checked by the
   fill, the destroy and the reset as the geometry is, with a rule for a plane that predates the
   key. Whether to make that schema change is open.
6. Whether the landing log's genesis should move off a catalog's first open is open with the owner
   (dn-temporal-snapshot §12, SN-1). Moved off it, a reset would never need the secret, and the
   refusal of §4.5 would go with it.
7. A reset excludes a writer that starts after it (the marker) and one that holds the supervisor
   lock, but not an on-demand writer that takes no lock and started before it (§4.3): such a
   writer goes on writing into the stores the reset clears and rebuilds. Closing that needs every
   writer to hold a lock the reset takes for the writer's whole run. Either every on-demand
   writer takes the supervisor lock, as `repo-sync` and `scripts/ingest.py` do, which widens the
   lock beyond the supervisor role dn-supervision-and-liveness §2.6 gives it and makes two
   on-demand writers exclude each other; or the writers share a lock the reset takes alone. Which
   one is a decision this note leaves open.
8. The corpus tooling writes files at the corpus's root that no namespace of the instance names
   (§7): the runner's `isolation.json`, `gate.log`, `progress.json` and `progress-vectors.json`,
   and the stage-1 measurements' `results/`. A destroy refuses such a root until they are moved
   out. Whether they are the instance's own state, for a destroy to remove with the root, and
   whether the measurements' results should be kept elsewhere first, is a decision this note
   leaves open.
9. The retention ledger is seeded from the chat log once, at its first open (§3.4). A transcript
   retained after that seed by code that writes no row, a daemon still running the code before
   the ledger or one a rollback put back, gets none, and a replay rebuilds its session from a
   later digest, or not at all when the guard holds that one (§10 item 30). A seed run at every
   build, adding each digest of the chat log the ledger lacks, closes that gap, but it appends
   after the rows already there: the turns a missing digest first wrote are then replayed from the
   later digest before it, and the rebuilt chat log names that digest for them. Placing a digest
   at its retention position needs an order the ledger does not keep. Whether to seed at every
   build, and how to order what it adds, is a decision this note leaves open.

## Cross-references

- dn-temporal-snapshot §2.2 (the inventory), §2.3 item 7 (the reset as it was), §3.2 (the landing
  log, SN-1, merged with #92), §5.2 and §5.3 (vectors and the lexical index as functions of a
  cut), §6.1 (what a purge leaves), §8 (horizons), §12 (the genesis at the first open); the
  algebra of cuts on the branch `feat/cut-algebra`, which amends it.
- chat-sensor CS-1 and CS-3; `core/stores/chatlog.py` header (the chat log as a derived layer).
- self-sensing §2.5 (readings rebuilt, history kept); code-observation-projection §2.4, §2.5.
- dn-two-phase-ingestion D1 (the vector and the units as derived fields); dn-embedder-use (the
  tokenizer's identity).
- dn-palace-lite (`[instance] root`); dn-corpus-instance §3 (the corpus's namespace).
- verdict-authority §3, §4 (the verdicts and their application).
