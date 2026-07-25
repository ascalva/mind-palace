# Design-pass routing — where captured material goes, and what actually needs a new note

A standing routing map: captured brainstorms, finding addenda, and owner rulings assigned to a
DESTINATION (fold into an existing draft · warrant a new note · already routed · needs nothing).
Written before spawning design passes, so the scarce top tier spends on reasoning rather than
rediscovery (delegate skill: "do the cheap scouting yourself"). Re-usable for future waves —
append a section per wave.

## 2026-07-25 — the session-44 wave (the post-deploy incident night)

```capsule
topic: design-pass-routing
date: 2026-07-25 (session-44, ~02:20, while bp-100/101/102 builders run)

warrant (owner): "what are the next steps for that lengthy discussion we just had, should we spawn
fable builders to create the design documents for the relevant brainstorms? … or do you want to make
sense of it first as a body of text, since they are all related" — the second instinct, agreed and
confirmed ("I can agree with your A and B view").

THE STRUCTURE: TWO CLUSTERS, NOT ONE BODY.
  CLUSTER A — OPS: cost, observability, lifecycle contracts.
    organizing theses: (1) **cost is a property of a function IN A CONTEXT** — an O(n) primitive
    promoted into an O(n) loop, with no line of code wrong; (2) **you cannot catch an inconsistency
    without first having made a consistency claim** — enforcement requires a declared expectation.
    Has a track (docs/tracks/ops.md, minted this session) and three plans in flight.
  CLUSTER B — REPRESENTATION: what a vector, a chunk, and a space actually ARE.
    organizing thesis: **membership is the load-bearing structure** — it is simultaneously the
    dedup/compression mechanism, the identity mechanism (rename), the reuse mechanism (seen-check),
    and the history mechanism (slot-lineages). Clusters hard onto the EXISTING membership draft.
  CROSS-CUTTING (a SECTION in each, never its own note) — CALIBRATION: code as a labeled subgraph
    giving sigma ground truth; the eval-harness ladder; measured premises with a measurement date.

⚑ THE ROUTING TABLE (14 items from this wave):

| item | cluster | DESTINATION |
|---|---|---|
| f-0169 supersede_source quadratic | A | ROUTED — bp-100 in flight |
| f-0170 no enqueue coalescing | A | ROUTED — bp-101 in flight |
| f-0173 orphaned running row | A | ROUTED — bp-101 in flight |
| f-0172 status = levels not rates (Tier 1) | A | ROUTED — bp-102 in flight |
| f-0172 command center (Tier 2) | A | **NEW NOTE 1** (ops) |
| f-0171 unbounded drain / job budgets | A | oq-0035 OPEN (owner) + **NEW NOTE 1** once ruled |
| command-center.md (macro axes) | A | **NEW NOTE 1** |
| ops-and-optimal-form c2 (structured residuals) | A | **NEW NOTE 1** — instrument requirement |
| reconciliation-audit addendum (detection lag) | A | **NEW NOTE 1** + the audit's own queued pass |
| f-0174 ceiling ignores the embedder | A/B | **NEW NOTE 2** (runtime) — it is a required input |
| local-model-runtime addendum | A/B | **NEW NOTE 2** — direction decided 2026-07-22, no note yet |
| embedding-space-specialization.md | B | GATED behind NEW NOTE 2; not its own pass |
| f-0168 addendum 4 (rename = membership) | B | FOLD → dn-vector-membership-store (decisions §) |
| text-keypoints c1 + c2 (detector, grain) | B | FOLD → dn-vector-membership-store (grain §) |
| ops-and-optimal-form c1 + c3 (compression, seen-check) | B | FOLD → dn-vector-membership-store |
| doc-code addendum: lexical bridge | B→ | FOLD → dn-integrator-densification (historical window) |
| doc-code addendum: code as labeled subgraph | X | FOLD → evaluation-harness pass (sigma labels) |

⚑ THE ANSWER TO "HOW MANY NEW NOTES": **TWO, not four** — and one of them is small.

  **NEW NOTE 1 — the ops design note** (biggest, most urgent; the ops track's dod already sketches
  it). Scope: cost as a CHECKABLE property (scale witnesses, the perf-ratchet suite generalized
  beyond one method); the command center TIER 2 (macro axes: corpus completeness · history realized
  incl. n(v)/Zipf · causal density by grade · drift · headroom · liveness); the level-vs-derivative
  layout rule; anomaly as a computable predicate; the shutdown/job-budget contract (BLOCKED on
  oq-0035); detection lag as a TRACKED metric; structured residuals as an instrument requirement
  ("a diverging ETA is a measurement, not a bad number"). Warrants: f-0169..0173 + the three
  captures. Panel: **systems + core** (security low-threshold: it reads everything).

  **NEW NOTE 2 — the local-model-runtime note** (small; the DIRECTION is already owner-decided
  2026-07-22, so this is specification, not exploration). Scope: llama.cpp-direct migration; the
  OpenAI-compatible client abstraction that makes MLX a cheap later experiment; residency
  orchestration moved into palace-owned code; **f-0174 folded in as a required input** — re-ground
  `resident_gb`/`max_resident_models` against llama.cpp's REAL load/unload semantics, and decide
  whether the embedder is a third process rather than an unaccounted ghost. UNBLOCKS the embedder
  question, which is otherwise unanswerable. Panel: **systems + security** (it touches the sealed
  core's inference boundary).

  Everything else FOLDS into passes that are ALREADY OWED. That is the point of doing this map
  first: Cluster B looked like 4-5 new documents and is actually the decisions section of a draft
  that already exists.

⚑ THE REAL CONSTRAINT IS NOT BUDGET — IT IS THE PANEL/RATIFICATION QUEUE.
  Fable is at 0% this week; tokens are not the limit. The limit is that **every note needs an
  adversarial expert-panel pass before the owner ratifies** (standing ruling 2026-07-23), and the
  queue is already: dn-vector-membership-store (panel OWED) · dn-sector-experts (panel OWED) ·
  dn-integrator-densification (panel OWED, pre-dates the ruling). Adding 2 more = 5 panels + 5
  ratifications for ONE gatekeeper, on top of 3 builds in flight.
  ⇒ Sequence, do not batch.

PROPOSED ORDER (owner may re-order; nothing here is ratified):
  1. **NEW NOTE 1 (ops)** — three builds land INTO this track; writing it while they run means the
     seals and the note agree. Its Tier-1 half is being built right now, so the note's job is Tier 2
     + the ratchet doctrine, not the parts already in flight.
  2. **dn-vector-membership-store panel + fold** — absorb all of Cluster B in ONE pass rather than
     four. The note already exists; this is enrichment + the owed adversarial review, together.
  3. **NEW NOTE 2 (runtime)** — small, specification-shaped, unblocks the embedder question.
  4. **dn-integrator-densification panel** — absorb the lexical-bridge evidence for the historical
     window while the panel is running anyway.
  5. dn-sector-experts panel · the workflow-taxonomy / reconciliation-audit / eval-harness passes —
     the pre-existing queue, unchanged by this wave.

NOTE ON TIMING vs THE BUILDS IN FLIGHT: bp-100 is actively editing `core/stores/vectorstore.py`,
which the membership design reasons about. Not blocking (the design is about the MODEL, not that
file's current shape), but step 2 should read the MERGED state, not the pre-build state, or it will
ground itself on code that no longer exists.

## 2026-07-25 (addendum) — the post-build schedule, and what it actually waits on

```capsule
topic: design-pass-routing (scheduling the wave after bp-100/101/102)
date: 2026-07-25 (session-44, ~03:10)

warrant (owner): "what do you need from me to outline the rest of the build after the current
builds? just to easily schedule the work"

⚑ THE BOTTLENECK IS NOT AGENT THROUGHPUT — IT IS OWNER-GATE COUNT.
  The chain is: [AGENT: panel → design pass → /graduate → proposed] → [OWNER: ratify · bless] →
  [AGENT: build → seal] → [OWNER: deskcheck]. Everything up to `proposed` is agent-side and needs
  NOTHING from the owner. So the schedule should be organized to BATCH THE GATES, not to maximize
  agent parallelism — this file's parent brainstorm (decision-routing) already names owner attention
  as the scarcest budgeted resource.
  Current gate debt, measured: **39 open findings · 19 open owner-questions · 4 owed deskchecks ·
  3 drafts awaiting panel-then-ratification** — before this wave adds anything.

THE SEQUENCE (agent-side work, runnable without further input):
  S1. bp-100/101/102 return → diff review → sequenced merges (one at a time) → independent audit
      pass at reviewer tier (delegate skill D2) → seals with cost.actual.
  S2. RESTART CHECKLIST → `palace up` → watch the RATE → the backfill completes → code-ingest
      deskcheck becomes demonstrable.
  S3. ops design note (NEW NOTE 1) — writable NOW, in parallel with S1/S2; its Tier-1 half is
      being built, so the note covers Tier 2 + doctrine.
  S4. dn-vector-membership-store: adversarial panel + fold all of Cluster B in ONE pass.
      **Must read the MERGED vectorstore.py, so gated behind S1.**
  S5. local-model-runtime note (NEW NOTE 2, small, specification-shaped) + f-0174 folded.
  S6. dn-integrator-densification panel (absorb the lexical-bridge evidence).
  S7. the pre-existing queue: dn-sector-experts panel · workflow-taxonomy (now also carrying
      f-0175's session-state format) · reconciliation-audit · evaluation-harness.
  Each of S3-S7 ends at `draft` or `proposed` — i.e. parked ON A GATE, by design.

⚑ WHAT IS ACTUALLY NEEDED FROM THE OWNER — three decisions, not a plan:
  1. **Confirm or reorder S3-S7.** The proposed order is defensible but not the only one; the
     runtime note (S5) could reasonably jump ahead since f-0174 makes the ceiling untrustworthy TODAY.
  2. **Rule oq-0035** (shutdown escalation: bounded SIGKILL / worker-enforced job budgets / both).
     Small, and without it the ops note carries a parked decision in a load-bearing section.
  3. **Say whether the 4 owed deskchecks clear in this wave or defer.** They need ONLY the owner and
     they are what actually closes tracks — no amount of agent work substitutes.
  Optional 4th: anything the owner wants pulled forward that is NOT in the queue (the ouroboros.toml
  rename, f-0162, has been queued for days and is isolated/cheap).

⚑ AND THE STRUCTURAL ANSWER TO "just to easily schedule the work": DO NOT HAND-WRITE THE SCHEDULE.
  The artifacts already encode it — status, track, depends_on, warrant, re_entry, blocking flags.
  A schedule maintained by hand is another `resume-brief.md` (f-0175): a mutable blob that drifts
  from its sources. **The schedule should be a DERIVED VIEW** — the docket/board pattern a third
  time — showing per-track: what is owed, by whom (agent vs owner), and what it is blocked on.
  `scripts/board.py` already computes track × phase; adding "blocked-on" and "gate vs agent" turns
  it into the scheduler the owner is asking for, and it cannot drift.
  ⇒ This is the same conclusion as the findings-stream capsule (decision-routing, same session) and
    the same as f-0175: **append-only substrate + derived projection.** Fourth arrival. It should be
    a named principle before it is re-derived again.
```

open questions:
  - Does the ops note absorb finding-0165 (background starvation) and the tier-scheduling question,
    or do those stay scheduler-local? They are "cost as a first-class concern" in different clothes.
  - Should `local-model-runtime.md` move under `track: ops`? It has no track coordinate and is
    ops-shaped by every criterion in that manifest.
  - Is "detection lag" measurable from the corpora the palace already holds (git + findings + chat)?
    If yes it belongs in NEW NOTE 1 as a real gauge; if no, it stays a framing device — and that
    difference should be settled BEFORE the note claims it.
```

## 2026-07-25 (session-48) — the map reconciled after graduation: THREE notes, and NEW NOTE 1 shrank

```capsule
topic: design-pass-routing
date: 2026-07-25 (session-48, at `/graduate` on both ratified ops notes)

WHY THIS CAPSULE EXISTS. The graduate pass owed a re-scope of NEW NOTE 1 (completion-claims
honesty): `dn-supervision-and-liveness` SPLIT OUT of it and reduced it. The map above is NOT
edited — both notes reconcile with it in their own §1.1, and this capsule records the resulting
state so a future reader is not left comparing three documents to work out what is still owed.

⚑ THE COUNT IS THREE, NOT TWO.
  1. `dn-supervision-and-liveness` — RATIFIED (`3945d9f`). Split out of NEW NOTE 1 deliberately:
     it is a PREREQUISITE, not a sibling. Three of NEW NOTE 1's scoped items (liveness as a macro
     axis, detection lag as a tracked metric, anomaly as a computable predicate) all need a
     continuous probe, and a continuous probe needs a home that is not the blocked serve loop.
     That home is the execution model, which this note decides. GRADUATED → bp-108..bp-114.
  2. `dn-local-model-runtime` — RATIFIED (`56dcee4`). This IS NEW NOTE 2 (S5), with f-0174 folded
     in as the map required. GRADUATED → bp-107 (already minted) + bp-115..bp-119.
  3. **NEW NOTE 1 — still unwritten, and now SMALLER.** See its reduced scope below.

⚑ NEW NOTE 1'S SCOPE, AFTER THE SPLIT (this supersedes the bullet in the wave-1 section above).
  RETAINED, unchanged:
    · cost as a CHECKABLE property — the perf-ratchet suite generalized beyond one method; scale
      witnesses (OPS-6)
    · the command center TIER 2 — macro axes: corpus completeness · history realized (incl.
      n(v)/Zipf) · causal density by grade · drift · headroom · liveness AS A RENDERED AXIS
    · the level-vs-derivative layout rule
    · anomaly as a computable predicate
    · structured residuals as an instrument requirement ("a diverging ETA is a measurement, not a
      bad number")
    · detection lag as a TRACKED metric — but see below: its DEFINITION moved out
  MOVED OUT to `dn-supervision-and-liveness`:
    · the four-mode failure taxonomy (GONE / STUCK-IN-LANE / SLOW / HUNG)
    · the one-seam finding and the compute/land split
    · the oq-0035 ruling package and the shutdown/job-budget contract (OPS-4's design half)
    · finding-0165 (background starvation) — fairness is a property of the BATCH UNIT, i.e. of the
      execution model, not of the instrument layer
    · detection lag's four-mode DEFINITION (§2.9 there defines the four numbers; NEW NOTE 1 renders
      and tracks them)
  NO LONGER BLOCKED:
    · the shutdown contract was "BLOCKED on oq-0035". oq-0035 is RULED — (c) both, `941785d`. The
      ruling's evidence package is the supervision note, and its build half is bp-110 + bp-112.
      **NEW NOTE 1 no longer carries a parked decision in a load-bearing section**, which is the
      condition `:140` of this map set for it.
  Warrants after the split: f-0169..0173 minus what moved, plus f-0188's rendering half.
  Panel: unchanged — systems + core (security low-threshold: it reads everything).

⚑ TWO OF THIS MAP'S OWN OPEN QUESTIONS ARE NOW ANSWERED.
  · "Does the ops note absorb finding-0165, or does it stay scheduler-local?" → ANSWERED: it moves
    to `dn-supervision-and-liveness` (its §1.1), because fairness between lanes is a property of the
    batch unit — the execution model, not the instrument layer.
  · "Should `local-model-runtime.md` move under `track: ops`?" → ANSWERED by the note itself:
    `dn-local-model-runtime` carries `track: ops`, and the ops track manifest gained OPS-7 for it.
  · STILL OPEN: "Is detection lag measurable from the corpora the palace already holds?" — and it
    is now MORE answerable, because §2.9 of the supervision note gives the four quantities concrete
    definitions (lease ttl · landing-batch interval · the expectation window · batch budget +
    escalation deadline). Three of the four become measurable once bp-111/bp-112 land. The fourth
    (SLOW) is explicitly PARKED there for want of a denominator — so NEW NOTE 1 must not claim it
    as a gauge, only as a parked axis with a stated re-entry condition.

⚑ WHAT THIS MEANS FOR THE QUEUE. The panel/ratification queue was the map's stated real
  constraint, and it is now SHORTER than the wave-1 estimate rather than longer despite the note
  count going 2 → 3: two of the three are ratified, and the third arrives without a parked
  decision inside it. Sequencing: NEW NOTE 1 is the only design work left on the ops track, and it
  is best written AFTER bp-111/bp-112 land, when three of its four detection-lag numbers exist as
  measurements instead of definitions.
```
