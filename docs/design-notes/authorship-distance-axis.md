---
type: design-note
id: dn-authorship-distance-axis
status: draft
implementation: design-only   # nothing built; authored post-dates the 2026-07 corpus audit
created: 2026-07-09
updated: 2026-07-09
links:
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

**Origin:** Design dialogue, 2026-07-09.

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

## 1. The axis

Four base classes, ordered by **authorship distance** — the amount of mediation between
the owner and the artifact's content:

| class | name | the owner's relation to the content | current realization |
|---|---|---|---|
| **a₀** | self-authored | produced the content and signed it | `AUTHORED_SOLO`, `AUTHORED_DIALOGUE` (owner's side), verdicts |
| **a₁** | author-initiated | caused the artifact to exist deliberately, without authoring its content wholesale | ingest events, queries, promotion acts — the append-only event log (`ingest-identity-and-amendment.md` §2) |
| **a₂** | author-sensed | an instrument's reading of the owner, not deliberately produced | `OBSERVED` (reserved) — `sensor_readings`, activity exhaust, temporal patterns |
| **a₃** | author-curated | someone else's content; the owner's authorship lives entirely in the selection act | `CURATED` |

Total order: a₀ > a₁ > a₂ > a₃ (nearer = higher). Each step down, the *content* is less
the owner's while the *provenance event* remains fully the owner's — which is exactly why
all four belong in one system about one subject.

**The a₁/a₃ pairing (the selection-event insight).** A curated node decomposes into two
facts at two classes: the content (a₃) and the ingest event that selected it (a₁). The
log/index separation of `ingest-identity-and-amendment.md` §§1–2 already stores these
separately: the event log holds the owner's acts; the derived index holds the content.
The attention-trace — "what the owner chose to read, when, alongside what" — is the a₁
event stream over a₃ content. It exists today; it has simply never been *recognized* as
self-data. This note names it; whether anything reads it is parked (§10, PD-3).

**Edge cases, flagged not resolved:**

- **Dialogue counterparty.** `AUTHORED_DIALOGUE` is defined as *the owner's words only*
  (`core/provenance.py` docstring: "your words to it are more yours than its words to
  you"). The counterparty's words, wherever they land, are at best a₃ (curated by the
  act of conversing) — never a₀. Verify where they actually land (§9, B-4).
- **Dreamer/system output** is not a base class. Derived material takes a *footprint*
  from its support (§3), and `DERIVED_STRATUM`'s reserved semantics already state the
  matching doctrine: trusted as to origin, untrusted as to truth, never confusable with
  authored ground.

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

*(Verification item, not assumption: read the G8 entry at source — companion II / the gap
catalog — and confirm its rationale is the conflation reading and nothing broader. §9, B-1.)*

## 3. Formal core

**(1) The label.** α : V_base → A, A = {a₀ > a₁ > a₂ > a₃}, a bounded chain. For base
nodes α is fixed at mint and immutable — same discipline as ρ today ("ρ is invariant
under derivation; only human promotion re-tags"). For every existing base node α is
**derivable from ρ by the fixed map in §2** — α introduces no new stored fact for base
nodes (§7).

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

## 4. Preserved — the firewall's non-negotiables, restated structurally

Nothing in this section changes. Each is a set-membership constraint, weight-free:

1. **Raw exhaust never enters.** Only interpreted/aggregated a₂ material is
   ingest-eligible; the concentrated raw stream stays outside. Unchanged from both
   firewall notes; the surveillance-dossier reasoning stands.
2. **MR is untouched.** MIRROR_READABLE = {authored-solo, authored-dialogue} — in axis
   terms, the mirror and the §15 baselines / Constitution-conformance read
   **α̂ = a₀ base nodes only**. The self-model never reads a₁–a₃ or any derived
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
- **OQ-2 (unforgeable lineage): inherited, unresolved, blocking.** Now stricter: four
  base classes plus a computed footprint must be unforgeable, not one binary. The known
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
  finding-0022; verify before minting).
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
- **B-4. Dialogue counterparty landing zone.** Where do the Ambassador's words in a
  dialogue physically land, under what ρ? (§1 edge case.) *No falsifier — classification
  input.*
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

## 10. Parked decisions

- **PD-1. Weight vector w values.** Park until Track L is live; w is tuning and Track L
  is the only instrument that can tune it. Default at unpark: w = (1, 1, 0.5, 0.5) as a
  first ansatz, explicitly arbitrary. Re-entry: Track L live + verdict taxonomy ratified.
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

## Open questions

- **OQ-A (blocking, inherited).** Spike OQ-2 / B-3: unforgeable α̂ for derived material
  with out-of-graph supports. The direction fails without it — same kill condition the
  spike recorded, now with four classes at stake.
- **OQ-B.** Does `AUTHORED_DIALOGUE` belong at a₀ without qualification, given the
  counterparty shapes the elicitation? The owner's words are the owner's; the *prompt
  structure* is not. Likely resolution: a₀ with a loss-model annotation
  (elicitation-shaped), not a new class. Owner should weigh personally.
- **OQ-C.** Should promotion be single-step-up only (aᵢ → aᵢ₋₁) or arbitrary-up
  (aᵢ → a₀ direct)? Lean: arbitrary-up with the warrant carrying the burden — the gate
  is the owner's judgment, not the ladder. Settle at verdict-taxonomy ratification.

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
