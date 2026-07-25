---
type: build-plan
id: bp-107
track: ops
status: proposed
design_ref:
  - docs/design-notes/dn-local-model-runtime.md
contract: builder
write_scope:
  - core/models/loader.py
  - tests/unit/test_models.py
  - tests/property/test_loader_fsm.py
  - tests/unit/test_loader_reconcile.py
  - tests/integration/test_cron.py
  - tests/integration/test_supervisor.py
  - tests/integration/test_chat_sensor_wiring.py
  - tests/integration/test_research_cron.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 110k
  actual: null
depends_on: []
parallelizable_with: []
created: 2026-07-25
updated: 2026-07-25
links:
  - docs/findings/finding-0199.md
  - docs/findings/finding-0174.md
  - docs/design-notes/dn-local-model-runtime.md
re_entry: null
supersedes: null
superseded_by: null
warrant: docs/findings/finding-0199.md
---

# Build Plan — the memory ceiling stops guarding a belief (finding-0199's interim reconcile)

## 0. Mode & provenance

Corrective, and **deliberately not part of the runtime migration wave**.
`dn-local-model-runtime` §2.8 rules this out of its own wave and asks for it to be minted
separately and immediately, for three reasons: it is cheap and independent of the migration; the
breach lives on the **crash-restart path and the restart is imminent and owner-gated right now**;
and the note's durable fix (§2.3, residency = child-process existence) replaces `TwoSlotLoader`
entirely — coupling a one-day guard to a multi-plan migration is how the guard arrives late.

**finding-0199 is no longer code-traced. It was REPRODUCED LIVE**, all three phases, during the
runtime design pass (2026-07-25). This plan closes a measured breach of an inviolable kernel item,
not a suspected one.

## 1. Objective

`_check_ceiling` refuses on what Ollama is *actually* holding, not on what this process happens to
have loaded.

### 1.2 Non-goals (explicit — see §9)

Not replacing `TwoSlotLoader` (that is `dn-local-model-runtime` §2.3, a later wave), not adding a
`duckdb`-style shim, not fixing finding-0174's *declared-footprint* error (the embedder's 10.0 GB
real vs 2.5 GB declared — measured this session, out of scope here), not touching `ensure_tier`'s
routing, and not changing `OllamaClient` (`ps()` already exists and is sufficient).

[INFERENCE] These are inferred from right-sizing against §2.8's stated content, not from an owner
statement. Read them at the gate — a wrong non-goal fails silently forever (finding-0150).

## 2. Context manifest

Read in order, whole files before citing:

1. `docs/findings/finding-0199.md` — the warrant; its §"Status of the evidence" is now superseded
   by the live reproduction (see §3 Q1)
2. `docs/design-notes/dn-local-model-runtime.md` §2.8 — **the content spec for this plan**; also
   §2.1 (the measured ground) and §2.3 (the durable replacement this must not pre-empt)
3. `core/models/loader.py` — whole file, 97 lines; `_resident` `:33`, `_prospective` `:44-55`,
   `_check_ceiling` `:57-69`, `ensure` `:72-94`
4. `core/models/ollama_client.py:78-81` — `ps()`, the only reconciliation source
5. `core/models/registry.py:21-35` — `by_name` / `by_tier` / `pinned`
6. `config/defaults.toml` `[resources]` — `usable_ram_gb`, `max_resident_models`
7. `tests/unit/test_models.py` + `tests/property/test_loader_fsm.py` — **the surface this moves**
8. `docs/findings/finding-0174.md` — the sibling defect; this plan makes its cost *visible*,
   it does not fix it

**Does core already have this?** `ps()` exists (`ollama_client.py:78`) and is the one reconciliation
source — **do not add a second probe.** `Registry.by_name` already costs a known model. The gap is
purely that nothing calls `ps()` from the accounting path: today its ONLY caller in the repository
is `ops/lifecycle/launcher.py:1094`, a cosmetic status line.

## 3. Investigation & grounding  <!-- Part A -->

- **Q1 — is the breach real?** **Yes, reproduced live 2026-07-25** (runtime design pass, M2), all
  three phases: (i) *false-absent* — a fresh loader believes 1 model / 6.6 GB while `ollama ps`
  holds 2; (ii) *guard-pass on a real breach* — `_check_ceiling` **passed** at 23.0 ≤ 24.0 while
  the true prospective total was **25.7 GB > 24.0**; (iii) *false-resident* — a 0.0 ms stale
  early-return skipped a load that was actually needed after an external eviction.
- **Q2 — why does the eviction loop not help?** `ensure` `:83-86` iterates
  `[n for n in self._resident if n not in prospective]`. On a fresh process `_resident` is empty,
  so the loop body never runs and nothing is ever unloaded from Ollama. `loader.py:83`.
- **Q3 — how does the stale belief survive?** `ensure` `:77-78` early-returns on
  `if name in self._resident`, before any probe. `loader.py:77`.
- **Q4 — what invalidates the books from outside?** `default_keep_alive = "30m"`
  (`config/defaults.toml:10`) — Ollama's own timer evicts a worker; the loader never learns.
  Pinned models load with `keep_alive = -1` (`loader.py:88`) and are therefore **never**
  timer-evicted, so they persist across supervisor restarts.
- **Q5 — is `ps()` sufficient to cost the resident set?** **No, and this is the load-bearing
  limitation.** `ps()` returns **names only** (`ollama_client.py:79-81`). A name absent from the
  registry has no `resident_gb` and cannot be costed. That is why §2.8 requires the fail-closed
  rule and the "partial, never full" reporting — the fix must not *claim* completeness it lacks.
- **Q6 — what breaks when the loader gains a probe at construction?** Every test that builds a
  `TwoSlotLoader` with a stub client that has no `ps()`. Six files reference the loader
  (`tests/unit/test_models.py`, `tests/property/test_loader_fsm.py`,
  `tests/integration/{test_cron,test_supervisor,test_chat_sensor_wiring,test_research_cron}.py`).
  **The code does not settle which of the four integration files construct a loader directly** —
  the builder must grep before editing; all six are pre-widened into `write_scope` per the
  graduate skill's retrofit rule (findings 0071/0072/0075/0084).

**Additional risks surfaced:** the embedder is **not in the registry at all**
(`core/models/registry.py` never mentions it; `[embedding]` declares no `resident_gb`), so it will
always be an unknown name. Under the fail-closed rule that would refuse every non-pinned load on a
system that has ever embedded. **§6 pins the carve-out; get this wrong and the daemon bricks.**

## 4. Reconciliation  <!-- Part B -->

- **`core/models/loader.py:43`** — the section comment *"accounting (pure-ish, no Ollama calls)"*
  → **banner: correction.** It stops being true: reconciliation calls `ps()`. Say so, and say why
  the purity was load-bearing (it kept `_check_ceiling` testable without a client) and how the
  new shape preserves that (reconciliation is a separate, injectable step; `_check_ceiling` stays
  pure over a dict).
- **`docs/findings/finding-0199.md` §"Status of the evidence"** — *"code-traced, NOT empirically
  reproduced"* → **banner: correction**, but **by the orchestrator at seal, not by the builder**
  (a builder may not edit an existing finding). Recorded here so it is not lost.
- **`docs/findings/finding-0174.md`** → **cross-ref: extension.** This plan does not fix the
  declared-vs-real footprint error; it makes the *unknown* portion visible. Link, do not close.

## 5. Write scope

`core/models/loader.py` is the whole production surface. `tests/unit/test_loader_reconcile.py` is
new and holds the reproduction-derived acceptance tests. The other five test files are **carried
because they pin the surface this plan moves** — constructing a `TwoSlotLoader` now implies a
client that answers `ps()`, and a naïve scope would deny the builder mid-build (the exact
retrofit trap of findings 0071/0072/0075/0084).

Deliberately OUT of scope: `core/models/ollama_client.py` (`ps()` is sufficient),
`core/models/registry.py`, `config/defaults.toml`, `ops/lifecycle/launcher.py`, and every
foundation-denylist file.

## 6. Interfaces pinned inline

**The reconcile step — injectable, so `_check_ceiling` stays pure and testable clientless:**

```python
def reconcile(self) -> ReconcileReport:
    """Replace belief with measurement: ask Ollama what is ACTUALLY resident.

    Called at construction and before every `_check_ceiling`. Never raises — a probe failure
    degrades to today's behaviour and is REPORTED as unreconciled, because Ollama being
    unreachable means no load can succeed anyway (so refusing adds nothing but a brick risk)."""
```

```python
@dataclass(frozen=True)
class ReconcileReport:
    reconciled: bool          # False = the ps() probe failed; accounting is today's belief
    known_gb: float           # sum of resident_gb for names the registry can cost
    unknown: tuple[str, ...]  # resident names with NO registry entry — uncostable
    complete: bool            # known-and-costed everything ⇔ not unknown and reconciled
```

**The fail-closed rule, and the carve-out that keeps it from bricking the daemon:**

```
unknown names present  ⇒  refuse NON-PINNED loads (they are ceiling-consuming and uncostable)
                       ⇒  ALWAYS allow the PINNED model  — it is the router, the system is
                          unusable without it, and refusing it converts a memory guard into an
                          availability outage.
⚑ THE EMBEDDER IS ALWAYS AN UNKNOWN NAME (§3, additional risks). Treat `cfg.embedding.model`
  as a KNOWN name for costing purposes even though it is absent from the registry; cost it at
  its measured footprint or, if none is configured, name it explicitly in `unknown` and say so.
  Without this carve-out every system that has ever embedded refuses every worker load.
```

**Reporting — the honesty requirement, verbatim from §2.8:** accounting is reported as **partial,
never full**. `ReconcileReport.complete` is the flag; any surface that prints residency must say
"partial" when it is False. **Do not let a partial reconcile read as a full one** — that would
replace one silent-wrongness with another, which is the defect class, not the fix.

## 7. Items

Blast radius: pure measurement → refusal policy → the surface that moves.

### Item 1 — `reconcile()` reads what Ollama actually holds

- **Objective:** the loader can state the true resident set, and say what it could not cost.
- **Files:** `core/models/loader.py`, `tests/unit/test_loader_reconcile.py`
- **Acceptance test:** with a stub client whose `ps()` returns a known name, an unknown name, and
  nothing: `known_gb` sums only costable models, `unknown` carries the rest, `complete` is False
  whenever `unknown` is non-empty. A `ps()` that raises ⇒ `reconciled=False`, no exception.
- **Falsifier:** *`reconcile()` raises, or reports `complete=True` while `unknown` is non-empty.*
  Either turns a partial measurement into a false claim of completeness — the finding's own defect
  one level up.
- **Invariants:** `_check_ceiling` stays pure over a dict (no client); no second liveness/ps probe
  is introduced; `ensure`'s routing is unchanged.
- **Touches stored data?** No. **Parallelizable?** No. **Depends on:** none.

### Item 2 — the ceiling refuses on measurement, and the stale early-return dies

- **Objective:** the three reproduced phases stop being reachable.
- **Files:** `core/models/loader.py`, `tests/unit/test_loader_reconcile.py`
- **Acceptance test:** reproduce all three phases from finding-0199 §"the experiment" and assert
  each now fails closed: (i) fresh loader + 2 externally-resident models ⇒ the books show 2, not
  0; (ii) the **23.0 ≤ 24.0 pass against a true 25.7 GB** case now RAISES `MemoryCeilingError`;
  (iii) an externally-evicted model is no longer early-returned as resident.
- **Falsifier:** ⚑ *the measured breach still passes the guard.* Phase (ii) is the reason this
  plan exists — if `_check_ceiling` still admits 25.7 GB against a 24.0 budget, nothing shipped.
- **Invariants:** the **pinned model is never refused** (§6 — refusing it is an outage, not a
  guard); an unreachable Ollama does not brick startup; `MemoryCeilingError`'s type and message
  shape stay compatible with `Supervisor.tick`'s `defer` path (`scheduler/supervisor.py:72-74`).
- **Touches stored data?** No. **Parallelizable?** No. **Depends on:** Item 1.

### Item 3 — the moved surface, and the tests that pin it

- **Objective:** the suite is green and the retrofit is honest.
- **Files:** the five carried test files (§5)
- **Acceptance test:** full green gate — `uv run --extra dev pytest` (model-free tier), `ruff`,
  `mypy` Tier-2 floor 0 and the tests baseline **exactly 69**, `ops.type_gate`.
- **Falsifier:** *a carried test is made to pass by weakening what it asserted.* The stubs gain a
  `ps()`; they do not lose an assertion. Diff every edited test and justify each change in the
  journal.
- **Invariants:** `tests/property/test_loader_fsm.py`'s FSM properties keep their meaning — it is
  the property-based guard on exactly this state machine, so a weakened invariant there is
  invisible and permanent.
- **Touches stored data?** No. **Parallelizable?** No. **Depends on:** Items 1–2.

## 8. Math carried explicitly

N/A — no mathematical object. The arithmetic is a sum against a configured budget, unchanged in
form; only its *inputs* become measured rather than believed.

## 9. Non-goals

- **No replacement of `TwoSlotLoader`.** `dn-local-model-runtime` §2.3 replaces it with
  process-existence residency in a later wave. This is the interim guard, and it must not
  pre-empt or complicate that.
- **No fix for finding-0174's declared-footprint error** (embedder 10.0 GB real vs 2.5 GB
  declared, measured 2026-07-25). Make the gap visible; do not re-cost the registry here.
- **No new probe.** `ps()` is the one reconciliation source.
- **No change to `ensure_tier` routing, `OllamaClient`, or the registry.**
- **No claim of complete accounting** — ever. Partial is the honest state and must be reported.

## 10. Stop-and-raise conditions

- **The fail-closed rule would refuse the PINNED model** in any reachable configuration ⇒ **STOP.**
  That converts a memory guard into an availability outage and needs a design call, not a builder's.
- **`ps()` cannot distinguish two variants of one model** (e.g. differing `num_ctx`) such that
  costing is ambiguous ⇒ **STOP and raise**; ambiguous costing is finding-0174's class and is a
  design question.
- **A carried test cannot be made green without weakening an assertion** ⇒ **STOP**, file, and
  park the criterion. A green suite bought by a weaker property is the audit's falsifier↔test gap.
- Any blessing transition — the builder must never perform one.

## 11. Parked decisions

| Decision | Default recorded |
|---|---|
| `ps()` probe fails | degrade to today's belief; `reconciled=False`; do NOT refuse |
| unknown-name policy | fail-closed for non-pinned; the pinned model is always allowed |
| where "partial" is surfaced | on `ReconcileReport`; callers render it |

**Rejected alternatives and re-entry conditions**, per row:

- **`ps()` probe fails.** Rejected: *refuse all loads.* An unreachable Ollama already fails every
  load, so refusing adds nothing but a brick risk. Re-entry: a probe failure is ever observed
  while loads still succeed.
- **Unknown-name policy.** Rejected: *refuse everything* (an outage, not a guard — and the
  embedder is always unknown, §3); *ignore unknowns* (restores the defect exactly). Re-entry: the
  embedder enters the registry, shrinking "unknown" to genuinely foreign models.
- **Where "partial" is surfaced.** Rejected: *print it from the loader* — core does not own
  presentation. Re-entry: a caller ships that ignores the flag.

## 12. Dependency & ordering summary

Strictly linear: **Item 1 → Item 2 → Item 3.** One session. No plan depends on this, and it
depends on none — that independence is the point (§0). It is, however, **wanted before the
restart**: the restart is a fresh supervisor coming up against an Ollama that has held models
since run #35, which is exactly the reproduced false-absent path.

Later supersession is expected and fine: `dn-local-model-runtime` §2.3 removes `_resident`
entirely. This plan buys correctness for the interval between now and then.
