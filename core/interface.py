"""Core side of the interface handoff (BUILD-SPEC §6, §12; Invariant 2).

The sealed core never speaks to a messaging service. Instead the networked gateway (Zone B)
drops a **sanitized request** into the handoff directory; this inbox — running inside the
sealed core — reads it, dispatches the query to a core handler (the librarian / a minted
agent), and writes the answer back to the handoff directory. The gateway relays it onward.

The ONLY coupling to the outside is these JSON files on disk: no network, no adapter import,
no shared memory (the structural form of "network and private data never share a component").
The wire format is a small JSON object, mirrored — *not imported* — by the gateway side:
    requests/<id>.json   = {"id", "conversation", "text", "ts"}
    responses/<id>.json  = {"id", "conversation", "text", "ts"}
"""

from __future__ import annotations

import json
import os
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from config.loader import Config

# query text -> answer text. Wires to the librarian / factory; injected so the inbox stays
# model-agnostic and testable.
Handler = Callable[[str], str]

REQUESTS = "requests"
RESPONSES = "responses"


def _utcnow() -> str:
    return datetime.now(UTC).replace(tzinfo=None).isoformat(timespec="seconds")


def _atomic_write_json(path: Path, obj: dict[str, Any]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj), encoding="utf-8")
    tmp.replace(path)   # rename is atomic; the gateway never reads a partial response


@dataclass
class CoreInbox:
    handoff: Path
    handler: Handler

    def __post_init__(self) -> None:
        self.requests_dir = self.handoff / REQUESTS
        self.responses_dir = self.handoff / RESPONSES
        self.requests_dir.mkdir(parents=True, exist_ok=True)
        self.responses_dir.mkdir(parents=True, exist_ok=True)

    def process_once(self) -> int:
        """Process every pending request; return how many were handled. A handler error
        becomes an error response rather than crashing the inbox."""
        handled = 0
        for req_file in sorted(self.requests_dir.glob("*.json")):
            try:
                req = json.loads(req_file.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue   # partial/foreign file; skip this pass
            try:
                answer = self.handler(req["text"])
            except Exception as e:   # never let one bad request take down the inbox
                answer = f"[error] {e!r}"
            _atomic_write_json(self.responses_dir / f"{req['id']}.json", {
                "id": req["id"],
                "conversation": req.get("conversation", "default"),
                "text": answer,
                "ts": _utcnow(),
            })
            req_file.unlink(missing_ok=True)   # consumed
            handled += 1
        return handled

    def run(self, *, poll_interval: float = 0.5, max_cycles: int | None = None) -> None:
        """Serve the handoff in a loop. The scheduler (Phase 3) can also drive this as a job."""
        cycles = 0
        while max_cycles is None or cycles < max_cycles:
            self.process_once()
            cycles += 1
            time.sleep(poll_interval)


def build_core_inbox(config: Config | None = None) -> CoreInbox:
    """Wire the inbox to the **Ambassador** — the conversational front door (Track B). The
    Ambassador reasons about intent and routes to retrieve / explain / status / capture inline,
    delegating heavy work; conversations are captured as `authored-dialogue`.

    This base wiring has no DELEGATION queue handle (the core never imports the scheduler — that
    would invert the layering), so TASK here still attests + narrates effort but enqueues nothing.
    The full delegating inbox (task → gate → queue, with completed-result surfacing) is
    `scheduler.interface.build_conversation_runtime`, used by the CLI and the scheduled path.

    `agents.ambassador` is imported lazily (function-level): it transitively reaches the pure
    `scheduler.budget` budgeter, and a top-level import would invert core's layering — the
    Ambassador is core-side but is assembled, not imported, at module load (no network either)."""
    from agents.ambassador import build_ambassador
    from config.loader import get_config

    cfg = config or get_config()
    ambassador = build_ambassador(cfg)
    os.makedirs(cfg.interface.handoff_dir, exist_ok=True)
    return CoreInbox(handoff=cfg.interface.handoff_dir, handler=ambassador.handler)
