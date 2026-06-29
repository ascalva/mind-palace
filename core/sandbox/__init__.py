"""Zone A — sandboxed code execution: same power, no reach (BUILD-SPEC §11, Invariant 4).

Executed code runs in an ephemeral, network-off, vault-less, non-root, resource-limited
container (rootless Podman) and returns DATA, never actions. The isolation profile is built
into the podman argv in `policy.py` so it is verifiable by construction. A warm pool avoids
cold start; the broker is the thin facade agents call.
"""

from core.sandbox.broker import ExecutionBroker, build_broker
from core.sandbox.policy import (
    RUNTIMES,
    SANDBOX_INPUT_DIR,
    SandboxPolicy,
    build_run_argv,
    build_warm_argv,
    compose_program,
)
from core.sandbox.pool import SandboxBusyError, WarmPool
from core.sandbox.runner import (
    PodmanRunner,
    RoutingRunner,
    SandboxRunner,
    WasmRunner,
    WasmUnavailableError,
    build_runner,
)
from core.sandbox.spec import ExecResult, ExecSpec, Limits, Network

__all__ = [
    "RUNTIMES",
    "SANDBOX_INPUT_DIR",
    "ExecResult",
    "ExecSpec",
    "ExecutionBroker",
    "Limits",
    "Network",
    "PodmanRunner",
    "RoutingRunner",
    "SandboxBusyError",
    "SandboxPolicy",
    "SandboxRunner",
    "WarmPool",
    "WasmRunner",
    "WasmUnavailableError",
    "build_broker",
    "build_run_argv",
    "build_runner",
    "build_warm_argv",
    "compose_program",
]
