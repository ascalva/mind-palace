# Reconciliation audit — intent vs design vs implementation vs math (the anti-jenga instrument)

Brainstorms on making the four links of the artifact chain *mechanically checkable*, so speed
cannot silently accumulate drift. Feeds a Fable design-pass → its own track. Companion capsule:
the capability/limits test-tier ladder in `evaluation-harness.md` (2026-07-23).

## 2026-07-23 — the owner's jenga worry, made structural

```capsule
topic: reconciliation-audit
date: 2026-07-23 (session-43, post bp-099 seal)

warrant (owner, verbatim concern): "we are moving so fast that I might not notice the little
things … before I know it, I just have a jenga tower on a shaky foundation. Maybe we need a full
end-to-end audit — or how else can we reliably compare intent vs design, design vs what's actually
there, or if the math is even right. If you are missing something, that means I was wrong to trust
even your mathematical derivations."

evidence base (all from 2026-07-22, one day — the error-rate/detection-lag model):
  - PD-B was RATIFIED on a false quantitative premise (the "cost" of history was never measured;
    actual: 1,542 versions ≈ 6× HEAD — trivial). Detection lag: ~1 day, caught by the owner's
    insistence, not by any gate. (finding-0163)
  - The orchestrator's §6 probe shorthand was a WRONG DERIVATION (set-cardinality error; would
    enqueue backfills forever). Detection lag: hours — caught because the plan carried a
    FALSIFIER and the builder executed it. (finding-0166)
  - Stale module path in a ratified note (core/temporal → core/kernel/temporal); the id-collision
    across retained versions; FORCE_COLOR test fragility (finding-0160). All caught, all by
    DIFFERENT layers, with lags from minutes to weeks (findings 0141/0146/0159 were the
    weeks-late class: things that DID silently accumulate).
  - Model: error rate ∝ speed; jenga-vs-not is determined by DETECTION LAG, not by error rate.
    The audit's job is to bound the lag.

decisions (proposed):
  - The audit is NOT a one-time report (a report is stale the week after). Its deliverable is a
    standing, machine-checkable mapping: EVERY ratified design decision → its ENFORCEMENT
    artifact, one of {test | ratchet | structural (type/import/schema) | UNENFORCED-accepted
    (explicit, owner-signed)}. Drift = a decision whose artifact is missing, red, or no longer
    tests what the decision says. Structural-enforcement doctrine applied to the meta-level.
  - Four links, four instruments:
    (1) intent→design: ratification stays the human gate, hardened by two template rules —
        a parked decision carries a MEASUREMENT, never an estimate (the PD-B lesson); every §2
        decision names its intended enforcement inline. Ratification is the one step that must
        stay SLOW (owner reads §1.2 aloud; premises checked) — the system may move at machine
        speed everywhere except there.
    (2) design→implementation: the decision→enforcement map (above) + the deskcheck gate
        (already live) + the wiring question (finding-0159, already law).
    (3) implementation→behavior: the test-tier ladder (evaluation-harness capsule) — T1
        property tests carried from every §8 into the suite as a graduation requirement.
    (4) math→truth: every design-note derivation ships a CHECKABLE artifact (T2 harness:
        sympy/numeric/Mathematica) + ADVERSARIAL verification at design time — an independent
        checker briefed to REFUTE the derivation, not confirm it. An unchecked derivation is
        flagged AT RATIFICATION, not discovered at build.
  - One-time BASELINE SWEEP (its own track, budgeted): parallel auditors over
    {every ratified note × its claimed properties × the actual code}. Per property, verdict ∈
    {enforced-by-test | enforced-by-structure | unenforced-accepted | DRIFTED | FALSE}. Every
    DRIFTED/FALSE exits as a finding; every confirmed-but-unenforced property exits as a RATCHET
    (the output compounds instead of decaying). Home: docs/audits/ + a derived decision-map.
  - Standing cadence after baseline: a /triage extension (or sibling sweep) samples N decisions
    per cycle and re-verdicts them; the map is regenerated like the board (derived view, never
    hand-edited). New ratifications enter the map at ratification time.
  - The self-referential endgame (why this fits the system rather than sitting beside it): the
    composed causal graph (dn-integrator-densification) makes "which commits/conversations
    implement decision D" a QUERY — the audit progressively becomes a standing instrument of the
    system over itself, the same provenance chain (note → plan → commit → code) it already
    captures. Ouroboros as QA model.

OWNER RULING (2026-07-23, this capture — the standing pre-gate):
  - **Every design pass AND every build pass gains an ADVERSARIAL REVIEWER/AUDITOR before the
    artifact reaches the owner to bless/ratify** — review on merit, logic, reason, correctness.
    The blessing gate's input becomes {the artifact + the adversarial report}, never the artifact
    alone.
  - Shape (proposed, for the Fable pass to pin):
    * INDEPENDENT — never the author (fresh context, no sunk reasoning), briefed to REFUTE, not
      to confirm; findings ranked by severity, each with the concrete failure it implies.
    * Design-side scope: do the premises carry measurements (the PD-B class); does the argument
      hold (logic/reason); is the math checked or checkable (a derivation without a falsifier is
      itself a finding); are the pinned interfaces REAL (grep-verified paths/signatures — the
      stale core/temporal path class); §1.2 non-goals read adversarially (the load-bearing-
      non-goals class); is it worth building at all (merit — supersede/park is a legal verdict).
    * Build-side scope: the diff vs the plan's items/falsifiers/invariants (the review the
      orchestrator ran at the bp-099 merge, formalized + made independent of whoever supervised
      the builder); gates re-run on the combined tree; write-scope + pin conformance.
    * Output is a typed review artifact attached to the note/plan (the finding-0147 "fable
      line-by-line audit — 16 corrections" commit is the ad-hoc precedent; this makes it
      MANDATORY and uniform). Tier scales with stakes: design → Fable/xhigh; build diffs → opus.
  - Today's mirror, for the record: the §6 probe cardinality bug and the false PD-B premise are
    both design-side catches this gate would have made BEFORE ratification; the id-collision and
    poset-contract catches are build-side ones it institutionalizes.
  - Enforcement path: interim = orchestrator discipline EFFECTIVE NOW (no artifact goes to the
    owner un-reviewed); structural = the workflow-track-taxonomy Fable pass amends
    dn-agent-workflow (the chain gains a stage: draft → ADVERSARIAL REVIEW → ratify;
    seal → ADVERSARIAL REVIEW → bless/deskcheck), and gate-guard/Stop-gate learn to demand the
    review artifact's existence.

OWNER REFINEMENT (2026-07-23, same capture): **the adversaries are DOMAIN EXPERTS** — not one
generalist refuter but a panel of specialists, each with a single deep concern:
  - The roster (initial; grows as domains do):
    * **core auditor** — the sealed core: store/ingest/retrieval semantics, provenance firewall
      (non-laundering, MIRROR_READABLE), self-containment/import discipline, single-writer,
      re-derivability, the memory ceiling. Lives in BUILD-SPEC + core/**.
    * **harness/workflow auditor** — the artifact chain itself: gates, write_scope capability,
      hooks, template conformance, delegation discipline, blessing integrity.
    * **security auditor** — the non-negotiables as an attack surface: egress seal, network/vault
      separation, secrets, sandbox powerlessness, effector tiers, blast radius; adversarial about
      capability LEAKS (the Track-G class), not just bugs.
    * **mathematics/logic auditor** — derivations, invariants, premises-measured, falsifier
      presence, the reasoning-complex / fiber-geometry / homology claims, gauge statistics;
      wields the T2 harness (sympy/numeric) as its instrument.
    * **systems/scheduler auditor** — concurrency, queue discipline, starvation (the
      finding-0165 class), crash/recovery, idempotency under retry, growth curves.
  - **Auditor briefs are standing ARTIFACTS, not re-derived prompts** — the natural home is
    `.claude/agents/auditor-<domain>.md` beside builder.md/scribe.md (the contract mechanism
    already exists). Each brief carries: the domain's invariants, its checklist, and a grown
    "misses" section — every detection-lag failure in that domain becomes a permanent checklist
    line (the compounding property: the panel gets sharper with every finding).
  - **Routing is mechanical, not judgment:** the artifact's touched surfaces select the experts —
    write_scope globs map to domains (core/** → core auditor; scheduler/** → systems; edge/,
    secrets, effectors → security ALWAYS); a non-N/A §8 → math auditor MANDATORY; design notes
    always get workflow + their surface's experts. Security and math sit on a low threshold —
    when in doubt, they're in.
  - **Independence + accounting:** experts run parallel, read-only, small-context (brief +
    artifact + targeted greps — fleet-shaped, cheap per unit); each files findings independently
    (no consensus-seeking — a lone dissent is a feature); the merged report names WHICH experts
    examined WHAT, so an unexamined surface is visible (the integrator's named-not-dropped
    accounting, applied to review coverage). Tier by stakes: math/security highest.
  - This mirrors dn-agent-taxonomy on the workflow side: the system's own agents are typed by
    scope-and-concern; the auditors are the same species pointed at the workshop instead of the
    corpus.

open (for the Fable pass):
  - adversarial-review depth vs cost per artifact class (a one-line fix plan vs a new subsystem
    note do not warrant the same fleet); who reviews the reviewer's misses (the standing-cadence
    sweep is the backstop).
  - the decision-extraction grain: what exactly is "a decision" in a ratified note (the D-blocks?
    every [DERIVED] claim? §2 bullets?) — needs a convention the extractor can parse.
  - map representation: a derived markdown table (board.py precedent) vs a typed sqlite the
    ratchets read; who regenerates it and when.
  - verdict honesty: how to stop "enforced-by-test" from rotting (a test that no longer tests the
    claim) — mutation-testing spot checks? property-test minimums per decision class?
  - sizing/budget: baseline sweep is fleet-shaped (many small read-only auditors) — post-reset
    (Jul 24+) work; estimate at graduation, gate on the weekly pool.
  - relation to WIRING-AUDIT.md and docs/audits/* (the existing one-shot audit artifacts):
    absorb-and-supersede vs keep as historical snapshots.
```
