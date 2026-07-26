---
type: finding
id: finding-0205
status: open
created: 2026-07-25
updated: 2026-07-25
links:
  - docs/build-plans/bp-115/plan.md                    # §7 Item 2 falsifier, §10 STOP condition
  - tests/e2e/test_ollama_live.py                      # :46 — the single call site
  - core/models/server.py                              # ModelServer.client, now protocol-typed
  - core/models/loader.py                              # where residency questions belong (§3 Q2)
  - docs/findings/finding-0204.md                      # the sibling write_scope gap
ftype: discovery
origin_plan: bp-115
route: builder
resolution: null
---

# bp-115 Item 2's falsifier fired — and the investigation says the widening is right

## What

§7 Item 2's acceptance is *"⚑ no test file is edited"*, and its falsifier is *"⚑ any existing
test needs editing. That is the signal the change was not a pure widening — investigate rather
than edit the test (§10)."* §10 escalates it: **STOP and investigate before editing it.**

It fired, exactly once, and I stopped. Widening `ModelServer.client` from `OllamaClient` to
`InferenceClient` produces one new mypy error, in a file bp-115's `write_scope` does not contain:

```
tests/e2e/test_ollama_live.py:46: error: "InferenceClient" has no attribute "list_models"
    [attr-defined]
```

```python
# tests/e2e/test_ollama_live.py:46
    if PINNED not in core.models.client.list_models():
        pytest.skip(f"{PINNED} not pulled")
```

**The investigation the plan demands, and its result: this is not a hidden regression — it is
the widening doing its job.** `list_models` is one of the four residency-MANAGER operations §3 Q1
keeps off the seam on purpose ("a protocol that included them would force one implementation to
lie"). This line asks a *catalog* question — "is the pinned model pulled?" — through the
*inference* handle. Under the seam that question belongs to the loader's client, which §3 Q2
deliberately leaves `OllamaClient`-typed. The very next assertion in the same test already goes
that way:

```python
    assert PINNED in core.models.loader.resident_models()      # :52
```

At runtime `ModelServer.client` and `ModelServer.loader.client` are the *same object*
(`build_model_server` passes one `OllamaClient` to both), so the fix is a rename, not a
behaviour change.

Three facts bound the blast radius:

1. **It is the only site in the repository.** A scan for `models.client` / `server.client` across
   `core/ agents/ ops/ eval/ scheduler/ scripts/ edge/ tests/` returns this one line.
2. **§3 Q3's claim held exactly where it was made.** That analysis was about
   `build_embedder`/`Embedder(` — "30+ test files, none should need editing". None did:
   2054 passed with zero test edits. `ModelServer.client` was simply never enumerated as a
   reachable surface, and it has precisely one reach.
3. **The default gate never sees it.** The test is `@pytest.mark.live` behind a `skipif` on a
   running Ollama, so `pytest -q` stays unaffected. The cost is static only: the argless
   `uv run mypy` tests baseline moves **69 → 70** until the line is fixed.

## Why it matters

The falsifier earned its place — it converted an invisible coupling into a compile error. That is
the good outcome, and the record should say so plainly rather than let a one-line test edit
disappear into a diff. If a later reader sees only "widened an annotation, edited a test", they
lose the actual finding: **one caller was using the inference handle to ask a residency question,
and the seam is what made that legible.** bp-116 replaces the loader outright; whoever does that
work needs to know this call site exists and which side of the split it belongs on.

It also raises the tests-baseline number, which is a pinned gate value (69). A moved baseline
that nobody explains is how a ratchet quietly stops ratcheting.

## The exact change required (one line, one file)

`tests/e2e/test_ollama_live.py:46` — route the manager question to the manager's client:

```python
    if PINNED not in core.models.loader.client.list_models():
```

No behaviour changes (same object), the test's meaning is unchanged, and the tests baseline
returns to **69**. It is worth a short comment on the line saying *why* it goes through the
loader, so the next reader does not "simplify" it back.

## Re-entry condition

Parked on `tests/e2e/test_ollama_live.py` becoming writable under a plan. Until then bp-115's
argless-mypy tests baseline is **70, not 69**, and this finding is the whole difference. The
default `pytest -q` gate is unaffected. Verify at re-entry by running `uv run mypy` argless and
confirming the tail reads 69 again.

## Routing

`codebase` → the builder resolves. Blocked here only by `write_scope`, like finding-0204; the two
should be discharged together, since both are one-line edits in files bp-115 cannot reach and
both must land before the plan's own acceptance can be claimed.
