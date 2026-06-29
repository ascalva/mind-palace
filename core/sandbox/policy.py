"""The sandbox security profile, built into the podman argv (BUILD-SPEC §11, Invariant 4).

These are PURE functions so the isolation is verifiable by construction, not just empirically:
a test can assert the argv carries `--network=none`, `--read-only`, `--cap-drop=ALL`,
non-root `--user`, the resource limits, and — critically — that it mounts *nothing* from the
host, so the private vault (indeed the whole host filesystem) is structurally unreachable.
Code is delivered on **stdin** to the interpreter, so no bind mount is ever needed.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from core.sandbox.spec import ExecSpec, Limits, Network

# Where piped-in data lands inside the sandbox (the isolated scratch tmpfs, not a host mount).
SANDBOX_INPUT_DIR = "/tmp/input"

# language -> (default image, argv that executes a program read from STDIN)
RUNTIMES: dict[str, tuple[str, list[str]]] = {
    "python": ("python:3.12-slim", ["python3", "-"]),
    "bash": ("bash:5", ["bash", "-s"]),
    "node": ("node:22-slim", ["node", "-"]),
}


@dataclass(frozen=True)
class SandboxPolicy:
    image: str | None = None              # override the language default image
    user: str = "65534:65534"             # nobody:nogroup — non-root (Invariant 4)
    seccomp_profile: str | None = None    # None => podman's default (secure) seccomp profile
    tmpfs_size: str = "64m"               # scratch /tmp size
    extra: tuple[str, ...] = ()           # escape hatch; never used to add mounts/network


DEFAULT_POLICY = SandboxPolicy()   # module-level singleton (avoids a call in arg defaults)


def compose_program(spec: ExecSpec) -> str:
    """The exact program piped to the interpreter on stdin: the user's code, prefixed (when
    `inputs` are present) with a preamble that materializes each input to `/tmp/input/<name>`.

    The data travels IN-BAND on stdin, NOT via a host bind mount — so the structural guarantee
    that nothing from the host (the vault, indeed the whole host fs) is reachable is unchanged
    (Invariant 4). Supported for python only (the data-analysis target); requesting inputs for
    another language is refused rather than silently dropped."""
    if not spec.inputs:
        return spec.code
    if spec.language != "python":
        raise ValueError(f"data `inputs` are supported for python only, not {spec.language!r}")
    payload = json.dumps(spec.inputs)            # name -> text
    preamble = (
        "import os as _os, json as _json\n"
        f"_os.makedirs({SANDBOX_INPUT_DIR!r}, exist_ok=True)\n"
        f"for _n, _v in _json.loads({payload!r}).items():\n"
        f"    open(_os.path.join({SANDBOX_INPUT_DIR!r}, _n), 'w').write(_v)\n"
        "del _os, _json, _n, _v\n"
    )
    return preamble + "\n" + spec.code


def runtime_for(language: str) -> tuple[str, list[str]]:
    try:
        return RUNTIMES[language]
    except KeyError:
        raise ValueError(f"unsupported sandbox language {language!r}") from None


def image_for(language: str, policy: SandboxPolicy) -> str:
    return policy.image or runtime_for(language)[0]


def _isolation_flags(limits: Limits, policy: SandboxPolicy) -> list[str]:
    """The structural isolation common to every sandbox container. NB: no `-v`/`--mount`
    anywhere — nothing from the host is exposed, so the vault cannot be read (Invariant 4)."""
    flags = [
        "--network=none",                       # no network (Invariant 4)
        "--read-only",                          # read-only rootfs
        f"--tmpfs=/tmp:rw,nosuid,nodev,noexec,size={policy.tmpfs_size}",  # scratch only
        "--cap-drop=ALL",                       # drop every Linux capability
        "--security-opt", "no-new-privileges",  # no privilege escalation
        "--user", policy.user,                  # non-root
        "--memory", limits.memory,
        "--memory-swap", limits.memory,         # == memory => no swap headroom
        "--cpus", str(limits.cpus),
        "--pids-limit", str(limits.pids),
        "--workdir", "/tmp",
    ]
    # None => podman applies its default seccomp profile (the secure default); we never
    # pass `seccomp=unconfined`, which would disable it.
    if policy.seccomp_profile is not None:
        flags += ["--security-opt", f"seccomp={policy.seccomp_profile}"]
    return flags


def _guard_network(spec: ExecSpec) -> None:
    if spec.network is not Network.NONE:
        raise NotImplementedError(
            "scoped network grants are a deliberate, logged later extension (§11); "
            "Phase 4 runs network-off only"
        )


def build_run_argv(spec: ExecSpec, policy: SandboxPolicy = DEFAULT_POLICY, *,
                   name: str | None = None) -> list[str]:
    """Ephemeral `podman run --rm`: isolate, feed the code on stdin, capture output, vanish."""
    _guard_network(spec)
    _, cmd = runtime_for(spec.language)
    argv = ["podman", "run", "--rm", "-i", *_isolation_flags(spec.limits, policy)]
    for k, v in spec.env.items():
        argv += ["--env", f"{k}={v}"]
    if name:
        argv += ["--name", name]
    argv += list(policy.extra)
    argv.append(image_for(spec.language, policy))
    argv += cmd
    return argv


def build_warm_argv(policy: SandboxPolicy, *, name: str, image: str,
                    limits: Limits) -> list[str]:
    """Start a long-lived, idle, fully-isolated container for the warm pool. It holds no
    job; code is later `podman exec`'d into its scratch tmpfs and run."""
    return [
        "podman", "run", "-d", "--name", name,
        *_isolation_flags(limits, policy),
        image, "sleep", "infinity",
    ]
