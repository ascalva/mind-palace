---
type: finding
id: finding-0196
status: routed
created: 2026-07-25
updated: 2026-07-26
links:
  - docs/audits/ops-wave-2026-07-25.md
  - docs/book/chapters/02-architecture.tex
  - docs/book/figures/core-rings.tex
  - core/kernel/rings.py
  - core/sealing.py
ftype: spec-defect
origin_plan: orchestrator
route: orchestrator
resolution: routed — a SCRIBE fix, not a design change; and it is invisible to the next scribe (absent from SYNC.md)
---

# Two Chapter 2 assertions outrun their mechanism at the edition ref

> **Triage 2026-07-26 (session-52) — both defects live, verbatim, and the chapter is untouched.**
> (a) `INNER` has exactly **43** members of which **six** are not under `core/kernel/` — computed
> live: `core`, `core.complex`, `core.ingest`, `core.stores`, `core.temporal`, `core.typedshims`,
> declared permanent split-package residue at `core/kernel/rings.py:46-57`. But
> `02-architecture.tex:586-590` and `figures/core-rings.tex:38-39` both define the outer ring as
> `core/**` minus `core/kernel/**`, **mis-locating those six**.
> (b) *"unconditionally"* is still unqualified at `02-architecture.tex:263-264` and `:1114`, while
> `core/sealing.py:16-17` states the native-extension bypass the chapter itself quotes 50 lines later.
> **No owner ruling and no design change needed** — the ratified source (`dn-inner-outer-core` §2.5
> present-tense vs §2.7/M3 end-state) already says the right thing; the chapter mis-tensed it.
> **⚑ And it is invisible to the next scribe:** `grep 0196 docs/book/SYNC.md` → **zero hits**, while
> siblings 0183/0184/0185 are all in the `open:` block (`:139-158`).
> **Queue as item 1 of the next `/scribe` sync plan**, `write_scope` covering
> `02-architecture.tex`, `figures/core-rings.tex`, `SYNC.md` — restate the outer ring as
> `core/** minus INNER` naming the six residues, replace both "unconditionally" sites with this
> finding's weaker-true phrasing, and **add finding-0196 to `SYNC.md`'s `open:` list**. Carry
> finding-0185's Chapter-2 item in the same pass — one file, one visit.

## What
(a) RING GEOMETRY — `02-architecture.tex:586-594` and `figures/core-rings.tex:33,38` state
"the ring is 43 modules, and it physically lives in one subtree, `core/kernel/**` ... the
outer ring is the complement — `core/**` minus that subtree." But `core/kernel/rings.py::INNER`
has 43 members of which SIX are not under `core/kernel/`: `core`, `core.complex`,
`core.ingest`, `core.stores`, `core.temporal`, `core.typedshims` — documented at
`rings.py:44-57` as permanent split-package residue, not migration debt. The ratified source
separates the statements: §2.5 says "outer = core minus inner" (present tense); §2.7/M3 says
"core/** minus kernel" as the END-STATE, conditioned on gates that are open at the ref
(map != kernel-tree; ratchet = 20). So the chapter's stated definition of the outer ring is
wrong at HEAD and mis-locates 6 modules.

(b) "UNCONDITIONALLY" — `:262-265` and `:1114` say the runtime guard and kernel anchor "hold
the property unconditionally". Contradicted by `core/sealing.py:16-18` (a native extension
bypasses a Python-level guard — which the chapter itself QUOTES 50 lines later) and by the
`pf` anchor being inert. The chapter retracts both in §residuals; the word is unqualified
where it is USED.

## Why it matters
These are the mirror form of the ⚑ falsifier Item 2 exists to catch: not invention from
nothing, but a FUTURE claim in the record asserted as a PRESENT property. Non-negotiable #1
is the one place a weaker-true claim must not be traded for a stronger one — and the
chapter's own thesis is that this codebase prefers the weaker claim that is true.

(b) is a one-word fix: "unconditionally" -> "at run time and, once the anchor is loaded, at
the kernel". (a) needs the geometry restated as `core/** minus INNER`.

Generator worth naming: both defects came from citing a ratified §-number correctly while
changing the TENSE of the claim inside it. Citation-EXISTENCE checks are automatable;
tense-fidelity is not, and is where invention actually hides.
