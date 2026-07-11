"""The edge monitor's routing + rendering (Zone B) — testable without binding a socket.

Proves: the dashboard renders metrics from a snapshot (and says "waiting" with none); routes
resolve (dashboard / status.json / health / 404); chat returns the reply, 400s an empty message,
and 502s — without leaking internals — when the core can't be reached.
"""

from typing import Any

from edge.monitor import MonitorApp, render_dashboard

_STATUS: dict[str, Any] = {
    "generated_at": "2026-06-29T10:00:00",
    "run": {"id": 7, "commit": "abc123def456", "dirty": False, "started_at": "2026-06-29T09:00:00"},
    "activity": {"actions_logged": 12, "pending_approvals": 1,
                 "recent": [{"role": "ambassador", "action": "read", "at": "10:00"}]},
    "health": {"drift_within_tolerance": True, "constitution_intact": True,
               "memory_available_gb": 9.5, "flags": []},
    "patterns": {"dreams": 3, "tidy_suggestions": 2},
    "queue_depth": 4,
}


def test_render_waiting_when_no_snapshot():
    assert "Waiting for the first status snapshot" in render_dashboard(None)


def test_render_shows_metrics():
    html = render_dashboard(_STATUS)
    assert "healthy" in html                          # health pill
    assert "abc123def456" in html                     # the pinned commit
    assert "12" in html and "Actions logged" in html
    assert "Talk to it" in html                       # the chat box is present


def test_render_flags_show_a_warning():
    s = dict(_STATUS)
    s["health"] = {**_STATUS["health"], "flags": [
        {"metric": "mem.available_gb", "value": 1.2, "threshold": 2.0, "note": "low memory"}]}
    html = render_dashboard(s)
    assert "Warnings" in html and "low memory" in html


def test_get_routes():
    app = MonitorApp(read_status=lambda: _STATUS, chat=lambda _t, _c: "x")
    assert app.get("/")[0] == 200 and "text/html" in app.get("/")[1]
    code, ctype, _b = app.get("/status.json")
    assert code == 200 and ctype == "application/json"
    assert app.get("/health")[0] == 200
    assert app.get("/nope")[0] == 404


def test_chat_ok_empty_and_unreachable():
    app = MonitorApp(read_status=lambda: None, chat=lambda t, _c: f"echo:{t}")
    code, _ct, body = app.post_chat({"text": "hi"})
    assert code == 200 and b"echo:hi" in body
    assert app.post_chat({"text": "   "})[0] == 400          # empty message rejected

    def boom(_t, _c):
        raise RuntimeError("core down: /vault/secret leaked?")

    code, _ct, body = MonitorApp(read_status=lambda: None, chat=boom).post_chat({"text": "hi"})
    assert code == 502 and b"could not be reached" in body
    assert b"vault" not in body.lower()                       # no internals on the wire
