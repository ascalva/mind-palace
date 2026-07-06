# The Agent Workflow — Operator's Reference (Mind Palace)

*Internal reference for the brainstorm → design → build → reflection machinery in
this repo. A lookup document — not a tutorial, not the portable write-up. It
describes the system **as built**, warts included, so future-you stops
re-deriving it.*

*Authoritative spec: `docs/design-notes/agent-workflow.md` (ratified; amendments
A1–A6 in §16). When this doc and the note disagree, the note wins — flag it and
reconcile.*

*State at time of writing: **all six self-found defects closed.** A1–A6 are all in
effect; bp-004 landed the last two (A5 status-normalization, A6 schema
reconciliation). Every blessing gate is now enforced against Edit, Write, and
Bash. Verified against the committed files on disk: `.claude/hooks/_lib.py`,
`CLAUDE.md`, the `checkpoint` and `finding` skills, and `docs/PROGRESS.md`. Still
from the working record (worth a spot-check if you lean on a specific detail): the
bash hook wrappers, `settings.json`, the command files, and the `graduate` /
`build-plan` / `book` skills.*

---

## 0. What this is and why it exists

The workflow moves an idea from a chat brainstorm, through a ratified design note,
into session-scoped build plans that a builder agent (Claude Code, Opus, max
effort) executes, with findings routed back for reflection. It exists because
agents produce plausible work fast, so the bottleneck is **trust**: did the agent
stay in scope, did it build to spec, can I follow how a decision was reached, can
a fresh session resume where a dead one stopped. The workflow answers each
mechanically rather than by hoping the prompt held.

Governing idea, inherited from the store's doctrine and applied one level up to
the *building* of the system: **everything an agent touches is a typed file with a
state machine, and the human/machine boundary is enforced by hooks, not by
instructions.** State lives in greppable front-matter; nothing of consequence
lives only in a chat transcript or a session's context window.

The most useful mental model is the **three-beat rhythm**. Every cycle is a
sequence of exactly three kinds of act:

1. **You bless** (manual, by hand, main worktree) — ratify a design note, approve
   a plan's readiness, seal code. No agent may do these.
2. **The machine builds** (isolated, in a worktree, via `mp-new`) — the builder
   implements a `ready` plan, journals, files findings.
3. **You review and merge** (manual) — read the diff, commit on the branch,
   `mp-finish` → `mp-push` → `mp-cleanup`.

Once that rhythm is muscle memory, the *content* of a plan is where attention
goes; the shape is automatic.

---

## 1. The artifact chain and its state machines

Every stage is a typed file with front-matter (`type, id, status, created,
updated, links`) and a state machine. State is greppable so orchestrator sweeps
are `grep`-cheap.

| Artifact | Location | States | Terminal |
|---|---|---|---|
| Brainstorm note | `docs/brainstorms/<topic>.md` | living (append-only) | — |
| Design note | `docs/design-notes/<slug>.md` | draft → ratified → superseded | superseded |
| Build plan | `docs/build-plans/<id>/plan.md` | proposed → ready → in-progress → complete \| parked \| superseded | complete, superseded |
| Journal | `docs/build-plans/<id>/journal.md` | alive → sealed | sealed |
| Finding | `docs/findings/<id>.md` | open → routed → resolved \| promoted | resolved, promoted |
| Owner questions | `docs/inbox/owner-questions.md` | living (entries: open → answered → swept) | — |
| Book | `docs/book/` (LaTeX) | living; edition-tagged syncs | — |

Transitions that carry weight:

- **Design-note ratification** (draft → ratified): owner-only, by hand, in a text
  editor *outside* any agent session (see §3 — design notes are denylisted, so an
  agent's Edit is refused and a Bash flip is caught). `/graduate` refuses drafts.
- **Plan readiness** (proposed → ready): owner-only, by hand. The split-approval
  gate. `/build` refuses a non-`ready` plan. With A4 you approve *item-by-item*
  before flipping.
- **Plan supersession** is three-place: (P, P′, warrant), warrant = a `spec-defect`
  finding. A defect never edits a plan in place; graduation mints P′ citing the
  finding, P flips to `superseded`. Same relation as claim supersession — the
  discredited plan stays inspectable, and P′ grounds on the warrant, not on P.
- **Parked** requires a `re_entry` field (front-matter key — greppable, A6). No
  plan or criterion without one may enter `parked`.
- **Finding promotion**: a `discovery`/`spec-defect` finding that changes design
  mints a design-note amendment citing the finding as warrant, then flips to
  `promoted`.

---

## 2. Repository layout

```
CLAUDE.md                      # constitution, ~1 page, auto-loaded every session
.claude/
  settings.json                # hook registrations, shared
  settings.local.json          # per-machine permission cache — GITIGNORED (A3/finding-0004)
  hooks/                       # 6 thin bash wrappers + _lib.py (the shared decision engine)
  commands/                    # capture, graduate, build, resume, triage, scribe
  skills/                      # graduate, build-plan, finding, checkpoint, book
  agents/                      # builder, scribe (subagent variants for small delegations)
  state/                       # GITIGNORED — active-plan pointer, session-baseline (worktree-local)
docs/
  brainstorms/
  design-notes/                # the ratified record — authoritative for design; DENYLISTED
  build-plans/<id>/plan.md, journal.md, acceptance/run.sh
  findings/
  inbox/owner-questions.md
  templates/                   # build-plan.md (A4 form), design-note.md, finding.md, capsule.md
  book/                        # LaTeX design manual
  PROGRESS.md                  # orchestrator's single-writer completion log
bin/mp-env.sh                  # the mp-* session lifecycle tooling (sourced, not on PATH)
```

The domain kernel — `CONSTITUTION.md`, `BUILD-SPEC.md`, `CONVENTIONS.md` — is the
mind-palace fixed point, referenced by CLAUDE.md and never edited by the workflow.

---

## 3. The enforcement layer — six hooks

Hooks are registered in `.claude/settings.json` as **thin bash wrappers** whose job
is mode detection (hook-stdin vs `--standalone`), the fail-loud trap, and journal
markers. The **decisions** all live in `.claude/hooks/_lib.py`, where a real
front-matter parser and a correct glob matcher are cheap. Design choice worth
knowing: `_lib.py` uses **system `python3` with no third-party deps**, so the
enforcement layer never depends on the project `.venv` — a broken venv can't
silently disable the gates.

| Hook | Event | What it does |
|---|---|---|
| `scope-guard` | PreToolUse: Edit\|Write\|MultiEdit | Reads the active plan's `write_scope`; denies an out-of-scope `file_path` with a reason. The foundation denylist sits beneath any plan, every session, orchestrator included. |
| `gate-guard` | PreToolUse: Edit\|Write\|MultiEdit | Denies any Edit that performs a blessing transition (`→ ratified` on a design note, `proposed → ready` on a plan) in every session and role. Idempotent re-saves and non-blessing transitions pass. |
| `session-brief` | SessionStart | Emits world-state (plans by status, unswept-findings count, open owner questions, this worktree's active plan, book-debt note). Records HEAD into `state/session-baseline`. This is what makes bare `claude` land oriented. |
| `journal-gate` | Stop | Blocks session end on any of three checks — see §4. |
| `staleness-nudge` | UserPromptSubmit | If the journal is stale vs HEAD, injects a one-line reminder. Advisory. |
| `compaction-marker` | PreCompact | Appends a marker line to the journal so the post-compaction turn re-verifies against the journal, not the summary. |

### The foundation denylist

Absolute — never writable by any session, orchestrator included, beneath any plan.
As committed in `_lib.py`:

```
CONSTITUTION.md
docs/design-notes/**
eval/golden/**
eval/golden.py
```

Note `docs/design-notes/**` is here in full: **no agent session can write a design
note at all**, which is why ratification happens by hand in an editor. (`eval/golden.py`
— the golden-set *scoring code* — sits alongside the golden *data* as a fixed point;
its presence is a deliberate tightening. If you ever wonder why, that's the reason.)
Blessing *transitions* on plans (which are not denylisted) are the separate concern
`gate-guard` handles.

*Drift to know about: the `CLAUDE.md` denylist digest lists only the first three
(it omits `eval/golden.py`). The committed `_lib.py` above is authoritative for
enforcement; the constitution's digest trails by one entry. Reconcile on the next
amendment. (See §7.5 — this is the kind of inconsistency the auditability property
is meant to surface, so it's flagged, not smoothed.)*

### The decision protocol (how a wrapper reads `_lib.py`)

Every `_lib.py` subcommand prints exactly **one decision line** and exits **0 on a
clean decision**:

```
ALLOW                     # permit
DENY: <reason>            # scope-guard / gate-guard: block the write   (wrapper exits 2)
BLOCK: <reason>           # journal-gate: block session close           (wrapper exits 2)
```

An *internal* error (the machinery itself broke) **raises**, producing a non-zero
exit, which the wrapper distinguishes from a clean deny and treats as
**fail-loud, fail-open**: it emits `HOOK-FAILURE <name>: … enforcement NOT applied`
to the transcript and appends a journal marker. So: `exit 0 + ALLOW` = permit;
`exit 0 + DENY/BLOCK` = block-with-reason; `exit ≠ 0` = machinery broke, loud, not
enforced.

Every subcommand is dual-mode — a standalone form taking file args, and a `-hook`
form reading stdin JSON: `scope-check`/`scope-check-hook`,
`gate-check`/`gate-check-hook`, plus `stop-audit`, `brief`, `staleness`, `marker`.
"Rerun the hook" is therefore literal — invoke the standalone form and reconcile.
(Repo root resolves via `CLAUDE_PROJECT_DIR`, else `git rev-parse --show-toplevel`,
else cwd.)

### Two-layer write enforcement

The pre-hoc guards (`scope-guard`, `gate-guard`) cover Edit/Write only — a builder
can write through Bash, which they can't see. The `journal-gate` Stop audit is the
**untracked-inclusive backstop** that catches Bash-mediated writes at close.
Pre-hoc porous, post-hoc tight.

### The three blessing gates — the bright line

Three owner-only transitions, now enforced against **both** Edit/Write and Bash,
are the security spine: **ratify a design note**, **approve a plan
(proposed → ready)**, and **seal the core** (the integrity ceremony,
`core-integrity.md` — hardware-key gated, strongest of the three). No command
performs them; no agent may. They bound the feasible set of everything downstream,
which is why they live in the hook layer as hard constraints. Getting all three
enforced against every write path took the full A1–A6 chain (§6).

---

## 4. `journal-gate` — the three checks, precisely

The most-hardened hook. On Stop it blocks (with reason) if any of:

- **(a) journal freshness** — journal mtime predates the last commit
  (`git log -1 --format=%ct`); also fires if the journal is missing for the active
  plan. Forces the journal to reflect the latest work. *Wart: mtime is fragile — a
  git operation can touch it. Not yet bitten; parked.*
- **(b) scope audit** — the session's uncommitted delta, computed
  **untracked-inclusive** via `git status --porcelain --no-renames -uall`, filtered
  against `write_scope` (plus the plan, its journal, `docs/findings/**`), contains
  any out-of-scope path; denylist hits are reported separately. Untracked-inclusive
  is required because a Bash-written file is untracked and invisible to the pre-hoc
  guard. **Sound only under worktree isolation** (§5): there, every uncommitted path
  is the session's own. (A1, A3; warrant finding-0003.)
- **(c) blessing audit** — two composed detectors covering both ways a blessing can
  sneak in through Bash:
  - *tracked flip* — `_blessing_in_diff` scans `git diff HEAD -- docs/design-notes
    docs/build-plans` for an added `status:` line at a blessed value. Against **HEAD**
    (not the session baseline) so a *committed* blessing self-clears — it's
    accountable to its commit author — while an *uncommitted* flip still shows. (A1.)
  - *from-nothing mint* — `_untracked_blessing` reads `git ls-files --others
    --exclude-standard` under the blessing surfaces and checks each untracked file's
    on-disk status; a fresh untracked file already at `ready`/`ratified` is a
    blessing from nothing. Scans only *untracked* files, so it can't fire on a
    committed blessing — A1's self-clear is preserved. (A3; warrant finding-0005.)

  The union is total: a flip of an existing artifact → tracked detector; a
  Bash-minted file at a blessed status → untracked detector. `--exclude-standard`
  honors `.gitignore`, so an ambient ignored path (`settings.local.json`) never
  enters the audit (finding-0004).

**Status normalization (A5, warrant finding-0006).** All three blessing detectors
compare the status value by exact string equality. `_normalize_status` strips a
trailing YAML comment (cut at the first `" #"` — space-hash — then rstrip) from the
*status value only*, at three extraction sites: `status_of`, `_status_in_text`, and
`_blessing_in_diff` (the third routes through neither named extractor — easy to
miss, and the reason the fix pins three sites, not two). Without this,
`status: ready   # x` parses to `ready   # x != "ready"` and silently escapes every
gate. `ready#x` (no space) is deliberately **not** stripped, so normalization can
only ever *refuse* to recognize a malformed blessing, never fabricate one.
Crucially, `_scalar` and `parse_front_matter` are untouched — a `#` in a
`design_ref` or `links` entry survives; only the status path is normalized.

*Two things to hold onto about (b)/(c):* they cannot distinguish a builder's Bash
escape from an owner's parallel untracked file — both are uncommitted untracked
out-of-scope paths — which is *why* worktree isolation is a soundness invariant.
And during **bootstrap** (a plan that must run in the main worktree), parallel owner
activity *will* trip these; that's expected fail-loud behavior, reconciled by
committing, not a defect.

---

## 5. Worktree isolation — the soundness invariant

Builder sessions run in **dedicated git worktrees**, one per plan. Hard invariant,
not a nicety: the scope and blessing audits are only sound when every uncommitted
change in the tree is the session's own. In a shared tree the audits can't
attribute a change — false positives at best, ambiguity about a real escape at
worst. The `active-plan` pointer and `session-baseline` are worktree-local
(`.claude/state/`), so concurrent sessions never collide.

`mp-env.sh` encodes it. A plan named `foo` gets branch `claude-foo`, worktree
`~/mp-foo` (repo sibling), tmux session `mp-foo`.

**The one exception is bootstrap** — a plan that builds the workflow itself runs in
the main worktree because the tooling/branch may not exist yet. bp-000 and the
early fixes ran there and met the reconcile-on-commit dance. Every plan after runs
isolated and never does.

*Learned the hard way, on the record: don't hand-edit or `git checkout` tracked
machinery in the main worktree to "fix" branch work. The branch is truth until you
merge. Editing `docs/templates/build-plan.md` directly in main is exactly the class
of change that's supposed to go through `mp-new`.*

---

## 6. The amendment history — why the machinery is shaped as it is

The workflow found and closed six defects **in itself**, each surfaced by running
it. This is the best evidence the enforcement is real, and a useful index of the
sharp edges. All are ratified amendments to `agent-workflow.md §16`; **all six are
now landed.**

| # | Warrant | What it fixed |
|---|---|---|
| A1 | finding-0003 | `journal-gate` (c) diffs against HEAD, not the session baseline → a committed blessing self-clears (killed the re-anchor loop). |
| A2 | finding-0001 | Safety non-negotiables stay **inline** in the auto-loaded constitution, exempt from the thinness rule (an out-of-context guardrail is not a guardrail). |
| A3 | finding-0005, -0004 | `journal-gate` (c) made untracked-inclusive → a plan Bash-minted straight at `ready` is caught (closed the last unenforced blessing path); settings cache gitignored. |
| A4 | finding-0007 | Build-plan template upgraded to **investigate → reconcile → plan**: per-item acceptance *and* named falsifier, `path:line`-cited investigation, banner-vs-cross-reference reconciliation, math field-guide clauses, N/A-marking. Graduation becomes a grounded planning pass that implements nothing. |
| A5 | finding-0006 | Status-value normalization → a comment-bearing status line no longer defeats all three gates. (Landed via bp-004.) |
| A6 | finding-0008 | §3 schema reconciled to the A4 template — moved fields are body sections, `re_entry` stays a greppable front-matter key; command files corrected to match. (Landed via bp-004.) |

The pattern worth internalizing: each defect was found by the system auditing its
own construction (a verification pass, a scaffolding run, a grounded graduation),
and each was a *general* enforcement gap, not a domain quirk. A4's grounded
graduation proved itself on its first use by catching an error in the *build
prompt* — the normalization-site count (two sites named, three needed) — before it
shipped.

---

## 7. Roles and write discipline

**CLAUDE.md** — persona-neutral constitution (~1 page): artifact chain, routing
rule, note obligation, never-block-on-owner, pointer to commands, plus the domain
non-negotiables digest **inline** (A2). Depth lives in skills, loaded on
invocation.

**Orchestrator** — the default posture of a bare `claude` at the main root. Runs
`/graduate`, spawns/resumes builders, runs `/triage`, maintains
`owner-questions.md`, writes PROGRESS.md, flips plan status on completion.
Single-writer set: `PROGRESS.md`, `owner-questions.md`, plan status fields,
`docs/findings/` triage annotations. (With no active plan, `scope-guard` allows
everything except the denylist — that's how the orchestrator writes these.)

**Builder** — the contract layered by `/build <id>` or `/resume <id>` in an
isolated worktree. Writable surfaces are exactly three: the plan's `write_scope`,
its own `journal.md`, new files in `docs/findings/`. (Findings are always writable
regardless of `write_scope`.) Everything else is denied.

**Scribe** — the contract selected by a plan's `contract: scribe`. Maintains
`docs/book/` (LaTeX), grounding every claim in an artifact id or code `path@ref`,
filing a finding when writing exposes a gap. Same enforcement as builder — no new
hook needed, `scope-guard` covers it.

**Routing rule:** findings typed `design | math | direction` → orchestrator (who
batches to `owner-questions.md` if owner input is needed); `codebase | spec-fidelity`
→ builder resolves and annotates. **Never block on owner:** a builder facing an
owner-level question parks that criterion with a re-entry condition and continues;
only a `blocker` ends a session early.

---

## 7.5 Agent obligations and the auditable log

§7 describes what each role *may write*. This section describes what each role is
*obligated to do* — the note-taking and logging duties that keep the record
auditable — and the standing steering that imposes them. Grounded in the actual
`CLAUDE.md` and the `checkpoint` / `finding` skills, not the spec's summary of
them.

### The steering that creates the obligations (CLAUDE.md, verbatim intent)

`CLAUDE.md` is auto-loaded every session and states four binding rules that turn
permissions into duties:

- **Note-taking obligation.** "Checkpoint the journal at every semantic boundary
  (criterion closed, commit made, finding filed). The bar is the fresh-agent test:
  a new session with only plan + journal + write-scope files must continue without
  re-asking. Resume beats compaction." This is an *obligation*, not a permission —
  the Stop gate enforces it (a stale journal blocks close).
- **Never block on the owner.** An owner-level question parks its criterion with a
  re-entry condition and the session proceeds with the rest; only a `blocker` ends
  a session early, and even then the Stop gate demands a fresh journal.
- **Blessing gates are owner-only, by hand.** `draft→ratified` and
  `proposed→ready` are never done in a session; enforced pre-hoc and post-hoc.
- **Write discipline is a capability, not a suggestion.** "A denial means narrow
  the scope or file a finding — never route around." The prohibition on
  routing-around is itself an obligation: the correct response to a gate is to
  surface, not to circumvent.

### Note-taking and logging duties, per role

- **Builder — the journal.** Writes `journal.md` at every semantic boundary, in
  the seven-section shape the `checkpoint` skill fixes: (1) status line, (2)
  completed (with commit refs), (3) in-flight, (4) single concrete next action, (5)
  open questions (typed + routed), (6) context-manifest delta, (7) a `## Markers`
  section at the file end where hooks append. The obligation isn't "take notes" —
  it's "leave the journal in a state that passes the fresh-agent test at every
  stop," which is why the skill says to enrich Next-action and In-flight *before*
  stopping if a fresh agent would have to ask. The journal is **committed** —
  history, not scratch.
- **Builder / any session — findings.** Files a `finding` for anything that exits
  its lane: a `spec-defect` (the design record is wrong/contradictory), a
  `discovery` (building revealed something bearing on design), a `question`, or a
  `blocker`. The `finding` skill fixes the duty: type it correctly (type
  determines routing), **always** attach a re-entry condition when it parks a
  criterion (a parked item without one is disallowed), and resolve-in-lane what the
  code and spec can settle rather than escalating. Findings are the *only*
  asynchronous channel between sessions and the *only* path from build back to
  design — so an unfiled finding is lost signal, which is why filing is an
  obligation, not an option.
- **Orchestrator — the completion log and question inbox.** Single writer of
  `PROGRESS.md` (the auditable completion log), `owner-questions.md` (the batched
  question inbox), plan-status transitions, and triage annotations. Its logging
  duty is the checkpoint: on sealing a plan it writes a `PROGRESS.md` entry in the
  Built / Verified / Next / Decisions shape, tracing the full chain — what landed,
  the commit refs, the harness result, and every finding's disposition with its
  warrant. This is what makes "what got built, when, why, and with what
  verification" reconstructible from the log alone.
- **Scribe — grounded citation.** Every claim it writes into the book cites an
  artifact id or code `path@ref`; when writing exposes a gap, it files a finding
  rather than papering over it. Its note-taking duty *is* a provenance duty — no
  assertion without a citation to the ratified record or the code.

### Why the log is auditable — the property, stated plainly

The record is auditable because every state transition is:

- **Attributable** — every artifact is a committed file with an author; every
  blessing is a commit accountable to its committer (which is *why* `journal-gate`
  (c) diffs against HEAD — a committed blessing is already accountable).
- **Append-only in spirit** — nothing of consequence is rewritten in place. A
  wrong claim, plan, or design is *superseded* (three-place: P, P′, warrant), not
  edited away; the discredited version stays inspectable. Journals are committed
  and sealed, not overwritten.
- **Warrant-linked** — every promotion into the design record cites the finding
  that caused it. You can't change design by side effect; you change it through a
  finding→amendment→ratification trace.

Together these mean the **full causal history of any decision is reconstructible
from the artifacts alone** — no reliance on chat transcripts or memory. The
amendment chain A1–A6 is the worked proof: each of the six fixes can be walked
end to end — the finding that surfaced it, the warrant link, the design-note
amendment, the build plan that landed it, the commit, the harness that verified
it — entirely through committed files. A system that can reconstruct why every one
of its own six self-corrections happened, from the record, is auditable in the
strong sense.

*One honest drift to note (the kind an audit catches): the denylist digest in
`CLAUDE.md` lists three entries (`CONSTITUTION.md`, `docs/design-notes/**`,
`eval/golden/**`) while the committed `_lib.py` enforces four (adds
`eval/golden.py`). The code is authoritative for enforcement; the constitution's
digest is a hair behind. Worth a one-line reconciliation on the next amendment
pass — flagged here rather than smoothed over, since a hidden inconsistency is
exactly what this section is about surfacing.*

## 8. The journal and resume — why context is disposable

`journal.md` is alive while a plan is in-progress, sealed by `/triage` on
completion, committed (history, not scratch). Written at every semantic boundary —
criterion closed, commit made, finding filed — newest entry first: status line,
completed (with commit refs), in-flight, single concrete next action, open
questions (typed + routed), context-manifest delta, hook markers.

The **fresh-agent test** is the acceptance bar: a new session given only plan +
journal + write-scope files must continue without asking anything already
answered. When that holds, **resume strictly dominates compaction** — the journal
is an audited, committed artifact; a compaction summary is lossy and unreviewable.
Norm: kill sessions freely between criteria and `/resume` fresh; compaction is the
mid-criterion fallback only. This is the actual deliverable of the note-taking
obligation — it makes context disposable.

---

## 9. Commands and skills

| Command | Action |
|---|---|
| `/capture <topic>` | Append a pasted session capsule (or raw paste) to `docs/brainstorms/<topic>.md`. |
| `/graduate <note>` | Refuses non-`ratified`. Runs the **grounded planning pass** (A4): reads code, answers open questions with `path:line`, proposes reconciliation, emits a `proposed` plan — implements nothing. |
| `/build <plan-id>` | Refuses non-`ready`. Sets the worktree active-plan pointer, flips to `in-progress`, loads the contract + context manifest, begins. |
| `/resume <plan-id>` | Loads plan + journal + manifest delta into a fresh session under the plan's contract. Must pass the fresh-agent test. |
| `/triage` | Sweeps findings (route, batch owner questions, propose promotions as warranted amendments), seals completed journals, writes PROGRESS checkpoints, sweeps answered owner questions. The reflection loop, made mechanical. |
| `/scribe` | Computes book debt (ratified/superseded notes + promoted findings newer than `SYNC.md`) and mints a `contract: scribe` sync plan. Execution flows through `/build`. |

Skills (load on invocation, carry the depth CLAUDE.md omits): **graduate**
(decomposition + the investigate/reconcile/plan discipline), **build-plan**
(template semantics — interfaces pinned inline, per-item acceptance + falsifier,
math field-guide, N/A discipline), **finding** (typing/routing), **checkpoint**
(journal contract, semantic-boundary triggers, fresh-agent test), **book** (chapter
map, TikZ/notation conventions, citation-to-artifact scheme, sync semantics).

---

## 10. The build-plan template (A4) — the load-bearing artifact

`docs/templates/build-plan.md`. Every section required; inapplicable ones marked
`N/A — <reason>`, never omitted (the explicit N/A is itself an accountability act).
The 13 sections: **§0** mode/provenance, **§1** objective (one sentence), **§2**
context manifest (ordered read list), **§3** investigation & grounding
(`path:line`-cited; N/A on greenfield), **§4** reconciliation (banner-on-correction
/ cross-ref-on-extension; N/A if nothing corrected), **§5** write scope (+ explicit
out-of-scope), **§6** interfaces pinned inline (signatures/schemas copied in, never
referenced), **§7** items (each: acceptance test, **named falsifier**, invariants,
`touches_stored_data`, parallelizable + depends-on), **§8** math field-guide
(measures / valid-when / fails-its-keep-if; N/A if no math), **§9** non-goals,
**§10** stop-and-raise, **§11** parked decisions (default + rejected alternatives +
re-entry), **§12** dependency & ordering summary (blast-radius phase order).

Front-matter keys (A6): `type, id, status, design_ref, contract, write_scope,
session_budget, depends_on, parallelizable_with, created, updated, links,
re_entry` (greppable, for the parked gate), `supersedes/superseded_by/warrant`.
`objective`/`context_manifest`/`non_goals`/`stop_conditions` are **body sections**,
not keys.

The distinction that matters most: **acceptance vs falsifier.** Acceptance says "it
works"; the falsifier names the observable that would prove the approach *wrong*.
The harness must never pass vacuously — every blocking check pairs with a control
that must also fire (proving the path is wired), and Item falsifiers name
vacuous-pass as a failure mode.

---

## 11. The session lifecycle — `mp-env.sh`

Sourced into the shell (not a PATH executable) because several commands change
shell state (`mp-cd`) or own your tmux session (`mp-new`). Loaded once per terminal
via the `mp` bootstrap function in `~/.zshrc`.

```
mp                        # load the tooling (once per terminal)
mp-new <label>            # worktree + branch + tmux + caffeinate claude (or reattach)
mp-orch                   # orchestrator session in the main root
mp-attach <label>         # reattach to a session
mp-cd <label>             # cd this shell into a worktree
mp-ls                     # list worktrees + mp- tmux sessions
mp-review <label>         # preview commits + diffstat a branch would merge (read-only)
mp-finish <label>         # review, confirm, --no-ff merge to main (no push)
mp-push                   # push main to remote (deliberate, separate)
mp-cleanup <label>        # remove worktree + branch + kill tmux (after merge)
mp-help                   # the command list
```

`caffeinate -is` wraps `claude` so the Mac stays awake exactly as long as the
session runs. `mp-finish` shows the diff and asks y/n; `mp-push` is separate;
`mp-cleanup` refuses to delete an unmerged branch without override — reviewed-act
posture, not fire-and-forget. `mp-new` cuts from your **local** `MP_BASE` (default
`main`) — `git -C "$MP_ROOT" pull` first if you ever build across two machines.

*Two zsh gotchas baked in, because they cost real time:* `path` is a reserved
variable tied to `PATH` — a `local path=…` silently destroys command lookup, so the
tooling uses `wt`. And label validation is a POSIX `=~` regex
(`^[A-Za-z0-9][A-Za-z0-9_-]*$`), not a glob, because a dash inside a `[...]` glob
class forms a range.

---

## 12. The canonical cycle, end to end

With the beat each step is:

1. **Brainstorm** (chat, this interface, project context). End with a **session
   capsule** — decisions, parked items + re-entry, open questions, next steps — in
   a fenced block.
2. **`/capture`** it to the brainstorm note. When an idea finalizes, draft the
   design note in chat against the template.
3. **Bless: ratify** the design note by hand (draft → ratified) in an editor.
   Commit it.
4. **`/graduate`** it — the grounded planning pass emits a `proposed` plan.
5. **Review item-by-item; bless: approve** (proposed → ready) by hand.
6. **`mp-new <label>`; `/build`** — the machine builds in isolation, journaling at
   every boundary, filing findings.
7. **Review and merge** — read the diff (especially anything touching enforcement
   or scoping), commit on the branch, `mp-review` → `mp-finish` → `mp-push` →
   `mp-cleanup`.
8. **`mp-orch`; `/triage`** — route findings, write the PROGRESS checkpoint, seal
   the journal, sweep answered questions.

Repeat. Every cycle is that shape; only the plan contents change.

*The recurring review reflex: for a machinery change, the file to read closely is
whatever touches enforcement (`_lib.py`, the hooks) or scoping — and always run the
plan's own `acceptance/run.sh` yourself rather than trusting the builder's summary
table, watching specifically that the non-vacuous controls fire.*

---

## 13. Known warts and boundaries (as-built, on the record)

Honesty about the sharp edges, because a hidden failure mode is worse than a named
one. Verified against the committed `_lib.py`:

- **Hooks fail open on script error.** The decision protocol distinguishes clean
  deny (exit 0) from machinery-broke (exit ≠ 0 → fail-loud), and the traps make a
  break conspicuous — but a hook that's silently *wrong* (returns ALLOW when it
  shouldn't, without erroring) still enforces nothing. Keep the scripts trivial; the
  loud-failure path is the net, not a guarantee.
- **Worktree isolation is assumed, not verified.** Nothing checks that a builder is
  in a dedicated worktree; the invariant holds by discipline (`mp-new`) and by the
  audits false-positiving loudly in a shared tree. Bootstrap deliberately violates
  it.
- **`cmd_brief` renders status un-normalized** — the session brief reads status via
  `read_front_matter(...).get("status")` directly, *not* through `status_of`, so it
  would render a comment-bearing status verbatim. This is the diagnostic that first
  surfaced finding-0006, left cosmetic by choice (bp-004 §11 parked decision); the
  template fix removed the only source of comment-bearing status lines for new plans.
  Re-entry: a real session renders one for a plan whose status legitimately carries a
  comment (none exists today).
- **The `re_entry` "parked ⇒ re-entry" gate is discipline, not a hook.** §3 (of the
  design note) declares it; nothing enforces it mechanically. `re_entry` is kept a
  front-matter key (A6) precisely so a future hook *can* enforce it with a cheap
  grep.
- **Pre-hoc Bash write-denial is parked** — the Stop-gate audit is the only Bash
  backstop. Re-entry: a real escape observed slipping the post-hoc catch.
- **`active_plan_path()` returns a constructed path even when it doesn't exist** (the
  final ternary yields the same value on both branches) — harmless (downstream reads
  just yield empty), but a no-op to be aware of if you ever debug a stale pointer.
- **This is defense-in-depth, not a proof.** The blessing gates and core seal raise
  the bar and make tampering loud; whoever holds the signing token or rewrites the
  verifier defeats the integrity layer. The bright line is the network seal and the
  architecture; this machinery makes the *building* of it accountable.

---

## 14. Pointers

- **Authoritative spec:** `docs/design-notes/agent-workflow.md` (ratified; A1–A6 in
  §16). This reference summarizes it — the note governs.
- **Core integrity / sealing:** `docs/design-notes/core-integrity.md`.
- **Security composition the gates instantiate:** `docs/research/security-planes.md`.
- **Supersession (reused for plans and design-note promotion):**
  `docs/design-notes/supersession-lifecycle.md`.
- **Completion log:** `docs/PROGRESS.md`.
- **The findings that shaped the machinery:** `docs/findings/finding-000{1,3,4,5,6,7,8}.md`
  (0002 resolved in-plan; 0006 book-scaffolding is a separate 0006 — check the id).

*Maintenance note: this is a snapshot, verified against `_lib.py` at the close of
bp-004. It drifts when the workflow changes (a new amendment, a new command, a
skill edit). Treat `agent-workflow.md` as truth and refresh this deliberately —
ideally a `/scribe`-adjacent pass once the tool has matured with use, which is also
when the portable write-up (the one this doc is deliberately **not**) becomes worth
doing. A good verification step for the next refresh: have an orchestrator session
diff this doc against the real `.claude/` and `docs/` state and file a finding for
any drift — the kind of audit the system exists to do.*
