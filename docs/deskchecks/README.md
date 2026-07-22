# docs/deskchecks — the deskcheck record store

A **deskcheck** (`dc-NNN.md`) is the typed artifact that closes a track: the owner
sits with the built work, sees it run (or reads its honest current state), and
records a verdict. It is the third owner-only gate (`dn-track-board-and-deskcheck-gate`
D3) — alongside `draft→ratified` and `proposed→ready`.

## The record

Instantiate from `docs/templates/deskcheck.md`. The schema is pinned identically in
`bp-096 §6` (so `scripts/board.py` parses the verdict) and `bp-097 §6`. Front matter:
`type, id, track, date, items, audit_refs, verdict, send_back, links`; body: *What was
built · How · Surprises · What is NOT done*.

## The verdict is owner-only, by hand

`verdict: pending` is the **only** agent-legal starting value. The flip to
`approved` / `needs-work` is the owner's hand, in the blessing ceremony (lazygit;
the agent pre-loads the commit message, **never** stages/commits or polls — D6).
Enforcement is structural, both pre-hoc (`gate-guard` → `cmd_gate_check`) and post-hoc
(the Stop-audit clause (c) verdict scan). An agent that tries to flip a verdict is
denied; a Bash-mediated flip is caught at Stop until the owner commits it.

## Who authors the bundle

The agent prepares the *whole* bundle — the four body sections, `items`, `audit_refs`,
`track` — and leaves `verdict: pending`. Authoring an actual `dc-NNN` record is an
**owner session** off the deskcheck queue (`docs/DESKCHECK-QUEUE.md`), not a builder
task; none are seeded here.

`board.py` treats a track as CLOSED iff an `approved` `dc-NNN` names it **and** its
manifest `dod` items are closed. An empty `docs/deskchecks/` is the normal early
state ("no dc → deskcheck-pending"); the board must not error on it.
