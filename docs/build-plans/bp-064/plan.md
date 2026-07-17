---
type: build-plan
id: bp-064
alias: chat-clock-wiring
status: ready
design_ref:
  - docs/design-notes/chat-sensor.md            # RATIFIED — CS-4 (per-session chains in observed; cuts at session close)
contract: builder
write_scope:
  - core/temporal/spine.py
  - tests/unit/test_chat_clock.py
  - tests/unit/test_cuts.py
  - tests/integrity/test_cut_soundness.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 150k
  actual: null
depends_on: [bp-063]
parallelizable_with: []
created: 2026-07-17
updated: 2026-07-17
links:
  - docs/design-notes/global-event-clock.md               # GC-1..4 — the spine/clock/cut surface this EXTENDS
  - docs/design-notes/chat-sensor.md                       # CS-4 (the decision), CS-6 (the lag instrument this unblocks a gate for)
  - docs/build-plans/bp-063/plan.md                        # the chatlog store whose chains this wires
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — CS-4: wiring the chat clock — per-session chains in the observed stratum, cuts at session close

## 0. Mode & provenance
Graduated from RATIFIED `dn-chat-sensor` CS-4 (the second of the note's §3 tranche). Investigation &
planning produced this from a single context holding the whole note + `spine.py`'s pinned surface + its
"EXTEND, never reshape" banner. Implementation proceeds item-by-item on owner approval. Separate
authority-to-act from the readiness blessing (owner-only `proposed → ready`; no agent flips it). **This
plan touches the pinned spine surface** — it is an EXTENSION (a new store enrolled, a new stratum's
certificate rule), never a reshape; the reconciliation (§4) carries that discipline.

## 1. Objective
Enroll bp-063's `chatlog` store in the spine as a g1-chained source — chain-key = session id, position =
turn index — in the **`observed`** stratum, with a **session-close (trough-style) cut certificate** so a
certified cut over the observed band includes only closed sessions, making conversation proper time and
certified cuts readable at chat grain (the substrate CS-6's formalization-lag instrument needs).

## 2. Context manifest (read in order)
1. `docs/design-notes/chat-sensor.md` §2.4 (CS-4) — WHOLE §2.4: g1-chained store, chain-key = session id,
   position = turn index; stratum `observed` (NO new enum member); wall = bookmark (Law C4); cut legality
   = only closed sessions (trough-style certificate); no new stratum needed (chains are store-scoped).
2. `core/temporal/spine.py` — the pinned surface + its "GC-2/GC-3 EXTEND, never reshape" banner
   (`:100-105`). Specifically: `_STRATUM` (`:241-249`, store→stratum map), `_STRATUM_CERTIFICATES`
   (`:262-267`, stratum→required certificates — has NO `observed` yet), `Certificate` (`:174-181`,
   COMMIT/TROUGH/HANDOFF), `SpineSources` (`:305-357`), `_Builder.versions` (`:394-406`, the per-doc g1
   chain EXEMPLAR to copy for per-session chains), `_Builder.ledger` (`:408+`), `cut_at` (`:821-846`),
   `crossing_edges` (`:866-879`), `_source_certificate` (how a certificate rides from its observable).
3. `core/stores/chatlog.py` (bp-063) — the store being enrolled: `all_rows`, `rows_for(session_id)`, the
   `(session_id, turn_index)` identity. **bp-063 must be complete first** (`depends_on`).
4. `tests/unit/test_cuts.py` — the injected-cut fixture pattern + the exact certificate-composition
   assertions a new `observed` stratum must extend (this file is IN write_scope — it may need a new case).
5. `tests/integrity/test_cut_soundness.py` — the crossing-edge tooth on live stores (IN write_scope —
   confirm a chat chain does not introduce a crossing; extend if it asserts an exhaustive stratum set).
6. `core/temporal/atlas.py:14-66` — `SpineAtlas`/`has(clock)` (GC-4). Confirm whether the observed store's
   frontier clock needs an atlas entry (§3 Q4) — likely automatic (store-scoped frontier), verify.

## 3. Investigation & grounding
- **Q1 — how does a store enroll as a g1-chained source?** `_Builder.versions` (`spine.py:394-406`) is the
  per-DOC exemplar: `self.present.append("versions")`, then for each row `self._add(store, chain_key, pos,
  produces=..., consumes=...)` and `self.g13_edges.add((prev, eid, "g1"))` per chain. **The chat store
  copies this with chain_key = session_id, pos = turn_index** (both already the store's identity —
  `chatlog.rows_for(session_id)` is ordered by turn_index). A new `_Builder.chatlog(store)` method + a
  `chatlog: ChatlogStore | None` field on `SpineSources` + a `b.chatlog(...)` call in `Spine.derive`
  (`:621-635`). Additive, mirrors versions exactly.
- **Q2 — the stratum and its certificate.** `_STRATUM` (`:241-249`) maps stores→strata; add
  `"chatlog": "observed"`. `_STRATUM_CERTIFICATES` (`:262-267`) has NO `observed` key — a `cut_at(strata=
  {"observed"})` today raises "unknown strata" (`:827-832`). **Add `"observed": frozenset({TROUGH})`**:
  the chat sensor is a scheduler/ops job, so a cut over observed is sound exactly when the sensor is
  quiescent (no mid-session append in flight) — the same TROUGH the `eval` stratum uses (`:266`, "internal
  scheduler jobs, no edge dependency → TROUGH"). Open-session exclusion is enforced at INGEST (bp-063 Q4 —
  the store only ever holds closed-session rows), so the frontier a cut reads is already closed-only; the
  TROUGH certificate attests no in-flight sensor append. *The code does not settle whether observed also
  needs HANDOFF* — it does NOT: the chat sensor reads local files, never the edge↔core seam (bp-063 Q3), so
  no HANDOFF (unlike ops/interpreted). Recorded as a grounded resolution, cross-referenced to `:256-260`.
- **Q3 — does adding `observed` to `_STRATUM_CERTIFICATES` redden existing tests?** Investigate at build:
  `test_cuts.py` asserts per-stratum composition (mirror→COMMIT, ops→TROUGH+HANDOFF, eval→TROUGH) — a NEW
  key is additive and should not redden those, but `test_unknown_stratum_refuses` (`test_cuts.py:174`) uses
  `"nonesuch"`, NOT `"observed"`, so it stays valid. If any test asserts the EXACT set of known strata
  (grep `_STRATUM_CERTIFICATES` in tests), it reddens and is carried in write_scope (`test_cuts.py`,
  `test_cut_soundness.py` are pre-included for exactly this). The plan ADDS a positive case
  (`observed→TROUGH`), never edits an assertion's meaning.
- **Q4 — atlas coverage.** `SpineAtlas.has(clock)` (`atlas.py:54`) reports pullback-ability of a clock's
  window. The chat clock is store-scoped (read via `frontier_at("chatlog")`, a read-clock borrow, Law C3
  `spine.py:740-741`) — read-clocks already resolve through the existing atlas machinery, so **no atlas
  change is expected**. Item 2's acceptance verifies a chat-store frontier is atlas-reachable; if it is
  not, that is a `codebase` finding (a real gap), not a silent patch.
- **Q5 — the crossing-edge tooth.** `crossing_edges(cut)` (`:866-879`) must stay `[]` for a certified
  observed cut. A per-session chat chain produces NO cross-store consumes (an utterance consumes nothing;
  `produces=()` or the transcript digest, `consumes=()`), so it introduces no generator edge INTO the cut
  from outside — no crossing. Item 2 asserts `crossing_edges == []` on an injected observed cut over
  seeded chat sessions.

**Additional risks surfaced:** (a) `SpineSources.resolve` (`:318-357`) opens stores from config paths — a
`chatlog.sqlite` path must resolve there IF the live daemon's spine is to see chat; but `resolve()` reads
`cfg.paths.derived_store.parent` siblings, and `chatlog.sqlite` lives there (bp-063 `open_chatlog_store`),
so add a `chatlog_p = base / "chatlog.sqlite"` branch — additive, guarded by `.exists()` (no side effect).
(b) The `_STRATUM` default map is "a documented default refinable by the View layer" (`:238-240`) — adding
`chatlog` is exactly the sanctioned extension, not a reshape. (c) `frontier()` (`:654-665`) and `downset`
already handle any g1 chain generically — no per-store special-casing needed downstream.

## 4. Reconciliation
- `core/temporal/spine.py:100-105` — the banner **"Public surface (pinned — plan §6; GC-2/GC-3 EXTEND
  this, never reshape it)"** → **cross-reference-on-extension**: this plan is a GC-3-adjacent EXTENSION (a
  new enrolled store + a new stratum certificate rule). No signature changes; `_STRATUM`,
  `_STRATUM_CERTIFICATES`, `SpineSources`, and `_Builder` gain ADDITIVE entries only. An in-file comment at
  each addition cites CS-4 + this plan. No method is reshaped.
- `core/temporal/spine.py:262-267` (`_STRATUM_CERTIFICATES`) — quoted: it lists mirror/ops/interpreted/eval
  and NOT observed → **cross-reference-on-extension**: add `"observed": frozenset({Certificate.TROUGH})`
  with a comment grounding it in CS-4 (session-close trough-style; local-file sensor ⇒ no HANDOFF, cf. the
  eval case `:259`). This is the one behavioral change (a formerly-"unknown" stratum becomes cuttable) —
  announced by the comment + item 1's positive test, never silent.
- `tests/unit/test_cuts.py` — **cross-reference-on-extension**: ADD a `test_observed_cut_composes_trough`
  case beside the existing per-stratum cases; do not edit an existing assertion's meaning. (Carried in
  write_scope because CS-4 extends the surface these tests pin.)
- No correction to committed code — every edit is additive; the "reshape" line is the boundary this plan
  explicitly does not cross.

## 5. Write scope
Front-matter: `core/temporal/spine.py` (the additive enrollment + stratum certificate), a new
`tests/unit/test_chat_clock.py` (the CS-4 falsifiers), and — carried because CS-4 extends the surface they
pin — `tests/unit/test_cuts.py` (a new `observed→TROUGH` composition case) and
`tests/integrity/test_cut_soundness.py` (confirm/extend the crossing tooth for a chat chain). **OUT:**
`core/stores/chatlog.py` (bp-063's — imported, not modified), `core/scope.py` / `core/temporal/atlas.py`
(read-only substrate — §3 Q4 expects NO change; a needed change is a finding, not a patch here), the
correlator (CS-5, its own act), `config/**` beyond what `SpineSources.resolve` already reads (the
`chatlog.sqlite` path is a sibling of `derived_store`, no schema change), the golden set +
`CONSTITUTION.md` (foundation denylist). The `Stratum` enum is UNTOUCHED (no new member — CS-4).

## 6. Interfaces pinned inline
```python
# --- CONSUMED, verbatim current forms (core/temporal/spine.py) ---
class Certificate(Enum):
    COMMIT = "commit"; TROUGH = "trough-quiescent"; HANDOFF = "handoff-empty"

_STRATUM: dict[str, str] = {                     # :241-249 — ADD "chatlog": "observed"
    "versions": "mirror", "catalog": "mirror", "edges": "interpreted", "derived": "interpreted",
    "runledger": "ops", "attestations": "ops", "eval": "eval",
}
_STRATUM_CERTIFICATES: dict[str, frozenset[Certificate]] = {   # :262-267 — ADD "observed": {TROUGH}
    "mirror": frozenset({Certificate.COMMIT}),
    "ops": frozenset({Certificate.TROUGH, Certificate.HANDOFF}),
    "interpreted": frozenset({Certificate.TROUGH, Certificate.HANDOFF}),
    "eval": frozenset({Certificate.TROUGH}),
}

@dataclass
class SpineSources:                              # :305 — ADD `chatlog: ChatlogStore | None = None`
    ledger: RunLedger | None = None
    versions: VersionStore | None = None
    # …existing fields…

# the per-doc g1 chain EXEMPLAR to copy (chain_key = session_id, pos = turn_index):
def versions(self, store: VersionStore) -> None:                 # _Builder, :394-406
    self.present.append("versions")
    prev_by_doc: dict[str, str] = {}
    for row in store._conn.execute("SELECT doc_id, version_seq, digest FROM versions "
                                   "ORDER BY doc_id, version_seq").fetchall():
        eid = self._add("versions", doc_id, seq, produces=(digest,), consumes=())
        prev = prev_by_doc.get(doc_id)
        if prev is not None:
            self.g13_edges.add((prev, eid, "g1"))
        prev_by_doc[doc_id] = eid

def cut_at(self, *, strata: frozenset[str]) -> CertifiedCut: ...  # :821 — raises on a stratum with no cert rule

# --- TO BUILD (all ADDITIVE, in core/temporal/spine.py) ---
# 1. SpineSources.chatlog field + resolve() branch: chatlog_p = base / "chatlog.sqlite" (guarded .exists())
# 2. _Builder.chatlog(self, store): per-session g1 chains — chain_key=session_id, pos=turn_index,
#    produces=(), consumes=() (an utterance mints/consumes no cross-store identifier)
# 3. Spine.derive: `if sources.chatlog is not None: b.chatlog(sources.chatlog)`
# 4. _STRATUM["chatlog"]="observed"; _STRATUM_CERTIFICATES["observed"]=frozenset({Certificate.TROUGH})
```

## 7. Items
### Item 1 — the stratum certificate: `observed → TROUGH`
- **Objective:** teach `cut_at` the `observed` stratum: `_STRATUM_CERTIFICATES["observed"] =
  frozenset({TROUGH})` (session-close trough-style; local-file sensor ⇒ no HANDOFF).
- **Files:** `core/temporal/spine.py`, `tests/unit/test_cuts.py`.
- **Acceptance test:** `uv run pytest tests/unit/test_cuts.py -q` green including a new
  `test_observed_cut_composes_trough` — a cut over `frozenset({"observed"})` composes exactly
  `{Certificate.TROUGH}`; a missing/non-quiescent trough REFUSES (the existing refusal path extends
  unchanged); every pre-existing per-stratum composition case still passes (additive, no reshape).
- **Falsifier:** an `observed` cut composing HANDOFF or COMMIT (wrong certificate — the sensor reads local
  files, not the edge seam); any existing stratum's composition changing (a reshape, not an extension).
- **Invariant(s):** the EXTEND-never-reshape banner (`:100-105`); certificate composition is per-stratum
  additive; a stratum with no cert rule still refuses (never certifies blind).
- **Touches stored data?** No (a constant map + the cut algebra; reads nothing new).
- **Parallelizable?** No (foundation for item 2).  **Depends on:** none (within this plan).

### Item 2 — enrolling the chatlog store: per-session g1 chains
- **Objective:** `SpineSources.chatlog` + `_Builder.chatlog` (per-session g1 chains, chain-key = session
  id, pos = turn index) + the `Spine.derive` call + `_STRATUM["chatlog"] = "observed"` + the
  `resolve()` path branch.
- **Files:** `core/temporal/spine.py`, `tests/unit/test_chat_clock.py`, `tests/integrity/test_cut_soundness.py`.
- **Acceptance test:** `uv run pytest tests/unit/test_chat_clock.py tests/integrity/test_cut_soundness.py -q`
  green — a spine derived over a seeded `ChatlogStore` (two sessions, several turns each) exposes per-session
  chains in `frontier()` keyed `chatlog:<session_id>` with position = the latest turn index; `cut_at(strata=
  frozenset({"observed"}))` (with a quiescent trough) certifies and `crossing_edges(cut) == []`; positions
  within a session are contiguous (turn-index order, never wall time); the store's frontier clock is
  atlas-reachable (or a `codebase` finding is filed, §3 Q4).
- **Falsifier:** any ordering read from a wall timestamp (Law C4 — grep the added code for time/now/ts);
  a per-session chain with non-contiguous positions; a crossing edge on a certified observed cut; a chat
  chain reshaping `frontier()`/`downset` behavior for other stores.
- **Invariant(s):** CS-4 (per-session chains, turn-index order, observed stratum, no new enum member);
  the additive-only extension of the pinned spine surface; `crossing_edges == []` soundness.
- **Touches stored data?** No (reads the chatlog store; the spine is derived, writes nothing). Tests use
  a `:memory:` seeded store.
- **Parallelizable?** No.  **Depends on:** item 1, bp-063.

## 8. Math carried explicitly
N/A — no mathematical object implemented. The chain/cut algebra is the RATIFIED spine's (GC-1..3); this
plan enrolls a store into it, adding no new construction. Conversation proper time is READ through the
existing `frontier_at`/`proper_time` surface once the chains exist — computed by CS-6, not here.

## 9. Non-goals
No new `Stratum` enum member (CS-4 — `observed` is the existing tag; the `OBSERVED_DIALOGUE` refinement is
parked). No formalization-lag instrument (CS-6, triple-gated — this plan opens ONE of its three gates: the
sensor+clock built). No correlator reader (CS-5). No `core/scope.py`/`atlas.py` change (§3 Q4 expects none;
a need is a finding). No realtime cut (session-close only). No mirror access. No reshape of any pinned spine
method — additive enrollment only. No wall-clock ordering (Law C4).

## 10. Stop-and-raise conditions
- Enrolling the chat chain reddens an existing spine test whose assertion would have to CHANGE MEANING
  (not merely gain a case) → STOP: that is a reshape, not an extension; file a `spec-fidelity` finding
  (the CS-4 mapping conflicts with the pinned surface) rather than editing the assertion.
- The observed frontier clock is NOT atlas-reachable (§3 Q4 wrong) → STOP, file a `codebase` finding (a
  real GC-4 gap), park item 2's atlas assertion; the chains + cut still land.
- `crossing_edges` is non-empty on a certified observed cut → STOP: a chat chain is introducing a cross-cut
  read (unexpected — utterances consume nothing); file a `codebase` finding, do not certify.
- Any pressure to add a HANDOFF certificate "to be safe" → STOP (§3 Q2: the sensor reads local files; a
  spurious HANDOFF would make every observed cut require an edge-quiescence it has no dependency on).
- Any blessing (`proposed→ready`, `draft→ratified`): never.

## 11. Parked decisions
| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| `observed` cut certificate set | `{TROUGH}` (session-close, sensor-quiescent; local-file ⇒ no HANDOFF) | `{TROUGH, HANDOFF}` like ops/interpreted (the chat sensor has no edge↔core seam — a HANDOFF requirement is a false dependency) | a future observed source DOES cross the edge seam (an Ambassador-log sensor) → it declares its own cert |
| `OBSERVED_DIALOGUE` refinement stratum | plain `observed` (no new enum member) | a chat-specific stratum now (CS-4 forbids; the enum's refinement-predicate is the named future shape) | CN-4-style per-stratum stats need chat churn separated from other observed churn |
| open-session cut exclusion mechanism | ingest-time (bp-063 only stores closed sessions ⇒ the frontier is closed-only) | a cut-time open-session filter in `cut_at` (adds chat-specific logic to the generic cut algebra — a reshape) | a store lands open-session rows (bp-063's frozen-once-ingested rule is relaxed) |

## 12. Dependency & ordering summary
`depends_on: bp-063` — the `chatlog` store must exist to enroll it. Items serial: 1 (the `observed`
certificate rule — the cut algebra learns the stratum) → 2 (enroll the store's per-session chains + the
`resolve()`/`derive` wiring). Blast radius: read-only/derived throughout — the spine is DERIVED (writes
nothing); the only change is additive map/field entries + a new builder method. **Downstream:** the CS-6
formalization-lag instrument (triple-gated: connectivity tranche built ✓ via bp-059; sensor+clock built ⇐
bp-063+this; correlator scoped grant — the owner's separate act) reads conversation proper time + certified
cuts through the surface this plan completes. Not parallelizable with bp-063 (imports its store).
