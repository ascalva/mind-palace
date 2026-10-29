"""The Open WebUI bridge's edge: MCP over streamable HTTP on 127.0.0.1, in front of the palace.

    uv run python -m edge.mcp_http       # what the `com.mind-palace.webui-bridge` LaunchAgent runs

Open WebUI runs in lmtune's podman stack; lmtune's relay forwards it to this port and nothing else
(`[[stack.tool_servers]]` in lmtune's stack.toml). This process is Zone B: it holds NO store
handle and imports nothing from the private zones (Invariant 2; a test pins its imports). It
answers `initialize` and `tools/list` itself — from `edge/palace_tools.json`, which a test pins to
the core's `agents.ambassador.handoff.web_manifest()` — and turns each `tools/call` into a request
file in the handoff directory. The sealed responder (`scripts/palace_mcp_handoff.py`, started here
on demand, exits when idle) writes the answer back. A call the palace does not answer in time is
an error, never a made-up result.

Every request must carry the bearer key (a 0600 file), a known Host header (DNS-rebinding defense;
the relay passes Open WebUI's through unchanged) and no Origin (no browser may call it) — the same
gate as lmtune's media worker. Responses are single JSON bodies (the streamable-HTTP spec allows
that); there is no server-initiated stream. Logs name the tool and the outcome, never arguments.
"""

from __future__ import annotations

import argparse
import fcntl
import hmac
import json
import os
import secrets
import subprocess
import sys
import threading
import time
import tomllib
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = Path(__file__).resolve().parent / "palace_tools.json"
PROTOCOL_VERSIONS = ("2025-06-18", "2025-03-26", "2024-11-05")  # newest first
SERVER_INFO = {"name": "mind-palace", "version": "0.1.0"}
MAX_BODY = 1_000_000
# The handoff's wire shape, mirrored (not imported) from agents/ambassador/handoff.py.
REQUESTS, RESPONSES, LOCK = "requests", "responses", "responder.lock"
STALE_RESPONSE_S = 3600   # an answer nobody waited for (the call timed out) is swept after this
NOTICES_MAX_AGE_S = 3 * 3600   # older means the heartbeat stopped: show none rather than stale
NOTICES_HEADER = "Pending for the owner (raise briefly, once; then only if asked):"
NOTICE_LINE_MAX = 240   # one line each, never a wall of text in the system prompt
RESPAWN_COOLDOWN_S = 15.0  # a responder takes a few seconds to import; don't stack spawns


@dataclass(frozen=True)
class BridgeConfig:
    port: int = 8096
    key_file: Path = Path("~/.config/mind-palace/webui-bridge.key").expanduser()
    extra_hosts: tuple[str, ...] = ()
    handoff_dir: Path = ROOT / "data" / "handoff" / "mcp"
    call_timeout_s: float = 300.0
    log: Path = Path("~/Library/Logs/mind-palace/webui-bridge.log").expanduser()

    @property
    def hosts(self) -> frozenset[str]:
        """Host headers answered: loopback, plus the relay's address Open WebUI sends."""
        own = (f"127.0.0.1:{self.port}", f"localhost:{self.port}", f"[::1]:{self.port}")
        return frozenset(h.lower() for h in (*own, *self.extra_hosts))


def load_config(path: Path = ROOT / "config" / "stack.toml") -> BridgeConfig:
    """`[bridge]` of config/stack.toml, read directly (the config loader is core-side)."""
    raw = tomllib.loads(path.read_text()).get("bridge", {}) if path.exists() else {}
    d = BridgeConfig()
    return BridgeConfig(
        port=int(raw.get("port", d.port)),
        key_file=Path(raw.get("key_file", str(d.key_file))).expanduser(),
        extra_hosts=tuple(raw.get("extra_hosts", ())),
        handoff_dir=ROOT / raw.get("handoff_dir", "data/handoff/mcp"),
        call_timeout_s=float(raw.get("call_timeout_s", d.call_timeout_s)),
        log=Path(raw.get("log", str(d.log))).expanduser(),
    )


# ── the key ─────────────────────────────────────────────────────────────────────────────────────


def ensure_key(path: Path) -> str:
    """Create the bearer key once (0600; its directory 0700 when created here). lmtune reads the
    same file into Open WebUI's tool-server secret; neither side ever logs it."""
    if not path.exists():
        if not path.parent.exists():
            path.parent.mkdir(mode=0o700, parents=True)
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as f:
            f.write(secrets.token_urlsafe(32))
    return read_key(path)


def read_key(path: Path) -> str:
    mode = path.stat().st_mode & 0o777
    if mode & 0o077:
        raise PermissionError(f"{path} is readable by others ({oct(mode)}); chmod 600 it")
    key = path.read_text().strip()
    if len(key) < 32:
        raise ValueError(f"{path} holds no usable key")
    return key


# ── the handoff (edge half) ─────────────────────────────────────────────────────────────────────


def _utcnow() -> str:
    return datetime.now(UTC).replace(tzinfo=None).isoformat(timespec="seconds")


def _atomic_write_json(path: Path, obj: dict[str, Any]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)   # the responder never reads a partial request


def today_line(now: datetime | None = None) -> str:
    """The date, for a model with no clock ("remind me tomorrow" needs one). Day resolution on
    purpose (a cache-stable prefix): the instructions open the system prompt, so a line that
    changed every minute would void llama-server's prompt cache for the tool schemas after it."""
    d = now or datetime.now()
    return f"\n\nToday is {d:%A}, {d:%Y-%m-%d}."


class Handoff:
    """Drop a request, make sure a responder is up, wait for its answer."""

    def __init__(self, root: Path, timeout_s: float, start_responder: Callable[[], None], *,
                 poll_s: float = 0.05) -> None:
        self.root, self.timeout_s, self.start_responder, self.poll_s = (
            root, timeout_s, start_responder, poll_s)
        self.requests, self.responses = root / REQUESTS, root / RESPONSES
        self.requests.mkdir(parents=True, exist_ok=True)
        self.responses.mkdir(parents=True, exist_ok=True)
        self._spawn = threading.Lock()
        self._last_spawn = float("-inf")

    def responder_running(self) -> bool:
        """The responder holds `responder.lock` while it serves."""
        with (self.root / LOCK).open("a") as f:
            try:
                fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                return True
            fcntl.flock(f, fcntl.LOCK_UN)
            return False

    def ensure_responder(self) -> None:
        with self._spawn:
            now = time.monotonic()
            if now - self._last_spawn >= RESPAWN_COOLDOWN_S and not self.responder_running():
                self._last_spawn = now
                self.start_responder()

    def call(self, name: str, arguments: dict[str, Any]) -> tuple[str, bool]:
        self._sweep()
        rid = uuid.uuid4().hex
        req, resp = self.requests / f"{rid}.json", self.responses / f"{rid}.json"
        _atomic_write_json(req, {"id": rid, "name": name, "arguments": arguments, "ts": _utcnow()})
        deadline, next_check = time.monotonic() + self.timeout_s, 0.0
        while time.monotonic() < deadline:
            if resp.exists():
                try:
                    out = json.loads(resp.read_text(encoding="utf-8"))
                finally:
                    resp.unlink(missing_ok=True)
                return str(out.get("text", "")), bool(out.get("is_error"))
            # still waiting in the queue: a responder may have gone idle between our write and its
            # last scan, so look again every couple of seconds
            if time.monotonic() >= next_check and req.exists():
                self.ensure_responder()
                next_check = time.monotonic() + 2.0
            time.sleep(self.poll_s)
        req.unlink(missing_ok=True)   # never picked up: withdraw it
        return f"the palace did not answer within {self.timeout_s:.0f} s", True

    def notices(self) -> str:
        """The lines the core published for the model (`notices.json`, written by the heartbeat
        and the task tools), as an instructions suffix — empty when there are none, or when
        they are too old to trust. Open WebUI re-initializes per request, so they stay current."""
        try:
            doc = json.loads((self.root / "notices.json").read_text(encoding="utf-8"))
            age = time.time() - datetime.fromisoformat(doc["generated_at"]).timestamp()
            raw = doc["lines"]
        except (OSError, ValueError, KeyError, TypeError):
            return ""
        # the trust boundary checks shape, not just syntax: a list, from the recent past
        if not isinstance(raw, list) or not raw or not -60 <= age <= NOTICES_MAX_AGE_S:
            return ""
        lines = [" ".join(str(x).split())[:NOTICE_LINE_MAX] for x in raw[:10]]
        return "\n\n" + NOTICES_HEADER + "\n" + "\n".join(f"- {line}" for line in lines)

    def _sweep(self) -> None:
        cutoff = time.time() - STALE_RESPONSE_S
        for f in self.responses.glob("*.json"):
            try:
                if f.stat().st_mtime < cutoff:
                    f.unlink(missing_ok=True)
            except OSError:
                pass


def spawn_responder(cfg: BridgeConfig) -> Callable[[], None]:
    """Start the sealed responder as its own process (same interpreter, the project's venv),
    detached, logging next to the bridge."""

    def start() -> None:
        cfg.log.parent.mkdir(parents=True, exist_ok=True)
        with cfg.log.open("a") as log:
            subprocess.Popen(
                [sys.executable, str(ROOT / "scripts" / "palace_mcp_handoff.py")],
                cwd=ROOT, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                start_new_session=True)

    return start


# ── MCP ─────────────────────────────────────────────────────────────────────────────────────────


class RpcError(Exception):
    def __init__(self, code: int, message: str) -> None:
        super().__init__(message)
        self.code, self.message = code, message


def _error(mid: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": mid, "error": {"code": code, "message": message}}


class Mcp:
    def __init__(self, manifest: dict[str, Any], handoff: Handoff,
                 log: Callable[[str], None]) -> None:
        self.manifest, self.handoff, self.log = manifest, handoff, log
        self.names = frozenset(t["name"] for t in manifest["tools"])

    def handle(self, m: Any) -> dict[str, Any] | None:
        if (not isinstance(m, dict) or m.get("jsonrpc") != "2.0"
                or not isinstance(m.get("method"), str)):
            return _error(m.get("id") if isinstance(m, dict) else None, -32600, "invalid request")
        notification, mid = "id" not in m, m.get("id")
        try:
            result = self._dispatch(m["method"], m.get("params") or {})
        except RpcError as e:
            return None if notification else _error(mid, e.code, e.message)
        return None if notification else {"jsonrpc": "2.0", "id": mid, "result": result}

    def _dispatch(self, method: str, params: Any) -> dict[str, Any]:
        if not isinstance(params, dict):
            raise RpcError(-32602, "params must be an object")
        if method == "initialize":
            asked = params.get("protocolVersion")
            return {
                "protocolVersion": asked if asked in PROTOCOL_VERSIONS else PROTOCOL_VERSIONS[0],
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": SERVER_INFO,
                "instructions": (self.manifest["instructions"] + today_line()
                                 + self.handoff.notices()),
            }
        if method == "ping" or method.startswith("notifications/"):
            return {}
        if method == "tools/list":
            return {"tools": self.manifest["tools"]}
        if method == "tools/call":
            name, args = params.get("name"), params.get("arguments") or {}
            if not isinstance(name, str) or not isinstance(args, dict):
                raise RpcError(-32602, "tools/call needs a name and an arguments object")
            if name not in self.names:
                raise RpcError(-32602, f"unknown tool {name!r}")
            t0 = time.monotonic()
            text, err = self.handoff.call(name, args)
            self.log(f"{name} {'error' if err else 'ok'} {time.monotonic() - t0:.1f}s")
            return {"content": [{"type": "text", "text": text}], "isError": err}
        raise RpcError(-32601, f"method not found: {method}")


# ── HTTP ────────────────────────────────────────────────────────────────────────────────────────


class BridgeServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, addr: tuple[str, int], mcp: Mcp, key: str, hosts: frozenset[str]) -> None:
        self.mcp, self.key, self.hosts = mcp, key, hosts
        super().__init__(addr, McpHandler)

    def server_bind(self) -> None:
        """Skip HTTPServer's reverse-DNS lookup of the bind address."""
        self.socket.bind(self.server_address)
        self.server_address = self.socket.getsockname()[:2]
        self.server_name = str(self.server_address[0])
        self.server_port = int(self.server_address[1])


class McpHandler(BaseHTTPRequestHandler):
    server: BridgeServer
    server_version = "mind-palace-bridge"
    sys_version = ""

    def log_message(self, format: str, *args: Any) -> None:
        """Quiet: tool calls are logged by Mcp, without arguments (they are the owner's words)."""

    def _send(self, code: int, body: bytes = b"", ctype: str = "application/json") -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        if code == 401:
            self.send_header("WWW-Authenticate", 'Bearer realm="mind-palace"')
        self.end_headers()
        if body and self.command != "HEAD":
            self.wfile.write(body)

    def _gate(self) -> bool:
        if (self.headers.get("Host") or "").lower() not in self.server.hosts:
            self._send(421, b"unknown host\n", "text/plain")
            return False
        if self.headers.get("Origin") is not None:   # browsers send it; Open WebUI's backend not
            self._send(403, b"browser requests are not accepted\n", "text/plain")
            return False
        auth = self.headers.get("Authorization") or ""
        if not hmac.compare_digest(auth.encode(), f"Bearer {self.server.key}".encode()):
            self._send(401, b"missing or wrong key\n", "text/plain")
            return False
        if self.path.split("?", 1)[0] != "/mcp":
            self._send(404, b"not found\n", "text/plain")
            return False
        return True

    def do_POST(self) -> None:
        if not self._gate():
            return
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            n = -1
        if not 0 < n <= MAX_BODY:
            self._send(413 if n > MAX_BODY else 400,
                       json.dumps(_error(None, -32600, "bad body size")).encode())
            return
        try:
            msg = json.loads(self.rfile.read(n))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._send(400, json.dumps(_error(None, -32700, "parse error")).encode())
            return
        reply = self.server.mcp.handle(msg)
        if reply is None:
            self._send(202)
        else:
            self._send(200, json.dumps(reply, ensure_ascii=False).encode())

    def do_GET(self) -> None:
        if self._gate():   # no server-initiated stream: the spec allows 405 here
            self._send(405, b"", "text/plain")

    do_DELETE = do_GET


def _log(line: str) -> None:
    print(f"{datetime.now().isoformat(timespec='seconds')} {line}", flush=True)


def build(cfg: BridgeConfig, *, start_responder: Callable[[], None] | None = None,
          log: Callable[[str], None] = _log) -> BridgeServer:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    handoff = Handoff(cfg.handoff_dir, cfg.call_timeout_s,
                      start_responder if start_responder is not None else spawn_responder(cfg))
    return BridgeServer(("127.0.0.1", cfg.port), Mcp(manifest, handoff, log),
                        read_key(cfg.key_file), cfg.hosts)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="The palace's MCP-over-HTTP edge for Open WebUI.")
    ap.add_argument("--config", type=Path, default=ROOT / "config" / "stack.toml")
    cfg = load_config(ap.parse_args(argv).config)
    httpd = build(cfg)
    _log(f"mind-palace bridge: http://127.0.0.1:{cfg.port}/mcp · "
         f"{len(httpd.mcp.names)} tools · handoff {cfg.handoff_dir}")
    try:
        httpd.serve_forever(poll_interval=1.0)
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
