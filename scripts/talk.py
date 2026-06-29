#!/usr/bin/env python
"""Talk to the mind-palace — a local REPL over the Ambassador (Track B). From the repo root:

    ./.venv/bin/python scripts/talk.py                 # LIVE: real models + your ingested vault
    ./.venv/bin/python scripts/talk.py --offline       # OFFLINE: deterministic, self-contained demo

It drives the REAL path — LocalAdapter → gateway → filesystem handoff → core inbox → Ambassador
→ handoff → gateway — in-process, so there's no daemon to install and no Tailscale decision to
make to start using it. (A tiny stdlib HTTP front end reachable over Tailscale is an optional
owner-operational follow-up; see docs/runbook.md → "Talking to the system".)

Each turn, after the inbox replies, any DELEGATED task ("look into …") is run so its result is
ready to surface on your next message — the in-process stand-in for the supervisor.

LIVE needs Ollama running + an ingested vault (scripts/ingest.py) and the curated self-knowledge
graph (scripts/ingest_self_knowledge.py). OFFLINE uses a hashing embedder + a deterministic
responder over a throwaway temp store seeded with a few sample notes + the real design docs, so
the full loop (retrieve / explain / status / task→deferred / capture) runs with no Ollama.
"""

from __future__ import annotations

import dataclasses
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root on path

from core.sealing import seal


class _OfflineServer:
    """A deterministic, Ollama-free chat stand-in for the offline demo. It reads the assembled
    context (Constitution → role → retrieved chunks → history → question) and renders a plain,
    grounded-looking reply from the retrieved notes — enough to exercise the whole loop."""

    def chat(self, tier, messages, *, think=None, temperature=None) -> str:
        import re

        question = messages[-1]["content"] if messages else ""
        # Retrieved grounding is the system message(s) shaped like chunks — the Ambassador's
        # per-chunk "[[title]]\ntext" or the Librarian's "Retrieved notes …" block. (Anchored on
        # the message START so the role prompt's inline "e.g. [[note title]]" example is excluded.)
        grounding = "\n".join(
            m["content"] for m in messages
            if m.get("role") == "system"
            and (m["content"].startswith("[[") or m["content"].startswith("Retrieved notes"))
        )
        if not grounding:
            return (f"I don't have anything in your notes about \"{question}\". "
                    "Tell me about it and I'll remember it.")
        titles = re.findall(r"\[\[([^\]]+)\]\]", grounding)[:2]
        snippet = next((ln.strip() for ln in grounding.splitlines()
                        if ln.strip() and "[[" not in ln and not ln.startswith("Retrieved")), "")
        cited = ", ".join(f"[[{t}]]" for t in titles)
        return (f"From your notes ({cited}): {snippet[:180]} "
                "— that's what you've written; the reading is yours to make.")


def _seed_offline(store, embedder, cfg, repo_root: Path) -> None:
    """Seed a throwaway corpus so the offline demo has something to retrieve + explain."""
    from core.ingest.curated import curated_sources, ingest_curated
    from core.stores.catalog import VaultCatalog
    from core.stores.rawstore import RawStore

    samples = [
        ("sleep", "Racing thoughts at night again. Slow breathing before bed helps me settle."),
        ("running", "Felt steady and clear after the morning run. The routine is grounding me."),
        ("work", "The deadline pressure is back. I notice I get short with people when stressed."),
    ]
    rows = []
    for i, (title, text) in enumerate(samples):
        rows.append({"id": f"seed{i}:0", "digest": f"seed{i}", "title": title,
                     "source_path": f"/seed/{title}", "chunk_index": 0,
                     "provenance": "authored-solo", "text": text,
                     "vector": embedder.embed_documents([text])[0]})
    store.add(rows)
    # the real self-knowledge docs, so "how do you work?" has something to answer from
    ingest_curated(curated_sources(repo_root)[:8], raw=RawStore(cfg.paths.raw_store), store=store,
                   embedder=embedder, catalog=VaultCatalog(cfg.paths.vault_catalog),
                   repo_root=repo_root)


def _offline_runtime():
    from config.loader import REPO_ROOT, get_config
    from core.stores.vectorstore import VectorStore
    from scheduler.interface import build_conversation_runtime
    from tests.fixtures.fakes import HashingEmbedder

    tmp = Path(tempfile.mkdtemp(prefix="mind-palace-talk-"))
    base = get_config()
    paths = dataclasses.replace(
        base.paths, data_dir=tmp, raw_store=tmp / "raw", vector_store=tmp / "v.lance",
        vault_catalog=tmp / "catalog.sqlite", attestation_store=tmp / "att.sqlite",
        derived_store=tmp / "derived.sqlite", telemetry_db=tmp / "t.duckdb",
    )
    itf = dataclasses.replace(base.interface, handoff_dir=tmp / "handoff")
    cfg = dataclasses.replace(base, paths=paths, interface=itf)

    embedder = HashingEmbedder(64)
    store = VectorStore(cfg.paths.vector_store, dim=64)
    cfg = dataclasses.replace(cfg, embedding=dataclasses.replace(base.embedding, dim=64))
    _seed_offline(store, embedder, cfg, REPO_ROOT)
    return build_conversation_runtime(cfg, server=_OfflineServer(), embedder=embedder, store=store)


def main(argv: list[str]) -> int:
    seal()  # structural egress guard first (Invariant 1) — the loop is core-side
    offline = "--offline" in argv

    if offline:
        runtime = _offline_runtime()
        print("mind-palace (OFFLINE demo — deterministic, throwaway store).")
    else:
        from scheduler.interface import build_conversation_runtime
        runtime = build_conversation_runtime()
        print("mind-palace (LIVE — real models + your vault). Needs Ollama running.")
    print("Type a message; 'exit' or Ctrl-D to quit.\n")

    while True:
        try:
            text = input("you ❯ ").strip()
        except EOFError:
            print()
            break
        if text.lower() in {"exit", "quit"}:
            break
        if not text:
            continue
        reply = runtime.send(text)
        print(f"\npalace ❯ {reply}\n")
        runtime.run_pending_tasks()   # complete any delegated work for the next turn
    runtime.queue.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
