---
type: build-plan
id: bp-105
track: ops
status: in-progress
design_ref: []
contract: builder
write_scope:
  - ops/lifecycle/launcher.py
  - ops/lifecycle/snapshot.py
  - scheduler/code_sync.py
  - tests/unit/test_status_incident_oracle.py
  - tests/unit/test_lifecycle_liveness.py
  - tests/unit/test_restart_trustworthy.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 180k
  actual: null
depends_on: []
parallelizable_with: []
created: 2026-07-25
updated: 2026-07-25   # session-47: ready -> in-progress
links:
  - docs/audits/ops-wave-2026-07-25.md
  - docs/findings/finding-0186.md
  - docs/findings/finding-0188.md
re_entry: null
supersedes: null
superseded_by: null
warrant: docs/findings/finding-0188.md
---

# Build Plan — the restart is trustworthy: a discriminating instrument and a fail-closed start

## 0. Mode & provenance

Corrective. Both items are audit findings against already-merged wave code
(`docs/audits/ops-wave-2026-07-25.md`), not new capability. Item 2 implements an
**owner ruling given 2026-07-25**: *"start should refuse outright if there is any
potential for an issue to occur — it is the system deeming an unrunnable state, which
helps us not shoot ourselves in the foot."*

Both items gate the same event: the Ops track's DoD says *"the restart PROVES it —
daemon back up, backfill completes to ~1,542 versions, **rate observable throughout**."*
Today the rate is not observable in the discriminating sense (finding-0188), so the
restart cannot prove that DoD item. This plan is what makes the restart count.

## 1. Objective

1. **The status block distinguishes a healthy backfill from a wedged one.** Today it
   cannot: both render identically.
2. **`start` refuses when a live supervisor genuinely owns the queue** — and does *not*
   refuse when the pid was merely recycled.

### 1.2 Non-goals (explicit — see §9)

Not fixing the whole wedge-detection design, not adding a job timeout (that is oq-0035,
a BUILD not a tune), not touching the sweep's own semantics (finding-0186's guard lives
in `start`, not in `sweep_orphans`).

## 2. Context manifest

- `ops/lifecycle/snapshot.py:301-339` — `StoreStats`, `read_store_stats`, `vector_rows`
- `ops/lifecycle/snapshot.py:574,585` — the `stalled` / `wedged` predicates
- `ops/lifecycle/launcher.py:505-545` — `start()`; the sweep call at `:538`
- `ops/lifecycle/launcher.py:115-122` — `_pid_alive` (pure `os.kill(pid,0)`, no identity)
- `ops/lifecycle/launcher.py:1124-1128` — `reset()`'s guard: **the pattern Item 2 copies**
- `ops/lifecycle/runs.py:32,65,104` — the `runs` table carries `pid` and `started_at`
- `scheduler/code_sync.py:53` — `code_backfill_handler`, the unbounded synchronous call
- `pyproject.toml:11` — **`psutil>=5.9` is already a dependency**, with a §2.5 typedshim

**Does core already have this?** Yes for liveness — `reset()` already implements the
guard Item 2 needs. Copy it, do not re-invent. `psutil` is already a dependency; do not
shell out to `ps`.

## 3. Investigation & grounding (Part A — do this BEFORE writing Item 1)

Item 1's *requirement* is pinned (§7); its **channel is not**, and must be grounded:

1. **`checkpoint()` is DISQUALIFIED as the progress channel.** `scheduler/queue.py:396-403`
   sets `state=QUEUED`, and after bp-101 a QUEUED row is a **collapse target** — a
   heartbeating job could be coalesced away mid-run. Confirm this against the code, then
   record it as a rejected alternative. (Source: audit, bp-101 auditor F3.)
2. **Find the existing telemetry-vital mechanism** the SEAMS auditor referenced ("no
   telemetry vital") and determine whether it is the right channel.
3. **Choose the progress channel** from: (a) supervisor-written periodic sample the
   status block differences; (b) an additive `jobs` column (note: `_MIGRATIONS` is a
   growing tuple and its check+ALTER is **not race-safe** — bp-101 auditor F2 — fix that
   one-liner if you touch it); (c) an existing vitals surface.
   **Recommended: (a)** — the supervisor is already the single writer, and it keeps
   `status` off the write path (`status` is *already* not read-only; do not worsen it).

Record the choice and the rejected alternatives in the journal before writing code.

## 4. Reconciliation (Part B)

After grounding, reconcile §7's pinned acceptance against the channel you chose. If the
chosen channel cannot satisfy Item 1's falsifier, **stop and raise** (§10) rather than
weakening the falsifier — weakening the falsifier to fit the implementation is the exact
defect class this plan corrects.

## 5. Write scope

`launcher.py` (Item 2's guard, Item 1's render), `snapshot.py` (the predicates and
stats), `scheduler/code_sync.py` (progress emission if the chosen channel needs it),
plus the three test files. `tests/unit/test_restart_trustworthy.py` is new and holds the
cross-cutting "both states render differently" test.

## 6. Interfaces pinned inline

**Item 2 — the guard. Copy `reset()`'s shape, add identity:**

```python
# in start(), BEFORE runs.open_run(...)
prev = self.runs.last()
if prev is not None and prev.active and _supervisor_alive(prev):
    print(f"refusing to start — run #{prev.id} (pid {prev.pid}) is live. `palace stop` first.")
    return 1
```

**`_supervisor_alive(run) -> bool` — identity-checked liveness (NEW):**

```python
def _supervisor_alive(run) -> bool:
    """True only if `run.pid` is alive AND is plausibly THAT run's supervisor.

    `_pid_alive` alone is pid-EXISTENCE, and it deliberately reports a foreign owner as
    ALIVE (test_pid_alive_treats_a_foreign_owner_as_ALIVE). After an unclean exit the OS
    may recycle the pid to an unrelated process; keying a fail-closed `start` on
    existence alone would refuse FOREVER — under launchd KeepAlive, a self-inflicted
    brick. A process created BEFORE its own run row cannot be that run's supervisor.
    """
    if not _pid_alive(run.pid):
        return False
    # psutil is already a dependency (pyproject.toml:11) with a §2.5 typedshim.
    # Compare Process(run.pid).create_time() against run.started_at.
    # On ANY ambiguity (process vanished, permission denied, unparseable timestamp):
    # return True — fail CLOSED, per the owner ruling. Refusing wrongly is recoverable
    # by `palace stop`; starting wrongly corrupts the queue.
```

**The ambiguity rule is load-bearing and is the owner's ruling applied:** when identity
cannot be established, **refuse**. The recycled-pid carve-out is only for the case where
identity is *positively disproven*.

**Item 1 — the predicates.** `stalled` and `wedged` must not fire while the running job
is demonstrably progressing. Exact predicate shape depends on §3's channel; the
*falsifier* (§7) is fixed regardless.

## 7. Items

### Item 1 — the status block discriminates healthy from wedged (warrant finding-0188)

**Acceptance:** construct BOTH states — a healthy backfill genuinely embedding under a
live daemon, and the incident's wedged job under a live daemon — render the status block
for each, and assert the outputs **differ**.

**Named falsifier:** *the two renders are identical.* This is the plan's whole reason to
exist; if they match, the instrument has failed regardless of any other test passing.

**Second falsifier (the false-alarm guard, rebuilt):** the "healthy system raises no
flags" fixture must be **non-trivial** — `depth > 0` with a running job — so that every
anomaly predicate's preconditions are actually satisfiable. Prove the guard bites by
mutating each predicate to fire unconditionally and confirming the test fails. The
current fixture (`depth == 0`, no running row) makes both predicates unreachable by
construction; mutating `stalled` to a permanent alarm passes all 9 tests today.

**Invariant:** `status` gains no new unbounded I/O path. (Note finding-0195: it already
carries an uncosted 120 s Ollama call — do not add a second.)

### Item 2 — `start` refuses on an identity-confirmed live supervisor (warrant finding-0186)

**Acceptance:** with a run row marked active and a pid that is alive *and* identity-
confirmed, `start` prints the refusal and returns 1 **without opening a run or sweeping**.

**Named falsifier A (the hazard):** a second `start` against a live supervisor reclaims
the first's in-flight rows. Reproduce the audit's scenario and assert it now refuses.

**Named falsifier B (the trap — equally required):** *a recycled pid bricks start
forever.* Simulate a run row whose pid is alive but whose process predates the run row;
assert `start` **proceeds**. A guard that cannot distinguish these is not shippable.

**Invariant:** `--force` must **not** bypass this guard. The whole point of the ruling is
that a live supervisor is an unrunnable state; `--force` overrides *preflight*, not
*safety*. Update the recovery message at `launcher.py:528-529`, which currently prints
`start --force` as the remedy — it must instead direct the operator to `palace stop`.

### Item 3 — the sweep call is covered (warrant finding-0187)

**Acceptance:** an integration test drives `Launcher.start()` against a **real**
`JobQueue` (not `_FakeQueue`) with a pre-seeded stranded RUNNING row, asserting the row
is reclaimed **and** that adoption happened before the first `claim()`.

**Named falsifier:** *deleting the `sweep_orphans` call at `launcher.py:538` leaves the
suite green.* It does today — 85/85. This test must fail when the line is removed,
when the run id is wrong, and when the call moves after `_serve()`.

## 8. Math carried explicitly

N/A — no new mathematical object. Item 1 is a predicate correction, not a model.

## 9. Non-goals

- **No job-level timeout.** That is oq-0035 / finding-0178 and is a BUILD, not a tune.
- **No change to `sweep_orphans`' own semantics.** The guard belongs in `start`.
- **Not fixing finding-0195** (the 120 s Ollama call) — separate concern, separate plan.
- **Not fixing finding-0197** (the unguarded sweep / no telemetry) unless Item 3's test
  makes it free; if it does not, file rather than widen.

[INFERENCE] These non-goals are inferred from right-sizing, not from an owner statement.
Read them at the gate — a wrong non-goal fails silently forever (finding-0150).

## 10. Stop-and-raise conditions

- Item 1's channel cannot satisfy the "both states differ" falsifier ⇒ **STOP**, file,
  do not weaken the falsifier.
- The recycled-pid carve-out cannot be implemented without a new dependency ⇒ **STOP**
  (`psutil` is already present; if it proves unusable here, that is a design question).
- Item 3 reveals that `Components` cannot accept a real `JobQueue` without a structural
  change ⇒ **STOP and raise**; that is a seam-design question, not a builder's call.

## 11. Parked decisions

None at authoring. Item 1's channel is a §3 grounding choice, not a parked decision.

## 12. Dependency & ordering summary

Item 2 → Item 3 → Item 1. Item 2 is smallest and highest-safety (it closes the live
hazard). Item 3 establishes the real-`JobQueue` integration harness that Item 1's
two-state test can then reuse. Item 1 is the largest and depends on §3 grounding.
