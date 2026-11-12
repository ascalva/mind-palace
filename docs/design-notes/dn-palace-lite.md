---
type: design-note
id: dn-palace-lite
track: query-language
status: draft                  # provenance description, never a gate; the merge is ratification
implementation: partial        # the two switches, the repository source, the code instance, the hooks and the measurements landed 2026-11-09; the shared embedding service (§7.1) and the slim install (§7.2) are proposed, not built
created: 2026-11-09
updated: 2026-11-09
links:
  - docs/design-notes/dn-two-phase-ingestion.md       # an item is complete without its vector (ING-19 to ING-21); this note's starting point
  - docs/design-notes/dn-ingress-language.md          # the writer's rules, the table, the places, the library scripts
  - docs/design-notes/dn-corpus-instance.md           # a named instance (DI-2) and its runner; the embedder as the slow stage
  - docs/design-notes/dn-query-sentence-algebra.md    # the universe, `near`, the support and its notes
  - docs/design-notes/dn-code-ingest-pipeline.md      # the code embed lane this note leaves as it was
  - docs/experiments/palace-lite-2026-11-09.md        # the measurements of §6
  - papers/2026-11-09-palace-lite/paper.tex           # the article
supersedes: null
superseded_by: null
warrant: null
---

# The lite palace: the language model optional, the embedder optional

> Drafted on a branch from `origin/main` at `2b500e5e`. Every claim about code was read there or
> on the branch; every figure is from `docs/experiments/palace-lite-2026-11-09.md`, measured on
> this machine with the load named beside it.

## 1. The problem

Two-phase ingestion made the vector a derived field of an item: an item lands complete, its
bytes, label, lexical units, version, attestation and key, and the embed drain writes its vector
later (ING-19 to ING-21). That leaves three costs in place for an instance that does not need
vectors at all.

- The default instance's code stratum is a snapshot. Its code ingestion is off, because the code
  embed lane embeds every changed file through the embedder, and so a coding agent that asks the
  palace about the code reads files as they were at its last snapshot (2026-10-29), while ripgrep
  over the checkout finds them as they are.
- A small device cannot run an embedder beside the palace, and an instance that has no use for
  semantic similarity should not have to run one.
- A language model runs the dreaming, relation and curation passes. An instance whose job is
  lookup has no use for them either.

The palace should run lean: the language model optional, the embedder optional, and, for the
instances that do want vectors, one shared embedder in front of which the instances queue (§7.1).

## 2. Two switches

### 2.1 An instance that embeds nothing

`[embedding] enabled = false` declares an instance with no embedder. What follows from it:

- No embedder is built and no vector plane is opened. The factories refuse by name:
  `build_embedder`, `open_vector_store` and `open_curated_store` raise `EmbeddingOff` for such an
  instance, so a code path the profile did not anticipate fails with the reason instead of
  reaching for a server or making a directory.
- The readers that ask a plane (the writer's UNCHANGED check, the drain's pending set, the query
  engine's universe, the MCP surface's counts) are handed `NoPlane`, whose every read answers what
  an empty plane answers and whose every write refuses (`core/stores/noplane.py`).
- Every store lands as a lazy store lands under ING-19, its lexical units before its key, and
  stays so: no embedding is charged to the plan, no plane row is written, no drain is asked for.
  The embed job and `palace embed` say there is nothing to derive.
- No daemon runs for it. The daemon wires the embedder's consumers (the librarian, the code embed
  lane, the airlock's ranking), so `palace start` refuses such an instance by name; its sources
  sync on demand and by the hooks of §4.3.

### 2.2 A source that keeps no vectors

The same choice per source: `Source.embed = false` in the table. The writer decides per store,

    keeps_vectors(path) = [embedding] enabled  and  (the source that owns path).embed
    embeds_now(path)    = keeps_vectors(path)  and  not lazy
    lexical_witness(path) = lazy  or  not keeps_vectors(path)

so a store embeds before its key only when its item keeps a vector and the landing is not lazy;
the UNCHANGED check reads the lexical index when the store lands without a vector; and the drain
is asked for only by a lazy landing of an item that keeps one. An instance can then keep vectors
for its notes while its code lands lexically. Configured today for the code source:
`[ingestion.code] embed = false`. The drain never treats such an item as pending: the code's class
is not one of the plane's (`HOLDS`), and a lazy landing of it asks for no drain.

### 2.3 What each verb does without a vector

| verb | reads | without a vector |
|---|---|---|
| `near "t"` | the kernel column `clip(V·q̂)` | ranks the clause's vectorless nodes by the lexical index (BM25 over the same chunks the plane would hold), on a scale of its own, each hit labelled `ranked_by: lexical: the item keeps no vector`; the notes count pending and vectorless nodes apart |
| `diffuse S`, `reach S`, `walk … via S` | the backbone `S`, cosine at or above σ | `S` has no edge at a vectorless node; the answer is empty or covers the nodes with vectors, and the notes say so |
| `reach F`, `walk … via F` | the citation graph at the cut | unchanged; no vector is involved |
| `trace` | the version chain | unchanged; a file's chain grows by one version each sync that lands a change to it |
| `read` | the raw store, or git | unchanged; a landed repository file is read from the raw store by its digest |
| `witness` | the attestations and the edge stores | unchanged |
| `relate` | the signed relation edges | unchanged |
| `top`, `atleast`, `far`, `not`, `and`, `or`, `minus`, `then`, `within`, `over`, `assume` | fields and regions | unchanged; they compose whatever the verbs above produced |

A query never invents a vector: a node without one is ranked lexically and labelled, or reported.

### 2.4 The default instance

Nothing about it changes. `[embedding] enabled` and `[ingestion.code] embed` default to true, the
table holds no repository source unless the code lands lexically, and an instance that embeds every
item synchronously still opens no lexical index (`needs_lexical`). The `reference` place this note
adds is written by the operator's role alone.

## 3. The language model optional

The model runs the dreaming, curation and relation passes and the Ambassador's own chat. A lite
instance schedules none of them (`[dreaming] scheduled = false`, `[integrate] enabled = false`),
runs no daemon to wake one, and its sentence engine needs no model: every verb above is plain
arithmetic over the stores. The MCP server's `status` tool reports the embedder of such an
instance as `off` and never probes it.

## 4. The code instance

### 4.1 A repository as a source

A `repository` source is a git repository's files at a ref, read through git's object store and
never through the working tree (`core/ingest/repository.py`): `rev-parse` resolves the ref,
`ls-tree` lists the tree, one `cat-file --batch` process a batch reads the blobs. So no untracked
file, uncommitted edit, data directory or symlink target is read, and the files are the commit's
exactly. Git is told never to fetch (`GIT_NO_LAZY_FETCH`, `protocol.allow=never`), so a partial
clone's missing blob is an error, not a network request. The foundation's paths, the tool
directories, symlinks, submodules and binary blobs are not items.

Each file lands at `code/<name>/<path>` in the new `reference` place (the reference stratum, whose
class is `code`, a version chain per file), through `ingress/sync_repository.palace`: store every
file, retire every landed file the ref no longer has. Once a plan has stored every file it listed,
the commit is recorded as landed (`data/code/<name>.synced`), and `overview` reports how many
commits the ref has moved past it.

### 4.2 The instance

`config/instances/code.toml` declares the instance `code`: no embedder, no scheduled model, no
vault, transcripts, dialogue, secrets, effectors, backup or attestation keys, and one repository,
this one, at `main`. A named instance's state lived under `<checkout>/instances/<id>`, so the
corpus instance's data ended up inside the worktree that first ran it, where removing the worktree
would remove the data. `[instance] root` now lets a named instance declare its own root: an
absolute directory that the loader refuses inside any git working tree. The code instance's is
`~/.mind-palace/instances/code`. Every namespace derives from the declared root exactly as from the
derived one, and the sharing checks (`_refuse_shared`) hold against it unchanged. The default chain
refuses the key.

The repository is read through git alone, so the instance reads nothing any instance writes, the
default instance's data included, and starts, stops or calls no model server.

### 4.3 Keeping it current

Three mechanisms, by cost:

1. `palace repo-sync`, on demand: under the instance's supervisor lock, refused beside a live
   daemon. A re-run after no commit lands nothing.
2. The repository's own hooks. `.githooks/post-commit` already observes every commit on main for
   the code sensor; a pull that fast-forwards main commits nothing locally, so
   `.githooks/post-merge` now runs `repo-sync --if-landed` after every merge or pull on main, and
   the post-commit hook does the same after a commit there. `--if-landed` opens nothing until the
   instance has landed once, so its first sync stays the operator's, and a failed sync never blocks
   the merge.
3. In a daemon that embeds (the default instance with the code switch of §5), the `repository_sync`
   kind runs at housekeeping cadence and at startup in place of the code embed lane.

The hook is the recommendation: main moves only by a merge or a commit, the hook runs exactly
then, it needs no service, and its cost is the incremental sync of §6.2. A watcher on the
repository would wake on every working-tree write, and a timer would sync on a schedule unrelated
to the commits.

### 4.4 Serving it to an agent

The MCP server runs against the instance by its overlay:

    MIND_PALACE_OVERLAY=config/instances/code.toml uv run --project <checkout> python <checkout>/scripts/palace_mcp.py

The read is the one `query` tool; a lookup is `top 5 near "<words>" over reference`, `read
"code/<name>/<path>"`, `trace "code/<name>/<path>"`. The server's write tools spool requests that
no daemon of this instance lands. With `--role guest` it serves the read-only principal instead
(`dn-guest-principal`): `query` and `overview` alone, no write tool, and a grant with no version
plane, so `trace` is refused there and the other lookups answer as above.

    MIND_PALACE_OVERLAY=config/instances/code.toml uv run --project <checkout> python <checkout>/scripts/palace_mcp.py --role guest

## 5. The default instance's code, without embedding

Once this merges, the default instance can land its own code lexically while its notes keep their
vectors. The lines, in its per-machine overlay:

    [ingestion.code]
    enabled = true
    embed = false

With no repository declared, the source is the checkout at `main`, named after its directory. The
daemon then runs `repository_sync` at housekeeping cadence and at startup instead of the embed
lane and its history backfill; the plane gets no code row and the embedder no code text.

## 6. Measurements

Recorded in `docs/experiments/palace-lite-2026-11-09.md`, aggregates only.

### 6.1 Ingestion

On this machine with nothing else busy (one-minute load 1.8 to 2.2), through the CLI with the
interpreter's start included:

| run | effects | wall s | peak RSS MB |
|---|---|---|---|
| full ingestion of the repository | 2,015 files landed | 10.9 | 271 |
| again, no commit | all unchanged | 2.5 | 215 |
| after one commit (six files) | 6 landed | 2.6 | 217 |

The instance at `main` holds 2,021 files as 27,235 lexical units (2.5 million postings over 46,239
terms) in 112 MB of stores: the lexical index 86.6 MB, the raw store 22.4 MB, everything else under
4 MB, and no vector store. The lexical stage is two thirds of a full ingestion (7.4 of 10.9 s); a
sync that lands nothing spends 0.47 s in the writer and the rest starting up, evaluating the script
and reading the tree through git.

### 6.2 Lookups against ripgrep

Eleven questions with answers declared before the first run, asked as `top 5 near "<text>" over
reference`, against the pattern an agent would give ripgrep over a checkout of the same commit:

- the palace ranks a correct file in its top five for 8 of 11 (rank 1 once, 2 five times, 3 and 4
  once each); ripgrep's output holds a correct file for all 11, and prints a median of 8 files,
  from 1 for an exact definition to 18 for a phrase;
- median latency, warm: the palace 163 ms, ripgrep 50 ms; the first query of a process 707 ms;
- what outranks an answer is the text that talks about it most: tests, which name the identifiers
  they exercise, then design notes and papers. The three misses are of that kind (the drain's laws,
  the module that computes the spectral gap, the module that takes the supervisor lock);
- a file's history: `trace` gives the versions the instance has landed (one, for a file unchanged
  since the first sync), where `git log` gives every commit (nine).

### 6.3 The MCP server

Spawned as an MCP client spawns it, over the instance: `initialize` answered 0.71 s after the
spawn, the first `query` at 1.30 s, a second at 1.48 s (medians of five); peak resident memory 168
MB. No vector store, embedder or model client is constructed.

## 7. Proposed next steps (not built)

### 7.1 One shared embedding service

The instances that want vectors share one embedder through a service with a queue in front of the
server, so that no instance owns the embedder and none can starve another.

- **Priorities.** Three classes, served in order: an interactive query's text (one short input, a
  person or an agent waiting), a landing's chunks (an item lands lazily and waits only for its
  vector), and a backfill (the drain over a corpus, a re-embedding after a model change). A higher
  class preempts at the batch boundary, never inside a request. The measured server takes one
  stream of 64 chunks at 26 chunks a second and gains at most 15% per added stream while every
  other caller's latency grows by the queue in front of it, so the service keeps one stream for the
  lower classes and reserves a slot for queries.
- **Per-instance fairness.** Within a class, instances are served by deficit round robin over
  their queues, weighted by a declared share, so a corpus backfill of a hundred million chunks
  cannot hold the embedder from another instance's landing for days.
- **Backpressure.** Each class has a bounded queue. A query past its bound is answered lexically
  and labelled, as the profile here already does; a landing past its bound lands lazily and its
  vector waits for the drain; a backfill past its bound is told to retry after the queue drains.
  Nothing blocks a writer.
- **Identity.** Each request carries the embedder fingerprint the instance's plane records (model,
  template, dimension), and the service refuses a mismatch, so two instances sharing a server
  never mix geometries.

### 7.2 A slim install for small devices

The lite profile needs SQLite, NumPy and git, and no LanceDB, no model client and no embedder. A
slim install would make the vector store and the model clients optional extras of the package, so
that a device with a gigabyte of memory runs the code or notes instance of this note, its own
lexical index, and asks the shared embedding service of §7.1 over the network when it wants a
vector. The measured footprint of §6 is the budget.

### 7.3 What the code instance does not do yet

- **Identifiers split.** The tokenizer splits on underscores, so `embed_fitting` is the two terms
  `embed` and `fitting`. A code tokenizer that also keeps the whole identifier would sharpen
  definition lookups; it waits for the tokenizer identity of the embedder study's branch, so the two
  changes to the tokenizer do not collide.
- **No citation graph.** The code sensor derives the import and citation edges per commit over the
  whole history; on the default instance that ledger is several gigabytes. A head-only observation
  of the code instance's repository would give `reach F` its edges at the landed commit.
- **History from the first sync.** `trace` shows the versions the instance landed, one per sync
  that changed a file; git's history before the first sync stays git's.
- **`over reference` must be said.** `near` with no `over` reads the mirror by the precedents, and a
  code instance has no mirror; an instance's own default strata would remove the need.

## 8. Laws

No law changes. ING-19 is the landing of every store here, with the drain never asked; ING-20 and
ING-21 have no pending item to speak of in an instance that embeds nothing; the writer's rules R1
to R8 hold for the `reference` place as for the others, the repository source owning its space
(R8) and retiring only what its ref no longer has (R7).
