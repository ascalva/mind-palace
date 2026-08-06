# bp-155 — journal

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

- ⚑ **Expect chunk counts to go DOWN slightly, and some `text` to exceed 1200.** Slices in the band
  between `max_chars - len(header)` and `max_chars` are now emitted whole where they were previously
  windowed, so their embed text is up to `len(header)` over the budget. That is accepted and parked
  (§11): the budget bounds the identity body, and the header was always additive on top. Trimming
  the body to compensate would reintroduce path-dependence through the back door — i.e. it would
  re-create the entire defect.

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
