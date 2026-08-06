---
type: build-plan
id: bp-152
track: code-ingest
status: proposed
design_ref:
  - docs/design-notes/vector-membership-store.md
contract: builder
write_scope:
  - core/stores/memberships.py
  - core/stores/vectorstore.py
  - core/ingest/code_corpus.py
  - tests/unit/test_memberships.py
  - tests/unit/test_code_corpus.py
  - tests/unit/test_code_retrieval.py
  - tests/unit/test_vectorstore_supersede.py
  - tests/integration/test_code_mirror.py
  - tests/integration/test_code_vector_isolation.py
  - tests/integration/test_sourceset.py
  - tests/integration/test_index_keying.py
  - tests/integration/test_rekey_migration.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 650k
  actual: null
depends_on: [bp-151]
parallelizable_with: []
created: 2026-08-01
updated: 2026-08-01
links:
  - docs/findings/finding-0168.md
  - docs/findings/finding-0164.md
  - docs/design-notes/temporal-code-corpus.md
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — the membership store: the split, the lander, the read path (D1/D2/D3/D8)

## 0. Mode & provenance

Graduated from `dn-vector-membership-store` D1, D2, D3, D8 on 2026-08-01 under the owner's
"graduate now, merge = blessing" ruling (issue #27). Investigation and planning produced
this plan; implementation proceeds item-by-item. All `path:line` citations re-opened
against HEAD `174d06c`; zero drift since the note.

Second of three plans. **Depends on bp-151** — the atom+membership split is only correct
once identity survives a rename (finding-0168 addendum 4's precondition, supplied by D0).

## 1. Objective

Store one vector row per idea-atom and carry all occupancy in a membership relation, so a
version is a fiber and a re-land is idempotent.

## 2. Context manifest

Read in order:

1. `docs/design-notes/vector-membership-store.md` — D1, D2, D3, D8, §4, §5, §8(a)–(f).
   The whole note; D1–D3 and D8 are this plan.
2. `docs/build-plans/bp-151/plan.md` — the identity this plan builds on. Its §6 pins are
   this plan's inputs.
3. `core/stores/vectorstore.py` — whole file. The schema (`_schema`, `:37-61`) and the
   search prefilter (`:303-325`) are the surfaces that move.
4. `core/ingest/code_corpus.py` — whole file. `code_rows` (`:199-229`) is the row assembly
   the split rewrites; `derive_code_chunks` (`:181-194`) supplies `chunk_index`.
5. `core/kernel/stores/sourceset.py` — whole file. The `RowSource` protocol (`:48-55`) is
   the data-shaped seam D3 requires, and `group_sources` (`:131`) is the consumer this plan
   must not silently break (§3 Q5 — the one place the note's claim is over-broad).
6. `core/kernel/rings.py:36-41` — why the membership store may never be reached by a kernel
   import.
7. `core/stores/versions.py:17-35` — the C1 lesson in the repo's own words: content-keyed
   identity cannot hold a revert.
8. `docs/findings/finding-0168.md` — the five owner rulings this implements.

## 3. Investigation & grounding

- **Q1 — What is the current row identity, and what does the split change?**
  `code_rows` builds `rid = f"{path}:{ch.layer}:{ch.content_hash}"` (`code_corpus.py:213`)
  and dedups per path via `by_id.setdefault(rid, row)` (`:229`, "one point per (path, layer,
  content)"). D1 makes it `f"{ch.layer}:{ch.content_hash}"` — path-free — which promotes
  that per-path dedup to corpus-wide dedup. That single character-level change *is* the
  atom model.
- **Q2 — Does the `provenance` column really carry the mirror firewall (so D1's "it
  STAYS" is load-bearing)?** Yes. `search` builds `provenance IN (...)` and applies it with
  `prefilter=True` (`vectorstore.py:317-324`). The column is the filter's only input; drop
  it and the firewall is not weakened but *absent*. D1's insistence is correct and must be
  carried as a test.
- **Q3 — Is the `current = true` default clause safe to re-read as `current_any`?** Yes.
  `if not include_superseded: clauses.append("current = true")` (`:320-321`), and note rows
  carry a vacuous `current=true` (`:53-59` schema comment). Re-reading the column as "does
  ANY current membership contain this atom" keeps both lanes working through one clause,
  exactly as D1 says.
- **Q4 — Is `chunk_index` well-defined enough to key memberships?** Yes.
  `derive_code_chunks` is a pure deterministic function of `(path, source)`
  (`code_corpus.py:181-194`, F-CI2, "bit-identically re-derivable"), so the enumeration
  order `code_rows` uses (`:212`, `enumerate`) is re-derivable. The D1 key
  `(path, blob_sha, layer, chunk_index)` is therefore stable.
- **Q5 — ⚠ Does the shed of `digest` from atom rows break `group_sources`? The note says
  no; the code says "not by default, and not safely."** This is the one place D1's claim is
  over-broad, and it is recorded here rather than planned around.
  - `grouped_semantic_search` defaults to `provenances=MIRROR_READABLE`
    (`core/ingest/index.py:131-133`), and `MIRROR_READABLE = {AUTHORED_SOLO,
    AUTHORED_DIALOGUE}` (`core/kernel/provenance.py:96-97`). Code rows are `CODE`, so they
    never enter this path by default. **The note's claim holds here.**
  - But `source_sets(store)` explicitly defaults to **all strata** — "Default is all
    strata: this is a structural grouping utility, not a mirror read"
    (`sourceset.py:148-156`). Called with its default, it passes CODE atom rows into
    `group_sources`, which keys on `r["digest"]` (`:131`). Shed rows carry `digest=''`, so
    **every code atom in the corpus collapses into one bogus SourceSet keyed `''`**.
  - It fails **silently**: `MixedProvenanceError` (`:58-62`) fires only on a digest spanning
    *several* provenances, and these rows are uniformly CODE.
  - The code does not settle whether any caller does this today; what would settle it is a
    structural guard rather than an audit, since a future caller reintroduces the bug.
    **Item 3 builds the guard.**
- **Q6 — Is `delete_source` really path-scoped (D1's other shed-safety claim)?** Yes —
  `store.delete_source(record.source_path)` (`core/ingest/index.py:87`) is called with the
  note's own source path, so it cannot match an atom row's empty `source_path`. **The
  note's claim holds.**
- **Q7 — Can memberships enter the kernel as data (D3/C5)?** Yes. `RowSource` is a
  `Protocol` with a single `all_rows(*, provenances=...)` method (`sourceset.py:48-55`), so
  a membership-backed adapter satisfies it structurally with no kernel import. Note that
  `rings.py:41` subtracts `sqlite3` itself from the ring predicate — so the risk is *not*
  importing sqlite3; it is a kernel module importing `core.stores.memberships` (an outer
  module), which is what would demote `sourceset`. The pin is about module direction, not
  about sqlite.
- **Q8 — Does a revert actually round-trip in the existing chain machinery?** Yes, and the
  note's F4 dispute is correct on the code: `supersession_chains` appends only when
  `new_blob and (not chain or chain[-1] != new_blob)` (`ops/code_lineage.py:151-156`) —
  **adjacent** repeats only. `[A, B, A]` is preserved. The docstring's "ordered distinct
  sequence" (`:139`) is loose language, not the behavior.

- **Q9 — Will a new `core/stores/memberships.py` redden the inner-ring fixed point?** No,
  and the reason is the D3 pin working structurally. `tests/unit/test_inner_ring.py`
  recomputes the fixed point over `core/**` at test time and asserts `computed == INNER`
  (`:192`), so a new `core/` module that computed as *inner* would redden with "extra". But
  `INNER` contains only `"core.stores"` itself (`rings.py:102`) — a docstring-only package
  marker "whose outer submodules stay [outer]" (`:49`). The existing sqlite-backed sibling
  `core.stores.versions` is **not** a member. `memberships.py` has the identical import
  profile, so it computes outer, the ring test stays green, and **no `core/kernel/**` edit
  is needed** — placement alone satisfies C5. If the builder ever finds the ring test
  reddening on this module, that means the module drifted toward purity in a way that
  contradicts its role, and it is a stop-and-raise (§10), never an `INNER` hand-edit
  (`rings.py:24` — "never hand-edit toward green").

**Additional risks or questions surfaced during reading:**

- **`by_id.setdefault` silently drops duplicates within a file.** At `:229` two identical
  L0b windows in one blob collapse to one row. Under D1's multiset honesty ("two identical
  windows in one blob are two rows with distinct `chunk_index`") the *membership* side must
  **not** inherit this collapse. This is a concrete trap: the atom side dedups, the
  membership side must not. §7 Item 2's falsifier targets it.
- **No compaction API exists in `vectorstore.py`** (verified — no such method). The note
  puts compaction in scope but it belongs to bp-153; noted here so the builder does not
  discover it mid-session and improvise.
- **`current` is a lance column, so flips are dataset rewrites.** The note's §3 pin (batch
  flips, only atoms crossing 0↔1) is a performance property this plan must honor in the
  lander, even though the compaction that bounds it lands in bp-153.

## 4. Reconciliation

- `core/ingest/code_corpus.py:203-210` — the `code_rows` docstring: "`id` is
  `(source_path, layer, chunk_hash)` — doc+layer-scoped" and "`digest` is the git blob sha,
  so group-by-digest yields file = source object, its chunks = members" →
  **[banner: correction]**. Both clauses stop being true for code atom rows. The corrected
  docstring must say: id is `(layer, content_hash)`, corpus-wide; the source object is now
  the membership fiber, and group-by-digest is *not* the code lane's path (see Item 3's
  guard). Carried by §7 Item 1, called out as a correction.

- `core/stores/vectorstore.py:53-59` — the schema comment describing `current` as "is this
  row part of the source path's CURRENT (HEAD) projection?" → **[banner: correction]**. For
  atom rows the column is re-read as `current_any` ("does ANY current membership contain
  this atom"). Note rows keep the old vacuous reading. The comment must carry both readings
  explicitly, since one column now means two things.

- `core/kernel/stores/sourceset.py:148-156` — `source_sets`' "Default is all strata"
  → **[banner: correction]**, carried by §7 Item 3. This is the §3 Q5 gap: the docstring
  promises a structural grouping utility over every stratum, and after the shed that promise
  silently produces a garbage set for the code lane. The correction is a guard plus an
  honest docstring, not a quiet default change.

- `docs/design-notes/temporal-code-corpus.md` — the two §6 re-homes (the incompleteness
  probe's data source, `:141-143`; D5's endpoint resolution, `:125-126`) →
  **[banner: correction]** on the *parent note*. **Not carried by this plan**: the note is a
  design artifact and the amendment travels in the graduation PR as its own commit
  (`docs/design-notes/temporal-code-corpus.md` is deliberately absent from `write_scope`).
  The probe's mechanical re-home is bp-153's code work.

## 5. Write scope

Three production files:

- `core/stores/memberships.py` — **new**. The membership relation, its schema, and the
  fiber/currency operations. Home is `core/stores/` (outer ring) — never `core/kernel/`
  (§3 Q7).
- `core/stores/vectorstore.py` — the schema re-reading (`current` → `current_any` semantics
  for atom rows) and whatever the atom-row shed requires. `provenance` **stays** (§3 Q2).
- `core/ingest/code_corpus.py` — `code_rows` becomes atom-row assembly + fiber emission;
  the id goes path-free.

Nine test files, carried because they pin surfaces this plan moves:

- `tests/unit/test_memberships.py` — **new**; the store's own tests, §8(a)–(f).
- `tests/unit/test_code_corpus.py`, `tests/unit/test_code_retrieval.py` — import
  `code_rows` / `derive_code_chunks` directly (`:22`, `:16`), so the id change reddens them.
- `tests/unit/test_vectorstore_supersede.py` — pins the `current` flip semantics being
  re-read.
- `tests/integration/test_code_mirror.py`, `tests/integration/test_code_vector_isolation.py`
  — assert the firewall over code rows; carried so §3 Q2's invariant can be strengthened
  into a test here.
- `tests/integration/test_sourceset.py` — imports `group_sources` (`:16`, `:139`); carried
  for Item 3's guard.
- `tests/integration/test_index_keying.py`, `tests/integration/test_rekey_migration.py` —
  both assert stored id shape; the path-free id moves them.

Deliberately **out of scope**: `core/kernel/**` (a kernel import would demote `sourceset`
from the inner-ring fixed point — the C5/D3 pin; if the seam cannot stay data-shaped that
is a finding, §10), `ops/code_lineage.py` and `ops/code_snapshot.py` (bp-153),
`docs/design-notes/**` (the amendment travels in the PR, not from a builder's hand), all
note-lane ingest paths (PD-2 — prose is untouched), and the fixed points
(`CONSTITUTION.md`, `eval/golden/**`, `eval/golden.py`).

## 6. Interfaces pinned inline

**The membership schema (D1, verbatim from the note):** one row per occupancy, key =
`(path, blob_sha, layer, chunk_index)`, columns `content_id`, `slot`, `line_start`,
`line_end`, `current`, `tombstoned`. `slot` = qualname for **L0a only** — L0b and L1 carry
`qualname=''` (`code_corpus.py:177`), so L0a is the only slotted layer and L0b/L1 are
membership-only, honestly chainless (R4). A version's projection = the fiber
`M(path, blob_sha)`. **Multiset honesty:** two identical windows in one blob are two rows
with distinct `chunk_index` — no occupancy vanishes by key collision.

**The vector row (D1):** `id = "{layer}:{content_hash}"`, plus `layer`, `text`, `vector`,
`provenance` (**stays** — the firewall is a row prefilter and holds only if the column is
there to filter), and the existing `current` column re-read as `current_any`. The occupancy
columns (`source_path`, `digest`, `qualname`, `line_*`, `chunk_index`) are shed from
**code-atom rows, not from the schema** — note rows still carry them.

**`land(path, blob_sha, chunks)` — the write path (D2, all five steps; step 4 is the C1
bug):**

1. compute canonical `content_hash` per chunk (D0, bp-151);
2. insert only the atoms absent from the plane (the embed step);
3. write the membership fiber for `(path, blob_sha)`; an existing fiber's rows stand;
4. **currency reconciliation — NEVER skipped, even when step 3 was a no-op**: set
   `current=true` on exactly the fiber whose blob is the path's HEAD blob, and
   `current=false` on the path's every other fiber;
5. maintain `current_any` on atoms whose current-membership count crossed 0↔1.

> Re-landing is idempotent BECAUSE reconciliation converges, not because the call
> short-circuits — the first draft's "existing fiber ⇒ no-op" was precisely the C1 bug: on
> A→B→A the fiber for blob A already exists with `current=false`, and a short-circuit
> leaves **B** current — silent corruption.

**The embedder pin on reuse (owner confirmation, 2026-08-01 — issue #27 sub-confirmation 2).**
Step 2's "insert only the atoms absent from the plane" is an **embed-reuse** decision, and
reuse is only valid within one embedder. A model change must invalidate every reuse — an
atom present in the plane carries a vector from whichever embedder landed it, and silently
serving it alongside freshly-embedded atoms mixes two geometries in one ANN space, which no
downstream measurement can detect. **Pin: atom presence is keyed to `(layer, content_hash)`
AND the embedder identity; a reuse whose embedder identity differs from the live config is
not a hit.** The embedder identity is `EmbeddingConfig.model` + `dim`, current form
`core/kernel/config/loader.py:138-141`:

```python
class EmbeddingConfig:
    model: str
    dim: int
    query_instruction: str
```

(`query_instruction` is excluded: it conditions *queries*, not stored document vectors.)
The same pin governs bp-153's carry-forward seed, where 13,311 atoms are reused in bulk —
there it is the difference between a free migration and a corrupted plane.

**Write order (D8, crash consistency):** vector inserts FIRST (append-only,
unreferenced-is-harmless), membership fiber SECOND (transactional in SQLite), currency
reconciliation + `current_any` maintenance LAST (re-derivable — a repair pass exists).
Membership SQLite is the reference truth; `current_any` is a cache with a rebuild path.

**The read path (D3):** ANN search over `vectors` (prefilter: the existing `current = true`
clause read as `current_any`, plus provenance) → top-k atoms → **join memberships** to
resolve occupancies `(path, blob, slot, lines, current, tombstoned)`. One atom may resolve
to several occupancies — that is the feature. Default consumers see current occupancies
only.

**The seam that must stay data-shaped (D3/C5), current form `sourceset.py:48-55`:**

```python
class RowSource(Protocol):
    """Anything that yields provenance-filtered chunk rows — the VectorStore, or a test fake."""

    def all_rows(self, *,
                 provenances: Iterable[Provenance] | None = None) -> list[dict[str, Any]]:
        ...
```

**The prefilter that must keep working, current form `vectorstore.py:315-325`:**

```python
        q = self._table().search(vector).metric("cosine")
        clauses: list[str] = []
        if provenances is not None:
            allowed = ", ".join(f"'{Provenance(p).value}'" for p in provenances)
            clauses.append(f"provenance IN ({allowed})")
        if not include_superseded:
            clauses.append("current = true")        # current-view default (D3)
        if clauses:
            # prefilter so the k nearest are taken from the permitted set, not after.
            q = q.where(" AND ".join(clauses), prefilter=True)
        return q.limit(k).to_list()
```

**The §4 invariants to carry as tests:** per-slot `|edges| = |runs| − 1`;
`Σ fiber sizes = |M|`; `current_any(v) ⇔ n_doc(v, t) > 0`; append-only ⇒ no test may ever
observe `|V|` decrease (except across a logged purge).

## 7. Items

### Item 1 — the atom row: path-free identity and the code-row shed

- **Objective:** `code_rows` emits one row per `(layer, content_hash)` with occupancy
  columns shed, `provenance` retained.
- **Files:** `core/ingest/code_corpus.py`, `core/stores/vectorstore.py`,
  `tests/unit/test_code_corpus.py`, `tests/integration/test_index_keying.py`
- **Acceptance test:** the same chunk body appearing in two different files yields **one**
  row whose id is `f"{layer}:{content_hash}"`; a test asserts `provenance` is present and
  equal to `CODE` on every atom row.
- **Falsifier:** two rows appear (the id still carries the path), **or** `provenance` is
  absent/empty on an atom row — which would silently void the mirror firewall (§3 Q2),
  a worse outcome than a visible failure.
- **Invariant(s) it must not violate:** provenance stays structurally hardcoded — no
  parameter (`:220`, F-CI1). One-layer-one-provenance: an atom never spans strata (the PD-2
  fence), carried as a test invariant.
- **Touches stored data?** Yes — the row schema written to lance changes. Require a
  dry-run over a fixture store before any write against a real store; this plan never
  rewrites the live store (that is bp-153).
- **Parallelizable?** No. **Depends on:** bp-151.

### Item 2 — the membership store and the fiber

- **Objective:** `core/stores/memberships.py` exists and can write/read a version's fiber
  under the D1 key.
- **Files:** `core/stores/memberships.py`, `tests/unit/test_memberships.py`
- **Acceptance test:** writing a fiber for `(path, blob_sha)` and reading it back yields
  exactly the chunks derived for that blob, in `chunk_index` order; `Σ fiber sizes = |M|`
  holds on the fixture.
- **Falsifier:** **a blob containing two byte-identical L0b windows stores one membership
  row instead of two.** That is the multiset-honesty violation the atom-side dedup invites
  (§3, `by_id.setdefault` at `:229`) — the atom side must dedup and the membership side must
  not. Also falsified if the store is importable from `core/kernel/**`.
- **Invariant(s) it must not violate:** no kernel import (the C5/D3 ring pin); `slot` is
  populated for L0a only, `''` for L0b/L1 (R4 — never a quiet re-slot).
- **Touches stored data?** Yes — new SQLite store, created beside the vault catalog.
- **Parallelizable?** Yes, with Item 1 (disjoint files) once bp-151 has landed.
  **Depends on:** bp-151.

### Item 3 — the `group_sources` guard (the §3 Q5 gap)

- **Objective:** a shed code-atom row can never silently collapse into a bogus SourceSet.
- **Files:** `core/stores/vectorstore.py` or `core/ingest/code_corpus.py` (whichever holds
  the shed), `tests/integration/test_sourceset.py`
- **Acceptance test:** calling `source_sets(store)` with its **default** (all strata) over
  a store containing code atom rows either excludes them or raises — it does **not** return
  a SourceSet keyed `''`. The test asserts the precondition first: that the store actually
  contains ≥2 code atom rows (otherwise the check is vacuous).
- **Falsifier:** the call returns a single SourceSet containing every code atom — the
  silent-collapse bug, reproduced. Note that `MixedProvenanceError` does **not** fire here
  (`sourceset.py:58-62` needs mixed provenance; these rows are uniformly CODE), so a test
  that merely asserts "no exception" is itself vacuous and must not be written.
- **Invariant(s) it must not violate:** `core/kernel/stores/sourceset.py` is **out of write
  scope** — the guard lives on the shed side, in `core/stores/`. If the only correct fix
  proves to be inside the kernel module, that is a stop-and-raise (§10), not a scope
  widening.
- **Touches stored data?** No.
- **Parallelizable?** No. **Depends on:** Item 1.

### Item 4 — `land()`: the five-step write path with currency reconciliation

- **Objective:** landing a version is idempotent by convergence, not by short-circuit.
- **Files:** `core/stores/memberships.py`, `core/ingest/code_corpus.py`,
  `tests/unit/test_memberships.py`
- **Acceptance test:** **§8(a), the C1 case** — land A → B → A (a real revert). Zero vector
  inserts, zero new membership rows, **and** currency converges: A's fiber `current=true`,
  B's `current=false`.
- **Falsifier:** B stays `current=true` after the third land — the short-circuit bug the
  note names explicitly. Per the note's degenerate-input rule, a do-nothing lander also
  lands zero vectors, so **the currency assertions are mandatory**; a test asserting only
  "zero inserts" is vacuous and must not be written.
- **Invariant(s) it must not violate:** step 4 runs even when step 3 was a no-op. Append-only:
  no code path deletes a vector. `current_any(v) ⇔ n_doc(v, t) > 0`. **The embedder pin
  (§6):** reuse is keyed to `(layer, content_hash)` *and* the embedder identity — carried as
  a test that landing the same atom under a changed `EmbeddingConfig.model` re-embeds rather
  than reusing. A test that only exercises one embedder cannot see this, so the pin needs its
  own case.
- **Touches stored data?** Yes — dry-run against a fixture store first.
- **Parallelizable?** No. **Depends on:** Items 1, 2.

### Item 5 — fork semantics and the read-path join

- **Objective:** one atom resolves to all its current occupancies; default retrieval stays
  current-view.
- **Files:** `core/stores/memberships.py`, `core/stores/vectorstore.py`,
  `tests/unit/test_memberships.py`, `tests/unit/test_code_retrieval.py`
- **Acceptance test:** **§8(b) fork** — precondition asserted **first** (the shared atom has
  2 current memberships and `|V| < Σ chunks`), then editing one file yields exactly 1 new
  atom, 1 membership swap, the other fiber byte-identical, both lineages traversing the
  shared node. **§8(d) retrieval** — fixture holds ≥1 superseded occupancy (asserted first);
  default search returns only current occupancies, `include_superseded` surfaces the
  superseded one, and a shared atom resolves to all its current homes.
- **Falsifier:** the fork precondition passes on a store that never dedups — then "the
  other file's fiber untouched" is vacuous. Likewise an all-current fixture makes the
  current-filter test vacuous. Either means the test proves nothing.
- **Invariant(s) it must not violate:** the mirror firewall — an AUTHORED-scoped search
  still cannot surface a CODE atom. Flat retrieval behavior is preserved for existing
  consumers.
- **Touches stored data?** No — read path plus fixtures.
- **Parallelizable?** No. **Depends on:** Item 4.

### Item 6 — append-only, purge, and the D8 crash property test

- **Objective:** removal is observable and only by purge; a crash mid-land repairs.
- **Files:** `core/stores/memberships.py`, `tests/unit/test_memberships.py`
- **Acceptance test:** **§8(c)** — no API path deletes a vector except purge, and purge
  **observably acts**: row gone, memberships tombstoned. **§8(e)** — a crash injected
  between vector insert and fiber write; the test **first** asserts the orphan state is
  observable, then re-lands and asserts nothing dangles.
- **Falsifier:** a purge that silently no-ops still satisfies "never deletes" — so the test
  must assert the recorded hole exists. A "crash" injected *after* all writes makes repair
  vacuous — the injection point must be asserted.
- **Invariant(s) it must not violate:** no test may ever observe `|V|` decrease except
  across a logged purge. Membership SQLite stays the reference truth.
- **Touches stored data?** Yes — purge is a true delete; owner-gated, fixture-only here.
- **Parallelizable?** Yes, with Item 5. **Depends on:** Item 4.

### Item 7 — the §4 invariants as tests on the degenerate fixture

- **Objective:** §8(f) — the four invariants hold and redden under seeded violation.
- **Files:** `tests/unit/test_memberships.py`
- **Acceptance test:** on a fixture holding a revert, a merge side-branch version, a shared
  atom, and a duplicate L0b window pair: per-slot `|edges| = |runs| − 1`;
  `Σ fiber sizes = |M|`; `current_any(v) ⇔ n_doc(v, t) > 0`; `|V|` never decreases. Each
  invariant reddens under a seeded violation, and the load-bearing gates get a mutation
  check.
- **Falsifier:** an invariant that stays green under its seeded violation — it is not
  testing what it claims. A fixture missing any of the four shapes makes the corresponding
  invariant vacuous.
- **Invariant(s) it must not violate:** chain members ⊊ ledger versions — the side-branch
  fiber contributes to `M` and to `n(v)` but to **no** edge count (D4/F3). An invariant
  quantified over all fibers instead of chain members is wrong.
- **Touches stored data?** No.
- **Parallelizable?** No. **Depends on:** Items 4, 5, 6.

### Item 8 — repair the carried test surface

- **Objective:** the full local CI gate is green.
- **Files:** the carried test files in §5.
- **Acceptance test:** ruff + import-firewall + mypy at its current baseline + type_gate +
  CI-tier pytest, all green. Counts drift — trust the run.
- **Falsifier:** a test made green by weakening its assertion rather than by updating the
  expected identity — particularly any relaxation of a firewall assertion in
  `test_code_mirror.py` / `test_code_vector_isolation.py`.
- **Invariant(s) it must not violate:** the import-firewall must still show
  `core/kernel/**` free of any `core.stores.memberships` import.
- **Touches stored data?** No.
- **Parallelizable?** No. **Depends on:** Items 1–7.

## 8. Math carried explicitly

- **The membership relation `M ⊆ V × O`** — *measures:* which atoms occupy which
  `(path, blob)` versions, at which slot and lines. *valid when:* `chunk_index` is
  re-derivable (§3 Q4) so the key is stable, and the multiset reading is preserved (two
  identical windows = two rows). *fails its keep if:* `Σ fiber sizes ≠ |M|`, or an
  occupancy vanishes by key collision.

- **The fiber `M(path, blob_sha)`** — *measures:* one version's complete projection.
  *valid when:* derivation is pure, so fiber equality holds on a re-land. *fails its keep
  if:* a re-land produces a different fiber for the same blob.

- **Occurrence runs and supersession edges (the C1 formulation)** — *measures:* per slotted
  `(path, slot)`, the first-parent chain collapsed into runs of equal occupants; edges are
  consecutive-run pairs, so per slot `|edges| = |runs| − 1`. *valid when:* quantified over
  **chain members only** — a side-branch fiber sits on no chain (D4/F3) — and adjacent
  collapse (not distinct-collapse) is used, so `A→B→A` gives 3 runs and 2 edges. *fails its
  keep if:* a revert yields 1 edge (distinct-collapse crept back in), or the count is
  quantified over all fibers.

- **The atom projection as a directed multigraph** — *measures:* lineage projected from
  occurrences onto atoms. *valid when:* read as a multigraph, **not** a DAG: `A→B→A`
  projects the 2-cycle `h_A→h_B→h_A`, and an atom-cycle **is** a re-occupancy, readable as
  such. *fails its keep if:* a consumer requires acyclicity — then it is reading the wrong
  object, and forks/joins as intersections (D4) stop being expressible.

- **`current_any(v)`** — *measures:* whether any current membership contains `v`; the ANN
  prefilter's cheap default. *valid when:* maintained on every 0↔1 crossing (D2 step 5) and
  treated as a **cache** over membership truth. *fails its keep if:* it drifts from
  `n_doc(v, t) > 0` (R3) — which is why the equivalence is a carried invariant, not an
  assumption.

## 9. Non-goals

- **No rebuild, no backfill, no gauges, no compaction.** All bp-153. The live store is not
  rewritten by this plan.
- **The old duplicated backfill must never be run** — 52,755 vs 22,502 embeds is 2.34×
  measured waste (D7). Not "avoid"; never.
- **No notes-lane adoption (PD-2).** Prose rows are untouched; atoms never span strata. The
  builder must not "helpfully" migrate prose (R5).
- **No stored edge table for slot lineage (PD-3).** Edges stay derived from membership +
  `commit_diffs`.
- **No ANN/index tuning, no embedder change, no logical pruning.** Append-only makes
  pruning a non-feature.
- **No L1 re-slotting (PD-5), no id-shape work belonging to bp-151.**
- **No kernel edit.** Memberships enter the kernel as data or not at all.

## 10. Stop-and-raise conditions

- **The D3 seam cannot stay data-shaped** — if memberships can only reach `sourceset`
  through an import from `core/kernel/**`, **stop**. The note is explicit: "If the seam
  cannot stay data-shaped, that is a finding, not an import." A kernel import would
  mechanically demote `sourceset` from the inner-ring fixed point.
- **Item 3's guard requires editing `core/kernel/stores/sourceset.py`** — out of scope by
  design. File an issue and park the item; the remaining items continue.
- **The multiset/dedup tension proves irreconcilable** — if the atom-side dedup cannot be
  separated from the membership-side multiset, that is a spec defect in D1, not a coding
  problem.
- **A degenerate-input precondition cannot be asserted** for any of §8(a)–(f) — a criterion
  that cannot be made non-vacuous must be raised, never quietly weakened into a passing
  test.
- **Blast-radius surprise on stored data** — any write against a real (non-fixture) store.
  This plan's stored-data items are fixture-only.
- The builder performs **no blessing and no status flip**, and never writes the fixed
  points (`CONSTITUTION.md`, `eval/golden/**`, `eval/golden.py`).

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| Notes-lane adoption (PD-2) | Code-first; prose untouched; atoms never span strata (the D1 stratum fence) | Migrate prose now — rejected: cross-stratum sharing breaks both the prefilter and sourceset's one-stratum axiom (`sourceset.py:58-62`) | Notes keep-and-link lands (finding-0164) AND the prefilter is redesigned for sharing |
| Materialized slot-edge view (PD-3) | Derived on read | A second stored truth — rejected as a second source of truth for lineage | A consumer needs edge queries at a rate joins cannot serve |
| L1 slotting (PD-5) | L1 stays windowed + slotless (R4) | Re-slot L1 — rejected: a quiet re-slot is exactly what R4 forbids | A consumer needs docstring/comment lineage |
| Read-path join latency (R2) | Measure in T4 before optimizing; `current_any` prefilter keeps the ANN set lean | Pre-optimize the join now — rejected as unmeasured | T4 shows the k×SQLite lookups dominate |
| Where the Item 3 guard lives | On the shed side, in `core/stores/` | Inside `core/kernel/stores/sourceset.py` — rejected: out of scope, and a kernel edit for an outer-ring concern | The guard proves impossible outside the kernel (→ §10) |

## 12. Dependency & ordering summary

**Gated on bp-151** — the whole plan assumes canonical identity.

Blast-radius order: Item 3 (read-only guard) and Items 1–2 (store construction) precede the
lander (Item 4), which precedes the read path and the destructive/property work (Items 5–6),
with invariants (7) and surface repair (8) last.

- **Item 1** (atom row) and **Item 2** (membership store) are **parallelizable** — disjoint
  files.
- **Item 3** depends on Item 1 (needs the shed to exist to guard it).
- **Item 4** (land) depends on Items 1 + 2 — it is the join of both.
- **Item 5** (fork/read) depends on Item 4; **Item 6** (purge/crash) depends on Item 4 and
  is **parallelizable with Item 5**.
- **Item 7** (invariants) depends on 4, 5, 6 — it quantifies over everything they build.
- **Item 8** (surface repair) is last.

**Cross-plan:** bp-153 `depends_on: [bp-152]` — the rebuild needs a lander to rebuild into,
and the gauges need `|M|` and `|V|` to exist.

**Sizing note.** This is the largest of the three plans (estimate 650k, opus) and it is at
the edge of one session. It is kept whole because its six acceptance criteria
(§8 a–f) are mutually entangled — the fork test needs the lander, the invariants need the
fixture the fork test builds — and splitting them would put a barrier between a lander and
the tests that prove it correct. If the builder finds mid-session that it does not fit, the
discipline is **file a `spec-defect` issue and park** — never re-split mid-build (the
orchestrator re-graduates).
