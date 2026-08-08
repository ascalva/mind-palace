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

- ⚑ **`slot_line_start`/`slot_line_end` are the SLOT's extent, NOT the atom's text coverage**
  (issue #34; Amendment **A2** renamed them for exactly this reason, and **the rename is half the
  fix** — the other half is the test below. A rename without the degenerate-input assertion is
  cosmetic, since every leaf-symbol fixture passes either way). **Rename both halves together:**
  the membership columns AND `CodeChunk.line_start`/`line_end` → `slot_line_*`
  (`core/ingest/code_corpus.py`, one consumer at `:274-275`). The vector-row Arrow keys
  `"line_start"`/`"line_end"` **stay** — that schema is shared with the prose lane, which has no
  slot concept (A2.3). L0a partitions by *innermost owner*, so a class's chunk holds
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

---

## Session 1 — 2026-08-08 · builder, worktree `build/bp-152-membership-store` (base 68d8d39)

**Status: all eight items built; §8(a)–(f) green and non-vacuous. One issue filed for a
consequence the plan did not enumerate (the eval harness reach, below).**

### What was built, item by item

**Item 1 — the atom row.** `code_rows(chunks, vectors, *, current=False)`. The signature lost
`path` and `blob_sha` because nothing on an atom row uses them any more: the id is
`atom_id(chunk) = f"{layer}:{content_hash}"` (path-free, corpus-wide) and every occupancy column
is shed to its empty value through the new `ATOM_ROW_SHED` dict in `vectorstore.py`.
`provenance` stays, hardcoded, and `test_every_atom_row_keeps_its_provenance_and_sheds_its_occupancy`
asserts *presence and equality*, not merely "no code leaked" — the firewall is a prefilter, so an
empty column removes it rather than weakening it.

**One micro-gap in D1, decided and recorded rather than inferred silently.** The note's shed list
enumerates `source_path, digest, qualname, line_*, chunk_index`; the keep list is
`id, layer, text, vector, provenance, current`. **`title` is in neither.** On a code row `title`
was set to `path` — it *is* `source_path` under another name — so it is shed with the occupancy
columns. Keeping it would stamp every shared atom with its first-landed path, which is precisely
the coordinate D0's consequence note says must never be relied on. Flagged here and in the PR body
for the reviewer; it is a one-line reversal if the owner reads D1's enumeration as exhaustive.

**Item 2 — the store.** `core/stores/memberships.py`, outer ring, sqlite. Key
`(path, blob_sha, layer, chunk_index)` exactly as pinned. `code_memberships()` in
`code_corpus.py` is the A2 translation point and builds **its own list** — one row per chunk,
never per distinct atom — so the atom-side `by_id.setdefault` collapse cannot be inherited.

The A2 rename landed on both halves in one change: `CodeChunk.slot_line_start`/`slot_line_end`
and `memberships.slot_line_start`/`slot_line_end`, with the vector-row Arrow keys untouched
(A2.3 — shared with the prose lane).

**A second table lives in the same SQLite file: `atoms`.** It records `(content_id, layer,
embedder_model, embedder_dim, landed_at)`. This is not a second truth about occupancy — it stores
the one fact the vector table structurally *cannot*: its Arrow schema is shared with the prose
lane and has no embedder column, and a stored vector's `len()` recovers `dim` but never `model`.
Without it the owner's embedder pin is unenforceable. It is also what makes an orphan observable
(§8(e)): an atom in the ledger with no membership row.

**Item 3 — the guard.** It lives in `VectorStore.all_rows`: an **unscoped** read
(`provenances=None`) now excludes shed atom rows unless the caller passes
`include_atom_rows=True`. No kernel edit; `sourceset.py` untouched. The test reproduces the
falsifier first — `group_sources(vs.all_rows(include_atom_rows=True))` really does return the
bogus set keyed `''`, containing every atom — and only then asserts the guard. A second test pins
that the guard keys on the **shed** (`is_code_atom_row`), never on the provenance, so the live
store's existing pre-D1 code rows keep grouping until bp-153 rebuilds them.

⚠ **One consequence worth the reviewer's eye:** `core/ingest/index.py`'s `rekey_store` reads
`all_rows()` unscoped, then `reset()`s and re-adds. With the guard it would *drop* shed atom rows;
without the guard it would *corrupt* them (it recomputes ids from `source_path` + `text`, and an
atom row's `source_path` is `''`). It was already broken by the shed either way, it is a one-shot
historical migration behind `scripts/migrate_chunk_keys.py`, and `core/ingest/index.py` is a
note-lane path deliberately out of this plan's scope (PD-2/R5). Filed, not fixed here.

**Item 4 — `land()`.** `CodeLander.land(path, blob_sha, chunks, *, head_blob_sha=None)` in
`code_corpus.py`, all five steps in the D8 order. Step 4 runs unconditionally.

Step 5's crossing set is computed as pure membership arithmetic, with **no read of the lance
column**: `candidates = set(atom ids) | atom_ids_of_path(path)`, `before = currently_held(candidates)`
taken *before* the fiber write, `after` taken after reconciliation, and only
`after - before` / `before - after` are flipped. Two consequences worth writing down: (i) a fresh
atom is inserted with `current=False` (at insert time, under D8's write order, it genuinely has no
occupancy), so its 0→1 crossing is picked up in step 5; (ii) an atom already current in another
path is inside `candidates` via the id list, so it is not redundantly rewritten.

`reconcile(path, head)` and `supersede_path(path)` are steps 4–5 alone. **`sync()` calls
`reconcile` for every unchanged HEAD path** — skipping it is the C1 short-circuit one level up:
after A→B→A the HEAD fiber exists, the file reads as unchanged, and B stays current forever. Two
counting queries per path is not a price worth trading for that.

`CodeCorpusSync` gained `memberships` and `embedder_identity` as **required** fields. Optional
would have been a footgun of exactly the kind the "wiring is part of finishing" rule names: a
lander with no occupancy record is not a lander, and a reuse decision with no embedder identity is
the geometry-mixing bug waiting to happen. Its D-fiber state re-homed from
`{(source_path, digest)}` to `memberships.fibers()` — the note's §6 re-home (1), applied at this
call site only. **The daemon's incompleteness probe (`ops/lifecycle/launcher.py:387`) still reads
the old shape and is bp-153's, exactly as the plan says; it will false-positive against a
rebuilt store, which is a bp-153 precondition, not a regression introduced here.**

**Items 5/6/7** — read-path join (`resolve_occupancies`, `ResolvedHit`), purge
(`purge_atom` → deletes the row, tombstones the memberships, forgets the ledger entry), the D8
repair pass (`orphan_atom_ids`, `repair_current_any`, `current_any_drift`), and derived lineage
(`slot_runs`/`slot_edges`, **adjacent** collapse, quantified over a chain handed in).

One correction to the plan's phrasing, found while building: "slotted" is the **layer**, not a
non-empty name. The L0a **module shell** carries `qualname=''` just like L0b/L1, so reading
slottedness off `slot != ''` would silently drop the lineage of the one slot every file has.
`slot_runs` filters on `layer == LAYER_CODE_AST`.

**Item 8 — surface repair.** Repaired: `test_code_corpus`, `test_code_retrieval`,
`test_code_mirror`, `test_code_vector_isolation`, `test_sourceset`, and — not in the plan's §5
list — `test_code_lineage` (it constructs `CodeCorpusSync` and asserts stored
`(source_path, digest)`, so the shed moved it). No firewall assertion was relaxed; the
`test_code_mirror` / `test_code_vector_isolation` claims are unchanged in kind and now read
through the join.

### The one reach beyond write_scope, and why

`eval/harness/code_retrieval.py`'s `ranked_paths` reads `h["source_path"]` off a hit. On atom rows
that is `''`, so the M-C3/M-C5 battery silently ranked nothing — the plan's §3 investigation did
not surface it (it is the D3 read path, one file outside the enumerated scope). `ranked_paths` and
`run_mc3` gained an **optional** `memberships` parameter: pass it and each hit contributes every
path it currently occupies, which is the honest reading of a shared atom; omit it and the pre-split
behavior is byte-identical. Additive, ~20 lines, and it keeps the instrument working rather than
leaving a known-broken one behind. Called out in the PR body for the merge audit.

### How each criterion was made non-vacuous

| criterion | the precondition that makes it bite |
|---|---|
| §8(a) revert | A and B are asserted DISTINCT (`\|V\|` grew between them) before the third land; the currency assertions carry the claim, and a **mutation test** exhibits the short-circuiting lander passing every count and leaving B current |
| §8(b) fork | `\|V\| == 3 < Σ chunks == 4` and `n_doc(shared) == 2` asserted first; the edit is hand-built so "exactly 1 new atom" is exact arithmetic (a real file's single L0b window recuts on any edit) |
| §8(c) purge | the note-lane removal paths are shown to ACT (the note row really is deleted) while `\|V\|` is unmoved; then the purge's report is asserted non-zero and the tombstoned rows are asserted to still EXIST |
| §8(d) retrieval | a superseded occupancy is asserted to exist AND an atom whose every home is superseded (`n_doc == 0`) — so the current-filter is not passing on an all-current store |
| §8(e) crash | the injection point is asserted: `\|V\|` grew, `\|M\|` did not, the fiber is empty, and `orphan_atom_ids()` is non-empty and equals the landed set |
| §8(f) invariants | one test asserts the fixture carries **all four shapes** before any invariant is read; the runs invariant asserts A→B→A gives 3 runs / 2 edges and that distinct-collapse would give 2; the fiber-sum invariant is broken by a subclass whose `fiber()` drops superseded rows (the fixture is asserted to hold one); the drift invariant is broken by a hand-flipped flag |
| Item 2 / A2 | the fixture is asserted to contain a nested symbol (`Foo.bar` inside `Foo`) and a non-empty module shell; the leaf symbol `top` is asserted to have span == coverage **exactly**, as the control that makes the strict-subset assertions mean something |
| embedder pin | its own test, with the same-embedder control asserted first so "re-embedded" means "the embedder changed", not "reuse never worked" |

### Gate

Recorded in the PR body. Baseline on the clean base (68d8d39) before any edit:
**5 failed, 2427 passed, 15 skipped** — exactly the three known-red classes (finding-0103
self-containment ratchet, `test_dream_v2_live`, `test_worktree_enforcement` ×3, issue #13 /
finding-0280).

### For bp-153

- The incompleteness probe (`ops/lifecycle/launcher.py:_code_backfill_incomplete`) must re-home to
  `memberships.fibers()` **before** a rebuilt store exists, or it enqueues forever (finding-0166's
  named falsifier).
- `repair_current_any` / `current_any_drift` are built and tested — they are the R3 ratchet's
  instrument, ready to register as a gauge.
- `n_doc` / `n_occ` are built and separated (the F5 pin). `|M|` is `MembershipStore.count()`, `|V|`
  is `len(VectorStore.atom_rows())` — the `|M|/|V|` gauge needs no new machinery.
- The carry-forward seed re-enters through `record_atoms(...)` under the live `EmbedderIdentity`;
  an entry recorded under a different embedder is not a reuse hit, which is what makes the
  13,311-atom bulk reuse safe rather than a silent geometry mix.
