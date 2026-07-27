---
type: archive
id: archive-resume-brief-final
status: frozen
created: 2026-07-27
source: .claude/state/resume-brief.md
source_sha256: 7068b1a9ba64a162a06b3fddfd0ee083d4b4a57b9fd1ee35784196c0977286f6
source_lines: 163
source_bytes: 11622
taken_by: orchestrator (pre-emptive, before bp-126's cutover)
---

# ARCHIVE — the resume brief, preserved verbatim before its deletion

**Why this file exists.** `.claude/state/resume-brief.md` is **gitignored and was never tracked**,
so its deletion by bp-126 has no git safety net at all: once removed there is no `git show`, no
reflog, and no recovery. `finding-0241` established that the hazard is live rather than theoretical
— during bp-125's migration the file changed underneath the build, and the delta carried an owner
ruling whose only other copy was, at that moment, untracked.

This copy is taken **pre-emptively by the orchestrator**, ahead of the cutover, so that the
catastrophic case is closed before any builder touches the file. It does **not** discharge
bp-126's obligation: that plan must still take its own snapshot **at the moment of the deleting
commit**, because the live file may drift between this copy and that commit. A digest match against
this file is evidence, not permission.

**Content that exists only here and in the live file** (in no bp-125 migration snapshot):

1. ⚑ A **retraction of a false claim** — the reference substrate does **not** lack
   `corpus_to_corpus` edges. **644,785 exist** (bp-026 built them after the 2026-07-13 capsule the
   false claim was quoting). The real gap is **typing**: `ops/code_sensor.py:131-139` collapses
   `warrant` / `supersedes` / `links` / `depends_on` into a single `note-citation`, so zero typed
   rows exist. **If this retraction is lost, the false version is what survives** — precisely the
   laundering failure this wave exists to prevent.
2. A **severe unfiled data defect** — 39 hook-feedback rows attributed to `speaker='owner'`.
   Escalated to `oq-0060`; it amends a ratified note, so only the owner may set it.
3. The **measured clause-(e) data** — 108 firings / 99 fork-deduped over 8 days, 16 sessions,
   302 brief file-operations, peak day 36. Live input to clause (e)'s replacement.
4. A **fence against re-deriving the ratified query language**
   (`dn-core-query-protocol`, `dn-capability-scope`, `dn-chat-sensor`).

Verbatim copy follows the rule. Nothing below is edited.

---

# Orchestrator handoff — `75cb5cc` · opus[5]/high

## ⚑⚑ FIRST: A SUB-ORCHESTRATOR OWNS THE ACTIVE WAVE. **YOU DO NOT MERGE IT.**

Owner ruling, verbatim: *"sub-orchestrator will handle the merge and stand up its own auditor to
review before merging, **it manages the merge, not you**."*

It owns **bp-125 → bp-126 → bp-127**: spawning builders, standing up its own auditor, and merging.
Your instinct as a fresh orchestrator will be to audit and merge these. **Don't.** Verified alive
and working as of `b2743c4`; it survived a session clear once already.

**bp-124 is DONE** — merged `7df1841`, sealed `b2743c4`, `finding-0238` filed (its pre-merge audit).

If it later goes dead mid-wave: do NOT silently take over. Inspect the worktrees, say plainly what
state the wave is in, and ask the owner whether to re-spawn one or drive it yourself. A half-merged
wave is the bad outcome; guessing makes it worse.

## THE WAVE

**bp-125 is `in-progress`, AUDITED, and SENT BACK for six fixes** by the sub-orchestrator's own
auditor — which has since gone **idle**; it needs a nudge to continue, and it (not you) owns the
merge. ⚑ **bp-126/127 carry two pinned conditions from that audit (`f4c61ec`).** The brief is
gitignored and was **never tracked**, so its deletion has **no git safety net** — bp-126 must copy
it to a tracked path *in the same diff as the deletion*; a matching digest is NOT permission to
skip that. bp-125 proved the hazard live (finding-0241). They implement
`dn-role-state-and-scoped-handoff` — typed role state and a generated handoff, replacing this file.

⚑ **Blessing removed the WAIT, not the ORDERING.** Strictly serial: dependencies plus all three hold
`docs/roles/**`. Three green lights are **not** permission to fan out.

⚑ **bp-126 is the dangerous one.** It deletes `.claude/state/resume-brief.md` **and** its template
**and** re-points `session-brief.sh` in ONE diff. Atomicity is a correctness requirement: a missing
brief reads as infinitely stale to clause (e), so any intermediate state deadlocks every
orchestrator close. It also holds `.claude/hooks/**` exclusively.
⚑ **bp-125's §3 grounding is stale by my hand** — it was graduated against a 568-line brief that I
then cleared to ~100. Re-ground before Item 1; the re-entry is in its journal.

⚑ **BUDGET IS THE LIVE RISK.** The four plans estimate **≈1.9M tokens** before auditors. Last probe:
session 52% · week 43% (resets Jul 31, 8pm ET). Re-probe `claude -p "/usage"` before any spawn;
refuse one that cannot finish. A worker that dies at the limit burns everything it already spent.

## OWED BY THE OWNER — do not re-ask, they are on his phone

`~/.mind-palace/exhaust/owner-queue.md` (Syncthing). Two acts, **in this order**: order 3× YubiKey
**5C NFC** (not the Nano — no keyring hole), then harden the AWS root **recovery mailbox** *before*
registering any key. Five rulings open, **oq-0055 alone blocks anything** (bp-095 cannot honestly
start — both halves of its S↔F join are provably empty).
⚑ **finding-0235 needs his hand:** a ratified note's `track:` value carries an inline `#` comment,
corrupting the slug; the board reports a phantom orphan. Ratified ⇒ no agent may fix it.

## TRAPS THAT COST REAL TIME — each of these was paid for once already

- **The gate has TWO expected failures on a bare `pytest -q`:** the finding-0103 ratchet and
  `tests/e2e/test_dream_v2_live.py` (finding-0226). **Both carry `pytest.mark.live` and are NOT in
  the deploy gate or CI**, which run `-m "not live and not podman and not needs_vault and not
  needs_restic"`. Two seals claimed "1 failed" and were wrong. A *third*,
  `tests/e2e/test_scheduler_live.py`, is a known flake (failed once, passed four times after).
- **`pytest -q | tail` returns TAIL's exit code and buffers everything until completion.** Redirect
  to a file when you need a traceback. This cost two 18-minute runs.
- **`git merge` does not accept `-F -`** (unlike `git commit`). Write the message to a file.
- **`git add -A` / `git add .` are BANNED.** Stage by name; `git status --short` first. Use
  `git commit -F -` with a **quoted** heredoc — zsh eats backticks inside `-m "…"` and commit
  bodies are not repairable (the code sensor ingests them at commit time).
- ⚑ **oq-0041's "(c)" and oq-0057's "(c)" mean OPPOSITE things** — park the core plane vs. split the
  decrypt path. oq-0041's ratification question is still OPEN.
- **finding-0227: bp-113/bp-114 are under-priced.** Each needs a `ReadOnlyRows` signature refactor
  as a *precondition* neither estimate includes. **bp-111 is the safe next ops build.**
- **A lettered amendment to a ratified note is agent-impossible** (finding-0233): `scope-guard`
  denies ratified notes at `_lib.py:435-441` and returns *before* the write-scope check.

## STATE — regenerate, do not trust this snapshot

`git log --oneline -1` · `uv run scripts/board.py --queue-count` · plan statuses from front-matter.
At write time: **5 deskchecks owed, 0 records ever written**; ~25 owner questions open; ops wave
bp-111…bp-119 `ready` but serial and colliding on `ops/lifecycle/launcher.py`.

## ⚑⚑ READ THIS BEFORE DESIGNING ANY RETRIEVAL — the query language EXISTS and is RATIFIED

`core-query-protocol.md` (470L) · `capability-scope-algebra.md` (187L) · `chat-sensor.md` (204L) —
all **ratified ⇒ agent-immutable**. `dialogue-ingest-and-recursion.md` (153L) is `draft`.
**I nearly had a Fable agent re-derive all of it.** Every agent is a scoped client of ONE shared
typed query language; a query is **a question plus constraints**, scopes are enforced by the types,
and it is **LAZY — an under-constrained query does not resolve rather than returning a partial set**.
Bounding is the mechanism; once bounded it reduces to pattern matching. ⚑ *That laziness is a
structural defense against authority-laundering: a query cannot emit an incomplete answer that looks
complete.* Owner's canonical shapes: *"did this sequence occur"* · *"build a chain between these two
points"* (= the succession path) · *"find where the handoff-write fired"* (= clause-(e) forensics).

⚑ **CORRECTED — do not repeat my error.** An earlier revision of this brief said the reference
substrate has **no `corpus_to_corpus` edges**. **That is FALSE.** It was true in the 2026-07-13
capsule I quoted; **bp-026 built them since** — **644,785 corpus↔corpus edges exist.** The real gap
is **typing**: `ops/code_sensor.py:131-139` collapses `warrant`/`supersedes`/`links`/`depends_on`
into a single `note-citation`, so **zero typed rows** exist. Succession is not missing its edges —
it is missing their **kinds**. ⇒ I cited a two-week-old capsule instead of the code. Don't.

## CAPTURED — the transcript-only backlog is CLEARED, and an audit followed

Four brainstorms, written this session, **committed by the sub-orchestrator at `55c2f79`**:

- `kms-threat-layering.md` — the reasoning behind oq-0057 (the KMS decrypt-path ruling; its "(c)"
  is the *opposite* of oq-0041's). The three-layer threat model is a **partition, not a stack**.
- `email-architecture-aws-external-local-internal.md` — non-negotiable #1 *forces* the edge hop
  (core cannot address a cloud agent at all); #11 genuinely does not cover cloud-*formed* corpus.
- `owner-intent-audit.md` — **8 LOST owner intents**, 2 contradicted, 4 partial, 1 promised-not-done.
- `commit-economy-and-the-succession-path.md` — **RULED, do not act on it yet.** R1: plans/notes
  commit at **status transitions only**, brainstorms batch. R2: **decouple the code sensor first**
  (read artifacts + edit events, not commit bodies) — **R2 gates R1 behind a build**, so commit
  practice changes NOTHING until a sensor design note is written, ratified, and graduated. ⚑ Do not
  read the ruling and start committing less tomorrow. Next artifact: that design note.
- `context-load-as-a-feedback-loop.md` — +8 lines, one additive correction (audit item L-4).

⚑ **The audit's methodology finding outranks its contents: the owner types on THREE channels.**
Filtering `type=="user"` with string content — the obvious sweep — sees only ~**60%** of his words.
The rest are `queue-operation` rows (typed *mid-turn*; **86 unseen**) and `AskUserQuestion` results.
**Half the LOST items arrived on the queue channel** — structurally, that is the channel he uses
when the house is burning. Any future sweep that ignores it will miss the same half.

## ⚑⚑ SEVERE — unfiled, and it is a live data defect, not a workflow gripe

**`data/chatlog.sqlite` holds 39 hook-feedback rows attributed to `speaker='owner'`.** The corpus
believes the owner said things the Stop hook said. That is **authority laundering already in
production data** — criterion 4 of the destructive-loop signature — and it corrupts any query that
trusts speaker attribution, including the succession path. Measured by `dn-trace-retrieval`'s census
(gap **G1**: channel closure + a `speaker='system'` kind; amends ratified `dn-chat-sensor` CS-3, so
**the owner sets it**). ⚑ The same census failed on **queue-operation and system rows being
structurally invisible** — the ~40% blind spot, found independently by two agents tonight.

## OWED — needs writes to tracked files; deliberately NOT yet made

3 findings (L-5 `design` · L-6+L-7 merged `discovery` · clause-(e) misattribution `spec-fidelity`),
1 owner-question (L-2), 3 mechanical inbox fixes (record oq-0054 as answered; flip oq-0035, ruled at
`941785d` but still `open`; add a `status:` field to oq-0036/0037).

**L-1 is RULED and off this list** — see the commit-economy capsule above.
⚑ **L-2 is unanswered and structural:** *"are we getting rid of graduate → YOU BLESS → build?"*
⚑ **L-5 is being obeyed from an agent's working memory only:** the sub-orchestrator-owns-the-merge
rule amends the delegate contract and is recorded nowhere.

**Sweep gap, declared:** 07-20→07-24 had no queue-channel pass; sub-agent and worktree transcripts
are entirely unswept.

## RULES LIVE ELSEWHERE

Commit discipline, gate legs, delegation, blessing ceremony → `.claude/skills/`. Domain
non-negotiables → `CLAUDE.md`, `CONSTITUTION.md`. They load at the moment of use, which is why they
hold, and why prose copies here rot.

## THIS FILE IS SCHEDULED FOR DELETION

bp-126 removes it. Until then it is the handoff: rewrite it at the unit boundary, **after** the
final commit, and keep it short. Anything machine-knowable belongs in the STATE block and should be
regenerated, never typed. Its own history is the argument — it reached 568 lines, fired the stale
gate 19 times in one session, and contradicted itself four times while being edited to remove
staleness. Baseline and what to re-measure: `docs/brainstorms/context-load-as-a-feedback-loop.md`.

⚑ **Live input to bp-126 — now MEASURED, not anecdotal** (`docs/design-notes/trace-retrieval.md`
§Part 1). Clause (e) fired **108× raw / 99 fork-deduped** over 2026-07-19→27 across 16 sessions;
peak day 07-26 = **36**; **302 resume-brief file ops**, 4 cascades, 11 tool errors, 4 documented
self-contradictions during forced rewrites, and **10 firings with an owner message already queued**.
All 5 firings *this* session were on the **sub-orchestrator's** commits — it keys on
**commits-in-session, not authorship**. ⇒ Whatever replaces it should key on who authored the
commit, or exempt paths an active plan holds. Honest limit: the gate fires at *turn end*, so it
never truncated an answer; no thread died of (e) alone. It cost turns and context, not sentences.
