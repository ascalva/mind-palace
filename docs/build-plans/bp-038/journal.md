# Journal — bp-038 `CQ-wire-2`: two-snapshot `‖[d,τ]‖` coherence + supersession health

> Fresh-agent contract: plan.md + this journal + write-scope files must let a new session continue
> without re-asking. Checkpoint at every semantic boundary. Status flips are the orchestrator's.

## 2026-07-15 — GRADUATED (proposed), awaiting owner `proposed→ready` blessing

- Graduated by the orchestrator (opus) from `dn-core-query-protocol` §2.5/§2.7 +
  `dn-temporal-retrieval-algebra` §2.2–§2.3, gated on **bp-037** (its `TemporalView` is now BUILT, so
  this extends a real interface). Grounded pass done in-session (bp-037's build reads + live probes).
- **Design settled (§3):** (Q1) σ across two snapshots → **restrict to the common node set** (measure
  citations lost between notes present at both commits; node deltas reported separately); augment-X_{n+1}
  is the recorded rejected alternative. (Q2) two store-less views compared via `coherence_to` — no store
  handle added to the frozen view. (Q3) `doc_id == source_path` (bp-031) → poset docs share X_cite's
  namespace, so `δ_D²=0` health is well-defined. (Q4) data confirmed: 435 commits carry corpus→corpus.
- **3 items:** (1) `_restrict` + `coherence_to` + `CoherenceReport` (‖[d,τ]‖, severed, is_flat, node
  deltas); (2) `supersession_wellfounded` (poset δ_D²=0 over VersionStore); (3) live cross-check of both
  (Result-2 inversion `‖[d,τ]‖ == len(severed)` + live poset health). write_scope: `core/temporal_view.py`
  + the two temporal test files. Est **220k opus**.
- **Not started** — proposed. Owner blesses `proposed→ready` by hand, then `/build bp-038`
  (opus, self-driven; no fable).

## 2026-07-15 — AMENDED (owner design dialogue): snapshot semantics + generalization on record

- Owner asked "we're comparing snapshots, not commits, right?" + "don't lock out generalization." Both
  reconciled into the plan (still proposed, so editable):
  - **§3 Q4 rewritten + Q6 added.** A commit is a time-LABEL for a FULL re-projected citation graph; the
    doc-citation stratum moves slower than commits tick. **Live probe: the 6 most-recent commits are ONE
    identical 217-pair snapshot** — so "HEAD vs git-parent" would compare identical snapshots (‖[d,τ]‖=0
    trivially). CORRECTED: Item 3 selects the two most-recent **DISTINCT** snapshots.
  - **§11 generalization affordances on record:** `coherence_to` is anchor/stratum-agnostic; per-stratum
    (via a future `direction` kwarg on `build_citation_complex`), longitudinal `φ_coh` over distinct
    snapshots, corpus-time-vs-git-time dedup, and the augment-σ alternative all layer on the same API —
    corpus-only/git-anchored/combinatorial v1 is the FIRST instance, never a ceiling.
- Still proposed; owner satisfied ("as long as we can generalize, I am good"). Awaits `proposed→ready`.

## 2026-07-15 — BUILD complete; all 3 items green; gate legs 1–4 green; finding-0082 filed

- **Item 1 CLOSED** — `_restrict` + `coherence_to(other)` + `CoherenceReport` in `core/temporal_view.py`.
  σ = identity on the common node set (restrict-to-common, §3 Q1); wires `sigma_node_map` +
  `severed_citations`/`curvature_norm`/`is_flat`. 4 unit tests: severed (norm=1), flat-on-addition,
  the **dropped-node-is-not-severed falsifier** (the augment-semantics guard), `_restrict` correctness.
- **Item 2 CLOSED** — `supersession_wellfounded(doc_ids, version_store=…)` + `open_supersession_wellfounded`.
  **DEVIATION from §6:** `doc_ids` is REQUIRED (not `None→all`) — `VersionStore` has no doc_id
  enumerator (**finding-0082** filed, `codebase`/builder-resolved); the factory scopes to the anchor's
  corpus nodes. Added an optional `version_store` DI seam (a cycle can't be built via the append-only
  store API, so cycle-propagation stays boundary-layer-tested). 1 unit test (clean chain → True).
- **Item 3 CLOSED** — live two-snapshot coherence: selects the two most-recent **DISTINCT** snapshots,
  cross-checks `report.severed` against independent set arithmetic (non-circular). **LIVE RESULT**
  (`3797f8b → 177b7fd`): common 110, ‖[d,τ]‖ **0**, flat, +1 node — the honest "only additions" case;
  supersession health True. 10 unit + 2 live = **12 passed**.
- **Gate legs 1–4 GREEN:** ruff clean (a big E501 batch reflowed — docstrings/comments only); mypy typed
  0 (186 files); argless mypy **69** (held — fixed the 3 new set-type-arg errors rather than
  re-baselining); type_gate OK. **Leg 5 (full pytest) running.**
- **Separately (owner ask): the `pages` CI failure diagnosed.** `ci` passes; `pages` (mkdocs) fails —
  bp-030 removed `edge/monitor` but left the docs stub `site/api/edge.monitor.md` + `mkdocs.yml` nav →
  mkdocstrings BuildError. Fix scoped (OUT of bp-038 write_scope): delete the stub, drop the nav line,
  fix the `site/index.md` `api/ops/`→`api/ops.md` link. To apply AFTER sealing bp-038.

## 2026-07-15 — COMPLETE. Full suite green; sealed. The algebra is fully wired.

- **Leg 5 pytest: 1138 passed / 8 skipped / 0 failed** (9:18) — the 2 flaky live dream e2e passed this
  run. All 6 new bp-038 tests pass. Gate fully green (all 5 legs).
- **`core/temporal` is now FULLY WIRED** (single-snapshot β₁ via bp-037 + two-snapshot ‖[d,τ]‖ +
  supersession health via bp-038) — "complete the algebra" (owner roadmap #1) is DONE. complex.py,
  operators.py, superconnection.py, boundary.py all have a live consumer.
- Flipped in-progress→complete; cost.actual filled (self-driven opus, ~0.4× est; $ pending next /usage).
- **Next:** seal commit → PROGRESS + PARKING-LOT (CQ-wire-2 built) → clear active-plan → then the
  `pages` CI fix (separate commit, out of this scope) + mkdocs re-verify.

### Re-entry (for the builder — HISTORICAL; plan is COMPLETE)
- Start at **Item 1** (`_restrict` + `coherence_to`) — the heart; Item 2 (poset) is independent.
- `TemporalView` is frozen + store-less (bp-037) — `coherence_to` compares two views via `other._complex`
  (same-class private access); do NOT add a store handle. `_restrict` mirrors `build_citation_complex`'s
  assembly (`complex.py:83-92`) over a node subset, no store.
- Green gate (5-leg): ruff; `mypy core agents eval ops scheduler scripts`==0; argless `mypy` (was 69 —
  assert the new number); `ops.type_gate`; `pytest -q` (bp-037 baseline 1131 passed / 7 skipped; the 2
  live-model dream e2e may flake on a loaded box — tolerate ONLY those).
