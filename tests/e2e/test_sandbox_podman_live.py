"""Empirical isolation gate (BUILD-SPEC §11) — runs real containers. Auto-skips when Podman
is unavailable, like the live model tests. Run: pytest -m podman."""

import pytest

from core.sandbox import ExecSpec, PodmanRunner, SandboxPolicy

pytestmark = pytest.mark.podman

# "Usable" = binary present AND the Podman service answers (on macOS the machine may be off).
_HAS_PODMAN = PodmanRunner().available()
_skip = pytest.mark.skipif(not _HAS_PODMAN, reason="podman not available (machine not running?)")


@_skip
def test_runs_code_and_returns_stdout():
    res = PodmanRunner().run_once(ExecSpec(code="print('hello-sandbox')"), SandboxPolicy())
    assert res.ok and "hello-sandbox" in res.stdout


@_skip
def test_network_is_off():
    code = (
        "import socket\n"
        "try:\n"
        "    socket.create_connection(('1.1.1.1', 80), 2); print('NET-UP')\n"
        "except Exception:\n"
        "    print('NO-NET')\n"
    )
    res = PodmanRunner().run_once(ExecSpec(code=code), SandboxPolicy())
    assert "NO-NET" in res.stdout and "NET-UP" not in res.stdout


@_skip
def test_vault_is_unreachable():
    code = ("import os; p = os.path.expanduser('~/.mind-palace/vault'); "
            "print('EXISTS' if os.path.exists(p) else 'ABSENT')")
    res = PodmanRunner().run_once(ExecSpec(code=code), SandboxPolicy())
    assert "ABSENT" in res.stdout   # nothing mounted -> host vault path does not exist inside


@_skip
def test_wall_clock_timeout_is_enforced():
    res = PodmanRunner().run_once(ExecSpec(code="while True: pass", timeout_s=2), SandboxPolicy())
    assert res.timed_out


@_skip
def test_runs_as_non_root():
    res = PodmanRunner().run_once(ExecSpec(code="import os; print(os.getuid())"), SandboxPolicy())
    assert res.stdout.strip() != "0"
