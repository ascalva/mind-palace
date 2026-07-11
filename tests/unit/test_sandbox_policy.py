"""The isolation profile is correct BY CONSTRUCTION (BUILD-SPEC §11, Invariant 4).

These assert the security properties on the podman argv directly — no Podman needed — so a
later edit that weakens isolation (adds a mount, enables the network, disables seccomp, runs
as root) breaks a test.
"""

import dataclasses
from typing import cast

import pytest

from core.sandbox import (
    SANDBOX_INPUT_DIR,
    ExecSpec,
    Limits,
    Network,
    SandboxPolicy,
    build_run_argv,
    build_warm_argv,
    compose_program,
)


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
    # `_guard_network` checks `is not Network.NONE` (identity, not enum-membership), so any
    # non-NONE value trips the guard — a plain str proves that INCLUDING values that aren't
    # (yet) real Network members, which is exactly what this test wants to pin down. Cast, not
    # a real Network member, on purpose.
    spec = dataclasses.replace(ExecSpec(code="x"), network=cast(Network, "scoped-grant"))
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


# --- data piping IN (ExecSpec.inputs → /tmp/input, in-band on stdin, no host mount) -------------
def test_compose_program_without_inputs_is_just_the_code():
    assert compose_program(ExecSpec(code="print(1)")) == "print(1)"


def test_compose_program_materializes_inputs_into_the_scratch_tmpfs():
    spec = ExecSpec(code="print('done')", inputs={"data.csv": "a,b\n1,2\n"})
    prog = compose_program(spec)
    assert SANDBOX_INPUT_DIR in prog and "data.csv" in prog   # preamble writes it
    assert prog.rstrip().endswith("print('done')")            # user code last
    assert "a,b" in prog                                       # the data is carried in-band


def test_compose_program_rejects_inputs_for_non_python():
    with pytest.raises(ValueError):
        compose_program(ExecSpec(code="echo hi", language="bash", inputs={"x": "y"}))


def test_inputs_are_size_capped_and_name_safe():
    from core.sandbox.spec import MAX_INPUT_BYTES
    with pytest.raises(ValueError):                            # path traversal in a name
        ExecSpec(code="x", inputs={"../escape": "data"})
    with pytest.raises(ValueError):                            # absolute/separator in a name
        ExecSpec(code="x", inputs={"a/b": "data"})
    with pytest.raises(ValueError):                            # over the total cap
        ExecSpec(code="x", inputs={"big": "z" * (MAX_INPUT_BYTES + 1)})


def test_run_argv_still_mounts_nothing_even_with_inputs():
    # The load-bearing property: data-in does NOT add a host mount, so the vault stays unreachable.
    argv = build_run_argv(ExecSpec(code="print(1)", inputs={"data.csv": "a,b\n1,2"}))
    assert "-v" not in argv
    assert not any(a.startswith(("--volume", "--mount")) for a in argv)
    assert "--network=none" in argv
