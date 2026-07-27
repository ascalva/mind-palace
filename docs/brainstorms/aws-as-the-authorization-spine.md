# aws-as-the-authorization-spine

## 2026-07-27T17:35:00Z

```capsule
topic: aws-as-the-authorization-spine
date: 2026-07-27

seed (owner, verbatim): |
  "I'm also thinking of aws as the authorization spine, it proves and manages the nodes, ouroboros
  runs on a node that is my laptop, the whole network is a set of isolated regions with secure
  boundaries and gates"

status: THOUGHTS ONLY. Not designed. Every AWS mechanism named below is [INFERENCE] pending
        verification against current service capability.
```

## THE REFRAME — and it is the substantial part

Today the laptop **is** the system. Under this idea the laptop **is a node**, and the system is a
network of governed regions in which that node holds a place. Ouroboros does not stop being local;
it stops being *singular*.

⚑ **The value is not multi-machine compute. It is that a node can no longer vouch for itself.**
Identity asserted by the thing being identified is the same shape as every laundering defect this
repo measured this week: *a claim becomes true by being stated inside the artifact that benefits
from it* ([[the-unchecked-claim]]). An external authority is the structural fix, and it is the same
fix as the adversarial panel and the degenerate-input rule — **put the check outside the thing
being checked.**

## ⚑⚑ THE TENSION THAT DECIDES WHETHER THIS CAN EXIST

**Non-negotiable #1: the sealed core has zero network egress, enforced structurally.**

If the spine authorizes *core*, core must reach AWS, and NN-1 falls. That is not a trade to make.

⇒ **The only compatible reading: the spine authorizes the NODE, never the core.**

| layer | who attests | may it touch the network? |
|---|---|---|
| **node** | AWS spine, via `edge/` | yes — this is the attested boundary |
| **edge** | holds the node's credential | yes, by design (NN-2) |
| **core** | attests nothing, asks nothing, learns nothing | ⚑ **never** — unchanged |

The spine's sentence is *"this node is legitimate"*, not *"this core may run."* Core's isolation
stays a **structural property of the node**, not a permission granted from outside. `[INFERENCE]`
This is the load-bearing distinction; if a design ever has core consulting the spine, it has quietly
inverted NN-1 and should be stopped at that line.

## ⚑⚑ OWNER REFINEMENT (2026-07-27) — THE SPINE IS OUT OF THE STEADY-STATE PATH

> *"ouroboros is a node role that can only be assumed by one node, like our private/public keys, it
> registers through its enclave, so aws trusts it to perform its role, aws only needed for unseals
> (with mfa code maybe?)"*

**This resolves the availability tension below, and more cleanly than the lease answer.** If AWS is
needed **only for unseals**, it is not in the running path at all:

| | touches AWS? |
|---|---|
| ordinary operation — ingest, dream, retrieve, build | **no** |
| **unseal** — the moment a sealed secret becomes usable | yes |

⇒ An AWS outage does not stop the palace; it stops *unsealing*. The fail-open/fail-closed dilemma
collapses, because the only thing that can block is the one operation where blocking is **correct**.
No lease is required for steady state; the lease question, if it survives at all, is scoped to how
long an unsealed secret stays usable.

⚑ **And this is not a new gate — it is the gate `oq-0057` already rules on.** The KMS decrypt path
*is* the unseal moment. The spine does not sit over everything; it adds **node identity to a
decision that already exists.**

### The enclave is the correct primitive, and [[kms-threat-layering]] already established why

That capsule found Apple platform passkeys sync via iCloud Keychain — bound to the **account**, not
the device — which breaks the naive "Touch ID = device attestation" reading. **SEP `userPresence`
was named as the exception: a genuinely local, device-bound control.** An enclave-registered key is
therefore the one credential that is *actually* about this machine.

### ⚑ It closes the fourth gap in the partition

`[[kms-threat-layering]]` established a partition, not a stack. The refinement completes it:

| control | stops |
|---|---|
| non-exportable key | key **theft** |
| tailnet | a stolen credential used **elsewhere** |
| `MultiFactorAuthPresent` | an agent **already inside** the perimeter |
| ⚑ **enclave-registered node role** | **which machine** the agent is inside — *previously unbound by anything* |

Enclave and MFA are **orthogonal proofs**, and the "maybe?" is worth resolving deliberately: the
enclave proves *which node*; MFA proves *a human is present*. Requiring both says **this node, with
the owner present, may unseal.** `[INFERENCE]` Requiring only the enclave would let an agent already
on the attested machine unseal unattended — which is precisely the row-3 hole the KMS reasoning was
written to close.

### "Only one node may assume the role" — the singleton is the strongest and most dangerous property

Mutual exclusion enforced **cryptographically rather than by convention** is exactly the
structural-enforcement standard this repo holds. A second machine claiming to be Ouroboros fails at
the primitive, not at a policy check.

⚑ **But the same property is the design's weakest point, by construction:** a non-exportable key in
one enclave means **if the enclave is lost, the role cannot be re-assumed.** Dead laptop, wiped
device, hardware failure — the corpus survives (it is on disk, backed up), but the *role* does not.

⇒ **A break-glass / succession path is mandatory, and it is the hard part** — because any path that
can re-mint the singleton is, by definition, a path that can mint a second Ouroboros. `[INFERENCE]`
The candidates all have real costs: an offline-held recovery key (a physical secret to protect); a
quorum ceremony (needs a second party); an AWS-side re-registration gated on root (⚑ which is
exactly why the **root recovery mailbox hardening is already owed and blocking** — finding-0232).
**This should be designed before the singleton is built, not after it is lost.**

## ⚑ THE SECOND QUESTION: WHAT HAPPENS WHEN THE SPINE IS UNREACHABLE

> ⚑ **Largely answered by the refinement above** — retained because the reasoning still applies to
> anything that *would* put the spine in the steady-state path, which is the mistake to avoid.

If AWS is the authorization spine, an AWS outage is a question about whether the palace works.

- **Fail closed** ⇒ a third party becomes load-bearing for *local* operation, which contradicts
  NN-11's private default (local/Tailscale) and makes an external dependency a single point of
  failure for a system whose whole point is that it lives in the house.
- **Fail open** ⇒ the spine is advisory, and an advisory authorization boundary is not one
  ([[structural-enforcement]]: a property is real only when something proves it).

⇒ `[INFERENCE]` **The standard resolution is a lease, and it is probably the right one here:** the
node holds a **time-bounded** attestation. Work continues through a short outage; a revoked or
expired node stops within the lease window. The design question becomes *how long is the lease*, and
that is a tunable rather than a contradiction. **This must be answered before anything is built** —
it is the difference between resilience and a hostage.

## ⚑ IT DOES NOT REPLACE TAILSCALE — they answer different questions

The owner already runs Tailscale (with Mullvad exit nodes, see [[aws-as-the-outer-plane]]), and
Tailscale already carries device identity, ACLs, and key expiry. Conflating the two would be the
error here:

| | question answered |
|---|---|
| **Tailscale** | *may this device **reach** that device?* — reachability and network identity |
| **AWS spine** | *may this identity **perform** that action?* — resource authorization, MFA binding, audit trail |

⇒ Complementary. Tailscale is the **network** boundary; the spine is the **authority** boundary.
[[kms-threat-layering]] already found the partition that makes this precise: a non-exportable key
stops *theft*, the tailnet stops a *stolen credential used elsewhere*, and only
`MultiFactorAuthPresent` binds **an agent already inside the perimeter**. ⚑ **A node spine is the
missing member of that partition** — it binds *which machine* the agent is inside, which none of the
three currently do.

`[INFERENCE — verify, do not build from this]` The plausible mechanism for attesting a workload that
runs *outside* AWS is X.509-based role assumption from a trust anchor (AWS **IAM Roles Anywhere** is
the service shaped like this). Nitro attestation is for enclaves and does not apply to a laptop.

## "ISOLATED REGIONS WITH SECURE BOUNDARIES AND GATES" — already half true

This is not a new taxonomy; it is the existing one, promoted from *process* to *network*. The palace
already has regions with gates — sealed core, `edge/`, the vault, the sandbox, and the kernel's
inner ring with its import ratchet. What the spine adds is that **node membership becomes a member
of that same family**, with the same properties the others already have: enumerated, structurally
enforced, and checkable rather than conventional.

⇒ `[INFERENCE]` The natural home for this is the capability-scope algebra — a node would become
another axis of scope, alongside the strata a client may read and whether it may write.

## OPEN — worth owner-questions, not guesses

1. ⚑ **Lease length**, and what a node does when its lease lapses mid-build. (The answer probably
   differs for *reading* the corpus versus *acting* on the world.)
2. **What is the second node?** The idea's value is proportional to there being more than one. Is it
   a cloud agent ([[aws-as-the-outer-plane]] §a), a phone, a future machine — or is this purely
   about making the *first* node's identity honest?
3. **Revocation** — what does it mean to revoke the node the corpus physically lives on? Attestation
   can stop *actions*; it cannot un-store data. ⚑ That asymmetry deserves stating plainly before it
   is discovered.
4. **Does this subsume or complicate `oq-0057`** (the KMS decrypt-path ruling)? The spine would sit
   underneath that decision, and a ratified ruling should not be silently re-opened by a new layer.
