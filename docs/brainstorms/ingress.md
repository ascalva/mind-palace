---
type: brainstorm
id: ingress
track: query-language
created: 2026-11-05
status: open
links:
  - docs/design-notes/dn-ingress.md          # the design this warrants
  - docs/design-notes/dn-ingress-language.md        # its second form, after the owner's correction
  - docs/design-notes/dn-query-sentence-algebra.md
---

Called the door until 2026-11-05; renamed ingress at the owner's request.

# The ingress — the owner's seeds, 2026-11-05

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

Four seeds, then: the language is the ingress, so every action is a sentence; one ingestion with
the existing paths as its cases; many readers and one writer; embedding as the only serial
stage. The design note `dn-ingress` takes them in that order, and `formal/Palace/Ingress.lean`
holds the laws it rests on.

The owner, reading the first form's pull request the same day, verbatim:

> "hmm looking at pr 67, i realized that maybe there was some miscommunication, i didn’t want
> the language to support all these actions, like do a vault sync, do a dialogue sync, i wanted
> the language to be abstract and generic, so that all those ingestion use cases could be
> rewritten in it, an application of the generic language"

> "the language doesn’t know what dialogue is, but an interface/script uses the language to
> ingest data, store in a particular way and place, does that make sense? like python doesn’t
> know that i want to create a file called example.py, but it gives me the tools to write it"

> "don’t worry about the pr for now, redesign, prove , implement, test, audit first, then update
> the pr to reflect the new state"

> "yes, and how an operating system manages hardware resources, security, etc, mind palace
> manages data and its relationships, among other things, both are generic but powerful systems
> that create an abstraction layer to interface with"

> "another interesting thought based on something you said: budgets, a budget for a sentence is
> an interesting concept, reminds me of solidity (ethereum), where there is gas, or work
> associated, since some sentences are more costly, which means, the compiler/interpreter has to
> be able to translate a sentence to create computation in an optimized and efficient manner"

> "also, not sure if it’s too late, but feel free to make use of real compiler tools, from
> compiler compilers (eg yacc), to compiler back end tools (eg mlir, llvm), to properly making a
> consistent and secured type system"

> "of course, nested sentences should be allowed, with appropriate closure/code scoping"

> "another thought: i guess it makes more sense if the language is interpreted than compiled"

The first form had read "redefine all those ingestion paths" as one command word per path. The
correction: the language knows no path, and every path is written in it. The second form,
`dn-ingress-language`, takes the correction as its warrant.
