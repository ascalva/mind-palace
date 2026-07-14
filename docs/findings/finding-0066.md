---
type: finding
id: finding-0066
status: routed
created: 2026-07-13
updated: 2026-07-13
links:
  - docs/build-plans/bp-026/plan.md
  - docs/build-plans/bp-030/plan.md
  - scripts/palace.py
  - ops/lifecycle/launcher.py
ftype: direction
origin_plan: bp-026
route: orchestrator
resolution: >
  Two halves. (1) The KeepAlive-aware daemon-down command is GRADUATED into bp-030 (proposed,
  2026-07-13) — `down`/`up`/`restart` via launchctl bootout/bootstrap, part of the lifecycle-CLI
  overhaul (brainstorm: lifecycle-cli-overhaul.md). (2) The live-store-schema-migration deploy
  coupling remains a STANDING RULE (owner-coordinated bootout→migrate→bootstrap; resume-brief).
  Stays routed until bp-030 seals the command half.
---

# A live-store schema migration is deploy-coupled — and there's no KeepAlive-aware daemon-down command

## What

bp-026 §6(d)/Item 21 assumed the orchestrator runs the live wipe+reproject "at seal." That
assumption missed the running daemon: `com.mind-palace.palace` is a user LaunchAgent whose
`WorkingDirectory` is the repo and which **shares `data/`** (confirmed by `lsof`), holding the
**deployed (v1) code in memory** (Python doesn't hot-reload; a merge to main does not change
the running process). So a v2 schema migration of the live store:

1. **cannot run while the v1 daemon holds `data/`** — concurrent access + the daemon's next
   sync would hit a v2 store with v1 code (`sqlite3.OperationalError`, the builder's flag);
2. **is coupled to deploy** — the store schema must match the *running* code, and bringing the
   daemon onto v2 (a restart from disk HEAD) is effectively a deploy (owner-only);
3. **required a real daemon-down window** for the migration, which surfaced a second gap:

**`palace stop` does not hold the daemon down.** `KeepAlive=true` (the plist), so `stop` drains
and launchd immediately restarts it. Taking it down for maintenance needed a raw
`launchctl bootout gui/$(id -u)/com.mind-palace.palace`, and back up needed `bootstrap` — no
first-class command wraps this.

This migration was handled by a **coordinated owner-driven sequence** (owner: bootout → me:
wipe+reproject+verify → owner: bootstrap), which worked, but nothing in the plan or tooling
anticipated it.

## Why it matters

Every future schema change to a corpus-class store shared by the live daemon has this coupling.
Treating it as "orchestrator runs it at seal" (bp-026's framing) is wrong and unsafe; it is an
**owner-coordinated deploy+migration**. And the missing "maintenance down" command is a footgun
— `palace stop` looks like it stops the daemon but doesn't.

## Re-entry condition (two, separable)

1. **The control-command gap (small, near-term):** add KeepAlive-aware `palace down` (bootout —
   drain AND stay down), `palace up` (bootstrap), `palace restart` to `scripts/palace.py`, so
   the raw `launchctl` incantation is never hand-typed and "maintenance down" ≠ "operational
   stop". A small build plan; sonnet; the checker is a start/stop/verify cycle.
2. **The migration-coordination pattern (process):** the build-plan template / graduate skill
   should treat any live-daemon-shared store schema change as **deploy-coupled** — its live
   step is an owner-driven stop→migrate→restart, journaled with the down-window, never an
   orchestrator-at-seal write. Consider a `mind-palace migrate` mode that the deploy path can
   invoke in the stopped window.

## Routing

`direction` → orchestrator (process + a small tooling plan). Non-blocking; the pattern is
recorded so the next such migration is designed, not discovered mid-flight (as this one was).
