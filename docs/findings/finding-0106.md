---
type: finding
id: finding-0106
status: open
created: 2026-07-18
updated: 2026-07-18
links:
  - scripts/palace.py                              # the full lifecycle CLI (has up/down/restart/deploy)
  - ops/lifecycle/launcher.py                      # the launchd-control verbs
re_entry: the mind-palace wrapper should route (or explicitly delegate) the launchd/promote verbs; low-priority UX
ftype: codebase
origin_plan: orchestrator
route: builder
resolution: null
---

# The `mind-palace` wrapper omits the launchd/promote verbs (`up`/`down`/`restart`/`deploy`)

## What
Discovered during the session-27 Ouroboros recovery. The `mind-palace <verb>` shell wrapper exposes
only the day-to-day subset (`start | stop | status | reset`, plus talk/monitor/sandbox/ingest/…). The
launchd maintenance + promotion verbs — **`up`, `down`, `restart`, `deploy`** — are implemented in
`scripts/palace.py` (its `USAGE` + `main()` dispatch) but are NOT routed by the wrapper:

    $ mind-palace up
    mind-palace: unknown verb 'up'

They only work as `uv run scripts/palace.py <verb>`. Worse, `palace status` prints guidance that
references a verb the wrapper doesn't have:

    ⚠ running … — HEAD is …: run #N is behind. `palace deploy` to promote onto HEAD.

so a user who followed the on-screen instruction via `mind-palace deploy` would hit "unknown verb."

## Why it matters
It cost real confusion mid-incident: recovering the daemon needed `down`/`up`, but `mind-palace up`
failed, so the fix had to fall back to `uv run scripts/palace.py up`. The wrapper and the underlying
script have diverged, and the status output points at the wrapper-absent verb. It is a UX/consistency
defect, not a correctness bug (the functionality exists on the script).

## Fix (builder, when convenient)
Route the launchd/promote verbs through the `mind-palace` wrapper (pass-through to
`scripts/palace.py`), OR — if their omission is deliberate (advanced/gated verbs) — have the wrapper
print a one-line pointer ("use `uv run scripts/palace.py up`") for the unknown verb, and change the
`status` guidance to name the actual invocation. Low priority; a papercut, not a blocker.

## Routing
`codebase` → builder (the wrapper is tooling). Surfaced by the recovery incident; independent of
finding-0105 (the deploy-gate/ratchet interaction).
