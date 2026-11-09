---
type: design-note
id: dn-embedder-use
track: query-language
status: draft                  # provenance description, never a gate; the merge is ratification
implementation: partial        # the tokenizer fix and its identity are built and tested; every other change is a recommendation with its cost, no live default changed
created: 2026-11-08
updated: 2026-11-08
links:
  - docs/experiments/embedder-use-2026-11-08.md            # the pre-declared protocol and every measured figure
  - docs/experiments/embedder-use-2026-11-08.json          # the figures as data
  - eval/embedder_use/                                      # the harness
  - core/ingest/lexical.py                                  # the tokenizer and its identity
  - core/stores/lexical.py                                  # the store that records the identity and refuses another
  - docs/design-notes/dn-two-phase-ingestion.md             # the lexical index, the drain, the embedder as a source
  - docs/design-notes/vector-membership-store.md            # the plane, its fingerprint, float16 and VEC-1
  - docs/experiments/corpus-stage1-2026-11-07.md            # the corpus battery and the bridges this study reads
  - papers/2026-11-08-embedder-use/paper.tex                # the article
supersedes: null
superseded_by: null
warrant: null
---

# How the store uses its embedder, and whether its tokens are consistent

> Composed on the embedder study (Opus 5.5, 2026-11-08), on the direction that every choice about
> the embedder is judged across domains and every threshold calibrates itself from the data.
> Agent-drafted, filed `draft` on a branch; the merge is ratification. Every nontrivial claim
> carries a grade: `[MEASURED]` is a figure of docs/experiments/embedder-use-2026-11-08.md (its
> protocol committed before the runs); `[ESTABLISHED]` is a cited result or a fact of the
> repository read at this branch's base; `[DERIVED]` is argued here from those; `[INFERENCE]` is a
> design call with a named falsifier.

## 1. Purpose and scope

### 1.1 The question

The embedder is the store's first auto-integrator: a learned prior that turns any raw text into
structure, a semantic edge between two chunks, without a line of code written for the source the
text came from. The integrators before it were written for one use: the transcript integrator
turns session logs and commits into causal edges by rules about those events, and is worth
nothing on a Wikipedia article. So the embedder is judged here as a domain-free component should
be: a choice is good if it holds across the domains the store holds, and a threshold is good if it
sets itself from the data (a quantile, a held-out fit), never a constant tuned for one source.
`[INFERENCE]`

Six choices decide how much of the embedder the store uses, and each is measured against the
live default on two public sets (SciFact, NFCorpus) and the corpus instance's open text:

1. how the lexical index tokenizes, which normalizes no Unicode today;
2. the chunk budget, 1,200 characters, against budgets in characters and in the embedder's tokens;
3. whether a chunk is embedded with its document's context (the title in the document template,
   or late chunking);
4. which task prompt a query carries;
5. how many of the vector's 768 dimensions are kept (Matryoshka truncation);
6. how a semantic edge is thresholded: the global cosine 0.785, against thresholds the data sets
   and corrections for hubness.

### 1.2 What this note decides

- **Built:** the tokenizer fix. Lexical terms are NFKC-normalized and case folded, combining marks
  stay inside their word, and the tokenizer has an identity every lexical store records, refuses
  to mix with another, and re-derives under (§4). Content hashes stay on the raw bytes.
- **Recommended, not applied:** the changes of §5, each with what adopting it re-derives. No live
  default (template, chunk budget, threshold) is changed by this branch.
- **Out of scope:** another embedding model; a reranker; word segmentation for scripts written
  without spaces (Thai, Chinese, Japanese), which the tokenizer treats as one run.

## 2. What the store does today

- **Chunks.** The chunker packs paragraphs up to 1,200 characters with 150 of overlap and cuts a
  longer paragraph into windows. The median chunk takes 151 of the embedder's tokens on NFCorpus,
  210 on W and 255 on the working instance, against a slot of 2,048 `[MEASURED]`.
- **The title-only chunk.** When an item's first paragraph does not fit beside its title, the
  chunker emits the title alone, then carries all of it into the next chunk as its overlap. Every
  multi-chunk document of SciFact and NFCorpus has one (29% and 31% of their chunks), and so do
  23% of OpenAlex's chunks and 26% of arXiv's, 84,002 of the corpus's 1,369,944 in all; Wikipedia,
  Stack Exchange, Gutenberg and Hacker News almost never `[MEASURED]`. A domain-free rule with a
  domain-shaped failure: it bites exactly where documents are one long paragraph.
- **Short texts are hubs.** A chunk's vector is the mean over every token of its input, the
  template's included, so a short chunk is largely template. The title-only atoms of OpenAlex and
  arXiv have about 19,000 and 16,000 atoms of other items above the cosine 0.785, twice their
  other atoms; at the item grain, the 10-nearest digraph's in-degree has a skewness of 21 and one
  item is among the 10 nearest of 3,071 others `[MEASURED]`.

## 3. Findings

Every figure is a paired difference against the live default with its 95% interval, from the
record's tables; "better", "worse" and "no worse" are the record's decision words.

### 3.1 Tokenization and Unicode

- **The defect is real and rare in these sets.** Normalizing (NFKC, `casefold`) merges 32 of
  SciFact's 38,466 legacy terms into 16, 38 of NFCorpus's 28,425 into 19, and 7,211 of the
  corpus's 1,053,985 into 3,237; it changes 0.009%, 0.014% and 0.028% of token occurrences. The
  merged terms are the forms a reader takes for one: `identiﬁed` with a ligature from PDF
  extraction, the micro sign against the Greek letter in `µm` and `μm`, `h₂o₂`, `ic₅₀`, `m²`.
  Of the corpus's 1,338,585 atoms, 18,931 are not in NFKC, 574 not in NFC, 2,086 hold a combining
  mark NFC leaves in place, and 24 would coincide with another atom if hashes were normalized.
  `[MEASURED]`
- **Retrieval cannot tell the arms apart.** Every normalizing arm ranks every SciFact and NFCorpus
  query exactly as the legacy tokenizer, and gives every corpus question the same recall@10
  (0.874); the largest nDCG@10 difference on the corpus is +0.003 (Holm p 0.69). The pre-declared
  rule therefore implements the most normalizing arm, T5. `[MEASURED]`
- **Stemming is not domain-free.** Harman's S stemmer raises BM25's nDCG@10 on NFCorpus (+0.014,
  better) and SciFact (+0.012, no worse) and lowers the corpus battery's recall@10 (-0.002, no
  worse), whose questions are titles and names; it is English only. Not adopted. `[MEASURED]`
- **The corpus's index was built by another tokenizer.** Stage 1's index came from its branch's
  ASCII tokenizer (`[0-9a-z]+`, its 926,483 terms reproduced exactly), which loses recall@10
  against the Unicode one (-0.002, worse). `[MEASURED]`

### 3.2 Chunk size

Budgets of 2,400 and 4,800 characters, and of 512 and 1,024 tokens, raise nDCG@10 on NFCorpus
(+0.021 to +0.028, better) and on W's link questions (+0.020 to +0.031, better) with half to a
fifth of the vectors and 3% to 14% fewer tokens; W's recall@10, its pre-declared primary metric,
is undecided (-0.005 to +0.008, every interval reaching below -0.01). Smaller budgets lose on W
(C600 recall -0.038, worse). Counting in tokens instead of characters changes nothing at a matched
size. By the rule the live budget stays; the evidence leans to 2,400 characters. `[MEASURED]`

### 3.3 The chunk's context

- **The title in the document template pays.** `title: {title} | text: {text}` against `title:
  none`: SciFact nDCG@10 +0.029, NFCorpus +0.038 (better), W's link nDCG +0.017 (better) and recall
  -0.009 (undecided). It costs 12% more tokens on abstracts and 1% on W. It is the model's own
  documented document format. `[MEASURED]`
- **Late chunking does not, across domains.** It is better on SciFact (+0.047) and NFCorpus
  (+0.016) and worse on W's recall (-0.033). The control L1, which pools each chunk's own tokens
  without the rest of the document in view, gives most of the gain on SciFact (+0.040) and more
  than late chunking on NFCorpus (+0.030): on short documents what helps is leaving the
  template's and the special tokens out of the mean. On the long articles the other chunks in view
  cost recall. `[MEASURED]`
- **Dropping the title-only chunk pays at no embedding cost** (exploratory). SciFact recall@10
  +0.034 and nDCG@10 +0.033, NFCorpus nDCG@10 +0.034 (better), W +0.005 (better); 26% to 31% fewer
  vectors on the abstracts. The title is not lost: it opens the next chunk. `[MEASURED]`

### 3.4 The query's task prompt

No alternative prompt is better on the set whose task it names: question answering on NFCorpus
+0.005 (no worse), fact checking on SciFact -0.008 (undecided) and on NFCorpus -0.011 (worse). The
store keeps `task: search result`. `[MEASURED]`

### 3.5 Dimensions

The first 256 coordinates, renormalized, with the 50 best chunks rescored by the full float16
vector, lose nothing on SciFact (+0.000), NFCorpus (-0.001) or the corpus battery (-0.000), all no
worse, at a third of the resident bytes. Flat 256 already loses on NFCorpus (-0.014, worse);
128 loses everywhere. `[MEASURED]`

### 3.6 Semantic edges

The thresholds the data sets are all above 0.785 at the item grain (the median cosine to the 10th
nearest: 0.808 for Hacker News to 0.948 for Gutenberg, 0.865 over all items), so the global
threshold gives nearly every item its 10 nearest. Per-source quantiles even out the degrees across
sources (largest source mean over smallest 2.0, against 2.3 for 0.785 and 10.8 for a global
quantile) but find fewer bridges per false positive (2.68 against 3.79). Mutual nearest neighbours
and CSLS remove the hubness (degree skewness 0.8 and 1.2 against 23.0) and with it every bridge
above the null (0.84 and 0.78). The global 0.785 stays by the rule, and stage 1's excess of
semantic bridges is carried by hub edges. `[MEASURED]`

## 4. The tokenizer and its identity

### 4.1 The defect

The lexical tokenizer took maximal runs of letters and digits of `text.lower()`, with no Unicode
normalization anywhere before tokenizing or hashing `[ESTABLISHED: core/ingest/lexical.py at the
base]`. Two consequences follow from Python's character classes `[DERIVED]`:

- **One text, two sets of terms.** A precomposed "é" (U+00E9) and an "e" followed by a combining
  acute (U+0301) are canonically equivalent (UAX #15) and read the same, but a combining mark is
  not a letter, so the decomposed form splits the word at the mark: `naïve café` in NFD gave
  `nai`, `ve`, `cafe`. Compatibility forms never met their plain forms either: the ligature in
  `identiﬁed`, the micro sign in `µg` against the Greek `μg`, the subscripts of `H₂O` and `IC₅₀`,
  the superscript of `m²`, full-width digits.
- **Words of some scripts shredded.** Vowel signs and points that compose into no precomposed
  character (Devanagari, Hebrew, Arabic) are combining marks, so a word of those scripts became
  its consonants: `हिन्दी` gave `ह`, `न`, `द`.

### 4.2 The fix

`core/ingest/lexical.py::Tokenizer` puts text in a normal form, folds case, normalizes again
(a fold can leave a text unnormalized), and takes runs that start with a letter or digit and
continue with letters, digits and combining marks. The current tokenizer is NFKC, `casefold`,
marks inside (T5 of experiment 1), chosen by the record's pre-declared rule: the most normalizing
arm that loses on no primary set. Its properties, each tested
(`tests/unit/test_lexical_index.py`) `[DERIVED]`:

- canonically equivalent texts give the same terms (NFC and NFD forms of every sample agree);
- compatibility-equivalent texts give the same terms (`ﬁ` and `fi`, `µ` and `μ`, `₂` and `2`);
- caseless matches give the same terms (`Straße` and `STRASSE`);
- a word with combining marks is one term; underscores still split;
- the legacy tokenizer is reproduced exactly by `LEGACY`, so an old index can still be read.

Only terms are normalized. The raw store, the chunk texts and every content hash stay on the
bytes as they came, so normalization changes no atom and no key; the record counts the atoms
that would merge if hashes were normalized: none under NFC, 24 of the corpus's 1,338,585 under
NFKC. The pattern with marks is written for speed (one BMP class read by table, the rest behind a
guard) and tested equal to the plain statement of the rule on random strings; it costs 1.4 times
the unmarked pattern's time, where one class holding every mark cost 3.3, and the tokenizer as a
whole runs at 31 million characters a second against the legacy one's 44 `[MEASURED: a bench on
SciFact's and NFCorpus's chunks]`.

### 4.3 The identity, the refusal, the re-derivation

A term is a function of the tokenizer, so a store of units is a function of the tokenizer that
made them. A query tokenized one way scored against units tokenized another matches the words
both ways agree on and silently misses the rest, and no score shows it. So, as the plane records
its embedder's fingerprint and refuses another (`GeometryMismatch`) `[ESTABLISHED:
core/stores/plane.py]`:

- **Identity.** `Tokenizer.identity` names every parameter the terms depend on, the Unicode
  database's version among them (character classes and case folds change between versions):
  `runs/NFKC/casefold/marks/unicode-17.0.0`.
- **Record.** The lexical store writes the identity in the transaction of its first landing. A
  store that holds versions and records nothing predates the record, and its units are `LEGACY`'s.
  An in-memory `LexicalIndex` carries its tokenizer, tokenizes its queries with it, and saves the
  identity beside its terms; a saved index without one loads as `LEGACY`'s, and one whose
  identity this process cannot reproduce (another Unicode database) is refused.
- **Refusal.** A store whose recorded identity is not its tokenizer's refuses to land and to
  score (`TokenizerMismatch`). The currency reads (`holds_current`, the version records) do not
  depend on terms and do not refuse, so a lazy landing's UNCHANGED check still answers for items
  that did not change, and a changed item is refused rather than landed under the new tokenizer
  beside old units.
- **Re-derivation.** The lexical backfill (`derive.derive_lexical`) resets a stale index (units,
  postings, version records and identity, in one transaction) and lands every active item again
  from the raw store under the current tokenizer, as re-embedding is the vector drain over a reset
  plane. The `embed` command and the daemon's `embed` job run the backfill before the vector
  drain, so the first drain after a deploy that changes the tokenizer re-derives the index; the
  reset and the backfill run in the one writer, so no landing reads the empty index between them.
  Tested on a palace: the store refuses, the backfill re-derives every item, a second backfill does
  nothing, and the catalog, versions and attestations are untouched
  (`tests/integration/test_two_phase_ingestion.py`).

**What a deploy re-derives.** The working instance embeds synchronously and has no lexical store
`[ESTABLISHED: no lexical.sqlite in its data directory]`, so nothing. The corpus instance's
in-memory index (`data/lexical/`) predates the record and was built on stage 1's branch by an
ASCII-only tokenizer (`[0-9a-z]+`, which drops every other letter) `[ESTABLISHED: core/ingest/
lexical.py at that branch's head]`; read on this branch it would load as `LEGACY`'s, which it is
not, so it should be rebuilt (`scripts/corpus.py lexical`, 2 to 3 minutes for 1.37 million units)
before it is read again.

## 5. Recommendations, by gain per cost

| rank | change | gain on the primary metrics | what adopting it re-derives |
|---|---|---|---|
| 1 | do not emit a chunk carried whole into the next one (the title-only chunk) | SciFact +0.033, NFCorpus +0.034, W +0.005 nDCG@10 (exploratory: confirm on a fresh set first) | the plane's occupancies and the lexical units of the items it touches; no text is embedded, since every remaining chunk keeps its text and atom; the corpus loses 84,255 of 1,369,944 vectors |
| 2 | the title in the document template | SciFact +0.029, NFCorpus +0.038, W link +0.017 nDCG@10 | every vector, with 1% to 12% more tokens: the working instance's 17,328 texts, the corpus's 1,338,585 atoms (stage 1's vector phase took 11.4 hours) |
| 3 | 256 dimensions with float16 rescoring, for the corpus's next stage | none lost; a third of the resident bytes | a pass over the stored vectors (truncation needs no embedder) |
| 4 | the tokenizer fix (built) | correctness; no ranking moves on these sets | the lexical index only, minutes, by the backfill |
| 5 | a chunk budget of 2,400 characters, after a larger W decides its recall | NFCorpus +0.021, W +0.031 nDCG@10, half the vectors | every vector, with fewer tokens and half the vectors |

Not recommended: another task prompt, late chunking, per-source or global quantile thresholds,
mutual nearest neighbours or CSLS for the semantic edges, stemming. Rows 1 and 2 both act on the
title-only chunk; their combination was not measured, and the second's gain on abstracts may be
partly the first's. `[INFERENCE]`, falsified for a row if a confirming run on a fresh set shows its
primary metrics worse than the live default.

## 6. Thresholds that set themselves

The direction is that no threshold is a constant tuned for one source. The data say the global
0.785 is not such a constant at the item grain: it sits below every source's own quantile, so the
edges are the 10 nearest everywhere and the cap does the work. Where a constant does fail is the
chunk grain, where short template-dominated atoms make OpenAlex and arXiv look dense; removing the
title-only chunk (rank 1) attacks that cause before any threshold does. Per-source quantiles are
the right form for a threshold when one is needed, and they are measured here; they lost on the
bridge reading, which rewards the hub edges they trim. `[DERIVED]`

## 7. Open questions

- **Pooling without the template.** Leaving the template's and the special tokens out of a chunk's
  mean (L1) raised nDCG@10 by 0.040 on SciFact and 0.030 on NFCorpus, W undecided. It needs a
  server that pools a span of the input, or the pooling-none mode and a mean on the client. Does it
  add to rank 1, which removes the chunks the template dominates most?
- **The combinations** of ranks 1, 2 and 5, which were measured one at a time.
- **What the semantic bridges measure.** Their excess over the null vanishes with the hubs. Read
  them against the store's own downstream measurements (walks, diffusion, rises) before any
  threshold is changed for them.
- **W's power.** 543 link questions leave recall@10 undecided at the margin; a W with more
  questions, or with judged relevance, decides the chunk budget.
- **Tokens for scripts without spaces** (Thai, Chinese, Japanese) and joiners inside words (the
  zero-width non-joiner of Persian), which the tokenizer does not segment or keep.
- **Late chunking beyond the slot.** The model's metadata claims a long context; windows longer
  than 2,048 tokens were not tried.

## Falsifiers

| id | pre-declared falsifier | outcome |
|---|---|---|
| F1 | every NFKC arm worse than the legacy tokenizer somewhere | held: no arm worse; T5 implemented |
| F2 | no budget no worse on both primary metrics with fewer vectors, or better on one and no worse on the other | broken: W's recall undecided for every larger budget; the live budget stays |
| F3 | an arm pays only if better on one primary metric and worse on none | the title template pays; late chunking (worse on W's recall) does not |
| F4 | an alternative prompt better on the set whose task it names and worse on none | none; the store keeps one prompt |
| F5 | 256 dimensions rescored no worse on all three primary metrics | held; recommended for the next stage |
| F6 | a calibrated rule with a higher excess ratio and as many pairs above their own bar | none; the global 0.785 stays |

## Cross-references

- docs/experiments/embedder-use-2026-11-08.md (the protocol, every table, the deviations) and its
  JSON; eval/embedder_use/ (the harness); tests/unit/test_embedder_use.py.
- core/ingest/lexical.py, core/stores/lexical.py, core/ingest/derive.py (the tokenizer, its
  identity and the re-derivation); tests/unit/test_lexical_index.py,
  tests/integration/test_two_phase_ingestion.py.
- docs/design-notes/dn-two-phase-ingestion.md (the lexical index and the drain),
  docs/design-notes/vector-membership-store.md (the fingerprint the identity mirrors),
  docs/experiments/corpus-stage1-2026-11-07.md (the battery and the bridges).
- papers/2026-11-08-embedder-use/paper.tex (the article).
