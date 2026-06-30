"""The edge monitor (Zone B) — a small dashboard + chat surface over Tailscale.

A SEPARATE process palace supervises. Network-facing, so by Invariant 2 it cannot share the
sealed core process: it renders a core-emitted status snapshot (a read-only file) and relays chat
over the existing filesystem handoff to the core inbox. It NEVER imports core and never reads a
store. See `server.py`.
"""

from __future__ import annotations

from edge.monitor.server import MonitorApp, make_handler, render_dashboard, serve

__all__ = ["MonitorApp", "make_handler", "render_dashboard", "serve"]
