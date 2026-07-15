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
