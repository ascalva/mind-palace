---
type: finding
id: finding-0006
status: promoted
created: 2026-07-05
updated: 2026-07-06
links:
  - .claude/hooks/_lib.py
  - .claude/hooks/gate-guard.sh
  - docs/templates/build-plan.md
  - docs/design-notes/agent-workflow.md
  - docs/build-plans/bp-003/plan.md
ftype: discovery
origin_plan: orchestrator
route: orchestrator
resolution: "promoted → agent-workflow.md amendment A5 (status-value normalization as part of the blessing-detection contract, §6). Mechanical fix landed by bp-004: _lib.py `_normalize_status` applied at `status_of`, `_status_in_text`, and `_blessing_in_diff` (all three blessing detectors now fire on a comment-bearing ready/ratified; nospace `ready#x` deliberately not stripped); template line 4 status comment removed. Harness: docs/build-plans/bp-004/acceptance/run.sh."
---

# A trailing `#` comment on a `status:` line defeats every blessing gate

## What
Surfaced while `/scribe` minted `bp-003` from `docs/templates/build-plan.md`. The template's
status line (line 4) is `status: proposed          # proposed → ready → in-progress → complete
| parked | superseded`. Minting a plan verbatim from it reproduces that inline comment, and the
session-brief then rendered the plan's status as `proposed          # proposed → ready → …`
— because the front-matter parser does **not** strip a trailing `#` comment.

The parser gap is general and load-bearing for enforcement. `_lib.py`'s `_scalar` (L171–175),
`_status_in_text` (L253–259), and `parse_front_matter` (L157–167) strip surrounding whitespace
and quotes but **not** a trailing `# …`. The three blessing detectors then compare the status
value by **exact string equality**:
- gate-guard `cmd_gate_check` (L304/308): `new_status == "ratified"` / `== "ready"`;
- Stop-gate tracked-diff `_blessing_in_diff` (L395/397): `val == "ratified"` / `== "ready"`;
- Stop-gate untracked `_untracked_blessing` (L430/432): `status_of(f) == "ratified"` / `== "ready"`.

So `status: ready   # anything` parses to the value `ready   # anything`, which `!= "ready"`,
and **every** detector fails to recognize the blessing. A trailing comment is an
enforcement-invisible blessing.

**Empirically verified** (isolated temp repo + stdin, each with a clean-status control proving
the test is non-vacuous):

| path | `status: ready  # comment` | control `status: ready` |
|---|---|---|
| gate-guard (pre-hoc Edit gate) | **ALLOW, rc=0** (write permitted) | DENY, rc=2 |
| Stop-gate (c) A3 untracked detector | **rc=0** (no block) | rc=2, cites the blessing |

## Why it matters
`§10` makes the two blessing gates (`draft→ratified`, `proposed→ready`) owner-only,
"mechanically enforced, not steered" — a bright line on the security plane. This defeats that
enforcement on **all three** paths at once, *including* the pre-hoc gate-guard Edit path that
finding-0005 left intact (0005 escaped only the post-hoc Bash backstop; this also escapes the
front gate). An agent can bypass the pre-hoc gate deterministically by appending `  # x` to the
status line — and, more insidiously, the project's **own build-plan template models the
comment-on-status-line pattern**, so the escape is reachable by ordinary template-following
habit, not just deliberate attack. Low intent required, high invariant at stake — the same
adversarial-machinery class as finding-0003/0005.

The failure is one-directional: it only ever produces a **false negative in the blessing
direction** (a `proposed # …` line is still `!= "ready"`, correctly not a blessing), so it
silently *weakens* enforcement rather than over-blocking — the worst failure direction for a
guardrail, because nothing surfaces it in normal use.

## Re-entry condition
Owner picks a resolution (below), or a real session is observed reaching a blessed status via a
comment-bearing status line. Until then the default holds: the gates enforce clean status lines;
a comment-bearing `ready`/`ratified` line is a documented known gap — and the template should be
treated as if it *will* be hit, since it models the pattern.

## Options (owner/orchestrator to decide)
- **(a) Normalize the status value before comparison** — surgical; closes the hole at its root.
  In the status-specific extractors (`status_of` and `_status_in_text`), strip a trailing YAML
  comment: cut the value at the first ` #` (space-hash, matching YAML comment semantics) and
  rstrip, so `ready   # x` → `ready` and all three detectors fire. Scope it to the status path
  (not every scalar) to avoid touching fields where `#` may be legitimate. A one-plan `_lib.py`
  change + a harness regression (comment-bearing `ready` blocks; decide the `ready#nospace`
  no-space case). **Recommended.**
- **(b) Fix the template too** — drop the inline comment from `docs/templates/build-plan.md`
  line 4 (the real plans bp-000/001/002 already omit it; bp-003 was corrected to a clean
  `status: proposed`). Good hygiene but **insufficient alone**: any comment on a `ready`/
  `ratified` line, template-sourced or not, still escapes without (a). Do (a) **and** (b).
- **(c) Amend `agent-workflow.md §6`** to specify status-value normalization as part of the
  blessing-detection contract, warrant-linked here (the design-changing path, as A1/A3 were).
  On owner acceptance this flips to `promoted`.

Recommendation: **(a) + (b)**, optionally **(c)** to record the normalization contract in the
spec. **Not blocking** — `bp-003` sits at a clean `status: proposed` and nothing in flight is
blocked; this is the reflection loop reporting a gap the scaffolding accidentally surfaced.

## Routing
`discovery` → `route: orchestrator`. Options (a)/(b) are a pure code + template refinement (a
one-session builder plan, no spec edit). If the owner wants the enforcement *contract* tightened,
that mints an `agent-workflow.md §6` amendment warrant-linked here (→ `promoted`). Outside any
active plan's scope either way.
