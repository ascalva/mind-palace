# BP-002 — Build journal

Records the work landing amendment A3 and locking finding-0004's ambient-path
exclusion. Committed artifacts are history, not scratch (§9). Narrative entries are
newest-first below the header; the `## Markers` section at the file's end receives
the mechanical lines hooks append (compactions, audits, HOOK-FAILUREs).

Fresh-agent test (§9): a session given only `plan.md` + this journal + the
write-scope files must continue without re-asking anything already answered.

---

## Seal — 2026-07-06 — /triage — bp-002 `complete`, journal sealed

**Seal.** Plan flipped `ready → complete` (`plan.md:4`) and this journal sealed by `/triage`,
enacting owner ruling oq-0002 (fold bp-002 into the formal lifecycle for a uniform board). The owner
supplied the `proposed → ready` blessing by hand (owner-only, §10); the orchestrator flipped
`ready → complete` and sealed. A3's work is committed (`0e9fc90`, merged `c17a456`); the acceptance
harness re-ran green at HEAD (**6/6 — PASS=6 FAIL=0, 23 assertions**) under bp-004's A5 change (a
no-op on clean status lines); findings 0005 → promoted, 0004 → resolved. bp-002's §14-parked pre-hoc
`status: ready` denylist remains a separate open decision. Narrative ends here; subsequent lines are
mechanical markers only.

---

## Entry — 2026-07-05 — A3 implemented; harness green; findings resolved

**Status.** A3 landed and verified; `docs/build-plans/bp-002/acceptance/run.sh` is
green (**bp-002 6/6, 0 FAIL** — one group re-runs the 18 prior criteria by reference
[bp-000 13 + bp-001 5], plus the 5 new A3/0004 checks; 23 distinct assertions, all
PASS). The plan is **held at `status: proposed`** by design (see the
plan's Provenance note): this session executes under the owner's direct instruction
but performs **no** blessing transition — it never writes `status: ratified` or
`proposed → ready`, and it does not flip this plan. The deltas are in the working
tree, uncommitted, for the owner to review and commit.

**Completed (per criterion; each reproduced by `acceptance/run.sh`).**

- **Δ1 — journal-gate (c) → untracked-inclusive (A3, §6c, warrant finding-0005).** In
  `.claude/hooks/_lib.py`: added `_untracked_under(prefixes)` (→ `git ls-files
  --others --exclude-standard -- <prefixes>`) and `_untracked_blessing()` (filters
  those with `is_design_note`/`is_build_plan`, reads on-disk `status_of`, returns a
  reason iff a design note is `ratified` or a plan is `ready`). Wired into the
  `cmd_stop_audit` (c) block, right after the existing `_blessing_in_diff` tracked
  scan. A Bash-minted **untracked** plan at `status: ready` — invisible to `git diff
  HEAD` and to gate-guard (Edit/Write-only) — is now caught as a from-nothing
  blessing (rc=2, reason cites the blessing + the file). Criteria 1, 4 (0005-regression).

- **Δ1-tightness — legitimate creation still passes (A3, §14 caveat).** An untracked
  plan at `status: proposed` (exactly what `/graduate` emits) does **not** block
  (rc=0) — the catch is scoped to blessed statuses only, so it cannot break legitimate
  plan creation. Criterion 4 (0005-legit).

- **Δ1-A1-preserved — committed blessing self-clears (A1, §6c).** The new scan reads
  **only untracked** files, so a *committed* blessing (tracked, in HEAD) never trips
  it: a committed → ready plan yields rc=0. The uncommitted in-place `proposed → ready`
  flip on a *tracked* plan still blocks via the unchanged `_blessing_in_diff` tracked
  path. Criteria 2, 4 (committed-blessing, (c)-uncommitted-plan). A1's HEAD-anchored
  self-clear is intact — proven non-vacuous by the committed case going rc=0 while the
  untracked/uncommitted cases go rc=2.

- **Δ2 — finding-0004 (a) ambient-path exclusion (§6, warrant finding-0004).**
  `.gitignore` already carries `.claude/settings.local.json` (committed `868ed17`, the
  bp-001 commit) and the file is untracked (`git ls-files` empty); a machine-global
  ignore (`~/.config/git/ignore:1 **/.claude/settings.local.json`) reinforces it. No
  `_lib.py` change is needed — `git status --porcelain -uall` and `git ls-files
  --others --exclude-standard` both omit ignored paths, so gitignoring is the whole
  fix. Locked by the 0004 before/after check (tracked churn trips (b); after the
  committed untrack+gitignore, churn is clean). Criteria 3, 4 (0004).

- **Findings.** `finding-0005 → promoted` (warrant for A3; resolution cites §6c/§16
  A3, this plan, Δ1, and the 0005 regressions). `finding-0004 → resolved` (resolution
  cites the gitignore at `868ed17` + the 0004 regression). Session brief's unswept
  count drops from 2 to 0.

**In-flight.** None. At a clean boundary: A3 implemented, harness green, findings
terminal, plan + journal written.

**Next action (owner / orchestrator).** Review the working-tree delta and commit it
(`.claude/hooks/_lib.py`, `docs/build-plans/bp-002/**`, `docs/findings/finding-0005.md`,
`docs/findings/finding-0004.md`). The `.gitignore` line is already committed
(`868ed17`), so no `.gitignore` change is pending. Optionally: `/triage` to write the
canonical `docs/PROGRESS.md` checkpoint (orchestrator single-writer, out of this
plan's scope by design), and rule on the §14-parked *pre-hoc* plan-path `ready`
denylist (belt-and-suspenders over A3's post-hoc catch). If the owner wants bp-002 in
the formal lifecycle, the `proposed → ready` flip is theirs to make by hand.

**Open questions.** None blocking. One parked design question exists in §14 (added by
A3): whether to add the stronger *pre-hoc* denylist of `docs/build-plans/**/plan.md`
`status: ready` writes as belt-and-suspenders over A3's post-hoc catch. Default
(recorded in §14): post-hoc Stop-gate only; re-entry when a Bash-minted `ready` plan
is observed reaching operation despite the catch, and it must be scoped not to block
legitimate `/graduate` creation at `proposed`. Owner ruling, not blocking.

**Context-manifest delta.** Read beyond the manifest: `.claude/hooks/journal-gate.sh`
(the Stop wrapper — confirmed unchanged; `--standalone`/`--diff-file` contract intact),
`docs/build-plans/bp-000/acceptance/run.sh` and `docs/build-plans/bp-000/plan.md`
(the prior harness + bp-000 write_scope, to confirm the wrapped run stays green and to
reason about scope interaction with untracked bp-002 files — harmless: bp-002/plan.md
is `proposed`, never flagged; bp-000 2b greps for its own probe). Discovered during
smoke-testing: a **machine-global** git ignore hides `.claude/settings.local.json`
independent of the repo `.gitignore` — noted above so the 0004 regression force-adds
the file to reproduce finding-0004's original *tracked* state non-vacuously. Nothing
proved irrelevant.

**Verification.** All five new checks were smoke-tested standalone before baking into
the harness, then the full harness was run twice: once to confirm the pre-A3 baseline
green (bp-001 wrap: 18/18), once post-A3 (bp-002: 6/6 groups — the 18 prior re-run +
5 new). The prior harness stays byte-clean over bp-000/** and bp-001/**.

---

## Markers
