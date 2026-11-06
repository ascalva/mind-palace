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

What the inbox keeps of an exchange it keeps in its own record (`core/ingest/inbox.py`,
dn-ingress-language §E13), before it writes the response: the owner's text as the request file
held it and the reply it sends, each in its own field, so the palace's table labels the one
authored and the other observed and no model decides which is which. The responder says only
whether an exchange is kept. A request is the owner's only when its file was written by the
inbox's own account or the handoff directory's owner (the edge's), through one link; another's is
answered and not kept. Its id, which names the response and the record, is the gateway's 32 hex
digits and the file's name, or the request is removed unanswered.
"""

from __future__ import annotations

import json
import os
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from core.ingest.files import read_bounded
from core.ingest.inbox import Exchange
from core.ingest.table import MAX_ITEM_BYTES, REQUEST_ID
from core.kernel.config import Config

# query text -> answer text. Wires to the librarian / factory; injected so the inbox stays
# model-agnostic and testable.
Handler = Callable[[str], str]

REQUESTS = "requests"
RESPONSES = "responses"
MAX_MESSAGE_BYTES = MAX_ITEM_BYTES + (64 << 10)     # a request file: one item's text and its fields


@dataclass(frozen=True)
class Message:
    """A request as the inbox read it: the gateway's id, the conversation, the owner's text, the
    request's time."""

    id: str
    conversation: str
    text: str
    at: str


@dataclass(frozen=True)
class Answer:
    """A reply, and whether the exchange is the owner's to keep (the responder's call: which
    exchanges are kept, never what is in one)."""

    text: str
    keep: bool = False


Responder = Callable[[Message], "str | Answer"]
Keep = Callable[[Exchange], object]


def _utcnow() -> str:
    return datetime.now(UTC).replace(tzinfo=None).isoformat(timespec="seconds")


def _atomic_write_json(path: Path, obj: dict[str, Any]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj), encoding="utf-8")
    tmp.replace(path)   # rename is atomic; the gateway never reads a partial response


def _say(message: str) -> None:
    print(message, file=sys.stderr)


@dataclass
class CoreInbox:
    """The core side of the handoff. `handler` answers a text; `respond` answers a request read
    whole, when the caller needs its id and conversation; `record` keeps an exchange the
    responder keeps (the inbox's record); `writers` are the accounts whose requests are the
    owner's (the inbox's own and the handoff directory's owner when not given)."""

    handoff: Path
    handler: Handler | None = None
    respond: Responder | None = None
    record: Keep | None = None
    writers: frozenset[int] | None = None
    say: Callable[[str], None] = field(default=_say)

    def __post_init__(self) -> None:
        if self.handler is None and self.respond is None:
            raise ValueError("an inbox answers through a handler or a responder")
        self.requests_dir = self.handoff / REQUESTS
        self.responses_dir = self.handoff / RESPONSES
        self.requests_dir.mkdir(parents=True, exist_ok=True)
        self.responses_dir.mkdir(parents=True, exist_ok=True)
        if self.writers is None:
            self.writers = frozenset({os.getuid(), os.lstat(self.handoff).st_uid})

    def process_once(self) -> int:
        """Process every pending request; return how many were handled. A handler error
        becomes an error response rather than crashing the inbox."""
        handled = 0
        for req_file in sorted(self.requests_dir.glob("*.json")):
            rid = req_file.stem
            try:
                data, st = read_bounded(req_file, MAX_MESSAGE_BYTES)
            except ValueError as e:             # not a regular file, or past the cap: say so
                if REQUEST_ID.fullmatch(rid):
                    self._respond(rid, "default", f"[error] the message was not read: {e}")
                req_file.unlink(missing_ok=True)
                handled += 1
                continue
            except OSError:
                continue                        # a link, or gone: skip this pass
            try:
                req = json.loads(data.decode("utf-8"))
            except ValueError:
                continue                        # partial/foreign file; skip this pass
            if not isinstance(req, dict) or req.get("id") != rid or not REQUEST_ID.fullmatch(rid):
                # the id names the response and the record: never a path, never another's
                self.say(f"inbox: {req_file.name} removed unanswered: its id is not its name")
                req_file.unlink(missing_ok=True)
                continue
            conversation = str(req.get("conversation") or "default")
            text = req.get("text")
            if not isinstance(text, str):
                self._respond(rid, conversation, "[error] the request has no text")
                req_file.unlink(missing_ok=True)
                handled += 1
                continue
            msg = Message(rid, conversation, text, str(req.get("ts") or ""))
            try:
                if self.respond is not None:
                    answer: str | Answer = self.respond(msg)
                else:
                    assert self.handler is not None
                    answer = self.handler(msg.text)
            except Exception as e:              # never let one bad request take down the inbox
                answer = f"[error] {e!r}"
            reply = answer.text if isinstance(answer, Answer) else answer
            if isinstance(answer, Answer) and answer.keep:
                reply = self._keep(msg, reply, st)
            self._respond(rid, msg.conversation, reply)
            req_file.unlink(missing_ok=True)   # consumed
            handled += 1
        return handled

    def _keep(self, msg: Message, reply: str, st: os.stat_result) -> str:
        """Keep an exchange in the inbox's record, before the response is written: a crash after
        it leaves the request to be answered again and the same record written again. A request
        another account wrote is not the owner's and is not kept. A record that cannot be written
        is said in the reply, never lost in silence."""
        assert self.writers is not None
        if self.record is None:
            return reply
        if st.st_uid not in self.writers or st.st_nlink != 1:
            self.say(f"inbox: request {msg.id} was written by uid {st.st_uid} through "
                     f"{st.st_nlink} link(s), not by the owner's interface; it is not kept")
            return reply
        try:
            self.record(Exchange(msg.id, msg.conversation, msg.text, reply, msg.at))
        except (OSError, ValueError) as e:
            self.say(f"inbox: request {msg.id} could not be kept ({type(e).__name__}: {e})")
            return f"{reply}\n\n(This message was not kept: {e}.)"
        return reply

    def _respond(self, rid: str, conversation: str, text: str) -> None:
        _atomic_write_json(self.responses_dir / f"{rid}.json", {
            "id": rid,
            "conversation": conversation,
            "text": text,
            "ts": _utcnow(),
        })

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
    delegating heavy work; the exchanges it keeps go to the inbox's record, which the inbox's
    capture lands as dialogue (dn-ingress-language §E13).

    This base wiring has no DELEGATION queue handle (the core never imports the scheduler — that
    would invert the layering), so TASK here still attests + narrates effort but enqueues nothing.
    The full delegating inbox (task → gate → queue, with completed-result surfacing) is
    `scheduler.interface.build_conversation_runtime`, used by the CLI and the scheduled path.

    `agents.ambassador` is imported lazily (function-level): it transitively reaches the pure
    `scheduler.budget` budgeter, and a top-level import would invert core's layering — the
    Ambassador is core-side but is assembled, not imported, at module load (no network either)."""
    from agents.ambassador import build_ambassador
    from core.ingest.inbox import Record
    from core.kernel.config import get_config

    cfg = config or get_config()
    ambassador = build_ambassador(cfg)
    os.makedirs(cfg.interface.handoff_dir, exist_ok=True)
    return CoreInbox(handoff=cfg.interface.handoff_dir, respond=ambassador.answer,
                     record=Record.of(cfg).write)
