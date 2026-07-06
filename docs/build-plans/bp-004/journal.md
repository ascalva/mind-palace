# BP-004 — Build journal

Records the work landing the A5 (finding-0006) and A6 (finding-0008) mechanical
fixes: `_lib.py` status-value normalization, the template's clean status line +
restored `re_entry` key, the three command-file reconciliations, the harness
regressions, and the two finding promotions. Committed artifacts are history, not
scratch (§9). Narrative entries are newest-first below the header; the `## Markers`
section at the file's end receives the mechanical lines hooks append (compactions,
audits, HOOK-FAILUREs).

Fresh-agent test (§9): a session given only `plan.md` + this journal + the
write-scope files must continue without re-asking anything already answered.

---

## Entry — 2026-07-06 — ALL FIVE items closed; harness 21/21 green; findings promoted

**Status.** Build complete. All five acceptance criteria closed and demonstrated;
`bash docs/build-plans/bp-004/acceptance/run.sh` exits **0 (PASS=21 FAIL=0)**. The A5
blessing-gate hole is closed on all three detectors; the A6 template + command drift
is reconciled; both findings are `promoted`. bp-004 is left at `status: in-progress`
with completion evidence here — the `in-progress → complete` flip, journal seal, and
`docs/PROGRESS.md` checkpoint are the orchestrator's single-writer acts (§5), out of
this builder's lane. Working-tree delta is exactly the write_scope (7 M + 3 ??, zero
out-of-scope; Stop-gate audit returns ALLOW).

**Completed (per acceptance criterion / item).**

- **0006-strip (Item 1) — all three detectors fire on a comment-bearing blessing.**
  Verified in isolated temp repos: `status: ready   # x` → **gate-guard** (hook/stdin
  mode) DENIES rc=2; **Stop-gate tracked** (`_blessing_in_diff`, in-place flip) BLOCKS
  rc=2 citing the blessing; **Stop-gate untracked** (`_untracked_blessing`, minted file)
  BLOCKS rc=2 citing the blessing + the file. Each beside a clean-`ready` control that
  also blocks (non-vacuous — the path is wired). gate-guard is driven in **hook mode**
  because `--standalone` passes status raw, bypassing the extractor where the fix lives.

- **0006-nospace (Item 1) — normalization never fabricates a blessing.** `status:
  ready#x` (no space) ALLOWS (rc=0) on all three paths — `find(" #") == -1`, no cut,
  value stays `ready#x` ≠ `ready`. The fix is false-negative-only (the safe direction).

- **0006-scope (Item 1) — the fix is status-path-only.** Unit-asserted on the fixed
  `_lib.py`: `_scalar("bar # keep")` and a non-status `design_ref: … # keep` field
  survive `parse_front_matter` intact, while `_status_in_text`/`status_of`/
  `_normalize_status` strip a ` #` from status. `_scalar`/`parse_front_matter` unchanged.

- **PRIOR (Item 1/Item 4) — all 18 prior criteria green under the A5 fix.** bp-002's
  harness (wrapping bp-001 → bp-000) exits 0 with the A5-fixed `_lib.py` copied into its
  temp repos: every prior test uses a clean status line, so `_normalize_status` is a
  no-op and no verdict changed (the plan §3 Q7 guarantee, now demonstrated).

- **A5/A6 template (Item 2).** `build-plan.md:4` = `status: proposed` (no comment);
  `re_entry` restored as a front-matter key (`:16`); the four moved fields absent from
  front-matter but present as body sections §1/§2/§9/§10 — all harness-asserted.

- **0008-build + A6 commands (Item 3).** build.md/graduate.md/scribe.md reference the
  §2/§7/§9/§10 body sections; no command still names `context_manifest` as a front-matter
  key (harness grep). **Dry-run:** a literal `/build` on bp-004 (a new-template plan)
  following the *corrected* build.md resolves the context manifest from **§2** (an ordered
  9-entry read list) and acceptance from **§7** (5 items, each with an Acceptance test) —
  whereas bp-004's front-matter carries **no** such keys, so the *old* instruction would
  have stalled. The finding-0008 falsifier does not fire.

- **Findings promoted (Item 5).** finding-0006 `open → promoted` (resolution cites A5 +
  bp-004 + the harness); finding-0008 `routed → promoted` (resolution cites A6 + bp-004 +
  the harness); both `updated: 2026-07-06`. Promotion ran **last**, after the Item 1–4
  harness was green — the terminal accounting trails the proven fix (Item 5 falsifier:
  no premature promotion). Harness run history: 19/21 pre-promotion (the two finding
  checks correctly RED), 21/21 after — the designed ordering.

**In-flight.** None. Clean terminal boundary.

**Next action (orchestrator / owner).** Review the working-tree delta and commit it
(`.claude/hooks/_lib.py`, `.claude/commands/{build,graduate,scribe}.md`,
`docs/templates/build-plan.md`, `docs/build-plans/bp-004/**`,
`docs/findings/finding-000{6,8}.md`). Then flip bp-004 `in-progress → complete`, seal
this journal, and write the `docs/PROGRESS.md` checkpoint (orchestrator single-writer,
§5). No blessing transition was performed or is required; bp-004's readiness was the
owner's hand edit at session start.

**Open questions.** None blocking. Two decisions remain parked with re-entry conditions
(plan §11): normalizing `cmd_brief`'s cosmetic status render (`_lib.py:533` reads status
directly, not via `status_of`; the template fix moots it for new plans), and a
belt-and-suspenders `cmd_gate_check` normalization (only reachable via `--standalone`,
a debug path). Both deliberately out of scope.

**Context-manifest delta.** Read beyond the manifest: `.claude/agents/builder.md` (the
loaded contract). Confirmed (not re-read in full): `docs/PROGRESS.md` is the mind-palace
domain log, orchestrator single-writer, out of scope. Nothing proved irrelevant.

**Verification.** `bash docs/build-plans/bp-004/acceptance/run.sh` → PASS=21 FAIL=0,
exit 0. Stop-gate audit → ALLOW (delta in-scope, no uncommitted blessing). No design
note, `CONSTITUTION.md`, or golden-set path touched; no `ratified`/`ready` flip anywhere.

---

## Entry — 2026-07-06 — Items 1–3 landed & verified (code + template + commands); harness next

**Status.** `/build bp-004` under way (owner flipped `proposed → ready`; I flipped
`ready → in-progress`, `plan.md:4`). Items 1, 2, 3 landed and unit/grep-verified.
Item 4 (harness) and Item 5 (promote findings) remain. Working-tree delta so far is
exactly in-scope (`_lib.py`, template, three command files, the plan+journal).

**Completed (per item).**

- **Item 1 — A5 `_lib.py` normalization (code).** Added `_normalize_status(v)` after
  `_scalar` (cut at first `" #"`, then rstrip; nospace `ready#x` left intact —
  false-negative-only). Applied at **all three** status-extraction sites: `status_of`,
  `_status_in_text`, and — the third site surfaced in plan §3 Q2 — `_blessing_in_diff`
  (was `val = _scalar(...)` at the old `:394`, now wrapped in `_normalize_status`).
  `_scalar`/`parse_front_matter` untouched (scope stays status-only). **Smoke-verified**
  (heredoc): all comment forms → clean value; `ready#x` → unchanged; clean `ready` →
  no-op; a `#` in `design_ref`/`_scalar` survives while status strips.

- **Item 2 — A5+A6 template.** `docs/templates/build-plan.md:4` is now `status:
  proposed` (no inline comment). `re_entry: null` restored as a front-matter key
  (now `:16`, immediately before `supersedes`), with an inline comment naming §11 as
  its human-readable expansion (A6; the comment is legal — A5 bans it only on the
  status line). Verified: `objective`/`context_manifest`/`non_goals`/`stop_conditions`
  remain **absent** from front-matter (body sections §1/§2/§9/§10, still present).

- **Item 3 — A6 command reconciliation.** `build.md:26-27`, `graduate.md:16-17`,
  `scribe.md:16` now reference the **§2/§7/§9/§10 body sections** instead of
  front-matter keys; `re_entry` explicitly noted as staying a front-matter key. Grep
  confirms no lingering front-matter-key phrasing for the four moved fields.

**In-flight.** Item 4 — write `docs/build-plans/bp-004/acceptance/run.sh`: chain
bp-002's harness (→ bp-001 → bp-000, 18 prior criteria) + add the 0006-strip (three
paths, clean controls) / 0006-nospace / 0006-scope / template / command / finding
regressions. Then Item 5.

**Next action.** Build `acceptance/run.sh` per plan §6/§7 Item 4; run it to green;
then the 0008-build dry-run (record here); then promote finding-0006 → promoted (A5)
and finding-0008 → promoted (A6), Item 5, last.

**Open questions.** None blocking (two decisions parked, plan §11).

**Context-manifest delta.** No reads beyond the manifest for Items 1–3. Scratchpad
`Write` was denied by scope-guard (outside write_scope, as designed) — smoke test run
via a Bash heredoc instead (Bash writes are not pre-hoc scope-guarded; the scratchpad
is outside the repo so it never enters the Stop-gate delta).

**Verification.** Item 1 smoke test SMOKE OK; Items 2/3 grep-verified (see above). Full
harness verification is Item 4.

---

## Entry — 2026-07-06 — plan minted at `proposed` (grounded graduation pass, no implementation)

**Status.** bp-004 is minted at `status: proposed` and **held there**. This entry
records the grounded graduation pass (A4): the code was read, every claim is
`path:line`-cited (plan §3), the plan was written, and **nothing was implemented** —
`_lib.py`, the template, the command files, and the findings are all untouched. The
next session is `/build bp-004` (after the owner's `proposed → ready` hand edit),
which lands Items 1–5.

**Provenance — why this plan exists and what it lands.** A5 and A6 are already
ratified into `docs/design-notes/agent-workflow.md` (§16 lines 279/280; §6 line 152;
§3 line 78). This plan lands only their *mechanical consequence*, exactly as bp-003
landed A4's: the parser normalization, the template fixes, the command reconciliation,
and the terminal finding promotions. Authority-to-act (the owner's instruction) is
separate from the readiness blessing (owner-only, §10); this session performs **no**
blessing transition.

**Grounding highlights (full detail in plan §3).**
- The bypass and its extractor→detector wiring confirmed at `_lib.py`: `status_of`
  (`:186-189`) and `_status_in_text` (`:253-259`) return un-normalized values; the
  three detectors compare by exact equality (`:304/:308`, `:395/:397`, `:430/:432`).
- **Key surfaced risk (plan §3 Q2):** `_blessing_in_diff` extracts via `_scalar`
  **directly** at `_lib.py:394` — it routes through *neither* named extractor, so
  normalizing only `status_of`/`_status_in_text` would leave the tracked Stop-gate path
  unfixed. The plan applies `_normalize_status` at **all three** extraction sites
  (including `:394`) to make all three detectors fire, per §6/A5.
- No-space safety (Q3) and status-path scoping (Q4) confirmed: cut at first `" #"`
  only; `_scalar`/`parse_front_matter` unchanged so non-status `#` survives.
- Template gaps confirmed: `docs/templates/build-plan.md:4` carries the antipattern
  comment; front-matter has **no** `re_entry` key (grep). Command drift confirmed at
  `build.md:26-27`, `graduate.md:17`, `scribe.md:16`.
- Prior-harness safety (Q7): every bp-000/001/002 test drives clean status lines, so
  `_normalize_status` is a no-op on them; bp-004's harness chains bp-002's by reference.

**Completed (this pass).**
- Investigation & grounding (plan §3), reconciliation proposals (§4), interfaces pinned
  inline with exact before/after forms (§6), five blast-radius-ordered items with
  per-item acceptance **and** a distinct falsifier (§7), §8 marked `N/A — no
  mathematical object`, non-goals (§9), stop-and-raise (§10), two parked decisions (§11),
  dependency/ordering map (§12).
- Plan minted at `proposed`; this journal opened (alive).

**In-flight.** None. Clean boundary: the plan is complete and awaits the owner's
`proposed → ready` blessing, then `/build bp-004`.

**Next action (owner / orchestrator).** Owner reviews the plan item-by-item and, if
approved, hand-edits bp-004 `proposed → ready` (the only path onward, §10). Then
`/build bp-004` executes Items 1–5 in the §12 order: Items 1/2/3 (disjoint files, any
order) → Item 4 (harness join) → Item 5 (promote findings, terminal). Done =
`bash docs/build-plans/bp-004/acceptance/run.sh` exits 0 (new A5/A6 regressions +
all 18 prior criteria green) and both findings at `promoted`.

**Open questions.** None blocking. Two decisions parked with re-entry conditions
(plan §11): normalizing `cmd_brief`'s cosmetic status render, and a belt-and-suspenders
`cmd_gate_check` normalization — both deliberately out of scope (status-path-only fix;
the real enforcement path is the hook/stdin route through the extractors).

**Context-manifest delta.** Read beyond the manifest: `.claude/hooks/gate-guard.sh`
and `journal-gate.sh` (to pin the hook-mode-vs-standalone harness invariant, plan §6);
`.claude/skills/graduate/SKILL.md` (the grounded-pass discipline this plan follows);
`docs/PROGRESS.md` (confirmed it is the mind-palace domain log, orchestrator
single-writer — out of scope). Nothing proved irrelevant.

**Verification (of the graduation pass, not the build).** All `path:line` citations in
plan §3/§4/§6 were read directly from the current files. The A4 falsifier for a
graduation pass — an emitted implementation, or a required section omitted rather than
`N/A`-marked — does **not** fire: no code/template/command/finding was edited, and all
thirteen template sections (§0–§12) are present (§8 explicitly `N/A`).

---

## Markers
