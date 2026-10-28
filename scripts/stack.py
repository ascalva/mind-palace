#!/usr/bin/env python
"""The Ouroboros stack, one command: `mind-palace stack {up|status|check|down}`.

Declared in `config/stack.toml`; everything is idempotent. `up` installs the embedder as a launchd
LaunchAgent (llama-server, sleeps when idle), installs the OpenCode workflow from
`ops/stack/opencode/` (the palace MCP server, the Ambassador agent, the `palace` skill, the
commands), and runs the palace preflight. `check` proves the chain end to end with a real query
through the MCP server over stdio. Secrets never pass through here: lmtune's key reaches the palace
by file reference in the OpenCode config, and by env var NAME in the palace config.
"""

from __future__ import annotations

import json
import os
import plistlib
import shutil
import subprocess
import sys
import time
import tomllib
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
CFG = tomllib.loads((ROOT / "config" / "stack.toml").read_text())
UID = os.getuid()


def _x(p: str) -> Path:
    return Path(p).expanduser()


def _get(url: str, timeout: float = 3.0) -> dict[str, Any] | None:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            body = r.read()
            return json.loads(body) if body.strip().startswith(b"{") else {"status": r.status}
    except Exception:
        return None


# ── the embedder service ────────────────────────────────────────────────────────────────────────


def _plist() -> dict[str, Any]:
    e = CFG["embedder"]
    log = _x(e["log"])
    return {
        "Label": e["label"],
        "ProgramArguments": [
            e["binary"],
            "-m",
            str(_x(e["model"])),
            "--embedding",
            "--pooling",
            e["pooling"],
            "-c",
            str(e["ctx"]),
            "-np",
            str(e["parallel"]),
            "-b",
            str(e["ctx"]),
            "-ub",
            str(e["ubatch"]),
            "-ngl",
            str(e["gpu_layers"]),
            "-fa",
            "on",
            "--host",
            "127.0.0.1",
            "--port",
            str(e["port"]),
            "--alias",
            e["alias"],
            "--sleep-idle-seconds",
            str(e["sleep_idle_s"]),
        ],
        "RunAtLoad": True,
        "KeepAlive": True,
        "ProcessType": "Background",
        "StandardOutPath": str(log),
        "StandardErrorPath": str(log),
    }


def _agent_path() -> Path:
    return Path.home() / "Library" / "LaunchAgents" / f"{CFG['embedder']['label']}.plist"


def _loaded() -> bool:
    return (
        subprocess.run(
            ["launchctl", "print", f"gui/{UID}/{CFG['embedder']['label']}"], capture_output=True
        ).returncode
        == 0
    )


def embedder_up() -> str:
    e = CFG["embedder"]
    if not _x(e["model"]).exists():
        return f"✗ embedder model missing: {e['model']}"
    _x(e["log"]).parent.mkdir(parents=True, exist_ok=True)
    path, want = _agent_path(), plistlib.dumps(_plist())
    changed = not path.exists() or path.read_bytes() != want
    if changed:
        path.write_bytes(want)
    if changed and _loaded():
        subprocess.run(["launchctl", "bootout", f"gui/{UID}/{e['label']}"], capture_output=True)
        time.sleep(1)
    if not _loaded():
        r = subprocess.run(
            ["launchctl", "bootstrap", f"gui/{UID}", str(path)], capture_output=True, text=True
        )
        if r.returncode != 0:
            return f"✗ embedder: launchctl bootstrap failed: {r.stderr.strip()}"
    for _ in range(60):
        if _get(f"http://127.0.0.1:{e['port']}/health") is not None:
            how = "reinstalled" if changed else "unchanged"
            return f"✓ embedder: {e['alias']} on :{e['port']} ({how})"
        time.sleep(1)
    return f"✗ embedder: no /health on :{e['port']} after 60 s — see {e['log']}"


def embedder_down() -> str:
    if _loaded():
        subprocess.run(
            ["launchctl", "bootout", f"gui/{UID}/{CFG['embedder']['label']}"], capture_output=True
        )
        return "✓ embedder stopped (the LaunchAgent stays installed; `stack up` starts it again)"
    return "· embedder was not running"


# ── OpenCode ────────────────────────────────────────────────────────────────────────────────────


def opencode_up() -> str:
    src, dst = ROOT / "ops" / "stack" / "opencode", _x(CFG["opencode"]["config_dir"])
    copied = 0
    for f in src.rglob("*"):
        if f.is_file():
            target = dst / f.relative_to(src)
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists() or target.read_bytes() != f.read_bytes():
                shutil.copy2(f, target)
                copied += 1
    return f"✓ opencode: agent, skill, commands, palace MCP ({copied} file(s) updated)"


# ── checks ──────────────────────────────────────────────────────────────────────────────────────


def chat_status() -> str:
    """lmtune's server keeps everything but /health behind its key, so liveness comes from /health
    and the asleep/loaded state from lmtune's own status line — this script never reads the key."""
    if _get(f"{CFG['chat']['url']}/health") is None:
        return f"✗ chat (lmtune): nothing at {CFG['chat']['url']} — `lmtune serve install`"
    state = ""
    if shutil.which("lmtune"):
        out = subprocess.run(
            ["lmtune", "serve", "status"], capture_output=True, text=True, timeout=30
        )
        state = next(
            (
                ln.split("·", 1)[1].split("·")[0].strip()
                for ln in out.stdout.splitlines()
                if ln.startswith("server")
            ),
            "",
        )
    return f"✓ chat (lmtune): {state or 'up'} at {CFG['chat']['url']}"


def embedder_status() -> str:
    e = CFG["embedder"]
    props = _get(f"http://127.0.0.1:{e['port']}/props")
    if props is None:
        agent = "agent loaded" if _loaded() else "agent not loaded"
        return f"✗ embedder: not answering on :{e['port']} ({agent})"
    return f"✓ embedder: {'asleep' if props.get('is_sleeping') else 'loaded'} on :{e['port']}"


def mcp_roundtrip(query: str = "what have I been thinking about?") -> str:
    msgs = [
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": "2025-06-18"},
        },
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "overview", "arguments": {}},
        },
        {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {"name": "search", "arguments": {"query": query, "k": 3}},
        },
    ]
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "palace_mcp.py")],
        input="\n".join(json.dumps(m) for m in msgs) + "\n",
        capture_output=True,
        text=True,
        timeout=300,
        cwd=ROOT,
    )
    replies = {r["id"]: r for r in map(json.loads, proc.stdout.splitlines())}
    if 4 not in replies or replies[4]["result"].get("isError"):
        return f"✗ palace MCP: {proc.stderr.strip()[-300:] or replies}"
    tools = len(replies[2]["result"]["tools"])
    ov = json.loads(replies[3]["result"]["content"][0]["text"])
    hits = json.loads(replies[4]["result"]["content"][0]["text"])["hits"]
    return (
        f"✓ palace MCP: {tools} tools; {ov['vector_rows']} vectors, "
        f"{sum(ov['catalog_by_provenance'].values())} notes+turns, "
        f"{sum(ov['relation_edges'].values())} relation edges; "
        f"a real search returned {len(hits)} hit(s)"
    )


def palace_preflight() -> str:
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "palace.py"), "status"],
        capture_output=True,
        text=True,
        timeout=180,
        cwd=ROOT,
    )
    bad = [ln.strip() for ln in r.stdout.splitlines() if ln.strip().startswith("✗")]
    return "✓ palace preflight" if not bad else "✗ palace preflight: " + "; ".join(bad)


def main(argv: list[str]) -> int:
    cmd = argv[0] if argv else "status"
    if cmd == "up":
        lines = [chat_status(), embedder_up(), opencode_up(), palace_preflight()]
    elif cmd == "down":
        lines = [embedder_down()]
    elif cmd == "status":
        lines = [chat_status(), embedder_status(), palace_preflight()]
    elif cmd == "check":
        lines = [chat_status(), embedder_status(), mcp_roundtrip()]
    else:
        print(__doc__)
        return 2
    print("\n".join(lines))
    return 0 if all(not ln.startswith("✗") for ln in lines) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
