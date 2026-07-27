---
type: journal
plan: bp-126
started: 2026-07-27
updated: 2026-07-27
---

## 2026-07-27 — Item 12: clause (e′) built and proven in a throwaway repo

**Status.** Item 12 closed. Items 13 and 14 next; all three land in ONE commit (atomicity).

**Base verified.** `git log --oneline -1` → `f9cfe4f chore(bp-126): ready → in-progress — the
cutover, delegated with the deletion withheld`. Matches the expected base exactly.

**Mutual exclusion re-verified at build time** (the "Owed at seal" item): no other builder is
running and no other plan holds `.claude/hooks/**`. I hold it.

### ⚑⚑ The live-file deletion is WITHHELD BY THE ORCHESTRATOR and is NOT discharged by me

`.claude/state/resume-brief.md` is gitignored and **absent from this worktree** (`.claude/state/`
contains only `.gitignore`). The plan's §5 says the criterion is then "satisfied **vacuously**".
**I am not claiming that, and the orchestrator has withheld the act.** The live deletion will be
performed by the orchestrator in the main checkout at merge, together with a snapshot taken at
that moment. `rm`-ing nothing proves nothing; a criterion satisfied by absence is a finding, not
a discharge. What IS mine in Item 14 is `docs/templates/resume-brief.md` — tracked, a real diff.

**Safety net already in place, which reduces nothing.** The orchestrator archived the live brief
verbatim at `docs/archive/resume-brief-final-2026-07-27.md` (tracked, committed) with the source
digest pinned in its front matter. I read it whole. It uniquely carries a **retraction of a false
claim** (the reference substrate does *not* lack `corpus_to_corpus` edges — 644,785 exist; the
real gap is *typing* in the code sensor), a severe unfiled data defect, and the measured clause-(e)
firing data. Had it been deleted un-archived, the false version is what would have survived.

### What was built

`_lib.py` gains `SEAT_ROLE` (module constant) and `_handoff_is_stale()`, and clause (e) at
`:892-920` is replaced by clause (e′). The comment names the superseded decision explicitly —
a reader of the file can see that a prior *ratified* decision was replaced and by what.

**§3 Q2 — the subprocess-vs-import choice, settled by measurement, not taste.** MEASURED,
7 runs each on the real tree:

| | min | median | max |
|---|---|---|---|
| `python3 scripts/handoff.py --role orchestrator --check` | 130.5 ms | **137.0 ms** | 143.2 ms |
| `python3 .claude/hooks/_lib.py stop-audit` (clause (e), before) | 84.8 ms | 85.2 ms | 91.4 ms |

The spawn costs ~137 ms and only in orchestrator posture *and* only when commits landed this
session — far under §3 Q2's "a few hundred milliseconds" threshold, so the **subprocess form is
taken** and the import form does not earn its inversion of the `scripts/* → _lib` dependency
direction. Invoked as `sys.executable`, not `uv run`: the generator is stdlib-only and a Stop
hook must not pay an environment resolve.

**finding-0236 honoured.** Check 1 *shells out to* `--check` and never re-implements the compare.
That entry point is tree-pure (no queue, no clock, no HEAD sha), which is what keeps (e′) computed
off **the work** rather than off **the daemon**.

**Owner DRY rule honoured.** No second `git` invocation: (e′) reuses `head_sha` from the shared
call, and its two new reads are `os.path.getmtime` and one non-git subprocess.

### Acceptance — `uv run pytest tests/integration/test_handoff_gate.py -q` → **13 passed**

The fixture now carries a real seat (`journal.md`, `readings.md`, a generated `handoff.md`) and a
copy of `scripts/{handoff,board}.py`, because a fixture without the generator would exercise only
the fail-open path and prove nothing. All six original cases survive — (3), (5), (6) verbatim as
posture invariants; (1), (2), (4) re-expressed against the seat. **No case was deleted.**

`grep -c 'resume-brief' .claude/hooks/_lib.py` → **0** (and `grep -c 'resume brief'` → 0). The
supersession comment names the retired artifact by its *decision* (`dn-session-handoff-gate`
§2.2-2.3) rather than by its path — keep-and-link done properly: link to the record, do not leave
a live pointer to a deleted path in operational code.

### The falsifier, and the tests' non-vacuity proven by mutation

Item 12's named falsifier is **one-step convergence**. `test_e_prime_converges_in_exactly_one_step`
asserts the whole sequence: tree changes → BLOCK citing (e′) and `handoff.md` → regenerate →
**commit again (HEAD moves, the exact event that re-armed (e))** → close → **ALLOW**, then
`--check` rc 0 and a third close still ALLOW. **The falsifier did not fire.**

Four adversarial mutations of `_lib.py`, each run against the suite and reverted:

| mutant | caught? |
|---|---|
| A — check 1 never reports stale (`returncode == 1` → `False`) | ✅ 3 tests red |
| B — (e′) fires in builder posture (`plan is None` → `True`) | ✅ posture invariant (6) red |
| C — **check 2 keyed to `last_commit` instead of the baseline mtime** | ❌ **survived at first** |
| D — a missing seat journal treated as fresh | ✅ red |

⚑ **Mutant C survived the first suite and that mattered** — it is the re-arming bug the whole
note exists to remove, and *no test distinguished it* (the convergence test masked it: the entry
was stamped 100 s ahead, so a last-commit key still passed). Fixed by adding
`test_e_prime_check_2_is_keyed_to_session_start_not_to_the_last_commit`, which pins the entry at
the *earliest legal moment* (session start) and dates the commit an hour later via
`GIT_{AUTHOR,COMMITTER}_DATE`. Mutant C now reddens exactly that test. This is the
"structural enforcement" rule landing on my own work: a property is only real when a test proves
it, and the convergence test alone did not prove this one.

**Markers.** None.

## 2026-07-27 — Items 13 + 14, and the atomicity proof

**Status.** All three items' code changes complete and landing in ONE commit.

### Item 13 — `session-brief.sh` re-pointed

The auto-surface block now emits `docs/roles/orchestrator/handoff.md` and the seat journal's
**authoritative segment**. Untouched, as required: the worktree-aware `ROOT` resolution, the
`fail_loud`/`trap` posture, the deskcheck-owed line, and the baseline write at the tail (clause
(e′) check 2 keys on that file's mtime, and clause (c)'s consumer chain depends on it).

**Acceptance, observed:**

| leg | rc | observed |
|---|---|---|
| seat present, orchestrator posture | **0** | handoff emitted (1×), segment header (1×), then `SESSION BRIEF` and the `Deskchecks owed:` line; **stderr empty**; **0** `HOOK-FAILURE` |
| seat files absent (the falsifier) | **0** | 7 lines — brief + deskcheck line only; **stderr empty**; **0** `HOOK-FAILURE` |
| builder posture (`active-plan` set) | **0** | **0** handoff lines; brief still emitted |

`grep -c 'resume-brief' .claude/hooks/session-brief.sh` → **0**. **Item 13's falsifier did not
fire**: a missing seat file never errors the hook and never exits non-zero.

**Two defects found and fixed in my own first draft**, both caught by running the acceptance
rather than reading it:

1. `tr -d '[:space:]' < file 2>/dev/null` does **not** silence a *redirection* failure — the
   shell reports the missing file on its own stderr before `tr` ever runs, so a fresh checkout
   would have printed a spurious error at every SessionStart. Replaced with a `[ -r ]` guard.
2. The awk segment ran to EOF and swept in the journal's trailing `## Markers` section, whose
   own explanatory comment contains the literal string `HOOK-FAILURE` — which would have put
   that string into **every** session brief. The segment now stops at `## Markers`: it is a
   mechanical hook log, not an entry, so it was never part of the authoritative segment anyway.

**⚑ A behavioural choice I made and am flagging for veto: the surface is POSTURE-GATED.** The
retired brief lived in gitignored per-worktree state, so a builder's worktree had none and saw
nothing. The seat artifacts are **tracked**, so they exist in every checkout; emitting them
unconditionally would have pushed ~287 lines of orchestrator state into every builder session.
The guard mirrors `_lib.py`'s `plan is None` test exactly, so a session sees at its **start**
precisely the artifacts clause (e′) judges at its **close**. Nothing in the note or the plan
required this; it preserves a property the old surface had by accident, and it is one line to
revert.

**⚑ MEASURED — the SessionStart context cost went UP, and that deserves saying plainly.**

| | lines | bytes |
|---|---|---|
| retired brief (as archived) | 163 | 11,622 |
| seat surface now emitted | **287** | **18,074** |
| delta | **+124** | **+6,452 (+56%)** |

Composition: `handoff.md` 74 lines / 4,800 B, plus 212 lines of seat journal (the whole entry
list — there is no capsule yet). The designed remedy exists and is not mine: §2.8 compaction at
`/triage`, whose working threshold is ~300 lines, and the active segment is already at 212.
Filed as `finding-0244` (`discovery` → orchestrator). This does not block the cutover — the
brief was *destructively rewritten* and historyless, which is the defect being fixed; paying
more context for a versioned, append-only, partly-generated artifact is the trade the note
makes knowingly. But the wave's own warrant is context load, so an unmeasured claim of
improvement would have been dishonest.

### Item 14 — the template retired; the live file is NOT mine

**Pre-deletion verification, performed BEFORE the deletion** (the falsifier is "a session
started after this cannot orient"). Read `docs/roles/orchestrator/handoff.md` whole:

- **Unit in flight:** rendered — `bp-123 — the per-machine overlay becomes config/ouroboros.toml…`
- **Next action:** rendered — `/resume bp-123`
- **Blocking unknowns:** rendered — none

Both facts the falsifier names are answerable **from the rendering alone**. The retired
template's seven sections each have a named home: IN FLIGHT → the *Unit in flight* + *Units of
work* panes; THEN-QUEUE → the `ready` rows + *Next action*; OPEN DESK → *Awaiting the owner*
(32 open oqs, ids listed); DESKCHECKS OWED → the *Deskchecks owed* table; STANDING RULES →
`.claude/skills/**` (bp-125's migration, rule-by-rule verified in `finding-0242`); SESSION TIER
→ the checkpoint skill's tier-declaration duty in its new home; DESIGN-TIER DEFERRALS → the seat
journal plus the findings/oq panes; SELF-REWRITE → **retired outright**, replaced by §2.10's
mechanics. One honest re-homing rather than a rendering: the template asked for each running
builder's *worktree path + branch*; that is judgement/operational state and now lives in the
seat journal, with `git worktree list` as the derived view.

`git rm docs/templates/resume-brief.md` → `git status --short` shows `D`. **Item 14's grep
criterion over exactly the five live operational surfaces returns 0**:

```
.claude/hooks/_lib.py                      0
.claude/hooks/session-brief.sh             0
.claude/skills/context-economy/SKILL.md    0
tests/integration/test_handoff_gate.py     0
docs/templates/                            0   (no file matches)
```

Historical and immutable references are left exactly as they are — ratified notes, findings,
prior journals, `CHANGELOG.md`, brainstorms, `docs/book/`, `PROGRESS.md`, `PARKING-LOT.md`.

**⚑⚑ `.claude/state/resume-brief.md` — WITHHELD BY THE ORCHESTRATOR, NOT DISCHARGED BY ME.**
The file is gitignored and absent from this worktree; `.claude/state/` here holds only
`.gitignore` and a `session-baseline`. The plan's §5 offers a **vacuous** pass on that absence.
I decline it. The orchestrator performs the live deletion by hand in the main checkout at merge,
with a snapshot taken at that moment. **This criterion is OPEN against this plan and is owed by
the merge, not by this branch.**

### ⚑ How atomicity was proved — by execution, not by assertion

Two halves.

**(1) One diff.** `_lib.py`, `session-brief.sh`, `test_handoff_gate.py` and the template
deletion are staged and committed together, by name, in a single commit on top of `f9cfe4f`.
There is exactly one commit on this branch touching any of them, so **no intermediate state
exists in the history** — not merely none in the working tree.

**(2) The half-state genuinely deadlocks, demonstrated in a throwaway repo** (scratchpad, not
committed). Built a repo carrying the **base commit's** hooks — clause (e), verbatim from
`f9cfe4f` — with a full seat and **no** brief, i.e. exactly "template retired, clause (e) left
standing". After one commit this session:

```
close 1  BLOCK: (e) … the resume brief is stale or missing …
recovery A: regenerate the handoff + commit   -> close 2  BLOCK  (identical)
recovery B: append a seat-journal entry + commit -> close 3  BLOCK  (identical)
recovery C: touch EVERY tracked file + commit -> close 4  BLOCK  (identical)
then re-create the deleted artifact           -> close 5  ALLOW
```

Four independent recoveries, including touching every file in the repo, cannot clear it. **The
only key is the artifact the plan deletes.** That is the repo-wide deadlock the plan's §0
predicts, reproduced rather than assumed — and it is why the three items may not be split.

**Markers.** None.

## 2026-07-27 — the A10 amendment, DRAFTED for the owner's hand (not landed)

**⚑ This is a proposal, not a landing.** `docs/design-notes/agent-workflow.md` is `ratified`, so
`scope-guard` denies the write before the write-scope check runs and the Stop-gate (b2) clause
blocks the Bash path against HEAD status (`finding-0233`). No agent may land it, and none tried:
the note is untouched on this branch. It is drafted here so the owner can land it in one paste,
**after this plan merges** — so the amendment describes a clause that exists.

**Checked against the existing log before drafting.** The log carries A1–A6, A8, A9 (there is no
A7), so **A10** is the next id. **A9 already did more than the plan assumed:** it corrected §6c's
closing sentence (*"`session-baseline` survives only for the SessionStart brief's narration;
enforcement does not read it"*), which was already false, and it already extended the §6
journal-gate row's enumeration to (a)–(e). So A10 does not re-correct those; it supersedes A9's
(e) and closes two gaps A9 left. Two stale citations found in A9's own text while drafting, both
recorded and neither acted on (A9 lives in a ratified note): it cites the baseline write as
`session-brief.sh:52` — it was `:65` before this plan and is **`:103`** after it — and its
enumeration stops at (e), while clause **(f)** (seal follow-through, bp-097 / D5) has existed
since and appears in **no** amendment at all.

### Paste-ready — append to §16, after the A9 entry

```markdown
- **A10** — warrant: `dn-role-state-and-scoped-handoff` §2.10 (ratified; implemented by bp-126),
  which partially supersedes `dn-session-handoff-gate` §2.2–2.3. **Replaces Stop-audit clause
  (e)** — added by A9 — with clause **(e′)**. The trigger is unchanged (orchestrator posture,
  `plan is None`, and HEAD moved past `.claude/state/session-baseline`'s content). What the
  trigger DEMANDS is replaced, because (e)'s demand was circular twice over: it compared an
  unversioned file's mtime to the **last-commit time**, so every post-write commit re-armed it,
  and its block text instructed prose "citing the final commit hashes", which cannot be written
  before the commits it must cite. Measured cost: 108 firings (99 fork-deduped) over eight days
  across sixteen sessions, peak day 36 (`dn-trace-retrieval` Part 1). (e′) demands two facts
  instead, each dischargeable by one act: **(1) DERIVED** — regenerating the seat's
  `docs/roles/<seat>/handoff.md` must be a byte-identical no-op, delegated to
  `scripts/handoff.py --role <seat> --check` and never re-implemented in the hook (that entry
  point renders tree-pure, so the *work* re-arms the gate and a live daemon cannot —
  `finding-0236`); because the rendering embeds no sha and no timestamp, the recovery converges in
  exactly one step. **(2) NARRATIVE** — `docs/roles/<seat>/journal.md`'s mtime must be at least
  the **mtime** of `session-baseline` (its *session-start* key, deliberately not the last-commit
  time A9 used, so a late commit cannot re-arm it). **(3) MEASURED is explicitly NOT gated**:
  `readings.md` is never consulted, because gating a long suite reading at every close would
  either block honest closes or train `touch`-laundering. Fail-open is widened accordingly: a
  missing or unreadable baseline (as under A9), an absent seat directory, **and any generator
  error** — enforcement never crashes a close. (e′) adds no second `git` subprocess (it reuses the
  hoisted `%H %ct` call) but does add one **non-git** subprocess, the generator, measured at
  ~137 ms against an ~85 ms Stop baseline and incurred only in orchestrator posture when commits
  landed. Two residuals are accepted and named rather than papered over: a session may commit
  *after* its last narrative entry (existence, not quality — the same stance the gate note takes),
  and narrative purity is tier-4 only for the lintable class. **§5** additionally gains the
  **role registry**: a role is not only a session posture but a **seat** with typed standing state
  that outlives its occupant, and the registry is **closed** — `orchestrator` (three artifacts:
  `journal.md` NARRATIVE, `readings.md` MEASURED, `handoff.md` DERIVED and generated) and
  `scheduler` (whose state is already typed and durable in `data/queue.sqlite`, so it gets no
  narrative artifacts and no seat directory is minted for it). **§9** gains the **seat
  generalization**: the journal contract's seven required sections and its semantic-boundary
  triggers apply unchanged to a seat journal, with two differences — retention is append-only with
  compaction by supersession capsule (`## CAPSULE — <date>`; the authoritative segment is the
  latest capsule plus every entry newer than it), and clause (f)'s `## Follow-through` requirement
  binds **plan** journals only. `session-brief.sh` no longer surfaces the retired brief; it
  surfaces the seat's DERIVED rendering and its journal's authoritative segment, in orchestrator
  posture only. Per the A1–A9 precedent the log carries the change rather than rewriting §5/§6/§9
  in place. ⚑ Two corrections owed to A9's own text, recorded here because A9 is immutable: it
  cites the baseline write as `session-brief.sh:52` (it is `:103` after bp-126), and its §6
  enumeration stops at (e) — clause **(f)** (seal follow-through, bp-097 / D5) has existed since
  and is carried by no amendment.
```

### Also owed by the owner's hand, in the same sitting

- **The partial supersession of `dn-session-handoff-gate` §2.2–2.3**, effective on this plan's
  merge. Recorded in the amendment log; `superseded_by` on that note is deliberately **NOT** set —
  `dn-role-state-and-scoped-handoff` §1.1 rules that the note is not *wholly* replaced, and its §1
  purpose and §2.4 scope key survive unchanged and still govern. A builder performs neither act,
  and neither was attempted.

**Markers.** None.

## 2026-07-27 — seal: the cutover is built, proven and committed; the live deletion is owed

**Status line.** Items 12, 13 and 14 are built and green. **Item 14 is discharged in its tracked
half only** — `docs/templates/resume-brief.md` is deleted; `.claude/state/resume-brief.md` is
**withheld by the orchestrator and owed at merge, by hand, with a snapshot taken at that moment.**
Not merged, not pushed. The plan's `status:` is untouched (`in-progress`), and no blessing was
performed.

### Acceptance, criterion by criterion

| item | criterion | observed | falsifier |
|---|---|---|---|
| 12 | gate suite green over (e′-1)…(e′-4) + the three posture invariants | `13 passed in 4.19s` | **did not fire** — convergence proven: BLOCK → `--write` → commit → **ALLOW**, then `--check` rc 0 and a third close still ALLOW |
| 12 | `grep -c 'resume-brief' .claude/hooks/_lib.py` = 0 | **0** (also 0 for `resume brief`) | — |
| 12 | no second `git` subprocess | the shared `%H %ct` call is the only `git` invocation; (e′) adds two `getmtime` calls and one **non-git** subprocess | — |
| 12 | (e′) silent under an active plan | posture invariant test green; mutation forcing it on reddens exactly that test | **did not fire** |
| 13 | seat present → emits rendering + segment + brief + deskcheck line, **rc 0** | rc 0, stderr empty, 0 `HOOK-FAILURE` | — |
| 13 | seat absent → **rc 0**, no `HOOK-FAILURE` | rc 0, 7 lines, stderr empty, 0 `HOOK-FAILURE` | **did not fire** |
| 13 | `grep -c 'resume-brief' session-brief.sh` = 0 | **0** | — |
| 14 | template deleted, `git status --short` shows `D` | `D  docs/templates/resume-brief.md` | — |
| 14 | grep over exactly the five live surfaces = 0 | **0** across all five | — |
| 14 | pre-deletion verification: in-flight unit **and** next action answerable from the handoff pair alone | both rendered explicitly in `handoff.md` | **did not fire** |
| 14 | `.claude/state/resume-brief.md` absent in this checkout | **⚑ NOT CLAIMED — WITHHELD.** The file is absent here and the plan offers a vacuous pass; it is declined. Owed at merge | n/a |

**No stop-and-raise condition was met.** Convergence demonstrated; the pre-deletion verification
passed; the hook does not fail loud on a missing seat file; no (a)/(b)/(c)/(d)/(f) test moved; the
generator subprocess is cheap; no criterion needed a file outside §5; no ratified note was edited
and no blessing was implied.

### The gate — each leg run SEPARATELY, redirected to a file, never piped

| leg | rc | observed |
|---|---|---|
| `uv run ruff check .` | 0 | All checks passed! |
| `uv run python scripts/check_imports.py` | 0 | Import firewall (I2) OK; worker boundary (tier 4) OK |
| `uv run mypy core agents eval ops scheduler scripts` | 0 | Success: no issues found in **261** source files — floor holds at 0 |
| `uv run mypy` (ARGLESS) | 1 | **Found 69 errors in 20 files (checked 559 source files)** — exactly the pinned baseline; **zero** in either changed file |
| `uv run python -m ops.type_gate` | 0 | Tier-2 membership OK; bare-ignore scan OK; the one parked non-fatal shim report (finding-0223) unchanged |
| `uv run pytest -q` | 1 | **2 failed, 2308 passed, 15 skipped, 12 warnings in 349.05s** |

The two failures are the two expected ones, named exactly: `tests/unit/test_core_self_containment.py::test_core_imports_nothing_outside_core`
(the finding-0103 ratchet, 20 forbidden imports — unchanged) and
`tests/e2e/test_dream_v2_live.py::test_dream_v2_synthesizes_grounded_themes_live` (finding-0226;
it failed on `MemoryCeilingError: would use 27.0 GB > usable budget 24.0 GB`). **`tests/e2e/test_scheduler_live.py`
PASSED** — the known flake did not fire. **2301 → 2308 is fully accounted for**: this plan's gate
suite grew from 6 cases to 13. No other test moved.

### Findings filed

| id | type | route | what |
|---|---|---|---|
| `finding-0244` | `spec-fidelity` | **builder** (resolved in place, build continued) | (e′) inherits (e)'s **authorship blindness** — the trigger still keys on commits-in-session. The measurement that warranted this family says the replacement *"should key on who authored the commit"*; §2.10 reproduces the trigger unchanged, so it shipped unchanged and is named rather than silently narrowed. The re-arming half **is** fixed; the misattribution half is not |
| `finding-0245` | `discovery` | **orchestrator** | the SessionStart payload grew **+124 lines / +56%**, in the wave whose warrant is context load. Cause: §2.8 compaction has never been exercised and the seat journal has no capsule. Two discharging forms, both cheap |
| `finding-0246` | `spec-defect` | **orchestrator** | ⚑ found by **dogfooding, after the seal commit**: a nested one-shot `claude -p` fires SessionStart and clobbers `session-baseline`, which **silences** the gate (its content resets to HEAD, destroying the commits-this-session guard) and **spuriously arms** check 2 (its mtime jumps forward). The **mandated budget probe is exactly such an invocation.** The silencing half is *pre-existing* — true of clause (e) since A9 — and was never noticed; the arming half is new with check 2's mtime key. Not patched: `session-brief.sh`'s baseline write is pinned untouched by Item 13's invariants, the file has three consumers, and every one-line guard is wrong in a different direction |

### Owed at seal — every item from the plan's own list, discharged or explicitly owed

- ✅ **`## Follow-through`** — below.
- ✅ **A10's exact text** — drafted for a one-paste landing in the entry above. **Not attempted.**
  Two stale citations inside A9 were found while drafting and are recorded, not acted on.
- ✅ **Partial supersession of `dn-session-handoff-gate` §2.2–2.3** — effective on this plan's
  merge commit (this branch's tip is `aaff6ef` plus this seal commit). Recorded here for the
  owner's amendment-log entry; `superseded_by` deliberately **not** set. The note is untouched.
- ✅ **The Stop-latency measurement** — in `docs/roles/orchestrator/readings.md` with its
  timestamp, and repeated above. ⚑ I appended it out of timestamp order at first and caught it:
  that is exactly the defect `finding-0242` recorded against bp-125's readings appends. Re-done in
  order; the log is monotonic from `2026-07-27T04:56Z` onward.
- ✅ **Mutual exclusion on `.claude/hooks/**` re-verified at build time** — no other builder ran.

### cost.actual — for the orchestrator to transcribe into the plan's front matter

```yaml
cost:
  estimate:
    model: opus
    tokens: 500k
  actual:
    model: opus[5] (self-reported: claude-opus-5, high effort) — matches the plan's `opus` estimate
    tokens: ~430k  # ESTIMATED, not measured: no per-subagent token counter is exposed. Basis:
                   # ~55 tool calls over a ~180k working context, one full-suite run, one
                   # 13-test suite run x8 (baseline + 4 mutants + 3 re-runs). Treat as +/-25%.
    ratio: ~0.86   # actual/estimate. A WELL-PINNED plan (the expected band is ~0.5-1.0x): §6
                   # pinned the code being replaced verbatim, §3 Q1-Q8 pre-answered every
                   # grounding question, and the three manifest entries the orchestrator added
                   # after blessing (findings 0236/0238/0241-0242) removed the two decisions that
                   # would otherwise have cost the most — how check 1 computes, and whether the
                   # archive already existed. The overrun above a tighter 0.5x is real work the
                   # plan did not price: the mutation campaign, and the deadlock demonstration.
    dollars: n/a — subscription (Max), not metered per token
    session_delta: 59% -> 71%   # +12pp; probed at bp-125's re-seal and again at this seal
    week_delta: 49% -> 50%      # +1pp all-models; Fable unchanged at 25%; resets Jul 31 20:00 ET
```

### Next action (for the orchestrator, not for this branch)

1. Review the diff. 2. Merge. 3. **Delete `.claude/state/resume-brief.md` by hand in the main
checkout, taking a fresh snapshot at that moment** and diffing it against
`docs/archive/resume-brief-final-2026-07-27.md` — carry any delta into the seat journal in the
same commit. 4. Land A10 and the partial-supersession log entry by hand. 5. Regenerate
`handoff.md` after the status flip (one step, by the pin). 6. `/triage`: write the first
`## CAPSULE` (finding-0245).

**Markers.** None.

## 2026-07-27 — audit response: check 1 failed CLOSED on a crashing generator (merge-blocking, fixed)

**Status line.** The independent pre-merge audit returned MERGE WITH CONDITIONS with one
merge-blocking defect in my code. It is real, I reproduced it, and it is fixed. Two smaller items
in the same pass. Nothing else in the diff changed.

### The defect, stated exactly

`_handoff_is_stale` keyed on `proc.returncode == 1`. **CPython exits 1 on any unhandled
exception**, and `--check` exits 1 on drift — so *a crashing generator was byte-identical to a
stale one*. The consequence is worse than a false positive: check 1 read STALE and **BLOCKED**,
the instructed recovery `--write` then failed the same way, and the close was **wedged** — a Stop
BLOCK is a hard deny. **A gate that fails CLOSED on a tooling error also wedges the session trying
to repair the tooling.** My Item 12 fail-open invariant was therefore not met, and my own
docstring's claim that an import error fails open was simply false.

Reproduced before fixing, rather than accepted from the report:

```
genuine stale : rc 1, stderr "docs/roles/orchestrator/handoff.md: STALE — regenerate with …"
RuntimeError  : rc 1, stderr "Traceback (most recent call last): …"   <-- same rc
```

### The discriminator I chose, and why

**Positive identification of staleness, never inference from failure:** block only when
`rc == 1` **and** the generator's own rendered staleness line appears in its output. Constant:
`HANDOFF_STALE_SIGNATURE = f"{SEAT_ROLE}/handoff.md: STALE"` → `orchestrator/handoff.md: STALE`.

Three choices inside that, each defensible on its own grounds:

1. **Positive match, not negative ("no `Traceback`").** The success mode is a **closed set of
   one**; crash modes are **open-ended**. A negative match enumerates failures and is wrong the
   first time something fails in a shape nobody listed (a C-level abort, a killed process, an
   `argparse` error). A positive match is correct against failures that do not exist yet. It also
   puts the burden of proof on the signal we *act* on, which is the right place for a gate that
   can deny a close.
2. **Seat-qualified, not a bare `": STALE"`.** ⚑ This is not cosmetic. If the generator ever
   raised *at its own staleness `print`*, the traceback would echo that line's **source**, which
   contains the f-string template `{dest.relative_to(ROOT)}: STALE` — so a bare probe is
   **spoofable by a crash**, which is the very failure being fixed. Only the *rendered* message
   contains `orchestrator/handoff.md: STALE`. Mutation N4 below proves the distinction is live.
3. **Both streams searched.** The stream is an incidental detail; the wording is the contract. A
   stream change keeps working; a **wording** change degrades to **fail-open** (the safe
   direction) *and* reddens `test_e_prime_blocks_on_a_stale_derived_rendering`, which drives the
   **real** generator (the loud direction). Safe plus loud is the pair I want, and it is the
   honest answer to `scripts/handoff.py` being outside my `write_scope`: I cannot pin its exit
   codes, so I pin its observable contract and make the coupling fail visibly.

**Not widened to `rc != 0`**, exactly as the audit asks: rc 2 (absent / usage / scope) is an
error, not staleness.

> ⚑ **Correction (re-audit, condition 2) — this paragraph originally said "mutation N2 proves
> that widening is caught". That was true of the code and loose about the evidence, and the
> looser claim is already in commit `a62e5f1`'s message, which is not rewritten.** N2 drops the
> rc pin **and** the signature *together*, so what it demonstrates is the pair, not the pin.
> The **isolated** widening (drop `if proc.returncode != 1` and keep the signature check) is an
> **equivalent mutant**: I re-ran it here and it survives all 20 tests with a byte-identical
> six-mode matrix. That is not a coverage gap — with the signature required, no error mode can
> produce a block, so the rc pin is genuinely redundant *for correctness* and is kept as a cheap
> narrowing and a statement of intent. **What is actually shown:** the *signature* check is what
> makes the widening safe; the rc pin is belt to its braces.

### The six modes, re-measured BY EXECUTION at the fixed tip

Throwaway repo, seat genuinely stale so only the generator's behaviour decides the verdict, check
2 pre-satisfied so check 1 is isolated:

| # | mode | `--check` rc | clause (e′) check 1 |
|---|---|---|---|
| 0 | **genuine stale** (control) | 1 | **CLOSED — blocks** ✅ |
| 1 | ImportError | 1 | **OPEN — allows** ✅ |
| 2 | RuntimeError | 1 | **OPEN — allows** ✅ |
| 3 | SyntaxError | 1 | **OPEN — allows** ✅ |
| 4 | usage / scope error | 2 | **OPEN — allows** ✅ |
| 5 | absent generator | 2 | **OPEN — allows** ✅ |
| 6 | **timeout** (a generator sleeping 90 s) | n/a | **OPEN — allows** ✅ |
| 7 | up to date (control) | 0 | **OPEN — allows** ✅ |

Mode 6's evidence is the arithmetic, not an rc: the probe took **120 s** = 90 s for the direct
`--check` (which merely sleeps then exits) **+ 30 s** for the hook to hit its own `timeout=30` and
fall into the fail-open arm. All three previously fail-closed modes (1–3) now fail open; nothing
that used to block stopped blocking.

### The two smaller items

- **Mutation N1 — the `except` arm had NO coverage.** True, and worth dwelling on: the branch the
  entire fix now leans on was unproven. It cannot be provoked end-to-end from a fixture without
  breaking the runner's own interpreter or sleeping out the 30 s timeout, so it is driven at the
  seam — `test_e_prime_fails_open_when_the_subprocess_cannot_be_LAUNCHED` monkeypatches
  `subprocess.run` to raise `OSError`, `TimeoutError` and `MemoryError` and asserts
  `_handoff_is_stale()` is `False` for each. Inverting that arm now reddens it.
- **The docstring is corrected** to describe what the code does, including why rc alone is unsafe
  and the measured open/closed verdict per mode.

### Mutation campaign, re-run against the fix — 5 of 5 caught

| mutant | caught by |
|---|---|
| **N1** — fail-open `except` arm inverted (*previously survived*) | the new launch test |
| **N2** — widen to `rc != 0` **and** drop the signature (the two together) | all three crash tests |
| **N3** — drop the signature check, keep `rc == 1` (**the original defect**) | all three crash tests |
| **N4** — bare `": STALE"` **constant** (traceback-spoofable) | the signature-contract test |
| **C** — check 2 keyed to `last_commit` (the original survivor) | the session-start test |

⚑ **N4 was weaker than it looked, and the re-audit was right to say so.** It mutates the
*constant*, and the test that catches it does so by `assert sig == "orchestrator/handoff.md:
STALE"` — a **string identity**, not a behaviour. The sibling mutation **A2**, which drops the
qualifier at the **use site** and leaves the constant untouched, therefore **survived all 18
tests**. See the next entry: that gap is now closed.

**Convergence re-confirmed**: `test_e_prime_converges_in_exactly_one_step` passes in isolation.
Suite **13 → 18 passed**.

### finding-0245 is already stale in its own favour

Re-measured at this tip: the SessionStart seat surface is **366 lines / 23,852 bytes** — **+203
lines (+125%)** against the retired brief, up from 287 at the seal, with the emitted segment at
**286 lines** and still **zero** capsules. §2.8's ~300-line threshold is **about one entry away at
merge**, not two. The finding carries the addendum; the estimate of ~70 lines per entry held
exactly, so the trigger date is predictable rather than surprising.

**finding-0244 sharpened** per the audit: the ratified spec is the load-bearing reason not to
narrow the authorship key and now leads; the DRY argument is demoted and explicitly labelled the
weak one — widening the shared format string to `%H %ct %ae` is mechanically free, so **cost is
not the objection, the spec is**.

**Markers.** None.
- **Deskcheck.** ⚑ **Ready to deskcheck.** The demo is two commands: `bash
  .claude/hooks/session-brief.sh --standalone` in the main checkout (the seat is surfaced, the
  brief is gone), and a close after a commit (the gate names its one-step recovery). DONE is not
  sealed and not deskchecked; the owner has the final say.

## 2026-07-27 — re-audit condition 1: the seat qualifier now has a behavioural pin

**Status line.** The re-audit's one condition is closed. The suite is **20 passed**; mutation **A2
now reddens**. No production code changed in this pass — the gap was entirely in the evidence.

### The gap, stated exactly

The seat qualifier is the most subtle choice in the whole fix, and the re-audit proved it is
load-bearing by **reconstructing the spoof against the real generator**. Yet nothing behavioural
pinned it. `HANDOFF_STALE_SIGNATURE` was proved only by `assert sig == "orchestrator/handoff.md:
STALE"` — the constant's **spelling**, not its **consequence** — and all three crash fixtures
produce tracebacks containing *no* form of the marker, so none of them could tell a bare probe
from a qualified one. Mutation **A2** (drop the qualifier at the **use site**, leave the constant
alone) therefore survived all eighteen tests. **A check that passes without testing its claim,
inside the gate — the same shape as `finding-0249`.**

### Reproduced before fixing, both halves

The vector, built against the **real** generator (`dest` forced outside `ROOT` immediately before
the staleness `print`, so `relative_to` raises **at** that line with its source byte-untouched):

```
rc 1
stderr:  print(f"{dest.relative_to(ROOT)}: STALE — regenerate with "        <- the ECHOED SOURCE
         ValueError: '/nowhere/handoff.md' is not in the subpath of '…'
contains ": STALE"                            -> yes
contains "orchestrator/handoff.md: STALE"     -> no
```

- delivered (seat-qualified) discriminator → **ALLOW** ✅
- under **A2** (bare probe) → **BLOCK**, and `--write` dies identically, so the close is **wedged**
- A2 against the delivered 18-test suite → **18 passed** (it survived, exactly as reported)

### The test

`test_e_prime_is_not_spoofed_by_a_crash_that_merely_MENTIONS_stale`, beside the crash tests,
parametrized over **two** vectors: the faithful reconstruction against the real generator (proves
the vector is *reachable in shipped code*), and a synthetic crash carrying the bare marker
(survives any reshaping of that source line, so the behaviour stays pinned even if the
reconstruction's anchor goes stale). Both assert the crash exits 1, that its output **does**
contain `": STALE"` and **does not** contain the qualified form — so the test cannot pass
vacuously — and that the close is **ALLOW**.

### Mutation campaign, third pass — and two equivalent mutants confirmed independently

| mutant | verdict |
|---|---|
| **A2** — drop the qualifier at the use site (*was surviving*) | **CAUGHT** — both new vectors redden |
| **A3** — stdout-only (drops the stderr half) | **CAUGHT** — 3 tests redden |
| **A4** — stderr-only | **survives** — equivalent against today's generator |
| **A1** — isolated widening: drop the rc pin, keep the signature | **survives** — equivalent |
| N1 / N3 / C | caught, as before |

I re-ran A1, A3 and A4 myself rather than accept the classification. **A3 being caught while A4
survives is the useful pair**: it proves the **stderr half is the load-bearing one** (that is where
the generator actually writes), and that the stdout half is defensive — carried deliberately so a
future move of the message to stdout keeps working, at the cost of being untestable today. Both
survivors are equivalent mutants, not coverage gaps.

### ⚑ A correction to my own clause-(f) note in the entry above

That note says this journal is *"written newest-first (§9's 'newest entry first'), so its tail is
the oldest content"*. **The premise is wrong and I should not have asserted it without looking.**
These entries run **oldest-first**, top to bottom. The tail was the pre-build notes for a duller
reason: that section is the original file body, and my entries accumulated *above* it.

The conclusion survives and generalizes better than the wrong premise did:
**`_journal_tail_has_followthrough` keys on physical file position, so any journal whose last
`## ` section is not its newest entry can satisfy clause (f) vacuously** — whether because it is
newest-first, or because a static section sits at the bottom, which is the ordinary shape of every
journal minted from the template. That is a wider hole than "newest-first journals", not a
narrower one. Still reported rather than filed: pre-existing, outside this plan's items, and the
auditor holds the merge.

**Markers.** None.

# Journal — bp-126 (the cutover: clause (e′), the re-point, and the brief's retirement)

Minted 2026-07-26 by `/graduate`, decomposing ratified `dn-role-state-and-scoped-handoff`
(blessed `c0abfd1`). Third of four (bp-124…bp-127). **Not started.**

## Pre-build notes for whoever picks this up

- ⚑⚑ **THE HIGHEST-BLAST-RADIUS PLAN IN THE FAMILY. IT IS ATOMIC BY NECESSITY, NOT BY TASTE.**
  It deletes an artifact every agent reads at every SessionStart, re-points the hook that reads
  it, and replaces the Stop clause that demands it — in one diff. The intermediate states are all
  broken:
  - delete the brief, keep clause (e) → **every orchestrator session that commits can never
    close** (a missing brief is infinitely stale, `_lib.py:909-913`). Repo-wide deadlock.
  - replace clause (e), keep the old surface → SessionStart shows a brief nothing maintains.
  - re-point, keep clause (e) → the orchestrator writes a brief it cannot see.
  Land it whole or revert it whole.
- ⚑ **VERIFY THE LINE NUMBERS YOURSELF BEFORE CITING THEM.** Clause (e) is
  `.claude/hooks/_lib.py:892-920`; the posture guard is `:899`; the commits-this-session guard is
  `:908`; **the getmtime is `:911`**. **`:762` is clause (a)** — the *journal* mtime check. The
  live brief mis-cites `:762` as clause (e)'s getmtime (note §2.2), and that stale citation
  propagated into a design prompt. This is the defect exhibiting itself; do not re-copy it.
- ⚑ **Item 12's falsifier is the one that matters: one-step convergence.** After regenerating and
  committing, a second close must ALLOW. If it still blocks, the circularity has been reproduced
  in new clothes and the note's central by-construction claim (§2.10) is false. **Prove the whole
  sequence in the test** — block → regenerate → commit → close → ALLOW — not just the block.
- ⚑ **Item 14 is irreversible and gated on a human-grade verification.** Before deleting: read
  `docs/roles/orchestrator/handoff.md` + the journal's authoritative segment and confirm the
  in-flight unit and the next action are answerable **from those alone**. The brief has no
  history. Copy it to a scratch path outside the repo first.
- **The "no live reference remains" criterion is scoped to FIVE files**, deliberately: 38 files
  in the tree contain `resume-brief`, and nearly all are ratified notes (A8 — unwritable),
  findings, historical journals, `CHANGELOG.md`, brainstorms, `docs/book/`, `docs/PROGRESS.md`,
  `docs/PARKING-LOT.md`. A repo-wide grep criterion would be **unbuildable**. §3 Q5 enumerates
  the five.
- **`--check`'s mechanism is not pinned** (§3 Q2 — subprocess vs import). The plan bounds it with
  three criteria: no second `git` call (the owner DRY rule stated at `_lib.py:738-743`), fail-open
  on any generator error, never runs a MEASURED command. **Measure the Stop latency and record it
  as a MEASURED reading** — that is what settles the choice.
- **`session-brief.sh`'s baseline write at `:63-65` is untouched.** Clause (e′) check 2 keys on
  that file's mtime, and clause (c)'s consumer chain depends on it. So is the worktree-aware
  `ROOT` resolution (`:19-26`) and the deskcheck-owed line (`:51-61`).
  *(Note: A9's text cites the baseline write as `session-brief.sh:52`; it is `:65` in the tree
  today. A9 lives in a ratified note — record, do not edit.)*
- **`docs/roles/**` is in `write_scope` because this plan's own close is judged by the clause it
  installs.** Once (e′) lands, closing requires a fresh rendering and a seat-journal entry.
  Without that entry the builder would be denied the very files its new gate demands.
- **Amendment A10 and the `dn-session-handoff-gate` partial supersession are BOTH owner
  hand-acts.** `scope-guard` denies a ratified note pre-hoc (`_lib.py:435-441`) and Stop (b2)
  blocks the Bash path (`_lib.py:797-824`). See `docs/findings/finding-0233.md`. Draft the A10
  text here for a one-paste landing; attempt neither edit.

## Owed at seal (orchestrator, not the builder)

- A `## Follow-through` block is required by clause (f).
- The **A10 amendment text**, drafted for the owner: §5 gains the role registry, §6's journal-gate
  clause enumeration extends to (e′), §9 states the seat generalization.
- The **partial supersession** of `dn-session-handoff-gate` §2.2–2.3 is effective on this merge.
  Record the effective commit here; the owner records it in the amendment log. `superseded_by` on
  that note is deliberately **not** set (note §1.1 — the note is not wholly replaced).
- The **Stop-latency measurement** for (e′) check 1 — as a MEASURED reading in
  `docs/roles/orchestrator/readings.md`, and repeated here.
- Re-verify at `/build` time that **no other plan holds `.claude/hooks/**`.** Scanned clean at
  graduation (2026-07-26) across bp-111…bp-119 and bp-123, but the ops wave is live.

## Follow-through

- **Built?** Yes, and proven rather than asserted: clause (e′) with both checks, the SessionStart
  re-point, and the template's retirement, in one commit. The central claim — one-step convergence
  — is demonstrated as a sequence in a throwaway repo. **Nine adversarial mutations across two
  passes; two survived and each forced a real test**: check 2's session-start key (found by me),
  and the fail-open `except` arm (found by the pre-merge audit). The audit also found the one
  merge-blocking defect — check 1 keying on `rc == 1`, which conflates *stale* with *crashed* and
  **wedged** the close — now fixed by positively identifying staleness from the generator's own
  rendered signature, with all six failure modes re-measured by execution as fail-open.
  ⚑ **Neither survivor was found by reading; both came from mutating and running.**
- **Wired, or dormant?** **Fully wired, and unavoidably so** — this is not a flag-off deliverable.
  `journal-gate` (Stop) and `session-brief` (SessionStart) are already registered in
  `.claude/settings.json`; this plan edits their bodies, so the moment it merges, **every**
  orchestrator session's start reads the seat and every close is judged by (e′). There is no ON
  switch to build and none to forget. The one thing that is *not* wired is the live file's
  deletion, and that is deliberate: it is withheld for the orchestrator's hand.
- **Who consumes it?** Every agent, at every SessionStart, and every orchestrator session at every
  close. `bp-127` consumes it directly: F1c asserts the post-cutover checkout and F1b lints the
  authoritative segment this gate keys on. Its entry condition is now met.
- **Track state?** `workflow`. This is stage (b) of `dn-role-state-and-scoped-handoff` §4's
  enablement sequence; **stage (c) is `bp-127`, which is `ready` and unblocked by this merge.** The
  note is not fully discharged until F1b, F1c and the F2 drill land. ⚑ Two owner hand-acts stand
  between this plan and a clean record: the A10 amendment and the partial-supersession log entry.
- **New track or finding?** Three findings, no new track: `finding-0244` (`spec-fidelity` →
  builder, resolved in place, with a design-level re-entry), `finding-0245` (`discovery` →
  orchestrator, discharged by the first compaction capsule), and `finding-0246` (`spec-defect` →
  orchestrator). None blocks the merge. **`finding-0246` is the one that must be settled before
  `bp-127`** — its F2 drill spawns agents from inside a session and meets the defect immediately.

### ⚑ Post-seal addendum — the gate blocked its own author, and a budget probe laundered the block

I ran the new clause against my own close as a final check. It **blocked**, correctly and usefully:

```
BLOCK: (e′) commits landed this session but docs/roles/orchestrator/journal.md carries no entry
from this session — append one … then close again. It is keyed to session START, so a later
commit cannot re-arm it.
```

The reason names the artifact, the act, and the clause — the "block reason IS the automation"
contract, discharged. But the *cause* was not that I had forgotten: my seat entry was written at
`02:02:49` and the baseline's mtime was `02:04:56`, and what moved the baseline was the
`claude -p "/usage"` **budget probe** run between them. A nested one-shot fires SessionStart.
Confirmed by direct experiment (`claude -p "reply with the single word: ok"`): the baseline's mtime
jumped `02:04:56 → 02:09:03` and its **content** was reset to current HEAD. Immediately after, the
same `stop-audit` printed **`ALLOW`** with the seat journal *still* stale — the block was not
satisfied, it was **laundered**, because the commits-this-session guard had been reset.

Three honest consequences, all recorded in `finding-0246`:

1. The **silencing** half is **pre-existing** and applies to clause (e) exactly as it does to (e′);
   this plan did not introduce it and, on this evidence, nobody had noticed it.
2. The **spurious arming** half **is** introduced here, by check 2's new dependence on the
   baseline's *mtime*. That is a cry-wolf path — the failure mode §2.10.3 rules out for MEASURED —
   arriving through NARRATIVE.
3. **I did not patch it**, though `session-brief.sh` is in `write_scope` and the fix was reachable.
   Item 13's invariants pin the baseline write as untouched, the file has three consumers, and each
   obvious one-line guard breaks a different one. Filed and routed instead.

I did not attempt to close under a laundered ALLOW. The entry that discharges check 2 honestly is
in the seat journal, and it carries this discovery — which is exactly the judgement a generator
could not have written.

### ⚑ A third vacuity, noticed while relocating this block — reported, not filed

This section was physically **above** the audit-response entry until now, and clause (f) still
reported satisfied. It should not have: `_journal_tail_has_followthrough` takes the tail from the
**last** `## ` heading that is not Follow-through/Markers, and this journal is written
**newest-first** (§9's "newest entry first"), so its tail is the *oldest* content — the pre-build
notes. What satisfied the grep was the sentence *"A `## Follow-through` block is required by
clause (f)"* in the "Owed at seal" list: **a backticked prose mention of the header, in a section
written before the build started.**

So (f) is satisfiable, in any newest-first journal, by a file that mentions the header without
ever carrying the block. `_lib.py` already calls the clause "grep-class … the (a)-staleness family
of crude post-hoc checks", so the weakness is acknowledged in kind — but *this* instance is a
genuine vacuous pass, and it is the third one this build has met (the withheld deletion, the
`--check` rc, and now this). **Fixed here by moving the block to the physical end of the file**, so
what satisfies the clause is the real block. Not filed as a fourth finding: it is pre-existing,
out of this plan's items, and the auditor holds the merge — flagged to them for the call.

