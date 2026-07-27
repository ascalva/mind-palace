---
type: build-plan
id: bp-110
track: ops
status: complete
design_ref:
  - docs/design-notes/dn-supervision-and-liveness.md
contract: builder
write_scope:
  - scheduler/worker.py
  - scheduler/supervisor.py
  - core/kernel/config/loader.py
  - config/defaults.toml
  - scripts/check_imports.py
  - tests/unit/test_worker_protocol.py
  - tests/integration/test_supervisor.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 400k
  actual:
    model: opus              # claude-opus-5[1m], DELEGATED builder in a worktree (session-54)
    tokens: 327552           # HARNESS-MEASURED from the completion notification, 160 tool uses,
                             # ~50 min. The builder SELF-reported ~285k; the harness figure is
                             # recorded because a self-report is not an independent measurement.
    ratio: 0.82              # 327552/400k — the well-pinned side, as expected for a plan whose
                             # §6 carried every interface verbatim
    session_delta: unmeasured
    week_delta: unmeasured   # AT-SEAL readings: session 1% at spawn (fresh window), week 38%,
                             # Fable 19% (resets Jul 31 8pm ET)
    notes: >-
      SEALED session-54. Merged `--no-ff` after an orchestrator audit that VERIFIED THE TWO
      LOAD-BEARING FALSIFIERS EMPIRICALLY rather than taking them on report. MUT-1 (the most
      serious — a spawned worker starts UNSEALED on macOS and the failure is silent): deleting
      `seal()` from the entrypoint reddened SEVEN tests including
      `test_the_worker_process_is_sealed_and_blocks_a_non_loopback_connect` and
      `test_the_seal_is_the_first_thing_the_entrypoint_does`; restored, 14 passed. MUT-3 (the
      subtle one — bp-105's function-local `import psutil` passed every gate at the time): a
      FUNCTION-LOCAL store import planted in `scheduler/worker.py` made `scripts/check_imports.py`
      exit 1, naming the line and both the module and symbol firewalls; removed, exit 0. Reported
      as tier 4, not overclaimed.

      Scope clean — every path in `write_scope`, plus its own journal and new findings. bp-123's
      overlay guards UNTOUCHED (the loader diff is purely additive: `SchedulerConfig`, a defaulted
      `Config.scheduler`, one `raw.get`; `_refuse_on_legacy_overlay` still runs first).
      finding-0224 left open and untouched as instructed — `_dispatch_to_worker` passes no
      `timeout_s`, so no deadline could settle it by side effect.

      ⚑ THE §6 SHAPE TENSION RESOLVED CORRECTLY (finding-0228, `[banner: correction]`): §6 pinned
      `job_budget_s: float` but bp-109 built `JobQueue.job_budgets: Mapping[str, float]`, looked up
      BY KIND at `queue.py:435`. A scalar is unconsumable there without fanning it over every kind
      or adding a second budget source — the exact parallel source finding-0225 exists to prevent.
      Landed per-kind; the scalar deliberately NOT also shipped. Discharges finding-0225's wiring
      half.

      ⚑ A REAL BUG CAUGHT BY TEST DURATION, not by a failing assertion: the wall-clock bound took
      30.08 s to enforce a 1 s deadline because `_recv` blocked in `readline()` and the deadline
      was checked only BETWEEN frames — a green `pytest.raises(WorkerTimeout)` was attesting a
      bound that did not work. Fixed by passing the deadline into the read; the test now asserts
      elapsed time. 30.08 s -> 1.01 s.

      GATE, all six legs on the MERGED tree, each run separately: ruff · import-firewall
      (INCLUDING the new tier-4 worker boundary, "scanned transitively; module-level AND
      function-local") · tier-2 mypy 260 source files · argless mypy EXACTLY 69 · `ops.type_gate` ·
      bare `uv run pytest -q` = **2 failed, 2276 passed, 12 skipped in 1024.15s**. Both failures
      are pre-existing and explained, neither is this plan's: the finding-0103 INTENTIONAL-RED
      ratchet, and `tests/e2e/test_dream_v2_live.py` (finding-0226 — bp-107's correct ceiling
      refusing a real 29.7 GB load).

      ⚑ A THIRD FAILURE APPEARED ONCE AND IS A FLAKE, NOT A REGRESSION — recorded because a silent
      intermittent is exactly what a future seal would misread. The first post-merge run showed
      `tests/e2e/test_scheduler_live.py::test_supervisor_dispatches_a_real_job` failing (3 failed /
      2275 passed). It did NOT reproduce in FOUR subsequent runs: in isolation (1 passed, 18.93s),
      across the whole e2e set (only the known dream failure), with three models deliberately left
      warm (1 passed, 50.95s), and in a second full suite (2 failed / 2276 passed — it passed).
      Its own docstring names the mechanism: it unloads every model for a clean slate, so a cold
      generation "can queue behind a load and time out". Item 4's rule was RULED OUT as the cause
      by reading the code, not by assuming — `model_blocked_tiers()` returns `frozenset()` unless
      `_in_flight_key` is set, and that is assigned ONLY on the subprocess path, which
      `worker_mode = "inproc"` never takes. The `MemoryCeilingError -> defer` path in `tick` was
      verified PRE-EXISTING at `ff51028`.

      ⚑ SEVERITY NOTE that the earlier reading of this got wrong: BOTH e2e failures are marked
      `pytest.mark.live` and the deploy gate / CI run `-m "not live and not podman and not
      needs_vault and not needs_restic"`, so neither is in the attestable-green gate at all. They
      surface only in a bare `pytest -q`. The builder's own green-gate run (2258 passed, 11
      skipped, 21 deselected) was correctly, honestly green.

      FOUR FINDINGS FILED, and 0229 is the one that matters: bp-110 ships SYNCHRONOUS dispatch, so
      it delivers cancellability but NOT liveness — `_dispatch_to_worker` iterates to completion
      inside one `tick()`, so a 14-hour backfill still stalls the serve loop. §1's objective
      sentence promises "the supervisor stays live"; no ITEM asks for non-blocking dispatch, so
      nothing shipped is wrong and the gap is between the objective and the items. Consequently
      §2.7's hazard does not arise yet and Item 4's guard, though built and tested, currently
      guards an EMPTY window — recorded in the docstring rather than left to be discovered.
      0227 `discovery`: EVERY lane module imports a store class at module level, so bp-113/bp-114
      need a `ReadOnlyRows` signature refactor as a PRECONDITION their estimates do not price.
      0228: the per-kind correction above. 0230 (filed as 0226, renumbered at merge — see
      finding-0231 for the id-allocation race): V5 measured, a pure-CPU thread costs 2150x
      THROUGHPUT but leaves the loop at ~153 Hz, clearing a 1 s cadence by two orders of magnitude,
      so "starves the loop" is true as throughput and false as liveness and the thread rejection
      rests on non-cancellability — which is why no §10 STOP fired. The ratified decision stands.

      Ships DEFAULT-OFF: `worker_mode = "inproc"`, every existing handler unchanged, every existing
      supervisor test passing unedited.
depends_on: [bp-108, bp-109]
parallelizable_with: []
created: 2026-07-25
updated: 2026-07-25
links:
  - docs/findings/finding-0191.md
  - docs/findings/finding-0178.md
  - docs/findings/finding-0171.md
  - docs/inbox/owner-questions.md
re_entry: null
supersedes: null
superseded_by: null
warrant: docs/findings/finding-0178.md
---

# Build Plan — THE INTEGRATOR: the worker protocol and the dispatch seam

## 0. Mode & provenance

⚑ **This is the integrator plan `dn-supervision-and-liveness` §3 requires** — *"per-lane builder
plans with disjoint scopes, plus one integrator plan whose write_scope is exactly the seam files
(the supervisor dispatch path + the worker protocol), carrying a named falsifier per hand-off."*
It owns the seam and **no lane**. Every lane migration (bp-113, bp-114) depends on it and touches
only its own handler module.

It also discharges the **build half of oq-0035**, ruled **(c) both** by the owner on 2026-07-25
(`941785d`): (b) worker-enforced job budgets is the real fix and is this plan; (a) bounded
escalation is the fail-safe behind it and is bp-112.

Investigation and planning produced this; implementation proceeds item-by-item on owner approval.

## 1. Objective

A job's long-running compute can be dispatched to a subprocess that holds no store writer, so the
supervisor stays live, owns the clocks, and performs every landing itself.

### 1.2 Non-goals (explicit — see §9)

Not the lease, not escalation, not any ingest lane. **Not a default-on change**: `worker_mode`
ships `"inproc"` (`dn-supervision-and-liveness` §4, owner-stated wiring) and every existing
handler keeps running exactly as today.

## 2. Context manifest

Read in order, whole files before citing:

1. `docs/design-notes/dn-supervision-and-liveness.md` — **§2.3 in full** (the handler survey and
   the capability reframing), §2.4 (the oq-0035 position), §2.5 (the execution model),
   §2.7 (the ceiling under the worker model), §2.10, V1/V2/V4/V5. **The content spec.**
2. `docs/findings/finding-0191.md` — why this plan exists as a separate plan at all
3. `docs/findings/finding-0178.md` — the warrant: there is no job timeout anywhere
4. `scheduler/supervisor.py` — **whole file, 116 lines.** `tick` `:63-97`, `run` `:99-107`
5. `scheduler/interface.py:53-59` — `ambassador_task_handler`, **the in-repo reference shape**
6. `core/sandbox/runner.py:55-93` — the subprocess+timeout+destroy precedent
7. `core/runtime.py:37-48` — `seal()` then `assert_sealed()`; the V4 template
8. `core/kernel/config/loader.py:296-343` — the `Config` dataclass and its section fields
9. `scripts/check_imports.py` — the import walker the tier-4 ratchet must **reuse**

**Does core already have this?** Three reuses are mandatory, and re-implementing any of them is a
DRY defect (§10):
- **Subprocess lifetime** — `core/sandbox/runner.py:65-80` already does argv + stdin + wall-clock
  timeout + destroy-on-expiry. Borrow the discipline; do **not** write a second timeout harness.
- **Import-graph walking** — `scripts/check_imports.py` already exists and is in the local CI
  gate. The worker's tier-4 ratchet is a **new rule inside it**, not a second walker.
- **Seal assertion** — `core/runtime.py:38-39` is the exact two-line form. Copy it; do not invent
  a worker-specific seal.

## 3. Investigation & grounding  <!-- Part A -->

- **Q1 — is the seam where the note says?** **Yes.** `scheduler/supervisor.py:87` is
  `result = handler(job)` — a synchronous, unbounded, in-process call. `Handler` is declared one
  place, `supervisor.py:31`: `Handler = Callable[[Job], "str | None"]`.
- **Q2 — does `ambassador_task` really already have the target shape?** ⚑ **Yes, verified
  directly.** `ambassador_task_handler` (`scheduler/interface.py:53-59`) returns
  `librarian.answer(query).text` — pure text, no store write — and the supervisor lands it at
  `supervisor.py:94-95` (`if …state == RUNNING: self.queue.complete(job.id, result)`). The
  mechanism this plan generalizes is **already running in production on one kind**. That is why it
  is this plan's proof lane and why no ingest handler needs to change here.
- **Q3 — ⚑ does the compute half really need no store handle?** **NO — and the note does not
  settle this.** Three compute halves demonstrably need a store **READ**:
  `CodeCorpusSync.sync` reads `self.store.all_rows(provenances={Provenance.CODE})`
  (`core/ingest/code_corpus.py:283`), `backfill` does the same (`:321`), and even the proof lane's
  `librarian.answer` performs k-NN retrieval over the vector store. The note's §2.3 wording — the
  worker is handed *"sources, blobs, and an embedder client, never a `VectorStore`"* — is correct
  about **writes** and silent about reads. Pre-reading in the supervisor is not an option for
  retrieval. **§6 pins the resolution (a read-only facade) and §11 records it as an extension the
  note did not specify; §10 makes a leaking facade a STOP.**
- **Q4 — subprocess or `multiprocessing`?** ⚑ **Subprocess with a dedicated `__main__`
  entrypoint, and the reason is the ratchet.** The note's tier-4 backing is *"the worker
  entrypoint's import graph contains no store-opening constructor."* Under `multiprocessing` the
  worker's import graph **is the parent's**, so the ratchet would assert nothing. A separate
  `python -m scheduler.worker` gives a scoped import graph that `scripts/check_imports.py` can
  actually walk. The tier-4 claim is only buildable this way.
- **Q5 — does anything inherit the seal?** **No, and that is V4.** macOS uses **spawn**, and
  `core/sealing.py` is a per-process monkeypatch on `socket.connect` (its own docstring says so).
  A spawned worker starts **unsealed**. `core/runtime.py:38-39` is the template the worker
  entrypoint must run before anything else. This is not defensive — without it the worker is a
  Zone-A process with egress, breaching non-negotiable #1.
- **Q6 — where does the ceiling gate sit relative to the spawn?** `supervisor.py:71`
  (`self.loader.ensure_tier(...)`) runs **before** any handler call, so it already precedes the
  spawn. The refusal point survives unchanged (§2.7's first bullet, verified).
- **Q7 — is the §2.7 concurrency hazard real?** **Yes, and it arises with this plan, not before.**
  Today "≤2 resident models" holds implicitly because `tick` is serial. Once the supervisor stays
  live while a worker computes, it can claim a second model-using job and `ensure_tier` for job B
  would evict the model job A is mid-generation on. The rule must land **here**, with the
  mechanism that creates the hazard — shipping the split without it is a regression.
- **Q8 — V5: are threads really disqualified?** **Reasoned, not measured** — the note says so
  itself. The note is ratified with subprocess, so this plan builds subprocess; Item 1 measures V5
  anyway because a contrary result invalidates a ratified decision and that is a §10 raise, not a
  silent proceed.
- **Q9 — where does the `[scheduler]` config section live?** ⚑ **Not in `config/loader.py`.** That
  file is a **facade** re-exporting from `core.kernel.config.loader` (`config/loader.py:1-13`).
  The `Config` dataclass is at `core/kernel/config/loader.py:307-329`. Both notes say "the config
  loader" without disambiguating; the write_scope here is the real one.

**Additional risks or questions surfaced during reading:**

- ⚑ **An unknown config section is dropped silently.** `_overlay`
  (`core/kernel/config/loader.py:350-359`) merges by section name and `Config` has no catch-all,
  so a `[scheduler]` block in `local.toml`
  with no dataclass simply vanishes. This is the bp-102 / finding-0174 lesson verbatim, which is
  why §4 of the note makes the schema part of the deliverable. **Land the whole section's schema
  in this plan**, including the keys bp-111 will consume, so the section is never half-defined.
- Batch payloads carry float vectors (V2 estimates 1–5 MB). Serialization format is a real choice
  with a real cost; §11 parks it with a default and Item 1 measures it before Item 2 commits.
- `tests/integration/test_supervisor.py` constructs a `Supervisor` directly and is carried. The
  builder must **grep for `Supervisor(`** before editing — `tests/integration/{test_cron,
  test_chat_sensor_wiring,test_research_cron}.py` and `tests/unit/test_restart_trustworthy.py`
  also construct one, and are deliberately **not** carried because this plan adds only an
  *optional* field. If one of them reds, that is a §10 raise, not a scope widening.

## 4. Reconciliation  <!-- Part B -->

- **`scheduler/supervisor.py:1-14`** — the module docstring's step 3, *"run its handler to
  completion (or one checkpointed step)"* → **banner: correction.** It stops being the only shape.
  Amend to name both dispatch modes and cite the note; say explicitly that `inproc` remains the
  default and the documented behaviour for every unmigrated kind.
- **`scheduler/supervisor.py:12-13`** — *"A reactive escalation is simply a high-priority job; it
  is dispatched at the next boundary, never as a mid-generation interrupt."* → **cross-ref:
  extension.** Still true for *scheduling*; the note adds that a wedged worker is now killable
  mid-compute. Distinguish the two so a reader does not conclude the split introduced preemption.
- **`config/defaults.toml`** — a new `[scheduler]` section → **cross-ref: extension**, written in
  the file's established voice (a comment saying *why* each bound exists, as `[ollama]:11-16`
  does).
- **`docs/inbox/owner-questions.md`** oq-0035 → **cross-ref only.** The ruling is already
  recorded; the builder must not edit it. Note in the journal that (b) landed.

## 5. Write scope

`scheduler/worker.py` is new: the protocol types **and** the `__main__` entrypoint (Q4 — they must
share a module for the import-graph ratchet to mean anything). `scheduler/supervisor.py` is the
dispatch seam. `core/kernel/config/loader.py` + `config/defaults.toml` carry the `[scheduler]`
schema. `scripts/check_imports.py` gains the worker-boundary rule.
`tests/unit/test_worker_protocol.py` is new; `tests/integration/test_supervisor.py` is **carried
because it pins the surface this plan
moves**.

⚑ **Deliberately OUT of scope — this is the integrator plan and owns NO lane:**
`core/ingest/code_corpus.py` (bp-113), `core/ingest/sync.py` and `core/ingest/index.py` (bp-114),
`ops/chat_sensor.py`, `core/dreaming/`, `core/curator/`. Also out: `ops/lifecycle/launcher.py`
(bp-108/bp-111/bp-112 own it — this plan changes no wiring there because `worker_mode` defaults to
`inproc`), `scheduler/queue.py` (bp-109), and every foundation-denylist file.

## 6. Interfaces pinned inline

**The compute/land protocol. Copy these verbatim; a builder must never infer this shape.**

```python
# scheduler/worker.py

@dataclass(frozen=True)
class Batch:
    """One bounded unit of computed work, ready to land. `rows` are store-shaped dicts; `token`
    is an opaque resume marker the NEXT batch starts from (None = this job is finished)."""
    rows: tuple[dict[str, Any], ...]
    token: str | None
    items_done: int

# The compute half. Registered ALONGSIDE the existing `Handler`, never replacing it.
ComputeHandler = Callable[[Job, "WorkerContext"], "Iterator[Batch]"]

# The landing half — supervisor-side, short, single-writer, never in the worker.
Lander = Callable[[Job, Batch], None]
```

**The existing handler type is UNCHANGED** (`scheduler/supervisor.py:31`) — every registered kind
keeps working with no edit:

```python
Handler = Callable[[Job], "str | None"]
```

**`Supervisor`'s new field — additive, defaulted, so no existing construction site breaks:**

```python
@dataclass
class Supervisor:
    queue: JobQueue
    loader: TwoSlotLoader
    handlers: dict[str, Handler]
    ...
    compute: dict[str, tuple[ComputeHandler, Lander]] = field(default_factory=dict)   # NEW
    worker_mode: str = "inproc"                                                       # NEW
```

**⚑ The read-only store facade (§3 Q3 — the note's gap, resolved here).** The tier-2 claim is
about *writes*; retrieval needs *reads*. The worker is handed this and nothing else:

```python
class ReadOnlyRows(Protocol):
    """The ONLY store surface a compute half ever sees. It exposes reads and cannot express a
    write. It must NOT hold a reachable reference to the writable store — no `._store`, no
    `.__wrapped__`, no closure over the handle that `getattr` or pickling can recover. If the
    writable object is reachable, the capability restriction is decoration, not a capability,
    and the tier-2 claim in §2.3 is false."""
    def all_rows(self, *, provenances: set[str] | None = ...) -> list[dict[str, Any]]: ...
    def rows_for_source(self, source_path: str) -> list[dict[str, Any]]: ...
    def search(self, vector: list[float], k: int) -> list[dict[str, Any]]: ...
```

**The seal re-assertion — V4, first two statements of the worker entrypoint**, copied from
`core/runtime.py:38-39`:

```python
    seal()           # structural egress guard BEFORE anything else (Invariant 1)
    assert_sealed()
```

**The `[scheduler]` config section — the WHOLE section, including keys bp-111/bp-112 consume** (§3,
additional risks: a half-defined section is silently dropped):

```python
@dataclass(frozen=True)
class SchedulerConfig:
    worker_mode: str = "inproc"        # "inproc" | "subprocess"; default per note §4
    batch_deadline_s: float = 0.0      # 0 = no deadline (today's behaviour)
    job_budget_s: float = 0.0          # 0 = no budget (finding-0178's status quo)
    escalation_grace_s: float = 30.0   # SIGTERM -> N -> SIGKILL; consumed by bp-112
    lease_ttl_s: float = 0.0           # 0 = no lease; consumed by bp-111 after V9  (lease plan)
```

**The single-model-in-flight rule, verbatim from `dn-supervision-and-liveness` §2.7:**

```
At most one in-flight MODEL-USING job. While one is out, the supervisor may dispatch only jobs
sharing its `load_key` or doing landing/housekeeping.
```

Its enforcement point is the one claim site, `supervisor.py:65`, via `claim`'s existing
`loaded_key`/`blocked_tiers` parameters (`scheduler/queue.py:292-294`) — **no new queue API.**

## 7. Items

Blast radius: measurement → a library nothing calls → the dispatch seam (behind a default-off
flag) → the concurrency rule → the ratchet.

### Item 1 — V1, V2, V5: measure before building

- **Objective:** the three numbers the note says block this design are taken, not assumed.
- **Files:** none (scratchpad scripts; results recorded in `journal.md`)
- **Acceptance test:** three measurements in the journal. **V1** — `store.add` rows/sec for a
  representative batch (100–500 chunks × 2560-dim) on the real store, giving a p95 landing time.
  **V2** — serialize/deserialize one such batch worker→supervisor, as a fraction of the time to
  compute it. **V5** — a finding-0169-shaped pure-CPU scan on a thread, measuring the supervisor
  loop's achieved tick rate.
- **Falsifier:** ⚑ *V1 shows p95 landing time approaching the tick budget* — then the supervisor
  is blocked in its own landing loop and the seam has merely moved (the note's own §2.10
  falsifier). ⚑ *V5 shows the loop keeps a healthy tick rate under a pure-CPU thread* — then the
  thread model was rejected on a wrong premise and a **ratified** decision needs the owner, not a
  builder (§10).
- **Invariant(s) it must not violate:** read-only against the real store; no rows written.
- **Touches stored data?** No. **Parallelizable?** No. **Depends on:** none.

### Item 2 — `scheduler/worker.py`: the protocol and the sealed entrypoint

- **Objective:** a worker process exists that seals itself, computes, and streams batches back.
- **Files:** `scheduler/worker.py`, `tests/unit/test_worker_protocol.py`
- **Acceptance test:** `python -m scheduler.worker` round-trips a synthetic compute handler:
  batches arrive in order with correct `token`/`items_done`; a worker that raises reports a typed
  failure rather than hanging; **and a test asserts `assert_sealed()` holds INSIDE the worker
  process** (spawn a worker whose payload attempts a non-loopback connect and observe it blocked).
- **Falsifier:** ⚑ *the worker process is not sealed.* V4 exactly. A spawned Zone-A process with
  egress breaches non-negotiable #1 — this is the single most serious way this plan can go wrong,
  and it fails silently because nothing else in the system would notice.
- **Invariant(s) it must not violate:** the entrypoint's import graph contains **no** store-opening
  constructor (Item 5 proves it); the worker holds no secrets and no vault handle; a worker crash
  never takes down the supervisor.
- **Touches stored data?** No — the worker cannot write by construction. **Parallelizable?** No.
  **Depends on:** Item 1.

### Item 3 — the dispatch seam, behind `worker_mode`, proven on `ambassador_task`

- **Objective:** the supervisor can dispatch compute out-of-process and land the result itself,
  with today's behaviour bit-identical when the flag is off.
- **Files:** `scheduler/supervisor.py`, `core/kernel/config/loader.py`, `config/defaults.toml`,
  `tests/integration/test_supervisor.py`
- **Acceptance test:** ⚑ **the parallel-run proof.** The same `ambassador_task` job produces the
  **same result** under `worker_mode = "inproc"` and `worker_mode = "subprocess"`. With the flag
  at its default every existing supervisor test passes **unedited**. The `[scheduler]` section
  round-trips through `load_config` with a `local.toml` overlay (proving it is not silently
  dropped).
- **Falsifier:** ⚑ *the two modes disagree on the result*, or *any existing test needs editing to
  pass with the flag off*. The second is the more dangerous: it means this was not additive, and
  the "no behaviour change at landing" claim is false.
- **Invariant(s) it must not violate:** the ceiling gate stays at `supervisor.py:71`, **before**
  the spawn (§3 Q6); `Handler` is unchanged and every existing registration keeps working; the
  landing step remains the supervisor's, so single-writer holds; `queue.get(job.id).state ==
  RUNNING` (`:94`) still governs checkpoint-yield.
- **Touches stored data?** Yes — landings write the real stores. Require the parallel run against
  a **scratch** store before any run against `data/`.
- **Parallelizable?** No. **Depends on:** Item 2.

### Item 4 — one model in flight

- **Objective:** a live supervisor cannot evict the model a running worker is mid-generation on.
- **Files:** `scheduler/supervisor.py`, `tests/integration/test_supervisor.py`
- **Acceptance test:** with a model-using job out to a worker, the next `claim()` returns only a
  job sharing its `load_key` or a model-free job; a second model-using job stays QUEUED and is
  dispatched once the first lands. Ceiling semantics are **numerically identical** to today.
- **Falsifier:** ⚑ *`ensure_tier` is called for a second tier while a worker is out.* That is the
  §2.7 hazard realized — it would evict a model mid-generation and the failure would look like a
  model bug, not a scheduler bug. Also *(the note's own falsifier)* **if this serializes the
  system back to one-job-at-a-time in practice**, because every lane is model-using, then the
  fairness win of the batch unit is theatre — measure the interleave actually achieved and record
  it.
- **Invariant(s) it must not violate:** no new queue API — use `claim`'s existing `loaded_key` /
  `blocked_tiers` (`queue.py:292-294`); the foreground gate (`blocked_tiers`, `supervisor.py:60-61`)
  keeps its meaning and is not overloaded; non-negotiable #8's accounting is unchanged (this adds
  no new resident model, it prevents one).
- **Touches stored data?** No. **Parallelizable?** No. **Depends on:** Item 3.

### Item 5 — the tier-4 ratchet the capability claim rests on

- **Objective:** "the worker cannot write a store" is proven mechanically, not asserted.
- **Files:** `scripts/check_imports.py`, `tests/unit/test_worker_protocol.py`
- **Acceptance test:** a new rule in the **existing** walker asserts that
  `python -m scheduler.worker`'s transitive import graph contains no store-opening constructor
  (`open_vector_store`, `VectorStore`, `VaultCatalog`, `open_derived_store`, the ledger openers).
  It runs in the local CI gate alongside the existing rules.
- **Falsifier:** ⚑ *adding `from core.stores.vectorstore import open_vector_store` to the worker's
  import graph leaves the gate green.* Plant exactly that. And the subtler one: *the rule only
  walks module-level imports* — bp-105's raw `import psutil` was **function-local** and passed
  every gate (bp-106 Item 4 records this as the exact hole). A function-local store import must
  fail too.
- **Invariant(s) it must not violate:** no second import walker is written (§2, DRY); the existing
  `check_imports.py` rules are unchanged and still pass; the ratchet is reported as **tier 4**, and
  the code comment must not claim tier 1 or 2 for it — overclaiming the tier is the note's own
  named foot-gun.
- **Touches stored data?** No. **Parallelizable?** No. **Depends on:** Item 2.

## 8. Math carried explicitly

N/A — no mathematical object. The batch is a bounded sequence, not a measure; the vectors it
carries are computed by the embedder, unchanged in form and value by this plan (any change to them
would be a `dn-local-model-runtime` §2.5 equivalence concern, not this plan's).

## 9. Non-goals

- **No lane migration.** This plan owns the seam; bp-113 and bp-114 own lanes. Touching
  `core/ingest/` here is the finding-0191 failure being repeated in the plan written to prevent it.
- **No lease, no escalation, no drain report** — bp-111 and bp-112. This plan *defines* their
  config keys (so the section is never half-defined) and consumes none of them.
- **No default-on.** `worker_mode = "inproc"` at landing, per §4 of the note.
- **No `Handler` type change** — the new protocol is additive.
- **No worker pooling / warm workers** — the note parks it (one process per job, the sandbox's
  "overran ⇒ discarded, never reused" discipline).
- **No move of `ambassador`'s reactive path out-of-process** — the note parks it as default NO.
- **No retry policy change** for a killed job.

## 10. Stop-and-raise conditions

- ⚑ **V5 shows the supervisor loop survives a pure-CPU thread** ⇒ **STOP and raise.** The note
  rejected the thread model on a reasoned, unmeasured premise. A contrary measurement means a
  **ratified** decision rests on a false claim — that is an owner-level design question, and
  building subprocess anyway while knowing better is exactly the "shoot ourselves in the foot" the
  mandate forbids.
- ⚑ **V1 shows p95 landing approaching the tick budget** ⇒ **STOP.** The seam has moved rather
  than opened; the design needs revisiting before any lane migrates onto it.
- ⚑ **The read-only facade cannot be made non-leaking** (§6 — the writable handle is recoverable
  by `getattr`, pickling, or a closure) ⇒ **STOP.** Ship it and the tier-2 claim in a ratified note
  becomes false, which is worse than shipping nothing: the note would be quoted as a guarantee.
- **A store-opening import proves unavoidable in the worker's graph** ⇒ STOP and file a
  `spec-defect`. §2.3's capability restriction is the design's load-bearing claim; if the code
  cannot honour it, the note is wrong and must be corrected, not worked around.
- **An unmigrated kind reds with the flag off** ⇒ STOP. The change was not additive.
- **This plan feels too big mid-build** ⇒ file a `spec-defect` and park. **Do not re-split
  mid-build** — plan boundaries are decided at graduation (graduate skill).
- Any blessing transition — never.

## 11. Parked decisions

| Decision | Default recorded | Re-entry condition |
|---|---|---|
| IPC serialization | length-prefixed JSON lines over a pipe | Item 1's V2 number |
| worker process model | one per job, no reuse | V2/spawn cost against short jobs |
| the read-only store facade | a Protocol-typed reader, no writable handle | §10 if it leaks |
| batch size | per-lane, chosen by each lane plan | a lane exceeds the batch deadline |
| `job_budget_s` values | 0 (no budget) | bp-112 lands enforcement |

**Rejected alternatives, per row:**

- **IPC.** Rejected: *`multiprocessing.Queue`* — decisive on Q4, it destroys the tier-4 ratchet by
  giving the worker the parent's import graph. Rejected: *pickle* — it would let a live store
  object cross the boundary, which is precisely the capability the design removes. Rejected:
  *a binary float framing* — likely faster and worth revisiting, but premature before V2 says
  serialization matters; JSON keeps the wire inspectable during bring-up, which is worth more
  during the one build where the protocol is being debugged.
- **Process model.** Rejected: *a warm worker pool* — the note parks it; one-per-job gives the
  simplest kill semantics, matching `core/sandbox/pool.py:5`'s "overran ⇒ discarded, never reused."
- **The facade.** Rejected: *hand the worker the real store and rely on discipline* — that is
  tier 5 wearing tier 2's clothes, the note's named foot-gun. Rejected: *pre-read everything in
  the supervisor* — impossible for k-NN retrieval, and for `code_sync` it means shipping a
  22,621-row present-set across the pipe every job.
- **Batch size.** Deliberately per-lane: the note's fairness unit is the batch, and the right size
  differs between a 1,542-version backfill and a five-note vault sync.

## 12. Dependency & ordering summary

Items strictly linear: **1 → 2 → 3 → 4**, with **5** depending only on Item 2 (it may be built any
time after the entrypoint exists, and building it early is encouraged — it is the item that makes
the design's central claim true).

**`depends_on: [bp-108, bp-109]`**, both for substantive reasons:
- **bp-108** — the split's value is a loop that is no longer hostage to the backlog (its Item 4),
  and bp-108 holds `ops/lifecycle/launcher.py`, which this plan must not touch concurrently.
- **bp-109** — `dn-supervision-and-liveness` §2.5 **disqualifies cooperative batching** until the
  checkpoint/coalescing collision is pinned. bp-109 Item 4 is that pin. A batch-yield protocol
  landing before it would re-open the exact channel bp-105 Checkpoint 1 eliminated.

**No plan is parallelizable with this one.** It is the seam; everything downstream reads the
protocol it defines. bp-111, bp-112, bp-113 and bp-114 all depend on it, and bp-113/bp-114 are
parallelizable **with each other** (disjoint lane files) once it lands.

⚑ **`core/kernel/config/loader.py` + `config/defaults.toml` are the wave's second contended
file pair** — this plan lands `[scheduler]`, bp-115 lands `[runtime]`. They must not run as
concurrent worktrees even though their sections are disjoint.

⚑ **The wave's ordering rule, from `dn-supervision-and-liveness` §3:** *"The last commit before the
wave's seal must never be the first commit of a behaviour."* This plan ships its behaviour behind
a default-off flag and proves it on a lane that already has the shape — so the first real lane
(bp-113) meets a protocol that has already run in production shape, not one it is discovering.
