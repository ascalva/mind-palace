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

**Complete and GREEN.** All four items are implemented, all four §7 acceptance criteria are met,
and the six-leg gate passes on the merged tree (main @ `510714b`, bp-108 included). The scope gap
that parked Items 1/2/4 is resolved: the owner granted the `write_scope` widening (plan §5,
amended session-49), the three lines finding-0204 and finding-0205 prescribed landed **under the
plan**, and the gate went green exactly as the pre-verification predicted. Nothing is owed except
the orchestrator's closure of those two findings at seal.

⚑ **Findings were renumbered at integration** (`0c70100`): this journal's `finding-0204` and
`finding-0205` were filed as 0200/0201 in the build session. Both worktrees independently minted
a 0200 and main already had a different one. Only the new ids are used below.

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
because `healthy()` has no home (finding-0204a).

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
one-line remedy are in **finding-0205**; the short version is that the widening is *correct* and
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
(finding-0204b).

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

## Gate — FINAL, on the merged tree (session-49, the resolution)

Six legs, run separately on `main` merged in (bp-108's supervisor lock included), after the three
owed lines landed. **This table supersedes the build-session table below**, which is kept because
it is the evidence finding-0204 rests on.

| leg | result |
|---|---|
| `uv run ruff check .` | **PASS** — "All checks passed!" (exit 0) |
| `uv run python scripts/check_imports.py` | **PASS** (exit 0) — "audited loopback exceptions: core/models/llama_server_client.py, core/models/ollama_client.py, core/sealing.py" |
| `uv run mypy core agents eval ops scheduler scripts` | **PASS** — "Success: no issues found in 258 source files" (exit 0) |
| `uv run mypy` (argless) | **"Found 69 errors in 20 files (checked 550 source files)"** — exactly the pinned tests baseline. Exit 1 is expected: this leg always exits 1 at the baseline |
| `uv run python -m ops.type_gate` | **PASS** (exit 0) — membership OK, bare-ignore scan OK |
| `uv run pytest -q` | **1 failed, 2109 passed, 15 skipped in 502.00s** |

The single failure is the expected one:
`tests/unit/test_core_self_containment.py::test_core_imports_nothing_outside_core`, the labelled
**INTENTIONAL RED** ratchet (finding-0103, owner ruling) that the green gate deselects by policy.
⚑ Its count is **20**, unchanged from the pre-build baseline, and **not one of the 20 is a file
bp-115 touched** (they are in `core/dreaming/shadow.py`, `core/effect_proposal.py`,
`core/factory/factory.py`, `core/ingest/code_corpus.py`, `core/interface.py`, `core/ops_view.py`,
`core/reference_view.py`, `core/sensing.py`, `core/temporal/spine.py`). Checked explicitly because
this plan writes into `core/`, so a moved count would have been mine.

⚑ The pytest exit code was captured directly (`> file 2>&1; echo $?`), **not** through a `tail`
pipe, which would have reported the pipe's status instead of the suite's.

### What the three landed lines were

1. `core/models/ollama_client.py` — `healthy()` **added** (`return bool(self.version())`). No
   existing body touched, so Item 1's falsifier still does not fire.
2. `ops/import_lint.py` — `NETWORK_ALLOWLIST` gains `core/models/llama_server_client.py` with the
   same one-line rationale style the other two carry; the docstring's "the two audited
   loopback/seal modules" becomes three, and its honesty clause moves with it.
3. `tests/e2e/test_ollama_live.py` — `core.models.client.list_models()` →
   `core.models.loader.client.list_models()`, with a comment saying why so it is not "simplified"
   back.

### Acceptance now met

- **Item 1** — `OllamaClient` satisfies `InferenceClient`; mypy accepts it where the protocol is
  required (Tier-2 clean), and `test_ollama_client_satisfies_the_protocol` passes. **Met.**
- **Item 2** — unchanged and still met; the argless baseline is back to 69, which was the whole of
  finding-0205's cost. **Met.**
- **Item 3** — the client is enrolled on the audited allowlist; `check_imports.py` and both
  integrity tests pass. **Met** (chat still wire-contract only — that limit is permanent until
  V-B, not a parked item).
- **Item 4** — unchanged and still met. **Met.**

---

## Gate — the build session (superseded, kept as finding-0204's evidence)

Six legs, run separately, at the build session's HEAD **before** the write_scope amendment:

| leg | result |
|---|---|
| `uv run ruff check .` | **PASS** — "All checks passed!" |
| `uv run python scripts/check_imports.py` | **FAIL** — 2 violations, both finding-0204b |
| `uv run mypy core agents eval ops scheduler scripts` | **FAIL** — 2 errors, both finding-0204a |
| `uv run mypy` (argless) | **70**, not the pinned 69. The +1 is finding-0205, exactly |
| `uv run python -m ops.type_gate` | **PASS** — membership OK, bare-ignore scan OK |
| `uv run pytest -q` | **4 failed / 2074 passed / 15 skipped** in 569s — itemised below |

The four pytest failures, each attributed:

1. `tests/integrity/test_import_firewall.py::test_core_has_no_forbidden_imports` — finding-0204b
2. `tests/integrity/test_import_firewall.py::test_allowlist_files_exist_and_are_the_only_network_importers`
   — finding-0204b (same missing allowlist entry; this one fails in both directions by design)
3. `tests/unit/test_inference_seam.py::test_ollama_client_satisfies_the_protocol` — finding-0204a.
   Mine, and deliberately not skipped: it IS §7 Item 1's acceptance criterion.
4. `tests/unit/test_core_self_containment.py::test_core_imports_nothing_outside_core` — ⚑ **fails
   on a clean tree too** (20 pre-existing violations in `core/dreaming/shadow.py`,
   `core/effect_proposal.py`, `core/factory/factory.py`, `core/ingest/code_corpus.py`,
   `core/interface.py`, `core/ops_view.py`, `core/reference_view.py`, `core/sensing.py`,
   `core/temporal/spine.py` — **none** in a file this plan touches). The finding-0103 ratchet the
   green gate deselects by policy. Not attributable here.

⚑ **Zero existing tests broke.** Baseline before any edit was 2054 passed; it is now 2074 passed,
i.e. +20 = my 21 new tests less the one that is red by design. Item 2's falsifier fired
**statically only** (mypy), never at runtime — see finding-0205.

### The three owed lines were VERIFIED, not assumed

"Land three lines and it goes green" is a claim, so I measured it instead of asserting it. `git
archive HEAD` into a throwaway tree under the session scratchpad (outside the repo — no repo file
was touched and `write_scope` was not stretched), the three patches from finding-0204 /
finding-0205 applied there, `uv sync --extra dev`, then the same six legs:

| leg | verification copy |
|---|---|
| `ruff check .` | PASS |
| `scripts/check_imports.py` | **PASS** — "audited loopback exceptions: core/models/llama_server_client.py, core/models/ollama_client.py, core/sealing.py" |
| `mypy core agents eval ops scheduler scripts` | **Success: no issues found in 257 source files** |
| `mypy` (argless) | **69** — exactly the pinned tests baseline |
| `python -m ops.type_gate` | PASS |
| `pytest tests/integrity/test_import_firewall.py tests/unit/test_inference_seam.py` | **25 passed** |

The full-suite run in that copy shows 10 failures, and ⚑ **9 of them are artifacts of the
verification harness, not of the code**: `git archive` produces a tree with no `.git`, so
`test_code_ingest_wiring.py` and `test_temporal_view_live.py` die on
`subprocess.CalledProcessError: Command '['git', 'rev-parse', '--show-toplevel']' returned
non-zero exit status 128`. The tenth is the pre-existing self-containment ratchet. **None of the
three blocking failures survives the patch**, which is the thing that needed proving.

So the residual risk on the owed lines is not "will it work" but only "will someone write them".

⚑ **The pre-verification was accurate.** It predicted Tier-2 mypy clean, argless mypy 69,
check_imports pass, and the three blocking failures gone. The real merged tree delivered exactly
that — the only difference is source-file counts (257→258, 548→550) and the pass count
(2074→2109), both from bp-108 merging in between.

## Findings filed

- **`finding-0204`** (`spec-defect`, route builder) — the `write_scope` omits
  `core/models/ollama_client.py` (needs the 3-line `healthy()`) and `ops/import_lint.py` (needs
  the `NETWORK_ALLOWLIST` entry for the new client). Both patches written out verbatim. This is
  the third instance of finding-0191's pattern in this wave.
- **`finding-0205`** (`discovery`, route builder) — Item 2's falsifier fired at
  `tests/e2e/test_ollama_live.py:46`; the investigation §10 demands, plus the one-line remedy.

Neither is a `blocker`: the session proceeded and finished the plan's code.

⚑ **Both are RESOLVED IN CODE as of session-49, but neither is closed here** — a builder may not
edit an existing finding; the orchestrator closes them at seal. The resolution to record against
each: finding-0204 → the owner granted the `write_scope` widening (plan §5) and both patches
landed under the plan, exactly the remedy the finding itself prescribed and the re-entry through
the artifact chain finding-0191 requires; finding-0205 → the one-line fix landed and the argless
mypy tests baseline is back to **69**, which was the entirety of its cost.

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

- ~~Land finding-0204's two patches and finding-0205's one line~~ — **DONE session-49**, under the
  amended `write_scope`. The final six-leg gate is at the top of this journal.
- **Close `finding-0204` and `finding-0205`** (resolutions drafted under "Findings filed"). The
  builder may not edit a finding; this is the orchestrator's at seal.
- `finding-0174` is cross-referenced by this work, **not closed** — bp-116 closes it structurally.
  Nothing here reduced the embedder's 10.0 GB footprint; P1 built the seam that makes the
  structural fix possible.
- A deskcheck cannot be offered for this plan on its own: its acceptance is "nothing changed",
  which is shown by the gate, not by a demo. The first deskcheckable artifact in this wave is
  bp-117's equivalence report.
- Flip `status` to `complete` — owner/orchestrator's, never a builder's.

## Where the next builder picks up

bp-116 (the process manager) is the direct successor and inherits three things from here, all
already written down rather than needing re-derivation:

1. **The port question.** `LlamaServerClient(port=...)` is constructor-injected with a default of
   8080 precisely so the manager can assign a port per process; `[runtime]` deliberately has no
   port key (journal decision 3).
2. **The call site finding-0205 found.** `core/models/loader.py` is the manager's to replace, and
   `tests/e2e/test_ollama_live.py` reaches its client for `list_models` — that reach must move
   with the loader.
3. **The schema is already there.** `server_binary`, `pinned_build`, `embed_ctx` and `grace_s`
   are landed, defaulted and documented in `config/defaults.toml`; bp-116 consumes them without
   touching the config loader.
