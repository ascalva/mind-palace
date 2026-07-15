# Journal — bp-040 `sigma-sweep`: a read-only σ-sweep harness for the dreaming threshold

> The fresh-agent contract: a new session with only `plan.md` + this journal + the write-scope files
> must continue without re-asking. Checkpoint at every semantic boundary. Status flips are the
> orchestrator's, by hand.

## 2026-07-15 — GRADUATED (proposed), awaiting owner `proposed→ready` blessing

- Graduated by the orchestrator (opus, self-driven) at the owner's direction ("tackle the σ
  re-calibration"). Warrant = **finding-0079** (a `direction` finding); implements NO new design (the σ
  knob + bound `σ∈[0.55,0.75]` + "calibrate on the owner's corpus" already exist,
  `config/defaults.toml:211`) — so no ratified note is needed; the finding is the warrant.
- **Grounding done in-session** (one Explore subagent, context economy). Key facts:
  - **σ needs NO re-embed** — it is only the clustering `threshold` (`cluster_notes(..., threshold=σ)`,
    `core/dreaming/cluster.py:89`) over FIXED centroids. So the sweep re-runs only cheap NumPy clustering
    per σ; read-only, no daemon-down, no model call.
  - **The live graph is already clean (body-only)** — finding-0077 RESOLVED by bp-036 (`strip_properties`
    wired at `core/ingest/pipeline.py:33,57`, strips ALL `key::` props) + the owner's 2026-07-14 re-embed.
    So the sweep runs on the honest content-only graph finding-0079 wants σ calibrated against.
  - **Read path to mirror exactly** (`dreamer.py:110-112`): `MirrorView.project(open_vector_store(cfg))
    .rows()` → `note_centroids` → `cluster_notes`. Corpus = 13 authored notes → sweep is sub-second.
  - **Model on** `scripts/reembed_bodyonly.py` but strip every mutation (no seal/daemon-refusal/reset/
    re-embed/re-dream) — bp-040 is READ-ONLY.
- **TRIAGE ERROR CORRECTED this session:** /triage-8 batched oq-0023 (finding-0077 "id:: vs all key::")
  WITHOUT checking bp-036 — which already resolved finding-0077 (strips ALL key::). finding-0077 flipped
  → resolved; oq-0023 closed as moot. So the σ work has NO 0077 dependency (0077 is done).
- **Scope decisions (graduation judgment):**
  1. **READ-ONLY, graph-structural sweep** — edges/clusters/near-threshold("bubble") pairs per σ. NO
     re-dream per σ (27b synthesis ~290s/cluster — impractical; the graph is the calibration signal).
     Re-dream once at the OWNER's chosen σ, separately. NO config write (σ is the owner's hand edit to
     `config/local.toml`, owner-gated). NO auto-recommended σ (a taste call on the owner's own corpus).
  2. TWO items: Item 1 pure `sweep()` + synthetic-fixture tests (monotone edges, bubble detection); Item
     2 the live read wiring + table/JSON emit. `scripts/sigma_sweep.py` + one test file.
- **Cost estimate:** opus 90k (small read-only script over built machinery; self-driven ~0.5–0.8×).
  No fable, no xhigh.
- **Not started** — `proposed`. Owner blesses `proposed→ready` by hand, then `/build bp-040`. It is
  read-only + cheap + safe even at week 93%. After build: the owner RUNS it (ideally after this deploy
  settles / daemon idle), reads the curve, sets σ, re-dreams once — none of which is this plan.

## 2026-07-15 — REVISED (still proposed): σ-sweep → off-loop full-dreamer evaluation harness

- Owner directives (2026-07-15): (1) sweep σ + bring back best candidates AND run dream sequences at
  candidate σ to see how dreams change with connectivity; (2) "no feature flag should stop the full
  dreamer"; then via AskUserQuestion: **see it off-loop first**, and **dream_v2 replaces Phase-7** when
  live.
- **Grounded dream_v2's runtime contract** (one Explore). Key facts that made the harness safe + correct:
  - `dream_v2(*, config=None) -> list[Theme]`; σ = `config.dream_rnd.sigma`. Enable IN-PROCESS via
    `dataclasses.replace(cfg, dream_rnd=replace(cfg.dream_rnd, enabled=True, sigma=σ))` — NEVER flips the
    on-disk flag. It's **end-to-end complete + tested** (`test_dream_v2_end_to_end`), all 8 lenses live
    (`change_point` an honest empty-emitter, non-blocking).
  - Runs OFF-LOOP: construct `Dreamer` directly (NOT `build_dreamer`) with `derived=DerivedStore(scratch)`,
    `snapshots=None`, `attestor=None`, `edge_store=None` → all writes land in scratch, never
    `data/derived.sqlite`. `store` is duck-typed (read-only over the live VectorStore).
  - TWO output modes: narrated dreams (dream_v2 + real local 27b synthesis, ~290s/cluster) vs model-free
    structural claims (`run_dream_rnd` → DREAM_LOG, no model). Harness does both: cheap structural sweep
    across the grid + narrated dreams at a few `--candidates`.
- **Plan revised** (alias `sigma-sweep` → `dream-calibrate`; est 90k → 150k): 3 items —
  (1) pure σ-connectivity sweep + candidate surfacing; (2) off-loop dream_v2 runner into scratch stores;
  (3) report + CLI. OFF-LOOP + SCRATCH-ONLY (owner's "see it first"); NO live-loop wiring, NO config/live-
  store write. The 27b synthesis is LOCAL compute (not Claude budget).
- **Sequel named:** `bp-041` (NOT authored) — wire dream_v2 LIVE replacing Phase-7 (flip `[dream_rnd]`,
  cron/launcher, set the owner's σ, validate). Graduate AFTER the owner sees bp-040's report.
- Still `proposed` — owner blesses `proposed→ready` → `/build bp-040`. Read-only over live data + scratch
  writes; safe. The RUN (real 27b dreams) is done daemon-idle/down (Ollama contention, finding-0069).

## 2026-07-15 — ON HOLD (still proposed): SUBSUMED by the harness design

- Owner (2026-07-15) directed a proper, consolidated evaluation/test-harness DESIGN NOTE before building
  ad-hoc harness pieces. bp-040 `dream-calibrate` (the dual-dreamer σ-sweep) is now **one component under
  that harness design** — it will be **re-derived from the ratified `dn-evaluation-harness`**, not built
  standalone. **Do NOT `/build` bp-040** until the harness note is written (Fable, post-Jul-17 reset) and
  ratified; the note may reshape bp-040's scope (shared eval-results store, report format, sweep
  orchestration). Warrant/synthesis: `docs/brainstorms/evaluation-harness.md`. Held at `proposed`.
