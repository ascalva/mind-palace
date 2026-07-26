# Brainstorm — autopilot mode: MFA-delegated blessing with an adversarial auditor in the owner's seat

Captured by the orchestrator from a live owner ask (2026-07-25, session-49). A **constitutional
amendment proposal** — it touches the two blessing gates, which are the load-bearing safety
mechanism of the whole artifact chain. Captured as brainstorm; adoption requires a design note and
a deliberate ratification, not a session decision.

## 2026-07-25 (session-49)

### The ask, verbatim

> *"I also have a new idea, I understand you may have some pushback, but for low-priority, quality
> of life, bug hunting, disaster recovery, we can have an auto pilot mode, this way, we can talk
> about it, form it in a session or a prompt, and I give you some MFA code (i was just thinking of
> a way to prove my approval from my phone) and that grants you the blessing needed for that
> particular ask, that the agent already follows standard protocols, where instead of me, there is
> an adversarial auditer, all to say it's peer reviewed with the relevant parties at each step and
> continues along until completion, the deskcheck is still mandatory."*

### ⚑ The parts that are RIGHT, and stronger than they may look

Not a reflexive objection — three of the four load-bearing choices here are well made:

1. **The deskcheck stays mandatory.** This is the whole reason the proposal is discussable. The
   deskcheck is the *terminal* human gate, and it is the one that cannot be gamed by a plausible
   artifact, because it demands the thing **working**, not the thing **described**. Keeping it
   means autopilot can produce a wrong result but cannot silently *close a track* on one.
2. **An adversarial auditor is not a downgrade for what it can check.** Precedent exists and it
   worked: `docs/audits/ops-wave-2026-07-25.md` — *"six independent auditors, cold-read, parallel
   worktrees, mutation-verified"* — produced `finding-0186`/`0187`/`0188` and `finding-0191`, all
   real, one of them (0188) disqualifying on the plan's own terms. Cold-read adversarial agents
   demonstrably outperform a tired human on **grounding, mutation-survival, and internal
   consistency**.
3. **The category scoping is the sharpest part of the idea.** *"Low-priority, quality of life, bug
   hunting"* are precisely the cases where **intent is already settled and only execution is
   open** — the goal of a bug fix is self-evident from the bug. That is not an arbitrary
   low-stakes carve-out; it is a principled one, and it happens to name the exact region where the
   owner's read adds least.

### ⚑⚑ The one thing that must not be lost: THE GATE IS THE READ, NOT THE SIGNATURE

`CLAUDE.md`: *"Two blessing gates are owner-only, by hand. `draft→ratified` (a design note) and
`proposed→ready` (a plan split) are never done in a session."*

An MFA code proves **authentication** — that Alberto approved. The gate exists for
**comprehension** — that Alberto *read*. Those are different properties, and only the second one
catches the failures the gates were built for. Evidence from this session alone:

- `finding-0203` — bp-110 pins a bare `§2.3` inside a **docstring**, meaning a different document's
  §2.3. Caught by reading, invisible to any test.
- `finding-0204` — bp-115's `write_scope` structurally cannot reach its own §7 acceptance. Third
  instance this wave (with `0177`, `0191`).
- `finding-0150` (prior) — **wrong non-goals fail silently forever.** The standing rule is that the
  owner reads §1.2 explicitly at ratification *because nothing downstream ever detects a wrong
  one*.

⇒ A design that swaps the read for a signature deletes exactly the class of defect that has no
other detector. **But the proposal does not actually have to do that** — see the two refinements
below, which preserve the read while granting nearly everything asked for.

### Refinement 1 — SPLIT THE TWO GATES. They are not the same risk.

They are named together in `CLAUDE.md` but they guard different things:

| gate | what it decides | delegable? |
|---|---|---|
| `proposed → ready` (build plan) | **execution** of intent already ratified upstream | ✅ **yes** — the plan is a *decomposition*, not a decision; its parent note was read and blessed by the owner |
| `draft → ratified` (design note) | **the intent itself** — objectives, and §1.2 **non-goals** | ❌ **never** — this is where `finding-0150`'s silent-forever failure lives, and no auditor holds the ground truth (what the owner *wants* exists only in his head) |

This single split grants most of the ask. Autopilot operating on plans graduated from an
already-ratified note is *executing an intent the owner personally approved* — the adversarial
auditor then checks the things it is genuinely better at (grounding, reachability, falsifiers,
mutation survival) and never has to substitute for intent, because intent was fixed upstream.

**Corollary, and it is a strong one:** an autopilot restricted to `proposed→ready` can never
originate a goal. It can only carry out one the owner already ratified. That is the same shape as
NN-3 (*the model advises; code acts*) lifted to the process layer.

### Refinement 2 — BIND THE MFA CODE TO THE ARTIFACT'S CONTENT HASH

The weakness of a bare MFA code is that it authorizes *an occasion*, not *a text* — the artifact
could change between approval and use, and the code would still verify.

Bind it: `approve(sha256(plan.md)) → code`. Then

- the code proves *"I approved **this exact artifact**"*, not *"I was awake at 9pm"*;
- **any** edit to the plan invalidates the approval — which is precisely the `HEAD`-keyed,
  laundering-proof property amendment A8 already gives ratified design notes;
- and it composes with the phone surface (`docs/brainstorms/phone-chat-surface.md`): the artifact is
  rendered to the phone, the owner **reads it there**, and the code is issued from the reading.
  **The read is preserved, only its location moves.** That is a genuinely better answer than either
  "owner at the keyboard" or "MFA as a rubber stamp."

NN-12 already sets the precedent for phone-side authentication of the human (*"a passphrase/callback
authenticates the human before personalized content is spoken"*), so this is an extension of an
existing constitutional pattern rather than a new one.

### ⚑ Refinement 3 — CARVE OUT DISASTER RECOVERY. It is the one category that inverts.

Three of the four named categories are well chosen. **Disaster recovery is the exception and it
should be removed from the list**, for a reason specific to how adversarial auditing works:

**An auditor's power comes from reading the artifacts. In a disaster, the artifacts are exactly
what may be untrustworthy.** The auditor would be checking a broken system against a description
that the breakage may have invalidated — highest stakes, most time pressure, least reliable
baseline, and the greatest chance of touching something irreversible. It is the scenario where a
human in the loop is worth *most*, not least.

Supporting constraints already on the books: NN-5 (*self-modification is gated → validated →
reversible; no step skipped*), NN-9 (*the fixed points are sacred — `CONSTITUTION.md` and the frozen
golden set are never auto-modified*), and the standing owner rule that **`mind-palace deploy` is the
one owner-in-loop gate, never run autonomously**. An autopilot with a pre-granted blessing operating
under disaster conditions is in tension with all three.

Counter-proposal for that case: autopilot may **diagnose, propose, and stage** a recovery — the full
adversarial-review pipeline, right up to the action — and then **stop for a live human**. That
preserves the speed benefit (the thinking is done when the owner arrives) without pre-authorizing the
irreversible step.

### What autopilot must never reach, regardless of MFA

- `CONSTITUTION.md`, `eval/golden/**`, `eval/golden.py` — the foundation denylist, NN-9. Never.
- `draft → ratified` — refinement 1.
- `deploy` — standing owner rule.
- The deskcheck — the owner's own proposal already says this; keep it explicit.

### Open questions

1. **What exactly is the adversarial auditor adversarial *to*?** The wave audit used **six
   independent cold-read auditors**; a single auditor sharing the builder's context is not a peer
   review, it is a rubber stamp with extra steps. The count, the independence, and the cold-read
   property are the mechanism — they must be specified, not implied.
2. **What is the stopping condition?** *"Continues along until completion"* needs a bound: a
   blocker finding, a budget ceiling, N consecutive failed gates, or a falsifier firing should all
   halt it. Unbounded autonomy is the part that turns a good idea into an incident.
3. **Is the auditor's verdict recorded as an artifact?** It must be — the deskcheck evaluates a
   track against its DoD *and its audit*, so an unrecorded audit reads as "audit: owed" on the
   board. Autopilot should file its audit like any other.
4. **Does MFA expire?** A code bound to a content hash arguably needs no TTL (the hash is the
   binding), but a stale approval resurfacing weeks later is a real failure mode.
5. **How does this interact with `finding-0193`?** "Low-priority" has to be *typed* to be
   machine-decidable, and the ftype vocabulary is currently two disjoint sets.

### Recommendation

**Pursue it, scoped.** Specifically: `proposed→ready` only · MFA bound to a content hash and issued
from a phone-side *read* · disaster recovery downgraded to propose-and-stop · adversarial auditor
specified with a count and a cold-read requirement · explicit stopping conditions · deskcheck
mandatory, as the owner already said.

That version is not a weakening of the gates. It is **the same gates with the owner's read relocated
to his phone and the auditable half handed to something better at it than a human.**

⇒ Needs a design note before any plan. This is an amendment to the operating constitution, and the
`draft→ratified` gate on *that note* is emphatically not delegable to the mechanism it describes.

### ⚑ CORRECTION — "disaster recovery" meant OWNER-PRESENT. Refinement 3 was aimed at the wrong scenario.

Owner clarified, verbatim: *"what I meant by disaster recovery: if we are working, migrating, etc,
and the system is failing in some way and requires immediate action, I can give you my approval to
stop the bleeding."*

**The orchestrator misread this and the objection above is largely withdrawn.** Refinement 3 argued
against *unsupervised* recovery — autopilot alone, artifacts possibly invalidated by the breakage,
no human. The actual proposal is the opposite: **the owner is present, live, watching the bleed.**
The MFA is not substituting for his judgment; it is substituting for the **ceremony** — the lazygit
blessing flip, the artifact round-trip, the normal pace of the chain — at the moment those are the
thing standing between a diagnosis and a stop.

The "auditor reads artifacts that may be untrustworthy" argument does not apply, because the
auditor is not the one deciding. The owner is. Keep the earlier text as the record of a wrong
reading, not as live guidance.

### ⚑ But the correction exposes a better question: WHICH GATE IS ACTUALLY IN THE WAY?

Worth asking before designing anything, because the answer may be *none*. Stop-the-bleeding actions
in this system are overwhelmingly **operational, not artifact-gated**:

| real incident | what stopped/would stop the bleeding | gate involved |
|---|---|---|
| session-44: `code_backfill` at 99% CPU for 74m50s, died on TimeoutError (`command-center.md`) | `palace stop` | none — lifecycle command |
| session-49: daemon down, 1,766 duplicate queued jobs | `palace up` after dropping idempotent re-syncs | none — owner rule, not a blessing |
| a bad merge on main | `git revert` | none |
| a runaway lane | flag off / kill the job | none |

⇒ **`draft→ratified` and `proposed→ready` are rarely what blocks an emergency.** They gate *new
design* and *new work*, and an incident usually needs neither — it needs an operational lever
pulled now. The genuinely gated emergency action is `deploy`, which is owner-in-loop **by standing
rule** and already assumes the owner is present.

So the emergency case may not need blessing-delegation at all. What it plausibly needs is
**operational authority that is fast to exercise and provably bounded** — a different mechanism
from the autopilot gate question, and cleaner for not being entangled with it.

### ⚑ The principle worth designing to: PRE-AUTHORIZE THE PLAYBOOK, NOT THE IMPROVISATION

Fast approval of a *novel* action under stress is how incidents compound. Fast execution of a
*rehearsed* one is how they stop. The asymmetry is the whole design:

- **Pre-enumerate the stop-the-bleeding action set** — `palace stop`, kill a job, revert a merge,
  flag off a lane, drain the queue — each with its blast radius and reversibility stated.
- **Adversarially review that list at leisure**, when nothing is on fire. That is when the thinking
  is good and the artifacts are trustworthy. The review that Refinement 3 worried could not happen
  mid-incident **happens beforehand instead** — which resolves the objection rather than accepting
  it.
- **MFA authorizes firing one item from the reviewed list**, not authoring a new action. Bound to
  the action id, logged, with the incident state captured at fire time.
- **A post-incident finding is mandatory** — the artifact chain re-entered after the fact, so the
  emergency path never becomes a hole in the record. (This is the same shape as `f:0191`'s lesson:
  the failure was never the urgency, it was work that never re-entered the chain.)

Anything **not** on the list still stops for a live decision — which is exactly the owner's own
framing, since he is present anyway.

⇒ Splits the original proposal cleanly in two, and they should probably be separate design notes:
1. **Autopilot** — unattended, low-stakes, `proposed→ready` only, adversarial auditor, deskcheck
   mandatory. (Refinements 1 and 2 above stand unchanged.)
2. **The emergency lever** — owner-present, pre-reviewed bounded action set, MFA-fired, mandatory
   post-incident finding. Not a blessing-delegation mechanism at all.

Conflating them was the orchestrator's error, not the owner's: they share an authentication
primitive (MFA from the phone) and nothing else. **Different risk, different gate, different note.**

### ⚑⚑ Owner proposal — SMART as the CHECKABLE form of the understanding-check

Verbatim: *"are you familiar with SMART goals? I have to read write them for my job's yearly check
in… but they could make sense here, if you can answer those few questions, based on our
conversation, then there is enough here, else, not enough."* (Specific · Measurable · Achievable ·
Relevant · Time-bound — the acronym is correct.)

**This is the answer to the crux.** The open question was: *what makes an understanding-check
checkable rather than vibes?* SMART supplies a **completeness predicate over the conversation** —
five fields that are either fillable from what was said or are not. Unfillable ⇒ not ready.

#### ⚑ It is not a foreign framework — it is already this repo's vocabulary, renamed

Each letter has an existing artifact home. That is what makes it cheap to adopt and hard to fake:

| SMART | already exists here as | source |
|---|---|---|
| **Specific** | *"a single coherent objective statable in one sentence"*; split when *"the objective needs an 'and'"* | graduate skill, session-sizing |
| **Measurable** | *"acceptance criteria that are **runnable** — a test passes, a file exists and parses, a command exits 0 — not 'looks good'"* | graduate skill |
| **Achievable** | **the acceptance-reachability check** — every §7 criterion buildable from §5 (`e7915c2`) — plus `session_budget: 1` | graduate skill |
| **Relevant** | `design_ref` — does it trace to a ratified note? — and §1.2 non-goals | build-plan front matter |
| **Time-bound** | `session_budget`, `cost.estimate`, and (for autopilot) **the stopping condition** | build-plan front matter |

⇒ A SMART statement is **the build plan's skeleton written early**, not extra ceremony. It is a
pre-flight rendering of §1 + §7 + §5, short enough to read on a phone.

#### ⚑ THE EMPIRICAL TEST — run it on this session's two candidate asks. It DISCRIMINATES.

The owner named two: *"even having spell check, or reinvent the `gf` binding."* Filling SMART from
the conversation as it actually stands:

**(a) The `gf` / reference standard — SMART FAILS at Achievable, correctly.**

| field | fillable from the conversation? |
|---|---|
| Specific | ✅ resolve `<type>:<name>[:<anchor>]`; a validator plus an editor action |
| Measurable | ✅ `scripts/check_refs.py` exits 0 over `docs/`; every typed ref resolves; `gf`/`K` resolve `dn:x`, `bp:108`, `::§10` |
| **Achievable** | ❌ **NO — four decisions are still open** (uniform vs typed-only-where-ambiguous · retrofit · whether to discourage bare line refs · journals-as-prose). The resolver hardcodes whichever answer is chosen, so it cannot be built yet. |
| Relevant | ⚠ traces to `owner-cockpit.md` — **a brainstorm, not a ratified note.** No `design_ref` exists. |
| Time-bound | ❌ unknown |

⚑ **The predicate rejects it — and rejects it for exactly the reason the orchestrator had already
identified independently** (*"four decisions before anything gets built"*). That is the strongest
evidence available that SMART has real discriminating power here rather than being a formality:
**two independent methods reached the same verdict.**

**(b) Spell-check — SMART plausibly PASSES.** Specific (spell-check `docs/**` prose); Measurable (a
script exits 0 / a dictionary-diff is empty); Achievable (a new script plus a gate leg — a scope a
reviewer holds in their head); Relevant (QoL, no design dependency); Time-bound (one session).
⇒ The two examples land on **opposite sides** of the same test. The predicate separates them.

#### ⚑ Where SMART is NOT sufficient — three gaps, all of which this repo already covers

Adopt it as *necessary*, never as *the whole gate*:

1. **SMART has no FALSIFIER.** §7 requires acceptance **and a named falsifier** — *what observation
   would prove this wrong*. Measurable ≠ falsifiable: a goal can be perfectly measurable with no
   designed disproof. This repo's epistemology (falsifiers, not proofs) is strictly stronger than
   SMART, so **SMART + falsifier**, always.
2. **SMART has no NON-GOALS.** "Relevant" says what it is *for*, never what it is *not*. `f:0150`:
   **wrong non-goals fail silently forever.** This is the most dangerous gap and the least
   auto-checkable — it stays owner-read.
3. ⚑ **SMART checks the GOAL, not the UNDERSTANDING.** The subtle one. An agent can emit a flawless
   SMART restatement of an ask it *misread*. Well-formedness is not comprehension.

#### The resolution — SMART is the FORM of a readback; the owner's recognition is the CONTENT

Gap 3 dissolves once the mechanism is stated properly. This is **closed-loop / readback-hearback**,
the technique aviation and medicine use for exactly this problem:

1. converse until the idea is formed;
2. the agent emits a **SMART statement** — five short fields, phone-readable;
3. the owner reads it and either **corrects** (the loop repeats — and a correction is *information*,
   the disagreement surfaces cheaply, before any work) or **recognises it as his own goal**;
4. **the MFA binds to `sha256(SMART statement)`** — Refinement 2, unchanged. Any edit invalidates it.
5. autopilot executes *that statement* and nothing else; it becomes the plan's §1/§7 seed.

The owner's *"once I believe you understand"* is therefore not vibes: it is a **structured readback
he confirms**, and the confirmed artifact is small, hashed, and binding. **The read is preserved,
shrunk to five fields, and made portable.**

⇒ Supersedes the crux as an open question. The Fable design pass has been sent this capsule.
