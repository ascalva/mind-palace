"""Foreground-presence detection (BUILD-SPEC §13 foreground check).

Heavy synthesis must not fire while the owner is actively using the machine. This reads the
OS HID idle time (deterministic, no model) and reports whether the owner is present. The
idle source is injectable so the scheduler is testable off-host and a non-macOS worker can
supply its own probe.

Fail safe: if idle time is unknown, assume the owner IS present — never run heavy batch work
on a blind guess.
"""

from __future__ import annotations

import shutil
import subprocess
from collections.abc import Callable
from dataclasses import dataclass

DEFAULT_IDLE_THRESHOLD_S = 300.0   # "present" if there was input within the last 5 minutes

IdleProbe = Callable[[], "float | None"]


def macos_idle_seconds() -> float | None:
    """Seconds since the last HID (keyboard/mouse) event, via `ioreg`. None if unavailable
    (e.g. not macOS, or the field is missing)."""
    if shutil.which("ioreg") is None:
        return None
    try:
        out = subprocess.run(
            ["ioreg", "-c", "IOHIDSystem"], capture_output=True, text=True, timeout=5
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    for line in out.splitlines():
        if "HIDIdleTime" in line:
            try:
                ns = int(line.rsplit("=", 1)[1].strip())
                return ns / 1_000_000_000
            except (ValueError, IndexError):
                return None
    return None


@dataclass
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
