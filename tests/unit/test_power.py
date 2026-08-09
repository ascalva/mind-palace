"""The power sensor (`scheduler/power.py`; `dn-supervision-and-liveness` Amendment A1, bp-154
Item 1) — the scheduler's second resource axis, in the `Presence` mould.

⚑ **The single most important test in this file is `test_an_unreadable_battery_is_treated_as_
discharging`**, and its sibling for a probe that raises. Amendment A1.7's named falsifier is *"the
sensor fails open"*: if an unreadable or absent `pmset` yielded "not discharging" and work
dispatched, the design would be inverted — it would fail exactly when the machine is least healthy.
`test_the_fail_closed_default_is_what_makes_that_true` executes the inversion rather than trusting
prose, so the default is proven load-bearing instead of merely present.

Every test here injects its probe. No `pmset` subprocess runs in this file, and the real probe is
proven not to run at import or at construction (`test_constructing_the_sensor_runs_no_subprocess`).
"""

from __future__ import annotations

import subprocess

import pytest

from scheduler import power as power_mod
from scheduler.power import (
    DEFAULT_FLOOR_PERCENT,
    Power,
    PowerState,
    macos_power_state,
    parse_pmset,
)

# Captured verbatim from the live machine on 2026-08-05 (`pmset -g batt`, on mains, 100%).
AC_OUTPUT = (
    "Now drawing from 'AC Power'\n"
    " -InternalBattery-0 (id=23068771)\t100%; charged; 0:00 remaining present: true\n"
)
# The discharging shape, as the Jul 28 sampler logged it on the way from 100% to 8% in 2h40m.
BATTERY_OUTPUT = (
    "Now drawing from 'Battery Power'\n"
    " -InternalBattery-0 (id=23068771)\t8%; discharging; 0:21 remaining present: true\n"
)


def _probe(state: PowerState | None) -> tuple[power_mod.PowerProbe, list[int]]:
    """A probe returning `state`, plus the call log that makes a claim about it non-vacuous: a test
    asserting the fail-closed answer must also show the probe was actually consulted, or it would
    pass just as happily against a sensor that never looked."""
    calls: list[int] = []

    def probe() -> PowerState | None:
        calls.append(1)
        return state

    return probe, calls


# --- the readings ------------------------------------------------------------------------------


def test_a_discharging_probe_reports_discharging_with_its_percentage():
    probe, calls = _probe(PowerState(discharging=True, percent=55.0))
    sensor = Power(power_probe=probe)
    assert sensor.discharging() is True
    assert sensor.state() == PowerState(discharging=True, percent=55.0)
    # Non-vacuity: 55% is deliberately well ABOVE the floor, so this reading exercises the
    # discharging rule and nothing else — the floor must stay quiet here.
    assert 55.0 > DEFAULT_FLOOR_PERCENT and sensor.below_floor() is False
    assert calls, "the sensor answered without consulting its probe"


def test_an_ac_probe_reports_not_discharging():
    probe, calls = _probe(PowerState(discharging=False, percent=100.0))
    sensor = Power(power_probe=probe)
    assert sensor.discharging() is False
    assert calls


# --- ⚑ fail closed — the plan's most important case ---------------------------------------------


def test_an_unreadable_battery_is_treated_as_discharging():
    """⚑ Item 1's falsifier. `None` is an ORDINARY state (no `pmset`, a failed exec, unparseable
    output), and it must yield the RESTRICTIVE answer."""
    probe, calls = _probe(None)
    sensor = Power(power_probe=probe)
    # Precondition: the default under test is the fail-closed one, not something a fixture set.
    assert sensor.assume_discharging_when_unknown is True
    assert sensor.state() is None
    assert sensor.discharging() is True
    assert calls, "the sensor answered without consulting its probe"


def test_a_probe_that_raises_is_treated_as_discharging_and_does_not_propagate():
    """An exception escaping into `tick` would be a new crash path in the scheduler, not a guard.
    Every probe failure is the same fact — unreadable — so it lands on the same answer."""
    raised: list[str] = []

    def exploding_probe() -> PowerState | None:
        raised.append("boom")
        raise OSError("pmset went away mid-read")

    sensor = Power(power_probe=exploding_probe)
    assert sensor.state() is None                  # swallowed, not propagated
    assert sensor.discharging() is True            # and it lands on the restrictive answer
    assert sensor.below_floor() is False           # unknown percent does not halt (see below)
    assert raised, "the probe never ran — this test would pass against a sensor that never looks"


def test_the_fail_closed_default_is_what_makes_that_true():
    """The inversion, executed. Flipping the one field turns the unreadable case into "fine" —
    which is precisely A1.7's falsifier, and proves the default above is load-bearing rather than
    incidental."""
    probe, _ = _probe(None)
    assert Power(power_probe=probe, assume_discharging_when_unknown=False).discharging() is False


# --- the floor ---------------------------------------------------------------------------------


def test_the_floor_is_reached_only_while_discharging():
    """"Hold for AC" has no content on AC: a machine that is charging is recovering, at any
    percentage. The pair is asserted at the SAME percentage, so `discharging` is provably the only
    difference between the two answers."""
    low = 5.0
    assert low < DEFAULT_FLOOR_PERCENT
    on_battery, _ = _probe(PowerState(discharging=True, percent=low))
    on_mains, _ = _probe(PowerState(discharging=False, percent=low))
    assert Power(power_probe=on_battery).below_floor() is True
    assert Power(power_probe=on_mains).below_floor() is False


@pytest.mark.parametrize(
    ("percent", "expected"),
    [(19.9, True), (20.0, True), (20.1, False), (95.0, False)],
)
def test_the_floor_boundary_is_inclusive(percent: float, expected: bool):
    """`<=`, not `<`: reaching the floor counts as reaching it, because the margin exists to close
    down cleanly and spending it is not one of the options. The 20.0 row is the boundary the
    comparison would silently move if it were rewritten as `<`."""
    assert DEFAULT_FLOOR_PERCENT == 20.0
    probe, _ = _probe(PowerState(discharging=True, percent=percent))
    assert Power(power_probe=probe).below_floor() is expected


def test_an_unknown_percentage_does_not_halt_by_default_but_the_knob_exists():
    """The one named asymmetry in the fail-closed posture. Unknown percent must not halt EVERY
    tier by default — a host with no battery to read (a desktop, CI, a non-macOS worker) would then
    dispatch nothing ever, and the guard against an outage would be an outage. The knob is
    asserted in both positions so the default is a decision, not an accident."""
    probe, _ = _probe(PowerState(discharging=True, percent=None))
    assert Power(power_probe=probe).halt_when_percent_unknown is False
    assert Power(power_probe=probe).below_floor() is False
    assert Power(power_probe=probe, halt_when_percent_unknown=True).below_floor() is True
    # And the same for a wholly unreadable battery: discharging (fail closed), but not halted.
    blind, _ = _probe(None)
    assert Power(power_probe=blind).discharging() is True
    assert Power(power_probe=blind).below_floor() is False
    assert Power(power_probe=blind, halt_when_percent_unknown=True).below_floor() is True


# --- the real probe: parsing, and the guards that funnel into `None` -----------------------------


def test_parse_reads_the_two_real_pmset_shapes():
    ac = parse_pmset(AC_OUTPUT)
    battery = parse_pmset(BATTERY_OUTPUT)
    assert ac == PowerState(discharging=False, percent=100.0)
    assert battery == PowerState(discharging=True, percent=8.0)
    # Non-vacuity: the fixtures are the real formats, so a parser that only handled one of them —
    # or that keyed off the status word alone ("charged" vs "discharging") — fails here.
    assert "AC Power" in AC_OUTPUT and "Battery Power" in BATTERY_OUTPUT


def test_the_source_line_outranks_the_status_word():
    """`Now drawing from` answers the source question directly; the per-battery status word is a
    vocabulary that grows with the OS (`charged`, `charging`, `finishing charge`, `AC attached`).
    A machine plugged in at 30% reads `charging` — and a parser keyed off the word list would have
    to know every member. The word is a fallback for output missing the source line, not an
    override of it."""
    charging = (
        "Now drawing from 'AC Power'\n"
        " -InternalBattery-0 (id=23068771)\t30%; charging; 1:12 remaining present: true\n"
    )
    assert parse_pmset(charging) == PowerState(discharging=False, percent=30.0)
    # The fallback path: no source line at all, but the word is there.
    assert parse_pmset(" -InternalBattery-0\t8%; discharging; 0:21 remaining") == PowerState(
        discharging=True, percent=8.0
    )


def test_a_host_on_mains_with_no_battery_reports_a_state_with_no_percentage():
    """A desktop answers the source question while having no battery to report. The two facts are
    separable, so they are separate fields — and `percent=None` must not be read as 0%."""
    assert parse_pmset("Now drawing from 'AC Power'\n") == PowerState(
        discharging=False, percent=None
    )


@pytest.mark.parametrize("text", ["", "\n\n", "some other tool's output entirely"])
def test_unreadable_output_parses_to_None(text: str):
    """The third path to `None`, and the reason the fail-closed default is load-bearing: an
    unrecognized format degrades to "discharging", never to "fine"."""
    assert parse_pmset(text) is None
    assert Power(power_probe=lambda: parse_pmset(text)).discharging() is True


def test_an_absent_pmset_yields_None_rather_than_an_exception(monkeypatch):
    """The `shutil.which` guard, carried from `presence.macos_idle_seconds`: an absent tool is a
    `None`, not a crash — which is what a non-macOS worker sees."""
    monkeypatch.setattr(power_mod.shutil, "which", lambda _name: None)
    assert macos_power_state() is None


@pytest.mark.parametrize("boom", [OSError("no such tool"), subprocess.TimeoutExpired("pmset", 5)])
def test_a_failed_or_hung_exec_yields_None_rather_than_an_exception(monkeypatch, boom):
    """The other two carried habits: the explicit `timeout=` (a hung probe must not stall dispatch
    — this runs on the supervisor's own thread inside `tick`) and the
    `(OSError, SubprocessError)` catch. Both funnel to `None`."""
    monkeypatch.setattr(power_mod.shutil, "which", lambda _name: "/usr/bin/pmset")

    def explode(*_a, **_kw):
        raise boom

    monkeypatch.setattr(power_mod.subprocess, "run", explode)
    assert macos_power_state() is None


def test_the_probe_passes_an_explicit_timeout(monkeypatch):
    """The timeout is asserted, not assumed: a probe without one can hang the supervisor's tick
    forever, and nothing else in the suite would notice its removal."""
    seen: dict[str, object] = {}

    def fake_run(argv, **kwargs):
        seen["argv"] = argv
        seen["timeout"] = kwargs.get("timeout")
        return subprocess.CompletedProcess(argv, 0, stdout=AC_OUTPUT, stderr="")

    monkeypatch.setattr(power_mod.shutil, "which", lambda _name: "/usr/bin/pmset")
    monkeypatch.setattr(power_mod.subprocess, "run", fake_run)
    assert macos_power_state() == PowerState(discharging=False, percent=100.0)
    assert seen["argv"] == ["pmset", "-g", "batt"]
    assert seen["timeout"] == 5


def test_constructing_the_sensor_runs_no_subprocess(monkeypatch):
    """Item 1's invariant: the real probe must not be invoked at import time or by construction.
    The call counter is checked in BOTH directions — zero after construction, and one after a
    reading — so the test cannot pass against a probe that is simply dead."""
    calls: list[list[str]] = []

    def fake_run(argv, **_kwargs):
        calls.append(argv)
        return subprocess.CompletedProcess(argv, 0, stdout=AC_OUTPUT, stderr="")

    monkeypatch.setattr(power_mod.shutil, "which", lambda _name: "/usr/bin/pmset")
    monkeypatch.setattr(power_mod.subprocess, "run", fake_run)

    sensor = Power()
    assert sensor.power_probe is macos_power_state    # the default binding, not an injected double
    assert calls == []                                # construction consults nothing

    assert sensor.discharging() is False              # ... but a READING does
    assert calls == [["pmset", "-g", "batt"]]
