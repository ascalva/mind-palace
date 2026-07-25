# Ops and the optimal form of the code — compression, cost, and measured access patterns

Brainstorms on the operations dimension of the project: performance as a first-class concern, cost
as a checkable property, and what the *optimal form* of the code and its data actually is. Warrant:
finding-0169 (the first real performance bottleneck) and the owner's reading of it as a complexity
time bomb. Companion capsule: `command-center.md` (the instrument this track needs).

## 2026-07-25 — the first bottleneck, and what it says about form

```capsule
topic: ops-and-optimal-form
date: 2026-07-25 (session-44, immediately after the finding-0169 incident)

warrant (owner, verbatim): "I'd say we hit our first performance bottleneck that resulted in a
potential ticking timebomb of complexity, I think these types of performance metrics and a quick
but deep understanding of the system's live metrics: the ops side of the project (operations, that
is), but this motivates me to now think about compression and performance, what is the optimal (or
at least more optimal) form of the code?"

owner's sharpening (same sitting): "which relates to the vector store containing vectors to
different memberships, that is a type of data compression" — i.e. finding-0168's membership model
is NOT only a semantic model; storing one vector with many memberships instead of one copy per
version/file IS compression, and the semantic and performance arguments are the same argument.

WHY IT WAS A TIME BOMB, NOT A BUG:
  Nothing about `supersede_source` changed. Its CALLING CONTEXT changed. Delete-then-re-add is
  correct and cheap at note scale (tens of rows, one-off migration). bp-099 promoted that same
  primitive into a per-version loop against a monotonically growing table. An O(n) primitive inside
  an O(n) loop is O(n^2), and NO LINE OF CODE HAD TO BE WRONG for that to happen.
  ⇒ **Cost is not a property of a function. It is a property of a function IN A CONTEXT.**
  The codebase has strong discipline about SEMANTICS (types, provenance, import firewall,
  attestations, the sealed core) and essentially NONE about COST. No function declares "I am
  O(table)", and nothing notices when such a function is called inside a loop.

THE REPEAT (uncomfortable, and the reason this deserves a track):
  finding-0163 = "PD-B was ratified on a false quantitative premise — the cost of history was never
  measured." finding-0169 = the re-land idiom was adopted without measuring its cost. SAME FAILURE
  MODE, ONE WEEK APART: a cost premise ASSERTED rather than MEASURED. The reconciliation-audit's
  "measured premises" instrument was designed for exactly this and does not exist yet.

THREE LAYERS (the question "what is the optimal form?" is really three questions):

  (1) REPRESENTATION — compression. The vector column IS the cost: 2560 dims x float32 ~ 10 KB/row;
      22,621 rows ~ 226 MB of pure geometry. An operation that drags vectors through Python pays
      ~1000x one that touches metadata only.
      · Structural rule: SEPARATE THE GEOMETRY PLANE FROM THE METADATA PLANE. Never carry vectors
        through an operation that only flips a flag.
      · ⚑ THE f-0168 CONVERGENCE: that rule is what the membership store already says — "a point is
        geometry, meaning lives in membership, history in slot-lineages." Derived from SEMANTICS
        (dedup, append-only, git's model at idea grain) and now INDEPENDENTLY RE-DERIVED FROM
        PERFORMANCE. Two orthogonal arguments converging on one design. Under it, tonight's defect
        is structurally impossible — there is no re-land.
      · The owner's point stated precisely: membership IS the compression. One vector reachable from
        many memberships replaces one copy per (version, file). Dedup across versions/reverts/files
        is a storage win AND a semantic win; the backfill was re-embedding and re-landing chunks
        that never changed.
      · Further, MEASURED not assumed: quantization (int8/binary coarse pass + exact rerank) is a
        further 4-32x on the geometry plane, but trades retrieval quality — it needs a measurement
        and a falsifier before adoption, per this very finding's lesson.

  (2) ACCESS — the mechanical rules. Any one of these alone prevents finding-0169:
      · push predicates into the store; never filter in Python after a full scan
      · never scan what can be indexed
      · never materialize a column you do not read (above all, `vector`)

  (3) DISCIPLINE — how the NEXT one is prevented. Rules in a doc do not hold (standing owner
      ruling: a property is only real when a test/ratchet proves it). The structural version is a
      PERFORMANCE RATCHET SUITE — the ops analog of the frozen golden set:
      · assert an operation's cost is independent of unrelated store size
      · store ops declare the largest N at which they have been MEASURED ("scale witness")
      · a call site operating beyond its primitive's measured N is a finding
      · candidate: extend the reconciliation-audit's decision→enforcement map with a cost column

THE REFRAME (the part worth arguing about):
  "What is the optimal form?" cannot be answered yet, because THE SYSTEM DOES NOT KNOW ITS OWN
  ACCESS PATTERNS. Optimal is a function of how data is actually read; right now that is
  speculation. But Ouroboros is unusual — it already ingests its own code, transcripts, and
  exhaust. It can measure itself.
  ⇒ Honest sequence: INSTRUMENT → MEASURE ACCESS PATTERNS → DERIVE REPRESENTATION.
  ⇒ Which makes the command center more than a dashboard: it is the SENSOR THAT MAKES PERFORMANCE
    WORK EMPIRICAL, and the same philosophy already ratified everywhere else (falsifiers over
    proofs, measured premises over asserted ones). The ops track and the compression track are the
    same track; the metrics are its INPUT, not its alarm panel.

open questions:
  - Does the performance ratchet live in `eval/` (beside the golden set, as its ops analog) or in
    `tests/` as a ratchet? The golden set is frozen and human-only; perf baselines drift with
    hardware — so they are NOT the same kind of fixed point. Needs a design answer.
  - How is a "scale witness" expressed so it is checkable and not a comment? (type? decorator?
    docstring convention parsed by a gate? — the provenance discipline is the model to copy)
  - Which access patterns actually matter? Retrieval is the obvious one, but the dreamer's full
    scans, the integrator's joins, and the drift gauges have entirely different shapes.
  - Quantization: what is the acceptable retrieval-quality loss, and what falsifier proves it?
  - Does this track absorb finding-0165 (background starvation) and f-0171 (job budgets), or do
    those stay scheduler-local? They are all "cost as a first-class concern" in different clothes.

sequencing: THIS MUST NOT DELAY THE finding-0169 FIX. That is a small mechanical change that gets
the daemon back up. This is a track — capture → Fable design pass → adversarial panel (systems +
core + math) → graduate. Its natural first deliverable is the ratchet, not a rewrite: the membership
store (f-0168) is already the representation answer, and it needs the measurement discipline around
it more than it needs new ideas.
```

## 2026-07-25 — structured residuals: reading the parameters we failed to model

```capsule
topic: ops-and-optimal-form (the prediction half) · touches fiber-geometry
date: 2026-07-25 (session-44, same sitting, ~01:30)

warrant (owner, verbatim — offered as "a funny thought"): "what if the future comes from a higher
dimensional projection into the space we operate, its landing produces a lossy artifact, perfect
prediction is futile, but that doesn't mean you can't be close, teasing out the higher dimension's
parameters to get a glimpse behind the curtain"

WHY THIS IS NOT ONLY POETRY — it is a fiber bundle, and this project already has that track:
  A projection pi: E -> B from a total space to the base space we observe, with a FIBER over each
  base point holding the coordinates we cannot see. "Teasing out the higher dimension's parameters"
  = reconstructing fiber structure from base-space observations. See docs/tracks/fiber-geometry.md;
  the joke landed on the project's own machinery.

TWO RESULTS THAT MAKE "LOSSY BUT CLOSE" RIGOROUS RATHER THAN CONSOLING:
  · Johnson-Lindenstrauss — project a point set into far fewer dimensions and pairwise distances
    survive within (1 +- eps), with the needed dimension depending on eps and the number of points,
    NOT on the source dimensionality. You lose the coordinates and keep the RELATIONSHIPS. This is
    the bet every embedding here already makes: 2560 dims is itself a shadow of whatever generated
    the text, and retrieval works anyway.
  · Structured residuals (the part with teeth) — if a model's errors are RANDOM, you have captured
    what is capturable. If the errors have STRUCTURE, that structure is the fingerprint of an
    UNMODELED DIMENSION. The latent-variable game. You never see the hidden axis; you see what its
    absence systematically does to your predictions.

⚑ THE LIVE INSTANCE, SAME NIGHT (this is why it belongs in the ops track, not only in philosophy):
  We predicted the backfill along the dimension we could see — versions landed — and got ~4.5 h.
  The real generator carried a second parameter we were not modelling: cost per version scales with
  TOTAL TABLE SIZE. We could not observe that parameter directly. But **the ETA DIVERGED, and the
  divergence had structure — it grew monotonically.** That residual was the hidden dimension
  announcing itself through the shadow it cast on our estimate. The system named a variable we had
  not, in the only language available to it: a wrong prediction that was wrong in a PATTERNED way.
  ⇒ Corollary for the command center: a diverging ETA is not a bad ETA, it is a MEASUREMENT. An
    instrument that only shows the point estimate throws away the residual — which was the single
    most informative quantity available at minute five.
  ⇒ Corollary for epistemics: "perfect prediction is futile" is operational here, not defeatist. A
    model that cannot be wrong in an informative way teaches nothing about the fiber. This is the
    same disposition as ratifying falsifiers rather than proofs — see [[owner-background-self-mapping]].

the actionable question this opens for the ops track:
  **Which access-pattern parameters does the system currently fail to model, and what residual would
  reveal each of them?** Candidates: cost-vs-store-size (found tonight, the hard way);
  cost-vs-history-depth; embedding-throughput vs resident model set; queue drain vs tier contention
  (f-0165); retrieval latency vs corpus growth. Each is a hidden coordinate; each should have a
  named residual the instrument watches, rather than waiting for a laptop battery to notice.

open questions:
  - Is there a principled way to enumerate a system's unmodeled dimensions, or is it always
    "watch residuals until one has structure"? (The honest answer may be the latter — which makes
    residual-watching an INSTRUMENT REQUIREMENT, not a nice-to-have.)
  - Does this connect to the drift axes already built (eval/*_drift.py)? Drift is a residual over
    time; this is a residual over scale. Same shape, different base space.
  - Fiber-geometry track overlap: is "which parameters generate the observed cost surface?" the same
    question the survey readings (M1-M8) ask about the corpus? If so, one instrument, two uses.
  - Would a design note be premature here? The ops track's first deliverable is a ratchet; this is
    the theory of WHY the ratchet's residuals matter. Possibly a section of the ops design note
    rather than a note of its own.
```

## 2026-07-25 — "have I embedded this before?" — and why membership makes the check intrinsic

```capsule
topic: ops-and-optimal-form (ingest cost) · bears on finding-0167, finding-0168
date: 2026-07-25 (session-44, ~02:45)

warrant (owner, verbatim): "you can even optimize if you've seen token by maybe using something
like a bloom filter to check if it's been seen before, or maybe that's possible before embedding if
the tokenizer knows if the token has been seen before, it would need a cheap way of checking"

FIRST — THE INSTINCT IS RIGHT, AND IS ALREADY AN OWED FINDING (his own).
  finding-0167 is exactly this, warranted by his earlier question 2026-07-23 ("if only one line
  changed, only that vector should re-embed"). Grounded there: the temporal code corpus is efficient
  at FILE grain (unchanged blob = zero embeds) but NOT at CHUNK grain — on a changed blob,
  `_embed_and_land` embeds EVERY chunk of the new version, "even though ~most chunks carry a
  content_hash identical to the prior version's rows sitting in the store with vectors." The NOTE
  lane already has the reuse discipline (`vec_by_hash`); the CODE lane does not. So the missing
  piece is not the idea — it is the port.

SECOND — THE BLOOM FILTER IS THE WRONG TOOL HERE, for a specific and checkable reason.
  A Bloom filter's error is ONE-SIDED: no false negatives, but false POSITIVES. In this application
  a false positive reads as "I have seen this chunk" when it has never been embedded ⇒ the embed is
  SKIPPED ⇒ **a vector that should exist silently does not.** That directly violates the owner's own
  bar in f-0168: "a vector that doesn't change is never duplicated; once stored it's always in the
  history." A probabilistic skip trades correctness for a lookup that is, at this scale, free.
  ⇒ The CORRECT Bloom usage is the inverse: as a NEGATIVE pre-filter in front of an exact store.
    "Definitely not present" is exact, so a Bloom miss ⇒ certainly new ⇒ embed immediately, no disk
    lookup. A Bloom hit ⇒ fall through to the exact index. This is the LSM/SSTable pattern
    (RocksDB/LevelDB) and it is sound — it just is not needed yet (below).
  ⇒ SCALE CHECK (the discipline this session keeps re-learning — measure, do not assume): the store
    holds **22,621 rows**. An exact in-memory set of sha256 chunk hashes at that size is trivial;
    even low MILLIONS of chunks is ~100 MB. **The exact structure fits in RAM by orders of
    magnitude, so the probabilistic structure buys nothing and costs correctness.** Re-entry
    condition for Bloom: the chunk index no longer fits in memory, or the lookup is MEASURED to be
    a material fraction of ingest time. Neither is true today.

THIRD — GRAIN MATTERS, and "token" is the wrong level.
  At TOKEN grain a seen-check is vacuous: the vocabulary is ~10^5 and essentially every token has
  been seen after the first few documents — the filter would answer "yes" always and save nothing.
  The value lives at CHUNK grain, where the space is astronomically large and a repeat is
  semantically meaningful (an unchanged function across two commits). Between the two sits
  n-gram/shingle grain, which is MinHash/LSH territory — relevant to near-duplicate detection
  (see text-keypoints-and-chunk-grain.md), not to embed-skipping.

⚑ FOURTH — AND THIS IS THE INTERESTING PART: under finding-0168 the check is NOT AN OPTIMIZATION,
  IT IS INTRINSIC.
  In the membership model, ingesting a chunk REQUIRES resolving whether that content-addressed
  chunk already exists — because that is how the membership edge is created (point at the existing
  vector, or mint one). The lookup is not bolted on to save work; it is the operation. Reuse falls
  out for free, and "have I seen this?" stops being a question the pipeline asks and becomes the
  shape of what the pipeline does.
  ⇒ Exactly the same move as addendum 4 (rename detection stops being a mechanism and becomes an
    observation). That is twice now that the membership model has absorbed a thing we were about to
    implement separately. Worth stating as a design heuristic in the f-0168 pass: **if membership
    makes a mechanism disappear, that is evidence the model is right.**

⚑ FIFTH — HONEST CALIBRATION, so this is not mis-sold: THIS WOULD NOT HAVE FIXED TONIGHT.
  During the failed backfill, `llama-server` was measured at **0.3% CPU** while the worker sat at
  99% — embedding was NOT the bottleneck; the quadratic re-land (f-0169) was. Chunk-level reuse is a
  STEADY-STATE INGEST win (and a large one once history is dense: most chunks of a changed file are
  unchanged), not an incident fix. Sequencing unchanged: bp-100 first.

open questions:
  - Where does the chunk-hash index live — a column/index on the vector store, a sidecar sqlite, or
    (post-f-0168) the membership table itself? The last is the only one that is not a second source
    of truth.
  - Does the reuse path need to verify the retrieved vector's dimension/model provenance? A chunk
    hash matching under a DIFFERENT embedder is a false reuse — ties to
    embedding-space-specialization.md (a model change must invalidate every reuse).
  - Measure first: what FRACTION of chunks on a changed blob are actually unchanged? f-0167 asserts
    "~most" — that number has not been measured, and this session's recurring lesson is that
    unmeasured quantitative premises are where the defects live.
```
