#!/usr/bin/env python
"""The Ambassador's MCP server on stdio — spawned by a harness (OpenCode), never a listener.

    uv run --project ~/mind-palace python scripts/palace_mcp.py

Seals the core first (Invariant 1), then speaks MCP over stdin/stdout; see
`agents/ambassador/mcp.py` for the tools and the scoping they enforce.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))  # repo root on path
os.chdir(ROOT)  # config and data paths resolve against the repo root

from core.sealing import seal  # noqa: E402


def main() -> None:
    seal()  # structural egress guard first (Invariant 1); only loopback model servers are reachable
    from agents.ambassador.mcp import serve

    serve()


if __name__ == "__main__":
    main()
