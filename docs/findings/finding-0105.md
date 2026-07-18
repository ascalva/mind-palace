---
type: finding
id: finding-0105
status: open
created: 2026-07-18
updated: 2026-07-18
links:
  - ops/lifecycle/launcher.py                      # gate_cmd (:251) + start()/deploy() (:271, :388)
  - tests/unit/test_core_self_containment.py        # the red-by-design ratchet the gate now trips on
  - docs/build-plans/bp-066/plan.md                 # where the intentional red was introduced
re_entry: owner decides the deploy-gate policy during the self-containment red period (options below)
ftype: direction
origin_plan: orchestrator
route: orchestrator
resolution: null
---

# The red-by-design ratchet BLOCKS `palace deploy` for the whole self-containment cleanup period

## What
Discovered while diagnosing why Ouroboros is in recovery (owner asked 2026-07-18). The promotion gate
`Launcher.deploy` runs (launcher.py:251):

    uv run pytest -q -m "not live and not podman and not needs_vault and not needs_restic"

That is the deterministic suite — which is now **RED by design**: `test_core_self_containment` fails at
19 (bp-066's ratchet) and carries no `live`/`podman`/`needs_*` marker, so the gate selection runs it and
the gate FAILS. Therefore **`palace deploy` cannot promote the live daemon onto HEAD** for the entire
period the ratchet is red (bp-066 → the cleanup reaching zero, bp-068 + the 16 machinery inversions).

The escape hatches exist but each has a cost:
- `palace deploy --skip-tests` — bypasses the WHOLE gate (all tests + the intentional one), not just the
  ratchet. Loses the real regression signal.
- `palace start --force` — resumes on the current working-tree HEAD, but UNGATED (no suite, no CI check,
  no graceful successor verification). It runs whatever is checked out.

## Why it matters
The owner chose the red as a forcing function (bp-066). A non-obvious consequence is that it also
freezes the *gated* deploy path — so the live system cannot be safely promoted onto HEAD (which now holds
the chat sensor, the connectivity refactor, and the config move) by the normal, verified route until the
cleanup finishes. During a multi-plan cleanup that could be several sessions, that is a real operational
gap: HEAD keeps advancing while the daemon can only be updated by an ungated `--force`/`--skip-tests`.

## Options (owner decision)
- **(A) Teach the gate to deselect the ONE intentional test.** Change `gate_cmd` to
  `… -m "…" --deselect tests/unit/test_core_self_containment.py::test_core_imports_nothing_outside_core`
  (or a `not selfcontainment_red` marker on it). The gate then enforces everything EXCEPT the
  known-intentional red, so gated deploys work throughout the cleanup and regain full strength
  automatically when the test goes green. **Orchestrator leans (A)** — smallest, keeps the gate honest.
- **(B) Freeze gated deploys until green.** Accept that the daemon stays on its current commit (or is
  moved only by an explicit `start --force`) until the ratchet reaches 0. Simplest; leaves the live
  system behind HEAD for the cleanup's duration.
- **(C) Deploy with `--skip-tests` when needed.** Pragmatic but blunt — drops the regression gate too.

## Routing
`direction` → orchestrator → owner (the deploy-gate policy). Surfaced by the Ouroboros-recovery
diagnosis; independent of the recovery itself (that is a separate fail-safe — see PROGRESS 2026-07-18).
