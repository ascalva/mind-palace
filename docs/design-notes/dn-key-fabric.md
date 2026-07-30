---
type: design-note
id: dn-key-fabric
track: deployed-instances
status: draft            # draft → ratified → superseded.  draft→ratified is an OWNER-ONLY hand edit.
created: 2026-07-29
updated: 2026-07-29
links:
  - docs/design-notes/dn-amnesiac-clones.md
  - docs/brainstorms/kms-threat-layering.md
  - docs/brainstorms/the-distributed-ecosystem.md
  - docs/brainstorms/aws-as-the-authorization-spine.md
  - docs/brainstorms/nodes-are-nodes-cross-node-protocols.md
  - docs/design-notes/attestation-layer.md
  - docs/design-notes/vault-runtime-auth.md
supersedes: null
superseded_by: null
warrant: null
---

# The key fabric — information flow as key placement

> Filed as `draft` by the orchestrator (fable pass, `claude-fable-5`), companion to
> `dn-amnesiac-clones` in the same proposal PR — one large proposal, two notes, one track.
> It answers the owner's 2026-07-30 question directly: *"this all relies on building out
> the kms/asymmetric key framework — is that already in the ecosystem design notes?"*
> Grounded answer: **no.** No design note claims this territory; what exists is the ruled
> oq-0057 substrate (KMS encryption context, `seal "awskms"`, admin/use split — scoped to
> one host), brainstorm-grade sketches, and built machinery that is entirely symmetric or
> single-host (§2.1). This note is that missing design. Two owner directives recorded
> 2026-07-30 are inputs, not open questions: the framework is required substrate for the
> ecosystem, and it lands as **its own isolated Terraform deployment** under
> `cloud/terraform/` (§4).
>
> **Scope discipline.** Design only. oq-0057 (`f52821e`) is consumed, never re-derived or
> re-opened; `dn-vault-runtime-auth` and `dn-attestation-layer` are consumed as the
> secrets- and signing-substrate they already design. Claims labeled `[ESTABLISHED]` /
> `[DERIVED]` / `[INFERENCE]`; code claims grounded at HEAD `174d06c` — re-verify before
> building. This note introduces **zero new owner decisions**: it is the substrate that
> realizes D1–D5 as presented in `dn-amnesiac-clones` §5.

## 0. Executive map

- **The organizing law: information flow is key placement.** Every one-way property the
  ecosystem claims (clone speaks home; home never speaks clone; AWS carries but never
  reads) is restated as a fact about *where private halves live* — auditable by
  enumeration, enforced by absence, never by policy. The dataflow diagram and the key
  inventory are the same document (§2.3).
- **Four key classes, two jurisdictions.** Identity (signing) and channel (letter-box)
  keys are *local* asymmetric cryptography — the spine never holds them. Data keys and
  their wrapping roots are *spine* (KMS) territory. **The spine wraps bodies, never
  letters**: KMS sits in the at-rest/unseal path only; the semantic channel is KMS-free by
  construction, so no cloud compulsion can open a letter (§2.2).
- **Per-relationship letter-box pairs, not one global key.** One home pair for all clones
  would make one home-side compromise read every stream, and rotation impossible without
  re-minting the fleet. Keys are cheap; blast radius is not (§2.2, §2.7).
- **Rotation is succession for deaf parties.** A clone cannot be told a new key — that
  deafness is the security feature — so re-keying a clone means minting its successor.
  Stated as a law, not discovered as a surprise (§2.7).
- **oq-0057 extends without reinterpretation**: per-individual CMKs, the encryption-context
  consequence-split applied *within* each individual, the admin/use role split applied
  *per* individual, brick = one `DisableKey` (§2.6).
- **Its own Terraform stack** (owner directive): `cloud/terraform/keyfabric/` — isolated
  state, isolated blast radius, peer to `bootstrap/`/`airlock/`/`backups/`. Unseal,
  minting, and destruction key material never rides along with fetcher or bucket changes
  (§4).

## 1. Purpose and scope

**What this note decides.** The key classes of the deployed-instances ecosystem and their
placement (which plane of which individual holds which half); the six laws that make
information flow provable from placement; the ceremonies (birth, unseal, retirement,
brick) and the named revocation act for every key; the public-key registry; how the ruled
oq-0057 mechanism extends from one host to N individuals; and the isolated Terraform stack
that carries the spine-side resources.

**Non-goals:**

- **Not the Ouroboros-role singleton or its succession/break-glass path** — the
  authorization-spine thread owns that, and it is explicitly harder than anything here
  (any path that can re-mint the singleton can mint a second Ouroboros). Nothing in this
  note touches the role lease. [ESTABLISHED: aws-as-the-authorization-spine ⚑]
- **Not HashiCorp Vault's interior.** `dn-vault-runtime-auth` designs per-interaction
  runtime authorization; the headless-bootstrap note owns the daemon's boot secret. This
  fabric *uses* Vault as home's core-plane secret store; it does not redesign it.
- **Not Nitro attestation** — parked in `dn-amnesiac-clones` behind D2-at-T2.
- **Not primitive selection.** Sealed-box construction (age / libsodium crypto_box_seal /
  HPKE RFC 9180) is a build-plan choice with a spike; the design constrains the *shape*
  (asymmetric sealed box, local, auditable), not the library. [INFERENCE — parked]
- **Not home-host secret handling.** Keychain/env remain the NN-10 seam at home; nothing
  moves out of the Keychain by this note.

## 2. The design

### 2.1 What exists at HEAD (the honest inventory)

| Mechanism | Kind | Scope today |
|---|---|---|
| restic repo password (`ops/backup/backup.sh:13,18`, Keychain) | symmetric | backups only; one secret, one repo |
| Backups CMK + SSE-KMS (`cloud/terraform/backups/kms.tf`) | KMS, symmetric | defense-in-depth under restic; one key |
| HashiCorp Vault (`ops/vault/`, `config/secrets_backend.py`) | secrets store | home host; unseal key in Keychain at HEAD (`vault-unseal.sh:31`); `seal "awskms"` is ruled (oq-0057) — verify migration state before building |
| Vault AWS engine (`cloud/terraform/airlock/vault_engine.tf`) | STS minting | short-TTL creds for the bridge role only |
| Attestation keys (`ops/attestation/*.pub`, flag-off) | Ed25519 signing | home-internal chain-of-custody (`dn-attestation-layer`, draft) |

**Absent**: any asymmetric *encryption* of content; any per-individual identity; any
channel construct; any registry; any per-key revocation act. [ESTABLISHED: grounding
survey at `174d06c`] The ecosystem's capsules assumed this layer; nothing designed it.

### 2.2 Four key classes, two jurisdictions

| Class | Primitive | Private half lives | Public half lives | Revocation act |
|---|---|---|---|---|
| **Identity** (per individual) | Ed25519 — `dn-attestation-layer`'s primitive extended to new principals, never a parallel scheme (DRY) | the individual's core plane, born in-body at first unseal, never transits | registry (§2.5): spine + home mirror | standing revoked at the registry — letters verify but no longer *count* |
| **Channel / letter-box** (per relationship-direction) | asymmetric sealed box (HPKE-class) | the *receiver's* core plane (home's Vault, for clone→home) | ships in the sender's seed manifest | receiver deletes the private half — the stream goes dark unreadably |
| **Data keys** (per store × consequence class) | symmetric envelope | in RAM at unseal, only ever wrapped at rest | n/a | flinch zeroizes RAM copies; brick disables the wrapping root |
| **Wrapping roots** (per individual) | KMS CMK, non-exportable | KMS (the spine) | n/a | `DisableKey` (reversible) / `ScheduleKeyDeletion` (terminal, 7–30d) [ESTABLISHED: AWS — verify API at build] |

Two jurisdictions, cleanly: identity and channel keys are **local** cryptography — the
spine never holds either half, so **no cloud actor can be compelled to open or forge a
letter**. Data keys and wrapping roots are **spine** territory — bodies at rest are
KMS-governed, which is exactly what makes brick a one-call act. The slogan the reviewer
should test every design change against: *the spine wraps bodies, never letters.*
[DERIVED: NN-1 forces this too — home core cannot call KMS (network), so letter decryption
could never be KMS-resident without moving plaintext to edge, violating NN-2. The clean
jurisdiction split is not taste; it is the only placement that types.]

**Per-relationship letter-box pairs.** Home mints one letter-box pair *per clone* (private
in home's Vault, public in that clone's seed). One global pair would mean: one compromise
reads every clone's stream, and rotation would require re-minting the entire fleet
simultaneously (§2.7). Per-pair cost is zero; the registry carries the mapping. [DERIVED]

### 2.3 The six laws

1. **Information flow is key placement.** X can send confidentially to Y iff X holds Y's
   letter-box public key; X can trust a message as Y's iff X holds Y's verification key.
   The ecosystem's dataflow topology is *audited by enumerating key placements* — a
   one-way property is proven by an absence, and the audit is mechanical (§3: the placement
   table ships as a checked artifact, not prose).
2. **Private halves never transit.** Born where they live, die where they live. Public
   halves ship in seeds and registries. No ceremony moves a private key — not birth, not
   succession, not brick recovery.
3. **The spine wraps bodies, never letters.** KMS appears only in the at-rest/unseal path.
   The semantic channel is KMS-free; the anchor authenticates and wraps, it never carries
   and never reads. [ESTABLISHED: extends "the anchor authenticates; it must never carry",
   nodes-are-nodes]
4. **Non-reciprocity is the default.** A new relationship receives exactly the placements
   its ruled dataflow requires — never a symmetric set for operational convenience. The
   clone's deafness (no verification key for home, no letter-box key of its own that home
   writes to) is the worked example, and every future relationship is designed by the same
   subtraction.
5. **Rotation is succession for deaf parties** (§2.7).
6. **Every key names its owner-plane and its revocation act at mint time** (the table
   above is the schema). A key without a named revocation act is unmintable — the fabric's
   analogue of "no park without re-entry."

### 2.4 Ceremonies

All owner-initiated; the model advises, code acts, Terraform and the `palace` CLI are the
hands (NN-3). Each ceremony is a script with a verifier, reversible where reversal is
meaningful.

- **Birth (minting an individual).** Owner runs the mint: the new body generates its
  identity pair in-body (private never leaves); its verification key registers at the
  spine registry and home's mirror; home mints the per-relationship letter-box pair,
  stores the private half in Vault, places the public half plus the embedder pin and
  disclosure tier into the seed manifest; the keyfabric stack (§4) provisions the
  individual's CMK and its use-role. The manifest is signed by home's *attestation* key so
  a body can verify its own seed — the one legitimate use of a home-held signing key in a
  clone's life, consumed once at birth, before the body is deaf. [DERIVED; the seed is
  verified at birth precisely because it can never be re-verified later]
- **Unseal (per body class).** Home: Keychain + owner presence, unchanged. Clone: the
  body's node identity authenticates to the spine; KMS unwraps the data keys at bootstrap,
  before `seal()` — never inside sealed core (the oq-0057 ⚑ pin). Attended vs unattended
  posture is D5, presented in the clones note; the fabric only fixes *where* the unwrap
  happens, not *who must be present*.
- **Retirement (planned death).** The fencing-token discipline: the body's spine
  credentials are destroyed at retirement so a zombie ex-body cannot act; its registry
  standing flips to retired (letters cease counting); its CMK is disabled after the last
  letter is acknowledged. Its history is already home — letters were its durability.
- **Brick (unplanned death, owner-side).** Two acts, distinguished because they answer
  different failures: `DisableKey` on the individual's CMK (**stop-reading** — at-rest
  remains locked but recoverable) and registry standing revocation (**stop-trusting** —
  no future letter counts, even signed ones, covering signing-key theft). The clone-side
  flinch (trip → zeroize) needs no spine participation — RAM is gone by physics.
  Post-mortem recovery re-enables the CMK under owner ceremony and replays the remains
  through the letters gate as testimony, never as a graft (`dn-amnesiac-clones` §2.5).

### 2.5 The registry

The spine holds the authoritative registry of (individual → verification key, standing,
CMK id, mailbox prefix); home holds a signed mirror. The anchor may *authenticate* — assert
who is speaking and revoke standing — and must never *carry* (no corpus, no letters
resident). A single anchor is a single point of trust failure; that cost was weighed and
accepted in the nodes-are-nodes thread, and the home mirror bounds it: losing AWS loses the
ability to *change* standings, not the knowledge of what they were. Substrate choice (S3
object + signature vs SSM vs DynamoDB) is a build-plan matter. [INFERENCE — parked]

### 2.6 oq-0057, extended without reinterpretation

The ruled mechanism generalizes by *indexing*, not by change:

- **Per-individual CMKs** (the clones note's D3 lean): each individual's wrapping root is
  its own key, so brick semantics are one API call and blast radius is one individual.
- **The encryption-context consequence-split applies within each individual** exactly as
  ruled at home: context = `{individual, plane, consequence}`; the decrypt path an agent
  can reach unattended is split from the one that pays out effector credentials.
- **The admin/use role split applies per individual**: a clone's instance role can *use*
  only its own CMK; *admin* on every CMK stays with the owner's SSO principal; root sits
  in the key policy and is never authenticated (finding-0232's recovery-hardening
  ordering still binds).
- Phase 2 (VPC endpoints / PrivateLink for KMS) inherits its deferral; the clone VPC may
  revisit it as a *clone-stack* concern, not a home concern. [INFERENCE]

### 2.7 Rotation is succession

A clone cannot receive a new key — it cannot authenticate the sender of one; that deafness
is the point (law 4). Consequences, stated so nobody discovers them angry:

- **Home letter-box private key compromised** (the fat target): per-relationship pairs
  bound the blast to one clone's stream; that clone's successor is minted with a fresh
  pair; the old private half is deleted (revocation act = the stream goes dark).
- **Clone signing key compromised**: registry standing revoked (stop-trusting); the clone
  is bricked; post-mortem letters after the compromise timestamp are quarantined as
  testimony-of-doubted-authorship — the a₄ record carries standing-at-receipt, so the
  quarantine is a query, not a migration. [DERIVED]
- **Identity keys do not rotate on schedule** — they rotate by succession, and succession
  is cheap *by design* (bodies are disposable, letters are durable). Scheduled rotation of
  long-lived home keys (attestation, Vault) stays under their own notes' regimes.

## 3. Consequences

- Licenses the fabric's home-side build ahead of anything cloud-shaped: extend the
  attestation layer's Ed25519 identity to the individual grain; the sealed-box library
  spike; letter-box mint + Vault storage; the registry schema + signed mirror; **the
  placement-audit artifact** — a checked table of every key, its plane, and its revocation
  act, enforced by a test (law 1 made mechanical; a new key without a row fails CI).
- Licenses the `cloud/terraform/keyfabric/` stack (§4) — which `dn-amnesiac-clones` DI-5
  then consumes for per-clone CMKs and mailbox IAM.
- Re-sequences nothing in the clones note; it slots as DI-3 in the track's definition of
  done, between instance identity and the letters lane.

## 4. Wiring & enablement

**How it wires:** (a) **`cloud/terraform/keyfabric/` — its own isolated deployment**
(owner directive 2026-07-30): separate backend/state and blast radius, peer to
`bootstrap/`, `airlock/`, `backups/`; owns per-individual CMKs + aliases, key policies
(admin/use split, encryption-context conditions), the registry substrate, and the
brick/retire IAM actions — so unseal/minting/destruction key material never rides a
fetcher or bucket change, and a `terraform plan` on this stack is *readable as a key-
lifecycle diff and nothing else*. (b) `ops/keys/` tooling: mint/retire/brick scripts with
verifiers (owner-run, NN-3). (c) `palace` CLI verbs (`mint-individual`, `retire`, `brick`)
that *drive* the scripts — advise-and-display, never holding AWS credentials themselves.
(d) A `[keys]` config section: registry location, placement-audit path. (e) The
placement-audit test in CI.

**What it takes to flip it on:** (a) the home-side build (§3) and the keyfabric stack
land; (b) the owner rules D1–D5 on the clones note (this note adds no decisions of its
own); (c) the owner runs `terraform apply` on `keyfabric/` and performs the first birth
ceremony. Until then the fabric exists as code, tests, and an empty registry — buildable,
auditable, and OFF.

## Parked decisions

| Parked | Default | Re-entry |
|---|---|---|
| Sealed-box primitive (age / libsodium / HPKE) | Undecided; shape constrained (§1) | The DI-3 build plan opens with the spike |
| Registry substrate (S3+sig / SSM / DynamoDB) | Undecided; schema constrained (§2.5) | Same build plan |
| KMS asymmetric CMKs anywhere in the letter path | **No** — the channel stays KMS-free (law 3) | Only an owner re-ruling of law 3 itself |
| Scheduled rotation for home's long-lived keys | Governed by their own notes (attestation, Vault) | Those notes' own regimes |
| Phase-2 VPC endpoints for KMS | Deferred (inherited from oq-0057) | The clone-stack build revisits as its own concern |

## Cross-references

- Companion: `docs/design-notes/dn-amnesiac-clones.md` (§2.4 consumes this fabric; D1–D5
  are the rulings this note realizes; same proposal PR).
- Ruled substrate: oq-0057 (`f52821e`) — encryption context, `seal "awskms"`, admin/use
  split; `docs/brainstorms/kms-threat-layering.md` (⚑ the KMS-decrypt-outside-sealed-core
  pin; the partition-not-stack frame; finding-0232 ordering).
- Threads: `the-distributed-ecosystem.md` (aligned secrets, panic-seal, fencing tokens,
  envelope encryption); `aws-as-the-authorization-spine.md` (spine authorizes the node,
  never the core; revocation asymmetry; singleton — out of scope here);
  `nodes-are-nodes-cross-node-protocols.md` (the anchor authenticates, never carries).
- Consumed notes: `dn-attestation-layer` (draft — the Ed25519 substrate this extends);
  `dn-vault-runtime-auth` (draft — home's core-plane secret store);
  `dn-headless-daemon-secret-bootstrap` (draft — the boot-secret seam, unchanged here).
- Code at `174d06c`: `ops/backup/backup.sh:13,18`; `ops/vault/vault-unseal.sh:31`;
  `cloud/terraform/backups/kms.tf`; `cloud/terraform/airlock/vault_engine.tf`;
  `ops/attestation/`; `config/secrets_backend.py`.
