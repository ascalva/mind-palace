"""A trivial agent that inherits the Constitution (the inheritance + self-eval seam).

Every agent — static, scheduled, or minted by the factory (Phase 5) — is built this
way: the Constitution is its outermost frame and the role/task nest inside it
(Invariant 6), and no agent returns output without passing through the Constitution
pre-return check (§IV). The factory will extend this with tool scope, tiers, and the
scope ceiling; the Librarian (Phase 2, `core/librarian/`) is the first real specialization.

The self-evaluation logic lives in `core.selfcheck` and is re-exported here so callers
and tests can keep importing it from the agent module.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.constitution import Message, frame_context
from core.models import ModelServer
from core.selfcheck import Finding, SelfCheck, self_evaluate

__all__ = ["Agent", "Finding", "SelfCheck", "self_evaluate"]


@dataclass
class Agent:
    name: str
    role_prompt: str
    tier: str = "routine"
    server: ModelServer | None = None

    def build_context(self, task: str, *, history: list[Message] | None = None) -> list[Message]:
        """The agent's context, Constitution outermost (Invariant 6)."""
        return frame_context(self.role_prompt, task, history=history)

    def respond(self, task: str, *, history: list[Message] | None = None,
                think: bool | None = None) -> tuple[str, SelfCheck]:
        if self.server is None:
            raise RuntimeError(f"agent {self.name!r} has no model server bound")
        output = self.server.chat(self.tier, self.build_context(task, history=history), think=think)
        # A generic agent has no retrieval context, so grounding is N/A (sources=None).
        return output, self_evaluate(output)
