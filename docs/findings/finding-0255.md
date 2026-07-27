---
type: finding
id: finding-0255
status: open
created: 2026-07-27
updated: 2026-07-27
links:
  - docs/design-notes/erratum-relation.md
  - ops/chat_sensor.py
  - docs/build-plans/bp-129/plan.md
ftype: spec-defect
origin_plan: orchestrator
route: orchestrator
resolution: null
---

# `dn-erratum-relation` §5 cites `message.role`; φ_chat actually keys on the top-level `record["type"]`

## What

`docs/design-notes/erratum-relation.md:204-205` states:

> φ_chat 1.0.0 mapped `message.role: user` → `speaker='owner'` (`ops/chat_sensor.py`,
> `_ROLE_TO_SPEAKER`), and the harness delivers hook output inside user-role records.

The cited symbol is real, but the field it is keyed on is not `message.role`. Ground truth,
`ops/chat_sensor.py:124`:

```python
speaker = _ROLE_TO_SPEAKER.get(str(record.get("type", "")))
```

with `_ROLE_TO_SPEAKER = {"user": "owner", "assistant": "agent"}` at `:64`. The map is applied to
the **top-level JSONL record's `type`** field. `message` is fetched separately at `:127` and only
its `content` is read (`:132`); `message.role` is never accessed anywhere in the module.

The note's *conclusion* is unaffected — hook output does arrive in records typed `user`, and the
139 rows are genuinely mis-attributed. Only the mechanism's citation is wrong.

## Why it matters

Small on its face, load-bearing in one specific place: **the builder of φ_chat 2.0.0 must
discriminate on the right field.** A1.1/A2 add `speaker='system'`, which requires deciding *what
signal separates a hook/harness record from an owner turn*. An implementer working from the note's
prose would look for a discriminator beside `message.role`; the actual decision point is the
top-level record shape, where different fields are available. Choosing the wrong locus is the kind
of error that produces a correct-looking interpreter that mis-classifies a different subset — the
same class of defect the erratum relation exists to record.

It is also, precisely, an instance of `docs/brainstorms/the-unchecked-claim.md` occurring **inside
the design that is the remedy for it**: a claim citing a symbol rather than the line, carried at an
unmarked hop. Recording it is cheap; the shape is worth more than the digit.

## Re-entry condition

No criterion is parked on this. `bp-129` §3 Q7 and §4 record the ground truth so no builder in the
erratum wave inherits the error, and no plan in the wave touches `ops/chat_sensor.py`.

Re-entry is at **whichever plan first modifies φ_chat** (the parked re-projection half, `bp-129`
§11 PD-C): that plan must ground its discriminator at `ops/chat_sensor.py:124` and must not
inherit the note's prose.

## Routing

`spec-defect` on a **ratified** design note ⇒ **route: orchestrator**. `dn-erratum-relation` is
agent-immutable; only the owner's hand can amend it. The correction is offered as an owner-hand
amendment (the A1/A2 idiom this very note formalizes in its §6 table: *"ratified notes → owner-hand
amendment (A1 idiom) — the gate IS the authority; no store record"*), or the owner may judge a
one-line imprecision not worth an amendment and close this as recorded-only. Either is a legitimate
disposition; the finding exists so the choice is made rather than defaulted.
