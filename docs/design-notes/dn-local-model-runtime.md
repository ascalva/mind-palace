---
type: design-note
id: dn-local-model-runtime
track: ops
status: ratified
created: 2026-07-25
updated: 2026-07-25
links:
  - docs/brainstorms/local-model-runtime.md          # direction (07-22) + promotion (07-25)
  - docs/brainstorms/design-pass-routing.md          # NEW NOTE 2 — this is that note (see §1.1)
  - docs/design-notes/dn-supervision-and-liveness.md # ratified sibling; §2.7 boundary, V3/V4
  - docs/findings/finding-0174.md                    # ceiling ignores the embedder (folded, §2.3)
  - docs/findings/finding-0199.md                    # cold-start ceiling breach (REPRODUCED, §2.1)
  - docs/inbox/owner-questions.md                    # oq-0035 ruled (c): cancellation is committed
supersedes: null
superseded_by: null
warrant: docs/findings/finding-0199.md
---

# Local model runtime — own the inference lifecycle (llama.cpp-direct)

> Filed by the chat agent as `draft` (chat-side protocol, §8). Ratification is a
> hand edit by the owner — no command performs it, and `gate-guard` denies any
> agent attempt (§10). `/graduate` refuses this note until `status: ratified`.

**Owner's mandate (2026-07-25, verbatim):** *"as part of making a robust system, I think you also
need to spawn a design fable probe to understand and create the design for migrating to llama.cpp,
so that we can stop living in uncertainty on how ollama handles errors"* — and the direction was
decided earlier: *(2026-07-22)* migrate local inference off Ollama to llama.cpp-direct;
*(session-47)* *"we manage the model loading, inference, scheduling, memory, all by ourselves,
like a true OS."*
On equivalence *(2026-07-25)*: *"I agree with the non-goal of swapping models, first we need to make
sure the same model produces the same results as our baseline."*

Read the first mandate as the acceptance bar: **the deliverable's job is to end an epistemic
dependency, not to swap a binary.** §2.2 says exactly which uncertainties the migration *deletes*
(because we come to own the answer) and which it merely *relocates* (we own a different unknown).
A migration that trades Ollama's unknowns for llama.cpp's unknowns and claims victory is the
failure mode this section exists to prevent.

Every mechanism in this note is ranked on `dn-supervision-and-liveness`'s five-tier ladder
(1 unrepresentable · 2 capability · 3 protocol · 4 ratchet · 5 runtime check). Overclaiming a
tier is itself the foot-gun; §2.7 is the honest ledger.

## 1. Purpose and scope

This note specifies **how** the palace migrates local inference from Ollama to palace-owned
`llama-server` processes: the target process model, the residency/accounting redesign that folds
in finding-0174 and finding-0199, the seal posture, the equivalence gate the cutover must pass,
the migration order, and the rollback story. The direction itself is owner-decided (2026-07-22)
and is not re-opened here.

It is grounded in measurements taken 2026-07-25 on the target machine (M2 Max, 32 GB), against
the installed packages — Ollama **0.31.2** and llama.cpp **build 10090 (7347430f4, brew)** — not
against documentation (the finding-0176 discipline). §2.1 is the evidence; everything downstream
cites it.

### 1.1 Reconciliation with the routing map

This is **NEW NOTE 2** of `design-pass-routing.md:66-73` (S5 in the addendum's sequence), with
finding-0174 folded in as that map requires. Two amendments to the map's assumptions, made
explicitly rather than by drift: (a) the note is no longer "small" — the 2026-07-25 promotion
capsule and the owner's equivalence ruling added a measurement obligation and a cutover gate;
(b) it carries the brainstorm's two open questions to answers (§2.3: three processes; and this
note now has the ops track coordinate the brainstorm lacked). The embedder-*choice* question
(`embedding-space-specialization.md`) stays gated behind this note, unchanged. Panel: systems +
security (it touches the sealed core's inference boundary).

### 1.2 Non-goals (load-bearing — read at ratification)

- **NOT a model change.** Owner-stated (2026-07-25, verbatim above). Same models, same weights,
  same quant; the embedder migrates on the *identical GGUF file* Ollama serves today (§2.1 E).
  Running the same model under a different runtime must be retrieval-neutral, and §2.5 is the
  gate that proves it. An embedder-model swap (8B, BGE-M3, Matryoshka truncation) remains gated
  behind the 2026-07-22 constraint: build the retrieval eval first, never migrate on a
  leaderboard number.
- **NOT MLX adoption.** Owner-parked (2026-07-22 capsule): the OpenAI-compatible seam this note
  builds is what makes MLX a cheap later A/B; adopting it is a separate decision with its own
  re-entry condition.
- **NOT vLLM.** Owner-ruled-out for this hardware (2026-07-22 capsule).
- **NOT the supervisor execution model.** The compute/land split, worker subprocess, leases and
  escalation belong to `dn-supervision-and-liveness` (ratified). This note supplies the runtime
  side of their shared boundary (§2.7 there; §2.3–§2.4 here) and closes its V3 empirically.
- **NOT a re-embed of the corpus.** [INFERENCE] The cutover is designed so that no re-embed is
  needed in either direction (§2.5–§2.6); a full re-embed from raw remains the *recovery* path
  if the equivalence gate ever fails, never a planned step. Inferred: no artifact demands one,
  and avoiding it is the point of the gate.
- **NOT σ recalibration or chunking changes.** [INFERENCE] `similarity_threshold`,
  `near_dup_threshold`, `max_chars`/`overlap_chars` are untouched; §2.5 states why the gate
  keeps their calibration valid. Inferred from the model-change non-goal.
- **NOT retiring `OllamaClient` at first landing.** [INFERENCE] Both backends coexist behind the
  seam until every tier has flipped and a deskcheck has passed; the old path IS the rollback.
  Inferred from the reversibility requirement.
- **NOT voice/telephony model serving.** [INFERENCE] BUILD-SPEC #12's local speech models are a
  separate serving path, out of scope. Inferred: no current wiring exists.

## 2. Principles / decision

### 2.1 The measured ground (2026-07-25, all empirical, hygiene: everything unloaded after)

**A. M1 — Ollama DOES abandon work when its HTTP client dies (V3 answered).** Long generation on
`qwen3.5:2b` (`num_predict=8000`), client killed at t+7 s. Non-streaming (the palace's actual
mode, `core/models/ollama_client.py:116`): server log shows the request logged at the disconnect
moment (`500 | 6.647s`), then `srv stop: cancel task, id_task = 0` and
`slot release: … stop processing: n_tokens = 429` — 429 of 8000 tokens; a follow-up request
completed in 0.457 s (no queueing behind abandoned work). Streaming: identical
(`n_tokens = 431`, follow-up 0.43 s). **The V3 uncertainty is ended for 0.31.2 by measurement:
the burn stops.** What measurement cannot end is the *re-opening*: this is a property of
software we do not control, silently re-answerable on every upstream bump. §2.2 is precise about
what the migration adds beyond today's good news.

**B. M2 — finding-0199 REPRODUCED, all three phases, live Ollama.** Staged the pre-crash state
(`2b` loaded `keep_alive=-1` exactly as `ensure_pinned` issues it, + `9b` at 30 m), then a fresh
`TwoSlotLoader` in a new process: (1) *false-absent* — after `ensure("qwen3.5:9b")` the loader
believes 1 model / 6.6 GB while `ollama ps` holds 2; the timer-immune pinned model is invisible.
(2) *guard-pass on a real breach* — `ensure("qwen3.6:35b-a3b", warm=False)` (same accounting
path, `loader.py:80-93` gates only client calls) raised nothing: the guard summed 23.0 ≤ 24.0
while the true prospective (stretch + the really-resident pinned) is **25.7 GB > 24.0**, and the
eviction loop never targets the real 2b. (3) *false-resident* — after an external unload (the
30 m timer's stand-in), `ensure("qwen3.5:9b")` returned in 0.0 ms on the stale belief, skipping
a needed load. Finding-0199 is no longer code-traced; it is a **measured safety fact**, and it
upgrades the urgency of the interim fix (§2.8).

**C. Residency reality under Ollama — bigger than filed.** `ollama ps` during the runs:
`qwen3.5:2b` = 2.5 GB at ctx 8192 but **3.6 GB at ctx 65536** (a bare load takes the model's
default); the embedder `qwen3-embedding:4b` = **10.0 GB at ctx 40960** — its model-default
context, which is what production gets because `OllamaClient.embed()` passes no `num_ctx`
(`ollama_client.py:97-104`). finding-0174 assumed ~2.5 GB; the invisible consumer is ~10 GB.
Under palace-launched `llama-server` at ctx 8192 the same embedder blob runs at **RSS 3.69 GB**.
Context, not weights, dominates the declared-vs-actual gap — `resident_gb` as a weights-only
constant is the wrong shape (§2.3).

**D. Ollama is already one llama-server per model.** `pgrep` during the runs:
`/Applications/Ollama.app/Contents/Resources/llama-server` — one subprocess per loaded model,
`-np 1`, the 2b at `-c 8192 --no-jinja --chat-template chatml`, the embedder at
`-c 40960 --embedding`, both `--offline`. The "two-slot server" the loader models does not
exist; reality is N single-model server processes behind an opaque Go manager. **The migration
replaces the manager, not the server.**

**E. The embedder blob is portable; the chat blobs are NOT.** Upstream `llama-server` loads
Ollama's `qwen3-embedding:4b` blob directly (1.66 s to healthy, dims 2560 correct). The chat
lineup (`qwen3.5:2b/9b`, `qwen3.6:27b` — all GGUF arch `qwen35`) **fails to load**:
`key qwen35.rope.dimension_sections has wrong array length; expected 4, got 3`. Ollama's bundled
fork accepts metadata upstream rejects; Ollama's model store has drifted from upstream
conventions for this family. Chat-tier migration therefore requires upstream-convention GGUFs
(owner-fetched, outside the core — §2.4), and the load failure itself was fail-closed: process
exit with a clear log, no zombie.

**F. Cross-runtime embedding equivalence on the identical blob — measured.** 20 diverse texts
(prose, notes, code, SQL, multilingual, degenerate single tokens) embedded under both runtimes:
cross-runtime cosine **min 0.999990, mean 0.999999, max 1.000000**; the worst case is the
single token "the". Within-runtime repeat and single-vs-batch floors: **1.000000** everywhere.
Same dims (2560). This grounds §2.5's tolerance from data.

**G. llama-server behavior, measured on b10090.** Generation cancel on client death: slot freed
≤1.1 s (`cancel task`, `n_tokens = 1195` of a forced 12000; follow-up 0.077 s). Batched embed
(256 inputs, baseline 107 s): cancel works at coarser granularity — slot freed in ~20 s, follow-up
13.5 s vs ~95+ s had it kept computing (V-E pins client-side batch sizing). Errors are typed
JSON (`exceed_context_size_error` with `n_prompt_tokens`/`n_ctx` fields; parse errors detailed) —
versus Ollama's opaque string errors wrapped in `OllamaError`. Observability: `/health`
(503-while-loading → 200), `/slots` (`is_processing` ground truth), `/props`, `--metrics`
(Prometheus). Greedy decoding (temp 0, seed 42) reproduced identically across runs. **SIGTERM:
idle → 0.25 s clean exit; mid-request → wedged, no exit in 30.9 s (and >3.5 min in a second
observation); SIGKILL required.** Load failure → immediate process death, nonzero exit.
`--offline` exists upstream (`LLAMA_ARG_OFFLINE`, "prevents network access").

### 2.2 What the migration deletes, what it relocates (the acceptance bar)

Deleted — the palace comes to own the answer, and the question loses its object:

| uncertainty today | why it is deleted |
|---|---|
| is the model resident? | residency = a child process we hold; kernel fact, not a belief |
| when does the embedder load/unload? | we start/stop the process; no third-party keep-alive timer |
| what does a load actually cost? | we pass `-c` explicitly; footprint measured at bring-up |
| whose eviction wins? (two schedulers) | one scheduler remains — ours |
| does cancel survive a version bump? | cancel = SIGKILL of our child; kill(2) does not regress |

Prose for the last row, because it must not be overclaimed: M1 measured that Ollama 0.31.2
cancels on disconnect — today's behavior is *good*. What the migration deletes is the *question's
recurrence*: under Ollama the property lives in an unpinned third party (the app auto-updates)
and is re-answerable only empirically per version; under palace-owned processes, "stop the burn"
is `SIGKILL` + waitpid — tier 3, an authority outside any wedge — and the residual per-bump
question shrinks to the equivalence gate re-run (§2.5), which is mechanical.

Relocated — honest column; these become OUR unknowns and the design must carry them:

| new unknown we own | carried where |
|---|---|
| llama-server's crash/wedge modes are ours to supervise | §2.4 escalation; measured SIGTERM wedge |
| restart authority (Ollama's manager auto-restarts today) | §2.4 process manager |
| chat-model files must come from upstream, not Ollama's store | §2.6 P5; V-B |
| per-bump behavior drift is ours to re-gate | §2.5 gate re-run; pinned build (§2.6) |
| multi-process memory arithmetic is ours | §2.3; V-A for the big tiers |
| macOS can still kill a child under memory pressure | §2.3 falsifier; V-F |

The last row bars a tier-1 claim anywhere in this note: an actor outside our scheduler (jetsam)
can still change residency. What we get is that every such change is *observed* (waitpid, tier 3)
instead of silently absorbed into a stale belief.

### 2.3 The residency model: three processes, budget-gated at spawn (folds f-0174, f-0199)

The brainstorm's open question is answered **yes**: the model is **N single-model processes** —
concretely three roles — not two slots in someone else's server.

| process | model | ctx | grounded footprint |
|---|---|---|---|
| pinned router | qwen3.5:2b | 8192 | 2.5 GB (measured, ollama ps @8k) |
| worker (one at a time) | per tier | per role | 9b @16k = 6.2 GB measured; 27b/35b = V-A |
| embedder | qwen3-embedding:4b | 8192 | 3.69 GB RSS measured (was 10 GB @40960) |

- **Residency is process existence.** A model is resident iff its server process is alive. The
  loader's successor (the *process manager*) holds child handles; `resident_models()` becomes a
  view over the process table. The false-absent and false-resident states of finding-0199 lose
  their representation: there is no belief dict to start empty or to go stale — tier 2 for the
  bookkeeping (the manager is the only spawner), tier 3 for the fact itself (kernel process
  table, waitpid). Honest bound: *external* death (jetsam, crash) is still representable — it is
  detected at tier 3, not made impossible (no tier-1 claim, per §2.2).
- **The budget gate moves to spawn time and gets real numbers.** Refusal before load survives
  (`_check_ceiling`'s refusal point, non-negotiable #8), but the sum is over *per-process
  budgets* = weights + ctx-dependent buffers, seeded from measured bring-up RSS, reconciled
  against live RSS (`ps`) — not a declared weights-only constant. The embedder is inside the
  books by construction: it cannot exist except through the gate (closes finding-0174
  structurally). The arithmetic check itself is tier 5 with a tier-4 ratchet (no spawn site
  outside the manager; the `check_imports.py` species); the refusal is only as good as the
  budgets, which is why they are measured, not declared.
- **Eviction is process stop.** Deterministic, verified by waitpid — never an unload request
  whose effect we hope for. Swap = stop worker A, spawn worker B; measured small-model
  bring-ups are ~1–3 s, big-tier cold-load is V-A (it gates the responsiveness claim).
- **`max_resident_models = 2` is replaced**, not reinterpreted: the constraint becomes "the
  budget sum fits" plus a policy row per role. Steady state routine = 2.5 + 3.7 + 6.2 ≈ 12.4 GB.
  Synthesis @32k and stretch likely do NOT fit beside both housemates (V-A measures); policy:
  the manager stops the embedder (and for stretch, the pinned router — the existing documented
  tradeoff) for the window, restarting after. That is the same evicts_pinned semantics, now
  executed by an actor that can verify it happened.
- **Embed context is right-sized to 8192** (from the model-default 40960): chunks are capped at
  `max_chars = 1200` (`config/defaults.toml:109`), far under 8k tokens; the measured saving is
  ~6.3 GB. V-D confirms no embed call can exceed it (fail-closed: the typed
  `exceed_context_size_error` is loud, §2.1 G).

### 2.4 The seal boundary and the process manager (M5; supervision's V4 neighbor)

**Spawned local servers, never in-process bindings.** `core/sealing.py` is a per-Python-process
monkeypatch on `socket.connect`; its own docstring names native extensions as the bypass. Moving
inference *into* the sealed process (llama-cpp-python) would put a large C++ surface inside the
seal where the Python guard cannot see it — it would *weaken* the provable seal. Spawned
`llama-server` keeps the boundary exactly where it is today with Ollama: the core talks
loopback HTTP to a local inference process that never reads the vault (non-negotiables #1/#2
posture unchanged, and the client already binds to `127.0.0.1` literals — no DNS).

The spawned server's own egress, ranked honestly:
- **Tier 2 (capability):** the manager launches with a local `-m` path and `--host 127.0.0.1`
  and never passes `--model-url`/`-hf`; plus `--offline` (upstream flag, measured present) as
  belt-and-suspenders. The server is never *given* anything to dial out for. Model acquisition
  (chat GGUFs, §2.6 P5) is an owner/ops action outside the core, like `ollama pull` is today.
- **Tier 4 (ratchet):** a test asserting the spawn argv contains no download flags + an `lsof`
  scan asserting the server holds loopback-only sockets while serving.
- **Tier 3 (later):** under dn-plane-principals, the server runs as a principal with no route
  out (pf anchor / separate uid) — deployment hardening, not claimed now.

**The process manager** (the loader's successor, core-side): spawn (argv-as-capability), health
(`/health` 503→200, measured), readiness-gated handoff, budget gate at spawn (§2.3), and stop as
**SIGTERM → grace → SIGKILL** — *required*, not optional: §2.1 G measured that llama-server
wedges on SIGTERM mid-request. SIGKILL of an inference server is safe by construction: it is
stateless (no store handles, no corpus writes; the only loss is in-flight tokens, which the
compute/land split already treats as disposable). This is the same escalation contract as
dn-supervision §2.5, pointed one layer down, and it is tier 3 where it matters (the kill is a
kernel operation) with the fire-decision at tier 5, stated as such. The sandbox runner
(`core/sandbox/runner.py:65-86`) is the in-repo precedent for subprocess + timeout + destroy.

Supervision's V4 (the seal is per-process; a spawned worker must re-assert it) is unchanged by
this note and stays owned there; this note adds only: the inference server is *outside* the seal
by design (as Ollama is today), so V4 applies to Python workers, not to llama-server.

### 2.5 The equivalence gate (owner-ruled; the cutover precondition)

**The hazard, named:** a partial or unvalidated cutover leaves `data/vectors.lance` holding
vectors from two runtimes. Every cosine across that boundary is then subtly wrong and *nothing
detects it* — not the drift gauge, not `status`, not the ratchets; the first symptom is bad
retrieval months later, on the one asset not rebuildable from git. And σ makes it worse than a
retrieval concern: `similarity_threshold = 0.62` is calibrated per-embedder-*and*-vectors
(`config/defaults.toml:267-272`), `near_dup_threshold = 0.93` (`:277`), `[dream_rnd] sigma`
(`:286`) — every σ-thresholded instrument (thought-graph edges, theme clustering, merge
detection) silently inherits a vector shift. This is why the tolerance is tight, not
"close enough."

**Position (the coordinator's three options, decided):** cutover is **per-lane all-or-nothing,
gated on measured equivalence** — not a blind atomic swap, and not a forced re-embed. The gate
is what makes the no-re-embed cutover *and* the no-re-embed rollback both sound: if the runtimes
agree beyond σ-resolution, provenance mixing is harmless; we still gate per-lane so that a
failed gate stops the lane cleanly. If the gate ever fails after a cutover, the recovery is a
full re-embed from raw (§8 re-derivability) — never a knowingly mixed store.

**The tolerance, proposed from data (§2.1 F), for the owner to ratify:**
- pass: per-text cross-runtime cosine ≥ **0.9999** on every fixture text (measured worst:
  0.999990 — 10× headroom), and `regressions()` empty (below);
- disqualifying (STOP the migration): any text < **0.999**. Rationale: the tightest live
  threshold is `near_dup = 0.93` with ~0.07 cosine of margin; a 1e-3 shift is 70× under that
  margin, and the measured deviation is two orders under the gate. Bit-identity is explicitly
  NOT the bar (different backends/batching); deviation ≤1e-4 is acceptable *because* it is
  three orders below any decision boundary the system holds.

**The harness (first-class deliverable, sequenced before any cutover):** a new
`eval/runtime_equivalence.py` (eval-side; `eval/golden.py` + `eval/golden/**` are foundation
denylist — **read and run, never write**) that:
1. embeds `eval/golden/corpus/` fixtures + `golden_set.json` queries under both backends via the
   §2.6 client seam and asserts the per-text tolerance above (worst case reported, not mean);
2. runs `evaluate(golden, retriever)` (`eval/golden.py:98`) with the llama.cpp-backed retriever
   and asserts `regressions(report, load_baseline())` is empty — the frozen golden set is
   non-negotiable #9's fixed point, stable across the migration *by construction*, which is
   exactly what a cross-runtime baseline needs;
3. re-runs on every runtime version bump (the pinned-build discipline, §2.6) — this is the
   mechanical residue of the deleted per-bump uncertainty (§2.2).

Generation tiers get the looser, correct bar: seed-pinned greedy determinism as a sanity check
(measured reproducible, §2.1 G) and the golden/drift gauges for behavior — never string
equality over sampled output. Tier accounting: the gate is a **tier-4 ratchet** (a test proving
a property at a point in time) and is claimed as nothing more; it does not watch production.
The cutover run additionally stamps backend + build into the ingest attestation record
(`core/ingest/sync.py:122` emits per-note records) so vector provenance is reconstructible —
field availability to be confirmed at graduation.

### 2.6 Migration path, reversibility, and order

**P0 — interim reconcile (independent, before the restart).** §2.8; not part of this wave.

**P1 — the client seam.** A backend-agnostic inference client protocol (chat/embed/health) with
two implementations: the existing `OllamaClient` and a `LlamaServerClient` speaking the
OpenAI-compatible surface (`/v1/chat/completions`, `/v1/embeddings` — measured working;
stdlib-only urllib, same as today, CONVENTIONS-compliant). Config selects backend **per role**
(embedder / chat tiers). No behavior change at landing; default stays `ollama`. This seam is the
whole reversibility story: rollback of any later phase is a config flip back, and it is also
what makes MLX a cheap later experiment (owner's 2026-07-22 point).

**P2 — the process manager + accounting** (§2.3, §2.4). Lands flag-off beside the untouched
`TwoSlotLoader`; the daemon keeps running Ollama until a role flips.

**P3 — the equivalence harness** (§2.5) + its measured report on the real fixture corpus.

**P4 — embedder cutover (first, deliberately).** The embedder is where the migration bites
hardest and risks least: the blob is portable (§2.1 E), equivalence is provable to 1e-5 (F),
the accounting win is largest (10 → 3.7 GB, C), and it is the corpus-critical path. Shadow-run
(both backends embedding the fixture set + a sample of live traffic compared offline), gate
pass, then owner flips `[embedding] backend = "llamacpp"` in `config/local.toml`. Rollback =
flip back; gate-proven vector agreement means no re-embed in either direction.

**P5 — chat tiers, per-tier** (router → routine → synthesis → stretch), each gated on golden +
drift, each reversible by flag. Requires upstream-convention GGUFs (V-B): owner-fetched, quant
matched to Ollama's (Q4_K_M lineage), placed locally; the core never fetches (§2.4). Ollama
retires only after all tiers flip and a deskcheck passes; until then it remains the standing
fallback.

**Version pinning:** the runtime is a pinned brew version (or vendored binary — parked); a bump
is a deliberate ops action = re-run §2.5 + re-check the SIGTERM wedge (V-H). Never auto-updated
— the exact property Ollama.app lacks.

### 2.7 The tier ledger (every mechanism, ranked honestly)

| mechanism | tier reached |
|---|---|
| residency = child process existence | 3 (kernel fact) + 2 (sole spawner) |
| no stale residency belief (f-0199 class) | 2 — the belief dict ceases to exist |
| embedder inside the books (f-0174) | 2 (only path is the gate) + 4 (ratchet) |
| budget refusal at spawn | 5 (arithmetic) + 4 (measured-budget test) |
| cancellation of a running job's compute | 3 (SIGKILL + waitpid) |
| stop-decision policy (when to escalate) | 5, stated as such |
| server egress: argv capability + --offline | 2, backed by 4 (argv + lsof ratchets) |
| server egress under plane principals | 3 — later, not claimed now |
| equivalence gate | 4 (point-in-time ratchet; not a monitor) |
| no client bypasses the seam | 4 (import ratchet), else convention |
| version pinning / re-gate on bump | 5 + protocol discipline; honest floor |

Nothing here reaches tier 1, and one row explains why nothing can: jetsam and process crash are
external actors that keep "resident set changed without our decision" representable. The gain
over today is uniform: every belief either stops existing (tier 2) or becomes a kernel-held
fact (tier 3), and what remains runtime-checked says so.

### 2.8 finding-0199's interim fix: mint separately, NOW

**Ruling this note proposes:** the interim reconcile is **not absorbed here** — it should be
minted as its own small builder plan immediately, because (a) it is cheap and independent of the
migration; (b) the breach lives on the crash-restart path and *the restart is imminent and
owner-gated right now* — the fresh supervisor will come up against an Ollama that has held
models across runs (the finding's own re-entry condition says "weigh before the restart");
(c) this note's durable fix (§2.3) replaces the loader entirely, and coupling a one-day guard
to a multi-plan migration is how the guard arrives late. Content: reconcile `_resident` against
`ps()` at construction and before `_check_ceiling`; unknown resident names (outside the
registry) are treated fail-closed as ceiling-consuming — refuse non-pinned loads until
reconciled or unloaded — and reported as *partial* accounting, never full. M2's reproduction
script shape (scratchpad, this session) is the acceptance test template.

### 2.9 Falsifiers (the owner ratifies falsifiers, not proofs)

- **Process-residency model** — *wrong if:* a model's memory outlives its process (RSS/Metal
  allocations after waitpid), or steady-state RSS diverges from the spawn-time budget by >10%
  (then budgets are declarations again — the f-0174 defect in new clothes; the reconcile loop
  must alarm). *Does not catch:* host-level pressure — V-F.
- **SIGKILL stops the burn** — *wrong if:* GPU busy persists > a few seconds after the child is
  reaped (powermetrics), i.e. Metal work outliving the process. *Does not catch:* a wedged
  *manager*; that is dn-supervision's lease layer.
- **Cancellation latency** — *wrong if:* client-side embed batches make cancel granularity
  exceed the batch budget (measured ~20 s at 256 inputs; V-E sizes batches so the bound holds).
- **Equivalence gate** — *wrong if:* any fixture text < 0.999 cross-runtime cosine, or
  `regressions()` non-empty → the migration STOPS at the current lane. *Does not catch:*
  drift after cutover from a version bump that skipped the re-gate — hence pinning (§2.6).
- **Egress posture** — *wrong if:* `lsof` shows any non-loopback socket in a serving
  llama-server, or a spawn argv ever contains a download flag.
- **Escalation contract** — *wrong if:* grace-then-SIGKILL still leaves a process (unkillable
  state), or clean idle SIGTERM stops being 0.25 s-fast (regression watch on bump).
- **Three-process arithmetic** — *wrong if:* V-A shows synthesis/stretch cannot fit even with
  the embedder stopped — then the ctx budgets or the tier lineup must change and the note
  returns to the owner.

### V-series (not settled by reading; each blocks the item that cites it)

- **V-A** — measure 27b (and 35b) under llama-server: upstream-GGUF bring-up time and true RSS
  at the role ctx. Blocks §2.3's synthesis/stretch policy numbers and the swap-latency bar.
  (Not measured this pass: the 14.4 GB free-RAM envelope forbade the big tiers.)
- **V-B** — source upstream-convention GGUFs for the chat lineup; verify quant parity with the
  Ollama tags and that b10090+ loads them. Blocks P5.
- **V-C** — `lsof` verification of loopback-only sockets across load + serve + `--offline`, on
  the pinned build. Grounds the §2.4 tier-4 ratchet.
- **V-D** — confirm no palace embed call can exceed ctx 8192 (chunker caps + query paths), and
  that the typed overflow error is surfaced loudly if one does.
- **V-E** — pin client-side embed batch size so cancel granularity ≤ the batch budget
  (dn-supervision §2.5's clock); measured: 256-input batch ⇒ ~20 s granularity.
- **V-F** — behavior under real memory pressure: what jetsam does to a 17 GB server and how the
  manager reports it (the honest tier-3 detection claim).
- **V-G** — wire `/slots` + `/metrics` into the supervision probes (NEW NOTE 1's instruments):
  the runtime finally *reports* residency and busyness instead of being believed.
- **V-H** — the SIGTERM-mid-request wedge: reproduce on the pinned build at graduation time,
  report upstream if present; until fixed, the grace default stays short and SIGKILL is the
  contract's teeth.

## 3. Consequences

**Plans this licenses (after ratification, via `/graduate`):** P1–P5 as separate session-sized
plans in dependency order, plus the P0 interim reconcile which should be minted *now* without
waiting for this note (§2.8). **finding-0191 applies — the write_scope partition is a
graduation-time decision:** the surfaces are `core/models/` (seam, manager, loader successor),
`config/` (schema: backend-per-role + budgets), `eval/` (the harness — *never*
`eval/golden/**` or `eval/golden.py`), `ops/lifecycle/` (daemon wiring, status render of
process residency), `scripts/palace.py` (enable path), and possibly `core/runtime.py`
(bootstrap wiring). Per-lane builder plans with disjoint scopes + one integrator plan owning
exactly the seam files, a named falsifier per hand-off.

**Findings this bears on:** folds finding-0174 (the embedder enters the books structurally,
§2.3) and finding-0199 (reproduced §2.1 B; durable fix §2.3; interim fix routed §2.8). Closes
dn-supervision's **V3** empirically (§2.1 A) and narrows its V4's scope (§2.4). Unblocks the
embedder-choice question (`embedding-space-specialization.md`) *after* the migration lands, per
the sequencing capsule.

**What remains open after this note** (completion-claims honesty): the note is draft — panel
(systems + security) then ratification; P0 unminted; P1–P5 unminted; V-A/V-B block the big-tier
and chat halves; the equivalence tolerance and the escalation grace default are owner calls at
ratification.

## 4. Wiring & enablement

**How it wires:** a `[runtime]` config section, schema'd in the config loader (unknown sections
are dropped silently — the bp-102/f-0174 lesson, so the schema IS the deliverable):
`embedding_backend = "ollama" | "llamacpp"`, per-tier `chat_backend` overrides, per-role
`ctx`/`budget_gb`, `server_binary` path + pinned build string (asserted at spawn),
`grace_s` for the SIGTERM→SIGKILL window. The process manager wires into the daemon's
component build; `status` renders process residency (pid, RSS vs budget, `/slots` busyness) in
place of today's belief-derived line; the equivalence harness is runnable standalone
(`uv run python -m eval.runtime_equivalence`) and is the gate artifact the deskcheck shows.

**What it takes to flip it on:** (a) P1–P3 land flag-off (defaults unchanged, Ollama serving);
(b) the harness run is deskchecked — the owner sees the measured worst-case cosine and the
golden report; (c) the owner flips `[runtime] embedding_backend = "llamacpp"` in
`config/local.toml` (P4), later per-tier `chat_backend` flips (P5); each flip is reversible in
place by flipping back, no re-embed either direction while the gate holds. Ollama is retired
only after all roles flip + deskcheck; until then it is the standing rollback.

## Parked decisions

- **Vendored binary vs pinned brew** for the runtime. Default: pinned brew formula + build
  string asserted at spawn. Re-entry: if brew's formula churn outpaces the re-gate cadence, or
  the SIGTERM wedge (V-H) needs a patched build.
- **Warm-spare worker processes** (spawn-ahead for swap latency). Default: no — one worker,
  stop-then-spawn, simplest kill semantics (the sandbox's discipline). Re-entry: V-A's measured
  cold-load, if it breaks the responsiveness bar.
- **MLX A/B.** Owner-parked (2026-07-22). Re-entry: after P1's seam lands, on the owner's read
  of MLX serving maturity.
- **Embedder always-on vs on-demand.** Default: always-on at 3.7 GB (it fits beside routine and
  the router; stop-for-synthesis policy per §2.3). Re-entry: V-A's synthesis arithmetic.
- **Attestation stamping of backend+build per embed run.** Default: yes if the existing record
  shape carries it without schema change; else a V at graduation. Re-entry: P3.

## Cross-references

Measured this pass (2026-07-25, session scratchpad scripts `m1_ollama_kill.sh`, `m2_repro.py`,
`m3_llama_server.sh`, `m3_equivalence.py`): Ollama 0.31.2; llama.cpp b10090 (7347430f4).
Code (at `941785d`): `core/models/loader.py:33,44-55,57-69,77-93` (belief dict, prospective,
ceiling, warm gate) · `core/models/ollama_client.py:78-80,97-104,116` (ps, embed without
num_ctx, stream=False) · `core/models/registry.py` · `core/sealing.py:69-108` (per-process
monkeypatch; native-extension caveat in its docstring) · `core/runtime.py:37-48` (seal-first
bootstrap) · `core/sandbox/runner.py:65-86` (subprocess+timeout+destroy precedent) ·
`core/ingest/sync.py:122` (attestor emit) · `config/defaults.toml:5-27,96-119,126-153,267-277`
(`[ollama]`, `[resources]`, `[code_ingest]`, `[embedding]`, `[[models]]`, σ bounds) ·
`eval/golden.py:26-32,98-131` (fixture paths, evaluate, regressions — foundation denylist,
read/run only).

Artifacts: `docs/brainstorms/local-model-runtime.md` (both capsules) ·
`docs/brainstorms/design-pass-routing.md:66-73,131` (NEW NOTE 2 / S5 — reconciled §1.1, not
edited) · `docs/design-notes/dn-supervision-and-liveness.md` (ladder; §2.5 escalation; §2.7
shared boundary; V3/V4) · `docs/findings/finding-0174.md` · `docs/findings/finding-0199.md` ·
oq-0035's ruling (`docs/inbox/owner-questions.md:1043-1068`) · `docs/tracks/ops.md`.
