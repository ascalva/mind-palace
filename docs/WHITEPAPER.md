# The Mind Palace — A White Paper
### A sealed, offline-first personal AI: a second brain that reflects a mind back to itself

**Version 1.0 (living document) · 2026-06-26**
This document records the full scope, philosophy, design, technical decisions, security model,
and rebuild path of the system. It is maintained alongside the code; sections marked *(built)*
exist and are tested as of Phase 7. It is meant to be sufficient to rebuild the system from
nothing.

---

## 0. Abstract
The Mind Palace is a single-user, self-hosted AI that indexes a person's *authored* corpus
(notes, poems, journals) and reflects patterns back across it over time — a "second brain."
It runs offline on one Apple-Silicon laptop, with a small set of local models, a sealed core
that never touches the network, and a deliberately bounded path for outward action. Its
governing discipline is that *the model advises and code acts*; its governing risk is that a
system meant to mirror a mind can instead distort or flatter it. Every architectural choice
serves one of those two facts.

---

## 1. Inspiration & philosophy (the DNA)
The system began as a set of musings, recorded here verbatim because they are the design's
reason for being, not decoration. The owner wanted:

> "a birdseye view into my own thoughts… the only knowledge base of your own brain… a mind
> palace, a sandbox." — "can a spiritual system emerge?" — "a graph observing itself, recursive
> in nature, over time." — "is that what dreams are made of?" — "entropy = time… is that
> consciousness?" — "madness… a closed loop that would make a computer stack overflow." — "a
> guardian angel looking out for me." — "a living organism that needs to be properly nurtured
> and protected, like a brain… a system greater than the sum of its parts."

These are held under one discipline, stated once and enforced everywhere: **the poetry is the
inspiration; it does not go in the logs.** A metaphor may motivate a subsystem (dreaming as
deferred background sense-making; recursion-decay as the taming of rumination), but the
subsystem's outputs must stand on evidence, not on the beauty of the metaphor. The white paper
keeps both — the inspiration and the engineering — and never confuses them.

The core philosophical commitment, which is also an engineering one: a second brain must be a
**mirror, not an oracle.** Its syntheses are the owner's own material plus a model's training,
reflected back — a lens that surfaces patterns the owner can accept or reject, never a verdict,
never a source of external truth. This single commitment, taken seriously, generates the
provenance model, the firewall, the grounding checks, and the recursion limits below.

---

## 2. Design principles
1. **The model advises; code acts.** No model holds a shell, raw credentials, or unattended
   power to mutate state. Capability is a narrow handle code grants, never a flag a model is
   given.
2. **The sealed core has zero network egress.** Components that can read the private corpus
   cannot reach the network. Enforced structurally, not by convention.
3. **Mirror, not oracle.** Inference is marked as inference; it never masquerades as the
   owner's ground truth.
4. **Provenance is first-class.** Every datum carries where it came from; reads are scoped by
   provenance; the authored mirror and observed exhaust are separate pools (§6).
5. **Fixed points make change safe.** Human-blessed immutable anchors — the Constitution
   (values) and the frozen golden set (capability) — are what let the rest grow, spawn agents,
   and self-modify without drifting. Remove the anchor and the system degrades smoothly while
   every check passes.
6. **Scale in agents, not models.** Inference is the scarce resource; agents are cheap config
   time-sharing a tiny fixed model budget.
7. **Deterministic floor.** Cheap math does the work a model isn't needed for; the model is
   earned only where judgment is genuinely required.

---

## 3. Architecture overview
**Trust zones.** Zone A (sealed core, no network): corpus, stores, local models, the
introspective agents. Zone B (networked edge, containerized): the only processes that touch the
network — the bridge (research airlock) and the interface gateway. Zone C (cloud, AWS):
encrypted backups and outbound research fetchers, seeing only de-identified criteria and public
data. Core↔edge communicate by **filesystem handoff, never shared imports** — the structural
form of "network and private data never share a component." *(built: core/edge split, egress
guard, handoff interface)*

**Resource model.** One Apple-Silicon laptop, 32 GB unified memory, ~24 GB usable ceiling. Not
N models — **two slots**: a pinned tiny model (router/watchdog, always warm) and one swappable
worker (routine / synthesis / stretch tiers). Agents are config (Constitution + role + task +
scope + memory) time-sharing the slots through a durable queue. *(built: TwoSlotLoader,
memory-ceiling accounting, refuses breaching loads before any model call)*

**Polyglot stores.** LanceDB (thought-graph vectors), DuckDB (telemetry/time-series; system
vitals now, sensors dormant), SQLite (job queue, gate ledger, agent registry, derived
interpreted artifacts). Each independently replaceable; access scoped in code as
object-capability (a writer handle has no read method). *(built)*

**Nothing is baked into Ollama.** Personas and parameters (system prompt, temperature,
`num_ctx`) are injected at request time, never via Modelfile; the router decides routing/tier/
window, deterministic code drives Ollama. Two lifecycles: agents (many, runtime config) and
models (a few weights). *(built)*

---

## 4. Subsystems
- **Ingest** *(built)* — a content-addressed **immutable raw store** (sha256 → verbatim bytes;
  "raw is sacred") + regenerable derived layer (chunks, embeddings). Logseq/markdown parser;
  deterministic chunker. Re-embedding is a config change, never a loss, because raw is kept.
- **Librarian** *(built)* — the RAG agent over the AUTHORED mirror; frames Constitution-first
  with retrieved notes as the only citable evidence; self-checks grounding before answering.
- **Curator** *(built)* — graph health on the *interpreted* layer: flags near-duplicate merge
  *candidates*, prune candidates (orphaned derived rows), and contradictions (deferred judge
  seam). **Never rewrites authored ground truth** — applying a merge is the gated loop's job.
- **Dreamer** *(built, expanding)* — deferred background synthesis: deterministic clustering of
  the authored mirror → per-theme grounded synthesis → stored as `interpreted` dreams. The R&D
  track (§8) generalizes this into a panel of interpreters with evidence-based adjudication.
- **Scheduler** *(built)* — the supervisor + durable SQLite queue; tier grouping + swap
  minimization; foreground gate (heavy work never runs while the owner is present); cooperative
  run-to-completion / checkpointed scheduling (not preemptive time-slicing — the model slot is
  the serial resource; model-load is the cost to avoid).
- **Agent factory** *(built)* — mints agents from role templates; the Constitution is the
  immutable outermost frame; a minted agent can never exceed its template's scope or a
  pre-declared max; privileged requests route to the human gate.
- **Sandbox** *(built)* — code an agent runs is powerless: rootless container, no network, no
  vault, resource/time limits; returns data, never actions.
- **Interface** *(built)* — pluggable adapters behind one contract; private local/Tailscale
  default; third-party adapters (WhatsApp) carry an explicit `transits_third_party` flag and
  are opt-in. The core never speaks to a messaging service directly.
- **Airlock** *(next, Phase 8)* — outbound research: de-identified criteria out to S3, public
  literature back, ranked inside the walls; the bridge never reads the vault.
- **Self-modification loop** *(Phase 10)* — propose → human-approve → code-executes → validate
  against baselines → auto-rollback. The last and most gated capability.
- **Eval / baselines** *(built)* — a frozen golden set (synthetic, committable, human-blessed)
  + deterministic metrics (recall@k, set overlap, cosine distance); the behavioral self-check
  (grounding authoritative now; subjective judge deferred, never faked).

---

## 5. The flow of a query (worked)
1. A message arrives via an interface adapter (Zone B) → written as a sanitized request to the
   filesystem handoff.
2. The core inbox (Zone A, no `import edge`) reads it, dispatches to the librarian/factory.
3. The router classifies → role + tier + context window. Deterministic code assembles the
   context in priority order: **Constitution → role/skills → retrieved evidence → history →
   query**, trimmed by the budgeter to fit the window.
4. The worker model generates an answer grounded in the retrieved authored notes.
5. The self-check verifies every cited note resolves to a retrieved source (fabricated citation
   = FAIL); subjective directives are deferred to the judge seam.
6. The answer is written back to the handoff; the gateway relays it to the adapter.
No model touched the network; no model held a credential; the corpus never left Zone A.

---

## 6. Provenance model (the firewall)
Data is classed on a spectrum, and reads are scoped by class:
- `authored-solo` — the owner wrote it alone (notes, poems, photos). Feeds the mirror.
- `authored-dialogue` — the owner wrote it in dialogue (Claude conversations, sent messages).
  Feeds the mirror, duet-tagged so the dreamer doesn't mistake a conversation's shape for the
  solo mind.
- `curated` — the owner selected/annotated *others'* words (Goodreads highlights). Interest
  signal, not the owner's voice.
- `observed` — behavioral exhaust from third-party systems (analytics, music, sensors,
  received-message content). **Assistant tier only; never the mirror, never the baselines.**
- `interpreted` — the system's own inferences (dreams, curator findings). Marked derived;
  **structurally cannot be authored** (the derived store has no provenance parameter); never
  promoted except by a deliberate human act.

**The firewall:** the introspective mirror reads only authored classes; the assistant may read
everything. Observed exhaust feeding the mirror would contaminate it (algorithmic bias
reflected back as the owner's psyche) — a silent failure the firewall exists to prevent.
Cross-source insight is an assistant-tier read, marked interpreted, never a mirror dream.

---

## 7. Security model
- **Sealing** *(built)* — a fail-closed in-process egress guard permits only loopback (the
  Ollama channel) + AF_UNIX; OS-level isolation (pf/netns) is the deployment-hardening layer
  before any networked phase. The guard is installed in core, never in edge.
- **Object-capability** *(built)* — scope is the *set of handles an agent holds*, not a flag it
  is granted; out-of-scope is *unreachable*, not "checked then refused." A writer handle has no
  read method. This is the precedent for all tool capability.
- **Skills vs scope** — a skill's text grants *context*; the scope ceiling grants *capability*;
  the two are checked by different subsystems at different times. A skill can only activate a
  tool already in the role's scope. Loading a "deploy" skill into an unscoped agent yields one
  that *knows about* deploying and *cannot do it*.
- **Secrets & keys** — Keychain/Secure Enclave (local, no network) for local secrets; a sealed
  core **cannot call KMS** (that's network), so off-machine keys are unwrapped by an edge-side
  broker that hands the core only what it needs. `get_secret` reads env/Keychain only — no
  secrets in the repo. *(built: get_secret seam)*
- **Encryption posture** — FileVault for at-rest (transparent, no per-access overhead);
  hashes/signatures for *integrity and provenance* (the raw store is content-addressed);
  TLS/Tailscale in-flight; restic (client-side encrypted) for backups. App-level field
  encryption is reserved for data that leaves the machine — its marginal benefit locally is low
  against FileVault.
- **Outward action** — anything that sends, books, pays, or posts is a gated executable skill:
  propose → human-approve → code-acts. No agent holds live credentials. This is the discipline
  that separates a guardian assistant from an over-credentialed daemon.

---

## 8. The dream / interpretation engine (R&D track, flag OFF)
The dreamer is the system's subconscious — deferred background sense-making that maintains the
graph and produces *ranked hypotheses* about the owner's mind. It is the highest-risk layer
because it is the one place the system reasons over its own outputs. Three rules tame it:
1. **Grounding terminates in authored evidence**, every generation. Prior dreams are
   scaffolding, never evidence; the citation chain cannot loop within `interpreted`.
2. **Confidence decays with interpretation-depth**, never compounds — correct recursion
   compounds skepticism. (The taming of the "stack overflow of a mind thinking only about
   itself.")
3. **Confidence (evidence) and utility (usage) are separate axes** — utility decides what to
   surface; grounding decides what to believe; collapsing them makes the mirror a flatterer.
Interpreters specialize by **method** (same corpus, different algorithms, adjudicated by
evidence). Source-specialists are a *different layer* (ingest/curation) that feed
provenance-appropriate pools — never one shared graph. Consensus is a confidence signal, not a
decision mechanism; the adjudicator decides on grounding. The whole process is instrumented:
drift signatures (dreams-citing-dreams, utility-up/grounding-down, confidence-up-with-depth)
are alarmed against the authored floor. See `dream-phase-rnd-charter.md` and its two sub-notes.

---

## 9. Self-improvement & alignment
Two human-blessed fixed points anchor a system that can change itself:
- the **Constitution** — a small immutable *prime-directive kernel* + a *belief system* derived
  from and bounded by it (the belief layer may evolve; the kernel effectively never does);
- the **frozen golden set** — capability ground truth.
Every self-modification is gated, validated against *both* anchors, and reversible. **Drift is
measured, not assumed:** the rolling baseline catches acute breakage; the frozen anchors catch
slow drift (the boiling-frog problem). The Phase-11 dashboard plots golden-set + conformance
scores over time against the anchors — "some drift is OK; deterioration is not" becomes a
visible curve with a tolerance band and a rollback trigger. The system is a living thing that is
*nurtured by being watched*, not by being trusted.

---

## 10. Key structures & pseudo-code (rebuild kernel)
```
# Provenance — the firewall as a type
Provenance ∈ {AUTHORED_SOLO, AUTHORED_DIALOGUE, CURATED, OBSERVED, INTERPRETED}
MIRROR_READABLE = {AUTHORED_SOLO, AUTHORED_DIALOGUE}   # the introspective dreamer's input set

# Two-slot loader — the ceiling is structural
load(model, tier):
    if tier == STRETCH: evict(pinned)
    if resident_bytes + size(model) > CEILING: raise CeilingExceeded   # BEFORE any Ollama call
    ensure_warm(model)

# Context assembly — priority order, fitted to the window
frame_context(role, skills, evidence, history, query, window):
    frames = [CONSTITUTION, role, *skills, *evidence, *history, query]   # Constitution outermost
    while tokens(frames) > window - reply_headroom:
        trim_in_order(evidence_topk → compact(history) → truncate(tool_out))  # never the Constitution
    return frames

# The grounding self-check — what keeps the mirror honest
self_check(answer, retrieved):
    for cite in answer.citations:
        if cite not in retrieved: yield FAIL("fabricated citation")     # deterministic, always on
    for directive in SUBJECTIVE: yield DEFERRED(directive)              # judge seam, never faked

# A dream — grounded, interpreted-only, never promoted
dream(mirror):                      # mirror = vectorstore.all_rows(MIRROR_READABLE)
    clusters = deterministic_cluster(mirror)            # NumPy, model-free, reproducible
    for c in clusters[:MAX]:
        theme = synthesize(frame_context(role=MIRROR_NOT_ORACLE, evidence=c.notes, …))
        if self_check(theme, c.notes).passed:
            derived.add(kind="dream", body=theme, provenance=INTERPRETED)  # no other class possible

# Outward action — model advises, code acts, human gates
act(proposal):                      # proposal emitted by a model
    if proposal.tool ∉ agent.scope: route_to_human_gate(); return
    if proposal.is_outward: require_human_approval(proposal)
    result = code_execute(proposal)          # sandboxed; no creds/network/vault unless granted
    validate_against(rolling_baseline, frozen_golden, constitution); rollback_if_regressed()
```

---

## 11. Build status (as of Phase 7)
Phases 0–7 complete and tested (152 logic tests + live): sealing & egress guard, two-slot
loader, scoped telemetry, Constitution inheritance; content-addressed raw store + Logseq
ingest + embeddings + provenance-aware vector store (118 notes → 914 vectors of the owner's
real corpus); the Librarian + frozen golden set + grounding self-check; the scheduler +
foreground gate + sandbox + factory; the interface gateway (local default, opt-in third-party);
the Curator + Dreamer on the interpreted layer (trough-only, mirror-only, grounded). Next:
Phase 8 (airlock). The dream R&D track (§8) runs behind a flag, off by default.

---

## 12. How to rebuild
1. **Honor the invariants first** (sealed core no egress; network and private data never share a
   component; model advises/code acts; sandboxed execution; every self-modification gated &
   reversible; every agent inherits the Constitution; consequential advice defers; respect the
   memory ceiling; the fixed points are sacred; secrets outside code; interface may transit a
   third party, the corpus never does; voice bounded & code-dialed).
2. **Build in phases, verify each gate, checkpoint, one phase per session**, resuming from
   `PROGRESS.md` not chat history. Self-modification is built last.
3. **Carry the decisions**: local models for the 32 GB budget; provenance as an extensible type;
   object-capability for all scope; FileVault + integrity hashes + restic; the firewall.
4. **Read the design notes** for the subtle parts: `skills-and-scope`, `observed-data-and-the-
   assistant-tier`, `roadmap-and-future-directions`, `dream-phase-rnd-charter`, `dreaming-v2`,
   `recursive-dreaming`.
The full specification is `docs/BUILD-SPEC.md`; the operating rules are `CLAUDE.md`; the fixed
points are `CONSTITUTION.md`; the practice is `CONVENTIONS.md`.

---

## 13. Closing
The system is an attempt to answer an honest question — *what does my own mind look like from
the outside?* — without lying in the answer. Everything hard in it comes from refusing the easy
version: refusing to let inference pose as truth, refusing to let convenience hold credentials,
refusing to let the system's reflections on its reflections drift free of the ground. What makes
it a second brain rather than a clever toy is not any single capability; it is that the whole is
disciplined to stay honest as it grows — a living thing, nurtured by being watched, anchored by
what the owner actually wrote. The poetry was the inspiration. The discipline is what makes it
real.
