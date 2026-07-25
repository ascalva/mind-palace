---
type: build-plan
id: bp-115
track: ops
status: ready
design_ref:
  - docs/design-notes/dn-local-model-runtime.md
contract: builder
write_scope:
  - core/models/inference.py
  - core/models/llama_server_client.py
  - core/models/server.py
  - core/models/__init__.py
  - core/ingest/embed.py
  - core/kernel/config/loader.py
  - config/defaults.toml
  - tests/unit/test_inference_seam.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 220k
  actual: null
depends_on: []
parallelizable_with: [bp-108, bp-109]
created: 2026-07-25
updated: 2026-07-25
links:
  - docs/findings/finding-0174.md
  - docs/brainstorms/local-model-runtime.md
re_entry: null
supersedes: null
superseded_by: null
warrant: docs/findings/finding-0174.md
---

# Build Plan — P1: the inference client seam (the whole reversibility story)

## 0. Mode & provenance

**P1 of `dn-local-model-runtime` §2.6**, verbatim: *"A backend-agnostic inference client protocol
(chat/embed/health) with two implementations: the existing `OllamaClient` and a
`LlamaServerClient` speaking the OpenAI-compatible surface… No behavior change at landing; default
stays `ollama`. **This seam is the whole reversibility story**: rollback of any later phase is a
config flip back, and it is also what makes MLX a cheap later experiment."*

⚑ **Nothing observable changes when this lands.** That is the acceptance bar, not a caveat. A P1
that alters a single embedding value has failed, because every later phase's rollback story rests
on this being a pure refactor.

Investigation and planning produced this; implementation proceeds item-by-item on owner approval.

## 1. Objective

Inference is reached through a backend-agnostic protocol with two implementations, selected per
role by config, with `ollama` as the default and no behavioural change.

### 1.2 Non-goals (explicit — see §9)

Not the process manager (bp-116), not any cutover (bp-118/bp-119), not the equivalence harness
(bp-117). **Not a model change** — owner-stated (`dn-local-model-runtime` §1.2, verbatim
2026-07-25). Not MLX, not vLLM (both owner-ruled). Not retiring `OllamaClient`.

## 2. Context manifest

Read in order, whole files before citing:

1. `docs/design-notes/dn-local-model-runtime.md` — **§2.1 E, F, G** (the measured ground:
   which blobs are portable, the equivalence numbers, llama-server's actual endpoints and error
   shapes), **§2.6 P1**, §2.4 (the seal boundary), §4 — the content spec
2. `core/models/ollama_client.py` — **whole file, 127 lines.** The surface being generalized
3. `core/models/server.py` — **whole file, ~50 lines.** `ModelServer.chat` `:32-43`
4. `core/ingest/embed.py` — **whole file, 41 lines.** `Embedder` `:17-34`, `build_embedder` `:36-41`
5. `core/kernel/config/loader.py:37-48` (`OllamaConfig`), `:109-115` (`EmbeddingConfig`),
   `:296-343` (`ModelConfig`, `Config`), `:350-359` (`_overlay`)
6. `config/defaults.toml:1-27` — the `[ollama]` section's voice and its two-timeout rationale
7. `CONVENTIONS.md` §Language — stdlib-only in the sealed core

**Does core already have this?** ⚑ **`Embedder` is ALREADY a backend-neutral facade.**
`core/ingest/embed.py:29-34` exposes `embed_documents` / `embed_query` and nothing else; only its
`client` field is concretely typed (`:19`). Everything above it in the system — the ingest lanes,
the librarian, the dreamer, the golden harness — already talks to `Embedder`, not to Ollama. **The
migration flows underneath a facade that already exists**; do not build a second one. (This is
also why `dn-supervision-and-liveness`'s worker protocol needs no ordering against this plan — the
worker takes an `Embedder`, whose surface is unchanged here.)

## 3. Investigation & grounding  <!-- Part A -->

- **Q1 — what belongs in the protocol?** §2.6 says chat/embed/health. Reading the client confirms
  the split: `chat` (`:107-127`), `embed` (`:97-104`) and `version` (`:70-72`) are *inference*;
  `ps` (`:78-80`), `load`/`unload` (`:83-94`) and `list_models` (`:74-76`) are **manager**
  operations that exist only because Ollama owns residency. Under §2.3 residency becomes child-
  process existence, so those four have **no llama.cpp counterpart** and must stay off the
  protocol. Putting them on it would force `LlamaServerClient` to implement four lies.
- **Q2 — ⚑ does this touch `core/models/loader.py`?** **No, deliberately.** The loader's client is
  used exclusively for `load`/`unload`/`ps` (`loader.py:85,91`), i.e. the manager operations Q1
  excludes. Leaving `loader.py` alone (a) keeps this plan off bp-107's surface, which is landing
  the finding-0199 interim reconcile on the same file, and (b) keeps it off bp-116's, which
  replaces the loader outright. **The loader stays `OllamaClient`-typed until bp-116 deletes the
  question.**
- **Q3 — how wide is the retrofit surface?** ⚑ **Almost zero, and the reason is a type-theory
  one.** Widening `Embedder.client` and `ModelServer.client` from a concrete class to a `Protocol`
  is **strictly more permissive**: every existing construction site and every test stub that
  satisfies `OllamaClient` also satisfies the protocol. `build_embedder`/`Embedder(` appear in 30+
  test files; **none should need editing**, and if one does, that is a signal the change was not
  purely a widening (§10).
- **Q4 — what does `LlamaServerClient` actually speak?** Measured, not documented
  (`dn-local-model-runtime` §2.1 G): `/v1/chat/completions` and `/v1/embeddings` (OpenAI-compatible,
  confirmed working), `/health` (503-while-loading → 200), `/slots` (`is_processing` ground truth),
  `/props`. Errors are **typed JSON** (`exceed_context_size_error` carrying
  `n_prompt_tokens`/`n_ctx`) rather than Ollama's opaque strings wrapped in `OllamaError`.
- **Q5 — may it use `requests`/`httpx`?** **No.** `core/models/ollama_client.py:1-8` states the
  rule: *"Stdlib-only by design: the sealed core must not import a network-capable third-party
  package (CONVENTIONS)."* `urllib` is permitted because the egress guard allows exactly the
  loopback endpoint. `LlamaServerClient` is bound by the same rule, and `dn-local-model-runtime`
  §2.6 P1 says so explicitly (*"stdlib-only urllib, same as today, CONVENTIONS-compliant"*).
- **Q6 — how is the backend selected?** §4: a `[runtime]` section with
  `embedding_backend = "ollama" | "llamacpp"` and per-tier `chat_backend` overrides. **Per role,
  not global** — that is what makes P4 (embedder only) a real, independently reversible step.
- **Q7 — will an unknown `[runtime]` section be silently dropped?** ⚑ **Yes, today.** `_overlay`
  (`core/kernel/config/loader.py:350-359`) merges by section name and `Config` (`:307-329`) has no
  catch-all, so a `[runtime]` block in `local.toml` with no dataclass simply vanishes. This is the
  bp-102 / finding-0174 lesson, and it is why §4 of the note makes the schema part of the
  deliverable rather than a follow-up. **Land the whole section, including keys bp-116/bp-118
  consume**, so it is never half-defined.
- **Q8 — where does the seal boundary sit?** Unchanged. §2.4: spawned local servers, never
  in-process bindings; the core talks loopback HTTP to a local inference process exactly as it does
  to Ollama today, and the client already binds to `127.0.0.1` literals so no DNS is involved
  (`config/defaults.toml:8`). **This plan does not move the boundary and must not appear to.**

**Additional risks or questions surfaced during reading:**

- ⚑ **The chat blobs are NOT portable** (§2.1 E): Ollama's `qwen3.5:2b/9b`, `qwen3.6:27b` fail to
  load upstream (`key qwen35.rope.dimension_sections has wrong array length; expected 4, got 3`).
  So `LlamaServerClient`'s **chat path cannot be exercised end-to-end against a real model in this
  plan** — only the embedder blob is portable. Item 3's acceptance must be honest about that:
  chat is tested against the wire contract, not against a loaded chat model. V-B (owner-sourced
  upstream GGUFs) is bp-119's blocker, not this plan's.
- `ops/lifecycle/{launcher,preflight}.py` and `scripts/watch.py` construct `OllamaClient` directly
  (`launcher.py:378,430,1092-1094`; `preflight.py:51-53`; `watch.py:32,41`). They are **deliberately
  left alone** — see §5. Routing them through a factory here would collide with bp-108's launcher
  edits for no benefit, since they use manager operations (Q1) anyway.

## 4. Reconciliation  <!-- Part B -->

- **`core/models/ollama_client.py:1-8`** — the module docstring, which asserts the stdlib-only rule
  as a property of *this client* → **cross-ref: extension.** The rule now binds a second client.
  Restate it once in `core/models/inference.py` (the protocol module) as a property of the seam,
  and cross-reference rather than duplicating the reasoning.
- **`core/ingest/embed.py:19`** — `client: OllamaClient` → **banner: correction**, small but
  load-bearing: the field's type was the last place the corpus pipeline named a vendor. Say in the
  commit that this is the seam that makes the runtime migration reversible.
- **`config/defaults.toml`** — a new `[runtime]` section → **cross-ref: extension**, written in the
  file's established voice: a comment explaining *why* each key exists, as `[ollama]:11-16` does
  for its two timeouts. ⚑ **Do not touch `[ollama]`** — it remains the default backend and its
  removal is bp-119's, after every role has flipped.
- **`docs/findings/finding-0174.md`** → **cross-ref: extension.** This plan does not fix the
  embedder's accounting (bp-116 does, structurally); it builds the seam that makes the fix
  possible. Link, do not close.

## 5. Write scope

`core/models/inference.py` (new) holds the protocol; `core/models/llama_server_client.py` (new)
the second implementation. `core/models/server.py`, `core/models/__init__.py` and
`core/ingest/embed.py` carry the annotation widening and the factory.
`core/kernel/config/loader.py` + `config/defaults.toml` carry the `[runtime]` schema.
`tests/unit/test_inference_seam.py` is new.

⚑ Deliberately OUT of scope, each for a stated reason:
- **`core/models/loader.py`** — manager operations only (§3 Q2); bp-107 is landing on it and
  bp-116 replaces it.
- **`ops/lifecycle/launcher.py`, `ops/lifecycle/preflight.py`, `scripts/watch.py`** — direct
  `OllamaClient` constructions that use manager operations. Migrating them here would collide with
  bp-108's launcher edits and buy nothing. bp-116 owns them when residency actually changes.
- **`eval/golden.py` and `eval/golden/**`** — foundation denylist; read and run, never write.
- Every design note, and every other foundation-denylist file.

## 6. Interfaces pinned inline

**The protocol — chat/embed/health only** (§3 Q1: manager ops are excluded on purpose):

```python
# core/models/inference.py
class InferenceClient(Protocol):
    """Backend-agnostic local inference. Implementations: OllamaClient (default) and
    LlamaServerClient. Deliberately EXCLUDES ps/load/unload/list_models — those are residency-
    manager operations that exist only because Ollama owns residency; under
    dn-local-model-runtime §2.3 residency becomes child-process existence and they have no
    counterpart. A protocol that included them would force one implementation to lie."""

    def embed(self, model: str, inputs: list[str], *,
              keep_alive: str | int | None = None) -> list[list[float]]: ...

    def chat(self, model: str, messages: list[Message], *,
             num_ctx: int | None = None, temperature: float | None = None,
             keep_alive: str | int | None = None, think: bool | None = None) -> str: ...

    def healthy(self) -> bool: ...
```

⚑ **The signatures above are `OllamaClient`'s exact current ones**
(`core/models/ollama_client.py:97-98` and `:107-109`), copied verbatim so the existing
implementation satisfies the protocol with **zero
edits to its method bodies**. `healthy()` is the one addition: Ollama's form is `version()`
(`:70-72`) returning non-empty; llama-server's is `/health` returning 200 (§2.1 G).

**The measured llama-server surface** (`dn-local-model-runtime` §2.1 G — measured on b10090,
7347430f4, not read from docs):

```
POST /v1/chat/completions     OpenAI-compatible, confirmed working
POST /v1/embeddings           OpenAI-compatible, confirmed working; dims 2560 correct
GET  /health                  503 while loading -> 200 when ready
GET  /slots                   is_processing — busyness ground truth
GET  /props                   loaded model properties
errors                        typed JSON: exceed_context_size_error {n_prompt_tokens, n_ctx}
```

**The `[runtime]` config section — the WHOLE section, including keys bp-116/bp-118 consume**
(§3 Q7: a half-defined section is silently dropped):

```python
@dataclass(frozen=True)
class RuntimeConfig:
    embedding_backend: str = "ollama"        # "ollama" | "llamacpp"; default UNCHANGED
    chat_backend: dict[str, str] = ...       # per-tier overrides; empty = ollama everywhere
    server_binary: str = ""                  # llama-server path; "" = not configured
    pinned_build: str = ""                   # asserted at spawn (bp-116); "" = unpinned
    embed_ctx: int = 8192                    # §2.3: right-sized from the model default 40960
    grace_s: float = 5.0                     # SIGTERM -> SIGKILL window (bp-116)
```

**The stdlib-only rule, verbatim** (`core/models/ollama_client.py:3-6`) — it binds the new client
identically:

> *"Stdlib-only by design: the sealed core must not import a network-capable third-party package
> (CONVENTIONS). `urllib` is network-capable, but every request here targets the loopback Ollama
> endpoint, and the egress guard (`core.sealing`) permits exactly that and blocks everything else."*

**What must NOT change** — `Embedder`'s public surface (`core/ingest/embed.py:22-34`), because 30+
test files and every ingest lane depend on it:

```python
    @property
    def dim(self) -> int: ...
    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...
    def embed_query(self, text: str) -> list[float]: ...
```

## 7. Items

Blast radius: a type-only change → a new isolated client → the config selector → the factory.

### Item 1 — the protocol, and `OllamaClient` satisfies it unchanged

- **Objective:** the seam exists and the existing client fits it without a single edited method.
- **Files:** `core/models/inference.py`, `core/models/__init__.py`,
  `tests/unit/test_inference_seam.py`
- **Acceptance test:** mypy accepts `OllamaClient` where `InferenceClient` is required, with **no
  change to any `OllamaClient` method body**; `healthy()` is the only added method. The full green
  gate passes: `ruff`, `scripts/check_imports.py`, mypy Tier-2 floor 0 and the tests baseline
  **exactly 69**, `ops.type_gate`, `uv run --extra dev pytest`.
- **Falsifier:** ⚑ *`OllamaClient`'s signatures had to change to fit the protocol.* Then the
  protocol was designed for llama.cpp and retrofitted to Ollama, and every existing caller is at
  risk. The protocol must be *read off* the working client (§6), not designed against it.
- **Invariant(s) it must not violate:** stdlib-only; no manager operations on the protocol (§3 Q1);
  `core/` imports nothing outside `core/` (the import firewall).
- **Touches stored data?** No. **Parallelizable?** No. **Depends on:** none.

### Item 2 — annotations widen; nothing else moves

- **Objective:** `Embedder` and `ModelServer` depend on the protocol, not on a vendor.
- **Files:** `core/ingest/embed.py`, `core/models/server.py`, carried by the suite
- **Acceptance test:** ⚑ **no test file is edited.** §3 Q3: widening a concrete annotation to a
  Protocol is strictly more permissive, so all 30+ files touching `build_embedder`/`Embedder(`
  must pass unedited. `Embedder`'s public surface (§6) is byte-identical.
- **Falsifier:** ⚑ *any existing test needs editing.* That is the signal the change was not a pure
  widening — investigate rather than edit the test (§10).
- **Invariant(s) it must not violate:** `build_embedder`/`build_model_server` keep their signatures
  and default behaviour; `ModelServer.chat` still passes `num_ctx` from the model config
  (`server.py:36-42`).
- **Touches stored data?** No. **Parallelizable?** No. **Depends on:** Item 1.

### Item 3 — `LlamaServerClient`

- **Objective:** a second implementation exists, speaking the measured OpenAI-compatible surface.
- **Files:** `core/models/llama_server_client.py`, `tests/unit/test_inference_seam.py`
- **Acceptance test:** against a **local llama-server the test starts itself** (or a stub HTTP
  server when no binary is configured): `/v1/embeddings` returns 2560-dim vectors for the portable
  embedder blob; `healthy()` reflects the 503→200 transition; a typed
  `exceed_context_size_error` surfaces as a **specific, catchable error carrying `n_ctx` and
  `n_prompt_tokens`**, not a flattened string.
- **Falsifier:** ⚑ *the typed error is flattened into a generic message.* §2.1 G names typed errors
  as one of the concrete wins over Ollama's opaque strings; discarding them at the client boundary
  throws away the reason for migrating. ⚑ Also: *the chat path is claimed as verified.* §3
  (additional risks) — the chat blobs do not load upstream, so chat is tested against the wire
  contract only. Saying otherwise in the journal is a false completion claim.
- **Invariant(s) it must not violate:** stdlib `urllib` only; `127.0.0.1` literals, never a
  hostname (no DNS — the seal permits the loopback literal); the client **never spawns a server**
  (that is bp-116's process manager; a client that spawns is two responsibilities and breaks the
  argv-as-capability story).
- **Touches stored data?** No. **Parallelizable?** Yes, with Item 2. **Depends on:** Item 1.

### Item 4 — `[runtime]` config and the per-role factory

- **Objective:** a backend is selected per role by config, defaulting to today's behaviour.
- **Files:** `core/kernel/config/loader.py`, `config/defaults.toml`, `core/ingest/embed.py`,
  `core/models/server.py`, `tests/unit/test_inference_seam.py`
- **Acceptance test:** the whole `[runtime]` section round-trips through `load_config` with a
  `local.toml` overlay (proving §3 Q7's silent-drop does not apply); with defaults, `build_embedder`
  returns an Ollama-backed `Embedder` and **every behaviour is identical to before this plan**;
  setting `embedding_backend = "llamacpp"` returns a llama-server-backed one.
- **Falsifier:** ⚑ *a `[runtime]` key in `local.toml` is silently ignored.* That is finding-0174's
  mechanism reproduced in the plan built to end it. Assert the round-trip explicitly — a test that
  only constructs `RuntimeConfig()` directly would pass while the overlay path is broken.
- **Invariant(s) it must not violate:** `[ollama]` is untouched; defaults produce byte-identical
  behaviour; **no flip is performed** — flipping is the owner's, at bp-118.
- **Touches stored data?** No. **Parallelizable?** No. **Depends on:** Items 2, 3.

## 8. Math carried explicitly

N/A — no mathematical object is implemented. ⚑ The *values* this seam carries are load-bearing
(embedding vectors), but this plan must not change one: any change is a `dn-local-model-runtime`
§2.5 equivalence concern and is bp-117's to measure, not this plan's to introduce.

## 9. Non-goals

- **No cutover, no flip.** Defaults stay `ollama`. The flip is the owner's (bp-118/bp-119).
- **No process manager, no spawning** — bp-116. A client that spawns is out of scope (§7 Item 3).
- **No model change, no re-embed, no σ recalibration** — all owner-stated or `[INFERENCE]` non-goals
  in `dn-local-model-runtime` §1.2.
- **No MLX, no vLLM** — both owner-ruled (§1.2).
- **No retiring `OllamaClient`** — it is the standing rollback until every role flips.
- **No manager operations on the protocol** (§3 Q1).
- **No touching `core/models/loader.py`** (§3 Q2).

## 10. Stop-and-raise conditions

- ⚑ **Item 1's falsifier fires** — `OllamaClient`'s signatures must change to fit the protocol ⇒
  **STOP.** Re-derive the protocol from the working client instead; a protocol shaped around the
  new backend puts every existing caller at risk for a phase that is supposed to change nothing.
- ⚑ **Item 2's falsifier fires** — an existing test needs editing ⇒ **STOP and investigate before
  editing it.** The widening is supposed to be strictly permissive; a red test means something
  else moved, and editing the test would hide it.
- **A third-party HTTP package proves necessary** ⇒ **STOP.** CONVENTIONS forbids it in the sealed
  core, and §2.4's whole argument is that the inference boundary stays exactly where it is.
- **The measured endpoints do not behave as §2.1 G records** on the installed build ⇒ raise. The
  note's ground was measured on b10090 (7347430f4); a different build is a different fact, and V-H
  already flags a re-check at graduation time.
- Any blessing transition — never.

## 11. Parked decisions

| Decision | Default recorded | Re-entry condition |
|---|---|---|
| `healthy()` on the protocol | yes — both backends need it | never; both need it |
| `/slots` busyness | not on the protocol | V-G wires it into the probes (bp-116) |
| streaming | not on the protocol | a caller needs token streaming |
| chat verification | wire-contract only | V-B: upstream GGUFs arrive (bp-119) |

**Rejected alternatives, per row:**

- **`healthy()`.** Rejected: *reuse `version()`* — llama-server's readiness is a 503→200 transition
  during load (§2.1 G), which a version string cannot express; a caller that treats "responded" as
  "ready" would dispatch into a loading server.
- **`/slots`.** Rejected: *add it now* — it is an *observability* surface for the supervision
  probes (V-G), not an inference operation, and Ollama has no equivalent. Adding it would repeat
  the Q1 mistake of forcing one implementation to lie.
- **Streaming.** Rejected: *include it* — the palace is non-streaming today
  (`ollama_client.py:116`, `"stream": False`) and §2.1 A's cancellation measurement was taken in
  exactly that mode. Adding an unused mode would widen the protocol and the test matrix for
  nothing.
- **Chat verification.** Forced by §2.1 E, not chosen: Ollama's chat blobs fail to load upstream
  (`qwen35` arch, `rope.dimension_sections` 3 vs 4). Re-entry is V-B, owner-sourced GGUFs.

## 12. Dependency & ordering summary

Items: **1 → {2, 3} → 4.** Items 2 and 3 are independent of each other.

**`depends_on: []`** — this plan is the runtime wave's root and blocks nothing else in the
supervision wave.

**`parallelizable_with: [bp-108, bp-109]`** — genuinely disjoint (`core/models/` +
`core/ingest/embed.py` + config here; `ops/lifecycle/` + `scheduler/` there).

⚑ **NOT parallelizable with bp-110.** Both edit `core/kernel/config/loader.py` and
`config/defaults.toml` — bp-110 lands `[scheduler]`, this lands `[runtime]`. Disjoint *sections*,
same *files*; concurrent worktrees would conflict. Since bp-110 depends on bp-108 and bp-109, the
natural order runs this plan alongside those and finishes it before bp-110 starts. **The config
loader is the wave's second contended file, and naming it here is the finding-0191 discipline:
write_scope is not a partition of the diff.**

⚑ **Cross-note note, worth stating once because it is the thing a naïve partition would get
wrong:** `dn-supervision-and-liveness` and `dn-local-model-runtime` overlap on `core/models/`, and
one might expect the worker split to have to wait for this seam. **It does not** — the supervision
worker takes an `Embedder` (§2, "Does core already have this?"), whose surface this plan leaves
byte-identical. The runtime migration flows *underneath* that facade. That is why the two waves
run concurrently rather than in series.
