"""The Ambassador's tools over the filesystem handoff — the core side of the Open WebUI bridge.

    uv run python scripts/palace_mcp_handoff.py     # sealed; started on demand by edge/mcp_http.py

Open WebUI (in lmtune's podman stack) reaches the palace only through `edge/mcp_http.py`, a Zone-B
HTTP server that holds no store handle. Each `tools/call` it receives becomes a request file; this
responder — sealed, like every core process (Invariant 1) — answers it with the SAME dispatch the
stdio server uses (`agents.ambassador.mcp.Server`) and writes a response file. The coupling is these
JSON files alone (Invariant 2), mirrored, not imported, by the edge — the `core.interface.CoreInbox`
pattern with a structured payload:

    requests/<id>.json   = {"id", "name", "arguments", "ts"}
    responses/<id>.json  = {"id", "text", "is_error", "ts"}

The web client gets a narrower tool set than OpenCode's: every read, plus capture and the two
syncs — never `dream`/`relate` (long synthesis-model jobs) or `link` (interpreted edges) from a
chat window. `WEB_TOOLS` is enforced HERE; the edge's advertised list is a copy for the client,
not the gate.
One responder runs at a time (`responder.lock`, which is also how the edge sees it is up); it exits
after `idle_exit_s` with no calls, and the edge starts it again on the next one.
"""

from __future__ import annotations

import fcntl
import json
import re
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from agents.ambassador.mcp import INSTRUCTIONS, TOOLS, Server

REQUESTS, RESPONSES, LOCK = "requests", "responses", "responder.lock"

# The web client's tools (owner defaults, 2026-10-29: "be able to see and interact with ouroboros").
WEB_TOOLS = frozenset({
    "search", "neighbors", "hybrid", "history", "related", "reach", "origin", "read", "overview",
    "capture", "sync_dialogue", "sync_notes",
    # the loop's bookkeeping (phase 1): status, and the owner's tasks and reminders
    "status", "task_list", "task_add", "task_update", "remind",
})

_ID = re.compile(r"[0-9a-f]{32}")   # the edge's uuid4().hex; anything else never names a file

# (tool name, arguments) -> (text, is_error)
Call = Callable[[str, dict[str, Any]], tuple[str, bool]]


def web_manifest() -> dict[str, Any]:
    """What the edge serves for `initialize`/`tools/list` — `edge/palace_tools.json` must equal
    this (a test pins it), so the client never sees a tool the responder would refuse."""
    return {
        "instructions": INSTRUCTIONS,
        "tools": [{"name": n, "description": d, "inputSchema": s}
                  for n, d, s, _ in TOOLS if n in WEB_TOOLS],
    }


def _utcnow() -> str:
    return datetime.now(UTC).replace(tzinfo=None).isoformat(timespec="seconds")


def _atomic_write_json(path: Path, obj: dict[str, Any]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)   # rename is atomic; the edge never reads a partial response


def server_call(server: Server | None = None) -> Call:
    """A tool call through the stdio server's own dispatch — same results, same error shape —
    behind the web allowlist."""
    srv = server if server is not None else Server()

    def call(name: str, arguments: dict[str, Any]) -> tuple[str, bool]:
        if name not in WEB_TOOLS:
            return f"{name!r} is not available from Open WebUI", True
        reply = srv.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                            "params": {"name": name, "arguments": arguments}})
        if reply is None or "error" in reply:
            return str(((reply or {}).get("error") or {}).get("message", "no reply")), True
        result = reply["result"]
        text = "".join(str(c.get("text", "")) for c in result.get("content", []))
        return text, bool(result.get("isError"))

    return call


@dataclass
class ToolInbox:
    handoff: Path
    call: Call

    def __post_init__(self) -> None:
        self.requests_dir = self.handoff / REQUESTS
        self.responses_dir = self.handoff / RESPONSES
        self.requests_dir.mkdir(parents=True, exist_ok=True)
        self.responses_dir.mkdir(parents=True, exist_ok=True)

    def process_once(self) -> int:
        """Answer every pending request; return how many. A failed call is an error RESPONSE —
        one bad request never takes the responder down."""
        handled = 0
        for req_file in sorted(self.requests_dir.glob("*.json")):
            try:
                req = json.loads(req_file.read_text(encoding="utf-8"))
                rid, name, arguments = str(req["id"]), str(req["name"]), req.get("arguments") or {}
            except (OSError, json.JSONDecodeError, KeyError, TypeError):
                continue   # partial/foreign file; skip this pass
            if not _ID.fullmatch(rid) or req_file.stem != rid:
                req_file.unlink(missing_ok=True)   # never let a request name the response path
                continue
            try:
                text, is_error = self.call(name, arguments if isinstance(arguments, dict) else {})
            except Exception as e:  # noqa: BLE001 — reported to the caller, not raised
                text, is_error = f"{type(e).__name__}: {e}", True
            _atomic_write_json(self.responses_dir / f"{rid}.json",
                               {"id": rid, "text": text, "is_error": is_error, "ts": _utcnow()})
            req_file.unlink(missing_ok=True)   # consumed
            handled += 1
        return handled

    def run(self, *, idle_exit_s: float, poll_interval: float = 0.1,
            clock: Callable[[], float] = time.monotonic,
            sleep: Callable[[float], None] = time.sleep) -> None:
        """Serve until `idle_exit_s` passes with no request: models and stores are not held for
        a chat window that has gone quiet."""
        last = clock()
        while clock() - last < idle_exit_s:
            if self.process_once():
                last = clock()
            else:
                sleep(poll_interval)


def serve_handoff(handoff: Path, *, idle_exit_s: float, call: Call | None = None) -> int:
    """Run the responder unless one already holds the lock (then return at once: it is serving)."""
    handoff.mkdir(parents=True, exist_ok=True)
    with (handoff / LOCK).open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return 0
        ToolInbox(handoff, call if call is not None else server_call()).run(
            idle_exit_s=idle_exit_s)
    return 0
