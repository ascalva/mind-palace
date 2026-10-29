"""Read the owner's Open WebUI chats out of lmtune's container, read-only, into a handoff file.

    python -m edge.openwebui --out data/handoff/dialogue/openwebui.json [--container lmtune-webui]

Zone B: this process imports nothing from the core and never reads the vault. It runs a fixed,
read-only SQLite query inside the Open WebUI container (`podman exec`, `mode=ro` URI — the
container's database is opened read-only and nothing in Open WebUI changes), walks each chat's
ACTIVE branch (`history.currentId` back through `parentId`, so abandoned regenerations are not
ingested), keeps text content only, and writes one JSON document to `--out` atomically. The core
side (`palace dialogue-sync`) reads that file — the filesystem handoff is the only channel.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

CONTAINER_DB = "/app/backend/data/webui.db"

_READER = r"""
import json, sqlite3, sys
db = sys.argv[1] if len(sys.argv) > 1 else "/app/backend/data/webui.db"
con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
out = []
for cid, title, updated, raw in con.execute(
        "select id, title, updated_at, chat from chat where archived = 0 order by updated_at"):
    chat = json.loads(raw or "{}")
    msgs = (chat.get("history") or {}).get("messages") or {}
    cur, branch, seen = (chat.get("history") or {}).get("currentId"), [], set()
    while cur and cur in msgs and cur not in seen:
        seen.add(cur)
        branch.append(msgs[cur])
        cur = msgs[cur].get("parentId")
    turns = []
    for m in reversed(branch):
        content = m.get("content")
        if isinstance(content, list):
            content = "\n".join(p.get("text", "") for p in content if isinstance(p, dict))
        if not isinstance(content, str) or not content.strip():
            continue
        turns.append({"id": m.get("id"), "role": m.get("role"), "content": content,
                      "timestamp": m.get("timestamp")})
    out.append({"chat_id": cid, "title": title, "updated_at": updated, "turns": turns})
json.dump(out, sys.stdout)
"""


def export_chats(
    container: str, *, runner: list[str] | None = None, db: str = CONTAINER_DB
) -> list[dict]:
    """Run the read-only reader inside `container` (or under `runner`, e.g. a local python for a
    test fixture) and return the chats' active branches."""
    argv = runner or ["podman", "exec", "-i", container, "python3"]
    proc = subprocess.run(
        [*argv, "-", db], input=_READER, capture_output=True, text=True, timeout=120
    )
    if proc.returncode != 0:
        raise RuntimeError(f"reading Open WebUI chats failed: {proc.stderr.strip()[:300]}")
    return json.loads(proc.stdout or "[]")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="edge.openwebui")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--container", default="lmtune-webui")
    args = ap.parse_args(argv)
    chats = export_chats(args.container)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    tmp = args.out.with_suffix(".part")
    tmp.write_text(json.dumps({"source": "openwebui", "container": args.container, "chats": chats}))
    os.replace(tmp, args.out)
    print(f"{len(chats)} chat(s), {sum(len(c['turns']) for c in chats)} turn(s) -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
