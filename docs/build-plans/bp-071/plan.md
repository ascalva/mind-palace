---
type: build-plan
id: bp-071
alias: chat-code-doc-integrator
status: complete
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
  actual:
    model: opus
    sessions: 1                      # single OPUS session (session-31); budget was 2 — under
    tokens: 122.5k                   # output (owner /usage relay); vs 180k estimate → ratio 0.68x
    ratio: 0.68x                     # actual/estimate output; the Item-0 re-ground added the extra
    dollars: 19.30                   # this session's opus spend (owner /usage relay)
    session_delta: +9%               # session window 11% → 20% (owner /usage relay)
    week_delta: +1%                  # week all-models 17% → 18% (the gate figure); Fable 14%→14% (0, all OPUS)
    landed: 3/3 items; full suite 1629p/8s/1f (intentional ratchet); ratchet held 19
depends_on: [bp-069, bp-070]
parallelizable_with: []
supersedes: null
superseded_by: null
warrant: docs/design-notes/agent-taxonomy.md
created: 2026-07-18
updated: 2026-07-19
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

## 3. Investigation & grounding (COMPLETED at Item 0, 2026-07-19 — see finding-0111)
RE-GROUND against landed Β rewrote Q2/Q4 (finding-0111). The charter (proven edges, no inference)
is unchanged; the provisional resolution model was.
- **Q1 edge shape:** `CausalEdge(session_id, event_order, kind="C", dst_type, dst, witness_digest,
  witness_turn, pair_cut_sha)`; one row per directly-proven endpoint. Weight 1.0 (bp-070 parked).
- **Q2 resolution semantics (RE-GROUND).** Every edge is minted DIRECTLY from ONE L1 event's tool
  record — no fan-out, no join. Two species:
  - a `commit` event (ref = ABBREVIATED sha) resolves against the commit ledger (`snapshots`) by
    PREFIX-match → `dst_type=commit, dst=full_sha`, `pair_cut_sha=full_sha` (the (digest, sha) cut).
    0 matches → `unknown-sha`; >1 → `ambiguous-sha`; ref="" → `unparsed-sha` — NAMED, no edge.
  - a `file_edit`/`build_plan`/`finding`/`design_note` event (ref = path/artifact-id) mints its
    endpoint DIRECTLY (the Write/Edit tool record is the proof) → `dst_type=file|doc`,
    `dst=path|artifact-id`, `pair_cut_sha=""` (a working-tree write has no commit anchor — honest).
    `dst_type` INHERITS the L1 event kind (the sensor already ran `_classify_file_write` at
    projection — DRY by construction: the integrator maps kind→dst_type, re-parses nothing).
  - **The ledger stores the FULL TREE, not the diff** (`_py_blobs` = `git ls-tree -r`), so a
    commit's *changed* file set is NOT resolvable from any store; fanning a commit out to it would
    be an inferred edge (the falsifier). action→commit and commit→file are composed by Δ's
    `ComposedGraph` (C≠D composition), never joined here.
- **Q3 idempotency/incrementality:** replace-per-session-digest (the LANDED L1 `replace_session`
  pattern) — a `causal_edge_digests(session_id, transcript_digest)` sidecar; unchanged digest ⇒
  skip; grown digest ⇒ delete-then-remint. Witness-keyed identity is `(digest, event_order, dst)`.
- **Q4 F-edges (RE-GROUND):** v1 mints **C only**. The landed L1 emits a structural `ref` ONLY for
  writes/commits (a read collapses to `tool_use("Read")`, no path) — so no read/cite endpoint
  survives L1. F stays in the scope (`write_fibers={C,F}`) as a declared-but-unfed capability; the
  edge-store write handle claims fiber "C" only (conformance: actual ⊑ declared).

## 4. Reconciliation
All additive: a NEW core module + NEW store + job registration beside existing kinds; router
`_PINNED_KINDS` gains `integrate` (or reuses the bp-069 mechanism); `reset_targets()` gains
`causal_edges.sqlite` (corpus-side; rebuilt by re-integration from raw + ledgers — the floor
invariant: pure function of retained raw). Ratchet stays 19 (core-internal modules).

## 5. Write scope
As front-matter. **OUT:** `core/chat_events.py`/store (bp-069's — consumed); the code-sensor stores
(read-only); `reference_edges` (proto — untouched unless Item 0 rules "extend", then a scope
amendment via finding); the dreamer/grant machinery; the eval harness (Δ).

## 6. Interfaces pinned inline (RE-GROUND at Item 0, 2026-07-19 — finding-0111)
```python
# core/integrator.py (NEW — the role's first full instance; model-free):
INTEGRATOR_SCOPE = integrator_scope(
    read=[(Stratum.DIALOGUE, "L1"), (Stratum.OBSERVED, "commit-ledger"),
          (Stratum.DIALOGUE_ARTIFACT, "*")],
    write_fibers=["C", "F"])                    # F declared-but-unfed in v1 (finding-0111)
@dataclass(frozen=True)
class CausalEdge:
    session_id: str; event_order: int; kind: str          # "C" (v1 mints only C)
    dst_type: str; dst: str                                # commit|file|doc → sha|path|artifact-id
    witness_digest: str; witness_turn: int                 # witness = (digest, turn) + event (kind,ref)
    pair_cut_sha: str                                      # (digest, sha) cut — full sha for commit
                                                           # edges, "" for working-tree writes
@dataclass
class Integrator:
    events: ChatEventStore                                 # bp-069 L1 (read): events_for/digest_for/sessions
    ledger: sqlite3.Connection                             # code_snapshots.sqlite (read): commit existence
    edges: CausalEdgeStore                                 # C-fiber writer (write)
    def integrate(self, *, max_sessions: int) -> IntegrationReport: ...   # resolve; account everything
    # conformance: assert_conforms(INTEGRATOR_SCOPE, (
    #   Handle("chat_events", DIALOGUE), Handle("commit_ledger", OBSERVED),
    #   Handle("causal_edges", DIALOGUE, writes_fiber="C")))

# core/stores/causal_edges.py (NEW): replace-per-session-digest (L1 pattern) + causal_edge_digests
#   sidecar; content id over (witness_digest, event_order, dst_type, dst); C-coverage + parity queries.
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
invariant). Each edge is the image of ONE L1 tool record under the deterministic resolver — no
fan-out, no join, so no unchanged-file leaks into E_proven (finding-0111). The pair-cut
`(digest, full_sha)` is the two-token consistent cut for a `commit` edge (the causal bracket
`turn_i ≺ commit ≺ turn_{i+1}`, dn-agent-taxonomy §2.5, read from op-seq ORDER not wall-clock);
working-tree writes carry `pair_cut_sha=""` (witness-only, no cross-clock cut). No inference anywhere.

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
| extend reference_edges vs sibling store | **DECIDED sibling** (`causal_edges.sqlite`; finding-0111) | — |
| C/F boundary | **DECIDED** write/commit ⇒ C; v1 mints C only, F declared-unfed (finding-0111) | — |
| doc endpoints | dst_type INHERITED from L1 kind (sensor already classified) | Δ-phase consumption needs |
| commit→file composition | NOT joined here — Δ's `ComposedGraph` composes it (finding-0111) | Δ |

## 12. Dependency & ordering summary
`depends_on: [bp-069, bp-070]` — Phase Γ. Item 0 (re-ground) → 1 → 2. **Downstream:** Δ feeds
`E_proven` into bp-070's composed graph for the connectivity re-measure (oq-0031 cluster); the
dreamer's grounding law (Law 2) consumes the same edges; the C-edges accumulate the cross-clock
anchor points for the future global clock N.
