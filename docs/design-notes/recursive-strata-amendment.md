---
type: design-note
id: dn-recursive-strata-amendment
status: draft
implementation: design-only   # corpus-audit 2026-07 (N/A-design-only)
created: 2026-07-04
updated: 2026-07-04
links: []
supersedes: null
superseded_by: null
warrant: null
---

# Amendment Spec — `recursive-strata.md` (revised against the actual file)

**Status:** DRAFT patch-spec — pending owner ratification
**Origin:** Design dialogue, July 2026 (edge-model / supersession-lifecycle work),
revised after reading the current `recursive-strata.md`.
**What this is:** precise diffs to apply against the existing note, with real
anchors. The note is parked; these are design-capture edits, applied by the
builder after approval — banners on corrections, cross-references on extensions,
no silent rewrite.

---

## 0. Correction to the earlier draft of this spec (read first)

An earlier version of this spec claimed depth might be a single stratum index with
the grounding term **missing**, and recommended "combine two depth terms." **That
was wrong, and is withdrawn.** The file already carries both risks, factored more
cleanly than the earlier proposal:

`c ≤ γ^d · g` (Invariant 10) —
`γ^d` damps by **stratum depth** (I4: every derived node carries its stratum depth
as data) → the recursive-processing / **echo-chamber** term;
`g` is the **grounding ratio** (§6: fraction of cited support reaching K₀) → the
inference-distance term, as a **separate multiplicative factor**, not a depth term.

Nothing is missing. So the reasoning-path work does **not** change the damper. It
only needs to (1) keep supersession edges out of both terms, (2) correct how a
revision's `derived_from` feeds `g`, (3) fix a stale cross-ref, (4) add the
blessing gate, (5) add cross-references. The `supersession-lifecycle.md` note has
been corrected to match `c ≤ γ^d · g`.

---

## 1. Correction — stale cross-ref in I2

The I2 cross-ref currently reads (paraphrased): supersession as an edge type is
introduced in ingest-identity, *built as `SUPERSEDES` in `core/stores/edges.py`*.
That is now **stale**: Item 6 **dropped** `SUPERSEDES` from `core/stores/edges.py`
(with a "don't re-add" note) and moved version history to an append-only version
store (`core/stores/versions.py`), keyed on `(doc_id, version_seq)`. Replace the
built-as clause with:

> supersession is now split into two dispositional edge types in **distinct
> stores** — note-version `supersedes` in the version store
> (`core/stores/versions.py`, Item 6; `SUPERSEDES` was removed from
> `core/stores/edges.py`) and claim-level `supersede` in the claim-op store
> (`core/recursion_ops.py`, Item 2b). Both are dispositional and excluded from the
> balance Laplacian; see `the-edge-model.md`.

This is a **correction** → banner.

## 2. Extension — I5 edge budget covers citation edges, not dispositional edges

The typed `strata.edge_budget` (grounding / lateral / cross-stratum) governs
**citation / support (E_geom) edges** — the edges that feed diffusion, curvature,
and the Laplacian, and whose cross-stratum kind is the tower's building material.
Add:

> The typed edge budget governs **citation (E_geom) edges only**. The dispositional
> supersession edges (note-version `supersedes`, claim `supersede`) live in
> separate stores, do not feed the operator, and are **outside this budget** —
> budgeting them would throttle bookkeeping, not tower formation. A supersession is
> a reasoning path whose **warrant fibers** *are* citation edges and **are**
> budgeted (grounding / lateral / cross-stratum per where each fiber lands). See
> `the-edge-model.md` (E_geom ⊔ E_disp). Consequently a revision that grounds on
> its warrant's K₀ anchors spends *grounding* budget (unbudgeted), while a revision
> that grounds on its predecessor spends *cross-stratum* budget — i.e. builds the
> tower; this is why the `derived_from` correction (§5) is also a tower-prevention
> measure.

This is an **extension** → cross-reference, unless the current edge-budget text
states or implies that *all* edges are budgeted, in which case → banner.

## 3. Addition — the demotion (blessing) gate

The invariants govern promotion (I1: derived weights rise only by verdict) and
decay (I2). They do **not** yet govern **demotion by supersession** — a dialogue
op that removes content from the active projection. Add this, as an extension of
I1 or a short new invariant, cross-referencing `supersession-lifecycle.md` §3:

> **Supersession of blessed content is verdict-gated.** A dialogue supersession may
> freely remove **unpromoted derived** content (the Dreamer's own scratch, not
> retrievable per the indexing policy). It may **not** silently remove **blessed**
> content — **authored (K₀) or promoted-derived**, both retrievable and both
> owner-endorsed. Superseding blessed content records a defeater plus the (unpromoted)
> derived alternative and routes a recommendation to the verdict store; the blessed
> claim stays retrievable, flagged contested, until an owner verdict executes the
> removal. This is I1 applied to the demotion direction: the retrievable view
> changes only by the owner's hand. Decay (I2) is exempt — it is not an assertion
> that a claim is *wrong*; a supersession is.

This closes a gap in the current build (Item 2b's `superseded()` removes from the
active projection without this distinction). → new invariant / I1 extension.

## 4. Cross-references to add

- To `the-edge-model.md` — the E_geom ⊔ E_disp partition and the `L = D − A_geom`
  restriction that keeps dispositional edges out of the operator (the derived
  *citation* edges do feed the operator, down-weighted by `layer_weight` per I3).
- To `supersession-lifecycle.md` — **grounding maintenance** (`Stale(C)` =
  grounding-descendant closure, the proactive complement to the §6 grounding-ratio
  gauge), the **grounding-ratio-along-a-thread** reading of a revision arc (§4.4),
  and **unasserted-supersession candidate surfacing** (§6), which reuses the
  frustration / curvature instruments and is a direct instance of this note's §3
  apophenia / §7 self-generated-drift threat model.

## 5. `derived_from` and the grounding-ratio walk

Two implementation points for the grounding ratio `g` (§6), captured here because
they touch this note's gauge:

- The grounding-ratio walk must **not traverse dispositional (supersession) edges**
  — they are not "cited support."
- A claim `supersede` must set the alternative's `derived_from` to the **warrant's
  K₀-reaching anchors**, not to the superseded claim `[C]` (the committed Item 2b
  value). Grounding on `[C]` makes a revision cite the very claim it discredits and
  makes its `g` collapse when `C` is superseded. See `supersession-lifecycle.md`
  §4.2 and Q10.

## 6. Open decision to add to §10

Add to the §10 unpark decision list:

> Whether a `promote` verdict lifts a derived claim's weight *within* the `γ^d·g`
> ceiling, or **re-anchors its stratum depth** so the ceiling itself rises. `d` is
> immutable at mint (I4), so under the former a genuinely good insight reached late
> stays permanently capped by `γ^d` for having taken many cycles. Revision threads
> (`supersession-lifecycle.md` §4.5) make this pressing, as they are how claims
> accumulate depth.

## 7. For the builder

Apply §1 and §3 as corrections (banners), §2/§4/§5/§6 as extensions
(cross-references), all **only after owner approval**, banner-vs-cross-reference
decided from the current text per repository discipline. Do not silently rewrite
the note. §5 is also an implementation item in the build plan (Q10 / Item 9).
