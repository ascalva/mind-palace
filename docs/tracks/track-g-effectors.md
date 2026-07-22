---
type: track
slug: track-g-effectors
title: Track G / effectors — G1–G7 (e0bf1ad)
status: deferred
warrant: finding-0011
audit_refs: []
re_entry: a design decision on WHETHER/HOW to wire the effectors (what tier, what controls) — the effectors are a major safety surface and we don't have that answer yet
dod:
  - G1–G7 built (e0bf1ad) — but NOT wired (max reachable tier NONE)
  - WIRE the effectors reachable behind the full control stack (72-state gate, propose-never-send, JIT creds), DEFAULT OFF + owner-flippable — worth building ⇒ worth wiring
  - a design pass on the wiring approach precedes the build
backlog_deskcheck: null
links:
  - docs/findings/finding-0011.md
  - docs/findings/finding-0159.md
---
# Track — Track G / effectors (G1–G7)

The identity card for the effectors track. **Scope:** the hands — the effector
types, the 72-state gate, the catalog/pipeline, the reversible-writes propose-never-send
path, and the JIT-credential executor (G1–G7, committed `e0bf1ad`).

**Status: DEFERRED — not done, not "dormant-by-design"** (owner 2026-07-22, finding-0159).
G1–G7 are built but NOT wired (max reachable tier NONE = unreachable). "Built but never wired,
called done" is banned — if it was worth building it is worth wiring. But we genuinely lack the
answers on WHETHER/HOW to wire the effectors (the most dangerous capability — the hands), so the
track is honestly **deferred**: paused, open, with the re-entry above. Deferred ≠ done; when off,
"off" must mean WIRED-but-flag-off (a real, owner-flippable ON switch behind the control stack),
never permanently unreachable.

**Not deskcheck-ready** — a deferred track is not finished; it resumes at its re-entry, gets
wired, and only a demonstration of it working (gated off is fine) is deskcheckable.
