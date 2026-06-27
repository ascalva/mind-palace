"""The isolation profile is correct BY CONSTRUCTION (BUILD-SPEC §11, Invariant 4).

These assert the security properties on the podman argv directly — no Podman needed — so a
later edit that weakens isolation (adds a mount, enables the network, disables seccomp, runs
as root) breaks a test.
"""

import dataclasses

import pytest

from core.sandbox import ExecSpec, Limits, Network, SandboxPolicy, build_run_argv, build_warm_argv


def test_run_argv_has_full_isolation_and_mounts_nothing():
    argv = build_run_argv(ExecSpec(code="print(1)"))
    joined = " ".join(argv)
    assert "--network=none" in argv                  # no network
    assert "--read-only" in argv                     # read-only rootfs
    assert "--cap-drop=ALL" in argv                  # no capabilities
    assert "no-new-privileges" in joined             # no privilege escalation
    assert "--user" in argv and "65534:65534" in argv  # non-root
    assert "--memory" in argv and "256m" in argv     # memory limit
    assert "--pids-limit" in argv                    # pids limit
    # CRITICAL: nothing from the host is mounted -> the vault is structurally unreachable.
    assert "-v" not in argv
    assert not any(a.startswith(("--volume", "--mount")) for a in argv)
    assert "--privileged" not in argv
    assert "seccomp=unconfined" not in joined        # never disable seccomp
    # code is delivered on stdin to the interpreter (so no bind mount is needed)
    assert argv[-2:] == ["python3", "-"]


def test_run_argv_rejects_any_network_request():
    # Network grants are a deliberate, logged later extension; Phase 4 runs network-off only.
    spec = dataclasses.replace(ExecSpec(code="x"), network="scoped-grant")
    with pytest.raises(NotImplementedError):
        build_run_argv(spec)
    assert Network.NONE == "none"


def test_unsupported_language_raises():
    with pytest.raises(ValueError):
        build_run_argv(ExecSpec(code="x", language="brainfuck"))


def test_language_and_image_selection():
    argv = build_run_argv(ExecSpec(code="x", language="node"))
    assert "node:22-slim" in argv and argv[-2:] == ["node", "-"]
    override = build_run_argv(ExecSpec(code="x"), SandboxPolicy(image="custom:img"))
    assert "custom:img" in override


def test_env_is_passed_through():
    argv = build_run_argv(ExecSpec(code="x", env={"FOO": "bar"}))
    assert "--env" in argv and "FOO=bar" in argv


def test_warm_argv_is_an_isolated_idle_container():
    argv = build_warm_argv(SandboxPolicy(), name="c1", image="python:3.12-slim", limits=Limits())
    assert "-d" in argv and argv[-3:] == ["python:3.12-slim", "sleep", "infinity"]
    assert "--network=none" in argv and "--cap-drop=ALL" in argv and "--read-only" in argv
    assert "-v" not in argv
