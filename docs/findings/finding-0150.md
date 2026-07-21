---
type: finding
id: finding-0150
status: open
created: 2026-07-21
updated: 2026-07-21
links:
  - docs/design-notes/code-ingest-pipeline.md          # §5-3 (partial vs full) — ANSWERED: FULL
  - docs/design-notes/code-observation-projection.md   # the superseded note
  - docs/findings/finding-0146.md                      # the warrant chain
ftype: design
route: orchestrator
resolution: recorded
---

# Owner ruling — FULL supersession of dn-code-observation-projection (answers §5-3), and the non-goal lesson

## The ruling (2026-07-21, at ratification)

The owner answered `dn-code-ingest-pipeline` §5-3 (partial vs full) as **FULL**, setting
`superseded_by: dn-code-ingest-pipeline` on the projection note, with the stated reason:
*"the code-observation-projection dn was wrong — I explicitly have been wanting code and
doc strings ingested/embedded, and I didn't realize then that that was never in scope…
what was the point of that design note if the real purpose was out of scope."*

Disposition of the successor's §2.6 "partial" argument: overruled by the owner — when the
note's ORGANIZING FRAME (structure-only, semantics never) is rejected as the intended
design, the note is superseded whole; its machinery clauses survive via the successor's
§2.6 absorption table (quoted clause-by-clause), so the live stores' design record is not
orphaned. The completing hand edit (optional, owner-only): flip the projection note's
`status: ratified → superseded` — the three-place-relation shape of the
dn-ouroboros-principal precedent (`215070d`). Until then the front-matter pointer carries
the ruling; no tooling treats `superseded_by` as gating (only φ_doc mints a citation edge).

## The root defect, named (audit + owner reading agree)

The projection note's §2.1 generalized the 2026-07-11 owner ruling — a PROVENANCE ruling
("code is not authored corpus; the repo is an instrument") — into an EMBEDDING exclusion
("code text never enters the vector corpus", §1.2 + PD-b) the owner never stated. An
inference about intent was written as a non-goal, ungraded, and passed the ratification
gate unnoticed for ten days while the semantic blindness it mandated (finding-0146)
accumulated.

## The process lesson (saved to memory: non-goals-are-load-bearing)

Non-goals/out-of-scope clauses are the highest-blast-radius sentences in a design note:
they silently narrow intent and nothing downstream re-examines them. Two obligations
follow: (1) composing — a non-goal derived from an inference about owner intent carries
`[INFERENCE]` like any other claim, so the gate sees it; (2) at ratification — the §1.2
list deserves the owner's explicit read ("is anything here something I actually want?").

## Routing

`design` → orchestrator; resolution: recorded (the ruling is executed — front matter set
by the owner's hand at `4eb80c8`/`0c2deae`; only the optional status flip remains).
