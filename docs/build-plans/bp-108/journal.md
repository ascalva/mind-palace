---
type: journal
plan: bp-108
started: 2026-07-25
updated: 2026-07-25
---

# Journal — bp-108 (the supervisor role becomes exclusive)

Minted 2026-07-25 (session-48) by `/graduate`, decomposing both ratified ops notes
(`dn-supervision-and-liveness` and `dn-local-model-runtime`) in one context. **Started
2026-07-25** by a delegated builder in worktree `worktree-agent-afd9955cc85840a13`, based on
`origin/main` @ `7b37453` ("bless(bp-107,bp-108,bp-115): proposed -> ready").

## Pre-build notes for whoever picks this up

- **Item 1 (V8) gates everything.** If `uv run` holds the lock from a wrapper process rather than
  the python process, the mechanism is mis-tiered and §10 says STOP. Do not build Items 2-5 first
  and measure afterwards.
- ⚑ **The interim fix is SMALLER than the note implies.** `Supervisor.run` already accepts
  `max_ticks` (`scheduler/supervisor.py:99`); only the call site (`launcher.py:676`) is wrong.
  If you find yourself editing `scheduler/`, you are fixing it in the wrong place.
- ⚑ **The sleep is the other half of Item 4.** `launcher.py:694-695` sleeps unconditionally per
  iteration. Bound the drain without making the sleep conditional and 1,766 no-ops take ~29 min.
- **Do NOT delete bp-105's identity gate.** It is demoted in documentation, kept in code: the lock
  can only say no, the gate can say why (§3 Q4).
- **`scripts/watch.py` is NOT deleted.** V7 is unanswered (§3 Q6); bring it under the lock instead.

## Owed at seal (orchestrator, not the builder)

Findings referenced in §4 Reconciliation are cross-referenced, never edited — a builder may not
edit an existing finding. Record closure evidence here for the orchestrator to apply at seal.

---

## Item 1 — V8: `flock` measured where it will actually run ✅ PASS (no STOP)

**Verdict: the falsifier does NOT fire.** Built Items 2-5 on this. Full driver scripts lived in
the session scratchpad (measurement-only, per Item 1's "Files: none"); every command and its
output is transcribed below so the measurement is reproducible from this journal alone.

Platform: macOS 25.5.0 (Darwin), `data/` on `/dev/disk3s5` **apfs** (`df -Y`), uv at
`/opt/homebrew/bin/uv`, python `.venv/bin/python3` (CPython 3.13.14).

### (a) two processes on APFS under `data/` — the second is refused

Holder opens `data/v8-throwaway.lock` with `os.open(O_CREAT|O_RDWR)` then
`fcntl.flock(fd, LOCK_EX|LOCK_NB)`; a separate process attempts the same.

```
$ uv run python v8_holder.py <lockfile>
HELD pid=29796 ppid=29795 exe=.../.venv/bin/python3
$ python v8_probe.py <lockfile>          -> rc=1
BLOCKED pid=29805 errno=35 (Resource temporarily unavailable)
```

`errno 35` = `EAGAIN`/`EWOULDBLOCK` — advisory `flock` holds on APFS. ✅

### (b) ⚑ the holder IS python, but NOT because `uv run` execs — it FORKS

This is the one place the plan's grounding was wrong, and it looked like the STOP condition
at first glance. **Read this before concluding anything from a pid comparison.**

```
$ uv run python v8_holder.py <lockfile>
wrapper(uv)=30413  python=30414          <- TWO pids. uv did NOT exec in place.
$ lsof <lockfile>
COMMAND     PID    USER   FD   TYPE  NAME
python3.1 30414 ascalva    3u   REG  .../data/v8-throwaway.lock
=> wrapper 30413 appears in lsof: False
$ pgrep -fl v8_holder.py
30413 uv run python v8_holder.py <lockfile>
30414 .../.venv/bin/python3 v8_holder.py <lockfile>
```

bp-108 §3 Q7(b) says "`uv run` execs into python on this platform, but that must be
*observed*, not assumed." **Observation refutes the exec, and confirms the conclusion it was
supporting.** uv spawns a child python and waits on it; the lockfile fd is opened by python
*after* the fork, so the wrapper never holds it. Item 1's acceptance criterion (b) is stated
in terms of `lsof`, not pid identity — *"the holder pid **is** the python process, not a
wrapper (`lsof <lockfile>`)"* — and by that criterion it PASSES.

Isolating the "wrapper outlives python" direction (kill the python child only, do **not**
reap the wrapper, then poll):

```
kill -9 30414   # the lock holder only
successor acquired after 19 ms
uv wrapper still un-reaped at that moment: False
```

The wrapper exits as soon as its child dies, and it held nothing regardless. Filed as
**finding-0200** (`discovery`, route builder, resolved in-plan) so bp-111 inherits the
measured mechanism instead of the assumed one — the lease-home decision (§2.6: "a row in
`runs.sqlite` **or** the lockfile's mtime") keys on exactly this.

### (c) SIGKILL frees it with no residue; a successor acquires immediately

```
$ kill -9 29796
holder reaped, rc=137
lockfile still exists after holder death: True (size=0)
$ lsof <lockfile>        -> <no output, rc=1>  — nothing holds it
$ python v8_probe.py <lockfile>  -> rc=0  (17 ms)
ACQUIRED pid=29808
```

**No stale-lock state exists.** The zero-byte file persisting is not residue in any
operational sense: it carries no state, and the kernel dropped the lock at process death.
Nothing needs cleaning up after a crash — which is precisely the property §6 of the plan
claims for the primitive. ✅

### (c') the launchd `KeepAlive` restart shape — §10's second STOP does not fire

`ops/lifecycle/com.mind-palace.palace.plist` runs `ProgramArguments = [/opt/homebrew/bin/uv,
run, .../scripts/palace.py, start]` with `KeepAlive=true` and `ThrottleInterval=10`.
Combined with (b): launchd watches the **uv wrapper**, and uv exits only *after* its python
child (the lock holder) has died. So the lock is always free before launchd even observes the
job exit, and `ThrottleInterval=10` puts a 10-second floor on the restart against a measured
**19 ms** release.

```
predecessor: HELD pid=29809 ... ; SIGTERM (graceful, as launchd's stop does)
successor immediately after predecessor reaped: rc=0 (17 ms) -> ACQUIRED pid=29810
```

⇒ the lock **cannot** convert a KeepAlive restart into an outage. §10 STOP condition 2 is
measured shut, not argued shut.

### Bonus measurement that shaped Item 2's test

```
SAME-PROCESS-SECOND-FD BLOCKED errno=35
```

A second `open()` + `flock` **in the same process** is *refused* on this platform — `flock`
is per-open-file-description (unlike `fcntl.lockf`/POSIX record locks, which are per-process
and WOULD self-grant). Item 2's falsifier text reads as though a re-open self-grants; the
measured behaviour is the opposite, and it is the *safer* direction. The forked-subprocess
test the falsifier demands is still the one that matters and is still what got written —
a same-process test would pass for a reason that does not generalize.

---

## Item 2 — `ops/lifecycle/lock.py` + `tests/unit/test_supervisor_lock.py` ✅

`SupervisorLock` is built exactly to the §6 pin (`path`, `acquire`, `release`, `__enter__`,
`__exit__`, `SupervisorLockHeld`), plus one addition the pin did not name: a read-only `held`
property. It exists because `_shutdown` must be able to release unconditionally, and asking
"do I hold it?" is the only honest question the object can answer (a lock held by *another*
process is deliberately not observable from here).

**15 tests, all green.** `uv run pytest tests/unit/test_supervisor_lock.py -q` → `15 passed`.

### The falsifier, exercised — three planted mutations

Item 2's named falsifier is *"a second acquirer in the SAME process succeeds"*, with the
rationale that a same-process test alone would pass while the guarantee is absent. Drilled with
three mutations of the `acquire()` flock line (harness in the session scratchpad):

| mutation | tests reddened |
|---|---|
| **M1** flock call deleted outright | **8** — incl. both cross-process tests |
| **M2** `LOCK_SH` (shared, so everyone is admitted) | **8** — same set |
| **M3** `fcntl.lockf` (POSIX record locks: per-PROCESS, not per-fd) | **1** — the same-process test ONLY |

⚑ **M3 inverts the falsifier's own rationale, and it is the reason both kinds of test are in
the file.** The plan reasons that a cross-process test is the load-bearing one and a
same-process test would be a false comfort. M1/M2 confirm that. But M3 — swapping `flock` for
`lockf`, which is the single most plausible way to get this wrong — leaves **every cross-process
test green** and is caught *only* by
`test_a_second_lock_object_in_the_same_process_is_also_refused`. POSIX record locks are
per-process, so they exclude other processes correctly while silently self-granting inside the
daemon. Neither test class subsumes the other; the file keeps both, and the same-process test's
docstring now says explicitly that it is not the tier-3 guarantee.

### ⚑ Two real defects found and fixed while drilling — read these before re-running anything

**(1) A leaked forked holder wedges any capturing parent.** The first drill run HUNG (killed at
600 s). Cause: `_forked_holder` originally returned a pid and relied on the test's `finally` to
kill it. Under M1 an assertion failed *before* that cleanup, so the child leaked, was reparented
to init, and kept pytest's inherited **stdout pipe** open — `subprocess.run(capture_output=True)`
then waited on EOF forever. Confirmed as `pid 35638, ppid 1` still holding the pipe.

Fixed structurally, three ways, in `_forked_holder` (now a `@contextmanager`): unconditional
kill+reap in `finally`; the child re-points fds 0/1/2 at `/dev/null` immediately after the fork
so a leaked child can never hold a capture pipe; and the child self-terminates after 60 s. Any
one of the three would have prevented the hang — a failing test must never be able to hang.

**(2) ⚑ The mutation drill silently ran STALE BYTECODE. Filed as finding-0201.** After the
harness restored a byte-identical original, the suite still reported `1 failed, 14 passed`, and
kept doing so on a fresh invocation. `inspect.getsource` showed correct source. Spying on
`fcntl.flock` revealed it was **never called**:

```
b.acquire():
  open(PosixPath('.../supervisor.lock'), flags=514) -> fd 4
 -> GRANT                      # ...and no flock(...) line at all
```

CPython invalidates a `.pyc` on **(source mtime, source size)**. `lockf`/`flock` are the same
length and `LOCK_SH`/`LOCK_EX` are the same length, so M2 and M3 — and the restore — changed
neither, within the same mtime second. The interpreter kept the M3 bytecode. Every drill result
above was re-taken after adding a `__pycache__` sweep between mutations; the restored run is now
`rc=0, 15 passed`. **This matters beyond bp-108:** every plan here discharges named falsifiers
by planting mutations, and this failure mode reports a *false* verdict in the direction of
confidence. finding-0201 asks the orchestrator whether the drill procedure should carry the
guard as standard.

### Deliberate design choices, and what would show them wrong

- **No pid written into the lockfile.** Tempting diagnostics, but it reintroduces exactly what
  §2.6 removes: a stored assertion outliving its actor. `test_the_lockfile_carries_no_state`
  pins it. The "which run, and why" answer stays with bp-105's identity gate.
- **`release()` does not unlink.** Unlinking races a successor that has already opened the path,
  which would leave two processes flocking two different inodes under one name — two
  supervisors, the exact outcome the module prevents. `test_release_does_not_unlink_the_lockfile`.
- **`release()` is idempotent**, so `_shutdown` (Item 3) can call it unconditionally rather than
  tracking whether `start()` got far enough to acquire.
- **Re-acquire on the same object raises `RuntimeError`, not `SupervisorLockHeld`.** Blaming
  "another process" for a caller bug (two acquisition sites, a missing release) would be a lie
  about which process is at fault.
- **The lock fd must not survive into a child.** `ops/lifecycle/children.py` spawns the edge
  monitor via `subprocess.Popen(argv)`; an inherited descriptor would keep the lock alive after
  the supervisor died and lock the successor out **forever** — exclusivity turned into a
  permanent outage. Two independent guards (PEP 446 non-inheritable-by-default, and `Popen`'s
  `close_fds=True`), both asserted in
  `test_the_lock_descriptor_is_not_inherited_by_spawned_children`, so a future `close_fds=False`
  reddens instead of quietly bricking restarts.

---

## Item 3 — `start()` acquires the lock; the gate is re-documented as a diagnostic ✅

Committed `8d873a0`. `start`'s body moved into a new `_start_locked` so the acquisition has **one**
paired release rather than one per early return; `start` itself is now gate → lock → delegate →
`finally: _release_lock()`.

**Placement, and why it is not merely "before `sweep_orphans`".** The plan requires the acquire
before `sweep_orphans` (`:653`). It is placed earlier still — immediately after the identity gate
and *before preflight* — for the gate's own stated reason (finding-0195): an unrunnable state must
not first cost the operator preflight's uncosted 120 s Ollama probe. Ordering is therefore
**gate (explains) → lock (guarantees) → preflight → sweep**, which is also the order §4 of the plan
describes ("the gate ... sitting ahead of the kernel-held lock").

**The gate's comment block was corrected, not deleted** (§4's banner). It claimed to be the
"SINGLE-INSTANCE GATE ... NOT bypassable by --force"; the first half of that is now false. It reads
`SINGLE-INSTANCE **DIAGNOSTIC**`, names both ladder tiers (gate = 5, a probe with a check-then-act
window; lock = 3, atomic), and says explicitly that deleting the gate would lose the *explanation*,
not the *exclusion*. Behaviour at that site is unchanged — all of bp-105's 24 tests still pass
untouched, and **no assertion in `test_restart_trustworthy.py` was weakened** (§10's fourth STOP
condition). The only edits to existing code there were widening two fake supervisors' signatures.

**Release ordering is load-bearing.** `_shutdown` releases **after** `runs.mark_stopped`.
Releasing earlier would open a window where a successor holds the lock while this run's row is
still active — so the successor's `sweep_orphans` would find live rows to reclaim, which is
finding-0186 reintroduced by an ordering mistake. `start`'s `finally` is the net for paths that
never reach `_shutdown` (a failed preflight returns before `open_run`); without it, one bad start
would poison every later one, and under launchd `KeepAlive` that is an unrecoverable restart loop
rather than an inconvenience.

### The falsifier, exercised — and one mutation that initially caught NOTHING

Item 3's named falsifier is *"deleting the `acquire()` call leaves the suite green"* — finding-0187's
exact failure mode reproduced in a new mechanism.

| mutation | tests reddened |
|---|---|
| **L1** the `acquire()` call deleted outright | **5** |
| **L2** the release in `_shutdown` deleted | **0** → then **1** (see below) |
| **L3** acquisition genuinely MOVED to after the sweep | **4** |

⚑ **L2 reddened nothing on the first pass, and that was a real coverage gap, not a false alarm.**
Because `start`'s `finally` also releases, deleting `_shutdown`'s release changed no observable
behaviour — so the plan's own acceptance criterion ("released in `_shutdown`") was an *untested
claim*. Rather than delete the redundant call, the behaviour is now pinned directly:
`test_shutdown_relinquishes_the_role_on_its_own` and
`test_shutdown_releases_even_when_there_is_no_run_to_close` drive `_shutdown` on its own. L2 now
reds. Keeping both sites is deliberate — `_shutdown` is the semantic release point (the role is
relinquished when the run ends), `start`'s `finally` is the safety net — and each is now
independently asserted.

L3 was rewritten mid-drill: the first version replaced the acquire with `pass` and so was just a
duplicate of L1. The real relocation removes it from its site **and re-inserts it after
`sweep_orphans`**, so the lock still exists and still excludes — just too late. It reds 4 tests,
including `probes["preflight"] == 0` (a lock acquired after preflight refuses too slowly).

---

## Item 4 — the drain is bounded, and the sleep stops being unconditional ✅

Committed `c22058f`. `scheduler/supervisor.py` is **untouched**, as §5 requires — `run` already
took `max_ticks`; only `launcher.py:676` was wrong.

`SupervisorLike` was widened from `run() -> object` to `run(*, max_ticks=None) -> int`, because
`_serve` now uses **both** halves: the bound returns control at a job boundary, and the returned
dispatch count is what makes the sleep conditional.

K lives in **one** place — `DEFAULT_DRAIN_MAX_TICKS = 64` in `launcher.py`, with
`Launcher.drain_max_ticks` defaulting to it and `scripts/watch.py` importing it. Two serve loops
with two different duty cycles would be two answers to one question. It is a field, not config:
the config loader is schema'd and drops unknown sections, so a `[scheduler]` key would be inert
today (finding-0174) and that schema change belongs to bp-110.

⚑ **`drain_max_ticks` is NOT `start(max_ticks=…)`.** The plan's invariant, honoured and commented
at both sites: the outer value bounds serve-loop *iterations* and is the test seam; the inner one
bounds *dispatches*. Conflating them would make a test's `max_ticks=1` silently mean "dispatch one
job".

`_idle` keeps its unconditional sleep, deliberately and now with a test
(`test_recovery_mode_keeps_its_unconditional_sleep`): recovery halts the scheduler entirely, so
there is never a drain to be idle after. Without that test, a future "unify the two loops" tidy-up
would silently spin recovery mode at 100 % CPU.

### The falsifier, exercised — both halves, mutated separately

| mutation | tests reddened |
|---|---|
| **L4** the bound removed (back to a bare `run()`) | **3** |
| **L5** the sleep made unconditional again | **2** |

The throughput falsifier is measured in wall-clock, not asserted in the abstract:
`test_a_no_op_backlog_does_not_take_N_times_tick_seconds` drains the plan's own **1,766** no-ops
through a fake that honours `max_ticks` exactly as the real `Supervisor.run` does (and treats
`max_ticks=None` as "drain until empty", which is the pre-fix behaviour — that fidelity is what
makes L4 red). At K = 64 the backlog needs ⌈1766/64⌉ = **28** passes, every one of which must skip
the sleep. Both mutations red it.

---

## Item 5 — `watch.py` cannot be the second claimant ✅

`scripts/watch.py` now: acquires the same `SupervisorLock` **first** — before the queue, the
loader, the supervisor or the watcher exist — opens a real run row, sweeps orphans with that id,
drains with the daemon's own K, and releases the role after `mark_stopped`.

⚑ **The falsifier drove the design.** Item 5's named falsifier is *"it acquires the lock but still
runs with `active_run_id = None`"* — the lock stops a *second* claimant but does nothing about the
NULL stamp when this script is the *only* one, and a NULL stamp is by definition reclaimable. So
the plan's acceptance ("acquire + bound") is **not sufficient on its own**, and the falsifier says
so: it must "either call `sweep_orphans` or refuse". That is why the run ledger appears here at
all — `sweep_orphans` needs a run id to adopt, and the only honest source of one is a real row.

**Consequence recorded in the docstring, because it is a behaviour change an operator can see:**
while `watch.py` runs, `palace status` shows it as the live run, and killing it uncleanly leaves an
unclean row so the next `palace start` comes up in recovery mode. That is the honest accounting of
what the script is — a supervisor — rather than a quiet exception to it.

The module docstring was rewritten per §4's banner: it now states the hazard (a second `Supervisor`
over the shared queue, NULL-stamping rows the daemon's sweep can reclaim), both closures, and that
V7 is unresolved — which is why it is bounded rather than deleted (§9, §10). **The script is not
deleted.**

### Acceptance, end to end and for real

The literal criterion — *"Running it while the daemon is up exits non-zero **without claiming a
single row**"* — was executed, not just unit-tested. A separate process held the lock; the real
script was then run:

```
$ uv run scripts/watch.py   -> rc=1  (1.0s)
refusing to start — another process holds the supervisor lock (…/data/supervisor.lock).
The palace daemon supervises this queue and runs this watcher itself, so there is nothing for
this script to do while it is up. Check with `palace status`; stop it with `palace stop` …

  exits non-zero:             True
  names the lock:             True
  claimed NOTHING (no queue): True     <- queue.sqlite was never even created
  opened NO run row:          True     <- runs.sqlite likewise
```

**A risk this introduced, checked rather than assumed:** `main()` now imports
`ops.lifecycle.launcher` (for K) *after* `seal()` has monkeypatched the process. The script never
imported `ops` before, so the sealed-import path is new. Verified explicitly — every import in
`main()` resolves under the seal, `K = 64`.

### Enforcement, and its honest limit

An end-to-end happy-path test is **not** available in this plan's write scope: `main()` calls
`seal()` (a process-wide monkeypatch that would follow the rest of the suite) and reads the real
`data_dir` with no injection seam, and Item 5's `Files:` list is `scripts/watch.py` alone. What is
pinned instead — in `tests/integration/test_lifecycle.py`, which IS in scope — are four **AST-level
ratchets** over the real source, one per hazard: the acquire precedes both `JobQueue(` and
`Supervisor(`; the `SupervisorLockHeld` handler returns non-zero; `open_run` → `sweep_orphans` →
first `run` in that order; and the drain reuses `DEFAULT_DRAIN_MAX_TICKS` rather than re-declaring
a literal. These are structural, not behavioural — stated plainly in the test module so nobody
mistakes them for the stronger thing. The refusal path *is* covered behaviourally, by the
end-to-end run above.

---

## Green gate — all six legs, run separately

| leg | result |
|---|---|
| `uv run ruff check .` | **All checks passed!** |
| `uv run python scripts/check_imports.py` | **OK** — core imports no zone or networking module |
| `uv run mypy core agents eval ops scheduler scripts` | **Success: no issues found in 256 source files** |
| `uv run mypy` (argless) | **69 errors in 20 files** — exactly the pinned tests/ baseline, unmoved |
| `uv run python -m ops.type_gate` | **OK** — Tier-2 membership + bare-ignore scan |
| `uv run pytest -q` | 1 failed, **2088 passed**, 15 skipped |

The single failure is `tests/unit/test_core_self_containment.py::test_core_imports_nothing_outside_core`
— the finding-0105 decision-A **intentional red**, which is the one node `Launcher.gate_cmd`
deselects (`launcher.py`, unchanged by this plan). Under the gate's own selection:

```
uv run pytest -q -m "not live and not podman and not needs_vault and not needs_restic" \
  --deselect tests/unit/test_core_self_containment.py::test_core_imports_nothing_outside_core
2072 passed, 11 skipped, 21 deselected, 12 warnings in 38.51s
```

**The 12 warnings are new and mine**, so they are named rather than left to be discovered:
`DeprecationWarning: This process is multi-threaded, use of fork() may lead to deadlocks in the
child`, from `test_supervisor_lock.py`'s `os.fork()`. The fork is deliberate — it is the strongest
form of the Item 2 falsifier (a child that shares everything) — and the children do only
`os.open`/`flock`/`os._exit`, never allocation-heavy or ObjC work. `filterwarnings` has no `error`
entry, so this does not fail the suite today; it would become a problem only if CPython promotes
it. The cross-process claim is *also* covered by a fresh-interpreter subprocess test, so if that
day comes the fork tests can be dropped without losing the guarantee.

---

## Owed at seal — closure evidence for the orchestrator

**finding-0186 (`blocker`, its OPEN half).** The finding's re-entry condition says: *"do NOT run
`scripts/watch.py` against the shared queue concurrently."* That is now structurally impossible
rather than a standing instruction — evidence above under Item 5 (rc=1, nothing claimed, no run
row). The route it named (`watch.py:39-47` building a second `Supervisor` with `active_run_id=None`)
is closed twice over: the lock denies the concurrency, and the run row + sweep deny the NULL stamp.
The builder has **not** edited the finding.

**finding-0187 (`spec-defect`).** Its lesson — an untested switch is a claim, not a mechanism — was
applied as a procedure, not a citation: every new mechanism here was mutation-drilled, and the one
that reddened nothing (L2) was treated as a coverage gap and fixed. Not closed by this plan; the
leased-rows ratchet it asks for is bp-109's.

**New findings filed:** finding-0200 (`discovery` — `uv run` forks rather than execs; bp-111's
lease-home decision keys on it) and finding-0201 (`discovery` — a mutation drill can silently run
stale bytecode; asks whether the drill procedure should carry a `__pycache__` sweep as standard).

**V7 remains unanswered and is NOT parked-blocking.** Nothing in the repository imports or invokes
`scripts/watch.py`; the daemon builds its own vault watcher. Whether a human still runs it by hand
needs an owner statement. Item 5's action was the one available without that answer, so no
criterion is parked and no re-entry condition is owed.
