# bp-152 — journal

## Pre-build notes for whoever picks this up

- ⚑⚑ **The C1 trap is the reason this plan exists — read D2 step 4 twice.** Re-landing is
  idempotent **because currency reconciliation converges**, NOT because the call
  short-circuits. The first draft's "existing fiber ⇒ no-op" is the bug: on A→B→A the fiber
  for blob A already exists with `current=false`, so a short-circuit leaves **B** current —
  silent corruption. **Step 4 runs even when step 3 was a no-op.** The repo already learned
  this once: `core/stores/versions.py:22-27` documents content-keyed identity failing on a
  revert. Do not learn it twice.

- ⚑⚑ **The atom side dedups; the membership side must NOT.** `code_rows` currently collapses
  duplicates via `by_id.setdefault(rid, row)` (`core/ingest/code_corpus.py:229`). That
  collapse is correct for atoms and **wrong for memberships**: two byte-identical L0b windows
  in one blob are **two** membership rows with distinct `chunk_index` (D1 multiset honesty,
  the F5 pin). It is very easy to inherit the collapse by reusing the same dict. Item 2's
  falsifier targets exactly this.

- ⚑⚑ **`provenance` STAYS on atom rows, or the mirror firewall silently vanishes.** The
  firewall is a row prefilter — `provenance IN (...)` with `prefilter=True`
  (`core/stores/vectorstore.py:317-324`) — and it holds only if the column is there to
  filter. Shedding it does not weaken the firewall; it *removes* it, with no visible error.
  Item 1's falsifier treats an absent/empty `provenance` as worse than a hard failure.

- ⚑ **The `group_sources` gap is real and the note understates it (§3 Q5).** `source_sets(store)`
  explicitly defaults to **all strata** (`core/kernel/stores/sourceset.py:148-156`), and
  `group_sources` keys on `r["digest"]` (`:131`). Shed code-atom rows carry `digest=''`, so
  they collapse into one bogus SourceSet keyed `''`. **`MixedProvenanceError` does NOT fire**
  (`:58-62` needs *mixed* provenance; these rows are uniformly CODE), so it fails silently. A
  test asserting "no exception raised" is therefore vacuous and must not be written. The
  guard lives on the shed side in `core/stores/` — `sourceset.py` is out of write scope. If
  the only correct fix is inside the kernel module, **stop and raise**; do not widen.
  (The *default* read path is safe: `grouped_semantic_search` passes `MIRROR_READABLE =
  {AUTHORED_SOLO, AUTHORED_DIALOGUE}` — `core/ingest/index.py:131-133`,
  `core/kernel/provenance.py:96-97`. The risk is the all-strata caller.)

- ⚑ **Never import the membership store from `core/kernel/**`.** That import would
  mechanically demote `sourceset` from the inner-ring fixed point. Memberships enter the
  kernel **as data**, through the existing `RowSource` protocol (`sourceset.py:48-55`).
  Note the subtlety: `rings.py:41` subtracts `sqlite3` itself, so importing sqlite3 is not
  the risk — a *kernel module importing an outer module* is. If the seam cannot stay
  data-shaped, the note is explicit: "that is a finding, not an import."

- ⚑ **The ring test will not redden — and if it does, do not hand-edit `INNER`.**
  `tests/unit/test_inner_ring.py:192` asserts `computed == INNER`. `core.stores` appears in
  `INNER` only as a docstring-only package marker (`rings.py:49,102`); the sqlite-backed
  sibling `core.stores.versions` is not a member, and `memberships.py` has the same profile.
  If it *does* redden, that means the module drifted toward purity against its role — raise
  it. `rings.py:24` is explicit: recompute and edit `INNER` to match, **never hand-edit
  toward green**. And `core/kernel/**` is out of scope here regardless.

- ⚑ **The embedder pin (owner-confirmed 2026-08-01).** Reuse is keyed to
  `(layer, content_hash)` **and** the embedder identity (`EmbeddingConfig.model` + `dim`,
  `core/kernel/config/loader.py:138-141`). A model change must invalidate every reuse —
  otherwise two geometries share one ANN space and no downstream measurement can detect it.
  This needs its own test case: a suite that only ever exercises one embedder cannot see the
  bug.

- ⚑ **`line_start`/`line_end` are the SLOT's extent, NOT the atom's text coverage** (issue #34,
  pinned in §6, asserted in Item 2). L0a partitions by *innermost owner*, so a class's chunk holds
  the class statement, its docstring, its attributes — **but not its methods**, which became their
  own chunks. Yet the coordinates are the owner's full declared span. Measured: `Foo` carries
  `lines 5-14` while its text holds only lines 5–7 and 13; the **module shell carries the entire
  file** (`1..n`) for four lines of text. Leaf functions agree exactly, which is why **every other
  fixture in this plan is blind to it** — build the class-with-methods + module-shell fixture, and
  assert the strict-subset relation explicitly. The trap: composing this with D0's "coordinates for
  display always resolve from memberships" and concluding that rendering the span shows the atom.
  For the module shell that renders the whole file.

- ⚑ **Every acceptance criterion has a named degenerate input. Assert the precondition
  first.** A do-nothing lander lands zero vectors (so §8(a) *must* assert currency). A store
  that never dedups makes the fork test vacuous (so §8(b) asserts `|V| < Σ chunks` first). An
  all-current fixture passes any current-filter (so §8(d) asserts a superseded occupancy
  exists). A purge that no-ops "never deletes" (so §8(c) asserts the recorded hole). A crash
  injected after all writes makes repair vacuous (so §8(e) asserts the orphan is observable).

- **Sizing.** This is the biggest of the three plans and sits at the edge of one session. Its
  six criteria are deliberately kept together because they are entangled — the fork test
  needs the lander, the invariants need the fork fixture. **If it does not fit: file a
  `spec-defect` issue and park. Never re-split mid-build** — the orchestrator re-graduates.

- **Depends on bp-151.** The dedup claims are only true once identity survives a rename.
  Confirm bp-151 has merged before starting.
