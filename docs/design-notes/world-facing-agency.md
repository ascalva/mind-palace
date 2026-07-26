---
type: design-note
id: dn-world-facing-agency
track: track-g-effectors
status: draft            # draft → ratified → superseded.  draft→ratified is an OWNER-ONLY hand edit.
created: 2026-07-26
updated: 2026-07-26
links:
  - docs/brainstorms/acting-as-the-owner.md              # the warrant capsule — the owner's question, verbatim
  - docs/brainstorms/ambassador-thread-and-the-afk-loop.md
  - docs/brainstorms/public-diffusion-markers.md         # "pull the haystack, never broadcast the needle"
  - docs/brainstorms/prediction-market-sensor-fusion.md  # the calibration ledger that would earn a grant
  - docs/brainstorms/autopilot-mode.md                   # ruling 1 (role = catalog subset) · ruling 2 (the ε raise)
  - docs/brainstorms/ouroboros-email-identity.md         # precedent: the system's OWN outbound identity
  - docs/design-notes/ambassador-as-reasoning-agent.md   # RATIFIED — the owner-facing surface; constraints imported here
  - docs/design-notes/nervous-system-and-ambassador.md   # draft — §4 pins "a window and a switchboard, not a hand"
  - docs/design-notes/hands-and-the-effector-layer.md    # draft — the catalog design this note's axes amend
  - docs/findings/finding-0011.md                        # max reachable effector tier is NONE; nothing wired
  - docs/findings/finding-0109.md                        # the failure mode this note exists to prevent
  - docs/findings/finding-0218.md                        # actor identity is inexpressible in the catalog type
supersedes: null
superseded_by: null
warrant: null
---

# World-facing agency — the three senses of "as me", the non-impersonation bright line, and the amendment acting requires

> Filed by the chat agent as `draft` (chat-side protocol, §8). Ratification is a
> hand edit by the owner — no command performs it, and `gate-guard` denies any
> agent attempt (§10). `/graduate` refuses this note until `status: ratified`.

## 1. Purpose and scope

### 1.1 Purpose

The owner asked (2026-07-26, verbatim, `docs/brainstorms/acting-as-the-owner.md`): *"mind-palace
is the design of my brain, ouroboros is the instance of it, so can you navigate the world as me in
a secure and safe way?"* This note is the design-level answer. It does five things:

1. Fixes the **three-sense decomposition** of "as me" — deciding as the owner would, acting on his
   behalf, speaking as him — and makes the distinction *structural* (checkable by machinery), not
   interpretive.
2. Establishes **non-impersonation as a bright line excluded by kind**, and argues it as a safety
   mechanism, not only an ethical one.
3. Replaces the word "secure" with **four testable properties**: bounded by construction,
   attributable, revocable, and recourse-preserving for affected third parties.
4. Adds the **missing axes to the effect catalog**: social irreversibility (orthogonal to resource
   reversibility) and actor identity (finding-0218) — the third and fourth gaps found in the
   catalog in a single day (2026-07-26; the first two are recorded in
   `prediction-market-sensor-fusion.md` and `ouroboros-email-identity.md`).
5. **Names the constitutional amendment that acting requires and leaves the ruling to the owner.**
   The founding frame ("the mirror, not the oracle"; "one subject, at a distance" —
   `docs/book/chapters/01-philosophy.tex` §1.1/§1.3, grounded in `CONSTITUTION.md` §I and §III.2)
   currently reads against a system that acts. Shipping an acting capability without amending that
   frame is finding-0109's exact failure mode. §2.5 states the tension without smoothing it.

This note is (part of) the design pass `docs/tracks/track-g-effectors.md` demands at re-entry
("a design decision on WHETHER/HOW to wire the effectors"). Its answer to WHETHER splits by sense:
**read — yes, inside the current frame today; act — only after the §2.5 amendment is ruled;
speak-as — never, by kind.**

**Surface discipline — what this note deliberately does NOT own.** The ambassador design already
buried one note for double-minting (`ambassador-interpretation-and-flow.md`, superseded). The
owner↔system channel is owned by ratified `ambassador-as-reasoning-agent.md` and by
`nervous-system-and-ambassador.md` §4 (draft), which pins the Ambassador as *"a window and a
switchboard, not a hand"* — it delegates, never executes, and never holds worker capabilities.
Those constraints are **imported here unchanged**, not re-derived: whatever world-facing machinery
this note's ladder licenses, the Ambassador *narrates and proposes* it and is never the component
that performs it. This note covers the **system↔world surface** — the counterparty-facing side —
which no existing note specifies: the inbound-thread brainstorm (`ambassador-thread-and-the-afk-loop.md`)
covers owner↔system transport; the nervous-system note covers tamper response, verification, and
the owner-facing front door. Where this note touches the Ambassador's design space it amends by
reference (§3, consequence c), never by minting over it.

### 1.2 Non-goals — load-bearing (finding-0150); [INFERENCE]-tagged where inferred

1. **No concrete effector, hand, transport, or catalog entry is designed here.** The warrant
   capsule is explicit: "nothing graduatable, nothing to build" — this note's output is a
   distinction, a bright line, and an amendment question.
2. **Ratification of this note raises no effector ceiling and wires nothing.** Max reachable tier
   remains NONE (finding-0011) until a per-rung design note + plan lands. [INFERENCE] — inferred
   from finding-0011's terminal-resolution shape and the "ruling ≠ wire" discipline; the owner
   should confirm this is the intended gate order at ratification.
3. **The undisclosed speaking-as question is not reopened here.** It is excluded by kind (§2.3),
   with the reopening burden recorded under Parked decisions — not deferred to a tier.
4. **No legal instrument is created.** The limited-power-of-attorney analogue in §2.4 is a design
   metaphor for scope/disclosure/revocation; this note does not attempt to make grants legally
   binding or to settle actual liability, which is the owner's and a professional's domain (NN-7,
   as scoped by oq-0049). [INFERENCE]
5. **Disclosure is not claimed to eliminate risk.** It bounds *relationship* damage by preserving
   counterparty recourse; a disclosed delegate can still cause real, bounded harm inside its grant.
   Anyone reading this note as "disclosed ⇒ safe" is misreading it. [INFERENCE]
6. **The calibration ledger is not designed here.** `prediction-market-sensor-fusion.md` owns it;
   this note only names it as a precondition for any acting grant (§2.4).
7. **The owner↔system thread/channel is out of scope** — see surface discipline above.

## 2. Principles / decision

### 2.1 "As me" is three requests, and the distinction is structural

The danger lives in conflation: the safest request and the most dangerous share the phrase "as me".
The decomposition, with the invariant that **every world-facing proposal is classified as exactly
one sense before any gate sees it**:

| Sense | What it is | Egress? | Under whose identity? | Risk profile |
|---|---|---|---|---|
| **1 — deciding as he would** | modelling the owner's judgement | none | n/a — nothing leaves | internal only |
| **2 — acting on his behalf** | a bounded, disclosed, revocable grant | yes | **the system's own**, disclosed as a delegate | bounded, if §2.4 holds |
| **3 — speaking as him** | impersonation — borrowing identity and reputation | yes | **the owner's** | unbounded; the bound cannot be engineered |

Interrogating the decomposition rather than restating it: the boundary between (1) and (2) is not
intent — it is a **mechanical predicate**: *does any bit cross the trust boundary, and under whose
name?* No egress ⇒ sense 1. Egress under the system's attributable identity within a grant ⇒
sense 2. Egress under the owner's identity ⇒ sense 3. This matters because the first coordinate is
already policed structurally (NN-1 zero core egress; NN-2 only `edge/` touches the network, never
the vault) and the second coordinate *can* be, once actor identity is expressible in the effector
type — which today it is not (finding-0218). The decomposition is therefore not a taxonomy of
motives but a pair of checkable coordinates, which is the only kind of taxonomy this project
accepts (`structural-enforcement`: a property is only real when machinery proves it).

### 2.2 Sense 1 is the project's whole thesis — and evidence is not authority

Deciding-as-he-would is what the corpus is *for* (`CONSTITUTION.md` §I: a mirror onto the owner's
own mind). It needs no new permission and carries almost no external risk, because nothing leaves
the machine.

The invariant that keeps it safe as it improves: **the self-map is evidence about past judgements,
never authority for future ones.** More corpus and a better embedder make the *prediction* better;
they make the *authority* no more legitimate. Authority derives from a grant, and a grant comes
from the owner. The gap between "it knows what I would choose" and "it may commit me" is the entire
safety problem, and it does not close asymptotically — at no corpus size does prediction become
permission.

Sense 1's one real hazard is internal, and it should be named: a system that reasons over a corpus
containing its own predictions can launder "what he would decide" into apparent ground truth — the
ouroboros danger the manual states in ch. 1 §1.2. That hazard is owned by the provenance machinery,
not this note; it is cited here because "the system knows me, let it act" is exactly the drift this
invariant exists to refuse.

### 2.3 Sense 3 is a bright line, excluded by kind — and the exclusion is a *safety* mechanism

**The system never signs, sends, or speaks under the owner's identity toward any third party.**
Not tier 4, not "later", not behind a gate: excluded by kind, the way NN-12 excludes dialing any
number but the owner's — by making the capability inexpressible, not by trusting restraint.

The safety argument, stated so it cannot be mistaken for etiquette: **disclosure is what bounds
damage, because it preserves the counterparty's recourse.** A counterparty who knows they are
dealing with a delegate calibrates their trust to a delegate, can ask for the principal, and can
escalate to a human. Undisclosed action removes their ability to protect themselves — and that
removal, not any particular mistake, is what makes the blast radius unboundable. A sent message
believed to be from the owner cannot be unsent, and the damage lands on a *relationship*, not a
resource; there is no rollback path for trust (§2.6 makes this an axis). Liability follows the same
line: a disclosed delegate acting inside a bounded grant has a clean answer to "who did this"; an
undisclosed one does not.

Two consequences that make the line structural rather than aspirational:

- **The disclosure must bind in both directions.** Interrogating the bright line: disclosure that
  only shields the owner would be a liability dodge — "the bot did it" as plausible deniability.
  Within its grant, the delegate's disclosed acts are the *owner's* acts (that is what "on his
  behalf" means); outside its grant they are defects, disclosed as such, with the grant's audit
  trail (attestation, NN-3/NN-5 machinery) adjudicating which side of the line an act fell on.
  Disclosure bounds the counterparty's exposure; the grant bounds the owner's.
- **A channel that cannot carry structural disclosure is excluded from every grant.** If a
  counterparty surface renders a delegate indistinguishably from the principal — no sender
  distinction, disclosure strippable in transit — then on that channel disclosure does not deliver
  recourse, and the channel is out, whatever its convenience. Precedent already in the tree: the
  system's email identity is its *own* (`ouroboros-email-identity.md` — its own address, SES
  sandbox-restricted to the owner's verified address), never the owner's account.

### 2.4 Sense 2 is a grant — and "secure" means four testable properties

The closest human analogue is a **limited power of attorney**: scoped, disclosed, revocable,
auditable, and the counterparty knows it is dealing with a delegate. The analogue imports the
shape and *not* the enforcement: a real PoA is held together by courts standing outside both
parties, and here there is no outside enforcer for most acts. So enforcement must be structural —
the house move (stop trusting posture): the grant is a typed object consumed by the gate, the hand
is expressible iff cataloged (`ops/effect_catalog.py`), the model proposes and code acts (NN-3),
executed code is powerless (NN-4), and the credential for an irreversible act is minted per-action
and never held (the G6 pattern).

"Secure", replaced by what can be tested — a grant is well-formed iff all four hold:

1. **Bounded by construction** — the grant names a catalog subset (autopilot ruling 1: a role *is*
   a catalog subset), parameter bounds, a budget, and an expiry. Nothing outside the subset is
   expressible, so the bound needs no vigilance.
2. **Attributable** — every act carries the system's own identity outward (§2.3) and an attested
   record inward: which grant, which proposal, which hand, which parameters.
3. **Revocable** — revocation is unilateral, immediate, and does not depend on the delegate's
   cooperation (kill the grant object, the gate refuses; never "ask the agent to stop").
4. **Recourse-preserving** — an affected third party can discover they dealt with a delegate,
   reach the owner, and have the interaction repudiated or honored by a human. This is the one
   property measured from *outside* the system, which is why it, and not the other three, is the
   bright line's justification.

**Preconditions, both open today:** (a) the object that would *earn* a grant does not exist — the
calibration ledger (`prediction-market-sensor-fusion.md`) must exist and be consumed by the
authorization gate, so that a grant's scope tracks demonstrated judgement rather than enthusiasm;
(b) the §2.5 frame amendment must be ruled. Until both: sense 2 stays parked, and the max
reachable tier stays NONE (finding-0011). NN-7 does not block this parking's eventual release —
oq-0049 (owner, 2026-07-26) scoped NN-7 to the owner's own wellbeing, handing acting-effector
questions to NN-3/NN-4 and the effector gates, where this note picks them up.

### 2.5 The frame tension, stated without smoothing — and the amendment named

The manual opens with "The mirror, not the oracle" (§1.1) and "One subject, at a distance" (§1.3);
both rest on `CONSTITUTION.md` §I ("a mirror onto their own mind... a sealed, single-user
sandbox") and §III.2 ("a lens that surfaces patterns, never external truth"). **A mirror that acts
has stopped being a mirror.** Sense 1 sits fully inside the frame. Sense 2 strains it. Sense 3
breaks it.

Interrogating the frame rather than reciting it: the load-bearing content of "one subject" is not
that the system never *does* anything — it already curates, schedules, and proposes. It is that
everything the system touches belongs to **one consenting subject: the owner**. A world-facing act
changes the subject-count. A counterparty is a subject who never consented to being part of
anyone's experiment in delegated judgement — their data, their trust, and their recourse enter the
system's moral surface the moment the first outbound act lands. That is why sense 2 requires a
*constitutional* amendment and not a config flag: it revises the single-subject premise that the
entire privacy design (NN-2, NN-11) was derived under. And it is why a capability that contradicts
the ratified frame while shipping anyway — finding-0109's exact shape, a ratified note still
forbidding what is built and wired — is the single most likely way this goes wrong.

**The amendment, named for the owner to rule on (never to be performed by an agent — the
Constitution is a fixed point, NN-9, human-only):**

> **Proposed amendment — "the disclosed instrument".** Two edits, one ruling:
> (i) `CONSTITUTION.md` §III.2 gains a clause: *"When permitted to act beyond this sandbox, the
> system acts as a disclosed instrument of the owner — under its own identity, within an explicit,
> bounded, revocable grant — never as the owner, and never on the authority of its own
> predictions."*
> (ii) `docs/BUILD-SPEC.md` §3 gains an invariant (NN-13): *"World-facing action is
> disclosed-delegate-only. The system never signs, sends, or speaks under the owner's identity
> toward any third party. Prediction of the owner's judgement is never authority to commit the
> owner; authority derives solely from an explicit grant."*

**Both rulings are acceptable outcomes of this note.** (A) Amend: sense 2 becomes designable along
§2.7's ladder, gated by §2.4's preconditions. (B) Decline: the frame stands as written, this
note's rung 0 (read-only) remains the ceiling, and sense 2 stays excluded — the read rung needs no
amendment (§2.7). What is *not* acceptable is the unstated middle — acting capabilities accreting
under an unamended frame. The decision is the owner's; this note's job is to make it explicit.

### 2.6 The catalog is missing two axes, and this note supplies their design

The effect catalog models **resource reversibility** (`ops/effects.py` `ReversibilityClass`:
SENSING / REVERSIBLE / IRREVERSIBLE, an IntEnum whose order is load-bearing for the β filtration).
Necessary — and, for world-facing acts, not sufficient:

- **Axis: social irreversibility.** Most world-facing acts are *technically reversible and
  socially irreversible*: a sent message can be deleted and cannot be unsent; a cancelled order
  was still placed; a retracted offer was still made. Reversibility of the **resource** is not
  reversibility of the **relationship**. Under the current single axis, a deletable-after-send
  message is honestly classifiable as REVERSIBLE ("the owner can undo") and would inherit the
  weaker gate — the trap is live the day the first class-2 hand wires. Design decision: the
  catalog gains a second, orthogonal field (never a new member of the existing IntEnum — its
  order is the filtration index and must not be overloaded): `social_reversibility`, and **a hand
  gates at the *stricter* of its two axes**. A send-with-delete gates as irreversible. This is the
  third catalog gap found on 2026-07-26; per the warrant capsule, three arrivals in one day are a
  design-note-shaped problem, and this section is where the third one lands.
- **Axis: actor identity (finding-0218).** `ActuatorSpec` carries no identity/disclosure field —
  `send_email`'s parameters are `{to, subject, body}`; there is no representation of *as whom* an
  act is performed. The §2.3 bright line is therefore currently unenforceable at the catalog
  layer: "excluded by kind" requires the kind to exist in the type. Design decision: `ActuatorSpec`
  gains an actor-identity declaration pinned to the system's own identity, structurally incapable
  of expressing the owner's — the NN-12 pattern (the dialer cannot express any number but the
  owner's) transposed to identity. Direction is safe today (nothing wired, tier NONE), so this is
  a precondition for wiring, not an emergency.

Both axes amend the design space of `hands-and-the-effector-layer.md` (draft, agent-writable under
A8) §3's type and §8's audit — an amendment by addition, licensed in §3 below, warranted by
finding-0218.

### 2.7 The ladder — and why the bottom rung is most of the answer

"Navigating the world" is overwhelmingly *reading*: tracking, watching, researching, correlating,
summarising. Acting is the small dangerous tail. `public-diffusion-markers.md` reached the same
inversion independently on the same day ("pull the haystack, never broadcast the needle") — two
arrivals, one principle: **prefer pulling to pushing.** The ladder, each rung its own future note
and plan, no rung skippable:

- **Rung 0 — read-only world-facing capability in `edge/`.** Pull-based, quiet (the diffusion
  note's quietness constraints apply), no credential, no calibration ledger, no frame amendment:
  BUILD-SPEC §1.5 already includes the outbound research capability through the one-way airlock,
  and NN-2 as written already permits an `edge/` component that touches the network and never the
  vault. Retrieved content is untrusted OBSERVED data, never instruction (the probe-role
  discipline). This rung delivers the bulk of "navigate the world as me" at a fraction of the
  risk, and it is the honest first rung: it earns the calibration record sense 2 would later spend.
- **Rung 1 — disclosed acts, reversible on *both* axes.** Staging, drafting, holds — acts whose
  resource and relationship state can both be restored. Requires: the §2.5 amendment ruled (A),
  the calibration ledger consumed by the gate, both §2.6 axes landed, grants per §2.4.
- **Rung 2 — disclosed, socially irreversible acts.** Sends, purchases, bookings. Everything from
  rung 1 plus the full gate and per-action JIT credential (G6), gating at the stricter axis.
- **Rung ∅ — speaking as the owner.** Not a rung. Excluded by kind (§2.3).

### 2.8 Falsifiers — what would prove this note wrong (ratify falsifiers, not proofs)

- **F1 (central) — disclosure and utility can always coexist.** The note claims non-impersonation
  costs convenience, never a capability class: for every act worth granting, a disclosed form
  exists that retains the act's utility. Falsified by exhibiting a *wanted* act on a channel where
  disclosure is structurally impossible or destroys the act's point. The observation to watch for
  is pressure to "just this once" impersonate — that pressure is F1 firing, and the mandated
  response is reopening this note by supersession, never bending the line in a plan.
- **F2 — the decomposition is exhaustive and exclusive.** Falsified by a world-facing proposal the
  egress×identity classifier cannot place in exactly one sense (e.g. an act that is simultaneously
  a prediction and a commitment). One genuine hybrid breaks §2.1.
- **F3 — the read rung dominates the value.** Falsified if, after a sustained period of rung 0
  live, the owner's world-facing requests are predominantly *act*-requests rung 0 cannot serve
  (measurable from the oq/thread record). Then "most of the value is read-side" was wrong and the
  ladder's economics need re-arguing — though not its safety ordering.
- **F4 — the two-axis gate assigns no false weak gate.** Falsified by any cataloged hand whose
  social irreversibility exceeds its resource class and which the implemented gate nevertheless
  admits at the weaker tier. This one is a ratchet-shaped falsifier: it should become a property
  test the day the axes land.
- **F5 — recourse is real, not declared.** Falsified if a disclosed act's counterparty cannot, in
  practice, discover the delegation and reach the owner (e.g. disclosure present but illegible, or
  attribution present but dead-ended). Property 4 of §2.4 is only real when this path has been
  walked.

## 3. Consequences

- **a. An owner ruling** on the §2.5 amendment (A or B), at ratification of this note or as a
  recorded oq. Either outcome is coherent; the note is written to be buildable under both (rung 0
  is inside the current frame).
- **b. On ratification: one design pass for rung 0** (the read-only world-facing capability in
  `edge/`), which should absorb the probe-role design from `public-diffusion-markers.md` rather
  than mint a sibling. No build plan is licensed directly by this note.
- **c. An amendment edit to `hands-and-the-effector-layer.md`** (draft, A8 agent-writable) adding
  the §2.6 axes to its §3 type and §8 audit, warranted by finding-0218 — a plan whose write_scope
  names that note. `ops/effects.py`/`ops/effect_catalog.py` changes follow that amendment, not
  this note.
- **d. The ε staging inherits this note's semantics:** any per-role ceiling raise (autopilot
  ruling 2, staged per role/class per finding-0011's recommendation) classifies hands by the
  stricter of the two §2.6 axes, and no role's catalog subset may contain a hand whose actor
  identity is not the system's own.
- **e. Book debt:** if ruling (A) lands, ch. 1's frame (§1.1/§1.3) gains the disclosed-instrument
  clause and the subject-count argument; if (B), no book change. Scribe work either way follows
  the ruling, never precedes it.
- **f. NN-7 wording sweep (already owed under oq-0049)** proceeds independently; this note leans
  only on the ruled interpretation, not the pending wording fix.

## 4. Wiring & enablement

**How it wires:** this is a frame note — it designs no runnable capability, so there is no daemon
or CLI surface here. The connective tissue it obligates downstream (and which must be IN-SCOPE for
the rung-0 note, per the wiring-is-part-of-finishing rule): the rung-0 design note must specify
its config schema (`[world_read]`-style block), its daemon/CLI enqueue path, and its ON switch as
deliverables; the §2.6 axes must land in the catalog type *before* any class-2 hand wires.

**What it takes to flip it on:**
- (a) owner ratifies this note (hand edit, `draft → ratified`);
- (b) owner rules the §2.5 amendment question, A or B — recorded in `CONSTITUTION.md`/BUILD-SPEC
  by his hand if A, recorded as a declined ruling in this note's ledger if B;
- (c) rung 0 gets its own design note and, after that note's ratification, plans whose write_scope
  includes the enable path. Nothing in (a)–(c) raises ε; finding-0011 closes only when a live
  entry point reaches a ruled tier through the full control stack.

## Parked decisions

- **Undisclosed speaking-as the owner.** Default: **NO — excluded by kind, not parked as a tier**
  (§2.3); this row exists only to record the reopening burden. Re-entry: a dedicated design note
  whose §1.2 non-goals are argued rather than inferred, and whose burden is showing how a
  counterparty retains recourse — not how the system avoids mistakes.
- **Whether sense-2 acting is permitted at all.** Default: not yet — the blocker is not caution
  but the missing earning object (the calibration ledger) plus the unruled frame amendment.
  Re-entry: ledger exists and is consumed by the authorization gate, AND the §2.5 amendment is
  ruled (A).
- **Grant vocabulary and shape** (duration, budget units, per-channel scoping, renewal). Default:
  undesigned — deliberately, to avoid designing sense 2 before the amendment ruling. Re-entry:
  ruling (A) lands; the rung-1 note owns it.
- **Where the social-reversibility field lives** (a second enum field on `ActuatorSpec` vs a
  wrapper classification at the gate). Default: a second field on the spec, gate takes the
  stricter axis; never a new member of the existing IntEnum (its order is the load-bearing
  filtration index, `ops/effects.py:63-75`). Re-entry: the consequence-c amendment plan.
- **Who narrates world-facing activity to the owner.** Default: the Ambassador narrates and
  proposes, never performs — imported from its ratified note and `nervous-system-and-ambassador.md`
  §4. Re-entry: only via a superseding note over the ambassador surface (none proposed).

## Cross-references

- Warrant capsule: `docs/brainstorms/acting-as-the-owner.md` (owner's question verbatim; the
  three senses; the parked defaults this note carries forward)
- Frame: `CONSTITUTION.md` §I (`:11`), §III.2 (`:32`), §III self-check (`:40`);
  `docs/book/chapters/01-philosophy.tex` §1.1 "The mirror, not the oracle" (`:13-37`),
  §1.3 "One subject, at a distance" (`:61-78`)
- Non-negotiables cited where they bind: `docs/BUILD-SPEC.md` §3 — NN-1/NN-2 (§2.1, §2.7 rung 0),
  NN-3/NN-4 (§2.4), NN-5 (§2.3 audit trail), NN-7 as scoped by oq-0049 (§2.4),
  NN-9 (§2.5 — the amendment is owner-only), NN-11 (§2.5 — the privacy design the subject-count
  argument protects), NN-12 (§2.3, §2.6 — the bounded-by-construction precedent transposed);
  BUILD-SPEC §1.5 + §16 (the outbound research airlock rung 0 lives inside)
- Ambassador surface (imported constraints): `docs/design-notes/ambassador-as-reasoning-agent.md`
  (RATIFIED); `docs/design-notes/nervous-system-and-ambassador.md` §4 (draft — "a window and a
  switchboard, not a hand"); cautionary precedent `ambassador-interpretation-and-flow.md`
  (superseded)
- Effector machinery: `ops/effect_catalog.py` ("expressible iff cataloged"; `ActuatorSpec` fields;
  `send_email` params `{to,subject,body}`); `ops/effects.py:63-75` (`ReversibilityClass`,
  order-load-bearing); `docs/design-notes/hands-and-the-effector-layer.md` §3/§8 (draft — the
  amendment target); `docs/tracks/track-g-effectors.md` (deferred; this note is its re-entry
  design pass, in part)
- Rulings: `docs/brainstorms/autopilot-mode.md` ruling 1 (role = catalog subset) and ruling 2
  (ε raise, "yes, go for it" — intent, not a wire); `docs/inbox/owner-questions.md` oq-0049
  (NN-7 is wellbeing-scoped; sweep axis still owed)
- Findings: finding-0011 (tier NONE, nothing wired; update 2026-07-26); finding-0109 (the
  ratified-frame-vs-shipped-capability failure mode); finding-0150 (non-goals are load-bearing);
  finding-0218 (actor identity inexpressible in the catalog type — filed with this note)
- Kin brainstorms: `public-diffusion-markers.md` (pull-not-push; quietness; the probe role rung 0
  should absorb); `prediction-market-sensor-fusion.md` (calibration ledger; the "irreversible but
  bounded blast radius" gap — the second of the day's three); `ouroboros-email-identity.md` (the
  system's own outbound identity — §2.3's precedent; the first of the three)
