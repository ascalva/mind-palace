---
type: experiment-report
experiment: embedder-input-lengths
run: 1
status: complete
started: 2026-11-08
links:
  - docs/experiments/embedder-input-lengths-2026-11-08.json   # the counts
  - eval/embed_input_lengths.py                               # the harness
  - core/ingest/embed.py                                      # the fit these figures size
---

# The embedder's input lengths, measured (2026-11-08)

**Question.** How many of the texts a store embeds are longer, in the embedding server's tokens,
than the server's batch of 2,048, which it refuses rather than truncates? A chunk's budget of 1,200
characters does not bound its tokens.

## Method

- **The working instance:** `uv run python -m eval.embed_input_lengths --lance <data>/vectors.lance
  --template 'title: none | text: {text}'`, every text of the vector store's chunks table, read
  only.
- **The corpus instance:** `... --instance <root> --sample 2000 --chunks 5000 --seed 7 --template
  'title: none | text: {text}'`, up to 2,000 items a source drawn from its catalog, their bytes
  read from its raw store and chunked as the landing chunks them, at most 5,000 chunks a source.
- Each text is counted by the server's `/tokenize` with special tokens, the document template
  applied as the embedder applies it. Only counts leave the run.

## Results

| set | texts | median | 99th pct. | 99.9th pct. | max | chars/token | over 2,048 |
|---|---|---|---|---|---|---|---|
| working instance (all) | 17,328 | 255 | 439 | 493 | 616 | 3.33 | 0 |
| corpus: arxiv | 3,936 | 136 | 328 | 387 | 426 | 4.84 | 0 |
| corpus: gutenberg | 5,000 | 245 | 586 | 925 | 1,117 | 4.41 | 0 |
| corpus: hackernews | 5,000 | 231 | 345 | 484 | 1,360 | 4.11 | 0 |
| corpus: openalex | 3,649 | 137 | 334 | 463 | 811 | 4.79 | 0 |
| corpus: stackexchange | 2,995 | 202 | 491 | 1246 | 1,347 | 3.84 | 0 |
| corpus: wikipedia | 5,000 | 216 | 346 | 496 | 622 | 4.55 | 0 |

No text in either set exceeds the batch. The working instance's longest text takes 616 tokens; the
corpus's tails reach 1,360 (Hacker News) and 1,347 (Stack Exchange). The corpus's full vector phase
(1,338,585 embeddings, the corpus's stage-1 vector run) met one text the server
refused: a Hacker News comment of 1,145 characters at 2,951 tokens, cut to 701 characters. A sample
of 25,580 chunks is not expected to contain an event at that rate.

## Caveats

- One sample of the corpus, one seed; the working instance read once, as it stood.
- The counts are the server's tokenizer for this model; another model or server moves them.
