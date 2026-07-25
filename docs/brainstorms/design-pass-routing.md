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
| ops-and-optimal-form c2 (structured residuals) | A | **NEW NOTE 1** — as an instrument requirement |
| reconciliation-audit addendum (detection lag) | A | **NEW NOTE 1** + the audit's own queued pass |
| f-0174 ceiling ignores the embedder | A/B | **NEW NOTE 2** (runtime) — it is a required input |
| local-model-runtime addendum | A/B | **NEW NOTE 2** — direction decided 2026-07-22, no note yet |
| embedding-space-specialization.md | B | GATED behind NEW NOTE 2; not its own pass |
| f-0168 addendum 4 (rename = membership) | B | FOLD → dn-vector-membership-store (decisions §) |
| text-keypoints c1 + c2 (detector, grain) | B | FOLD → dn-vector-membership-store (grain §) |
| ops-and-optimal-form c1 + c3 (compression, seen-check) | B | FOLD → dn-vector-membership-store |
| doc-code addendum: lexical bridge | B→ | FOLD → dn-integrator-densification (historical window) |
| doc-code addendum: code as labeled subgraph | X | FOLD → the evaluation-harness pass (sigma labels) |

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

open questions:
  - Does the ops note absorb finding-0165 (background starvation) and the tier-scheduling question,
    or do those stay scheduler-local? They are "cost as a first-class concern" in different clothes.
  - Should `local-model-runtime.md` move under `track: ops`? It has no track coordinate and is
    ops-shaped by every criterion in that manifest.
  - Is "detection lag" measurable from the corpora the palace already holds (git + findings + chat)?
    If yes it belongs in NEW NOTE 1 as a real gauge; if no, it stays a framing device — and that
    difference should be settled BEFORE the note claims it.
```
