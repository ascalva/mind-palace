---
type: build-plan
id: bp-104
track: workflow
status: ready
design_ref:
  - docs/design-notes/agent-workflow.md
contract: scribe
session_budget: 1
write_scope:
  - docs/book/**
cost:
  estimate:
    model: opus
    tokens: 160k
  actual: null
depends_on: []
parallelizable_with:
  - bp-103
created: 2026-07-25
updated: 2026-07-25
links:
  - docs/book/SYNC.md
  - docs/findings/finding-0117.md
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — bp-104: book sync, Chapter 2 (Architecture) — the boundaries, told from ratified mechanism

## 0. Mode & provenance

Scribe sync plan, minted by `/scribe`. The book is a **derived projection of the ratified record and
the codebase** (`dn-agent-workflow` §3): it asserts nothing without citing a source, and it
**synthesizes** a spine from the artifact chain — it never invents.

Owner's stated purpose for this edition (2026-07-25), which is the voice brief as much as the scope:
*"I want to be able to read about a section myself, and re-inspire myself, or look at the same design
from different perspectives at different times."* So the chapter must **read standalone and carry
intuition**, not merely be correct. A reader who knows nothing of the last 260 commits should finish
Chapter 2 understanding *why the boundaries exist*, not just where they are.

Authority-to-act is the owner's instruction to continue the book; `proposed → ready` stays owner-only.

## 1. Objective

Write Chapter 2 (Architecture) — the boundary/zone story of the system — from **ratified and
superseded sources only**, and re-key `docs/book/SYNC.md` to the new edition.

## 2. Context manifest

**The debt.** `docs/book/SYNC.md` is keyed to `bdcd9bc` (2026-07-20). HEAD is **260 commits** later.
Present: Chapter 1 (philosophy). Stubbed: chapters 2–5. Incorporated so far: only `dn-agent-workflow`
and `dn-ouroboros-principal`. Total record now: **34 ratified + 6 superseded** design notes. That is
far beyond one session, so this plan takes **one chapter cluster** (the standard split rule);
chapters 3–5 remain debt and stay listed in SYNC.md `pending`.

Read in order:

1. `docs/book/SYNC.md` — the edition marker, toolchain, citation scheme, and the `open` block
   (finding-0117's resolution). **Whole file.**
2. The **book** skill — chapter map, voice, TikZ/notation conventions, citation scheme, snippet
   provenance rules. Load it before writing a line.
3. `docs/book/chapters/01-philosophy.tex` — the established voice, and what Chapter 2 must not
   repeat. Also `preamble.tex`, `notation.tex`, `main.tex`.
4. `docs/design-notes/agent-workflow.md` §3 — the rule that governs this plan: what may be cited.
5. **The chapter's ratified sources** (all verified `status: ratified` at HEAD unless noted):
   - `plane-principals.md` — the plane split (the mechanism the chapter is built on)
   - `type-system-as-core-audit.md` — the type system as a boundary instrument
   - `capability-scope-algebra.md` — capability/scope algebra; blessing-as-grant
   - `session-handoff-gate.md` — the Stop-audit; the artifact chain made enforceable
   - `exhaust-lane.md` — the exhaust lane layout and writer
   - `agent-taxonomy.md` — §2.5 zone boundary, the witness law
   - `track-board-and-deskcheck-gate.md` — tracks × phases, the deskcheck gate
   - `ouroboros-principal.md` — **`status: superseded`.** Citable as a fixed source, but it MUST be
     cited *as superseded*, naming its successor. Do not present it as current.
6. `CONSTITUTION.md` and `docs/BUILD-SPEC.md` §3 — the invariants the boundaries enforce (already
   cited in Chapter 1; reuse the established `\artifact{}` refs rather than re-deriving).
7. `scripts/check_imports.py` and `core/typedshims/lancedb.py` — the boundary made executable. Any
   snippet must be re-verified at HEAD and carry `source: path@ref`.

**DRY audit.** Chapter 1 already establishes the artifact chain, the fixed-point kernel, and the
"structural enforcement" thesis. Chapter 2 must **build on** those, not restate them — cross-
reference with `\artifact{}` / `\ref{}` instead of re-explaining.

## 3. Investigation & grounding

- **Q1 — What may be cited?** `dn-agent-workflow` §3 admits **ratified** and **superseded** notes and
  the codebase. **DRAFT notes are barred.**
- **Q2 — ⚑ SYNC.md's own pending list names BARRED sources.** Its `architecture` debt lists *"the
  zone / boundary notes — the-sacred-boundary (mechanism), the-edge-model, etc."* Both are
  **`status: draft` at HEAD** (verified 2026-07-25). They **may not be sources.** This is precisely
  the trap **finding-0117** caught in bp-077 (four draft notes listed as Chapter-1 sources), and its
  recorded resolution is the one to reuse: **ratified anchors only; draft theses forward-referenced.**
  ⇒ Tell the boundary story from `plane-principals` + `type-system-as-core-audit` +
  `capability-scope-algebra` (all ratified), and forward-reference the draft theses as *"the
  argument being developed"* without asserting their content.
  ⇒ **Also fix SYNC.md's pending list** so the next scribe does not re-walk into it.
- **Q3 — Toolchain.** `latexmk` (pdflatex), recorded at bp-077 §3 Q1; **tectonic is NOT installed**
  on this host. Build: `cd docs/book && latexmk -pdf main.tex`.
- **Q4 — Is the arc complete?** Owner rule: *let a full arc land before its chapter.* The boundary
  arc has landed — the plane split, the import firewall, the typedshims, the Stop-gate, and the
  deskcheck gate are all built and ratified. **The ops arc (findings 0169–0179) has NOT** — bp-103 is
  in flight and finding-0169 is open. **Ops is therefore out of scope** (see §9).
- **Q5 — What is genuinely new since `bdcd9bc`?** Code does not settle chapter placement for all of
  it; this plan claims only the architecture cluster and leaves the rest as recorded debt.

## 4. Reconciliation

- `docs/book/SYNC.md` `pending.architecture` — lists two DRAFT notes as sources → **banner:
  correction.** Replace with the ratified anchor set (Q2) and note explicitly that the draft theses
  are forward-referenced, citing finding-0117 so the reasoning is not lost.
- `docs/book/SYNC.md` `git-ref` / `incorporated` / `chapters-present` — **update on completion** to
  the new edition (HEAD ref, the notes incorporated, `02-architecture` moved to present).
- `docs/book/chapters/02-architecture.tex` — currently a stub → replaced with the chapter. This is
  an **extension**, not a correction; nothing published is being retracted.

## 5. Write scope

`docs/book/**` only — the chapter, figures, `SYNC.md`, and any notation/preamble additions the
chapter needs. Plus the always-writable `docs/build-plans/bp-104/journal.md` and new files in
`docs/findings/`.

Deliberately OUT: every design note (the book never edits its sources), all source code, chapters
3–5, and the foundation denylist. **A scribe that wants to change a source has found a finding, not
an edit.**

## 6. Interfaces pinned inline

Citation scheme (from `SYNC.md`, verbatim — do not invent a second one):

```
\artifact{<id>}                  % design ids, e.g. \artifact{dn-plane-principals}
\coderef{<path>}{<git-ref>}      % code references
% Snippets are COPIES, annotated:  source: <path>@<ref>
```

Build command (recorded toolchain):

```
cd docs/book && latexmk -pdf main.tex
```

**Snippets are PSEUDO-CODE, not Python** (owner rule): they convey the idea, not the implementation.
A literal copy is only for `\coderef` citation, and then it carries `source: path@ref` and must be
re-verified at HEAD.

**Citations to external research must be VERIFIED** (external-grounding gate). Never cite from
memory. If a claim wants a paper and you cannot verify it in-session, write the claim without the
citation and file a finding — a fabricated reference is worse than an uncited sentence.

## 7. Items

### Item 1 — Correct SYNC.md's barred-source list, and fix the debt record

- **Objective:** the next scribe cannot repeat Q2's trap.
- **Files:** `docs/book/SYNC.md`.
- **Acceptance test:** `pending.architecture` names only ratified/superseded ids; the draft notes
  appear under an explicit forward-reference note citing finding-0117.
- **Falsifier:** a draft id still appears anywhere it could be read as a citable source.
- **Touches stored data?** No. **Depends on:** none.

### Item 2 — Write Chapter 2 (Architecture)

- **Objective:** the boundary story, told from ratified mechanism, readable standalone.
- **Files:** `docs/book/chapters/02-architecture.tex`, figures, `notation.tex`/`preamble.tex` as needed.
- **Acceptance test:** every assertion carries an `\artifact{}` or `\coderef{}`; clean
  `latexmk -pdf main.tex`; **zero undefined references**; every snippet carries `source: path@ref`
  re-verified at HEAD.
- **Falsifier:** ⚑ **an assertion that cannot be traced to a ratified source** — i.e. the chapter
  states something true-of-the-system that the record does not support. That is invention, and it is
  the one failure mode this contract exists to prevent. Sweep the finished chapter claim-by-claim
  before declaring done.
- **Second falsifier (voice):** the chapter reads as a knowledge dump — mechanism with no motivation.
  The owner's test is *"re-inspire myself"* and *"look at the same design from different
  perspectives."* A section that only enumerates has failed even if every citation is correct.
- **Invariants:** never edits a source; never cites a draft; math is welcome and should be rigorous
  where it earns its place.
- **Touches stored data?** No. **Depends on:** Item 1.

### Item 3 — Whole-book review and re-key the edition

- **Objective:** the book is internally consistent and SYNC.md describes the new edition truthfully.
- **Files:** `docs/book/SYNC.md`, any Chapter 1 cross-reference fixes.
- **Acceptance test:** whole-book read-through; every existing snippet and `\coderef` **re-verified
  against HEAD** (260 commits have passed — a citation valid at `bdcd9bc` may be stale); clean
  compile; zero undefined references; `SYNC.md` updated with the new git ref, incorporated ids, and
  `chapters-present`.
- **Falsifier:** a Chapter-1 `\coderef` still points at a line that moved or a symbol that was
  renamed since `bdcd9bc`, and the review did not catch it. **Check every one; do not spot-check.**
- **Touches stored data?** No. **Depends on:** Item 2.

## 8. Math carried explicitly

N/A — no new mathematical object is implemented. Chapter 2 is architectural; the coboundary framing
and the derived instruments remain Chapter 3 debt (`SYNC.md` `pending.mathematics`). If the chapter
needs a formal statement of a boundary invariant, state it rigorously and cite its ratified source.

## 9. Non-goals

- **Not** chapters 3, 4, or 5 — they stay recorded debt in `SYNC.md`.
- **Not** the ops arc (findings 0169–0179, the ops track). **That arc has NOT landed** — bp-103 is in
  flight and finding-0169 is open. Owner rule: let a full arc land before its chapter.
- **Not** any draft design note as a source (Q2).
- **Not** edits to any source note or to code. A scribe that wants one files a finding.
- **Not** a rewrite of Chapter 1 — only stale-citation repair found by the Item 3 review.

## 10. Stop-and-raise conditions

- A necessary part of the boundary story exists **only** in a draft note → do NOT cite it. Write
  around it, forward-reference, and **file a finding** proposing the note for ratification.
- A Chapter-1 citation is found stale in a way that changes its meaning (not just a moved line) →
  STOP and surface; that is a correctness issue in published material.
- The compile cannot be made clean → STOP; a book that does not build is not an edition.
- Any urge to edit a source note to make the chapter easier → STOP. That is the inversion this
  contract forbids.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| Draft boundary theses (`the-sacred-boundary`, `the-edge-model`) | Forward-referenced, not cited | Cite them (barred by `dn-agent-workflow` §3, finding-0117) | Owner ratifies either note |
| Chapters 3–5 | Remain debt in `SYNC.md` | Attempt them here (exceeds one session — the split rule) | A later `/scribe` run |
| The ops arc | Excluded | Include it (arc has not landed; f-0169 open) | bp-103 merges and the restart proves the backfill completes |

## 12. Dependency & ordering summary

Sequential: **Item 1 → Item 2 → Item 3.** Item 1 first so the corrected source list governs the
writing rather than being retrofitted; Item 3 last because the whole-book review must see the
finished chapter.

Across plans: no dependencies. `parallelizable_with: bp-103` — disjoint by construction
(`docs/book/**` vs `core/**`), and this plan touches no code at all.
