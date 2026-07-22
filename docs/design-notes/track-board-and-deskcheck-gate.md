---
type: design-note
id: dn-track-board-and-deskcheck-gate
track: workflow
status: ratified            # draft → ratified → superseded.  draft→ratified is an OWNER-ONLY hand edit.
implementation: design-only   # licenses WF-1 (board substrate) + WF-2 (deskcheck gate); nothing built
created: 2026-07-21
updated: 2026-07-21
links:
  - docs/findings/finding-0153.md                    # THE WARRANT — the deskcheck gate + track hierarchy (owner practice)
  - docs/findings/finding-0148.md                    # evidence — K1 never minted behind a "wave complete"
  - docs/findings/finding-0141.md                    # evidence — dreamers sealed-but-not-wired
  - docs/findings/finding-0152.md                    # the bless-handoff friction WF-2 softens
  - docs/findings/finding-0154.md                    # a queued track the board must carry from day one
  - docs/design-notes/agent-workflow.md              # the artifact-chain constitution this EXTENDS (never edits)
  - docs/design-notes/session-handoff-gate.md        # RATIFIED — the Stop-audit clause family two teeth join
  - docs/templates/build-plan.md                     # gains `track:` (additive)
  - docs/templates/design-note.md                    # gains `track:` (additive)
supersedes: null
superseded_by: null
warrant: docs/findings/finding-0153.md
---

# The track board and the deskcheck gate — follow-through made structural

> Composed at **fable** (main loop, 2026-07-21, session-41; owner set `/model` + `/effort f@h`
> for this pass; harness-reported model id `claude-fable-5`. Per the banner-unreliability
> lesson of finding-0147, the owner should cross-check the session's usage at ratification —
> a banner is a claim, not a proof). Filed as `draft`; ratification is an owner-only hand
> edit. **Design only; builds licensed are §3's WF-1/WF-2.** Every nontrivial claim carries a
> grade (`[ESTABLISHED]`/`[DERIVED]`/`[INFERENCE]`); code claims verified on disk this
> session at `3f56c26`.

## 1. Purpose and scope

### 1.1 What this note decides

The owner's spec (2026-07-21, finding-0153 + the same-day refinements): work is tracked as
**tracks × phases** on a JIRA-like board — `brainstorm (any model) → design-pass (Fable
required) → graduate (Fable/Opus by size) → build (right model per job) → audit (Opus/Fable)
→ deskcheck (Opus; the owner approves or sends back) → CLOSED` — and **a track is closed
only by an owner-approved deskcheck**. Three sessions' evidence shows why convention alone
fails: the dreamers sealed-but-never-wired (finding-0141), the reference track half-built
with no owner (finding-0145/0154), K1 never minted behind a "wave complete" (finding-0148).
`[ESTABLISHED — the owner's words + the three findings]`

This note makes that workflow **structural** under the house rule that a property is only
real when a test/ratchet proves it. It decides: the track as a front-matter coordinate (D1);
the board as a **derived** view, never a maintained file (D2); the deskcheck record as a
typed artifact whose verdict is owner-only, gate-guarded like a blessing (D3); the surfacing
obligations (session brief + `/triage`) made automatic (D4); the seal's follow-through shape
with its Stop-audit tooth (D5); the clause-(c) yield posture for owner-staged blessings
(D6); the honest, non-structural handling of model-per-phase (D7); and the consolidation of
the four tracking surfaces (D8).

### 1.2 Out of scope

- **No change to the two blessing gates** (draft→ratified, proposed→ready) or to any
  ratified text (A8). This note ADDS a third owner-verdict artifact; it touches neither.
- **No change to `write_scope`/scope-guard semantics**, the foundation denylist, or any
  safety bright line.
- **No web UI / database for the board** — markdown + a generator at this scale (P-WF3).
- **The audit phase's internal method** — the audit rides existing practice (the
  finding-0147/0149 precedent); only its *recording* is standardized here.
- **Retroactive re-opening of CLOSED history** — the five owed deskchecks enter the board;
  older, genuinely-delivered work is not re-litigated (the owner may deskcheck anything on
  request, but the backlog is the five named items).

## 2. Principles / decisions

### 2.1 D1 — the track is a front-matter coordinate, not a registry

**Ruling.** A track is identified by a kebab slug carried as an additive front-matter key —
`track: <slug>` — on design notes and build plans (findings optionally; they already route
by ftype). Track-level metadata (title, the definition-of-done checklist, the owed-deskcheck
statement) lives in a small manifest, **`docs/tracks/<slug>.md`** — the track's identity
card, the thing a deskcheck evaluates against. The artifact tree remains the only store: a
track's members are exactly the artifacts declaring its slug (grep-able, hook-parsable).
`[DERIVED — the house "artifacts are the database" pattern]`

- **Additive-safe:** front-matter consumers are key-selective — `scope-guard` reads
  `write_scope`; the docket reads `status`; φ_doc mints edges only from its named ref keys
  (`_FRONT_MATTER_REF_KEYS`, `ops/code_sensor.py:126-131` — `track:` is a slug, not a path,
  so no reference edge is minted and the citation graph is untouched). `[ESTABLISHED]`
- **The manifest carries the DoD** — e.g. code-ingest's manifest lists "integrator
  densification (finding-0151)" as a DoD item, so the deskcheck can't pass while it's open.
  DoD edits are working-material (owner or orchestrator may add; only a deskcheck closes).
- **Rejected:** a central `tracks.yaml` registry (a second source of truth that drifts from
  the artifacts — the exact docket lesson); a sqlite store (machinery ahead of need; nothing
  queries tracks at runtime). Recorded, not straw-manned: the registry WOULD give atomic
  renames — accepted cost, renames are rare and grep-able.

*Falsifier (F-WF1):* two artifacts of one body of work end up under different slugs with no
manifest naming both ⇒ the coordinate failed its job; the generator's orphan report (D2)
must surface it, or D1 needs a stricter registration step.

### 2.2 D2 — the board is DERIVED; the generator is the enforcement

**Ruling.** `scripts/board.py` (the `docket.py` pattern, verbatim: *"a DERIVED view,
recomputed from the artifact tree on every run: NO persisted state, so it cannot drift"* —
`scripts/docket.py:4-6`; front-matter parsing reused from `.claude/hooks/_lib.py`, never a
second parser — `:16-18`) renders **both** views from the tree:

- `docs/TRACKS.md` — the board: swim lanes = tracks; per item its computed phase;
- `docs/DESKCHECK-QUEUE.md` — the owed-deskchecks inbox: exactly the tracks whose computed
  phase is `deskcheck-pending`, plus the standing backlog rows.

Both generated files carry a `<!-- GENERATED by scripts/board.py — do not hand-edit -->`
banner; the hand-authored versions seeded this session become the manifests' content at
WF-1 and are thereafter derived. **Derivation replaces enforcement**: a board that cannot
be stale needs no hook to keep it honest. `[DERIVED — the docket precedent, proven since
bp-072]`

**The phase function (computed, per track):**

| computed condition (from front matter + dc records) | phase |
|---|---|
| a linked note is `draft` | design-pass |
| notes `ratified`, some licensed plans not yet minted or `proposed` | graduate |
| any plan `ready`/`in-progress` | build |
| all minted plans `complete`, no approved deskcheck record | **deskcheck-pending** (the queue) |
| an approved `dc-NNN` names the track and its DoD items are closed | **CLOSED** |
| manifest declares `dormant-by-design` + its warrant | dormant (deskcheck = confirm) |

The **audit** phase is carried as a flag inside `deskcheck-pending` — "audit: present/owed"
— computed from the manifest's `audit_refs` (appended when an audit finding lands). Audit
depth is **risk-proportional** (delegated/lower-tier builds ⇒ independent Opus pass; a
supervised same-tier merge ⇒ the merge scrutiny IS the audit, recorded as such) — the
right-sizing rule, recorded in the delegate skill by WF-2. `[DERIVED — owner's phase list,
composed with the 2026-07-11 right-sizing rule; the owner confirms the risk-proportional
reading at ratification (§5-2)]`

**Rejected:** hand-maintained TRACKS.md (this session's seed — already the proven failure
shape); a Stop-audit clause forcing board edits at seal (enforcing maintenance of a file
that derivation makes unnecessary — a hook where a compiler belongs).

*Falsifier (F-WF2):* `board.py` output disagrees with any artifact's front matter, or two
consecutive runs over an unchanged tree differ ⇒ the generator is stateful/buggy — fix the
generator, never hand-edit the output.

### 2.3 D3 — the deskcheck record: a typed artifact; the verdict is a third owner-only gate

**Ruling.** A deskcheck is recorded as **`docs/deskchecks/dc-NNN.md`** (new template,
`docs/templates/deskcheck.md`): front matter `{type: deskcheck, id, track, date, items:
[plan ids], audit_refs, verdict: pending | approved | needs-work, send_back: <phase — on
needs-work>, links}` and a body carrying the bundle — **what was built · how · surprises ·
the demo script or the honest state · what is NOT done** (the owner's deskcheck content,
finding-0153 verbatim). The agent prepares everything and sets `verdict: pending`. **The
verdict flip to `approved`/`needs-work` is the owner's hand — the third owner-only gate**,
enforced exactly like the two blessings:

- **pre-hoc:** `gate-guard` (PreToolUse Edit/Write, `.claude/hooks/gate-guard.sh:1-10` —
  today firing on `docs/design-notes/` + `docs/build-plans/**/plan.md`) gains
  `docs/deskchecks/**` with the denied transition "verdict leaves `pending` by an agent
  edit". Additive pattern in an existing hook. `[DERIVED]`
- **post-hoc:** Stop-audit clause (c) (the blessing-transition audit,
  `.claude/hooks/_lib.py` — the (a)–(e) family verified live this session) extends its
  transition set with the verdict flip, so a Bash-mediated flip is caught even past the
  pre-hoc guard — the same double enforcement blessings carry.
- **Closure legality is computed, not flipped:** no artifact carries a "closed" boolean —
  a track is CLOSED iff an *approved* dc names it and its manifest's DoD items are closed
  (D2's phase function). Nothing exists for an agent to launder. `[DERIVED — the
  "unrepresentable beats forbidden" house pattern]`
- The verdict ceremony reuses the blessing ceremony verbatim (lazygit; the agent pre-loads
  the commit message; **never polls** — D6).

**Rejected:** verdicts in the plan files (spreads owner-gated lines across many files —
gate-guard's pattern surface should stay small); verdicts only in chat (the anti-pattern
this whole note exists to kill — no decision lives only in a transcript).

*Falsifier (F-WF3):* an agent-authored commit changes a dc verdict, or the board shows a
track CLOSED with no approved dc on disk ⇒ the gate is decorative; treat as a gate incident
(the clause-(c) posture), not a bug.

### 2.4 D4 — surfacing is automatic: the brief and the triage sweep

**Ruling.** The owed-deskchecks inbox is surfaced the way plans/findings/OQ already are:

- **SessionStart:** `session-brief.sh` (the script that assembles the `═══ SESSION BRIEF ═══`
  block — its plan/finding/OQ counts appear in every session's opening context, observed
  live this session) appends one line: `Deskchecks owed: N (top: …)` sourced from
  `board.py --queue-count` (the docket `--count` idiom, `scripts/docket.py:20-22`). The
  standing obligation stops depending on the agent's memory. `[DERIVED]`
- **`/triage`:** the sweep adds the third inbox — route/park/surface each owed deskcheck
  beside findings and OQ (one skill edit).
- The resume-brief template gains a standing "deskchecks owed" line (already practiced this
  session; the template makes it durable).

*Falsifier (F-WF4):* a session opens while a deskcheck is owed and the brief block carries
no owed-count line ⇒ the injection broke; surfacing has silently regressed to memory.

### 2.5 D5 — the seal answers follow-through, and the Stop gate checks the shape

**Ruling.** A seal (a plan flipping to `complete`) must contain a **`## Follow-through`**
block answering five questions: *built? · wired/delivered (or why dormant)? · does a
consumer use it? · track state (what remains on this track)? · did this open a new
track/finding?* — the checkpoint skill's seal shape gains the block; **Stop-audit clause
(f)** (new, joining (a)–(e)) blocks session close when a plan was flipped to `complete`
this session and its journal tail lacks the block (the clause-(a) staleness pattern, one
more grep-class check — crude, post-hoc, and real). `[DERIVED — journal-gate's existing
clause family; the "wave complete" lesson made mechanical]`

*Falsifier (F-WF5):* a sealed plan's journal passes the gate without honestly answering
"wired?" (e.g. the block is present but content-free) ⇒ the grep-class check is too weak —
tighten to per-question tokens, or accept the residual (the deskcheck itself is the
backstop; the gate only forces the writing).

### 2.6 D6 — clause (c) learns to yield to an owner-staged blessing (finding-0152)

**Ruling, honest about attribution limits.** A Stop hook cannot prove *who* edited the
working tree. What it CAN check cheaply: whether this session's own tool log wrote the
flipped files. The fix ships in two layers:

1. **Behavioral (shipped already, memory-bound):** never arm watchers/polls for an
   owner-manual commit; state the loaded message once and yield the turn.
2. **Gate message (WF-2):** when the uncommitted diff is *exactly* the blessing/verdict
   shape (status/verdict lines only, in gate-guarded files) — the message becomes: *"owner
   blessing appears staged — if these flips are yours (agent), revert; if the owner's, say
   so once and YIELD (do not poll; do not re-ask)."* Same block, correct posture. A full
   attribution fix (session-write tracking) is parked (P-WF2) — the behavioral rule plus
   the message covers the observed waste at zero new machinery. `[DERIVED — the friction
   is measured (finding-0152: repeated watcher spawns this session); the fix is
   proportional]`

*Falsifier (F-WF6):* an agent session still burns >1 watcher/poll cycle on an owner-staged
blessing after WF-2 lands ⇒ the message+rule pair failed; unpark P-WF2.

### 2.7 D7 — model-per-phase: recorded and visible, honestly not structural

**Ruling.** The phase→model table (design-pass **Fable**; graduate Fable/Opus; build
right-sized; audit Opus/Fable; deskcheck Opus) is enforced **procedurally**: (a) artifacts
record `composed at <tier>` in their banner AND the tier is verified by completion-usage /
harness report, never self-report (the finding-0147 lesson — a banner lied this session);
(b) the cockpit pins launch defaults (opus-high; the owner re-tiers for design — both
verified in `scripts/cockpit.sh:96-99` / `scripts/orchestrator-launch.sh:33`, edited this
session); (c) the board renders the phase's required tier so a mismatch is visible at a
glance. **Structural enforcement is parked** (P-WF1) with a concrete re-entry: WF-2 carries
a five-minute investigation item — does the hook environment expose the running model id?
If yes, gate-guard can refuse a design-note *creation* commit at a non-Fable tier; if no,
the park stands and says so. `[INFERENCE on the hook-env question — deliberately parked,
not asserted]`

*Falsifier (F-WF7):* a design note is composed at the wrong tier and nothing surfaces it
before ratification ⇒ the procedural layer failed; P-WF1's priority rises to the owner.

### 2.8 D8 — consolidation: state vs log (four surfaces become two)

**Ruling.** After WF-1: **the generated board is the state authority** (which track, which
phase, what's owed); **PROGRESS.md becomes an append-only session log** (what happened,
when — never re-stated state); **PARKING-LOT.md** stops gaining track-scoped rows — new
parks live in the owning track's manifest (existing rows migrate lazily, each when its
track is next touched; no big-bang sweep). The DESKCHECK-QUEUE stays as the generated
filter view. `[DERIVED — single-writer + single-source; the drift this session found in
PROGRESS/parking-lot is the evidence]`

### 2.9 Enforcement summary (property → tooth → tier)

| property | tooth | tier |
|---|---|---|
| board cannot go stale | derived by `board.py`; no persisted state | **structural** |
| track closure needs the owner | closure computed from an approved dc; verdict flip gate-guarded pre-hoc + clause-(c) post-hoc | **structural** (double) |
| owed deskchecks cannot drop | brief injection + `/triage` third inbox + F-WF4 | guard |
| seals answer follow-through | clause (f) grep on the seal shape | guard (post-hoc) |
| owner-staged blessings don't cause thrash | behavioral rule + clause-(c) yield message | process |
| model-per-phase | banner + usage verification + board visibility; P-WF1 investigates the structural upgrade | process (named limit) |

## 3. Consequences — licensed builds (session-sized; jump the queue by owner order)

The owner ruled "build this immediately" — WF-1/WF-2 run **before** bp-090 (their write
scopes are disjoint from the K/CI plans except `scripts/**` and the skills/hooks tree, so
they must simply not run concurrently with bp-090; they are small).

- **WF-1 — the board substrate.** `track:` key into the two templates + backfilled onto the
  ACTIVE artifacts (the seven current tracks' notes/plans — a bounded, mechanical sweep);
  `docs/tracks/<slug>.md` manifests for the seven (content = this session's hand-seeded
  board rows + DoD items, incl. code-ingest's finding-0151 DoD line); `scripts/board.py`
  (docket pattern, `_lib.py` parser reuse) + generated TRACKS.md / DESKCHECK-QUEUE.md with
  the do-not-hand-edit banner; `session-brief.sh` owed-count injection; `/triage` skill
  edit. **The generator caps every rendered table row at ≤190 chars** (owner rule 2026-07-21;
  terse cells, detail in prose beneath) so the board stays readable unwrapped. Born green:
  generation reproduces this session's seeded truth. *Falsifiers F-WF1, F-WF2, F-WF4 as
  tests/checks.* (~1 session, opus.)
- **WF-2 — the deskcheck gate.** `docs/templates/deskcheck.md` + `docs/deskchecks/`;
  gate-guard extension (verdict denial) + clause-(c) transition-set extension (post-hoc
  verdict audit) + the clause-(c) yield message (D6); Stop-audit clause (f) (the seal
  shape) + the checkpoint skill's Follow-through block; the delegate skill's
  audit-right-sizing rule; the P-WF1 hook-env investigation (5-minute item, journaled
  either way). *Falsifiers F-WF3, F-WF5, F-WF6 as tests where testable (gate-guard has a
  `--standalone` test mode, `gate-guard.sh:9`), else standing review checks.* (~1 session,
  opus.)
- **Explicitly NOT licensed:** any board UI/store beyond markdown+generator; any change to
  blessing gates, scope-guard, or ratified notes; the five owed deskchecks themselves
  (they are owner sessions, not builds — scheduled by the owner off the queue).

## Parked decisions

| id | decision | default recorded | re-entry condition |
|---|---|---|---|
| P-WF1 | structural model-per-phase enforcement | procedural (banner + usage verify + board visibility) | WF-2's hook-env probe finds a model id available to hooks |
| P-WF2 | true authorship attribution for working-tree flips (owner-staged vs agent) | the D6 message + behavioral rule | F-WF6 fires (thrash recurs despite the rule) |
| P-WF3 | board as web UI / sqlite | markdown + generator | the board outgrows a screen (≫ ~20 concurrent tracks) or the phone needs it interactive |
| P-WF4 | auto-drafting dc bundles from journals/reports | agent drafts by hand from the seal + phone report | drafting measured as the bottleneck after a few deskchecks |
| P-WF5 | findings carry `track:` | optional | triage finds routing needs it |

## 5. Open questions (owner)

1. **The phase-model table's audit row** — confirm the risk-proportional reading (§2.2):
   independent audit for delegated/lower-tier builds, merge-scrutiny-as-audit for
   supervised same-tier ones. (Default recorded: risk-proportional.)
2. **Deskcheck cadence** — batched sessions (2–3 owed items, pre-prepared bundles, ~30 min)
   vs per-track on demand. (Default: batched, owner-called.)
3. **The five owed deskchecks' order** — recommend: inner/outer M0+S1 first (genuinely
   demonstrable), then dreamers (a decision is owed: wire vs dormant), then AL-1/2/3, G-A,
   effectors-confirm.
4. **Does `dormant-by-design` require a dc record too** (a signed "accepted dormant"), or
   is the manifest note + finding-0011-style warrant enough? (Default: manifest + warrant;
   a dc only if the owner wants the ceremony.)

## Cross-references

**Code (verified on disk this session @ `3f56c26`):** `scripts/docket.py:1-25` (the derived-
view precedent + `_lib.py` parser reuse + `--count`/`--write` idioms) ·
`.claude/hooks/gate-guard.sh:1-30` (the blessing-denial hook + `--standalone` mode + the
worktree-aware ROOT preamble every sibling copies) · `.claude/hooks/_lib.py` (the Stop-audit
clause family (a)–(e), observed firing live this session: (c) on the six-plan blessing, (e)
on brief staleness) · `.claude/hooks/session-brief.sh:46-52` (brief assembly + session-
baseline write) · `ops/code_sensor.py:126-131` (`_FRONT_MATTER_REF_KEYS` — `track:` mints no
edge) · `scripts/cockpit.sh:96-99` + `scripts/orchestrator-launch.sh:33` (the pinned launch
tiers) · `docs/templates/{build-plan,design-note,finding}.md` (the template family the two
additions join).

**Design:** finding-0153 (warrant; the phase pipeline + hierarchy) · findings
0141/0145/0148/0151/0152/0154 (the evidence set + the queued consumers) ·
dn-session-handoff-gate (the clause family) · dn-agent-workflow (the constitution this
extends; its §5 thinness rule is honored — CLAUDE.md gains nothing; depth lives here and in
the skills WF-2 edits).
