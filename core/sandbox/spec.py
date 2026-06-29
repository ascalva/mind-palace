"""Execution request/result types for the sandbox (BUILD-SPEC §11, Invariant 4).

Executed code is *powerless*: it gets no credentials, no network (unless an explicit,
logged, per-execution grant — not in Phase 4), and no access to the private vault. It
returns **data** (stdout/stderr/exit code), never actions on the system. Output is capped
so a result can never blow the context budget (§13).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

DEFAULT_TIMEOUT_S = 10
MAX_TIMEOUT_S = 120
MAX_OUTPUT_BYTES = 64 * 1024   # results are data; cap to protect the context budget (§13)
MAX_INPUT_BYTES = 16 * 1024 * 1024   # total `inputs` data piped IN; bounded so a dataset can't
#                                      exhaust memory or the stdin pipe (the data-in counterpart)


class Network(StrEnum):
    NONE = "none"   # the only mode Phase 4 runs. Scoped grants are a deliberate, logged
    #                 later extension (§11): per-execution, narrowly scoped, audited.


@dataclass(frozen=True)
class Limits:
    memory: str = "256m"   # podman --memory (also pins --memory-swap to forbid swap)
    cpus: float = 1.0
    pids: int = 128


@dataclass(frozen=True)
class ExecSpec:
    code: str
    language: str = "python"
    timeout_s: int = DEFAULT_TIMEOUT_S
    limits: Limits = field(default_factory=Limits)
    network: Network = Network.NONE
    env: dict[str, str] = field(default_factory=dict)   # NON-secret only (never secrets, §Secrets)
    # Data piped IN for the code to process — name -> text content, materialized read-only at
    # /tmp/input/<name> inside the sandbox (see policy.compose_program). This is how an agent
    # hands the sandbox a dataset to analyze (e.g. observed/IoT series for pattern-finding) and
    # gets results back: DATA in, DATA out — never creds, the vault, or the host fs (Invariant 4).
    # It rides STDIN with the code (no host bind mount), so the "nothing is mounted" structural
    # property — and thus vault-unreachability — is preserved.
    inputs: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.code.strip():
            raise ValueError("ExecSpec.code is empty")
        if not 0 < self.timeout_s <= MAX_TIMEOUT_S:
            raise ValueError(f"timeout_s must be in (0, {MAX_TIMEOUT_S}], got {self.timeout_s}")
        total = sum(len(v.encode("utf-8")) for v in self.inputs.values())
        if total > MAX_INPUT_BYTES:
            raise ValueError(f"inputs total {total} bytes exceeds {MAX_INPUT_BYTES} (§11 cap)")
        for name in self.inputs:
            if "/" in name or name in ("", ".", "..") or "\\" in name:
                raise ValueError(f"unsafe input name {name!r} (no path separators)")


@dataclass(frozen=True)
class ExecResult:
    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool = False
    duration_s: float = 0.0
    truncated: bool = False

    @property
    def ok(self) -> bool:
        return self.exit_code == 0 and not self.timed_out
