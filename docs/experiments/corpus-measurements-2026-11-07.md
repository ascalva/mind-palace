---
type: experiment-report
experiment: corpus-measurements
run: 1
status: complete
started: 2026-11-07
links:
  - docs/design-notes/dn-corpus-instance.md                 # the design these figures size
  - docs/experiments/corpus-measurements-2026-11-07.json    # the raw numbers: ratios, throughput, rates
  - docs/experiments/vector-quantization-2026-10-30.md      # the recall figures the vector options cite
  - docs/experiments/profile-2026-11-06.md                  # the latency baseline the staged plan re-measures
  - core/kernel/ingest/chunk.py                             # the chunker the counts use (1200 / 150)
---

# The corpus instance's measurements (2026-11-07)

**Question.** What does a gigabyte of open text cost the palace, in compressed raw bytes, in chunks and
so in vectors, and in embedder time on this machine? The design note `dn-corpus-instance` sizes a
100 GB instance from these ratios; nothing here was ingested into any store.

## Method

Samples of six open sources were fetched into a scratch directory outside every checkout (88 MB of
data plus a 21 MB catalogue), each reduced to the form that would land (plain text, markup removed),
then measured: UTF-8 bytes, `zstd` at levels 3, 9 and 19 and `gzip -6` on the concatenated text,
and the repository's own chunker (`chunk_text`, 1,200 characters with 150 of overlap) for the chunk
count. The embedder was timed against the stack's own service on port 8081 (EmbeddingGemma-2 Q8_0,
768 dimensions, four slots, context 8,192), with the chat model on port 8080 checked idle through
its `/slots` before every configuration, in six bounded configurations of 512 chunks each, 3,000
chunks in all drawn interleaved from five sources. A single-query probe was timed idle and once
beside each running configuration, as another caller would see it.

| sample | how | fetched | text |
|---|---|---|---|
| Wikipedia | 24.1 MB of bz2 streams cut on stream boundaries from `pages-articles-multistream1` (part 1 of the current dump, 2026-11-07), 2,100 pages, 1,602 articles after redirects and other namespaces; wikitext reduced to prose by a regular-expression pass | 91.0 MB XML, 86.5 MB wikitext | 36.1 MB |
| Stack Exchange | the public API, `physics`, 800 newest questions and 800 newest answers with bodies, HTML stripped | 3.9 MB JSON | 2.3 MB |
| OpenAlex | the public API, 2,000 works of 2024 with abstracts, the abstract rebuilt from its inverted index, title prepended | 16.6 MB JSON | 3.2 MB |
| arXiv | OAI-PMH on `export.arxiv.org`, set `cs`, records dated 2026-10-01 to 02, one page of 1,300 | 4.2 MB XML | 2.0 MB |
| Hacker News | the Algolia search API, 3,000 newest comments and 1,000 newest stories; 2,000 items had text | 2.4 MB JSON | 0.5 MB |
| Project Gutenberg | 20 plain-text books, headers and footers removed, lines unwrapped into paragraphs; the catalogue CSV for counts | 19.4 MB | 18.6 MB |

## Results

### Compression and chunks

| source | items | mean item bytes | zstd -3 | zstd -9 | zstd -19 | gzip -6 | chunks | mean chunk chars | chunks per MB of text |
|---|---|---|---|---|---|---|---|---|---|
| Wikipedia (prose) | 1,602 | 22,531 | 2.77 | 3.12 | 3.59 | 2.72 | 43,925 | 964 | 1,217 |
| Wikipedia (wikitext, as in the dump) | 1,602 | 54,014 | 3.01 | | 3.93 | | | | |
| Stack Exchange | 1,600 | 1,442 | 2.95 | 3.29 | 3.64 | 2.84 | 3,030 | 830 | 1,313 |
| OpenAlex | 2,000 | 1,588 | 3.08 | 3.50 | 3.94 | 2.87 | 5,011 | 704 | 1,578 |
| arXiv | 1,300 | 1,514 | 2.93 | 3.23 | 3.58 | 2.79 | 3,400 | 649 | 1,728 |
| Hacker News (one item per comment) | 2,000 | 251 | 2.65 | 2.84 | 3.00 | 2.53 | 2,110 | 240 | 4,212 |
| Project Gutenberg | 20 | 932,137 | 2.83 | 3.15 | 3.67 | 2.73 | 21,045 | 1,018 | 1,129 |

Ratios are uncompressed over compressed. Prose compresses 2.7 to 3.1 times at `zstd -3` and 3.6 to
3.9 times at `-19`; the level buys a quarter more at about ten times the compressor's time. The
chunker yields 1,100 to 1,700 chunks per MB on long-form and abstract-length items, because a short
item is one chunk however short, and 4,200 per MB on comments taken one at a time; a thread taken
as one item, each comment a block, falls into the long-form rate.

Other counts from the samples: a Wikipedia article in the slice links to 205 distinct pages on
average (median 133); an OpenAlex work of 2024 with an abstract references 135 works on average
(median 70), 93% reference at least one.

### Embedding throughput

3,000 chunks, mean 973 characters, 240 tokens each by the server's count. Idle probe latency
23 ms (median of five).

| batch | concurrent requests | chunks/s | tokens/s | batch latency p50 | probe beside it |
|---|---|---|---|---|---|
| 8 | 1 | 21.4 | 5,298 | 0.34 s | 0.60 s |
| 32 | 1 | 23.4 | 5,940 | 1.20 s | 1.23 s |
| 64 | 1 | 26.1 | 6,245 | 2.38 s | 1.84 s |
| 32 | 2 | 28.9 | 6,753 | 2.15 s | 1.65 s |
| 32 | 4 | 30.4 | 6,795 | 3.99 s | 4.32 s |
| 64 | 4 | 29.0 | 6,750 | 8.06 s | 8.45 s |

Throughput saturates near 30 chunks/s (about 6,800 tokens/s); batch 64 on one stream gives 26 and
every further stream buys at most 15% while another caller's latency grows from 23 ms to the
length of the queue in front of it (1.8 s beside one batch of 64, 4.3 s beside four streams of 32).
The embedder bench of 2026-10-28 measured 24.3 documents/s on documents cut at 2,000 characters;
these are consistent.

### Rates of the live sources, and the daemon

- Wikimedia EventStreams `recentchange`, 30 seconds: 1,137 events over every wiki, 96 English
  Wikipedia edits (3.2 a second, about 280,000 a day).
- Hacker News, from the sample's timestamps: 9,300 comments and 850 stories a day; `maxitem`
  50,408,507.
- physics.stackexchange.com, from the sample: 6.7 questions and 15 answers a day.
- arXiv `cs`: 1,300 records dated across two days.
- The daemon's queue, read-only: 27,398 `vault_sync` jobs done between 2026-11-06 07:51 and
  2026-11-07 21:58, 720 an hour, 12 a minute, 0.07 s each. The job rate is the tick's, not a
  ceiling of the writer; a job that carries one item would need 580 days for 10^7 items, one that
  carries 2,000 needs 25 hours.

### The live stores' bytes per row (read-only)

| store | rows | bytes per row |
|---|---|---|
| the curated Lance table (`research_curated.lance/chunks.lance`) | 147,417 | 2,215, of which the float16 vector 1,536 and the text column with ids 679 |
| its plane (`plane.sqlite`, occupancies with three indexes) | 148,240 | 1,084 |
| `memberships.sqlite` (memberships and atoms) | 34,764 | 385 |
| `reference_edges.sqlite` (five indexes) | 3,029,562 | 567 |
| `attestations.sqlite` | 1,981 | 1,060 |

## Caveats

- The Wikipedia slice is from part 1 of the dump, the oldest page ids, which are long articles; its
  mean item size overstates the encyclopedia's, its chunk rate per MB does not depend on it.
- The wikitext reduction is a regular-expression pass, not a parser; 5 to 10% of the prose bytes
  are markup residue, which compresses better than prose, so the prose ratio is slightly high.
- One sample per source, one run per embedder configuration; the throughput figures carry the
  machine's ordinary variance (a few percent) and the design uses them to one significant figure.
- The Gutenberg sample is twenty well-known books, longer than the collection's median.

## Reproduce

The fetch scripts and the measurement harness lived in the session's scratch directory and are not
committed; the method above is complete. The numbers are in
`docs/experiments/corpus-measurements-2026-11-07.json`.
