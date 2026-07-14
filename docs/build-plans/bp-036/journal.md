# bp-036 journal

## 2026-07-14 — Items 13 + 14 COMPLETE + green; A/B measured (9→4); Item 15 gains a dream-wipe

**Status:** `in-progress`. Unblocked (owner corrected `write_scope` to bare paths, `aad2317`). Items 13
+ 14 built + green, offline. **A/B measured.** Item 15 (re-embed tool) is next and NOW also wipes the
id::-polluted dreams (owner-directed, this session) — pending the owner's scope call (post-mint-only vs
reset-all). No live store touched.

**Completed — Item 13 (the deterministic strip):**
- `core/ingest/logseq.py`: `strip_properties(text)` — removes every line the module's `_PROP` object
  matches (the SAME object `parse_text` uses → parse≡strip by construction), body preserved verbatim.
  Column-0 only (§10 verified: 0 indented block props in the corpus). 11 unit tests
  (`tests/unit/test_property_strip.py`): parse≡strip exactness, body byte-preservation (http://, `3::00`,
  links, code, unicode, indentation), idempotence, boundary shapes. Green.

**Completed — Item 14 (wire + invariants + the A/B):**
- `core/ingest/pipeline.py`: `derive_chunks` AND `ingest_note` now chunk `strip_properties(...)` — the
  ONE shared derivation, so `verify.py` re-derives the SAME body chunks (no false drop; the load-bearing
  constraint). Docstrings updated (§4 reconciliation).
- `tests/integration/test_body_only_embedding.py` (4 tests): body-only rows pass `verify_rows_against_raw`
  (0 dropped); digest = sha256(raw bytes) UNCHANGED; `doc_id`/`id::` resolves unchanged; links + titles
  survive. Regression: the ingest-adjacent suite = **143 passed** (verify consistency holds).
- **A/B MEASUREMENT (real embedder, current corpus, σ=0.62):** properties-in = **9** edges (matches the
  live polluted graph — validates the method); **body-only = 4** edges; **5 removed, 0 added**; centroid
  shift min 0.89 / mean 0.95. The property artifact is REMOVED. (4 not 5 = `date::` also stripped, as
  predicted §3 Q4.) The plan's stop-and-raise "A/B does not reduce the edges" did NOT trigger.
- Green (touched files): ruff clean; `mypy core agents eval ops scheduler scripts` = 0 (184 files).

**NEW REQUIREMENT (owner, this session) — wipe the id::-polluted dreams.** The post-mint dreams were
CLUSTERED on the polluted 9-edge graph, so their structure (not just their refs) is artifact-driven →
"practically useless." Earlier option-3 digest-remap does NOT fix this (clustering is wrong). Sequencing
constraint: the live daemon keeps regenerating polluted dreams each pass, so the wipe must be part of the
re-embed op — **deploy strip → re-embed body-only (daemon down) → wipe/reset dreams → daemon up →
regenerate clean.** Fold into Item 15. **Parked on the owner's scope decision:** wipe only post-mint
dreams, or reset ALL (recommended — the re-embed changes the graph for every note; even pre-mint dreams
are now on a stale graph).

**Next action:** on the owner's scope answer, build Item 15 — `scripts/reembed_bodyonly.py`: seal →
daemon-down gate → confirm-gated → backup vector store (+ derived store) → reset+rescan body-only →
wipe/reset dreams per scope → verify body-only + report the new edge count. Build-don't-run.

**Re-entry condition:** owner picks the dream-wipe scope (post-mint-only | reset-all).

**Context-manifest delta:** `core/ingest/verify.py` (`verify_rows_against_raw` API); `core/ingest/embed.py`
(`build_embedder` for the A/B). Findings: 0078 (resolved by the bare-path write_scope).

## 2026-07-14 — BUILD started (opus/high, offline-only); PARKED on owner-gated write_scope fix

**Status:** `in-progress`, `active-plan` set. Build is **offline-only** (owner rule: extensive tests +
the A/B before any live store; the re-embed is owner-run). **Currently PARKED** — the first code write
(`strip_properties` in `logseq.py`) was DENIED by scope-guard because bp-036's `write_scope` entries
carry inline `#` comments that the hook matches verbatim (a bare path never matches a commented entry).
Correcting `write_scope` is owner-gated (finding-0075). Nothing was written; the hook denied cleanly.

**Completed:**
- Build mechanics: `active-plan` → bp-036; status `ready → in-progress`; owner's `proposed → ready`
  blessing committed FIRST (`5f4f3b2`, rule 0060).
- **Item 13 step 1 — the §10 stop-and-raise inspection (read-only, DONE):** inspected all 13 live notes
  for indented block-level properties. **Result: 0 indented block properties** → no stop, no `_PROP`
  widening; the column-0 strip (== `_PROP`) is complete + exact for this corpus. Surfaced: **2 notes
  carry a `date::` property alongside `id::`** (note-2026-07-11-000843, -000928), so "strip ALL props"
  (owner's choice) removes `date::` too → the body-only graph may NOT land on the pre-mint 5 edges
  (which embedded `date::`). Item 14's A/B will MEASURE it; assert "id:: artifact removed," not a
  hardcoded 5 (matches plan §3 Q4).

**In-flight / blocked:**
- `strip_properties(text)` for `logseq.py` is designed (reuse the exact `_PROP` object; return
  `"\n".join(line for line in text.split("\n") if not _PROP.match(line))` — deterministic, idempotent,
  parse≡strip by construction). Write BLOCKED by scope-guard (above).
- Filed **finding-0078** (scope-guard matches write_scope verbatim; inline comments silently block writes;
  recommend the hook strip `# …` before matching).

**Next action (re-entry):** OWNER strips the inline `#` comments from bp-036 `write_scope` (bare paths;
same 5 files, no set change). Then: (1) add `strip_properties` to `core/ingest/logseq.py`; (2) write
`tests/unit/test_property_strip.py` (parse≡strip, body byte-preserved, idempotent, edge cases: `http://`,
`time 3::00`, `[[links]]`, code, unicode); (3) Item 14 — route `derive_chunks`+`ingest_note` through the
strip, prove `verify.py` passes + digests/`doc_id` unchanged, run the offline A/B on copies; (4) Item 15
— `scripts/reembed_bodyonly.py` (gated, build-don't-run). NO live store in the build.

**Re-entry condition:** bp-036 `write_scope` corrected to bare paths (owner-gated, finding-0075).

**Open questions:** none blocking beyond the write_scope correction.

**Context-manifest delta:** read beyond the manifest — `.claude/hooks/scope-guard.sh` (the verbatim-match
cause); inspected the 13 notes' property structure (Item 13 step 1). Findings filed: 0078.

## Markers
- 2026-07-14: park committed clean at `c748025` (journal + finding-0078 `dd3e5f5`; status flip `c748025`).
  Repo clean, pushed. Build resumes on the owner-gated `write_scope` bare-path correction (finding-0075).
