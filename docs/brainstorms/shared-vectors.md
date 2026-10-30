# shared-vectors

## 2026-10-29

```capsule
topic: shared-vectors (content-addressed chunk vectors, supersession by reference set)
date: 2026-10-29

owner (verbatim): |
  "vector data needs to be stored efficiently, since ingesting/embedded tokens will be common,
  common words and phrases will occur, so it will actually be better and there SHOULD be a design
  doc somewhere outlining this direction: so if doc A and B both are composed of 10 vectors, and 5
  are the same, then A and B have pointers to those vectors in common, but if one of those changes
  in A, then a supersession edge from the doc is created to the updated doc with the new vector
  reference set, i believe that's loosely what the idea was"

state today (checked in code, 2026-10-29):
  - Rows carry their own vectors (LanceDB, one row per chunk). The curated importer skips a
    document whose text digest is stored, but its row ids include the source path, so the same
    passage in two documents is embedded and stored twice.
  - The code lanes already work the owner's way: content-addressed atoms plus membership edges
    (bp-153's D7 atom+membership rebuild; 17,508 memberships). Generalize that, don't invent anew.
  - FOUND, the note the owner remembers: docs/design-notes/vector-membership-store.md
    (dn-vector-membership-store, draft): one vector row per idea-atom, all occupancy in a
    membership relation (built for code: 4b5422a/48ba77d, bp-152; gauges n_doc, n_occ, |M|/|V|,
    embeds-avoided: 7211c1d; §4 "the frequency plane": n(v) counts and the corpus histogram as
    standing gauges). Its line 173 pins the opposite of the owner's newer ask below: "an atom
    never spans strata" (the PD-2 fence, carried as a test invariant).

direction (to design, then build):
  - A vector table keyed by (chunk content hash, embedder id): each unique chunk is embedded and
    stored once. A document version is an ordered reference set of chunk hashes (memberships).
  - An edit makes a new version that reuses every unchanged chunk's vector and adds a supersession
    edge old → new carrying the new reference set; nothing is deleted (archive, never delete).
  - Gains: a slightly edited note re-embeds only its changed chunks; versions and quoted or
    boilerplate passages cost nothing extra; a model change re-embeds unique chunks only.
  - Precision on "common words and phrases": vectors here are per chunk (a passage), not per
    token, so sharing pays for repeated passages and versions, not for common words. Per-token
    vectors would mean multi-vector (late-interaction) retrieval, where the state of the art
    compresses repeated token vectors with centroid codebooks (ColBERTv2 / PLAID residuals).
  - First step: measure the duplicate-chunk rate per store (vault, dialogue, curated, code).

owner (verbatim, later the same day): |
  "papers, dialogues, monologues can also reference the same vectors, that's how we connect the
  full stratum as well, common language use exists, and that's how we would also be able to run
  the statistical tests, like number of times a given token is used, a histogram, where a
  language-like histogram plot should appear, i think it's an exponential decay? where the most
  common words are sorted and the graph slowly dies out towards less common words/tokens?"
  - Conflict to resolve with the owner: cross-stratum atoms reverse dn-vector-membership-store's
    PD-2 fence (an atom never spans strata). A way to have both: the vector is shared, while
    provenance and access live on each membership, so curated rows stay unreadable from the
    mirror (the rule is enforced per membership, not per vector). Re-check the prefilter and
    sourceset arguments the fence protects before amending the note (owner-only ratification).
  - Math, corrected: word (and token) frequency by rank follows Zipf's law, a power law
    f(r) ∝ 1/r^s with s ≈ 1 (Zipf–Mandelbrot: 1/(r+b)^s), not an exponential decay. On log-log
    axes it is close to a straight line of slope ≈ -1, and its tail dies out far more slowly than
    an exponential would. Vocabulary growth follows Heaps' law, V(n) ∝ n^β with β ≈ 0.4–0.6. Fit
    the exponent by maximum likelihood with a goodness-of-fit test (Clauset, Shalizi & Newman,
    2009), not by least squares on the log-log plot.
  - Where it lives: sharing chunk vectors connects identical passages only. "Common language" is
    a token layer: a vocabulary with per-stratum counts (an inverted index). That layer gives the
    histogram and Zipf and Heaps statistics, lexical search beside dense search (hybrid
    retrieval), and cross-strata links through shared rare terms (IDF weighting; the Zipf head
    is mostly stopwords that carry little signal).

measured 2026-10-29 (eval/storage_census.py → data/eval/storage-census.json):
  - Exact duplicate chunks: notes, dialogue, observed 0%; code 0.63% (17,256 rows); papers 0.56%
    (148,240 rows); no text appears in two strata. A content-addressed table would save ~3 MB
    today. Code is already content-addressed (dn-vector-membership-store; current view: code_ast
    9,164 occupancies over 8,912 atoms), so its savings land across commits, not within one.
  - Where sharing does pay: versions (an edited note keeps its unchanged chunks' vectors; the
    prose lanes re-embed a whole note today), and model changes (re-embed unique chunks only).
  - Where the bytes are: the vectors themselves, 508.6 MB as float32 at 768 dimensions, most of
    each store on disk. The state-of-the-art levers, to measure as recall@10 against float32 on
    the palace's own queries before choosing: int8 scalar quantization (4x, ~127 MB); binary
    quantization with float rescoring (32x, ~16 MB plus a rescoring pass); product quantization
    (IVF-PQ, native to LanceDB); Matryoshka truncation to 512/256/128 dimensions if
    EmbeddingGemma-2 keeps v1's Matryoshka training (verify first).
  - Common language lives in the vocabulary, not in shared vectors: 87% of the words the owner's
    notes use at least twice also appear in the papers and 82% in the code (observed: 85% and
    82%). That is the token layer's case: an inverted index across strata, hybrid lexical and
    dense retrieval, and cross-strata links through shared rare terms.
  - Zipf, per stratum (rank-frequency fitted over the top 2,000 ranks): papers slope -1.10 (power
    law R² 0.987 vs exponential 0.837); code -1.00 (0.981 vs 0.862); notes -0.88 (0.969 vs 0.735);
    observed -0.75 (0.957 vs 0.726). A power law in every stratum; the small strata run flatter
    with half their vocabulary used once. Maximum-likelihood α of the frequency distribution
    1.45–2.47 (KS 0.04–0.19; the small strata fit worst): a proper tail analysis (likelihood-ratio
    tests against lognormal and stretched exponential, Clauset et al.) is still to do.

build plan (owner, 2026-10-29, verbatim: "yes, implement the efficient vector storage for all
strata layers, where the atoms are shared, but you're right, do it in a way that does not leak";
"the lean ladder ... should follow the vector storage changes, that is the more important work"):
  A. Amend dn-vector-membership-store (still draft; ratification stays the owner's hand) to
     re-design the PD-2 fence (§D1: "an atom never spans strata"):
     1. Atom identity for prose = (content_hash, embedder); the code layers keep D0's header-free
        body identity. The atom (vector) row carries no provenance.
     2. Provenance and access move to the membership (occupancy) row. The mirror firewall stays a
        row prefilter, now per class: boolean currency columns on the atom row (current_authored,
        current_dialogue, current_observed, current_code: D3's current_any, split by class),
        kept in step by the landing path (D2) and the R3 ratchet. A mirror query prefilters on
        current_authored = true (today: vectorstore.py:317-324 filters the row's provenance).
     3. The no-leak invariant, tested adversarially: a hit's attribution lists only memberships
        the grant may read. An atom reached through an authored membership never reveals that
        its text also occurs in a dialogue, observed or curated document. Sourceset's
        one-stratum axiom (core/kernel/stores/sourceset.py:58-62) holds per membership fiber,
        not per atom.
     4. Papers stay physically apart (dn-external-grounding §2.2, ratified): the curated store
        gets its own atoms and memberships (dedupe and versions inside the literature). Across
        the two stores, an embedding cache keyed by (content_hash, embedder) embeds a text once
        even when both store it. Merging the stores is the owner's decision, not this build's.
  B. Build (tests first, adversarial first):
     - Landings: vault notes (core/ingest/index.py: index_amendment / delete_source become
       membership landings; an edit keeps unchanged chunks' atoms, writes the new version's
       reference set and a supersession record), dialogue (core/ingest/dialogue.py
       capture_turn), observed captures, curated (scripts/curate_local.py,
       core/research/persist.py).
     - Reads: VectorStore.search prefilters by class column; QueryEngine attribution through
       memberships filtered by the grant (core/query.py `_hit_from_row`, `_search`).
     - Migration on D7's pattern (sliced, checkpointed, resumable), rebuilt from the raw store;
       archive the old tables under ~/mind-palace-archive/ first.
     - Gauges: per-class n_doc, n_occ, |M|/|V| and embeds-avoided (extend lane_gauges).
     - Tests: a mirror query never surfaces an atom whose only current memberships are observed
       or curated, and never lists a non-authored membership; the D4/D5 laws over reference sets
       and supersession chains as Hypothesis properties; tests/integrity stays green.
  C. Then the storage lever: int8, binary with float rescoring, IVF-PQ and Matryoshka 256,
     each measured as recall@10 against float32 on the palace's own queries.
  D. Then the Lean ladder. Ready: formal/ (untracked; Mathlib 9d581dff of 2026-10-27, Lean
     v4.36.0-rc2, 7.2 GB cache). Mathlib's names have drifted from the foundations note: the PSD
     lemma is SimpleGraph.posSemidef_lapMatrix (the note cites isPosSemidef_lapMatrix);
     components-equal-nullity is card_connectedComponent_eq_finrank_ker_toLin'_lapMatrix.
  Decision models: tev1:0.8b pulled (1.5 GB file; 2.0 GB resident on MLX; 2.2 s cold). First
     probe, a LanceDB commit-conflict log: choice "concurrency" 0.97; noul "a retry would fix it"
     0.46, unsettled. Heartbeat rows should pass keep_alive 0 so it unloads at once.
```

## 2026-10-29 (later) — built

```capsule
topic: shared-vectors — what landed (design: dn-vector-membership-store Amendment A3)
date: 2026-10-29

owner (verbatim, during the build):
  - "it shouldn't just be a simple condition, accessible records without the correct permission
    should be unrepresentable, and also enforced by the type system"
  - "no ratify, just do it" · "be thorough and correct about applying any new modules to the core"
  - "no type ignores allowed in the inner core" · "don't add a package just for dev only"
  - "upgrade the python version of the project if possible to the latest version that can resolve
    all dependencies"

built (branch ouroboros/shared-plane):
  - Python 3.15 (the newest CPython every dependency resolves on); pyarrow 26 typed by local stubs.
  - core/kernel/clearance.py — the permission as a capability: Clearance[L] with L a union of
    Provenance Literals (the subset lattice IS mypy's subtype lattice), sealed Row/Occupancy/PlaneHit,
    minting pinned by tests/integrity/test_clearance_holders.py; zero ignores in the inner ring,
    enforced by ops/type_gate.py's fourth scan.
  - core/stores/plane.py — atoms shared by every prose stratum; occupancy in one relation per class
    (occ_<class>); position-keyed supersession log per class (sup_<class>); held/held_ever as a
    fail-closed ANN prefilter cache; flock-serialized writes in D8 order; purge deletes freed atoms
    first.
  - VectorStore: every read takes a clearance (no default, no None); prose lands in the plane; the
    worker pipe binds its clearance at wiring time (a worker can no longer choose its permission).
  - Writers: delete-by-digest retired (it erased identical turns at other strata and left edited
    curated docs' old versions current); embed_new embeds only texts the plane lacks.
  - ops/plane_migrate.py — build beside, verify bit for bit, swap by rename into the archive.
  - Tests: Hypothesis noninterference + seeded leak; mypy negative test + label-erasure control;
    SQL trace (a mirror reader never names an uncleared relation); real-LanceDB end-to-end
    (identical turns, edit supersession, purge removes text, corrupted cache fail-closed).
```
