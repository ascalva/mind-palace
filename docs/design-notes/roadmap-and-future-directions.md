---
type: design-note
id: dn-roadmap-and-future-directions
status: draft
implementation: partial   # corpus-audit 2026-07 verification
created: 2026-06-25
updated: 2026-07-01
links: []
supersedes: null
superseded_by: null
warrant: null
---

# Design note — Roadmap & future directions (post-Phase-10 areas of interest)

*Family tag → cross-cutting: post-Phase-10 directions spanning all families; each area notes its provenance/zone (family 1) implications. See [`../NOTATION.md`](../NOTATION.md).*

**Status:** roadmap, NOT committed spec. Does **not** change Phases 0–10; the phased build
proceeds unchanged. Captures the 2026-06-25 discussion so it's tracked and we can circle
back. Each area lists where it attaches, its provenance/zone implications, and open
questions. Decisions deferred until the area lands. Read alongside `skills-and-scope.md`
and `observed-data-and-the-assistant-tier.md`; this extends both.

A few items here are relevant *before* post-10 and are flagged **[affects current build]** —
chiefly the process/concurrency model (Phase 3) and the provenance spectrum (extends the
type already built in Phase 1).

---

## 0. The end state, and the two things that keep it sane
The target is a "guardian / second brain": a system that, with minimal interaction,
contributes to progress, productivity, thematic extraction, and self-understanding by being
woven into daily life. Two non-negotiables keep that from rotting into an over-credentialed
daemon:

- **The firewall** (observed-data note): the authored *mirror* and the observed *assistant*
  are separate provenance pools. Life-tracking enriches the assistant; it never feeds the
  mirror or the behavioral baselines.
- **Read vs act** (skills-and-scope): reading-to-summarize is a sandboxed fetch into a
  derived view; *acting* outward (send, book, pay, post) is a gated executable skill —
  propose → human-approve → code-acts. No agent holds live credentials.

**Wellbeing directive (record this):** a system that tracks productivity, health, and mood
must *inform, not nag*. It surfaces patterns the owner can accept or reject (mirror, not
oracle); it does not judge, pressure, or amplify negative self-talk. This follows directly
from the Constitution's autonomy and no-over-reliance directives, and it applies with extra
force to anything biometric or productivity-scored.

---

## 1. Provenance spectrum (the unifying thread) **[affects current build]**
The binary authored/observed is too coarse for the new sources. Refine into sub-classes
(the Phase-1 `Provenance` type was deliberately built extensible — this is its growth path):

| class | meaning | feeds mirror? | examples |
|---|---|---|---|
| `authored-solo` | owner wrote it, alone | yes | notes, poems, film photos (visual) |
| `authored-dialogue` | owner wrote it, in dialogue | yes (duet-tagged) | Claude conversations, owner's *sent* messages |
| `curated` | owner selected/annotated *others'* words | interest-signal only, not as the owner's voice | Goodreads highlights + notes |
| `observed` | behavioral exhaust from third-party systems | **no** (assistant only) | analytics, music plays, sensors, received-message content-signal, reading lists |
| `interpreted` | system inference over any of the above | n/a (marked derived) | inferred themes, moods, style summaries |

Rules: a query/agent declares which classes it may read; the mirror declares the authored
classes (+ optionally `curated` as interest signal, never as voice). Promotion across
classes (e.g. observed → authored) is a **deliberate human act**, never automatic. The
`authored-dialogue` tag exists so the dreaming agent doesn't mistake the shape of a
conversation-with-an-interlocutor for the owner's solo mind.

---

## 2. The inbound distillation gate (the "delicate procedure")
The owner named the hard part: an interface that sanitizes/extracts external data for
internalization *without causing drift/misalignment*. Make it a named subsystem, not an
afterthought. It is the inbound side of the airlock (§16) with three jobs, in order:
1. **Fetch** in the edge zone (never the core); land raw in staging.
2. **Tag provenance on entry** (§1) — observed data is `observed`, immutably, before the
   core sees it.
3. **Distil to a derived view** the assistant tier reads — relevance-filtered, summarized,
   provenance-stamped. Nothing crosses into `authored`/mirror automatically.
The gate is where contamination would happen, so it is conservative by construction:
default-quarantine, explicit-allow, human-gated promotion. Core agents have **zero** access
to external sources; only this gate's *output* (tagged, distilled) is readable, and only by
the assistant tier.

---

## 3. New data sources (attach via §1 + §2)
- **Claude conversations** → `authored-dialogue`. High-quality, deliberate reasoning. Export
  from Claude (periodic, owner-pulled), through the inbound gate. Style inferences stay
  `interpreted` — never feed the model a summary of "how the owner thinks" as fact (it
  performs its own caricature back). 
- **Text messages** → owner's *sent* = `authored-dialogue`; *received* contains **other
  people's data** — consent/privacy wrinkle: treat received content as low-trust signal at
  most, do not ingest others' words as the owner's corpus.
- **Email** → sent = `authored-dialogue`; received = `observed` content-signal (interests),
  others' data handled like received texts. Triage/summarize = read; sending = gated skill.
- **Goodreads** (read / want-to-read / highlights / notes) → highlights & notes = `curated`;
  the lists = `observed` interest signal. The owner's *own* marginal notes lean toward
  `authored`. Good signal for the recommendation and reading-companion agents.

---

## 4. Peripherals & sensors
- **Oura / Apple Watch (or open-source equivalents)** → `observed`, into the dormant
  `sensor_readings` table (already built, Phase 0). Biometrics (HRV, sleep, activity).
  Assistant tier only; never a behavioral baseline for the mirror. Remember the honest limit
  from earlier: biometrics → *mood* is noisy; surface correlations against authored mood
  entries for the owner to judge, don't assert mood.
- **Calendar** is two things: *reading* (events as assistant context) and *writing* (create
  events, reminders, doctor appointments — from parsed emails, manual entry, or "schedule
  X"). Writing is an **outward action** = gated executable skill (propose → approve →
  code-acts). Appointment extraction from email is read-only distillation; the *booking* is
  gated.

---

## 5. Multi-sensory & creative
- **Film-photo embeddings** → `authored-solo` (visual). Needs a **multimodal/vision embedding
  model** (CLIP-class) — a real capability jump with **RAM implications** on the 32 GB
  ceiling (a resident vision model competes for the worker slot). Value: the dreaming agent
  could surface visual style/themes alongside textual ones — cross-modal thematic
  extraction. Treat as its own capability track; likely wants the second node (§7) for the
  heavier model. Image inferences (detected style, recurring subjects) are `interpreted`.
- **Music taste tracking + recommendation/playlists** → listening history = `observed`; a
  recommendation agent = assistant tier. A genuine live life-tracker; outputs are
  assistant-tier suggestions, not introspective truth.

---

## 6. Capture & conversation loop (the daily UX)
"Where do I write notes on my phone that auto-ingest, and how does that become a
conversation?" Two complementary paths:
- **Deliberate capture** → a synced markdown vault (the ingest pipeline already watches a
  vault path; a phone Logseq/Obsidian or a synced folder writes into it; the watcher ingests
  as `authored-solo`).
- **Conversational capture** → the messaging/interface adapter: text the assistant, it stores
  the exchange as `authored-dialogue` and ingests it, and you can immediately converse about
  any topic because the librarian retrieves over the same graph. The interface is both the
  capture surface and the query surface — one loop.

---

## 7. Process & concurrency model **[affects current build — Phase 3]**
Answering the "are agents processes / round-robin / time-slice?" question, because Phase 3
is the scheduler.
- **Agents are not OS processes.** They are config (prompt + scope + memory) time-sharing the
  model slots through the durable queue. There is a *small* set of long-lived processes: the
  **supervisor**, Ollama, and (later) the **edge gateways** (separate for the trust
  boundary). Agents are in-process tasks within the core runtime.
- **Not preemptive time-slicing.** You cannot cleanly preempt a model mid-generation, and
  swapping model+context per slice thrashes on model-load (the dominant cost). Scheduling is
  **cooperative**: short jobs run to completion; long jobs (dreaming, curation) are written
  as **checkpointed steps** that yield between units. Priority and preemption act **at job
  boundaries** — a reactive escalation is dispatched next, it does not interrupt a running
  generation. The pinned router does quick interstitial classifications while the worker
  runs; two *heavy* generations never run at once.
- **The queue is the single safe serialization point.** One supervisor owns it (SQLite, WAL).
  Single-writer-by-design avoids most contention; readers are fine. "Restoring an agent" is
  cheap — its context is re-composed from the stores per invocation (agents are config), so
  there's no heavyweight context-switch, only the model load.
- **Optimal execution unit:** task-based (run-to-completion / checkpointed-step), not a fixed
  time quantum. The scarce serial resource is the worker slot; design around model-load, not
  around fairness ticks.

---

## 8. OS-agent health & "self-replacement" (the reframe)
The worry: the always-on, most-privileged *agent* needs a delicate blue-green self-swap.
The reframe dissolves most of it:
- **The privileged always-on thing is the supervisor (deterministic code), not the model.**
  The tiny model only *advises*; code *acts*. The model holds **no durable state** (all in
  SQLite), so it is a **stateless, hot-swappable advisor** — "replacing" it is just loading a
  different model into the pinned slot. No handoff dance, because there is no agent state to
  hand off.
- **Health & resilience:** monitor the model via telemetry (latency, error rate, sane
  output). If it degrades, **fall back to rules** — the scheduler is rule-capable by design;
  the router model is an enhancement, not a single point of failure. **launchd `KeepAlive`**
  restarts the supervisor *process* if it dies. The always-on guarantee is OS-level, not a
  self-replicating agent.
- **Model upgrade = shadow-eval + gated promotion (reuses §14/§15).** Load a candidate
  pinned/worker model, run it in shadow against the golden set + behavioral check, compare to
  the frozen baseline, **promote or roll back** — blue-green at the *model* level, but it's
  the existing gated/validated loop, deterministic in execution, never the model rewriting
  itself. Frequency: event-driven (a candidate appears), not a timer.

---

## 9. Self-audit & self-optimization (design/infra/logic — NOT the graph)
The owner wants the system to audit itself and know efficient ways to add capabilities.
Split cleanly:
- **Self-audit = observe + propose.** Reports on its own design/infra/logic (perf, dead code,
  invariant drift, cost). This is **safe and can be liberal** — it produces *reports and
  proposals*, it does not act.
- **Self-modification = act.** Any change those audits imply goes through the §14 gate
  (propose → approve → execute → validate → rollback). Auditing is not modifying.
- **Use Claude / external coding agents for the design/infra/logic audits** (best-in-class at
  exactly this), via build-outside → review → install-under-scope (observed-data note). The
  live system does not write its own new capabilities unreviewed — that is §14, the last,
  most-gated phase. (The knowledge graph itself is the core agents' work, never an external
  agent's — keep that line.)

---

## 10. Dashboards — candidate **Phase 11**
Admin / birds-eye observability, read-only over stores that already exist or are planned:
current model executing, models loaded, RAM headroom, queue depth/task queues, graph
metrics, sensor/IoT metrics, subsystem metrics, dream-cycle reports, system health. Low-risk
(read-only). Lives as a **local/private interface** (Tailscale/local app, like the §12
interface), not internet-exposed.
- **Drift & alignment study** (the interesting part): yes, drift is studyable — plot the
  **golden-set metrics and Constitution-conformance scores over time against the frozen
  baseline**. The divergence between the rolling baseline and the frozen anchors *is* the
  drift signal (§15). "Some drift is OK; deterioration is not" becomes a visible curve with a
  human-set tolerance band; breaching it is the rollback trigger. The dashboard is where the
  "living organism that needs nurturing" intuition becomes an actual gauge.

---

## 11. Security
- **Provenance integrity.** Content-addressing (sha256) already gives the immutable raw layer
  integrity + dedup. Extend with **signatures (asymmetric)** to attest *source/authenticity*
  of ingested external data, and to distinguish **immutable** (raw, content-addressed) from
  **mutable** (derived indexes, graph organization) cryptographically. This belongs to a
  provenance/integrity module, layered on the existing raw store.
- **Encryption posture (a deliberate call, not maximalism).** Rely on **FileVault** for
  at-rest (transparent, strong, no per-access overhead) rather than frequent app-level
  encrypt/decrypt of the live stores (low marginal benefit, high perf/key cost). Use
  **hashes/signatures for integrity** (the provenance module), **TLS / Tailscale for
  in-flight** (anything to edge/cloud/second node), and **restic** (already encrypted) for
  backups. Reserve app-level encryption for data that *leaves* the machine.
- **Keys from a sealed core.** A no-egress core **cannot call KMS** (network). Resolution:
  the core never does. Local secrets come from **Keychain / Secure Enclave** (hardware-backed,
  local, no network). Off-machine keys (KMS, a YubiKey) are unwrapped by an **edge-side secret
  broker** that hands the core only the material it needs over the local channel. The core
  depends on a *local secret-retrieval interface*; whether it's Keychain or a broker is an
  implementation detail behind that interface — the core never makes the call. Preserves
  Invariant 1.

---

## 12. Backups as drift recovery
restic → S3 (§16) already covers crash recovery. Add the framing: backups are also
**drift-recovery checkpoints** — restore to a pre-drift state when §15 detects deterioration
past tolerance, complementing the §14 per-change rollback. Snapshot *system state* (the
gated-change ledger, baselines, agent registry), not just data, so a restore is coherent.

---

## 13. Candidate new phases (summary)
Folded into the plan when the time comes; not committed:
- **Phase 11 — Dashboards & drift study** (read-only observability; the drift gauge).
- **Multi-node offload** — a *deliberate* extension of the sealed boundary to a second sealed
  peer over a private link (Tailscale, no internet egress, explicitly allowlisted in
  `core.sealing`) or routed via edge — **never silent** (the builder's Phase-1 flag stands).
  Gated by Phase 3 existing first.
- **Assistant tier + provenance enforcement + inbound distillation gate** — the observed pool,
  the firewall enforcement, the executable-skill capabilities (calendar/email/news/music).
  Spans the airlock (Phase 8) and skills/factory (Phases 4–5).
- **Multimodal / film-photo embeddings** — its own capability track; wants the second node.
- **Self-audit reporting** — safe, can land early as observe+propose; modification stays §14.

---

## 14. Open questions to resolve when each lands
- Multimodal model choice + where it runs (almost certainly the second node) and its RAM
  budget against the two-slot ceiling.
- Consent handling for *received* messages/emails (others' data) — likely: never ingest as
  corpus; at most low-trust observed signal, possibly excluded entirely.
- Promotion mechanism for `observed`/`curated` → `authored` (human ritual; what the UI is).
- Tolerance bands for the drift gauge (what divergence is "OK" vs "rollback").
- Secret-broker design (edge process vs Keychain-only) once a KMS/off-machine key is actually
  needed.
