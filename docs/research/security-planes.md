---
type: research
id: rn-security-planes
status: draft
created: 2026-07-03
updated: 2026-07-04
links: []
supersedes: null
superseded_by: null
warrant: null
---

# Security Planes

**Status:** Draft for review. Parked items carry explicit re-entry conditions.
**Origin:** Train-of-thought `un-represent-ability.md` plus survey of type-driven security literature (same directory), refined in discussion.
**Placement:** `docs/research/` pending ratification; candidate for promotion to `docs/design-notes/`.

---

## 1. Thesis

"Make illegal states unrepresentable" is an established principle (type-driven design, parse-don't-validate). Its application here differs from the standard setting in one respect: the code author is a high-throughput builder agent whose output volume exceeds review capacity. Types substitute for review the same way provenance labels substitute for trusting ingested content.

No single instrument covers the system. The security posture is a composition of three planes:

| Plane | Instrument | Guarantee | Threat model |
|---|---|---|---|
| Code | Type system of the privileged path | Code cannot express an unauthorized operation | Threat B-adjacent: builder mistakes and malice in code |
| Data | Provenance labels, capability ceiling | Data cannot escalate influence regardless of content | Threat A: adversarial payloads in ingested material |
| Boundary | Object capabilities, attestation | Neither the type layer nor the label lattice is writable by the builder | Threat B: tampering with governing artifacts |

The planes do not overlap and do not substitute for one another:

- Types constrain what compiles. They are inert against a payload, which never needs to compile. A fully verified core will index an adversarial note as a well-formed `String`.
- Provenance constrains what data may affect. It is inert against a privileged code path that ignores labels.
- Capabilities constrain who may redefine the other two planes. A type guarantee is only as strong as the write boundary around the type definitions; a label lattice is only as strong as the write boundary around the lattice definition.

Falsification clause (field-guide style): the composition claim fails if a demonstrated attack crosses planes — e.g., a payload that alters compiled behavior without a code write, or a builder write that escalates data influence without touching the label lattice. Any such demonstration invalidates the plane separation and requires redesign, not patching.

## 2. The foundation file set

The load-bearing invariant is not "illegal states are unrepresentable." It is:

> **The builder's write capability never covers the files that define representability.**

This is a capability-system claim, enforced by the existing object-capability model, not by the type system it protects.

Membership criterion: a file belongs to the foundation set if modifying it changes what states are representable, what data may influence what, or what evidence of change exists. Candidate enumeration (to be verified against the repo before ratification):

- The Constitution and all assembled-prompt components (per H7: the fingerprint must cover the full assembled prompt, including templates and skill definitions — the known gap)
- Provenance label lattice definition and `DERIVED_STRATUM` type reservation
- Capability grant definitions and the alignment gate
- Type definitions of the privileged read/write path (Section 3)
- Attestation keys and signing configuration
- This file and its peers, once ratified

Enforcement is two-layer: capability (the builder is never granted a write handle to these paths) and attestation (any change to the set is signed and logged, making violations evident even if the first layer fails). H7's finding stands: tamper-evidence is post-facto; the capability layer is the preventive control.

## 3. The privileged-path language split

**Decision: parked, with a recorded default of Rust via PyO3 if the split is ever justified.**

The proposal: privileged reads and writes against the core stores route through a compiled, strongly typed subroutine rather than Python.

Argument for: affine types (the borrow checker) genuinely enforce single-use capabilities and non-aliased write handles at compile time. A builder agent writing against this path cannot express a double-spend of a write capability. Rust has the strongest combination of checker strength and training-data coverage; agents write it competently.

Argument against, recorded in full because it is the reason for parking: **every language boundary is a serialization boundary, and serialization is where type guarantees die.** Python calling a Rust subroutine does not receive Rust's types; it receives bytes. Each split adds an FFI surface where illegal states become representable again. The guarantee only holds if the privileged path's public surface is minimal and the types are re-validated (parsed, not trusted) on the Python side.

Rejected alternatives, recorded:

- **Nelua:** hobby-scale ecosystem. The selection criterion for agent-written code is maximum training data with the strongest checker; Nelua fails the first.
- **Haskell as privileged subroutine:** weaker FFI story than PyO3 for this stack; GC pauses irrelevant at this scale but the ecosystem argument favors Rust.
- **Coq/Agda/F\* verification of the core:** full verification is a career, not a track. Fails proportionality.
- **Koka/Frank effect typing:** restates in language what MirrorView/EffectView capability objects already enforce architecturally. Decoration, not constraint.

Re-entry conditions: (a) a Track L or Track G incident traceable to a privileged-path code error that the capability layer did not catch, or (b) Track G irreversible-effect ports, where compile-time enforcement of write-handle non-aliasing has proportionate value.

## 4. Lightweight formal treatment

Full verification fails the formalism-must-constrain test. The proportionate alternative: specify only the invariants that matter, in two complementary forms.

1. **Model level (TLA+ or Alloy):** model-check the design, not the code.
2. **Implementation level (Hypothesis):** property-based tests asserting the same invariants against the real stores.

Invariants worth this treatment:

| Invariant | Statement | Falsifying observation |
|---|---|---|
| Label monotonicity | Derived artifacts carry labels ≥ (in lattice order) the join of their sources; no operation lowers a label | Any artifact whose label is below the join of its provenance edges |
| Capability non-amplification | No sequence of grants yields a capability exceeding the grantor's | A held capability with no derivation chain from a root grant |
| Append-only | Attested stores admit no in-place mutation or deletion | A store state unreachable by appends from any prior attested state |

The correspondence between model and code is itself an assumption; divergence between a Hypothesis failure and a clean model check indicates the model is wrong, and is reportable, not embarrassing.

## 5. Encryption as capability hardening

**Decision: accepted in principle, one paragraph of scope, not a track.**

Threat model honestly stated: local, offline, single-user; FileVault already covers device theft. The adversary this layer adds coverage against is *a process on the same machine with filesystem read but no key* — which describes the builder agent. Store encryption with keys held only inside the privileged path converts corpus confidentiality into a capability question: repo access no longer implies corpus access. Defense in depth behind the path-capability layer, not a replacement for it.

Two caveats, recorded so the scope stays honest:

- **The index is the leak.** Any structure the librarian materializes for efficiency — inverted indexes, embeddings, cluster summaries — is a plaintext-adjacent projection. Embedding inversion recovers substantial content from vectors alone. Consequence: indexes live inside the same boundary as the key. Residual leakage through index structure is accepted; the goal is reduced exposure and source confidentiality, not searchable-encryption-grade guarantees, which would fight the performance model for little gain.
- **Encryption does not provide integrity.** Ciphertext can be corrupted by an adversary who cannot read it. Integrity is the attestation layer's job (content-addressing, Ed25519), already in place. At rest, use an AEAD mode so decryption itself fails on modification. Property statement: confidentiality from key-as-capability; integrity from authenticated decryption plus the attestation chain.

Implementation default when picked up: SQLCipher (or equivalent AEAD-wrapped storage) for SQLite; key custody in the privileged path (Section 3 strengthens this if the Rust split occurs). Re-entry condition: Track G ports that widen same-machine process exposure, or any multi-process deployment.

## 6. The librarian and the adjudicator

**One librarian, many desks.** The librarian is a role in the ingest-to-index pipeline, parameterized by stratum, not a component per stratum. Author-layer and dialogue-layer payloads arrive with different labels and indexing decisions may differ by label, but the machinery — parse at the boundary into narrow types, embed, index, propagate labels into every derived artifact — is one pipeline. Per-stratum librarians would duplicate the component most exposed to Threat A.

The librarian is where the type plane helps least and the data plane helps most: its job is intimate contact with untrusted payloads, all of which are well-typed strings. Its derived artifacts (indexes, embeddings, context packings) inherit source labels; the index is a derived stratum and is typed as one (slots into the reserved `DERIVED_STRATUM`).

**Indexing policy is a function of the label lattice:**

- External strata: index on ingest.
- Derived strata: index on promotion. Unverdicted self-generated material must not influence retrieval.

**The adjudicator is an owner-facing instrument, not a pipeline component.** It consumes the math spine's outputs (stability filter, clustering, curvature bridges, frustration enumeration), compresses them into an interpreted report, and interrupts the owner only when a decision is pending — the earned-interruptions pattern applied to Track L. Boundaries:

- Recommendations land in the verdict store's inbox as annotations. Promotion spends only owner verdicts. Adjudicator selection taking effect without a verdict would be optimization over the system's own outputs — self-modification, requiring the separate gate. The adjudicator is a clerk, not a proxy. (How an owner verdict is *authenticated* — an Ed25519 signature over the canonical payload, not a possession proof — is `design-notes/verdict-authority.md`; the append-only signed store is `core/stores/verdicts.py`.)
- The report itself is not corpus content. If a report is deliberately ingested (e.g., to make adjudication history queryable), it enters as a depth-2 derived stratum — derived content about derived content, provenance edges pointing at the artifacts it adjudicates — and waits for promotion like anything else.
- The adjudicator is the natural consumer of the stability filter (per the parked stability-adjudication note): artifacts failing perturbation stability are discarded before reaching the owner's queue. This directly attacks review fatigue, the primary failure mode of longitudinal harnesses.

## 7. Parked items and re-entry conditions (summary)

| Item | Status | Re-entry condition |
|---|---|---|
| Rust privileged-path split | Parked; default recorded | Privileged-path code incident, or Track G irreversible-effect ports |
| Store encryption (AEAD, key-as-capability) | Accepted in principle; not scheduled | Track G exposure widening, or multi-process deployment |
| TLA+/Alloy + Hypothesis on the three invariants | Recommended; unscheduled | Ratification of this note; natural fit alongside provenance migration validation |
| Foundation file set enumeration | Blocking ratification | Repo verification pass |
| Full assembled-prompt fingerprint | Known H7 gap; owned there | Per H7 follow-up |
