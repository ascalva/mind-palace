---
type: finding
id: finding-0232
status: open
created: 2026-07-26
updated: 2026-07-26
links:
  - docs/inbox/owner-questions.md          # oq-0041 — the secret-bootstrap ruling this sits under
  - docs/design-notes/headless-daemon-secret-bootstrap.md   # `draft` — the four LOCAL options
  - docs/design-notes/vault-runtime-auth.md
  - CONSTITUTION.md                         # NN-10 secrets outside code; NN-3 the model never holds secrets
ftype: spec-defect
origin_plan: orchestrator
route: orchestrator
resolution: null
---

# Every proposed key-custody design is bounded above by the security of the AWS **root account's
# recovery email**, and no design note mentions it. The strongest link is load-bearing on the weakest.

## What

The 2026-07-26 owner exchange settled the shape of secret custody: a KMS CMK (key material
non-exportable by construction), Vault `seal "awskms"` auto-unseal so **no unseal key exists to
store**, a split between an unattended `daemon-boot` decrypt path and an MFA-gated `effector` path,
and hardware FIDO2 on root. That design is sound, and the owner's stated posture — *"only root has
access and I NEVER auth to root from anywhere"* — is stronger than most production setups.

**It is also bounded above by something none of it controls.** AWS root account recovery runs
through the root user's **email address and phone number**. An attacker who controls that mailbox
can initiate a root password reset. If that mailbox is protected by weaker factors than the AWS
root itself, then the entire custody chain — non-exportable key material, encryption-context
scoping, MFA conditions, hardware tokens — resolves to *the security of an email account*.

⚑ **The gap is invisible from inside the console.** Every AWS-side control reads as correctly
configured. Nothing in IAM, KMS, or CloudTrail surfaces "your recovery mailbox is a consumer
account with SMS 2FA". It is the one link in the chain that AWS's own tooling cannot show you.

`[GROUNDED]` The repo's own record has the same blind spot: `dn-headless-daemon-secret-bootstrap`
(`draft`) proposes four custody mechanisms (System keychain with an ACL · an `ouroboros`-only file ·
a hybrid · a boot-time unseal helper) and `dn-secrets-management-evolution` recommends KMS
auto-unseal — and **not one of them mentions account recovery**. The threat model stops at the
machine boundary in every note we have.

## Why it matters

**1. It inverts the effort/benefit of everything else.** Hardware tokens, encryption-context
scoping and MFA conditions are real work. Every hour spent there is wasted if the recovery path
stays soft — not partially wasted, *entirely*, because an attacker takes the cheapest route and
never touches the hardened one.

**2. It is the same defect class this repo keeps finding.** finding-0222: *a note is not a control*.
finding-0011: a capability that is built but unwired is a claim, not a mechanism. Here: a custody
design that does not name its own weakest precondition is **a control with an unaudited bypass**.
The bypass is not in the code, which is exactly why no ratchet will ever catch it.

**3. It compounds with the email overhaul now under discussion.** The owner proposes
`ouroboros@ascalva.com` on AWS as a managed, cloud-resident mail identity. That makes the *domain*
(`ascalva.com`) and its DNS control plane part of the trust chain too — domain-registrar takeover
becomes a path to both the mail identity and, via mail, potentially to account recovery. The
registrar account needs the same hardening, and it is one further hop nobody has priced.

## The ask

Not a build. An **owner act**, and it is the first entry of the kind this exchange named:

1. Identify the AWS root account's current recovery email and phone.
2. Ensure that mailbox is protected by **at least** the factors protecting AWS root — FIDO2, not
   SMS — and that *its own* recovery path does not route through a weaker account.
3. Do the same for the **domain registrar** holding `ascalva.com`.
4. Record the resulting posture (not the addresses or secrets) so the design notes can stop
   assuming it.

⚑ **Ordering matters and is easy to get wrong:** harden the recovery path **before** registering
hardware tokens on root, not after. Registering FIDO2 on root while the recovery mailbox is soft
just adds a lock to a door whose hinges are exposed, and creates a false sense that the work is done.

## Re-entry condition

Nothing is parked and nothing is blocked — no plan depends on this. It gates *the value* of
oq-0041's KMS work rather than its buildability, which is precisely why it is easy to skip and
worth writing down: the KMS plan will look complete and correct without it.

Re-entry is **the owner-build session that runs the KMS setup**: this is step 0 of that session's
checklist, and the session must not proceed to token registration until it is done.

## Routing

`spec-defect` → **orchestrator**. It is a defect in the *threat model* the design notes share, not
in any code. The remedy is an owner act plus one paragraph added to
`dn-headless-daemon-secret-bootstrap` naming account recovery as an explicit precondition, so the
next reader of that note cannot inherit the same blind spot.
