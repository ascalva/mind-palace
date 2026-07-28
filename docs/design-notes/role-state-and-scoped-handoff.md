---
type: design-note
id: dn-role-state-and-scoped-handoff
track: workflow
status: ratified            # draft → ratified → superseded.  draft→ratified is an OWNER-ONLY hand edit.
created: 2026-07-26
updated: 2026-07-27
links:
  - docs/brainstorms/role-state-and-scoped-handoff.md   # the commissioning capture (2026-07-26)
  - docs/findings/finding-0175.md                       # the warrant — displaced eleven times
  - docs/design-notes/session-handoff-gate.md           # clause (e) — partially superseded here (§1.1)
  - docs/design-notes/agent-workflow.md                 # §6/§9/§16 — amended by enumeration (A10)
  - docs/design-notes/track-board-and-deskcheck-gate.md # the track coordinate this note reuses (D1)
  - .claude/skills/checkpoint/SKILL.md                  # the journal contract, generalized to seats
  - .claude/skills/context-economy/SKILL.md             # the resume-brief discipline being retired
  - scripts/board.py                                    # the DERIVED-view generator being extended
  - scripts/docket.py                                   # the cannot-drift falsifier's origin
  - scheduler/queue.py                                  # the durable role state that already works
  - .claude/hooks/_lib.py                               # cmd_stop_audit — clauses (a)…(f)
supersedes: null         # proposes partial supersession of dn-session-handoff-gate §2.2–2.3; owner sets on ratification (§1.1)
superseded_by: null
warrant: docs/findings/finding-0175.md
---

# Role state and scoped handoff — the seat outlives the occupant

> Filed by the chat agent as `draft` (chat-side protocol, §8). Ratification is a
> hand edit by the owner — no command performs it, and `gate-guard` denies any
> agent attempt (§10). `/graduate` refuses this note until `status: ratified`.

**Owner's mandate (2026-07-26, verbatim, from the commissioning capture):** *"I meant the ROLE's
state, orchestrators come and go, but the state stays and is managed by every succeeding agent,
assuming the role."* And, authorizing this work: *"commence the design/build/audit for fixing the
resume handoff bug, and not just fix it, rewrite it entirely, make it robust, and states can be
scoped to a specific queue/topic/role, that is how handoffs can be performed efficiently, and you
could even use the scheduler's queue."* `[GROUNDED docs/brainstorms/role-state-and-scoped-handoff.md:9-17]`

The agent is a disposable **occupant** of a persistent **seat**. What survives a session is the
seat's state, and every successor inherits it. This note types that state, scopes it, decides its
substrate and versioning, re-specifies the Stop-gate clause that has fired against the current
format eleven times in one session, and makes the fresh-agent test executable.

## 1. Purpose and scope

This note decides: (D1) the scope taxonomy of handoff state and the identity of a scope; (D2) how
singleton and plural roles are encoded; (D3) the content split of the state itself — corrected
from the capture's three categories to four; (D4) the storage substrate, ruling on the owner's
scheduler-queue suggestion; (D5) versioning; (D6) retention and compaction; (D7) the concrete
artifact set and generator contract; (D8) the re-specified Stop-gate clause; and (§2.11) the
executable falsifier. It is the design pass finding-0175 has been owed since 2026-07-25.

### 1.1 What this note amends, and how

- **`dn-agent-workflow` (ratified, agent-immutable A8).** Amended by enumeration, never by edit:
  on ratification this note contributes amendment **A10** to `agent-workflow.md` §16 (§6's clause
  enumeration gains (e′); §9's journal contract gains the seat-journal generalization). The
  amendment text lands via a build plan after ratification, per the A1–A9 precedent
  `[GROUNDED docs/design-notes/agent-workflow.md:276 §16; the A9 entry is the direct precedent]`.
- **`dn-session-handoff-gate` (ratified).** Its §1 purpose (enforce a fresh handoff on Stop) and
  §2.4 scope key (orchestrator posture = no active plan) **survive unchanged**. Its §2.2 block
  condition and §2.3 freshness signal (mtime of a gitignored brief vs. last-commit time) are
  **superseded by §2.10 of this note** once the replacement is built. Until that build merges,
  clause (e) as built remains binding — supersession is keyed to the build landing, not to
  ratification, so there is never a gap with no handoff gate. The owner records the partial
  supersession by hand (front-matter `superseded_by` on the gate note is deliberately NOT set:
  the note is not wholly replaced; the amendment log carries the partial supersession instead).
  `[INFERENCE]` — partial supersession by amendment-log entry rather than front-matter flip is
  inferred from the A9 precedent (a note-sized change carried as a lettered amendment); no
  existing artifact prescribes the partial case. If the owner prefers whole-note supersession,
  §2.10 here is self-contained enough to receive it.
- **`finding-0175`** is this note's warrant and closes (→ `promoted`) when this note is ratified.
- **The checkpoint and context-economy skills** are consequential surfaces (§3), not amended here.

### 1.2 Non-goals (load-bearing — the owner reads this section aloud at ratification)

- **NOT a redesign of `docs/PROGRESS.md`, `docs/inbox/owner-questions.md`, or the owner queue.**
  They keep their lifecycles and single-writer rules. The capture's open question — "does this
  subsume the brief, PROGRESS.md, and the owner queue as three renderings of one scoped store?" —
  is answered *no for now*: only the resume brief is replaced (§2.9). PROGRESS-as-rendering is
  parked with a re-entry condition (Parked decisions). `[INFERENCE]` — separability inferred:
  PROGRESS.md has its own measured debt (the 12-plan backlog) and its own consumers; coupling its
  redesign here would fail the one-honest-read ratification bar (the M2/K1 lesson, finding-0148).
- **NOT a change to the per-plan journal contract.** Builders' handoff artifact stays
  `docs/build-plans/<id>/journal.md` under the checkpoint skill, clauses (a)/(f) unchanged. This
  note *generalizes* that contract to seats; it does not touch the plan instance of it.
  `[GROUNDED]` — the capture assigns plural-role state to the plan, "which is exactly why the
  journal is per-plan" (`docs/brainstorms/role-state-and-scoped-handoff.md:31-38`).
- **NOT a message bus, role inbox, or delivery mechanism.** Addressing (`orchestrator@`,
  `bp-110@`) is settled by the capture only as *identity*; delivery (email lane, ambassador,
  Syncthing return path) belongs to the email/ambassador notes and is not designed here.
- **NOT a schema change to `data/queue.sqlite`.** No session rows, no new columns, no second
  writer. §2.6 licenses read-only *reads* of the queue file and nothing else.
  `[GROUNDED scheduler/queue.py:17-18]` — the queue is single-writer by design; a second writer
  class would breach the stated concurrency model.
- **NOT autonomous deletion or rewriting of history.** Compaction is supersession-with-retention
  (§2.8); the keep-and-link ruling binds (finding-0164, finding-0168).
- **NOT a relocation of the standing rules' content.** §2.5 rules that durable rules do not live
  in handoff state; each actual move (a rule into its skill/hook) is its own reviewed change with
  its own diff. This note moves the *category*, not the individual rules.
- **NOT machine-judged narrative quality.** The gate guarantees existence, freshness, and (for
  one lintable class) purity — never that the prose is good. The fresh-agent drill (§2.11) is
  where quality is caught, and its behavioral half is judged, not asserted. This carries forward
  `dn-session-handoff-gate` §2.6's "existence, not quality" stance unchanged.
- **NOT multi-machine or offline-device sync semantics.** `[INFERENCE]` — git-tracked artifacts
  are portable by pull; anything beyond that (phone, Syncthing) is the exhaust lane's concern.
- **NOT new corpus-ingestion machinery.** Versioning the artifacts (§2.7) makes them visible to
  the existing repo ingest; nothing ingestion-specific is built here. `[INFERENCE]` from
  finding-0175 §"The direction" — ingestion was a listed want; tracking satisfies it for free.

## 2. Principles / decision

### 2.1 The reframe, sharpened — the defect is uneven coverage, not a missing concept

The capture states the load-bearing idea as **"role state is untyped."** `[GROUNDED
docs/brainstorms/role-state-and-scoped-handoff.md:19-29]` Verified against the tree, that
sentence is close but not exact, and the correction changes what should be built:

The system already types per-scope state **twice, well**:

- **The plan scope** is fully typed: `plan.md` (front-matter state machine) + `journal.md` (the
  checkpoint contract, committed, sealed, follow-through-gated by clause (f))
  `[GROUNDED .claude/skills/checkpoint/SKILL.md:1-88; .claude/hooks/_lib.py:929-937]`.
- **The scheduler seat** is typed to tier 2: a SQLite schema with a guarded transition system,
  leases, checkpoint tokens, additive-only migrations over 300k+ lifetime rows
  `[GROUNDED scheduler/queue.py:1-14,100-146]`. The scheduler is the existing proof that "the
  seat outlives the occupant" works: every restart is a succession, and the successor reads the
  queue.

Exactly **one seat** — the orchestrator — and **one scope kind** — the cross-cutting topic —
never got the treatment. The orchestrator's state is split across a hand-written, gitignored,
destructively-overwritten blob (`.claude/state/resume-brief.md`) and a hand-maintained tracked
ledger (`docs/PROGRESS.md`) with no stated rule about what belongs where `[GROUNDED
docs/findings/finding-0175.md:20-27,47-59]`. Topics have membership (`track:` front matter) and a
board, but no handoff view.

**Consequence for the design [DERIVED]:** the fix is to *extend the two proven mechanisms* — the
journal contract to the orchestrator seat, the derived-view generator to the handoff — not to
mint a new universal "scoped state store." A new store would re-implement what the artifact chain
already owns (the DRY defect class, CONVENTIONS §Language & style) and would itself need the
typing/versioning/gating this note would still have to specify. The capture's own three-place
observation (orchestrator/scheduler/plan each already persist seat state) points the same way.

### 2.2 The census of the artifact under redesign — the evidence

Read whole on 2026-07-26 (405 lines as read; size is a session-instantaneous reading, not a
property — the finding-0175 triage correction). Classified line-by-line by whether a generator,
a recorded measurement, judgement, or a rule-book could have produced each line `[DERIVED]`:

| class | ≈ lines | ≈ share | examples (line refs into the 2026-07-26 reading) |
|---|---|---|---|
| tree-derivable (incl. restated findings/oqs) | ~135 | ~33% | hash lists (:10-13), statuses + wave graph (:237-250), finding/oq digests (:122-165, :278-310), deskcheck counts (:391-398) |
| execution-derived readings | ~30 | ~7% | the gate's true reading (:86-113), the full-suite run (:114-121), `/usage` figures (:377-379) |
| judgement / transcript-only | ~180 | ~44% | uncaptured owner exchanges (:15-59), the lettering trap (:79-84), audit watch-items (:210-235), queue ordering (:322-341) |
| durable rules | ~45 | ~11% | standing rules (:359-382), tooling traps (:108-113), the self-rewrite instruction (:400-405) |
| headers/blank | ~15 | ~4% | — |

Two sharper sub-facts the aggregate hides:

1. **Within the judgement class, roughly half restates tracked artifacts with a one-sentence
   gloss** (finding-0226/0227 summaries, oq-0051's ruling, the deferral list). The genuinely
   non-derivable content — the part no generator can write — is on the order of **80–100 lines of
   405**: the uncaptured exchanges, the traps noticed, the ordering judgement. That quarter is
   the narrative half's honest size.
2. **The brief's own machine-derivable facts have measurably rotted while sitting in prose.**
   The brief asserts clause (e) keys on `os.path.getmtime` at `_lib.py:762` (:318-319). In the
   tree, `:762` is clause **(a)**'s journal check; clause (e)'s trigger is `_lib.py:899-920`
   (getmtime at `:911`) `[GROUNDED .claude/hooks/_lib.py:762,899-920]`. A hand-copied line
   number drifted — inside the very paragraph documenting the staleness defect. This is the
   defect exhibiting itself, and it is the class of fact D3 evicts from narrative entirely.

The capture's firing counts — clause (e) fired eleven times in session-54, session-52 rewrote
five times, session-53 four `[GROUNDED docs/brainstorms/role-state-and-scoped-handoff.md:41-44]`
— are **testimony from the capture, not mechanically re-verifiable** (transcripts are not in the
tree). Stated as such; the design does not depend on the exact count, only on the mechanism,
which *is* verifiable (§2.10).

### 2.3 D1 — the scope taxonomy: a scope is an existing artifact, kind ∈ {role, plan, track}

**A scope is a pair `(kind, id)` where the id must resolve to an artifact already on disk.**
Scope identity is never a free string:

| kind | id resolves to | state artifact | exists today? |
|---|---|---|---|
| `role` | a seat in the closed registry (§2.4) | `docs/roles/<role>/journal.md` + derived handoff (§2.9) | new (this note) |
| `plan` | `docs/build-plans/<id>/plan.md` | the existing per-plan journal | yes — unchanged |
| `track` | `docs/tracks/<slug>.md` manifest | derived aggregation over members (§2.9); no standing narrative | membership yes; view new |

- **`topic:` is not a fourth kind — it is the existing `track` coordinate.** The hard case the
  capture names (the KMS work spans oq-0041, oq-0057, finding-0232, and a future note — exactly
  what a per-plan journal handles badly) is precisely the cross-cutting-membership problem the
  track system was built for: artifacts declare `track:` in front matter, `board.py` aggregates,
  and the F-WF1 orphan check enforces coordinate integrity `[GROUNDED scripts/board.py:158-198,
  343-356]`. Reusing it means the KMS work gets a `docs/tracks/<slug>.md` manifest (e.g.
  `secrets-custody`) instead of a new key vocabulary. What extends: **findings and owner
  questions gain an optional `track:` front-matter key** (plans and design notes already carry
  one), so a track-scoped handoff can aggregate all four artifact types. Additive, and the
  existing orphan check covers the new members for free.
- **`queue:` is not a scope kind.** The scheduler's queue is one seat's *own* state (the
  `scheduler` role's, §2.4), not a coordinate other state is scoped by. Treating "queue" as a
  scope key would conflate a transport with an identity — the same correction the capture's
  email thread already made for builders (a reply routes to the artifact, never the worker).
- **Composition.** Scopes compose by membership, not nesting: an artifact may belong to a plan
  (its home) and a track (its `track:` key) simultaneously; a track view is a *derived join* over
  member artifacts, never a second copy of their state. Role scopes do not contain plan scopes —
  the orchestrator's journal records orchestration judgement (what to spawn, what to watch), and
  the plan's journal records the plan's own ground truth. A fact wanted in two scopes lives in
  the lower one (plan) and is *rendered* into the higher one (track/role) by the generator.
  Single-home, multi-render — the anti-drift rule, and DRY applied to state.
- `track:` remains single-valued per artifact (the board convention). Multi-track membership is
  parked (Parked decisions).

### 2.4 D2 — singleton vs plural: encoded by enumeration, not emergent

**The taxonomy encodes it; it does not fall out.** Role scopes exist only for seats in a closed
registry, declared in `agent-workflow.md` §5 on amendment (initially exactly two):

- `orchestrator` — one seat; single-writer of PROGRESS.md, the inbox, plan statuses
  `[GROUNDED CLAUDE.md:42-45]`. Gets the new seat journal + handoff rendering (§2.9).
- `scheduler` — one seat; its state is *already* `data/queue.sqlite` + the runs ledger, typed
  and durable `[GROUNDED scheduler/queue.py:15-34]`. Gets **no new narrative artifact** — the
  daemon does not write prose; its seat state stays where it is, and the handoff generator
  *reads* it (§2.6).

Builders are plural and concurrent: there is no "the builder," so a builder role-scope has no
well-defined referent, and none is minted. A builder's state belongs to its **plan** — the
already-correct arrangement `[GROUNDED docs/brainstorms/role-state-and-scoped-handoff.md:31-38]`.

Why enumeration rather than derivation: singleton-ness *could* be inferred from single-writer
file ownership, but that inference is convention (a doc sentence), not structure. A closed enum
checked by the same coordinate rule as D1 (a `docs/roles/<role>/` directory whose name is not in
the registry is an orphan — the F-WF1 pattern) is tier-4 enforceable. Honest tier statement: the
registry itself is prose in a ratified note, tier 5 until the orphan check lands (tier 4).

### 2.5 D3 — the split is four ways, not three: DERIVED · MEASURED · NARRATIVE · RULES

The capture proposes DERIVED / NARRATIVE / RULES `[GROUNDED
docs/brainstorms/role-state-and-scoped-handoff.md:55-69]`. **The census falsifies the three-way
split: ~30 lines of the live brief fit none of the three.** The gate's suite reading (~17 min of
wall clock to reproduce), the `/usage` figures (an external call), the daemon's up/down state —
these are mechanical facts a *tree-scan generator cannot produce* and hand-written prose
demonstrably rots ("the gate had ONE expected failure" was exactly such a reading, rotted in
place `[GROUNDED docs/brainstorms/role-state-and-scoped-handoff.md:45-47]`). Forcing them into
DERIVED makes the generator run the suite at every close (fails the cheap-idempotent requirement
of §2.10); leaving them in NARRATIVE re-creates the defect this note exists to fix. They are a
fourth category:

| class | definition | freshness semantics | where it lives (§2.9) |
|---|---|---|---|
| **DERIVED** | pure function of the artifact tree | regenerate; staleness is impossible by construction (the docket falsifier) | the handoff rendering |
| **MEASURED** | result of running something (suite, `/usage`, daemon probe) | a timestamped reading; **age displayed, never hidden** — stale is a fact, not a defect | the readings log |
| **NARRATIVE** | judgement no generator can write | append-only; freshness = "an entry exists for this session" (§2.10) | the seat journal |
| **RULES** | durable discipline | not handoff state at all — a rule loads at the moment of use (skill/hook) or it does not hold | skills, hooks, templates |

- The RULES eviction is already proven in this repo: the `git add -A` / `-F -` rules held once
  moved into the commit skill and failed repeatedly while they lived in the brief `[GROUNDED
  docs/brainstorms/role-state-and-scoped-handoff.md:62-65]`.
- The NARRATIVE purity rule: **narrative refers to artifacts by stable id (`bp-110`,
  `finding-0227`, `oq-0051`) and never states a machine-derivable value** — no commit hashes, no
  plan statuses, no counts, no `path:line` into volatile code. The derivable value lives in the
  DERIVED pane; the id is the join key. Enforcement is honest tier 4 for the lintable class
  (hex strings of length ≥ 7 word-bounded; `status:` transition phrasing) and review-grade for
  the rest — stated plainly rather than overclaimed (§2.10 residuals).
- MEASURED entries are `(timestamp, command, one-line result)` rows, append-only. The DERIVED
  pane renders the latest reading per command **with its age** — "suite: 2 failed / 2276 passed
  (18h ago)" — so a stale reading advertises itself instead of impersonating a current fact.

### 2.6 D4 — the substrate: the registry as source, files as its export (revised 2026-07-27; originally "files as source")

> **Revision notice (2026-07-27, post-ratification — the warrant is lapsed).** Edited under
> `dn-typed-workflow-registry` §2.10's protocol: the edit lapses this note's warrant, the PR
> is the resubmission, the owner's merge is the re-auth. Owner instruction, verbatim:
> *"amend this note: role-state-and-scoped-handoff, it was written at a time when we didn't
> expect the hook migration would somehow make it all worse, needs to be amended, files are
> no longer the source of truth, and an agent's write scopes could be forced by role, scope
> still plays a part."*
>
> **D4's ruling sentence, as amended: the registry is the source of truth for state,
> identity, relations, transitions, and ordering; files are its EXPORT — authoritative
> prose, derived frontmatter** (`dn-typed-workflow-registry` §2.3). The queue half of D4 is
> unchanged and was never in question: a read-only input to the DERIVED pane, never a
> substrate. D4's error was one word — it concluded "files are the *source*" from premises
> that only establish "files must remain readable, and authoritative where the registry is
> absent." That weaker claim is the one this revision preserves, ground by ground below.

**Ruling (original, queue half unchanged): the scheduler's queue does not become the handoff substrate.** The owner's suggestion
("you could even use the scheduler's queue") is honored where it is right — and it is right
about the *pattern*, not the *storage*:

The queue genuinely has what handoff wants: durability, ordering, claim/lease semantics, a
tested state machine over 302,010 real rows `[GROUNDED scheduler/queue.py:100-146,388-443]`. But
it fails the one constraint the capture itself names as hard `[GROUNDED
docs/brainstorms/role-state-and-scoped-handoff.md:71-81]`: **the handoff must be readable with
no running system.** Four independent failures, each sufficient:

1. **Fresh worktrees have no queue.** Worktree builders branch from `origin/main`;
   `data/` is not in the tree, so `data/queue.sqlite` simply does not exist in the checkout
   where a delegated resume happens. (The daemon being down is survivable for SQLite — the file
   is readable without a server — but the file not being *present* is not.) `[DERIVED]` from
   the worktree spawn model (push-before-spawning rule; `data/**` gitignored).
2. **Single-writer would be breached.** One supervisor owns the queue by design
   `[GROUNDED scheduler/queue.py:17-18]`. Sessions writing handoff rows adds a second writer
   class from a different process family — the exact contention the design excludes.
3. **The artifact chain requires typed *files*.** "No decision lives only in a transcript" —
   and no state should live only in a blob git cannot diff, review, or ingest. A SQLite row is
   invisible to the corpus, to `git log`, and to the owner's `nvim`.
4. **The fresh-agent test reads files.** Its inputs are "plan + journal + write-scope files"
   `[GROUNDED .claude/skills/checkpoint/SKILL.md:70-79]`; a substrate the test cannot read
   cannot be the substrate.

**How the registry answers the four grounds (2026-07-27 revision — three of the four are
requirements it must satisfy, not objections it overturns; the first it *inherits*):**

| D4 ground | still binding? | how the registry answers it |
|---|---|---|
| 1. fresh worktrees have no queue | **YES — binds the registry too** | store is machine-level, outside the repo; registry-less checkouts read the export, fail closed on writes |
| 2. single-writer would be breached | satisfied | the registry is single-writer by construction — the property that makes serial minting work |
| 3. the artifact chain requires typed files | **YES — stronger than D4 stated** | the export, pinned + CI-ratcheted; published files make a hash resolvable — load-bearing for auth |
| 4. the fresh-agent test reads files | **YES** | it still reads files — the exported ones; the drill must pass in a checkout with no registry present (F8 there) |

**Write scope, as the owner's instruction says, "still plays a part" — but the part changed
twice the same night (registry note §2.6 is the single home for the mechanics, per the DRY
rule; what belongs *here* is the role fact):** credential capability is **role-forced at
dispatch** — the registry constructs each worker (Claude SDK) with the credentials its role
warrants, which for every builder-shaped role is *none* (no AWS key, no merge ability, no
signing material); the agent is never forbidden them, it is never given them. File writes,
by the later ruling, are **not** role-fenced at all: the foundation denylist (including
`.github/workflows/**`) is checked by an external-principal Action on the PR, and
everything else is review judgement against the plan's declared intent. The role ceiling as
an *allowlist over paths* — the shape this note's era assumed — is retired with the rest of
act-based scope enforcement; what the role still fixes is **who is acting and with what
capability**, which is exactly this note's subject. `[GROUNDED — both rulings verbatim at
docs/brainstorms/the-typed-workflow-registry.md:260-305 and :959-1025.]`

**What the queue contributes instead:**

- **As a read-only input to the DERIVED pane.** When `data/queue.sqlite` is present, the
  generator reads it (queue depth, RUNNING rows, lease status — the `read_queue_stats` shape)
  and renders it; when absent (worktree, fresh clone), the pane renders `queue: unavailable in
  this checkout` and everything else still works. Graceful degradation is the availability
  requirement, satisfied.
- **As the pattern.** The queue's discipline — append-only migrations, states as data,
  supersession over deletion, "a property of the row, not of someone remembering to sweep"
  `[GROUNDED scheduler/queue.py:221-232]` — is exactly the discipline §2.5–§2.8 impose on the
  file substrate. The reuse is of the *design*, at zero coupling.
- `[ANALOGY]` Seat occupancy mirrors `claim()`/lease: a session "claims" the orchestrator seat
  at start and its Stop-gate close is the lease end. This analogy is deliberately NOT built —
  no seat-lock file, no occupancy ledger — because concurrent orchestrator sessions are a
  human-procedure error today, not a mechanical race the system must survive. Parked.

### 2.7 D5 — versioning: the seat is versioned; the sitting is not

The split the capture calls "unstated rather than decided" is decided:

**Versioned (git-tracked):** everything that belongs to the *seat* and survives the occupant —
the seat journal (NARRATIVE), the readings log (MEASURED), the handoff rendering (DERIVED, with
its GENERATED banner, the TRACKS.md precedent: derived AND versioned are independent axes and
this artifact is deliberately both `[GROUNDED docs/findings/finding-0175.md:30-34]`). Tracking
buys: history ("what did we believe at 02:00" becomes answerable), lag measurability
(finding-0175's owner ask — claim-at-T1 vs falsified-at-T2 needs surviving timestamps), corpus
ingestion via the existing repo ingest (Ouroboros eats this tail), and portability to any
checkout.

**Unversioned (`.claude/state/`, per-worktree, gitignored):** everything that identifies the
*sitting* — `active-plan`, `session-baseline`, the `docket.md` landing buffer. These are
occupancy pointers: regenerable, worktree-local, meaningless to a successor
`[GROUNDED .claude/state/.gitignore (main checkout): "Regenerable, per-worktree, never shared"]`.

`resume-brief.md` — seat state living on the sitting side of the line — is the anomaly this rule
retires (§2.9). One consequence stated for honesty: seat journals commit at semantic boundaries,
which adds commits to `main`; the code sensor ingests them (CONVENTIONS §Commits), which is a
feature (the session layer becomes visible to the palace) and a cost (ledger noise) the owner
accepts or rejects at ratification.

### 2.8 D6 — retention: append-only, compaction by supersession capsule

Seat journals and readings logs are **append-only** in the finding-0164/0168 sense: keep and
link, never delete and replace.

- **Compaction trigger:** at a `/triage` sweep, when the active segment (entries after the last
  compaction capsule) exceeds a working threshold — default **~300 lines**, a number chosen to
  keep the resume read under one screen-minute; it is a knob, not an invariant. `[INFERENCE]` —
  no artifact prescribes a threshold; the default is sized from the census (the genuinely
  narrative quarter of the old brief).
- **Mechanism:** a **compaction capsule** — one entry that carries forward every still-live
  judgement (open watch-items, standing traps, in-flight intent) and names the range it
  supersedes. Prior entries are retained beneath it, marked superseded — the slot-lineage
  discipline applied to prose (finding-0168 addendum 1 pattern).
- **Authority rule (the capture's open question, answered):** after compaction, the
  authoritative narrative is **the latest capsule plus all entries after it**. Everything before
  the capsule is history — readable, ingestable, lag-measurable, and *non-binding*: a fresh
  agent reads capsule + suffix and may stop there. Git history additionally makes even physical
  truncation recoverable, but keep-and-link is the ruled discipline and file-visible history is
  what the corpus and the lag metric consume.
- The DERIVED rendering never compacts — it is regenerated, bounded by what is currently owed.
  The MEASURED log compacts by the same capsule rule (latest reading per command carries
  forward).

### 2.9 D7 — the artifact set and the generator contract

**New, for the orchestrator seat (the only new machinery):**

```
docs/roles/orchestrator/journal.md    NARRATIVE  append-only seat journal — the checkpoint
                                                 contract (§9) generalized: same entry shape,
                                                 same semantic-boundary triggers, compaction
                                                 capsules per §2.8. Committed.
docs/roles/orchestrator/readings.md   MEASURED   append-only (timestamp, command, result) log.
                                                 Committed.
docs/roles/orchestrator/handoff.md    DERIVED    generated rendering, GENERATED banner, committed.
                                                 Never hand-edited.
```

**The generator** extends the `board.py` machinery (same `_lib` front-matter reuse, same
deterministic-render discipline `[GROUNDED scripts/board.py:26-33]`); whether it lands as a
`board.py` subcommand or a sibling `scripts/handoff.py` sharing its scan functions is a
graduation-time call — the contract is what this note pins:

- **Inputs:** the artifact tree (plan/note/finding/oq front matter + statuses), the readings log,
  and — when present — a read-only open of `data/queue.sqlite` (§2.6).
- **Output:** a deterministic rendering per scope. `--role orchestrator` writes the standing
  `handoff.md` (session tier recommendation is *rendered from* the context-economy rubric's
  inputs where derivable, hand-set in narrative where not); `--track <slug>` and `--plan <id>`
  render **on demand to stdout** — no standing files for track/plan scopes (a plan's standing
  artifact is its journal; a track's is its manifest), so there is no fleet of generated files
  to go unregenerated.
- **The idempotence pin (load-bearing for §2.10):** the rendering is a pure function of the
  artifact tree *excluding itself*, and embeds **no HEAD sha and no generation timestamp**
  (readings carry their own timestamps as data). Therefore regenerate-then-commit converges in
  one step: after the regen commit, regeneration is byte-identical. A rendering that embedded
  HEAD or `now()` would have no fixed point and would re-arm any freshness gate forever — the
  current brief's circularity, mechanized. This pin is *why* hashes leave the handoff: **a
  tracked artifact never needs to cite its own tree's commits — `git log` is already the derived
  view of commits.** The old brief cited hashes only because it lived outside git.
- **What retires:** `.claude/state/resume-brief.md` (both halves replaced), its template
  `docs/templates/resume-brief.md` (superseded by a seat-journal entry template + the generator),
  and the self-rewrite instruction (replaced by §2.10's mechanics). `session-brief.sh`'s
  auto-surface (`:46-48`) re-points from the brief to `handoff.md` + the journal's
  authoritative segment. `docs/PROGRESS.md` is untouched (§1.2).

### 2.10 D8 — clause (e′): the gate re-specified, and the by-construction claim verified

**Current clause (e)** `[GROUNDED .claude/hooks/_lib.py:892-920]`: in orchestrator posture, if
HEAD moved past `session-baseline`, block unless `mtime(resume-brief.md) ≥ last-commit-time`;
the block text instructs "citing the final commit hashes" (`:917-918`). The circularity, stated
precisely after verification: **the mtime check alone is satisfiable by writing last, but every
post-brief commit re-arms it, and the instructed content (final hashes) makes the rewrite a
hand-authored act each time** — so any late commit (a seal, a board regen, a capture) forces a
manual brief rewrite. That is the eleven-firings mechanism. The capture's phrasing ("the format
demands a fact it cannot yet contain") is accurate about the *content demand*, slightly stronger
than the *check* — the check is mtime-only; the note records both halves honestly.

**Clause (e′)**, replacing (e) when built — orchestrator posture, commits landed this session:

1. **DERIVED freshness = idempotence, not mtime.** Block unless regenerating the handoff
   rendering is a **no-op** (byte-identical to the committed file). The block reason instructs:
   run the generator with `--write`, commit, close again. Because of the §2.9 idempotence pin,
   that recovery converges in exactly one step — the regen commit does not re-arm the check.
   This also upgrades the signal from a launderable mtime (tier 5) to a content compare
   (tier 4).
2. **NARRATIVE freshness = an entry for this session.** Block unless the seat journal's mtime ≥
   the SessionStart baseline write (`session-brief.sh:65`). Keyed to *session start*, not to
   *last commit* — deliberately: the narrative contains no commit-derived facts (purity rule),
   so an entry written mid-session before a final seal commit is still a truthful entry, and a
   late commit cannot re-arm this check. The circularity is cut **by the gate re-spec**, not by
   trusting narrative purity.
3. **MEASURED: not gated.** A reading is taken when the work warrants it; the pane shows age.
   Gating "freshness" of a 17-minute suite reading at every close would either block honest
   closes or train `touch`-laundering — the cry-wolf disqualifier.

**The prize, verified rather than assumed.** The capture claims clause (e) becomes satisfiable
*by construction*. Verdict: **true for the derived half, with two named residuals.**
(i) Derived: regeneration is deterministic, cheap (a tree scan — no suite run, per D3's MEASURED
split, which is what *makes* this feasible), and idempotent, so check 1 is always dischargeable
by one mechanical command whose output is correct by definition — the docket cannot-drift
falsifier, now standing guard on the handoff itself. (ii) Narrative: check 2 references no
post-entry facts, so it cannot re-arm — satisfiable by one honest act at any boundary.
**Residual R1 (accepted porosity):** a session may commit *after* its last narrative entry and
close; the final commits are mechanically visible (git log + pane) but the judgement about them
may be missing. Same "existence, not quality" stance as the ratified gate note, carried forward
knowingly. **Residual R2:** narrative purity is tier 4 only for the lintable class (hash-shaped
strings; status-transition phrasing); an agent can still write "bp-113 is bigger than priced" —
which is fine, that is judgement — or smuggle a count — which is rot, and only review or the
§2.11 drill catches it. If R2's lint proves too weak in practice, that is a finding against this
note, not a silent widening.

**mtime laundering** (a Bash `touch` defeating check 2) remains possible — the identical
porosity clauses (a) and (e) accept today; pre-hoc porous, post-hoc tight targets forgetting,
not adversarial evasion `[GROUNDED docs/design-notes/session-handoff-gate.md:108-113]`.

### 2.11 The executable falsifier — the fresh-agent drill

The bar exists as prose `[GROUNDED .claude/skills/checkpoint/SKILL.md:70-75]`. Made executable,
in two layers — mechanical always, behavioral on cadence:

**F1 — mechanical (cheap, every run of the drill and available to CI):**
- **F1a cannot-drift:** generator `--check` regenerates to a temp path and byte-compares with
  the committed rendering; mismatch = FAIL (this is also clause (e′) check 1).
- **F1b purity lint:** zero word-bounded `[0-9a-f]{7,40}` tokens and zero `status:`-transition
  phrases in the seat journal's authoritative segment (capsule + suffix); hit = FAIL. Scoped to
  entries post-migration; legacy text is not back-filled (the readmap precedent).
- **F1c availability:** in a **fresh worktree of `origin/main` with no daemon running**, the
  generator must exit 0, rendering `queue: unavailable` rather than erroring, and the committed
  journal + rendering must be present (tracked ⇒ present in every checkout). This is the §2.6
  hard constraint as a test, run in the environment that motivated it.

**F2 — behavioral (the actual fresh-agent test):**
- **Spawn:** a cheap-tier agent (grind row of the context-economy table) in a fresh worktree
  from `origin/main`, no daemon, **no conversation history**.
- **Inputs, exactly:** the scope bundle — for `role:orchestrator`: `handoff.md` + the journal's
  authoritative segment; for `plan:<id>`: `plan.md` + its journal (the classic test, now also
  drilled); for `track:<slug>`: the on-demand track rendering. Nothing else; tools disabled or
  read-only.
- **Probe protocol:** the agent must output (1) the unit currently in flight, (2) the single
  concrete next action, (3) every blocking unknown as a literal `BLOCKED: <question>` line.
- **Observable pass/fail:** (1) and (2) must match the generator's own structured answer (the
  generator emits the expected fields as JSON alongside the rendering — a string/field compare,
  fully mechanical). **FAIL** on: any mismatch; OR any `BLOCKED:` line whose answer a judge
  locates *inside the bundle* (the "re-asks something already answered" clause — the one
  genuinely subjective check, run as a model-judge A/B against the last passing baseline per
  CONVENTIONS §Testing, never scored cold). A `BLOCKED:` line whose answer is genuinely absent
  is a **pass with a defect report** — the drill found under-specified state, which is its job.
- **Cadence:** every `/triage`, and mandatorily in any build plan that touches the handoff
  machinery. Result recorded as a MEASURED reading (the drill is itself execution-derived).
- **Why this is a falsifier and not an eyeball:** a broken handoff is invisible until a real
  session fails `[GROUNDED docs/brainstorms/role-state-and-scoped-handoff.md:88-89]`; F2 makes
  the failure happen on schedule, in a worktree, at grind-tier cost, where it is a red line
  instead of a lost session.

### 2.12 V-series — not settled by reading (each blocks the item that cites it)

- **V1:** Does the F2 JSON-answer compare survive contact with real renderings, or does "the
  single next action" resist canonical form? If it resists, F2 degrades to judge-only — weaker,
  and the plan that builds the drill must say so. (Blocks §2.11 acceptance criteria.)
- **V2:** Is the ~300-line compaction threshold right? No evidence exists either way; the first
  three compactions are the measurement. (Blocks nothing; tunes §2.8.)
- **V3:** Does rendering the queue pane from a read-only SQLite open ever contend with the live
  supervisor's WAL? Expected no (WAL readers don't block the writer), but "expected" is not a
  test. (Blocks the generator's queue-input item.)
- **V4:** The orchestrator seat journal doubles as the place session-54-style perishable capture
  lists live. Whether that content belongs in the journal or should immediately become
  brainstorm files (standing capture authority) is a working-practice question the first weeks
  of use answer. (Blocks nothing; §2.3's single-home rule already forbids duplication.)

## 3. Consequences

- **Licenses (post-ratification, via `/graduate`):** [DERIVED] a natural two-plan split —
  **(P1)** the substrate: `docs/roles/` artifacts, the generator extension + idempotence pin,
  the one-time migration of the current brief (derived facts dropped — regenerable; genuinely
  narrative content into the seat journal's first entry; rules dispatched to their skills as
  enumerated diffs; readings seeded), `session-brief.sh` re-point; **(P2)** the gate + drill:
  clause (e′) in `_lib.py` + integration tests (the bp-074 pattern), F1a–c, the F2 harness.
  P2 depends on P1; neither runs while another builder holds `.claude/hooks/**`.
- **Amendment A10 to `dn-agent-workflow`** (§1.1): §6 enumeration (e)→(e′); §9 journal contract
  states the seat generalization; §5 gains the role registry.
- **Partial supersession of `dn-session-handoff-gate`** §2.2–2.3, effective when P2 merges
  (§1.1).
- **Skill updates (docs-tier):** checkpoint — seat-journal instance of the contract;
  context-economy — resume-brief section replaced by the handoff-pair mechanics; the
  resume-brief template retires.
- **finding-0175 → promoted;** its append-only/lag-measurement direction lands here (§2.7,
  §2.8).
- **The session layer becomes corpus-visible:** tracked seat state is ingested by the existing
  repo ingest — the highest-density record the system produces stops being invisible to it.
- **Cost shift, stated:** session closes gain one mechanical regen+commit; they lose the
  hand-rewrite of a ~400-line brief. The 405-line every-session read is replaced by a bounded
  rendering + a bounded narrative segment (capsule + suffix) — the context-economy win is the
  point, not a side effect.

## 4. Wiring & enablement

**How it wires:** the generator extension (`scripts/board.py` machinery, §2.9) with `--role
--track --plan --write --check`; the `docs/roles/orchestrator/` artifact trio; the
`session-brief.sh:46-48` re-point (auto-surface `handoff.md` + the journal's authoritative
segment at SessionStart); clause (e′) replacing (e) in `.claude/hooks/_lib.py:cmd_stop_audit`;
the F1/F2 drill runnable via `uv run` (F1 wired into the existing integration-test pattern; F2
as a script the orchestrator invokes at `/triage`). The one-time brief migration is P1's final
item and is itself the first F2 subject.

**What it takes to flip it on:** (a) P1 merges → the artifacts exist and the generator runs, but
clause (e) still governs (old brief still written — a deliberately overlapping window, at the
cost of double bookkeeping for its duration); (b) P2 merges → clause (e′) governs, the brief and
its template are deleted in the same diff, `session-brief.sh` re-points; (c) the owner's only
hand-acts: ratify this note, bless the two plans, and — the first live use — start one fresh
session that resumes from `handoff.md` + journal alone and says so. No daemon flag; this is
workflow tooling, `mind-palace deploy` is not involved.

## Parked decisions

- **PROGRESS.md as a rendering of the seat journal.** Default: unchanged, hand-maintained.
  Re-entry: after four weeks of seat-journal use, if PROGRESS checkpoints are observed to be
  restatements of journal capsules, propose the derivation in a follow-on note.
- **Seat-occupancy lock (the `claim()` analogy, §2.6).** Default: not built; concurrent
  orchestrators remain a procedure error. Re-entry: an observed double-occupancy incident.
- **Multi-track membership (`track:` list-valued).** Default: single-valued (board convention).
  Re-entry: a real artifact that genuinely belongs to two tracks, named in a finding.
- **A `readings.md` schema tightening** (typed commands, machine-parsed results feeding the
  command-center Tier 2). Default: freeform `(timestamp, command, result)` lines. Re-entry: the
  command-center note (NEW NOTE 1 lineage) wanting to consume readings mechanically.
- **Queue-mirroring of handoff events for the ambassador/message lane.** Default: none — files
  are the source (§2.6). Re-entry: the email/return-path design needing a job-shaped projection;
  it would be a *rendering into* the queue, never a move of the source.

## Cross-references

- Commissioning capture: `docs/brainstorms/role-state-and-scoped-handoff.md` (2026-07-26)
- Warrant: `docs/findings/finding-0175.md` (+ its 2026-07-26 triage corrections)
- Superseded in part: `docs/design-notes/session-handoff-gate.md` §2.2–2.3 (§1.1, §2.10)
- Amended by enumeration: `docs/design-notes/agent-workflow.md` §5, §6, §9, §16 (A10)
- Track coordinate reused: `docs/design-notes/track-board-and-deskcheck-gate.md`;
  `scripts/board.py:134-198` (membership + orphan check)
- Cannot-drift falsifier origin: `scripts/docket.py:4-6`
- The gate today: `.claude/hooks/_lib.py:892-920` (clause (e); getmtime `:911`), `:762`
  (clause (a) — the line the old brief mis-cites, §2.2), `:929-937` (clause (f));
  `.claude/hooks/session-brief.sh:46-48` (auto-surface), `:65` (baseline write)
- The durable-seat precedent: `scheduler/queue.py` (single-writer `:17-18`; leases
  `:388-443`; additive migrations `:122-146`; NULL-polarity discipline `:174-189`)
- Contracts generalized: `.claude/skills/checkpoint/SKILL.md` (journal + fresh-agent test);
  `.claude/skills/context-economy/SKILL.md` (the brief being retired; session typing for F2's
  grind-tier spawn)
- Keep-and-link discipline: `docs/findings/finding-0164.md`, `docs/findings/finding-0168.md`
