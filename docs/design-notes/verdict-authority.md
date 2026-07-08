---
type: design-note
id: dn-verdict-authority
status: draft
implementation: built-wired   # corpus-audit 2026-07 verification
created: 2026-07-04
updated: 2026-07-04
links: []
supersedes: null
superseded_by: null
warrant: null
---

# Verdict Authority — Owner-in-the-Loop Authentication

**Status:** DRAFT — pending codebase reconciliation and owner ratification
**Origin:** Design dialogue, July 2026
**Boundary:** Inbound channel — verdict authorization. Governed by the sacred-
boundary principle (`the-sacred-boundary.md`): owner verdicts are sacred, and
sanctity is achieved by making forgery infeasible rather than by trusting the
acceptor.
**Reconciles with:** `docs/research/security-planes.md` (which already records the
TOTP-wrong / Ed25519 direction — this is the fuller treatment),
`ambassador-as-reasoning-agent.md`, `docs/audits/prompt-integrity-audit.md`
(Threat B).

---

## 1. Problem

The owner is unavoidably in the loop to authorize interpretation verdicts
(adopt / reject / supersede / promote). The authorization must be easy for the
owner to produce and infeasible for any other person **or system component** to
produce. The mechanism sits at the interface between the Ambassador and the
owner.

## 2. Why TOTP is the wrong primitive

Two independent defects:

1. **Symmetric.** Whatever component verifies a TOTP code must hold the shared
   seed, and holding the seed *is* the ability to generate valid codes. The
   acceptor becomes a component that can forge owner verdicts — directly
   violating "infeasible for any other system to authorize."
2. **Authenticates a moment, not a message.** A TOTP code attests only that
   someone with the secret was present at time *t*; it does not bind to *which*
   verdict was approved. A compromised Ambassador can take a code entered for
   verdict A and staple it to verdict B — verification still passes, because it
   checks time and secret, not payload. The authorization is replayable across
   verdicts.

## 3. Correct primitive

An **Ed25519 signature over the canonical serialization of the verdict**. The
signed payload commits to, at minimum:

- the insight / cluster identifier the verdict applies to;
- the verdict category;
- a **monotonic sequence number**;
- a timestamp.

Properties:

- **Asymmetric** → the acceptor holds only the public key and *cannot forge*,
  even if fully compromised. This is the capability-dissolution test passing: the
  verifier is no longer a forger.
- **Content-bound** → the signature is not replayable onto a different verdict.
- **Non-repudiable** → each verdict carries a durable, owner-attributable
  artifact.

This is the same primitive family already used for attestation and named in the
prompt-integrity audit as the Threat B defense set (`constitution_fingerprint`,
append-only SQLite, Ed25519 signing). Verdict forgery **is** a Threat B event —
tampering with a governing signal — so it takes the Threat B toolkit, not a
possession proof.

## 4. Ambassador degrades to transport

With signing at the owner boundary, the Ambassador is transport and never
verifier. A compromised Ambassador can **drop or reorder** verdicts (a liveness /
censorship failure) but can **never forge** one (integrity is preserved). Signed
monotonic sequence numbers make even censorship **detectable**: a gap in the
sequence is visible to any later auditor. This is the correct, bounded
degradation mode.

## 5. Where MFA re-enters

The owner's multi-factor instinct is right, one level in: it protects **custody
of the signing key**, not the authorization itself. Preferred form on the
existing hardware:

- the owner private key lives in the Secure Enclave or a FIDO2 / PIV hardware
  token;
- "apply verdict" is a **hardware-gated signature**: physical touch + PIN.

Something-you-have (the token) plus something-you-know (the PIN) protect the key;
the key produces the attributable artifact. This yields payload-binding and
non-repudiation on top of the two factors — properties TOTP cannot provide.

## 6. Boundary property: auto-optimization over verdicts is a separate gate

Verdicts feed tuning through the owner's hand only. Auto-optimizing system
parameters directly over the verdict stream is optimization over the alignment
objective and therefore self-modification — it requires its own gate, distinct
from verdict authorization itself. (Sacred-boundary property 4:
un-purchasable by expected value.)

## 7. Open question (requires reading the code)

- **Q4.** What is the current verdict-authorization mechanism in code? Is
  anything TOTP-shaped already present? Cite. Locate the Ambassador↔owner
  interface (`path:line`) and identify the exact insertion point for Ed25519
  verdict signing + monotonic sequence numbers. Confirm reuse of the existing
  attestation-signing code rather than a parallel implementation.

## 8. Reconciliation

The **verdict store** this authenticates is recorded in
`docs/research/security-planes.md` §6 (the verdict-store inbox; owner-verdict
promotion) and, concretely, `live-adoption-and-longitudinal-harness.md` §3 (L2 —
the append-only `claim_verdicts` store). Those record the *store*; this note adds
the **authentication** the plain schema lacked — Ed25519 over the canonical payload,
the monotonic-sequence-number requirement, the payload-binding argument, and the
Ambassador-as-transport degradation model. This is an **extension**, so
cross-reference; no existing text conflicts.

**Correction (build plan R4):** an earlier draft said `security-planes.md` already
records the "TOTP-wrong / Ed25519 direction." It does not — it records the verdict
store (§6) and Ed25519-for-integrity (§5), but no TOTP argument; the TOTP-vs-Ed25519
reasoning is original to this note. Built: `core/verdict/`, `core/stores/verdicts.py`.
