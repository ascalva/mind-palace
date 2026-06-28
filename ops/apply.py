"""The execute/rollback primitive: write a knob value into the machine-owned overlay (§14).

`execute` and `rollback` in the self-mod loop both come down to mutating ONE file —
`config/levers.toml`, a gitignored overlay the loop owns end to end. This module is that
mutation, kept deliberately small and free of any policy: it writes the value it is handed.
All the judgment (bounds, approval, validation) lives upstream; by the time a value reaches
here it has already cleared the gate.

Two properties matter for §14's "reversible":
  * The loop NEVER edits the owner's hand-authored `config/local.toml`. It writes only
    `levers.toml`, and the loader overlays local.toml *on top* of it, so a human override
    always wins (config/loader.py). The writable surface is one file, fully auditable.
  * Every write returns the EXACT prior overlay state for that key (a value, or "absent").
    Rollback replays that prior state — restoring a previous value, or removing the key if the
    loop had introduced it — so an executed change reverses with no residue.

The on-disk format is a strict subset (sections of scalar `key = value`) that this module both
reads (via tomllib) and re-emits deterministically, so the file round-trips and diffs cleanly.
"""

from __future__ import annotations

import os
import tomllib
from pathlib import Path

from config.loader import LEVERS_OVERLAY
from ops.levers import Lever, LeverKind

_HEADER = (
    "# MACHINE-OWNED — written by the self-modification loop (ops/apply.py), not by hand.\n"
    "# Each value is a knob tuned through the propose→approve→execute→validate→rollback gate\n"
    "# (BUILD-SPEC §14). The loader overlays config/local.toml ON TOP of this, so a human\n"
    "# override in local.toml always wins. Safe to delete: deleting reverts every knob to its\n"
    "# committed default. Do not add sections/keys here that are not registered levers.\n"
)


def read_overlay(path: Path = LEVERS_OVERLAY) -> dict[str, dict]:
    """Parse the overlay into {section: {key: value}}. Missing file → empty (no knobs tuned)."""
    if not path.exists():
        return {}
    return tomllib.loads(path.read_text(encoding="utf-8"))


def _format(value: float | int, kind: LeverKind) -> str:
    # repr() gives the shortest round-tripping float literal; int stays int.
    return str(int(value)) if kind is LeverKind.INT else repr(float(value))


def write_overlay(data: dict[str, dict], path: Path = LEVERS_OVERLAY) -> None:
    """Emit `data` deterministically (sorted sections + keys) and replace the file atomically.

    Values are written untyped-by-section here because callers always pass already-coerced
    numbers; the kind only affects formatting, handled in `overlay_set`/`overlay_restore` which
    pre-format. Here we render whatever scalar is present."""
    lines = [_HEADER]
    for section in sorted(data):
        body = data[section]
        if not body:
            continue
        lines.append(f"\n[{section}]\n")
        for key in sorted(body):
            v = body[key]
            rendered = str(int(v)) if isinstance(v, int) and not isinstance(v, bool) else repr(v)
            lines.append(f"{key} = {rendered}\n")
    text = "".join(lines)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)  # atomic on POSIX — no half-written overlay is ever observed


def overlay_get(lever: Lever, path: Path = LEVERS_OVERLAY) -> float | int | None:
    """The value this lever currently has IN THE OVERLAY (what the loop last set), or None if the
    loop has never set it (the knob is at its committed default / a human override)."""
    return read_overlay(path).get(lever.section, {}).get(lever.key)


def overlay_set(
    lever: Lever, value: float | int, path: Path = LEVERS_OVERLAY
) -> float | int | None:
    """Set the lever's overlay value; return the PRIOR overlay value (None if it was absent), so
    the caller can record exactly what to restore on rollback."""
    data = read_overlay(path)
    section = data.setdefault(lever.section, {})
    prior = section.get(lever.key)
    section[lever.key] = lever.coerce(value)
    write_overlay(data, path)
    return prior


def overlay_restore(lever: Lever, prior: float | int | None, path: Path = LEVERS_OVERLAY) -> None:
    """Reverse an `overlay_set`: restore the prior value, or remove the key entirely if the loop
    had introduced it (prior was None). Leaves an empty section pruned so the file stays clean."""
    data = read_overlay(path)
    section = data.get(lever.section, {})
    if prior is None:
        section.pop(lever.key, None)
    else:
        section[lever.key] = lever.coerce(prior)
    if not section:
        data.pop(lever.section, None)
    else:
        data[lever.section] = section
    write_overlay(data, path)
