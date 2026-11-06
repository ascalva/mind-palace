"""The consumers of the instance namespace map (DI-2, #25): what a named instance runs as, writes
and is refused, beside a control showing Ouroboros's is unchanged.

The launcher drives the instance's own launchd job; notices land under the instance's root; the
stack, `backup.sh` and `run_with_secrets.sh`, which hold Ouroboros's labels, Keychain items and
staging dir, refuse a named instance. The script tests put a recording `security` first on PATH,
so a broken guard shows up as a call to it and the real Keychain is never reached.
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
from pathlib import Path

import pytest

from core.kernel.config import loader

ROOT = loader.REPO_ROOT


def _isolated(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(loader, "REPO_ROOT", tmp_path)          # roots and stores land in tmp
    monkeypatch.setattr(loader, "_CONFIG_DIR", tmp_path)
    monkeypatch.setattr(loader, "_INSTANCE_OVERLAY", tmp_path / "ouroboros.toml")
    monkeypatch.setattr(loader, "_LEGACY_OVERLAY", tmp_path / "local.toml")
    monkeypatch.setattr(loader, "LEVERS_OVERLAY", tmp_path / "levers.toml")
    monkeypatch.delenv(loader.OVERLAY_ENV, raising=False)


def _named(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, iid: str) -> loader.Config:
    overlay = tmp_path / f"{iid}.toml"
    overlay.write_text(f'[instance]\nid = "{iid}"\n')
    monkeypatch.setenv(loader.OVERLAY_ENV, str(overlay))
    loader.get_config.cache_clear()
    return loader.get_config()


def test_a_named_instance_drives_its_own_launchd_job(monkeypatch, tmp_path) -> None:
    from ops.lifecycle.launcher import PALACE_LABEL, LaunchDomain, build_launcher

    _isolated(monkeypatch, tmp_path)
    ouroboros = build_launcher(loader.load_config())
    assert ouroboros.launchd_label == PALACE_LABEL == "com.mind-palace.palace"     # control
    assert ouroboros.installed_plist == (
        Path.home() / "Library/LaunchAgents/com.mind-palace.palace.plist")
    assert ouroboros.domain.repo_plist(ouroboros.repo_root, PALACE_LABEL).exists()

    bench = build_launcher(_named(monkeypatch, tmp_path, "bench"))
    assert bench.launchd_label == "com.mind-palace.bench.palace"
    assert bench.installed_plist == (
        Path.home() / "Library/LaunchAgents/com.mind-palace.bench.palace.plist")
    assert LaunchDomain.system().installed_plist(bench.launchd_label) == Path(
        "/Library/LaunchDaemons/com.mind-palace.bench.palace.plist")
    # No committed plist bears a named instance's label, so `deploy` finds no drift to "repair"
    # and never copies Ouroboros's plist (Label com.mind-palace.palace) over this instance's.
    assert not bench.domain.repo_plist(bench.repo_root, bench.launchd_label).exists()
    assert bench.runs.path.is_relative_to(tmp_path / "instances" / "bench")


def test_notices_land_under_the_instance_root(monkeypatch, tmp_path) -> None:
    from core.stores.tasks import notices_path

    _isolated(monkeypatch, tmp_path)
    assert notices_path() == tmp_path / "data" / "handoff" / "mcp" / "notices.json"    # control
    _named(monkeypatch, tmp_path, "bench")
    assert notices_path() == (
        tmp_path / "instances" / "bench" / "data" / "handoff" / "mcp" / "notices.json")


def _stack():
    spec = importlib.util.spec_from_file_location("stack_script", ROOT / "scripts" / "stack.py")
    assert spec and spec.loader
    stack = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(stack)
    return stack


def test_the_stack_is_ouroboros_and_refuses_a_named_instance(monkeypatch, capsys) -> None:
    stack = _stack()
    assert stack.OVERLAY_ENV == loader.OVERLAY_ENV
    # the heartbeat's label in config/stack.toml is the one the namespace map derives for Ouroboros
    assert stack.CFG["tick"]["label"] == loader.InstanceConfig().label("tick")
    ran: list[object] = []
    monkeypatch.setattr(stack.subprocess, "run", lambda *a, **k: ran.append(a))
    monkeypatch.setenv(loader.OVERLAY_ENV, "config/instances/bench.toml")
    assert stack.main(["up"]) == 1
    assert ran == [] and "Ouroboros's" in capsys.readouterr().out


def _fake_security(tmp_path: Path) -> tuple[dict[str, str], Path]:
    """A PATH whose first `security` records its arguments and prints nothing."""
    bin_dir, calls = tmp_path / "bin", tmp_path / "security.calls"
    bin_dir.mkdir()
    fake = bin_dir / "security"
    fake.write_text(f'#!/bin/sh\necho "$@" >> "{calls}"\nexit 1\n')
    fake.chmod(0o755)
    env = {**os.environ, "PATH": f"{bin_dir}:{os.environ.get('PATH', '/usr/bin:/bin')}"}
    return env, calls


@pytest.mark.parametrize("script", [["ops/backup/backup.sh"],
                                    ["scripts/run_with_secrets.sh", "true"]])
def test_the_scripts_holding_ouroboros_secrets_refuse_a_named_instance(tmp_path, script) -> None:
    env, calls = _fake_security(tmp_path)
    env[loader.OVERLAY_ENV] = "config/instances/bench.toml"
    done = subprocess.run(["sh", str(ROOT / script[0]), *script[1:]], env=env, cwd=tmp_path,
                          capture_output=True, text=True, timeout=60)
    assert done.returncode == 1 and "MIND_PALACE_OVERLAY" in done.stderr
    assert not calls.exists(), "the guard ran after a Keychain read"


def test_control_without_the_guard_the_wrapper_reads_the_keychain(tmp_path) -> None:
    """The same harness on the wrapper with its guard cut out: the fake `security` is called, so
    the test above would see a guard that runs too late."""
    env, calls = _fake_security(tmp_path)
    env[loader.OVERLAY_ENV] = "config/instances/bench.toml"
    text = (ROOT / "scripts" / "run_with_secrets.sh").read_text()
    head, _, rest = text.partition('if [ -n "${MIND_PALACE_OVERLAY:-}" ]; then')
    unguarded = tmp_path / "unguarded.sh"
    unguarded.write_text(head + rest.partition("fi\n")[2])
    done = subprocess.run(["sh", str(unguarded), "true"], env=env, cwd=tmp_path,
                          capture_output=True, text=True, timeout=60)
    assert done.returncode == 0 and calls.exists()


def test_a_named_instance_has_no_dialogue_lane(monkeypatch, tmp_path, capsys) -> None:
    """The door's table and the dialogue sync read the instance's lanes: Ouroboros's two, a
    named instance's none, so nothing of its runs an edge reader over the owner's chats."""
    from core.ingest.table import build_table
    from ops.lifecycle.launcher import dialogue_sync

    _isolated(monkeypatch, tmp_path)
    ouroboros = {n for n in build_table(loader.load_config()).sources if n.startswith("dialogue/")}
    assert ouroboros == {"dialogue/openwebui", "dialogue/opencode"}                  # control
    cfg = _named(monkeypatch, tmp_path, "bench")
    assert not [n for n in build_table(cfg).sources if n.startswith("dialogue/")]
    ran: list[object] = []
    monkeypatch.setattr("core.ingest.door.run_library", lambda *a, **k: ran.append(a))
    assert dialogue_sync(cfg, ROOT) == 0 and ran == []
    assert "reads no dialogue lanes" in capsys.readouterr().out


def test_the_heartbeat_refuses_a_named_instance(monkeypatch, tmp_path, capsys) -> None:
    from ops import heartbeat

    _isolated(monkeypatch, tmp_path)
    _named(monkeypatch, tmp_path, "bench")
    monkeypatch.setattr(heartbeat, "tick", lambda *a, **k: pytest.fail("the beat ran"))
    assert heartbeat.main([]) == 1 and "Ouroboros's" in capsys.readouterr().out


@pytest.mark.parametrize(("module", "reads"), [
    ("edge.openwebui", ("latest_update", "export_chats")),
    ("edge.opencode_sessions", ("latest_update", "export_sessions")),
])
def test_the_dialogue_readers_refuse_a_named_instance(monkeypatch, module, reads) -> None:
    """Each reader refuses before it opens its source: the functions that read the owner's
    chats are replaced by ones that fail the test, so a guard placed too late shows."""
    import importlib

    reader = importlib.import_module(module)
    for name in reads:
        monkeypatch.setattr(reader, name, lambda *a, **k: pytest.fail("read the source"))
    monkeypatch.setenv(loader.OVERLAY_ENV, "config/instances/bench.toml")
    with pytest.raises(SystemExit) as refused:
        reader.main(["--latest"])
    assert "MIND_PALACE_OVERLAY" in str(refused.value.code)
    monkeypatch.delenv(loader.OVERLAY_ENV)                     # control: Ouroboros's run reads it
    with pytest.raises(pytest.fail.Exception, match="read the source"):
        reader.main(["--latest"])
