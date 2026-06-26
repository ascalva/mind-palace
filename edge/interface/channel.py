"""Gateway side of the core handoff (BUILD-SPEC §6, §12; Invariant 2).

The gateway writes a request into the shared handoff directory and polls for the core's
response — the ONLY way the networked edge reaches the sealed core. No imports cross the
boundary; the wire format (mirrored in `core.interface`) is:
    requests/<id>.json   = {"id", "conversation", "text", "ts"}
    responses/<id>.json  = {"id", "conversation", "text", "ts"}
The gateway never reads the private vault — it only moves messages.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path

from edge.interface.protocol import InboundMessage, OutboundMessage

REQUESTS = "requests"
RESPONSES = "responses"


def _atomic_write_json(path: Path, obj: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj), encoding="utf-8")
    tmp.replace(path)   # the core never reads a partial request


@dataclass
class GatewayChannel:
    handoff: Path

    def __post_init__(self) -> None:
        self.requests_dir = self.handoff / REQUESTS
        self.responses_dir = self.handoff / RESPONSES
        self.requests_dir.mkdir(parents=True, exist_ok=True)
        self.responses_dir.mkdir(parents=True, exist_ok=True)

    def submit(self, message: InboundMessage) -> str:
        _atomic_write_json(self.requests_dir / f"{message.id}.json", message.to_request())
        return message.id

    def read_response(self, request_id: str) -> OutboundMessage | None:
        path = self.responses_dir / f"{request_id}.json"
        if not path.exists():
            return None
        try:
            obj = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        path.unlink(missing_ok=True)
        return OutboundMessage.from_response(obj)

    def await_response(self, request_id: str, *, timeout_s: float = 30.0,
                       poll_interval: float = 0.1) -> OutboundMessage | None:
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            resp = self.read_response(request_id)
            if resp is not None:
                return resp
            time.sleep(poll_interval)
        return None
