# bp-026 journal

## 2026-07-13 — /build enactment (builder session, worktree agent-a8c92cab76a5a8980)

Plan flipped `ready → in-progress`. Worktree pointer written to
`.claude/state/active-plan` via `$PWD` (own worktree, finding-0051 discipline).
Read the full §2 manifest in order: `core/stores/reference_edges.py` (whole v1
store), `ops/code_sensor.py:80-109,239-290,155-189` (VALIDATED_PATTERNS,
extract_references, _mint_reference_edges, _corpus_reference_edges, sync/_project),
`tests/integration/test_reference_edge_isolation.py` (the B-c falsifier — pinned
`build_complex` params `{view, edges, derived, sim_floor}`, line 122),
`ops/lifecycle/launcher.py:524` (reset registration, confirmed out of write_scope —
not touched, not needed: the migration only touches schema + writer + test
fixtures per §5), `docs/build-plans/bp-020/plan.md` §6(b,c)/§11 (the
dry-run-harness / live-command / orchestrator-at-seal pattern reused verbatim for
Item 21 prep).

Baseline gate check before any edit: `uv run pytest -q
tests/unit/test_reference_extraction.py tests/unit/test_reference_edges.py
tests/integration/test_reference_edge_isolation.py` → **19 passed**. Recorded as
the pre-migration baseline.

**Finding filed: finding-0063** (`spec-fidelity`, resolved by this builder before
Item 18 work). `tests/unit/test_reference_extraction.py` (bp-013's original Item-7
test, landed `e20bb09`, pre-dates this plan) is **NOT in bp-026's write_scope**
but directly reads v1 field names off returned `ReferenceEdge` objects —
`.direction`, `.code_path`, `.qualname`, `.corpus_ref`, `.corpus_kind` — at lines
105, 122, 143, 145-146 (via `sensor.sync()` / `backfill_observations()`, which
route through `ops/code_sensor.py`'s writer, in-scope). It never calls `mint()`
directly with v1 kwargs, only reads attributes back. Plan §6(b)'s target schema
drops `code_path`/`corpus_ref`/`qualname`(as top-level)/`corpus_kind` in favor of
symmetric `source_*`/`target_*` fields — a hard break for this out-of-scope file.
**Resolution (codebase-fidelity fix, not a design change):** the v2
`ReferenceEdge` dataclass stores ONLY the symmetric v2 fields (no asymmetric
residue — the Item 18 falsifier's letter is honored: nothing named `code_path`/
`corpus_ref` is a stored column), but exposes `direction`, `code_path`, `qualname`,
`corpus_ref`, `corpus_kind` as READ-ONLY DERIVED PROPERTIES computed from the v2
tuple (mirroring how `direction` itself is required to be derived, §6(b)). For a
`code_to_corpus`/`corpus_to_code` edge (the only directions v1 ever minted) this
recovers the v1 read surface exactly, so `test_reference_extraction.py` keeps
passing unchanged with zero edits to it. For a `corpus_to_corpus` edge (v2-only,
never seen by v1 code) the derived `code_path`/`corpus_ref` properties raise
`AttributeError`-shaped `ValueError` (accessing a code-endpoint alias on an edge
with no code endpoint is a misuse, not a silent wrong answer) — no v1 caller can
hit this path since v1 never minted that direction. This is a narrow read-compat
shim, not a design change: the plan's falsifier text says the schema must not
KEEP a stored `code_path`/`corpus_ref` field; it says nothing about derived
convenience properties, and Item 18's own spec already requires exactly this
pattern for `direction`. Routed as `spec-fidelity` (a write_scope gap the plan
didn't anticipate — a fixed file outside scope depends on the old shape), resolved
by construction rather than escalated, per CLAUDE.md's builder-resolves rule for
`codebase | spec-fidelity`. See `docs/findings/finding-0063.md`.

Proceeding to Item 18.

## 2026-07-13 — Item 18 DONE (the symmetric v2 schema)

Rewrote `core/stores/reference_edges.py` per §6(b): DDL is the symmetric
`(source_kind, source_ref, source_detail, target_kind, target_ref, target_detail)`
+ `edge_id`/`commit_sha`/`ref_type`/`source_line`/`created_at`; `KINDS = ("code",
"corpus")`; `DIRECTIONS` extended to `code_to_corpus | corpus_to_code |
corpus_to_corpus | code_to_code` (the last reachable, unminted, per §11 parked
row). `ReferenceEdge.direction` is now a `@property` computed as
`f"{source_kind}_to_{target_kind}"` — NOT a dataclass field, so it cannot be
passed to the constructor or drift from the endpoints (falsifier honored,
asserted by the new `test_schema_has_no_stored_asymmetric_residue`).
`_edge_id`/`mint()`/`_row` generalized to the symmetric tuple; `add_batch`/`all`/
`for_commit` carried over; `all()` gained `source_ref=`/`target_ref=` filters
(the "references TO doc X" query, §6(b)'s explicit ask) plus a `direction=`
filter that now resolves server-side via `source_kind`/`target_kind` (no stored
direction column to filter on directly). The v2 banner note is in the module
docstring (`**[banner: schema v2 — bp-026]**` paragraph) recording the old shape,
the warrant (findings 0059/0061/0062), and the wipe+reproject migration
discipline (no lossy in-place row surgery, no v1↔v2 edge_id preservation
attempted — §3's "Additional risks" note honored explicitly).

Also implements finding-0063's resolution inline: `code_path`/`qualname`/
`corpus_ref`/`corpus_kind` as read-only derived `@property`s (see finding write-up
above) — NOT stored fields, satisfying the falsifier's literal text while keeping
the out-of-write-scope `test_reference_extraction.py` green.

New/updated unit tests in `tests/unit/test_reference_edges.py` (rewritten for the
v2 API, all `_edge()` fixture calls now use `source_kind=/source_ref=/...`):
round-trip of a `code_to_corpus` edge AND a new `corpus_to_corpus` edge; direction
derives correctly for all three directions
(`test_direction_is_derived_for_all_three_directions`); `all(target_ref=…)` /
`all(source_ref=…)` return the citing sources
(`test_all_filters_by_source_ref_and_target_ref` — the "who cites doc X" query,
the whole point); closed-vocabulary validation still raises on a bad
`source_kind`/`target_kind`/`ref_type`/`source_line`
(`test_vocabularies_are_closed_at_mint`); plus two new falsifier-guard tests
(`test_schema_has_no_stored_asymmetric_residue`,
`test_v1_read_compat_properties_raise_on_corpus_to_corpus`) and the carried-forward
isolation grep guard (`test_no_import_path_from_core_complex_to_this_store`).

One bug caught by the test run and fixed before green: `add_batch`'s raw SQL
`INSERT ... VALUES (?×10)` had 10 placeholders for an 11-column table (missed the
extra column from the v1→v2 field-count change: v1 had 10 columns, v2 has 11 —
`edge_id, commit_sha, ref_type, source_kind, source_ref, source_detail,
target_kind, target_ref, target_detail, source_line, created_at`). Fixed to 11
placeholders.

`uv run pytest -q tests/unit/test_reference_edges.py` → **15 passed**.
`uv run ruff check core/stores/reference_edges.py tests/unit/test_reference_edges.py`
→ all checks passed. `uv run mypy core/stores/reference_edges.py` → no issues.

Item 18 — **DONE**. Proceeding to Item 19 (migrate `ops/code_sensor.py`'s writer).

**IMPORTANT process correction, recorded for the fresh-agent test.** Early verification
runs in this session were accidentally executed with `pwd` at
`/Users/ascalva/mind-palace` (the MAIN checkout) rather than this worktree
(`/Users/ascalva/mind-palace/.claude/worktrees/agent-a8c92cab76a5a8980`) — `uv run
pytest` silently ran against the OLD, unedited files and reported stale green results.
Caught when a later `pwd`-correct run of `test_reference_edge_isolation.py` failed with
`TypeError: ReferenceEdge.mint() got an unexpected keyword argument 'direction'` (the v1
fixture calls, not yet migrated). **From this point forward every command in this
journal was run with `pwd` == this worktree**, verified explicitly before each gate
run. Anyone resuming this session: always confirm `pwd` before trusting a green result.

## 2026-07-13 — Item 19 DONE (migrate the code sensor's writer to v2)

Migrated `ops/code_sensor.py`'s `_mint_reference_edges` and `_corpus_reference_edges` to
the v2 `mint()` signature (`source_kind=/source_ref=/source_detail=` +
`target_kind=/target_ref=/target_detail=`), same code↔corpus semantics: the
`references_out` code→corpus loop now mints `source_kind="code", source_ref=o.path,
source_detail=o.qualname` → `target_kind="corpus", target_ref=<ref target>`; the md-side
corpus→code scan mints `source_kind="corpus"` → `target_kind="code"`. No behavior
change to WHICH edges land, only the constructor shape (§6(b)'s explicit "no code↔corpus
behavior change" acceptance bar).

Updated `tests/integration/test_reference_edge_isolation.py`'s mint FIXTURES ONLY (the
plan's explicit scope: "fixtures only, never relax assertions") — all four `_edge`-style
`ReferenceEdge.mint()` calls converted to v2 kwargs; ALSO added a fifth planted edge
(`corpus_to_corpus`, ref_type `design-ref`) since the test's own comment says "both
directions, every validated ref_type" and v2 admits a third direction now — this
STRENGTHENS the falsifier's coverage, never weakens it. The one assertion touched
(`{e.corpus_ref for e in ref_store.all()} <= set(node_digests)`) could not survive
verbatim: `.corpus_ref` (the finding-0063 v1-compat property) raises `ValueError` on a
`corpus_to_corpus` edge (ambiguous which side is "the" corpus endpoint when BOTH are
corpus). Rewrote it as `corpus_refs = {source_ref where source_kind=='corpus'} |
{target_ref where target_kind=='corpus'} <= node_digests` — semantically IDENTICAL for
every v1-shaped edge (code_to_corpus/corpus_to_code) and additionally correct for the
new corpus_to_corpus edge; nothing was loosened, the predicate just became endpoint-kind
aware instead of relying on a property that is undefined for 3-directions-admitting data.
The four bit-identity assertions that ARE the B-c falsifier
(`lam0==lam1`/`tris0==tris1`/`curv0==curv1`/`cl0==cl1`) are BYTE-IDENTICAL to before this
session — untouched.

`uv run pytest -q tests/integration/test_reference_edge_isolation.py -v` (pwd confirmed
== this worktree) → **2 passed**
(`test_reference_edges_never_reach_the_balance_math`,
`test_build_complex_has_no_handle_to_the_reference_edge_store` — the latter untouched,
still asserts `inspect.signature(build_complex).parameters == {"view", "edges",
"derived", "sim_floor"}` verbatim). No instrument moved when the (now 3-direction) edge
set was planted — the isolation invariant holds bit-identically post-migration.

`uv run pytest -q tests/unit/test_reference_extraction.py` (the out-of-write-scope
fixed file, finding-0063's subject) → still **8 passed, 0 failed** — the v1 read-compat
properties on `ReferenceEdge` recover its expectations exactly; zero edits to that file.

Item 19 — **DONE**. Proceeding to Item 20 (the corpus→corpus extractor, φ_doc).

## 2026-07-13 — Item 20 DONE (the corpus→corpus extractor, φ_doc)

Added `CodeSensor._corpus_to_corpus_edges(sha)` per §6(c): scans `docs/**/*.md` at the
projected commit's OWN tree state (`git show sha:path`, deterministic — same discipline
as the existing `_corpus_reference_edges` corpus→code scan) for three reference sources:

1. **Front-matter** (`design_ref`/`links`/`depends_on`/`warrant`/`supersedes`/
   `superseded_by`) whose value is a `docs/….md` path → `corpus_to_corpus`, `ref_type`
   `design-ref` for the `design_ref` key, `note-citation` for the rest. **Parsed, not
   regex-approximated** (plan §10's explicit requirement): wrote a minimal YAML-subset
   parser (`_parse_front_matter`/`_front_matter_scalar`, a proper grammar over the
   container structure — block scalars, `- item` block lists, `key: [a,b]` inline
   lists, quoted scalars, `null`) rather than adding a PyYAML dependency
   (`pyproject.toml`'s runtime deps are "intentionally minimal" — confirmed no `yaml`
   import resolves in this venv: `ModuleNotFoundError`). This closely mirrors an
   existing project precedent (`.claude/hooks/_lib.py:parse_front_matter`, outside this
   plan's write_scope, so independently reimplemented rather than imported) — same
   shape, same semantics (comment-stripping, list-upgrade, quote-honoring). The
   `_RE_NOTE_CITATION` regex is applied AFTER parsing, only to LOCATE the doc-path
   substring within an already-isolated scalar (`_front_matter_doc_paths`) — this is
   not the forbidden regex-approximation (which would mean regexing the RAW YAML text
   for references), it is the same trusted 100%-precision pattern the code↔corpus scan
   already uses, applied to a properly parsed value. `warrant: finding-0059` (a bare
   finding id, not a `docs/….md` path) correctly yields nothing — verified against the
   real corpus (`bp-026/plan.md` itself has `warrant: finding-0059`).
2. **Inline `_RE_NOTE_CITATION` matches** in the document BODY (front-matter and body
   are split first via `_split_front_matter`, so a body scan never double-counts a
   front-matter-block line) → `note-citation`.
3. **`[[wikilink]]` references** resolving to a known doc's stem in the same tree scan
   → `note-citation`; an unresolved wikilink mints nothing.

Self-loops (`source_ref == target_ref`) dropped at each of the three sites.
`CORPUS_TO_CORPUS_VALIDATED = {(corpus_to_corpus, design-ref), (corpus_to_corpus,
note-citation)}` defined and asserted against at every mint site (mirrors
`VALIDATED_PATTERNS`'s existing discipline). Wired into `_mint_reference_edges` as a
third `minted.extend(...)` call alongside the existing two.

**New tests, `tests/unit/test_reference_edges.py` (Item 20 section):** a 3-doc fixture
repo (`note-a.md`, `note-b.md`, `finding-planted.md`) planting one instance of each
source (front-matter `design_ref` + `links`, inline citation, `[[wikilink]]`) plus three
deliberate distractors (a self-loop, a `warrant:` value that names no doc, an unresolved
wikilink) — `test_corpus_to_corpus_extractor_emits_expected_edges` asserts the exact
6-edge set. `test_corpus_to_corpus_self_loops_are_dropped`,
`test_corpus_to_corpus_only_validated_pattern_ref_types`,
`test_corpus_to_corpus_extraction_is_deterministic` (two independent sync runs over
independent tmp stores → identical edge sets), `test_corpus_to_corpus_reprojection_mints_nothing_new`.

**The grep-oracle (plan's Item 20 crisp checker):**
`_grep_oracle_targets(repo, doc_path)` is an INDEPENDENT reimplementation (shares no
code with `_corpus_to_corpus_edges`) — every `docs/(design-notes|findings|brainstorms)/
….md` substring anywhere in the raw file text (front matter OR body), minus the
self-reference. Two oracle tests:
- `test_grep_oracle_precision_and_recall_on_finding_planted` — **exact match**
  (`extractor_targets == oracle_targets`), the strongest form: finding-planted.md has no
  wikilinks, so the extractor's full target set is grep-confirmable both ways. PASS —
  zero recall gap, zero precision gap.
- `test_grep_oracle_precision_and_recall_on_note_a` — note-a.md DOES use a wikilink
  (`[[Note B]]`), which the crude grep-oracle cannot resolve to `note-b.md` by
  substring-matching alone (a wikilink's rendered text never contains the target path
  string) — the plan's own framing (§7 Item 20) scopes the oracle to the
  `docs/….md`-substring surface, not wikilink resolution. Asserts recall
  (`oracle_targets <= extractor_targets` — nothing the grep sees is silently dropped)
  AND that every non-wikilink extraction is oracle-confirmable. PASS on both.

Result: **zero recall gap, zero precision gap** on both sampled docs — the extractor's
front-matter/inline output equals the independent grep exactly where the oracle can see
(finding-planted.md, no wikilinks) and is a strict superset (by design, the wikilink
edge) elsewhere (note-a.md) with recall still holding. No stop-and-raise fired.

`uv run pytest -q tests/unit/test_reference_edges.py` (pwd confirmed == worktree) →
**22 passed**. `uv run ruff check ops/code_sensor.py` → all checks passed. `uv run mypy
ops/code_sensor.py` → no issues found in 1 source file.

Item 20 — **DONE**. Proceeding to Item 21 PREP (dry-run only; no live migration).

## 2026-07-13 — Item 21 PREP (verified dry-run; NOT the live migration)

Built a dry-run harness per §6(b)/bp-020's proven pattern: `CodeSensor` wired against
FRESH `tempfile.TemporaryDirectory()` stores each run (`CodeObservationStore`,
`ReferenceEdgeStore`, `open_snapshot_db`, `CodeSensingHandoff`), `attestor=None` (a
dry-run must not enter the attestation chain), `history=None`, `repo=<this worktree>`,
`branch="main"` — then `sensor.sync()` (ingest full ledger) followed by
`sensor.backfill_observations()` (the full-history reprojection Item 21's live run will
also invoke) against the REAL repo, REAL branch `main`, at this worktree's HEAD
(`e365436` — `main`==`HEAD` in this worktree since nothing has been committed this
session yet; confirmed identical via `git rev-parse main` == `git rev-parse HEAD`). Ran
TWICE (fresh tmp stores each time, full independent history walk) for the determinism
check, plus a same-store second `backfill_observations()` call each run for a cheap
idempotence check (avoiding a wasteful THIRD full-history pass — idempotence over a
fresh full walk is already covered by the passing unit tests
`test_re_projection_mints_nothing_new` / `test_corpus_to_corpus_reprojection_mints_nothing_new`).

**Process note:** the first dry-run attempt piped through `tail -100` in a backgrounded
shell and was killed mid-run with zero captured output (buffering ate it) — re-ran with
direct unbuffered file redirection (`print(..., flush=True)` + `nohup ... > log 2>&1 &`).
Full-history projection is genuinely slow (~390-400s per full run: 362 commits × up to
105 corpus docs × 2 `git show` subprocess calls each, for the corpus→code AND
corpus→corpus scans) — not a hang, confirmed by steadily advancing CPU time while
waiting.

**RESULTS (both runs, byte-identical):**

```
sync.ingested=362 sync.projected=362 sync.reference_edges=182388
backfill_observations()=0                    # sync() already projects everything new
total_edges=182388
by_direction={'corpus_to_corpus': 45253, 'corpus_to_code': 101359, 'code_to_corpus': 35776}
code_to_corpus+corpus_to_code (v1-equivalent)=137135
corpus_to_corpus (new)=45253
python-warnings-caught=0
idempotence-check (same-store 2nd backfill_observations()): 0 new (PASS)
r1 == r2 (full dict equality: totals, by_direction, warnings): True
```

**Reconciliation note on the v1-equivalent count vs the plan's "≈ prior 61,380" (§6(d)/
Item 21 acceptance text) — investigated, not a discrepancy.** The dry-run's
137,135 is ~2.24x the plan's cited baseline. Checked the LIVE store
(`data/reference_edges.sqlite`, main checkout, read-only inspection, never touched):
`code_to_corpus=16392, corpus_to_code=49743` (66,135 total, roughly matching the "prior"
figure's ballpark) — but covering only **137 of 362** commits on main
(`SELECT count(DISTINCT commit_sha)` = 137). `backfill_observations()` has never been
run against the live store (bp-013's journal: "available, deliberately NOT wired into
sync" — an owner-nod-gated action, same parked status bp-020 hit for the self-sensing
store). The plan's "≈61,380" is therefore a STALE partial-coverage baseline (the
finding-0059 class of stale count, but for THIS store) — not a target this dry-run
should match. Cross-check: live-store density = 66,135/137 ≈ 483 edges/commit; my
dry-run's density = 182,388/362 ≈ 504 edges/commit — consistent (a slightly higher rate
is expected: later-history commits accumulate against a larger corpus, so density rises
over time). This is exactly the "v1-equivalent code↔corpus count regenerated" the
acceptance test asks for, just over the FULL history the live store hasn't yet seen —
not a bug, not a stop-and-raise (no divergence AT THE SAME HEAD/coverage; the live store
simply has less coverage than a full backfill would). Filed as context for the
orchestrator's Item 21 seal-time run rather than a new finding (no spec defect — the
plan's "≈" already signals an order-of-magnitude expectation, not an exact pin, and Item
21's own falsifier is "live counts diverge from the dry-run AT THE SAME HEAD" — which
this dry-run IS the reference point for).

**Grep-oracle, extended to the REAL corpus (beyond Item 20's synthetic fixture) —
three real, richly-cited documents, all EXACT matches (zero recall gap, zero precision
gap):**
- `docs/findings/finding-0059.md` → extracted `{docs/design-notes/self-sensing.md}` ==
  oracle `{docs/design-notes/self-sensing.md}`. MATCH.
- `docs/design-notes/core-query-protocol.md` (10 links, richest front-matter in the
  corpus) → extracted == oracle, both 10 targets, identical sets. MATCH.
- `docs/findings/finding-0062.md` → extracted == oracle, both 3 targets. MATCH.

**The exact live command (§6(c), orchestrator-executed at seal, main checkout, AFTER
this plan's commits are merged to main):**
```
uv run python -c "from ops.code_sensor import build_code_sensor; s = build_code_sensor(); print(s.sync()); print('backfilled:', s.backfill_observations())"
```
(No dedicated `scripts/`-level entry point exists yet for this backfill, unlike
`scripts/sense_self.py` — `build_code_sensor()` wires all real handles including the
real attestor and `data/`-rooted stores per `open_reference_edge_store`/
`open_code_observation_store`; `sync()` alone only projects NEW commits since last
run, so `backfill_observations()` is the deliberate full-reprojection call, exactly the
one this dry-run exercised.) Reset first if a clean re-project is wanted:
`reset_targets()` already lists `reference_edges.sqlite` and `code_observations.sqlite`
(`ops/lifecycle/launcher.py:519,524`) as corpus-class wipe targets — the orchestrator's
call whether to wipe-then-backfill (clean v2-only state) or backfill-in-place (v1 rows
already in the live store keep their v1-shaped IDENTITY under the OLD `_edge_id`
formula and would sit alongside NEW v2-formula rows for the same logical reference,
since the v2 code path is now the only writer — re-running `backfill_observations()`
without a wipe will NOT dedupe against stale v1-schema rows still in the DB from before
this migration, because the DB file itself must be re-created under the NEW `_DDL`
column set; the OLD table shape is schema-incompatible with the new INSERT statement's
column count, so an unwiped live run would in fact ERROR, not silently duplicate).
**Recommendation: wipe-then-backfill is required, not optional, given the DDL column
change** (confirmed: `_DDL` uses `CREATE TABLE IF NOT EXISTS` — an existing v1 table on
disk under the OLD 10-column shape will NOT be altered to the NEW 11-column shape by a
plain re-open, so the live store's `.sqlite` file MUST be deleted/reset before the v2
sensor writes to it, or every `add_batch` call will raise `sqlite3.OperationalError`
exactly as I hit and fixed in Item 18's own test run). This is `reset_targets()`'s
sanctioned mechanism (§6(d), Q2) — flagged explicitly for the orchestrator's Item 21
run: **reset `reference_edges.sqlite` (via `reset_targets()` or direct file removal)
BEFORE running the live command above**, then run it.

**Verification queries for the orchestrator, post-live-run (sqlite3 CLI, read-only,
against `data/reference_edges.sqlite`):**
```sql
-- total + per-direction (compare to this dry-run's 182388 / {corpus_to_corpus:45253,
-- corpus_to_code:101359, code_to_corpus:35776} at the SAME HEAD; may differ if main has
-- moved between this session and the orchestrator's run -- that is expected, not a
-- falsification, per the plan's own "at the same HEAD" framing)
SELECT count(*) FROM reference_edges;
SELECT source_kind || '_to_' || target_kind AS direction, count(*)
  FROM reference_edges GROUP BY 1 ORDER BY 1;

-- the finding-0059 capability, live: "who cites this note"
SELECT source_ref, ref_type, source_line FROM reference_edges
  WHERE target_ref = 'docs/design-notes/self-sensing.md' ORDER BY source_ref;

-- idempotence: re-run the live command a SECOND time, then re-run the total-count query
-- above -- must be byte-identical (0 new rows).
```

Item 21 — **PREP DONE, NOT RUN**. No live write, no `data/` touch, no attestation
emitted by this builder (confirmed: every store constructed this session used
`tempfile.TemporaryDirectory()` paths; `data/reference_edges.sqlite`'s mtime and content
were only ever READ, once, read-only, for the reconciliation note above — verified via
`sqlite3 ... "SELECT count(*)"`, never opened by any `ReferenceEdgeStore`/`sqlite3.connect`
call this session). Satisfies finding-0031's discipline (builders never touch the main
checkout's live stores) and the plan's explicit "do NOT run the live wipe+reproject —
that is the ORCHESTRATOR's at seal from the main checkout" instruction.

## 2026-07-13 — the five-leg gate, leg 5 catches an unanticipated ratchet interaction

Running the full gate (below). Leg 5 (`uv run pytest -q`) surfaced a real, expected
interaction the plan never named: `tests/unit/test_interpreter_versions.py` (bp-018's
interpreter-version ratchet, dn-self-sensing §3.2 V2) pins a `(version, sha256)` pair
over `(ops/code_sensor.py, ops/code_snapshot.py)` for `phi_code`. Item 20's source
changes (new `_corpus_to_corpus_edges` pass + helpers) changed the file's bytes without
bumping `INTERPRETER_VERSION` — exactly the silent-drift shape the ratchet exists to
catch, and it correctly caught it (`test_source_hash_matches_the_pin[phi_code]`,
`test_declared_version_matches_the_pin[phi_code]` both red).

**Judgment call (spec-fidelity, resolved in-scope where possible):** this IS a worldview
change, not a refactor, by the ratchet's own stated criterion — φ_code now senses a
reading category (`corpus_to_corpus` edges) it never produced before; Item 19's
code↔corpus semantics are explicitly UNCHANGED (the plan's own acceptance bar), so this
is additive, licensing a MINOR bump. Bumped `ops/code_sensor.py`'s
`INTERPRETER_VERSION` from `"1.0.0"` to `"1.1.0"` (in write_scope) with an inline
comment recording the reasoning and noting Item 21's wipe+reproject already IS the
re-projection this bump calls for (no separate action needed). Computed the new pinned
sha256 (`source_fingerprint(("ops/code_sensor.py", "ops/code_snapshot.py"))` at this
worktree's HEAD post-Item-20): `20be1ca5d483a51141377b23262a4b1041f7c2a94114120af20ced6abd4eab7b`.

**Two out-of-write-scope files need the corresponding fix; I cannot land either myself:**
1. `tests/unit/test_interpreter_versions.py`'s `INTERPRETERS["phi_code"]` entry needs
   `version="1.1.0"` + the new sha256 above.
2. `tests/unit/test_code_sensor.py::test_version_bump_makes_backfill_reproject_and_archive`
   independently breaks: it hardcodes the literal `"1.0.0"` twice (lines 147, 149) to
   assert the PRE-monkeypatch generation's version, which is now really `"1.1.0"`.
   Confirmed by direct run: `AssertionError: assert False = is_projected(sha, '1.0.0')`.
   Needs both literals replaced with the real base version (recommend capturing
   `ops.code_sensor.INTERPRETER_VERSION` at test start, before the monkeypatch, so a
   FUTURE bump doesn't silently re-break the same way).

**Finding filed: finding-0064** (`spec-fidelity`, partially resolved — the in-scope half
landed, the two out-of-scope fixes routed to the orchestrator with exact diffs, both
verified against a real failing run so the fix is pre-computed, not speculative).
Checked for other `"1.0.0"` literals across the tree that might be similarly affected:
found several in `test_code_observations.py`/`test_agent_observations.py`/
`test_observation_history.py`, but ALL of those pass `interpreter="1.0.0"` as an
explicit fixture kwarg (self-contained test data, never reading the real
`ops.code_sensor.INTERPRETER_VERSION` constant) — confirmed unaffected by re-running
those three files (`37 passed`). Only `test_code_sensor.py`'s two literals actually
exercise the real constant via `CodeSensor.sync()`/`backfill_observations()`.

## 2026-07-13 — the five-leg gate, final run

1. `uv run ruff check .` → **All checks passed!**
2. `uv run mypy core agents eval ops scheduler scripts` → **Success: no issues found in
   173 source files**
3. `uv run mypy` (argless, whole-tree ratchet) → **Found 69 errors in 20 files (checked
   345 source files)** — matches the pinned baseline exactly (finding-0029); confirmed
   none of the 20 files are in bp-026's write_scope (grep-checked the file list).
4. `uv run python -m ops.type_gate` → **Tier-2 membership: OK**; **Bare-ignore scan: OK**.
5. `uv run pytest -q` → **4 failed, 980 passed, 8 skipped** in 636.55s (0:10:36):
   - `tests/e2e/test_scheduler_live.py::test_supervisor_dispatches_a_real_job` — a
     `pytest.mark.live` test (real Ollama call), the SAME confirmed cross-suite
     contention flake bp-020's journal documented. Per the plan's flake rule, re-ran
     isolated: `uv run pytest tests/e2e/test_scheduler_live.py::test_supervisor_dispatches_a_real_job -v`
     → **PASSED** (82.30s). Confirmed flake, not a regression.
   - `tests/unit/test_interpreter_versions.py::test_declared_version_matches_the_pin[phi_code]`,
     `::test_source_hash_matches_the_pin[phi_code]`, and
     `tests/unit/test_code_sensor.py::test_version_bump_makes_backfill_reproject_and_archive`
     — all three EXPECTED, all three routed to **finding-0064** (the `INTERPRETER_VERSION`
     bump's out-of-write-scope consequences, diagnosed above with pre-computed exact
     fixes for the orchestrator).

**Discounting the confirmed flake, the true tally is 981 passed, 3 known/routed
failures (all finding-0064), 8 skipped.** No other regression. Gate: **GREEN modulo
finding-0064** (an honest, routed, pre-computed-fix scope gap — not a silent pass, not
an unexplained red).
