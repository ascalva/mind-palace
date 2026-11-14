---
type: design-note
id: dn-typed-workflow-registry
track: workflow
status: ratified
created: 2026-07-27
updated: 2026-07-27
links:
  - docs/brainstorms/the-typed-workflow-registry.md
  - docs/brainstorms/blessing-auth-gate.md
  - docs/brainstorms/aws-as-the-authorization-spine.md
  - docs/brainstorms/the-identity-foundation.md
  - docs/design-notes/dn-autopilot-and-delegated-blessing.md
  - docs/design-notes/agent-workflow.md
  - docs/design-notes/attestation-layer.md
  - docs/design-notes/dn-role-state-and-scoped-handoff.md
  - docs/brainstorms/study-not-product.md
  - scripts/handoff.py
  - .claude/hooks/_lib.py
supersedes: null
superseded_by: null
warrant: null
---

# The typed workflow registry: act-based security retired for sign-based security

> Filed by the chat agent as `draft` (chat-side protocol, §8). Ratification is a
> hand edit by the owner — no command performs it, and `gate-guard` denies any
> agent attempt (§10). `/graduate` refuses this note until `status: ratified`.
>
> **This note nests inside `dn-autopilot-and-delegated-blessing` (ratified).**
> Where the two collide, the ratified note wins; every collision is *recorded*
> here (§2.5.3), never resolved. It also proposes amendments to
> `dn-agent-workflow` (ratified) — under §2.10's revision protocol those are
> direct edits whose PRs the owner merges; the lettered A-series ceremony this
> header previously invoked is dissolved (§2.10).
>
> **Revision notice (2026-07-27, post-ratification — the warrant is lapsed).**
> This note was ratified early on 2026-07-27 and the owner then ruled for several
> hours past it. It is edited directly under the owner's own re-auth model:
> editing a ratified artifact is a *proposal*, not a violation — the edit lapses
> the warrant that made it ratified, and the author resubmits for
> re-authorization [GROUNDED docs/brainstorms/the-typed-workflow-registry.md:307-324].
> The pull request carrying this revision is the resubmission; the owner's merge
> is the re-ratification. `status: ratified` is deliberately untouched — status
> is the registry's business, not this file's (§2.3); what lapsed is the warrant,
> and no field edit can express that.

## 1. Purpose and scope

### 1.1 What this note decides

One mechanism, presented as one note because the brainstorm's synthesis showed the two
halves are the same primitive [GROUNDED docs/brainstorms/the-typed-workflow-registry.md:38-58]:

1. **A typed workflow registry** — design notes, build plans, findings, journal entries as
   typed entities whose primary representation is an **append-only event log**; current
   state is a fold over that log; submission returns a ref; minting is serial; submission
   is idempotent under retry (§2.2).
2. **The frontmatter/prose split** — the registry owns state, identity, relations,
   transitions, and ordering; the markdown file owns prose; the registry **exports** to
   git under an idempotence pin, and CI ratchets `export == working tree` (§2.3).
3. **Sign-based transitions** — a privileged transition is a signed event over
   `(id, from_status, from_content_hash, to_status, to_content_hash)`; the signing
   substrate is a pair of YubiKeys (owner ruling, 2026-07-27); the verification layer
   reuses the existing `core/attestation/` + `core/verdict/` primitives rather than
   minting a third (§2.4).
4. **The gate asymmetry** — `draft→ratified` requires a signature and is never
   automatable, foreclosed at the frame; `proposed→ready` has no signing requirement and
   is what autopilot delegates; the discriminator is reversibility ∧ semantic depth
   (owner ruling, 2026-07-27) (§2.5).
5. **Hook retirement** — the disposition of all six agent hooks, guarantee by guarantee,
   including the two that do not move cleanly (§2.6).
6. **Resume-brief deprecation** — the structural diagnosis, the replacement (state
   distributed across units, reconstructed by query; the journal narrows to judgement),
   and the full list of artifacts that must change (§2.7).
7. **Placement and the deadlock question** — local, single-file, no-daemon, machine-level,
   outside the repo; reads never block; a specified degraded mode; a surviving escape
   hatch (§2.8, §2.9).
8. **The surrounding pipeline, under the same frame** (added in the 2026-07-27
   post-ratification revision; each entry is a recorded owner ruling, not new design):
   the hub that carries pointers and never content, and the notary that routes and never
   signs (§2.4.5–2.4.6); the revision protocol that replaces the A-series amendment
   ceremony (§2.10); landing, audit, and deploy as authorization acts (§2.11); merge-gated
   edge ingestion (§2.12); deskcheck gating (§2.13). Kept in this one note deliberately:
   its subject is how work moves, and these are the same movement governed by the same
   act-based→sign-based frame.

**Reprioritization, stated here rather than buried (owner, 2026-07-27).** The corpus is a
self-map of the owner's reasoning, so **corpus integrity is identity integrity**. The
merge-gated ingestion lane (§2.12) is therefore not signal-to-noise hygiene — it prevents a
defective agent from writing into the owner's self-model. Measured instance: per-commit
ingestion put two *later-corrected* orchestrator readings into the corpus, unmarked,
retrievable with equal standing to the owner's own thinking
[GROUNDED docs/brainstorms/study-not-product.md:59-70; the ledger movement is measured at
docs/brainstorms/the-typed-workflow-registry.md:824-833]. This changes the work's priority,
not just its rationale.

The through-line, named by the owner and adopted here as the design's organizing frame:
**the shift from act-based security to sign-based security**
[GROUNDED docs/brainstorms/the-typed-workflow-registry.md:222-233]. A hook intercepts an
*act* and asks "may you do this?" — an answer that exists only at the instant of the act,
on the hot path, and that clogs the machinery it protects. A signature is a property of
*state*: "does this state carry a valid warrant?" — answerable at any time, by anyone,
offline, long after the act. The registry can retire hooks rather than reimplement them
because **a warrant travels with the artifact; an interception exists only at the moment
of interception.** What this dissolves, and what it honestly does not, is §2.6's table.

### 1.2 Non-goals — read these aloud at ratification

1. **The identity foundation is not designed here.** Proton tiers, the offsite envelope,
   the DNS pass, the key-enrollment ceremony are owner ceremony, captured in
   `docs/brainstorms/the-identity-foundation.md`. This note *consumes* the ceremony's
   output (two enrolled YubiKeys) and constrains it in exactly one place: both keys must
   be enrolled before key #2 goes offsite (§2.4.4). Nothing else about it is decided here.
2. **`oq-0037` (who holds the autopilot MFA secret) stays parked.** This note does not
   answer it, quietly or loudly. Where the registry touches the autopilot grant flow, the
   collision is recorded in §2.5.3 and left for the owner.
3. **Blessing *semantics* are untouched.** The code-bound-to-content-hash grant, the HMAC
   attestation tag, the halt list, the low-stakes predicate P1–P5 all remain
   `dn-autopilot-and-delegated-blessing`'s authority. This note supplies substrate
   (hardware key) and representation (the transition as a first-class event) only.
4. **`draft→ratified` is never automatable — foreclosed at the frame, not deferred.**
   Reaffirmed from the ratified note's non-goal 2 and strengthened: the registry's schema
   itself has no unsigned path to `ratified` (§2.5.1), so a later "the system got good
   enough" argument has no mechanism to attach to (NN-9: the fixed points are sacred).
5. **The corpus embedding pipeline is unchanged; its *source* is not.** Workflow
   *outputs* (design notes, findings, plans) remain ingestable by Ouroboros exactly as the
   markdown exports they already are — but the lane that reads them moves to `origin/main`
   only, merge-gated (§2.12; a change from this section's ratified text, which called the
   boundary unchanged). The registry's administrative event log is **not** part of the
   semantic corpus and is not embedded. [INFERENCE — the owner allowed either ("its own
   knowledge graph if possible, or ouroboros could still work"); this note takes the
   smaller reading and parks the administrative-graph question (§Parked) rather than
   deciding it.]
6. **No cloud service, no daemon coupling, no core residency** — argued, not just
   asserted, in §2.8.
7. **Historical prose is not migrated.** Migration moves frontmatter *fields* into the
   registry; the §1..§9 bodies of every existing artifact stay byte-identical markdown.
   [INFERENCE — nothing in the brainstorm demands body migration; stating it as out of
   scope so the migration plan cannot silently balloon.]
8. **The effector layer (Track G) is untouched.** The registry governs workflow
   artifacts, not world-actions; `ops/effect_*` keeps its own gate machinery.
   [INFERENCE — the shared reversibility axis (§2.5.2) is an analogy, not a merger.]

## 2. Principles / decision

### 2.1 Act-based → sign-based: what the shift actually buys

Three properties, each currently absent:

- **Illegal transitions become unrepresentable, not intercepted.** Today `status:` is a
  line in a file any shell can write; three layers of guard (pre-hoc deny, Stop-gate diff
  scan, untracked-blessing scan — `_lib.py:480-511, :587-651`) exist to catch the writes.
  In the registry, status is not file-resident at all: there is nothing to hand-edit, so
  `gate-guard`'s entire reason to exist dissolves rather than moves
  [GROUNDED docs/brainstorms/the-typed-workflow-registry.md:73-75].
- **The transition becomes an object.** `blessing-auth-gate` already ruled: sign the
  transition, not the act — `sig over (id, from_status, from_content_hash, to_status,
  to_content_hash)` [GROUNDED docs/brainstorms/blessing-auth-gate.md:27-37]. In the
  markdown world the pre-image is an archaeological claim reconstructed from git diffs
  (the whole reason `oq-0040` was open). In an event log the transition is a row: the
  from-nothing blessing is unexpressible because there is no event without a pre-image.
- **Audit becomes a query, not a reconstruction.** The event log *is* the chain of
  events; "who blessed what, when, over which content" is a fold, not forensics. This is
  the owner's "audits via query algebra" ask satisfied by representation rather than by
  tooling [GROUNDED docs/brainstorms/the-typed-workflow-registry.md:28, :56].

What the shift does **not** buy, stated now so §2.6 cannot overclaim: a signature cannot
guide a *mid-flight* act (the compaction-marker problem), and a store cannot stop a write
to an arbitrary path (the write_scope problem). Both are handled explicitly, neither is
claimed to dissolve.

### 2.2 The registry: entities, events, folds, refs

**Typed entities.** The existing artifact taxonomy, unchanged in meaning: design note,
build plan, finding, journal entry — plus the relations today's frontmatter carries
(`track`, `design_ref`, `depends_on`, `links`, `supersedes`, `warrant`, `write_scope`).
Each entity's state machine is the one `dn-agent-workflow` §3 already ratified; the
registry changes *where the state lives*, not what the states are.

**Append-only event log as primary representation.** Every mutation is an event:
`minted`, `transitioned`, `related`, `content-landed` (a prose revision, recorded as a
content hash — the prose itself stays in the file), `parked`, `sealed`. Current state is
a **fold** over an entity's events. Nothing is ever updated in place; a correction is a
new event. This is the same append-only, attributable, typed-and-gated write-channel
doctrine the workflow already applies to journals and findings
[GROUNDED docs/design-notes/agent-workflow.md §2(3)] — applied, at last, to status itself.

**Submission returns a ref.** An agent submits a typed payload ("mint me a finding with
this frontmatter"); the registry validates the type, assigns the ID, appends the event,
and returns the ref (`finding-0271`). The agent then writes prose to the exported path.
The ref is the identity; the file is the body.

**Serial minting closes a live race.** [GROUNDED — verified in-tree this pass: no script
anywhere allocates workflow-artifact IDs. `scripts/mint_ids.py` mints *corpus note* ids
(`core/ingest/mint_ids.py`, bp-034) and is unrelated; `bp-NNN`/`finding-NNNN`/`dn-` ids
are chosen by an agent eyeballing the highest existing number. The brainstorm's own
verification pass found the same
(docs/brainstorms/the-typed-workflow-registry.md:143-149).] Two parallel worktree
builders *will* pick the same finding number; the collision surfaces as a merge conflict
when paths collide and **silently** when they do not. Parallel delegation (a standing
owner rule) makes this more likely every wave. Single-writer append is the serialization:
minting through the registry is atomic, and the race is closed structurally, not by
convention.

**Idempotency under retry is schema, not afterthought.** Every submission carries a
client-supplied idempotency key (the delegating session mints a UUID per intent). A
submit that times out and is retried returns the *same* ref, because the key is unique on
the events table. This is also what makes the degraded mode (§2.9) reconcilable: a
provisional ref written offline *is* the idempotency key, and reconciliation binds it to
a serial ID exactly once. [INFERENCE — standard idempotency-key design; the specific
binding of provisional-ref = idempotency-key is this note's proposal.]

### 2.3 The frontmatter/prose split, and the export ratchet

**The seam.** Every field in today's frontmatter is a relation or a state — exactly what
a store is for. The `§1..§9` body is prose — exactly what markdown, nvim, and git diffs
are for. So: **the registry owns state, identity, relations, transitions, ordering; the
file owns prose.** The file keeps a minimal header (its ref, so a file is
self-identifying when read cold) and nothing else that can drift.
[INFERENCE — the minimal header is this note's addition; a fully headerless file would
make the degraded mode (§2.9) unable to self-identify.]

**Export → git, pinned.** The registry renders each entity's authoritative frontmatter
back into its markdown file — a derived view. The in-tree precedent is exact:
`scripts/handoff.py`'s committed rendering is a pure function of the artifact tree,
embedding **no HEAD sha and no generation timestamp**, so regenerate-then-commit
converges in one step and the freshness gate is dischargeable by one mechanical command
[GROUNDED scripts/handoff.py:20-27 — "THE IDEMPOTENCE PIN"]. The registry export carries
the same pin: no wall-clock, no sequence counters in the rendered text, so two exports of
an unchanged registry are byte-identical.

**The CI ratchet: `export == working tree`.** CI regenerates the export from the
committed event log snapshot and byte-compares. This needs **no access to the
machine-level store**: the event log's git-visible snapshot (§2.8) plus the working tree
are sufficient inputs, so CI stays hermetic. The ratchet is what makes the split safe:
a hand-edited `status:` line in a file is not a security event anymore (the registry does
not read it back) — it is a *drift* event, and the ratchet turns it red. Structural
enforcement, per the standing rule: the property is real because a check proves it.

**What survives of today's ergonomics.** Prose stays nvim-editable; git diff of prose
stays the review surface; `grep`-cheap state sweeps survive because the export puts
state back into the tree — the sweep greps the *export*, which the ratchet certifies.

### 2.4 Sign-based transitions: the event, the keys, the reuse

#### 2.4.1 The signed transition event

A privileged transition is an event whose payload is the five-tuple
`(id, from_status, from_content_hash, to_status, to_content_hash)` and whose signature is
verified before the event is accepted into the log
[GROUNDED docs/brainstorms/blessing-auth-gate.md:27-37]. Three defects die at once:

| defect | why it dies |
|---|---|
| forged flip (finding-0206) | no valid signature over the tuple — the acceptor holds only the public key and cannot forge |
| from-nothing blessing (oq-0040) | no `from_content_hash` exists to sign; the pre-image is part of the signed object |
| no grant record (oq-0036) | the signature IS the grant record, and the event log is where it durably lives |

**Where verification runs.** Twice, deliberately: at **admission** (the registry refuses
an unsigned privileged event — the convenient check) and at **CI/export** (the ratchet
re-verifies every privileged transition in the log against the enrolled public keys — the
check outside the agent's reach, the same shape as the deploy gate's remote attestation
leg [GROUNDED docs/brainstorms/blessing-auth-gate.md:39-45]). A local check alone is a
local check; the CI leg is what makes patching the local verifier pointless.

#### 2.4.2 The substrate: a pair of YubiKeys

Owner-confirmed [GROUNDED docs/brainstorms/the-typed-workflow-registry.md:169-207]:
**YubiKeys, a pair, touch-to-sign.** The division of labor with the Secure Enclave is
settled by the same ruling and adopted here unchanged:

| factor | proves | portable? |
|---|---|---|
| Secure Enclave (`userPresence`) | which **node** — this machine is Ouroboros | no, by design — non-portability is the binding |
| YubiKey pair, touch-to-sign | which **human, present now** — the owner authorized *this* transition | yes — which is what makes it the succession path |

Ratification signs with the YubiKey. AWS stays where the owner's own refinement put it —
**unseal only, out of the steady-state path**
[GROUNDED docs/brainstorms/aws-as-the-authorization-spine.md:50-67]; the registry never
consults it. Key #2, enrolled at the same ceremony and stored offsite, is simultaneously
the blessing-continuity path and the node-role succession path — it retires the
"mandatory, and it is the hard part" break-glass item without an offline software key, a
quorum, or an AWS-root ceremony
[GROUNDED docs/brainstorms/the-typed-workflow-registry.md:175-188].

**Parked, not guessed** (owner ceremony, §Parked): which applet/slot (PIV 9c with
PIN+touch vs FIDO2/`hmac-secret`), which algorithm, and where key #2 physically lives.
One constraint is design-load-bearing and stated here: **both keys enroll before key #2
leaves** — a key enrolled later cannot sign for the period before it existed.

#### 2.4.3 Reuse before re-implementation — the existing crypto layers

Two Ed25519 layers exist in-tree, both wired-but-unexercised; duplication is a defect
(standing owner rule), so the registry is designed as their **first real exerciser**, not
a third implementation:

- `core/attestation/crypto.py` — thin Ed25519 sign/verify wrappers over `cryptography`;
  keys as base64 raw seeds; permitted in the sealed core (no socket)
  [GROUNDED core/attestation/crypto.py:1-9].
- `core/verdict/payload.py` — the pattern to copy *structurally*: canonical serialization
  of a typed payload, signature over the canonical bytes, acceptor holds only the public
  key, monotonic sequence enforced by the append-only store. It **reuses the attestation
  crypto verbatim and deliberately does not reuse the attestation record**, because the
  record's canonical form lacks the verdict's fields
  [GROUNDED core/verdict/payload.py:20-27]. The registry transition payload follows the
  identical precedent: reuse `crypto.py`'s verify primitives, mint its own canonical
  five-tuple serialization (the transition has fields neither existing payload carries).

**The honest complication, recorded rather than elided:** `crypto.py` speaks software
Ed25519 (seed in Keychain); a YubiKey signs *on-token* and its available algorithms
depend on applet and firmware. If the chosen slot cannot produce Ed25519 signatures, the
registry's verify path needs an algorithm-parametric extension of the crypto layer rather
than verbatim reuse. [INFERENCE — firmware-dependent; verify at the key ceremony, do not
build from this note's guess. This is falsifier F5.] Verification code placement also
matters: the registry tool lives outside core (§2.8), and repo-workflow tooling
deliberately never imports `core` (the `scripts/handoff.py` stance
[GROUNDED scripts/handoff.py:41-43]). ~~Resolution proposed: a parity-tested sibling verifier…~~

⚑⚑ **OWNER RULING (2026-07-27) — IMPORT IT. The parity-test proposal is withdrawn.**

> *"import it, the bigger issue is that core doesn't depend on anything outside the core"*

**The self-containment principle is directional, and this note had it backwards.** The rule
is that **`core` must not depend outward** — it may not reach into `eval`, `scripts`, or
workflow tooling. It says nothing about the reverse. Workflow tooling importing
`core.attestation.crypto` adds **no outward edge to core**; the arrow points *inward*,
which is the permitted direction.

⇒ The registry's verifier **imports `core.attestation.crypto` directly.** No sibling
module, no parity test, no second implementation. This is also the smaller diff and the
DRY-correct answer — the two standing rules were never actually in tension, only
apparently so, because the direction of the dependency was left implicit.

⚑ `scripts/handoff.py`'s no-core-import stance is a *stdlib-purity* choice for a
zero-dependency derived-view renderer, **not** an instance of the self-containment rule; it
does not generalize to tooling that needs cryptography. [GROUNDED — the distinction is the
ruling's operative content; recorded so a later reader does not re-derive the parity test
from `handoff.py`'s example.]

#### 2.4.4 Proportionality

Per-transition touch-to-sign would make a nine-plan batch blessing painful
[GROUNDED docs/brainstorms/blessing-auth-gate.md:67-69]. But the ruling's asymmetry
(§2.5) already removes most volume: `proposed→ready` needs **no** signature, and
ratification is rare and deliberate — the act where per-item touch is arguably the point.
Default: one touch per ratified note; batch-signature (one signature over a set of
five-tuples) is parked with a recorded default of "not built until the owner hits the
friction." [INFERENCE]

#### 2.4.5 The notary is a courier, never an authority

The notary — the component that routes a re-auth request to the owner, carries the
signature back, and records it — lives on the scheduler side of Ouroboros "for now"
[GROUNDED docs/brainstorms/the-typed-workflow-registry.md:360-377]. That placement does not
contradict §2.8's "do not couple the registry to the daemon", because the two components
have opposite availability profiles: the registry must answer at **every agent action**
(local file, no daemon); the notary is needed only at **auth moments** — rare, and by
definition the owner is present. A scheduler outage stops *notarization*, not work, and
blocking is the correct behaviour for the one operation where blocking is correct.

**The invariant, pinned rather than left implicit: the notary routes and records; it never
holds signing capability.** The signing capability lives in the YubiKey, physically outside
every process. Compromising the scheduler therefore buys an attacker denial of service —
dropped, delayed, or reordered requests — and **never forgery**. If the notary ever holds
signing material "for convenience," compromising the scheduler becomes compromising
ratification, and Ouroboros becomes able to bless its own design
[GROUNDED docs/brainstorms/the-typed-workflow-registry.md:379-393]. Falsifier F9: any code
path by which the scheduler could produce a valid transition signature without a hardware
touch. [INFERENCE — the owner's "(for now..)" reads as anticipating the notary's promotion
to its own node; the courier constraint makes that cheap, since a courier holds no secrets.]

#### 2.4.6 The hub carries pointers, never content — and pre/post hashing is a TOCTOU defence

The hub — a document-processing and routing node, **explicitly not the Ouroboros
scheduler** — may live anywhere (AWS, a phone-reachable service) because it structurally
cannot see content [GROUNDED docs/brainstorms/the-typed-workflow-registry.md:399-424,
450-461]. **Its single invariant: the hub carries pointers only, never content.** Three
independent uses converged on that wire format, which is evidence it is the right format
rather than a constraint tolerated three times
[GROUNDED docs/brainstorms/the-typed-workflow-registry.md:903-922]:

| use | what crosses the wire | what never does |
|---|---|---|
| seal request | content hash + commit ref | the document |
| merge → deploy (§2.11) | the merged ref | the code |
| ingestion notice (§2.12) | the new head sha | the corpus |

Falsifier F10: any hub payload whose body is not resolvable-by-reference. This satisfies
NN-11 ("the interface may transit a third party; the corpus never does") structurally, not
by policy — the hub has nothing to leak.

**The hash is a content address, not an opaque token.** The artifacts in question are
already committed and pushed — public, retrievable, locatable to the exact commit by the
metadata the hub carries (commit ref, artifact id, type). The owner verifies by retrieving
at that commit and recomputing the hash; because the hash *is* the integrity check, the
retrieval path need not be trusted — a tampered copy simply fails to recompute
[GROUNDED docs/brainstorms/the-typed-workflow-registry.md:463-491]. Consequence for §2.3:
the export stops being a convenience with a ratchet attached and becomes **load-bearing for
the auth loop** — published files are what make a hash resolvable at all
[GROUNDED docs/brainstorms/the-typed-workflow-registry.md:493-502].

**The precondition, stated as an invariant:** the argument rests on "not personal data —
already published." Only artifact types that are *published by construction* (design notes,
plans, findings, journals) may transit the hub; a future type touching corpus or vault
content does not get this channel by default, and the client's type system is where that is
enforced [GROUNDED docs/brainstorms/the-typed-workflow-registry.md:504-512].

**The pre/post hash comparison is a TOCTOU (time-of-check-to-time-of-use) defence — named
as one** [GROUNDED docs/brainstorms/the-typed-workflow-registry.md:426-448]:

```
1. agent writes the file locally
2. client computes  hash_pre , submits ONLY that
3. hub → owner: "the file with hash_pre needs your seal"
4. owner verifies (retrieve + recompute) and signs
5. re-hash the local file NOW → hash_post
6. hash_pre == hash_post ?  →  accept; store hash_post
                          ✗  →  REFUSE — the request is stale; resubmit
```

Without steps 5–6 there is a window between "please sign hash X" and the signature landing
in which an agent can rewrite the file — the owner would be signing content he never saw,
and the prize is a forged ratification. The failure mode is a stale request, never a silent
bad signature. It is the same arithmetic as the warrant lapse (§2.5.1): a warrant binds to
a content hash, so any divergence — mid-ceremony or years later — lapses it. One mechanism,
three jobs: ratification, tamper-evidence, TOCTOU defence. **This is a named acceptance
criterion owed to `bp-145`** (the signed-admission plan): its acceptance must exercise the
pre≠post refusal path. Falsifier F11.

[INFERENCE — owner ruling required, recorded not decided: the standing "blessings stay at
the keyboard" rule was written when remote signing was blind. It no longer is — content is
retrievable, identity provable, and a YubiKey NFC can sign against a phone. The rule stands
until the owner rules; the reason it rested on has changed
(docs/brainstorms/the-typed-workflow-registry.md:514-523).]

### 2.5 The gate asymmetry — and the independence it creates

#### 2.5.1 The ruling, made structural

Owner ruling, verbatim source
[GROUNDED docs/brainstorms/the-typed-workflow-registry.md:222-258]: the two owner-only
gates split.

| gate | signature? | automatable? | why |
|---|---|---|---|
| `draft → ratified` | **yes** | **never — permanently** | design judgement: semantic, effectively irreversible (restoring a lapsed warrant takes the owner's key), inherited |
| `proposed → ready` | **no** | yes — this is what autopilot delegates | a judgement about readiness: mechanical, checkable, reversible (`ready → proposed` costs nothing) |

Foreclosure at the frame, not as a current limitation: the registry schema admits **no
unsigned path** to `ratified` — there is no flag, no config, no privileged role that
waives the signature. An unsigned `→ratified` event is malformed input, rejected at the
type level. Softening this would require the owner's re-authorization of this very
section — the §2.10 loop applied to itself.

**Ratified is warrant-bearing, not immutable (owner ruling, 2026-07-27 — revises this
section's ratified framing).** The earlier model — ratified artifacts as agent-immutable,
an edit as a violation to be blocked — is retired. A ratified artifact is *mutable*; what
cannot survive a content change is the **warrant**: the signature binds to the content
hash, so an edit lapses it by arithmetic. Nothing needs to detect tampering — the hash
stops matching, the artifact drops out of `ratified` in the fold, and the edit stands as a
self-announcing **proposal awaiting re-auth**
[GROUNDED docs/brainstorms/the-typed-workflow-registry.md:307-324]:

| | old model | this model |
|---|---|---|
| ratified note | agent-immutable — the edit must be prevented | agent-writable — the edit invalidates its own warrant |
| what detects tampering | a hook diffing against HEAD | nothing needs to; the hash stops matching |
| an edited ratified note is | a violation to be blocked | a proposal awaiting re-auth |
| the gate | prevent the act | withhold the signature |

§2.10 gives the full loop. **Consequence for `bp-145`** (the signed-admission plan): its
acceptance must test the **lapse-on-edit path** — edit a ratified artifact, observe the
fold report the warrant lapsed, re-auth restores it — not only the no-unsigned-path-in
direction. Falsifier F13: an edited ratified artifact that still folds to `ratified`
without re-auth has a warrant that survived a content change it must not survive.

#### 2.5.2 The discriminator generalizes

Reversibility ∧ semantic depth — not "is it a gate." This is the same axis
`ops/effect_catalog.py` already uses for effectors (blast radius), which is evidence it
is the real axis and not an ad-hoc split
[GROUNDED docs/brainstorms/the-typed-workflow-registry.md:243-247]. It also cleanly
classifies the third owner-only gate: a deskcheck verdict (`pending→approved|needs-work`)
is semantically deep but *reversible* (a verdict can be re-run). The ratified text parked
verdict signing with a default of "unsigned, owner-by-hand, revisit only on observed
forgery"; **that parked decision is re-opened, not silently kept** — with ratify (§2.4)
and merge (§2.11) both becoming warranted acts, the unsigned third gate is the odd one
out, and it guards the strongest claim in the system. See §2.13 and §Parked. [INFERENCE —
the classification is this note's extension of the ruling; the re-opened decision stays
the owner's.]

**Consequence — two independent tracks, stated so nobody serializes them:** `bp-138` /
`bp-139` (autopilot delegated blessing, AP5/AP6) automate the gate with **no** signing
requirement; the hardware key serves the gate autopilot will **never** touch. The signing
track and the autopilot track are independent and can proceed in parallel
[GROUNDED docs/brainstorms/the-typed-workflow-registry.md:249-253]. Likewise, key
onboarding does not block on the registry: the signing primitive works against today's
markdown+git world (the pre-image hash is merely harder to obtain), so onboarding + the
primitive can land first and the registry adopts them
[GROUNDED docs/brainstorms/the-typed-workflow-registry.md:262-265].

#### 2.5.3 Collisions with the ratified note — recorded, not resolved

The ratified `dn-autopilot-and-delegated-blessing` wins on every row; each row names what
this note would *want* and what it *defers to*:

1. **The flip's executor.** Ratified §2.3: the MFA verifier performs the
   `proposed→ready` flip as a file edit + flip commit carrying the grant record. Registry
   world: the flip is a registry event submitted by the verifier, and the grant record
   (capsule hash, P1–P5 results, HMAC attestation tag — semantics untouched) is the
   event's payload. **Recorded collision:** the ratified note specifies commit mechanics
   (`grant.md` in the flip commit); re-homing them onto an event payload is an amendment
   to that note, owner-ratified, licensed only after this note is itself ratified.
2. **Enforcement mechanics named by the ratified note.** Its §2.3 pre-hoc/post-hoc
   layers are *hook-shaped*: "gate-guard continues to deny…", "the Stop-gate clause (c)
   contract gains one narrow exception…". Retiring those hooks (§2.6) removes the named
   mechanisms while this note preserves the *guarantees* (owner-only flips → signed or
   grant-verified events; post-hoc verifiability → the event log + CI ratchet).
   **Recorded collision:** the guarantee survives, the named mechanism does not; the
   ratified text must be amended by the owner before the hooks it names are removed.
   Until then, those hooks stay in place (§3 sequencing).
3. **`oq-0037`** — who holds the autopilot MFA secret — is touched by nothing here and
   remains parked. The registry stores the grant *record*; it neither holds nor moves
   the secret.
4. **Invariant 4 of the ratified note** ("`draft→ratified` has no autopilot path — ever")
   is not a collision but is restated because this note strengthens it from a rule to a
   schema property (§2.5.1) — a strengthening, which nesting permits; the weaker text
   stays authoritative until amended.
5. **Warrant-bearing vs agent-immutability (added in the 2026-07-27 revision).** The
   ratified autopilot note — and CLAUDE.md's A8 status guard — frame ratified artifacts as
   *agent-immutable*; §2.5.1 now makes them *warrant-bearing*. The guarantee is preserved
   and strengthened (an edit cannot *pass as* ratified), but the named mechanism
   ("agent-immutable, HEAD-keyed, laundering-proof") is contradicted. **Recorded, not
   resolved:** until the owner re-warrants the surrounding texts, their rule governs agent
   conduct and this note's model governs the registry's schema.
6. **`dn-role-state-and-scoped-handoff` §2.6 D4** (the ratified role-state note) ruled
   "files as source; the queue as an input, never the source." The registry inverts the
   first half: registry as source, files as its export. The owner directed that note's
   amendment (2026-07-27, verbatim in its §2.6); the fold rides this same PR under §2.10's
   protocol, preserving the three D4 grounds that still bind. Both re-auths are the same
   merge — if the owner rejects one, he rejects both, which is the correct coupling since
   the two rulings are one decision.

### 2.6 Hook retirement — the disposition table, honestly

The six hooks and where each *guarantee* goes. A guarantee is retired only when a
registry-side test proves parity (structural-enforcement rule: built-but-unvalidated is
not built); this table is the completeness checklist
[GROUNDED docs/brainstorms/the-typed-workflow-registry.md:77-103, and the hook sources
read this pass: .claude/hooks/_lib.py, *.sh].

| hook | guarantee today | disposition |
|---|---|---|
| `gate-guard` (PreToolUse) | owner-only status flips denied pre-hoc | **dissolved.** Status is not file-resident; a flip is a signed event; a hand-edit is ratchet-caught drift |
| `journal-gate` (Stop) | no close on unfinished obligation — clauses (a)–(f) | **dissolved into queries + land-time admission** — per-clause map below |
| `session-brief` (SessionStart) | orientation + close-audit baseline | **replaced by query.** Orientation is a registry read; no denial semantics remain (a read cannot clog) |
| `staleness-nudge` (UserPromptSubmit) | derived views drifted | **dissolved.** Views derive from the store on read; there is nothing to go stale |
| `compaction-marker` (PreCompact) | post-compaction turn re-verifies vs journal | **kept — the one surviving hook.** Interception-shaped; no registry equivalent (argued below) |
| `scope-guard` (PreToolUse) | writes outside `write_scope` denied; denylist | **dissolved.** Writes unconstrained mid-flight; bright lines → PR denylist check; rest is review (below) |

**The journal-gate clause map** (each clause is a distinct guarantee; none silently
dropped):

| clause | today | in the registry |
|---|---|---|
| (a) journal staleness vs last commit | mtime check at Stop | land/seal submission *requires* the unit's judgement entry; unlanded staleness costs nothing landing won't demand |
| (b) out-of-scope worktree changes | git-status sweep at Stop | review judgement at the PR: the diff is questioned against declared intent (§2.6); denylist paths checked by the Action |
| (b2) ratified-note immutability, HEAD-keyed | diff vs HEAD at Stop | reframed by §2.5.1: divergence is a warrant *lapse* — a proposal awaiting re-auth; nothing passes as ratified |
| (c) uncommitted / untracked blessing flips | diff + untracked scan | unrepresentable: a blessing exists only as an accepted event; bytes in a file are not a blessing |
| (d) cross-checkout state bleed | main-checkout pointer check | dissolves with its substrate: `active-plan` becomes a registry ref; no per-checkout state file remains |
| (e′) session-handoff freshness | handoff `--check` + seat-journal mtime | DERIVED rendering becomes a registry query; the NARRATIVE demand moves into land/seal like (a) |
| (f) seal follow-through block | journal-tail grep at Stop | a **typed field on the seal event** — submission refuses a seal without the five answers; grep upgraded to schema |

**Honest loss in the (a)/(b) family, stated:** Stop fires at session close; the PR-side
checks and review fire at submission for merge. A session that never opens a PR can leave
a dirty tree that no gate ever examined. Backstops: the CI ratchet (nothing merges
un-reconciled), the denylist Action (nothing merges over a bright line), and the fact
that an unlanded worktree is, by the disposable-sessions doctrine, discardable state.
The guarantee's *location* moves from "before close" to "before consequence"; the window
between them is exactly the window in which nothing has happened yet. [INFERENCE — this
is the trade the design makes deliberately; falsifier F4 covers it.]

**`compaction-marker` — why it stays.** The owner's complaint is that hooks *deny on the
hot path*. This hook never denies: it appends one marker line at PreCompact so the
post-compaction turn re-verifies against the journal rather than trusting the lossy
summary. Compaction is a context-window event — invisible to any store, existing only at
the instant it happens. A warrant cannot travel with a context window. Retiring it buys
nothing (it clogs nothing) and loses a real guarantee. One hook, read-only, fail-open,
is the honest residue of the interception model. [GROUNDED — behavior verified in
.claude/hooks/compaction-marker.sh; the disposition matches the brainstorm's own
assessment at docs/brainstorms/the-typed-workflow-registry.md:91.]

**`write_scope` — superseded twice in one night, and the halves separate (owner rulings,
2026-07-27; revises this section's ratified decision).** The ratified text weighed two
options — (a) land-time admission and (b) worktree-as-scope, per-unit as an enforcement
*level* [GROUNDED docs/brainstorms/the-typed-workflow-registry.md:94-103]. Both are
retired, in two steps that must be recorded separately because they now govern different
things:

1. **Dispatch-time capability — and it stands, for credentials.** The registry is not
   merely a recorder; it **dispatches the workers** (Claude SDK), so a capability is what a
   worker is *constructed with*: no AWS key, no merge ability, no signing material — the
   agent is never forbidden them, it is never given them. There is no legitimate need to
   overrule this half, which is what marks it as capability work rather than judgement work
   [GROUNDED docs/brainstorms/the-typed-workflow-registry.md:260-301 — "the central system
   dispatches the workers with claude sdk … no need to force the hand of an agent, as
   we've seen, it cripples them"].
2. **File writes go unconstrained — an allowlist is a prediction; a denylist is a bright
   line.** The final ruling: *"no more write scopes, or at least it's more of a denylist
   than an allow list, github action on PR to check 0 writes to specific files, only I can
   overrule … let the builder do what it needs to do, don't limit it, we then question via
   PR review"* [GROUNDED docs/brainstorms/the-typed-workflow-registry.md:959-1025]. An
   allowlist encodes a *prediction* about what the work will need; predictions are wrong,
   and a wrong one blocks legitimate work — mechanically how `write_scope` clogged the
   machinery it protected, re-guessed across all 137 plans. A denylist encodes only what
   must never happen, a set that is small, stable, and actually knowable. Judgement does
   not compress to a glob; the new model puts judgement back where it lives — a reviewer
   who can ask *"why did you touch this?"* at the PR (§2.11). **General rule, stated once:
   mechanism for the absolute, judgement for the contextual.**

The mechanics that follow:

- **The foundation denylist** — `CONSTITUTION.md`, `eval/golden/**`, `eval/golden.py`,
  **and `.github/workflows/**`** — is enforced by a **GitHub Action on every PR** (zero
  writes to those paths), a required check only the owner can overrule. The Action is an
  external principal: it does not share an identity with the agent it binds, unlike
  `scope-guard`, which read a file the agent could write
  [GROUNDED docs/brainstorms/study-not-product.md:102-141 — a control cannot bind a
  principal it shares an identity with].
- **The self-protection interlock:** `.github/workflows/**` is on the denylist because the
  check lives there — a constraint the constrained party can remove is decoration. Third
  instance of the pattern (agent token minus `Administration`, `finding-0276`; now this);
  generalized: **every external control must deny writes to itself**
  [GROUNDED docs/brainstorms/the-typed-workflow-registry.md:1004-1012].
- **`write_scope` the *field* survives with a new job: a declaration of intent.** The PR
  diff is questioned against it in review — "you said X, you touched Y, why?" It becomes a
  hypothesis, not a fence; divergence is a question, never a denial. [INFERENCE — arguably
  more useful than its enforcement role: a stated intent the work contradicts is a genuine
  review signal, where a denial was merely an obstacle.]
- **Knock-ons, recorded:** `bp-146` (the graduated plan making `write_scope` a per-unit
  enforcement level) is **largely obsolete** — it graduated hours before the ruling against
  a mechanism now retired, and must be superseded explicitly, not left pointing at a dead
  design. `finding-0275`'s clearing condition changes: `scope-guard` is not coming back,
  so its three red enforcement tests are answered by the CI denylist check, not by parity
  tests. (Recorded here; neither artifact is edited by this note.)
- **The honest residual:** the denylist check fires at the PR, and dispatch-time
  capability binds only workers the dispatcher constructs. An interactive session at the
  owner's keyboard is bound by neither mid-flight; for it, the warrant model is the
  backstop — an unauthorized write produces a file without a warrant, not an artifact
  (§2.5.1). [INFERENCE — this note's honesty clause, not the ruling's; falsifier F7.]

**The `HOOK-FAILURE` / `OUROBOROS_HOOKS_OFF` escape-hatch spirit** carries forward as
§2.9's registry escape hatch — the property (the owner can always get out) is preserved
under a new mechanism, not dropped with the old one.

### 2.7 Resume-brief deprecation

**Diagnosis — structural, which is why it failed *every* time.** The resume brief is a
hand-maintained cache of a derivable fact, written at the exact moment the agent is most
depleted: end of session, context exhausted, the work of writing it competing with the
work it summarizes. Lossy by construction, stale on write
[GROUNDED docs/brainstorms/the-typed-workflow-registry.md:105-111]. The repo has already
walked this exact road once and drawn the same conclusion at smaller scale: the
`.claude/state/` handoff file was retired for being "outside git, mixing four kinds of
fact with four freshness rules, freshness as a hand-authored act that every later commit
re-armed" — replaced by *regenerate and commit*
[GROUNDED .claude/skills/context-economy/SKILL.md, the CORRECTION block]. The resume
brief is the same defect one level up, and the fix is the same shape: **derive, don't
carry.**

**The replacement is not a better brief — it is that nothing session-shaped needs
handing off.** State distributes across *units of work*: each registry unit carries its
open criteria, parked items with re-entry conditions, last landed commit, and linked
findings — as typed fields, written at the semantic boundary where each fact is born (the
moment of least depletion), not recalled at close. A fresh session reconstructs "where
was I" by query: *open units, their open criteria, their parked items, in dependency
order*. The fresh-agent test stops being a discipline the journal strains to satisfy and
becomes the registry's ordinary read path.

**The structural cause, named by the owner — "there is no third place" (2026-07-27,
sharpening the diagnosis above).** The system has exactly two homes: **product** (git,
public — notes, plans, findings, code, and commit messages) and **strata** (Ouroboros,
local, private — transcripts and deliberation, ingested as memory, never published).
Anything in between rots, whatever discipline is applied to it. The resume brief was
homeless: not product (it described work rather than being it), not strata (authored, not
ingested) — so it went stale between the writing and the reading, every time
[GROUNDED docs/brainstorms/the-typed-workflow-registry.md:687-710]. This is the test to
apply to any proposed artifact before inventing it; PR-feedback tracking fails it (§2.11).

**The journal narrows to judgement.** Status was always the registry's job; the journal
carried it under protest. What remains is what no store can derive: the why, the
surprises, the approaches discarded and the reason. Shorter, and the part that was
actually valuable. The seat-journal purity rule (no shas, no counts, no statuses)
already points exactly here — it becomes the rule for *every* journal.

**Every artifact that must change** (named per the brief's requirement; all changes are
licensed by ratification and executed under plans, none by this note):

| artifact | change |
|---|---|
| `CLAUDE.md` (note-taking rule; "resume brief" sentence at :78) | obligation re-worded: unit-state fields at semantic boundaries + judgement entry; resume-brief sentence deleted |
| `.claude/skills/checkpoint/SKILL.md` | sections 1–6 split: status/completed/in-flight/next become registry unit fields; entry keeps judgement + markers |
| `.claude/skills/context-economy/SKILL.md` | clearing boundary: "write the handoff pair" → "submit unit state; append judgement entry" |
| `.claude/skills/resume/SKILL.md` (`/resume`) | resumes from registry query + prose files, not from a journal narrative |
| `.claude/skills/build-plan/SKILL.md` + `docs/templates/build-plan.md` | frontmatter fields move to registry submission; `write_scope` re-typed as declared intent (§2.6) |
| `.claude/skills/delegate/SKILL.md` | builders mint IDs/refs via the registry; push-before-spawn gains "registry ref, not eyeballed ID" |
| `docs/design-notes/agent-workflow.md` §6, §9, §13 | owner-ratified amendment: hook contracts retired per §2.6; §9 re-worded |
| `docs/design-notes/dn-role-state-and-scoped-handoff.md` | DERIVED rendering becomes a registry query; NARRATIVE/MEASURED unchanged — owner-ratified amendment |
| `scripts/handoff.py`, `scripts/board.py` | re-pointed to derive from the registry (board.py's artifact scan is subsumed by a query; handoff.py keeps only live-pane rendering) |
| `.claude/hooks/*` + `.claude/settings.json` | retired per §2.6's staged sequence; `compaction-marker` survives |

[INFERENCE — the list is believed complete for in-repo consumers of journal-as-status
and of frontmatter-as-state; the graduation plan must re-verify by grep before each
retirement stage, per the ground-before-building rule.]

### 2.8 Placement: local, single-file, no-daemon, machine-level, outside the repo

**Decision: a single-file store (SQLite) at a machine-level path — `~/.mind-palace/`
(exact filename decided at build) — plus a git-visible export of the event log snapshot
for CI.** Justified against each constraint explicitly:

- **Not in core (NN-1).** The registry serves agents and, plausibly someday, a phone
  surface. In core it either breaks zero-egress or must route through `edge/` for every
  workflow read. Core also never outsources to nor absorbs repo-workflow tooling (the
  self-containment principle). Keep it out of the question entirely
  [GROUNDED docs/brainstorms/the-typed-workflow-registry.md:127-129].
- **Not coupled to the daemon (NN-8).** The registry must answer whenever an *agent*
  runs — in a worktree, in CI, with the palace down, in recovery mode. Coupling workflow
  liveness to a daemon under a ≤2-model / 20–24 GB ceiling trades a hard availability
  requirement for nothing [GROUNDED docs/brainstorms/the-typed-workflow-registry.md:130-133].
- **Not a cloud service.** "Simple, flexible, robust" rules it out; a cloud registry
  means no work on a plane, and it makes spine availability load-bearing for *ordinary*
  operation — the exact mistake the owner's AWS refinement ("unseal only") was written to
  avoid [GROUNDED docs/brainstorms/aws-as-the-authorization-spine.md:50-67].
- **Outside the repo, not `data/`.** Each worktree gets its own `data/`; a per-worktree
  store silently defeats serial minting — the defect that motivated the whole idea. A
  machine-level path is what makes minting actually serial across parallel builders
  [GROUNDED docs/brainstorms/the-typed-workflow-registry.md:136-138].
- **CI needs no tunnel.** The ratchet's inputs are the committed event-log snapshot and
  the working tree (§2.3); the machine-level store is never a CI dependency.
  [INFERENCE — the committed snapshot (an append-only export of the log, updated at land
  time) is this note's mechanism for making CI hermetic; its exact format is a build
  decision.]

**The portability clause (folded from the deleted A11 draft; owner-directed 2026-07-27).**
The machine-level placement makes minting serial on one machine — and makes the registry
*absent* everywhere else: a fresh clone, a worktree on another machine, a CI runner has no
registry. In such a checkout **the export is authoritative and read-only**: it may be
read, built in, and reasoned from; it may **not** mint, transition, or seal. Those
operations require the registry and **fail closed with a named error, never a silent
local fallback** — a registry-less checkout that quietly wrote frontmatter would fork the
truth into two divergent sources with no reconciliation, invisible until it corrupts. The
fresh-agent drill doubles as this clause's falsifier: it must still pass in a checkout
with only the export (F8). [GROUNDED — the clause is the A11.2 draft in substance
(docs/inbox/amendment-A11-draft.md, deleted in this revision); the multi-machine hole it
closes was left open by this section's ratified text, which argued only the
one-machine/parallel-worktree case.]

**Why SQLite specifically:** single file (owner-openable, backup = copy), no server, and
WAL mode gives the concurrency shape §2.9 requires — readers do not block the writer and
the writer does not block readers [GROUNDED — external: SQLite WAL documentation,
sqlite.org/wal.html: "WAL provides more concurrency as readers do not block writers and
a writer does not block readers"]. Write serialization (one writer at a time) is exactly
the serial-minting property, obtained from the substrate rather than built.

### 2.9 The registry as the new deadlock — designed in, not bolted on

The stated motivation is that hooks clog the machinery they protect. A centralized
registry can fail the same way, worse: locked, corrupt, or unavailable means **no work at
all**, where a broken hook could at least be escaped. Non-negotiables, each with its
mechanism [GROUNDED docs/brainstorms/the-typed-workflow-registry.md:156-167]:

1. **Reads never block.** Substrate-level (WAL, §2.8), plus a rule: every read path has a
   fallback to the *export* — the working tree's certified frontmatter is a complete,
   always-readable projection of current state. A reader that cannot open the store reads
   the tree and says so.
2. **A degraded mode exists and is specified now**, not discovered during the first
   outage. If the store is unavailable at submission: the agent appends the event to a
   local pending file (per-worktree, append-only) under a **provisional ref** — which is
   its idempotency key (§2.2) — and continues working. Reconciliation on next
   availability replays pending events through normal admission; serial IDs bind to
   provisional refs exactly once. Privileged transitions are the exception: a blessing
   does not happen degraded — it *queues* unverified and is not effective until admitted.
   Degraded mode loosens liveness, never authority.
3. **An escape hatch survives.** Two, layered: (i) the export **is** the hatch — because
   the ratchet keeps files complete, the markdown tree can carry the system alone in an
   emergency, exactly as today, and a recovery import reconciles the tree back into the
   log afterward (divergences surface as conflicts for the owner, not silent merges);
   (ii) the store is a plain local file the owner can open, query, and — with his own
   hands — repair; owner overrule is a signed event, the same primitive as blessing, so
   even the overrule leaves a warrant. If the registry can wedge the owner out of his own
   system, it has reproduced the defect it was built to remove; these two hatches are the
   proof obligation, and falsifier F3 is their test.

The dispatch role (§2.6) does not sharpen this concern — it relaxes it: a dispatcher
constructs workers at spawn and sits on no mid-flight path, so a registry outage delays
*new* workers and never blocks running ones
[GROUNDED docs/brainstorms/the-typed-workflow-registry.md:303-305].

**Invariants, stated explicitly:**

1. No event is ever mutated or deleted; corrections are events.
2. Two submissions with one idempotency key yield one ref, always.
3. No unsigned path to `ratified` exists in the schema — not flagged off, absent.
4. The export embeds no clock and no counter; two exports of an unchanged log are
   byte-identical.
5. Reads degrade to the export; they never wait on a writer and never fail closed.
6. A degraded-mode blessing is queued, not effective; authority never degrades.
7. The foundation denylist — `CONSTITUTION.md`, `eval/golden/**`, `eval/golden.py`,
   `.github/workflows/**` — is enforced by an external-principal check on every PR; only
   the owner can overrule it, and the check denies writes to itself (§2.6).
8. A hook is retired only after a registry-side test proves its guarantee's parity.
9. The registry holds no secret: not the MFA secret (oq-0037, parked), not key material —
   public keys and signatures only (NN-10).
10. The hub carries pointers only — a content hash, a commit ref, a head sha; a payload
    whose body is not resolvable-by-reference is malformed (§2.4.6).
11. Only artifact types published by construction may transit the hub (§2.4.6).
12. The notary routes and records; it never holds signing capability (§2.4.5).
13. A checkout without the registry reads the export and fails closed, with a named
    error, on mint/transition/seal (§2.8).
14. A warrant never survives a content change: edit ⇒ lapse ⇒ re-auth, with no path that
    re-attaches a signature to bytes the owner did not see (§2.5.1, §2.4.6).

### 2.10 The revision protocol — the A-series amendment ceremony dissolves

**The loop (owner ruling, 2026-07-27):** an agent may edit any artifact, ratified ones
included. The edit changes the content hash, which lapses the warrant by arithmetic
(§2.5.1); the agent **resubmits for re-auth**; the system routes the request to the owner
(§2.4.5); the owner notarizes — *"I interact with the system as my seal of approval, my
notary"* [GROUNDED docs/brainstorms/the-typed-workflow-registry.md:307-334]. "Notary" is
exact: a notary neither authors nor judges content — they attest that the named party
signed. That is what a hardware touch proves, and why `draft→ratified` is permanently
un-automatable: a notary who is a program is not a notary.

**Consequence: the lettered amendment ceremony (A1–A10, and the A11 drafted the same
night) dissolves.** It existed only because ratified notes could not be edited — unable to
change the text, the repo grew a parallel artifact describing the change it could not
make, plus a build plan to land it, plus a protocol section explaining itself. Remove
immutability and the apparatus is unnecessary: you edit the note, the warrant lapses, you
resubmit, the owner notarizes. **The event log is the amendment history** — every prior
ratification, every lapse, every re-auth, in order, queryable — which is the owner's
"audits via query algebra" ask arriving from the other direction; the amendment log was a
hand-maintained, ceremony-laden cache of exactly that chain, the resume brief's defect in
a different costume [GROUNDED docs/brainstorms/the-typed-workflow-registry.md:336-355].

**Until the registry exists, the PR is the venue:** the diff is the amendment, the merge
is the re-auth, GitHub's record is the interim event log — held by a party the agent
cannot rewrite [GROUNDED docs/brainstorms/study-not-product.md:132-141]. This note's own
revision is the protocol's first exercise. The transitional A11 draft
(`docs/inbox/amendment-A11-draft.md`) is deleted in this revision, its content folded
where it belongs (§2.6, §2.8, and `dn-role-state-and-scoped-handoff` §2.6) — recorded so
its successor is not mistaken for missing work
[GROUNDED docs/brainstorms/the-typed-workflow-registry.md:357-358].

### 2.11 Landing is an authorization act — the integrator, the merge train, the audit venue, the deploy plane

**No local main-merges (owner ruling, 2026-07-27).** *"Machine merges are never allowed;
builds now open a PR with the proper docs and reasoning; I merge from GitHub."* The same
move as the notary, applied to code: a note becomes ratified by a hardware signature; a
branch becomes main by the owner pressing merge — the agent is removed from the
authorization loop, not restrained within it. Scope, per the owner's own narrowing: the
forbidden act is `git merge <branch>` into main *locally*; orchestrator doc-commits
directly to main are a different act and are unaffected
[GROUNDED docs/brainstorms/the-typed-workflow-registry.md:529-548].

**The sub-orchestrator is the integrator.** Builders merge into *its* integration branch,
never into main; it assembles and opens the PR; the owner merges. Integration is also
where id collisions surface and are fixed — one level below the owner's attention, where
that belongs [GROUNDED docs/brainstorms/the-typed-workflow-registry.md:744-774]:

| # | stage | actor | act | warrant |
|---|---|---|---|---|
| 1 | `draft → ratified` | owner | notarize | hardware signature over a content hash |
| 2 | graduate + build | sub-orchestrator, builders | mint plans, write code | none — proposals |
| 3 | integrate | sub-orchestrator | assemble the PR | none — still a proposal |
| 4 | audit | auditor agent | review comments in the PR | none — advisory |
| 5 | approve + merge | owner | merge (⇒ deploy) | the GitHub merge button |
| 6 | deskcheck (§2.13) | owner | track verdict | re-opened — see §Parked |

**The merge train: staging, not landing, triggers the rebase.** PRs land in sequence,
never independently, and **when a merge is *staged* — queued, not yet landed — every
other active branch rebases**. This is deliberately earlier than the delegate skill's
current on-land trigger, which it strictly dominates (the skill's text is owed the
update): staging-as-trigger removes the window in which a branch builds on a base already
known to be stale, which is what keeps "it passed" meaning something
[GROUNDED docs/brainstorms/the-typed-workflow-registry.md:556-569]. The queue is
event-log-shaped — `staged → rebased → landed` are ordered events with a warrant on the
terminal one — not a second mechanism. **Honesty note:** today this is convention, not
control — branch protection was verified absent this pass (`gh api …/branches/main/protection`
→ 404); the structural version is an owner act, and whether GitHub can require PRs for
merges while leaving direct doc-commits alone must be checked before it is promised
[GROUNDED docs/brainstorms/the-typed-workflow-registry.md:571-581].

**The PR is the audit venue.** A PR review is natively what the delegate skill demands an
audit be — attributed, timestamped, anchored to the exact lines, threaded against the
diff it judges — and it makes the *deliberation* public, which nothing else in the chain
does. Review events enter the registry log as **occurrence, not content**: *that* an
audit happened, by whom, with what verdict — never what was said
[GROUNDED docs/brainstorms/the-typed-workflow-registry.md:643-659, 727-735]. There is no
third place (§2.7): the arguing lives in the strata, the decision lands in the product.
**The cost, and it is real: the commit message becomes the only surviving record of
*why*.** It stops being a label for a diff and becomes the carrier of what the review
changed — what the auditor questioned, what the answer was, what the builder altered. A
commit reading `fix: address review comments` destroys the record this design keeps in
exactly one place [GROUNDED docs/brainstorms/the-typed-workflow-registry.md:712-721].
[INFERENCE — this is the strongest argument yet for CONVENTIONS §Commits being enforced
rather than encouraged; under the old model a thin message was recoverable from
surrounding artifacts, under this one it is the only copy.]

Two risks recorded so they are designed rather than discovered
[GROUNDED docs/brainstorms/the-typed-workflow-registry.md:803-813]: (i) the
auditor↔builder feedback cycle has no termination condition and needs a bound
([INFERENCE] escalate-to-owner-on-disagreement is probably right; parked); (ii) a
sub-orchestrator-spawned auditor is independent of the *builder* but not of the
orchestrator that scoped the work — fine for spec-fidelity, wrong for auditing the
decomposition itself; needs an explicit rule, since the failure reads as agreement.

**The deploy plane: `plan : apply :: proposal : authorization`.** The agent may generate
`terraform plan` — a reviewable statement of intent that changes nothing — and may not
apply it. `apply` runs in GitHub Actions, triggered by the owner's merge, so the third
layer joins the pattern: design is notarized, code is merged, infrastructure is applied
by the same merge. **The agent holds no AWS credentials — that is the whole point**;
there is nothing local to scope, rotate, or leak
[GROUNDED docs/brainstorms/the-typed-workflow-registry.md:583-607; the OIDC trust-policy
shape is [INFERENCE] there and must be verified before building]. This retires
`mind-palace deploy` as a discipline-held rule: the deploy stops being a command anyone
could run and becomes a consequence of an authorization already given — unexpressible
locally rather than forbidden
[GROUNDED docs/brainstorms/the-typed-workflow-registry.md:609-612]. NN-3 ("the model
advises; code acts") becomes structural rather than procedural. **Open, deliberately not
defaulted:** on a public repo, posted plan output leaks topology (ARNs, account ids,
security-group shapes); accept / narrow to a check artifact / redact is the owner's
decision *before* the first plan posts, because the first post cannot be unpublished
[GROUNDED docs/brainstorms/the-typed-workflow-registry.md:614-641].

### 2.12 Ingestion moves to the edge and reads only `origin/main`

**The ruling:** *"ingestion is now an edge agent, it only ingests from github remote/main
directly, you can't accidentally slip something on the local main"*
[GROUNDED docs/brainstorms/the-typed-workflow-registry.md:815-822]. The property bought:
**the corpus contains only what survived the merge gate** — "what was authorized," not
"whatever was on this disk." Why this is priority work and not hygiene is §1.1: corpus
integrity is identity integrity.

**The measured defect (not hypothetical):** `.githooks/post-commit` snapshots on every
local commit; sixteen ingestions were counted in a single session, none gated, including
two orchestrator readings that were *later corrected* — both the wrong reading and its
correction now sit in the corpus with equal standing, nothing marking which superseded
which. The same session committed one evolving brainstorm ten times, so the corpus holds
~10 near-duplicate embeddings of one document
[GROUNDED docs/brainstorms/the-typed-workflow-registry.md:824-833, 873-889; whether
`core/stores/sourceset.py`'s group-by-digest already mitigates the duplicate flooding at
*retrieval* rank is worth measuring, not assuming]. The deeper argument: **a commit is a
moment; a merge is a unit.** Ingesting commits ingests work-in-progress wearing
knowledge's clothes; the merge is the moment someone decided the thing was coherent
[GROUNDED docs/brainstorms/the-typed-workflow-registry.md:859-871]. This is also the last
act-based hook in the loop — an act (commit) triggering a consequence (ingest) with no
warrant between them — retired the same way as the other six.

**The NN-2 boundary, drawn before it can be drawn wrong:** NN-2 forbids network and
private data sharing a component. So the lane is a **fetch lane, not an "ingestion edge
agent"**: edge *fetches* from `origin/main` and hands bytes inward; core *ingests* and
writes the stores. A single component doing both would be the violation, and the naming
invites it [GROUNDED docs/brainstorms/the-typed-workflow-registry.md:843-857]. Falsifier
F12.

**Deferred and pull-shaped:** merge-triggered via a notification whose payload is the new
head sha (a pointer — §2.4.6), drained by the edge lane on its own schedule, at night or
on demand. Night ingestion respects the memory ceiling (NN-8) and joins the dreamer's
existing lane ([INFERENCE — pin the ordering: ingest the day's merged units, then dream
over them]). **Pull, not push:** AWS enqueues; the house initiates every connection; no
listener, tunnel, or ingress into the machine holding the vault
[GROUNDED docs/brainstorms/the-typed-workflow-registry.md:924-952]. Restartable for free:
a notice is a ref, so a missed run is caught by the next one. Stated once as the general
rule, third convergence of the night (notary, fetch lane, notification bus):
**components that move things must not also be components that hold things**
[GROUNDED docs/brainstorms/the-typed-workflow-registry.md:954-957].

### 2.13 Deskcheck gating — the third owner gate, and its parked venue re-opened

**The rule (owner, 2026-07-27):** a track may be deskchecked only when **all** of its
designs are merged — *except* long-running tracks (`workflow`), which deskcheck **after
each design→merge**. The exception is load-bearing, not a convenience: `workflow` never
reaches "all designs merged" because it is the track that keeps redesigning the system
that builds it; without the carve-out its deskcheck is unreachable by construction, and
an unreachable gate quietly stops being applied — how "DONE ≠ sealed" gets violated
without anyone deciding to
[GROUNDED docs/brainstorms/the-typed-workflow-registry.md:744-751, 788-796].
"All designs merged" is a **query over the event log**, not a status field anyone
maintains — the fifth ceremony the log absorbs (amendments, merges, audits, reviews,
deskcheck-eligibility) [GROUNDED docs/brainstorms/the-typed-workflow-registry.md:798-801].

**Deskcheck is now the third owner gate and the only one without a venue.** Ratify has
the signature; merge has the PR; deskcheck has neither, and it guards the strongest claim
in the system ("this track is done") — the gate the owner has already ruled is never
self-declarable. This note parked verdict signing when the gate stood alone; with stages
1 and 5 both warranted, the unsigned third gate is the odd one out. **The parked decision
is re-opened, not silently kept** (§Parked) — re-opened because the surrounding structure
changed underneath it, not because anything broke; the decision remains the owner's
[GROUNDED docs/brainstorms/the-typed-workflow-registry.md:776-786].

## 3. Consequences

**On ratification of this note, and not before:**

1. **Revisions, under §2.10's protocol, to two ratified notes:** `dn-agent-workflow` (§6
   hook contracts, §9 note-taking, §2/§10 gate wording — the registry becomes the named
   enforcement substrate) and `dn-autopilot-and-delegated-blessing` (the §2.5.3 recorded
   collisions: flip-executor mechanics, the hook-named enforcement layers, and the
   agent-immutability framing). Executed as direct edits whose PRs the owner merges — the
   A-series ceremony is dissolved. Until each revision merges, the text it revises governs
   and the corresponding hook stays. (`dn-role-state-and-scoped-handoff` §2.6 D4 is
   revised in this same PR, §2.5.3 item 6.)
2. **A one-sentence-scale edit to `CLAUDE.md`** — the write-discipline and note-taking
   rules re-pointed at the registry; the resume-brief sentence deleted (§2.7's table).
3. **Graduation licenses, in dependency order (each session-sized, split at graduation):**
   (i) the store + minting + refs + idempotency (closes the live ID race; changes no
   enforcement); (ii) frontmatter migration + export + CI ratchet; (iii) the signed
   transition event + verification (adopts the separately-landed key onboarding — the
   signing primitive does **not** wait for the registry, per §2.5.2); (iv) staged hook
   retirement, one guarantee at a time, each behind its parity test; (v) resume-brief
   deprecation — the skills/CLAUDE.md/scripts edits of §2.7's table.
4. **Sequencing rule adopted from the brainstorm:** key onboarding proceeds now against
   the markdown world; the registry adopts the primitive when stage (iii) lands.
5. **Independence declared:** `bp-138`/`bp-139` proceed in parallel with all of the
   above; nothing here blocks them and they block nothing here (§2.5.2).
6. **Book chapter, eventually:** act-based → sign-based is a real constitutional idea;
   it enters the workflow chapter after the mechanism survives contact.
7. **Landing discipline (§2.11):** branch protection and the required denylist check are
   owner acts; the delegate skill's rebase trigger updates from on-land to on-staged; the
   CONVENTIONS §Commits text gains the load-bearing-message clause. The denylist GitHub
   Action (§2.6) is buildable immediately — it needs no registry.
8. **The deploy plane (§2.11):** a GitHub-Actions apply lane replaces local deploy;
   `mind-palace deploy` (and its standing never-run-autonomously rule) retires when that
   lane lands; the plan-output-visibility decision is the owner's before the first plan
   posts.
9. **The fetch lane (§2.12):** graduation adds an edge fetch-lane plan; the
   `.githooks/post-commit` snapshot lane retires in its favor; a plan is owed for marking
   the already-ingested superseded content (the two corrected readings and the
   near-duplicates are in the corpus *now*).
10. **Plan-ledger corrections (§2.6):** `bp-146` (write_scope as per-unit enforcement
    level) is proposed for explicit supersession; `finding-0275`'s clearing condition is
    re-pointed at the CI denylist check. Both are owner-visible follow-ups, not silent
    edits.

**Explicitly not licensed:** the identity-foundation ceremony (owner-run, separately
captured), any answer to `oq-0037`, any `draft→ratified` tooling, an administrative
knowledge graph (parked), any change to blessing semantics.

## 4. Wiring & enablement

**How it wires:** a registry library + CLI as repo-workflow tooling (`scripts/`-side, run
via `uv run`; importing `core.attestation.crypto` directly per §2.4.3's ruling — the
dependency arrow points inward, which is the permitted direction), speaking to the
machine-level store; a path override (env var) so tests and drills use a scratch store;
the export subcommand (regenerate + byte-compare, `handoff.py --check`'s shape) wired
into the local CI gate and remote CI; the signed-transition verifier beside the CLI; the
denylist GitHub Action (§2.6) as a required PR check, registry-independent and buildable
first; per-stage rollout switches — stage (i) minting is
live the moment the CLI exists (it changes no enforcement); stages (ii)–(iv) each flip by
an owner-visible edit to `.claude/settings.json` (removing a hook registration) **only
after** the corresponding parity test is green in CI; the pending-file degraded path and
the recovery import as CLI subcommands, built in stage (i)–(ii), not deferred to the
first outage.

**What it takes to flip it on:** (a) a build must add: store schema + CLI (mint, submit,
query, land, export, reconcile, import), the CI ratchet job, the verifier + parity test,
and the per-guarantee parity tests for §2.6; then (b) the owner turns it on in stages:
adopt minting immediately (no risk — it only closes a race); commit the first full
export; enable the CI ratchet; after key ceremony, enroll the two public keys into the
verifier's trust file and sign the first ratification; then retire hooks one at a time by
hand-editing `.claude/settings.json` as each parity test goes green — the hook removals
are themselves owner-visible diffs. First end-to-end exercise is deliberately a trivial
finding mint from two parallel worktrees, deskchecked before anything is retired.

## Parked decisions

| decision | default recorded | re-entry condition |
|---|---|---|
| YubiKey applet/slot + algorithm; key #2's offsite location | none — owner ceremony decides | the key-onboarding ceremony (identity-foundation capsule) |
| batch signature over a set of transitions | not built | owner hits the per-touch friction on a real batch |
| administrative knowledge graph vs event-log-as-graph | event log + query algebra only | a real admin query the log's algebra cannot answer |
| ~~write_scope level assignment~~ ⚑ **SUPERSEDED 2026-07-27** | denylist + review; `write_scope` is declared intent (§2.6) | resolved by owner ruling; `bp-146` supersession is §3(10) |
| deskcheck-verdict signing | ⚑ **RE-OPENED 2026-07-27 (§2.13)** — the unsigned third gate is now the odd one out | owner decides at this revision's re-auth |
| PR feedback-cycle termination rule | escalate to owner on disagreement [INFERENCE] | first audit cycle that loops past two rounds (§2.11) |
| terraform-plan output visibility on a public repo | none — owner decision, not a default | before the first Actions-posted plan (§2.11) |
| "blessings stay at the keyboard" relaxation | the standing rule stands | owner ruling; remote verify is now possible (§2.4.6 [INFERENCE]) |
| dream/ingest night ordering | ingest, then dream [INFERENCE] | the fetch-lane build plan (§2.12) |
| exact store filename / snapshot format | decided at stage (i) build | stage (i) plan |
| ~~core-import vs parity-test for crypto reuse~~ ⚑ **OWNER RULED 2026-07-27 — IMPORT IT** | workflow tooling **imports `core.attestation.crypto` directly**; no parity-tested sibling, no duplicated verifier | resolved; see §2.4.3 note below |
| `compaction-marker` retention | kept as the one surviving hook | harness-level compaction hooks change, or the hook fires zero times over a measured month |

## Falsifiers — what would prove this design wrong

- **F1 (serial minting):** two parallel worktree builders minting concurrently ever
  receive the same ref, or a timed-out-and-retried submit yields two refs. Either
  observation voids §2.2's central claim.
- **F2 (idempotent export):** two consecutive exports of an unchanged registry differ by
  one byte. The frontmatter/prose split then re-arms the staleness treadmill it was
  built to end (§2.3).
- **F3 (the new deadlock):** any read blocks on the store, or an outage prevents an
  agent from continuing ordinary work, or the owner cannot operate the system from the
  markdown tree alone during a registry failure. The design has then reproduced the hook
  defect and §2.9 has failed.
- **F4 (guarantee parity):** any row of §2.6's table whose hook is retired before a
  registry-side test proves the guarantee holds — or a post-retirement incident that
  today's hook would have caught and the registry did not.
- **F5 (crypto reuse):** the enrolled YubiKey configuration cannot produce signatures
  the reused verification layer accepts on shared test vectors. §2.4.3's reuse claim
  fails and the verify path must be redesigned before stage (iii).
- **F6 (resume by query):** a fresh-agent drill — new session, registry + prose files
  only — cannot continue an in-flight unit without re-asking. The resume-brief
  replacement (§2.7) is then not yet real, and the deprecation halts at the skills edit.
- **F7 (denylist + capability):** a PR touching a denylist path merges without the
  owner's explicit overrule; or the denylist check is removable by an agent-authored
  change (the `.github/workflows/**` interlock failing); or a dispatcher-constructed
  worker acts with a credential it was not constructed with. Any of the three voids
  §2.6's claim that mechanism covers the absolute.
- **F8 (registry-less checkout):** a checkout without the registry can mint, transition,
  or seal — or refuses silently instead of with a named error — or the fresh-agent drill
  fails in a checkout holding only the export. The §2.8 portability clause has failed.
- **F9 (courier notary):** any code path by which the scheduler/hub could produce a valid
  transition signature without a hardware touch. §2.4.5's invariant has failed and
  Ouroboros can bless its own design.
- **F10 (pointers-only hub):** any hub payload whose body is not resolvable-by-reference
  — content where an address belongs. §2.4.6's single invariant has failed, and NN-11 is
  back to being policy instead of structure.
- **F11 (TOCTOU):** a signature is accepted over content whose signing-time hash differs
  from the requested pre-image — the pre/post comparison failed to refuse a stale
  request. Named acceptance criterion on `bp-145` (§2.4.6).
- **F12 (fetch/ingest split):** any single component in the ingestion lane that both
  touches the network and writes the corpus stores. §2.12's NN-2 boundary has failed.
- **F13 (warrant lapse):** an edited ratified artifact still folds to `ratified` without
  re-auth. The warrant survived a content change it must not survive (§2.5.1); the
  lapse-on-edit acceptance on `bp-145` is the test.
