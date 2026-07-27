---
type: build-plan
id: bp-126
track: workflow
status: complete
design_ref:
  - docs/design-notes/role-state-and-scoped-handoff.md
contract: builder
write_scope:
  - .claude/hooks/_lib.py
  - .claude/hooks/session-brief.sh
  - tests/integration/test_handoff_gate.py
  - docs/templates/resume-brief.md
  - .claude/state/resume-brief.md
  - docs/roles/**
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 500k
  actual: null
depends_on:
  - bp-124
  - bp-125
parallelizable_with: []
created: 2026-07-26
updated: 2026-07-26
links:
  - docs/design-notes/role-state-and-scoped-handoff.md
  - docs/design-notes/session-handoff-gate.md
  - docs/findings/finding-0175.md
  - docs/findings/finding-0233.md
  - docs/findings/finding-0234.md
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — the cutover: clause (e′), the re-point, and the brief's retirement

> **Every section below is required.** A section that does not apply is marked
> `N/A — <one-line reason>`, never silently omitted.

## 0. Mode & provenance

Investigation and planning produced this plan; implementation proceeds item-by-item on
owner approval. It graduates `dn-role-state-and-scoped-handoff` §2.10 (clause (e′)) and the
retirement clause of §2.9, and it is stage (b) of the note's §4 enablement sequence.

Authority-to-act is separate from the readiness blessing. **This plan is `proposed`; no
agent flips it to `ready`.**

**⚑ THIS IS THE HIGHEST-BLAST-RADIUS PLAN IN THE FAMILY, AND IT IS DELIBERATELY ATOMIC.**
It deletes an artifact that **every agent reads at every SessionStart**, re-points the hook
that reads it, and replaces the Stop-gate clause that demands it — **in one diff**. The
atomicity is a correctness requirement, not a preference:

- delete the brief but leave clause (e) → **every orchestrator session that commits is
  permanently unable to close** (a missing brief is infinitely stale
  `[GROUNDED .claude/hooks/_lib.py:909-913]`). A repo-wide deadlock.
- replace clause (e) but leave the re-point → SessionStart surfaces a brief nothing
  maintains, and the seat's rendering is never read.
- re-point but leave clause (e) → the orchestrator must keep writing a brief it can no
  longer see.

There is no safe intermediate state. The plan lands whole or it is reverted whole.

**The overlapping window closes here.** Note §4: stage (a) is bp-124 + bp-125 merged, where
"clause (e) still governs (old brief still written — a deliberately overlapping window, at
the cost of double bookkeeping for its duration)"; stage (b) is this plan, where "clause (e′)
governs, the brief and its template are deleted in the same diff, `session-brief.sh`
re-points." **The re-point belongs here, not in bp-125** — the note's §3 sketch put it in P1
and its §4 put it at stage (b); §4 is the operative sequencing statement and is followed. See
`finding-0234` correction (1).

## 1. Objective

In one diff: replace Stop-gate clause (e) with clause (e′) (idempotence for DERIVED,
session-baseline freshness for NARRATIVE, MEASURED ungated), re-point `session-brief.sh` to
the handoff pair, and delete the resume brief and its template.

## 2. Context manifest

Read exactly these, in order, before any work:

1. `docs/design-notes/role-state-and-scoped-handoff.md` — the ratified decision, whole.
   **§2.10 is this plan's specification** (clause (e′), the by-construction claim, residuals
   R1/R2); §2.9's "What retires"; §4's enablement sequence.
2. `docs/design-notes/session-handoff-gate.md` — the note being **partially superseded**
   (§2.2 block condition, §2.3 freshness signal). Its §1 purpose and §2.4 scope key survive
   unchanged; read to know precisely what survives.
3. `.claude/hooks/_lib.py` — read `cmd_stop_audit` whole (`:734-943`). Clause (e) is
   `:892-920`; the shared git call is `:744-755`; clause (a) is `:757-768`; clause (f) is
   `:922-937`. Do not skim: (e′) must not disturb (a)–(d) or (f).
4. `.claude/hooks/session-brief.sh` — read whole (69 lines). The auto-surface is `:38-47`;
   the baseline write is `:63-65`.
5. `tests/integration/test_handoff_gate.py` — read whole (225 lines). Its six cases are
   this plan's regression contract; each must be re-expressed against (e′), not deleted.
6. `scripts/handoff.py` and `docs/roles/orchestrator/` — bp-124's generator and artifacts.
   Clause (e′) check 1 consumes `--check`; the builder must know its exit contract.
7. `docs/findings/finding-0234.md` — correction (1) is why the re-point lands here.
8. `docs/findings/finding-0233.md` — why amendment A10 is **not** attempted in this plan.
9. `docs/findings/finding-0236.md` — ⚑ **binding on clause (e′) check 1.** bp-124 renders one
   computation **two ways**: `--write` / `--check` / `--json` are pure functions of the
   artifact tree (no queue state, no wall clock, no HEAD sha, no environment), while a bare
   render to stdout is live. This is what keeps (e′) computed off **the work** rather than off
   **the daemon** — a queue count in the committed artifact would make two regenerations of an
   unchanged tree differ, and staleness would fire on daemon activity. Check 1 must therefore
   **shell out to `--check`** and must never re-implement the compare over a live render.
10. `docs/findings/finding-0238.md` — bp-124's independent pre-merge audit. Two operational
    facts for this plan: the `--check` exit contract is verified end to end (0 = up to date,
    non-zero = stale, and regeneration converges in **exactly one step**); and the rendering
    reads `readings.md`, so appending a reading *after* regenerating re-arms check 1 once —
    regenerate the handoff **last**, after all other artifact writes.
11. `docs/findings/finding-0241.md` and `docs/findings/finding-0242.md` — ⚑⚑ **BINDING ON THE
    DELETION, AND THE MOST IMPORTANT THING IN THIS MANIFEST.** `.claude/state/resume-brief.md`
    is **gitignored and was never tracked**, so once you delete it there is no `git show`, no
    reflog, and no recovery — the artifact chain's usual safety net does not exist here.
    bp-125 migrated the brief's non-derivable content out, but it worked from a **snapshot**,
    and the live file **changed underneath it mid-build**: the delta carried an owner ruling on
    commit economy whose only other copy was, at that moment, an untracked file. It was rescued
    only because bp-125's builder re-diffed at seal.
    **Therefore, before you delete anything:** (a) `cp` the live brief to a **tracked** path and
    commit it in the same diff as the deletion, so the pre-deletion state has git history;
    (b) diff the live file against bp-125's snapshot digests (pinned in finding-0241) and
    migrate anything that arrived after the snapshot; (c) if the digest does not match, the
    finding gives you a tripwire but **not** a recovery — a delta is detectable and not
    computable — so step (a) is what makes this safe, not step (b).
    ⚑ Do **not** treat a matching digest as permission to skip (a).

**Does `core/` already implement this? (the DRY audit.)** N/A in the algorithmic sense — no
algorithm or primitive is introduced. The DRY constraint that *does* bind is the owner rule
already encoded in the file being edited: `cmd_stop_audit` fetches HEAD sha and last-commit
epoch in **one** subprocess shared by clauses (a) and (e) — *"owner DRY rule: never a second
git call"* `[GROUNDED .claude/hooks/_lib.py:738-743]`. Clause (e′) must honor it: it may
reuse `head_sha`, and it must not add a second `git` invocation. Whether it may add a
**non-git** subprocess (the generator) is §3 Q2 — an open question, answered honestly there.

## 3. Investigation & grounding  <!-- Part A -->

- **Q1 — Where exactly is clause (e), and what does it actually check?**
  `[GROUNDED .claude/hooks/_lib.py:892-920]`, inside `cmd_stop_audit`. Verified line by line
  at graduation:
  - `:899` — `if plan is None:` (orchestrator posture only; builder sessions carry a plan and
    are governed by (a)).
  - `:900-907` — read `.claude/state/session-baseline`; on any exception `baseline = ""`,
    i.e. **fail-open**.
  - `:908` — `if baseline and head_sha and head_sha != baseline:` — the commits-this-session
    guard.
  - `:909` — `brief_abs = …/.claude/state/resume-brief.md`.
  - **`:911` — `brief_fresh = os.path.getmtime(brief_abs) >= last_commit`** — the freshness
    test, mtime vs **last-commit time**.
  - `:912-913` — `except OSError: brief_fresh = False  # missing brief = infinitely stale`.
  - `:914-920` — the block reason, which instructs writing the brief *"citing the final
    commit hashes."*
  **⚑ `:762` is clause (a)**, the *journal* mtime check (`if os.path.getmtime(j_abs) <
  last_commit`) — **not** clause (e). The live brief mis-cites `:762` as clause (e)'s getmtime
  (note §2.2), and that stale citation has since propagated into at least one design prompt.
  Verified independently here; the builder must not re-copy the wrong number.

- **Q2 — How does clause (e′) check 1 compute "regenerating is a no-op"?**
  **The code does not settle this, and no artifact prescribes a mechanism.** The note (§2.10)
  specifies the *predicate* — "block unless regenerating the handoff rendering is byte-identical
  to the committed file" — and F1a (§2.11) specifies the *user-facing form* — "generator
  `--check` regenerates to a temp path and byte-compares." It does not say whether the hook
  shells out to the generator or re-implements the compare. Two admissible implementations:
  **(i) subprocess** `python3 scripts/handoff.py --role orchestrator --check` — reuses one
  implementation (DRY, and F1a and the gate are then provably the same check), at the cost of
  a process spawn on every orchestrator Stop; **(ii) import** the generator module from
  `_lib.py` — no spawn, but inverts the existing dependency direction (today `scripts/*.py`
  import `_lib`, `[GROUNDED scripts/board.py:28-33]`), and `_lib.py` is deliberately
  stdlib-only hook code.
  **This plan does not pick; it bounds the choice** with criteria that are checkable either
  way (Item 12): the check must (a) add **no** second `git` call, (b) **fail open** on any
  generator error or absence — enforcement never crashes a close, matching the `except`
  posture at `:906-907` and `:889-890` — and (c) never run the test suite or any MEASURED
  command. **What would settle the choice:** measuring the added Stop latency of (i) against
  a real tree; if a spawn costs more than a few hundred milliseconds it is the wrong shape and
  (ii) earns its inversion. Record the measurement in the journal as a MEASURED reading.

- **Q3 — What is the NARRATIVE freshness signal, precisely?** Note §2.10 check 2: block
  unless the seat journal's mtime ≥ **the SessionStart baseline write**, i.e. the mtime of
  `.claude/state/session-baseline`, written at `session-brief.sh:65` by
  `git -C "$ROOT" rev-parse HEAD > "$ROOT/.claude/state/session-baseline"`
  `[GROUNDED .claude/hooks/session-brief.sh:63-65]`. **This is deliberately not the
  last-commit time** that clause (a) and clause (e) use: keyed to session start, a late commit
  cannot re-arm the check, which is the circularity being cut. *(The note cites this line as
  `session-brief.sh:65`; amendment A9 cites the same write as `:52`. `:65` is correct in the
  tree today — verified — and `:52` is a stale citation in the A9 text. Recorded, not acted
  on: A9 lives in a ratified note.)*

- **Q4 — What does `session-brief.sh` do today, verbatim?**
  `[GROUNDED .claude/hooks/session-brief.sh:46-47]`:
  ```bash
  _RB="$ROOT/.claude/state/resume-brief.md"
  if [ -r "$_RB" ]; then cat "$_RB"; echo; fi
  ```
  Two lines, guarded by `[ -r ]`, emitting **before** `python3 "$LIB" brief` at `:49`. The
  note cites this as `:46-48`; `:48` is blank. The surrounding comment block `:38-45` explains
  the finding-0035 rationale and must be rewritten, not left describing a deleted artifact.
  The hook's fail-open/fail-loud posture (`trap` at `:34`, `fail_loud` at `:30-33`) is
  load-bearing and must survive: **a missing handoff rendering must never error the hook.**

- **Q5 — Which files may this plan's "no live reference remains" criterion actually touch?**
  Measured at graduation: 38 files contain the string `resume-brief`. All but five are
  **immutable or out of role**: ratified design notes (`agent-workflow.md`,
  `session-handoff-gate.md`, `track-board-and-deskcheck-gate.md`,
  `role-state-and-scoped-handoff.md` — agent-immutable, A8), nine findings, eight build-plan
  journals/plans, `CHANGELOG.md`, `docs/book/chapters/02-architecture.tex` (scribe surface),
  seven brainstorms, and `docs/PROGRESS.md` + `docs/PARKING-LOT.md` (orchestrator
  single-writer, explicit non-goals). **The five live operational surfaces are:**
  `.claude/hooks/_lib.py`, `.claude/hooks/session-brief.sh`,
  `.claude/skills/context-economy/SKILL.md` (**bp-125's**, already clean by then),
  `docs/templates/resume-brief.md` (deleted here), `tests/integration/test_handoff_gate.py`.
  Item 14's criterion is scoped to exactly that set — a repo-wide grep criterion would be
  **unbuildable**, since most matches are in files no agent may edit.

- **Q6 — Is the live brief deletable from a worktree?** No — and nothing needs to be.
  `.claude/state/**` is gitignored per-worktree; a fresh worktree contains only
  `.claude/state/.gitignore` (verified 2026-07-26), so there is no brief there to delete and
  its deletion produces **no diff** and is invisible to the Stop-gate (b) audit. The *tracked*
  deletion in this plan is `docs/templates/resume-brief.md` alone. The live file's removal is
  a **main-checkout housekeeping act**; it is listed in `write_scope` so that a session running
  in the main checkout can perform it with a tool rather than being denied, and §7 Item 14
  states it as conditional-on-presence, never as a criterion a worktree cannot satisfy.

- **Q7 — What does the existing gate test pin?** Six cases
  `[GROUNDED tests/integration/test_handoff_gate.py:17-23]`: (1) block on commits + stale
  brief; (2) block on commits + missing brief; (3) allow on no-commits; (4) allow on fresh
  brief; (5) fail-open allow on missing baseline; (6) silent under an active plan. Cases
  (3), (5), (6) are **posture invariants that survive (e′) unchanged** and must still pass in
  spirit. Cases (1), (2), (4) are brief-specific and are re-expressed against the rendering
  and the seat journal. The fixture builds a throwaway git repo under `tmp_path` and asserts
  on the `ALLOW`/`BLOCK:` line — reuse that shape.

- **Q8 — Can this plan land amendment A10?** **No** — `docs/design-notes/agent-workflow.md`
  is `status: ratified` and `scope-guard` denies the write before the write-scope check runs
  `[GROUNDED .claude/hooks/_lib.py:435-441]`; the Stop-gate (b2) clause blocks the Bash path
  against HEAD status `[GROUNDED .claude/hooks/_lib.py:797-824]`. Warrant `finding-0233`;
  parked as an owner act in §11.

**Additional risks or questions surfaced during reading:**

- **This plan's own close is governed by the clause it installs.** Once (e′) lands, the
  builder's final Stop is judged by it. The recovery is one mechanical step by construction
  (regenerate, commit, close) — but if (e′) is wrong, the session may be unable to close at
  all. Item 12's acceptance therefore requires the throwaway-repo tests to pass **before**
  the clause is trusted on the real repo.
- `.claude/settings.json` needs **no** change: `journal-gate` (Stop) and `session-brief`
  (SessionStart) are already registered; this plan edits their bodies, not their registration.
- The block-reason **text** is part of the contract: the note calls the reason "the
  automation" (it tells the agent exactly how to recover). A vague reason is a defect even if
  the predicate is right.

## 4. Reconciliation  <!-- Part B -->

- `.claude/hooks/_lib.py:892-898` (the clause comment) — currently:

  > *"(e) session-handoff gate (dn-session-handoff-gate §2.2) -> orchestrator posture only …
  > BLOCK when commits landed THIS session (HEAD moved past the SessionStart baseline) but the
  > resume brief is stale (mtime older than the last commit) or absent … The block reason IS
  > the automation — it instructs writing the brief."*

  → **[banner: correction]**. Replaced by an `(e′)` comment that names its warrant
  (`dn-role-state-and-scoped-handoff` §2.10), states that it **supersedes (e) of
  `dn-session-handoff-gate` §2.2–2.3**, and records the two checks and the deliberate
  ungating of MEASURED. The superseded design is named in the comment, not silently dropped —
  a reader of this file must be able to see that a prior ratified decision was replaced and by
  what.

- `.claude/hooks/_lib.py:914-920` (the block reason) — currently instructs
  *"write .claude/state/resume-brief.md (the resume-brief shape, context-economy skill) citing
  the final commit hashes, then close again."* → **[banner: correction]**: the new reason
  instructs the **one-step convergent** recovery — regenerate with `--write`, commit, close
  again — and, for check 2, "add an entry to the seat journal." *The "citing the final commit
  hashes" instruction is the content-demand half of the circularity (note §2.10) and must not
  survive in any form.*

- `.claude/hooks/session-brief.sh:38-47` (the auto-surface block and its comment) —
  currently: *"Auto-surface the orchestrator's self-resume brief (finding-0035, bp-014 Item 3):
  if the worktree-local .claude/state/resume-brief.md exists, emit it at the TOP of the SESSION
  BRIEF …"* → **[banner: correction]**: replaced by a block surfacing
  `docs/roles/orchestrator/handoff.md` **and** the seat journal's authoritative segment
  (capsule + suffix), with a comment naming the supersession and preserving the fail-open
  property verbatim ("a missing or unreadable file never errors the hook").

- `tests/integration/test_handoff_gate.py:1-28` (the module docstring pinning the (e)
  condition) — → **[banner: correction]**: rewritten to pin (e′)'s two checks, explicitly
  noting which of the six original cases survive as posture invariants (3, 5, 6) and which are
  re-expressed (1, 2, 4). The file is not deleted — its regression value is the posture
  coverage, and deleting it would silently drop cases (3)/(5)/(6).

- `docs/design-notes/session-handoff-gate.md` — **partially superseded, and not edited.**
  Note §1.1 rules that the partial supersession is recorded by the owner's hand in the
  amendment log, and that `superseded_by` is deliberately **not** set (the note is not wholly
  replaced). The builder records the effective date in its journal; it does not touch the note.

- `docs/design-notes/agent-workflow.md` — amendment A10 → **not attempted** (finding-0233).
  The exact A10 text is drafted into this plan's journal for the owner to land by hand.

## 5. Write scope

Front-matter globs, mirrored with rationale (bare globs in the front matter — no inline
comments, per finding-0085):

- `.claude/hooks/_lib.py` — clause (e) → (e′). The plan's principal deliverable.
- `.claude/hooks/session-brief.sh` — the auto-surface re-point.
- `tests/integration/test_handoff_gate.py` — **carried because it pins the surface this plan
  moves.** Its six cases assert (e)'s exact block condition
  `[GROUNDED tests/integration/test_handoff_gate.py:5-13]`; changing the clause reddens it,
  and it is outside a naïve "hooks only" scope.
- `docs/templates/resume-brief.md` — **carried so it can be deleted.** A deletion is a write;
  without this entry the Stop-gate (b) out-of-scope audit flags the removal and the plan
  cannot close.
- `.claude/state/resume-brief.md` — carried so a main-checkout session can remove the live
  file with a tool rather than being denied (§3 Q6). Gitignored, so its removal produces no
  diff; in a worktree there is nothing to remove and the criterion is satisfied vacuously.
- `docs/roles/**` — **carried because this plan's own close is judged by the clause it
  installs.** Once (e′) lands, closing requires a fresh rendering and a seat-journal entry;
  without this entry the builder is denied the very files its new gate demands. *This is the
  acceptance-reachability trap in miniature: the criterion is created by the plan itself.*

**Deliberately OUT of scope, and why:**

- `scripts/handoff.py` — bp-124's. If `--check`'s contract is wrong for the gate, that is a
  finding against bp-124, not an edit here. (The gate **consumes** the generator; it must not
  reshape it mid-cutover.)
- `.claude/skills/**` — bp-125's. context-economy is already brief-free by the time this
  plan runs; re-editing it here would collide with a merged plan's diff.
- `.claude/settings.json` — no hook registration changes (§3, additional risks).
- `docs/design-notes/**` — ratified, agent-immutable (A8). Both the A10 amendment
  (finding-0233) and the `dn-session-handoff-gate` partial supersession are **owner hand-acts**.
- `docs/PROGRESS.md`, `docs/PARKING-LOT.md`, `docs/book/**`, `docs/brainstorms/**`,
  `CHANGELOG.md`, prior build-plan journals — all contain the string `resume-brief` and all
  are out of role or historical. Item 14's criterion is scoped to the five live surfaces
  (§3 Q5) precisely so it stays buildable.
- `docs/findings/**` — always writable, not listed by convention.

## 6. Interfaces pinned inline

**Clause (e) as it exists today — the code being replaced, verbatim
`[.claude/hooks/_lib.py:899-920]`:**

```python
    if plan is None:
        try:
            with open(
                os.path.join(ROOT, ".claude", "state", "session-baseline"),
                encoding="utf-8",
            ) as fh:
                baseline = fh.read().strip()
        except Exception:
            baseline = ""  # missing/unreadable baseline -> fail-open (skip)
        if baseline and head_sha and head_sha != baseline:
            brief_abs = os.path.join(ROOT, ".claude", "state", "resume-brief.md")
            try:
                brief_fresh = os.path.getmtime(brief_abs) >= last_commit
            except OSError:
                brief_fresh = False  # missing brief = infinitely stale
            if not brief_fresh:
                reasons.append(
                    "(e) commits landed this session but the resume brief is stale "
                    "or missing — write .claude/state/resume-brief.md (the resume-"
                    "brief shape, context-economy skill) citing the final commit "
                    "hashes, then close again (dn-session-handoff-gate)."
                )
```

**The shared git call that must not be duplicated `[.claude/hooks/_lib.py:744-755]`:**

```python
        _headline = subprocess.run(
            ["git", "log", "-1", "--format=%H %ct"],
            capture_output=True, text=True, cwd=ROOT, check=True,
        ).stdout.split()
        head_sha = _headline[0] if _headline else ""
        last_commit = int(_headline[1]) if len(_headline) > 1 else 0
```

`head_sha` and `last_commit` are already in scope at clause (e)'s site. **(e′) adds no second
`git` invocation** (`:738-743`, the owner DRY rule stated in the file).

**Clause (e′) — the specification (note §2.10), pinned as the contract:**

> Orchestrator posture (`plan is None`), commits landed this session
> (`baseline and head_sha and head_sha != baseline`):
>
> 1. **DERIVED freshness = idempotence, not mtime.** Block unless regenerating the handoff
>    rendering is a **no-op** (byte-identical to the committed file). The block reason
>    instructs: run the generator with `--write`, commit, close again. Because of the §2.9
>    idempotence pin, that recovery converges in **exactly one step** — the regen commit does
>    not re-arm the check. This upgrades the signal from a launderable mtime (tier 5) to a
>    content compare (tier 4).
> 2. **NARRATIVE freshness = an entry for this session.** Block unless the seat journal's
>    mtime ≥ the SessionStart baseline write (`session-brief.sh:65`). Keyed to *session
>    start*, not to *last commit* — deliberately: the narrative contains no commit-derived
>    facts (purity rule), so an entry written mid-session before a final seal commit is still
>    truthful, and a late commit cannot re-arm this check.
> 3. **MEASURED: not gated.** A reading is taken when the work warrants it; the pane shows
>    age. Gating a 17-minute suite reading at every close would either block honest closes or
>    train `touch`-laundering — the cry-wolf disqualifier.

**The two accepted residuals (note §2.10) — carry them into the comment, do not overclaim:**
- **R1:** a session may commit *after* its last narrative entry and close; the final commits
  are mechanically visible but the judgement about them may be missing. Same "existence, not
  quality" stance as the ratified gate note, carried forward knowingly.
- **R2:** narrative purity is tier 4 only for the lintable class; an agent can still smuggle a
  count in prose. *"If R2's lint proves too weak in practice, that is a finding against this
  note, not a silent widening."*
- **mtime laundering** (a Bash `touch` defeating check 2) remains possible — the identical
  porosity clauses (a) and (e) accept today; **pre-hoc porous, post-hoc tight** targets
  forgetting, not adversarial evasion.

**`session-brief.sh` today — the block being replaced, verbatim `[:46-47]`:**

```bash
_RB="$ROOT/.claude/state/resume-brief.md"
if [ -r "$_RB" ]; then cat "$_RB"; echo; fi
```

The replacement surfaces `docs/roles/orchestrator/handoff.md` **and** the seat journal's
**authoritative segment** (note §2.8: *the latest capsule plus all entries after it*; a
journal with no capsule yet is wholly authoritative). The `[ -r ]` guard pattern and the
hook's fail-open posture are preserved: **a missing file never errors the hook.**

**The hook's failure posture, which must survive unchanged `[.claude/hooks/session-brief.sh:30-34]`:**

```bash
fail_loud() {
  printf 'HOOK-FAILURE %s: %s — enforcement NOT applied\n' "$NAME" "$1" >&2
  python3 "$LIB" marker "HOOK-FAILURE $NAME: $1 — enforcement NOT applied" >/dev/null 2>&1 || true
}
trap 'rc=$?; [ "$HOOK_INTENTIONAL" = 1 ] || fail_loud "unexpected exit rc=$rc"' EXIT
```

**The six existing test cases `[tests/integration/test_handoff_gate.py:17-23]`:**

```
  (1) block on commits + stale brief
  (2) block on commits + missing brief
  (3) allow on no-commits (baseline == HEAD, brief stale)
  (4) allow on fresh brief (mtime > last commit)
  (5) fail-open allow on missing baseline
  (6) silent under an active plan (decided by (a)-(d) only)
```

**What retires (note §2.9), verbatim:** *"`.claude/state/resume-brief.md` (both halves
replaced), its template `docs/templates/resume-brief.md` … and the self-rewrite instruction
(replaced by §2.10's mechanics). `session-brief.sh`'s auto-surface (`:46-48`) re-points from
the brief to `handoff.md` + the journal's authoritative segment. `docs/PROGRESS.md` is
untouched."*

## 7. Items

Ordered by blast radius: the gate is built and proven in a throwaway repo **before** anything
is deleted; deletion is last.

### Item 12 — clause (e′) in `cmd_stop_audit`, proven in a throwaway repo

- **Objective:** replace clause (e) with (e′)'s two checks, preserving every posture invariant
  of (a)–(d) and (f).
- **Files:** `.claude/hooks/_lib.py`, `tests/integration/test_handoff_gate.py`
- **Acceptance test:** `uv run pytest tests/integration/test_handoff_gate.py` green, covering:
  **(e′-1)** commits + a rendering that differs from a fresh regeneration → BLOCK citing (e′);
  **(e′-2)** commits + seat journal mtime older than `session-baseline`'s mtime → BLOCK citing
  (e′); **(e′-3)** commits + fresh rendering + fresh journal entry → ALLOW; **(e′-4)** commits
  + a **stale MEASURED readings log** → **ALLOW** (the explicit negative: MEASURED is never
  gated); plus the three surviving posture invariants — no-commits → ALLOW; missing
  `session-baseline` → fail-open ALLOW; active plan → (e′) silent. `grep -c 'resume-brief'
  .claude/hooks/_lib.py` returns **0**.
- **Falsifier:** **the one-step convergence fails** — after regenerating and committing, a
  second close still blocks on check 1. That is the circularity reproduced in new clothes and
  it falsifies the note's central by-construction claim (§2.10). Prove convergence explicitly
  in the test: block → regenerate → commit → close → ALLOW, in one sequence.
  Equally falsifying: (e′) fires in builder posture, or a clause (a)/(f) test reddens.
- **Invariant(s) it must not violate:** **no second `git` subprocess** (§6); fail-open on a
  missing/unreadable baseline **and** on any generator error — enforcement never crashes a
  close; (e′) is silent when `plan is not None`; clause (f)'s verbatim `## Follow-through`
  grep is untouched; the block reason remains "the automation" (it states the exact recovery).
- **Touches stored data?** No. It changes when a session may end — a workflow-blast-radius
  change, which is why it is proven under `tmp_path` before the real repo runs it.
- **Parallelizable?** No.  **Depends on:** bp-124 (the generator's `--check`), bp-125 (a
  migrated journal to be fresh *about*).

### Item 13 — re-point `session-brief.sh` to the handoff pair

- **Objective:** SessionStart surfaces the seat's rendering and its authoritative narrative
  segment instead of the brief.
- **Files:** `.claude/hooks/session-brief.sh`
- **Acceptance test:** `bash .claude/hooks/session-brief.sh --standalone` in a checkout that
  has the seat artifacts emits the handoff rendering and the journal's authoritative segment,
  then the existing `python3 "$LIB" brief` output and the deskcheck-owed line, and **exits 0**;
  in a checkout where `docs/roles/orchestrator/handoff.md` is absent it still **exits 0**, emits
  the rest, and prints **no** `HOOK-FAILURE`. `grep -c 'resume-brief' .claude/hooks/session-brief.sh`
  returns **0**.
- **Falsifier:** the hook prints `HOOK-FAILURE` (or exits non-zero) when a seat file is
  missing. That would make every fresh clone's first session start with a failed hook — the
  fail-open posture `[:30-34]` broken, and a far worse failure than the one being fixed.
- **Invariant(s) it must not violate:** fail-open, fail-loud preserved; the baseline write at
  `:63-65` is **untouched** (clause (e′) check 2 keys on it, and clause (c)'s consumer chain
  depends on it); the worktree-aware `ROOT` resolution at `:19-26` is untouched; the
  deskcheck-owed line at `:51-61` is untouched.
- **Touches stored data?** No.
- **Parallelizable?** Yes — a different file from Item 12, no shared symbol.  **Depends on:**
  bp-124.

### Item 14 — retire the brief and its template

- **Objective:** the superseded artifacts are gone from the live surfaces, and nothing
  operational still points at them.
- **Files:** `docs/templates/resume-brief.md` (deleted), `.claude/state/resume-brief.md`
  (removed if present)
- **Acceptance test:** `docs/templates/resume-brief.md` does not exist and its deletion is
  staged (`git status --short` shows `D`); `.claude/state/resume-brief.md` does not exist **in
  this checkout** (vacuous in a worktree — §3 Q6); and a grep for `resume-brief` over **exactly
  the five live operational surfaces** — `.claude/hooks/_lib.py`,
  `.claude/hooks/session-brief.sh`, `.claude/skills/context-economy/SKILL.md`,
  `docs/templates/`, `tests/integration/test_handoff_gate.py` — returns **0** matches.
- **Falsifier:** a session started after this item cannot orient — i.e. the handoff pair does
  not in fact carry what the brief carried. **Verify before deleting**, not after: read
  `docs/roles/orchestrator/handoff.md` + the journal's authoritative segment and confirm the
  in-flight unit and the next action are both answerable from them alone. The brief has **no
  history** (gitignored — finding-0175's whole complaint), so this deletion is genuinely
  irreversible.
- **Invariant(s) it must not violate:** the grep criterion is scoped to the five live
  surfaces — **historical and immutable references are left exactly as they are** (ratified
  notes, findings, journals, `CHANGELOG.md`, brainstorms, `docs/book/`, `docs/PROGRESS.md`,
  `docs/PARKING-LOT.md`); keep-and-link binds the record, and A8 makes the notes unwritable
  anyway.
- **Touches stored data?** **Yes — irreversibly.** `.claude/state/resume-brief.md` is
  unversioned and unrecoverable. **Dry-run required:** copy the live brief to a scratch path
  outside the repo, complete the verification above, and only then remove.
- **Parallelizable?** No — **strictly last.**  **Depends on:** Items 12 and 13, and bp-125
  (the content must already have been migrated).

## 8. Math carried explicitly

N/A — no mathematical object is implemented. The one formal property the plan **relies on**
is the idempotence of the rendering (`render(tree)` is a fixed point after one regen commit),
which is bp-124's deliverable and bp-124's §7 acceptance; here it appears only as Item 12's
convergence falsifier, which is a behavioral test of the gate, not a mathematical object
needing a field-guide entry.

## 9. Non-goals

- **No generator changes.** `scripts/handoff.py` is bp-124's; a wrong `--check` contract is a
  finding, not an edit.
- **No skill edits.** bp-125 already made context-economy brief-free.
- **No amendment.** A10 to `dn-agent-workflow` is unbuildable by any agent (finding-0233) and
  is parked as an owner act (§11). The A10 **text** is drafted into the journal, which is a
  proposal, not a landing.
- **No supersession flip on `dn-session-handoff-gate`.** Note §1.1 rules that the partial
  supersession is recorded by the owner in the amendment log and that `superseded_by` is
  deliberately **not** set. A builder does neither.
- **No PROGRESS.md, PARKING-LOT.md, book, brainstorm, or CHANGELOG edits** — out of role and
  historical; their brief references become stale by design.
- **No back-fill and no history rewrite.** Prior journals and findings keep their references.
- **No new hook and no `settings.json` change.** This edits two registered hooks' bodies.
- **No drill.** F1b, F1c and the F2 harness are bp-127.
- **No widening of what (e′) gates.** MEASURED stays ungated; adding a readings-freshness
  check would be exactly the cry-wolf failure §2.10 names.

## 10. Stop-and-raise conditions

- **⚑ The one-step convergence cannot be demonstrated** (Item 12's falsifier) — **STOP and do
  not delete anything.** The whole cutover rests on (e′) being dischargeable by one mechanical
  command. Without it the family must not proceed: the old brief still exists, clause (e)
  still works, and reverting costs nothing at this point.
- **⚑ Item 14's pre-deletion verification fails** — the handoff pair does not carry what the
  brief carried — **STOP.** File a `spec-defect` finding against bp-125's migration and park.
  The brief is unrecoverable; deleting it on a failed verification is unrecoverable data loss,
  the single worst outcome available to this plan.
- **The hook fails open-loud in a fresh checkout** (Item 13's falsifier) — STOP; a broken
  SessionStart affects **every agent in every checkout**.
- **A clause other than (e) changes behavior** — any reddening of an (a)/(b)/(c)/(d)/(f) test
  is a blast-radius surprise. Stop and reconcile; those clauses have their own warrants and
  their own findings behind them.
- **The generator subprocess measurably slows every Stop** (§3 Q2) — record the measurement,
  switch to the import form, and note it; do not ship a gate that taxes every close.
- **A criterion needs a file outside §5** — file a `codebase` finding naming file and
  criterion; never route around `scope-guard`.
- **An edit to a ratified design note is implied** — never perform it
  `[GROUNDED .claude/hooks/_lib.py:435-441, 797-824]`. Route a finding.
- **A blessing is implied** — never perform it.
- **An owner-level question arises** — park the criterion with a re-entry condition and
  continue with the rest. Never block on the owner.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| **Amendment A10 to `dn-agent-workflow`** (note §1.1) | Not attempted. The exact A10 text — §5 gains the role registry, §6's enumeration extends to (e′), §9 states the seat generalization — is drafted into this plan's journal for a one-paste owner landing. | (a) Builder edits the note — **impossible**, `scope-guard` denies a ratified note before write_scope is consulted `[_lib.py:435-441]`; (b) Bash-write — blocked by (b2) `[_lib.py:797-824]`, and laundering; (c) supersede the whole note — disproportionate. | The owner lands A10 by hand once this plan merges (so the amendment describes a clause that exists). Warrant: `finding-0233`. |
| **Partial supersession of `dn-session-handoff-gate` §2.2–2.3** | Recorded in the journal as effective-on-merge; the note's front matter is **not** flipped. | Setting `superseded_by` — rejected by the design note itself (§1.1): the gate note is not *wholly* replaced; its §1 purpose and §2.4 scope key survive. | The owner's amendment-log entry, alongside A10. |
| **(e′) check 1 mechanism: subprocess vs import** (§3 Q2) | Not pinned. Bounded by three criteria (no second git call, fail-open, never runs MEASURED); the builder picks and records a latency reading. | Pinning subprocess now — rejected: the spawn cost on every orchestrator Stop is unmeasured. Pinning import now — rejected: inverts the established `scripts → _lib` dependency direction for an unquantified gain. | A measured Stop-latency delta. If a spawn exceeds a few hundred ms, the import form earns its inversion; record as a MEASURED reading either way. |
| **R2 — narrative purity lint strength** (note §2.10) | Tier 4 for the lintable class only (hash-shaped strings, status-transition phrasing); review-grade for the rest. Stated plainly rather than overclaimed. | Claiming tier-4 purity generally — rejected as overclaiming; the note forbids it. | *"If R2's lint proves too weak in practice, that is a finding against this note, not a silent widening."* The lint itself lands in bp-127 (F1b). |
| **R1 — the post-entry commit porosity** (note §2.10) | Accepted knowingly. A session may commit after its last narrative entry; the commits are mechanically visible, the judgement may be missing. | Gating on "an entry after the last commit" — rejected: that is exactly the re-arming circularity being removed. | An observed handoff failure traced to a missing post-commit judgement. |

## 12. Dependency & ordering summary

**Within this plan:** Item 12 ∥ Item 13 (different files, no shared symbol) → **Item 14
strictly last**. Blast-radius phase order: build and prove the gate under `tmp_path`
(Item 12) → change SessionStart's read, still non-destructive and revertible (Item 13) →
**irreversible deletion** (Item 14), gated behind an explicit pre-deletion verification.

**Across the family:**

```
bp-124  substrate + generator
   └─→ bp-125  migration + skill contracts   (MAIN CHECKOUT ONLY)
          └─→ bp-126 (this)  the atomic cutover
                 └─→ bp-127  the executable falsifier (F1b, F1c, F2)
```

- **Depends on bp-124** — Item 12 consumes `--check`; Item 13 surfaces `handoff.md`.
- **Depends on bp-125** — **load-bearing**: Item 14 deletes an unversioned artifact whose
  content must already have been migrated. Running this plan before bp-125 destroys the brief.
- **bp-127 depends on this plan** — F1c asserts the post-cutover checkout, and F1b lints the
  authoritative segment the new gate keys on.
- **⚑ MUTUAL EXCLUSION — this plan holds `.claude/hooks/**`.** Per the note (§3), **no other
  builder may run against `.claude/hooks/**` while this plan is in-progress.** Verified at
  graduation: no `ready` or `in-progress` plan (bp-111…bp-119, bp-123) carries
  `.claude/hooks/**`, `session-brief`, or `scripts/board.py` in its `write_scope`
  `[GROUNDED, scanned 2026-07-26]`. Re-verify at `/build` time — the ops wave is live and the
  set may have changed.
- **Parallelizable with:** nothing in this family. Disjoint from the live ops wave as scanned,
  but the exclusion above is a standing requirement, not a one-time check.
- **A standing consequence:** after this plan merges, **every** orchestrator session's close is
  judged by (e′). If (e′) is wrong, the failure is repo-wide and immediate — which is why
  Item 12's tests must be green before Item 14 runs.
