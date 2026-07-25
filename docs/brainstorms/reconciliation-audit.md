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

## 2026-07-25 — the first incident: the cycle CLOSED but did not START

```capsule
topic: reconciliation-audit (detection lag, measured empirically for the first time)
date: 2026-07-25 (session-44, immediately after the finding-0169 incident)
companion capsules: command-center.md · ops-and-optimal-form.md (same sitting)

warrant (owner, verbatim): "all this is how we get closer to proving ouroboros is operating as
expected, by catching inconsistencies in performance, investigating, brainstorm/design, planning,
building, resolving, a cycle of refinement"

WHAT THE INCIDENT PROVED — the chain closes, and fast:
  inconsistency (backfill not progressing) → measurement (11.7s/scan, 2 scans/version, sample(1)
  hot stack, the failed job row) → 5 TYPED findings with numbers attached → routing (4 builder,
  1 orchestrator) → 2 captures → a track with sequencing → a restart checklist. ~2 hours, and
  nothing load-bearing lives only in the transcript. The fresh-agent test passes: tomorrow's
  session has the figures, the forbidden action (`palace up`), and the order of work.

WHAT IT DID NOT PROVE — and this is the finding:
  **The cycle did not START on its own. Ouroboros did not catch this. The OWNER did — because his
  laptop fans went quiet and the battery hit 1%.** Detection came from the PHYSICAL WORLD, not from
  any instrument the system owns. Plugged in and asleep, the lag would have been overnight and the
  queue in the tens of thousands by morning.
  ⇒ Five of six links in the refinement cycle are working. THE FIRST ONE IS STILL MANUAL.
  ⇒ This audit's own model says jenga-vs-not is determined by DETECTION LAG, not error rate.
    First empirical datum for that model on a PERFORMANCE defect: **lag ≈ 75 min, and it was
    bounded by an ACCIDENT (a battery), not by an instrument.** Every prior datum in this file was
    a correctness/spec defect caught by a human, a falsifier, or a gate. Performance had no layer
    at all — not a weak layer, an ABSENT one.
  ⇒ Reframes the command center: not a nicer dashboard, but THE MISSING FIRST LINK of the loop the
    owner is describing. It is what moves the trigger from "the owner happened to look" to "the
    system said so."

THE SHARPENING (the formulation worth keeping):
  **You cannot catch an inconsistency without first having made a consistency claim.**
  "Operating as expected" presupposes a stated expectation. There was NO declared expectation for
  backfill throughput, so nothing could be violated — the system was not silent about a problem, it
  was silent because no predicate existed to be false. This is the deep form of the ratchet
  argument, and it generalizes this audit's thesis: the decision→enforcement map is exactly a
  registry of consistency claims. Scale witnesses, rate budgets, declared bounds are not
  bureaucracy — they are what makes "inconsistent" a COMPUTABLE PREDICATE rather than a human
  noticing the room got quiet.
  ⇒ Proposed extension to the audit's map: every ratified decision gets an enforcement artifact
    (already designed) AND, where it makes a quantitative claim, a MEASURED PREMISE with its
    measurement date. A premise with no measurement is drift waiting to happen — f-0163 (PD-B's
    cost premise) and f-0169 (the re-land idiom's cost premise) are the same defect one week apart.

THE RECURSION (Ouroboros doing the thing it is named for — and its shadow):
  These findings become corpus. Tonight's failure is ingested, embedded, retrievable, and informs
  the design that prevents its recurrence — the system learning from its own operational exhaust.
  SHADOW SIDE, same property, same night: f-0170 — the chat watcher watches the agent's own
  transcripts, so self-observation became self-load. Investigating the queue grew the queue.
  Self-consumption is the thesis AND the failure mode; the audit should treat "does this sensing
  loop have damping?" as a standing question, not a one-off.

open questions:
  - Should the audit map carry a "last measured" column for every quantitative premise, and should
    a stale premise (older than N, or predating a scale change) itself be a finding?
  - Detection-lag as a tracked METRIC: can the system compute its own lag (defect introduced →
    defect detected) from the git + findings + chat corpora it already holds? That would make this
    file's central model self-measuring rather than anecdotal.
  - Which layer SHOULD have caught f-0169, counterfactually? (a perf ratchet in CI; a rate alarm in
    the daemon; a scale witness on the store primitive) — the answer picks the first instrument to
    build, and the three are not equally cheap.
```
