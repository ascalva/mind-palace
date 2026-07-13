---
type: build-plan
id: bp-027
status: complete
design_ref:
  - docs/design-notes/external-grounding.md
contract: builder
write_scope:
  - docs/reference_material/**
session_budget: 1
cost:
  estimate:
    model: sonnet
    tokens: 100k
  actual:
    model: sonnet
    tokens: 89k          # 88,998 metered (notification <usage>) — 0.89× estimate
    tool_calls: 86
    duration_min: 18
depends_on: []
parallelizable_with: [bp-028, bp-029]
created: 2026-07-13
updated: 2026-07-13
links:
  - docs/reference_material/README.md
  - docs/design-notes/core-query-protocol.md
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — reference_material seed fill (the 9 web-verified citations)

> **Every section below is required.** Inapplicable sections are marked `N/A — <reason>`.

## 0. Mode & provenance

Graduated from `dn-external-grounding` (ratified 2026-07-13) §2.2 (the maturity
gradient) + §2.3 (the seed set) + §3.2 (the near-term, no-fable seed fill).
Investigation and planning produced this plan; implementation proceeds item-by-item
on owner approval. Authority-to-act (build) is separate from the readiness blessing
(`proposed → ready`, owner-only, by hand). No agent flips readiness.

This is pure authoring against an **already-established** filesystem form and schema
(`docs/reference_material/README.md` v0; the first resident `moore-aronszajn-1950/`
exists as the exemplar). No code is touched.

## 1. Objective

Author a `docs/reference_material/<slug>/` card (schema-valid `manifest.md` +
`distillation.md`) for each of the nine web-verified citations from the 2026-07-13
literature pass that lacks one, so the curated layer's seed set is `VERIFIED +
DISTILLED` (not yet `EMBEDDED`).

## 2. Context manifest

Read these whole, in order, before writing:

1. `docs/reference_material/README.md` — the v0 manifest schema, the two-plane model, and the three separable states (VERIFIED / DISTILLED / EMBEDDED). The authoring contract.
2. `docs/reference_material/moore-aronszajn-1950/manifest.md` + `distillation.md` — the EXEMPLAR. Match its shape exactly (a `verified` + `not_fetched` card).
3. `docs/design-notes/external-grounding.md` §2.2–§2.3 — why these are VERIFIED+DISTILLED-not-EMBEDDED, and the `load_bearing_for` discipline.
4. `docs/design-notes/core-query-protocol.md` §1.3 item 6 (the literature-pass verdicts) + §2.2 / §2.5 (the load-bearing STATEMENT of each result — this is what each distillation records).

## 3. Investigation & grounding

**N/A — greenfield authoring, no existing code touched.** The only pre-existing
artifact is the exemplar card + the README schema, both in the context manifest;
matching them is authoring, not code investigation.

## 4. Reconciliation

**N/A — nothing corrected or extended.** The one correction this seed set embodies
(Mercer → Moore–Aronszajn) is already carried by the resident `moore-aronszajn-1950/`
card and was already applied inline to `dn-core-query-protocol §2.2`. This plan
adds new cards only; it edits no existing doc or card.

## 5. Write scope

Front-matter `write_scope`: `docs/reference_material/**`. In prose: create new
`docs/reference_material/<slug>/` subdirectories, each with a `manifest.md` and a
`distillation.md`. **Deliberately OUT of scope:** `docs/reference_material/README.md`
(the schema is fixed for v0 — do not revise it); `docs/reference_material/moore-aronszajn-1950/**`
(already resident — leave untouched); ALL code (`ops/code_sensor.py` / φ_doc
manifest-extraction is fable-gated per `dn-external-grounding §1` out-of-scope — NOT
this plan); the `data/` local embedding store (EMBEDDED is bp-029, not this plan);
every design note and finding.

## 6. Interfaces pinned inline

**The `manifest.md` front-matter schema (v0 — copied from `reference_material/README.md`; author each card to THIS shape):**

```yaml
type: reference-material
id: <ref-slug>                      # kebab, e.g. saerens-2009-rsp
citation: "<full citation string>"
identifiers:
  doi: <doi or null>
  arxiv: <id or null>
  isbn: <isbn or null>
  url: <stable url or null>
verification:
  state: verified                   # asserted | verified   → all cards here are `verified`
  date: 2026-07-13
  verdict: CONFIRMED                # CONFIRMED | PARTIAL | REFUTED | UNCERTAIN  → use the pass's verdict
  by: "web-check 2026-07-13 (dn-core-query-protocol §1.3 item 6 literature pass)"
source_ingestion:
  state: not_fetched                # not_fetched | fetched | embedded  → all `not_fetched` here
  venue: <arxiv|scholar|nature|…|null>
  store_ref: null                   # null until bp-029 EMBEDs it
  retrieved: null
authority: high                     # domain-vetted; peer-reviewed math/CS results
load_bearing_for:
  - "<path#section>: <the exact claim this reference grounds>"
cited_by:
  - <path>                          # the notes that cite it
docs:
  - distillation.md
provenance: agent-proposed          # this fill is agent-authored (contrast owner-curated moore-aronszajn)
```

**The exemplar card's front-matter (`moore-aronszajn-1950/manifest.md`) — the shape to match verbatim:** a `verified` + `not_fetched` card whose `load_bearing_for` names the precise `dn-core-query-protocol §2.2` claim and whose `cited_by` lists the notes. Reproduce that structure per ref.

**The nine seed references (from `dn-core-query-protocol §1.3 item 6`; Moore–Aronszajn is ALREADY resident and excluded):**

| # | slug (suggested) | citation | verdict | grounds (dn-core-query-protocol) |
|---|---|---|---|---|
| 1 | `saerens-2009-rsp` | Saerens, Yen, Fouss, Achbany — randomized shortest-paths / free-energy distances (2009) | CONFIRMED | §2.2 the free-energy/RSP family `K(β)` interpolating 1a↔1b |
| 2 | `kivimaki-2013-free-energy` | Kivimäki, Shimbo, Saerens — two-limit free-energy distance (2013) | CONFIRMED | §2.2 the β→∞ / β→0 endpoints of the RSP family |
| 3 | `chebotarev-2011-forest-metrics` | Chebotarev — forest metrics (2011; on the 1997 matrix-forest theorem) | CONFIRMED | §2.2 the resistance/forest-metric locus of mode 1b |
| 4 | `schur-1911-product` | Schur — the Schur (Hadamard) product theorem (1911) | CONFIRMED | §2.2 hybrid retrieval `K_struct ⊙ K_sem` is a cone operation |
| 5 | `schoenberg-1938-negative-type` | Schoenberg — metric spaces of negative type (1938) | CONFIRMED | §2.2 the β=∞ phase transition (metric not of negative type) |
| 6 | `sz-nagy-1953-dilation` | Sz.-Nagy — unitary dilation of contractions (1953) | CONFIRMED | §2.5 the ledger as the isometric dilation of the contractive transport |
| 7 | `litvinov-2005-maslov` | Litvinov — Maslov dequantization survey (2005) | CONFIRMED | §2.2 the tropical endpoint as Maslov dequantization of the path semiring |
| 8 | `quillen-1985-superconnection` | Quillen — superconnections and the Chern character (1985) | CONFIRMED | §2.5 the `[d,τ]` obstruction as superconnection curvature |
| 9 | `alamgir-vonluxburg-2011-p-resistances` | Alamgir & von Luxburg — p-resistances (NIPS 2011) | **PARTIAL** | §2.2 span shortest-path (p=1) → resistance (p=2) → cut/connectivity (p→∞); the distillation must record the PARTIAL correction (the high-p end is cut/connectivity, NOT resistance) |

The builder confirms each citation's exact form + identifiers against `dn-core-query-protocol §1.3 item 6`; the table's slugs/wording are guidance, not gospel.

## 7. Items

### Item 22 — Author the nine seed reference cards

- **Objective:** create `docs/reference_material/<slug>/{manifest.md, distillation.md}` for each of the nine verified references (§6 table), schema-valid and matching the exemplar.
- **Files:** nine new `docs/reference_material/<slug>/manifest.md` + `distillation.md` pairs (created only).
- **Acceptance test:** (a) nine new subdirs exist, each with both files; (b) every `manifest.md` front-matter parses as YAML and carries every v0 key from §6 (a script or `python -c` YAML-load over each front-matter block exits 0 and asserts the required keys present); (c) `verification.state == verified`, `source_ingestion.state == not_fetched`, `store_ref == null` on every card; (d) `verdict` matches the §6 table (CONFIRMED × 8, PARTIAL × 1); (e) each `distillation.md` states the load-bearing result named in `load_bearing_for` and nothing the cited note does not assert.
- **Falsifier:** a manifest that fails YAML-parse or omits a v0 key; a distillation that introduces a claim absent from `dn-core-query-protocol §2.2/§2.5` (the "verify before trust" discipline — a distillation must record the *verified* statement, never a fresh, unverified assertion); any card with `state: embedded` or a non-null `store_ref` (that is bp-029's job, not this plan's); any edit to the README or the moore-aronszajn card.
- **Invariant(s) it must not violate:** objective-only (no owner/mirror/private content in any card — these are ground truth *about the world*); the v0 schema is fixed (do not invent fields); Constitution §9 (these are `agent-proposed`, NOT the sacred golden set — provenance field says so).
- **Touches stored data?** No — docs only; `data/` (the embedding store) is untouched.
- **Parallelizable?** Yes — disjoint write_scope from bp-028/bp-029.  **Depends on:** none.

## 8. Math carried explicitly

**N/A — no mathematical object implemented.** The distillations *describe* mathematical
results in prose, but the plan implements no math machinery (that is bp-029's embedding
pipeline / the deferred math gate, not this authoring plan).

## 9. Non-goals

- **No EMBEDDING.** Full-text fetch → chunk → embed into `data/` is bp-029. Every card here stays `not_fetched`.
- **No φ_doc / code changes.** Wiring the manifest as a `reference`-kind graph node (extending φ_doc to parse `cited_by`/`load_bearing_for`) is fable-gated (`dn-external-grounding §1` out-of-scope; the Jul-17 vet). Not this plan.
- **No schema revision.** The v0 manifest schema is fixed; if it feels wrong, file a finding — do not edit the README.
- **No new distillation of already-resident refs.** Moore–Aronszajn is done.

## 10. Stop-and-raise conditions

- A citation the literature pass marked verified turns out, on authoring, to be unresolvable or to say something other than `load_bearing_for` claims → **file a `spec-defect` finding** (a verified ref that fails on closer read is exactly the dogfood signal `dn-external-grounding §2.3` predicts) and park that one card; author the rest.
- Any urge to embed, to touch code, or to revise the schema → STOP; those are out of scope (§9).
- A blessing (`proposed→ready`, `draft→ratified`) it would have to perform → it must not.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| φ_doc manifest-edge extraction (turn `cited_by`/`load_bearing_for` into graph edges) | deferred — cards ingest as ordinary corpus (semantically searchable) until the kind-migration | do it now (rejected: the `reference`-kind grammar is fable-gated, `dn-external-grounding §1`) | the Jul-17 dn-core-query-protocol fable-vet settles the citation-extraction grammar |
| EMBED the full source text | deferred to bp-029 | embed now (rejected: network boundary + copyright/licence gate is a substantive separate build) | bp-029 (the EMBED tail) reaches `ready` |
| provenance of the seed cards | `agent-proposed` (this fill is agent-authored) | `owner-curated` (rejected: that is reserved for owner-vetted entries like moore-aronszajn) | owner may re-stamp any card `owner-curated` on review |

## 12. Dependency & ordering summary

Single item (22), no internal ordering. `depends_on: []` — buildable immediately.
`parallelizable_with: [bp-028, bp-029]` — disjoint write_scope (`docs/reference_material/**`
vs the code/store scopes of the driver and the EMBED tail). Blast radius: **reversible
docs-only writes** (lowest) — no stored data, no code, no network. This is the safest
of the three external-grounding plans and the natural first to bless.
