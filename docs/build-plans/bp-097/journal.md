# Journal — bp-097 (WF-2: the deskcheck gate)

> Alive while the plan is proposed/in-progress; sealed on completion.

## 2026-07-21 — MINTED (graduation, session-42)

- **State:** `proposed`. Graduated from the ratified
  `dn-track-board-and-deskcheck-gate` (§3's WF-2) alongside bp-096 (WF-1).
- **Grounding done at graduation:** gate-guard fires on `Edit|Write|MultiEdit`
  broadly with file-type gating in the lib (`_lib.py:424-426`), so covering
  `docs/deskchecks/**` is a lib change only — no settings.json edit (Q1). The
  post-hoc (c) scanner (`_blessing_in_diff:510-527`) and `cmd_stop_audit`
  (`:571-745`) are the surfaces extended; `test_handoff_gate.py` is carried in
  `write_scope` (retrofit rule) because this plan modifies `cmd_stop_audit`.
- **A NEW gap this session surfaced (folded into Item 4):** D6 teaches clause (c)
  to yield to an owner-staged *blessing*, but clause **(b2)** has no yield
  affordance — and the WF-1 track-backfill (owner hand-editing ratified notes)
  is a brand-new (b2) trigger that thrashed live this session (repeated Stop
  BLOCKs on the uncommitted `track:` edits). Item 4 adds a narrow, conservative
  (b2) yield for additive-metadata edits (never for body edits). `[ESTABLISHED —
  observed 2026-07-21]`.
- **Next action (on owner bless → ready):** `/build bp-097`; ship Item 1 (dc
  template + dir) first so the gate has a shape to test, then skills/probe
  (5,6,7), then the `_lib.py` chain 2→3→4 in sequence. Do NOT run concurrently
  with bp-090. Verdict flip stays owner-only after this lands.
- **Blocking:** none. Awaiting the proposed→ready blessing (owner-only, by hand).
