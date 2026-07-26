# ambassador-thread-and-the-afk-loop

The owner is away from the keyboard and wants to *converse*, not just receive. Today the AFK loop is
**half-duplex**: the exhaust lane pushes reports to his phone and there is no return path. The
Ambassador's reasoning half is already ratified; what is missing is a **thread** — a durable,
two-way, authenticated channel that survives the death of any one session.

## 2026-07-26T15:05:00Z

```capsule
topic: ambassador-thread-and-the-afk-loop
date: 2026-07-26

decisions:
  - THE IDEA (owner, 2026-07-26, verbatim): "times like this where I will be afk makes me want what we
    had discussed, some way of opening messages, threads, having a conversation with a claude
    ambassador/insider agent".
    ⇒ Raised in the live condition that motivates it: he is AFK, two builders are running, reports are
    about to land in the exhaust lane, and the only way he can respond is by returning to this session.
  - ⚑ THE SHARP FRAMING, AND IT NARROWS THE PROBLEM A LOT: the missing piece is not the agent. It is the
    RETURN PATH. `docs/design-notes/ambassador-as-reasoning-agent.md` is **ratified** — thinking, cadence
    and transparent effort are designed. The exhaust lane already delivers one-way to the phone
    (Syncthing). What does not exist is an INBOUND queue plus a thread identity. So this is a transport
    and state problem wearing an agent's clothes.
  - ⚑ WHAT A THREAD REQUIRES THAT A REPORT DOES NOT — three things, and each is already constrained by a
    non-negotiable rather than open:
      (a) HUMAN AUTHENTICATION. NN-12 already fixes the pattern for voice: a passphrase/callback
          authenticates the human BEFORE personalized content is spoken. An inbound text channel needs
          the same gate for the same reason, and should reuse the pattern rather than invent a second one.
      (b) A DURABLE THREAD OBJECT. Sessions are deliberately disposable; a thread must not be. This is
          the same shape as `docs/brainstorms/durable-chat-blessings.md` (chat as a queryable, causally-
          linked stratum) — that note is the prior art and should be read before designing anything here.
      (c) AN INBOUND QUEUE THE DAEMON POLLS. The scheduler already owns a job queue; a message is a job.
          Probably no new machinery, which is the argument for doing it at all.
  - ⚑ THE PRIVATE DEFAULT IS ALREADY DECIDED AND IT IS NOT A MESSAGING APP. NN-11: the interface may
    transit a third party; **the corpus never does** — adapters leak interactions, not the corpus, opt-in
    only, and the private default is local/Tailscale. He already runs Tailscale and the daemon is already
    local. So the FIRST version should be a thread over Tailscale straight to the daemon — no Slack, no
    SMS, no third party, nothing to opt into. Reaching for a messaging platform first would be choosing
    the harder, leakier design when the private one is already installed.
  - ⚑ THE BOUNDARY THAT MUST BE STATED UP FRONT: a phone thread may DISCUSS and QUEUE. It may not FLIP A
    GATE. The owner's own standing rule is "review away from computer; bless stays at keyboard", and the
    machinery agrees structurally — blessings are owner-by-hand and committed, and journal-gate clause
    (c) refuses to close a session on an UNCOMMITTED flip. A thread that could bless would dissolve the
    one gate the whole artifact chain rests on. So: read, ask, answer, rule-in-words, park, prioritize —
    all fine from the phone. `proposed → ready` and `draft → ratified` stay at the keyboard.
      ⇒ Corollary worth noticing: a RULING is not a BLESSING. Most of what the owner did today from
      chat — answering oq questions, choosing options, redirecting scope — is ruling, and rulings are
      exactly what a thread should carry. That distinction makes the feature much more useful than it
      first looks while leaving the gates untouched.

parked:
  - decision: transport for v1
    default: Tailscale to the local daemon (NN-11's private default; already installed, zero third
      parties, no opt-in needed)
    re_entry: the owner wants reachability from a device that cannot join the tailnet — then, and only
      then, an adapter and its opt-in are on the table
  - decision: whether the thread can carry a BLESSING
    default: NO — discuss and queue only; gates stay at the keyboard
    re_entry: an owner ruling that explicitly reopens it, which would need to answer how an uncommitted
      flip becomes accountable (clause (c)) — `durable-chat-blessings.md` is where that argument lives

open_questions:
  - Does `docs/design-notes/nervous-system-and-ambassador.md` (status `draft`) already specify this
    channel? It is the Ambassador's other half and it is agent-writable under A8. ⚑ READ IT FIRST — this
    may be an amendment to an existing draft rather than a new note, and minting a second note over the
    same surface is how the ambassador design already accumulated one superseded note
    (`ambassador-interpretation-and-flow.md`).
  - What is the unit of a "thread" — one per topic, one per day, one per plan? The artifact chain has no
    conversational object today, and picking wrong here means retrofitting later.
  - Who speaks: the Ambassador, or the orchestrator? The owner said "ambassador/insider agent" with a
    slash, which reads as genuinely undecided. They have different authority: the Ambassador is the
    outward face; the orchestrator holds the write duties. A thread that can *do* things needs the
    second, which raises the trust question the Ambassador's ratified note may already answer.
  - How does a thread interact with the exhaust lane's existing HTML reports? Ideally the report IS the
    first message of a thread rather than a separate artifact — otherwise there are two records of the
    same delivery and they will drift (finding-0175's family).

next_steps:
  - Nothing graduatable. FIRST ACTION IS READING, not designing: `nervous-system-and-ambassador.md`
    (draft), `ambassador-as-reasoning-agent.md` (ratified — the constraints it already fixes), and
    `durable-chat-blessings.md`. The odds are good that most of this is already specified and the real
    output is an amendment plus one small build.
  - The cheapest thing that would help TODAY, and it needs no design note: the exhaust report already
    reaches his phone — give it a REPLY affordance that lands in a file the next session reads. Even a
    plain text file in a synced directory closes the loop from half-duplex to full, badly but really,
    and it would have been useful this morning.

references:
  - docs/design-notes/ambassador-as-reasoning-agent.md   # RATIFIED — the reasoning half is designed
  - docs/design-notes/nervous-system-and-ambassador.md   # draft — the other half; read before designing
  - docs/design-notes/ambassador-interpretation-and-flow.md  # SUPERSEDED — the cautionary precedent
  - docs/brainstorms/durable-chat-blessings.md           # chat as a durable queryable stratum
  - docs/BUILD-SPEC.md                                   # NN-11 (adapters leak interactions, not corpus) · NN-12 (voice: authenticate the human)
```
