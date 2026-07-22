# Journal — bp-096 (WF-1: the board substrate)

> Alive while the plan is proposed/in-progress; sealed on completion.

## 2026-07-21 — BUILD START (delegated builder, worktree)

- **Worktree recovery (pre-work):** this worktree branched from an ancestor
  (`22bdaee`) that PREDATED the plan mint — `docs/build-plans/bp-096/` did not
  exist here. `HEAD` was a strict ancestor of local `main` (`28e66f2`); merge-base
  == HEAD, zero divergence, so a clean `git merge --ff-only main` brought in the
  plan + bp-097 + the owner's `5d0d1ba` ratified-note tags. No conflict possible.
  Verified the six ratified active-track notes carry their `track:` slug
  (code-ingest, inner-outer-core, sync-diac-dreamers, agentic-loop, fiber-geometry,
  workflow).
- **Grounding re-confirmed this session:** all 16 backfill plans' `design_ref`
  matches the §6 plan→track map exactly (no STOP condition). `_FRONT_MATTER_REF_KEYS`
  (`ops/code_sensor.py:126-133`) does NOT list `track:` → additive-safe. `_lib.py`
  parser: unquoted scalars keep a glued `#`, so REAL plan `track:` lines are BARE
  (no inline comment); template placeholders may carry a guidance comment.
- **Design decision recorded for board.py (from note D2 + §6):** the generated
  board renders one row per plan-member (phase computed) grouped by track lane,
  plus manifest-derived rows for no-plan tracks (reference-bookkeeper design-pass,
  track-g dormant). The free-form "next/gate" prose column of the seed is DROPPED
  (it is scheduling advice that goes stale — exactly what derivation kills; the
  falsifier guards ROWS, not columns). queue = tracks where phase==deskcheck-pending
  OR backlog_deskcheck non-null (5 today: sync/agentic/fiber pending + inner-outer +
  track-g backlog); `--queue-count` = |owed| (the §6 pin "deskcheck-pending + backlog").
- **Next:** Items 1–3 (templates, manifests, backfill) → Item 4 (board.py+test) →
  Item 5 (generate) → Items 6–7 (brief, triage).

## 2026-07-21 — ALL ITEMS COMPLETE (delegated builder)

- **Item 1 (templates + resume-brief):** `track:` key added to build-plan.md +
  design-note.md (after `id:`, with a guidance comment — placeholders, so the glued
  comment is harmless); resume-brief.md gained a `## DESKCHECKS OWED` section with a
  `Deskchecks owed: <N>` standing line. `grep -c '^track:'` = 1 each; both parse.
- **Item 2 (8 manifests):** `docs/tracks/{code-ingest,inner-outer-core,
  sync-diac-dreamers,agentic-loop,fiber-geometry,reference-bookkeeper,
  track-g-effectors,workflow}.md`. All parse `type: track`, slug==stem; track-g is
  `dormant-by-design` + `warrant: finding-0011`; code-ingest dod carries "integrator
  densification (finding-0151)". Seeded from the seed TRACKS.md rows + QUEUE backlog.
- **Item 3 (backfill):** `track:` onto the 16 active plans per the §6 map; every plan
  `git diff --numstat` == `1 0` (one added line, nothing else). All design_refs
  matched the map (no STOP).
- **Item 4 (board.py + test):** `scripts/board.py` (derived, no state, reuses `_lib`
  parser, never imports core) + `tests/unit/test_board.py` (13 tests, all pass).
  Handles the `_lib` "null"→string quirk via `_is_absent`. queue-count = 5.
- **Item 5 (generated board):** `board.py --write` regenerated TRACKS.md +
  DESKCHECK-QUEUE.md with the GENERATED banner; idempotent (2nd write byte-equal).
  **No seeded fact lost** — all 16 plan rows, integrator densification (f-0151, in
  DoD), reference-bookkeeper (design-pass row), G1–G7 dormant, and the 5 standing
  backlog deskchecks all present. **Intentional wording changes (per Item 5):**
  (a) header prose rewritten "orchestrator owns/updates" → "derived view; edit sources
  + regenerate"; (b) the free-form "next/gate" column DROPPED (scheduling advice that
  goes stale — the falsifier guards rows, not columns); (c) the stale cross-cutting
  live counts ("OQ 18 open; findings 0142–0154") dropped (docket/triage own those);
  (d) grouped seed rows (bp-079..082 as one) expanded to per-plan rows (more granular,
  all facts kept); (e) Workflow phase corrected design-pass→build (note now ratified,
  bp-096/097 ready — a CORRECT derivation update).
- **Item 6 (brief injection):** `session-brief.sh` appends `Deskchecks owed: N …`
  after `python3 "$LIB" brief`, sourced from `board.py --queue-count`, fail-open
  (shows `?` on generator error — verified live: normal→5, errored→?). Bash-side only;
  `_lib.py` untouched (WF-2's surface).
- **Item 7 (triage third inbox):** `triage.md` gained step 6 (read the queue, surface
  each owed track, regenerate if statuses changed, never flip a verdict); terse summary
  (now step 7) mentions "deskchecks surfaced (owed count)".
- **Next:** run the full green gate, then commit in logical units on the worktree
  branch (do NOT merge — orchestrator sequences merges).

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
