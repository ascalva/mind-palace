"""Interface message contract (BUILD-SPEC §12).

The adapter-facing message types. The on-disk handoff format (the JSON the gateway writes
for the core and reads back) is defined here on the edge side and **mirrored, not imported,**
by `core.interface` — the core/edge boundary is a filesystem handoff, never a shared import
(Invariant 2, CONVENTIONS).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4


def _utcnow() -> str:
    return datetime.now(UTC).replace(tzinfo=None).isoformat(timespec="seconds")


@dataclass(frozen=True)
class InboundMessage:
    text: str
    conversation: str = "default"
    id: str = field(default_factory=lambda: uuid4().hex)
    attachments: tuple[str, ...] = ()    # references only; the core fetches/handles content
    ts: str = field(default_factory=_utcnow)

    def to_request(self) -> dict:
        return {"id": self.id, "conversation": self.conversation, "text": self.text,
                "ts": self.ts}


@dataclass(frozen=True)
class OutboundMessage:
    text: str
    conversation: str = "default"
    id: str = ""
    ts: str = field(default_factory=_utcnow)

    @classmethod
    def from_response(cls, obj: dict) -> OutboundMessage:
        return cls(text=obj.get("text", ""), conversation=obj.get("conversation", "default"),
                   id=obj.get("id", ""), ts=obj.get("ts", ""))
