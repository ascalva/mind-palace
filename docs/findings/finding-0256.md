---
type: finding
id: finding-0256
status: open
created: 2026-07-27
updated: 2026-07-27
links:
  - docs/design-notes/chat-sensor.md
  - docs/design-notes/erratum-relation.md
  - docs/roles/orchestrator/readings.md
  - docs/build-plans/bp-131/plan.md
ftype: spec-defect
origin_plan: orchestrator
route: orchestrator
resolution: null
---

# The mis-attribution class is broader than the 139 — and A1.2's "closed" channel set omits a channel

## What

Re-deriving the chat census read-only at graduation (`sqlite3 "file:data/chatlog.sqlite?mode=ro"`,
2026-07-27) produced **two** results that do not match the record.

**1. The broader-match figure does not reproduce.** The seat's readings pane
(`docs/roles/orchestrator/readings.md`, row `2026-07-27T14:53Z`) records:

> Rows beginning literally `Stop hook feedback:` and attributed to `speaker='owner'`: 139
> (broader match, hook text anywhere in an owner row: **146**).

Measured now:

| predicate | count |
|---|---|
| `speaker='owner' AND text LIKE 'Stop hook feedback:%'` | **139** ✓ (matches) |
| `speaker='owner' AND text LIKE '%Stop hook feedback%'` | **141** ✗ (pane says 146) |
| `speaker='owner' AND text LIKE '%hook feedback%'` | 141 |
| `speaker='owner' AND text LIKE '%Stop hook%'` | 141 |
| `speaker='agent' AND text LIKE '%Stop hook feedback%'` | 0 |

The **139** — the figure A2 ratifies and the whole wave depends on — **reproduces exactly**
(33 distinct sessions, `interpreter` uniformly `1.0.0`, `observed_at` 2026-07-18…07-25, of 9,145
total utterances; sampled rows are genuine hook output). Only the parenthetical broader figure
does not. No predicate tried yields 146; the pane's own row does not record which one it used.

**2. The 2 extra rows are a *different* mis-attribution channel.** Inspecting the two rows that
*contain* `Stop hook feedback` without *beginning* with it: both are the **`update-config` skill's
own documentation text**, injected into a user-role record —

```
# Update Config Skill | | Modify Claude Code configuration by updating settings.json files. |
| ## When Hooks Are Required (Not Memory) | ...
```

— at `turn_index` 10 and 1 of two different sessions. This is machine-injected harness text stored
as `speaker='owner'`. It merely *mentions* "Stop hook"; it is not hook feedback.

⇒ **The rows the corpus wrongly attributes to the owner are a strictly larger set than the 139.**
Skill/harness injection is a further source, and `dn-chat-sensor` A1.2 states the channel set is
**closed and enumerated** at three (ordinary turn / queued prompt / structured answer), with the
falsifier: *"any stored row whose `speaker` is `owner` or `agent` while its text originates from a
hook, gate, or harness notice."* These rows trip that falsifier while matching channel 1
structurally.

## Why it matters

- **A1.2's closure claim is incomplete.** The enumeration is asserted closed; a channel outside it
  demonstrably produces owner-attributed rows. Closure is the property the whole taxonomy rests on
  — an unenumerated channel means *"every consumer of speaker attribution must treat stored rows as
  untrusted"* stays true even after the 139 are corrected.
- **It is direct evidence for PD-1** (`dn-erratum-relation` §3: enumerate targets at assertion, keep
  the generating predicate as *evidence* only). A predicate (`LIKE '%Stop hook feedback%'`) would
  have swept these 2 rows into the erratum's target set. They are mis-attributed, but they are
  **not** what A2's warrant covers, and an authority's assertion must not silently widen past what
  was examined. The parked act must enumerate the **139**, not re-run a predicate.
- **It is the 39→139 error recursing one level out.** A2 corrected a count within a class; this
  finds the *class itself* was drawn too narrowly. Same shape, same cause: a census generalized at
  an unmarked hop (`the-unchecked-claim`).
- **A reading in the seat's MEASURED pane does not reproduce.** That pane's contract is that its
  rows are results of *running* something. One row's parenthetical is unreproducible and its
  literal command is unrecorded. Small, but the pane's value is that it can be trusted without
  re-derivation.

## Re-entry condition

No criterion is parked. The wave proceeds on the **139**, which reproduces exactly.

Three concrete re-entry points:
1. **`bp-131`** carries the 2 rows as **decoy fixtures** — rows that contain the hook text but must
   *survive* the correction, proving enumeration rather than predication (its §7 Item 2).
2. **A full census of the mis-attribution class** — every owner-attributed row whose text did not
   originate with the owner — is owed before any φ_chat 2.0.0 plan claims to close the gap. That
   census is **not** this wave's work.
3. **A1.2's closure** re-enters at the owner's hand if he judges the omitted channel worth an
   amendment.

## Routing

`spec-defect` against a **ratified** note (`dn-chat-sensor` A1.2) ⇒ **route: orchestrator**, and
owner-level: only his hand can amend a ratified note, and only he can decide whether "closed and
enumerated" should be re-opened to admit a harness-injection channel. Batched to
`docs/inbox/owner-questions.md` rather than blocking — the wave's 139-row basis is unaffected.

The readings-pane discrepancy is separately trivial to settle: append a fresh row with the literal
command, per that file's own append-only *"a row is never edited to refresh it"* rule. ⚑ Not done
here — `docs/roles/**` is outside this sub-orchestrator's write scope while another wave holds it.
