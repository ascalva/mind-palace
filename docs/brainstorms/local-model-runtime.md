# Local model runtime — Ollama's sharp edges → llama.cpp-direct

Brainstorms on the local inference runtime for the palace: what serves the resident
models + embedder on the sealed core (loopback, zero-egress), and whether to move off
Ollama as performance and reliability become more important.

## 2026-07-22 14:18 UTC

```capsule
topic: local-model-runtime
date: 2026-07-22

decisions:
  - Direction: migrate local inference OFF Ollama to llama.cpp-direct (`llama-server`) —
    keep the GGUF ecosystem + the same Metal backend Ollama already wraps, shed only
    Ollama's middleware (the model-lifecycle/keep-alive/API quirks the owner has been
    compensating for). Owner explicitly likes the flexibility/control llama.cpp exposes
    (KV cache, n_gpu_layers, context, parallel slots, the exact quant).
  - Architectural fit is the real argument, not just ergonomics: `llama-server` is a
    SINGLE-model server and does NOT hand you residency orchestration — but the palace
    ALREADY owns that (`scheduler`, `max_resident_models=2`, the `resident_gb` model).
    Today two schedulers fight for residency (the palace's + Ollama's opaque one) — the
    source of the swap thrash. Going direct moves the residency decision entirely into
    code the palace owns, tests, and can ratchet — squarely the structural-enforcement
    ethos ("the model advises, code acts; a property is real only when a test proves it").
  - Enabling refactor: abstract the core's inference client from the NATIVE Ollama API
    onto the OpenAI-compatible surface. Both `llama-server` and `mlx-lm` serve it, so the
    backend becomes swappable — this is what makes MLX a cheap later experiment instead of
    a re-architecture.
  - vLLM is RULED OUT for the current hardware: it is CUDA-first with no Metal/Apple-Silicon
    backend (CPU-only fallback = unusable at these sizes), and it optimizes high-concurrency
    SERVING (PagedAttention/continuous batching) — a problem a single-user daemon with ≤2
    residents does not have. Reserved only for a hypothetical future Linux + NVIDIA box.

parked:
  - decision: MLX (mlx-lm) as the inference backend.
    default: not adopted — llama.cpp-direct is the choice; MLX stays a candidate, not a bet.
    re_entry: AFTER the OpenAI-API abstraction lands, A/B mlx-lm vs llama.cpp on the actual
      corpus/models on the M2 Max; adopt ONLY if it wins on perf AND its serving layer is
      mature enough for an always-on daemon. (Owner reservation: MLX maturity — younger
      serving story, MLX-specific quant path (not GGUF), faster tooling churn. Apple's
      post-WWDC-2026 push is a momentum signal but is past the assistant's Jan-2026 cutoff,
      so unverified — weight the owner's current read.)

open_questions:
  - Residency with single-model servers: how does the palace serve ≤2 resident models (up to
    ~23 GB on ~24 GB usable) when `llama-server` is one-model-per-process? (Two server
    processes + palace-side swap orchestration, vs Ollama's automatic swapping.)
  - Exact re-grounding of `resident_gb` / `max_resident_models` against llama.cpp's REAL
    load/unload semantics (they differ from Ollama's) — the scheduler's memory gate is
    currently calibrated to Ollama's behavior.
  - Cold-load / model-swap latency for big weights under llama.cpp — does it meet the
    daemon's responsiveness bar, and does the slot/keep-alive model cover the embedder +
    a reasoning model coexisting?
  - Is the embedder (`qwen3-embedding:4b`) served by the same llama.cpp path or a separate
    process/endpoint?

next_steps:
  - Graduate this into a DESIGN NOTE — the model runtime is BUILD-SPEC §5/§7 governed
    (sealed-core loopback, zero network egress); any switch must preserve those bright lines
    structurally, not by convention.
  - Scope the two bounded migration costs in the note: (1) core inference client →
    OpenAI-compatible API surface; (2) scheduler residency model re-grounded against
    llama.cpp load/unload.
  - Prototype first: stand up `llama-server` on the M2 Max serving the current models over
    loopback; MEASURE load/unload + swap latency + real memory footprint vs the `resident_gb`
    assumptions before committing the scheduler rewrite.

references:
  - config/defaults.toml — the current `[ollama]` block (loopback, `resident_gb`,
    `max_resident_models=2`, `model="qwen3-embedding:4b"`)
  - docs/BUILD-SPEC.md §5/§7 — sealed-core loopback + zero network egress (the invariants
    any runtime must preserve)
  - Hardware: Apple M2 Max, 32 GB unified memory (~20–24 GB usable)
  - external tools: llama.cpp `llama-server` (OpenAI-compatible endpoint, GGUF, Metal);
    MLX / `mlx-lm` (Apple-native, Metal, OpenAI-compatible server); vLLM (CUDA-first —
    ruled out for Apple Silicon)
```

## 2026-07-25 — the embedder question is DOWNSTREAM of this migration (and f-0174)

```capsule
topic: local-model-runtime (the embedder's residency)
date: 2026-07-25 (session-44, ~02:00)

how it came up: the owner asked whether there is "another embedder model that would be a genuinely
good idea to migrate to". The orchestrator answered partly from a MEMORY-CEILING argument — that an
8B embedder would compete with the 27B chat model for the two slots — and the owner pushed back
correctly: "why do we need to run both models at the same time, the scheduler should be able to
adequately manage between models, and this also feels like it ties into the conversation of
migrating to llama.cpp". Both halves of that push were right, and checking produced a finding.

WHAT THE GROUNDING SHOWED:
  · The owner is right that co-residency is not required. The scheduler ALREADY does swap-avoidance
    within a priority band over a two-slot loader (scheduler/queue.py:174, :188;
    scheduler/supervisor.py:4-9 counts worker-slot swaps as "the cost to minimize"), and
    `vault_sync` routes to the PINNED tier precisely because it "calls the embedder directly — so
    making it resident is a no-op and the worker slot is never evicted"
    (scheduler/vault_sync.py:9-11). The embedder does NOT contend for the worker slot.
  · ⚑ BUT the check turned up worse than the claim it refuted: **the embedder is not in the memory
    accounting AT ALL.** `[embedding]` (config/defaults.toml:112-119) has no `resident_gb` and is
    not a `[[models]]` entry, so `MemoryLoader` (core/models/loader.py:40-41, :58-64) never sums it.
    Stretch tier 23.0 GB (declared, evicts_pinned) + embedder ~2.5 GB (real, warm 30m, invisible)
    = 25.5 GB against usable_ram_gb = 24.0 — and the gate approves, because it is summing an
    incomplete set. **Filed as finding-0174.** Non-negotiable 8 is enforced over a model of memory,
    not memory.

⚑ THE SEQUENCING CONCLUSION (the point of this capsule):
  **The embedder-migration question is DOWNSTREAM of the runtime migration, and cannot be answered
  honestly before it.** "Can we afford an 8B embedder?" is unanswerable today in EITHER direction,
  because under Ollama residency is opaque — Ollama decides when the embedder loads and unloads on
  its own keep-alive, invisible to the palace. Under llama.cpp-direct the embedder becomes a
  `llama-server` process the palace starts and stops with an explicit budget and lifetime, and the
  accounting becomes REAL rather than declared. This capsule's own earlier open question — "exact
  re-grounding of resident_gb / max_resident_models against llama.cpp's REAL load/unload semantics"
  — is finding-0174 stated in advance; f-0174 is its measured instance.
  ⇒ ORDER: llama.cpp-direct design pass (with f-0174 folded in as a required input) → residency and
    the embedder budget become explicit and testable → THEN the embedder-choice question
    (docs/brainstorms/embedding-space-specialization.md) becomes computable rather than a guess.

the embedder-choice research, parked here so it is not lost (grounded 2026-07-25, web-verified):
  · current: `qwen3-embedding:4b`, 2560 dims — near-frontier, not a compromise. Qwen3-Embedding-8B
    scored 70.58 on MTEB multilingual and held #1; the 4B is one tier below, same family.
  · candidates: Qwen3-Embedding-8B (~5 GB Q4, same family); NVIDIA Llama-Embed-Nemotron-8B
    (reported multilingual MTEB leader, fully open-weight); BGE-M3 (MIT, 100+ languages, 8K ctx,
    1024 dims) — whose interesting property is NOT its dense score but **hybrid dense + sparse +
    multi-vector retrieval**. Dense embeddings are weak at exact-token matching (identifiers,
    symbols, error strings); the palace now embeds code as a first-class source, so sparse is a
    CAPABILITY difference, not a leaderboard delta. That is the candidate worth testing.
  · API embedders (Voyage, Cohere, OpenAI) are ARCHITECTURALLY FORBIDDEN — sealed core, zero egress.
  · cheap lever before any migration: Qwen3-Embedding supports Matryoshka-style variable dimensions
    (truncate 2560 → 1024 or fewer) — a compression knob with NO model change, squarely ops-track.
  · caveat that must not be skipped: MTEB v2 (2026) scores are NOT comparable to v1, and benchmark
    gains routinely fail to transfer to a specific corpus. A migration costs a full re-embed (§8)
    + sigma recalibration (sigma in [0.55,0.75] is EMBEDDER-specific, defaults.toml:268-271) +
    revalidation of every downstream instrument. Migrating on a leaderboard number would be
    f-0163/f-0169/f-0174's failure mode a fourth time. Build the retrieval eval FIRST.

open questions:
  - Does the llama.cpp pass now need to model THREE processes (pinned + worker + embedder) rather
    than two slots? `max_resident_models = 2` may itself be the wrong shape once the embedder is
    counted honestly.
  - Should `docs/brainstorms/local-model-runtime.md` move under the new `ops` track
    (docs/tracks/ops.md, minted 2026-07-25)? It is runtime/residency/performance — ops-shaped by
    every criterion in that manifest, and it currently has no track coordinate at all.
```

## 2026-07-25 — ⚑ promoted: the runtime is what decides supervision's achievable TIER

```capsule
topic: local-model-runtime
date: 2026-07-25 (session-47, from the supervision design pass)

owner, verbatim: "you mention the ollama effort, is this a place to say that it's worth it to
continue also along the llama.ccp track? we manage the model loading, inference, scheduling,
memory, all by ourselves, like a true OS"

VERDICT: yes, and stronger than "also worth continuing." The supervision pass produced MEASURED
evidence that promotes NEW NOTE 2 from "small, queued, direction-already-decided" to **the note
that decides how far the OS-layer mandate can actually be taken.**

--- the two things that forced the promotion ---

1. V3 IS ONLY ASKABLE BECAUSE WE DO NOT OWN THE RUNTIME. dn-supervision-and-liveness leaves open:
   "does Ollama abort its work when the client dies?" If it does not, killing a wedged worker stops
   the ACCOUNTING but not the BURN — the fail-safe half of oq-0035(c) is weaker than it reads. That
   question is a property of someone else's software, answerable only empirically and re-answerable
   on every version bump. On the tier ladder it is a **tier-5 dependency inside a design whose
   whole mandate is tiers 1-2.** Own the runtime and it is not answered — it is DELETED: we hold
   the cancellation token, and "worker killed, compute continues" loses its representation.

2. THE CEILING IS ALREADY BREACHABLE, SILENTLY — finding-0199 (filed this session, code-traced).
   `TwoSlotLoader._resident` starts EMPTY on every construction; nothing reconciles it against
   Ollama; `ps()` is called from exactly ONE place in the repo (the cosmetic status line), never
   from the accounting path. Ollama outlives the supervisor, pinned models load keep_alive=-1
   (never timer-evicted), workers 30m. So after an unclean exit + automatic launchd restart inside
   that window: `_check_ceiling` sums only what THIS process loaded, the eviction loop iterates an
   empty dict and never tells Ollama to drop the stale model, and actual residency can exceed BOTH
   max_resident_models and usable_ram_gb WHILE THE GUARD PASSES.
   ⇒ non-negotiable #8 is enforced against a belief, and is silent about being wrong. That is the
   owner's disqualifying shape ("shoot ourselves in the foot without realizing") landing on an
   INVIOLABLE KERNEL item, on the crash-restart path, which launchd exercises automatically.

--- the unifying claim (the runtime twin of the supervision note's class) ---

supervision note: "every ops ledger is written by the actor whose failure it must record."
runtime:          "the memory ledger is maintained by an actor that CANNOT OBSERVE what it
                   accounts for, and that a third party can invalidate unilaterally."

Same defect class, one layer down. Owning the runtime converts residency from a BELIEF ABOUT
ANOTHER PROCESS into a FACT WE HOLD — tier 5 → tier 1-2 — and removes the third-party eviction
timer that can invalidate the books at any moment.

--- ⚑ what it does NOT buy (be precise; do not oversell) ---

Supervision is NOT blocked on the runtime. The compute/land split, job deadlines, the lease and
the dead-man's switch all work fine with Ollama behind an HTTP boundary. The runtime is not a
PREREQUISITE — it RAISES THE ACHIEVABLE TIER on exactly two targets: cancellation and memory.
Sequencing follows from that: supervision can proceed now; the runtime decides how good it gets.

--- the costs, stated (an OS owns every bug in what it manages) ---

  - Owning inference means owning a C++ dependency's crash modes, memory behaviour, upgrade path,
    quantization handling and concurrency. Ollama does real work for us today.
  - It changes what sits inside the seal (non-negotiables #1/#4). dn-supervision-and-liveness's V4
    already flags that the seal is a per-process monkeypatch a spawned worker must re-assert —
    in-process vs spawned inference interacts with that directly. The two notes must agree here.
  - It does NOT fix f-0163/f-0169/f-0174's failure mode (migrating on a number). The retrieval
    eval still comes first — that constraint from the 2026-07-22 capsule stands unchanged.

--- immediate, cheap, independent of the migration ---

Reconcile `_resident` against `ps()` at loader construction / before `_check_ceiling`. Closes the
cold-start hole; partial (ps() returns NAMES, so a model outside the registry cannot be costed —
must not be reported as full accounting). Worth weighing BEFORE the restart, since the restart is
a fresh supervisor coming up against an Ollama that has held models since run #35.
```
