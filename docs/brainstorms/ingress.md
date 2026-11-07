---
type: brainstorm
id: ingress
track: query-language
created: 2026-11-05
status: open
links:
  - docs/design-notes/dn-ingress.md          # the design this warrants
  - docs/design-notes/dn-ingress-language.md        # its second form, after the correction of the first
  - docs/design-notes/dn-query-sentence-algebra.md
---

Called the door until 2026-11-05.

# The ingress — the seeds, 2026-11-05

The seeds, set down after the causal moves landed and the question of actions came up:

- The query language should extend to actions: a command to start dreaming, or to ingest.
  Ingestion, updates and state changes should be formalized.
- The ingestion framework should be reworked so that one language unifies the distinct ingestion
  methods, and every ingestion path and action can be redefined in it: the language is the way
  into the palace. From there actions can be enqueued; many readers may run beside one writer,
  and the only inherently serial stage of ingestion is embedding.
- Design and proof come first and guide the implementation. Agents review, audit and validate
  along the way, working through design, proof, implementation and audits in that order.

Four seeds, then: the language is the ingress, so every action is a sentence; one ingestion with
the existing paths as its cases; many readers and one writer; embedding as the only serial
stage. The design note `dn-ingress` takes them in that order, and `formal/Palace/Ingress.lean`
holds the laws it rests on.

The correction, made on reading the first form's pull request (#67) the same day:

- The language should not support one action per ingestion path (a vault sync, a dialogue sync).
  It should be abstract and generic, so that every ingestion use case can be rewritten in it, as
  an application of the generic language.
- The language does not know what a dialogue is; an interface or script written in it ingests
  data and stores it in a particular way and place. A general-purpose language does not know
  which file a program will create, but gives the program the means to write one.
- The pull request waits: redesign, prove, implement, test and audit first, then update it to
  reflect the new state.
- As an operating system manages hardware resources and security, the palace manages data and
  its relationships, among other things. Both are generic systems that put an abstraction layer
  between a program and what it touches.
- A budget for a sentence: some sentences cost more work than others, as transactions on
  Ethereum cost gas, so the interpreter must be able to turn a sentence into computation in an
  optimized and efficient way, and must know what a sentence costs.
- Real compiler tools are welcome, from parser generators (yacc) to compiler back ends (MLIR,
  LLVM), toward a consistent and secured type system.
- Nested sentences are allowed, with closure and code scoping.
- The language is interpreted rather than compiled.

The first form had read the requirement to redefine every ingestion path as one command word per
path. The correction: the language knows no path, and every path is written in it. The second
form, `dn-ingress-language`, takes the correction as its warrant.
