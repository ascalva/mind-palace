"""Gateway <-> sealed-core round-trip over the filesystem handoff (BUILD-SPEC §6, §12).

Proves: messages round-trip; the core processes purely from disk + a handler (never an
adapter / the network — Invariant 2); third-party adapters are refused unless opted in.
"""

import inspect
import json

import pytest

import core.interface
from core.interface import CoreInbox
from edge.interface import (
    GatewayChannel,
    InboundMessage,
    InterfaceGateway,
    LocalAdapter,
    ThirdPartyNotAllowedError,
    WhatsAppAdapter,
)


def test_channel_submit_then_read(tmp_path):
    ch = GatewayChannel(tmp_path / "h")
    m = InboundMessage(text="hi")
    rid = ch.submit(m)
    assert rid == m.id and ch.read_response(rid) is None     # no response yet
    (ch.responses_dir / f"{rid}.json").write_text(
        json.dumps({"id": rid, "text": "yo", "conversation": "default", "ts": "t"})
    )
    assert ch.read_response(rid).text == "yo"
    assert ch.read_response(rid) is None                     # consumed


def test_message_round_trips_gateway_to_core_to_gateway(tmp_path):
    handoff = tmp_path / "handoff"
    inbox = CoreInbox(handoff=handoff, handler=lambda text: f"echo: {text}")   # core side
    adapter = LocalAdapter()                                                   # edge side
    gateway = InterfaceGateway(adapter=adapter, channel=GatewayChannel(handoff))

    adapter.receive("hello palace")            # owner types into the local app
    assert gateway.submit_inbound() and len(gateway._pending) == 1
    assert inbox.process_once() == 1           # the sealed core handles it (separate process)
    assert gateway.deliver_responses() == 1    # reply relayed back to the adapter
    assert adapter.sent[-1].text == "echo: hello palace"
    assert gateway._pending == []


def test_core_inbox_never_imports_the_messaging_side():
    # The structural form of "network and private data never share a component" (Invariant 2):
    # the core side of the handoff must not import the networked edge.
    src = inspect.getsource(core.interface)
    assert "import edge" not in src and "from edge" not in src


def test_gateway_refuses_third_party_adapter_unless_opted_in(tmp_path):
    with pytest.raises(ThirdPartyNotAllowedError):
        InterfaceGateway(adapter=WhatsAppAdapter(), channel=GatewayChannel(tmp_path / "h"))
    gw = InterfaceGateway(adapter=WhatsAppAdapter(), channel=GatewayChannel(tmp_path / "h2"),
                          allow_third_party=True)
    assert gw.adapter.name == "whatsapp"


def test_handler_error_becomes_an_error_response_not_a_crash(tmp_path):
    handoff = tmp_path / "handoff"

    def boom(_text):
        raise ValueError("kaboom")

    inbox = CoreInbox(handoff=handoff, handler=boom)
    ch = GatewayChannel(handoff)
    rid = ch.submit(InboundMessage(text="x"))
    assert inbox.process_once() == 1
    assert "kaboom" in ch.read_response(rid).text
