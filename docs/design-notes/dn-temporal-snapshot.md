---
type: design-note
id: dn-temporal-snapshot
track: query-language
status: draft                  # provenance description, never a gate; the merge is ratification
implementation: partial        # SN-1 built (the landing log, core/stores/landings.py; SNP-1 to SNP-5 in docs/LAWS.md); SN-2 to SN-8 design
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
  - core/stores/landings.py                                # SN-1 as built: the landing log, in the catalog's file
  - docs/experiments/landing-log-2026-11-11.md             # SN-1 measured on a copy of the corpus instance's catalog
  - papers/2026-11-11-landing-log/paper.tex                # the article of SN-1
supersedes: null
superseded_by: null
warrant: null
---

# The temporal snapshot: the palace as of a cut

> Composed on the snapshot session (Fable 5.2, 2026-11-10 and 2026-11-11), on the standing
> direction that the design and its proofs come first and the build follows a licence given at
> the merge. Agent-drafted, filed `draft` on a branch; the merge is ratification. When the design
> was merged nothing was built: `core/` was untouched and no store of any instance was read.
> Every nontrivial claim carries a grade: `[THEOREM]` is machine-checked in
> `formal/Palace/Snapshot.lean` and names its declaration; `[ESTABLISHED]` is a ratified note's, a
> fact of the code read at the line cited, or a figure of the repository's own experiment records,
> cited by file and line; `[DERIVED]` is argued here from those; `[MEASURED]` is a figure taken
> for this note, for the design on a synthetic fixture by a probe that is not in the repository
> (§11 says how, and which stage commits its harness), and from SN-1 on by a stage's committed
> harness, on a copy of an instance's store where its record says so; `[INFERENCE]` is a design
> call with a named falsifier; `[HYPOTHESIS]` is a claim nothing here checks, with what would
> check it named. Code claims were read on `origin/main` at `e3e3ee47`. The article
> `papers/2026-11-10-temporal-snapshot/paper.tex` states the same theorems with proof sketches
> and the references.
>
> Two things were added on 2026-11-11, after the design was merged, and each is marked where it
> stands. The owner decided what a retire does to the past (D3, §6.2), against the
> recommendation this note had made, and the note now carries the decision wherever the design
> rested on the seal. And six findings the review of the design left open are closed (§3.1,
> §3.5, §5.1, §5.4). The code cited for both was read at `f969904e`.
>
> Stage SN-1, the landing log, was built the same day (§12), with its tests, its ledger rows
> (SNP-1 to SNP-5, `docs/LAWS.md` family XVI) and its measurements on a copy of the corpus
> instance's catalog (§11, `docs/experiments/landing-log-2026-11-11.md`). Where the build
> departed from §3.2 the section says so where it stands: the key of a path takes half of its
> key from the instance's secret, outside the file; a path that changes class leaves its chain
> by a sixth kind, `leave`; and the genesis writes a renamed path's tombstone as a `move`. The
> review of the build added three things, each marked where it stands: a purge by digest empties
> the tombstones of a path none of whose versions keeps its content (§6.1); the first open writes
> the genesis for a reader too, which is open for the owner (§12, SN-1); and every head costs
> what building the answer costs, which meets SNF-6 (§4.2, §11).

## 1. Purpose and scope

### 1.1 The requirement

A sentence of the query language can carry `as of "<cut>"`. Today it moves one relation: the
citation graph, which the stores index by commit, is read at the cut, and a file of the repository
is read as git's blob there when git holds the commit. Every other verb reads the stores as they
are now, and the answer says so. The requirement is the rest: the palace as of a cut. A read at a cut must be the same
whenever it is asked, since the store only grows above the cut; it must never return what was
erased since; it must respect the grant the asker holds today; and where it cannot read a store at
the cut it must say so instead of answering from the present.

The same object serves three needs the record already names: a generic integrator, whose
checkpoint is a cut and whose input is the delta between two cuts; the velocity of an identity
over a window of cuts (dn-graph-dynamics GD-4, which waits on the snapshot); and the utility field
as of a cut (dn-utility-field, open question 1).

### 1.2 Decisions

1. **A cut is one position per chain, about a dozen positions for an instance, not one per
   document (§3.1, §3.3).** The chains are the stores' own append orders. A chain has an id that
   never changes and carries a provenance class as a label, so clearances that separate rows
   separate chains. `[DERIVED from global-event-clock §2.4; INFERENCE, falsifier SNF-2]`
2. **The missing ledger is a landing log (§3.2).** The catalog is rewritten in place, and no
   ledger records which digest a path held when, except the version chains of one place. One
   append-only, hash-chained log, written by the catalog's own methods in the transaction of the
   row they write, makes the catalog its fold and gives every landed stratum a past.
   `[ESTABLISHED for the gap; INFERENCE for the log, falsifier SNF-1]`
3. **A name resolves to a frontier, and the read is at the greatest consistent cut under it
   (§3.4, §3.5).** Every frontier resolves to exactly one such cut. That consistent cuts are
   closed under meet and join is CLK-2's, already in the ledger. Wall time selects a frontier by
   lookup in the bookmarks and orders nothing. `[THEOREM: SNP-8, CLK-2]`
4. **A cut is certified by the digest of each hashed chain's prefix, recorded on a chain of records
   that no other chain reads (§3.3, §3.6).** A certificate verifies on every later state of the
   store and, under a collision-free digest, pins the prefix it digests. For the landing log that
   prefix is the commitments, so under a binding commitment it pins the events. It attests no
   erasure and no grant: those are the present's, and an answer at a certified cut is the same
   on two stores for one erasure and one grant. `[THEOREM: SNP-9]`
5. **Derived data is a function of the prefixes, held store by store in the cheapest of the
   equal ways (§5):** version-keyed rows selected by the log for vectors and lexical units,
   recomputation for the causal fiber and for the relations a note declares, kept generations
   for model output. `[THEOREM: SNP-5; INFERENCE per store]`
6. **The grant and the erasure are the present's (§6), and removal has two forms.** A narrower
   grant's snapshot is the restriction of a wider one's; nothing erased is visible at any cut,
   and a read by path returns a hole where the version at the cut is erased. A purge is the deep
   removal: a hole at every cut. A retire is the shallow one: the item leaves the present, its
   history stays readable at the cuts where it existed, no seal is applied, and a note written
   later at its path takes a fresh identity. `[THEOREM: SNP-6, SNP-7; the owner's decision of
   2026-11-11 for the retire, D3]`
7. **A read under `as of` holds no event from after the cut it names (§7).** Where a store cannot
   serve the cut asked, the cut read is the greatest consistent cut among the positions the stores
   serve, and the answer names it chain by chain. A chain that no other chain reads is lowered
   alone; a chain that others read takes its readers down with it, which is why a recorded cut is
   kept off the chains that content reads, and why a row that reads a landing without being a
   landing's own record, as a pass attestation, a row of model output and an authored supersession
   do, is withheld by a filter of the read and lowers no position (§3.5). `[THEOREM: SNP-8, SNP-10;
   INFERENCE for the surface, falsifier SNF-4]`
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
(dn-two-phase-ingestion, open question 4); backups and migration archives, which a purge does
not reach today and which this note does not design.

Not in a snapshot, each for its reason. The job queue, the task list and the telemetry are
operational state and not content. So are the launcher's run ledger (`ops/lifecycle/runs.py:27`,
whose rows are updated at a stop, `:117`), the self-modification proposal ledger
(`ops/ledger.py:294`) and the effect ledger (`ops/effect_ledger.py:294`): they record the
system's own runs and acts, and no sentence reads them. The eval results
(`eval/harness/store.py:164`) are measurements of the system; the spine cuts them as a stratum
of its own (`core/temporal/spine.py:279`, `:346`) and no sentence reads them either. The spools
and state files hold what is in flight: the ingress spools with their receipts
(`core/ingest/ingress.py:1-27`), the dialogue handoff documents and their `.synced` marks
(`core/ingest/table.py:276`, `ops/heartbeat.py:298`), the two sensing handoffs
(`ops/code_sensor.py:862`, `ops/self_sensor.py:345`), a stream source's cursor
(`core/ingest/stream.py:30`) and the heartbeat's tick files (`ops/heartbeat.py:76`). A recorded
cut does not certify that these are empty. Its handoff certificate, as the spine sources it, is
that the `requests/` and `observations/` directories of the one sensing handoff it is given
hold nothing (`core/temporal/spine.py:218`, `:283-286`, `:1090-1103`), and its trough
certificate that no job is queued or running (§3.3). The code and agent sensing handoffs are
other directories, and the ingress spools and the dialogue handoff are not looked at. A cut
does not need them to be empty: what a spool or a handoff holds has not landed, so it is an
event of no chain, no sentence reads it, and when it lands it lands at a position after the
cut. One of them keeps text, the rejected requests, and §6.1 names it for the purge.

### 1.4 What is proved, what is measured, what is open

Proved, in `formal/Palace/Snapshot.lean` over `formal/Palace/Snapshot/Defs.lean`: SNP-1 to SNP-10
as §10 states them, 193 theorems, twenty of them the controls; attacked in
`formal/PalaceTest/Snapshot.lean` (seeds 430 to 528: fifty-four attacks, every one surviving
all 500 instances, and forty-five negative controls, each refuted). SNP-1 to SNP-5 entered the
ledger with SN-1, the landing log: they are family XVI of `docs/LAWS.md`, and the 47 declarations
§10 lists for them are restated in `formal/Spec/Snapshot.lean` and judged by the comparator. SNP-6
to SNP-10 are design theorems: no code relies on them yet, so they have no row and no statement;
§12 says when each enters. Some of what §6 and §7 require holds by the construction of
the model and not by a theorem about the code: §10 says which, law by law.

Measured, on synthetic fixtures (§11): the landing log's size and the cost of its reads; what
a kept version costs in the lexical index; what a purge leaves behind today; that the causal store
depends on the order of two jobs; that the events of a transcript's prefix are not always the
prefix of its events, and what re-deriving a session costs; what `as of` accepts and when; that a
position taken from a store's row numbering is given again after a delete. And, at SN-1, the log as
built, on a copy of the corpus instance's catalog: its migration, its bytes, its writes and its
reads (§11, as built).

Open, stated where it bites: the attestation ledger's own content hashes under an erasure
(decision D9); the cadence of recorded cuts (§3.3); a repository history that is not one line
(§3.1); rows written to the curated store outside the catalog (§5.6).

## 2. What exists

### 2.1 `as of` today

`as of "<cut>"` is an adjective of the grammar (`core/sentence/grammar.py:253-256`,
`core/sentence/ast.py:205-210`): the index of the reading, never a letter of a chain
(dn-query-sentence-algebra §2.3). `[ESTABLISHED]`

- **One cut a sentence.** The universe's builder keeps the cut of the `as of` it meets
  (`core/sentence/universe.py:125-127`), and the executor refuses a clause whose cut is not the
  universe's (`core/sentence/execute.py:713-718`). `[ESTABLISHED]`
- **The names it accepts.** A commit's sha, whole, or a prefix the reference store resolves to
  one commit (`universe.py:466-477`, `core/stores/reference_edges.py:381-388`). When the store
  holds some reading, a name it has no reading for falls back to the newest reading
  (`universe.py:478-484`, taken only when `latest_commit()` is not `None`) and the clause is then
  refused; so are `HEAD` and a date. When the store holds no reading at all, as on an instance
  with no repository or one just reset, the string asked becomes the universe's cut as it is, the
  executor's prefix check passes (`execute.py:714`), and `as of "HEAD"`, a date and any other
  string are answered: a walk over `F` over an empty graph with no note, another verb with the
  note that it read the present. `[ESTABLISHED; MEASURED §11]`
- **What is read at the cut.** The citation graph (`universe.py:485-486`), and a file of the
  repository, as git's blob in the tree at the commit (`execute.py:249-302`, called with the
  universe's cut at `universe.py:787-788`), when git resolves the cut. When it does not, a
  reading whose commit the checkout lacks, the read tries the cut and then `HEAD`
  (`execute.py:266-270`) and returns `HEAD`'s blob. `[ESTABLISHED; MEASURED §11]`
- **What is read as it is now.** Everything else, and the answer carries a note naming the verbs
  (`execute.py:503-521`, `:719-725`). The note lists `read` among them, though a `read` of a
  repository path is at the cut where git holds it: on a file that changed since the cut the text
  returned is the cut's blob and the note says the present. `[MEASURED §11]` The record of such a
  read carries the commit it was read at, and the hit built from the record drops it
  (`execute.py:296-299`, `:1121-1126`), so the answer does not show which commit the text is
  from, the cut's or, after the fallback, `HEAD`'s. A note's `read` opens
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

Every store an instance writes that holds content a sentence can read, by what a past state of
it is. The clock is the order that positions its rows; wall-time columns are bookmarks and
position nothing (event clock, Law C4). The operational stores, the eval results, the spools and
the state files are left out, each with its reason (§1.3).

**Ledgers: a past state is a prefix.**

| store | clock | what names a position | what a rewrite loses today |
|---|---|---|---|
| raw objects (`core/kernel/stores/rawstore.py:28-40`) | none of its own; an object is ordered by the events that name its digest | the digest | nothing is rewritten; a purge deletes the object (`rawstore.py:51-61`); a transcript that grew is retained whole again under a new digest (`ops/chat_sensor.py:289-333`) |
| version chains (`core/stores/versions.py:77-86`) | `version_seq` per document | `(doc_id, version_seq)` | nothing (one admitted relabel of `doc_id`, `versions.py:132`); kept by one place only, `mirror_authored` (`core/ingest/table.py:241-251`) |
| attestations (`core/attestation/store.py:27-36`) | insertion order and the parents' graph; read back `ORDER BY timestamp, id` (`store.py:130`) | the content-addressed id | nothing; one per (action, digest), and one more for a landing that appended a version (`core/ingest/landing.py:77-86`), so not one a landing outside the place that keeps chains, and no path |
| chat utterances (`core/stores/chatlog.py:77-92`) | `turn_index` per session | `(session_id, turn_index)` | nothing: the first write of a turn stands (`chatlog.py:161`); the store is wiped by a reset and filled again from the raw store (`chatlog.py:41-45`) |
| citation readings (`core/stores/reference_edges.py:134-148`) | the commit of the reading; git orders the commits | `commit_sha`, part of every edge's identity (`reference_edges.py:164-174`) | no row: the store is append-only (`reference_edges.py:289-302`). What is lost is which projection wrote an edge: a deliberate re-projection under a later extractor (`ops/code_sensor.py:827-845`, through `_project`, `:473-490`) adds edges under the old `commit_sha`, the rows carry no extractor version, and one is owed (`code_sensor.py:83-91`). So a commit's reading is the union of every projection of it so far, not a function of its tree |
| commit ledger (`ops/code_snapshot.py:44-58`) | git's ancestry: the ledger keeps no parent, and the sensor reads the commits of one branch in `rev-list` order (`ops/code_sensor.py:404-418`) | `commit_sha` | nothing |
| code and agent observations, current readings (`core/stores/code_observations.py:246`, `core/stores/agent_observations.py:205`) with their history (`core/stores/observation_history.py:46-56`) | the interpreter's generation per identity | (store, identity, interpreter) | nothing: a superseding write archives the old generation first, and it is never dropped (`code_observations.py:211-254`); a reset wipes the current readings and keeps the history (`ops/lifecycle/launcher.py:1765`, `:1776`, `:111-118`). This is generations as built, the form §5.4 takes |
| run ledger, verdicts (`core/stores/runledger.py:140`, `:161`; `core/stores/verdicts.py:145`) | insertion order | the row's id | nothing; a dream claim keeps the digests it rests on and its surface text (`runledger.py:90-97`) |
| structural snapshots (`core/complex/temporal.py:41-58`, `:208`) | a sequence of its own, one row a dream pass (`core/dreaming/dreamer.py:288`) | `snapshot_id` | nothing: invariants of the graph as it stood at the pass, appended |
| claim ops (`core/stores/claim_ops.py:40-48`) | none: `at` is wall time | a hash of (kind, claim, related, text) (`core/kernel/recursion_ops.py:134-135`) | nothing but the bookmark: a row is keyed by its whole content, so the `INSERT OR REPLACE` of a second application (`claim_ops.py:73`) only stamps `at` again. An append-only set with no position. The store calls no model (`claim_ops.py:14-15`), and its rows are by design a model's proposals: extracting the operations from a dialogue is a model task behind an injected analyzer whose default proposes none (`core/kernel/recursion_ops.py:44-46`), and at `e3e3ee47` no caller outside the tests applies an operation. A supersede names the conclusion artifact the same call writes (`claim_ops.py:45`, `:161-163`) |
| verdict dispositions (`core/verdict/dispositions.py:59-64`) | the verdict's sequence number | `verdict_seq` | nothing but the bookmark: append-only, one row a verdict, the latest winning by subject (`dispositions.py:4-6`); a second application of one verdict replaces the row with the same subject and effect and stamps `at` again (`dispositions.py:82-87`) |
| authored supersessions (`core/stores/authored_supersession.py:112-120`) | none: `at` is wall time | the pair (superseded, superseding) | the bookmark and the note of an earlier declaration of the same pair (`authored_supersession.py:159-161`); owner-declared, never model output (`:150-157`). An append-only set with no position |
| staging (`core/stores/staging.py:118-138`) | its own generation clock | the generation | a sweep stamps `tombstoned_at_gen` and the row stays; `read_at(g)` exists (`staging.py:232-244`) |
| query log (`core/sentence/surface.py:93`) | line order | the line | nothing |

**Version-keyed derived stores: every version's rows are kept and a flag marks the head.**

| store | clock | what names a position | what a rewrite loses today |
|---|---|---|---|
| plane occupancies (`core/stores/plane.py:268-278`) | none: `landed_at` is wall time | (path, digest, chunk) | which version was the head when: only `current` flips, and flips back when a path returns to bytes it held before (`plane.py:466-487`) |
| the plane's supersession log (`plane.py:282-289`) | `seq` per path | (path, seq) | a purge deletes entries and the next entry takes the position again (`plane.py:491-495`, `:552-553`) `[MEASURED §11]`; a reset drops it (`plane.py:628-640`); an instance with no plane has none; under lazy embedding it is written by the drain, in the drain's order, and only for the versions still current then (`core/ingest/derive.py:85-118`) |
| atoms (the vector table) | none: content-addressed (`plane.py:113-115`) | the atom's id | the `held` and `current` cache columns; the table's own dataset versions, one a write, which a compaction drops (`core/stores/vectorstore.py:780-812`) |
| the curated store: a second vector table with a plane of its own (`core/stores/curated_store.py:30-38`, `core/stores/vectorstore.py:243`) | as the plane and the atoms | as the plane and the atoms | as the plane and the atoms. It has two writers. `ingest_curated` lands through the catalog (`core/ingest/curated.py:66-82`). `scripts/curate_local.py:96-108` writes rows with `store.add` and no catalog row, raw object or attestation, so nothing positions them. `near` seeds from it (`core/sentence/universe.py:378-393`) and `read` opens its rows (`core/sentence/execute.py:318-326`); the purge does not open it (`scripts/purge_raw.py:51-56`) |
| lexical units and postings (`core/stores/lexical.py:56-82`) | none: `landed_at` is wall time | (path, digest, chunk) | the head flag (`lexical.py:251-256`, `:260-265`); every unit, when the tokenizer changes (`lexical.py:180-194`) |
| code memberships (`core/stores/memberships.py:140-155`) | git: (path, blob) | the version's identity | the head flag; a purge leaves a recorded hole (`memberships.py:153`, `:491-497`) |

**Stores rewritten in place: no past.**

| store | clock | what names a position | what a rewrite loses today |
|---|---|---|---|
| catalog (`core/stores/catalog.py:36-45`) | none: `updated_at` is wall time | the path | which digest a path held before and whether it was active: an upsert (`catalog.py:113-121`), a tombstone that flips `active` (`catalog.py:167-170`), a purge that deletes the row (`catalog.py:254-258`) |
| chat events (`core/stores/chat_events.py:40-48`) | `ord` per session, on each row | (session, ord) | the session's rows are deleted and written again (`chat_events.py:72-88`); re-derivable from the retained transcript |
| causal edges (`core/stores/causal_edges.py:51-61`) | `event_order` and `witness_turn`, on each row | the edge's id, a hash that includes the transcript's digest (`causal_edges.py:71-76`) | the session's rows are deleted and written again (`causal_edges.py:130-154`), under new ids when the session grew; what they were before the commit ledger gained a commit |
| interpreted artifacts and hyperedges (`core/stores/derived.py:49-60`) | none: `created_at` is wall time | a hash of the kind, the subkind and the sorted subjects, which are note titles (`derived.py:55`, `:97-100`) | the artifact a later pass over the same titles replaced (`derived.py:209-216`), whatever versions of those notes each pass read: model output, not recomputable. What a row was built from is its `derived_from`, note digests or other artifacts' ids (`derived.py:186-189`); it records no run, only the attestation that produced it (`derived.py:59`) |
| relation edges (`core/stores/edges.py:37-46`) | none: `created_at` is wall time | hash of (u, v, relation), the two ends content digests | the weight, sign and provenance a re-assertion replaced (`edges.py:88-106`). Two producers, kept apart by provenance (`core/relations.py:7-16`): authored edges read off a note's own `supports::`, `contradicts::` and `contextualizes::` properties (`relations.py:140-158`), a function of the note's text and so recomputable; and interpreted edges from a model (`relations.py:192-210`) or a `link` request (`core/ingest/writer.py:521-535`), which never replace an authored one (`writer.py:526-530`) |

### 2.3 What the two-class picture misses

The picture this note started from has two classes: ledgers that only append, where a past state
is a prefix, and derived stores rewritten in place, which keep no past and are recomputed from the
ledgers. Read against the code it needs eight corrections. `[ESTABLISHED, each at the lines cited
in §2.2 unless given]`

1. **The catalog is neither, and it is the gap.** It is the head of every landed item and the
   idempotence key (ING-7), rewritten in place, and outside one place no ledger holds its past.
   The version chains exist for `mirror_authored` only; for the dialogue, observed and curated
   places the sequence of digests a path held is recorded nowhere. It has six writing methods:
   `record` (`catalog.py:100-123`), `tombstone` (`:160-172`), `relabel_provenance` (`:195-208`),
   `migrate_rekey_doc_id` (`:210-241`), `remove` (`:243-246`) and `remove_digest` (`:254-259`).
   A seventh write is the migration's, which fills `doc_id` at open (`catalog.py:91`). The
   callers are seven modules of `core/ingest/` (`writer.py:419`, `:433`, `:518`; `sync.py:201`,
   `:238`; `founding.py:110`; `dialogue.py:75`; `curated.py:80`; `purge.py:61`;
   `mint_ids.py:252`) and one script, the only caller of `relabel_provenance`
   (`scripts/migrate_provenance_split.py:61`); `remove` has no caller. No statement outside
   `catalog.py` writes the table. So a record of its past written inside the catalog misses
   nothing, and one written by a caller would.
2. **The attestations do not fill it.** An attestation names a digest and no path. In the
   dialogue, observed and curated places a landing attests once per (action, digest), so a path
   that returns to bytes it held before, or bytes that land at a second path, leave no new
   record. In `mirror_authored` both append a version and are attested again
   (`core/ingest/landing.py:77-86`, `core/ingest/writer.py:409-418`), which is the one place
   whose past is already kept. The ledger is read back in wall-time order.
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
   endpoint is the digest and the interpreted artifacts whose `derived_from` names it are not
   touched either, nor are the curated store, the dream claims, the staging rows and the claim
   ops (§6.1 lists each), and no deletion attestation is written, though the attestation store's
   header says one is (`core/attestation/store.py:3-6`; no call in `purge.py` or
   `scripts/purge_raw.py`). A snapshot that read those stores at a cut would return what the
   purge left, so §6.1 states what an erasure must reach before any of them is read at a cut.
7. **A reset takes the ledgers with the derived stores.** Its targets are the raw store, the
   vector store, the catalog, the attestations, the version chains, the chat log and the stores
   derived from them (`ops/lifecycle/launcher.py:1748-1800`); the commit ledger and the
   observation history are guarded (`launcher.py:111-118`). The raw store is the first target
   listed (`launcher.py:1753`), while the comment beside the chat log's entry says it is not one
   (`launcher.py:1779-1780`). The lexical index and the relation edges are not among the targets,
   so they outlast a reset with rows about items that are gone. Whatever the intent, no chain of
   an instance survives a reset with its positions, so a reset opens a new history (§8).
8. **A path written again after a delete continues the deleted note's history.** A re-record of
   an existing path keeps the stored identity, and a tombstoned row stays in the catalog
   (`catalog.py:103-121`, `:160-172`), so the version chain of the identity appends
   (`core/stores/versions.py:109-119`): a new note written at a deleted note's path has the
   deleted note's versions under it. The same holds after a rename. The old path's row is
   tombstoned with the identity that moved, the writer asks for an identity only where the path
   has no row (`core/ingest/writer.py:372`, `:409`), and so a new note written at the old path
   takes the identity that now lives at the new one: two active paths under one identity, which
   the writer's rule R6 otherwise refuses. `[MEASURED §11 on the catalog]` §6.2 gives a note
   written at a path with a past an identity of its own.

## 3. The cut

### 3.1 Chains and positions

A chain is an append order a store already records, or one this note adds; a position is a
prefix length of it. `[DERIVED from global-event-clock §2.2, generator g1]`

| chain | store | position | today |
|---|---|---|---|
| `land`, one or more a provenance class | the landing log (§3.2), in the catalog's file | `seq`, from 1, given once while the log's tables stand (§12, SN-1's rollback) | not built |
| `chat` | the chat log | a sequence number beside each row; within a session it is the turn order | the order is recorded, the number is not |
| `att` | the attestation ledger | a sequence number beside each row | the order is recorded, the number is not; the ledger is read in wall-time order |
| `repo` | git, mirrored by the commit ledger and the per-commit readings | a commit, standing for its ancestors | recorded |
| `interp`, one a store | interpreted artifacts with their hyperedges, interpreted relation edges, claim ops: rows of the class `interpreted` only | a sequence number a write (§5.4) | not built |
| `decl` | authored supersessions | a sequence number a declaration | not built |
| `staging` | the staging store | its generation | recorded |
| `runs` | the run ledger, with the structural snapshot of a pass | a sequence number | recorded as insertion order |
| `verdicts` | the verdict ledger (`core/stores/verdicts.py:42-51`), which the dispositions are read by (§5.1) | its `seq`: signed with the verdict, strictly increasing, never given twice (`verdicts.py:135-139`) | recorded; a dropped verdict is a gap the store reports (`verdicts.py:171-181`), and a position is the rows at or under it |
| `use` | the utility field's use log (dn-utility-field §3.1) | the tick | not built |
| `cuts` | the recorded cuts (§3.3) | `seq` | not built; it reads every chain it certifies, and no other chain reads it |

Four choices are made here.

**The position is the store's, not the document's.** The spine's frontier has a pair per version
chain and a pair per chat session (`spine.py:414-427`, `:428-445`). The version chains exist for
one place, so on a corpus instance, whose items land in `observed`
(`ingress/sync_corpus.palace:5`, `core/ingest/table.py:241-251`), today's frontier has no pair
for them at all. Giving every place a per-document chain, which is decision D1's first
alternative, is what would make a frontier of one pair an item, ten million at the scale the
repository's records plan for (`docs/experiments/corpus-measurements-2026-11-07.md:94-96`). One
position a store with the per-path order inside it says the same thing (CLK-2: a frontier cut
needs only its cross-store edges checked). `[DERIVED]` The version chains stay as they are: the
log carries each landing's document and version number, so a document's chain is the log's
sub-chain, and the versions store remains the primary record of supersession.

**Where clearances separate rows the chain is per class.** A position counts every event before
it, so on a chain that mixes classes a reader of one class learns from its positions how many
landings the others made (`Witness.position_channel`), and a snapshot under a grant reads only the
chains the grant names and the cut on them (`snapshot_congr`). `[THEOREM: SNP-6]` So the `interp`
chains hold rows of the class `interpreted` only: the relations a note declares are of the
note's class and are recomputed from the note at the cut (§5.4), not numbered with the model's.

**A chain is keyed by an id, and its class is a label.** A certificate and a recorded cut name
chains, and a certificate of a cut does not verify on a store whose chains were renamed
(`Witness.rename_breaks_certificate`). The catalog's whole-class relabel
(`catalog.py:195-208`) changes the class of every row at once, and its one use merges a class
into another that already has rows (`scripts/migrate_provenance_split.py:58-61`). So a landing
chain has an integer id that is never reused or changed, and a row of a `landing_chains` table
gives the class it holds now. A relabel rewrites that label and no row of the log; after a merge
a class has two chains, and the read of a class is the union of its chains' reads. `[THEOREM
for the control; INFERENCE for the id]` As built at SN-1 the ids are given once while the log's
tables stand: the rollback drops them, and the genesis after it numbers its chains from 1 again
(§12, SN-1), which SN-3's fresh identity must not rest on (§6.2).

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

Two tables in the catalog's file, written by the catalog's own methods in the transaction that
writes the catalog's row, so the key and its log entry land together, no caller can write one
without the other, and ING-7's order is unchanged (the key last, now two rows of one
transaction). Stage SN-1 built them on 2026-11-11 (`core/stores/landings.py`), and three things
changed from the design as it was merged, each marked where it stands: where the key of a path
comes from, a sixth kind, and the tombstone the genesis writes.

```sql
CREATE TABLE landing_chains (
    chain     INTEGER PRIMARY KEY,  -- never changed, and given once while the tables stand (§12)
    class     TEXT    NOT NULL,     -- the provenance class it holds now; a relabel rewrites it
    secret    BLOB    NOT NULL,     -- 32 random bytes: the chain's half of the key of path_key
    key_check BLOB    NOT NULL      -- hmac-sha256(the chain's key, 'key check')
);
CREATE TABLE landings (
    chain       INTEGER NOT NULL,  -- landing_chains.chain
    seq         INTEGER NOT NULL,  -- the position, from 1, given once while the tables stand (§12)
    kind        TEXT    NOT NULL,  -- genesis | store | retire | move | leave | horizon
    path_key    BLOB,              -- hmac-sha256(the chain's key, source_path): kept by a hole
    source_path TEXT,              -- NULL once purged
    doc_id      TEXT,              -- the identity the event belongs to; NULL once purged
    version     INTEGER,           -- the version number, where the place keeps a chain
    digest      TEXT,              -- a store's digest; NULL for every other kind, and once purged
    title       TEXT,              -- NULL once purged
    att_head    INTEGER,           -- the head of att when the row was written; NULL before SN-2
    horizon     INTEGER,           -- a horizon row: the position it declares; NULL otherwise
    salt        BLOB,              -- 16 random bytes; NULL once purged
    commitment  BLOB    NOT NULL,  -- sha256(salt, the row's fields): what the chain digests
    hash        BLOB    NOT NULL,  -- sha256(the previous row's hash, commitment)
    closed_at   INTEGER,           -- the seq of the path's next event; NULL while it is the head
    at          TEXT,              -- wall bookmark: lookup only, never an order; NULL once purged
    PRIMARY KEY (chain, seq)
) WITHOUT ROWID;
CREATE INDEX landings_path   ON landings (chain, path_key, seq) WHERE path_key IS NOT NULL;
CREATE INDEX landings_doc    ON landings (chain, doc_id, seq)
    WHERE doc_id IS NOT NULL AND doc_id <> source_path;
CREATE INDEX landings_closed ON landings (chain, closed_at) WHERE closed_at IS NOT NULL;
```

**The kinds** are the catalog's writes. `store` is a landing (`record`). `retire` is the tombstone
of an identity no other active path holds. `move` is a tombstone that leaves the identity at another
path (the second half of a rename, which the writer tells from a delete by the catalog,
`writer.py:409-413`), and the owner-gated re-key of an identity (`catalog.py:210-241`), which writes
the path's `store` under the new identity after it, or its `retire` when the path is tombstoned.
`leave` is the row that closes a path in one chain when a `record` gives it another class, its
`store` then landing in a chain of the new class. The design had a `move` for this too; SN-1 made it
a kind of its own, because the two fold differently. The catalog keeps a renamed path's row,
tombstoned, so the old path's `move` folds to that row; a path that changed class has its row from
the chain it went to, so its `leave` folds to nothing; and a path that changed class and was then
renamed has an open `move` in two chains, which one kind cannot tell apart. `genesis` and `horizon`
are below and in §8. There is no kind that lifts a retire: a retire seals nothing (§6.2). A purge is
not a kind: it empties rows (§6.1). A `record` that changes nothing, the same path, digest, title,
class and identity as the path's open row, appends nothing: the log is of the changes of the map,
and the catalog's `updated_at` is a bookmark (the curated lane re-lands an unchanged digest after a
plane reset, `core/ingest/curated.py:66-82`).

**Which chain a landing goes to.** The chain that holds the path's last event; for a path with
no event, the newest chain of its class, opened if the class has none. So a relabel moves no row
and no position (§3.1), and after a merge both chains go on growing, each with the paths it
holds.

**The commitment and the hash.** `commitment` is SHA-256 over the salt followed by the canonical
JSON (keys sorted, no white space, UTF-8) of the object with the fields `chain`, `seq`, `kind`,
`source_path`, `doc_id`, `version`, `digest`, `title`, `att_head`, `horizon` and `at`.
`closed_at` is out, since it is written later, and so is `path_key`, which is an index key.
`hash` is SHA-256 over the previous row's `hash` followed by the commitment; the first row's
previous hash is 32 zero bytes. No row is ever deleted, by a purge or by a history window: both
empty rows and keep their commitments and hashes (§6.1, §9.2), so the chain is hashed from its
first row for as long as it lives. The chain is hashed like the prediction ledger
(`eval/predictions/ledger.py:1-12`), with one difference that §6.1 needs: a row's hash covers a
commitment to the row and not the row, so a purge can empty the row and keep the chain
(`commitments_purge`, `verifies_purge`). `[THEOREM: SNP-9]`

**The key of a hole.** `path_key` is a keyed hash of the path. It is what a read by path seeks on,
and it is the one name a purged row keeps, so a hole still shadows the path's earlier versions
(§6.1). Its key has two halves: the chain's 32 random bytes, in the file, and the instance's
landing-log secret, which is never in the file. The design had the chain's bytes alone; SN-1 takes
the secret as the repository takes every instance's secret, from the environment through
`get_secret`, Keychain-backed in the owner's setup and the instance's own item under a named
instance (`landing-log-key`, `<id>.landing-log-key`), so the key a hole keeps cannot be tested
against a guess of the path without the secret. Whatever appends a row or seeks a path's rows by
their key needs it: without it the genesis, a `record` or a `tombstone` that changes the map, the
re-key and `remove` refuse, loudly, and write nothing, and so do the two reads by path,
`state_at` and `history_at`. A relabel and a purge by digest need none, since they append no row
and find their rows by the label, the digest, the names they carry and the keys the emptied rows
keep; nor does a write that changes nothing, or a read of positions. A secret that is not the one
a chain was written with is refused by the chain's `key_check`. `version` and `att_head` are the
two fields a caller supplies:
`record` gains a `version` argument, passed by the writer's last step from the version it just
appended or found (`writer.py:408-419`, `:433`; `sync.py:201`) and left out where the place keeps no
chain; `att_head` is the attestation ledger's head read inside the key's transaction, after the
landing's own attestation, and stays `NULL` until SN-2 numbers that ledger, which reads as the end
of the ledger's genesis (§8).

**The genesis.** At the first open after the migration that fills `doc_id` (`catalog.py:77-92`),
each class the catalog holds gets a chain: a `genesis` row, then the catalog's rows of the class in
path order, an active path as one `store` and a tombstoned path as a `store` of the digest it held
followed by its tombstone, then a `horizon` row whose `horizon` is its own position. The tombstone
is the one `tombstone` would write: a `move` where another active path holds the identity, a
`retire` otherwise (the design said `retire` for every one, which would count a renamed path among
the identities that run across a retire, §6.2). The order inside the block is not history, so the
positions before the `horizon` are under it (§8). A class that first appears later opens its chain
at its first landing, with a `genesis` and a `horizon` and nothing between. As built, the genesis
is written by whichever process opens the catalog first, a reader's included, so that open needs
the secret and holds the write lock while it writes (§12, SN-1, where what this changes is
stated and left to the owner).

The catalog is then the fold of the log: each path's last event (`stateOf`) in the chain that holds
its present, the one where its last event is not a `leave`; an active row for a `store`; a
tombstoned row for a `retire` or a `move`, with the digest and title of the path's last `store` and
the identity the tombstone names; and no row when that `store` is a hole. (The design read a `move`
as no row, which the catalog contradicts: it keeps a renamed path's row, tombstoned.) The state at a
position is the same fold of the prefix (`stateAt`), read by one seek as the path's last event at or
under the position (`stateAt_eq_lastWrite`), or for every path at once through the closing stamp:
the rows with `seq ≤ c` and `closed_at` absent or above `c` (`genRead_gens`). The stamp is the one
field written after a row is appended, and it is a function of the rows, the position of the path's
next event (`gens_append_singleton`), so it can be rebuilt and it changes no read at a cut inside
the chain (`genRead_gens_append`). At most one row of a path is alive at a cut
(`length_filter_selects_le_one`), which is L7's falsifier turned into a theorem. `[THEOREM: SNP-5]`
The store's own precedent is the staging store: a generation clock, an admission stamp and a
tombstone stamp on each row, and `read_at(g)` as exactly this predicate
(`core/stores/staging.py:232-244`). `[ESTABLISHED]`

### 3.3 The cut and its record

A cut is a position for every chain of §3.1: for an instance, about a dozen integers.
`[DERIVED]` The read at a cut is the prefix of every chain (`readAt`), and everything else in this
note is a function of that. A cut is worth recording when it is consistent (§3.5) and certified
in the event clock's sense. GC-N3 names three certificates
(`docs/design-notes/global-event-clock.md:175-186`): the commit, which certifies the strata the
repository backs; trough quiescence, an empty queue with no queued and no running job
(`core/temporal/spine.py:197-206`), which certifies that no causality of the core is in flight;
and the empty handoff, which certifies that nothing is in flight between the edge and the core.
A cut across strata composes the three, and the spine refuses a cut whose certificate it cannot
source (`spine.py:275-281`, `:1064-1084`). As the spine sources it, the handoff certificate is
the emptiness of the two directories of the one sensing handoff it is given (`spine.py:218`,
`:283-286`, `:1090-1103`); §1.3 says what that leaves unlooked at, and why a cut does not need
it. `[ESTABLISHED]`

So a cut is recorded at a trough and at no other moment. Two things ask for one: the trough
itself, when the queue and the handoff are empty and the frontier moved since the last record;
and the owner's command, which is served at the next trough. With no daemon running that is at
once only when no job is queued. A landing through the writer enqueues jobs
(`core/ingest/writer.py:203`, `:555`), and the trough certificate needs none queued as well as
none running (`spine.py:197-206`), so with jobs queued and nothing running to take them the
spine refuses the cut: the command says so and records nothing until the queue is drained. The
sensor reading a commit does not record a cut: it reads inside its job
(`ops/code_sensor.py:404-418`), where the trough certificate is refused. A record names the
newest commit of the ledger as its `repo` position, so it covers every commit sensed since the
record before it, and §3.4 says what a commit's name resolves to.

A recorded cut is a row of a chain of its own:

```sql
CREATE TABLE cuts (
    seq         INTEGER PRIMARY KEY,  -- the position in the records' chain, from 1
    id          BLOB    NOT NULL UNIQUE,  -- sha256 of the canonical bytes: the cut's name
    prev        BLOB,                 -- the previous record's id; NULL for the first
    reason      TEXT    NOT NULL,     -- trough | command
    commit_sha  TEXT,                 -- the newest commit of the ledger; NULL with no repository
    frontier    TEXT    NOT NULL,     -- JSON: [[chain, position, digest or null, horizon], ...]
    certs       TEXT    NOT NULL,     -- JSON: the commit, trough and handoff evidence strings
    attestation BLOB,                 -- the attestation of action cut; NULL with no attestor
    at          TEXT    NOT NULL      -- wall bookmark: the key a date is looked up by
);
CREATE INDEX cuts_at     ON cuts (at);
CREATE INDEX cuts_commit ON cuts (commit_sha) WHERE commit_sha IS NOT NULL;
```

The id is the hash of the record's canonical bytes: the JSON, keys sorted and no white space, of
the previous id, the reason, the commit, the frontier in chain order (each chain's name or id,
its position, the digest of its prefix where the chain is hashed (§3.6) and its horizon (§8))
and the certificates as the spine sources them. The bookmark is not in the id. An attestation
has no field for a payload: it names an action, input and output hashes and its parents
(`core/attestation/record.py:51-62`). So the record's attestation, of action `cut`, names the id
as its output and the previous record's attestation as its parent, and it is built and signed
as any other is (`core/attestation/attestor.py:59-90`) but kept in the record's row and not
appended to the ledger that landings read. `[INFERENCE, falsifier SNF-3]`

That last point is forced. A record reads from the prefix of every chain it certifies, and every
landing reads from the attestation ledger. If records sat on that ledger, a chain that could
serve only a position below one a record certified would exclude the record, the ledger's
prefix would stop before it, and every landing attested later would go with it: one chain read
low can take a landing chain to its empty prefix (`Witness.record_drags`). On a chain of
their own, which no event of another chain reads, a record takes no chain down. Its own chain
does go down with a chain it certifies: the chain of records is read at its last record every
position of which the cut read holds, and nothing follows it (`resolvesIn_of_followed`,
`Witness.record_follows`; §7.1). `[THEOREM: SNP-10]`

Since each record is the head of every chain at some moment and chains only grow, the recorded
cuts are totally ordered. A record is about 2.7 kilobytes by arithmetic from its fields, not
measured: twelve chains at about 110 bytes each in the frontier, the certificates, and an
attestation at the 1,060 bytes a row of the attestation ledger takes in the repository's
records (`docs/experiments/corpus-measurements-2026-11-07.md:107`). A record at every trough
that moved is at most one a job. At the job rate those records show, 720 an hour
(`corpus-measurements-2026-11-07.md:94-95`), a record a job would be 47 megabytes a day; but
those were sync jobs of 0.07 s each, and a job that moves no chain asks for no record.
An instance with thirty troughs a day that moved writes 81 kilobytes a day. The cadence is
parked (SN-a).

### 3.4 Names

`as of` takes a string, and the string resolves to a frontier. The shapes do not overlap:

| name | resolves to | exact |
|---|---|---|
| `head` | the head cut; the answer is the answer without `as of` (`view_head`) | yes |
| `cut:` and a recorded cut's id, or a prefix that names one | that record's frontier | yes, and checkable against its certificate on the chains it digests |
| a commit's sha or an unambiguous prefix, as today | the frontier of the first record that holds the commit, with `repo` lowered to the commit, resolved as §3.5 says. For a commit sensed before the first record: the commit on `repo` and the empty prefix elsewhere | on `repo` for the tree; elsewhere a consistent cut between two records, which the answer names. It carries the commit certificate and not the trough's |
| a date or a date and time | the last recorded cut whose bookmark is at or before it. A date after the newest record is the newest record, never the head | to the cadence of the records; the answer names the record, and says when the head has moved since |

A commit's name needs the resolution because the sensor's attestation of a commit reads from the
commit (`code_sensor.py:413-418`): with `repo` lowered, the attestation of the next commit is
outside the cut, so `att` stops before it, and the landing chains stop at the last landing
attested before it. A chain that reads nothing, as `chat`, stands at the record. The cut read is
then no later than the record on any chain and holds nothing that read a later commit.
`[DERIVED]`

Wall time enters in the last row only, as a lookup key into bookmarks, and the cut it selects is
ordered by the chains (Law C4; the staging store's sweep resolves wall time to a generation the
same way, `staging.py:26-30`). A branch or a tag is not a name: it moves. A name that resolves
to nothing is refused whether or not the stores hold a reading, which is not so today (§2.1).
The grammar does not change; the names it accepts do, and the answer always carries the cut
read. `[INFERENCE, falsifier SNF-3]`

### 3.5 Consistency and resolution

An event of one chain may read from an event of another: `R k i k' j` says the `i`-th event of
chain `k` reads from the `j`-th of chain `k'` (the event clock's generators g2 and g3). The
references between the chains of §3.1 are these. `[ESTABLISHED: read off the writers]` The
list is what a reading of the writers found, and the review of this note found two it had
missed, the witness's attestation and the supersession, which are in it now; SNF-16 is the
falsifier for the next one.

- a landing reads from its attestation and, where the place keeps chains, its version row, by
  the order the writer lands them in (`core/ingest/writer.py:397-436`: the version, the
  attestation, the key last);
- the attestation of a sensed commit, and of a projection of it, reads from the commit
  (`ops/code_sensor.py:413-418`, `:498-499`);
- a citation edge reads from its commit and from the projection that wrote it;
- a recorded cut reads from the prefix of every chain it certifies and from the record before
  it, and no row of another chain reads a recorded cut;
- the attestation of a verdict on a commit reads from the commit, and the sensor did not write
  it. The CI witness appends to the ledger every landing reads an attestation whose input is a
  commit's sha (`ops/ci_witness.py:112-121`, through `build_attestor`,
  `core/attestation/attestor.py:94`); a deploy runs it for the head of main
  (`ops/lifecycle/launcher.py:757-761`), and the code sensor reads the commits of main inside a
  job of its own (`ops/code_sensor.py:404-418`), which may not have run yet;
- the attestation of a pass reads from the landings of the notes the pass read. The dreamer's
  and the curator's attestations sit on the ledger the landings' attestations sit on, name the
  notes' digests as their inputs (`core/dreaming/dreamer.py:144-148`, `:223-227`;
  `core/curator/curator.py:167-171`; `core/attestation/record.py:57`) and take as parents the
  attestations that produced those digests (`core/attestation/attestor.py:64-69`);
- a dream claim of the run ledger reads from the landings of the digests it rests on
  (`core/stores/runledger.py:90-97`);
- an interpreted artifact reads from the digests its `derived_from` names, through the artifacts
  it names there, and from the attestation its `attestation_id` names
  (`core/stores/derived.py:186-191`); an interpreted relation edge reads from the landings of its
  two endpoint digests;
- a claim op reads from the note or the artifact its `claim_id` names, and a supersede from the
  conclusion artifact the same call wrote, its `related_id` (`core/stores/claim_ops.py:45`,
  `:161-163`); a verdict's disposition reads from the verdict and from the claim or artifact it
  is about (`core/verdict/dispositions.py:59-64`);
- an authored supersession reads from the landings of the two notes it names. Both are
  authored content digests (`core/stores/authored_supersession.py:106-107`), resolved among
  the catalog's active paths when the owner declares it (`ops/supersede.py:42-50`) or taken
  from the two items a founding sequence has just landed (`core/ingest/founding.py:118-131`).

The first four are **resolved**: the resolver follows them, and the cut read is consistent for
them. Three of them join chains of §3.1. A citation edge is a row of no chain: it is read by its
stamps, which are positions on `repo` and `att` (§5.1), so a cut that holds its stamps holds its
sources. The last six are **filtered**: the resolver does not follow them, and a row that has one
is served at a cut only when its sources are. Both are taken up below, after the definition.

A causal edge reads from the turn that witnessed it and, when it ends at a commit, from the
commit (`causal_edges.py:58-60`, `integrator.py:134-137`); it is recomputed at a cut (§5.5), so
it is a filter of a read and no row of a chain.

A cut is **consistent** when every source of an event inside it is inside it (`Consistent`): no
fact whose sources lie after the cut, every cross-chain reference closed. `[THEOREM: SNP-8]`

- Consistent cuts are the event clock's cuts among the frontier cuts: a cut is consistent
  exactly when the events under its frontier are a down-set of the order the chains and the
  references generate (`consistent_iff_isCut`, on CLK-2's `IsCut` and `frontierCut`).
- So they are closed under the pointwise meet and join, with the empty cut at the bottom: this
  is CLK-2, which the ledger already states for frontiers (`docs/LAWS.md:114`,
  `Clock.IsCut.frontier_inf`, `Clock.IsCut.frontier_sup`), read through that equivalence
  (`Consistent.inf`, `Consistent.sup`, `consistent_zero`, `consistentCuts`). It is not a new law.
  `[THEOREM: CLK-2]`
- What SNP-8 adds is resolution. Every frontier has exactly one greatest consistent cut under
  it, and a later frontier has a later one (`exists_resolves`, `Resolves.unique`,
  `Resolves.mono`); a consistent frontier is its own (`resolves_self`). This is what a name's
  resolution is.
- Consistency is append invariant: the references a store gains by growing start at events at or
  past its old head, so a cut inside the old head that was consistent stays consistent
  (`Consistent.of_grown`).

So ING-7's invariant, that a key implies its rows, holds at every consistent cut and not only at
the head: a cut that holds a landing holds its attestation and its version. `[DERIVED]`

**Where the resolved references are recorded.** The resolver has to know, for an event, where its
sources lie. A landing records the head of `att` at its writing (`att_head`); the sensor's
attestation of a commit names the commit; a recorded cut carries its whole frontier. These three are
the bounds of the resolved references, and the resolver reads no other. With one writer a row's
sources were all written before it, so the head at its writing bounds them, the bound rises along
the chain, and it is sound: a cut consistent for the recorded bounds is consistent for the true
references they bound (`Consistent.of_bound`). It can only make fewer cuts consistent. The theorem's
hypothesis is a recorded bound at or above every true reference, so it speaks of the resolved
references and of no other. `[THEOREM: SNP-8; DERIVED from the one-writer rule, dn-ingress D3, for
the bound]`

**Rows that are filtered, not resolved.** The other references must not be given to the
resolver. A pass attestation sits on `att`, which every landing reads, and it reads landings.
Resolved, that reference would put `att` below the first pass that read a landing outside the
cut, and every landing chain attested after that pass would fall with it: a landing chain read
low behind a history window would take the other landing chains to the positions they had when
that pass ran, which is the cascade of a record kept on the ledger, through a pass
(`Witness.pass_drags`). A witness's attestation of a commit is the same case from the other
side: it sits on `att` and reads a commit the ledger may not hold yet, so resolved it would make
a record taken at a trough between a deploy and the sensor's job inconsistent, and the resolver
would put `att` under the witness's row and every landing chain attested after it with it. So
the closure of these references is kept row by row. A row is
**withheld** at a cut when it fails a test of its own, when a source of it lies outside the cut,
or when a source of it is withheld (`Withheld`); the read at a cut is the rows inside the cut
that are not withheld (`Kept`). `[THEOREM: SNP-8 for the control; INFERENCE for the choice,
falsifier SNF-16]` What a row's sources and its own test are, store by store:

- **A pass attestation:** an attestation whose inputs name the digests of notes it did not itself
  land, which today are the dreamer's and the curator's. Its chain-table row records, at its
  writing, the landing chains that held its inputs and the head of each. It is withheld when the cut
  read lies under one of those heads. The head stands for the landings the pass read, which lie at
  or under it, so the bound can only withhold more; it is a position and names no digest, so a purge
  or a history window, which empty rows and move no position, change nothing in what is withheld.
  The ledger is read by sequence number with those rows left out.
- **A witness's attestation of a commit:** an attestation whose input is a commit's sha and
  whose writer is not the sensor, which today is the CI witness's. Its chain-table row records
  the commit. It is withheld when the commit is not inside the cut on `repo`, which is one
  ancestry test, or one lookup of the commit ledger on a history that is a line (§3.1).
- **A row of the run ledger.** A run's chain-table row records the same pairs, and a dream
  claim is served when its run is.
- **An interpreted artifact and an interpreted relation edge.** §5.4: the attestation the row
  names is kept at the cut, and every digest its sources reach is a head at the cut and is not
  erased.
- **A claim op and a disposition.** The note or the artifact it names is served at the cut,
  and for a supersede the conclusion artifact as well. A disposition is read at the cut's
  position on `verdicts` (§3.1, §5.1).
- **An authored supersession.** Its chain-table row records, at the declaration, the position
  in the log of each of the two notes' open rows, a chain and a `seq` each, found through the
  catalog's index by digest (`core/stores/catalog.py:45`). It is served when the cut read holds
  both positions and neither row is a hole. The positions name no digest, so a history window
  changes nothing in what is withheld, and a purge of either note empties the supersession's
  own row (§6.1). A row the store holds when the columns are added is given the positions of
  the earliest `store` rows of its two digests that the log holds, and for a digest the log
  does not hold, the head of the newest chain of the note's class at the migration: a bound
  that can only withhold more.

What is proved of the filtered read, for any reads-from relation and any test. `[THEOREM:
SNP-8, with SNP-1 and SNP-2 for the last item]`

- It is closed: every source of a kept row is kept, so it lies inside the cut (`Kept.source`,
  `Kept.passes`). The read holds no fact whose sources lie after the cut, for every reference
  of the list above, whatever cut the resolver returned.
- It withholds no more than it must: every set of rows inside the cut that pass their test and
  that holds its own sources is kept (`kept_of_closed`).
- It never withholds a row all of whose references are resolved. The landings, the attestations
  of landings and of commits, and the commits read only one another, by resolved references, so
  at a cut consistent for those references every one of them inside the cut is kept
  (`kept_of_resolved`). The filter takes rows out of `att`, `runs`, the `interp` chains, `decl`
  and the dispositions, and takes no landing.
- At a cut consistent for every reference, where every row passes its test, it withholds
  nothing and the read is the prefix (`kept_iff_of_consistent`). For the pass attestations and
  the runs, whose test is empty, that is the case at the head, since a pass is written after
  the landings it read, and at a recorded cut every position of which is served. It is not the
  case at the head for one row: a witness's attestation of a commit the sensor has not read
  yet, whose commit is not in the ledger until the sensor's next job. Until then the filtered
  read at the head cut withholds it and the present read returns it. No answer shows the
  difference, since `as of "head"` is the present read (§3.4); a test that compares the two
  reads at the head leaves that row out (§10, SNP-8).
- For a test that does not depend on the cut it is monotone, a row kept at a cut being kept at
  every later one, and it is append invariant (`Kept.mono`, `kept_grown_iff`).

So the cut read is consistent for the resolved references, and the read at it is filtered for the
rest. That read is a derived view of the prefixes (SNP-5), and on `att`, `runs`, the `interp`
chains, `decl` and the dispositions it is not the prefix. The control is the store of
`Witness.pass_drags` with the pass's reference filtered: the landing chain behind its window is
lowered alone, the prefix at that cut holds a pass whose landing is outside it, and the filtered
read withholds the pass and keeps the attestation after it and the other class's landing
(`Witness.pass_withheld`).

**The resolver.** A name that selects a recorded cut needs none while every chain serves the
record's positions: the record is consistent. Otherwise it is two steps alternated until
nothing moves:

1. the floor: each chain's position is lowered to the greatest position at or under it that the
   chain serves (§7.1);
2. one pass of the descent: each chain's position is lowered to the first event inside the cut
   whose recorded bound, for a resolved reference, lies outside it.

The bound the descent reads is one of three and no other: `att_head` on a landing, the commit
on the sensor's attestation of a commit, the frontier on a record. A chain-table row also
records positions for the filter: the landing heads on a pass attestation and on a run, the
commit on a witness's attestation, the two landing positions on a supersession. The descent
never reads those. Followed, they are the cascade the filter exists to prevent
(`Witness.pass_drags`).

A round that moves anything lowers a position, so there are at most as many rounds as the
frontier has positions. Neither step alone is enough, in either order: the descent leaves the
served positions, and the floor breaks consistency again. The library proves that the cut
exists and is unique, with and without served positions. The attack module runs the descent
against the definition by enumerating every cut under the frontier (seed 461) and the
alternation against the greatest consistent served cut (seed 492), with each one-shot order as
a control that is refuted (493, 494). SN-2 transcribes the alternation. `[THEOREM for existence
and uniqueness; the resolver attacked, not proved]`

### 3.6 Certificates

The certificate of a cut is, for each chain, the digest of its prefix under the chain's hash
(`certify`). A store verifies a certificate when its own prefixes have those digests
(`Verifies`). `[THEOREM: SNP-9]`

**Which chains have a hash.** A landing chain from SN-1, as the `hash` of the row at the
position. `repo` always: the commit's sha is git's own chain. `chat`, `att`, `staging` and
`runs` from SN-2, as the running hash of the chain table added beside each. The `interp` chains,
the claim ops among them, `decl` and `verdicts` from SN-6. An `interp` chain gets a sequence
number and a running hash over its rows' content, the wall bookmark left out. `decl` gets a
chain-table row at every declaration, a second declaration of a pair included, and its hash
runs over a salted commitment to each row as the landing log's does, so no row a hash covers is
rewritten when a note is declared again (§5.4) and a purge can empty one (§6.1). `verdicts` has
its position already and gets the running hash. And `use` with the stage that builds the
field. A record carries a digest
for each chain that has a hash when it is taken and a null for the others, and `verify` says
which chains it checked. Until a chain is hashed, a recorded cut fixes its position and nothing
about its rows, and the two conclusions below do not reach a view that reads it. `[INFERENCE]`

- **Reproducible.** The certificate of a cut verifies on every extension of the store
  (`verifies_certify_of_extends`): the same store later, a restored backup, a clone.
- **Checkable, for what it digests.** Under a collision-free digest, two stores that verify one
  certificate have the same prefix of each digested chain at its cut (`Verifies.readAt_eq`), so
  every derived view of those prefixes is the same on both (`Verifies.view_eq`). A landing chain
  digests commitments, so what is pinned directly is the commitments. A commitment that is
  binding, as a salted SHA-256 is under the same hypothesis, pins the events behind them: two
  committed stores that verify one certificate were made from the same events at its cut
  (`Verifies.readAt_eq_of_committed`), and under one erasure they read the same store with holes
  (`Verifies.contents_eq`). The control is a digest with collisions, under which two different
  chains of one length agree (`Witness.digest_collides`).
- **What it does not attest.** An erasure: a store verifies a certificate after a purge exactly
  when it did before (`verifies_purge_iff`), so a backup taken before a purge and restored later
  verifies every certificate and still holds what was purged. A restore therefore has to apply
  again the purges recorded since, which §6.1's attestation of a purge makes listable. The
  grant, and the identity of the embedder and the tokenizer (D5). So an answer at a recorded cut
  is the same on two stores that verify it for one erasure, one grant and one derivation
  identity, and not otherwise; for the grant and the erasure together that is
  `Verifies.shown_eq`. A seal would be a third thing a certificate does not attest, since a
  retire written after a certified cut would change what is served at it
  (`Witness.seal_not_certified`); the design applies none (§6.2), so a retire after a cut
  changes nothing read at it.
- **Cheap.** A certificate extends over the events since an earlier one
  (`certify_digest_readBetween`), and the meet and the join of two certified cuts are certified
  from the two certificates alone, chain by chain the earlier or the later digest (`certify_inf`,
  `certify_sup`).
- **Compatible with erasure.** A chain that digests commitments keeps every certificate when an
  event's content is erased (`verifies_purge`), and what a reader then reads is the store with
  holes (`contents_purge_committed`).

Checking a certificate against a store is one seek a chain, the stored hash at the position
against the certified digest, 3 microseconds; recomputing a chain from its first row is the
audit, 0.7 to 0.8 s for a million rows. `[MEASURED §11]`

## 4. Reads

### 4.1 `read_at` and `read_between`, ledger by ledger

`read_at(c)` is the prefix of a chain at a position and `read_between(a, b)` the events after `a`
and up to `b` (`readAt`, `readBetween`). The second composes with the first and with itself
(`readAt_append_readBetween`, `readBetween_append`), so nothing more is needed of a ledger than
these two. `[THEOREM: SNP-3]` For a ledger of keyed rows the read a caller wants is the state of
a key at a cut, which is a function of the prefix (`stateAt`); the table names it `state_at`.
For each ledger, the reads, the index each needs and the cost. A cost with no grade is an
estimate from the measured log, the same engine and the same shape of index, and is not
measured:

| ledger | `read_at(c)` | `read_between(a, b)` | index | cost |
|---|---|---|---|---|
| landing log, a chain | the rows with `seq ≤ c`; `state_at` of one path: its last event at or under `c`, by its key; every head of a class: the `store` rows with `seq ≤ c` not closed at or under `c`, over the class's chains | the rows with `a < seq ≤ b` | the primary key, `landings_path`, `landings_closed` | one path 3 µs through `landings_path`, and 1.4 µs for its keyed hash; 1,000 positions 0.64 to 0.69 ms; every head §4.2 `[MEASURED §11]` |
| a document's version chain | the log's `store` rows of the identity at or under `c` (§6.2) | the same rows in the range | `landings_path` where the identity is the path, `landings_doc` where it is not | 9 µs for seven versions through the index, and 49 to 57 ms when the planner takes the primary key, so the statement names the index `[MEASURED §11]` |
| raw objects | the object of the digest the log names at `c` | the objects the delta names | none: content-addressed | one file read, the object's bytes |
| chat log | a session's turns whose chain number is at or under `c` | the turns numbered in the range | the chain table's key and its `(session, turn)` | a range of an integer key: of the order of the log's 0.7 ms a thousand rows |
| attestations | by id, as today; in order, the chain table at or under `c` | a range of the chain table | the chain table | the same order, where `all()` sorts the ledger by wall time and `producers_of` decodes every record today (`core/attestation/store.py:127-132`, `:159-165`) |
| citation readings | the edges of the commit projected at or under `c` on `att` (§5.1) | the paths whose blob differs between the two commits, by the commit ledger's `files` rows (`ops/code_snapshot.py:59-69`), with their readings at each | exists: `(target_ref, commit_sha)` and `(source_ref, commit_sha)` (`reference_edges.py:149-156`); the projection's position is one integer column more | one indexed lookup a reference, as today |
| commit ledger | the commit and, through git, its ancestors | git's range | none: the ledger keeps no parent, so the range is git's | one `rev-list`, not measured |
| staging | `read_at(g)`, as built | the rows admitted or tombstoned in the range | `staged_rows_generation` exists; none on the tombstone stamp | a range of the generation index; a scan for the tombstones |
| run ledger, verdicts, structural snapshots, observation history | by key; in insertion order | a range | a sequence number, from SN-2 for the run ledger | no reader at a cut yet |

The landing log's reads are the ones every other store's read at a cut goes through, since it
is the log that says which version of a path a cut holds (§5).

### 4.2 Every head at a cut

Reading the head of every path of a class at a cut is the `store` rows with `seq ≤ c` whose
`closed_at` is absent or above `c`. On a synthetic chain of a million events over 100,000 paths
it took 52 to 56 ms at a cut a tenth of the way in, 147 to 166 ms at the middle cut and 240 to
275 ms at and near the head. `[MEASURED §11]` The cost is the part of the log the statement
walks, about a quarter of a microsecond an event, and not the size of the answer. Two readers
need it: the universe, for the strata it loads whole (`core/sentence/universe.py:275-299`), and
the lexical statistics at a cut (§5.3).

So the read from the log alone passes a tenth of a second at between a quarter and a third of a
million events in one chain, and the rule is by size. A chain under 250,000 events reads its
heads from the log. A chain over it keeps heads: the heads at some recorded cuts, continued
over the events since (`stateAt_eq_foldl`), which costs the distance to the nearest kept cut
instead of the prefix. That is built with SN-4 for an instance that has such a chain, and a
corpus instance has one from the start: ten million items are ten million events at the least.
An instance of a few thousand notes never needs it. `[THEOREM for the journal; INFERENCE for the
threshold, falsifier SNF-6]`

As built at SN-1 the cost is the other way round (§11). `heads_at` builds a row in Python for
each head it returns, 3.5 to 3.9 µs a head, against a walk of 0.14 to 0.15 µs an event, so the
size of the answer and not the part of the log walked is the cost, and the read from the log
alone passes a tenth of a second near 27,000 heads: a chain of 30,002 events takes 0.11 s. That
meets SNF-6's first condition. Kept heads at a recorded cut shorten the walk and leave the
building, so they do not answer it. Before SN-4 builds the universe's nodes on this read, either
the threshold moves or the read changes so that it builds less than a row a head, and which is
open (SN-c). `[MEASURED §11; the decision open]`

### 4.3 What the reads cost in bytes

On the fixture a landing is 434 bytes in the log with its indexes when the identity is the path
(the table 374, the key index 47, the closing index 13), and 396 when the identity is a short
id of its own (the table 315, the key index 47, the identity index 21, the closing index 13).
`[MEASURED §11]` The fixture's paths are 37 characters and its titles under twelve; a row grows
by the bytes of a longer path, twice where the identity is the path. A chain table's row is an
integer, the row's key and a 32-byte hash. A recorded cut is about 2.7 kilobytes by arithmetic
(§3.3). None of it is content: the log holds paths, digests and titles, which the catalog holds
already.

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
| vectors (atoms, occupancies), in the plane and in the curated store for what landed through the catalog | the chunk's text and the embedder's identity | version-keyed rows the plane keeps already; the log selects the version | no new bytes; a search over every version's rows, then a join with the heads at the cut. Not measured: the rows searched are the current ones over the current share, three times as many where two thirds are superseded, as on the lexical fixture | an instance that must drop superseded atoms (§9), after which a cut finds them pending |
| lexical units and postings | the chunk's text and the tokenizer's identity | version-keyed rows the index keeps already; the log selects the version; the statistics from the mask | no new bytes; 4,179 bytes a kept unit on synthetic text `[MEASURED §11]` | a query at a past cut over its budget at the instance's size: then statistics stored per class and per recorded cut |
| chat events, causal edges | the transcript as retained at the cut, and the commits inside the cut | recomputed at the cut, the present rows a cache of the head | 6 ms a session of 2,000 records `[MEASURED §11]`; no bytes | a sentence that walks the causal fiber at a past cut over a second on a real instance (SNF-5): then generations, written with a diff |
| interpreted artifacts with their hyperedges, interpreted relation edges | a model's output: of nothing that can be computed again | generations, the replaced row archived with its interval | one archived row a replacement, which is thrown away today; how often a row is replaced is not measured | a measured churn so low that declaring them outside the snapshot loses nothing |
| the relations a note declares | the note's text at a version, and the titles the catalog resolves at the cut | recomputed from the heads at the cut | one parse of a note's properties a head that has any, kept in a memo by digest; no bytes | nothing |
| claim ops | nothing: they are appended, keyed by their whole content | a position a first insert; the read at a cut is the rows at or under it, each served with what it names (§3.5) | one integer a row | nothing |
| authored supersessions | nothing: the owner's declarations, keyed by the pair, with a note a second declaration of the pair replaces | a chain-table row a declaration, with the note and the log positions of the two notes; the read at a cut is each pair's last declaration at or under it, served when the cut read holds both positions and neither is a hole (§3.5, §5.4) | one chain-table row a declaration: an integer, the pair, the note, two positions, a salt and two hashes | nothing |
| verdict dispositions | nothing: one row a verdict, appended (§2.2) | the key is the position: the read at a cut is the rows whose `verdict_seq` is at or under the cut's position on `verdicts` (§3.1), each served with the claim it is about (§3.5) | nothing new | nothing |
| the similarity backbone | the vectors of the support | recomputed, as today | nothing | nothing |
| citation readings | the tree at the commit and the extractor that projected it | append-only rows, as built, each stamped with the extractor's version and the position on `att` of the projection that wrote it; the reading of a commit at a cut is its rows stamped at or under the cut | one integer and a short string a row, on 3,029,562 rows over 1,487 commits at 567 bytes a row in the repository's records | the store's size: then a row valid over a range of commits (SN-b) |
| code memberships | git's blob at the path | version-keyed by blob; git's tree selects the version | nothing new | nothing |
| the utility field (not built) | the use log | a fold with kept checkpoints | a checkpoint a declared number of ticks | its own note's measurements |

The figures for the citation readings are `docs/experiments/corpus-measurements-2026-11-07.md:106`
and `core/reference_view.py:15-16`. `[ESTABLISHED]`

The stamp on a citation edge is what makes its reading a function of a cut. Today a commit's
reading is the union of every projection of it so far (§2.2), so `as of` a commit answers
differently after a re-projection though the cut did not move, which is the reader SNP-1's
control refutes; and the commit's sha does not pin it. With the stamp, the reading at a cut is
the edges projected at or under it, a later projection is a later event, and the head reads
every projection as it does today. The rows the store holds when the stamp is added are stamped
with the `att` genesis, so their history starts there (§8). `[DERIVED from SNP-1]`

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
the statistics are the collection's and not the support's: every unit of every head, where the
mask reads the units' stored lengths and postings. A journal of the changes to the document frequencies has an entry a term a unit, no
fewer than the postings (122 a unit on the synthetic text). An index with its statistics built in
cannot serve a cut, or a clearance, without a copy a mask; if the index moves to immutable
segments, a segment carries no statistics and they are computed from the mask, as they are
today, until a query at a past cut runs over its budget (SN-e). None of the three is measured
at a corpus's size. `[INFERENCE, falsifier SNF-7]` The tokenizer's identity is the
present's, as the embedder's is: a changed tokenizer resets the index (`lexical.py:180-194`) and
the backfill lands the active items, so a superseded version's units are derived again from the
raw store when a cut asks for them.

### 5.4 Model output, and what is not model output

Three stores were read as one kind, and they are three.

**The relations a note declares** are not model output. The edge store has two producers kept
apart by provenance (`core/relations.py:7-16`): an authored edge is read off a note's own
`supports::`, `contradicts::` and `contextualizes::` properties and resolved by title through
the catalog (`relations.py:140-158`), so it is a function of the note's text at a version and of
the catalog. At a cut it is recomputed: for each head at the cut that has such a property, the
property parsed from the raw object the log names, the title resolved among the heads at the
cut. Nothing is stored and the edge has its note's class. `[DERIVED from SNP-5]`

**Claim ops and authored supersessions** are appended sets that lack a position, and they differ in
their key. A claim op is keyed by its whole content (§2.2), so a second write stamps a bookmark and
changes nothing else. An authored supersession is keyed by the pair, and its note is a column
outside the key, so a second declaration of a pair replaces the note with the bookmark
(`core/stores/authored_supersession.py:113-119`, `:159-161`; §2.2 says what that loses today). The
supersessions are the owner's declarations. The claim ops are appended by a store that calls no
model (`core/stores/claim_ops.py:14-15`), and what it appends is by design a model's proposal:
extracting the operations from a dialogue is a model task behind an analyzer whose default proposes
none (`core/kernel/recursion_ops.py:44-46`), and at `e3e3ee47` no caller outside the tests applies
one. So the claim ops are rows of the class `interpreted` (§3.1). The storage choice does not depend
on who proposes them. A claim op gets a sequence number at its first insert, and the read at a cut
is the rows at or under it. A supersession gets a row of its chain table at every declaration: the
sequence number, the pair, the note and the positions §3.5 gives, under a salted commitment the
chain's hash runs over. The store's own row stays the pair's latest declaration, the head's cache;
the read at a cut is each pair's last declaration at or under it. So no row that a running hash
covers is rewritten, in either store. Both are further filtered by what they name. A claim op is
served when the claim it acts on is and, for a supersede, the conclusion artifact the same call
wrote (`claim_ops.py:45`, `:161-163`). A supersession is served when the cut read holds the landings
of both its notes (§3.5), so a read of the active projection at a cut marks no note historical by a
note the cut does not hold. `[DERIVED]`

**Interpreted artifacts and interpreted relation edges** are model output: written by a pass
that calls a model or by a `link` request (`core/relations.py:192-210`,
`core/ingest/writer.py:521-535`), each keyed by what it is about, so a later write replaces the
row (`core/stores/derived.py:209-216`, `core/stores/edges.py:88-106`). The output cannot be
computed again, so the two choices are to keep it by generation or to declare it outside the
snapshot. This note keeps it. `[INFERENCE, falsifier SNF-8]`

The form is the one the observation stores use: archive, then replace
(`core/stores/code_observations.py:211-254`, `core/stores/observation_history.py:46-56`). Each
store gets a sequence number a write, its chain; each row the number it was written at; and a
replaced row goes to a history table with the number it was replaced at. The read at a cut is
the row whose interval holds the position (`genRead`), and at the head it is the present row
(`genRead_gens_length`). `[THEOREM: SNP-5, SNP-4]`

A kept row is served at a cut only when its sources are there, and what a row's sources are
differs between the two stores.

- A relation edge's two ends are content digests (`edges.py:39-40`), so the row is about two
  particular versions.
- An artifact's key is not its sources. The key hashes the kind, the subkind and the sorted
  `subjects`, which are note titles (`derived.py:55`, `:97-100`; the callers pass titles,
  `core/curator/curator.py:98`, `core/dreaming/dreamer.py:153`), so one row is replaced by a
  later pass over the same titles whatever versions of those notes the two passes read. Its
  sources are its `derived_from`: note digests, or the ids of other artifacts
  (`derived.py:186-189`; `curator.py:175`, `dreamer.py:160`). The artifact records no run. Its
  link to the pass that wrote it is the attestation it names (`derived.py:59`).

So a kept row is in the read at a cut when four things hold: it was written at or under the cut
on its own chain; the attestation it names, if any, is kept at the cut on `att`, which for a
pass attestation is more than lying under the cut (§3.5); every
digest its sources reach is some path's head at the cut, where an artifact's sources are
followed through the artifacts it names, each as it stood at the cut, down to digests (the
store refuses a cycle, `derived.py:186-189`); and none of those digests is erased
(`mem_serve_iff`). A source retired since the cut withholds nothing: the retire is shallow
(§6.2). `[THEOREM: SNP-7 for the erasure, SNP-8 for the closure; DERIVED for the
rest]` This is the row filter of §3.5: it withholds a row and lowers no position. Until SN-6
builds it the `interp` chains serve two positions, the empty prefix and the head (§7.1).
Lowering them moves no chain outside them but the chain of records, which follows (§7.1): the
other references into them are their own, a claim op's to an artifact and an artifact's to
another, and those are the filter's.

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
extraction happen once a process. By arithmetic from that figure, not measured: the first
sentence of a process that walks the fiber at a past cut pays 6 ms and one transcript read a
session, so 6 s and 0.8 GB read for a thousand sessions of the fixture's size, and the memo's
price after that. Generations are the alternative: the rows kept, keyed by session and order,
each with the range of `chat` positions it was valid on, written with a diff so that a session's
growth adds its new events and closes only the rows that changed. They need the projector and
the integrator written again, which is not sized here, and are kept for the instance that needs
them (SNF-5).

### 5.6 An instance with no embedder

Nothing above reads the plane to learn what existed. The node set of a snapshot comes from the
landing log, which lives in the catalog's file; the lexical units, the version chains, the causal
fiber and the citation readings need no vector; and a semantic clause on such an instance ranks
by the lexical index and says so, at a cut as at the head (ING-21). The plane's own supersession
log could not carry this: an instance with no plane has none, and under lazy embedding it records
the order in which the drain reached the items, not the order in which they landed. Today the
universe takes the mirror's nodes from the plane's rows (`core/query.py:462-465`); at a cut it
takes them from the log. `[DERIVED; ESTABLISHED for the present reads]`

One set of rows the log cannot give. The curated store is read by `near` and by `read`
(§2.2), and one of its two writers, `scripts/curate_local.py:96-108`, adds rows with no catalog
row, so no landing and no position. Such a row is outside the snapshot: at a cut it is not a
node, and the answer's note says how many curated rows have no landing and were not read. What
`ingest_curated` landed is in the log's `curated` chain and is read at a cut as a note is. The
repair is to route that script through the writer's `store`, as every other source is; it is
parked (SN-i) because it changes a writer and not a reader. `[INFERENCE]`

## 6. Erasure and scope

Two things are parameters of a read and no function of the cut, because they are the present's:
what has been erased, and what the asker may see.

### 6.1 A purge leaves a hole

No erased event is visible at any cut (`not_erased_of_mem_visible`), a larger erasure shows a
sublist (`visible_sublist`), and two stores that differ only in erased events give every
derivation of what is visible the same reading at every cut (`erased_invisible`). `[THEOREM:
SNP-7]` That is a statement about a reader that reads the visible events. It becomes a
statement about the code only when every reader of a store goes through the erasure, which is
what the table below is for.

The erasure keeps positions. The store with a hole at each erased event has the head it had and
commutes with the cut (`head_redact`, `redact_readAt`); an erasure that deletes rows moves the
later ones up, and a read at a cut then holds an event from after it (`Witness.compact_moves`).
`[THEOREM]` The plane's supersession log is the second kind today: after a purge, a later landing
at the path took position 1 again. `[MEASURED §11]`

**The hole keeps its key.** A purge is by digest, and it may take an old version of a path
that is still live, since only the digest's active references block it
(`core/ingest/purge.py:52`). If the emptied row lost its path, a seek by path would pass over it
and return the version before it as the path's head at a cut where the purged version was the
head; and a reader that dropped the holes before seeking would return a version from after the
cut (`Witness.keyless_hole`). So the row keeps `path_key`, the keyed hash of its path. On a
chain whose holes keep their keys, the read of a path at a cut is its last event at or under
the cut, returned as a hole when that event is erased, never an earlier version and never a
later one (`stateAt_holes`, `stateAt_holes_of_erased`, `not_erased_of_stateAt_holes`), and the
seek, the closing-stamp read and the fold still agree (`lastWrite_holes`, `genRead_gens_holes`).
`[THEOREM: SNP-7]` On the fixture, after the fifth of a path's ten versions was emptied, the
seek at a cut where it was the head returned the emptied row. `[MEASURED §11]`

**What a purge empties in the log.** The path, the identity, the digest, the title, the salt
and the wall bookmark become null; the commitment and the hash stay. The certificates keep
verifying (`verifies_purge`), a reader reads a hole (`contents_purge_committed`), and since the
commitment was salted and the salt is gone, it can no longer be tested against a guess of the
content. `[THEOREM: SNP-9 for the chain; DERIVED for the salt]` What stays, and why:

- `chain`, `seq` and `kind`: the position, which the erasure must keep.
- `path_key`: so that the hole shadows. It can be tested against a guess of the path only with
  the instance's landing-log secret, which is not in the file (§3.2, as built at SN-1).
- `closed_at` and `version`: positions and a count, no content. `closed_at` is a function of
  the rows that keep their keys, so nulling it would hide nothing.
- `att_head`: a position on another chain.

The hole is thus still tied to its path while another version of the path keeps its content, which
is the intent: the purge is of a digest, and the path with its other versions is not erased. When
no version of the path keeps its content, its other rows, its `retire`, its `move` and its `leave`,
name nothing that is not erased, so they are emptied with the last version, and no row names the
path, its identity or the date of its delete (D14). As built at SN-1, after review: `remove`
empties every row of the path; `remove_digest` empties the rows of the digest and then, for each
path they named, the path's other rows in every chain when none of its `store` rows keeps its
content, finding them by the names they carry and the keys the emptied rows keep, so a purge needs
no secret. That is `purge_raw`'s usual case, a note deleted and then purged, whose `retire` had
kept its path, its identity and its date before. The bookmark goes because nothing looks a
landing up by its date, and a date on a hole says when the erased content arrived. The bytes
SQLite frees when a row is emptied stay in the file until it is vacuumed, as the catalog's deleted
row's do (§11); a file copied before then holds them, and clearing them is SN-3's reach.
`[MEASURED for the bytes, by a probe of the build: the purged path in the freed pages after the
purge and a checkpoint, and in none after a vacuum, which the stage's test checks]`

That is a rule the record already has: no tombstone keeps a content hash of purged private text,
and for prose privacy outranks lineage (`docs/design-notes/vector-membership-store.md:810-813`).
A digest of purged bytes is a test for those bytes. What a purge has to reach, against what it
reaches today:

| store | today, after a purge | what a snapshot needs |
|---|---|---|
| raw object, catalog row, plane occupancies and their freed atoms | removed `[MEASURED §11]` | the same, and the log's rows emptied |
| the vector table's earlier dataset versions | still return the text `[MEASURED §11]` | the purge ends with a compaction that keeps no earlier version |
| lexical units, postings and version records | remain, with the words `[MEASURED §11]` | removed with the plane's rows |
| the version chain's rows | still name the digest `[MEASURED §11]` | the digest nulled, the row and its number kept: a second owner-gated write beside the relabel (`core/stores/versions.py:132`) |
| the curated store's plane and atoms | not opened: the purge is given the main vector store only (`scripts/purge_raw.py:51-56`, `core/stores/curated_store.py:30-38`) | the same removal and compaction as the main store |
| relation edges and artifacts that name the digest | untouched (`core/ingest/purge.py:58-62` names neither store) | not served (`mem_serve_iff`), and removed by the purge, with the archived generations that name it |
| dream claims of the run ledger | keep the digests a claim rests on and its surface text (`core/stores/runledger.py:90-97`) | the claim's support and text nulled, the row kept |
| staging rows | keep the content digest and the payload (`core/stores/staging.py:130-131`) | the digest and the payload nulled, the row and its generation kept |
| claim ops | keep the warrant's text (`core/stores/claim_ops.py:40-48`) | the ops on a removed artifact removed |
| authored supersessions | keep both digests and the note (`core/stores/authored_supersession.py:112-120`) | the store's rows that name the digest removed; in the chain table the pair, the note and the salt nulled, the commitment and the hash kept |
| rejected requests of the ingress spools | keep the request's text (`core/ingest/ingress.py:20-27`, `:505-517`) | the files that hold the purged text removed |
| the attestation ledger | still names the digest `[MEASURED §11]` | decision D9 |
| a deletion attestation | none is written (`core/attestation/store.py:3-6` says one is) | one, of action `purge`, naming the positions emptied and no digest |

Rows without a grade were read in the code and not measured. Until the stores of the middle
rows are reached, a read of them at a cut would return what a purge left. So the erasure's reach
is stage SN-3, and it lands before any of those stores is read at a past cut (§12). The
attestation of a purge lists the positions it emptied, which is what lets a backup restored from
before it be purged again (§3.6).

### 6.2 A retire is the shallow removal

A vault delete is a tombstone: the catalog's row goes inactive and the raw object stays
(`catalog.py:160-172`). What that does to the past was decision D3. This note recommended a
seal; the owner decided otherwise on 2026-11-11, after the design was merged, and this section
states the decision and what follows from it. Removal has two forms.

- **A retire is the shallow form.** The item leaves the present: from the retire on, no read
  returns it as live. Its history stays readable at the cuts where it existed. No seal is
  applied to a retire, and a note written later at the same path takes a fresh identity, so
  that it does not inherit the retired note's versions.
- **A purge is the deep form** (§6.1): a hole at every cut. Every derived answer at a past cut
  becomes what it is on a store that never held the item's content: a kept row that rests on it
  is not served, the statistics of a mask are computed without it, and what is recomputed is
  recomputed without it (`erased_invisible`, `mem_serve_iff`). So the answers about the item's
  neighbourhood at past cuts change with a purge, and that is intended. What survives is the
  record that a purge happened, its attestation and the positions it emptied, and not the
  content.

**What a read at a cut returns of a retired item.** The value of an identity at a cut is the
one it held there: its last event at or under the cut, a `store` or nothing (`stateAt`). The
history of an identity at a cut is its landings inside the cut (`landingsAt`). Both are derived
views of the prefix, so a retire written after a cut changes neither (`stateAt_append`,
`landingsAt_append`), the history at an earlier cut is a prefix of the history at a later one
(`landingsAt_mono`), and at the head the history is every landing of the identity
(`landingsAt_length`). `[THEOREM: SNP-1, SNP-2, SNP-4]` Two things the seal cost are gone with
it. A read at a cut no longer consults the present for a later retire, which was one more seek
a keyed read. And a certificate now pins what is served of a retired item: with a seal, a
retire after a certified cut changed the answer at it and the certificate could not show that
(§3.6).

**The two seals remain proved, and the design applies neither.** They are facts of the model
and stay in the library as what a seal would do.

- The stricter seal (`servedAt`, `historyAt`). A retire among the events past the cut closes
  the cut for that identity: no cut before the retire serves it or any version of it
  (`servedAt_append_of_retire`, `historyAt_append_of_retire`), and growth changes what is
  served only by removing it (`servedAt_of_append`).
- The looser seal (`servedNow`). An identity is withheld at every cut exactly while it is not
  live at the head; a later landing lifts it and brings the past back
  (`servedNow_of_servedAt`, `Witness.servedNow_restores`).

The history with no seal holds everything the stricter seal serves, as its end
(`historyAt_suffix_landingsAt`): the seal only withheld. The control for the choice is the
retire that empties a served history under the seal and leaves the unsealed one as it was
(`Witness.seal_empties_history`). `[THEOREM: SNP-7]`

**The fresh identity.** The stricter seal was recommended for one failure, and the fresh
identity removes that failure at its source. A new row's identity is its path unless it
declares one, and a re-record of a path keeps the identity the path has (`catalog.py:103-121`),
a tombstoned row included. So a different note written later at a deleted note's path has the
deleted note's identity, and its chain of versions holds the deleted note's versions (§2.3,
item 8). With one identity used again, the history with no seal returns the deleted note's
versions under the new note, at the head and at every cut after it landed
(`Witness.reused_identity_inherits`); the looser seal brought them back at the earlier cuts as
well; and the stricter seal hid them by sealing the whole past of the identity. The decision
takes the fourth way: the new note is another identity.

The rule is on the first bind. A `store` at a path that has an open row lands under that row's
identity, as today. A `store` at a path with no open row is a first bind, whether the path has
no row, a tombstoned one or only emptied ones: the identity is the one the item declares, or
the one held at a vanished path with the same bytes (the writer's rule R6,
`core/ingest/writer.py:438-481`), and otherwise the path's own when the log holds no event of
the path, and a fresh one when it does. The fresh identity is named by the path and the
position of the path's last event in the log, `<path>#<chain>.<seq>`: the retire, the `move` or
the hole that closed it. A position is given once, so the name is new. It is a function of the
rows already written, so a landing repeated after a crash before its key takes the identity
the first attempt took and appends no second version (ING-7). It differs from its path, so
`landings_doc` indexes it (§3.2), and R6's refusal of an identity that another active path
holds applies to it as to a declared one. As built at SN-1, a position is given once only while
the log's tables stand: the rollback drops them and the next genesis numbers chains and positions
from 1 again (§12, SN-1), while the version chains, in their own file, keep their rows. A name
made after a rollback could then be one made before it, and its version chain would already hold
the earlier note's versions. SN-3 decides, before it names any identity, what closes that: a
high-water mark of chain ids kept outside the tables a rollback drops, or a name a rollback cannot
repeat.

On the model a chain of landings and retires at paths is keyed again by identity (`lives`): the
path with the number of the path's retires before the event. `[THEOREM: SNP-1, SNP-7]`

- The identity a landing takes is a function of the events before it (`lives_take`).
- The history of the identity a path holds at a cut is the path's landings since its last
  retire inside the cut: no version of an identity retired at the path is in it, at the head or
  at any cut (`landingsAt_lives_present`). This is what the stricter seal's history gave where
  it served anything (`historyAt_of_retire_inside`), with nothing sealed.
- A retired identity keeps the life it had and gains nothing: at every cut that holds its
  retire, whatever lands at the path afterwards, its history is the landings of that life
  (`landingsAt_lives_of_retire`), and at a cut inside the chain it is unchanged by any growth
  (`landingsAt_lives_append`). Under the stricter seal the same retire emptied it.

What the model leaves to the code: the name of an identity, an identity a note declares, a
rename, which moves an identity between paths, and a life closed by a hole: the rule above takes a
path whose rows a purge emptied as closed (§6.1), and `lives` counts retires only, so that case is
an obligation of SN-3's tests and no theorem. The retire is by identity and not by path, so a
rename retires nothing: the old path's tombstone is a `move` (§3.2). A new note written at a
path a rename left is a first bind like any other, which closes the second case of §2.3's item
8, where today it takes the identity that moved.

**What the decision costs.**

- **A note that goes and comes back is two identities.** The sync retires every stored path
  its source no longer lists (`ingress/sync_vault.palace:7-15`,
  `core/ingest/writer.py:499-519`), and a source whose directory is missing lists no file
  (`core/ingest/readers.py:126-137`), so a vault that is missing at a sync retires every note,
  and the next sync lands each again under a fresh identity. Nothing is sealed and nothing is
  lost: at every cut before the retire the old identity reads as it did, and the log's rows of
  a path, read by its key, run across both lives. What is lost is continuity at the head:
  `trace` of a returned note starts at its return. Under the stricter seal the same event
  sealed every note's past until the owner lifted it. A note that declares its identity is the
  exception by its own statement: it binds that identity again when it returns, and its
  history at a cut is all its landings inside the cut, on both sides of the retire. The
  decision as the owner stated it names no exception; this one is the design's reading of it,
  for the owner to confirm, and it holds for any note that declares the retired identity, since
  R6 binds a declared identity that no active path holds (`core/ingest/writer.py:448-462`).
  `[INFERENCE, falsifier SNF-17]` Joining
  two identities of one path is not designed here: the owner-gated re-key
  (`catalog.py:210-241`, `core/stores/versions.py:132`) refuses to merge two chains. It is
  parked as SN-l, with SNF-10 as its re-entry.
- **A delete withdraws nothing from the past.** A retired note is read at the cuts where it
  existed by any asker whose grant reads its class. An item that must not be read at a past cut
  is purged; that is what the deep form is for.
- **The rule is not retroactive.** An identity bound before the rule keeps the versions it has,
  the ones it inherited included: the log's commitments cover the identity of every row, and
  the versions store has no write that splits a chain. From the stage that builds the rule on,
  no chain continues across a retire unless the note declares it. The stage's migration counts
  the identities that have a `store` at a path after that path's `retire` in the log, which is
  what the log has recorded since its genesis, and no more. The genesis writes a path's present
  as one `store`, so an identity that inherited before the log is not counted; where such an
  inheritance could be found, if anywhere, is the version chains read against the catalog's rows,
  and this note has not established that any store marks a delete before the log. Nor does the
  count see §2.3's second case: a note landed at a path a rename left is a `store` after a
  `move`, and the identity it inherits is then held by two active paths, which the catalog shows
  at the head. So the count tells the owner how many histories run across a delete the log
  recorded, not how many inherit.

**At the head.** `trace` of a note written at a path with a past starts at that note's first
landing, where today it runs back through the deleted note's versions. This is the one change
to a read at the head, and it was owed under every alternative (D3).

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
  applied after the read, and what must be hidden in number is hidden by chain, which is why a
  landing chain holds one class.
- The grant and the erasure compose: what an asker is shown, the grant's snapshot with the
  erased events masked (`shown`), is append invariant, holds no erased event, and under a
  narrower grant and a larger erasure is the restriction of what the wider grant is shown under
  the smaller erasure (`shown_grow`, `not_erased_of_mem_shown`, `shown_narrow`).

**What these laws are about.** They are about the read: the rows a grant is shown. They pass to
an answer when the answer is a filter of the read, as the members of `reach`, `trace`, `read`
and `changed` are. They do not pass to a score. A lexical score uses the statistics of the
reader's own classes, the unit count, the mean length and each term's document frequency
(`core/stores/lexical.py:316-321`, `:337-340`), and §5.3 keeps it so; a rank depends on every
candidate. So for a sentence that scores or ranks, the narrower answer is not the wider one
masked, at the head today as at a cut, and nothing here claims it is. `[ESTABLISHED for the
statistics]`

**The cut shown.** `snapshot_congr` holds for a fixed cut. The cut read is resolved over every
chain (§7.1), and its position on a chain the grant names can depend on a chain the grant does
not name, when the named chain reads it (`Witness.resolution_reads_unnamed`). On a set of
chains that read from no chain outside the set, the cut read is a function of that set alone
(`ResolvesIn.eq_on_of_closed`). `[THEOREM: SNP-6]` A landing chain reads `att`, and `att` reads
`repo`; both mix every class. So the cut shown to a grant is a function of its own chains, of
`att` and of `repo`. Landings of another class move the head of `att` and change none of that
at a recorded cut: the record's positions are fixed, `att` is never pruned, so it serves them,
and the references of the events inside the cut do not change as the store grows
(`Consistent.of_grown`). What a narrower grant can learn through the cut shown is only that
`att` or `repo` did not serve a position, which is a fact about the instance and no class's
data. The filtered references do not enter the cut shown, since the resolver does not follow
them. A row withheld because a chain the grant does not name was read low tells the asker that
that chain did not serve the cut, the same kind of fact. `[DERIVED]`

Two consequences for the surface. An answer names the cut it read on the chains the asker's grant
names and on no other, and the bounds a row records (§3.5) are never shown: `att` mixes every
class, so its positions count other classes' landings. And a class is a row's class now: a
whole-class relabel changes the label of a chain, and a row moves between chains only by a
`leave` and a `store` (§3.2; the design had a `move`, and SN-1 made it a kind of its own), after
which its earlier events stay under the class they had (ING-17). A relabel itself moves a whole
chain to another class, so a read by class at a past cut follows the chain's class now, while a
read by chain is unchanged (§10, SNP-1's test). `[DERIVED]`

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
- It rises with the frontier, and with what is served while the served positions only grow
  (`ResolvesIn.mono`): as the stages of §12 give stores a past, the cut read for one name climbs
  toward the cut asked.
- When every position is served it is the resolution of the frontier (`resolvesIn_univ`), and at
  the head, which is consistent because a store holds the sources of its own events, it is the
  head (`resolvesIn_self`).

**Which chains go down together.** The cut read is not a floor taken chain by chain. A chain
that others read takes its readers with it: where it is read low, every event that reads past
that position is outside the cut, and so is everything that reads those events
(`Witness.record_drags`). A chain that no other chain reads is lowered alone: from a consistent
cut asked, the cut read is the cut asked with each such chain at the greatest position it
serves at or under the one asked, and every other chain as asked (`resolvesIn_of_unread`, and
`resolvesIn_update_of_unread` for one chain). And a chain that reads a lowered chain, and that
nothing but itself reads, follows it and takes nothing with it: it is read at the greatest
position it serves whose events read the lowered chains inside their new positions
(`resolvesIn_of_followed`). `[THEOREM: SNP-10]`

The design is arranged so that, among the references the resolver follows, the second and the
third case are the only ones that occur at a recorded cut. Those references are a landing's to
`att`, the sensor's attestation's to `repo` and a record's to every chain it certifies (§3.5).
Neither
`att` nor `repo` has a horizon that moves: the attestation ledger is never pruned (§9.2) and
`repo` is git's. Every chain that can fail to serve a recorded position, a landing chain behind
a history window, a chain that keeps no past yet, the use log behind its horizon, is read
through a resolved reference by one chain only, the chain of records, which no other chain
reads (§3.3). So at a recorded cut each chain that cannot serve is lowered to the greatest
position it serves; the chain of records is lowered with them, to its last record every
position of which the cut read holds (`Witness.record_follows`); and every other chain is read
as recorded. `[DERIVED]`

That is a statement about positions, and it holds for the resolved references only. A row that reads
a lowered chain through a filtered reference, a pass attestation, a dream claim, an interpreted row,
a claim op or an authored supersession, leaves the read by the filter of §3.5 and moves no position:
at a cut where a landing chain is read at its empty prefix, every pass attestation that read a
landing of that chain is withheld, with the artifacts that name it and the supersessions between
notes of that chain, and `att` keeps its position. Resolving those references instead would bring
the cascade back through `att` (`Witness.pass_drags`, against `Witness.pass_withheld`). `[THEOREM:
SNP-8 for the two controls]`

**When the cut read falls.** The monotonicity needs the served positions to grow. They do not
always. A store that keeps no past serves its empty prefix and its head, and loses its old head
when it grows; a history window removes the positions under the new horizon. In both cases the
same name read later is read lower (`Witness.served_set_shrinks`). So an answer read at the head
of a store with no past names a position that store will not serve again. The answer's note
marks such a chain as served at its head only, and the same name asked after the store grew
reads that chain at its empty prefix and says so. `[THEOREM for the control; INFERENCE for the
note]`

The answer is then exact for the cut it names: every law of §10 holds at the cut read. What the
answer says is that cut. It carries one note with the cut asked, the cut read on the chains the
asker's grant names (§6.3), and each chain on which the two differ with the reason: the store keeps
no past, the cut is under the chain's horizon, or the stage that reads the store at a cut is not
built. Where the filter withheld rows because a chain was read low, the note says of which store and
how many. For example, on an instance where the interpreted relation edges do not yet keep
generations:

```
as of "cut:4c1f09a2": land 3 (authored-solo) 412, chat 9318, repo 9de5325. Not read at the
cut: the interpreted relation edges keep no past and were read at their empty prefix.
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
| structural | `reach F`, `diffuse F`, `walk` over `F` | the citation reading of the cut's commit, as projected at or under the cut (§5.1) | today for a commit projected once; SN-4 for one projected again |
| temporal | `trace`, `reach D`, `walk` over `D`, `changed` (§7.4) | the history of the identity at the cut (§6.2): the log's `store` rows of the identity at or under the cut | SN-4; `changed` SN-8 |
| causal | `reach C`, `walk` over `C`, `witness` | the causal fiber recomputed at the cut (§5.5); an attestation kept at the cut on `att` (§3.5) | SN-5 |

| species | at a cut |
|---|---|
| `S`, similarity | recomputed from the vectors of the versions alive at the cut, within a stratum, as today (`core/sentence/universe.py:733-739`); no edge at a pending node |
| `F`, citation | the edges of the reading at the commit; a reading is whole, so nothing is inferred between commits |
| `D`, supersession | consecutive versions of the chain's prefix; at the node grain it is empty today and stays so (`universe.py:810`) |
| `C`, causal witness | an edge whose witness turn is inside the cut on `chat` and whose commit, if it ends at one, is inside the cut on `repo` |
| the signed relations (supports, contradicts, contextualizes) | an authored edge recomputed from the heads at the cut; an interpreted edge as a kept generation whose two endpoint digests are heads at the cut (§5.4) |
| an assumed edge (`assume`) | applied to the universe of the cut read; nothing is stored, and the result is a `Hyp` as today |

### 7.3 The verbs

- **`near`, `diffuse`, `reach`, `relate`, `walk`, `trace`, `witness`** read as their mode says.
- **`far`, `top`, `atleast`, `not`, `minus`, `and`, `or`, `then`, `within`, `over`** are the
  algebra on whatever universe the clauses built. Their laws (QSA-1 to QSA-4, QSA-10) are stated
  for any universe, so they hold at a cut with no change. `over` masks by a row's class, which is
  its class now (§6.3).
- **`read`.** A repository path: git's blob at the cut's commit, with the commit shown on the
  hit; when git does not hold the cut's commit the read is refused and says so, where today it
  returns `HEAD`'s blob (§2.1). A note or a dialogue turn: the raw object of the digest the log
  names for the path at the cut, never the vault file, which is the present and can be newer
  than the catalog (§2.1). A path whose event at the cut is a hole reads as erased, and not as
  the version before it (`stateAt_holes_of_erased`); a path whose last event at the cut is a
  retire reads as retired there, and at an earlier cut as what it held (§6.2). A
  transcript turn: the chat log's row when its number is at or under the cut. A curated row:
  what landed through the catalog as a note is; a row with no landing is not read (§5.6).
- **`witness`.** The record when it lies inside the cut: an attestation by its number on `att`,
  and a pass attestation only when the landings it read are inside the cut as well (§3.5); a
  causal edge by its turn and its commit; a citation edge by its commit.
- **`assume`.** The overlay applied to the universe of the cut read: a hypothetical at a past cut.
- **`do`.** A request is a whole sentence and takes no adjective (`core/sentence/grammar.py:4-5`),
  so it cannot be written under `as of`: a write has no past.

**`as of "head"` is no `as of`.** At the head cut the read is the store (`readAt_head`), every
derived view is the derivation of the present (`view_head`), the generational store reads the
store rewritten in place (`genRead_gens_length`), a snapshot is the grant's restriction of the
store (`snapshot_head`), the history of an identity is every landing of it
(`landingsAt_length`) and what is visible is the store without the erased events
(`visible_head`). `[THEOREM: SNP-4]` On the code this is the first test
of every stage: the same sentence with and without `as of "head"` returns the same hits.

**Refusals.** An ambiguous prefix, as today (`universe.py:471-475`). A name that selects nothing:
a sha no chain knows, a cut id no record has, a date before the first record, `HEAD`, a branch;
the refusal says which names would resolve, and it does not depend on what the stores hold. A
date after the newest record is not refused and is not the head: it is the newest record
(§3.4), and the answer says the head has moved since when it has.

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
  before was never recorded, so the positions before the genesis block ends are under the
  horizon. For the chat log and the attestation ledger the genesis is the rows they hold when
  their chain tables are added, numbered in the order they were inserted and followed by a
  horizon: within a chat session the turn order is exact, but the order across sessions and
  across the two stores was not recorded, so no cut inside the block is served. The citation
  edges held when their stamp is added are stamped with that genesis (§5.1).
- **Retention** (§9), which drops the generations closed at or under a declared position.
- **A reset**, after which every chain is a new chain with a new id (§2.3, item 7), and no
  record taken before it names a chain that exists.

The law is the same for the three. A generational store that drops the rows closed at or under a
horizon reads, at every cut from the horizon on, the state recomputed from the whole prefix
(`genRead_prune_gens`), though the prefix is no longer held, and landings after the pass leave
it so (`prune_landGen`). Under the horizon it is never wrong: a value it returns at a cut is the
value the key held (`stateAt_of_genRead_prune`). But what it lost it reads as absent
(`Witness.prune_forgets`), and nothing in the rows that remain tells a lost key from a key that
was never there: two chains can leave the same pruned store where, at one cut under the
horizon, a key held a value in the first and had never been written in the second
(`Witness.prune_indistinct`). Two horizons are the later one (`prune_prune`). `[THEOREM:
SNP-10]` The journal form says the same of a fold: continued from the state kept at the
horizon over the events since, it is the fold of the whole prefix (`foldAt_readBetween`), and
for a chain that drops its prefix whole, as the use log does, the chain's digest at the horizon,
kept as the seed, lets every certificate from the horizon on verify
(`certify_digest_readBetween`). `[THEOREM: SNP-3, SNP-9]` The landing log needs no seed: a
window empties its rows and keeps their commitments, so it is hashed from its first row (§9.2).

So the horizon is recorded, and a cut under it is not served.

- **Where.** As a `horizon` row of the chain, which the chain's hash covers, and in every
  recorded cut (§3.3). It only advances.
- **What a question before it gets.** The chain is read at the greatest position it serves at
  or under the one asked, which under a horizon is its empty prefix, and the answer says the cut
  is under the chain's horizon and names the first cut the chain serves. Every other chain but
  one is read as asked. Among the references the resolver follows, a chain that has a horizon
  above a recorded position is read by the chain of records alone, so each such chain is
  lowered alone and the chain of records with them, to its last record that the cut read holds
  (§7.1, `resolvesIn_of_followed`). What else follows a lowered landing chain is the rows about
  it, by the filter and not by position: a pass attestation, a dream claim, an interpreted
  row, a claim op or an authored supersession whose sources are not inside the cut read is
  withheld (§3.5, §5.4). A sentence
  all of whose chains are under their horizons returns the note and no hit.
- **What that means today.** A commit read before the log exists resolves, on every chain but
  `repo`, under the horizon: `as of` such a commit reads the citation graph and the repository's
  files at the commit and nothing else. For a commit projected once, and held by the checkout,
  that part is exact, and it is the lawful part of what `as of` does now; a commit projected
  again has a reading that grew (§5.1), and a commit the checkout lacks is read at `HEAD`
  (§2.1). The observation that the version store held one generation and so had nothing to
  snapshot (limits-of-the-algebra, L7) is this boundary seen from the other side. `[DERIVED]`

## 9. Retention and cost

### 9.1 What grows

A landing drops nothing today: a retired path's rows and a superseded version's rows stay in the
plane and in the lexical index (`core/stores/plane.py:497-499`, `core/stores/lexical.py:260-265`),
and rows go only with a purge or a reset. So the bytes of a past are mostly paid already, and
the snapshot adds three things.

| what | a | bytes | source |
|---|---|---|---|
| the landing log | landing | 396 to 434 on the fixture | `[MEASURED §11]` |
| a recorded cut, with its attestation | record | about 2,700, by arithmetic | §3.3 |
| a chain table's row, for `chat`, `att`, `staging` and `runs` | appended row | under 100, by arithmetic: an integer, the row's key, a 32-byte hash | §3.1 |
| archived model output | replaced row | the row's; how often one is replaced is not measured | §5.4 |
| kept already: a lexical unit of a superseded version | unit | 4,179 on synthetic text, 122 postings a unit | `[MEASURED §11]` |
| kept already: a plane occupancy | row | 734 to 1,084 | `docs/experiments/corpus-stage1-2026-11-07.md:416`, `corpus-measurements-2026-11-07.md:104` |
| kept already: an atom | changed chunk | 2,215, of which the vector 1,536 | `corpus-measurements-2026-11-07.md:103` |
| kept already: a raw object | version | the version's bytes; a transcript's, whole, at each growth | §2.2 |

By arithmetic, not measurement: an instance with a hundred landings a day adds 43 kilobytes a day
to the log, 16 megabytes a year, and thirty recorded cuts a day add 81 kilobytes. A corpus
instance at the ten million items the repository's records plan for
(`docs/experiments/corpus-measurements-2026-11-07.md:94-96`) has a log of about 4 gigabytes for
the first landing of each item.

The rows kept already are what grows: with three versions an item, two thirds of the synthetic
lexical index were superseded versions. `[MEASURED §11]` What one superseded version keeps, by
arithmetic from the rows above for a note of four chunks all of which changed: four lexical
units, four occupancies and four atoms, 28.5 to 29.9 kilobytes of derived rows, and the note's
own bytes as a raw object, against 0.4 kilobytes in the log. At a hundred such landings a day
that is about 2.9 megabytes a day of derived rows, a gigabyte a year, which the instance pays
today whether or not anything reads a past. A transcript is the other large term: it is
retained whole at each growth, 0.79 MB each time for the fixture's session of 2,000 records.
What the snapshot brings is less a cost than the means to stop paying one: a horizon makes it
safe to drop.

### 9.2 The rule, counted in events

A chain can declare two windows, each in positions, and a retention pass runs at a recorded cut.

- **A window for derived rows.** The derived rows of the versions closed at or under the head
  less the window are dropped: lexical units and postings, plane occupancies, and the atoms
  nothing retained holds. No horizon moves. The log and the raw objects stay, so every read of a
  ledger at those cuts is still exact, and a derived row a cut asks for is pending and can be
  derived again (§9.3).
- **A window for the history.** The chain's horizon moves to the later of the horizon in force
  and the head less the window. A `horizon` row is appended first, so the positions under it are
  unserved from that moment; then the derived rows still under it and the raw objects no
  retained row names are dropped, and the log's rows closed at or under it are emptied.

**What a window leaves of a row.** An emptied row keeps `chain`, `seq`, `kind`, `closed_at`,
`commitment` and `hash`, and loses every other field, its key included. No row of the log is
deleted. The rows closed at or under a horizon and the rows still alive there interleave, and a
row at the horizon's position is never closed under it, so with rows deleted there would be no
last row dropped whose hash could seed the rest, and the hashes of the rows kept under the
horizon could not be computed again. With the commitments kept, `verify` runs from the first
row as it does on a chain that was never pruned (§3.2), every certificate keeps verifying, as
after a purge (`verifies_purge`), and a row still alive under the horizon is checked like any
other, by its commitment and by the chain. For the reads an emptied row is a dropped one
(`genRead_prune_gens`): it has no key, so no seek by path finds it, and it needs none, since a
row closed at or under the horizon is the last event of its path at no cut from the horizon on;
its closing stamp keeps it out of the heads at those cuts. `[THEOREM: SNP-9 for the chain,
SNP-10 for the reads; DERIVED for the key]` By arithmetic, not measured: an emptied row is
about 100 bytes, two 32-byte hashes, the kind, three integers and its entry of the closing
index, against the 396 to 434 measured for a whole one.

The window for the history is an exception to the rule that raw objects are kept
(`core/kernel/stores/rawstore.py:1-8`), which only the owner's purge makes today, so it is the
owner's to declare. Its order is the one the stores use for a cache: the horizon is declared
first, so a crash in the middle leaves rows that are no longer served, never a position that is
served and incomplete (the discipline of PLN-4, where a cache is stale only by excess).
`[DERIVED]` The attestation ledger and the version chains are not pruned: they are the audit
record, they are small, and they have no delete. That the ledger keeps every position is also
what §7.1 rests on: `att` is the one chain every landing reads, so a horizon on it would take
the landing chains down with it. The converse is why a pass attestation's reference to a
landing is filtered and not resolved (§3.5): resolved, a history window on one landing chain
would lower `att`, and through it every other landing chain.

A window is counted in events because wall time orders nothing (Law C4): the last ten thousand
landings of a class, not the last ninety days. It is one position a chain, not a number of
versions an identity. Keeping the last `n` versions of each identity would leave no horizon:
which cuts are exact would differ from one identity to the next, with no position to record
them by. The control of §8 is proved for a store pruned at one horizon; that a store pruned per
identity is no better at telling what it lost is the step this note infers. `[INFERENCE,
falsifier SNF-9]`

The default instance declares neither window and keeps everything; by the arithmetic above its
log is megabytes a year and its superseded derived rows about a gigabyte a year at a hundred
landings a day. An instance that must bound its disk declares the first window, which frees
those derived rows and moves no horizon. The second frees, beyond that, only the raw objects
and about three quarters of the bytes of the log's rows of the closed versions, and it is
declared only by the owner (D8). At the cuts a chain no longer serves it also withholds every
pass attestation, dream claim, interpreted row and authored supersession that read a landing of
that chain (§7.1).

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
dn-utility-field: the field's clock is a chain of the cut, `use`, and the field as of a cut is
then exact. Two more things follow.

- **The use log has a natural horizon.** A site left alone returns within `ε` of its baseline after
  `log(c/(lam ε))/lam` ticks (UTL-2, `idle_window`), so a horizon that far behind the head, with the
  field's state at the horizon kept, is exact from the horizon on and loses nothing a reader of the
  present could see. No chain but the chain of records reads the use log, so a cut under its horizon
  lowers that chain, the chain of records with it, and no other (§7.1). `[DERIVED from UTL-2, SNP-3
  and SNP-10]`
- **The field could order what retention drops.** The order a pass drops in is by age: the
  oldest closed versions first. When a window forces a choice among the derived rows of
  superseded versions, the ones whose sites stand at the baseline were not used for anything
  that produced value, and could go first instead. `[HYPOTHESIS: checked by comparing, on the corpus
  instance, how often a pass ordered by the field drops a row a later cut asks for against a
  pass ordered by age; falsifier SNF-9]`

## 10. The laws

Each law is stated so that it becomes a property test when its stage is built, and is proved
now. The Lean names are in `formal/Palace/Snapshot.lean`, the attacks and controls in
`formal/PalaceTest/Snapshot.lean`, by seed. `[THEOREM]` throughout. Each law also says what in
it is a theorem and what holds because the model was built that way, since the second kind
passes to the code only as an obligation of the stage that transcribes it.

- **SNP-1 append invariance.** A read at a cut inside the store, a read between two such cuts and
  every derived view are unchanged by any growth of the store (`readAt_grow`, `readAt_of_extends`,
  `readBetween_grow`, `appendInvariant_view`), also under an erasure and a grant (`visible_grow`,
  `snapshot_grow`, `shown_grow`), for the keyed forms (`stateAt_append`, `genRead_gens_append`), for
  the history of an identity, a retire of it among the growth included (`landingsAt_append`,
  `landingsAt_lives_append`), and for the filtered read of SNP-8 (`kept_grown_iff`). By
  construction: a store is a family of lists, so growth is append and nothing else. That the code's
  stores only append below a cut is what the stage's test checks. Controls: the reader that ignores
  the cut (`Witness.present_not_appendInvariant`); a read at a cut past the head (431, 487, 488);
  the history a seal serves, which a later retire empties (`Witness.seal_empties_history`, 522).
  Attacks 430, 432, 446, 521, 527. The test, at SN-1: over random sequences of catalog writes,
  `read_at(chain, c)` and each path's last event in each chain at `c`, taken after every further
  write, equal the ones taken when `c` was the head, up to the holes a later purge leaves; so does
  `state_at` of every path over a class while the class's chains are the ones it had. A relabel is
  not in the model (below): it moves a whole chain to another class, so a read by class at a past
  cut follows the chain's class now (§6.3), and across one the test compares chain by chain.
- **SNP-2 monotonicity.** The read at an earlier cut is a prefix, chain by chain, of the read at a
  later one, and a cut of a cut is the meet (`readAt_mono`, `mem_readAt_of_le`, `readAt_readAt`,
  `head_readAt`, `visible_mono`), the history of an identity at an earlier cut is a prefix of its
  history at a later one (`landingsAt_mono`), and the filtered read of SNP-8 grows with the cut
  (`Kept.mono`).
  Controls: the read at one cut taken for a prefix of the read at any other (434); a cut of a cut
  taken for the join (500). Attacks 433, 435, 515, and 523, whose second half is
  `landingsAt_mono`'s (its first is SNP-7's). The test, at SN-1: for `a ≤ b`,
  `read_at(chain, a)` is a prefix of `read_at(chain, b)`, and a path's history, chain by chain.
  Across two chains of one class, which only a change of class and a relabel make, `history_at`
  orders the chains by a rule of the prefixes, the ones the path left first, and the read at an
  earlier cut need not be a prefix of the later one; the stage's test pins that rule.
- **SNP-3 composition.** The read at `a` followed by the read between `a` and `b` is the read at
  `b`, and two adjacent reads-between compose (`readAt_append_readBetween`, `readBetween_append`);
  a fold continued from a checkpoint over the delta is the fold of the prefix
  (`foldAt_readBetween`, `stateAt_eq_foldl`); an event, or a pair of events, read at the later cut
  was read at the earlier one or lies in the delta (`mem_readAt_iff`, `pair_readAt`); a key the
  delta does not write has one state at both cuts (`stateAt_eq_of_not_written`). Controls: the
  two cuts in any order (437); two reads-between composed in the other order (502); the delta
  left out (503, 505); a key's state taken for unchanged whatever the delta writes (477).
  Attacks 436, 438, 439, 447, 475, 476. The test, at SN-1: the catalog rebuilt from the state at
  a checkpoint and the delta equals the catalog; at SN-8: the region of §7.4.
- **SNP-4 idempotence.** The read at the head cut is the store, and every reading at it is the
  present's (`readAt_head`, `readAt_of_head_le`, `view_head`, `genRead_gens_length`,
  `snapshot_head`, `shown_head`, `landingsAt_length`, `visible_head`, and for the two seals
  `servedAt_length`, `servedNow_length`, `historyAt_length`). Control: the read at a cut that is not
  the head taken for the store (501). Attack 440. The test, at every stage: a sentence under `as of
  "head"` returns what it returns without.
- **SNP-5 a derived view depends only on the prefixes.** A reader is append invariant exactly
  when it reads only the prefixes, exactly when it is a derived view (`prefixOnly_view`,
  `view_congr`, `appendInvariant_iff_prefixOnly`, `appendInvariant_iff_exists_view`). For keyed
  writes the generational store read at a cut is the state recomputed from the prefix and the
  key's last write inside it, and at most one generation of a key is alive at a cut
  (`genRead_gens`, `stateAt_eq_lastWrite`, `length_filter_selects_le_one`). Controls: the store
  rewritten in place (`Witness.stateOf_forgets`, 444); generations without the closing stamp
  (445). Attacks 441, 442, 443. The test, at SN-1: the three reads of the log agree at every
  position, before and after rows are emptied, and no path has two rows alive.
- **SNP-6 grant restriction.** A narrower grant's snapshot is the restriction of a wider one's;
  a snapshot reads only the chains the grant names and the cut on them; restricting to chains
  commutes with the cut; the grant and the erasure applied together keep both (`snapshot_narrow`,
  `snapshot_congr`, `snapshot_grow`, `restrict_restrict`, `restrict_readAt`, `shown_narrow`). The
  cut read on a set of chains that read from no chain outside it is a function of that set
  (`ResolvesIn.eq_on_of_closed`). By construction: the grant is an argument of the reader and
  not of the cut, so that it is the asker's now is a choice of the model, not a theorem.
  Controls: an event filter applied before the cut (`Witness.filter_before_cut`, 449); positions
  that count hidden events (`Witness.position_channel`, 451); a named chain that reads an
  unnamed one (`Witness.resolution_reads_unnamed`); a narrower grant under a smaller erasure
  (510). Attacks 448, 450, 509. The test, at SN-4: of two grants one under the other, the rows
  the narrower is shown at a cut, and the members of a sentence whose answer is a filter of
  those rows, are the wider one's masked; a sentence that scores or ranks is not tested so
  (§6.3); and landings of a class the grant does not name change neither the rows shown at a
  recorded cut nor the cut shown.
- **SNP-7 erasure dominance.** No erased event is visible at any cut; a larger erasure shows a
  sublist; the store with holes keeps every position; stores that differ only in erased events read
  the same at every cut; a kept row is served only when none of its sources is erased
  (`not_erased_of_mem_visible`, `not_erased_of_mem_shown`, `visible_sublist`, `head_redact`,
  `redact_readAt`, `visible_eq_reduceOption`, `visible_congr`, `erased_invisible`, `mem_serve_iff`,
  `serve_sublist`). A read by key on a chain whose holes keep their keys is the key's last write at
  or under the cut, a hole when that write is erased, on all three reads (`stateAt_holes`,
  `stateAt_holes_of_erased`, `not_erased_of_stateAt_holes`, `genRead_gens_holes`,
  `lastWrite_holes`). Of a retire the library proves both readings, and the design takes the first
  (§6.2, the decision of 2026-11-11). With no seal: the history of an identity at a cut is its
  landings inside the cut, and it holds as its end everything a seal serves
  (`historyAt_suffix_landingsAt`); where a landing at a retired path takes a fresh identity, the
  identity is a function of the events before the landing, the history of the identity a path holds
  at a cut is the path's landings since its last retire, and a retired identity keeps the life it
  had at every cut that holds its retire (`lives_take`, `landingsAt_lives_present`,
  `landingsAt_lives_of_retire`). With a seal, which the design does not apply: a key retired after a
  cut is served at no earlier cut, growth changes a served value only by removing it, and the looser
  seal serves what the stricter one serves (`stateAt_of_servedAt`, `servedAt_append_of_retire`,
  `servedAt_append_of_no_retire`, `servedAt_of_append`, `servedNow_of_servedAt`,
  `servedNow_of_not_live`); the seal covers the key's versions: the history served ends at the value
  served, a retire after the cut empties it, and after a retire it holds only versions landed since,
  at every cut (`getLast?_historyAt`, `historyAt_append_of_retire`, `historyAt_of_retire_inside`,
  `sinceRetire_append_retire`). By construction: these are laws of a reader that reads `visible`,
  `holes` or `landingsAt`, on a chain keyed as `lives` keys it. That every reader of every store in
  the code does, and that the writer names identities so, is SN-3's to transcribe, checked by its
  scan and its tests, and no theorem. Controls: the erasure that deletes rows
  (`Witness.compact_moves`, 455); the hole that loses its key (`Witness.keyless_hole`, 496, 497); an
  identity used again after its retire, whose history holds the retired item's versions
  (`Witness.reused_identity_inherits`, 526, and 513 for the same reading against the seal); a
  retired identity's history taken for empty (528); the state at a cut taken for what the stricter
  seal serves (458); the looser seal taken for a monotone one (`Witness.servedNow_restores`, 474);
  kept rows served without their sources (460). Attacks 452, 453, 454, 456, 457, 459, 473, 495, 511,
  512, 523, 524, 525. The test, at SN-3: after a purge no read at any cut and no scan of the
  instance's files finds the purged words; after a purge of an old version of a live path, the read
  of the path at a cut where that version was the head is a hole, by all three reads; after a retire
  every read at a cut before it, of the identity's value and of its history, returns what it
  returned before the retire; a new note that declares no identity, landed at the path, has an
  identity no earlier row carries, no read of its history, at the head or at any cut, returns a
  version from before the retire, and the retired identity's history at every cut is what it was
  (a note that declares the retired identity takes it back, §6.2, SNF-17); a landing at a path a
  purge emptied takes a fresh identity as well, which `lives` does not model; a landing at a
  retired path repeated after a crash before its key takes the identity the first attempt took.
- **SNP-8 resolution.** Every frontier resolves to exactly one greatest consistent cut under
  it, monotonically; a consistent cut stays consistent as the store grows; a cut consistent for
  a recorded bound on the references is consistent for the true ones (`exists_resolves`,
  `Resolves.unique`, `Resolves.mono`, `resolves_self`, `Consistent.of_grown`,
  `Consistent.of_bound`). The consistent cuts are CLK-2's cuts among the frontier cuts
  (`consistent_iff_isCut`), so their closure under meet and join is CLK-2, cited and not
  claimed here (`Consistent.inf`, `Consistent.sup` and `consistentCuts`, derived from
  `Clock.IsCut.frontier_inf` and `Clock.IsCut.frontier_sup`; `consistent_zero` for the bottom).
  The references the resolver does not follow are kept by a filter of the read: a row is
  withheld when it fails its own test, when a source of it lies outside the cut or when a
  source of it is withheld. The filtered read holds the sources of its rows, is the greatest
  such set inside the cut, is the prefix at a cut consistent for every reference, and never
  withholds a row whose references are all resolved (`Kept.source`, `Kept.passes`,
  `kept_of_closed`, `kept_iff_of_consistent`, `kept_of_resolved`, on `Withheld.anti` and
  `Withheld.of_grown`). By construction: which references are resolved and which filtered is
  the design's reading of the writers (§3.5), and that every reader of `att`, `runs`, the
  `interp` chains, `decl` and the dispositions at a cut goes through the filter is the stages'
  to transcribe. Controls: a
  frontier taken for a cut (462); a consistent cut advanced by one position (464); resolution
  taken to fall as the frontier rises (490); a pass attestation's reference resolved, which
  lowers a landing chain that serves its position (`Witness.pass_drags`); the prefix read where
  that reference is filtered, which is not closed (`Witness.pass_withheld`, 518); the filter
  without its closure (517). Attacks 461, 463, 465, 514, 516. The test, at SN-2: the resolver
  against enumeration on small stores, and no recorded cut with a resolved reference crossing
  it; at SN-5 and SN-6: at every cut, no row served whose source, by any reference of §3.5, is
  outside the cut or withheld, and at the head no row withheld that the present read returns,
  but a witness's attestation of a commit the sensor has not read yet (§3.5).
- **SNP-9 certified cuts.** A certificate verifies on every extension of the store; under a
  collision-free digest two stores that verify one certificate have the same prefix of every
  digested chain at its cut and the same derived views of it; a certificate extends over the
  delta; the meet and the join are certified from the two certificates; an erasure that keeps
  commitments keeps every certificate, and a certificate attests no erasure; under a binding
  commitment a certificate over commitments pins the events, so two stores that verify it read
  the same store with holes under one erasure, and show the same under one grant and one
  erasure (`verifies_certify`, `verifies_certify_of_extends`, `eq_of_chainDigest_eq`,
  `Verifies.readAt_eq`, `Verifies.view_eq`, `certify_digest_readBetween`, `certify_inf`,
  `certify_sup`, `commitments_purge`, `verifies_purge`, `verifies_purge_iff`,
  `contents_purge_committed`, `Verifies.readAt_eq_of_committed`, `Verifies.contents_eq`,
  `Verifies.shown_eq`). By hypothesis, not by theorem: the digest is collision free and the
  commitment injective. Controls: a digest with collisions (`Witness.digest_collides`, 468); a
  digest over contents, which an erasure changes (472); a seal written after the cut
  (`Witness.seal_not_certified`); a renamed chain (`Witness.rename_breaks_certificate`); the
  certificate of a cut past the head (489); the meet certified from the later digest (504).
  Attacks 466, 467, 469, 470, 471. The test, at SN-2: a certificate verifies after any further
  writes, on a copy of the files and after a purge, and fails when one row under the cut is
  edited or a chain is given another id.
- **SNP-10 the horizon.** A generational store pruned at a horizon is exact at every cut from the
  horizon on and never wrong under it; horizons compose to the later one; pruning commutes with a
  later landing (`genRead_prune`, `genRead_prune_gens`, `stateAt_of_genRead_prune`, `prune_prune`,
  `prune_landGen`). Among the positions the chains serve, every frontier resolves to exactly one
  greatest consistent cut, which never passes the cut asked and rises with the frontier and with
  served positions that grow (`exists_resolvesIn`, `ResolvesIn.unique`, `ResolvesIn.mono`,
  `ResolvesIn.le_resolves`, `resolvesIn_univ`, `resolvesIn_self`). A chain that no other chain reads
  is lowered alone, and so is every such chain at once (`Consistent.update_of_unread`,
  `resolvesIn_update_of_unread`, `resolvesIn_of_unread`); a chain that reads the lowered chains, and
  that nothing but itself reads, follows them and takes nothing with it (`resolvesIn_of_followed`).
  Controls: the pruned store read under its horizon, which cannot tell a lost key from one never
  written (`Witness.prune_forgets`, `Witness.prune_indistinct`, 480); a record on a chain that
  content reads (`Witness.record_drags`); a chain of records taken to be read as recorded when a
  chain it certifies is lowered (`Witness.record_follows`, 520); a chain that others read lowered
  alone (499); served positions that shrink (`Witness.served_set_shrinks`, 507); a frontier lowered
  to the served positions without the descent (483); the floor and the descent each run once, in
  either order (493, 494); pruning at the earlier of two horizons (491); the cut read taken to reach
  the floor, or the resolution of the frontier (506, 508). Attacks 478, 479, 481, 482, 484, 485,
  486, 492, 498, 519. The test, at SN-2: the served resolver against enumeration; at SN-4: the cut
  read is under the cut asked on every chain, and at a recorded cut it differs from the record only
  on the chains that could not serve and on the chain of records; at SN-7: every read at a cut from
  the horizon on is the same before and after a retention pass.

What the model leaves out, said plainly. A chain is a list and a store a family of lists: one writer
is assumed, and nothing is said of two. Events are opaque, and so is the stores' SQL. The set of
chain keys is fixed: a relabel is not in the model, which is why a chain has an id that a relabel
does not change (§3.1). The hash's collision freedom and the commitment's binding are hypotheses of
SNP-9 (`CollisionFree`, an injective `commit`), not theorems about SHA-256. The `horizon` event is
not in the model of a keyed chain, and the owner's gate on a history window is the code's. The fresh
identity is in the model as a count of a path's retires (`lives`); the name the code gives it, an
identity a note declares, a rename and a life closed by a purge's hole are not (§6.2). There is no
single reader in the model that applies the cut's resolution, the grant, the erasure and the
history of an identity together:
`shown` composes the grant and the erasure over one read, the history is stated on a keyed chain,
and the resolution on cuts; the sentence's reader applies the resolution first, then `shown`, and no
seal (§6.2), and that order is the code's to transcribe. The row filter of §3.5 is in the model as
`Kept`, with the reads-from relation and each row's own test as parameters; what the code's rows
read is §3.5's reading of the writers and no theorem, and the bound a pass attestation records is
argued there, not proved. The filtered read is a derived view, not a prefix. A repository history
with merges is covered by CLK-2's down-sets and not by the chain model (§3.1). The resolver, the
descent and its alternation with the floor, is attacked, not proved.

## 11. Measurements

Every figure measured for the design, before SN-1 was built, is from a synthetic fixture: a
temporary directory or in-memory stores built by the probe, the test suite's throwaway palace for
the purge, and nothing of any instance; SN-1's figures, below the table, are of the build on a
copy of the corpus instance's catalog. The other figures the note uses are the repository's own
records of an instance, cited where they stand and graded `[ESTABLISHED]`: the attestation
ledger's bytes a row, the job rate, the citation store's rows and bytes, the plane's bytes an
occupancy and the curated table's bytes an atom
(`docs/experiments/corpus-measurements-2026-11-07.md:94-107`,
`docs/experiments/corpus-stage1-2026-11-07.md:416`, `core/reference_view.py:15-16`). Figures
given as arithmetic are marked so where they stand.

The probes are short scripts and are not in the repository: the design's pull request changed
no Python, and the newest notes keep a harness under `eval/` with a record under
`docs/experiments/`. So these figures cannot be repeated from the tree as it stands. Each stage
of §12 commits the harness of what it builds with its record: SN-1 the log's size and reads
(done: `eval/landing_log_bench.py`, measured on the corpus's catalog, below the table), SN-3 the
purge probe as a test, SN-5 the causal probes. The table gives each fixture closely
enough to be built again.

One machine (Apple M2 Pro, 12 cores, 32 GB, macOS 27.0) with other work running, the load
average between 2.4 and 5; Python 3.15.2, SQLite 3.54.1, LanceDB 0.33.0; the code at `e3e3ee47`.
The timings are medians with their ranges. Each probe was run at least twice, and a range across
the runs is given where they differed. `[MEASURED]`

| probe | fixture | result |
|---|---|---|
| the landing log | the two tables of §3.2 with their three indexes, in one SQLite file; one chain, 100,000 paths of 37 characters with titles under twelve, ten landings a path in a shuffled order, one transaction, every row keyed, committed to and hashed and the path's previous row stamped; built twice, with every identity its path and with every identity a nine-character id | 1,000,000 rows in 434.3 MB where the identity is the path: 434 bytes a row (table 374, key index 47, closing index 13, identity index empty); 396.5 MB where it is an id: 396 bytes a row (table 315, key index 47, identity index 21, closing index 13); 35,000 to 42,000 rows a second written |
| its reads | the same files, 200 repetitions a point read, 5 a scan | one path at the middle cut 3 µs through the key index, and 1.4 to 1.5 µs for the keyed hash of its path; a path's seven versions at the middle cut 9 µs through the key index and 49 to 57 ms when the planner took the primary key; 1,000 positions 0.64 to 0.69 ms; every head 52 to 56 ms at a cut a tenth of the way in (65,103 rows), 147 to 166 ms at the middle cut (99,916 rows) and 240 to 275 ms at and near the head (100,000 rows); the chain's hash recomputed from the first row in 0.71 to 0.76 s; the stored hash at a position read in 3 µs |
| a hole in the log | the same files: the fifth of one path's ten rows emptied as §6.1 says, its key kept | the seek by key at the last cut before the path's next landing returned the emptied row, with no digest |
| a kept version in the lexical index | `LexicalStore` on a temporary file; 500 items of 4 chunks in 3 versions, each chunk 171 words drawn from a vocabulary of 20,000 with frequencies falling as the inverse of the rank | 6,000 units held, 2,000 of them current; 734,409 postings, 122 a unit; 25.1 MB, 4,179 bytes a unit; superseded share 0.67 |
| what a purge leaves | the test suite's throwaway palace (`tests/fixtures/ingress.py:73`), lazy, with its fake embedder: two notes landed and drained, one edited and drained, then deleted from the vault, then both its digests purged (`purge_raw`); a control note never purged, found at every step | gone: the raw objects, the plane's occupancies and supersession entries, the catalog rows. Left: the words in the vector table read at versions 2 to 9 and 3 to 7 of its 10; the lexical units, postings, title and version records; both version rows; one attestation a digest |
| after the purge | the same palace: the vector table compacted with no retention; every SQLite file checkpointed, then vacuumed; a new note landed at the path | the compaction left 1 dataset version and no purged word in the table's files; the deleted catalog and plane rows' path and digest were still in the files' bytes after the checkpoint and gone after the vacuum; the plane's supersession log held position 1 for the path again, and the version chain appended number 3 |
| the order of two jobs | in-memory stores; one session with a commit event; the ledger holds the commit before the integrator's first pass, or gains it after | 1 edge against 0, and still 0 after a second pass, the session being skipped as unchanged |
| the events of a prefix | a transcript of four records: a prompt, a reply with a `git commit` call, the call's result with the sha, a reply | the prefix that ends before the result gives the commit event an empty reference; the whole gives the sha; the two longer prefixes agree with the whole |
| re-deriving a session | a synthetic transcript of 2,000 records, 0.79 MB, 7 repetitions | 6.0 to 6.1 ms median (5.7 to 7.2) |
| what `as of` accepts | the unit tests' store fakes, with two readings in the reference store and with none; the real reference store on an empty temporary file; git read-only on the checkout | with readings held: `as of "HEAD"` and `as of "2026-11-01"` refused, a sha prefix accepted. With none held (`latest_commit()` is `None` on the empty store): `as of "HEAD"`, the date and an unknown name all answered, the universe's cut the string asked |
| `read` under `as of` | the same fakes, one reading at a commit of the checkout fourteen back and one at a sha of forty `d`s that git does not hold | at the commit git holds: that commit's blob and not the head's, under a note saying that `read` read the present, the hit carrying no commit; at the sha git does not hold: `HEAD`'s blob, the same note, the same hit |
| row numbering | a table keyed by text, five rows, in a temporary file | after the last row was deleted the next insert was numbered 5 again; a vacuum after a delete in the middle kept the numbers |
| an identity after a rename | an in-memory `VaultCatalog` at `f969904e`: a path recorded, a second path recorded with the first one's identity, the first tombstoned, then the first recorded again with no identity given, as the writer records a path that has a row (`core/ingest/writer.py:372`, `:409`) | the identity then has two active paths, the old one and the new one; added on 2026-11-11 for §2.3's item 8 |

Not measured for the design: anything on an instance's own stores, which SN-1 measured for the
log alone (below); the size of a recorded cut, of a chain table's row and of a row of the log that
a window emptied, which are arithmetic; how often a row of model output is replaced; the lexical
statistics computed from a mask at a corpus's size; the causal fiber recomputed over a real
instance's sessions, cold or warm; a vector search with superseded rows joined to the heads at a
cut; the reads of the chat log and the attestation ledger through their chain tables; a retention
pass. Each is the measurement of the stage that builds it.

**Measured at SN-1, on a copy of the corpus instance's catalog (added 2026-11-11).** The log as
built, by its committed harness (`eval/landing_log_bench.py`), on two copy-on-write clones of the
corpus instance's catalog, 400,274 rows all `observed` and active; the record is
`docs/experiments/landing-log-2026-11-11.md`, every figure in its JSON. The same machine, with
Python 3.15.2 and SQLite 3.54.1 and other work running. `[MEASURED]`

| probe | result |
|---|---|
| the migration: the tables, their indexes and the genesis, one chain of 400,276 rows | 6.71 to 6.73 s; the file 162.7 MB before and 334.1 MB after, 429 bytes a row (the table 381, the key index 47, the other two empty); the fold of the log equal to the catalog row by row |
| `verify`, every commitment and hash from the first row | 3.07 to 3.08 s |
| the reads | `state_at` of one path at the middle cut 13.7 to 16.5 µs, 1.6 to 1.7 of them the keyed hash; `history_at` at the head 15.5 to 18.9 µs; `read_at` and `read_between` of 1,000 positions 3.2 to 3.4 ms, the rows built in Python; `heads_at` 0.15 s at a tenth, 0.79 s at the middle and 1.62 s at the head, of which the walk in SQL is 6 ms, 29 to 30 ms and 59 to 60 ms |
| every head of a smaller chain, one class, landed through `record` | 30,000 paths 111 to 112 ms (the walk 4 to 5 ms); 100,000 paths 374 to 376 ms (the walk 15 ms): 3.5 to 3.6 µs a head returned beyond the walk |
| a key's write in a batch of 10,000: as built, with the log's rows switched off, and as `record` made it before SN-1 | a new path 55.7 to 57.4 µs, 10.4 to 10.5 and 4.6 to 4.7; a new version of a held path 119.1 to 120.3, 45.0 to 46.0 and 34.5 to 34.7: SN-1 adds 51 to 53 and 84 to 86 µs, the log's rows 45 to 47 and 74 of them, 0.16 to 0.28 percent of a lazy landing's 31 ms (`docs/experiments/two-phase-ingestion-2026-11-07.md`) |

The load average was between 2.7 and 3.9. Three findings came out of it. The update that writes a
row's closing stamp took the primary key and walked the chain, about 40 ms a landing at this size,
until it named the key index as the seeks do (§4.1); a test now asks the plan of every statement
by path to name it. The savepoint each write in a batch takes, added after review so that a failed
write leaves neither of its rows (§12, SN-1), kept its journal in a temporary file and doubled a
key's write, 105 to 108 µs for a new path in two runs; the catalog's connection now keeps its
temporary store in memory, where the savepoint costs about 6 µs. And every head costs what
building the answer costs: the walk is 0.14 to 0.15 µs an event, against §4.2's quarter of a
microsecond on the fixture, but each head returned costs 3.5 to 3.9 µs more, in Python, so the read
from the log alone passes a tenth of a second near 27,000 heads, a chain of 30,002 events taking
0.11 s. That is SNF-6's first condition, met at SN-1, and kept heads do not remove it: a kept head
at a recorded cut shortens the walk, not the building of the answer (§4.2).

## 12. The build order

Nothing is built by this note. What the merge licenses is decision D12. The stages, each a pull
request against main with its tests and its rollback, each transcribing its laws and
property-testing the transcription against the Lean statements; the laws a stage relies on enter
`docs/LAWS.md` and `formal/Spec/` with it, as design theorems do when code comes to rely on them.

- **SN-1 the landing log.** Built on 2026-11-11: `core/stores/landings.py` and the catalog's six
  methods, `tests/property/test_landing_log.py`, family XVI of `docs/LAWS.md` with
  `formal/Spec/Snapshot.lean`, and the measurements of §11; the three departures from §3.2 are
  marked there, and the landing-log secret is a deploy's precondition (`docs/runbook.md` §0).
  What is built:
  - The tables `landing_chains` and `landings` of §3.2 with their three indexes, in the
    catalog's file, created by the catalog's own migration after it fills `doc_id`
    (`core/stores/catalog.py:77-92`), and the genesis of §3.2 for each class the catalog holds.
  - The log written inside `record`, `tombstone`, `relabel_provenance`,
    `migrate_rekey_doc_id`, `remove` and `remove_digest`, in the transaction of the row each
    writes, so that a `deferred()` batch (`catalog.py:125-138`) carries its log rows. `record`
    gains a `version` argument (`None` where the place keeps no chain), passed at
    `writer.py:419`, `:433` and `sync.py:201`. `att_head` is `NULL` at this stage.
    `relabel_provenance` rewrites the label in `landing_chains` and no row of `landings`.
    `remove` and `remove_digest` empty the log's rows of the path or of the digest as §6.1
    says, the key kept, so the purge's effect on the log is this stage's and not SN-3's. As
    built, after review: `remove_digest` also empties the other rows of a path none of whose
    versions keeps its content (§6.1), and each write in a batch is a savepoint, so a write that
    fails leaves neither of its rows when the batch's caller catches the error and goes on.
  - The reads, on `VaultCatalog`: `chains(class)`; `head(chain)`; `read_at(chain, c)`, the rows
    with `seq ≤ c` in order; `state_at(class, path, c)`, the path's last event at or under the
    cut over the class's chains, which is a `store`, a `retire` or `move`, a hole, or nothing (as
    built, a `leave` too, when the path's present is in a chain of another class at the cut);
    `history_at(class, path, c)`, its `store` rows at or under the cut; `heads_at(class, c)`,
    the `store` rows alive at the cut over the class's chains, a hole returned as a hole with
    its position and no name; `read_between(chain, a, b)`; and `verify(chain)`, which recomputes
    the hashes from the first row and the commitment of every row that still has its salt (as
    built, it also fails a row without its salt that keeps any content a purge empties). The
    statements of `state_at` and `history_at` name `landings_path`. Here `c` is a position of a
    chain, or for a class one position a chain.
  - Nothing reads them yet, and no reader's behaviour changes.

  As built, that last line holds once the log has its genesis and not before it. The genesis is
  written by the migration, at the first open of a catalog that has rows and no log, and every
  process that opens the catalog runs the migration, a reader's included (the MCP server, the
  sentence's executor, the spine, the query modes and the launcher open it:
  `agents/ambassador/mcp.py:74`, `core/sentence/execute.py:342`, `core/temporal/spine.py:373`,
  `core/query.py:428`, `ops/lifecycle/launcher.py:1625`). So the first process to open the catalog
  after the deploy writes the genesis: it needs the secret, raising `LandingLogKeyMissing` without
  it, and it holds the write lock for the genesis, about six seconds on the corpus's catalog, while
  any other opener waits up to two minutes. After the genesis a reader needs no secret and opens
  as fast as before; a writer needs it for every write that appends a row (§3.2). So §3.2's rule,
  that the genesis refuses loudly without the secret, and the line above, that no reader's
  behaviour changes, cannot both hold while every open runs the migration, and which gives way is
  the owner's to decide before SN-1 is deployed:
  the genesis written by a writer's first write, or by an owner-run migration, with an open that
  lacks the secret skipping it; or SN-1 stated as changing what the first open needs, with every
  process that may open the catalog first run with the secret in its environment. Under either,
  every writer needs the secret, the daemon first, and a deploy installs a committed plist that
  changed (`ops/lifecycle/launcher.py:1071-1078`); so the two plists
  (`ops/lifecycle/com.mind-palace.palace.plist`, its daemon twin) run the daemon under
  `scripts/run_with_secrets.sh`, which carries the item, the twin, run as `ouroboros`, reading
  it from that account's keychain. The runbook's §0 makes the item a precondition of the deploy.

  Tests, in `tests/property/test_landing_log.py`: SNP-1 to SNP-5 as §10 states them, over
  random sequences of catalog writes that include retires, renames, relabels and purges; the
  catalog equals the fold of the log after every write, a purge included; a `record` that
  changes nothing, and a store the UNCHANGED check skips, write no row; a transaction killed
  between the two rows leaves neither; the genesis equals the catalog, tombstoned paths
  included, and is followed by a horizon; after a relabel into a class that has rows, no row of
  the log changed and every chain verifies; after a purge of an old version of a live path the
  three reads return a hole at a cut where it was the head; `verify` fails on an edited row.

  The ledger: `docs/LAWS.md` gains a family XVI, the temporal snapshot, with rows SNP-1 to
  SNP-5, each with its statement as §10 gives it, the reads above as its code, the tests above,
  and the Lean declarations §10 lists for it. `formal/Spec/Snapshot.lean` restates those
  declarations over `Palace/Snapshot/Defs.lean` with their proofs left out, and
  `formal/comparator.json` gains their names, as the last family added did.

  Rollback: the tables are additive and unread, so dropping them restores the file; a build
  that stops writing them and resumes later appends a `horizon`. As built, the resumption is a
  new genesis on the dropped tables, which ends at its `horizon`: a build without the log that
  wrote the catalog while the tables stayed would leave the log behind the catalog, and nothing
  detects that yet, so the rollback drops them (`docs/runbook.md` §0). The new genesis numbers
  its chains and positions from 1 again, so a chain id and a position are given once only while
  the tables stand; nothing at SN-1 relies on more, and SN-3's fresh identity, which is named by
  a position, must (§6.2).
- **SN-2 cuts.** The chain tables, each with its running hash and its genesis followed by a horizon,
  for `chat`, `att`, `staging` and `runs`; `att_head` filled from then on; on the chain-table row of
  a pass attestation and of a run, the landing chains that held its inputs and the head of each, and
  on the row of a witness's attestation of a commit, the commit (§3.5); `verdicts` among the chains
  a record names, by the position it has; the extractor's version and the projection's position on
  `att` stamped on new citation edges, the edges already held stamped with the genesis; the `cuts`
  table of §3.3, a record at a trough that moved and on command, and an attestor method that builds
  and signs an attestation without appending it; the four names, with every name that resolves to
  nothing refused; the resolver of §3.5, the floor and the descent alternated, the descent reading
  the three bounds of the resolved references and no position recorded for the filter; a command,
  `mind-palace cut` with `record`, `list` and `verify`. Tests: SNP-8 and SNP-9 as stated; the served
  resolver against enumeration; a record refused inside a job, and refused with jobs queued and no
  daemon; a cut read below a record on one chain reading the chain of records at its last record
  under it; a record taken after a witness attested a commit the sensor has not read is consistent,
  and lowers no chain. SNP-8 enters the ledger as resolution, with its closure cited to CLK-2's row,
  and SNP-9 with it. Rollback: additive tables and columns; the names fall back to today's.
- **SN-3 the two forms of removal.** The deep form's reach: a purge removes the lexical units,
  nulls the version rows' digests, removes the relation edges and artifacts that name the
  digest, opens the curated store, nulls the support and text of the dream claims and the
  digest and payload of the staging rows, removes the claim ops on a removed artifact, the
  authored supersessions that name the digest and the rejected requests that hold the text,
  compacts both vector tables and writes its attestation, which names the positions it emptied
  (§6.1); decision D9's form for the attestation ledger. The shallow form's identity: a `store`
  at a path with no open row is a first bind, and where it neither declares an identity nor
  carries one from a vanished path, and the log holds an event of the path, it takes the fresh
  identity `<path>#<chain>.<seq>` of §6.2, in both lanes that bind one
  (`core/ingest/writer.py:372`, `:409`; `core/ingest/sync.py:140-201`); the migration's count of
  the identities that already run across a retire. No seal and no `unseal` are built.

  The fresh identity is this stage's for three reasons. It changes what the writer admits and
  what `trace` returns at the head, and D12 licenses a change of behaviour with its own pull
  request, where SN-1 adds tables and changes no answer any read gives (what it does change,
  what a process needs at the first open and to write, is SN-1's item as built). It needs the
  log: the name is the
  position of the path's last event, which exists from SN-1. And it has to be in force before
  any history is read at a cut, which is SN-4, so that no reader of a history is built on
  identities that inherit; SN-3 is the stage already ordered before SN-4 for removal, and with
  it the stage holds both forms the owner's decision names.

  It lands before SN-4, since SN-4 is the first stage that reads a superseded version. Tests:
  SNP-7 as stated, with the purge probe of §11 turned into a test that must find nothing; the
  two-paths probe of §11 turned into a test that finds one path an identity. Rollback: a purge
  has none by its nature; the identity rule is one branch of the first bind, and with it off a
  landing at a retired path continues the path's identity as today, the identities already
  given staying as they are.
- **SN-4 the notes at a cut.** The universe's nodes from `heads_at`, with kept heads for a chain
  over the size §4.2 gives; `read` from the raw object the log names, and refused for a
  repository path whose commit git lacks; the vectors and the lexical units joined to the heads;
  the pending rule at a cut; the curated rows that landed through the catalog, and the count of
  those that did not; the citation reading as projected at or under the cut; `trace` at a cut;
  the cut read and its note (§7.1), which retires the note that says a verb read the present;
  the commit on a `read` hit. Tests: `as of "head"` against no `as of` over the query battery
  (`eval/query_battery.py`); a sentence at a recorded cut asked before and after unrelated
  landings and after a re-projection; SNP-6 with two grants, as §10 states it; the cut read
  under the cut asked, and equal to the record but for the chains that could not serve and the
  chain of records. Rollback: one configuration switch under `[query]`, off being today's behaviour.
- **SN-5 the causal fiber at a cut.** The recomputation of §5.5 with its memo; edges named by
  session, order and endpoint; the transcript integrator's checkpoint a cut on `chat` and `repo`;
  `witness` at a cut, the ledger read by sequence number with the pass attestations and the
  witness's attestations of a commit filtered (§3.5).
  Tests: the two job orders giving one result; the prefix that ends before a result; the stored rows
  at the head equal to the recomputation; a pass attestation withheld at a cut that lacks a landing
  it read, the attestations after it served, and none withheld at the head; a witness's attestation
  withheld at a cut whose commit is an ancestor of its own, and served from its commit on.
  Rollback: the stored rows stay the head's cache.
- **SN-6 model output by generation.** A sequence number, a running hash and a history table
  for the interpreted artifacts and the interpreted relation edges, a chain each; a sequence
  number and a running hash for the claim ops, which need no history table since a row is
  keyed by its whole content and none is replaced; for the authored supersessions a chain-table
  row at every declaration, with the note, the log positions of the two notes and a salted
  commitment the hash runs over, since a second declaration of a pair replaces the store's row
  (§5.4); the running hash of `verdicts`; the authored relations recomputed at a cut; `relate`
  at a cut; a kept row served only with its sources inside the cut and its attestation kept
  there, a claim op only with the artifacts it names, a dream claim only with its run, a
  supersession only with both its notes, a disposition at the cut's position on `verdicts`
  (§3.5, §5.4). Tests: SNP-5 on random sequences of writes and replacements; `mem_serve_iff`'s
  test; SNP-8's filter as §10 states it; an artifact replaced over the same titles served with
  the sources each generation had; a pair declared twice read at a cut between the two
  declarations with the first note, the chain verifying after the second; a supersession
  withheld at a cut that holds one of its notes and not the other, so that the active
  projection at that cut marks nothing historical by it. Rollback: additive columns and tables.
- **SN-7 retention.** The two windows a chain in the instance's configuration; the pass of
  §9.2; the `horizon` row; the horizon in the answers. Tests: SNP-10 as stated; a pass killed at
  each step leaving no served position incomplete; a derived row dropped under the first window
  reported pending and derived again; a cut asked under a landing chain's new horizon read with
  every other landing chain, `att` and `repo` as recorded, the chain of records at its last
  record under the cut read, and the rows that read a landing of the lowered chain withheld;
  after a pass, `verify` of the chain passing from its first row and a certificate taken before
  the pass still verifying. Rollback: none for dropped rows by their nature; nothing runs
  unless a window is declared.
- **SN-8 the delta.** `changed between` and `changed since` (§7.4); the integrator interface
  below. Tests: the region's union law, and equal reads at both cuts for an identity outside it.
  Rollback: the region is a new production of the grammar and the interface a new module, so
  both are withdrawn by removing them; no store changes.

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

Each with the recommendation and what the alternative costs. Where a cost has a figure it is
given. D3, D4, D6, D11 and D12 are choices of behaviour: they have no cost in bytes or time to
give, and what each alternative costs is the answers it changes, which the entry states.

1. **D1, where the catalog's past is kept.** Recommended: the landing log in the catalog's file,
   written by the catalog (§3.2), at about 0.4 kilobytes a landing on the fixture. The
   alternatives: version chains for every place, which is a second file, so the key and its
   history are two transactions, one more commit a landing, and ING-7's order gains a stage, and
   whose chains are per document, so a cut is a pair an item; or the plane's supersession log,
   which an instance with no plane lacks, which records the drain's order under lazy embedding,
   and which gives a position again after a purge.
2. **D2, the grain of a cut.** Recommended: one position a chain, the landing chains each of one
   provenance class (§3.1): about a dozen integers. The alternatives: a position a document,
   which today's spine has only for the one place that keeps version chains and which, extended
   to every place, is ten million pairs a cut at the scale the corpus records plan for; or one
   landing chain for every class, which saves a few integers a cut and tells a narrower reader,
   by its positions, how many landings the classes it cannot read made.
3. **D3, what a retire does to the past. Decided by the owner on 2026-11-11, against the
   recommendation.** The decision: removal has two forms. A retire is the shallow one: the item
   leaves the present, its history stays readable at the cuts where it existed, no seal is
   applied, and a note written later at the same path takes a fresh identity so that it does
   not inherit the retired note's versions. The purge of §6.1 is the deep one: a hole at every
   cut, with every derived answer at a past cut becoming what it is without the item; the
   change that makes to the past answers of the item's neighbourhood is intended, and what
   survives is the record that a purge happened, not the content (§6.2). What had been
   recommended: the stricter seal, by identity, over the value and the versions, lifted only by
   an owner's `unseal`; its alternative was the looser seal, which brings a deleted note's
   versions back at earlier cuts when another note is written at its path. What the decision
   costs: a note that is retired and returns has two identities unless it declares its own, so
   its history at the head starts at its return (SN-l, SNF-10); a delete withdraws nothing
   from the past, and only a purge does; and the identities bound before the rule keep what
   they inherited. What it saves: the `unseal` event and its gate, a read of the present in
   every keyed read at a cut, and the one thing about a retire that a certificate did not pin
   (§3.6). The failure the seal was recommended for, a deleted note's versions standing under
   a new note, is removed by the fresh identity at the first bind, at the head as at a cut.
4. **D4, a store that cannot serve the cut asked.** Recommended: read at the greatest consistent
   cut among the positions the stores serve, and name it (§7.1). With the recorded cuts on a
   chain of their own (D13), and the rows that read a landing without being its record filtered
   and not resolved (§3.5), that lowers only the chains that could not serve and the chain of
   records; the rows that read what was lowered are withheld and counted in the answer's note.
   The alternatives:
   refuse the sentence, after which `as of` answers nothing that touches a store without a past
   until SN-6, and nothing under a horizon ever; or keep today's behaviour, which answers from
   after the cut and changes as the store grows.
5. **D5, the embedder's and the tokenizer's identity at a cut.** Recommended: the present's
   (§5.2, §5.3). The alternative, the identity in force when the content landed, needs every
   identity's vectors kept, a vector table an identity (1,536 bytes an atom at the present
   dimension and precision), in a plane that refuses a second identity today.
6. **D6, the names `as of` takes.** Recommended: `head`, a recorded cut's id, a commit, a date
   (§3.4). The alternatives: commits only, as today, which leaves no name for a moment between
   two commits and none on an instance with no repository; or dates without the cut read in the
   answer, which gives an answer that cannot be asked again.
7. **D7, between two cuts.** Recommended: the region `changed between` and `changed since`
   (§7.4), one range read of the log. The alternatives: nothing, and every integrator and every
   question about change is a hand-written read; or a general two-cut adjective, which is a
   second universe a sentence and a pair sort, and which dn-graph-dynamics designs already as
   GD-4. Neither alternative is sized here.
8. **D8, retention.** Recommended: no window on the default instance; where the disk is bounded, a
   window for derived rows, which moves no horizon and frees what a superseded version mostly costs,
   about 29 kilobytes of derived rows for a note of four chunks by §9.1's arithmetic; and a window
   for the history only when the owner declares one, since it drops raw objects (§9.2), and at the
   cuts under the new horizon withholds every pass attestation, dream claim, interpreted row and
   authored supersession that read a landing of the chain. The alternatives: a horizon everywhere,
   which over the first window frees only a closed version's raw bytes and about 0.3 of its 0.4
   kilobytes of log, by arithmetic, and loses the default instance's history for it; that trade is
   worth making only where raw objects are large, as a transcript retained whole at each growth is
   (0.79 MB a growth on the fixture). Or the last `n` versions an identity, which leaves no horizon
   to name.
9. **D9, the attestation ledger under a purge.** It still names a purged digest (§6.1), against
   the plane's rule that no content hash of purged text is kept. Recommended: from SN-3 on, an
   attestation names a content digest by a salted commitment, the salt held in a side table of
   the attestation store keyed by a keyed hash of the digest, written in the transaction of the
   first attestation that names the digest. The landing order does not change: the attestation
   still comes before the key, a re-run after a crash finds the salt by the digest and attests
   nothing twice, and the landing still reads from its attestation. A purge deletes the side
   row, after which no attestation can be tested against a guess of the content. It costs a
   side row a distinct digest, of the order of a hundred bytes; a lookup an attestation; every
   reader that matches an attestation's hashes against a digest going through the side table
   (`core/attestation/attestor.py:59-69`, `core/ingest/landing.py:60-75`); and an outside
   verifier needing the salt to check an attestation against bytes. The rows written before
   stay, and a purge lists their ids as what it could not reach. The alternatives. Name the
   landing log's commitment in the attestation: the log's row, its salt and its position are
   written in the key's transaction, last, and its commitment covers `att_head`, so either the
   attestation moves after the key, which reverses the reference of §3.5 and leaves a landed
   item unattested after a crash between the two, or the salt and the position are fixed before
   the attestation, which is a write before ING-7's first stage. Rewrite the ledger at a purge,
   which breaks its construction as append-only and every id computed from a row. Or leave it,
   and a digest of purged bytes stays.
10. **D10, model output.** Recommended: the interpreted artifacts and the interpreted relation
    edges kept by generation (§5.4). The alternative, outside the snapshot, costs nothing and
    means `relate` over interpreted edges and the dreams are never read at a past cut. The
    relations a note declares are not part of this decision: they are recomputed at a cut
    either way.
11. **D11, the read-only principal at a cut.** Recommended: the present's list, applied to the
    edges inside the cut (§6.4). The alternative, the list taken at the cut's tree, shows at a
    past cut a file that was tracked then and is not now, which the head withholds, and makes the
    grant a function of the cut.
12. **D12, what the merge licenses.** Recommended: SN-1 and SN-2. SN-1 adds tables and changes no
    reader's answer; as built it changes what a process needs at the first open of a catalog and
    to write it, the secret, which §12 states and leaves to the owner. SN-2 adds tables, columns
    and names; the one behaviour it changes is that a name which
    resolves to nothing is refused on an instance whose reference store is empty, where today it is
    answered (§2.1). SN-3 to SN-8 change an erasure, the identity a landing takes, the universe and
    what an instance keeps, and each is licensed with its own pull request. The alternative, all
    eight at once, saves the owner seven decisions and reviews the purge, the universe and retention
    together.
13. **D13, where a recorded cut is kept.** Recommended: a chain of its own that no other chain
    reads, its attestation in its own row (§3.3). That chain is read at its last record under
    the cut read, and takes nothing with it. The alternative, a row of the attestation ledger,
    is one table fewer and signs a record where every other attestation is signed; but every
    landing reads that ledger, so a chain read below a position a record certified, as a
    landing chain behind a history window is, can take every landing chain to its empty prefix
    (`Witness.record_drags`).
14. **D14, what a purged row of the log keeps.** Recommended: the keyed hash of its path, with
    its position (§6.1), 47 bytes a row of index on the fixture. The alternatives: keep the
    path, which saves the hash and leaves a purged note's name readable in the log when every
    version of it is purged; or keep no key, after which a read by path at a cut returns the
    version before the purged one (`Witness.keyless_hole`). As built at SN-1, the purge empties
    a path's tombstones with its last version, which the recommendation needs: a `retire` that
    kept its path would leave the name readable as the first alternative does (§6.1).

## Parked decisions

| id | decision | default recorded | re-entry condition |
|---|---|---|---|
| SN-a | the cadence of recorded cuts | a trough that moved, the owner's command | a date that resolves to a cut farther from it than a declared tolerance |
| SN-b | the citation readings as rows valid over a range of commits | append-only rows a commit, stamped with their projection | the store's size on an instance |
| SN-c | the heads kept at some recorded cuts | none for a chain under 250,000 events; kept, from SN-4, for a chain over it (§4.2) | `heads_at` past a tenth of a second on a chain under the threshold, or under it by a wide margin on one over; met at SN-1, 0.11 s on a chain of 30,002 events, the cost the building of the answer (§4.2, §11), so this re-enters before SN-4 |
| SN-d | a second embedder identity's vectors kept beside the first | none: the present's identity | dn-two-phase-ingestion's open question 4 |
| SN-e | lexical statistics stored per class and per recorded cut | computed from the mask | a lexical query at a past cut over its budget |
| SN-f | `repo` as a graph of commits, and a chain a repository | the line of the branch the sensor reads, one repository | an instance whose history has merges or that reads several repositories |
| SN-g | which recorded cuts are kept under a horizon | the records stay; a landing chain keeps its commitments and hashes, so a record under its horizon still verifies there and reads nothing | a consumer that must read, and not only verify, a cut under a horizon |
| SN-h | generations with a diff for the causal fiber | recomputation with a memo | SNF-5 |
| SN-i | the curated rows written outside the catalog | outside the snapshot, counted in the answer's note (§5.6) | the script routed through the writer |
| SN-j | a date asked under a narrower grant | resolved over every record, the answer showing the record's id and its positions on the grant's chains only | a use that must hide when the instance was quiescent |
| SN-k | the genesis of a class seeded from the plane's supersession log | not seeded: the genesis is the catalog as it stands | a need for a path's order before the log existed, on an instance that has a plane |
| SN-l | joining the identities a path had on the two sides of a retire | none: a note that returns takes a fresh identity unless it declares its own (§6.2) | SNF-10 |

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
- **SNF-6 (the threshold for kept heads is wrong):** `heads_at` past a tenth of a second on a
  chain under 250,000 events, or the kept heads costing more than the read they save on one
  over. Then the threshold moves; on the fixture the read from the log alone passes a tenth of
  a second between 100,000 and 500,000 events (§4.2). Met at SN-1: as built every head costs 3.5
  to 3.9 µs a head returned, and a chain of 30,002 events reads them in 0.11 s (§4.2, §11). Since
  kept heads leave that cost, moving the threshold alone does not answer it; the read's shape is
  open with SN-c.
- **SNF-7 (the mask is too slow for the lexical statistics):** a lexical query at a past cut over
  its budget at the instance's size. Then SN-e; the rule that the statistics are the mask's does
  not change.
- **SNF-8 (kept model output is never read):** no sentence under `as of` reads an archived
  artifact or relation in a declared period. Then the archive stops and D10 takes its
  alternative.
- **SNF-9 (retention drops what is asked for):** cuts asked for under a declared horizon, or a
  pass ordered by the field that drops rows later asked for more often than a pass ordered by
  age. Then the window grows, or the order stays age.
- **SNF-10 (the fresh identity splits what is one item):** returns after a retire become
  routine, as an instance whose vault goes missing at syncs would show: notes that declare no
  identity whose history at the head starts at a return. Then SN-l, a join the owner runs. The
  retire stays unsealed: that is the owner's decision and no falsifier of this note reopens it.
- **SNF-11 (a transcription lies):** a built stage whose property test against a Lean statement
  fails. A transcription defect; the stage does not land until it agrees.
- **SNF-12 (an erasure leaks):** after a purge, a read at any cut or a scan of the instance's
  files finds the purged words. Then SN-3's reach is incomplete and no stage after it is on.
- **SNF-13 (append invariance fails on the code):** a sentence at a recorded cut that answers
  differently after unrelated landings, a retire or a re-projection, the erasure and the grant
  unchanged; or `as of "head"` that differs from no `as of`. Then some reader is not a function
  of the prefixes, and SNP-5 says which kind of store to look for.
- **SNF-14 (the region is not what is asked):** questions about change that need the two
  readings and cannot be put with the region. Then GD-4's form is built sooner, on the two
  readings this note supplies.
- **SNF-15 (a lowering is not local):** at a recorded cut, a chain other than the chain of
  records read below the record though it serves the record's position. Then some chain that
  can fail to serve is read through a resolved reference by a chain that content reads, the
  premise of §7.1 is false for it, and that reference is found and moved to the filter of §3.5
  or the chain is kept whole.
- **SNF-16 (a filtered row is served without its source):** at some cut, a pass attestation, a
  witness's attestation, a dream claim, an interpreted row, a claim op, a disposition or an
  authored supersession served while a row it reads, by a reference of §3.5 or one that list
  missed, is outside the cut or withheld. Then the list of §3.5 is
  incomplete or a reader goes around the filter, and the stage that reads that store at a cut
  does not land until it is closed.
- **SNF-17 (a declared identity is taken back by another note):** after a retire, a note that is
  not the retired one declares the retired identity, as a copied front matter would, and its
  history at the head holds the retired note's versions. Then the exception of §6.2 for a note
  that declares its identity is reopened with the owner (D3); the retire stays unsealed.

## Open questions

Each with the default the stages build on until it is decided.

- The chat log and the attestation ledger have no erasure today except a reset. Their chain
  tables digest commitments so that one can leave a hole; who may erase a turn is not decided
  here. Default: no erasure of a turn is built.
- A purge does not reach a backup or a migration's archive. A backup restored from before a
  purge verifies every certificate and holds what was purged (§3.6), so a restore has to apply
  the purges recorded since; that procedure, and whether a recorded cut is taken before a purge
  so that the purge's own moment is certified, belong with the design of backups. Default:
  neither is built, and the purge's attestation lists the positions it emptied so that either
  can be.
- The `cuts` chain under a reset: the records name chains by id, and a reset makes new chains.
  Default: the records are in the catalog's file and go with it.

## Cross-references

**Formal (this branch):** `formal/Palace/Snapshot/Defs.lean` (`Store`, `Cut`, `head`, `grow`,
`Extends`, `readAt`, `readBetween`, `view`, `present`, `AppendInvariant`, `PrefixOnly`, `foldAt`,
`stateOf`, `stateAt`, `lastWrite`, `Gen`, `closeAt`, `landGen`, `gens`, `selects`, `genRead`,
`prune`, `sealedAt`, `servedAt`, `servedNow`, `restrict`, `snapshot`, `redact`, `visible`,
`compact`, `serve`, `committed`, `purge`, `commitments`, `contents`, `Consistent`, `generator`,
`reached`, `Resolves`, `reachedIn`, `ResolvesIn`, `Withheld`, `Kept`, `chainDigest`,
`CollisionFree`, `Certificate`, `certify`, `Verifies`, and `sinceRetire`, `historyAt`, `holes`,
`shown`, `landingsAt`, `retiresOf`, `lives`); `formal/Palace/Snapshot.lean` (the declarations
§10 names, by law, and the twenty `Witness` controls); `formal/PalaceTest/Snapshot.lean` (seeds
430 to 528); the families cited:
`Palace/Clock.lean` (CLK-2: `IsCut`, `frontierCut`, `isCut_iff_not_crossed`, `IsCut.inter`,
`IsCut.union`, `IsCut.frontier_inf`, `IsCut.frontier_sup`), `Palace/Ingress.lean` (ING-7),
`Palace/Script.lean` (ING-17), `Palace/Derived.lean` (ING-19 to ING-21), `Palace/Plane.lean`
(PLN-4), `Palace/Utility.lean` (UTL-2, UTL-4), `Palace/Sentence.lean` (QSA-1 to QSA-4, QSA-10).

**Code (read at `e3e3ee47`, unchanged):** `core/sentence/grammar.py`, `ast.py`, `universe.py`,
`execute.py` (`as of`, the universe, `read`); `core/query.py` (the modes, `note_graph`);
`core/temporal/spine.py` (`CertifiedCut`, `cut_at`); `core/stores/catalog.py`, `versions.py`,
`chatlog.py`, `chat_events.py`, `causal_edges.py`, `reference_edges.py`, `plane.py`,
`vectorstore.py`, `lexical.py`, `memberships.py`, `derived.py`, `edges.py`, `claim_ops.py`,
`authored_supersession.py`, `staging.py`, `observation_history.py`, `code_observations.py`,
`agent_observations.py`, `curated_store.py`, `runledger.py`, `verdicts.py`;
`core/kernel/stores/rawstore.py`, `core/kernel/recursion_ops.py`; `core/attestation/store.py`,
`record.py`, `attestor.py`; `core/ingest/writer.py`, `landing.py`, `table.py`, `purge.py`,
`derive.py`, `sync.py`, `curated.py`, `readers.py`, `ingress.py`, `stream.py`;
`core/relations.py`, `core/curator/curator.py`, `core/dreaming/dreamer.py`,
`core/complex/temporal.py`, `core/verdict/dispositions.py`; `core/chat_events.py`,
`core/integrator.py`; `ingress/sync_vault.palace`, `ingress/sync_corpus.palace`;
`scripts/purge_raw.py`, `scripts/curate_local.py`, `scripts/migrate_provenance_split.py`;
`ops/code_sensor.py`, `ops/self_sensor.py`, `ops/code_snapshot.py`, `ops/chat_sensor.py`,
`ops/ci_witness.py`, `ops/supersede.py`, `core/ingest/founding.py`,
`ops/heartbeat.py`, `ops/ledger.py`, `ops/effect_ledger.py`, `ops/lifecycle/launcher.py`,
`ops/lifecycle/runs.py`; `eval/harness/store.py`, `eval/predictions/ledger.py`.

**Design:** global-event-clock §2.2 to §2.4 (the generators, Law C4, the certified frontier,
GC-N3's three certificates);
limits-of-the-algebra L7; dn-query-sentence-algebra §2.3, §2.7, §2.9; dn-ingress D1, D3, D5
(ING-7, the one writer); dn-ingress-language (ING-13 to ING-17); dn-two-phase-ingestion D1, D2
(ING-19 to ING-21); vector-membership-store A3.5, A3.7 (noninterference, the purge);
dn-utility-field §3.1, §4 (UTL-2, UTL-4) and its first open question; dn-graph-dynamics §6, §7.1
(GD-4, the state at a cut); dn-decision-integrators (the integrators' layer);
dn-mathematical-foundations §2.4 (design theorems and the ledger);
`papers/2026-11-10-temporal-snapshot/paper.tex`.
