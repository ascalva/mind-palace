# bp-036 journal

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
