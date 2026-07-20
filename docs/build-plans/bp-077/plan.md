---
type: build-plan
id: bp-077
status: in-progress
design_ref:
  - docs/design-notes/authorship-distance-axis.md
  - docs/design-notes/the-sacred-boundary.md
contract: scribe
write_scope:
  - docs/book/**
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 200k
  actual: null
depends_on: []
parallelizable_with: []
created: 2026-07-19
updated: 2026-07-20
links:
  - CONSTITUTION.md
  - docs/BUILD-SPEC.md
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — The book: scaffold + Chapter 1 (Philosophy)

> **Every section below is required.** A section that does not apply is marked
> `N/A — <one-line reason>`, never silently omitted.

## 0. Mode & provenance

The first scribe plan through the finished machinery (book skill §12). It stands
up the LaTeX project (`docs/book/`) and writes the first chapter — Philosophy.
`contract: scribe`: write scope is `docs/book/**` only; the scribe CANNOT edit a
design note (`scope-guard` enforces). Concern is EXPOSITION; **accuracy outranks
style** — a beautiful sentence about a false mechanism is a defect, and a gap
found while explaining is routed as a `spec-defect`/`discovery` finding, never
"fixed" in prose. The book is a **derived projection** (skill §3): it asserts
nothing without a cited source. `proposed → ready` is the owner's milestone flip.

## 1. Objective

`docs/book/` compiles to a PDF whose front matter, notation registry, and
Chapter 1 (Philosophy) are in place — every claim in the chapter carrying a
citation to the ratified record or to code by `path@ref`.

## 2. Context manifest

The scaffold is toolchain + conventions; Chapter 1's debt delta is the
philosophy-bearing record. Read in order:

1. `docs/build-plans/bp-077/plan.md` — this plan.
2. `.claude/skills/book/SKILL.md` — chapter map, voice, TikZ/notation/citation
   conventions, sync semantics (the authoritative style contract).
3. `CONSTITUTION.md` — the inviolable kernel; the philosophical spine.
4. `docs/BUILD-SPEC.md` §3 — the domain non-negotiables (the bright lines that
   philosophy motivates).
5. `docs/design-notes/authorship-distance-axis.md` — "every stratum is
   self-data, at a distance" (a design_ref; a central philosophical thesis).
6. `docs/design-notes/the-sacred-boundary.md` — writes-to-core discipline; the
   model-advises/code-acts principle in its purest form (design_ref).
7. `docs/design-notes/recursive-strata.md` — the dreamer-as-a-map framing (the
   system reasoning about itself).
8. Memory `ouroboros-naming` — the framework (mind-palace) vs the live system
   (Ouroboros) distinction; the builder LOCATES the founding note it names and
   cites it (candidate: `docs/design-notes/founding-corpus.md` — confirm).
9. `docs/design-notes/agent-workflow.md` — the artifact chain as epistemology
   (how a decision becomes real); philosophy of the process itself.

**Note on scope:** these are the Chapter-1 sources only. Architecture,
mathematics, intuition, and future-work chapters are LATER scribe plans; do not
pull their material in. If a philosophy claim needs a not-yet-written chapter,
forward-reference it (a `\ref` to a stubbed chapter), don't inline it.

**Earmark — the session-36 trust-boundary designs** (`dn-session-handoff-gate`,
`dn-exhaust-lane`, `dn-ouroboros-principal`, all ratified 2026-07-19) are
**Architecture-chapter debt**, recorded in `SYNC.md`'s pending list so the next
`/scribe` routes them there — their *mechanism* (Stop-audit clauses, the
ingest/exhaust lanes, the uid principal, LaunchDaemon) is architecture, not
philosophy. BUT Chapter 1 SHOULD cite `dn-ouroboros-principal` as the exemplar
of a philosophical stance it names: **"stop trusting posture; make the property
physical"** (structural enforcement — the same move as the core-seal reckoning,
memory `structural-enforcement`). The principle is philosophy; the LaunchDaemon
is architecture. Chapter 1 states the principle and `\ref`s the mechanism
forward. Likewise the artifact-chain-as-epistemology thread may cite the
handoff-gate as a lived example of "a decision doesn't live only in a
transcript" — principle here, mechanism in Architecture.

## 3. Investigation & grounding

- **Q1 — LaTeX toolchain + build.** Default to **tectonic** (single self-
  contained binary, reproducible, no system TeX install) unless it is
  unavailable, then `latexmk`. RECORD the chosen default in `SYNC.md` on this
  first run (skill §sync). The builder verifies a clean compile locally; if no
  toolchain is available, that is a `blocker` finding (the acceptance cannot be
  met) — surface it, do not fake the compile.
- **Q2 — the founding note's id.** Memory `ouroboros-naming` says the live
  system is "named by its own founding note." The builder locates it (grep
  `founding`/`Ouroboros` over `docs/design-notes/` — `founding-corpus.md` is
  the leading candidate) and cites the actual ratified id; if none is ratified,
  the naming claim cites the memory-independent source (CONSTITUTION / BUILD-SPEC)
  and notes the gap.
- **Q3 — citation scheme mechanics.** Design claims cite an artifact id;
  implementation claims cite `path@ref` (skill §grounding). The builder sets up
  the BibTeX/`\cite` or a lightweight `\artifact{}`/`\coderef{}` macro pair in
  the preamble (its choice; record it in a `CONVENTIONS`-style comment in
  `main.tex`), so every later chapter uses one mechanism. Snippets are COPIES
  annotated `source: path@ref`.
- **Q4 — what belongs in Chapter 1 vs later.** Philosophy = the *why*: the
  self-map thesis (mining one's own brain), authorship-distance, the sacred
  boundary as principle (not yet its mechanism), the artifact chain as
  epistemology, the ratify-falsifiers-not-proofs stance. The *how* (zones,
  math, instruments) is forward-referenced, not written here.

**Additional risks surfaced:** the book must be a STORY, not a knowledge dump
(memory `book-narrative-philosophy`): motivation → prerequisites → idea →
what-it-unlocks → why-it-matters, with strong intuition. The scribe SYNTHESIZES
a spine from the artifact chain; it never invents. Chapter 1 must read as the
opening of that story.

## 4. Reconciliation

N/A — greenfield exposition; the book derives from the record and corrects
nothing in it. Any contradiction discovered while writing is routed as a finding
(skill §accuracy), never reconciled in the book itself.

## 5. Write scope

`docs/book/**` only (the scribe contract). This includes `main.tex`,
`notation.tex`, `preamble.tex`, `chapters/01-philosophy.tex`, `SYNC.md`, a
`.gitignore` for LaTeX aux artifacts, and any `figures/*.tex` (TikZ) Chapter 1
needs. Deliberately OUT: every design note, `CONSTITUTION.md`, all code — the
book reads them, cites them, and copies snippets from them, but writes none.

## 6. Interfaces pinned inline

Project layout (the builder may refine names, but this is the intended shape):

```
docs/book/
  main.tex            # documentclass, \input preamble/notation, \include chapters
  preamble.tex        # packages, tikz/pgfplots, the \artifact{}/\coderef{} macros
  notation.tex        # THE symbol registry — defined once, used everywhere (skill)
  chapters/01-philosophy.tex
  figures/            # TikZ sources only — NO binary assets (skill)
  SYNC.md             # git ref + artifact ids incorporated; the toolchain default
  .gitignore          # *.aux *.log *.pdf(?) *.fls *.fdb_latexmk etc.
```

`SYNC.md` shape (skill §sync — updated at the end of every scribe run):

```markdown
# Book sync marker
git-ref: <HEAD sha at edition>
toolchain: tectonic            # recorded on first run (Q1)
incorporated:
  design-notes: [authorship-distance-axis, the-sacred-boundary, recursive-strata, agent-workflow, <founding note>]
  findings: []                 # none in Chapter 1
pending:                       # debt for LATER chapters — the next /scribe reads this
  architecture: [session-handoff-gate, exhaust-lane, ouroboros-principal, <the zone/boundary notes>]
chapters-present: [01-philosophy]
```

Citation macros (Q3 — pin the pattern so later chapters match):

```latex
\newcommand{\artifact}[1]{\textsc{[#1]}}      % design-note / finding id
\newcommand{\coderef}[2]{\texttt{#1}@\texttt{#2}}  % path @ git-ref
```

Chapter map (recorded in `main.tex` as the skeleton; only Ch.1 written now):
Philosophy → Architecture (zones & boundaries) → Mathematics (coboundary
framing + derived instruments) → Intuition → Future work (parked decisions
verbatim, warrant-linked). Superseded material = marked *design-evolution*
remarks. Draft notes never enter.

## 7. Items

### Item 1 — the scaffold (project compiles empty)

- **Objective:** `docs/book/` with `main.tex`, `preamble.tex`, `notation.tex`
  (seeded with the symbols Ch.1 needs), the citation macros, the chapter
  skeleton (Ch.2–5 stubbed with titles + a one-line abstract each), `SYNC.md`,
  `.gitignore` — compiling to a title-page-plus-stubs PDF with **zero undefined
  references**.
- **Files:** `docs/book/main.tex`, `preamble.tex`, `notation.tex`, `SYNC.md`,
  `.gitignore`, `chapters/0{1..5}-*.tex` (2–5 as stubs).
- **Acceptance test:** the chosen toolchain compiles clean (no errors, zero
  undefined refs); `SYNC.md` records the toolchain + HEAD sha.
- **Falsifier:** the compile emits an undefined-reference or an error, or no
  toolchain exists (→ `blocker` finding — the acceptance is unmeetable here).
- **Invariant(s):** no binary assets; notation defined only in `notation.tex`;
  citation via the one macro pair.
- **Touches stored data?** No.
- **Parallelizable?** No (foundation). **Depends on:** none.

### Item 2 — Chapter 1: Philosophy

- **Objective:** write `chapters/01-philosophy.tex` as the opening of the book's
  story: the self-map thesis, authorship-distance, the sacred boundary as
  principle, the artifact chain as epistemology, ratify-falsifiers-not-proofs —
  each claim cited (`\artifact`/`\coderef`), at least one TikZ figure (e.g. the
  authorship-distance axis or the artifact chain), narrative not enumerative.
- **Files:** `chapters/01-philosophy.tex`, `notation.tex` (extend), a
  `figures/*.tex` or two.
- **Acceptance test (fixed scribe acceptance, skill §sync):** whole-book review;
  EVERY snippet + code citation re-verified against HEAD (each carries
  `source: path@ref`); clean compile; zero undefined references; `SYNC.md`
  updated (git ref + artifact ids). Plus: every philosophy claim traces to a
  cited artifact/code source (no uncited assertion).
- **Falsifier:** a claim in the chapter has no citation, OR a cited snippet does
  not match HEAD, OR the chapter reads as a knowledge-dump list rather than a
  motivated narrative (memory `book-narrative-philosophy`).
- **Invariant(s):** accuracy outranks style; a discovered design gap is a
  finding, not a prose fix; draft-note material never enters.
- **Touches stored data?** No.
- **Parallelizable?** No. **Depends on:** Item 1.

## 8. Math carried explicitly

N/A — the mathematics chapter is a LATER scribe plan; Chapter 1 forward-
references it and implements no mathematical object itself.

## 9. Non-goals

- No chapters beyond Philosophy (architecture / math / intuition / future-work
  are separate scribe plans — the debt was split by cluster).
- No edit to any design note or code — the scribe reads and cites only.
- No PDF committed if the repo convention is source-only (skill §14: source
  commits now, PDF built locally); the builder confirms and sets `.gitignore`
  accordingly.
- No inventing design to smooth a narrative — synthesize the spine from the
  record; a gap is a finding.

## 10. Stop-and-raise conditions

- No LaTeX toolchain available → `blocker` finding (acceptance unmeetable).
- A philosophy claim has no citable source in the ratified record → either
  forward-reference a later chapter or file a `discovery`/`spec-defect` finding;
  never assert uncited.
- Writing exposes a contradiction between two ratified notes → `spec-defect`
  finding, route to the orchestrator; do not adjudicate in prose.
- The founding note (Q2) turns out unratified → cite the memory-independent
  source and note the gap; do not cite a draft.
- Owner-level question → park with re-entry, continue.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| Toolchain | tectonic (self-contained, reproducible) | latexmk (needs a full TeX install) | tectonic unavailable on the build host |
| PDF in-repo | source-only, PDF built locally (skill §14) | commit the PDF (binary churn) | owner wants a browsable PDF in-repo |
| Citation macro vs BibTeX | lightweight `\artifact`/`\coderef` macros | full BibTeX (heavier, ids aren't bib entries) | the reference count outgrows macros |

## 12. Dependency & ordering summary

Item 1 (scaffold compiles empty) → Item 2 (Chapter 1). Single session, one
chapter cluster. No stored-data writes; no live effect. This plan is the
foundation the later book-sync plans extend; its `SYNC.md` marker is what the
next `/scribe` reads to compute the remaining debt (architecture chapter next).
Independent of bp-075/bp-076 (disjoint write scope: `docs/book/**` vs their
config/ops/scripts surfaces) — runs concurrently with them by design (owner:
build the book while the plans build).
