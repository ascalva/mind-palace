---
type: build-plan
id: bp-121
track: ops
status: ready
design_ref: []
contract: builder
write_scope:
  - ops/lifecycle/launcher.py
  - tests/unit/test_restart_trustworthy.py
session_budget: 1
cost:
  estimate:
    model: sonnet
    tokens: 60k
  actual: null
depends_on: []
parallelizable_with: []
created: 2026-07-26
updated: 2026-07-26
links:
  - docs/findings/finding-0211.md
  - docs/findings/finding-0186.md
  - docs/findings/finding-0198.md
re_entry: null
supersedes: null
superseded_by: null
warrant: docs/findings/finding-0211.md
---

# Build Plan — make D2's interpreter probe platform-robust, and get CI green

## 0. Mode & provenance

Investigation complete and recorded in `finding-0211` (root cause narrowed to a single branch by
the CI log's own values). This plan corrects committed code from bp-105 (`2add267`); it carries
`warrant: docs/findings/finding-0211.md` accordingly. Authority to act is the owner's instruction
this session ("investigate … give me the design plan, and I clear and you go"); the readiness
blessing (`proposed → ready`) remains the owner's, by hand.

## 1. Objective

Make `_supervisor_alive`'s D2 disproof ask "is this process a Python interpreter?" in a way that does
not depend on how the interpreter was invoked, so the authoritative CI `ratchet` job is green again.

## 2. Context manifest

Read in this order, whole files before citing:

1. `docs/findings/finding-0211.md` — the diagnosis; do not re-derive it. D1 is arithmetically excluded
   by the logged `RunRecord`; D2 is the firing branch.
2. `ops/lifecycle/launcher.py` — `_pid_alive` (`:126`), `_CLOCK_SLACK_S` (`:140`),
   `_process_identity` (`:143-173`), `_supervisor_alive` (`:176-221`). The docstrings are load-bearing:
   they record the owner ruling and why `cmdline()` was rejected.
3. `tests/unit/test_restart_trustworthy.py` — all 32 tests, especially
   `test_this_very_process_reads_as_a_live_supervisor` (`:131`) and the two `launcher.start` refusal
   tests (`:210`, `:227`).
4. `docs/findings/finding-0186.md` — the owner ruling D2 implements (*on ambiguity, refuse*). The fix
   must not weaken it.
5. `docs/findings/finding-0198.md` — why this `psutil` touch is quarantined here instead of in
   `core/typedshims/psutil.py`. That hand-off stays open; this plan does **not** move it.
6. `.github/workflows/ci.yml` — the `ratchet` job (`:36-50`), including the existing single deselect.

## 3. Investigation & grounding

- **Q1 — which disproof fires on Linux?** D2. The CI log records
  `RunRecord(started_at='2026-07-26T06:28:31', pid=2268)` and the pytest process was created ~06:27, so
  `created > opened + 5` is false and D1 cannot fire — `ops/lifecycle/launcher.py:213-217`.
- **Q2 — what does `name()` return on each platform?** macOS: `'Python'`, measured this session
  (`exe()` = `…/Python.app/Contents/MacOS/Python`). Linux runner: a value containing no `"python"` —
  inferred from the failure plus Q1's exclusion of D1. ⚑ **The code does not settle the exact Linux
  string, and this plan must not guess it** — Item 1's acceptance is that the *remote* run passes, which
  is the only authority on that value.
- **Q3 — is `exe()` safe for a foreign owner on macOS?** The existing docstring says yes:
  *"on macOS `cmdline()` raises AccessDenied for a foreign owner … while `name()`/`exe()` read fine"* —
  `ops/lifecycle/launcher.py:168-170`. This matters because the deployed daemon runs as a different
  principal post-migration.
- **Q4 — is the deployed daemon affected today?** No. Only user LaunchAgents are installed and the
  daemon runs as `ascalva` (no `/Library/LaunchDaemons/com.mind-palace.*`), and macOS returns
  `'Python'`, so D2 does not misfire in production. The exposure is that correctness rests on a platform
  accident, not that the guard is currently broken here.
- **Q5 — does `_process_identity` need a new failure mode?** No. It already returns `None` per
  component and never raises (`:158-173`); `exe()` gets the same try/except treatment as `name()`, and
  an unreadable `exe()` degrades to the existing ambiguity path.

**Additional risks surfaced during reading:** (a) the three failures are one root cause, so a fix that
greens one and not the other two means the diagnosis was wrong — treat that as the falsifier, not as
two bugs; (b) `_CLOCK_SLACK_S`/D1 carries a **separate latent timezone question** — `.replace(tzinfo=UTC)`
reinterprets `started_at`, and whether that is correct depends on how `runs.py` writes it. That is
**out of scope here** (§9) and parked in §11 rather than fixed opportunistically.

## 4. Reconciliation

- `ops/lifecycle/launcher.py:196-200` — the D2 docstring: *"**D2 — the process is not a Python
  interpreter.** The supervisor always is: the plist runs `uv run scripts/palace.py start` and the pid
  recorded is the python child's."* → **[banner: correction]**: the *premise* stands; the *probe* was
  wrong. Add a warrant line naming `finding-0211` and stating that `name()` reports an
  invocation-dependent basename (a console script on Linux) while `exe()` reports the executed
  interpreter, so the probe reads `exe()` first. Do not delete the existing reasoning — it explains why
  `cmdline()` is still rejected.
- `ops/lifecycle/launcher.py:167-172` — the `name()`-over-`cmdline()` comment → **[cross-ref:
  extension]**: keep it verbatim and extend it to say `exe()` is preferred over both, with `name()`
  retained as the fallback when `exe()` is unreadable.

## 5. Write scope

Two files. `ops/lifecycle/launcher.py` — only `_process_identity` and `_supervisor_alive` (plus their
docstrings); nothing else in that 1300-line module is touched, and in particular `reset_targets()`,
`status()`, and the launchd paths are out of bounds. `tests/unit/test_restart_trustworthy.py` — the
host-coupled test keeps existing and gains a sibling that pins the console-script shape via the
injected probe.

Deliberately **out of scope**: `core/typedshims/psutil.py` (finding-0198's hand-off stays open — moving
the shim is a separate plan and a trust-boundary change, which must not ride a bug fix);
`.github/workflows/ci.yml` (adding a deselect would hide this, not fix it); `core/stores/runs.py` and
anything touching `started_at`'s format (§11); every design note; the foundation denylist.

## 6. Interfaces pinned inline

Current, from `ops/lifecycle/launcher.py`:

```python
def _process_identity(pid: int) -> tuple[float | None, str | None]:
    ...
    name = str(proc.name())
    return (created, name)

def _supervisor_alive(run: RunRecord, *,
                      pid_alive: Callable[[int], bool] = _pid_alive,
                      identity: Callable[[int], tuple[float | None, str | None]]
                      = _process_identity) -> bool:
    if not pid_alive(run.pid):
        return False
    created, name = identity(run.pid)
    if created is not None:
        try:
            opened = datetime.fromisoformat(run.started_at).replace(tzinfo=UTC).timestamp()
        except ValueError:
            opened = None
        if opened is not None and created > opened + _CLOCK_SLACK_S:
            return False                       # D1
    if name is not None and "python" not in name.lower():
        return False                           # D2
    return True
```

⚑ **The two-tuple shape and the injected-probe signature are load-bearing** — the docstring at `:206-209`
explains that injection is what lets tests pin shapes the host cannot have, and `snapshot.run_state`
follows the same discipline. Prefer resolving `exe()` **inside** `_process_identity` and keeping the
returned tuple's meaning as "an interpreter-identifying string", so `_supervisor_alive` stays pure and
every existing injected-probe test keeps compiling. Widening the tuple to three elements is permitted
only if every call site and test is updated in the same item.

## 7. Items

### Item 1 — D2 probes the executed interpreter, not the invocation name

- **Objective:** `_process_identity` reports an interpreter-identifying string derived from `exe()`,
  falling back to `name()` when `exe()` is unreadable; `_supervisor_alive`'s D2 test is unchanged in
  meaning.
- **Files:** `ops/lifecycle/launcher.py`
- **Acceptance test:** `uv run pytest tests/unit/test_restart_trustworthy.py -q` → 32+ passed locally,
  **and** the pushed HEAD's authoritative `ratchet` job succeeds:
  `gh run list --workflow=ci --limit 1` reports `success`. ⚑ The remote run is the acceptance; a local
  pass is exactly what hid this bug for 55 runs.
- **Falsifier:** the remote run still fails, or fails on only one or two of the three tests. Either
  means D2 was not the firing branch and finding-0211's narrowing was wrong — **stop and re-diagnose
  from the runner's own values**, do not add a second fix on top.
- **Invariant(s) it must not violate:** finding-0186's ruling — ambiguity still REFUSES (an unreadable
  `exe()` **and** an unreadable `name()` must yield "not disproven ⇒ alive ⇒ start refuses", never a
  permissive shortcut); D1 unchanged; `_process_identity` still never raises; the probes stay injected.
- **Touches stored data?** No.
- **Parallelizable?** No.  **Depends on:** none.

### Item 2 — pin the regression with an injected console-script shape

- **Objective:** a test that fails on the *pre-change* code and passes after, without depending on the
  host's process naming — so this can never regress silently on any platform.
- **Files:** `tests/unit/test_restart_trustworthy.py`
- **Acceptance test:** a new test injects an `identity` returning a console-script-shaped name (the
  Linux shape) with a `created` that predates the row, and asserts `_supervisor_alive(...) is True`.
  Run it against the pre-change function first to show RED (the falsifier-demo discipline), then green.
  ⚑ Before that demo run, enumerate the pre-change module's live side-effecting functions and mock or
  skip them (the oq-0017 rule) — `launcher.start` writes rows and acquires the supervisor lock, so use
  `_supervisor_alive` directly rather than driving `start`.
- **Falsifier:** the new test passes against the pre-change code — meaning it does not actually pin the
  shape that broke, and the regression can recur.
- **Invariant(s) it must not violate:** the existing host-coupled test
  `test_this_very_process_reads_as_a_live_supervisor` is **kept**, not deleted or skipped — it is the
  only thing that caught this, and deleting it would trade a real signal for a green board.
- **Touches stored data?** No.
- **Parallelizable?** No.  **Depends on:** Item 1.

## 8. Math carried explicitly

N/A — no mathematical object implemented.

## 9. Non-goals

- **Not** moving the `psutil` touch into `core/typedshims/psutil.py` — finding-0198's hand-off stays
  open; a trust-boundary move must not ride a bug fix (the standing rule: keep a mechanical move and a
  boundary change in separate plans).
- **Not** touching D1, `_CLOCK_SLACK_S`, or `started_at`'s timezone handling (§11).
- **Not** adding a CI deselect, marking a test `xfail`, or skipping on `sys.platform` — each would
  restore a green board while leaving the guard's correctness resting on a platform accident.
- **Not** fixing finding-0212 (the seal-attests-the-local-gate duty gap). Orchestrator-routed, no code.
- **Not** re-running or re-sealing bp-105.

## 10. Stop-and-raise conditions

- The remote run still fails after Item 1 → the diagnosis is wrong. **Stop**, file a finding with the
  runner's actual values, do not stack a second guess.
- The fix cannot preserve finding-0186's refuse-on-ambiguity default → **stop**; that is an owner-level
  question (a ruling would be being reinterpreted), park the item and continue.
- A green local gate against a red remote at seal time → record it explicitly in the journal's
  Follow-through rather than omitting it; that is finding-0212's live re-entry.
- Any temptation to widen `write_scope` → file a finding instead of routing around scope-guard.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| D1's `.replace(tzinfo=UTC)` on `started_at` | Leave unchanged — it is accidentally correct on a UTC runner and D1 is provably not the firing branch here | Fix it in this plan (an unverified second change in a fail-closed guard, on a bug we have not observed); delete D1 (loses the pid-recycle disproof) | A D1 misfire is observed, or `runs.py`'s `started_at` convention is confirmed local-naive — then a scoped plan owning `core/stores/runs.py` |
| Where the `psutil` probe lives | Stays quarantined in `launcher.py` per finding-0198 | Move to `core/typedshims/psutil.py` now (out of write_scope, and a boundary change riding a fix) | finding-0198's own plan |
| Whether CI should also run a macOS matrix leg | No — out of scope, and cost unknown | Add one now (would have caught the divergence, but doubles runner cost and is a CI-content change) | A second platform-divergent failure, or an owner ruling |

## 12. Dependency & ordering summary

Two items, strictly sequential: Item 1 (the fix) → Item 2 (the pin). Nothing else depends on this plan,
and it depends on nothing — but it **unblocks the deploy gate**, which needs an attestable green HEAD,
which in turn gates the owner-owed code-ingest deploy. Blast radius is minimal and in phase order:
Item 1 changes a read-only probe; Item 2 adds a test. No stored data, no external effects, no migration.
