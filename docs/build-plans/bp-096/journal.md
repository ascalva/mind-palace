# Journal — bp-096 (WF-1: the board substrate)

> Alive while the plan is proposed/in-progress; sealed on completion.

## 2026-07-21 — MINTED (graduation, session-42)

- **State:** `proposed`. Graduated from the ratified
  `dn-track-board-and-deskcheck-gate` (§3's WF-1) alongside bp-097 (WF-2).
- **Grounding done at graduation** (so a builder inherits it, doesn't re-derive):
  all five active-track design notes are `ratified` → a builder cannot backfill
  `track:` onto them (scope-guard `_lib.py:390-398`; Stop (b2) `:634-645`). The
  owner hand-tagged the six ratified active-track notes in commit `5d0d1ba` (the
  accountable channel). So this plan backfills only agent-writable artifacts (the
  active plans; any draft-status track note). Canonical slug set + plan→track map
  are pinned in §6.
- **Key design choice recorded in §4/§6:** `TRACKS.md` + `DESKCHECK-QUEUE.md`
  become GENERATED (banner-on-correction); `board.py` reuses `_lib` parser, holds
  no state (docket precedent). The dc-record schema is pinned inline so `board.py`
  needs no WF-2 output — the two plans are `write_scope`-disjoint.
- **Next action (on owner bless → ready):** `/build bp-096`; start with Items 1–3
  (additive template/manifest/front-matter), then `board.py` (Item 4), then
  generate the board (Item 5, gated on a lossless-reproduction check), then the
  brief + triage surfacing (6–7). Do NOT run concurrently with bp-090.
- **Blocking:** none. Awaiting the proposed→ready blessing (owner-only, by hand).
