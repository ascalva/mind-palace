"""Read the owner's OpenCode sessions with the local model, read-only, into a handoff file.

    python -m edge.opencode_sessions --out data/handoff/dialogue/opencode.json [--db PATH]

The same shape and the same discipline as `edge.openwebui`: this process imports nothing from the
core and never reads the vault; it opens OpenCode's own database read-only (`mode=ro`), keeps the
top-level sessions (subagent sessions are the model talking to itself), and from each message only
its TEXT parts — reasoning, tool calls and step markers are left out — then writes one JSON document
atomically. `palace dialogue-sync` ingests it like an Open WebUI chat.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any

DEFAULT_DB = Path.home() / ".local" / "share" / "opencode" / "opencode.db"


def latest_update(db: Path = DEFAULT_DB) -> int:
    """When the newest top-level session last changed (OpenCode's `time_updated`, epoch ms)."""
    if not db.exists():
        return 0
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        row = con.execute("select max(time_updated) from session "
                          "where parent_id is null and time_archived is null").fetchone()
        return int(row[0] or 0)
    finally:
        con.close()


def export_sessions(db: Path = DEFAULT_DB) -> list[dict[str, Any]]:
    if not db.exists():
        return []
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        out = []
        for sid, title, updated in con.execute(
            "select id, title, time_updated from session "
            "where parent_id is null and time_archived is null order by time_updated"
        ):
            texts: dict[str, list[str]] = {}
            for mid, data in con.execute(
                "select message_id, data from part where session_id = ? order by time_created",
                (sid,),
            ):
                part = json.loads(data or "{}")
                if part.get("type") == "text" and str(part.get("text", "")).strip():
                    texts.setdefault(mid, []).append(part["text"])
            turns = []
            for mid, data, created in con.execute(
                "select id, data, time_created from message where session_id = ? "
                "order by time_created",
                (sid,),
            ):
                role = json.loads(data or "{}").get("role")
                if mid in texts and role in ("user", "assistant"):
                    turns.append(
                        {
                            "id": mid,
                            "role": role,
                            "content": "\n".join(texts[mid]),
                            "timestamp": int(created) // 1000 if created else None,
                        }
                    )
            out.append({"chat_id": sid, "title": title, "updated_at": updated, "turns": turns})
        return out
    finally:
        con.close()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="edge.opencode_sessions")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    ap.add_argument("--latest", action="store_true",
                    help="print when the newest session last changed, and nothing else")
    args = ap.parse_args(argv)
    if args.latest:
        print(json.dumps({"latest": latest_update(args.db)}))
        return 0
    if args.out is None:
        ap.error("--out is required")
    chats = export_sessions(args.db)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    tmp = args.out.with_suffix(".part")
    tmp.write_text(json.dumps({"source": "opencode", "chats": chats}))
    os.replace(tmp, args.out)
    print(f"{len(chats)} session(s), {sum(len(c['turns']) for c in chats)} turn(s) -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
