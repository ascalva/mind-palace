---
type: build-plan
id: bp-153
track: code-ingest
status: proposed
design_ref:
  - docs/design-notes/vector-membership-store.md
contract: builder
write_scope:
  - ops/code_rebuild.py
  - ops/code_lineage.py
  - core/stores/memberships.py
  - core/stores/vectorstore.py
  - core/typedshims/lancedb.py
  - core/ingest/code_corpus.py
  - scripts/palace.py
  - tests/unit/test_code_rebuild.py
  - tests/unit/test_code_lineage.py
  - tests/unit/test_memberships.py
  - tests/integration/test_code_mirror.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 500k
  actual: null
depends_on: [bp-152]
parallelizable_with: []
created: 2026-08-01
updated: 2026-08-01
links:
  - docs/design-notes/temporal-code-corpus.md
  - docs/findings/finding-0168.md
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — the rebuild, the frequency gauges, the probe re-home, compaction (D6/D7/§3/§6)

## 0. Mode & provenance

Graduated from `dn-vector-membership-store` D6, D7, §3 (wiring + physical maintenance) and
§6 (the probe re-home) on 2026-08-01 under the owner's "graduate now, merge = blessing"
ruling (issue #27). Investigation and planning produced this plan; implementation proceeds
item-by-item. Citations re-opened against HEAD `174d06c`.

Third of three plans. **Depends on bp-152** — there must be a lander to rebuild into and a
membership relation for the gauges to count.

**This plan has an operational precondition that is the owner's, not the builder's** (§10):
the wedge-clearing and backlog drain (D7/S6). The builder does not clear the wedge.

## 1. Objective

Rebuild the code corpus once into the atom+membership model, sliced and resumable, and
leave standing gauges that keep the dedup factor observable forever.

## 2. Context manifest

Read in order:

1. `docs/design-notes/vector-membership-store.md` — D6, D7, §3, §6, §8(g), R5, R6.
2. `docs/build-plans/bp-152/plan.md` — the lander and membership store this rebuilds into;
   its §6 interfaces (especially the embedder pin) are this plan's inputs.
3. `ops/code_lineage.py` — whole file. `capture_commit_diffs` (`:112-130`) is **step 0**.
4. `ops/code_snapshot.py` — the ledger walk (`:353-360`) that defines the version set.
5. `docs/design-notes/temporal-code-corpus.md:141-143` and `:125-126` — the two passages the
   §6 re-homes correct; the amendment banners them, this plan re-homes the mechanism.
6. `core/stores/vectorstore.py` — for the compaction path that does not yet exist.
7. `scripts/palace.py` — where `code-rebuild` is wired as an owner-visible verb.

## 3. Investigation & grounding

- **Q1 — Has `commit_diffs` ever been captured?** No. The note verified zero
  `commit_diffs` / `_commit_diffs_captured` tables in the live snapshots db (read-only,
  2026-07-27), and the one capturing job (300240) died in `TimeoutError` on 2026-07-25.
  The machinery is shipped but **never successfully run** — `capture_commit_diffs`
  (`ops/code_lineage.py:112-130`). This is genuinely step 0: nothing downstream of it has
  ever executed against real data.
- **Q2 — Is the capture idempotent, so a sliced/resumed run is safe?** Yes. It skips
  already-captured commits via the `_commit_diffs_captured` marker and uses
  `INSERT OR IGNORE` under a `with db:` transaction per commit (`:119-129`), returning the
  count newly captured. A re-run captures nothing new — including for an empty-diff merge.
  This is what makes a per-slice time budget safe.
- **Q3 — What defines the version set the rebuild walks?** `backfill` walks
  `rev-list --reverse HEAD` — **all** commits (`ops/code_snapshot.py:353-360`) — while
  chains are first-parent (`code_lineage.py:85-95`). So chain members are a strict subset of
  ledger versions (D4/F3): a side-branch version lands a fiber but sits on no chain. The
  rebuild must land fibers for **every** ledger version, not only chain members.
- **Q4 — Does a rename appear as a rename to the capture?** No — deliberately. `-M` is not
  passed, so "renames come back as a delete row + an add row" (`code_lineage.py:86-89`,
  PD-1), and a rename's add starts the new path's own chain (`:139`). Under D0 this is
  exactly right: the new path's fiber references the *same* atoms, so the rename costs
  0 embeds and lineage crosses via the shared atoms rather than via a rename edge.
- **Q5 — Does a compaction path exist in `vectorstore.py`, and can the shim express one?**
  No, on both counts — and the note's "if the shim lacks the API, that is a finding" needs
  splitting into two cases, because only one of them is a finding.
  - `vectorstore.py` has no compaction or version-cleanup method (verified).
  - The typed shim `core/typedshims/lancedb.py` (`vectorstore.py:22` imports
    `VectorTable, connect` from it) declares `VectorTable` as a Protocol with exactly
    `add`, `count_rows`, `delete`, `update`, `to_arrow`, `search`, `scan` (`:82-97`) —
    **no compaction member**. The shim is *our* code, so adding a Protocol member is
    ordinary in-scope work, **not** a finding; `core/typedshims/lancedb.py` is in
    `write_scope` for exactly this reason.
  - The finding case is narrower and real: **the code does not settle whether the pinned
    lancedb release exposes compaction / old-version cleanup at all.** What would settle it
    is reading the installed lancedb surface at build time. If the capability is absent
    underneath, widening the Protocol cannot conjure it — *that* is the finding (§10).
- **Q6 — What is the measured target the rebuild must hit?** From D7, re-derived
  2026-07-27 over all 1,653 ledger versions: **52,755** embeds under the duplicated model
  vs **22,502** atoms under membership+D0 = **2.34×** (L0a 2.54× · L0b 2.05× · L1 2.42×).
  Carry-forward seed: **13,311** atoms (7,791 L0a + 5,520 L0b) already embedded with embed
  text unchanged; **L1 recuts under D0's windowing pin and re-embeds** (3,424 atoms).
- **Q7 — Is the live store's own duplication consistent with that?** The note measured
  22,621 rows / 16,761 distinct `(layer, text)` = 1.35× *today*. Live `palace status`
  on 2026-08-01 reports **33,861 vector rows** — the store has grown since the measurement.
  **The code does not settle whether the 22,502 target still holds at the current ledger
  cut**; what would settle it is re-deriving the figure at rebuild time, which Item 1 does
  before any write.

**Additional risks or questions surfaced during reading:**

- **The falsifier's baseline is a moving target.** §8(g) pins "the 2026-07-27 ledger cut".
  Since the corpus grows, the rebuild must compare **like-for-like at its own cut** — the
  ratio (≈2.34×), not the absolute 22,502, is the portable claim. Item 1 re-derives both.
- **`reference_edges` scale is 8.4× stale in the docstrings** (open issue #28: docstrings
  say ~272k edges, the live store holds 2,284,272). Not this plan's write scope, but it is
  the same *class* of defect this plan must not commit — every figure this plan writes into
  a docstring or gauge must be a query, not a constant.
- **The daemon must not be stopped.** D7 is explicit: the rebuild runs as background queue
  jobs with checkpoint resume tokens, respecting single-writer as a queue citizen. The job
  class it enlarges is exactly the one that wedged (`code_sync`, and the live daemon shows
  a `code_sync` TimeoutError as its most recent failure — issue #18 tracks it).

## 4. Reconciliation

- `docs/design-notes/temporal-code-corpus.md:141-143` — the §3 incompleteness probe reads
  "the store's distinct code-digest count" → **[banner: correction]** on the parent note,
  carried by the amendment commit in the graduation PR (**not** by this plan — the note is
  out of `write_scope`). The `digest` column leaves atom rows, so the probe re-homes to the
  membership store's distinct `(path, blob_sha)` fiber count — the same number, a sturdier
  home. **The backfill TRIGGERS stand unchanged; only the probe's data source moves.** The
  mechanical re-home is §7 Item 5 of this plan.
- `docs/design-notes/temporal-code-corpus.md:125-126` — D5's supersession-edge endpoints
  "resolvable **by digest in the vector store**" → **[banner: correction]**, same vehicle.
  Endpoints re-home to fiber existence: endpoint resolvable ⇔ `M(path, blob)` is non-empty
  (F6).
- `ops/code_lineage.py:139` — the `supersession_chains` docstring says a chain is "the
  ordered distinct sequence of its blobs" → **[banner: correction]**. The behavior collapses
  only **adjacent** repeats (`:151-156`), so `[A, B, A]` is preserved and a revert stays
  visible. The docstring is loose language, not the behavior — and since the note's F4
  dispute rests on this exact distinction, the docstring must stop contradicting the code.
  A one-line correction, carried by §7 Item 5.
- `core/stores/vectorstore.py` — **[cross-ref: extension]**: the compaction path is new
  surface, not a correction. It links §3 of the note as its warrant.

## 5. Write scope

Production files:

- `ops/code_rebuild.py` — **new**. The sliced, checkpointed, resumable rebuild.
- `ops/code_lineage.py` — the step-0 capture is invoked here; the `:139` docstring
  correction lands here.
- `core/stores/memberships.py` — the gauge queries (`n_doc`, `n_occ`, `|M|/|V|`) and the
  re-homed probe's fiber count.
- `core/stores/vectorstore.py` — the compaction + old-version cleanup path (§3), which does
  not exist today (§3 Q5).
- `core/ingest/code_corpus.py` — only if the carry-forward re-hash needs a derivation hook;
  named so the builder is not denied mid-slice.
- `scripts/palace.py` — the owner-visible `code-rebuild` verb. (Note: `down`/`up`/`restart`/
  `deploy` live here, **not** on the `mind-palace` wrapper.)

Test files carried: `tests/unit/test_code_rebuild.py` (new),
`tests/unit/test_code_lineage.py` (pins chain behavior + the corrected docstring),
`tests/unit/test_memberships.py` (gauges join the membership tests),
`tests/integration/test_code_mirror.py` (the firewall must survive a rebuild).

Deliberately **out of scope**: `docs/design-notes/**` (the amendment travels in the PR as
its own commit, never from a builder's hand), the note lane (PD-2 — prose rows are not
migrated, R5), `core/kernel/**`, and the fixed points (`CONSTITUTION.md`, `eval/golden/**`,
`eval/golden.py`).

## 6. Interfaces pinned inline

**Step 0 — the capture, current form `ops/code_lineage.py:112-118` (shipped, never
successfully run):**

```python
def capture_commit_diffs(db: sqlite3.Connection, repo: Path, commits: list[str]) -> int:
    """Capture first-parent `git diff-tree` deltas for `commits` into `commit_diffs` (D4).
    Idempotent per commit via the `_commit_diffs_captured` marker: an already-captured commit
    (including an empty-diff merge) is skipped, so a re-run — or the incremental sync re-passing the
    same commits — captures nothing new. Returns the number of commits newly captured. The ONLY
    writer of `commit_diffs`; derives from git + the ledger, never re-interpreting φ_code's rows."""
```

**The ledger walk that defines the version set, `ops/code_snapshot.py:353-360`:**

```python
def backfill(db: sqlite3.Connection, repo: Path) -> int:
    """Snapshot every commit on the current branch, oldest first. Idempotent."""
    done = 0
    cache: dict[str, FileShape] = {}
    for sha in _git(repo, "rev-list", "--reverse", "HEAD").splitlines():
        if snapshot_commit(db, repo, sha, _cache=cache):
            done += 1
    return done
```

**The chain threading whose adjacent-collapse preserves a revert, `ops/code_lineage.py:150-157`:**

```python
    chains: dict[str, list[str]] = {}
    for path, old_blob, new_blob in rows:
        chain = chains.setdefault(str(path), [])
        if not chain and old_blob:
            chain.append(str(old_blob))
        if new_blob and (not chain or chain[-1] != new_blob):
            chain.append(str(new_blob))
    return {p: c for p, c in chains.items() if c}
```

**D6 — the two counts, never conflated (the F5 pin):** `n_doc(v)` = distinct current paths
holding `v` — the document-frequency/IDF reading, immune to within-file repetition, and the
histogram's default; `n_occ(v)` = membership rows — the multiset reading, where L0b's
repeated windows count. Both current-cut and lifetime variants defined. Standing gauges: the
**n_doc(v) histogram** per lane and over time, **plus the dedup factor `|M|/|V|` and
embeds-avoided per landing**. `|M|/|V|` **is** the dedup factor, so the D7 falsifier stays
observable forever.

**D7 — the measured targets (re-derived 2026-07-27 over all 1,653 ledger versions):**

| figure | measured value |
|---|---|
| full history, duplicated model | **52,755** embeds (Σ per-version chunks) |
| full history, membership + D0 | **22,502** atoms = **2.34×** (L0a 2.54× · L0b 2.05× · L1 2.42×) |
| carry-forward seed | **13,311** atoms (7,791 L0a + 5,520 L0b) already embedded, embed text unchanged |
| L1 | recuts under D0's windowing pin and **re-embeds** (3,424 atoms) |
| live store at graduation | 33,861 vector rows (`palace status`, 2026-08-01) — grown since the measurement |

**The embedder pin (carried from bp-152 §6, owner-confirmed 2026-08-01).** The carry-forward
seed is a **bulk embed-reuse**, so it is governed by the pin: an atom's stored vector is
reusable only if the embedder identity that produced it matches the live
`EmbeddingConfig.model` + `dim` (`core/kernel/config/loader.py:138-141`). If the embedder has
changed since those 13,311 rows landed, **the seed is not free** — it must re-embed, and the
rebuild's cost estimate changes accordingly. Item 1 checks this before Item 3 spends anything.

**D7 slicing:** the rebuild runs as **BACKGROUND jobs** with `jobs.checkpoint` resume tokens
and a **per-slice time budget**, respecting single-writer as a queue citizen — **no daemon
stop**. The job class it enlarges is exactly the one that wedged.

**§3 physical maintenance:** `current_any` stays in lance (the ANN prefilter needs it);
flips are batched per landing (only atoms crossing 0↔1 — typically zero to few rows); the
rebuild ends with compaction + old-version cleanup; housekeeping runs cleanup on cadence.
Measured 2026-07-27: 298 dataset versions, 245 MB on disk vs ~232 MB raw payload
(22,621 rows × 2560 dims × 4 B) — modest bloat; the panel's ~2.4× figure did not survive
re-measurement (owner-confirmed 2026-08-01).

## 7. Items

### Item 1 — re-derive the baseline before spending anything (read-only)

- **Objective:** the rebuild's target and cost are computed at the *current* ledger cut, not
  inherited from a July constant.
- **Files:** `ops/code_rebuild.py`, `tests/unit/test_code_rebuild.py`
- **Acceptance test:** a read-only pass reports, at the current cut: Σ per-version chunks
  (the duplicated-model count), the distinct atom count under D0, their ratio, the
  carry-forward seed size, and **whether the seed's embedder identity matches the live
  config**. No store is written.
- **Falsifier:** the ratio deviates from **2.34×** by more than ~10% like-for-like. Per
  §8(g) that is a **finding, not a shrug** — it means D0's dedup did not materialize and
  the rebuild should not proceed on its projected economics. Also falsified if the pass
  writes anything.
- **Invariant(s) it must not violate:** read-only. Every figure is a query; no measured
  constant is hardcoded into a docstring (the issue #28 defect class).
- **Touches stored data?** No — this is the dry-run that precedes every later item.
- **Parallelizable?** No. **Depends on:** bp-152.

### Item 2 — step 0: the first successful `commit_diffs` capture

- **Objective:** `commit_diffs` and `_commit_diffs_captured` exist and are populated — for
  the first time ever.
- **Files:** `ops/code_rebuild.py`, `tests/unit/test_code_lineage.py`
- **Acceptance test:** after a sliced run, `commit_diffs` is non-empty and re-running
  captures **0** new commits (idempotence, `:119-129`). Chains derived from it reproduce a
  known revert as `[A, B, A]` — 3 runs, 2 edges.
- **Falsifier:** the capture times out again (the 300240 failure mode, `TimeoutError`,
  2026-07-25) — meaning the slicing did not actually bound the work, and the design's
  central operational claim is unproven. A slice that exceeds its budget **without leaving a
  checkpoint** is the R6 falsifier and must stop the run.
- **Invariant(s) it must not violate:** idempotent per commit; the ONLY writer of
  `commit_diffs`; derives from git + ledger, never re-interpreting φ_code's rows.
- **Touches stored data?** Yes — writes the snapshots db. Idempotent and additive; verify
  on a copy first.
- **Parallelizable?** No. **Depends on:** Item 1.

### Item 3 — the sliced, checkpointed, resumable rebuild

- **Objective:** the corpus is rebuilt into atoms+memberships as background queue jobs
  without wedging the lane.
- **Files:** `ops/code_rebuild.py`, `core/stores/memberships.py`,
  `core/ingest/code_corpus.py`, `tests/unit/test_code_rebuild.py`
- **Acceptance test:** **§8(g)** — the rebuild lands ≈ the atom count Item 1 derived, against
  the duplicated model's count, within ~10% like-for-like. Each slice checkpoints; killing
  the run mid-slice and resuming completes without double-landing (fiber equality holds
  because derivation is pure). The carry-forward seed enters by canonical **re-hash** of
  stored rows at zero embed cost **only if** the embedder identity matches (§6); L1
  re-embeds.
- **Falsifier:** "|atoms| ≤ Σ chunks" alone is **not** acceptance — it holds vacuously at
  zero savings (the false-success shape). The measured **factor** is the claim under test.
  Additionally: any slice exceeding its budget without a checkpoint (R6), or the queue depth
  growing without bound behind the rebuild (the wedge reproduced).
- **Invariant(s) it must not violate:** **the old duplicated backfill is never run** —
  52,755 vs 22,502 is 2.34× measured waste. No daemon stop; single-writer respected. Note
  rows are **not** migrated (PD-2/R5). Append-only: `|V|` never decreases.
- **Touches stored data?** **Yes — this is the plan's irreversible item.** Requires Item 1's
  dry-run to have passed, and a verified backup/restore path before the real write.
- **Parallelizable?** No. **Depends on:** Items 1, 2.

### Item 4 — the frequency-plane gauges (D6)

- **Objective:** `n_doc`, `n_occ`, `|M|/|V|`, and embeds-avoided are standing, queryable
  gauges.
- **Files:** `core/stores/memberships.py`, `tests/unit/test_memberships.py`
- **Acceptance test:** on the §8(f) degenerate fixture (a revert, a merge side-branch, a
  shared atom, a duplicate L0b window pair): `n_doc` and `n_occ` **differ** on the duplicate
  L0b pair — `n_occ` counts both, `n_doc` counts one path. `|M|/|V|` reproduces the fixture's
  known dedup factor. The rank-frequency histogram of lifetime `n_doc(v)` renders.
- **Falsifier:** `n_doc` and `n_occ` return the same number on the duplicate-window fixture
  — the two counts have been conflated, which is exactly the F5 defect the pin exists to
  prevent. A fixture without a duplicate L0b pair cannot see this, so the fixture
  precondition is asserted first.
- **Invariant(s) it must not violate:** `current_any(v) ⇔ n_doc(v, t) > 0`. Gauges are
  read-only and cheap. Zipf conformance is **checked, never assumed** (T2/T4).
- **Touches stored data?** No.
- **Parallelizable?** Yes, with Item 5. **Depends on:** Item 3.

### Item 5 — the §6 probe re-home and the `:139` docstring correction

- **Objective:** the incompleteness probe reads fiber counts, and the chain docstring stops
  contradicting the chain code.
- **Files:** `core/stores/memberships.py`, `ops/code_lineage.py`,
  `tests/unit/test_code_lineage.py`
- **Acceptance test:** the probe's count equals the membership store's distinct
  `(path, blob_sha)` fiber count, and on a corpus where the old digest-based count was
  correct, the two agree — "the same number, a sturdier home". The `:139` docstring says
  *adjacent*, and a test asserts `[A, B, A]` survives.
- **Falsifier:** the backfill **triggers** change behavior. Only the probe's *data source*
  moves; the triggers stand unchanged (§6). Any trigger-level change is out of design.
- **Invariant(s) it must not violate:** endpoint resolvable ⇔ `M(path, blob)` non-empty (F6).
  The catch-up probe keeps its cadence and its meaning.
- **Touches stored data?** No.
- **Parallelizable?** Yes, with Item 4. **Depends on:** Item 3.

### Item 6 — compaction and old-version cleanup (§3)

- **Objective:** the lance dataset's version accumulation is bounded.
- **Files:** `core/stores/vectorstore.py`, `core/typedshims/lancedb.py`,
  `tests/unit/test_code_rebuild.py`
- **Acceptance test:** after the rebuild, compaction + old-version cleanup runs and the
  dataset version count drops measurably; row count and search results are **unchanged**
  (compaction removes no logical row).
- **Falsifier:** any logical row disappears, or search results change — compaction must be
  semantically invisible. Note the two cases of §3 Q5: widening the `VectorTable` Protocol
  (`core/typedshims/lancedb.py:82-97`) to declare a compaction member is **in-scope work**;
  discovering that the pinned lancedb release has no such capability underneath is **a
  finding at build**, never an improvised physical rewrite.
- **Invariant(s) it must not violate:** append-only — compaction is physical, never logical.
  `current_any` stays in lance (the prefilter needs it).
- **Touches stored data?** Yes — physical rewrite. Verify row-count and search equality
  before and after.
- **Parallelizable?** No. **Depends on:** Item 3.

### Item 7 — `palace code-rebuild`, the owner-visible verb

- **Objective:** the enable act exists as a runnable, owner-visible command.
- **Files:** `scripts/palace.py`, `tests/unit/test_code_rebuild.py`
- **Acceptance test:** `code-rebuild` appears in the verb listing and runs the sliced
  rebuild with a `--dry-run` that performs Item 1's read-only pass and writes nothing.
- **Falsifier:** the verb exists but the switch is not wired — the flag-off-is-not-done
  failure. Wiring **is** part of the deliverable: the ON path must exist, not merely the
  code behind it.
- **Invariant(s) it must not violate:** the verb never stops the daemon; it enqueues.
  `deploy` remains the separate owner-in-loop gate and is untouched.
- **Touches stored data?** No directly — it enqueues work that does.
- **Parallelizable?** No. **Depends on:** Items 3, 6.

## 8. Math carried explicitly

- **`n_doc(v)` — document frequency** — *measures:* the number of distinct current paths
  holding atom `v`; the IDF reading. *valid when:* counted over **distinct paths**, so
  within-file repetition cannot inflate it; current-cut and lifetime variants kept separate.
  *fails its keep if:* it equals `n_occ(v)` on a corpus containing any repeated window —
  the two readings have been conflated (F5).

- **`n_occ(v)` — occupancy multiplicity** — *measures:* membership rows referencing `v`; the
  multiset reading. *valid when:* the membership key `(path, blob_sha, layer, chunk_index)`
  keeps duplicate windows as distinct rows. *fails its keep if:* it never exceeds `n_doc` on
  a corpus with duplicate L0b windows — the multiset honesty was lost at the key.

- **The dedup factor `|M|/|V|`** — *measures:* occupancies per atom — how much reuse the
  membership model is actually buying. *valid when:* `|M|` counts occupancies and `|V|`
  counts atoms at the same cut. *fails its keep if:* it sits at ≈1.0 after a full rebuild —
  the model bought nothing and D7's economics are false. It **is** the D7 falsifier, kept
  observable forever rather than measured once.

- **The rank-frequency histogram of lifetime `n_doc(v)`** — *measures:* the corpus's
  vocabulary shape; Zipf conformance is a falsifiable corpus property. *valid when:*
  computed per lane, and **checked rather than assumed** (T2/T4). *fails its keep if:*
  deviation localizes nothing real — if a shape anomaly never corresponds to boilerplate
  consolidation or vocabulary flux, the gauge is decoration and should be cut.

## 9. Non-goals

- **The builder does not clear the wedge or drain the backlog** — an owner op (D7/S6), and
  a precondition for Item 3, not work for this plan.
- **The old duplicated backfill is never run.**
- **No notes-lane migration (PD-2/R5)** — the builder must not "helpfully" migrate prose.
- **No design-note edits** — the §6 amendment travels in the graduation PR as its own
  commit; this plan re-homes the *mechanism* only.
- **No IDF-weighted ranking (PD-4)** — gauges only; no retrieval-ranking change.
- **No materialized edge table (PD-3), no L1 re-slotting (PD-5), no embedder change, no ANN
  tuning, no logical pruning.**
- **No `deploy`.** Promoting a run onto HEAD is the owner's gate and is never run
  autonomously.

## 10. Stop-and-raise conditions

- **The wedge is not clear / the backlog is not drained** — Item 3 must not start. Park it
  with the re-entry condition "wedge cleared and backlog drained (owner op)" and continue
  Items 1, 2, 4, 5 where their own dependencies allow. Never block the whole session on it.
- **The Item 1 ratio deviates >~10%** — a finding (§8 g), not a shrug. File the issue, park
  Item 3, continue.
- **The embedder identity does not match the carry-forward seed** — the rebuild is far more
  expensive than projected. Raise before spending; this changes the economics the owner
  blessed.
- **A slice exceeds its budget without a checkpoint** (R6) — stop the run. This is the live
  wedge failure mode reproducing.
- **The typed lancedb shim lacks a compaction API** (§3 Q5) — file a finding; do not
  improvise a physical rewrite against an unpinned surface.
- **Any need to stop the daemon** — the design forbids it; a rebuild that requires it is a
  spec defect.
- The builder performs **no blessing, no status flip, no `deploy`**, and never writes the
  fixed points.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| Note-row migration | Prose rows stay on the old path until PD-2; the builder settles which is mechanically smaller **only if trivially so**, else parks | Migrate prose in this rebuild — rejected: R5 scope creep, and the D1 stratum fence is not yet redesigned | PD-2 opens (notes keep-and-link lands + prefilter redesigned) |
| IDF-weighted retrieval (PD-4) | Gauge only; no ranking change | Wire `n_doc` into ranking now — rejected as unmeasured | A T4 retrieval-quality experiment shows lift |
| Compaction cadence | Rebuild ends with compaction; housekeeping runs cleanup on cadence | Compact on every landing — rejected: flips are batched and typically touch few rows; per-landing compaction would cost more than it saves | Measured version growth outpaces the housekeeping cadence |
| Materialized slot-edge view (PD-3) | Derived on read | A stored edge table — rejected: second source of truth | A consumer needs edge queries at a rate joins cannot serve |

## 12. Dependency & ordering summary

**Gated on bp-152**, and Item 3 additionally gated on an **owner operation** (wedge cleared,
backlog drained) that no builder performs.

Blast-radius order is strict and is the spine of this plan:

1. **Item 1** — read-only baseline. Writes nothing. Everything downstream depends on its
   numbers.
2. **Item 2** — step 0 capture. Additive and idempotent.
3. **Item 3** — the rebuild. **The irreversible item**, gated on 1 + 2 + the owner op.
4. **Items 4 and 5** — gauges and probe re-home. **Parallelizable with each other**;
   both read-only; both depend on Item 3 having produced a store to measure.
5. **Item 6** — compaction. Physical rewrite, after the rebuild.
6. **Item 7** — the owner-visible verb, last: it wires what Items 3 and 6 built.

If Item 3 parks on the owner op, Items 1, 2 still complete and Items 4–7 park behind it —
the session ends at that boundary with a journal, rather than blocking.

**Cross-plan:** this is the last plan of the family. On its completion the track is **ready
to deskcheck**, not done — the deskcheck is the owner's, and it is filed into
`docs/DESKCHECK-QUEUE.md` rather than self-declared.
