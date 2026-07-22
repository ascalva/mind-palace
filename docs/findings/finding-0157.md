---
type: finding
id: finding-0157
status: routed           # open → routed → resolved | promoted
created: 2026-07-22
updated: 2026-07-22
links:
  - docs/build-plans/bp-090/plan.md
  - docs/build-plans/bp-091/plan.md
  - docs/design-notes/inner-outer-core.md
  - docs/findings/finding-0156.md
ftype: direction         # blocker | spec-defect | question | discovery | direction
origin_plan: null        # discovered by the owner's "why is the pipeline failing" investigation
route: orchestrator      # a process/prevention decision
resolution: immediate breakage FIXED (98bc7b2); this finding is about preventing recurrence
---

# The `pages` CI is the only gate that catches core-refactor doc drift — and no builder can fix it

## What

The GitHub `pages` workflow (mkdocs + mkdocstrings) went red at the K3 seal and
stayed red. Cause: K1/K3 (bp-090/bp-091) relocated **8 modules** into
`core/kernel/**` with **no re-export shims** (by design), but the hand-maintained
mkdocs API pages (`site/api/*.md` + the `mkdocs.yml` nav) still named the old
`core.*` import paths, so `mkdocstrings` could not collect them and the build
aborted (`core.matching`, then `core.complex_types/constitution/mirror/provenance/
recursion/recursion_ops/selfcheck`). Fixed in `98bc7b2` (repointed to
`core.kernel.*`; build now exits 0). **The `ci` (test) workflow was green
throughout — only `pages` caught it.**

## Why it matters — three compounding gaps

1. **The local attestable-green gate does not run the mkdocs build.** The gate is
   ruff · mypy · type_gate · pytest only. A doc-collection break is invisible to
   it, so K1/K3 passed every local + `ci` check and still shipped a red `pages`
   deploy. The failure is only ever seen post-push, in a workflow nobody watches.
2. **No builder could have fixed it even if it noticed.** K1/K3's `write_scope`
   was `core/** tests/** …` — `site/**` and `mkdocs.yml` were out of scope. This
   is the exact drift class as finding-0156 (bp-092's `core/provenance.py`
   write_scope): a relocation invalidates references that live **outside** the
   relocating plan's capability. The mover can't fix the reference; the reference
   silently rots.
3. **The API pages are hand-maintained flat module lists** — they enumerate
   `::: core.X` per module, so every single module move requires a manual
   `site/api/*.md` + nav edit or the build breaks. This will recur on CI-1..4
   (bp-092–095, which also touch `core/`) and every future ring migration.

## Options (owner/orchestrator decision)

- **A — cheap, prevents the silent-post-push failure:** add the mkdocs build
  (`uvx … mkdocs build`) to the pre-push / attestable-green gate so doc drift
  reddens locally like ruff. Add `site/**` + `mkdocs.yml` to the `write_scope` of
  any plan that relocates modules (a graduation checklist item, paired with the
  finding-0156 "scan for out-of-scope references the move invalidates" rule).
- **B — kills the drift class entirely:** replace the hand-maintained `site/api/*`
  pages with `mkdocs-gen-files` + `mkdocs-literate-nav` auto-discovery, so the API
  surface is generated from the actual package tree and a module move needs zero
  doc edits. Larger change; the right long-term shape.
- Recommended: **A now** (mechanical, immediate), **B graduated onto the
  inner-outer-core or a tooling track** (the kernel split makes the flat "core"
  nav increasingly wrong — it lists kernel modules flatly under "core — the sealed
  kernel"; a generated nav would mirror the ring structure).

## Routing

`direction` → orchestrator. Pair with **finding-0156** (the sibling write_scope
drift): both are "a relocation invalidates a reference outside the mover's
capability." A graduation-time rule ("when a plan relocates modules, scan for and
carry every out-of-scope reference: write_scopes, mkdocs pages, import strings")
would prevent both. Belongs to the **inner-outer-core** track's follow-through and
any future migration.
