"""Zone B — interface gateway + adapters (BUILD-SPEC §6, §12).

The networked relay between the owner's messaging front-end and the sealed core. The private
default is the local app over Tailscale (`LocalAdapter`); WhatsApp-style adapters are opt-in
(Invariant 11). The gateway reaches the core ONLY through the filesystem handoff
(`GatewayChannel`), never by importing it; it cannot read the vault.
"""

from edge.interface.adapter import InterfaceAdapter, LocalAdapter, WhatsAppAdapter
from edge.interface.channel import GatewayChannel
from edge.interface.gateway import InterfaceGateway, ThirdPartyNotAllowedError
from edge.interface.protocol import InboundMessage, OutboundMessage

__all__ = [
    "GatewayChannel",
    "InboundMessage",
    "InterfaceAdapter",
    "InterfaceGateway",
    "LocalAdapter",
    "OutboundMessage",
    "ThirdPartyNotAllowedError",
    "WhatsAppAdapter",
]
