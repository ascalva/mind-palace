---
type: design-note
id: dn-live-adoption-and-longitudinal-harness
status: draft
implementation: not-built   # corpus-audit 2026-07 verification
created: 2026-07-03
updated: 2026-07-04
links: []
supersedes: null
superseded_by: null
warrant: null
---

# Live adoption & the longitudinal harness (Track L)

**Status:** design note, forward-looking. Defines the path from "reasoning-complex core built (H1–H3,
2026-07-01)" to "the strong Dreamer running continuously on the live mirror, tuned against owner
verdicts, measured over time." Consumes: companions III/IV, `REASONING-COMPLEX-BUILD.md`, the F9
quality suite, the A1 drift gauge, the F4 longitudinal harness sketch, `alignment-subsystem.md`.
Builder prompts for H4–H7 and the Dreamer loop v2 already exist (companion-IV session) and are
**not** re-issued here; this note adds the **L-series** that follows them.

The claim this track exists to test is the one no green suite can prove: **that the structure the
Dreamer finds in the real corpus corresponds to what the owner would call insight.** Everything
below is machinery for making that claim falsifiable, repeatedly, over months.

---

## 0. Ordering (the whole track in one view)

```
prereqs (owner)      H4–H7 + loop v2        L1 shadow          L2 verdicts        L3 tuning        L4 metrics        L5 continuous
migration --apply →  interpreters land  →   run ledger,   →    review REPL,  →    manifest +  →    longitudinal →    digest, probes,
self-knowledge       (already prompted)     dual pipeline      ground truth       gated apply      curves, F4        earned interrupts
ingest                                      on live mirror     accrues            (owner-only)     Θ calibration     steady state
```

Hard dependencies: L1 needs the loop v2 (something worth shadowing). L2 needs L1 (claims to judge).
L3 needs L2 (verdicts are what tuning optimizes against — tuning before ground truth is tuning
against taste). L4 needs a few weeks of L2 data. L5 is mostly wiring and can interleave from L1 on.

**Owner prerequisites, before L1 (both already runbook'd, both blocking):**
1. `scripts/migrate_provenance_split.py --apply` — 918 legacy vector rows + 135 catalog rows are
   not mirror-readable until relabeled; the live mirror reads empty and every live run below is vacuous.
2. `scripts/ingest_self_knowledge.py` — so EXPLAIN and the digest can cite the real docs.

---

## 1. Finish the complex first (H4–H7 + loop v2) — and why nothing live precedes it

The temptation is to start live-running the H2 diffusion clusterer now. Resist it: the clusterer
alone emits *groupings*, not *claims*. Owner verdicts over raw clusters are low-signal ("is this a
good cluster?" is barely answerable). The interpreters (bridges via curvature, tensions via
frustration, holes via persistence, themes-with-confidence via SBM) are what turn structure into
**claims with citations**, and claims are the unit everything downstream — verdicts, novelty,
precision curves — is defined over. Ship H4–H7 and the loop v2 per the existing prompts, flag-OFF,
then start Track L. Estimated builder effort is small relative to what's already landed; the math
and module layout are fully specified.

One addition to the loop-v2 prompt scope (carry into the builder session, not a new prompt):

- **Claims are content-addressed.** `claim_id = sha256(kind ‖ canonical(support_set) ‖ polarity)` —
  *excluding* free-text surface wording and confidence. Two runs that find the same tension emit the
  same id. This is what makes novelty, duplication, and verdict-carryover well-defined across runs
  (family 2 discipline applied to the Dreamer's own output). A re-emitted claim inherits its prior
  verdict; only *new* ids reach the review queue.

---

## 2. L1 — Shadow mode + the run ledger (dual pipeline, one corpus)

**Principle (family 2).** The old single-linkage Dreamer and the new complex Dreamer are two derived
functors over the same raw. Because derivation is regenerable and inputs are content-addressed, the
comparison is exact: same corpus digest in, two claim sets out, diffable.

**Built:**
- `core/dreaming/shadow.py` — `ShadowRunner`: executes BOTH pipelines (live default = single-linkage,
  shadow = complex loop v2) against the same `MirrorView` snapshot in the same trough window. Shadow
  output is written to the run ledger only — never to the interpreted store, never surfaced except
  through review (L2). Live behavior unchanged; no flags flipped by building this.
- `core/stores/runledger.py` — append-only `dream_runs` + `dream_claims` tables (SQLite, WAL,
  scheduler's single-writer discipline):
  - `dream_runs(run_id, started_at, pipeline, config_fingerprint, corpus_digest, node_count,
    edge_count, duration_s, spectral_stats_json)` — `config_fingerprint` = sha256 of the resolved
    tuning manifest (L3); `corpus_digest` = Merkle root over the MirrorView's chunk digests. Every
    run is reproducible from (raw store, fingerprint) — the same guarantee the rest of the system has.
  - `dream_claims(claim_id, run_id, kind, confidence, support_json, surface_text, novel)` —
    `novel` = claim_id not seen in any prior run.
- Nightly trough schedule for the shadow run (existing cron/trough machinery; shadow is background
  priority, yields to everything).

**σ-tuning lives here.** The §2.2 note (real embedder cosine statistics may need a lower σ) is
resolved *inside* shadow mode: the ShadowRunner can carry a small σ-sweep on its first runs (3–5
values, one extra spectral solve each — cheap), recording per-σ cluster stats in the ledger. The
owner picks σ by inspecting L2 output quality, not by theory. The clusterer default-flip (the
deliberate adoption step H2 deferred) happens **after** shadow evidence, as a manifest change (L3),
not a code change.

**Done when:** two pipelines run nightly over the live mirror; ledger rows accumulate; claim ids
dedupe across runs; live surface provably unchanged (existing suite green, no interpreted-store
writes from shadow); firewall green (shadow reads only MirrorView).

---

## 3. L2 — The verdict store + the review interface (the owner in the loop)

This is the center of the track. Owner verdicts are the **ground truth the whole apparatus has been
missing** — the empirical closure of the "provable vs. insightful" gap, and the labeled data that
makes L3 tuning and L4 curves meaningful rather than aesthetic.

**Verdict taxonomy (proposed, owner to ratify — keep it ≤5 or review fatigue kills the loop):**

| verdict | meaning | feeds |
|---|---|---|
| `novel_useful` | true, and I didn't already know it | the number that matters |
| `true_known` | correct but already in my head | calibration (not failure) |
| `plausible` | can't verify yet; interesting | probe candidates (L5) |
| `wrong` | the claim is false | precision; if citations don't support it → also a grounding defect |
| `noise` | not even a claim worth judging | clusterer/threshold tuning signal |

**Built:**
- `core/stores/verdicts.py` — append-only `claim_verdicts(claim_id, verdict, note, verdicted_at,
  config_fingerprint_at_verdict)`. Verdicts are **operational ground truth, not mirror content**
  (family 1: they label interpreted-tier output; they do not enter `MIRROR_READABLE`). If the owner
  writes a substantive *note* during review and wants it kept, that specific text can be captured
  through the existing `DialogueCapture` path as `authored-dialogue` — a deliberate, per-note act,
  never automatic.

  > **Cross-ref (verdict authentication):** `design-notes/verdict-authority.md` extends this store
  > with owner-attributable authentication — an Ed25519 signature over a canonical verdict payload +
  > a monotonic sequence number (columns `signature`, `signer`, `seq`), so a compromised transport
  > can drop/reorder but never forge a verdict. The plain schema here is the base; signing is the
  > sacred-boundary upgrade. Built: `core/stores/verdicts.py` (store), `core/verdict/` (sign/apply).
- `scripts/review.py` — a deterministic review REPL (no model call needed to display): presents each
  unverdicted novel claim with its kind, confidence, surface text, and the **actual cited chunks**
  (resolved through MirrorView so the owner judges against the real support, not the paraphrase);
  single-keystroke verdicts; optional note; shows both pipelines' claims interleaved and *labeled*
  (single-linkage vs. complex) so every session doubles as an A/B. Sessions are resumable; queue
  ordered novel-first, confidence-descending.
- **Theory probes (owner-initiated).** `review.py probe "<hypothesis>"` — the owner states an
  expectation ("my notes on X and Y are connected", "there's a tension between A and B"). Stored as
  a `probe(probe_id, hypothesis, expectation_kind, target_hints)`. The next shadow run evaluates it
  against the complex (nearest structural claim, diffusion distance between hint-matched nodes,
  membership in a frustrated triangle, …) and the outcome lands in the review queue as a claim of
  kind `probe_result`. This is "proving out theories" as a first-class, ledgered act — and each
  resolved probe is a permanent regression test (a planted expectation on the *real* corpus, the
  live-data sibling of F9's synthetic plants).
- Ambassador: a `REVIEW` awareness only — STATUS narration gains "N claims awaiting your review;
  M probes resolved" (OpsView extension, read-only). The Ambassador does **not** collect verdicts
  conversationally in v1; free-text verdict parsing is a place to be wrong silently. The REPL is the
  verdict surface; the Voice tells you when to visit it.

**Done when:** the owner can run a 10-minute review session, verdicts persist and carry across runs
via claim ids, probes round-trip (posed → evaluated → verdicted), and per-pipeline verdict tallies
are queryable.

---

## 4. L3 — The tuning manifest + gated apply ("light tweaking," made safe and honest)

**Principle (families 3+4).** "Light tweaking" must be *structurally* light — a closed, declared set
of parameters with ranges, changed through a gate, attested, and evaluated by the next runs' curves.
Anything not in the manifest is a design change (a Claude-session + builder-prompt act), not a tweak.
This is the same shape as the self-mod gate but strictly weaker: parameters only, owner-initiated
only, no code motion — the safe-lever list from §14, formalized.

**Built:**
- `config/tuning.toml` + `core/complex/manifest.py` — the manifest: every tunable with type, range,
  default, and the subsystem it feeds. Initial set: `sigma` (diffusion), `eigengap_k_max`,
  `min_cluster_size`, `confidence_floor` (claim emission), `noise_ceiling` (F9's), `frustration_min_w`
  (triangle reporting floor), `resonance_threshold` (R5, dormant), `clusterer` (enum:
  `single_linkage | diffusion` — **the H2 default-flip is row one of this table**), and `g_scaling`
  (enum: `similarity_only | support_count` — the open adjudicator question becomes an A/B-able
  parameter instead of a debate; verdict data settles it).
- `scripts/tune.py` — `show | set <key> <value> | history`. `set` validates against the manifest
  range, writes the overlay (the existing `config/local.toml` mechanism), **attests** the change
  (action=`tune`, old→new, fingerprint before/after), and prints the new `config_fingerprint`.
  Refuses out-of-range and unknown keys. Owner-only by the same posture as `--bless`.
- Ledger linkage: because every run records its `config_fingerprint`, every tuning change creates a
  natural before/after boundary in the L4 curves — tuning efficacy is *measured*, not vibed. A
  `--revert` restores the prior fingerprint's values from attestation history.

**Explicitly out of scope for tweaking:** the Constitution, `MIRROR_READABLE`, any provenance rule,
gate predicates, the frozen golden set, drift tolerances/Θ (those change only via `--bless`).
The manifest cannot express them; the wrong tweak is unrepresentable.

**Done when:** a tune → nightly run → review → curve inspection loop closes end-to-end with every
step attested; an out-of-range set is refused with the range in the error.

---

## 5. L4 — Longitudinal metrics + F4 (the "damn good harness over a larger period")

**Principle.** One run tells you nothing; the harness's unit of evidence is a **curve**. Three
confounds must be separable or the curves lie: corpus growth (mirror changes), config change
(tuning), and pipeline change (adoption). The ledger already keys every run by `corpus_digest` ×
`config_fingerprint` × `pipeline` — the curves are just group-bys over that, plus one control.

**Built:**
- `eval/longitudinal.py` — computes, per (pipeline, fingerprint) segment over time:
  - **precision@review** = novel_useful / (novel_useful + wrong + noise) — the headline;
  - **novelty rate** (new claim_ids / run) and **duplication rate** (re-emissions / run) —
    a healthy Dreamer's novelty decays toward a floor on a static corpus and jumps on ingest;
  - **grounding-defect rate** (wrong-with-unsupportive-citations) — must stay ~0 independently of
    everything else; this is a selfcheck failure, not a taste failure;
  - **probe resolution rate** and probe precision (owner-posed expectations confirmed);
  - **confidence calibration** — mean confidence of `wrong/noise` vs. `novel_useful/true_known`
    claims (the Dreamer should be *less* sure of its failures; if not, confidence is decoration);
  - **drift trajectory** — the A1 gauge sampled per run, now over axes that include the verdict
    rates (extends μ exactly as A2 anticipated: capability rates ⊕ conformance, where capability is
    finally *measured usefulness*).
- **The frozen control.** The literary-probe corpus (already designed) runs through the same shadow
  pipeline weekly in its **own graph** (`CURATED`, never the mirror — the dreaming-on-curated-graphs
  note, R5's infrastructure without R5's resonance step). Same config, frozen corpus ⇒ any movement
  on the control curve is *pipeline/config* effect isolated from corpus growth. This is what lets
  F4 assert "the tune helped" rather than "the corpus grew."

  > **Cross-ref:** `design-notes/founding-corpus.md` §2.3 records why the founding corpus
  > (deliberately coherent) can never double as this control, and why the two acts stay mechanically
  > distinct. And `dialogue-ingest-and-recursion.md` §5–§6 is the closed-loop form of this study —
  > the graph's trajectory under alternating ingest-events and sleep-events (derived reasoning
  > re-entering), which the verdict store (L2) is the precondition for labeling.
- **F4 lands here:** drift-trajectory asserts over ledger segments (deterioration one-sided, hard
  Constitution trip, tolerance-band regression between blessed checkpoints), plus F9's two
  drift-deferred tests moved to `longitudinal/` as planned. **Θ calibration** = after ~4 weeks of
  curves, propose Θ from observed variance (e.g. p99 of healthy inter-run drift); owner re-blesses
  in `baseline.json`. Until then Θ stays advisory — the harness reports, doesn't trip.
- `scripts/curves.py` — renders the curves as terminal sparklines + a static HTML report into
  `data/reports/` (local file, no serving, no egress; the roadmap's dashboard item in its smallest
  honest form).

**Adoption criterion (the H2 flip, made explicit and falsifiable):** flip `clusterer=diffusion` when,
over ≥3 weeks of interleaved review, the complex pipeline shows (a) precision@review ≥ single-linkage,
(b) grounding-defect rate ≤ single-linkage, (c) strictly higher novelty rate, and (d) a flat control
curve. Retire the single-linkage shadow only after 2 further clean weeks — then it becomes the
fallback path, not a nightly cost.

**Done when:** curves render over real ledger data; the control corpus runs; F4 asserts pass; the
adoption criterion is computable as one function over the ledger.

---

## 6. L5 — Continuous operation (the steady state)

- **Cadence:** nightly shadow dream (trough, background); weekly control-corpus run; weekly digest.
- **The digest, through the Voice:** the Ambassador gains a `DIGEST` path (OpsView + run-ledger reads,
  plain-language register, no internal nouns): "This week I found 3 new tensions and 2 bridges; 1
  probe resolved in favor of your hypothesis; 4 claims await review; precision is trending up since
  the last tune." Expected update — delivered on ask or on schedule, never as interruption.
- **Earned interruptions (existing policy, one new earner):** a claim may interrupt only if
  `novel ∧ confidence ≥ interrupt_floor ∧ kind ∈ {tension, probe_result}` — tensions and answered
  hypotheses are the two kinds worth the owner's attention unprompted; bridges and themes wait for
  the digest. `interrupt_floor` is a manifest parameter (default high; the owner tunes toward
  chattiness only if earned).
- **Verdict-hygiene guard:** if unreviewed novel claims exceed a ceiling (manifest), the digest says
  so and the harness marks subsequent precision points as low-confidence (sparse labels) rather than
  silently thinning the curve. The loop degrades honestly when the owner is busy.
- **Quarterly:** re-bless checkpoints (baseline drift section, Θ, control-corpus expectations),
  archive the ledger segment, and revisit the manifest's ranges against what tuning actually explored.

---

## 7. What this track does *not* do

- No live tweaking of prompts/interpretation *text* by the system itself — "light tweaking" is the
  owner moving manifest parameters, full stop. Self-directed modification remains Phase-10/self-mod
  territory behind its own gate; this track feeds it evidence (the verdict-extended μ) but grants it
  nothing.
- No verdict-driven automatic retuning. The loop is owner-closed by design; an auto-optimizer over
  verdicts is a future proposal that would itself need the self-mod gate.
- No effector work. Track G still waits on this track's headline number — "the Dreamer is measurably
  useful" is the precondition we set for opening the right boundary, and precision@review is now the
  measurement.

---

## Builder prompts (L-series)

### Prompt L1 — Shadow runner + run ledger

> **Context.** H4–H7 + loop v2 are in (flag-OFF). Build the dual-pipeline shadow layer and the
> append-only run ledger so the complex Dreamer runs nightly against the live mirror with zero live
> surface change. Read: this note §2; `REASONING-COMPLEX-BUILD.md` §3 (loop v2); scheduler queue
> conventions (WAL single-writer).
> **Task.** `core/stores/runledger.py` (`dream_runs`, `dream_claims`, content-addressed `claim_id`
> with `novel` computed on insert); `core/dreaming/shadow.py` `ShadowRunner` (both pipelines, one
> MirrorView snapshot, one corpus digest; optional σ-sweep mode recording per-σ stats); nightly
> trough job wiring at background priority. Claims of the shadow pipeline write ONLY to the ledger.
> **Constraints.** Zone A, no network (firewall green). Shadow never writes the interpreted store.
> No flags flipped; live cron dreamer unchanged. Deterministic given (corpus digest, fingerprint).
> **Done when.** Two nightly ledger rows per night (one per pipeline) over the real mirror; claim
> dedup across runs proven in tests; existing suite green; an integrity test proves shadow cannot
> reach the interpreted store.

### Prompt L2 — Verdict store + review REPL + theory probes

> **Context.** Ground truth. Read: this note §3; `DialogueCapture`; MirrorView resolution of chunk ids.
> **Task.** `core/stores/verdicts.py` (append-only, 5-verdict enum — a closed StrEnum, illegal
> verdicts unrepresentable); `scripts/review.py` (REPL: unverdicted-novel queue, cited chunks
> resolved and displayed, keystroke verdicts, notes, resumable, pipeline-labeled interleave; `probe`
> subcommand storing hypotheses); shadow-run probe evaluation emitting `probe_result` claims; OpsView
> + STATUS narration gain pending-review counts.
> **Constraints.** Verdicts ∉ MIRROR_READABLE (integrity test). Review display path is model-free.
> Note-capture to authored-dialogue is per-note explicit, never bulk.
> **Done when.** Pose→evaluate→verdict round-trips live; verdicts survive claim re-emission; tallies
> per pipeline queryable; integrity gate green.

### Prompt L3 — Tuning manifest + gated apply

> **Context.** The safe-lever list as a type. Read: this note §4; `config/local.toml` overlay
> mechanism; attestation emit conventions; self-mod gate (for the *shape*, not the machinery).
> **Task.** `config/tuning.toml` + `core/complex/manifest.py` (typed, ranged; includes `clusterer`
> and `g_scaling` enums); `scripts/tune.py` (`show/set/history/--revert`, range-validated, attested
> old→new, prints new fingerprint); ShadowRunner + Dreamer read all listed parameters through the
> manifest.
> **Constraints.** Unknown/out-of-range keys refused with the range in the error. Constitution,
> provenance, gates, golden set, Θ inexpressible in the manifest. Every change attested.
> **Done when.** tune→run→ledger-fingerprint-boundary closes in an integration test; revert restores
> a prior fingerprint exactly; property test: no manifest value outside its declared range can reach
> the Dreamer.

### Prompt L4 — Longitudinal curves + control corpus + F4

> **Context.** The evidence layer. Read: this note §5; `eval/drift.py` (A1); F4/F9 notes; the
> literary-probe corpus design; dreaming-on-curated-graphs (own-graph discipline).
> **Task.** `eval/longitudinal.py` (precision@review, novelty/duplication, grounding-defect rate,
> probe rates, confidence calibration, drift trajectory per (pipeline, fingerprint) segment); weekly
> control-corpus shadow run in its own CURATED graph; F4 asserts + move F9's two drift-deferred
> tests to `longitudinal/`; `scripts/curves.py` (sparklines + static local HTML into `data/reports/`);
> the adoption criterion as one pure function over the ledger.
> **Constraints.** Control corpus ∉ mirror (integrity test). Curves computable offline from the
> ledger alone. Θ remains advisory until owner re-bless; the harness reports, never auto-trips.
> **Done when.** Curves render from real + synthetic ledger fixtures; control isolation proven;
> F4 green; `adoption_ready(ledger) -> bool` exists and is tested against constructed histories.

### Prompt L5 — Digest, earned interruptions, steady state

> **Context.** Close the loop through the Voice. Read: this note §6; Ambassador policy.py (earned
> interruptions); OpsView; run ledger.
> **Task.** Ambassador `DIGEST` path (ledger+OpsView reads, plain register); interruption earner for
> `novel ∧ conf ≥ interrupt_floor ∧ kind ∈ {tension, probe_result}` with `interrupt_floor` from the
> manifest; verdict-hygiene ceiling + low-confidence curve marking; runbook section "Living with the
> Dreamer" (cadence, review habit, quarterly re-bless).
> **Constraints.** Digest is expected-update class, never unprompted. No internal nouns in narration.
> No new write scopes for the Ambassador.
> **Done when.** A scripted week of ledger fixtures produces a correct digest; interruption fires on
> a planted qualifying claim and not on a non-qualifying one; hygiene degradation marks curves.

---

## Open decisions for the owner

1. **Verdict taxonomy** — ratify or trim the 5 verdicts (§3). Fewer is better than finer.
2. **σ selection** — sweep-in-shadow as proposed, or fix from theory first? (Proposed: sweep.)
3. **`g_scaling`** — accept demoting the open adjudicator question to a manifest A/B settled by
   verdict data (§4), or keep it a design decision?
4. **Interrupt floor default** — start silent-except-digest (floor=1.01, i.e. off) or permissive?
   (Proposed: off for the first month; earn the interruptions with precision first.)
5. **Review cadence you'll actually keep** — the harness is honest about sparse labels, but the
   curves are only as good as the verdict rate. Ten minutes, twice a week, is the design target.
