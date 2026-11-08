# The sentence language on one page

A query is a sentence: verbs over nouns, joined by connectives, narrowed by adjectives. It
compiles to a plan, runs read-only and answers with hits, their provenance and notes. Try it in
`mind-palace shell` (Tab completes, `help <verb>` explains, `plan <sentence>` shows the plan
without running it). The full guide is `docs/query/asking.md`; the design is
`docs/design-notes/dn-query-sentence-algebra.md`.

## Grammar, loosest to tightest

```
sentence := or-expr ("then" or-expr)*
or-expr  := and-expr ("or" and-expr)*
and-expr := unary (("and" | "minus") unary)*
unary    := operand ("within" operand | "over" stratum+ | "as of" "<cut>")*
operand  := "far" operand | "not" operand | "top" n unary | "atleast" t unary
          | "assume" hypothesis "in" sentence | "(" sentence ")" | clause
```

A `<note>` is a quoted path, digest or title (a bare path works when it is one word). A relation
letter is `S` similarity, `F` citation, `D` version, `C` causal; a `<path>` is a regular
expression over them (`F+`, `S{0,2}C+`, `(S|F)+`). A sentence is a *field* (a score per note), a
*region* (a set of notes), *chains*, a *witness* or a *text*.

## Verbs

<!-- verbs:begin (generated from the parser by tests/unit/test_sentence_shell.py) -->
- **and** `<s> and <s>`: a field (the product, or a field masked by a region) or a region (the meet). Example: `near "x" and reach F from "n.md"`
- **as of** `<s> as of <text>`: the sentence with the citation graph read at that commit. Example: `reach F from "core/query.py" as of "HEAD"`
- **assume** `assume S|F|D|C <note> <note> [+|- <number>] in <s>` · `assume sever S|F|D|C <note> <note> in <s>` · `assume contradict <note> <note> in <s>`: a Hyp: the answer on the perturbed graph beside the actual one, never an Inv. Example: `assume sever F "a.md" "b.md" in reach F from "a.md" depth 3`
- **atleast** `atleast <number> <s>`: a region: the notes whose score reaches the threshold. Example: `atleast 0.5 near "x"`
- **diffuse** `diffuse [S|F|D|C] from <note> [beta <number>]`: a field: the retrieval curve e^(-beta d) out of the note. Example: `diffuse S from "health/sleep.md" beta 2`
- **far** `far <s>`: a field: the bounded reversal 1 - f of a field. Example: `near "x" and far near "y"`
- **minus** `<s> minus <s>`: a region: the left region without the right. Example: `reach F from "a.md" minus reach F from "b.md"`
- **near** `near <text>`: a field: a score per note, the embedding kernel's column at the text. Example: `near "sleep debt"`
- **not** `not <s>`: a region: the complement of a region in the universe. Example: `reach F from "a.md" and not reach F from "b.md"`
- **or** `<s> or <s>`: a field (the convex mixture) or a region (the union). Example: `near "x" or near "y"`
- **over** `<s> over <strata>`: the sentence evaluated on the named strata instead of the default. Example: `near "x" over curated reference`
- **reach** `reach [S|F|D|C] from <note> [depth <n>] [forward|back|both]`: a region: the notes reachable along the relation, with their hops. Example: `reach F from "core/query.py" depth 2 back`
- **read** `read <note> [chunk <n>]`: the text at a ref: a note, a turn, or a window of a paper or a repo file. Example: `read "core/sealing.py" chunk 2`
- **relate** `relate <note>`: a region: the notes a signed relation edge ties to the note. Example: `relate "health/sleep.md"`
- **then** `<s> then <s>`: the right sentence, masked by the left one's region. Example: `reach F from "n.md" back then near "x"`
- **top** `top <n> <s>`: a region: the k best of a field, with their scores. Example: `top 10 near "x"`
- **trace** `trace <note> [forward|back|both]`: chains: the note's version chain along D. Example: `trace "health/sleep.md" back`
- **walk** `walk from <note> [to <note>] via <path> [depth <n>]`: chains: the paths a regular language over S F D C admits. Example: `walk from "a.md" to "b.md" via F+`
- **within** `<s> within <s>`: the left sentence restricted to the right one's region. Example: `near "x" within reach F from "n.md" depth 2`
- **witness** `witness <text>`: the record that minted an edge, or the attestation a receipt names. Example: `witness "e-1"`
<!-- verbs:end -->

## Strata: what `over` scopes

With no `over`, a sentence reads `mirror_authored`: the owner's own notes and words.
`over <strata>` evaluates the clause it qualifies on the named strata instead (several may be
named): `mirror` the notes, `dialogue` every chat turn (`dialogue_transcript`,
`dialogue_artifact` its parts), `curated` the papers and the system's own docs, `reference`
the repository's code and docs (`reference_repo` its part). An adjective binds to the operand
before it, so `near "x" and reach F from "a.md" over reference` scopes only the `reach`. Each
clause answers within its own strata, and the plan lists the scope each clause needs.

## What a result carries

- **hits**: refs ranked best first, each with its title, score or detail (hops, a relation's
  sign, a chain's word) and its provenance label in brackets (`[authored-solo]`,
  `[observed]`, ...). A field shows its best 5 unless `top k` says otherwise.
- **the plan**: the normal form, each clause's scope and mode, the assumptions under `assume`.
- **notes**: the universe's `missing` list (the support's census, the cut the citation graph was
  read at, what this universe cannot answer) and every truncation. An empty answer says why.
- under `assume`, a **Hyp**: the assumed hits beside the actual ones; never relay it as fact.

## Five composed sentences

1. `near "sleep debt"`: the notes nearest a phrase.
2. `top 10 near "sleep debt" over mirror dialogue`: the ten best among the notes and the chats.
3. `near "sleep debt" and reach F from "health/sleep.md" depth 2`: ranked by the phrase, masked
   to what a note cites within two hops.
4. `reach F from "core/query.py" back then near "scope" over reference`: what the files citing
   `core/query.py` say about scope.
5. `assume sever F "docs/a.md" "core/x.py" in walk from "docs/a.md" via F+ depth 3`: the
   citation chains out of a document if one citation were cut, beside the actual ones.
