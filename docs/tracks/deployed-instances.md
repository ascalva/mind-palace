---
type: track
slug: deployed-instances
title: Deployed instances — the amnesiac clone and the one-way loop home
status: active
warrant: null
audit_refs: []
dod:
  - DI-1 structure-seed exporter + payload-freedom ratchet + the F4 value benchmark (home-side only; stops the program cheaply if seeded ≤ unseeded)
  - DI-2 instance identity in config — per-instance backup/letter namespaces before any second body boots (the F5 precondition, issue #25)
  - DI-3 the key fabric — identity keys on the attestation primitive, per-clone letter-box mint, registry + placement-audit ratchet, and the ISOLATED cloud/terraform/keyfabric/ stack (dn-key-fabric)
  - DI-4 letters lane, home side — a₄ landing behind the handoff gate (gated on dn-authorship-distance-axis ratification)
  - DI-5 clone runtime image + plane split + clone Terraform, consuming keyfabric CMKs (gated on owner decisions D1–D3, D5)
  - DI-6 first clone boot — exits the second-instance fence; owner-initiated ceremony
  - DI-7 the shared embedder service (dn-embedder-service) — stateless text→vector as fleet infra; sealed-to-attested-enclave, control-queue + data-plane; public-material clean, private material gated on the Nitro-frontier ruling
backlog_deskcheck: null
links:
  - docs/design-notes/dn-amnesiac-clones.md
  - docs/design-notes/dn-key-fabric.md
  - docs/brainstorms/ouroboros-cloud-clones.md
  - docs/brainstorms/the-distributed-ecosystem.md
  - docs/brainstorms/palace-instances-as-nodes.md
  - docs/brainstorms/nodes-are-nodes-cross-node-protocols.md
---
# Track — Deployed instances (the amnesiac clone and the one-way loop home)

The identity card for the deployed-instances track. **Scope:** spawning mind-palace
instances beyond the laptop — seeded with Ouroboros's learned structure, never its corpus
payloads — and the one-way learning loop that brings what they learn home as attributed
testimony. Members are the artifacts declaring `track: deployed-instances`
(`dn-amnesiac-clones` and its substrate companion `dn-key-fabric` first — one proposal,
two notes).

**Why this track exists.** The distributed-ecosystem thread accumulated seven capsules of
design (speciation, panic-seal, WAL-shipping, the overlay law) with no track coordinate and
no design note claiming the territory. The owner's 2026-07-30 capsule
(`ouroboros-cloud-clones`) added the missing architecture — structure ships, knowledge
stays — and the owner explicitly asked for the design pass (the deployment park's stated
re-entry). This track owns that territory so its plans, findings, and rulings have one
home.

**The organizing thesis.** Intelligence is shipped, not knowledge: a clone inherits the
geometry of the parent's mind (the structure seed, at a priced disclosure tier) and none of
its contents; everything it learns flows home as signed, sealed letters it can never read
again; home overlays on demand and adopts only by re-authorship. The security argument is
one line — bound what a total compromise of the body yields to the disclosure tier of the
seed.

**Definition of done** (a deskcheck evaluates against the `dod` list): DI-1 proves the
value claim or stops the program; DI-2 makes a second body *nameable* before one exists;
DI-3 lays the key substrate (information flow as key placement, its own Terraform state);
DI-4..6 land in ruling order, and the first clone boot is the demonstration — per the
deskcheck discipline, this track cannot be deskchecked while it merely *could* work.

## Relationship to other tracks

- **ops** — the clone's runtime is ops-shaped (residency, cost, liveness), and cloud spend
  is "measurement, not architecture"; ops owns the instruments this track will read.
- **inner-outer-core / workflow** — no overlap; the clone consumes the framework as shipped
  nature. The framework-vs-instance line (palace-instances) is exactly what DI-2 makes
  mechanical.
- **The cross-node protocol fence** — `dn-authorship-distance-axis` §15 parks cross-node
  work until a second instance exists; DI-6 is the fence's exit, so that work re-enters
  through this track's sequencing, never around it.

**Owed:** WORK, not a deskcheck. Both notes are `draft`; the owner decisions D1–D6 are
presented in `dn-amnesiac-clones` and unruled (`dn-key-fabric` adds none of its own).
Nothing in this track is buildable past DI-1, DI-2, and DI-3's home side until they are —
and nothing flips ON without the owner's ceremonies.

## DI-2: instance identity

Built on `build/instance-identity` (issue #25). A configuration now says which individual it
is, and everything that individual holds is a name derived from that identity, so two instances
cannot write one history.

**Selection.** `MIND_PALACE_OVERLAY` names the one overlay a named instance reads, in place of
`config/ouroboros.toml` and `config/levers.toml`. Unset or empty, the configuration is the
default chain, `defaults ← levers.toml ← ouroboros.toml`, and that chain is Ouroboros.

**The `[instance]` section.** `cfg.instance.id` is `ouroboros` for the default chain. A named
overlay must declare `[instance] id`: a lowercase letter, then up to 31 lowercase letters, digits
or hyphens, so the id is one path segment and one dotted component, and two ids never name one
directory on a case-insensitive filesystem. `ouroboros` is reserved to the default chain, and
Ouroboros's overlay may restate its id and nothing else. The section holds no other key.

**The namespace map** (`InstanceConfig`, `namespaces_of` in `core/kernel/config/loader.py`):

| Namespace | Ouroboros | Named instance `<id>` |
|---|---|---|
| root of relative data paths | `<repo>` | `<repo>/instances/<id>` |
| data dir and stores | `<repo>/data/…` | `<root>/data/…` |
| ingestion spool (`cfg.interface.handoff_dir`) | `<repo>/data/handoff` | `<root>/data/handoff` |
| supervisor lock | `<repo>/data/supervisor.lock` | `<root>/data/supervisor.lock` |
| levers file | `<repo>/config/levers.toml` | `<root>/levers.toml` |
| Keychain items (attestation signing and owner keys, restic password, backup key pair) | `attestation-signing-key`, … | `<id>.attestation-signing-key`, … |
| launchd labels | `com.mind-palace.palace`, `com.mind-palace.tick` | `com.mind-palace.<id>.palace`, `com.mind-palace.<id>.tick` |
| restic repository | as its overlay names it | its overlay's, whose last path segment is `<id>` |

**The invariant.** For instances i ≠ j, Ouroboros among them, `shared(N(i), N(j))` is empty:
no path of one is equal to, inside, or around a path of the other, no Keychain item or label is
common, and neither restic repository lies at or inside the other's location. For named instances
it holds by construction (distinct ids give distinct roots, item prefixes and label segments, and
no derived name is Ouroboros's). `tests/property/test_instance_namespaces.py` checks it with
Hypothesis over generated ids through the real loader, and its controls break the derivation
twice, once by ignoring the id and once by handing a named instance Ouroboros's names (the hazard
of #25); the property fails on both.

**What a named instance is refused.** Loading refuses an overlay that declares no id, a malformed
id, or `ouroboros`; that sets a derived Keychain item name, even to its derived value; that moves
a data path out of its root (absolute, or through `..`); whose restic repository does not end in
its id; or that would share any namespace with Ouroboros, whose chain is read on this host for
that check alone. Naming Ouroboros's restic repository, or a location inside it, therefore
refuses outright. At run time, a self-modification loop pointed at another levers file refuses
(`ForeignLevers`), and three Ouroboros-only tools refuse under `MIND_PALACE_OVERLAY`: `mind-palace
stack`, `ops/backup/backup.sh` and `scripts/run_with_secrets.sh`, which hold Ouroboros's labels,
Keychain items, Vault token and staging dir.

**What Ouroboros sees.** Nothing changes. Its paths, item names, labels, levers file and
repository are the ones it had. `tests/unit/test_instance_identity.py` pins this on a fixture with
the live overlay's sections and keys (placeholder values), against values it recomputes from the
TOML, with a control showing the same overlay loaded as a named instance differs in every
namespace. Checked by hand once, on a copy of the live overlay, the new loader's Config equals the
old loader's field for field (the new `instance` field aside).

**Trade-offs chosen.**
- *Derived, not declared.* An overlay states no namespace, and stating one refuses rather than
  being overridden, because a value the loader replaces is a setting that looks applied and never
  took. A declared name could also collide with another instance's; a derived one cannot.
- *State under `instances/<id>/`.* Nested in `data/`, a named instance would ride Ouroboros's
  backup and fall to Ouroboros's `reset`; under the home directory it would have no stable place
  in a container. The root is gitignored and is one directory to mount or archive.
- *Every Keychain item, not only the attestation key.* With Ouroboros's restic password a named
  instance could read Ouroboros's backups, and with its owner key forge its gate decisions; the
  amnesiac-clones design asks for zero shared secret material. Sharing one now takes a deliberate
  act: placing the same value under both names.
- *The repository is checked, not rewritten.* What the overlay writes is what restic gets; the
  last-segment rule keeps two named instances apart, and the check against Ouroboros's
  repository catches a copied overlay. In a container that has no `ouroboros.toml` the second
  check has nothing to compare; there the derived password still keeps Ouroboros's repository
  closed, since restic neither opens it with another password nor initialises over it.
- *A derived levers file, not a refusal.* The brief allowed refusing self-modification until an
  instance declares a levers path. A declared path is outside the derivation, so the invariant
  could not cover it; derived, it is disjoint by construction and `[selfmod] enabled` stays the
  one switch.
- *Ouroboros's tools refuse instead of learning instances.* The stack, the backup job and the
  secrets wrapper name Ouroboros's services and items directly; a named instance's services
  belong with its container profile.

**Limits.** The supervisor lock is a `flock` in the instance's data dir: it excludes a second
supervisor of one instance on one host, not on two (a lease or the DI-3 registry would). A named
instance's sources still default to Ouroboros's: the vault root, the transcripts directory, the
dialogue lanes the heartbeat reads, and the exhaust lane it writes reports to. `[secrets]` points
at Ouroboros's Vault. The bridge's handoff dir in `config/stack.toml` is read outside the loader
by the edge; only the notices the core writes there follow the instance's root.

**What it gives the container profile.** One volume per instance, mounted at
`/app/instances/<id>`, carries all of its state; the overlay at `config/instances/<id>.toml`
and the id are its whole identity in the image; item names map one-to-one onto a container's
secrets; labels name its units. A sealed core with network none and a filtered edge then share
only the spool under that root.
