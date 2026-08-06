---
type: build-plan
id: bp-155
track: code-ingest
status: proposed
design_ref:
  - docs/design-notes/vector-membership-store.md
contract: builder
write_scope:
  - core/ingest/code_corpus.py
  - tests/unit/test_code_corpus.py
session_budget: 1
cost:
  estimate:
    model: sonnet
    tokens: 120k
  actual: null
depends_on: [bp-151]
parallelizable_with: []
created: 2026-08-06
updated: 2026-08-06
links:
  - docs/build-plans/bp-151/plan.md
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — the L0a oversize cut decides over the canonical body (A1.2)

## 0. Mode & provenance

Graduated from `dn-vector-membership-store` **Amendment A1** (path-independence as the principle),
2026-08-06, at the owner's direction (*"this needs to be addressed immediately"*). The amendment
lands in the same PR as this plan, so this plan's licence becomes ratified by the same merge that
readies it.

Warrant: **issue #31**, discovered while building bp-151 and measured on the real chunkers at
`45c4a15`. bp-151 correctly refused this change — it was excluded by §1.2's *"No other chunker
behavior changes"*, a clause A1 has now replaced with a principle that licenses exactly this and
nothing more.

**This plan completes D0.** bp-151 took the aggregate rename cost from 11,096 → 3; this takes it
to **0**.

## 1. Objective

Decide the L0a oversize split over the canonical body, so no chunk boundary depends on the file's
path.

## 2. Context manifest

Read in order:

1. `docs/design-notes/vector-membership-store.md` — **Amendment A1** (the licence and its bound),
   then D0 and §1.2 as amended.
2. `docs/build-plans/bp-151/plan.md` §6 and `docs/build-plans/bp-151/journal.md` — the identity
   model this completes, and the traps that still apply.
3. `core/ingest/code_corpus.py` — `_l0a_chunks` is the whole surface.
4. `tests/unit/test_code_corpus.py` — specifically
   `test_l0a_oversize_threshold_is_the_one_rename_residue`, which currently pins the defect and is
   **designed to redden** when this plan lands.
5. Issue #31 and its orchestrator amplification comment — the general form (a path-length defect,
   not a rename defect) and why the gauge consequence matters.

## 3. Investigation & grounding

- **Q1 — What exactly is the defect?** `_l0a_chunks` decides the oversize split on the
  header-bearing length: `full = f"{header}\n{body}"`, then `if len(full) <= max_chars`
  (`core/ingest/code_corpus.py`, the `_l0a_chunks` loop). `header` is
  `f"# {path}:{qualname}{signature}"`, so the path's length participates in a cut decision.
- **Q2 — What is `max_chars`?** **1200 characters** — the per-chunk budget, with
  `overlap_chars=150` (`core/kernel/ingest/chunk.py:44`). Characters, not tokens ("characters are
  a stable proxy now"). It is **not** a file-size limit. ~1200 chars ≈ 30–40 lines, which is
  inside the normal size distribution of a Python function — hence 123 affected groups, not a
  handful.
- **Q3 — Is the fix really one token?** The decision becomes `len(body) <= max_chars`. But note
  what must NOT change with it: the **embed text** in the whole branch stays `full`
  (header + body). Only the *decision* moves to the canonical body. Getting this wrong by also
  changing what is emitted would strip headers from L0a embed text, violating D0's "embed text may
  keep headers" (R7).
- **Q4 — What is the measured blast radius?** **123 L0a groups across 95 files** change chunk
  boundaries (measured at `45c4a15`, reported in issue #31). Those atoms take new identities.
  Nothing has been re-embedded yet — bp-153's rebuild has not run — so no stored data is
  invalidated by this plan.
- **Q5 — Does the existing residue test have to change?** Yes, and that is by design. bp-151's
  `test_l0a_oversize_threshold_is_the_one_rename_residue` asserts the residue mints exactly 1 atom
  and its docstring names the re-entry: *"if #31 is ruled that way, this expectation becomes 0 and
  this test reddens — that redness is the tripwire."* The builder must convert it, not delete it.

**Additional risks or questions surfaced during reading:**

- **The overlap interaction is unexamined.** When a slice is windowed, `chunk_text(body, ...)` is
  already called on the header-free body, so the *windowing* was always path-independent — only
  the whole↔windowed *decision* was not. This means the fix should not change any already-windowed
  slice's pieces. If it does, something else is going on and the change is not what it claims
  (§7 Item 1's falsifier).
- **A slice between `max_chars - len(header)` and `max_chars`** is the affected band. After the
  fix, slices in that band are emitted **whole** where they were previously windowed — so chunk
  count goes *down* slightly and individual chunks get slightly larger.
- **`max_chars` is NOT a hard cap today, and this plan does not make it one** (measured
  2026-08-06, orchestrator, over 400 repo files). `chunk_text`'s greedy packer emits a chunk and
  then seeds the next with `overlap_chars` of tail **plus** a whole block, so a chunk reaches
  `max_chars + overlap_chars + 2` = **1352**; the observed L0b/L1 maximum is exactly 1352, which
  confirms the mechanism. L0a adds its header on top — observed max **1647** against a nominal
  1200. Measured distribution: L0a median **563**, p90 **1175**; L0b median 1001, p90 1198; L1
  median 1094, p90 1184. **11.5% of symbols (591/5,139) already hit the budget and split.**
  Two consequences for this plan: (a) a reviewer must NOT treat "text > 1200" as evidence of a
  regression — it is pre-existing and larger than what this change adds; (b) the L0a p90 of 1175
  against a 1200 budget is *why* this defect matters — the distribution piles up against the
  threshold, so a ~30-char header delta moves a real population across it, not a rare tail.

## 4. Reconciliation

- `core/ingest/code_corpus.py` `_l0a_chunks` — the KNOWN RESIDUE comment bp-151 left in place
  (naming issue #31 and "the orchestrator's call") → **[banner: correction]**. It is now ruled;
  the comment is replaced by one recording that the decision is canonical-body-scoped per A1.2,
  with the reason (path-independence), not deleted silently.
- `tests/unit/test_code_corpus.py::test_l0a_oversize_threshold_is_the_one_rename_residue` →
  **[banner: correction]**. Converted from "pins the residue at 1" to "asserts the residue is
  gone", renamed to say what it now guards. Its docstring must record that it was bp-151's
  tripwire and that the tripwire fired as designed.
- `docs/design-notes/vector-membership-store.md` §1.2 + Amendment A1 — the licence. Lands as its
  own commit in this PR; **not** in this plan's `write_scope` (a builder does not edit the note it
  graduates from).

## 5. Write scope

Two files. `core/ingest/code_corpus.py` holds the entire change (`_l0a_chunks`);
`tests/unit/test_code_corpus.py` holds the converted tripwire and the re-measured ladder.

Deliberately **out of scope**: `core/kernel/ingest/chunk.py` (`max_chars` is **not** retuned —
A1.5's third falsifier names that as over-reading the principle), every other chunker (L0b and L1
are already path-independent after bp-151), `core/stores/**` (bp-152), `docs/design-notes/**`, and
the fixed points (`CONSTITUTION.md`, `eval/golden/**`, `eval/golden.py`).

## 6. Interfaces pinned inline

**The current code, as bp-151 left it** (`core/ingest/code_corpus.py`, `_l0a_chunks`):

```python
        header, ls, le = coords[key]
        body = "\n".join(lines[i - 1] for i in owned[key])
        full = f"{header}\n{body}"
        # identity = the header-free body (D0); the header rides only on the embed text.
        # KNOWN RESIDUE (issue #31, parked): this ONE cut is still decided over header-bearing
        # length, so a rename that crosses the budget flips a slice whole↔windowed and mints 1
        # atom — the L1 mechanism surviving here. Deciding on len(body) is out of D0's bounds
        # (§9: no other chunker behavior changes); it is the orchestrator's call, pinned by
        # test_l0a_oversize_threshold_is_the_one_rename_residue.
        if len(full) <= max_chars:
            out.append(CodeChunk(LAYER_CODE_AST, key, ls, le, text=full, canonical_body=body))
        else:  # oversized slice: hard-split the body via the ONE window machinery, re-headered
            for piece in chunk_text(body, max_chars=max_chars, overlap_chars=overlap_chars):
                out.append(CodeChunk(LAYER_CODE_AST, key, ls, le,
                                     text=f"{header}\n{piece.text}", canonical_body=piece.text))
```

**The change, exactly:** `if len(full) <= max_chars:` becomes `if len(body) <= max_chars:`.
**Everything else in this block is unchanged** — in particular `text=full` stays `text=full`, so
L0a embed text keeps its header (D0/R7).

**The licence, verbatim from Amendment A1.2 — the bound the builder must not exceed:**

> **D0's bound is PATH-INDEPENDENCE, not a list.** A chunker behavior may change if and only if the
> change is required to make a chunk's **identity** independent of the file's path. Everything else
> about the chunkers stays fixed: no re-slotting (PD-5), no L0b span rework, no `max_chars` retune,
> no new layers, no embed-text redesign beyond the header prefix D0 already pins.

**The tripwire to convert** (`tests/unit/test_code_corpus.py`, current form):

```python
def test_l0a_oversize_threshold_is_the_one_rename_residue():
    """PARKED — issue #31 ... RE-ENTRY: if #31 is ruled that way,
    this expectation becomes 0 and this test reddens — that redness is the tripwire."""
    here, moved = "a/m.py", "a/much_longer_module_name.py"
    body = "def f():\n    y = 1\n\n    return y"
    budget = len(f"# {here}:f()") + 1 + len(body)
    assert len(f"# {here}:f()") + 1 + len(body) <= budget < len(f"# {moved}:f()") + 1 + len(body)
    a = _at(here, body + "\n", LAYER_CODE_AST, max_chars=budget)
    b = _at(moved, body + "\n", LAYER_CODE_AST, max_chars=budget)
    assert len(a) == 1
    assert len({c.content_hash for c in b} - {c.content_hash for c in a}) == 1   # ← issue #31
```

## 7. Items

### Item 1 — decide the oversize cut over the canonical body

- **Objective:** the whole↔windowed decision no longer depends on the path.
- **Files:** `core/ingest/code_corpus.py`, `tests/unit/test_code_corpus.py`
- **Acceptance test:** the converted tripwire — the same fixture that minted 1 atom now mints
  **0**, with its straddle precondition still asserted first (the fixture must still be one where
  the *old* rule would have flipped, or the test proves nothing).
- **Falsifier:** an already-windowed slice's pieces change. The windowing itself was always
  path-independent (`chunk_text` is called on `body`), so this change must move only the
  whole↔windowed decision. Pieces changing means something other than the decision moved. Also
  falsified if L0a embed `text` loses its header — that is D0/R7 violated, not fixed.
- **Invariant(s) it must not violate:** `derive_code_chunks` stays pure and deterministic (F-CI2).
  `max_chars` is **not** retuned. L1 and L0b are untouched. Row id shape untouched (bp-152's).
- **Touches stored data?** No. The live store's ids go staler than they already are; the
  reconciliation is bp-153's rebuild, which has not run.
- **Parallelizable?** No. **Depends on:** bp-151 (merged).

### Item 2 — re-measure the ladder: the aggregate rename cost is 0

- **Objective:** D0's spine holds across the whole tree, not 577/580 of it.
- **Files:** `tests/unit/test_code_corpus.py`
- **Acceptance test:** re-run bp-151's measurement over all tracked `.py` files: renaming every
  one of them mints **0** new atoms across all three layers (was 11,096 → 3). Record the number in
  the PR body.
- **Falsifier:** the aggregate is non-zero. Per A1.5 that means a **fourth** path-dependent site
  exists that neither the L1 probe nor the L0a threshold covered — the principle has not been
  fully applied, and the finding is more valuable than the fix. File it and report; do not tune
  the measurement until it reads zero.
- **Invariant(s) it must not violate:** the measurement must be over the **real** chunkers on real
  files, not a fixture — that is what made issue #31 findable at all.
- **Touches stored data?** No.
- **Parallelizable?** No. **Depends on:** Item 1.

### Item 3 — characterize the 123-group boundary change

- **Objective:** the blast radius is confirmed as measured, and is of the expected kind.
- **Files:** `tests/unit/test_code_corpus.py`
- **Acceptance test:** count the L0a groups whose chunk boundaries change under the new rule and
  report it in the PR. Expected ≈ **123 across 95 files** (measured at `45c4a15`; the tree has
  moved since, so report what you observe and compare — do not assert the constant).
- **Falsifier:** a file whose largest slice is nowhere near `max_chars` changes boundaries. The
  affected band is slices between `max_chars - len(header)` and `max_chars`; anything outside it
  means the change did something other than move the decision.
- **Invariant(s) it must not violate:** no measured figure is hardcoded into a docstring — a count
  is a query, not a comment (the issue #28 defect class).
- **Touches stored data?** No.
- **Parallelizable?** No. **Depends on:** Item 1.

## 8. Math carried explicitly

N/A — no mathematical object is implemented. The change is a predicate's argument.

## 9. Non-goals

- **No `max_chars` retune.** A1.5's third falsifier names this explicitly as over-reading the
  principle.
- **No other chunker change.** L0b and L1 are already path-independent after bp-151; A1.2 licenses
  only what path-independence requires.
- **No re-slotting (PD-5), no L0b span rework, no new layers, no embed-text redesign.**
- **No id-shape change** (bp-152), **no store work**, **no migration or re-embed** (bp-153).

## 10. Stop-and-raise conditions

- **The aggregate rename cost is still non-zero after the fix** — a fourth path-dependent site.
  File it (`type:defect`, `route:orchestrator`, `track:code-ingest`) and report; this is the
  finding A1.5 anticipates and it outranks finishing the plan.
- **The fix requires touching `chunk_text` or `max_chars`** — that is outside A1.2's bound. Stop.
- **The boundary change is larger or differently-shaped than Item 3's band predicts** — the change
  is not what it claims; raise before landing.
- No blessing, no status flip, no merge, no `deploy`; never write the fixed points.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| Embed text may exceed `max_chars` | Accepted, and **not new** — chunks already reach 1352 (`max_chars + overlap_chars + 2`) via overlap seeding, and 1647 at L0a with the header (measured 2026-08-06). The budget bounds the identity body; the header was always additive | Trim the body to keep `text` ≤ budget — rejected: reintroduces path-dependence through the back door, which is the entire defect | A downstream consumer breaks on a chunk longer than the budget |
| `max_chars` value (1200) | Unchanged | Retune while here — rejected: explicitly outside A1.2 and named in A1.5 | A measured retrieval-quality result, in its own plan |

## 12. Dependency & ordering summary

**Gated on bp-151** (PR #32) being merged — this edits the code bp-151 introduces.

Items are sequential: **1 → 2 → 3.** Item 1 is the change; Items 2 and 3 are read-only
measurements over it. No item writes stored data.

**Cross-plan — this plan moved to the FRONT of the wave (A1.3):** the order is now
**bp-151 → bp-155 → bp-152 → bp-153**, not bp-151 → bp-152 → bp-153. Two reasons, and the first is
the load-bearing one:

1. **bp-152's premise is corpus-wide dedup** (PD-1, owner-ruled in). This residue is a hole in
   exactly that, and §8(b)'s fork criterion uses a fixture so it cannot see the hole. Building the
   membership store on a known-holey identity and then changing identity underneath it is
   backwards.
2. **They share `core/ingest/code_corpus.py`**, so they are serial regardless of ordering
   preference.

It must also precede **bp-153**: the 123 groups need re-embedding, and bp-153 re-embeds everything
anyway — so landing before that rebuild costs ≈ 0 and landing after costs a second pass plus a
window where the store holds atoms cut under two rules.
