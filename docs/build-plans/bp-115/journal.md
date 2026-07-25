---
type: journal
plan: bp-115
started: 2026-07-25
updated: 2026-07-25
---

# Journal — bp-115 (P1: the inference client seam)

Minted 2026-07-25 (session-48) by `/graduate`. **Built 2026-07-25** by a delegated builder in a
worktree branched from `origin/main` @ `7b37453`.

## Status in one paragraph (read this first)

All four items are **implemented and committed**; the code is complete and the design is
plan-faithful. The build is **not green**, and every red is traceable to exactly three one-line
changes in three files that bp-115's `write_scope` does not contain. They are written out
verbatim in `finding-0200` (two of them) and `finding-0201` (one). Nothing else is owed. Do not
re-derive: read those two findings, land the three lines under a plan that can reach them, and
the gate is expected green with no further code change.

## Pre-build notes (kept — every one of them held)

- ⚑ **Nothing observable may change.** Held: 2054 tests passed with **zero existing test files
  edited**, and `Embedder`'s public surface is byte-identical.
- ⚑ **`Embedder` is ALREADY a backend-neutral facade.** Confirmed; only its `client` annotation
  moved. No second facade was built.
- ⚑ **Read the protocol OFF the working client.** Done — `embed`/`chat` are `OllamaClient`'s
  current signatures copied verbatim. Item 1's falsifier did NOT fire: no `OllamaClient` signature
  needed to change.
- ⚑ **`ps`/`load`/`unload`/`list_models` are NOT on the protocol.** Held, and ratcheted by a test
  (`test_manager_operations_are_absent_from_the_protocol`).
- ⚑ **Do not touch `core/models/loader.py`.** Untouched.
- ⚑ **The chat path cannot be verified against a real model.** Stated in the client's module
  docstring, in the test's docstring, and here. It is tested against the WIRE CONTRACT only.

## What landed, by item

### Item 1 — the protocol (`core/models/inference.py`, `core/models/__init__.py`)

`InferenceClient` is a `runtime_checkable` `Protocol` with exactly `embed` / `chat` / `healthy`,
signatures copied verbatim from `core/models/ollama_client.py:97-98,107-109`. `Message` is imported
from `core.kernel.constitution`, not from `ollama_client` — the two `Message` TypedDicts are
kept deliberately interchangeable (see both docstrings), and taking the neutral one keeps the
seam from naming a vendor in its own signature. `core/models/server.py` already relied on that
interchangeability, so it is proven in the checked region, not assumed.

`build_inference_client(config, *, tier=None)` lives here too (the per-role selector, §4 of the
note): `tier=None` is the embedding role, a tier name reads `chat_backend`. Implementations are
imported *inside* the function so the protocol module does not drag them into every importer.

**Status: code complete; acceptance NOT met** — `OllamaClient` does not satisfy the protocol
because `healthy()` has no home (finding-0200a).

### Item 2 — the widening (`core/ingest/embed.py`, `core/models/server.py`)

`Embedder.client` and `ModelServer.client` are now `InferenceClient`. `build_embedder` goes
through the selector; `build_model_server` still constructs `OllamaClient` concretely and says why
inline (the same object is the loader's residency client, and per-tier `chat_backend` dispatch
needs one client per tier — a shape change belonging to bp-118/P5, not to the seam).

⚑ **`ModelServer.version()` was not pinned by the plan and had to be re-homed.** `version()` is
not on the protocol (`healthy()` replaces it — a version string cannot express llama-server's
503→200 loading state), so `self.client.version()` no longer type-checks. It now reads
`self.loader.client.version()`, i.e. the residency client, which §3 Q2 deliberately leaves
`OllamaClient`-typed. `build_model_server` hands the same object to both fields, so the return
value is identical. This is the one place the plan under-specified and I resolved rather than
parked; it is annotated inline in `core/models/server.py`.

⚑ **Item 2's falsifier FIRED — once — and §10's STOP was honoured**: I investigated and did not
edit the test. `tests/e2e/test_ollama_live.py:46` asks a residency question
(`core.models.client.list_models()`) through the inference handle. Full investigation and the
one-line remedy are in **finding-0201**; the short version is that the widening is *correct* and
the call site was always reaching through the wrong handle. It is the only such site in the repo.

### Item 3 — `LlamaServerClient` (`core/models/llama_server_client.py`)

`/v1/embeddings`, `/v1/chat/completions`, `/health`, stdlib `urllib` only, `127.0.0.1` literal,
never spawns (source-level ratchet in the tests). Embeddings are ordered by the server's own
`index` rather than by arrival — order preservation is a contract the corpus depends on.

`exceed_context_size_error` becomes `ContextOverflowError` carrying `n_prompt_tokens` and `n_ctx`
**as integers**; an unrecognised error body degrades to `LlamaServerError` rather than being
mistaken for an overflow. Both branches are tested.

`keep_alive` and `num_ctx` are accepted for protocol compatibility and deliberately ignored, each
with the reason inline: `keep_alive` is an Ollama residency timer and residency here is process
existence; `num_ctx` is fixed at spawn (`-c`), and an over-long prompt is a loud typed error
rather than a silent truncation. `think` maps to `chat_template_kwargs.enable_thinking` — that
mapping is **unverified** against a loaded model (V-B) and says so in the docstring.

**Status: code complete; blocked from green only by the import-firewall allowlist**
(finding-0200b).

### Item 4 — `[runtime]` (`core/kernel/config/loader.py`, `config/defaults.toml`)

`RuntimeConfig` lands whole — `embedding_backend`, `chat_backend`, `server_binary`,
`pinned_build`, `embed_ctx`, `grace_s` — including the keys bp-116/bp-118 consume, because a
half-defined section is silently dropped by the section-name overlay. Every default is today's
behaviour; `[ollama]` is untouched; **no flip is performed**.

Item 4's falsifier is exercised properly: the round-trip test drives the REAL overlay path
(`load_config()` with no argument, with `_LOCAL` and `LEVERS_OVERLAY` monkeypatched into
`tmp_path` so the owner's actual `local.toml` cannot affect the assertions), not a direct
`RuntimeConfig()` construction — which is precisely the test that would have passed while the
overlay stayed broken.

`[runtime]` is **appended at the end of `config/defaults.toml`** on purpose: no line numbers move,
which keeps `dn-local-model-runtime`'s `Cross-references` citations valid and leaves bp-110's
`[scheduler]` section a clean rebase. `RuntimeConfig` is **not** re-exported from
`core/kernel/config/__init__.py` (out of write_scope, and not needed — `ChatConfig`,
`CodeIngestConfig` and `ExhaustConfig` set the same precedent; import it from
`core.kernel.config.loader`).

**Status: code complete and green on its own.**

## Gate — measured, not asserted

Six legs, run separately, at commit `HEAD` of this worktree:

| leg | result |
|---|---|
| `uv run ruff check .` | **PASS** — "All checks passed!" |
| `uv run python scripts/check_imports.py` | **FAIL** — 2 violations, both finding-0200b |
| `uv run mypy core agents eval ops scheduler scripts` | **FAIL** — 2 errors, both finding-0200a |
| `uv run mypy` (argless) | **70**, not the pinned 69. The +1 is finding-0201, exactly |
| `uv run python -m ops.type_gate` | **PASS** — membership OK, bare-ignore scan OK |
| `uv run pytest -q` | **4 failed / 2074 passed / 15 skipped** in 569s — itemised below |

The four pytest failures, each attributed:

1. `tests/integrity/test_import_firewall.py::test_core_has_no_forbidden_imports` — finding-0200b
2. `tests/integrity/test_import_firewall.py::test_allowlist_files_exist_and_are_the_only_network_importers`
   — finding-0200b (same missing allowlist entry; this one fails in both directions by design)
3. `tests/unit/test_inference_seam.py::test_ollama_client_satisfies_the_protocol` — finding-0200a.
   Mine, and deliberately not skipped: it IS §7 Item 1's acceptance criterion.
4. `tests/unit/test_core_self_containment.py::test_core_imports_nothing_outside_core` — ⚑ **fails
   on a clean tree too** (20 pre-existing violations in `core/dreaming/shadow.py`,
   `core/effect_proposal.py`, `core/factory/factory.py`, `core/ingest/code_corpus.py`,
   `core/interface.py`, `core/ops_view.py`, `core/reference_view.py`, `core/sensing.py`,
   `core/temporal/spine.py` — **none** in a file this plan touches). The finding-0103 ratchet the
   green gate deselects by policy. Not attributable here.

⚑ **Zero existing tests broke.** Baseline before any edit was 2054 passed; it is now 2074 passed,
i.e. +20 = my 21 new tests less the one that is red by design. Item 2's falsifier fired
**statically only** (mypy), never at runtime — see finding-0201.

## Findings filed

- **`finding-0200`** (`spec-defect`, route builder) — the `write_scope` omits
  `core/models/ollama_client.py` (needs the 3-line `healthy()`) and `ops/import_lint.py` (needs
  the `NETWORK_ALLOWLIST` entry for the new client). Both patches written out verbatim. This is
  the third instance of finding-0191's pattern in this wave.
- **`finding-0201`** (`discovery`, route builder) — Item 2's falsifier fired at
  `tests/e2e/test_ollama_live.py:46`; the investigation §10 demands, plus the one-line remedy.

Neither is a `blocker`: the session proceeded and finished the plan's code.

## Decisions I made that the plan did not pin (all annotated inline)

1. **`Message` comes from `core.kernel.constitution`**, not `core.models.ollama_client`, so the
   neutral seam does not name a vendor in its own signature. Safe because the two TypedDicts are
   maintained interchangeable and `ModelServer` already relies on it.
2. **`ModelServer.version()` reads `self.loader.client.version()`** — see Item 2 above.
3. **No `[runtime]` port key.** `LlamaServerClient` takes `port` (default 8080, llama-server's
   own) at construction. Ports are per-PROCESS and the note's residency model is three concurrent
   servers, so assigning them is the process manager's job (bp-116) — which is why neither the
   note's §4 list nor the plan's §6 `RuntimeConfig` has one. Do not add a global port key.
4. **`build_model_server` does not use the selector.** One `client` field cannot serve per-tier
   backends; that shape change is bp-118/P5's. `chat_backend` is schema'd and read by
   `chat_backend_for()`, so it is not half-defined — the §3 Q7 requirement is met.
5. **`chat_backend` is a `dict`, not this file's usual tuple/frozenset** — pinned as
   `dict[str, str]` by §6. Consequence noted in the dataclass docstring: `Config` is no longer
   hashable. Verified nothing hashes it (no `lru_cache` takes a `Config`; `get_config` caches on
   no arguments).
6. **`think` → `chat_template_kwargs.enable_thinking`** on the llama-server chat path. The
   documented upstream mechanism, but **unverified** against a loaded model. Re-entry: V-B.

## What is explicitly NOT claimed

- **The chat path is not verified.** No upstream-loadable chat blob exists (§2.1 E). It is
  exercised against a stub speaking the wire contract, nothing more.
- **The measured endpoints were not re-checked against a live llama-server.** No binary is
  configured on this machine (`server_binary = ""`), and §10's "the measured endpoints do not
  behave as §2.1 G records ⇒ raise" therefore had no opportunity to trigger. V-H's re-check at
  bring-up still stands, un-discharged.
- **No memory win was realised.** This plan builds the seam that makes finding-0174's fix
  possible; the fix itself is structural and bp-116's. finding-0174 is linked, not closed.
- **No flip was performed.** Every default is `ollama`.

## Owed at seal (orchestrator, not the builder)

- Land finding-0200's two patches and finding-0201's one line under a plan that can reach those
  files, then re-run all six gate legs. Expected: ruff pass, check_imports pass, Tier-2 mypy 0,
  argless mypy **69**, type_gate pass, pytest with only the pre-existing self-containment ratchet
  red (deselected by the green gate).
- `finding-0174` is cross-referenced by this work, **not closed** — bp-116 closes it structurally.
- A deskcheck cannot be offered for this plan on its own: its acceptance is "nothing changed",
  which is shown by the gate, not by a demo.
