"""Interface adapters (BUILD-SPEC §12, Invariant 11).

One contract, many transports. The PRIVATE DEFAULT is `LocalAdapter` — a local app reached
over loopback/Tailscale, so the owner's interactions never leave the trust boundary. Other
transports (WhatsApp/Telegram/Signal) route through a third party, so the owner's
*interactions* leave the boundary even though the corpus never does — those carry
`transits_third_party = True` and are **opt-in** (the gateway refuses them unless explicitly
allowed). The adapter only ever sees messages and replies; it cannot read the vault.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from edge.interface.protocol import InboundMessage, OutboundMessage


@runtime_checkable
class InterfaceAdapter(Protocol):
    name: str
    transits_third_party: bool

    def poll(self) -> list[InboundMessage]:
        """Return messages received since the last poll (may be empty)."""
        ...

    def send(self, message: OutboundMessage) -> None:
        """Deliver a reply to the owner."""
        ...


@dataclass
class LocalAdapter:
    """Private default: a local app over loopback/Tailscale. The local UI pushes the owner's
    messages via `receive()`; replies land in `sent` (what the UI renders). No third party."""

    name: str = "local"
    transits_third_party: bool = False
    _inbox: list[InboundMessage] = field(default_factory=list)
    sent: list[OutboundMessage] = field(default_factory=list)

    def receive(self, text: str, *, conversation: str = "default") -> InboundMessage:
        msg = InboundMessage(text=text, conversation=conversation)
        self._inbox.append(msg)
        return msg

    def poll(self) -> list[InboundMessage]:
        msgs, self._inbox = self._inbox[:], []
        return msgs

    def send(self, message: OutboundMessage) -> None:
        self.sent.append(message)


@dataclass
class WhatsAppAdapter:
    """Opt-in convenience adapter that transits a third party (Invariant 11). Declared to
    demonstrate the pluggable contract + the privacy flag; the live integration (an
    unofficial library / Business Cloud API, with its ToS/stability caveats) is not built
    in Phase 6."""

    name: str = "whatsapp"
    transits_third_party: bool = True

    def poll(self) -> list[InboundMessage]:
        raise NotImplementedError("WhatsApp adapter is an opt-in stub (Invariant 11)")

    def send(self, message: OutboundMessage) -> None:
        raise NotImplementedError("WhatsApp adapter is an opt-in stub (Invariant 11)")
