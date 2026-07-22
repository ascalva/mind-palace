---
type: build-plan
id: bp-096
track: workflow
status: proposed
design_ref:
  - docs/design-notes/track-board-and-deskcheck-gate.md
contract: builder
write_scope:
  - docs/templates/build-plan.md
  - docs/templates/design-note.md
  - docs/templates/resume-brief.md
  - docs/tracks/**
  - docs/TRACKS.md
  - docs/DESKCHECK-QUEUE.md
  - docs/build-plans/*/plan.md
  - scripts/board.py
  - tests/unit/test_board.py
  - .claude/hooks/session-brief.sh
  - .claude/commands/triage.md
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 300k
  actual: null
depends_on: []
parallelizable_with: []
created: 2026-07-21
updated: 2026-07-21
links:
  - docs/design-notes/track-board-and-deskcheck-gate.md
  - docs/findings/finding-0153.md
  - docs/findings/finding-0151.md
  - scripts/docket.py
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — WF-1: the board substrate

> Every section below is required; an inapplicable one is `N/A — <reason>`.

## 0. Mode & provenance

Investigation and planning produced this plan (graduation of the ratified
`dn-track-board-and-deskcheck-gate`, §3's WF-1). Implementation proceeds
item-by-item on owner approval. Authority-to-act (the owner ruled "build this
before bp-090") is separate from the readiness blessing (owner-only
proposed→ready); no agent flips readiness. This plan stands up the *board
substrate* — the `track:` coordinate, the track manifests, and the derived
generator — but installs **no gate** (the deskcheck verdict gate is WF-2/bp-097).

## 1. Objective

Make the track board a **derived** artifact: `scripts/board.py` recomputes
`docs/TRACKS.md` + `docs/DESKCHECK-QUEUE.md` from the artifact tree (a `track:`
front-matter coordinate + per-track `docs/tracks/<slug>.md` manifests), so the
board can no longer go stale, and the owed-deskcheck count surfaces every session.

## 2. Context manifest

Read these, in order, before any work:

1. `docs/design-notes/track-board-and-deskcheck-gate.md` — the whole note; D1
   (coordinate), D2 (derived board + phase function), D4 (surfacing), D8
   (state-vs-log). §3 licenses this plan; §2.9 is the property→tooth map.
2. `scripts/docket.py` — the DERIVED-view precedent copied verbatim in spirit:
   the no-persisted-state docstring stance (`:1-21`), the `_lib.py` parser reuse
   (`:32-37`), the `--count`/`--write` idioms (`:194-206`), the grouped render
   with short item lines (`:161-191`). `board.py` is this pattern, second view.
3. `.claude/hooks/_lib.py` — `parse_front_matter`, `_normalize_status`
   (reused by `board.py`, never re-derived); `cmd_brief` (`:748-801`) is the
   SESSION BRIEF composer the owed-count line joins conceptually (the actual
   injection lands in `session-brief.sh`, §7 Item 6).
4. `.claude/hooks/session-brief.sh` — `:47-56`: it `cat`s the resume brief, then
   runs `python3 "$LIB" brief`, then records `session-baseline`. The owed line
   is appended here (Bash-side, fail-open), not in `_lib.py`.
5. `docs/TRACKS.md` + `docs/DESKCHECK-QUEUE.md` — the hand-authored seeds. Their
   *content* (swim-lane rows, the DoD lines, the standing-backlog rows) is the
   truth `board.py` must reproduce; their *header prose* ("the orchestrator owns
   this board and updates it every seal") is what derivation corrects.
6. `docs/templates/{build-plan,design-note,resume-brief}.md` — the three
   templates that gain the `track:` key / the owed line.
7. `.claude/commands/triage.md` — the reflection sweep; gains the third inbox.
8. `ops/code_sensor.py:126-131` — `_FRONT_MATTER_REF_KEYS`; confirms `track:`
   mints no citation edge (additive-safe).

## 3. Investigation & grounding

- **Q1 — Can a builder backfill `track:` onto the active-track design notes?**
  **No — and it must not try.** All five active-track notes are `ratified`
  (`code-ingest-pipeline`, `inner-outer-core`, `synchronic-diachronic-dreamer`,
  `agentic-loop`, `fiber-geometry`), and `cmd_scope_check` denies any write to a
  ratified note (`_lib.py:390-398`), with Stop clause (b2) as the HEAD-keyed
  backstop (`_lib.py:634-645`). **Resolved out-of-band:** the owner hand-tagged
  the six ratified active-track notes (the sixth being this note itself) in commit
  `5d0d1ba` — an accountable owner edit, the correct channel for a ratified file.
  So the notes already self-declare `track:`; this plan backfills only the
  *agent-writable* artifacts (the build plans; any draft-status track notes).
- **Q2 — Is `track:` additive-safe against existing front-matter consumers?**
  Yes. `scope-guard` reads only `write_scope`; `docket.py` reads only `status`;
  `code_sensor._FRONT_MATTER_REF_KEYS` (`ops/code_sensor.py:126-131`) lists
  `design_ref/links/depends_on/warrant/supersedes/superseded_by` — `track:` is
  absent, and it is a slug not a path, so φ_doc mints no edge. Verified live:
  `parse_front_matter` on the six tagged notes returns `track` alongside
  `status` with no error (this session).
- **Q3 — Backfilling `track:` onto plans: any gate risk?** No. Adding a `track:`
  line changes no `status`, so `cmd_gate_check_hook` (`_lib.py:448-469`) reads
  `new_status = None` → ALLOW; `scope-guard` allows any build-plan write inside
  `write_scope` (build plans are not status-immutable — only design notes are).
- **Q4 — Which plans are backfilled?** The active-track plans:
  `bp-079,080,081,082,083,085,086,087,088,089,090,091,092,093,094,095`.
  (`bp-096`/`bp-097` are minted already carrying `track: workflow`, so the sweep
  skips them.) The plan→track map is in §6.
- **Q5 — Where does the owed-count come from?** `board.py --queue-count` (a new
  `--count`-style idiom, mirroring `docket.py:196-198`), consumed by
  `session-brief.sh`. `board.py` computes the queue = tracks whose phase is
  `deskcheck-pending`, plus the standing-backlog rows the manifests carry.
- **Q6 — Does any test pin a surface this plan moves?** No. `test_docket.py`
  is `track:`-agnostic (parses `status` only); nothing asserts the templates,
  `session-brief` output, or `triage.md` text. `board.py`'s test is new
  (`tests/unit/test_board.py`, mirroring `test_docket.py`).

**Additional risks surfaced during reading:** the note says "seven current
tracks" (§3) but the seed board lists **eight** swim lanes (Code-ingest,
Inner/outer-core, Sync/diac-dreamers, Reference-bookkeeper, Agentic-loop,
Fiber-geometry, Track-G/effectors, Workflow). The discrepancy is that Workflow
is itself the track being built. **Resolved:** author a manifest per swim lane
(eight), including `workflow` — completeness beats matching a round number; noted
in §11.

## 4. Reconciliation

- `docs/TRACKS.md` + `docs/DESKCHECK-QUEUE.md` — **[banner: correction]**. Today
  hand-maintained; their headers say "the orchestrator owns this board and
  updates it every seal + `/triage`". This plan makes them **generated**. Each
  file gains, as its first line, the banner
  `<!-- GENERATED by scripts/board.py — do not hand-edit -->` and the header prose
  is rewritten to "a derived view; edit the manifests / front matter, then
  regenerate." The *content* (rows, DoD, backlog) is preserved by reproduction —
  the generator is not allowed to lose a seeded fact (Item 4 acceptance).
- `docs/templates/{build-plan,design-note}.md` — **[cross-ref: extension]**. Add
  an additive `track:` front-matter key with a one-line comment
  `# the board coordinate — dn-track-board-and-deskcheck-gate (D1)`. No existing
  key changes; the key is optional-by-consumers (Q2).
- `docs/templates/resume-brief.md` — **[cross-ref: extension]**. Add a standing
  `Deskchecks owed: N (top: …)` line to the brief shape (D4; already practiced
  this session, now durable).
- `.claude/hooks/session-brief.sh` — **[cross-ref: extension]**. Append the
  owed-count line after `python3 "$LIB" brief`, sourced from
  `board.py --queue-count`, fail-open (a generator error never breaks the brief).
- `.claude/commands/triage.md` — **[cross-ref: extension]**. Add a third inbox
  (owed deskchecks) to the sweep, beside findings and OQ.

## 5. Write scope

- `docs/templates/build-plan.md`, `docs/templates/design-note.md`,
  `docs/templates/resume-brief.md` — the three template additions (§4).
- `docs/tracks/**` — new per-track manifests (Item 2).
- `docs/TRACKS.md`, `docs/DESKCHECK-QUEUE.md` — regenerated from the tree (Item 5).
- `docs/build-plans/*/plan.md` — the `track:` backfill onto the active plans
  (Item 3). Broad glob because the sweep touches ~16 plan files; the builder
  edits *only* the `track:` line on each (Q3/Q4). It must not touch `journal.md`
  of other plans, nor any `status`/`design_ref` line.
- `scripts/board.py` + `tests/unit/test_board.py` — the generator + its test.
- `.claude/hooks/session-brief.sh` — the owed-count injection (Item 6).
- `.claude/commands/triage.md` — the third inbox (Item 7).

**Deliberately OUT of scope:** every `docs/design-notes/**` file (ratified notes
are owner-tagged already, Q1; draft-note tagging that *is* agent-writable is
in-scope only if a draft note heads an active track — e.g. Track-G's note — via
its own path, and only if that note is `draft`); `.claude/hooks/_lib.py` (WF-2's
surface; the brief injection is deliberately Bash-side to keep the two plans
disjoint); the deskcheck template / `docs/deskchecks/**` / any gate (WF-2); the
foundation denylist; `PROGRESS.md` / `PARKING-LOT.md` (D8 consolidation is a
later lazy migration, §11).

## 6. Interfaces pinned inline

**The DERIVED-view stance (copy `docket.py`'s posture verbatim in spirit):**
`board.py` holds NO persisted state; it recomputes from the tree every run, so it
cannot drift (that IS the enforcement, §2.9). It reuses `_lib.py`'s parser — never
a second YAML parser — via:
```
import sys; from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / ".claude" / "hooks"))
from _lib import parse_front_matter, _normalize_status   # noqa: E402
```

**CLI idioms (mirror `docket.py:194-206`):**
```
uv run scripts/board.py                # render both views to stdout (for inspection)
uv run scripts/board.py --write        # write docs/TRACKS.md + docs/DESKCHECK-QUEUE.md
uv run scripts/board.py --queue-count  # print ONE integer: # tracks in deskcheck-pending + backlog
```

**Track manifest schema — `docs/tracks/<slug>.md` (this plan defines it):**
```
---
type: track
slug: <kebab>                 # MUST equal the artifacts' `track:` value and the filename stem
title: <human title>
status: active | dormant-by-design
warrant: <finding-id>         # REQUIRED iff status is dormant-by-design (e.g. finding-0011)
audit_refs: []                # appended when an audit finding lands (the phase's audit flag)
dod:                          # definition-of-done checklist — a deskcheck evaluates against this
  - <item>                    #   e.g. code-ingest: "integrator densification (finding-0151)"
backlog_deskcheck: <one-line owed-deskcheck statement, or null>   # seeds the QUEUE backlog rows
links: []
---
# Track — <title>
<body: the identity card — scope, the DoD as prose, the owed-deskcheck statement>
```

**Deskcheck-record front matter `board.py` must parse (defined by WF-2; pinned
here so `board.py` reads verdicts without depending on WF-2's build order) —
from the note D3 verbatim:**
```
{type: deskcheck, id: dc-NNN, track: <slug>, date, items: [plan ids],
 audit_refs: [...], verdict: pending | approved | needs-work,
 send_back: <phase — only on needs-work>, links: [...]}
```
`board.py` treats a track as CLOSED iff an `approved` `dc-NNN` names it AND its
manifest `dod` items are closed. No dc records exist yet, so the common path is
"no dc → deskcheck-pending"; `board.py` must not error on an empty
`docs/deskchecks/`.

**The phase function (compute per track — from the note D2 table verbatim):**

| computed condition (front matter + dc records) | phase |
|---|---|
| a linked note is `draft` | design-pass |
| notes `ratified`, some licensed plans not yet minted or `proposed` | graduate |
| any plan `ready`/`in-progress` | build |
| all minted plans `complete`, no approved dc record | deskcheck-pending |
| an approved `dc-NNN` names the track and its DoD items closed | CLOSED |
| manifest `status: dormant-by-design` + its warrant | dormant |

The **audit** flag rides inside `deskcheck-pending` ("audit: present/owed") from
the manifest's `audit_refs`. Audit depth is risk-proportional (delegated/lower
tier ⇒ independent Opus pass; supervised same-tier merge ⇒ merge scrutiny IS the
audit) — the recording rule; WF-2 records the right-sizing prose in delegate.

**Row-width rule (owner, 2026-07-21):** every rendered table row ≤ **190 chars**.
Keep cells terse; put detail in prose beneath the table.

**Plan → track map for the Item-3 backfill:**
```
code-ingest        : bp-092 bp-093 bp-094 bp-095
inner-outer-core   : bp-083 bp-089 bp-090 bp-091
sync-diac-dreamers : bp-079 bp-080 bp-081 bp-082
agentic-loop       : bp-086 bp-087 bp-088
fiber-geometry     : bp-085
```
(Track-G/effectors, reference-bookkeeper: no active plans to backfill — carried
by manifest only. Verify each plan's `design_ref` against the map before tagging;
if a plan's `design_ref` disagrees, STOP and raise, don't guess.)

## 7. Items

### Item 1 — `track:` key into the two templates + resume-brief owed line
- **Objective:** the templates carry the additive coordinate; the resume-brief
  shape carries a standing owed-deskchecks line.
- **Files:** `docs/templates/build-plan.md`, `docs/templates/design-note.md`,
  `docs/templates/resume-brief.md`.
- **Acceptance test:** `grep -c '^track:' docs/templates/build-plan.md
  docs/templates/design-note.md` prints 1 each; the resume-brief template contains
  a `Deskchecks owed:` line. Both templates still parse via `parse_front_matter`.
- **Falsifier:** adding `track:` to the templates reddens `test_docket.py` or any
  front-matter consumer ⇒ the key is not additive-safe after all (contra Q2).
- **Invariant(s):** no existing template key changes; comment rationale on the key,
  never inline on a `write_scope` glob (bp-066).
- **Touches stored data?** No.  **Parallelizable?** Yes.  **Depends on:** none.

### Item 2 — author `docs/tracks/<slug>.md` manifests (eight tracks)
- **Objective:** each active track has an identity card carrying title, status,
  DoD, and the owed-deskcheck statement.
- **Files:** `docs/tracks/{code-ingest,inner-outer-core,sync-diac-dreamers,
  agentic-loop,fiber-geometry,reference-bookkeeper,track-g-effectors,workflow}.md`.
- **Acceptance test:** eight files exist, each parses via `parse_front_matter`
  with `type: track` and a `slug` equal to the filename stem; `track-g-effectors`
  carries `status: dormant-by-design` + `warrant: finding-0011`; `code-ingest`'s
  `dod` lists "integrator densification (finding-0151)".
- **Falsifier:** a manifest's `slug` disagrees with an artifact's `track:` value
  for the same body of work (F-WF1) ⇒ the coordinate split; `board.py`'s orphan
  report (Item 4) must surface it.
- **Invariant(s):** DoD/statement content is *seeded from* the current TRACKS.md
  rows + DESKCHECK-QUEUE.md backlog — reproduce the seeded truth, invent nothing.
- **Touches stored data?** No.  **Parallelizable?** Yes.  **Depends on:** none.

### Item 3 — backfill `track:` onto the active build plans
- **Objective:** every active-track plan self-declares its track.
- **Files:** the 16 `docs/build-plans/<id>/plan.md` in the §6 map.
- **Acceptance test:** for each id in the map, `grep -c '^track:' plan.md` is 1
  and the value equals the map; `git diff --numstat` shows `1 0` per plan (one
  added line, nothing else).
- **Falsifier:** any plan diff touches a line other than the added `track:` ⇒ the
  sweep overreached; revert and narrow.
- **Invariant(s):** no `status`/`design_ref` line touched; `bp-096`/`bp-097`
  skipped (already tagged).
- **Touches stored data?** No.  **Parallelizable?** Yes.  **Depends on:** none.

### Item 4 — write `scripts/board.py` + `tests/unit/test_board.py`
- **Objective:** the derived generator: renders both views, computes the phase
  per track, reports orphans, caps rows at 190 chars, and exposes `--write` /
  `--queue-count`.
- **Files:** `scripts/board.py`, `tests/unit/test_board.py`.
- **Acceptance test:** `uv run scripts/board.py` runs clean; `test_board.py`
  asserts (a) **idempotence** — two renders over an unchanged tree are byte-equal
  (F-WF2); (b) every rendered row ≤190 chars; (c) `--queue-count` prints an
  integer equal to the deskcheck-pending count; (d) an **orphan report** lists any
  `track:` slug with no manifest, or manifest with no members (F-WF1). `uv run
  ruff check scripts/board.py` and `mypy` (scripts floor 0) pass.
- **Falsifier:** two consecutive runs over an unchanged tree differ, or the output
  disagrees with an artifact's front matter (F-WF2) ⇒ the generator is
  stateful/buggy — fix the generator, never hand-edit output.
- **Invariant(s):** no persisted state; reuse `_lib.parse_front_matter`, never a
  second parser; never import `core` (repo-workflow tooling, mirror `docket.py`).
- **Touches stored data?** No (reads the tree; writes only under `--write`).
  **Parallelizable?** No.  **Depends on:** Items 2, 3 (needs manifests + tagged
  plans to render truthfully) + the owner's `5d0d1ba` note tags.

### Item 5 — generate `docs/TRACKS.md` + `docs/DESKCHECK-QUEUE.md`
- **Objective:** replace the hand-authored board files with `board.py --write`
  output carrying the do-not-hand-edit banner.
- **Files:** `docs/TRACKS.md`, `docs/DESKCHECK-QUEUE.md`.
- **Acceptance test:** both files begin with the GENERATED banner; a fresh
  `board.py --write` reproduces them byte-for-byte (`git diff` empty on a second
  run); **no seeded fact is lost** — every swim-lane row and every backlog row
  present in the hand-authored seed appears in the generated output (diff-review
  the pre/post content, list any intentional wording change in the journal).
- **Falsifier:** the generated board drops or contradicts a row the seed carried
  (e.g. a track vanishes, or the five standing backlog deskchecks shrink) ⇒
  reproduction is lossy; the manifests/generator are under-seeded — fix before seal.
- **Invariant(s):** the generated files are never hand-edited thereafter (the
  banner says so; the discipline is D2).
- **Touches stored data?** No (docs).  **Parallelizable?** No.  **Depends on:** 4.

### Item 6 — `session-brief.sh` owed-count injection
- **Objective:** every session's opening block carries `Deskchecks owed: N`.
- **Files:** `.claude/hooks/session-brief.sh`.
- **Acceptance test:** a bare session's SESSION BRIEF (or the appended line after
  it) shows `Deskchecks owed: <N>` matching `board.py --queue-count`; with
  `board.py` made to error, the brief still emits (fail-open) and the line is
  omitted or shows a `?`.
- **Falsifier:** a session opens while a deskcheck is owed and no owed-count line
  appears (F-WF4) ⇒ the injection broke; surfacing regressed to memory.
- **Invariant(s):** fail-open, fail-loud (never break the brief on a generator
  error); the injection is Bash-side (does not touch `_lib.py`).
- **Touches stored data?** No.  **Parallelizable?** Yes (after Item 4 exists).
  **Depends on:** 4 (needs `--queue-count`).

### Item 7 — `/triage` third inbox
- **Objective:** the reflection sweep routes/surfaces owed deskchecks beside
  findings and OQ.
- **Files:** `.claude/commands/triage.md`.
- **Acceptance test:** `triage.md` contains a step that reads the deskcheck queue
  (`board.py --queue-count` / `DESKCHECK-QUEUE.md`) and surfaces each owed item;
  the terse-summary step (`triage.md:32`) mentions deskchecks.
- **Falsifier:** a `/triage` run completes without ever mentioning owed
  deskchecks while the queue is non-empty ⇒ the sweep skips the third inbox.
- **Invariant(s):** the orchestrator stays single-writer of the surfaces triage
  touches; this adds a read+surface step, not a new writer.
- **Touches stored data?** No.  **Parallelizable?** Yes.  **Depends on:** none.

## 8. Math carried explicitly

N/A — no mathematical object implemented (a text generator + front-matter sweep).

## 9. Non-goals

- No board UI, sqlite, or persisted state (P-WF3) — markdown + generator only.
- No change to any gate: not the two blessing gates, not scope-guard, not the
  deskcheck verdict gate (that is WF-2/bp-097).
- No editing of ratified design notes (owner-tagged already in `5d0d1ba`).
- No D8 consolidation sweep of `PROGRESS.md` / `PARKING-LOT.md` — those migrate
  lazily, each when its track is next touched (§11); this plan does not rewrite them.
- No dc records authored (they are owner sessions off the queue).

## 10. Stop-and-raise conditions

- A plan's `design_ref` disagrees with the §6 plan→track map ⇒ STOP, raise (don't
  guess the track).
- `board.py` finds an active-track artifact whose note is ratified **but
  untagged** ⇒ it must *orphan-report*, never fail or attempt to edit the note
  (that write is denied); surface for the owner to hand-tag.
- Any discovered need to change a gate, a ratified note, or a blessing ⇒ STOP
  (this plan installs no gate; that is a spec boundary, file a finding).
- A blast-radius surprise in Item 5 (generation would lose a seeded fact and the
  manifests can't be seeded to recover it) ⇒ STOP and raise before overwriting.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| Board as web UI / sqlite (P-WF3) | markdown + generator | central registry drifts (docket lesson); sqlite is machinery ahead of need | board ≫ ~20 concurrent tracks, or phone needs it interactive |
| Findings carry `track:` (P-WF5) | optional / omitted | forcing it now adds a key nothing consumes | `/triage` finds routing needs it |
| D8 consolidation (PROGRESS→log, PARKING-LOT→manifests) | lazy per-track migration | a big-bang sweep is out of this plan's scope + risk | a track is next touched (migrate its rows then) |
| "seven vs eight" tracks | author 8 manifests incl. `workflow` | matching "seven" would orphan the workflow track's own artifacts | n/a — resolved |

## 12. Dependency & ordering summary

- **Blast-radius order:** Items 1–3 (additive template/manifest/front-matter
  edits — lowest radius) → Item 4 (`board.py`, read-only over the tree) → Item 5
  (overwrites the two board docs — highest radius, gated on a lossless
  reproduction check) → Items 6–7 (process-surface edits).
- **Edges:** 1, 2, 3, 7 are mutually independent and parallelizable within the
  session; 4 depends on 2 + 3 (+ owner tags in `5d0d1ba`); 5 depends on 4; 6
  depends on 4 (`--queue-count`).
- **Cross-plan:** independent of **bp-097 (WF-2)** — disjoint `write_scope`
  (WF-1 owns `session-brief.sh` + `triage.md` + templates + board files; WF-2
  owns `_lib.py` + `gate-guard.sh` + checkpoint/delegate skills + the deskcheck
  template). The dc-record schema WF-2 defines is pinned inline (§6) so `board.py`
  needs no WF-2 output. **Must NOT run concurrently with bp-090** (both touch
  `scripts/**`; the note §3). Owner blesses proposed→ready item-by-item.
