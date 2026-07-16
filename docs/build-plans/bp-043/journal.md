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

## 2026-07-16 — BUILD START (delegated builder, opus, self-driven)

- **Worktree bootstrap:** the worktree branch was cut from a stale base (103b3eb) predating the plan
  + prerequisites. It was a clean ancestor of `main` (0 divergent commits) → `git merge --ff-only main`
  brought in the plan, bp-042 (`eval/harness/{store,registry}.py`) and bp-045 (SnapshotStore wiring).
  Active-plan pointer set to `bp-043`.
- **Read whole:** plan.md, the two dream pipelines (`dreamer.py` dream/:126 dream_v2/:168), interpreters
  (`Claim`/:67, `collect_claims`/:328, `community_interpreter`/:83, method names/:56-64), adjudicator
  (`adjudicate`/:92 — `support_of=None` default = flat `grounding_score`, identical to noisy-OR when all
  refs are authored leaves), `eval/harness/store.py` (`EvalKey`/`Reading`/`open_eval_store`, put is
  append-only-by-key, skip-on-present), `eval/harness/registry.py` (`golden_recall`+`drift_D` ARE
  registered; `structural_axes.*` are NOT), `eval/golden.py` (`evaluate(golden, retriever)`→`GoldenReport`,
  fixture corpus not the vault), `eval/drift.py` (`drift_from_report(..., structural=)`), `temporal.py`
  (`compute_snapshot`, `SnapshotStore.latest_structural()`→`{frustration,min_conductance}`), `cron.py`
  (`DREAM_KIND`, `enqueue_dream`/:61), `router.py` (`_SYNTHESIS_KINDS`, `plan`), `supervisor.py`
  (`HEAVY_TIERS={"synthesis","stretch"}` — keyed on TIER), `queue.enqueue(kind, tier, num_ctx, *, priority)`.

- **KEY DESIGN RECONCILIATIONS (settled in-build, faithful to the pins):**
  1. **Model-free forces direct pipeline steps, not `Dreamer.dream_v2`.** `Dreamer.dream_v2` calls
     `self.synthesize` (step 8) → a MODEL call, which violates Item 6's model-free invariant. So the
     runner runs the pipeline *steps directly*: phase7 = `community_interpreter(graph, rnd)`; dream_v2 =
     `collect_claims(graph, ctx, rnd)` + `adjudicate(...)` (no `support_of` → flat grounding, no derived
     read). This also satisfies Q4 ("run the interpreters/adjudicator directly, persist nothing but
     ledger rows"). Q6's "its own Dreamer" phrasing is reconciled to: the runner computes step-10
     (`compute_snapshot`) itself into an EPHEMERAL scratch `SnapshotStore` (NOT the live structural.duckdb
     — no live pollution), then reads `latest_structural()` from that scratch store. bp-045 IS landed but
     the runner no longer depends on `build_dreamer.snapshots` at all; the not-captured fallback fires
     only if `latest_structural()` is None (honest, §2.8).
  2. **eval keys per run:** `EvalKey(spec_hash=sha256("shadow-runner/v1‖<pipeline>"), corpus_ref=corpus_digest,
     config_fingerprint=fp, seed=0)`. spec_hash carries the pipeline (§2.1) so phase7 vs dream_v2 get
     DISTINCT keys → both guardrail readings land. corpus_digest + config_fingerprint are SHARED across
     the two runs (one snapshot, one [dreaming]-lever set). Guardrails (`drift_D`,`golden_recall`) are
     corpus properties (same value both pipelines); `structural_axes.*` are dream_v2-only.
  3. **corpus_digest** = deterministic Merkle fold over `sorted(set(row['digest']))` of the MirrorView
     rows (the mirror rows carry `digest` — vectorstore schema confirms; NO §10 stop). **config_fingerprint**
     = sha256 of canonical-JSON of the 4 `[dreaming]` levers (E3 widens later — parked).
  4. **guardrail retriever is INJECTED** (golden fixture corpus, not the vault → firewall intact). When
     absent → guardrails logged not-captured (§2.8), never fabricated. Golden/baseline/drift_cfg auto-load
     from the frozen files when a retriever is present but they are not injected.
  5. **enqueue_shadow routes via the DREAM plan's tier** (`router.plan(DREAM_KIND)` → synthesis tier +
     background priority) but enqueues under `SHADOW_KIND="shadow"`, so it is foreground-gated exactly like
     dream (HEAVY_TIERS is keyed on TIER) WITHOUT editing router.py (out of write_scope). `cron_handlers`
     (the live map) is left UNTOUCHED; `shadow_handler` is added standalone beside it.
- **Polarity (Q3):** map lives in runledger as string literals (avoid core/stores→core/dreaming coupling):
  `tension→"-"`, `community/theme/hole/thread→"+"`, else `"+"` FLAGGED. `collect_claims` also yields
  `centrality/bridge/density` (unmapped) → default `"+"`, flagged once per run (sensible default exists →
  NOT a §10 stop). Annotated as spec-fidelity.
- **OPEN spec-fidelity (to annotate, not block):** `structural_axes.*` are written per the §3 Q6/§6 pin but
  are NOT registered in `eval/harness/registry.py` (out of write_scope; a follow-up should register them).
  put() does not gate on registration so no runtime break.

### Item 5 — DONE: `core/stores/runledger.py` + `tests/unit/test_runledger.py`

- SQLite/WAL, `dream_runs`+`dream_claims` (columns verbatim §6), `claim_id`/`polarity_for`/
  `polarity_and_flag` module-level, `add_claim` computes novel across ALL prior runs (INDEX on
  claim_id), `open_run_ledger(config)` → `<derived_store_dir>/run_ledger.sqlite`. Reads via
  `sqlite3.Row`→dict. Ledger decoupled from core/dreaming (polarity keys are string literals).
- **Acceptance MET** + falsifier actively guarded: `test_claim_id_excludes_surface_and_confidence`
  (order+dup-insensitive, surface invisible), `test_novel_is_false_on_reemit_despite_different_surface`,
  `test_novel_spans_all_prior_runs_not_just_this_run`, `test_append_only_reemit_is_a_new_row`.
  7/7 green; `mypy core/stores/runledger.py` clean.

### Item 6 — DONE: `core/dreaming/shadow.py` + `tests/unit/test_shadow_runner.py`

- `ShadowRunner.run(config)` → `(phase7_run_id, dream_v2_run_id)`. phase7 = `community_interpreter`;
  dream_v2 = `collect_claims`+`adjudicate` (no support_of, no derived read) + step-10
  `compute_snapshot`→scratch in-memory `SnapshotStore`→`latest_structural()`. `corpus_digest` =
  deterministic Merkle fold over `sorted(set(digest))`; `config_fingerprint` = sha256 of the 4
  `[dreaming]` levers. Eval keys per run: `spec_hash=sha256("shadow-runner/v1‖<pipeline>")`,
  shared corpus_digest/config_fingerprint. Guardrails (`drift_D`,`golden_recall`, by registered name)
  written for both pipelines; `structural_axes.*` for dream_v2 only. Injectable seams; not-captured
  fallbacks for retriever/A2 (no silent cap). Never imports `core.stores.derived`; reads only via
  `MirrorView.project`; enables dream_v2 via `replace(cfg.dream_rnd, enabled=True)` (never disk).
- **Acceptance MET:** two `dream_runs`, ONE corpus_digest, claims per pipeline, guardrail+axes
  Readings keyed to the run, live derived store row-count unchanged, disk flag still False, second
  run → re-emits novel=False + eval cells skipped. 5/5 green (~26s: real complex+duckdb). ruff+mypy
  clean.
- **Verified NOT tripping falsifiers:** single corpus_digest for both runs; every Reading key ==
  run's corpus_digest/config_fingerprint; no synthesizer wired (model never called); derived store
  untouched.

### Item 7 — DONE: `scheduler/cron.py` + `tests/integrity/test_shadow_isolation.py`

- Added `SHADOW_KIND="shadow"`, `shadow_handler(runner)`, `enqueue_shadow(queue, router)` BESIDE the
  untouched `enqueue_dream`/`dream_handler` (one-line cross-ref comment to `core/dreaming/shadow.py`).
  `cron_handlers` (the live map) left untouched. `enqueue_shadow` routes via `router.plan(DREAM_KIND)`
  (synthesis tier + background priority) and enqueues under `SHADOW_KIND` — foreground-gated identical
  to dream (HEAVY_TIERS keyed on tier) WITHOUT editing router.py (out of scope).
- Integrity tooth (AST, non-skippable): (1) shadow.py never imports `core.stores.derived` (no write
  path by construction); (2) reads corpus only via `MirrorView.project` — no raw `.all_rows(`/`.search(`;
  + two negative controls (dreamer.py DOES import derived; mirror.py DOES call all_rows) so the scanner
  has teeth; (3) `enqueue_shadow` lands at BACKGROUND priority on synthesis tier == dream. 5/5 green.

## 2026-07-16 — GREEN GATE (all 5 legs, run separately) + COMPLETE

- **leg 1 ruff** `ruff check .` → `All checks passed!`
- **leg 2 mypy targeted** `mypy core agents eval ops scheduler scripts` → `Success: no issues found in
  192 source files` (0 errors; 190→192 = +runledger.py +shadow.py).
- **leg 3 argless mypy** `mypy` → `Found 69 errors in 20 files (checked 393 source files)` — EQUALS the
  pinned tests/-baseline of 69 (no new argless errors introduced).
- **leg 4** `python -m ops.type_gate` → Tier-2 membership OK; bare-ignore scan OK.
- **leg 5 pytest** `pytest -q -m 'not live'` → `1199 passed, 10 skipped, 9 deselected in 38.89s`.

- **Findings filed:** finding-0086 (`spec-fidelity`, builder-resolved) — `structural_axes.*` referenced
  per §3 Q6/§6 but not registered in `eval/harness/registry.py` (out of write_scope). Resolved:
  written as pinned (put() does not gate on registration); a follow-up should register the family.
- **Parked decisions (unchanged from §11):** σ-sweep deferred to E3; config_fingerprint = [dreaming]
  subset; per-claim polarity derived from method; no scratch derived-store persistence.
- **No §10 stops hit.** Mirror rows carry a stable `digest` (Q2 confirmed) → Merkle corpus_digest fine.
  Polarity default `+` exists for unmapped kinds → no spec-defect stop (flagged, not blocked).
- **Status:** all three items (5,6,7) built + accepted + green. Ready for orchestrator review/merge.
  Do NOT flip plan status here (orchestrator owns it).
