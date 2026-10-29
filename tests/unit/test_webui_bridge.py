"""The Open WebUI bridge (docs/brainstorms/ambassador-open-webui-bridge.md): a Zone-B MCP-over-HTTP
edge that holds no store handle, the filesystem handoff, and the sealed responder behind it.

Proves: the edge imports nothing from the private zones (Invariant 2); its advertised tool list IS
the core's web manifest, which leaves out dream/relate/link; the responder refuses anything outside
WEB_TOOLS and never lets a request name a file; the HTTP gate answers like lmtune's media worker
(Host, Origin, key, path); a tools/call travels edge → request file → responder → response file;
and a palace that does not answer is an error, never a made-up result.
"""

from __future__ import annotations

import ast
import http.client
import json
import threading
import time
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from agents.ambassador.handoff import (
    REQUESTS,
    RESPONSES,
    WEB_TOOLS,
    ToolInbox,
    server_call,
    web_manifest,
)
from agents.ambassador.mcp import TOOLS
from edge import mcp_http

ROOT = Path(__file__).resolve().parents[2]
KEY = "k" * 43
_PRIVATE = frozenset({"core", "ops", "scheduler", "agents", "config"})


# --- the edge is a dumb pipe ------------------------------------------------------------------
def test_the_edge_imports_no_private_zone():
    tree = ast.parse((ROOT / "edge" / "mcp_http.py").read_text(encoding="utf-8"))
    roots = {a.name.split(".", 1)[0] for n in ast.walk(tree) if isinstance(n, ast.Import)
             for a in n.names}
    roots |= {n.module.split(".", 1)[0] for n in ast.walk(tree)
              if isinstance(n, ast.ImportFrom) and n.level == 0 and n.module}
    assert not roots & _PRIVATE, roots & _PRIVATE


def test_the_advertised_tools_are_the_core_web_manifest():
    assert json.loads(mcp_http.MANIFEST.read_text(encoding="utf-8")) == web_manifest()


def test_the_web_tools_leave_out_long_jobs_and_interpretive_writes():
    assert WEB_TOOLS <= {t[0] for t in TOOLS}
    assert {"dream", "relate", "link"}.isdisjoint(WEB_TOOLS)
    assert {"search", "read", "capture", "sync_dialogue", "sync_notes"} <= WEB_TOOLS


# --- the responder ----------------------------------------------------------------------------
class _Server:
    def __init__(self) -> None:
        self.seen: list[dict[str, Any]] = []

    def handle(self, msg: dict[str, Any]) -> dict[str, Any]:
        self.seen.append(msg)
        return {"jsonrpc": "2.0", "id": 1,
                "result": {"content": [{"type": "text", "text": '{"hits": []}'}], "isError": False}}


def test_the_responder_refuses_a_tool_outside_the_web_set():
    srv = _Server()
    text, err = server_call(srv)("dream", {})            # type: ignore[arg-type]
    assert err and "not available" in text
    assert srv.seen == []                                # never reached the dispatch


def test_the_responder_answers_through_the_stdio_servers_dispatch():
    srv = _Server()
    assert server_call(srv)("search", {"query": "x"}) == ('{"hits": []}', False)  # type: ignore[arg-type]
    assert srv.seen[0]["params"] == {"name": "search", "arguments": {"query": "x"}}


def _request(root: Path, rid: str, **body: Any) -> None:
    (root / REQUESTS / f"{rid}.json").write_text(json.dumps({"id": rid, **body}))


def test_the_inbox_answers_and_consumes(tmp_path):
    inbox = ToolInbox(tmp_path, lambda name, args: (f"{name}:{args['q']}", False))
    rid = "a" * 32
    _request(tmp_path, rid, name="search", arguments={"q": 1})
    assert inbox.process_once() == 1
    out = json.loads((tmp_path / RESPONSES / f"{rid}.json").read_text())
    assert (out["text"], out["is_error"]) == ("search:1", False)
    assert not list((tmp_path / REQUESTS).glob("*.json"))


def test_a_request_never_names_the_response_path(tmp_path):
    inbox = ToolInbox(tmp_path, lambda name, args: ("x", False))
    (tmp_path / REQUESTS / "evil.json").write_text(
        json.dumps({"id": "../../evil", "name": "search", "arguments": {}}))
    assert inbox.process_once() == 0
    assert [p.name for p in tmp_path.rglob("*evil*")] == []   # dropped, nothing written


def test_a_failing_call_is_an_error_response(tmp_path):
    def boom(name: str, args: dict[str, Any]) -> tuple[str, bool]:
        raise RuntimeError("store unavailable")

    rid = "b" * 32
    inbox = ToolInbox(tmp_path, boom)
    _request(tmp_path, rid, name="search", arguments={})
    assert inbox.process_once() == 1
    out = json.loads((tmp_path / RESPONSES / f"{rid}.json").read_text())
    assert out["is_error"] and "store unavailable" in out["text"]


# --- the key ----------------------------------------------------------------------------------
def test_the_key_is_made_once_and_private(tmp_path):
    path = tmp_path / "conf" / "bridge.key"
    key = mcp_http.ensure_key(path)
    assert len(key) >= 32 and mcp_http.ensure_key(path) == key
    assert path.stat().st_mode & 0o777 == 0o600
    path.chmod(0o640)
    with pytest.raises(PermissionError):
        mcp_http.read_key(path)


# --- HTTP, end to end through the handoff ------------------------------------------------------
def _serve(tmp_path: Path, *, answer: bool, timeout_s: float = 5.0) -> tuple[Any, threading.Event]:
    key_file = tmp_path / "key"
    key_file.write_text(KEY)
    key_file.chmod(0o600)
    cfg = mcp_http.BridgeConfig(port=0, key_file=key_file, handoff_dir=tmp_path / "handoff",
                                call_timeout_s=timeout_s, log=tmp_path / "log")
    stop, started = threading.Event(), threading.Event()

    def start_responder() -> None:   # stands in for the sealed process: same inbox, fake tools
        if not answer or started.is_set():
            return
        started.set()
        inbox = ToolInbox(cfg.handoff_dir,
                          lambda name, args: (json.dumps({"tool": name, "args": args}), False))

        def loop() -> None:
            while not stop.is_set():
                inbox.process_once()
                stop.wait(0.02)

        threading.Thread(target=loop, daemon=True).start()

    httpd = mcp_http.build(cfg, start_responder=start_responder, log=lambda line: None)
    httpd.hosts = frozenset({f"127.0.0.1:{httpd.server_port}"})   # port 0 → the bound one
    threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.05},
                     daemon=True).start()
    return httpd, stop


@pytest.fixture
def bridge(tmp_path) -> Iterator[Any]:
    httpd, stop = _serve(tmp_path, answer=True)
    yield httpd
    stop.set()
    httpd.shutdown()
    httpd.server_close()


def _post(httpd: Any, msg: Any, *, key: str | None = KEY, host: str | None = None,
          origin: str | None = None, path: str = "/mcp") -> tuple[int, Any, dict[str, str]]:
    conn = http.client.HTTPConnection("127.0.0.1", httpd.server_port, timeout=10)
    headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream",
               "Host": host or f"127.0.0.1:{httpd.server_port}"}
    if key is not None:
        headers["Authorization"] = f"Bearer {key}"
    if origin is not None:
        headers["Origin"] = origin
    conn.request("POST", path, json.dumps(msg), headers)
    r = conn.getresponse()
    body = r.read()
    conn.close()
    reply = json.loads(body) if body and r.getheader("Content-Type") == "application/json" else None
    return r.status, reply, dict(r.getheaders())


_PING = {"jsonrpc": "2.0", "id": 1, "method": "ping"}


def test_the_gate(bridge):
    assert _post(bridge, _PING, host="evil.example:8096")[0] == 421        # DNS rebinding
    assert _post(bridge, _PING, origin="https://evil.example")[0] == 403   # a browser
    status, _, headers = _post(bridge, _PING, key=None)
    assert status == 401 and "Bearer" in headers.get("WWW-Authenticate", "")
    assert _post(bridge, _PING, key="wrong")[0] == 401
    assert _post(bridge, _PING, path="/other")[0] == 404
    assert _post(bridge, _PING)[0] == 200


def test_initialize_and_tools_list_come_from_the_manifest(bridge):
    _, init, _ = _post(bridge, {"jsonrpc": "2.0", "id": 1, "method": "initialize",
                                "params": {"protocolVersion": "2025-03-26"}})
    assert init["result"]["protocolVersion"] == "2025-03-26"
    assert init["result"]["capabilities"] == {"tools": {"listChanged": False}}
    _, listed, _ = _post(bridge, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    assert listed["result"]["tools"] == web_manifest()["tools"]


def test_a_notification_is_accepted_without_a_body(bridge):
    status, reply, _ = _post(bridge, {"jsonrpc": "2.0", "method": "notifications/initialized"})
    assert (status, reply) == (202, None)


def test_a_tool_call_travels_the_handoff(bridge):
    _, reply, _ = _post(bridge, {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                                 "params": {"name": "search", "arguments": {"query": "q"}}})
    result = reply["result"]
    assert result["isError"] is False
    assert json.loads(result["content"][0]["text"]) == {"tool": "search", "args": {"query": "q"}}


def test_a_tool_the_web_client_lacks_is_unknown_at_the_edge(bridge):
    _, reply, _ = _post(bridge, {"jsonrpc": "2.0", "id": 4, "method": "tools/call",
                                 "params": {"name": "dream", "arguments": {}}})
    assert reply["error"]["code"] == -32602


def test_a_silent_palace_is_an_error_never_a_guess(tmp_path):
    httpd, stop = _serve(tmp_path, answer=False, timeout_s=0.5)
    try:
        _, reply, _ = _post(httpd, {"jsonrpc": "2.0", "id": 5, "method": "tools/call",
                                    "params": {"name": "search", "arguments": {"query": "q"}}})
        result = reply["result"]
        assert result["isError"] and "did not answer" in result["content"][0]["text"]
        assert not list((tmp_path / "handoff" / REQUESTS).glob("*.json"))   # withdrawn
    finally:
        stop.set()
        httpd.shutdown()
        httpd.server_close()


# --- the instructions: the brief, then the date, then the notices -----------------------------
def _notices(root: Path, lines: list[str], *, age_s: float = 0.0) -> None:
    root.mkdir(parents=True, exist_ok=True)
    at = datetime.fromtimestamp(time.time() - age_s).isoformat()
    (root / "notices.json").write_text(json.dumps({"generated_at": at, "lines": lines}))


def test_notices_reach_the_instructions_only_while_fresh(tmp_path):
    h = mcp_http.Handoff(tmp_path, 5.0, lambda: None)
    assert h.notices() == ""                                     # none yet
    _notices(tmp_path, ["#1 reminder due 2026-10-29T09:00: call the dentist"])
    assert mcp_http.NOTICES_HEADER in h.notices()
    assert h.notices().endswith("- #1 reminder due 2026-10-29T09:00: call the dentist")
    _notices(tmp_path, ["old"], age_s=mcp_http.NOTICES_MAX_AGE_S + 60)
    assert h.notices() == ""                                     # the heartbeat stopped: none
    _notices(tmp_path, [f"line {n}" for n in range(25)])
    assert h.notices().count("\n- ") == 10                       # capped
    now = datetime.now().isoformat()
    for junk in ("", "{", "[]", '{"lines": ["x"]}', '{"generated_at": "never", "lines": ["x"]}',
                 json.dumps({"generated_at": now, "lines": "a string, not a list"}),
                 json.dumps({"generated_at": "2099-01-01T00:00:00", "lines": ["forged"]})):
        (tmp_path / "notices.json").write_text(junk)
        assert h.notices() == "", junk
    _notices(tmp_path, ["a\nmulti-line   " + "x" * 1000])
    (line,) = h.notices().splitlines()[3:]
    assert line.startswith("- a multi-line x") and len(line) == 2 + mcp_http.NOTICE_LINE_MAX


def test_the_date_line_changes_once_a_day():
    a = mcp_http.today_line(datetime(2026, 10, 29, 0, 1))
    assert a == "\n\nToday is Thursday, 2026-10-29."
    assert mcp_http.today_line(datetime(2026, 10, 29, 23, 59)) == a   # a cache-stable prefix
    assert mcp_http.today_line(datetime(2026, 10, 30, 0, 0)) != a


def test_initialize_serves_the_brief_then_the_date_then_the_notices(bridge, tmp_path):
    _notices(tmp_path / "handoff", ["#2 task due 2026-10-29T10:00: file taxes"])
    _, init, _ = _post(bridge, {"jsonrpc": "2.0", "id": 1, "method": "initialize",
                                "params": {"protocolVersion": "2025-03-26"}})
    text = init["result"]["instructions"]
    assert text.startswith(web_manifest()["instructions"])
    assert text.index("Today is") < text.index("file taxes")
