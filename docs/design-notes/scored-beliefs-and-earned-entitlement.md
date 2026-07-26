---
type: design-note
id: dn-scored-beliefs-and-earned-entitlement
track: scored-beliefs      # manifest minted with this note (docs/tracks/scored-beliefs.md); owner renames/rejects at ratification
status: draft            # draft → ratified → superseded.  draft→ratified is an OWNER-ONLY hand edit.
created: 2026-07-26
updated: 2026-07-26
links:
  - docs/brainstorms/prediction-market-sensor-fusion.md   # THE WARRANT — three capsules 2026-07-26; the last supersedes the earlier ordering
  - docs/brainstorms/dreamer-and-graph-direction.md       # what a dreamer IS; the ledger must carry Σ; the VOICE of a belief
  - docs/design-notes/synchronic-diachronic-dreamer.md    # RATIFIED — §2.7 conditioning law, §2.8 diachronic park; extended, never contradicted
  - docs/design-notes/recursive-dreaming-bounded-by-grounding.md  # the four safety rules; rules 2/3 are this note's scoring kin
  - docs/design-notes/cross-strata-dreamer.md             # RATIFIED — per-grant regime; the harness lane that consumes per-Σ scores
  - docs/design-notes/global-event-clock.md               # RATIFIED — certified cuts, the resolution substrate
  - docs/findings/finding-0217.md                         # filed by this pass — Σ is NOT recoverable after the fact; the ledger is new bookkeeping
  - docs/findings/finding-0126.md                         # the diachronic park's RESTATED re-entry — honored here
  - docs/findings/finding-0141.md                         # dreamers built-not-wired; the deskcheck decision this note's wiring waits on
  - docs/tracks/sync-diac-dreamers.md                     # the owed wire-or-accept-dormant decision — this note's precondition, not its call
supersedes: null
superseded_by: null
warrant: null            # warrant chain is the two 2026-07-26 brainstorms (links above); no supersession here
---

# Scored beliefs and earned entitlement — the ledger the predictors were always owed

> Filed by a dispatched design-tier agent as `draft` (chat-side protocol, §8). Ratification is a
> hand edit by the owner — no command performs it, and `gate-guard` denies any agent attempt
> (§10). `/graduate` refuses this note until `status: ratified`. **Design only; no build is
> authorized by this note.** Code claims were verified on disk this session (2026-07-26, worktree
> at `d54d6b1`); the load-bearing code fact — that a belief's Σ is not recoverable from any
> persisted record — is filed separately as finding-0217 so it survives this note's fate.
> Note on paths: the capability code moved under `core/kernel/` after
> dn-synchronic-diachronic-dreamer was ratified; its citations (e.g. `core/agent_scope.py:143-158`)
> resolve today to `core/kernel/agent_scope.py:143-158` — same content, known repackaging.

## 1. Purpose and scope

The system already makes predictions it never scores. The dreamers ARE the predictors — ratified
design settled that a forecasting capability is a *grant value* on one dreamer role, not a new
agent (`dn-synchronic-diachronic-dreamer` §2.1; `dreamer_scope`,
`core/kernel/agent_scope.py:143-158`) — and the adjudicator already ranks their claims by
grounded confidence. What no machinery does is hold a belief open until reality answers, and
record what the answer was. The missing object is a **ledger of beliefs scored against later
resolution**, and this note designs it.

The thesis, interrogated rather than restated: "score the predictions" sounds like grading, and
grading would be the wrong object. A dreamer's output is a *belief* — defeasible, revisable,
formed over a declared stratum set Σ from what exists (the owner's definition, 2026-07-26). So
scoring one is **belief revision**: the interesting output is not "right/wrong" but *which kind
of wrong* — wrong given everything it could see, or wrong because it could not see enough. Those
two failures are different objects with different consequences (the first indicts the
instruments, the second indicts the grant), and a single scalar destroys the distinction. "The
more you know, the better the view gets" — the project's founding slogan — is precisely the
claim that widening Σ improves the belief. A ledger that does not carry Σ cannot test the
project's own thesis; a ledger that carries it turns the slogan into a measurable (§2.3).

This note decides: the belief record and its Σ/occasion split (§2.1); the resolution classes,
including the contamination law for owner-in-the-loop resolution (§2.2); the two-failure
attribution and the thesis test (§2.3); the read-only law and where the revision loop actually
closes (§2.4); scoring rules per claim family and the credence/confidence distinction the code
forces (§2.5); earned entitlement as per-domain evidence at owner gates (§2.6).

### 1.2 Non-goals (load-bearing — the owner reads this section explicitly at ratification)

Sources marked: a non-goal is either READ from the warrant/ratified record, or `[INFERENCE]` —
inferred by this pass and checkable at ratification (finding-0150 discipline).

- **No market access, no Polymarket, no money, no wallet, no `edge/` surface.** READ — the
  warrant's final capsule reorders the program: synchronic claims scored against later certified
  cuts are the first experiment, "internal, free, no market, no credential, no frame amendment";
  Polymarket stays parked behind the ledger *and* the 10-resolved-markets kill test.
- **No diachronic execution.** READ — §2.8's park stands with the finding-0126 restated re-entry
  (the `graph-at-a-past-cut` family graduates AND D-1 is sealed). Diachronic *claims* are
  therefore unscorable here too: nothing can emit them.
- **No automatic score→capability coupling.** READ — the warrant's own open question notes the
  72-state gate's authorization is flag-derived today, so "earned grant" as a gate *input* is a
  change to a ratified mechanism — a future design-note supersession, not this note and not a
  build (§2.6, parked BL-e). Entitlement output here is evidence presented at owner-only gates.
- **No global trust score.** READ — rejected in the warrant with re-entry "never, unless someone
  produces evidence that calibration transfers across action classes." Adopted verbatim (§2.6).
- **No new predictor.** READ — the dreamers are the predictors; this note adds zero forecasting
  machinery, only recording, resolving, and attributing.
- **No wire/dormant decision for the dreamers.** READ — that decision is owed at the
  sync-diac-dreamers deskcheck (finding-0141) and is the owner's. This note makes the ledger
  ready to receive it, never makes it (§4).
- **No change to the adjudicator's confidence law.** `[INFERENCE]` — c(κ) = min{1, γ^d·g·(1+λ(|Agr|−1))}
  stays exactly as built; the ledger adds a *separate* credence field rather than reinterpreting
  c as a probability (§2.5). Inferred from the code's own insistence that c is not a probability;
  the owner may instead want the confidence law revisited — that would be a different, bigger note.
- **No scoring of the owner's own authored content.** `[INFERENCE]` — the ledger grades system
  beliefs, never the owner's notes. Inferred from the mirror-not-oracle posture; nothing in the
  warrant states it, and it fails silently if wrong (a "grade the owner's predictions too" reading
  of the corpus-as-self-map is conceivable and is explicitly not designed here).
- **No retroactive scoring of pre-ledger dreams.** `[INFERENCE]`, warranted by finding-0217 —
  their Σ was never recorded and is recoverable only by the class-constant convention
  (`MirrorView.SCOPE`); scoring them would smooth over exactly the distinction the ledger exists
  to draw. Parked BL-f with an owner override.
- **No occasion-computation machinery.** READ (partially) — "becoming relevant" may require an
  input the dreamer does not have (the ambassador thread's inbound channel, per the voice
  capsule). The ledger *records* an occasion when one exists; computing occasions is that
  thread's problem, not this note's.

## 2. Principles / decision

### 2.0 The DRY audit — what exists, and the three genuinely new things

Per the §2-manifest discipline, the machinery this note rides, verified in code 2026-07-26:

| capability | existing home | status |
|---|---|---|
| the predictors (dreamer role, per-grant dispatch) | `dreamer_scope` + `DreamCharter` (`core/dreaming/charter.py`) | built, NOT wired (finding-0141) |
| Σ fully typed per dispatch | `DreamCharter.grant: Scope` | built, in-memory only (finding-0217) |
| grounded confidence c(κ), explicitly not a probability | `core/dreaming/adjudicator.py`, `core/kernel/recursion.py` | built |
| confidence/utility as separate axes, never collapsed | recursive-dreaming rule 3 | ratified posture; this note's scalar-refusal is its kin |
| resolution substrate — certified cuts, refusal-not-fabrication | `core/temporal/spine.py:159-274` (GC-3, bp-055) | built |
| resolution-by-adoption — owner verdicts (endorse/retract/record) | `verdict_dispositions` + `core/kernel/provenance.py` promotion stub | built (taxonomy pending) |
| the with/without diff (influence = taint attribution) | §2.7 conditioning law; `core/dreaming/conditioning.py` | built (flag-off) |
| lineage by content address | `derives` hyperedges, attestations (`core/attestation/`) | built |
| per-grant A/B evaluation lane | dn-cross-strata-dreamer owner ruling; eval harness | ratified design |
| revocation-shaped drift signal (effector domains) | `eval/effector_drift.py` | built, nothing wired (finding-0011) |

**Genuinely new — exactly three things:** (N1) the **belief record** + charter persistence at
emission (§2.1 — new bookkeeping; finding-0217 proves it cannot be a read over existing state);
(N2) the **resolution sweep** with its class taxonomy and contamination law (§2.2); (N3) the
**Σ-attribution replay** and the per-domain entitlement dossier over it (§2.3/§2.6). Everything
else is composition.

### 2.1 BL-1 — the belief record: a belief is (claim, credence, Σ, occasion), and Σ must be persisted at emission

A scorable belief is a typed record written when a dreamer dispatch surfaces a forward-looking
claim:

1. **The claim** — statement in the belief register (first-person, hedged — the voice capsule:
   "I think this will happen, I think I see this pattern…"), PLUS a **truth-condition**: the
   observable that resolves it, decidable against a future certified cut, stated at emission.
   Pre-registration is the discipline, for the same reason the warrant wrote falsifiers before
   reading outputs: fluent narration is exactly what tempts a post-hoc bar. A claim whose
   truth-condition cannot be stated is not scorable and does not enter the ledger (it may still
   be a dream; the ledger is a subset of dream output, not a replacement for it).
2. **The credence** — a stated p ∈ [0,1], elicited at emission, distinct from c(κ) (§2.5).
3. **The Σ** — the dispatch's charter, persisted: the grant's strata, the cut id, gauge,
   generation (if counterfactual), instrument set, budget, plus the charter's content digest.
   **This is the finding-0217 consequence and the record's spine:** no persisted surface carries
   Σ today — the charter is in-memory, the dream log records the *support* set (cited evidence),
   attestations record `input_hashes` = cited digests, and the one live path's Σ is a class
   constant recoverable only by convention. The support set cannot substitute: Σ is *intensional*
   (what could be seen), evidence is *extensional* (what was used), and the difference between
   them — what the dreamer could see and did not cite — is precisely the §2.3 discriminator.
   So Σ is written at emission or it is lost; there is no back-fill.
4. **The occasion** — what made the belief worth surfacing *now*, when one exists: the live
   problem or retrieval context it bore on. **Σ and occasion are different objects and the
   ledger treats them differently:** Σ is constitutive (part of the belief's identity; enters
   the score's conditioning), occasion is circumstantial (recorded as metadata; NEVER enters the
   score). Scoring occasions would select for flashy occasions — the utility/grounding collapse
   of recursive-dreaming rule 3, one level up. Occasion has exactly two ledger uses: the
   surfacing decision (a true-but-inert belief fails NAME-THE-READER; the ledger still records
   it, unsurfaced) and the §2.2 contamination classification.
5. **The emission anchor** — the certified cut the belief was formed at (already inside Σ's
   T-coordinate; named separately because resolution horizons are measured in *cuts*, never wall
   time — Law C4; a wall timestamp rides along as owner convenience only).
6. **Lineage** — evidence digests and attestation id, as today. The record extends the existing
   discipline; it replaces nothing.

### 2.2 BL-2 — resolution: later cuts answer, and the owner in the loop contaminates

A belief resolves when a later certified cut decides its truth-condition. The classes:

- **R-INDEPENDENT** (the clean channel): the resolving evidence entered the corpus through work
  not downstream of the belief's surfacing — the owner authored the claimed connection without
  having been shown the belief, or the claimed structure dissolved on its own. This is the only
  class that measures *foresight*.
- **R-ADOPTION**: the owner saw the surfaced belief and ruled on it — which is the existing
  verdict machinery (endorse/retract dispositions), not a new mechanism. Valuable, and
  **scored separately**: adoption measures plausibility-to-the-owner, not foresight. The
  existing disposition channel IS this resolution class, already built; the ledger consumes it,
  never duplicates it.
- **R-STILL-OPEN**: unresolved after the horizon (measured in cuts). Not a failure — but the
  ledger reports the open fraction, because of the starvation risk below.
- **R-ILL-POSED**: the truth-condition turns out undecidable at resolution time. Scored against
  the emitter as a register defect: an unresolvable "belief" was narration wearing a belief's
  clothes.

**The contamination law (new, and the warrant did not name it).** The scoreboard has the owner
inside it: surface a belief → the owner reads it → the owner writes it down → "confirmed." That
loop is self-fulfilling — the resolution is downstream of the surfacing — and it is the
hypothesis-laundering shape running *through a human* instead of through dream exhaust. So:
**a belief's surfacing events are recorded in the ledger, and any post-surfacing owner authorship
that matches the claim resolves it as R-ADOPTION, never R-INDEPENDENT.** The clean channel is
only ever fed by pre-surfacing or never-surfaced beliefs. Consequence, stated honestly: the
cleanest calibration data comes from beliefs the owner never saw — which is in tension with
surfacing being the point of dreaming. The design accepts the tension: the ledger records *all*
beliefs (surfaced or not); the unsurfaced ones are the control arm the surfaced ones can be
compared against. Whether the two arms score differently is itself a finding the ledger can
produce.

**Resolution scarcity — the honest viability risk.** A prediction market resolves by
construction; the owner's corpus resolves only when later work happens to bear on a claim.
Nothing guarantees the resolution rate is nonzero at this corpus's scale. This is stated as a
falsifier (F-BL4) rather than smoothed over: if the ledger starves, the internal-first ordering
was optimistic and the external scoreboard question re-opens *on that evidence* — which is
exactly how the warrant wanted the Polymarket decision made.

### 2.3 BL-3 — the two-failure attribution: wrong-given-Σ vs Σ-too-narrow, and the thesis test

On a refuted belief, the ledger runs the **attribution replay** — the §2.7 with/without diff
reused on the grant axis instead of the overlay axis:

1. **Reproduce**: re-run the belief's formation over its recorded (Σ, cut, instruments). The
   formation path below narration is deterministic (the panel/adjudicator is model-free by
   design — "no model scores argument quality here"), so the claim must reproduce bit-comparably.
   Failure to reproduce is F-BL6 and invalidates the attribution, loudly.
2. **Attribute**: locate the refuting material at the resolving cut. If it lay *inside* the
   belief's Σ-materialized view at formation time (present, visible, uncited or misread) →
   **wrong-given-Σ**: the instruments or the formation misread what was seeable. If it lay
   *outside* Σ (in strata not granted, or in events after the formation cut) → **Σ-too-narrow**:
   the grant, not the reading, bounded the belief.
3. **Record both coordinates, never their collapse.** The ledger's unit of account is the pair
   (outcome, attribution), plus the credence for calibration. A scalar "score" may be *derived*
   for a specific reader (a calibration curve needs numbers), but the stored record must always
   reproduce the split — F-BL3 makes storing only a scalar a design violation, not a shortcut.

**The thesis test — the reason the ledger exists.** "The more you know, the better the view
gets" becomes: *across matched claims, do beliefs formed over wider Σ score better, and does the
Σ-too-narrow failure class shrink as granted Σ widens?* The per-grant harness lane
(dn-cross-strata-dreamer's owner ruling: each grant owner-declared, harness-evaluable) is the
natural consumer: per-Σ score distributions are exactly what a per-grant A/B wants and never had.
If widening Σ does **not** improve scores — if the wider view dreams worse, or no better — the
slogan is falsified as measured, and that is a first-class result this project's doctrine
(ratify falsifiers) is built to want. This is the note's central falsifier, F-BL1.

### 2.4 BL-4 — the read-only law: the ledger grades the dreamer, so the dreamer never reads it

**The law:** the ledger is READ-ONLY with respect to dreamer inputs — no dreamer dispatch, under
any grant, can materialize a ledger row. This is §2.7's fifth safety rule applied to the
instrument that grades it: a dreamer that can read its own scores will (by optimization or by
accident of retrieval) condition beliefs on what scored well, which is hypothesis laundering
with the grader as the launderer. The structural form: **the ledger is machinery, not corpus.**
It is not a `Stratum`; no grant can name it (there is nothing to name — Σ ranges over R, and the
ledger is outside R); its store is eval/ops-side, per the core template ("core computes and
returns pure data; the machinery calls core, records, grades, runs") and the grading rule ("the
agent that made a change never grades it," CONVENTIONS §Testing). A dreamer cannot be granted
the ledger for the same structural reason it cannot be granted the golden set.

**Where the revision loop actually closes — the tension interrogated.** The warrant says scoring
a belief is belief *revision*, and revision implies the belief's owner learns. Read-only seems to
forbid that. The resolution: **scores revise grants and records, never formation inputs.** The
loop is: beliefs → resolutions → the ledger's reports → `/triage` → the owner adjusts grants
(widen a Σ that keeps failing narrow, retire an instrument that keeps misreading) or ratifies
design changes → new beliefs under better grants. Every arrow crosses an existing gate; the
feedback is real, closed, and *slow on purpose* — it flows through the capability layer at the
owner's cadence, never through the data layer at the dreamer's. The dreamer does not remember
being wrong; the *system* does, and its memory lives where the dreamer cannot read it. The
residual honest gap: a genuinely self-calibrating predictor (formation parameters tuned by its
own scores) is a real future and the only lawful channel for it is a gated self-mod proposal
(NN-5: propose → human-approve → execute → validate → auto-rollback). Parked BL-a with that as
the re-entry — not designed here, and not reachable by any reading of this note.

### 2.5 BL-5 — scoring rules: credence is not c(κ), and v1 scores only what is binary

**The code forces a distinction the warrant glossed.** The built confidence
c(κ) = min{1, γ^d·g·(1+λ(|Agr|−1))} is *explicitly not a probability* — the adjudicator's own
docstring says so, and its semantics (grounding × corroboration, clamped) confirm it: c measures
*how well-anchored in authored evidence a claim is*, not *how likely it is to come true*. A
proper scoring rule (Brier) is only meaningful over a probability. So the belief record carries
**both, never conflated**: c(κ) (anchoring — what the adjudicator already computes) and the
credence p (forecast — new, stated at emission). Scoring p with Brier grades the register itself:
if the narration's hedges are decorative, the calibration curve will say so. This extends
recursive-dreaming rule 3's two-axes discipline (confidence ≠ utility) with a third axis
(credence), and the same collapse prohibition binds all pairs.

**Per-claim-family rules, v1 binary only.** "Edge (a,b) exists but is unstated" has a truth
value; "this cluster is a theme" does not obviously. v1 admits only claim families with
binary-decidable truth-conditions against a certified cut (structural existence/dissolution
claims — the arrow-read dispatch's census-witnessed family is the exemplar: exact, witnessed,
gauge-immune). Brier over p on those. Non-binary families are parked (BL-b) until each brings
its own rule *and its own falsifier* — a family admitted without a stated rule is how the
post-hoc bar sneaks back in.

**Minimum track record is computed, not tasted.** A Brier mean over N resolutions has a
variance; the N below which a dossier (§2.6) is statistically meaningless has a real answer
computable from the claim mix. Per the warrant, that computation is stated *before* any grant is
defined in terms of the ledger — parked BL-c, blocking every entitlement consumer, none of which
exist yet.

### 2.6 BL-6 — earned entitlement: per-domain dossiers, evidence at gates, decay by default

If entitlement to act is ever earned, it is earned **per-domain and per-effect-class**; the
global trust score is rejected (warrant, adopted verbatim — calibration does not transfer:
well-calibrated on "will X resolve by Y" says nothing about sending an email). The object:

- **The dossier**, keyed by (claim family, Σ region, effect class): resolved-N, outcome and
  attribution distributions, the calibration curve over p, recency. A dossier is a *report over
  the ledger* — derived, regenerable, no new authority.
- **Consumption is evidence at owner gates, full stop.** A dossier is what the owner reads when
  deciding a wire/unpark/ε question — it converts "gain the confidence to act" from a posture
  into a document. It flips nothing. The 72-state gate consuming a dossier as an authorization
  *input* is a supersession-grade change to a ratified mechanism, explicitly out of scope
  (non-goal; parked BL-e).
- **Decay by default.** A track record is not an annuity: the corpus is non-stationary and any
  adversarial domain more so. Dossier weight decays with resolution-cycles-since; a stale
  dossier reports itself stale rather than confidently old. For effector domains the built
  revocation signal (`eval/effector_drift.py`'s blast-radius axis) remains the named companion —
  consumed beside a dossier, never replaced by one.
- **The reader is named** (the process-weight test): (1) the owner at gates, (2) the per-grant
  harness lane (§2.3), (3) — future, gated — the authorization machinery, only after BL-e's
  design pass. A ledger nobody reads is the 5th artifact nothing reads; these three are the
  named readers, and the first two exist.

### 2.7 Constraints honored

| constraint | binding form here |
|---|---|
| §2.7 conditioning law (ratified) | extended: the ledger is a non-input by construction (§2.4); grounding chains can never terminate in a ledger row because no grant can name one |
| the four safety rules (+ fifth) | rule 1 untouched (beliefs cite authored evidence); rules 2/3's axis-separation generalized to credence (§2.5); rule 4 untouched (no promotion path through the ledger) |
| diachronic park (§2.8, finding-0126) | honored: no diachronic claims exist to score; the ledger's design is window-agnostic so unparking adds a claim family, not a schema change |
| the model advises; code acts (NN-3) | scoring, replay, sweeps are code; the model appears only at emission (narration + credence); refusal/attribution is machinery-side |
| self-modification gated (NN-5) | scores reach formation only through BL-a's future gated proposal; no autonomous parameter update exists in this design |
| owner-only blessings | entitlement dossiers inform gates; every gate stays owner-by-hand; nothing here flips on a score |
| sacred fixed points | the ledger is denylist-kin for dreamers (unreadable by any grant); golden set untouched; no lever names it |
| Law C4 (no wall ordering) | horizons and decay are measured in certified cuts; wall timestamps are convenience metadata |
| memory ceiling (NN-8) | the sweep is trough-tier batch work over sqlite; no resident model is added |

## 3. Consequences

On ratification, `/graduate` decides the splits; the natural decomposition, each session-sized,
queued behind the sync-diac-dreamers deskcheck decision where marked:

- **BL-P0 — charter persistence + the belief record** (the finding-0217 bookkeeping): persist
  the charter (digest + grant coordinates) at dispatch; the belief-record store and emission
  hook (a dream whose claim carries a truth-condition + credence writes a record). Additive;
  flag-off; buildable before the wire decision (the emission hook simply never fires while
  `[dream_rnd]` is off).
- **BL-P1 — the resolution sweep**: trough-tier job resolving open beliefs against the latest
  certified cut; verdict-channel ingestion (R-ADOPTION via existing dispositions); the
  contamination classifier over surfacing records. Gated on BL-P0 and on the wire decision
  (nothing resolves if nothing emits).
- **BL-P2 — the attribution replay + thesis report**: reproduce-then-attribute (§2.3); the
  per-Σ report the harness lane consumes; F-BL1's measurement rendered for the owner.
- **BL-P3 — entitlement dossiers**: the keyed reports + staleness/decay + the owner-facing
  render. Blocked by BL-c (minimum-N computed first).
- **Explicitly NOT licensed:** any market/external scoreboard work (BL-d); any gate-input wiring
  (BL-e); any formation-parameter feedback (BL-a); diachronic anything (upstream park);
  retroactive scoring (BL-f).

Book debt: none until something builds; the thesis test, once it has produced one real
measurement, is a chapter-grade arc (the slogan meeting its own scoreboard).

## 4. Wiring & enablement

**How it wires:** three surfaces, all in-scope for the plans above, none deferred: (a) config —
a `[belief_ledger]` section (`enabled`, `resolution_horizon_cuts`, `require_credence`) beside
`[dream_rnd]` in `config/defaults.toml`; (b) the emission hook in the dream path (charter
persisted at dispatch, record written at adjudication) and the resolution sweep enqueued by the
daemon's trough-tier scheduler (`ops/lifecycle/launcher.py` is where the existing sensor jobs
enqueue; the sweep joins them); (c) an owner-facing render — a `scripts/`-level CLI
(`uv run scripts/belief_ledger.py report`, exact home a plan call) that prints open/resolved/
attribution tables and the calibration curve, so the ledger is inspectable from day one.

**What it takes to flip it on:** (a) a build adds the config schema + emission hook + sweep +
CLI (BL-P0/P1); then (b) the owner: resolves the sync-diac-dreamers deskcheck as **wire live**
(`[dream_rnd] enabled=true` — the standing precondition: a predictor that never runs cannot be
scored), sets `[belief_ledger] enabled=true`, and runs the first sweep by hand
(`uv run scripts/belief_ledger.py sweep`) as the owner-visible seed run. If the deskcheck
resolves **accept dormant**, this note's machinery stays correctly unbuildable-to-useful and the
track parks on that decision — stated here so "built but never fed" cannot masquerade as done
(wiring-is-part-of-finishing).

## Parked decisions

| id | decision | default recorded | re-entry condition |
|---|---|---|---|
| BL-a | predictor self-calibration (scores → formation parameters) | never — read-only law absolute in v1 | a gated NN-5 self-mod proposal, after ≥ 1 full resolution cycle exists to justify it |
| BL-b | scoring rules for non-binary claim families ("this is a theme") | excluded from the ledger | a family arrives with its own rule AND its own falsifier; owner admits it per-family |
| BL-c | minimum track-record N | no dossier is citable at any gate | N computed from the actual claim mix and stated in the dossier design before first citation |
| BL-d | external scoreboard (Polymarket) | parked — internal cuts first | the warrant's ordering: the ledger exists and has scored something, AND the 10-resolved-markets kill test passes; F-BL4 starvation may accelerate this on evidence |
| BL-e | the 72-state gate consuming a dossier as authorization input | not an input; evidence-at-gates only | owner requests it after dossiers exist; it is a supersession-grade design pass on the gate, never a build rider |
| BL-f | retroactive scoring of pre-ledger dreams via convention-Σ | never (finding-0217: back-filled Σ is convention wearing a record's clothes) | owner explicitly accepts convention-Σ labeling, marked as such on every such row |
| BL-g | occasion computation (what makes a belief relevant *now*) | occasion recorded when supplied, else null | the ambassador-thread inbound channel (or another source of "current problem") graduates |

## Falsifiers (the load-bearing set — this project ratifies falsifiers, not proofs)

- **F-BL1 — the thesis test (central).** Across matched claims, beliefs formed over wider Σ fail
  to out-score narrower ones, or the Σ-too-narrow failure class does not shrink as Σ widens ⇒
  "the more you know, the better the view gets" is falsified *as measured on the owner's own
  corpus* — the strongest result this note can produce in either direction.
- **F-BL2 — laundering.** Any dreamer formation input derivable from a ledger row (a retrieval
  path, a conditioning term, a prompt fragment) ⇒ the read-only law is theater; the §2.4
  structural claim is wrong and the fifth safety rule is breached by its own grader.
- **F-BL3 — scalar collapse.** A stored record from which the (outcome, attribution) pair cannot
  be reconstructed ⇒ the ledger destroyed the one distinction it exists to carry.
- **F-BL4 — starvation.** After a stated horizon (proposed: 20 certified cuts past first
  emission; owner tunes at ratification) the resolved fraction in the clean channel is below a
  stated floor (proposed: 10%) ⇒ the internal scoreboard cannot feed the thesis test at this
  corpus scale; BL-d re-opens on that evidence.
- **F-BL5 — contamination.** Any R-INDEPENDENT resolution whose evidence chain traces through a
  post-surfacing owner artifact ⇒ the clean channel is polluted and every dossier built on it is
  suspect; the classifier is re-ruled before any further citation.
- **F-BL6 — replay invalidity.** A recorded belief whose formation does not reproduce over its
  recorded (Σ, cut, instruments) ⇒ the attribution is unfounded for that belief (and, if
  systematic, the determinism assumption in §2.3 is wrong and attribution needs a redesign, not
  a patch).

## Cross-references

**Warrant:** `docs/brainstorms/prediction-market-sensor-fusion.md` (all three 2026-07-26
capsules; the third's reordering governs) · `docs/brainstorms/dreamer-and-graph-direction.md`
(the 2026-07-26 capsules: the dreamer definition, Σ-carrying, the voice/register spec).

**Code (verified on disk 2026-07-26, worktree at `d54d6b1`):**
`core/dreaming/charter.py:155-222` (DreamCharter — Σ typed, unpersisted) ·
`core/dreaming/adjudicator.py:1-25,138-167` (c(κ) "NOT a probability"; `run_dream_rnd`'s
persisted fields — no Σ, no cut, no attestation) · `core/dreaming/dreamer.py:139-149,221-228`
(attestation inputs = cited evidence) · `core/attestation/record.py` (extensional hashes only) ·
`core/kernel/agent_scope.py:143-158` (`dreamer_scope`) · `core/kernel/mirror.py:76-82`
(`MirrorView.SCOPE`, the convention Σ) · `core/kernel/scope.py:60-100` (Stratum — the ledger is
deliberately not here) · `core/temporal/spine.py:159-274` (certified cuts — the resolution
substrate) · `core/dreaming/rnd.py:31` + `config/defaults.toml` `[dream_rnd]` (the flag whose
decision gates emission) · `eval/effector_drift.py` (the decay/revocation companion).

**Design:** dn-synchronic-diachronic-dreamer §2.1/§2.2/§2.7/§2.8 (ratified — extended, not
contradicted: the ledger grades what its dispatches emit and adds a non-input, touching no law) ·
dn-recursive-dreaming-bounded-by-grounding (rules 1–4; the axis-separation kinship §2.5) ·
dn-cross-strata-dreamer (the per-grant lane, §2.3's consumer) · dn-global-event-clock (cuts;
Law C4) · finding-0217 (Σ unrecoverable — this note's storage verdict) · finding-0126 (the
diachronic park's restated re-entry, honored) · finding-0141 + `docs/tracks/sync-diac-dreamers.md`
(the wire decision this note's usefulness gates on) · finding-0011 (effector tier NONE — why
entitlement output is evidence, not authorization) · oq-0049 (NN-7 wellbeing-scoped — the ruled
non-blocker) · `docs/brainstorms/process-weight.md` (NAME THE READER, applied §2.6).

**External claims:** none. (Brier scoring is used by name as the warrant already uses it; no
citation to external literature is made or needed here — the external-grounding gate binds any
future book chapter, not this note's use of a named scoring rule the warrant introduced.)
