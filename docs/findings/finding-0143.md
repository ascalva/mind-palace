---
type: finding
id: finding-0143
status: routed
created: 2026-07-21
updated: 2026-07-26
links:
  - docs/design-notes/agentic-loop.md   # §2.8 M-3/M-6 owed rows; PD-3's precondition
  - core/integrator.py                  # CoverageGauge / coverage_gauge (M-3)
  - core/complex/topology.py            # long_lived_holes (M-6, hole lens)
  - core/mirror.py                      # MirrorView.project (M-6, hole lens input)
  - core/dreaming/cluster.py            # note_centroids (M-6, hole lens input)
  - ops/code_sensor.py                  # doc_coverage query shape (M-6)
  - eval/drift.py                       # measure_drift/Retriever (M-6, deferred leg)
ftype: discovery
origin_plan: bp-087
route: orchestrator                     # direction — records baselines dn-agentic-loop §2.8 owes
resolution: routed — re-entry narrowed to M-6c only; the §2.8 checkpoint the finding asked for is NOT executable (A8)
---

# AL-2 baselines: M-3 (C-coverage) and M-6 (gap-instrument battery), 2026-07-21, live `data/`

> **Triage 2026-07-26 (session-52) — still live, and the finding's own routing instruction is
> impossible.** `dn-agentic-loop` §2.8 still reads M-3 *"gauge built, reading not yet taken"*
> (`agentic-loop.md:488`) and M-6 *"owed"* (`:491`). The finding asserted "nothing here is ratified
> text" — but that note was **ratified in the same blessing commit `fbea48d`**, so A8 makes the table
> agent-immutable and **the requested checkpoint cannot be written at all.**
> ⇒ **finding-0143 is therefore the baseline record of record**: M-3 = 0.8996, M-6a = 0 long-lived
> holes, M-6b = 0.3391 doc_coverage.
> **Re-entry, narrowed to one item:** M-6c (drift-vs-anchor) was never run — `measure_drift` still
> exists at `eval/drift.py:210`. Run it against `eval/golden.py`'s golden set +
> `eval/golden/baseline.json` in the first session with a live retriever, then amend or succeed this
> finding with D(t). A wired inference seam (bp-115/bp-118) is the cheapest home.

## What

Bp-087 (AL-2) took the two owed readings from `dn-agentic-loop` §2.8 against the **live**
`data/` stores at `/Users/ascalva/mind-palace/data/` (main checkout, read-only — see grounding
below). All three code paths used are pinned at the plan's §6 interfaces plus their upstream
callers (traced this session); none were modified.

### M-3 — C-coverage (`core.integrator.coverage_gauge`, `core/integrator.py:82,97,117`)

```
coverage_gauge(ChatEventStore(data/chat_events.sqlite), CausalEdgeStore(data/causal_edges.sqlite)).coverage
  integrable = 4,540   (L1 events naming an endpoint: commit + write kinds)
  witnessed  = 4,084   (distinct (session_id, event_order) pairs carrying a C-edge)
  unwitnessed=   456
  coverage   = 0.8995594713656387  (~89.96%)
```
`[GROUNDED]` — ran verbatim against the live sqlite files; `witnessed` matches M-2's already-recorded
4,084 C-edges exactly (§2.8 table), which is the expected cross-check (M-2 counts the same edge
store's `all_edges()`).

### M-6 — the three gap-instrument reads

**(a) hole count/persistence** — `core.complex.topology.long_lived_holes` (`:104`), fed by
`core.mirror.MirrorView.project` over `core.stores.vectorstore.VectorStore(data/vectors.lance,
dim=2560)` and `core.dreaming.cluster.note_centroids`:

```
mirror-readable chunk rows: 28   (VectorStore.all_rows(provenances=MIRROR_READABLE))
note centroids (distinct digests): 19
  — matches the vault ingest source exactly: ~/.mind-palace/vault/janus_notes/*.md has 19 files,
    so this is the FULL current vault-authored corpus, not a truncated read.
distance matrix: 19 × 19 (cosine)
long-lived holes (min_persistence=0.15, config/defaults.toml default): 0
```
`[GROUNDED]` — a real zero: 19 authored notes is enough vertices for an H₁ feature (≥4 required),
and the run completed; it found none at the configured threshold. Distinguishable from "no data"
by the populated 19×19 matrix and the matching vault file count.

**(b) doc_coverage** — the same read `ops.code_sensor.CodeSensor.sync` performs
(`ops/code_sensor.py:329-332`), executed directly against `data/code_snapshots.sqlite` (read-only
connection, `mode=ro`) rather than through a full sensor sync (which also ingests — out of
write-scope):

```
SELECT count(*), count(*) FILTER (WHERE docstring != '') FROM symbols
  total symbols:      2,973,708
  documented symbols: 1,008,484
  doc_coverage:        0.339133499321386  (~33.91%)
  ledger_total (commits snapshotted): 883
```
`[GROUNDED]` — pure read query, identical shape to the sensor's own computation; no write handle
opened, no ingest run.

**(c) drift-vs-anchor** — `eval.drift.measure_drift` (`eval/drift.py:210`) requires a live
`Retriever` (`Callable[[str, int], Sequence[dict]]`, `eval/golden.py:32`) to answer the golden-set
queries — i.e. an active embedding pass through the Ollama model, not a store read. This is
daemon/model-adjacent infrastructure (memory-ceiling non-negotiable #8: ≤2 resident models), not
something a read-only builder session should spin up ambiently.

```
drift-vs-anchor: deferred — needs live daemon (a Retriever requires the embedding model to answer
  eval/golden.py's golden-set queries; not reachable as a pure store read)
```
This matches plan §10's second stop-and-raise condition exactly ("a coverage read that requires
the daemon running ... ⇒ record 'deferred: needs live daemon'").

## Why it matters

Closes the `dn-agentic-loop` §2.8 table's two "owed" rows (M-3, M-6) with dated, population-
qualified values (M-6c deferred, not silently skipped) — the note's own rule ("no plan graduated
from this note may skip the M-row it depends on") is satisfied for M-3 fully and M-6 two-thirds.
**PD-3's precondition ("owner wires the R&D flag + a charter entry point AND these M-6 baselines
are recorded") is now on the record** for (a) and (b); (c) needs a follow-on read once a
daemon-attached session is available (a natural fit for a future plan that already has the
retriever wired, e.g. riding the drift gate's own harness).

These are also delta anchors: the next AL pass should diff against these exact numbers rather than
re-deriving from scratch.

## Re-entry condition

M-6c (drift-vs-anchor) re-enters when a build/orchestrator session has a live retriever available
(daemon running or an in-process embedding-capable harness) — run `eval.drift.measure_drift`
against `eval/golden.py`'s golden set and `eval/golden/baseline.json`'s blessed anchor, then amend
this finding (or file a successor) with the D(t) value and its axis breakdown.

## Routing

`direction` → orchestrator. No owner decision is required to *record* these baselines (§2.8's
table is descriptive, not a design edit — A8 untouched, nothing here is ratified text); the
orchestrator should checkpoint M-3/M-6(a)/(b) into `dn-agentic-loop` §2.8's table (design-note
mechanics, out of this builder's write_scope) and note M-6c as still-owed, and update PD-3's
parked-decision row (bp-087 §11) to reflect "two of three M-6 legs recorded; drift-vs-anchor still
pending a daemon-attached read."
