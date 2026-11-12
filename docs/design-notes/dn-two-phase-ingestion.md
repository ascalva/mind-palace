---
type: design-note
id: dn-two-phase-ingestion
track: query-language
status: draft                  # provenance description, never a gate; the merge is ratification
implementation: built          # the switch, the lexical index, the drain, the fallback, the pending report, the tests and the laws (ING-19 to ING-21) landed 2026-11-07; the default instance keeps synchronous embedding
created: 2026-11-07
updated: 2026-11-07
links:
  - docs/design-notes/dn-ingress.md                        # the ingress: the one writer, the landing order with the key last (ING-7), the ACID answer
  - docs/design-notes/dn-ingress-language.md               # the second form: ingestion as scripts, the writer's rules, the table, the jobs
  - docs/design-notes/vector-membership-store.md           # the shared plane: atoms content-addressed, occupancies per class, the fingerprint
  - docs/design-notes/dn-corpus-instance.md                # the instance this design serves: the embedder as the only slow stage
  - docs/experiments/corpus-measurements-2026-11-07.md     # the embedder at 21 to 30 chunks a second, the yield policy
  - docs/design-notes/dn-scale-and-attribution.md          # SCL-3: the Shapley value over the sources; the embedder as a player
  - docs/design-notes/dn-query-sentence-algebra.md         # the universe, `near`, the support and its notes
  - docs/experiments/two-phase-ingestion-2026-11-07.md     # the measurements of §6
  - formal/Palace/Derived.lean                             # the laws, machine-checked (Derived/Defs.lean the model; PalaceTest/Derived.lean the attacks)
  - papers/2026-11-07-two-phase-ingestion/paper.tex        # the article
supersedes: null
superseded_by: null
warrant: null
---

# Two-phase ingestion: an item is complete without its vector

> Composed on the ingress's third session (Fable 5.1, 2026-11-07), on the standing direction that
> the design and its proofs come first and the implementation follows them. Agent-drafted, filed
> `draft` on a branch; the merge is ratification. Every nontrivial claim carries a grade:
> `[THEOREM]` is machine-checked in `formal/` and names its declaration; `[ESTABLISHED]` is a
> ratified note's, a cited result's or a measured fact of the repository; `[DERIVED]` is argued
> here from those; `[MEASURED]` is a figure from `docs/experiments/two-phase-ingestion-2026-11-07.md`
> or from the corpus measurements; `[INFERENCE]` is a design call with a named falsifier. Code
> claims were read on `origin/main` at `87e2854`.

## 1. Purpose and scope

### 1.1 The requirement

The embedder produces exactly one of the store's relations: semantic similarity, the backbone
`S`. Every other relation, and nearly all of the mathematics the store computes, is defined over
the graph alone: the explicit edges (citations, hyperlinks, question to answer, version chains,
replies, code references), the walk sums and the resolvents (DYN-1), the Hodge potential (DYN-3),
the spectral gaps and the k-cores of the scale study, `reach`, `walk` and `via`. A tokenizer alone
gives an item a lexical representation (TF-IDF, BM25) that needs no model. And the embedder is the
only slow stage of ingestion: 21 to 30 chunks a second on this machine, sixty days for the hundred
gigabytes the corpus instance is built for, where every other stage lands 362,000 items in under
three minutes. `[ESTABLISHED: dn-corpus-instance §5, corpus-measurements-2026-11-07]`

So ingestion is two phases. **Phase 1** lands the item with its label, its bytes, its explicit
edges and its lexical index, at once, under the ingress's laws as they stand (ING-7 key-last
convergence, label soundness, one writer). **Phase 2** embeds lazily, in the background, as a
derived, idempotent, convergent write into the vector plane. A query that needs only structure
or lexical similarity works the moment the item lands; a query that needs a missing vector
reports it pending instead of guessing. And since the embedder brings outside knowledge, a prior
learned elsewhere, it becomes a source whose contribution the attribution machinery (SCL-3) can
measure.

### 1.2 What this note decides

D1, the invariant: an item is complete without its vector, and the vector is a derived field with
a key of its own, written by a drain. D2, the query semantics: `near` over vectors where they
exist and over the lexical index where they do not, labelled, the certificate over the known
vectors, the pending items in `missing`. D3, the label soundness and the one-writer rule unchanged.
D4, the embedder as a source, measured by SCL-3. D5, the laws ING-19 to ING-21. D6, the switch and
the defaults: `[embedding] lazy = false` on the default instance, so its behaviour is unchanged
unless the operator flips it; `lazy = true` on the corpus instance.

### 1.3 Out of scope

The chunker, the embedder, the plane's schema and its laws (PLN-1 to PLN-6), the catalog, the
versions and the attestations are unchanged. The lexical index is a derived store beside the
others, not a new place of the language; no word of the language names it. The corpus runner's
yield policy (whether a bulk batch waits for another caller of the embedder) is the runner's; this
note fixes the batch and the streams the drain uses and leaves yielding to it. Parallel dispatch of
the drain beside the writer in one daemon is designed (ING-20 says it is safe) and not built: the
drain is one job of the one writer.

### 1.4 What is proved, what is cited, what is open

Proved, in `formal/Palace/Derived.lean` on the model of `Derived/Defs.lean` (items, each item's
landed structure as one value, the plane's atoms per embedder identity, each item's mark per
identity), built under `--wfail`, fourteen attacks and five controls green (`PalaceTest/Derived.lean`,
seeds 374 to 392), twenty-two statements judged by the comparator (`Spec/Derived.lean`): ING-19,
ING-20 and ING-21 as §3.5 states them. Cited: ING-7 (the landing's own stages and the key last),
ING-5 (a held atom is not embedded again), PLN-4 (the plane inserts its atoms before its
occupancy transaction), VEC-1 (the margin certificate), SCL-3 (the Shapley value over sources),
the corpus measurements. Open (§7): the lexical index at the corpus's scale, the drain's yielding,
parallel dispatch, re-embedding under two identities at once.

### 1.5 The bar

**Correctness**: the laws are stated and attacked before the code, the code transcribes them, and
every law has a falsifier in the suite. **Security**: the lexical units and the vector carry no
label of their own, they inherit the item's, and the drain writes under the writer's own stores
and rules, so no principal gains a write it did not have. **Efficiency**: the landing no longer
waits for the embedder; the drain embeds in the measured batch, each atom once. **Verifiability**:
every answer that touches a pending item says so, and the measurements of §6 can be repeated with
one command. **Flexibility**: the switch is one key; the same drain re-embeds on a model change.

## 2. What exists: the inventory this note rearranges

**The landing.** `Writer.store` (`core/ingest/writer.py`) lands a store effect as the first form's
landers did: the raw object (`ingest_note`), then `index_amendment(record, [], embedder, plane)`,
which embeds the chunks the plane does not hold and lands the rows, then the version row where the
place keeps chains, the attestation, and last the catalog's digest, the idempotence key the
UNCHANGED check reads; the UNCHANGED check asks the plane whether it holds the version's rows
current (`holds_current`), so an active key implies current rows (ING-7, dn-ingress §9 finding 2).
The plan is priced before anything lands, and its embeds are charged to the meter as `embed`.
`[ESTABLISHED: read off the code]`

**The plane.** The vector store's shared prose plane (`core/stores/plane.py`) keeps one atom per
distinct chunk text, content addressed, with its vector, and per class an occupancy relation of
`(path, digest, chunk) → atom` with a currency flag; `land` inserts the missing atoms first, then
writes the fibers in one transaction and makes the version current (PLN-4); it refuses a new atom
that brings no vector (`MissingVector`); it records the embedder's identity, model, document
template and dimension (`Fingerprint`), refuses another (`GeometryMismatch`), and forgets it on
`reset`. `[ESTABLISHED: vector-membership-store A3, A4; PLN-4]`

**The universe.** `core/sentence/universe.py` builds a sentence's support: the mirror from the
plane's rows (`note_graph`), the dialogue from the plane's rows, papers and code from the indexes,
the citation graph at the cut. Its `known` mask already tolerates nodes without a vector (a
transcript turn, a reference node), whose row of the matrix is zero and which have no edge of `S`;
its `missing` reports what the universe lacks. `near` is the kernel column `clip(V·q̂, 0, 1)` over
the clause's carrier (QSA-3). `[ESTABLISHED: dn-query-sentence-algebra §2.9]`

**The certificate.** `VectorStore.search_ranked` computes VEC-1's margin over the stored vectors
the read ranked, opt-in beside `search`. `[ESTABLISHED: VEC-1]`

**The lexical tools.** The corpus instance's first stage (dn-corpus-instance) brought a lexical
index held in memory, BM25 weights as one sparse matrix over a fixed set of units
(`LexicalIndex`), which its battery loads to score millions of units at once, and a structural
phase: its runner landed items with `Writer.vectors` off and derived their rows afterwards from
the raw store (`index_from_raw`), with a note in the universe counting the items without rows.
`eval/metrics.py` holds recall and overlap over ranked lists, and the embedder bench reads two
BEIR collections from local files. This note keeps the matrix, gives it the same tokenizer as
the store below, and replaces the rest: the switch is `lazy`, the derivation is the drain, and
the pending items are reported as D2 says. `[ESTABLISHED: read off the code]`

**The measurements.** The embedder saturates at 30 chunks a second; one stream at batch 64 gives
26, and every further stream buys at most 15% while another caller's latency grows to the length
of the queue in front of it. The daemon's job rate is 12 a minute and is not the bottleneck; a
plan of two thousand items lands 10^7 items in a day. `[MEASURED: corpus-measurements-2026-11-07]`

## 3. Decisions

### D1 — The invariant: an item is complete without its vector

**The item.** What the landing writes for an item is a function of its bytes and its source: the
raw object, the label its source's rule gives it (ING-13, ING-14), its path and identity, its
explicit edges (a `link` effect, a version chain, a citation the sensors read), its lexical units
(the chunks the same chunker derives, each as term counts), its version row, its attestation and,
last, its key. Everything on that list is computed by the writer with no model. **The vector is
not on the list**: it is a function of the bytes and of the embedder's identity, a learned prior
the item did not bring, and it is the one thing the writer cannot compute at once. So the key
(ING-7) marks the item complete without it. `[DERIVED]`

**The derived field.** The vector is a field derived from the item, keyed by `(atom, identity)`:
the plane's atom is the content address of the chunk text, and the identity is the plane's
fingerprint, model, document template and dimension. The field's own key is the plane's current
occupancy of `(path, digest)`, written in the plane's transaction after the atoms (PLN-4), so the
drain's key is written last of the drain's writes as the landing's key is written last of the
landing's. An item whose key is written and whose current version the plane does not hold current
is **pending**: its field is absent, or an older version's. `[DERIVED from ING-7, PLN-4]`

**The drain.** `core/ingest/derive.py::drain` lists the pending items (`pending`: every active
catalog entry of a plane class whose `(path, digest)` the plane does not hold current, except one
the lexical index records as landed with no unit, an item with no text, complete with nothing to
derive; the plane's current versions are read once a clearance, so the list is one pass over the
catalog at any size), reads
each one's bytes back by digest, chunks them exactly as the landing did (`record_of`: the same
parse, the same chunker), embeds the atoms the plane lacks in requests of `batch` chunks with
`streams` in flight, and lands each group's rows in one plane transaction. Run again, it finds
nothing pending and embeds nothing (ING-20, `drain_idem`; ING-5 for the cost). Interrupted
between the atoms' insert and the occupancy transaction, it leaves the item pending and the atoms
held, so the next run embeds nothing and lands the rows (ING-20, `codeDrain_field`; on the code,
the test with the plane's transaction made to die). A text the embedder refuses must not stop
it either: the embedding server refuses an input longer than its physical batch (2,048 tokens)
rather than truncating it, and a chunk's 1,200 characters do not bound its tokens (in the corpus,
one comment of 1,145 characters was 2,951 tokens). So a refused group goes in halves until the
refused text is alone, and that text is cut to the longest prefix the server takes, by bisection
on the characters, as an embedding model truncates at its maximum length; the cut depends only
on the text and the server, so a second drain cuts it the same way, and the report counts the
cuts. Any other failure of the embedder is raised, never guessed past. The embedder applies the
same fitting to every request it makes (`core/ingest/embed.py`), so the synchronous landing, code
atoms, papers and queries cut the same text the same way instead of failing, and the ingress's
receipt says how many texts a landing cut; the plane does not mark such an atom, whose vector is
of a prefix. The drain is a job of the one writer
(`scheduler/embed.py`, kind `embed`, idempotent and pinned like `code_sync`): the writer asks for
it once a plan has landed an item without its vector, the housekeeping and the catch-up ask for
it under the switch, `mind-palace embed` runs it on demand, and `do sync_embed` is its script
(`ingress/sync_embed.palace`, `run "embed"`). `[THEOREM: ING-20; DERIVED on the code]`

**What the index records.** The lexical index records every version it lands with its count of
units, in the transaction that lands them, so the drain tells an item with no text (recorded,
none) from an item landed before the index was opened (no record): the first is complete, the
second is pending, and the drain finds out by chunking it. Reading a missing unit as an empty
item would leave every item of an earlier structural landing without its vector forever, which
is the mistake the record exists to prevent (tested). The index is derived like the vectors, and
`derive_lexical` is its drain: it lands the units of every active item the index has no record
of, from the raw store, a transaction a group, and run again it writes nothing. The corpus
runner's backfill (`scripts/corpus.py embed`) runs it before the vectors, and drains the vectors
through its gated embedder, which yields to other callers (`derive_entries`, the drain over the
entries the runner picks). `[DERIVED; tested]`

**Re-embedding on a model change is the same drain.** The plane records the identity its atoms
came from and refuses another; `reset` forgets the atoms, the occupancies and the identity, after
which every active item is pending, and the drain derives every one under the configured
embedder. Under `lazy`, `mind-palace reembed --confirm` is exactly that: a reset and a drain. The
catalog, the raw store, the versions, the edges and the lexical index are untouched by both: a
model change moves no identity and no history (`drain_other_atom`, `drain_other_mark`: the drain
under one identity leaves another identity's field alone). `[THEOREM: ING-19; DERIVED on the code]`

**What the UNCHANGED check reads.** Under `lazy` the plane's rows are the drain's, so their
absence is pending, not unlanded; the UNCHANGED check reads the key and the lexical index's
currency instead (`Writer.holds`): an active key implies the lexical units are held, which is
ING-7's invariant at the item's grain with the units in the rows' place. A landing that dies after
its units and before its key lands once when run again (tested). `[DERIVED from ING-7]`

**The price.** A lazy plan is charged its writes and no embeds: the drain's work is the daemon's
own, not the speaking role's. The ledger of the embedder's work is the drain's report (items,
chunks, embedded, reused, seconds), which the queue shows. `[INFERENCE; falsifier TP-5]`

### D2 — Query semantics: a query never invents a vector

**The rule.** `near` ranks over vectors where they exist and over the lexical index where they do
not, and says which. In the universe, an item landed without a vector, or whose plane rows are an
older version's than the catalog's, is a node without a vector and a member of `Universe.pending`;
its row of `V` is zero, so the kernel column scores it 0, which is no score, and `S` has no edge
at it. The evaluator (`Evaluator._near_pending`) gives the pending nodes of the clause's carrier
the lexical index's score for the text (each path's best unit, divided by the best among them, so
the best pending item scores 1 on a scale of its own), marks each such hit `ranked_by: lexical:
the vector is pending`, and adds a note to the answer saying how many of the clause's nodes are
pending and that the two parts are not one scale. Without a lexical index (an engine built by
hand), the pending nodes score nothing and the note says so. A stale vector is never read: a node
whose rows are an older version's drops its vector and is pending (`load_pending`), since the
vector is another text's. `[THEOREM: ING-21 on the model; DERIVED on the code]`

**Why not one scale.** A cosine and a BM25 score measure different things; dividing the BM25
scores by their maximum puts the best lexical match at the top of its part, which is the rule's
intent (a pending item the text names should surface), and the label on the hit and the note on
the answer keep the parts apart. Reciprocal rank fusion of the two rankings is the hybrid arm of
the battery (§6), where both exist; it is not `near`'s rule, since `near` is a field, not a
ranking. `[INFERENCE; falsifier TP-3]`

**The pending report.** The universe's `missing` carries one line: how many items are pending,
that the drain derives them, that a semantic clause ranks them by the lexical index and says so,
that `S` has no edge at them, and the first five by path. Pending items of the whole-loaded strata
(the mirror, the dialogue) are added as nodes; pending papers of the curated stratum are seeded by
the lexical index for each `near` text, at most `support`, since the vector index cannot reach
them (`seed_lexical`). `[DERIVED]`

**The certificate.** `search_ranked` ranks the stored vectors and certifies the top `k` among
them; a pending item is not among its candidates, so the certificate is asserted over the known
vectors alone, which is the only sound reading, and the share of certified reads is the same
before and after the drain for the vectors the store holds (§6 measures it at 0%, 50% and 100%
drained). The answer's pending note is what tells a reader the certificate's scope. `[DERIVED
from VEC-1]`

**Structural and lexical answers.** `relate`, `reach`, `walk`, `trace`, `witness`, `read` and a
lexical `near` read nothing the drain writes: their answer is a function of the keyed items and
what the landing wrote, so it is the same before and after any embed step (`structural_invariant`,
tested on `relate` across a drain). `[THEOREM: ING-21]`

### D3 — Label soundness and one writer, unchanged

The lexical units and the plane rows carry the item's label and no other: the lexical store's
rows copy the label of the store effect, and the drain's rows copy the catalog entry's, which the
writer fixed at the first store (ING-17) from the source's rule (ING-13, ING-14). No script, no
model and no field a model writes decides either. The drain lands through the writer's own stores
(`build_stores`) as a job of the supervisor, the one writer, so the single-writer property is what
it was (dn-ingress D3), and the drain's writes are confined to the plane (its atoms, occupancies
and cache) and nothing else. A retire takes the lexical units with the plane rows, before the
tombstone (ING-7). `[DERIVED from ING-13, ING-14, ING-17]`

### D4 — The embedder as a source

The embedder brings a prior learned elsewhere. In the attribution loop's terms
(dn-scale-and-attribution §3.2 to §3.4), it is a source of the system: an arm is a configuration
of the sources, context windows and tools the system may use, and the embedder is one of them,
beside the lexical index the landing builds from the bytes alone. The value function over the two
sources on a retrieval battery is `v(∅) = 0`, `v({L})` the lexical arm's score, `v({E})` the
semantic arm's, `v({L, E})` the hybrid's (reciprocal rank fusion of the two rankings), and the
embedder's attribution is its Shapley value, `φ_E = ½ (v({E}) − v(∅)) + ½ (v({L, E}) − v({L}))`,
the unique efficient, symmetric, null-respecting, additive attribution (SCL-3,
`Scale.lean::eq_shapley_of_axioms`); the leave-one-out reading `v({L, E}) − v({L})` is the
sign-flip test's estimand. The ledger records it as it records every arm: the configuration
digest names the sources in the arm, the pairs are scored per query, and the Shapley and
leave-one-out readings are functions of the ledger (§3.4's two readings). Here, before the loop
runs on the corpus instance, the battery of §6 computes them on a public control set, per query,
and records them in the experiment's JSON beside the arms' scores. `[DERIVED from SCL-3]`

### D5 — The laws

Family XII continued; the model is `formal/Palace/Derived/Defs.lean`: a state is the keyed items,
each item's landed structure as one value `S` (bytes, label, edges, lexical units: the laws read it
only through functions of it), the plane's atoms `E → S → Option V` per identity, content
addressed, and each item's mark `I → E → Option S`, the drain's key. A landing is one step (its
internal order is ING-7's); an embed step is the atom write then the mark write; the drain derives
every keyed item; the code's drain the pending ones; the field is what a reader sees: a derived
item's vector, `none` for a pending one.

| law | statement | the Lean | falsifier (pytest) | the Plausible control |
|---|---|---|---|---|
| ING-19 | completeness without the vector: a landing writes no atom and no mark and the landed item is keyed; the drain changes neither keys nor structures; the drain under one identity leaves another identity's atoms and marks alone | `land_atom`, `land_mark`, `complete_land`, `structural_invariant_drain`, `drain_other_atom`, `drain_other_mark` | a lazy landing with no plane row and a key, the UNCHANGED check reading the units, `relate` across a drain, re-embedding under a second fake embedder with the catalog, versions and attestations fixed | a run with a landing in it changes what a structural query reads (refuted within 45 instances) |
| ING-20 | the drain converges and is idempotent: an item's derivation is idempotent and commutes with another item's and with a later landing of another item; the drain is idempotent, leaves nothing pending and gives every keyed item its structure's image; from any interleaving of landings and embed steps the drain's field is the landings' followed by the drain; the code's drain reaches it from sound truthful states; every key-last prefix keeps soundness, every run truthfulness | `derive_idem`, `derive_comm`, `derive_land_comm`, `drain_idem`, `not_pending_drain`, `field_drain`, `field_drain_run`, `codeDrain_field`, `sound_derive_prefix`, `truthful_run` | the drain's store equal to a synchronous landing's, a second drain embedding nothing, two interleavings to one store, a drain dying inside the plane's transaction then converging with zero embeds, groups committed as they go | a landing of the same item does not commute with its derivation (first instance); the mark-first order is unsound (within 17) and the code's drain never repairs it (within 6): `mark_first_unsound`, `mark_first_does_not_converge` |
| ING-21 | pending-report soundness: a structural or lexical answer is invariant under every embed run; a pending item's field is `none`; a reported vector is the item's own structure's image | `structural_invariant`, `pending_field_none`, `field_some_truthful` | `near` ranking pending items by the lexical index with the label and the note, a stale vector pending and never read, no index giving no score and a note, the certificate's candidates excluding the pending item | reading a pending vector as zero gives an answer the embedding changes (within 8): `zeroRead_changes` |

Every attack survived (twelve all 500 instances, the two guarded ones 486 and 467); every control
was refuted. The model's `Sound` (a derived item has its atom) and `Truthful` (every atom is the
embedder's vector of its structure) are the hypotheses under which the code's drain, over the
pending items alone, reaches the full drain's field; both hold of a fresh state and are kept by
every key-last run, which is what the attacks generate their states by. `[THEOREM]`

What the model leaves out, said plainly: the landing's own stages and their order (ING-7's
model); the plane's cache and search (PLN-2 to PLN-4); the lexical index's arithmetic, a function
of the bytes the model takes as part of the structure; the embedder's determinism, which is an
assumption on the code (the same text to the same vector under one identity; the plane's atoms
are content addressed, so a nondeterministic embedder would land the first vector and reuse it,
which is still one vector per atom, but not `f e σ` for a fixed `f`). `[DERIVED]`

### D6 — The switch and the defaults

`[embedding] lazy = true | false`, with `batch` (64) and `streams` (1), the measured yield policy:
one stream of 64 saturates the embedder at 26 chunks a second; more streams buy at most 15% and
cost every other caller seconds of latency, so a second stream is the instance's deliberate
choice. Off, the writer embeds before it keys as it always did, opens no lexical index and writes
nothing it did not write before: the **default instance keeps synchronous embedding**, and its
behaviour is byte for byte what it was unless the operator flips the switch in its overlay. On,
the writer lands without embedding and asks for the drain, the lexical index is opened and landed
beside the raw object, `near` falls back and labels, the universe reports pending items, the
housekeeping and the catch-up enqueue the drain, and `reembed` is a reset and a drain. The
**corpus instance** sets `lazy = true` in its overlay (`config/instances/corpus.toml`), since the
embedder is its only slow stage. A runner that chooses per run says so to the ingress
(`perform(…, lazy=…)`), which otherwise reads the instance's key: the corpus runner's structural
phase is a lazy landing, and its other runs land synchronously while still writing the lexical
units, since the index is open. The batched landing of a plan of fresh stores
(`Writer.land_batch`, dn-corpus-instance §5.2) keeps its stages: every raw object, then the
lexical units of every store in one transaction, then (unless lazy) one embedding and one plane
transaction, then each version, attestation and key, last. `[INFERENCE; falsifier TP-1]`

## 4. The order of work

Built on this branch, in this order: the laws (`formal/Palace/Derived.lean`, attacked and judged)
before the code; the configuration key and its parsing; the lexical arithmetic and its store; the
drain and its report; the writer's `lazy` path, the UNCHANGED check's witness and the retire; the
scheduler kind, the launcher's wiring, the CLI verb and the script; the universe's pending nodes,
the lexical seed and the fallback; the tests, one per law and per path; the measurements (§6).
Nothing in the default instance's path changed except the field `lazy` it reads as `False`.

## 5. Falsifiers: the measurements that would break the design

- **TP-1 (the switch is not inert).** A deterministic test, or the live instance's receipts, show a
  store under `lazy = false` opening the lexical index, charging differently, or landing anything
  it did not land at `87e2854`. Then the switch is not a switch and the default instance's
  behaviour has changed; the fix is to the writer, not to the default.
- **TP-2 (the drain does not converge on the code).** A drain interrupted anywhere, run again,
  leaves a store that differs from the uninterrupted drain's in its current rows, or embeds an atom
  the plane holds. Then PLN-4's order is not what the plane does, or `pending` misreads the plane;
  ING-20's hypotheses fail on the code.
- **TP-3 (the fallback guesses).** A pending item appears in a semantic answer without its label,
  or an item whose rows are an older version's keeps its old vector in a universe, or an answer
  over pending items carries no note. Then D2's rule is not what the evaluator does.
- **TP-4 (the lexical index is not a stage).** A landing that dies after its lexical units and
  before its key lands twice, or a key is active while the units are not held, or a retire leaves
  the units current. Then the UNCHANGED check's witness is wrong and ING-7 does not hold at the
  item's grain.
- **TP-5 (the price lies).** A lazy plan's receipt charges embeds, or a role's budget is spent by
  the drain's work. Then the meter's units are the wrong principal's.
- **TP-6 (the embedder adds nothing).** On the battery of §6 the hybrid arm is no better than the
  lexical arm within its standard error, so `φ_E` is within noise of `½ v({E})`, and the leave-one-out
  reading is zero. Then on that collection the embedder's prior buys nothing over the bytes, and
  the design's cost is paid for structure alone; the measurement still stands, and the attribution
  loop on the corpus instance is where the question is decided on the system's own questions.
- **TP-7 (lazy landing is not faster).** The landing without the embedder is not at least ten
  times faster than with it, items a second, on the same items and plans. Then another stage is
  slow and this design does not move the bottleneck; the profile names it.
- **TP-8 (the certificate changes with the drain).** The share of certified ranked reads over the
  stored vectors falls as the drain completes, beyond what more candidates near the top `k` would
  explain. Then the certificate is reading pending items, which D2 forbids.

## 6. Measurements

The harness is `eval/two_phase_bench.py`, run against a scratch instance (a temporary root with
its own vault, stores and lexical index, the stack's embedder on port 8081, nothing of any live
instance) on a public control set, the SciFact collection of BEIR read from local files (5,183
documents, 300 test queries with graded relevance), each document a markdown item of its title
and text cut at 1,200 characters so that every item is one chunk, landed in ten requests. The
record is `docs/experiments/two-phase-ingestion-2026-11-07.md`, with one JSON a run. The harness
samples the embedder's busy slots every five seconds through each phase. The timings are a control
run on an idle machine (no sample showed another caller) and a lag run; the retrieval figures are
a first run's, since a ranking does not depend on timing. The first run's timings are not used:
another ingest's backfill held the same embedder for all of it, and its landing ratio read
91 where the control reads 21. One run a figure, read to one
significant figure.

| quantity | measured |
|---|---|
| landing without the embedder (lazy), items a second (two runs) | 32.0, 32.0 |
| landing with the embedder (synchronous), items a second | 1.50 |
| ratio of landing times, synchronous over lazy (TP-7: at least 10) | 21.4 |
| seconds a request of 519 items, first and last: lazy; synchronous | 2.2, 32.5; 67.0, 651.4 |
| the drain, chunks a second, one stream at batch 64 | 25.8 |
| lag from key to vector, drained at once, p50 / p90 / max (s) | 218 / 231 / 233 |
| recall@10, all derived: lexical, semantic, both | 0.755, 0.926, 0.929 |
| recall@10 at 50% drained: semantic alone, `near`'s rule | 0.544, 0.855 |
| the embedder's attribution at recall@10: Shapley, leave-one-out (se) (TP-6) | 0.550, 0.174 (0.022) |
| VEC-1 certified share at 0%, 50%, 100% drained (TP-8) | 1.00, 0.42, 0.44 |

TP-6, TP-7 and TP-8 survive: the embedder adds 0.17 of recall@10 over the
lexical index alone, 8 standard errors; landing without it is
21 times faster; and the certified share does not fall as the drain
completes (the share at 0% is of empty reads, which claim nothing). Both landings slow as the store
grows: the lazy one by the attestation lookup's pass over the ledger a store (the batched landing
reads it once a batch), the synchronous one far more, where every item is its own embedding
request and its own plane transaction; the drain lands 64 at a time. `[MEASURED: the record]`

## 7. Open questions

1. **The lexical index at the corpus's scale.** The store is SQLite postings with the document
   frequencies read at query time, right for the mirror and the dialogue and for the corpus's
   first gigabyte; at a hundred gigabytes the posting lists are the plane's size. The corpus's
   battery already holds the weights as a sparse matrix built in bulk (`LexicalIndex`); serving
   queries from it, or from an on-disk inverted index with skip lists, is the next form. The
   reconciliation (a version's units written once, the currency last) carries over. The first
   step is taken (2026-11-11, `docs/experiments/keyword-and-ledger-2026-11-11.md`): the unit count,
   the total length and the document frequencies are kept per class in the transaction of every
   write that changes which units are current, a reader's statistics are its cleared classes'
   rows summed, and the arithmetic, the sum and the top `k` are one statement read from the
   query terms' postings or the given paths' units, the scores the old statements' to the bit.
2. **Yielding.** The daemon's drain takes the embedder's time in batches of 64 without asking who
   else is waiting. The corpus runner's backfill drains through its gated embedder, which waits
   while another principal has a request in flight; the right place for that policy is the
   drain's job, with the slot probe a stated hypothesis on the server.
3. **Parallel dispatch.** ING-20 says a derivation commutes with another item's and with a later
   landing of another item, which is what would let the drain run beside the writer on disjoint
   items; the supervisor dispatches one job at a time today.
4. **Two identities at once.** The plane holds one fingerprint; a migration that keeps the old
   vectors searchable while the new ones are derived needs two planes or a fingerprint per atom,
   and the model already carries the identity per atom and per mark.
5. **The attribution loop.** D4 computes the embedder's value on a public battery; the loop of
   dn-scale-and-attribution computes it on the store's own questions as they resolve, with the
   embedder an arm's source, and that is where the question of what the prior buys is settled.
