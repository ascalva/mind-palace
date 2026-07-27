---
type: finding
id: finding-0259
status: open
created: 2026-07-27
updated: 2026-07-27
links:
  - docs/design-notes/role-state-and-scoped-handoff.md   # §2.9 renders "The answer"; §2.11 puts handoff.md in the bundle
  - scripts/handoff.py                                   # render() — the "## The answer" section
  - scripts/handoff_drill.py                             # build_bundle
  - docs/build-plans/bp-127/plan.md                       # Item 17
ftype: design
origin_plan: bp-127
route: orchestrator
resolution: null
---

# F2's mechanical half is near-tautological for a `role` scope — the bundle contains the answer it asks the agent to reproduce

## What

Two ratified decisions meet, and their intersection was not examined at graduation:

- **§2.9** gives the DERIVED rendering a `## The answer` section: *"Unit in flight: …", "Next
  action: …"* — the generator's own structured answer, rendered into the document.
- **§2.11** puts that document in the drill's bundle: *"for `role:orchestrator`: `handoff.md` +
  the journal's authoritative segment."*
- **§2.11**'s mechanical pass/fail then asks the agent for exactly those two fields and compares
  them to `handoff.py --json`.

So for a role scope the drill hands the agent a document that **literally states the answer**, asks
for the answer, and compares it to the same computation that produced the document. MEASURED
2026-07-27 (bp-127 Item 17, first live run): PASS on both fields, $0.1833, 4.8 s. The bundle's
`handoff.md` opened with *"Unit in flight: bp-123 … Next action: `/resume bp-123`"* and the agent
returned `UNIT: bp-123` / `NEXT: /resume bp-123`.

## Why it matters

The mechanical half is, for this scope, mostly a **reading-comprehension check**. It tests that an
agent can copy a line out of a document it was handed — not that the handoff carries what a
successor needs, which is the claim §2.11 exists to falsify.

⚑ **It is not worthless, and the residual value is worth stating precisely**, because the obvious
over-correction (drop field (1)/(2) for role scopes) would throw it away:

1. **It detects a STALE committed rendering.** `handoff.md` is the committed artifact; `--json` is
   computed fresh from the tree. If the rendering has drifted, the agent answers from the stale
   pane and the compare FAILS. That is real — though it is also exactly what F1a (`--check`)
   already does, more cheaply and without tokens.
2. **It is a genuine test for the other two scopes.** `plan:<id>` is `plan.md` + its journal, and
   `track:<slug>` is a rendering with no `## The answer` section for a plan scope's unit. There the
   agent must actually *derive* the in-flight unit and next action from artifact state, which is
   the classic fresh-agent test and is not tautological at all.
3. **The `BLOCKED:` half is untouched by this.** Which unknowns a successor cannot resolve from the
   bundle is not stated anywhere in the bundle, so that half is doing real work at every scope. On
   the first live run it produced one genuine defect report — *"What is Item 2 owed on bp-123?"* —
   which is precisely the drill finding under-specified state.

## ⚑ The re-entry condition FIRED during the same session — and it settles this finding

The re-entry condition below asked for "the first `plan:<id>` drill run". It was run. MEASURED
2026-07-27, `--scope plan:bp-127`, $0.2679, 51 s:

| | agent (reading `plan.md` + the journal) | generator (`--json`) |
|---|---|---|
| `unit_in_flight` | `none` | `bp-127` |
| `next_action` | *"the sub-orchestrator's audit, then the two status flips"* | `/resume bp-127` |

**FAIL on both fields — and the agent was not wrong.** The journal's last entry says, in as many
words, *"**In-flight.** Nothing. All three items are closed."* and *"**Next action.** The
sub-orchestrator's audit, then the two status flips."* The agent read the NARRATIVE. The generator
read the plan's front matter, which still says `status: in-progress`, because flipping it is the
orchestrator's act and not the builder's.

Two conclusions, and the second is the more useful one.

1. **The plan-scope compare is a genuine derivation test.** It is not tautological, and it produced
   a real disagreement on its very first run. That confirms the claim above and makes option C
   concrete: the derivation claim belongs on `plan:`/`track:` scopes.
2. ⚑ **The mechanical compare disagrees with a CORRECT reader whenever narrative and status
   legitimately diverge** — and that window is not an edge case. It is exactly the interval between
   a builder sealing its journal and the orchestrator flipping the status, which is *precisely when
   §2.11's mandatory cadence fires* (*"mandatorily in any build plan that touches the handoff
   machinery"*). A drill run at its own mandated moment will report FAIL for a state that is
   correct and expected.

`[INFERENCE]` The clean resolutions are (i) treat a `plan:` scope whose journal carries a
`## Follow-through` block as sealed-pending-flip and expect `next_action` to be the flip, or (ii)
run the mandatory drill *after* the flip rather than at seal. Neither is ruled and neither is built;
(i) changes `handoff.derive`'s ladder, which is bp-124's contract and a design decision, not a
builder's.

## What is NOT claimed

- **Not that §2.9 should stop rendering `## The answer`.** It is the most useful thing in the
  document for a human, and the note's whole thesis is that derivable facts should be regenerated
  rather than remembered.
- **Not that the drill should be dropped.** Its unique product — the defect report — is unaffected.
- **Not that this was a graduation error.** Both decisions are individually right; nothing in the
  note or the plan asked anyone to consider their product.

## Options for the owner

| option | effect |
|---|---|
| **A — leave it** (default; what bp-127 ships) | the role drill's compare is a staleness check that duplicates F1a; the defect report carries the value |
| **B — make `role` scope's bundle the journal segment only**, dropping `handoff.md` | the compare becomes a genuine derivation test — but it stops testing the artifact the whole family exists to produce, and the successor loses the pane a real resume would have |
| **C — keep the bundle, and treat the role scope's compare as explicitly a staleness check**, letting `plan:`/`track:` carry the derivation claim | honest labelling, no machinery; the mandatory cadence would attach to a `plan:` scope |

`[INFERENCE]` C looks right — it costs nothing and stops the role drill's PASS being read as
evidence of something it did not test — but it is a re-reading of §2.11's acceptance and therefore
the owner's, not a builder's.

## Re-entry condition

The first `plan:<id>` drill run. If a plan-scope drill *fails* its compare where the role-scope
drill passes, that is direct evidence the role scope's PASS was carrying less information, and C
(or B) becomes an easy call.

## Routing

`design` → the orchestrator. It is a property of two ratified decisions taken together, and the
note is agent-immutable (A8).
