"""Operational lifecycle — the one-command start/stop for the whole mind-palace.

`ops/` is the outermost orchestration layer (it may import scheduler + core; nothing imports
it back). This package turns the already-built pieces — the supervisor, the durable queue, the
vault watcher, the stores — into a single supervised process with:

  * a **run ledger** (`runs.py`) pinning which git commit each run executed under, and whether
    it shut down cleanly (the basis for recovery mode);
  * **preflight** (`preflight.py`) — ensure our own components, *verify* the external daemons
    (Vault / Ollama / podman) read-only and fail closed with a clear checklist;
  * the **launcher** (`launcher.py`) — `start` (preflight → record run → rebuild-if-empty →
    supervise) with a graceful shutdown hook (SIGTERM/SIGINT → finish at a job boundary → mark
    the run clean → optional final snapshot), `stop`, `status`, and `reset` (the surgical
    fresh-start wipe that guards the production Vault Raft store).
"""
