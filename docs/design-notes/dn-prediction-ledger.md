---
type: design-note
id: dn-prediction-ledger
track: scored-beliefs
status: draft                  # provenance description, never a gate; the owner's merge is ratification
implementation: built          # G1-G6 built 2026-11-05 in eval/predictions/; each experiment's sources, arms and schedule are its application's (G7)
created: 2026-11-05
updated: 2026-11-05
links:
  - docs/design-notes/scored-beliefs-and-earned-entitlement.md  # the parent: BL-1 the record, BL-2 resolution, BL-4 machinery not corpus, BL-5 binary scoring and the computed track record
  - docs/design-notes/prediction-castles.md                     # the dreamer's supersession forecasts: one kind of prediction this ledger records
  - docs/tracks/deployed-instances.md                           # DI-2 (issue #25): an experiment that needs an instance of its own
supersedes: null
superseded_by: null
warrant: null
---

# Pre-registered prediction experiments: the ledger, the scorer, the controls

## 1. Purpose and scope

The palace will run many experiments in which something (a model, an agent with and without the
palace, a dreamer, a whole instance) makes predictions that resolve later. Each needs the same
machinery, and none should rebuild it: a bar written before the first prediction, a record nobody
can quietly edit, proper scores, comparisons that respect how outcomes cluster, controls that
make a null result mean something, and a reading taken once. This note designs that machinery as
a feature of the framework. What an experiment is about (its questions, arms, sources, schedule
and the instance it runs in) belongs to the application and stays out of it.

It is the ledger `dn-scored-beliefs-and-earned-entitlement` asks for, in its generic form: BL-1's
record (a claim with a truth condition and a credence, what the predictor could see and what it
used, its anchor in time), BL-4's placement (machinery, not corpus) and BL-5's scoring (yes/no
questions, Brier, the minimum track record computed rather than guessed).

### 1.1 What this note decides

- **G1** the object: a probability on a question that resolves later, and how it is scored.
- **G2** forward only, for every arm whose inputs could already hold the outcome.
- **G3** the protocol, the genesis of every experiment.
- **G4** the ledger.
- **G5** scoring, the controls and blinding.
- **G6** variants and pinned arms.
- **G7** what an application supplies.

### 1.2 Out of scope

- Any particular experiment.
- BL-3's attribution replay and BL-6's dossiers: they read this ledger and come later.
- Running anything. The feature is a library and a command; an application schedules it.

## 2. Decisions

### G1. A prediction is a probability on a question that resolves later

A question is yes/no. It carries its source's own resolution text, a close time, a **family**
(the experiment's own grouping of questions) and a **cluster**: questions that turn on the same
underlying event share one, because their outcomes are not independent. A prediction is one
arm's probability that a question resolves yes, given in a round.

Predictions are scored by strictly proper rules, whose expected score is best only at the true
probability: Brier (primary) and the log score (with `p` clipped, the bound in the protocol). An
arm's skill is its improvement in Brier on a baseline arm, on the same questions in the same
round. "Was it right" is never the measure.

### G2. Forward only, for every arm whose inputs could already hold the outcome

A model's training data can contain the outcome of anything before its cutoff (Sarkar & Vafa,
"Lookahead bias in pretrained language models"), and an agent with web access can read an outcome
that has already happened. Halawi et al. ("Approaching human-level forecasting with language
models", NeurIPS 2024) kept only questions published after their models' cutoff for this reason.

So an arm that calls a model predicts only questions that close after the prediction is
recorded, and the ledger's own clock decides "after" (G4). Model-free arms may also be
backtested, walk-forward, on point-in-time inputs. That happens outside the ledger, which records
forward predictions only.

### G3. The protocol is the genesis

An experiment is one ledger whose first record is its protocol, and the scorer reads every number
from it:

- the **arms** (names, with variants, G6);
- the **families**;
- one **primary comparison** and any number of **secondary** ones, Holm-corrected as a family;
- **δ** (the smallest effect worth detecting), **α** and **power**;
- the log score's clip, and the bootstrap's resamples and seed;
- the **control arms**: `reference` (the arm the ORACLE control is measured against) and `null`
  (an arm recorded as an exact copy of `reference`);
- **pins** (G6);
- the **selection rule's parameters**, which decide which questions enter and depend on no arm;
- **n_clusters**, fixed by an amendment after the blinded pilot (G5);
- notes.

An amendment is a later protocol record, visible in the chain. Once a prediction exists, an
amendment may add arms, families, secondary comparisons and pins, fix `n_clusters` once, and
change the selection or the notes. It may not move the primary comparison, δ, α, power, the clip,
the bootstrap, the seed or the control arms, and it may not drop anything. The bar is written
before the first prediction and stays there.

### G4. The ledger

`eval/predictions/ledger.py`. One append-only JSONL file per experiment.

- **Records:** `protocol`, `question`, `prediction`, `resolution`, `void` (a question its source
  withdrew; excluded from every score).
- **The chain:** each line holds its sequence number, the previous line's hash and its own, the
  sha256 of the canonical JSON of the rest. `verify` recomputes the chain, so an edited, dropped or
  reordered line fails it.
- **The ledger's clock** stamps `recorded_at`. A prediction carries no timestamp of its own, so an
  arm cannot backdate one.
- **Refusals,** each writing nothing: any record before the protocol; a question already
  registered, in an undeclared family, or already closed; a prediction whose question is unknown,
  closed, resolved or voided, whose arm is unregistered or does not match its pin, whose `p` is
  not a probability, or that repeats an arm, question and round; a resolution that is not 0 or 1,
  or comes a second time; a naive datetime anywhere.
- **`extend`** appends several records all or nothing, each checked against the state the ones
  before it leave: a round lands whole or not at all.
- **One writer** at a time (an exclusive lock around each write, with the whole chain verified
  under it). Readers need no lock.
- **Anchoring:** `head` prints the chain head for publication outside the writer's reach (a pushed
  commit, a public timestamping service). A writer could rewrite an unanchored local chain, never
  an anchored one.
- **Machinery, not corpus (BL-4):** the ledger is not a stratum, no grant names it, nothing under
  `core/` imports it, and no dreamer can read its own scores.

### G5. Scoring, the controls and blinding

`eval/predictions/scoring.py`.

- **Pairs.** The unit is a (question, round) pair. Two arms are compared on the pairs both
  predicted, with `d = Brier(baseline) − Brier(arm)`.
- **Clusters.** The interval comes from resampling whole clusters (percentile, the protocol's
  resamples and seed), and secondary comparisons carry a two-sided bootstrap p-value, Holm-adjusted.
- **Late predictions,** recorded at or after the time the source says the question resolved, are
  excluded and counted. The ledger could not have known; the scorer does.
- **Calibration:** reliability in ten bins and the Murphy decomposition (reliability, resolution,
  uncertainty, and a within-bin residual that makes the identity exact).

| control | how | must show |
|---|---|---|
| NULL | an arm recorded as a copy of the reference arm | paired skill exactly 0: the harness pairs and scores correctly |
| KNOWN-EDGE | derived, never recorded: the primary comparison's own pair differences, centered and moved to a true mean of δ (the same clusters, the same spread) | its interval excludes 0 at the realized N; otherwise the run is underpowered and a null reads as inconclusive |
| ORACLE | derived: `p = o` against the reference arm | maximal skill: the scorer can see an edge at all |

An arm that merely leaned toward the outcome would improve on every question and look detected at
any N, so it cannot measure power. KNOWN-EDGE borrows the run's real noise instead, and says
nothing about the real mean.

**Blinding.** The pilot reports only the spread of the primary comparison's cluster means and the
clusters it implies, `N = ((z(1 − α/2) + z(power)) · sd / δ)²`, never a mean. With sd 0.08 and δ
0.02, N is 126; with δ 0.01, 503. `n_clusters` is fixed by an amendment, and the report refuses
the comparisons until N is reached unless the caller unblinds on purpose. The decision at N: the
arm improves if the interval's lower bound is above 0; no useful improvement if its upper bound is
below δ; otherwise inconclusive.

### G6. Variants and pinned arms

An arm may name a variant after a colon (`dreamer:model-x`). Each registered variant is an arm of
its own, so models, prompts and revisions are compared the way arms are.

Every prediction carries `config`, the digest of its arm's model, prompt and tools. The protocol
pins the arms it chooses, usually the two the primary comparison names. A prediction from a
pinned arm with another digest is refused, and once predictions exist a pin cannot change.
Experiments run for days or weeks and get tweaked while they run; a tweak is a new variant, never
a silent change to an arm the comparison depends on.

### G7. What an application supplies

- Its protocol: arms, families, comparisons, the bar, the selection rule.
- Question sources and resolvers, which append questions and resolutions.
- The arms, which append predictions with their config digests, what they could see, and their
  evidence (for an arm that asks the palace, its query sentences with their trace digests).
- A schedule of rounds, the anchoring of the head, and liveness: a missed round must raise an
  alarm, because silence is not success.
- Where it runs: anywhere `eval` runs, or a named instance of its own when it needs a corpus of
  its own (DI-2, §4).
- Optionally, a family in which no skill should be possible. Skill there is read as leakage first.

## 3. Falsifiers

- **F-1:** the null arm's paired skill against the reference is not exactly 0. The pairing or the
  scoring is broken; nothing is read until it is fixed.
- **F-2:** a prediction recorded at or after its question's close or resolution, or a chain that
  fails `verify`. Pre-registration is broken.
- **F-3:** KNOWN-EDGE is not detected at the realized N. The run is underpowered; a null is
  reported as inconclusive, never as "no effect".
- **F-4:** an arm's evidence cites the outcome of the question it predicts. That arm read the
  answer; its predictions for the question are voided and the leak is reported.

## 4. Running an experiment in an instance of its own: findings

The loose work on a second instance is `feat/podman-bench` (six commits on 3108741, unpushed).

1. **DI-2's first half is built there:** `MIND_PALACE_OVERLAY` names the one overlay a named
   instance reads, in place of Ouroboros's chain, and a missing file refuses. Missing, issue #25's
   second half: an `[instance]` id in the schema and the namespaces derived from it (backup
   repository, attestation key, spool, supervisor lock).
2. **A latent cross-instance write.** Under a named overlay the loader stops reading
   `config/levers.toml`, but the self-modification loop still writes it by default
   (`ops/apply.py::write_overlay`, `ops/selfmod.py`, `LEVERS_OVERLAY`). A named instance running
   from a shared checkout with self-modification on would write Ouroboros's tuned knobs. The bench
   turns self-modification off and runs on a read-only root, so it cannot happen there. DI-2
   should give each instance its own levers path, or refuse self-modification under a named
   overlay.
3. **The bench's sealed profile is the right base** for an instance's core: network `none` with
   the embedder joined on loopback, a read-only root, every capability dropped, an unprivileged
   user, named volumes only, a whitelisted build context. An experiment that fetches its own
   questions adds the README's unbuilt `prod` profile: an edge container with filtered egress.
4. **Memory.** The default podman machine (2 vCPUs, 2 GiB) also hosts the owner's other containers;
   an embedder and a runner there made the kernel kill Open WebUI 13 times in one afternoon before
   `oom_score_adj` was added. A long-running instance needs a podman machine of its own.
5. **Merge order.** The branch merges cleanly onto `build/ingest-door` (`git merge-tree`).

## 5. Consequences

- **Built:** `eval/predictions/` (G1 to G6) and `python -m eval.predictions
  {verify,head,power,score}`. The tests were checked against five mutations (no close check,
  late predictions scored, pairs resampled instead of clusters, no blinding, pins ignored); each
  turns a test red.
- **Next, per application:** its protocol, sources, arms and schedule, outside this feature.
- **Later:** BL-3's attribution replay and BL-6's dossiers over this ledger. The castles' forecasts
  (`dn-prediction-castles` PC-1) land here as predictions whose truth condition is a later
  version; PC-3's registration and the Brier score read the same pair.
- **Parked:** proving the scores' strict properness and the Murphy identity in Lean (design
  theorems; textbook results, nothing in the code relies on them yet).

## Cross-references

- `docs/design-notes/scored-beliefs-and-earned-entitlement.md`: BL-1 to BL-6
- `docs/design-notes/prediction-castles.md`: PC-1 the prediction unit, PC-3 grading
- `docs/tracks/deployed-instances.md`, issue #25: DI-2
- Sarkar & Vafa, "Lookahead bias in pretrained language models" (2024)
- Halawi, Zhang, Chen & Steinhardt, "Approaching human-level forecasting with language models"
  (NeurIPS 2024)
