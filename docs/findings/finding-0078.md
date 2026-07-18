---
type: finding
id: finding-0078
status: resolved             # open → routed → resolved | promoted
created: 2026-07-14
updated: 2026-07-18
links:
  - .claude/hooks/scope-guard.sh
  - docs/templates/build-plan.md
  - docs/build-plans/bp-036/plan.md
ftype: spec-defect       # blocker | spec-defect | question | discovery
origin_plan: bp-036
route: builder           # codebase | spec-fidelity → builder / tooling
resolution: resolved 2026-07-18 (triage) — see the Triage resolution section below
---

# scope-guard matches write_scope entries verbatim — an inline `# comment` silently blocks every write

## What

`bp-036`'s `write_scope` annotated each path with an inline YAML comment
(`- core/ingest/logseq.py            # a deterministic strip_properties() helper`). `scope-guard.sh`
compares a target file path against the write_scope entries **as literal strings** and does NOT strip
the trailing `#`-comment, so `core/ingest/logseq.py` fails to match `core/ingest/logseq.py   # …` and
EVERY in-scope write is denied — the build cannot start. A real YAML parser would drop the comment; the
hook's line-based extraction does not.

## Why it matters

Inline comments in `write_scope` read as legitimate documentation (the rest of the plan template uses
them freely), but here they are load-bearing-breaking and fail *silently* into a total build block. The
denial message even prints the commented strings as the scope, which is the tell — but a plan author has
no warning at authoring time. It cost a mid-build stop + an owner-gated write_scope correction.

## Re-entry condition

Not parked (worked around by bare-path write_scope). Fix opportunistically, either: (a) `scope-guard.sh`
(and `_lib.py`'s write_scope reader) strip an inline `# …` from each entry before matching — the robust
fix, matches YAML semantics; or (b) the build-plan template / graduate skill state explicitly that
`write_scope` entries MUST be bare paths (no inline comments) and a lint checks it. Recommend (a).

## Routing

`spec-fidelity` → builder/tooling. Non-blocking once write_scope is bare paths. Batch for the next
tooling touch or `/triage`.

## Triage resolution (2026-07-18)
Fixed at source (commit 4afa2d8, bp-067 session): write_scope entries are now bare globs — the rule landed in `docs/templates/build-plan.md` + `.claude/skills/build-plan/SKILL.md`, and scope-guard's quoted-vs-unquoted comment behavior is documented. **finding-0085 and finding-0104 are the SAME footgun re-found** (three times total); all closed by this fix. Memory `[[write-scope-quoting]]` strengthened.
