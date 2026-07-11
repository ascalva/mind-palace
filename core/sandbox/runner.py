"""Sandbox runners — the thing that actually executes isolated code (BUILD-SPEC §11).

`PodmanRunner` is the default substrate (rootless Podman). `WasmRunner` is the seam for the
pure-compute wasmtime+Pyodide path (the §11 upgrade option); it is declared but not built in
Phase 4. The runner shells out to `podman` — that is deterministic *code* acting, never a
model holding a shell (Invariant 3); the executed code itself is powerless (Invariant 4),
which is enforced structurally by the argv in `policy.py`.

The wall-clock timeout is enforced here via the subprocess timeout; a container that overran
is force-removed (and, if pooled, discarded rather than reused).
"""

from __future__ import annotations

import shutil
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from uuid import uuid4

from core.sandbox.policy import (
    SandboxPolicy,
    build_run_argv,
    build_warm_argv,
    compose_program,
    runtime_for,
)
from core.sandbox.spec import MAX_OUTPUT_BYTES, ExecResult, ExecSpec, Limits


def _truncate(text: str) -> tuple[str, bool]:
    raw = text or ""
    if len(raw.encode("utf-8")) <= MAX_OUTPUT_BYTES:
        return raw, False
    return raw.encode("utf-8")[:MAX_OUTPUT_BYTES].decode("utf-8", "replace"), True


class SandboxRunner(Protocol):
    def available(self) -> bool: ...
    def run_once(self, spec: ExecSpec, policy: SandboxPolicy) -> ExecResult: ...
    def start(self, policy: SandboxPolicy, limits: Limits, image: str) -> str: ...
    def exec_in(self, container: str, spec: ExecSpec) -> ExecResult: ...
    def reset(self, container: str) -> None: ...
    def destroy(self, container: str) -> None: ...


@dataclass
class PodmanRunner:
    binary: str = "podman"

    def available(self) -> bool:
        """Usable, not merely installed: the binary must exist AND the (rootless) Podman
        service must answer. On macOS `podman` can be on PATH while the machine is stopped."""
        if shutil.which(self.binary) is None:
            return False
        try:
            return subprocess.run([self.binary, "info"], capture_output=True,
                                  text=True, timeout=10).returncode == 0
        except (OSError, subprocess.SubprocessError):
            return False

    def _exec(self, argv: list[str], *, input_text: str, timeout_s: int,
              on_timeout: Callable[[], None] | None = None) -> ExecResult:
        t0 = time.monotonic()
        try:
            proc = subprocess.run(argv, input=input_text, capture_output=True,
                                  text=True, timeout=timeout_s)
        except subprocess.TimeoutExpired as e:
            if on_timeout is not None:
                on_timeout()
            out, _ = _truncate(e.stdout or "" if isinstance(e.stdout, str) else "")
            return ExecResult(stdout=out, stderr="wall-clock timeout", exit_code=-1,
                              timed_out=True, duration_s=time.monotonic() - t0)
        out, tr = _truncate(proc.stdout)
        err, _ = _truncate(proc.stderr)
        return ExecResult(stdout=out, stderr=err, exit_code=proc.returncode,
                          timed_out=False, duration_s=time.monotonic() - t0, truncated=tr)

    def run_once(self, spec: ExecSpec, policy: SandboxPolicy) -> ExecResult:
        name = f"mp-sbx-{uuid4().hex[:12]}"
        argv = build_run_argv(spec, policy, name=name)
        return self._exec(argv, input_text=compose_program(spec), timeout_s=spec.timeout_s,
                          on_timeout=lambda: self.destroy(name))

    def start(self, policy: SandboxPolicy, limits: Limits, image: str) -> str:
        name = f"mp-sbx-{uuid4().hex[:12]}"
        argv = build_warm_argv(policy, name=name, image=image, limits=limits)
        subprocess.run(argv, capture_output=True, text=True, timeout=60, check=True)
        return name

    def exec_in(self, container: str, spec: ExecSpec) -> ExecResult:
        _, cmd = runtime_for(spec.language)
        argv = [self.binary, "exec", "-i"]
        for k, v in spec.env.items():
            argv += ["--env", f"{k}={v}"]
        argv += [container, *cmd]
        return self._exec(argv, input_text=compose_program(spec), timeout_s=spec.timeout_s)

    def reset(self, container: str) -> None:
        subprocess.run([self.binary, "exec", container, "sh", "-c",
                        "rm -rf /tmp/* 2>/dev/null || true"],
                       capture_output=True, text=True, timeout=30)

    def destroy(self, container: str) -> None:
        subprocess.run([self.binary, "rm", "-f", container],
                       capture_output=True, text=True, timeout=30)


class WasmUnavailableError(RuntimeError):
    """The WASM runner was asked to run but wasmtime and/or a WASI python module is not placed."""


@dataclass
class WasmRunner:
    """Pure-compute substrate (BUILD-SPEC §11): a WASI build of CPython run under **wasmtime**.

    The strongest isolation we have — isolation BY ABSENCE OF SYSCALL IMPORTS rather than by
    dropped capabilities: a wasm guest can touch only what the host explicitly grants through
    WASI, and we grant nothing but stdio (no `sock_*`, no host preopens) → no network, no host
    fs, no vault, *structurally*, the same powerless guarantee as Podman but enforced by the
    runtime rather than the kernel. Preferred for pure computation; Podman remains the substrate
    for anything needing a fuller OS.

    Activation is an owner step (a heavy artifact, like the Podman libs image): `pip install
    wasmtime` (done) AND a WASI CPython at `wasm_module` (a `python.wasm`). Until both are
    present, `available()` is False and the RoutingRunner falls back to Podman — fail-closed,
    never a silent wrong-substrate run. The execution path below is real wasmtime; it activates
    the moment the module is placed (runbook → "WASM sandbox")."""

    wasm_module: Path | None = None      # path to a WASI CPython (python.wasm)
    fuel: int | None = None              # optional wasmtime fuel cap (deterministic step bound)

    def available(self) -> bool:
        if self.wasm_module is None or not Path(self.wasm_module).exists():
            return False
        try:
            # warrant(T3): optional dependency, absent until the owner activates the
            # WASM substrate — presence-probed, fail-closed (WasmUnavailableError).
            import wasmtime  # type: ignore[import-not-found]  # noqa: F401
        except ImportError:
            return False
        return True

    def run_once(self, spec: ExecSpec, policy: SandboxPolicy) -> ExecResult:
        if not self.available():
            raise WasmUnavailableError(
                "WASM runner needs `pip install wasmtime` + a WASI python at "
                f"wasm_module={self.wasm_module!r} (runbook → 'WASM sandbox')"
            )
        if spec.language != "python":
            raise ValueError("the WASM substrate runs python only")
        return self._run_wasi(compose_program(spec), spec.timeout_s)

    def _run_wasi(self, program: str, timeout_s: int) -> ExecResult:
        """Run `program` (read from stdin by the WASI python) under wasmtime, capturing stdio via
        temp files (WASI stdio is file-backed). A watchdog thread bumps the engine epoch to honor
        the wall-clock timeout. No WASI preopens/sockets are granted → powerless by construction."""
        import tempfile
        import threading

        # warrant(T3): optional dependency (see available()); reaching here implies installed.
        import wasmtime  # type: ignore[import-not-found]

        cfg = wasmtime.Config()
        cfg.epoch_interruption = True
        if self.fuel is not None:
            cfg.consume_fuel = True
        engine = wasmtime.Engine(cfg)
        with tempfile.TemporaryDirectory() as d:
            din, dout, derr = (Path(d) / n for n in ("in", "out", "err"))
            din.write_text(program, encoding="utf-8")
            dout.touch()
            derr.touch()
            store = wasmtime.Store(engine)
            if self.fuel is not None:
                store.set_fuel(self.fuel)
            store.set_epoch_deadline(1)
            wasi = wasmtime.WasiConfig()
            wasi.argv = ["python", "-"]                 # CPython reads the program from stdin
            wasi.stdin_file = str(din)
            wasi.stdout_file = str(dout)
            wasi.stderr_file = str(derr)
            store.set_wasi(wasi)                         # ONLY stdio — no preopen_dir, no sockets
            linker = wasmtime.Linker(engine)
            linker.define_wasi()
            module = wasmtime.Module.from_file(engine, str(self.wasm_module))

            timed_out = [False]

            def _interrupt() -> None:
                engine.increment_epoch()
                timed_out[0] = True

            timer = threading.Timer(timeout_s, _interrupt)
            t0 = time.monotonic()
            timer.start()
            exit_code = 0
            try:
                instance = linker.instantiate(store, module)
                instance.exports(store)["_start"](store)
            except wasmtime.ExitTrap as e:
                exit_code = e.code
            except wasmtime.Trap:
                exit_code = -1                           # trap = epoch interrupt (timeout) or fault
            finally:
                timer.cancel()
            out, tr = _truncate(dout.read_text(encoding="utf-8", errors="replace"))
            err, _ = _truncate(derr.read_text(encoding="utf-8", errors="replace"))
            return ExecResult(stdout=out, stderr=err, exit_code=exit_code,
                              timed_out=timed_out[0], duration_s=time.monotonic() - t0,
                              truncated=tr)

    # The warm-pool / persistent-container protocol is a Podman concept; WASM runs are always
    # fresh single-shot instances (use `run_once`), so these are not applicable.
    def start(self, policy: SandboxPolicy, limits: Limits, image: str) -> str:
        raise NotImplementedError("the WASM substrate has no warm-pool containers; use run_once")

    def exec_in(self, container: str, spec: ExecSpec) -> ExecResult:
        raise NotImplementedError("the WASM substrate has no warm-pool containers; use run_once")

    def reset(self, container: str) -> None: ...

    def destroy(self, container: str) -> None: ...


@dataclass
class RoutingRunner:
    """Picks the substrate per job: the WASM pure-compute path for python-with-no-network WHEN
    it is actually available, else Podman (BUILD-SPEC §11 / roadmap E2). Fail-safe by default —
    with no WASI module placed, every job routes to the verified Podman substrate."""

    wasm: WasmRunner
    podman: PodmanRunner

    def _pick(self, spec: ExecSpec) -> SandboxRunner:
        from core.sandbox.spec import Network
        if spec.language == "python" and spec.network is Network.NONE and self.wasm.available():
            return self.wasm
        return self.podman

    def available(self) -> bool:
        return self.wasm.available() or self.podman.available()

    def run_once(self, spec: ExecSpec, policy: SandboxPolicy) -> ExecResult:
        return self._pick(spec).run_once(spec, policy)

    # Warm-pool ops are Podman's (WASM has none); delegate so a pool built on a RoutingRunner works.
    def start(self, policy: SandboxPolicy, limits: Limits, image: str) -> str:
        return self.podman.start(policy, limits, image)

    def exec_in(self, container: str, spec: ExecSpec) -> ExecResult:
        return self.podman.exec_in(container, spec)

    def reset(self, container: str) -> None:
        self.podman.reset(container)

    def destroy(self, container: str) -> None:
        self.podman.destroy(container)


def build_runner(runtime: str, *, binary: str = "podman",
                 wasm_module: Path | None = None) -> SandboxRunner:
    if runtime == "podman":
        return PodmanRunner(binary=binary)
    if runtime == "wasm":
        return WasmRunner(wasm_module=wasm_module)
    if runtime == "routing":
        return RoutingRunner(wasm=WasmRunner(wasm_module=wasm_module),
                             podman=PodmanRunner(binary=binary))
    raise ValueError(f"unknown sandbox runtime {runtime!r}")
