"""Deterministic context budgeter (BUILD-SPEC §13).

A tokenizer + assembler — *code, not a model*. It composes each agent invocation to fit
the active model's window with headroom for the reply, in the §13 priority order:

    Constitution -> role -> retrieved RAG chunks -> history -> tool outputs -> task

When it won't fit, it trims in the §13 order: tighten retrieval depth first (the primary
lever — retrieval is usually over-fetched), then compact history (sliding window, oldest
first), then truncate tool outputs, and — if even the mandatory frame won't fit — flag
`escalate` so the caller routes to a larger-window tier rather than silently dropping the
Constitution. The Constitution, role, and task are never trimmed (Invariant 6); keeping the
Constitution lean is therefore context-budget discipline, not just style.

Token counts are a deterministic ESTIMATE (no model in the loop); we bias slightly high and
reserve reply headroom so the estimate is safe. A real tokenizer can be injected via
`Budgeter(estimator=...)` without changing callers.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from core.constitution import Message, load_constitution

# h = the reply headroom in the fit constraint Στ ≤ W − h (WHITEPAPER-TECHNICAL §budget).
# BOUND (gap G7): h ≥ a role's largest expected reply, ~512–2048 tokens; 1024 is the default.
# Too small risks truncating the model's answer; too large wastes window. A per-role override
# is the §14 safe-lever's job once usage is tracked.
DEFAULT_REPLY_RESERVE = 1024     # h: tokens held back for the model's reply
_MSG_OVERHEAD = 4                # per-message role/formatting tokens (estimate)
_TRUNC_MARK = "\n…[truncated]"

Estimator = Callable[[str], int]


def estimate_tokens(text: str) -> int:
    """Deterministic token estimate (~4 chars/token, rounded up). Stable across runs and
    biased slightly high so budgeting with reply headroom stays safe."""
    return (len(text) + 3) // 4


def _msg_tokens(m: Message, est: Estimator) -> int:
    return est(m.get("content", "")) + _MSG_OVERHEAD


def _truncate_to_tokens(text: str, max_tokens: int, est: Estimator) -> str:
    if max_tokens <= 0:
        return ""
    if est(text) <= max_tokens:
        return text
    keep = max(0, max_tokens * 4 - len(_TRUNC_MARK))
    return text[:keep] + _TRUNC_MARK


@dataclass(frozen=True)
class ContextParts:
    role: str
    task: str
    retrieved: tuple[str, ...] = ()      # RAG chunks, highest-priority (nearest) first
    history: tuple[Message, ...] = ()    # conversation, oldest first
    tool_outputs: tuple[str, ...] = ()   # tool/code outputs (Phase 4+)
    constitution: str | None = None      # None => the loaded Constitution


@dataclass(frozen=True)
class BudgetReport:
    window: int
    reserve: int
    used_tokens: int
    retrieved_kept: int
    retrieved_dropped: int
    history_kept: int
    history_dropped: int
    tool_truncated: int
    fits: bool          # the assembled context fits window - reserve
    escalate: bool      # even the mandatory frame won't fit -> route to a larger window


@dataclass(frozen=True)
class BudgetedContext:
    messages: list[Message]
    report: BudgetReport


class ConstitutionFrameError(RuntimeError):
    """Refused: a caller tried to assemble a context whose outermost frame is not the canonical
    Constitution (Invariant 6/9) without a deliberate, visible override. The Constitution is a
    fixed point, not caller-substitutable content — closing the Threat-B assembly-logic seam."""


@dataclass
class Budgeter:
    window: int
    reserve: int = DEFAULT_REPLY_RESERVE
    estimator: Estimator = estimate_tokens

    def _t(self, text: str) -> int:
        return self.estimator(text)

    def assemble(self, parts: ContextParts, *,
                 allow_constitution_override: bool = False) -> BudgetedContext:
        # The outermost frame is the fixed point (Invariant 6/9), not caller-substitutable content.
        # Default: the loaded Constitution. A caller may pass `parts.constitution` ONLY if it is the
        # canonical text (a harmless echo) — anything else is a silent substitution of the governing
        # values and is REFUSED fail-closed, unless a test/tool sets `allow_constitution_override`
        # (loud, greppable, and never on the live dispatch path). Closes audit finding G9.3.
        canonical = load_constitution()
        constitution = parts.constitution
        if constitution is None:
            constitution = canonical
        elif constitution != canonical and not allow_constitution_override:
            raise ConstitutionFrameError(
                "refusing a non-canonical Constitution as the outermost frame — pass "
                "constitution=None to use the loaded fixed point, or "
                "assemble(..., allow_constitution_override=True) for a deliberate test/tool."
            )
        budget = self.window - self.reserve

        # Mandatory frame — never trimmed (Invariant 6): Constitution, role, task.
        const_msg: Message = {"role": "system", "content": constitution}
        role_msg: Message = {"role": "system", "content": parts.role}
        task_msg: Message = {"role": "user", "content": parts.task}
        mandatory_tokens = (
            _msg_tokens(const_msg, self.estimator)
            + _msg_tokens(role_msg, self.estimator)
            + _msg_tokens(task_msg, self.estimator)
        )

        retrieved = list(parts.retrieved)
        history = list(parts.history)
        tools = list(parts.tool_outputs)

        def total() -> int:
            t = mandatory_tokens
            t += sum(self._t(r) + _MSG_OVERHEAD for r in retrieved)
            t += sum(_msg_tokens(h, self.estimator) for h in history)
            t += sum(self._t(o) + _MSG_OVERHEAD for o in tools)
            return t

        ret_dropped = hist_dropped = tool_trunc = 0

        # 1) tighten retrieval depth (the primary lever) — drop lowest-ranked first.
        while total() > budget and retrieved:
            retrieved.pop()
            ret_dropped += 1
        # 2) compact history — sliding window, drop oldest first.
        while total() > budget and history:
            history.pop(0)
            hist_dropped += 1
        # 3) truncate tool outputs — shrink the last one toward fitting, else drop it. The
        # while-condition re-checks fit each pass, so this is correct for any estimator.
        while total() > budget and tools:
            over = total() - budget
            keep = (self._t(tools[-1]) + _MSG_OVERHEAD) - over
            if keep > _MSG_OVERHEAD:
                truncated = _truncate_to_tokens(tools[-1], keep - _MSG_OVERHEAD, self.estimator)
                if self._t(truncated) < self._t(tools[-1]):
                    tools[-1] = truncated
                    tool_trunc += 1
                    continue
            tools.pop()
            tool_trunc += 1

        escalate = total() > budget    # only the mandatory frame remains and still over
        messages: list[Message] = [const_msg, role_msg]
        messages += [{"role": "system", "content": r} for r in retrieved]
        messages += history
        messages += [{"role": "system", "content": o} for o in tools]
        messages.append(task_msg)

        report = BudgetReport(
            window=self.window,
            reserve=self.reserve,
            used_tokens=total(),
            retrieved_kept=len(retrieved),
            retrieved_dropped=ret_dropped,
            history_kept=len(history),
            history_dropped=hist_dropped,
            tool_truncated=tool_trunc,
            fits=not escalate,
            escalate=escalate,
        )
        return BudgetedContext(messages=messages, report=report)


def suggest_num_ctx(p95_tokens: int, *, headroom_frac: float = 0.25,
                    floor: int = 2048, step: int = 1024) -> int:
    """Right-size a role's load-time window from tracked usage (§13): p95 + headroom,
    rounded up to a `step` multiple, never below `floor`. The deterministic basis for the
    per-(model, role) window safe-lever (§14) — the OS agent may tune within bounds."""
    target = max(floor, int(p95_tokens * (1.0 + headroom_frac)))
    return ((target + step - 1) // step) * step
