---
type: design-note
id: dn-temporal-snapshot
track: query-language
status: draft                  # provenance description, never a gate; the merge is ratification
implementation: design-only    # nothing built in the store; the laws are machine-checked in formal/Palace/Snapshot.lean
created: 2026-11-10
updated: 2026-11-11
links:
  - papers/2026-11-10-temporal-snapshot/paper.tex          # the article: the same theorems, with proof sketches and the references
  - docs/design-notes/global-event-clock.md                # N, its generators, the cut as a certified frontier (§2.4)
  - docs/brainstorms/limits-of-the-algebra.md              # L7: the snapshot as the clock's cut on the version chains
  - docs/design-notes/dn-query-sentence-algebra.md         # `as of` as the index of the reading; §2.9 what is not in the universe
  - docs/design-notes/dn-ingress.md                        # the one writer, the landing order, the key written last (ING-7)
  - docs/design-notes/dn-two-phase-ingestion.md            # an item complete without its vector; the pending report (ING-19 to ING-21)
  - docs/design-notes/vector-membership-store.md           # atoms, occupancies per class, purge (A3.7)
  - docs/design-notes/dn-utility-field.md                  # the use log and the field as its fold (UTL-4); its open question 1
  - docs/design-notes/dn-graph-dynamics.md                 # GD-4: velocity over a window of cuts, which waits on the snapshot
  - docs/design-notes/dn-mathematical-foundations.md       # the ladder; design theorems before code
  - formal/Palace/Snapshot.lean                            # the theorems (Snapshot/Defs.lean the model; PalaceTest/Snapshot.lean the attacks)
supersedes: null
superseded_by: null
warrant: null
---

# The temporal snapshot: the palace as of a cut

> Composed on the snapshot session (Fable 5.2, 2026-11-10 and 2026-11-11), on the standing
> direction that the design and its proofs come first and the build follows a licence given at
> the merge. Agent-drafted, filed `draft` on a branch; the merge is ratification. Nothing is
> built: `core/` is untouched and no store of any instance was read. Every nontrivial claim
> carries a grade: `[THEOREM]` is machine-checked in `formal/Palace/Snapshot.lean` and names its
> declaration; `[ESTABLISHED]` is a ratified note's, or a fact of the code read at the line
> cited; `[DERIVED]` is argued here from those; `[MEASURED]` is a figure taken for this note on a
> synthetic fixture (§11 says how); `[INFERENCE]` is a design call with a named falsifier;
> `[HYPOTHESIS]` is a claim nothing here checks, with what would check it named. Code claims were
> read on `origin/main` at `e3e3ee47`. The article `papers/2026-11-10-temporal-snapshot/paper.tex`
> states the same theorems with proof sketches and the references.

## 1. Purpose and scope

### 1.1 The requirement

A sentence of the query language can carry `as of "<cut>"`. Today it moves one relation: the
citation graph, which the stores index by commit, is read at the cut, and a file of the repository
is read as git's blob there. Every other verb reads the stores as they are now, and the answer
says so. The requirement is the rest: the palace as of a cut. A read at a cut must be the same
whenever it is asked, since the store only grows above the cut; it must never return what was
erased since; it must respect the grant the asker holds today; and where it cannot read a store at
the cut it must say so instead of answering from the present.

The same object serves three needs the record already names: a generic integrator, whose
checkpoint is a cut and whose input is the delta between two cuts; the velocity of an identity
over a window of cuts (dn-graph-dynamics GD-4, which waits on the snapshot); and the utility field
as of a cut (dn-utility-field, open question 1).

### 1.2 Decisions

1. **A cut is one position per chain, about a dozen positions for an instance, not one per
   document (§3.1, §3.3).** The chains are the stores' own append orders, one per provenance class
   where clearances separate the rows. `[DERIVED from global-event-clock §2.4; INFERENCE,
   falsifier SNF-2]`
2. **The missing ledger is a landing log (§3.2).** The catalog is rewritten in place, and no
   ledger records which digest a path held when, except the version chains of one place. One
   append-only, hash-chained log a provenance class, written by the catalog's own methods in the
   transaction of the row they write, makes the catalog its fold and gives every landed stratum a
   past. `[ESTABLISHED for the gap; INFERENCE for the log, falsifier SNF-1]`
3. **A name resolves to a frontier, and the read is at the greatest consistent cut under it
   (§3.4, §3.5).** Consistent cuts are closed under meet and join, and every frontier resolves to
   exactly one. Wall time selects a frontier by lookup in the bookmarks and orders nothing.
   `[THEOREM: SNP-8]`
4. **A cut is certified by the digest of each chain's prefix, recorded and attested (§3.6).** A
   certificate verifies on every later state of the store and, under a collision-free digest,
   pins the read. `[THEOREM: SNP-9]`
5. **Derived data is a function of the prefixes, held store by store in the cheapest of the
   equal ways (§5):** version-keyed rows selected by the log for vectors and lexical units,
   recomputation for the causal fiber, kept generations for model output. `[THEOREM: SNP-5;
   INFERENCE per store]`
6. **The grant and the erasure are the present's (§6).** A narrower grant's snapshot is the
   restriction of a wider one's; nothing erased is visible at any cut; a retired identity is
   sealed at every earlier cut. `[THEOREM: SNP-6, SNP-7]`
7. **A read under `as of` holds no event from after the cut it names (§7).** Where a store
   cannot serve the cut asked, it is read at the greatest position at or under it that it serves,
   the cut read is the greatest consistent cut among those positions, and the answer names it
   chain by chain. `[THEOREM: SNP-10; INFERENCE for the surface, falsifier SNF-4]`
8. **History is exact from the horizon, and the horizon is an event of the chain (§8).** A
   store that drops old generations reads every cut from its horizon on exactly, and a cut under
   the horizon is not served. `[THEOREM: SNP-10]`
9. **Retention is counted in positions and drops derived rows before ledgers (§9).**
   `[INFERENCE, falsifier SNF-9]`
10. **The build is eight stages, each a pull request with its tests and its rollback; the first
    is the landing log (§12).** `[INFERENCE, falsifier SNF-1]`

### 1.3 Out of scope

Any change to `core/` (code is licensed at the merge); the storage engines (a study of storage at
scale is under way and none of its figures is in the repository, so this note cites none, measures
what it needs on fixtures of its own, and names for each choice the evidence that would change
it); the spine's reachability index; a second embedder identity held beside the first
(dn-two-phase-ingestion, open question 4); a snapshot of the job queue, the task list and the
telemetry, which are operational state and not content; backups and migration archives, which a
purge does not reach today and which this note does not design.

### 1.4 What is proved, what is measured, what is open

Proved, in `formal/Palace/Snapshot.lean` over `formal/Palace/Snapshot/Defs.lean`: SNP-1 to SNP-10
as §10 states them, 125 theorems, eight of them the controls; attacked in
`formal/PalaceTest/Snapshot.lean` (seeds 430 to 486: thirty-nine attacks, every one surviving all
500 instances, and eighteen negative controls, each refuted). They are design theorems: no code
relies on them, so they have no row in `docs/LAWS.md` and no statement in `formal/Spec/`; §12 says
when they enter the ledger.

Measured, on synthetic fixtures only (§11): the landing log's size and the cost of its reads; what
a kept version costs in the lexical index; what a purge leaves behind today; that the causal store
depends on the order of two jobs; that the events of a transcript's prefix are not always the
prefix of its events, and what re-deriving a session costs; what `as of` accepts; that a position
taken from a store's row numbering is given again after a delete.

Open, stated where it bites: reading every head at a cut on a store of millions of paths (§4.2);
the attestation ledger's own content hashes under an erasure (§6.1); the cadence of recorded cuts
(§3.3); a repository history that is not one line (§3.1).

## 2. What exists

### 2.1 `as of` today

`as of "<cut>"` is an adjective of the grammar (`core/sentence/grammar.py:253-256`,
`core/sentence/ast.py:205-210`): the index of the reading, never a letter of a chain
(dn-query-sentence-algebra §2.3). `[ESTABLISHED]`

- **One cut a sentence.** The universe's builder keeps the cut of the `as of` it meets
  (`core/sentence/universe.py:125-127`), and the executor refuses a clause whose cut is not the
  universe's (`core/sentence/execute.py:713-718`). `[ESTABLISHED]`
- **The names it accepts.** A commit's sha, whole, or a prefix the reference store resolves to
  one commit (`universe.py:466-477`, `core/stores/reference_edges.py:381-388`). A commit the store
  holds no reading for falls back to the newest reading (`universe.py:478-484`) and the clause is
  then refused; so are `HEAD` and a date. `[ESTABLISHED; MEASURED §11]`
- **What is read at the cut.** The citation graph (`universe.py:485-486`), and a file of the
  repository, as git's blob in the tree at the commit (`execute.py:249-302`, called with the
  universe's cut at `universe.py:787-788`). `[ESTABLISHED]`
- **What is read as it is now.** Everything else, and the answer carries a note naming the verbs
  (`execute.py:503-521`, `:719-725`). The note lists `read` among them, though a `read` of a
  repository path is at the cut: on a file that changed since the cut the text returned is the
  cut's blob and the note says the present. `[MEASURED §11]` The record of such a read carries the
  commit it was read at, and the hit built from the record drops it (`execute.py:296-299`,
  `:1121-1126`), so the answer does not show which commit the text is from. A note's `read` opens
  the vault file when its reference is a path under the vault, and the raw object of the catalog's
  digest otherwise (`execute.py:342-350`): the present, in the first case newer than the catalog.
  `[ESTABLISHED]`
- **The cut the spine certifies.** `Spine.cut_at` (`core/temporal/spine.py:1004-1029`) builds a
  `CertifiedCut` from the frontier the stores have now: one position per chain, a chain per
  document for the versions (`spine.py:222-234`, `:805-816`), with the quiescence certificates of
  the event clock's §2.4 as evidence strings. No past cut can be named through it, nothing in it
  lets a later reader check that a store still holds the prefix that was cut, and the catalog
  enters the spine with no chain at all (`spine.py:549-556`). `[ESTABLISHED]`

### 2.2 The inventory

Every store an instance writes, by what a past state of it is. The clock is the order that
positions its rows; wall-time columns are bookmarks and position nothing (event clock, Law C4).
The job queue, the task list and the telemetry are left out (§1.3).

**Ledgers: a past state is a prefix.**

| store | clock | what names a position | what a rewrite loses today |
|---|---|---|---|
| raw objects (`core/kernel/stores/rawstore.py:28-40`) | none of its own; an object is ordered by the events that name its digest | the digest | nothing is rewritten; a purge deletes the object (`rawstore.py:51-61`); a transcript that grew is retained whole again under a new digest (`ops/chat_sensor.py:289-333`) |
| version chains (`core/stores/versions.py:77-86`) | `version_seq` per document | `(doc_id, version_seq)` | nothing (one admitted relabel of `doc_id`, `versions.py:132`); kept by one place only, `mirror_authored` (`core/ingest/table.py:241-251`) |
| attestations (`core/attestation/store.py:27-36`) | insertion order and the parents' graph; read back `ORDER BY timestamp, id` (`store.py:130`) | the content-addressed id | nothing; one per (action, digest) unless a version event (`core/ingest/landing.py:77-86`), so not one a landing, and no path |
| chat utterances (`core/stores/chatlog.py:77-92`) | `turn_index` per session | `(session_id, turn_index)` | nothing: the first write of a turn stands (`chatlog.py:161`); the store is wiped by a reset and filled again from the raw store (`chatlog.py:41-45`) |
| citation readings (`core/stores/reference_edges.py:134-148`) | the commit of the reading; git orders the commits | `commit_sha`, part of every edge's identity (`reference_edges.py:164-174`) | nothing: one whole reading a commit, append-only (`reference_edges.py:289-302`) |
| commit ledger (`ops/code_snapshot.py:44-58`) | git's ancestry: the ledger keeps no parent, and the sensor reads the commits of one branch in `rev-list` order (`ops/code_sensor.py:404-418`) | `commit_sha` | nothing |
| observation history (`core/stores/observation_history.py:46-56`) | the interpreter's generation per identity | (store, identity, interpreter) | nothing: a superseded generation is archived, never dropped (`core/stores/code_observations.py:211-254`) |
| run ledger, verdicts (`core/stores/runledger.py:140`, `:161`; `core/stores/verdicts.py:145`) | insertion order | the row's id | nothing |
| staging (`core/stores/staging.py:118-138`) | its own generation clock | the generation | a sweep stamps `tombstoned_at_gen` and the row stays; `read_at(g)` exists (`staging.py:232-244`) |
| query log (`core/sentence/surface.py:93`) | line order | the line | nothing |

**Version-keyed derived stores: every version's rows are kept and a flag marks the head.**

| store | clock | what names a position | what a rewrite loses today |
|---|---|---|---|
| plane occupancies (`core/stores/plane.py:268-278`) | none: `landed_at` is wall time | (path, digest, chunk) | which version was the head when: only `current` flips, and flips back when a path returns to bytes it held before (`plane.py:466-487`) |
| the plane's supersession log (`plane.py:282-289`) | `seq` per path | (path, seq) | a purge deletes entries and the next entry takes the position again (`plane.py:491-495`, `:552-553`) `[MEASURED §11]`; a reset drops it (`plane.py:628-640`); an instance with no plane has none; under lazy embedding it records the drain's order, not the landing's |
| atoms (the vector table) | none: content-addressed (`plane.py:113-115`) | the atom's id | the `held` and `current` cache columns; the table's own dataset versions, one a write, which a compaction drops (`core/stores/vectorstore.py:780-812`) |
| lexical units and postings (`core/stores/lexical.py:56-82`) | none: `landed_at` is wall time | (path, digest, chunk) | the head flag (`lexical.py:251-256`, `:260-265`); every unit, when the tokenizer changes (`lexical.py:180-194`) |
| code memberships (`core/stores/memberships.py:140-155`) | git: (path, blob) | the version's identity | the head flag; a purge leaves a recorded hole (`memberships.py:153`, `:491-497`) |

**Stores rewritten in place: no past.**

| store | clock | what names a position | what a rewrite loses today |
|---|---|---|---|
| catalog (`core/stores/catalog.py:36-45`) | none: `updated_at` is wall time | the path | which digest a path held before and whether it was active: an upsert (`catalog.py:113-121`), a tombstone that flips `active` (`catalog.py:167-170`), a purge that deletes the row (`catalog.py:254-258`) |
| chat events (`core/stores/chat_events.py:40-48`) | `ord` per session, on each row | (session, ord) | the session's rows are deleted and written again (`chat_events.py:72-88`); re-derivable from the retained transcript |
| causal edges (`core/stores/causal_edges.py:51-61`) | `event_order` and `witness_turn`, on each row | the edge's id, a hash that includes the transcript's digest (`causal_edges.py:71-76`) | the session's rows are deleted and written again (`causal_edges.py:130-154`), under new ids when the session grew; what they were before the commit ledger gained a commit |
| interpreted artifacts and hyperedges (`core/stores/derived.py:97-100`) | none: `created_at` is wall time | hash of (kind, subkind, subjects) | the artifact a later pass over the same subjects replaced (`derived.py:209-216`): model output, not recomputable |
| relation edges (`core/stores/edges.py:37-46`) | none: `created_at` is wall time | hash of (u, v, relation) | the weight, sign and provenance a re-assertion replaced (`edges.py:88-106`) |
| claim ops, authored supersessions (`core/stores/claim_ops.py:73`, `core/stores/authored_supersession.py:161`) | none | the key | the replaced row |

### 2.3 What the two-class picture misses

The picture this note started from has two classes: ledgers that only append, where a past state
is a prefix, and derived stores rewritten in place, which keep no past and are recomputed from the
ledgers. Read against the code it needs seven corrections. `[ESTABLISHED, each at the lines cited
in §2.2 unless given]`

1. **The catalog is neither, and it is the gap.** It is the head of every landed item and the
   idempotence key (ING-7), rewritten in place, and outside one place no ledger holds its past.
   The version chains exist for `mirror_authored` only; for the dialogue, observed and curated
   places the sequence of digests a path held is recorded nowhere. It has six writing methods
   (`record`, `tombstone`, `remove`, `remove_digest`, `relabel_provenance`,
   `migrate_rekey_doc_id`: `catalog.py:100-123`, `:160-172`, `:195-208`, `:210-241`, `:243-246`,
   `:254-259`) called from seven modules of `core/ingest/` (`writer.py:419`, `:433`, `:518`;
   `sync.py:201`, `:238`; `founding.py:110`; `dialogue.py:75`; `curated.py:80`; `purge.py:61`;
   `mint_ids.py:252`), so a record of its past has to be written inside the catalog and not by a
   caller.
2. **The attestations do not fill it.** An attestation names a digest and no path, and a landing
   attests once per (action, digest): a path that returns to bytes it held before, or bytes that
   land at a second path, leave no new record. The ledger is read back in wall-time order.
3. **Lexical postings and a changed item's vectors are not rewritten.** The units and the
   occupancies of a superseded version stay; only a `current` flag moves. They are generations in
   all but the stamp. And a stamp on the row would be wrong: a path that returns to bytes it held
   before makes the same rows current again (`plane.py:466-487`), so a version's rows are valid on
   a set of intervals, not on one. What they lack is the position at which each version became the
   head and stopped being it, which is the catalog's past again.
4. **The causal store is not a function of its inputs' present state.** The integrator skips a
   session whose transcript digest is unchanged (`core/integrator.py:106-111`) and resolves a
   commit against the ledger as it is at that pass (`integrator.py:148-164`), so two instances with
   the same transcripts and the same ledger hold different edges when the two jobs ran in
   different orders. `[MEASURED §11]` The extractor reads every tool result of the transcript
   before it walks it (`core/chat_events.py:110-123`, `:153`), so the events of a prefix that ends
   between a commit and its result are not the prefix of the events. `[MEASURED §11]` And an
   edge's id is a hash over the transcript's digest (`integrator.py:134-137`), so every edge of a
   session takes a new id when the session grows, and an id noted from an earlier answer names
   nothing.
5. **`read` under `as of` is already at the cut for a repository path** (§2.1).
6. **An erasure does not reach every store.** `purge_raw` removes the vector rows, the raw object
   and the catalog rows (`core/ingest/purge.py:58-62`). On a synthetic palace, after the purge of
   both versions of a note: the lexical units and postings of the purged versions remain, with
   their words; the version rows and the attestations still name the digests; and the purged text
   is still returned by the vector table read at its earlier dataset versions, until a compaction
   with no retention, which the purge does not call. `[MEASURED §11]` The relation edges whose
   endpoint is the digest and the interpreted artifacts whose subject it is are not touched
   either, and no deletion attestation is written, though the attestation store's header says one
   is (`core/attestation/store.py:3-6`; no call in `purge.py` or `scripts/purge_raw.py`). A
   snapshot that read those stores at a cut would return what the purge left, so §6.1 states what
   an erasure must reach before any of them is read at a cut.
7. **A reset takes the ledgers with the derived stores.** Its targets are the raw store, the
   vector store, the catalog, the attestations, the version chains, the chat log and the stores
   derived from them (`ops/lifecycle/launcher.py:1748-1800`); the commit ledger and the
   observation history are guarded (`launcher.py:111-118`). The raw store is the first target
   listed (`launcher.py:1753`), while the comment beside the chat log's entry says it is not one
   (`launcher.py:1779-1780`). Whatever the intent, no chain of an instance survives a reset with
   its positions, so a reset opens a new history (§8).

## 3. The cut

### 3.1 Chains and positions

A chain is an append order a store already records, or the one §3.2 adds; a position is a prefix
length of it. `[DERIVED from global-event-clock §2.2, generator g1]`

| chain | store | position | today |
|---|---|---|---|
| `land:<class>`, one a provenance class | the landing log (§3.2), in the catalog's file | `seq`, from 1, never given twice | not built |
| `chat` | the chat log | a sequence number beside each row; within a session it is the turn order | the order is recorded, the number is not |
| `att` | the attestation ledger | a sequence number beside each row | the order is recorded, the number is not; the ledger is read in wall-time order |
| `repo` | git, mirrored by the commit ledger and the per-commit readings | a commit, standing for its ancestors | recorded |
| `interp` | interpreted artifacts, relation edges, claim ops | a generation (§5.4) | not built |
| `staging` | the staging store | its generation | recorded |
| `runs` | the run ledger | a sequence number | recorded as insertion order |
| `use` | the utility field's use log (dn-utility-field §3.1) | the tick | not built |

Three choices are made here.

**The position is the store's, not the document's.** The spine's frontier has a pair per document
(`spine.py:222-234`), which is a frontier of millions of pairs on a corpus instance, where one
position a store with the per-path order inside it says the same thing (CLK-2: a frontier cut
needs only its cross-store edges checked). `[DERIVED]` The version chains stay as they are: the
log carries each landing's document and version number, so a document's chain is the log's
sub-chain, and the versions store remains the primary record of supersession.

**Where clearances separate rows the chain is per class.** A position counts every event before
it, so on a chain that mixes classes a reader of one class learns from its positions how many
landings the others made (`Witness.position_channel`), and a snapshot under a grant reads only the
chains the grant names and the cut on them (`snapshot_congr`). `[THEOREM: SNP-6]`

**A position is a number the store keeps, never the row numbering it happens to have.** The chat
log and the attestation ledger are keyed by text, and SQLite numbers their rows as the largest
number in use plus one, so a number is given again after the last row is deleted. `[MEASURED
§11]` Stage SN-2 adds a chain table beside each (an integer key, the row's own key, the running
hash of §3.6), written in the transaction of the append.

On `repo` the order is git's ancestry, which is a chain only when the history read is one line. A
commit names the down-set of its ancestors, and CLK-2's laws are stated for down-sets of any
order (`Clock.IsCut.inter`, `Clock.IsCut.union`), so the meet of two cuts at two commits is the
down-set of their common ancestors and the join the down-set of both; a join of two commits
neither of which is the other's ancestor is not named by one sha. On an instance that reads one
branch whose history is a line, which is what this repository's merges by rebase produce, every
cut on `repo` is a commit and the model's chain applies as it stands. `[DERIVED from CLK-2;
INFERENCE for the line, parked as SN-f]`

### 3.2 The landing log

One table in the catalog's file, written by the catalog's own methods in the transaction that
writes the catalog's row, so the key and its log entry land together, no caller can write one
without the other, and ING-7's order is unchanged (the key last, now two rows of one
transaction):

```sql
CREATE TABLE landings (
    class       TEXT    NOT NULL,  -- the provenance class: one chain a class
    seq         INTEGER NOT NULL,  -- the position in the class's chain, from 1, never given twice
    kind        TEXT    NOT NULL,  -- genesis | store | retire | move | unseal | horizon
    source_path TEXT,              -- NULL once purged
    doc_id      TEXT,              -- the identity the event belongs to; NULL once purged
    version     INTEGER,           -- the version number, where the place keeps a chain
    digest      TEXT,              -- NULL for a retire, and once purged
    title       TEXT,              -- NULL once purged
    att_head    INTEGER,           -- the head of `att` when the row was written (§3.5)
    salt        BLOB,              -- 16 random bytes; NULL once purged
    commitment  BLOB    NOT NULL,  -- sha256(salt, the row's fields): what the chain digests
    hash        BLOB    NOT NULL,  -- sha256(the previous row's hash, commitment)
    closed_at   INTEGER,           -- the seq of the path's next event; NULL while it is the head
    at          TEXT    NOT NULL,  -- wall bookmark: lookup only, never an order
    PRIMARY KEY (class, seq)
) WITHOUT ROWID;
CREATE INDEX landings_path   ON landings (class, source_path, seq);
CREATE INDEX landings_closed ON landings (class, closed_at) WHERE closed_at IS NOT NULL;
```

The kinds are the catalog's writes. `store` is a landing (`record`). `retire` is the tombstone of
an identity no other active path holds. `move` is a tombstone that leaves the identity at another
path (the second half of a rename, which the writer tells from a delete by the catalog,
`writer.py:409-413`) and the owner-gated re-key of an identity (`catalog.py:210-241`). `genesis`
opens a class's chain and is followed by one row for each path the catalog holds at that moment,
in path order. `unseal` and `horizon` are §6.2's and §8's. A purge is not a kind: it empties rows
(§6.1). A relabel of a whole class (`catalog.py:195-208`) renames its chain and moves no position.

The catalog is then the fold of the log: each path's last event (`stateOf`). The state at a
position is the same fold of the prefix (`stateAt`), read by one seek as the path's last event at
or under the position (`stateAt_eq_lastWrite`), or for every path at once through the closing
stamp: the rows with `seq ≤ c` and `closed_at` absent or above `c` (`genRead_gens`). The stamp is
the one field written after a row is appended, and it is a function of the rows, the position of
the path's next event (`gens_append_singleton`), so it can be rebuilt and it changes no read at a
cut inside the chain (`genRead_gens_append`). At most one row of a path is alive at a cut
(`length_filter_selects_le_one`), which is L7's falsifier turned into a theorem. `[THEOREM:
SNP-5]` The store's own precedent is the staging store: a generation clock, an admission stamp
and a tombstone stamp on each row, and `read_at(g)` as exactly this predicate
(`core/stores/staging.py:232-244`). `[ESTABLISHED]`

The chain is hashed like the prediction ledger (`eval/predictions/ledger.py:1-12`), with one
difference that §6.1 needs: a row's hash covers a commitment to the row and not the row, so a
purge can empty the row and keep the chain (`commitments_purge`, `verifies_purge`). `[THEOREM:
SNP-9]`

### 3.3 The cut and its record

A cut is a position for every chain of §3.1: for an instance, about a dozen integers.
`[DERIVED]` The read at a cut is the prefix of every chain (`readAt`), and everything else in this
note is a function of that. A cut is worth recording when it is consistent (§3.5) and the stores
were quiescent when it was taken, which is the event clock's certified frontier: between two jobs
of the one writer, with the handoff empty, the head of every chain is such a cut (GC-N3).
`[ESTABLISHED: global-event-clock §2.4]`

A recorded cut is a row of a `cuts` table beside the log and an attestation of it. An attestation
has no field for a payload: it names an action, input and output hashes and its parents
(`core/attestation/record.py:51-62`). So the record is content-addressed: its id is the hash of
its canonical bytes (the frontier, the digest of each chain's prefix at it (§3.6), the horizons in
force (§8), the quiescence certificates as the spine sources them (`spine.py:1064` on), the reason
it was taken, the previous record's id), with a wall bookmark beside it; and the attestation, of
action `cut`, names the id as its output and the previous cut's attestation as its parent, passed
as the batched landing passes its parents (`writer.py:427-430`). The recorded cuts are then a
chain inside the attestation ledger, signed when attestations are, and the id is the cut's name.
Since each record is the head of every chain at some moment and chains only grow, the recorded
cuts are totally ordered. `[INFERENCE, falsifier SNF-3]`

Three moments record one: the code sensor reading a commit (`ops/code_sensor.py:404-418`, where it
already attests the commit), so that every commit of the ledger has a cut; the trough, when the
frontier moved since the last record; and the owner's command. At the kilobyte a row the
attestation ledger takes in the repository's records
(`docs/experiments/corpus-measurements-2026-11-07.md:107`) a recorded cut is about two kilobytes
with its row. A record a job would be tens of megabytes a day at the job rate those records show
(720 an hour, `corpus-measurements-2026-11-07.md:94-95`); a record a sensed commit and a moved
trough is far less, and the cadence is parked (SN-a).

### 3.4 Names

`as of` takes a string, and the string resolves to a frontier. The shapes do not overlap:

| name | resolves to | exact |
|---|---|---|
| `head` | the head cut; the answer is the answer without `as of` (`view_head`) | yes |
| `cut:` and a recorded cut's id, or a prefix that names one | that record's frontier | yes, and checkable against its certificate |
| a commit's sha or an unambiguous prefix, as today | the cut recorded when the sensor read the commit; where none was recorded, the commit on `repo` and the empty prefix on every chain whose horizon is later (§8) | on `repo` always; elsewhere from the first recorded cut |
| a date or a date and time | the last recorded cut whose bookmark is at or before it | to the cadence of the records; the answer names the cut it read |

Wall time enters in the last row only, as a lookup key into bookmarks, and the cut it selects is
ordered by the chains (Law C4; the staging store's sweep resolves wall time to a generation the
same way, `staging.py:26-30`). A commit is resolved by the moment the palace read it, which is an
event of its own chains, and not by the commit's date, which is another clock's. A branch or a
tag is not a name: it moves. The grammar does not change; the names it accepts do, and the answer
always carries the cut read. `[INFERENCE, falsifier SNF-3]`

### 3.5 Consistency and resolution

An event of one chain may read from an event of another: `R k i k' j` says the `i`-th event of
chain `k` reads from the `j`-th of chain `k'` (the event clock's generators g2 and g3). The
references between the chains of §3.1 are these. `[ESTABLISHED: read off the writers]`

- a landing reads from its attestation and, where the place keeps chains, its version row, by the
  order the writer lands them in (`core/ingest/writer.py:397-436`: the version, the attestation,
  the key last);
- a causal edge reads from the turn that witnessed it and, when it ends at a commit, from the
  commit (`causal_edges.py:58-60`, `integrator.py:134-137`);
- a citation reading reads from its commit;
- an interpreted artifact reads from its subjects' landings and from the run that produced it;
  a relation edge from the landings of its two endpoints;
- a recorded cut reads from the prefix of every chain it certifies.

A cut is **consistent** when every source of an event inside it is inside it (`Consistent`): no
fact whose sources lie after the cut, every cross-chain reference closed. `[THEOREM: SNP-8]`

- Consistent cuts are closed under the pointwise meet and join, with the empty cut at the bottom
  (`Consistent.inf`, `Consistent.sup`, `consistent_zero`): a sublattice of the cuts, so a
  distributive lattice (`consistentCuts`).
- They are the event clock's cuts among the frontier cuts: a cut is consistent exactly when the
  events under its frontier are a down-set of the order the chains and the references generate
  (`consistent_iff_isCut`, on CLK-2's `IsCut` and `frontierCut`).
- Every frontier has exactly one greatest consistent cut under it, and a later frontier has a
  later one (`exists_resolves`, `Resolves.unique`, `Resolves.mono`); a consistent frontier is its
  own (`resolves_self`). This is what a name's resolution is.
- Consistency is append invariant: the references a store gains by growing start at events at or
  past its old head, so a cut inside the old head that was consistent stays consistent
  (`Consistent.of_grown`).

So ING-7's invariant, that a key implies its rows, holds at every consistent cut and not only at
the head: a cut that holds a landing holds its attestation and its version. `[DERIVED]`

**Where the references are recorded.** The resolver has to know, for an event, where its sources
lie. Each row of a chain that reads another records the head of the chain it reads at the moment
the row was written: the landing's `att_head`, a kept generation's birth (§5.4), a causal edge's
turn and commit, a recorded cut's whole frontier. With one writer a row's sources were all
written before it, so the head at its writing bounds them, the bound is sound (it can only make
fewer cuts consistent, each of them consistent for the true references), and it rises along the
chain. `[DERIVED from the one-writer rule, dn-ingress D3]`

**The resolver.** A name that selects a recorded cut needs none: the record is consistent. For
any other frontier it is a descent: lower each chain's position to the first event inside the cut
whose recorded bound lies outside it, and repeat until nothing moves, which is at most as many
passes as the frontier has positions. The library proves the cut exists and is unique; the attack
module runs the descent against the definition by enumerating every cut under the frontier (seed
461), and SN-2 transcribes that descent. `[THEOREM for existence and uniqueness; the descent
attacked, not proved]`

### 3.6 Certificates

The certificate of a cut is, for each chain, the digest of its prefix under the chain's hash
(`certify`): for a landing log the `hash` of the row at the position, for `repo` the commit's sha,
which is git's own chain, for `chat` and `att` the running hash of the chain table SN-2 adds
beside them. A store verifies a certificate when its own prefixes have those digests (`Verifies`).
`[THEOREM: SNP-9]`

- **Reproducible.** The certificate of a cut verifies on every extension of the store
  (`verifies_certify_of_extends`): the same store later, a restored backup, a clone.
- **Checkable.** Under a collision-free digest, two stores that verify one certificate have the
  same read at its cut (`Verifies.readAt_eq`), so every derived view at it is the same on both
  (`Verifies.view_eq`). The control is a digest with collisions, under which two different chains
  of one length agree (`Witness.digest_collides`).
- **Cheap.** A certificate extends over the events since an earlier one
  (`certify_digest_readBetween`), and the meet and the join of two certified cuts are certified
  from the two certificates alone, chain by chain the earlier or the later digest (`certify_inf`,
  `certify_sup`).
- **Compatible with erasure.** A chain that digests commitments keeps every certificate when an
  event's content is erased (`verifies_purge`), and what a reader then reads is the store with
  holes (`contents_purge_committed`).

Checking a certificate against a store is one seek a chain, the stored hash at the position
against the certified digest, 3 microseconds; recomputing a chain from its first row is the
audit, 0.8 s for a million rows. `[MEASURED §11]`
