---
type: design-note
id: dn-decision-integrators
track: query-language
status: draft                  # provenance description, never a gate; the merge is ratification
implementation: design-only    # nothing built in the store; the harness eval/decision_integrators.py measured the design on public data
created: 2026-11-08
updated: 2026-11-08
links:
  - docs/experiments/decision-integrators-2026-11-08.md   # the measurements this note reads, arms and falsifiers declared before the runs
  - eval/decision_integrators.py                          # the harness: local and hosted arms
  - eval/decision_questions.py                            # every question, as declared data
  - edge/systemone.py                                     # the hosted decision model's client, a process of its own
  - papers/2026-11-08-decision-integrators/paper.tex      # the article
  - docs/design-notes/dn-scale-and-attribution.md         # SCL-3: a source's contribution, the Shapley value
  - docs/design-notes/vector-membership-store.md          # the plane: a derived field keyed by content and the embedder's identity
  - docs/design-notes/supersession-lifecycle.md           # §6: supersession candidates, surfaced and never certified
  - docs/design-notes/dn-query-sentence-algebra.md        # the carrier a kind would scope; QSA-9's signed edges and camps
supersedes: null
superseded_by: null
warrant: null
---

# Decision integrators: typed meaning beside the vector

> Composed on the decision-integrator session (Opus 5.5, 2026-11-08). Agent-drafted, filed
> `draft` on a branch; the merge is ratification. Nothing is built in the store and no `core/`
> code changes. Every nontrivial claim carries a grade: `[MEASURED]` is a figure of
> `docs/experiments/decision-integrators-2026-11-08.md`; `[ESTABLISHED]` is a ratified note's,
> a cited result's or a fact read off the repository; `[DERIVED]` is argued here from those;
> `[INFERENCE]` is a design call with a named falsifier. Two companion designs are open as pull
> requests and are cited by number: two-phase ingestion (dn-two-phase-ingestion, PR #83: the
> embed drain and the laws ING-19 to ING-21) and the utility field (dn-utility-field, PR #84:
> bounded, decayed weights, UTL-1 to UTL-6). This note depends on neither to merge.

## 1. Purpose and scope

### 1.1 The requirement

An auto-integrator turns any raw input into structure without code written for one domain. The
embedder is one: every chunk gets a vector, and so every pair of texts a similarity and the
store a semantic backbone `S`. The palace's older integrators were tailor-made: the transcript
integrator turns session logs and commits into causal edges by rules written for those events,
which is why they do not generalize. A similarity is one number with one meaning, nearness, and
it cannot say whether a passage supports a claim, contradicts it, or merely shares its words.

A decision model answers typed questions about supplied state with probabilities: a Choice among
options, a Noul (the probability that a statement is true), a Score on described levels. If the
questions are generic families that apply to any text, held as declared, versioned data rather
than code, such a model can attach typed meaning to any node or edge: the kind of an item (a
claim, a question, an instruction), the polarity of an edge (supports, contradicts, says
nothing), whether a reply answers a question, whether two items ask the same thing. That is a
second generic integrator. This note designs the layer that holds its answers, says how they
feed the machinery the palace already has, proposes laws that generalize the embed drain's to
several derived fields, designs the loop above the integrators that decides what to ask, and
reports the measurements on public benchmarks that decide which families ship first and whether
the local model can be the default.

### 1.2 Decisions

1. **An integrator is a model identity and a question set; its answers are typed derived fields**
   beside the vector: a kind on a node, a polarity on an edge, each the full typed answer (the
   probabilities), keyed by `(item digest, integrator identity, question-set digest)` (§3, D1).
2. **A drain computes them, like the embed drain**: landing never waits, a missing answer is
   reported pending and never guessed, a change of question set is a new key (§3, D2).
3. **Questions are declared, versioned data** with a digest; no question reaches a model that is
   not in a declared set (§3, D3).
4. **Each integrator is a source whose contribution is attributed** by SCL-3's Shapley value
   over the arms that switch it on and off (§3, D4).
5. **Local by default; hosted only where an instance's configuration lets the data leave the
   machine**, default deny, never the default instance's private strata (§3, D5).
6. **Answers feed existing machinery** through typed producers with their own provenance: signed
   edges into the balance and frustration measures, polarity into supersession candidates, kinds
   into query scoping, judged relevance into re-ranking on a scale of its own (§3, D6).
7. **The model is chosen per family by measurement** against a declared bar (§3, D7).
8. **A question-discovery loop proposes, measures and retires questions** under four laws: kept
   only on held-out rows, bounded in number and budget, versioned and attributable, and never
   raised in weight without measured gain (§5).

### 1.3 Out of scope

Any change to `core/`, the plane, the edge store, the relation detector or the sentence algebra
(code is licensed at the merge); Lean proofs of the proposed laws (they carry falsifiers; the
proofs follow the ladder); the `elaborates` option of the polarity family, which no benchmark here
labels (§8, open); any domain taxonomy as a palace feature: arXiv's archives appear only as a
benchmark with ground truth (§7).

### 1.4 What is measured, what is open

Measured, on public data with ground truth, local and hosted, with the arms and falsifiers
declared before the runs (`docs/experiments/decision-integrators-2026-11-08.md`): polarity
(SciFact), the two integrators composed (re-ranking BEIR SciFact and NFCorpus), contradiction
mining among neighbours, subject (arXiv archives), kind (Stack Exchange question or answer), reply
(question to answer linking), equivalence (duplicate questions), and a question-discovery pilot.
Open (§8): the drain at the corpus's scale, the `elaborates` option, the loop's later steps, the
proofs.

## 2. What exists

**The vector as a derived field.** The plane keeps one atom per distinct chunk text, content
addressed, with the embedder's identity (model, document template, dimension) as its fingerprint;
a different identity is refused, and re-embedding is a reset and a drain.
`[ESTABLISHED: vector-membership-store A3, A4]` Two-phase ingestion (PR #83) makes the vector a
field with a key of its own, written by a drain after landing: an item is complete without its
vector (ING-19), the drain converges and is idempotent (ING-20), and a query never invents a
vector, reporting pending items instead (ING-21). `[ESTABLISHED: dn-two-phase-ingestion, PR #83]`

**Signed edges and their mathematics.** `core/stores/edges.py` holds the typed, signed edges the
cosine graph cannot carry (supports +1, contradicts −1, contextualizes +1 weaker), the input to
`core/kernel/complex/balance.py`: balance of the signed graph (LAP-5), frustrated triangles
(LAP-6), the magnetic fibers (BRG-7) and the camps a hypothetical signed edge keeps or breaks
(QSA-9). `core/relations.py` has two producers: authored properties (`contradicts:: [[…]]`) and an
interpreted detector that wakes the synthesis tier to label σ-backbone pairs with one word,
provenance `interpreted`, weight the pair's cosine. `[ESTABLISHED: read off the code]`

**Supersession candidates.** `s(C, D) = sim(C, D) · 1[contradiction(C, D)] · 1[t(D) > t(C)]`,
surfaced and sharpened, never certified: an owner's verdict demotes a note.
`[ESTABLISHED: supersession-lifecycle §6]`

**Attribution.** SCL-3: over the arms that switch sources on and off, the Shapley value is the
only efficient, symmetric, null-respecting, additive attribution; leave-one-out answers whether a
source is necessary, the Shapley value what share it carries. `[ESTABLISHED: dn-scale-and-
attribution §3.4]`

**Bounded weights.** The utility field (PR #84) updates a weight by decay toward a baseline at
rate `λ` and a clamped increment `|Δ| ≤ c`, so it stays in the box `|u − b| ≤ c/λ` (UTL-1), and
enters ranking only as a bounded multiplier (UTL-3). `[ESTABLISHED: dn-utility-field, PR #84]`

**Decision models on this machine.** `tev1:0.8b` (752 M parameters) is served by Ollama at
`/v1/systemone` with TypeSafe's request shape; the hosted Jev (`jev-1.14.0`) answers the same
shape. Ollama scores each question as its own prompt and counts the state once per question; Jev
reads the state once per request. Ollama's window is the loaded model's (`num_ctx 2048` in tev1's
Modelfile; the endpoint has no per-request window); the study raised it with a derived tag, and
measured that the tag answers as tev1 does (the record's C1). `[MEASURED]`

## 3. Decisions

### D1. The integrator layer

**An integrator** is a pair: a model identity (the model's name and the digest of its weights, or
the hosted model's versioned id) and a question set (a family's declared questions, with their
digest, `eval/decision_questions.py::digest`: sha256 over the questions, ids sorted, each
question's own order kept, since a Choice's option order is part of what the model reads). Two
integrators that differ in either are different sources.

**An answer is a typed derived field**, beside the vector and like it a function of the item's
bytes and an identity: a node field (the kind of an item) reads one item; an edge field (the
polarity between two items) reads an ordered pair. The field's value is the whole typed answer:
a Choice's probabilities, a Noul's probability, a Score's level probabilities, never a label cut
from them. The thresholds that turn a probability into an action live in code, in one table, and
the band between them is a state of its own, "unsettled", with its own row in the truth table.
`[INFERENCE; falsifier IF-1]`

**The key** is `(item digest, integrator identity, question-set digest)`; for an edge, the item
digest is the ordered pair's. An answer is never edited: a new question set or a new model is a
new key, and the old answers stay keyed by the old identity, as the plane's atoms stay keyed by
content. `[DERIVED from ING-19's identity rule]`

### D2. A drain like the embed drain

Answers are derived after landing, by a drain of the one writer, as vectors are under two-phase
ingestion: the drain lists the pending (item, integrator) keys, reads each item's bytes back by
digest, builds the state from them with the family's state builder (a pure function: the same
bytes give the same state), asks the integrator in batches, and lands each answer with its key
last. Landing never waits for it. A query that reads a field reports the items whose answer is
pending, as ING-21 reports a pending vector, and never reads a missing answer as a no: in the
harness, a failed request is an error row, counted and excluded, never an answer
(`tests/unit/test_decision_integrators.py::test_a_failed_request_is_never_read_as_an_answer`).
Edge fields are drained over candidate pairs only (§D6), never all pairs. `[DERIVED from ING-20,
ING-21]`

### D3. Questions as declared, versioned data

Every word a model is asked lives in one declared module (in the study, `eval/decision_questions.py`;
in the store, a declared question-set file per family), with a version and a digest, so every
stored answer names the exact questions that produced it. The wording follows the decision-model
vendor's guidance: one judgment per question, the subject named, option names that describe their
content, criteria that describe each outcome as a situation, a companion Noul beside a Choice
whose options may not fit. No question reaches a model unless it is in a declared set; a question
drafted by a model enters a declared set only through the discovery loop's gate (§5).
`[INFERENCE; falsifier IF-2]`

### D4. Each integrator a source, its contribution attributed

The embedder and each integrator are sources in SCL-3's sense: an arm is a configuration of
sources, and an integrator's value on a question battery is its Shapley value over the arms that
switch it on and off; leave-one-out says whether it is necessary. The discovery pilot computes
both on held-out SciFact rows, with the embedder and each kept question as players (§4.8).
`[DERIVED from SCL-3]`

### D5. Local by default, hosted only where allowed

The local decision model is the default integrator. A hosted model is a source only on an
instance whose configuration declares that its data may leave the machine (default deny), and
never for the default instance's private strata (the vault, the dialogue). The path is the
edge's own process (`edge/systemone.py`), which reads no store, takes its key from the Keychain
at start, and stops at a declared dollar limit kept in a ledger across runs; the caller writes
only text the instance's configuration allows. In the study, only public benchmark text was
written for the hosted arm. `[INFERENCE; falsifier IF-5]`

### D6. How answers feed the machinery that exists

- **Polarity into signed edges.** The polarity family is a producer for `core/stores/edges.py`
  beside the authored properties and the synthesis-tier detector: on a candidate pair from the
  σ-backbone, the decided label becomes an edge when its probability clears the upper threshold
  (0.7 to start), with provenance `interpreted` and weight `cosine × probability`; the unsettled
  band writes nothing and is counted. The signed edges then reach balance (LAP-5), the frustrated
  triangles (LAP-6) and the camps (QSA-9) unchanged. A typed, calibrated answer replaces a
  one-word label from the synthesis tier, at a small fraction of its cost.
- **Polarity into supersession candidates.** `s(C, D) = sim(C, D) · P(contradicts | C, D) ·
  1[t(D) > t(C)]`: the probability takes the indicator's place, so candidates rank by how sure the
  contradiction is. They are surfaced, never certified (supersession-lifecycle §6).
- **Kinds into query scoping.** A kind field is a filter on a sentence's carrier: only the items
  that ask a question, only the claims. An item whose kind is pending is reported as such and is
  neither kept nor dropped silently (ING-21's rule).
- **Judged relevance into re-ranking.** The composition measured in §4.2: the embedder proposes a
  shortlist, the relevance or reply family judges each candidate, and the judged order is
  reported on a scale of its own, labelled, never added to a cosine (ING-21's reason for keeping
  the lexical fallback apart).
- **Equivalence into near-duplicate candidates**, beside the cosine line, surfaced for the
  owner's verdict.

`[INFERENCE; falsifiers IF-3, IF-4]`

### D7. The model is chosen per family by measurement

The bar declared before the runs: the local model is a family's default integrator if, on that
family's benchmark, (D1) its primary arm beats the embedder baseline with an interval above zero,
(D2) its expected calibration error is at most 0.10, and (D3) its primary metric reaches 0.8 of
the hosted model's. D1 without D2 makes it a ranker whose order can be used and whose probabilities
cannot. A family whose local model fails D1 is hosted only where D5 allows, and otherwise stays
off. §4 reads the bar. `[MEASURED]`

## 4. Measurements

Every figure is from `docs/experiments/decision-integrators-2026-11-08.md`, which declared the
arms, falsifiers and the bar before the runs. Local is `tev1:0.8b` (752 M parameters); hosted is
`jev-1.14.0`; the embedder is EmbeddingGemma-2 on the stack's server. Hosted spend: $0.74 of a
$1.50 stop. `[MEASURED]`

| family (benchmark) | metric | tev1 0.8B | Jev 1.14 | embedder | other |
| --- | --- | --- | --- | --- | --- |
| polarity (SciFact dev, 339 pairs) | macro-F1 of the Choice | 0.386 | 0.835 | 0.319 (logistic on the cosine) | majority 0.193 |
| polarity | AUROC, supports against contradicts | 0.854 | 0.974 | 0.536 | |
| polarity | ECE of the Choice | 0.354 | 0.078 | 0.124 | |
| relevance, judging the top 20 (SciFact, 300) | nDCG@10 | 0.636 | 0.830 | 0.849 | fused with Jev 0.850 |
| relevance, judging the top 20 (NFCorpus, 323) | nDCG@10 | 0.275 | 0.414 | 0.368 | fused with Jev 0.400 |
| contradiction mining (6,000 neighbour pairs) | average precision | 0.066 | 0.465 | 0.155 | random 0.013 |
| subject (arXiv, 780, 13 archives) | accuracy | 0.321 | 0.526 | 0.558 (kNN, k = 10) | chance 0.077 |
| kind (Stack Exchange, 600) | AUROC | 0.898 | 0.996 | 0.685 (kNN) | question mark 0.848 |
| reply (300 questions) | MRR@10 of the judged top 10 | 0.719 | 0.981 | 0.905 | fused with Jev 0.936 |
| equivalence (400 pairs) | AUROC | 0.653 | 0.869 | 0.504 (cosine, near chance by construction) | |
| discovery (SciFact, held out) | log loss of the kept questions with the embedder | 0.772 | 0.399 | 1.075 | prior 1.061 |

**What it shows.** Similarity is blind to polarity (0.536, interval [0.424, 0.638]); a typed
question is not (Jev 0.974). The two integrators compose: the embedder finds every one of the 71
labelled contradictions in its top 20 and cannot say which they are, and Jev's P(contradicts)
lifts average precision from 0.155 to 0.465; Jev's judgment of the embedder's shortlist raises
reply MRR from 0.905 to 0.981 and NFCorpus nDCG@10 by 0.047. On SciFact's ranking it does not,
and the answers say why: BEIR marks a claim's cited abstract relevant even when the release labels
it without evidence (112 of 300 claims), and the question asked for evidence. Jev's probabilities
are calibrated where the task is clear (ECE 0.078 polarity, 0.011 kind) and not on the subject
Choice (0.163) or equivalence (0.279). Controls held: the 8192-token tag answers as `tev1:0.8b`
(60 of 60 top answers, median difference 0.004), both models repeat themselves (60 of 60; 59 of
60), and the embedder reproduces its bench (0.849, 0.368).

**The bar, read.** The local model fails it for every family: polarity (D1 fails: [−0.019,
0.148]; D2 fails: 0.354), subject (below kNN), relevance and reply (its judgments lower the
embedder's rankings), equivalence (D3: 0.653 against 0.869). For kind it passes D1 and D3 and fails
D2: a ranker whose order can be used (0.898) and whose probabilities cannot (293 of 300 answers
above 0.5). Its answers carry signal; its Choices lean on one option (`supports` for 298 of 339
pairs) and lose to option order with many options (26% flips over 13 archives). So the default for
private strata is no decision integrator today, except kind as an order; the hosted model clears
the bar for polarity, kind, reply and answer-style relevance where an instance allows it. The next
local candidate is tev1's 4-billion-parameter sibling, measured against the same bar on the same
answers' benchmarks (§8). `[MEASURED; INFERENCE, falsifier IF-1]`

**The labels are not always the questions.** Three benchmark labels measured a different relation
from the question asked: arXiv's primary archive against cross-lists (half of Jev's subject errors
name an archive the item is listed in), BEIR's cited-is-relevant against evidence, and Stack
Exchange's closed-as-duplicate against asks-the-same-question (67 of 200 duplicate pairs involve
one of 8 canonical posts that specific questions are closed against; without them Jev's AUROC is
0.935). Each was found by reading answers, and each is a reason to measure a family on more than
one source before it ships (IF-6).

**Families to ship first**, generic and in the order the measurements support: kind (the kind
Choice's `asks_a_question`, with the Noul beside it), polarity (the Choice and its companion Noul,
producer for signed edges and contradiction candidates), reply (judging the embedder's shortlist),
and relevance judging where the store's notion of relevance is an answer. Equivalence waits for a
"covered by" variant measured on held-out data.

## 5. Question discovery: the loop above the integrators

### 5.1 The loop

The integrators answer declared questions; something must decide which questions to declare.
The loop follows the feature-discovery pattern of the decision-model vendor's cookbook: a
proposer writes candidate questions, the decision model answers each for every row, a classical
model trained on the answers judges each change on rows the proposer never read, and the misses
on the rows it may read go back to the proposer. Here:

1. **Propose.** Candidates come from the generic families (relatedness, evidence, agreement,
   direction, negative results, certainty, the form of an item), instantiated on a family's state
   shape, or a local chat model drafts them from the family list and the misses on read rows. A
   drafted question names no row's words (the cookbook's rule: a question built on one row's
   wording looks tuned to that row).
2. **Screen.** A column that hardly varies across rows cannot separate anything and is dropped
   before it is scored.
3. **Measure.** Each candidate's gain is the fall in log loss, on check rows, of a model over the
   current features when the candidate's answers are added; the models are fit on other rows.
4. **Keep or retire** by the weight rule DSC-4, and read the series once on a held-out split.

### 5.2 What a question is worth

For the label `Y`, the current features `X` and a question's answers `A`, the Bayes-optimal
predictors' expected log losses differ by the conditional mutual information:
`E[−log p(Y | X)] − E[−log p(Y | X, A)] = H(Y | X) − H(Y | X, A) = I(Y; A | X)`. The fall in
held-out log loss of fitted models estimates it, biased down by misspecification. With the value
of a set of sources `v(S) = LL(∅) − LL(S)`, the Shapley value splits what the sources carry
together, the embedder among them, as SCL-3 splits any value. `[DERIVED]`

### 5.3 The guard rails

The four laws DSC-1 to DSC-4 of §6: kept only on held-out rows, bounded in number and budget,
versioned and attributable, never raised in weight without measured gain.

### 5.4 The pilot

On SciFact, twenty candidates drafted from the families before any answer was read, plus the
declared polarity Choice, all asked in one request per pair; the train claims split by a seeded
draw into 554 fit rows and 365 check rows, the 339 dev rows held out; a multinomial logistic
regression over the embedder's cosine and the kept questions; a candidate kept if it lowers
check-row log loss by at least 0.005 nats, at most six kept. `[MEASURED]`

- **Jev** kept the polarity Choice (+0.675 nats on check rows), "mentions the main things the claim
  is about" (+0.025), "mentions the claim's subject only in passing" (+0.016) and "an effect in the
  opposite direction" (+0.011), and refused the fifth (+0.0048). Held out, the kept set lowers log
  loss from the embedder's 1.075 to 0.399 ([0.569, 0.786] nats of gain). Shapley shares over the
  held-out rows: the Choice 0.293, the direction question 0.161, the entities question 0.131, the
  in-passing question 0.083, the embedder −0.007.
- **tev1** kept six, the cap: the Choice, the two Scores (relatedness, support), the negative-result
  question, "denies part" and "reports on the relationship"; held out, 1.075 to 0.772 ([0.210,
  0.389]). With weaker single answers, more questions pay, and the Scores carry what its Choice
  misses.
- In both, the claim-only questions (hedged, time-bound, causal, negative) add almost nothing to
  polarity, the embedder's share is at or below zero, and all 21 candidates together do slightly
  better than the kept set on held-out rows (0.381 against 0.399 for Jev): the 0.005 bar was
  conservative, not overfit. DSC-1 to DSC-3 held by construction in the pilot (disjoint splits by
  claim, at most 21 questions a request and six kept, every candidate's digest recorded); DSC-4's
  weight rule needs several passes and was not exercised by one.

## 6. Proposed laws

ING-19 to ING-21 make one derived field, the vector, safe to compute after landing. The laws below
generalize them to every derived field and add what typed answers and a discovery loop need. They
are proposed: each has a falsifier a test can run, and none is proved yet. The model they speak
of: a state is the keyed items, each with its bytes and its landed structure; a set of
integrators, each with an identity (for a decision integrator, the model's identity and the
question set's digest); and per integrator a field from keys (an item's digest, or an ordered
pair's) to an optional typed answer.

| law | statement | falsifier |
|---|---|---|
| INT-1 | completeness without any derived field (ING-19 generalized): a landing writes no answer and keys its item; a drain of integrator `J` writes only `J`'s field, so keys, structures and every other integrator's field are unchanged by it, and a query that reads none of `J`'s field answers the same before and after | a lazy landing that writes an answer; a drain of `J` that changes a structural answer or `K`'s field, compared byte for byte across the drain |
| INT-2 | convergence and idempotence per key (ING-20 generalized): deriving a key is idempotent and commutes with deriving another key and with a later landing of another item; the drain leaves nothing pending for its integrator; an answer, once landed, is never recomputed, so a model's run-to-run noise (C2) cannot change a stored field | an interrupted drain that, run again, asks a key already answered or leaves one pending |
| INT-3 | pending-report soundness (ING-21 generalized): a query reads only answers held under the field's current identity; a key without one is reported pending and never read as a default (no, says nothing, zero); an answer under another identity is never read as the current one | reading a pending key as "no" changes a query's answer (the control, as ING-21's `zeroRead_changes`); an answer of an older question set read under the new one |
| INT-4 | identity: an answer's key includes the integrator's identity and the question set's digest; a change of wording or of a Choice's option order changes the digest; no answer is edited in place | two declared question sets with one digest; an update that rewrites an answer under an unchanged key |
| INT-5 | locality: a hosted integrator's field exists only on an instance whose configuration allows its data to leave the machine; the default instance's private strata never reach one; the process that reads stores holds no network connection and the process that sends holds no store | a request written for the hosted process that carries text from a stratum the configuration does not allow; an edge process that opens a store |
| INT-6 | bounded influence: an answer enters a ranking only on a labelled scale of its own or as a bounded multiplier of a structural weight (UTL-3's form); it never creates or removes an authored edge, and a signed edge it produces carries provenance `interpreted` | an answer that changes an authored edge; a ranking that adds a probability to a cosine on one unlabelled scale |
| DSC-1 | held out: a question is kept only for its gain on rows disjoint from the rows it was drafted from and the rows its scoring model was fit on; the series of passes is read once on a split no pass read | a kept question whose held-out gain is not positive, reported by the loop itself; a split assignment that is not a function of the cluster (claim, thread) |
| DSC-2 | bounded: at most `K` questions an item and a declared budget a pass (requests, tokens, dollars); a pass that would exceed it stops before sending | a pass that sends more |
| DSC-3 | versioned and attributable: every kept question has an id, a version, a family and a digest in a declared set, and its measured gain and Shapley share are recorded under that digest | a kept question whose digest is in no declared set, or whose gain is not recorded |
| DSC-4 | no weight without gain (UTL-1's rule): a question's weight moves by `w ← w + λ (b − w) + clamp(g, −c, c)`, where `g` is the gain measured on held-out rows in the pass and zero when none was measured; so without measured gain it can only decay toward `b`, it stays in `[b − c/λ, b + c/λ]`, and a question whose weight falls under a declared line retires | a weight that rises in a pass without a positive measured gain, or leaves the box |

INT-1 to INT-3 are the derived-field laws of PR #83 with the identity widened from one embedder
to a set of integrators; their proofs should transcribe, since `Derived/Defs.lean` already carries
the identity per atom and per mark. INT-4 is a property of the digest and the append-only store.
INT-5 is the edge rule (only the edge touches the network, and never with private data) applied to
a new source. INT-6 and DSC-4 borrow the utility field's boundedness: the field never creates
support, and a weight without increments decays. `[DERIVED]`

## 7. Domain taxonomies are benchmarks, never features

The subject family is a Choice over options the caller supplies. arXiv's archives were the options
here because the corpus instance's arXiv items carry arXiv's own listing, which is ground truth;
the archive list lives in the question module as a benchmark fixture and nowhere else. In the
store, a subject Choice takes its options from the store's own structure (the clusters a dreamer
finds, an instance's declared scopes), so no domain's taxonomy becomes a palace feature. The
families that ship are the ones that apply to any text: kind, polarity, reply, equivalence,
relevance. `[INFERENCE; falsifier IF-6]`

## 8. Open questions

1. **The drain at the corpus's scale.** Edge fields are drained over candidate pairs only (the
   σ-backbone's pairs, a shortlist), never all pairs. At the local rate measured here (0.72 s a
   polarity request of five questions, one stream, with the embedder busy) a hundred thousand pairs
   take about twenty hours; where hosting is allowed, the same pairs cost about four and a half
   dollars at the measured 1,083 tokens a request. Which pairs deserve an answer first is the discovery loop's kind of
   question, asked of pairs instead of questions.
2. **The `elaborates` option.** The polarity family the store would ship has four options
   (supports, contradicts, elaborates, says nothing), matching the edge store's `contextualizes`;
   no benchmark here labels elaboration, so the fourth option is unmeasured.
3. **Calibration per integrator.** Where a model ranks well and calibrates badly, a monotone
   recalibration (isotonic or Platt) fit on a held-out split becomes part of the integrator's
   identity, measured like any other change.
4. **The loop's later steps.** The pilot ran one proposal step; the cookbook's loop then shows the
   proposer its worst misses on read rows and asks for revisions. Its cost and its gain past the
   first step are unmeasured here.
5. **The proofs.** INT-1 to INT-6 and DSC-1 to DSC-4 on a model like `Derived/Defs.lean`, with
   attacks and controls, before code relies on them.
6. **A larger local model.** tev1's 4-billion-parameter sibling (about 4.4 GB) fits the memory
   ceiling beside the embedder; whether it clears the bar where the 0.8-billion model does not is
   one rerun of the harness's local arm with the same questions and samples.

## Falsifiers

The study's own falsifiers (F1 to F10, C1 to C3) are the record's and are read in §4. The design's:

- **IF-1, probabilities over labels.** On a family's benchmark, a decision that reads the stored
  probabilities with an unsettled band is no better than one that reads the argmax label alone
  (for polarity: the precision of the contradiction edges written above 0.7 equals the argmax's).
  Then storing the whole answer buys nothing for that family, and a label suffices.
- **IF-2, identity is enough.** Two runs of one integrator identity on one declared question set
  disagree beyond the model's measured repeatability (C2). Then the identity misses something
  (the runtime's version, a quantization), and the key must carry it.
- **IF-3, polarity edges are worth writing.** On SciFact's candidate pairs, the contradiction
  edges the family would write at the upper threshold are no more precise than the base rate of
  contradiction among the candidates. Then they add noise to balance and frustration, and the
  producer stays off.
- **IF-4, the composition earns its cost.** On a family's battery the judged order is no better
  than the embedder's (F7, F9). Then the judge's tokens buy nothing there.
- **IF-5, locality holds by construction.** Any request written for the hosted process that
  carries text outside the strata its instance allows, or an edge process that opens a store.
- **IF-6, the families are generic.** A family that clears the bar on one collection fails it on
  a second collection of a different source, never tuned on. Then it is a family of that source,
  not a generic one, and it does not ship as generic.
