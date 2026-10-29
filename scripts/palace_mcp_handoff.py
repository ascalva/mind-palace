#!/usr/bin/env python
"""The Open WebUI bridge's core responder — answers `edge/mcp_http.py`'s tool calls.

    uv run --project ~/mind-palace python scripts/palace_mcp_handoff.py

Started on demand by the edge (never a listener: it reads and writes the handoff directory only),
it seals the core first (Invariant 1), serves until it has been idle for
`[bridge] responder_idle_exit_s`, and exits. See `agents/ambassador/handoff.py`.
"""

from __future__ import annotations

import os
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))  # repo root on path
os.chdir(ROOT)  # config and data paths resolve against the repo root

from core.sealing import seal  # noqa: E402


def main() -> int:
    seal()  # structural egress guard first (Invariant 1)
    from agents.ambassador.handoff import serve_handoff

    bridge = tomllib.loads((ROOT / "config" / "stack.toml").read_text()).get("bridge", {})
    return serve_handoff(ROOT / bridge.get("handoff_dir", "data/handoff/mcp"),
                         idle_exit_s=float(bridge.get("responder_idle_exit_s", 600)))


if __name__ == "__main__":
    raise SystemExit(main())
