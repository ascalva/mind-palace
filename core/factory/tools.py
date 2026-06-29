"""Tools — capability as object-capability handles (BUILD-SPEC §10, §11; skills-and-scope).

A tool is a narrow HANDLE an agent is given, not a flag it is granted (the telemetry
store-layer precedent: "the wrong access is impossible, not discouraged"). A minted agent's
dispatcher holds ONLY the handles for tools inside its resolved scope; a tool id that isn't
there resolves to nothing → the call is refused and routed to the human gate. Out-of-scope
is *unreachable*, not "checked then maybe allowed".

Tools are deterministic CODE (model advises, code acts — Invariant 3). A tool that runs code
does so through the Phase-4 sandbox broker (powerless: no creds/network/vault — Invariant 4).
The action path (the dispatcher) is deliberately separate from an agent's advisory respond().
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

ToolHandler = Callable[[dict[str, Any]], dict[str, Any]]


@dataclass(frozen=True)
class ToolSpec:
    id: str
    description: str
    handler: ToolHandler
    sandboxed: bool = False    # True => the handler executes code via the §11 broker


@dataclass(frozen=True)
class ToolResult:
    tool_id: str
    ok: bool
    data: dict[str, Any]


class ToolNotInScopeError(RuntimeError):
    """A tool id was invoked that is not among the agent's in-scope handles (§10)."""


@dataclass
class ToolRegistry:
    """All registered tools, independent of any role/skill (skills bind tools by name)."""

    _tools: dict[str, ToolSpec] = field(default_factory=dict)

    def register(self, spec: ToolSpec) -> ToolSpec:
        self._tools[spec.id] = spec
        return spec

    def get(self, tool_id: str) -> ToolSpec:
        return self._tools[tool_id]

    def ids(self) -> frozenset[str]:
        return frozenset(self._tools)

    def __contains__(self, tool_id: str) -> bool:
        return tool_id in self._tools


@dataclass
class ToolDispatcher:
    """Holds ONLY the in-scope tool handles — the object-capability enforcement point."""

    _handles: dict[str, ToolSpec]

    @property
    def scope(self) -> frozenset[str]:
        return frozenset(self._handles)

    def can_invoke(self, tool_id: str) -> bool:
        return tool_id in self._handles

    def invoke(self, tool_id: str, args: dict[str, Any]) -> ToolResult:
        spec = self._handles.get(tool_id)
        if spec is None:                       # unreachable, not "checked then refused"
            raise ToolNotInScopeError(tool_id)
        return ToolResult(tool_id=tool_id, ok=True, data=spec.handler(args))


def dispatcher_for(scope: frozenset[str], registry: ToolRegistry) -> ToolDispatcher:
    """Build a dispatcher holding handles for exactly the in-scope tools present in the
    registry — nothing else is reachable."""
    return ToolDispatcher({tid: registry.get(tid) for tid in scope if tid in registry})


def build_default_registry(broker: Any | None = None) -> ToolRegistry:
    """The Phase-5 tool set. `run_python` runs code in the §11 sandbox (powerless, returns
    data). It is registered only if a broker is provided; with no broker there are no
    executable tools at all."""
    reg = ToolRegistry()
    if broker is not None:
        reg.register(ToolSpec(
            id="run_python",
            description="Run short Python in the sandbox; returns stdout/stderr/exit (data only).",
            handler=_run_python_handler(broker),
            sandboxed=True,
        ))
    return reg


def _run_python_handler(broker: Any) -> ToolHandler:
    from core.sandbox.spec import ExecSpec

    def handler(args: dict[str, Any]) -> dict[str, Any]:
        res = broker.run(ExecSpec(
            code=args["code"],
            language=args.get("language", "python"),
            timeout_s=int(args.get("timeout_s", 10)),
            inputs=args.get("inputs", {}),   # data to analyze, materialized at /tmp/input/<name>
        ))
        return {"stdout": res.stdout, "stderr": res.stderr,
                "exit_code": res.exit_code, "timed_out": res.timed_out}

    return handler
