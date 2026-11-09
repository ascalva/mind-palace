"""How the store uses its embedder, and whether its lexical tokens are consistent, measured
(docs/experiments/embedder-use-2026-11-08.md, docs/design-notes/dn-embedder-use.md).

    uv run python -m eval.embedder_use <experiment> --cache DIR [--instance ROOT] [--out PATH]

One subcommand an experiment of the record: `tokens` (the lexical tokenizer and Unicode), `chunks`
(the chunk budget, in characters and in the embedder's tokens), `context` (the title in the
document template, late chunking), `prompts` (the query's task prompt), `dims` (Matryoshka
truncation, flat and rescored) and `edges` (semantic edges: a global threshold against thresholds
the data sets, and hubness corrections). Each writes its numbers as JSON; only aggregates leave a
run. The corpus instance is read only, the public sets come from local files, and every embedding
is cached by its input's text under `--cache`, so the experiments share the vectors they have in
common and an interrupted run resumes.
"""
