"""Interface adapters + message contract (BUILD-SPEC §12, Invariant 11)."""

import pytest

from edge.interface import InboundMessage, InterfaceAdapter, LocalAdapter, WhatsAppAdapter
from edge.interface.protocol import OutboundMessage


def test_inbound_to_request_and_outbound_from_response():
    m = InboundMessage(text="q", conversation="c")
    req = m.to_request()
    assert req["text"] == "q" and req["conversation"] == "c" and req["id"] == m.id
    out = OutboundMessage.from_response({"text": "a", "conversation": "c", "id": req["id"]})
    assert out.text == "a" and out.id == req["id"]


def test_local_adapter_is_private_and_round_trips_in_memory():
    a = LocalAdapter()
    assert a.transits_third_party is False          # private default, no third party
    a.receive("hi", conversation="c1")
    msgs = a.poll()
    assert [m.text for m in msgs] == ["hi"] and msgs[0].conversation == "c1"
    assert a.poll() == []                            # drained after poll
    a.send(OutboundMessage(text="reply", conversation="c1"))
    assert a.sent[-1].text == "reply"


def test_whatsapp_adapter_is_flagged_third_party_and_stubbed():
    w = WhatsAppAdapter()
    assert w.transits_third_party is True            # interactions leave the boundary (Inv 11)
    with pytest.raises(NotImplementedError):
        w.poll()


def test_adapters_satisfy_the_contract():
    assert isinstance(LocalAdapter(), InterfaceAdapter)
    assert isinstance(WhatsAppAdapter(), InterfaceAdapter)
