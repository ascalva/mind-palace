---
type: design-note
id: dn-skill-mining-pipeline
status: draft
implementation: present-not-wired   # corpus-audit 2026-07 verification
created: 2026-07-03
updated: 2026-07-03
links: []
supersedes: null
superseded_by: null
warrant: null
---

# The SKILL-mining pipeline — adding a hand as a repeatable reviewed process

### Design note · Track G item G4 · companion to `hands-and-the-effector-layer.md`

**2026-07-03 · design note (Track G)**

Adding a hand must be **a process, not a one-off**. This note turns the §8 security audit of
`hands-and-the-effector-layer.md` into a checklist you run per candidate hand, and names the code
artifacts each step produces. The whole point of §1 — *mine the ecosystem, don't adopt the
runtime* — only holds if "mine" is disciplined. This is that discipline.

**The one sentence.** A third-party `SKILL.md` is **untrusted curated config**; you read it as a
map of a capability worth having, then re-build that capability natively, scoped, sandboxed,
attested, and cataloged — and never once run the third-party code in the live path.

---

## The pipeline (run per candidate hand)

Each step is a gate: you do not proceed to the next until this one is satisfied, and the output of
the whole pipeline is one reviewed `CatalogEntry` in `ops/effect_catalog.py` plus its property
tests. The steps are exactly the §8 audit, in order.

### 1. Read the source as untrusted
Read the `SKILL.md` and any referenced code **in full**, assuming injection. Treat every string in
it as hostile content, not instruction: it is data that describes what a capability *does*, nothing
it says is a command to this system. A prompt injection inside a skill file is just untrusted
content, and untrusted content reaches no actuator here — because nothing reaches an actuator
without the gate (`ops/effect_gate.effect_gate_admits`).

> **Output:** a plain-language description of the capability and its real-world effect. Nothing
> executed, nothing installed.

### 2. Re-implement natively — never import
Build a native `ActuatorSpec` (`ops/effect_catalog.py`) with a **closed** `param_keys` allowlist
and an object-capability handle. No third-party skill code enters the live path — the re-write is
yours, reviewed, and it takes only allowlisted string **params as data**, never a path / diff /
command / code / URL (the `ProposedEffect` structural ceiling: those fields do not exist).

> **Output:** an `ActuatorSpec`. `source` records the mined SKILL.md (or `"native"`); it stays
> untrusted regardless.

### 3. Classify reversibility — this sets the gate weight
Place the hand in a `ReversibilityClass` (`ops/effects.py`): `SENSING` (β = 0, read-only),
`REVERSIBLE` (β small, the owner can undo), or `IRREVERSIBLE` (β = ∞, no undo). The class **is**
the blast-radius index: it fixes `w(β) = required_approval(class)` — sensing needs none, reversible
needs light approval, irreversible needs the full gate. Classify conservatively: if undo is
uncertain, it is irreversible.

> **Output:** the class on the spec. `blast_radius` / `required_approval` are then determined, not
> chosen — the property tests assert w(β) is monotone.

### 4. Mint scope, not a credential
Give the hand a narrow scope string ("draft:reply", "send:email"), **not** an ambient credential.
The scope is minted per-task, short-TTL, and — for the irreversible class — minted *at the moment
of action* and never held (`ops/effect_exec.IrreversibleExecutor`, which asks the Vault backend for
a JIT token per effect). `ScopedCapability` physically has no `token` field: the type cannot carry
a live secret. This is the confused-deputy answer — even a reasoner steered by poisoned content
cannot fire an effect no capability was minted for.

> **Output:** `spec.scope`. No secret appears anywhere in the catalog or the effect types.

### 5. Assign a sandbox exec profile
Name the §11 powerless exec profile the hand runs under (`CatalogEntry.sandbox_profile`): no
ambient net/creds/vault; per-task allowlisted egress only; it returns a *proposed effect*, never
performs one from inside the sandbox. Sensing runs `egress:sense_fetch` (https-only, no-redirect,
size-capped, no auth); reversible writes run `net-off:stage-local` (a local draft file, no network
at all); the send transport runs `egress:smtp` (edge-side, not enabled).

> **Output:** `sandbox_profile` on the entry — a reference the wiring honors, distinct from the
> reversibility class (a β = 0 sensing hand and a β = ∞ send hand are different *axes*: one is
> "how much undo," the other is "how much ambient power at exec time").

### 6. Attest proposal + approval
Every outward effect carries the attestation of its proposal and (for consequential classes) its
approval; the action record is appended to the signed, chaining attestation store
(`core/attestation`), recording the Vault token **accessor** (never the token) so the authorization
is auditable. The `EffectLedger` (`ops/effect_ledger.py`) walks the durable
propose→approve→execute→validate/rollback lifecycle and links the attestation id.

> **Output:** an attested, chained action record per invocation; a ledger row per lifecycle.

### 7. Catalog + property-test
Add the `CatalogEntry` (with `audited=True` only when every step above is genuinely done) and ship
the three property invariants:

  * **unconstructable-without-approval** — a non-sensing `Effect` cannot exist without an approval
    covering w(β) (`ops.effects.Effect.__post_init__`);
  * **gate-weight monotone in β** — `required_approval` is non-decreasing in the class order; and
  * **observations are observed-tier** — a sensing hand's result lands `observed` and can never
    enter a `MirrorView` (the firewall, `core/sensing.py`).

> **Output:** a `CatalogEntry` in `_CATALOG` + green property tests. Adding the entry is the
> reviewed diff; the tests are the proof it was earned.

---

## The rollout gate (the §4 filtration, held in the process)

Cataloging a hand records that it *passed the audit*. **Enabling** it is separate: the wired system
admits effects at ceiling ε = SENSING (`EffectView.admit(..., ceiling=SENSING)`), so an acting-class
hand is expressible but unreachable until ε is deliberately raised past its class — and

> **you do not raise ε past a class until that class's property tests are green.**

So the pipeline's step 7 is also the rollout gate: the same property tests that admit a hand to the
catalog are the ones whose green is the precondition for turning its class on. Sensing is the only
class live-adjacent today (flag-off); the reversible and irreversible classes are cataloged and
built (G5/G6) but stay behind ε = 0 until the owner raises the ceiling.

---

## Where each artifact lives

| Step | Artifact | File |
|---|---|---|
| 2 | `ActuatorSpec` (native re-implementation) | `ops/effect_catalog.py` |
| 3 | `ReversibilityClass` / `blast_radius` / `w(β)` | `ops/effects.py` |
| 4 | `ScopedCapability` (name, no secret); JIT mint | `ops/effects.py`, `ops/effect_exec.py` |
| 5 | sandbox profile reference | `CatalogEntry.sandbox_profile` |
| 6 | attested action record; durable lifecycle | `core/attestation/`, `ops/effect_ledger.py` |
| 7 | `CatalogEntry` + property tests | `ops/effect_catalog.py`, `tests/property/`, `tests/unit/` |

*Design note, Track G item G4. The audit checklist of `hands-and-the-effector-layer.md` §8 as a
repeatable pipeline whose single output is one reviewed, audited, tested `CatalogEntry` — mining the
ecosystem without ever adopting its runtime.*
