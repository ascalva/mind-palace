"""Injected power sensors for the scheduler tests (`dn-supervision-and-liveness` Amendment A1).

`Supervisor.power` defaults to a sensor that FAILS CLOSED: a host that cannot read `pmset` — CI,
any non-macOS worker — reads as discharging, and a host that can read it reports whatever the
developer's battery happens to be doing right now. Either way a default-constructed supervisor in a
test would decide heavy-tier dispatch from the machine the suite runs on. So every test that
constructs a real `Supervisor` injects one of these instead, exactly as it already injects
`Presence(idle_probe=...)` rather than reading the host's real HID idle time.

⚑ One rule about which one to inject. `on_ac()` restores the intended subject of a test that was
never about power (the foreground gate, the ceiling, the dispatch seam). Injecting it into a test
that is *meant* to exercise a power refusal would hide the feature rather than accommodate it —
bp-154 Item 5's named falsifier.
"""

from __future__ import annotations

from scheduler.power import Power, PowerState


def on_ac(percent: float = 100.0) -> Power:
    """Plugged in — the power axis refuses nothing."""
    return Power(power_probe=lambda: PowerState(discharging=False, percent=percent))


def on_battery(percent: float = 55.0) -> Power:
    """Running on the battery. The default is deliberately well above the floor, so a test using it
    exercises the discharging shed and NOT the floor; pass a low percentage to reach the floor."""
    return Power(power_probe=lambda: PowerState(discharging=True, percent=percent))


def unreadable() -> Power:
    """A battery that cannot be read at all (no `pmset`, a failed exec, unparseable output). The
    fail-closed default makes this discharging."""
    return Power(power_probe=lambda: None)
