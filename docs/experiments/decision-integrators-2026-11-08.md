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

Pending.
