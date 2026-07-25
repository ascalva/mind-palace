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
