# Design note — The Ambassador: interpretation, flow, and why it isn't a bottleneck

**Status:** design only. Refines §4 of `nervous-system-and-ambassador.md` — the
conversational front door. Resolves two questions: (1) what "interpretation" actually
means at the conversational layer (and why most of it is safe), and (2) how the single
front door avoids becoming a throughput bottleneck. Builds on shipped pieces: the pinned
tier, the scheduler/queue, MirrorView, the Phase-10 gate, the attestation chain, and the
§13 context budgeter. Honor at Phase 11 / text-interaction activation.

---

## 0. The reframe that dissolves the worry

The dangerous interpretation — finding patterns in the owner's psyche, deciding what
the notes *mean* — **already happened**, offline, in the dream/correlator layers:
grounded, depth-decayed, attested. By the time the Ambassador speaks, the
interpretation is **done and on the shelf**.

The Ambassador's job at conversation time is smaller and safer: **route, retrieve,
render.** It reads a question, picks which already-processed shelf to pull from, and
renders the result into sentences. It is a **reader of conclusions, not a generator of
them.** This is why the "isn't this trivial?" intuition is substantially correct — but
*which* part is trivial matters.

---

## 1. Two kinds of interpretation at the Ambassador

### 1a. Retrieval-time interpretation — SAFE (the trivial part)
"What did I write about my father?" → embed the query → search the mirror → rank →
summarize what returns. The model interprets **the question into a query**, not **the
owner into a verdict**. It reads already-grounded, already-attested content and narrates
it — standard RAG shape. Safe *because it is downstream of all grounding*: it cannot
manufacture a pattern, only surface one the dream layer already grounded and the
attestation chain already signed.

### 1b. Intent interpretation — needs a boundary (the only consequential part)
"Look into whether I've been more anxious lately" → the Ambassador decides **what task
to spawn**. This is the one genuinely consequential interpretation it performs. The
safeguard is already in the architecture: **it does not act on its interpretation — it
proposes a scoped task that goes through the gate.** If it misreads intent, it misroutes
a task: recoverable, visible, gated. **The blast radius of an Ambassador
misinterpretation is a wrong query, not a corrupted mirror.**

### 1c. The line that keeps it secure
The Ambassador reads **interpreted-and-attested outputs**, never raw authored text it
then re-interprets as truth. **Wide window, narrow hands:** it can *see* the mirror, the
dreams, and the operational state, but its authority is *read + propose*, never *write +
act*.

---

## 2. Why the single front door is not a bottleneck

A front door bottlenecks only if it does the work itself. The design prevents that:

### 2a. The Ambassador is a dispatcher, not a worker
It holds **no heavy computation**. It does three cheap things — embed the query, pull
from a shelf, render a sentence — and hands everything expensive to the queue. It never
blocks on a dream pass, never waits for a correlator run, never holds the synthesis
model. A question needing real work → it **spawns a gated task, says "looking into
that," and the work runs asynchronously** on the existing scheduler (the same trough
machinery that runs dreaming). The conversation stays responsive because the
conversational layer is deliberately **thin**.

### 2b. It runs on the pinned tier (always warm, small, fast)
- **Model:** the pinned tier (`qwen3.5:2b`) — **already resident**, so there is no
  load-latency on each message (no swap into a slot per turn).
- **Retrieval:** a vector search — milliseconds.
- **Rendering:** short-context generation on the small model — fast.
- The **expensive tiers** (synthesis 27B, stretch) are touched **only by delegated
  background work**, never inline in the conversation. You are not waiting on a big
  model to chat — you chat with the small always-warm one, and it dispatches the big
  work to run while you keep talking.

This is the **same move as the nervous-system note**: put each operation at the lowest
tier that can handle it. Chatting is a reflex (pinned, µs–ms); deep work is cognition
(delegated, trough-scheduled).

### 2c. The real bottleneck risk — context assembly (name it, then bound it)
The temptation: stuff the Ambassador's context with everything — mirror + recent dreams
+ operational state + full history — on **every turn**. That blows the window and slows
every response. **Discipline: the §13 budgeter retrieves *selectively per turn*, not
exhaustively.** Pull the few relevant shelves for *this* question; do not mount the
whole library every message. That is the difference between a responsive front door and
one that re-reads everything before answering "hello."

---

## 3. The conversation loop (concrete)

```
1. Owner message arrives (interface gateway, Zone B, over Tailscale).
2. Ambassador (pinned tier) classifies intent:
   (a) retrieval  → embed query → MirrorView/DerivedStore search → rank → render. Done inline.
   (b) status     → read operational state (attestations/ledger/drift) → render. Done inline.
   (c) task       → compose a scoped ProposedTask → gate → queue. Reply "on it"; result later.
   (d) capture    → store the message as `authored-dialogue` → enqueue ingest. Reply, done.
3. For (c): the worker runs async on the scheduler; the Ambassador surfaces the result
   on completion (push via the gateway, or on the next turn).
4. Every step emits an attestation (role: "ambassador", action: read|propose|capture).
```

Inline paths (a/b/d) are cheap and synchronous. Only (c) — real work — is delegated, and
it is delegated *precisely so the conversation never blocks on it*.

---

## 4. Integration with what already exists

| Concern | Mechanism (already built) |
|---------|---------------------------|
| Stays responsive | Pinned tier hosts it; heavy work delegated to the queue (Phase 3) |
| Reads the mirror safely | `MirrorView` read handle — no write path to authored content |
| Reads operational state | NEW read handle over attestations/ledger/drift (the §4 introspection scope) |
| Never acts directly | Proposes `ProposedTask`/`ProposedChange` → the Phase-10 gate |
| Context stays bounded | The §13 budgeter; selective per-turn retrieval |
| Auditable | Every turn emits an attestation; conversations are `authored-dialogue` |
| Knows the system | The white papers/design notes as a `curated` self-knowledge graph (own graph, firewall-preserved) |

**Net new work is small:** the intent classifier (cheap, on the pinned model), the
delegation grammar (intent → scoped gated task), the operational-introspection read
handle, and the selective per-turn retrieval policy. Everything expensive it stands on
is already shipped.

---

## 5. Failure modes & bounds
- **Misread intent (1b):** misroutes a task → gated, visible, recoverable. Never a write.
- **Over-retrieval (2c):** bounded by the budgeter; selective per-turn retrieval.
- **Latency creep:** if inline rendering ever needs a heavy tier, that is a routing bug —
  inline stays on the pinned tier; anything needing synthesis is delegated by definition.
- **Over-exposure of internals:** explaining the design is fine; live secrets/keys are
  never in the self-knowledge graph (same rule as §4: narrate the architecture, never the
  credentials).
- **Consequential advice:** health/financial/legal correlations surface with uncertainty
  and defer to the owner + a professional (Invariant 7).

---

## 6. The one-line answer to both questions
**Interpretation at the Ambassador is mostly retrieval-rendering of already-grounded,
already-attested conclusions (safe); the only consequential interpretation — what task
to spawn — is gated, not acted on. It does not bottleneck because it is a thin dispatcher
on the always-warm pinned tier that delegates all heavy work to the existing async
scheduler. Wide window, narrow hands, thin body.**

---

## 7. Open questions
- Intent classification: a small deterministic router first (keyword/embedding intent),
  earning the model only for ambiguous cases? (Lean: yes — mirror the dream layer's
  "deterministic floor, model earned" pattern.)
- Does the Ambassador ever *proactively* surface a finding (a new high-confidence dream,
  a drift alarm), or only answer? (Lean: opt-in notifications, owner-controlled — a
  proactive mirror can become a nag; the owner sets the cadence.)
- Result delivery for delegated tasks: push on completion vs. report on next turn?
- How much conversation history is itself retrieved as context vs. re-derived from the
  `authored-dialogue` ingest — avoid double-storing the same thread.
