"""End-to-end conversations with the Ambassador, the way Open WebUI holds them.

    uv run python eval/ambassador_e2e.py [--think] [--live-writes] [--only NAME ...]

Each scenario is one owner message that does NOT say "use the palace": the model gets the brief
(`agents/ambassador/brief.md`, the same text Open WebUI's model preset carries) and the 12
`palace_*` tools (`edge/palace_tools.json`, named as Open WebUI names an MCP server's tools), and
must decide on its own whether local context is needed, which strata to ask, and what to read.
Every tool call goes through the live bridge on 127.0.0.1:8096 — edge, handoff, sealed responder —
so this measures the real path minus Open WebUI's relay (proven separately from its container).

Write tools (capture, sync_dialogue, sync_notes) are answered with a dry-run stub unless
`--live-writes`: whether the model DECIDES to write is the measurement, not the write. Thinking is
off by default (minutes per turn otherwise). The transcript prints the owner's note text: it is a
local console report, never a committed artifact.
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
CHAT = "http://127.0.0.1:8080/v1/chat/completions"
BRIDGE = "http://127.0.0.1:8096/mcp"
WRITES = {"capture", "sync_dialogue", "sync_notes"}
MAX_ROUNDS = 5


@dataclass(frozen=True)
class Scenario:
    name: str
    prompt: str
    expect: str   # "search" | "curated" | "none" | "capture"


SCENARIOS = (
    Scenario("implicit-recall", "I keep coming back to that snake-eating-its-own-tail idea for my "
             "project. What did I originally mean by it?", "search"),
    Scenario("implicit-recent", "What have I been preoccupied with lately?", "search"),
    Scenario("open-problem", "Is Kaplansky's direct finiteness conjecture still open?", "curated"),
    Scenario("general-control", "How many feet are in a mile?", "none"),
    Scenario("remember", "Please remember this: as of today the palace runs on EmbeddingGemma-2 "
             "instead of the Qwen 4B embedder.", "capture"),
)


@dataclass
class Run:
    scenario: Scenario
    calls: list[tuple[str, dict[str, Any], str]] = field(default_factory=list)
    answer: str = ""
    seconds: float = 0.0

    @property
    def verdict(self) -> str:
        names = [c[0] for c in self.calls]
        ok = {
            "search": "search" in names,
            "curated": any(n == "search" and "curated" in (a.get("strata") or [])
                           for n, a, _ in self.calls),
            "none": not names,
            "capture": "capture" in names,
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


def converse(s: Scenario, *, brief: str, tools: list[dict[str, Any]], lm_key: str, br_key: str,
             think: bool, live_writes: bool) -> Run:
    run, t0 = Run(s), time.monotonic()
    messages: list[dict[str, Any]] = [{"role": "system", "content": brief},
                                      {"role": "user", "content": s.prompt}]
    for _ in range(MAX_ROUNDS):
        msg = _post(CHAT, {"model": "qwen3.8-27b", "messages": messages, "tools": tools,
                           "max_tokens": 900,
                           "chat_template_kwargs": {"enable_thinking": think}},
                    lm_key)["choices"][0]["message"]
        messages.append(msg)
        calls = msg.get("tool_calls") or []
        if not calls:
            run.answer = (msg.get("content") or "").strip()
            break
        for c in calls:
            name = c["function"]["name"].removeprefix("palace_")
            args = json.loads(c["function"].get("arguments") or "{}")
            if name in WRITES and not live_writes:
                text = json.dumps({"dry_run": True, "would": name, "arguments": args})
            else:
                res = _post(BRIDGE, {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                     "params": {"name": name, "arguments": args}}, br_key)
                text = res["result"]["content"][0]["text"]
            run.calls.append((name, args, _summary(name, text)))
            messages.append({"role": "tool", "tool_call_id": c["id"], "content": text})
    run.seconds = time.monotonic() - t0
    return run


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--think", action="store_true")
    ap.add_argument("--live-writes", action="store_true")
    ap.add_argument("--only", nargs="*")
    a = ap.parse_args(argv)
    lm_key = Path("~/.config/lmtune/api-key").expanduser().read_text().strip()
    br_key = Path("~/.config/mind-palace/webui-bridge.key").expanduser().read_text().strip()
    brief = (ROOT / "agents" / "ambassador" / "brief.md").read_text(encoding="utf-8")
    manifest = json.loads((ROOT / "edge" / "palace_tools.json").read_text(encoding="utf-8"))
    tools = [{"type": "function", "function": {"name": f"palace_{t['name']}",
                                               "description": t["description"],
                                               "parameters": t["inputSchema"]}}
             for t in manifest["tools"]]
    runs = []
    for s in SCENARIOS:
        if a.only and s.name not in a.only:
            continue
        r = converse(s, brief=brief, tools=tools, lm_key=lm_key, br_key=br_key,
                     think=a.think, live_writes=a.live_writes)
        runs.append(r)
        print(f"\n=== {s.name} [{r.verdict}: expected {s.expect}] {r.seconds:.0f} s")
        print(f"owner: {s.prompt}")
        for name, args, summary in r.calls:
            print(f"  → palace_{name}({json.dumps(args, ensure_ascii=False)})")
            print(f"      {summary}")
        print(f"ambassador: {r.answer[:900]}")
    passed = sum(r.verdict == "PASS" for r in runs)
    print(f"\n{passed}/{len(runs)} scenarios behaved as expected "
          f"({sum(r.seconds for r in runs):.0f} s in all, thinking {'on' if a.think else 'off'})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
