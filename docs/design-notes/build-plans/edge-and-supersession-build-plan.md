# Build Plan — The Edge Model & Supersession Lifecycle (Items 7–12)

**Status:** IN PROGRESS. Investigation complete + owner-ratified (R5, R3, 2026-07-04). **Items 7 & 9
BUILT and verified** (offline suite green); Items 8, 10, 11, 12 awaiting approval item-by-item.
**Origin:** `docs/builder-prompt-edge-and-supersession.md`, grounded against the committed code.

**Ratified decisions (owner, 2026-07-04):**
- **R5 (founding supersession) — resolved, not the builder's binary.** Founding ingest is *authoring
  content*, not *authorizing a demotion* — two different sacred channels. A K₀↔K₀ founding
  supersession is a **version-relation**, and the bug is *routing*: `core/ingest/founding.py:121-123`
  files it in the **claim**-op store when it should route to the **version** store (Item 6). Founding
  is **not** a fourth authority. The blessing gate applies **only** when a supersession would demote
  an *active, retrievable* K₀ note; establishing the historical chain (v1→v2, v2 active) needs no
  gate. **Folded into Item 8** (routing fix + the active-note-demotion gate); note the wrinkle that
  founding items are distinct `source_paths`, not versions of one `doc_id` — Item 8 designs that.
- **R3 (sequencing) — a HARD dependency edge, not a preference.** *No non-no-op `DialogueAnalyzer`
  merges until Items 8 & 9 are landed and their falsifier tests are green.* Interlocks before
  ignition: the path's inertness is the only thing keeping the two defects latent, and the corruption
  they'd cause lands in derived strata that feed the next sleep cycle (echo-chamber with a head
  start). Enforced as a dependency edge in C.0 below.
**Location note:** the build-plans location already exists —
`docs/design-notes/build-plans/` (holds `sacred-boundary-build-plan.md`). This plan lives beside
it and **continues that plan's item numbering** (prior plan ended at Item 6; parked decisions ran
PD1–PD7). New items are **7–12**; new parked decisions are **PD8+**.

**Reads that ground this plan:** `the-edge-model.md`, `supersession-lifecycle.md`,
`recursive-strata-amendment.md`, `recursive-strata.md`, `the-sacred-boundary.md` §2.3/§4,
`ingest-identity-and-amendment.md` §4A, `dialogue-ingest-and-recursion.md` §3–§4; and the code:
`core/recursion.py`, `core/recursion_ops.py`, `core/stores/{versions,edges,derived,verdicts}.py`,
`core/verdict/dispositions.py`, `core/verdict/taxonomy.py`, `core/ingest/{sync,founding}.py`,
`core/complex/{build,balance,laplacian,curvature,support}.py`, `core/selfcheck.py`,
`core/dreaming/{adjudicator,cluster}.py`, `core/dreams_view.py`, `core/stores/catalog.py`,
`core/provenance.py`, `docs/research/security-planes.md`.

**How to read the state verdicts:** ✅ built as the design wants · ⚠️ partially / by construction ·
❌ absent / diverges. Every current-state claim carries a `path:line` citation.

---

## Part A — Open questions, answered

### Q9 — Confidence-bound terms (the file answers; confirmed in code, with one divergence)

**Claim under test:** the bound is `c ≤ γ^d · g` with `d` = mint-time stratum stamp (echo-chamber
term) and `g` = §6 transitive grounding ratio (inference-distance term); both already present; **no
new depth term**; and two exclusions — (a) `d` is not graph-computed, (b) the grounding walk does
not traverse dispositional edges.

**Finding — the bound and `g`:** ✅. The bound is implemented exactly as `c ≤ γ^d · g`:
`decay_bound(depth, grounding, gamma) = γ^depth · g` (`core/recursion.py:43-53`) and the single
clamped definition `claim_confidence = min{1, γ^d · g · (1 + λ(|Agr|−1))}`
(`core/recursion.py:56-80`). `g` **is** the §6 transitive grounding ratio: the flat form
`grounding_score` = fraction of support refs resolving to authored leaves
(`core/selfcheck.py:152-165`), generalized to the multi-path transitive form
`support_scores`/`grounding_with_support` = mean per-ref noisy-OR strength to authored leaves over
the derivation DAG (`core/complex/support.py:40-64,67-86`). It is applied at the one live callsite,
the adjudicator: `g = grounding_with_support(...)` or `grounding_score(...)`
(`core/dreaming/adjudicator.py:112-113`) fed into `claim_confidence(...)`
(`core/dreaming/adjudicator.py:118`). **There is no missing term and no place a depth term should be
added or swapped** — confirmed, consistent with `recursive-strata-amendment.md` §0.

**Finding — what `d` actually is (the divergence to surface):** ⚠️/❌. The note says `d` is a
**mint-time stratum stamp** (`supersession-lifecycle.md` §4.1; `recursive-strata.md` I4). **The code
has no such stamp.** Two different depth notions exist, neither a stratum stamp:

- **Live path (today):** `d` is a **hard-coded constant** — `AUTHORED_LEAF_DEPTH = 1`
  (`core/dreaming/adjudicator.py:43`), passed to `claim_confidence` at
  `core/dreaming/adjudicator.py:118`, because every R0/R1 claim rests directly on authored leaves so
  depth is uniform (`core/dreaming/adjudicator.py:16-18,40-43`). The recursive path is not live.
- **Recursion path (R3, exists but unwired to confidence):** `DerivedStore.depth(κ)` =
  `1 + max(depth of interpreted parents)`, **computed from the `derived_from` DAG**
  (`core/stores/derived.py:250-265`). This is **derivation depth, graph-computed** — the opposite of
  a mint-time stamp.

So the file's "`d` is a mint-time stamp" is an idealization the code does not implement; the code
uses derivation depth. This matters for the exclusions (below) and is called out as **Risk R1**.

**Exclusion (a) — supersession edges cannot affect `d`:**
- *Today:* ✅ vacuously — `d = 1` is constant (`core/dreaming/adjudicator.py:43,118`), so no edge of
  any kind moves it.
- *Under R3:* ❌ **not yet**, because `d = DerivedStore.depth` reads `derived_from`
  (`core/stores/derived.py:257-265`) **and a claim `supersede` currently writes
  `derived_from=[C]`** (`core/recursion_ops.py:212-213`). So once R3 wires real depth, a supersession
  *would* raise `d` along a revision chain. The exclusion holds structurally **only after Item 9**
  removes `derived_from=[C]` (moving the C→C′ relation entirely to the dispositional
  `ClaimOpStore`). Note the property that actually delivers the exclusion is *"a supersession is not
  in `derived_from`"* — **not** *"`d` is a stamp."*

**Exclusion (b) — the grounding-ratio walk skips dispositional edges:**
- ✅ **structurally at the store boundary:** the walk reads only `refs_of`/`support` = `derived_from`
  (`core/complex/support.py:51-64`, `core/selfcheck.py:163-165`); it holds **no handle** to
  `ClaimOpStore` or `VersionStore`, so a *dispositional* (claim-op / version) supersession edge is
  never traversed.
- ⚠️ **but the supersession is mirrored into `derived_from`:** because `apply_operations` writes
  `derived_from=[C]` (`core/recursion_ops.py:212-213`), `C` sits in `C′`'s citation set and the walk
  **does** traverse the `C′→C` link — as a *citation*, exactly the "supersession recorded as cited
  support" the prompt names as a bug. **Item 9 fixes it.** After Item 9 the walk cannot reach the
  supersession because it lives only in `ClaimOpStore`.

**Verdict:** the file is right about the math (`c ≤ γ^d · g`, two terms, nothing to add). The two
exclusions are **not both structurally true today**; they become true once **Item 9** stops the
claim-`supersede` from writing `derived_from=[C]`. Item 11 is the confirmation/enforcement item and
is **conditional on Item 9**, not independent.

---

### Q10 — Grounding of a revision (correction to committed Item 2b)

**Finding:** ❌ as the note predicts. A claim `supersede` mints the alternative with
**`derived_from=[C]`** — the claim it replaces — not the warrant's anchors:

```python
# core/recursion_ops.py:211-214
if isinstance(op, Supersede):
    art = derived.add(kind=DIALOGUE_CONCLUSION, summary=op.conclusion,
                      subjects=(op.claim,), derived_from=[op.claim])   # ← [C], the bug
    ops_store.record(OpKind.SUPERSEDE, op.claim, related_id=art.id, text=op.warrant)
```

The warrant is recorded only as free text on the op (`text=op.warrant`,
`core/recursion_ops.py:214`); it never becomes grounding. This is exactly the
`supersession-lifecycle.md` §4.2 target: `derived_from` should reach the **warrant's K₀ anchors**
(surviving grounding of `C` + the dialogue's new evidence), and the `C→C′` relation should be
carried **only** by the dispositional edge in `ClaimOpStore`.

Both harms in §4.2 are real against this code:
1. **Cites what it discredits** — `C` enters `C′`'s cited support (`derived_from=[C]`).
2. **`g` collapses / a tower forms** — `g` and `DerivedStore.depth` are transitive
   (`core/complex/support.py:51-64`, `core/stores/derived.py:257-265`). In a chain
   `C(authored) → C′ → C″`, the *second* revision grounds on `C′` which is **derived, not authored**,
   so `grounding_score` counts it 0 (`core/selfcheck.py:163-165`) → `g` falls, and
   `depth(C″) = 1 + depth(C′) = 2` → `γ^d` collapses. That is the §4.4 tower, formed by the
   `derived_from=[C]` rule itself.

**Guarantee preservation (asked explicitly):** ✅ the "derived can't out-rank authored" guarantee is
untouched by the correction, and it comes from `γ^{d≥1}`, not from grounding on `C`. `C′` is minted
through `DerivedStore`, which writes **`INTERPRETED` only, structurally, with no `provenance`
parameter** (`core/stores/derived.py:181-199`). Under the corrected grounding its parents are
authored leaves, so `depth(C′) = 1` (`core/stores/derived.py:263-265`) and `γ^{1} ≤ γ < 1` caps it
below authored ground regardless of `g`. Caveat: `apply_operations` **does not currently call
`claim_confidence` at all** (`core/recursion_ops.py:199-225`) — a dialogue conclusion is minted but
never scored — so the guarantee is *structural* (it is INTERPRETED and would be γ^d-damped when
scored under R3), not yet *numerically applied*.

**Scope note (narrows Item 9):** the `derived_from=[C]` mint is **only** in `apply_operations`
(the dialogue path). The founding-corpus path records its supersede **directly** —
`ops_store.record(OpKind.SUPERSEDE, prior, related_id=record.digest, …)`
(`core/ingest/founding.py:121-123`) — with `related_id` = the new **authored** note's digest and
**no `DerivedStore` mint**, so it does not exhibit this bug. Item 9 targets `apply_operations`.

---

### Q11 — The demotion (blessing) gate

**Finding:** ❌ no gate. `superseded()` returns **every** claim id with a `SUPERSEDE` op, with no
blessed-vs-unblessed distinction:

```python
# core/recursion_ops.py:167-172
def superseded(self) -> set[str]:
    return {r["claim_id"] for r in self._conn.execute(
        "SELECT claim_id FROM claim_ops WHERE kind = ?", [OpKind.SUPERSEDE.value])}
```

`apply_operations` records the supersede unconditionally (`core/recursion_ops.py:211-216`). Nothing
checks whether `C` is authored (K₀), promoted-derived, or unpromoted-derived. So the design's
required gate — *defeater + unpromoted alternative + verdict recommendation, blessed claim stays
contested* (`supersession-lifecycle.md` §3) — is absent.

**Mitigating fact (why it is latent, not yet live):** ⚠️ nothing **consumes** `superseded()` as an
active-projection filter today. The only wired active projection is `DreamsView`, which filters by
`DispositionStore.retracted()` — i.e. **owner verdicts**, not claim-ops
(`core/dreams_view.py:40,56-58`). The claim-op path is also dormant end-to-end because the
`DialogueAnalyzer` default emits **no** operations (`core/recursion_ops.py:102-106`). So no blessed
content is being hidden *right now* — but the moment a real analyzer is wired **and** a consumer
reads `superseded()`, the ungated silent removal becomes live. `core/ingest/founding.py:121-123`
already writes real supersede ops **between two authored (K₀) notes**, so the store contains the
exact records the gate must catch.

**Indexing policy (asked to confirm):** ✅ by construction — "unpromoted `DERIVED_STRATUM` not
retrievable" holds, though the *mechanism* named in the design is not the reason. The label is
reserved (`DERIVED_STRATUM`, `core/provenance.py:54`) and the policy is documented — "Derived
strata: index on promotion. Unverdicted self-generated material must not influence retrieval"
(`docs/research/security-planes.md:106`). In the code, derived artifacts live in the `DerivedStore`
(sqlite), and the librarian retrieves only from the `VectorStore`
(`core/librarian/librarian.py:124,136`); **no path indexes derived artifacts into retrieval at
all** (index-on-promotion is unbuilt). So *unpromoted* derived is non-retrievable — and so is
*promoted* derived, for now. The gate's premise ("the unpromoted alternative isn't retrievable") is
therefore satisfied; the content the gate must protect is **authored (K₀)**, which *is* retrievable
(`VectorStore`), plus promoted-derived once that path exists.

---

### Q12 — Disposition authority

**Finding:** ❌ not uniformly recorded. There is no single removal-from-active record carrying an
authority discriminator `{owner-verdict, dialogue-op, decay}`:

- **owner-verdict:** the `DispositionStore` row carries `verdict_seq`
  (`core/verdict/dispositions.py:57-64,79-87`), so a RETRACT is traceable to a signed owner verdict —
  authority is *implicit* in the store, for verdict-driven removals only.
- **dialogue-op:** `ClaimOpStore` rows carry `op_id, kind, claim_id, related_id, text, at`
  (`core/recursion_ops.py:119-129`) — **no authority column**, and `superseded()` returns bare ids
  (`core/recursion_ops.py:167-172`).
- **decay:** I2 decay-driven removal is **not wired at all** (recursive-strata parked); no record
  exists to tag.

The three live in different stores (or nowhere), so today they are distinguishable *only* by which
store you read — there is no explicit authority field, which is what `supersession-lifecycle.md` §3
("Disposition provenance") requires. Item 8 adds it.

---

### Q13 — Proposed/certified states + candidate surfacing

**Finding — states:** ❌ single type. `OpKind` has only `SUPERSEDE`
(`core/recursion_ops.py:59-62`); the `claim_ops` schema has no state column
(`core/recursion_ops.py:119-129`); a supersede is recorded and *immediately* appears in
`superseded()` (`core/recursion_ops.py:167-172`). There is no `proposed → certified` transition and
therefore no way for audit to distinguish a hypothesis from a ruling (`supersession-lifecycle.md`
§2). The parallel machinery to model it on exists: the verdict→disposition transition
(`core/verdict/dispositions.py`, keyed by `verdict_seq`) is the same shape.

**Finding — candidate surfacing:** ⚠️ instruments available, nothing wired. No `s(C,D)` candidate
scorer or surfacing job exists. But every instrument §6 calls for is built and passing:
- frustrated-triangle enumeration — `frustrated_triangles` (`core/complex/balance.py:77-99`);
- signed-Laplacian dissonance — `signed_spectrum` (`core/complex/balance.py:28-49`);
- curvature bridges — `forman` / `most_negative_edges` (`core/complex/curvature.py:25-43,46-60`);
- Ollivier-Ricci is deliberately **not** implemented — Forman is the floor
  (`core/complex/curvature.py:15-17`).

So Item 10 is an *application* of existing instruments, gated on the Ollivier-Ricci re-entry
condition, exactly as the note frames it.

---

### Q14 — Secondary (rename fork; no-op re-save)

**(a) Rename forks a version thread:** ✅ confirmed. `doc_id` **is** `source_path` — the version
store's `doc_id` is "the catalog source_path" (`core/stores/versions.py:53`), and `VaultSync`
records `version_store.record(source_path, digest)` (`core/ingest/sync.py:111`). A rename changes
`source_path` → a new `doc_id` → `VersionStore.record` allocates `seq = 1` for the "new" document
(`core/stores/versions.py:82-92`), orphaning the old chain. The vector layer still dedups on content
(`index_amendment` keyed by `(source_path, chunk_hash)`), but version continuity is lost — matches
`supersession-lifecycle.md` §7. (Mitigation parked — see **PD10**.)

**(b) No-op re-save does not create a phantom version:** ✅ the important half. The `UNCHANGED`
branch returns **before** `version_store.record` is reached:

```python
# core/ingest/sync.py:88-90,110-111
prev = self.catalog.get(source_path)
if prev is not None and prev.active and prev.digest == digest:
    return SyncOutcome.UNCHANGED           # ← returns here; version_store.record never runs
...
if self.version_store is not None:
    self.version_store.record(source_path, digest)   # only on the INDEXED path
```

So the version chain is not inflated with non-amendments. ⚠️ **but** the positive "logged as an
occurrence" half of `ingest-identity-and-amendment.md` §2 is **not** implemented: `RawStore.add`
merely dedups (`is_new=False`, `core/stores/rawstore.py:28-40`), and the catalog is a **current-state
UPSERT**, not an event log (`ON CONFLICT(source_path) DO UPDATE`, `core/stores/catalog.py:76-87`).
The dedup is real; the occurrence-*event* record is absent. Flagged as **Risk R4** (low severity).

---

### Q15 — Promotion vs depth cap (open decision)

**Finding:** ❌ neither behaviour exists — promotion is parked, so nothing lifts weight *or*
re-anchors depth today:

- the ratified taxonomy has **no** promote verdict; the strata-promotion verdict ("promote insight
  weight") is explicitly deferred to recursive-strata unpark (`core/verdict/taxonomy.py:8-11,16-22`);
- the verdict **apply** half is parked on the promotion mechanism
  (`core/stores/verdicts.py:24-27`);
- `DispositionStore` has an `ENDORSE` effect but its docstring states weight promotion (I1) "stays
  parked, so this is a label, not yet a weight change" (`core/verdict/dispositions.py:36,17-18`);
- `d` in the live confidence path is the constant `AUTHORED_LEAF_DEPTH = 1`
  (`core/dreaming/adjudicator.py:43`); nothing writes a per-node depth that promotion could
  re-anchor.

So Q15 is genuinely **open**: a promoted deep revision would stay capped by `γ^d` because no code
lifts weight within the ceiling *or* re-anchors depth. Recorded as **PD8**, with a default and
re-entry condition, and it belongs in `recursive-strata.md` §10 (amendment §6). Because promotion is
unbuilt, Item 12 is a **decision, not code** — do not change promotion behaviour without
ratification.

---

### A.8 — Additional risks / questions discovered

- **R1 — "stratum stamp" vs derivation depth (documentation ↔ code divergence).**
  `supersession-lifecycle.md` §4.1 and `recursive-strata.md` I4 describe `d` as a mint-time stratum
  stamp carried as node data. The code has no such field: the live path uses a constant
  (`core/dreaming/adjudicator.py:43`) and the recursion path uses graph-computed derivation depth
  (`core/stores/derived.py:250-265`). Neither is a stamp. **Recommendation:** treat derivation depth
  as the operative `d` and reconcile the notes' wording (the exclusion the design wants is delivered
  by "supersession ∉ `derived_from`", Item 9 — not by depth being a stamp). Fold the wording fix into
  the Item 11 acceptance and the `recursive-strata.md` I4 cross-reference; do **not** build a separate
  stratum-stamp field (recursive-strata is parked). Carried as **PD9** if the owner wants it deferred.

- **R2 — Item 7's partition is structural for `L`, but the claim-`supersede` is *not* fully
  partitioned today.** Version-`supersedes` is fully isolated (`VersionStore`, never passed to
  `build_complex`, `core/complex/build.py:106-114`). The claim-`supersede`, however, **mirrors itself
  into `DerivedStore`** via `derived_from=[C]` (`core/recursion_ops.py:212-213`), so it appears as a
  `derives` B-arc in `ReasoningComplex.hyper` (`core/complex/build.py:161`). It does **not** reach
  `A_geom`/`L` (nothing assembles `hyper` into the balance math — see Q-cross-check below), so Item
  7's specific invariant holds; but the dispositional relation is sitting in a derivation store
  mislabeled as a citation. **Item 9 completes the partition** (moves it wholly to `ClaimOpStore`).
  State this dependency explicitly: Item 7's `A_geom` invariant is satisfiable now; the *clean*
  E_disp partition for claim-`supersede` requires Item 9.

- **R3 — the whole dialogue-op path is inert wiring, so the bugs are pre-live.** `apply_operations`
  never scores confidence (`core/recursion_ops.py:199-225`), `superseded()` is unconsumed by any
  view, and the analyzer is a no-op (`core/recursion_ops.py:102-106`). **This is the sequencing
  lever:** Items 8 and 9 must land **before** a real `DialogueAnalyzer` is wired, or the silent
  blessed-content removal (Q11) and the tower-forming `derived_from` (Q10) become live simultaneously.

- **R4 — occurrence event-log absent (Q14b).** Dedup works but the append-only *log of occurrences*
  in `ingest-identity-and-amendment.md` §2 is not built (catalog is current-state,
  `core/stores/catalog.py:76-87`). Low severity; note only. Not in scope for Items 7–12; flag for a
  future ingest-provenance item.

- **R5 — new design question: does an *owner-authored founding* supersession get the blessing gate?**
  `core/ingest/founding.py:121-123` records a claim-`supersede` between two **authored (K₀)** founding
  notes as part of owner-run ingest. That is owner *intent*, but it is **not a signed owner verdict**.
  Under Item 8's gate, superseding blessed content should record a defeater + recommendation and leave
  the claim contested until a verdict — which would mean an owner-authored founding revision does
  **not** immediately take effect. **Question for the owner:** is founding-sequence supersession an
  authority that may hide K₀ directly (a fourth authority, `authored-ingest`), or does it too route
  through the verdict gate? Recommended default: treat it as `dialogue-op` authority (gated) for
  safety, since it enters through the same ingest boundary, not the signed-verdict boundary — but
  flag for ratification (**PD8 companion**, folded into Item 8's authority enum).

**Cross-check backing R2 (what feeds the balance math):** every balance/curvature/clustering consumer
reads `A`/`A_signed` (from the `EdgeStore` overlay) or note centroids — **none reads `hyper`,
`VersionStore`, or `ClaimOpStore`**: `forman(kx.A)` (`core/complex/temporal.py:89`),
`signed_spectrum(kx.A_signed)` (`core/complex/temporal.py:101`, `core/complex/cut.py:120`),
`most_negative_edges(kx.A, …)` (`core/dreaming/interpreters.py:134`), and `cluster_notes` over note
centroids (`core/dreaming/cluster.py:86-123`). `A_signed` is overlaid **only** from the `EdgeStore`
(`core/complex/build.py:127,139-152`), and `EdgeStore` structurally forbids a `supersedes` rel-type
(`core/stores/edges.py:30-33`).

---

## Part B — Reconciliation proposal (proposed diffs — **DO NOT APPLY until approved**)

Banner on a **correction** (existing text is now wrong); cross-reference on an **extension** (existing
text is right but incomplete); never a silent replacement. Decisions below are made against the
**current** text of each file.

### B.1 `recursive-strata.md` — apply `recursive-strata-amendment.md`

**B.1.1 — I2 cross-ref is stale → BANNER + replacement (amendment §1).** Current text
(`recursive-strata.md:45`) still says supersession was built as `SUPERSEDES` in
`core/stores/edges.py`; Item 6 removed it (`core/stores/edges.py:30-33`) and split it into two
dispositional stores.

```diff
  > **Cross-ref (identity & amendment):** `design-notes/ingest-identity-and-amendment.md` gives the
  > structural-layer instantiation — corrections are supersession + re-projection of the derived
  > index, never in-place edits. Decay (I2) and *supersession* are distinct mechanisms: supersession
- > as an edge type is introduced there (built as `SUPERSEDES`, `core/stores/edges.py`), not here.
+ > as a mechanism is introduced there.
+ >
+ > **⚠ Partially superseded (edge-model reconciliation, July 2026).** The clause "built as
+ > `SUPERSEDES`, `core/stores/edges.py`" is **stale**: Item 6 removed `SUPERSEDES` from
+ > `core/stores/edges.py` (with a don't-re-add note) and split supersession into **two dispositional
+ > edge types in distinct stores** — note-version `supersedes` in the version store
+ > (`core/stores/versions.py`, Item 6) and claim-level `supersede` in the claim-op store
+ > (`core/recursion_ops.py`, Item 2b). Both are dispositional and excluded from the balance
+ > Laplacian; see `the-edge-model.md` (E_geom ⊔ E_disp).
```

**B.1.2 — I5 edge budget → CROSS-REFERENCE (amendment §2).** The current edge-budget text
(`recursive-strata.md:54`) is about the three **citation** edge kinds (grounding / lateral /
cross-stratum) and does **not** claim *all* edges are budgeted, so this is an extension, not a
correction. Append after the I5 `strata.edge_budget` bullet:

```diff
+ > **Scope (edge-model reconciliation).** This typed budget governs **citation (E_geom) edges
+ > only** — the edges that feed the operator and whose cross-stratum kind is the tower's material.
+ > The dispositional supersession edges (note-version `supersedes`, claim `supersede`) live in
+ > separate stores, do not feed the operator, and are **outside this budget**. A supersession's
+ > **warrant fibers** *are* citation edges and *are* budgeted (grounding / lateral / cross-stratum
+ > per where each lands). So a revision grounding on its warrant's K₀ anchors spends *grounding*
+ > budget (unbudgeted); one grounding on its predecessor spends *cross-stratum* budget — the tower.
+ > See `the-edge-model.md` and the `derived_from` correction (Item 9).
```

**B.1.3 — the demotion (blessing) gate → NEW invariant (amendment §3).** The invariants govern
promotion (I1, `recursive-strata.md:41`) and decay (I2), not demotion-by-supersession. Add as an
extension of I1 (an addition closing the Item 2b gap, cross-referencing `supersession-lifecycle.md`
§3):

```diff
+ **I1a — Demotion by supersession is blessing-gated.** A dialogue supersession may freely remove
+ **unpromoted derived** content (the Dreamer's own scratch, not retrievable per the indexing
+ policy). It may **not** silently remove **blessed** content — authored (K₀) or promoted-derived,
+ both retrievable, both owner-endorsed. Superseding blessed content records a defeater + the
+ (unpromoted) derived alternative + a verdict-store recommendation; the blessed claim stays
+ retrievable, flagged contested, until an owner verdict executes the removal. This is I1 in the
+ demotion direction: the retrievable view changes only by the owner's hand. Decay (I2) is exempt —
+ it is not an assertion that a claim is *wrong*; a supersession is. See `supersession-lifecycle.md`
+ §3 and Item 8. (Closes the gap in committed Item 2b, whose `superseded()` removed without this
+ distinction — `core/recursion_ops.py:167-172`.)
```

**B.1.4 — cross-references (amendment §4) → CROSS-REFERENCE.** Add to §6 (Gauges) beside the
grounding-ratio gauge, and to the §2 map D cross-ref: pointers to `the-edge-model.md` (E_geom ⊔
E_disp; `L = D − A_geom`) and `supersession-lifecycle.md` (`Stale(C)` grounding-maintenance, the
grounding-ratio-along-a-thread reading §4.4, and unasserted-supersession candidate surfacing §6).
*(Extension; verbatim text per amendment §4.)*

**B.1.5 — `derived_from` + grounding-walk note (amendment §5) → CROSS-REFERENCE + Item 9.** Add a
note to §6 that (i) the grounding-ratio walk must not traverse dispositional edges and (ii) a claim
`supersede` must set `derived_from` to the warrant's K₀ anchors, not `[C]`; cross-reference
`supersession-lifecycle.md` §4.2 and **Item 9**. *(This is also a code item, Part C.)*

**B.1.6 — §10 open decision (amendment §6) → CROSS-REFERENCE.** Add the promotion-vs-depth-cap
decision (Q15 / **PD8**) to the §10 unpark list, verbatim per amendment §6.

**B.1.7 — minor: `core/recursion.py` vs `core/recursion_ops.py` (optional).** The §2 map-D cross-ref
(`recursive-strata.md:23`) attributes the operation vocabulary to "`core/recursion.py`"; the ops
live in `core/recursion_ops.py` (`core/recursion.py` is the γ^d bound). Optional one-word fix; not a
correctness banner.

### B.2 `core/recursion_ops.py` — the `derived_from` correction is a code correction → BANNER on the docstring + code change (Item 9)

The module docstring currently presents `derived_from=[C]` as correct ("`C′` is minted via
`DerivedStore.add(derived_from=[C])`", `core/recursion_ops.py:28-31`; echoed at
`core/recursion_ops.py:205-206,213`). Because the design **corrects** this, the reconciliation is a
banner in the code plus the change itself (not a silent edit). Proposed docstring banner (the code
change is Item 9):

```diff
    * **The conclusion is INTERPRETED.** C′ is minted via `DerivedStore.add(derived_from=[C])`, so
      carries `INTERPRETED` provenance (I5) and a derivation depth, and `core.recursion` bounds its
      confidence by γ^d (I10): a dialogue conclusion can never out-rank the authored claim it revised
      without an owner verdict (I1).
+
+   ⚠ CORRECTION PENDING (edge-model / supersession-lifecycle, Item 9): grounding `C′` on `[C]` is
+   wrong — it cites the very claim it discredits and collapses `g` when `C` is superseded
+   (supersession-lifecycle.md §4.2). C′ must ground on the **warrant's K₀-reaching anchors**; the
+   C→C′ relation is carried by the dispositional ClaimOpStore edge alone. The γ^{d≥1} "can't
+   out-rank authored" guarantee is preserved (it comes from depth ≥ 1, not from grounding on C).
```

### B.3 The three already-reconciled notes (`M` in git status) — CONFIRM, no diff proposed

These were updated when the new notes were authored and already carry the correct cross-references;
**no further change proposed** (verify only):

- `the-sacred-boundary.md` — §2.3 already extends "typed and promotion-gated" onto edges
  (`the-sacred-boundary.md:50-53`) and §5 indexes both new notes
  (`the-sacred-boundary.md:112-119`). ✅
- `ingest-identity-and-amendment.md` — §4A already states Constraints 2–3 are generalized in
  `the-edge-model.md` and points to `supersession-lifecycle.md`
  (`ingest-identity-and-amendment.md:85-87`). ✅
- `dialogue-ingest-and-recursion.md` — §4 already carries the `the-edge-model.md` /
  `supersession-lifecycle.md` pointers **and** the `derived_from=[C]` correction pointer
  (`dialogue-ingest-and-recursion.md:75-81`). ✅

---

## Part C — Build plan (Items 7–12)

### C.0 Ordering, blast radius, and the dependency graph

Respect `the-sacred-boundary.md` §4: **verdict store → close the loop → study.** The verdict store
is already built (`core/stores/verdicts.py`) and its disposition half exists
(`core/verdict/dispositions.py`), so Item 8 has its prerequisite. Phase by blast radius: the
**store-boundary invariant (Item 7)** and the **no-stored-data correction while the analyzer is
no-op (Item 9)** go first; the **gate + states (Item 8)** next; confirmation (Item 11) follows Item
9; instrument (Item 10) and decision (Item 12) are parked/gated.

```
Item 7  (E_geom/E_disp structural invariant; test-only, no behaviour change)
  │  underpins
  ├──────────────► Item 8  (blessing gate + proposed→certified + authority)   ── requires VerdictStore ✅
  │                   │  composes with
  ├──────────────► Item 9  (derived_from = warrant anchors; grounding maint.)  ── sequence BEFORE any real analyzer
  │                   │  enables
  │                   ▼
  ├──────────────► Item 11 (confirm c ≤ γ^d·g exclusions)  ── CONDITIONAL on Item 9 (g exclusion) 
  │
  ├──────────────► Item 10 (unasserted-supersession candidate s(C,D))  ── GATED on Ollivier-Ricci re-entry (parked)
  │
  └── Item 12 (promotion vs depth cap)  ── DECISION only (PD8); no code without ratification
```

**Parallelizable (‖) vs serial (⛓):**
- **Item 7** ‖ — independent, test-only. No dependency edges in.
- **Item 8** ⛓ after Item 7 (invariant) + requires `VerdictStore`/`DispositionStore` (built). ‖ with
  Item 9 *up to* the shared `ClaimOpStore` schema change — coordinate the one migration (see C.8).
- **Item 9** ✅ BUILT. ⛓ after Item 7; **HARD EDGE (R3, ratified):** no non-no-op `DialogueAnalyzer`
  merges until Items 8 **and** 9 are landed with green falsifier tests. Item 9 is landed; **Item 8 is
  the remaining gate on wiring any real analyzer.** ‖ with Item 8 except the shared schema.
- **Item 11** ⛓ after Item 9 (the `g`-exclusion acceptance cannot pass until `derived_from=[C]` is
  gone). ‖ with Item 8.
- **Item 10** ⛓ gated (parked) on the Ollivier-Ricci re-entry condition.
- **Item 12** ‖ (decision), independent; do not implement.

---

### Item 7 — Edge assertion-authority typing + structural `E_geom`/`E_disp` partition
**✅ BUILT & VERIFIED (2026-07-04). ‖ parallelizable. Touches stored data: NO.**

> **Built.** Strengthened the partition invariant at `core/complex/build.py:_overlay_signed` (the one
> place `A_signed` is assembled — states E_geom ⊔ E_disp explicitly, cites the-edge-model.md §4 and
> the regression test). Realized the "authority typing" as the **structural store-separation
> invariant** (the honest form: an edge's authority *is* which store it lives in) rather than a dead
> enum — deferred a branched-on `EdgeAuthority` type until a consumer needs one, to avoid speculative
> scaffolding. `tests/integration/test_edge_partition.py` (new, 2 tests): frustration + Forman
> curvature + clustering are bit-identical after adding a `VersionStore` row **and** a `ClaimOpStore`
> supersede over the same authored nodes; and `build_complex`'s signature admits no dispositional
> store. All green.

**What.** Make the E_geom ⊔ E_disp partition an explicit, tested **invariant** rather than an
emergent property. Introduce the `authority ∈ {geometry, dreamer-proposed, verdict-certified}` typing
from `the-edge-model.md` §3 as the vocabulary; assert structurally that **no dispositional edge is
ever assembled into `A_geom`/`A_signed`/`L`**. This is already true at the store boundary
(`VersionStore`/`ClaimOpStore` are never passed to `build_complex`, `core/complex/build.py:106-114`;
`EdgeStore` forbids `supersedes`, `core/stores/edges.py:30-33`) — Item 7 pins it with a regression
test and a stated invariant so a future consumer cannot silently break it.

**Files.**
- `core/complex/build.py` — a comment-level invariant at `_overlay_signed`
  (`core/complex/build.py:139-152`): "only `EdgeStore` (`authority=geometry`) edges enter
  `A_signed`." Optionally record `authority` on `Edge` (`core/stores/edges.py`) as a non-behavioural
  provenance column (default `geometry`) so the taxonomy is legible — **no** consumer branches on it.
- `tests/complex/test_edge_partition.py` (new) — the invariant test below.

**Acceptance test.** Build a complex; compute `frustration`, `signed_spectrum`,
`frustrated_triangles`, `forman`/`most_negative_edges`, and `cluster_notes`. Then add a
`VersionStore` supersession row **and** a `ClaimOpStore` supersede op referencing the same nodes;
rebuild; recompute. **All five results are bit-identical.**

**Falsifier.** Any of the five changes when a dispositional edge is added/removed → `E_disp` has
leaked into `A_geom` → fix at the store boundary, not with a per-consumer rel-type filter.

**Invariants it must not violate.** Invariant 6 (authored-only complex); the store separation of §4A
C2–C3. **Note (R2):** this item's invariant is about `A_geom`/`L`. The claim-`supersede`'s
`derived_from=[C]` still contaminates `hyper` until **Item 9**; Item 7 does not claim otherwise —
its acceptance targets the balance-math results, which do not read `hyper`.

---

### Item 8 — Supersession lifecycle: blessing gate + proposed→certified + disposition authority
**⛓ after Item 7; requires `VerdictStore` (built ✅). ‖ with Item 9 except shared schema. Touches
stored data: YES — new columns on `claim_ops`; reuses `DispositionStore`.**

**What.** Three coupled changes from `supersession-lifecycle.md` §2–§3:

1. **Blessing gate (Q11).** In `apply_operations`, branch a `Supersede` on the target's blessing
   status: **blessed** (authored K₀ — resolvable in the `MirrorView`/catalog — or promoted-derived)
   ⇒ do **not** remove; instead record `attach_defeater(C, D)` + mint the unpromoted derived
   alternative `C′` + route a recommendation to the verdict-store inbox, leaving `C` **contested,
   still retrievable**. **Unblessed** (unpromoted derived) ⇒ `superseded()` removal stays free.
2. **`proposed → certified` states (Q13).** Add a `state ∈ {proposed, certified}` column to
   `claim_ops`; a dreamer/dialogue supersede lands `proposed`; the `proposed → certified` transition
   **is** an owner-verdict event, applied through the existing `VerdictStore` →
   `DispositionStore.record(subject, RETRACT, verdict_seq)` path (`core/verdict/dispositions.py:79-87`).
   `superseded()` returns only `certified` (or free-unblessed) removals.
3. **Disposition authority (Q12).** Every removal-from-active record carries
   `authority ∈ {owner-verdict, dialogue-op, decay}`. `owner-verdict` = a `DispositionStore` RETRACT
   (has `verdict_seq`); `dialogue-op` = a free unblessed `ClaimOpStore` removal; `decay` reserved for
   I2 (parked). Provide one read that unions these with the authority tag for audit.

**Files.** `core/recursion_ops.py` (gate in `apply_operations`; `state` column + `superseded()`
filter; authority tag), `core/verdict/dispositions.py` (reuse for the certified transition), a new
active-projection reader (or extend `DreamsView`/the MirrorView filter) that consumes
`certified`-only supersessions, plus tests.

**Acceptance.** (a) No blessed claim (authored **or** promoted-derived) leaves the active projection
without an owner verdict — superseding a blessed `C` yields a defeater + unpromoted `C′` +
recommendation, and `C` is still retrievable and flagged contested. (b) Superseding an unpromoted
derived claim is still free (no verdict required). (c) The `proposed → certified` transition **is** a
verdict event (a `DispositionStore` row with `verdict_seq`). (d) Every removal record names its
authority.

**Falsifier.** A blessed claim disappears from retrieval after a `Supersede` with no corresponding
`VerdictStore`/`DispositionStore` row → the gate is bypassed. An audit query cannot tell an
owner-verdict removal from a dialogue-op removal → the authority tag is missing.

**Invariants.** I1 (promotion by verdict only) in the demotion direction (new I1a); §4A C3 (distinct
stores). Leans on the indexing policy (unpromoted derived not retrievable — holds by construction,
Q11) so the unpromoted alternative is safe to mint immediately.

**Sub-item 8f — founding routing fix (R5; taxonomy RESOLVED; ✅ BUILT & VERIFIED 2026-07-04).**
Re-route K₀↔K₀ founding supersessions off the **claim-op store**.

> **Built.** `core/stores/authored_supersession.py` — `AuthoredSupersessionStore` (append-only,
> keyed on the two authored digests; `superseded()` active-projection filter), **owner-declared only,
> structurally fail-closed**: `record(..., declaration)` verifies an `OwnerDeclaration` (construction-
> guarded via `_OWNER_TOKEN`) at its own boundary and raises `MachineAuthorityRefused` for any other
> value. `core/ingest/founding.py` rerouted to it (mints `owner_declaration()`; no longer imports
> `ClaimOpStore`). Acceptance met: (1) founding writes the authored-historical edge, **no claim-op row**
> (founding can't even construct one); (2) **structural negative test** — a simulated dreamer/scheduler
> caller (bad `declaration`) is rejected at the boundary (`test_authored_supersession.py`). Full offline
> 722 passed; ruff clean; seal green. (3) — the active-projection *consumer* of `superseded()` is the
> remaining Item-8 gate work; nothing demotes from retrieval yet.

*The one-line test — does the edge connect two versions of one document, or two documents?* A founding
`supersede(A, B)` has `A`, `B` at **different `source_paths`** (`founding.py:114-123`: `prior` and
`record.digest` are two distinct authored notes). So it connects **two documents** → it is **not** a
note-version `supersedes`; and it carries **no warrant, no reasoning act, mints no derived
alternative** → it is **not** a claim-`supersede`. It is a **third thing: an authored-historical
supersession** — both endpoints K₀, both persist in the log, **dispositional** (E_disp, structurally
excluded from the balance math), **owner-authority** (asserted at *authoring* time, which *is* the
owner's hand, so it needs no verdict gate to establish the historical chain).

**Decision (recorded, PD11): option (b) — its own authored-historical dispositional edge type**, a
third E_disp member distinct from note-version `supersedes` and claim `supersede` (documented in
`the-edge-model.md` §4–§5).
- **Rejected — option (a), reuse the version store as-is.** Its `PRIMARY KEY (doc_id, version_seq)`
  keys versions of **one** `source_path` and derives supersession from consecutive `version_seq`
  *within one `doc_id`* (`core/stores/versions.py:57,99-103`); it **cannot** represent a
  cross-`source_path` relation. Confirmed unkeyable, not merely awkward.
- **Rejected — synthesize a shared `doc_id`** for a founding revision pair to force it into the
  version key. A fabricated identity is the same failure family as content-digest-as-version-key
  (`ingest-identity-and-amendment.md` §4A C1) and will surface as corruption later. **Do not.**

*Gate scope — settled 2026-07-04 (the machine-derivation question).* The "ungated" property is **not
intrinsic to the edge type**; it holds **only for owner-declared** assertions. Investigation:
`FoundingItem.supersedes` is an owner-authored manifest field (`scripts/ingest_founding.py:33-34`,
`core/ingest/founding.py:56-66`), and the only two supersession writers today are `founding.py:122`
(owner-declared) and the inert dialogue path (`recursion_ops.py:278`). **But a supersession between
two authored notes CAN be machine-derived by design** — Item 10's `s(C,D)` scorer runs over authored
`E_geom` (`supersession-lifecycle.md` §6), and the curator's near-duplicate finder pairs authored
notes (`core/curator/curator.py:86-101`); both propose "B revises A" with no owner in the loop. A
machine-derived edge demoting an *active, retrievable* K₀ note is derived material silently hiding
blessed content — the I1a failure.

**Write-path invariant (bake into Item 8).** The authored-historical store is **owner-declared only**
— its write-path admits **no** model / scheduler / dreamer source (fail-closed), so ungated-ness holds
*by construction* (capability-dissolution, `the-sacred-boundary.md` §3). Owner-declared assertions
(founding manifest / an owner CLI) are ungated, **including** active-note demotion (the owner's
explicit hand). A machine-inferred authored↔authored supersession does **not** enter this store: it is
a **dreamer-proposed candidate** routed through the proposed→certified blessing gate (Item 8 core),
demoting an active retrievable note **only after an owner verdict**. *Rejected:* let the store hold
machine-derived edges behind an `asserted_by` flag — that puts gating logic + a forgeable authority
discriminator *inside* the "ungated" store (the per-consumer-filter discipline the E_disp partition
dissolves); owner-declared-only **removes** the machine-write capability instead of guarding it.

*Safe to defer to implementation:* `founding.py:121`'s current claim-op records are **inert** —
`ClaimOpStore.superseded()` has **no consumer** (grep), and the wired active projection filters on
`DispositionStore.retracted` (owner verdicts) only (`core/dreams_view.py:56-58`), so nothing is hidden
today. **Implementation is Item 8/8f, next session** (owner-declared-only authored-historical store
keyed on the two authored digests + re-route `founding.py`; machine candidates stay in the gated
lifecycle). *Acceptance (at implementation):* (1) a founding K₀↔K₀ supersession leaves **no
`ClaimOpStore` row** and records an owner-declared authored-historical edge; (2) **the store REFUSES
machine authority at its own boundary — a structural negative test.** Assert the negative directly: a
supersession submitted through a *simulated dreamer/scheduler caller* (i.e. `record()` called without a
valid owner-authority capability — `None`, a forged object, or a would-be direct construction) is
**rejected by the store** (raises), **not** merely "no machine path is currently wired to call it."
Fail-closed-by-source is only as strong as the store's ability to check its caller's authority — a
shared helper / batch tool / refactor that routes an owner call and a dreamer call through one function
collapses a source-only rule; the store must therefore *check-and-reject at its own boundary* so the
guarantee survives a careless future caller (the point of capability-dissolution over a flag). (3) no
active retrievable K₀ note leaves the projection except by owner-declared authorship **or** an owner
verdict.

---

### Item 9 — Revision-grounding correction + grounding maintenance
**✅ BUILT & VERIFIED (2026-07-04). ⛓ after Item 7; MUST precede any real `DialogueAnalyzer` (R3).
Touches stored data: NO new rows while the analyzer is no-op.**

> **Built.** `core/recursion_ops.py`: (1) `Supersede` gains `anchors: tuple[str,...] = ()` (the
> warrant's K₀-reaching authored digests); `apply_operations` now mints C′ with
> `derived_from = op.anchors`, or — when empty — a fallback **scoped by C's type** (Part 1
> correction, `DerivedStore.is_artifact`): a **derived** C inherits its `leaf_refs` (**never `[C]`**,
> which decays); an **authored** (K₀) C grounds on `[C]` itself (bedrock — does not decay, g=1, so
> the revision is **not weightless**). The naive "never `[C]`" fallback produced `g=0`/`c=0` for an
> authored-note rephrase (a silent "blessed content vanishes" bug — scratch-confirmed and fixed). The
> C→C′ relation is carried by the `ClaimOpStore` edge alone. (2) `stale_closure(derived, claim)`
> computes `Stale(C)` (the
> grounding-descendant closure over `derived_from`); `ApplyReport` gains a `stale` field surfacing the
> flagged-for-re-examination set (never cascade-retracted). Docstrings corrected per Part B.2.
> **Verified** by five new tests in `tests/integration/test_dialogue_ops.py`: grounds-on-anchors-
> not-claim; the §4.4 no-tower falsifier (flat depth + flat `g` along a warrant-anchored thread, with
> the predecessor-grounded negative control that towers to depth 2 / `g`=0); default-anchors-inherit-
> surviving-grounding-never-the-claim; γ^{d≥1} guarantee preserved; and `Stale(C)` = the
> grounding-descendant closure that a well-formed revision does **not** self-generate. All green.

**What.** Two changes from `supersession-lifecycle.md` §4.2 and §5:

1. **Re-ground the revision (corrects committed Item 2b).** In `apply_operations`
   (`core/recursion_ops.py:211-214`), mint `C′` with `derived_from =` the **warrant's K₀-reaching
   anchors** (surviving grounding of `C` + the dialogue's new evidence), **not** `[C]`. Carry the
   `C→C′` relation **only** on the dispositional `ClaimOpStore` edge. This simultaneously fixes Q10
   (grounding), the Q9(b) walk-traversal leak, and the R2 `hyper` contamination.
2. **Grounding maintenance — `Stale(C)`.** On supersession of `C`, compute
   `Stale(C) = { x : C is reachable from x along grounding fibers }` — the grounding-descendant
   closure over `derived_from` (a directed-reachability query on the `DerivedStore` DAG, the inverse
   of `leaf_refs`/`support_scores`, `core/stores/derived.py:267-283`, `core/complex/support.py:40-64`).
   **Flag** those nodes for re-examination (do **not** cascade-retract); a Dreamer
   grounding-maintenance pass emits **proposals** (never silent edits), routed through the Item 8
   gate for anything blessed. Surface `|Stale(C)|` in the weekly digest.

**Acceptance / falsifier (the §4.4 tower diagnostic).** Along a revision thread ordered by op-seq, a
sequence of **strictly-improving** revisions must **not** show a **falling** grounding ratio `g`
(computed by `grounding_with_support`, `core/complex/support.py:67-86`). Construct `C(authored) → C′
→ C″` where each cites the warrant's authored anchors: assert `g(C′) = g(C″) = 1.0` and
`depth = 1` for each. Then the pre-fix control (`derived_from=[C]`) must **fail** it: `g(C″) < 1` and
`depth(C″) = 2` (`core/selfcheck.py:163-165`, `core/stores/derived.py:263-265`). Falling `g` along
improving revisions ⇒ the revisions cite predecessors (cross-stratum) ⇒ `derived_from` is wrong.
Separately: `Stale(C)` equals the grounding-descendant closure; maintenance emits proposals, never
silent edits (assert no `DerivedStore`/active-projection mutation without a proposal record).

**Guarantee test.** After the correction, `C′` is INTERPRETED (`core/stores/derived.py:181-199`) with
`depth ≥ 1`, so `γ^{d≥1} < 1` still caps it below authored — assert `decay_bound(depth(C′)) < 1`
(`core/recursion.py:43-53`). The guarantee does **not** depend on `derived_from` being `[C]`.

**Invariants.** Acyclicity of the derivation DAG (`DerivedStore._guard_acyclic`,
`core/stores/derived.py:232-248`) — warrant anchors are authored leaves, so no cycle risk; I10
(`c ≤ γ^d·g`). Also update the `core/recursion_ops.py` docstring per **B.2**.

---

### Item 10 — Unasserted-supersession candidate surfacing (instrument)
**⛓ GATED (parked) on the Ollivier-Ricci re-entry condition. Touches stored data: NO (read-only
instrument + an eval harness).**

**What.** As an **application of existing instruments** (signed Laplacian, frustrated triangles,
Forman/Ollivier-Ricci curvature — `core/complex/balance.py`, `core/complex/curvature.py`), implement
the candidate score
`s(C, D) = sim(C, D) · 1[contradiction(C, D)] · 1[t(D) > t(C)]` (optionally curvature-weighted),
surface top-`k` candidates, and run the blind-adjudication falsification experiment
(`supersession-lifecycle.md` §6): the instrument earns its place only if the adjudicated true-revision
rate exceeds similarity/time-matched random controls.

**Gate.** Re-entry inherits the Ollivier-Ricci condition — **Track L shadow runner live + verdict
taxonomy ratified**. If unmet at build time, **record as parked (PD-linked), do not build now.**

**Acceptance (when un-gated).** True-revision rate on top-`k` by `s` strictly exceeds the matched
control in blind adjudication. **Falsifier.** No lift over control ⇒ the motif does not indicate
revision ⇒ drop the instrument. **Invariants.** Time surfaces/sharpens; only a verdict certifies
(the Item 8 gate still owns certification).

---

### Item 11 — Confidence-bound confirmation + exclusions
**⛓ CONDITIONAL on Item 9 (the `g` exclusion). Touches stored data: NO (assertions/tests; possible
I4 wording reconciliation).**

**What.** The bound is **already** `c ≤ γ^d · g` — `γ^d` (depth, echo-chamber) × `g` (grounding,
inference-distance). **No new depth term; no swap** (`recursive-strata-amendment.md` §0; Q9). Verify
both are wired (`core/recursion.py:43-80`; `core/dreaming/adjudicator.py:112-118`;
`core/complex/support.py:67-86`) and enforce the two exclusions: `d` is not moved by a dispositional
edge, and the grounding walk skips dispositional edges. Per **R1**, reconcile the "stratum stamp"
wording: the operative `d` is derivation depth; the exclusion is delivered by "supersession ∉
`derived_from`" (Item 9), not by a stamp.

**Acceptance.** Adding or removing a dispositional edge (a `ClaimOpStore` supersede / `VersionStore`
row) changes **neither `d` nor `g`** for any node. *This passes only after Item 9* — pre-Item-9, a
superseded claim's revision has `C ∈ derived_from`, so both `d` and `g` move (Q9/Q10). Include the
pre-fix negative control as a guard that the test is real.

**Falsifier.** A dispositional edge shifts `d` or `g` after Item 9 ⇒ the supersession is still being
recorded as citation somewhere (re-check `apply_operations` and any other `derived.add` caller).

**Invariants.** I10; the E_geom ⊔ E_disp partition (Item 7).

---

### Item 12 — Promotion vs depth cap (open decision; **park**)
**‖ decision only. Touches stored data: NO. Do not implement without owner ratification.**

**What.** Resolve Q15: does a `promote` verdict lift a derived claim's weight *within* the `γ^d·g`
ceiling, or **re-anchor its stratum depth** so the ceiling rises? Promotion is unbuilt today
(`core/verdict/taxonomy.py:8-11`; `core/stores/verdicts.py:24-27`;
`core/verdict/dispositions.py:36`), so this is a decision, not code. Record in `recursive-strata.md`
§10 (amendment §6) with the default + re-entry below (**PD8**).

---

### C.7 — The math carried into the plan (with field-guide clauses)

- **`L = D − A_geom`, restricted to `E_geom` (Item 7).** `A_geom[u,v] = Σ sign·weight` over geometry
  edges only; `L = D − A_geom`, `D = diag(Σ|A_geom|)` (`core/complex/laplacian.py:46-53`,
  `core/complex/build.py:127`). Derived **citation** edges *are* in the operator via the hypergraph,
  down-weighted by `layer_weight` (I3); **dispositional** edges are excluded.
  *Field-guide (the-edge-model §4): Measures the semantic-tension structure of the current claims;
  valid when `E_geom` holds only observer-independent relations; falsifier — adding/removing a
  dispositional edge changes any clustering/frustration/curvature result.*

- **`c ≤ γ^d · g` with `d` = depth, `g` = transitive grounding, both excluding dispositional edges
  (Item 11).** `decay_bound = γ^d·g` (`core/recursion.py:43-53`); `g` = mean per-ref transitive
  strength to authored leaves (`core/complex/support.py:67-86`). `d` excludes supersession because
  supersession ∉ `derived_from` (post-Item-9); `g` excludes it for the same reason.
  *Field-guide (supersession-lifecycle §4.1): γ^d is the echo-chamber term (depth), g the
  inference-distance term (grounding); neither substitutes for the other, so the bound multiplies
  them; a supersession orders/disposes claims, it does not ground them.*

- **Grounding-ratio-along-a-thread = the tower/undulation diagnostic (Item 9 falsifier).** Read `g`
  per-thread ordered by op-seq: high & flat = well-grounded (K₀-cited, unbudgeted); falling = tower
  (predecessor-cited, cross-stratum).
  *Field-guide (supersession-lifecycle §4.4): rising stratum depth along the thread is expected;
  falling `g` along strictly-improving revisions means `derived_from` is wrong.*

- **`Stale(C)` closure and backlog (Item 9).** `Stale(C) = {x : C reachable from x along grounding
  fibers}`; the proactive complement to the detective grounding gauge; load grows with
  supersession-frequency × grounding fan-out; surface `|Stale(C)|` in the digest.

- **Candidate score `s(C,D)` + adjudication experiment (Item 10).**
  `s(C,D) = sim(C,D)·1[contradiction]·1[t(D)>t(C)]`; blind-adjudicate top-`k` vs matched controls;
  keep only if true-revision rate beats control.

---

### C.8 — Shared-schema coordination note

Items 8 and 9 both touch `claim_ops` / `apply_operations` (`core/recursion_ops.py`). Item 8 adds a
`state` column (+ authority) and the gate branch; Item 9 changes the `derived.add(derived_from=…)`
argument and adds the `Stale(C)` computation. **Land the `claim_ops` schema change once** (a single
additive migration — new nullable columns, no rewrite; the store is append-only,
`core/recursion_ops.py:142-165`), then apply the two behavioural changes. Because the analyzer is a
no-op (R3), neither item mutates existing stored rows on delivery.

---

## Parked-decision records (protocol: default · rejected alternatives + reasons · re-entry)

**PD8 — Promotion vs depth cap (Q15 / Item 12).**
*Default:* **PARK**; keep promotion lifting **weight within** the `γ^d·g` ceiling (do not re-anchor
depth), and record the "good deep claim stays capped" limitation in `recursive-strata.md` §10.
*Rejected:* (a) *re-anchor depth on promote* — lets an owner verdict rewrite the echo-chamber term,
coupling promotion to the depth model before either is calibrated; (b) *raise γ on promote* — a
global change masquerading as a local one. *Re-entry:* recursive-strata unpark (L4 adoption
criterion met) **and** the strata-promotion verdict is added to the taxonomy
(`core/verdict/taxonomy.py:8-11`). *Companion (R5):* fix the founding-supersession authority
(`authored-ingest` vs gated `dialogue-op`) as part of Item 8; default gated.

**PD9 — "Stratum stamp" vs derivation depth wording (R1).**
*Default:* adopt **derivation depth** (`DerivedStore.depth`, `core/stores/derived.py:250-265`) as the
operative `d`; reconcile `recursive-strata.md` I4 / `supersession-lifecycle.md` §4.1 wording to say
so; **do not** build a separate stratum-stamp field. *Rejected:* build the stamp now — recursive-
strata is parked and the graph-computed depth already delivers the exclusion (via Item 9). *Re-entry:*
if R3 wiring shows derivation depth and stratum depth must differ (e.g. cross-cycle re-derivation),
revisit at recursive-strata unpark.

**PD10 — Rename-stable document identity (Q14a).**
*Default:* **PARK**; `doc_id = source_path` (`core/stores/versions.py:53`) forks a version thread on
rename. *Rejected:* migrate to a front-matter UUID now — a foundational identity change to coordinate
with provenance-migration `--apply`, not worth it pre-corpus-reorg. *Re-entry:* before any large
corpus reorganization/rename campaign; adopt a rename-stable id (front-matter uuid or per-doc
surrogate) then.

**PD11 — Founding K₀↔K₀ supersession taxonomy (R5 / Item 8 sub-item 8f). RESOLVED 2026-07-04.**
*Decision:* **option (b) — its own authored-historical dispositional edge type**, a third E_disp
member distinct from note-version `supersedes` and claim `supersede`. *Rejected (a):* reuse the
version store — `PRIMARY KEY (doc_id, version_seq)` cannot key a cross-`source_path` relation
(`core/stores/versions.py:57,99-103`), confirmed unkeyable. *Rejected:* synthesize a shared `doc_id`
to force the version key — a fabricated identity, same failure family as content-digest-as-version-key
(`ingest-identity-and-amendment.md` §4A C1). *Properties:* both endpoints K₀; dispositional (excluded
from balance math). **Ungated only when owner-declared (settled 2026-07-04).** Investigation confirmed
`FoundingItem.supersedes` is an owner-authored manifest field (`scripts/ingest_founding.py:33-34`), but
a supersession between two authored notes **can be machine-derived** (Item 10 `s(C,D)` over authored
`E_geom`; the curator near-duplicate finder, `core/curator/curator.py:86-101`), so ungated-ness is a
property of the **authority, not the edge type**. **Write-path invariant:** the store is
**owner-declared only** (fail-closed on any model/scheduler/dreamer source) ⇒ ungated by construction,
including active-note demotion (the owner's explicit hand); a machine-inferred authored↔authored
supersession is a **dreamer-proposed candidate** through the Item 8 blessing gate, demoting an active
note only after an owner verdict. *Rejected:* hold machine-derived edges behind an `asserted_by` flag
(gating logic + forgeable authority inside the "ungated" store). *Implementation:* Item 8/8f, next
session (owner-declared-only store keyed on the two authored digests + re-route `founding.py:121`; safe
to defer — the current claim-op records are inert, no `superseded()` consumer). Documented
`the-edge-model.md` §4a/§5.

**Resolved (recorded, not open) — grounding-maintenance propagation (Item 9 / supersession-lifecycle
§5).** **Flag-for-re-examination**, not cascade. *Rejected:* *nothing* (grounding rot accumulates
silently) and *cascade-retract* (auto-resolves a semantic judgment). *Re-entry:* if the `|Stale(C)|`
digest backlog outgrows owner review capacity, revisit a bounded auto-proposal budget — still
proposal-terminating, never silent.

**Resolved (recorded, not open) — authored-vs-derived grounding fallback (Item 9 / Part 1, 2026-07-04).**
A `supersede` with no explicit anchors grounds C′ by C's type: **derived** C → inherit `leaf_refs(C)`,
never `[C]`; **authored** C → `[C]` (bedrock, g=1). *Rejected:* the uniform "never `[C]`" rule — it
made an authored-note rephrase weightless (`g=0`, scratch-confirmed), a silent blessed-content-vanishes
bug. The `[C]` prohibition targets grounding through content that **decays or is superseded without a
verdict** — an authored C does neither.

---

## Status / next

Investigation + owner ratification complete. **Items 7 & 9 are BUILT and verified** (offline suite
714 passed / 7 skipped, ruff clean, seal green; no model tier or sandbox touched, so live gate N/A);
**not committed.** The recommended first cut (7 ‖ 9) is done. **Next: Item 8** (blessing gate +
proposed→certified + disposition authority + the R5 founding-routing sub-item) — the remaining hard
gate before any real `DialogueAnalyzer` (R3). Then **Item 11** (confirmation, now unblocked by 9).
**Item 10** parked on the Ollivier-Ricci gate; **Item 12** parked as **PD8**. Per build discipline,
Item 8 is a fresh session — resume from `docs/PROGRESS.md`.
