---
type: track
slug: track-g-effectors
title: Track G / effectors — G1–G7 (e0bf1ad)
status: active
warrant: finding-0011
audit_refs: []
dod:
  - G1–G7 built (e0bf1ad) — but currently NOT wired (max reachable tier NONE): work-owed
  - WIRE the effectors reachable behind the full control stack (72-state gate, propose-never-send, JIT creds), DEFAULT OFF + owner-flippable — the ON switch must exist (worth building ⇒ worth wiring)
  - a design pass on the wiring approach (what tier, what controls) precedes the build
backlog_deskcheck: null
links:
  - docs/findings/finding-0011.md
  - docs/findings/finding-0159.md
---
# Track — Track G / effectors (G1–G7)

The identity card for the effectors track. **Scope:** the hands — the effector
types, the 72-state gate, the catalog/pipeline, the reversible-writes propose-never-send
path, and the JIT-credential executor (G1–G7, committed `e0bf1ad`).

**Status: active — WORK-OWED, not "dormant-by-design"** (owner ruling 2026-07-22, finding-0159):
G1–G7 are built but NOT wired — the max reachable effector tier is NONE (unreachable). That is the
built-not-wired anti-pattern, not a valid final state: **if it was worth building, it is worth
wiring.** Safety-gating the effectors OFF by default is correct — but off means WIRED-but-flag-off
(the ON switch exists, owner-flippable behind the full control stack), never unreachable. Wiring
them (default-off, reachable, gated) is owed; a design pass on how precedes it.

**Not deskcheck-ready.** Not until the effectors are wired (reachable, gated off) — a deskcheck is
"here it is, working as expected", never "confirm it stays dark".
