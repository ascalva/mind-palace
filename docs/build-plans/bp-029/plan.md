---
type: build-plan
id: bp-029
status: complete
design_ref:
  - docs/design-notes/external-grounding.md
contract: builder
write_scope:
  - cloud/fetcher/**
  - core/research/**
  - core/stores/curated_store.py
  - config/**
  - docs/reference_material/**
  - tests/integration/test_fetcher_fulltext.py
  - tests/integration/test_curated_store.py
  - tests/integration/test_research_persist.py
  - tests/integration/test_curate_manifest.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 450k
  actual:
    model: opus
    tokens: 120k          # non-cache: 14.7k in + 105.7k out (+16.8M cache-read, 272k cache-write)
    dollars: 13.82
    ratio: 0.27           # 120k / 450k — UNDER, leaner than bp-028's 0.54× (fakes, no live tier)
    session_delta: "+8pp (34%->42%)"
    week_delta: "+1pp (72%->73%, cache-dominated — cheap on the weekly quota)"
depends_on: [bp-028]
parallelizable_with: []
created: 2026-07-13
updated: 2026-07-13
started: 2026-07-13
links:
  - docs/design-notes/external-grounding.md
  - docs/reference_material/README.md
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — the EMBED tail (flip transient → persisted, into a separate curated store)

> **Every section below is required.** Inapplicable sections are marked `N/A — <reason>`.

## 0. Mode & provenance

Graduated from `dn-external-grounding` (ratified 2026-07-13) §2.2 (the two-plane store +
EMBEDDED state) + §2.6 (the EMBED tail + the copyright/licence gate — "the real decision
this note opens") + §2.7 (Inv 1/2/11 reconciliation). Investigation + planning produced
this plan (§3 grounded via a 2026-07-13 recon); implementation proceeds item-by-item on
owner approval. `proposed → ready` is owner-only, by hand.

**The most invariant-touching of the three plans.** It adds a network act (full-text
fetch) and a new local store, and it carries the copyright/licence decision. Run it as a
scrutinized full-strength session; the licence-gate falsifier needs judgment.

## 1. Objective

Flip the ranked-then-discarded pipeline to **persist keepers**: fetch open-access full
text (Europe PMC / arXiv), chunk + embed it into a **separate curated vectorstore** (in
`data/`, gitignored — never the mirror), and mint/update the `reference_material/`
manifest to `source_ingestion.state: embedded` — all gated so only clearly open/licensed
full text is embedded.

## 2. Context manifest

Read whole, in order:

1. `docs/design-notes/external-grounding.md` §2.2 (two-plane store; asserted→verified→DISTILLED→EMBEDDED) + §2.6 (the EMBED tail + copyright gate) + §2.7 (Inv reconciliation).
2. `docs/reference_material/README.md` — the manifest v0 schema, esp. `source_ingestion` (`state`, `venue`, `store_ref`, `retrieved`) and the DISTILLED-vs-EMBEDDED distinction.
3. `core/research/rank.py` — the transient contract this plan extends (the keepers to persist come from `rank_literature`'s output).
4. `core/ingest/chunk.py` — `chunk_text(text, *, max_chars=1200, overlap_chars=150) -> list[Chunk]`; `Chunk(index, text)` + `content_hash`. **Reused unchanged.**
5. `core/ingest/embed.py` — `Embedder.embed_documents/embed_query`; `build_embedder(config)`.
6. `core/stores/vectorstore.py` — `VectorStore` (LanceDB), `add(rows) -> int` (row schema), `open_vector_store(config)`. **The pattern the curated store copies.**
7. `cloud/fetcher/sources.py` (openalex/europepmc/arxiv — currently abstract-only) + `cloud/fetcher/aggregate.py` (the `Paper` record shape) + `cloud/fetcher/handler.py` (the Lambda entry + `http_fetch`).
8. `config/defaults.toml` + `config/loader.py` (`PathsConfig`; how store paths are declared) + `.gitignore` (`data/` line 9, `*.lance/` line 12).

## 3. Investigation & grounding

- **Q1 — Does the fetcher fetch full text today?** No — abstract/metadata only. `cloud/fetcher/sources.py`: openalex reconstructs the abstract from `abstract_inverted_index` (`:72`), europepmc reads `abstractText` (`:125`), arxiv reads `summary` (`:156`). No full-text field is accessed. The code settles this — full text is NEW work.
- **Q2 — What full text is reachable open-access?** Europe PMC exposes an open-access flag + full-text endpoint (`isOpenAccess`); arXiv PDFs are URL-derivable from the id; OpenAlex has no direct full text. So the open-access tail is **Europe PMC + arXiv**; OpenAlex-only records stay DISTILLED-not-EMBEDDED. The code does not settle the exact Europe-PMC full-text endpoint URL — the builder confirms it against the live API at build time (a fetcher integration detail, `codebase`-resolvable).
- **Q3 — Is chunking reusable?** Yes, unchanged: `chunk_text(text, *, max_chars=1200, overlap_chars=150) -> list[Chunk]` (`core/ingest/chunk.py:44-56`). The code settles this.
- **Q4 — Is embedding reusable?** Yes: `Embedder.embed_documents(texts)` (`core/ingest/embed.py:18-34`), built via `build_embedder(config)` (`:37-41`). The code settles this.
- **Q5 — How is a second (curated) store instantiated?** `VectorStore(path, dim)` (`core/stores/vectorstore.py:41-52`); `add(rows) -> int` rows `{id, digest, title, source_path, chunk_index, provenance, text, vector}` (`:54-65`); `open_vector_store(config)` (`:156-160`) reads `cfg.paths.vector_store`. A curated store is a **second instance** at a new path — add `research_store`/`curated_store` to `PathsConfig` and a parallel `open_curated_store(config)` factory. The code settles the pattern; the config key is new.
- **Q6 — Where do curated vectors physically live, and are they git-safe?** `data/` is gitignored (`.gitignore:9`); `*.lance/` too (`:12`). A curated store at `data/research_curated.lance/` is auto-ignored. The code settles this — no git leakage of full text.
- **Q7 — Is the network boundary preserved?** The only network entrypoint is `http_fetch()` in the fetcher (`cloud/fetcher/sources.py:42`), injected into `aggregate()`; `core/` imports no fetcher/urllib/socket. Full-text fetch MUST stay in `cloud/fetcher/**` (Zone C), never in `core/`. The code settles this — the constraint is Inv 2.

**Additional risks or questions surfaced during reading:**
- The full-text fetch is a NEW network act and MUST live in `cloud/fetcher/**`; the embed step is core-side over the already-fetched text (read from the airlock `results/`), so **core never fetches**. This split is load-bearing for Inv 2 and pinned into the item boundaries.
- The `source_path`/`provenance` fields of the curated store's rows must mark these as CURATED-objective, never mirror provenance — so no ranking or retrieval accidentally treats a paper as owner-authored (never-pollute-the-mirror).

## 4. Reconciliation

- `core/research/rank.py:7-10` (the transient doctrine: "ranked in-memory and DISCARDED; never written into the AUTHORED mirror") — `dn-external-grounding §2.4` reframes this: transient was a consequence of a *missing curated home*, not a principle; the flip persists keepers into a **separate** store, so "never pollutes the MIRROR" still holds. → **[cross-ref: extension]** the persist step is a NEW path that reads `rank_literature`'s output and writes the CURATED store — it does NOT modify `rank.py`'s mirror-safety; add a comment at the persist site citing `dn-external-grounding §2.4`. Do NOT weaken or rewrite the `rank.py` transient guarantee for the mirror.
- `docs/reference_material/README.md` `source_ingestion` schema — used as-is; this plan is the first writer of `state: embedded` + a non-null `store_ref`. No schema change (extension, not correction).
- The bp-027 seed cards (if present) — this plan UPDATES their `source_ingestion` when it embeds them. **[cross-ref: extension]** not a correction; the DISTILLED→EMBEDDED transition is the designed maturity step.

## 5. Write scope

Front-matter: `cloud/fetcher/**` (full-text fetch), `core/research/**` (the persist/embed
step — a new module or an addition alongside `rank.py`), `core/stores/curated_store.py`
(the new curated store factory/wrapper — a NEW file only), `config/**` (the new store
path), `docs/reference_material/**` (mint/update manifests). **Deliberately OUT of scope:**
`core/stores/vectorstore.py` itself (copied as a pattern, not edited — if the base
`VectorStore` needs a change, that is a `spec-defect` finding); the mirror vectorstore and
its data (never written); `scheduler/**` + `agents/ambassador/**` (bp-028); `core/ingest/**`
(chunk/embed reused unchanged); every design note, finding, the README schema, and the
foundation denylist.

## 6. Interfaces pinned inline

```python
# core/ingest/chunk.py:44 — REUSED unchanged
def chunk_text(text: str, *, max_chars: int = 1200, overlap_chars: int = 150) -> list[Chunk]: ...
# Chunk(index: int, text: str); .content_hash -> sha256

# core/ingest/embed.py:18 — REUSED unchanged
class Embedder:
    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...
    def embed_query(self, text: str) -> list[float]: ...
def build_embedder(config) -> Embedder: ...

# core/stores/vectorstore.py — the PATTERN the curated store copies (do NOT edit this file)
class VectorStore:                       # LanceDB
    def add(self, rows: Iterable[dict]) -> int: ...   # row: {id, digest, title, source_path,
                                                      #       chunk_index, provenance, text, vector}
def open_vector_store(config) -> VectorStore: ...     # reads cfg.paths.vector_store

# core/research/rank.py:49 — the keepers to persist
# RankedPaper: paper, relevance: float, evidence_tier: str, score: float, flags: tuple[str,...]

# docs/reference_material manifest — the fields this plan WRITES (README v0):
#   source_ingestion: { state: embedded, venue: <arxiv|europepmc>, store_ref: <content-hash/id>, retrieved: <date> }
```

## 7. Items

### Item 27 — Open-access full-text fetch (fetcher-side, Zone C)

- **Objective:** add a `full_text: str | None` field to the `Paper` record and a conditional full-text fetch for open-access Europe PMC + arXiv sources; abstract-only sources leave it `None`.
- **Files:** `cloud/fetcher/sources.py` (europepmc/arxiv full-text fetch), `cloud/fetcher/aggregate.py` (carry `full_text` through the result payload).
- **Acceptance test:** a test with a fake `http_fetch` returning an open-access record populates `full_text`; a non-open-access / OpenAlex-only record yields `full_text is None`; the airlock `results/` payload round-trips `full_text`.
- **Falsifier:** full text is fetched for a record NOT flagged open-access (licence-gate breach at the fetch boundary); OR any full-text fetch code lands outside `cloud/fetcher/**` (Inv 2 breach — `core/` must never fetch).
- **Invariant(s) it must not violate:** Inv 2 (only the fetcher touches the network); Inv 7 (medical evidence-honesty flags carry through unchanged); the licence gate (open-access only).
- **Touches stored data?** No (produces a richer transient payload).
- **Parallelizable?** No (Item 29 depends on it).  **Depends on:** none (fetcher-local).

### Item 28 — The separate curated vectorstore

- **Objective:** a `core/stores/curated_store.py` factory `open_curated_store(config) -> VectorStore` at a new gitignored path, distinct from the mirror store; add the `curated_store` path to config.
- **Files:** `core/stores/curated_store.py` (new), `config/defaults.toml` + `config/loader.py` (`PathsConfig` gains `curated_store` / `research_store`, default `data/research_curated.lance/`).
- **Acceptance test:** `open_curated_store(cfg)` opens a store at the configured `data/*.lance/` path; a round-trip `add()`/read of a row with `provenance="curated"` works; the path resolves under `data/` (gitignored — `git check-ignore` confirms).
- **Falsifier:** the curated store resolves to the mirror store's path or any git-tracked location; OR a curated row carries mirror/owner provenance.
- **Invariant(s) it must not violate:** never-pollute-the-mirror (a physically separate store); Inv 11 (full text lives in `data/`, never git, never egress).
- **Touches stored data?** Yes (creates a new store) — require a dry-run open + round-trip on a temp path before wiring the real path.
- **Parallelizable?** Yes (independent of Item 27).  **Depends on:** none.

### Item 29 — The persist/embed step (chunk → embed → curated store), licence-gated

- **Objective:** after ranking, for each keeper WITH open-access `full_text` that clears the licence gate, `chunk_text` → `embed_documents` → `curated_store.add(...)` with `provenance="curated"`.
- **Files:** `core/research/persist.py` (new; the persist step) — reads `RankedPaper`s + the airlock full text, writes the curated store.
- **Acceptance test:** a test feeds a keeper with open-access full text → asserts N chunks embedded into the curated store with `provenance="curated"` and a returned `store_ref`; a keeper WITHOUT open-access full text is skipped (not embedded), stays DISTILLED-only.
- **Falsifier:** a paper without a clear open-access/licence basis gets embedded (licence-gate breach); OR any chunk lands in the MIRROR store; OR core-side code performs a network fetch (it must read already-fetched text from the airlock `results/`, never fetch).
- **Invariant(s) it must not violate:** the licence gate (default-deny — §11); never-pollute-the-mirror; Inv 2 (no core network); Inv 4 (the embed step returns/writes data, takes no action).
- **Touches stored data?** Yes (writes the curated store) — dry-run count before the real embed.
- **Parallelizable?** No.  **Depends on:** Items 27, 28.

### Item 30 — Mint/update the reference_material manifest (DISTILLED → EMBEDDED)

- **Objective:** for each embedded keeper, set `source_ingestion.state: embedded`, `venue`, `store_ref` (the Item-29 handle), `retrieved` on its `reference_material/<slug>/manifest.md` — updating a bp-027 card if it exists, else minting a new card.
- **Files:** `docs/reference_material/<slug>/manifest.md` (+ `distillation.md` if newly minted).
- **Acceptance test:** each embedded keeper's manifest has `state: embedded` + a non-null `store_ref` matching the curated store; a keeper that was DISTILLED-only stays `not_fetched`; every manifest still passes the v0 schema check.
- **Falsifier:** a manifest reads `embedded` with no corresponding curated-store vectors (a dangling claim — the exact "verify before trust" failure the arc guards against); OR the full source text is written into git (only the `store_ref` pointer belongs in git; the text lives in `data/`).
- **Invariant(s) it must not violate:** Inv 11 (only the pointer is git-tracked, never the source text); the manifest schema (v0).
- **Touches stored data?** Docs only (the vectors are Item 29).
- **Parallelizable?** No.  **Depends on:** Item 29.

## 8. Math carried explicitly

**N/A — no new mathematical object.** Embedding + cosine reuse existing machinery; this
plan adds an ingestion path, not math. (The `w(d,a,c)` authority weight is fable-gated and
out of scope, `dn-external-grounding §1`.)

## 9. Non-goals

- **No `reference`-KIND graph tagging.** Curated chunks ingest as ordinary corpus (searchable) until the fable-vet settles the kind vocabulary (`dn-external-grounding §1` out-of-scope).
- **No OpenAlex full text** (no open-access endpoint) — those stay DISTILLED-only.
- **No mirror writes, ever.** Curated store only.
- **No edit to the base `VectorStore`, chunker, embedder, or `rank.py`'s mirror guarantee** — reused/extended, not modified.
- **No live-driver work** (bp-028) and **no index-query surface** (finding-0070 / fable-vet).

## 10. Stop-and-raise conditions

- The Europe-PMC / arXiv full-text endpoint or licence signal is unclear at build time → default-DENY (skip full-text, keep DISTILLED-only) and file a `codebase` finding noting the unresolved endpoint; never embed on a guess.
- The copyright/licence policy needs an owner ruling beyond default-deny-non-open-access → **park (§11) with an `owner-questions.md` entry** whose default degrades to "open-access-only", and proceed embedding only the clearly-open subset.
- A base-store / chunker / embedder change seems necessary → **file a `spec-defect` finding**; park; do not edit out-of-scope files.
- Any blessing flip it would have to perform → it must not.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| The copyright/licence allow-list (which venues/licences clear the gate automatically) | **default-DENY**: embed full text ONLY for records flagged open-access (Europe PMC `isOpenAccess`, arXiv); everything else stays DISTILLED-only | embed-all (rejected: redistribution/copyright risk — `dn-external-grounding §2.6`); owner-approves-each (deferred: too slow for the worklist, revisit if the open-access subset is too small) | owner ruling on the allow-list, via an `owner-questions.md` entry; default holds until then |
| Curated-store path/name | `data/research_curated.lance/` | reuse the mirror store (rejected: never-pollute-the-mirror); a non-LanceDB store (rejected: reuse the proven `VectorStore`) | — |
| `reference`-kind tagging of curated chunks | none (ordinary corpus) | tag now (rejected: fable-gated grammar) | the Jul-17 dn-core-query-protocol fable-vet |
| Distillation authorship for newly-minted (non-bp-027) cards | agent-proposed, from the paper's own abstract/full text | owner-only (deferred) | owner may re-stamp `owner-curated` on review |

## 12. Dependency & ordering summary

Blast-radius order: **Item 28** (new store, reversible) ∥ **Item 27** (fetcher full-text,
external/network) → **Item 29** (persist/embed, writes the curated store) → **Item 30**
(manifest DISTILLED→EMBEDDED, docs). 29 gates on 27+28; 30 gates on 29.
`depends_on: [bp-028]` — this plan flips bp-028's transient surfacing to persisted, so the
driver must exist first. **Shares `docs/reference_material/**` with bp-027** → must be
sequenced AFTER bp-027 (or run non-concurrently); hence `parallelizable_with: []`. Model:
opus (network + new store + the licence decision; falsifiers need judgment). This is the
last and heaviest of the external-grounding near-term plans.
