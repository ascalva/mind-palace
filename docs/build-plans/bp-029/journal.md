# bp-029 journal

## 2026-07-13 — minted at graduation (orchestrator)

Born `proposed` from `/graduate dn-external-grounding` (ratified 2026-07-13). The EMBED
tail: flip transient→persisted — fetch open-access full text (Europe PMC / arXiv), chunk
+ embed into a **separate** curated vectorstore (`data/`, gitignored), mint/update the
`reference_material/` manifest to `source_ingestion.state: embedded`. §3 grounded against
the 2026-07-13 recon (citations inline: fetcher is abstract-only today,
`cloud/fetcher/sources.py:72/125/156`; chunk/embed reused unchanged; the curated store is
a second `VectorStore` instance at a new gitignored path; the network boundary is Inv 2 —
full-text fetch MUST stay in `cloud/fetcher/**`). The copyright/licence gate is the real
decision (§2.6): parked default-DENY (open-access only), with an `owner-questions.md`
degrade path for the allow-list. Items 27∥28 → 29 → 30. `depends_on: [bp-028]`; shares
`docs/reference_material/**` with bp-027 → sequenced after it (`parallelizable_with: []`).
Model estimate opus/450k (network + new store + licence judgment). The heaviest, most
invariant-touching of the three. Awaiting the owner-only `proposed → ready` blessing. No
work started.

## 2026-07-13 — build start: context manifest read, design settled (opus/high)

Owner blessed `ready`; budget-gated (week 72%, ~28% headroom; self-driven opus ~250–350k fits);
tier confirmed opus/high. `active-plan` set, status `in-progress`. Read the full §2 manifest
in order. Design resolutions (grounded, `[GROUNDED]` = read at path):

- **`Provenance.CURATED = "curated"` ALREADY EXISTS** (`core/provenance.py:49`) and is deliberately
  **excluded from `MIRROR_READABLE`** (`:80-82`). So Item 29 uses `provenance="curated"` directly;
  never-pollute-the-mirror holds structurally TWO ways (separate physical store + CURATED ∉
  MIRROR_READABLE firewall). **No `core/provenance.py` edit needed** (it is out of write_scope anyway).
- **`full_text` seam** [GROUNDED]: fetcher dict → `results/<id>.json` → `ResearchResult.from_dict`
  (`core/research/airlock.py:51`) → `Paper.from_dict` (`core/research/criteria.py:141`) →
  `RankedPaper.paper` (`rank.py:50`). So Item 27 adds `full_text`/`open_access` to BOTH the fetcher
  dict AND the core `Paper` dataclass (criteria.py is in `core/research/**`); rank.py passes Paper
  through unchanged (no edit). `persist.py` (Item 29) consumes `list[RankedPaper]` standalone.
- **`scheduler/**` is OUT of write_scope** → persist is a NEW core module, unit-tested directly, NOT
  wired into bp-028's live chain (`scheduler/research.py`) in this plan. Clean boundary.
- **OFFLINE BUILD** — core must never fetch (Inv 2), and there is no live Zone-C fetcher/Ollama here.
  So Items 27/28/29 build + unit-test the full mechanism with FAKES (fake `http_fetch`, fake
  `Embedder`). **Item 30 delivers the manifest write+validate mechanism + an end-to-end test on TEMP
  manifests; it does NOT flip real seed cards** — no genuine curated vectors exist for them offline, so
  flipping = the Item-30 dangling-claim falsifier. Real DISTILLED→EMBEDDED card flips ride a live
  driver run (bp-028) once a Zone-C fetcher is deployed. → will file a `spec-fidelity` finding at Item 30.
- **arXiv full text = PDF**, not extractable in the stdlib-only Lambda (`sources.py` docstring:
  "Stdlib only") → default-DENY arXiv full-text (DISTILLED-only), `open_access=True` but
  `full_text=None`; **will file a `codebase` finding**. **Europe PMC OA `fullTextXML`** (stdlib
  `xml.etree`) is the working open-access tail: gate on `isOpenAccess=="Y"` + a `pmcid`. Both paths
  **fail-closed** (any fetch/parse exception → `full_text=None`, never crash the gather, never embed
  garbage — matches aggregate.py's per-source try/except).
- **Licence gate (Item 29)** = `paper.open_access and paper.full_text.strip()` (belt-and-suspenders;
  the explicit `open_access` flag, not mere text-presence, satisfies the falsifier).
- **PathsConfig** gains `curated_store: Path = Path("data/research_curated.lance/")` as a LAST field
  WITH a default (so direct `PathsConfig(...)` construction in tests keeps working); loader reads
  `_resolve(p.get("curated_store", ...))`. `data/` + `*.lance/` are gitignored (`.gitignore:9,12`) →
  auto-ignored, `git check-ignore` confirms in the Item-28 test.

Blast-radius order: **Item 28** (new store, reversible) first, then **27** (fetcher), **29** (persist),
**30** (manifest mechanism). Green gate = all 5 legs run separately (delegate skill).

## 2026-07-13 — write_scope corrected (finding-0072) + Item 28 DONE

- **Scope defect finding-0072 (= finding-0071 class):** bp-029's write_scope omitted the §7 test
  paths → scope-guard denied `tests/**`. Filed finding-0072; **owner authorized in-session** →
  orchestrator added the 4 `tests/integration/{test_fetcher_fulltext,test_curated_store,
  test_research_persist,test_curate_manifest}.py` paths to write_scope (NO inline comments — the
  scope-guard parser keeps a bare-path `# comment` as part of the string; authorization lives in
  this journal + finding-0072). finding-0072 → resolved. Standing fix still owed: enforce the
  test-path check at /graduate.
- **Item 28 DONE.** `core/stores/curated_store.py::open_curated_store(config)` — a thin factory
  aiming the PROVEN `VectorStore` at `cfg.paths.curated_store` (default `data/research_curated.lance`),
  the base store UNTOUCHED (§5: a base-store change would be a spec-defect finding, not an edit).
  `config/loader.py` PathsConfig gained `curated_store: Path` (LAST field, defaulted — direct
  construction unaffected) + loader `_resolve(p.get(...))`; `config/defaults.toml` `[paths]` key added.
  Test `tests/integration/test_curated_store.py` (3 passed): separate-from-mirror + curated round-trip;
  curated ∉ MIRROR_READABLE firewall (all_rows/search); default path under data/ → `git check-ignore`
  confirms gitignored (Inv 11). No Ollama (dim overridden to 3 via `dataclasses.replace`).

## 2026-07-13 — Item 27 DONE (open-access full-text fetch, Zone C)

- **`cloud/fetcher/sources.py`**: each source record now carries `open_access` + `full_text`.
  **Europe PMC** = the working OA tail: gate `isOpenAccess=="Y"` + a `pmcid` → `_europepmc_fulltext`
  fetches `.../PMC/{pmcid}/fullTextXML` (JATS) and extracts text via stdlib `xml.etree.itertext`,
  **failing closed** (any fetch/parse error or empty body → None, DISTILLED-only — the SAME
  injected `fetch`, so tests inject fakes). **arXiv** = `open_access=True`, `full_text=None`
  (PDF not stdlib-extractable → **finding-0073** deferral). **OpenAlex** = honest `is_oa` flag,
  `full_text=None` (no stdlib full text).
- **`core/research/criteria.py`** `Paper` gained `open_access: bool=False`, `full_text: str|None=None`
  + `from_dict` reads them (defaulted — every existing `Paper(...)` unaffected). **`aggregate.py`**:
  passthrough (papers are the source dicts; keys ride the S3 payload) — doc note only.
- Test `tests/integration/test_fetcher_fulltext.py` (5 passed) + `test_fetcher.py` regression (4,
  green): OA→full text; **NON-OA never triggers a full-text fetch** (Item-27 falsifier, asserts the
  fullTextXML URL is never called); fail-closed on malformed XML; arXiv/OpenAlex DISTILLED-only;
  full_text rides `aggregate` → `Paper.from_dict`. **finding-0073** filed (arXiv PDF path deferred,
  builder-routed, not a blocker).

## 2026-07-13 — Item 29 DONE (persist/embed, licence-gated)

- **`core/research/persist.py`** (new): `persist_keepers(ranked, embedder, curated_store, *,
  retrieved=None) -> list[CuratedRecord]`. Licence gate `_passes_licence_gate` = `open_access AND
  full_text.strip()` (default-DENY, belt-and-suspenders). For each keeper: `chunk_text` →
  `embed_documents` → rows `{id: source_path:chunk_hash, digest: store_ref, ..., provenance:
  "curated", source_path: "reference:{source}:{id}"}` → `curated_store.add`. `store_ref =
  sha256(full_text)` (the manifest join). **No network import** (reads already-fetched text — Inv 2);
  returns data, no action (Inv 4). Typed `Paper` (mypy-clean, no getattr duck-typing).
- Test `tests/integration/test_research_persist.py` (5 passed): OA keeper embedded curated; a
  keeper without OA-flag OR without full text is SKIPPED (Item-29 falsifier, store empty); mixed
  batch embeds only the OA one; curated rows never surface under MIRROR_READABLE (search + all_rows);
  store_ref content-addressed (same text→same ref, different→different). Fake `HashingEmbedder`
  `cast` to `Embedder` (new-test-fake rule: cast, don't add mypy errors).

## 2026-07-13 — Item 30 DONE (manifest DISTILLED→EMBEDDED mechanism + dangling-claim guard)

- **`core/research/curate.py`** (new): `parse_frontmatter` (focused nested parser — the repo has
  NO yaml dep; the hook parser is flat-only), `set_embedded`/`mark_manifest_embedded` (surgical,
  comment-preserving rewrite of ONLY the `source_ingestion:` block), `schema_errors` (v0), and
  `ingestion_errors` — the **dangling-claim guard** (embedded ⟹ real store_ref/venue/retrieved AND,
  given the store, curated vectors actually present for that store_ref).
- **Item 30 = mechanism, not real-card flips (finding-0074, spec-fidelity).** Flipping a real seed
  card needs real vectors → a real fetch → Zone-C/curation-time (core never fetches, Inv 2). Offline
  build has none, so flipping a real card would BE the dangling-claim falsifier. Delivered the tested
  mechanism; real flips ride a live driver run (bp-028) + `mark_manifest_embedded`, gated by
  `ingestion_errors`. **finding-0074 resolved** (builder-routed).
- Test `tests/integration/test_curate_manifest.py` (6 passed): sample manifest parses + v0 schema;
  full 29→30 flip on a temp manifest is backed by real vectors + preserves every other block/body;
  dangling claim (store_ref not in store) caught; embedded-with-null-ref caught; not_fetched-with-ref
  caught; **all ≥10 REAL seed manifests pass the v0 schema, are non-dangling, and stay `not_fetched`
  (build flipped none)**.

**All four items (27∥28→29→30) DONE + green individually.** Next: full attestable-green gate (all
5 legs separately), then seal.

## 2026-07-13 — SEAL: bp-029 COMPLETE (the EMBED tail)

The transient→persisted flip is built: open-access full text (Europe PMC OA `fullTextXML`) →
chunk → embed → a SEPARATE curated store (`data/research_curated.lance`, gitignored) with
`provenance="curated"`, licence-gated default-DENY; plus the manifest DISTILLED→EMBEDDED mechanism
+ dangling-claim guard. All invariant-adjacent boundaries held **structurally**: Inv 2 (persist reads
already-fetched text, no core network), never-pollute-the-mirror (separate store + CURATED ∉
MIRROR_READABLE), Inv 11 (full text under `data/`, git-ignored), the licence gate (open_access AND
full_text, belt-and-suspenders).

**Green gate (all 5 legs, run SEPARATELY):**
- Leg 1: `ruff check .` clean; import-firewall OK (core imports no zone/network); pytest
  `-m 'not live and not podman and not needs_vault and not needs_restic'` → **1010 passed, 4 skipped**,
  20 deselected, no regressions (+20 new bp-029 tests: 3+5+5+6, +1 fetcher regression already existed).
- Leg 2: `mypy core agents eval ops scheduler scripts` → **0** (177 files, hard floor held); argless
  `mypy` → **69** (pinned tests baseline — one new bare-`dict` fixed to hold the pin); `type_gate` OK.
- Leg 3 (`needs_vault`): unaffected (no vault code touched) — CI/witness attests after push.
- Leg 4 semgrep report-only; Leg 5 release on push.

**Scope:** exactly write_scope + journal + findings. `cloud/fetcher/{sources,aggregate}.py`,
`config/{loader,defaults}`, `core/research/{criteria,persist,curate}.py`,
`core/stores/curated_store.py`, +4 `tests/integration/*`. NO out-of-scope files; base `VectorStore`,
`rank.py`, chunk/embed, `core/provenance.py`, scheduler/, the mirror store — all untouched.

**Findings filed:** 0072 (write_scope test-path gap — RESOLVED, owner-authorized scope fix; = 0071
class, /graduate check still owed), 0073 (arXiv PDF full-text deferred — codebase, not a blocker,
Europe PMC is the working OA tail), 0074 (Item-30 real-card flips are a live/curation-time act —
spec-fidelity, RESOLVED: mechanism delivered + tested, real flips ride a live driver run).

**Deferred to a live run (by design, Inv 2):** real seed cards stay `not_fetched`; the live airlock
+ a deployed Zone-C fetcher (bp-028) turns candidates → keepers → real full text → `store_ref`, at
which point `mark_manifest_embedded` (gated by `ingestion_errors`) flips real cards. Optional
owner-only `mind-palace deploy` activates the live airlock; absent a live fetcher the chain degrades
to `[]` (bp-028) and the curated store simply stays empty.

**Cost.actual:** self-driven opus/high, 4 items, one owner scope-gate + effort/budget gate; measured
non-cache-token delta recorded in the plan front-matter `cost.actual` (owner /usage relay at seal).
Self-driven code lands UNDER the delegated pad (bp-028 datum 0.54×) — this build ran lean (fakes,
no live tier, tight edits).
