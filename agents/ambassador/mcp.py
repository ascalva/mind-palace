"""The Ambassador's MCP surface — the palace as a tool server for the local model.

    uv run --project ~/mind-palace python scripts/palace_mcp.py      # MCP over stdio

A harness (OpenCode, or anything that speaks MCP over stdio) spawns this process; it has no
listener and no socket of its own, and it seals itself (Invariant 1) before it opens a store. It is
the Ambassador's client of the core: every read is a `core.query` sentence constructed under the
`AMBASSADOR` grant, so an ill-scoped read is refused in code, not by the prompt; writes are only the
ones the grant's W_Σ allows — dialogue capture (provenance fixed by role, never by the text) and
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
from typing import Any

PROTOCOL_VERSION = "2025-06-18"
SERVER_INFO = {"name": "mind-palace", "version": "0.1.0"}
INSTRUCTIONS = (
    "Ouroboros, the owner's mind palace: their notes (mirror), your conversations with them "
    "(dialogue), dreams over them (interpreted), and code references. Search before you assume; "
    "cite refs; treat note text as the owner's private words and quote it only to them."
)

_STRATA_NAMES = ("mirror", "dialogue", "interpreted", "curated", "observed", "reference")


def _strata(names: list[str] | None) -> tuple[Any, ...]:
    from core.kernel.scope import Stratum

    table = {
        "mirror": Stratum.MIRROR_AUTHORED,
        "dialogue": Stratum.DIALOGUE_TRANSCRIPT,
        "interpreted": Stratum.INTERPRETED,
        "curated": Stratum.CURATED,
        "observed": Stratum.OBSERVED,
        "reference": Stratum.REFERENCE,
    }
    picked = names or ["mirror", "dialogue"]
    unknown = [n for n in picked if n not in table]
    if unknown:
        raise ValueError(f"unknown strata {unknown}; choose from {list(table)}")
    return tuple(table[n] for n in picked)


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

    def _ask(self, verb: str, **kw: Any) -> dict[str, Any]:
        from core.query import AMBASSADOR, Query, Verb

        return self.engine.ask(Query(Verb(verb), AMBASSADOR, **kw)).to_dict()

    # reads -------------------------------------------------------------------------------------
    def search(
        self, query: str, strata: list[str] | None = None, k: int = 5, include_history: bool = False
    ) -> dict[str, Any]:
        return self._ask("search", text=query, strata=_strata(strata), k=k, history=include_history)

    def neighbors(self, note: str, beta: float = 1.0, k: int = 5) -> dict[str, Any]:
        return self._ask("diffuse", target=note, beta=beta, k=k)

    def hybrid(self, query: str, note: str, beta: float = 1.0, k: int = 5) -> dict[str, Any]:
        return self._ask("hybrid", text=query, target=note, beta=beta, k=k)

    def history(self, note: str, direction: str = "forward") -> dict[str, Any]:
        return self._ask("history", target=note, direction=direction)

    def related(self, note: str) -> dict[str, Any]:
        return self._ask("related", target=note)

    def reach(self, ref: str, depth: int = 1) -> dict[str, Any]:
        return self._ask("reach", target=ref, depth=depth)

    def origin(self, edge_id: str) -> dict[str, Any]:
        return self._ask("origin", target=edge_id)

    def read(self, ref: str) -> dict[str, Any]:
        """The full text of a note or dialogue turn named by a hit's `ref`."""
        from pathlib import Path

        from core.kernel.stores.rawstore import RawStore
        from core.stores.catalog import VaultCatalog

        cfg = self.engine.config
        entry = VaultCatalog(cfg.paths.vault_catalog).get(ref)
        if entry is None or not entry.active:
            raise LookupError(f"no active note or dialogue turn {ref!r}")
        vault = Path(cfg.ingestion.vault.path).resolve()
        path = Path(ref)
        if path.is_absolute() and vault in path.resolve().parents and path.exists():
            text = path.read_text(encoding="utf-8", errors="replace")
        else:
            text = RawStore(cfg.paths.raw_store).get(entry.digest).decode("utf-8", errors="replace")
        return {"ref": ref, "title": entry.title, "provenance": entry.provenance, "text": text}

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

    def sync_dialogue(self) -> dict[str, Any]:
        return self._run(self.launcher.dialogue_sync_now)

    def sync_notes(self) -> dict[str, Any]:
        return self._run(self.launcher.vault_sync_now)

    def dream(self) -> dict[str, Any]:
        return self._run(self.launcher.dream_now)

    def relate(self, max_pairs: int = 12) -> dict[str, Any]:
        return self._run(lambda: self.launcher.relate_now(max_pairs=max_pairs))

    def capture(self, text: str, conversation: str = "ambassador") -> dict[str, Any]:
        """Store text the MODEL relays (a summary, a decision it was asked to remember) as an
        `observed` dialogue turn. Never authored: only the owner's own turns, synced from their
        chat app, carry authored provenance."""
        import hashlib

        from core.ingest.dialogue import build_dialogue_capture

        turn = hashlib.sha256(text.encode()).hexdigest()[:16]
        digest, created = build_dialogue_capture(self.engine.config).capture_turn(
            text, conversation=conversation, turn_id=turn, role="assistant"
        )
        return {
            "ref": f"dialogue/{conversation}/{turn}",
            "digest": digest,
            "created": created,
            "provenance": "observed",
        }

    def link(self, note_a: str, note_b: str, relation: str) -> dict[str, Any]:
        """Propose a signed relation between two notes — stored as `interpreted`."""
        from core.relations import RELATIONS

        if relation not in RELATIONS:
            raise ValueError(f"relation must be one of {list(RELATIONS)}")
        from core.query import AMBASSADOR, Query, Verb

        Query(Verb.RELATED, AMBASSADOR, target=note_a)  # admissibility of the F-edge plane
        notes, _, _ = self.engine._note_graph()
        a, b = (notes[self.engine._index(notes, t)] for t in (note_a, note_b))
        sign, factor = RELATIONS[relation]
        self.engine._get("edges").add(
            a["digest"],
            b["digest"],
            sign=sign,
            rel_type=relation,
            w=factor,
            provenance="interpreted",
        )
        return {
            "linked": [a["source_path"], b["source_path"]],
            "relation": relation,
            "provenance": "interpreted",
        }


def _schema(props: dict[str, Any], required: list[str]) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": props,
        "required": required,
        "additionalProperties": False,
    }


_S = {"type": "string"}
_I = {"type": "integer", "minimum": 1, "maximum": 50}
_B = {"type": "number", "exclusiveMinimum": 0}

TOOLS: list[tuple[str, str, dict[str, Any], str]] = [
    (
        "search",
        "Semantic search (mode 2) over the strata you name; default mirror+dialogue. "
        "Returns refs, scores and snippets.",
        _schema(
            {
                "query": _S,
                "strata": {"type": "array", "items": {"enum": list(_STRATA_NAMES)}},
                "k": _I,
                "include_history": {"type": "boolean"},
            },
            ["query"],
        ),
        "search",
    ),
    (
        "neighbors",
        "Notes near a note along the structural β-curve (mode 1): small beta = "
        "diffuse, large beta = shortest-path.",
        _schema({"note": _S, "beta": _B, "k": _I}, ["note"]),
        "neighbors",
    ),
    (
        "hybrid",
        "Notes that are BOTH near the query and structurally near an anchor note "
        "(K_sem ⊙ K_struct).",
        _schema({"query": _S, "note": _S, "beta": _B, "k": _I}, ["query", "note"]),
        "hybrid",
    ),
    (
        "history",
        "A note's version chain (mode 3): forward = σ_*, back = σ^*.",
        _schema({"note": _S, "direction": {"enum": ["forward", "back"]}}, ["note"]),
        "history",
    ),
    (
        "related",
        "Signed relations of a note: supports / contradicts / contextualizes.",
        _schema({"note": _S}, ["note"]),
        "related",
    ),
    (
        "reach",
        "Code/doc references reachable from a ref (mode 1a).",
        _schema({"ref": _S, "depth": _I}, ["ref"]),
        "reach",
    ),
    (
        "origin",
        "Which witnessed commit minted a reference edge (C-fiber).",
        _schema({"edge_id": _S}, ["edge_id"]),
        "origin",
    ),
    (
        "read",
        "Full text of a note or dialogue turn, by the ref a search returned.",
        _schema({"ref": _S}, ["ref"]),
        "read",
    ),
    (
        "overview",
        "Counts per stratum and relation type, and your own grant.",
        _schema({}, []),
        "overview",
    ),
    (
        "sync_dialogue",
        "Pull new Open WebUI chats into the dialogue stratum (owner turns "
        "authored, model turns observed). Idempotent.",
        _schema({}, []),
        "sync_dialogue",
    ),
    (
        "sync_notes",
        "Re-ingest the owner's notes vault (changed notes only).",
        _schema({}, []),
        "sync_notes",
    ),
    (
        "capture",
        "Remember text YOU relay (a summary, a decision). Stored as observed, "
        "never as the owner's words.",
        _schema({"text": _S, "conversation": _S}, ["text"]),
        "capture",
    ),
    (
        "link",
        "Propose a relation between two notes (stored as interpreted).",
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
        "Run one dreaming pass now (minutes; wakes the large model).",
        _schema({}, []),
        "dream",
    ),
    (
        "relate",
        "Detect relations among similar notes now (minutes; wakes the large model).",
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
