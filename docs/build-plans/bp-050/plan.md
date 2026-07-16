---
type: build-plan
id: bp-050
alias: fibers-consumer
status: proposed
design_ref:
  - docs/design-notes/sigma-fibers-and-multiscale-dreaming.md   # RATIFIED 2026-07-16 — §2.2 fiber object; §2.3 pers + three clauses; §2.4 harness realization (FB-1)
contract: builder
write_scope:
  - eval/harness/fibers.py
  - scripts/fibers.py
  - tests/unit/test_fibers.py
  - tests/integration/test_fibers_consumer.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 240k
depends_on: []
parallelizable_with: [bp-051, bp-052]
created: 2026-07-16
updated: 2026-07-16
links:
  - docs/build-plans/bp-049/plan.md   # the sweep engine whose retained cells this consumes; §8 select is the SELECTION consumer sibling
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — FB-1: the σ-fibers consumer (per-claim persistence over the retained per-σ series)

## 0. Mode & provenance
Graduated from RATIFIED `dn-sigma-fibers` (owner hand-flip 2026-07-16). Implementation proceeds
item-by-item on owner blessing (`proposed → ready`, owner-only). This is the RETENTION consumer
dual to bp-049's `select`: same stores, zero schema change, model-free.

## 1. Objective
Add `eval/harness/fibers.py` — a derived, read-only consumer that: reconstructs the cell→σ join
from a declared grid + base config; groups run-ledger claims by content-addressed `claim_id`
across the joined cells; computes per-claim `(pers, hull, gap)`; writes aggregate readings into
the eval store under a fibers `spec_hash`; renders a report section. Plus `scripts/fibers.py`
(the run entry over a completed sweep night).

## 2. Context manifest (read in order)
1. `docs/design-notes/sigma-fibers-and-multiscale-dreaming.md` §2.1–§2.4 (WHOLE — the design;
   the math and falsifiers below cite it, never re-derive it).
2. `core/stores/runledger.py` (whole) — `claim_id` (:37-42), `dream_runs` carries
   `config_fingerprint`+`corpus_digest` (:78-88), `runs()`/`claims()` reads (:171-193).
3. `eval/harness/store.py` (whole) — `EvalKey`, `Reading` (type_tag is a free VARCHAR — :38),
   `put` dedup (:100-111), `query` (:125-151). spec_hash definition (:32).
4. `core/dreaming/shadow.py:94-113` — `_config_fingerprint` (pure function of config; derived
   from `ops.levers.LEVERS`) and :208-212 (`_key`, `_SPEC_PREFIX`).
5. `eval/harness/sweep.py:297-303` (`DriveResult.fp_to_value` — the in-memory map this consumer
   REGENERATES), :328-331 (`_modify_config` — the generic replace pattern to reuse).
6. `core/dreaming/graph.py:22-40` — `MirrorGraph.sim` (the exact-oracle substrate, Item 2).
7. `config/sweeps/dreamer-sigma-ab.toml` — the shipped grid instance (m=21, seeds=5).

## 3. Investigation & grounding (resolved at graduation — verify, don't re-open)
- **fp→σ reconstruction is pure:** for each grid value v, compute
  `_config_fingerprint(replace(cfg, **{section: replace(getattr(cfg, section), **{key: v})}))`
  and match against `dream_runs.config_fingerprint`. MUST record (grid, base fingerprint,
  lever-registry hash) into the fibers evidence at run time — reconstruction across registry
  versions is refused (note §2.4.1 pin), fail-closed with a clear message.
- **Per-claim layer reads the RUN LEDGER, not the eval store** (the note's recorded capsule
  correction, §2.4). Aggregates go TO the eval store.
- **Seeds:** `e(χ, σ_i) = 1` iff emitted in ≥ ⌈k/2⌉ seeds; today claim paths are seed-invariant
  (shadow threads seed only into EvalKey) — the majority rule must be implemented anyway
  (forward-compat, note §2.1 caveat).

## 4. Reconciliation
No committed code is corrected. Stores, fingerprint, sweep engine are read-only dependencies.
`put()` does not gate on registration (the structural_axes precedent) — FB-1 writes
`sigma_persistence.*` readings with `type_tag="Res(sigma)"` BEFORE bp-054 registers them;
recorded here so it never reads as a violation (registration is bp-054's job).

## 5. Write scope
Exactly the four files in frontmatter. **OUT:** every store module, `shadow.py`, `sweep.py`,
`registry.py` (bp-054), any `core/**` file, `eval/golden/**` (denylist).

## 6. Interfaces pinned inline
```python
# runledger reads (verbatim)
def runs(self, *, pipeline: str | None = None) -> list[dict[str, Any]]   # has config_fingerprint, corpus_digest
def claims(self, *, run_id: str | None = None, novel_only: bool = False) -> list[dict[str, Any]]  # claim_id, kind, support_json, confidence

# eval store (verbatim)
class EvalResultsStore:
    def put(self, r: Reading) -> bool          # False => present => SKIP
    def query(self, *, metric_name=None, corpus_ref=None) -> list[Reading]

# the fibers key (NEW — this plan's one design-fixed choice, from note §2.4.3)
# spec_hash = sha256("fibers/v1‖<pipeline>‖<sigma-grid-descriptor>")   # grid IS a battery param
# corpus_ref = the shared corpus_digest; config_fingerprint = the BASE config's; seed = 0 (aggregates)

# per-claim output record (report artifact, NOT a store row)
@dataclass(frozen=True)
class ClaimFiber:
    claim_id: str; kind: str; pers: float; sigma_min: float; sigma_max: float
    gap: bool; n_cells: int; n_seeds_rule: int
```
Aggregate metric names (must match bp-054's registrations EXACTLY):
`sigma_persistence.mean`, `.p50`, `.max`, `.frac_ge_strong`, `.n_claims`.

## 7. Items
### Item 1 — the consumer core + script entry
- **Objective:** fp→σ reconstruction (§3), claim grouping by `claim_id` across joined cells per
  pipeline, `(pers, hull, gap)` per note §2.3 definitions, aggregates into the eval store keyed
  per §6, a markdown report section under `data/reports/`, `scripts/fibers.py <sweep-spec>` entry.
- **Acceptance:** `uv run pytest tests/integration/test_fibers_consumer.py -q` green: over
  in-memory ledger+store seeded by a 3-cell synthetic sweep, the consumer joins all cells,
  computes pers per planted claim, writes exactly the five aggregate readings once; a RE-RUN
  writes ZERO new rows; a registry-state mismatch (simulated) refuses with the §3 message.
- **Falsifier:** the consumer re-keys or overwrites any existing reading; or reconstruction
  silently proceeds under a changed lever registry; or per-claim data is read from the eval
  store rather than the ledger.
### Item 2 — the exact-partition oracle + the falsifier tests
- **Objective:** a test-side exact evaluator: enumerate distinct `sim` entries in [σ_lo,σ_hi],
  evaluate the (deterministic) pipeline once per equivalence interval, compute exact support
  measures — the §2.3-falsifier instrument.
- **Acceptance:** `uv run pytest tests/unit/test_fibers.py -q` green: **(degeneracy anchor)** on
  a synthetic corpus with planted pairwise cosines, a bare-edge claim's pers ==
  `clip((min(w,σ_hi)−σ_lo)/(σ_hi−σ_lo), 0, 1)` exactly; **(ruler test)** grid m=11 vs refined
  m=21 moves pers by ≤ the note's discretization bound; **(gap)** a support set with a hole sets
  `gap=True` and pers counts cells, not the hull.
- **Falsifier:** grid-estimator pers disagrees with the exact oracle beyond the stated bound —
  the computation is broken, STOP and fix before anything ships.

## 8. Math carried explicitly
From ratified §2.3 (cite, hold exactly): `S(χ) = {σ_i ∈ Γ_m : e(χ,σ_i)=1}`;
`pers(χ) = |S(χ)|/m ∈ (0,1]` (support measure, NOT hull length); hull `[min S, max S]`;
`gap(χ) = 1` iff S(χ) is not one run of consecutive grid indices. Validity: one corpus_digest
across cells (assert it — mixed digests ⇒ refuse); deterministic pipelines per (config, seed).
Falsifier three-clause: §7 Item 2 implements clauses (i)+(ii); clause (iii) is bp-057's.

## 9. Non-goals
No gate/tiers (bp-057). No registry edit (bp-054). No `Res[T]` runtime type (bp-054). No
DreamLogEntry change (SF-d parked). No live sweep run (owner/scheduler act). No claim MATCHING
across σ (SF-a parked — exact identity only).

## 10. Stop-and-raise
Mixed corpus_digest across joined cells → STOP (confound). Registry-state mismatch → refuse
(§3). Any write outside the eval store's new keyed readings → scope violation, stop. Any
blessing the builder would have to perform: it must not.

## 11. Parked decisions
| Decision | Default | Re-entry |
|---|---|---|
| exact evaluator in production path | test-oracle only (SF-f) | a consumer needs exact pers |
| per-claim rows in a store | report artifact only | REPL wants inline fibers (SF-d) |

## 12. Dependency & ordering
No dependencies (bp-046/bp-049 machinery is built). Parallel with bp-051/bp-052 (disjoint
scopes). Feeds bp-054 (names) and bp-057 (tiers). First real dataset: the owner's σ-sweep RUN
(oq-0024) — not this builder's act.
