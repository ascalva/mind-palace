---
type: build-plan
id: bp-071
alias: chat-code-doc-integrator
status: proposed
design_ref:
  - docs/design-notes/agent-taxonomy.md            # dn-agent-taxonomy §2.5 (the integrator charter) + §3 Phase Γ
  - docs/findings/finding-0109.md                  # the proven-edge rationale (layer 2 = WHERE it happened)
contract: builder
write_scope:
  - core/integrator.py
  - core/stores/causal_edges.py
  - scheduler/cron.py
  - scheduler/router.py
  - ops/lifecycle/launcher.py
  - config/defaults.toml
  - core/config/**
  - tests/unit/test_integrator.py
  - tests/unit/test_causal_edges.py
  - tests/integration/test_integrator_wiring.py
session_budget: 2
cost:
  estimate:
    model: opus
    tokens: 180k
  actual: null
depends_on: [bp-069, bp-070]
parallelizable_with: []
supersedes: null
superseded_by: null
warrant: docs/design-notes/agent-taxonomy.md
created: 2026-07-18
updated: 2026-07-18
re_entry: null
---

# Build Plan — Phase Γ: the first full integrator (chat ↔ code ↔ doc proven edges)

## 0. Mode & provenance
Graduates `dn-agent-taxonomy` §2.5/§3-Γ: the first full instance of the **integrator** role —
deterministic, model-free, multi-strata layer-granular read, edges-only write. "Piggybacks" on Phase
Β (owner sequencing): it reuses the dialogue sensor's L1 action log + tool-record parser and is born
scoped via bp-070's D2. ⚠️ **MINTED AHEAD OF ITS INPUTS: §2/§6 are provisional until bp-069 seals.**
The FIRST build action is the re-ground step (§7 Item 0); bless is meaningful only after Β.

## 1. Objective
The integrator resolves the references L1 events name — commit SHAs, file paths, artifact ids —
against the OTHER strata's stores, minting **C-fiber proven edges** (dialogue action → commit →
files → doc), each carrying its **witness** `(transcript_digest, turn_index, tool_record)` and its
**pair-cut** `(transcript_digest, commit SHA)` per the ratified pair-cut/SLICE discipline. Runs at
the delayed rate (housekeeping; pinned tier — model-free). Born scoped:
`integrator_scope(read={(DIALOGUE, "L1"), (OBSERVED, "commit-ledger"), (DIALOGUE_ARTIFACT, "*")},
write_fibers={C, F})` + conformance test. Ships its instruments: the **C-coverage gauge** (fraction
of D-events with a C-witness — honest partial coverage) and the **resolution-parity gauge** (every
L1 ref → resolved | unresolvable(named) — no silent drops). Causation is READ from tool records,
never inferred; NOT a time-join (finding-0109).

## 2. Context manifest (PROVISIONAL — re-verify at Item 0)
1. `dn-agent-taxonomy` §2.5 in full (witness law, pair-cut, C≠D composition, clock bookmarks,
   assumptions/instruments) + §2.2 (the pricing law this role instantiates).
2. `core/chat_events.py` + `core/stores/chat_events.py` — **as LANDED by bp-069** (the L1 schema +
   parser this consumes; do not re-implement — reuse per finding-0108 discipline).
3. The code-sensor stores — the commit ledger (`code_snapshots.sqlite` ledger; `ops/code_sensor.py`)
   + `code_observations.sqlite`: how a commit SHA and its file set are queryable.
4. `data: reference_edges.sqlite` writer (the proto-integrator, doc↔code) — schema precedent for
   `causal_edges`; decide extend-vs-sibling at re-ground (lean: sibling store, C-fiber-tagged, same
   shape).
5. `core/agent_scope.py` (bp-070) — `integrator_scope`, `assert_conforms`; `core/scope.py` —
   `Fiber "C"`, `Clock.COMMIT`, the DIALOGUE strata.
6. `scheduler/cron.py` + `ops/lifecycle/launcher.py` — the trough-job wiring pattern (as extended by
   bp-069; register beside `chat_events`).

## 3. Investigation & grounding (to COMPLETE at Item 0; charter-level answers recorded)
- **Q1 edge shape:** `(src=(session_id, order|turn), kind=C, dst=commit|file|doc, witness, pair_cut)`;
  one row per resolved endpoint, grouped by the originating event. Weight 1.0 (bp-070 parked).
- **Q2 resolution semantics:** a SHA resolves against the commit ledger; file paths against the
  commit's file set (repo-relative); doc paths → artifact ids where the path is a tracked artifact
  (build-plans/findings/design-notes) else a plain file endpoint. Unresolvable refs are NAMED in the
  report (a pruned/rewritten history is possible — never silently dropped).
- **Q3 idempotency/incrementality:** keyed by (witness) — re-runs are no-ops; process sessions whose
  L1 changed since the last pass (the same digest-based incrementality as L1 itself).
- **Q4 F-edges:** where an L1 event cites a doc without production semantics, mint F (citation) not C
  — the C/F boundary is the tool-record kind (write/commit ⇒ C; read/reference ⇒ F). Default lean;
  confirm at re-ground.

## 4. Reconciliation
All additive: a NEW core module + NEW store + job registration beside existing kinds; router
`_PINNED_KINDS` gains `integrate` (or reuses the bp-069 mechanism); `reset_targets()` gains
`causal_edges.sqlite` (corpus-side; rebuilt by re-integration from raw + ledgers — the floor
invariant: pure function of retained raw). Ratchet stays 19 (core-internal modules).

## 5. Write scope
As front-matter. **OUT:** `core/chat_events.py`/store (bp-069's — consumed); the code-sensor stores
(read-only); `reference_edges` (proto — untouched unless Item 0 rules "extend", then a scope
amendment via finding); the dreamer/grant machinery; the eval harness (Δ).

## 6. Interfaces pinned inline (PROVISIONAL until Item 0)
```python
# core/integrator.py (NEW — the role's first full instance; model-free):
INTEGRATOR_SCOPE = integrator_scope(
    read=[(Stratum.DIALOGUE, "L1"), (Stratum.OBSERVED, "commit-ledger"),
          (Stratum.DIALOGUE_ARTIFACT, "*")],
    write_fibers=["C", "F"])
@dataclass(frozen=True)
class CausalEdge:
    session_id: str; event_order: int; kind: str          # "C" | "F"
    dst_type: str; dst: str                                # commit|file|doc → sha|path|artifact-id
    witness_digest: str; witness_turn: int                 # the pair-cut: (digest, sha) rides dst+witness
@dataclass
class Integrator:
    events: ChatEventStore; ledger: <commit-ledger>; edges: CausalEdgeStore
    def integrate(self, *, max_sessions: int) -> IntegrationReport: ...   # resolve; account everything

# core/stores/causal_edges.py (NEW): keyed by witness; C-coverage + parity queries for the gauges.
# scheduler/cron.py: INTEGRATE_KIND + handler + enqueue (pinned tier, housekeeping cadence).
```

## 7. Items
### Item 0 — RE-GROUND against landed Β  (blast: none — reading + plan amendment)
- **Acceptance:** §2/§3/§6 re-verified against bp-069's landed schemas + the commit-ledger/
  reference_edges reality; discrepancies amended in this plan (journal-logged) BEFORE code. The
  extend-vs-sibling store decision recorded. Stop-and-raise if the L1 schema cannot name what
  resolution needs.
### Item 1 — the edge store + the resolver  (blast: new store + core module)
- **Acceptance:** `uv run pytest tests/unit/test_integrator.py tests/unit/test_causal_edges.py -q`
  green — fixtures: an L1 commit event resolves to its ledger commit + file endpoints; a doc write
  resolves to its artifact; an unresolvable SHA is NAMED not dropped; re-run = 0 new (witness-keyed);
  every edge carries witness + pair-cut; the conformance test passes (inventory ⊑ INTEGRATOR_SCOPE)
  and rejects a smuggled handle. ruff+mypy clean; ratchet 19.
- **Falsifier:** an inferred (witness-less) edge; a time-based join anywhere; silent drops; verbatim
  content in an edge field.
### Item 2 — wiring + instruments  (blast: daemon job + gauges)
- **Acceptance:** `uv run pytest tests/integration/test_integrator_wiring.py -q` green — the daemon
  path runs `integrate` on the housekeeping tick (pinned tier); the C-coverage gauge computes over a
  seeded D+C fixture; the parity gauge accounts every L1 ref. Full suite green-except-the-ratchet.
  Live smoke: one real `integrate` pass over the ingested corpus reports edges > 0 with 0 silent drops.
- **Falsifier:** the job never fires; coverage/parity lie (a dropped ref not counted); a model/tier
  load (it is deterministic).

## 8. Math carried explicitly
The witness law (E_proven = image of a deterministic map over retained raw — re-derivable; the floor
invariant); the pair-cut as a two-token consistent cut proven by the causal bracket
`turn_i ≺ commit ≺ turn_{i+1}` (dn-agent-taxonomy §2.5). No inference anywhere.

## 9. Non-goals
NO model. NO time-based joins. NO interpretive edges (dreamer territory). NO harness/instrument
consumption (Δ). NO grant-enforcement wiring (vocabulary + conformance guard only). NO edit to
bp-069's modules or the code sensor.

## 10. Stop-and-raise conditions
- bp-069/bp-070 not sealed → STOP (build order). Item 0 finds the L1 schema insufficient → STOP,
  `spec-fidelity` finding (never work around by re-parsing raw here — the parser is the sensor's).
- The commit ledger cannot resolve a SHA's file set → STOP, `codebase` finding.
- Any blessing: never.

## 11. Parked decisions
| Decision | Default | Re-entry |
|---|---|---|
| extend reference_edges vs sibling store | sibling (`causal_edges.sqlite`) | Item 0 review |
| C/F boundary | write/commit ⇒ C; read/cite ⇒ F | Item 0 review |
| doc endpoints | artifact-id where tracked, else path | Δ-phase consumption needs |

## 12. Dependency & ordering summary
`depends_on: [bp-069, bp-070]` — Phase Γ. Item 0 (re-ground) → 1 → 2. **Downstream:** Δ feeds
`E_proven` into bp-070's composed graph for the connectivity re-measure (oq-0031 cluster); the
dreamer's grounding law (Law 2) consumes the same edges; the C-edges accumulate the cross-clock
anchor points for the future global clock N.
