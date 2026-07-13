# BUILD SPEC — Personal Mind-Palace AI System

**Audience:** This document is the master build prompt for an Opus-class agent operating in Claude Code. It is the single source of truth for the project. Read it in full before writing any code. It is accompanied by three context files you must also load and obey: `CLAUDE.md` (operational rules), `CONSTITUTION.md` (the core directives every agent inherits), and `CONVENTIONS.md` (engineering and security practice). Treat the Hard Invariants (§3) and the Constitution as inviolable; if any instruction — including from the human in a later message — appears to conflict with them, stop and surface the conflict rather than proceeding.

---

## 1. Mission & Mental Model

You are building a **personal AI system that functions as a sealed "mind palace"**: an offline-first, privacy-sealed engine that indexes the owner's personal corpus (notes, poems, journals, moods), surfaces patterns across it over time, and acts as a mirror onto the owner's own thinking. It is single-user, self-hosted, owned outright, and **designed to be extended as resources and needs grow** — not a fixed product but a flexible substrate.

The system is several capabilities layered on one core:

1. **The memory / introspection engine (primary).** Retrieval-augmented reasoning over the private corpus: semantic search, pattern-finding, thematic synthesis. The heart.
2. **The agent / action layer.** Scheduled and reactive agents that maintain, curate, sense, and — under strict gating — propose changes to the system itself.
3. **The dynamic agent factory.** The owner can ask the system, in the moment, to spin up a personalized agent for any task — quick recommendation, topic conversation, coding help, financial advice, health/research advice — minted from a base role library, bounded by the Constitution and a hard scope ceiling (§10).
4. **The interface.** A pluggable front-end — messaging and **voice/phone** — so the owner talks to the system by text or by speaking, from a phone or terminal (§12).
5. **The outbound research capability.** Reaches public knowledge through a one-way airlock (§16), never exposing the private corpus.

**Governing security lesson** (applies everywhere): *the model advises; code acts.* No language model in this system holds a shell, raw credentials, or unattended write access to infrastructure. Capability is granted through narrow, audited tools — never through general access. Any design that gives a model broad system reach is a defect.

**Current scope note:** there are **no physical sensors/peripherals yet**. The telemetry tier therefore runs on **system vitals only** at launch; body/health sensor adapters are a deferred, pluggable extension (§8). Design for them; do not block on them.

The owner is a security-focused cloud/DevOps engineer with deep AWS and Terraform expertise and strong Python. Write to that level: precise, minimal, no hand-holding, no unexplained magic.

---

## 2. Design Principles

These shape every choice. When in doubt, optimize for them.

- **Flexible and expandable.** Everything that touches the outside world — interface, sensors, model backends, stores — is a pluggable adapter behind a stable contract. Adding a capability should not require rearchitecting.
- **Scale in agents, not models.** Inference is the scarce resource (§5). Agents are cheap definitions time-sharing a fixed model budget.
- **Thin custom code over heavy frameworks.** Roll your own narrow logic on top of solid OSS primitives. Avoid agent frameworks (LangGraph / CrewAI / AutoGen) — they are ceremony that obscures ownership. You own the loop.
- **Efficient and secure by default.** Prefer the cheapest correct mechanism (deterministic math over a model where it suffices); isolate anything that executes code or touches the network.
- **A stable core makes safe expansion possible.** The Constitution (§4) and the frozen baselines (§15) are immutable human-blessed anchors. They are what let the rest of the system change, spawn agents, and even modify itself without drifting away from its purpose.

---

## 3. Hard Invariants (non-negotiable)

These must hold at every phase. A change that violates any is wrong even if it "works."

1. **The sealed core has zero network egress.** Components that can read the private corpus run with no outbound network. Enforce structurally (separate process/namespace without network), not by convention.
2. **Network and private data never coexist in one component.** Only the bridge and the interface gateway touch the network (§6); neither can read the private corpus. Only de-identified, owner-sanctioned content crosses outward.
3. **The model advises; code acts.** No model holds a shell, raw secrets, or the ability to mutate infrastructure directly. All actions execute through deterministic code or Terraform.
4. **Executed code is sandboxed and powerless.** Any code an agent runs executes in an isolated sandbox with no credentials, no network (unless an explicit scoped grant), and no access to the private vault. Results return as data, never as actions on the system. (§11)
5. **Every self-modification is gated, validated, and reversible.** Propose → human-approve → execute → validate-against-baseline → auto-rollback-on-regression. No step is skippable. (§14)
6. **Every agent inherits the Constitution.** Static or dynamically minted, an agent's outermost frame is `CONSTITUTION.md`. Task-specific instructions nest inside it and may never override it. A minted agent can never exceed the tool scope its base template grants or a pre-declared maximum. (§4, §10)
7. **Consequential advice defers, but is not withheld.** For health, financial, and legal topics the system gives substantive, well-grounded help, flags uncertainty honestly, refuses genuinely dangerous specifics, and defers the *final decision* to the owner and a qualified professional. It informs; it does not pose as the decision-maker. (Replaces the former medical lockout — now governed uniformly by the Constitution.)
8. **Respect the memory ceiling.** Never hold more than two models resident or exceed the usable-RAM budget (§5). The scheduler refuses work that would breach it.
9. **The fixed points are sacred.** The frozen golden baseline (§15) and the Constitution (§4) are never auto-modified by any agent. Only the human changes them, deliberately, logged.
10. **Secrets live outside code.** macOS Keychain and/or environment only; never commit, never let a model read them, never log them.
11. **The interface may transit a third party; the corpus never does.** If a messaging adapter routes through an external service (e.g. WhatsApp), the owner's *interactions* leave the trust boundary even though the corpus does not. This tradeoff must be explicit and opt-in; the private default keeps interactions inside the boundary (§12).
12. **Voice/telephony is bounded, owner-only, and code-dialed.** The system can speak and hold phone conversations, but: a phone call is network egress through a carrier (no airgapped calls), so speech synthesis and recognition run **locally in the sealed core** and only rendered audio crosses the carrier; the telephony adapter may dial **only the owner's pre-registered number(s)** and the LLM never supplies a number (code dials, the model advises); outbound calls are owner-initiated or pre-authorized, never unsolicited; and the human is authenticated on the call (passphrase/callback) before any personalized, privately-derived content is spoken (§12).

---

## 4. The Constitution / Core Directives — the Fixed Point

This is the system's stable behavioral anchor, and it is the same architectural move as the frozen capability baseline (§15) applied to *values and behavior* instead of retrieval quality. Without it, a self-modifying, self-spawning agent system slowly optimizes itself away from its own purpose — value drift, one acceptable step at a time. The Constitution is the immutable reference the whole system measures itself against.

It lives at `CONSTITUTION.md`, is loaded as the outermost context frame of **every** agent (Invariant 6), and is amended **only** by the human (Invariant 9). Build it in Phase 0, before anything inherits it.

**What it encodes** (full text in `CONSTITUTION.md`):
- **Purpose & identity** — what the system is for: a mirror onto the owner's mind, in service of the owner, kept as a sealed sandbox. The north star against which "is this still the thing I'm building" is judged.
- **Inviolable constraints** — the security floor, restated as values the agents hold and cannot argue their way out of: sealed core, model-advises/code-acts, sandboxed execution, no unattended infra change, secrets never read.
- **Behavioral directives** — calibration and honesty (surface uncertainty, never fabricate, especially citations); *mirror, not oracle* (synthesis is the owner's corpus plus model training reflected back, never presented as external truth); deference on consequential decisions; respect for the owner's autonomy; no fostering of over-reliance; prefer surfacing options to issuing directives.
- **Self-evaluation mandate** — every agent checks its output against these directives before returning; the system periodically audits its own behavioral drift against this fixed text (§15).
- **Amendment rule** — the Constitution is the fixed point: no agent may modify it; it is the reference against which all drift, capability and behavioral, is measured.

**Self-evaluation, concretely.** Each agent (including minted ones) runs a lightweight pre-return check: does this output fabricate, overclaim certainty, present a mirror as an oracle, or overstep into posing as a decision-maker on a consequential topic? Cheap to do; deterministic where possible (e.g. verify cited identifiers resolve); a small-model judge only for the subjective cases, A/B'd against a baseline rather than scored cold (§15).

---

## 5. Hardware & Resource Model

**Primary host:** Apple Silicon M2 Max, 32 GB unified memory. Assume ~20–24 GB usable for inference after the OS and working set. Do not design around having more.

This rewrites what "multi-agent" means. **You cannot hold N models. You hold at most two slots:**

- **Slot 1 — pinned, always warm:** a tiny model (≈1–3B, ~1–2 GB at 4-bit). Cheap enough to coexist with everything. Role: router + watchdog only (§9).
- **Slot 2 — single swappable worker:** loads one model at a time, sized to the job's declared tier (fast ~7–8B routine; ~14B synthesis). A stretch ceiling (~32B low-quant) is permitted occasionally **but it evicts the pinned model for its duration** — so the supervisor and the heaviest local synthesis cannot be warm simultaneously. Schedule around this; it is a tradeoff, not a crash.

**Agents are not models.** An agent = a role definition (Constitution + role prompt + task) + a scoped toolset + its own memory, time-sharing the two slots through a durable queue. Agents are cheap; inference is scarce. The system scales in agents. **Nothing is baked into Ollama:** personas and per-call parameters (system prompt, temperature, stop, and `num_ctx`) are injected at **request time via the Ollama API**, never via Modelfile `SYSTEM`/`PARAMETER`, because they are composed, trimmed, and right-sized dynamically (§10, §13). This yields two lifecycles the OS layer owns separately — **agent lifecycle** (many, cheap: the factory + the SQLite registry) and **model lifecycle** (a few weights: pulling/updating + the two-slot loader). The router *decides* (route, tier, window); deterministic code *does* (assemble the prompt, set options, load/swap, call Ollama) — model advises, code acts. Use the base models with their correct built-in chat templates; a custom Modelfile is rarely needed.

**Model-load latency is the cost to design against.** The scheduler groups same-tier jobs back-to-back to minimize swaps (§13).

**Portability:** keep model serving abstract (HTTP to a local server) so the architecture is not Metal-only. A future Linux/discrete-GPU node should join as an additional worker without rearchitecting — and lift the ceiling when it does.

---

## 6. Trust Zones & Network Boundary

The boundary between the core and the networked processes is the **filesystem handoff** (specific directories), not shared memory or shared DB access.

**Zone A — Sealed Core (no network).**
Holds: the private vault (Logseq), the vector store (thought-graph), the telemetry store, private-reasoning models, the librarian/curator/dreaming/matching agents, the agent factory, and the sandbox broker. No outbound network. Communicates outward only by writing **sanitized job specs** into a handoff directory and reading results from a staging directory.

**Zone B — Networked Edge (the only processes that touch the network).** Two narrowly-scoped, containerized processes, each with the private vault unmounted and accepting no inbound connections beyond what its job requires:
- **Bridge** — ships sanitized research specs to AWS and retrieves public corpora (§16). Never reads the private vault.
- **Interface gateway** — relays owner messages between a messaging adapter and the core via a local channel, and returns responses (§12). Never reads the private vault directly; it passes queries to the core and relays answers.

**Zone C — Cloud (AWS).** Encrypted backups and outbound research fetchers (§16). Sees only de-identified topic criteria and public literature. Never receives plaintext private data.

**Data-flow asymmetry (the airlock):** outbound is de-identified topic criteria only; inbound is public content only. The owner's inner life never leaves the walls; fresh external knowledge still gets in. Comment this asymmetry at the boundary so future edits don't erode it. Note: even topic keywords carry intent — keep outbound criteria general.

---

## 7. Technology Stack

Open-source for the plumbing; thin custom logic for orchestration. Hand-roll the ReAct/tool loop and the supervisor.

| Concern | Choice | Rationale |
|---|---|---|
| Model serving | **Ollama** (or `llama.cpp` `llama-server`) | Metal-native, keeps models warm, simple HTTP API, abstracts the worker slot |
| Thought-graph vectors | **LanceDB** | Rust core, embedded, no daemon |
| Telemetry (analytics) | **DuckDB** | Embedded; cheap time-windowed aggregations |
| Job queue / state / gate | **SQLite** (Postgres if outgrown) | Transactional, embedded, durable; the queue is the heartbeat |
| Stream math | **Polars / NumPy** (+ changepoint lib) | Deterministic reactive tier; no model needed |
| Notes source | **Logseq** vault (markdown) | Already the owner's graph |
| Code-exec sandbox | **rootless Podman**, network-off, no-mount, resource/time-limited; **wasmtime + Pyodide** for pure-compute; gVisor/Firecracker as hardening path | Contained execution; efficient warm pool (§11) |
| Interface | **Pluggable adapters** behind one contract; private default = local app over **Tailscale/WireGuard**; optional WhatsApp/Telegram/Signal/Matrix | Owner's choice, privacy-aware (§12) |
| Speech synthesis (TTS) | **Piper** or **Kokoro** (local, fast, CPU-friendly), run in core | On-the-fly voice; only rendered audio crosses the carrier (§12) |
| Speech recognition (STT) | **whisper.cpp / faster-whisper** (local, Apple-Silicon-friendly) | Hear the owner's side locally |
| Telephony | **Programmable-voice provider with media streams** (Twilio/Telnyx/SignalWire) or self-hosted **Asterisk/FreeSWITCH + SIP trunk**, in the edge | Carrier connection only; pipes raw audio to local STT/TTS (§12) |
| Orchestration | **Hand-rolled Python** supervisor + SQLite job table | Owner's strongest language; full ownership; Python-native ML ecosystem |
| Containers | **Podman / Colima** | Network-scoped isolation for edge + sandbox |
| Cloud | **S3, Lambda or Fargate, IAM, KMS**, via **Terraform** | Owner's competency; least-privilege |
| Backups | **restic → S3** | Client-side encryption + dedup |
| Secrets | **macOS Keychain** / env | Owner already uses Keychain-backed auth |

**Default orchestration/agent language: Python.** Performance-critical stream math may later move to Rust/Polars; the queue may later move to Go/River. Build in Python first. Exact model picks, messaging library, and sandbox strength are decision points (§20).

---

## 8. Data Architecture (polyglot persistence)

Different data, different stores, **scoped access per agent** — encoded as an access layer, not honor system. The mood/introspection agents must not have write access to telemetry; the watchdog must not have write access to the vault.

1. **Thought-graph (qualitative).** Logseq vault + LanceDB embeddings. Semantic/associative queries. Each note chunked, embedded, tagged; graph links from Logseq plus vector similarity.
2. **Telemetry (quantitative).** DuckDB time-series. **At launch: system vitals only** — latency, queue depth, model-load time, memory headroom, error rates, cron durations. The system is itself a sensor source. **Body/health sensor adapters are deferred and pluggable**: define the schema and an adapter contract so a wearable can later emit into the same store without rework.
3. **Job/state/gate (transactional).** SQLite: the durable job table, scheduler state, the propose/approve/validate ledger, rollback metadata, and the registry of persisted minted agents (§10).

**Raw is sacred; derived is regenerable.** Store every input — notes, poems, conversations — as an **immutable, content-addressed hard copy** (hash the raw; this also gives dedup for free). That verbatim original is the source of truth and is never rewritten or summarized away. Layer **derived representations** on top, all regenerable from the raw: chunk embeddings (retrieval), a summary/abstraction (cheap overview and context-budget headroom), extracted entities, inferred links. If you change an embedding model or summarization strategy, reprocess from the raw copies — abstraction is never allowed to lose information. Pull the summary or top-k chunks into context, not the whole transcript (the same lever the context budgeter uses, §13).

**Explicit vs interpreted — separate, provenance-marked layers.** The *explicit* layer is what the owner authored: note text, the tags they applied, the `[[links]]` they drew. Ground truth, immutable. The *interpreted* layer is what the system inferred: similarity edges, extracted entities, inferred themes and moods, derived connections. Per *mirror, not oracle* (§4), interpreted data is marked as derived and kept separable, so a query can always distinguish "the owner wrote this" from "the system thinks this" and can weight or filter by provenance. The **curator (§9) operates on the interpreted layer and must never silently rewrite the explicit layer.** Explicit ground truth is part of what the frozen anchors protect; interpreted data is the mutable, regenerable derivative.

**Graph seeds.** Don't pre-build a heavy ontology. Seed the thought-graph from the owner's existing **Logseq pages, tags, and explicit links** — their hand-made skeleton (the explicit layer) — plus a light set of node-type and edge-type primitives (source vs derived node; authored vs inferred edge). Structure grows from ingestion and curation rather than being imposed up front.

Provide migrations, a schema doc, and keep the three stores independently replaceable.

---

## 9. Agent Roles & Tiers

**The decisive axis is latency class, and it decides whether a role is even a model.**

**Reactive tier (live input) — mostly NOT models.** Continuous, cheap, deterministic: rolling windows, EWMA, z-scores, changepoint detection over DuckDB/Polars. Watches system (and later sensor) streams; **escalates to a model only when a measurement crosses a threshold.** More correct than a model for the task, and it keeps the single inference slot free.

**Cron / cognitive tier — earns the big model.** Heavy thinking run when the owner is idle: curation, dreaming, medical/research synthesis. Never concurrent with foreground use.

Roles are **templates** the factory (§10) instantiates; the persistent ones below are built in directly.

- **Router + Watchdog (pinned tiny model, Slot 1).** Classifies incoming work → assigns role + tier (including routing for **context fit** and right-sizing each role's loaded context window — see §13); reads system/body metrics → raises flags. *Not an operator* — it proposes, never changes infrastructure (§14).
- **Ingest analyzer (write path, fast/small model + deterministic steps).** Dedup, chunk, embed, tag — fast and cheap. The storage engine's write path.
- **Curator (background compaction, cron, synthesis tier).** Merge near-duplicates, prune dead weight, restructure the graph, **flag contradictions**. Optimized for quality, not speed.
- **Librarian (core query agent, RAG).** Semantic retrieval + grounded reasoning over the thought-graph. The owner's primary interface to their own mind. Also generates the **de-identified criteria** the research fetchers consume (§16).
- **Dreaming agent (cron, synthesis tier).** Clusters embeddings, tracks themes over time, generates synthesis. *Mirror, not oracle* — never presents output as external truth (§4).

**Base role library for the factory** (each a template — prompt fragment + default tier + tool scope + code-exec profile + network profile): personal assistant, coder, financial advisor, health/research advisor, writer/editor, general conversation, data analyst. Health/research is now an ordinary advisory role governed by the Constitution's deference directive (Invariant 7) — substantive and grounded, with a professional-deferral floor, not a special lockout.

Each role declares its **model tier** so the scheduler can group same-tier jobs.

---

## 10. Dynamic Agent Factory

The owner can ask, in the moment — "give me a quick recommendation," "let's talk about X," "be my coder for this," "act as a financial advisor" — and the system mints a personalized agent for the task. This is a first-class capability, and it must not become a backdoor around the security model.

**Minting.** The factory composes an agent as nested frames, outermost-first:
1. `CONSTITUTION.md` (immutable, Invariant 6)
2. the chosen **base role template** (§9) — prompt fragment, default tier, tool scope, code-exec profile, network profile
3. the owner's **task-specific instructions** (innermost; may never override the outer frames)

It then resolves the tool scope, assigns the model tier, and returns a session.

**Scope ceiling (security).** A minted agent can **never** exceed the tool scope its base template grants, can **never** be granted scope beyond a pre-declared maximum, and always inherits the Constitution. The factory cannot mint an agent with raw shell, credentials, or core-bypassing network. If a task appears to need privileged capability, the factory **routes to the human gate** (§14) instead of minting a privileged agent.

**Lifecycle.** Ephemeral by default — spun up, used, discarded. The owner may **promote** a useful agent to a persistent named agent with its own memory, recorded in the SQLite registry (§8).

**Self-evaluation.** Every minted agent runs the Constitution pre-return check (§4) before answering.

---

## 11. Sandboxed Code Execution

Agents need to run code — the coder role tests, the analyst computes, the financial role calculates. This is precisely the capability whose careless version made OpenClaw dangerous, so it is contained: **same power, no reach.**

**Execution substrate (default):** ephemeral **rootless Podman** containers — no network, no vault mount, read-only base + scratch tmpfs, dropped capabilities, seccomp profile, non-root user, CPU/memory/pids limits, and a wall-clock timeout. Keep a **warm pool** to avoid per-execution cold start; cap concurrency to respect the memory ceiling (§5). Roll a thin execution-broker around this.

**Tighter option for pure computation:** **wasmtime + Pyodide** (or a WASM runtime) — strongest in-process isolation, no syscalls; use where library needs are modest. **Hardening upgrade path:** gVisor (`runsc`) or a Firecracker microVM for kernel-level isolation.

**The invariant (Invariant 4):** executed code has no credentials, no network unless an explicit scoped grant, and no access to the private vault. Results return as **data**, never as actions on the system. Network grants, if ever needed, are per-execution, narrowly scoped, and logged.

---

## 12. Interface Layer

A pluggable messaging front-end so the owner talks to the system from a phone or terminal. Implemented as adapters behind a single `InterfaceAdapter` contract (receive message, send message, handle attachments), run in the **interface gateway** (Zone B) which relays to the sealed core. The core never speaks to a messaging service directly.

**Privacy posture — read this and decide consciously (Invariant 11).** WhatsApp, Telegram, and Signal all transit a third party, so your *interactions* (queries and the system's answers) leave the trust boundary even though the corpus never does. For a sealed mind palace, the privacy-consistent default is a **self-hosted interface**: a local web/TUI app reachable over **Tailscale/WireGuard**, or a self-hosted **Matrix** homeserver. Build that as the **primary** adapter. Provide a **WhatsApp adapter** the owner can enable knowingly for convenience (note also its ToS/stability caveats for unofficial libraries). The adapter pattern makes this the owner's call, switchable later.

**Voice & telephony (an adapter, not a new subsystem).** The owner can talk to the assistant by phone — e.g. for quick recommendations while out — implemented as a **voice adapter** in the interface gateway (Zone B), exactly like the messaging adapters. Three properties make it fit the architecture:
- **Local voice, carried audio.** TTS (Piper/Kokoro) and STT (whisper.cpp) run **inside the sealed core**; the edge adapter handles only the carrier connection (a provider media stream or SIP) and pipes raw audio ↔ core. A phone call is network egress through a carrier by nature, so the *conversation* transits a third party (Invariant 11's tradeoff, in voice form) — but reasoning, synthesis, and the corpus never leave the walls; only rendered audio does.
- **Owner-only, code-dialed, authenticated.** The adapter dials only the owner's pre-registered number(s); the LLM never supplies a number; calls are owner-initiated or pre-authorized; a passphrase or callback-to-known-number confirms the human before privately-derived content is spoken (Invariant 12). The clean pattern: the owner taps/texts "call me about X," the system calls the known number back, confirms, and converses. This bounding is also what keeps voice from becoming a generalized autonomous-calling capability.
- **A live call is the strongest foreground state** (see §13 conversation mode): it claims the worker slot for a *fast* conversational model and suspends batch work. Expect snappy short turns, not zero latency — stream the TTS so speech begins as tokens generate, and keep spoken answers concise.

---

## 13. The Scheduler (activity modulation)

The system's heartbeat: not models fanning out in parallel, but **one worker slot time-shared under a supervisor** that knows the difference between urgent, deferrable, and wait-until-he's-asleep.

- **Tier-aware grouping:** batch same-tier jobs to minimize model-load swaps.
- **Preemption:** reactive-tier escalations preempt batch work.
- **Foreground-use check:** heavy synthesis must not fire while the owner actively uses the machine. Detect presence (active session / recent input) and gate.
- **Conversation mode (strongest foreground):** while a voice call is active, claim the worker slot for a fast conversational model (not the 14B synthesis tier — trade depth for latency), run STT and TTS as auxiliaries alongside it, and suspend curation/dreaming/research synthesis until the call ends. The pinned tiny model still routes. RAM fits (fast LLM + small STT + tiny TTS within budget); the real constraint is latency, so favor concise streamed turns.
- **Trough-filling:** dreaming, curation, pruning, research synthesis run on cron when idle.
- **Ceiling enforcement:** refuse work that would breach the two-slot / RAM budget (Invariant 8); account for pinned-model eviction when the stretch-ceiling model is requested.

**Context-budget management (owned here).** Local models have differing, often modest context windows, so every agent invocation is assembled to fit the active model's window with headroom for the reply. A **deterministic budgeter** (a tokenizer + assembler — code, not a model) counts tokens and composes each context from its parts in priority order: Constitution frame → role/task → retrieved RAG chunks (retrieval depth is the primary lever) → conversation history → tool/code outputs. When it won't fit, apply in order: tighten retrieval top-k, compact conversation history (sliding window or rolling summary), truncate/summarize large tool outputs, and — if still over — escalate to a larger-window model tier (a routing decision the OS agent makes) rather than silently dropping context. **Track usage** per agent/session/job in the telemetry store so budgets, overflows, and summarization events are visible (and feed §15's vitals). Because the Constitution loads into *every* window, its tightness is context-budget discipline, not just style — keep it lean.

**Right-size the window per (model, role), not just the content.** Beyond fitting content to a fixed window, the OS agent sets how large a context window to *allocate* when loading a model for a role — the KV-cache / `num_ctx` budget — because a larger window costs RAM and latency. The router needs almost none; the latency-sensitive conversational role wants a small one; synthesis over the corpus wants a large one. Default each role to a window sized from its tracked usage (≈p95 + headroom), not the model's max, to save memory and speed. Treat the per-role window allocation as a tunable the OS agent may optimize over time and as a candidate safe-lever (§14). In Ollama, changing `num_ctx` generally forces a model reload, so treat the window as a per-role **load-time** setting and batch same-window jobs alongside same-tier ones — it is not a free per-call knob.

Start with **rules**; graduate the "what runs when" decision to the tiny router model later.

---

## 14. Self-Modification & Safety Loop

The owner wants the system to optimize its own infrastructure *with permission*. Earn the safety back by splitting **propose from execute**, and **judge from propose** (§15).

```
propose  →  approve  →  execute  →  validate  →  roll back (if regression)
(model)    (human)     (code/TF)   (baselines) (mechanical)
```

- **Propose:** an agent writes a *proposed* change — diff, plan, parameter — into the SQLite gate ledger. Nothing runs yet.
- **Approve:** the human approves (exception below).
- **Execute:** applied by deterministic code or Terraform. **Never by a model holding a shell.**
- **Validate:** tie every approved change to its pre-change window, post-change window, the golden-set diff, **and** a Constitution-conformance check (§15).
- **Roll back:** if telemetry breaches the envelope, the golden set regresses, or behavior drifts from the Constitution, the change reverts itself. Keep-or-roll-back is **mechanical**.

**Safe levers (unattended):** a small, pre-declared set of low-risk knobs the tiny model may touch without approval — defer the dreaming job, lower an embedding batch size, right-size a role's context-window allocation within set bounds. Everything else routes through the human gate. Keep the set explicit and auditable.

---

## 15. Testing & Baselines — Two Fixed Points

Approving a change is not knowing it helped. **A tester is only a tester if it has a fixed reference.** This system has **two** fixed references, for two kinds of drift.

**Split what's tested:**
- **System vitals (quantitative):** the reactive-tier math aimed *inward*. The EWMA/z-score/changepoint code now watches the queue. No model needed.
- **Cognitive quality (capability):** a **frozen golden set** — fixed queries with known-good expected retrievals — diffed on every relevant change. Deterministic metrics: recall@k, set overlap, cosine distance.
- **Behavioral conformance (values):** does output still conform to the **Constitution** (§4) — no fabrication, no oracle-posing, appropriate deference. Deterministic where possible; small-model judge only for subjective cases, **A/B'd against a baseline snapshot**, never scored cold.

**Judge ≠ proposer.** The agent that made a change must not grade it (same model = same blind spots).

**Two baselines defeat the boiling-frog problem.** Each approved change quietly re-baselines, so slow degradation across many changes never trips any single before/after check. So:
1. **Rolling baseline** — adapts; catches *acute* weirdness right after a change ("did this break something now?").
2. **Frozen anchors** — the **golden set** (capability) and the **Constitution** (behavior), blessed by hand, updated only on purpose (Invariant 9); catch *drift from known-good over time* ("have we wandered from where we started?").

Without the fixed anchors, every individual check can pass while the system degrades smoothly forever — in capability *and* in values.

---

## 16. The Cloud Airlock — AWS (Zone C)

> **Generalized by [`dn-external-grounding` §2.4](design-notes/external-grounding.md) (ratified 2026-07-13).**
> This machinery is **corpus-agnostic literature grounding**, not medical-only: the medical
> case (Europe PMC / PubMed, keeping Invariant 7) is one use; design-grounding (arXiv, OpenAlex)
> is another — one machinery, one airlock. The **live driver** that runs the dormant
> `criteria → emit → collect → rank → surface` chain (foreground Ambassador + background trough,
> transient) is §2.5 (built by bp-028). The body below remains accurate for the medical case.

All AWS via Terraform, least-privilege IAM, owner's stack conventions.

**a) Outbound research fetchers.**
1. Core librarian generates **de-identified criteria** → handoff dir.
2. Bridge PUTs to S3 `requests/` (outbound only).
3. A Lambda (or Fargate for heavier jobs) triggers, performs **broad public aggregation**, writes a public-literature corpus to S3 `results/`.
4. Bridge polls/GETs → staging dir → core ingests and ranks **inside the walls**.

**Sources:** PubMed E-utilities, Europe PMC (open-access full text), OpenAlex and/or Semantic Scholar, ClinicalTrials.gov, medRxiv/bioRxiv. **Bias toward systematic reviews, meta-analyses, Cochrane; flag preprints as not-yet-vetted.**

**Dumb outside / smart inside:** fetched literature is public, so it may be summarized by a larger *cloud-hosted* model out there at zero privacy cost; only personalization/ranking against private notes stays on the local small model — sidestepping the 32 GB ceiling where it costs nothing.

**IAM:** scope the fetcher to web egress + the two prefixes, nothing else.

**Evidence good-practice (per the Constitution's honesty directive):** verify every cited identifier resolves; never present a population statistic as individualized; surface evidence quality, not just conclusions. The research advisor informs the owner; final health decisions defer to a clinician (Invariant 7).

**b) Encrypted backups.** restic → S3, client-side encrypted + deduplicated so AWS never sees plaintext; SSE-KMS on the bucket for defense in depth; scheduled. Primary host is macOS (APFS) — back up data directories directly with restic (it handles encryption/dedup); APFS snapshots optional for read consistency. Do **not** assume btrfs here.

---

## 17. Repository Structure (target)

```
mind-palace/
  CLAUDE.md            # operational rules (loaded every session)
  CONSTITUTION.md      # the fixed-point directives every agent inherits
  CONVENTIONS.md       # engineering + security practice
  docs/
    BUILD-SPEC.md      # this document
    schema.md
    runbook.md
  core/                # Zone A — sealed, no network
    librarian/  curator/  dreaming/  ingest/  matching/
    factory/           # dynamic agent factory + base role library
    sandbox/           # code-execution broker + warm pool
    stores/            # LanceDB + DuckDB access layers, scoped
  edge/                # Zone B — networked, containerized
    bridge/            # research airlock client
    interface/         # gateway + adapters (local/Tailscale, WhatsApp, ...)
  cloud/               # Zone C — Terraform + Lambda/Fargate fetcher
    terraform/  fetcher/
  agents/              # persistent role definitions: prompt + scope + memory
  scheduler/           # supervisor, tier scheduling, foreground check, queue, context budgeter
  ops/                 # propose/approve/execute gate, safe levers, rollback
  eval/                # golden sets, deterministic metrics, baselines, drift
  config/              # non-secret config; secrets via Keychain/env only
```

Keep Zone A free of any import path that can reach the network.

---

## 18. Build Plan — Phased (with verification gates)

Build in order. **Verify each phase before advancing, and checkpoint with the human at every boundary.** The most dangerous capability (self-modification) comes last, after its safety scaffolding exists.

- **Phase 0 — Foundations, invariants & Constitution.** Repo scaffold, config, the two on-laptop trust zones, model server with two-slot discipline, vitals emitter into DuckDB, **and the Constitution authored + the inheritance mechanism stub**. *Verify:* model responds; vitals flow; core has no egress (test it); a trivial agent inherits the Constitution.
- **Phase 1 — Stores & ingest.** LanceDB, Logseq ingestion, ingest analyzer (chunk/embed/tag/dedup), telemetry store. *Verify:* notes indexed; semantic search sane; dedup works.
- **Phase 2 — Librarian + golden set + behavioral check (together).** Core RAG agent, the eval harness golden set with deterministic metrics, and the Constitution pre-return check. *Verify:* golden-set queries pass; metrics computed; the behavioral check fires.
- **Phase 3 — Scheduler + tiers + two-slot + context budget.** Durable job table, supervisor loop, tier grouping, swap minimization, foreground check, preemption, pinned router/watchdog, and the **deterministic context budgeter** (token counting, priority assembly, history compaction, overflow→escalate). *Verify:* jobs scheduled by tier; swaps minimized; foreground check blocks heavy jobs; ceiling enforced; contexts always fit the active model's window and usage is tracked.
- **Phase 4 — Sandboxed code execution.** Execution broker, isolated container profile, warm pool, optional WASM path. *Verify:* code runs isolated — no network, no creds, no vault; limits + timeout enforced; warm pool works.
- **Phase 5 — Dynamic agent factory + base role library.** Minting from templates, Constitution inheritance, scope ceiling, ephemeral/persist, self-evaluation, privileged-request routing to gate. *Verify:* minting works; a generated agent cannot exceed scope; inherits the Constitution; self-evaluates; privileged tasks route to the human.
- **Phase 6 — Interface layer.** Gateway + the private local/Tailscale adapter (primary); optional WhatsApp adapter; relay to core. *Verify:* messages round-trip; core never touches the messaging service directly; private default works.
- **Phase 6b — Voice & telephony adapter (optional extension).** Local TTS (Piper/Kokoro) + STT (whisper.cpp) in core; the voice adapter in the edge over a programmable-voice provider; conversation mode in the scheduler; owner-only dialing with callback + passphrase auth. *Verify:* a call round-trips with local TTS/STT and carrier-audio only; the adapter cannot dial any number but the registered one; conversation mode suspends batch work and restores it after; the human is authenticated before personalized content is spoken.
- **Phase 7 — Curator + dreaming.** Background compaction and dreaming synthesis. *Verify:* run on cron in troughs only; coherent output; never during foreground use.
- **Phase 8 — The airlock.** Terraform for `requests/`+`results/`, the fetcher, least-privilege IAM; the containerized bridge; the research flow. *Verify:* sanitized request → public corpus → ranked inside core; core never touched network; IAM tight.
- **Phase 9 — Backups.** restic → S3 + KMS, scheduled. *Verify:* encrypted backup + restore round-trips; AWS sees no plaintext.
- **Phase 10 — Self-modification loop (last).** Propose/approve/execute gate, safe-levers set, validate against the rolling baseline + the frozen golden set + the Constitution, automatic rollback. *Verify:* a proposed change traverses the gate; a deliberately-bad change auto-rolls-back; the frozen anchors catch simulated slow drift the rolling baseline misses — in both capability and behavior.

---

## 19. Build Discipline (how to work)

- **Incremental and verifiable.** Small, tested steps. Write tests as you build.
- **Checkpoint at phase boundaries.** Summarize what was built and verified; wait for the human before advancing.
- **Ask, don't guess, on flagged decisions** (§20). For unflagged choices, pick a reasonable default and state it inline.
- **Invariants and Constitution first.** If a feature can't be built without violating §3 or §4, stop and surface it.
- **Sandbox and secrets discipline.** Executed code is powerless (Invariant 4); secrets via Keychain/env only; never commit, never let a model read them, never log them.
- **Everything in AWS is Terraform.** No click-ops.
- **Comment the *why* at trust boundaries** — the airlock asymmetry, the propose/execute split, the scope ceiling — so future edits don't quietly erode them.
- **One phase per build session.** Build a single phase, verify against its gate, append a terse entry to `docs/PROGRESS.md`, update the Current-phase marker in `CLAUDE.md`, then stop. A fresh session resumes from `PROGRESS.md` rather than replaying history — this keeps the builder within its own context budget.

---

## 20. Open Decisions for the Human (resolve before or during Phase 0)

State your choice; sensible defaults noted.

1. **Exact model picks per slot/tier.** Default: class-based (tiny ~1–3B pinned; ~7–8B routine; ~14B synthesis; optional ~32B stretch). Pin exact current best-in-class for 32 GB on request.
2. **Queue implementation.** Default: hand-rolled Python + SQLite. Alternative: River (Go, Postgres).
3. **Interface adapter(s) to ship first.** Default: private local app over Tailscale (primary); WhatsApp as an opt-in convenience adapter. Confirm whether WhatsApp is wanted at launch given the third-party-transit tradeoff (Invariant 11).
4. **Messaging library** if WhatsApp is enabled (unofficial library vs Business Cloud API) — note ToS/stability tradeoffs.
5. **Sandbox strength.** Default: rootless Podman (network-off, no-mount, limited) + WASM for pure compute. Upgrade path: gVisor/Firecracker.
6. **Sensors/peripherals:** none at launch (system vitals only). Confirm; the body-telemetry adapter contract is built but dormant.
7. **AWS account / region / existing Terraform state** to slot into.
8. **Logseq vault path** and sub-scoping (which graphs are in-scope for ingestion).
9. **Fetcher compute:** Lambda (light) vs Fargate (heavy) — or both by job size.
10. **Cloud summarization model** for public literature (the "big remote" half), if used.
11. **Voice/telephony** (if enabling Phase 6b): whether to enable voice at all; the owner's pre-registered number(s); programmable-voice provider (Twilio/Telnyx/SignalWire) vs self-hosted Asterisk+SIP; exact local TTS and STT models (pin current best-in-class on request, as with the LLMs).

---

*End of spec. Begin at Phase 0 only after the human confirms §20 or explicitly defers individual items. Load `CLAUDE.md`, `CONSTITUTION.md`, and `CONVENTIONS.md` alongside this document.*
