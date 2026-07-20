"""Item 1 (bp-030) — KeepAlive-aware maintenance control: `down` / `up` / `restart`.

A fake `launchctl` runner records every subcommand and models the bootstrapped/booted-out state,
so these exercise the exact incantations (`bootout` / `bootstrap`), idempotency, and the
not-installed fallbacks without touching the real launchd domain. `stop`/SIGTERM is NOT a `down`
(launchd's KeepAlive relaunches it); `restart` is a plain down→up cycle, never a HEAD promotion.
"""

import os
import subprocess
from pathlib import Path

from config.loader import load_config
from ops.lifecycle.launcher import (
    LaunchDomain,
    Launcher,
    _run_launchctl,
    _run_launchctl_sudo,
)
from ops.lifecycle.runs import RunLedger

_LABEL = "com.mind-palace.palace"


class _FakeLaunchctl:
    """Models `launchctl` for our label: `print` reflects the managed state; `bootout`/`bootstrap`
    toggle it. Records the argv of every call; `fail` forces a subcommand to a non-zero rc."""

    def __init__(self, *, managed: bool):
        self.managed = managed
        self.calls: list[list[str]] = []
        self.fail: set[str] = set()

    def __call__(self, argv: list[str]) -> subprocess.CompletedProcess[str]:
        self.calls.append(argv)
        verb = argv[0]
        if verb in self.fail:
            return subprocess.CompletedProcess(argv, 1, stdout="", stderr="boom")
        rc = 0
        if verb == "print":
            rc = 0 if self.managed else 1
        elif verb == "bootout":
            self.managed = False
        elif verb == "bootstrap":
            self.managed = True
        return subprocess.CompletedProcess(argv, rc, stdout="", stderr="")

    def verbs(self) -> list[str]:
        return [c[0] for c in self.calls]


def _launcher(tmp_path, *, managed: bool, installed: bool = True,
              domain: LaunchDomain | None = None):
    plist = tmp_path / "com.mind-palace.palace.plist"
    if installed:
        plist.write_text("<plist/>")
    fake = _FakeLaunchctl(managed=managed)
    launcher = Launcher(
        cfg=load_config(), runs=RunLedger(tmp_path / "runs.sqlite"),
        repo_root=Path(".").resolve(), launchctl=fake, installed_plist=plist,
        domain=domain or LaunchDomain.gui())
    return launcher, fake


def test_down_boots_the_agent_out(tmp_path):
    launcher, fake = _launcher(tmp_path, managed=True)
    assert launcher.down() == 0
    assert ["bootout", f"gui/{os.getuid()}/{_LABEL}"] in fake.calls   # true down, not SIGTERM


def test_up_bootstraps_the_agent(tmp_path):
    launcher, fake = _launcher(tmp_path, managed=False)
    assert launcher.up() == 0
    assert ["bootstrap", f"gui/{os.getuid()}", str(launcher.installed_plist)] in fake.calls


def test_restart_cycles_down_then_up(tmp_path):
    launcher, fake = _launcher(tmp_path, managed=True)
    assert launcher.restart() == 0
    # a plain cycle: bootout BEFORE bootstrap; no git/gate/deploy anywhere in the path.
    cycle = [v for v in fake.verbs() if v in {"bootout", "bootstrap"}]
    assert cycle == ["bootout", "bootstrap"]


def test_down_is_idempotent_when_already_out(tmp_path):
    launcher, fake = _launcher(tmp_path, managed=True)
    assert launcher.down() == 0
    first = fake.verbs().count("bootout")
    assert launcher.down() == 0                        # already out → reports, returns 0
    assert fake.verbs().count("bootout") == first      # no second bootout issued


def test_up_is_idempotent_when_already_up(tmp_path):
    launcher, fake = _launcher(tmp_path, managed=True)
    assert launcher.up() == 0
    assert "bootstrap" not in fake.verbs()             # already up → no bootstrap


def test_up_not_installed_is_a_clear_noop(tmp_path):
    launcher, fake = _launcher(tmp_path, managed=False, installed=False)
    assert launcher.up() == 0                          # a guided message, not a real failure
    assert fake.calls == []                            # never touched launchctl


def test_down_not_installed_falls_back_to_stop(tmp_path):
    launcher, fake = _launcher(tmp_path, managed=False, installed=False)
    rc = launcher.down()                               # no agent, no live run → plain stop path
    assert fake.calls == []                            # no bootout attempted
    assert rc == 1                                     # stop() reports "no active run" to drain


def test_down_surfaces_a_real_bootout_failure(tmp_path):
    launcher, fake = _launcher(tmp_path, managed=True)
    fake.fail = {"bootout"}
    assert launcher.down() != 0                        # real failure → non-zero (agent may be live)


# --- bp-078: the system-daemon domain (dn-plane-principals §3.1/§3.2) ---------------------------
# The gui-domain assertions above are the byte-identical DEFAULT (no domain passed). These NEW
# cases pin the daemon-mode incantations: `system/<label>` targets, the `system` bootstrap domain,
# the /Library/LaunchDaemons install path, and the `sudo launchctl` runner. No real launchctl/sudo
# runs — the injected fake records the subcommand argv; the sudo prefix is proven purely on the
# LaunchDomain object (below), so the fake stays sudo-agnostic and the gui tests are untouched.


def test_launch_domain_gui_is_the_historical_form():
    """The default domain reproduces today's gui incantations EXACTLY — the no-silent-change
    invariant (Item 1 falsifier)."""
    d = LaunchDomain.gui()
    uid = os.getuid()
    assert not d.needs_sudo
    assert d.target(_LABEL) == f"gui/{uid}/{_LABEL}"
    assert d.bootstrap_domain() == f"gui/{uid}"
    assert d.launchctl_argv(["print", d.target(_LABEL)]) == ["launchctl", "print",
                                                             f"gui/{uid}/{_LABEL}"]
    assert d.installed_plist() == Path.home() / "Library/LaunchAgents/com.mind-palace.palace.plist"
    assert d.repo_plist(Path("/repo")) == Path("/repo/ops/lifecycle/com.mind-palace.palace.plist")


def test_launch_domain_system_uses_sudo_and_system_targets():
    """The daemon variant: `sudo launchctl`, `system/<label>` targets, the LaunchDaemon plist,
    and the daemon SOURCE plist (`…-daemon.plist`, UserName ouroboros)."""
    d = LaunchDomain.system()
    assert d.needs_sudo
    assert d.target(_LABEL) == f"system/{_LABEL}"
    assert d.bootstrap_domain() == "system"
    assert d.launchctl_argv(["bootout", d.target(_LABEL)]) == ["sudo", "launchctl", "bootout",
                                                               f"system/{_LABEL}"]
    assert d.installed_plist() == Path("/Library/LaunchDaemons/com.mind-palace.palace.plist")
    assert d.repo_plist(Path("/repo")) == Path(
        "/repo/ops/lifecycle/com.mind-palace.palace-daemon.plist")


def test_system_launcher_defaults_to_sudo_runner_and_daemon_plist():
    """A system-domain Launcher with NO overrides binds the `sudo launchctl` runner and points
    installed_plist at /Library/LaunchDaemons (post_init); an explicit override still wins."""
    base = Launcher(cfg=load_config(), runs=RunLedger(tmp_daemon_runs()),
                    repo_root=Path(".").resolve(), domain=LaunchDomain.system())
    assert base.launchctl is _run_launchctl_sudo
    assert base.installed_plist == Path("/Library/LaunchDaemons/com.mind-palace.palace.plist")
    # a gui Launcher keeps the plain runner + LaunchAgent path
    gui = Launcher(cfg=load_config(), runs=RunLedger(tmp_daemon_runs()),
                   repo_root=Path(".").resolve())
    assert gui.launchctl is _run_launchctl
    assert gui.installed_plist == Path.home() / "Library/LaunchAgents/com.mind-palace.palace.plist"


def test_daemon_down_boots_out_system_target(tmp_path):
    launcher, fake = _launcher(tmp_path, managed=True, domain=LaunchDomain.system())
    assert launcher.down() == 0
    assert ["bootout", f"system/{_LABEL}"] in fake.calls   # daemon target, not gui/$UID


def test_daemon_up_bootstraps_the_system_domain(tmp_path):
    launcher, fake = _launcher(tmp_path, managed=False, domain=LaunchDomain.system())
    assert launcher.up() == 0
    assert ["bootstrap", "system", str(launcher.installed_plist)] in fake.calls


def tmp_daemon_runs() -> Path:
    """A throwaway runs-db path under the pytest tmp base (these two Launchers never open it —
    they only inspect post_init-derived fields)."""
    import tempfile
    return Path(tempfile.mkdtemp()) / "runs.sqlite"
