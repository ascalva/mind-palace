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
  architecture:            # MECHANISM of the session-36 trust-boundary designs
    - dn-session-handoff-gate    # ratified — Stop-audit clause (e); artifact-chain example
    - dn-exhaust-lane            # ratified — the exhaust lane layout/writer
    - dn-ouroboros-principal     # ratified — the uid principal + LaunchDaemon (mechanism)
    - the zone / boundary notes  # the-sacred-boundary (mechanism), the-edge-model, etc.
  mathematics:
    - the coboundary framing and derived instruments (canonical write-up)
    - dn-authorship-distance-axis  # DRAFT — barred until ratified (finding-0117)
  intuition: []
  future-work:
    - the parked decisions of the record, verbatim with re-entry conditions

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
