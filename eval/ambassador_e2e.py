"""End-to-end conversations with the Ambassador, the way Open WebUI holds them.

    uv run python eval/ambassador_e2e.py [--think] [--live-writes] [--only NAME ...]

Each scenario is one owner message that does NOT say "use the palace": the model gets the live
bridge's MCP instructions (the brief, today's date and any notices: exactly what Open WebUI
appends to the system message) and the `palace_*` tools (`edge/palace_tools.json`, named as Open
WebUI names an MCP server's tools), and must decide on its own whether local context is needed,
which strata to ask, and what to read. `--brief PATH` swaps in another brief (plus the date).
Every tool call goes through the live bridge on 127.0.0.1:8096 — edge, handoff, sealed responder —
so this measures the real path minus Open WebUI's relay (proven separately from its container).

Write tools (capture, the syncs, the task tools) are answered with a success-shaped stub unless
`--live-writes`: whether the model DECIDES to write, and with what arguments, is the measurement,
not the write. A bridge error reaches the model as the tool's error text, as in Open WebUI.
Thinking is off by default (minutes per turn otherwise). The transcript prints the owner's note
text: it is a local console report, never a committed artifact.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
CHAT = "http://127.0.0.1:8080/v1/chat/completions"
BRIDGE = "http://127.0.0.1:8096/mcp"
WRITES = {"capture", "sync_dialogue", "sync_notes", "remind", "task_add", "task_update"}
MAX_ROUNDS = 5


@dataclass(frozen=True)
class Scenario:
    name: str
    prompt: str
    expect: str   # "search" | "curated" | "none" | "capture" | "status" | "remind" | "tasks"


SCENARIOS = (
    Scenario("implicit-recall", "I keep coming back to that snake-eating-its-own-tail idea for my "
             "project. What did I originally mean by it?", "search"),
    Scenario("implicit-recent", "What have I been preoccupied with lately?", "search"),
    Scenario("open-problem", "Is Kaplansky's direct finiteness conjecture still open?", "curated"),
    Scenario("dialogue-recall", "What did we talk about regarding my grad capstone?", "search"),
    Scenario("open-problem-2", "Has anyone settled whether Hadwiger's conjecture is true?",
             "curated"),
    Scenario("general-control", "How many feet are in a mile?", "none"),
    Scenario("creative-control", "Write a haiku about autumn rain.", "none"),
    Scenario("remember", "Please remember this: as of today the palace runs on EmbeddingGemma-2 "
             "instead of the Qwen 4B embedder.", "capture"),
    Scenario("status", "How's the paper import going?", "status"),
    Scenario("remind", "Remind me tomorrow at 9am to call the dentist.", "remind"),
    Scenario("tasks", "What's on my plate right now?", "tasks"),
)


def _tomorrow_at_nine(args: dict[str, Any]) -> bool:
    """The reminder lands at 09:00 tomorrow, however the model wrote the time."""
    from core.stores.tasks import parse_when

    want = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%dT09:00")
    try:
        return parse_when(str(args.get("at", ""))) == want
    except ValueError:
        return False


@dataclass
class Run:
    scenario: Scenario
    calls: list[tuple[str, dict[str, Any], str]] = field(default_factory=list)
    answer: str = ""
    seconds: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0

    @property
    def verdict(self) -> str:
        names = [c[0] for c in self.calls]
        ok = {
            "search": "search" in names,
            "curated": any(n == "search" and "curated" in (a.get("strata") or [])
                           for n, a, _ in self.calls),
            "none": not names,
            "capture": "capture" in names,
            "status": "status" in names,
            "remind": any(n == "remind" and _tomorrow_at_nine(a) for n, a, _ in self.calls),
            "tasks": "task_list" in names or "status" in names,
        }[self.scenario.expect]
        return "PASS" if ok else "MISS"


def _post(url: str, body: dict[str, Any], key: str, timeout: float = 900) -> dict[str, Any]:
    req = urllib.request.Request(url, json.dumps(body).encode(),
                                 {"Content-Type": "application/json",
                                  "Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def _summary(name: str, text: str) -> str:
    """A one-line account of a tool result for the transcript."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return text[:120].replace("\n", " ")
    if isinstance(data, dict) and "hits" in data:
        titles = [str(h.get("title", ""))[:60] for h in data["hits"][:3]]
        return f"{len(data['hits'])} hits: " + " | ".join(titles)
    if isinstance(data, dict) and "text" in data:
        return f"{data.get('title', '')[:60]} ({len(str(data['text']))} chars)"
    return text[:120].replace("\n", " ")


def converse(s: Scenario, *, system: str, tools: list[dict[str, Any]], lm_key: str,
             br_key: str, think: bool, live_writes: bool) -> Run:
    run, t0 = Run(s), time.monotonic()
    messages: list[dict[str, Any]] = [{"role": "system", "content": system},
                                      {"role": "user", "content": s.prompt}]
    for _ in range(MAX_ROUNDS):
        reply = _post(CHAT, {"model": "qwen3.8-27b", "messages": messages, "tools": tools,
                             "max_tokens": 900,
                             "chat_template_kwargs": {"enable_thinking": think}}, lm_key)
        usage = reply.get("usage") or {}
        run.prompt_tokens += int(usage.get("prompt_tokens", 0))
        run.completion_tokens += int(usage.get("completion_tokens", 0))
        msg = reply["choices"][0]["message"]
        messages.append(msg)
        calls = msg.get("tool_calls") or []
        if not calls:
            run.answer = (msg.get("content") or "").strip()
            break
        for c in calls:
            name = c["function"]["name"].removeprefix("palace_")
            args = json.loads(c["function"].get("arguments") or "{}")
            if name in WRITES and not live_writes:
                text = json.dumps({"ok": True, "note": "test run: nothing was saved"})
            else:
                res = _post(BRIDGE, {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                     "params": {"name": name, "arguments": args}}, br_key)
                if "result" in res:
                    text = res["result"]["content"][0]["text"]
                else:   # a JSON-RPC error: the model sees it, as Open WebUI would show it
                    text = f"error: {res.get('error', {}).get('message', res)}"
            run.calls.append((name, args, _summary(name, text)))
            messages.append({"role": "tool", "tool_call_id": c["id"], "content": text})
    run.seconds = time.monotonic() - t0
    return run


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--think", action="store_true")
    ap.add_argument("--live-writes", action="store_true")
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--brief", type=Path, help="another brief instead of the live instructions")
    ap.add_argument("--plain-system", action="store_true",
                    help="the brief as the whole system prompt, not Open WebUI's MCP framing")
    a = ap.parse_args(argv)
    lm_key = Path("~/.config/lmtune/api-key").expanduser().read_text().strip()
    br_key = Path("~/.config/mind-palace/webui-bridge.key").expanduser().read_text().strip()
    if a.brief:
        from edge.mcp_http import today_line

        brief = a.brief.read_text(encoding="utf-8").strip() + today_line()
    else:   # what Open WebUI receives at initialize: the brief, the date, any notices
        brief = _post(BRIDGE, {"jsonrpc": "2.0", "id": 0, "method": "initialize",
                               "params": {"protocolVersion": "2025-03-26"}},
                      br_key)["result"]["instructions"]
    # Open WebUI appends an MCP server's instructions to the system message under this header
    # (utils/middleware.py of the pinned image), so the brief reaches the model exactly so.
    header = 'MCP server "palace" instructions:\n'
    system = brief if a.plain_system else header + brief
    manifest = json.loads((ROOT / "edge" / "palace_tools.json").read_text(encoding="utf-8"))
    tools = [{"type": "function", "function": {"name": f"palace_{t['name']}",
                                               "description": t["description"],
                                               "parameters": t["inputSchema"]}}
             for t in manifest["tools"]]
    runs = []
    for s in SCENARIOS:
        if a.only and s.name not in a.only:
            continue
        r = converse(s, system=system, tools=tools, lm_key=lm_key, br_key=br_key,
                     think=a.think, live_writes=a.live_writes)
        runs.append(r)
        print(f"\n=== {s.name} [{r.verdict}: expected {s.expect}] {r.seconds:.0f} s · "
              f"{r.prompt_tokens} prompt + {r.completion_tokens} completion tokens")
        print(f"owner: {s.prompt}")
        for name, args, summary in r.calls:
            print(f"  → palace_{name}({json.dumps(args, ensure_ascii=False)})")
            print(f"      {summary}")
        print(f"ambassador: {r.answer[:900]}")
    passed = sum(r.verdict == "PASS" for r in runs)
    label = a.brief.name if a.brief else "live instructions"
    print(f"\n{label} ({len(brief.split())} words): {passed}/{len(runs)} scenarios "
          f"behaved as expected · {sum(r.seconds for r in runs):.0f} s · "
          f"{sum(len(r.calls) for r in runs)} tool calls · "
          f"{sum(r.prompt_tokens for r in runs)} prompt + "
          f"{sum(r.completion_tokens for r in runs)} completion tokens · "
          f"thinking {'on' if a.think else 'off'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
