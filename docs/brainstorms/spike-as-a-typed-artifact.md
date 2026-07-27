# spike-as-a-typed-artifact

## 2026-07-26T00:00:00Z

```capsule
topic: spike-as-a-typed-artifact
date: 2026-07-26

seed: |
  Owner, verbatim: "sometimes I should admit I don't have a good answer, which is a state I can
  invoke a research probe, a spike, investigate and recommend with proper tradeoffs, cost
  prediction, metrics, track candidates, a report I read to help me make a decision, that can be
  referred to by load-bearing questions with load-bearing answers."

⚑ it half-exists, and has since bp-005: |
  `docs/research/` holds FOUR notes (biometric-sensor-agent · planar_graphs · security-planes ·
  un-represent-ability) and `docs/experiments/` holds `sigma-sweep-run-1.md`. But **oq-0010 —
  "ratify the provisional research-note front-matter convention (template + spec line)" — is still
  OPEN**, so `docs/templates/research-note.md` was never written and no command invokes the type.
  This is the "wiring is part of finishing" pattern applied to an ARTIFACT rather than to code: the
  instances exist, the convention was drafted, ratification stalled, and the type never became
  reachable. Reviving it is cheaper than minting something new, and it closes oq-0010 as a
  side-effect.

⚑⚑ THE INSIGHT: owner-questions.md conflates TWO KINDS OF QUESTION: |
  - **CONSTITUTIVE / taste** — "does the mirror get to act?" (oq-0051), "is impersonation a bright
    line?" (oq-0052). Only the owner can answer. No evidence would settle it; his judgement IS the
    fact. A spike is irrelevant here and would be a category error.
  - **EMPIRICAL** — "what σ?" (oq-0024), "does `aws_signing_helper` talk to the Secure Enclave?",
    "what do bp-113/114 actually cost?" (finding-0227). There is a FACT OF THE MATTER, and the
    owner's judgement is a POOR SUBSTITUTE FOR MEASUREMENT.

  Both currently live in the same file with the same shape and the same `default_if_unanswered`.
  ⚑ Routing an empirical question to him as a "ruling" quietly asks him to GUESS at something
  measurable — and he will answer, because the form invites an answer.

  **oq-0024 is the proof.** It asked him to rule on a dreaming threshold; he gave an interim
  σ = 0.58 "owner-authorized" and the sweep/benchmark axis stayed OPEN. A measurable question
  wearing a ruling's clothes — and `docs/experiments/sigma-sweep-run-1.md` shows the measurement was
  even started. The artifact to answer it exists; the ROUTE to it does not.

live instances that need this right now (evidence, not speculation):
  - oq-0024 — the σ sweep/benchmark axis, still open behind an interim hand-set value
  - The Secure-Enclave ↔ `aws_signing_helper` integration (oq-0057's open sub-decision) — flagged
    by the orchestrator the same day as "needs a spike, not an assertion"
  - finding-0227 — bp-113/bp-114 are under-priced; pricing them IS a spike
  - oq-0042 — chase a fable-capable headless credential, or record the plane dormant
  - oq-0053 — cannot be answered until a belief ledger exists to make confidence earned

⚑ what a spike must be allowed to do that a build plan structurally cannot: |
  **Conclude "we still do not know."** A build plan has acceptance criteria and falsifiers; its
  honest failure mode is a §10 STOP. A spike's honest outcome includes an inconclusive one, and if
  the artifact cannot express that, it will manufacture confidence to look finished.

open_questions:
  - ⚑ SPIKE CODE MUST BE DISPOSABLE BY CONSTRUCTION. The classic failure is spike code shipping
    because "it works". Write-scope should be a scratch area; the DELIVERABLE is the report. A spike
    that lands production code is a build plan wearing a disguise, and it skips the plan's gates.
  - ⚑ COST PREDICTION DRAWS ON A KNOWN-BROKEN LEDGER. The owner asked for cost prediction in the
    report, but oq-0048 records that the per-plan cost ledger has holes, and session-54 sealed SIX
    plans `unmeasured`. Predictions will be weak until the estimate/actual pairs fill in. Say so in
    the report rather than emitting confident numbers off a sparse base.
  - ⚑ THE REPORT IS EXACTLY WHERE oq-0053's "SELF-AWARDED CONFIDENCE" BITES. A spike that
    recommends X with crisp tradeoffs is the system awarding itself authority — the precise failure
    oq-0053 exists to prevent. The format must carry calibration: what would CHANGE the
    recommendation · what was NOT measured · `[GROUNDED]`/`[DERIVED]`/`[INFERENCE]` per claim.
  - Who may invoke? The owner clearly. But agents hit "I don't know" too (the SEP case was the
    orchestrator's own). Can an agent PROPOSE a spike the way it files a finding, with the owner
    authorising the spend? Spikes cost tokens, so invocation is a budget act, not just a routing one.
  - Is it time-boxed, token-boxed, or scope-boxed? A research probe without a bound is how a session
    disappears.
  - Does it get a command (`/spike`)? The harness already ships a `deep-research` skill that could
    be the engine rather than something built from scratch.

⚑ the payoff the owner named, and why it is bigger than convenience: |
  "referred to by load-bearing questions with load-bearing answers" ⇒ an oq gains a `spike_ref:`,
  and the ruling becomes AUDITABLE: you can see what evidence produced it, and re-open it when the
  world changes rather than when someone remembers. Today an oq answer is unbacked judgement —
  correct for constitutive questions, wrong for empirical ones.
  ⚑ It also feeds `dn-scored-beliefs-and-earned-entitlement`: a recommendation with a recorded
  basis is a PREDICTION that later evidence can score. A spike report is a calibration datum.

next_steps:
  - Design note, `draft`. Likely REVIVES `docs/research/` + closes oq-0010 rather than minting a
    new type. Owner ratifies by hand.
  - Sequence AFTER the role-state note (in flight) — both touch how the artifact chain carries
    state, and landing them in the wrong order invites a duplicated taxonomy.
```
