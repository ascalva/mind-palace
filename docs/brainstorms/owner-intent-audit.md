# owner-intent-audit

## 2026-07-27T04:07:52Z

```capsule
topic: owner-intent-audit
date: 2026-07-27

⚑ WHAT THIS IS, AND WHAT IT IS NOT: |
  Commissioned by the owner, verbatim: *"I want to make sure that nothing was lost in the chaos,
  feels like I was inspired to write while the house burned around me."*

  This is **archaeology plus a consistency check**, not a summary. It reconstructs what he said
  across 2026-07-25 → 2026-07-27, and asks of each intent only one question: **does a durable
  artifact hold it?** The LOST section is the deliverable; everything else is context for it.

  Every entry carries transcript coordinates `(session-prefix, row, UTC)` so any claim here is
  re-checkable. Local time is **UTC − 4** throughout — file mtimes and `git log --date=local`
  are local, transcript timestamps are UTC. Several near-misses in this audit were the same
  event four hours apart.

⚑⚑ THE METHOD DEFECT THAT ALMOST SANK THIS AUDIT — three owner-input channels, not one: |
  Filtering `type == "user"` with string content (the obvious sweep) recovers **only ~60%** of
  what he actually typed. Two more channels carry his words:

  1. `type == "user"`, `message.content` a plain string — the ordinary turn.
  2. ⚑ `type == "queue-operation"`, `operation == "enqueue"`, with a top-level **`content`**
     string — a message he typed **while the agent was mid-turn**. 86 of these in this window are
     not recoverable from channel (1) at all.
  3. `AskUserQuestion` tool_result — `"Your questions have been answered: <q>"="<his choice>"`.
     Two in this window; one settled the commit-staging rule.

  ⚑ **Channel (2) is where the losses concentrate, and the reason is structural: it is exactly the
  channel he uses when the agent is busy — i.e. when the house is burning.** Four of the eight
  LOST items below arrived on it. Any future sweep that reads only channel (1) will find a clean
  repo and miss them.

seed: |
  Corpus swept: 217 transcripts, all rows dated ≥ 2026-07-20 (674 channel-1 turns, 86 unseen
  channel-2 messages, 2 channel-3 answers). Artifact side: `docs/brainstorms/`,
  `docs/design-notes/`, `docs/findings/`, `docs/inbox/owner-questions.md`, `docs/TRACKS.md`,
  `docs/DESKCHECK-QUEUE.md`, `~/.mind-palace/exhaust/owner-queue.md`, and `git log` (206 commits
  since 2026-07-24 — commit **bodies** in this repo carry reasoning, and three intents were found
  living only there).
```

## ⚑⚑ LOST — expressed, and no artifact holds it

Ordered by what it costs to have lost. Each row names the channel it arrived on.

### L-1 — The internal-documents / commit-economy proposal ⚑ highest value

**`2026-07-27T02:44:42Z` · `61710eca` row 974 · channel 1**

> *"…we don't need to push every single build plan and design note, those become internal
> documents, and not for privacy reasons, but I don[']t [think] we need to commit every single time
> one of those documents is edited, that's why we can use ouroboros to find the succession path to
> prove: it would look like a more grounded way of proving internal documents, that eventually get
> graduated as code changes, feature additions, etc, no one's gonna read through our insanly large
> docs dir, starting to feel like overkill, we push every time a brainstorm is had? too much"*

Searched and absent: `succession path`, `internal document`, `docs dir`, `overkill`, `push every`,
`commit every` across all of `docs/`. Nothing in `git log`, no finding, no oq.

**Why it was dropped:** it rode in the same message as *"anyways, start minting build plans"*. The
reply went straight to verifying the ratification, and three minutes later he redirected minting to
a fresh agent — the idea never got a turn of its own. He even flagged its own status: *"this is just
another idea that stacks on top-ish."*

⚑ **This is not a small process nit.** It proposes changing what the artifact chain *commits*, and
it proposes **ouroboros's own retrieval as the substitute proof** — the succession path standing in
for the git trail. That is a claim about the system auditing its own document lineage, and it
directly touches `dn-agent-workflow`'s premise that no decision lives only in a transcript.
`[INFERENCE]` It also sits in tension with the **code sensor**, which ingests commit bodies:
committing less means the corpus sees less of its own reasoning. He did not raise that tension;
neither did anyone else.

⇒ **Recommend: `finding`, ftype `design`, routed to the orchestrator.** It is a design-layer
question about the chain itself, so per the routing rule it does not stop at a builder.

### L-2 — "Are we getting rid of `graduate → YOU BLESS → build`?" ⚑ also PROMISED-NOT-DONE

**`2026-07-27T02:18:37Z` · `61710eca` row 868 · channel 1**

> *"I thought we were getting rid of this transition: graduate → YOU BLESS → build, so I'm not in
> the loop? or did we never get a chance to finalizing something?"*

At `02:20:44Z` the agent wrote, of this exact question: *"his blessing-gate question deserves a
durable answer, not just a chat reply."* No such answer exists. Searched and absent: `not in the
loop`, `getting rid of`.

⚑ **The second half of the very same message did land** — *"the types can still [be] disobeyed…
that's a trip, a system trip"* → `docs/brainstorms/type-trips-runtime-invariant-alarms.md`
(22:20 local). One message, two intents, one captured. **Multi-intent messages are a systematic
loss surface**, and this is the cleanest instance of it in the window.

⚑ **It is a question about a bright line.** `CLAUDE.md` holds `proposed→ready` as owner-only-by-hand,
and `dn-autopilot-and-delegated-blessing` (ratified `b27142d`) is the note that would relax it. He is
asking whether that already happened. The honest answer — that the ratified note licenses an
*attended* path and no plan has yet built it — exists nowhere he can read it.

⇒ **Recommend: an owner-question** (self-contained: quote him, state what the note actually
licenses, name what is unbuilt). Not a finding — he asked a question and is owed an answer.

### L-3 — oq-0054 was answered; every artifact still says it is open

**`2026-07-27T02:22:58Z` · `61710eca` queue-row 918 · channel 2**

> *"oq-0054: ok, provide the design note when ready"*

`oq-0054` glosses as: *the intent capsule's size cap bounds **shape**, not bytes — 38,122 chars pass
on 39 lines; pick (a) a character cap, (b) a max token length, or (c) accept and amend*
(`docs/inbox/owner-questions.md`, warrant `finding-0219`). In the file it still reads `status: open`
with an empty `answer:`, and `~/.mind-palace/exhaust/owner-queue.md` still lists it under
**RULINGS OWED** — so the queue that reaches his phone is asking him for something he already gave.

⚑ His answer does not pick (a)/(b)/(c); it accepts the parked default **and asks for a design note**.
That is a *different* disposition than any option offered, which is probably why it was not
pattern-matched as a ruling. Recording it as "answered — (c), plus a note owed" would be putting
words in his mouth; recording it as *what he actually said* is the correct move.

⇒ **Recommend: orchestrator records the answer verbatim in `oq-0054`'s `answer:` field** and drops
it from the exhaust queue's owed list. Orchestrator is single-writer of both; I am not.

### L-4 — The permission to wipe the resume brief, dropped for ~24 hours

**`2026-07-26T03:16:25Z` · `a73e8b34` queue-row 660 · channel 2**

> *"also, I give you permission to wipe the resume, you don't need a handoff right now"*

It was not acted on. Over the following ~24h the Stop gate's clause (e) — *commits landed but the
resume brief is stale* — fired at least **seventeen more times**, each one costing a turn, until he
re-issued the instruction three times in thirty minutes on 2026-07-26 evening:

| when (UTC) | session · row | what he said |
|---|---|---|
| 2026-07-26T03:16:25Z | `a73e8b34` q660 | *"I give you permission to wipe the resume"* — **dropped** |
| 2026-07-27T03:07:13Z | `61710eca` 1104 | *"clear the queue right now"* |
| 2026-07-27T03:07:32Z | `61710eca` 1107 | *"clear the handoff right now"* |
| 2026-07-27T03:36:33Z | `61710eca` 1259 | *"clear the handoff brief now and genuinely write a correct handoff"* |

⚑ **`docs/brainstorms/context-load-as-a-feedback-loop.md` measures this loop and misses this fact.**
Its baseline row reads `resume brief, after clearing | 83 lines | owner instruction, 2026-07-26` —
true, but it dates the instruction to when it was *obeyed*, not when it was *given*. The gap is the
measurement: the intervention was available a full day before it was applied, and the 17 firings are
the price of the delay. That capsule calls its numbers *"the baseline and the whole value of this
capsule"*, so the omission is load-bearing. **Corrected by surgical edit — see the EDITS section.**

⇒ Beyond that edit: **no new artifact needed.** The redesign it argues for is already ratified
(`dn-role-state-and-scoped-handoff`) and graduated to bp-124..127.

### L-5 — The sub-orchestrator's merge and audit authority

**`2026-07-27T03:27:29Z` · `61710eca` row 1205 · channel 1**

> *"tell the sub-orchestrator to start spawning them as i bless them, sub-orchestrator will handle
> the merge and stand up its own auditor to review before merging, it manages the merge, not you"*

This is a **standing amendment to the delegation contract**, not a one-off instruction for this
wave. The prior rule (owner, 2026-07-11, and the `delegate` skill) is that the *orchestrator*
scrutinizes diffs pre-merge. He has now interposed a layer: sub-orchestrator merges, and stands up
its own auditor. Searched and absent: `its own auditor`; `sub-orchestrator` appears only as
narrative in `docs/brainstorms/agent-interface-and-role-messaging.md` and `finding-0235`, never as
a rule.

⚑ It is being **obeyed right now** by the live bp-124..127 wave, purely from an agent's working
memory. When that agent's context ends, the rule ends with it — which is precisely the failure class
`dn-role-state-and-scoped-handoff` was ratified to close. `[INFERENCE]` It also raises a gate
question nobody asked: an auditor that a sub-orchestrator spawns is *chosen by the thing it audits*.

⇒ **Recommend: `finding`, ftype `design`**, routed to the orchestrator; it is a candidate amendment
to the `delegate` skill, and skills are not a builder's surface.

### L-6 — The battery-cycle process-management watch

**`2026-07-26T05:07:33Z` · `a73e8b34` row 1074 · channel 1**

> *"I'm in laptop mode now, keep an eye on how the OS manages other processes at different phases of
> the battery cycle"*

A baseline was taken in-session; nothing durable holds it. Searched and absent: `battery cycle`,
`laptop mode` across findings and brainstorms.

⚑ **This is a standing sensor request with a proven incident behind it**, which is what makes losing
it expensive. On `2026-07-25T03:44:32Z` (`9e9dee00` row 215) he reported the machine reaching ~1%
battery and the OS silently stopping the daemon, leaving **1,600+ jobs stranded in the queue** — the
incident that produced bp-100/101/102. That incident is captured; the follow-up instruction to
*instrument the thing that caused it* is not. The palace's scheduling model still assumes a
plugged-in machine.

⇒ **Recommend: `finding`, ftype `discovery`** — it names an unmeasured environmental input to the
supervisor, and belongs with the Ops track.

### L-7 — "Sensors may break when the daemon isn't running"

**`2026-07-25T05:56:44Z` · `bbc93d80` queue-row 1034 · channel 2**

> *"fyi, keep an eye on things, I'm sure certain sensors may break when the daemon isn't running"*

⚑ **Lower confidence than the rest of this section.** The daemon-down state is discussed in
`finding-0214` (self-mod tests read the gitignored overlay) and neighbours, but no artifact records
this as a *standing watch*, and no sensor-by-sensor behaviour-when-down inventory exists. I am
flagging it as LOST rather than PARTIAL because I could not find the specific claim anywhere; if
another sweep finds it absorbed, downgrade it.

⇒ **Recommend: fold into the L-6 finding** rather than file separately — same subject (the system's
behaviour when its own substrate is degraded), and two thin findings are worse than one.

### L-8 — The self-referential-soundness aside

**`2026-07-25T04:45:08Z` · `bbc93d80` queue-row 598 · channel 2**

> *"funny how we're building recursion to better manage the system, another layer of system
> operation, here's a joke: even the logic system has a logic system to logically decalre it's
> sound"*

Delivered as a joke and treated as one. ⚑ **It was correct, and the system paid two days to
rediscover it.** On 2026-07-27 `context-load-as-a-feedback-loop.md` independently arrives at **L5 —
corpus self-reference**: the code sensor ingests commit bodies, so the corpus contains the system's
own prose about itself, and *"a dreamer conditioning on that substrate can dream about its own
dreams."* That is his joke, stated as a design risk.

⇒ **Recommend: no new artifact — one line into the existing capsule's L5** noting the earlier
independent statement, if the orchestrator wants the provenance. I did **not** make that edit: it is
enrichment, not correction, and the rules say enrichment goes in the report. The transferable lesson
is the cheaper prize: **his jokes have been load-bearing twice this week**, and the capture heuristic
currently filters on register rather than content.

## CONTRADICTED — the later word is right, the artifact holds the earlier one

- **oq-0035 — ruled, still filed open.** Commit `941785d` (2026-07-25) reads *"rule(oq-0035): (c)
  both — worker job budgets, with bounded escalation as the fail-safe"*, and the owner's turn
  (`2026-07-25T19:01:04Z` · `d8e4581d` row 983) is *"I like (c), feels like the most robust
  approach."* `docs/inbox/owner-questions.md` still shows `status: open`. oq-0035 glosses as:
  *graceful shutdown has no bound — SIGKILL escalation, worker job budgets, or both?* (warrant
  `finding-0171`). ⇒ **Orchestrator: flip to answered, citing `941785d`.**
- **`DESKCHECK-QUEUE.md` entry 5 vs the oq-0050 ruling.** The row still reads *"decision owed — wire
  live, or accept dormant"* for the sync/diachronic dreamers, but oq-0050 (*should the dreamers be
  wired live?*) was answered **WIRE** on 2026-07-26 (`bfc42f2`), and he restated it at
  `2026-07-26T14:16:59Z` (`b1e67a03` row 858): *"the dreamers should be wired and we should start
  testing them and finalizing them soon."* The demo owed changed character — it is no longer "show
  it isn't wired", it is "show it running". ⚑ The file is **generated by `scripts/board.py`**, so
  the drift is in the generator, not the file. `scripts/**` is outside this audit's reach and inside
  the live wave's; **do not hand-edit either.** ⇒ Recommend a `codebase` finding against
  `scripts/board.py`, filed after the wave lands.

## PARTIAL — landed, but degraded

- **The two email rulings-forced are in prose, filed as questions nowhere.**
  `docs/brainstorms/email-architecture-aws-external-local-internal.md` raises both explicitly and
  says so: *does NN-11 cover corpus formed in the cloud?* and *is an emailed reply retractable?*
  `~/.mind-palace/exhaust/owner-queue.md` lists them under *"not yet filed as questions"*. Neither
  has an `oq-` id. ⚑ **`owner-questions.md` is the surface `/triage` sweeps; a ruling that never
  becomes an `oq-` is never put to him.** ⇒ Recommend the orchestrator mint two owner-questions.
- **oq-0036 and oq-0037 carry no `status:` field at all** — they use a prose format
  (`**Raised:** … **Options** …`) and are therefore invisible to any status-based sweep. oq-0036:
  *what legitimises a committed `proposed→ready` flip carrying no grant record?* oq-0037: *what
  actually stops the agent reading the autopilot secret?* Both are cited as live in
  `docs/brainstorms/blessing-auth-gate.md`. ⇒ `spec-defect` finding against the inbox format.
- **"Optimize your context so you don't fall into the same mistakes"** (`2026-07-27T00:54:07Z` ·
  `61710eca` row 604) produced a **measurement**, not a recommendation.
  `context-load-as-a-feedback-loop.md` diagnoses four loops and ranks four levers, and its
  `next_steps` say *"hold as a brainstorm."* He asked what to **do**. `[INFERENCE]` The lever ranking
  (*derived > checked-from-outside > cleared*) is the answer in substance; nobody wrote it back to
  him as one.
- **`context-load-as-a-feedback-loop.md`'s seed silently normalizes his text.** The capsule's quote
  fixes two typos (`becaue`→`because`, `helps us`→`help us`) and drops the leading *"wait, make a
  note,"*. Compare the sibling `kms-threat-layering.md`, which preserves `priveleged` and `presensce`
  verbatim. ⚑ Cosmetic and I did **not** edit it — but the house convention is verbatim-including-
  typos, and a capsule that tidies one owner quote is a capsule a reader cannot trust to be exact.

## PROMISED-NOT-DONE

- **The durable blessing-gate answer** — see **L-2**. The only clean instance in the window; the
  agent named the obligation in its own words at `2026-07-27T02:20:44Z` and did not discharge it.

⚑ Two near-misses that turned out **clean**, recorded so nobody re-opens them:
- *"you never sent me the current version of the textbook"* (`2026-07-26T13:49:07Z` · `b1e67a03`
  q560). **Delivered** — `~/.mind-palace/exhaust/reports/mind-palace-book-2026-07-26.pdf`, written
  09:50 local = `13:50Z`, one minute after he asked.
- *"one file change = one commit"* (`2026-07-26T15:40:33Z` · `b1e67a03` row 1158) was **not**
  quietly reframed. The agent flagged the cost, put it to him as an `AskUserQuestion`, and he chose
  *"Explicit paths, never -A"* (channel 3, `15:50:31Z`). Commit `97fe9d9`'s body records the whole
  negotiation including his choice. ⚑ **This is the model the rest of the window should have
  followed** — the reasoning survives in a commit body, which the code sensor then ingests.

## LANDED — spot-verified, no action

Recorded so this audit is falsifiable rather than merely alarming. Each was checked against the
transcript, not assumed from a filename.

| intent (UTC) | artifact |
|---|---|
| KMS custody, root-never-authed (07-27T01:02Z) | `bs:kms-threat-layering` · `oq-0057` · `finding-0232` |
| Tailnet/VPN layering, SourceVpce, Phase 2 deferred (07-27T01:05Z) | `bs:kms-threat-layering` |
| YubiKey form factor, 3 units, breakglass (07-27T01:28Z) | `~/.mind-palace/exhaust/owner-queue.md` |
| Cognito as a front door (07-27T01:28Z) | `bs:kms-threat-layering` — corrected to IAM Identity Center |
| "owner-build" session type (07-27T01:28Z) | `oq-0041` narrative · `finding-0232` |
| Owner to-do list, **not in git**, phone-synced (07-27T01:31Z) | `~/.mind-palace/exhaust/owner-queue.md` — exists, is ungitted |
| AWS=external / LOCAL=internal email residency (07-27T01:28Z) | `bs:email-architecture-aws-external-local-internal` |
| Per-role `orchestrator@` addresses; reply routes to role state (07-27T01:37Z) | same capsule, §THE CHANNEL SUB-THREAD |
| Unique-per-site email probes as a world sensor (07-27T01:50Z) | `bs:email-probes-as-a-world-sensor` |
| Role state, not instance state (07-27T01:53Z) | `bs:role-state-and-scoped-handoff` → `dn-role-state-and-scoped-handoff` |
| Rewrite the handoff; scope state to queue/topic/role (07-27T02:05Z) | ratified `c0abfd1` → bp-124..127 |
| The spike / "I don't have a good answer" state (07-27T02:11Z) | `bs:spike-as-a-typed-artifact` |
| Type trips as runtime alarms (07-27T02:18Z) | `bs:type-trips-runtime-invariant-alarms` |
| Code agent interface: schedule/evict/priority/broadcast (07-27T02:55Z) | `bs:agent-interface-and-role-messaging` |
| SDK spawning; provisioning as `(model, effort, context)` (07-27T02:56Z) | same capsule (`4e01a74`, `742de38`) |
| The handoff brief contradicts you every window (07-27T03:11Z) | `bs:context-load-as-a-feedback-loop` |
| Secure Enclave device registry (07-27T01:33Z) | `bs:kms-threat-layering` §DEVICE-IDENTITY |
| MFA from AWS; oq-0040/0036 auth gate (07-27T02:21Z) | `bs:blessing-auth-gate` |
| Higher-dimensional projection / lossy landing (07-25T04:48Z) | `bs:ops-and-optimal-form` |
| Findings as a kafka-like routed stream (07-25T06:31Z) | `bs:decision-routing` |
| Ref grammar: `dn:name::anchor`, `f:` prefix, release `gf` (07-25T22:58–23:15Z) | `bs:owner-cockpit` (~30 sub-sections) |
| Bloom filter for seen tokens (07-25T05:40Z) | `bs:ops-and-optimal-form` — Bloom argued *wrong* here |
| SIFT/ORB → text keypoints; the Fourier probe (07-25T05:34–05:48Z) | `bs:text-keypoints-and-chunk-grain` |
| Rename = membership edge, no new vector (07-25T05:24Z) | `finding-0168` addendum 4 · `dn-vector-membership-store` |
| Tables bounded to text width (07-25T05:42Z, 18:45Z) | memory `doc-table-formatting` + notes regenerated |
| SMART as a loop, not a filter (07-26T01:10–01:20Z) | `bs:autopilot-mode` · `dn-autopilot-and-delegated-blessing` |
| Autopilot + MFA; disaster-recovery correction (07-26T00:47–00:56Z) | `bs:autopilot-mode` → ratified `b27142d` |
| Single self-destructing key slot as a sum type (07-26T02:53–02:58Z) | `bs:autopilot-mode` (03:05Z, 03:18Z) |
| CT-logs privacy cost accepted; `ouroboros.ascalva.com` (07-26T03:14–03:31Z) | `bs:autopilot-mode` · `bs:ouroboros-email-identity` |
| Scoped AWS IAM role for the agent — **parked** (07-26T03:42Z) | `bs:autopilot-mode` 04:41Z, park + shape named |
| Public diffusion markers; probe safely (07-26T06:00–06:07Z) | `bs:public-diffusion-markers` |
| Kafka-esque process weight (07-26T06:19Z) | `bs:process-weight` |
| Legal-corpus sibling / multi-tenancy seam (07-26T06:23Z, 13:45Z) | `bs:legal-corpus-sibling` · bp-123 |
| Polymarket sensor fusion; $100 as a ladder (07-26T13:46–13:47Z) | `bs:prediction-market-sensor-fusion` |
| "Navigate the world as me" (07-26T13:59Z) | `bs:acting-as-the-owner` → `dn-world-facing-agency` |
| Dreamers as predictors; the voice of a belief (07-26T14:01–14:04Z) | `bs:dreamer-and-graph-direction` · `dn-scored-beliefs` |
| Ambassador / AFK conversation loop (07-26T00:38Z, 13:51Z) | `bs:phone-chat-surface` · `bs:ambassador-thread-and-the-afk-loop` |
| NN-7 is wellbeing-scoped, not a trade ban (07-26T13:55Z) | `oq-0049` answered · `3e9a59f` |
| Mirror may act, bounded by retractability (07-26T15:50Z) | `oq-0051` answered · `f9c22f3` |
| Security through transparency; notary self-correction (07-26T05:23Z) | `bs:phone-chat-surface` 06:52Z |
| `local.toml` → `ouroboros.toml` (07-26T13:22Z) | `finding-0225` · bp-123 · `6e60c5c` |
| Auditor must be the most expensive tier (07-26T05:54Z) | `bs:autopilot-mode` 07:14Z (five rulings) |
| `git add -A` banned, stage by name (07-26T15:50Z) | `.claude/skills/commit/SKILL.md:48` · `97fe9d9` |

```capsule
⚑ SWEEP HONESTY — what this audit did NOT cover: |
  - **Era.** Complete for **2026-07-25 → 2026-07-27** (the chaos window, all three channels). The
    2026-07-20 → 07-24 era was extracted (231 channel-1 turns) but **only skimmed**; a
    channel-2 sweep of it was NOT run. If something was lost before the 25th, this audit did not
    look for it.
  - **Duplicated sessions.** `9e9dee00`/`bbc93d80` and `d8e4581d`/`6c8c6588` are fork-pairs carrying
    the same turns at the same timestamps. Deduped by normalized-text prefix; a message that differs
    only past its first 180 characters could in principle have been collapsed. None observed.
  - **Sub-agent transcripts.** Builder and auditor worktree sessions were not swept. Owner turns do
    not appear in them by construction, but an owner instruction *relayed* into one could have been
    distorted in transit, and that class is unchecked.
  - **Parse failures: zero.** All 217 files parsed line-by-line without error.
  - **Not verified:** whether the LANDED capsules are *accurate*, only that they exist and address
    the intent. Two were read end to end (`kms-threat-layering`, `context-load-as-a-feedback-loop`);
    the rest were grep-confirmed at the claim level.

⚑ THE PATTERN UNDERNEATH THE EIGHT LOSSES — one cause, not eight: |
  Sorting the LOST rows by channel and by message shape gives a single generator:

    channel 2 (typed while the agent was busy) ......... L-3, L-4, L-7, L-8   (4 of 8)
    second intent in a multi-intent message ............ L-1, L-2             (2 of 8)
    an instruction issued as an aside, mid-topic ....... L-5, L-6             (2 of 8)

  All three are the same failure: **an intent that arrives without a turn of its own is processed
  as context rather than as an instruction.** The agent answers the message's *last* or *loudest*
  intent and the others become background.

  ⇒ `[INFERENCE]` The mitigation is not "read more carefully" — that is the vigilance answer this
  repo rejects. It is mechanical: **enumerate the intents in a message before answering any of
  them**, and carry the unanswered ones forward explicitly. That is the same shape as the
  fresh-agent test, applied to a turn rather than a session.

connections:
  - docs/brainstorms/context-load-as-a-feedback-loop.md   # L-4 corrects its baseline; L-8 predates its L5
  - docs/brainstorms/kms-threat-layering.md               # audited; accurate, and its verbatim discipline is the house standard
  - docs/brainstorms/email-architecture-aws-external-local-internal.md  # audited; holds two rulings-forced that are filed nowhere
  - docs/brainstorms/type-trips-runtime-invariant-alarms.md  # the half of row-868 that DID land — L-2 is its sibling
  - docs/inbox/owner-questions.md                         # oq-0035, oq-0036/0037, oq-0054 — three consistency defects
  - ~/.mind-palace/exhaust/owner-queue.md                 # the ungitted owner to-do list; asks for oq-0054 he already answered
  - docs/design-notes/role-state-and-scoped-handoff.md    # ratified c0abfd1; the L-4 loop's designed fix
  - .claude/skills/commit/SKILL.md                        # 97fe9d9 — the negotiation-in-a-commit-body model

next_steps:
  - Hold as a brainstorm. This capsule files nothing and rules nothing; it is the map.
  - ⚑ The orchestrator (single-writer of the inbox) owes three **mechanical** corrections, in this
    order of cheapness: record oq-0054's answer (L-3) · flip oq-0035 to answered citing `941785d` ·
    give oq-0036/0037 a `status:` field.
  - Four findings recommended, none filed here: L-1 `design` · L-5 `design` · L-6+L-7 `discovery` ·
    the `scripts/board.py` staleness `codebase` (AFTER the bp-124..127 wave merges).
  - One owner-question recommended: L-2, the blessing-gate answer, written so he never has to hunt.
  - ⚑ If only one thing is done: **L-1**. It is the only LOST item that proposes changing the
    artifact chain itself, and it is the only one with no trace anywhere but this file.
```
