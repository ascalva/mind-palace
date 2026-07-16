# Journal — bp-044 `harness-report`: the report generator + cost ledger (E4)

> The fresh-agent contract: a new session with only `plan.md` + this journal + the write-scope files
> must continue without re-asking. Checkpoint at every semantic boundary. Status flips are the
> orchestrator's, by hand.

## 2026-07-15 — GRADUATED (proposed), awaiting owner `proposed→ready` blessing

- Graduated by the orchestrator (opus, self-driven) from ratified `dn-evaluation-harness` §3 **E4**.
  Milestone-1 tranche member (renders the first A/B run).
- **Grounding done in-session** (direct reads, no subagents). Key facts:
  - `eval/harness/report.py`, `scripts/report.py`, `data/reports/` all ABSENT → greenfield renderer +
    a new report root. The ONE existing-code touch is `core/stores/telemetry.py` (the cost ledger).
  - Telemetry migration pattern grounded (`telemetry.py:22` `SCHEMA_VERSION = 2`; ordered `_DDL` list
    of `CREATE TABLE IF NOT EXISTS` + a `schema_migrations` version row; the `context_usage` table was
    the v1→v2 precedent). The cost ledger follows exactly: append one `harness_cost` table, bump to 3 —
    additive, every existing telemetry read/write stays green (the bit-identical-telemetry falsifier).
  - Attestation refs are OPAQUE provenance pointers read via `AttestationReader` Protocol
    (`core/ops_view.py:47`, `.all()`); the report *displays* the ref, does NOT verify chains (that's the
    E8 attestation battery). E1's `Reading.evidence_ref` + E2's `run_id` carry the refs.
  - No sparkline prior art (`grep` = 0) → a new pure `eval/harness/sparkline.py` (Unicode-block, no deps).
  - The load-bearing invariants: every figure carries its `(spec_hash, corpus_ref, config_fingerprint,
    seed)` key (no unprovenanced number); `report.md` + `report.json` are ONE model, two renderings (a
    golden-file test pins both, so they can't drift); the renderer is model-free + deterministic; "no
    silent caps" — dropped/truncated coverage is recorded, never hidden.
- **Scope decisions:** three items — (8) pure sparkline; (9) the report model + markdown/JSON renderers
  (read-only over E1/E2/telemetry); (10) the additive `harness_cost` table + cost appendix. Item
  numbering continues the family (Items 8–10).
- **Cost estimate:** opus 200k (deterministic templating + one additive telemetry table + golden-file
  tests). Self-driven ~0.5–0.8×. No fable, no xhigh.
- **Not started** — `proposed`. `depends_on: [bp-042, bp-043]` (reads their store surfaces; must build
  AFTER both land). Owner blesses `proposed→ready`, then `/build bp-044` (or delegate — budget gate first).
