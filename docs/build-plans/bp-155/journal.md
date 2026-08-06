# bp-155 — journal

## 2026-08-06 — build complete, all three items, PR open (SEAL)

**Status.** Items 1–3 built and green on `build/bp-155-l0a-canonical-cut` (base `7c42a30`,
origin/main). The measured aggregate rename cost is **0** — D0 is complete across the tree, not
577/580 of it. Not a status flip — the owner's merge is the gate.

**Completed.**

- **Item 1 — the oversize cut decides over the canonical body.** `_l0a_chunks`
  (`core/ingest/code_corpus.py:152`): `if len(full) <= max_chars:` → `if len(body) <= max_chars:`.
  Nothing else in the block moved — `text=full` stays `text=full` (D0/R7). The KNOWN RESIDUE
  comment (issue #31) is replaced by one recording the decision is canonical-body-scoped per
  Amendment A1.2, and why (`:146-151`). bp-151's deliberate tripwire,
  `test_l0a_oversize_threshold_is_the_one_rename_residue`, is converted to
  `test_l0a_oversize_cut_is_canonical_body_scoped` (`tests/unit/test_code_corpus.py:275`):
  same straddle-precondition fixture (the rename still crosses the OLD header-bearing threshold),
  the mint-1 assertion flipped to mint-0, and the docstring records that this was bp-151's
  tripwire and that it reddened exactly as designed when the fix landed. Confirmed by inversion:
  stashing the fix and re-running the whole suite reproduces the original 1-atom residue at this
  fixture; restoring it returns to 0.
- **Item 2 — aggregate rename cost re-measured at 0.** Script measurement (not a committed test —
  matching bp-151's own precedent, whose 11,096/2,373/3 ladder was also ad hoc, not shipped as a
  full-tree pytest test) over all **580** tracked `.py` files, real chunkers, real bytes: for each
  file, derive at its own path and at a length-changed moved path (same directory, longer
  basename), sum new `(layer, content_hash)` atoms across all three layers. **Result: 0.** Teeth
  confirmed by re-running the identical script against the pre-fix code (`git stash` the one file):
  **23** new atoms across 23 files — nonzero, and larger than bp-151's original 3 because the tree
  has grown since `45c4a15`. A1.5's first falsifier does not fire.
- **Item 3 — boundary-change census: 72 groups across 57 files, all in-band.** Comparing L0a
  `(path, qualname)` groups' canonical-body hashes before vs. after the fix (same script pattern,
  stash/restore), **73** groups changed across **58** files; **72/57** of those are rule-driven,
  and **1** (`core/ingest/code_corpus.py::_l0a_chunks` itself) is a measurement artifact — this
  commit's own comment edit inside that function's body, not a rule effect (confirmed: its body
  differs only in the reworded comment text, and every other changed group is untouched by any
  source edit). Verified **all 72** genuine changes fall inside the predicted band
  (`max_chars - len(header) <= len(body) <= max_chars`) — A1.5's second falsifier does not fire.
  The tree has moved since `45c4a15`'s **123/95** measurement; this is what it reads now, not a
  discrepancy.

**A finding surfaced during Item 3's inspection, not a defect — recorded for the reviewer.** For
groups in the affected band, the OLD rule routed the body through `chunk_text`
(`core/kernel/ingest/chunk.py`), whose `_blocks` calls `.strip()` on each block even when the
whole body is a single block that fits under budget — silently stripping the **first line's
leading indentation** for any nested symbol (a class method's body starts with its indent). E.g.
`config/secrets_backend.py::VaultClient.mint_token`: old routing rendered
`'def mint_token(self, role...'` (dedented); the raw body is
`'    def mint_token(self, role...'` (indented, correct). The new rule takes the whole branch
directly for these 72 slices, so their canonical bodies (and embed text) are the exact,
unmangled source for the first time — a side benefit of the fix, not a new behavior to chase.

**Gate — exact results.**
- `ruff check .` — clean (0 errors) after fixing one E501 introduced by the converted test's
  trailing comment.
- `mypy core agents eval ops scheduler scripts` — `Success: no issues found in 262 source files`.
- `mypy` (argless) — exits 1 as designed; tail `Found 69 errors in 20 files (checked 563 source
  files)` — **69**, unmoved from the pinned baseline.
- `python -m ops.type_gate` — exit 0; Tier-2 membership OK, bare-ignore scan OK, one parked
  non-fatal shim report (pre-existing, finding-0223, unrelated).
- `pytest -q` — **5 failed, 2427 passed, 15 skipped** in 224.14s. The 5: `test_dream_v2_live.py`
  (1), `test_worktree_enforcement.py` (3: `test_a_deny_cross_worktree`,
  `test_c_unsafe_direction_narrow_not_loosened`, `test_d_no_pointer_is_no_plan_not_main_fallback`),
  `test_core_self_containment.py::test_core_imports_nothing_outside_core` (1) — exactly the three
  known-red classes (finding-0103, e2e live, issue #13/finding-0280), same test names, same count
  bp-151 reported. **Diff-innocence proven**: stashed both changed files back to a byte-identical
  `origin/main` (`git diff --stat origin/main HEAD` empty), re-ran the full suite — **same 5
  failures, same names**, 249.76s. `test_scheduler_live.py`'s known flake did not fire either run.

**In-flight.** Nothing. Working tree = the two write-scope files (committed `023671b`) plus this
journal entry.

**Next action.** None for the builder. For the reviewer: audit the Item 3 in-band verification
(the `.strip()` side-finding above) and confirm the PR body's numbers against this entry.

**Open questions.** None raised to an issue — the aggregate rename cost came back 0 (A1.5's first
falsifier did not fire), so there is no fourth path-dependent site to file.

**Context-manifest delta.** Read beyond §2: `core/kernel/ingest/chunk.py`'s `_blocks` (load-bearing
for the Item 3 side-finding — the `.strip()` call is why "pieces stayed 1→1" for every in-band
group despite the canonical body changing). Nothing proved irrelevant beyond the manifest's own
scope.

```read-map
docs/design-notes/vector-membership-store.md:512: A1.2's licence, verbatim — the one line that bounds this entire change
core/ingest/code_corpus.py:147: the replaced KNOWN RESIDUE comment — why the decision moved, per A1.2
core/ingest/code_corpus.py:152: the one-token change itself — len(full) -> len(body)
core/kernel/ingest/chunk.py:33: _blocks' .strip() — why in-band groups keep pieces=1 but change hash (the side-finding)
tests/unit/test_code_corpus.py:275: the converted tripwire — same straddle fixture, mint-0 assertion, docstring records the redness-as-designed
docs/build-plans/bp-155/journal.md:1: this entry — the measured ladder (0 rename cost, 72/57 in-band boundary changes) and the .strip() side-finding
```

## Follow-through
- **Built?** Yes — Item 1 (the fix + converted tripwire), Item 2 (aggregate rename cost
  re-measured at 0), Item 3 (boundary census at 72/57, all in-band) — all three plan items.
- **Wired / delivered (or why dormant)?** Live on the derivation path: `_l0a_chunks` is called
  unconditionally by `derive_code_chunks`, which `CodeCorpusSync._embed_and_land` calls — the
  next `code_sync` derives path-independent L0a boundaries with no switch to flip. No flag, none
  wanted — this is a correction, not a feature.
- **Does a consumer use it?** Yes, immediately, and by design the 72 affected groups' stored rows
  (wherever they exist) go stale the same way bp-151's did — derived ids no longer match stored
  ones for those slices. No migration here (§9); bp-153's rebuild reconciles. Existing rows keep
  serving retrieval meanwhile.
- **Track state (what remains on this track)?** D0 is now complete (11,096 → 3 → **0**). Next on
  the revised order (A1.3): **bp-152** (membership store + path-free atom id), then **bp-153**
  (the one rebuild, which must re-embed the 72 groups this plan moved). Neither is un-blocked by
  anything this plan left undone — the aggregate came back 0.
- **Opened a new track/finding?** No. No issue filed — A1.5's falsifiers did not fire. The
  `.strip()` side-finding is recorded here and in the PR body for the reviewer's awareness, not
  filed as a defect (it is a strict improvement with no observed downside, folded into this
  plan's own measured numbers rather than a separate track).

## Pre-build notes for whoever picks this up

- ⚑⚑ **The change is `len(full)` → `len(body)` in ONE `if`. Nothing else in that block moves.**
  In particular `text=full` STAYS `text=full`. Only the *decision* becomes canonical-body-scoped;
  the emitted embed text keeps its header. Changing what is emitted would strip headers from L0a
  embed text — that is D0/R7 violated, not fixed, and it is the single most likely way to get this
  wrong while appearing to succeed.

- ⚑⚑ **Do NOT retune `max_chars`.** It is 1200 characters, the per-chunk budget
  (`core/kernel/ingest/chunk.py:44`) — not a file-size limit. Amendment A1.5's third falsifier names
  a retune explicitly as over-reading the principle. A1.2 licenses exactly what path-independence
  requires and nothing more; if you find yourself reaching for `chunk_text` or the budget, stop.

- ⚑ **The existing residue test is SUPPOSED to redden. Convert it, do not delete it.**
  `test_l0a_oversize_threshold_is_the_one_rename_residue` was written by bp-151 as a deliberate
  tripwire; its docstring says so ("if #31 is ruled that way, this expectation becomes 0 and this
  test reddens — that redness is the tripwire"). The tripwire firing is the system working. Convert
  it to assert the residue is gone, rename it to say what it now guards, and record in its docstring
  that it was bp-151's tripwire and that it fired as designed.

- ⚑ **Keep the straddle precondition.** The fixture must still be one where the OLD rule would have
  flipped whole↔windowed. If you relax the fixture while converting the assertion, the test passes
  for the wrong reason and proves nothing — the false-success shape this repo tests against
  everywhere.

- ⚑ **If the aggregate rename cost is still non-zero, that is the valuable result — report it, do
  not chase it to zero.** A1.5's first falsifier: a residue after this fix means a **fourth**
  path-dependent site that neither the L1 probe nor the L0a threshold covered. That finding outranks
  finishing the plan. File it and say so. Do not adjust the measurement until it reads what you
  want.

- ⚑ **Expect chunk counts to go DOWN slightly. Do NOT treat `text` > 1200 as a regression — it is
  already true today, and by more than this change adds.** Measured 2026-08-06 over 400 repo files:
  the greedy packer seeds each new chunk with `overlap_chars` of tail plus a whole block, so chunks
  already reach `1200 + 150 + 2 = 1352` (observed L0b/L1 max is exactly 1352), and L0a reaches
  **1647** with its header. `max_chars` is a packing budget, not a hard cap. Trimming the body to
  compensate would reintroduce path-dependence through the back door — i.e. re-create the defect.

- ⚑ **Why this defect is not a rare tail — the number that makes the case.** Measured over the same
  400 files: L0a median chunk is **563** chars but **p90 is 1175**, against a 1200 budget, and
  **11.5% of symbols (591/5,139) already hit the budget and split.** The distribution piles up
  right against the threshold. So a ~30-character change in header length does not nudge some
  outlier — it moves a real population of symbols across a line they are already sitting on.

- ⚑ **Already-windowed slices must not change.** `chunk_text(body, ...)` was always called on the
  header-free body, so the windowing itself was already path-independent. Only the whole↔windowed
  decision was not. If pieces of an already-windowed slice change, something other than the decision
  moved — raise it (§10).

- **Measure on the real chunkers over real files, not a fixture.** Running against the actual tree
  is what made issue #31 findable at all; a fixture-only measurement would have missed it and will
  miss its successor.

- **Context — why this plan exists and why it is early.** bp-151 took the aggregate rename cost from
  **11,096 → 3**. This takes it to **0** and completes D0. It sits BEFORE bp-152 (not after) because
  bp-152's premise is corpus-wide dedup and this residue is a hole in exactly that — and because
  both plans touch `core/ingest/code_corpus.py`, so they are serial anyway. It must precede bp-153
  because the 123 affected groups need re-embedding and bp-153 re-embeds everything regardless:
  free before, a second pass after.

- **The defect is not rename-specific.** Its general form: two files with identical code at
  different-length paths chunk differently and therefore do not dedup. Renames are just where it was
  noticed. Keep that framing when writing the PR body — it is why this was worth interrupting the
  wave for.
