#!/usr/bin/env python
"""The palace's MCP server on stdio — spawned by a harness (OpenCode), never a listener.

    uv run --project ~/mind-palace python scripts/palace_mcp.py
    uv run --project ~/mind-palace python scripts/palace_mcp.py --role guest
    uv run --project ~/mind-palace python scripts/palace_mcp.py --manifest > edge/palace_tools.json

Seals the core first (Invariant 1), then speaks MCP over stdin/stdout, stdout kept for the
protocol (`protocol_stream`); see `agents/ambassador/mcp.py` for the tools and the scoping they
enforce. With no `--role`, or `--role ambassador`, it is the Ambassador's surface; `--role guest`
is an external agent's, read-only under the `GUEST` grant (`query` and `overview`,
dn-guest-principal). `--manifest` prints the Open WebUI bridge's tool list instead
(`agents.ambassador.handoff.web_manifest`): regenerate the committed file whenever the
Ambassador's tool table changes.
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


def role_of(args: list[str]) -> str:
    """`--role <name>` or `--role=<name>`; the Ambassador's when absent, '' when the flag has no
    value (refused below)."""
    for i, a in enumerate(args):
        if a == "--role":
            return args[i + 1] if i + 1 < len(args) else ""
        if a.startswith("--role="):
            return a.removeprefix("--role=")
    return "ambassador"


def main() -> None:
    if "--manifest" in sys.argv[1:]:   # a read of the config and the tool table; no store, no seal
        from agents.ambassador.handoff import web_manifest

        print(json.dumps(web_manifest(), ensure_ascii=False, indent=1))
        return
    role = role_of(sys.argv[1:])
    seal()  # structural egress guard first (Invariant 1); only loopback model servers are reachable
    from agents.ambassador.mcp import ROLES, Server, protocol_stream, serve

    if role not in ROLES:
        sys.exit(f"palace_mcp: --role is one of {', '.join(ROLES)}")
    # the replies go to a copy of stdout, and stdout itself to stderr: what anything else in the
    # process writes there, a library's C code or a child process, cannot reach the client
    stream = protocol_stream()
    if role == "ambassador":
        serve(stdout=stream)
    else:
        serve(stdout=stream, server=Server(role))


if __name__ == "__main__":
    main()
