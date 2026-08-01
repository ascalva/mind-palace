---
type: design-note
id: dn-amnesiac-clones
track: deployed-instances
status: draft            # draft → ratified → superseded.  draft→ratified is an OWNER-ONLY hand edit.
created: 2026-07-29
updated: 2026-07-31
links:
  - docs/design-notes/dn-key-fabric.md
  - docs/brainstorms/ouroboros-cloud-clones.md
  - docs/brainstorms/the-distributed-ecosystem.md
  - docs/brainstorms/palace-instances-as-nodes.md
  - docs/brainstorms/nodes-are-nodes-cross-node-protocols.md
  - docs/brainstorms/kms-threat-layering.md
  - docs/brainstorms/aws-as-the-authorization-spine.md
  - docs/design-notes/authorship-distance-axis.md
  - docs/design-notes/plane-principals.md
  - docs/design-notes/exhaust-lane.md
supersedes: null
superseded_by: null
warrant: null
---

# The amnesiac clone — intelligence ships, the corpus stays home

> Filed as `draft` by the orchestrator: a fable pass (`claude-fable-5`) over the owner's
> 2026-07-30 capsule (`docs/brainstorms/ouroboros-cloud-clones.md`, PR #24). Under the
> merge-gated regime (owner ruling 2026-07-28) the owner's merge of the PR carrying this
> note is the blessing; the status field is provenance description and is never edited by
> an agent. This note exercises the deployment park's stated re-entry condition — "the
> owner … explicitly asks" (the-distributed-ecosystem, capsule 1 park): the owner asked
> for this design on 2026-07-29.
>
> **Scope discipline.** Design reasoning only; nothing here is buildable until the owner
> decisions in §5 are ruled. Ratified/draft prior art is consumed, never edited:
> `dn-plane-principals` (ratified), `dn-capability-scope` (ratified),
> `dn-authorship-distance-axis` (draft, rules the cross-node provenance questions),
> the oq-0057 KMS ruling (committed `f52821e`). Claims are labeled
> `[ESTABLISHED: cite]` / `[DERIVED: from X]` / `[INFERENCE]`. Code claims were grounded
> against HEAD (`174d06c`) on 2026-07-29 — per the orientation rule, re-verify before
> building.

## 0. Executive map

- **The premise, corrected.** At HEAD, "restore the encrypted backup, get points and edges
  but no data" is false: restic ships the vault plus all of `data/`, and the stores carry
  payload text. Amnesia is not achieved by withholding a file; it must be *manufactured* as
  a typed export — the **structure seed** — whose payload-freedom is proven by a test, not
  asserted (§2.1–§2.2).
- **The clone is a new individual, not Ouroboros elsewhere.** It never holds the Ouroboros
  role; the singleton and role-lease machinery are untouched. What is new against the
  speciation frame: the clone's shipped *nature* is enlarged to include learned structure —
  acquired geometry becomes heritable (§2.3).
- **The key fabric is two keypairs, never one.** The seed's stated layout is the signing
  half (clone speaks home, authenticated). The intended one-way flow needs the complementary
  encryption half (clone holds home's public letter-box key; home keeps the private). The
  clone can write letters home it can never read again; it is structurally deaf to home
  (§2.4). Control (brick) rides the AWS spine, never a semantic channel (§2.5).
- **The one-way learning loop already has ruled machinery.** Letters land at home as
  attributed testimony (a₄) in an excluded-by-default clone stratum; the owner's
  "overlay only when it needs to, in its own words" is exactly scoped on-demand reads plus
  gated re-authorship — no new authority lane is invented (§2.7).
- **The security thesis in one line:** bound what a total compromise of the body yields to
  the disclosure tier of the seed. Tiers T0/T1/T2 make that bound explicit and priced;
  embedding inversion means T2 is never "no data" (§2.2, §6).
- **Six owner decisions are surfaced, none resolved** (§5). The sharpest is D2 — plaintext
  *structure* in rented RAM — which is the standing "vectors are payload, fail-closed" park
  being re-entered deliberately, with the leak quantified instead of assumed away; D6 (the
  first clone's mission) gives D2 its denominator.

## 1. Purpose and scope

**What this note decides.** The architecture by which a mind-palace instance can be spawned
on a cloud node seeded with Ouroboros's learned structure but none of its corpus payloads:
what ships (the structure seed and its disclosure tiers), what the clone is (identity,
constitution, planes, containers), how it lives and dies (unseal, trip, flinch, brick), and
the one-way learning loop home (letters, a₄ landing, lazy overlay). It integrates every
standing ruling the idea touches and names the owner decisions it cannot make.

**Non-goals** (load-bearing; the owner reads these explicitly at ratification):

- **Not the fleet study.** the-distributed-ecosystem's longitudinal
  stability-and-alignment program (same nature, varied nurture) is its own future note;
  this note designs one clone class, and the priority ruling "revive Ouroboros first;
  ecosystem design follows" is respected — nothing here jumps the build queue.
- **Not role mobility.** The clone never assumes the Ouroboros role. Role-under-lease,
  the singleton property, and break-glass succession stay exactly where the
  authorization-spine thread parked them.
- **Not the general cross-node protocol.** `dn-authorship-distance-axis` owns cross-node
  provenance; the standing fence — nothing cross-node buildable before a second instance
  exists — stands. This note is the path that mints the second instance; it does not
  pre-build the protocol.
- **Not corpus DR.** The restic backup lane (BUILD-SPEC §16b, live on Ouroboros) is
  consumed as-is and unchanged. The structure seed is a *sibling artifact*, not a backup
  replacement.
- **Not the constitution-scope question.** Whether `CONSTITUTION.md` is global,
  per-instance, or a kernel each instance narrows (⚑ palace-instances-as-nodes, the most
  consequential open question) is owner-only; §2.3 is written to be valid under any of its
  answers. [INFERENCE — scoping choice]
- **Not clone↔clone.** One clone, letters home only. A mesh is unnameable until a second
  clone exists and the owner asks. [INFERENCE — scoping choice]

## 2. The design

### 2.1 The premise, corrected against HEAD

The capsule's seed assumed the existing encrypted backups are already the clone seed
("points and edges remain, but no data"). Ground truth at `174d06c`:

- The live backup plan ships **two roots: the corpus vault and the whole `data/`
  directory** (`ops/backup/plan.py:139`), client-side encrypted by restic to
  `s3://mind-palace-backups-054942746160` daily at 03:30, SSE-KMS beneath
  (`config/ouroboros.toml:35-37`, `cloud/terraform/backups/kms.tf`). [ESTABLISHED: HEAD]
- Those roots carry payloads, not just structure: `vectors.lance` stores the chunk **text**
  beside each vector (`core/stores/vectorstore.py:43`); `chatlog.sqlite` is the
  utterance-grain transcript corpus; `data/raw/` is the content-addressed verbatim source
  of truth ("raw is sacred", `core/kernel/stores/rawstore.py`). [ESTABLISHED: HEAD]

So decrypting the backup decrypts the corpus. The backup is the **resurrection artifact**
(full restore, home only); the clone needs a different artifact with a provable property.
The amnesia is a *type*, not an omission. [DERIVED]

### 2.2 The structure seed

**Definition.** A derived, exportable bundle containing exactly: content-hash identifiers,
vectors (per tier, below), edges (reference, causal, authored-supersession), strata and
provenance labels, and timestamps. No text columns, no raw store, no transcript bodies, no
code bodies. It is generated home-side by an exporter that enumerates columns by
**allowlist** — never by subtracting known-bad columns — and it ships only ciphertext
(restic-style client-side encryption under a clone-scoped key, §2.4).

**The payload-freedom ratchet.** A property is only real when a test proves it: the export
schema is frozen in code, a test asserts the export contains no column outside the
allowlist, and a second check screens exported identifiers for human-readable content —
because a doc id like `janus_notes/<revealing-title>.md` *is* payload. Identifiers are
hash-blinded at export; the home-side exporter keeps the (hash → id) map private, which is
also exactly the join key the overlay needs later (§2.7). [DERIVED; enforcement per the
structural-enforcement rule]

**Disclosure tiers.** "No data" is not binary; the seed's tier is a priced dial the owner
sets (D2):

| Tier | Ships | What a total compromise of the clone yields |
|---|---|---|
| T0 | ids + edges + strata + timestamps | Graph shape and tempo: cluster structure, activity rhythms, corpus scale. No semantic content. |
| T1 | T0 + quantized and/or privately-rotated vectors | T0 plus approximate geometry; inversion degraded but the rotation secret is clone-resident, so a live-RAM compromise upgrades to ~T2. |
| T2 | T0 + full-precision vectors | The semantic geometry — and partial text: embedding inversion recovers much of short passages [ESTABLISHED: vec2text, Morris et al. 2023, "Text Embeddings Reveal (Almost) As Much As Text"]. |

The honest statement: tiers **bound** the leak; none zero it (§6, F2–F3). The amnesia
metaphor calibrated — T2 is less "lost the memories" than "lost the words but kept the
shape of every thought."

The frame is not exotic (owner seed 2026-07-30): **modern AI already ships this way** — a
trained model is structure distilled from a corpus that does not travel with it; the seed
is Ouroboros's weights. The analogy carries its caveat honestly: weights memorize at the
margins (training-data extraction) exactly as embeddings invert at the margins — the
field's answer is measured disclosure, and the tiers are ours.

**The store-level cut at HEAD** (owner framing, 2026-07-30: the seed is a *selective,
least-privilege choice per store* — vectors and relationships, never plaintext). The store
layout already draws most of that line; the exporter *projects* the mixed stores and
*excludes* the payload stores rather than filtering ad hoc. Classification at `174d06c` —
column-level contents marked ✓ are verified, ○ are [INFERENCE] pending the ratchet's
column audit at build:

| Class | Stores | Seed treatment |
|---|---|---|
| Structure (ships at tier, ids blinded) | `reference_edges.sqlite` ○ · `causal_edges.sqlite` ○ · `edges.sqlite` ○ · `versions.sqlite` ○ · `authored_supersessions.sqlite` ○ | Near-whole projection: endpoints, types, strata, timestamps. Any snippet/context column found is stripped by the allowlist. |
| Mixed (projected, never copied) | `vectors.lance` ✓ (vector beside a `text` column, `core/stores/vectorstore.py:43`) · `structural.duckdb` ○ | Vector + blinded id + stratum ship at T1/T2; `text`, `qualname`, path metadata never. |
| Payload (never ships) | `data/raw/` ✓ · `chatlog.sqlite` ✓ · `chat_events.sqlite` ○ · `derived.sqlite` ○ (dreams/curator text) · `code_observations.sqlite` ✓ · `code_snapshots.sqlite` ✓ · `staging.sqlite` ○ · `vault_catalog.sqlite` ○ (real paths) | Excluded as whole stores. Code is corpus (owner ruling 2026-07-21), so the code stores sit here, not in ops. |
| Operational (not corpus; clone births its own) | `queue` · `run_ledger` · `runs` · `dream_runs` · `telemetry.duckdb` · `eval_results.duckdb` · `attestations` · `verdicts`/`dispositions`/`claim_ops` · `selfmod_ledger` · `effects` · `observation_history` ○ · `agent_observations` ○ · `data/vault/raft` (HashiCorp, secrets) | Never in the seed — a clone starts these empty; shipping them would leak tempo (F3) for zero seed value. |

The pleasant structural fact: edges already live in edge-only stores and text in
text-bearing ones — the vector store is the one genuinely mixed surface, and it is exactly
where the projection (never a file copy) is mandatory. The export operates per-store by
this classification and per-column by the allowlist; both are enforced by the ratchet, and
`derived.sqlite` is the cautionary case — system-*authored*, still semantic content.

**The embedder pin.** The clone's usefulness rests on embedding *new* material into the
*inherited* coordinate system. Therefore the embedder identity, version, and quantization
are part of the shipped nature, pinned in the seed manifest; an embedder drift is a
coordinate-system fork and the clone must refuse to mix frames. [DERIVED — the seed's
"prepared semantic language" claim depends on this pin; unstated in the capsule]

### 2.3 What the clone is

**A new individual under the speciation frame, with one amendment.** the-distributed-
ecosystem established: deployed instances share versioned *nature* (constitution anchor
hash, framework release tag, drift instruments) and grow their own *nurture* in place; the
corpus never transits, so there is no "Ouroboros in the cloud." This note keeps all of that
and enlarges nature by one element: **the structure seed — acquired geometry made
heritable.** Speciation stays; the inheritance is richer. A clone is a new individual born
knowing the shape of the parent's mind and none of its contents. [DERIVED: capsule +
ecosystem capsule 1]

The owner's second-pass names settle the vocabulary as a triple, and the words compose
mathematically rather than compete: the **projection** is the act — π, Ouroboros
projecting itself (payloads forgotten, geometry kept); the **image** is what lands on the
other side — im(π), the individual, *"a mirror image of Ouroboros"*; the **seed** is the
artifact that carries it. "Projection" carries the asymmetries that "clone" hides
(directional, lossy, revocable by its source); "image" carries the rest: the constitution
calls the system a mirror onto the owner's mind, so the image is the mirror mirrored; in
the optical sense it is a *real* image — formed at a distance, where the rays actually
converge on a screen (the cloud body is the screen; memories formed at a distance); and a
mirror image is chiral — same structure, never superimposable on the original, which is
speciation's divergence-is-expected said in one word. The pun is load-bearing, not
accidental: the image ships *as* an image (the container image / AMI is nature made
executable, §2.6) — prose below says "container image" when it means the artifact and
"image" alone when it means the individual. One calibration stands over all three words:
a mirror shows everything, and this one reflects shape, never words — the amnesia frame
remains the honest fidelity claim. Anatomy travels with it: the harness (everything
surrounding the core — its skin, the safe extensions) ships as the same flesh around a
new instance of the mind. [owner seeds 2026-07-30]

**Identity and constitution.** The clone has its own name, its own instance overlay, its
own vault (initially empty), its own keys (aligned secrets: same constitution, zero shared
secret material). It inherits `CONSTITUTION.md` as its outermost frame via the anchor hash
in its nature — true under any answer to the ⚑ constitution-scope question, since every
candidate answer includes at least the kernel. Its per-instance posture (what its corpus
is, which lines bind hardest, its own NN-8 memory ceiling — a node property, not a
framework law) is declared in its overlay, per the palace-instances vocabulary.

**Planes port; the seal gets stronger.** Inside the clone the architecture is the same:
sealed core, networked edge, filesystem handoff between them. The enforcement mechanisms
are code and port directly (import firewall `ops/import_lint.py`, runtime socket seal
`core/sealing.py`, the worker-boundary scan). The Mac's uid-keyed pf rule needs a Linux
analogue — and containers offer a *stronger* one: run clone-core in a container with **no
network namespace at all** (`--network=none`, the sandbox image's own precedent,
`ops/sandbox/Containerfile`), edge in a separate networked container, handoff over a shared
volume. Zero egress becomes a property of the namespace topology, not a filter rule.
[DERIVED] The answer to the capsule's docker/podman question is therefore **yes, and for
three reasons in this order**: the plane split (netns isolation), reproducible nature (the
image pins the framework tag — nature made executable), and portability. Not primarily
"security hardening" — a container is not an enclave, and the hypervisor trust frontier
remains Nitro-attestation territory (parked). Local model serving stays inside the
core-side pod (the loopback carve-out becomes a shared pod netns). [INFERENCE — wiring
detail, verify at build]

### 2.4 The key fabric — two keypairs, never one

The capsule states one relationship ("AWS and Ouroboros proper have the public key, the
clone has the corresponding private key, not reciprocated"). Realizing the stated *intent*
— clone→home possible, home→clone impossible, a compromised clone teaches an attacker
nothing about home — requires two independent keypairs [DERIVED: the capsule's layout is
the signing half; confidentiality needs the complementary half]:

| Keypair | Private half lives | Public half lives | Purpose |
|---|---|---|---|
| Clone signing pair | clone core only (born at first unseal) | home + the spine | Letters are authentic; the spine can attribute and revoke. This is the pair the capsule described. |
| Home letter-box pair | home core plane only | ships with the clone | Letters are confidential: encrypted to home, unreadable by AWS, the clone's own edge — or the clone itself, a moment after writing. |

The key classes, their placement laws, ceremonies (birth, unseal, retirement, brick), the
registry, and the isolated `cloud/terraform/keyfabric/` stack are designed in the
companion note **`dn-key-fabric`** (same proposal PR) — including one refinement adopted
from it: the letter-box pair is **per relationship, not global** (one pair per clone, so a
home-side compromise or rotation touches one stream, not the fleet).

Non-reciprocity, precisely: the clone holds **no decryption key for anything of home's and
no verification key for home** — it cannot read home's material, and it cannot even
authenticate a message claiming to be from home, so it is structurally deaf: there is no
channel on which home (or an impersonator of home) can teach it. A total clone compromise
yields: the seed at its tier, the clone's own nurture, the clone's signing key (an
impersonation risk — home revokes the verification key at the spine), and home's *public*
letter-box key (public by definition). Nothing decrypts home. [DERIVED]

**At rest.** Clone data keys are clone-local, wrapped by a per-clone KMS key (D3); the
oq-0057 mechanism — encryption context splitting the decrypt path by consequence — applies
*within* the clone exactly as ruled at home. Sealed core cannot call KMS (NN-1: KMS is a
network call), so the unwrap happens at bootstrap before `seal()` or edge-side — the same
constraint kms-threat-layering pinned for home. [ESTABLISHED: oq-0057 + kms-threat-layering ⚑]

**Letters home.** Each committed projection write emits an encrypted log record —
WAL-shipping, exactly the ecosystem capsule-6 mechanism — signed by the projection,
encrypted to home's letter-box key, written by its core to the handoff dir, shipped by its
edge to a per-projection S3 mailbox prefix. The edge carries ciphertext it cannot read
(NN-2 clean). Grain resolves the parked capsule-6 question (re-entry was *at graduation*):
**per-committed-write records at store-event grain, batched into one letter per shipping
interval**; snapshots, if ever wanted, are home-side derivations, never a second shipping
mechanism. One property holds in every mode: **the projection has no secrets from home;
home has every secret from the projection.** NN-11 is untouched — it protects home's
corpus from leaving; the projection's nurture flowing home is the design's purpose, not a
leak. [DERIVED; resolves the ecosystem capsule-6 park]

**Letter tiers and the durability switch** (owner refinement 2026-07-30). Letter *content*
is a dial, symmetric to the seed's, named per projection at birth:

| Tier | Carries | Posture |
|---|---|---|
| L0 | Histograms of **vector membership** per graph cut along the projection's temporal direction — occupancy counts over the inherited structure's regions, per time slice | The study silhouette: home watches which parts of its own map are filling, and how fast — content-free, membership expressed in seed ids (natively the home-grown language) |
| L1 | Cross-relationships only: new edges touching inherited structure, plus the local endpoint vectors they need to mean anything | "A new relationship between the local corpus and the headless remote corpus, in the home-grown language" — the pinned embedder IS the shared language. Local-only substructure stays local. Owner's lean. |
| L2 | Full fidelity: every committed write, including the projection's own corpus payloads | Letters-as-durability mode only |

The tier couples to the **durability switch**: either the projection persists nothing
(structure lives in RAM only; then L2 letters are its durability — home cannot hold a
history it cannot read), or — the owner's optional switch — it writes its own corpus to
local disk as **ciphertext under its KMS-wrapped keys**, and steady-state traffic drops to
L1 or L0, with the projection's full knowledge recovered only post-mortem through the
brick-recovery ceremony. Plaintext never touches disk in any mode. And in every mode **the
projection updates only its own overlay stores — the inherited seed is immutable
substrate** (enforced by the same ratchet family as payload-freedom; new edges may
*reference* seed nodes, never rewrite them — the mirror of home's own overlay-not-ingest
posture toward the projection). [owner seeds 2026-07-30; the capsule's second section is
the warrant]

### 2.5 Trip, flinch, brick — the lifecycle

- **The egg (deployment form; owner seed 2026-07-31).** What lands on the remote disk is
  a sealed egg: a **ciphertext yolk** — the container image, instance config, birth
  manifest, and the seed + store ciphertext — wrapped around by the only plaintext part,
  its **shell: a small bootstrap shell script** (the pun is load-bearing). The yolk has
  two compartments by consequence class: code + config under the boot key only
  (unrecoverable after birth; home has the repo, nothing is lost), and the seed + stores
  dual-wrapped under boot key *and* recovery CMK (the post-mortem door stays open). Hatch
  sequence: the shell presents the birth credential, receives the boot key, decrypts the
  yolk into tmpfs — the creature runs from RAM — and execs; the palace then decrypts the
  shipped DBs in memory; the first letter flies. In every phase of the body's existence —
  before birth, during life, after death — its disk holds shell + ciphertext, nothing
  else: "plaintext never rests" completed from data to the entire body. Deliberately
  *not* native encrypted EBS/AMI: platform-transparent decryption is a **standing**
  capability tied to the instance profile — exactly what the one-shot rule kills; the
  egg's app-level unseal is strictly stronger [INFERENCE — verify at build]. The RAM cost
  of the resident decrypted image joins the NN-8 node-ceiling arithmetic. The shell's own
  integrity is F9 (§6).
- **Boot-sealed; unseal once, ever — the one-shot rule (owner seed 2026-07-31).** Every
  boot comes up sealed (panic-seal inheritance: plaintext only in RAM, mlock/no-swap in
  the spec, crash = seal by physics). On a remote body the unseal is **one-shot**: a
  birth-scoped **boot key** — unique, disjoint from the recovery CMK, oq-0057's
  consequence-split applied a third time (boot and recovery are different consequence
  classes) — unwraps the data keys at bootstrap, before `seal()`, never inside sealed
  core; then the capability self-destructs, both halves one-way: the wrapped blob is
  shredded body-side at unseal, and home's code disables the birth key on receipt of the
  **first letter** — *the birth cry closes the door* (observation-triggered, retractable,
  automatable per oq-0051; nothing flows back). Steady state holds no invocable unseal
  key anywhere; **every reboot is a death and succession is the only restart** — crash =
  seal-by-physics hardens into crash = brick-by-construction. What it buys: restart-class
  attacks (evil-maid, cold-boot-and-reharvest) become void, and the row-3
  unattended-key window shrinks from the image's lifetime to one birth moment. What it
  does not buy, honestly: live-RAM compromise is unchanged — D2's tier is still the
  bound. Updates and maintenance become successor mints; availability is deliberately
  brittle, toward dark. The birth window itself is F8 (§6). Effector credentials stay
  human-gated exactly as at home, unchanged.
- **Trip.** Illegal-state detectors, clone-local: an egress attempt from core, an
  attestation failure, a scope violation, tamper signals — the type-trips runtime-alarm
  frame applied to the body. Detectors are code in the clone's supervisor; the model
  advises, code trips (NN-3). [INFERENCE — detector inventory is build-plan work]
- **Flinch.** The trip's reflex: zeroize the in-RAM data keys and structure. The body is
  instantly inert ciphertext; disk was never plaintext. The flinch is cheap because the
  panic-seal design already made every death a seal event — and under the one-shot rule
  it is also **final from the body's side**: no re-unseal path exists, so self-seal is
  self-brick. This is the image's one un-retractable act, and it types under oq-0051 by
  **pre-declaration**: the trip inventory in the owner-blessed birth manifest *is* the
  authorization, granted before the body ever runs. The irreversibility is bounded to the
  live process alone — everything the image knows survives as ciphertext it can no longer
  read; knowledge stays recoverable, only continuity does not. [owner seed 2026-07-31]
- **Brick.** "It decides when to brick the projection" (owner seed 2026-07-30) — home
  holds brick authority, and the authority type-checks against the owner's own standing
  rule (oq-0051: retractable actions need no per-action permission): `DisableKey` is
  reversible [ESTABLISHED: AWS KMS; distinct from `ScheduleKeyDeletion`, 7–30-day
  destruction — verify exact API at build], so a *defined trip* observed home-side in the
  letter stream (divergence, standing anomaly, silence beyond the lease window) may
  auto-brick through deterministic code — the flinch at fleet scale, failing toward dark.
  The model advises the trip inventory; code executes it (NN-3). **Re-enabling and
  deletion remain owner-ceremony-only: the system may put a projection to sleep; only the
  owner wakes or destroys one.** The capsule's "AWS keeps the key but disables it" is
  exactly this. Post-mortem: the owner re-enables under ceremony, decrypts the remains,
  and the remains re-enter home **only through the letters gate** — parsed as a₄ testimony
  like any letter, never grafted raw (§2.7).
- **Revocation asymmetry, honestly.** The spine can stop actions; it cannot un-store data
  (the authorization-spine ⚑). This design's answer is to shrink what "stored" means: at
  rest the clone is ciphertext under a disableable key; in RAM it is structure at the
  chosen tier. **What revocation cannot un-store is bounded to the seed's disclosure tier
  plus ciphertext** — that bound is the design's whole security argument, and it is why D2
  is the decision that matters most.

### 2.6 Habitat

AWS VPC, joined to the home network over the Tailscale overlay (owner's stated posture;
subnet-router lean already recorded in the ecosystem park). Two integration facts:

- **The mailbox is an airlock.** The letters lane reuses the proven §16(a) shape — S3
  prefixes, least-privilege IAM per prefix, edge-side transfer, filesystem handoff to core —
  with roles reversed (clone writes, home fetches). No home listener; home-edge polls the
  mailbox; home-core never touches the network (NN-1 both sides). Transport via tailnet
  instead is parked (default: S3 mailbox — spine-governed, no new ingress surface).
- **The mailbox is a void, not a conversation** (owner seed 2026-07-30: "communicate to
  the void … read this only, we never interact with, we study"). The projection's IAM on
  its mailbox prefix is **put-only — no List, no Get, no Delete** — so it cannot observe
  whether, when, or by whom a letter is read; and there are no semantic acknowledgments in
  any mode. Even the one-bit "home is consuming" side channel is closed by IAM
  construction (`dn-key-fabric` §4 provisions it). Home's posture toward a live projection
  is a researcher's: read-only, at a distance, studying the accumulation.
- **Location is a trust modifier, never an authenticator** (owner law, ecosystem capsule
  7). Being inside the VPC or tailnet grants reach, never access: letters are accepted on
  signature, node standing at the spine, and the ±window of the rendezvous discipline if
  adopted — never on source address. [ESTABLISHED: capsule 7]

### 2.7 The learning loop — one-way, and lazy

**Clone → home.** Home-edge fetches mailbox objects and drops them in the handoff dir;
home-side code decrypts (letter-box private key lives in home's core plane), verifies the
clone signature, and lands the content as **attributed testimony (a₄) rows in an
excluded-by-default clone stratum with a mandatory attestation record** — precisely the
machinery `dn-authorship-distance-axis` §12/§14 already rules (one base class for all
foreign authors; node is a principal, not a stratum axis; foreign vocabulary never admitted
into Σ). Nothing new is invented here; the letters lane is that note's first real customer.
[ESTABLISHED: dn-authorship-distance-axis (draft) §12–§14]

**Overlay on demand.** The owner's refinement — "proper only needs to overlay the clone's
vectors/edges when it needs to, if it wants to understand it in its own words" — is the a₄
landing's read side: the clone stratum is excluded by default, so nothing changes in home's
reasoning until a scoped query names it explicitly. Overlay is a read posture per
consultation, not a standing ingest. The hash-blinded ids join back to home's real ids via
the exporter's private map, so home reads clone testimony *in its own coordinates* — the
literal mechanization of "in its own words." [DERIVED]

**Adoption is re-authorship.** If home wants to *keep* something a clone learned, it does
not import the clone's rows into its own strata — it re-derives: re-embed, re-ground,
re-author through the same gates any new content passes. Testimony is a frame change, not
a longer distance (§11's one-axis-per-author law); promotion across frames is deliberate
and gated. This answers the capsule's "learn new vectors (if new ones)" without any raw
graft path existing. [DERIVED: from §11/§13 two-axis law]

**Home → clone: nothing, structurally.** No key material exists to carry it (§2.4) and no
protocol defines it. A clone with a stale seed is not updated; a successor clone is minted
with a newer seed and the old body is retired through the normal lifecycle. Seed refresh =
re-speciation. One-way purity is never traded for freshness. [DERIVED]

**Local clocks.** Memories form at a distance: each individual runs its own temporal
spine, and the ecosystem has no global clock (owner seed 2026-07-30; kinship: the G3
park's per-individual-clock direction and the ecosystem thread's meshing events). A letter
carries its **formed-at** time on the projection's clock; the a₄ attestation record adds
**received-at** on home's clock — two coordinates, never conflated, and letters are the
only meshing events the ecosystem has. Ordering across individuals is partial by design;
any analysis wanting a total order must construct it explicitly and say so. [DERIVED]

### 2.8 Non-negotiable readings

| NN | Reading under this design |
|---|---|
| NN-1 sealed core, zero egress | Preserved per-node; *stronger* on the clone (core in a no-netns container vs a pf filter rule). KMS unwrap stays outside sealed core (bootstrap/edge), per the kms-threat-layering pin. |
| NN-2 network ∥ private data | Preserved: clone-edge ships ciphertext it cannot read; home-edge fetches ciphertext it cannot read; only cores see plaintext, and only their own. |
| NN-6 constitution inheritance | The anchor hash is part of shipped nature; every clone agent nests inside it. |
| NN-8 memory ceiling | A node property (palace-instances): the clone declares its own ceiling; in-RAM structure residency is counted by its scheduler alongside models (ecosystem capsule 6). |
| NN-10 secrets outside code | Per-clone: KMS-wrapped data keys + instance-role credentials; no Keychain exists on Linux — the compliant seam is the cloud analogue (KMS + instance metadata), named explicitly for the reviewer. [INFERENCE — D-adjacent, see D5] |
| NN-11 corpus never transits | The corpus payloads never leave home under any tier — that line is untouched. What *does* ship is corpus-derived structure, and pretending that is "not the corpus" would be dishonest at T2: the tiers exist so the owner rules on a quantified disclosure, not a euphemism. D1/D2. |

## 3. Consequences

If the owner merges this note, it licenses graduation into build plans in this order —
sequencing chosen so the falsifiable, zero-boundary-risk work runs first and every
boundary-touching step waits for its ruling:

1. **The structure seed exporter + payload-freedom ratchet** (home-side only; no cloud, no
   NN-11 exposure; the export artifact never leaves the laptop until D1/D2 are ruled).
   This plan also carries the **value falsifier F4**, criteria pinned here so no builder
   invents eval design: a paired A/B — two fresh instances, identical framework and
   embedder pin, one seeded at tier, one blank, ingesting the *same* held-out corpus never
   seen by home; a pre-registered primary metric (organization/retrieval quality on the
   new corpus) with a stated margin; seeded must beat blank on the primary with no
   regression on secondaries; and the run executes on clone-class hardware so F6 (embedder
   feasibility + cost reading) rides along. If seeded ≤ blank, the program stops here,
   cheaply. Metric implementation and the corpus choice are plan-level; the shape above is
   design and is not a builder's to change.
2. **Instance identity in config** — the precondition discovery (§6 F5, issue #25): an
   `instance` identity with per-instance backup/letter namespaces must exist before any
   second body boots anywhere, cloud or not.
3. **The key fabric, home side + its isolated Terraform stack** (`dn-key-fabric`, same
   proposal): identity keys on the attestation primitive, per-clone letter-box mint, the
   registry, the placement-audit ratchet, `cloud/terraform/keyfabric/` — the substrate
   everything cloud-shaped consumes.
4. **The letters lane, home side** (a₄ landing behind the handoff gate) — gated on
   `dn-authorship-distance-axis` ratification.
5. **Clone runtime image + plane split** (the containers) and **clone Terraform**
   (VPC, mailbox prefixes, per-clone CMKs consumed from the keyfabric stack, IAM) —
   gated on D1–D3, D5.
6. **First clone boot** — exits the second-instance fence; the cross-node protocol work
   that fence parks becomes falsifiable for the first time.

The "revive Ouroboros first" priority ruling stands: these plans mint `proposed` and enter
the queue like any others.

## 4. Wiring & enablement

**How it wires:** (a) config schema — an `[instance]` section (instance id, embedder pin,
disclosure tier, mailbox/namespace prefixes) surfaced through `get_config()`; (b) a
`palace seed-export` CLI (home) and the exporter module + ratchet tests; (c) the letters
job kinds in the scheduler (clone: emit/ship; home: fetch/land); (d) `cloud/terraform/clone/`
(VPC, per-clone KMS key, mailbox prefixes, IAM); (e) the clone image build
(daemon + core/edge containers) and its systemd/launchd-equivalent units. The ON switch is
part of the deliverable, not a later step.

**What it takes to flip it on:** (a) builds 1–4 above land; (b) the owner rules D1–D6;
(c) the owner runs `terraform apply` for the clone stack, runs
`palace seed-export --tier <T>` at home, and boots the clone body with the seed URI —
owner-initiated, like every unseal ceremony. Until (b), nothing in this note is runnable
by design.

## 5. OWNER DECISION items (surfaced, not resolved)

- **D1 — Ciphertext-at-rest in S3, reaffirmed for two new objects.** BUILD-SPEC §16(b) and
  Zone C already sanction encrypted backups ("never receives plaintext private data"), and
  the owner enabled them. D1 asks: does that standing sanction extend to (i) the structure
  seed object and (ii) clone letter objects — both client-side-encrypted, both under KMS?
  The ecosystem thread's ⚑ letter-vs-spirit park (NN-11, owner-only re-entry) is the same
  question at constitution altitude; this note narrows it to two named objects.
  (Rec: extend — both are strictly less disclosive than the sanctioned backup.)
- **D2 — Plaintext structure in rented RAM, at which tier.** The standing "vectors are
  payload, fail-closed" park re-entered deliberately. Options: refuse (clone waits for
  enclave-only execution); permit T0/T1; permit T2 under Nitro attestation; permit T2
  plain. §2.2's table is the price list; F2/F3 are the honest leak statement.
  (Rec: T0/T1 to start — prove F4's value claim at low tier before buying T2's exposure.)
- **D3 — Brick mechanics.** Per-clone KMS CMK (clean DisableKey semantics, larger key
  inventory) vs one CMK with per-clone encryption context (oq-0057-coherent, brick via key
  policy edit). (Rec: per-clone CMK; brick should be one API call, not a policy diff.)
- **D4 — Is chat/dialogue structure in the seed?** The transcript corpus is the most
  intimate stratum; even its topology and tempo (T0!) may be worth excluding from the seed
  entirely. A per-stratum include mask in the export manifest costs nothing to build and
  leaves this a pure owner taste call at export time. (Rec: build the mask; default
  chat-structure OFF.)
- **D5 — birth presence, under the one-shot default.** Mostly dissolved by the owner's
  one-shot-unseal rule (2026-07-31, §2.5): the unseal capability self-destructs after its
  single use, so "a key invocable without a human" — the row-3 hole — exists for one boot
  moment, not a lifetime, and every reboot is a death. What remains to rule: (a) is the
  owner present at each birth (rec: yes — birth is already a ceremony), and (b) is
  one-shot mandatory for every remote mission, or a per-mission line in the D6 manifest
  (rec: default ON; any override recorded in the manifest with its reason). Effector
  credentials stay human-gated as at home, unchanged.
- **D6 — The first clone's mission.** These notes design what a clone *is*; only the owner
  says what the first one is *for* (a field scout over a named public corpus; a continuity
  seed; something else). D2 has no denominator until this is named — the tier worth paying
  depends on the job — and DI-5 cannot pin the clone's functional interior (its job table,
  sensors, ingest roots) without it. The mission also names, at birth: the letter tier
  (L0/L1/L2, §2.4) and the durability switch — the owner's recorded lean is minimal
  traffic (L1, or L0 for a pure study) with the disk switch ON. Not an architecture
  decision: a sentence or two at ruling time suffices. (Rec: rule D6 before D2.)

## Parked decisions

| Parked | Default | Re-entry |
|---|---|---|
| Clone↔clone protocols | None; letters home only | A second clone is minted AND the owner asks |
| Nitro Enclaves for clone core | Not required at T0/T1 | D2 ruled at T2, or the hypervisor trust frontier is revisited |
| Seed refresh | Never — mint a successor clone | A live clone proves F4 value and staleness is measured, not assumed |
| Access-pattern leakage (ORAM) | Accept and classify as an adapter property (ecosystem capsule 5) | The adapter classification is challenged at D1 |
| Letters transport | S3 mailbox (airlock shape) | A latency-sensitive use appears that polling cannot serve |
| Rendezvous ratchet on the letters lane | Not adopted (tailnet + signatures suffice) | A second instance exists and relationship-integrity tripwires are wanted (its own park's condition) |
| Private rotation at T1 | Quantization only; rotation optional | The exporter build plan prices it; honest limit (§2.2) stands either way |

## 6. Honest edges / falsifiers

- **F1 — id leakage.** Payload-freedom by column allowlist can pass while identifiers leak
  meaning (paths, titles, slugs). The ratchet must include the id-blinding check, and the
  blind map must be proven absent from the export. A reviewer should try to defeat the
  exporter with a crafted vault filename.
- **F2 — embedding inversion.** T2 vectors partially reconstruct text
  [ESTABLISHED: vec2text]. Any claim that T2 is "no data" is false; D2 is asked with eyes
  open, and the book chapter (if ever) says "lost the words, kept the shape."
- **F3 — structure fingerprints.** Even T0 leaks: co-reference topology, cluster sizes,
  and timestamps fingerprint the corpus's domains and the owner's tempo of thought. The
  tiers bound the leak; information-theoretically nothing zeroes it short of not shipping.
- **F4 — the value claim is untested.** "Inherited structure gives a prepared semantic
  language" is the load-bearing *usefulness* premise and it has never been measured. Build
  1 defines the benchmark before the code; if seeded ≤ unseeded, stop the program.
- **F5 — the accidental second Ouroboros (real at HEAD, issue #25).** Config has no
  instance identity (the only handle is the gitignored overlay filename,
  `core/kernel/config/loader.py:30-33`), the supervisor lock is host-local
  (`data/supervisor.lock`), and the restic repository is named in the overlay — so a copied
  repo + overlay booted on a second machine today *is* Ouroboros to every system it
  touches, including writing snapshots into the **same** backup repository. Instance
  identity (Consequences item 2) must precede any second body, independent of everything
  else in this note.
- **F6 — the embedder is a dependency of the whole idea.** If the pinned embedder cannot
  run on the clone's hardware (or its cloud cost is unacceptable — measurement, not
  architecture), the clone cannot extend the inherited space and the seed decays to a
  static map. The build-1 benchmark must run on clone-class hardware.
- **F7 — L0's value and privacy claims are both untested.** Whether membership histograms
  alone carry study value is as unmeasured as F4 — and aggregates are not automatically
  private: repeated occupancy counts over a growing graph can reveal join structure and
  event timing. If L0 becomes a load-bearing mode, both directions get the F4 treatment —
  a defined benefit metric and a defined leakage bound — before anyone calls it "just a
  histogram."
- **F8 — the birth window.** "Deleted immediately after" is exactly-once *approximated*:
  between the unseal and home's receipt of the first letter, the birth credential is live
  and the door is open. The window is minutes and bounded (short-TTL birth credential;
  home-side timeout: no first letter within T → auto-disable and investigate), but it is
  not zero. A reviewer should attack it directly: boot the body, suppress its first
  letter, and see how long the door can be held open.
- **F9 — the shell is the residual plaintext trust root.** The classic bootstrap problem,
  relocated but not removed: a tampered shell can exfiltrate the boot key it receives.
  Two bounds hold it: the one-shot rule collapses the shell's entire threat life to the
  pre-birth window (after the single hatch no key ever arrives again — tampering a spent
  shell is worthless), and if that window itself must close, platform measured boot
  (NitroTPM-class attestation of the boot chain, gating the birth credential) is the
  escalation [INFERENCE — verify platform support at build]. The reviewer's attack:
  swap the shell between egg placement and birth. Keep the shell tiny, hash-pinned in the
  birth manifest, and boring.

## Cross-references

- Capsule: `docs/brainstorms/ouroboros-cloud-clones.md` (PR #24) — the seed + overlay addendum.
- Thread: `docs/brainstorms/the-distributed-ecosystem.md` (capsules 1–7: speciation, panic-seal,
  skeleton/payload, WAL-shipping, trust dichotomy, overlay law); `palace-instances-as-nodes.md`
  (per-instance NN parameterization, ⚑ constitution scope); `nodes-are-nodes-cross-node-protocols.md`
  (a₄, two-axis law, the fence); `kms-threat-layering.md` (oq-0057 ruled substrate, ⚑ NN-1/KMS
  pin); `aws-as-the-authorization-spine.md` (spine authorizes the node, revocation asymmetry);
  `type-trips-runtime-invariant-alarms.md` (trip/flinch prior art).
- Companion: `dn-key-fabric` (same proposal PR) — the key classes, placement laws,
  ceremonies, registry, and the isolated `cloud/terraform/keyfabric/` stack that §2.4 and
  §2.5 consume.
- Rulings and notes: oq-0057 (`f52821e`); `dn-authorship-distance-axis` (draft — §11 one axis
  per author, §12 a₄, §13 two-axis law, §14 node-as-principal); `dn-plane-principals`
  (ratified — planes, pf rule); `dn-exhaust-lane` (ratified — lane isolation precedent);
  `dn-capability-scope` (ratified — the lattice the clone stratum scopes against).
- Code at `174d06c`: `ops/backup/plan.py:139`; `core/stores/vectorstore.py:37-61`;
  `core/kernel/stores/rawstore.py:17-40`; `ops/import_lint.py:43-61`; `core/sealing.py`;
  `ops/network/ouroboros-egress.pf.conf:37-38`; `ops/sandbox/Containerfile`;
  `core/kernel/config/loader.py:30-33,260-282`; `cloud/terraform/backups/*`,
  `cloud/terraform/airlock/*`.
- External: Morris et al. 2023, "Text Embeddings Reveal (Almost) As Much As Text"
  (vec2text) — the embedding-inversion bound behind F2/T2.
