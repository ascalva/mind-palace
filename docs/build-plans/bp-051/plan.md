---
type: build-plan
id: bp-051
alias: spine-skeleton
status: complete
design_ref:
  - docs/design-notes/global-event-clock.md   # RATIFIED 2026-07-16 — §2.1 GC-N1; §2.2 generators g1/g2/g3 + the store audit; §2.7 no-payload; §2.8 three clauses (GC-1)
contract: builder
write_scope:
  - core/temporal/spine.py
  - tests/unit/test_spine.py
  - tests/integrity/test_spine_invariants.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 240k
  actual:
    model: opus
    tokens: 304840        # harness-measured, CUMULATIVE (initial build ~263k + fix rework ~41k)
    tool_uses: 79
    ratio: 1.27           # OVER estimate — the defect+fix rework (finding-0092); clean plans ran ~0.9x
    merged: 2c541db       # fix merge, 5-leg green + LIVE-corpus acyclicity PASS. Initial merge 0a3d468
                          # failed the live acyclicity tooth (1467-event cycle) → finding-0092 → fixed 14b3140
    sealed: 2026-07-16
    dollars: pending      # wave-level $ from owner end-of-session /usage relay → PROGRESS + self-rewrite
    findings: [finding-0092]   # spec-fidelity: g2 over-generated on shared attestation hashes — caught on
                               # LIVE data (worktree had no data/), fixed faithful to §2.8-5, RESOLVED
depends_on: []
parallelizable_with: [bp-050, bp-052]
created: 2026-07-16
updated: 2026-07-16
links:
  - docs/design-notes/capability-scope-algebra.md   # the ratified T machinery this materializes the re-entry of (CS-a/CS-b)
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — GC-1: the spine skeleton (the derived causal event poset, read-side)

## 0. Mode & provenance
Graduated from RATIFIED `dn-global-event-clock` (owner hand-flip 2026-07-16; the CS-a/CS-b
unpark blessing). Read-side ONLY: this plan derives, and never writes back into, any source
store. Owner condition recorded at ratification: the spine must bridge clocks WITHOUT
sacrificing structure or zone separation — GC-N1 (read-side only) is that condition's first half.

## 1. Objective
Add `core/temporal/spine.py`: enumerate store-append events across the audited stores; build
`(Ev, ≼)` from g1 per-store chains + g2 reads-from reference joins (the attestation auto-link
generalized) + g3 recorded program order; expose `order(e, e′) ∈ {before, after, concurrent}`,
per-store frontiers, and per-stratum restriction; enforce acyclicity and no-payload as
integrity tests.

## 2. Context manifest (read in order)
1. `docs/design-notes/global-event-clock.md` §2.1–§2.2, §2.7, §2.8 (WHOLE — the design; the
   audit table is the enumeration spec).
2. `core/attestation/attestor.py:59-69` + `core/attestation/store.py` (`producers_of`) — the
   built g2 exemplar the spine generalizes AND calibrates against (§2.8 clause 5).
3. The audited stores' schemas: `core/stores/versions.py:71-81`, `core/stores/runledger.py`
   (:76-101, :130-168), `core/stores/edges.py:37-44`, `core/stores/derived.py:49-73`,
   `eval/harness/store.py:30-44` (NO order column — the honest gap), `core/stores/catalog.py:34-35`.
4. `core/scope.py:171-184` (the `Clock` enum this will later serve — GC-2's concern, NOT this
   plan's; read for vocabulary only).

## 3. Investigation & grounding
- **SQLite stores carry rowid chains; DuckDB stores are chain-less** (the note's §2.9-5 audit
  law — the A-4 routing pin is the boundary). Chain-less events enter Ev via g2/g3 only, and
  their incomparability is CORRECT output, never an error.
- **Wall timestamps NEVER generate order** (Law C4). Structural expression: the generator code
  paths take no `ts`/`created_at` column as an ordering key — `created_at` may ride as display
  metadata on an event, never into an edge. (Tie-breaks inside one store use rowid; across
  stores there is no tie-break — concurrency is the answer.)
- **No payload:** an event row is (event_id, store, stratum_tag, position, reference_ids) —
  content digests are IDENTIFIERS here, never dereferenced to text (§2.7; falsifier below).

## 4. Reconciliation
No committed code corrected. If any audited store's schema differs on disk from the note's
§2.2 table → file a `codebase` finding and enumerate what IS there (no silent caps: stores not
yet enumerated are NAMED in the spine's report — §2.9-5).

## 5. Write scope
The three files in frontmatter. **OUT:** every store module (read-only), `core/scope.py`
(GC-4's), attestation modules, `eval/**` (except reading the eval store's DB file via its own
class), all denylist files.

## 6. Interfaces pinned inline
```python
# NEW — the spine's public surface (keep this exact shape; GC-2/GC-3 extend it)
@dataclass(frozen=True)
class SpineEvent:
    event_id: str          # "<store>:<chain-key>:<position>" — deterministic, content-free
    store: str
    stratum: str           # the Σ tag (mirror/ops/interpreted/... per the note's visibility rule)
    position: int | None   # None for chain-less (DuckDB) events
    refs: tuple[str, ...]  # outbound content-address identifiers (digests, run_ids, SHAs)

class Order(Enum): BEFORE = "before"; AFTER = "after"; CONCURRENT = "concurrent"

@dataclass
class Spine:
    @classmethod
    def derive(cls, sources: SpineSources) -> "Spine"      # injectable store handles (tests inject fakes)
    def order(self, a: str, b: str) -> Order               # over the transitive closure
    def frontier(self) -> dict[str, int]                   # per-store latest positions
    def restrict(self, stratum: str) -> "Spine"            # N_s (GC-2 consumes)
    def events(self) -> list[SpineEvent]

# the g2 exemplar (verbatim, attestation store) — the calibration oracle
def producers_of(self, hashes: set[str]) -> set[str]       # attestation ids whose outputs ∩ hashes
```
`SpineSources` = a small dataclass of optional store handles (ledger, versions, edges, derived,
attestations, eval, catalog) — every one injectable; production resolver reads config lazily
(the shadow-runner seam pattern).

## 7. Items
### Item 1 — enumeration + g1 chains
- **Acceptance:** `uv run pytest tests/unit/test_spine.py -q` green: over injected fakes, each
  SQLite-shaped store yields a chain in rowid order; per-doc version chains are SEPARATE chains;
  eval-store events carry `position=None` and no g1 edges; event_ids deterministic run-to-run.
- **Falsifier:** any g1 edge derived from a wall/`created_at` comparison (grep-testable: the
  generator never reads those keys for ordering); a re-derivation differing run-to-run.
### Item 2 — g2 + g3 + closure + order()
- **Acceptance:** a claim referencing a version's digest orders AFTER that version event; the
  attestation-DAG restriction of ≼ agrees edge-for-edge with `derived_from_ids` on a seeded
  chain (§2.8 clause 5); `order()` returns CONCURRENT for reference-less cross-store pairs;
  run→claims g3 ordering holds.
- **Falsifier:** spine-vs-attestation-DAG disagreement (the generalization is wrong, not the
  exemplar — STOP); a forged ref creating an edge to a nonexistent event (must be dropped +
  reported, never fabricated).
### Item 3 — the integrity teeth
- **Acceptance:** `uv run pytest tests/integrity/test_spine_invariants.py -q` green:
  **acyclicity** on the real repo's stores (a cycle FAILS the suite — non-skippable);
  **chain-embedding** (every store chain embeds order-isomorphically); **no-payload** (no event
  field contains note text — assert the row shape, and grep the module for store text-column
  reads).
- **Falsifier:** any of the three failing on main at merge time.

## 8. Math carried explicitly
`≼` = reflexive-transitive closure of g1 ∪ g2 ∪ g3 (note §2.2). Soundness law: every edge
witnesses a recorded sequence or information flow; `≼_derived ⊆ ≼_true`, false concurrency
possible (the documented caveat — carried into the module docstring verbatim). Acyclicity is an
invariant, not an assumption: a cycle = corrupted/forged reference = integrity failure.

## 9. Non-goals
No clock maps / p_κ / N_s laws (bp-053). No cuts (bp-055). No T-meet change (bp-056). No
Σ-gated query wrapper (the §2.7 visibility rule is enforced at the View layer later — the
stratum tag lands NOW so the wrapper needs no re-derivation; parked with that re-entry). No new
store, no write path, no model, no network.

## 10. Stop-and-raise
A real cycle found in the live stores' derived order → STOP, file a `codebase` finding (it
means a corrupted reference, not a design problem). Any schema drift from §2 manifest → finding
+ enumerate honestly. Any blessing: never.

## 11. Parked decisions
| Decision | Default | Re-entry |
|---|---|---|
| Σ-gated SpineView wrapper | stratum tags only; library-level | first non-test consumer outside core |
| stores beyond the §2.2 core seven | enumerated but unwired (named in report) | GC-2 needs their clocks |
| transitive reduction persistence | recompute per derive() | spine cost measured too high on grown corpus |

## 12. Dependency & ordering
No dependencies. Parallel with bp-050/bp-052 (disjoint). bp-053/bp-055 extend this file
SEQUENTIALLY (they depend on this plan's merge). Blast radius: read-only, additive — lowest.
