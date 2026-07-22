# bp-093 journal

## 2026-07-21 — minted (graduation, session-41)

Graduated from ratified dn-code-ingest-pipeline (0c2deae; fable-audited, finding-0147)
per §3. Status: proposed — awaiting the owner's proposed→ready hand-bless. No work
performed. Grounding computed at graduation is recorded in the plan's §3.

## 2026-07-22 — build session (delegated builder, worktree agent-a6f60af7)

**Step 0 — bind + sync.** `active-plan` = bp-093 (verified). `git merge --no-edit main` merged
bp-092/CI-1 cleanly (no conflict): `core/ingest/code_corpus.py` present, log shows
`seal(bp-092): CI-1 complete`. Stayed inside the worktree throughout.

**Grounding (whole-file reads).** Plan §0–§12, journal, ratified note dn-code-ingest-pipeline
(§2.1/§2.1b/§2.2/§2.3/§2.8/§3), bp-092's journal (seed parked, layer column live), and the read
surfaces: `core/ingest/index.py` (`semantic_search`, MIRROR_READABLE default, grouped search),
`core/ingest/code_corpus.py` (the three-layer lane + `CodeCorpusSync`), `core/stores/vectorstore.py`
(the `layer`/`qualname`/`line_*` columns, `all_rows`/`search` provenance filters, the Python-side
posture), `core/kernel/provenance.py` (`Provenance.CODE` ∉ MIRROR_READABLE), `tests/fixtures/
{embedding,fakes}.py` (the deterministic fake embedders), `eval/harness/{store,__init__}.py` +
`tests/integrity/test_eval_isolation.py` (the firewall: seeds are only `eval.harness.{store,
registry,__init__}`, so a new harness module importing a core read path is fine iff none of those
three import it — respected).

**PD-J is PULLED (§0 / §11).** The node-keyed `code_origin` authorship reader is out (owner ruling,
warrant finding-0151 — the integrator track owns it). No `core/**` written; this plan is read-only,
eval-side.

### Item 1 — the golden probes + M-C3/M-C4/M-C5 harness — DONE (readings park where they must)

**`eval/code_probes.py` — the golden probe fixture.** 15 "find the code that does X" probes, each a
natural-language query pinned to a known-answer HEAD path (`CodeProbe(probe_id, query,
answer_paths)`), over confirmed-present main-package + eval paths (never a test file, never
`eval/golden/**` — the frozen owner denylist). `probe_set_hash()` content-addresses the set (order-
independent) so a reading records exactly which fixture produced it (the CN-1 index). A test asserts
every answer path exists on disk, so a rename that orphans a probe fails the suite rather than
silently degrading a future reading.

**`eval/harness/code_retrieval.py` — the M-C3/M-C4/M-C5 battery (read-only).**
- **M-C3** (`run_mc3`): per probe, the rank of the known-answer path in the **code lane** (all three
  layers) vs the **docstring-only baseline** (the `codedoc`/L1 layer alone) — same k, same embedder,
  the honest comparator the note names (§3 Q2). `ranked_paths` pulls a flat pool via an EXPLICIT
  `provenances={CODE}` search (NEVER the MIRROR_READABLE default — §7), filters to the layer set in
  Python, dedups by source path at its best hit. Verdict `LANE_BEATS_BASELINE` iff lane_wins >
  baseline_wins AND zero catastrophic regressions (a probe the baseline finds in top-k but the lane
  misses entirely); else `NO_SIGNAL` (F-CI3 — a null is a result, the plan still seals). MRR + a
  per-probe journal table fall out.
- **M-C4** (`run_mc4`): the code↔note cross-space geometry. Samples ≤N code vectors
  (`provenances={CODE}`) and ≤N note vectors (`provenances=MIRROR_READABLE`) deterministically,
  compares the cross-class cosine distribution to the pooled within-class one via a histogram-overlap
  coefficient, and verdicts `INFORMATIVE` iff the overlap clears a threshold (the cross mass is not
  bimodally pushed to orthogonality) else `DEGENERATE` (F-CI4). Gates CI-4 (bp-095) + PD-C.
- **M-C5** (`run_mc5`): times a CODE-filtered `all_rows` full scan + one `search` — the Python-side-
  filter posture (`vectorstore.py`) at scale. Embedder-independent (row count + vector payload), so a
  synthetic-scale store measures it faithfully.
- **`ReadingIndex`** (CN-1): the reproducibility index recorded beside every reading — embedder pin,
  corpus ref, seed, k, pool, layer partition, probe-set hash.

**Tests.** `tests/unit/test_code_retrieval.py` (11) — probe fixture well-formed + every answer path
on disk + hash stability; M-C3 lane-beats-baseline on a controlled ordering (answer's terms in CODE,
decoy's in the DOCSTRING → lane ranks answer #1, docstring-only baseline ranks the decoy above it) +
the NO_SIGNAL path (lane==baseline layers ⇒ all ties) + reproducibility; M-C4 INFORMATIVE (classes
share the space) vs DEGENERATE (orthogonal subspaces, cross_median<0.05); M-C5 mechanics. `tests/
integration/test_code_mirror.py` (4) — the firewall CONSUMER check: over a mixed note+code store the
MIRROR_READABLE default still surfaces zero code, `ranked_paths` (lane AND baseline) returns only
code paths (never a note leak), and M-C4 reads each class through its own explicit provenance set.
All 15 green with the deterministic fake embedders (no Ollama).

### M-C3 / M-C4 REAL verdicts — PARKED (re-entry: the owner-visible seed run)

M-C3 and M-C4 need REAL qwen3 embeddings of the REAL seeded corpus to yield a real verdict; bp-092
parked the seed run (no Ollama / live store in a worktree). So the **numeric verdicts park** with the
seed run — the harness + probes + verdict logic are BUILT and unit-green; only the live numbers wait.
Re-entry: after the owner runs the CI-1 seed at an idle window, run `run_mc3(embedder, store)` and
`run_mc4(store)` and record the verdicts (they gate CI-4/PD-C). A degenerate M-C4 is a FINDING with
the embedder-bump re-entry (PD-C), never a silent tune (§3 / §10).

### M-C5 REAL reading — RECORDED (synthetic-scale, embedder-independent — not faked)

M-C5 depends only on row count + vector payload, so a synthetic store at the TRUE dim (2560) measures
the posture faithfully. One-off run this session, 7,000 CODE rows × dim 2560 random vectors, real
LanceDB + real `VectorStore`:

    seed(build, 7000x2560) = 0.9s
    all_rows (CODE-filtered full Arrow scan + Python filter) = 2.9–3.1s
    search (one nearest-neighbour over CODE)                 = 16–33 ms
    verdict: VIABLE (both under the 5s ceiling)

**Reading:** the search path stays cheap (LanceDB native, ~tens of ms) at ~7k; the cost center is the
full-scan `all_rows` Python materialization (~3s for 7k×2560). `CodeCorpusSync.sync()` calls
`all_rows(provenances={CODE})` once per sync, so at ~3s that is fine for a BACKGROUND housekeeping
task but is the scaling watch-item as the corpus grows past this order. Posture VIABLE at the seeded
~7k scale (the note's estimate); no defect ⇒ recorded as the M-C5 verdict, not a finding.

### The full attestable-green gate (this worktree)

- `uv run ruff check .` → **All checks passed!**
- `uv run mypy core agents eval ops scheduler scripts` → **Success: no issues found in 254 source files**
- `uv run mypy` (argless) tail → **Found 69 errors in 20 files (checked 530 source files)** — == baseline 69 ✓
- `uv run python -m ops.type_gate` → Tier-2 membership OK; bare-ignore scan OK
- `uv run pytest -q -m 'not live and not podman and not needs_vault and not needs_restic' --deselect
  'tests/unit/test_core_self_containment.py::test_core_imports_nothing_outside_core' --cov` →
  **1895 passed, 11 skipped, 21 deselected, 1140 warnings in 67.29s** (bp-092 was 1880 passed; +15 new
  CI-2 tests, all green — no red).
- (repo floor) `uv run python scripts/check_imports.py` → Import firewall (I2): OK. `eval.harness.
  code_retrieval` imports `core.ingest.index`, but the eval-isolation firewall seeds only
  `eval.harness.{store,registry,__init__}` and none import the new module — `test_eval_isolation`
  green.

## Follow-through

- **Built?** Yes — Item 1 complete: `eval/code_probes.py` (15-probe golden fixture, HEAD-path-pinned,
  content-addressed, NOT in `eval/golden/**`), `eval/harness/code_retrieval.py` (the M-C3/M-C4/M-C5
  battery + the CN-1 `ReadingIndex`, read-only, no store writes), and 15 tests (`tests/unit/
  test_code_retrieval.py` ×11, `tests/integration/test_code_mirror.py` ×4), all green with the
  deterministic fake embedders. M-C5's real reading RECORDED (synthetic 7k×2560, embedder-independent).
- **Wired/delivered (or why dormant)?** The battery is a callable eval-side reader; it writes nothing
  and mints nothing. It is exercised in tests today; the REAL M-C3/M-C4 verdicts DORMANT-BY-DESIGN
  until the owner-visible CI-1 seed run exists (bp-092 parked the seed — no Ollama/live store in a
  worktree). No daemon change.
- **Does a consumer use it?** CI-4 (bp-095) reads THIS plan's journal M-C4 verdict as its signal gate;
  PD-C (embedder re-entry) reads M-C3/M-C4. Both are PARKED pending the live seed — re-entry: run
  `run_mc3(embedder, store)` + `run_mc4(store)` on the seeded store, record verdicts, then bp-095's
  gate reads them. M-C5 posture reading is delivered now (VIABLE at ~7k).
- **Track state (code-ingest)?** CI-1 (bp-092) sealed. CI-2's proof MACHINERY complete + green; its
  M-C3/M-C4 NUMERIC verdicts park with the CI-1 seed run (the deskcheck's natural subject). M-C5
  recorded VIABLE. PD-J stayed PULLED (§0). CI-3 (bp-094, L2b + AST edges) and CI-4 (bp-095, S↔F lens,
  conditional on M-C4 signal) remain future plans.
- **Opened a new track/finding?** No finding filed. No spec-defect: every pinned interface (§6) matched
  the landed code (semantic_search provenance filter, the `layer` column, `Provenance.CODE` ∉
  MIRROR_READABLE). M-C5's ~3s `all_rows` full-scan cost is recorded as a scaling watch-item in the
  journal, not a defect (posture VIABLE at the seeded scale).

**Ready to deskcheck** — bp-093/CI-2 (the retrieval/geometry/scale proof). DONE ≠ sealed: the live
M-C3/M-C4 verdicts over the real seeded qwen3 corpus are the deskcheck's natural subject (run them at
the owner-visible CI-1 seed idle window). Status left `ready` for the orchestrator to seal.
