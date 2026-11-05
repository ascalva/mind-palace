---
type: brainstorm
id: the-door
track: query-language
created: 2026-11-05
status: open
links:
  - docs/design-notes/dn-ingest-door.md          # the design this warrants
  - docs/design-notes/dn-query-sentence-algebra.md
---

# The door — the owner's seeds, 2026-11-05

The owner, after the causal moves landed and the question of actions came up, verbatim:

> "odd question, but could the query language be extended to actions as well? like a command to
> start dreaming, or even to ingest ? formalize ingest/update/state changes?"

> "let's rework the ingestion framework, the language should be able to unify these distinct
> ingestion methods, from there we should be able to either redefine all those ingestion
> paths/actions, the language is the door into the palace, from there, yes, we can enqueue, i
> assume we could have multiple reads but only one writer? i guess technically the only serial
> action for ingestion is just embedding"

> "and yes, let's design and prove first, let that guide the implementation, feel free to spawn
> different agents for reviewing/auditing/validating, keep working through design, proof,
> implementation, and audits"

Four seeds, then: the language is the door, so every action is a sentence; one ingestion with
the existing paths as its cases; many readers and one writer; embedding as the only serial
stage. The design note `dn-ingest-door` takes them in that order, and `formal/Palace/Door.lean`
holds the laws it rests on.
