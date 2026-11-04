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

## Resolutions

None recorded yet. A resolution is added when the compiler refuses a sentence as ambiguous and the
owner picks a reading; it is recorded here as `phrase → reading`, with the date and the re-entry
condition, and the elaborator applies it from then on.
