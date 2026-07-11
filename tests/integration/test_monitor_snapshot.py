"""The core→edge monitoring handoff (Invariant 2): the snapshot carries operational METADATA only
(no corpus content), round-trips through the file, and the monitor's chat closure reaches the core
inbox and back over the existing handoff — proving the edge surface couples to the core ONLY via the
filesystem, never by importing it.
"""

import json
from pathlib import Path

from core.attestation.attestor import StoreAttestor
from core.attestation.store import AttestationStore
from core.dreams_view import DreamsView
from core.interface import CoreInbox
from core.ops_view import OpsView
from core.stores.derived import DREAM, DerivedStore
from edge.interface.channel import GatewayChannel
from edge.interface.protocol import InboundMessage
from ops.ledger import ProposalLedger
from ops.lifecycle.snapshot import build_status, write_status


def test_snapshot_is_metadata_not_corpus(tmp_path):
    att = AttestationStore(Path(":memory:"))
    StoreAttestor(att).emit(agent_role="ambassador", action="read", input_hashes=["d1"])
    derived = DerivedStore(Path(":memory:"))
    derived.add(kind=DREAM, summary="SECRET-NOTE-BODY recurring theme", subjects=["s1"])
    ops = OpsView.over(att, ProposalLedger(Path(":memory:")))
    dreams = DreamsView.over(derived)

    data = build_status(ops_view=ops, dreams_view=dreams, queue_depth=3, mem_available_gb=9.5)
    assert data["activity"]["actions_logged"] == 1
    assert data["patterns"]["dreams"] == 1
    assert data["queue_depth"] == 3 and data["health"]["memory_available_gb"] == 9.5
    # only the COUNT of dreams crosses — never the dream's text (no corpus leak over the network)
    assert "SECRET-NOTE-BODY" not in json.dumps(data)

    p = tmp_path / "monitor" / "status.json"
    write_status(p, data)                                    # atomic write under a fresh dir
    assert json.loads(p.read_text(encoding="utf-8"))["queue_depth"] == 3


def test_chat_closure_round_trips_through_the_handoff(tmp_path):
    # Exactly what serve()'s chat closure does: submit to the handoff, the core inbox answers,
    # read the reply back. The edge side imports only edge.* + the handoff — never core stores.
    handoff = tmp_path / "handoff"
    inbox = CoreInbox(handoff=handoff, handler=lambda text: f"echo: {text}")
    channel = GatewayChannel(handoff)

    def chat(text, conversation):
        msg = InboundMessage(text=text, conversation=conversation)
        channel.submit(msg)
        inbox.process_once()                                 # palace drives this via the supervisor
        resp = channel.await_response(msg.id, timeout_s=2.0)
        return resp.text if resp is not None else "(timeout)"

    assert chat("hello", "default") == "echo: hello"
