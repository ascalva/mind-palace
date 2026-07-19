---
type: finding
id: finding-0111
status: resolved
created: 2026-07-19
updated: 2026-07-19
links:
  - docs/build-plans/bp-071/plan.md                # §3 Q2 / §6 / §8 re-grounded here (Item 0)
  - ops/code_snapshot.py                           # _py_blobs uses `git ls-tree -r` = FULL TREE, not the diff
  - core/chat_events.py                            # the LANDED L1 schema: only writes/commits carry a structural ref
  - core/stores/reference_edges.py                 # the proto-integrator: extend-vs-sibling decided (sibling)
re_entry: RESOLVED-in-plan (bp-071 Item 0) — no owner input; the redesign stays inside the integrator charter (proven edges, no inference). Δ-phase composition (D3 ComposedGraph) joins action→commit with the separately-held commit→file edges.
ftype: spec-fidelity
origin_plan: bp-071
route: builder
resolution: resolved-in-plan (bp-071 Item 0) — file endpoints come from L1 file-write events (directly proven), NOT from the ledger tree; the ledger resolves commit EXISTENCE + full-sha only; CausalEdge gains `pair_cut_sha`; v1 mints C only (F reserved — no read/cite endpoint survives L1). Plan §3/§6/§8/§11 amended.
---

# bp-071 grounding gaps: the commit ledger stores the full tree (not the diff), and the landed L1 names no read/cite endpoint

## What
Item 0 (re-ground against landed Β) found three divergences between bp-071's PROVISIONAL
§3/§6 (minted ahead of bp-069) and landed reality:

1. **The commit ledger cannot resolve a commit's *changed* file set.** `ops/code_snapshot.py`
   `_py_blobs` snapshots `git ls-tree -r <sha>` — the commit's **FULL tree** of tracked `.py`
   files (hundreds), not its diff. So `snapshots`/`files` (`code_snapshots.sqlite`) holds every
   file present at each commit, not the files that commit produced. §3 Q2's "file paths against
   the commit's file set" — read as the diff, which a causal edge needs — is **not resolvable
   from any store** (`code_observations` is also full-tree; `reference_edges` holds citation
   endpoints, not diffs). This is the §10 "commit ledger cannot resolve a SHA's file set" trip.
   *Resolution (in charter):* do NOT fan a commit event out to a ledger file set (that would be
   an INFERRED edge to unchanged files — the exact falsifier). Instead mint file/doc endpoints
   DIRECTLY from L1's own `file_edit`/`build_plan`/`finding`/`design_note` events (each a proven
   Write/Edit tool record with its own `turn_index`). The ledger is used ONLY to resolve a
   commit event's abbreviated sha → EXISTENCE + full sha. Composing action→commit with the
   separately-held commit→file edges (reference_edges/code_observations) is the Δ-phase
   `ComposedGraph`'s job (C≠D composition), not the integrator's.

2. **The L1 `commit` ref is ABBREVIATED; the ledger key is the full 40-char sha.** `extract_events`
   pulls the sha from the `git commit` result banner `[branch abc1234]` via `[0-9a-f]{7,40}`
   (typically 7–9 chars); `snapshots.commit_sha` is the full `git rev-list` sha (PRIMARY KEY).
   Resolution must PREFIX-match (`WHERE commit_sha LIKE ?||'%'`), with the ambiguity/empty guards
   named (0 matches → `unknown-sha`; >1 → `ambiguous-sha`; ref="" → `unparsed-sha`).

3. **v1 mints C only; F has no data source.** §6/§11's C/F boundary (write/commit ⇒ C;
   read/cite ⇒ F) is correct, but the LANDED L1 emits a structural `ref` ONLY for writes/commits
   — a file READ collapses to `tool_use("Read")` (ref = the tool name, no path). So no read/cite
   endpoint survives L1 in v1: every integrable event is a production (C). F stays in the scope
   (`write_fibers={C,F}`, matching `integrator_scope`) as a declared-but-unfed capability; the
   CausalEdgeStore's write handle claims fiber "C" only (conformance: actual ⊑ declared).

Also confirmed: the "tool_record" witness token is represented STRUCTURALLY by the L1 event
`(kind, ref)` — the integrator does not re-read raw (non-goal; the parser is the sensor's), so the
stored witness is `(transcript_digest, turn_index)` + the event's structural `(kind, ref)`.

## Why it matters
Without (1) the integrator would mint thousands of false action→file edges (every repo file at
each commit), violating the witness law (E_proven = image of a deterministic map over retained
raw — an unchanged file is not in that image). Without (2) every commit event would be a silent
non-resolution. Both would make the C-coverage/parity gauges lie.

## Re-entry condition
RESOLVED in-plan — see `resolution`. No park.

## Routing
`spec-fidelity` → builder-resolved (bp-071 Item 0): plan amended, journal-logged, build continues.
No design-note change (the charter is unchanged; only the provisional plan text was wrong).

## Extend-vs-sibling (plan §11 decision 1) — DECIDED: sibling `causal_edges.sqlite`
`reference_edges` is φ_code's EXCLUSIVE, balance-isolated, corpus-class citation store (its
invariant: "the balance math holds no handle"; sole writer is the code sensor). The integrator is
a DIFFERENT writer with DIFFERENT identity columns (session_id, event_order, witness_digest,
witness_turn, pair_cut_sha) and a cross-strata DIALOGUE→OBSERVED provenance. A second writer into
`reference_edges` would break its sole-interpreter invariant and pollute its symmetric schema.
Owner DRY principle is satisfied by reusing the *shape* (SQLite, content-derived edge id, INSERT
idempotency, digest-sidecar incrementality — the `chat_events`/`reference_edges` convention), NOT
the table. Sibling store, C-fiber-tagged, is the §11 default and the correct call.
