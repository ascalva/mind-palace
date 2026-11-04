#!/usr/bin/env python
"""The Ambassador's MCP server on stdio — spawned by a harness (OpenCode), never a listener.

    uv run --project ~/mind-palace python scripts/palace_mcp.py
    uv run --project ~/mind-palace python scripts/palace_mcp.py --manifest > edge/palace_tools.json

Seals the core first (Invariant 1), then speaks MCP over stdin/stdout; see
`agents/ambassador/mcp.py` for the tools and the scoping they enforce. `--manifest` prints the
Open WebUI bridge's tool list instead (`agents.ambassador.handoff.web_manifest`): regenerate the
committed file whenever the tool table changes.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))  # repo root on path
os.chdir(ROOT)  # config and data paths resolve against the repo root

from core.sealing import seal  # noqa: E402


def main() -> None:
    if "--manifest" in sys.argv[1:]:   # a read of the config and the tool table; no store, no seal
        from agents.ambassador.handoff import web_manifest

        print(json.dumps(web_manifest(), ensure_ascii=False, indent=1))
        return
    seal()  # structural egress guard first (Invariant 1); only loopback model servers are reachable
    from agents.ambassador.mcp import serve

    serve()


if __name__ == "__main__":
    main()
