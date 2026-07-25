# Text keypoints — is there a SIFT/ORB for prose and code?

Brainstorms on the CHUNK GRAIN: what the right unit of semantic segmentation is, imported from the
owner's computer-vision instinct (keypoint detection + tracking, superpixel over-segmentation).
Sibling of `embedding-space-specialization.md` (the form of the SPACE) and `ops-and-optimal-form.md`
(the form of the DATA); this one is the form of the UNIT. Bears directly on finding-0168 addendum 4
and finding-0167.

## 2026-07-25 — the CV analogy, and the piece the palace is missing

```capsule
topic: text-keypoints-and-chunk-grain
date: 2026-07-25 (session-44, ~02:30)

warrant (owner, verbatim): "are you familiar with SIFT or ORB? I used to abuse them in computer
vision class, I would detect the key points on every video frame, and on the next, and the next,
such that you could track the use of the same key point, is there a text equivalent? humans don't
read letter by letter, we read almost in pattern like ways, we recognize shape, so maybe raw chars
isn't always the best way to detect language/semantic meaning tokens, the tokens that are used as
the chunk grain, in computer vision, we could also call this superpixels, to over segment regions
of interest"

THE CV PIPELINE, DECOMPOSED (so the mapping is exact rather than vibes):
  detector  — find locations that are DISTINCTIVE and REPEATABLE (DoG extrema for SIFT, FAST
              corners for ORB)
  descriptor— a LOCAL, INVARIANT fingerprint of each location (gradient histograms / binary BRIEF)
  matcher   — descriptor correspondence across frames
  track     — the same point, followed through time

⚑ THE PALACE ALREADY HAS THREE OF THE FOUR — AND IS MISSING THE DETECTOR:
  descriptor = the embedding of a chunk (have)
  matcher    = membership overlap, weighted ~1/n(v) (DESIGNED — f-0168 addenda 3 + 4)
  track      = slot-lineages / occupancy chains (DESIGNED — f-0168 addendum 1)
  detector   = **MISSING.** Chunking today is AST/line-structural, not content-defined, so it is
               NOT shift-invariant. An insertion above a chunk can move it.
  ⇒ Restated: **the membership store IS a keypoint tracker for text.** A content-addressed chunk
    persisting across versions is a tracked keypoint; addendum 4's rename detection is descriptor
    matching across frames. The owner's CV instinct and his own membership model are the same idea
    arriving from two directions.

⚑⚑ THE CONVERGENCE WORTH NAMING: this analogy lands on EXACTLY the gap flagged an hour earlier from
  a completely different direction. f-0168 addendum 4 records that graded rename detection has a
  PRECONDITION — chunk-boundary stability under edits — which f-0167 already owed ("L0a proven
  edit-stable, L1 line-header check owed"). The CV framing re-derives it as "your detector is not
  repeatable." Two independent derivations of one gap. (Same shape as f-0168's own
  semantics-vs-performance convergence, and as the f-0169/ops-track convergence. This keeps
  happening, which is itself worth noticing.)

WHAT THE TEXT EQUIVALENT ACTUALLY IS — the pieces exist, unassembled:

  (1) ⚑ CONTENT-DEFINED CHUNKING (CDC) — the real analogue of a REPEATABLE DETECTOR, and the most
      actionable item here. Rabin fingerprinting / gear-hash / FastCDC cut at boundaries determined
      by a rolling hash over content, not by offset. The literature's named problem is literally
      "the boundary-shift problem": fixed-size chunking loses all downstream boundaries after an
      insertion; CDC boundaries RE-SYNC. FastCDC (USENIX ATC '16, Xia et al.) reports 3-10x faster
      than Rabin-based CDC at equal-or-better dedup ratio.
      ⇒ This is precisely the invariance f-0168 addendum 4 needs, and it is a solved,
        production-grade problem (rsync/restic/borg lineage — note the palace already depends on
        restic).
      ⇒ CAUTION: CDC is content-agnostic. Applied naively to source code it will cut mid-function.
        The interesting design is HYBRID: structural boundaries (AST/qualname, which carry meaning)
        with CDC as the SHIFT-ABSORBING layer beneath them — or CDC within a structural unit.

  (2) ENTROPY-BASED PATCHING — the closest thing to a semantic keypoint DETECTOR in current
      research. Meta's Byte Latent Transformer (arXiv 2412.09871) segments raw bytes into
      DYNAMICALLY SIZED PATCHES cut on the entropy of the next byte, spending compute where the
      data is complex; tokenizer-free, matches token-based LLMs at scale with ~50% inference FLOP
      savings. Conceptually near-identical to a keypoint detector: boundaries land where the signal
      is locally SURPRISING, i.e. information-dense. This is the research-grade answer to "raw chars
      are not the right grain" — and it agrees with the owner's instinct rather than the tokenizer's.

  (3) DISCOURSE / TOPIC SEGMENTATION — the "region of interest" analogue: split on topic shift by
      comparing adjacent windows in embedding space (the TextTiling lineage, Hearst — CITATION NOT
      VERIFIED THIS SESSION, check before quoting). Modern RAG practice does the superpixel move
      directly: OVER-SEGMENT at sentence grain, then MERGE adjacent segments by embedding
      similarity. That is exactly superpixels-then-region-merging.

  (4) NEAR-DUPLICATE MATCHING — MinHash / SimHash over shingles is a mature descriptor-matching
      analogue, and is what a `1/n(v)`-weighted membership overlap would be re-deriving. Worth
      checking whether the design should just USE MinHash/LSH rather than invent a cousin (the DRY
      audit applies to algorithms, not only code — [[owner-dry-strictness]]).

WHERE THE ANALOGY BREAKS (stated so it is not over-extended):
  · SIFT's headline invariances are SCALE and ROTATION. Text is not rotated. The invariances that
    matter here are SHIFT (insertion/deletion — answered by CDC) and PARAPHRASE (answered by
    embeddings). They are different mechanisms and must not be conflated: CDC gives byte-level
    shift-resistance with zero semantic understanding; embeddings give paraphrase-tolerance with
    zero shift-resistance. A complete "text SIFT" needs BOTH, layered.
  · SIFT keypoints are SPARSE — a few hundred per frame, most of the image discarded. Text chunking
    is currently EXHAUSTIVE (every byte belongs to some chunk). A genuinely SIFT-like scheme would
    embed only the distinctive regions, which is a real option with real risk: what you do not
    detect, you cannot retrieve.
  · On "we recognize shape": the functional claim (reading is not serial char-by-char; it is
    parallel and heavily context-predictive) is sound and is the load-bearing part. The stronger
    word-SHAPE / bouma-template claim is, to my understanding, largely superseded in
    psycholinguistics by parallel letter recognition within words — NOT VERIFIED THIS SESSION, and
    it does not change the design argument either way. Flagged so it is not repeated as fact.

COST CAVEAT (ties to the ops track):
  Over-segmentation multiplies vectors. More chunks = more storage, more embedding compute, and a
  SHIFTED n(v) DISTRIBUTION — which matters because addendum 3 makes n(v) a standing gauge and
  addendum 4 makes 1/n(v) the identity weight. Changing the chunk grain silently re-scales both.
  Any grain change is therefore a re-embed AND a re-calibration, in the same class as an embedder
  migration (see embedding-space-specialization.md) — and equally unaffordable until bp-100 lands.

open questions:
  - Hybrid design: structural boundaries carrying meaning (qualname/AST) WITH a CDC layer absorbing
    shift — what is the composition rule, and which wins when they disagree?
  - Does chunk-id stability actually require CDC, or is it enough to strip the line-header from the
    chunk id (the cheap fix f-0167 implies)? MEASURE BEFORE BUILDING — the cheap fix may buy most of
    the benefit, and assuming otherwise is this week's recurring failure mode.
  - Sparse-vs-exhaustive: is there a principled "keypoint" notion for text where NOT embedding
    something is safe? (Retrieval says no by default; n(v)/Zipf may say some chunks carry ~no
    identity information and are near-free to drop.)
  - Should the detector be LEARNED (BLT-style entropy) or ALGORITHMIC (CDC)? Learned = a model in
    the ingest path, which has sealed-core and reproducibility consequences (a re-derivable
    projection must stay re-derivable — the append-only/INTERPRETED discipline).
  - Does the same grain serve prose AND code, or is grain per-layer (L0a/L0b/L1 already differ)?
    The layer split suggests the answer is already "no", which is a partial precedent.
```

## 2026-07-25 — the Fourier thought: chunking IS low-pass filtering (but the transform is wavelets)

```capsule
topic: text-keypoints-and-chunk-grain (the spectral framing)
date: 2026-07-25 (session-44, ~03:15)

warrant (owner, verbatim): "a way to possibly test, if a fourier analysis of code or documents is
computed, how similar is it to it's tokenized seperation, is the semantic meaning preserved? that
could help with choosing the right embedder, if that was ever a concern?"

THE PART THAT IS ALREADY ANSWERED IN THE LITERATURE:
  "Is semantic meaning preserved under a Fourier transform?" has a published, partial YES. **FNet**
  (arXiv 2105.03824, NAACL 2022) replaces the self-attention sublayer of a Transformer encoder with
  a standard UNPARAMETERIZED Fourier transform and retains **92-97% of BERT's GLUE accuracy**, at
  80% faster training on GPU. Token mixing in the frequency domain does most of the semantic work
  attention does. So the owner's intuition that frequency-domain structure carries meaning is not
  loose analogy — it is measured.
  Related, already inside the tools: sinusoidal positional encodings ARE Fourier features, and RoPE
  is literally rotation in frequency space. Fourier is not foreign to embedders; it is inside them.

⚑ THE PART THE PALACE ALREADY HAS — and it is spectral, just not on the token axis:
  `core/complex/**` (A_signed, L) and `core/graph/{sigma_star,conductance,census}.py` are
  **GRAPH-Fourier** — eigendecomposition of the Laplacian. For a corpus modelled as a graph, that is
  the NATIVE spectral analysis, and it is built. So "should we do spectral analysis?" is already
  answered yes; the open question is only whether a SEQUENCE-axis transform adds anything the GRAPH
  spectrum does not.

⚑⚑ THE REFRAME THAT IS ACTUALLY USEFUL — **CHUNKING IS LOW-PASS FILTERING.**
  Text has characteristic scales: token, line, block, function/paragraph, section, document.
  Choosing a chunk grain IS choosing a cutoff frequency. Over-segmentation (superpixels) = high
  cutoff; document-grain = low cutoff. This is the same object as the 2026-07-11 capsule's "SMEAR:
  a smear of resolution along the embedded vector space" in doc-code-entanglement.md — and that
  capsule PARKED it with a recorded default (single-scale-at-chunk-grain stands, per the 2026-07-03
  source-set decision) and a re-entry condition ("a measured retrieval failure attributable to grain
  mismatch"). **This thought presses on that parked decision; it does not open a new one.** Respect
  the re-entry condition rather than routing around it.

⚑ BUT THE TRANSFORM IS WRONG: FOURIER ASSUMES STATIONARITY; TEXT STRUCTURE IS LOCALIZED.
  A Fourier transform gives GLOBAL frequency content with no localization — it answers "what
  periodicities exist in this document" when the real question is "where does the structure change,
  and at what scale". A function definition is a LOCAL EVENT, not a periodic one. The right family
  is **WAVELETS / multi-resolution analysis**, which is localized in both position and scale.
  ⇒ Restated: the owner's "smear of resolution" is multi-resolution analysis. Wavelets are the
    named mathematics for it. That is the correction worth carrying into any design pass.
  ⇒ And it rejoins the detector thread above: BLT's entropy-based patching is change-point detection
    on a local signal — closer to a wavelet/edge detector than to an FFT.

WHY IT DOES NOT WORK AS AN EMBEDDER-SELECTION TEST (the honest verdict):
  1. **You cannot FFT "the text".** You must first project it to a numeric sequence — per-position
     entropy, model surprisal, indentation depth, line length. THAT CHOICE DOES ALL THE WORK and is
     itself unvalidated. The result would measure the projection, not the embedder.
  2. **No established link to the thing we care about.** Spectral similarity between a raw-signal
     transform and a tokenized separation has no demonstrated relationship to RETRIEVAL QUALITY. It
     would be selecting an embedder by a proxy nobody has shown is predictive — which is this
     week's recurring failure mode (f-0163, f-0169, f-0174) dressed in nicer mathematics.
  3. **The direct instrument exists and is cheaper.** Retrieval precision measured on the actual
     corpus — and now with LABELS, via the code half being a labeled subgraph (doc-code-entanglement
     2026-07-25 capsule). Measure the thing, not a correlate of it.
  ⇒ VERDICT: keep the spectral framing for CHUNK GRAIN (where it is illuminating and where wavelets
    are the right tool); do NOT adopt it as an embedder-selection instrument. Embedder choice is
    settled by task evaluation on this corpus, gated behind the runtime migration (f-0174) anyway.

open questions:
  - Does the SEQUENCE spectrum add anything over the GRAPH spectrum the palace already computes?
    Cheap first test: does a wavelet/multi-scale decomposition of a document predict better chunk
    boundaries than the current structural chunker — measured on retrieval, with a falsifier?
  - Is there a principled mapping from "cutoff frequency" to "chunk size" that would make grain a
    TUNED parameter rather than a taste call? (Same shape as the sigma-calibration opportunity —
    another taste parameter that labels could turn into a measured one.)
  - Does FNet's result imply anything USABLE here, or is it purely an architecture-efficiency result
    with no bearing on corpus representation? (My read: the latter — it is about how a model mixes
    tokens internally, not about how a corpus should be segmented. Recorded so the citation is not
    over-claimed later.)
```
