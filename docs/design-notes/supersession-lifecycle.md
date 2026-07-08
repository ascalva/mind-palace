---
type: design-note
id: dn-supersession-lifecycle
status: draft
implementation: partial   # corpus-audit 2026-07 verification
created: 2026-07-04
updated: 2026-07-04
links: []
supersedes: null
superseded_by: null
warrant: null
---

# Supersession Lifecycle — States, Gate, Grounding Maintenance, and Decay

**Status:** DRAFT — pending codebase reconciliation and owner ratification
**Origin:** Design dialogue, July 2026
**Boundary:** Inbound channel — ingestion (semantic layer), dynamics. Governed by
the sacred-boundary principle; the authored active view changes only by the
owner's hand.
**Companion:** `the-edge-model.md` defines supersession as a reasoning path
(statics). This note defines its **dynamics** — proposal, certification, the
authored-content gate, grounding maintenance, and the confidence math each
implies.
**Reconciles with:** `the-edge-model.md`, `dialogue-ingest-and-recursion.md`
(§3–§4), `ingest-identity-and-amendment.md` (§4A), `recursive-strata.md`
(depth, γ^d, budgets, I5/I10).

---

## 1. Recorded order, not detangled

The claim-op store is **append-only with a monotonic op-seq**. Arc order is
**read from the sequence**, never inferred from graph topology. A dialogue has
**intra-dialogue order** (claim → pushback → compromise) and a **position in the
stream**; the extractor stamps intra-dialogue op order, and op-seq is **one total
order consistent with both clocks**. Consequence: `C → C′ → C″` is a *recorded*
sequence regardless of wall-clock gaps between ingests. If anything ever needs to
recover thread order from topology, that is a **missing-sequence bug**, not a
Dreamer task.

*Math.* op-seq is a strict total order `≺` on operations. Within a revision
thread `T` (claims sharing an identity lineage), `≺` restricts to a total order —
`T` is a **chain**, not a partial order to be sorted.

## 2. Two states: proposed → certified

A dreamer-proposed supersession and a verdict-certified supersession are
**different assertions** — a hypothesis reaching for context vs ratified intent.
They are two **states of the same path**:

```
dreamer-proposed  ──(owner verdict)──▶  verdict-certified
```

The transition **is** the verdict event (same shape as the version dispositions).
Audit can therefore distinguish a hypothesis from a ruling; collapsing the states
destroys that distinction. This is the certification-state of `authority` in
`the-edge-model.md` §3.

## 3. The gate — acting on blessed vs unblessed content

The recursion governor prevents derived material from **gaining** authored
authority (I1: promotion by verdict only). It must also prevent derived material
from silently **superseding (hiding)** owner-blessed content — the inverse
direction, previously unguarded. The correct boundary is **blessing**, not
authored-vs-derived, and it lines up with the indexing policy
(`recursive-strata.md` I5 → `security-planes.md` §6: unpromoted `DERIVED_STRATUM`
nodes are not retrievable):

- **Blessed content — authored (K₀) OR promoted-derived** (both retrievable,
  both owner-endorsed): a dialogue supersession does **not** hide it. The
  operation records `attach_defeater(C, D)` **plus** the derived alternative `C′`
  (itself unpromoted, hence not retrievable), and routes a recommendation to the
  verdict-store inbox. `C` **remains in the active projection, flagged
  contested**, until an owner verdict executes the removal. Superseding a
  *promoted* derived claim autonomously would undo an owner promotion without a
  verdict — the same violation as hiding authored content, which is why the line
  is blessing, not stratum.
- **Unblessed content — unpromoted derived** (the Dreamer's own scratch, not
  retrievable): `superseded()` removes it freely. This churn happens entirely in
  the non-retrievable layer and is invisible to retrieval until something is
  promoted, so it needs no gate.

Nothing is blocked except the **silent removal of owner-blessed content**. All
reasoning is still captured autonomously — the defeater and alternative land
immediately, retrieval can down-weight a contested `C`, and the owner gets a
recommendation. This is the Adjudicator / owner-only-promotion pattern applied to
the **demotion** direction, and it composes with I2: *decay* (automatic, gradual,
unrenewed weights) still removes blessed content without a verdict, because decay
is not an assertion that a claim is *wrong* — a dialogue supersession is, so it
takes the gate.

**Disposition provenance.** Every removal-from-active record must carry **which
authority** removed the claim (`owner-verdict` vs `dialogue-op` vs `decay`).
Without it, owner-authorized, dialogue-proposed, and decay removals collapse in
audit — which would defeat the gate.

## 4. Depth, grounding, and the decay envelope (the math)

### 4.1 Two risk terms, already factored as `γ^d · g`; supersession excluded from both
The confidence bound is `c ≤ γ^d · g` (`recursive-strata.md` Invariant 10), and it
already carries **two distinct risk terms** — the reasoning-path work confirms the
factoring rather than adding to it:

- **`γ^d` — recursive-processing / echo-chamber.** `d` is **stratum depth** (I4:
  every derived node carries its stratum depth as data), assigned at mint time by
  which cycle produced the node. A claim that only surfaces after many self-
  synthesis rounds is more heavily damped — the term the echo-chamber threat model
  rests on.
- **`g` — inference-distance / grounding.** The grounding ratio (§6): the fraction
  of a node's cited support that reaches K₀ transitively, versus terminating in
  ungrounded derived nodes. A well-grounded claim has `g → 1`; a tower claim has
  `g → 0`. This is a **separate multiplicative factor**, not a depth term.

Neither term substitutes for the other (`γ^d` misses a shallow-grounded but late
self-referential claim; `g` misses a well-grounded claim that took many rounds to
surface), which is why the bound multiplies them.

**Supersession edges are excluded from both terms.** From `γ^d` trivially — `d` is
a mint-time stratum stamp, not graph-computed. From `g` by design — a supersession
is a dispositional edge (`the-edge-model.md` §4), not "cited support," so the
grounding-ratio walk must skip it. They order and dispose claims; they do not
ground them.

### 4.2 A revision grounds on its warrant's anchors, not on the claim it replaces
`C′` supersedes `C`. `C` is **replaced, not built upon**. Therefore `C′`'s
grounding fibers must reach the anchors its **warrant** actually rests on
(surviving grounding of `C` **+** the dialogue's new evidence), **not** `[C]`
itself. The `C → C′` relationship is carried by the **dispositional supersession
edge**, not by a grounding fiber.

This **corrects the committed `derived_from=[C]`** (Item 2b). Grounding a revision
on the claim it replaces is wrong on two grounds, both now expressed through the
grounding ratio `g`:

1. **It cites as support the very claim it discredits.** `C′`'s warrant is what
   justifies replacing `C`; that warrant reaches the surviving grounds plus the
   dialogue's new evidence — **not** the discredited `C`. Recording `derived_from
   = [C]` makes `C′`'s cited support include the thing `C′` declares wrong.
2. **`g` collapses when `C` is superseded (self-staleness).** The grounding ratio
   is transitive, so `C′` grounded on `C` routes its support *through* `C`; once
   `C` is superseded (removed from active), that path no longer reaches live
   ground and `C′`'s `g` drops. Grounding revision chains this way makes every
   supersession degrade the grounding of the claims downstream of it (§5).

Grounding on the **warrant's K₀-reaching anchors** fixes both: `g` reflects `C′`'s
own support and stays stable across `C`'s supersession. **The "derived cannot
out-rank authored" guarantee is untouched**, because it comes from `γ^{d≥1}` (any
derived claim is damped below any authored claim regardless of `g` or of what it
grounds on), not from grounding on `C`.

*Note on `γ^d` and improvement.* Because `d` is stratum depth, a later revision is
more `γ^d`-damped simply for being later, independent of `derived_from`; the
grounding correction does not change that. Whether a genuinely good deep revision
can escape the depth cap is a promotion question — see §4.5.

*Confirmation needed (builder):* does the grounding-ratio walk currently traverse
dispositional (supersession) edges, and does a claim `supersede` set `derived_from`
to `[C]` or to the warrant's anchors? See Q10.

### 4.3 The confidence envelope
The influence bound is `c ≤ γ^d · g` (`recursive-strata.md` Invariant 10): `γ^d`
damps by stratum depth (monotone decreasing in `d`), and `g ∈ [0,1]` damps by
ungroundedness. A claim is undamped only when it is **both** shallow (small `d`)
**and** well-grounded (`g → 1`); either risk alone pulls the ceiling down. I2
(decay of unrenewed weights) and I3 (bounded strata mass) bound influence further,
over time and in aggregate.

### 4.4 The undulation across strata is the grounding ratio along a thread
A revision thread's nodes sit at **increasing stratum depth** — each revision is
minted a cycle later, so `d` rises monotonically along the thread. What actually
*undulates*, and is the health signal, is the **grounding ratio `g`** (the §6
gauge) read along the thread ordered by op-seq:

- **well-grounded revisions** — each cites K₀-reaching anchors (*grounding* edges,
  unbudgeted): `g` stays high, no tower.
- **predecessor-grounded revisions** — each cites the prior derived claim
  (*cross-stratum* edges, the tightest I5 budget and the file's **tower material**,
  §3): `g` falls; this *is* the tower forming along the thread.

So the `derived_from` correction (§4.2) is, in the file's own terms, a
**tower-prevention** measure: grounding a revision on its warrant's K₀ anchors
turns a would-be cross-stratum citation into a grounding citation — high `g`,
unbudgeted, no tower — whereas `derived_from=[C]` manufactures exactly the
cross-stratum citation the tower is made of. Verdict cadence governs when a
thread's current claim becomes blessed; whether promotion also lifts the `γ^d`
ceiling is §4.5.

**Field-guide clause.** *Measures:* tower formation along a revision thread.
*Instrument:* the existing grounding-ratio gauge (§6), read per-thread. *Falsifier:*
a thread of strictly-improving revisions shows **falling `g`** → the revisions cite
predecessors (cross-stratum) rather than K₀ anchors → `derived_from` is wrong.
(Rising stratum depth along the thread is expected, not a fault.)

### 4.5 Promotion and the depth cap (open)
`d` is stratum depth, immutable at mint (I4); I1 promotion lifts *weight* via
verdict. So a promoted deep revision's confidence is still bounded by `γ^d` unless
promotion also **re-anchors depth** (records the promoted claim at an anchored /
shallow depth). If it does not, a genuinely good insight that took many cycles to
reach stays capped for having been reached late — the "good deep claim" case. The
decision — does a `promote` verdict lift weight *within* the `γ^d·g` ceiling, or
*re-anchor* the claim's depth so the ceiling rises? — sits alongside the file's §10
promotion-mechanics questions, and the supersession loop makes it pressing, because
revision threads are precisely how claims accumulate depth. Flagged, not resolved.
See Q11.

## 5. Grounding maintenance — the one autonomous detangling job

When `C` is superseded at op-seq `t`, claims grounded on `C` during its active
window are now grounded in superseded content — their grounding ratio `g` drops as
their transitive support routes through a dead node, but they are not re-examined.
Define the affected set as `C`'s grounding-descendant closure:

```
Stale(C) = { x : C is reachable from x along grounding fibers }
```

This is the **proactive** complement to the file's grounding-ratio gauge (§6),
which is *detective* — the gauge would show these nodes' `g` falling after the
fact; `Stale(C)` names them at the moment of supersession so the Dreamer can act
before the gauge moves.

These are **flagged for re-examination, not auto-resolved** — whether a derived
claim survives its parent's revision is itself a **semantic judgment**. The
Dreamer, cycle over cycle, revisits `Stale(C)` and **proposes** updated groundings
or retractions, terminating in proposals, never silent edits. This is the closest
thing to the Dreamer "detangling the thread on its own," and it still routes
through the proposal / verdict channel for anything touching blessed content (§3).

**Propagation decision (resolved): flag-for-re-examination.** Alternatives
rejected: *nothing* (grounding rot accumulates silently); *cascade-retract*
(auto-resolves a semantic judgment). Re-entry condition recorded in the build
plan.

*Interaction with §4.2:* grounding revisions on warrant-anchors (not on `[C]`)
keeps revision chains from **self-generating** `Stale` sets — a chain whose links
each ground on their predecessor makes every supersession flag the entire
downstream chain. Another reason for the §4.2 correction.

*Load.* `|Stale(C)|` is the size of `C`'s grounding-descendant closure. Flag
backlog grows with **supersession frequency × grounding fan-out**; this is a
review-load pressure and should be surfaced in the weekly digest.

## 6. Unasserted supersession — surface and sharpen, never certify

If `C` and `D` arrived as independent peers and a dialogue later reveals `D` was a
revision of `C`, the Dreamer sees the **geometry** — proximity, a contradiction
edge, possibly a frustrated triangle — but **cannot certify** the supersession
(intent is not in content). Its job is **candidate-surfacing**.

A supersession **candidate** is a local motif in `E_geom`: a pair `(C, D)` with
high embedding similarity, a contradiction edge, and temporal order (`D` later
than `C`). This **reuses existing instruments** — the signed Laplacian,
frustrated-triangle enumeration, and the (dormant) Ollivier-Ricci curvature —
pointed at a new question; it is **not new machinery**.

*Candidate score (starter):*

```
s(C, D) = sim(C, D) · 1[contradiction(C, D)] · 1[t(D) > t(C)]
          (optionally weighted by local curvature)
```

Recurrence across sleep cycles sharpens a candidate into a stronger
recommendation. **Time surfaces and sharpens; a verdict certifies.**

**A candidate over two authored notes is machine-derived — never an
authored-historical fact.** The complex is authored-only (Invariant 6), so `s(C, D)`
scores pairs of **authored (K₀) notes**: a hit is a machine-inferred "D revises C"
with no owner in the loop. It must therefore route through the §3 blessing gate — the
superseded authored note is demoted **only after an owner verdict**, never silently —
and it must **not** be written to the owner-declared authored-historical `supersede`
store (`the-edge-model.md` §4a). That store's "ungated" property holds only because it
admits no machine source; a machine candidate that reached it would be exactly the
derived-hides-blessed failure §3 guards. Owner authorship (a founding manifest / an
owner CLI) is the *only* ungated writer; the Dreamer surfaces, the owner certifies.

**Falsification experiment** (matches the project's curvature protocol): surface
top-`k` candidates by `s`, blind-adjudicate against similarity- and time-matched
random pairs; the instrument earns its place only if the adjudicated true-revision
rate exceeds the matched control. Re-entry condition inherits the Ollivier-Ricci
gate: Track L shadow runner live + verdict taxonomy ratified.

## 7. Secondary constraints

- **Rename stability.** `doc_id = source_path` forks a version thread on file
  rename (mints a fresh document at seq 1, orphans the old chain; the vector
  layer still dedups on content, but version continuity is lost). Parked: adopt a
  rename-stable identity (front-matter uuid or equivalent) before large corpus
  reorganization; re-entry condition recorded.
- **No-op re-save.** A re-ingest of unchanged bytes logs an **occurrence**
  (`ingest-identity-and-amendment.md` §2), **not** a phantom version; confirm the
  chain is not inflated with non-amendments.

## 8. Reconciliation

Dynamics companion to `the-edge-model.md`; instantiates the operation vocabulary
of `dialogue-ingest-and-recursion.md` §4; depth / γ^d / budgets per
`recursive-strata.md`. Open questions and build items are in the accompanying
builder prompt.
