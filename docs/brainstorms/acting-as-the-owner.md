# acting-as-the-owner

*"mind-palace is the design of my brain, ouroboros is the instance of it, so can you navigate the
world as me in a secure and safe way?"* — the ε raise's terminal ambition, stated plainly for the
first time. The honest answer is not yes or no; it is that **"as me" names three different things
with wildly different safety profiles**, and that one of them is in tension with the project's own
founding philosophy.

## 2026-07-26T15:55:00Z

```capsule
topic: acting-as-the-owner
date: 2026-07-26

decisions:
  - THE QUESTION (owner, 2026-07-26, verbatim): "after all, mind-palace is the design of of my brain,
    ouroboros is the instance of it, so can you navigate the world as me in a secure and safe way?"
    ⇒ Arrived at the end of a chain in one sitting: the overlay rename (instance identity) -> the legal
    sibling (a second instance) -> prediction markets (earning the right to act) -> this. That ordering
    is not accidental; each step was about identity or entitlement.
  - ⚑ "AS ME" IS THREE DIFFERENT REQUESTS AND THEY MUST NEVER BE CONFLATED. Conflating them is where all
    the danger lives, because the safest and the most dangerous share a phrase:
      (1) DECIDING AS YOU WOULD -- modelling your judgement. This is what the corpus IS FOR, it is
          already the project's whole thesis, and it carries almost no external risk because nothing
          leaves the machine.
      (2) ACTING ON YOUR BEHALF -- a bounded delegated grant, disclosed. Closest analogue is a limited
          power of attorney: scoped, revocable, auditable, and the counterparty knows it is a delegate.
      (3) SPEAKING AS YOU -- impersonation. Borrows your identity and reputation rather than your
          preferences. ⚑ This is the one with unbounded blast radius, and the bound cannot be
          engineered: a message believed to be from you cannot be unsent, and the damage is to a
          relationship, not to a resource.
  - ⚑ NON-IMPERSONATION SHOULD BE A BRIGHT LINE, and it is a SAFETY mechanism, not only an ethical one.
    If the system acts, it acts as *the system acting for you*, disclosed -- never as you. Disclosure
    bounds damage structurally, because a counterparty who knows they are talking to a delegate
    calibrates their trust accordingly and can escalate to you. Undisclosed action removes their ability
    to protect themselves, which is exactly the property that makes it unboundable. This is the same
    shape as the existing non-negotiables: make the property physical rather than trusting posture.
  - ⚑ THE TENSION WITH THE PROJECT'S OWN PHILOSOPHY, WHICH THE OWNER SHOULD SEE STATED. The manual's
    Chapter 1 opens with "The mirror, not the oracle", and §1.3 is "One subject, at a distance" -- the
    distance is deliberate and load-bearing. A mirror that begins acting in the world has stopped being
    a mirror. Request (1) above is fully inside the mirror framing; (2) strains it; (3) breaks it. This
    is not an argument against acting -- it is an argument that acting requires an EXPLICIT amendment to
    the founding frame rather than an incremental flag flip, because the frame currently says the
    opposite. A capability that contradicts a ratified frame while shipping anyway is finding-0109's
    exact failure mode, and it is the most likely way this goes wrong.
  - ⚑ THE SELF-MAP IS EVIDENCE ABOUT PAST JUDGEMENTS, NOT AUTHORITY FOR FUTURE ONES. "It knows how I
    think" licenses a *prediction* of what you would prefer. It does not license *committing you*. The
    gap between those two is the entire safety problem, and it does not close with more corpus or a
    better embedder -- more data makes the prediction better and the authority no more legitimate.
    Authority comes from a grant, and a grant comes from you.
  - ⚑ MOST OF THE VALUE IS ON THE READ SIDE, AND THE READ SIDE NEEDS ALMOST NO TRUST. "Navigating the
    world" is overwhelmingly reading: tracking, watching, researching, noticing, correlating,
    summarising. Acting -- buying, sending, booking, transacting -- is the small dangerous tail. This is
    the SAME inversion `public-diffusion-markers.md` already arrived at from the other direction ("pull
    the haystack, never broadcast the needle"), which makes it two independent arrivals at one
    principle: PREFER PULLING TO PUSHING. A read-only world-facing instance would deliver most of what
    was asked for at a fraction of the risk, and it is buildable inside `edge/` under NN-2 today.

parked:
  - decision: whether the system may ever speak AS the owner (undisclosed)
    default: NO -- a bright line, not a tier. Not "tier 4, later": excluded by kind.
    re_entry: none proposed. If the owner wants to reopen it, it needs its own design note whose §1.2
      non-goals are argued rather than inferred, and the burden is showing how a counterparty retains
      recourse -- not how the system avoids mistakes.
  - decision: whether "acting on your behalf, disclosed" is permitted at all
    default: not yet, and the blocker is NOT caution -- it is that the object which would EARN the grant
      does not exist. See the calibration ledger in `prediction-market-sensor-fusion.md`. Today the max
      reachable effector tier is NONE with nothing wired (finding-0011).
    re_entry: a calibration ledger exists, is consumed by the authorization gate, and the frame tension
      above has been resolved by an explicit amendment rather than ignored.

open_questions:
  - ⚑ A THIRD MISSING AXIS IN THE EFFECT CATALOG, distinct from the two already noted. The catalog models
    technical reversibility (Track G: reversible writes propose-never-send; irreversible needs JIT
    credentials). But most world-facing acts are TECHNICALLY REVERSIBLE AND SOCIALLY IRREVERSIBLE -- a
    sent message can be deleted and cannot be unsent; a cancelled order was still placed. Reversibility
    of the RESOURCE is not reversibility of the RELATIONSHIP. So the catalog's axis is necessary and not
    sufficient, and this is now the THIRD gap found in it today (with "irreversible but bounded blast
    radius" from the email and market notes). Three arrivals in one session is a design-note-shaped
    problem, not three findings.
  - Does the Ambassador already own this question? `ambassador-as-reasoning-agent.md` is ratified and the
    Ambassador is explicitly the outward face. If acting-in-the-world belongs to any existing role it is
    that one, and this may be an amendment rather than a new frame. ⚑ READ IT BEFORE DESIGNING -- the
    same warning the thread capture carries, for the same reason.
  - What does "secure" mean here, concretely? Not encryption. The owner's word probably means: bounded
    by construction, attributable, revocable, and with recourse for a third party who is affected. Those
    four are testable properties; "secure" is not. Worth pinning the vocabulary before any design.
  - Who is liable? A disclosed delegate acting within a bounded grant has a clean answer; an undisclosed
    one does not. This is the question that makes non-impersonation load-bearing rather than fastidious.

next_steps:
  - Nothing graduatable, nothing to build. The output of this capsule is a DISTINCTION (the three
    senses of "as me") and a BRIGHT LINE (non-impersonation), both of which should survive into whatever
    design note eventually owns this.
  - READ FIRST, as with the thread: `ambassador-as-reasoning-agent.md` (ratified),
    `nervous-system-and-ambassador.md` (draft), `ouroboros-principal.md`. The odds are good that the
    role and its constraints are already specified and this is an amendment.
  - THE CHEAP, HIGH-VALUE MOVE THAT NEEDS NO NEW TRUST: a read-only world-facing capability in `edge/`.
    It delivers the bulk of "navigate the world as me", is inside NN-2 as written, needs no credential,
    no calibration ledger, and no frame amendment. It is also the honest first rung of the ladder.
  - THE FRAME QUESTION IS OWNER-LEVEL AND SHOULD BE ASKED EXPLICITLY, not decided by drift: does
    "the mirror, not the oracle" still hold if the mirror acts? An answer either way is fine; an
    unstated answer is finding-0109 again.

references:
  - docs/book/chapters/01-philosophy.tex             # §1.1 "The mirror, not the oracle" · §1.3 "One subject, at a distance"
  - docs/design-notes/ambassador-as-reasoning-agent.md   # RATIFIED — the outward face; read before designing
  - docs/design-notes/ouroboros-principal.md         # who the instance IS
  - docs/brainstorms/public-diffusion-markers.md     # "pull the haystack, never broadcast the needle"
  - docs/brainstorms/prediction-market-sensor-fusion.md  # the calibration ledger that would earn a grant
  - docs/brainstorms/ambassador-thread-and-the-afk-loop.md  # the return path; same read-first warning
  - docs/findings/finding-0011.md                    # effector tier NONE, nothing wired
  - docs/findings/finding-0109.md                    # a ratified frame forbidding what ships anyway
```
