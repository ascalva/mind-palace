---
type: finding
id: finding-0226
status: open
created: 2026-07-26
updated: 2026-07-26
links:
  - tests/e2e/test_dream_v2_live.py            # the newly-red live test (NOT in bp-107's write_scope)
  - core/models/loader.py                       # :247 _check_ceiling — the refusal site
  - config/defaults.toml                        # :26 usable_ram_gb=24.0, :121 embedder, :146 synthesis
  - docs/build-plans/bp-107/plan.md             # the correct tightening that surfaced this
  - docs/findings/finding-0174.md               # the corrected arithmetic 23.0 + 10.0 = 33.0
  - docs/findings/finding-0199.md               # the measured breach, worse than filed
  - docs/inbox/owner-questions.md               # oq-0050 — "wire the dreamers live", just ruled
ftype: discovery
origin_plan: orchestrator
route: orchestrator
resolution: null
---

# The live synthesis-tier dream path is now REFUSED by the memory ceiling whenever the embedder is
# warm — 29.7 GB > 24.0 GB. bp-107 is right; the consequence lands on oq-0050's "wire them live".

## What

The full suite on `main` @ `5d42b65` reads **2 failed, 2249 passed, 12 skipped in 955.61s**. One
failure is the known finding-0103 INTENTIONAL-RED ratchet (`test_core_imports_nothing_outside_core`),
which the green gate deselects by policy. **The second is new and was not on any expected-failure
list:** `tests/e2e/test_dream_v2_live.py::test_dream_v2_synthesizes_grounded_themes_live`.

Re-run in isolation, it fails in 5.31s with `[GROUNDED]` `core/models/loader.py:247`:

```
core.models.registry.MemoryCeilingError: would use 29.7 GB > usable budget 24.0 GB
  (qwen3.5:2b, qwen3.6:27b + 10.0 GB measured non-registry)
```

The arithmetic, all four terms verified against live state rather than the registry:

| term | value | source |
|---|---|---|
| `qwen3.5:2b` (router, **pinned**) | 2.7 GB | `config/defaults.toml` registry |
| `qwen3.6:27b` (synthesis) | 17.0 GB | `config/defaults.toml:146` |
| `qwen3-embedding:4b` (**measured non-registry**) | 10.0 GB | `ollama ps`, live |
| **total** | **29.7 GB** | vs `usable_ram_gb = 24.0` (`:26`) |

⚑ **This test is not skipped.** Its `skipif` guard (`_models_present`, `:30-39`) checks that the
embedding and synthesis models are pulled — they are, and Ollama is reachable — so it RUNS, and
therefore it is a live assertion about this machine, not a dormant fixture.

## This is bp-107 working, not bp-107 breaking

⚑ **The refusal is CORRECT and the finding is not against bp-107.** bp-107 replaced a ceiling that
*believed the registry* with one that *measures residency*, and `_external_gb = 10.0` is exactly that
measurement — the embedder charged in the GB dimension only, never against `max_resident_models`
(`loader.py:247` docstring). finding-0199, corrected by measurement at bp-107's merge, records that
the **pre-change loader left 32.3 GB resident and ADMITTED a real 29.7 GB**. That admitted load is
precisely this one. The old code let this run and quietly breached non-negotiable #8; the new code
refuses it. **The test went red because the system stopped lying, and the test still assumes the lie.**

`[GROUNDED]` The file was last touched by bp-090 (`df97ecd`), long before bp-107, and `e2e` appears
nowhere in bp-107's `write_scope` — so the builder could not have carried it, and did not miss it.
This is the finding-0223 shape again: **a correct tightening leaves a red in a file the tightening
plan was not allowed to touch.** Second instance in three days; see "Why it matters" §3.

## Why it matters

**1. ⚑ It is a live constraint on the ruling the owner just made.** oq-0050 was answered
2026-07-26 — *wire the dreamers live* — and what it owes next is "a scoped plan for the live entry
point". **This finding is a hard input to that plan.** On this machine, right now, the synthesis-tier
dream path cannot load while the embedder is warm. A wiring plan written without this would ship a
dreamer that raises `MemoryCeilingError` in production on its first real pass, and the failure would
read as a model bug rather than a scheduling one.

**2. The condition is TRANSIENT, which makes it a scheduling problem, not a capacity problem.**
`ollama ps` shows the embedder resident with `UNTIL: 4 minutes from now` — it evicts itself. Without
it, 2.7 + 17.0 = **19.7 GB, comfortably under 24.0**. So the dreamer is not too big for this machine;
it is too big *concurrently with a warm embedder*. Three levers, none free, and the choice is a
design act rather than a builder's:
  - **Order the work** — the dreamer evicts the embedder (or waits for its keep-alive to lapse)
    before requesting synthesis. Cheapest; makes dream latency depend on embedder activity.
  - **Shrink the embedder's residency** — ⚑ it is 10.0 GB largely because it is loaded at
    `CONTEXT 40960`. A 4b embedding model does not inherently cost 10 GB. Whether that context is
    needed is a real question and nobody has asked it.
  - **Raise `usable_ram_gb`** — ⚑ the one to be most suspicious of. 24.0 is a
    non-negotiable-#8 number (~20–24 GB usable), not a tuning knob, and raising it to make a test
    pass is precisely the "thresholds tuned to manufacture signal" inversion.

**3. The gate's expected-failure set silently changed from ONE to TWO, and nothing enforces it.**
Recent seals (bp-108, bp-115) attest "**1 failed** — the finding-0103 ratchet". That sentence is now
false on `main`, and it became false without any gate noticing, because the expected-failure set
lives in **prose inside seal notes** rather than in a deselect list or a marker. Any future seal
copying the established wording would attest a green that is not there. ⚑ This is finding-0222's
thesis in a third costume: *a note is not a control.*

## Re-entry condition

Nothing is parked and no build is blocked — bp-110 is unaffected (it touches neither the loader nor
the dream path, and its `worker_mode` ships `inproc`).

Re-entry is at **the oq-0050 wiring plan**, which must pin the ordering lever explicitly in §6 rather
than leave a builder to discover the ceiling at runtime, and must carry this finding as a warrant.
Until then the correct reading of `test_dream_v2_live` is **"expected red, cause known and recorded
here"** — not "flaky", and not to be fixed by widening the budget.

## Routing

`discovery` → **orchestrator**. Three decisions, none a builder's: which lever resolves the
embedder/synthesis contention; whether the embedder's 40960 context is intentional; and whether the
expected-failure set becomes a mechanism (a deselect list or an `xfail(strict=True)` marker) instead
of prose in seal notes. The third is the one that generalises — it is the same defect class as
finding-0222 and finding-0223, and it is the cheapest of the three to build.
