# the-typed-workflow-registry

## 2026-07-27T22:00:00Z

```capsule
topic: the-typed-workflow-registry
date: 2026-07-27
status: OWNER BRAINDUMP + orchestrator synthesis. NOT designed. Starting point for a Fable
        design-note pass. Every mechanism named is [INFERENCE] pending that pass.

seed (owner, verbatim): |
  "no more hooks, clearly agent hooks isn't the correct move, it just clogs up the whole machinery
  it's trying to protect, it causes more issues than problem it solves, that is why I want to move
  things around a little bit. before the design note for fable to think of a new solution, I have a
  few thoughts:
  - a centralized system, it can be a store, but the documents themselves should not be the source
    of truth, they are just artifacts of the process, like github issues view
  - an object like a finding, design note, build plan, is a document type, you instantiate one of
    those via the central system, you give it what you want (finding info, journal entry, etc), it
    gives you a ref, the centralized system's goal is to stop deadlocks, to enforce outside of
    hooks, it needs to be simple, flexible, robust, while being overrule-able by me (MFA codes)
  - we now bless/ratify via auth codes, so that is the next work we need to work on before tomorrow
    when the keys arrive, for now, we can still set it all up, a system for onboarding the keys, use
    the computer's enclave, use MFA tied to kms keys (not sure if that's technically right, but you
    understand the sentiment)
  - submiting a document to the typed central system also executes document minting as a serial
    track, no race conditions
  - audits are performed using query algebra to uncover chain of events
  - resume brief is dead, the idea made sense, the execution was poor, EVERY time, good idea at
    first, but now, it feels like a bad idea, we need a distributed approach
  - the centralized system can be ouroboros, or even a new node, could be a cloud agent, its purpose
    is to queue and manage the development, it wouldn't contain ouroboros's knowledge graph
  - output (design, findings, build plans) can still be ingested by ouroboros, but the
    administrative side doesn't need to, its own knowledge graph if possible, or ouroboros could
    still work"
```

## ⚑⚑ THE SYNTHESIS — the store and the signed transition are ONE mechanism

The braindump reads as two projects (a registry; an auth gate). It is one.

[[blessing-auth-gate]] already ruled the auth shape: **do not sign the act, sign the transition** —
`sig over (id, from_status, from_content_hash, to_status, to_content_hash)`. The reason that was hard
in the markdown world is that a transition is not a *thing* there. It has no representation. It must
be reconstructed from a git diff, which is why `oq-0040` (is there a committed `proposed`
predecessor?) is an open question at all — the pre-image is an archaeological claim, not an object.

⚑ **A registry whose primary representation is an append-only event log makes the transition a
first-class object.** Then all four of the owner's asks collapse into one primitive:

| ask | satisfied by |
|---|---|
| enforce outside hooks | illegal transitions are *unrepresentable*, not *intercepted* |
| overrule-able by MFA | a privileged event requires a signature over the event |
| serial minting, no races | single-writer append = the serialization |
| audit via query algebra | the event log **is** the chain of events; audit is a query, not a reconstruction |

⇒ The design note should treat "typed registry" and "signed blessing" as one note, not two.

## ⚑ THE SPLIT THAT MAKES BOTH PROPERTIES SURVIVE — frontmatter moves, prose stays

"Documents are not the source of truth" is right but must be made precise, or it destroys two things
that currently work (nvim-editable prose; git-diff-as-audit).

**Proposal:** the registry owns **state, identity, relations, transitions, ordering**. The file owns
**prose**. Concretely — every field in today's frontmatter (`id, type, status, track, design_ref,
write_scope, depends_on, links, supersedes, created, updated`) is a *relation or a state*, which is
exactly what a store is for. The `§1..§9` body is exactly what markdown is for.

This is the seam that already has in-tree precedent: `scripts/handoff.py` is a derived view with an
idempotence pin (no sha, no timestamp) so two renders of an unchanged tree are byte-identical. The
same pin makes `store → export → git` safe, and CI can ratchet `export == working tree`.

⚑ Note this also *removes* the reason gate-guard exists. You cannot hand-edit `status:` to bless a
note if `status:` is not a field in the file.

## ⚑ WHAT ACTUALLY REPLACES THE HOOKS — write-time interception becomes land-time admission

Hooks clog because they fire on **every write**, mid-thought, and deny. The registry's equivalent
fires **once**, at submission. Same guarantee, and the friction moves off the hot path.

The six current hooks, and where each guarantee goes — this list is the completeness checklist for
the design note, so a guarantee is not silently dropped:

| hook | guarantee | disposition |
|---|---|---|
| `gate-guard` | owner-only status flips | ⇒ **dissolved.** Status is not file-resident; a flip is a signed event |
| `journal-gate` (Stop) | no session close on unfinished obligation | ⇒ **dissolved into query.** "Is there an open obligation" is a registry read, not a Stop trap |
| `session-brief` (SessionStart) | orientation | ⇒ **replaced by query** (see resume brief, below) |
| `staleness-nudge` | derived views drifted | ⇒ **dissolved.** Views derive from the store on read; nothing to go stale |
| `compaction-marker` (PreCompact) | post-compaction turn re-verifies | ⇒ ⚑ **genuinely interception-shaped.** No registry equivalent. Either keep as the one hook, or accept the loss |
| `scope-guard` | writes outside `write_scope` | ⇒ ⚑ **the hard one** — see below |

⚑ **`write_scope` is the one that does not move cleanly**, because a store cannot stop a `Write` to
an arbitrary path. Two honest options, and the note must pick deliberately:
- **(a) land-time admission** — the registry refuses a landing whose diff touches paths outside the
  declared scope. Unbypassable (landing goes through the registry), but the violation is discovered
  after the work, not during it.
- **(b) the worktree is the scope** — the agent physically cannot see files it may not write.
  Structural in the strongest sense, but costs a worktree per unit and complicates read-only context.

`[INFERENCE]` (a) is probably right and (b) is probably right for high-blast-radius units — i.e. the
choice is per-unit, not global. That would make `write_scope` an enforcement *level*, not a list.

## ⚑ "RESUME BRIEF IS DEAD" — the diagnosis, and what distributed means

It failed for a structural reason, not an execution reason, which is why it failed *every* time: **it
is a hand-maintained cache of a derivable fact, written at the exact moment the agent is most
depleted.** Lossy by construction, stale on write, and the work of writing it competes with the work
it is summarizing.

⚑ The replacement is not a better brief. It is **that there is nothing session-shaped to hand off.**
A resume brief is session-granular ("what was I doing") — but sessions are supposed to be disposable.
If each *unit of work* carries its own state in the registry (open criteria, parked items with
re-entry conditions, last landed commit, open findings), then state is already spread across the
units. That is the distribution: state lives with the work, not in a narrative about the work.

⇒ Consequence for the journal: it stops carrying status and carries only **judgement** — the why, the
surprises, the approaches discarded and the reason. Shorter, and the part that was actually valuable.
Status was always the registry's job; the journal was doing it under protest.

## ⚑ WHERE IT SHOULD LIVE — argue against the cloud agent

The owner floated: Ouroboros / a new node / a cloud agent. **Recommendation: none of those — a
local, single-file, no-daemon store, at a machine-level path outside the repo.**

- **Not in core.** NN-1 (zero egress). If the registry is ever to be reachable from the phone, in
  core it either breaks the frame or must route through `edge/`. Keep it out of the question.
- **Not coupled to the daemon.** The registry must answer whenever an *agent* runs — in a worktree,
  in CI, with the palace down. Coupling workflow liveness to a daemon under a ≤2-model / 20–24 GB
  memory ceiling (NN-8) trades a hard availability requirement for nothing.
- **Not a service.** "Simple, flexible, robust" rules it out; a cloud registry means no work happens
  on a plane, and it makes the availability question ([[aws-as-the-authorization-spine]] §"what
  happens when the spine is unreachable") load-bearing for *ordinary* operation — the exact mistake
  that capsule's owner refinement was written to avoid.
- ⚑ **Outside the repo, not in `data/`** — because each worktree gets its own `data/`, which would
  silently defeat the serial-minting property that motivated the whole idea. A machine-level path
  (`~/.mind-palace/`) is what makes minting actually serial across parallel builders.

⚑ **This preserves the owner's own refinement:** AWS is out of the steady-state path. It is consulted
at **unseal and blessing verification**, never at "mint me a finding."

## ⚑ THE PRESENT-TENSE DEFECT THIS FIXES — there is no ID allocator at all

Verified this pass: **no script anywhere mints `bp-NNN` / `finding-NNNN`.** IDs are chosen by an
agent eyeballing the highest existing number. Two builders in separate worktrees *will* pick the
same one; it surfaces as a merge conflict if the paths collide and **silently** if they do not.

⇒ Serial minting is not a nicety of the new design. It closes a live race that parallel delegation
([[delegated-builders-mode]]) makes more likely every wave.

⚑ Minting must also be **idempotent under retry** — a submit that times out and is retried must not
yield two refs. That means client-supplied idempotency keys, which is a schema decision, not an
afterthought.

## ⚑ THE FAILURE MODE TO DESIGN IN, NOT BOLT ON — the registry as the new deadlock

The stated motivation is that hooks *clog the machinery they protect*. A centralized registry can
fail the same way, worse: if it is locked, corrupt, or unavailable, **no work happens at all**,
whereas a broken hook could at least be escaped (the `OUROBOROS_HOOKS_OFF` hatch added this session).

Non-negotiable for the design note:
1. **Reads never block.** A reader must never wait on a writer.
2. **A degraded mode exists and is specified** — local append, reconcile later — not discovered
   during the first outage.
3. **An escape hatch survives**, in the same spirit as the hooks' one. If the registry can wedge the
   owner out of his own system, it has reproduced the defect it was built to remove.

## ⚑⚑ OWNER RULINGS (2026-07-27) — a PAIR of YubiKeys, and the note NESTS

> Q: what are the keys? — **"YubiKeys (a pair)"**
> Q: relation to the ratified autopilot note? — **"Nest — compose, don't touch"**

### ⚑ The pair is the break-glass answer, and it retires the hardest open item in the partition

[[aws-as-the-authorization-spine]] §singleton called the succession path **"mandatory, and it is the
hard part"**: a non-exportable enclave key means a dead laptop loses the *role* permanently, and every
candidate fix had a real cost (an offline recovery key to physically protect; a quorum ceremony
needing a second party; AWS-side re-registration gated on root — itself blocked on finding-0232's
recovery-mailbox hardening).

⚑ **A second YubiKey, enrolled at the same ceremony and stored offsite, is that path — and it costs
none of the three.** It is the offline recovery key, except it is one the owner already has and one
whose private half cannot be extracted to be lost.

⇒ **Re-registering the node role becomes a YubiKey-authorized ceremony, not an AWS-root ceremony.**
That decouples succession from `finding-0232` entirely. The design note should state this, because it
means the singleton can now be built *before* the mailbox hardening lands, rather than behind it.

### ⚑ The pair also settles enclave-vs-YubiKey — they are not competing, they answer different questions

[[blessing-auth-gate]] leaned Secure Enclave for blessing (local, frequent, offline-capable) over
AWS MFA. With a physical pair in hand the partition from [[aws-as-the-authorization-spine]] resolves
cleanly, and the owner's "use the computer's enclave, use MFA tied to kms keys" is satisfied by
**both, at different layers**:

| factor | proves | portable? |
|---|---|---|
| **Secure Enclave**, `userPresence` | ⚑ **which node** — this machine is Ouroboros | **no, by design** — non-portability *is* the binding |
| **YubiKey** (pair), touch-to-sign | ⚑ **which human, present now** — the owner authorized *this* transition | **yes** — which is what makes it the succession path |

⇒ The enclave's non-portability stops being a liability the moment the YubiKey can re-authorize a new
enclave registration. **The two properties are complementary, not redundant** — and neither replaces
the other. ⚑ Note this also keeps [[blessing-auth-gate]]'s reasoning intact rather than overturning
it: blessing stays local/offline-capable, it just moves substrate from SEP to the token, gaining
survivability. AWS remains where the owner's own refinement put it — **unseal only, out of the
steady-state path.**

### Nesting — what "compose, don't touch" constrains

`dn-autopilot-and-delegated-blessing` (ratified) keeps authority over blessing *semantics*: the
code-bound-to-content-hash grant, the HMAC attestation tag, the halt list, the low-stakes predicate.
The new note supplies the **substrate** (hardware key) and the **representation** (the transition as a
first-class event). `bp-138` (AP5, grant as pure core, injection-only `SecretProvider` seam) and
`bp-139` (AP6, the ON switch) stay valid — ⚑ and bp-138's provider seam is exactly the injection point
a YubiKey signer plugs into, which is a good sign the nesting is real and not forced.

⇒ **Constraint for Fable:** where the two notes collide, the ratified one wins and the new note
records the collision rather than resolving it. `oq-0037` (who holds the autopilot MFA secret) is
parked, not answered, and the new note must not quietly answer it.

## ⚑⚑ OWNER RULING (2026-07-27) — act-based → sign-based, and the gates are NOT symmetric

> *"because we are shifting the focus to security and somewhat abandoning act-based security for
> sign-based security, and it goes hand in hand with the autopilot, some actions that need to be
> signed will never be automatable (ratification included), but from the start, we can say that
> proposed->ready does not have a signing requirement"*

**Act-based → sign-based names the whole shift precisely.** Hooks are act-based: they intercept an
*act* and ask "may you do this?" A signature is state-based: it asks "does this *state* carry a valid
warrant?" — answerable at any time, by anyone, offline, long after the act. ⚑ That is why the
registry can retire hooks rather than reimplement them: **a warrant travels with the artifact; an
interception exists only at the instant of the act.**

### The two owner-only gates split, and the line is principled

CLAUDE.md currently treats `draft→ratified` and `proposed→ready` as one category ("two blessing gates
are owner-only, by hand"). ⚑ **The ruling splits them, and the rationale generalizes:**

| gate | requires a signature? | automatable? | why |
|---|---|---|---|
| `draft → ratified` | ⚑ **yes** | ⚑ **never** — permanently | a judgement about **design**: semantic, effectively irreversible (ratified notes are agent-immutable), and it is what every downstream plan inherits |
| `proposed → ready` | ⚑ **no** | yes — this is what autopilot delegates | a judgement about **readiness**: mechanical, checkable, and **reversible** (`ready → proposed` costs nothing) |

⇒ The discriminator is **reversibility ∧ semantic depth**, not "is it a gate." That is the same axis
`ops/effect_catalog.py` already uses for effectors (β, blast radius), which is a good sign it is the
real one and not an ad-hoc split.

⚑ **Consequence for scope:** `bp-138`/`bp-139` (autopilot delegated blessing) are now *unblocked by
the signing work*, because the gate they automate is the one with no signing requirement. The
hardware key is needed for **ratification**, which autopilot will never touch. ⇒ **The two tracks are
independent and can proceed in parallel** — a materially better position than the nested reading
suggested, and worth stating in the note so Fable does not serialize them.

⚑ **And note what this protects:** ratification stays a human act *by design*, not by current
limitation. A later "the system got good enough to ratify its own design notes" argument is
foreclosed at the frame, which is the correct place to foreclose it (NN-9: the fixed points are
sacred).

## ⚑⚑ OWNER RULING (2026-07-27, post-ratification) — AUTH REPLACES RESTRAINT; THE REGISTRY DISPATCHES

> *"you can edit a ratified note all you want, if you can't auth, it won't matter, it won't [be] an
> acceptable document, and the central system dispatches the workers with claude sdk, which means
> the system enforces that way, no need to force the hand of an agent, as we've seen, it cripples
> them"*

⚑ **This is the act-based → sign-based shift carried all the way, and the design note did not carry
it far enough.** The note retired hooks but kept asking *"how do we stop the agent from writing
X?"* — a question that is still act-shaped. The owner's reading dissolves it:

| | act-based | sign-based, fully |
|---|---|---|
| the question | how do we stop the write? | ⚑ **is the result a document?** |
| an unauthorized edit is | a denied act | **an act with no warrant — a file, not an artifact** |
| what enforces | interception, mid-work | **the absence of a signature, at read time** |

⇒ **You cannot forge a ratified note by editing bytes, because ratification is a signed transition,
not a line in a file.** Editing it produces something the system does not recognize. No guard is
needed to prevent it, and a guard that tried would only cost the agent its hands.

### ⚑⚑ THE SECOND HALF IS ARCHITECTURAL — the registry is the DISPATCHER

The registry does not merely record; it **spawns the workers** (Claude SDK). That changes what
enforcement *is*:

- `write_scope` is not a rule the worker is told and checked against — it is **the permission set
  the worker is constructed with**.
- The role ceiling (A11.3) is not admission-checked — it is **the agent definition the dispatcher
  builds**.
- ⚑ The agent is never forbidden a path. **It is never given one.** Capability, not prohibition.

⇒ **This supersedes §2.6's `write_scope` decision in the ratified note.** That section weighed two
options — land-time admission (default) and worktree-as-scope (high blast radius) — and both still
*tell an agent no*, one during the work and one after it. Dispatch-time capability does neither, and
is strictly better than both: no mid-flight friction, no late discovery, no reliance on discipline.

⚑ **Tonight is the evidence for both halves.** Two builders held their write scope perfectly with
**no hook watching** — good discipline, and precisely the assurance level that should never have
been the mechanism. Meanwhile the hook layer that *did* force the agent's hand is the thing the
owner turned off because it *"cripples them."* The measured lesson: **restraint is not a control,
and forcing it is not free.**

⇒ **Amendment owed to `dn-typed-workflow-registry` §2.6** (and it relaxes §2.9's deadlock concern,
since a dispatcher that constructs workers is not a chokepoint that blocks them mid-flight). Drafted
alongside A11 — see `docs/inbox/amendment-A11-draft.md` §A11.3.

## ⚑⚑ THE LOOP CLOSES — write freely, resubmit for re-auth, the owner notarizes

> *"so you can write to the file, and you're allowed to resubmit for re-auth, which gets routed to
> me (through the system), and I'm on the other end, not claude, to approve, I interact with the
> system as my seal of approval, my notary"*

⚑ **Editing a ratified artifact is not a violation. It is a PROPOSAL, and it is self-announcing.**
The edit changes the content hash, which invalidates the signature that made it ratified. Nothing
had to detect the edit — the warrant simply stops matching, and the artifact drops out of
`ratified` by arithmetic. The agent then **resubmits for re-auth**; the system routes it to the
owner; the owner notarizes.

| | old model | ⚑ this model |
|---|---|---|
| ratified note | **agent-immutable** — the edit must be prevented | **agent-writable** — the edit invalidates its own warrant |
| what detects tampering | a hook diffing against HEAD | ⚑ **nothing needs to. The hash stops matching.** |
| an edited ratified note is | a violation to be blocked | **a proposal awaiting re-auth** |
| the gate | prevent the act | **withhold the signature** |

### ⚑ "Notary" is the right word, and it is sharper than "blessing"

A notary does not author the document and does not judge its contents. They attest that **the named
party actually signed it**. That is exactly what a hardware-key touch proves and exactly what
`draft→ratified` needs — which is why it is permanently un-automatable: ⚑ **a notary who is a
program is not a notary.** *"I'm on the other end, not claude"* is the whole security property, and
it means the auth channel must be structurally unreachable by any agent — the same
put-the-check-outside-the-thing-being-checked rule [[aws-as-the-authorization-spine]] already
established.

### ⚑⚑ THIS DISSOLVES THE A-SERIES AMENDMENT CEREMONY

The lettered amendment log (A1–A10, and the A11 drafted tonight) exists **only because ratified
notes cannot be edited.** Unable to change the text, the repo grew a parallel artifact that
describes the change it cannot make, plus a build plan to land it, plus a §1.1 explaining the
protocol.

⇒ **Remove immutability and the entire apparatus is unnecessary.** You edit the note. The warrant
lapses. You resubmit. The owner notarizes. **The event log IS the amendment history** — every prior
ratification, every lapse, every re-auth, in order, queryable.

⚑ **Which is the owner's opening ask arriving from the other direction:** *"audits are performed
using query algebra to uncover chain of events."* The amendment log was a hand-maintained,
prose-shaped, ceremony-laden cache of exactly that chain — the same defect as the resume brief
(§resume-brief above), in a different costume. Both dissolve into the same event log.

⇒ **Owed to the design note:** §2.5.1's "no unsigned path to `ratified`" is unchanged and correct,
but its framing of ratified artifacts as *immutable* should become *warrant-bearing* — the artifact
is mutable, the **warrant** is not transferable across a content change. And `bp-145`'s acceptance
should test the lapse-on-edit path, not only the no-unsigned-path-in.

⚑ **Tonight's A11 draft is therefore a transitional artifact**, correct under today's rules and
obsolete under the registry. Recorded so its successor is not mistaken for missing work.

## ⚑ WHERE THE NOTARY LIVES — the scheduler side of Ouroboros, "for now"

> *"that notary, is the scheduler side of ouroboros (for now..)"*

⚑ **This does not contradict §placement's "do not couple the registry to the daemon" — because the
notary and the registry are different components with opposite availability profiles**, and keeping
them distinct is what makes both placements right:

| component | needed when | placement |
|---|---|---|
| **registry** (store · minting · events · folds) | ⚑ **every agent action** — in a worktree, in CI, with the palace down | local file, no daemon (§placement) |
| **notary** (route the re-auth request · carry the signature back · record it) | ⚑ **only at auth moments** — rare, and by definition the owner is present | `scheduler/` is fine |

⇒ Auth is **out of the steady-state path**, which is the owner's own refinement from
[[aws-as-the-authorization-spine]] (*"aws only needed for unseals"*) applied to a second layer. A
scheduler outage stops *notarization*, not work — and blocking is the correct behaviour for the one
operation where blocking is correct. `[GROUNDED — same reasoning, same conclusion, different
component.]`

### ⚑⚑ THE CONSTRAINT THAT MUST BE PINNED — the notary is a COURIER, never an authority

*"I'm on the other end, not claude"* is the security property, and it survives only if the notary
**cannot sign**. It carries the request to the human and carries the signature back; the signing
capability lives in the YubiKey, physically outside every process.

⇒ Compromising the scheduler therefore buys an attacker **denial of service** — dropped, delayed or
reordered requests — and **never forgery**. ⚑ If the notary ever holds signing material "for
convenience," compromising the scheduler becomes compromising ratification, and Ouroboros becomes
able to bless its own design. That is the one line in this design that must not be crossed, and it
is worth writing into the note as an invariant rather than leaving as an implicit property.

`[INFERENCE]` The `(for now..)` reads as anticipating the notary's promotion to its own node — which
the courier constraint makes cheap, since a courier holds no secrets and can be relocated without
re-keying anything.

⇒ **Owed to the design note:** a §2.4 invariant — *the notary routes and records; it never holds
signing capability* — plus its falsifier: any code path by which the scheduler could produce a valid
transition signature without a hardware touch.

## ⚑⚑ THE HUB SEES ONLY HASHES — which is why it can live anywhere

> *"the scheduler can be any node in the system, it is not an agent, but it is another hub node, the
> scheduler can be deployed to AWS, claude agents submit their work through a client that enforces
> types, the client is the one that computes the hash of the doc, such that it sends that, not the
> file, it uses the hash to tell me the file with hash needs my seal, the claude agent produces the
> file into the local system as usual, but when I sign, you compare the hashes pre and post sign,
> pre needs to match, [post]'s hash is stored, this scheduler is not even the ouroboros scheduler,
> it performs document processing and routing"*

⚑ **The document never leaves the machine. Only its hash transits.** That is what makes the earlier
"scheduler side of Ouroboros" answer provisional and this one general — and it resolves the
placement question that has been circling all night.

### ⚑ It satisfies NN-11 structurally, not by policy

> *"The interface may transit a third party; the corpus never does."*

A hash **is not the corpus**. So a hub node in AWS — reachable from the phone, outside the house,
run by a third party — carries **zero content**. NN-11 is not "respected by configuration"; it is
unviolatable by the data flow. ⚑ This is the same standard the repo holds everywhere else: a
property is real when something *proves* it, and here the proof is that the hub has nothing to leak.

⇒ **And it makes "the notary is a courier, never an authority" a fact rather than a rule.** The hub
cannot judge a document's contents **because it structurally cannot see them.** The invariant pinned
in the section above stops needing enforcement — it is a consequence of the wire format.

### ⚑⚑ THE PRE/POST HASH COMPARISON IS A TOCTOU DEFENCE — name it as one

The subtle half, and it closes a real hole:

```
1. agent writes the file locally
2. client computes  hash_pre , submits ONLY that
3. hub → owner: "the file with hash_pre needs your seal"
4. owner signs
5. ⚑ re-hash the local file NOW → hash_post
6. hash_pre == hash_post ?  →  sign & store hash_post
                          ✗  →  REFUSE; the request is stale, resubmit
```

⚑ **Without step 5–6 there is a window between "please sign hash X" and the signature landing, in
which an agent can rewrite the file.** The owner would be signing content he never saw — a
time-of-check-to-time-of-use attack, and the highest-value one in the system, since its prize is a
forged ratification. The pre/post comparison closes it, and the failure mode is a stale request
rather than a silent bad signature.

⇒ It is also the **same arithmetic** as the re-auth loop (§above): a warrant binds to a content
hash, so any divergence — mid-ceremony or years later — lapses it. **One mechanism, three jobs:**
ratification, tamper-evidence, and TOCTOU defence.

### The layering this settles

| component | sees | where it may live |
|---|---|---|
| **client** — type enforcement, hashing, submission | ⚑ **content** | local, in-process with the agent |
| **store / event log** — source of truth | ⚑ **content** | local, no daemon (§placement, unchanged) |
| **hub** — document processing, routing, seal requests | ⚑ **hashes only** | **any node — AWS, a phone-reachable service, anywhere** |
| **notary** — the owner + hardware key | content, locally | outside every process |

⚑ **Explicitly NOT the Ouroboros scheduler.** Different concern (document routing, not job
execution), different data (hashes, not the corpus), different deployment. Conflating them would
re-couple workflow liveness to the model daemon — the mistake §placement was written to avoid.

### ~~THE HONEST TENSION — a hash cannot be read~~ ⚑⚑ CORRECTED BY THE OWNER — the hash is a POINTER, and the document is already PUBLISHED

> *"each document is not personal data, it is a document you produced that's already published, all
> you have to do is git checkout, find the file, compute hash, or from a hash (of course you also
> get metadata) you know 'when' to checkout (from what commit, that is), and if you can recompute
> the hash, you prove it, and design notes and plans actually SHOULD stay, because that's how you
> can do a safe lookup from ANYWHERE"*

**The orchestrator's "blind signing" tension above was wrong, and the error is worth keeping visible:
it assumed the hash was an opaque token. It is a content ADDRESS.** The document is already
committed and pushed — public, retrievable, and (with the metadata the hub carries) locatable to the
exact commit.

```
hub sends:  hash + metadata (commit ref, artifact id, type)
owner:      git fetch / view at that commit  →  recompute the hash
            match  → this is provably the document, byte for byte  → sign
            differ → do not sign
```

### ⚑⚑ THE PROPERTY THAT MAKES THIS STRONG — the retrieval path need not be trusted

Because the hash **is** the integrity check, it does not matter where the bytes come from: GitHub, a
mirror, a cached copy, a hostile network. A tampered document simply fails to recompute. ⇒ **The
owner can verify from anywhere, over anything, with no trusted transport** — the same property that
makes content-addressed storage work, applied to the blessing ceremony.

⇒ **This dissolves the tension rather than managing it. Informed consent does NOT require being at
the machine — it requires being able to retrieve and recompute.**

### ⚑ AND IT REFRAMES THE EXPORT — files in git are the VERIFICATION SUBSTRATE

*"design notes and plans actually SHOULD stay"* is not a legacy concession to `nvim` and ingestion.
⚑ **Published files are what make a hash resolvable at all.** A registry-only artifact with no
committed form is a hash pointing at nothing retrievable from outside the machine that holds it.

⇒ D4's ground 3 (*"the artifact chain requires typed files"*) was **more right than §A11's reading
credited** — it has a justification D4 itself never stated: files-in-git are the substrate that makes
remote verification possible. The A11 draft should be updated to say so, and the export stops being
a convenience with a ratchet attached and becomes **load-bearing for the auth loop**.

### ⚑ THE BOUNDARY THAT MUST BE STATED — "already published" is a PRECONDITION, not a property of all artifacts

The whole argument rests on *"not personal data … already published."* True of design notes, build
plans, findings, journals. ⚑ **Not true of anything carrying corpus or vault content**, and the hub's
metadata (title, id, commit ref) leaks even when the payload does not.

⇒ **Invariant owed to the design note:** only artifact types that are *published by construction*
may transit the hub. A future document type that touches the vault does **not** get this channel by
default, and the type system — the client's job — is where that is enforced.

### ⚑ CONSEQUENCE — "blessings stay at the keyboard" may now be relaxable

`[INFERENCE — owner ruling required; the standing rule is explicit and this does not override it.]`
The rule exists because remote signing was blind. It is no longer: content is retrievable,
identity is provable, and a YubiKey 5 NFC / 5C can sign against a phone. The remaining requirement is
that the owner actually *performs* the recompute rather than trusting the notification — which is a
ceremony design question, not a security impossibility.

⇒ Worth an explicit ruling rather than silent drift: the rule was correct for its reason, and the
reason has changed.

⇒ **Owed to the design note:** the hub's wire format (hashes only) as an invariant with its
falsifier — *any hub payload carrying document content is a defect, not an optimization* — and the
pre/post comparison as a named acceptance criterion on `bp-145`.

## ⚑⚑ LANDING IS AN AUTHORIZATION ACT — no local main-merges, a merge train, an MR queue

> *"machine merges are never allowed, builds now open a PR with the proper docs and reasoning, I
> merge from github, removes you from that loop too"* · *"by this, I mean local main-merges do not
> happen locally"* · *"we perform a merge train"* · *"if a merge is 'staged', everyone rebases"* ·
> *"that's how we solidify the MR queue"*

⚑ **The same move as the notary, applied to code.** A design note becomes ratified by a hardware
signature; a branch becomes main by the owner pressing merge. In both cases **the agent is removed
from the authorization loop entirely** — not restrained within it.

| | design artifacts | code |
|---|---|---|
| the seal | hardware-key signature over a content hash | ⚑ **the GitHub merge button** |
| the agent may | write, propose, resubmit | **push a branch, open a PR** |
| the agent may not | make a warrant | ⚑ **land anything on main** |

⚑ **Scope of the rule, per the owner's own narrowing:** it is *local main-merges* that are
forbidden — `git merge <build-branch>` into main on this machine, never. Orchestrator commits of
captures, findings and seat files directly to main are a different act and are unaffected.

### The train, and why STAGED is the right trigger

- PRs land **in sequence**, never independently.
- ⚑ **When a merge is *staged* — queued, not yet landed — every other active branch rebases.**

This is **earlier** than the existing rule in the delegate skill (*"when anything merges to main,
every ACTIVE builder merges main into its branch"*). Staging-as-trigger removes the window in which
a branch is still building on a base that is already known to be stale. ⇒ The skill's text is owed
an update; the owner's version strictly dominates it.

⇒ **That is what "solidifies the MR queue":** an ordered queue whose members are continuously
rebased onto the head of the train is one where *"it passed"* keeps meaning something. Without it,
green is measured against a base that no longer exists by the time the PR lands.

### ⚑ The MR queue is event-log-shaped — it is not a second mechanism

`staged → rebased → landed` are **events on an artifact**, ordered, append-only, with a warrant on
the terminal one. That is the registry's native shape, not an adjacent system needing integration.
⇒ *"audits via query algebra over chain of events"* covers the merge history for free, exactly as it
covers the amendment history (§above).

### ⚑ IT IS CONVENTION TODAY, NOT A CONTROL — verified this pass

`gh api repos/:owner/:repo/branches/main/protection` → **404, "Branch not protected."** Nothing
prevents a local merge to main and a push. The rule currently rests on the agent's discipline, which
is exactly the assurance level tonight proved is not a mechanism.

⇒ **The structural version is branch protection** (require a PR, forbid direct pushes to main), and
it is an owner act — it constrains the owner's own tooling as well as the agent's, and it would
change how orchestrator doc-commits reach main. `[INFERENCE]` A ruleset that requires PRs for
*merges* while leaving direct commits alone is the shape that matches the narrowing above; whether
GitHub can express exactly that split is worth checking before promising it.

## ⚑⚑ THE DEPLOY PATH — plan is proposal, apply is CI, and the agent never holds AWS

> *"the point here, you can generate the plan, but can't deploy with terraform, and github gives
> unlimited CI minutes for public repos, and github has well understood integration with amazon"*

⚑ **This is the third instance of tonight's single pattern**, and the one that finally makes NN-3
(*"the model advises; code acts — no model holds a shell, raw secrets, or direct infra mutation"*)
structural rather than procedural:

| layer | the agent produces | the warrant | who acts |
|---|---|---|---|
| design | an edited note | hardware signature | the owner notarizes |
| code | a branch + PR | the merge button | the owner merges |
| ⚑ **infrastructure** | ⚑ **`terraform plan`** | **the same merge** | ⚑ **GitHub Actions applies** |

⇒ **`plan` : `apply` :: proposal : authorization.** Terraform already ships the split this whole
design has been reinventing all night — a plan is a *reviewable statement of intent* that changes
nothing, and apply is the authorized act. Using it as-is beats building an equivalent.

### ⚑ The agent holds NO AWS credentials — that is the whole point

`apply` runs **in CI, not on this machine**, so there is nothing to scope, rotate, or leak locally.
`[INFERENCE — the "well understood integration" is GitHub Actions OIDC → an AWS IAM role trusted by
this repo: short-lived, assumed per-run, no long-lived keys stored even as Actions secrets. Verify
the trust-policy shape before building; do not build from this sentence.]`

⚑ **This also retires a standing exception.** `mind-palace deploy` has been *"the ONE owner-in-loop
gate, never run autonomously"* — a rule held by discipline. Under merge-triggered deploy it stops
being a command anyone could run and becomes a **consequence of an authorization already given**.
The rule does not need to be obeyed; it becomes unexpressible locally.

### Economics — verified

`gh api repos/:owner/:repo --jq .private` → **`false`**. The repo is public, so Actions minutes are
unmetered. The CI-as-the-apply-plane design costs nothing, which is why it can be adopted now rather
than budgeted for.

### ⚑ THE COST OF PUBLIC, AND IT IS NOT ZERO — plan output leaks topology

A public repo means **`terraform plan` output posted to a PR is world-readable**. Plans routinely
disclose account ids, resource ARNs, bucket and function names, security-group rules — the shape of
the infrastructure, even when no secret value appears.

⇒ **A decision is owed, and it should not be made by default:**
- **(a)** accept it — the topology is public, and the security model rests on credentials and OIDC
  trust policies rather than on obscurity;
- **(b)** post the plan as a **check summary or artifact** rather than a PR comment, narrowing who
  sees it;
- **(c)** redact — brittle, and a redactor that silently misses a field is worse than (a).

`[INFERENCE]` (a) is defensible and probably correct — this repo already publishes its design notes,
findings and account-level decisions, and hiding topology while publishing the design that describes
it is not a coherent boundary. ⚑ But it should be *chosen*, because the first plan output posts
whatever it posts and cannot be unpublished.

⚑ Note this composes with §"the hash is a content address": the *reason* remote verification works
is that these artifacts are already public. Publicness is load-bearing for the auth loop and a leak
surface for infrastructure — the same property, cutting both ways, and worth naming as such rather
than treating each in isolation.

## ⚑⚑ THE PR IS THE AUDIT VENUE — and the deliberation becomes part of the record

> *"the reviewers can be the auditors and me, I can also give feedback on the PR, so even our
> messages and feedback is public, a more true representation of the ecosystem we have built"*

⚑ **The audit finally gets a home that matches its shape.** The delegate skill already demands that
an audit be *"a named artifact, not a vibe"* — an independent pass at the reviewer's tier, recorded
so the board's `audit: present/owed` flag has a basis. A PR review **is** that, natively: attributed,
timestamped, anchored to the exact lines, and threaded against the diff it judges. No separate
artifact has to be invented to carry it.

### ⚑ And it makes the DELIBERATION public, which nothing else in the chain does

Today the repo publishes conclusions — design notes, findings, seals — while the *arguing* stays
invisible: what the auditor doubted, what the builder answered, where the owner overruled. On a PR
that becomes the record. ⇒ *"a more true representation of the ecosystem"* is exact: the artifact
chain currently shows the **outputs** of a deliberative system without showing that it deliberates.

### ⚑⚑ THE UNPRICED PAYOFF — it is `finding-0276`'s identity work paying a second time

A review record is only legible if the reviewers are **distinguishable**. With one identity, a PR
authored, reviewed and merged by `ascalva` is an unbroken tautology — it records that a person agreed
with themselves.

| with one identity | with separate identities |
|---|---|
| author `ascalva`, reviewer `ascalva`, merger `ascalva` | author `builder-bot`, auditor `auditor-bot`, approver `ascalva` |
| ⚑ proves nothing | ⚑ **a real chain of custody, publicly verifiable** |

⇒ The identity separation was justified in `finding-0276` purely as merge-prevention. **This is a
second, independent reason to want it** — and arguably the more durable one, since it is what makes
the audit trail mean anything to a reader who is not the owner.

### ~~THE TRAP — a PR thread is a transcript that must be tracked~~ ⚑⚑ OWNER CORRECTION — THERE IS NO THIRD PLACE

> *"what survives is the product, not us talking, us talking/transcripts never get uploaded, they
> live in the strata as well, but briefs didn't, in the same way how PR feedback doesn't need to be
> tracked, the builder will publish its code changes with an appropriate commit message that
> explains the change"*

**The orchestrator's reading above was wrong in its remedy.** It correctly noticed a PR thread is a
transcript, then concluded the transcript must be *captured*. That is backwards, and it would have
rebuilt the resume brief in a new venue.

⚑ **The system has exactly two homes, and nothing lives between them:**

| home | holds | fate |
|---|---|---|
| **product** — git, public | design notes · plans · findings · code · ⚑ **commit messages** | survives, permanently |
| **strata** — Ouroboros, local, private | transcripts, chat, deliberation | ⚑ **ingested as memory, never published** |
| ~~in between~~ | ⚑ **nothing** | ⚑ **rots** |

⇒ *"no decision lives only in a transcript"* does **not** mean *record the transcript*. It means
**the decision must be visible in the product.** A commit message that explains the change **is** the
decision landing in an artifact. The argument that produced it needs no preservation — it is already
in the strata, where talking belongs.

### ⚑⚑ AND THIS IS THE RESUME BRIEF'S AUTOPSY, IN ONE LINE

> *"transcripts … live in the strata as well, but briefs didn't"*

⚑ **The brief was homeless.** Not product (it described work rather than being it), not strata (it
was authored, not ingested). It occupied the in-between, and the in-between has no keeper — so it
went stale between the writing and the reading, every time. ⇒ The §resume-brief diagnosis above
("a hand-maintained cache of a derivable fact") was right about the *mechanism*; **this is the
structural cause**, and it generalizes: **anything that is neither product nor strata will rot,
whatever discipline is applied to it.** That is the test to apply to any future artifact before
inventing it — including PR-feedback tracking, which fails it.

### ⚑ THE COST, AND IT IS REAL — the commit message becomes load-bearing

If deliberation is deliberately ephemeral, **the commit message is the only surviving record of
*why***. That raises the bar on it considerably: it stops being a label for a diff and becomes the
carrier of the reasoning the review produced.

⇒ The discipline is therefore **not** "track the feedback" but ⚑ **"the commit message must carry
what the feedback changed"** — what the auditor questioned, what the answer was, what the builder
altered as a result. A commit reading `fix: address review comments` **destroys** the record that
this design just decided to keep in exactly one place.

`[INFERENCE]` This is the strongest argument yet for CONVENTIONS §Commits being enforced rather than
encouraged — under the old model a thin commit message was recoverable from the surrounding
artifacts; under this one it is the only copy.

### What the registry still absorbs

The review **events** (`reviewed` · `approved` · `merged`) remain events on an artifact and belong in
the log — ⚑ but as **occurrence, not content**: *that* an audit happened, by whom, with what verdict.
Not what was said. ⇒ The board's `audit: present/owed` flag gets its basis without the system
becoming a transcript archive.

⚑ Amendments · merges · audit-occurrence — three ceremonies, one event log. The convergence holds; it
is the *contents* of the deliberation that were never the log's business.

### Open, and not to be defaulted

`[INFERENCE]` **Public review means self-disclosed defects are public in real time.** For a repo
already public this is mostly consistent — but an audit that surfaces a *security* weakness would be
published before it is fixed. Worth a rule (private advisory for that class, public for everything
else) rather than discovering it the first time an auditor finds something sharp.

## ⚑⚑ THE FULL PIPELINE — two merge stages, six actors, and where each authorization lives

> *"merges happen at least in two stages: draft->ratify, and on PRs, the suborchestrator … mints the
> plans, merges its changes, and then opens the PR(s), from there, I can spawn an auditor (or the
> sub-orch does) to then review the request and comment directly in the PR, and once feedback cycle
> finishes, it gets raised for me to approve and merge, only then can a track be deskchecked, when
> ALL of its designs are merged (unless it's one of the long running tracks like workflow, that one
> can be a deskcheck after each design->merge)"*

| # | stage | actor | the act | warrant |
|---|---|---|---|---|
| 1 | `draft → ratified` | ⚑ **owner** | notarize | hardware signature over a content hash |
| 2 | graduate + build | sub-orchestrator, builders | mint plans, write code | none — proposals |
| 3 | ⚑ **integrate** | sub-orchestrator | assemble the PR | none — still a proposal |
| 4 | audit | auditor agent | review comments **in the PR** | none — advisory |
| 5 | `approve + merge` | ⚑ **owner** | merge (⇒ deploy) | the GitHub merge button |
| 6 | deskcheck | ⚑ **owner** | track verdict | ⚑ **unspecified — see below** |

### ⚑ "The sub-orchestrator merges its changes" does NOT contradict "no local main-merges"

Worth stating because the two sentences look opposed. The sub-orchestrator is the **integrator**:

```
builder branches  ──merge──▶  sub-orch integration branch  ──PR──▶  main   (owner merges)
```

Builders merge into **it**, never into `main`. What the sub-orch merges is *its own* assembly; what it
opens is a proposal. ⇒ The forbidden act is specifically `git merge <branch>` **into main, locally**
— unchanged, and this hierarchy is fully consistent with it. ⚑ It also gives the `finding-0271`
collision a natural resolution point: **integration is where id conflicts surface and are fixed**,
one level below the owner's attention, which is where it belongs.

### ⚑⚑ DESKCHECK IS NOW THE THIRD OWNER GATE — and the only one without a venue

Ratify has a venue (the signature). Merge has a venue (the PR). **Deskcheck has neither**, and it is
the gate that decides a track is actually done — the one the owner has already ruled is never
self-declarable (`deskcheck-discipline`; the dreamer/reference/K1 slips).

⚑ The design note **parked** deskcheck-verdict signing (*"unsigned, owner-by-hand as today"*). That
default was reasonable when it stood alone; with stages 1 and 5 both becoming warranted acts, an
unsigned third gate is now the **odd one out**, and it is the gate guarding the strongest claim in
the system ("this track is done"). ⇒ **The parked decision deserves re-opening**, not because
anything broke, but because the surrounding structure changed underneath it.

### The new gating rule, and its exception

> **A track may be deskchecked only when ALL of its designs are merged** — *except* long-running
> tracks (`workflow`), which deskcheck **after each design→merge**.

⚑ The exception is load-bearing, not a convenience: `workflow` never reaches "all designs merged"
because it is the track that keeps redesigning the system that builds it. Without the carve-out its
deskcheck is unreachable by construction — ⚑ and an unreachable gate is a gate that quietly stops
being applied, which is how *"DONE ≠ sealed"* gets violated without anyone deciding to violate it.

⚑ **And "all of its designs are merged" is a QUERY over the event log** — not a status field anyone
maintains. That is the **fifth** ceremony the log absorbs (amendments · merges · audits · reviews ·
now deskcheck-eligibility), and the fifth time the owner's opening ask arrives from a direction it
was not aimed at.

### ⚑ TWO RISKS IN THE CYCLE, stated so they are designed rather than discovered

1. ⚑ **The feedback cycle has no termination condition.** auditor → builder → auditor → … can loop,
   and each round costs a full agent. It needs a bound: *N* rounds, or "auditor declares clean", or
   escalate to the owner with the disagreement stated. `[INFERENCE]` Escalation-on-disagreement is
   probably right — a second opinion the owner never sees is a cost with no decision attached.
2. **If the sub-orchestrator spawns its own auditor**, the audit is independent of the *builder* —
   which is the property the delegate skill actually requires — but **not** of the orchestrator that
   scoped the work. For a spec-fidelity audit that is fine; for anything questioning the
   *decomposition itself*, the auditor is grading its own commissioner. ⚑ Worth an explicit rule
   rather than an assumption, since the failure is silent and reads as agreement.

## ⚑⚑ INGESTION MOVES TO THE EDGE, AND READS ONLY `origin/main`

> *"ingestion is now an edge agent, it only ingests from github remote/main directly, you can't
> accidentally slip something on the local main"*

⚑ **The property this buys: the corpus contains only what survived the merge gate.** Ingestion source
becomes `origin/main`, which is by construction the set of artifacts the owner approved. The
knowledge graph stops being "whatever was on this disk" and becomes "what was authorized."

### ⚑ Measured tonight — the accident is not hypothetical

`git config core.hooksPath` → `.githooks`, and `.githooks/post-commit` runs `scripts/snapshot_code.py`
on **every local commit**. Observed across this session: the code-sensor ledger moved
**1330 → 1346** — ⚑ **sixteen ingestions, every one from local `main`, none gated by anything.**

That included commits nobody reviewed, and both captures where the orchestrator reasoned wrongly
before being corrected (§the-hash-is-an-address, §there-is-no-third-place). ⇒ **Two wrong readings
entered the corpus as knowledge**, and only the *later* correction entered too — the strata now holds
both with nothing marking which superseded which. The owner's rule closes exactly this.

### ⚑ It is the LAST act-based hook in the loop, and it goes the same way as the others

`.githooks/post-commit` is a git hook rather than an agent hook, so it survived tonight's disabling
untouched — but it is the same shape: **an act (commit) triggering a consequence (ingest), on the hot
path, with no warrant between them.** Replacing it with an edge lane triggered by *merge to
`origin/main`* is act-based → sign-based applied one final time. ⚑ The pattern has now consumed every
hook in the system.

### ⚑⚑ THE BOUNDARY THAT MUST BE DRAWN CAREFULLY — NN-2

**NN-2: *"Network and private data never share a component. Only `edge/` touches the network; it
never reads the vault."*** ⚑ *"Ingestion is an edge agent"* is safe or fatal depending on where the
line falls:

| shape | NN-2 |
|---|---|
| ⚑ **edge FETCHES from GitHub → hands bytes inward → core INGESTS and writes the stores** | ✅ the boundary holds |
| edge fetches **and** writes embeddings/stores itself | ⚑ **VIOLATION** — one component touching the network and the private stores, exactly what NN-2 forbids |

⇒ **The edge agent is a fetcher, not an ingester** — the same courier/authority distinction already
pinned for the notary (§above), arriving independently at the same shape. `[INFERENCE]` The naming
matters more than usual here: calling it "the ingestion edge agent" invites the fatal shape; calling
it **"the fetch lane"** does not.

### ⚑⚑ THE STRONGER ARGUMENT — a commit is a MOMENT, a merge is a UNIT

> *"we only merge when the product that we want to merge is ready, it ingesting on EVERY SINGLE
> COMMIT is difficult"*

⚑ The section above framed per-commit ingestion as an **authorization** problem. That under-weights
it. The bigger defect is **what gets ingested**: a commit is a *moment* in a working process — half-
finished code, a refactor that gets reverted two commits later, a reading that turns out to be wrong.
A merge is a *coherent unit* that someone decided was ready.

⇒ **Ingesting commits means ingesting moments; ingesting merges means ingesting units.** The corpus
is supposed to hold knowledge, and an intermediate state is not knowledge — it is work in progress
wearing knowledge's clothes.

### ⚑ And the retrieval pathology is concrete, from tonight

This one brainstorm was committed **ten times** in a single session, each version a superset of the
last. Under per-commit ingestion the corpus now holds ~10 near-duplicate embeddings of one evolving
document — ⚑ and the early ones contain the two readings that were subsequently *corrected*
(§the-hash-is-an-address, §there-is-no-third-place).

⇒ Two failure modes, both live:
1. **Near-duplicate flooding.** A single night's drafting can dominate a retrieval result set with
   ten versions of one idea, crowding out genuinely different sources. `[INFERENCE — the source-set
   relation (`core/stores/sourceset.py`, group-by-digest) exists precisely to handle multi-version
   sources and may already mitigate this; whether it does at *retrieval* rank is worth measuring
   rather than assuming.]`
2. ⚑ **Superseded content persists as peer knowledge.** The corrected readings are in there
   alongside their corrections, with **nothing marking which won.** A future retrieval can surface
   the refuted version with equal standing — which is the *"a claim becomes true by being stated"*
   defect, arriving through the ingestion lane instead of through an artifact.

⚑ Merge-triggered ingestion fixes both at once, and for the same reason: **the merge is the moment
someone decided the thing was coherent.** Everything before it is drafting, and drafting belongs in
the strata (§there-is-no-third-place) — not in the corpus.

### The bonus property — the corpus becomes reproducible

Ingesting from public, immutable git history means **what was ingested can be reconstructed by
anyone**, from the same source, and checked. A corpus built from a local working tree is
unreproducible by construction — nobody else ever had those bytes. ⚑ This is the same property the
hash-as-content-address gives the auth loop (§above): **public + immutable = independently
verifiable**, and it is now load-bearing in two places.

## OPEN — remaining owner rulings, not guesses

1. **Sequencing against tomorrow's keys.** ⚑ Recommendation: **do not block key onboarding on the
   registry.** Signing a transition works against today's markdown+git world (the pre-image hash is
   just harder to obtain). Onboarding + the signing primitive can land first; the registry adopts it.
2. **`write_scope` enforcement level** — land-time admission vs worktree-as-scope, per-unit (§hooks).
3. **Does the registry get its own knowledge graph, or is ingestion enough?** The owner allowed
   either. `[INFERENCE]` An event log with a query algebra may already *be* the administrative graph,
   making a second one redundant.
4. ⚑ **What is enrolled on the YubiKeys, and where does the second one live?** Both keys must be
   enrolled at the same ceremony — a key added later cannot sign for the period before it existed —
   and the offsite location is a real decision, not a detail. `[INFERENCE]` PIV slot 9c (digital
   signature, PIN+touch policy) is the conventional home for a signing key; FIDO2/`hmac-secret` is
   the alternative if the design wants challenge-response rather than raw signatures.
