# email-architecture-aws-external-local-internal

## 2026-07-26T00:00:00Z

```capsule
topic: email-architecture-aws-external-local-internal
date: 2026-07-26

⚑⚑ NOTHING HERE IS RULED. This is recovered REASONING, not a decision: |
  Unlike its sibling capture (`kms-threat-layering.md`, whose ruling is safe in **oq-0057**), **this
  thread produced no ruling at all.** It produced a *shape*, two rulings the shape **forces**, and a
  set of corrections. It existed only in the session transcript until now.
  ⚑ It is also a document the **ratified** `dn-role-state-and-scoped-handoff` already points at:
  §89-90 defers delivery ("email lane, ambassador, Syncthing return path") to *"the email/ambassador
  notes"* — **which did not exist.** This capsule is that missing seed.

seed: |
  Owner, verbatim (2026-07-26, one message, lightly line-broken; typos his): "let's setup a new email
  with proper security, or even better yet: we completely overhaul the current email stuff in aws, so
  that we manage relevant emails that might go to something like ouroboros@ascalva.com, of course
  that data lives in the cloud, never downloaded, accessible only via cloud APIs, managed by the
  cloud, that is where my external data that is still processed or interrogated via a cloud agent
  that interacts with the core through the edge interface we talked about, so that is how ouroboros
  could handle emails, and potentially even active interaction like email subscriptions, which can be
  curated ways of learning about the world, but through layers of security, data encapsulated,
  AWS=external, main public presensce, AWS tools used, limited raw data transfer, LOCAL=INTERNAL
  SYSTEM, the central hub for the residency of ouroboros"
```

## THE SHAPE — a residency asymmetry, not a deployment split

The frame is two planes with **unequal standing**, and the inequality is the whole idea:

```
   AWS  =  EXTERNAL       public presence · AWS tools · the mail identity lives here
                          data STAYS here: "never downloaded, accessible only via cloud APIs"
                          "limited raw data transfer"                 <-- the cut
   LOCAL = INTERNAL       "the central hub for the RESIDENCY of ouroboros"
                          the corpus · the vault · sealed core

   the mediator:   a CLOUD AGENT that "interacts with the core through the edge interface"
```

⚑ **"Residency" is the load-bearing word.** This is not "some services in the cloud, some local".
It is: *the system lives here; it keeps an outpost there.* The outpost may hold and touch external
data; it is never where Ouroboros **is**. That asymmetry is what makes the shape compatible with the
constitution rather than merely adjacent to it.

⚑ **The same frame was independently reached for a different decision, hours later, and used to
reject something concrete** — `agent-interface-and-role-messaging.md` rejects Anthropic's Managed
Agents *for this exact reason*: CMA would put tool execution (filesystem, repo, corpus-adjacent
work) inside Anthropic's cloud container, and *"the owner's frame is LOCAL = internal, the residency
of Ouroboros. That is the opposite of the boundary he drew."* ⇒ The frame is already doing
load-bearing work as a **decision criterion**, which is a good sign it is real and not a slogan.

## HOW IT SQUARES WITH THE NON-NEGOTIABLES — three clean, one genuinely uncovered

| NN | Verdict | Why |
|---|---|---|
| **#1** sealed core, zero egress | ✅ clean, and it **forces** the mediator | Core cannot dial AWS. A cloud agent is a network correspondent, so **core cannot address it at all** — every byte must be mediated by `edge/`. The shape does not merely permit the edge hop; NN-1 *requires* it. |
| **#2** network and private data never share a component | ✅ clean | Only `edge/` touches the network and it never reads the vault. The cloud agent sits by construction on the far side of `edge/`, so it is *further* from the vault than the component already trusted to be far from it. |
| **#11** interface may transit a third party; the corpus never does | ⚑⚑ **NOT COVERED** — see below | |
| **#12** bounded channels (telephony precedent) | ⚠️ inherit, don't reinvent | NN-12 demands passphrase/callback to authenticate the human before personalized content is spoken. `ouroboros-email-identity.md` flagged this precedent as an open question on 2026-07-20; it became load-bearing twice in one night. Email should **inherit** it rather than invent something weaker. |

⚑ Note the NN-1 line is the *same structural constraint* the KMS thread hit from the other side
(sealed core cannot make the KMS call either). **One boundary, two consequences** — worth stating
once in whatever design note lands, rather than rediscovering per-lane.

## ⚑⚑ RULING FORCED #1 — DOES NN-11 COVER CORPUS FORMED *IN THE CLOUD*?

This is the sharpest thing in the exchange and it is **not filed as an oq**.

> NN-11 says: *the interface may transit a third party; **the corpus never does**.*

Email subscriptions as **"curated ways of learning about the world"** means that content
**becomes corpus**. And if a **cloud agent** does the curating, then **corpus formation is happening
in AWS.**

⚑ **NN-11 was written about interactions leaking *outward*. It was not written about corpus being
*formed outside the walls*.** That is a **new case, not a covered one** — and the difference matters
because the naive reading ("the corpus is local, so we're fine") passes while the actual property
(the corpus is *constituted* locally) fails.

- **Sub-question, equally unfiled:** *which model does the cloud agent run?* **Bedrock means a third
  party reads the content** — a materially different leak from the mail provider merely *storing* it.
- ⚑ **PARTIALLY RESOLVED, for one lane only.** `email-probes-as-a-world-sensor.md` (captured
  `d7a5d15`) closes it for the probe lane by construction: **extract metadata in the cloud, form
  beliefs locally** ⇒ no cloud agent reasons about content ⇒ no corpus forms outside the walls. That
  lane also shows the cut has the right economics —

      the BULK is content (message bodies)                     -> stays in S3, never downloaded
      the SIGNAL is metadata (probe_id, sender_domain, ...)     -> a few dozen bytes cross to core

  **the value/volume ratio wants the cut exactly where the constitution wants it.** ⚑ **This does
  NOT settle the general case**: a cloud agent curating newsletter *content* still forms corpus in
  AWS. One question closed for one tenant; the general one is still genuinely open.

## ⚑⚑ RULING FORCED #2 — IS AN EMAILED REPLY RETRACTABLE?

Also unfiled. Under oq-0051 the mirror **may act, bounded by retractability** — so retractability is
now the load-bearing axis of the whole authority structure, and email lands on its worst case.

- `ops/effect_catalog.py` catalogs **`send_email` as IRREVERSIBLE, β = ∞**, deliberately contrasted
  with `draft_reply` (REVERSIBLE, β small, "never sent"). `[GROUNDED]` — verified in the file.
- It is the **A3 axis** from `effect-catalog-missing-axes.md`: **technically reversible** (delete the
  message) but **socially irreversible** (you cannot *unsend* it). The catalog reads reversibility
  off the *resource*; authority needs it read off the *world*.
- ⇒ The question: does a **disclosed** reply from `ouroboros@` count as retractable-and-autonomous,
  or unretractable-and-needs-the-owner?

⚑⚑ **WHY THIS THREAD IS WORTH MORE THAN ITS SUBJECT MATTER: the email lane is the FIRST CONCRETE
BUILD where oq-0051, oq-0052 and the effect-catalog axes stop being philosophy and become a config
flag.** Good forcing function — *better to hit it on email than on something with money attached.*

⚑ And it **supports** the non-impersonation bright line rather than straining it: `ouroboros@ascalva.com`
is a **disclosed instrument**, not the owner. oq-0052 working in practice rather than in theory.

## THE CHANNEL SUB-THREAD — email as a return path, and its corrections

Same exchange, immediately after. Owner, verbatim: *"my todo list can also be synced into my phone,
or actually, a second email, where your role-unique-identifier@ascalva.com is from an orchestrator, a
scheduler, a builder, that's how you also communicate to me that I have pending items, I wonder if my
responding to an individual owner question email, I respond during the week, and that gets processed
and routed to that builder's state ... but that role's inbox"*

It answers a gap already on the record: `ambassador-thread-and-the-afk-loop.md` states the loop is
**half-duplex** — *"the exhaust lane pushes reports to his phone and there is no return path."*

- ⚑⚑ **THE CORRECTION THAT MATTERS MOST: a reply routes to the ARTIFACT, never to a builder.**
  Builders are **disposable by design** — by the time he answers on Thursday that session is gone and
  its worktree may be reaped (**21 worktrees currently lying around with no reaper**, verified). Routing
  a reply "to the builder's state" would resurrect the very thing the artifact chain exists to make
  unnecessary. Replies route to the **owner-question / finding / plan**; the next session picks it up.
  ⇒ *That is what makes a week-long reply latency **safe** rather than broken.* `[GROUNDED]` — the
  ratified `dn-role-state-and-scoped-handoff` §201 already cites this exact correction.
- **The asymmetry that decides sequencing.** **Outbound** (system → owner) is cheap and low-risk: it
  leaks *interactions*, which NN-11 already permits. **Inbound** (owner → system state) is the
  **entire security surface** — an untrusted channel writing into the artifact chain, and `From:`
  headers are trivially spoofable, so "reply routes into state" means *anyone who can forge an email
  can inject into the system.* ⇒ **Ship outbound first; treat inbound as its own deliberate build.**
- **Role addresses: right for outbound, inverted for inbound.** Seeing `scheduler@` vs
  `orchestrator@` in the inbox tells him what it is about before opening — real legibility. But for
  inbound, **one address with subaddressing**:

      From:      orchestrator@ascalva.com                  <- legibility, per-role
      Reply-To:  ouroboros+oq0052-a7f3c2@ascalva.com       <- ROUTING and AUTH in one token

  The token says *which artifact* **and** proves *this reply answers a message we actually sent*.
  Per-role **inboxes** would instead give address sprawl for ephemeral roles, stale mailboxes, and
  internal architecture leaking into headers.
- ⚑ **THE FREE v0 NOBODY HAS TRIED: Syncthing is BIDIRECTIONAL.** `~/.mind-palace/exhaust/owner-queue.md`
  already syncs to his phone — so if he checks a box or types an answer inline on the train, **it
  comes back.** The return path may already exist: no third party, no auth problem, no NN-11 opt-in.
  It is the ambassador capture's own *"a plain text file in a synced directory closes the loop from
  half-duplex to full, badly but really"*. ⇒ **Try that this week before building SES.**
- **Two constraints already ruled, easy to re-litigate by accident:**
  - **A reply may DISCUSS and QUEUE. It may never FLIP A GATE.** Email can carry a **ruling**; it can
    never be a **blessing**. `proposed → ready` and `draft → ratified` stay hand-made at a keyboard —
    which is *exactly why* "I respond during the week" works: rulings are the thing that benefits
    from async, and blessings are the thing that must not have it.
  - **NN-11 makes inbound an explicit opt-in, not a free choice.** Inbound email means his
    *rulings* — his judgments about his own system — transit a mail provider. The private default is
    local/Tailscale. Decide knowingly rather than by drift.

```capsule
⚑ A CITATION NOT TO LAUNDER: |
  The transcript attributed the "decide knowingly rather than by drift" failure mode to
  **finding-0109**. Checked: finding-0109 is *"chat freeze-once is lossy — a session left open drops
  its tail"*, which is not that. ⚑ Treat the attribution as **UNVERIFIED** and do not propagate it;
  the *claim* stands on its own, the citation does not. (Recorded deliberately — L4 laundering in
  `context-load-as-a-feedback-loop.md` is exactly a mis-citation copied forward as fact.)

open_questions:
  - ⚑⚑ **Does NN-11 cover corpus formed in the cloud?** Unfiled. Resolved for the probe lane only.
    Sub-question: which model does the cloud agent run (Bedrock ⇒ a third party reads the content)?
  - ⚑⚑ **Is an emailed reply retractable?** Unfiled. `send_email` is cataloged IRREVERSIBLE β = ∞.
  - **SES vs WorkMail — still unanswered.** `ouroboros-email-identity.md` asked it on 2026-07-20 and
    the 2026-07-26 exchange **never returned to it.** Send-only vs a real inbox drives the whole
    setup, and the two forced rulings above cannot be built past without it.
  - ⚑ **What is the actual boundary CONTRACT between the cloud agent and `edge/`?** ⚑ NOT DISCUSSED
    ANYWHERE in the transcript. "Interacts with the core through the edge interface" was said and
    never unpacked: no API surface, no direction of initiation (does edge poll, or does the cloud
    agent push?), no schema for what crosses. `[INFERENCE]` The probe lane's metadata/content cut is
    the only worked example of *what* crosses; *how* it crosses is entirely unspecified.
  - `[INFERENCE]` **"Never downloaded" needs a definition before it can be enforced.** Reading a
    message body through a cloud API in order to summarize it *is* a download by any technical
    reading; what he plausibly means is that the bulk never becomes a local artifact. Until that is
    pinned, it is a slogan, not a testable property — and this repo's standing rule is that a
    property is only real when a test or ratchet proves it.
  - **Does the mail identity's DNS/registrar control plane get hardened with the rest?**
    finding-0232 names it: putting `ouroboros@ascalva.com` on AWS makes `ascalva.com`'s registrar
    part of the trust chain, and registrar takeover reaches both the mail identity and, via mail,
    AWS root recovery. Unpriced.

connections:
  - docs/brainstorms/ouroboros-email-identity.md            # 2026-07-20 seed: the name is settled, creation deferred; SES-vs-WorkMail and the NN-12 precedent were ITS open questions and remain open
  - docs/brainstorms/email-probes-as-a-world-sensor.md      # the SENSOR sibling — deliberately a SEPARATE artifact: a channel carries rulings and needs auth; a sensor authenticates nothing BY DESIGN (the unauthenticated stranger IS the datum). Do not fold them.
  - docs/brainstorms/ambassador-thread-and-the-afk-loop.md  # names the half-duplex gap this answers; its "badly but really" option is the Syncthing v0
  - docs/brainstorms/effect-catalog-missing-axes.md         # the A3 axis (technically reversible, socially irreversible)
  - docs/brainstorms/agent-interface-and-role-messaging.md  # uses this same frame to REJECT Managed Agents
  - docs/design-notes/role-state-and-scoped-handoff.md      # RATIFIED; §89-90 defers delivery to "the email/ambassador notes" — i.e. to this
  - docs/design-notes/plane-principals.md                   # §3.4 the edge plane (ouroboros-edge) — the natural owner of an email adapter
  - docs/brainstorms/kms-threat-layering.md                 # sibling capture, same session; the registrar hop compounds finding-0232
  - ops/effect_catalog.py                                   # `send_email` IRREVERSIBLE β = ∞ vs `draft_reply` REVERSIBLE
  - docs/inbox/owner-questions.md                           # oq-0051 (mirror may act, bounded by retractability) · oq-0052 (non-impersonation)
  - CONSTITUTION.md                                         # NN-1 · NN-2 · NN-11 · NN-12

⚑ A STANDING RULE THIS THREAD REFINES RATHER THAN BREAKS: |
  "GMAIL FULLY RETIRED — never email reports" was aimed at a THIRD-PARTY MAILBOX ADAPTER (reading and
  sending through someone else's mailbox), not at email as a medium. SES from a verified own domain
  is a different mechanism: first-party sender, our zone, our DNS, no mailbox adapter. ⇒ The
  retirement stands; a new thing is being authorized. Stated in `ouroboros-email-identity.md`
  (2026-07-26 capsule) and repeated here because the next reader of the rule will otherwise —
  correctly — refuse.

next_steps:
  - **Stays a BRAINSTORM.** Explicitly not draftable as a design note until the two forced rulings
    land: it is not a matter of effort, it is that the note would have to *assume* an answer to
    whether NN-11 covers cloud-formed corpus, and assuming it is how a non-negotiable gets eroded by
    drift rather than by decision.
  - **File the two forced rulings as owner-questions** — they are constitutive/taste, not empirical,
    so they route to him and no spike would settle them (the spike-as-a-typed-artifact distinction).
  - **Answer SES vs WorkMail first** — it is EMPIRICAL and gates the rest; a spike, not a ruling.
  - **Try the Syncthing return path before building any of it.** If a bidirectional text file closes
    the AFK loop, the inbound security surface never has to be opened at all.
```
