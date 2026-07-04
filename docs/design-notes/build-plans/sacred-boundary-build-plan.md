# Sacred-Boundary Design Set — Reconciliation & Build Plan

**Status:** Investigation + plan. Items 1a/1b/1c, 2a, 4a/4b(store+apply), DERIVED_STRATUM,
verdict taxonomy + transport, and Part B are now **BUILT** (owner-approved; see
`docs/PROGRESS.md` 2026-07-04 entries). **This revision (post-builder-review) adds Q7–Q8 and
Item 6 — supersession-edge correctness — which is PLANNING ONLY: awaiting owner approval before
implementation** (it touches stored data and coordinates with `--apply`).
**Origin:** Grounds the July-2026 sacred-boundary design set (`the-sacred-boundary.md`
+ five subsystem notes) against the live codebase per `docs/builder-prompt.md`. The design set
was itself refined mid-build: `ingest-identity-and-amendment.md` §4A and
`dialogue-ingest-and-recursion.md` §4 now carry the supersession corrections Q7–Q8 confirm.
**Location note:** the repo had **no established build-plan location**; this file
creates `docs/design-notes/build-plans/` as the builder prompt directed.

Every claim about current system state below carries a `path:line` citation. Where
the code does not settle a question it is said so explicitly rather than inferred.

---

## Part A — Answered open questions (with citations) + new risks

### Q1 — Index keying (`ingest-identity-and-amendment.md` §8)

**Answer.** The derived embedding index is keyed by **`(raw-note-content-digest,
chunk-position-index)`** — an *occurrence / whole-note-content* key, **not** a
chunk-content-hash. The §3 content-addressed-projection model is **PARTIAL**:
satisfied at the whole-note-artifact grain, absent at the chunk grain, and the §4
versioned-amendment machinery does not exist at all.

Evidence:

- Vector-row id is `f"{r.digest}:{chunk.index}"`, and `digest` is the *raw-note*
  content hash, not the chunk's — write path `core/ingest/index.py:33`; digest
  defined `core/ingest/pipeline.py:35,51`; schema comment "`id` = `f"{digest}:{chunk_index}"`",
  "`digest` = raw-store identity of the source note" `core/stores/vectorstore.py:27-28`.
- `Chunk` carries only `index` + `text` — there is no chunk content hash anywhere
  to key on: `core/ingest/chunk.py:15-18`.
- Index-time dedup is by **whole-note digest**, not chunk: `core/ingest/index.py:24-27`
  (`seen_digests`).
- **Whole-note grain IS content-addressed** (so §3's false-density-from-exact-duplicate
  pathology cannot arise at the note level, and §7's "dedup at authored-artifact
  identity, not proximity" holds): exact re-ingest is a no-op — `core/ingest/sync.py:82-84`
  (UNCHANGED on equal digest); raw dedup — `core/ingest/pipeline.py:51`.
- **Chunk grain is NOT content-addressed.** Amendment is *destroy-and-replace* of
  derived rows keyed by the whole-note digest: on a changed note the store deletes
  the digest and re-embeds **every** chunk (`core/ingest/sync.py:88-89`), then drops
  the previous digest's rows entirely if unreferenced (`core/ingest/sync.py:99-101`).
  So §4's "unchanged chunks keep their existing points — no re-embed" is **not**
  achieved, and there is **no supersession edge / version chain** recording that v2
  supersedes v1.
- The stable document identity §4 needs *does* exist (catalog `source_path` PK, with
  changed/deleted semantics) — `core/stores/catalog.py:32-39`, `:11-13`. What is
  missing is the versioned-amendment machinery layered on it.
- No `supersedes` relation exists: EdgeStore rel-types are
  `{similar, supports, contradicts, contextualizes}` — `core/stores/edges.py:26-29`.

**Verdict:** content-addressed-projection **partial** (note grain yes, chunk grain no;
no versioning). **Touches stored data → highest caution.** Note the retrieval-integrity
check already re-derives chunks from raw and drops non-reproducing rows
(`core/ingest/verify.py`, `PROGRESS.md:1049-1063`), which is adjacent machinery a
chunk-key migration should reuse, not duplicate.

### Q2 — Dialogue operations (`dialogue-ingest-and-recursion.md` §7)

**Answer.** Dialogue ingest today emits a **document** (one `authored-dialogue` note
per owner message), **not** reasoning operations. The starter vocabulary
`{supersede, attach_defeater, record_warrant}` is **entirely absent**; **warrant is
neither node nor edge** — it does not exist. **No real exported dialogues exist** in
the repo to assess additions against.

Evidence:

- Dialogue capture stores the message as a note through the shared `ingest_note` path,
  provenance `AUTHORED_DIALOGUE` — `core/ingest/dialogue.py:44-68` (esp. `:60-64`);
  the Ambassador's CAPTURE just stores + acks — `agents/ambassador/agent.py:114-116,139-140`.
- Vocabulary absent repo-wide (only an incidental "warrants" in
  `eval/effector_drift.py:14`, unrelated).
- No exported/live dialogue corpus exists (only the design note itself). Per the
  note's own bar ("recommend additions only if justified by an actual case, and cite
  it"), **recommend NO additions** to `{supersede, attach_defeater, record_warrant}`
  until a real dialogue corpus exists (see PD2). Recommend **warrant as an edge /
  typed relation, not a node** (a warrant is a relation between claims C, C′, and a
  peer node is precisely the §2 failure mode the note warns against) — see PD3.

Composition points the note asks to confirm:

- **γ^d confidence damper — BUILT.** `core/recursion.py:43-53` (`decay_bound`),
  `:56-80` (`claim_confidence`); depth from `core/stores/derived.py:250-265`. Any
  dialogue-derived interpreted claim routed through `DerivedStore` inherits γ^d **by
  construction** (no provenance param ⇒ INTERPRETED, `core/stores/derived.py:6,181`;
  acyclic ⇒ depth well-defined, `:82-88`).
- **I5 population damper + typed edge budgets — SPECIFIED, NOT BUILT.** Defined only
  in `recursive-strata.md:47-52,64-65`; that note's status is "Parked. Design captured;
  no implementation" (`recursive-strata.md:3`). No `strata` / `node_budget` /
  `edge_budget` exists in code (grep across `core ops scheduler agents`). **Therefore
  the operations cannot yet be "confirmed to compose" with I5 / edge budgets — those
  enforcement points do not exist.** They compose only with γ^d today. This is a
  dependency the sacred-boundary ordering implies but does not name (see the plan).
- Existing typed edges: `core/stores/edges.py:26-29`; grounding/derivation edges as a
  hypergraph junction: `core/stores/derived.py:44,60-79`.

### Q3 — Corpus unit (`founding-corpus.md` §4)

**Answer.** Steady-state ingest is **document-emitting** (whole note → chunks →
vectors), **not** operation-emitting. The founding corpus must therefore share the
document-emitting `ingest_note` path. The required founding **unit** is a *dated,
supersession-linked sequence of documents* — but supersession-linking does not exist
yet (Q1/Q2), so that part of the unit is unmet by the current path.

Evidence:

- Steady-state ingest emits `IngestRecord` (a document + chunks) —
  `core/ingest/pipeline.py:33-62`; `index_records` writes chunk rows —
  `core/ingest/index.py:19-40`.
- The pipeline is explicitly the ONE provenance-parametric path, already reused for a
  batch of authored-elsewhere docs — `core/ingest/pipeline.py:5-9`;
  `core/ingest/curated.py:51-69` (the working template for a founding batch:
  `parse_note → ingest_note(provenance=…) → index_records → catalog.record`).
- **Fracture point:** any *separate* founding path that bypasses
  `ingest_note`/`index_records`/`VaultCatalog.record` fractures provenance at the
  origin. The safe founding path reuses that exact chain (as `curated.py` does).
- The note's "dated, supersession-linked sequence" (`founding-corpus.md` §2.1) needs
  the Q1/Q2 supersession primitive, which is absent — so **founding-corpus is BLOCKED
  on the supersession primitive** (ordering dependency: Q1/Q2 → Q3).

### Q4 — Verdict auth (`verdict-authority.md` §7)

**Answer.** **No verdict-authorization mechanism exists in code.** No verdict store
(`core/stores/verdicts.py` **ABSENT**). **Nothing TOTP-shaped** anywhere (code or
docs, except this note). The Ed25519 attestation-signing code the note wants to reuse
**exists and is production-grade**, and even anticipates an `"owner"` signer. The
Ambassador↔owner interface exists but carries **no verdict path**; verdict signing is
a **new inbound path**.

Evidence:

- No TOTP anywhere (grep of code + docs).
- Verdict store absent: `core/stores/verdicts.py` does not exist; the spec lives in
  `live-adoption-and-longitudinal-harness.md:108-114` (L2 `claim_verdicts` — a **plain
  append-only SQLite with no signature and no sequence number**). Absence corroborated:
  `docs/README.md:118` and the design-note audit "Track L (all L-series artifacts
  absent)" `PROGRESS.md:987-989`.
- Current owner-approval is a recorded **boolean / reference, not a signature**:
  self-mod `GateDecision.approved: bool` — `ops/gate.py:56-75`; CLI records
  `approver="owner"` — `ops/selfmod_cli.py:83-93`; effect `ApprovalRef`
  (approver/strength/ref, no signature) — `ops/effects.py:109-118`.
- **Ed25519 reuse target (reuse, do not re-implement):** primitives
  `core/attestation/crypto.py:52-83` (`sign`/`verify`/`Ed25519Signer`, signer name
  already `"supervisor" | "owner"`); canonical serialization pattern
  `core/attestation/record.py:21-46` (`_canonical`, sorted keys, deterministic) +
  `:63-69` (`signing_payload`); append-only store (structural, no delete/update)
  `core/attestation/store.py:1-11`; record already carries `signature`/`signer` with
  `"owner"` anticipated `core/attestation/record.py:60-61`; signer wired from Keychain/
  Vault via `get_secret` `core/attestation/attestor.py:105-111`.
- **Insertion point:** the Ambassador↔owner turn is `agents/ambassador/agent.py:110-119`
  (reached via the edge interface gateway), but `_dispatch` has no verdict intent
  (`agent.py:126-140`). Per the note's own "Ambassador degrades to transport"
  (verdict-authority §4), the owner device signs (hardware-gated), the Ambassador
  *transports*, and a **new verdict-apply component** verifies signature + monotonic
  sequence, then effects promotion/supersession. The Ambassador's scope is deliberately
  empty (read+propose, never write) — `agents/ambassador/agent.py:53-63` — so the
  *apply* (a write) must **not** be an Ambassador capability (see R7).
- Monotonic sequence number: absent everywhere (attestations carry a timestamp, no
  sequence — `core/attestation/record.py:49-61`) — genuinely new.
- Hardware-key custody (Secure Enclave / FIDO2-PIV): new, owner-operational; the
  current custody path is `get_secret` (Keychain/Vault) `core/attestation/attestor.py:105`.

Reuse confirmation: **yes** — reuse `core/attestation/crypto.py` verbatim; model a
verdict-specific canonical payload on `record.py:_canonical` (do **not** literally reuse
it — it has no verdict-category / insight-id / sequence fields, see R6); store verdicts
in an append-only SQLite modeled on `core/attestation/store.py`, or the L2
`claim_verdicts` schema **extended** with `signature`, `signer`, `seq`.

### Q5 — Effector risk (`effector-risk-computation.md` §7)

**Answer.** Track G scaffolding **exists and is COMPLETE (G1–G7), flag-off**. Bright
lines are **GATED (feasible-set constraints), never PRICED**. There is **no
expected-value / regret / utility / reachability / penalty computation anywhere** — no
interior scalarizer at all. The note's proposed interior optimizer (EV − irreversibility
penalty − alignment-drift penalty *within* the feasible set) is **entirely absent** and
would be new.

Evidence:

- Blast radius is a **3-value class**, not a computed magnitude: `ops/effects.py:47-57`
  (`ReversibilityClass`), `:68-77` (`blast_radius` β ∈ {0, 1, ∞}), `:79-88`
  (`required_approval` w(β) — a lookup, monotone, property-tested).
- The gate is a **pure boolean conjunction** (feasible-set constraint):
  `ops/effect_gate.py:132-144` (`effect_gate_admits`); illegal effect **unconstructable**
  `ops/effects.py:146-163` (`Effect.__post_init__`); filtration by ceiling
  `ops/effects.py:170-204` (`EffectView`).
- An effect **carries no confidence, deliberately** — `ops/effects.py:20-26`, `:144`.
  So EV-over-`c` is structurally excluded today.
- The only "risk number" is a **detection-only** drift gauge, explicitly kept **out of
  any gate** — `eval/effector_drift.py:20-23,105-115` ("this never feeds the gate").
- No priced terms exist (grep for expected-value/regret/reachability/utility/penalty/
  scalarize over the effector code → nothing; the only "unreachable" hits are the ε
  ceiling). No inaction / null-action candidate logic exists (the layer gates a single
  proposed effect; it does not choose among actions).
- Reconciliation target: `hands-and-the-effector-layer.md:119-144` (§4 blast-radius
  filtration — the port order this note quantifies), `:182-194` (§6 gate), `:198-224`
  (§7 propose-never-send + the Dreamer-model precondition). Track G value is gated on
  Track H depth — `PROGRESS.md:1141-1143`, `hands-and-the-effector-layer.md:198-210`.

**Recommendation: PARK** the interior-optimizer / reachability-contraction work (PD1).
The current layer already satisfies the note's load-bearing §3 rule (constraints, not
terms) *trivially* — there are no terms; adding an EV optimizer introduces the exact
machinery the note warns *rationalizes* boundary-crossing, with **no consumer** (every
class above SENSING is unreachable, ε = SENSING — `PROGRESS.md:1085-1088`).

### Q6 — Track L prerequisites (`the-sacred-boundary.md` §4)

**Answer.** Both named prerequisites are **not live blockers in the form the design set
states**, and the set's premise here is **partly stale**:

1. **Provenance migration `--apply` — the named artifact is MOOT.**
   `scripts/migrate_provenance_split.py --apply` relabels legacy `authored` →
   `authored-solo` (`scripts/migrate_provenance_split.py:1-18`; backed by
   `core/stores/vectorstore.py:87-105` + `core/stores/catalog.py:123-136`). It was made
   **moot** by a corpus wipe + native re-ingest: "the provenance-split migration is now
   MOOT (no `--apply` needed)" — `PROGRESS.md:243-244`; reconfirmed `PROGRESS.md:1031-1034`.
   **Discrepancy to surface (R-Q6):** the design set treats "provenance migration
   `--apply`" as a live pending artifact, but the only such artifact in the repo is moot.
   The substantive *pending stored-data migration* is really the **Q1 content-addressed
   chunk-key migration** (unbuilt) and/or the **`DERIVED_STRATUM` reservation**
   (recursive-strata §8 immediate action 1, still undone — `PROGRESS.md:984-986`,
   `core/provenance.py:42-51`). The design set conflates a moot relabel with the real,
   unbuilt migration.

2. **Self-knowledge ingest — BUILT, not confirmed-run.** Code exists
   (`core/ingest/curated.py:32-88`, `scripts/ingest_self_knowledge.py`); it is
   owner-deferred and needs Ollama — `PROGRESS.md:195,252`. No later PROGRESS entry
   confirms it has been run over the live corpus. Status: **built, execution pending
   (owner-operational).**

### Q7 — Version identity / edge keying (`ingest-identity-and-amendment.md` §4A, §8)

**Answer.** Confirmed on all three points, exactly as §4A anticipates: supersession edges are
keyed on **content digest, not version identity**; there is **no version identity independent of
content digest**; and a no-op re-save **records no occurrence**.

- **Edges keyed on content digest.** `core/ingest/sync.py:110-111` (`edge_store.add(prev.digest,
  digest, …)` — endpoints are the previous and new *content* digests); `core/stores/edges.py:57-59`
  (`_edge_id` = SHA-256 over `(rel_type, u, v)`, content-derived). So the **revert case collapses**:
  editing v1 → v2 → back to v1's exact bytes makes the third digest equal v1's, merging the node and
  closing the cycle `(v1→v2)` + `(v2→v1)` — §4A Constraint 1 confirmed against code.
- **No version identity exists.** The catalog is `source_path → (digest, active)` with **no
  version-seq / per-version surrogate** — `core/stores/catalog.py:31-41` (schema: `source_path` PK,
  `digest`, `title`, `provenance`, `active`, `updated_at`); the digest is the *current* version,
  upserted in place on amendment (`core/stores/catalog.py:76-87`). A version-identity key
  (`source_path` + monotonic version-seq, or a surrogate) is a **foundational addition** that touches
  stored data and must coordinate with `--apply` (Item 6).
- **Occurrences not logged on unchanged re-ingest.** `core/ingest/sync.py:90-91` returns `UNCHANGED`
  *before* the ingest attestation (`:103`), and nothing else records a second event; the raw store
  dedups the bytes but logs no occurrence (`core/ingest/pipeline.py:51`). So §2's "ingested twice is
  historical truth and provenance must record it" is **not satisfied** — the no-op re-save drops the
  occurrence fact. Recording it needs an append-only occurrence log, which does not exist.
- **(Bonus) Constraint 4's active-view exclusion IS already satisfied.** `index_amendment`
  (`core/ingest/index.py`) rebuilds the note's projection from the *current* chunks only and
  `delete_source` drops the rest, so a removed chunk's vector never lingers in the active view. Item 6
  is thus only the edge/store correction, not an active-view fix.

### Q8 — Version-history store separation (`ingest-identity-and-amendment.md` §4A Constraint 2, §8)

**Answer.** The balance-math consumer reads the **same `EdgeStore`** that now holds `supersedes`
edges and **does not filter by rel-type**. `supersedes` is excluded today only **accidentally** —
*weaker* than §4A assumed (there is not even a rel-type filter to lean on).

- `build_complex` overlays persisted edges onto the signed adjacency the balance math consumes
  (`core/complex/build.py:127` → `_overlay_signed`). `_overlay_signed` iterates **`edges.all()`** with
  **no rel-type selection** (`core/complex/build.py:145`) and sets `signed[i,j] = sign·w` for every
  edge whose endpoints are both nodes (`:149-151`); the signed Laplacian / frustration math then sum
  those signs (`core/complex/balance.py:77-105`).
- So `supersedes` is skipped **only because the superseded endpoint (the prev-version digest) is not
  an active node** → `if i is None or j is None: continue` (`core/complex/build.py:147-148`). The
  placeholder `sign=+1` (`core/ingest/sync.py:110`) would become a live `+w` support edge the instant
  both endpoints are active nodes. This **confirms and sharpens §4A Constraint 2**: version history
  must move to a structure the balance math is *structurally unable to read*, not merely a filtered
  view of the shared store.

### Additional questions / risks discovered (not anticipated by the design set)

- **R1 — §3-vs-§7 tension at chunk grain (design-internal contradiction).** §3 says
  "one point per canonical chunk, keyed by chunk-content-hash" (global); §7 says never
  coalesce distinct authored artifacts that agree. **Global** chunk-hash keying would
  coalesce a verbatim chunk shared by two *distinct* notes — erasing the corroboration
  §7 protects. Resolution: chunk identity must be **`(stable-doc-id, chunk-content-hash)`
  scoped within a version chain**, not bare chunk-content-hash. `ingest-identity-and-amendment.md:43-50`
  vs `:94-106`. This must be settled before Q1's migration (Item 1).

- **R2 — "supersession edges in `recursive-strata.md`" is a mis-citation.**
  `ingest-identity-and-amendment.md:124` claims consistency with "the supersession edges
  in `recursive-strata.md`", but that note models **decay (I2) + promotion (I1)**, not
  supersession edges (`recursive-strata.md:39-43`), and the EdgeStore has no `supersedes`
  type (`core/stores/edges.py:26-29`). Supersession is **new**, not "already there."

- **R3 — Verdict-taxonomy mismatch.** `verdict-authority.md:19` names verdicts
  "adopt / reject / supersede / promote", but the ratified-candidate taxonomy is
  `novel_useful / true_known / plausible / wrong / noise`
  (`live-adoption-and-longitudinal-harness.md:98-106`) + recursive-strata's
  "promote insight weight" (`recursive-strata.md:84`). The signing design must sign
  **whatever taxonomy is ratified**; the note's paraphrase is not the taxonomy.

- **R4 — The verdict note's reconciliation claim is inaccurate.**
  `verdict-authority.md:9-10,105` says `security-planes.md` "already records the
  TOTP-wrong / Ed25519 direction." `security-planes.md` contains **no TOTP**; it records
  the *verdict-store inbox* (`security-planes.md:110`) and *Ed25519-for-integrity*
  (`security-planes.md:93`). The verdict store's true home is
  `live-adoption-and-longitudinal-harness.md:92-136` (L2). The cross-reference should
  target L2 (extend) + security-planes §6 (cross-ref), not a "TOTP already recorded"
  correction (see Part B).

- **R5 — Two different "depths."** The built γ^d damper's `depth` counts *derivation-DAG
  hops* among interpreted artifacts (`core/stores/derived.py:250-265`); recursive-strata's
  I4 "stratum depth" is *cycle number* (`recursive-strata.md:45`). `dialogue-ingest §5`
  conflates the loop's stratum depth with the built derivation depth. Which depth governs
  the damper for dialogue-emitted derived edges must be pinned before Item 2b.

- **R6 — Attestation `_canonical` cannot express a verdict.** It has no
  verdict-category / insight-id / sequence fields (`core/attestation/record.py:21-46`),
  so "reuse the attestation-signing code" must mean the **crypto primitives + the
  pattern**, not the record type. A verdict needs its own canonical payload.

- **R7 — Ambassador scope excludes verdict *application*.** The Ambassador is
  read+propose, never write (`agents/ambassador/agent.py:53-63`); applying a verdict is a
  write. Verdict application must live in a separate component; the Ambassador only
  transports the signed verdict (consistent with verdict-authority §4).

---

## Part B — Reconciliation proposal (propose only; do not apply)

**Finding:** all five subsystem notes **extend** their home docs; none **contradicts**
one. BUILD-SPEC §8 asserts only note-grain content-addressing ("hash the raw; this also
gives dedup for free" — `docs/BUILD-SPEC.md:144`), which the chunk-hash model refines,
not contradicts. **Therefore: five cross-references, zero partially-superseded banners
against existing docs.** The single *correction* needed is internal to the new
verdict-authority note (R4). Proposed diffs (not applied):

**B1 — `verdict-authority.md` extends `live-adoption-and-longitudinal-harness.md` §3 (L2)
and `security-planes.md` §6 → cross-references; plus a self-correction (R4).**

_Add to `live-adoption-and-longitudinal-harness.md` after the L2 `claim_verdicts` schema
(`:108-114`):_
```diff
   config_fingerprint_at_verdict)`. Verdicts are **operational ground truth, not mirror
   content** ...
+
+  > **Cross-ref (verdict authentication):** `design-notes/verdict-authority.md` extends
+  > this store with owner-attributable authentication — an Ed25519 signature over a
+  > canonical verdict payload + a monotonic sequence number (columns `signature`,
+  > `signer`, `seq`), so a compromised transport can drop/reorder but never forge a
+  > verdict. The plain schema here is the base; signing is the sacred-boundary upgrade.
```
_Add to `security-planes.md` §6 at the verdict-store-inbox bullet (`:110`):_
```diff
 - Recommendations land in the verdict store's inbox as annotations. Promotion spends
-  only owner verdicts. ...
+  only owner verdicts. ... (See `design-notes/verdict-authority.md` for how an owner
+  verdict is authenticated — Ed25519 over the canonical payload, not a possession proof.)
```
_Self-correction to `verdict-authority.md` §8 (R4), owner to ratify:_ replace
"already records the TOTP-wrong / Ed25519 direction" with a reference to the **verdict
store inbox** (`security-planes.md` §6) and the **L2 verdict store**
(`live-adoption` §3); drop the claim that TOTP is discussed in security-planes.

**B2 — `ingest-identity-and-amendment.md` extends `recursive-strata.md` §4 and
`BUILD-SPEC.md` §8 → cross-reference; fix the R2 mis-citation.**

_Add to `recursive-strata.md` near I2 (`:41-43`):_
```diff
 **I2 — Decay by default.** ...
+
+  > **Cross-ref (identity & amendment):** `design-notes/ingest-identity-and-amendment.md`
+  > gives the structural-layer instantiation — corrections are supersession + re-projection
+  > of the derived index, never in-place edits; decay (I2) and supersession are distinct
+  > mechanisms (supersession is not yet an edge type in this note).
```
_(The reciprocal fix in `ingest-identity-and-amendment.md:124`: soften "the supersession
edges in `recursive-strata.md`" to "the decay/promotion discipline in `recursive-strata.md`
(supersession as an edge type is introduced here, not there)".)_

**B3 — `dialogue-ingest-and-recursion.md` extends `recursive-strata.md` and
`live-adoption-and-longitudinal-harness.md` → cross-references.**

_Add to `recursive-strata.md` §2 (`:16-21`):_
```diff
 ... the recursion is fixed-point iteration of D — not call-stack recursion.
+
+  > **Cross-ref (ingest operations):** `design-notes/dialogue-ingest-and-recursion.md`
+  > is the concrete ingest-operation instantiation of this map — the operation vocabulary
+  > (supersede / attach_defeater / record_warrant) that turns "a thought" into a graph
+  > change, composing with the I5 budgets and γ^d bound specified here.
```
_Add to `live-adoption-and-longitudinal-harness.md` where the longitudinal study is
framed (§6 / the L4 curves section):_ a cross-ref to dialogue-ingest §5–§6 as the
**closed-loop** form (ingest-events + sleep-events perturbation study).

**B4 — `founding-corpus.md` extends `live-adoption-and-longitudinal-harness.md`
(control corpus) → cross-reference (no correction — the notes agree).**

_Add to `live-adoption-and-longitudinal-harness.md` at the control-corpus passage
(`:193-196`):_
```diff
 - **The frozen control.** The literary-probe corpus ... runs through the same shadow
   pipeline weekly in its **own graph** (`CURATED`, never the mirror ...).
+  > **Cross-ref:** `design-notes/founding-corpus.md` §2.3 records why the founding corpus
+  > (deliberately coherent) can never double as this control, and why the two acts stay
+  > mechanically distinct.
```

**B5 — `effector-risk-computation.md` extends `hands-and-the-effector-layer.md` §4/§6 →
cross-reference (no banner: both derive the port order, they do not conflict).**

_Add to `hands-and-the-effector-layer.md` §4 (`:142-144`):_
```diff
 The blast-radius metric is why the graduated port order is not a convention but a
 **structural discipline**: ...
+
+  > **Cross-ref (quantitative backing):** `design-notes/effector-risk-computation.md`
+  > derives this port order from reversibility-as-reachability-contraction, adds the
+  > action-risk-vs-inaction-regret decomposition, and pins the load-bearing rule that
+  > bright lines are **constraints on the feasible set, never priced terms**.
```

---

## Part C — Phased build plan

**Ordering constraint** (`the-sacred-boundary.md` §4): **verdict store → close the
recursive loop → longitudinal study.** **Phasing by blast radius:** verification /
read-only → schema-additive → stored-data rewrite (mirrors the effector port order).
Each item is marked **‖ parallelizable** or **⛓ serial**, with explicit dependency edges.

**Unnamed dependency the ordering implies (surfaced):** closing the recursive loop
(Item 2b) needs the **I5 / typed-edge-budget enforcement**, which does not exist and is
parked behind `recursive-strata.md`'s re-entry condition (L4). The plan resolves this by
implementing the operations with budgets **floored to non-recursive** (recovering current
behavior exactly, per `recursive-strata.md:52`) rather than blocking on recursion — see PD4.

**Dependency graph (edges):**
```
  Item4a ─▶ Item4b            (verdict track: sign before store) — the ORDERING-FIRST item
  Item1a ─▶ Item1b ─▶ Item1c  (verify → schema → rewrite; stored data)
  Item2a ─▶ Item2b ;  Item1c ─▶ Item2b ;  (I5/budgets: floored, PD4) ─▶ Item2b
  Item6  ─▶ Item2/Item2b   (version-`supersedes` store separation BEFORE claim-`supersede` vocab — §4A C3)
  Item1  ≈ Item6           (the two ingest-layer identity-keying corrections; both stored-data, both --apply)
  Item1c ─▶ Item3 ;  Item2b ─▶ Item3
  Item4b ─▶ (Track L L4 study) ;  Item2b ─▶ (Track L L4 study)
  Item5  : PARKED (PD1)
```
Item 4 (verdict track) is independent of the 1/2/3 ingest chain → **a distinct builder
can own it fully in parallel.**

---

### Phase 0 — Verification & read-only (tightest, reversible)

**Item 1a — Index-keying verification harness.** ‖ parallelizable. Touches stored
data: **no** (temp stores only).
- *Files (new):* `tests/integration/test_index_keying.py`.
- *Acceptance test:* ingest a note; amend one chunk; re-ingest; assert the **current**
  behavior — all chunk rows for the note re-embed under a new id and the old digest's
  rows are dropped (`core/ingest/sync.py:88-101`) — documenting the Q1 gap as a
  falsifiable fixture.
- *Named falsifier:* if an unchanged chunk **retains** its point id across an amendment,
  the §4 gap does not exist and Items 1b/1c are unnecessary.
- *Invariants:* raw-is-sacred (must not mutate raw); the seal (no network).

**Item 4a — Verdict canonical serialization + signing (pure).** ‖ parallelizable
(different builder). Touches stored data: **no**.
- *Files (new):* `core/verdict/payload.py` (canonical serialization, modeled on
  `core/attestation/record.py:21-46`, with fields: insight/cluster id, verdict category,
  monotonic `seq`, timestamp — R6), `tests/unit/test_verdict_signing.py`.
- *Reuse:* `core/attestation/crypto.py:52-83` verbatim (`Ed25519Signer(name="owner")`).
- *Acceptance test:* sign a verdict with an owner key → `verify` passes; a one-byte
  payload change → fails; a signature made for verdict A does **not** verify for verdict
  B (content-binding).
- *Named falsifier:* a signature valid for verdict A verifies for verdict B (replay
  across verdicts) → the payload binding is wrong.
- *Invariants:* sacred-boundary property 1 (attributable); the model never holds the key
  (code signs — `core/attestation/crypto.py:67-70`).

**Item 5a — Effector-risk falsifier harness.** ⛓ conditional. **PARKED (PD1)** unless
Track G is being opened now; if opened, this is the first (read-only) step and defines
the named falsifier for the reachability-contraction measure before any optimizer is
built (`effector-risk-computation.md` §6).

---

### Phase 1 — Schema-additive (append-only; largely reversible)

**Item 4b — Signed append-only verdict store (the ORDERING-FIRST deliverable).**
⛓ after 4a; ‖ with the Item 1 chain. Touches stored data: **new table only, no rewrite.**
- *Files (new):* `core/stores/verdicts.py` (append-only, modeled on
  `core/attestation/store.py:1-11,86-98`; columns extend the L2 `claim_verdicts` schema
  `live-adoption:109` with `signature`, `signer`, `seq`); `core/verdict/apply.py` (verify
  signature + enforce monotonic `seq` + then effect promotion/supersession — a component
  **separate from the Ambassador**, R7); `tests/integration/test_verdict_store.py`.
  *Changed:* wiring in `scheduler/interface.py` to route a transported signed verdict to
  `verdict/apply` (the Ambassador only carries it — `agents/ambassador/agent.py`).
- *Acceptance test:* append a signed verdict → persisted + verifiable; a **sequence gap**
  is detectable by an auditor; an **unsigned or forged** verdict is **rejected at apply**;
  a replayed/lower `seq` is rejected.
- *Named falsifier:* a verdict with a reused or lower `seq`, or an invalid signature,
  is applied.
- *Invariants:* all four sacred-boundary properties; append-only is **structural** (no
  update/delete — `core/attestation/store.py:1-6`); I12 (the applier is data-in → effect,
  the owner's signed verdict is the only promoter — `recursive-strata.md:39` I1).
- *Parked sub-decision (PD-taxonomy):* the exact verdict categories are owner-ratified
  (R3) — build the store category-agnostic (a `verdict` string validated against a ratified
  set), do not hard-code "adopt/reject/supersede/promote".

**Item 2a — Ratify the dialogue operation vocabulary (decision, no code).**
‖ parallelizable. Touches stored data: **no**.
- *Deliverable:* an owner decision recorded in `dialogue-ingest-and-recursion.md` §4:
  ratify `{supersede, attach_defeater, record_warrant}`; decide `retract/split/merge/
  confidence_adjust` (recommend **defer**, PD2); decide warrant node-vs-edge (recommend
  **edge/relation**, PD3).
- *Acceptance:* the note's §4 status changes from "starter set — to be ratified" to a
  ratified list with each rejected candidate carrying a re-entry condition.

**Item 1b — Chunk content-hash + scoped chunk identity (schema).** ⛓ after 1a; **only if
1a shows the gap AND owner wants §4 semantics** (PD5). Touches stored data: **additive
columns, no rewrite yet.**
- *Files (changed):* `core/ingest/chunk.py` (add `content_hash` to `Chunk`),
  `core/stores/vectorstore.py:26-36` (add a `chunk_hash` column; id becomes
  `(stable-doc-id, chunk_hash)` per **R1** — *not* bare chunk-hash),
  `core/ingest/index.py:30-39`; *new:* `tests/integration/test_chunk_identity.py`.
  *Also (PD6):* reserve `DERIVED_STRATUM` + integer `depth` in `core/provenance.py:42-51`
  (recursive-strata §8 immediate action 1 — one enum line, do it here).
- *Acceptance test:* across an amendment, an **unchanged** chunk keeps its point (no
  re-embed); two **distinct** notes sharing a verbatim chunk keep **both** points (R1 /
  §7 corroboration preserved).
- *Named falsifier:* a verbatim chunk shared across distinct notes **coalesces** to one
  point (violates §7) → the identity scope is wrong.
- *Invariants:* §7 dedup-at-artifact-identity-not-proximity; raw-is-sacred; derived-is-
  regenerable.

---

### Phase 2 — Stored-data rewrite (highest caution; serialize)

**Item 1c — Migrate to content-addressed chunk keys + supersession edges.** ⛓ after 1b.
Touches stored data: **YES — rewrites the vector-store id scheme.** **Not parallelizable
with anything touching the vector store.**
- *Files (changed):* `core/ingest/sync.py:74-102` (amendment becomes a chunk-level diff:
  unchanged chunks retained, changed/new re-embedded, removed marked superseded — §4);
  `core/stores/edges.py:26-29` (add a `supersedes` rel-type — resolves R2);
  *new:* `scripts/migrate_chunk_keys.py` (dry-run default + `--apply`, modeled on
  `scripts/migrate_provenance_split.py:1-18`; **reuse** `core/ingest/verify.py`'s
  re-derivation so a migrated row is provably raw-consistent).
- *Coordinate with:* the (moot) provenance migration and the `DERIVED_STRATUM`
  reservation — this is the **real** "provenance migration `--apply`" the design set
  half-named (Q6 / R-Q6). Take a restic snapshot first (`PROGRESS.md:194`).
- *Acceptance test:* re-ingesting an amended note produces a **supersession edge**,
  re-embeds **only** changed chunks, and leaves full version history queryable; retrieval
  over unchanged content is byte-identical pre/post migration.
- *Named falsifier:* an amendment loses a chunk's provenance, or an unchanged chunk
  re-embeds, or retrieval output changes for untouched content.
- *Invariants:* append-only log (the raw store and history are never destroyed — only the
  derived projection is rebuilt, `ingest-identity §5`); sacred-boundary property 2
  (append + re-project, no mutate-the-immutable).

**Item 6 — Supersession-edge correctness (`ingest-identity-and-amendment.md` §4A).** ⛓ pairs with
1c (the two ingest-layer identity-keying corrections); **before** Item 2/2b (§4A C3 — claim-
`supersede` must not collide with version-`supersedes`). Touches stored data: **YES** — re-keys the
edge onto a version identity and moves it out of the `EdgeStore`; coordinate with `--apply` + Item 1.
- *Problem (built today, confirmed Q7/Q8):* `sync_path` writes a `SUPERSEDES` edge into the
  balance-fed `EdgeStore` keyed on content digests with `sign=+1` (`core/ingest/sync.py:108-111`,
  `core/stores/edges.py`). That collapses on revert (Q7) and sits in a store the balance math reads
  unfiltered (Q8).
- *Files (changed / new):* **new** `core/stores/versions.py` — an append-only version-history store
  (`versions(doc_id, version_seq, digest, superseded_by, at)`) the balance math cannot reach
  (Constraint 2), keyed on `(doc_id, version_seq)` not digest (Constraint 1); **change**
  `core/ingest/sync.py` to record the version transition there (allocate the next `version_seq` for
  the `source_path`) and **remove** the `EdgeStore`/`SUPERSEDES` write; **change**
  `core/stores/edges.py` to drop the `SUPERSEDES` constant; **change** `core/ingest/sync.py`
  `build_vault_sync` to stop wiring the edge store for supersession; a small migration to move any
  existing `supersedes` rows out of the `EdgeStore`; `tests/integration/test_version_history.py`.
- *Acceptance test:* a revert (v1 → v2 → v1-bytes) yields a **linear** chain v1→v2→v3 (v3 distinct
  from v1 by `version_seq`, not digest); `build_complex._overlay_signed` sees **no** `supersedes`
  sign (assert `A_signed` is unchanged by an amendment); the current version resolves by
  **version-seq**, never by walking edges; **no `sign=+1` placeholder appears in any balance-fed
  edge**.
- *Named falsifier:* the version chain forms a cycle on revert; OR a `supersedes` sign enters
  `A_signed` (a λ_min / frustration change from a version edge); OR `build_complex` can read the
  version store.
- *Invariants:* §4A Constraints 1–4; append-only, **no cycle guard** (a revert edge is truthful
  history — `§4A`); ordering by version-seq, never edge topology (`§4A Ordering authority`); the §8
  firewall / layer separation (§1, §6).
- *Deferred (PD7):* **per-chunk** supersession edges — raw blobs of every version are kept, so
  chunk-removal history is reconstructible by diffing raw; and Constraint 4's active-view exclusion is
  already satisfied (Q7). This item is only the note-version edge/store correction.

**Item 2b — Implement the dialogue operations (close the recursive loop).** ⛓ after 2a + **Item 6**
(§4A C3) +
1c; needs I5/budget enforcement **floored** (PD4). Touches stored data: **YES — writes
supersession/defeater/warrant edges.**
- *Files (changed):* `core/ingest/dialogue.py` (emit operations, not only a document);
  *new:* `core/recursion_ops.py` (the operation → edge mapping) and I5/edge-budget hooks
  (floored to non-recursive by default, `recursive-strata.md:52`);
  `tests/integration/test_dialogue_ops.py`.
- *Acceptance test:* a dialogue **correction** emits a `supersede` edge — the active
  projection shows C′, C lives in history as provenance (not a peer node); derived
  dialogue claims **inherit γ^d** (`core/recursion.py`); with budgets floored, behavior
  equals current document-only ingest (the I3 floor-zero guarantee).
- *Named falsifier:* a correction enters as a **peer assertion** (both C and C′ at the
  authored layer — the §2 failure), or a derived dialogue claim escapes γ^d.
- *Invariants:* I1 (promotion by owner verdict only — no auto-promotion of a dialogue
  conclusion); I5 (unforgeable interpreted — dialogue-derived claims are INTERPRETED,
  `core/stores/derived.py`); γ^d (I10); pin R5 (which depth governs the damper) before
  coding.

---

### Phase 3 — Founding corpus (after the loop is closed; before any corpus is authored)

**Item 3 — Founding-corpus ingest path.** ⛓ after 1c + 2b. Touches stored data: **writes
authored strata (the initial condition).**
- *Files (new):* `core/ingest/founding.py` (a batch driver reusing
  `ingest_note → index_records → catalog.record`, the `core/ingest/curated.py:51-69`
  template, with supersession-sequencing from Item 1c/2b); `scripts/ingest_founding.py`;
  `tests/integration/test_founding_corpus.py`.
- *Acceptance test:* a founding batch ingests as a **dated, supersession-linked sequence**
  through the **same** path as steady-state (no bespoke writer — `founding-corpus.md` §4);
  the control corpus stays **mechanically distinct** (own `CURATED` graph, never the
  mirror — `live-adoption:193-196`, `founding-corpus.md` §2.3).
- *Named falsifier:* the founding path bypasses `ingest_note`/`index_records`/
  `catalog.record` (provenance fracture), or the founding set is reused as the control
  corpus.
- *Invariants:* the one-pipeline rule (`core/ingest/pipeline.py:5-9`); founding is
  **ingest, not fine-tuning** — weights never move (`founding-corpus.md` §1).

### Phase 4 — Longitudinal study (last, per the ordering)

Out of scope for implementation here; named as the downstream consumer (Track L / L4).
Depends on Item 4b (verdict store — the labeled fitness signal) + Item 2b (closed loop).
`dialogue-ingest-and-recursion.md` §6; `live-adoption-and-longitudinal-harness.md` L4.

---

### Parked-decision records (protocol: default · rejected alternatives + reasons · re-entry)

- **PD1 — Effector-risk interior optimizer (Item 5).** *Default:* **PARK.**
  *Rejected:* build-now (adds EV machinery the note itself warns rationalizes
  boundary-crossing, with no consumer — every class above SENSING is unreachable,
  `PROGRESS.md:1085-1088`); delete-the-design (loses the constraint-structure argument).
  *Re-entry:* ε raised past SENSING (a reversible/irreversible class wired) **AND** Track H
  produces a model deep enough to tailor multiple candidate actions requiring
  selection-among-feasible (`hands-and-the-effector-layer.md:198-210`).

- **PD2 — Dialogue vocab extras (`retract/split/merge/confidence_adjust`).** *Default:*
  **defer** to the starter set. *Rejected:* add-now (no cited case exists — no dialogue
  corpus in the repo — violating the note's own bar, `dialogue-ingest §7`).
  *Re-entry:* a real exported dialogue exhibits a case a starter op cannot express; cite it.

- **PD3 — Warrant: node or edge.** *Default:* **edge / typed relation** in the EdgeStore.
  *Rejected:* node (recreates the peer-assertion failure, `dialogue-ingest §2`).
  *Re-entry:* a warrant needs independent retrieval/embedding of its own text (then a
  typed node with its own provenance).

- **PD4 — I5 / edge-budget enforcement for Item 2b.** *Default:* implement operations with
  budgets **floored to non-recursive** (recovers current behavior exactly,
  `recursive-strata.md:52`). *Rejected:* block dialogue ops until recursion is built
  (over-serializes a parked track); build recursion now (parked behind `recursive-strata.md`
  L4 re-entry). *Re-entry:* recursive-strata's L4 adoption criterion is met.

- **PD5 — Chunk-key migration (Items 1b/1c).** *Default:* proceed **only if** Item 1a shows
  the gap **and** the owner wants §4 amendment semantics. *Rejected:* migrate-now
  unconditionally (stored-data risk without demonstrated need); never-migrate (leaves §4 /
  Q3 supersession unmet). *Re-entry:* amendment false-density observed, or the founding
  corpus (Item 3) requires supersession sequencing.

- **PD6 — `DERIVED_STRATUM` reservation.** *Default:* **reserve now** (one enum line +
  integer `depth`, `core/provenance.py:42-51`), consume later — cheap per
  `recursive-strata.md:83`. *Rejected:* skip (a second migration to retrofit after any
  future relabel). *Re-entry:* fold into Item 1b (it is a taxonomy commitment, not a
  mechanical win — `PROGRESS.md:1031-1034`).

- **PD-Q6 — "Provenance migration `--apply`" identity.** *Default:* treat the named
  `migrate_provenance_split.py --apply` as **moot/closed** (`PROGRESS.md:243-244`) and
  treat the **Item 1c chunk-key migration** as the real pending stored-data migration the
  design set half-named. *Rejected:* run the moot relabel (no-op on wiped/re-ingested data);
  assume a third unbuilt migration exists (none does). *Re-entry:* if the owner meant a
  distinct migration, name it before Item 1c.

- **PD7 — Version identity key + per-chunk supersession edges (Item 6).** *Default:* key the new
  version store on **`(doc_id = source_path, monotonic version_seq)`** (the catalog already carries
  the stable `source_path`; add the seq), and **defer** per-chunk supersession edges. *Rejected:* a
  random per-version surrogate (works, but `(source_path, version_seq)` reuses the existing identity
  and is legible); keep the edge in the `EdgeStore` behind a rel-type filter (§4A Constraint 2 rejects
  — correctness-by-discipline + the `sign` hazard, confirmed *accidental-only* in Q8); build per-chunk
  edges now (raw-diff reconstructs the history, so the granularity isn't earning its cost yet).
  *Re-entry (per-chunk edges):* a consumer needs chunk-level supersession without a raw diff.

---

## Status & next step

Items 1a/1b/1c, 2a, 4a/4b (store + apply), DERIVED_STRATUM, verdict taxonomy + transport, and the
Part B cross-references are **built + owner-approved** (`docs/PROGRESS.md`, 2026-07-04 entries).
**Item 6 (supersession-edge correctness) is the sole open item in this revision and is PLANNING
ONLY** — it touches stored data (a new version store + re-keying the supersession relation) and
coordinates with `--apply`, so it awaits explicit owner approval before implementation. It pairs
with Item 1 and must land **before** the dialogue vocabulary (Items 2/2b, §4A C3). Nothing from
Item 6 has been implemented.
