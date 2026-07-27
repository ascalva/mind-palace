---
type: design-note
id: dn-authorship-distance-axis
status: draft
implementation: design-only   # nothing built; authored post-dates the 2026-07 corpus audit
created: 2026-07-09
updated: 2026-07-27
links:
  - docs/brainstorms/nodes-are-nodes-cross-node-protocols.md   # THE §11–§15 WARRANT — owner verbatim: four authors; authorship ⊥ trust; scoping
  - docs/brainstorms/palace-instances-as-nodes.md              # containment ("the knowledge graph is contained to its own node"); framework vs instance
  - docs/brainstorms/aws-as-the-authorization-spine.md         # role→node binding; the spine authorizes the NODE, never the core
  - docs/design-notes/capability-scope-algebra.md              # RATIFIED — (Σ,E,T,A); §14 grounds against it and core/kernel/scope.py
  - docs/design-notes/chat-sensor.md                           # RATIFIED + A1/A2 — the conversational-scale instance; the 139-row worked example
  - docs/design-notes/erratum-relation.md                      # RATIFIED — E1; the first frame-discriminating consumer (§11); PD-11's seam
  - docs/design-notes/agentic-loop.md                          # RATIFIED — G-C routes the self-authored class + w(a_self) to THIS note's gate
  - docs/design-notes/observed-stratum-spike.md
  - docs/design-notes/observed-data-and-the-assistant-tier.md
  - docs/design-notes/observed-iot-and-cross-source-synthesis.md
  - docs/design-notes/the-sacred-boundary.md
  - docs/design-notes/the-edge-model.md
  - docs/design-notes/recursive-strata.md
  - docs/design-notes/ingest-identity-and-amendment.md
  - docs/design-notes/supersession-lifecycle.md
  - docs/design-notes/live-adoption-and-longitudinal-harness.md
  - docs/design-notes/skills-and-scope.md
  - docs/design-notes/attestation-layer.md
supersedes: null        # intended: dn-observed-stratum-spike — lands at ratification (§8)
superseded_by: null
warrant: null           # requires a new warrant finding at ratification (§8)
---

# Design note — The Authorship Axis: every stratum is self-data, at a distance

*Family tag → family 1 (labelings & flow) primary: a graded authorship coordinate factored
out of ρ, with a monotone footprint map on derived nodes. Family 2 (regenerable derivation):
graded grounding extends the confidence envelope. Family 5 consumes both. See
[`../NOTATION.md`](../NOTATION.md).*

**Status:** DRAFT — **ratifiable intent.** This note answers the central question the
observed-stratum spike declared unanswerable within its own frame (OQ-3), and proposes to
supersede that spike and partially amend the two firewall notes. Per house discipline
(`supersession-lifecycle.md`; the spike's own §3), the `supersedes`/`warrant` front-matter
lands only on owner ratification. Until then the firewall notes remain authoritative
wherever this note conflicts with them.

**Origin:** Design dialogue, 2026-07-09. **Revised 2026-07-27** (fable pass, `claude-fable-5`)
from the node/instance dialogue captured in the linked capsules: §§11–15 integrate the frame
extension (one axis per author), the fifth class (attributed testimony), the authorship⊥trust
law, and the node/scope ruling. §1's dialogue-counterparty edge case is resolved (§11); §9 B-4
is answered at source. The 2026-07-09 core (§§0–10) stands; where the revision sharpens it,
the sharpening is marked in place.

**Boundary:** Inbound — ingestion; and read-scope declarations. Governed by
`the-sacred-boundary.md` §2 (typed-and-promotion-gated; un-purchasable by EV).

**Ordering:** Downstream of Track L, same as the spike. Nothing here licenses building
ahead of provenance migration `--apply` and self-knowledge ingest. What it *does* license
immediately: the schema-coupling check in §7 and the ratification decision in §8.

---

## 0. The reframe

The firewall doctrine models the system as holding two kinds of material: the owner's
authored corpus (the mirror's food) and everything else (quarantined or excluded). The
reframe: **there is only one subject.** Every stratum in the system is self-data — the
difference between strata is not *whose data it is* but **how much mediation sits between
the owner and the artifact**.

- A verdict is the owner, first-order.
- A biometric aggregate is the owner as read by an instrument.
- A curated book chapter is someone else's content — but its presence, timing, and
  position in the complex were authored by the owner's attention. The selection function
  is the signature. The external corpus was never a sample of the world; it is a sample
  of the owner's attention.

In measurement language: each ingest path is a **measurement operator on the same
underlying state**, with its own basis and its own characterized loss model (embedding
non-injectivity, negation blindness, sensor distortion, self-report bias). Provenance
labels are therefore doing double duty the current doctrine leaves implicit: they are a
security boundary *and* sensor metadata — which instrument took this reading, under what
conditions, with what distortion. (§3.6–§3.7 make the instruments themselves first-class.)

Under this reframe the firewall's deepest worry — **masquerade**, algorithmic exhaust
reflected back as the owner's psyche — is stated more precisely than the doctrine states
it: masquerade is a **class confusion**, presenting content of one authorship class as if
it were a nearer class. Exclusion prevents class confusion by hiding a class. Typing
prevents it by making the class unforgeable and visible everywhere the content travels.
This note takes the typing position, with the structural conditions under which it is
sound (§3, §4).

**Frame scoping (2026-07-27).** "There is only one subject" is true **per frame**, and the
frame is now part of the claim: this instance's axis is *its owner's* axis, and other authors
— the resident agent, the node's own system, another palace instance — each carry an axis of
their own (§11). Everything above stands unchanged read frame-wise; what the revision removes
is only the silent assumption that the owner's frame is the *only* frame. The masquerade
definition survives intact and gains a new instance: presenting another author's content as
nearer to *this* owner than it is — including "trusted channel ⇒ owner's words," the live
139-row defect (§13) — is class confusion across frames.

## 1. The axis

Five base classes, ordered by **authorship distance** — the amount of mediation between
the owner and the artifact's content (a₀–a₃ from 2026-07-09; a₄ added 2026-07-27, §12):

| class | name | the owner's relation to the content | current realization |
|---|---|---|---|
| **a₀** | self-authored | produced the content and signed it | `AUTHORED_SOLO`, `AUTHORED_DIALOGUE` (owner's side), verdicts |
| **a₁** | author-initiated | caused the artifact to exist deliberately, without authoring its content wholesale | ingest events, queries, promotion acts — the append-only event log (`ingest-identity-and-amendment.md` §2) |
| **a₂** | author-sensed | an instrument's reading of the owner, not deliberately produced | `OBSERVED` (reserved) — `sensor_readings`, activity exhaust, temporal patterns |
| **a₃** | author-curated | someone else's content; the owner's authorship lives entirely in the selection act | `CURATED` |
| **a₄** | attributed testimony | another author's content received in interaction; the owner's mediation is at most the standing decision to interact (§12) | none typed yet — today's nearest rows: chat `speaker∈{agent,system}` (`OBSERVED` + metadata) |

Total order: a₀ > a₁ > a₂ > a₃ > a₄ (nearer = higher; a₄'s seat relative to a₃ is a recorded
default, PD-8). Each step down, the *content* is less the owner's while the *provenance
event* remains fully the owner's — which is exactly why all five belong in one system about
one subject. (For a₄ the provenance event thins to the interaction itself, and may be
system-initiated; the event's own class does the discriminating, per the pairing below.)

**The a₁/a₃ pairing (the selection-event insight).** A curated node decomposes into two
facts at two classes: the content (a₃) and the ingest event that selected it (a₁). The
log/index separation of `ingest-identity-and-amendment.md` §§1–2 already stores these
separately: the event log holds the owner's acts; the derived index holds the content.
The attention-trace — "what the owner chose to read, when, alongside what" — is the a₁
event stream over a₃ content. It exists today; it has simply never been *recognized* as
self-data. This note names it; whether anything reads it is parked (§10, PD-3).

**Edge cases:**

- **Dialogue counterparty — RESOLVED (2026-07-27, §11).** `AUTHORED_DIALOGUE` is defined
  as *the owner's words only* (`core/provenance.py` docstring: "your words to it are more
  yours than its words to you"). The 2026-07-09 text read the counterparty's words as "at
  best a₃" — that was the flattening §11 rejects: they are **a₀ on the counterparty
  author's frame** and enter the owner's frame at **a₄** (§12), never among his curation
  acts. Where they land is now answered at source (B-4): `Provenance.OBSERVED` with
  `speaker='agent'` row metadata (`dn-chat-sensor` CS-2, ratified; A1 closed the speaker
  set with `system`). The `speaker` field *is* the frame tag at conversational grain.
- **Dreamer/system output** is not a base class. Derived material takes a *footprint*
  from its support (§3), and `DERIVED_STRATUM`'s reserved semantics already state the
  matching doctrine: trusted as to origin, untrusted as to truth, never confusable with
  authored ground. (§11's attestation discipline extends exactly this origin/truth split
  across the node boundary.)

## 2. The factorization — G8 vindicated, not violated

An objection must be met head-on: **G8 retired the trust preorder on P.**
`core/provenance.py` is explicit: "No code orders the classes, and `INTERPRETED` is a
*derived* axis orthogonal to trust, so a single trust order would be fiction."

G8 was right, and this note does not reintroduce what it retired. G8's finding was that
**P conflates two coordinates** — authorship relation and derivation status — and no
single order over the conflated set is truthful. The axis is the factorization G8's
objection implies:

```
ρ  (conflated)          factors into        (α, δ)
─────────────                               ──────
AUTHORED_SOLO        →   (a₀, base)
AUTHORED_DIALOGUE    →   (a₀, base)          α : authorship class  (ordered chain)
CURATED              →   (a₃, base)          δ : derivation status (base | derived,
OBSERVED             →   (a₂, base)               with depth d — family 2, orthogonal)
INTERPRETED          →   (footprint(support), derived)
DERIVED_STRATUM      →   (footprint(support), derived, depth-carrying)
```

The order lives **only on the α coordinate, only over base classes**. Derived nodes are
not "somewhere on the trust order" — they carry a computed footprint (§3) plus their own
orthogonal depth. The fiction G8 retired (one order over a mixed set) never returns.
MR-membership remains the load-bearing set for the mirror, unchanged (§4).

*(2026-07-27: the map is no longer purely ρ-determined — for dialogue rows it refines over
`(ρ, speaker)` to reach a₄ (§12), the §7 derived-view move with one more input. Still per-frame,
still base-classes-only, still no order on ρ itself; G8's retirement is untouched. And there is
now explicitly **no order across frames** — a₀(trader) and a₂(owner) are incomparable by
construction, §11.)*

*(Verification item, not assumption: read the G8 entry at source — companion II / the gap
catalog — and confirm its rationale is the conflation reading and nothing broader. §9, B-1.)*

## 3. Formal core

**(1) The label.** α : V_base → A, A = {a₀ > a₁ > a₂ > a₃ > a₄}, a bounded chain
(a₄ added 2026-07-27, §12; per-frame per §11 — this α is α_owner, the instance's default
frame). For base nodes α is fixed at mint and immutable — same discipline as ρ today ("ρ is
invariant under derivation; only human promotion re-tags"). For every existing base node α is
**derivable from ρ by the fixed map in §2** — extended over `(ρ, speaker)` for dialogue rows
(§12) — α introduces no new stored fact for base nodes (§7).

**(2) The footprint (derived nodes).** For derived κ with support set S(κ):

  α̂(κ) = ⋀ { α̂(s) : s ∈ S(κ) }   — the meet (minimum, i.e. *furthest* class) over support.

A derived node's authorship footprint can never exceed its weakest support. This is
family 1's own pattern — a monotone map on a bounded lattice — applied to a new
coordinate; label-lattice information flow, nothing exotic. It is computable from the
derivation DAG (family 2's acyclic provenance-of-inference); whether it is *materialized*
is an efficiency choice (§10, PD-2).

**(3) Promotion is the only up-move.** No operation raises α̂ except an owner-certified
promotion: three-place (C, C′, warrant), verdict-gated, exactly the existing supersession/
promotion discipline. An adjudicator recommendation synthesized over a₂ support carries
footprint a₂ until the owner's signature converts the *promoted artifact* into an a₀
record. Promotion is a change of authorship class — which is *why* it rightly requires
the owner's key. This gives the blessing gate its semantic content: it was already the
rule; the axis explains it.

**(4) Evidentiary weight is monotone — and is tuning, never protection.** A weight
w : A → [0,1], monotone non-increasing in distance, w(a₀) = 1. Restating the spike's D2
lesson because it is the easiest mistake to re-make: **w is I-OS2's successor and carries
no part of any guarantee.** Bright lines are hard constraints bounding the feasible set;
every protection in §4 is a set-membership test on α̂/ρ, structural, weight-free. A
scalar weight is precisely what expected-value reasoning rationalizes past
(`the-sacred-boundary.md` §2.4).

**(5) Graded grounding — the envelope extends conservatively.** Current envelope
(NOTATION.md, family 2; I10): c ≤ γ^d · g, with g the authored-grounding score — support
reaching K₀. Generalize the single ground to per-class grounds:

  g_w(κ) = Σ_a  w(a) · g_a(κ),   g_a = fraction of κ's support reaching ground of class a
  c ≤ γ^d · g_w

Two properties make this the right move rather than a new mechanism:

- **Conservative extension.** w = 1_{a₀} recovers current doctrine *exactly*. The
  firewall is the degenerate weighting; current behavior is a special case, not a casualty.
- **d needs no new mint.** Per NOTATION.md, d is derivation depth in the acyclic DAG —
  0 for a leaf, 1 + max over derived parents. An external base node (curated chapter,
  observed aggregate) is a **leaf of its own class: d = 0, ground of class a₂/a₃**. A
  depth-1 synthesis over curated support then gets c ≤ γ · w(a₃) — nonzero, discounted,
  well-defined. *(The spike described d as "minted per Dreamer cycle"; NOTATION.md and
  `DerivedStore.depth` describe derivation depth. If the source matches NOTATION, OQ-1's
  d-half dissolves; verify at source — §9, B-2.)*

**(6) Sensor metadata — the calibration sheet.** Each base class carries a loss-model
annotation as first-class schema-adjacent documentation: a₀ — self-report bias; a₁ —
intent ≠ outcome; a₂ — instrument distortion, algorithmic shaping; a₃ —
author-of-content ≠ author-of-attention. These are the calibration sheets the ingestion
loss models already began (non-injectivity, training-objective selectivity, negation
blindness); the axis gives them a home per class. §3.7 adds the second half of a proper
calibration sheet: the **transform attribution** — interpreter identity, version, and
configuration digest — because a reading is an artifact of the instrument *and* of
whoever read the instrument. Class-level loss models may later refine to per-instrument
models; that refinement is parked (§10, PD-6).

**(7) Interpreters as projection maps — late fusion by doctrine.**

The reframe in §0 treats each ingest path as a measurement operator. This subsection
makes the operators first-class objects with their own discipline, because the
architecture has already committed to a fusion topology without naming it.

**(7a) The fusion topology is a theorem of the doctrine, not a choice left open.**
In sensor-fusion terms, a system may fuse in raw measurement space (early fusion), in
feature space, or over per-sensor interpreted outputs (late fusion). "Raw exhaust never
enters" (§4.1; both firewall notes) *prohibits* fusion in raw measurement space inside
the core: no component ever holds two raw streams to combine. Every sensor's readings
are projected into the shared representation first, and combination happens only there.
**The sealed core is a late-fusion architecture by security doctrine** — the same rule
that protects against the surveillance dossier fixes the fusion stage. One decision,
two consequences; neither is negotiable independently of the other.

**(7b) Anatomy of a projection map.** For each sensor domain *s* there is a raw
measurement space M_s (Oura JSON, activity exports, file bytes) living **outside** the
core, and an interpreter

  φ_s : M_s → 𝔎

that is the **sole path** from M_s into the stratum. A φ_s decomposes exactly as a
camera calibration does:

- **intrinsics** — domain expertise: what an overnight RMSSD figure *means*, which
  fields of a raw payload carry signal, what a defensible aggregate is. This is the
  doctor reading the test the owner cannot read; the system relies on the interpreter's
  expertise exactly as the owner relies on a specialist's.
- **extrinsics** — registration into the shared frame. **The shared coordinate is
  time**: timestamps are what allow heterogeneous readings to align at all
  (`sensor_readings.ts`; the correlator's lagged windows in
  `observed-iot-and-cross-source-synthesis.md` §2 are correlations over this axis and
  nothing else). A reading that cannot be registered in time cannot be fused.
- **the error model** — the §3.6 calibration sheet: characterized loss, not assumed
  fidelity.

**(7c) The pattern already exists in embryo — this names it.** The biometric
normalizer (`observed-iot-and-cross-source-synthesis.md` §1c: raw Oura JSON →
structured feature rows; core never imports the API client) is a deterministic φ_s.
The Librarian is φ_text, with the embedding loss model as its calibration sheet. The
correlator is not a φ_s at all — it is the **fusion stage**, and the doctrine that it
only ever sees post-projection signals ("never raw authored text", §2 safety rules) is
late fusion stated as a safety rule. What this note adds is the claim that these are
instances of one pattern with one discipline: **one expert per sensor domain, and the
expert is the only path from M_s into the stratum.** In house terms that is a
capability statement — a reading that did not pass through the domain's interpreter is
*unrepresentable*, the `sensor_readings`-has-no-provenance-column pattern applied to
provenance-of-transform. Interpreters are executable skills under `skills-and-scope.md`
(scoped tool, object-capability handle, gated install), so onboarding a new sensor
domain inherits the existing skill blessing gate — no new governance machinery is
required to answer "who certifies the doctor."

**(7d) Base relative to the core; derived relative to the world.** An interpreted
observation is *derived* out in the world (φ_s produced it from raw) yet lands as a
**base node** of class a₂/a₃ in the core's DAG (§3.5). There is no contradiction: the
provenance-of-inference DAG (family 2) records **the core's own derivations**, and
begins at ingestion. External derivation is recorded not as DAG edges but as **sensor
metadata**: interpreter identity, version, and configuration digest on the node. Two
attributions therefore ride every sensed node — the *measurement* (about the owner) and
the *transform* (the interpreter, at a version). The attestation layer already draws
this exact line one subsystem over: `DERIVED_STRATUM` is "trusted as to ORIGIN (the
attestation chain proves the Dreamer produced them), untrusted as to TRUTH"
(`core/provenance.py`). Transform attribution is the same origin-trust, extended to
external instruments.

**(7e) Re-interpretation is versioned supersession — the machinery exists.** When an
interpreter improves (better intrinsics, a fixed bug, a new aggregate), re-running
φ_s^{v2} over retained raw blobs is an **amendment**, not a mutation:
`ingest-identity-and-amendment.md` §4 already specifies it — stable identity, new
version, supersession recorded, raw unchanged, unchanged rows keep their points. No
mutate-the-immutable operation is needed to upgrade an instrument, which is the
capability-dissolution test passing again, now for calibration updates. The
interpreter version in the sensor metadata is what makes "which calibration produced
this reading" answerable forever.

**(7f) The fusion taxonomy maps onto math the system already runs.** Classical
taxonomy: *competitive* fusion (redundant sensors measuring the same quantity),
*complementary* (different sensors covering different aspects), *cooperative*
(combined signals deriving a quantity no single sensor measures).

- **Competitive fusion is already implemented as the corroboration lift**:
  c₀ = g·(1 + λ(|Agr|−1)) with agreement counted over *distinct* interpreters
  (NOTATION.md family 2; `core/recursion.py`) — and the dedup boundary rule
  (`ingest-identity-and-amendment.md` §7: distinct artifacts that agree are
  corroboration, never coalesced) is precisely the rule that keeps competitive fusion
  honest. The math was fusion-shaped before the vocabulary arrived.
- **Complementary fusion is the axis itself**: classes a₀–a₃ are different modalities
  of one subject, fused in the multilayer complex.
- **Cooperative fusion is the correlator**: cross-class derived signals producing
  correlations no single class contains.

The pipeline in vision terms, for the record: **per-sensor interpretation** (φ_s) →
**registration & fusion** (time-axis alignment; the correlator; the complex's
inter-layer structure) → **scene understanding** (the Dreamer, within the fused
complex). Three stages, three existing subsystems.

**(7g) Interpreter substrate — deterministic commit, model advice.** A φ_s may need a
model (unstructured domains) or may be pure code (the biometric normalizer). The house
pattern already resolves the split: **model advises, code acts** — one level down this
time. A model may participate in *interpretation*; deterministic code performs the
*commit* of rows, and whenever a model participated, its identity and version join the
transform attribution (7d) so model priors entering through a projection map are
attributable, characterized in the calibration sheet, and never mistaken for the
sensor's own signal. A model-committed write path is prohibited for the same reason
agents hold no live credentials. Default and re-entry recorded in §10, PD-7.

**(8) The access matrix — the axis as an integrity lattice.**

**(8a) The reading.** An ordered authorship coordinate plus the meet-footprint is a
**Biba-style integrity lattice**, and naming it buys searchable vocabulary and four
decades of known failure modes, not new machinery: the footprint rule (§3.2) is the
**low-water-mark policy** — a derived object drops to the minimum integrity of what it
read — and the self-model's a₀-only scope (§4.2) is **no-read-down**, enforced
structurally by the typed `MirrorView` rather than by checks.

**(8b) The inversion.** In a protection-ring OS, privilege increases toward the center.
Here it inverts: **capability dissolves toward the center.** The layer nearest the self
is written through the narrowest channel in the system (owner-attributable acts only)
and read by the most restricted scope in the system (the self-model). Nothing powerful
lives at the center; the center is where the fewest operations are representable — the
capability-dissolution principle showing up as ring geometry. Two corollaries that keep
the intuition precise:

- **The owner is the sole a₀ authority.** No agent authors a₀; every a₀ write is an
  owner-attributable act.
- **Channel and authority are distinct.** The Librarian is the sole write *conduit*
  (the ingestion channel), never an *author* — conflating the two is how "the Librarian
  is highly privileged" misreads the design. Its actual writes are safe-shaped, per
  (8e).

**(8c) The matrix.** Per-operation, per-layer:

| layer | write | read |
|---|---|---|
| **a₀** | ingestion channel only; every write owner-attributable (Librarian as conduit, never author) | MR consumers: self-model, synthesis, Ambassador (π_MR) |
| **a₁** | append-only event log, recorded as a side effect of owner acts | nothing yet (§10, PD-3) |
| **a₂** | ingestion channel only, committing outside-φ_s outputs (§3.7); raw M_s stays outside forever | declared-scope synthesis + correlator; **never** the self-model |
| **a₃** | ingestion channel (curated ingest) | deliberate non-default scope (`provenances={CURATED}`); synthesis under declared scope |
| **derived** | Dreamer / correlator via `DerivedStore` (provenance structurally unforgeable) | per declared scope; footprint = low-water-mark (8a) |

**(8d) Two enforcement regimes — one verified at source.** The matrix is enforced by
two different mechanisms for two different populations:

- **Minted agents — the capability semilattice. Verified 2026-07-09:**
  `PRE_DECLARED_MAX = frozenset({"run_python"})` (`core/factory/roles.py`) — **one
  handle in the entire grantable universe**, sandboxed execution, requested only by
  `coder` and `data_analyst`. No shell, credential, or network handle (documented,
  deliberate: a task needing one routes to the human gate, never satisfied by minting)
  — and **no store handle of any kind, read or write**. `RoleTemplate.__post_init__`
  refuses construction for any scope ⊄ MAX; the dispatcher holds only in-scope handles,
  so an out-of-scope call is *unreachable*, not checked-then-denied
  (`core/factory/tools.py`, `ToolNotInScopeError`). For the minted population,
  "nobody writes base layers" is therefore **vacuously structural**: touching any store
  is outside the space of grantable things.
- **Pipeline components — typed stores and module boundaries.** The Librarian, Dreamer,
  and correlator are not minted agents; they hold store access as ordinary code
  imports. Their confinement rests on the type plane: `DerivedStore`'s absent
  provenance parameter, `MirrorView`'s typed projection, the append-only log. This
  regime is the one with residual audit surface — B-9 — and is where the
  foundation-file-set concept (`security-planes.md`) must cover the modules that
  *define* these boundaries.

**(8e) Why the Librarian's privilege is safe-shaped.** Its writes decompose into
(i) **append-conduit** to the event log — owner-attributable events, never content of
its own authorship — and (ii) **re-materialization of a regenerable, content-addressed
index** (family 2; `ingest-identity-and-amendment.md` §§2–3, Q1 pending at source). A
compromised Librarian corrupts a *rebuildable projection*, never ground truth — the
privilege is real but its blast radius is bounded by regenerability. Not yet specified:
how placement works across axis classes (OQ-D).

**(8f) The Dreamer writes derived nodes and proposes edges — never base nodes, never
certification.** "Writing an edge" is minting a derived claim, and it carries this
note's factorization unchanged: the edge's **footprint** is the meet over its support
(endpoints and warrant — §3.2 extends to edges without modification), while its
**authority** is the proposed/certified status, raised only by the owner's verdict
(`the-edge-model.md` §3; `supersession-lifecycle.md` §2). An edge between two a₀ nodes
proposed by the Dreamer is high-footprint, zero-authority until signed. Evidence class
and authority status are separate coordinates — the §2 factorization recurring one
level up.

## 4. Preserved — the firewall's non-negotiables, restated structurally

Nothing in this section changes. Each is a set-membership constraint, weight-free:

1. **Raw exhaust never enters.** Only interpreted/aggregated a₂ material is
   ingest-eligible; the concentrated raw stream stays outside. Unchanged from both
   firewall notes; the surveillance-dossier reasoning stands.
2. **MR is untouched.** MIRROR_READABLE = {authored-solo, authored-dialogue} — in axis
   terms, the mirror and the BUILD-SPEC §15 baselines / Constitution-conformance read
   **α̂ = a₀ base nodes only**. The self-model never reads a₁–a₄ or any derived
   footprint below a₀. This is the spike's I-OS3, kept structural.
3. **No silent promotion.** α̂ is raised only by owner-certified promotion with warrant
   (spike I-OS4; `supersession-lifecycle.md` §§2–3). Interestingness buys attention and
   ingest-eligibility; it never buys class.
4. **Unforgeability is load-bearing.** The entire construction stands on α̂ being
   unrepresentable-if-wrong: immutable at mint for base nodes, computed (not asserted)
   for derived nodes. This is the spike's I-OS1 and its OQ-2, **inherited unresolved and
   still blocking** (§6).
5. **Bright lines are constraints, not weights.** §3(4). D2's ghost, pinned twice on
   purpose.

## 5. What changes

1. **Exclusion → typed graded readability, for synthesis only.** The Dreamer's
   *synthesis* read-scope may extend beyond MR to declared class sets (the existing
   "a query/agent declares which provenance classes it may read" mechanism from
   `observed-data-and-the-assistant-tier.md` — the machinery already exists). The
   *self-model* scope does not move (§4.2). This is the spike's single relaxation,
   adopted, with the guarantee carried by typing per §0.
2. **The observed layer gets its answer.** The spike's proposed layer becomes: a₂ base
   nodes (interpreted observations produced outside, landing typed), readable by
   synthesis under a declared scope, footprint-propagating into anything derived from
   them, permanently below a₀ absent promotion. The "stratum" naming overload the spike
   flagged is resolved by dropping the word: these are **a₂ base nodes**, not a stratum
   Sₙ.
3. **The correlator is unchanged and newly explained.** It reads across classes via
   derived signals and writes `INTERPRETED` — in axis terms it is the **fusion stage**
   of a late-fusion architecture (§3.7a/f): cooperative fusion over post-projection
   signals, with outputs carrying a mixed footprint. Its existing safety rules ("never
   raw authored text"; write-only to `DerivedStore`) are the footprint discipline and
   the late-fusion topology avant la lettre.
4. **Curated gains graded voice.** Under w, curated-supported synthesis can carry
   nonzero (discounted) confidence instead of the implicit zero of authored-only
   grounding — the reading corpus finally participates in reasoning *as evidence about
   the owner's attention and influences*, at a weight that says what it is.

## 6. The spike's open questions — disposition

- **OQ-1 (g, d for non-K₀ ground): answered in shape.** g generalizes to graded
  grounding g_w (§3.5); external base nodes are d = 0 leaves of their own class. The
  envelope *extends*; it is not replaced and the direction is not dead. Falsifiable at
  source: if `decay_bound` / I10's property tests hard-code K₀-only ground in a way that
  admits no per-class decomposition, §3.5 must be reworked (§9, B-2).
- **OQ-2 (unforgeable lineage): inherited, unresolved, blocking.** Now stricter: five
  base classes plus a computed footprint must be unforgeable, not one binary — and for a₄
  the *attested sender-frame* coordinate is exempted by design: it is origin-trusted only
  and feeds no protection (§11 cost 3), so unforgeability binds the receiver-frame
  coordinate and the attribution, never the counterparty's self-report. The known
  soft spot is externally-produced derived material — does the DAG record complete
  support for correlator outputs whose supports live in `sensor_readings` rather than
  the graph? (§9, B-3.)
- **OQ-3 (does typing preserve the no-masquerade guarantee?): answered — conditionally
  yes.** Typing preserves the guarantee **iff** (i) every protective boundary is a
  set-membership test on α̂/ρ (never a weight threshold), (ii) α̂ is unforgeable (OQ-2),
  and (iii) every owner-facing rendering surfaces the class. Under (i)–(iii), typing is
  *stronger* than exclusion: exclusion protects one boundary by hiding; typing protects
  every consumer, everywhere the content travels, and states precisely what masquerade
  is (class confusion, §0). If any of (i)–(iii) fails, exclusion was the safer wall and
  the firewall notes stand.

## 7. Schema & migration coupling — corrected

The design dialogue initially concluded the axis must be encoded "before `--apply`
relabels 918 rows, else a second migration." **Reading `core/provenance.py` corrects
this: no new column is needed for base nodes.** α is derivable from existing ρ by the
fixed map in §2 — and even legacy un-relabeled `authored` rows are α-unambiguous, since
both authored classes map to a₀. The axis can be layered as a **derived view over
existing labels**, which is itself evidence the taxonomy is cutting reality at a joint
the schema already respected.

What *does* couple to the migration, reduced to its true size:

- **C-1.** Confirm post-`--apply` every row carries a ρ in the §2 domain (no value
  outside the six enum classes). Cheap invariant check to ride along with `--apply`
  verification.
- **C-2.** The migration's backing design note was **not located** in this pass
  (`docs/**/*migration*` → no matches, 2026-07-09), consistent with the standing
  verification item in PROGRESS. Resolve that item first; if a migration design pass is
  needed, this note's §2 map should be an input to it.
- **C-3 (deferrable).** Materialized footprint on derived nodes is an optimization, not
  a schema prerequisite (§10, PD-2).

## 8. Proposed supersession & amendment set (lands at ratification, not before)

Recording the intended front-matter surgery exactly, per house discipline:

- **Supersedes `dn-observed-stratum-spike` (whole note).** The spike's central question
  (OQ-3) is answered (§6); its direction is absorbed with corrections (naming resolved,
  I-OS2 succeeded by w with the same demotion, OQ-1 answered in shape). The spike
  remains in place with a `superseded_by` banner — it is the historical record of the
  investigation, including defects D1–D3, and house discipline is supersession-in-place,
  never rewriting. *(Chain accuracy: the spike superseded nothing — its front-matter is
  `supersedes: null` and it declared the firewall notes authoritative. This note is the
  first actual supersession in the lineage doctrine → divergent spike → resolution.)*
- **Partially amends `dn-observed-data-and-the-assistant-tier`:** the firewall's
  *mechanism* (exclusion of observed from all mirror-adjacent reasoning) is amended to
  typed graded readability for synthesis (§5.1) — while its **core decision** (two
  purposes, no shared pool for the *self-model*; raw exhaust reasoning; no silent
  promotion) is preserved verbatim (§4). Partially-superseded banner on the "Firewall"
  paragraph only.
- **Partially amends `dn-observed-iot-and-cross-source-synthesis` §0:** "Dreamers do not
  combine data sources" is amended to "the Dreamer's *self-model* reads a₀ only; its
  *synthesis* may read declared class sets with footprint propagation." §§1–5
  (correlator, ingest paths, safety rules) stand unamended.
- **Warrant:** a new finding recording the 2026-07-09 design dialogue and the §7
  correction — next id in the findings sequence (0023 if none minted since
  finding-0022; verify before minting). *(2026-07-27: the warrant set now also carries the
  linked node/instance capsules — `nodes-are-nodes-cross-node-protocols` above all — as the
  §§11–15 warrant. The "0023" figure is long stale (the sequence passed 0249 this week) and
  MUST be re-derived at minting; a copied id is exactly `the-unchecked-claim`'s defect.)*
- **Owner ratification** is the gate for all of the above. Until it, the divergence
  notice in the spike governs and the firewall notes are authoritative.

## 9. What a builder must investigate first (with falsifiers)

Read the code, then report. Do not resolve unilaterally.

- **B-1. G8 at source.** Read the G8 entry (companion II / gap catalog). Confirm its
  rationale is the conflation reading (§2). *Falsifier: if G8's rationale bars any order
  on any provenance-adjacent coordinate — not just the conflated P — §2's factorization
  argument fails and this note must confront G8 directly or die.*
- **B-2. The envelope at source.** `core/recursion.py` (`decay_bound`), `DerivedStore.depth`,
  I10's property tests, and `recursive-strata.md` Invariant 10 **at source** (the spike's
  D1 citation caveat still stands — it was never read at source). Report whether g admits
  per-class decomposition and whether d is derivation-depth (NOTATION) or cycle-minted
  (spike's description). *Falsifier for §3.5: K₀-only ground hard-coded with no
  decomposition seam.*
- **B-3. Footprint computability.** Trace support-edge completeness for every derived
  write path, especially correlator outputs whose supports are `sensor_readings` rows.
  Can α̂ be computed, unforgeably, for every derived node? *Falsifier for the whole
  direction (inherits spike OQ-2): any derived node whose support set is unrecorded or
  assertable by the producer.*
- **B-4. Dialogue counterparty landing zone — ANSWERED AT SOURCE (2026-07-27), one lane
  residual.** CLI-transcript lane: every chat row lands `Provenance.OBSERVED` with
  `speaker ∈ {owner, agent, system}` as row metadata (`dn-chat-sensor` CS-2 + A1, ratified
  — speaker is never provenance). The Ambassador's own transcript lane is still unbuilt
  and parked at `dn-chat-sensor` §4 ("other chat sources") — that residual re-parks there,
  not here. Classification is resolved by §11/§12: counterparty words are a₄ in the
  owner's frame, a₀ in the counterparty's.
- **B-5. Declared-scope enforcement.** Is "a query/agent declares which provenance
  classes it may read" enforced structurally (typed view, MirrorView-style) or by
  runtime filter? Same question as spike §5.3, still worth knowing independent of
  everything here. *Report either way.*
- **B-6. Renderer class-visibility.** Inventory owner-facing rendering surfaces; confirm
  each can carry a class marker (condition (iii) of §6/OQ-3). *Falsifier for the typing
  position: a surface that structurally cannot distinguish classes.*
- **B-7. Interpreter sole-write-path audit.** For each existing ingest surface
  (Librarian text path; the planned biometric normalizer per
  `observed-iot-and-cross-source-synthesis.md` §1c; any research-airlock landing path),
  trace every write path into its target store and report whether an identifiable
  interpreter is the *only* path in (§3.7c), citing `path:line`. *Falsifier for the
  capability statement: a write path into `sensor_readings` or the ingest stores that
  bypasses an identifiable interpreter.*
- **B-8. Transform-attribution capacity.** Report where interpreter identity, version,
  and configuration digest could live today (per-row column, `raw_json` sidecar, ingest-
  event log fields) and whether the ingest-event log already records *which code*
  performed each ingest. If the event log carries it, §3.7d needs no schema change —
  the log/index separation covers transform attribution the way it covers a₁ (§1).
  *No falsifier — placement input; but if no surface can carry it, §3.7e's "answerable
  forever" claim fails and must be weakened.*
- **B-9. Pipeline-component access regime.** The minted-agent half of the
  base-layer-write question is **resolved at source** (2026-07-09; citations in §3.8d)
  and needs no builder pass. The residue: for the Librarian, Dreamer, and correlator,
  report how each acquires its store access (`path:line` of the imports/constructors),
  what besides module discipline confines each to its designated stores, and whether
  the foundation file set (`security-planes.md`) covers the modules that define these
  boundaries (`core/provenance.py`, `core/mirror.py`, `core/stores/derived.py`,
  `core/factory/roles.py`). Overlaps B-7's write-path tracing; fold them if convenient.
  *Falsifier for §3.8d's pipeline claim: a pipeline component able to construct a
  base-store writer through a public constructor carrying no type or label constraint.*
- **B-10. The conversational census (added 2026-07-27; the §15 non-vacuous check).**
  Implement the `(ρ, speaker)` α-refinement as a derived view and run it over
  `data/chatlog.sqlite` (mode=ro): every `speaker ∈ {agent, system}` row maps to a₄; no
  `system` row is promotion-eligible (A1.1); `speaker='owner'` rows are byte-identically
  where the unrefined map put them (the CS-2 fail-safe, untouched). Real inputs exist
  (6,429 agent rows per `dn-agentic-loop` G-C; 139 mis-attributed rows per
  `dn-chat-sensor` A2), so the check can genuinely redden. *Falsifier: any refinement
  output that raises a row's coordinate relative to today's map, or that consults a
  channel/trust field to compute α (§13's collapse, caught mechanically).*
- **B-11. The landing-path fiber audit (added 2026-07-27; a ratchet recorded ahead of its
  subject).** When any testimony landing path is first proposed — Ambassador transcripts
  or cross-node — trace that no fiber is auto-minted from a landed a₄ row into local
  ground (§14's laundering path). *Falsifier: a landed testimony row reachable as support
  by the grounding walk without an owner-certified edge.* *Degenerate input, named per the
  false-success rule: today's corpus has zero landing paths, so this audit is vacuously
  green until one exists — it must be run at the landing path's build, never reported as
  passing before.*

## 10. Parked decisions

- **PD-1. Weight vector w values.** Park until Track L is live; w is tuning and Track L
  is the only instrument that can tune it. Default at unpark: w = (1, 1, 0.5, 0.5) as a
  first ansatz, explicitly arbitrary. Re-entry: Track L live + verdict taxonomy ratified.
  *(2026-07-27: the vector gains a fifth entry, w(a₄) — this IS the `w(a_self)` obligation
  `dn-agentic-loop` G-C and `dn-code-ingest-pipeline` route to this gate (§12). Ansatz 0.25,
  equally arbitrary; strictly below w(a₃) per PD-8's chain default. Same park, same
  re-entry.)*
- **PD-2. Materialized α̂ vs computed-on-read.** Default: computed from the DAG.
  Re-entry: profiling shows footprint computation on the synthesis path is hot.
- **PD-3. Reading the a₁ attention-trace.** The selection-event stream is named (§1)
  but nothing reads it yet. Re-entry: Track L live, and only as a synthesis input with
  footprint a₁ — never a self-model input without a separate ratification.
- **PD-4. Inter-class edges in the Laplacian.** Inherits the spike's PD-1 unchanged:
  default no — separate layers, typed inter-layer edges, `A_geom` stays a₀-lineage.
  Re-entry: multilayer construction specified + Track L comparison possible.
- **PD-5. a₁ as a stored label vs event-log-only.** Default: event-log-only (it already
  lives there; §1). Re-entry: PD-3 unparks and needs a queryable label.
- **PD-6. Per-instrument grounding weights.** g_w (§3.5) weights by *class*; a refinement
  weights by *instrument*, w(s), since two a₂ sensors can differ in reliability as much
  as two classes do. Default: per-class only — per-instrument weights are exactly the
  kind of parameter surface that multiplies before the harness exists to tune it.
  Re-entry: Track L live **and** verdict evidence of intra-class reliability spread
  (i.e., the data asks for it; the design does not volunteer it).
- **PD-7. Interpreter substrate.** Default: deterministic φ_s wherever the domain admits
  it; where a model must participate, model-advises-code-commits with mandatory model
  identity + version in the transform attribution (§3.7g). Re-entry: the first sensor
  domain whose interpretation demonstrably cannot be deterministic — at which point the
  model-participating interpreter needs its own short design pass (attestation shape,
  calibration-sheet entries for model priors) before install.
- **PD-8. a₄'s seat relative to a₃ (added 2026-07-27).** Default: a₃ > a₄ — the owner's
  per-artifact selection of a finished work is more of his mediation than elicitation-in-
  interaction. `[INFERENCE — the ordering argument is this pass's]` Affects only w
  monotonicity and rendering order; every protection is set-membership (§3.4), so the seat
  is tunable without safety consequence. Re-entry: ratification (the owner reads the chain
  aloud — the non-goals rule applied to an order), or the first w tuning at Track L.
- **PD-9. ρ member vs derived view for a₄ (added 2026-07-27).** Default: derived view over
  `(ρ, attribution metadata)` — no migration, no new `Provenance` member (§12; the §7
  argument; `dn-agentic-loop`'s fail-safe preserved). Re-entry: the first cross-node
  landing path is designed — at which point structural minting wants a real member with no
  provenance parameter on the landing API (the `CodeObservation.to_row` move,
  `core/kernel/provenance.py:36-44`).
- **PD-10. The testimony landing stratum (added 2026-07-27).** Default: shape undecided,
  constraints decided — local, excluded-by-default (the `EXHAUST` precedent,
  `core/kernel/scope.py:120-128`), readable only under a grant that names it (the
  CURATED/CODE deliberate-grant precedent). Re-entry: cross-node protocol design, which
  waits on a second instance (§15).
- **PD-11. Retroactive trust-revocation errata (added 2026-07-27).** A node's attestation
  later voided ⇒ every row landed under it becomes erratum-candidate en masse; the
  authority lane (spine-revocation + owner?) is absent from `dn-erratum-relation` §3's
  authority list, and the target class may be too large to enumerate (its PD-1 tension).
  Default: none — flagged, not solved. Re-entry: the node-trust state machine is designed.

---

*Sections 11–15 were composed 2026-07-27 (fable pass) from the node/instance dialogue; the
warrant capsules are linked in the front matter and quoted at source below.*

## 11. The frame extension — one axis per author

**Warrant (owner, verbatim, `nodes-are-nodes-cross-node-protocols.md` capsule):** *"a
different instance is a different author, the trader is the trader author, not the alberto
author, not the claude/dev author, not my node's system author, different authors, and when
talking about authorship as an axis, they are at the opposite end of alberto author … but
their trust relationship between each other (instance nodes) are not the same as my
authorship."* Four authors are named — and two of them already have rows in this instance's
stores today (the claude/dev author and the node's system author: `data/chatlog.sqlite`,
`speaker ∈ {agent, system}` per `dn-chat-sensor` A1; 6,429 agent-authored base rows counted
at `dn-agentic-loop` G-C). **The frame question does not wait for a second instance.**

**Ruling: the axis is a frame bundle — one chain per author — and §1's single axis is its
projection onto the owner's frame.** Formally: replace `α : V_base → A` with a family
`α_u : V_base → A` indexed by author `u ∈ U`. Every frame is total in principle (all content
sits at *some* distance from any author), but exactly two coordinates are ever
**materialized**: the owner-frame coordinate, computed at mint by the §2 map (extended per
§12), and — for received content only — the *sender-frame* coordinate, carried as an
**attestation**, never computed here (§12). Cross-instance content is a **frame change, not
a longer distance**. `[INFERENCE]` — the formal shape is this pass's construction; the
multi-author fact it encodes is the owner's, verbatim.

**Why a single total order does not survive — shown, not asserted.** Try the alternative:
seat the trader's self-authored claim on the owner's chain. Any honest seat is ≤ a₃ (not his
hand, not his instrument, not his selection of a finished artifact). But then trader-a₀ and
trader-a₂ content collapse into the same far neighborhood, destroying at the boundary the
coordinate the sender's own machinery keeps unforgeable. That information already has a
consumer on paper: **correction processing**. `dn-erratum-relation` (ratified) makes a
retraction a warranted act discriminated by *the asserting author's* classes — a counterparty
retracts what *it authored*, not what it relayed — so a receiver that flattened everything to
one owner-relative rung cannot even state which landed rows a sender-side retraction covers.
`[INFERENCE — consumer identified by analysis; nothing is built]` If that consumer (and every
other) turns out to need only the receiver-frame coordinate, the bundle collapses — that is
the named falsifier, §15.

**What survives, exactly.** Within one frame, §§2–5 stand unchanged: the chain, mint-
immutability, the meet-footprint (frame-wise: `α̂_u(κ) = ⋀{α̂_u(s) : s ∈ S(κ)}`), promotion
as the only up-move, w monotone per frame. Nothing here re-orders what G8 retired: no order
on ρ, and now explicitly **no order across frames**.

**The cost, stated plainly (this is not free):**

1. §0's "there is only one subject" weakens to *one subject per instance* — the reframe
   holds frame-wise, and the frame is part of the claim.
2. Any consumer wanting a single scalar must first **choose a frame**. The instance's
   default frame is its owner's; that choice becomes visible policy, not silent assumption.
3. The sender-frame coordinate is **origin-trusted, truth-untrusted** — the
   `DERIVED_STRATUM` doctrine (`core/kernel/provenance.py:60-66`) extended across the node
   boundary. A counterparty can mis-attest its own frame; the spine authenticates the node,
   never its bookkeeping ([[aws-as-the-authorization-spine]]). Therefore **no protection may
   be a function of the attested coordinate** — it feeds w and rendering, both tuning
   (§3.4's rule, doing new work).
4. Cross-frame comparability, if ever wanted, is a deliberate transport with its own design
   — the CS-f conservatism (`dn-capability-scope`, Parked: "re-binning … is always a new
   measurement") applied to frames. `[INFERENCE]`

**Divergence is expected, not drift.** Owner, verbatim: *"they could have slightly different
authored content and dialogue, and that's ok."* Two instances disagreeing is two authors
correctly not being the same author. No reconciliation machinery is licensed by
disagreement; the erratum consequences are drawn in §12.

## 12. The fifth class — attributed testimony (a₄)

**The gap.** A claim received from another author in interaction — an agent's utterance, a
hook's notice, a future cross-node answer — is not the owner's hand (a₀), not his deliberate
act (a₁), not an instrument's reading of *him* (a₂), and not his curation of a finished
artifact (a₃ — there the selection function is the owner's signature; here the *counterparty*
performed the selection, and the solicitation may be system-initiated). Today's taxonomy has
no member for it, and the rows exist anyway, metadata-discriminated inside `OBSERVED`
(`dn-agentic-loop` G-C, ratified — which routes exactly this class, and its weight
`w(a_self)`, to this note's gate; its §2.7 reconciliation table names
`dn-authorship-distance-axis` "EXTEND (amendment candidate named)"). Content with no home gets filed as something it is not — the same
structural gap `speaker='system'` closed at `dn-chat-sensor` A1, one level up.

**Decision: one new base class, a₄, plus a mandatory attestation record — not a rung per
author, and not a trust grade.** Every a₄ node carries:

| carried | what it is |
|---|---|
| receiver-frame coordinate | a₄ — fixed at mint, immutable; §3's discipline unchanged (promotion the only up-move) |
| author attribution | whose frame the content is native to: `speaker` / agent id / node role — row metadata, the §3.7d transform-attribution pattern |
| sender-frame coordinate | *(cross-node only)* the sender's own α for the content, **as attested** — origin-trusted, truth-untrusted (§11 cost 3) |
| channel record | the trust standing under which it arrived (local process / attested node / …) — §13's axis, **recorded beside, never fused** |

- **One class for all foreign authors.** Resident agent, node system, remote instance: one
  a₄, discriminated by attribution, never by enum growth. This generalizes
  `dn-agentic-loop`'s own ruling ("NOT a stratum per agent — the lattice is a finite enum;
  producers are unbounded", §2.4b) — producers are attribution; classes are structure. It is
  also §13 made structural: if resident-agent testimony sat at a different *rung* than
  remote-instance testimony, the axis would be encoding channel trust — the collapse §13
  forbids.
- **`a_self`, resolved.** The `w(a_self)` entry that `dn-agentic-loop` G-C and
  `dn-code-ingest-pipeline` route to this note's PD-1 gate is **w(a₄) restricted to
  resident-agent attribution**: a_self is not a sixth rung; it is a₄ worn by the claude/dev
  author. One weight per class; per-author refinement of w is PD-6's per-instrument question
  wearing a new name, and parks with it. `[INFERENCE — the unification is this pass's; the
  ratified notes name the gate, not the shape]`
- **ρ stays put for now.** The coordinate is a **derived view over (ρ, attribution
  metadata)** — the §7 argument, again decisive: existing labels plus existing metadata
  already determine a₄ for every current row, so no migration and no new `Provenance` member
  yet (PD-9). This preserves `dn-agentic-loop`'s recorded fail-safe ("until then OBSERVED
  stands"). The refinement moves **only** `speaker ∈ {agent, system}` rows, strictly in the
  over-distrust direction; owner CLI utterances stay at the CS-2 fail-safe (a₂-mapped, with
  `/capture` the promotion path — the never-automatic rule is untouched).
- **Never mirror-readable; machine-promotion impossible; `system` rows never promotable at
  all** (A1.1, inherited verbatim). Owner promotion of an a₄ node — adopting another's claim
  as his own record — is the §3.3 signed act; the warrant should name the original author,
  because the adoption is the owner's while the words remain attributed. `[INFERENCE]`
- **No cross-node erratum authority.** `dn-erratum-relation` E1 (warranted or
  unrepresentable) already gives this its form: **no authority lane exists by which a
  counterparty's contrary claim retracts a local row.** A counterparty retracting its *own*
  prior testimony lands as new testimony *about* that testimony; whether it also warrants a
  local erratum against the landed rows is an owner/policy act. The ugly case is named, not
  solved: attestation revoked retroactively ⇒ every row landed under it becomes
  erratum-candidate en masse, an authority lane `dn-erratum-relation` §3 does not yet list
  (PD-11).

## 13. Authorship and node trust are orthogonal — the two-axis law

Owner, verbatim: *"their trust relationship between each other (instance nodes) are not the
same as my authorship."*

| axis | question | where it acts | scale |
|---|---|---|---|
| authorship distance | how mediated, and from whose hand? | **on the result** — a coordinate carried by what returns | a₀ … a₄, per frame (§11) |
| node trust | may I address this counterparty at all? | **before the query** — a precondition on the grant/channel | attested / revoked / unreachable |

**Trust gates the sentence; authorship annotates the answer.** A revoked node cannot be
scoped, so no query against it is even expressible; everything an attested node returns
arrives far from a₀-owner — which is *correct*, not a defect.

**Both collapses, named:**

- *"far ⇒ distrusted"* makes every counterparty useless: a trader at maximal node trust —
  spine-attested, enclave-bound — is still, correctly, at the far end of the owner's frame.
- *"trusted ⇒ mine"* is **the 139-row defect, exactly**: hook output filed as
  `speaker='owner'` because it arrived on the legitimate transcript channel
  (`dn-chat-sensor` A1/A2 — ratified, owner-amended; the rows sit uncorrected in
  `data/chatlog.sqlite` today pending the erratum build, `dn-erratum-relation` §5). Channel
  legitimacy was read as authorship. Not hypothetical: it forced two amendments to a
  ratified note.

**The structural statement:** no function computes any α coordinate from a trust/channel
input, and no trust decision reads α. The two axes meet only as co-present fields on a row
(§12's table), never in each other's derivations. Same partition-not-stack shape the warrant
capsule notes for the KMS threat layering: independent controls answering different
questions; merging them destroys what makes each useful.

*Falsifier for the law:* a legitimate consumer is exhibited that cannot be specified without
**deriving** one axis from the other. (Reading both is expected; deriving is the collapse.)

## 14. Node, scope, and containment — where the network enters the algebra, and where it must not

The capsules propose: make **node** a scope coordinate, and *"the knowledge graph is
contained to its own node"* becomes *"no scope may name another node's stratum"* — a sentence
that cannot be constructed. Grounded against the ratified lattice (`dn-capability-scope`
§2.1; `core/kernel/scope.py`), the attractive version — **node as a stratum** — does not
survive the test:

1. **A stratum is grant vocabulary over data this instance holds.** Σ's downward closure,
   meets, and ideals are evaluated by this instance over its own refinement forest R
   (`core/kernel/scope.py:60-96`; "R is grant vocabulary, not a disk partition", `:73-75` —
   vocabulary *over its own stores*). A foreign corpus is not a region of this instance's
   data; naming it in R would assert exactly the addressability containment exists to deny.
2. **Producers are unbounded; the enum is finite.** `dn-agentic-loop` §2.4b already rejected
   stratum-per-agent on this shape; stratum-per-node is the same rejected move at network
   scale.
3. **The inheritance that made "node is a stratum" attractive survives anyway — on the
   legitimate side.** What strata machinery *should* govern is the **landed testimony**:
   local rows in a local stratum, which get ideals, grants, budgets, and default-exclusion
   for free. The right local shape is the `EXHAUST` precedent — an excluded-by-default
   refinement, readable only under a grant that names it
   (`core/kernel/scope.py:120-128`; the CURATED/CODE deliberate-grant precedent) — PD-10.

**Verdict `[INFERENCE]`: a node is a principal, not a scope coordinate.** Three homes, none
a fifth lattice component:

| concern | question | home |
|---|---|---|
| addressing | may I ask node X at all? | node trust, **pre-query, edge-side** — only `edge/` touches the network (NN-2); the sealed core never addresses a counterparty (NN-1) |
| granting | what may node X ask of *us*? | a scope this instance computes for that principal in its **own** (Σ,E,T,A), default ⊥; node identity indexes the grant as client class already does |
| landing | what do answers become here? | a₄ rows (§12) in a local, deliberately-granted stratum (PD-10) |

A cross-node ask is a **protocol act that returns rows** — negotiated, authenticated,
refusable (three states: declined ≠ unreachable ≠ answered-no) — never a read against a
foreign Σ. The spine's role→node binding makes the principal identity checkable
([[aws-as-the-authorization-spine]]); the anchor authenticates and must never carry
(NN-11: the interface may transit a third party; the corpus never does).

**The containment sentence, honestly graded.** "No scope may name another node's stratum" is
true today by unconstructibility — `Stratum` has no foreign member — and **vacuously so**:
per the false-success rule, the degenerate input is the single-instance corpus itself, on
which every cross-node invariant passes without testing its claim (the observable — an enum
with no foreign members — is not causally downstream of any protocol behaving well). The
sentence earns teeth only when a protocol first proposes to mint addressable foreign
vocabulary, and the refusal to write down **now** is: such a proposal is admitted only as
principal + grant + landing (the table above), never as Σ-vocabulary. Recorded so the
elegant wrong version has a named refusal waiting for it.

Likewise the capsule's walk rule — *a semantic walk must never traverse a cross-node edge* —
is, stated at the right layer, not a new walk rule at all: cross-node edges are not edges of
this graph, so the walk cannot traverse what the store cannot represent. The enforcement
point is the **landing path**: a testimony row arrives with **no fibers into local ground**
beyond its own attribution/warrant records; any auto-minted fiber from a foreign claim into
local support is *the* laundering path, and the grounding walk treating a₄ content as ground
is governed the same way every class is — by g_w's weight (tuning) over set-membership
protections that never move (§3.4, §4). `[INFERENCE]`

## 15. Decidability fence, non-goals, and the falsifiers of the revision

**Nothing cross-node is buildable until a second instance exists** — a protocol with one
endpoint cannot be falsified. The fence:

| decidable now (this revision decides) | genuinely waits (second instance / protocol design) |
|---|---|
| frame relativity (§11) — forced by resident authors already in-store | the wire protocol; refusal semantics (declined ≠ unreachable ≠ no) |
| a₄ + the attestation record's shape (§12) | attestation payload format; limits of sender-frame verification (OQ-E) |
| the orthogonality law + its falsifier (§13) | the node-trust state machine; revocation semantics |
| node-as-principal; the named refusal of Σ-vocabulary (§14) | the landing stratum's concrete shape (PD-10); budgets |
| the (ρ, speaker) view refinement — testable on the live chatlog **today** (B-10) | the retroactive-revocation erratum lane (PD-11) |

**Non-goals of the 2026-07-27 revision** (load-bearing; the owner reads these at
ratification):

- **NOT a cross-node protocol design.** No message, handshake, or transport is specified
  here. `[stated]`
- **NOT an amendment to any ratified note.** `dn-chat-sensor`, `dn-capability-scope`,
  `dn-erratum-relation`, `dn-agentic-loop` are cited ground, untouched. `[stated]`
- **NOT the constitutional question.** Whether `CONSTITUTION.md` is global, per-instance, or
  a kernel each instance narrows is the owner's alone (the `palace-instances-as-nodes`
  capsule, OPEN 1); nothing here presumes an answer. `[stated]`
- **NOT reconciliation machinery.** Divergence between instances is expected (§11); no
  sync/merge is licensed by this note. `[INFERENCE — generalized from the owner's "that's
  ok"]`
- **NOT a change to CS-2's fail-safe.** Owner CLI utterances stay OBSERVED → a₂-with-
  promotion-path; the refinement moves only `speaker ∈ {agent, system}` rows, in the
  over-distrust direction. `[INFERENCE — the direction is this pass's fail-safe choice]`

**The central claim and its named falsifier.** Central claim: *authorship distance is
frame-relative; cross-author content enters the owner's frame only at a₄ carrying its
attestation record; no protection is a function of the attested sender-frame coordinate.*
**The flattening falsifier:** if every consumer of a₄ content — retrieval weighting,
rendering, correction processing, promotion — is shown to need only the receiver-frame
coordinate and never the sender-frame attestation, the frame bundle collapses to one chain
plus one rung, and §11's machinery should be deleted in favor of bare a₄. The first
discriminating consumer to test is sender-side correction processing (§11): if it can be
fully specified without the sender-frame coordinate, that is strong evidence for collapse.

**The degenerate input (the false-success rule, applied to this revision).** The
single-instance, pre-protocol corpus: *every* cross-node invariant — no foreign stratum
nameable, testimony never mirror-readable, trust never implying authorship at node scale —
evaluates green over **zero cross-node rows**. A checker that inspects the `Stratum` enum
for foreign members and reports success is the false success, named. The **non-vacuous**
check available today is conversational-scale: after the (ρ, speaker) refinement, a census
over `data/chatlog.sqlite` (mode=ro) must show zero `speaker ∈ {agent, system}` rows carrying
any coordinate above a₄, and zero promotion-eligible `system` rows (A1.1) — real inputs
exist (6,429 + 139 rows), so this check can actually redden (B-10).

## Open questions

- **OQ-A (blocking, inherited).** Spike OQ-2 / B-3: unforgeable α̂ for derived material
  with out-of-graph supports. The direction fails without it — same kill condition the
  spike recorded, now with five classes at stake (§6's OQ-2 disposition scopes what
  unforgeability means for a₄).
- **OQ-B.** Does `AUTHORED_DIALOGUE` belong at a₀ without qualification, given the
  counterparty shapes the elicitation? The owner's words are the owner's; the *prompt
  structure* is not. Likely resolution: a₀ with a loss-model annotation
  (elicitation-shaped), not a new class. Owner should weigh personally. *(§11 sharpens the
  question without answering it: the counterparty shapes elicitation from its own frame,
  so the annotation would name whose frame did the shaping.)*
- **OQ-C.** Should promotion be single-step-up only (aᵢ → aᵢ₋₁) or arbitrary-up
  (aᵢ → a₀ direct)? Lean: arbitrary-up with the warrant carrying the burden — the gate
  is the owner's judgment, not the ladder. Settle at verdict-taxonomy ratification.
- **OQ-D.** How does the Librarian place and index across axis classes — one index
  carrying α labels, or per-class indexes? This is the `MirrorView` question one level
  down: typed views over one store vs. separate stores. Couples to
  `ingest-identity-and-amendment.md` Q1 (index keying, unverified at source) and to
  (8e)'s unspecified placement mechanics. Settle before any a₂/a₃ index work begins;
  lean: undecided — both satisfy the matrix in §3.8c, and the deciding evidence is
  whether declared-scope reads can be made structural (B-5) under each shape.
- **OQ-E (added 2026-07-27).** Is there any protocol-level strengthening of the
  sender-frame attestation worth its cost — per-claim signed provenance, an attested
  envelope carrying the sender's α — or is origin-trusted/truth-untrusted the permanent
  honest ceiling? Lean: permanent — a counterparty's self-report of its own authorship
  classes is exactly the self-vouching an external anchor cannot fix; the spine
  authenticates the node, never its bookkeeping ([[aws-as-the-authorization-spine]]).
  `[INFERENCE]` Settles at cross-node protocol design (second instance).

## Cross-references

- `docs/design-notes/observed-stratum-spike.md` — the investigation this note resolves;
  D1–D3 and OQ-1–3 dispositioned in §6. **Intended supersession target.**
- `docs/design-notes/observed-data-and-the-assistant-tier.md` — core decision preserved
  (§4); firewall mechanism amended (§5.1, §8). **Authoritative until ratification.**
- `docs/design-notes/observed-iot-and-cross-source-synthesis.md` — §0 amended (§8);
  correlator §§1–5 stand, re-read in §3.7 as the fusion stage and the embryonic φ_s
  pattern (§1c normalizer). **Authoritative until ratification.**
- `docs/design-notes/skills-and-scope.md` — interpreters are executable skills; the
  install/blessing gate that answers §3.7c's "who certifies the doctor."
- `docs/design-notes/attestation-layer.md` — origin-trust precedent extended to
  transform attribution (§3.7d).
- `core/provenance.py` — ρ, MR, G8's retirement of the trust preorder, and the six-class
  spectrum the §2 factorization maps from. Read 2026-07-09.
- `core/factory/roles.py`, `core/factory/tools.py` — the capability semilattice:
  `PRE_DECLARED_MAX = {"run_python"}`, construction-time refusal of scope ⊄ MAX,
  dispatcher unreachability of out-of-scope calls (§3.8d). Read 2026-07-09.
- `docs/NOTATION.md` — families 1, 2, 5; c ≤ γ^d · g and the d/g definitions §3.5 extends.
- `docs/design-notes/the-sacred-boundary.md` §2.3–§2.4, §3 — promotion gating;
  un-purchasable-by-EV; capability dissolution.
- `docs/design-notes/ingest-identity-and-amendment.md` §§1–3 — the log/index separation
  that already physically realizes the a₁/a₃ decomposition.
- `docs/design-notes/supersession-lifecycle.md` — three-place supersession; blessing gate.
- `docs/design-notes/recursive-strata.md` + amendment — Invariant 10 (⚠ still unread at
  source; B-2); `DERIVED_STRATUM` reserved semantics.
- `docs/design-notes/live-adoption-and-longitudinal-harness.md` — Track L as arbiter;
  shared prerequisites; PD-1's re-entry.

*Added 2026-07-27 (§§11–15):*

- `docs/brainstorms/nodes-are-nodes-cross-node-protocols.md` — **the §§11–15 warrant**: the
  owner's four authors and the orthogonality correction, verbatim; the scoping close.
- `docs/brainstorms/palace-instances-as-nodes.md` — containment ("the knowledge graph is
  contained to its own node"); the constitutional question §15 declines (owner's alone).
- `docs/brainstorms/aws-as-the-authorization-spine.md` — role→node binding; the spine
  authorizes the node, never the core; the anchor authenticates and never carries.
- `docs/design-notes/capability-scope-algebra.md` + `core/kernel/scope.py` — the ratified
  lattice §14 grounds against (`Stratum`/R `:60-96`; excluded refinements `:120-128`;
  ideals `:626-648`). Read at source 2026-07-27.
- `docs/design-notes/chat-sensor.md` (+ A1/A2) — CS-2 (speaker is metadata, never
  provenance); the closed speaker set; the 139-row worked example §13 turns on.
- `docs/design-notes/erratum-relation.md` — E1 (warranted or unrepresentable) as the form
  of "no cross-node erratum authority" (§12); the first frame-discriminating consumer
  (§11); PD-11's missing authority lane.
- `docs/design-notes/agentic-loop.md` — G-C (the class gap, 6,429 rows, `w(a_self)`
  routed here); §2.4b (no stratum per producer; the `EXHAUST` excluded refinement);
  its §5 naming this note the amendment candidate — §§11–12 are that extension.
- `core/kernel/provenance.py` — current home of ρ/MR (the note body's `core/provenance.py`
  citations are the 2026-07-09 path, kept as historical record); `DERIVED_STRATUM`'s
  origin/truth split `:60-66`; the structural-mint precedent `:36-44`. Read 2026-07-27.
