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
