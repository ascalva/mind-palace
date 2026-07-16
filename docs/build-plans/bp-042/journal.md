# Journal — bp-042 `eval-results-store`: the eval-results store + metric registry (E1, keystone)

> The fresh-agent contract: a new session with only `plan.md` + this journal + the write-scope files
> must continue without re-asking. Checkpoint at every semantic boundary. Status flips are the
> orchestrator's, by hand.

## 2026-07-15 — GRADUATED (proposed), awaiting owner `proposed→ready` blessing

- Graduated by the orchestrator (opus, self-driven) from ratified `dn-evaluation-harness` §3 **E1**
  — the keystone of the milestone-1 tranche (E1 → {E2, E4} + E5(A2), the first overnight dual-dreamer
  A/B). Implements NO new design (the note is banked, ratified 2026-07-15); this plan *builds* the
  eval-results store + metric registry the note specifies.
- **Grounding done in-session** (direct reads, no subagents — context economy + the /usage note's
  subagent-heavy flag). Key facts:
  - `eval/harness/` is absent (verified `ls`) → greenfield; §3/§4/§8 marked N/A with judgment
    (§4 carries the one existing-code touch: `eval/metrics.py` absorbed *by re-export*, additive).
  - The §2.1 key `(spec_hash, corpus_ref, config_fingerprint, seed)` + the §2.2 row shape are pinned
    verbatim in §6; the store is DuckDB (A-4), append-only-**by-key** (the discipline is in code —
    DuckDB will happily dup, so `put()` must skip a present cell; that is the whole-plan falsifier).
  - Telemetry store (`core/stores/telemetry.py`) is the house DuckDB precedent (writer/reader split,
    `open_store(config)`), NOT a dependency — the eval store mirrors its shape only.
  - Four built metric families to register: golden recall (`eval/metrics.py` — the 3 pure fns),
    drift `D` (`eval/drift.py`), F9 components (`tests/quality` `THRESH`: signal_recall/noise_max_conf/
    noise_max_mean), telemetry vitals (`core/stores/telemetry.py`). Registry declares the §2.5 fields.
- **Scope decisions (graduation judgment):** four items, blast-radius ordered — (1) store + types +
  append-only-by-key; (2) resumability/honest-comparison tests; (3) registry + `eval/metrics.py`
  absorption (the ONLY existing-code touch, additive); (4) the eval-isolation integrity tooth
  (non-skippable, proves ∉ MIRROR_READABLE + no ingest path). One session, not parallel.
- **Cost estimate:** opus 200k (new DuckDB store + typed registry + tests; smaller than bp-039's
  240k est — one table, no lattice). Self-driven ~0.5–0.8×. No fable, no xhigh (deterministic).
- **Not started** — `proposed`. Owner blesses `proposed→ready` by hand, then `/build bp-042`. This is
  the keystone: E2/E3/E4/E5 all read or write its surface, so it builds FIRST. Safe (a new store,
  touches no live data; tests use tmp/`:memory:`), so it can build even at week 95%.
