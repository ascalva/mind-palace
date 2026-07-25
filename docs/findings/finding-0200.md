---
type: finding
status: open
id: finding-0200
created: 2026-07-25
updated: 2026-07-25
links:
  - docs/build-plans/bp-108/plan.md
  - docs/design-notes/dn-supervision-and-liveness.md
  - ops/lifecycle/com.mind-palace.palace.plist
  - ops/lifecycle/lock.py
ftype: discovery
origin_plan: bp-108
route: builder
resolution: >
  Resolved in-plan. V8 PASSES, but by a different mechanism than bp-108 §3 Q7(b)
  assumed: `uv run` FORKS, it does not exec. The lock is nonetheless held by the
  python process alone (lsof shows no wrapper fd), so the guarantee stands. Item 2
  built on the measured mechanism, not the assumed one.
---

# V8 measured: `uv run` forks rather than execs — the lock still lands on python, for a
# different reason than the plan assumed

## What
bp-108 §3 Q7(b) grounds the supervisor lock on an assumption it explicitly flagged as
needing observation: *"whether the lock is held by the **supervisor's** python process
rather than a `uv run` wrapper that exits — `uv run` execs into python on this platform,
but that must be observed, not assumed."*

Measured on APFS (`/dev/disk3s5`, `data/`), macOS 25.5.0, uv from `/opt/homebrew/bin/uv`:

```
$ uv run python v8_holder.py <lockfile>
wrapper(uv)=30413  python=30414          <- TWO pids: uv does NOT exec in place
$ lsof <lockfile>
COMMAND     PID    USER   FD   TYPE  NAME
python3.1 30414 ascalva    3u   REG  .../data/v8-throwaway.lock
=> wrapper 30413 appears in lsof: False  <- but the wrapper holds NO fd
```

**The exec claim is false; the conclusion it was supporting is true.** `uv run` spawns a
child python and waits on it. The lockfile fd is opened *by python, after the fork*, so
the wrapper never holds it and cannot outlive it. The falsifier as stated in Item 1 —
*"`uv run` holds the lock from a wrapper process that outlives or precedes python"* —
does not fire: the wrapper neither holds nor precedes the lock.

Supporting measurements (all in `docs/build-plans/bp-108/journal.md` with commands):

| observation | result |
|---|---|
| second process, `LOCK_EX\|LOCK_NB`, while held | `BLOCKED errno=35 EAGAIN` |
| SIGKILL the holder → successor acquires | 17-19 ms, no residue, zero-byte file remains |
| kill python only, wrapper un-reaped → successor | acquires (wrapper holds nothing) |
| same-process second `open()` + flock | `BLOCKED errno=35` — flock is per-open-file-description |

## Why it matters
Two downstream consumers key on *which process* owns the lockfile, and both would be
mis-grounded by the exec claim:

1. **bp-111 (the supervisor lease).** `dn-supervision-and-liveness` §2.6 offers "a row in
   `runs.sqlite` **or** the lockfile's mtime" as the lease home, and V9 picks between them.
   If the lease is the lockfile's mtime, the renewer is the python process — the same one
   that records `pid=os.getpid()` in the run ledger. Consistent, but only because of the
   fork-and-hold-in-child shape measured here, not because of an exec.
2. **launchd KeepAlive restart ordering** (bp-108 §10's second STOP condition). launchd
   watches the *top* process, which is `uv` (`ProgramArguments = [uv, run,
   scripts/palace.py, start]`, `KeepAlive=true`, `ThrottleInterval=10`). Because uv waits
   on its python child, the lock holder is **always dead before launchd observes the job
   exit**, and `ThrottleInterval=10` adds a 10 s floor on top of a measured 19 ms release.
   The restart-outage STOP condition therefore cannot fire — but that argument depends on
   the fork shape. Under a hypothetical exec, the reasoning would be simpler; under a
   wrapper that *retained* an fd it would be false.

The correction is small but it is the kind that fails silently: a future reader who trusts
the exec claim would conclude "one process, nothing to reason about" and would not notice
if a `uv` version change started holding a descriptor.

## Re-entry condition
None — nothing is parked. This is a grounding correction recorded so bp-111 inherits the
measured mechanism rather than the assumed one. Re-measure if the uv version changes such
that `pgrep -fl` shows the wrapper holding an fd on the lockfile.

## Routing
`discovery` on a builder-resolvable grounding detail → route `builder`. Resolved within
bp-108: Item 2 is built against the measured behaviour and Item 1's acceptance criterion
(b) — *"the holder pid **is** the python process, not a wrapper (`lsof <lockfile>`)"* — is
satisfied as written. No owner input needed. Flagged to the orchestrator only so the
plan's §3 Q7 text is not carried forward verbatim into bp-111's grounding.
