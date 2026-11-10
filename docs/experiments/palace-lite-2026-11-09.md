# The lite palace: a code instance with no embedder (2026-11-09)

Measurements for `docs/design-notes/dn-palace-lite.md`. Aggregates only; the raw record is
`palace-lite-2026-11-09.json`.

## Setup

- Machine: Apple M2 Pro, 32 GB, macOS; Python 3.15; ripgrep 15.2.0.
- Source: this repository, through a local clone, so that one commit could be replayed. The full
  ingestion ran at `a91ec39e` (2,015 files after exclusions), the incremental after advancing the
  clone's `main` by one real commit, `6b8d472b` (five files changed, one added), then to `2b500e5e`
  (three more commits, six files). The lookups ran at `2b500e5e`, the commit the answers were read
  at.
- Instance: `config/instances/code.toml`'s settings with the root and the repository path moved
  into a scratch directory; no embedder, no plane, no model. Each sync is the CLI's
  `uv run scripts/palace.py repo-sync` under `/usr/bin/time -l`, so the wall time includes uv's
  environment check and the interpreter's start.
- Load: every timed run waited for a window with no process above 30% CPU but the window server
  and a one-minute load under 3.5; the one-minute load during the runs was 1.8 to 2.2. Two other
  agents' formal checks and test suites ran before and after the window, never during it.
- The lookups' sentences and ripgrep patterns were fixed before the first run and not tuned
  after it (`eval/palace_lite.py`).

## Ingestion

| run | effects | wall s | peak RSS MB | writer stages s (admit, derive, index, finish) |
|---|---|---|---|---|
| full, `a91ec39e` | 2,015 landed | 10.94 | 271.0 | 0.27, 0.99, 7.35, 0.69 |
| again, no commit | 2,015 unchanged | 2.53 | 215.4 | 0.47, 0, 0, 0 |
| one commit, `6b8d472b` | 6 landed, 2,010 unchanged | 2.61 | 217.0 | 0.49, 0.005, 0.08, 0.005 |
| three commits, `2b500e5e` | 6 landed, 2,015 unchanged | 2.58 | 219.8 | 0.47, 0.003, 0.06, 0.005 |
| the real instance, `2b500e5e` | 2,021 landed | 10.86 | 271.0 | 0.26, 0.96, 7.46, 0.61 |

At `2b500e5e` the instance holds 2,021 active items, 27,235 lexical units (27,059 current),
2,496,241 postings over 46,239 terms. Its stores take 112.1 MB of file bytes: the lexical index
86.6 MB, the raw store 22.4 MB, the attestations 1.6 MB, the catalog 0.9 MB, the versions 0.55 MB,
the rest under 0.1 MB each; no vector store exists. The real instance's root measures 126 MB with
`du`, which counts allocated blocks.

The lexical stage is two thirds of a full ingestion: one transaction of 27,000 units and 2.5
million postings. A sync that lands nothing still reads every blob of the tree and checks every
file's key and units: 0.47 s in the writer, the rest of its 2.5 s the interpreter's start, the
evaluation of the script and git.

## Lookups against ripgrep

The palace is asked `top 5 near "<text>" over reference` in one process over the instance's
stores (cold: the first time; warm: the median of five more). Ripgrep is asked the pattern an agent
would type, `rg -l --sort path <pattern>`, over the clone's checkout, the median of five. A hit for
the palace is a correct file in its top five; for ripgrep, a correct file among those it prints,
which are what an agent must then open.

| lookup | palace rank | palace warm ms | palace cold ms | rg files | rg holds it | rg ms |
|---|---|---|---|---|---|---|
| where is `embed_fitting` defined | 2 | 157 | 707 | 1 | yes | 50 |
| where does the writer's UNCHANGED check live | 2 | 159 | 161 | 18 | yes | 50 |
| which note describes landing without vectors | 1 | 322 | 331 | 1 | yes | 8 |
| which laws govern the embed drain | miss | 282 | 292 | 14 | yes | 53 |
| which files import `core.ingest.writer` | 2 | 272 | 275 | 8 | yes | 52 |
| which code computes the spectral gap | miss | 105 | 110 | 6 | yes | 30 |
| where is the BM25 term weight computed | 2 | 147 | 155 | 14 | yes | 52 |
| where is the instance root resolved | 2 | 198 | 224 | 7 | yes | 54 |
| which Lean file proves the script firewall | 3 | 163 | 168 | 3 | yes | 9 |
| where is the supervisor lock taken | miss | 149 | 157 | 14 | yes | 50 |
| which constant reciprocal rank fusion uses | 4 | 193 | 198 | 12 | yes | 53 |
| the commit history of `core/ingest/writer.py` | 1 version | 9 | | 9 commits (`git log`) | | 24 |

The palace ranks a correct file in its top five for 8 of the 11 lookups; ripgrep's output holds one
for all 11 and prints a median of 8 files. Median warm latency: the palace 163 ms, ripgrep 50 ms.
The first query of the process took 707 ms (the stores opened); the others were within a few
milliseconds of their warm times.

What outranks the answer is the text that talks about it most. Where a correct file came
second, the first was a test in three of five lookups (a test names the identifiers it exercises
more often than the module that defines them), the design note in one, and in the import lookup the
imported module itself. The misses are of the same kind: for the drain's laws the design note and
the Lean files outrank `docs/LAWS.md`; for the supervisor lock its tests and plans outrank
`ops/lifecycle/lock.py`; for the spectral gap a test, `docs/LAWS.md` and two papers outrank the
module that computes it. That last answer was declared before the run as `core/graph/influence.py`
alone; the palace's fifth hit, `formal/Palace/Gap.lean`, is the Lean proof of the spectral-gap
lemma, which a broader reading of "code about the spectral gap" would count (9 of 11). Ripgrep
never misses a pattern it is given, but an agent must know the pattern and open what it prints:
one file when the pattern is an exact definition, 14 to 18 when it is a phrase.

The file's history is a limit of the instance, not of the lookup: `trace` shows the versions the
instance has landed, one per sync that changed the file, and this instance began at `a91ec39e`.

## The MCP server

Spawned five times as an MCP client spawns it (`uv run --project <checkout> python
scripts/palace_mcp.py` with the instance's overlay), timed from the spawn: `initialize` answered at
0.71 s, the first `query` at 1.30 s, a second at 1.48 s (medians). Peak resident memory of the
server's process tree: 168 MB. The server never opened a vector store, an embedder or a model
client (the integration tests make constructing any of them fail).
