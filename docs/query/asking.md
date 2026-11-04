# Asking the palace — a question compiles to a sentence

How an agent, or the owner at a terminal, asks the palace for context (dn-query-sentence-algebra §3,
QL-3; first written as the `/context` skill, moved here when the `.claude/` controls were retired
on 2026-11-04). The palace answers **sentences**, not keywords
(`docs/design-notes/dn-query-sentence-algebra.md`).
A natural question is translated into one sentence over the sorts — a *field* (a score per note),
a *region* (a set of notes), a *chain* (moves with the notes reached) — and the compiler checks it,
plans it by proved rewrites and runs it read-only. **The model advises; code acts:** you propose
the sentence, the compiler decides whether it is well-formed, well-sorted and admissible, and the
executor returns data with its plan. Nothing here writes to the corpus.

## 1. Write the sentence

Verbs — the relation noun carries the edge letter (`S` similarity, `F` citation, `D` version,
`C` causal):

- **fields**: `near "<text>"` (semantic; the old SEARCH) · `diffuse S from <note> [beta <β>]`
  (the retrieval curve out of a note; the old DIFFUSE) · `far <field>` (the bounded reversal
  `1 − f`)
- **regions**: `reach F from <note> [depth <n>] [back|forward|both]` (citations; the old REACH) ·
  `relate <note>` (supports / contradicts / contextualizes) · `top <k> <field>` ·
  `atleast <t> <field>` · `not <region>` · `<region> minus <region>`
- **chains**: `trace <note> [forward|back]` (the version chain) · `walk from <note> [to <note>]
  via <path>` (a regular expression over `S F D C`: `F+`, `S{0,2}C+`)
- `witness "<edge id>"` (the record that minted an edge) · `read "<ref>" [chunk <n>]` (the text at a
  ref: a note, a dialogue turn, or a window of a curated paper — read before quoting; the one verb
  that returns content, so it composes with nothing)

Connectives, tightest first: the adjectives `within <region>`, `over <strata>`, `as of "<cut>"`;
then `and` / `minus`; then `or`; then `then` (`s then t` ≡ `t within region(s)`). Parenthesize to
override. `and` of a field and a region is the field masked by the region; `and` of two fields is
their product (HYBRID is `near "t" and diffuse S from <note>`). A `<note>` is a quoted path, digest
or title; a title that names several notes is refused with the paths to choose from.

Patterns:

| question | sentence |
|---|---|
| near a topic, among what a note cites | `near "sleep debt" and reach F from "health/sleep.md"` |
| the neighbourhood of a note, ranked by a topic | `top 10 near "x" within reach F from "n.md" depth 2` |
| near one thing, far from another | `near "x" and far near "y"` |
| what the citers of a note say about a topic | `reach F from "n.md" back then near "x"` |
| how a note reached another by citations | `walk from "a.md" to "b.md" via F+` |

Dials you leave unsaid come from the resolution ledger `docs/query/precedents.md` (β `1.0`, depth
`1`, `near` over `mirror_authored`, the `5` best scores of a bare field); the plan shows them.
`assume <hypothesis> in <sentence>` evaluates the sentence on the perturbed graph — `assume S "a" "b"
+0.5 in …` adds backbone weight, `assume sever F "a" "b" in …` cuts a citation, `assume contradict
"a" "b" in …` adds a negative relation — and answers as a `Hyp` beside the actual answer, with the
response class in the notes; the overlay is granted while `[query] hypotheticals` is on (the
owner's grant of 2026-11-04).

## 2. Run it, from the live checkout

```bash
mind-palace query 'near "sleep debt" and diffuse S from "health/sleep.md"' --as orchestrator
```

`mind-palace` on PATH resolves the live checkout (`~/mind-palace`, the live stores). From a
worktree, `uv run scripts/palace.py query …` reads that worktree's own test-made `data/`, which is
empty — do not read an empty answer there as "nothing in the notes". `--as <role>` labels the
asker for the sensor (`orchestrator`, `builder`, `scribe`, …) and grants nothing: every sentence
runs under the Ambassador's grant. `--json` for programs; `--no-plan` to shorten.

## 3. Read the answer

- **The plan rides with the answer**: the term tree, each clause's scope `Σ`/`E`/`T` and mode,
  the assumptions in force. Two sentences with the same plan mean the same thing.
- **Hits carry provenance** (`authored_solo`, `authored_dialogue`, …) and, for regions and chains,
  their detail (the sign and type of a relation, a chain's word). Cite the ref; read the note
  before quoting it.
- **`notes:` are part of the answer**: what this universe cannot answer (`D`/`C` moves at the note
  grain are empty), what a bare field shows. An empty answer is loud and says which bound emptied
  it — never a silent nothing.
- A **`Hyp`** result (under `assume`) is never an `Inv`: do not relay it as fact.

## 4. A refusal is a question back

`refused (parse | sort | scope | ambiguous | lookup | unsupported): <reason>` — the reason names
the production that failed, the sort rule, the plane no grant covers, the candidates, the unknown
note, or the evaluator this universe lacks. Rewrite the sentence with the word it names. Never
fall back to a nearest-neighbour mush that looks like an answer (falsifier QSF-3).

## 5. The lessons loop

A translation that failed — refused twice, empty where the owner's notes plainly hold the answer,
or answered from the wrong strata — is a **finding**: file a GitHub issue (`gh issue create`,
labels `type:investigation` or `type:defect` and `track:query-language`), quoting the question,
the sentence(s) tried and the plan. `mind-palace query --log` is the sensor: which strata served which
roles, the recent failed translations. A new default or a resolved ambiguity is recorded in
`docs/query/precedents.md` and its executable mirror `core/sentence/precedents.py` together, with a
re-entry condition — never a silent resolution.
