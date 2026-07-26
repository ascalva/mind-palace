---
type: design-note
id: dn-autopilot-and-delegated-blessing
track: workflow
status: draft
created: 2026-07-25
updated: 2026-07-25
links:
  - docs/brainstorms/autopilot-mode.md
  - docs/design-notes/agent-workflow.md
  - docs/brainstorms/phone-chat-surface.md
  - docs/audits/ops-wave-2026-07-25.md
  - docs/findings/finding-0150.md
  - docs/findings/finding-0193.md
  - docs/findings/finding-0203.md
  - .claude/skills/delegate/SKILL.md
supersedes: null
superseded_by: null
warrant: null
---

# Autopilot and the delegated blessing: an MFA-bound grant, a factored read, an adversarial audit in the reviewer's seat

> Filed by the chat agent as `draft` (chat-side protocol, §8). Ratification is a
> hand edit by the owner — no command performs it, and `gate-guard` denies any
> agent attempt (§10). `/graduate` refuses this note until `status: ratified`.
>
> **This note is a constitutional amendment proposal.** It touches one of the two
> blessing gates named in `CLAUDE.md:62` and in `dn-agent-workflow` §2(4)/§10(2).
> The `draft→ratified` gate on *this note* is emphatically not delegable to the
> mechanism it describes — a note that ratifies itself is void.
> [GROUNDED docs/brainstorms/autopilot-mode.md:154-155]

## 1. Purpose and scope

### 1.1 What this note decides

An **autopilot mode** for low-stakes, quality-of-life work: the owner grants the
`proposed → ready` blessing remotely, via an MFA code bound to the content hash of an
**intent capsule** he has actually read on his phone; an **adversarial audit pair** occupies
the reviewer seat he would have occupied at the keyboard; the run halts on an enumerated
list of conditions rather than "continuing along until completion"; and it terminates at a
merge-ready branch with a **mandatory, never-delegable deskcheck** still ahead of it.

The owner's ask, verbatim, is the source [GROUNDED docs/brainstorms/autopilot-mode.md:12-18],
and his refinement is load-bearing for the whole design:

> *"a lot of times I'm asking you for small quality improvements, like even having spell
> check, or reinvent the 'gf' binding, those are low stakes/QoL that once I believe you
> understand my thoughts/question/idea, then I can grant you an autopilot blessing"*

This note decides: (a) what makes that understanding-check *checkable* rather than vibes
(§2.2); (b) how the MFA grant works and why it is not a rubber stamp (§2.3); (c) what
"low stakes" means such that a machine can verify it and an autopilot cannot decide its
own eligibility (§2.4); (d) what the adversarial auditor is adversarial *to* — count,
independence, cold-read, dissent semantics (§2.5); (e) the stopping conditions (§2.6);
(f) the audit trail (§2.7); and (g) the reversibility story that satisfies NN-5 (§2.8).

Positions carried forward from the brainstorm, unchanged: **the gate is the read, not the
signature** [GROUNDED docs/brainstorms/autopilot-mode.md:40-59]; **the two blessing gates
split** — `proposed→ready` is delegable because it decides execution of upstream-settled
intent, `draft→ratified` never is [GROUNDED docs/brainstorms/autopilot-mode.md:61-77];
**the MFA code binds to a content hash, not an occasion**
[GROUNDED docs/brainstorms/autopilot-mode.md:79-96]. Three owner capsules landed *after*
this note's first draft — SMART as the readback form, the loop, the router
[GROUNDED docs/brainstorms/autopilot-mode.md:224-401] — and the first draft's "intent
capsule" had converged on the readback mechanism independently; §2.2 now reconciles the
two explicitly (SMART is the capsule's field structure; loop and router are load-bearing).
Where this note still goes beyond the brainstorm, it argues the departure explicitly.

### 1.2 Non-goals — read these aloud at ratification

Wrong non-goals fail silently forever [GROUNDED docs/findings/finding-0150.md:44-51], so
each is explicit, and each inferred one is graded:

1. **The owner-present emergency lever is NOT designed here.** The brainstorm's correction
   established that stop-the-bleeding actions are operational, not artifact-gated, and
   concluded the two mechanisms need two notes
   [GROUNDED docs/brainstorms/autopilot-mode.md:174-223]. That lever (pre-reviewed bounded
   action set, MFA-fired, owner watching live) shares only the authentication primitive
   with this note and nothing else. Its note does not exist yet.
2. **`draft → ratified` is untouched — permanently non-delegable.** No auditor holds the
   ground truth of owner intent; `finding-0150`'s silent-forever failure lives at exactly
   this gate. This note *reaffirms* the exclusion (`dn-agent-workflow` §1: "any automation
   of ratification (excluded permanently)") rather than weakening it.
3. **Autopilot never originates a goal.** Under a grant it writes no design note — not
   even a draft. If it learns something design-shaped, it files a finding and halts (§2.6).
   This strengthens the brainstorm's corollary [GROUNDED docs/brainstorms/autopilot-mode.md:75-77].
4. **`deploy` stays owner-in-loop by standing rule.** Out of reach regardless of grant.
5. **Autopilot never merges to main.** Terminal state is a merge-ready branch (§2.8). The
   owner's merge is folded into the deskcheck touchpoint. [DERIVED — from NN-5's
   reversibility requirement, §2.8]
6. **The deskcheck is never delegable.** The owner's own condition, kept verbatim.
7. **The phone chat surface is not built here.** Autopilot consumes an outbound render
   lane that already exists (the exhaust lane) and any inbound channel for the code; the
   capture-inbox surface is `docs/brainstorms/phone-chat-surface.md`'s own future note.
8. **No topic-based "stakes taxonomy."** Blocked on `finding-0193` (§2.4) and structurally
   unnecessary in v1. [INFERENCE — that the structural predicate suffices for the owner's
   named use cases; the owner should confirm his examples all fall inside §2.4's envelope.]
9. **One grant, one plan.** Batch grants (a wave under one capsule) are parked, not designed.

Out of scope also: CI enforcement of the grant schema, and any change to the foundation
denylist — NN-9 surfaces (`CONSTITUTION.md`, `eval/golden/**`, `eval/golden.py`) remain
unreachable by every agent, autopilot included, regardless of MFA [GROUNDED CLAUDE.md:25].

## 2. Principles / decision

### 2.1 The read is factored, never deleted

The blessing gates exist for **comprehension**, not authentication — the failures they
catch are readable-only: a bare `§2.3` in pinned docstring text resolving to a different
document [GROUNDED docs/findings/finding-0203.md:29-48], a `write_scope` structurally
unable to reach its own §7 acceptance [GROUNDED docs/findings/finding-0204.md — minted
with bp-115's merge and since resolved via the amended-write_scope route recorded at
`docs/build-plans/bp-115/plan.md:172-178`], and wrong non-goals that nothing
downstream ever detects [GROUNDED docs/findings/finding-0150.md:44-51]. A design that
swaps the read for a signature deletes exactly the defect class with no other detector.

The decision: **factor the read along the same line Refinement 1 factored the gates.**

| layer | who holds ground truth | who reads it under autopilot | why that reader |
|---|---|---|---|
| intent — goal, non-goals, DoD | the owner, only | **the owner**, on his phone, via the intent capsule (§2.2) | no auditor can substitute; finding-0150's layer |
| execution fidelity — grounding, scope, falsifiers, theatre | the artifacts | **the adversarial audit pair** (§2.5), cold-read | demonstrably outperforms a tired human here |

The evidence for the second row: the ops-wave audit — six independent cold-read auditors —
produced four real findings, one disqualifying on the plan's own terms
[GROUNDED docs/audits/ops-wave-2026-07-25.md:5-36], and both finding-0203 and
finding-0204 were caught by agents reading, not by the owner or by any test. The claim is
not that auditors replace the owner; it is that the owner's read was always doing two
different jobs, only one of which requires him. [DERIVED]

### 2.2 The intent capsule — a SMART readback, looped until fillable, routed at the mouth

The owner's refinement locates the grant at the moment he believes the agent understands
— in conversation, before any plan exists. Taken literally, that is a grant against a
transcript, and the workflow's first principle already forbids it: *"No decision, question,
or state lives only in a chat transcript"* [GROUNDED docs/design-notes/agent-workflow.md:48].
It also quietly breaks Refinement 1's own justification: the gate-split argument grants
`proposed→ready` because *"its parent note was read and blessed by the owner"*
[GROUNDED docs/brainstorms/autopilot-mode.md:67] — but a spell-check or keybinding ask has
no parent note. For QoL work, intent is settled in conversation or nowhere.

**Position: the conversational understanding is where comprehension is *formed*; it becomes
*checkable* only when reified as a text the grant can bind to.** This note's first draft
and the owner converged on that mechanism from opposite directions — his **SMART readback**
[GROUNDED docs/brainstorms/autopilot-mode.md:224-305] and the draft's "intent capsule" are
one artifact. Reconciled: the capsule keeps its name (it is the thing hashed, granted
against, and embedded); **SMART is its field structure**, plus the three fields SMART
lacks. The owner's two follow-on corrections — the loop and the router — are incorporated
below as load-bearing, not decorative.

**Form.** Each SMART letter is this repo's existing vocabulary renamed
[GROUNDED docs/brainstorms/autopilot-mode.md:235-248], and the brainstorm's three gaps
[GROUNDED docs/brainstorms/autopilot-mode.md:275-288] are filled by standing obligations:

| capsule field | SMART letter | existing home |
|---|---|---|
| goal, one sentence | Specific | graduate skill: "statable in one sentence" |
| definition-of-done, runnable — the exact thing the deskcheck later evaluates | Measurable | graduate skill: runnable acceptance |
| write-surface summary + §2.4 predicate results + no open decisions | Achievable | acceptance-reachability check; `session_budget: 1` |
| trace to settled intent (sharpened below) | Relevant | `design_ref`; §1.2 discipline |
| budget ceiling + base commit + TTL | Time-bound | `session_budget` / `cost.estimate`; §2.6 |
| **named falsifier** — the observation that would prove the run wrong | gap 1 | §7's standing acceptance-AND-falsifier rule |
| **explicit non-goals**, inferred ones graded `[INFERENCE]` | gap 2 | the finding-0150 obligation |
| the readback close — owner recognition (grant path, below) | gap 3 | closed-loop readback |

Hard size cap: **≤ 40 lines / ≈ 300 words** — a capsule too long to genuinely read on a
phone defeats the read. [DERIVED]

**Loop — a rejection is a work order, not a verdict.** An unfillable field names,
specifically rather than as vague unease, the decision that is still open; the unfillable
fields ARE the brainstorm agenda [GROUNDED docs/brainstorms/autopilot-mode.md:307-328]:

    attempt → unfillable fields name the open decisions → resolve in conversation
        → re-attempt → fillable → the owner reads → grant

An unfillable field is a **parked decision with a re-entry condition** — already legal
artifact vocabulary (§11 + `re_entry`), nothing new to invent
[GROUNDED docs/brainstorms/autopilot-mode.md:330-339]. One artifact therefore does three
jobs: readiness test, agenda generator, and — once filled — the thing the MFA signs. The
loop runs pre-grant, in attended conversation (later, optionally, through the Ambassador:
*"what is missing from the SMART statement for X?"* is its archetypal query
[GROUNDED docs/brainstorms/autopilot-mode.md:341-352]); it is never autopilot's to run
alone, so non-goal 3 is untouched.

**Router — a failure has two meanings, and which letter fails names the lane**
[GROUNDED docs/brainstorms/autopilot-mode.md:357-388]. Three outcomes, not two:
**pass → the grant path** · **fail-undecided → the loop** · **fail-too-big → the full
ceremony**, discriminated by the graduate skill's session-sizing heuristic surfaced early:
Specific fails ("the objective needs an 'and'") ⇒ decompose · Measurable fails (acceptance
not runnable) ⇒ design pass · Achievable fails on open decisions ⇒ loop · Achievable fails
on zone-sprawl ⇒ too big · Relevant fails ⇒ design note first · Time-bound fails
(> 1 session) ⇒ decompose. This is the safety argument, not just ergonomics: **the chain
remains the default; autopilot is a fast path for the provably small subset, and the
capsule is the gate at its mouth** [GROUNDED docs/brainstorms/autopilot-mode.md:390-401].
An autopilot absorbing design-scale work has failed its own entrance test, and the
entrance test is the thing that notices.

**Relevant without a parent note — the one letter this note must sharpen.** For QoL work
no `design_ref` can exist, yet the router sends "no design_ref, novel intent" to a design
note first. The reconciliation: Relevant passes iff the ask **executes settled intent** —
either a ratified note covers it, or the ask is **design-inert**: it changes no designed
contract, boundary, or behavior of the system (the spell-check class; §2.4's P2 already
walls off the design and enforcement surfaces mechanically). Relevant fails when the ask
carries novel design intent with no note — the `gf`/reference-standard case, an authoring
convention for the whole corpus wearing a keybinding's clothes. For the design-inert
class, the owner's grant is itself the relevance ruling. [INFERENCE — "design-inert" as
the pass condition for note-less QoL work is this note's proposal; the owner should
confirm or replace it at ratification, since it is the boundary of what autopilot may
accept at all.]

**Grant path.** The capsule renders to the phone; the owner reads it and either
**corrects** — the loop repeats, and a correction is *information*, disagreement surfaced
before any work exists — or **recognises the statement as his own goal**, and **the MFA
code is issued from that reading, bound to `sha256(capsule)`** — Refinement 2's property
with the capsule as its object: *"the read is preserved, only its location moves"*
[GROUNDED docs/brainstorms/autopilot-mode.md:84-92, :289-305]. The capsule is the
conversation's **terminating condition**; the gate is the owner's recognition.

The capsule is then embedded **verbatim** as the plan's §1 objective and §9 non-goals.
The plan may elaborate execution; it may not exceed the capsule. "Does not exceed" is
audited, not trusted: Gate A (§2.5) checks every write_scope entry, acceptance item, and
action for traceability to the capsule, and any excess is a halt.

Why the capsule is the agent's text and not the owner's: it is the **demonstration of
understanding itself** — the agent restates, the owner verifies the restatement
(readback-hearback, the aviation/medicine pattern for exactly this problem). This is what
closes SMART's third gap: an agent can emit a flawless SMART restatement of an ask it
misread, but a misread restatement is exactly what the recognition step catches — SMART
is the FORM of the readback; the owner's recognition is the CONTENT. "I believe you
understand" becomes four checkable facts: a text exists; the owner read that text (the
code was issued from its render); everything downstream is mechanically comparable
against that text (hash + verbatim embedding + Gate A); and the deskcheck later evaluates
against the DoD stated in that same text. [DERIVED]

What the owner does **not** read by default: the full plan. That is deliberate and argued,
not elided — a 200-line plan "read" on a phone under-reads in practice, and a fake read is
worse than a factored one. The full-plan render remains available on request; the default
is capsule-only. [INFERENCE — that the owner prefers an honest small read to a nominal
large one; he should confirm or reverse this default at ratification.]

### 2.3 The grant — hash-bound, code-verified, A8's property extended to approvals

**The mechanism.** `approve(sha256(capsule)) → code`, per Refinement 2. Properties:

- The code is `f(secret, artifact-hash)` — HMAC-style over the capsule hash, truncated to
  6–8 digits — never `f(secret, time)`. It authorizes **a text**, not an occasion. Any
  edit to the capsule invalidates it. Single-use.
- The shared secret lives in Keychain (NN-10 [GROUNDED CLAUDE.md:26]); **the model never
  sees it.** A small verifier script recomputes and compares. NN-12 is the constitutional
  precedent for phone-side authentication of the human [GROUNDED CLAUDE.md:28].
- **The verifier performs the `proposed→ready` flip, not the model.** The flip commit
  contains the flip and the grant record (§2.7) together, and records the plan hash at
  flip time. This is NN-3 — *the model advises; code acts* [GROUNDED CLAUDE.md:19] —
  applied to the gate itself: the model requests, the owner decides, code executes.
- The code may transit **any** channel, untrusted included: it is useless without a
  matching artifact hash and it expires. The channel is not the security boundary; the
  binding is. [DERIVED]
- **The grant record carries an attestation no model can mint.** On successful code
  verification, the verifier writes into the grant record (§2.7) a full-width
  `HMAC(secret, "record" ‖ capsule-hash ‖ issued-at)` — domain-separated from the code's
  own derivation, so the stored tag reveals nothing about any code, past or future. HMAC
  is a PRF: the tag is recomputable offline by anything holding the Keychain secret and
  unforgeable by anything that does not — which is every model (NN-10). Without this
  field a well-formed grant record is just prose an agent could write, and the post-hoc
  check below would bless a forged one; with it, laundering-proof is a property of the
  record rather than a hope. Single-use is verifier-enforced: the verifier records each
  consumed capsule-hash on its own side, and a second presentation fails. [DERIVED —
  this closes a hole in the first draft, which stored no verifiable material at all]
- **Expiry** (brainstorm open question 4): the hash alone is not enough, because the world
  can move while the text stands still. The grant is void at the earliest of: a TTL
  (default 72 h, parked for owner tuning), or **base drift** — any file in the plan's
  context manifest or write_scope changed on main since the capsule's base commit
  (mechanical: `git diff --name-only base..HEAD` intersected with those sets). [DERIVED]

**Relation to amendment A8.** A8 redrew the design-note guard from location to status and
made the blessed record laundering-proof by two-layer enforcement: pre-hoc against on-disk
status, post-hoc against **HEAD** status
[GROUNDED docs/design-notes/agent-workflow.md:138-140, :286-305]. This grant is the same
property extended one step: A8 makes an already-blessed *text* tamper-evident; the
hash-bound grant makes the *approval of a text* tamper-evident. Both replace "trust the
occasion" with "verify against the fixed text." Enforcement mirrors A8's two layers:

- **Pre-hoc:** `gate-guard` continues to deny every model-side Edit/Write blessing flip,
  unchanged in every session and role. The verifier is a separate, authenticated channel —
  not an exception *for agents* but a new legitimate *actor*, like the owner's own hand.
- **Post-hoc:** the Stop-gate clause (c) contract gains one narrow exception: a committed
  `proposed→ready` flip is legitimate **iff** the same commit carries a grant record whose
  recorded hash matches the plan's capsule at flip time **and whose attestation tag
  re-verifies against the Keychain secret** — verifiable offline, after the fact,
  laundering-proof in the same sense as A8 (an edit-after-approval breaks the hash chain;
  a fabricated record fails the tag; either way it reads as an unauthorized flip). All
  other agent-side flips remain violations.

**What this amends upstream.** `dn-agent-workflow` §2(4) ("automating a blessing gate
would put an expected-value step inside a bright line") and §10(2) are amended for the
`proposed→ready` half only — and the amendment does not automate the blessing. The
decision remains human, per-occasion, deliberate, and made on a read text; what changes is
the location of the read (phone), its object (the capsule), and the executor of the flip
(the verifier, on the owner's authenticated instruction). `draft→ratified` is reaffirmed
as permanently manual. The wording change to `CLAUDE.md:62` on ratification is one
sentence, because the digest must stay in-context (thinness exemption is for guardrails
only [GROUNDED CLAUDE.md:14-16]). This note cannot and does not make those edits — they
are licensed by ratification (§3) and executed under a plan.

### 2.4 Eligibility — "low stakes" defined structurally, decided by the owner

The failure mode named in the delegation brief is an autopilot that decides its own
eligibility. The design removes the possibility by splitting eligibility into a
**necessary mechanical predicate** and a **sufficient human grant**, with the agent
holding neither.

**Definition: work is low-stakes iff its complete rollback is a git operation.**
Not a topic taxonomy — a structural property, checkable from the plan's own fields:

| predicate | check | grounding |
|---|---|---|
| P1 — repo-confined | every `write_scope` glob resolves inside the worktree | write_scope is the capability [GROUNDED agent-workflow.md:49] |
| P2 — record/enforcement-free | scope ∩ {`CLAUDE.md`, `.claude/hooks/**`, `.claude/settings.json`, `docs/design-notes/**`, `eval/**`} = ∅ | non-goal 3; NN-9 beneath it |
| P3 — no stored-data blast | every plan item carries `touches_stored_data: false` | flag exists per-item [GROUNDED agent-workflow.md:80] |
| P4 — no live-state mutation | no acceptance step or action runs `deploy`, `palace` lifecycle mutation, or any credentialed external call | standing owner rules; NN-4 |
| P5 — bounded | `session_budget` finite and un-self-extendable; cost ceiling stated in the capsule | §2.6 H4 |

P1–P5 are conjunctive, hook-checkable (glob math and grep, the same machinery scope-guard
already runs), and evaluated by the verifier **before** it will accept any code — their
results are printed in the capsule the owner reads. But they are only *necessary*. The
*sufficient* condition is the owner issuing the code, and only the phone makes codes. The
agent's role in eligibility is exactly nothing: it cannot set a stakes field (there is
none), cannot bypass the predicate (the verifier runs it, not the model — NN-3), and
cannot manufacture a grant (no secret). [DERIVED]

The owner's own examples validate the definition: spell check and a `gf` keybinding sit
trivially inside P1–P5; a migration, a schema change, or anything touching the corpus
falls out at P3/P4 — which matches the brainstorm's observation that the named categories
are "precisely the cases where intent is already settled and only execution is open"
[GROUNDED docs/brainstorms/autopilot-mode.md:34-38].

**The finding-0193 constraint, honestly.** The ftype vocabularies in
`docs/templates/finding.md:9` and CLAUDE.md's routing rule are disjoint sets, so *typing*
is currently unreliable and "low-priority has to be typed to be machine-decidable" cannot
be built today [GROUNDED docs/findings/finding-0193.md:20-35]. This design is therefore
deliberately **vocabulary-free**: eligibility reads structural plan fields that exist and
are already enforced, not any type tag. One consequence bites anyway: halt condition H1
(§2.6) routes on the CLAUDE.md ftype set, which 0193 shows is not what builders actually
emit. Until the owner rules on the authoritative set, autopilot applies the conservative
reading — **any finding not unambiguously `codebase | spec-fidelity` halts the run.**
Ambiguity resolves toward stopping. [DERIVED]

### 2.5 The adversarial audit — what it is adversarial to, and what a dissent does

A single auditor sharing the builder's context is a rubber stamp with extra steps
[GROUNDED docs/brainstorms/autopilot-mode.md:129-132]. The working precedent is the
ops-wave audit: independent auditors, cold-read (plan + diff, **not** the builder's
journal), parallel worktrees, one adversarial question verbatim, mutation-verified
[GROUNDED docs/audits/ops-wave-2026-07-25.md:19-23]. Six auditors is wave-sized;
right-sizing per the delegate skill's D2 rule (audit sized to who built it and at what
tier [GROUNDED .claude/skills/delegate/SKILL.md:41-59]), an autopilot run carries
**two mandatory, disjoint audit gates**:

| gate | when | inputs (cold-read) | adversarial to | question |
|---|---|---|---|---|
| **A — intent fidelity** | pre-build, gates the `ready` flip | capsule + plan | intent drift; the 0203/0204 classes | "find how this plan exceeds or misreads the capsule" |
| **B — mechanism** | post-build, before terminal state | capsule + plan + diff | theatre; acceptance-passes-while-objective-fails | the ops-wave question, verbatim |

- **Count:** minimum two audit passes per run, always distinct agent instances. Scale up
  only on evidence (parked, §Parked).
- **Independence:** each auditor runs in a fresh session and own worktree, shares no
  context with the builder or the other auditor, and never receives the builder's journal
  or conversation. Cold-read is load-bearing twice over: it removes anchoring, and it
  forces the artifacts to stand alone — the fresh-agent test applied adversarially.
  [DERIVED from agent-workflow.md §2(5) zone isolation + the audit's method line]
- **Gate A dissent:** pre-build, the plan is unblessed working material — the builder may
  revise and resubmit to a **fresh** Gate-A auditor. If the dissent is intent-level (the
  capsule itself is ambiguous or the ask is misunderstood), the run halts to the owner:
  remediating intent unattended is goal origination (non-goal 3).
- **Gate B dissent:** a mechanism CONCERNS permits **one** remediation cycle, re-audited
  by a fresh auditor — never the one who dissented, which would grade its own remediation
  ask. A second CONCERNS, or any intent-level CONCERNS (work exceeds the capsule), halts.
  Autopilot never adjudicates its own audit.
- **Verdicts are artifacts** (§2.7): a dissent is filed as a finding + audit record either
  way, so a halted run leaves the same trail a completed one does. Mutation-verification
  applies where a runnable acceptance exists; where none does, the auditor must state
  explicitly what it could not verify — silence is not a pass.

### 2.6 Stopping conditions — the halt list

*"Continues along until completion"* is unbounded, and unbounded autonomy is what becomes
an incident [GROUNDED docs/brainstorms/autopilot-mode.md:133-135]. Any one of these halts
the run — halt meaning: stop work, checkpoint the journal, file what exists, park with a
re-entry condition, notify via the exhaust lane:

- **H1 — owner-level finding.** Any finding routed `orchestrator` (`design | math |
  direction`, conservatively read per §2.4). The attended-session rule — park the
  criterion, proceed — is deliberately **inverted** for autopilot: never-block-on-owner
  assumes an owner reachable to unpark; unattended, proceeding past an owner question *is*
  the drift failure. A low-stakes run that raises a design question has left the
  low-stakes envelope by that very fact. [DERIVED — inversion argued, not assumed]
- **H2 — audit dissent** per §2.5 (intent-level immediately; mechanism-level after the one
  permitted remediation cycle).
- **H3 — blocker finding.** Already ends any session [GROUNDED CLAUDE.md, never-block rule].
- **H4 — budget.** Token/cost ceiling from the capsule, or `session_budget` exhausted.
  Neither is self-extendable.
- **H5 — scope pressure.** A second scope-guard denial on the same target. One denial
  means narrow-or-file-a-finding; repeated pressure on one target means the plan
  mis-scoped, and unattended, that is a halt — never route around. [DERIVED from the
  CLAUDE.md write-discipline rule]
- **H6 — enforcement failure.** Any `HOOK-FAILURE` line. Attended sessions rerun and
  reconcile; autopilot must not self-reconcile its own cage. Enforcement-not-applied
  voids the run's premise.
- **H7 — grant void.** Capsule/plan hash mismatch at any checkpoint, TTL expiry, or base
  drift (§2.3). Also fired if the flip commit's grant record fails offline re-verification.
- **H8 — completion (the only terminal halt).** All acceptance closed, Gate B CLEAN,
  artifacts filed (§2.7), branch merge-ready. Autopilot then **stops**: no merge, no
  deskcheck, no self-declared done (the deskcheck-discipline rule: never self-declare).

### 2.7 The audit trail — what an autopilot run leaves behind

A deskcheck evaluates a track against its DoD **and its audit**; an unrecorded audit reads
as "audit: owed" [GROUNDED .claude/skills/delegate/SKILL.md:57-59]. Every run, halted or
completed, leaves:

1. **The grant record** — `docs/build-plans/<id>/grant.md`: capsule text verbatim, its
   sha256, base commit, TTL, budget, predicate results (P1–P5), issued-at and verified-at
   timestamps, and **the verifier's attestation tag** (§2.3). **Never the code or the
   secret** (NN-10): the code is verified and discarded; the attestation is a
   domain-separated HMAC that reveals neither and cannot be produced without the Keychain
   secret — the record proves the binding *checkably*, not by narrative. Committed in the
   same commit as the `proposed→ready` flip (§2.3), which is what makes the flip
   post-hoc-verifiable.
2. **The journal** — the standing obligation, unchanged; every semantic boundary.
3. **Audit records** — Gate A and Gate B verdicts filed in `docs/audits/` (ops-wave
   format), dissents additionally as findings; both named in the deskcheck entry's
   `audit_refs`.
4. **The deskcheck queue entry** — filed into `docs/DESKCHECK-QUEUE.md` at H8, citing DoD
   (= the capsule's DoD, verbatim) and audit_refs.
5. **The run report** — exhaust-lane HTML + push notification, the existing phone-report
   lane, so the owner learns of completion or halt away from keyboard.

Nothing about a run lives only in a transcript; the chain is: capsule → grant record →
plan (capsule embedded) → journal → audits → deskcheck entry, each hash- or
cross-linked to its predecessor. [DERIVED from Principle 1]

### 2.8 Reversibility — the NN-5 mapping

NN-5: gated → validated → reversible, no step skipped [GROUNDED CLAUDE.md:21].

- **Gated:** three gates, none skippable — the owner's capsule grant (human, per-run),
  Gate A (pre-build), Gate B (post-build). Plus the terminal deskcheck, owner-only.
- **Validated:** per-item acceptance + named falsifiers (the plan template's standing
  requirement), mutation-verification where runnable, and the Gate B pass.
- **Reversible, by construction rather than by promise:** the §2.4 predicate *is* the
  reversibility guarantee — P1–P4 jointly mean every effect of the run is uncommitted-to-
  main, git-tracked, stored-data-free, and live-state-free. Rollback of a completed run is
  `delete the branch`; of a merged-then-regretted run is `git revert` of one merge commit.
  There is no state anywhere the rollback does not reach. This is why non-goal 5
  (never merge main) is load-bearing and not conservatism: it keeps the rollback a
  one-step git operation for the entire life of the run. [DERIVED]

### 2.9 Invariants, stated explicitly

1. The model never sees the MFA secret; the model never performs a blessing flip (NN-3).
2. No code verifies against a text the owner did not read: code issuance and capsule
   render are one phone-side act.
3. The capsule embedded in the plan is byte-identical to the hashed capsule; Gate A and
   the Stop-gate both check it.
4. `draft→ratified` has no autopilot path — not for this note, not for any note, ever.
5. The foundation denylist (NN-9) binds beneath every grant; P2 additionally walls off the
   whole design-note tree and enforcement surfaces.
6. Every halt leaves a parked state with a re-entry condition — a run never evaporates.
7. Ambiguity — in routing, in a verdict, in a hash check — always resolves toward halting.
8. The deskcheck evaluates capsule-DoD, not plan-DoD, if the two ever diverge (they cannot,
   by invariant 3, but the tie-break is stated so the check has a defined answer).
9. A grant record without a re-verifiable attestation tag is not a grant record — the flip
   it accompanies reads as unauthorized (§2.3, H7). Narrative alone never proves a grant.

## 3. Consequences

**On ratification of this note, and not before:**

1. **An amendment to `dn-agent-workflow`** (owner-ratified like A1–A9, warrant: this
   note): §2(4)/§10(2) amended for `proposed→ready` per §2.3; Stop-gate clause (c) gains
   the grant-record exception; §6 gains the verifier as a recognized actor. A8 itself is
   untouched.
2. **A one-sentence edit to `CLAUDE.md:62`** — the "Two blessing gates" rule gains the
   autopilot exception for `proposed→ready` with a pointer here. Owner-visible diff,
   executed under a plan whose write_scope names CLAUDE.md explicitly (P2 forbids
   autopilot itself from ever touching that file — the plan that builds autopilot is a
   normal, owner-blessed, attended plan).
3. **Graduation licenses (one attended build plan, possibly two):** the `mfa-verifier`
   script + Keychain enrollment; the grant-record and capsule templates; the P1–P5
   predicate check; the journal-gate (c) exception; the capsule render into the exhaust
   lane; the halt-list supervisor wired into the existing delegate/worktree machinery
   (autopilot is a *mode* of the existing orchestrator + delegated-builder flow, not new
   machinery — the orchestrator session the owner leaves running is the supervisor, with
   its blessing authority replaced by the grant).
4. **Deskcheck/board integration:** autopilot runs appear in `docs/DESKCHECK-QUEUE.md`
   with `audit_refs` mandatory — an autopilot entry without both gate verdicts is
   malformed and reads "audit: owed."
5. **Book chapter, eventually:** the factored read is a genuinely new constitutional
   idea and belongs in the workflow chapter once the mechanism has survived contact.

**Explicitly not licensed:** the emergency lever (needs its own note), any `draft→ratified`
tooling, batch grants, the phone chat surface.

## 4. Wiring & enablement

**How it wires:** config schema `[autopilot]` (`enabled = false` default) in
`config/defaults.toml` + loader; the `mfa-verifier` script (dual-mode like every hook:
stdin JSON and standalone, fail-loud `HOOK-FAILURE` on error) holding no secret in code —
Keychain read at invocation (NN-10); the phone-side code generator (parked: Shortcut vs
tiny app — the *property* is fixed by §2.3, the implementation is not); capsule render
placed into `~/.mind-palace/exhaust/reports/` (lane exists — Syncthing to phone); inbound
code path v1 = owner enters the code via any shell (SSH/Tailscale) into the verifier's
standalone mode, upgraded to the capture inbox when the phone-chat-surface note lands; the
journal-gate (c) exception and the P1–P5 pre-flight inside the verifier; the halt-list
supervisor as orchestrator-session logic (no daemon change).

**What it takes to flip it on:** (a) a build must add: the verifier + templates + config
schema + hook amendment + capsule render step, all under an owner-blessed attended plan
per §3; (b) the owner then: enrolls the shared secret (Keychain + phone generator), sets
`autopilot.enabled = true`, and — the real switch — **issues a grant**, which is per-run
by design: the enable flag alone authorizes nothing, because no code exists until the
owner's phone makes one against a specific capsule hash. First run is deliberately a
trivial ask (the spell-check class) deskchecked end-to-end before a second grant.

## Parked decisions

| decision | default recorded | re-entry condition |
|---|---|---|
| TTL default | 72 h | owner tunes at ratification |
| phone-side generator implementation | iOS Shortcut computing truncated HMAC over the hash prefix | first build plan; property (§2.3) is fixed regardless |
| auditor count scaling | 2 gates, 1 auditor each | first defect that escapes both gates and is caught at deskcheck → raise count or add a seams-style pass |
| batch grants (one capsule, N plans) | not allowed | after 5 clean single-plan runs with zero intent-level dissents |
| stakes taxonomy on top of P1–P5 | none — structural predicate only | finding-0193 resolved by owner ruling; then revisit whether a typed tier adds anything |
| inbound code channel | shell entry (SSH/Tailscale) | phone-chat-surface note ratified and its capture inbox built |
| owner reads full plan vs capsule-only default | capsule-only, full render on request | owner reverses at ratification if he wants the full-plan read (see §2.2 [INFERENCE]) |
| H1 routing vocabulary | conservative: any not-unambiguously-builder finding halts | finding-0193 ruling lands; then route on the authoritative set |
| "design-inert" as Relevant's pass condition for note-less QoL work | as proposed in §2.2 [INFERENCE] | owner confirms or replaces the boundary at ratification |

Each row's prose argument lives in the named section; nothing here is decided by the table.

## Cross-references

- `docs/brainstorms/autopilot-mode.md` — the source thread: ask verbatim (:12-18), the
  read-not-signature principle (:40-59), Refinements 1–2 (:61-96), the withdrawn
  Refinement 3 and its correction (:98-126, :157-172), the two-notes split (:215-223),
  the SMART readback (:224-305), the loop (:307-355), the router (:357-401) — the last
  three landed after this note's first draft and are incorporated in §2.2.
- `docs/design-notes/agent-workflow.md` — the constitution amended: Principle 1 (:48),
  Principle 4 (:51), §6 hook contracts (:131-159), §10 gates (:200-206), **A8**
  (:138-140, :286-305), A9 precedent for amendment mechanics (:306-327).
- `CLAUDE.md` — NN digest (:17-28, esp. NN-3 :19, NN-5 :21, NN-9 :25, NN-10 :26,
  NN-12 :28); the two-gates rule (:62).
- `docs/audits/ops-wave-2026-07-25.md` — the audit precedent: method (:7, :19-23),
  verdicts (:25-36).
- `docs/findings/finding-0150.md` — non-goals fail silently; the §1.2 read-aloud rule.
- `docs/findings/finding-0193.md` — the disjoint ftype vocabularies constraint (§2.4, H1).
- `docs/findings/finding-0203.md` — the read-only defect class, instance 1.
- `docs/findings/finding-0204.md` — instance 2 (write_scope cannot reach acceptance);
  minted with bp-115's merge, `status: resolved` 2026-07-25 via the amended-write_scope
  route (`docs/build-plans/bp-115/plan.md:172-178`).
- `.claude/skills/delegate/SKILL.md` — audit right-sizing (:41-59), fable delegation.
- `docs/brainstorms/phone-chat-surface.md` — the inbound lane's future home; the exhaust
  lane's existence (:24-30).
- `docs/tracks/workflow.md` — the track manifest this note's `track:` coordinate names.
