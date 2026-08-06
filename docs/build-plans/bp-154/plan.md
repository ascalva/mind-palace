---
type: build-plan
id: bp-154
track: ops
status: proposed
design_ref:
  - docs/design-notes/dn-supervision-and-liveness.md
contract: builder
write_scope:
  - scheduler/power.py
  - scheduler/supervisor.py
  - tests/unit/test_power.py
  - tests/integration/test_supervisor.py
  - tests/integration/test_queue.py
  - tests/e2e/test_scheduler_live.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 200k
  actual: null
depends_on: []
parallelizable_with: [bp-151, bp-152, bp-153]
created: 2026-08-05
updated: 2026-08-05
links:
  - docs/findings/finding-0279.md
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — the power axis: the scheduler refuses work it cannot power

## 0. Mode & provenance

Graduated from `dn-supervision-and-liveness` **Amendment A1** (the power axis) on 2026-08-05, at
the owner's direction. The amendment is agent-drafted and lands by the owner's merge in the same
PR as this plan — so **this plan's `design_ref` becomes ratified by the same merge that readies
the plan.** Investigation and planning produced this plan; implementation proceeds item-by-item.
All `path:line` citations were re-opened against HEAD `174d06c`.

Warrant chain: issue #12 (`type:direction`, `route:orchestrator`), migrated from frozen
`finding-0279`. **Three** measured emergencies — Jul 24 (fatal, daemon dead three days), Jul 28
(caught at the wire), Aug 1 (fatal, machine died mid-run).

## 1. Objective

Give the supervisor a power axis: refuse to dispatch energy-hungry work while discharging, and
close the ledger clean before the battery dies.

## 2. Context manifest

Read in order:

1. `docs/design-notes/dn-supervision-and-liveness.md` — **Amendment A1 in full** (this plan),
   then §0's enforcement ladder, §1.2 non-goals, and §2.7 (the memory ceiling — the axis this
   one is modelled on).
2. `scheduler/supervisor.py` — whole file. `HEAVY_TIERS` (`:59`), `blocked_tiers()` (`:130-135`),
   `model_blocked_tiers()` (`:137-147`), and the claim site (`:177`) are the entire surface.
3. `scheduler/presence.py` — whole file (~60 lines). This is the **template**; the power sensor
   mirrors it, including the fail-closed default.
4. `docs/findings/finding-0279.md` — the frozen evidence: the three drains, the sampler traces.

## 3. Investigation & grounding

- **Q1 — Does a shed mechanism already exist, or is this new machinery?** It exists.
  `HEAVY_TIERS = frozenset({"synthesis", "stretch"})` (`scheduler/supervisor.py:59`) is shed by
  `blocked_tiers()` when `presence.foreground_active()` (`:130-135`). This plan adds a
  **predicate**, not machinery.
- **Q2 — Where is the ONE enforcement point?** `supervisor.py:177` —
  `blocked_tiers=self.blocked_tiers() | self.model_blocked_tiers()`, passed to `claim`. The code
  pins it at `:153`: *"Enforced at the ONE claim site, via `claim`'s existing `blocked_tiers` —
  no new queue"*. The power predicate joins that union and **nothing else changes**.
- **Q3 — May the power rule live inside `blocked_tiers()`?** **No — this is the plan's one hard
  constraint.** `:131-134` states the foreground gate is *"THE FOREGROUND GATE, and nothing
  else"*, deliberately not extended with the single-model rule, citing bp-110 §7 Item 4's
  invariant (*"the foreground gate keeps its meaning and is not overloaded"*) because *"two
  different reasons to refuse a tier, conflated into one predicate, is how a reader later cannot
  tell which rule refused a job."* `model_blocked_tiers()` (`:137`) is the precedent for a
  second, separate predicate. The power axis is a third.
- **Q4 — What shape does the sensor take?** `scheduler/presence.py:46-59` is a frozen-ish
  dataclass with an **injectable probe** (`idle_probe: IdleProbe = macos_idle_seconds`), a
  threshold (`threshold_s`), and a fail-closed default: `assume_present_when_unknown: bool = True`
  — when `idle_probe()` returns `None`, `foreground_active()` returns the restrictive answer
  (`:56-59`). The power sensor mirrors this exactly; injectability is what makes the gate
  testable with no hardware.
- **Q5 — Is preflight a valid home?** No. `preflight` lives in `scripts/palace.py` — the CLI's
  process — and open issue #19 is the standing proof that this misreports: `status` claims
  `sandbox: present` while every live run booted with it off, *because preflight runs in the
  caller's environment, not the daemon's*. Confirmed live this session: `palace status` reported
  `sandbox: podman present` from my shell, which says nothing about the daemon. A1.3 amends the
  issue's own direction text on this point.
- **Q6 — Is the battery hardware actually healthy (i.e. is this really a scheduling defect)?**
  Yes, re-measured 2026-08-05: Condition **Normal**, Maximum Capacity **95%**, Cycle Count **128**
  (up 4 from the 124 in the frozen finding). The drain is load, not degradation.
- **Q7 — Does the sampler still exist to promote?** **No.** `/tmp/mind-palace-battery-watch.sh` is
  gone — `/tmp` was cleared by the Aug 1 reboot. The builder is writing a sensor from the
  `Presence` template, not porting a script. (This is A1.5's argument, verified.)

**Additional risks or questions surfaced during reading:**

- **The honest limit is real and must not be papered over.** A dispatch-time refusal cannot stop
  an already-running job from draining the battery — Jul 24's `code_backfill` was in flight when
  the throttle hit. This plan bounds what is *started*. If the builder finds itself reaching for
  job cancellation, that is finding-0178's machinery and out of scope (§9).
- **`tests/integrity/test_shadow_isolation.py:96-107` imports `HEAVY_TIERS` and asserts
  `shadow_job.tier in HEAVY_TIERS`.** This plan does not modify `HEAVY_TIERS`, so that test should
  stay green — but it is the tripwire to watch if the builder is tempted to reshape the tier set
  instead of adding a predicate. It is deliberately **not** in write_scope: if it reddens, the
  approach is wrong (§10).
- **"Embedder-bound lanes" needs a mechanical definition.** A1 says shed them; the code has
  `HEAVY_TIERS` (tiers) and `load_key` (models). The builder must pin which is the selector and
  say so — the code does not settle it, and guessing would produce a rule nobody can read. See
  §11 (parked, with a recorded default).

## 4. Reconciliation

- `scheduler/supervisor.py:130-135` — `blocked_tiers()`'s docstring says *"THE FOREGROUND GATE,
  and nothing else"* → **[cross-ref: extension]**, not a correction. The statement stays exactly
  true; a sibling predicate is precisely what it prescribes. Add a one-line pointer noting the
  power axis is a third predicate (A1.1), so a reader finds all three from any one of them.
- `scheduler/supervisor.py:177` — the union → **[cross-ref: extension]**: one more term.
- `docs/design-notes/dn-supervision-and-liveness.md` — extended by **Amendment A1**, which lands
  in this same PR. Deliberately **not** in this plan's `write_scope`: the amendment is the design
  and travels as its own commit; a builder does not edit the note it graduates from.
- Issue #12's direction text (*"health/preflight reads `pmset -g batt`"*) → **[banner:
  correction]**, carried in A1.3 and to be recorded as a comment on the issue when this lands:
  preflight may *display* power state, never enforce it (§3 Q5).

## 5. Write scope

- `scheduler/power.py` — **new**. The sensor, mirroring `presence.py`.
- `scheduler/supervisor.py` — the `power_blocked_tiers()` predicate and the union at `:177`.

Test files carried:

- `tests/unit/test_power.py` — **new**; the sensor's own tests including the fail-closed path.
- `tests/integration/test_supervisor.py`, `tests/integration/test_queue.py`,
  `tests/e2e/test_scheduler_live.py` — all three exercise dispatch/`blocked_tiers` and may observe
  a supervisor constructed without a power sensor; carried so a default-construction change can be
  repaired in-session.

Deliberately **out of scope**: `docs/design-notes/**` (the amendment is its own commit),
`scripts/palace.py` (preflight may display power state later — **not this plan**, per A1.3's
"never the thing that enforces it"), `scheduler/presence.py` (the template is read, never edited —
the foreground gate keeps its meaning), `tests/integrity/test_shadow_isolation.py` (the tripwire —
see §10), and the fixed points (`CONSTITUTION.md`, `eval/golden/**`, `eval/golden.py`).

## 6. Interfaces pinned inline

**The template — `scheduler/presence.py:46-59`, current form, copied verbatim:**

```python
class Presence:
    idle_probe: IdleProbe = macos_idle_seconds
    threshold_s: float = DEFAULT_IDLE_THRESHOLD_S
    assume_present_when_unknown: bool = True

    def idle_seconds(self) -> float | None:
        return self.idle_probe()

    def foreground_active(self) -> bool:
        """True if the owner is actively using the machine (so heavy tiers are gated)."""
        idle = self.idle_probe()
        if idle is None:
            return self.assume_present_when_unknown
        return idle < self.threshold_s
```

**The probe precedent — `scheduler/presence.py:24-33`, current form.** The `pmset` probe mirrors
this shape exactly; note that `subprocess` is already established in `scheduler/`, so there is no
import-firewall question to resolve:

```python
import shutil
import subprocess

def macos_idle_seconds() -> float | None:
    """Seconds since the last HID (keyboard/mouse) event, via `ioreg`. None if unavailable
    ...
    if shutil.which("ioreg") is None:
        return None
    try:
        out = subprocess.run(
            ["ioreg", "-c", "IOHIDSystem"], capture_output=True, text=True, timeout=5
        )
    except (OSError, subprocess.SubprocessError):
        ...
```

Three things to carry over deliberately: the `shutil.which` guard (absent tool → `None`, never a
crash), the **explicit `timeout=`** (a hung probe must not stall dispatch), and the
`(OSError, subprocess.SubprocessError)` catch. All three funnel into `None` — which is exactly why
the fail-closed default is the load-bearing decision: `None` is a *reachable, ordinary* state here,
not a theoretical one.

**The gate whose meaning must NOT be overloaded — `supervisor.py:130-135`, verbatim:**

```python
    def blocked_tiers(self) -> frozenset[str]:
        """THE FOREGROUND GATE, and nothing else. Deliberately not extended with the
        single-model-in-flight rule (bp-110 §7 Item 4's invariant: "the foreground gate keeps its
        meaning and is not overloaded") — two different reasons to refuse a tier, conflated into
        one predicate, is how a reader later cannot tell which rule refused a job."""
        return HEAVY_TIERS if self.presence.foreground_active() else frozenset()
```

**The ONE claim site — `supervisor.py:177`, verbatim (the line this plan extends):**

```python
                               blocked_tiers=self.blocked_tiers() | self.model_blocked_tiers())
```

**The tier set — `supervisor.py:59`, verbatim (read, not modified):**

```python
HEAVY_TIERS = frozenset({"synthesis", "stretch"})
```

**The rule being implemented (A1.2), verbatim from the amendment:** on `discharging`, shed the
embedder-bound lanes. Below the floor (~20%), **close the ledger clean and hold for AC** — a clean
stop, never a death. `assume_discharging_when_unknown = True`: an unreadable battery is treated as
discharging, because the failure mode being designed against is the machine dying, and a sensor
that fails open re-creates it exactly when the system is least healthy.

**Enforcement tier (A1.4):** tier 5 (runtime check) with a **tier-4 test** — identical to what
§2.7 claims for the memory ceiling. Overclaiming is the ladder's named foot-gun.

## 7. Items

### Item 1 — the `Power` sensor

- **Objective:** `scheduler/power.py` reports power state from an injectable probe, fail-closed.
- **Files:** `scheduler/power.py`, `tests/unit/test_power.py`
- **Acceptance test:** with an injected probe, the sensor reports discharging/charging and
  percentage correctly; **with a probe returning `None` it reports discharging** (fail-closed);
  with a probe that raises, likewise — a sensor that propagates an exception into dispatch is a
  new crash path, not a guard.
- **Falsifier:** the `None` path yields "not discharging". That inverts the design — the guard
  would fail open exactly when the system is least healthy. This single case is the plan's most
  important test.
- **Invariant(s) it must not violate:** no `pmset` subprocess runs in the unit tests — the probe
  is injected, exactly as `presence.py` makes `idle_probe` injectable. The real probe must not
  be invoked at import time.
- **Touches stored data?** No.
- **Parallelizable?** No. **Depends on:** none.

### Item 2 — `power_blocked_tiers()`, its own predicate

- **Objective:** a third refusal predicate, beside the foreground and single-model gates.
- **Files:** `scheduler/supervisor.py`, `tests/integration/test_supervisor.py`
- **Acceptance test:** `power_blocked_tiers()` returns the shed set while discharging and
  `frozenset()` on AC; `blocked_tiers()` is **byte-identical to its current behavior** under
  every power state (a test asserts the foreground gate is unchanged).
- **Falsifier:** **the power rule appears inside `blocked_tiers()`.** That is the amendment's one
  load-bearing pin (A1.1/§3 Q3) — a conflated predicate means a reader can no longer tell which
  rule refused a job. Also falsified if `HEAVY_TIERS` is mutated rather than read.
- **Invariant(s) it must not violate:** the foreground gate keeps its meaning (bp-110 §7 Item 4).
  Three predicates, three questions, separately readable.
- **Touches stored data?** No.
- **Parallelizable?** No. **Depends on:** Item 1.

### Item 3 — compose at the ONE claim site (the tier-4 test)

- **Objective:** the union at `:177` includes the power predicate, and a test proves it.
- **Files:** `scheduler/supervisor.py`, `tests/integration/test_supervisor.py`
- **Acceptance test:** with a discharging probe, a job in a shed tier is **not claimed**; on AC it
  **is** claimed. The tier-4 test asserts the union at the claim site actually contains the power
  term — not merely that the predicate exists in isolation (a predicate nobody calls is the
  finding-0187 shape: deleting bp-105's sweep call left 85/85 green).
- **Falsifier:** the predicate exists and is green in unit tests but is never composed into
  `claim` — the guard is decorative. Deleting the new term from `:177` must **redden** a test; if
  it does not, this item did not land.
- **Invariant(s) it must not violate:** no new queue machinery, no second enforcement point
  (`:153` — "Enforced at the ONE claim site"). The pinned tier stays never-blocked (`:149`).
- **Touches stored data?** No.
- **Parallelizable?** No. **Depends on:** Item 2.

### Item 4 — the floor: close the ledger clean and hold for AC

- **Objective:** below the floor, the daemon stops cleanly rather than dying.
- **Files:** `scheduler/power.py`, `scheduler/supervisor.py`,
  `tests/integration/test_supervisor.py`
- **Acceptance test:** with a probe below the floor, the supervisor closes the ledger cleanly and
  dispatches nothing further; a subsequent AC reading resumes dispatch. The test asserts the
  ledger is closed **clean** — i.e. a following start is not a recovery run.
- **Falsifier:** the stop leaves the ledger in the state a crash would (a stale `running` row) —
  then this reproduces the very condition it exists to prevent, and the Aug 1 recovery run was the
  demonstration. Also falsified if the hold spins hot: holding for AC must not itself consume the
  battery it is protecting.
- **Invariant(s) it must not violate:** **never kill an in-flight job** — this plan bounds what is
  *started* (A1.4's honest limit). Under launchd KeepAlive a stop is a restart, which is the
  intended shape: come back, see discharging, dispatch nothing.
- **Touches stored data?** **Yes** — the ledger close is a queue write. Verify against a fixture
  queue before any real run.
- **Parallelizable?** No. **Depends on:** Item 3.

### Item 5 — repair the carried dispatch-test surface

- **Objective:** the full local CI gate is green.
- **Files:** `tests/integration/test_supervisor.py`, `tests/integration/test_queue.py`,
  `tests/e2e/test_scheduler_live.py`
- **Acceptance test:** ruff + import-firewall + mypy at its current baseline + type_gate + the
  CI-tier pytest selection, green. Counts drift — trust the run.
- **Falsifier:** a test made green by injecting an always-on-AC probe into a case that was
  meant to exercise refusal — that hides the feature rather than accommodating it.
- **Invariant(s) it must not violate:** `tests/integrity/test_shadow_isolation.py` stays green
  **without being edited** (it is out of scope — see §10).
- **Touches stored data?** No.
- **Parallelizable?** No. **Depends on:** Items 1–4.

## 8. Math carried explicitly

N/A — no mathematical object is implemented. The floor is a threshold comparison and the shed set
is a set union; neither earns a field-guide entry, and inventing one would be the formalism this
repo's §8 exists to refuse.

## 9. Non-goals

Carried from Amendment A1.6, which is the binding list:

- **NOT in-flight energy bounding.** Dispatch-time refusal only. Killing or suspending a *running*
  job on power state is finding-0178's job-timeout machinery. If the builder reaches for it, stop
  (§10).
- **NOT thermal, CPU, or any third axis.** Power only.
- **NOT the embedder's residency or runtime** — `dn-local-model-runtime`'s boundary (§2.7) is
  untouched. This decides *whether an embedder-bound lane dispatches*, never where the embedder
  lives or what it costs.
- **NOT a config-driven policy engine.** One floor, one discharging rule, `Presence`-shaped.
- **NOT preflight enforcement** (A1.3). Display may come later, in another plan.
- **NOT a `HEAVY_TIERS` reshape.** Read it; do not redefine it.
- **NOT the deploy gate.** `palace deploy` is the owner's single in-loop act.

## 10. Stop-and-raise conditions

- **The power rule cannot be expressed as a separate predicate** — if it seems to require folding
  into `blocked_tiers()`, **stop**. That is the amendment's one hard pin; a spec defect, not a
  coding problem.
- **`tests/integrity/test_shadow_isolation.py` reddens.** It is deliberately out of write scope
  and asserts `shadow_job.tier in HEAVY_TIERS`. A red there means the tier set was reshaped
  instead of a predicate added — the wrong approach. Stop; do not edit the test to fit.
- **The floor logic requires cancelling a running job** — that is finding-0178's machinery and
  A1.4's recorded limit. File and stop.
- **`pmset` proves unreadable in the daemon's actual environment** (not the caller's — §3 Q5's
  whole point). If the daemon cannot read power state where it runs, the sensor's home is wrong
  and the design question reopens. Fail-closed means this degrades to "always discharging", which
  is *safe but useless* — raise it rather than shipping a permanently-shedding scheduler.
- The builder performs **no blessing, no status flip, no `deploy`**, and never writes the fixed
  points.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| The selector for "embedder-bound lanes" | **Default: `HEAVY_TIERS`** — the existing shed set, reused so there is one shed vocabulary, not two (§3's surfaced risk) | Select by `load_key` — rejected as the default because it introduces a second, finer vocabulary for shedding whose interaction with `HEAVY_TIERS` nobody has designed | Measurement shows a non-heavy lane is the real drain (then the selector is wrong, not the axis) |
| The floor value | ~20%, as A1 records | A lower floor buys runway — rejected: the margin exists to close cleanly, and Jul 28 fell 100%→8% in 2h40m, so the tail is fast | A fourth emergency at ≥20%, or gauges showing the floor is never approached (A1.7) |
| Preflight display of power state | Not built here (A1.3) | Build it now — rejected: display and enforcement in one plan invites the enforcement to drift into preflight, which #19 proves misreports | Someone wants power on the status line |
| Hold-for-AC mechanism | Stop cleanly; launchd KeepAlive restarts and re-evaluates | An in-process sleep/wait loop — rejected: it holds a supervisor lock while doing nothing and can itself drain | The restart cycle proves too coarse in practice |

## 12. Dependency & ordering summary

Strictly sequential: **1 → 2 → 3 → 4 → 5**, and the order is the blast-radius order.

- **Item 1** (sensor) is pure and stores nothing — a dataclass over an injected probe.
- **Item 2** (predicate) is read-only with respect to dispatch: it computes a set nobody consumes
  yet, so it cannot change behavior.
- **Item 3** (compose) is the first behavior change — a job that would have been claimed is not.
- **Item 4** (the floor) is the only item that **writes** (closing the ledger).
- **Item 5** repairs the surface the previous four moved.

Items 2 and 3 are deliberately separate even though both touch `supervisor.py`: Item 2 can land
and be reviewed as inert, and Item 3's whole content is *"and now it is actually consumed"* — which
is exactly the finding-0187 failure this plan must not repeat (a guard nobody calls).

**Cross-plan:** `parallelizable_with: [bp-151, bp-152, bp-153]` — disjoint write scopes
(`scheduler/**` vs `core/**` + `ops/**`) and a different track. Worth noting the coupling in the
other direction: **this plan protects bp-153's rebuild.** That rebuild is a long sliced job whose
own D7 slicing exists because the lane wedged once already — and the Jul 24 wedge was *caused* by
a battery drain. Landing bp-154 before bp-153 Item 3 runs is the cheap insurance.
