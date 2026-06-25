"""Load and frame the Constitution — the fixed point inherited by EVERY agent
(Invariant 6, BUILD-SPEC §4).

This module is the inheritance mechanism: it loads `CONSTITUTION.md` and assembles each
agent's context OUTERMOST-FIRST, so the Constitution is always the outer frame and
task-specific instructions nest strictly inside it and can never displace it. The
factory (Phase 5) mints agents through this same seam; static agents use it directly.

The Constitution is read-only here — no agent may modify it (Invariant 9). Its SHA-256
fingerprint is the frozen-anchor identity used by drift audits (BUILD-SPEC §15).
"""

from __future__ import annotations

import hashlib
from functools import lru_cache
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CONSTITUTION_PATH = REPO_ROOT / "CONSTITUTION.md"

# Message-shaped context, compatible with the Ollama chat API.
Message = dict  # {"role": "system"|"user"|"assistant", "content": str}


@lru_cache(maxsize=1)
def load_constitution() -> str:
    return CONSTITUTION_PATH.read_text(encoding="utf-8")


def constitution_fingerprint() -> str:
    """Stable SHA-256 of the Constitution. Drift audits compare against this to detect
    any change to the fixed point (BUILD-SPEC §15)."""
    return hashlib.sha256(load_constitution().encode("utf-8")).hexdigest()


def frame_context(role_prompt: str, task: str | None = None, *,
                  history: list[Message] | None = None,
                  context_blocks: list[str] | None = None) -> list[Message]:
    """Assemble an agent's context outermost-first (BUILD-SPEC §13 priority order):
    Constitution -> role -> retrieved RAG context -> history -> task. The Constitution is
    ALWAYS messages[0]; everything else nests inside it and may never override it
    (Invariant 6).

    `context_blocks` are retrieved grounding (e.g. the Librarian's RAG chunks), injected
    after the role and before history per the §13 priority order.
    """
    messages: list[Message] = [{"role": "system", "content": load_constitution()}]
    if role_prompt:
        messages.append({"role": "system", "content": role_prompt})
    for block in context_blocks or []:
        messages.append({"role": "system", "content": block})
    messages.extend(history or [])
    if task is not None:
        messages.append({"role": "user", "content": task})
    return messages
