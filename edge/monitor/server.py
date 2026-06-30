"""The edge monitor HTTP server (Zone B, Invariant 2).

Two surfaces, both behind the tailnet:
  * dashboard  — `GET /` renders the core-emitted status snapshot (health, activity shape, queue
                 depth, memory, dream counts). `GET /status.json` is the raw snapshot for the
                 page's auto-refresh. Read-only — it opens a file, never a store.
  * chat       — `POST /chat {text, conversation}` writes to the interface handoff and awaits the
                 core's reply (the Ambassador answers inside the walls). The handoff is the ONLY
                 coupling to the core; no import crosses the boundary.

Routing is split from the socket (`MonitorApp` returns `(code, content_type, body)` tuples) so it
is unit-testable without binding a port. `serve()` wires the file reader + the handoff chat closure
and runs a stdlib `HTTPServer`. The process is deliberately NOT sealed — it is Zone B and must bind
a (Tailscale) socket; the sealing guard protects the core, not this one.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from socketserver import TCPServer

from edge.monitor.page import CHAT, PAGE

Response = tuple[int, str, bytes]


class _Server(HTTPServer):
    """HTTPServer without the reverse-DNS lookup. Stock `HTTPServer.server_bind` calls
    `socket.getfqdn(host)` to set `server_name`, which can BLOCK for tens of seconds on a host
    with no working reverse DNS (observed: 35s) — stalling startup. We never use `server_name`,
    so bind plainly and skip the lookup."""

    allow_reuse_address = True

    def server_bind(self) -> None:
        TCPServer.server_bind(self)
        host, port = self.server_address[:2]
        self.server_name, self.server_port = host, port


@dataclass
class MonitorApp:
    """Pure request routing over two injected seams: `read_status` (the snapshot file) and `chat`
    (the handoff round-trip). No sockets here — testable directly."""

    read_status: Callable[[], dict | None]
    chat: Callable[[str, str], str]

    def get(self, path: str) -> Response:
        if path in ("/", "/index.html"):
            html = render_dashboard(self.read_status())
            return (200, "text/html; charset=utf-8", html.encode("utf-8"))
        if path == "/status.json":
            return (200, "application/json", json.dumps(self.read_status() or {}).encode("utf-8"))
        if path == "/health":                       # liveness probe (palace / curl)
            return (200, "text/plain; charset=utf-8", b"ok")
        return (404, "text/plain; charset=utf-8", b"not found")

    def post_chat(self, payload: dict | None) -> Response:
        text = (payload or {}).get("text", "").strip()
        conversation = (payload or {}).get("conversation", "default")
        if not text:
            return (400, "application/json", b'{"error": "empty message"}')
        try:
            reply = self.chat(text, conversation)
        except Exception:                           # never leak internals to the wire
            return (502, "application/json", b'{"error": "the core could not be reached"}')
        return (200, "application/json", json.dumps({"reply": reply}).encode("utf-8"))


def make_handler(app: MonitorApp) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def _send(self, resp: Response) -> None:
            code, ctype, body = resp
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:                   # noqa: N802 (BaseHTTPRequestHandler API)
            self._send(app.get(self.path))

        def do_POST(self) -> None:                  # noqa: N802
            if self.path != "/chat":
                self._send((404, "text/plain; charset=utf-8", b"not found"))
                return
            length = int(self.headers.get("Content-Length", 0) or 0)
            raw = self.rfile.read(length) if length else b"{}"
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                self._send((400, "application/json", b'{"error": "bad json"}'))
                return
            self._send(app.post_chat(payload))

        def log_message(self, *_a) -> None:         # quiet — palace captures stdout
            pass

    return Handler


def serve(host: str, port: int, *, status_path: str | Path, handoff: str | Path,
          request_timeout_s: float = 30.0) -> None:
    """Wire the file reader + handoff chat closure and run the server. Imports the handoff channel
    lazily so the routing/render units stay import-light for tests."""
    from edge.interface.channel import GatewayChannel
    from edge.interface.protocol import InboundMessage

    status_path = Path(status_path)
    channel = GatewayChannel(Path(handoff))

    def read_status() -> dict | None:
        try:
            return json.loads(status_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None                             # no snapshot yet / mid-write → render "waiting"

    def chat(text: str, conversation: str) -> str:
        msg = InboundMessage(text=text, conversation=conversation)
        channel.submit(msg)                         # → handoff (the core inbox drains it)
        resp = channel.await_response(msg.id, timeout_s=request_timeout_s)
        return resp.text if resp is not None else "(no reply in time — the core may be busy.)"

    app = MonitorApp(read_status=read_status, chat=chat)
    httpd = _Server((host, port), make_handler(app))
    print(f"monitor: serving on http://{host}:{port}  (snapshot={status_path})", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


# --- rendering -------------------------------------------------------------------------------
def _health_pill(health: dict) -> tuple[str, str]:
    """(label, css-class) from the snapshot's health block — green/amber/red."""
    if health.get("constitution_intact") is False:
        return ("core integrity check failed", "bad")
    if health.get("flags"):
        return ("running, with resource warnings", "warn")
    within = health.get("drift_within_tolerance")
    if within is False:
        return ("drifting from baseline", "warn")
    if within is None:
        return ("running (health not yet measured)", "ok")
    return ("healthy", "ok")


_ACTION_WORDS = {
    "ingest_note": "took in a note", "capture": "saved something you told it",
    "read": "looked something up", "propose": "lined up some work",
    "mint_token": "was granted a scoped credential",
    "dream_pass": "looked for patterns", "curate_finding": "tidied notes",
}


def render_dashboard(status: dict | None) -> str:
    """Render the snapshot as a self-contained HTML page (inline CSS/JS, no external deps). Shows
    only metadata the snapshot carries — never corpus content."""
    if not status:
        body = ('<p class="muted">Waiting for the first status snapshot… '
                'is <code>palace</code> running?</p>')
        return PAGE.replace("{{BODY}}", body).replace("{{GEN}}", "—")

    health = status.get("health", {})
    label, cls = _health_pill(health)
    run = status.get("run") or {}
    act = status.get("activity", {})
    pat = status.get("patterns", {})
    mem = health.get("memory_available_gb")

    cards = [
        _card("Status", f'<span class="pill {cls}">{label}</span>'),
        _card("Running on", f'{run.get("commit", "—")}{" (dirty)" if run.get("dirty") else ""}'
              f'<div class="sub">since {run.get("started_at", "—")}</div>'),
        _card("Actions logged", str(act.get("actions_logged", 0))),
        _card("Queue depth", str(status.get("queue_depth", 0))),
        _card("Awaiting approval", str(act.get("pending_approvals", 0))),
        _card("Patterns noticed", f'{pat.get("dreams", 0)} '
              f'<span class="sub">+ {pat.get("tidy_suggestions", 0)} tidy-ups</span>'),
        _card("Memory free", "—" if mem is None else f"{mem:.1f} GB"),
    ]
    recent = act.get("recent", [])
    rows = "".join(
        f'<li><span class="role">{r.get("role", "?")}</span> '
        f'{_ACTION_WORDS.get(r.get("action", ""), r.get("action", "did something"))} '
        f'<span class="sub">{r.get("at", "")}</span></li>'
        for r in recent[:8]
    ) or '<li class="muted">nothing recorded yet</li>'
    flags = health.get("flags", [])
    flag_html = ""
    if flags:
        items = "".join(f'<li>⚠ {f.get("note", "")} '
                        f'<span class="sub">({f.get("metric")}={f.get("value")} '
                        f'&lt; {f.get("threshold")})</span></li>' for f in flags)
        flag_html = f'<div class="panel warnbox"><h2>Warnings</h2><ul>{items}</ul></div>'

    body = (
        f'<div class="cards">{"".join(cards)}</div>'
        f'{flag_html}'
        f'<div class="panel"><h2>Recent activity</h2><ul class="activity">{rows}</ul></div>'
        f'{CHAT}'
    )
    return PAGE.replace("{{BODY}}", body).replace("{{GEN}}", status.get("generated_at", "—"))


def _card(label: str, value: str) -> str:
    return (f'<div class="card"><div class="label">{label}</div>'
            f'<div class="value">{value}</div></div>')
