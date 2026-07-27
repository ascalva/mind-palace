# aws-as-the-outer-plane

## 2026-07-27T17:16:00Z

```capsule
topic: aws-as-the-outer-plane
date: 2026-07-27

seed (owner, verbatim, two threads): |
  (a) "the scheduler can also schedule agents in aws with the appropriate context, prompt, and
      constraints to perform cloud operations"
  (b) "what more can we do with aws? like not even ouroboros related, but now that emails are also
      routed through, how can i use aws for real security, cost, productivity, and efficiency gains?
      not sure if i ever mentioned this: i have mullvad vpn plan via tail scale for vpn and exit nodes"

status: THOUGHTS ONLY. Nothing here is designed, nothing is grounded against live AWS state.
        Every service-level claim is [INFERENCE] until verified.
```

## (a) SCHEDULING CLOUD AGENTS — the constraint is already decided, and it is favourable

Non-negotiable #1 (sealed core, zero egress) does not merely *permit* this shape — it **forces** it,
exactly as [[email-architecture-aws-external-local-internal]] found: **core cannot address a cloud
agent at all.** Anything reaching AWS goes through `edge/`, and `edge/` never reads the vault (#2).

⇒ A cloud agent is therefore, by construction, an agent **with no corpus access**. That is not a
limitation to work around — it is the security property, and it makes the class safe to reason about:
a cloud agent can only ever act on what the scheduler hands it.

⚑ **The scheduler is the interesting half, not the agent.** The owner's phrase — *"the appropriate
context, prompt, and constraints"* — is a **provisioning triple**, and this repo already has that
concept: the captured `(model, effort, context)` prep triple, and `dn-capability-scope`'s
`(Σ,E,T,A)` lattice. A cloud agent is a scoped client whose scope happens to be empty of the corpus.

**What such an agent could legitimately do:** infrastructure reconciliation, cost queries, log
triage, certificate and key rotation checks, backup verification — all *reporting inward*, none
*reading outward into the vault*. `[INFERENCE]` Under `dn-hands-and-the-effector-layer`, any
irreversible cloud action belongs on the effector path (propose → human → JIT credential), never
issued by a model directly (#3: the model advises, code acts).

## (b) AWS BEYOND OUROBOROS — directions, not designs

`[INFERENCE]` throughout. These are worth *investigating*, and none should be built from this list.

**Security.** The root-recovery-mailbox hardening is already owed and already blocking (finding-0232,
the owner queue) — that is the ceiling over every other control and should land before anything new
is added. Beyond it: consolidating on the SSO door rather than long-lived keys; a keyed audit trail
for anything the palace does in the cloud; and the KMS threat-layering already reasoned through in
[[kms-threat-layering]] — its finding that **only `MultiFactorAuthPresent` binds an agent already
inside the perimeter** applies to every new cloud capability, not just the decrypt path.

**Cost.** ⚑ The honest first move is *measurement, not architecture*. This repo has repeatedly found
that inherited figures were wrong when finally measured (the "~4–5×" dedup claim, the resume-brief
line count, the mis-attribution count). A cost baseline — what is actually running, and what it costs
per month — is a **reading**, and it belongs in the seat's readings pane before any optimisation is
designed.

**Productivity / efficiency.** The lane that has already proven itself is the **exhaust lane**:
render outward, act locally. Email is the newest instance. `[INFERENCE]` Anything that follows the
same shape — the palace renders, a third party carries, the owner reads on a phone — inherits the
same privacy analysis and is cheap to reason about. Anything that inverts it (a third party holding
state the palace depends on) is a new trust boundary and needs its own note.

## ⚑ MULLVAD-VIA-TAILSCALE — EGRESS SEGMENTATION (owner correction, 2026-07-27)

> ⚑ **An earlier revision of this capsule read this as an *inbound/auth* concern — how the system
> reaches AWS or KMS. That was wrong and is retracted.** The owner: *"the vpn is not to access kms,
> we already have a locked down view of it, tailscale network. what i am saying is that whenever the
> system needs to reach outside aws for anything, they can be routed through exit nodes to keep a
> more segmented security boundary."*

**It is about OUTBOUND traffic to the open internet, and it fits the architecture unusually well.**

Non-negotiable #2 already says only `edge/` touches the network and it never reads the vault. Exit
nodes add a **second, orthogonal boundary on the same component**: not *what* may reach the network,
but *from where it appears to*.

| property | what it buys |
|---|---|
| home IP never exposed to a third party | a hostile or breached counterparty sees an exit node, not the house |
| egress separated from tailnet-internal traffic | one compromised outbound integration does not sit on the same path as internal reachability |
| egress is *chosen*, not incidental | it becomes a configured, auditable property rather than whatever the ISP assigns |

⚑ **The threat layering in [[kms-threat-layering]] is entirely about INBOUND authority** — who may
invoke, and whether a human was present. It says nothing about outbound exposure, because that was
not the question being asked. ⇒ **These are complementary, not competing.** Exit-node segmentation
is a fourth concern beside that partition, not a fourth layer inside it.

`[INFERENCE]` The AWS-facing path is presumably *not* the one to route through an exit node — AWS
access is the locked-down, SSO-and-tailnet-governed door, and deliberately varying its source
address would work against controls, not for them. **The candidate for exit-node routing is the
open-internet leg: third-party APIs, outbound mail, fetches.** Worth stating explicitly in any
design so the two paths do not get conflated the way this capsule first conflated them.

## ⚑ THE QoL SERVICES QUESTION — the sorting rule matters more than the list

> *"aws already has notifications services, queues, cloudfront, text/phone services, emails, dns,
> etc, so many useful and potential QoL services that can be cheap at our scale"*

**One question sorts all of them: which side of the `edge/` boundary does it live on?**

- **OUTWARD-FACING PLUMBING — candidates.** The palace renders, a third party carries, the owner
  receives. This is the exhaust lane's proven shape and inherits its privacy analysis unchanged.
- **ANYTHING HOLDING STATE THE PALACE DEPENDS ON — not candidates without a note.** A cloud queue,
  a cloud store, or a cloud scheduler that core must consult inverts NN-1: core cannot reach it, so
  it would have to reach core. That is a new trust boundary, never a convenience.

`[INFERENCE]` throughout — service capabilities and pricing are **not verified** and must be before
anything is planned.

| service | fit | note |
|---|---|---|
| **notifications** | ⚑ **strongest immediate fit** | A push lane is *already an owed gap* — `PushNotification` is not in the repo (found at autopilot graduation), and the phone-report lane fired **silently twice today**. Pure outward: a title and a link, never corpus. |
| **email** | fits, already reasoned | [[email-architecture-aws-external-local-internal]] — AWS-external / LOCAL-internal, cloud agent reaching core through `edge/`. ⚑ Inbound is the entire security surface (`From:` is spoofable); outbound ships first. |
| **DNS** | fits | Naming for the outward-facing lane. Low risk, low drama. |
| **CDN** | fits *with care* | Could serve the exhaust reports — but reports contain build detail. Signed, expiring URLs at minimum, and the whitelist discipline the GitHub pane needs ([[github-as-the-proof-of-work-pane]]). |
| **text / phone** | ⚑ **already constrained by NN-12** | Speech synthesis and recognition run **locally in core**; only audio crosses the carrier; the adapter dials **only the pre-registered number**; the LLM never supplies a number; a passphrase authenticates before personalized content is spoken. Any SMS/voice idea inherits all of it. |
| **cloud queue** | ⚑ **not a candidate for core work** | The local queue is single-writer by design and is *wedged right now*. A cloud queue would only ever be legitimate for **cloud-side** work an edge agent performs — never as a path into core. |
| **log aggregation** | fits, for the cloud side only | Observability for edge/cloud actions. Must not ingest local corpus logs. |
| **object storage / archive** | ⚑ **needs a note** | Backup is `restic`-shaped here already. Off-site corpus backup is a *corpus leaving the house* question — NN-11 territory, encryption-at-rest analysis required. **Not a QoL item.** |

⇒ **Recommended first move, and it is small:** the notification lane. It is already owed, it is
purely outward, it needs no corpus access, and it closes a gap that has silently failed twice.
**Everything cost-shaped should wait on a measured baseline** — this repo has been wrong about every
inherited number it eventually checked.

## OPEN — the ones worth an owner-question rather than a guess

- Is a cloud-scheduled agent a **new agent archetype** (a scoped client with an empty corpus scope),
  or an existing one relocated? The taxonomy note would decide.
- Does the **exit node** strengthen, weaken, or merely relocate the tailnet layer in
  [[kms-threat-layering]]'s partition?
- What is the **actual monthly AWS spend**, by service? Unmeasured, and everything cost-shaped is
  guesswork until it is a reading.
