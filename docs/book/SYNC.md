# Book sync marker

The book is a derived projection of the ratified record and the codebase
(`dn-agent-workflow` §3). This marker records the edition: the git ref it is keyed
to, the toolchain, what has been incorporated, and the debt left for later
`/scribe` runs. The next scribe computes remaining debt against this file.

git-ref: bdcd9bc            # HEAD at this edition (bp-077: scaffold + Chapter 1)
toolchain: latexmk          # RECORDED ON FIRST RUN (bp-077 §3 Q1).
                            # tectonic (the plan's preferred default) is NOT installed
                            # on the build host; MacTeX is present at /Library/TeX/texbin,
                            # so latexmk (pdflatex) is the recorded fallback. Build:
                            #   cd docs/book && latexmk -pdf main.tex
citation-scheme: \artifact{<id>} for design ids; \coderef{<path>}{<git-ref>} for code.
                            # Snippets are copies annotated `source: path@ref`.

incorporated:
  design-notes:            # RATIFIED / fixed sources cited in this edition
    - dn-agent-workflow          # ratified — artifact chain, plan-as-capability, book rules
    - dn-ouroboros-principal     # ratified — structural enforcement; the name "Ouroboros"
  fixed-sources:
    - CONSTITUTION.md            # the fixed-point kernel (§I purpose, §II/§IV/§V)
    - docs/BUILD-SPEC.md         # §1 mission, §2 principles, §3 invariants, §4 fixed point
  code:
    - scripts/check_imports.py@bdcd9bc     # the import firewall (Invariant 2)
    - core/factory/roles.py@bdcd9bc        # PRE_DECLARED_MAX = frozenset({"run_python"})
  findings: []             # none incorporated as content in Chapter 1

pending:                   # DEBT for later chapters — the next /scribe reads this
                           # ⚑ READ THIS BEFORE ADDING A LINE. Every id listed under a
                           # chapter here is a CITABLE source, i.e. `status: ratified` or
                           # `status: superseded` at HEAD. Draft notes are BARRED from the
                           # book (dn-agent-workflow §3) and must never appear in this
                           # block — that is the trap finding-0117 caught in bp-077 (four
                           # draft ids listed as Chapter-1 sources) and it was still live
                           # in this file's `architecture` row until bp-104 corrected it.
                           # Draft theses go under `forward-referenced` below, never here.
  architecture: []         # DONE this edition (bp-104) — see `incorporated` above.
  mathematics:             # CITABLE ids only (see the banner above)
    - dn-temporal-retrieval-algebra   # ratified — the retrieval math home
    - dn-magnetic-laplacian           # ratified
    - dn-fiber-geometry               # ratified
    - dn-connectivity-instruments     # ratified
    - dn-core-graph-instruments       # ratified
    - the coboundary framing and derived instruments (canonical write-up)
  intuition: []
  future-work:
    - the parked decisions of the record, verbatim with re-entry conditions
    # Ch.2 already contributes: dn-inner-outer-core P1/P2/P8, dn-plane-principals §5,
    # dn-capability-scope CS-a..CS-e, dn-type-system-as-core-audit PD-1..PD-4,
    # dn-track-board-and-deskcheck-gate P-WF1..P-WF5.

forward-referenced:        # DRAFT theses — NAMED in the book, never CITED, never asserted.
                           # A draft note is barred as a source (dn-agent-workflow §3); the
                           # book may say "this argument is being developed" and point at the
                           # chapter that will carry it once the owner ratifies. `\fwdthesis`
                           # (preamble.tex) is the macro that makes the distinction mechanical.
                           # Each row: <draft id>  # what the book withholds -> lands in
  - dn-the-sacred-boundary       # the three-channel taxonomy of writes crossing the core
                                 #   boundary (verdict / ingestion / effects) -> ch:architecture.
                                 #   Ch.2 §2.7 gives only the RATIFIED partial: dn-capability-scope's
                                 #   A = P x W_Sigma x W_world authority product. Ch.1's forward
                                 #   promise was repaired to a \fwdthesis at bp-104 (finding-0180).
  - dn-the-edge-model            # the edge zone's own model -> ch:architecture. Ch.2 §2.4 gives
                                 #   only the ratified `ouroboros-edge` plane (dn-plane-principals
                                 #   §3.1/§3.4) and says the tenancy question is open.
  - dn-authorship-distance-axis  # the graded authorship coordinate -> ch:math (finding-0117).
  - dn-founding-corpus           # the naming claim of memory `ouroboros-naming` (bp-077 Q2).

chapters-present: [01-philosophy]
chapters-stubbed: [02-architecture, 03-mathematics, 04-intuition, 05-future-work]

open:
  # Q2 gap (bp-077 §3): memory `ouroboros-naming` says the live system is "named by
  # its own founding note"; the candidate `founding-corpus.md` is DRAFT and does not
  # itself name "Ouroboros" (read at bdcd9bc). The name is cited to the ratified
  # `dn-ouroboros-principal` §1 instead. See docs/findings/finding-0117.md.
  # finding-0117 (spec-defect -> orchestrator): bp-077 §2 lists four DRAFT notes as
  # Chapter-1 sources, but dn-agent-workflow §3 bars draft notes from the book.
  # Resolution this edition: ratified anchors only; draft theses forward-referenced.
