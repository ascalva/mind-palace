---
type: finding
id: finding-0219
status: routed
created: 2026-07-26
updated: 2026-07-26
links:
  - docs/design-notes/dn-autopilot-and-delegated-blessing.md   # §2.2 the <= 40-line / ~300-word cap; §2.9 invariant 2
  - docs/build-plans/bp-120/plan.md                            # §6 the pinned counting rules; §7 Item 3's falsifier; §11 row 3
  - scripts/capsule.py                                         # LINE_CAP / WORD_CAP, validate()
  - tests/unit/test_capsule.py                                 # the realistic-capsule bound that does hold
ftype: spec-defect
origin_plan: bp-120
route: orchestrator
resolution: >-
  Batched to the owner as **oq-0054** at the 2026-07-26 sweep (three candidates carried verbatim: (a) character cap, (b) max token length, (c) accept + amend §2.2). Not applied: §2.2 is agent-immutable (A8), so any cap change is a superseding note or an owner-ratified amendment. Ruling lands naturally at bp-120's deskcheck.
---

# The capsule's "too long to genuinely read" cap is unbounded in characters — a 38 KB capsule passes `validate` on 39 lines and 227 words

## What

**Context in one line, so this is self-contained.** `dn-autopilot-and-delegated-blessing`
(ratified) designs *autopilot*: the owner grants the `proposed → ready` blessing remotely, via
an MFA code bound to the sha256 of an **intent capsule** — an agent-written SMART readback of the
ask that the owner reads on his phone. `bp-120` built that capsule as a typed artifact
(`docs/templates/intent-capsule.md` + `scripts/capsule.py`). The note's §2.2 caps the capsule:

> Hard size cap: **≤ 40 lines / ≈ 300 words** — a capsule too long to genuinely read on a
> phone defeats the read. [DERIVED]

`bp-120` §6 pins that into two mechanical counts (a *word* is a maximal run of non-whitespace
characters; *lines* is `\n`-separated lines of the canonical text), both hard errors, and §11 row 3
records them as deliberately **not configurable** ("a cap the run can raise is not a cap").

**This is bp-120 Item 3's named falsifier, and it fired.** The falsifier, verbatim from the plan:

> **Falsifier:** a capsule passing `validate` that a human would call unreadable-on-a-phone — the
> cap is measuring the wrong thing and §2.2's "too long to genuinely read" needs a different proxy
> than lines+words.

Measured against the built tool at bp-120's completion, both cases pass `validate` with **zero**
diagnostics:

| capsule | lines | words | characters | `validate` |
|---|---|---|---|---|
| all eight fields filled, plus one unbroken 8,000-char token | 18 / 40 | 161 / 300 | **9,177** | passes |
| all eight fields filled, plus 30 lines of seven 180-char tokens | 39 / 40 | 227 / 300 | **38,122** | passes |

Neither count is wrong; both are exactly what §6 pins. The gap is that **lines × words does not
bound the size of the text**, because neither counts characters and a "word" has no maximum
length. The realistic bound *does* hold — a genuine capsule for the owner's own named ask
(markdown spell-check, §1.1's example) measures 17 lines / 159 words / ~1 KB, and the empty
template 18 lines / 168 words — so this is not the opposite defect (a cap too tight to hold a real
capsule, which §10 named as a `spec-defect` against §2.2 and which did **not** occur).

## Why it matters

The cap is not ergonomics; it is the enforcement of the design's central claim. §2.1 argues the
blessing gate exists for **comprehension**, and §2.2 turns "I believe you understand" into four
checkable facts, the first being that the owner *read* the text. Invariant 2 — *"No code verifies
against a text the owner did not read"* — is what the cap protects: the owner's read is the only
detector for the finding-0150 defect class (wrong non-goals, which nothing downstream ever
catches).

The threat model is the specific reason this matters rather than being a curiosity about
adversarial input: **the capsule is agent-authored** (§2.2: "the agent restates, the owner verifies
the restatement"). The thing the cap must bound is the length of a text an agent produces and the
owner is asked to read. A proxy that admits 38 KB does not bound it. Under the standing rule that
a property is real only when something **proves** it, `≤ 40 lines / ≤ 300 words` currently proves
"is not many lines and not many words" — not "is a phone-sized read".

The practical failure is not a forged grant (the hash binding is unaffected, and an obviously
enormous capsule is self-defeating on a phone — the owner would simply decline). It is the quieter
one: the cap reads as a guarantee in §2.2 and in the template's own header, so a later reader
reasonably concludes the capsule's size is bounded when it is not, and the render plan (AP3) may
be built assuming a bound the artifact does not carry.

## Candidate resolutions (a ruling, not the builder's to make)

Deliberately **not** applied in bp-120: §6 pins the two counts exactly, §11 row 3 forbids making
caps configurable, and adding a third cap changes a pinned interface — which is a design act, not
a build one. Options, cheapest first:

- **(a) Add a character cap alongside the two counts** — e.g. `≤ 2,000 characters` of canonical
  text, which the realistic 1 KB capsule clears with room and which bounds the read directly. One
  constant and one diagnostic in `scripts/capsule.py`, one line in the template header. It makes
  the *character* count the real cap and lines/words the readability shaping — arguably what §2.2
  meant all along.
- **(b) Add a maximum token length** (no single non-whitespace run longer than ~60 characters).
  Narrower: it kills the pathological case without capping honest length, and it doubles as a
  paste-accident detector. Does not bound total size on its own; pairs with (a).
- **(c) Accept it and say so.** Amend §2.2 to state that the cap bounds *shape*, not *bytes*, and
  that the owner's read is the backstop for a capsule that is merely enormous. Cheapest, but it
  weakens a stated guarantee, which is a constitutional edit and must not happen silently.

(a) or (a)+(b) is the builder's read of the intent, but §2.2 is agent-immutable (A8), so any
change to the cap is a **superseding note or an owner-ratified amendment**, never an edit.

## Re-entry condition

**Nothing is parked** — bp-120's four items all closed and its gates are green; the tool implements
exactly the pinned §6 caps and its tests record this boundary explicitly rather than hiding it.
Re-entry is for the *design*: when the owner rules among (a)/(b)/(c) — naturally at bp-120's
deskcheck, where §11 row 3 already anticipates him tuning the cap — the caps change in
`scripts/capsule.py` and `docs/templates/intent-capsule.md` **together** (that row's own
condition), under a plan whose write_scope names both. AP3 (the capsule render to the exhaust
lane) should not assume a byte bound until then.

## Routing

`spec-defect` against a **ratified** note, and the correction is design-level (it changes what the
mechanism must enforce, and it touches a guarantee §2.2 states) ⇒ `design` → **orchestrator** →
batched to `docs/inbox/owner-questions.md`. Not builder-resolvable: bp-120 §6 pins the counts and
§11 row 3 pins their non-configurability, so a builder tightening the cap would be redesigning a
pinned interface. Per §4 reconciliation discipline this finding is the announced correction; any
plan that changes a cap carries a banner citing it.
