---
type: journal
plan: bp-107
started: 2026-07-26
updated: 2026-07-26
---

# Journal — bp-107 (the memory ceiling stops guarding a belief)

## SEAL — 2026-07-26 (delegated builder, worktree `agent-a24ae15774d56e3ea`, base `7941da1`)

**Status.** All three items complete, gate fully green, ceiling verified against the live Ollama
read-only. `_check_ceiling` now refuses on what Ollama is *actually* holding: the corrected
finding-0174 arithmetic (`23.0 + 10.0 = 33.0` vs `usable_ram_gb = 24.0`) is **REFUSED** where the
pre-bp-107 loader admitted it at 23.0. One finding filed (finding-0220, `spec-fidelity`, resolved
in-build). Plan left `in-progress` and unpushed for the orchestrator.

### Completed

**Item 1 — `reconcile()` reads what Ollama actually holds.** `core/models/loader.py`.
`ReconcileReport` is exactly the four fields §6 pins, and `complete` is built only through
`ReconcileReport.measure(...)`, so Item 1's falsifier (*"reports `complete=True` while `unknown` is
non-empty"*) is **unreachable by construction**, not merely untested. `reconcile()` partitions
`ps()` three ways: registry-costable → `_resident` (the two-slot books, now measured); the
configured embedder at its **measured** 10.0 GB → `_external_gb`; everything else → `_unknown`
(uncostable). It never raises — a probe failure degrades to today's belief with `reconciled=False`
and deliberately does *not* clear `_unknown`/`_external_gb`/`_resident` (an unreachable Ollama is
not evidence about residency, and keeping the last measurement is the fail-closed direction).
Acceptance test evidence — `tests/unit/test_loader_reconcile.py`: a `ps()` returning a known name +
the embedder + a foreign name gives `known_gb == 2.7 + 10.0`, `unknown == (FOREIGN,)`,
`complete is False`; an empty `ps()` is the one `complete is True` case; a raising `ps()` gives
`reconciled=False` with no exception at construction *or* on an explicit call.

**Item 2 — the ceiling refuses on measurement, and the stale early-return dies.** `ensure()` now
calls `reconcile()` **before** the idempotence early-return (killing false-resident) and before
`_check_ceiling` (killing false-absent). All three reproduced phases are tests, and each asserts
twice over — the loader's books *and* what the fake server really holds afterwards, because the
defect was never that the arithmetic was wrong but that it was about the wrong world.

**Item 3 — the moved surface.** All five carried test files switched to a hermetic client. This was
not cosmetic: **Ollama is live on this machine (0.31.2)** and the carried tests passed only because
`ollama ps` happened to be empty at that moment. Measured, with anything warm:
`test_ceiling_refuses_breaching_load` **errors on its first line** (`would use 12.7 GB > usable
budget 5.0 GB`) and the FSM oracle **diverges** (`refused=True` vs `would_breach=False`) — because
`_check_all_transitions` computes `would_breach` from `cfg` alone and is structurally blind to
residency the config does not describe. The retrofit is additive in exactly the direction Item 3's
falsifier demands: the stubs gained a `ps()`; **not one assertion was removed, weakened, or
retargeted** — the only change in each file is which client object the loader is built with, plus a
docstring saying why. Side effect: the loader test surface went from 16.10 s to 1.92 s (no loopback
probes).

### The falsifier, run

Item 2's ⚑ falsifier is *"the measured breach still passes the guard."* Ran the three phases plus
the fail-closed rule against the **stashed pre-bp-107 loader** to confirm the new tests are
discriminating rather than merely green:

| phase | pre-bp-107 loader | post |
|---|---|---|
| (i) false-absent | `books=[] gb=0` while `ps()` held 2 | books show both / 9.3 GB |
| (ii)a the reproduced breach | `unloads=[]`, really held 2b+9b+stretch = **32.3 GB** vs 24.0 | `unloads={2b,9b}`, held `[stretch]` = 23.0 |
| (ii)b guard-pass on a real breach | **ADMITTED**; really held 2b+embedder+27b = **29.7 GB** vs 24.0 | **`MemoryCeilingError`** at 29.7 > 24.0 |
| (iii) false-resident | `loads_issued=[]` after external eviction | the needed load is issued |
| fail-closed | admitted a non-pinned load beside an uncostable name | refused; pinned still admitted |

Every phase fails on the old code. Note (ii)a: the live repro filed 25.7 GB, but the fake-server
ground truth shows the old path really left **32.3 GB** resident — worse than filed, because
`ensure` also never evicted the 9b.

### Can the ceiling still refuse breaching work? Yes — strictly more than before

Verified end-to-end against the **live** Ollama, read-only (`GET /api/ps` only; no load, no unload,
no model touched, so neither the daemon nor the ceiling was disturbed). With the embedder really
resident, pure accounting now gives: router ADMIT · routine ADMIT · **synthesis REFUSE (27.0 >
24.0)** · **stretch REFUSE (33.0 > 24.0)**. That last line is the orchestrator's corrected
arithmetic exactly — `23.0 + 10.0 = 33.0` against `usable_ram_gb = 24.0` — and the pre-bp-107 loader
admitted it. Two tiers moved from ADMIT to REFUSE; none moved the other way.

### In-flight

Nothing. Working tree is committed; the plan is deliberately left `in-progress` (the builder does
not flip to `complete`) and **not pushed**.

### Next action

Orchestrator: review the diff (read-map below), then (a) rule on **finding-0220 ruling 1** — the
scoped-vs-blanket pinned exemption, a one-function change if the owner meant the blanket reading;
(b) discharge the pre-existing *"Owed at seal"* item below (banner-correct finding-0199's stale
§"Status of the evidence"); (c) file bp-107 into `docs/DESKCHECK-QUEUE.md`; (d) flip to `complete`.
**Sequencing reminder** (`finding-0199`, `bp-115/plan.md:133`): bp-107 must merge **before** bp-116
is spawned — both land on `core/models/loader.py`.

### Open questions

- **finding-0220** (`spec-fidelity`, `route: builder`, resolved in-build): bp-107 states its ceiling
  rules three times and two phrasings would have weakened the guard. All three resolved toward more
  enforcement, per the orchestrator's stop-and-raise instruction. (1) *"The pinned model is never
  refused"* — resolved as scoped to the fail-closed rule, **not** a blanket exemption from the
  arithmetic; the blanket reading is undetectable by the FSM property test, which is why it is
  written down. (2) Item 2's *"phase (ii) now RAISES"* is not literally achievable — the 25.7 GB
  state stops being a *breach* rather than starting to *raise*, because the eviction the arithmetic
  assumed now actually happens; forcing a raise would mean reshaping `_prospective`, which is the
  FSM test's own oracle (§10's third stop condition). Substance discharged two ways instead.
  (3) `max_resident_models` counting is unspecified for the measured non-registry consumer —
  resolved as a GB-only charge, since reinterpreting that knob is `dn-local-model-runtime` §2.3's
  job (§9's first non-goal).
- **No blocker, nothing parked.** No owner-level question was hit, so no criterion was parked.
- **finding-0174 stays open by design** (§4 cross-ref: *extension*, not closure). bp-107 makes the
  invisible consumer's cost **visible to the guard**; it does not re-cost the registry. The declared
  weights-only `resident_gb` constants are untouched. Per finding-0174's own triage that closes at
  **bp-118's** seal, and only if the embedder role actually flipped.

### Context-manifest delta

Read beyond §2's list, all load-bearing:
- `scheduler/supervisor.py:30-90` — confirmed Item 2's compatibility invariant: `tick` catches
  `MemoryCeilingError` and defers with `f"ceiling: {e}"`, so type and message shape both survive
  (pinned by a test). Also confirmed `warm: bool = True` — **no production caller passes
  `warm=False`**, which is what makes gating the probe on `warm` safe.
- `core/models/inference.py` — settles that the loader keeps `client: OllamaClient` concretely: the
  `InferenceClient` protocol *deliberately excludes* `ps`/`load`/`unload`, so there was no protocol
  to widen and no temptation to add one.
- `core/models/server.py`, `ops/lifecycle/launcher.py:467`, `scripts/watch.py:94` — the three
  production loader construction sites. All now probe at construction; none needed an edit, because
  `reconcile()` cannot raise.
- `core/kernel/config/loader.py:66-68,125-128,342-348` — `ResourceConfig`, `EmbeddingConfig` (no
  `resident_gb`, confirming the embedder is permanently unknown), `ModelConfig`.
- `pyproject.toml` `[tool.ruff]` / `[tool.mypy]` / `[tool.pytest]` — `E,F,I,B,UP` (so `BLE` is not
  selected), the exactly-69 tests baseline, and `pythonpath = ["."]`.
- `tests/quality/test_diffusion_clusterer.py:19` — the precedent for importing a helper from a
  sibling test module, which is how `FakeOllama` is shared without `tests/fixtures/` (out of scope).

Proved irrelevant: nothing in §2 was wasted. `config/defaults.toml` was read for the numbers only
and is deliberately unedited (§5, §9).

### Notes for bp-116 (the durable replacement)

- `_MEASURED_NON_REGISTRY_GB` is keyed by model name **on purpose**: the mechanism is **context, not
  weights** (the same embedder blob is 10.0 GB at Ollama's default ctx 40960 and 3.69 GB under
  `llama-server` at 8192), so a `resident_gb` added to config would have been the wrong shape. The
  3.69 GB figure is deliberately *absent* from the table — a `llama-server`-hosted embedder never
  appears in `/api/ps`, so it is bp-116/bp-118's number for accounting this loader will not be doing.
- Two structures here should NOT be carried forward as-is: `_external_gb` exists only because the
  embedder is outside the registry, and `_unknown` exists only because `ps()` returns names. §2.3
  dissolves both (a spawned process is costed at spawn, by definition).
- `tests/fixtures/` is `FakeOllama`'s natural home; it was outside bp-107's `write_scope`, so the
  fake lives in `tests/unit/test_loader_reconcile.py` and is imported from there. Worth relocating
  whenever a plan legitimately owns that path.

```read-map
docs/findings/finding-0220.md:32: START HERE — the three rulings, and why each losing reading fails silently
core/models/loader.py:52: the embedder carve-out: MEASURED 10.0 GB @ ctx 40960, and why it is not a config resident_gb
core/models/loader.py:94: ReconcileReport.measure — Item 1's falsifier made unreachable by construction
core/models/loader.py:149: reconcile() — the three-way partition; never raises, degrades fail-closed
core/models/loader.py:227: _check_ceiling — why the external floor is a GB charge and NOT a max_resident_models count
core/models/loader.py:252: _refuse_uncostable — the fail-closed rule, and the SCOPE of the pinned carve-out (ruling 1)
core/models/loader.py:278: ensure() — the ordering that is the whole fix, and why warm=False does not probe
tests/unit/test_loader_reconcile.py:170: phase (ii)a — the breach becomes UNREACHABLE (real evictions), not merely refused
tests/unit/test_loader_reconcile.py:194: phase (ii)b — the guard now REFUSES a real breach it used to admit, 29.7 > 24.0
tests/unit/test_loader_reconcile.py:234: phase (iii) — the stale early-return dies; the needed load is really issued
tests/unit/test_loader_reconcile.py:285: the embedder carve-out keeps worker loads available (the anti-brick test)
tests/property/test_loader_fsm.py:12: why the FSM enumeration needs a guaranteed-empty world, and that the properties are untouched
```

+15 new tests (5 worth reading, listed above); 5 carried test files retrofitted mechanically
(client object + docstring only, zero assertion changes) — counted, not listed.

### Gate

| leg | result |
|---|---|
| `ruff check .` | All checks passed |
| `scripts/check_imports.py` | OK — core imports no zone or networking module |
| `mypy core agents eval ops scheduler scripts` | **0 errors** (258 files) |
| `mypy` (tests baseline) | **exactly 69** in 20 files (551 checked) — unchanged |
| `ops.type_gate` | Tier-2 membership OK · bare-ignore scan OK |
| `pytest` (green gate) | **2117 passed, 11 skipped, 21 deselected, 0 failed** |
| loader surface specifically | `test_loader_reconcile.py` **15 passed** · `test_models.py` + `test_loader_fsm.py` **7 passed** · the four integration files **17 passed** = **39 passed** (15 new + 24 carried) |

## Follow-through
- **Built?** Yes, all three items. `reconcile()` + `ReconcileReport` + the fail-closed rule + the
  measured-carve-out table in `core/models/loader.py`; 15 acceptance tests reproducing
  finding-0199's three live phases; five carried test files retrofitted with zero assertion loss.
- **Wired / delivered (or why dormant)?** **Wired, and there is no flag** — deliberately. The fix is
  on the accounting path itself: `__post_init__` reconciles at construction and `ensure()` reconciles
  before every `_check_ceiling`, so all three production construction sites
  (`core/models/server.py:62`, `ops/lifecycle/launcher.py:467`, `scripts/watch.py:94`) get it with no
  edit and no config key. A guard behind an off-by-default switch would not be a guard (non-negotiable
  #8), and there is nothing to turn on later. Verified live, read-only, against Ollama 0.31.2.
- **Does a consumer use it?** Yes: `Supervisor.tick` is the real consumer and is unchanged —
  it catches `MemoryCeilingError` and defers the job (`scheduler/supervisor.py:72-74`); the type and
  message shape are pinned by a test. The refusals now fire on measurement instead of belief. The
  *reporting* half has no consumer yet: `ReconcileReport.complete` is exposed via
  `TwoSlotLoader.last_reconcile` and **nothing renders "partial"** — by design, since core does not
  own presentation (§11), and `ops/lifecycle/launcher.py` is out of scope. That is bp-107 §11's
  recorded re-entry (*"a caller ships that ignores the flag"*), not an oversight.
- **Track state (what remains on this track)?** bp-107 is the *interim* guard and nothing more. On
  the `dn-local-model-runtime` track: bp-115 `complete`, **bp-107 now built (this plan)**, and
  **bp-116 / 117 / 118 / 119 remain `proposed`** — the durable fix (§2.3, residency = child-process
  existence) deletes `_resident` and this whole class. finding-0199 closes when this merges;
  **finding-0174 does not** — it closes at bp-118's seal, and only if the embedder role actually
  flipped. bp-107 is **ready to deskcheck**, not done: DONE ≠ sealed, and the owner's verdict is the
  third gate.
- **Opened a new track/finding?** One finding, no new track: **finding-0220** (`spec-fidelity`,
  resolved in-build, `route: builder`) — bp-107 states its ceiling rules three times and two
  phrasings would have weakened the guard; all three resolved toward more enforcement and annotated
  at the code sites. Ruling 1 (the scoped-vs-blanket pinned exemption) is flagged for the seal rather
  than buried: it is a judgement about an inviolable-kernel item and a one-function change to revisit.

Minted 2026-07-25 (session-47) by `/graduate` on `dn-local-model-runtime` §2.8, which rules this
out of the migration wave and asks for it separately and immediately. **Not started.**

## Pre-build notes for whoever picks this up

- **The warrant is MEASURED, not argued.** finding-0199 was reproduced live during the runtime
  design pass — all three phases, including a `_check_ceiling` **pass at 23.0 ≤ 24.0 against a
  true prospective 25.7 GB**. Item 2's falsifier is that exact case. If it still passes, nothing
  shipped.
- **The brick risk is the thing to be careful about.** The embedder is absent from the registry
  entirely, so it is *always* an unknown name. A naïve fail-closed rule refuses every non-pinned
  load on any system that has ever embedded. §6 pins the carve-out; §10 makes "the pinned model
  would be refused" a STOP.
- **The retrofit trap is pre-widened, not discovered.** Constructing a `TwoSlotLoader` will now
  imply a client answering `ps()`, so five existing test files are already in `write_scope` per
  the graduate skill's rule (findings 0071/0072/0075/0084). **Grep before editing** — §3 Q6
  records that the code does not settle which of the four integration files build a loader
  directly.
- **This plan is expected to be superseded**, and that is fine: `dn-local-model-runtime` §2.3
  deletes `_resident` outright when residency becomes child-process existence. bp-107 buys
  correctness for the interval.

## Owed at seal (orchestrator, not the builder)

finding-0199's §"Status of the evidence" still reads *"code-traced, NOT empirically reproduced."*
That is now false — correct it with a banner. A builder may not edit an existing finding, so it is
recorded here rather than done.
