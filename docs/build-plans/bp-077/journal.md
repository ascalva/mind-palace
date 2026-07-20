# bp-077 — journal

## 2026-07-20 — Item 1 (scaffold) ACCEPTED

**Status line.** Scaffold built and compiles clean. Item 1 acceptance met.

**Completed — Item 1.** `docs/book/` created: `main.tex`, `preamble.tex` (the pinned
`\artifact{}`/`\coderef{}` macros + `\gitref=bdcd9bc` + `principle`/`devolution`
envs + `\fwdthesis` forward-ref helper), `notation.tex` (proper-name macros +
artifact-chain node macros; math symbols reserved-commented for later chapters),
`chapters/01-philosophy.tex` (temporary stub for Item 1), `chapters/02..05-*.tex`
(stubs with title + one-line abstract + `\label`), `SYNC.md` (git-ref `bdcd9bc`,
toolchain `latexmk`, incorporated/pending/open), `.gitignore` (LaTeX aux + PDF).
- **Compile (latexmk, exit 0):** `Output written on main.pdf (7 pages)`; explicit
  scan for `undefined` / `Reference ... undefined` / `Label ... may have changed` =
  **NONE**. Only benign warning: hyperref duplicate-destination `page.i` (roman
  frontmatter — cosmetic, not a reference error).

**In-flight.** Writing Item 2 (Chapter 1 full narrative + 2 TikZ figures).

**Next action.** Replace the 01 stub with the Philosophy narrative; extend notation
if needed; recompile; re-verify snippets against HEAD.

**Open questions.** finding-0116 (routed). No blockers.

**Context-manifest delta.** (unchanged from prior entry).

## 2026-07-20 — grounding complete + spec-defect filed (scribe build, delegated)

**Status line.** Contract loaded (scribe, write_scope `docs/book/**`); plan flipped
`ready → in-progress`; all §2 sources read; toolchain + founding-note + draft-source
questions resolved; finding-0116 filed. Ready to build the scaffold (Item 1).

**Completed.**
- Q1 toolchain: `tectonic` NOT installed; full MacTeX present at `/Library/TeX/texbin`
  (`latexmk`, `pdflatex`, `xelatex`). Default = **latexmk** (the plan's recorded
  fallback). Recorded in SYNC.md on this first run.
- Q2 founding note: `founding-corpus.md` is `draft` AND never names "Ouroboros"
  (read at HEAD `bdcd9bc` — it is about corpus curation). It does not perform the
  naming. Ratified naming source = `dn-ouroboros-principal` §1. Gap noted in SYNC +
  finding-0116.
- Status audit of every candidate citation source. RATIFIED: `dn-agent-workflow`,
  `dn-ouroboros-principal`, `dn-session-handoff-gate`, `dn-exhaust-lane`. FIXED:
  CONSTITUTION.md, BUILD-SPEC.md. DRAFT (barred as book authorities): the two plan
  `design_ref`s `dn-authorship-distance-axis` + `dn-the-sacred-boundary`, plus
  `dn-recursive-strata`, `dn-founding-corpus`.
- **finding-0116 (spec-defect → orchestrator):** bp-077 §2 names four DRAFT notes
  as Chapter-1 sources, but ratified `dn-agent-workflow` §3/§13 bar draft notes from
  the book. Resolution taken: anchor every claim to ratified/fixed sources; present
  the draft theses as principles with their formalizations forward-referenced to
  later chapters; cite NO draft note in `\artifact{}`. Non-blocking.
- Code paths verified at HEAD `bdcd9bc` for potential `\coderef`:
  `scripts/check_imports.py` (import firewall, Invariant 2),
  `core/factory/roles.py:24` (`PRE_DECLARED_MAX = frozenset({"run_python"})`).

**In-flight.** None — grounding phase closed.

**Next action.** Build Item 1 scaffold: `docs/book/{main,preamble,notation}.tex`,
`chapters/01-philosophy.tex` (written in Item 2) + Ch.2–5 stubs, `SYNC.md`,
`.gitignore`. Compile clean with `latexmk`, zero undefined refs.

**Open questions.** finding-0116 (routed, orchestrator). No blockers.

**Context-manifest delta.** Read beyond §2: `dn-founding-corpus` (confirmed it does
not name Ouroboros), `BUILD-SPEC §1–§4` (ratified anchors for mission / model-advises
/ fixed-point argument), `core/factory/roles.py` + `scripts/check_imports.py` (coderef
verification). All §2 sources read.

## 2026-07-19 — minted at graduation (orchestrator /scribe, session-36)

The FIRST scribe plan — the book's initial scaffold + Chapter 1 (Philosophy).
Minted while bp-075/bp-076 build in parallel (owner: build the book alongside
the plans; disjoint write scope `docs/book/**` makes it safe).

Book debt computed: `docs/book/` does not exist → debt = initial scaffold +
first edition. The full ratified record is large (33 ratified/superseded notes +
30 promoted findings) — FAR more than one session — so split by chapter cluster
(book skill standard rule). This plan = scaffold + Philosophy; architecture,
mathematics, intuition, future-work are subsequent scribe plans keyed off the
`SYNC.md` marker this plan writes.

Owner steer (2026-07-19): the session-36 trust-boundary designs
(session-handoff-gate, exhaust-lane, ouroboros-principal) must be incorporated.
Resolution recorded in §2 + `SYNC.md pending`: their MECHANISM is
Architecture-chapter debt (routed by the sync marker, nothing lost); their
PRINCIPLE ("stop trusting posture, make the property physical"; "a decision
doesn't live only in a transcript") is philosophy and Chapter 1 cites
dn-ouroboros-principal / dn-session-handoff-gate as exemplars, forward-ref'ing
the mechanism.

Grounding left to the builder: the LaTeX toolchain (tectonic default, blocker
finding if none), the founding-note id (founding-corpus.md candidate), the
citation-macro vs BibTeX choice. Accuracy outranks style; a gap found while
writing is a finding, never a prose fix. The book TELLS A STORY (memory
book-narrative-philosophy) — motivation→idea→what-it-unlocks→why-it-matters,
intuition-first, not a knowledge dump.

Status: `proposed`. Awaiting the owner's `palace bless bp-077` + hand commit
(the ready-flip is the book's milestone confirmation, skill §11).
