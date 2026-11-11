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
    is the landing log (§12).** `[INFERENCE, falsifier SNF-11]`

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
| the plane's supersession log (`plane.py:282-289`) | `seq` per path | (path, seq) | a purge deletes entries and the next entry takes the position again (`plane.py:491-495`, `:552-553`) `[MEASURED §11]`; a reset drops it (`plane.py:628-640`); an instance with no plane has none; under lazy embedding it is written by the drain, in the drain's order, and only for the versions still current then (`core/ingest/derive.py:85-118`) |
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
   (`launcher.py:1779-1780`). The lexical index and the relation edges are not among the targets,
   so they outlast a reset with rows about items that are gone. Whatever the intent, no chain of
   an instance survives a reset with its positions, so a reset opens a new history (§8).

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

## 4. Reads

### 4.1 `read_at` and `read_between`, ledger by ledger

`read_at(c)` is the prefix of a chain at a position and `read_between(a, b)` the events after `a`
and up to `b` (`readAt`, `readBetween`). The second composes with the first and with itself
(`readAt_append_readBetween`, `readBetween_append`), so nothing more is needed of a ledger than
these two. `[THEOREM: SNP-3]` For each ledger, the read, the index it needs and its cost:

| ledger | `read_at(c)` | `read_between(a, b)` | index | cost |
|---|---|---|---|---|
| landing log, a class | one path: its last event at or under `c`; every path: the rows with `seq ≤ c` not closed at or under `c` | the rows with `a < seq ≤ b` | the primary key, `landings_path`, `landings_closed` | one path 3 to 4 µs through `landings_path`, and 6 ms when the planner takes the primary key, so the statement names the index; 1,000 positions 0.7 ms; every head §4.2 `[MEASURED §11]` |
| a document's version chain | the log's rows of the identity at or under `c` | the same rows in the range | `(class, doc_id, seq)`, partial where the identity is not the path | as one path's |
| raw objects | the object of the digest the log names at `c` | the objects the delta names | none: content-addressed | one file |
| chat log | a session's turns whose chain number is at or under `c` | the turns numbered in the range | the chain table's key and its `(session, turn)` | a range |
| attestations | by id, as today; in order, the chain table at or under `c` | a range of the chain table | the chain table | a range, where `all()` sorts the ledger by wall time and `producers_of` decodes every record today (`core/attestation/store.py:127-132`, `:159-165`) |
| citation readings | the reading of the commit, as today | the paths whose blob differs between the two commits, by the commit ledger's `files` rows (`ops/code_snapshot.py:59-69`), with their readings at each | exists: `(target_ref, commit_sha)` and `(source_ref, commit_sha)` (`reference_edges.py:149-156`) | as today |
| commit ledger | the commit and, through git, its ancestors | git's range | none: the ledger keeps no parent, so the range is git's | git's |
| staging | `read_at(g)`, as built | the rows admitted or tombstoned in the range | `staged_rows_generation` exists; none on the tombstone stamp | as built |
| run ledger, verdicts, observation history | by key; in insertion order | a range | a sequence number, when a consumer needs one | none needs one yet |

The landing log's two reads are the ones every other store's read at a cut goes through, since
it is the log that says which version of a path a cut holds (§5).

### 4.2 Every head at a cut

Reading the head of every path of a class at a cut is the rows with `seq ≤ c` whose `closed_at`
is absent or above `c`. On a synthetic log of a million events over 100,000 paths it took 149 to
163 ms at the middle cut and 246 to 285 ms at and near the head. `[MEASURED §11]` The cost is the
part of the log the statement walks, not the size of the answer. Two readers need it: the
universe, for the strata it loads whole (`core/sentence/universe.py:275-299`), and the lexical
statistics at a cut (§5.3). The bound is the journal form: the heads kept at some recorded cuts
and continued over the events since (`stateAt_eq_foldl`), which costs the distance to the nearest
kept cut instead of the prefix. It is parked until an instance shows the need (SN-c). `[THEOREM
for the journal; INFERENCE for parking it, falsifier SNF-6]`

### 4.3 What the reads cost in bytes

A landing is 409 bytes in the log with its two indexes (the table 315, the path index 67, the
closing index 27), measured without the two integer columns `version` and `att_head`.
`[MEASURED §11]` A chain table's row is an integer, the row's key and a 32-byte hash. A recorded
cut is about two kilobytes (§3.3). None of it is content: the log holds paths, digests and
titles, which the catalog holds already.

## 5. Derived data as a function of a cut

### 5.1 The rule and the four forms

A derived view at a cut is a derivation applied to the prefixes (`view`), and a reader of a store
at a cut is append invariant exactly when it is one (`appendInvariant_iff_exists_view`). On a
store of keyed writes three ways of holding such a view agree: recomputed from the prefix
(`stateAt`), journaled from a checkpoint over the delta (`stateAt_eq_foldl`,
`foldAt_readBetween`), and kept by generation, a row valid from the cut that contains its write
up to the cut that contains the key's next one (`genRead_gens`). The store rewritten in place
determines no read at a past cut (`Witness.stateOf_forgets`). `[THEOREM: SNP-5]` So the choice
among the three is cost, store by store. A fourth form is a way of storing the third: immutable
segments under a versioned manifest, where the manifest's version is the position. The vector
table is built that way, and §5.2 says why its versions are not the snapshot.

| derived store | a function of | held as | what it costs here | what would change the choice |
|---|---|---|---|---|
| vectors (atoms, occupancies) | the chunk's text and the embedder's identity | version-keyed rows the plane keeps already; the log selects the version | no new bytes; a search over superseded rows, then a join with the heads at the cut | an instance that must drop superseded atoms (§9), after which a cut finds them pending |
| lexical units and postings | the chunk's text and the tokenizer's identity | version-keyed rows the index keeps already; the log selects the version; the statistics from the mask | no new bytes; 4,179 bytes a kept unit on synthetic text `[MEASURED §11]` | a query at a past cut over its budget at the instance's size: then statistics stored per class and per recorded cut |
| chat events, causal edges | the transcript as retained at the cut, and the commits inside the cut | recomputed at the cut, the present rows a cache of the head | 6 ms a session of 2,000 records `[MEASURED §11]`; no bytes | a sentence that walks the causal fiber at a past cut over a second on a real instance (SNF-5): then generations, written with a diff |
| interpreted artifacts, hyperedges, relation edges, claim ops | a model's output: of nothing that can be computed again | generations, the replaced row archived with its interval | one archived row a replacement, which is thrown away today | a measured churn so low that declaring them outside the snapshot loses nothing |
| the similarity backbone | the vectors of the support | recomputed, as today | nothing | nothing |
| citation readings | the tree at the commit | one whole reading a commit, as built | 3,029,562 rows over 1,487 commits at 567 bytes a row in the repository's records | the store's size: then a row valid over a range of commits (SN-b) |
| code memberships | git's blob at the path | version-keyed by blob; git's tree selects the version | nothing new | nothing |
| the utility field (not built) | the use log | a fold with kept checkpoints | a checkpoint a declared number of ticks | its own note's measurements |

The figures for the citation readings are `docs/experiments/corpus-measurements-2026-11-07.md:106`
and `core/reference_view.py:15-16`.

### 5.2 Vectors

An atom is one chunk text under one embedder: its id is its layer and the hash of its text
(`core/stores/plane.py:113-115`), the plane records the embedder's identity and refuses another
(`plane.py:350-362`), and an occupancy says that a document at a version holds an atom at a
position (`plane.py:268-278`). So a vector is a function of a content digest and an embedder
identity, and a past version's vectors are still in the plane: a superseded version's occupancies
and atoms stay, and only `current` moves. `[ESTABLISHED]` The vectors at a cut are therefore the
atoms of the versions the landing log says were the heads at the cut: a read of the plane with
its superseded rows (`plane.py:772-821`) joined with the heads. `[DERIVED from SNP-5]`

Three things follow.

- **No stamp on the rows.** The interval a version's rows are valid on is read from the log. A
  stamp on the rows would have to be a set of intervals (§2.3, item 3).
- **Not the table's own versions.** The vector table keeps a dataset version a write, and an
  earlier version can be read. After a purge the purged text was still returned by eight and by
  five of the table's ten versions, and the compaction that removes it leaves one version, so it
  removes every earlier snapshot with it. `[MEASURED §11]` A manifest's version cannot be both
  the position a snapshot is read at and something an erasure reaches. The cut is a predicate on
  rows, taken from the log; the manifest stays a physical form.
- **The embedder's identity is the present's.** After a model change the plane is reset and the
  drain derives the current versions only (`core/ingest/derive.py:85-118` lists the active
  entries the plane does not hold current), so a superseded version has no vector. At a cut such
  a version is pending, and a semantic clause ranks it by the lexical index or reports it, which
  is ING-21's rule read at a cut. Deriving it is the same drain run over the versions a cut
  holds. `[DERIVED from ING-19, ING-21]` A snapshot is of content, not of the geometry in force
  when the content landed (decision D5, §13).

### 5.3 The lexical index

The index keeps every version's units and postings and marks the head
(`core/stores/lexical.py:56-82`, `:251-256`), and it computes its statistics at query time over
the current units of the reader's classes: the unit count and the mean length
(`lexical.py:316-321`) and each term's document frequency (`lexical.py:337-340`).
`[ESTABLISHED]` At a cut the arithmetic is the same with one predicate changed: a unit counts
when its version is its path's head at the cut, in place of `current = 1`. The collection size,
the mean length and the document frequencies are then the masked set's own, which is what makes
a score at a cut the score the index gave then under the same tokenizer. A clearance and a cut
are the same kind of thing to this index: a mask over units whose statistics must be the mask's.
`[DERIVED]`

The other forms cost more here. Recomputing means tokenizing every item alive at the cut, since
the statistics are the collection's and not the support's: right for a few hundred notes, not for
a corpus. A journal of the changes to the document frequencies has an entry a term a unit, no
fewer than the postings (122 a unit on the synthetic text). An index with its statistics built in
cannot serve a cut, or a clearance, without a copy a mask; if the index moves to immutable
segments, a segment has to carry its statistics per class and per recorded cut, or leave them to
be computed from the mask. `[INFERENCE, falsifier SNF-7]` The tokenizer's identity is the
present's, as the embedder's is: a changed tokenizer resets the index (`lexical.py:180-194`) and
the backfill lands the active items, so a superseded version's units are derived again from the
raw store when a cut asks for them.

### 5.4 Model output

Interpreted artifacts, relation edges and claim ops are written by passes that call a model, and
each is keyed by what it is about, so a later pass over the same subjects replaces the row
(`core/stores/derived.py:209-216`, `core/stores/edges.py:88-106`). The output cannot be computed
again, so the two choices are to keep it by generation or to declare it outside the snapshot.
This note keeps it. `[INFERENCE, falsifier SNF-8]`

The form is the one the observation stores use: archive, then replace
(`core/stores/code_observations.py:211-254`, `core/stores/observation_history.py:46-56`). Each
store gets a sequence number a write (its chain; the three are written `interp` in §3.1), each
row the number it was written at, and a replaced row goes to a history table with the number it
was replaced at. The read at a cut is the row whose interval holds the position (`genRead`), and
at the head it is the present row (`genRead_gens_length`). `[THEOREM: SNP-5, SNP-4]`

A kept row is served at a cut only when its sources are there. An artifact's subjects and a
relation edge's endpoints are content digests (`derived.py:186-189`, `edges.py:39-40`), so the row
is about particular versions: it is in the snapshot when it was written at or under the cut, every
digest it names is some path's head at the cut, and none of them is erased or sealed
(`mem_serve_iff`). `[THEOREM: SNP-7 for the erasure; DERIVED for the heads]` Until SN-6 builds
this the three stores serve two positions, the empty prefix and the head (§7.1).

### 5.5 The causal fiber

The events of a session and its causal edges are a deterministic function of the transcript and
the commit ledger (`core/chat_events.py:136-176`, `core/integrator.py:118-164`), so recomputing is
exact, and it is the definition here. At a cut: for each session, the transcript is the raw
object the session's last turn inside the cut names (`core/chat_events.py:211` takes the last
row's digest the same way for the head); its events are extracted and kept when their turn is
inside the cut; a commit event resolves against the commits inside the cut on `repo`. `[DERIVED
from SNP-5]`

This repairs three things the stored rows have today (§2.3, item 4). The result no longer depends
on the order in which the projector, the integrator and the code sensor ran. An event whose
result arrived after the cut is read without it, as it stood. And an edge is named by its session,
its event's order and its endpoint, which a session's growth does not change.

The cost is an extraction a session: 6 ms for a synthetic session of 2,000 records and 0.79 MB.
`[MEASURED §11]` The builder reads the causal store whole once a sentence
(`core/sentence/universe.py:581-595`), so at a cut it would extract every session with a turn
inside the cut, and a memo keyed by the session and its transcript's digest makes each
extraction happen once a process. Generations are the alternative: the rows kept, keyed by
session and order, each with the range of `chat` positions it was valid on, written with a diff so
that a session's growth adds its new events and closes only the rows that changed. They cost a
rewrite of the projector and the integrator and are kept for the instance that needs them
(SNF-5).

### 5.6 An instance with no embedder

Nothing above reads the plane to learn what existed. The node set of a snapshot comes from the
landing log, which lives in the catalog's file; the lexical units, the version chains, the causal
fiber and the citation readings need no vector; and a semantic clause on such an instance ranks
by the lexical index and says so, at a cut as at the head (ING-21). The plane's own supersession
log could not carry this: an instance with no plane has none, and under lazy embedding it records
the order in which the drain reached the items, not the order in which they landed. Today the
universe takes the mirror's nodes from the plane's rows (`core/query.py:462-465`); at a cut it
takes them from the log. `[DERIVED; ESTABLISHED for the present reads]`

## 6. Erasure and scope

Two things are parameters of a read and no function of the cut, because they are the present's:
what has been erased, and what the asker may see.

### 6.1 A purge leaves a hole

No erased event is visible at any cut (`not_erased_of_mem_visible`), a larger erasure shows a
sublist (`visible_sublist`), and two stores that differ only in erased events give every
derivation the same reading at every cut (`erased_invisible`): erased content is an argument of
no read. `[THEOREM: SNP-7]`

The erasure keeps positions. The store with a hole at each erased event has the head it had and
commutes with the cut (`head_redact`, `redact_readAt`); an erasure that deletes rows moves the
later ones up, and a read at a cut then holds an event from after it (`Witness.compact_moves`).
`[THEOREM]` The plane's supersession log is the second kind today: after a purge, a later landing
at the path took position 1 again. `[MEASURED §11]` In the landing log a purge empties the row:
the path, the identity, the digest, the title and the salt become null, and the commitment and
the hash stay. The certificates keep verifying (`verifies_purge`), a reader reads a hole
(`contents_purge_committed`), and since the commitment was salted and the salt is gone, it can no
longer be tested against a guess of the content. `[THEOREM: SNP-9 for the chain; DERIVED for the
salt]`

That last point is a rule the record already has: no tombstone keeps a content hash of purged
private text (`docs/design-notes/vector-membership-store.md:810-813`). A digest of purged bytes
is a test for those bytes. What a purge has to reach, against what it reaches today:

| store | today, after a purge `[MEASURED §11]` | what a snapshot needs |
|---|---|---|
| raw object, catalog row, plane occupancies and their freed atoms | removed | the same, and the log's rows emptied |
| the vector table's earlier dataset versions | still return the text | the purge ends with a compaction that keeps no earlier version |
| lexical units, postings and version records | remain, with the words | removed with the plane's rows |
| the version chain's rows | still name the digest | the digest nulled, the row and its number kept: a second owner-gated write beside the relabel (`core/stores/versions.py:132`) |
| relation edges and artifacts that name the digest | untouched (read, not measured: `core/ingest/purge.py:58-62` names neither store) | not served (`mem_serve_iff`), and removed by the purge |
| the attestation ledger | still names the digest | open: decision D9 |
| a deletion attestation | none is written (`core/attestation/store.py:3-6` says one is) | one, of action `purge`, naming the commitment and not the digest |

Until the stores of the middle rows are reached, a read of them at a cut would return what a
purge left. So the erasure's reach is stage SN-3, and it lands before any of those stores is read
at a past cut (§12).

### 6.2 A retire seals

A vault delete is a tombstone: the catalog's row goes inactive and the raw object stays
(`catalog.py:160-172`). The requirement is that a tombstoned item does not come back through a
snapshot either. Two rules do that, both proved, and they are ordered.

- **The stricter seal** (`servedAt`). A retire among the events past the cut closes the cut for
  that identity. Once the chain retires an identity, no cut before the retire serves it
  (`servedAt_append_of_retire`); growth that does not retire it changes nothing
  (`servedAt_append_of_no_retire`); so growth changes a served value only by removing it
  (`servedAt_of_append`).
- **The looser seal** (`servedNow`). An identity is withheld at every cut exactly while it is not
  live at the head. It serves everything the stricter one serves (`servedNow_of_servedAt`), keeps
  an identity that is retired now out of every cut (`servedNow_of_not_live`), and is lifted by a
  later landing, which brings the past back (`Witness.servedNow_restores`). `[THEOREM: SNP-7]`

This note takes the stricter seal, keyed by identity, with an `unseal` event that only the owner
writes. `[INFERENCE, falsifier SNF-10]` The reason is in the code: a new row's identity is its
path unless it declares one (`catalog.py:103-110`), so a different note written later at a
deleted note's path has the deleted note's identity, and under the looser seal it would bring
the deleted note's versions back at the earlier cuts. The seal is by identity and not by path so
that a rename seals nothing: the old path's tombstone is a `move` (§3.2). The cost of the
stricter seal is also in the code: a rescan tombstones every catalog path whose file is gone
(`core/ingest/sync.py:262`, `:285-286`), so a vault that is missing at a rescan seals every
note's past, and the owner lifts it with one `unseal` over the range.

The seal is read off the whole chain, the present, and off no prefix of it: one more seek, the
position of the identity's last retire that no later `unseal` names. At the head nothing is
sealed (`servedAt_length`).

### 6.3 The grant is the asker's now

A snapshot under a grant is the read at the cut restricted to the chains the grant names and,
within them, to the events it may see named (`snapshot`). The grant is no function of the cut.
`[THEOREM: SNP-6]`

- A narrower grant's snapshot is the restriction of a wider one's, at every cut
  (`snapshot_narrow`): what a wider grant was shown at a cut bounds what a narrower one is shown
  there.
- It reads only the chains the grant names and the cut's positions on them (`snapshot_congr`),
  and it is append invariant (`snapshot_grow`).
- Restricting to whole chains commutes with the cut (`restrict_readAt`). Filtering events before
  the cut does not: it moves the positions (`Witness.filter_before_cut`), and a position on a
  chain counts the events a filter hides (`Witness.position_channel`). So an event filter is
  applied after the read, and what must be hidden in number is hidden by chain, which is why the
  landing log is a chain a class.

Two consequences for the surface. An answer names the cut it read on the chains the asker's grant
names and on no other, and the bounds a row records (§3.5) are never shown: `att` mixes every
class, so its positions count other classes' landings. And a class is a row's class now: a
whole-class relabel renames a chain, and nothing else moves a row between chains (ING-17).
`[DERIVED]`

### 6.4 A reader that is shown only named endpoints

Take a read-only principal that is shown a causal edge only when the edge ends at a commit or
at a file git tracks at `HEAD`. That rule is an event filter in the sense of §6.3, and at a cut
it is the present's filter applied to the edges inside the cut: an edge is shown when its
witness turn is inside the cut on `chat`, its commit, if it ends at one, is inside the cut on
`repo`, and its endpoint passes the list as the list stands now. The list is not taken at the
cut's tree. `[DERIVED from SNP-6]` Two reasons. The grant is the asker's now, so a file that left
the tracked tree since the cut is withheld at the cut as it is at the head, and no cut shows a
name the head withholds. And the filter is then applied after the read, which is the order
`restrict_readAt` and its control require. The principal's snapshot is the restriction of the
owner's at every cut (`snapshot_narrow`). The alternative, the list taken at the cut's tree, is
decision D11.

## 7. The sentence surface

### 7.1 The cut asked and the cut read

A sentence has one cut, as today (§2.1). The name resolves to a frontier, the cut asked (§3.4).
Each chain serves some positions exactly: every position from its horizon to its head (§8), and
the empty prefix; a store that keeps no past serves the empty prefix and the head. The read is
taken at the greatest consistent cut under the frontier asked every position of which is served
(`ResolvesIn`). `[THEOREM: SNP-10]`

- It exists and is unique whatever the stores serve (`exists_resolvesIn`, `ResolvesIn.unique`).
- It never passes the cut asked (`ResolvesIn.le_resolves`), so what is read is a prefix, chain by
  chain, of what the cut asked holds (`readAt_mono`): a read under `as of` holds no event from
  after the cut it names.
- It rises with what is served and with the frontier (`ResolvesIn.mono`): as the stages of §12
  give stores a past, the cut read climbs toward the cut asked and never falls.
- When every position is served it is the resolution of the frontier (`resolvesIn_univ`), and at
  the head, which is consistent because a store holds the sources of its own events, it is the
  head (`resolvesIn_self`).

The answer is then exact for the cut it names: every law of §10 holds at the cut read. What the
answer says is that cut. It carries one note with the cut asked, the cut read on the chains the
asker's grant names (§6.3), and each chain on which the two differ with the reason: the store
keeps no past, the cut is under the chain's horizon, or the stage that reads the store at a cut
is not built. For example, on an instance where the relation edges do not yet keep generations:

```
as of "9de5325d": read at the cut recorded when the commit was read (cut:4c1f09a2).
land:authored-solo 412, chat 9318, repo 9de5325. Not read at the cut: the relation edges
keep no past and were read at their empty prefix.
```

This replaces what the executor does today, which reads those stores at the head and says so
(`core/sentence/execute.py:719-725`). The head is later than the cut asked, and a reader that
ignores the cut is not append invariant: the same sentence gives another answer after the store
grows (`Witness.present_not_appendInvariant`). `[THEOREM: SNP-1]`

A store read at its empty prefix makes its clauses empty. That is the answer at the cut named,
and it is not a bound on the answer at the cut asked: `reach` and `relate` only lose members when
edges are missing, but `diffuse` normalizes by degree and `top` ranks, and both can move either
way (the executor says so of an assumption that removes weight, `execute.py:473-481`). So the
note is part of the answer's meaning. The alternative is to refuse such a sentence (decision D4).
`[INFERENCE, falsifier SNF-4]`

### 7.2 Each mode and each edge species at a cut

The mode of a clause follows from its scope (`core/query.py:273-281`).

| mode | verbs | what it reads at the cut | exact from |
|---|---|---|---|
| semantic | `near`, `diffuse S`, `reach S`, `relate` | the heads of the clause's classes, from the log; their vectors by content address and the lexical index for the pending ones (§5.2, §5.3); the backbone recomputed among them | SN-4; `relate` SN-6 |
| structural | `reach F`, `diffuse F`, `walk` over `F` | the citation reading of the cut's commit | today |
| temporal | `trace`, `reach D`, `walk` over `D`, `changed` (§7.4) | the version chain's prefix: the log's rows of the identity at or under the cut | SN-4; `changed` SN-8 |
| causal | `reach C`, `walk` over `C`, `witness` | the causal fiber recomputed at the cut (§5.5); an attestation at or under the cut on `att` | SN-5 |

| species | at a cut |
|---|---|
| `S`, similarity | recomputed from the vectors of the versions alive at the cut, within a stratum, as today (`core/sentence/universe.py:733-739`); no edge at a pending node |
| `F`, citation | the edges of the reading at the commit; a reading is whole, so nothing is inferred between commits |
| `D`, supersession | consecutive versions of the chain's prefix; at the node grain it is empty today and stays so (`universe.py:810`) |
| `C`, causal witness | an edge whose witness turn is inside the cut on `chat` and whose commit, if it ends at one, is inside the cut on `repo` |
| the signed relations (supports, contradicts, contextualizes) | a kept generation whose two endpoint digests are heads at the cut (§5.4) |
| an assumed edge (`assume`) | applied to the universe of the cut read; nothing is stored, and the result is a `Hyp` as today |

### 7.3 The verbs

- **`near`, `diffuse`, `reach`, `relate`, `walk`, `trace`, `witness`** read as their mode says.
- **`far`, `top`, `atleast`, `not`, `minus`, `and`, `or`, `then`, `within`, `over`** are the
  algebra on whatever universe the clauses built. Their laws (QSA-1 to QSA-4, QSA-10) are stated
  for any universe, so they hold at a cut with no change. `over` masks by a row's class, which is
  its class now (§6.3).
- **`read`.** A repository path: git's blob at the cut's commit, as today, with the commit shown
  on the hit. A note or a dialogue turn: the raw object of the digest the log names for the path
  at the cut, never the vault file, which is the present and can be newer than the catalog
  (§2.1). A hole reads as erased and a sealed identity as nothing (§6). A transcript turn: the
  chat log's row when its number is at or under the cut.
- **`witness`.** The record when it lies inside the cut: an attestation by its number on `att`, a
  causal edge by its turn and its commit, a citation edge by its commit.
- **`assume`.** The overlay applied to the universe of the cut read: a hypothetical at a past cut.
- **`do`.** A request is a whole sentence and takes no adjective (`core/sentence/grammar.py:4-5`),
  so it cannot be written under `as of`: a write has no past.

**`as of "head"` is no `as of`.** At the head cut the read is the store (`readAt_head`), every
derived view is the derivation of the present (`view_head`), the generational store reads the
store rewritten in place (`genRead_gens_length`), a snapshot is the grant's restriction of the
store (`snapshot_head`), nothing is sealed (`servedAt_length`) and what is visible is the store
without the erased events (`visible_head`). `[THEOREM: SNP-4]` On the code this is the first test
of every stage: the same sentence with and without `as of "head"` returns the same hits.

**Refusals.** An ambiguous prefix, as today (`universe.py:471-475`). A name that selects nothing:
a sha no chain knows, a cut id no record has, a date before the first record; the refusal says
which names would resolve. A date after the newest bookmark is the head.

### 7.4 Between two cuts

One form is worth admitting, and it is a region:

```
changed between "<a>" and "<b>"          changed since "<a>"
```

Its members are the identities with an event in the delta, on the landing chains of the classes
the clause reads; `since` is `between` with `head`. `[INFERENCE, falsifier SNF-14]`

- **It is sound for what did not change.** An identity outside the region has the same state at
  both cuts (`stateAt_eq_of_not_written`). It over-approximates what did: a path that returned to
  the bytes it had is a member.
- **It composes.** The region between `a` and `c` is the union of the regions between `a` and `b`
  and between `b` and `c` (`readBetween_append`, `mem_readAt_iff`). `[THEOREM: SNP-3]`
- **It is cheap.** One range read of the log: 0.7 ms a thousand positions. `[MEASURED §11]`
- **It composes with the algebra.** A region masks a field or meets a region, so
  `near "x" within (changed since "<a>")` needs no new rule; its mode is temporal, since its
  window is not a point (`core/query.py:277`).

The general form, a sentence evaluated at two cuts with the difference reported as `assume`
reports its two universes (`execute.py:1045-1063`), is the `velocity of` that dn-graph-dynamics
designs as GD-4. This note supplies the two readings it needs and does not add a second way to
write it.

## 8. The exactness boundary

History is exact from the first retained generation and from no earlier. Each chain has a
**horizon**: the first position from which it serves every cut. Three things set one.

- **The genesis.** The landing log opens with the catalog as it stood (§3.2). What a path held
  before was never recorded, so the positions before the genesis rows end are under the horizon.
  For the chat log and the attestation ledger the genesis is the rows they hold when their chain
  tables are added, in the order they were inserted.
- **Retention** (§9), which drops the generations closed at or under a declared position.
- **A reset**, after which every chain is a new chain (§2.3, item 7).

The law is the same for the three. A generational store that drops the rows closed at or under a
horizon reads, at every cut from the horizon on, the state recomputed from the whole prefix
(`genRead_prune_gens`), though the prefix is no longer held. Under the horizon it is never wrong:
a value it returns at a cut is the value the key held (`stateAt_of_genRead_prune`). But what it
lost it reads as absent, and nothing in the rows that remain tells a lost key from a key that was
never there (`Witness.prune_forgets`). Two horizons are the later one (`prune_prune`).
`[THEOREM: SNP-10]` The journal form says the same of a fold: continued from the state kept at the
horizon over the events since, it is the fold of the whole prefix (`foldAt_readBetween`), and the
chain's digest at the horizon, kept as the seed, lets every certificate from the horizon on
verify (`certify_digest_readBetween`). `[THEOREM: SNP-3, SNP-9]`

So the horizon is recorded, and a cut under it is not served.

- **Where.** As a `horizon` row of the chain, which the chain's hash covers, and in every
  recorded cut (§3.3). It only advances.
- **What a question before it gets.** The chain is read at its empty prefix (§7.1), and the
  answer says the cut is under the chain's horizon and names the first cut the chain serves. A
  sentence all of whose chains are under their horizons returns the note and no hit.
- **What that means today.** A commit read before the log exists resolves, on every chain but
  `repo`, under the horizon: `as of` such a commit reads the citation graph and the repository's
  files at the commit, which are exact, and nothing else. That is the lawful part of what it does
  now. The observation that the version store held one generation and so had nothing to
  snapshot (limits-of-the-algebra, L7) is this boundary seen from the other side.
  `[DERIVED]`

## 9. Retention and cost

### 9.1 What grows

A landing drops nothing today: a retired path's rows and a superseded version's rows stay in the
plane and in the lexical index (`core/stores/plane.py:497-499`, `core/stores/lexical.py:260-265`),
and rows go only with a purge or a reset. So the bytes of a past are mostly paid already, and
the snapshot adds three things.

| what | a | bytes | source |
|---|---|---|---|
| the landing log | landing | 409 | `[MEASURED §11]` |
| a recorded cut, with its attestation | record | about 2,000 | §3.3 |
| archived model output | replaced row | the row's | §5.4 |
| kept already: a lexical unit of a superseded version | unit | 4,179 on synthetic text, 122 postings a unit | `[MEASURED §11]` |
| kept already: a plane occupancy | row | 734 to 1,084 | `docs/experiments/corpus-stage1-2026-11-07.md:416`, `corpus-measurements-2026-11-07.md:104` |
| kept already: an atom | changed chunk | 2,215, of which the vector 1,536 | `corpus-measurements-2026-11-07.md:103` |
| kept already: a raw object | version | the version's bytes; a transcript's, whole, at each growth | §2.2 |

By arithmetic, not measurement: an instance with a hundred landings a day adds 41 kilobytes a day
to the log, 15 megabytes a year, and thirty recorded cuts a day add 60 kilobytes. The rows kept
already are what grows: with three versions an item, two thirds of the synthetic lexical index
were superseded versions. `[MEASURED §11]` What the snapshot brings is less a cost than the means
to stop paying one: a horizon makes it safe to drop.

### 9.2 The rule, counted in events

A chain can declare two windows, each in positions, and a retention pass runs at a recorded cut.

- **A window for derived rows.** The derived rows of the versions closed at or under the head
  less the window are dropped: lexical units and postings, plane occupancies, and the atoms
  nothing retained holds. No horizon moves. The log and the raw objects stay, so every read of a
  ledger at those cuts is still exact, and a derived row a cut asks for is pending and can be
  derived again (§9.3).
- **A window for the history.** The chain's horizon moves to the later of the horizon in force
  and the head less the window. A `horizon` row is appended first, so the positions under it are
  unserved from that moment; then the derived rows still under it, the raw objects no retained
  row names, and the log's rows closed at or under it are dropped, the chain's digest at the
  horizon kept as its seed.

The second is an exception to the rule that raw objects are kept
(`core/kernel/stores/rawstore.py:1-8`), which only the owner's purge makes today, so it is the
owner's to declare. Its order is the one the stores use for a cache: the horizon is declared
first, so a crash in the middle leaves rows that are no longer served, never a position that is
served and incomplete (the discipline of PLN-4, where a cache is stale only by excess).
`[DERIVED]` The attestation ledger and the version chains are not pruned: they are the audit
record, they are small, and they have no delete.

A window is counted in events because wall time orders nothing (Law C4): the last ten thousand
landings of a class, not the last ninety days. It is one position a chain, not a number of
versions an identity. Keeping the last `n` versions of each identity would leave no horizon:
which cuts are exact would differ from one identity to the next, and the control of §8 says such
a store cannot tell what it lost. `[INFERENCE, falsifier SNF-9]`

The default instance declares neither window and keeps everything; by the arithmetic above its
log is megabytes a year. An instance that must bound its disk declares the first, and the second
only by its owner's decision (D8).

### 9.3 Lazy landing, in time

Under lazy embedding an item is complete without its vector, and the drain derives the vectors of
the current versions (`core/ingest/derive.py:85-118`). A version superseded before the drain
reached it never gets one. So at a past cut the plane can hold nothing for a version that was
the head, and the rule is the one two-phase ingestion already has: the item is pending, a
semantic clause ranks it by the lexical index or reports it, and no vector is invented (ING-21).
`[DERIVED from ING-19, ING-21]`

The first window of §9.2 and lazy derivation are then one mechanism run in two directions. A
derived row is an entry of a cache of a function of a content digest and an identity (§5.2,
§5.3): present or absent, reported when absent, derivable again from the raw object while the
ledger holds it. The drain run over the versions a cut holds derives what a cut's readers ask
for, and nothing obliges an instance to derive a past nobody reads.

### 9.4 The utility field

The field is the fold of its update over the use log (UTL-4, `evolve_append`), so it is a derived
view in the sense of §5: its use log is a chain of the cut, its tick the position, and the field
as of a cut is the fold of the prefix, continued from a kept checkpoint over the uses since
(`foldAt_readBetween`). `[THEOREM: SNP-3 with UTL-4]` That answers the first open question of
dn-utility-field: the field's clock can be a chain of the cut, and then the field as of a cut is
exact. Two more things follow.

- **The use log has a natural horizon.** A site left alone returns within `ε` of its baseline
  after `log(c/(lam ε))/lam` ticks (UTL-2, `idle_window`), so a horizon that far behind the head,
  with the field's state at the horizon kept, is exact from the horizon on and loses nothing a
  reader of the present could see. `[DERIVED from UTL-2 and SNP-3]`
- **The field can order what retention drops.** When a window forces a choice among the derived
  rows of superseded versions, the ones whose sites stand at the baseline were not used for
  anything that produced value, and go first. `[HYPOTHESIS: checked by comparing, on the corpus
  instance, how often a pass ordered by the field drops a row a later cut asks for against a
  pass ordered by age; falsifier SNF-9]`

## 10. The laws

Each law is stated so that it becomes a property test when its stage is built, and is proved
now. The Lean names are in `formal/Palace/Snapshot.lean`, the attacks and controls in
`formal/PalaceTest/Snapshot.lean`, by seed. `[THEOREM]` throughout.

- **SNP-1 append invariance.** A read at a cut inside the store, a read between two such cuts
  and every derived view are unchanged by any growth of the store (`readAt_grow`,
  `readAt_of_extends`, `readBetween_grow`, `appendInvariant_view`), also under an erasure and a
  grant (`visible_grow`, `snapshot_grow`) and for the keyed forms (`stateAt_append`,
  `genRead_gens_append`). Controls: the reader that ignores the cut
  (`Witness.present_not_appendInvariant`); a read at a cut past the head (seed 431). Attacks 430,
  432, 446. The test, at SN-1: over random sequences of catalog writes, `read_at(c)` taken after
  every further write equals the one taken when `c` was the head.
- **SNP-2 monotonicity.** The read at an earlier cut is a prefix, chain by chain, of the read at
  a later one, and a cut of a cut is the meet (`readAt_mono`, `mem_readAt_of_le`,
  `readAt_readAt`, `head_readAt`, `visible_mono`). Control: the read at one cut taken for a prefix
  of the read at any other (434). Attacks 433, 435. The test, at SN-1: for `a ≤ b`, `read_at(a)`
  is a prefix of `read_at(b)`.
- **SNP-3 composition.** The read at `a` followed by the read between `a` and `b` is the read at
  `b`, and two adjacent reads-between compose (`readAt_append_readBetween`, `readBetween_append`);
  a fold continued from a checkpoint over the delta is the fold of the prefix
  (`foldAt_readBetween`, `stateAt_eq_foldl`); an event, or a pair of events, read at the later cut
  was read at the earlier one or lies in the delta (`mem_readAt_iff`, `pair_readAt`); a key the
  delta does not write has one state at both cuts (`stateAt_eq_of_not_written`). Controls: the
  two cuts in any order (437); a key's state taken for unchanged whatever the delta writes (477).
  Attacks 436, 438, 439, 447, 475, 476. The test, at SN-1: the catalog rebuilt from the state at
  a checkpoint and the delta equals the catalog; at SN-8: the region of §7.4.
- **SNP-4 idempotence.** The read at the head cut is the store, and every reading at it is the
  present's (`readAt_head`, `readAt_of_head_le`, `view_head`, `genRead_gens_length`,
  `snapshot_head`, `servedAt_length`, `servedNow_length`, `visible_head`). Attack 440. The test,
  at every stage: a sentence under `as of "head"` returns what it returns without.
- **SNP-5 a derived view depends only on the prefixes.** A reader is append invariant exactly
  when it reads only the prefixes, exactly when it is a derived view (`prefixOnly_view`,
  `view_congr`, `appendInvariant_iff_prefixOnly`, `appendInvariant_iff_exists_view`). For keyed
  writes the generational store read at a cut is the state recomputed from the prefix and the
  key's last write inside it, and at most one generation of a key is alive at a cut
  (`genRead_gens`, `stateAt_eq_lastWrite`, `length_filter_selects_le_one`). Controls: the store
  rewritten in place (`Witness.stateOf_forgets`, 444); generations without the closing stamp
  (445). Attacks 441, 442, 443. The test, at SN-1: the three reads of the log agree at every
  position, and no path has two rows alive.
- **SNP-6 grant restriction.** A narrower grant's snapshot is the restriction of a wider one's;
  a snapshot reads only the chains the grant names and the cut on them; restricting to chains
  commutes with the cut (`snapshot_narrow`, `snapshot_congr`, `snapshot_grow`,
  `restrict_restrict`, `restrict_readAt`). Controls: an event filter applied before the cut
  (`Witness.filter_before_cut`, 449); positions that count hidden events
  (`Witness.position_channel`, 451). Attacks 448, 450. The test, at SN-4: of two grants one under
  the other, the narrower answer at a cut is the wider one masked, and landings of a class the
  grant does not name change neither the answer nor the cut it shows.
- **SNP-7 erasure dominance.** No erased event is visible at any cut; a larger erasure shows a
  sublist; the store with holes keeps every position; stores that differ only in erased events
  read the same at every cut; a kept row is served only when none of its sources is erased
  (`not_erased_of_mem_visible`, `visible_sublist`, `head_redact`, `redact_readAt`,
  `visible_eq_reduceOption`, `visible_congr`, `erased_invisible`, `mem_serve_iff`,
  `serve_sublist`). A key retired after a cut is served at no earlier cut, growth changes a served
  value only by removing it, and the looser seal serves what the stricter one serves
  (`stateAt_of_servedAt`, `servedAt_append_of_retire`, `servedAt_append_of_no_retire`,
  `servedAt_of_append`, `servedNow_of_servedAt`, `servedNow_of_not_live`). Controls: the erasure
  that deletes rows (`Witness.compact_moves`, 455); the state served without the seal (458); the
  looser seal taken for a monotone one (`Witness.servedNow_restores`, 474); kept rows served
  without their sources (460). Attacks 452, 453, 454, 456, 457, 459, 473. The test, at SN-3: after
  a purge no read at any cut and no scan of the instance's files finds the purged words; after a
  retire no cut before it serves the identity.
- **SNP-8 consistent cuts.** They are closed under meet and join, a sublattice of the cuts; they
  are CLK-2's cuts among the frontier cuts; every frontier resolves to exactly one greatest
  consistent cut under it, monotonically; a consistent cut stays consistent as the store grows
  (`consistent_zero`, `Consistent.inf`, `Consistent.sup`, `consistentCuts`,
  `consistent_iff_isCut`, `exists_resolves`, `Resolves.unique`, `Resolves.mono`, `resolves_self`,
  `Consistent.of_grown`). Controls: a frontier taken for a cut (462); a consistent cut advanced
  by one position (464). Attacks 461, 463, 465. The test, at SN-2: the resolver against
  enumeration on small stores, and no recorded cut with a reference crossing it.
- **SNP-9 certified cuts.** A certificate verifies on every extension of the store; under a
  collision-free digest two stores that verify one certificate have the same read at its cut and
  the same derived views; a certificate extends over the delta; the meet and the join are
  certified from the two certificates; an erasure that keeps commitments keeps every certificate
  (`verifies_certify`, `verifies_certify_of_extends`, `eq_of_chainDigest_eq`,
  `Verifies.readAt_eq`, `Verifies.view_eq`, `certify_digest_readBetween`, `certify_inf`,
  `certify_sup`, `commitments_purge`, `verifies_purge`, `contents_purge_committed`). Controls: a
  digest with collisions (`Witness.digest_collides`, 468); a digest over contents, which an
  erasure changes (472). Attacks 466, 467, 469, 470, 471. The test, at SN-2: a certificate
  verifies after any further writes and on a copy of the files, and fails when one row under the
  cut is edited.
- **SNP-10 the horizon.** A generational store pruned at a horizon is exact at every cut from
  the horizon on and never wrong under it; horizons compose to the later one (`genRead_prune`,
  `genRead_prune_gens`, `stateAt_of_genRead_prune`, `prune_prune`). Among the positions the
  chains serve, every frontier resolves to exactly one greatest consistent cut, which rises with
  what is served and never passes the cut asked (`exists_resolvesIn`, `ResolvesIn.unique`,
  `ResolvesIn.mono`, `ResolvesIn.le_resolves`, `resolvesIn_univ`, `resolvesIn_self`). Controls:
  the pruned store read under its horizon (`Witness.prune_forgets`, 480); a frontier lowered to
  the served positions without the descent (483). Attacks 478, 479, 481, 482, 484, 485, 486. The
  test, at SN-4: the cut read is under the cut asked on every chain; at SN-7: every read at a cut
  from the horizon on is the same before and after a retention pass.

What the model leaves out, said plainly. A chain is a list and a store a family of lists: one
writer is assumed, and nothing is said of two. Events are opaque, and so is the stores' SQL. The
hash's collision freedom is a hypothesis of SNP-9 (`CollisionFree`), not a theorem about SHA-256.
The `unseal` and `horizon` events are not in the model of the seal, and the owner's gate on them
is the code's. A repository history with merges is covered by CLK-2's down-sets and not by the
chain model (§3.1). The descent that computes a resolution is attacked, not proved.

## 11. Measurements

Every figure in this note is from a synthetic fixture: a temporary directory or in-memory stores
built by the probe, the test suite's throwaway palace for the purge, and nothing of any
instance. One machine (Apple M2 Pro, 12 cores, 32 GB, macOS 27.0) with other work running, the
load average between 2.4 and 5; Python 3.15.2, SQLite 3.54.1, LanceDB 0.33.0; the code at
`e3e3ee47`. The timings are medians with their ranges. Each probe was run at least twice, and a
range across the runs is given where they differed. `[MEASURED]`

| probe | fixture | result |
|---|---|---|
| the landing log | the table of §3.2 without `version` and `att_head`, with its two indexes, in one SQLite file; one class, 100,000 paths, ten landings a path in a shuffled order, one transaction, every row hashed and the path's previous row stamped | 1,000,000 rows in 408.9 MB: 409 bytes a row (table 315, path index 67, closing index 27); 50,000 to 54,000 rows a second written |
| its reads | the same file, 200 repetitions a point read, 5 a scan | one path at the middle cut 3 to 4 µs through the path index and 6.0 to 7.1 ms when the planner took the primary key; 1,000 positions 0.69 ms; every head 149 to 163 ms at the middle cut (99,908 rows) and 246 to 285 ms at and near the head (100,000 rows); the chain's hash recomputed from the first row in 0.77 to 0.79 s; the stored hash at a position read in 3 µs |
| a kept version in the lexical index | `LexicalStore` on a temporary file; 500 items of 4 chunks in 3 versions, each chunk 171 words drawn from a vocabulary of 20,000 with frequencies falling as the inverse of the rank | 6,000 units held, 2,000 of them current; 734,409 postings, 122 a unit; 25.1 MB, 4,179 bytes a unit; superseded share 0.67 |
| what a purge leaves | the test suite's throwaway palace (`tests/fixtures/ingress.py:73`), lazy, with its fake embedder: two notes landed and drained, one edited and drained, then deleted from the vault, then both its digests purged (`purge_raw`); a control note never purged, found at every step | gone: the raw objects, the plane's occupancies and supersession entries, the catalog rows. Left: the words in the vector table read at versions 2 to 9 and 3 to 7 of its 10; the lexical units, postings, title and version records; both version rows; one attestation a digest |
| after the purge | the same palace: the vector table compacted with no retention; every SQLite file checkpointed, then vacuumed; a new note landed at the path | the compaction left 1 dataset version and no purged word in the table's files; the deleted catalog and plane rows' path and digest were still in the files' bytes after the checkpoint and gone after the vacuum; the plane's supersession log held position 1 for the path again, and the version chain appended number 3 |
| the order of two jobs | in-memory stores; one session with a commit event; the ledger holds the commit before the integrator's first pass, or gains it after | 1 edge against 0, and still 0 after a second pass, the session being skipped as unchanged |
| the events of a prefix | a transcript of four records: a prompt, a reply with a `git commit` call, the call's result with the sha, a reply | the prefix that ends before the result gives the commit event an empty reference; the whole gives the sha; the two longer prefixes agree with the whole |
| re-deriving a session | a synthetic transcript of 2,000 records, 0.79 MB, 7 repetitions | 6.0 to 6.1 ms median (5.7 to 7.2) |
| what `as of` accepts | the unit tests' store fakes; git read-only on the checkout | `as of "HEAD"` and `as of "2026-11-01"` refused; a sha prefix accepted; `read` of a repository path under a commit where the file differed returned that commit's blob and not the head's, under a note saying that `read` read the present |
| row numbering | a table keyed by text, five rows, in a temporary file | after the last row was deleted the next insert was numbered 5 again; a vacuum after a delete in the middle kept the numbers |

Not measured: anything on an instance's own stores; the lexical statistics computed from a mask
at a corpus's size; the causal fiber recomputed over a real instance's sessions; a vector search
with superseded rows joined to the heads at a cut; a retention pass. Each is the measurement of
the stage that builds it.

## 12. The build order

Nothing is built by this note. What the merge licenses is decision D12. The stages, each a pull
request against main with its tests and its rollback, each transcribing its laws and
property-testing the transcription against the Lean statements; the laws a stage relies on enter
`docs/LAWS.md` and `formal/Spec/` with it, as design theorems do when code comes to rely on them.

- **SN-1 the landing log.** The `landings` table of §3.2 in the catalog's file, created by the
  catalog's own migration (`core/stores/catalog.py:77-92`) and written inside `record`,
  `tombstone`, `remove`, `remove_digest`, `relabel_provenance` and `migrate_rekey_doc_id`, in the
  transaction of the row each writes, so that a `deferred()` batch (`catalog.py:125-138`) carries
  its log rows; a `genesis` at first open; the reads `read_at(class, path, c)`,
  `heads_at(class, c)`, `read_between(class, a, b)`, `head(class)` and `verify(class)`. Nothing
  reads them yet, and no reader's behaviour changes. Tests: SNP-1 to SNP-5 as §10 states them,
  over random sequences of catalog writes; the catalog equals the fold of the log after every
  write; a store the UNCHANGED check skips writes no row; a transaction killed between the two
  rows leaves neither; the genesis equals the catalog; `verify` fails on an edited row. The laws
  SNP-1 to SNP-5 enter the ledger here. Rollback: the table is additive and unread, so dropping
  it restores the file; a build that stops writing it and resumes later appends a `horizon`.
- **SN-2 cuts.** The chain tables for `chat` and `att`; the `cuts` table and the `cut`
  attestation; a record at a sensed commit, at a moved trough and on command; the four names; the
  resolver; a command that records, lists and verifies cuts. Tests: SNP-8 and SNP-9 as stated.
  Rollback: additive tables; the names fall back to today's.
- **SN-3 the erasure's reach and the seal.** A purge empties the log's rows, removes the lexical
  units, nulls the version rows' digests, removes the relation edges and artifacts that name the
  digest, compacts the vector table and writes its attestation; the seal by identity and the
  owner's `unseal`. It lands before SN-4, since SN-4 is the first stage that reads a superseded
  version. Tests: SNP-7 as stated, with the purge probe of §11 turned into a test that must find
  nothing. Rollback: a purge has none by its nature; the rest is additive.
- **SN-4 the notes at a cut.** The universe's nodes from `heads_at`; `read` from the raw object
  the log names; the vectors and the lexical units joined to the heads; the pending rule at a
  cut; `trace` at a cut; the cut read and its note (§7.1), which retires the note that says a verb
  read the present; the commit on a `read` hit. Tests: `as of "head"` against no `as of` over the
  query battery (`eval/query_battery.py`); a sentence at a recorded cut asked before and after
  unrelated landings; SNP-6 with two grants; the cut read under the cut asked. Rollback: one
  configuration switch under `[query]`, off being today's behaviour.
- **SN-5 the causal fiber at a cut.** The recomputation of §5.5 with its memo; edges named by
  session, order and endpoint; the transcript integrator's checkpoint a cut on `chat` and `repo`.
  Tests: the two job orders giving one result; the prefix that ends before a result; the stored
  rows at the head equal to the recomputation. Rollback: the stored rows stay the head's cache.
- **SN-6 model output by generation.** A sequence number and a history table for artifacts,
  relation edges and claim ops; `relate` at a cut; a kept row served only with its sources.
  Tests: SNP-5 on random sequences of writes and replacements; `mem_serve_iff`'s test. Rollback:
  additive columns and tables.
- **SN-7 retention.** The two windows a chain in the instance's configuration; the pass of
  §9.2; the `horizon` row; the horizon in the answers. Tests: SNP-10 as stated; a pass killed at
  each step leaving no served position incomplete; a derived row dropped under the first window
  reported pending and derived again. Rollback: none for dropped rows by their nature; nothing
  runs unless a window is declared.
- **SN-8 the delta.** `changed between` and `changed since` (§7.4); the integrator interface
  below. Tests: the region's union law, and equal reads at both cuts for an identity outside it.

**A generic integrator on the delta.** An integrator job is a registered, scoped job that reads
what changed and writes one batch of edges with their evidence. Its checkpoint is a cut `a`. A
run takes `b`, the greatest consistent cut under the head on the chains the job reads; reads
`read_between(a, b)` on them; writes its batch, every edge's sources inside `b`; and records `b`
as its checkpoint in the transaction of the batch. Three laws make that correct. The state the
job would compute from the whole prefix at `b` is its state at `a` continued over the delta
(`foldAt_readBetween`), so a run and a rebuild agree. The delta up to `b` is the same however
the stores grow while the job runs or after it (`readBetween_grow`), so a run repeated after a
crash reads what the interrupted one read, and anything more lies after `b`
(`readBetween_append`). And for a job that joins two chains, a pair read at `b` was read
at `a` or has a member in the delta (`pair_readAt`), so the job visits the old events of one
chain only against the new events of the other. The transcript integrator is the case at hand:
it joins `chat` and `repo`, a commit that reaches the ledger after its session was read is a
delta on `repo`, and the session's unresolved commit events are visited against it, which the
digest it keeps a session today does not do (§2.3, item 4). The integrators that
dn-decision-integrators designs, and the embed drain, are jobs of this shape; their designs stay
where they are. `[THEOREM: SNP-1, SNP-3; DERIVED for the job]`

## 13. Decisions for the owner

Each with the recommendation and what the alternative costs.

1. **D1, where the catalog's past is kept.** Recommended: the landing log in the catalog's file,
   written by the catalog (§3.2). The alternatives: version chains for every place, which is a
   second file, so the key and its history are two transactions and ING-7's order gains a stage,
   and whose chains are per document, so a cut is a pair a document; or the plane's supersession
   log, which an instance with no plane lacks, which records the drain's order under lazy
   embedding, and which gives a position again after a purge.
2. **D2, the grain of a cut.** Recommended: one position a chain, the landing chains one a
   provenance class (§3.1). The alternatives: a position a document, the spine's frontier today,
   which is millions of pairs a cut on a corpus instance; or one landing chain for every class,
   which saves a few integers a cut and tells a narrower reader, by its positions, how many
   landings the classes it cannot read made.
3. **D3, what a retire does to the past.** Recommended: the stricter seal, by identity, lifted
   only by the owner's `unseal` (§6.2). The alternative, the looser seal, brings a deleted note's
   versions back at earlier cuts when another note is written at its path, and lets a past answer
   grow; it needs no unseal when a vault is missing at a rescan, where the stricter one does.
4. **D4, a store that cannot serve the cut asked.** Recommended: read it at the greatest position
   at or under the cut that it serves, and name the cut read (§7.1). The alternatives: refuse the
   sentence, after which `as of` answers nothing that touches a store without a past until SN-6,
   and nothing under a horizon ever; or keep today's behaviour, which answers from after the cut
   and changes as the store grows.
5. **D5, the embedder's and the tokenizer's identity at a cut.** Recommended: the present's
   (§5.2, §5.3). The alternative, the identity in force when the content landed, needs every
   identity's vectors kept, a vector table an identity (1,536 bytes an atom at the present
   dimension and precision), in a plane that refuses a second identity today.
6. **D6, the names `as of` takes.** Recommended: `head`, a recorded cut's id, a commit, a date
   (§3.4). The alternatives: commits only, as today, which leaves no name for a moment between
   two commits and none on an instance with no repository; or dates without the cut read in the
   answer, which gives an answer that cannot be asked again.
7. **D7, between two cuts.** Recommended: the region `changed between` and `changed since`
   (§7.4). The alternatives: nothing, and every integrator and every question about change is a
   hand-written read; or a general two-cut adjective, which is a second universe a sentence and a
   pair sort, and which dn-graph-dynamics designs already as GD-4.
8. **D8, retention.** Recommended: no window on the default instance; where the disk is bounded,
   a window for derived rows, which moves no horizon, and a window for the history only when the
   owner declares one, since it drops raw objects (§9.2). The alternatives: a horizon everywhere,
   which loses the default instance's history to save megabytes a year; or the last `n` versions
   an identity, which leaves no horizon to name.
9. **D9, the attestation ledger under a purge.** It still names a purged digest (§6.1), against
   the plane's rule that no content hash of purged text is kept. Recommended: from SN-3 on a
   landing's attestation names the log row's commitment in place of the content digest, so a
   purge leaves nothing that can be tested; the rows written before stay, and a purge lists them
   as what it could not reach. It makes an attestation a landing, a kilobyte each at the recorded
   row size, where today there is one per action and digest, and it turns the landing's check
   for an earlier attestation into a read of the log, where today it scans the ledger
   (`core/ingest/landing.py:16-19`). The alternatives: rewrite the ledger at a purge, which
   breaks its construction as append-only and every id computed from a row; or leave it, and a
   digest of purged bytes stays.
10. **D10, model output.** Recommended: kept by generation (§5.4). The alternative, outside the
    snapshot, costs nothing and means `relate` and the dreams are never read at a past cut.
11. **D11, the read-only principal at a cut.** Recommended: the present's list, applied to the
    edges inside the cut (§6.4). The alternative, the list taken at the cut's tree, shows at a
    past cut a file that was tracked then and is not now, which the head withholds, and makes the
    grant a function of the cut.
12. **D12, what the merge licenses.** Recommended: SN-1 and SN-2, which add tables and change no
    reader. SN-3 to SN-8 change an erasure, the universe and what an instance keeps, and each is
    licensed with its own pull request. The alternative, all eight at once, saves the owner seven
    decisions and reviews the purge, the universe and retention together.

## Parked decisions

| id | decision | default recorded | re-entry condition |
|---|---|---|---|
| SN-a | the cadence of recorded cuts | a sensed commit, a moved trough, the owner's command | a date that resolves to a cut farther from it than a declared tolerance |
| SN-b | the citation readings as rows valid over a range of commits | one whole reading a commit, as built | the store's size on an instance |
| SN-c | the heads kept at some recorded cuts | none: every head is read from the log | reading every head at a cut past a tenth of a second on an instance |
| SN-d | a second embedder identity's vectors kept beside the first | none: the present's identity | dn-two-phase-ingestion's open question 4 |
| SN-e | lexical statistics stored per class and per recorded cut | computed from the mask | a lexical query at a past cut over its budget |
| SN-f | `repo` as a graph of commits | the line of the branch the sensor reads | an instance whose history has merges or that reads several repositories |
| SN-g | which recorded cuts are kept under a horizon | the records stay as attested claims; their chains' rows go | a consumer that must verify a cut under a horizon |
| SN-h | generations with a diff for the causal fiber | recomputation with a memo | SNF-5 |

## Falsifiers

- **SNF-1 (the log is not the catalog's past):** after some sequence of writes the fold of the
  log differs from the catalog, or a row of one is found without its row of the other. Then the
  log is not written in the key's transaction and SN-1 does not land.
- **SNF-2 (a position a document is needed):** a consumer that must name a cut holding one
  document of a class at an older version and another at a newer one in an order the class's
  chain did not have. Then chains are per document and decision D2 is reopened.
- **SNF-3 (a name resolves far from what was meant):** a date, or a commit, whose recorded cut
  lies farther from it than the tolerance SN-a declares. Then the cadence changes; the names do
  not.
- **SNF-4 (the cut read misleads):** readers take an answer at a lowered cut for the answer at
  the cut asked, seen as `as of` sentences in the query log asked again without `as of` after an
  answer with a lowered chain. Then such a sentence is refused (D4's first alternative).
- **SNF-5 (recomputing the causal fiber is too slow):** a sentence that walks `C` at a past cut
  over a second on a real instance, the memo warm. Then generations with a diff (SN-h).
- **SNF-6 (every head is too slow):** `heads_at` past a tenth of a second on an instance's log.
  Then the kept heads of SN-c.
- **SNF-7 (the mask is too slow for the lexical statistics):** a lexical query at a past cut over
  its budget at the instance's size. Then SN-e; the rule that the statistics are the mask's does
  not change.
- **SNF-8 (kept model output is never read):** no sentence under `as of` reads an archived
  artifact or relation in a declared period. Then the archive stops and D10 takes its
  alternative.
- **SNF-9 (retention drops what is asked for):** cuts asked for under a declared horizon, or a
  pass ordered by the field that drops rows later asked for more often than a pass ordered by
  age. Then the window grows, or the order is age.
- **SNF-10 (the stricter seal is the wrong default):** unseals become routine, as an instance
  whose vault goes missing at rescans would show. Then D3 takes the looser seal, with its cost.
- **SNF-11 (a transcription lies):** a built stage whose property test against a Lean statement
  fails. A transcription defect; the stage does not land until it agrees.
- **SNF-12 (an erasure leaks):** after a purge, a read at any cut or a scan of the instance's
  files finds the purged words. Then SN-3's reach is incomplete and no stage after it is on.
- **SNF-13 (append invariance fails on the code):** a sentence at a recorded cut that answers
  differently after unrelated landings, the erasure and the grant unchanged; or `as of "head"`
  that differs from no `as of`. Then some reader is not a function of the prefixes, and SNP-5
  says which kind of store to look for.
- **SNF-14 (the region is not what is asked):** questions about change that need the two
  readings and cannot be put with the region. Then GD-4's form is built sooner, on the two
  readings this note supplies.

## Open questions

- May a narrower grant name a date? The answer names a cut on its own chains only, but the
  cadence of recorded cuts is itself a fact about when the stores were written.
- The chat log and the attestation ledger have no erasure today except a reset. Their chain
  tables digest commitments so that one can leave a hole; who may erase a turn is not decided
  here.
- Should the genesis of a class the plane holds be seeded from the plane's supersession log? It
  would recover an order per path before the log existed, without positions across paths, and
  not on an instance with no plane.
- A purge does not reach a backup or a migration's archive. Whether a recorded cut is taken
  before a purge, so that the purge's own moment is certified, belongs with that design.
- On an instance that reads several repositories, is `repo` one chain a repository?

## Cross-references

**Formal (this branch):** `formal/Palace/Snapshot/Defs.lean` (`Store`, `Cut`, `head`, `grow`,
`Extends`, `readAt`, `readBetween`, `view`, `present`, `AppendInvariant`, `PrefixOnly`, `foldAt`,
`stateOf`, `stateAt`, `lastWrite`, `Gen`, `closeAt`, `landGen`, `gens`, `selects`, `genRead`,
`prune`, `sealedAt`, `servedAt`, `servedNow`, `restrict`, `snapshot`, `redact`, `visible`,
`compact`, `serve`, `committed`, `purge`, `commitments`, `contents`, `Consistent`, `generator`,
`reached`, `Resolves`, `reachedIn`, `ResolvesIn`, `chainDigest`, `CollisionFree`, `Certificate`,
`certify`, `Verifies`); `formal/Palace/Snapshot.lean` (the declarations §10 names, by law, and
the `Witness` controls); `formal/PalaceTest/Snapshot.lean` (seeds 430 to 486); the families
cited: `Palace/Clock.lean` (CLK-2: `IsCut`, `frontierCut`, `isCut_iff_not_crossed`,
`IsCut.inter`, `IsCut.union`), `Palace/Ingress.lean` (ING-7), `Palace/Script.lean` (ING-17),
`Palace/Derived.lean` (ING-19 to ING-21), `Palace/Plane.lean` (PLN-4), `Palace/Utility.lean`
(UTL-2, UTL-4), `Palace/Sentence.lean` (QSA-1 to QSA-4, QSA-10).

**Code (read at `e3e3ee47`, unchanged):** `core/sentence/grammar.py`, `ast.py`, `universe.py`,
`execute.py` (`as of`, the universe, `read`); `core/query.py` (the modes, `note_graph`);
`core/temporal/spine.py` (`CertifiedCut`, `cut_at`); `core/stores/catalog.py`, `versions.py`,
`chatlog.py`, `chat_events.py`, `causal_edges.py`, `reference_edges.py`, `plane.py`,
`vectorstore.py`, `lexical.py`, `memberships.py`, `derived.py`, `edges.py`, `claim_ops.py`,
`authored_supersession.py`, `staging.py`, `observation_history.py`, `code_observations.py`,
`runledger.py`, `verdicts.py`; `core/kernel/stores/rawstore.py`; `core/attestation/store.py`,
`record.py`, `attestor.py`; `core/ingest/writer.py`, `landing.py`, `table.py`, `purge.py`,
`derive.py`, `sync.py`; `core/chat_events.py`, `core/integrator.py`; `ops/code_sensor.py`,
`ops/code_snapshot.py`, `ops/chat_sensor.py`, `ops/lifecycle/launcher.py`;
`eval/predictions/ledger.py`.

**Design:** global-event-clock §2.2 to §2.4 (the generators, Law C4, the certified frontier);
limits-of-the-algebra L7; dn-query-sentence-algebra §2.3, §2.7, §2.9; dn-ingress D1, D3, D5
(ING-7, the one writer); dn-ingress-language (ING-13 to ING-17); dn-two-phase-ingestion D1, D2
(ING-19 to ING-21); vector-membership-store A3.5, A3.7 (noninterference, the purge);
dn-utility-field §3.1, §4 (UTL-2, UTL-4) and its first open question; dn-graph-dynamics §6, §7.1
(GD-4, the state at a cut); dn-decision-integrators (the integrators' layer);
dn-mathematical-foundations §2.4 (design theorems and the ledger);
`papers/2026-11-10-temporal-snapshot/paper.tex`.
