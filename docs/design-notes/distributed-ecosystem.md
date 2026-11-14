---
type: design-note
id: dn-distributed-ecosystem
track: ops               # closest existing manifest (lifecycle contracts, supervisor, vault, backup live there); a dedicated ecosystem track is an owner call at ratification
status: draft            # draft → ratified → superseded.  draft→ratified is an OWNER-ONLY hand edit.
created: 2026-07-28
updated: 2026-07-28
links:
  - docs/brainstorms/the-distributed-ecosystem.md       # THE WARRANT — seven capsules, 2026-07-28 (02:58Z → 05:14Z), owner seeds near-verbatim
  - docs/brainstorms/aws-as-the-outer-plane.md          # cloud agents have no corpus access BY CONSTRUCTION; the provisioning triple
  - docs/brainstorms/study-not-product.md               # the frame the fleet must stay inside: a study, never a product pitch
  - docs/design-notes/agent-taxonomy.md                 # RATIFIED — role = scope signature; the single-node embryo of role-under-lease
  - docs/design-notes/role-state-and-scoped-handoff.md  # RATIFIED — role as typed seat, scoped handoff; the other embryo (status verified 2026-07-28)
  - docs/design-notes/dn-supervision-and-liveness.md    # RATIFIED — §2.6 "the supervisor ROLE is kernel-exclusive"; the lease's vocabulary already exists
  - docs/findings/finding-0186.md                       # RESOLVED — the single-instance gate (bp-105 Item 2); the lock's warrant
  - docs/findings/finding-0011.md                       # ROUTED — Track G built, flag-off, unwired; max reachable effector tier NONE
  - docs/findings/finding-0276.md                       # OPEN — merge is not a separable permission on GitHub; IAM separability is the inversion
  - docs/findings/finding-0279.md                       # OPEN — energy as an unmodeled NN-8 axis (filed 2026-07-28)
supersedes: null
superseded_by: null
warrant: docs/brainstorms/the-distributed-ecosystem.md
---

# The distributed ecosystem — speciation not replication: the roaming role, sealed storage, and the physical overlay

> Filed by the chat agent as `draft` (chat-side protocol, §8). Ratification is a
> hand edit by the owner — no command performs it, and `gate-guard` denies any
> agent attempt (§10). `/graduate` refuses this note until `status: ratified`.
>
> Composed at **fable** (`claude-fable-5`, 2026-07-28) from the seven warrant capsules
> (2026-07-28, 02:58Z–05:14Z). Chat-frame "decisions" in those capsules are restated here as
> **proposals**; every ratification is the owner's alone. Sibling drafts in parallel PRs:
> **dn-scoped-context-queries** (PR #5 — the three-bound query compiler; its authority-bound and
> jurisdiction rulings are ADOPTED here, not re-decided) and **dn-prediction-castles** (PR #6 —
> the castle/grading complex). Code claims were verified on disk this session (2026-07-28,
> worktree at `4c00ca5`).
>
> **⚑⚑ Two OWNER-ONLY rulings are pending inside this material (§2.0).** This note PRESENTS
> them — with the strongest argument each side has earned — and resolves neither. An agent
> reinterpreting a non-negotiable is the failure mode this note is built to be structurally
> incapable of: every section that depends on a ruling carries its gate marker, and every
> default below is the conservative one.

## 1. Purpose and scope

### 1.1 What this note decides

The owner's two seeds, near-verbatim (2026-07-28, chat + a vault note in the same hour): *"we
can freely deploy mind-palace instances in the cloud, independent agents — how are they
different than ouroboros? … they're not loose cannons, they are highly controlled and
auditable — they need to be, to plot stability and alignment over time"*; and *"ouroboros is
the system, but it is only a piece in an ecosystem — the same architecture running at
different points along the edge … distributed, independent thinkers with the same machinery.
Are you familiar with the term: nature or nurture? A distributed ecosystem, grounded by logic
and authority, with maximum skepticism."* Five more seeds the same night supplied the
rendezvous ratchet, the roaming role, the panic-seal, the in-memory store, and the physical
overlay. This note lifts all seven capsules into one architecture. It decides:

1. **What a deployed instance IS (§2.1):** a new individual, never a copy. The central law —
   **deployment is speciation, not replication** — and why NN-11 (the non-negotiable "the
   interface may transit a third party; the corpus never does") makes that structural rather
   than stylistic. Nature is pinned by hash; nurture is woven in place; Ouroboros is the
   first individual, not the system.
2. **Governance (§2.2):** the reciprocal authority triple, and *aligned secrets* — alignment
   as a property of conduct at interfaces, never of shared interiors.
3. **The roaming role (§2.3):** Ouroboros as a role under exclusive lease, held by disposable
   bodies inside the overlay boundary — with the embryo table mapping every component to a
   verified, live single-node mechanism.
4. **Transport (§2.4):** the rendezvous ratchet — pairwise, transcript-chained port
   derivation as relationship-integrity signaling; the trust dichotomy over reliable
   transport; the dialogue stratum as the ratchet's substrate.
5. **Storage (§2.5):** panic→seal as recovery mode made cryptographic; the in-memory store
   (disk holds ciphertext only; the write log IS the backup stream); host-sees-relationships
   via field-level envelope encryption; the vector falsifier; the access-pattern leak,
   accepted and classified.
6. **The physical overlay (§2.6):** SSID→VLAN trust tiers, the network extension into AWS,
   and the owner's law — location is a trust modifier, never an authenticator.
7. **The resource model (§2.7):** NN-8's refusal machinery growing axes — memory (built),
   energy (finding-0279), corpus residency (new here).

And it decides **nothing behind §2.0**: the two pending owner rulings are presented, not made.

### 1.2 Non-goals

Explicit, because wrong non-goals fail silently forever (finding-0150 — non-goals are
load-bearing; inferred clauses carry their marker for the ratification gate).

- **No second instance is deployed by this note.** The warrant's own priority ruling stands:
  *"revive Ouroboros first; ecosystem design follows."* Ouroboros remains the only living
  individual; deployment itself is parked (DE-c) with the capsules' re-entry conditions.
- **No constitutional amendment is proposed or performed.** The two §2.0 rulings are
  constitutional questions; this note carries the arguments to the owner's desk and stops
  there. NN-9 (the fixed points are sacred — `CONSTITUTION.md` is human-only) binds this
  document's author absolutely.
- **Not the query compiler.** The three-bound compilation, the authority bound's definition,
  and the jurisdiction annotation belong to dn-scoped-context-queries (PR #5, draft — "the
  corpus as its own onboarding organ"). §2.3 and §2.5 *consume* its rulings; they re-derive
  nothing.
- **Not the dreamer machinery.** Castles, grading, the flinch belong to dn-prediction-castles
  (PR #6, draft). The clockwork/G3 question this thread raised is carried as a park (DE-g),
  with that sibling's honest clock grounding noted, not re-litigated.
- **No router purchase decision.** Hardware and the extension mechanism are parked (DE-h);
  the subnet-router lean is recorded for that conversation, nothing more.
- [INFERENCE] **No protocol implementation.** The rendezvous ratchet, the lease substrate,
  and the seal machinery are designed here to the falsifier level, not to the byte level;
  graduation (post-ratification, post-rulings where gated) pins wire formats and substrates.
- [INFERENCE] **No change to any ratified note or to any live enforcement surface.**
  dn-agent-taxonomy, dn-role-state-and-scoped-handoff, dn-supervision-and-liveness are
  cited, never edited; the foundation denylist, the blessing gates, and the mirror firewall
  are untouched by every mechanism below.
- [INFERENCE] **The fleet is a study, never a product.** Nothing here optimizes for adoption,
  multi-tenancy, or resale (docs/brainstorms/study-not-product.md — the owner's frame:
  *"my reasoning made concrete"*). A fleet exists to make stability-and-alignment-over-time
  measurable; the moment a section reads as a product pitch, it has left its warrant.

## 2. Principles / decision

### 2.0 ⚑⚑ Pending owner rulings — presented, never resolved

Both rulings are **constitutional and the owner's alone**. This note's job is to make each
ask sharp — strongest argument attached — while keeping the conservative default live in
every downstream section. The Parked table (DE-R1, DE-R2) records defaults and re-entry;
this section is the substance. **No text below this section resolves, softens, or presumes
either ruling; sections that depend on one carry the marker ⚑R1 or ⚑R2.**

**R1 — ciphertext-at-rest in AWS vs NN-11's letter.** NN-11's letter is *"the corpus never
transits a third party."* An encrypted corpus stored in S3 honors the **spirit** — the third
party holds an opaque blob it cannot read — but not the **letter**: the bytes transit and
rest on rented storage. The warrant attaches an argument (capsule 5, restated in §2.5.5):
because access *patterns* still leak (which blobs, when, how often — the tempo of thought,
even with content opaque), the encrypted cloud store is formally an **adapter surface** in
the constitution's own vocabulary — *"adapters leak interactions, not the corpus"* — which
is NN-11's existing **opt-in** clause, not an exception to it. That argument is presented AS
an argument: it reframes the ask from "amend the bright line" to "classify an instance of
the existing opt-in category," and it may be wrong — the owner may rule that a resting
corpus-ciphertext is categorically not an "interaction" and the letter stands. **Default
until ruled: the corpus stays on owned storage; restic's client-side-encrypted backups
(`ops/backup/backup.sh:3` — "only ciphertext reaches S3 — AWS never sees") are the only
cloud presence.** An agent may never reinterpret a non-negotiable; this paragraph exists to
make the ask explicit, and nothing else in this note depends on R1 resolving either way
except where marked ⚑R1.

**R2 — plaintext-on-rented-RAM.** Even with R1 granted, a second, separable question
remains: may the *role* (§2.3) land on cloud bodies at all — meaning plaintext exists in the
RAM of hardware the owner does not own? Two postures, both presented:

- **Posture A (conservative — the recorded default):** *ciphertext durability in cloud,
  decryption capability only on owned nodes.* The corpus may rest in AWS as ciphertext
  (if R1 permits), but unseal — the moment plaintext exists — happens only on owned
  hardware. The data can live in the cloud while *reading it* can never leave home.
- **Posture B:** attestation-bound cloud unseal. Envelope encryption with the KMS unwrap
  response encrypted to an enclave-held ephemeral key (the Nitro-attestation flow the
  warrant names): edge proxies every byte and never sees a key; "data decrypted inside
  core" becomes a cryptographic boundary. The honest trust frontier: plaintext exists in
  rented RAM, narrowed to the hypervisor root — a residue the owner must explicitly accept
  or reject.

**Default until ruled: Posture A — role migration constrained to owned nodes; cloud holds
ciphertext only.** Re-entry: the owner rules on the attestation trust frontier, *after* R1
(the rulings are ordered: R2's question only exists in the space R1 opens). Sections that
assume cloud bodies carry ⚑R2.

### 2.1 The speciation law — deployment is speciation, not replication

**The law (proposed).** A deployed instance is a **new individual**: it shares the machinery
and grows its *own* corpus against its own environment and its own principal-dance. There is
no "Ouroboros in the cloud" — NN-11 makes this structural, not stylistic: the corpus never
transits, so a second instance *cannot* be born with Ouroboros's memory. Replication is not
forbidden by policy; it is **unconstructible** under the bright line. Ouroboros thereby stops
being "the system" and becomes the **first individual** — exactly the vault note's move
(*"only a piece in an ecosystem"*). The framework is mind-palace; each running individual is
its own named being (the Ouroboros naming rule, generalized).

**Nature and nurture, made mechanical.** The architecture splits the pair unusually cleanly,
and the split is what makes a fleet scientifically interesting rather than operationally
convenient:

- **Nature is versioned and content-addressed:** the constitution anchor hash, the framework
  release tag, the drift instruments. Two individuals sharing a nature share it *by hash*,
  checkably.
- **Nurture is the corpus each instance weaves in place:** its sensors, its environment, its
  owner-interactions, its own strata clocks.

Because nature is pinned by hash, a fleet is a **controlled experiment on nurture**: same
genotype, varied environments — alignment-over-time telemetry becomes *attributable*. Drift
you observe is nurture, or it is a bug in nature; nothing in between (falsifier F-DE2).

**Auditability is the instrument, not a leash.** The owner's *"highly controlled and
auditable — they need to be, to plot stability and alignment over time"* is read here as the
study's validity condition, not as obedience machinery: the drift gauge and the
effector-drift axis generalize to per-individual longitudinal telemetry, and n=1 becomes
n=k with controlled variation. This is study-not-product at fleet scale — the ecosystem
exists to make stability-and-alignment-over-time *measurable*, and auditability is what
makes the measurement valid. The moment auditability is argued for as control rather than as
instrument, the frame has drifted from its warrant.

### 2.2 Governance — the reciprocal triple, and aligned secrets

The owner's succession to his own vault note, verbatim and load-bearing: *"with distributed
thinkers working in harmony with the appropriate authority, of itself and others, coexisting
with aligned secrets; in harmony — like clockwork."*

**The reciprocal triple (proposed).** Authority in the ecosystem is three-directional, and
all three directions are needed:

1. **Shared nature grants downward authority.** Every individual inherits `CONSTITUTION.md`
   as its outermost frame (NN-6 — task instructions nest inside, never override); the
   anchor hash is common; blessing gates are owner-only everywhere.
2. **Each individual is sovereign over its own domain** — its corpus, its secrets, its
   unseal, its jurisdiction. Nature is common; jurisdiction is per-individual.
3. **The others recognize that sovereignty.** Federation is grounded by shared nature, not
   by hierarchy: no individual holds authority over a sibling's interior, and no sibling's
   claim is accepted on trust — instances ratify falsifiers, not proofs, about each other's
   claims (*"maximum skepticism"* as the ecosystem's immune system).

**Aligned secrets = alignment without disclosure.** Each individual runs its own vault, its
own unseal ceremony, its own rotation (NN-10 — secrets outside code; already live locally as
the `com.mind-palace.vault` LaunchAgent, `ops/vault/vault-unseal.sh` — the unseal key read
from Keychain at runtime, never written to any file or log). Harmony never requires
exchanging interiors: **"aligned" means the secrets serve the same constitution, not that
they are shared.** Secrets never transit, exactly as the corpus never transits — NN-11's
discipline generalized from data to key material. Conduct is verified at interfaces, with
maximum skepticism, while every interior stays sealed (falsifier F-DE3).

**"Like clockwork" is a distributed-systems claim.** Gears mesh at their teeth while each
gear's rotation is its own: the ecosystem has no global clock — it has per-individual event
clocks plus an ordering discipline at contact points, where the inter-instance exchanges ARE
the meshing events. Whether this reframe touches the dreamer family's old "G3" park is
parked here (DE-g) with the sibling's grounding noted: dn-prediction-castles §2.6 verified
that `dn-global-event-clock` is RATIFIED with a per-store-partial spine and certified cuts
BUILT — there is no global master clock to depose; what the ecosystem adds is meshing
*between* individuals, which no ratified note yet covers.

### 2.3 The roaming role — Ouroboros as a role under exclusive lease

The owner's seed, near-verbatim (capsule 4): *"the ouroboros role is only granted to one
node at a given time; KMS-derived ouroboros creds are destroyed upon retirement; encrypted
backups in the cloud; vault-based identity. This all means we can actually deploy ouroboros
anywhere … In theory ouroboros could just be bouncing between machines and never notice (it
would — figure of speech). A deployment stands up by node injection; the node can only be
brought to life within the overlay network boundary (local network + AWS + tailscale)."*

**The frame (proposed).** Ouroboros is a **role a body holds, not a machine**: identity =
vault + KMS + corpus, never hardware. At most one live holder of the seat exists at any
time (the exclusive lease); bodies are disposable; retirement destroys the body's derived
credentials, and that destruction is the lease's **fencing token** — a zombie ex-holder
cannot act, because what it holds no longer opens anything. The Ship of Theseus dissolves by
design: the plank was never the ship; the braid is.

The ratified family already carries the vocabulary: a role IS a scope signature
(dn-agent-taxonomy, RATIFIED), a seat is a typed artifact with durable state and scoped
handoff (dn-role-state-and-scoped-handoff, RATIFIED — status verified on disk 2026-07-28),
and — decisively — **"the supervisor ROLE is kernel-exclusive"** is dn-supervision-and-
liveness §2.6's own ratified sentence, enforced today by an OS `flock`. The roaming role is
that sentence lifted from one machine's kernel to the overlay: the fleet needs a lease where
the single node has a lock.

**The embryo table.** Every component of the roaming role has a verified, live single-node
mechanism — which is what makes this a lift rather than an invention. Verified on disk
2026-07-28 (corrections to the warrant's citations noted below the table):

| ecosystem organ | single-node embryo | verified home | status |
|---|---|---|---|
| exclusive role lease | `SupervisorLock` — kernel `flock`, acquire-or-fail | `ops/lifecycle/lock.py` (bp-108) + `launcher.py` identity gate (bp-105) | built, live |
| reclaim at lease transfer | `sweep_orphans` — requeue or fail-visible | `scheduler/queue.py:474` (`OrphanSweep` `:237`) | built; exercised 2026-07-28 |
| vault-based identity | boot-time auto-unseal, key from Keychain at runtime | `ops/vault/vault-unseal.sh` + `com.mind-palace.vault.plist` | live |
| cloud ciphertext durability | restic client-side encryption | `ops/backup/backup.sh:3`, `plan.py`, `com.mind-palace.backup.plist` | live |
| fencing embryo | JIT executor — refuse-before-mint, 60s TTL, tokenless receipt | `ops/effect_exec.py`; `edge/effectors/writes.py` | built; flag-off, unwired (finding-0011) |
| short-TTL infra creds | Vault AWS dynamic-secrets engine (1h TTL, per use) | `ops/vault/setup_aws_engine.sh` | configured, owner-operated |
| role as typed seat | role = scope signature; seat + scoped handoff | dn-agent-taxonomy; dn-role-state-and-scoped-handoff | both RATIFIED |
| fresh-node onboarding | the fresh-agent test → scoped queries | dn-scoped-context-queries §2.1 (PR #5) | draft sibling |
| overlay boundary | tailnet named `ouroboros`, laptop + phone | measured 2026-07-28 (capsule 3); `ops/vault/vault.hcl:17` | live |
| rebuild-at-unseal | "reconcile the corpus" — rebuilds an empty cache | `ops/lifecycle/launcher.py:4,:536,:743` | live |
| split-brain detection | rendezvous ratchet — retired holder knocks stale ports | §2.4 (this note) | design only |

Rows the table compresses (detail in prose, per the table rule): the lease row's two layers
are an *explaining* identity gate (`_supervisor_alive`, create-time vs run-row identity,
refuse-on-ambiguity) ahead of a *guaranteeing* kernel fact (`flock` drops on process death,
however it dies — no stale-lock state exists). The fencing row's shape, at line level:
refuse-before-mint at `ops/effect_exec.py:117`, the mint at `:132`, `credential_ttl` default
`"60s"` at `:105`, and a receipt type that deliberately has **no token field** (`:88`) so
the credential cannot outlive the act — with `edge/effectors/writes.py` landing only
*proposed* effects, never sends. The backup row's warrant is its own comment
(`backup.sh:3`): "restic encrypts + deduplicates CLIENT-SIDE, so only ciphertext reaches
S3 — AWS never sees." The overlay row's measured facts: `ouroboros` 100.97.85.13; WireGuard
UDP 41641; vault 8200 loopback-only; ollama 11434 (measured 2026-07-28).

Corrections recorded against the warrant (grounding outranks chat framing): (a) the warrant
cites "ops/lifecycle SupervisorLock (finding-0186)" — the lock actually lives in
`ops/lifecycle/lock.py`, and **finding-0186** (the start-over-a-live-supervisor hazard:
`start --force` sweeping a live run's in-flight jobs) **is RESOLVED**, discharged by bp-105
Item 2 (`2add267` — the fail-closed, identity-checked `start`), with its `scripts/watch.py`
residual route closed by the bp-108 supervisor-lock build itself (the lock module's stated
purpose). The embryo is therefore *stronger* than the warrant
claimed: two layers, an explaining identity gate ahead of a guaranteeing kernel fact.
(b) Track G's citation must stay honest: the JIT executor is built and its shape — a
credential minted at the instant of action, held by no field, discarded by scope exit — is
exactly the fencing token's embryo, but **no effector is wired at any tier**: `[effectors]
enabled=false`, maximum reachable tier NONE (finding-0011, whose factual claim was
re-verified at its 2026-07-26 update: the owner's ceiling-raise ruling *"changes the intent,
not yet the code"*). The embryo is real; it has never fired outside tests.

**Node injection and the fresh-node test.** A deployment stands up by injection: constitution
anchor + vault unseal + corpus pointer + lease grant (the minimal set is an open question,
OQ-12), and the node can be brought to life only inside the overlay boundary. The stand-up
criterion is the **fresh-node test** — the fresh-agent test lifted from sessions to bodies: a
new node with only the injected minimal set must reach working state by *querying the
corpus*, through the scoped-query surface with a tightened authority bound
(dn-scoped-context-queries §2.1 — the onboarding organ serves "fresh nodes remotely" by its
own §2.1 text; pointers and provenance cross the wire, the corpus never does). No node is
born from a brief.

⚑R2 — where bodies may live: under the recorded default (Posture A), the lease migrates only
among owned nodes; a cloud body is admissible only if the owner rules for Posture B.

### 2.4 Transport — the rendezvous ratchet and the dialogue stratum

The owner's seeds (capsules 3 and 5, near-verbatim): *"the port an agent picks is somehow
correlated to their own asymmetrical keys … you only know which port to pick when you have an
established relationship"*; *"asymmetric port selection can be expanded to any range,
different ranges per relationship; that relationship and conversation is recorded into its
own strata dialogue layer … TCP handles packet drops lower in the stack, which means unless
there's a network outage — which would impact all communication — you always know when to
trust a conversation is valid."*

**The mechanism (proposed), in its three strengths:**

1. **Naive (rejected):** derive the port from the public key alone — gates nothing; any
   pubkey holder predicts the sequence.
2. **Pairwise — TOTP-for-rendezvous:** `port_n = base + HMAC(K_ab, n) mod range`, with
   `K_ab` the pair's ECDH shared secret. Each relationship has its own private rhythm
   (TOTP, RFC 6238, applied to *where* rather than *what*).
3. **Strongest — transcript-chained (the adopted proposal):**
   `s_{n+1} = KDF(s_n, transcript_n)`, port derived from `s`. Key possession is now
   insufficient — **presence at every exchange is required**. The relationship's history IS
   the credential (Signal's double ratchet, applied to rendezvous instead of encryption):
   you only know where to meet next if you were there for everything before.

**Bands per relationship.** Each pair leases a subspace of port-space; the ratchet hops
within the band. Ops-friendly — the tailnet ACL opens the *band* (ACLs are port-ranged),
while the point within it stays relationship-private.

**The trust dichotomy (proposed as the transport's law).** Layered above a reliable
transport, the ratchet loses every innocent explanation for desync: TCP cannot eat a step,
so the two-generals residue survives only at session boundaries — exactly what a ±1
skew window absorbs. The verdict procedure is then clean and mechanical:

- **Silence = outage.** Affects every relationship at once. Global, innocent.
- **Wrong door beyond ±1 = divergence.** Rollback, stale-backup restore, or stolen keys
  without the history — affecting exactly one relationship. Local, never innocent.

Trust verdicts become local per relationship and cheap to compute — maximum skepticism with
a decision procedure (falsifier F-DE5).

**Honest assessment — integrity signaling, not confidentiality.** Inside a tailnet,
WireGuard already authenticates every packet and an insider scans 64k ports in seconds; ACLs
own secrecy, so as a *secret* the hopping is ceremonial. Its real value is the tripwire: a
peer restored from a stale backup, rolled back, or impersonated-without-history **knocks on
yesterday's door** — the retired holder of the roaming role (§2.3) announces itself the
moment it wakes, by knocking on stale ports. Rollback/zombie detection at zero payload
bytes, which is precisely the transport-seam instrument a fleet of mutually-skeptical
individuals needs. Each successful contact advances the pair's counter: the port sequence is
the pairwise event clock made physical — *clockwork, literally* (§2.2).

**The sharp edge is a feature.** Transcript-chaining means losing state = losing the
relationship. Re-keying is therefore an explicit, LOUD, logged, owner-visible ceremony —
relationship repair must never be silent (whether owner-mediated or peer-negotiable with
notification is an open question, OQ-10).

**The dialogue stratum.** The conversation between two individuals is recorded into its own
strata dialogue layer, and each party weaves its **own** record of the shared dance — joint
authorship, separate corpora, NN-11 intact. The stratum is not merely a log: **the stratum
IS the transcript the next port derives from** — the record and the credential are one
object. Whether the stratum carries the derivation state or only the transcript it derives
from (state reconstructible = migration-proof; state stored = faster) is carried as OQ-14.

### 2.5 Storage — sealed at rest, alive only in memory

Owner seeds (capsules 5–6, near-verbatim): *"core panics trigger system seals; data at rest
will need to be encrypted as well (the sqlite dbs) — so this means a host only sees
relationships, not the data it references"*; *"doesn't sqlite live in memory when in use?
which means it can be decrypted as part of unseal in memory; the disk copy is encrypted;
writes immediately encrypt and backup."*

#### 2.5.1 Panic→seal — recovery mode made cryptographic

Recovery mode (live today: `ops/lifecycle/launcher.py` holds the scheduler read-only after
an unclean exit until an operator clears the cause) is the same fail-closed instinct one
layer up. The seal is its cryptographic twin one layer *down*: in-memory data keys are the
only bridge from ciphertext to plaintext; the panic handler zeroizes them; a watchdog covers
non-cooperative death; and **every boot comes up SEALED by default** — unseal is a ceremony,
automatable per body-class (Keychain-backed at home, as `ops/vault/vault-unseal.sh` already
does for the vault; attestation-bound in cloud ⚑R2). The move generalizes vault semantics
from the secrets store to the whole individual. Which panics seal versus merely restart is
an open question with a live lesson attached (OQ-15: a seal that fires on every crash makes
the ceremony routine, and routine ceremonies stop being ceremonies).

#### 2.5.2 The in-memory refinement — the disk never sees plaintext

The owner's premise needs one correction, and the design survives it: stock SQLite is
disk-paged, not memory-resident — but SQLite has **native machinery for exactly this
scheme**: `sqlite3_deserialize` loads a whole DB image from a buffer into `:memory:`;
`serialize`/`VACUUM INTO` emits one back. So: **unseal → decrypt blob → deserialize into
memory → operate; the disk artifact is only ever ciphertext.** Not a fight against SQLite; a
supported mode.

*"Writes immediately encrypt and backup"* is **WAL-shipping**, and it unifies two needs:
per-write full-image re-encryption would be absurd; the right shape is an encrypted
append-log — each committed write emits one encrypted record to disk immediately (the
durability boundary is that record's fsync), with periodic full-snapshot checkpoints. **The
same encrypted log SHIPS as the cloud backup stream** — point-in-time recovery and capsule
4's "encrypted backups in the cloud" fall out of one mechanism (per-store granularity —
queue vs ledger vs vector store have different write tempos — is parked, DE-f).

**Crash = seal, by physics.** If plaintext exists only in RAM, panic→seal stops being
handler code and becomes a property of volatile memory: any death — panic, SIGKILL, power —
IS a seal event. There is no half-open state to recover from; boot can only enter through
the ceremony. Fail-closed by construction beats fail-closed by discipline (the
structural-enforcement rule, applied to key material). Two caveats are **part of the spec,
not afterthoughts**: `mlock` for key/plaintext pages and verified-encrypted swap per
body-class (macOS default-encrypts swap; a Linux body must prove it), and hibernation images
(falsifier F-DE7 covers all three sideways paths).

#### 2.5.3 Host-sees-relationships — field-level envelope, and the query plan as the boundary

The owner's phrasing — *"a host only sees relationships, not the data it references"* —
selects field-level envelope encryption over whole-file (SQLCipher-style makes the host a
pure blob store; the owner's design is sharper and generative): the relational **skeleton**
(ids, edges, strata, status, timestamps) stays host-visible and host-indexable; every
**payload** column is ciphertext. Structure server-side; semantics core-side.

The jurisdiction machinery is the sibling's, adopted, not re-derived: dn-scoped-context-
queries §2.4 (duty 2) defines the compiled query plan's **jurisdiction annotation** —
temporal + authority bounds evaluate host-side on the plaintext skeleton; the semantic bound
evaluates only in-core, after decryption. One query, two jurisdictions; **the query plan is
the privacy boundary**, and the compiler that translates a question into bounds is the same
machinery that decides what a host may compute. What THIS note owns is the storage-side
counterpart: the **column-by-column schema audit** (skeleton | payload) as a concrete
graduation artifact, with the fail-closed rule — *any ambiguous column defaults to payload*
(some "metadata" is content: titles, status strings, finding summaries).

#### 2.5.4 ⚑ The vector falsifier — vectors are content, not structure

Embedding inversion recovers text from vectors to a workable degree; server-side ANN would
hand the host the GEOMETRY of the mind with every payload encrypted. So "host sees only
relationships" survives only if **vectors are payload**: ciphertext at rest, the similarity
index living in-core, rebuilt at unseal. The rebuild is trivial at today's ~27k rows and a
real cost at 27M — **the rebuild-at-unseal cost curve is a measurable design input**, and
the vectors-as-payload default holds until that measurement forces a ruling (parked, DE-e;
falsifier F-DE8 kills §2.5.3's claim if the default is ever silently relaxed).

#### 2.5.5 The access-pattern leak — accepted, and classified ⚑R1

Even with all content opaque, traffic analysis sees the *tempo* of thought: which blobs are
fetched together, when, how often. ORAM exists and is heavy; the honest position is to
**accept the leak and classify it** — and the classification is exactly the adapter argument
presented in §2.0/R1: a store that leaks interactions-but-not-content is, in the
constitution's own taxonomy, an adapter surface under NN-11's opt-in clause. This section
supplies the argument's technical premise; the ruling remains the owner's, and the default
remains owned storage.

#### 2.5.6 Durability is cheap because the stores are views

The launcher already rebuilds an empty cache from sources — "reconcile the corpus"
(`ops/lifecycle/launcher.py:4,:536,:743`, live): truth lives in the artifact chain + sensors,
and sync jobs are re-runnable. A lost log tail is a re-sync, not a loss. The in-memory
scheme's durability bar is low precisely because the system was already built with
rebuildable stores — the materialized-view property, now load-bearing (falsifier F-DE9).

### 2.6 The physical overlay — location is a trust modifier, never an authenticator

The owner's closing seed (capsule 7, near-verbatim): *"Is it possible for the network
gateway to access a VPC directly, so me being in my home network is more secure? Think of it
as an extended space, a network extension. And different wifis for guests, my partner and I,
and admin needs. … This doesn't mean we don't authenticate anymore — WE DO — but this is
just another layer of trust; I can still access from different wifis but with more limited
access."*

**Two extension mechanisms, one already half-built:** Site-to-Site IPsec (router ⇄ AWS VPN
Gateway, subnets routed natively) versus **Tailscale subnet routers at both ends** (the home
box advertises LAN routes; a small VPC instance advertises the VPC CIDR — the existing
overlay becomes the extension). The second makes §2.3's overlay-boundary sentence literal
infrastructure with hardware mostly in hand; the lean is recorded, the decision parked with
the router purchase (DE-h).

**SSID→VLAN trust tiers:** guests (internet-only, isolated) · household (LAN, no admin
surfaces) · admin (the only VLAN routed into the overlay/VPC; the palace and vault live
behind it).

**The law, the owner's own words kept verbatim: location is a trust MODIFIER, never an
authenticator.** VLAN decides *reach*; identity decides *access*; authentication happens
everywhere regardless — **reach by network tier, access by identity, authentication
always.** Composition with the overlay: device identity carries the tailnet ACL tag, the
VLAN bounds which surfaces are even routable, so "same person, guest wifi" degrades
gracefully to the exhaust lane instead of failing open or closed (falsifier F-DE10). This is
the rendezvous-ratchet philosophy at the RF layer: the network is a filter; identity is the
gate. Whether the admin VLAN's overlay route makes the home LAN part of the node-injection
boundary — and whether that boundary is then listed per-VLAN in the constitution's adapter
terms — is carried as OQ-17.

### 2.7 The resource model grows axes — one refusal machinery, several axes

NN-8's principle — *the scheduler refuses breaching work* — is already load-bearing on one
axis and now provably needs three:

| axis | status | evidence |
|---|---|---|
| memory | built | the ≤2-resident-models / ~20–24 GB ceiling; the scheduler refuses breaching work today (NN-8 as written) |
| energy | filed 2026-07-28 | finding-0279 — two battery emergencies in four days, one fatal: 100%→8% in 2h40m under backlog compute; the 2026-07-24 death cost three days |
| corpus residency | new here | the §2.5.2 in-memory store competes with model residency — ~hundreds of MB at 27k rows, real at millions |

finding-0279 (glossed: *"Energy is an unmodeled resource axis"* — an open `design` finding
filed 2026-07-28 after the daemon's compute profile twice outran the laptop's power
envelope; its proposed direction is a power-state preflight sensor, drain-slow shedding, and
a clean hold below ~20%) supplies the second axis's warrant; this note adds the third: an
unsealed in-memory corpus is resident state the scheduler must count, exactly like a
resident model. **The design rule: one refusal machinery, several axes** — new axes enter as
sensors feeding the existing refusal logic, never as parallel mechanisms (falsifier F-DE11).
Per-body-class sensors follow (a cloud body's "energy" is a metered budget, not a battery —
OQ-18).

## 3. Consequences

What this note licenses, **on ratification and not before** — sequenced by gate, because the
§2.0 rulings partition the space:

1. **Gated on ratification only (no §2.0 dependency):**
   - *The sealed-storage wave for owned nodes* (§2.5): the schema audit (skeleton | payload,
     ambiguous→payload), the seal/unseal ceremony generalizing `vault-unseal.sh`, the
     in-memory deserialize path + encrypted WAL-shipping, mlock/encrypted-swap verification.
     Plaintext never rests, on hardware the owner already owns — no ruling touched.
   - *The energy axis* (§2.7 with finding-0279): the power preflight sensor and refusal
     wiring. Small, pattern-matching, already warranted.
   - *The overlay tiers* (§2.6): VLAN/SSID design ready for the hardware conversation when
     the owner buys the router (purchase itself stays parked, DE-h).
2. **Gated on the deployment park re-opening (DE-c — a second individual exists):** the
   rendezvous ratchet + dialogue stratum (§2.4), the inter-individual governance protocol
   (§2.2), fleet drift telemetry (§2.1).
3. **Gated on R1 (owner rules the NN-11 question):** any corpus-ciphertext residency in AWS
   beyond the existing restic backup lane; the WAL-ship target moving to S3.
4. **Gated on R2 (after R1):** the roaming role landing on cloud bodies; attestation-bound
   cloud unseal. Under the standing default, §2.3 deploys with the lease migrating among
   owned nodes only.

The sibling notes are consumers, not dependents: dn-scoped-context-queries' onboarding
surface gains its second client (fresh nodes) when tier 2 opens; dn-prediction-castles is
untouched by every tier.

## 4. Wiring & enablement

**How it wires:** nothing in this note is wired today, and this note builds nothing. The
connective tissue a graduating plan must build, named per tier of §3: (a) the **seal
config block** (e.g. `[seal] enabled=false`, per-store granularity table, watchdog cadence)
plus `palace seal-status` / an unseal entry in the lifecycle CLI — the ceremony scripts
generalizing `ops/vault/vault-unseal.sh` per body-class; (b) the **schema-audit artifact**
(skeleton | payload, checked into the repo, enforced at store-creation time so an unaudited
column cannot ship); (c) for tier 2+, the **lease substrate** (OQ-11 pins it), the
**injection ceremony** scripts, and the ratchet's band declarations in the tailnet ACL file.
Everything lands flag-off in a plan's write_scope; the ON switch EXISTS as part of each
deliverable (the wiring-is-part-of-finishing rule, owner 2026-07-22).

**What it takes to flip it on:** the full chain, honestly: (1) the owner ratifies this note
(hand edit, never an agent's); (2) for tier-1 items — a graduating plan builds the wiring
above behind `[seal] enabled=false`, then the owner flips it and runs the owner-visible
seed: kill the daemon mid-write, observe boot-sealed state, complete the unseal ceremony,
verify the store rebuilt and the log tail re-synced; (3) for tiers 3–4 — the §2.0 rulings,
owner-only, in order (R1 then R2), before any plan is even minted; (4) for tier 2 — the
deployment park's re-entry (DE-c) as recorded from the warrant. Until (1), traversal of this
note is all there is; until (3), the conservative defaults ARE the design.

## 5. Falsifiers

For each major claim, the observation that would kill it (claims of this note; inherited
falsifiers name their owners):

| id | claim | the observation that kills it |
|---|---|---|
| F-DE1 | speciation (§2.1) | corpus bytes cross an instance boundary by any channel, or an instance answers from a sibling's corpus rather than its own + pointers — a replica existed |
| F-DE2 | nature-pinned attribution (§2.1) | inter-individual drift attributable to neither nurture nor a nature bug under an identical anchor hash — the hash failed to pin nature |
| F-DE3 | aligned secrets (§2.2) | a harmony requirement satisfiable only by exchanging interior secret material — alignment demanded disclosure |
| F-DE4 | role lease (§2.3) | two live holders observed at once, or a retired body's action lands after lease transfer — the fencing token failed at fleet scale |
| F-DE5 | trust dichotomy (§2.4) | a wrong-door event beyond ±1 with an innocent cause over intact TCP — the dichotomy has a third case; verdicts stop being mechanical |
| F-DE6 | ratchet tripwire (§2.4) | a rollback / stale restore that knocks INSIDE the ±1 window and passes — the skew tolerance swallowed the tripwire |
| F-DE7 | crash = seal (§2.5.2) | plaintext found at rest after any unclean death — swap page, hibernation image, core dump — the spec had a sideways path |
| F-DE8 | host-sees-relationships (§2.5.3–4) | host-visible columns shown to reconstruct payload semantics — the ⚑ embedding-inversion falsifier, owned here |
| F-DE9 | rebuildable views (§2.5.6) | a lost log tail not recoverable by re-sync — a store held truth absent from the artifact chain + sensors |
| F-DE10 | location law (§2.6) | any reachable path where network position alone grants access without identity authentication — location became an authenticator |
| F-DE11 | one refusal machinery (§2.7) | a resource axis needing its own separate refusal mechanism rather than a sensor feeding the scheduler's — the model fragmented |

Rows the table compresses: **F-DE1** fires on the *structural* claim — NN-11 was supposed to
make replication unconstructible, so a replica observed by any route is a constitutional
breach, not a bug. **F-DE2**'s exemplar is unpinned dependency divergence — two "identical"
natures behaving differently. **F-DE6** is OQ-9's live edge: n−1 is tolerable, n−k (k>1) is
the tripwire; a tripwire case passing inside tolerance kills the window's design. **F-DE8**
also fires if vectors are ever host-side-indexed without the DE-e ruling — server-side ANN
hands the host the corpus's geometry even with every payload encrypted.

## Parked decisions

Each with the recorded default and re-entry condition, carried faithfully from the warrant
capsules (rows terse per the table rule; §2.0 holds the substance of the first two):

| id | decision | default recorded | re-entry condition |
|---|---|---|---|
| DE-R1 | ⚑ ciphertext corpus at rest in AWS — NN-11 letter vs spirit (§2.0) | corpus on owned storage; restic backups the only cloud presence | OWNER-ONLY constitution-level ruling |
| DE-R2 | ⚑ plaintext-on-rented-RAM — the role on cloud bodies (§2.0, §2.3) | Posture A: owned nodes only; cloud holds ciphertext | owner rules the attestation frontier, AFTER DE-R1 |
| DE-c | actually deploying a second instance | Ouroboros remains the only living individual | owner ratifies a graduated note, or asks to bootstrap scoped creds for a named environment |
| DE-d | credential bootstrap ceremony | owner's creds via SSO for near-term infra work | DE-c re-opens; finding-0276's IAM-separability inversion is the design input |
| DE-e | vectors: payload or skeleton (§2.5.4) | payload — fail-closed; in-core index | row count nears the rebuild-at-unseal pain threshold — measure, then rule |
| DE-f | log-record vs snapshot granularity per store (§2.5.2) | WAL-shipping shape; per-store tempo unpinned | graduation; pinning needs measured per-store write tempos |
| DE-g | does "like clockwork" re-open the dreamer's G3 park (§2.2) | the park stands as written | owner reads the capsule; PR #6 §2.6's grounding informs any re-write |
| DE-h | router hardware + extension mechanism (§2.6) | current router; overlay reaches AWS device-by-device | owner buys hardware; the subnet-router lean is recorded |
| DE-i | ratchet adoption into the inter-instance protocol (§2.4) | no second instance; the tailnet carries only the exhaust lane | DE-c re-opens (a second individual is minted) |

Rows the table compresses, carried faithfully from the capsules: **DE-R1** arrives with the
adapter argument attached (§2.5.5 — the capsule-5 sharpening of the capsule-4 park: "the
same OWNER-ONLY ruling, now with the adapter argument attached"); an agent may never
reinterpret a non-negotiable, which is why the row's re-entry names no condition an agent
could satisfy. **DE-d**'s ceremony must declare who mints, the max-scope declaration, and
the audit trail (the NN-6 minted-agent pattern applied to infra credentials); its design
input is finding-0276 — measured on GitHub, merge is not a separable permission and the
agent is indistinguishable from the owner, whereas IAM can separate nearly anything: scoped
per-instance roles under permission boundaries, admin retained at the owner's SSO. **DE-g**'s
long form: sibling PR #6 §2.6 verified the spine is ratified per-store-partial with
certified cuts BUILT — no global clock exists to depose; if the reframe holds, the dreamer's
park condition is *rewritten* rather than waited on. **DE-h**'s two candidates: IPsec
site-to-site vs tailscale subnet routers at both ends. **DE-i**'s default in full: nothing
binds beyond ollama 11434 and vault 8200 (loopback-only); the tailnet carries only the
exhaust lane today.

## Open questions

Carried faithfully from the warrant capsules (OQ-1..17), then added by this note (OQ-18+):

1. **The minimal viable individual** — which organs are load-bearing for a fresh corpus in a
   new environment, and which are Ouroboros-specific history?
2. **Who blesses remotely?** Both owner-only gates assume a keyboard; a remote instance
   needs an authenticated blessing channel (the NN-12 passphrase/callback pattern —
   telephony's authenticate-the-human-first rule — generalized).
3. **Drift baseline for a fresh individual** — calibrated against its own founding state, or
   fleet-relative? (Nature-pinned-by-hash suggests: against founding, compared across the
   fleet.)
4. **Cross-pollination** — is another instance's pointer stream just another edge sensor
   with a provenance tag, and does maximum skepticism type it lowest-trust-by-default?
5. **Nature updates** — is upgrading an instance a blessing-gated self-mod (NN-5) per
   individual, and is a fleet running mixed nature versions a natural experiment or a
   hazard?
6. **The meshing event's artifact type** — is an inter-instance pointer exchange itself a
   typed, logged interaction? (It must be, for the cohort study to read causality.)
7. **Does clock meshing need wall-clock at all**, or only ordering? (Deploy attestation and
   drift windows currently assume wall-clock.)
8. **Is the transcript the message log or its hash chain** — and does the hash chain double
   as the pair's shared event clock (one structure, both uses)?
9. **The ±1 window's exact semantics** — a knock at n−1 within tolerance while n−k (k>1) is
   the tripwire: does the tolerance weaken divergence detection enough to matter (F-DE6's
   live edge)?
10. **Re-keying ceremony** — owner-mediated for instance pairs (parallel to the blessing
    gates), or peer-negotiable with owner notification?
11. **The role lease's substrate** — Vault lock, DynamoDB conditional write, or the run
    ledger generalized; and does the lease record live INSIDE the corpus (the system knows
    who embodies it) or beside it?
12. **Node injection's minimal set** — constitution anchor + vault unseal + corpus pointer +
    lease grant; is each step attested?
13. **Retirement verification** — KMS key deletion has a waiting period: is
    schedule-delete + alias-flip a sufficient fencing token during the window, and what does
    fencing look like at the tailnet layer (key expiry vs ACL revocation)?
14. **Does the dialogue stratum carry the port-derivation state**, or only the transcript it
    derives from (state reconstructible = migration-proof; state stored = faster)?
15. **The panic taxonomy** — which panics seal (integrity violations, constitution-anchor
    mismatch) vs merely restart (transient OS errors)? A seal firing on every crash makes
    the unseal ceremony routine, and routine ceremonies stop being ceremonies.
16. **Who can unseal which body-class**, and is unseal itself logged as a typed artifact?
17. **Does the skeleton include the reference graph** (edges = relationships, the thing the
    host explicitly MAY see) — and is that acceptable when edge density itself is a
    self-map signature? Relatedly (capsule 7): does the admin VLAN's overlay route make the
    home LAN part of the node-injection boundary, listed per-VLAN in adapter terms?

Added by this note (beyond the capsules):

18. **Energy per body-class** — a cloud body's "energy" axis is a metered budget, not a
    battery: does the NN-8 refusal machinery read a spend sensor the way finding-0279
    proposes it read `pmset`, and who sets the budget?
19. **Is the lease handoff itself a dialogue event** — does the outgoing→incoming holder
    transfer transit the rendezvous ratchet (making handoff transcript-chained and
    rollback-evident), or is it vault-mediated only?
20. **Is a body swap visible in the drift instruments** — the owner's *"bouncing between
    machines and never notice (it would — figure of speech)"* made testable: which gauge
    detects a lease transfer, and MUST one (if identity is truly role-not-hardware, an
    undetectable swap is the design succeeding; an unexplained detectable one is F-DE2
    territory)?
21. **mlock scope and encrypted-swap verification per body-class** (carried from capsule 6's
    open list into the §2.5.2 spec): macOS default-encrypts swap; a cloud Linux body must
    prove it — what is the proof artifact?

## Cross-references

- `docs/brainstorms/the-distributed-ecosystem.md` — **THE WARRANT**: all seven capsules,
  2026-07-28 (02:58Z, 03:14Z, 03:41Z, 04:55Z, 05:07Z, 05:09Z, 05:14Z); owner seeds kept
  near-verbatim above; the measured tailnet facts (ouroboros 100.97.85.13; WireGuard UDP
  41641; vault 8200 loopback-only; ollama 11434 — measured 2026-07-28).
- **dn-scoped-context-queries** (PR #5, draft) — the authority bound as Σ-refinement and
  jurisdiction as a compiled-plan annotation (§2.2.2, §2.4 there; adopted in §2.3/§2.5
  here); the fresh-node onboarding organ (§2.1 there).
- **dn-prediction-castles** (PR #6, draft) — sibling; its §2.6 clock grounding informs
  DE-g; otherwise disjoint by its own non-goals.
- `docs/design-notes/agent-taxonomy.md` (`dn-agent-taxonomy`, RATIFIED) — role = scope
  signature; the roaming role's type.
- `docs/design-notes/role-state-and-scoped-handoff.md` (`dn-role-state-and-scoped-handoff`,
  RATIFIED — verified 2026-07-28) — role as typed seat, scoped handoff; the lease's
  single-node artifact shape.
- `docs/design-notes/dn-supervision-and-liveness.md` (RATIFIED) — §2.6 "the supervisor ROLE
  is kernel-exclusive"; the lease vocabulary, already ratified at single-node scale.
- code, verified on disk 2026-07-28 at `4c00ca5`: `ops/lifecycle/lock.py` (SupervisorLock —
  flock, acquire-or-fail, bp-108); `ops/lifecycle/launcher.py` (identity-gated start,
  bp-105; "reconcile the corpus" at `:4,:536,:743`); `scheduler/queue.py:474`
  (`sweep_orphans`; `OrphanSweep` `:237`); `ops/vault/vault-unseal.sh` +
  `ops/vault/com.mind-palace.vault.plist` + `ops/vault/vault.hcl:17` (loopback 8200);
  `ops/vault/setup_aws_engine.sh` (1h-TTL dynamic creds); `ops/backup/backup.sh:3` +
  `ops/backup/plan.py` + `ops/backup/com.mind-palace.backup.plist` (restic, client-side
  encryption); `ops/effect_exec.py:88,:105,:117,:132` + `edge/effectors/writes.py` (Track G
  JIT executor, propose-never-send).
- `docs/findings/finding-0186.md` (RESOLVED — the single-instance gate; the §2.3
  correction); `docs/findings/finding-0011.md` (ROUTED — Track G flag-off, unwired, max
  reachable tier NONE; the §2.3 honesty); `docs/findings/finding-0276.md` (OPEN — GitHub
  credential collapse; IAM separability, DE-d's input); `docs/findings/finding-0279.md`
  (OPEN — the energy axis, §2.7).
- `docs/brainstorms/aws-as-the-outer-plane.md` — cloud agents have no corpus access by
  construction; the provisioning-triple reading; the measurement-before-architecture rule.
- `docs/brainstorms/study-not-product.md` — the study frame (§1.2's last non-goal) and the
  identity-in-control frame the fleet must serve.
- CLAUDE.md non-negotiables NN-1, NN-2, NN-5, NN-6, NN-8, NN-9, NN-10, NN-11, NN-12 — each
  glossed at first use above.
