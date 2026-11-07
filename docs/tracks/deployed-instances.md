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
is, and everything that individual writes, reads as its own or runs as is a name derived from
that identity, so two instances can neither write one history nor read each other's corpus.

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
| exhaust lane | `~/.mind-palace/exhaust` | `<root>/exhaust`, movable only within the root |
| vault source | `~/.mind-palace/vault` (its overlay's) | declared, else `<root>/vault` and off |
| transcripts source | `~/.claude/projects/<repo path>` | declared, else `<root>/transcripts` and off |
| code agent | on, over the checkout | off unless its overlay turns it on |
| dialogue lanes | `openwebui`, `opencode` | none |
| secret names: the Keychain items (attestation signing and owner keys, restic password, backup key pair, Vault token) and the airlock's AWS profile | `attestation-signing-key`, … | `<id>.attestation-signing-key`, … |
| launchd labels | `com.mind-palace.palace`, `com.mind-palace.tick` | `com.mind-palace.<id>.palace`, `com.mind-palace.<id>.tick` |
| restic repository | as its overlay names it | its overlay's, whose last path segment is `<id>` |
| airlock S3 prefixes | as its overlay names them | as its overlay names them |
| Vault server | `[secrets] addr` | the one its overlay names; none if it names none |

**The invariant.** For instances i ≠ j, Ouroboros among them, `shared(N(i), N(j))` is empty:
no location one writes or reads (data paths, lock, levers, exhaust lane, sources) is equal to,
inside, or around a location of the other, each compared by its real path with every symlink on it
resolved; no Keychain item, label or dialogue lane is common; neither restic repository nor
airlock prefix lies at or inside the other's; and the Vault servers differ, each host read as the
resolver reads it (userinfo dropped, every IPv4 form `inet_aton` accepts, IPv6 and v4-mapped
addresses, one trailing dot), with every loopback or unspecified address and the localhost names
counting as one host. For named instances it holds by
construction: distinct ids give distinct roots, item prefixes and label segments, no derived name
is Ouroboros's, and an undeclared source points into the instance's own root. What an overlay
declares is checked at load against every instance declared on the host: Ouroboros and each other
overlay under `config/instances/`, each read only for its namespaces. Sources count like every
other location, so two named instances cannot read one corpus either: a source at, inside or
around another instance's location, read or written, refuses.
`tests/property/test_instance_namespaces.py` checks the invariant with Hypothesis over generated
ids through the real loader, the named instances declared side by side so that each load checks
the others, over pairs of named ids as well. Its controls break the derivation five ways and the
property fails on each: ignoring the id; handing a named instance Ouroboros's names (the #25
hazard); and letting an undeclared vault, exhaust lane or Vault server fall back to the committed
default, which is Ouroboros's. With the loader's refusal on, the last four refuse at load, and so
does the first between two named instances.

**What a named instance is refused.** Loading refuses an overlay that declares no id, a malformed
id, or `ouroboros`; that sets a derived Keychain item name, even to its derived value; that moves
a data path or its exhaust lane out of its root (absolute, `~`, or through `..`); that turns the
vault or transcripts agent on without naming its source, or `[secrets]` on without naming its
Vault; whose restic repository does not end in its id; or that would share anything with another
instance declared on the host, Ouroboros or another named one, whose configuration is read for
that check alone. A declared source at, inside or around a location of Ouroboros's, Ouroboros's
restic repository named outright or nested, Ouroboros's Vault in any spelling, two named
instances whose repositories nest or whose roots one links to the other, and two overlays that
declare one id therefore refuse outright. An overlay under `config/instances/` that could never
load (no readable TOML, no id) holds nothing and is left out of the check. At run time, a
self-modification loop pointed at another levers file refuses (`ForeignLevers`), and every tool
that names Ouroboros's own state outside the config refuses while `MIND_PALACE_OVERLAY` is set:
`mind-palace stack`, `palace tick`, `backup.sh`, `run_with_secrets.sh`, the Open WebUI bridge and
its responder, the two dialogue readers, `curate_local.py`, `handoff.py`, `verify_planes.py`,
`cockpit.sh`, the query battery, the storage census, the quantization bench, the plane and
float16 migrations, the eval report writers' `data/reports` default, and the three Vault scripts.

**What a named instance that declares nothing reads and writes.** It writes only under
`<repo>/instances/<id>/`: its data dir and stores, spool, lock, levers file, exhaust lane and the
empty places its vault and transcripts would be. It reads its own root, its overlay and the
committed defaults, and the framework it runs from: the code, the door scripts, the committed
public keys. Two reads cross outside, and neither carries data: at load, Ouroboros's overlay and
levers file and the other overlays under `config/instances/`, read only to refuse a collision,
with no value reaching the named instance's configuration; and the local inference servers its
runtime points at (the committed default is
Ollama on loopback), which keep no state. Its Keychain items, labels and repository are names until
the owner creates them, and it has no Vault.

**What Ouroboros sees.** Nothing changes. Its paths, sources, lanes, item names, labels, levers
file, exhaust lane, repository and Vault are the ones it had. `tests/unit/test_instance_identity.py`
pins this on a fixture with the live overlay's sections and keys (placeholder values), against
values it recomputes from the TOML, with a control showing the same overlay loaded as a named
instance differs in every namespace. Checked by hand on a copy of the live overlay, the new
loader's Config equals the old loader's field for field, the new `instance` field aside.

**Trade-offs chosen.**
- *Derived, not declared.* An overlay states no derived name, and stating one refuses rather than
  being overridden, because a value the loader replaces is a setting that looks applied and never
  took. A declared name could also collide with another instance's; a derived one cannot.
- *Sources are declared or off.* A source is read, not written, so a named instance may read a
  corpus anywhere but Ouroboros's; with nothing declared it reads none. Every location of
  Ouroboros's counts, not only its sources, so a vault path into Ouroboros's data dir refuses too.
- *State under `instances/<id>/`.* Nested in `data/`, a named instance would ride Ouroboros's
  backup and fall to Ouroboros's `reset`; under the home directory it would have no stable place
  in a container. The root is gitignored and is one directory to mount or archive.
- *Every secret name, not only the attestation key.* With Ouroboros's restic password a named
  instance could read Ouroboros's backups, with its owner key forge its gate decisions, with its
  Vault token reach its Vault; the amnesiac-clones design asks for zero shared secret material.
  The owner key is per instance too: sharing one key across instances means placing the same seed
  under both names, which is the owner's act.
- *A Vault of its own or none.* A prefix on Ouroboros's Vault would still reach Ouroboros's server,
  so the rule is a different server or no Vault secrets at all.
- *The repository is checked, not rewritten.* What the overlay writes is what restic gets; the
  last-segment rule keeps two named instances apart, and the check against Ouroboros's
  repository catches a copied overlay. In a container with no `ouroboros.toml` that check has
  nothing to compare; the derived password still keeps Ouroboros's repository closed, since restic
  neither opens it with another password nor initialises over it.
- *A derived levers file, not a refusal.* The brief allowed refusing self-modification until an
  instance declares a levers path. A declared path is outside the derivation, so the invariant
  could not cover it; derived, it is disjoint by construction and `[selfmod] enabled` stays the
  one switch.
- *Ouroboros's tools refuse instead of learning instances.* Each names Ouroboros's data dir,
  services, archive or Vault directly; a named instance's services belong with its container
  profile, and making one of these tools instance-aware later is a change to read the config.

**Limits.** The supervisor lock is a `flock` in the instance's data dir: it excludes a second
supervisor of one instance on one host, not on two (a lease or the DI-3 registry would). No
configuration can yet declare a named instance's dialogue lane, so it has none. The committed
attestation public keys are Ouroboros's: a named instance that signs with its own key and verifies
against them fails closed until its overlay names its own. The checks hold at load: a symlink
planted afterwards is outside their reach, and so is a name that DNS resolves to this machine,
since core resolves no names; such a name would reach Ouroboros's Vault without Ouroboros's
token, the named instance's token item being its own.

**What it gives the container profile.** One volume per instance, mounted at
`/app/instances/<id>`, carries all of its state; the overlay at `config/instances/<id>.toml`
and the id are its whole identity in the image, and with no `ouroboros.toml` in the image there is
no other instance's state to reach. Item names map one-to-one onto a container's secrets, labels
name its units, and its sources are only the volumes it declares. A sealed core with network none
and a filtered edge then share only the spool under that root.
