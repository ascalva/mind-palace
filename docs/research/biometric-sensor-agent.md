---
type: research
id: biometric-sensor-agent
status: draft
family: [sensor-ingestion, authorship-distance, track-l, security-planes]
links:
  - docs/design-notes/authorship-distance-axis.md   # §3.7 projection map φ_s; a₂ author-sensed
  - docs/research/security-planes.md                 # three-plane composition; write-channel doctrine
  - docs/design-notes/capability-evaluation-harness.md  # masked replay; ablation ladder
  - docs/design-notes/recursive-strata.md            # derived-stratum promotion invariants
  - docs/PROGRESS.md
supersedes: []
---

# The Biometric Sensor-Domain Agent — A Research Note

> **Framing.** This is a thought experiment, deliberately scoped. It asks whether a
> single-subject physiological-monitoring instrument can be built *inside* the Mind
> Palace's existing doctrine — provenance-strict, sealed, warning-only — without
> importing any of the failure modes the doctrine was written to exclude. It is **not**
> a clinical tool, **not** a diagnostic system, and **not** medical advice. The
> instrument's ceiling of authority is: *"a deviation from your own established baseline
> occurred; here is retrievable literature about what patterns like it can mean; a human
> should decide what, if anything, to do."* Everything below is written to keep it at
> that ceiling.

---

## 0. Non-goals (stated first, because they bound everything else)

- **NG-1.** Not a diagnostician. It never emits a diagnosis, a probability of a named
  disease, or a treatment. It emits *baseline-deviation events* and *grounded
  interpretive context*.
- **NG-2.** Not an actuator. It has no path to the Hands (Track G). Its only output is a
  recommendation written to the adjudicator inbox. Owner-only promotion. No effect is
  minted from a physiological signal, ever.
- **NG-3.** Not a population model applied to you. The instrument's statistical unit is
  *N = 1 (you)*. It does not import a cohort prior as ground truth about your body.
- **NG-4.** Not a care-seeking suppressor. It can raise the salience of a concern; it can
  never lower it, never tell you a symptom is "probably fine," never stand between you
  and a clinician.

---

## 1. The claim under test

Reframed to the narrowest defensible form:

> Continuous physiological self-data, reduced to a small set of interpretable channels
> and compared against **your own** longitudinal baseline, can surface early, low-authority
> warnings of physiological change — and an ingested best-practice corpus can supply the
> *interpretation* of those warnings — provided (a) the detector is deterministic and
> personal, (b) the interpreter is grounded in retrievable text rather than latent weights,
> and (c) both are held below diagnostic authority by construction.

This is a testable claim with a real literature behind each clause. Sections 2–3 audit
that literature honestly, including where it fails to support the claim.

---

## 2. What the current literature *does* support

### 2.1 Personal-baseline anomaly detection is real and pre-symptomatic

The strongest evidence is the Stanford/Snyder wearable-alerting line of work. In a
prospective cohort of 3,318 participants (84 SARS-CoV-2 infections), a real-time
smartwatch alerting system flagged pre-symptomatic or asymptomatic infection in 67 of 84
infected individuals (~80%), with pre-symptomatic signals appearing a median of ~3 days
before symptom onset. The detectors were two anomaly algorithms over resting heart rate —
an online residual-heart-rate detector (RHRAD) and a CUSUM changepoint detector — both
operating on *deviation from a personal baseline*, not population thresholds.
[Alavi et al., Nat Med 2022; Mishra et al., Nat Biomed Eng 2020]

This is the load-bearing result for our design: it is exactly a *reactive-tier,
deterministic, personal-baseline* detector — the same shape the Mind Palace already
specifies for the reactive tier (EWMA / z-score / changepoint, escalate on threshold
crossing). The literature independently converged on the architecture the system already
mandates.

### 2.2 The N-of-1 premise is the point, not a limitation

Snyder's deep-phenotyping program (personal-omics profiling, N-of-1 trials, longitudinal
multi-omic baselines) produced a finding that maps almost exactly onto the
authorship-distance doctrine: **an individual's health profile, when they are ill,
resembles their *own* healthy profile more than it resembles another healthy person's
profile.** Inter-individual variation exceeds within-individual perturbation. The
personal baseline is therefore the correct — and in many cases the *only* — valid
comparator. [Snyder lab; Chen et al., Cell 2012; Schüssler-Fiorenza Rose et al.]

This is the empirical vindication of treating biometric data as **self-data at
authorship-distance a₂ (author-sensed)**: the subject is one person (you), the signal is
mediated by an instrument (the sensor), and the meaningful reference frame is internal,
not cohort-derived.

### 2.3 Open-weight medical models are locally runnable and non-trivially capable

The interpreter layer has viable open-weight options that run on an M2 Max:

| Model | Size | MedQA | Notes |
|---|---|---|---|
| MedGemma 4B (multimodal) | 4B | 64.4% | Among best <8B open models; runs comfortably local |
| MedGemma 27B (text) | 27B | 87.7% | Within ~3 pts of DeepSeek-R1 at ~1/10 inference cost |
| MedGemma 1.5 4B | 4B | — | Adds anatomical localization, multi-timepoint, EHR/lab parsing (Apr 2026 report) |
| Meditron | 7B / 70B | — | Llama-2 base; EPFL/Yale/ICRC; trained on PubMed + guidelines |
| BioMistral / Me-LLaMA / OpenBioLLM | 7–70B | — | Open-source research tier |
| gpt-oss-20b | 20B | — | General open-weight reasoner; viable local fallback |

[Sellergren et al., MedGemma Technical Report 2026; Google Research; AI Multiple 2026]

Crucially, MedGemma is *open weights* — checkpoints, tokenizer, and training citations are
inspectable, which matters for a sealed, auditable system in a way a closed API never can.
Note also that Google frames MedGemma explicitly as a **developer foundation for building
clinician-facing tools, not a direct-to-consumer diagnostic** — the same ceiling this note
imposes.

---

## 3. What the literature *does not* support — limitations and warnings

This section is the point of the exercise. Each item is a reason the instrument must stay
low-authority.

### 3.1 The sensor layer is noisy, and error propagates

- **PPG heart-rate error.** Consumer wrist PPG is reasonable at rest (reported MAE
  ~2–4 bpm in a controlled Fitzpatrick III–V cohort; ~7 bpm in an earlier mixed study)
  but degrades markedly under motion — absolute error rises ~30% during activity, and
  algorithms appear to overfit predictable, repetitive movement.
  [Bent et al., npj Digit Med 2020; Sensors 2026]
- **HRV from PPG ≠ HRV from ECG.** PPG-derived HRV, especially high-frequency components,
  is less accurate than ECG-derived HRV. HRV is one of the most physiologically
  informative channels *and* one of the least reliably measured on the wrist.
- **Sleep staging is weak.** Accelerometry+HR sleep staging achieves only ~60–70%
  agreement with polysomnography, systematically underestimating REM and overestimating
  deep sleep. [Depner et al. 2020, via Project Hermes]
- **Skin-tone bias is contested, not settled.** Some large analyses found *no*
  statistically significant HR-accuracy difference across skin tones; a Duke analysis
  found activity — not skin tone — to be the significant driver; but a 2026 Hispanic
  Fitzpatrick III–V cohort found greater error dispersion at the darkest tones combined
  with high BMI. The honest position is: **phenotype-linked agreement drift is plausible
  and under-studied, and must be treated as an open confound rather than dismissed.**
  [npj Digit Med 2020; MobiHealthNews/Duke; Sensors 2026]

**Design consequence:** upstream sensor error cannot be recovered downstream. A validation
layer can *suppress* an artifactual alarm (e.g. HRV drop from the device shifting during
sleep) but cannot *reconstruct* a signal lost to sensor failure. The instrument must carry
sensor-quality metadata into the provenance record and let the confidence envelope reflect
it.

### 3.2 The benchmark-to-bedside gap is large

MedQA/USMLE accuracy is exam performance on multiple-choice clinical vignettes. It is
**not** evidence of competence on longitudinal personal vitals streams — a modality that
appears in essentially none of these models' training data. A 2026 real-world dermatology
evaluation (5,811 cases, 46,405 images) found that benchmark performance did **not**
cleanly translate to real consultation workflows for open-weight multimodal models
including MedGemma-4B. [arXiv 2605.04098]

**Design consequence:** the medical model is an *interpreter of retrieved text*, never a
detector and never an authority. It reasons over (a) a flagged deviation and (b) retrieved
guideline passages. It is not asked to "read the vitals and tell me what's wrong."

### 3.3 The false-positive base rate is the primary failure mode

The same Stanford alerting work is candid: stress, alcohol, travel, intense exercise, and
poor sleep all trigger baseline deviations that *look like* early infection. Non-illness
events triggered alerts at a lower but non-trivial rate (~1.15 alert-days/person vs
~3.42 for COVID cases). A monitor that cries wolf becomes a monitor you mute.

**Design consequence:** this is the *exact* structural analogue of Track L review fatigue.
Alarm fatigue is to this instrument what verdict fatigue is to the verdict store. The
mitigation is the same: a stability filter, an adjudicator inbox rather than an interrupt,
and confidence gating tuned to protect attention, not to maximize recall.

### 3.4 The single-subject statistical problem

N-of-1 is the correct frame (§2.2) but it has a hard cost: **no control, no ground-truth
labels, no cohort to bound your false-discovery rate.** You cannot compute a classical
specificity for a cohort of one. Correlation-vs-causation is unresolvable from the signal
alone (did HRV drop because you're getting sick, or because you drank last night?). The
instrument can *observe co-occurrence*; it cannot *establish cause*, and must never phrase
a warning as if it had.

---

## 4. Architectural integration

Here is how the instrument fits the existing system without special-casing.

### 4.1 Placement on the authorship-distance axis

Biometric data enters at **a₂ (author-sensed)**: self-data about one subject, mediated by
an instrument. It is *not* a₀/a₁ (you did not author or initiate the measurement act
per-sample) and *not* a₃ (it is not curated external corpus). This placement is not
cosmetic — it sets what the data is permitted to affect and how much it is trusted
relative to the core.

### 4.2 The projection map φ_s and the "raw exhaust never enters" rule

Per §3.7 of the authorship-distance note, each sensor-domain agent is a specialist
interpreter executing a projection map φ_s from raw measurement space into the shared
representation. For biometrics:

```
φ_s :  {raw PPG waveform, accelerometer, temp, ...}
        ↓  (specialist reduction, stays outside the core)
       {RHR, HRV(RMSSD/SDNN), resp-rate, skin-temp Δ, sleep-summary,
        + per-channel quality/confidence + baseline-residual}
```

The raw waveform is **exhaust**; it never crosses into the core. What crosses is the
reduced, quality-tagged channel set plus the baseline residual. This is not a preference —
it is the security rule fixing the fusion stage: because raw streams cannot enter, fusion
is **late-fusion by doctrine**, which is *also* the property that prevents the store from
becoming a re-identifiable surveillance dossier of raw physiological telemetry.

### 4.3 Two-tier decomposition (this is the whole design in one move)

| Tier | Component | Nature | Runs |
|---|---|---|---|
| Reactive | **Detector** | Deterministic: EWMA / z-score / CUSUM / changepoint over *personal* baseline | Continuously, cheap |
| Cognitive | **Interpreter** | Open-weight medical model, RAG over guideline corpus | *Only on flag* |

The detector is the RHRAD/CUSUM shape the literature validated (§2.1). It is exact,
provable, and free of model risk. The interpreter earns the big model only when the
detector crosses a threshold — matching the existing reactive/cognitive tier split and
keeping the single inference slot free. **The detector decides *whether*; the interpreter
supplies *context*. Neither decides *what to do*.**

### 4.4 Provenance: the un-provenanced-weight problem and its fix

A warning whose warrant is "latent knowledge in the model's weights" has **no citation** —
it is un-provenanced in precisely the way the system forbids. The fix is structural:

- The interpreter runs **RAG over an ingested best-practice corpus** (clinical guidelines,
  reference ranges, patient-education material) at **a₃ (author-curated)**.
- Every interpretive statement grounds in a retrievable passage. Grounding edges run
  derived → guideline-corpus.
- The warning enters as a **derived stratum relative to world** (not relative to core),
  carrying a **confidence envelope with graded grounding**: sensor-quality × baseline-
  residual-strength × retrieval-grounding-strength.
- A warning that cannot ground in retrieved text is *not promoted* — it is recorded as
  "deviation observed, no grounded interpretation" and parked. This is the graded-grounding
  conservative extension already specified for the confidence envelope.

### 4.5 Write-channel discipline

Two of the three sacred write-channels are touched, and both stay clean:

- **Ingestion inbound (sensor):** attributable (which device, which φ_s version,
  which quality flags), append-only (the event log of measurements; the derived index is a
  versioned supersession per the append-only-belongs-to-the-log invariant), typed and
  promotion-gated (a₂ derived stratum, owner-promoted). *Un-purchasable by expected value*
  applies: no volume of "this deviation is probably important" buys promotion past the
  owner gate.
- **Effects outbound:** **untouched.** There is no effector path from a physiological
  signal. This is the removes-the-dangerous-capability principle in its cleanest form —
  the instrument does not act under controls; it is *built with no ability to act.* The
  output is a recommendation to the adjudicator inbox, consumed under owner-only promotion,
  behind the stability filter that already exists to cut review fatigue.

### 4.6 Security posture

- **Sealed / offline.** The medical model runs locally on the M2 Max. Biometric data never
  egresses. This is the decisive advantage of open weights over any medical API: on-prem
  privacy is *possible*, and peer review of the model is *possible*.
- **Store encryption.** AEAD-for-integrity and key-as-capability apply to biometric
  time-series as to everything else; the **index-leakage caveat** matters more here —
  access patterns over a physiological index can themselves be sensitive, and this is a
  recorded limitation, not a solved problem.
- **Model swappability.** Per prior doctrine, model choice is a *parked decision* with a
  recorded default. The guideline corpus and the detector-baseline schema are the parts
  that constrain the design; the interpreter is swappable by construction (MedGemma 27B
  text default; MedGemma 4B / gpt-oss-20b fallbacks).

---

## 5. Track L integration — how we know it earns its place

The instrument is subject to the same experimental arbiter as everything else.

- **Eval primitive.** Masked replay (per the capability-evaluation harness): hold out a
  window of historical biometric data around a *known* self-annotated event ("I had a
  cold starting the 12th"), and ask whether the detector flags the deviation ahead of the
  annotation, and whether the interpreter's grounded context is relevant.
- **Ablation ladder.** Random-baseline → threshold-on-raw-channel → personal-baseline
  residual → residual + interpreter. Each rung must beat the one below on the replay
  battery or it does not ship.
- **Primary metric is not recall.** It is **attention-adjusted precision** — warnings that
  a reasonable owner, in hindsight, judged worth surfacing — because alarm fatigue (§3.3)
  is the failure mode that kills the instrument.
- **Null-result handling.** If there is no signal at current personal-data scale, that is
  recorded as *"no signal at this scale"* and parked with a re-entry condition (more
  longitudinal baseline accumulated), **not** treated as terminal. Ablation greed is a
  real risk; the detector and interpreter remain modular and cheap to reactivate.

---

## 6. Bright lines (hard constraints, not weighted terms)

1. **No diagnosis.** The instrument never names a disease as a conclusion. Named
   conditions may appear only as *quoted content of a retrieved guideline passage*,
   attributed to that source, never as the system's assertion.
2. **No care-suppression.** No output ever says a symptom is safe to ignore. The
   instrument's monotonic direction of influence is *raise salience only.*
3. **No effector path.** Enforced structurally (§4.5), not by policy.
4. **Emergency carve-out is human, not machine.** If you feel acutely unwell, the correct
   action is to contact a clinician or emergency services — not to consult this instrument.
   The instrument is a slow, low-authority background mirror; it is not a triage line and
   must say so wherever it surfaces.

These are constraints bounding the feasible set, not terms in an objective — because
expected-value reasoning ("this warning is probably important enough to phrase more
strongly") is exactly the mechanism that erodes bright lines.

---

## 7. A note on the regulatory frame (research context, not compliance advice)

For a personal, single-subject, non-commercial thought experiment this is informational
only — but the regulatory line is *architecturally instructive*. Under the 21st Century
Cures Act (§3060) and FDA's January 2026 General Wellness and Clinical Decision Support
guidance, software "for maintaining or encouraging a healthy lifestyle" and unrelated to
diagnosing/curing/treating disease is *not* a medical device; and CDS software stays a
non-device largely when a human can **independently review the basis** of its
recommendation — the more the software is a "black box," the more likely FDA treats it as a
device. [Faegre Drinker 2026; Arnold & Porter 2026; FDA 2026 guidance]

The instructive part: the regulatory non-device posture (**transparent basis, reviewable
grounding, no autonomous clinical decision**) is *the same posture the provenance doctrine
already enforces.* Building it provenance-strict is not extra work for a hypothetical
compliance goal — it is the same discipline that keeps the instrument honest. This is a
convergence worth recording, not a claim about legal status.

---

## 8. Open questions

- **OQ-1.** What is the minimum viable channel set? RHR + HRV + resp-rate + skin-temp Δ +
  sleep-summary is the literature's high-value subset; is skin-temp reliable enough on the
  target device to include, given §3.1?
- **OQ-2.** Baseline establishment window. Snyder-style work implies weeks-to-months of
  healthy baseline before residuals are meaningful. What is the cold-start policy, and does
  the instrument stay silent until baseline confidence crosses a floor?
- **OQ-3.** Confounder annotation. The false-positive base rate (§3.3) drops sharply if the
  owner can cheaply annotate "drank / traveled / hard workout / stressed." Is that a
  lightweight a₁ (author-initiated) side-channel feeding the detector's suppression logic?
- **OQ-4.** Guideline-corpus curation. Which sources, at what recency, and how is
  supersession handled when a guideline is revised? (This is a corpus-curation problem
  identical to the founding-corpus one.)
- **OQ-5.** Does the interpreter output re-enter the complex as a derived stratum
  (recursive-strata invariants apply), or is it ephemeral per-warning? Echo-chamber threat
  model if the former.

---

## 9. Verification items (route to builder/orchestrator as grep-and-cite)

- **V-1.** Confirm the reactive-tier detector spec in the repo can express CUSUM /
  changepoint over a personal-baseline residual, or whether it is currently EWMA/z-score
  only. Path-and-line evidence.
- **V-2.** Confirm the sensor-domain agent contract in `authorship-distance-axis.md` §3.7
  already carries a per-channel quality/confidence field, or whether B-series work is
  needed to add one.
- **V-3.** Confirm the confidence-envelope implementation supports a three-factor product
  (sensor-quality × residual-strength × grounding-strength) or only the current form.
- **V-4.** Confirm the adjudicator inbox schema can accept a warning-class recommendation
  distinct from a promotion recommendation.

## 10. Builder items

- **B-1.** Draft the φ_s reduction schema for the target wearable's export format (raw →
  reduced channel set + quality tags), with raw exhaust explicitly excluded at the boundary.
- **B-2.** Prototype the personal-baseline residual detector on a held-out slice of your own
  historical data (masked-replay harness) before any interpreter is wired in — the detector
  must earn its rung on the ablation ladder first.

## 11. Parked decisions

| id | decision | default recorded | re-entry condition |
|---|---|---|---|
| PD-B1 | Interpreter model choice | MedGemma 27B text (4B / gpt-oss-20b fallback) | Detector proven useful via masked replay; local inference budget confirmed |
| PD-B2 | Recursive re-entry of interpreter output (OQ-5) | Ephemeral per-warning | Track L shows interpreter context is reused, not one-shot |
| PD-B3 | Skin-temp channel inclusion (OQ-1) | Excluded pending reliability check | Device-specific validation of skin-temp stability |

---

## References

- Alavi A, Snyder M, et al. *Real-time alerting system for COVID-19 and other stress events
  using wearable data.* Nature Medicine, 2022. PMC8799466.
- Mishra T, Snyder M, et al. *Pre-symptomatic detection of COVID-19 from smartwatch data.*
  Nature Biomedical Engineering, 2020.
- Chen R, Snyder M, et al. *Personal Omics Profiling Reveals Dynamic Molecular and Medical
  Phenotypes.* Cell, 2012. (N-of-1 personal-omics program.)
- Snyder Lab, Stanford Medicine — longitudinal multi-omic baseline profiling; personal
  baseline necessity. med.stanford.edu/snyderlab.
- Sellergren A, et al. *MedGemma Technical Report.* arXiv:2507.05201, 2026; *MedGemma 1.5
  Technical Report*, arXiv:2604.05081, 2026. Google Research MedGemma release notes.
- *Are Multimodal LLMs Ready for Clinical Dermatology? A Real-World Evaluation.*
  arXiv:2605.04098, 2026. (Benchmark-to-bedside gap, incl. MedGemma-4B.)
- Bent B, Dunn J, et al. *Investigating sources of inaccuracy in wearable optical heart
  rate sensors.* npj Digital Medicine, 2020.
- *PPG-Based Heart Rate Accuracy in Hispanic Adults with Fitzpatrick III–V Skin Tones.*
  Sensors, 2026. doi:10.3390/s26102922.
- Duke/MobiHealthNews — activity vs skin-tone effects on PPG HR accuracy.
- *Project Hermes: A Model-Agnostic Validation Layer for Wearable Health Prediction
  Systems.* arXiv:2602.18643. (Sensor-limitation survey; sleep-staging agreement.)
- Faegre Drinker; Arnold & Porter; Akin — analyses of FDA January 2026 General Wellness and
  CDS guidance updates and 21st Century Cures Act §3060.

---

> **Standing medical disclaimer.** This document describes an experimental,
> single-subject, research thought experiment. It is not medical advice and describes no
> validated clinical tool. No instrument built from it should be relied on for any health
> decision. For any health concern, consult a qualified clinician; for anything acute, seek
> emergency care. The instrument's designed authority is, and must remain, that of a
> low-confidence mirror — never an oracle.
