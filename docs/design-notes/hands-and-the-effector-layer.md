---
type: design-note
id: dn-hands-and-the-effector-layer
status: draft
implementation: present-not-wired   # corpus-audit 2026-07 verification
created: 2026-07-01
updated: 2026-07-04
links: []
supersedes: null
superseded_by: null
warrant: null
---

# Hands and the Effector Layer — Track G
### Design note · reframed with the reasoning-complex mathematics (companions III–IV)

**2026-07-01 · design note (Track G)**

The Mind Palace is the hardened reasoning-and-memory core that OpenClaw-style systems are missing.
This note specifies how it grows **hands** — real-world action — without surrendering the discipline
that makes it trustworthy. The whole design is one sentence: **the reasoner proposes, the effector
disposes, and disposal only happens under a minted capability, a scoped credential, and (for
consequential effects) the gate.**

**The one rule.** A hand never bypasses the gate. Jarvis prepared, proposed, and waited for "do it."
That is not a limit on the aspiration — it *is* the aspiration, done correctly.

**Why this note is short (the formal reason).** Companion IV shows the system is a small number of
mathematical object *families*. The effector layer is not a new family — it is the **dual instance**
of one the system already has (family 1: typed labels that constrain flow). Ingestion constrains
*read*-flow into the store; effection constrains *action*-flow out into the world. Track G adds **no
new geometry** — one boundary operator symmetric to the one already there. That symmetry is why the
design is small and why its guarantees are inherited rather than invented.

---

## 1. The reframe: mine the ecosystem, don't adopt the runtime

OpenClaw's capabilities arrive as community `SKILL.md` files — natural-language *specifications* of
useful hands. Its danger is not that it has hands; it is that the same untrusted channel carries both
data and instructions, and action authority is unscoped (~20% of ClawHub skills carry injection /
tool-poisoning / hidden-payload risk; the ecosystem's own breaches are recent). Installing that
runtime against this vault would bolt on the exact failure mode Invariant 11, the gate, the powerless
sandbox, and the firewall exist to prevent.

**Conclusion: do not adopt the runtime. Mine the ecosystem.**

- **Read** the catalog as a map of what hands are worth having.
- **Re-implement** each desired hand as a *native* executable skill under the existing
  `skills-and-scope.md` model: a scoped `ToolSpec`, an object-capability handle, the §11 sandbox exec
  profile, gated for any outward action, tested.
- **Build outside** the live system; bring in by **PR review**; **never** live-install third-party
  code from ClawHub.

A third-party `SKILL.md` is **curated config** in this system's terms — human-curated, versioned,
untrusted-by-default, a *gated change, not a safe lever*. A prompt injection inside a skill file is
just untrusted content, and untrusted content does not reach actuators here, because *nothing*
reaches actuators without passing the gate.

---

## 2. The load-bearing distinction OpenClaw collapses: sense vs. act

| Class | Examples | Path | Risk |
|---|---|---|---|
| **Sensing hands** (read-only) | read calendar, inbox metadata, weather, Home-Assistant *state*, fetch a page | sandboxed fetch → de-identified → **`observed`-tier** derived view | low — cannot *do* anything; a new sensor |
| **Acting hands** (outward effect) | send email, post message, move money, set thermostat, run shell | **propose → human-approve → code-acts**; no agent holds the live credential | high — gated, always |

Sensing hands are just new sensors; the assistant tier + correlator already handle `observed` data
without letting it touch the authored mirror. Acting hands are the Phase-10 gate generalized from
"bounded config knobs" to "world effects" — same machine, wider domain. The model composes the effect
as a proposal artifact; the **owner** approves; **code** executes. This single split dissolves most of
the danger.

**The formal symmetry (companion IV, family 1).** The effector layer is the mirror image of the
ingestion boundary: ingestion is *read-only into the store* (`MirrorView`, authored-only); effects are
*write-only into the world* (`EffectView`, gated). The provenance firewall constrains one flow
direction (observed ↛ mirror); the effector boundary constrains the other (effect ↛ world without
approval). Both are **typed boundaries, not manifolds** — the same object family as the firewall, the
capability ceiling, and the airlock de-identification: *typed labels that constrain flow, enforced by
making the wrong flow unrepresentable.* This is why the design reuses the store's own boundary
discipline, reflected — and adds no new mathematics of its own.

---

## 3. The effector layer as a first-class type (symmetric to ingestion)

Effects are typed, scoped, attested, and **blast-radius-graduated** — the mirror image of the
provenance-classed ingestion boundary. An `Effect` carries: the actuator id, the scoped capability it
requires, a reversibility class, and the attestation of its proposal + approval. **Illegal states
unrepresentable:** a sensing-hand result type has no actuator field; an `Effect` cannot be constructed
without an approval reference for its reversibility class. This is the same structural move as
`MirrorView` (non-authored view untypable) and `ProposedChange` (no path field) — an illegal effect is
not "checked then refused," it is *unbuildable*.

```python
# OBJECT:     EffectView — the write-only-into-world boundary (family 1, dual of MirrorView)
# INVARIANT:  an Effect of irreversible class cannot exist without an approval reference
# ENFORCED:   structural — Effect.__post_init__ requires approval_ref for its reversibility class
@dataclass(frozen=True)
class Effect:
    actuator:      str                    # which hand (send_email, set_thermostat, ...)
    capability:    ScopedCapability        # minted per-task, short-TTL; NOT an ambient credential
    reversibility: ReversibilityClass      # SENSING | REVERSIBLE | IRREVERSIBLE  (an enum, not a str)
    proposal_att:  AttestationId           # the signed proposal
    approval_ref:  ApprovalRef | None       # REQUIRED for REVERSIBLE/IRREVERSIBLE; None only for SENSING
    # __post_init__: raise if reversibility != SENSING and approval_ref is None   → illegal state deleted
```

**An effect has no confidence of its own.** This is the load-bearing formal point, inherited straight
from companion III. The math keeps the *utility axis* $u$ separate from *adjudicator confidence* $c$
(and $c$ separate from *grounding* $g$) precisely so it cannot launder subjective worth as objective
certainty. The effector layer inherits that separation as a **hard rule**: a hand's worth-doing-ness
is $u$-like — subjective, owner-judged — and **must never be read off $c$**. An `Effect` may *cite* the
$c$ of the interpretation that motivated it, but its own gate weight comes from its reversibility class
and the owner's $u$-judgment, not from a confidence number. **A high-$c$ dream does not earn an
automatic action.** That collapse of $u$ into $c$ is exactly the flatterer/oracle failure the firewall
exists to prevent — now guarded at the actuator instead of the mirror.

**Reversibility classes (the rollout order):**

1. **Read-only sensing** — no approval; `observed`-tier; reversible by definition.
2. **Reversible writes** — create a draft, add a calendar hold, stage a file. Approval-light (owner
   can undo).
3. **Irreversible / external effects** — send, pay, post, actuate, shell. **Always human-approved,
   always attested, never an agent-held credential.** Hardest gate.

You build and roll out **in this order**; you do not get a class until the one below it is solid.

---

## 4. Blast radius as a metric filtration (companion IV, family 4) — the new math extension

The reversibility classes are not just an ordered list; they are a **metric** — a distance from the
reversible origin — and the graduated rollout is a **filtration by blast radius**, the exact same
shape as the confidence filtration the Dreamer uses (companion III §5.1).

Define a blast-radius pseudometric $\beta:\text{Effect}\to\mathbb{R}_{\ge0}$: $\beta=0$ for sensing
(reversible by definition), small for reversible writes (undo cost bounded), large/$\infty$ for
irreversible external effects (no undo). Then:

- **The gate weight is monotone in $\beta$.** Approval strength is a non-decreasing function of
  blast-radius distance: sensing needs none, reversible needs light approval, irreversible needs the
  full gate. Formally $\text{gate\_weight}(E)=w(\beta(E))$ with $w$ non-decreasing — the effector
  analogue of "confidence decays with derivational depth."
- **The rollout is a filtration.** $\text{Effects}_{\beta\le\epsilon}$ is the set of effects within
  blast radius $\epsilon$; you enable capabilities by *raising $\epsilon$*, starting at $\epsilon=0$
  (sensing only). "You do not get a class until the one below is solid" is: *do not raise $\epsilon$
  past a class until that class's property tests are green.* **[Engineering].**
- **This composes with the drift metric (family 4).** An effector that begins proposing
  higher-blast-radius effects than its history warrants is a *measurable* trajectory — appendable as a
  drift `Axis` (A2), exactly like a Dreamer bubble whose conductance is falling. Misbehavior at the
  actuator becomes a number, watched against a frozen anchor.

The blast-radius metric is why the graduated port order is not a convention but a **structural
discipline**: the same "distance-against-a-frozen-reference" mathematics that governs alignment drift
governs how far the hands are allowed to reach.

> **Cross-ref (quantitative backing):** `design-notes/effector-risk-computation.md` derives this
> port order from reversibility-as-reachability-contraction, adds the action-risk-vs-inaction-regret
> decomposition, and pins the load-bearing rule that bright lines are **constraints on the feasible
> set, never priced terms**. The current effector layer is already constraint-only (`ops/effects.py`,
> `ops/effect_gate.py`); the note's interior optimizer is parked (build plan PD1).

---

## 5. What changes, what holds

**Changes (small, because the pieces exist):**

- The Phase-10 gate generalizes from `ProposedChange` (config knobs) to `ProposedEffect` (world
  effects) — same propose→approve→execute→attest→rollback shape, wider domain, with the reversibility
  class selecting the approval weight (§4).
- The Vault scoped-token mechanism (already wired) mints the per-effect capability: a hand is a task
  needing a scoped capability for a bounded time — scope = "send one email to this address," not "hold
  the mail credential."
- A new `effectors/` surface in the **edge/assistant tier** (never Zone A), each effector a reviewed
  native skill with a sandbox exec profile.

**Holds (non-negotiable — the v1 boundaries, applied to hands):**

- No agent ever holds a live send/pay/exec credential.
- Every outward irreversible effect is human-gated and attested.
- The sealed core never egresses; hands live in the edge/assistant tier.
- Skills are curated, versioned, untrusted-by-default config — never live-installed from ClawHub.
- The firewall holds: a hand's observations are `observed`-tier and never touch the authored mirror.

**Two genuinely new problems hands introduce that read-only never had:**

1. **The confused deputy** — the effector acting for a reasoner that untrusted data steered. *Answered
   by per-task capability minting, never ambient authority:* even if a poisoned page convinces the
   reasoner to *want* to email credentials to attacker.com, no capability was minted for that egress,
   so the effect does not fire. Security comes from the effector being narrow, not the reasoner being
   trusted — that inversion is the entire ballgame.
2. **Irreversibility** — a sent email or spent dollar has no undo. *Answered by the blast-radius
   filtration (§4):* start at the reversible origin, gate the irreversible class fully, attest every
   outward effect, and mint the credential *at the moment of action* with a short TTL.

---

## 6. The gate generalized — a guarded transition system (companion IV, family 3)

The self-mod gate is already a guarded transition system (I12): $s'=\Delta\!\cdot\!s$ iff
$G_{\text{now}}(\Delta,s)$, else $s$; the model emits $\Delta$, **code** applies it, rejection is
identity. Hands generalize $\Delta$ from a config-knob change to a world effect:

$$G_{\text{effect}}(E,\,\text{world})\ =\ \textsf{proposed}(E)\ \wedge\ \textsf{approved}_{w(\beta(E))}(E)\ \wedge\ \textsf{scoped\_cap\_valid}(E)\ \wedge\ \textsf{attested}(E),$$
$$\text{world}'=\begin{cases}\text{apply}(E) & G_{\text{effect}}\\ \text{world} & \text{otherwise}.\end{cases}$$

Same shape, wider domain: the guard now carries the blast-radius-weighted approval $w(\beta(E))$ (§4)
and the scoped-capability check. Because it is the *same machine*, it inherits the FSM-verification
discipline — the effect gate's state space is small enough to enumerate, exactly like the config gate.
**[Engineering].** Nothing new to trust; one machine, wider inputs.

---

## 7. The Dreamer's model is what makes the hands act well (family 5 — the loop closes)

This is the point the whole system serves, stated precisely. An effector that tailors an action — write
the reply in the owner's voice, propose the calendar move that fits the owner's actual concerns — must
*read a model of the owner*. That read is a **`MirrorView`** (authored-only; the firewall holds even
here), and the **output is a proposal, never a sent artifact**. The tailoring is real; the boundary is
intact.

And the model it reads is exactly what the reasoning complex (companions III) builds: not cosine
clusters but a structured account — the bridges, the tensions, the robust themes, tracked over time. **A
hand acting on a shallow model does errands; a hand acting on the Dreamer's deep model does something
worth building.** This is why the engine must get strong *before* the hands are worth having, and why
Track H (the reasoning complex) is the precondition for Track G (the hands) delivering value. The loop:

```
   ingest (family 1,2) → reasoning complex 𝔎 (family 5) → Dreamer model (bridges/tensions/themes)
        ↓ read via MirrorView (authored-only, firewall)
   effector tailors a PROPOSAL (never a sent artifact)
        ↓ ProposedEffect
   gate G_effect (family 3) + blast-radius weight (family 4)  ──approve──►  code acts in the world
        ↓ observations return
   observed-tier (family 1) — never the authored mirror
```

The hands close the loop the Dreamer opens: the deep model is *for* acting well, and the acting returns
observations that never contaminate the ground. Every arrow is one of the five families; Track G invents
no sixth.

---

## 8. The security audit (every hand, before it ships)

A checklist, run per candidate hand, treating the source skill as **untrusted**:

1. **Read the source.** The `SKILL.md` and any referenced code, in full. Assume injection.
2. **Re-implement, don't import.** Native `ToolSpec` + object-capability handle; no third-party code in
   the live path.
3. **Classify reversibility** (§3) — this sets the gate weight $w(\beta)$ (§4).
4. **Mint scope, not credential.** A per-task scoped capability, short-TTL, minted *at the moment of
   action* — never ambient authority (defeats the confused deputy).
5. **Sandbox exec profile.** The §11 powerless sandbox: no ambient net/creds/vault; per-task
   allowlisted egress only; returns a proposed effect, never performs one.
6. **Attest proposal + approval.** The `Effect` carries both attestations; the action record is signed
   and chains (family 2) — an audit trail of every outward act.
7. **Catalog + test.** Add to the **effector catalog** and ship the property tests: the
   unconstructable-without-approval invariant (§3), the gate-weight-monotone-in-$\beta$ invariant (§4),
   and the firewall check (observations are `observed`-tier). Adding a hand is a **repeatable reviewed
   process** (the SKILL-mining pipeline), not a one-off.

---

## 9. Open questions

- **Approval UX.** Where does the owner approve — the Ambassador conversation, the edge dashboard, or a
  dedicated approval surface? *(Lean: the Ambassador for proposal + a one-tap approve, mirroring how it
  already surfaces dreams.)*
- **Standing approvals.** Should low-blast-radius reversible writes ever be pre-authorized for a session
  (e.g. "you may draft replies all afternoon")? *(Lean: time-boxed, reversible-class-only, never for
  irreversible — i.e. a bounded lift of $\epsilon$ (§4) with a hard ceiling below the irreversible
  class.)*
- **Batching.** How to approve a multi-step plan (book travel = search + hold + pay) without approving
  each atom, while keeping the irreversible atom (pay) individually gated. *(A plan is a filtration:
  auto-approve the $\beta\le\epsilon$ prefix, individually gate each atom above it.)*
- **Tailoring read.** Does an effector ever read the authored mirror to tailor an action (write in the
  owner's voice)? *(Yes — via `MirrorView`, authored-only; the output is a proposal, never a sent
  artifact. §7.)*

---

## 10. Track placement & build order

**Track G — the hands / effector layer.** Sits beside Track H (the reasoning complex) and consumes it:
Track H builds the deep model; Track G lets the system act on it. Build order follows the blast-radius
filtration (§4) — **you do not get a class until the one below is solid:**

| Step | Item | Blast radius | Depends on |
|---|---|---|---|
| G1 ✅ | The `Effect`/`EffectView` type + `ReversibilityClass` enum (illegal states unrepresentable) — `ops/effects.py` (2026-07-03) | — | — |
| G2 ✅ | `ProposedEffect` gate generalization (family 3) + blast-radius-weighted approval — `ops/effect_gate.py`, 72-state FSM (2026-07-03) | — | G1, Phase-10 gate |
| G3 ✅ | **Read-only sensing** effectors (class 1): sandboxed fetch → `observed`-tier — `core/sensing.py` + `edge/effectors/sensing.py`, flag-off (2026-07-03) | $\beta=0$ | G1, correlator |
| G4 ✅ | The effector catalog + the SKILL-mining pipeline doc (the §8 audit as a process) — `ops/effect_catalog.py`, `docs/design-notes/skill-mining-pipeline.md` (2026-07-04) | — | G1–G3 |
| G5 ✅ | **Reversible writes** (class 2): draft/hold/stage — approval-light, `MirrorView` tailoring, propose-never-send + durable `EffectLedger` — `core/effect_proposal.py`, `edge/effectors/writes.py`, `ops/effect_ledger.py` (2026-07-04) | small | G3 solid |
| G6 ✅ | **Irreversible / external** (class 3): send/pay/actuate — full gate, per-action JIT scoped credential, attested record — `ops/effect_exec.py` (2026-07-04) | large | G5 solid |
| G7 ✅ | Blast-radius drift `Axis` (family 4) — effector reach vs a frozen anchor, detection-only — `eval/effector_drift.py` (2026-07-04) | — | G3+, A1 |

> **G1–G3 built 2026-07-03; G4–G7 built 2026-07-04** (`docs/PROGRESS.md`). Track G is now
> structurally complete: the catalog + pipeline (G4), the reversible class with its `MirrorView`-
> tailored propose-never-send path and durable `EffectLedger` (G5), the irreversible class with a
> per-action JIT credential and attested record (G6), and the blast-radius reach `Axis` (G7).
> **The whole surface is still `[effectors] enabled=false`, and the wired ceiling is ε = SENSING**:
> the acting classes are cataloged, built, and property-tested, but a reversible or irreversible
> effect raises before it reaches any handoff (`EffectView.admit(..., ceiling=SENSING)`). Turning a
> class on is a separate, deliberate act — raising ε past it once its tests are green (§4), and only
> when Track H's model is deep enough to make its proposals worth tailoring (below).

**The precondition holds:** Track G class-1 sensing can proceed in parallel with Track H (it is $\beta=0$,
safe), but the *value* of the acting classes (G5–G6) is gated on Track H producing a model deep enough to
tailor actions worth proposing. Build the engine; then the hands are worth building.

*Design note, Track G. Reframed with companions III–IV: the effector layer is the dual instance of the
labelings/information-flow family (not a new geometry), blast radius is a metric filtration, the gate is
the existing guarded transition system, and the Dreamer's deep model is what the hands act on — the loop
the whole system was built to close.*
