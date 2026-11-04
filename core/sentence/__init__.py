"""The query sentence algebra — a query is a typed sentence, compiled to a plan whose rewrites
are theorems (dn-query-sentence-algebra; the laws in `formal/Palace/Sentence.lean`).

A query used to be one word: `(verb, scope)` in `core/query.py`. Here it is a sentence over sorts.
Nouns are values of a sort — a *field* (a score per note, a kernel's column), a *region* (a set of
notes), a *chain* (moves with the notes reached), a *witness* (the record that minted an edge).
Verbs are operators between sorts, and the relation noun they walk carries the edge letter:

* field verbs: `near "<text>"` (the embedding kernel's column: the old SEARCH), `diffuse <rel> from
  <note> [beta <β>]` (the retrieval curve's `e^{−βd}` column: the old DIFFUSE), `far <field>` (the
  bounded reversal `1 − f`);
* region verbs: `reach <rel> from <note> [depth <n>] [back|forward|both]` (reachability: the old
  REACH), `relate <note>` (the signed relation edges: the old RELATED), `top <k> <field>` and
  `atleast <t> <field>` (the two lossy bridges from a field), `not <region>`, `<region> minus
  <region>`;
* chain verbs: `trace <note> [forward|back]` (the version chain along D: the old HISTORY), `walk
  from <note> [to <note>] via <path>` (the chains a regular language over `{S, F, D, C}` admits,
  by the product automaton);
* `witness "<edge id>"` (the C fiber: the old ORIGIN).

Connectives: `and` (the Schur product on fields, intersection on regions, a field masked by a
region), `or` (the convex mixture, union), `then` (the left clause's region masks the right).
Adjectives: `within <region>`, `over <strata>`, `as of <cut>`. The modality `assume <hypothesis>
in <sentence>` evaluates a sentence on the perturbed graph; its result is a `Hyp`, never an `Inv`.
HYBRID is no longer a verb: it is the sentence `near "<text>" and diffuse S from <note>`.

The pipeline: `parse` (grammar.py) → `typecheck` (types.py: sorts, the clause-wise scope check,
the mode per clause) → `compile_sentence` (plan.py: the normal form, the intermediate form) →
`execute` (execute.py, against a `Universe`). `ask` runs all four against the live stores;
`ask_logged` (surface.py) is what the surfaces call — `palace query` and the Ambassador's `query`
tool — recording every sentence asked in the query log, the sensor `palace query --log` reads.
"""

from __future__ import annotations

from core.sentence.execute import (
    Evaluator,
    Overlay,
    SentenceAnswer,
    Universe,
    UnsupportedSentence,
    ask,
    execute,
)
from core.sentence.grammar import ParseError, parse, quote
from core.sentence.legacy import sentence_of
from core.sentence.plan import Plan, compile_sentence, normalize
from core.sentence.surface import (
    QueryLog,
    ask_logged,
    render_text,
    run_query,
    sentence_grant,
    summarize,
)
from core.sentence.types import (
    AmbiguousSentence,
    Clause,
    IllScopedSentence,
    Sort,
    SortError,
    admissible,
    clauses_of,
    hyps_of,
    is_inv,
    sort_of,
    typecheck,
)

__all__ = [
    "AmbiguousSentence",
    "Clause",
    "Evaluator",
    "IllScopedSentence",
    "Overlay",
    "ParseError",
    "Plan",
    "QueryLog",
    "SentenceAnswer",
    "Sort",
    "SortError",
    "Universe",
    "UnsupportedSentence",
    "admissible",
    "ask",
    "ask_logged",
    "clauses_of",
    "compile_sentence",
    "execute",
    "hyps_of",
    "is_inv",
    "normalize",
    "parse",
    "quote",
    "render_text",
    "run_query",
    "sentence_grant",
    "sentence_of",
    "sort_of",
    "summarize",
    "typecheck",
]
