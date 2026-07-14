---
type: finding
id: finding-0073
status: open
created: 2026-07-13
updated: 2026-07-13
links:
  - docs/build-plans/bp-029/plan.md
  - cloud/fetcher/sources.py
  - docs/design-notes/external-grounding.md
ftype: codebase
origin_plan: bp-029
route: builder
---

# arXiv open-access full text is deferred — PDF is not extractable in the stdlib-only fetcher

## What

bp-029 Item 27 names Europe PMC **and arXiv** as the open-access full-text tail. On building it
I settled arXiv to **default-DENY** (`open_access=True`, `full_text=None`, DISTILLED-only) for a
concrete, code-grounded reason:

- The cloud fetcher is **stdlib-only by contract** (`cloud/fetcher/sources.py` docstring: "Stdlib
  only (`urllib`, `xml`, `json`) so the Lambda zip is dependency-free") — no PDF or LaTeX parser.
- arXiv's full text is a **PDF** (`arxiv.org/pdf/{id}`) or a **LaTeX source tarball**
  (`arxiv.org/e-print/{id}`). Neither is extractable to clean text with the stdlib. arXiv's native
  HTML (`arxiv.org/html/{id}`) exists only for recent LaTeX submissions and is not universal.

So embedding arXiv full text would require either a non-stdlib dependency in the Lambda (breaks
the dependency-free contract) or an HTML path with partial coverage — both "embed on a guess"
risks the plan's §10 stop-and-raise forbids. **Europe PMC OA (`fullTextXML`, JATS XML — stdlib
`xml.etree`) is the working open-access tail** and is fully implemented + tested (Item 27).

## Why it matters

Not a blocker: the licence gate default-denies, so arXiv correctly stays DISTILLED-only and the
EMBED tail ships with a real open-access source (Europe PMC). But arXiv is the primary venue for
the math/CS design-grounding corpus (the seed cards are mostly arXiv/journal), so the open-access
subset that actually embeds is narrower than the plan imagined until an arXiv text path exists.

## Resolution (deferred, builder-routed)

Deferred to a follow-up: add an arXiv full-text extraction path that respects the fetcher's
dependency posture — options, in preference order: (1) the arXiv **HTML** endpoint
(`arxiv.org/html/{id}`) parsed with stdlib `html.parser`, gated on availability (graceful None
fallback) — stdlib-clean, partial coverage; (2) a **separate** enrichment step outside the
Lambda zip (an owner curation-time act, §2.6) that may use a PDF library, keeping the Lambda
dependency-free. Until then arXiv is DISTILLED-only. Annotated in `sources.py` (arxiv record) +
the module docstring. Continuing the build (Europe PMC path complete).
