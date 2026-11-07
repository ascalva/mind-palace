# The resolution ledger — precedents of the query sentence algebra

The defaults a sentence inherits when it leaves a dial unsaid, and the ambiguities the owner has
resolved, each with a default and a re-entry condition (dn-query-sentence-algebra §2.7: a
precedent in the second sense). `core/sentence/precedents.py` is this file's executable mirror;
the two change together, and a sentence re-run under a changed precedent is a measured
answer-drift, never a silent one.

## Defaults in force

| dial | default | why | re-entry |
|---|---|---|---|
| `diffuse … beta` | `1.0` | the code's default; `e^{−d}` is positive definite there (RSP-3) | a retrieval eval set gives β a falsifier (TA-b) |
| `reach … depth` | `1` | `ReferenceView.connected_set`'s default | — |
| `walk … depth` | `4` | chains longer than four moves have not been asked for | a question needs them |
| `walk`'s most chains | `200` | a bound on the product walk's enumeration | a question needs more |
| `diffuse` with no relation | `S`, the similarity backbone | the only weighted relation at the note grain (TRA §2.1-i: the binary citation graph degenerates the curve) | citation weights become graded |
| `reach` with no relation | `F`, citations | REACH's meaning | — |
| `reach` with no direction | `both` | `connected_set` walks both ways | — |
| `trace` with no direction | `forward` (`σ_*`) | HISTORY's default | — |
| `near` with no `over` | `mirror_authored` | the owner's notes are the default universe | — |
| a field as the whole sentence | the `5` best scores are shown | SEARCH's `k` | — |
| `read` with no `chunk` | `0`, the paper's start | the retired `read` tool's default | — |
| `read`'s window | `5` chunks (~5K characters) | a whole paper won't fit a turn | a client needs more |
| the support an indexed stratum contributes | `200` units per `near` text or anchor | the dense backbone is n²; the index returns the nearest (dn-query-sentence-algebra §2.9) | a battery row loses to a larger support |
| `reach` and `walk` depth at most | `50` hops | the retired schema's cap; the surfaces answer one call at a time, so one sentence must not hold them | a question needs more |
| `top k` at most | `1000` | the retired schema capped `k` at 50; a ranking past a thousand is a dump | a question needs more |
| a path's count `{n,m}` at most | `32` | each count copies the automaton, and nested counts multiply | a question needs more |
| `walk`'s budget | `100000` partial chains | the product walk enumerates simple paths, exponential on a dense graph; the answer says when it stopped | a question needs more |

## The ingress's prices

What a request's work costs (dn-ingress-language §E10), one unit the time of one evaluation step.
Measured by `eval/ingress_gas.py` on 2026-11-05 on the owner's Mac: 300 notes, the median of seven
runs on a warm page cache, the embeds on the palace's embedder (EmbeddingGemma-2 on llama-server,
`:8081`, ten notes' chunks, one request a note, as the landing sends them). A step took 0.30 µs.
Prices are rounded to two figures. `PRICES` in `core/sentence/interpret.py` and the roles'
budgets in `core/ingest/table.py` are this table's executable mirror.

| operation | price | measured | re-entry |
|---|---|---|---|
| `step` | `1` | 0.30 µs: a statement, an expression node, a loop's turn | the unit |
| `item` | `270` | 81 µs: a note opened and parsed | a reader that parses less |
| `kib` | `75` | 23 µs: a KiB of an item's content read | — |
| `entry` | `22` | 6.6 µs: a place's entry read from the catalog | — |
| `effect` | `10000` | 3.2 ms: the effect evaluated, and the writer's check of a store, twice (the price pass and the landing; mostly the plane's lookup of a version's rows) | the plane's lookup gets cheaper |
| `write` | `140000` | 42 ms: a store that lands, its embeds apart (the raw object, the plane's append, the catalog, the attestation); charged too for a retire, a link and a run | the plane's append gets cheaper |
| `query` | `360000` | not measured: one embed, its text's, as its floor | the read verbs priced in this unit (§E10's follow-up) |
| `embed` | `360000` | 109 ms: a chunk embedded | another embedder |
| the `cli` role's budget | `50000000000` | about four hours of measured work: the owner's and the daemon's own jobs, a first sync of every doc after a plane reset (about 5,300,000,000) ten times over | a sync that needs more |
| the `ambassador` role's budget | `100000000` | about 30 seconds: a capture is under one million, a link or a job's start under two hundred thousand | a request the Ambassador needs that does not fit |
| the `inbox` role's budget | `50000000000` | the operator's: the inbox's capture is the daemon's own job and reads only the inbox's record of what the owner typed (an exchange of two short texts is under two million) | a backlog that needs more |

The two coalescing requests, `do sync_vault` and a bare `do sync_dialogue`, run as the daemon's
own jobs under the `cli` role's budget, whoever asked: their scripts are the library's, admitted
under the asker's grant when spoken.

## Resolutions

None recorded yet. A resolution is added when the compiler refuses a sentence as ambiguous and the
owner picks a reading; it is recorded here as `phrase → reading`, with the date and the re-entry
condition, and the elaborator applies it from then on.
