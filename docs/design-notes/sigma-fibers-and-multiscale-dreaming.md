---
type: design-note
id: dn-sigma-fibers
status: draft            # draft → ratified → superseded.  draft→ratified is an OWNER-ONLY hand edit.
implementation: design-only
created: 2026-07-16
updated: 2026-07-16
links:
  - docs/brainstorms/cross-strata-and-multiscale-dreamers.md   # THE WARRANT — founding + σ-fibers + harness×algebra capsules
  - docs/design-notes/resolution-result-typing.md              # companion: the Res(π) result-typing amendment this note consumes
  - docs/design-notes/cross-strata-dreamer.md                  # companion: Idea B, the firewall fork (separate blessing stakes)
  - docs/design-notes/evaluation-harness.md                    # §2.1 key, §2.3 catalog typing, §2.5 registry/THRESH, §2.6 optimizer, §2.8 overnight
  - docs/design-notes/capability-scope-algebra.md              # §2.3 Inv/Rate(κ), :116 Rule CLOCK — the typing this extends via the companion
  - docs/design-notes/dreamer-quality-suite-evaluation.md      # F9 — the gate's validation battery
  - docs/design-notes/recursive-strata.md                      # I1 — the promotion boundary the gate must not cross
  - docs/brainstorms/doc-code-entanglement.md                  # the multi-resolution-family capsule (the meta-pattern ruling, §2.8)
supersedes: null
superseded_by: null
warrant: docs/brainstorms/cross-strata-and-multiscale-dreamers.md
---

# σ-fibers: claim persistence across the mirror-graph filtration, and the strength-gated surface

> Composed at **fable** (`claude-fable-5`, 2026-07-16, the owner-sanctioned Fable+xhigh design
> pass on `cross-strata-and-multiscale-dreamers`). Filed as `draft`; ratification is a hand edit
> by the owner — no command performs it, `gate-guard` denies any agent attempt, and `/graduate`
> refuses this note until `status: ratified`. **Design only; no build is authorized by this note.**

## 1. Purpose and scope

The σ-fibers capsule asked: the sweep engine (bp-046 + bp-049) varies `dream_rnd_sigma` across a
grid to *select one value* — should the system instead **retain σ as a dimension**, treating a
connection's persistence across the σ-family as a principled strength scalar? This note designs
that retention: the fiber object (§2.2), the persistence functional with its falsifier (§2.3),
the harness realization over the existing stores (§2.4), the strength→surfacing gate and its
F9 validation protocol (§2.5), the result-typing verdict (§2.6), the query-surface shape (§2.7),
and the dreamer-family axes this makes precise (§2.8).

This is **Idea A of the parent brainstorm made concrete**: pure scope/scale over the AUTHORED
graph via `MirrorView` — no new boundary, no union scope, firewall untouched. Two companions
carry the pieces with different blessing stakes: `dn-resolution-result-typing` (an amendment to
the *ratified* scope algebra's §2.3 — the highest bar) and `dn-cross-strata-dreamer` (Idea B,
the firewall fork). **Out of scope here:** anything reading a non-mirror stratum; the chunk-smear
(its evidence bar is unchanged — the offline grain experiment gates it, `doc-code-entanglement`
2026-07-11 park); the conversation-layer sensor; any build.

## 2. Principles / decision

### 2.1 The filtration {G_σ}, formally — and where it already lives

Let V be the authored notes of one `MirrorView` snapshot (`core/mirror.py:96-101`, π_MR — every
row provably `∈ MIRROR_READABLE`, `core/provenance.py:78-80`) and let `w(u,v) ∈ [-1,1]` be the
cosine of note centroids. The mirror graph at threshold σ is

```
G_σ = (V, E_σ),   E_σ = {(u,v) : w(u,v) ≥ σ}          (core/dreaming/graph.py:39)
```

over the swept range `[σ_lo, σ_hi] = [0.55, 0.75]` (the `dream_rnd_sigma` lever's hard bounds,
`ops/levers.py:112-122`). Three structural facts, each grounded:

1. **{G_σ} is a superlevel filtration:** σ ≤ σ′ ⇒ E_{σ′} ⊆ E_σ. Monotone nesting is exact, by
   construction of the indicator `sim >= sigma` (`graph.py:39`).
2. **The full filtration is already materialized in compressed form.** `MirrorGraph` retains the
   complete cosine matrix `sim` (`graph.py:28,37`); adjacency at *any* σ is a comparison against
   it. Retaining "a graph per σ" would duplicate what one matrix already encodes — this kills
   fiber-candidate (a) below.
3. **Everything downstream of G_σ is piecewise-constant in σ.** The adjacency changes only when
   σ crosses one of the ≤ n(n−1)/2 distinct entries of `sim`; between consecutive breakpoints,
   G_σ — and hence every *deterministic* pipeline computation over it (`community_interpreter`,
   `collect_claims`, `adjudicate`; all model-free, `core/dreaming/shadow.py:152-205`) — is
   constant. So `[σ_lo, σ_hi]` partitions into finitely many intervals with breakpoints at
   cosine values, on each of which the emitted claim set is fixed. This is the theorem the
   estimator (§2.3) and the exact evaluator (§2.4) both rest on. (Seed caveat: today the claim
   path consumes no seed at all — `ShadowRunner.seed` reaches only the `EvalKey`,
   `shadow.py:208-212` — so per-σ claim sets are seed-invariant; the definitions below carry a
   seed-majority rule anyway, for forward-compatibility with a stochastic pipeline.)

**The degeneracy result (state it, or the metric is a re-dressed cosine).** For a feature that
is a bare edge (u,v), the σ-support is exactly `{σ ∈ [σ_lo, σ_hi] : σ ≤ w(u,v)}` — an interval
whose measure is a monotone transform of `w(u,v)`. **Edge-level persistence adds nothing over
the stored cosine.** The value of persistence lives strictly at the *feature* level — clusters,
communities, tensions, holes: claims whose existence at σ is not monotone and not readable off
any single matrix entry. This is why the fiber object is the claim, not the edge (§2.2), and it
supplies the metric's first falsifier clause (§2.3).

### 2.2 The fiber object — parked decision (a)/(b)/(c), resolved

The capsule parked three candidates. Ruling: **(b), sharpened — the fiber is the
content-addressed *claim* together with its σ-support**, where claim identity is the run
ledger's existing `claim_id = sha256(kind ‖ canonical(support) ‖ polarity)`
(`core/stores/runledger.py:37-42` — surface wording and confidence deliberately excluded, so
"the same pattern, found twice" is one identity across cells).

- **(a) a whole graph per σ — rejected.** Redundant with the retained `sim` matrix (§2.1 fact 2)
  and with the append-only per-σ series the stores already hold (§2.4). Pure storage cost, no
  new information.
- **(c) a σ-parameterized dreamer instance — rejected as the *first* move.** k live instances
  = k synthesis passes; live `dream_v2` makes the earned model call (step 8), so k instances
  press directly on the ≤2-resident-model ceiling (BUILD-SPEC §3 #8) while the strength
  annotation that would justify them does not yet exist. Revisit *after* the gate proves tiers
  carry signal — parked as FB-4 (§3) with that re-entry.
- **(b) accepted, with a sharpening the capsule lacked:** the persistence-carrying object is the
  **claim**, not the "connection/edge" — because edge persistence is degenerate (§2.1) and
  because claims already have exactly the identity persistence needs: content-addressed,
  order-insensitive, wording-insensitive, stable across runs and cells. No new identity scheme
  is invented; the annotation is computed from data the ledger already holds.

Consequence of (b): σ-fibers is a **derived-consumer feature, not a storage or dreamer-family
change**. Nothing new is persisted at drive time; a consumer annotates after the fact (§2.4).

### 2.3 The persistence functional — definition and three clauses

Fix a pipeline p ∈ {phase7, dream_v2}, the swept range `[σ_lo, σ_hi]`, and a uniform grid
`Γ_m = {σ_i = σ_lo + i·Δσ : i = 0..m−1}`, `Δσ = (σ_hi−σ_lo)/(m−1)` (the shipped instance:
m = 21, `config/sweeps/dreamer-sigma-ab.toml`). For a claim identity χ and k seeds:

- **Per-cell emission:** `e(χ, σ_i) = 1` iff a run of pipeline p at the cell σ_i emitted a claim
  with `claim_id = χ` in ≥ ⌈k/2⌉ of the k seeds. (Today this collapses to the deterministic
  indicator — §2.1 seed caveat.)
- **σ-support:** `S(χ) = {σ_i ∈ Γ_m : e(χ, σ_i) = 1}`.
- **Hull:** `[σ_min(χ), σ_max(χ)] = [min S(χ), max S(χ)]` — σ_max is the *strictest* threshold
  at which the claim still appears (its birth, reading the filtration from sparse to dense);
  σ_min the loosest.
- **Persistence (the strength scalar):** `pers(χ) = |S(χ)| / m ∈ (0, 1]` — the fraction of the
  declared σ-range on which the claim is emitted. The **support measure, not the hull length**:
  gaps do not count. By §2.1 fact 3 the true support set `Σ*(χ)` is a finite union of intervals
  with breakpoints at cosine values, and `pers(χ)` converges to `λ(Σ*(χ))/(σ_hi−σ_lo)` as m→∞,
  with discretization error ≤ B·Δσ/(σ_hi−σ_lo) for B boundary crossings.
- **Gap flag:** `gap(χ) = 1` iff S(χ) is not a single run of consecutive grid indices
  (grid-adjacency exactly as `select` uses `grid_index`, `eval/harness/sweep.py:273-285`).
  Non-contiguity is diagnostic — under deterministic pipelines it means the claim's identity
  flickered across a breakpoint (see the identity caveat below), never noise.

**Deliberately excluded from `pers`:** the objective value ȳ, the adjudicator confidence c(κ),
any weighting. Strength is purely structural. Folding belief into strength would recreate the
one-scalar conflation the adjudicator explicitly forbids ("c decides what to *believe*, utility
decides what to *surface*; one scalar is forbidden" — `core/dreaming/adjudicator.py:20-21`), and
at n≈13 scalar weights are fiction (dn-evaluation-harness §2.6).

**The identity caveat (the honest limit of v1).** `pers` tracks *exact* claim identity. A
community that morphs as σ falls — {A,B,C} at σ=0.70 gaining D at σ=0.65 — is two claim_ids,
each with short support, though the underlying feature persisted. Exact-identity persistence is
therefore a **conservative lower bound** on feature persistence (the matching/elder-rule problem
of persistent homology, deliberately not solved in v1). v2 — matching claims across adjacent
cells by support-set Jaccard, reusing the adjudicator's existing union-find machinery
(`adjudicator.py:66-80`) — is parked with re-entry: the §2.5 validation shows planted features
scored weak *because they morph* (see Parked).

**Three clauses (the bp-049 §8 discipline):**

- *What it measures:* per content-addressed claim, the fraction of the declared σ-range on which
  the pipeline emits it (seed-majority), plus its hull and gap flag; distribution aggregates over
  the claim set per (pipeline, corpus_ref).
- *Validity assumptions:* one corpus snapshot across all cells (the shared `corpus_digest`
  Merkle root guarantees detection of violation, `shadow.py:75-91`); pipelines deterministic
  given (config, seed) — true today, model-free by construction; the grid dense enough that the
  discretization bound is small relative to the tiers' θ separation (m=21 ⇒ Δσ=0.01 on a
  0.20-range: error ≤ 0.05·B_normalized — report it, never hide it); comparisons only within an
  identical resolution descriptor π (§2.6).
- *The observable that falsifies it:* **(i) the degeneracy anchor** — on a synthetic corpus
  with planted pairwise cosines, a bare-edge claim's `pers` must equal the analytic value
  `(min(w, σ_hi) − σ_lo)/(σ_hi−σ_lo)` clipped to [0,1]; disagreement means the computation is
  broken. **(ii) the ruler test** — recomputing on a refined grid (2m−1, which contains Γ_m)
  must move any `pers(χ)` by no more than the stated discretization bound; a larger move means
  the metric is measuring the grid, not the claim. **(iii) earning-its-place** — if the tiering
  built on `pers` (§2.5) fails its gate falsifier, the metric is recorded as *no signal at this
  scale* and parked with a corpus-growth re-entry (dn-evaluation-harness §2.3 clause 2), never
  kept because the math is pretty.

### 2.4 The harness realization — a derived consumer, no schema change

**A correction to the warrant capsule, recorded:** the capsule asserted the persistence metric is
"computable from `EvalResultsStore.query` alone." Not quite — the eval store holds *scalar
metric readings* per cell (`eval/harness/store.py:30-44`), while claims live in the **run
ledger** (`dream_claims`, keyed to runs that carry `config_fingerprint` + `corpus_digest`,
`core/stores/runledger.py:76-101`). The capsule's *spirit* holds exactly: σ-fibers is a derived
consumer over **existing per-σ series in existing stores, zero schema change** — but the
per-claim layer reads the RunLedger and the aggregate layer writes the eval store:

1. **Reconstructing the cell→σ join, model-free.** `dream_runs.config_fingerprint` identifies a
   cell but is a sha256 — you cannot read σ out of it. The sweep engine holds the map only
   in-memory (`DriveResult.fp_to_value`, `eval/harness/sweep.py:297-303`). The consumer
   *regenerates* it: `_config_fingerprint` is a pure function of config
   (`core/dreaming/shadow.py:94-113`), so for a declared grid it recomputes
   `fp(replace(cfg, dream_rnd=replace(rnd, sigma=σ_i)))` per σ_i and joins. **Pin:** the
   fingerprint hashes *every registered lever*, so the reconstruction must run under the same
   lever registry and base config as the drive night — the consumer therefore records its grid,
   base fingerprint, and lever-registry state in its own evidence at run time, never relying on
   late reconstruction across registry versions (a bp-046-widening would silently re-key).
2. **The per-claim layer** (RunLedger → annotations): group `dream_claims` by `claim_id` across
   the joined cells; compute `(pers, hull, gap)` per claim per pipeline. Output is a report
   artifact (E4 tenant) — *not* a new store, *not* a DreamLogEntry field change (parked).
3. **The aggregate layer** (→ EvalResultsStore): distribution summaries as registered readings —
   `sigma_persistence.mean`, `.p50`, `.max`, `.frac_ge_strong`, `.n_claims` — keyed by
   `EvalKey(spec_hash, corpus_ref, config_fingerprint, seed)` where `spec_hash` carries the
   fibers instrument id+version **and the grid descriptor π** (spec_hash is defined as
   "instrument id+version ‖ pipeline ‖ battery params", `store.py:32` — the grid is a battery
   param), `corpus_ref` is the shared Merkle digest, and `config_fingerprint` is the *base*
   config's. This is the same discipline bp-049 held: consume `query`, write keyed readings,
   never re-key, never overwrite.
4. **Registry rows** (`eval/harness/registry.py:24-32`): the `sigma_persistence.*` family with
   `type_tag = "Res(sigma)"` (§2.6), `source_instrument = "row15-sigma-fibers"` (a new catalog
   row), `comparability = "same corpus_ref, identical resolution descriptor π; never across
   grids/ranges without a declared transport"`, `assertion_shape = "regression"`,
   `guardrail_eligible = False` (descriptive, not a bright line). **Gated on the companion
   note's ratification** (the tag extends ratified §2.3 vocabulary); recorded fallback if the
   owner rejects Res(π): register as `Inv` with the grid pinned in `spec_hash` and the same
   comparability string — strictly weaker typing, identical arithmetic. Sibling of
   finding-0086's `structural_axes.*` registration rider — one registration pass covers both.
5. **The exact evaluator (cheap, optional, the falsifier's instrument).** By §2.1 fact 3 the
   consumer *can* run grid-free: enumerate distinct `sim` entries in `[σ_lo, σ_hi]` (≤ 78 at
   n=13), evaluate the pipeline once per equivalence interval, and compute `λ(Σ*(χ))` exactly.
   v1 ships the grid estimator (it reuses sweep nights for free); the exact evaluator is the
   §2.3 falsifier-(ii) instrument and the natural unit-test oracle.

**What the sweep already gives away free (a correction to the capsule's framing):** the capsule
said "today we discard the grid after picking a value." At the data layer nothing is discarded —
the eval store and run ledger are append-only and retain every cell (`store.py:100-111`,
`runledger.py:150-168`); only the in-memory fp→σ map evaporates, and item 1 regenerates it. So
`select` (bp-049 §8) and the fibers consumer are **two consumers of one already-retained
series**: the SELECTION consumer collapses the family to a value; the RETENTION consumer scores
each claim across it. One overnight σ-sweep (the run owed under oq-0024) feeds both.

**Cost and the memory ceiling (parked decision 3, resolved).** The drive phase is bp-049's
existing profile: 21 cells × 5 seeds × 2 pipelines = 210 shadow runs/night, model-free (the
dream_v2 step-8 synth is never reached, `shadow.py:19-22`) — **zero models resident**. Ledger
growth ≈ 210 runs × O(10) claims ≈ low-thousands of SQLite rows per night — negligible. The
consumer is arithmetic over two local stores — seconds, no model. The only model-bearing
extension anywhere in this design is parked FB-4 (per-tier dreamer instances), which if ever
unparked runs batched/overnight with ≤ 1 model resident, serialized under the scheduler's
refusal. The ceiling is untouched by everything this note licenses.

### 2.5 The strength→surfacing gate — pinned before any build

**The boundary conditions (non-negotiable, inherited):**

- **I1 stands absolutely:** persistence never changes an edge weight, a confidence, or a
  promotion — "a derived node's edge weights are increased only through an explicit owner
  verdict … never automatically" and "no Dreamer-confidence-based weighting of derived content,
  ever" (`recursive-strata.md` §4 I1, §9). The gate filters **surfacing** of PROPOSED-tier
  candidates only.
- **No scalar fusion:** `pers(χ)` is never multiplied into c(κ) (`adjudicator.py:20-21`); the
  gate is a two-axis lexicographic rule, matching the house pattern
  (no-regression-on-all + improvement-on-headline, never scalar weights —
  dn-evaluation-harness §2.6).

**The rule.** Two thresholds `0 < θ_weak < θ_strong ≤ 1` partition claims into three tiers:

```
pers(χ) ≥ θ_strong                  → SETTLED   surfaced as a strong association
θ_weak ≤ pers(χ) < θ_strong         → HUNCH     surfaced only in a capped, labelled hunch section
pers(χ) < θ_weak                    → RETAINED  ledger-only; never surfaced
```

Within a tier, ordering is by confidence c(κ) alone (belief stays the ranking axis). Every
surfaced item remains a hypothesis awaiting verdict (the E6 review REPL / report layer); the only
crossing into authored remains owner ratification. Provisional defaults, recorded for
calibration, not asserted: `θ_weak = 2/m` (at least two grid cells — kills single-cell
flickers), `θ_strong = 0.5` (the claim holds on half the declared σ-range). Both join the
`THRESH` lifecycle — "thresholds are tuning, not code"
(`tests/quality/test_dreamer_quality.py:456`, dn-dreamer-quality-suite §5) — tuned by the
harness, blessed like any lever, never hardcoded.

**Validation against F9 — measured, not asserted (the capsule's requirement).** The brainstorm's
premise "low σ ⇒ higher apophenia risk" is itself a hypothesis; the gate earns its place on
F9's fixtures (the F1 noise / planted-structure corpus variants, dn-dreamer-quality-suite §6):

1. run the fibers consumer over a sweep of each fixture;
2. measure the per-σ false-claim rate on pure noise (this *tests* the premise) and the tier
   assignment of planted-structure claims;
3. the gate ships iff: on pure noise, SETTLED-tier claims ≈ 0 (the apophenia guard extended
   along σ) **and** planted claims reach SETTLED **and** persistence-tiering strictly improves
   surfaced-claim precision over the best single-σ baseline (the bp-049-selected σ) on the same
   fixtures.

**The gate's own three-clause falsifier:** (i) noise-fixture claims reach SETTLED at ≥ the
single-σ baseline's rate → the gate does not filter apophenia → it must not ship; (ii) planted
claims land below HUNCH → over-filtering (first suspect: the §2.3 identity caveat — trigger the
v2-matching park's re-entry); (iii) tier assignment changes no ordering that confidence alone
would not produce → persistence is redundant at this scale → record *no signal at this scale*,
park with corpus-growth re-entry.

### 2.6 The typing verdict — `Res(σ)`, a result class; NOT a scope coordinate

Worked in full in the companion (`dn-resolution-result-typing`); the ruling this note consumes:

- **σ-persistence is not honest as bare `Inv`.** It is invariant under grid *refinement* (the
  §2.3 convergence) — that argues Inv — but it depends irreducibly on the declared range
  `[σ_lo, σ_hi]`: change the ruler and every strength rescales. Tagging it `Inv` invites exactly
  the A7-class failure Rule CLOCK forecloses for rates (`capability-scope-algebra.md:116`, §2.3
  there): a strength compared across unacknowledged rulers. It is not a `Rate(κ)` either — no
  clock, nothing eventful divides into it (`core/scope.py:171-175`: clocks coarsen the ledger's
  causal order; σ orders nothing).
- **So the value must carry its ruler:** `pers` is typed `Res(π_σ)` with
  `π_σ = ("sigma", [0.55, 0.75], Γ)` carried like Rate carries its clock
  (`core/scope.py:596-601`), comparability iff π-identical.
- **And scale must NOT enter the scope object.** For every σ, σ′ the required capability is the
  same constant: `req(dream@σ) = req(dream@σ′) = MirrorView.SCOPE` (`core/mirror.py:76-82`) —
  the graph is built from an already-admitted view (`graph.py:33-36`), and every σ reads
  identical rows under the identical grant. σ is invisible to ⊑/meet/join, so no lattice
  expression can distinguish resolutions, and adding a fifth scope coordinate would be a
  fictional capability. The founding capsule's claim "local vs macro scope IS the scope
  algebra's meet/join" is hereby corrected: meet/join governs *strata extent* (Σ), not
  *resolution within a stratum* — resolution is result-typing.

### 2.7 The query surface — a resolution parameter, in the house posture

The three multi-resolution threads press identically here (the capsule's "strongest test"). The
shape, pinned once: **resolution enters queries as an optional instrument parameter that never
touches admissibility** — a sentence is `(verb, s, π?)` with `admissible(verb, s, π) ⟺
admissible(verb, s)` (π-erasure; companion note §2.3). Surface posture follows
`grouped_semantic_search` exactly (`core/ingest/index.py:124-138`): a separate opt-in entry
point per query family, the flat/default path byte-identical (the recursive-strata I3
floor-zero posture). The concrete v1 sentences, all served by the fibers consumer's output —
"claims with `pers > θ`", "the σ_max at which this claim is born", "the claim set at grain
σ = x" — are report/REPL reads, not vector-store changes. "Retrieve at grain g" (the smear's
sentence) inherits the same π-shape *if its own park ever re-enters* — pinned here so the shape
is named once, built zero times prematurely.

### 2.8 The dreamer-family axes — and the meta-pattern ruling

The founding capsule asked where scale sits among synchronic/diachronic and mirror/cross-strata.
The answer, now typeable: **the three axes land in three different slots of the existing type
system** —

| axis | lives in | example |
|---|---|---|
| temporal (synchronic/diachronic; local/global clock) | `T = (clock κ, window)` of the scope; readings `Rate(κ)` | dream_v2 = point-window synchronic; DD-1 = interval-window diachronic |
| scale/resolution (tight/loose; σ, grain, depth) | the **result** descriptor π — never the scope (§2.6) | a "tight" reading of G_{0.70} vs a "loose" reading of G_{0.60}, both under `MirrorView.SCOPE` unchanged |
| strata (mirror-only / cross-strata) | Σ of the scope; firewall ideals | Idea A: Σ = {mirror_authored}; Idea B: the owner-granted join (companion note) |

One consequence worth stating plainly: **"multi-scale dreamers" require no new dreamer family
and no new boundary.** A tight and a loose reading are the same pipeline at two π values over
one unchanged `MirrorView` — which is why the whole of Idea A reduces to a consumer plus a gate.

**The meta-pattern ruling (the doc-code-entanglement capsule's question, answered at the
cheapest moment):** what generalizes across σ-fibers / chunk-smear / conversation-layers is the
**typing and comparability discipline** — a scale-family confounds rulers identically in all
three, so `Res(π)` is parameter-generic (π_σ, π_grain, π_depth) and is lifted ONCE into the
companion algebra note. What does **not** generalize is the fusion instrument: selection
(bp-049 §8 `select`), retention-scoring + tiering (this note), and privacy-ordering
(L2→L1→never-L0) are three different rules with three different falsifiers. No
"scale-as-a-dimension framework" note is warranted — the resonance is real, the shared part is
the type, and forcing more would abstract three worked instruments into one unworkable one. The
smear's evidence bar is explicitly unchanged.

### 2.9 Constraints honored (the binding table)

| constraint | binding form here |
|---|---|
| Mirror firewall (I6) | every read is `MirrorView`-mediated (`mirror.py:96-101`); σ varies a *derived construction*, never the read boundary; fibers consumer reads RunLedger + eval store, both ∉ `MIRROR_READABLE` |
| I1 / no auto-promotion | persistence gates surfacing only (§2.5); weights, confidence, promotion untouched; owner verdict remains the only crossing |
| The model advises; code acts | consumer + gate are arithmetic; no model in any path this note licenses (parked FB-4 is the only exception, gated) |
| Memory ceiling ≤ 2 residents | zero residents for everything licensed (§2.4 arithmetic) |
| Sacred fixed points | untouched; `eval/golden/**` read via built loaders only; no lever can name them (dn-evaluation-harness §2.6) |
| No silent caps | discretization bound reported per §2.3; capped HUNCH section labelled with its cap; gaps flagged, never smoothed |
| Append-only stores | consumer writes new keyed readings only; never re-keys, never overwrites (`store.py:100-111`) |

## 3. Consequences — the build decomposition this note licenses (on ratification)

Session-sized candidates, blast-radius ordered; `/graduate` decides final splits.

- **FB-1 — the fibers consumer** (`eval/harness/fibers.py` + a script entry): the fp→σ
  reconstruction (§2.4.1), per-claim `(pers, hull, gap)` (§2.4.2), aggregates into the eval
  store (§2.4.3), the exact-partition evaluator as test oracle (§2.4.5), report section (E4
  tenant). Model-free, read-only over ledger + store, no schema change. Depends on nothing
  unbuilt — it can consume the first real σ-sweep night (oq-0024's owed RUN) as its first
  dataset: one night, two consumers.
- **FB-2 — registry + catalog rows**: `sigma_persistence.*` registered per §2.4.4; catalog
  row 15. **Depends on `dn-resolution-result-typing` ratification** (fallback recorded).
  Riders with finding-0086's `structural_axes.*` registration.
- **FB-3 — the surfacing gate + F9 validation**: tier assignment in the report/REPL layer (E6
  tenant), θ levers under THRESH lifecycle, the §2.5 validation protocol run on the F1-variant
  fixtures, the gate falsifier as tests. Depends on FB-1; ships only if the §2.5 gate criteria
  hold.
- **FB-4 — PARKED: σ-tiered dreamer instances** (candidate (c) revisited — a "tight" and a
  "loose" synthesis pass). Re-entry: FB-3 validated AND the owner wants tier-differentiated
  synthesis; batched/overnight, ≤1 model resident, scheduler-refusal binds.

## Parked decisions

| id | decision | default recorded | re-entry condition |
|---|---|---|---|
| SF-a | claim matching across σ (v2 persistence; elder-rule/Jaccard union-find) | exact-identity persistence only (conservative lower bound) | §2.5 falsifier (ii): planted features score weak because identity morphs |
| SF-b | σ-persistence as a drift axis (μ absorbs it per the A2 contract) | registered metric only; NOT a drift axis | its distribution stabilizes across ≥ 4 weeks of longitudinal curves (the §2.5-lifecycle bar); then the A2 axis question re-opens |
| SF-c | per-tier dreamer instances (FB-4) | not built | FB-3 validated + owner demand |
| SF-d | DreamLogEntry carries persistence as a field | report-layer annotation only (no core type change) | the REPL needs it inline for verdict ergonomics (E6 evidence) |
| SF-e | θ defaults | θ_weak = 2/m, θ_strong = 0.5 (provisional) | first F9 validation run calibrates; owner blesses via THRESH lifecycle |
| SF-f | exact evaluator as the production path | grid estimator (reuses sweep nights free) | a consumer needs exact persistence (e.g., SF-b) or grids stop being free |

## Cross-references

- **Warrant:** `docs/brainstorms/cross-strata-and-multiscale-dreamers.md` — the founding capsule
  (Idea A/B split), the σ-fibers capsule (2026-07-16T17:18), the harness×algebra capsule
  (2026-07-16T17:32). Two capsule claims corrected above, recorded: "EvalResultsStore.query
  alone" (§2.4) and "local-vs-macro scope is meet/join" (§2.6).
- **Companions:** `docs/design-notes/resolution-result-typing.md` (the Res(π) amendment — FB-2
  gates on it); `docs/design-notes/cross-strata-dreamer.md` (Idea B).
- **Code (verified on disk 2026-07-16):** `core/dreaming/graph.py` (:28,:33-40),
  `core/dreaming/shadow.py` (:19-22,:75-113,:147-148,:152-212), `core/stores/runledger.py`
  (:37-42,:76-101,:150-168), `eval/harness/store.py` (:30-55,:100-151), `eval/harness/sweep.py`
  (:241-289,:297-303), `eval/harness/registry.py` (:24-32), `ops/levers.py` (:112-122),
  `core/mirror.py` (:76-82,:96-101), `core/provenance.py` (:78-80),
  `core/dreaming/adjudicator.py` (:8-24,:46-58,:66-80), `core/scope.py` (:171-184,:586-619),
  `core/ingest/index.py` (:124-138), `config/sweeps/dreamer-sigma-ab.toml`,
  `tests/quality/test_dreamer_quality.py` (:456).
- **Design:** `dn-evaluation-harness` §2.1/§2.3/§2.5/§2.6/§2.8; `dn-capability-scope` §2.3;
  `dn-dreamer-quality-suite-evaluation` §1/§5/§6; `dn-recursive-strata` §4 I1/§9;
  finding-0086 (registration rider); bp-046/bp-049 (the machinery consumed); oq-0024 (the owed
  σ-sweep RUN that doubles as FB-1's first dataset).
