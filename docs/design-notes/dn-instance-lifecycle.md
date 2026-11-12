---
type: design-note
id: dn-instance-lifecycle
track: deployed-instances
status: draft                  # provenance description, never a gate; the merge is ratification
implementation: built          # part B built §4 to §8; §10 records where the build departs
created: 2026-11-12
updated: 2026-11-12
links:
  - docs/design-notes/dn-temporal-snapshot.md          # §2.2 the inventory this note checks and extends; §2.3 item 7 the reset as it was; §3.2 the landing log
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

> Drafted on the branch `feat/instance-lifecycle`, cut from `origin/main` at `0a5fba27`. Every
> claim about code was read there, at the lines cited; the landing log was read on the branch of
> pull request #92 at `245f938d` (`git show`, no checkout). Nothing is built by this part: part B
> builds §4 to §8. Grades: `[ESTABLISHED]` is a fact of the code at the lines cited or of a
> ratified note; `[DERIVED]` is argued here from those; `[INFERENCE]` is a design call with a
> named falsifier; `[PROPOSED]` is a choice this note makes and leaves to the owner (§9).

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
   catalog, the attestations, the version chains, the verdicts and the queue, which the reset
   removes today, are kept. The lexical index and the authored relation edges, which it leaves
   today, are rebuilt. `[DERIVED from decision 1 and §3]`
3. **The chat log is rebuilt from the raw store through a new ledger of retained transcripts
   (§3.4).** Today a kept raw store makes the chat sensor skip every transcript it has seen, so
   nothing would rebuild the chat log. `[ESTABLISHED for the gap; INFERENCE for the ledger,
   falsifier LCF-3]`
4. **Every landing re-derives a stale lexical index before it lands, in the one writer (§5).**
   `[INFERENCE, falsifier LCF-4]`
5. **Destroy applies to a named instance only, is a dry run unless confirmed, and leaves a shared
   cache of raw objects, vectors and downloaded sources at `~/.mind-palace/cache` (§6).** Only the
   open sources' content enters the cache, never a private stratum's, and a purge reaches it.
   `[PROPOSED]`
6. **The corpus instance declares its root, and its stores are read in place, read only, by the
   regression and stress tooling (§7).** `[PROPOSED]`

### 1.3 Out of scope

The landing log itself (pull request #92) and every file it changes; the erasure of what a purge
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
sentence can read, with the operational ones, and was checked against the code at `0a5fba27`.

### 3.1 Ledgers: sources of truth, kept

| store | writer | why it is a ledger |
|---|---|---|
| `raw/` (`core/kernel/stores/rawstore.py`) | the writer's derive step (`writer.py:407-412`), the chat sensor (`chat_sensor.py:310`) | the verbatim bytes; every derived store is a function of them; a purge is its one deletion (`rawstore.py:51-61`) |
| `vault_catalog.sqlite` (`core/stores/catalog.py`) | the writer's key (`writer.py:449-450`, `:463-464`), the vault sync, the founding, dialogue and curated landers | the map from path to digest, title, class and identity. Before #92 nothing else holds it (§3.6) |
| `versions.sqlite` (`core/stores/versions.py`) | `Writer.finish` for the place that keeps chains (`writer.py:433-445`) | the version chains of `mirror_authored` |
| `attestations.sqlite` (`core/attestation/store.py`) | the attestor, from the writer and the sensors | append-only, content-addressed; the record of who produced what |
| `chat_retention.sqlite` (new, §3.4) | the chat sensor, at retention | which raw objects are transcripts, in the order they were retained |
| `code_snapshots.sqlite` (`ops/code_snapshot.py`) | the code sensor | the commit ledger; already in `_RESET_GUARD` |
| `observation_history.sqlite` (`core/stores/observation_history.py`) | the code and self sensors, on supersession | superseded generations, whose interpreters no longer exist (self-sensing §2.5); already guarded |
| `reference_edges.sqlite` (`core/stores/reference_edges.py`) | the code sensor's projection | append-only, `INSERT OR IGNORE`; a commit's reading is the union of every projection so far, and the rows carry no extractor version (dn-temporal-snapshot §2.2), so a re-projection under today's extractor would not give the rows back. Kept: decision D3 |
| `query_log.jsonl` (`core/sentence/surface.py:52`) | the sentence surface | the record of what was asked |
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
| 5 | `memberships.sqlite` and the code atoms' occupancy (`core/stores/memberships.py`) | commit ledger, git | the code lane's `backfill` over `ledger_versions` (`scheduler/code_sync.py:59-76`), without the job's `capture_commit_diffs`, which appends to the commit ledger |
| 6 | the authored rows of `edges.sqlite` (provenance `authored-solo`) | catalog, raw | `RelationDetector.authored`, changed to parse each active note's raw bytes by its catalog digest instead of its vault file |
| 7 | `chatlog.sqlite` | the retention ledger, raw | a replay of the retention ledger (§3.4) |
| 8 | `chat_events.sqlite` | chat log, raw | `ChatEventProjector.project` (`core/chat_events.py:199-215`) |
| 9 | `causal_edges.sqlite` | chat events, commit ledger | `Integrator.integrate` (`core/integrator.py:97-116`) |
| 10 | `verdict_dispositions.sqlite` | verdicts | `apply_verdict` over every verdict in sequence order (`core/verdict/apply.py:68-77`) |

Then the atoms that no occupancy and no membership holds are dropped, so the atom table holds
exactly what the rebuilt relations name. Steps 2 and 5 are skipped by an instance that embeds
nothing; steps 3 to 5 by one whose code sensor and code lane are off; steps 7 to 9 by one that
reads no transcripts. A step with nothing to rebuild costs a read of its inputs.

The interpreted rows of `edges.sqlite` stay: they are model output (§3.5). So the reset of that
store deletes the rows of provenance `authored-solo` and keeps the rest, the one derived store
cleared by rows and not by file. `[DERIVED]`

The rebuild writes no ledger. The derivations above write only their own stores once the attestor
is left out (steps 3 and 4) and the reference edges are found held (step 3). An attestation from
the first derivation still names the same output, since the output is a deterministic function of
the same input. `[DERIVED; the property is P2 in §8]`

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
| the interpreted rows of `edges.sqlite` | a model's labels (`core/relations.py:198-210`) or a `link` request's (`writer.py:552-568`). Decision D4 |
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

### 3.6 The catalog, before and after the landing log

The catalog is the head of every landed item and the idempotence key (ING-7), and at main no
ledger holds its past outside `mirror_authored`'s version chains (dn-temporal-snapshot §2.3 item
1). The sources it was landed from may be gone, as a transcript may be, as a dialogue export may
be. So before #92 the catalog cannot be computed from anything, and the reset keeps it whole, as it
keeps a ledger. `[DERIVED]`

Pull request #92 adds the landing log to the catalog's file (`core/stores/landings.py` at
`245f938d`): an append-only, hash-chained log written in the transaction of the catalog's row,
whose fold is the catalog (§3.2 of dn-temporal-snapshot on that branch). Once it has landed:

- the log's two tables, `landing_chains` and `landings`, are a ledger, and the reset keeps them;
- the catalog's rows are derived, and the reset rebuilds them by folding the log, without
  appending to it. That needs a write of the catalog's table that bypasses its logging methods,
  which belongs in `core/stores/catalog.py`, a file #92 changes, so it is a follow-up to both pull
  requests and not part of this one;
- the version-keyed derived stores can be rebuilt for every version and not only the head: the
  lexical units, the plane's occupancies and its supersession log are written by replaying the
  log's `store` and `retire` rows in chain order, which gives every version's rows and the
  supersession entries in landing order. Before #92 a rebuild gives the head only (§4.4).

What the reset does before #92 lands is what this pull request builds: the catalog is kept, and
nothing in the reset reads or writes the log's tables, so the two pull requests merge in either
order. `[DERIVED]`

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
other store of §3, byte for byte. The classes are one table in `ops/lifecycle/` (the store's path
relative to the data directory, its class, and for a derived store its rebuild step), and
`reset_targets` and `_RESET_GUARD` are replaced by it. `[DERIVED]`

### 4.2 The vectors without the embedder

The atom table is a memo of one function: the embedder's vector of a text, keyed by the text's
hash (`plane.py:113-115`) under the geometry the plane records (`plane.py:154-166`). Keeping it
through a reset loses no derived state and keeps the rebuild from calling the embedder. So the
plane's reset for a lifecycle reset forgets the occupancies and the supersession log and keeps the
atoms and the recorded geometry; the drain then finds every atom held (`embed_missing`,
`derive.py:146-180`) and embeds nothing; the atoms no rebuilt row holds are dropped last. The
`held` and `current` cache columns of the atom table are repaired from the rebuilt relations by the
plane's existing repair ratchet. A configured embedder that differs from the recorded geometry is
not a reset's business: the reset refuses and names `palace reembed` (§4.5). `[INFERENCE,
falsifier LCF-2]`

### 4.3 What starts the rebuild

The reset runs the rebuild itself, in its own process, after the clearing, under the instance's
supervisor lock (`ops/lifecycle/lock.py`), the lock every on-demand writer takes. It writes a
marker, `reset.pending` in the data directory, before it clears anything and removes it when the
last step has run. While the marker is there the daemon's start and every on-demand writer refuse,
naming the reset, so nothing lands into a half-rebuilt instance. Every step is idempotent, so
`palace reset --confirm` run again after an interruption clears the derived stores again and
finishes. `[INFERENCE, falsifier LCF-5]`

### 4.4 Its guarantees

- **Nothing is lost.** Every store of §3.1, §3.2, §3.5 and §3.7 is byte for byte what it was:
  a raw object's file, and every row of every table of a kept SQLite or DuckDB file. `[DERIVED]`
- **The rebuild converges to the state before.** For each derived store but the causal edges, the
  head after the rebuild equals the head before, with the wall-time bookmarks left out
  (`landed_at`, `observed_at`, `created_at`, `at`, `updated_at`; Law C4). The head is: every row of
  the chat log, the chat events, the dispositions, the code and agent observations' current
  readings and the authored relation edges; the current units and their postings, and the
  version records of the current versions, in the lexical index; the current occupancies of each
  plane class with their atoms' vectors; the current memberships. `[DERIVED; P3]`
- **Before #92, the head only.** The lexical units and plane occupancies of superseded versions,
  and the plane's supersession log, are rebuilt for the current versions only, since no ledger
  names a superseded version's path outside the version chains. No reader at main reads a
  superseded version's lexical units or occupancies but the purge, which finds them by digest. The
  re-derivation of a stale index and the re-embedding after a model change already rebuild the head
  only. Decision D2. `[ESTABLISHED for the readers; DERIVED]`
- **The causal edges equal a fresh integration over the present inputs**, and a reset run twice
  gives the same edges. `[DERIVED; P4]`
- **No embedder call when the atoms are held, and no ledger written.** `[DERIVED; P2, P8]`
- **A reset of a reset is the reset.** Two resets in a row leave the same state as one. `[P4]`

### 4.5 Its refusals

A live daemon (the last run active and its process the supervisor, `_supervisor_alive`,
`launcher.py:193-244`); the supervisor lock held by another writer; a configured embedder whose
geometry is not the one the plane records. Each refusal says what to do, and writes nothing.

### 4.6 Its dry run

As today: without `--confirm` nothing is written. The dry run prints, by class, every store it
would clear with its row count, the rebuild's steps with the count of items each would read, the
stores it keeps, and the count of atoms the cache or the atom table holds against the count the
rebuild needs, so the operator sees whether the embedder would be called.

## 5. A sync heals a stale lexical index

`Writer.land` (`core/ingest/writer.py:205-219`) is where every landing into the lexical index
passes: the ingress's `perform` (`core/ingest/ingress.py:709-756`) builds a `Writer` for each
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
`rederive`, which the receipt carries already (`ingress.py:751-752`). `[INFERENCE, falsifier
LCF-4]`

This changes none of the files the open pull requests change: `writer.py`'s `land`, not
`finish`; no change to `lexical.py`, `landing.py`, `ingress.py` or `sync.py`.

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

### 6.2 What it removes, and what it leaves

It fills the cache from the instance (§6.4), then removes the instance's root, the declared one or
`<repo>/instances/<id>`, without following a symbolic link out of it. It leaves what is not in the
root: the sources the instance read (a declared vault, a transcript directory, a repository), its
overlay in `config/instances/`, which is code, and its Keychain items (`<id>.<name>`), which the
dry run and the result name for the owner to remove. `[PROPOSED]`

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
  purged.sqlite               the digests a purge erased (§6.6)
  uses.sqlite                 the last time each entry was taken, for retention
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
  membership;
- a source file enters when it is a downloaded file of an open-corpus source (the edge readers'
  dumps under the corpus root's `<name>/`), not a stream cursor or a checkpoint.

Nothing else: no raw object of `authored-solo` or `authored-dialogue` (the mirror's notes, the
dialogue), no observed item outside an open-corpus source (the dialogue's model turns, the inbox,
the sensors' readings), no transcript (the chat sensor's raw objects have no catalog row), no raw
object no catalog row names, and no digest in `purged.sqlite`. `[PROPOSED, D9]`

Why sharing an object held by an open item is safe even when a private item holds the same bytes:
a cache entry carries no path, title or class, so it says only that some open item held these
bytes, and the open item's source holds them in public. The same argument covers an atom shared by
a note and a corpus document. What would break it is an entry whose existence says something the
open sources do not, which the allow-list excludes by taking open items alone. `[DERIVED]`

Reading the cache is not restricted by class: a lookup by hash of bytes the reading instance
already holds tells it only that some open item held them, and writes nothing. `[DERIVED]`

### 6.5 How an instance reuses the cache

- **A vector, by atom.** The vector cache's key is the plane's geometry (`Fingerprint`: model,
  document template, dimension) together with the runtime backend that served it
  (`[runtime] embedding_backend`), hashed. `embed_missing` (`derive.py:146-180`) looks up the
  atoms the plane lacks in the cache under the instance's key before it calls the embedder, and
  lands a found vector as if embedded; `DrainReport` counts it as `cached`. A vector is reused only
  under the same key, so a geometry never mixes. `[PROPOSED; falsifier LCF-6]`
- **A raw object, by digest.** `RawStore.get` on a miss reads the cache's object, checks that its
  SHA-256 is the digest asked for, and copies it in; a mismatch is refused and the entry deleted.
  The address is the whole trust decision. This is how an instance takes a raw object it has a
  digest for and no bytes: a catalog seeded from another instance's for a fixture (§7), or a log
  replay after #92.
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
embedding. So the cache is no way around erasure. `[PROPOSED, D10]`

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
read-only open of its stores (SQLite `mode=ro`, Lance read-only) for the regression reads; and
through the cache, once the corpus has filled it (`palace cache fill` under the corpus's overlay),
for a stress instance that lands corpus items and takes their vectors by atom and their raw
objects by digest instead of embedding again. Nothing but the corpus's one writer,
`scripts/corpus.py ingest` under its supervisor lock, writes under its root.

**The regression fixture.** A regression run reads fixed numbers off the corpus read only: the
catalog's count of active items, a lexical query's top hits, a `near` query's answer. Part B
reports the first two in the pull request, from a read-only check that the configuration resolves
the corpus to its root and that its stores open.

**Reset and destroy of the corpus.** The corpus is a named instance, so both apply. A reset keeps
its 19 GB of raw and its catalog and rebuilds its lexical index and plane relations from them,
with every atom held, so the embedder is not called. A destroy would fill the cache with all of
it, since every corpus item is open. Neither is run by this pull request.

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
  ledger included.
- **P3, the rebuild converges.** For each derived store but the causal edges, the head of §4.4
  after a confirmed reset equals the head before, the wall-time bookmarks left out.
- **P4, a reset is idempotent.** Two confirmed resets leave the state one leaves, the causal edges
  included.
- **P5, the chat stores come from raw.** With the transcript directory emptied after the first
  sync, a reset gives back the chat log and the chat events as they were; a fixture with a grown
  session and one held by the guard included.
- **P6, the dry run writes nothing** and names every store it would clear.
- **P7, the refusals.** A live run, the lock held, a changed embedder geometry: each refuses and
  every byte is unchanged.
- **P8, no embedder call.** A reset of an instance whose atoms are held calls the embedder zero
  times.
- **P9, an interrupted reset finishes.** A failure injected at each rebuild step leaves the
  marker; the daemon's start and `repo-sync` refuse; a second `reset --confirm` finishes and P3
  holds.
- **P10, a sync heals a stale index.** A repository landed under the legacy tokenizer, its index
  then opened under the current one: `repo_sync_now` lands where it raised `TokenizerMismatch`
  before, and the index is no longer stale; the same through `Writer.land` for a vault plan.
- **P11, destroy's refusals.** The default instance, a live run, the lock held, a root in a working
  tree, a root that is or holds the cache, a symbolic link out of the root: each refuses and writes
  nothing; the dry run writes nothing.
- **P12, destroy keeps exactly the cache's classes.** After a confirmed destroy of a fixture with
  notes, dialogue, a transcript, corpus items and a repository, the root is gone; the cache's raw
  objects are exactly the digests open items named, its vectors exactly the atoms open items or
  code memberships held, its sources exactly the open sources' downloaded files; no raw object of a
  note, a dialogue turn or a transcript, and no vector only a private item held, is in it.
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

## 9. Decisions for the owner

Each is proposed, with the recommendation first.

- **D1, destroy's scope.** Recommended: named instances only, the default instance refused by the
  command whatever its state, a dry run unless confirmed. The alternative, a destroy of the default
  instance behind a second confirmation, would remove the checkout's `data/` and the HashiCorp
  Vault storage in it.
- **D2, a reset before #92 rebuilds the head of the version-keyed stores.** Recommended: accept it,
  and rebuild every version once #92 has landed and the follow-up of §3.6 has. The alternative is
  to keep the lexical index and the plane's relations out of the reset until then, which leaves the
  stale-row problem of §2.2 in place.
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
3. **The reuse wiring is `with_cache`, not `build_stores` (§6.5).** `core/ingest/ingress.py` is
   changed by pull request #89, so the cache is attached to the writer's stores by
   `core.stores.cache.with_cache` where the drain runs: the embed job, `palace embed`, the reset and
   the corpus runner. A landing through `run_library` alone does not take raw objects from the
   cache.
4. **A source is reused when its stream is empty (§6.5).** The edge readers write streams, not
   whole downloads, so the reuse is `scripts/corpus.py fetch` copying a cached stream, checked file
   by file against its manifest, into a source that has none before the reader resumes it.
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

## Falsifiers

- **LCF-1 (the inventory is not total):** a store written by a lane the fixtures exercise that the
  class table does not name. P1 finds it.
- **LCF-2 (the atoms are not a memo):** a reset whose drain lands a vector that differs from the one
  the plane held for the same atom under the same geometry.
- **LCF-3 (the chat log is not the fold of the retained transcripts):** a fixture whose replay of
  the retention ledger gives a chat log that differs from the one the sensor built.
- **LCF-4 (the heal is not enough):** a landing that still raises `TokenizerMismatch`, or a command
  that lands into an instance without passing `Writer.land`.
- **LCF-5 (the marker leaks):** a writer that lands while `reset.pending` exists.
- **LCF-6 (the vector key is too coarse):** two instances under the same key whose embedders give
  one text vectors with a cosine below 0.9999; then the key needs the model file's digest.

## Open questions

1. The vector key names the model and the backend but not the model file. A requantized file under
   the same name would share a key (LCF-6). The llama.cpp backend can report the file it serves;
   whether to put its digest in the key is open until a measurement says the geometry moves.
2. The default instance has no destroy. Whether it needs a command that empties it to a fresh start
   (the reset at main's old purpose) is open; this note gives none, by decision 4.
3. A reset of the corpus rebuilds 1.3 million chunks a gigabyte of lexical units from raw; its cost
   at the corpus's size is not measured here.

## Cross-references

- dn-temporal-snapshot §2.2 (the inventory), §2.3 item 7 (the reset as it was), §3.2 (the landing
  log, on #92's branch), §6.1 (what a purge leaves).
- chat-sensor CS-1 and CS-3; `core/stores/chatlog.py` header (the chat log as a derived layer).
- self-sensing §2.5 (readings rebuilt, history kept); code-observation-projection §2.4, §2.5.
- dn-two-phase-ingestion D1 (the vector and the units as derived fields); dn-embedder-use (the
  tokenizer's identity).
- dn-palace-lite (`[instance] root`); dn-corpus-instance §3 (the corpus's namespace).
- verdict-authority §3, §4 (the verdicts and their application).
