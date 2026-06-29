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


@_skip
def test_piped_in_data_is_readable_and_processed():
    # The data-in / data-out path: hand the sandbox a CSV, have stdlib code sum a column.
    code = (
        "import csv\n"
        "with open('/tmp/input/series.csv') as f:\n"
        "    rows = list(csv.DictReader(f))\n"
        "print(sum(int(r['v']) for r in rows))\n"
    )
    spec = ExecSpec(code=code, inputs={"series.csv": "t,v\n1,10\n2,20\n3,12\n"})
    res = PodmanRunner().run_once(spec, SandboxPolicy())
    assert res.ok and res.stdout.strip() == "42"


@_skip
def test_vault_still_unreachable_with_inputs_present():
    # Piping data IN must not open a host path: the vault remains absent even with inputs.
    code = ("import os\n"
            "print('input_present' if os.path.exists('/tmp/input/x') else 'input_absent')\n"
            "vp = os.path.expanduser('~/.mind-palace/vault')\n"
            "print('vault_present' if os.path.exists(vp) else 'vault_absent')\n")
    res = PodmanRunner().run_once(ExecSpec(code=code, inputs={"x": "hi"}), SandboxPolicy())
    lines = res.stdout.split()
    assert "input_present" in lines      # the data arrived
    assert "vault_absent" in lines and "vault_present" not in lines   # the vault did NOT
