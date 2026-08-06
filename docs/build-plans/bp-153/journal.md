# bp-153 — journal

## Pre-build notes for whoever picks this up

- ⚑⚑ **The old duplicated backfill must NEVER be run.** 52,755 embeds vs 22,502 atoms is
  **2.34× measured waste** (D7). This is not "prefer the new path" — it is a prohibition. The
  one historical attempt (job 300240) died in `TimeoutError` on 2026-07-25 and left
  `_code_corpus_backfilled` at 0 rows.

- ⚑⚑ **Clearing the wedge and draining the backlog is an OWNER op — you do not do it.** It
  gates Item 3 only. If it is not done, **park Item 3 with its re-entry condition and
  continue Items 1, 2** — never block the session on an owner action. (Standing rule: never
  block on the owner; only a `blocker` finding ends a session early, and the Stop gate still
  wants a fresh journal.)

- ⚑⚑ **Never stop the daemon.** D7 is explicit: the rebuild runs as background queue jobs
  with `jobs.checkpoint` resume tokens and a per-slice time budget, respecting single-writer
  as a queue citizen. A rebuild that requires a daemon stop is a spec defect, not an
  operational choice. Note the job class you are enlarging is exactly the one that wedged —
  `code_sync` is the daemon's most recent failure (`TimeoutError`, tracked as issue #18).

- ⚑ **The baseline is a MOVING TARGET — re-derive it, do not trust the constant.** The note's
  22,502 / 52,755 figures were measured 2026-07-27 over 1,653 ledger versions. Live
  `palace status` on 2026-08-01 reports **33,861 vector rows** against the 22,621 the note
  measured — the corpus has grown. **The portable claim is the ratio (~2.34×), not the
  absolute count.** Item 1 exists precisely to re-derive both before anything is spent.

- ⚑ **Do not hardcode a measured figure into a docstring.** Open issue #28 is this exact
  defect elsewhere in the tree: `reference_edges` docstrings claim ~272k edges while the live
  store holds 2,284,272 — an 8.4× stale inline constant that becomes a silent design input.
  **A count is a query, not a comment.** Every figure this plan emits must be computed.

- ⚑ **Step 0 has genuinely never run.** `capture_commit_diffs` (`ops/code_lineage.py:112-130`)
  is shipped but the live snapshots db has zero `commit_diffs` / `_commit_diffs_captured`
  tables. Nothing downstream of it has ever executed against real data — treat its first run
  as unproven machinery, not as a routine invocation. It *is* idempotent per commit
  (`:119-129`, `INSERT OR IGNORE` + marker), which is what makes slicing safe.

- ⚑ **The compaction shim has two failure cases and only one is a finding (§3 Q5).** The
  typed `VectorTable` Protocol (`core/typedshims/lancedb.py:82-97`) declares
  `add/count_rows/delete/update/to_arrow/search/scan` and no compaction member. **Widening
  our own Protocol is ordinary in-scope work** — the file is in `write_scope`. **Discovering
  the pinned lancedb release has no such capability underneath is the finding** — and then
  you stop, because widening a Protocol cannot conjure a capability, and improvising a
  physical rewrite against an unpinned surface is how you lose a corpus.

- ⚑ **The embedder pin decides whether the carry-forward seed is free.** 13,311 atoms
  (7,791 L0a + 5,520 L0b) are already embedded with embed text unchanged — but reuse is only
  valid if their embedder identity matches the live `EmbeddingConfig.model` + `dim`
  (`core/kernel/config/loader.py:138-141`). If the embedder changed since they landed, **the
  seed is not free and the rebuild's economics change** — raise before spending, because the
  owner blessed a cost that would no longer be true. L1 re-embeds regardless (3,424 atoms):
  its stored windows were cut over header-bearing prose and do not survive D0's pin.

- ⚑ **"|atoms| ≤ Σ chunks" is NOT acceptance.** It holds vacuously at zero savings — the
  false-success shape the note calls out by name. The **measured factor** is the claim under
  test. Likewise `n_doc` vs `n_occ`: a fixture without a duplicate L0b window pair cannot
  distinguish them, so the fixture precondition is asserted first.

- ⚑ **Fibers for EVERY ledger version, not just chain members.** The ledger walks all commits
  (`ops/code_snapshot.py:353-360`, `rev-list --reverse HEAD`) while chains are first-parent
  (`ops/code_lineage.py:85-95`). A side-branch version lands a fiber but sits on **no chain**
  (D4/F3). Quantifying edge invariants over all fibers instead of chain members is wrong.

- ⚑ **Prose is not migrated (PD-2/R5).** Note rows stay on the old path. Do not "helpfully"
  migrate them; the D1 stratum fence has not been redesigned.

- ⚑ **Never run `deploy`.** Promoting a run onto HEAD is the owner's single in-loop gate.
  Also note `down`/`up`/`restart`/`deploy` live on `scripts/palace.py`, not on the
  `mind-palace` wrapper.

- **On completion the track is "ready to deskcheck", not done.** File it into
  `docs/DESKCHECK-QUEUE.md` and say so. Never self-declare a track done.

- **Depends on bp-152** — there must be a lander to rebuild into and a membership relation
  for the gauges to count.
