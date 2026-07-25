# Book sync marker

The book is a derived projection of the ratified record and the codebase
(`dn-agent-workflow` §3). This marker records the edition: the git ref it is keyed
to, the toolchain, what has been incorporated, and the debt left for later
`/scribe` runs. The next scribe computes remaining debt against this file.

git-ref: 009b726            # HEAD at this edition (bp-104: Chapter 2 + whole-book review).
                            # Previous edition: bdcd9bc (bp-077: scaffold + Chapter 1).
                            # EVERY \coderef and snippet in the book was re-verified against
                            # this ref, file by file, at bp-104 Item 3 — not spot-checked.
toolchain: latexmk          # RECORDED ON FIRST RUN (bp-077 §3 Q1).
                            # tectonic (the plan's preferred default) is NOT installed
                            # on the build host; MacTeX is present at /Library/TeX/texbin,
                            # so latexmk (pdflatex) is the recorded fallback. Build:
                            #   cd docs/book && latexmk -pdf main.tex
citation-scheme: \artifact{<id>} for design ids; \coderef{<path>}{<git-ref>} for code.
                            # Snippets are copies annotated `source: path@ref`.

incorporated:              # ALL ids below verified `ratified` (or `superseded`, marked) at 009b726
  design-notes:
    # --- Chapter 1 (edition bdcd9bc, re-verified here) ---
    - dn-agent-workflow          # ratified — artifact chain, plan-as-capability, book rules; §6 hooks
    - dn-ouroboros-principal     # SUPERSEDED (by dn-plane-principals, warrant finding-0116).
                                 #   Still citable as a fixed source, but ONLY as superseded and
                                 #   naming its successor. Ch.1's three citations were repaired to
                                 #   say so at bp-104; Ch.2 carries it as a design-evolution remark.
    # --- Chapter 2 (this edition) ---
    - dn-plane-principals        # ratified — the four plane principals; §3.1 matrix, §3.4 kernel facts
    - dn-inner-outer-core        # ratified — the ring predicate, the computed fixed point, §2.8 geometry
    - dn-type-system-as-core-audit  # ratified — Curry–Howard, the two obligations, tiers, static shadow
    - dn-capability-scope        # ratified — s=(Σ,E,T,A); meet=delegation; firewalls as ideals; Inv/Rate
                                 #   NB the FILE is capability-scope-algebra.md; the ID is dn-capability-scope
    - dn-agent-taxonomy          # ratified — §2.5 the C fiber (origin, not lineage)
    - dn-agentic-loop            # ratified — §2.4b the exhaust refinement, default-excluded
    - dn-session-handoff-gate    # ratified — Stop-audit clause (e); the block condition; its porosity
    - dn-exhaust-lane            # ratified — the one-way invariant; structural isolation over exclusion
    - dn-track-board-and-deskcheck-gate  # ratified — derived board; computed closure
  fixed-sources:
    - CONSTITUTION.md            # the fixed-point kernel (§I, §II.1/.2, §III.1/.2, §IV–§V)
    - docs/BUILD-SPEC.md         # §1 mission, §2 principles, §3 invariants 1–2/3/9/11, §4, §6 zones
  code:                      # every path re-verified to exist at 009b726; snippets byte-checked
    - scripts/check_imports.py@009b726             # the import firewall CLI (Invariant 2)
    - core/factory/roles.py@009b726                # PRE_DECLARED_MAX = frozenset({"run_python"})
    - ops/import_lint.py@009b726                   # SNIPPET: FORBIDDEN_ZONES + NETWORK_ALLOWLIST
    - ops/network/ouroboros-egress.pf.conf@009b726 # SNIPPET: the two pf rules (:43-44)
    - core/sealing.py@009b726                      # the runtime fail-closed egress guard
    - core/kernel/rings.py@009b726                 # the ring map (INNER, 43 members at this ref)
    - core/kernel/scope.py@009b726                 # the built scope algebra (E ⊆ {F,D,C}; ⊤_Σ = R∖𝔇)
    - core/typedshims/lancedb.py@009b726           # the boundary wrapper quarantining Any
    - core/reference_view.py@009b726               # _resolve_default_commit — the consistent cut
    - scripts/verify_planes.py@009b726             # the read-only four-plane verifier
    - tests/unit/test_core_self_containment.py@009b726  # the outer ratchet (red by design)
    - CLAUDE.md@009b726                            # the operational constitution
  findings:                  # cited as content, not merely as provenance
    - finding-0011           # max reachable effector tier is NONE (Ch.2 §planes)
    - finding-0026           # no type checker ran — the warrant of the type note
    - finding-0103           # core self-containment audit — Ch.2's (⋆) hypothesis
    - finding-0116           # the exhaust write-owner conflict — the supersession warrant
    - finding-0117           # draft notes barred from the book (the standing rule)
    - finding-0183           # FILED THIS EDITION — Ch.1's forward promise vs the draft taxonomy
    - finding-0184           # FILED THIS EDITION — the three-plane composition is unratified
    - finding-0185           # FILED THIS EDITION — the firewall's global claim is conditional
  external-references:       # VERIFIED IN-SESSION 2026-07-25 via DOI metadata. Never from memory.
    - 10.2140/pjm.1955.5.285   # Tarski 1955, Pacific J. Math 5(2):285-309 — greatest fixed point
    - 10.1145/2699407          # Wadler 2015, CACM 58(12):75-84 — propositions as types
    - 10.1145/359545.359563    # Lamport 1978, CACM 21(7):558-565 — time, clocks, ordering
    - 10.1145/214451.214456    # Chandy & Lamport 1985, TOCS 3(1):63-75 — distributed snapshots

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
                                 #   promise was repaired to a \fwdthesis at bp-104 (finding-0183).
  - dn-the-edge-model            # the edge zone's own model -> ch:architecture. Ch.2 §2.4 gives
                                 #   only the ratified `ouroboros-edge` plane (dn-plane-principals
                                 #   §3.1/§3.4) and says the tenancy question is open.
  - dn-authorship-distance-axis  # the graded authorship coordinate -> ch:math (finding-0117).
  - dn-founding-corpus           # the naming claim of memory `ouroboros-naming` (bp-077 Q2).

chapters-present: [01-philosophy, 02-architecture]
chapters-stubbed: [03-mathematics, 04-intuition, 05-future-work]

figures:                   # TikZ only, no binary assets (book skill). \input from a chapter.
  - figures/artifact-chain.tex     # Ch.1 (bp-077)
  - figures/fixed-point.tex        # Ch.1 (bp-077)
  - figures/enforcement-ladder.tex # Ch.2 — one invariant, three tiers
  - figures/trust-zones.tex        # Ch.2 — zones A/B/C and the airlock asymmetry
  - figures/plane-principals.tex   # Ch.2 — four OS users, two composing denials
  - figures/core-rings.tex         # Ch.2 — kernel ⊂ core ⊂ repo; perimeter vs meaning boundary

notation-additions:        # notation.tex is THE registry — extend, never fork (book skill)
  # Ch.2 added: zone names; the four principal names; the import-closure symbols
  # (C, N, L, B, I, imp, Reach); the scope symbols (s, Σ, E, T, A, 𝔇, R, ⊓, ⊔, ⊑, κ, Inv, Rate);
  # the three enforcement-tier names. preamble.tex gained booktabs + the `invariant` and
  # `proposition` theorem environments with their \autoref names.

open:
  # --- carried from edition bdcd9bc (bp-077), still open ---
  # Q2 gap: memory `ouroboros-naming` says the live system is "named by its own
  # founding note"; the candidate `founding-corpus.md` is DRAFT and does not itself
  # name "Ouroboros". The name is cited to `dn-ouroboros-principal` §1 — which is now
  # SUPERSEDED, so Ch.1 cites it as such and names dn-plane-principals §1, which
  # retains the naming. See docs/findings/finding-0117.md.
  # finding-0117 (spec-defect -> orchestrator): a plan listed DRAFT notes as book
  # sources, which dn-agent-workflow §3 bars. Standing resolution, reaffirmed by
  # bp-104: ratified/superseded anchors only; draft theses forward-referenced.
  #
  # --- opened by edition 009b726 (bp-104), all routed to the orchestrator ---
  # finding-0183 (spec-defect): Ch.1 forward-promised the three-channel taxonomy of
  # the sacred boundary; its only source is the DRAFT dn-the-sacred-boundary, so Ch.2
  # gives only dn-capability-scope's ratified authority product. Ch.1's sentence was
  # repaired to a \fwdthesis. RE-ENTRY: on ratification, amend Ch.2 with the full
  # taxonomy, restore Ch.1's citation, drop the id from `forward-referenced`.
  # finding-0184 (spec-defect): the three-plane security composition (code / data /
  # boundary planes, and the claim that none substitutes for another) lives in the
  # DRAFT docs/research/security-planes.md — which is also the cited origin of the
  # foundation denylist at .claude/hooks/_lib.py:27, and the doctrinal frame the
  # RATIFIED dn-type-system-as-core-audit says it extends. Ch.2 therefore states its
  # organizing frame as the MANUAL'S OWN reading, not as a ratified claim.
  # RE-ENTRY: on ratification, that frame becomes Ch.2's cited opening thesis.
  # finding-0185 (discovery): the import firewall checks DIRECT imports only, so its
  # global no-egress-path claim is conditional on core self-containment — whose
  # ratchet is red by design (finding-0103). Ch.2 states the local invariant, proves
  # what it yields (Prop. 2.1), names the hypothesis (⋆) explicitly, and gives the
  # unconditional closure only as a limit (Prop. 2.2). RE-ENTRY: if a closure-walking
  # lint lands, or the ratchet reaches zero, Prop. 2.2 becomes unconditional and the
  # residual bullet in Ch.2 §residuals retires.
  #
  # --- verification note for the NEXT scribe ---
  # Chapter-1 citation sweep at bp-104 (all 260 commits since bdcd9bc): every
  # \coderef path still resolves; the PRE_DECLARED_MAX snippet is byte-identical at
  # core/factory/roles.py:24; scripts/check_imports.py still fronts ops.import_lint.
  # The ONLY meaning-affecting drift found was dn-ouroboros-principal's flip to
  # `superseded` — repaired in place, three citations, plus a design-evolution remark
  # in Ch.2 §planes. Typographic repairs only elsewhere (two figures).
