# Journal — bp-043 `run-ledger-shadow`: the run ledger + shadow runner (E2, carried from Track L L1)

> The fresh-agent contract: a new session with only `plan.md` + this journal + the write-scope files
> must continue without re-asking. Checkpoint at every semantic boundary. Status flips are the
> orchestrator's, by hand.

## 2026-07-15 — GRADUATED (proposed), awaiting owner `proposed→ready` blessing

- Graduated by the orchestrator (opus, self-driven) from ratified `dn-evaluation-harness` §3 **E2**;
  the L1 stage shapes are carried verbatim from the superseded `live-adoption-and-longitudinal-harness.md`
  §2 (the protocol annex of record). Milestone-1 tranche member (needed by the first A/B run).
- **Grounding done in-session** (direct reads, no subagents). Key facts:
  - `core/stores/runledger.py` + `ShadowRunner` are ABSENT (verified) → greenfield store + runner;
    but the plan reads the two dream pipelines + adds a cron job, so it carries a REAL §3 grounding pass.
  - The `dream_runs`/`dream_claims` column lists are pinned VERBATIM from the annex §2 (§6 of the plan).
    `claim_id = sha256(kind ‖ canonical(support) ‖ polarity)` EXCLUDES surface wording + confidence.
  - The `Claim` type (`interpreters.py:67`) is `method/statement/support/data` — **no confidence, no
    polarity field**. So (Q3) `kind`=method, `support_set`=`sorted(set(support))`, and **polarity is
    NOT in the code** → the plan settles it: a method→polarity map (TENSION→"−", THEME/HOLE/THREAD/
    COMMUNITY→"+"), documented; unmapped defaults "+" and is flagged.
  - `config_fingerprint`/`corpus_digest` don't exist yet (grep = 0 hits) → the plan settles them:
    corpus_digest = Merkle over the mirror rows' `digest`s; config_fingerprint = sha256 of the resolved
    `[dreaming]` levers (E3 later widens to the full tuning manifest). Flagged as a STOP if mirror rows
    carry no stable digest.
  - Off-loop safety grounded via the bp-040 journal: dream_v2 enabled IN-PROCESS (`replace(cfg.dream_rnd,
    enabled=True)`), NEVER the disk flag; shadow reads the live mirror READ-ONLY, writes ONLY the ledger,
    never the interpreted/derived store. That is the whole-plan falsifier (live surface unchanged).
- **KEY GRADUATION DECISION — the soft §3-vs-§2.9 seam, resolved (§1 reconciliation + Q6).** The note
  says the first A/B needs `E1+E2+E5(A2)+E4` (§3, no E3a) but calls it "the first *sweep* instance"
  (§2.9 → §2.6 = E3a). Reconciled: the milestone A/B is the **single-config** dual-pipeline comparison
  (one snapshot, phase7 vs dream_v2, guardrails + dream_v2 structural axes); the σ-**grid** version is
  E3a's declarative sweep, deferred. **So the ShadowRunner is the harness's run PRODUCER** — it writes
  claims → the ledger AND the registered metric readings (guardrails drift D/golden recall + dream_v2
  `structural_axes.*`) → the **E1 eval store** ("everything writes through it", §2.2). That makes
  **bp-043 depend on bp-042** (imports `eval.harness.{store,registry}`). A2 keying (Q6): `StructuralSnapshot`
  has NO config/run key, so the runner reads `SnapshotStore.latest_structural()` and writes keyed
  `Reading`s into the eval store — NO `structural.duckdb` schema change; attribution lives in the §2.1 key.
- **Scope decisions:** three items — (5) ledger store + claim_id + novel-on-insert; (6) ShadowRunner
  (both pipelines, one snapshot; ledger + eval-store metric writes; row-count-before/after dry check on
  the live derived store); (7) the shadow trough job (additive to `scheduler/cron.py`, `enqueue_dream`
  untouched) + the isolation integrity tooth. Items 5–7 (after bp-042's 1–4).
- **Cost estimate:** opus 260k (raised from 220k for the metric-evaluation-into-eval-store surface).
  Self-driven ~0.5–0.8×. No fable, no xhigh.
- **Runtime cross-dep on E5(A2):** if bp-045 hasn't landed, dream_v2 writes no snapshot, so the runner
  records claims + guardrails and logs `structural_axes.*` as **not-captured** (no silent cap, §2.8),
  never failing. Build order for the milestone: bp-042 → bp-043 (+ bp-045 for non-empty A2) → bp-044.
- **Not started** — `proposed`. `parallelizable_with: [bp-044]`; `depends_on: [bp-042]`. Owner blesses
  `proposed→ready`, then `/build bp-043` (or delegate — pre-flight budget gate first). Safe: new store +
  read-only live-mirror access + additive cron; the RUN is trough/background.
