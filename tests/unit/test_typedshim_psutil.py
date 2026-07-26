"""The `core/typedshims/psutil.py` boundary (bp-106 Item 3, warrant finding-0198 / §3 Q6).

The shim is the ONE place the repo touches raw `psutil`. bp-106 moved the three per-process
accessors `ops/lifecycle/launcher.py` reads — `create_time()`, `exe()`, `name()` — out of the
launcher and in here, discharging finding-0198's open hand-off. Until this file the psutil shim was
the only boundary wrapper with no test at all (§3 Q6); its lancedb sibling has had one since bp-103.

This module is the structural enforcement of three things a type annotation cannot prove:

1. **The quarantine is REAL, not nominal.** Every accessor returns `None` rather than propagating a
   psutil exception. Item 1's falsifier is that one of them leaks: a raising facade forces its
   caller to `import psutil` to name `NoSuchProcess`/`AccessDenied` in an `except`, which moves the
   import while keeping the type dependency (§3 Q5). The launcher's `except Exception` used to be
   that caller; the whole point of the move is that it no longer needs one.
2. **The shim is HONEST, not a laundering `__getattr__` proxy.** The declared surface is the WHOLE
   surface — the same falsifier bp-103 pinned for lancedb. A raw-psutil attribute reachable through
   this module would mean nothing was quarantined.
3. **The empty/None asymmetry between the two name probes is deliberate**, and it is the subtlest
   thing bp-106 moved. `process_exe_name('')` is None (unreadable, fall through); `process_name('')`
   is `''` (an answer D2 reads as "not an interpreter"). Collapsing them looks like a tidy-up and is
   a behaviour change — finding-0186's ambiguity ruling, inverted.

Local measurement only: no network, no subprocess, no daemon. Nothing here asserts on a value that
depends on host uptime or on which platform the runner is (the finding-0211 lesson: the probe must
be pinned by SHAPE, not by whatever the host happens to be).
"""

from __future__ import annotations

import os

import psutil  # type: ignore[import-untyped]  # typedshim-exempt: a test OF the boundary must fake `psutil.Process` and name `AccessDenied`/`NoSuchProcess`; handing those out through the shim is the laundering proxy this file's own falsifier forbids  # noqa: E501
import pytest

import core.typedshims.psutil as shim
from core.typedshims.psutil import (
    process_create_time,
    process_exe_name,
    process_name,
)

# Above the pid ceiling, so it can never name a live process — the same constant
# `test_restart_trustworthy.py` uses for its dead-pid fixture.
DEAD_PID = 2 ** 22

# The three accessors bp-106 moved. Every one is a `(pid) -> value | None` probe, so the
# no-raise and dead-pid properties below are parametrized over the set rather than repeated.
PROBES = (process_create_time, process_exe_name, process_name)
PROBE_IDS = tuple(p.__name__ for p in PROBES)


# ── the accessors read real values for a real process ─────────────────────────────────────

def test_create_time_reads_this_process_as_a_plausible_epoch() -> None:
    """A real reading for a real pid. Bounded loosely on purpose: an exact value is unassertable
    and an uptime-dependent one is flaky (§7 Item 3 invariant). 2020 < t <= now is enough to prove
    it is Unix epoch seconds and not, say, a monotonic clock or milliseconds."""
    created = process_create_time(os.getpid())
    assert created is not None
    assert 1_577_836_800.0 < created <= psutil.time.time() + 1.0  # 2020-01-01 < t <= now


def test_exe_name_reads_this_interpreter_and_is_a_BASENAME() -> None:  # noqa: N802 — emphasis
    """The launcher's D2 asks "is this a Python interpreter?" of this string, so for the process
    running the test suite it must contain "python" — and it must be a basename, not a path.

    The basename part is load-bearing rather than cosmetic: an interpreter living under
    `~/python-projects/` would make every binary on that path answer "python" to D2, and D2 could
    then never fire (warrant finding-0211)."""
    name = process_exe_name(os.getpid())
    assert name is not None
    assert "python" in name.lower()
    assert os.sep not in name, f"{name!r} is a path, not a basename — D2 would read the directory"


def test_name_reads_this_process_too() -> None:
    """`name()` is the FALLBACK probe, but it must work on its own terms. No assertion that it
    contains "python": that is exactly the invocation-dependent assumption that made CI red for 55
    consecutive runs on Linux while passing on macOS (finding-0211)."""
    assert process_name(os.getpid()) is not None


def test_a_root_owned_foreign_process_is_still_readable() -> None:
    """The DEPLOYED case, measured in bp-105: the daemon runs as the `ouroboros` principal, so the
    probe must read a process it does not own. pid 1 is root-owned everywhere.

    Deliberately NOT asserting on pid 1's `create_time` being old — that is uptime-dependent and
    would be flaky on a freshly-booted CI runner (§7 Item 3 invariant). Only readability is claimed,
    and only of the composite: on Linux `/proc/1/exe` is unreadable for a foreign owner while
    `name()` reads fine, which is precisely why the launcher keeps a fallback. Requiring `exe()`
    specifically would encode one platform's answer as the rule."""
    assert process_create_time(1) is not None
    assert (process_exe_name(1) or process_name(1)) is not None


# ── Item 1's FALSIFIER: no accessor may propagate a psutil exception ──────────────────────

@pytest.mark.parametrize("probe", PROBES, ids=PROBE_IDS)
def test_a_dead_pid_returns_None_rather_than_raising(probe) -> None:  # noqa: N802 — emphasis
    """⚑ ITEM 1's NAMED FALSIFIER. A pid above the ceiling makes `psutil.Process()` itself raise
    `NoSuchProcess`. Every accessor must absorb it.

    If any of these raised, the quarantine would be nominal: the caller would need to `import
    psutil` to name the exception type in an `except`, so the import would have moved while the
    dependency stayed (§3 Q5) — and `_process_identity`'s `except Exception`, the very thing bp-106
    removed, would have to come back."""
    assert probe(DEAD_PID) is None


@pytest.mark.parametrize("probe", PROBES, ids=PROBE_IDS)
def test_an_AccessDenied_accessor_returns_None_rather_than_raising(  # noqa: N802 — emphasis
        probe, monkeypatch: pytest.MonkeyPatch) -> None:
    """The same falsifier for the OTHER failure mode. A dead pid fails at construction; a foreign
    owner constructs fine and then denies the individual accessor (macOS `cmdline()`, Linux
    `/proc/<pid>/exe`). The host cannot be made to deny on demand, so the denial is faked — pinning
    the shape rather than the host, per finding-0211."""
    class _Denying:
        def create_time(self) -> float:
            raise psutil.AccessDenied(1)

        def exe(self) -> str:
            raise psutil.AccessDenied(1)

        def name(self) -> str:
            raise psutil.AccessDenied(1)

    monkeypatch.setattr(psutil, "Process", lambda _pid: _Denying())
    assert probe(1234) is None


# ── the empty/None asymmetry — the subtlest thing the move carried ────────────────────────

def _faked(monkeypatch: pytest.MonkeyPatch, *, exe: str, name: str) -> None:
    class _Proc:
        def create_time(self) -> float:
            return 0.0

        def exe(self) -> str:
            return exe

        def name(self) -> str:
            return name

    monkeypatch.setattr(psutil, "Process", lambda _pid: _Proc())


def test_an_empty_exe_is_unreadable_not_an_answer(monkeypatch: pytest.MonkeyPatch) -> None:
    """psutil returns `''` — it does not raise — when a process's executable cannot be determined.
    `''` is evidence of nothing, so the shim folds it to None and the launcher falls through to
    `process_name`. Take `''` as the answer instead and D2 fires against every such process, which
    is a fail-OPEN on a fail-closed guard."""
    _faked(monkeypatch, exe="", name="python3.13")
    assert process_exe_name(1234) is None


def test_an_exe_whose_basename_is_empty_is_also_unreadable(monkeypatch: pytest.MonkeyPatch) -> None:
    """`Path('/').name` is `''`. The emptiness guard is applied AFTER taking the basename, so a
    pathological path degrades to the fallback rather than to an empty "answer"."""
    _faked(monkeypatch, exe="/", name="python3.13")
    assert process_exe_name(1234) is None


def test_an_empty_name_is_preserved_as_empty_NOT_folded_to_None(  # noqa: N802 — emphasis
        monkeypatch: pytest.MonkeyPatch) -> None:
    """⚑ The asymmetry, pinned. `process_name` is the LAST probe, so `''` there is a real (if
    uninformative) answer, and D2 reads it as "not a Python interpreter" — a positive disproof.
    Folding it to None the way `process_exe_name` does would convert that disproof into ambiguity,
    and ambiguity REFUSES (finding-0186): `start` would refuse where it previously proceeded.

    That is a behaviour change disguised as consistency, so it is a test and not a comment. The
    asymmetry is inherited verbatim from the pre-bp-106 launcher body (`or None` on the exe branch,
    a bare `str()` on the name branch)."""
    _faked(monkeypatch, exe="", name="")
    assert process_name(1234) == ""
    assert process_name(1234) is not None


# ── Item 3's FALSIFIER: the shim declares its whole surface ───────────────────────────────

def test_the_shim_is_not_a_laundering_proxy_onto_raw_psutil() -> None:
    """⚑ ITEM 3's NAMED FALSIFIER — the same one bp-103 pinned for lancedb. A shim that proxies has
    quarantined nothing: raw `Any` walks straight back into the checked region.

    `pids` and `Popen` are real, useful psutil attributes and must be unreachable here. `psutil`
    itself IS bound in this module (that is unavoidable — it is the module doing the importing), so
    the property asserted is the one that matters: no dynamic passthrough exists, and the callable
    surface is exactly the seven declared functions."""
    assert not hasattr(shim, "__getattr__"), "the shim forwards blindly — Any is laundering"
    for absent in ("pids", "Popen", "process_iter", "boot_time", "disk_usage", "net_io_counters"):
        assert not hasattr(shim, absent), f"raw psutil surface {absent!r} is reachable via the shim"


def test_the_declared_surface_is_exactly_the_pre_bp106_four_plus_the_moved_three() -> None:
    """Additive, and nothing speculative. bp-106 is a MOVE: it may add exactly the accessors the
    launcher already read and no more (§9's non-goal — the count reads "two" because the plan
    predates `e49a715`, which made the launcher read three; the intent, "nothing beyond what
    moves", is what this pins). If a future change widens the shim, this fails and the widening has
    to arrive with the call that needs it — the lancedb shim's stated discipline, applied here."""
    # `__module__` filters out imported callables (`Path`, `dataclass`) — the question is what this
    # module DEFINES, not what it happens to have in scope.
    public = {
        n for n, v in vars(shim).items()
        if not n.startswith("_") and callable(v) and getattr(v, "__module__", None) == shim.__name__
    }
    assert public == {
        # pre-bp-106, untouched by the move
        "virtual_memory", "process_rss", "cpu_percent", "loadavg_1m",
        # moved in by bp-106 Item 1
        "process_create_time", "process_exe_name", "process_name",
        # the frozen dataclass `virtual_memory()` returns
        "VirtualMemory",
    }


def test_the_pre_bp106_surface_still_behaves(monkeypatch: pytest.MonkeyPatch) -> None:
    """Item 1's acceptance bar: ADDITIVE. The four pre-existing exports keep their signatures and
    their behaviour — including `process_rss`, whose RAISING signature bp-106 deliberately left
    alone (§9 non-goal; the latent leak is filed, not fixed)."""
    vm = shim.virtual_memory()
    assert vm.total > 0 and vm.available > 0 and 0.0 <= vm.percent <= 100.0
    assert shim.process_rss(os.getpid()) > 0
    assert 0.0 <= shim.cpu_percent() <= 100.0 * (os.cpu_count() or 1)

    load = shim.loadavg_1m()
    assert load is None or load >= 0.0

    # `process_rss` still RAISES rather than returning None — the asymmetry §9 protects and §10
    # requires be filed rather than folded in. Pinned so the follow-up finding has a live referent.
    with pytest.raises(psutil.NoSuchProcess):
        shim.process_rss(DEAD_PID)


def test_the_moved_accessors_resolve_psutil_at_CALL_time(  # noqa: N802 — emphasis
        monkeypatch: pytest.MonkeyPatch) -> None:
    """The mechanism the launcher's five probe tests depend on, asserted where it now lives.

    `test_restart_trustworthy.py::_fake_psutil` patches `Process` on the REAL psutil module object
    and drives `_process_identity` through it. That only works because the shim looks the attribute
    up at call time (`psutil.Process(pid)`) rather than binding it at import (`from psutil import
    Process`). Rewriting the import to a `from`-import would silently un-test the probe layer, so
    the resolution order is pinned here rather than assumed there."""
    _faked(monkeypatch, exe="/opt/whatever/bin/python9.9", name="sentinel")
    assert process_exe_name(4321) == "python9.9"
    assert process_name(4321) == "sentinel"
