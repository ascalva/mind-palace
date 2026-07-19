---
type: build-plan
id: bp-072
alias: owner-cockpit
status: ready
design_ref:
  - docs/brainstorms/owner-cockpit.md      # THE SPEC — and the direct-mint warrant (line 10: "no design-note gate needed for the tooling itself")
  - docs/brainstorms/decision-routing.md   # §Sequencing v1: docket + bless CLI, zero governance change
contract: builder
write_scope:
  - scripts/cockpit.sh
  - scripts/docket.py
  - scripts/readmap.py
  - scripts/palace.py
  - docs/supplemental/cockpit.md
  - tests/unit/test_docket.py
  - tests/unit/test_readmap.py
  - tests/unit/test_bless.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 100k
  actual: null
depends_on: []
parallelizable_with: []
created: 2026-07-19
updated: 2026-07-19
links:
  - docs/brainstorms/dyadic-epistemology.md   # S2 — why the cockpit is load-bearing, not cosmetic
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — the owner cockpit (tmux reading room + docket + read maps + bless CLI; decision-routing v1)

## 0. Mode & provenance
Minted DIRECTLY from two owner brainstorms — no design note exists, deliberately: the owner's own
capture rules *"no design-note gate needed for the tooling itself"* (`owner-cockpit.md:10`), and
decision-routing's sequencing pins v1 (docket + bless CLI) as *"no governance change, papercut-tier"*.
Authority-to-act is that recorded steer; the readiness blessing stays owner-only `proposed → ready`,
**by hand** — necessarily so: the bless CLI this plan builds does not exist yet, and per
decision-routing §Security ("bootstrap self-reference"), the automation cannot approve its own
creation. bp-072 enters through the fully-manual gate, by construction.

## 1. Objective
Build the owner's reading room: `scripts/cockpit.sh` (idempotent tmux session `palace`),
`scripts/docket.py` (the derived awaiting-the-owner view + ambient count), `scripts/readmap.py`
(quickfix emitter for seal read-map blocks), the owner-run `palace bless <plan-id>` flip, and
`docs/supplemental/cockpit.md` (the dotfiles snippet block + the read-map block format) — with zero
change to gate semantics.

## 2. Context manifest
1. `docs/brainstorms/owner-cockpit.md` — the spec: interaction contract (read in vim · decide in
   dialogue · act by keystroke), reading tiers, guide-not-gate rule, dotfiles boundary, parked/open Qs.
2. `docs/brainstorms/decision-routing.md` — §Three lanes + §Sequencing (what v1 IS and is NOT) +
   §Security invariants (what must not loosen).
3. `scripts/palace.py` — the whole file (71 lines): the dispatcher `bless` joins.
4. `.claude/hooks/_lib.py:169-260, 335-348` — `parse_front_matter` / `read_front_matter` / `status_of`
   / `is_design_note` / `is_build_plan`: the artifact front-matter machinery docket REUSES.
5. `docs/inbox/owner-questions.md:1-40` — the oq entry grammar (`## oq-NNNN — title`, `- status:`,
   `- blocking:`) the docket parses.
6. `docs/build-plans/bp-073/plan.md:1-38` — the plan front-matter grammar (status/created/updated).
7. `docs/build-plans/bp-073/journal.md:185-192` — the current PROSE read map: the legacy shape
   `readmap.py` deliberately does NOT parse (motivates the structured block).
8. `CLAUDE.md` §Rules-that-bind + §Roles — the two owner-only gates and the Stop-gate audit this
   plan must leave byte-identical in behavior.

**DRY audit (required):** artifact front-matter parsing already exists in `.claude/hooks/_lib.py`
(`parse_front_matter:169`, `read_front_matter:238`, `status_of:246`, `is_build_plan:343`) —
`docket.py` imports these (sys.path insertion of `.claude/hooks`), never re-derives. `core/` owns NO
YAML-front-matter parser (`core/ingest/logseq.py` parses Logseq `key::` properties — a different
grammar; not reusable, not duplicated). Nothing here belongs in `core/`: this is repo-workflow
tooling; core self-containment cuts the OTHER way — none of these scripts may import `core`.

## 3. Investigation & grounding
- **Q1 — dispatcher shape.** `palace.py:39-67`: flat if-chain; `build_launcher` imported only after
  `seal()`. `bless` dispatches BEFORE the launcher import (it never touches the daemon).
- **Q2 — front-matter helpers exist?** Yes — `_lib.py:169,238,246,343` (cited above; reuse).
- **Q3 — oq grammar.** `owner-questions.md`: `## oq-NNNN — <title>` + `- status: open|answered|swept`
  + `- blocking: true|false`. **No per-entry date field exists** → v1 ages oqs by id order (pinned §6;
  a date field is a template change = owner's, parked §11).
- **Q4 — read-map current form.** `bp-073/journal.md:188` is prose ("Read map (concept-bearing
  lines…)"), not `file:line` spans. No structured block exists anywhere yet → `readmap.py` parses
  only the NEW fenced format; on a legacy seal it says so and exits 1 — it never guesses.
- **Q5 — the agent-session env guard.** Verified live (session-33): `CLAUDECODE` is set in Claude
  Code Bash sessions (alongside `CLAUDE_CODE_SESSION_ID` etc.). `bless` refuses when present —
  belt-and-suspenders; the Stop-gate blessing audit remains the real guard, unchanged.
- **Q6 — tmux.** 3.7b at `/opt/homebrew/bin/tmux`. `focus-events` is a server option settable at
  runtime (`tmux set -s focus-events on`) without touching any dotfile — this settles the
  brainstorm's open Q1: cockpit.sh sets it at runtime (ephemeral, repo-owned behavior), AND the
  snippet doc shows the permanent `.tmux.conf` line. The dotfiles boundary governs FILES; runtime
  state of a session the repo owns is the repo's.
- **Q7 — the generated docket's home.** `.claude/state/.gitignore` ignores everything but itself →
  `.claude/state/docket.md` is already untracked-and-ignored; no `.gitignore` edit needed.
- **Q8 — ops-window log path.** Code does not settle this here; Item 0 greps
  `ops/lifecycle/launcher.py` for the daemon log location and pins it in the journal.

**Additional risks or questions surfaced during reading:** none beyond §10.

## 4. Reconciliation
Additive throughout. `palace.py` gains one subcommand — its docstring + `USAGE` updated in the same
edit (cross-reference-on-extension, not silent). The seals-carry-read-maps process (live since
session-29, prose form) is EXTENDED with a structured block format; old seals are NOT back-filled
(§9). The checkpoint skill's one-line cross-ref to the block format is an ORCHESTRATOR act at seal
time, outside builder scope. Nothing corrected.

## 5. Write scope
As front-matter: the four scripts, the one supplemental doc, three new test files. **OUT:**
`.claude/hooks/**` and `.claude/skills/**` (process surfaces — imported/read, never edited);
`docs/build-plans/**` beyond this plan's own files (the builder NEVER flips any real plan — bless
tests run on tmp fixtures only); `ops/**` (the launcher is consumed by `palace status`, not edited);
`core/**` (never imported here); all dotfiles (the boundary rule — snippets are proposed in
`cockpit.md`, adopted by the owner's hand).

## 6. Interfaces pinned inline
```python
# scripts/palace.py — add ONE dispatch arm BEFORE the launcher import (bless never touches the daemon);
# USAGE string gains: "bless <plan-id>". Guard order is LAW:
#   1) refuse if os.environ.get("CLAUDECODE"): "agent session — blessing is owner-only" (exit 2)
#      — the check precedes ANY path resolution, so even a probe with a fake id proves the guard.
#   2) resolve docs/build-plans/<plan-id>/plan.md; missing -> exit 2.
#   3) current status must be EXACTLY "proposed"; anything else -> exit 2 (no force path exists).
#   4) flip: rewrite ONLY the `status:` line value proposed->ready and the `updated:` date —
#      line-targeted edits, NEVER a YAML round-trip (front-matter comments must survive verbatim).
#   5) print the flip ("bp-NNN: proposed -> ready").

# scripts/docket.py — the derived view; recomputed every run, NO persisted state.
def scan_docket(root: Path) -> list[DocketRow]: ...
# DocketRow: id, kind, action, sort_key, title, path
# Sources (v1, exhaustive):
#   docs/build-plans/*/plan.md   front-matter status == proposed -> "bless proposed->ready"
#   docs/design-notes/*.md       front-matter status == draft    -> "ratify (or leave working)"
#   docs/inbox/owner-questions.md entry status: open             -> "answer" (blocking flag carried)
# EXCLUDED by design: ready plans, answered oqs (agent-actionable, not owner-awaiting).
# Sort: blocking open oqs -> proposed plans -> draft notes -> non-blocking oqs; oldest first within
# class (plans/notes by created:; oqs by id ascending — Q3). Front-matter via _lib (Q2), NEVER re-derived.
# CLI: (no flag) render rows to stdout | --count print ONE integer | --write render to
# .claude/state/docket.md (the vim landing buffer; regenerable, already gitignored — Q7).

# scripts/readmap.py <plan-id> — emit the seal's read map in quickfix format.
# Finds the LAST ```read-map fenced block in docs/build-plans/<plan-id>/journal.md and emits its
# lines VERBATIM (the authoring format IS the output format — nothing transforms, nothing drifts).
# A listed path that no longer exists -> WARNING to stderr, line still emitted. No block -> exit 1
# with "no structured read-map block (legacy prose seal?)" — it never parses prose.

# The read-map block format (seals author this from now on; spec lives in docs/supplemental/cockpit.md):
#   ```read-map
#   eval/harness/re_measure.py:41: the co-production projection — fail-loud witness
#   tests/unit/test_re_measure.py:118: the falsifier worth reading
#   ```
# i.e. quickfix lines "path:line: why", vim-consumed as :cfile + ]q.

# scripts/cockpit.sh — idempotent: join the "palace" session if it exists, else build it.
#   Joining is $TMUX-aware: OUTSIDE tmux -> `tmux attach -t palace`; INSIDE another session ->
#   `tmux switch-client -t palace` (attach would nest — the owner jumps sessions with prefix+s/L,
#   so in-tmux invocation is the NORMAL case, not an edge).
#   window "desk": left pane `nvim .claude/state/docket.md` (after `uv run scripts/docket.py --write`),
#                  right pane `claude`; panes rooted at repo root (derived from the script's own path).
#   window "ops":  `uv run scripts/palace.py status` + daemon log tail (path pinned at Item 0).
#   status-right: #(cd <root> && uv run scripts/docket.py --count) awaiting · status-interval 60
#   runtime: tmux set -s focus-events on   (Q6 — no dotfile touched)
#   --dry-run: print every tmux command it WOULD run, execute none (the testable surface).
```

## 7. Items

### Item 0 — ground the leans  (blast: none — reading + journal)
- **Objective:** confirm the §6 leans against the live tree before code.
- **Files:** journal only.
- **Acceptance test:** journal entry pinning: the daemon log path for the ops window (Q8); a live
  `_lib.read_front_matter` call succeeding on one real plan, note, and the oq file's entry grammar;
  `.claude/state/.gitignore` coverage re-confirmed.
- **Falsifier:** a §6 lean contradicted by the live tree that survives into Items 1–4 unamended.
- **Invariant(s):** read-only. **Touches stored data?** no. **Parallelizable?** no. **Depends on:** none.

### Item 1 — docket.py + tests  (blast: new script, read-only sensor)
- **Objective:** the derived awaiting-the-owner view, count mode, write mode.
- **Files:** `scripts/docket.py`, `tests/unit/test_docket.py`.
- **Acceptance test:** `uv run pytest tests/unit/test_docket.py -q` green: fixture tree exercises all
  three sources; ready plans + answered/swept oqs EXCLUDED; blocking oq sorts first; `--count` prints
  one integer; `--write` emits the file. Live smoke: `uv run scripts/docket.py` on the real repo
  exits 0 and lists a known-open row (e.g. oq-0003).
- **Falsifier:** any persisted docket state (the view must be recomputed from artifacts every run —
  "never hand-maintained ⇒ cannot drift"); a row for an agent-actionable state; docket re-implementing
  front-matter parsing instead of importing `_lib` (the DRY falsifier); an import of `core`.
- **Invariant(s):** derives, never mutates; no network. **Touches stored data?** no.
  **Parallelizable?** yes (with 2, 3). **Depends on:** Item 0.

### Item 2 — readmap.py + tests + the block-format spec  (blast: new script + doc section)
- **Objective:** quickfix emission of seal read-map blocks; the format specified once.
- **Files:** `scripts/readmap.py`, `tests/unit/test_readmap.py`, the format section of
  `docs/supplemental/cockpit.md`.
- **Acceptance test:** tests green: two-block fixture journal → LAST block emitted verbatim;
  no-block fixture → exit 1 with the legacy message; missing-path line → stderr warning, line still
  emitted. `uv run scripts/readmap.py bp-073` exits 1 (bp-073's read map is prose — honest).
- **Falsifier:** readmap parsing legacy prose "helpfully" (guessing is the trust-surface violation —
  guide-not-gate demands the full diff stay one command away, not a cleverer filter); ANY transform
  between authored block lines and emitted output.
- **Invariant(s):** verbatim emission; read-only. **Touches stored data?** no.
  **Parallelizable?** yes (with 1, 3). **Depends on:** Item 0.

### Item 3 — `palace bless` + tests  (blast: repo-file mutation, owner-run, reversible)
- **Objective:** the owner's one-command blessing flip, structurally refused to agents.
- **Files:** `scripts/palace.py`, `tests/unit/test_bless.py`.
- **Acceptance test:** tests green on **tmp_path fixtures only**: proposed→ready flip lands;
  ready/complete/missing → exit 2; `CLAUDECODE` set (monkeypatched) → refusal; a front-matter
  comment on an adjacent line survives byte-identical (no YAML round-trip). LIVE demo from the build
  session: `uv run scripts/palace.py bless bp-nonexistent` refuses with the agent-session message
  (guard fires BEFORE path resolution — proven with a fake id, zero flip risk).
- **Falsifier:** `git status docs/build-plans` shows ANY real plan modified during this item (a
  blessing-gate breach the Stop-gate would also catch — the item fails outright); a force/override
  flag existing at all; the launcher imported on the bless path.
- **Invariant(s):** the two owner-only gates and the Stop-gate audit unchanged in behavior; no new
  agent capability minted. **Touches stored data?** no (repo files only).
  **Parallelizable?** yes (with 1, 2). **Depends on:** Item 0.

### Item 4 — cockpit.sh + docs/supplemental/cockpit.md  (blast: new script + doc; no dotfile)
- **Objective:** the tmux reading room + the snippet block the owner adopts by hand.
- **Files:** `scripts/cockpit.sh`, `docs/supplemental/cockpit.md`.
- **Acceptance test:** `bash -n scripts/cockpit.sh` clean; `--dry-run` prints the §6 layout (session
  `palace`, desk + ops windows, status-right count hook, runtime focus-events) executing nothing, and
  its has-session branch shows join-not-rebuild, $TMUX-aware (attach outside tmux, switch-client
  inside — idempotence and non-nesting both legible in the dry run). `cockpit.md`
  carries: the snippet block (autoread, permanent focus-events line, `<leader>pb` → `palace bless`,
  the `:cfile` read-map recipe, render-markdown suggestion), the read-map format spec (Item 2), the
  guide-not-gate rule stated verbatim, and a session-switching tips line (`prefix+s` choose-tree,
  `prefix+L` last-session toggle — the owner's cmd+tab between their session and `palace`; owner
  steer 2026-07-19).
- **Falsifier:** cockpit.sh writing ANY path outside the repo (the dotfiles boundary); requiring the
  daemon to be up to open the cockpit; setting any tmux server option other than `focus-events`;
  a second run minting a second session.
- **Invariant(s):** repo owns session + data, dotfiles own the editor. **Touches stored data?** no.
  **Parallelizable?** no (consumes 1's `--write` and 3's bless in the snippet). **Depends on:** Items 1, 3.

## 8. Math carried explicitly
N/A — no mathematical object implemented (the docket sort is a lexicographic key, not a measure).

## 9. Non-goals
NO stakes typing, policy note, checker, ledger, audit gauge, or any auto-approval — that is
decision-routing v2 and REQUIRES ratification (the gate this plan must not creep toward). NO
`palace.lua` / `:Palace*` user-commands (v1.5, parked). NO dotfile writes, ever. NO change to
gate-guard / scope-guard / Stop-gate semantics. NO back-fill of legacy prose read maps. NO docket
rows for agent-actionable states. NO daemon coupling (the cockpit opens with Ouroboros down).

## 10. Stop-and-raise conditions
- A needed surface outside `write_scope` → STOP, scope-amendment finding; never route around.
- ANY real artifact status flip in-session, however caused → hard STOP (blessing gate).
- A docket source whose front-matter `_lib` cannot parse → `codebase` finding (grammar drift), park
  that source, continue the rest.
- tmux behavior that cannot be verified headless → pin in the dry-run surface, park live tuning to
  the first cockpit session (§11), and proceed — not a blocker.
- Any blessing: never.

## 11. Parked decisions
| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| desk layout / sizes / focused pane | vim left on docket, claude right, ~50/50 | dashboard-first (plugin dep, dotfiles-side) | first cockpit session — owner taste, then pinned in cockpit.sh |
| landing buffer | `.claude/state/docket.md` | snacks.nvim dashboard (a dotfiles concern, not repo's) | owner taste at first session |
| `palace.lua` plugin | documented snippets only | plugin now (unproven stickiness) | snippets prove sticky and owner wants native commands |
| read-map authoring | hand-written per seal, block format | derive-from-diff automation (unproven need, trust surface) | authoring cost proves annoying → finding |
| oq age source | id-order proxy | per-entry date field (an owner template change) | owner adds `asked:` to the oq template |

## 12. Dependency & ordering summary
No plan dependencies (leaf; disjoint from every active surface). Item 0 → Items 1, 2, 3 (mutually
parallelizable, one session so sequential in practice) → Item 4 (consumes 1 + 3). All writes are
repo-local and git-reversible; the only workflow-artifact mutation (`bless`) is owner-run by
construction and structurally refused to agents (Q5). Downstream: decision-routing v2 (policy +
checker + gauge) builds on the docket's view once RATIFIED; the cockpit is its reading room either way.
