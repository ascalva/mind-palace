# Journal — bp-085 (G-A)

**Status:** proposed (awaiting owner `proposed → ready` blessing, by hand).
**Design ref:** `docs/design-notes/fiber-geometry.md`.

## Graduation — 2026-07-21 (session-40)

Minted `proposed` by `/graduate` over the three ratified notes (`fbea48d`). Decomposition and
grounding done in a single orchestrator context (subagent-assisted decomposition parked, §14);
seams/instruments re-verified on disk at HEAD `d08da37`. No implementation performed —
graduation implements nothing (A4). The plan's §3 carries the grounding citations; §6 pins the
interfaces verbatim so a fresh builder infers no design.

Next: owner blesses `proposed → ready` by hand, then `/build bp-085` in a fresh (delegated)
session.

## Build session — 2026-07-21 (delegated builder, worktree)

Plan is `ready`; entered as delegated builder. Worktree branch predated the bp-085 commit, so
merged `main` (fast-forward-ish, 2 commits) to bring the plan + journal + design note into the
worktree at HEAD `d08da37`. All named instruments verified present on disk.

**Grounding / data reconnaissance (read-only over `/Users/ascalva/mind-palace/data/`):**
- Embedder is reachable (`build_embedder()` → 2560-dim vectors) → **S rows are computable** by
  embedding the dialogue-artifact docs eval-side (the re_measure pattern), no daemon write.
- **Store populations (live, this HEAD):**
  - C (`causal_edges.sqlite`, kind='C', dst_type='doc'): 1062 doc rows over **237 distinct doc
    endpoints** → C is NOT empty at this HEAD (a *result*: the bp-080-seal "live census empty"
    reading has moved — the co-production doc-pair population is now non-trivial).
  - F (`reference_edges.sqlite`, corpus→corpus): 293,721 rows → dense citation fabric.
  - D (`versions.sqlite`): 19 doc_ids, 34 versions, 13 with >1 version (→ ~15 supersession
    arcs); `authored_supersessions.sqlite`: 1 row.
- **KEY STRUCTURAL FACT (drives M1):** the three recorded classes index **different node
  spaces**. C endpoints are artifact-ids (`bp-000`, `finding-XXXX`, `agent-taxonomy.md`) →
  resolve to `docs/**` paths. F corpus→corpus is already `docs/**` repo-relative paths. D
  `versions.doc_id` is vault janus_note paths + catalog UUIDs — a **disjoint** corpus from the
  docs/ dialogue-artifacts. So S/F/C share the docs/ node space (normalize C via
  `resolve_doc_path`), while D sits over a disjoint population. Near-zero D-vs-{S,F,C} overlap
  is therefore a measured fact, and it is exactly PD-a re-entry cond. 1 (support non-degenerate)
  evidence — pointing to PARK, not build.

**CN-1 index for an eval-side read-only survey:** the σ*/connectivity family's live certified
cut is a Spine op over the mirror stratum (not buildable read-only over dialogue-artifacts from
a worktree). The survey therefore pins its recoverable corpus coordinate as (git HEAD, σ-grid,
node-space label, n_nodes, a content digest over the exact node set + edge multiset measured).
Every reading carries this index or it is malformed (the battery's own falsifier).

Next: build `eval/harness/fiber_survey.py` (loaders + M1–M8 + CN-1 index), run it live, write
`finding-0142`, add the smoke/honesty test, run the full gate.

## Build complete — 2026-07-21 (delegated builder)

**Built (write_scope only):**
- `eval/harness/fiber_survey.py` — the read-only survey: `?mode=ro` loaders (reusing
  `re_measure`'s `open_causal_edges_ro`/`proven_pairs_from_causal`/`embed_docs`/`resolve_doc_path`
  — NOT the RW `VersionStore`/`ReferenceEdgeStore`, which mkdir/write), path-space normalization
  (S/F/C → docs/**; D disjoint), M1–M8 each emitting a CN-1-indexed `Reading`, a D-triangle
  stop-and-raise, and a `main()` JSON emitter. Imports the built instruments UNCHANGED.
- `tests/unit/test_fiber_survey.py` — 9 smoke/honesty tests: runs on a fixture with no store/no
  embedder; every reading carries its CN-1 index + grid; D-integrity fires on a planted triangle;
  the embedder-deferral path defers S rows while F/D/C still measure. All green.
- `docs/findings/finding-0142.md` — the survey record (math/direction → orchestrator).

**Live run result (HEAD 42123068, grid (0.55,0.65,0.75)) — see finding-0142 for the full table:**
- **Recorded classes measured.** C: 237 nodes / 1193 edges; F: 207 / 593 (deduped from 293,721
  commit-keyed rows); D: 19 docs / 28 digest-nodes / 16 arcs (disjoint vault/catalog space).
- **F∩C = 126 shared nodes (Jaccard 0.40); C|D = F|D = 0 (D disjoint — measured fact).**
- **M3 D_triangles = 0** → covering-only integrity CLEAN; stop-and-raise did NOT fire. C=3976, F=583.
- **M6** D-thermometer measured; per-region χ_s instrument-blocked (needs a live Spine).

**§10 stop-and-raise (recorded, handled by design, NOT a plan defect):** the **S (computed) class
is DEFERRED** — eval-side embedding times out at the 120 s fail-fast limit because the embed model
shares the memory-ceiling'd ollama (bright line 8) with the live daemon (both `qwen3.5:9b` and
`qwen3-embedding:4b` resident). The survey must not evict/restart the daemon, so it degrades
gracefully: S rows (M2/M4/M5/M8 + S columns of M1/M3/M7) defer with a re-entry condition (re-run
with embed headroom); F/D/C rows compute. This is a null-as-result, not a silent zero.

**Direction flag surfaced:** the note's "C live census empty at bp-080 seal" (§2.0/§2.5) has MOVED
— C is a populated fiber at this HEAD (1193 edges). Flagged in finding-0142 for /triage (no
ratified-text edit — A8).

**Gate:** ruff clean; check_imports OK; mypy targeted + argless (69 baseline) + type_gate OK;
test_fiber_survey 9/9 green. Full-suite baseline compared (known-red ratchets unchanged; no new
failures — I touch no core imports). Committing on the worktree branch; orchestrator sequences the
merge. Did NOT flip plan status; did NOT touch the denylist.
