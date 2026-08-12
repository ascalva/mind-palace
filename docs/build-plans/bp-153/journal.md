# bp-153 — journal

## Session 1 — 2026-08-12 · builder, worktree `build/bp-153-rebuild-gauges-probe-compaction`

**Base:** `f5306d4` ("docs(bp-152): journal the membership-store build"), verified before any
write. bp-151, bp-155, bp-152 all merged.

**Status: all seven items BUILT. One item's live execution is parked on an owner op and that is
the plan's design, not an incomplete item** — Item 3's machinery is complete and proven on
fixtures; its live run is `palace code-rebuild` after the deploy (re-entry condition below).
Three issues filed (#50, #51, #52); this plan closes #39.

---

### The wedge state observed at build time

`palace queue`, read-only, 2026-08-12: **0 queued · 0 running · 5 deferred** (3 `curate`, 2
`dream`, deferred 15–18 days). Lifetime 534,735 done / 23 failed. **The wedge is drained** — the
D7/S6 owner precondition Item 3 was gated on is satisfied. The live daemon (run #40) deliberately
runs pre-bp-152 code, which is why the live rebuild physically cannot execute until the owner
deploys; issue #39 holds that deploy until this lands.

Corroborating live state, all read-only: `data/memberships.sqlite` **does not exist** (bp-152 is
built but not deployed), the vector store holds **33,861** rows of which **33,823** are CODE and
**zero** are shed atom rows, and the snapshots ledger's newest commit is `bb0caa7`
(2026-07-28) — the ledger is frozen at that cut because the code lane is `enabled=False` on this
machine.

---

### Item 1 — the read-only baseline, RUN FOR REAL against the live store + ledger

The whole point of this item is that the design's economics were measured on a July cut and the
corpus grows, so **the ratio is the portable claim and the absolute counts are not**.

| figure | design (2026-07-27, 1,653 versions) | **measured (2026-08-12, 1,663 versions)** | Δ |
|---|---|---|---|
| Σ per-version chunks (duplicated model) | 52,755 | **52,200** | −1.1% |
| distinct atoms under D0 | 22,502 | **22,897** | +1.8% |
| **ratio** | **2.34×** | **2.280×** | **−2.6%** |
| carry-forward seed | 13,311 (7,791 L0a + 5,520 L0b) | **15,186** (8,681 L0a + 6,505 L0b) | +14.1% |
| embeds avoided | 30,253 | **29,303** | — |

**−2.6% is well inside the ~10% band, so the §8(g) falsifier did NOT fire and Item 3 proceeded on
the blessed economics.** Per lane: L0a **2.55×** (design 2.54×), L0b **2.06×** (2.05×), L1
**1.96×** (2.42× — the one real deviation, filed as #51). The seed is **66.3%** of the atom set
(design projected ~59%).

**Embedder identity — the pin, answered on every axis it has.** `stored_dim=2560` equals the live
`EmbeddingConfig.dim`, and `ledger_mismatched=0`. The `model` is **not recorded on a pre-D1 row** —
structurally: the Arrow schema is shared with the prose lane and has no embedder column, which is
precisely the gap bp-152's `atoms` ledger closes for everything landed hereafter. The report says so
(`unrecorded_rows=15186`) rather than assuming a match. The gap is closed by evidence outside the
store: `config/defaults.toml`'s `model = "qwen3-embedding:4b"` has **exactly one commit in its
entire history** (`7502109`, 2026-06-25), predating the code lane — so no model change can have
occurred under those rows. **Verdict: the seed's geometry is the live one; the carry-forward is
free.**

**Read-only, verified rather than asserted:** the pass ran with a stub embedder that raises if
called; live store rows were **33,861 before and 33,861 after**; `|M|` stayed 0; no
`memberships.sqlite` was created beside the live vault catalog. Runtime 11.9s for 1,663 versions.

⚑ **A trap for a successor:** `get_config()` resolves `data_dir` **relative to the CWD's repo
root**, so running this from a worktree measures the worktree's (empty) store, not the live one.
The first run did exactly that and reported `seed=0` from a 0-row store. Every live measurement
here uses explicit absolute paths. The same hazard is why the `code-rebuild` verb passes
`repo=self.repo_root` rather than taking `build_code_corpus_sync`'s CWD-derived default.

Receipts: `ops/code_rebuild.py:measure_baseline`; `tests/unit/test_code_rebuild.py`
`test_the_baseline_measures_the_factor_and_writes_nothing`.

---

### Item 2 — step 0: the first successful `commit_diffs` capture in the project's history

Confirmed at HEAD before touching anything: the live snapshots db has **zero**
`commit_diffs` / `_commit_diffs_captured` tables. §3 Q1 and panel finding S2 hold — the machinery
has shipped since bp-099 and had never run.

Proven on a **copy**, never the live db (the live daemon owns that file and single-writer is the
invariant). The copy carries the `snapshots` table verbatim in live rowid order — that is the
entire input `ledger_commits`/`supersession_chains` read, so the proof is against the REAL ledger's
commits without a 5 GB duplication or a write handle on the live file.

- **1,377 commits captured in 4 budgeted slices, 18s**, at a deliberately tight 5s budget.
- **2,209 `commit_diffs` rows**, 1,377 marker rows.
- **Re-run captured 0** — idempotence, via the marker table.
- **The R6 falsifier did not fire.** Every slice that hit its budget yielded at a commit boundary
  with its progress already durable. There is no window in which work is done but unrecorded,
  because the durable progress IS `_commit_diffs_captured` — the budget is only ever checked
  *between* commits, each of which is its own transaction. The 300240 `TimeoutError` failure mode
  is bounded, not merely hoped away.

**A real revert exists in this repo's own history**, which is the receipt the F4 dispute wanted:
`ops/lifecycle/launcher.py` re-occupies blob `e09f038e` at run positions **10 and 12**
(non-adjacent) and `281bce1d` at 9 and 11; `tests/unit/test_interpreter_versions.py` likewise.
Adjacent-collapse preserved every one of them; a distinct-collapse would have erased them.

Receipts: `ops/code_rebuild.py:capture_slice`, `pending_commits`;
`tests/unit/test_code_rebuild.py::test_the_sliced_capture_is_idempotent_and_leaves_durable_progress`.

---

### Item 3 — the sliced, checkpointed, resumable rebuild

Built complete: `seed_carry_forward` (bulk embed-reuse by canonical re-hash, zero embedder calls),
`rebuild_slice` (the budgeted walk over every ledger version), `rebuild_step` (the four-phase
machine `capture → seed → land → compact`), and `retire_legacy_rows`.

**Resumability is proven, and proven not to depend on the token.** The acceptance kills a run
mid-slice (a zero budget forces a yield with work already landed — asserted, so it is a real
resume), resumes from the token to completion, and compares against an **independent single-shot
rebuild of the same ledger**: identical `|V|`, identical `|M|`, identical fibers chunk-for-chunk.
Then the token is thrown away entirely and the walk re-run from scratch — **0 new occupancies, 0
embeds** — and again with an unreadable token. Fiber equality holds because derivation is pure, so
the token buys time and nothing else.

**§8(g) is asserted as an EQUALITY, not the inequality the design warns about.** `|atoms| ≤ Σ
chunks` holds vacuously at zero savings; instead the standing `|M|/|V|` gauge must reproduce the
baseline's ratio *exactly*, because `|M|` **is** Σ per-version chunks and `|V|` **is** the distinct
atom count — the same number reached from two independent directions, derived-and-counted before
the run and stored-and-queried after it. The fixture's sharing (across files AND across versions) is
asserted before any ratio is read.

**`retire_legacy_rows` is a decision the plan did not enumerate**, reported separately for exactly
that reason. The rebuild lands the atom plane into the same table as the duplicated rows it
replaces, so both would answer the default current-view search — the dedup would be bought and then
not served. It is a **supersession** (keep-and-link, D2), never a removal: nothing deleted, `|V|`
cannot fall, D5's "purge is the ONE removal" untouched, and reversible by the same update in the
other direction. Flagged in the PR body for the merge audit.

**LIVE RUN — parked, with its re-entry condition:**

> **Wedge drained (observed depth 0 at build); the live rebuild runs post-deploy via
> `palace code-rebuild` — an OWNER op.** The live daemon runs pre-bp-152 code, so the rebuild
> physically cannot execute until the owner deploys (issue #39 holds the deploy until this plan
> merges). Order on the owner's side: merge → `deploy` → `palace code-rebuild --dry-run` to confirm
> the ratio at the then-current cut → `palace code-rebuild` to enqueue. The verb enqueues; the
> daemon drains it as checkpointed BACKGROUND slices. Expected at today's cut: ~22,897 atoms
> landed, ~15,186 of them free by carry-forward, so **~7,700 actual embeds** rather than the
> duplicated model's 52,200.

---

### Item 4 — the frequency-plane gauges (D6)

`n_doc_counts`, `rank_frequency`, `occupied_atoms`, `occupancy_count`, `lane_gauges` on the store;
`frequency_gauges(vectors, memberships) → FrequencyGauges` across the two. Three aggregate queries
plus one server-side row count — **no vector crosses into Python**, which is what makes it
registrable on a cadence rather than an occasional investigation.

The F5 falsifier is exercised on the only input that can see it: `n_doc` and `n_occ` must **differ**
on a duplicate L0b window pair. The pair is asserted to exist as TWO rows with distinct
`chunk_index` inside ONE path *first* — then `n_occ == 2` against `n_doc == 1` (lifetime 6 vs 1) —
and a non-repeated atom is used as the control that makes the inequality mean something. The dedup
factor gets an explicit **control store** where every landing is a fresh atom and the gauge reads
≈1.0; without it "dedup > 1" would establish nothing. `dedup_factor` **is** the D7 falsifier kept
observable forever (the S5 amendment): it fails its keep by sitting at ≈1.0 after a rebuild.

Receipts: `core/stores/memberships.py`; four new tests in `tests/unit/test_memberships.py`.

---

### Item 5 — the probe re-home and the `:139` docstring correction — **closes #39**

`_code_backfill_incomplete` (`ops/lifecycle/launcher.py:374-393`, call site `:551`) counted distinct
`(source_path, digest)` pairs over the code lane. bp-152 shed both columns from atom rows, so
against a rebuilt store every atom row collapses to the single tuple `('','')` and the probe reads
`1 < 1,663` on every daemon start — **enqueueing a backfill forever**. finding-0166's named
falsifier returning through a different door.

The store side now reads `memberships.fibers()`: a version **is** its fiber, so this is the same
number at a sturdier home and the honest form of the F6 re-home. **Only the data source moved** —
cadence, call site, `ingestion.code.enabled` gate and enqueued kind all stand, pinned by its own
test, because a trigger-level change is out of design.

The test builds a genuinely rebuilt store and **computes the old reading beside the new one**,
asserting the old one would have looped (`{('','')}`, `1 < 2`). Without that counterfactual the
assertion is only "the probe says complete", which the un-re-homed code could also produce on some
other input. It also asserts the probe still says INCOMPLETE when a version really is missing —
becoming a constant `False` is the other way to stop the loop, and it is useless.

The `:139` docstring said a chain is "the ordered **distinct** sequence of its blobs" while the code
collapses only **adjacent** repeats — the exact distinction the F4 dispute rests on, so the prose
was contradicting the argument that cites it as evidence. Corrected, with a revert fixture that
computes both readings side by side and a ratchet asserting the contradicting phrase is **absent**
(gaining the word "adjacent" while keeping the wrong claim would otherwise still pass).

---

### Item 6 — compaction and old-version cleanup (§3)

**§3 Q5 resolves to its in-scope case, not the finding.** The capability exists underneath: verified
against the **installed** lancedb 0.33.0 (the bp-103 rule — read the package, not the docs). So
widening the `VectorTable` Protocol was ordinary work, and no finding was owed.

**But the obvious path was wrong, and only running it showed that.** `compact_files` and
`cleanup_old_versions` — the pair the API advertises — are **deprecated as of 0.21.0 and route
through `Table.to_lance()`, which raises `ImportError` without the optional `pylance` package**
(not a dependency of this project). The shim declares **`optimize`** instead: one call, both halves,
supported path, no new dependency. Measured on a 7-version table: **7 → 1 versions, row count
unchanged**.

Acceptance asserts both halves, since either alone is vacuous: row count AND search results
unchanged, **and** the version count actually **dropped** — with the fixture asserted to hold
several dataset versions first, or there is nothing to drop. The firewall gets its own integration
test: compaction and legacy-row retirement are physical rewrites and the firewall is a row
prefilter, so the notes are asserted retrievable before and after (identical hit ids), the code lane
still reachable through its own provenance set, and every row still carrying a non-empty
`provenance`. A firewall that held by deleting the corpus is not a firewall.

---

### Item 7 — `palace code-rebuild`, the owner-visible verb

Listed in `USAGE`, in the module docstring, and dispatched in `main()`; `CODE_REBUILD_KIND` + a
checkpointing handler registered unconditionally in `build_components`. **Wiring is the
deliverable** — a method nothing routes to is not a verb — so the tests read the dispatch out of the
*source* and assert the enqueued kind has a handler.

This is the **first handler in the system to use the queue's checkpoint/resume protocol**, and the
one the protocol was built for: `checkpoint` clears the lease, so a yielded row reads as waiting
rather than orphaned and the next `claim` stamps a fresh **per-batch** deadline — the shape §2.10
requires ("a healthy 14-hour backfill" must not die at hour N on a per-job deadline).

The verb **enqueues**; it never stops the daemon, and a test reads the method's source for the calls
it must not make. `--dry-run` runs Item 1's read-only pass and writes nothing, asserted against a
real seeded ledger with an empty queue afterwards.

---

### Gate (verbatim, run on the final tree)

| leg | result |
|---|---|
| `uv run ruff check .` | **All checks passed!** (exit 0) |
| `uv run mypy core agents eval ops scheduler scripts` | **Success: no issues found in 265 source files** |
| `uv run mypy` (argless) | **Found 69 errors in 20 files (checked 570 source files)** — baseline **UNMOVED** |
| `uv run python -m ops.type_gate` | exit **0** (the one parked psutil report is pre-existing, non-fatal) |
| `uv run pytest -q` | **6 failed, 2515 passed, 15 skipped** in 429s |

The 6 are the five known-red plus one named flake, and nothing else:

1. `tests/e2e/test_dream_v2_live.py::test_dream_v2_synthesizes_grounded_themes_live`
2. `tests/integration/test_worktree_enforcement.py::test_a_deny_cross_worktree`
3. `tests/integration/test_worktree_enforcement.py::test_c_unsafe_direction_narrow_not_loosened`
4. `tests/integration/test_worktree_enforcement.py::test_d_no_pointer_is_no_plan_not_main_fallback`
5. `tests/unit/test_core_self_containment.py::test_core_imports_nothing_outside_core`
6. `tests/e2e/test_scheduler_live.py::test_supervisor_dispatches_a_real_job` — **the named flake**

No new failures.

Two diff-innocence checks, since counts drift and "trust the run" cuts both ways:
- The argless baseline first read **71**. Both extra errors were **mine**, in
  `tests/unit/test_code_rebuild.py` (a generator fixture annotation and a `str | None` assignment).
  Fixed → **69**, exactly the pinned baseline. My changes contribute zero.
- The self-containment ratchet reports **20 forbidden imports**, and **none are in a file I
  touched** (`core/stores/vectorstore.py`, `core/stores/memberships.py`,
  `core/typedshims/lancedb.py` do not appear). `core/ingest/code_corpus.py:87 → ops` is bp-152's
  pre-existing reach.
- `test_scheduler_live` constructs its own `Supervisor` with `handlers={"ping": handler}` — it never
  calls `build_components`, so the handler I registered cannot reach it. Its failure is an empty
  response from a live model.

---

### Write-scope amendment (made in-branch, commit `dbf6ae2`)

Added **`ops/lifecycle/launcher.py`** (Item 5's entire target — the probe at `:374-393` and its call
site at `:551` — plus Item 7's `Launcher` method and handler registration) and
**`scheduler/code_sync.py`** (the job kind + checkpointing handler the verb enqueues, placed beside
its two siblings rather than in a new module that splits one lane across two homes). Bare globs, no
inline comments. Status field untouched. **Third instance this wave** → issue #52 proposes deriving
`write_scope` from the items' own `file:line` citations instead of restating it by hand.

---

### In-flight

Nothing. All seven items are built and the branch is gate-green.

### Next action

Owner reviews and merges the PR. Then, in order: `deploy` (which #39 has been holding) →
`palace code-rebuild --dry-run` to re-confirm the ratio at the then-current cut →
`palace code-rebuild` to enqueue the live run.

### Open questions

- **#50 — D4/F3 is falsified on the real ledger.** "Chain members are a strict subset of the version
  set" is not true of the shipped reader: measured **1,663 versions, 1,663 chain members, an empty
  difference both ways**. The reasoning assumed chains follow HEAD's first-parent line; they do not
  — `capture_commit_diffs` is handed *every* snapshotted commit, each diffed against **its own**
  first parent, so a side branch's own linear history is captured too. Nothing in the code relies on
  the strict-subset reading and the rebuild is correct either way, but §4 quantifies invariants with
  that clause and F3's disposition rests on it. A note amendment is not a builder's hand.
- **#51 — D7's L1 lane figure is 19% off the shipped chunkers** (2.42× noted, **1.96×** measured)
  while the aggregate holds at −2.6%. The L1 *atom* count matches (3,482 vs 3,424); the *chunk*
  count is 17.6% lower than the note's probe produced. Exactly the shape Amendment A1.4 warns about
  — small enough to be invisible in the total, in the number the design uses to prove itself.
- **#52 — `write_scope` omits files the plan's own items cite by `file:line`**, third instance.
- **#18 stays OPEN** (the `code_sync` TimeoutError wedge). The slicing addresses its failure mode
  and Item 2 demonstrates the bound, but it closes when the **live** capture succeeds post-deploy,
  not when the machinery lands.
- **The derived board is stale by ~34 rows** (bp-128…bp-150, bp-154, the erratum-relation track).
  `scripts/board.py --write` was run, produced 34 lines of unrelated catch-up, and was **reverted**
  — that drift belongs to a `/triage` sweep, not to this PR. Flagged so it is not lost.

### Context-manifest delta

Read beyond §2, and worth a successor's time:
- `scheduler/queue.py:395-434, 545-560` — the `claim`/`checkpoint` lease protocol. Essential: this
  plan is its first consumer, and the per-batch-vs-per-job deadline distinction is the whole reason
  a long rebuild is safe.
- `scheduler/supervisor.py:280-297` — the dispatch seam. "Complete only if still RUNNING after the
  handler returns" is what makes a self-checkpointing handler yield rather than finish.
- `docs/tracks/code-ingest.md` + `scripts/board.py` — the deskcheck queue is **generated**, so the
  statement goes in the manifest's `backlog_deskcheck`, never by hand-editing the view.
- `tests/unit/test_memberships.py:545-572` — bp-152's `degenerate` fixture already carries all four
  §8(f) shapes. Item 4's gauges reuse it rather than build a fifth.

### Read-map (where a successor starts)

1. `ops/code_rebuild.py` — the whole rebuild, module docstring first: it names the four movements
   and, more usefully, says what the resume token **is not**.
2. `tests/unit/test_code_rebuild.py` — every acceptance with its degenerate input named in the
   docstring and its precondition asserted first.
3. `docs/design-notes/vector-membership-store.md` D6/D7/§3/§6/§8(g) — the contract, read against
   issues #50 and #51, which are where it stopped matching the code.

### Follow-through

- **Built?** Yes — all seven items.
- **Wired/delivered?** Yes. `palace code-rebuild` is listed, dispatched, its kind is registered on
  the daemon, and `--dry-run` runs the read-only pass. The ON path exists, not merely the code
  behind it.
- **Consumer?** The owner, via the verb; the daemon's catch-up probe, which now reads fibers; and
  the standing `frequency_gauges`, which keep `|M|/|V|` — the D7 falsifier — observable forever
  rather than measured once.
- **Track state?** The **vector-membership arc** (bp-151 → bp-155 → bp-152 → bp-153) is **READY TO
  DESKCHECK** on this merge, filed into `docs/tracks/code-ingest.md`'s `backlog_deskcheck` (the
  generated queue's actual source). **Not done, and not self-declared** — the arc's closing act is
  the live rebuild, which is the owner's. The rest of the code-ingest track (bp-095, the seed run,
  integrator densification) remains **work-owed**, not deskcheck-owed.
- **New findings?** #50 (F3 falsified by measurement), #51 (the L1 figure), #52 (`write_scope`
  derivation). One defect found by an acceptance test and fixed in-branch: `pending_commits` called
  `_ensure_schema` before reading — a `CREATE TABLE` that raises on a `mode=ro` connection and
  silently mutates the file otherwise. The dry-run reads the LIVE ledger, where those tables have
  never existed, so this was the ordinary path, not a corner. Now ratcheted.
