---
type: track
slug: query-language
title: Query language — the sentence algebra, its compiler, and the surface
status: active
warrant: null
audit_refs: []
dod:
  - QL-0 the design proved — dn-query-sentence-algebra ratified with its composition laws machine-checked in formal/Palace/Sentence.lean (sorts, connectives, adjectives, the modality, the chain language, the response laws), attacks and controls green
  - QL-1 the compiler as pure functions — grammar, type checker, scope checker, planner over the existing Scope/Grant, each planner rewrite a transcription of a proved law with its property test
  - QL-2 the executor — clause evaluators over the existing stores, the mask/column/product/threshold operators, the product-automaton walker, the overlay for assume
  - QL-3 the surface — palace query, a /context skill, the resolution ledger, the query log as a sensor
  - QL-4 the falsifier battery run — composed sentences against flat search on owner-endorsed answers, a finding either way
backlog_deskcheck: null
links:
  - docs/design-notes/dn-query-sentence-algebra.md
  - docs/brainstorms/query-sentence-algebra.md
---
# Track — Query language (the sentence algebra, its compiler, and the surface)

The identity card for the query-language track, minted alongside its founding note
(the scored-beliefs and mathematical-foundations precedent; ⚑ the owner renames or
rejects this coordinate at the merge). **Scope:** the query sentence algebra over the
core — nouns as sorts, adjectives, connectives, the `assume` modality — the compiler
that parses, checks, plans and explains a sentence, the surface agents and the owner
ask through, and the measurement that decides whether composed sentences beat flat
search. Members are the artifacts declaring `track: query-language`.

**Not in scope:** the scope algebra itself (`core/kernel/scope.py`, ratified and
machine-checked under `mathematical-foundations`); the retrieval mathematics (the
β-curve, the transports, the magnetic fibers: `dn-temporal-retrieval-algebra`,
`dn-magnetic-laplacian`); the Librarian's and the Ambassador's RAG machinery, which
become clients of the sentence; `core/` changes before the owner's ratification.

## Relationship to other tracks

`mathematical-foundations` proves the laws this track's compiler transcribes; the
design theorems live in `formal/` and enter the ledger as rows when code relies on
them. `fiber-geometry` designed the chain language (FG-3) and parked its build on a
consumer (FG-d); the `via` adjective is that consumer. `workflow` owns the claim
ladder the design note's grades come from.
