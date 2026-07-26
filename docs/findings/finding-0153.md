---
type: finding
id: finding-0153
status: promoted
created: 2026-07-21
updated: 2026-07-26
links:
  - docs/design-notes/agent-workflow.md                # the artifact-chain spec a deskcheck gate extends
  - docs/findings/finding-0148.md                      # K1 never minted — a "wave complete" that wasn't done
  - docs/findings/finding-0141.md                      # dreamer built-not-wired — sealed ≠ delivered
  - docs/findings/finding-0145.md                      # reference sensor: minting live, current-view half unbuilt
  - .claude/skills/verify                              # the agent's half of a deskcheck (drive it, observe behavior)
  - docs/TRACKS.md                                     # the track board (portfolio view) this finding establishes
  - docs/DESKCHECK-QUEUE.md                            # the deskcheck-pending action-list view of the board
ftype: design
route: orchestrator
resolution: promoted — dn-track-board-and-deskcheck-gate (ratified, warrant: this finding) + bp-096/bp-097 (complete)
---

# Adopt a DESKCHECK gate + queue — "done" means demonstrated and owner-accepted, not sealed

> **Triage 2026-07-26 (session-52) — PROMOTED.** Fully absorbed into ratified design and shipped
> code. `dn-track-board-and-deskcheck-gate` is `status: ratified` with `warrant:` = this finding, and
> both plans it licensed (**bp-096** WF-1, **bp-097** WF-2) are `complete`. Live in the tree: the
> derived board and queue (`docs/TRACKS.md`, `docs/DESKCHECK-QUEUE.md`, both GENERATED banners, both
> git-tracked), the record store + template, the **third owner-only gate** (`_lib.py:635` denies an
> agent writing `verdict: approved|needs-work` pre-hoc), the clause-(f) seal tooth (`:711-731`), and
> `/triage` surfacing (`.claude/commands/triage.md:32-38`). Nine track manifests exist.
> **⚑ The mechanism has never been exercised, and that is now the live item — not a reopening of this
> finding:** `docs/deskchecks/` holds only `README.md`, i.e. **0 deskcheck records against 5 tracks
> owed**, and there is no `/deskcheck` command. Surfaced to the owner as an inbox item.

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

## The phase pipeline (owner spec 2026-07-21 — the swim-lane columns)

`brainstorm` (any model) → `design-pass` (**Fable required**) → `graduate` (Fable/Opus by size)
→ `build` (right model per job) → `audit` (Opus/Fable) → `deskcheck` (**Opus**, owner approves or
sends back) → **CLOSED**. Cross-cutting types, routed as before: **OQ** and **findings** — and,
owner-endorsed, **deskchecks-owed** is a third persistent surfaced inbox (raised every session +
triage until closed). Full pipeline + model-per-phase live in `docs/TRACKS.md` (the board).

## The tracking hierarchy (owner, 2026-07-21 — the unit above build plans)

Individual-track tracking doesn't scale with concurrent tracks, so the ontology has levels:
**item** (a build-plan item) ⊂ **build plan** (a session) ⊂ **track** (all design + all builds
+ wiring for one cohesive body of work — "the inner/outer core track") ⊂ **the board**
(`docs/TRACKS.md`, the portfolio view of every concurrent track). A *track* — not a plan — is
the unit that gets deskchecked and closed; a track is CLOSED only when the whole thing is
demonstrated and owner-approved. The board is the "another category of tracking" a team needs
when many tracks run at once; the orchestrator owns it and keeps every track visible until the
owner closes it.

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
