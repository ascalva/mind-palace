# prediction-market-sensor-fusion

Can an instance fuse a prediction market's crowd-aggregated probabilities with the graph's own
structure and produce a *better* view than either alone? The domain is incidental. What makes this
worth doing is that it is the first proposal where the instruments would be graded by an
**adversarial, numeric, timestamped scoreboard** that nobody in this project controls.

## 2026-07-26T14:45:00Z

```capsule
topic: prediction-market-sensor-fusion
date: 2026-07-26

decisions:
  - THE IDEA (owner, 2026-07-26, verbatim): "sensor fusion, can ouroboros or some other mind-palace
    instance be a crypto value predictor? based on polymarket and graph behavior, like predicting the
    future, the more you know the better the view gets" ... "and say testing with $100 in crypto, a real
    world example to see if the graph can make useful predictions?"
  - WHY POLYMARKET, in the owner's own framing (verbatim): "i started hearing that a good
    metric/prediction is sometimes outsourcing, and polymarket allows you to outsource and crowfund an
    answer to a question about life, crowfunding for free".
    ⇒ This rationale is sound and it is not a crypto rationale -- it is an EPISTEMICS rationale. A
    prediction market is a mechanism for aggregating dispersed private information into a single number,
    at zero cost to a reader. That is the same move the palace makes internally (many notes -> one
    view), performed by a crowd instead of by an embedder. Fusing them is a genuinely novel pairing.
  - ⚑ THE SHARPEST REFRAME (agent, and the owner should push back if it is wrong): Polymarket's value
    here is as a SCOREBOARD FOR THE INSTRUMENTS, not as a business. Every corpus the palace has ever
    been graded on is static and self-owned -- the owner's notes have no answer key. Case law was
    identified as "the first corpus with ground truth" (overruling = supersession). A resolved
    prediction market is strictly better ground truth than that: it is timestamped, numeric, adversarial,
    and it comes with a proper scoring rule (Brier). It can answer the question the project has never
    been able to answer about itself -- is "the more you know, the better the view gets" TRUE, or is it
    a slogan? -- with a number.
  - ⚑ THE EDGE CLAIM MUST BE STATED CORRECTLY OR THE EXPERIMENT IS VACUOUS. "Read Polymarket and follow
    it" has no edge by construction; the reader is a price taker and the market has already aggregated
    everything public. The only falsifiable claim is: *the graph sees something the market has not
    priced yet.* So the measurement is never "was the prediction right" -- it is "did the fused
    prediction beat THE MARKET'S OWN PRICE AT THE SAME TIMESTAMP." Anything less is measuring the market
    and crediting the palace.
  - ⚑ DROP "crypto value predictor" from the experiment, keep "resolvable-event forecaster." They are
    different objects: a Polymarket question is a discrete event with published resolution criteria and
    a settlement date; a crypto price is continuous with no resolution and no answer key. Only the first
    is gradeable. The price half can come back later, once the instruments have a score.
  - ⚑ IT MUST BE A SIBLING INSTANCE, NOT OUROBOROS. Same argument as the legal sibling and it is a
    non-negotiable, not a preference: NN-11 (the interface may transit a third party; the corpus never
    does). Market data has no business in the owner's self-map, and a self-map has no business informing
    a trade.

parked:
  - decision: whether real money moves at all
    default: NO -- paper only, and BACKTEST FIRST. Resolved markets are historical data, so the entire
      epistemic experiment runs offline, for free, with no waiting and no irreversibility: pull markets
      that have ALREADY settled, produce a probability from information available before settlement,
      score it against both the outcome and the market's contemporaneous price. If the palace cannot beat
      the closing price on already-resolved markets, there is no edge and no money should ever move.
      The $100 adds realism to nothing that is in question yet.
    re_entry: a backtest shows a positive edge over market price that survives an out-of-sample split.
      Only then is execution (fees, slippage, timing, custody) a separate and much harder question.
  - decision: where a live trading effector would even sit
    default: nowhere -- it is unbuildable today, and this is structural rather than a scheduling
      excuse. NN-3 (the model advises; code acts), NN-4 (executed code is powerless: no creds, no
      network, no vault), and Track G's effector layer is at max reachable tier NONE with nothing wired
      at any tier (finding-0011). A trading effector is the most dangerous class that exists here:
      irreversible, external, financial, adversarial.
    re_entry: the effect catalog can express the missing class below, AND the ε raise has staged past
      read-only.

open_questions:
  - ⚑ THE SECOND INDEPENDENT DEMAND FOR A MISSING EFFECT CLASS -- this is the most reusable thing in the
    capsule. `docs/brainstorms/ouroboros-email-identity.md` already surfaced that the effect catalog
    cannot express "IRREVERSIBLE BUT BOUNDED BLAST RADIUS." A $100 segregated wallet is that class,
    stated more sharply than email ever stated it: the loss is capped by construction, the action cannot
    be undone, and the bound is enforced by the world (the wallet holds $100) rather than by trusting the
    agent. Two independent arrivals make it a pattern, not an anecdote. Worth a finding against Track G
    regardless of whether a single trade is ever placed.
  - Does NN-7 (consequential advice -- health/financial/legal -- DEFERS, substantive but the decision is
    the owner's and a professional's) forbid this outright, or does it govern only ADVICE TO A HUMAN? A
    system that trades is not deferring; it is deciding. A system that produces a scored probability and
    hands it to the owner is squarely inside NN-7 as written. The distinction is load-bearing and the
    owner should rule on it before any execution question is reopened.
  - What is the actual fusion mechanism? "Market price + graph behavior" is a direction, not a design.
    Candidates worth separating: (a) the market as one more SENSOR feeding the correlator (Track D --
    `ObservedView` is its seam, and this would be its first external sensor); (b) the graph as a PRIOR
    that the market updates; (c) the market as a CALIBRATION TARGET that grades the dreamer's own
    confidence estimates without ever predicting anything. ⚑ (c) is the cheapest and possibly the most
    valuable -- it needs no forecasting ability at all, only honest confidence numbers to grade.
  - Is the palace's corpus even RELEVANT to any tradeable question? The honest prior is mostly no: the
    corpus is the owner's private notes and this repo's own history. A market on "will X ship by Q3"
    might be informed by it; a market on an election is not. The domain-relevance question should be
    answered BEFORE any harness is built, by listing candidate market types and asking which the corpus
    could possibly speak to.

next_steps:
  - Nothing is graduatable, and nothing should touch money, a wallet, a key, or `edge/` yet.
  - The cheapest high-information first move needs no corpus, no market access, and no code in this
    repo: LIST 10 RESOLVED POLYMARKET QUESTIONS and ask, by hand, whether the palace's corpus contains
    anything that bears on them. If the answer is no ten times, the fusion has nothing to fuse and the
    idea is dead for free -- which is a real result, cheaply bought.
  - If some do bear: the harness is a BACKTEST + SCORING pass (Brier vs. outcome, and vs. market price
    at the same timestamp), read-only, offline, paper only, in a sibling instance. Falsifier written down
    BEFORE any output is read -- fluent reasoning about markets is exactly what will tempt a post-hoc bar,
    the same trap the legal note names.
  - Independently of all of the above: file the "irreversible but bounded blast radius" gap against
    Track G, citing BOTH this note and the email note. That is owed whether or not this experiment runs.

references:
  - docs/brainstorms/ouroboros-email-identity.md    # first arrival of the missing effect class
  - docs/brainstorms/legal-corpus-sibling.md        # the sibling-instance pattern + ground-truth argument
  - docs/findings/finding-0011.md                   # effector tier is NONE; nothing wired
  - docs/BUILD-SPEC.md                              # NN-3 · NN-4 · NN-7 · NN-11
  - docs/inbox/owner-questions.md                   # oq-0031 (instruments can't discriminate at 13 docs)
```
