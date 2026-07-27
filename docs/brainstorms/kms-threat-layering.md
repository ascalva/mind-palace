# kms-threat-layering

## 2026-07-26T00:00:00Z

```capsule
topic: kms-threat-layering
date: 2026-07-26

⚑⚑ WHAT IS ALREADY RULED — DO NOT RE-DERIVE IT HERE: |
  The **decision** is durable in `docs/inbox/owner-questions.md` under **oq-0057** (RULED, committed
  `f52821e`): option **(c)**, the decrypt path split by consequence, with **KMS encryption context**
  as the mechanism; Vault `seal "awskms"` auto-unseal; the admin/use role split; root in the key
  policy but never authenticated; Phase 1 now, Phase 2 deferred. `docs/findings/finding-0232.md`
  carries the root-recovery defect. **This capsule adds none of that.** It recovers the *reasoning
  layer underneath* the ruling, which existed only in the session transcript.

  ⚑⚑ **THE LETTERING TRAP, restated because it inverts intent.** oq-0057's **(c)** = *split the
  decrypt path by consequence* (an active build). oq-0041's **(c)** = *keep the core plane parked*.
  Opposite things, same subject area, same letter. oq-0041's ratification question is **still open**.
  Never log a "(c)" answer against the wrong one.

seed: |
  Owner, verbatim (mis-addressed to oq-0055; it is oq-0041's subject): "show me how to set up and
  recommend me a good authentication app or someway to securely store the private key, we could also
  keep it on AWS under extremely priveleged access pattern, or even a kms key, vault already properly
  authenticates, the cloud can be the holder of the cryptographic key, if my laptop and phone die,
  the key is still secure, and I can even access AWS console from my phone, but the trick: we create
  you a user role such that you can't view it, and I also remove my own permission from my user
  'alberto' to view so you can't use my credentials, only root has access and I NEVER auth to root
  from anywhere"

  And, a message later: "or even put it any resources behind a vpn where only certain IPs can access,
  my laptop and phone, and through the tailnet network, so traffic never goes into the internet, it
  goes from one network to another"

⚑ THE FIRST CORRECTION — the proposed control was weaker than a property he already had: |
  He proposed *removing view permissions*. He does not need to: **KMS key material is
  non-exportable by construction.** There is no API that returns a CMK's bytes — not to an agent,
  not to `alberto`, not to root, not to AWS staff. What a policy grants is **use** (`kms:Decrypt`,
  `kms:Sign`), never **read**.

  ⇒ "create a role that can't view it" is the **default**, and it is strictly stronger than a
  permission that could be re-granted by accident. Same for the unseal key: Vault's `seal "awskms"`
  means **there is no unseal key to store anywhere**. The bottom turtle stops being "a secret on a
  laptop" and becomes "an IAM-authenticated call" — the blocker is *dissolved*, not relocated.

⚑⚑ THE HONEST LIMIT THAT REFRAMED THE WHOLE QUESTION: |
  Verbatim from the exchange: *"here's the uncomfortable truth: **I have Bash on this machine.**
  A role that can't view the key but can invoke `kms:Decrypt` gives me exactly what I'd want anyway
  — I'd just call decrypt."*

  **Non-exportability protects against key THEFT. It does nothing against key USE by whatever is
  already running on the box.** So the real boundary is not view-vs-not. It is:

      can this key be invoked WITHOUT A HUMAN PRESENT?

  …and the daemon *must* invoke it to boot unattended. That single reframing is what generates the
  (a)/(b)/(c) option set that oq-0057 then ruled on.
```

## THE THREAT LAYERS — the table, and the reason it is a table and not a stack

This is the load-bearing artifact of the exchange. Three controls were on the table; the instinct
is to read them as redundant defence-in-depth. **They are not. Each binds a different adversary,
and only one of them binds an agent that is already inside.**

| Layer | Stops | Does **not** stop |
|---|---|---|
| **Non-exportable KMS key** | Key *theft* — the bytes never exist outside AWS | Anyone who can **call** `Decrypt` |
| **Tailnet / VPC-endpoint restriction** | A stolen credential used **from somewhere else** | Anything running on the owner's Mac |
| **`aws:MultiFactorAuthPresent`** | Unattended automated use — **including the agent** | Nothing else; it is the only one that binds the agent |

⚑⚑ **Why row 3 is the only one that matters for the owner's stated worry.** The daemon runs on his
Mac. The Mac is on the tailnet. The agent runs on that Mac — so **the agent is inside the perimeter
by construction.** A tailnet restriction bounds an attacker in Bulgaria holding a stolen access key;
it does not bound the agent at all.

Verbatim, and it is the layering principle in one line: *"That's not an argument against it. It's an
argument for knowing which problem it solves."*

⇒ **The exercise is not "add layers". It is "name the adversary each layer binds."** A perimeter
control and an inside-the-perimeter control are not interchangeable quantities of security.

## Why (c), stated as the reason rather than the preference

> **(c) is the owner's own ruling in infrastructure form.** He ruled (oq-0051) that unretractable
> actions need his per-action permission and retractable ones do not. An MFA-gated KMS grant **is**
> that boundary — *enforced by AWS instead of by the agent's restraint*. That is the difference
> between a **policy** and a **control**.

The same sentence explains why the mechanism had to be encryption context rather than two key ARNs
and good habits: he asked for "a specific ops pattern", and a pattern only becomes a control when
KMS itself refuses on context mismatch.

## The tailnet corrections — three, all of them load-bearing

- **"Traffic never goes into the internet" is false as stated.** Tailscale is WireGuard: encrypted
  and authenticated end to end, and it **does** transit the public internet, possibly bouncing
  through a DERP relay when no direct path exists. The property that *is* true — and is the stronger
  one anyway — is that **nothing is exposed**: no public listener, no open inbound port, no attack
  surface to scan.
- **`aws:SourceIp` allowlists rot.** Home IPs change, cellular NAT rotates constantly, hotel wifi is
  random. Tailscale pins to a **stable device identity** rather than a mutable address — same
  intent, actually durable. (His instinct to say "certain IPs" and then immediately reach for the
  tailnet was itself the correction.)
- **The lockout gotcha:** once calls arrive via a VPC endpoint, `aws:SourceIp` stops matching —
  condition on **`aws:SourceVpce`** instead. People lock themselves out on exactly this.

⇒ Hence Phase 2 (VPC + PrivateLink + Tailscale subnet router) **deferred**: for a single
non-exportable key already restricted to one role, it buys marginal security against a threat the
key policy and CloudTrail already cover, **and adds a hard dependency where the daemon cannot boot
if Tailscale is down** — a real availability cost under launchd KeepAlive. The tailnet belongs on the
**interface** path (Ambassador, phone access) where NN-11 already puts it and the win is unambiguous.

## The two operational traps that would have bitten

- **Do not remove root from the KMS key policy.** Locking every principal out makes the key
  permanently unmanageable — only AWS Support can help. Root stays *in the policy* as the escape
  hatch; it is simply never authenticated.
- **"Only root has access" fights "I never auth to root."** If root is the sole administrator, the
  key can never be rotated or re-policied. Hence the split: a break-glass **admin** role (MFA,
  rare, owner) and a **use** role (`kms:Decrypt`, one key ARN, daemon).

## THE DEVICE-IDENTITY LAYER — and the nuance that breaks the obvious version

Owner asked (paraphrased from the same session) for a registry of *his* devices, where a new
computer must be registered. That opened a fourth layer:

- **The Secure Enclave does exactly what he described.** On Apple Silicon the SEP generates ECC
  P-256 keys whose private half **never leaves the enclave** — cannot be exported, backed up, or
  migrated to another Mac. Device-uniqueness by construction, not by policy. A key can also be bound
  to *presence* (Touch ID or passcode per use) and to the *current biometric enrollment*, so it
  self-invalidates if fingerprints change.
- ⚑ **But "just register Touch ID as a FIDO2 authenticator on AWS" is the wrong answer for this
  purpose: Apple platform passkeys sync through iCloud Keychain by default.** A synced credential is
  bound to the **Apple account**, not the **device** — the opposite of what he asked for. It proves
  *it's him*; it does not prove *it's this Mac*. ⇒ A quiet second argument for hardware keys: **a
  YubiKey is device-bound because it *is* the device.**
- **The registry he wants is already running and switched off:** Tailscale **device approval** +
  **tailnet lock**. Every tailnet node already has a unique device key; approval holds a new machine
  pending until admitted; tailnet lock requires devices to be signed by a node he trusts, so even a
  compromised coordination server cannot inject one. Zero new infrastructure.
- **IAM Roles Anywhere** is the device-bound AWS path (X.509 against a trust anchor → short-lived
  STS). The SEP is the right place for the private key — **but whether `aws_signing_helper` talks to
  the Secure Enclave cleanly was explicitly NOT asserted.** It supports PKCS#11 and certificate
  stores; SEP-backed macOS keys are the integration point to *verify*. Filed as a spike with an
  explicit "may not work, fall back to YubiKey" outcome.

⚑⚑ **Where device attestation lands in the table — and the one configuration that escapes it.**
Attestation is **row 2**: it stops a stolen credential being used *elsewhere*, and does nothing
about the agent, which runs on the attested device. **Except** when the SEP key requires
`userPresence`: a fingerprint **per signature** cannot be produced unattended. That is a **row 3**
control — and unlike the AWS MFA condition it is **local**, so it needs no network and no round trip.

⇒ The sharpest form of (c) may therefore not be "AWS MFA for effectors" at all, but:
**daemon-boot decrypts unattended via KMS; effector credentials require a Touch ID signature on this
machine.** Same boundary, enforced closer to the action, and it survives AWS being unreachable.
**This is oq-0057's open sub-decision — raised, not ruled.**

## The two hardware/identity corrections worth keeping

- **YubiKey form factor.** The "super small usb plug" he described is the **5 Nano** — designed to
  live *permanently inside* a port, with **no keyring hole**. For a keyring he wants the **5C NFC**
  (or 5 NFC for USB-A): keyring hole, crush- and water-resistant, no battery, no moving parts. **NFC
  matters for him specifically**, since he wants AWS console access from his phone. Buy 3; register
  **at least 2** on root (AWS allows 8) — one registered device is a lockout waiting to happen.
- **Cognito is the wrong door.** Cognito is *application* user identity. For his own AWS access he
  already has **IAM Identity Center — `alberto-sso`** (Phase-8 decisions); that plus FIDO2 *is* the
  front door. Cognito only becomes relevant if the email lane grows a real web app with users, and
  for a single-user system Tailscale + a local app beats it and matches NN-11.

## THE LAYER ABOVE EVERY LAYER — and it is why finding-0232 exists

**AWS root account recovery runs through email and phone.** If that mailbox is protected by weaker
factors than AWS root itself, then the entire chain — non-exportable key material, encryption-context
scoping, MFA conditions, hardware tokens — **resolves to the security of an email account.**

⚑ It is **invisible from inside the console**: every IAM/KMS/CloudTrail control reads as correctly
configured. Nothing in AWS's own tooling surfaces "your recovery mailbox is a consumer account with
SMS 2FA".

⚑ **Ordering is the actionable part and is easy to get backwards:** harden the recovery path
**before** registering hardware tokens on root, not after. Registering FIDO2 on root while the
recovery mailbox is soft adds a lock to a door with exposed hinges *and makes it feel finished*.

⚑ **It compounds with the email overhaul** (see the sibling capture): putting `ouroboros@ascalva.com`
on AWS makes the **domain and its DNS/registrar control plane** part of the trust chain too —
registrar takeover becomes a path to the mail identity and, via mail, potentially to account
recovery. One further hop that nobody has priced.

```capsule
open_questions:
  - ⚑ **Touch ID vs AWS MFA for the effector gate** — oq-0057's own recorded open sub-decision.
    Raised 2026-07-26, NOT ruled. The local gate is strictly better on availability (works with AWS
    unreachable) and strictly worse on portability (binds to one Mac).
  - ⚑ **Does `aws_signing_helper` integrate with the Secure Enclave?** Deliberately unasserted in the
    exchange. A **spike**, with a real possibility of "doesn't work cleanly, use a YubiKey" — and a
    live instance for the spike-as-a-typed-artifact capture.
  - **What happens to an MFA/Touch-ID-gated effector when the owner is unreachable?** ⚑ NOT DISCUSSED
    anywhere in the transcript. `[INFERENCE]` The whole point of the (c) split is that the
    consequential path *blocks* without a human — but nothing was said about queueing, expiry, or
    what a blocked effector owes the artifact chain. This is a real hole in the ruling as it stands.
  - **How the encryption-context split composes with Vault's own runtime-auth layer**
    (`dn-vault-runtime-auth`, the authoritative Vault note) — ⚑ NOT DISCUSSED. Two authorization
    layers are now in play for the same secrets and their relationship was never stated.
  - `[INFERENCE]` The table's row-3 argument generalizes past KMS: **any control that binds an agent
    must require something the agent cannot synthesize.** MFA-present and `userPresence` qualify;
    perimeter, attestation and non-exportability do not. That generalization was never stated in the
    exchange, but it is the reusable part and it applies directly to the effector tier.

connections:
  - docs/inbox/owner-questions.md              # oq-0057 (RULED) · oq-0041 (still open — opposite "(c)")
  - docs/findings/finding-0232.md              # the root-recovery gap; step 0 of the owner-build session
  - docs/design-notes/headless-daemon-secret-bootstrap.md   # `draft` — the four LOCAL options the KMS path supersedes
  - docs/design-notes/secrets-management-evolution.md       # `superseded` — but its "Option A: KMS auto-unseal (recommended)" is the path taken
  - docs/design-notes/vault-runtime-auth.md    # the authoritative Vault note
  - docs/brainstorms/spike-as-a-typed-artifact.md           # the SEP/`aws_signing_helper` question is one of its live instances
  - docs/brainstorms/email-architecture-aws-external-local-internal.md  # the sibling capture; the registrar hop compounds finding-0232
  - CONSTITUTION.md                            # NN-1 (sealed core zero egress) · NN-3 · NN-10 · NN-11
  - Phase-8 AWS decisions: acct 054942746160 · SSO `alberto-sso` · us-east-1

⚑ THE CONSTRAINT ANY BUILD MUST PIN (already in oq-0057, repeated because it is architectural): |
  **Sealed core has zero network egress (NN-1), and KMS is a network call.** The decrypt therefore
  CANNOT happen inside sealed core. It runs in `edge/`, or at bootstrap before `seal()`.
  ⚑ Note this is the *same structural constraint* the email architecture hits from the other side —
  a cloud agent is a network correspondent, so core cannot address it either. One boundary, two
  consequences.

next_steps:
  - Hold as a brainstorm. The ruling is already durable; this is the reasoning it rests on.
  - It feeds the design note owed by oq-0057 — the one superseding
    `dn-headless-daemon-secret-bootstrap`'s four LOCAL options with the KMS path. The threat table
    above is that note's §-1: state which adversary each layer binds *before* listing mechanisms.
  - The **owner-build session** running Phase 1 takes finding-0232's recovery hardening as step 0.
```
