---
type: finding
id: finding-0009
status: open
ftype: discovery
origin_plan: null            # surfaced in /triage while regularizing bp-002/bp-003, not a build session
route: orchestrator
created: 2026-07-06
updated: 2026-07-06
links:
  - .claude/hooks/_lib.py (cmd_gate_check L313-331; Stop-gate paths _blessing_in_diff / _untracked_blessing)
  - docs/design-notes/agent-workflow.md (§6 blessing-detection contract; §10 owner-only gates)
  - docs/findings/finding-0005.md (same family — Bash-minted `ready` escaped the gate)
  - docs/findings/finding-0006.md (same family — comment on status line defeated the gate)
---

# finding-0009 — A plan flipped `proposed → complete` (or `→ in-progress`) escapes the readiness blessing

## Observation

`gate-guard`'s `cmd_gate_check` (`.claude/hooks/_lib.py:313-331`) denies exactly two
transitions, by **exact equality on the _new_ status value**: a design note `→ ratified`
(`:322`, `dn and new_status == "ratified" and cur != "ratified"`) and a build plan `→ ready`
(`:326`, `bp and new_status == "ready" and cur != "ready"`). Every other new value falls
through to `ALLOW` (`:330`).

So an agent editing a plan's `status` directly from `proposed` to `complete` — or to
`in-progress` — is **allowed**: it never sets the value `ready`, so the `new_status == "ready"`
guard does not fire, and no rule guards `complete`/`in-progress`. The plan reaches a terminal,
build-implying state **without the owner's `proposed → ready` blessing ever occurring.**
Confirmed by reading the code, not inferred: with `cur = "proposed"`, `new_status = "complete"`,
`cmd_gate_check` returns `ALLOW`. The two Stop-gate paths (`_blessing_in_diff`,
`_untracked_blessing`) likewise key on `ready`/`ratified`, so they do not catch it either.

## Why it matters

The `proposed → ready` gate exists so a graduated plan is owner-blessed before it is treated as
buildable (§6/§10 — the "owner-only, by hand" bright line). But the gate guards the *destination
value* `ready`, not *egress from `proposed`*. The one sanctioned way out of `proposed` (the
owner's hand-blessing to `ready`) can therefore be skipped wholesale by an agent jumping straight
to `in-progress`/`complete`. This is the same failure family as **finding-0005** (a Bash-minted
plan born at `ready` escaped the pre-hoc gate) and **finding-0006** (a comment on the status line
defeated the exact-equality compare): a bright line that a plausible, ordinary edit path silently
bypasses — the worst failure direction for a guardrail, because it *weakens* rather than
over-tightens.

## Recommended direction (owner ratifies at the gate)

Gate the **egress**, not just the destination: deny an agent transition **into** `in-progress` or
`complete` unless the on-disk `cur` is a legitimate predecessor — `in-progress` requires
`cur == "ready"` (or `in-progress`, idempotent); `complete` requires `cur in {"in-progress"}`.
Equivalently: no forward transition may reach a build-implying state without the plan having first
passed the owner's hand-made `ready`. Apply at `gate-guard` **and** both Stop-gate paths, for
parity with the A5 all-three-detectors rule. Candidate amendment **A7**, warrant this finding.
(Design of the exact predecessor table is the owner's ratification call; this finding only names
the hole and the direction.)

## Provenance

Surfaced during `/triage` (2026-07-06) while enacting the owner's ruling (`owner-questions.md`
oq-0002) to regularize bp-002/bp-003 — held at `proposed`, their work already committed — to
`complete`. The ruling is enacted by the **owner** hand-blessing `proposed → ready` and the
orchestrator then flipping `ready → complete`; it is deliberately **not** done by an agent
`proposed → complete` edit, precisely because this finding shows that path is ungated.
