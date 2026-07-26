---
type: journal
plan: bp-110
started: 2026-07-26
updated: 2026-07-26
---

# Journal — bp-110 (THE INTEGRATOR: the worker protocol and the dispatch seam)

---

## Checkpoint 2 — Items 2 and 5 CLOSED: a sealed worker exists, and a ratchet proves it holds no store

**Status.** `scheduler/worker.py` exists, seals itself, streams batches, and dies typed. The
tier-4 ratchet is in the CI gate and both of Item 5's named falsifiers were planted and watched
go red. Item 5 was built early per §12 ("it is the item that makes the design's central claim
true"). Next is Item 3, the dispatch seam.

### Item 2 — `scheduler/worker.py`

Built as §6 pins it, verbatim: `Batch`, `ComputeHandler`, `Lander`, `ReadOnlyRows`. Both ends of
the wire live in this one module (§3 Q4 — they must share a module for the ratchet to mean
anything): the worker entrypoint, and `run_batches()`, the supervisor-side driver.

Three decisions worth a fresh agent's attention, none of them inferable from §6:

1. **⚑ The compute registry is STATIC, and this is load-bearing, not a convenience.** The obvious
   design — a dotted handler path in the job spec, `importlib.import_module(spec["handler"])` —
   would make the tier-4 ratchet **theatre**: a static AST walk cannot see a dynamically imported
   module, so the worker could be handed `core.stores.vectorstore` at runtime with every gate
   green. Kinds resolve only from names `worker.py` statically imports. bp-113/bp-114 register
   their lanes by adding them there.
2. **⚑ The `ReadOnlyRows` facade is an RPC proxy, and that is what makes §10's non-leaking
   requirement *structural* instead of argued.** `RowsProxy` sends each read back over the pipe;
   the supervisor answers from the real store. In the worker process **no store object exists**,
   so there is nothing for `getattr`, pickling, a closure, or `gc.get_referrers` to recover.
   Worth stating plainly because it is the deeper reason §2.5 chose a process: **an in-process
   facade over a live store can NEVER satisfy §6 in Python** — a closure cell is always reachable
   via `__closure__`, and `gc.get_referrers` defeats any attribute-hiding scheme. Had this plan
   tried to ship an in-process facade, §10's STOP would have fired. It did not fire because the
   process boundary answers the question the wrapper could not.
   The supervisor's read server (`_serve_read`) dispatches a **closed verb set** — never
   `getattr(store, verb)`, which would turn it into an arbitrary method-call channel and hand back
   exactly the capability being removed.
3. **Subprocess lifetime reuses `core/sandbox/runner.py:65-80`'s DISCIPLINE, not its harness**
   (§2's mandatory reuse). Discipline borrowed: a wall-clock deadline, destroy on expiry,
   SIGTERM → grace → SIGKILL, a typed timed-out result. Harness NOT borrowed, and the reason is
   forced: `subprocess.run(timeout=…)` cannot stream, and a batch protocol is a stream. `Popen`
   with the same discipline is one implementation each, not two timeout harnesses. `_terminate`
   carries the note's rule that escalation targets **only the worker** — killing the supervisor
   mid-landing is how you create the partial write oq-0035 worried about.

Also: the worker is spawned with a **pruned environment** (PATH/HOME/LANG/TMPDIR/PYTHONPATH/
VIRTUAL_ENV only). Invariant 10 — a process with no business holding secrets is not handed the
parent's environment.

### Item 2's falsifier — V4, and it was PLANTED, not asserted

`test_the_worker_process_is_sealed_and_blocks_a_non_loopback_connect` spawns a real worker whose
payload attempts a connect to a routable non-loopback literal (`93.184.216.34:80`, an IP literal —
never a name, since resolving one is itself egress) and asserts the guard refused it **from inside
that process**. Two supporting tests: an AST test that `seal(); assert_sealed()` are literally the
first two statements of `main` (a guard with a statement in front of it has a hole the runtime test
cannot see), and a control test that a spawned child does **not** inherit the seal — so V4's
premise is re-derived rather than assumed.

**MUT-1 planted:** replaced `seal(); assert_sealed()` in `main` with `pass`.
**Result — reddened, as required:**

```
FAILED tests/unit/test_worker_protocol.py::test_the_worker_process_is_sealed_and_blocks_a_non_loopback_connect
FAILED tests/unit/test_worker_protocol.py::test_the_seal_is_the_first_thing_the_entrypoint_does
2 failed, 6 passed in 32.62s
```

Restored; 8/8 green. The most serious failure available to this plan is now one that cannot land
silently.

### Item 5 — the tier-4 ratchet, in the existing walker

`scripts/check_imports.py` gains `scan_worker_boundary()`. **No second walker was written** (§2's
DRY mandate): the traversal reuses `ops.import_lint._imported_names` for module edges and its
`Violation` record for reporting. One addition, `_imported_symbols`, is a second **projection over
the same AST**, not a second walker — needed because `_imported_names` returns the MODULE for
`from M import S` (all I2 ever needed) while this rule must let `from scheduler.queue import Job`
pass and `from scheduler.queue import JobQueue` fail. Module granularity cannot draw that line.

⚑ **The forbidden set is stated as PACKAGES + NAME SHAPES, not a list of class names** — a name
list is precisely the thing that rots (the next store lands in `core/stores/` and a list silently
stops covering it: §1.2's "N ad-hoc detectors, each with its own rot"). Packages:
`core.stores`, `core.kernel.stores`, `ops.effect_ledger`, `ops.ledger`. Shapes: `*Store`,
`*Catalog`, `*Ledger`, `open_*store`, plus exact `JobQueue`/`open_store`.

⚑ **Reported as TIER 4 and the module comment says so explicitly.** The *property* ("the worker
cannot write a store") is tier 2; this scan is its tier-4 backing. Not tier 1 (stores are files on
a shared disk), not tier 2 (a scan is not a capability). Overclaiming is the note's own named
foot-gun and the comment is written to be unquotable in the wrong direction.

### Item 5's falsifiers — BOTH planted, on the real file, through the real gate

**MUT-2, module-level** (Item 5's named falsifier, verbatim):
```
scheduler/worker.py:476: imports 'core.stores.vectorstore' (worker-store-module firewall)
scheduler/worker.py:476: imports 'core.stores.vectorstore.open_vector_store' (worker-store-symbol firewall)
EXIT=1
```
**MUT-3, FUNCTION-LOCAL** (the subtler one — bp-105's raw `import psutil` was function-local and
passed every gate; finding-0198 records it as the exact hole):
```
scheduler/worker.py:241: imports 'core.stores.vectorstore' (worker-store-module firewall)
scheduler/worker.py:241: imports 'core.stores.vectorstore.open_vector_store' (worker-store-symbol firewall)
EXIT=1
```
Both restored; gate `EXIT=0`. The function-local case reddens because `ast.walk` descends into
function bodies — the same idiom `_imported_names` already used, which is why reuse was the right
call rather than a coincidence.

The falsifiers are also **encoded as tests**, not left as a one-time manual check — `scan_worker_
boundary()` takes `repo_root`/`entry` so the plants run against a synthetic tree in CI. A ratchet
nobody has watched go red is an assertion, not a ratchet (finding-0187: deleting bp-105's sweep
call left 85/85 green). One harness bug was caught doing this: the transitive-reach test passed a
mangled path and reported GREEN for the wrong reason; fixed, then confirmed red-for-the-right-
reason.

`tests/unit/test_worker_protocol.py`: **14 passed**. Existing I2 rules unchanged and still passing
(asserted by `test_the_existing_I2_firewall_rules_are_unchanged_and_still_pass`).

### finding-0227 filed (`discovery` → orchestrator)

Surveying what happens when a lane *does* register: **every** lane module in §2.3's table imports
a store CLASS at module level (`sync.py:34-37` four of them, `dreamer.py:35-37` three,
`curator.py:39-41` three, `librarian.py:33,36` two, and so on). They are annotations, not
constructions — every one already takes its stores by injection — but the ratchet cannot tell an
annotation from a constructor, and must not try.

**This does NOT trip §10's STOP**, and the distinction is the finding's content: §10 fires when a
store import is *unavoidable*, and these are avoidable — `ReadOnlyRows` is the seam that avoids
them. §2.3's capability claim survives intact. What it changes is **plan sizing**: bp-113/bp-114
each carry a protocol-parameterization pass over their lane module *before* they can register, and
some lanes reach read surfaces `ReadOnlyRows` does not cover (`VaultCatalog`, `VersionStore`,
`EdgeStore`) — which is a §6 pin their graduation must write, not something a builder should
discover against a red ratchet.

It is also **why Item 3's proof lane is a worker-side bring-up handler rather than the production
`ambassador_task` compute half**: `librarian.py:33,36` would red the ratchet, and both
`core/librarian/` and `scheduler/interface.py` are outside write_scope (§5, "owns the seam and NO
lane"). Migrating them would have been the finding-0191 failure repeated inside the plan written
to prevent it.

## Next action

Build **Item 3** — the dispatch seam in `scheduler/supervisor.py` behind `worker_mode`, plus the
`[scheduler]` config section in `core/kernel/config/loader.py` + `config/defaults.toml`.

⚑ **Before editing `tests/integration/test_supervisor.py`, the flag-off invariant is the one that
matters**: every existing supervisor test must pass UNEDITED, and the six other `Supervisor(`
sites (listed in Checkpoint 1's manifest delta) must stay green. If one reds, that is a §10 STOP
— the change was not additive — not a scope widening.

⚑ **The `[scheduler]` schema carries a live tension to resolve deliberately** (see Open questions).

---

## Checkpoint 1 — Item 1 CLOSED: V1, V2, V5 measured. No §10 STOP trips.

**Status.** Item 1 complete; the three numbers the note says block this design are taken, not
assumed. None of the three §10 measurement STOPs fires. Item 5 is next (§12 encourages building
it early; it depends only on Item 2's entrypoint existing, so Item 2 lands first).

### The environment these numbers were taken in

- Worktree `agent-a1a8d30858012771f`, base `f9c22f3`, python 3.13.14, GIL enabled,
  `sys.getswitchinterval() = 5.0 ms`, Apple Silicon (owner's M2 Max, 32 GB).
- Scripts are scratchpad-only (Item 1 has no `Files:`), under
  `/private/tmp/claude-501/.../scratchpad/{v1_landing,v2_ipc,v5_gil,v5b_latency}.py`.
- ⚑ **Stored data was NOT mutated.** The worktree has no `data/` of its own. The live store
  `/Users/ascalva/mind-palace/data/vectors.lance` was opened **read-only** (`count_rows` + one
  row's column names; no `add`/`delete`/`drop` path was entered). Every timed `store.add` ran
  against a scratch LanceDB in the scratchpad, seeded to the live store's row count so the
  table-size regime is representative.

### V1 — the landing cost. **[GROUNDED]** measured

Live store shape, read-only: `rows=22621`, columns
`[id, digest, title, source_path, chunk_index, provenance, text, layer, qualname, line_start,
line_end, current, vector]` — the 22,621 rows §11 names as the `code_sync` present-set.

Scratch store seeded to 22,621 rows; `VectorStore.add` timed 20× per batch size, payloads
pre-built so vector synthesis is outside the timed region:

```
[V1] batch=100 rows  n=20  p50=    4.99 ms  p95=    5.43 ms  max=   16.22 ms  rows/sec@p50=    20022
[V1] batch=200 rows  n=20  p50=    8.40 ms  p95=    9.55 ms  max=    9.68 ms  rows/sec@p50=    23820
[V1] batch=500 rows  n=20  p50=   16.55 ms  p95=   20.27 ms  max=   21.75 ms  rows/sec@p50=    30213
```

**Verdict: the falsifier does NOT fire.** The tick budget is `tick_seconds = 1.0`
(`ops/lifecycle/launcher.py:559`). Worst measured p95 landing is **20.27 ms at 500 rows = 2.0% of
the tick budget**; the 20 ms p95 is ~1/50th of one tick. "Landing is short" holds with two orders
of magnitude of headroom, so the seam opens rather than merely moving (§2.10, note V1). Landing
throughput *improves* with batch size (20k → 30k rows/sec), which is the expected LanceDB
per-append fixed cost being amortized — a datum for the per-lane batch-size choice (§11).

### V2 — IPC serialization as a fraction of compute. **[GROUNDED]** measured

Wire format under test is §11's parked default (length-prefixed JSON lines). The compute
denominator is **live**: `api/ps` showed `qwen3-embedding` already resident before the run, so no
model load was provoked and nothing was evicted.

```
[V2] batch=100  wire= 5.30 MB  serialize=   73.1 ms  deserialize=   42.8 ms  round-trip=  116.0 ms
[V2] batch=200  wire=10.60 MB  serialize=  148.8 ms  deserialize=   85.8 ms  round-trip=  234.6 ms
[V2] batch=500  wire=26.51 MB  serialize=  368.8 ms  deserialize=  214.2 ms  round-trip=  583.0 ms
[V2 denominator] embed 8 chunks -> dim=2560, 32.8 ms/chunk (live, embedder already resident)
[V2 ratio] batch=100  compute=  3.28 s  ipc round-trip=  116.0 ms  ipc/compute= 3.537 %
[V2 ratio] batch=200  compute=  6.56 s  ipc round-trip=  234.6 ms  ipc/compute= 3.578 %
[V2 ratio] batch=500  compute= 16.39 s  ipc round-trip=  583.0 ms  ipc/compute= 3.557 %
```

**Verdict: the falsifier does NOT fire.** IPC is a **flat ~3.55% of compute**, invariant across
batch size — both halves scale linearly, so the ratio does not degrade as lanes pick bigger
batches. That is not "a nontrivial fraction of computing it" (§2.10). JSON-lines is confirmed as
the landing default and §11's row is closed for this plan.

⚑ **One honest correction to the note's own estimate, worth carrying to whoever revisits §11.**
The note estimates "≈10 KB/vector float32; ~1–5 MB/batch expected". Measured wire is **5.30 MB for
a 100-row batch** — 1.02 MB of float32 payload inflated **~5.2×** by JSON's decimal float encoding.
The note's per-vector figure is right (2560 × 4 B = 10.2 KB); the per-batch estimate is low because
it did not price the encoding. This does **not** change the decision (3.55% of compute is cheap
either way) but it is the number the binary-framing alternative would be judged against: binary
framing would cut the wire ~5× and the IPC share from ~3.55% to ~0.7%. Recorded, not acted on —
§11 rejects it as premature, and JSON's inspectability is worth more during bring-up.

### V5 — GIL starvation under a pure-CPU thread. **[GROUNDED]** measured

Load is finding-0169's actual shape (whole-set materialization + a Python-side predicate over
4,000 × 2560-dim rows, on repeat — pure interpreter work, no IO). The loop under measurement is
the **real** `Supervisor.tick()` over a real SQLite-backed `JobQueue`.

```
[V5] CPU-scan working set: 4000 rows x 2560 dims
[V5] loop ALONE            :  987958 ticks in 3.0s ->   329318.9 ticks/sec
[V5] loop + pure-CPU thread:     460 ticks in 3.0s ->      153.1 ticks/sec
[V5] degradation           : 2150.4x slower ( 0.05% of the uncontended rate)
[V5] sys.getswitchinterval = 5.0 ms; python 3.13.14, GIL enabled = True

[V5b] loop ALONE                 n= 974286  p50=   0.003 ms  p99=   0.004 ms  max=   0.198 ms
[V5b] loop + pure-CPU thread     n=    584  p50=   7.518 ms  p99=   7.608 ms  max=  15.096 ms
```

**Verdict: the §10 STOP does NOT fire — but not for the reason a quick read would give, and the
difference is recorded as finding-0226 rather than smoothed over.**

The throughput claim is confirmed hard: **2150× degradation, 0.05% of the uncontended rate**, and
per-tick latency clamped at ~7.5 ms ≈ `sys.getswitchinterval()` — the textbook GIL-starvation
signature (the loop's throughput stops being governed by its own work and becomes governed by the
switch interval).

⚑ **But 153 ticks/sec is not a dead loop.** Against a 1.0 s tick cadence, a loop cycling every
7.5 ms clears the supervisory duty (renew a lease, record vitals, observe) by two orders of
magnitude. So the note's phrase *"starves the supervisor loop anyway"* is true as **throughput**
and false as **liveness** — a threaded supervisor would still *observe* a pure-CPU wedge fine.

This does not overturn the ratified decision, because the decision does not rest on that premise.
The note's own conclusion sentence is *"**the mode-4 power-to-act never arrives**"* — i.e.
**cancellability**, not observability, and it states V5's job as verifying *"the degree"*, a
secondary quantity. Python threads cannot be cancelled; that is a language fact no measurement can
move, and it is what makes the process boundary tier 3 (SIGKILL is enforced by an authority
outside the wedge) where an in-process cancel flag would be tier-5 cooperation with the code that
stopped cooperating. **Subprocess stands, on its load-bearing leg.** The over-strong phrasing is
filed as finding-0226 (`design` → orchestrator) so the note cannot later be quoted for a liveness
claim it does not own. No criterion is parked on it.

## Completed

- **Item 1 — CLOSED.** V1, V2, V5 all measured above; no falsifier fires; no §10 STOP trips.
- Plan `status: ready → in-progress` (the builder's own flip; the two blessing flips are untouched).

## In-flight

Nothing mid-motion. Baseline gate captured clean before any edit (ruff pass · import-firewall OK ·
`mypy core agents eval ops scheduler scripts` = 0 in 259 files · argless `mypy` = **69** errors in
20 files · `ops.type_gate` = the known non-fatal parked `test_restart_trustworthy.py:21` psutil
row, finding-0223). **69 is the number Item 2/3's new test files must not move.**

## Next action

Build **Item 2** — `scheduler/worker.py`: the `Batch`/`ComputeHandler`/`Lander` protocol (§6,
verbatim), the `ReadOnlyRows` facade, and the `python -m scheduler.worker` entrypoint whose FIRST
TWO STATEMENTS are `seal()` then `assert_sealed()` (copied from `core/runtime.py:38-39`). Prove
the seal from INSIDE the worker process by spawning one whose payload attempts a non-loopback
connect and observing `SealedCoreEgressError` — not by reading the code.

## Open questions

- **finding-0226** (`design` → orchestrator) — the note's "starves the supervisor loop" is a
  throughput claim, not a liveness claim; measured 2150× degradation but a still-live 153 Hz loop.
  Decision unaffected (cancellability is the load-bearing leg). Not parking anything.
- **finding-0224 is OPEN and NOT this plan's to settle** — bp-109 §4 vs §9 on whether a lapsed
  lease licenses reclamation. bp-112's graduation rules on it. This plan defines `[scheduler]`'s
  budget key and consumes none of it, so nothing here settles it in either direction.

## Context-manifest delta

Read beyond §2's manifest, and why:
- `docs/findings/finding-0224.md`, `finding-0225.md` — bp-109 landed after this plan was written;
  0225 names the budget key's enable path as this plan's to define.
- `ops/import_lint.py` — ⚑ **§2's manifest points at `scripts/check_imports.py` as "the import
  walker", but that file is a 17-line CLI shim; the actual walker (`_imported_names`, `scan_file`,
  `Violation`) lives in `ops/import_lint.py`, which is NOT in write_scope.** Item 5 must therefore
  host its rule in `check_imports.py` while *importing* the walker from `ops.import_lint` — which
  satisfies §2's "no second walker" DRY mandate and the write_scope simultaneously. Resolved by the
  builder (`codebase`); no scope widening needed.
- `core/sealing.py` — confirms Q5: `seal()` is a per-process monkeypatch on `socket.socket.connect`
  with a module-global `_INSTALLED`, so a spawned process starts unsealed. V4 is real.
- `core/stores/vectorstore.py:36-80,142-200` — the real row schema for V1's payloads and the
  `all_rows`/`rows_for_source`/`search` signatures the §6 facade must mirror.
- `ops/lifecycle/launcher.py:559` — `tick_seconds = 1.0`, the tick budget V1 is judged against.
- `config/defaults.toml` `[runtime]` + `core/kernel/config/loader.py:312-339` — bp-115's
  `RuntimeConfig` is the exact in-repo precedent for landing a WHOLE config section (its docstring
  states the `_overlay`-drops-unknown-sections reasoning verbatim). `[scheduler]` follows it.
- `tests/integration/{test_cron,test_chat_sensor_wiring,test_research_cron}.py`,
  `tests/unit/test_restart_trustworthy.py`, `tests/e2e/test_scheduler_live.py`, `scripts/watch.py`
  — the `Supervisor(` construction sites §3 tells me to grep. Six outside the carried file; all
  keyword-constructed, so §6's defaulted additive fields break none of them. `scripts/watch.py:95`
  is a seventh (non-test) site.

Proved irrelevant so far: none.

---


Minted 2026-07-25 (session-48) by `/graduate`, decomposing both ratified ops notes
(`dn-supervision-and-liveness` and `dn-local-model-runtime`) in one context. **Not started.**

## Pre-build notes for whoever picks this up

⚑ **This is the biggest and most consequential plan of the supervision wave. Read it whole before
starting.** It owns the seam and no lane; bp-113 and bp-114 consume the protocol it defines.

- ⚑ **§3 Q3 is a GAP IN THE RATIFIED NOTE, resolved here, not re-litigated by you.** The note says
  the worker is handed "never a `VectorStore`" — true for WRITES, silent on READS. Three compute
  halves need store reads (`code_corpus.py:283,321`, and the proof lane's retrieval). §6 pins a
  read-only facade; §10 makes a LEAKING facade a STOP. If the writable handle is recoverable by
  `getattr`, pickling, or a closure, the tier-2 claim in a ratified note becomes false — which is
  worse than shipping nothing, because the note would be quoted as a guarantee.
- ⚑ **Subprocess, not `multiprocessing`, and the reason is the RATCHET** (§3 Q4). Under
  `multiprocessing` the worker's import graph is the parent's, so the tier-4 backing asserts
  nothing. Item 5 is only buildable with a separate `python -m scheduler.worker` entrypoint.
- ⚑ **V4: a spawned worker starts UNSEALED.** macOS uses spawn; `core/sealing.py` is a per-process
  monkeypatch. Item 2's falsifier is the most serious failure available here and it is SILENT.
- **`ambassador_task` is the proof lane** — it already has the target shape and the supervisor
  already lands its result (`supervisor.py:94-95`). No ingest handler changes in this plan.
- **Item 1 first.** If V5 shows the loop survives a pure-CPU thread, a RATIFIED decision rests on
  a false premise: §10 STOP and raise. Do not build subprocess anyway while knowing better.

## Owed at seal (orchestrator, not the builder)

Findings referenced in §4 Reconciliation are cross-referenced, never edited — a builder may not
edit an existing finding. Record closure evidence here for the orchestrator to apply at seal.
