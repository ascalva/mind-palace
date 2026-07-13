---
type: finding
id: finding-0063
status: resolved
created: 2026-07-13
updated: 2026-07-13
links:
  - docs/build-plans/bp-026/plan.md
  - tests/unit/test_reference_extraction.py
  - core/stores/reference_edges.py
ftype: spec-defect
origin_plan: bp-026
route: builder
resolution: >
  ReferenceEdge (v2) exposes direction/code_path/qualname/corpus_ref/corpus_kind
  as read-only derived properties over the symmetric source_*/target_* fields,
  recovering the v1 read surface exactly for code_to_corpus/corpus_to_code edges
  (the only directions v1 ever minted) with zero stored asymmetric residue.
  test_reference_extraction.py passes unchanged, no edit to it required.
---

# bp-026's write_scope excludes a fixed file that reads v1 `ReferenceEdge` field names

## What

`docs/build-plans/bp-026/plan.md` §6(b) specifies a v2 `ReferenceEdge`/schema with symmetric
`(source_kind, source_ref, source_detail, target_kind, target_ref, target_detail)` endpoints,
replacing the v1 asymmetric fields (`code_path`, `qualname`, `corpus_ref`, `corpus_kind`) and
making `direction` a derived, non-stored property. The plan's falsifier for Item 18 explicitly
requires the v1 fields NOT survive as stored columns.

However `tests/unit/test_reference_extraction.py` (bp-013's original Item-7 test, landed at
`e20bb09`, pre-dating bp-026) is **not** in bp-026's `write_scope`
(`core/stores/reference_edges.py`, `ops/code_sensor.py`,
`tests/unit/test_reference_edges.py`, `tests/integration/test_reference_edge_isolation.py`
[fixtures only], `docs/build-plans/bp-026/**`, `docs/findings/**` — `test_reference_extraction.py`
is absent from this list). That file directly reads `.direction`, `.code_path`, `.qualname`,
`.corpus_ref`, `.corpus_kind` off `ReferenceEdge` objects returned by `sensor.sync()` /
`sensor.backfill_observations()` (lines 105, 122, 143, 145-146) — it never calls `mint()` with
v1 kwargs directly, so the writer migration (Item 19, in-scope) doesn't break it by itself, but
a literal reading of Item 18's target schema (no `code_path`/`corpus_ref` fields at all) would
break this file's attribute access, and the plan gives the builder no permission to fix it.

## Why it matters

A literal implementation of §6(b) — dropping the v1 field names entirely — would redden a
passing, out-of-write-scope test with no way to repair it from inside this plan's contract,
violating the builder-contract's "never route around a denial" discipline and the isolation
test's sibling requirement that in-scope work never breaks a fixed file outside its zone.

## Re-entry condition

N/A — resolved within this session; no parked criterion.

## Routing

`spec-fidelity` — resolved by the builder (bp-026), not escalated. **Resolution:** the v2
`ReferenceEdge` dataclass stores only the symmetric v2 tuple (honoring the letter of the Item
18 falsifier — no stored asymmetric residue) but exposes `direction`, `code_path`, `qualname`,
`corpus_ref`, `corpus_kind` as **read-only derived properties**, computed from the v2 fields —
the exact same "derived, not stored" treatment the plan already mandates for `direction`
itself, just extended to the other v1-named accessors. For `code_to_corpus`/`corpus_to_code`
edges (the only directions v1 code ever produces or reads) this recovers the v1 read surface
byte-for-byte, so `test_reference_extraction.py` passes with zero edits. For a `corpus_to_corpus`
edge (v2-only; unreachable from any v1 caller) accessing a code-endpoint-shaped alias
(`code_path`/`qualname`) raises `ValueError` rather than returning a misleading value — a
deliberate misuse guard, never hit by existing callers. Annotated here + `journal.md`; no
design-note change needed (this is a codebase-fidelity fix, not a schema-shape change — the
stored DDL and `mint()` signature are exactly §6(b)'s).
