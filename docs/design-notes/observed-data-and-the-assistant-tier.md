---
type: design-note
id: dn-observed-data-and-the-assistant-tier
status: draft
implementation: partial   # corpus-audit 2026-07 verification
created: 2026-06-25
updated: 2026-07-01
links: []
supersedes: null
superseded_by: null
warrant: null
---

# Design note — Observed data, the assistant tier, and the authored/observed firewall

*Family tag → family 1 (labelings & flow): the observed provenance class and the authored/observed firewall — observed exhaust is quarantined from the mirror and the §15 baselines. See [`../NOTATION.md`](../NOTATION.md).*

**Status:** design only, not implemented. Raised 2026-06-25 while scoping a "Jarvis-like"
expansion (email/calendar/news/activity-history, multi-node compute). Steers Phases 3+
and the airlock/interface work; nothing here changes Phases 0–2. Read alongside
`skills-and-scope.md` — every external capability below is an **executable skill** under
that model (scoped tool, object-capability handle, gated for any outward action).

## The core decision (honor this above the rest)
The system now has two purposes that must NOT share one data pool:

1. **The mirror** — introspection over the owner's *authored* corpus (notes, poems,
   journals). Fed only by what the owner deliberately wrote. This is the original §1
   mission and the thing the dreaming agent (§9) reflects back.
2. **The assistant** — outward productivity (email triage, calendar, news, recommendations)
   that may read *observed* data (activity/web/social history, sensors).

**Firewall:** authored ground truth and observed signal are separate provenance classes in
separate pools. Observed data MUST NOT feed the thought-graph that the mirror/dreaming
agent reads, and MUST NOT feed behavioral baselines (§15) or the Constitution-conformance
checks. The assistant may read both; the mirror reads only authored. If the two pools ever
merge, the introspective mirror is contaminated by algorithmic exhaust (YouTube/feed bias
reflected back as if it were the owner's psyche) — a silent, hard-to-detect failure.

## Provenance classes (extends §8 explicit/interpreted)
- **authored** — owner wrote it. Ground truth, immutable, feeds the mirror. (Existing.)
- **observed** — behavioral exhaust from third-party systems (Google "My Activity" via the
  Data Portability API, web/social history, sensor streams). Third-party origin,
  low-trust, noisy, algorithmically shaped. New class. Tagged, quarantined to the
  assistant tier.
- **interpreted** — system inferences over either, already marked derived. (Existing.)
Observed data is never silently promoted to authored. A query/agent declares which
provenance classes it may read; the mirror declares `authored` only.

## Why observed data is low-trust (record the reasoning, not just the rule)
- It is not deliberate — idle searches, abandoned videos, impulse clicks.
- It is algorithmically distorted — skewed toward the engaging/impulsive, the opposite
  distortion from the authored corpus's skew toward the unresolved/intense. Blending two
  opposite distortions does not yield "the real owner"; it yields a portrait neither
  honest nor attributable.
- It is a concentrated surveillance dossier — pulling it inward is a large inbound flow of
  exactly the sensitive data the sealed core exists to protect. Storing it is a real
  decision, not a free enrichment.

## How it attaches without breaking the design
- **Ingestion** of observed data (Data Portability export, etc.) runs through the airlock
  pattern (§16): the fetch is a Zone-B/edge job; the export lands in staging; the core
  ingests it tagged `observed`. The Data Portability API is the right mechanism (authorized
  export, not scraping).
- **Assistant capabilities** (email/calendar/news/recommendations) are **executable skills**
  (`skills-and-scope.md`): scoped tools, sandboxed, object-capability handles.
- **Read vs act, the Jarvis caution.** Reading-to-summarize is a sandboxed fetch into a
  derived view — fine. *Acting* outward (send email, book appointment, pay, post) is an
  action-on-the-world-with-credentials = the OpenClaw failure mode. Every outward action
  goes through propose → human-approve → code-acts (§14). Agents draft and propose; the
  owner approves; deterministic code executes. No agent holds live send/pay credentials.
- **Derived assistant agents** (a personalized news aggregator / "Ground News alternative",
  a recommendation agent) read the `observed` pool + interpreted layer, never the authored
  mirror. Their outputs are assistant-tier, not introspective truth.

## Multi-node compute (related, lighter)
A second machine does NOT raise the 32GB ceiling — inference can't pool working memory
across a slow interconnect. What it buys is **offload**: the scheduler (Phase 3) targets a
second **worker node** for cron-tier jobs (dreaming/curation/synthesis) so the foreground
M2 Max is uncontended. Fits §5's HTTP-abstracted model serving with no rearchitecture.
Best value: a used larger-memory Apple-Silicon box (same stack, headless, and 64GB+ lifts
the ceiling for offloaded jobs). Defer purchase until Phase 3 — the scheduler is what makes
a second node useful.

## Delegating future tool development to coding agents
New tools are self-contained: a skill doc + a scoped ToolSpec + a §11 exec profile + tests
against the invariants. Build them **outside** the live system in a normal repo with PR
review (best-in-class coding agents are good at exactly this shape), then install the
reviewed artifact inside under scope. The live system does NOT write its own new
capabilities unreviewed — that is the self-modification loop (§14), the last and most gated
thing. Keep development-time codegen separate from the runtime's own sandboxed execution.

## Conflicts flagged
- **Mission (§1) / mirror integrity:** the firewall is the protection — observed never
  feeds the mirror or behavioral baselines.
- **Sealed core (Inv 1) / airlock (§16):** observed ingestion is an inbound flow; route it
  through edge/staging, tag on entry, never let the fetcher read the authored corpus.
- **Scope ceiling + model-advises-code-acts (§10, Inv 3):** assistant actions are gated
  executable skills; no live credentials in any agent.
- **Provenance (§8):** add the `observed` class; agents/queries declare readable classes;
  mirror = authored only.
