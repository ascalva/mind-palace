# Decision models as generic integrators: what typed questions add to the embedder

Date 2026-11-08. Harness `eval/decision_integrators.py`, questions `eval/decision_questions.py`,
the hosted client `edge/systemone.py`, tests `tests/unit/test_decision_integrators.py`, the design
`docs/design-notes/dn-decision-integrators.md`, the article
`papers/2026-11-08-decision-integrators/`. Aggregates in
`docs/experiments/decision-integrators-2026-11-08.json`. Requests, answers and vectors stay
outside the repository.

## Question

An auto-integrator turns any raw input into structure without code written for one domain. The
embedder is one: every chunk gets a vector, and so every pair a similarity. Similarity cannot say
whether a passage supports a claim or contradicts it. A decision model answers typed questions
about supplied state with probabilities (a Choice among options, a Noul for the probability that a
statement is true, a Score on described levels). With the questions held as declared, versioned
data, it could attach typed meaning to any node or edge. Can it be a second generic integrator
beside the embedder, and is the local model good enough to be the default?

## Pre-declaration

This section was committed before any benchmark was run; the results below it were added after.

### Models

- **Local**: `tev1:0.8b` (752 M parameters, BF16, Ollama's MLX runner, weights digest
  `b661d565…`), at `127.0.0.1:11434/v1/systemone`. Its Modelfile sets `num_ctx 2048`, and the
  endpoint takes no per-request window (no `options` field; a request over the window returns
  400, "input is never truncated"; verified). The window was raised without restarting any server
  by a derived tag, `tev1-ctx8192`, made with `ollama create` from a two-line Modelfile
  (`FROM tev1:0.8b`, `PARAMETER num_ctx 8192`): the same weights, template, system prompt,
  renderer, parser and temperature. The local arm uses that tag; the control C1 measures that it
  answers as `tev1:0.8b` does. Ollama counts the state once per question (`usage.input_tokens`).
- **Hosted**: TypeSafe's Jev, `jev-1.14.0`, through `edge/systemone.py`, a process of its own
  that reads the key from the Keychain at start and stops at $1.50 of a $2.00 grant
  ($0.042 per million input tokens). Only public benchmark text is written for it.
- **Embedder**: EmbeddingGemma-2 (Q8_0, 768 dimensions) on the stack's server
  (`127.0.0.1:8081`), one stream of 32 behind the corpus runner's gate, in the embedder bench's
  formats: documents `title: … | text: …` cut at 2,000 characters, queries `task: fact checking |
  query: …` (SciFact) or `task: question answering | query: …`.

The decision model sees a passage cut at 6,000 characters (the cuts are counted); the embedder
sees it cut at 2,000, the bench's cut, which its batch limit requires.

### Data

1. **Polarity.** AllenAI's original SciFact release (`data.tar.gz`, sha256 `11c62128…`):
   every labelled (claim, cited abstract) pair of train and dev. SUPPORT is `supports`,
   CONTRADICT is `contradicts`, and a cited abstract without evidence is `says_nothing` (claims
   without evidence, and cited abstracts outside a claim's evidence). Train: 919 pairs (370, 194,
   355); dev: 339 (138, 71, 130). Test labels are hidden and not used. State: `{"claim",
   "passage": {"title", "text"}}`.
2. **Topic.** arXiv items of the corpus instance (read-only). The stored item holds the title and
   abstract only; the category is recovered from the source's own record of the item
   (`sources/arxiv/meta/items.jsonl`, arXiv's listing), joined by arXiv id. The ground truth is
   the first listed category's archive. Of 20 archives, the 13 with at least 70 items are kept;
   60 items each by a seeded draw, 780 in all. State: `{"document": {"title", "text"}}`.
3. **Kind.** Stack Exchange posts of the corpus instance (cs, cstheory, datascience), 100
   questions and 100 answers per site by a seeded draw, the type from the post's record. The
   stored post begins with its title or with "Answer to: <title>" and a question ends with a
   "Tags:" line; both name the kind, so the model sees the body without them. State:
   `{"text"}`.
4. **Composition (re-ranking).** BEIR SciFact (300 test claims, the dev claims above, 5,183
   abstracts) and NFCorpus (323 test queries, 3,633 documents), local parquet. The embedder ranks
   the whole collection; the decision model judges each of the top 20.
5. **Contradiction mining.** The SciFact run of 4: every (dev claim, top-20 neighbour) pair,
   6,000 in all; a pair labelled CONTRADICT is a hit (71 such pairs exist in dev, some outside the
   top 20). SciFact labels only cited abstracts, so an uncited neighbour counts as a miss: the
   precision measured is a lower bound.
6. **Question-to-answer linking.** 300 Stack Exchange questions with answers (seeded), and a
   pool of every answer to them and to 300 other questions; for each question the embedder's 10
   nearest answers in the pool are judged. The ground truth is the answer's parent.
7. **Duplicates.** 200 pairs of questions linked as duplicates (seeded); for each, a negative:
   the first question's nearest neighbour among the same posts that is not linked to it.
8. **Question discovery.** SciFact pairs again: the train claims split 60/40 by a seeded draw
   into fit and check rows, dev held out.

### Questions

All wording is in `eval/decision_questions.py`, version `2026-11-08.1`; every result names the
digest of its question set. Polarity: a Choice over supports / contradicts / says nothing (the
citation-check cookbook's), the same Choice with its options reversed (the order control), and
three Nouls: supports, contradicts, and the companion "does the passage report a finding on what
the claim asserts". Relevance (NFCorpus): "Does the passage contain an answer to the query?" and
"Does the passage address the subject of the query?". Kind: "Is the writer of the text asking a
question?" and a Choice over five kinds of text. Reply: "Does the reply answer the question?".
Equivalence: "Do the two posts ask the same question?". Subject: a Choice over the archives, and
its reverse. Discovery: 20 candidates drafted from the generic families (relatedness, evidence,
agreement, direction, negative results, certainty, the claim's own form), plus the polarity
Choice.

### Arms

| benchmark | decision-model arms | baselines |
|---|---|---|
| polarity | Choice (primary); Noul product rule (supports alone, contradicts alone, neither, renormalized); companion rule; reversed Choice | embedder: a three-class logistic regression on the cosine, fit on train; majority class |
| topic | Choice (primary); reversed Choice | embedder kNN, k = 10, leave-one-out on the 780 items |
| kind | Noul (primary); the kind Choice's "asks a question" | a question mark in the body; embedder kNN, k = 10 |
| re-ranking | the Noul's order (SciFact: the companion Noul; NFCorpus: "contains an answer"), ties in the embedder's order; reciprocal rank fusion (k = 60) of both orders; the secondary question's orders | the embedder's order |
| mining | P(contradicts) of the Choice (primary); the contradicts Noul; the product rule | cosine order; random order |
| linking | the Noul's order; fusion | the embedder's order |
| duplicates | the Noul | cosine |
| discovery | greedy forward selection on check-row log loss: a candidate is kept if it lowers it by at least 0.005 nats, at most 6 kept; the kept set scored once on dev | the embedder alone; the embedder and the polarity Choice; all 21 candidates |

### Metrics

Accuracy; macro-F1 over the classes in the ground truth; the multiclass Brier score; log loss;
expected calibration error over 10 equal bins of the top-label probability (for a binary task
also of the positive class's probability) with the reliability curve's data; AUROC where binary;
nDCG@10 with graded relevance (the embedder bench's formula); MRR@10; average precision and
precision at k. Intervals are 95% percentile bootstraps (2,000 draws) over claims for SciFact
pairs, over queries for re-ranking and linking, over items elsewhere. Input tokens per request,
local seconds per request (one stream, with the share of 5-second samples in which the embedder
served another caller), and the hosted cost of a million requests at the measured mean.

### Falsifiers

- **F1, similarity is blind to polarity.** If the cosine's AUROC for supports against contradicts
  on dev exceeds 0.60 with its interval above 0.5, the premise fails on this benchmark.
- **F2, a typed question adds what similarity lacks.** If a model's Choice macro-F1 minus the
  embedder arm's on dev has an interval that reaches 0, the premise fails for that model.
- **F3, calibration.** A model whose polarity Choice has ECE above 0.15 on dev does not give
  calibrated probabilities there.
- **F4, order.** A Choice whose top answer flips under reversed options on more than 10% of
  items is order-sensitive.
- **F5, topic.** If the Choice's accuracy minus kNN's has an interval below 0, the embedder with
  labelled neighbours carries what the Choice gives.
- **F6, kind.** If the Noul's AUROC minus the question mark's has an interval reaching 0, code
  decides this family as well as the model.
- **F7, composition.** If a model's re-ranked nDCG@10 minus the embedder's has an interval
  reaching 0, the composition adds nothing on that collection. Control C3: the embedder's own
  nDCG@10 reproduces the embedder bench (0.849 SciFact, 0.367 NFCorpus) within 0.01, or the
  comparison is withheld.
- **F8, mining.** If precision at 50 of P(contradicts) does not exceed the cosine order's, the
  polarity question finds contradictions no better than similarity.
- **F9, linking and duplicates.** An interval of the decision model minus the embedder (MRR@10;
  AUROC) that reaches 0 means no gain there.
- **F10, discovery.** If the kept set's held-out log-loss gain over the embedder has an interval
  reaching 0, the kept questions do not pay on unseen rows.
- **C1, the context tag.** On 60 train pairs, the tag and `tev1:0.8b` agree on the Choice's top
  answer for at least 95% and differ by at most 0.02 (median) per probability, or the local
  results are the tag's alone. **C2, repeatability.** The same 60 requests sent again agree on
  the top answer for at least 95%, per arm.

**The default bar.** The local model is good enough to be a family's default integrator if, on
that family's benchmark, (D1) its primary arm beats the embedder baseline with an interval above
0, (D2) its ECE is at most 0.10, and (D3) its primary metric reaches at least 0.8 of the hosted
model's. D1 without D2 makes it a ranker whose order can be used and whose probabilities cannot.

### Commands

    uv run python -I -m eval.decision_integrators <benchmark> --out <dir> --arms local,hosted \
        --scifact <SciFact data dir> --corpus <corpus instance root>

with `<benchmark>` in `controls`, `polarity`, `rerank`, `topic`, `kind`, `linking`,
`duplicates`, `discovery`, then `report`. Seeds are fixed in the harness (`SEED = 20261108`).

## Results

### Conditions, spend and deviations

The runs took place from 2026-11-08 22:29Z to 2026-11-09 02:14Z. The hosted arm spent **$0.7396 of its $1.50 stop**
(17,609,844 input tokens over 19,366 requests, including 60 repeats), all of it public benchmark
text; the ledger is `hosted-ledger.json` beside the answers. The stack's embedder was shared with
another study for the whole run: during local polarity the 5-second sampler saw it serving another
caller in 86% of samples, and the load average stood at 4. No embedder timing is claimed, and the
local seconds below were measured with the embedder serving that caller.

Deviations from the pre-declaration, none of which changes a question, a sample or a metric:

1. The embedder's batch was 32 for the arXiv and Stack Exchange kind vectors and 64 (the corpus
   runner's measured default) for the rest, to shorten round trips on the busy server. One
   stream throughout.
2. The first hosted linking attempt sent question texts to the embedder uncut; one was longer
   than the embedder's batch, the server refused it and the gate retried. The attempt was stopped
   before any decision-model request; queries are now cut at 2,000 characters like documents.
3. Local polarity ran as one stream (its seconds are single-stream latency). The later local
   benchmarks ran with two or three requests in flight, measured to raise throughput by about 1.7
   on an idle GPU, so their seconds are not latency; the controls' repeat pass is one stream. The
   local kind, subject, reply and equivalence runs used a second process with its own answer file
   and the same cached vectors; the two answer files were joined after both had stopped.
4. Three readings were added after the first answers were read and are labelled post hoc: topic's
   accuracy against any archive an item is listed in; duplicates without the pairs that involve a
   canonical post; and SciFact re-ranking split by whether the claim has evidence. Each is
   computed by the harness from the same answers.

### Controls

- **C3 holds**: the embedder's own nDCG@10 is 0.849 on SciFact and 0.368 on NFCorpus, against the
  embedder bench's 0.849 and 0.367.
- **C2 holds for the hosted model**: the same 60 requests sent again agreed on the Choice's top
  answer 59 times (0.983), with a median absolute difference of 0 and a largest of 0.08 per
  probability. For tev1 the 60 requests, sent again
  after about 14,000 others, agreed 60 times, with a median difference of 0.0017 per probability
  and a largest of 0.016.
- **C1 holds**: on the same 60 pairs the `tev1-ctx8192` tag and `tev1:0.8b` itself agreed on the
  Choice's top answer 60 times; the median difference per probability was 0.004 (Choice) and
  0.004 (Nouls), the largest 0.029, and the base tag refused none of the 60.

### Polarity (SciFact dev, 339 pairs)

| arm | accuracy | macro-F1 (95% CI) | Brier | ECE | AUROC supports vs contradicts |
| --- | --- | --- | --- | --- | --- |
| tev1 0.8B: Choice | 0.484 | 0.386 [0.316, 0.449] | 0.767 | 0.354 | 0.854 |
| tev1 0.8B: Nouls, product rule | 0.552 | 0.492 [0.431, 0.545] | 0.594 | 0.193 | 0.851 |
| tev1 0.8B: Nouls, companion rule | 0.525 | 0.453 [0.403, 0.504] | 0.600 | 0.092 | |
| tev1 0.8B: Choice, options reversed | 0.493 | 0.395 [0.323, 0.459] | 0.766 | 0.353 | |
| Jev 1.14: Choice | 0.838 | 0.835 [0.792, 0.873] | 0.238 | 0.078 | 0.974 |
| Jev 1.14: Nouls, product rule | 0.850 | 0.847 [0.806, 0.886] | 0.228 | 0.040 | 0.974 |
| Jev 1.14: Nouls, companion rule | 0.864 | 0.864 [0.823, 0.900] | 0.212 | 0.049 | |
| Jev 1.14: Choice, options reversed | 0.841 | 0.837 [0.794, 0.876] | 0.248 | 0.073 | |
| embedder: logistic regression on the cosine (fit on train) | 0.454 | 0.319 [0.273, 0.364] | 0.653 | 0.124 | 0.536 [0.424, 0.638] |
| majority class | 0.407 | 0.193 | 0.643 | 0.004 | |

The train split (919 pairs) gives the same picture: tev1's Choice 0.367 and Nouls 0.451 macro-F1,
Jev's 0.841 and 0.854. For evidence either way against nothing, the AUROCs are 0.666 (cosine),
0.760 and 0.794 (tev1's Choice and companion Noul), 0.942 and 0.949 (Jev's).

- **F1 survives: similarity is blind to polarity.** The cosine's AUROC for supports against
  contradicts is 0.536, interval [0.424, 0.638]. It separates evidence from nothing somewhat
  (0.666), not one polarity from the other.
- **F2 survives for Jev and fires for tev1's Choice.** Jev's Choice exceeds the embedder arm's
  macro-F1 by an interval of [0.459, 0.574]. tev1's Choice (0.386) against the embedder's 0.319
  has an interval of [−0.019, 0.148], which reaches zero: on the declared primary arm the local
  model does not add polarity. Its answers carry the signal (AUROC 0.854 for supports against
  contradicts, against the cosine's 0.536), but its Choice puts most mass on `supports` whatever
  the pair (298 of 339 pairs); the Noul product rule recovers part of it (macro-F1 0.492).
- **F3 survives for Jev (ECE 0.078) and fires for tev1 (0.354).**
- **F4 survives for both**: the reversed options change the top answer on 2.6% (Jev) and 2.9%
  (tev1) of pairs.
- Jev's three-Noul companion rule is the best arm (macro-F1 0.864, ECE 0.049).

### Composition: the embedder proposes, the decision model judges

| collection | arm | embedder | judged (95% CI of the difference) | fused | judged by the secondary question |
| --- | --- | --- | --- | --- | --- |
| SciFact | tev1 0.8B | 0.849 | 0.636 [−0.252, −0.173] | 0.784 [−0.088, −0.042] | 0.630 |
| SciFact | Jev 1.14 | 0.849 | 0.830 [−0.049, 0.013] | 0.850 [−0.016, 0.016] | 0.818 |
| NFCorpus | tev1 0.8B | 0.368 | 0.275 [−0.115, −0.073] | 0.340 [−0.041, −0.017] | 0.294 |
| NFCorpus | Jev 1.14 | 0.368 | 0.414 [0.033, 0.061] | 0.400 [0.025, 0.040] | 0.416 |

nDCG@10 over 300 SciFact and 323 NFCorpus queries; the shortlist holds a relevant document for
95.7% and 80.5% of them.

- **NFCorpus: F7 survives for Jev.** Judging the embedder's top 20 with "Does the passage contain
  an answer to the query?" raises nDCG@10 from 0.368 to 0.414 (+0.047, [0.033, 0.061]); the
  fused order gains +0.032 and the secondary question +0.048.
- **SciFact: F7 fires for Jev.** The judged order scores 0.830 against the embedder's 0.849
  ([−0.049, 0.013]); the fused order is level (0.850). Reading the losses explains it (post hoc):
  of BEIR's 300 SciFact test claims, 112 have no evidence in the release, and BEIR marks their
  cited abstract relevant anyway. The companion Noul asks whether a passage decides the claim, and
  for those abstracts it correctly says no. On the 188 claims with evidence the judged order
  scores 0.940 against 0.920; on the 112 without, 0.646 against 0.731. The question measured
  evidence, the benchmark measured citation.
- **tev1: F7 fires on both collections.** Its judged orders lose 0.21 (SciFact) and 0.09
  (NFCorpus) of nDCG@10; fusion halves the loss and does not remove it. On SciFact's claims with
  evidence it scores 0.740 against the embedder's 0.920 (post hoc): the loss is not the
  benchmark's labels but the small model's judgment.

### Contradiction mining (SciFact dev, 6,000 neighbour pairs, 71 labelled contradictions)

| arm | ranker | average precision | P@10 | P@25 | P@50 (95% CI) | P@100 |
| --- | --- | --- | --- | --- | --- | --- |
| tev1 0.8B | P(contradicts), Choice | 0.066 | 0.300 | 0.160 | 0.140 [0.040, 0.220] | 0.100 |
| tev1 0.8B | contradicts Noul | 0.102 | 0.400 | 0.240 | 0.200 [0.060, 0.300] | 0.120 |
| Jev 1.14 | P(contradicts), Choice | 0.465 | 0.700 | 0.480 | 0.420 [0.340, 0.680] | 0.410 |
| Jev 1.14 | contradicts Noul | 0.430 | 0.500 | 0.440 | 0.460 [0.320, 0.640] | 0.410 |
| embedder | cosine | 0.155 | 0.100 | 0.080 | 0.220 [0.080, 0.380] | 0.200 |
| | random | 0.013 | 0.000 | 0.040 | 0.040 [0.000, 0.100] | 0.020 |

All 71 labelled contradictions are among the embedder's top 20, so the embedder finds the pairs
and cannot say which of them contradict: ranked by cosine, 22% of the top 50 are labelled
contradictions; ranked by Jev's P(contradicts), 42%, and average precision rises from 0.155 to
0.465. **F8 survives for Jev.** Since SciFact labels only cited abstracts, an uncited neighbour
that does contradict counts as a miss, so these precisions are lower bounds. **F8 fires for tev1**: its contradiction ranking finds more than the cosine in the
first ten (0.3 to 0.4 against 0.1) and fewer by fifty (0.14 to 0.20 against 0.22).

### Subject (780 arXiv items, 13 archives)

| arm | accuracy | macro-F1 | Brier | ECE | top-3 | order flips | any listed archive (post hoc) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| tev1 0.8B: Choice | 0.321 | 0.305 | 1.037 | 0.417 | 0.595 | 0.262 | 0.532 |
| Jev 1.14: Choice | 0.526 | 0.532 | 0.643 | 0.163 | 0.832 | 0.081 | 0.764 |
| embedder: kNN, k = 10 | 0.558 | 0.550 | 0.590 | 0.038 | | | 0.696 |

Chance is 1/13 = 0.077.

**F5 survives** (Jev's accuracy minus kNN's has the interval [−0.077, 0.009], which is not below
zero): a zero-shot Choice over archive names matches a kNN that needs 779 labelled neighbours.
Read item by item, the errors are mostly defensible: 555 of the 780 items are cross-listed, and
51% of Jev's errors name an archive the item is itself listed in (`stat.ML` with `cs.LG` answered
as computer science, `quant-ph` with `cs.CC` as computer science). Counted against any listed
archive (post hoc), Jev reaches 0.764 and kNN 0.696. The Choice is overconfident here (ECE 0.163).
For tev1 **F5 fires** (its accuracy minus kNN's has the interval [−0.280, −0.199])
and **F4 fires**: with 13 options, reversing their order changes its top answer on 26% of items.

### Kind (600 Stack Exchange posts, 300 of them questions)

| arm | accuracy | Brier | ECE (positive class) | AUROC |
| --- | --- | --- | --- | --- |
| tev1 0.8B: Noul | 0.512 | 0.505 | 0.288 | 0.898 |
| tev1 0.8B: kind Choice, `asks_a_question` | 0.713 | 0.378 | 0.090 | 0.810 |
| Jev 1.14: Noul | 0.957 | 0.055 | 0.056 | 0.996 |
| Jev 1.14: kind Choice, `asks_a_question` | 0.985 | 0.026 | 0.011 | 0.996 |
| embedder: kNN, k = 10 | 0.602 | 0.471 | 0.116 | 0.685 |
| a question mark in the body | 0.848 | | | 0.848 |

**F6 survives for Jev**: its Noul exceeds the question-mark rule's AUROC by [0.120, 0.176]. The
kind Choice's `asks_a_question` is the better arm (accuracy 0.985, ECE 0.011). The borderline
posts are requests phrased as statements of need, without a question mark (a writer looking for
sources, a writer who wants to prove a property), where the Noul hesitates and the Choice leans
to asking.
Answers spread over `makes_a_claim` (0.58) and `gives_an_instruction` (0.32). For tev1 **F6 survives, narrowly**: its Noul's AUROC exceeds the question mark's by
[0.011, 0.084], and it orders posts well (0.898) while placing nearly all of them above 0.5 (293
of 300 answers): an order that can be used and a probability that cannot.

### Reply: question to answer linking (300 questions, a pool of 889 answers)

| arm | MRR@10 | hit@1 | MRR minus the embedder's (95% CI) | AUROC over the pairs |
| --- | --- | --- | --- | --- |
| embedder | 0.905 | 0.862 | | |
| tev1 0.8B: judged | 0.719 | 0.579 | [−0.231, −0.141] | 0.799 |
| tev1 0.8B: fused | 0.865 | 0.790 | [−0.068, −0.013] | |
| Jev 1.14: judged | 0.981 | 0.966 | [0.049, 0.105] | 0.984 |
| Jev 1.14: fused | 0.936 | 0.893 | [0.020, 0.044] | |

**F9 survives for Jev**: judging the embedder's ten nearest answers raises MRR@10 from 0.905 to
0.981 ([0.049, 0.105]) and hit@1 from 0.862 to 0.966; 290 of the 300 questions have an answer in
the ten. Of the ten questions whose judged first answer is not their own, most are near ties
(0.92 against 0.91) with an answer written to a related question. For tev1 **F9 fires**: its judged order loses 0.19 of MRR@10.

### Equivalence: duplicate questions (200 linked pairs, 200 nearest non-linked)

| arm | accuracy | Brier | ECE (positive class) | AUROC | AUROC minus the cosine's (95% CI) | AUROC without canonical-post pairs (post hoc) |
| --- | --- | --- | --- | --- | --- | --- |
| tev1 0.8B: Noul | 0.585 | 0.491 | 0.114 | 0.653 | [0.091, 0.207] | 0.734 |
| Jev 1.14: Noul | 0.662 | 0.517 | 0.279 | 0.869 | [0.313, 0.414] | 0.935 |
| embedder: cosine | | | | 0.504 | | 0.585 |

The negatives were chosen as the embedder's nearest non-linked neighbours, so the cosine is near
chance by construction (0.504) and **F9 survives** trivially; the informative number is Jev's AUROC
of 0.869 on pairs the embedder cannot tell apart. Its accuracy at 0.5 is 0.662: it calls 133 of
the 200 duplicates different. Read pair by pair, 67 of the 200 involve one of 8 canonical posts
(each in three or more sampled pairs: general questions on how to analyse an algorithm's running
time or how to solve recurrences), against which the site closes specific questions. There Stack Exchange's "duplicate" means "covered by the general question";
Jev, reading "ask the same question" literally, gives those pairs a median of 0.07 and none above
0.5. Without them (post hoc) its AUROC is 0.935. The label measured a relation the question did
not ask. tev1 shows the same split, weaker (0.653 overall, 0.734 without the canonical posts).

### Question discovery (SciFact; 554 fit rows, 365 check rows, 339 held out)

| held-out arm (339 dev pairs) | tev1 0.8B log loss | tev1 macro-F1 | Jev 1.14 log loss | Jev macro-F1 |
| --- | --- | --- | --- | --- |
| class prior | 1.061 | 0.193 | 1.061 | 0.193 |
| embedder alone | 1.075 | 0.319 | 1.075 | 0.319 |
| embedder and the polarity Choice | 0.823 | 0.625 | 0.426 | 0.855 |
| embedder and the kept questions | 0.772 | 0.626 | 0.399 | 0.856 |
| the kept questions alone | 0.736 | 0.670 | 0.394 | 0.855 |
| embedder and all 21 candidates | 0.768 | 0.641 | 0.381 | 0.866 |

Kept, in order of selection: for Jev, the polarity Choice, `names_claim_entities`,
`background_only`, `opposite_direction`; for tev1, the polarity Choice, `relatedness_level`,
`support_level`, `null_finding`, `denies_part`, `reports_on_relationship` (the cap of six).

- **Jev.** Selection kept the declared polarity Choice first (+0.675 nats on check rows), then
  "mentions the main things the claim is about" (+0.025), "mentions the claim's subject only in
  passing" (+0.016) and "an effect in the opposite direction" (+0.011), and refused the next
  (+0.0048, under the 0.005 bar). On the held-out rows the kept set lowers log loss from the
  embedder's 1.075 to 0.399, a gain of 0.675 nats ([0.569, 0.786]): **F10 survives**. The
  embedder alone is worse than the class prior on held-out rows (1.075 against 1.061), and its
  Shapley share is −0.007 nats against the Choice's 0.293: for polarity it carries nothing. All
  21 candidates together reach 0.381, so the bar was conservative here rather than overfit. The
  claim-only questions (hedged, time-bound, causal) gained under 0.012 each on their own.
- **tev1.** Selection kept six questions, the cap, each above the bar on check rows; on held-out
  rows they lower log loss from 1.075 to 0.772, a gain of 0.303 nats ([0.210, 0.389]): **F10
  survives** for the small model too. With weaker single answers, more questions pay: the scores
  (`relatedness_level`, `support_level`) and the negative-result question add what its Choice
  misses, and the kept questions without the embedder do best (0.736). The embedder's Shapley
  share is again below zero (−0.025 nats).

### Tokens, time and cost

| benchmark | tev1: input tokens a request (Ollama counts the state once per question) | tev1: seconds a request, median | Jev: input tokens a request | Jev: seconds a request, median | Jev: dollars per million requests |
| --- | --- | --- | --- | --- | --- |
| polarity (5 questions) | 2,752 | 0.72, one stream | 1,083 | 0.10 | 45 |
| re-ranking, SciFact (5) | 2,595 | 2.81, three in flight | 1,051 | 0.10 | 44 |
| re-ranking, NFCorpus (2) | 982 | 1.31, three in flight | 726 | 0.10 | 30 |
| subject (2 Choices of 13 options) | 1,400 | 3.28, two in flight | 1,257 | 0.10 | 53 |
| kind (2) | 837 | 2.67, two in flight | 710 | 0.10 | 30 |
| reply (1) | 603 | 2.53, two in flight | 793 | 0.10 | 33 |
| equivalence (1) | 555 | 2.93, two in flight | 749 | 0.09 | 31 |
| discovery (20) | 10,472 | 7.01, three in flight | 1,232 | 0.10 | 52 |

Only the polarity row's local seconds are single-stream latency, and they were measured while the
embedder served another caller; the others are wall time per request with several in flight on a
shared GPU. Jev's seconds include the network. Jev reads the state once a request, so twenty
questions cost it 1,232 tokens where Ollama counts 10,472.

### What the individual answers show

- **Jev's polarity errors** fall on two kinds of pair: labels a careful reader could dispute (a
  claim that PGE2 promotes tumor growth by altering DNA-repair genes, against an abstract titled
  "promotes intestinal tumor growth via DNA methylation", labelled without evidence and answered
  supports), and claims that turn on a number ("decreased by 10% in women since 1979"), a known
  weak spot of these models.
- **tev1's polarity errors** are mostly its prior: `supports` for 298 of 339 pairs. Its confident
  errors include negated claims ("compression stockings did not reduce deep vein thrombosis"
  against a trial that found no reduction), which it reads as contradictions.
- **The benchmarks' labels are not always the questions' relations**, and reading answers is how
  this showed: arXiv's primary archive against cross-lists, BEIR's cited-is-relevant against
  evidence, Stack Exchange's closed-as-duplicate against asks-the-same-question. In each case the
  typed question answered what it asked.

### The default bar, read

| family | D1 beats the embedder (interval above 0) | D2 ECE at most 0.10 | D3 at least 0.8 of Jev | reading |
| --- | --- | --- | --- | --- |
| polarity (Choice) | no: [−0.019, 0.148] | no: 0.354 | no: 0.386 against 0.835 | not the default |
| subject | no: below kNN | no: 0.417 | no: 0.321 against 0.526 | not the default |
| kind (Noul) | yes: 0.898 against kNN's 0.685 and the question mark's 0.848, [0.011, 0.084] | no: 0.288 | yes: 0.898 against 0.996 | a ranker: its order, not its probabilities |
| re-ranking (relevance) | no: loses on both collections | | no | not the default |
| reply | no: loses 0.19 MRR | | no | not the default |
| equivalence | yes against the cosine, by construction | no: 0.114 | no: 0.653 against 0.869 | not the default |

**The local 0.8-billion-parameter model is not good enough to be the default integrator for any
family measured here.** Its answers carry signal (AUROC 0.85 for polarity, 0.90 for kind), but its
Choices lean on one option, its probabilities are not calibrated, and its judgments lower the
embedder's rankings. Jev clears the bar's D1 and D2 for polarity (0.835, ECE 0.078), kind (0.996,
0.011 for the Choice), reply (+0.076 MRR) and NFCorpus re-ranking (+0.047 nDCG@10), and ranks
equivalence (0.869) without calibrated probabilities (0.279).

### Families to ship first

Generic families, in the order the measurements support:

1. **Kind**, as the kind Choice's `asks_a_question` with the Noul beside it: the clearest answer of
   the study (Jev 0.996 AUROC, ECE 0.011), cheap (one short request), and the local model can rank
   with it.
2. **Polarity**, the Choice and the companion Noul: what similarity cannot give (cosine 0.536,
   Jev 0.974 for supports against contradicts), the producer for signed edges and contradiction
   candidates (mining's average precision 0.155 to 0.465). Hosted only where allowed.
3. **Reply**, "Does the reply answer the question?", judging the embedder's shortlist (MRR 0.905
   to 0.981).
4. **Relevance** judging of the embedder's shortlist, on a scale of its own, where what the store
   calls relevant is an answer rather than a citation (NFCorpus +0.047 nDCG@10).

Equivalence needs a "covered by" variant, measured on held-out data before it ships; subject stays
a benchmark.
