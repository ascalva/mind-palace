# ouroboros-email-identity

## 2026-07-20T16:08:40Z

```capsule
topic: ouroboros-email-identity
date: 2026-07-20

decisions:
  - The owner controls the `ascalva.com` domain and can provision email accounts
    on it via AWS (capability already present; "might need a refresh"). This makes
    a real email identity for the system feasible on demand.
  - When Ouroboros ever needs an email address for anything, it will be
    `ouroboros@ascalva.com` — the name is settled; creation is deferred until a
    concrete need exists.

parked:
  - decision: Create the `ouroboros@ascalva.com` mailbox.
    default: Not created — no mailbox provisioned until something needs it.
    re_entry: Any capability, adapter, or workflow requires Ouroboros to send or
      receive email (e.g. an edge-plane notification/inbound channel, an account
      signup, a build-report delivery lane). Then provision it (owner-run,
      AWS-side; refresh the email-provisioning capability first if needed).

open_questions:
  - Which AWS email path is intended — SES (send/receive, programmatic) vs
    WorkMail (a full mailbox)? Send-only vs a real inbox drives the setup.
  - Which plane owns the email identity? An email channel is an interface adapter
    that transits a third party (the mail provider), so by non-negotiables #11
    (the interface may transit a third party; the corpus never does) and #2
    (network and private data never share a component) it belongs to the EDGE
    plane (`ouroboros-edge`, dn-plane-principals §3.4), never core, and is opt-in
    — it leaks interactions, never the corpus.
  - Voice/telephony precedent (#12): email may want the same bounded posture —
    owner-authenticated, owner-registered destinations only? Or is email a looser
    channel than telephony? To decide at design time.

next_steps:
  - None now — this is a seed, held until a need surfaces (see re_entry).
  - When a need surfaces: /graduate this from (or fold it into) the edge/ambassador
    adapter design; the mailbox creation itself is an owner-run AWS step.

references:
  - docs/design-notes/plane-principals.md   # §3.4 the edge plane (ouroboros-edge) — the natural owner of an email adapter
  - CONSTITUTION.md                          # non-negotiables #2, #11, #12 (network/data separation; interface transits a third party; bounded channels)
  - Phase-8 AWS account (memory phase8-aws-decisions): acct 054942746160, SSO alberto-sso, us-east-1
```
