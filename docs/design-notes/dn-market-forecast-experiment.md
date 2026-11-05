---
type: design-note
id: dn-market-forecast-experiment
track: scored-beliefs
status: draft                  # provenance description, never a gate; the owner's merge is ratification
implementation: building       # E1 (the ledger, the scorer, the controls) built 2026-11-05; E2 onward follow (§4)
created: 2026-11-05
updated: 2026-11-05
links:
  - docs/brainstorms/prediction-market-sensor-fusion.md        # THE WARRANT: the July capsules and the 2026-11-05 capsule, the owner's seeds verbatim
  - docs/design-notes/scored-beliefs-and-earned-entitlement.md # the ledger this builds first, outside Ouroboros: BL-1 record, BL-2 resolution, BL-4 read-only, BL-5 binary scoring
  - docs/brainstorms/palace-instances-as-nodes.md              # a second instance, each in its own node; the per-instance constitution
  - docs/tracks/deployed-instances.md                          # DI-2, instance identity (issue #25): the sibling's precondition
  - docs/design-notes/synchronic-diachronic-dreamer.md         # the dreamers as predictors; §2.8 the diachronic park
  - docs/design-notes/erratum-relation.md                      # a correction is a supersession and an erratum: data vintages (D8)
  - docs/design-notes/external-grounding.md                    # §2.6 the licence gate for third-party text
  - docs/design-notes/dn-ingest-door.md                        # on build/ingest-door: the spool and the one writer the sibling's edge feeds
  - docs/design-notes/prediction-castles.md                    # open PR #6 (draft): the supersession event as the dreamer's prediction unit (D8)
supersedes: null
superseded_by: null
warrant: docs/brainstorms/prediction-market-sensor-fusion.md
---

# The market forecasting experiment: a sibling instance, a ledger, and arms scored against the market

## 1. Purpose and scope

The owner asked (2026-11-05, verbatim in the warrant) whether the palace can be used to understand
a subset of the financial market, and how to test its prediction capabilities: a steady influx of
data, a Claude model as the agent that researches and ingests, predictions recorded, then waiting
to see whether they were right. This note designs that test so that its result means something
whichever way it comes out.

### 1.1 What this note decides

- **D1** the object: forecasts of resolvable yes/no questions, scored by proper scoring rules
  against a baseline at the same timestamp, never "was it right".
- **D2** forward only, for every arm with a model in it.
- **D3** the families and their baselines.
- **D4** the arms, and the one comparison that answers the owner's question.
- **D5** the ledger: pre-registration as its genesis record, a hash chain, the ledger's own clock.
- **D6** scoring, the controls, and the sample size fixed before any result is read.
- **D7** the sibling instance: posture, topology, scheduling.
- **D8** the data model for assets (the owner's supersession seed).
- **D9** crypto as a second universe.

### 1.2 Out of scope

- **Money.** Paper only. July's ruling stands, and no effector exists (finding-0011).
- **Ouroboros.** Nothing here reads or writes it. The experiment runs in a sibling or, before the
  sibling exists, in no palace at all (E2).
- **The dreamer arm's grant.** The owner's call (§8). The dreamers join last (E5).
- **Fetchers and the Claude arms' code.** E2, edge-side, after this note.

### 1.3 The bar

A null result has to be informative and a positive one has to survive the obvious explanations
(leakage, luck, a broken harness). Every claim the experiment can make is paired with a control
that would expose it (§6). The protocol (D6) enters the ledger as its first record, before any
forecast, so the bar cannot move after the results are read.

## 2. What exists

| piece | where | state |
|---|---|---|
| belief record, resolution classes, read-only law, binary scoring | `dn-scored-beliefs-and-earned-entitlement` | draft design, no code |
| the dreamers | `core/dreaming/` | read authored notes only; synchronic not wired; diachronic parked |
| a named instance selected at run time | `feat/podman-bench` 9be10ac (`MIND_PALACE_OVERLAY`) | built, unpushed |
| a sealed container profile | `feat/podman-bench` (`compose.yaml`, `ops/container/`) | built for the bench, unpushed |
| the door: a spool per principal, the daemon the one writer | `build/ingest-door` | built, unmerged |
| instance identity (`[instance]`, namespaces) | issue #25, DI-2 | open |
| graph instruments: persistence, Forman curvature, Hodge, signed Laplacian, effective resistance | `core/complex/`, `core/kernel/complex/`, `core/graph/` | built; Lean statements for curvature, Hodge, balance, frustration, the sever horizon |
| magnetic Laplacian (direction as phase) | `formal/Palace/Magnetic.lean` | proved, not in code |
| version history keyed by sequence; erratum relation | `core/stores/versions.py`; `dn-erratum-relation` | built; ratified |

## 3. Decisions

### D1. The object is a scored forecast of a resolvable question

A forecast is a probability `p` that a yes/no question resolves yes, given before it resolves.
Each question carries its source's own resolution text, a close time and an event cluster. A
continuous quantity (a price, a volatility, a graph reading) enters only as a thresholded
question with a horizon ("SPX realized volatility over the 21 trading days after the round exceeds
the VIX close of the round"). This is BL-5's v1 rule (binary only), and it answers July's
objection to prices ("no resolution and no answer key").

"Was it right" is never the measure. A forecast is scored by a strictly proper rule (Brier
primary, log secondary), and an arm's skill is its score's improvement on a baseline's score on
the same questions at the same round. Scoring against the market's own price removes the
incentive to pick easy questions (July): an easy question has a confident price.

### D2. Forward only, for every arm with a model in it

A model's weights hold the outcome of anything before its training cutoff (Sarkar & Vafa,
"Lookahead bias in pretrained language models"), and a researcher with web search can read an
outcome that has already happened. A backtest of a model arm therefore measures memory. Halawi et
al. ("Approaching human-level forecasting with language models", NeurIPS 2024) used only questions
published after their models' cutoff for this reason.

So every arm that calls a model forecasts only questions that close after the forecast is
recorded, and the ledger's own clock decides "after" (D5). Model-free arms (I) may also be
backtested, walk-forward, on point-in-time history: index members as of each date, each day's
inputs from data published before it, no centered windows.

### D3. The families and their baselines

| family | example question | baseline to beat |
|---|---|---|
| EVENT | a Fed decision, a CPI print, a recession call, a company event (Kalshi, Polymarket) | the market's price at the round (arm M) |
| VOLATILITY | realized vol over the next 21 days above the round's implied vol | implied vol (VIX) and HAR-RV |
| STRUCTURE | a co-movement graph reading crosses a threshold, a cluster splits or merges, an edge flips sign | "nothing changes" (persistence) |
| DIRECTION | an asset closes higher over a horizon | the market price, or 0.5 |

DIRECTION is a control, not a target: in liquid markets nothing should beat it, so skill there is
first read as a leak (F-MF3). STRUCTURE is the palace's native family: the yes/no structural claims
BL-5 admits first, resolved by a later cut.

### D4. The arms

| arm | what it is | sees |
|---|---|---|
| M | the market's price at the round | the market |
| NULL | a copy of M, as a harness check | the market |
| W | Claude with web search, no palace | the web, market domains blocked |
| P | Claude with web search and the sibling's read-only `query` | the web and the palace |
| F | Claude with web search and the same notes as flat text | the web and the notes, no graph |
| L | the local model with the sibling's `query`, no web | the palace |
| I | graph instruments to a probability (logistic, fitted walk-forward) | prices and the graph |
| D | the dreamers' beliefs, with a stated credence | the grant the owner rules (§8) |

**The comparison that answers the owner's question is P against W:** the same model and the same
web access, with and without the palace. Every arm against M asks whether there is an edge at
all. F is an attribution control in the bench's sense (`ops/container/README.md`, "for attribution
and never as candidates"): if P beats W but not F, the gain is the notes, not the graph.

The model arms forecast without seeing the market's price, so they report independent information
rather than an anchor. For W this is best effort (`blocked_domains` keeps the market sites out,
but articles quote odds); for P and L, Σ enforces it. A combination with the market price is a
fixed formula fitted on the first weeks, never the model's own adjustment.

### D5. The ledger

`eval/forecast/ledger.py`, built with this note. One append-only JSONL file per experiment:

- **Records:** `protocol` (the pre-registration, D6; the genesis, and amendments later in the
  chain where everyone can see them), `question`, `forecast`, `resolution`, `void` (a market
  cancelled or annulled).
- **The chain:** every line holds its sequence number, the previous line's hash and its own:
  `sha256` over the canonical JSON of the line without the hash. `verify` recomputes the chain;
  any edited, dropped or reordered line fails it.
- **The ledger's clock decides.** `recorded_at` is stamped by the ledger when it appends. A
  forecast is refused when its question is unknown, already resolved or voided, closed at or
  before `recorded_at`, when its arm is not registered, or when `p` is outside [0, 1]. A
  resolution is refused for an unknown question or a second time.
- **Anchoring:** the chain head (sequence, hash) is published outside the writer's reach (a
  pushed commit; the sibling's attestation once it has keys). A writer could rewrite a whole
  local chain; it cannot rewrite one already anchored.
- **One writer** (an exclusive lock around each append); readers need no lock.
- **Machinery, not corpus (BL-4):** the ledger is not a stratum, no grant names it, and no
  dreamer can read its own scores. It lives under `eval/`, and core imports nothing from it.

### D6. Scoring, the controls and the sample size (the pre-registration)

The `protocol` record holds these values. The scorer reads them from the ledger, not from code
defaults.

- **Unit:** a (question, round) pair. An arm's forecast for a pair is its first one recorded in
  that round. Pairs are clustered by the question's event cluster (five brackets of one Fed
  decision are one cluster).
- **Primary hypothesis H1:** P improves on W on the EVENT family. Statistic: the mean over pairs of
  `d = Brier(W) − Brier(P)`, with a 95% interval from a cluster bootstrap (10,000 resamples,
  fixed seed).
- **Decision at N:** "P helps" if the interval's lower bound is above 0; "no useful help" if its
  upper bound is below δ; otherwise inconclusive, and the known-edge control says whether more N
  could settle it.
- **δ = 0.02 Brier, α = 0.05 two-sided, power 0.80.**
- **Blinded pilot:** two weeks of rounds, then the scorer reports only the standard deviation of
  the cluster-mean differences, never their mean. N in clusters is
  `((z_{1−α/2} + z_{power}) · sd / δ)²`, fixed in a protocol amendment, and the comparison is read
  once at N. With sd = 0.08 that is about 126 clusters (three months at ten a week).
- **Secondary**, Holm-corrected as one family: each model arm against M on EVENT; I against its
  baselines on VOLATILITY and STRUCTURE; L against W; F against P.
- **Log score:** `p` clipped to [0.001, 0.999]. Brier needs no clip.
- **Calibration:** reliability in ten bins and the Murphy decomposition (reliability, resolution,
  uncertainty) per arm and family.
- **Question selection is code, frozen in the protocol, and independent of every arm:** open
  yes/no markets in the declared categories, closing 3 to 60 days after the round, the K most
  traded, at most three per event cluster.

Controls, each with what it guards:

| control | how | must show |
|---|---|---|
| NULL | a copy of M, recorded as an arm | paired skill against M exactly 0 (the harness pairs and scores correctly) |
| KNOWN-EDGE | derived in the scorer, never recorded: the primary comparison's own pair differences, centered and moved to a true mean of δ (the same clusters, the same spread) | its interval excludes 0 at the realized N; otherwise the run is underpowered and a null reads as inconclusive |
| ORACLE | derived: `p = o` against M | maximal skill (the scorer can see an edge at all) |

A synthetic arm that leans toward the outcome (`p = m + κ(2o − 1)`) would improve on every
question and be "detected" at any N, so it cannot measure power. The control borrows the run's
real noise instead, and says nothing about the real mean.
| DIRECTION | a family no arm should beat | no skill; skill there is read as a leak first |

### D7. The sibling instance

- **Identity first.** A named instance (DI-2): its own overlay `config/instances/<name>.toml`, an
  `[instance]` id, and the namespaces issue #25 derives from it (the backup repository or prefix,
  the attestation key, the spool, the supervisor lock) before it boots. The bench branch has the
  first half (§9).
- **Posture.** Public data only; paper only; no effector; the corpus is public by construction.
  Whether a third party may read it (bright line 11, for arm P) is the owner's explicit call,
  declared in the instance's posture, never inferred from the data being public (the instances
  capsule: "loosening by analogy").
- **Topology,** extending the bench profile:
  - a podman machine of its own (the instances capsule: "each one must live in its own node";
    the shared 2 GiB machine has no headroom, §9);
  - `core`: network `none`, loopback shared with `embedder` as the bench does, read-only root,
    every capability dropped, an unprivileged user, named volumes only;
  - `edge`: an internal network whose only route out is an allowlisting proxy; holds the API key
    as a podman secret; writes requests into the spool volume, which the core drains (the door);
  - the ledger in a volume of its own.
- **Arm P's queries.** Strict default: the edge asks through the spool and the core answers into
  an outbox, so the corpus never sits in a component with egress. The alternative, the edge
  reading the data volume read-only (readers need no lock, DOR-12), is simpler and puts the
  corpus beside the network; it is allowed only if the owner's posture ruling says so.
- **Scheduling.** Run-to-completion rounds started by a host job the owner installs, not a daemon.
  The launchd labels hard-coded in `ops/lifecycle/launcher.py` (`com.mind-palace.palace`) and
  `ops/heartbeat.py` (`com.mind-palace.tick`) never come into play.

### D8. The data model for assets (seed 4)

- **The trunk is a version chain.** An asset is an identity keyed by a permanent id (FIGI or CIK;
  tickers get reused), and each daily state is a version in `core/stores/versions.py`. Versions
  are keyed by sequence, not digest (C1), so a price that returns to an old value is a new
  version, not a loop.
- **Revisions are a supersession and an erratum** (`dn-erratum-relation`): the first print of a
  statistic and its later revision are both kept, and `as of` returns what was known then. This
  is how vintage archives such as ALFRED store macro data, and it is the lookahead most backtests
  get wrong.
- **The trunk stays out of the spectral math** (C2, as built). Adjacency in time is not
  influence.
- **Influence is not a causal edge.** A C edge is witnessed (the witness law: every proven edge
  carries the mechanical evidence it was derived from). "A's move moves B" is an estimate: its
  own letter, interpreted provenance, its estimator, lag, window and strength, estimated per cut
  from data before the cut, and versioned. The edge store keys `(u, v, rel_type)` today, so the
  cut has to join the key, or a re-estimate overwrites its history.
- **Witnessed links** (customer and supplier from filings, parent and subsidiary, holdings) are
  observed edges with the filing as their record. C stays for the system's own provenance (which
  run wrote which note, which queries formed which forecast).
- **Branches are corporate actions:** a spin-off splits an identity, a merger joins two. These
  are the σ transports between cuts; pulling a reading back across a merger counts it once per
  predecessor (‖σ^*‖ = √(max fiber), TRN-1..4) unless weighted by the fiber.
- **Ripples are walks:** `walk from "asset/A" via I D{0,4}` (one influence step, then up to four
  days on B's trunk) is a regular path query the language evaluates exactly (QSA-7), once D moves
  exist at the node grain (open, L7). Read globally, the Hodge decomposition of the lead-lag flow
  splits into a ranking of who leads (the gradient) and feedback loops (curl and harmonic parts).
- **A first ripple experiment:** forecasts that B's return after A's move is positive, with
  ripples along witnessed customer and supplier links, along estimated lead-lag edges, and with
  no ripple at all. This replicates Cohen and Frazzini (2008) forward and tests the seed
  directly.
- **The castles' prediction unit, with a resolver on a schedule.** `dn-prediction-castles` (open
  PR #6, draft) makes the supersession event the diachronic dreamer's prediction unit ("X will
  be superseded, within window W on clock κ, by something of shape S") and names the per-doc
  version chains of `core/stores/versions.py` a lawful grading target (its PC-1). In the
  sibling an asset's trunk is exactly that family, written by the market lander, which no
  dreamer can write: a castle's forecast on an asset resolves at the next cut, with no owner in
  the loop. When castles exist, arm D records each forecast here with a credence and a truth
  condition, and PC-3's registration and this ledger's Brier score read the same pair.

### D9. Crypto as a second universe (seed 2)

Volatility does not make answers come faster; the count of independent resolved forecasts does,
and large swings add noise to each one. Crypto helps for other reasons: it trades every day,
minute history is free from the exchanges, and short-dated price markets turn a price into
resolvable questions with a market price to beat. The cost: those markets are the DIRECTION
family. Telling a 52% hit rate from 50% takes about 4,900 resolutions: seven months of hourly
questions on one coin, nineteen years of daily questions on a stock. That pace suits arm I, and
the model arms stay daily. Co-movement is computed after removing the Bitcoin factor, or every
coin is one cluster.

## 4. Consequences: the order of work

- **E1** (this note's branch): the ledger, the scorer, the controls, the blinded power reading.
  No network, no palace.
- **E2** (edge-side): question selection and snapshots for arm M, arm W with Claude's server-side
  web search, a daily round started by a host job. This starts the clock with no palace changes.
  It needs the owner's go-ahead for API spend and for the host job.
- **E3** (after the door's PRs and the bench branch merge): DI-2's second half, the sibling's
  profile, the landers (`do ingest paper`-style commands for research notes and daily bars), the
  query spool, arms P, F and L.
- **E4:** arm I, backtested walk-forward and then run forward, on stocks and crypto; the asset
  trunks and the influence edges of D8.
- **E5:** the dreamer arm, after the owner's grant rulings.
- **E6:** the comparison read once, at the N fixed after the pilot.

## 5. Wiring

E1 wires nothing: `uv run python -m eval.forecast {verify,head,score,power}` over a ledger file
the caller names. No default path writes into `data/`.

## 6. Risks and falsifiers

- **F-MF1:** the NULL arm's paired skill against M is not exactly 0. The pairing or the scoring is
  broken; nothing is read until it is fixed.
- **F-MF2:** a forecast recorded at or after its question's close or resolution, or a chain that
  fails `verify`. Pre-registration is broken.
- **F-MF3:** skill in the DIRECTION family at α. Suspect leakage before believing it.
- **F-MF4:** the KNOWN-EDGE control is not detected at the realized N. The run is underpowered; a
  null is reported as "inconclusive", never as "no effect".
- **F-MF5:** a model arm's evidence cites the outcome of the question it forecasts. That arm
  read the answer; its forecasts for that question are voided and the leak is reported.
- **Risk, non-stationarity:** a market's regime changes inside the run. The result holds for the
  period measured; the dossier decays (BL-6).
- **Risk, cost:** model arms cost money every round. E2 starts with W only and a small K.

## 7. Parked decisions

- Real money: never in this experiment.
- The dreamer arm's grant, and any lift of the diachronic park in the sibling (§8).
- Proving the scoring rules' strict properness and the Murphy decomposition in Lean (design
  theorems; textbook results, nothing in the code relies on a proof of them yet).

## 8. Owner decisions

1. The sibling's name, and its posture: in particular whether a third party may read its corpus
   (bright line 11) for arm P.
2. Whether the dreamers may read observed and interpreted strata in the sibling. "Mirror, not
   oracle" fits a self-map, not a forecaster; the sibling's ground truth would be observed market
   data.
3. Whether the diachronic park lifts in the sibling first. Markets have a native clock (one cut
   per trading day, every claim resolving on schedule), which makes it the easiest place to build
   the past-cut instruments the park waits on.
4. A podman machine of the sibling's own, and its size.
5. E2's go-ahead: API spend for arm W, and the host job that starts each round.

## 9. Findings: the review of `feat/podman-bench`

The loose work on a second instance is `feat/podman-bench` (six commits on 3108741, unpushed, no
PR).

1. **DI-2, first half, built.** `MIND_PALACE_OVERLAY` names the one overlay a named instance
   reads, replacing Ouroboros's chain; a missing file refuses; the test suite clears the variable.
   Missing, issue #25's second half: an `[instance]` id in the schema and the namespaces derived
   from it (backup repository, attestation key, spool, supervisor lock).
2. **A latent cross-instance write.** Under a named overlay the loader stops reading
   `config/levers.toml`, but the self-modification loop still writes it by default
   (`ops/apply.py::write_overlay`, `ops/selfmod.py`: `LEVERS_OVERLAY`). A named instance running
   from a shared checkout with self-modification on would write Ouroboros's tuned knobs. The bench
   turns self-modification off, and its root filesystem is read-only, so it cannot happen there.
   DI-2 should give each instance its own levers path, or refuse self-modification under a named
   overlay.
3. **The sealed profile is the right base for the sibling's core:** network `none` with the
   embedder joined on loopback (probed: only `lo`, DNS fails), read-only root, every capability
   dropped, an unprivileged user, named volumes only, a whitelisted build context (verified by
   planting `data/` and `config/ouroboros.toml` before a build). What the sibling adds is the
   README's unbuilt `prod` profile: an edge with filtered egress.
4. **Memory.** The default podman machine (2 vCPUs, 2 GiB) hosts the owner's containers (about
   1.3 GB); an embedder and a runner there made the kernel kill Open WebUI 13 times in one
   afternoon before `oom_score_adj` was added. A daily sibling needs a machine of its own (§8.4).
5. **Merge order.** The branch merges cleanly onto `build/ingest-door` (checked with
   `git merge-tree`), so it can land after the door's PRs.
6. **Scheduling.** The bench runs to completion and starts no daemon; the sibling should keep
   that shape (D7).

## Cross-references

- `docs/brainstorms/prediction-market-sensor-fusion.md`: the warrant
- `docs/design-notes/scored-beliefs-and-earned-entitlement.md`: BL-1..BL-6
- `docs/tracks/deployed-instances.md`, issue #25: DI-2
- `docs/design-notes/prediction-castles.md` (open PR #6): PC-1 the prediction unit, PC-3 grading
- `eval/forecast/`: the ledger, the scorer, the controls (E1)
- Sarkar & Vafa, "Lookahead bias in pretrained language models" (2024)
- Halawi, Zhang, Chen & Steinhardt, "Approaching human-level forecasting with language models"
  (NeurIPS 2024)
- Cohen & Frazzini, "Economic links and predictable returns", Journal of Finance (2008)
