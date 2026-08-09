"""Power-state detection — the scheduler's SECOND resource axis (`dn-supervision-and-liveness`
Amendment A1; issue #12).

§2.7 gave the supervisor exactly one resource to refuse on: **memory** (non-negotiable #8, "the
scheduler refuses breaching work"). That principle was never memory-specific — it was simply never
given a second axis. The machine's remaining energy is a schedulable resource too, and work that
would spend the last of it is breaching work. Three measured emergencies are the warrant: Jul 24
(drained to 1% during a deploy night — the embedder starved under critical-battery throttle,
`code_sync` wedged, and the daemon died unwitnessed and stayed dead three days), Jul 28 (100%->8%
in 2h40m, caught at the wire), and Aug 1 (fatal — the machine died mid-run and run #39 came up in
recovery). The battery hardware is healthy throughout: Condition Normal, 95% maximum capacity, 128
cycles, re-measured 2026-08-05. **The drain is load, not degradation** — the scheduler was the
defect.

This module is deliberately shaped like `scheduler/presence.py` rather than invented: an injectable
probe (so the gate is testable with no hardware, and a non-macOS worker can supply its own), a
threshold, and — the idiom that matters — a fail-CLOSED default. `Presence` reads
`assume_present_when_unknown = True`; this reads `assume_discharging_when_unknown = True`.

⚑ **Fail closed, and why that is the load-bearing line.** `None` is an ORDINARY state here, not a
theoretical one: `pmset` may be absent (`shutil.which`), the exec may fail or hang (hence an
explicit `timeout=`), and the output may be unreadable — all three funnel into `None`, and so does
a probe that raises. The failure mode being designed against is *the machine dying*; a sensor that
failed OPEN would re-create it precisely when the system is least healthy. So an unreadable battery
is treated as discharging.

What this module does NOT decide, deliberately: **which** tiers are shed (that is
`supervisor.HEAVY_TIERS` — read, never reshaped, so there is one shed vocabulary and not two) and
**whether** a job is refused (that is `Supervisor.power_blocked_tiers`, one of three sibling
predicates). One sensor feeding one predicate is A1.5's constraint, carried from this note's §1.2
non-goal: N ad-hoc detectors, each with its own falsifier and its own rot, is the failure mode the
note exists to avoid.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from collections.abc import Callable
from dataclasses import dataclass

# The charge at which the answer stops being "shed the heavy lanes" and becomes "start nothing at
# all" (Amendment A1.2, ~20%). A lower floor buys runway and was rejected: the margin exists to
# close cleanly, and Jul 28 fell 100%->8% in 2h40m, so the tail is fast.
DEFAULT_FLOOR_PERCENT = 20.0


@dataclass(frozen=True)
class PowerState:
    """One sampled reading of the physical world. `percent` is optional because a host can answer
    the source question ("am I on mains?") while having no battery to report at all — a desktop, a
    machine with the battery removed. The two facts are separable, so they are separate fields."""

    discharging: bool
    percent: float | None = None


PowerProbe = Callable[[], "PowerState | None"]

_SOURCE_PREFIX = "now drawing from"
_AC = "'ac power'"
_BATTERY = "'battery power'"
_PERCENT = re.compile(r"(\d{1,3}(?:\.\d+)?)%")


def parse_pmset(text: str) -> PowerState | None:
    """Read `pmset -g batt` output. `None` when it cannot be read — which the caller turns into the
    restrictive answer, so an unrecognized format degrades to "discharging" rather than to "fine".

    The two shapes this parses, both real (the first captured verbatim from the live machine on
    2026-08-05, the second is the discharging form the Jul 28 sampler logged)::

        Now drawing from 'AC Power'
         -InternalBattery-0 (id=23068771)\t100%; charged; 0:00 remaining present: true

        Now drawing from 'Battery Power'
         -InternalBattery-0 (id=23068771)\t8%; discharging; 0:21 remaining present: true

    The `Now drawing from` line is authoritative and is read first: it answers the source question
    directly, whereas the per-battery status word is a vocabulary (`charged`, `charging`,
    `discharging`, `finishing charge`, `AC attached`) that grows with the OS. The word is a
    FALLBACK for output that lacks the source line, never an override of it.
    """
    source: bool | None = None
    saw_discharging_word = False
    percent: float | None = None
    for raw in text.splitlines():
        line = raw.strip().lower()
        if source is None and line.startswith(_SOURCE_PREFIX):
            if _BATTERY in line:
                source = True
            elif _AC in line:
                source = False
        if "discharging" in line:
            saw_discharging_word = True
        if percent is None:
            found = _PERCENT.search(line)
            if found is not None:
                percent = float(found.group(1))
    if source is None and not saw_discharging_word:
        return None            # unreadable — the caller's fail-closed default takes over
    return PowerState(discharging=source if source is not None else True, percent=percent)


def macos_power_state() -> PowerState | None:
    """The machine's power state via `pmset -g batt`. `None` if unavailable (e.g. not macOS, the
    exec failed or hung, or the output was unreadable).

    Three habits are carried deliberately from `presence.macos_idle_seconds`, and each one is a
    path to `None` rather than to a crash or a stall: the `shutil.which` guard (an absent tool is
    not an exception), the explicit `timeout=` (a hung probe must not stall dispatch — this runs on
    the supervisor's own thread, inside `tick`), and the `(OSError, SubprocessError)` catch.
    """
    if shutil.which("pmset") is None:
        return None
    try:
        out = subprocess.run(
            ["pmset", "-g", "batt"], capture_output=True, text=True, timeout=5
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    return parse_pmset(out)


@dataclass
class Power:
    """The power sensor, in the `Presence` mould: an injectable probe, a floor, and a fail-closed
    default. Injectability is what makes the gate testable with no hardware — every test in
    `tests/unit/test_power.py` injects, so no `pmset` subprocess runs there, and the real probe is
    never invoked at import time or by construction (only by a call)."""

    power_probe: PowerProbe = macos_power_state
    floor_percent: float = DEFAULT_FLOOR_PERCENT
    # ⚑ THE FAIL-CLOSED DEFAULT — the module docstring's load-bearing line, and the amendment's
    # named falsifier (A1.7: "if an unreadable/absent `pmset` yields 'not discharging' and work
    # dispatches, the design is inverted"). Exposed as a field, like `Presence`'s, so the inversion
    # is *executable* in a test rather than merely asserted in prose.
    assume_discharging_when_unknown: bool = True
    # ⚑ The ONE asymmetry in that posture, named rather than accidental. An unreadable battery is
    # treated as DISCHARGING above, and the cost of that is bounded: the heavy lanes are shed,
    # which is the "safe but useless" degradation the plan's §10 already accepts. An unreadable
    # battery treated as BELOW THE FLOOR is a different animal — the floor refuses EVERY tier, so a
    # host with no battery to read (a desktop, CI, any non-macOS worker) would dispatch nothing,
    # ever, and the guard against an outage would BE an outage. So an unknown percentage does not
    # halt by default; the knob exists, defaulted off, so the decision is visible and reversible.
    halt_when_percent_unknown: bool = False

    def state(self) -> PowerState | None:
        """The current reading, or `None` when the battery is unreadable. **Never raises**: a probe
        that throws is a `None`, because an exception escaping into `tick` would be a new crash
        path in the scheduler — a guard that can take down the loop it protects is not a guard."""
        try:
            return self.power_probe()
        except Exception:   # noqa: BLE001 — every probe failure is the same fact: unreadable
            return None

    def discharging(self) -> bool:
        """True if the machine is running on its battery (so the heavy lanes are shed). An
        unreadable battery returns the restrictive answer — see `assume_discharging_when_unknown`.
        """
        state = self.state()
        if state is None:
            return self.assume_discharging_when_unknown
        return state.discharging

    def below_floor(self) -> bool:
        """True when the remaining charge has reached the floor WHILE discharging — the point at
        which the supervisor starts nothing at all.

        Two boundaries stated exactly. **On AC is never below the floor**, at any percentage: the
        floor's whole content is "hold for AC", so a machine that is already charging is recovering
        and there is nothing to hold for. And the comparison is `<=`, not `<` — reaching the floor
        counts as reaching it, because the margin exists to close down cleanly and spending it is
        not one of the options.
        """
        state = self.state()
        if state is None:
            return self.assume_discharging_when_unknown and self.halt_when_percent_unknown
        if not state.discharging:
            return False
        if state.percent is None:
            return self.halt_when_percent_unknown
        return state.percent <= self.floor_percent
