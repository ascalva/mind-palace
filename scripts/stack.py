#!/usr/bin/env python
"""The Ouroboros stack, one command: `mind-palace stack {up|status|check|restart|down}`.

Declared in `config/stack.toml`; everything is idempotent. `up` installs the embedder as a launchd
LaunchAgent (llama-server, sleeps when idle), the Open WebUI bridge as another (a stdlib HTTP
edge on loopback; its sealed responder starts per use and exits idle) and the heartbeat as a third
(`palace tick` every 15 minutes: plain-code decisions, models only on need), installs the OpenCode
workflow from `ops/stack/opencode/` (the palace MCP server, the Ambassador agent, the `palace`
skill, the commands), and runs the palace preflight. `check` proves both chains end to end with a
real query: the MCP server over stdio, and the bridge over HTTP with its key. Secrets never pass
through here: lmtune's key reaches the palace by file reference in the OpenCode config, and by env
var NAME in the palace config; the bridge's key is a 0600 file this script creates but never prints.
"""

from __future__ import annotations

import json
import os
import plistlib
import shutil
import signal
import subprocess
import sys
import time
import tomllib
import urllib.error
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


def embedder_argv() -> list[str]:
    """llama-server's argv, read from config/stack.toml at every (re)start — the plist below never
    names a model, so switching embedders is a config edit plus `stack restart`."""
    e = CFG["embedder"]
    return [
        e["binary"], "-m", str(_x(e["model"])), "--embedding", "--pooling", e["pooling"],
        "-c", str(e["ctx"]), "-np", str(e["parallel"]),
        "-b", str(e["ctx"]), "-ub", str(e["ubatch"]),
        "-ngl", str(e["gpu_layers"]), "-fa", "on", "--host", "127.0.0.1", "--port", str(e["port"]),
        "--cors-origins", e.get("cors_origins", "localhost"),
        "--alias", e["alias"], "--sleep-idle-seconds", str(e["sleep_idle_s"]),
    ]  # fmt: skip


def _plist() -> dict[str, Any]:
    """Stable across model switches: launchd runs `stack serve-embedder`, which reads the config and
    execs llama-server — so the plist (and with it the persistence approval) never changes."""
    e = CFG["embedder"]
    log = _x(e["log"])
    uv = shutil.which("uv") or "/opt/homebrew/bin/uv"
    return {
        "Label": e["label"],
        "ProgramArguments": [uv, "run", "--quiet", "--directory", str(ROOT), "python",
                             str(ROOT / "scripts" / "stack.py"), "serve-embedder"],
        "RunAtLoad": True,
        "KeepAlive": True,
        "ProcessType": "Background",
        "StandardOutPath": str(log),
        "StandardErrorPath": str(log),
    }


def serve_embedder() -> None:
    """The LaunchAgent's entry point: become llama-server (exec — launchd supervises the server
    itself, and its stop signal reaches it directly)."""
    argv = embedder_argv()
    os.execv(argv[0], argv)


def embedder_restart() -> str:
    """Apply a config/stack.toml change to the installed service: kick it so it re-reads."""
    if not _loaded(CFG["embedder"]["label"]):
        return "✗ embedder: the service is not installed — run `mind-palace stack up`"
    subprocess.run(["launchctl", "kickstart", "-k", f"gui/{UID}/{CFG['embedder']['label']}"],
                   capture_output=True)
    port = CFG["embedder"]["port"]
    for _ in range(60):
        if _get(f"http://127.0.0.1:{port}/health") is not None:
            return f"✓ embedder restarted: {CFG['embedder']['alias']} on :{port}"
        time.sleep(1)
    return f"✗ embedder: no /health on :{port} after restart — see {CFG['embedder']['log']}"


def _agent_path(label: str) -> Path:
    return Path.home() / "Library" / "LaunchAgents" / f"{label}.plist"


def _loaded(label: str) -> bool:
    return (
        subprocess.run(["launchctl", "print", f"gui/{UID}/{label}"], capture_output=True).returncode
        == 0
    )


def _install(label: str, plist: dict[str, Any]) -> tuple[str, str | None]:
    """Write the plist if it changed and (re)bootstrap it: ("reinstalled"|"unchanged", error)."""
    path, want = _agent_path(label), plistlib.dumps(plist)
    changed = not path.exists() or path.read_bytes() != want
    if changed:
        path.write_bytes(want)
    if changed and _loaded(label):
        subprocess.run(["launchctl", "bootout", f"gui/{UID}/{label}"], capture_output=True)
        time.sleep(1)
    if not _loaded(label):
        r = subprocess.run(
            ["launchctl", "bootstrap", f"gui/{UID}", str(path)], capture_output=True, text=True
        )
        if r.returncode != 0:
            return "", f"launchctl bootstrap failed: {r.stderr.strip()}"
    return ("reinstalled" if changed else "unchanged"), None


def embedder_up() -> str:
    e = CFG["embedder"]
    if not _x(e["model"]).exists():
        return f"✗ embedder model missing: {e['model']}"
    _x(e["log"]).parent.mkdir(parents=True, exist_ok=True)
    how, err = _install(e["label"], _plist())
    if err:
        return f"✗ embedder: {err}"
    for _ in range(60):
        if _get(f"http://127.0.0.1:{e['port']}/health") is not None:
            return f"✓ embedder: {e['alias']} on :{e['port']} ({how})"
        time.sleep(1)
    return f"✗ embedder: no /health on :{e['port']} after 60 s — see {e['log']}"


def embedder_down() -> str:
    if _loaded(CFG["embedder"]["label"]):
        subprocess.run(
            ["launchctl", "bootout", f"gui/{UID}/{CFG['embedder']['label']}"], capture_output=True
        )
        return "✓ embedder stopped (the LaunchAgent stays installed; `stack up` starts it again)"
    return "· embedder was not running"


# ── the Open WebUI bridge ───────────────────────────────────────────────────────────────────────


def _bridge_plist() -> dict[str, Any]:
    b = CFG["bridge"]
    log = _x(b["log"])
    uv = shutil.which("uv") or "/opt/homebrew/bin/uv"
    return {
        "Label": b["label"],
        "ProgramArguments": [uv, "run", "--quiet", "--directory", str(ROOT), "python", "-m",
                             "edge.mcp_http"],
        # the responder's `sync_dialogue` reads Open WebUI's chats through podman (Homebrew)
        "EnvironmentVariables": {"PATH": "/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"},
        "RunAtLoad": True,
        "KeepAlive": True,
        "ProcessType": "Background",
        "StandardOutPath": str(log),
        "StandardErrorPath": str(log),
    }


def _bridge_post(msg: dict[str, Any], *, key: str | None,
                 timeout: float = 10.0) -> tuple[int, dict[str, Any] | None]:
    """One MCP message to the bridge over HTTP: (status, JSON reply or None)."""
    req = urllib.request.Request(
        f"http://127.0.0.1:{CFG['bridge']['port']}/mcp", json.dumps(msg).encode(),
        {"Content-Type": "application/json", "Accept": "application/json, text/event-stream",
         **({"Authorization": f"Bearer {key}"} if key else {})})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read()
            return r.status, (json.loads(body) if body else None)
    except urllib.error.HTTPError as e:
        return e.code, None
    except OSError:
        return 0, None


def _bridge_key() -> str:
    sys.path.insert(0, str(ROOT))
    from edge.mcp_http import ensure_key

    return ensure_key(_x(CFG["bridge"]["key_file"]))


def _hand_started_bridges(port: int) -> list[int]:
    """Bridges started by hand (`python -m edge.mcp_http`, e.g. while testing) that hold the port
    the service needs; nothing else on the port is ever touched."""
    r = subprocess.run(["lsof", "-nP", f"-iTCP:{port}", "-sTCP:LISTEN", "-t"],
                       capture_output=True, text=True)
    out = []
    for pid in {int(p) for p in r.stdout.split()}:
        cmd = subprocess.run(["ps", "-o", "command=", "-p", str(pid)], capture_output=True,
                             text=True).stdout
        if "edge.mcp_http" in cmd:
            out.append(pid)
    return out


def bridge_up() -> str:
    b = CFG["bridge"]
    _bridge_key()   # created once, 0600; lmtune reads the same file into Open WebUI's secret
    _x(b["log"]).parent.mkdir(parents=True, exist_ok=True)
    if not _loaded(b["label"]):   # first install: a hand-started bridge yields the port
        for pid in _hand_started_bridges(b["port"]):
            os.kill(pid, signal.SIGTERM)
    how, err = _install(b["label"], _bridge_plist())
    if err:
        return f"✗ bridge: {err}"
    ping = {"jsonrpc": "2.0", "id": 1, "method": "ping"}
    for _ in range(60):
        if _bridge_post(ping, key=None, timeout=2.0)[0] == 401:   # answering, and gated
            return f"✓ bridge: MCP for Open WebUI on 127.0.0.1:{b['port']}/mcp ({how})"
        time.sleep(1)
    return f"✗ bridge: no answer on :{b['port']} after 60 s — see {b['log']}"


def bridge_down() -> str:
    if _loaded(CFG["bridge"]["label"]):
        subprocess.run(["launchctl", "bootout", f"gui/{UID}/{CFG['bridge']['label']}"],
                       capture_output=True)
        return "✓ bridge stopped (the LaunchAgent stays installed; `stack up` starts it again)"
    return "· bridge was not running"


def bridge_status() -> str:
    b = CFG["bridge"]
    code, _ = _bridge_post({"jsonrpc": "2.0", "id": 1, "method": "ping"}, key=None, timeout=2.0)
    if code != 401:
        agent = "agent loaded" if _loaded(b["label"]) else "agent not installed"
        return f"✗ bridge: not answering on :{b['port']} ({agent})"
    return f"✓ bridge: answering on :{b['port']}, key required"


def bridge_roundtrip(query: str = "what have I been thinking about?") -> str:
    """Through the edge, the handoff and the sealed responder (started on demand) — the path
    Open WebUI's tool calls take, minus the relay."""
    key = _bridge_key()
    code, init = _bridge_post({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                               "params": {"protocolVersion": "2025-06-18"}}, key=key)
    if code != 200 or not init:
        return f"✗ bridge: initialize answered {code or 'nothing'} — is it up? (`stack up`)"
    _, listed = _bridge_post({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}, key=key)
    call = {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
            "params": {"name": "search", "arguments": {"query": query, "k": 3}}}
    _, reply = _bridge_post(call, key=key, timeout=float(CFG["bridge"]["call_timeout_s"]) + 10)
    result = (reply or {}).get("result") or {}
    if not result or result.get("isError"):
        return f"✗ bridge: search failed — {str(result or reply)[:300]}"
    hits = json.loads(result["content"][0]["text"])["hits"]
    tools = len(((listed or {}).get("result") or {}).get("tools", []))
    return (f"✓ bridge: {tools} tools over HTTP; a real search through the handoff returned "
            f"{len(hits)} hit(s)")


# ── OpenCode ────────────────────────────────────────────────────────────────────────────────────


# ── the heartbeat ───────────────────────────────────────────────────────────────────────────────


def _tick_plist() -> dict[str, Any]:
    t = CFG["tick"]
    log = _x(t["log"])
    uv = shutil.which("uv") or "/opt/homebrew/bin/uv"
    return {
        "Label": t["label"],
        "ProgramArguments": [uv, "run", "--quiet", "--directory", str(ROOT), "python",
                             "scripts/palace.py", "tick"],
        # pmset and ps live in /usr/bin; podman (the Open WebUI check) in Homebrew
        "EnvironmentVariables": {"PATH": "/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"},
        "StartInterval": int(t["interval_s"]),   # a missed beat (the Mac asleep) runs on wake
        "RunAtLoad": True,
        "ProcessType": "Background",
        "LowPriorityIO": True,
        "StandardOutPath": str(log),
        "StandardErrorPath": str(log),
    }


def tick_up() -> str:
    t = CFG["tick"]
    _x(t["log"]).parent.mkdir(parents=True, exist_ok=True)
    how, err = _install(t["label"], _tick_plist())
    if err:
        return f"✗ heartbeat: {err}"
    return f"✓ heartbeat: `palace tick` every {int(t['interval_s']) // 60} min ({how})"


def tick_down() -> str:
    if _loaded(CFG["tick"]["label"]):
        subprocess.run(["launchctl", "bootout", f"gui/{UID}/{CFG['tick']['label']}"],
                       capture_output=True)
        return "✓ heartbeat stopped (the LaunchAgent stays installed; `stack up` starts it again)"
    return "· heartbeat was not running"


def tick_status() -> str:
    if not _loaded(CFG["tick"]["label"]):
        return "✗ heartbeat: agent not installed (`mind-palace stack up`)"
    try:
        rec = json.loads((ROOT / "data" / "tick.json").read_text())
    except (OSError, ValueError):
        return "· heartbeat: installed, no tick recorded yet"
    said = "; ".join(f"{d['action']} {'yes' if d['go'] else 'no'}" for d in rec["decisions"])
    return f"✓ heartbeat: last tick {rec['at'][:16]} ({rec['took_s']} s): {said}"


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
        agent = "agent loaded" if _loaded(e["label"]) else "agent not loaded"
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
    if cmd == "serve-embedder":           # the LaunchAgent's entry point; never returns
        serve_embedder()
    if cmd == "up":
        lines = [chat_status(), embedder_up(), bridge_up(), tick_up(), opencode_up(),
                 palace_preflight()]
    elif cmd == "restart":
        lines = [embedder_restart()]
    elif cmd == "down":
        lines = [embedder_down(), bridge_down(), tick_down()]
    elif cmd == "status":
        lines = [chat_status(), embedder_status(), bridge_status(), tick_status(),
                 palace_preflight()]
    elif cmd == "check":
        lines = [chat_status(), embedder_status(), mcp_roundtrip(), bridge_roundtrip()]
    else:
        print(__doc__)
        return 2
    print("\n".join(lines))
    return 0 if all(not ln.startswith("✗") for ln in lines) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
