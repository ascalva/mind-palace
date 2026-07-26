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

## 2026-07-26T07:02:00Z

```capsule
topic: ouroboros-email-identity
date: 2026-07-26

decisions:
  - THE OPENING (owner, 2026-07-26, verbatim): "with aws being more tightly integrated to ground its
    public presence, you'll finally be able to properly send me emails."
  - ⚑ FIRST, A RULE THAT MUST BE REFINED RATHER THAN QUIETLY BROKEN. The standing operating rule is
    "GMAIL FULLY RETIRED -- never email reports"; the report lane is `~/.mind-palace/exhaust/reports/`
    → Syncthing → phone. That retirement was aimed at a THIRD-PARTY MAILBOX ADAPTER (reading and
    sending through someone else's mailbox), not at email as a medium. SES from our own verified
    domain is a different mechanism: first-party sender, our zone, our DNS, no mailbox adapter, no
    inbound surface. ⇒ Record this as a REFINEMENT with its scope stated, or the next session reads
    "never email reports" and correctly refuses. The retired thing stays retired; a new thing is
    being authorized.
  - ⚑⚑ THE HARD PROBLEM, AND IT IS ALREADY IN OUR OWN CATALOG: SENDING AN EMAIL IS IRREVERSIBLE.
    `ops/effect_catalog.py:26` says it in as many words -- `send_email` is cataloged as
    **IRREVERSIBLE, β = ∞**, deliberately contrasted with `draft_reply` (REVERSIBLE, β small, "never
    sent"). And the ε-raise staging recommended under autopilot ruling 2 is explicitly *class 3
    (irreversible) stays unreachable*. ⇒ Taken literally, the capability just authorized is the one
    class the ceiling plan keeps out of reach. This is a real conflict, not a wording problem, and it
    should be resolved on purpose.
  - ⚑⚑ THE RESOLUTION IS ALREADY CONSTITUTIONAL -- TRANSPOSE NN-12. The voice/telephony
    non-negotiable (`docs/BUILD-SPEC.md:54`, elaborated `:215`) faced exactly this shape: a phone
    call is irreversible network egress carrying private content. It is permitted because it is
    BOUNDED, not because it is reversible: the adapter dials **only the owner's pre-registered
    number(s)**; the **LLM never supplies a number** (code dials, the model advises); calls are
    owner-initiated or pre-authorized; the human is authenticated before privately-derived content is
    spoken. Transposed verbatim to email: send **only** to the owner's pre-registered address; the
    **LLM never supplies a recipient**; code sends, the model composes only the body; owner-initiated
    or pre-authorized. Under that bounding the worst case is that the owner receives an unwanted
    email -- not that an arbitrary party does.
    ⇒ ⚑ AND THIS EXPOSES A GAP IN THE TAXONOMY: what makes this acceptable is not reversibility but a
    CLOSED RECIPIENT SET. The catalog's reversibility axis cannot express "irreversible but
    bounded blast radius", which is precisely what NN-12 encodes for voice and nothing encodes for
    email. Either the catalog gains that axis, or email is admitted as a named NN-12-style exception.
    The first is better; the second is honest.
  - ⚑⚑ THE SES SANDBOX IS THE GUARDRAIL, NOT AN OBSTACLE -- DO NOT REQUEST PRODUCTION ACCESS. A new
    SES account is sandboxed: it may send **only to verified addresses**. Since the only legitimate
    recipient is the owner's own (already-verified) address, the sandbox restriction *is* the
    closed-recipient-set property -- enforced by AWS, outside our code, unbypassable by a bug or a
    confused model. That is exactly non-negotiable #1's demand: enforce structurally, not by
    convention. Staying sandboxed deliberately is the strongest form of this design, and it costs
    nothing we want.
  - ⚑ ONE INFRASTRUCTURE STEP UNLOCKS FOUR THREADS. SES sender identity needs DKIM CNAMEs + SPF +
    DMARC in `ascalva.com` -- zone `Z04459637698U9GB7PGC`, already measured authoritative in Route53,
    no `ouroboros` record, no wildcard. The same zone is where three other open items land: the
    passkey's full-FQDN `rpId` requirement, the still-open "`ouroboros.ascalva.com` A record public or
    tailnet-only?" decision, and the `tailscale cert` non-auto-renewal problem (DNS-01 already
    identified as the clean path). ⇒ Sequence these as ONE deliberate DNS/identity pass, not four
    drive-bys. That is also what "grounding its public presence" actually means operationally.
  - BOUNDARY PLACEMENT, non-negotiable. SES is network egress carrying content: it lives in `edge/`
    only, never reads the vault (NN-2), and the sealed core keeps zero egress (NN-1). The body is
    TAILORED before it leaves -- the Track G `MirrorView` / propose-never-send precedent -- not a raw
    dump of privately-derived text.
  - WHAT IT ACTUALLY BUYS, stated modestly. The exhaust→Syncthing→phone lane works but is a PULL:
    it needs the sync up and the phone to fetch. Email is a PUSH that survives being away from both
    machines. It does not touch the standing division of labour: reports are for reading away from
    the keyboard; **blessing stays at the keyboard**.

parked:
  - decision: does the full report body go in the email, or only a subject + TL;DR + pointer?
    default: SUBJECT + TL;DR + POINTER into the exhaust lane. A full report quotes privately-derived
    corpus content into a channel that transits AWS; NN-11 permits the interface to transit a third
    party but never the corpus, and a build report sits close enough to that line to warrant the
    conservative default. The phone resolves the pointer locally.
    re_entry: an owner ruling, or the first report where a pointer is demonstrably not enough.
  - decision: is email admitted as an NN-12-style named exception, or does the effect catalog gain a
    bounded-blast-radius axis alongside reversibility?
    default: gain the axis -- an exception list grows and a taxonomy does not, and the axis is what
    the catalog was missing anyway.
    re_entry: the superseding autopilot note (where the role/class staging is being decided).

open_questions:
  - Does the SES send happen from the daemon (edge/, resident) or from the already-deployed Lambda
    tier? The cloud tier exists and is deployed; routing outbound mail through it would keep the
    resident daemon free of AWS credentials entirely, which is the stronger posture.
  - Is there ever an INBOUND direction? Everything above is send-only, and send-only is what keeps
    this free of a mailbox adapter. Inbound would reintroduce exactly what was retired.
  - Does the phone report lane get retired, or do both run? Both is fine and cheap; retiring
    Syncthing would make the push channel a single point of failure for delivery.

next_steps:
  - Design-note-first; not graduatable. The note must carry: the retirement's scope refined, the
    NN-12 transposition, the sandbox-as-guardrail decision, the edge-only placement, and the
    reversibility-vs-blast-radius taxonomy gap.
  - The DNS/identity pass (four threads, one zone) is the concrete owner-side prerequisite.

references:
  - ops/effect_catalog.py:26                    # send_email = IRREVERSIBLE, β = ∞ -- our own catalog
  - docs/BUILD-SPEC.md:54                       # NN-12: bounded, code-dialed, pre-registered
  - docs/BUILD-SPEC.md:215                      # the elaboration -- the pattern being transposed
  - docs/brainstorms/autopilot-mode.md          # ruling 2: class 3 stays unreachable (the conflict)
  - docs/brainstorms/phone-chat-surface.md      # the passkey rpId / FQDN thread on the same zone
  - docs/brainstorms/public-diffusion-markers.md # the other "public presence" thread, same zone work
```

## 2026-07-26T07:10:00Z — status correction on the capsule above

```capsule
topic: ouroboros-email-identity
date: 2026-07-26

decisions:
  - ⚑ THE CAPSULE ABOVE IS EXPLORATORY, NOT A RULING. Owner, same session, immediately after:
    "don't worry too much about the email, that was not a fully fleshed out idea, i just meant that we
    can continue automating more aspects of the system."
    ⇒ Read the 07:02Z capsule as an ANALYSIS OF WHAT EMAIL WOULD COST, not as an authorization to build
    it. Nothing about the retired-Gmail rule is changed; the report lane stays exhaust → Syncthing →
    phone; no SES work is licensed. This correction exists because the capsule's own framing ("you'll
    finally be able to") would otherwise read to a future session as a granted capability.
  - WHAT WAS ACTUALLY BEING SAID, and it is the more useful point: grounding the system's public
    presence in AWS widens the surface on which MORE OF THE SYSTEM CAN BE AUTOMATED. Email was one
    illustration of that, not the goal.
  - ⚑ THE TWO FINDINGS FROM THE 07:02Z ANALYSIS SURVIVE ANYWAY, independent of email, and are worth
    keeping precisely because they generalize to any new automation:
      1. THE TAXONOMY GAP IS REAL. The effect catalog's reversibility axis cannot express "irreversible
         but bounded blast radius" — the property that makes NN-12's bounded telephony acceptable. Any
         future outbound automation will hit this same wall, so the axis is worth adding on its own
         merits, not for email's sake.
      2. AWS SANDBOX-STYLE LIMITS ARE GUARDRAILS, NOT OBSTACLES. Where a provider enforces a closed
         recipient/target set outside our code, deliberately staying inside it is structural
         enforcement of a property we would otherwise assert by convention. That reasoning transfers to
         every AWS capability we automate next.
  - ⇒ NO PARKED DECISIONS CARRY FORWARD from the 07:02Z capsule. Its parked rows (report body vs
    pointer; exception-vs-axis) are void as email decisions; the axis question migrates to the
    autopilot role/class work, where it has a real caller.

next_steps:
  - Do NOT open a design note for email. If automation breadth is the goal, the live threads that
    already carry it are the autopilot role catalog (roles as catalog subsets) and the ε-raise staging
    under finding-0011.

references:
  - docs/brainstorms/ouroboros-email-identity.md   # the 07:02Z capsule this corrects
  - docs/findings/finding-0011.md                  # where the ε-raise staging is now recorded
```
