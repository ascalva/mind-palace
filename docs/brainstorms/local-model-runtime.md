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
