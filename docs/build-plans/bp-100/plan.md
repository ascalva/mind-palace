---
type: build-plan
id: bp-100
track: ops
status: complete
design_ref:
  - docs/design-notes/temporal-code-corpus.md
contract: builder
write_scope:
  - core/stores/vectorstore.py
  - tests/unit/test_vectorstore*.py
  - tests/unit/test_store_cost_ratchet.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 120k
  actual:
    model: opus              # claude-opus-5, single delegated builder in a worktree, session-44
    tokens: 138k             # harness-measured (137,814); 73 tool calls; 36.2 min wall
    ratio: 1.15              # vs 120k — well-pinned; the overrun is the shim investigation, not the code
    session_delta: one delegated builder; Item 1 closed, Items 2–3 PARTIAL — stopped at a capability boundary
    notes: >-
      ⚑ THE PLAN IS complete; ITS OBJECTIVE IS NOT MET. finding-0169 stays OPEN and now points at
      bp-103. Do NOT read this `complete` as "the backfill is unblocked" — supersede_source went
      from 2 full-table materializations to 1 and delete_source from 1 to 0, which moves the wall
      out ~2× rather than removing it. Q3 resolved and INVERTED the plan's premise: the docstring's
      portability claim is FALSE — lancedb 0.33.0 does support in-place Table.update, verified
      empirically. But that surface must cross core/typedshims/lancedb.py per the plan's own §2.6,
      and §5 did not make the shim writable. The builder did not edit it, rejected three in-scope
      workarounds (pyarrow filter, KNN masquerade, local Protocol + cast), and filed finding-0176
      carrying the complete patch — the stop-and-raise contract working as designed. Bonus catch,
      red at HEAD and stash-verified: an id is {doc_id}:{chunk_hash} and doc_id need not equal
      source_path, so the old `id IN (…)` delete could remove ANOTHER PATH'S ROWS — latent data
      loss, now tested. The two ratchets encoding the real bound are committed xfail(strict=True),
      so they XPASS-FAIL the suite when bp-103 lands: a forcing function, not a TODO.
    week_delta: +4%          # weekly 2%→6% across the 3-builder wave spawn→seal (resets Jul 31)
depends_on: []
parallelizable_with:
  - bp-101
  - bp-102
created: 2026-07-25
updated: 2026-07-25
links:
  - docs/findings/finding-0169.md
  - docs/findings/finding-0167.md
  - docs/findings/finding-0168.md
  - docs/brainstorms/ops-and-optimal-form.md
re_entry: null
supersedes: null
superseded_by: null
warrant: docs/findings/finding-0169.md
---

# Build Plan — bp-100: make `supersede_source` cost-independent of store size (the backfill blocker)

## 0. Mode & provenance

Corrective plan, warranted by **finding-0169** — a measured production defect, not a design change.
dn-temporal-code-corpus D2 (keep-and-link) is RATIFIED and its semantics are already proven on the
live store (8,619 `current=false` rows retained). This plan does not touch those semantics; it makes
the implementation able to carry them at history scale. Authority-to-act is the owner's instruction
to plan tonight's build; the readiness blessing (`proposed → ready`) remains owner-only and is not
performed here.

**This plan is the gate on restarting the daemon.** The daemon is deliberately DOWN; `palace up`
before this lands re-arms `code_backfill` into the same wall.

## 1. Objective

Make `supersede_source` (and the reads it depends on) cost a function of the *path's own rows*, not
of total store size, so the history backfill can complete.

## 2. Context manifest

Read in order, whole files before citing:

1. `core/stores/vectorstore.py` — the defect and its blast radius. Note every caller of
   `rows_for_source` / `delete_source` / `all_rows` inside this file before changing any of them.
2. `docs/findings/finding-0169.md` — the measurements (11.7 s per full materialization at 22,621
   rows × 2560 dims; 2 materializations per superseded version; job death at 74m50s / 847 of 1,542).
3. `core/ingest/code_corpus.py` — the caller. `supersede_source` is invoked per changed path
   (`:293`, `:298`); confirm the call shape before optimizing the callee.
4. `docs/findings/finding-0167.md` — predicted the shape ("O(depth) re-land bound owed").
5. `docs/findings/finding-0168.md` — the membership store. Read to ensure this fix does not
   entrench the re-land idiom that f-0168 retires; this is a bridge, not a destination.
6. `core/typedshims/lancedb.py` — the §2.5 boundary shim. Any new LanceDB surface used here must
   pass through it, not around it.

**DRY audit — does `core/` already implement this?** Yes, partially, and it must be reused rather
than re-derived: `search()` (`core/stores/vectorstore.py:248+`) already builds SQL-ish predicate
clauses (`provenance IN (...)`, `current = true`) and passes them to LanceDB rather than filtering
in Python. **The predicate-pushdown idiom already exists in this very class** — the defect is that
`rows_for_source` / `all_rows` do not use it. Reuse that construction; do not invent a second
filtering mechanism. Check also whether `delete_source`'s id-escaping helper can be shared rather
than duplicated.

## 3. Investigation & grounding

- **Q1 — What exactly is quadratic?** `rows_for_source` (`core/stores/vectorstore.py:172`) calls
  `self._table().to_arrow().to_pylist()` over the WHOLE table then filters in Python
  (`:177-178`). `supersede_source` (`:192`) calls it at `:204`, then calls `delete_source` (`:181`)
  at `:208`, which calls `rows_for_source` AGAIN at `:185`. **Two full materializations per call.**
- **Q2 — Is the vector column the cost?** Yes. Measured 11.7 s for 22,621 rows at 2560 dims;
  `sample(1)` of the wedged worker showed the hot stack as pyarrow
  `Array_to_pylist → arrow::FixedSizeListArray::value_slice` — the embedding column — with
  `llama-server` at 0.3% CPU. The cost is Arrow→Python marshalling of vectors, not inference.
- **Q3 — Does LanceDB support an in-place column update at the pinned version?** **Code does not
  settle this.** The `supersede_source` docstring (`:198-199`) asserts delete-then-re-add is used
  "so it stays portable — no dependency on a LanceDB in-place `update`", but that claim is not
  tested and the pinned version is `lancedb>=0.10` (`pyproject.toml:12`). The builder MUST check
  the installed version's API before choosing between (a) in-place update and (b) scoped
  read-modify-write. Do not assume either.
- **Q4 — Can the filter be pushed down safely for arbitrary paths?** The docstring at `:175-176`
  cites "a quoting hazard on arbitrary source paths" as the reason for the Python-side filter.
  `delete_source` (`:187-188`) already solves exactly this by escaping single quotes. **The stated
  reason for the slow path is already refuted by the fast path three lines below it.** Reuse that
  escaping.
- **Q5 — Is `all_rows` on the hot path too?** It is used by `_code_backfill_incomplete`
  (`ops/lifecycle/launcher.py:243`) once per probe, not per version — so it is NOT the quadratic
  term, but it does materialize vectors for a metadata-only comparison. In scope only if the
  column-projection fix is free; otherwise file a follow-up finding rather than widening this plan.
- **Q6 — What is the actual job timeout that killed the backfill?** ~4,490 s observed. **Code does
  not settle this** — grep of `config/defaults.toml` and `scheduler/` did not locate the knob.
  OUT OF SCOPE here (assigned to bp-102); do not chase it.

**Additional risks surfaced during reading:** the migration `_migrate_current_if_needed` (`:109`)
also does a full read-and-re-land. It runs ONCE per store instance and is already complete on the
live store, so it is not a hot path — but it shares the idiom and must not be broken by changes to
the helpers it calls.

## 4. Reconciliation

- `core/stores/vectorstore.py:175-176` — *"Python-side filter (single-user scale; avoids a quoting
  hazard on arbitrary source paths, matching `all_rows`)."* → **banner: correction.** The premise is
  false at history scale and the quoting hazard is already solved at `:187-188`. Replace with a
  docstring stating the pushdown and citing finding-0169.
- `core/stores/vectorstore.py:198-201` — *"the store's portable re-index idiom … no dependency on a
  LanceDB in-place `update`"* → **banner: correction** if Q3 finds in-place update available at the
  pinned version; otherwise **cross-ref: extension** recording that the idiom is retained but scoped
  to the path, with the cost bound now stated and tested.
- `docs/design-notes/temporal-code-corpus.md` D2 — semantics UNCHANGED. No edit proposed (and it is
  ratified ⇒ agent-immutable regardless). This plan is a fidelity repair, not a design change.

## 5. Write scope

- `core/stores/vectorstore.py` — the defect.
- `tests/unit/test_vectorstore*.py` — existing store tests, extended.
- `tests/unit/test_store_cost_ratchet.py` — NEW, the structural enforcement.

Deliberately OUT of scope: `core/ingest/code_corpus.py` (the caller is correct; do not "help" by
changing call sites), `scheduler/**` (bp-101), `ops/lifecycle/launcher.py` (bp-102), every design
note, and the foundation denylist. Do not touch the live store — tests use temp stores only.

## 6. Interfaces pinned inline

Current schema (`core/stores/vectorstore.py`, verified on the live store 2026-07-25):

```
id · digest · title · source_path · chunk_index · provenance · text ·
layer · qualname · line_start · line_end · current · vector
```
`vector` is a `FixedSizeList<float>` of **2560** dims. `current` is `pa.bool_()` (`:59`).

The three methods, verbatim as they stand:

```python
def rows_for_source(self, source_path: str) -> list[dict[str, Any]]:          # :172
    if TABLE not in self._db.list_tables().tables:
        return []
    return [r for r in self._table().to_arrow().to_pylist()
            if r.get("source_path") == source_path]

def delete_source(self, source_path: str) -> None:                            # :181
    rows = self.rows_for_source(source_path)
    if not rows:
        return
    ids = ", ".join("'" + str(r["id"]).replace("'", "''") + "'" for r in rows)
    self._table().delete(f"id IN ({ids})")

def supersede_source(self, source_path: str) -> int:                          # :192
    rows = self.rows_for_source(source_path)
    flipped = sum(1 for r in rows if r.get("current"))
    if flipped == 0:
        return 0
    self.delete_source(source_path)
    for r in rows:
        r["current"] = False
    self.add(rows)
    return flipped
```

The pushdown idiom to REUSE, already in this class (`search`, `:262+`):

```python
clauses.append(f"provenance IN ({allowed})")
# and the escaping idiom, from delete_source:
"'" + str(v).replace("'", "''") + "'"
```

**Contract that must not change:** `supersede_source` returns the number of rows flipped
`current=true → false`; superseded rows are RETAINED; already-superseded rows are unchanged; a path
with nothing current is a no-op returning 0; ids are NOT unique once history is retained (an
unchanged chunk keeps its content-addressed id across versions) — this is why the original deletes
the whole path in one pass. Any new implementation must handle that id collision explicitly.

## 7. Items

Ordered by blast radius: read-only measurement → in-memory correctness → the write path.

### Item 1 — The cost ratchet (write the failing test first)

- **Objective:** A test that fails against today's implementation and passes only when cost is
  independent of unrelated store size.
- **Files:** `tests/unit/test_store_cost_ratchet.py` (new).
- **Acceptance test:** Build a temp store with N rows for path A and M unrelated rows; call
  `supersede_source("A")`; assert the number of rows materialized (or elapsed cost proxy) does not
  grow with M. Run it against the PRE-change module once and show it RED.
- **Falsifier:** The test passes against the *unmodified* implementation — meaning it does not
  actually measure the quadratic term and is theatre. Independent observable: it must go red at
  HEAD before any fix lands.
- **Invariants:** No network; no live store; temp dirs only. Deterministic — assert on rows
  touched / call counts, not wall-clock, or the ratchet will flake on loaded machines.
- **Touches stored data?** No — temp stores only.
- **Parallelizable?** No (gates items 2–3). **Depends on:** none.
- **Falsifier-demo side-effect audit:** the pre-change module's live-action surface is store writes
  only (`add`, `delete`); the demo runs against a temp store, so no live side effect is reachable.
  No network or credential path exists in this module.

### Item 2 — Push the filter down; stop materializing vectors

- **Objective:** `rows_for_source` returns one path's rows via a store-side predicate, and callers
  that only need metadata do not pull the `vector` column.
- **Files:** `core/stores/vectorstore.py`.
- **Acceptance test:** Item 1's ratchet goes green for the read half; existing
  `tests/unit/test_vectorstore*.py` stay green unchanged.
- **Falsifier:** A path containing a quote/space/unicode character returns wrong or zero rows —
  showing the pushdown broke the identity the Python filter got right. Test explicitly with a path
  containing `'`.
- **Invariants:** Return shape unchanged (`list[dict]`); rows still carry every column their
  existing consumers read — verify by grepping consumers before narrowing any projection.
- **Touches stored data?** No.
- **Parallelizable?** No. **Depends on:** Item 1.

### Item 3 — Scope the re-land, or replace it with an in-place flip

- **Objective:** One scan per `supersede_source`, not two; and the flip does not rewrite vectors if
  the pinned LanceDB supports an in-place column update (Q3).
- **Files:** `core/stores/vectorstore.py`.
- **Acceptance test:** Item 1's ratchet fully green; a test asserting `supersede_source` is
  idempotent (second call returns 0 and leaves rows byte-identical) and that already-superseded
  rows are untouched.
- **Falsifier:** Vectors change across a supersede — i.e. a re-land silently re-derives or drops
  embeddings. Assert vector equality before/after, exactly, for every row of the path. (§8 of the
  store's own contract: vectors are carried through the move, never recomputed.)
- **Invariants:** keep-and-link semantics (retained rows, `current=false`); id-collision handling
  across retained versions; the `_migrate_current_if_needed` path still works on a pre-bp-099 store.
- **Touches stored data?** No in tests. **The live store is NOT migrated by this plan** — the
  backfill re-runs after the daemon comes up and is idempotent.
- **Parallelizable?** No. **Depends on:** Item 2.

## 8. Math carried explicitly

- **Cost of `supersede_source`** — *measures:* rows materialized per call as a function of (rows for
  the path `d`, total rows `N`). *valid when:* the store's predicate pushdown is exact, so the
  filtered read returns precisely the path's rows. *fails its keep if:* measured cost still grows
  with `N` at fixed `d` — i.e. the ratchet in Item 1 goes red at any store size. Target: **O(d)**,
  today **O(N)** twice over.

## 9. Non-goals

- **Not** the membership store (finding-0168). This is the bridge that unblocks the backfill; the
  membership rebuild retires this idiom entirely and is a separate design pass.
- **Not** quantization, index tuning, or any change to embedding dimensionality.
- **Not** the job-timeout knob (bp-102), enqueue coalescing (bp-101), or orphan reclaim (bp-101).
- **Not** a live-store migration, and **not** bringing the daemon up. Restart is an owner action
  after all three plans merge.
- **Not** call-site changes in `core/ingest/code_corpus.py`.

## 10. Stop-and-raise conditions

- Q3 resolves to "no in-place update at the pinned version" AND scoping the re-land still leaves
  cost growing with `N` → STOP, file a finding; the answer may be that f-0168 must come first.
- Any consumer is found to depend on `rows_for_source` returning the whole table's rows (i.e. the
  Python filter was load-bearing somewhere) → STOP and surface; that is a spec surprise.
- The vector-equality falsifier (Item 3) fires → STOP. Silently re-derived embeddings are a
  corpus-integrity issue, not a perf bug.
- Any temptation to widen scope into `scheduler/` or `ops/` → file a finding, do not edit.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| In-place update vs scoped re-land | Builder chooses on the Q3 finding, documented in the journal | Assume in-place available (unverified — the docstring claims the opposite); assume it is not (may leave cost on the table) | Q3 answered against the installed LanceDB version, in Item 3 |
| `all_rows` vector projection (Q5) | Leave as-is | Fix it here (widens scope beyond the blocker) | Free to include if the Item 2 projection work covers it; else follow-up finding |
| Retiring the re-land idiom entirely | Keep it, scoped and bounded | Rewrite onto membership now (f-0168 is a design pass, not yet ratified) | f-0168 design pass ratified → the rebuild plan supersedes this code path |

## 12. Dependency & ordering summary

Strictly sequential within the plan: **Item 1 → Item 2 → Item 3.** Item 1 is the ratchet and must be
red before any fix; Items 2 and 3 make it green in two stages (read path, then write path).

Across plans: bp-100 has **no dependencies** and is `parallelizable_with` bp-101 and bp-102 — write
scopes are disjoint (`core/stores/**` here, `scheduler/**` in bp-101, `ops/**` + `config/**` in
bp-102). **bp-100 is the blocker for the daemon restart**; bp-101 and bp-102 are required for the
restart to be *safe* and *observable*, but only bp-100 makes the backfill able to finish.
