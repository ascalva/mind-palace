"""Execution broker — the thin facade agents use to run code (BUILD-SPEC §11, Invariant 4).

`run(spec) -> ExecResult` returns **data, never actions**. It routes through the warm pool
(reusing a ready sandbox) when the job's language matches the pooled image, else an ephemeral
container; it enforces the concurrency cap (Invariant 8) and **logs every execution** —
language, network mode, timeout — to telemetry so any (future) network grant is auditable
(§11). Phase 4 runs network-off only.
"""

from __future__ import annotations

from dataclasses import dataclass

from config.loader import Config
from core.sandbox.policy import SandboxPolicy
from core.sandbox.pool import SandboxBusyError, WarmPool
from core.sandbox.runner import SandboxRunner, build_runner
from core.sandbox.spec import ExecResult, ExecSpec
from core.stores.telemetry import TelemetryWriter


@dataclass
class ExecutionBroker:
    runner: SandboxRunner
    policy: SandboxPolicy
    pool: WarmPool | None = None
    telemetry: TelemetryWriter | None = None
    max_concurrency: int = 1
    _in_flight: int = 0

    def run(self, spec: ExecSpec) -> ExecResult:
        if self._in_flight >= self.max_concurrency:
            raise SandboxBusyError(
                f"concurrency cap {self.max_concurrency} reached (RAM ceiling, Invariant 8)"
            )
        self._in_flight += 1
        self._log(spec)
        try:
            if self.pool is not None and spec.language == self.pool.language:
                return self._run_pooled(self.pool, spec)
            return self.runner.run_once(spec, self.policy)
        finally:
            self._in_flight -= 1

    def _run_pooled(self, pool: WarmPool, spec: ExecSpec) -> ExecResult:
        # The pool arrives as a parameter (narrowed non-None by run()'s guard) so the
        # requirement is visible in the signature instead of an unchecked deref of self.pool.
        container = pool.acquire()
        healthy = False
        try:
            result = self.runner.exec_in(container, spec)
            healthy = not result.timed_out
            return result
        finally:
            pool.release(container, healthy=healthy)

    def _log(self, spec: ExecSpec) -> None:
        if self.telemetry is None:
            return
        # An audit trail for every execution; network mode is recorded so a scoped grant
        # (a later §11 extension) is never silent.
        self.telemetry.record_vital(
            "sandbox.exec", 1.0, unit="run", source="sandbox",
            labels={"language": spec.language, "network": str(spec.network),
                    "timeout_s": spec.timeout_s},
        )

    def shutdown(self) -> None:
        if self.pool is not None:
            self.pool.shutdown()


def build_broker(config: Config | None = None, *,
                 telemetry: TelemetryWriter | None = None) -> ExecutionBroker:
    """Wire a broker from config: the configured runtime + a warm pool sized to the
    concurrency cap."""
    from config.loader import get_config

    cfg = config or get_config()
    sb = cfg.sandbox
    from pathlib import Path
    wasm_module = Path(sb.wasm_module).expanduser() if sb.wasm_module else None
    runner = build_runner(sb.runtime, wasm_module=wasm_module)
    policy = SandboxPolicy(image=sb.image)
    from core.sandbox.spec import Limits

    limits = Limits(memory=sb.memory, cpus=sb.cpus, pids=sb.pids_limit)
    pool = None
    # The warm pool is a container concept (podman / routing-via-podman); the pure-wasm runtime
    # has no persistent containers, so it never pools.
    if sb.warm_pool_size > 0 and sb.runtime != "wasm":
        pool = WarmPool(runner=runner, policy=policy, limits=limits, size=sb.warm_pool_size)
    return ExecutionBroker(runner=runner, policy=policy, pool=pool,
                           telemetry=telemetry, max_concurrency=sb.max_concurrency)
