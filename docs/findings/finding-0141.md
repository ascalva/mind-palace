---
type: finding
id: finding-0141
status: open
created: 2026-07-21
updated: 2026-07-21
links:
  - docs/brainstorms/agent-causal-loop.md
  - docs/design-notes/agentic-loop.md
  - docs/design-notes/synchronic-diachronic-dreamer.md
  - docs/findings/finding-0011.md
ftype: spec-fidelity
origin_plan: orchestrator        # session-39 dispatched fable design pass (dn-agentic-loop)
route: orchestrator
resolution: null
---

# finding-0141 — "Internal loop closed and LIVE" overstates: the probe half (bp-079/082) is built, flag-gated, and not wired

## What
`docs/brainstorms/agent-causal-loop.md` (first capsule) states the internal
sense→act→confirm loop is *"built, closed, LIVE"* via bp-079 (DreamCharter/force)
and bp-082 (influence + conditioning). Verified in code 2026-07-21: the charter and
influence machinery are **built and sealed but not reachable from any live entry
point** — `[dream_rnd] enabled = false` (`config/defaults.toml:263-267`), every R&D
entry raises via `require_rnd_enabled` (`core/dreaming/rnd.py:31`), and a grep of
`ops/lifecycle/launcher.py` + `scheduler/` for `charter|influence|force` returns
zero live constructions. What IS live is the internal **record-keeping** loop:
sensors (φ_chat/φ_code/φ_self) + the chat↔code↔doc integrator run in the daemon
(`ops/lifecycle/launcher.py:238,246,316,325`; 4,084 C-edges, 7,966 chat utterances
in the live stores). The brainstorm conflated the two halves.

## Why it matters
Same honesty class as finding-0011 (a wiring-posture claim in the design record),
one tier in: posture claims about which loops run must match code, because the
loop's governance story ("the probe is budget/refusal-gated") is only auditable
against the half that actually runs. Direction of the error is **safe** — the half
claimed live is read-only-plus-interpreted and is in fact more dormant than
claimed. Accuracy defect, not a safety hole. `dn-agentic-loop` §2.0/§2.6 (G-A)
carries the corrected inventory.

## Re-entry condition
Either (a) the brainstorm's status language is glossed/corrected at its next
capsule (the design note's §2.0 already carries the correction), or (b) the claim
becomes true: the owner wires the R&D flag on and a live entry point constructs a
DreamCharter dispatch — a deliberate, owner-shaped act (PD-3 of `dn-agentic-loop`
gates the steering heuristic on exactly this).

## Routing
`spec-fidelity` → orchestrator (the surface is a brainstorm + PROGRESS posture,
orchestrator-owned; no builder action exists).
