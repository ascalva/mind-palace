"""Typed facade over `psutil` (type-system-as-core-audit.md §2.5 boundary wrapper).

psutil ships no `py.typed` (V2, 2026-07-11). This module is the ONE place the REPO
touches the raw package; the vitals path and the lifecycle launcher read system
measurements through these typed functions only. Local measurement only — no
network (Invariant 2).

[banner: correction] That first sentence used to read *"the ONE place **core**
touches the raw package"*, and it was **aspirational, not enforced** — until bp-106
nothing anywhere (`ops/type_gate.py`, `ops/import_lint.py`, `scripts/check_imports.py`,
the hooks, CI, `[tool.ruff]`) mentioned `typedshims` at all, so the rule was a
docstring sentence. bp-105 then imported raw psutil in `ops/lifecycle/launcher.py`
(finding-0198) and nothing objected — the violation was authored, reviewed, gated and
merged. Two corrections, both from bp-106: the scope is the whole **repo**, not only
`core/` (bp-105's violation was in `ops/`, which the old wording arguably did not
cover), and the rule is now scanned mechanically by `ops.type_gate`
(`raw_shim_imports`), with an inline `# typedshim-exempt: <reason>` as the only
waiver. See bp-106 §3 Q1 and `docs/findings/finding-0223.md`.

**Exceptions are ABSORBED here, never re-raised (bp-106 §3 Q5).** The states a caller
must distinguish — `NoSuchProcess`, `AccessDenied` — are psutil *types*. A facade that
raises them forces every caller to import psutil to name them in an `except`, which
moves the import while keeping the type dependency: a quarantine in name only. So the
process accessors below return `None` on any failure. `loadavg_1m()` set this
precedent before the rule was written.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import psutil  # type: ignore[import-untyped]  # warrant: no py.typed upstream (V2); Any quarantined to this shim


@dataclass(frozen=True)
class VirtualMemory:
    """The fields of `psutil.virtual_memory()` the vitals emitter reads."""

    total: int  # bytes
    available: int  # bytes
    percent: float  # 0..100


def virtual_memory() -> VirtualMemory:
    vm = psutil.virtual_memory()
    return VirtualMemory(
        total=int(vm.total), available=int(vm.available), percent=float(vm.percent)
    )


def process_rss(pid: int) -> int:
    """Resident-set size of `pid`, in bytes."""
    return int(psutil.Process(pid).memory_info().rss)


def cpu_percent() -> float:
    """System-wide CPU percent since the previous call (non-blocking: interval=None)."""
    return float(psutil.cpu_percent(interval=None))


def loadavg_1m() -> float | None:
    """1-minute load average, or None on a platform without `getloadavg`."""
    if not hasattr(psutil, "getloadavg"):
        return None
    return float(psutil.getloadavg()[0])


# ── per-process identity: the accessors `ops/lifecycle/launcher.py` reads (bp-106 Item 1) ────────
#
# Moved here verbatim from `_process_identity` (bp-105, warrant finding-0198's OPEN hand-off) as a
# TRUST-BOUNDARY MOVE: behaviour is bit-identical, only the module that touches raw psutil changed.
# Each reads one accessor and absorbs every failure as `None` (module docstring, bp-106 §3 Q5).
#
# ⚑ Each constructs its own `psutil.Process(pid)` where `_process_identity` constructed one and
# shared it. Observationally identical: construction fails only for a pid that cannot be resolved,
# and then EVERY accessor on it would have failed too — so the pre-move `(None, None)` early return
# and the post-move "each returns None independently" reach the same tuple. Pinned by
# `test_an_unconstructable_process_is_ambiguity_not_a_crash` (test_restart_trustworthy.py), which
# drives this path with `psutil.Process` patched to raise `NoSuchProcess`.


def process_create_time(pid: int) -> float | None:
    """Unix epoch seconds at which `pid`'s process was created, or None if unreadable.

    None, never an exception: `psutil.NoSuchProcess` / `AccessDenied` are psutil TYPES, so a
    raising facade would force every caller to import psutil to name them — moving the import
    while keeping the dependency. Absorbing them here is what makes the quarantine real.

    The launcher's D1 disproof reads this: a process created after its run row's `started_at`
    cannot have written that row (finding-0198)."""
    try:
        return float(psutil.Process(pid).create_time())
    except Exception:  # noqa: BLE001 — an unreadable process is ambiguity, never a crash
        return None


def process_exe_name(pid: int) -> str | None:
    """Basename of the binary `pid` is actually EXECUTING, or None if unreadable.

    The BASENAME and not the whole path: an interpreter living under `~/python-projects/` would
    otherwise make every binary on that path read as one, and the launcher's D2 disproof ("is this
    process a Python interpreter?") could never fire.

    ⚑ Empty is UNREADABLE, not an answer. psutil returns `''` — it does not raise — when a
    process's executable cannot be determined, so `'' -> None` and the caller falls through to its
    fallback. Taking `''` as the answer would make D2 fire against every such process
    (`test_an_empty_exe_is_treated_as_unreadable_not_as_an_answer` is the mutation pin).

    `exe()` and not `cmdline()`: on macOS `cmdline()` raises AccessDenied for a foreign owner
    (measured against pid 1) while `name()`/`exe()` read fine — and a foreign owner is exactly the
    deployed case, the daemon running as the `ouroboros` principal."""
    try:
        return Path(str(psutil.Process(pid).exe())).name or None
    except Exception:  # noqa: BLE001 — an unreadable process is ambiguity, never a crash
        return None


def process_name(pid: int) -> str | None:
    """`pid`'s process name (e.g. 'launchd', 'python3.13'), or None if unreadable.

    This is the `comm`/argv0 basename, which depends on HOW the process was invoked — under
    `uv run pytest` on Linux it resolves to the console script, not the interpreter
    (warrant finding-0211). It is therefore the launcher's FALLBACK, never its first choice; see
    `_process_identity` for why the order is load-bearing in both directions.

    `name()` and not `cmdline()`, for the same AccessDenied reason recorded on `process_exe_name`.

    Emptiness is deliberately NOT folded to None here, unlike `process_exe_name`: `name()` is the
    last probe, so `''` there is a real (if uninformative) answer that the launcher's D2 reads as
    "not a Python interpreter". Folding it to None would silently convert a disproof into
    ambiguity, and ambiguity REFUSES (finding-0186) — a behaviour change, not a tidy-up."""
    try:
        return str(psutil.Process(pid).name())
    except Exception:  # noqa: BLE001 — an unreadable process is ambiguity, never a crash
        return None
