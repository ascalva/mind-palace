---
type: finding
id: finding-0237
status: open
created: 2026-07-27
updated: 2026-07-27
links:
  - scripts/board.py
  - scripts/docket.py
  - scripts/handoff.py
  - docs/build-plans/bp-124/plan.md
ftype: codebase
origin_plan: bp-124
route: builder
resolution: null
---

# Three repo-workflow scripts now share a scan surface, and the owner-question header regex is
# duplicated across two of them

## What

`scripts/board.py` gained `scan_oqs` (bp-124 Item 4) so the F-WF1 coordinate check can reach a
`track:` declared on an owner question. Parsing an owner question means knowing its section shape,
and `scripts/docket.py:114` already knows it:

```python
_OQ_HEADER = re.compile(r"(?m)^##\s+(oq-\d+)\b[ \t]*[—-]*[ \t]*(.*)$")
```

That pattern is now written twice. It is a small duplication, but it is a duplication of a
*format contract* — the shape of `docs/inbox/owner-questions.md` — and the two copies can drift
the moment the entry shape changes (a renumbering scheme, an em-dash convention, a nested entry).
`docket.py` additionally parses `- status:` / `- blocking:` bullets with its own regex, where
`board.scan_oqs` returns the whole `- key: value` bullet map; the second is a superset of the
first, so the duplication is real rather than coincidental.

## Why it was not fixed in place

Two constraints, both from bp-124:

1. **`scripts/docket.py` is not in bp-124's `write_scope`.** Rewiring it onto `board.scan_oqs` is
   an edit to a file this plan may not touch, and routing around a scope denial is never the move.
2. **`scripts/handoff.py`'s imports are pinned** by the plan's Item 2 invariant to stdlib + `_lib`
   + `board`. Having `board` import `docket` (the other direction) would have satisfied DRY at the
   cost of coupling two peer scripts through a private name, and would make `board` inherit
   `docket`'s module-level `sys.path` mutation for one regex.

So the single implementation was placed in `board.py` — which bp-124 §4 already designates as the
shared scan surface (`scripts/handoff.py` reuses `scan_plans` / `scan_notes` / `scan_findings` /
`scan_oqs`) — and the duplication is recorded here with a comment at the site.

## Why it matters

`docs/inbox/owner-questions.md` is the only artifact class with no front matter of its own, so its
shape lives entirely in regexes rather than in `_lib`'s parser. Every consumer that grows one is a
place the shape can be got wrong silently: `docket.py` would simply stop listing an entry, and
`board.py` would simply stop checking its coordinate. Neither failure is loud.

## The ask

**Not urgent, and deliberately not done here.** When a plan next holds `scripts/docket.py` and
`scripts/board.py` together (or a third derived view appears — the extraction trigger bp-124 §11
already records), do one of:

- point `docket.py`'s `_scan_oqs` at `board.scan_oqs` and delete its private regexes; **or**
- extract the shared scan surface into a module both import, which is the same re-entry condition
  bp-124's parked-decisions table names for `board`'s other scanners.

The second is the better end state once a third consumer exists; the first is a two-line change
available today to any plan whose scope covers both files.

## Re-entry condition

Nothing is blocked. **Re-entry:** the next build plan whose `write_scope` covers both
`scripts/board.py` and `scripts/docket.py`, or any change to the `## oq-NNNN` entry shape in
`docs/inbox/owner-questions.md` — at which point BOTH copies must move together, and this finding
is the record that there are two.

## Routing

`codebase` → **builder**. It is settleable against the code with no design question in it; it is
open only because the fix needs a `write_scope` this plan does not hold.
