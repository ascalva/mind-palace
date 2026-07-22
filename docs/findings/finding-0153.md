---
type: finding
id: finding-0153
status: open
created: 2026-07-21
updated: 2026-07-21
links:
  - docs/design-notes/agent-workflow.md                # the artifact-chain spec a deskcheck gate extends
  - docs/findings/finding-0148.md                      # K1 never minted — a "wave complete" that wasn't done
  - docs/findings/finding-0141.md                      # dreamer built-not-wired — sealed ≠ delivered
  - docs/findings/finding-0145.md                      # reference sensor: minting live, current-view half unbuilt
  - .claude/skills/verify                              # the agent's half of a deskcheck (drive it, observe behavior)
  - docs/DESKCHECK-QUEUE.md                            # the concrete queue this finding seeds
ftype: design
route: orchestrator
resolution: null
---

# Adopt a DESKCHECK gate + queue — "done" means demonstrated and owner-accepted, not sealed

## The problem (owner-named 2026-07-21)

We build a lot but don't follow through: work reaches `complete` in the plan ledger and is
treated as done, when "complete" only means *built + sealed + committed*. It does not mean
**wired**, **delivered** (a consumer uses it), or **owner-accepted**. The gap is a whole
missing state, and it has bitten repeatedly:

- **dn-synchronic-diachronic-dreamer** — bp-079..082 all sealed, but the dispatches are
  **built-not-wired** (`[dream_rnd] enabled=false`, no live entry point; finding-0141). Track
  never delivered.
- **reference sensor (PD-5 / finding-0145)** — F-edge minting is live, but the current-view
  materialize/serve/prune **was never built** (parking-lot: brainstorm). Track incomplete.
- **inner/outer core (M2)** — K1/K3 physical migration was **never minted**; "GRADUATION WAVE
  COMPLETE (6/6)" read as done when the program's physical half hadn't started (finding-0148).
- **Track G effectors** — built, dormant by design (finding-0011) — the *acceptable* version
  of the same shape, but only because it was made explicit.

## The owner's mechanism — the deskcheck (from his engineering practice)

"The work is not done until you can clearly show it working, or clearly show its state." A
**deskcheck** is a demonstration + acceptance gate: the builder declares *"ready to
deskcheck,"* then walks the reviewer (at the owner's job: tech lead + product owner; here: the
owner) through **(1) what was built, (2) how it was built, (3) any surprises, (4) it working
end-to-end OR its true current state** — and **the reviewer has the final say** on whether the
story / feature / track / task is done, or something is missing. Nothing is done until it
passes a deskcheck.

## Proposed integration into the artifact chain (a Fable design pass sizes it)

- **A new gate after `complete`:** `complete (built+sealed) → deskcheck-pending (in the queue)
  → [owner deskcheck] → done | needs-work`. `needs-work` spawns a follow-up plan or finding;
  `done` is the only terminal state that means delivered. This is owner-blessed like every
  other gate (the model presents; the owner decides).
- **The agent's half is `/verify` + the phone-build-report** — drive the flow, observe
  behavior, and present the deskcheck bundle (the 6-section report already carries what/how;
  add "here it is working / here is its state, and here is what is NOT done").
- **A deskcheck QUEUE** (`docs/DESKCHECK-QUEUE.md`, seeded now) — every sealed item enters it
  and stays until the owner deskchecks it. `/triage` surfaces the queue; the queue is the
  follow-through ledger the owner asked for ("built vs followed-through vs wired vs
  track-done").
- **Seal-time enforcement:** a build's seal must answer, explicitly — *built? wired? a consumer
  uses it? track complete or pending items? opened a new track/finding?* — and file the item
  into the queue. A "wave complete" claim must enumerate the design note's remaining stages,
  not the plan ledger ([[completion-claims-honesty]], now with teeth).

## Immediate adoption (before the full design pass)

1. The **queue exists now** (`docs/DESKCHECK-QUEUE.md`), seeded with the honest current
   backlog (sealed-not-deskchecked + built-not-wired).
2. Behavioral rule adopted to memory ([[deskcheck-discipline]]): on any build completion I say
   **"ready to deskcheck"** and present the bundle; I never call a track "done" — that verdict
   is the owner's.

## Routing

`design` → orchestrator. The full workflow integration (the gate, the state machine, the
seal-time enforcement, the `/deskcheck` ceremony) is a **Fable design pass**, bundled with the
integrator pass (finding-0151) for AFTER the current build tracks. The queue + behavioral rule
serve immediately.
