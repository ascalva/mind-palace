# the-identity-foundation

## 2026-07-27T22:40:00Z

```capsule
topic: the-identity-foundation
date: 2026-07-27
status: OWNER BRAINDUMP + orchestrator synthesis with VERIFIED provider facts.
        NOT designed, NOT authorized. Proton facts below are externally grounded (linked).
        Everything else is [INFERENCE].

seed (owner, verbatim): |
  "one the secure and well maintained email recovery, does something like proton mail work?
  and it would potentially help with creating two emails:
  - the root email, minimal use, true breakglass
  - the common email: what is used for billing, regular day-to-day admin-like requirements and tasks
  this security layer is the backbone, from which the domain ascalva.com depend on, from which
  emails using …@ascalva.com depend on, something like alberto@ascalva.com would be my new
  day-to-day personal email, of course different emails go to different inboxes, which can be
  managed via mail clients as well, my apple mail one might have my legacy email (that I have been
  wanting to migrate out of): ascalva@gmail.com,
  ouroboros can send me emails from ouroboros@ascalva.com
  this is a chain of security dependencies that are related and benefit from a well secured
  security foundation
  proton mail also offers vpn for actual personal use, drive for my relevant documents that need to
  be shared there, and MFA auth, and an uipgrade from apple passwords
  the point also of this project is to provide utility value to me, and peace of mind, ive never had
  peace of mind when it comes to my own digital space, this all seconds as a secure public identity
  in addition: the moment the system does provide real utility value, and can even create a
  profitable (in some way, loose for now) utility value, then that brings up the question of
  hardware upgrades that are more sustainable"
```

## ⚑⚑ THE ARCHITECTURE — three tiers, strictly acyclic

> ⚑ **Owner clarification (supersedes an orchestrator misread in this same capsule's first pass):**
> *"I meant we will have a `…@protonmail.com` address, that is the root, we will also have a
> independent proton email for normal admin operation, from that secure foundation, we are then (on
> aws side or proton) start minting emails, which rely on `ascalva.com` domain ownership, which is
> tied to the secure emails"*
>
> The orchestrator's first pass put the *admin* mailbox on `ascalva.com`. **Wrong** — both foundation
> mailboxes are provider-native, and `ascalva.com` addresses are a **third tier minted on top.**

| tier | address | account | depends on | role |
|---|---|---|---|---|
| **0 — root** | `…@protonmail.com` | its own, separate | ⚑ **nothing** | true breakglass, minimal use; recovery for tier 1 |
| **1 — admin** | `…@protonmail.com` | independent of tier 0 | tier 0 | billing, registrar login, AWS non-root, day-to-day admin; **holds `ascalva.com`** |
| **2 — identity** | `alberto@`, `ouroboros@ascalva.com` | minted on the domain | tier 1 (domain ownership) | personal + system identity, public surface |

⚑ **The property this has, and it is the one that matters: every edge points *downward*.** Tier 2
depends on tier 1, tier 1 depends on tier 0, tier 0 depends on nothing. **No cycles** — which is
exactly what `finding-0232` failed to find in any existing note, and what makes "the strongest link
is load-bearing on the weakest" stop being true.

### ⚑⚑ THE TRAP — tier 0 must have NO recovery email, only the recovery phrase

This is the one place the design can silently invert itself, and the failing choice is the
*default-looking* one. Proton offers recovery email/SMS on every account. Setting **tier 1 as tier 0's
recovery address** is the natural thing to do and it is fatal:

```
tier 0 ──recovers──> tier 1        ⚑ an UPWARD edge — the cycle is back
tier 1 ──recovers──> tier 0
```

⇒ Compromise tier 1 (the account used daily, for billing, exposed to every vendor) → reset tier 0 →
own everything. **The hierarchy inverts and the tier-0 hardening becomes decorative.**

⚑ **Therefore tier 0 is terminal: recovery phrase only, no recovery email, no recovery SMS.** It is
the root of the tree and a root has no parent. This is viable *precisely because* tier 0 is
minimal-use — it holds no history worth recovering, so the E2EE "reset without the phrase loses the
mail" property costs nothing there.

### ⚑ Which account holds what — login vs recovery are different questions

The high-value accounts should be *operated* from tier 1 and *recovered* from tier 0. That keeps tier
0 genuinely minimal-use while making takeover of anything require the offsite envelope:

| account | login / daily | recovery address |
|---|---|---|
| domain registrar (`ascalva.com`) | tier 1 | ⚑ tier 0 |
| AWS root | — (never used) | ⚑ tier 0 |
| AWS daily / IAM | tier 1 | tier 1 |
| billing, vendors | tier 1 | tier 1 |

⚑ `[INFERENCE]` The registrar is the subtle one: `ascalva.com` ownership is what tier 2 rests on, so
registrar takeover collapses tier 2 entirely. Its recovery belongs at tier 0 even though its login
lives at tier 1.

### ⚑ Cost — tier 0 can be FREE, and that is not a compromise

Verified: **2FA with U2F/FIDO2 security keys is available on Proton free accounts**, not gated to
paid. Tier 0 needs no custom domain, no storage, no VPN — only the ability to receive a message and
to be hardened with hardware keys.

⇒ **Tier 0 = free plan, fully hardened. Tier 1 = the paid plan** (Unlimited if VPN/Drive/Pass are
wanted; it is also the account that must carry `ascalva.com`, so the custom-domain allowance applies
there). The security of the foundation does not scale with spend.

## ⚑ VERIFIED — Proton clears the bar `finding-0232` actually set

`finding-0232`'s requirement is specific: the recovery mailbox must be protected by **at least** the
factors protecting AWS root — *"FIDO2, not SMS"* — and its own recovery path must not route through
anything weaker. Checked against the provider, not assumed:

| requirement | Proton | verdict |
|---|---|---|
| hardware-key 2FA (U2F/FIDO2, YubiKey) | supported; **up to 4 keys** per account | ✅ **clears it** — and 4 slots means both keys + spares |
| recovery not dependent on SMS | **recovery phrase** (12-word) is the data-recovery method; email/SMS recovery explicitly does *not* restore encrypted data | ✅ but see below |
| custom domain on `ascalva.com` | paid plans only — Mail Plus: 1 domain / 10 addresses · Unlimited: 3 domains / 15 addresses | ✅ |
| works with a Route53-hosted zone | Proton publishes an **AWS-specific** custom-domain guide | ✅ integration path exists |

### ⚑ The E2EE property, read correctly for a *breakglass* mailbox

Proton is end-to-end encrypted, so a password reset **without** the recovery phrase keeps the account
but loses the encrypted mail. That sounds alarming and is **nearly irrelevant here** — a breakglass
mailbox's job is *to receive a message*, not to hold history. It should contain almost nothing.

⇒ ⚑ **But it inverts what the critical secret is:** for the root mailbox the recovery phrase becomes
*the* single point of failure, replacing the password. That is a physical secret to protect — the
precise cost [[aws-as-the-authorization-spine]] flagged when it weighed "an offline-held recovery key"
against a quorum ceremony.

## ⚑⚑ THE ENVELOPE — one offsite location closes BOTH succession problems

The registry pass established that YubiKey #2, stored offsite, is the node-role succession path. This
pass adds a second item needing exactly the same treatment. They are the same envelope:

> **Offsite envelope:** { YubiKey #2 · tier-0 recovery phrase · tier-1 recovery phrase }

⇒ **One ceremony, one location, one thing to protect** — and it covers node-role re-registration
*and* both mailbox recoveries. `[INFERENCE]` This is a real simplification: independently-hard
succession problems collapse into one physical procedure, which is the difference between a plan the
owner will actually maintain and one he won't.

⚑ **Ceremony ordering detail that is easy to get wrong:** both YubiKeys must be enrolled on **both**
Proton accounts *before* key #2 leaves for the offsite location. A key enrolled later cannot be
enrolled remotely, and a key enrolled on only tier 1 cannot recover tier 0 — which is the whole
point of holding it. Proton allows up to 4 keys per account, so 2 keys × 2 accounts is comfortably
within budget.

## ⚑⚑ ORDERING — this changes what tomorrow's key ceremony may do

`finding-0232` is explicit and the ordering is *easy to get backwards*:

> *"harden the recovery path **before** registering hardware tokens on root, not after. Registering
> FIDO2 on root while the recovery mailbox is soft just adds a lock to a door whose hinges are
> exposed, and creates a false sense that the work is done."*

⇒ ⚑ **Tomorrow's ceremony has an unbuilt predecessor.** The correct order is:

> ⚑⚑ **CORRECTION (2026-07-27, verified): the AWS root email is the SIGN-IN IDENTITY, not a
> recovery field.** Changing it changes how root logs in. AWS sends a verification code to the
> **new** address and requires the current root password; changes take **up to 4 hours** to
> propagate. ⇒ **It is a swap, not an addition** — the instant it lands, `ascalva@gmail.com` has no
> AWS role. There is no "keep gmail as fallback" for root. ⚑ And tier 0 therefore becomes the AWS
> root *login*: losing it is losing root, not losing a recovery route.

> ⚑ **Owner state (2026-07-27):** *"`ascalva@gmail.com` will still exist, but it has currently been
> the only recovery method for AWS."* ⇒ `finding-0232`'s predicted exposure is **confirmed present**,
> and closing it is the highest-value act in this ceremony.

### TODAY — safe without the keys

1. **Tier 0** (free): create, strong unique password, ⚑ **TOTP 2FA now** as the interim factor.
2. Generate the recovery phrase and record it. ⚑ **Leave recovery email and SMS empty** (the trap).
3. **Tier 1** (free, independent account): TOTP, phrase, recovery → tier 0.
4. ⚑ **STOP — do not touch AWS.**

⚑ **Interim-window hygiene:** the tier-0 TOTP seed must not live anywhere tier 0 recovers, and
ideally not in anything `ascalva@gmail.com` recovers either. A standalone authenticator for ~24h is
sufficient; the YubiKeys replace it tomorrow.

### TOMORROW — once the keys are in hand

5. Enroll **both** YubiKeys on **both** accounts.
6. ⚑ Phrases + YubiKey #2 → **offsite envelope. THIS IS THE GATE** for everything below.
7. Swap the **AWS root email** → tier 0 (needs the root password; code goes to tier 0; allow 4h).
8. Register the YubiKeys on **AWS root** MFA — ⚑ **this hardens the registrar too.**
9. Transfer lock ON, auto-renew ON, **registrant contact → tier 1**.

### ⚑⚑ THE RULE THAT ORDERS ALL OF IT — overlap, never gap

**Do not leave a working recovery path until the replacement is sealed.** Between account creation
and the sealed envelope, tier 0 is a new account whose only recovery is a phrase on a desk. Making it
the AWS root login in that window means one mishap — lost phrase, forgotten password, dead device —
locks the owner out of AWS entirely, ⚑ *with gmail no longer a path back, because step 7 is a swap.*
Gmail today is imperfect but it **works**. The trade is only safe at the instant the replacement is
actually strong, which is step 6, not step 1.

⚑ **The one genuinely fragile interval is tonight:** the recovery phrases exist before the envelope
does. That is the only window in this plan where losing a piece of paper is unrecoverable, and it is
worth being deliberate about rather than discovering.
6. **Tier 2** (paid): personal Proton account, both keys, recovery → tier 0. Add `ascalva.com`.
7. ⚑ **The single DNS pass** — MX → Proton, SPF with both includes, two DKIM selectors, DMARC,
   subdomain MX → SES, plus the already-queued `rpId` / A-record / Tailscale DNS-01 items. **One
   deliberate pass; the MX decision is the irreversible-ish one.**
8. Blessing/ratification signing key — independent of all the above, can land whenever.

Doing (5) before (1)–(4) is the failure `finding-0232` was written to prevent. `[INFERENCE]` Steps
1–4 are owner acts of maybe an hour or two; the cost of getting the order wrong is that all the token
work is uncounted.

## ⚑ "GMAIL FULLY RETIRED" DOES NOT BLOCK THIS — but it draws a line that matters

The standing retirement is about **Ouroboros reading a third-party mailbox through an adapter**
(reports go to the exhaust lane + PushNotification, never email). It says nothing about **where the
owner's own mail lives**. Proton as Alberto's personal provider is *not* the retired category.

⚑ **The line it does draw:** the moment anything wants Ouroboros to *read* `alberto@ascalva.com`,
that is a third-party mailbox adapter and the retirement applies in full. Outbound
`ouroboros@ascalva.com` (first-party sender, own domain, own zone) stays the authorized shape.

⇒ Record this explicitly, because the two look identical from outside and only one is permitted.

## ⚑ THE ZONE-CHANGE DISCIPLINE — MX is now a FIFTH contender, not a drive-by

`ouroboros-email-identity.md:95-101` already ruled: **one deliberate DNS/identity pass, not four
drive-bys.** Four items contend for the `ascalva.com` zone — SES DKIM/SPF/DMARC, passkey `rpId`,
`ouroboros.ascalva.com` A record, `tailscale cert` DNS-01. **Proton MX + DKIM is a fifth**, and
pointing MX at Proton is not compatible with also sending via SES from the same domain without a
deliberate SPF/DMARC decision.

⇒ ⚑ This does **not** block the root mailbox — that is provider-native and touches no zone at all,
which is a second reason the split is the right first move. It blocks only `alberto@ascalva.com`,
which should ride the single planned pass.

## ⚑ "PEACE OF MIND" IS A REQUIREMENT, NOT A SENTIMENT — record it as one

> *"the point also of this project is to provide utility value to me, and peace of mind, ive never had
> peace of mind when it comes to my own digital space"*

⚑ Worth stating plainly because it **reorders the roadmap**. The repo has treated identity/custody as
*infrastructure for Ouroboros* — a precondition for KMS, effectors, autopilot. The seed says it is
also **a deliverable in its own right**, with a user (Alberto) and an outcome (peace of mind) that
does not depend on a single track landing.

⇒ `[INFERENCE]` That makes the identity layer the **first thing in this project to deliver standalone
value**, and it lands in days rather than waves. It should probably be sequenced accordingly rather
than as track-N infrastructure. It also reframes "secure public identity" as a *product* surface —
`ascalva.com`, a real address, a coherent presence — not a side effect.

## ⚑⚑ THE HYBRID IS FORCED, NOT CHOSEN — and the split line is human/machine

> Owner: *"I guess we could also even split it, so a hybrid approach? my PERSONAL email, every day
> personal email can be managed with proton mail, `alberto@ascalva.com`, but everything else is
> handled/minted through AWS"*

⚑ **Two verified external facts remove the choice:**

| fact | source | consequence |
|---|---|---|
| ⚑ **Amazon WorkMail is discontinued 2027-03-31** — *"After March 31, 2027, you will no longer be able to access Amazon WorkMail."* | AWS product page, fetched 2026-07-27 | the only AWS product that gives a human mailbox **dies in ~8 months** |
| ⚑ **SES has no POP/IMAP** — *"you can't use an email client such as Microsoft Outlook to receive incoming email"*; inbound goes to S3/SNS/Lambda | AWS SES docs | SES can never be an inbox; it is a **sender + an event source** |

⇒ **AWS cannot host `alberto@ascalva.com` as a real mailbox — not now (WorkMail is 8 months from
EOL) and not after (nothing replaces it).** The owner's stated requirement — *"different emails go to
different inboxes, which can be managed via mail clients as well"*, Apple Mail — requires IMAP.

⚑ **This retires the repo's oldest unanswered gate.** `ouroboros-email-identity.md:26-27` and
`email-architecture…:177-179` have carried *"SES vs WorkMail — unanswered empirical gate"* since
2026-07-20, flagged as something the design *"cannot be built past."* It is now answered by
elimination: **WorkMail is not a candidate at all.** ⇒ Delete the fork rather than resolve it.

### ⚑ Why the hybrid is the *right* shape and not merely the surviving one

The split lands exactly on the human/machine boundary, and each side gets what it actually needs:

| | needs | gets | the other option's "limitation" is… |
|---|---|---|---|
| **Alberto** (`alberto@ascalva.com`) | a mailbox — IMAP, Apple Mail, history, E2EE | **Proton** | SES's no-IMAP is **disqualifying** |
| **Ouroboros** (`ouroboros@…`) | **events**, not a mailbox — programmatic, first-party sender | **SES** → S3/Lambda | Proton's E2EE mailbox is **obstructive** |

⚑ A machine does not want an inbox; it wants a message-arrived event with the body in object storage.
That is precisely what SES inbound is, and it is *better* for Ouroboros than a mailbox would be.

### ⚑⚑ THE DNS CONSTRAINT — MX is per-domain, so the split must be by SUBDOMAIN

This is the part that must be decided before the single DNS pass, because it is not reversible
cheaply and it is where a naive hybrid breaks:

- **MX is one system per domain.** `ascalva.com` MX → Proton means SES **cannot** receive for
  `ascalva.com`. There is no "both."
- **Sending from both is fine.** SPF takes multiple `include:` (Proton + SES) within the 10-lookup
  limit; DKIM is per-selector so both coexist; DMARC is one policy for the domain.

⇒ **The shape that works:**

| record | points at | serves |
|---|---|---|
| `ascalva.com` **MX** | Proton | ⚑ `alberto@ascalva.com` — the human inbox |
| `ascalva.com` SPF | `include:` **both** Proton and SES | both may *send* as the domain |
| `ascalva.com` DKIM | two selectors | Proton-signed and SES-signed mail both validate |
| ⚑ `<sub>.ascalva.com` **MX** | SES | Ouroboros inbound → S3/Lambda, no mailbox |

⚑ **And the subdomain makes the Gmail-retirement rule STRUCTURAL rather than conventional.** The
standing rule is that Ouroboros must never read a third-party mailbox through an adapter. Under this
split it *cannot*: Alberto's mail is behind a different MX, a different provider, and credentials the
system does not hold. ⇒ **A policy becomes a topology.** That is the standard this repo holds
([[structural-enforcement]]) and the hybrid satisfies it by construction rather than by promise.

`[INFERENCE]` The subdomain is likely already contemplated — `ouroboros.ascalva.com` is one of the
four items already contending for the zone (`ouroboros-email-identity.md:95-101`), so this folds into
the planned pass rather than adding a fifth contender.

### ⚑ Consequence for the tiers — and only ONE account needs to be paid

If `alberto@ascalva.com` is a Proton mailbox, it needs the custom-domain allowance. **Where it lives
is a real choice**, and the cheap answer is also the better one:

| | account | plan | holds |
|---|---|---|---|
| tier 0 | root / breakglass | **free** | nothing; receives resets |
| tier 1 | admin / billing / registrar login | ⚑ **free** — needs no custom domain | provider-native address only |
| tier 2 | ⚑ personal — `alberto@ascalva.com` | **paid** (Unlimited if VPN/Drive/Pass wanted) | `ascalva.com` |

⚑ **Recommendation: keep personal mail in its own account, separate from tier 1 admin.** They have
opposite exposure profiles — `alberto@` is handed out widely and is a phishing target; the admin
identity recovers the registrar and AWS root and should be known to nobody. Sharing one login joins
them. Splitting also means **tier 1 needs no custom domain and can stay on the free plan**, so the
stricter design is also the cheaper one — only one paid subscription.

`[INFERENCE]` Hardware keys on all three accounts (2 keys × 3 accounts, within Proton's 4-key limit)
makes phishing of the address non-fatal regardless; the separation is defence in depth, not the only
control.

## ⚑⚑ THE REGISTRAR IS AWS — which answers `finding-0232` step 3, and creates a different problem

> Owner: *"`ascalva.com` domain is registered in AWS"*

### The good half — there is no extra hop to price

`finding-0232` treated the registrar as *"one further hop nobody has priced"* and asked (step 3)
whether it supports hardware 2FA. ⚑ **The answer is that it is zero hops, not one:** Route 53 Domains
is not a separate vendor with its own login — it *is* the AWS account. Hardening AWS root with the
YubiKeys **is** hardening the registrar. One control, not two, and it is already in the plan.

⇒ **`finding-0232` step 3 collapses into step 5.** That is a real simplification of tomorrow's
ceremony and should be recorded, because the finding currently implies a separate workstream.

### ⚑ The bad half — zero hops also means zero separation

| | consequence |
|---|---|
| AWS account **compromise** | simultaneously a **domain** compromise — no independent second opinion |
| AWS account **closure** | ⚑ *"Most domains will be deleted upon closure of your AWS account"* |
| AWS **billing failure / suspension** | domain does not renew; `alberto@ascalva.com` — the new primary personal identity — **dies with the infra account** |

⚑ Note this is **not a cycle** — the DAG still holds, because AWS recovery routes to tier 0
(`@protonmail.com`), which depends on nothing. The owner's architecture is sound. This is
**concentration**, a different defect: one account failure takes the domain, the DNS, the SES lane,
*and* the personal identity, all at once.

### ⚑⚑ THE TRAP — the domain's registrant contact must NOT be `@ascalva.com`

Same shape as the tier-0 recovery trap, same failure mode, and equally tempting once
`alberto@ascalva.com` exists and feels like the "real" address:

> If the registrant/admin contact for `ascalva.com` is `alberto@ascalva.com`, then every notice that
> matters — **expiry warnings, transfer-authorization requests, registrar-change confirmations** —
> is delivered to an address that **only exists while the domain does.**

⇒ The domain lapses, and the warnings about it were sent to an address that lapsed with it. ⚑ **The
registrant contact belongs on tier 1** (`@protonmail.com`), which depends on nothing downstream.

### ⚑ The principle both traps are instances of — worth stating once, in the design note

> **No identity may be reachable only through the thing it is meant to recover.**

| instance | wrong | right |
|---|---|---|
| tier 0 recovery | recovery email → tier 1 | ⚑ **none** — phrase only |
| AWS root recovery | `@ascalva.com` | tier 0 |
| domain registrant contact | `alberto@ascalva.com` | tier 1 |

`[INFERENCE]` This is the same defect class the repo keeps re-finding under other names — *"a claim
becomes true by being stated inside the artifact that benefits from it"* ([[the-unchecked-claim]]),
and the circularity clause in `finding-0269`. Naming it once as a **rule with a checklist** is more
durable than catching it a fourth time.

### Mitigations, cheapest-first

1. ⚑ **Transfer lock ON** and ⚑ **auto-renew ON** — free, one click each, and AWS's own guidance for
   production domains. Transfer lock sets `clientTransferProhibited`; it does not prevent closure but
   stops a third party moving the domain during the post-closure suspension window.
2. ⚑ **Registrant contact → tier 1**, per the trap above.
3. **Billing alarms → tier 1**, and a payment method that cannot silently expire. ⚑ Billing is now
   load-bearing for the owner's personal email address; that sentence is uncomfortable and is the
   point.
4. ~~A separate AWS account holding only the domain registration~~ ⚑ **OWNER RULED — DECLINED
   (2026-07-27):** *"I think second AWS account is a step too far for me, everything else I agree
   with."*

   ⚑ **The residual risk this leaves, stated plainly so it is a known acceptance and not an
   oversight:** domain, DNS, SES lane and the owner's personal identity share one AWS account's fate.
   Items 1–3 are therefore **not optional hygiene — they are the whole mitigation**, and their value
   rises accordingly: transfer lock and auto-renew are what stand between a billing lapse and losing
   `alberto@ascalva.com`. `[INFERENCE]` The judgement is defensible for a solo owner: the realistic
   threat is billing failure or accident, both of which items 1–3 address, rather than AWS closing
   the account adversarially. ⚑ Revisit only if the domain later carries something whose loss would
   be unrecoverable.

## PARKED — right thread, wrong timescale

> *"the moment the system does provide real utility value, and can even create a profitable … utility
> value, then that brings up the question of hardware upgrades that are more sustainable"*

Recorded, deliberately not designed. It is downstream of demonstrated utility, and the honest
sequencing is: identity layer → daily use → observed value → *then* the hardware question, which is
bounded today by NN-8 (≤2 resident models, ~20–24 GB). ⚑ Do not let it pull the security pass toward
speculative capacity planning.

## OPEN — owner rulings, not guesses

1. ⚑ **Which plan for tier 1?** Mail Plus (1 domain / 10 addresses) covers `ascalva.com` alone. The
   seed also names **VPN, Drive, Pass** — that is Unlimited. If probe addresses need a
   non-`ascalva.com` domain ([[email-probes-as-a-world-sensor]] requires exactly this), the 3-domain
   allowance decides it. (Tier 0 is free either way.)
2. ~~Where does tier 2 get minted — Proton or SES?~~ ⚑ **RESOLVED BY EXTERNAL FACT — see the
   hybrid section below. AWS cannot host a human mailbox, so the split is forced, not chosen.**
3. ~~Registrar for `ascalva.com`~~ ⚑ **ANSWERED (owner, 2026-07-27): it is AWS.** `finding-0232`
   step 3 is closed — hardening AWS root hardens the registrar. ⚑ **The finding should be updated**,
   since it currently implies a separate registrar workstream that does not exist. The *residual*
   question is concentration, not 2FA: **does the domain move to its own AWS account?**
4. **`ascalva@gmail.com` migration** — the seed calls it legacy and wants out. Migration order
   matters: it is likely still the recovery address on accounts nobody has enumerated. ⚑ Enumerate
   before retiring, or retiring it *creates* lockouts.
5. **Does Proton Pass replace Apple Passwords, or sit beside it?** The seed says "upgrade from"; a
   partial migration is usually worse than either endpoint.
