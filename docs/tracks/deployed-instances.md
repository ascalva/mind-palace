---
type: track
slug: deployed-instances
title: Deployed instances — the amnesiac clone and the one-way loop home
status: active
warrant: null
audit_refs: []
dod:
  - DI-1 structure-seed exporter + payload-freedom ratchet + the F4 value benchmark (home-side only; stops the program cheaply if seeded ≤ unseeded)
  - DI-2 instance identity in config — per-instance backup/letter namespaces before any second body boots (the F5 precondition)
  - DI-3 letters lane, home side — a₄ landing behind the handoff gate (gated on dn-authorship-distance-axis ratification)
  - DI-4 clone runtime image + plane split + clone Terraform (gated on owner decisions D1–D3, D5)
  - DI-5 first clone boot — exits the second-instance fence; owner-initiated ceremony
backlog_deskcheck: null
links:
  - docs/design-notes/dn-amnesiac-clones.md
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
(`dn-amnesiac-clones` first).

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
DI-3..5 land in ruling order, and the first clone boot is the demonstration — per the
deskcheck discipline, this track cannot be deskchecked while it merely *could* work.

## Relationship to other tracks

- **ops** — the clone's runtime is ops-shaped (residency, cost, liveness), and cloud spend
  is "measurement, not architecture"; ops owns the instruments this track will read.
- **inner-outer-core / workflow** — no overlap; the clone consumes the framework as shipped
  nature. The framework-vs-instance line (palace-instances) is exactly what DI-2 makes
  mechanical.
- **The cross-node protocol fence** — `dn-authorship-distance-axis` §15 parks cross-node
  work until a second instance exists; DI-5 is the fence's exit, so that work re-enters
  through this track's sequencing, never around it.

**Owed:** WORK, not a deskcheck. The design note is `draft`; the owner decisions D1–D5 are
presented in it and unruled. Nothing in this track is buildable past DI-1/DI-2 until they
are.
