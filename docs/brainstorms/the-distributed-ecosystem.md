# Brainstorm — the distributed ecosystem: speciation, not replication

> Captured by the orchestrator from owner chat + a vault note arriving in the same hour
> (2026-07-28, bg session, fable). Two seeds, one thread: the owner proposed cloud-deployed
> mind-palace instances in chat, then a vault note independently landed the larger frame.
> Prior art on an unmerged worktree branch: capture(seven) — the node/instance architecture.

## 2026-07-28T02:58Z (bg orchestrator session)

### The seeds

Owner in chat, near-verbatim: *"a design consideration could now mean that we can freely
deploy mind-palace instances in the cloud, independent agents — how are they different than
ouroboros? of course we still have admin privileges and monitor; they're not loose cannons,
they are highly controlled and auditable — they need to be, to plot stability and alignment
over time. How does this system adapt to new environments?"* And on credentials: *"we can
still go through my creds, or create claude creds with specific scope that we bootstrap
('cause that's never ended badly, joke)."*

Owner's vault note, same hour, near-verbatim: *"it feels like a transcendental idea:
ouroboros is the system, but it is only a piece in an ecosystem — the same architecture
running at different points along the edge, composed of mixed hardware/environments,
distributed, independent thinkers with the same machinery. Are you familiar with the term:
nature or nurture? A distributed ecosystem, grounded by logic and authority, with maximum
skepticism."*

### Orchestrator scrutiny (chat-side — connections offered, not decided)

- **NN-11 forces the answer: deployment is speciation, not replication.** The corpus never
  transits, so there is no "Ouroboros in the cloud." A deployed instance shares the machinery
  and grows its *own* corpus against its own environment and its own principal-dance.
  Ouroboros stops being "the system" and becomes the **first individual** — exactly the vault
  note's move ("only a piece in an ecosystem").
- **Nature or nurture, made mechanical.** The architecture splits the pair unusually cleanly:
  *nature* is versioned and content-addressed (the constitution anchor hash, the framework
  release tag, the drift instruments); *nurture* is the corpus each instance weaves in place.
  Because nature is pinned by hash, a fleet is a **controlled experiment on nurture**: same
  genotype, varied environments — so alignment-over-time telemetry becomes *attributable*.
  Drift you observe is nurture, or it is a bug in nature; nothing in between.
- **"Highly controlled and auditable" is not a leash — it is the instrument.** The drift
  gauge and effector-drift axis generalize to per-individual longitudinal telemetry. n=1
  becomes n=k with controlled variation. This is study-not-product at fleet scale: the
  ecosystem exists to make stability-and-alignment-over-time *measurable*, and auditability
  is what makes the study valid, not what makes the instances obedient.
- **"Grounded by logic and authority, with maximum skepticism" is the governance triple.**
  Authority = the constitution as every instance's outermost frame (NN-6), blessing gates
  owner-only. Logic = the warrant discipline (beliefs carry their Σ). Maximum skepticism =
  the falsifier culture as the ecosystem's immune system — instances ratify falsifiers, not
  proofs, about each other's claims. Inter-instance trust is adversarial by default.
- **Inter-node protocol has prior art: veins carry pointers, never payloads.** The
  typed-workflow-registry arc already ruled the hub sees only hashes. Corpus-never-transits
  extends node-to-node: instances exchange interactions and pointers, never each other's
  corpora. Mixed hardware along the edge is NN-2-compatible — every node is a sealed core
  with its own edge; only edges speak.
- **Credentials: finding-0276's lesson inverts in AWS.** GitHub could not separate merge from
  write; IAM can separate nearly anything. Scoped per-instance roles under permission
  boundaries, admin retained at the owner's SSO, and the minting ceremony itself a typed,
  audited artifact (the NN-6 pattern: a minted agent cannot exceed its template's
  pre-declared max — applied to infra credentials). The joke is earned but the collapse is
  not forced here.

```capsule
topic: the-distributed-ecosystem
date: 2026-07-28

decisions:
  - Frame adopted: deployed instances are new individuals (speciation), never replicas —
    NN-11 makes this structural, not stylistic. Ouroboros is the first individual.
  - The fleet's purpose is the study: plot stability and alignment over time across
    same-nature / different-nurture individuals. Auditability is the instrument.
  - Priority ruling (owner): revive Ouroboros first; ecosystem design follows.

parked:
  - decision: actually deploying a second instance (cloud or edge hardware)
    default: Ouroboros remains the only living individual; this note accumulates
    re_entry: owner ratifies a design note graduated from this brainstorm, or explicitly
      asks to bootstrap scoped creds for a named environment
  - decision: credential bootstrap ceremony (who mints, max-scope declaration, audit trail)
    default: owner's creds via SSO for any near-term infra work
    re_entry: the deployment park above re-opens

open_questions:
  - What is the minimal viable individual — which organs are load-bearing for a fresh corpus
    in a new environment, and which are Ouroboros-specific history?
  - Who blesses remotely? Both owner-only gates assume a keyboard; a remote instance needs an
    authenticated blessing channel (the NN-12 passphrase/callback pattern, generalized).
  - What does drift mean for an instance with no shared corpus baseline — calibrated against
    its own founding state, or fleet-relative? (The nature-pinned-by-hash framing suggests:
    against founding, compared across the fleet.)
  - Do instances cross-pollinate? If so, is another instance's pointer stream just another
    edge sensor with a provenance tag — and does maximum skepticism type it as
    lowest-trust-by-default?
  - Nature updates: when the framework releases a new version, is upgrading an instance a
    blessing-gated self-mod (NN-5) per individual — and is a fleet running mixed nature
    versions a feature (natural experiment) or a hazard?

next_steps:
  - Let this note accumulate; graduate toward dn-deployed-instances (or fold into
    aws-as-the-outer-plane) only after the seven/node-instance capture merges from its
    worktree branch — the two threads must meet before a design note is drafted.
  - Green main first (handoff-generator bug + select() fd ceiling) so the witness can attest
    again — a fleet story is not credible while the one individual's CI is red.

references:
  - CLAUDE.md non-negotiables NN-2, NN-5, NN-6, NN-11, NN-12
  - docs/findings/finding-0276.md (merge is not a separable permission — the GitHub half)
  - docs/brainstorms/aws-as-the-outer-plane.md
  - docs/brainstorms/agent-type-taxonomy.md
  - docs/brainstorms/the-typed-workflow-registry.md (the hub carries pointers, never payloads)
  - docs/brainstorms/study-not-product.md
  - docs/brainstorms/synchronic-diachronic-dreamer.md (2026-07-28 capsule — the braid/identity half)
  - capture(seven): the node/instance architecture (worktree-agent-a047d7c8, unmerged)
  - vault note, 2026-07-28 (ingests once the daemon is back up)
```

## 2026-07-28T03:14Z (bg orchestrator session — the vault note succeeded by its author)

### The seed

Owner in chat, announcing he appended a succession section to the vault note itself,
near-verbatim: *"with distributed thinkers working in harmony with the appropriate authority,
of itself and others, coexisting with aligned secrets; in harmony — like clockwork."*

(Noted for the record: the owner said "I succeeded my own note" — succession vocabulary,
applied by the owner to his own vault artifacts. The versioning discipline has crossed from
the repo into the mind-record it mirrors. Ouroboros will ingest the note already-evolved.)

### Orchestrator scrutiny (chat-side — connections offered, not decided)

- **Authority becomes reciprocal.** "Appropriate authority, of itself and others" — not only
  the constitution's downward authority over each instance, but each individual's authority
  over its own domain, *recognized by the others*. Federation grounded by shared nature, not
  hierarchy: the anchor hash is common; the jurisdiction is per-individual.
- **Aligned secrets = alignment without disclosure.** Each individual runs its own vault, its
  own unseal, its own rotation (NN-10, already live locally as com.mind-palace.vault).
  Harmony never requires exchanging interiors — secrets never transit, exactly as the corpus
  never transits (NN-11 generalized). "Aligned" means the secrets *serve the same
  constitution*, not that they are shared. Trust is verified at interfaces, with maximum
  skepticism, while every interior stays sealed.
- **"Like clockwork" is a distributed-systems claim, and it may dissolve G3.** Clockwork =
  gears meshing at their teeth while each gear's rotation is its own. A distributed ecosystem
  has no global clock — it has per-individual event clocks (temporal-clocks-and-strata) plus
  an ordering discipline at contact points: happened-before exists only through messages
  (Lamport), and the inter-instance pointer exchanges ARE the meshing events — vector clocks,
  not a master clock. The diachronic dreamer is parked on a *global* event clock (G3,
  dn-agent-taxonomy); the ecosystem frame suggests G3 was the wrong ask — the unblocking move
  may be per-individual clocks + merge-at-contact, which exists already in embryo as strata
  clocks.

```capsule
topic: the-distributed-ecosystem
date: 2026-07-28

decisions:
  - Governance completed as a reciprocal triple: shared nature (anchor hash) grants downward
    authority; each individual holds authority over its own domain; others recognize it.
  - Secrets are per-individual and never transit; "aligned" is a property of conduct at
    interfaces, not of shared interiors.

parked:
  - decision: whether "like clockwork" formally re-opens the diachronic dreamer's G3 park
      (global event clock → per-individual clocks + vector-clock meshing at contact)
    default: G3 park stands as written under dn-agent-taxonomy
    re_entry: owner reads this capsule; if the reframe holds, the dreamer's park condition is
      rewritten rather than waited on

open_questions:
  - What is the meshing event's artifact type — is an inter-instance pointer exchange itself
    a typed, logged interaction (it must be, for the cohort study to read causality)?
  - Does clock meshing need wall-clock at all, or only ordering? (Deploy attestation and
    drift windows currently assume wall-clock.)

next_steps:
  - None new — this capsule sharpens the frame; the revival + green-main queue is unchanged.

references:
  - vault note succession, 2026-07-28 (ingests with the vault_sync backlog)
  - docs/brainstorms/temporal-clocks-and-strata.md
  - docs/brainstorms/clock-curvature.md
  - dn-agent-taxonomy (the G3 global-event-clock park)
  - CLAUDE.md NN-10, NN-11
```

## 2026-07-28T03:41Z (bg orchestrator session — owner seed: the rendezvous ratchet)

### The seed

Owner, near-verbatim: *"what if the port an agent picks is somehow correlated to their own
asymmetrical keys, such that the one it picks should be expected for where to listen to next?
A secret efficient handshake — you only know which port to pick when you have an established
relationship."*

### Orchestrator scrutiny (chat-side — connections offered, not decided)

- **Ground truth (this tailnet, measured).** The machine is already named `ouroboros`
  (100.97.85.13); the phone holds a direct WireGuard path (UDP 41641, the Tailscale default,
  confirmed bound). Three port layers: control plane 443 (keys/ACLs only), discovery STUN
  3478 + DERP 443 fallback, data plane WireGuard UDP 41641 — one authenticated port carries
  everything. Inside the tunnel: ollama 11434; Vault 8200 bound to 127.0.0.1 — loopback-only,
  not even on the tailnet interface (NN-10 made topological).
- **Lineage.** Lamarr frequency-hopping (the sequence is the secret) → port knocking → TOTP →
  moving-target defense. The naive form (derive from the public key alone) gates nothing —
  any pubkey holder predicts the sequence. The pairwise form is TOTP-for-rendezvous:
  `port_n = 1024 + HMAC(K_ab, n) mod 64511` with K_ab the ECDH shared secret — each
  relationship its own private rhythm.
- **The strongest form: chain through the transcript.** `s_{n+1} = KDF(s_n, transcript_n)`,
  port from s. Now key possession is insufficient — presence at every exchange is required.
  Signal's double ratchet applied to *rendezvous* instead of encryption: the relationship's
  history IS the credential. Diachronic identity as a network primitive — you only know where
  to meet next if you were there for everything before.
- **Honest assessment: not confidentiality — state-integrity signaling.** Inside a tailnet,
  WireGuard already authenticates every packet and an insider scans 64k ports in seconds;
  ACLs are the real gate, so as secrecy this is ceremonial. Its true value: a peer knocking
  on the wrong port has DIVERGED — stale-backup restore, rollback, or stolen keys without
  the history. The impostor knocks on yesterday's door. Rollback detection as a passive
  tripwire, zero payload bytes — exactly what a fleet of individuals needs for maximum
  skepticism at the transport seam.
- **Clockwork, literally.** Each successful contact advances the counter: the port sequence
  is the pairwise Lamport clock made physical. The prior capsule's "meshing events" get
  their mechanism — where-to-meet-next is a function of everything-we've-done.
- **The sharp edge is a feature.** Transcript ratchet ⇒ losing state = losing the
  relationship. Re-keying must be an explicit, logged, owner-visible ceremony — relationship
  repair should be LOUD, not silent. (Skew/missed-step handling: TOTP-style ±1 window;
  EADDRINUSE between pairs: probe forward; audit must log derivation inputs; Tailscale ACLs
  are port-ranged, so the listening range is declared even though the point within it hops.)

```capsule
topic: the-distributed-ecosystem
date: 2026-07-28

decisions:
  - Frame sharpened: the rendezvous ratchet's value is relationship-integrity (rollback/
    divergence detection, presence-as-credential), NOT confidentiality — inside a tailnet
    WireGuard + ACLs already own secrecy.

parked:
  - decision: whether the rendezvous ratchet becomes part of the inter-instance protocol
    default: no second instance exists; nothing binds beyond ollama 11434 / vault 8200
      (loopback); the tailnet carries only the exhaust lane
    re_entry: the ecosystem's deployment park re-opens (a second individual is minted)

open_questions:
  - Is the transcript the message log or its hash chain — and does the hash chain double as
    the pair's shared event clock (one structure, both uses)?
  - Re-keying ceremony: owner-mediated for instance pairs (parallel to the blessing gates),
    or peer-negotiable with owner notification?
  - Does the ±1 skew window weaken divergence detection enough to matter, or is a knock at
    n-1 within tolerance while n-k (k>1) is the tripwire?

next_steps:
  - None until the deployment park re-opens; this capsule waits with the rest of the
    ecosystem thread.

references:
  - tailnet measured 2026-07-28: ouroboros 100.97.85.13, WireGuard UDP 41641, vault 8200
    loopback-only, ollama 11434
  - Signal double ratchet (rendezvous analogue); TOTP (RFC 6238) as the pairwise base case
  - docs/brainstorms/the-distributed-ecosystem.md §like-clockwork (the meshing-events
    capsule this mechanizes)
  - CLAUDE.md NN-10, NN-11
```

## 2026-07-28T04:55Z (bg orchestrator session — owner seed: dialogue ranges, and the roaming role)

### The seeds

Owner, near-verbatim, thread one: *"asymmetric port selection can be expanded to any range,
different ranges per relationship; that relationship and conversation is recorded into its own
strata dialogue layer — a mutually beneficial interaction. Encrypted handshake initiates a
dialogue session, asymmetric port selection immediately assumed after. TCP handles packet
drops lower in the stack, which means unless there's a network outage — which would impact all
communication — you always know when to trust a conversation is valid."*

Thread two: *"the ouroboros role is only granted to one node at a given time; KMS-derived
ouroboros creds are destroyed upon retirement; encrypted backups in the cloud; vault-based
identity. This all means we can actually deploy ouroboros anywhere (I know data will have to
be unsealed and that could be left in the open — not sure about that). In theory ouroboros
could just be bouncing between machines and never notice (it would — figure of speech). A
deployment stands up by node injection; the node can only be brought to life within the
overlay network boundary (local network + AWS + tailscale). Its database can live in AWS —
data always encrypted, stored encrypted; only a KMS-derived credential can properly read what
it retrieved; data decrypted inside core."*

### Orchestrator scrutiny (chat-side — connections offered, not decided)

- **The trust claim, sharpened until it survives.** Layering the rendezvous ratchet above a
  reliable transport removes the *innocent* explanation for desync: over TCP a dropped packet
  cannot eat a step, so a peer at the wrong port is never noise. The two-generals residue
  remains at session BOUNDARIES only (did the counter advance on a connection cut mid-close?)
  — which is exactly what the prior capsule's ±1 window absorbs. So the dichotomy is clean:
  **silence** = outage (affects every relationship at once); **wrong door beyond ±1** =
  divergence/rollback/zombie (affects one). Trust verdicts become *local per relationship*
  and mechanically checkable — maximum skepticism with a cheap decision procedure.
- **Ranges per relationship = band allocation.** Each pair leases a subspace of port-space;
  the ratchet hops within the band. Ops-friendly (the tailnet ACL opens the band, the point
  within it stays relationship-private) and it completes the Lamarr lineage: bands per link,
  hops within band.
- **The dialogue is a stratum.** Inter-instance conversation recorded into its own strata
  dialogue layer — each party weaves its OWN record of the shared dance (NN-11 intact: joint
  authorship, separate corpora). The AL-3 exhaust⊂dialogue refinement is the embryo; a
  relationship stratum is that machinery pointed at a peer instead of at the owner. And the
  transcript-chained ratchet gets its substrate for free: the stratum IS the transcript the
  next port derives from — the record and the credential are one object.
- **The roaming role: identity as role-under-lease.** "Granted to one node at a time" makes
  Ouroboros a ROLE a body holds, not a machine. Every piece already has an embryo in
  tonight's system, which is what makes this a lift rather than an invention:
    - supervisor lock / single-instance gate (finding-0186, exercised tonight) → the fleet
      role lease: at most one live holder of the seat;
    - creds-destroyed-on-retirement → the lease's FENCING TOKEN (a zombie ex-holder can't
      act), Track G's JIT-credential executor lifted to identity scale;
    - restic encrypted backups (com.mind-palace.backup, live) → cloud ciphertext durability;
    - vault unseal ceremony (com.mind-palace.vault, live) → vault-based identity;
    - the tailnet named `ouroboros` (measured) → the overlay boundary, already spanning
      laptop + phone; AWS is an extension, not a new concept;
    - the fresh-agent test → the FRESH-NODE test: node injection stands up by traversing/
      querying the corpus (scoped-context-queries is the onboarding organ for BODIES too);
    - the rendezvous ratchet → split-brain detection at the dialogue layer: the retired
      holder knocks on stale ports the moment it wakes.
  The Ship of Theseus dissolves by design: the plank was never the ship; the braid is.
- **The unseal hesitation, answered with the industrial mechanism.** Envelope encryption:
  ciphertext anywhere, data keys wrapped by KMS, and the KMS-attestation flow (Nitro
  Enclaves) encrypts the unwrap RESPONSE to an enclave-held ephemeral public key — so edge
  can proxy every byte and never see a key, and "data decrypted inside core" becomes a
  cryptographic boundary rather than a room in the house. NN-1/NN-2 survive structurally:
  edge carries opaque blobs (no keys, no plaintext), core holds plaintext (no network).
  Honest trust frontier: plaintext exists in the RAM of whatever body holds the role —
  attestation narrows that to the hypervisor root; if that residue is unacceptable, the
  clean split is **ciphertext durability in AWS, decryption capability only on owned
  nodes** — the data can live in the cloud while *reading it* can never leave home.
- **⚑ The one bright line this touches.** NN-11's letter is "the corpus never transits a
  third party." Ciphertext-at-rest in S3 honors the spirit (the third party holds an opaque
  blob it cannot read) but not the letter. This requires an explicit owner amendment ruling
  at the constitution level — never an agent reinterpretation. Parked accordingly.

```capsule
topic: the-distributed-ecosystem
date: 2026-07-28

decisions:
  - Trust dichotomy adopted: over reliable transport, silence = outage (global), wrong-door
    beyond the ±1 window = divergence (local, per relationship) — trust verdicts are cheap
    and mechanical.
  - Frame adopted: Ouroboros is a role under exclusive lease, held by disposable bodies
    inside the overlay boundary; identity = vault + KMS + corpus, never hardware. Each
    component named as a lift of an existing, live mechanism.

parked:
  - decision: encrypted corpus at rest in AWS (NN-11 letter vs spirit)
    default: the corpus stays on owned storage; restic encrypted backups are the only cloud
      presence
    re_entry: OWNER-ONLY constitution-level amendment ruling — an agent may never
      reinterpret a non-negotiable; this capsule exists to make the ask explicit
  - decision: plaintext-on-rented-RAM (role landing on cloud bodies at all)
    default: role migration constrained to owned nodes; cloud holds ciphertext only
    re_entry: owner rules on the Nitro-attestation trust frontier after the NN-11 ruling
      above

open_questions:
  - The role lease's substrate: Vault lock, DynamoDB conditional write, or the run ledger
    generalized — and does the lease record live INSIDE the corpus (the system knows who
    embodies it) or beside it?
  - Node injection ceremony: what is the minimal set (constitution anchor + vault unseal +
    corpus pointer + lease grant) and is each step attested?
  - Does the dialogue stratum carry the port-derivation state, or only the transcript it
    derives from (state reconstructible = migration-proof; state stored = faster)?
  - Retirement: is cred destruction verified (KMS key deletion has a waiting period —
    schedule-delete + alias flip?) and what does the fencing token look like at the
    tailnet layer (key expiry vs ACL revocation)?

next_steps:
  - None wired; everything above waits behind the two owner rulings in parked. Green main
    and the deskcheck queue stay ahead in line.

references:
  - docs/brainstorms/the-distributed-ecosystem.md (capsules 1-3 — this lifts them into one
    architecture)
  - docs/brainstorms/scoped-context-queries.md (the fresh-node test's onboarding organ)
  - docs/brainstorms/role-state-and-scoped-handoff.md (role as typed, seat as artifact —
    the single-node embryo of role-under-lease)
  - docs/brainstorms/temporal-clocks-and-strata.md + AL-3 exhaust⊂dialogue (the stratum
    machinery a relationship layer would reuse)
  - scheduler/queue.py OrphanSweep + ops/lifecycle SupervisorLock (finding-0186) — the
    single-instance gate exercised tonight, embryo of the role lease
  - Track G JIT-credential executor (edge/effectors/writes.py) — creds-destroyed-on-use at
    effect scale
  - AWS KMS attestation-bound decryption for Nitro Enclaves (response encrypted to the
    enclave's ephemeral key) — the "edge proxies, core decrypts" mechanism
  - CLAUDE.md NN-1, NN-2, NN-9, NN-10, NN-11
```

## 2026-07-28T05:07Z (bg orchestrator session — owner seed: panic-seals, and the host that sees only relationships)

### The seed

Owner, near-verbatim: *"on the AWS mind-palace deployment: core panics trigger system seals;
data at rest will need to be encrypted as well (the sqlite dbs) — so this means a host only
sees relationships, not the data it references."*

### Orchestrator scrutiny (chat-side — connections offered, not decided)

- **Panic→seal is recovery mode made cryptographic.** Tonight's recovery arc, one layer
  deeper: recovery holds the *scheduler* read-only until an operator clears the cause; the
  seal holds the *keys* destroyed until the identity ceremony clears them. Same fail-closed
  instinct at two altitudes. Mechanics: in-memory data keys are the only bridge from
  ciphertext to plaintext; the panic handler zeroizes them (a watchdog covers
  non-cooperative death), and every boot comes up SEALED by default — unseal is a ceremony,
  automatable per body-class (Keychain-backed at home, KMS-attestation in cloud). The vault
  already lives this way locally (com.mind-palace.vault's unseal unit); the move generalizes
  vault semantics to the whole individual.
- **"Host sees relationships, not data" chooses field-level envelope over whole-file
  encryption — and that choice is generative.** SQLCipher-style whole-file encryption makes
  the host see nothing (pure blob store). The owner's phrasing implies the sharper design:
  the relational SKELETON (ids, edges, strata, timestamps) stays host-visible and
  host-indexable; every payload column is ciphertext. Structure server-side, semantics
  core-side.
- **The query plan becomes the privacy compiler.** The scoped-context capsule's three bounds
  split exactly along this line: temporal + authority bounds evaluate HOST-SIDE on the
  plaintext skeleton (WHERE strata/status/window); the semantic bound evaluates only
  IN-CORE, after decryption. One query, two jurisdictions, and the compiler that translates
  a question into bounds is the same machinery that decides what the host is allowed to
  compute. Two capsules that didn't know about each other compose without a seam.
- **⚑ The falsifier: vectors are content, not structure.** Embedding inversion recovers
  text from vectors to a workable degree; server-side ANN means the host sees the GEOMETRY
  of the mind even with every payload encrypted. So "host sees only relationships" holds
  only if vectors are ciphertext at rest and the similarity index lives in-core (rebuilt at
  unseal — trivial at today's 27k rows, a real cost at 27M; that scaling threshold is a
  measurable design input, not a guess). Naming this now because the claim dies quietly
  without it.
- **Access patterns still leak rhythm.** Which blobs are fetched together, when, how often —
  traffic analysis sees the tempo of thought even when content is opaque. ORAM exists and
  is heavy; the honest position is to ACCEPT the leak and classify it: this makes the
  encrypted cloud store formally an ADAPTER in the constitution's own vocabulary — "adapters
  leak interactions, not the corpus" (NN-11's opt-in clause). An argument, not a decision:
  it reframes the parked NN-11 ruling from "exception to the bright line" to "instance of
  the existing opt-in category." The owner still rules; the ask just got sharper.
- **The skeleton must be chosen, not assumed.** Some "metadata" is content — titles, status
  strings, finding summaries. A column-by-column schema audit (skeleton | payload) is the
  concrete artifact a design note would pin; defaulting any ambiguous column to payload is
  the fail-closed direction.

```capsule
topic: the-distributed-ecosystem
date: 2026-07-28

decisions:
  - Frame adopted: panic→seal generalizes vault semantics to the individual (boot-sealed,
    ceremony-unsealed, zeroize-on-panic); the twin of recovery mode at the key layer.
  - Frame adopted: field-level envelope encryption — skeleton host-visible, payloads
    ciphertext; the query plan splits into host-side structural bounds and core-side
    semantic bounds.

parked:
  - decision: whether vectors are payload (ciphertext, in-core index) or skeleton
    default: payload — fail-closed; the in-core index is trivial at current scale
    re_entry: the store's row count approaches the rebuild-at-unseal pain threshold
      (measure it, then rule)
  - decision: the NN-11 reclassification (encrypted cloud store as an adapter surface)
    default: unchanged — corpus stays on owned storage
    re_entry: the same OWNER-ONLY ruling parked in capsule 4, now with the adapter
      argument attached

open_questions:
  - Panic taxonomy: which panics seal (integrity violations, constitution-anchor mismatch)
    vs merely restart (transient OS errors)? A seal that fires on every crash makes the
    unseal ceremony routine, and routine ceremonies stop being ceremonies (the recovery-mode
    lesson from tonight, exactly).
  - Who can unseal which body-class, and is unseal itself logged as a typed artifact?
  - Does the skeleton include the reference graph between artifacts (edges = relationships,
    the thing the host explicitly MAY see) — and is that acceptable when edge density
    itself is a self-map signature?

next_steps:
  - None wired; joins the capsule-4 queue behind the two owner rulings and green main.

references:
  - docs/brainstorms/the-distributed-ecosystem.md capsule 4 (the roaming role this
    completes: seal = what retirement/panic does to a body)
  - docs/brainstorms/scoped-context-queries.md (the three bounds that split into two
    jurisdictions)
  - ops/lifecycle recovery mode as exercised 2026-07-28 (the scheduler-layer twin)
  - HashiCorp Vault seal/unseal semantics; SQLCipher (the rejected whole-file alternative);
    embedding-inversion literature (the vector falsifier)
  - CLAUDE.md NN-11 adapter clause
```

## 2026-07-28T05:09Z (bg orchestrator session — owner refinement: the store lives in memory; the disk never sees plaintext)

### The seed

Owner, near-verbatim: *"or doesn't sqlite live in memory when in use? which means it can be
decrypted as part of unseal in memory; the disk copy is encrypted; writes immediately encrypt
and backup."*

### Orchestrator scrutiny (chat-side — one correction, then the architecture is right)

- **The premise needs one correction; the design survives it.** Stock SQLite is disk-paged,
  not memory-resident — pages fault into cache on demand, WAL/journal writes hit disk. But
  SQLite has NATIVE machinery for exactly the owner's scheme: `sqlite3_deserialize` loads a
  whole DB image from a buffer into `:memory:`, `serialize`/`VACUUM INTO` emits one back.
  So: unseal → decrypt blob → deserialize into memory → operate; the disk artifact is only
  ever ciphertext. The scheme is not a fight against SQLite; it is a supported mode.
- **"Writes immediately encrypt and backup" is WAL-shipping, and it unifies two needs.**
  Per-write full-image re-encryption is too heavy; the right shape is an encrypted
  append-log: each committed write emits one encrypted record to disk immediately
  (durability boundary = that record's fsync), full snapshots checkpoint periodically. The
  same encrypted log SHIPS as the cloud backup stream — point-in-time recovery and the
  capsule-4 "encrypted backups in the cloud" fall out of one mechanism.
- **Crash = seal, by physics.** If plaintext exists only in RAM, panic→seal stops being
  handler code and becomes a property of volatile memory: any death — panic, SIGKILL,
  battery — IS a seal event. Tonight's near-death would have been a clean seal. Boot can
  only enter through the unseal ceremony; there is no half-open state to recover from.
  Fail-closed by construction beats fail-closed by discipline (the structural-enforcement
  rule, applied to key material). Caveats that are part of the spec, not afterthoughts:
  mlock/encrypted swap (plaintext pages must never hit disk sideways) and hibernation
  images.
- **Durability is cheap HERE because the stores are views.** The launcher already rebuilds
  an empty cache from sources ("reconcile the corpus"); truth lives in the artifact chain +
  sensors, and sync jobs are re-runnable. A lost log tail is a re-sync, not a loss. The
  in-memory scheme's durability bar is low precisely because the system was already built
  with rebuildable stores — the materialized-view property, now load-bearing.
- **The NN-8 arithmetic grows an axis.** An in-memory corpus competes with model residency
  (~hundreds of MB at 27k rows today, real at millions). The scheduler's refusal logic —
  which learned the memory ceiling, and should learn the battery (tonight's finding) — now
  counts corpus residency too. One resource model, three axes.

```capsule
topic: the-distributed-ecosystem
date: 2026-07-28

decisions:
  - Frame adopted: stores decrypt at unseal into memory (sqlite deserialize path); disk
    holds ciphertext only; writes emit encrypted log records immediately, and the log IS
    the backup stream (WAL-shipping).
  - Crash=seal-by-physics accepted as the enforcement mode: no plaintext at rest, no
    half-open boot path.

parked:
  - decision: per-write log-record vs periodic-snapshot granularity per store (queue vs
    ledger vs vector store have different write tempos)
    default: undecided — a design note pins it per store
    re_entry: graduation of the ecosystem thread into dn-deployed-instances

open_questions:
  - mlock scope and encrypted-swap verification per body-class (macOS default-encrypts
    swap; a cloud Linux body must prove it).
  - Snapshot cadence vs unseal latency: the rebuild-at-unseal cost curve as the corpus
    grows (same measurable threshold as capsule 5's vector question — measure, then rule).

next_steps:
  - Joins the capsule-4/5 queue behind the owner rulings and green main.

references:
  - sqlite3_serialize/deserialize, VACUUM INTO (the native machinery)
  - ops/lifecycle/launcher.py "reconcile the corpus" (stores-as-rebuildable-views, already
    live)
  - docs/brainstorms/the-distributed-ecosystem.md capsules 4-5 (the architecture this
    completes)
  - CLAUDE.md NN-8 (the resource model gaining axes: memory, energy, residency)
```

## 2026-07-28T05:14Z (bg orchestrator session — owner seed: the physical overlay, and location as a trust modifier)

### The seed

Owner, near-verbatim, closing the night: *"we're going to need a new router — I just have the
cheapest possible one; a real infra upgrade. Is it possible for the network gateway to access
a VPC directly, so me being in my home network is more secure? Think of it as an extended
space, a network extension. And different wifis for guests, my partner and I, and admin
needs. This isn't for tracking — it's for me to access my network securely. This doesn't
mean we don't authenticate anymore — WE DO — but this is just another layer of trust; I can
still access from different wifis but with more limited access."*

### Orchestrator scrutiny (chat-side — connections offered, not decided)

- **Two mechanisms, one already half-built.** Site-to-Site IPsec (router ⇄ AWS VPN Gateway,
  subnets routed natively) vs Tailscale subnet routers at both ends (home box advertises LAN
  routes, a small VPC instance advertises the VPC CIDR — the existing overlay becomes the
  extension). The second makes capsule 4's overlay-boundary sentence literal infrastructure
  with hardware we mostly have.
- **SSID→VLAN trust tiers:** guests (internet-only, isolated) · household (LAN, no admin
  surfaces) · admin (the only VLAN routed into the overlay/VPC; the palace and vault live
  behind it).
- **The design rule the owner stated himself, kept verbatim as law: network location is a
  trust MODIFIER, never an authenticator.** VLAN decides reach; identity decides access;
  authentication happens everywhere regardless. The rendezvous-ratchet philosophy at the RF
  layer — the network is a filter, identity is the gate. Composition with tailnet ACLs:
  device identity carries the ACL tag, the VLAN bounds which surfaces are even routable, so
  "same person, guest wifi" degrades gracefully to the exhaust lane.

```capsule
topic: the-distributed-ecosystem
date: 2026-07-28

decisions:
  - Design rule adopted: location is a trust modifier, never an authenticator — reach by
    network tier, access by identity, authentication always.

parked:
  - decision: router hardware + which extension mechanism (IPsec site-to-site vs tailscale
    subnet routers)
    default: current router; overlay reaches AWS only device-by-device
    re_entry: owner buys the hardware; subnet-router lean recorded for that conversation

open_questions:
  - Does the admin VLAN's overlay route make the home LAN part of the node-injection
    boundary (capsule 4), and is that boundary then listed per-VLAN in the constitution's
    adapter terms?

next_steps:
  - None — hardware first; joins the ecosystem queue.

references:
  - docs/brainstorms/the-distributed-ecosystem.md capsule 4 (the overlay boundary this
    physicalizes)
  - AWS Site-to-Site VPN; Tailscale subnet routers (both-ends pattern)
```
