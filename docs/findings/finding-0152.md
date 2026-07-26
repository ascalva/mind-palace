---
type: finding
id: finding-0152
status: resolved
created: 2026-07-21
updated: 2026-07-26
links:
  - docs/design-notes/session-handoff-gate.md          # the Stop-audit clause family this interacts with
  - .claude/hooks/journal-gate.sh                        # clause (c) blessing-transition audit
  - docs/design-notes/blessing-ceremony-lazygit.md      # (if present) the blessing ergonomics
ftype: direction
route: orchestrator
resolution: resolved — bp-097 D6 landed the gate-aware yield (_lib.py:844-850, :803-814) + the 2026-07-25 agent-commits-the-flip rule
---

# The bless/ratification handoff is clunky — the agent burns tokens polling for a commit the owner is about to make by hand

> **Triage 2026-07-26 (session-52) — RESOLVED.** Both halves are closed. The gate-aware fix the
> finding named as its real target shipped in **bp-097 (`complete`)**: clause (c) now emits the yield
> posture instead of the commit-or-revert nag — `.claude/hooks/_lib.py:844-850`, *"if it is the
> owner's staged hand, say so once and YIELD … do not poll, do not re-ask"* — and the (b2) sibling
> gap found during that build got its own additive-front-matter yield (`:803-814`), deliberately
> conservative (any body change still hard-blocks, `:676`). The D6 design ruling is
> `dn-track-board-and-deskcheck-gate:216`.
> The **ergonomic** half is closed by the 2026-07-25 ceremony rule (the agent commits the owner's
> staged flip after verifying the diff is the status line alone) — there is no longer anything to
> poll across.

## The friction (owner-reported 2026-07-21)

When the owner stages a blessing/ratification (proposed→ready, draft→ratified) but hasn't
committed yet, the current loop is wasteful:
1. The Stop-audit clause (c) fires on the uncommitted blessing transition every turn — the
   agent sees "commit it or revert" repeatedly.
2. The agent, unable to commit (owner-only) and unwilling to revert the owner's edits,
   **spins up shell `until`-loop watchers to wait for the commit**, which time out, fail,
   and get re-spawned — a token sink for zero value.
3. Meanwhile the agent re-asks/re-explains each turn, adding noise.

The owner is doing exactly the right thing (blessing by hand); the harness makes the agent
*thrash* around that manual step instead of quietly parking.

## What good looks like

The agent should recognize "a blessing is staged and mine is not the hand that commits it,"
state the ready-to-commit artifact ONCE (the pre-loaded message), and then **go quiet /
yield the turn** — no polling watcher, no re-asking, no repeated Stop-loop churn. The Stop
gate's clause (c) is correct to flag an uncommitted flip, but its remedy for an *owner-staged*
one should be "yield to the owner," not "agent must resolve it now."

## Candidate fixes (a design pass sizes; not decided here)

- **Behavioral (cheapest):** a standing rule/memory — never arm a wait-watcher for an
  owner-manual commit; state the loaded message once and end the turn. (I can adopt this now.)
- **Gate-aware:** clause (c) distinguishes an *owner-staged blessing* (the diff is exactly a
  status flip in a plan/note the owner is editing) from an *agent-mediated flip* (the real
  target), and emits a quiet "owner blessing staged — yielding" instead of the
  commit-or-revert nag.
- **Ergonomic:** a cockpit/lazygit affordance that commits the pre-loaded message in one
  keystroke, closing the staging→commit gap the agent keeps waiting across.

## Routing

`direction` → orchestrator. Pairs with `dn-session-handoff-gate` (the clause-(c) home) and the
blessing-ceremony ergonomics. Immediate mitigation: the behavioral rule is adopted to memory
this session; the gate-aware fix is a small design pass when prioritized.
