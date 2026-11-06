"""The Ambassador's MCP surface — the palace as a tool server for the local model.

    uv run --project ~/mind-palace python scripts/palace_mcp.py      # MCP over stdio

A harness (OpenCode, or anything that speaks MCP over stdio) spawns this process; it has no
listener and no socket of its own, and it seals itself (Invariant 1) before it opens a store. It is
the Ambassador's client of the core: every read is ONE command, `query` — a sentence of the query
algebra (`core.sentence`, dn-query-sentence-algebra) compiled under the Ambassador's grant, widened
by the hypothetical overlay the owner granted on 2026-11-04 — so an ill-scoped read is refused in
code, not by the prompt, and the plan rides with every answer; writes are only the ones the
grant's W_Σ allows — dialogue capture (provenance fixed by role, never by the text) and
interpreted relation edges. Long operations (dream, relate, sync) wake models and run on demand.

Protocol: JSON-RPC 2.0, one message per line (MCP stdio transport). `initialize`, `ping`,
`tools/list`, `tools/call`; anything printed by an operation is captured and returned as the tool's
text, so stdout carries protocol messages only. Diagnostics go to stderr.
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
import traceback
from collections.abc import Callable
from pathlib import Path
from typing import Any

PROTOCOL_VERSION = "2025-06-18"
SERVER_INFO = {"name": "mind-palace", "version": "0.1.0"}
# The brief (agents/ambassador/brief.md) IS the server's MCP `instructions`: a harness that honours
# them — Open WebUI appends them to the system message whenever the palace tools are on — loads it
# on every chat with no prompt to paste. One text for every client and for eval/ambassador_e2e.py.
INSTRUCTIONS = (Path(__file__).with_name("brief.md")).read_text(encoding="utf-8").strip()

class Ambassador:
    """Tool implementations. Stores and the launcher open lazily, once per process."""

    def __init__(self) -> None:
        from core.query import QueryEngine

        self.engine = QueryEngine()
        self._launcher: Any = None

    @property
    def launcher(self) -> Any:
        if self._launcher is None:
            from ops.lifecycle.launcher import build_launcher

            self._launcher = build_launcher()
        return self._launcher

    # the one read ------------------------------------------------------------------------------
    def query(self, sentence: str, trace: bool = False) -> dict[str, Any]:
        """A sentence of the query algebra (dn-query-sentence-algebra) under `sentence_grant()` —
        the Ambassador's grant with the overlay the owner granted: the plan rides with the answer,
        a refusal names the word that would fix it, a hypothetical answers as a `Hyp` beside the
        actual answer, and `trace` shows the work. Logged as `mcp`/`ambassador` (the query log,
        the sensor)."""
        from core.sentence.surface import ask_logged, sentence_grant

        return ask_logged(sentence, sentence_grant(), surface="mcp", role="ambassador",
                          engine=self.engine, trace=bool(trace)).to_dict()

    def overview(self) -> dict[str, Any]:
        from collections import Counter

        from core.query import AMBASSADOR
        from core.stores.catalog import VaultCatalog

        cfg = self.engine.config
        catalog = Counter(
            e.provenance for e in VaultCatalog(cfg.paths.vault_catalog).active_entries()
        )
        edges = Counter(e.rel_type for e in self.engine._get("edges").all())
        planes = [
            {
                "strata": sorted(s.sigma.strata),
                "edges": sorted(s.edges.fibers),
                "clock": s.time.clock.value,
                "write": bool(s.authority.store_write),
            }
            for s in AMBASSADOR.scopes
        ]
        return {
            "catalog_by_provenance": dict(catalog),
            "vector_rows": self.engine._get("vectors").count(),
            "relation_edges": dict(edges),
            "versions": self.engine._get("versions").count(),
            "your_grant": planes,
        }

    # writes and on-demand work -----------------------------------------------------------------
    def _run(self, fn: Callable[[], int]) -> dict[str, Any]:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = fn()
        return {"ok": code == 0, "output": buf.getvalue().strip()}

    # The write tools, as aliases of the one command `query` (dn-ingress-language §E8): each calls a
    # library script of the ingress and writes the request the daemon's one writer lands; the
    # receipt rides back as the answer's hit. Nothing is written from this process.
    def _do(self, sentence: str) -> dict[str, Any]:
        return self.query(sentence)

    def sync_dialogue(self) -> dict[str, Any]:
        return self._do("do sync_dialogue")

    def sync_notes(self) -> dict[str, Any]:
        return self._do("do sync_vault")

    def dream(self) -> dict[str, Any]:
        return self._do("do dream")

    def relate(self, max_pairs: int = 12) -> dict[str, Any]:
        from core.ingest.table import JOBS

        most = JOBS["relate"].args["pairs"]
        if not 0 <= int(max_pairs) <= most:
            raise ValueError(f"max_pairs is from 0 to {most}")   # refused here, not at landing
        return self._do(f"do relate(pairs: {int(max_pairs)})")

    def capture(self, text: str, conversation: str = "captures") -> dict[str, Any]:
        """Remember text the MODEL relays (a summary, a decision it was asked to remember) as an
        `observed` dialogue turn, by the ingress, under
        `dialogue/ingress/ambassador/<conversation>/`. Never authored: only the owner's own turns,
        synced from their chat app, carry authored provenance. A conversation is a name, not a
        path."""
        from core.sentence.script import quote

        return self._do(f"do capture(text: {quote(text)}, conversation: {quote(conversation)})")

    def link(self, note_a: str, note_b: str, relation: str) -> dict[str, Any]:
        """Propose a signed relation between two notes, stored as `interpreted`, by the ingress."""
        from core.relations import RELATIONS

        if relation not in RELATIONS:
            raise ValueError(f"relation must be one of {list(RELATIONS)}")
        from core.sentence.script import quote

        return self._do(f"do link(a: {quote(note_a)}, b: {quote(note_b)}, "
                        f"relation: {quote(relation)})")

    # the loop's bookkeeping (docs/brainstorms/ambassador-agent-loop.md, phase 1) ----------------
    def status(self) -> dict[str, Any]:
        """The ecosystem at a glance, read-only and local: jobs (ledger and live processes),
        models, services, store sizes, and what is open or due."""
        from core.stores.tasks import OPEN, now_local, open_task_store
        from ops.heartbeat import chat_key, last_tick, load_policy, model_state, palace_processes

        cfg = self.engine.config
        policy = load_policy()
        store = open_task_store(cfg)
        try:
            running = [j.brief() for j in store.select(kinds=("job",), statuses=("running",))]
            recent = [j.brief() for j in store.finished(limit=20) if j.kind == "job"][:5]
            open_n = len(store.select(kinds=("task", "reminder"), statuses=OPEN, limit=500))
            due = [i.brief() for i in store.due()]
        finally:
            store.close()
        return {
            "now": now_local().isoformat(timespec="minutes"),
            "jobs_running": running,
            "palace_processes": palace_processes(),
            "jobs_recent": recent,
            "tasks_open": open_n,
            "due": due,
            "models": {
                "chat": model_state(cfg.runtime.port_for("routine") or 8080,
                                    key=chat_key(policy)),
                "embedder": model_state(cfg.runtime.port_for("embedding") or 8081),
            },
            "heartbeat": last_tick(cfg.paths.data_dir, interval_s=policy.interval_s),
            "services": _launch_agents(),
            "stores": {
                "vectors": self.engine._get("vectors").count(),
                "literature_chunks": self.engine._get("curated").count(),
                "relation_edges": len(self.engine._get("edges").all()),
            },
        }

    def task_add(self, title: str, detail: str = "", due: str = "") -> dict[str, Any]:
        """Track a task for the owner, with an optional deadline."""
        from core.stores.tasks import parse_when

        return self._ledger(lambda s: {"added": s.add(
            "task", title, detail=detail, due_at=parse_when(due) if due else None).brief()})

    def remind(self, text: str, at: str) -> dict[str, Any]:
        """Bring something up at a moment: it appears among the due items from then on."""
        from core.stores.tasks import parse_when

        return self._ledger(lambda s: {"reminder": s.add(
            "reminder", text, due_at=parse_when(at)).brief()})

    def task_list(self, include_done: bool = False) -> dict[str, Any]:
        """Open tasks and reminders, running jobs; recently finished ones on request."""
        from core.stores.tasks import OPEN

        return self._ledger(lambda s: {"items": [
            i.brief() for i in [*s.select(statuses=(*OPEN, "running")),
                                *(s.finished(limit=10) if include_done else [])]]})

    def task_update(self, id: int, status: str = "", note: str = "",
                    due: str = "") -> dict[str, Any]:
        """Change an item's status, add a note, or move its deadline."""
        from core.stores.tasks import parse_when

        return self._ledger(lambda s: {"updated": s.update(
            int(id), status=status or None, note=note or None,
            due_at=parse_when(due) if due else None).brief()})

    def _ledger(self, op: Callable[[Any], dict[str, Any]]) -> dict[str, Any]:
        """Run one ledger operation, then refresh the notices the bridge shows the model."""
        from core.stores.tasks import now_local, open_task_store, write_notices

        store = open_task_store(self.engine.config)
        try:
            out = op(store)
            write_notices(store)
        finally:
            store.close()
        return {**out, "now": now_local().isoformat(timespec="minutes")}


def _launch_agents() -> list[dict[str, str]]:
    """The stack's LaunchAgents: running (pid) or idle, and the last exit status."""
    import subprocess

    out = subprocess.run(["launchctl", "list"], capture_output=True, text=True).stdout
    agents = []
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) == 3 and parts[2].startswith("com.mind-palace."):
            pid, last_exit, label = parts
            agents.append({"name": label.removeprefix("com.mind-palace."),
                           "state": "running" if pid != "-" else "idle", "last_exit": last_exit})
    return agents


def _schema(props: dict[str, Any], required: list[str]) -> dict[str, Any]:
    """Lean on purpose: every request carries every schema (the fixed cost of a turn), and the
    dispatch already refuses unknown arguments, so `additionalProperties` buys nothing here."""
    return {"type": "object", "properties": props, **({"required": required} if required else {})}


_S = {"type": "string"}
_I = {"type": "integer", "minimum": 1, "maximum": 50}
_WHEN = {"type": "string", "description": "local ISO time (2026-10-30T09:00) or +30m, +2h, +1d"}

TOOLS: list[tuple[str, str, dict[str, Any], str]] = [
    (
        "query",
        "The one read: a sentence of the query algebra, not keywords. Verbs: "
        'near "text" | diffuse S from <note> [beta b] | reach F from <note> [depth n] '
        "[back|forward] | relate <note> | trace <note> | walk from <note> [to <note>] via <regex "
        'over S,F,D,C> | witness "<edge id>" | read "<ref>" [chunk n] (the full text; read before '
        "quoting). Connectives and, or, minus, then; adjectives within <region>, over <strata>; "
        "top k, atleast t, far, not; assume <rel> <a> <b> [+w] in <sentence> (a hypothetical: the "
        "answer is a Hyp, never a fact). A <note> is a quoted path or title. Papers: over curated. "
        'Example: top 5 (near "sleep" and diffuse S from "health.md"), the five best of the '
        "product; top k takes its field with the field's adjectives, so top 5 near \"x\" within "
        "<region> ranks within it. The plan rides with the answer; a refusal names the word that "
        "would fix it; trace: true shows the work: the parse, every rewrite with its law, the "
        "support's census, each clause's arithmetic, the ranking.",
        _schema({"sentence": _S,
                 "trace": {"type": "boolean",
                           "description": "show the work: the parse, the rewrites and their "
                                          "laws, the census, each clause's arithmetic, the "
                                          "ranking"}}, ["sentence"]),
        "query",
    ),
    (
        "overview",
        "Counts per stratum and relation type; your grant.",
        _schema({}, []),
        "overview",
    ),
    (
        "sync_dialogue",
        "Sync new Open WebUI and OpenCode chats into the palace now.",
        _schema({}, []),
        "sync_dialogue",
    ),
    (
        "sync_notes",
        "Re-ingest the owner's changed notes (a `do sync vault` request the daemon lands).",
        _schema({}, []),
        "sync_notes",
    ),
    (
        "capture",
        "Remember text you relay, stored as observed, never as the owner's words (a `do capture` "
        "request the daemon lands).",
        _schema({"text": _S, "conversation": _S}, ["text"]),
        "capture",
    ),
    (
        "status",
        "Palace processes and jobs (ingestion, imports) with progress, models, services, "
        "store sizes, open and due items.",
        _schema({}, []),
        "status",
    ),
    (
        "task_list",
        "The owner's open tasks and reminders, and running jobs.",
        _schema({"include_done": {"type": "boolean"}}, []),
        "task_list",
    ),
    (
        "task_add",
        "Track a task for the owner; due is optional.",
        _schema({"title": _S, "detail": _S, "due": _WHEN}, ["title"]),
        "task_add",
    ),
    (
        "task_update",
        "Change a task or reminder: status open/waiting/done/dropped, a note, or a new due.",
        _schema({"id": _I | {"maximum": 10**9}, "status": {"enum": ["open", "waiting", "done",
                 "dropped"]}, "note": _S, "due": _WHEN}, ["id"]),
        "task_update",
    ),
    (
        "remind",
        "Remind the owner at a time.",
        _schema({"text": _S, "at": _WHEN}, ["text", "at"]),
        "remind",
    ),
    (
        "link",
        "Propose a relation between two notes, stored as interpreted (a `do link` request the "
        "daemon lands).",
        _schema(
            {
                "note_a": _S,
                "note_b": _S,
                "relation": {"enum": ["supports", "contradicts", "contextualizes"]},
            },
            ["note_a", "note_b", "relation"],
        ),
        "link",
    ),
    (
        "dream",
        "Request one dreaming pass (a `do dream` request; minutes, in a trough, wakes the large "
        "model).",
        _schema({}, []),
        "dream",
    ),
    (
        "relate",
        "Request a relation pass among similar notes (a `do relate` request; minutes, wakes the "
        "large model).",
        _schema({"max_pairs": _I}, []),
        "relate",
    ),
]


class Server:
    def __init__(self) -> None:
        self._amb: Ambassador | None = None

    @property
    def amb(self) -> Ambassador:
        if self._amb is None:
            self._amb = Ambassador()
        return self._amb

    def handle(self, msg: dict[str, Any]) -> dict[str, Any] | None:
        method, mid = msg.get("method"), msg.get("id")
        if mid is None:  # a notification (e.g. notifications/initialized)
            return None
        if method == "initialize":
            client = (msg.get("params") or {}).get("protocolVersion") or PROTOCOL_VERSION
            return _ok(
                mid,
                {
                    "protocolVersion": client,
                    "serverInfo": SERVER_INFO,
                    "capabilities": {"tools": {"listChanged": False}},
                    "instructions": INSTRUCTIONS,
                },
            )
        if method == "ping":
            return _ok(mid, {})
        if method == "tools/list":
            return _ok(
                mid,
                {
                    "tools": [
                        {"name": n, "description": d, "inputSchema": s} for n, d, s, _ in TOOLS
                    ]
                },
            )
        if method in ("resources/list", "prompts/list"):
            return _ok(mid, {method.split("/")[0]: []})
        if method == "tools/call":
            params = msg.get("params") or {}
            spec = next((t for t in TOOLS if t[0] == params.get("name")), None)
            if spec is None:
                return _err(mid, -32602, f"unknown tool {params.get('name')!r}")
            try:
                result = getattr(self.amb, spec[3])(**(params.get("arguments") or {}))
                text = json.dumps(result, ensure_ascii=False, default=str)
                return _ok(mid, {"content": [{"type": "text", "text": text}], "isError": False})
            except Exception as e:  # a refused or failed call is a result, not a crash
                print(traceback.format_exc(), file=sys.stderr)
                return _ok(
                    mid,
                    {
                        "content": [{"type": "text", "text": f"{type(e).__name__}: {e}"}],
                        "isError": True,
                    },
                )
        return _err(mid, -32601, f"method not found: {method}")


def _ok(mid: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": mid, "result": result}


def _err(mid: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": mid, "error": {"code": code, "message": message}}


def serve(stdin: Any = None, stdout: Any = None) -> None:
    stdin, stdout = stdin or sys.stdin, stdout or sys.stdout
    server = Server()
    for line in stdin:
        if not line.strip():
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            stdout.write(json.dumps(_err(None, -32700, "parse error")) + "\n")
            stdout.flush()
            continue
        reply = server.handle(msg)
        if reply is not None:
            stdout.write(json.dumps(reply, ensure_ascii=False) + "\n")
            stdout.flush()
