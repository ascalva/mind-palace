---
type: design-note
id: dn-ingest-door
track: query-language
status: draft                  # provenance description, never a gate; the owner's merge is ratification
implementation: building       # DO-0 proved, DO-1 to DO-4 built 2026-11-05 (the command sort, the landing order, the spool, the daemon's drain and handlers, the surfaces, the audits folded); DO-5 entered the ledger; DO-6 follows (§4)
created: 2026-11-05
updated: 2026-11-05
links:
  - docs/brainstorms/the-door.md                          # THE WARRANT — the owner's seeds, verbatim
  - docs/design-notes/dn-query-sentence-algebra.md        # the language this extends: sorts, QSA-5 admissibility, the overlay
  - docs/design-notes/capability-scope-algebra.md         # RATIFIED — the scope lattice; the authority coordinate A = P × W_Σ × W_world
  - docs/design-notes/ingest-identity-and-amendment.md    # RATIFIED — append-only log, content-addressed projection, versioned amendment
  - docs/design-notes/vector-membership-store.md          # the shared plane: atoms, occupancies per class, one writer by lock
  - docs/design-notes/dn-supervision-and-liveness.md      # the worker protocol: the compute half returns batches, the supervisor lands them
  - docs/design-notes/temporal-code-corpus.md             # keep-and-link: a changed version supersedes, never deletes
  - docs/design-notes/global-event-clock.md               # every store append is an event; cuts compose (CLK-2)
  - docs/design-notes/agent-taxonomy.md                   # the witness law: a proven edge is one record's image
  - docs/design-notes/vault-sync-and-capture.md           # capture: the owner's turns and the model's, split by the caller, never by text
  - docs/design-notes/chat-sensor.md                      # CS-2: everything the sensor lands is observed; promotion is human
  - docs/design-notes/plane-principals.md                 # the principals, the handoff directory (2770), who writes data/
  - formal/Palace/Door.lean                               # the laws, machine-checked (formal/Palace/Door/Defs.lean the model; PalaceTest/Door.lean the attacks)
supersedes: null
superseded_by: docs/design-notes/dn-door-language.md   # in part: D1's sum of source kinds, D2's command table, D7, D8 (in part)
warrant: docs/brainstorms/the-door.md
---

> **Superseded in part, 2026-11-05.** The owner's correction (the warrant's last passages): the
> language should know no ingestion path, and every path should be written in it. The second
> form, `dn-door-language`, replaces this note's command table (D2), its per-command landers
> (D7) and refusals (D8, in part) with a generic write language and scripts. The door (D3), the
> landing order with the key last, the answer on ACID (D5), the laws (D9) and the findings (§9)
> stand.

# The door — ingestion as sentences: one operation, one writer, embedding the serial stage

> Composed on the Lean-ladder session (Fable 5.1, 2026-11-05) from the owner's seeds of the same
> day (the warrant), on the owner's direction that the design and its proofs come first and the
> implementation follow them, with agents reviewing, auditing and validating along the way. This
> is the second draft: the first was audited against the code by a review agent, whose nineteen
> findings are folded in, three of them defects in the code as it stands (§9). Agent-drafted,
> filed `draft` on a branch; the owner's merge is ratification. Nothing in `core/` changes by this
> note alone; what it licenses is in §4. Every nontrivial claim carries a grade: `[THEOREM]` is
> machine-checked in `formal/` and names its declaration; `[ESTABLISHED]` is a ratified note's or
> Mathlib's; `[DERIVED]` is argued here from those; `[INFERENCE]` is a design call with a named
> falsifier. Code claims were read on `build/ingest-door` at `93bf66a`.

## 1. Purpose and scope

### 1.1 What this note decides

The query language gains a sort of **commands**: `do <command>` is a sentence whose value is a
receipt, not a field. Ingestion becomes **one operation** over typed sources, with today's front
doors as its cases. Every surface that acts on the palace, the CLI, the Ambassador's tools, the
watchers, does so by **writing a request the daemon enqueues**; the **supervisor is the only
writer**, readers are unlimited, non-conflicting commands may run in parallel, and the only
expensive serial stage is **embedding**. The decisions are D1 to D9 in §3; the laws they rest on
are family XII, DOR-1 to DOR-12, in §3.9, machine-checked in `formal/Palace/Door.lean` and
attacked in `formal/PalaceTest/Door.lean` before any code relies on them, all but DOR-4, the
queue's discipline, which the import ratchet is to check (DO-5).

### 1.2 Out of scope

The content of ingestion is unchanged: the chunkers, the code parser, the embedder, the plane's
schema, the catalog and version stores. The owner-gated operations (purge, re-key, reset,
re-embed) stay the owner's CLI with `--confirm` and are **not in the grammar** (§3.8). The
effectors (the "hands") stay flag-off at every tier; a command here never reaches the world
(`W_world = NONE`). The edge readers (the Open WebUI container, the opencode sessions) stay edge
processes; only the core half of a dialogue sync is a command (D7). The Ambassador's bookkeeping
tools (tasks, reminders, status) are reads and writes of the task ledger, not of the palace, and
get a verb of their own later. The worker protocol's compute/land split (D4) is designed here and
built later.

### 1.3 What is proved, what is cited, what is open

Proved, in `Door.lean` on the keyed model (`Door/Defs.lean`: rows, chains, and each identity's
key, the catalog's digest the UNCHANGED check reads; a guarded `ingest`; a command's steps with
the key last), built under `--wfail`, seventeen attacks and eleven controls green (`PalaceTest/Door.lean`,
seeds 245 to 272): DOR-1 (a command is admissible iff a granted plane above its scope carries the
write bit, so a read-only grant admits no command; the Ambassador's grant as written admits a
projection-event command and refuses a commit-clock one), DOR-2 (extensive, idempotent, monotone
on the rows of sound states; a chain only grows), DOR-3 (ingests of distinct identities commute, a
batch of them lands the same state in any order and lands nothing when run again), DOR-5 (a
re-ingest of held content embeds nothing; two commands sharing an atom pay once; a batch of fresh
commands on distinct identities embeds its distinct new atoms), DOR-6 (the receipt names the rows added and the digest that is the
chain's new head, and nothing else), DOR-7 (with the key last, a
fresh run interrupted after any step converges under re-run, in the model's stage order and in
any order of the steps before the key, the code's among them; a key written while some of the
command's rows are not held is never repaired, first or after the plane's rows as the audit's
defect 1 wrote it), DOR-8 (commands on one identity land in the order of their chain, and two orders give two
chains), DOR-9 (the steps of fresh commands on distinct identities run to the batch's state in
any order), DOR-10 (a schedule that orders each identity's landings and keys as the list does
lands the batch, repeated identities allowed, when each command is fresh at its turn; with the
guard, a schedule of the commands that land lands the whole list), DOR-11 (a batch of fresh
commands on distinct identities stopped anywhere in a parallel run, each command after a prefix
of its own steps, converges under re-run; with repeated identities, a serial run stopped inside
a command converges when that command and the ones after it run again, and not when the whole
batch does), DOR-12 (every state a key-last run passes through is sound for its own command, and
a batch on distinct identities stopped anywhere is sound for each of its commands when the state
before was, so readers that trust the key need no lock, at the ledger's grain).
A proof audit (an agent, 2026-11-05) found the first model keyless, so that DOR-7 held
for the old order as much as the new; the keyed model is its result. The model's rows are the
ledger-grain rows (the raw store, the plane's atoms and occupancies, the versions, the
attestations); the reconciled view the readers see is derived from them. Where the code today
departs from the model, §9 says so and §4 brings the code to the model. Cited: QSA-5, the plane's noninterference (vector-membership-store A3.5), CLK-2,
the witness law, CS-2. Open (§8): the Ambassador's write planes, the `wait` adjective, the
authored half of `relate`, the MCP aliases.

### 1.4 The bar

The owner's standing bar, applied here. **Correctness**: every decision rests on a law in §3.9,
machine-checked before code relies on it; where the code departs from the model today, the
departure is named as a defect (§9) with its falsifier, not papered over. **Security**: the
owner's operations are unrepresentable in the grammar, not refused; no word of a sentence ever
names a provenance class or a role, the surface that spoke binds both (D3); the write bit governs
admissibility at the door and again at the writer; text never enters the queue. **Efficiency**:
the serial stage is embedding alone, it embeds only atoms the plane lacks, the queue coalesces
repeated idempotent commands, and writes on distinct identities need no ordering (DOR-9), so the
dispatcher may run them in parallel. **Verifiability**: a command returns a receipt, the receipt
names what landed and nothing else, `witness` reads it back, and the attestation chain holds it.
**Flexibility**: a source kind is a row in one table and a case of one sum type; a new kind adds
a row; every surface speaks the same sentence. Elegance is what is left when the five are met by
one mechanism rather than five.

## 2. What exists — the inventory this note rearranges

**The front doors, and one core.** Every prose path runs through `ingest_note` (raw store add,
content-addressed, then chunking) and `index_records` or `index_amendment` (embed only the atoms
the plane does not hold, land, reconcile and supersede), then a catalog record, an attestation,
and for notes a version row. The paths differ in the source, the identity, the provenance class
and the ledgers they touch:

| path | module | source | identity | class written | ledgers after landing | trigger today |
|---|---|---|---|---|---|---|
| the owner's notes | `core/ingest/sync.py::VaultSync.sync_path` | a vault file | `source_path`, `doc_id` via the catalog | `authored-solo` | catalog, attestation (`vault_watcher`/`ingest_note`), versions | the watcher → `vault_sync` job; `palace vault-sync`; MCP `sync_notes` |
| dialogue turns, the model's | `core/ingest/dialogue.py::DialogueCapture.capture_turn` | a turn's text | `dialogue/<conversation>/<turn>` | `observed` (the caller binds it: MCP `capture` passes `assistant`) | catalog, attestation (`ambassador`/`capture`) | MCP `capture` |
| dialogue turns, the owner's | the same, called by `dialogue_sync_now` with the edge reader's role; the inbox's `capture_sink.capture` | the handoff file `data/handoff/dialogue/<source>.json`; an inbox message | `dialogue/<conversation>/<turn>`; a timestamp-keyed path for the inbox | `authored-dialogue` | catalog, attestation | `palace dialogue-sync`; the heartbeat; the `ambassador` inbox job |
| the system's own docs | `core/ingest/curated.py::ingest_curated` | a repo markdown file | repo-relative path | `curated` | catalog, attestation (`ingest_curated`), no idempotence key (§9) | `scripts/ingest_self_knowledge.py` |
| papers | `scripts/curate_local.py` (a manifest; `core/research/persist.py::persist_keepers` has no caller) | a paper's chunks | `reference:<ref>` | `curated` (the curated plane) | the curated store, no attestation | the owner, inline |
| research | `scheduler/research.py` via the airlock | criteria | — | **nothing**: it emits, collects and ranks, and writes no paper | — | the `research` job |
| code, the embed lane | `core/ingest/code_corpus.py::CodeCorpusSync.sync/backfill` | a blob at a commit | `(path, blob_sha)` fibers | `code` atoms and memberships | memberships (keep-and-link); no attestation | `code_sync`, `code_backfill`, `code_rebuild` jobs; `palace code-seed`; `palace lanes code-embed` |
| code, the sensor | `ops/code_sensor.py` | the repo at a commit | the commit | code observations, **reference edges** (the `F` fibers), the snapshot ledger | the observation and reference stores | `palace lanes code-observe`; `scripts/snapshot_code.py`; never a daemon job |
| transcripts | `ops/chat_sensor.py` | a session transcript | `(session, turn_index)` | `observed` (the chatlog) | chatlog, then `chat_events`, `integrate` (causal edges) | `chat_sync` job; `palace ingest-chat` |

**The queue's discipline, and its exceptions.** The scheduler's docstrings state the rule: "all
store mutation happens on the single supervisor writer (the queue's discipline)". The code
honours it for the jobs, and the CLI's on-demand verbs refuse beside a live daemon
(`_refuse_if_live`: `dream`, `dialogue-sync`, `reembed`, `lanes`, `relate`, `vault-sync`). The
processes that write a palace store today, read off the code:

- the daemon's supervisor: `vault_sync`, `chat_sync`, `code_sync`, `code_backfill`, `code_rebuild`,
  `chat_events`, `integrate`, `dream`, `curate`, and the `ambassador` inbox job, whose capture
  sink writes the owner's message as `authored-dialogue`;
- the CLI: `ingest-chat`, **unguarded**, writes the raw store and the chatlog beside a live
  daemon; the guarded verbs when the daemon is down; `reembed --confirm` resets the vector store;
  `lanes code-observe` writes observations and reference edges; `lanes code-embed` runs the embed
  lane inline;
- the stdio MCP server (`scripts/palace_mcp.py`): `capture` and `link`, **always inline**;
- the Open WebUI bridge, a second MCP process (`scripts/palace_mcp_handoff.py`): `capture`,
  `sync_dialogue`, `sync_notes`;
- the heartbeat (`palace tick`, a LaunchAgent): the dialogue sync, guarded;
- owner scripts with no live-daemon guard: `ingest_self_knowledge.py`, `ingest_founding.py`,
  `curate_local.py`, `ingest.py` (a full rebuild that resets the vector store),
  `migrate_chunk_keys.py`, `migrate_provenance_split.py`, `snapshot_code.py`, `talk.py` (whose
  runtime completes QUEUED jobs without claiming them), `purge_raw.py`;
- `scripts/watch.py`, a standalone supervisor, exclusive with the daemon under its lock.

Second writers **while the daemon is live**, then: `ingest-chat`, `capture` and `link` from two MCP
processes, and the unguarded scripts. The plane serialises its own writes by an advisory lock and
SQLite serialises the rest, so nothing corrupts; the code lane's physical Lance add has no lock
and is safe only because its writers are the daemon and the guarded `lanes code-embed`. The
single-writer claim is a discipline today, not a property. `[DERIVED — read off the code; the
audit of 2026-11-05]`

**The serial stage.** `index.py::embed_new` asks the plane which atoms it holds
(`store.known_atoms`, a read), embeds only the distinct texts it does not, in one batch, through
the one embedder slot the memory ceiling admits. Acquiring bytes, chunking and parsing are pure
per source; landing is one short critical section under the lock. The owner's reading is right:
embedding is the only expensive serial stage. `[DERIVED]`

## 3. Decisions

### D1 — One operation over typed sources

`ingest : Source → Receipt`, where a `Source` is one of seven kinds, each fixing what the five
stages do:

| kind | acquire | identity | class written | derive | land | ledgers |
|---|---|---|---|---|---|---|
| `note <path>` | the vault file's bytes | `source_path`, the catalog's `doc_id` | `authored-solo` | prose chunks | occupancies, supersede the old version | catalog, versions, attestation |
| `turn <conversation> <id> "<text>"` | the text | `dialogue/<conversation>/<id>` | `observed`, always (D3 binds the owner's turns elsewhere) | prose chunks | occupancies | catalog, attestation |
| `doc <repo path>` | the checkout's file | repo-relative path | `curated` | prose chunks | occupancies | catalog, attestation |
| `paper <ref>` | the manifest's clean chunks (the `curate_local` path) | `reference:<ref>` | `curated` (the curated plane) | the manifest's chunks | the curated store | attestation (new: today none) |
| `code [<commit>]` | the blob at the commit (HEAD by default) | `(path, blob_sha)` | `code` | L0a/L0b/L1 code chunks | atoms and memberships, keep-and-link | attestation (new: today none) |
| `observe code [<commit>]` | the repo at the commit | the commit | code observations | the sensor's readings | observations, reference edges (the `F` fibers), the snapshot ledger | attestation (new) |
| `transcript <session>` | the session's transcript | `(session, turn_index)` | `observed` | utterances, no embedding | the chatlog | chat events, causal edges |

The five stages are the same for every kind: **acquire** (read the bytes or rows), **address**
(the raw store's content address, `raw.add`, append-only, write-then-rename), **derive** (chunk
or parse, a pure function of the bytes), **embed** (only the atoms the plane does not hold,
`embed_new`), **land** (one transaction: occupancies or memberships, reconcile and supersede;
then the ledgers; then the attestation whose output hashes are the digests landed; and **last,
the idempotence key**, the catalog's digest for the path, so that a crash before it leaves a run
the next run repeats in full, D5). Acquire and derive are per-source and independent; address,
embed and land are the writer's. Nothing here changes a chunker, an identity rule or a
provenance rule: the provenance class is fixed by the kind, and for turns by the surface that
spoke (D3), never by a word of the sentence or the text (vault-sync-and-capture: the owner's
turns and the model's are split by the caller; chat-sensor CS-2: everything the sensor lands is
observed, promotion is human). `[DERIVED — a restatement of the paths over one signature]`

### D2 — The action sort

The grammar gains one production and the sorts one member:

```
sentence := "do" command | <the query sentence of dn-query-sentence-algebra §2.3>
command  := "ingest" source | "sync" lane | "observe" "code" [atom] | "dream" | "curate"
          | "relate" ["pairs" NUMBER] | "link" atom atom relation | "capture" STRING ["in" WORD]
          | "research" STRING
source   := "note" atom | "turn" WORD WORD STRING | "doc" atom | "paper" atom | "code" [atom]
          | "transcript" WORD
lane     := "vault" | "dialogue" | "chat" | "code"
relation := "supports" | "contradicts" | "contextualizes"
```

A command is a **whole sentence**: it takes no connective and no adjective. Its value is a
receipt (D5), and the state it changes lands later, so `do ingest note x then near "x"` would
read the state before the ingest and lie about it; the grammar refuses the composition rather
than defining it. The sort is `EVENT`. There is **no role word**: a `turn` is observed, a
`capture` is observed, and the owner's turns reach the palace only through the dialogue handoff
file the edge reader writes and the lander reads (D7). One word is reserved, `do`; the command words are
read in place after it, so a bare `WORD` atom such as `code` or `vault` keeps its meaning
everywhere else in a sentence (DO-1). `[INFERENCE — falsifier: a composition a consumer needs that cannot be written
as two sentences]`

**Typing.** Each command requires a scope with the **write bit** (`W_Σ = 1`, the authority
coordinate of `capability-scope-algebra` §2.2) on the strata it writes, at the window `now`, with
the fibers it adds and the clock of the stratum:

| command | strata written | fibers | clock | privilege |
|---|---|---|---|---|
| `ingest note`, `sync vault` | `mirror_authored` (the projection of the owner's note) | — | projection event | — |
| `ingest turn`, `capture` | `observed` | — | projection event | — |
| `ingest doc`, `ingest paper` | `curated` | — | projection event | — |
| `research` | `curated` (what it may later persist) | — | projection event | propose; the one outward path (§8) |
| `ingest code`, `sync code` | `reference` | — | commit | — |
| `observe code` | `reference` | `F` | commit | — |
| `ingest transcript`, `sync chat` | `dialogue_transcript` | `C` | commit | — |
| `dream`, `curate` | `interpreted` | — | projection event | propose |
| `relate` | `interpreted` (the authored half of today's detector moves to the vault lane, §8) | `S` | projection event | propose |
| `link` | `interpreted` | `S` | projection event | propose |

Admissibility is QSA-5 unchanged: a sentence is admissible under a grant iff each clause's
required scope lies under some granted plane, and a command's required scope has the write bit,
so a plane admits it only if the plane's authority carries the bit over those strata. A read-only
grant admits no command. `[THEOREM — DOR-1, Door.lean::command_admissible_iff,
command_needs_a_writing_plane, readonly_admits_no_command]`

Under the Ambassador's grant as it stands (`core/query.py::AMBASSADOR`): the first plane, at the
projection-event clock, carries propose and write over the mirror, the curated, the interpreted,
the dialogue, the observed and the reference strata and their refinements, so every
projection-event row above would be admissible to the Ambassador, `ingest note` and `dream`
included; the second plane, at the commit clock, carries no write bit, and the order is false
across clocks, so the commit-clock rows (`code`, `observe code`, `transcript`, `sync chat`) are
not. The code's own comment beside the grant, "projection-write into the dialogue stratum only",
describes a narrower plane than the one written. That is the grant's statement today, enforced
nowhere; the door enforces it, which is the reason to narrow it (§8, the owner's). `[DERIVED —
read off the grant; the audit confirmed it]`

### D3 — The door: every action is a request, the daemon enqueues, one writer

A command's evaluation **writes no store and no queue row**. A surface compiles the sentence
under its grant (the first check), and if admissible writes a **request** into its own spool, a
per-principal directory under the interface handoff directory (`cfg.interface.handoff_dir`,
today `data/handoff/door/<role>/`; the agents' spool group-writable and sticky under a dedicated
group, the operator's the owner's account's alone, §5), holding the sentence, the text a
`capture` or `turn` carries, and a request id. The daemon drains the spools each tick
(`scheduler/door.py`): it stages its own copy of each request and enqueues one job per request
with the **role bound to the spool it came from**: the filesystem is the authenticator, and no
field of the request names a role or a class. The job's payload is the request id and the
sentence's **digest**; the text stays in the staged copy, so `queue.sqlite` never holds corpus
text (the queue's own rule). The supervisor's handler compiles the staged sentence **again**,
under the grant the spool's role names (the second check, the one that counts), performs it
under the single writer, and writes the receipt in the spool's `receipts/`. A request forged into a
spool is bounded by that spool's role; a request in no spool is nothing. Readers never take the
writer's lock: the plane's lock is a writers' lock, SQLite's readers do not block, and the
language's queries stay as they are. The surfaces that write today (D7) become spool writers:
the three writer processes beside the daemon become none. `[INFERENCE — falsifier: a store
mutation reachable from a process other than the supervisor after D7 lands; the import ratchet
can name it once the readers open stores through a read-only constructor family (DO-5), which
the ratchet today does not distinguish]`

### D4 — The pipeline and the serial stage

The five stages of D1 split onto the worker protocol of `dn-supervision-and-liveness` §2.5 as
they are: **acquire** and **derive** are the compute half (pure per source: bytes in, chunks
out; the worker holds no store, so it neither addresses nor asks the plane what it holds),
**address**, **embed** and **land** are the supervisor's half (the raw store's add, the plane's
`known_atoms` read, the one embedder slot, one transaction, the ledgers, the attestation, the
key). Today every kind runs in-process on the supervisor (`worker_mode = "inproc"`), which
satisfies D3 already; the split is what lets several sources be acquired and derived at once
while the embedder, one slot under the ceiling, is shared in batches and the writer lands each
batch. The cost of a batch is its distinct new atoms, counted at the lander: `embed_new` embeds
each text the plane does not hold once, so re-ingesting an unchanged note costs no embed and two
notes sharing a chunk cost one. `[THEOREM — DOR-5, Door.lean::embeds_ingest_twice_zero,
Door.lean::embeds_share]`

### D5 — Idempotence, coalescing, the receipt; and ACID, stated honestly

Ingestion is idempotent at every layer the ledgers have: the raw store is content-addressed, the
plane holds one atom per distinct text, landing reconciles the fiber, the version store records
only a change. So `ingest` is a **closure operator** on store states: extensive (the state after
holds the state before), monotone on the rows between sound states (a larger state before gives
a larger state after; a chain only grows, in the prefix order), idempotent (running it again changes nothing, since its key names its
digest), and ingests of distinct identities commute, so a batch of them lands the same state in
any order, and lands nothing when run again. `[THEOREM — DOR-2, Door.lean::ingest_extensive,
chain_prefix_ingest, ingest_monotone, ingest_idempotent; DOR-3, Door.lean::ingest_comm,
ingest_batch_perm, batch_idempotent]` The model's state is at the ledger grain: the rows the
append-only stores hold (the raw store, the plane's atoms and occupancies, the versions, the
attestations, the chatlog, the plane's supersession log), each identity's chain, and each
identity's key. The stores that reconcile in place (the catalog's upsert, the plane's `current`
flip and `held` cache, the edge store's replace) derive the view the readers see from that ledger
and are not modelled; the plane keeps its superseded occupancies, so the ledger grain is also
what it physically holds. Two commands on distinct identities are not disjoint in the physical rows: two notes
sharing a chunk both touch the shared atom and its `held` cache; they commute because the plane's
lock makes each landing atomic with respect to the other, which is why the lock stays under
parallel dispatch (DOR-9 is about the compute halves and the order of landings, not about two
landings at once).

The queue coalesces a queued job with a waiting one of the same kind and payload, for the kinds
declared idempotent and only those (`JobQueue.enqueue`'s four properties, bp-101 and bp-109:
only QUEUED rows, the key is `(kind, payload)`, the first row wins and keeps its age, a
checkpointed row is not a target; the set deliberately excludes `dream`, `curate` and
`research`, whose re-run after a crash is a double execution). The door keeps **today's kinds as
the queue's kinds**: a sentence compiles to a kind and a payload (`do sync vault` → `vault_sync`;
`do dream` → `dream`; `do ingest note x` → an `ingest` kind with the request id), so the router's
tiers and priorities, the pinned set and the orphan sweep keep their meaning, and idempotence is
a predicate of the kind, as now; `act` is the dispatcher's name for the family, not a kind. The
payload is the role, the request id and the sentence's digest (the text never; the file named
by the id holds it), and for today's kinds their usual payload, so a `do sync vault` coalesces
with the watcher's row and two different door commands never do. The **receipt** is the request id, then
the job id when enqueued, then the attestation the landing emitted, whose output hashes are
exactly the digests landed; the receipt of a capture or a note's ingest names the attestation
ids under `attestations`, and `witness "<attestation id>"` returns the record (the branch after
the reference edge's origin and the causal edge's own id; a hit of stratum `door`). In the model the
receipt is a function of the source, the rows it adds and the digest it lands, as the
attestation's output hashes are: a fresh command's state after is the state before plus the
receipt's rows, the receipt's digest is the chain's new head, and on a sound state every row it
names is held. `[THEOREM — DOR-6, Door.lean::receipt_complete, receipt_head,
receipt_rows_subset]`

**Is it ACID, and must there be one writer?** The owner's question, answered on the stores as
they are. *Atomicity* holds per statement and per store: SQLite's transactions, the plane's one
`BEGIN IMMEDIATE` for occupancies and supersession, a LanceDB write as one version. It does
**not** hold across the stores, and it should not pretend to: an ingest touches the raw store,
the plane, the catalog, the version store and the attestation store, five files, and a crash
between two of them leaves a prefix. What replaces cross-store atomicity is **crash
convergence**: the stages are ordered so that every prefix is a consistent state (an atom nobody
references is dormant geometry, an occupancy names an atom that exists, an attestation names
digests the raw store holds), every stage is idempotent, and the **idempotence key is written
last**, so the next run of the same command repeats everything after the crash and lands exactly
what the interrupted run would have; with the key written first, a run interrupted right after
it is never repaired, since the next run reads the key and lands nothing. `[THEOREM — DOR-7,
Door.lean::ingest_prefix_converges, ingest_after_nonkey; the controls
Door.lean::key_first_does_not_converge, key_early_does_not_converge]` The code before this note
had the key in the wrong place: `sync_path` and `capture_turn` wrote the catalog's digest, which
is what the UNCHANGED check reads, before the attestation and the version row, so a crash between
them was never repaired, and `ingest_curated` had no key at all and re-attested on every run (§9,
defects 1 and 2). DO-2 fixed the order. The code writes the version row before the attestation,
an order the model's stages do not have, and `ingest_after_nonkey` covers it; the falsifier is a
crash injected between the catalog record and the version record, then a re-run, which must
write the version row. Three windows stay outside the law, each in §9: a crash inside a rename's
landing appends its version twice (item 1), one between a revert's version row and its
attestation loses the attestation (item 46), and a re-run does not repair the `held` cache
(item 7).
*Consistency* is that stage order, which the plane already enforces for its own three writes
(vector-membership-store's D8 order: atoms, then occupancies and the supersession edge in one
transaction, then the `held` cache; the cache is re-derivable and `repair()` rebuilds it, which a
crash between the second and the third write needs, since the UNCHANGED check would otherwise
skip it). *Isolation* is where the owner is right to doubt the usual rule. The reconciled state
is a function of the ledger, and two commands on **distinct identities** (two notes, a note and a
paper, two commits) commute: any interleaving of their stages lands the state of any serial
order (DOR-9), and the lock makes each landing atomic. Two commands on **one identity** (two
versions of a note) do not commute, and must not: their serial order is the document's chain,
the one ordered thing in the system (ingest-identity-and-amendment §4A). That is
conflict-serializability by identity, with the chain as the serial order: a schedule that
orders the landings on each identity, and its keys, as the queue did lands the serial batch, and
a permutation that does not lands another chain. The guard is the one read in a landing, and it
reads the key; the model has no reads, so the theorem holds for schedules whose guards read the
serial key, and the queue makes every schedule one by running the commands on an identity whole,
one after another (a guard read early decides otherwise: `early_guard_skips`). Across identities
anything may interleave. `[THEOREM — DOR-3, DOR-8, DOR-9, DOR-10, Door.lean::ingest_comm,
ingest_batch_perm, same_identity_orders_the_chain, same_identity_not_comm, run_perm_of_disjoint,
run_eq_of_cls_filter, serializable, serializable_landsOf; the controls
serializable_needs_the_order, early_guard_skips; the reads clause is CLK-2, cited, not a theorem
of this model, which has no reads]` *Durability* is the stores' own: the raw store's
write-then-rename (without an fsync today), the catalog's, the plane's and the queue's WAL
commits, the rollback journals of the versions, attestations, edges, derived, chatlog, chat event
and causal edge stores, plus the one property a database does not give: no command deletes, and
the ledger-grain stores are never overwritten, so the state at every cut is recoverable from the
ledger.

So the mathematics does not require one writer; it requires one order **per identity** and one
embedder. One writer process stays the design (D3) for three reasons that are not mathematical:
the request spool binds a role to a principal and the queue to the daemon, a read-only
constructor family lets the import ratchet name any other writer (DO-5), and one read-modify-
write that two writers would race is in the code today: `VersionStore.record` reads the current
sequence and inserts the next in a second statement, outside a transaction, so under two writers
the same `(doc_id, version_seq)` could be allocated twice and the second insert would fail on the
primary key (the catalog's upsert is one statement and atomic; its check-then-act is `sync_path`'s
UNCHANGED test, which D1's key order makes safe). Relaxing to several writers is therefore
`BEGIN IMMEDIATE` around each per-identity read-modify-write and no change to the laws.
`[DERIVED — read off core/stores/versions.py and core/stores/catalog.py]`

**Many readers, one queue, parallel dispatch.** The owner's refinement, taken as stated. Readers
are unlimited and need no coordination: a query is a function of a cut of the event clock, every
ledger only appends above it, the reconciled stores change under a lock the readers never take,
and the stage order keeps every prefix consistent: every state a key-last run passes through is
sound for its own command, and a batch on distinct identities interleaved in any order and
stopped anywhere is sound for each of its commands when the state before was, so a reader that
reads a version only when the catalog's key names it sees the version whole or not at all. That
is soundness at the ledger's grain: the reconciled stores the readers go through (the catalog's
upsert, the plane's `current` flag and `held` cache) are not in the model. `[THEOREM — DOR-12, Door.lean::sound_prefix, sound_after_prefixes; the control
key_first_unsound]` Actions go through one **central queue**,
which is the serializer: the order of two commands on one identity is the order the queue
landed them in, and that order is the chain. The dispatcher may run queued commands **in
parallel when their identity sets are disjoint**, highest priority first, then any further queued
command whose identities meet none of the running ones (a greedy independent set by priority),
and the stages of such commands may interleave arbitrarily: the landed state is the batch's,
whatever the interleaving, and a crash anywhere in it leaves each command at a prefix of its
own steps, from which the batch run again lands the same state. On one identity the commands run
one after another, and a crash inside one of them converges when that command and the ones after
it run again, not the whole batch: the handler skips a request already receipted as landed (§9
item 28). `[THEOREM — DOR-9, DOR-11, Door.lean::run_steps, run_perm_of_disjoint,
batch_after_prefixes, batch_after_interrupted; the control rerun_whole_batch_diverges]`
Commands that share an identity wait; the embedder is shared by the compute halves as a resource,
not as an order; each landing is still one critical section under the plane's lock. The queue's
priorities and anti-starvation aging are unchanged; what the rule adds is the conflict test, the
identities a command's plan names, read off the plan before dispatch (DO-6).

### D6 — The event clock

A landed command is a set of store-append events: the raw object, the occupancies, the version
row, the attestation that consumes the digests. On the global event clock they are g1 appends
and one g2 reference, so the cut after a batch is the cut before joined with the batch's events,
and the certificates compose by CLK-2; the versions' per-doc chains stay chains because a
re-ingest of an unchanged note appends no version (D5). `[ESTABLISHED — CLK-2,
global-event-clock §2.4; DERIVED here]`

### D7 — What each path becomes

| today | the sentence | who writes the request |
|---|---|---|
| the watcher's `vault_sync` job; `palace vault-sync`; MCP `sync_notes` | `do sync vault` | the watcher (as today, the daemon's own), the CLI, the MCP server |
| `palace dialogue-sync` | the edge readers stay edge processes and write `data/handoff/dialogue/<source>.json` as today; the core half, reading that file and capturing its turns with the reader's roles, is `do sync dialogue` | the MCP server, the web bridge, the CLI through `query`; `palace dialogue-sync` and the heartbeat still run it in process behind the live-daemon guard until they write requests (DO-3b) |
| MCP `capture` | `do capture "<text>" in <conversation>`, observed by construction | the MCP server, the Open WebUI bridge |
| the inbox capture sink | unchanged: the daemon's own job, the owner's message as `authored-dialogue` by the inbox's identity; not a sentence (its catalog key is a timestamp and it is not idempotent) | — |
| MCP `link` | `do link <a> <b> <relation>` | the MCP server |
| MCP `dream`; `palace dream` | `do dream` (a BACKGROUND synthesis-tier job: with the owner present it waits for a trough, as every synthesis job does) | the MCP server, the CLI |
| MCP `relate`; `palace relate` | `do relate pairs 24` | the MCP server, the CLI |
| `palace ingest-chat`; the `chat_sync` job | `do sync chat` | the CLI, the scheduler's cadence |
| `code_sync`, `code_backfill`, `code_rebuild`; `palace code-seed`; `lanes code-embed` | `do sync code`; `do ingest code <commit>` | the scheduler, the CLI |
| `lanes code-observe`; `scripts/snapshot_code.py` | `do observe code [<commit>]` | the CLI |
| `scripts/ingest_self_knowledge.py` | `do ingest doc <path>` per doc | the CLI |
| `scripts/curate_local.py` | `do ingest paper <ref>` per manifest entry | the CLI |
| the `research` job | `do research "<criteria>"`, carrying the criteria by reference (the request file), de-identified before the airlock as today | the scheduler |

The MCP keeps its tool names for one release as aliases that compile the sentence and write the
request, so no client breaks; then the Ambassador has one tool, `query`, and the manifest says
so. The existing job kinds keep their handlers; the door's handler dispatches to them by the
command, so the landers are not rewritten by this note. `[INFERENCE — falsifier: a client that
needs a tool the sentence cannot say]`

### D8 — Refusals, and what is unrepresentable

Purge, re-key, reset and re-embed are the owner's, by a signed declaration
(`core/stores/authored_supersession.py::verify_owner_declaration`, `MachineAuthorityRefused`) or
by `--confirm` at the CLI. They are **not in the grammar**: a machine cannot ask for them in the
language, which is stronger than refusing the ask. Everything else is governed by the write bit
(DOR-1). A command never deletes: `sync` tombstones a vanished note and supersedes a changed one,
keep-and-link (temporal-code-corpus D2), and the raw store is never written twice or emptied. The
provenance of what a command writes is fixed by its kind and the surface that spoke (D3); no
word of a sentence decides a class. One existing write breaks this rule from the other side: the
edge store's key is `(u, v, rel_type)` with no provenance, and `add` is a replace, so a `link`
today can overwrite an authored edge on the same pair (§9, defect 3); the door's `link` writes
interpreted edges only and refuses the pair when an authored edge holds it, until the key carries
the class. `[DERIVED — the firewall, carried]`

### D9 — The laws: family XII, the door

| law | statement | structure | formal |
|---|---|---|---|
| DOR-1 | a command is admissible under a grant iff some granted plane lies above its scope, at its clock and window, and carries the write bit; a grant whose planes all have `W_Σ = 0` admits no command; the Ambassador's grant as written admits a projection-event command and refuses a commit-clock one; that the clause's strata are the strata written is the typing's convention, and that `and`, `or` and `then` never join a command is the grammar's (no theorem) | the scope lattice's authority coordinate, QSA-5 | `Door.lean::command_admissible_iff`, `command_admissible_iff_write`, `command_needs_a_writing_plane`, `readonly_admits_no_command`, `ambassador_admits_projection_command`, `ambassador_refuses_commit_command` |
| DOR-2 | ingestion is extensive, `s.rows ⊆ (ingest x s).rows` and a chain only grows; monotone on the rows between sound states; idempotent, `ingest x (ingest x s) = ingest x s`, since its key names its digest | a closure operator on the ledger-grain states, keyed | `Door.lean::ingest_extensive`, `chain_prefix_ingest`, `ingest_monotone`, `ingest_idempotent` |
| DOR-3 | ingests of distinct identities commute, a batch of distinct identities lands the same state in any order, and a batch run again lands nothing | commuting keyed closure operators on disjoint identities | `Door.lean::ingest_comm`, `ingest_batch_perm`, `batch_idempotent` |
| DOR-4 | every store mutation is a job landed by the one writer; a surface writes a request and returns the receipt | the queue's discipline, made a property by D3 and D7 | the import ratchet over a read-only constructor family (DO-5), no theorem |
| DOR-5 | a command embeds nothing iff the plane holds its atoms, so a re-ingest of held content costs zero; two fresh commands sharing an atom pay once; a batch of fresh commands on distinct identities embeds exactly its distinct new atoms | the plane's atom dedup (A3) | `Door.lean::embeds_eq_zero_iff`, `embeds_ingest_twice_zero`, `embeds_share`, `embedsBatch_eq` |
| DOR-6 | the receipt is the rows added and the digest landed: a fresh command's state after is the state before plus the receipt's rows, the receipt's digest is the chain's new head, and on a sound state every row it names is held, so `witness` of a receipt is complete and never over-claims | the attestation's output hashes | `Door.lean::receipt_complete`, `receipt_head`, `receipt_rows_subset` |
| DOR-7 | with the key written last, a fresh run interrupted after any step leaves a state from which the next run lands exactly the uninterrupted run's state; so does one that ran any of its steps but its key, in any order and any number of times, which covers the code's order (the version row before the attestation) as well as the model's; a key written while some of the command's rows are not held, first or after the plane's rows as the audit's defect 1 wrote it, the run interrupted right after it, is never repaired | idempotent stages, the key last | `Door.lean::ingest_prefix_converges`, `ingest_after_nonkey`; the controls `key_first_does_not_converge`, `key_early_does_not_converge` |
| DOR-8 | fresh commands on one identity land in the order of their chain, and two orders give two chains | conflict-serializability by identity, the chain as the serial order | `Door.lean::same_identity_orders_the_chain`, `same_identity_not_comm` |
| DOR-9 | the steps of fresh commands on distinct identities run to the batch's state in any order, which includes every interleaving of their stages, so the queue may dispatch them in parallel; the reads clause (a read is a function of a cut, CLK-2) is cited, not a theorem of this model | commuting steps on disjoint identities; the queue as the serializer | `Door.lean::run_steps`, `run_stepsOf`, `stepsOf_comm`, `run_perm_of_disjoint` |
| DOR-10 | conflict-equivalence is state-equivalence: a schedule that is a permutation of another and orders the landings on each identity, and the keys of each identity, as the other does runs to the same state; the commands keyed at their turn drop out of the batch, and a schedule of the rest's steps that keeps their order on each identity lands the batch of the whole list, repeated identities allowed; a permutation alone does not. The model's steps carry no read, so the guard's moment is outside it: a command whose guard reads its key before the previous command on its identity has written its own decides otherwise (the control `early_guard_skips`), and the plane's occupancies on one path are ordered where the model's rows are not; both are why the queue runs the commands on one identity whole, one after another, which makes every guard read the serial key (only key steps on an identity write it, `run_key_of_not_keyed`) | conflict-serializability, the classical theorem, for the door's steps; the queue's order on one identity as the serial order | `Door.lean::run_eq_of_cls_filter`, `run_stepsOf_along`, `serializable`, `batch_landsOf`, `freshAlong_landsOf`, `serializable_landsOf`; the controls `serializable_needs_the_order`, `early_guard_skips` |
| DOR-11 | if each command of a batch of fresh commands on distinct identities has run a prefix of its own steps, in any global order, the batch run again lands the uninterrupted batch: every crash point of every parallel run of commands on distinct identities converges; on one identity it need not (two versions, the second run whole before the first starts), and running such commands one after another is not enough either: a serial run of commands each fresh at its turn, stopped inside one of them, converges when that command and the ones after it run again, and not when the whole batch does, so the handler skips a request already receipted as landed (§9 item 28) | DOR-7 per command, DOR-9's commutation across commands | `Door.lean::batch_after_prefixes`, `run_key_of_not_keyed`, `batch_after_interrupted`; the controls `prefixes_need_distinct_identities`, `rerun_whole_batch_diverges` |
| DOR-12 | every state a key-last run passes through is sound for its own command, and a batch on distinct identities interleaved in any order and stopped anywhere is sound for each of its commands when the state before was: a key naming a digest finds that version's rows held; so a reader that reads a version only when the key names it sees it whole or not at all, and needs no lock against the writer, at the ledger's grain (the reconciled stores are not modelled); with the key first a reader sees rows that are not there | the key last, read side; with CLK-2's cuts, readers without limit beside one writer | `Door.lean::sound_prefix`, `sound_after_prefixes`, `rows_subset_run`; the control `key_first_unsound` |

What the model leaves out, the second review's list, each a reason for a rule above or a limit
of a law: the guard's read at a command's start (DOR-10's scope); the plane's lock, which makes
each landing atomic (the atom's check-then-insert, the occupancy transaction), so that a stage
half written is not a step; the plane's supersession order on one path, ordered where the model's
rows are not (DOR-10's scope); the `held` cache, which only `repair()` rebuilds, not a re-run;
the catalog's `active` flag, which the model's key ignores; and that a re-run happens at all,
which for the door's kinds the orphan sweep now provides (§9 item 28).

An id is unbolded until code relies on its law; then the row enters `docs/LAWS.md` with its
falsifier test and the statement enters `formal/Spec/`: DOR-1 (`_command_clause`, `grant_for`) and
DOR-7 (`core/ingest/landing.py`) entered on 2026-11-05 as family XII. The attacks and their controls are
`PalaceTest/Door.lean` seeds 245 to 272: an operation that always appends a version is not
idempotent, two commands on one identity do not commute, an interleaving that lands them in the
other order lands the other chain, and a run that writes its key first does not converge; three
commands on three identities land one state in every order of the commands, and a batch run
again lands nothing; two versions of one note scheduled in their order beside another note land
the batch and in the other order do not (DOR-10); two commands stopped at any prefixes converge
under re-run, and a command whose run is not a prefix of its own steps does not (DOR-11); a run
stopped anywhere is sound for its command, alone or beside another, and with the key first it is
not (DOR-12); a run of any two of a command's steps but its key, in either order, converges
(DOR-7 in the code's order); the second review's two counterexamples, a revert whose guard reads early and two versions of one
note stopped out of order, are controls; and from the third review, a run that writes its key
after the plane's rows, as the audit's defect 1 did, does not converge (DOR-7), a command keyed
at its turn drops out of a schedule that lands the whole list (DOR-10 with the guard), and a
serial run on one identity stopped inside a command converges when that command runs again
alone, and not when the whole batch does (DOR-11).

## 4. Consequences — the order of work, on the owner's merge

- **DO-0, the design proved.** Done on this branch: `formal/Palace/Door/Defs.lean` (the keyed
  model), `formal/Palace/Door.lean` (DOR-1 to DOR-3 and DOR-5 to DOR-12 with their controls; DOR-4 is the
  queue's discipline, for the ratchet), `formal/PalaceTest/
  Door.lean` (the attacks), the L1 gate green. The admissibility law reuses
  `Palace/Sentence/Defs.lean`'s `Admissible` and `Palace/Scope/Defs.lean`'s `Authority` and
  `ambassador`. The two theorems the first draft left for DO-6 are proved: crash convergence
  under a parallel run (DOR-11) and conflict-serializability with repeated identities (DOR-10).
- **DO-1, the grammar, typing and plan.** Done on this branch: `core/sentence/grammar.py` (the
  `do` production; one reserved word, `do`, the command words read in place so `over dialogue`
  and a note titled `code` keep working; a number is never the head of a word, so a session id
  parses), `ast.py` (`Do`, `Command`, `Source`, `describe_command`), `types.py` (`Sort.EVENT`,
  `command_requirement` as D2's table, `_command_clause` with the write bit, `check_admissible`
  unchanged), `plan.py` (a command's plan is itself), `execute.py` (a command is refused by name
  until DO-3 wires the door). Tests: the parses and their refusals, the table's totality, the
  Ambassador's grant as written (projection-event commands admitted, commit-clock ones refused),
  a read-only grant refusing every command and admitting every query (DOR-1).
- **DO-2, the operation and the key order.** Done on this branch. The key written last in
  `sync_path`, `capture_turn` and `ingest_curated` (§9, defects 1 and 2), with the crash-injection
  test (`core/ingest/landing.py`, `tests/integration/test_landing_order.py`). `core/ingest/door.py`:
  the roles and their grants (`grant_for`: the Ambassador's for the agents' surfaces, the operator's
  for the owner's), the spool under the interface handoff directory (`write_request`, `pending`,
  `stage`, `read_request`, the receipts), the kind map (`kind_of`: today's kinds stay the queue's
  kinds, and `do sync dialogue` is the queue's own coalescing `dialogue_sync`; the door's own are
  `ingest`, `capture`, `link`, `relate`, `code_observe`), and the landing (`perform`, with `Landers` injectable: a note from the vault
  only, a turn and a capture observed by construction, a doc among the curated sources only, a
  link that never overwrites an authored edge, the relation pass). `scheduler/door.py`:
  `drain_spool` (each tick: compile under the spool's grant, stage the daemon's own copy in
  `queued/`, enqueue, receipt with the job id, unlink the writer's file; a refused request is
  receipted and dropped) and `door_handler` (compile again,
  perform, receipt what landed). Not landed yet, refused by name before anything is written:
  `research`, a paper's manifest, one commit's backfill (DO-3b).
- **DO-3, the surfaces.** Done on this branch. `ask_logged` compiles a `do` sentence under the
  role's grant, writes the request and returns the receipt as the answer's one hit (stratum
  `door`), logged as `requested`; the trace gains the `act` stage. The daemon drains the spools
  each tick (`Components.drain_spool`) and registers the door's handlers; the dialogue sync is a
  function the daemon calls as the one writer and the CLI behind its live guard; `observe code`
  runs the code sensor. The MCP's `sync_notes`, `sync_dialogue`, `dream`, `relate`, `capture` and
  `link` are aliases of door sentences through `query`, and write nothing from the server's
  process; the manifest is regenerated. The attestation branch of `witness` closes the loop
  (a landing's receipt names its attestations; `witness` dereferences them). Left for DO-3b:
  the three refused landings and the CLI's inline verbs as sentences.
- **DO-4, the audits.** Agents, as the first draft had: a design review against the code (done,
  2026-11-05, nineteen findings folded in), a proof audit (done; the keyless model it refuted was
  replaced by the keyed one), a security review of the door (done, 2026-11-05, fifteen findings, §9 items 8 to 22: twelve fixed on
  this branch, three the owner's), a second review (§9 items 23 to 36) and a third, of the door's
  Python at `761692d` (§9 items 37 to 50), beside a review of the formal side whose findings are
  folded into D5 and D9, a validation run (the gates,
  the live read-only smoke of the parser and the typing).
- **DO-5, the ledger and the ratchet.** The rows of D9 enter `docs/LAWS.md` as code relies on
  them, each with its falsifier; a read-only constructor family (`open_*_reader`) that the import
  ratchet admits in the surfaces, so that DOR-4 has a checker.
- **DO-6, the split and the parallel dispatcher.** The compute/land split onto the worker protocol
  and the dispatcher's conflict test (DOR-9 and DOR-10: a job's identities, read off its plan,
  disjoint from the running set, and the jobs on one identity run whole, one after another, in
  queue order, so every guard reads the serial key; DOR-11: a crash anywhere among commands on
  distinct identities converges, the one-after-another rule keeps commands on one identity from
  leaving interleaved prefixes, and a crash inside one of them converges when it and the ones after
  it run again; DOR-12: readers need no lock throughout), when the owner
  wants parallel acquisition; nothing above depends on it. The laws it needs are proved.

## 5. Wiring & enablement

The sentence surfaces run under `[query]`; a command rides the same switch and the grant decides
its admission (no `[query] actions` key was needed). The spool directories live under the
interface handoff directory (`cfg.interface.handoff_dir`, `data/handoff/door/<role>/`), and the
daemon makes them each tick (`ensure_spools`): the root `0755` (the daemon adds every entry), the
operator's spool `0700` (the owner's account alone writes it), the agents' spool `3770` when the handoff directory's group is a dedicated one (the group writes,
the sticky bit keeps one writer from moving another's file) and `0700` under a group every account
is in (`staff`, `everyone`, `users`), and beneath each `queued/` and `rejected/` the daemon's alone
(`0700`), and `receipts/` the same, or `2750` where the agents read theirs. Only the daemon's
account makes the spools; a surface that finds them missing writes nothing. It drains only a spool whose every directory is a real directory
owned by its own account and writable by no one it should not be, reports any other once, and
trusts a request only as `_load_request` reads it: through a descriptor that follows no link and
blocks on nothing, a regular file with one link under 64 KiB whose id is its name, written, in the
operator's spool, by the daemon's own account. The first form of this paragraph followed
plane-principals' `2770` for every spool; on this machine the `palace` group holds the agents'
account, so the operator's spool was theirs to write (the second review's finding 1, §9 item 23).
What the principals' split adds is a principal per role in place of the one group. `queue.sqlite` stays the daemon's own file, opened by no surface. The daemon
drains the spools each tick before it dispatches and registers the door's handlers beside the
others; the CLI's `code-seed`, `code-backfill` and `code-rebuild`, which enqueue directly today,
and `talk.py`'s runtime, which completes queued rows without claiming them, become spool writers
in DO-3b. Nothing restarts; a request is drained by the running daemon like any other job.

## 6. Risks and falsifiers

- A surface that still writes after D7: the import ratchet, over the read-only constructor
  family, names it. The falsifier of DOR-4.
- A forged request: a request is bounded by the spool it sits in; a test writes a request naming a
  command the spool's role may not say and asserts the writer's second compile refuses it, logs
  the refusal, and lands nothing.
- Coalescing swallowing a needed re-run: only QUEUED rows of idempotent kinds collapse; a door
  `do sync vault` drained while the watcher's row waits is that row, and drained while it runs is
  a second row (`test_a_door_sync_coalesces_with_a_waiting_row_and_never_with_a_running_one`, on
  the real queue).
- The receipt over-claiming: DOR-6's statement; two notes and a capture land through `perform`
  on real stores, and each receipt's attestations are records whose outputs are exactly the digest
  it landed, none named twice, a re-landing naming the same record
  (`tests/integration/test_landing_order.py`).
- Latency. Today MCP `capture` lands synchronously and the turn is readable by the next query.
  After the door the receipt is a request id, and the landing waits for the daemon: one tick
  (`tick_seconds = 1.0`) when idle, the boundary of the running job when busy (there is no
  preemption), and behind a long `code_backfill`, hours, as the queue's own history shows. The
  floor is stated; the remedy for a script that needs the state is the `wait` adjective (§7);
  the `digest` and `created` that `capture` returned arrive with the receipt's landing, not with
  the call. The measurement is the time from the request to the attestation on the live instance.
- Starvation: a watcher-written `do sync vault` keeps `vault_sync`'s kind, tier and aging, so it
  behaves as today; the risk the first draft carried, one kind for every command mis-tiering the
  syncs onto the synthesis tier or `dream` onto the pinned one, is removed by keeping the kinds.
- The stale `held` cache after a crash between the plane's second and third writes: `repair()`
  rebuilds it; the repair on a missing receipt is not wired (§9, item 19).
- A flood or a forgery at the spool: the drain is bounded a tick and a role, the request file is
  trusted only as `_load_request` says, the handler lands only the sentence the drain compiled,
  and the identities the door mints live under `dialogue/door/<role>/`; `tests/unit/test_door.py`
  holds each falsifier (a malformed, oversized and FIFO file; a world-writable and an unknown
  spool; a replayed id; a rewritten queued file; a path in a conversation name; a second `ingest
  doc` outside the allow-list; a note outside the vault's scope; `relate pairs` over the cap).

## 7. Parked decisions

The compute/land split and the parallel dispatcher (DO-6). A `wait` adjective (`do … wait`) that
blocks a surface until the landing, for scripts that need the state. The bookkeeping verbs
(tasks, reminders, status) as sentences over the task ledger. An `fsync` in the raw store's
write-then-rename.

## 8. Open questions

- The Ambassador's write planes: today the first plane would admit every projection-event
  command to the Ambassador, `ingest note` and `dream` included, while the commit-clock commands
  are refused. Narrow it to `observed` and `interpreted`, with `sync` lanes under a plane the CLI
  and the heartbeat hold? The owner's.
- Should `do research` be admissible to the Ambassador at all (it reaches the airlock, the one
  outward path)? The owner's.
- The authored half of `relate`: today the detector also mints `authored-solo` edges from the
  owner's `supports::` properties; move that half to the vault lane, where the owner's note is
  read, so `relate` writes interpreted edges only? The owner's.
- The MCP's aliases: one release, or keep them?

## 9. Findings for the owner — defects in the code today, from the audit of this note

Recorded here; the first two are fixed on this branch (DO-2a, `core/ingest/landing.py`), items 4
and 6 later on `build/ladder-fixes`, the rest stay the owner's.

1. **The idempotence key preceded the attestation and the version row.** `sync_path` wrote the
   catalog's digest, then emitted the attestation, then recorded the version; `capture_turn` had
   the same shape. A crash after the catalog record left a state the next run read as UNCHANGED,
   so the attestation and the version row were never written. *Fixed:* the key is the last write
   in both lanes, the version row is appended only when its digest is not the chain's head, and
   the attestation is emitted once per (action, digest); `tests/integration/test_landing_order.py`
   injects the crash and asserts the re-run lands exactly once. A rename, the same bytes under a
   new path, stays a version event (bp-031): `sync_path` tells it from a re-run by the catalog,
   where the old path still binds the identity until the pass tombstones it. The one window this
   cannot tell apart is a crash inside a rename's landing; closing it needs the version row to
   carry its path, an additive column on the §4A store, the owner's call.
2. **`ingest_curated` had no idempotence key.** Every run re-upserted the catalog and appended a
   new attestation, since the attestation id hashes the timestamp. *Fixed:* a doc the catalog
   holds at the same digest lands nothing and attests nothing, and the key is written last.
3. **The edge store's key has no provenance.** `EdgeStore.add` is a replace on `(u, v, rel_type)`,
   so an interpreted `link` can overwrite an authored edge on the same pair, its weight, sign and
   time included.
4. **`palace ingest-chat` writes beside a live daemon.** It has no `_refuse_if_live` guard; the
   other on-demand verbs do. *Fixed:* the verb refuses beside a live run, as they do;
   `tests/integration/test_chat_sensor_wiring.py` asserts it.
5. **The code lane's physical Lance add takes no lock.** It is safe today only because its writers
   are the daemon and a guarded verb. *Decided, no race today* (the one-writer model, DOR-12): the
   code rows have one writer at a time, since the daemon dispatches one job a tick and `lanes
   code-embed` refuses while it is live; the table's other writers, the plane's, under its own
   lock, write disjoint rows (prose atoms carry no class and no path), and row-disjoint writes
   commute, so every interleaving of their commits holds the rows of a serial order; LanceDB
   commits each write whole and rebases concurrent ones (measured on lancedb 0.33.0, four runs of
   three processes, two updating disjoint rows of one fragment and one appending, 120 commits a run:
   no error, no lost write); and a commit that failed would be a crash at that step, which D8 and
   PLN-4's crash points cover. A lock is owed once a second process may write code rows beside the
   daemon, or drop the table: an unguarded script's `reset()` commutes with nothing.
6. **`talk.py`'s runtime completes QUEUED jobs without claiming them**, outside the supervisor's
   one claim site. *Fixed:* `run_pending_tasks` claims each job through `JobQueue.claim` (a new
   `kinds` filter keeps it to the kinds it handles) before completing it;
   `tests/integration/test_ambassador_conversation.py` asserts the handler sees a RUNNING row.
7. **The plane's `held` cache can go stale across a crash** between its second and third writes,
   and the UNCHANGED check keeps a re-run from repairing it; only `repair()` does. *Proved and
   fixed* (PLN-4's crash points, `formal/Palace/Plane.lean`): a re-run repaired the stale entries
   that hid rows and left those in excess; a land now writes its cache's additions before its
   transaction, so a crash leaves only excess, which changes no search (`search_after_crash`).

The security review of the door (2026-11-05, a read-only agent over the branch at `f782151`)
found fifteen defects in the door as first built. Fixed on this branch, with a test each:

8. **The `ingest doc` allow-list ran once per daemon lifetime**, inside the lander's lazy build, so
   a second doc anywhere under the repository, `data/` included, landed as curated. *Fixed:* the
   allow-list is read on every call.
9. **The dialogue identity was the sentence's**, so `ingest turn openwebui/<chat> <id> "…"` could
   supersede one of the owner's turns with observed text, and `capture … in` could plant turns in
   the owner's conversation. *Fixed:* the door's turns live under `dialogue/door/<role>/`, a
   conversation or turn name carries no path, and `capture_turn` refuses a turn whose class
   differs from the one its identity holds.
10. **The request id was file content, spliced into paths** on both sides of the door. *Fixed:*
    an id is sixteen hex digits and the file's name, checked by the drain and by the handler
    before either names a path; a receipt is written under a checked role and id only.
11. **The drain was not robust**: a file that was not JSON of an object stopped the daemon, a FIFO
    hung it, a flood held the serve loop. *Fixed:* a request is a regular file under the cap, or
    it is moved to `rejected/` and reported; the drain is bounded a tick; a request whose enqueue
    fails is receipted and set aside; the serve loop logs a drain that raises and goes on.
12. **The spool directories were created under the surface's umask** and a role was a directory
    name nothing checked. *Fixed in part:* the daemon creates them with `2770`, a symlink is
    refused, a world-writable spool is not drained; the owner check waits on the principals'
    split (§5). (Superseded by item 23: the `2770` modes were the defect.)
13. **No cap on a role's requests, and `capture` at the reactive priority** aging never demotes.
    *Fixed:* at most sixteen of a role's door jobs queued at once (the rest wait in the spool),
    `capture` at the interactive priority, `relate pairs` at most fifty. (Superseded by item 25: the quota now refuses by lane.)
14. **The job's kind was decided on one sentence and the work done on whatever the queued file said
    later.** *Fixed:* the payload carries the sentence's digest, the handler refuses a staged request whose digest or kind is not the job's, and the staged copy
    lives in `queued/`, which only the daemon writes (`stage`).
15. **`ingest note` bypassed the vault's scope** (its pattern and excluded directories), so a
    recycled note or a binary could land as authored. *Fixed:* `VaultSync.in_scope` binds the
    sentence as the rescan is bound.
16. **Corpus text reached the query log and the receipts**, and `--log` listed every command as a
    failed translation. *Fixed:* a command's literals are logged as their lengths, `requested` is
    its own outcome, a receipt names the request and not the sentence, and a queued file is
    removed once its receipt is terminal (a failed one stays, for the operator to re-spool).
17. **`--as` had become a grant selector.** *Fixed:* the CLI speaks to the door as `cli`, whatever
    the label; the MCP speaks as `ambassador`; neither can choose.
18. **`quote` was not the tokenizer's inverse** for a backslash. *Fixed:* both escape it; a
    round-trip test holds.
19. **Receipts claimed landings the sentence did not get**: `observe code <commit>` ignored the
    commit, `ingest transcript <session>` synced every session. *Fixed:* both are refused by name
    until DO-3b wires them, as `ingest code <commit>` was.
20. **The drain deleted files in directories it did not know.** *Fixed:* a directory that is not a
    role's is not touched; the dead roles (`mcp`, `webui`, `owner`) are gone from the table.

Recorded, not fixed, the owner's:

21. **The Ambassador's write plane** (`core/query.py`) admits `ingest note`, `ingest doc`, `sync
    vault`, `sync dialogue`, `dream` and `curate` to the model, the door being what makes them
    reachable; §8's question. Narrowing it to `observed` and `interpreted` keeps `capture`,
    `link`, `relate`, `dream` and `curate` and refuses the rest; the MCP's `sync_notes` and
    `sync_dialogue` aliases would then be refused to the model.
22. **A delegated kind's receipt ends at `queued`** with the job id: `vault_sync`, `dream`,
    `curate`, `chat_sync`, `code_sync` and `dialogue_sync` carry no request id, by design, so that
    a door-written `sync vault` coalesces with the watcher's; the queue's row is their record from
    there. A door kind's job that raises is receipted `failed`; the repair of a stale `held` cache
    on a missing receipt (§6) is not wired.

A second review (2026-11-05, an agent over the branch at `fcdaca6`, with probes in Python and
Lean) checked the fixes above and found fourteen more defects, the first introduced by item 12's
fix. Fixed on this branch, with a test each:

23. **The `2770` spools let the agents' account speak as the operator.** On this machine a new
    directory takes its parent's group, `palace`, which holds the agents' account; the operator's
    spool was theirs to write. *Fixed:* the modes of §5, the operator's spool the owner's account's
    alone, every directory checked for kind, owner and write bits before a tick drains it, and a
    request in the operator's spool read only if the daemon's own account wrote it.
24. **The web chat's narrowed tools were bypassed by `query`**, which since the door can carry a
    command. *Fixed:* from Open WebUI, `query` speaks only `do capture`, `do sync dialogue` and
    `do sync vault` (`agents/ambassador/handoff.py::web_admits`).
25. **A role's dreams held its captures**, one quota counting both. *Fixed:* a quota by lane (the
    interactive `capture`, sixty-four; the bulk rest, sixteen), and a request past its lane's share
    is refused as busy, not left to wait, so nothing lingers in the spool; a surface refuses to add
    to a spool already 256 deep (`Busy`, a refusal of its own class).
26. **The trust checks looked at a path, not an open file**: a writer keeping a hard link could
    grow its request after the check, and a swap to a symlinked pipe could hang the writer.
    *Fixed:* a request is read through a descriptor (`O_NOFOLLOW`, `O_NONBLOCK`, `fstat`: a
    regular file, one link, under the cap, read to the cap at most), and the daemon stages its own
    copy in `queued/` before a job names it, so the writer's file is never read again.
27. **The query log still took a command's text**: an unterminated string was logged whole, a
    parse error quoted the string it stopped at, and the redaction's regex was quadratic. *Fixed:*
    a command is redacted from its tokens (linear), one that does not tokenize is logged as its
    command word and length, a refusal's reason drops quoted text, the parser never quotes a
    string, and a command over the cap is refused before it is parsed.
28. **A crash mid-landing lost a door request, and a failed one could not be spooled again.**
    *Fixed:* the orphan sweep puts a door job back in the queue (`_REQUEUE_KINDS`), the handler
    skipping a request already landed or refused, and a request whose receipt says `failed` may be
    spooled again.
29. **Two operator roles had no writer** (`heartbeat`, `watcher`). *Fixed:* removed.
30. **A spool a surface made first was not the daemon's to manage.** *Fixed:* such a spool fails
    the owner check and is reported, not drained.
31. **The drain could raise.** *Fixed:* each request is drained under its own guard, and only the
    roles whose spools pass the check are read.
32. **The coalescing kinds' requests were never removed.** *Fixed:* a delegated kind keeps no
    copy; receipts, rejected files and failed requests' copies are pruned after a week (`prune`).
33. **`do sync dialogue` was a door kind**: never coalesced, and receipted `landed` when an edge
    reader failed. *Fixed:* it is the queue's own coalescing kind, and a failed reader fails the
    job. That the edge readers run as subprocesses of the daemon, up to 180 s, stays as D7 left it.
34. **A crash between the enqueue and the move ran a delegated kind twice.** *Recorded:* the
    order is now stage, enqueue, receipt, remove, so a crash after the receipt is rejected as seen;
    before it, a door kind lands once (the handler skips a landed request) and a delegated kind
    may run twice.
35. **Tests aimed at the wrong place** (the traversal's target, the vault scope without the real
    pattern). *Fixed.*
36. **A note was named by the resolved path** where the rescan names it by the vault's configured
    path, which would fork its identity under a symlinked vault path. *Fixed:* `perform` names it
    as the rescan does.

The third review (2026-11-05, a read-only agent over the door's Python at `761692d`) found
fourteen more, the first pre-existing on main:

37. **Every vault rescan deleted the shared catalog's rows the vault does not own**: dialogue turns,
    curated docs, door captures, and their plane rows with them; a capture receipted `landed` was gone
    after the owner's next edit. Pre-existing on main. *Fixed* (on `build/next-rung`): `VaultSync.owns`,
    so a rescan reaps only the vault's own rows; a test rescans beside
    dialogue turns and curated docs.
38. **The curated key blocked the repair after a plane reset**: `palace reembed --confirm` resets
    the plane and re-embeds the vault and dialogue only, and a re-run of the curated ingest then found
    every doc UNCHANGED. *Fixed:* the key asks the plane as well (`has_digest` under the curated
    clearance), so a re-run after a reset lands again.
39. **`ingest note`'s scope was spelled in one case** on a disk that ignores case, so an excluded
    directory in another case landed a deleted or backup note as authored, and a live note in another
    case forked its identity. *Fixed:* the path must be one the vault's listing yields, as the disk
    spells it, and an excluded directory is matched in any case.
40. **`do sync dialogue` could not find podman** under launchd's PATH, so its Open WebUI half failed
    every time, unseen behind a delegated receipt. *Fixed:* the edge readers look where Homebrew keeps
    it.
41. **`ingest note` of a note renamed just before it forked its identity.** *Fixed:*
    `VaultSync.sync_one` adopts a vanished note's identity when the bytes are that note's, as the rescan
    would.
42. **An empty `id::` property split the version chain**, the first version under the path and the
    rest under the empty id. *Fixed:* the resolved id is tested against None.
43. **A request the surface accepted could be rejected by the daemon with no receipt**: escaping
    grows a request's file past the daemon's cap while its sentence is under the surface's, and a
    rejection wrote no receipt, so the client polled forever. *Fixed:* the surface refuses a request
    whose escaped file would pass the cap; a rejected file whose name is an id no receipt names is
    receipted `refused`; a rejection never lands on an earlier one's name.
44. **A directory named like a request stopped the prune and flooded the log.** *Fixed:* the drain
    and the prune touch only regular files, and the prune removes staged copies no receipt names.
45. **Any account could make the spools, and their checks read only the mode bits.** *Fixed:* only
    the daemon's account makes them, `queued/` and `rejected/` are the daemon's alone, and the agents'
    spool is group-writable only under a dedicated group (§5). *Recorded, the owner's call:* inherited
    ACLs are not checked.
46. **Receipts named other landings' attestations** when the bytes matched (a capture identical to
    an inbox message), and reverts, duplicates and restores emitted none. *Fixed:* a receipt names only
    its own action's attestations (`landing.attested_by`), and a landing that appends a version is
    attested as its own event. *Recorded, the owner's call:* a crash between a revert's version row and
    its attestation loses that attestation on re-run, since an older one names the digest (closing it
    needs the attestation to name the version); and a delete and restore of the same bytes appends no
    version, the head being unchanged, where the code before appended one.
47. **A door job that killed the process was requeued on every restart.** *Fixed:* at most twice;
    the third start fails it.
48. **Load the Ambassador can make without meeting a quota.** *Recorded, the owner's call:* the
    coalescing syncs are not counted, so the Ambassador or the web client can keep `vault_sync` and
    `dialogue_sync` running back to back on the one dispatcher; captures run at the interactive tier up
    to 64 queued, so a sustained flood delays the background work until aging catches up, about 135
    minutes. The quota bounds what waits, not the rate.
49. **The MCP aliases changed behaviour.** *Fixed:* `relate pairs 0` judges none, as before.
    *Recorded, the owner's call:* the default capture conversation moved from `ambassador` to
    `door/ambassador/captures`, so re-capturing an old text makes a second identity; captures over about
    32 KiB are refused; the return shapes changed. Whether a client relies on the old ones is the
    owner's to say.
50. **Tests that would pass on wrong code**: the scope test used lowercase paths only, no spool test
    used a directory, the receipt test used distinct texts only, the landing-order test had
    `doc_id` equal to the path, and the test of a request two jobs name drained once and called the
    handler twice. *Fixed:* a test each; the last now kills the drain between the enqueue and the
    receipt. The dialogue-sync tests still stub `subprocess.run`, so
    they cannot see the edge reader's PATH.

The second review's findings on the model are taken up in D9 (DOR-10's scope, DOR-11's
hypothesis, what the model leaves out).

## Cross-references

`dn-query-sentence-algebra` §2.3 (the grammar this extends), §2.4 (typing), §2.5 (QSA-5), §2.6
(the overlay, whose made-real form is a command); `capability-scope-algebra` §2.2 (the authority
coordinate); `ingest-identity-and-amendment` §2 to §5 (append-only, content-addressed, no
mutate-the-immutable); `vector-membership-store` A3 (one atom per text, the lock, the D8 order);
`dn-supervision-and-liveness` §2.5 (the worker protocol); `global-event-clock` §2.4 (cuts);
`agent-taxonomy` §2.5 (the witness law); `vault-sync-and-capture` (capture by the caller);
`chat-sensor` CS-2; `plane-principals` (the handoff directory's principals and mode);
`formal/Palace/Door.lean`, `formal/PalaceTest/Door.lean`.
