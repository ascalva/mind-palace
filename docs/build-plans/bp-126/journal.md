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
