"""The interface gateway (BUILD-SPEC §6, §12) — Zone B.

Relays owner messages between an adapter and the sealed core over the filesystem handoff,
and relays the core's replies back. The gateway holds the network-facing adapter; the core
holds the vault. Neither reaches the other's resource — they meet only at the handoff
(Invariant 2). Third-party adapters are refused unless the owner explicitly opts in
(Invariant 11).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from edge.interface.adapter import InterfaceAdapter
from edge.interface.channel import GatewayChannel


class ThirdPartyNotAllowedError(RuntimeError):
    """A third-party-transiting adapter was used without an explicit opt-in (Invariant 11)."""


@dataclass
class InterfaceGateway:
    adapter: InterfaceAdapter
    channel: GatewayChannel
    allow_third_party: bool = False     # opt-in switch for WhatsApp-style adapters (Inv 11)
    _pending: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.adapter.transits_third_party and not self.allow_third_party:
            raise ThirdPartyNotAllowedError(
                f"adapter {self.adapter.name!r} transits a third party; set "
                "allow_third_party=True to opt in (Invariant 11)"
            )

    def submit_inbound(self) -> list[str]:
        """Poll the adapter and hand any new messages to the core. Returns request ids."""
        ids = [self.channel.submit(m) for m in self.adapter.poll()]
        self._pending.extend(ids)
        return ids

    def deliver_responses(self) -> int:
        """Send any ready core responses back through the adapter. Returns how many."""
        delivered, still_pending = 0, []
        for rid in self._pending:
            resp = self.channel.read_response(rid)
            if resp is None:
                still_pending.append(rid)
            else:
                self.adapter.send(resp)
                delivered += 1
        self._pending = still_pending
        return delivered
