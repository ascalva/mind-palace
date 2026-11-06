"""The tools that name Ouroboros's own state outside the config refuse a named instance (DI-2).

Each of them reaches Ouroboros's data dir by path (`<repo>/data/…`, or `data/…` from the repo),
its bridge, its archive, its plane homes or its Vault. Under `MIND_PALACE_OVERLAY` it would act on
Ouroboros's state for the named instance, so it refuses first. The Python guards are checked
twice: by structure (the guard is the first thing the entry point does, and a control shows the
check rejects a guard placed later) and by behaviour where a run is cheap to fence. The shell
guards run with recording fakes first on PATH, so a guard placed too late shows as a call.
"""

from __future__ import annotations

import ast
import os
import subprocess
from pathlib import Path

import pytest

from core.kernel.config import loader

ROOT = loader.REPO_ROOT
OVERLAY = "config/instances/bench.toml"

# (file, entry point) whose first act is `ouroboros_only(...)`
GUARDED = [
    ("scripts/palace_mcp_handoff.py", "main"),
    ("scripts/curate_local.py", "main"),
    ("scripts/verify_planes.py", "main"),
    ("eval/query_battery.py", "main"),
    ("eval/storage_census.py", "main"),
    ("eval/quantization_bench.py", "main"),
    ("ops/plane_migrate.py", "main"),
    ("ops/float16_migrate.py", "main"),
]
# report writers whose cwd-relative default, data/reports, refuses
WRITERS = [
    ("eval/harness/report.py", "write_report"),
    ("eval/harness/fibers.py", "write_report"),
    ("eval/harness/experiment.py", "write_blind_sample"),
    ("eval/harness/experiment.py", "write_composite"),
]


def _body(source: str, name: str) -> list[ast.stmt]:
    fn = next(n for n in ast.walk(ast.parse(source))
              if isinstance(n, ast.FunctionDef) and n.name == name)
    body = fn.body
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
        body = body[1:]                                        # the docstring
    return [s for s in body if not isinstance(s, ast.ImportFrom)]


def _calls_the_guard(stmt: ast.stmt) -> bool:
    return (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call)
            and isinstance(stmt.value.func, ast.Name) and stmt.value.func.id == "ouroboros_only")


def _guarded_first(source: str, name: str) -> bool:
    return _calls_the_guard(_body(source, name)[0])


@pytest.mark.parametrize(("path", "name"), GUARDED)
def test_each_tool_refuses_before_it_acts(path, name) -> None:
    assert _guarded_first((ROOT / path).read_text(encoding="utf-8"), name), path


@pytest.mark.parametrize(("path", "name"), WRITERS)
def test_each_writer_guards_its_default_first(path, name) -> None:
    first = _body((ROOT / path).read_text(encoding="utf-8"), name)[0]
    assert isinstance(first, ast.If) and any(_calls_the_guard(s) for s in first.body), path


def test_control_the_structure_check_rejects_a_late_guard() -> None:
    late = "def main():\n    work()\n    ouroboros_only('x')\n"
    early = ("def main():\n    '''doc'''\n    from m import ouroboros_only\n"
             "    ouroboros_only('x')\n")
    assert not _guarded_first(late, "main") and _guarded_first(early, "main")


def test_the_guard_refuses_only_a_named_instance(monkeypatch) -> None:
    monkeypatch.delenv(loader.OVERLAY_ENV, raising=False)
    loader.ouroboros_only("a tool")                            # Ouroboros: nothing happens
    monkeypatch.setenv(loader.OVERLAY_ENV, "")
    loader.ouroboros_only("a tool")                            # empty is the default chain
    monkeypatch.setenv(loader.OVERLAY_ENV, OVERLAY)
    with pytest.raises(loader.InstanceOverlayError, match="Ouroboros's own state"):
        loader.ouroboros_only("a tool")


def test_a_report_into_data_reports_refuses_a_named_instance(monkeypatch, tmp_path) -> None:
    from eval.harness.report import write_report

    monkeypatch.setenv(loader.OVERLAY_ENV, OVERLAY)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(loader.InstanceOverlayError):
        write_report(object(), root="data/reports")            # type: ignore[arg-type]
    assert not (tmp_path / "data").exists()


def test_handoff_refuses_a_named_instance(monkeypatch, capsys) -> None:
    """handoff.py never imports core, so its guard is inline; it refuses before parsing."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("handoff_script", ROOT / "scripts" / "handoff.py")
    assert spec and spec.loader
    handoff = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(handoff)
    monkeypatch.setattr(handoff, "_parse", lambda argv: pytest.fail("parsed before refusing"))
    monkeypatch.setenv(loader.OVERLAY_ENV, OVERLAY)
    assert handoff.main(["--role", "x"]) == 1
    assert "MIND_PALACE_OVERLAY" in capsys.readouterr().err


def test_the_bridge_refuses_a_named_instance(monkeypatch) -> None:
    import edge.mcp_http as bridge

    monkeypatch.setattr(bridge, "build", lambda cfg: pytest.fail("the bridge started"))
    monkeypatch.setenv(loader.OVERLAY_ENV, OVERLAY)
    with pytest.raises(SystemExit) as refused:
        bridge.main([])
    assert "MIND_PALACE_OVERLAY" in str(refused.value.code)


def test_the_bridge_responder_refuses_a_named_instance(monkeypatch) -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location("responder",
                                                  ROOT / "scripts" / "palace_mcp_handoff.py")
    assert spec and spec.loader
    responder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(responder)
    monkeypatch.setattr(responder, "seal", lambda: pytest.fail("sealed before refusing"))
    monkeypatch.setenv(loader.OVERLAY_ENV, OVERLAY)
    with pytest.raises(loader.InstanceOverlayError):
        responder.main()


def _fakes(tmp_path: Path, names: tuple[str, ...]) -> tuple[dict[str, str], Path]:
    bin_dir, calls = tmp_path / "bin", tmp_path / "calls"
    bin_dir.mkdir()
    for name in names:
        fake = bin_dir / name
        fake.write_text(f'#!/bin/sh\necho "{name} $@" >> "{calls}"\nexit 1\n')
        fake.chmod(0o755)
    env = {**os.environ, "PATH": f"{bin_dir}:/usr/bin:/bin"}
    return env, calls


@pytest.mark.parametrize(("script", "shell"), [
    ("ops/vault/vault-unseal.sh", "sh"),
    ("ops/vault/setup_policies.sh", "sh"),
    ("ops/vault/setup_aws_engine.sh", "sh"),
    ("scripts/cockpit.sh", "bash"),
])
def test_the_ouroboros_scripts_refuse_a_named_instance(tmp_path, script, shell) -> None:
    env, calls = _fakes(tmp_path, ("security", "vault", "tmux", "terraform"))
    env.update({loader.OVERLAY_ENV: OVERLAY, "VAULT_ADDR": "http://127.0.0.1:1",
                "VAULT_TOKEN": "x", "BRIDGE_ROLE_ARN": "x"})
    done = subprocess.run([shell, str(ROOT / script), "--dry-run"], env=env, cwd=tmp_path,
                          capture_output=True, text=True, timeout=60)
    assert done.returncode == 1 and "MIND_PALACE_OVERLAY" in done.stderr, done.stderr
    assert not calls.exists(), calls.read_text()
