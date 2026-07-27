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
> `dn-agent-workflow` (ratified) — those amendments are licensed only by this
> note's own ratification and are executed by the owner's hand, never by this
> note's existence.

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
5. **The corpus boundary is unchanged.** Workflow *outputs* (design notes, findings,
   plans) remain ingestable by Ouroboros exactly as the markdown exports they already
   are; the registry's administrative event log is **not** part of the semantic corpus
   and is not embedded. [INFERENCE — the owner allowed either ("its own knowledge graph
   if possible, or ouroboros could still work"); this note takes the smaller reading and
   parks the administrative-graph question (§Parked) rather than deciding it.]
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

### 2.5 The gate asymmetry — and the independence it creates

#### 2.5.1 The ruling, made structural

Owner ruling, verbatim source
[GROUNDED docs/brainstorms/the-typed-workflow-registry.md:222-258]: the two owner-only
gates split.

| gate | signature? | automatable? | why |
|---|---|---|---|
| `draft → ratified` | **yes** | **never — permanently** | design judgement: semantic, effectively irreversible (ratified notes agent-immutable), inherited downstream |
| `proposed → ready` | **no** | yes — this is what autopilot delegates | a judgement about readiness: mechanical, checkable, reversible (`ready → proposed` costs nothing) |

Foreclosure at the frame, not as a current limitation: the registry schema admits **no
unsigned path** to `ratified` — there is no flag, no config, no privileged role that
waives the signature. An unsigned `→ratified` event is malformed input, rejected at the
type level. Softening this would require amending a ratified note at the owner's hand,
which is precisely the ceremony such a change deserves.

#### 2.5.2 The discriminator generalizes

Reversibility ∧ semantic depth — not "is it a gate." This is the same axis
`ops/effect_catalog.py` already uses for effectors (blast radius), which is evidence it
is the real axis and not an ad-hoc split
[GROUNDED docs/brainstorms/the-typed-workflow-registry.md:243-247]. It also cleanly
classifies the third owner-only gate: a deskcheck verdict (`pending→approved|needs-work`)
is semantically deep but *reversible* (a verdict can be re-run); default: owner-by-hand
as today, **unsigned**, revisit only if verdict forgery is ever observed. [INFERENCE —
the deskcheck classification is this note's extension of the ruling; the owner should
confirm at ratification.]

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
| `scope-guard` (PreToolUse) | writes outside `write_scope` denied; foundation denylist | **moved to land-time admission, per-unit level** — the hard one, argued below |

**The journal-gate clause map** (each clause is a distinct guarantee; none silently
dropped):

| clause | today | in the registry |
|---|---|---|
| (a) journal staleness vs last commit | mtime check at Stop | land/seal submission *requires* the unit's judgement entry; unlanded staleness costs nothing landing won't demand |
| (b) out-of-scope worktree changes | git-status sweep at Stop | land-time admission: the landing's diff is checked against the unit's declared scope |
| (b2) ratified-note immutability, HEAD-keyed | diff vs HEAD at Stop | ratified content hash is registry state; the ratchet reddens on divergence; laundering has no target |
| (c) uncommitted / untracked blessing flips | diff + untracked scan | unrepresentable: a blessing exists only as an accepted event; bytes in a file are not a blessing |
| (d) cross-checkout state bleed | main-checkout pointer check | dissolves with its substrate: `active-plan` becomes a registry ref; no per-checkout state file remains |
| (e′) session-handoff freshness | handoff `--check` + seat-journal mtime | DERIVED rendering becomes a registry query; the NARRATIVE demand moves into land/seal like (a) |
| (f) seal follow-through block | journal-tail grep at Stop | a **typed field on the seal event** — submission refuses a seal without the five answers; grep upgraded to schema |

**Honest loss in the (a)/(b) family, stated:** Stop fires at session close; land-time
admission fires at landing. A session that never lands can leave a dirty tree that no
gate ever examined. Backstops: the CI ratchet (nothing merges un-reconciled) and the fact
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

**`write_scope` — an enforcement level, not a global choice.** A store cannot stop a
`Write` to an arbitrary path; the two honest options
[GROUNDED docs/brainstorms/the-typed-workflow-registry.md:94-103]:

- **(a) land-time admission** — the registry refuses a landing whose diff touches paths
  outside the unit's declared scope. Unbypassable (landing goes through the registry),
  but the violation is discovered after the work, not during it.
- **(b) worktree-as-scope** — the agent physically cannot see files it may not write.
  Structural in the strongest sense; costs a worktree per unit and complicates read-only
  context.

Decision: **per-unit, not global — `write_scope` becomes an enforcement *level* declared
at graduation.** Default level = (a). Level (b) for units whose blast radius the
delegation rubric already scores full-strength (enforcement surfaces, core invariants,
migrations) — the axis exists and is in use; graduation assigns the level the way it
already assigns model tier. The **foundation denylist** (`CONSTITUTION.md`,
`eval/golden/**`, `eval/golden.py`) binds at admission for every unit at every level, and
additionally stays covered by the CI ratchet, so it is enforced twice with neither
enforcement on the write hot path. What is honestly given up at level (a): the mid-flight
"you are about to stray" signal. A builder discovers the mis-scope at land time with the
exact offending diff in hand — later than today, cheaper than today's per-write tax.
[INFERENCE — that the trade is net-positive is the design bet; falsifier F7.]

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
| `.claude/skills/build-plan/SKILL.md` + `docs/templates/build-plan.md` | frontmatter fields move to registry submission; `write_scope` gains its enforcement level |
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

**Invariants, stated explicitly:**

1. No event is ever mutated or deleted; corrections are events.
2. Two submissions with one idempotency key yield one ref, always.
3. No unsigned path to `ratified` exists in the schema — not flagged off, absent.
4. The export embeds no clock and no counter; two exports of an unchanged log are
   byte-identical.
5. Reads degrade to the export; they never wait on a writer and never fail closed.
6. A degraded-mode blessing is queued, not effective; authority never degrades.
7. The foundation denylist binds at admission for every unit at every enforcement level.
8. A hook is retired only after a registry-side test proves its guarantee's parity.
9. The registry holds no secret: not the MFA secret (oq-0037, parked), not key material —
   public keys and signatures only (NN-10).

## 3. Consequences

**On ratification of this note, and not before:**

1. **Amendments, owner-ratified, to two ratified notes:** `dn-agent-workflow` (§6 hook
   contracts, §9 note-taking, §2/§10 gate wording — the registry becomes the named
   enforcement substrate) and `dn-autopilot-and-delegated-blessing` (the §2.5.3 recorded
   collisions: flip-executor mechanics and the hook-named enforcement layers). Until each
   amendment lands, the text it amends governs and the corresponding hook stays.
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

**Explicitly not licensed:** the identity-foundation ceremony (owner-run, separately
captured), any answer to `oq-0037`, any `draft→ratified` tooling, an administrative
knowledge graph (parked), any change to blessing semantics.

## 4. Wiring & enablement

**How it wires:** a registry library + CLI as repo-workflow tooling (`scripts/`-side, run
via `uv run`; **never** importing `core` unless the owner rules otherwise per §2.4.3),
speaking to the machine-level store; a path override (env var) so tests and drills use a
scratch store; the export subcommand (regenerate + byte-compare, `handoff.py --check`'s
shape) wired into the local CI gate and remote CI; the signed-transition verifier beside
the CLI with the §2.4.3 parity test; per-stage rollout switches — stage (i) minting is
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
| write_scope level assignment heuristics | (a) default; (b) at full-strength blast radius | first post-registry graduation wave reviews the assignments |
| deskcheck-verdict signing | unsigned, owner-by-hand as today | any observed verdict forgery, or owner ruling at ratification (§2.5.2 [INFERENCE]) |
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
- **F7 (land-time admission):** measured post-adoption, mis-scoped work discovered at
  land time costs more (rework, abandoned diffs) than today's per-write denials cost in
  friction. The §2.6 write_scope default then flips toward level (b) per-unit isolation.
