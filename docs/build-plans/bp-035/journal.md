# bp-035 journal

## 2026-07-14 — authored `proposed` (orchestrator, graduation of dn-core-query-protocol)

Graduated from ratified `dn-core-query-protocol` §2.3 (the reference agent — "the archetype, and the
first build") + §3 Consequence 2. Owner directed the graduation in-session ("loop back to using ouroboros
itself to identify references"); tier ruled **opus/high, no fable** — the math/design is banked in the
ratified notes, and §2.3 is deliberately the simplest client (no model, no firewall composition).

**Why this is the first plan (not §3.1's doc→doc extractor):** the note's §3 named the doc→doc extractor
as the recommended first graduation, but grounding (Explore sweep, 2026-07-14) found it **already built**
— `ops/code_sensor.py:427` (`_corpus_to_corpus_edges`) mints doc→doc edges (front-matter + inline +
wikilink); the store holds ~272k edges incl. ~73k corpus_to_corpus. So the real gap is the READ surface:
the graph is fed but **agent-unreachable** (`all(target_ref=…)` has zero callers). This plan closes that.

**Grounding done at graduation (§3):** the store's read API (`reference_edges.py:282,312`), the per-commit
identity (`:118-120,142`) → the "current commit" anchor question (Q1, pinned to the run ledger's active
commit / HEAD, parked with the union-across-history alternative rejected); fibers `F` = the reference
store is citation-only, so `E={F}` is free (Q2); zero-reader confirmation (Q3); connected_set = bounded
BFS (Q4); the §2.6 grep-not-store oracle discipline (Q5).

**Reconciliation (§4) → OWED FINDING:** the ratified note's frontmatter ("61k edges … code-anchored") and
§3.1 (extractor as first plan) are STALE — the extractor shipped via the sensor post-snapshot. File a
`spec-fidelity` finding recording this (the note is immutable A8; the finding is the channel; orchestrator
batches the erratum to the owner). This plan edits the note nowhere.

**Scope (§5):** new `core/reference_view.py` + two test files. Store/extractor/`core/temporal` all
untouched (reused/separate). Three items ordered by blast radius: read window → connected_set → grep
oracle. Model estimate opus/250k (deterministic read surface + a differential oracle; the falsifiers are
runnable, not judgment calls).

**Downstream graduations this note still licenses** (recorded in plan §12, NOT authored here): the
build-time repo-derived twin (§2.4), the general capability-scope type system (§2.1 — the fable-grade
piece), wiring `core/temporal` into a query answer, the alignment instrument + diachronic interpreter.

Awaiting the owner-only `proposed → ready` blessing. No work started.

## 2026-07-15 — builder session (in-progress): Items 1 & 2 green

Set active-plan pointer, flipped `status: ready → in-progress`. Grounding read in full:
`reference_edges.py` (the substrate + `all(source_ref=/target_ref=)`), `ops_view.py` (the
bind-the-readers pattern mirrored exactly), `runs.py` (`RunLedger.last()` + `git_state` — note
`git_state` lives in `runs.py`, launcher only re-imports it, so the factory imports from `runs`
to stay light), `launcher.py`, and the existing `tests/unit/test_reference_edges.py` for fixture
idiom.

**Item 1 + 2 built** — `core/reference_view.py`:
- `ReferenceView` frozen dataclass; `.over(store, *, commit)` binds two closures
  (`edges_to`/`edges_from`) that call `store.all(target_ref=/source_ref=)` and drop any row whose
  `commit_sha != commit` (the stale-union bug is structurally excluded — §3 Q1).
- `references_to` / `references_from` / `connected_set(ref, *, depth=1)` — BFS over
  `references_to ∪ references_from`, `visited`-guarded (cycle-safe), self-excluded (§11 pinned
  default), `depth`-bounded, `depth≤0`→∅.
- `open_reference_view(config=None, *, commit=None)` factory: anchor default = `RunLedger.last()
  .commit_sha` else `git_state(REPO_ROOT)` HEAD.
- Read-only: public surface is exactly `{references_to, references_from, connected_set, commit,
  over}` — no `add_batch`/`_conn`/`close` reachable (asserted).

**Unit tests** — `tests/unit/test_reference_view.py`, **17 passed**. Covers: anchor-filtering
(both directions), no-mutator surface, code+corpus endpoints, factory anchor resolution (active
run / HEAD fallback / explicit), and connected_set (self-exclusion, both-directions, cycle
termination, depth-bounding, depth-0, unknown-ref, anchor-respecting).

**Store facts probed** (main repo store, 100MB, worktree data dir is EMPTY): ~272k edges, ~75k
corpus_to_corpus, 469 distinct commits; the worktree HEAD `5168b42` has 994 edges projected —
so the store IS projected at HEAD. The worktree's own `data/` has no store, so the Item 3 oracle
must skip gracefully when the live store is absent/unprojected (measured against the main store
for the reported number).

Next: Item 3 oracle.

## 2026-07-15 — Item 3 oracle green + owed finding filed

**Item 3 built** — `tests/integration/test_reference_oracle.py`: the §2.6 repo-grep differential
oracle. INDEPENDENT grep (regexes reimplemented in the test, NOT imported from `code_sensor` —
§2.6 discipline 1) of each doc's outbound citations (full `docs/….md` paths + backtick `.py` +
resolved bare `finding-NNNN`/`dn-slug` prose), diffed against `references_from(doc)` via the
built VIEW (not raw SQL). PRINTS the fidelity block; asserts FLOORS, never equality.

**Skip guard:** opens the live store, checks `for_commit(HEAD)` — if 0 edges (store absent/not
projected at this checkout's HEAD, as in a fresh worktree) → `pytest.skip` (environmental). In
the main checkout where the daemon projects, it MEASURES. Verified BOTH paths:
- skip path (empty worktree store): `1 skipped`.
- measure path (temporarily symlinked the main 100MB store into `data/` — gitignored, removed
  after): `1 passed`.

**Measured fidelity @ worktree HEAD `5168b42`, 994 edges at anchor, 78 docs with citations:**
- doc→doc recall (full-path surface): **227/228 = 0.996**
- doc→doc recall (expanded, +bare finding-/dn- prose): 228/299 = 0.763 (the residual precision-
  gating gap — bare-id prose mentions the sensor doesn't mint)
- doc→doc precision (grep-confirmable): 228/230 = 0.991
- doc→code(.py) recall: 373/373 = 1.000
- **Reconciliation:** the note's stale hand-demo was doc→doc recall **0/16 = 0.000** at the 61k
  snapshot → now **0.996** full-path. Night-and-day; the extractor shipped via the sensor.
- Floors asserted: doc-recall ≥ 0.90, py-recall ≥ 0.90, precision ≥ 0.85, expanded > 0.5, and
  full-path ≥ expanded (precision-gating). Floors well below measured (NOT equality — §7 Item 3
  falsifier). The one full-path gap: `finding-0034.md` 1/2.

**Owed finding filed** — `docs/findings/finding-0081.md` (ftype `spec-defect`, route
`orchestrator`): the note's frontmatter ("61k edges … code-anchored") + §3.1 (doc→doc extractor
as first plan) are stale — the extractor shipped via `code_sensor` post-snapshot; the real first
gap was the read surface (this plan). Note is immutable A8 → owner-gated amendment; parks no
bp-035 criterion. Orchestrator batches to owner.

Next: the 5-leg attestable-green gate.

## 2026-07-15 — attestable-green + committed

All three items complete; the 5-leg gate run SEPARATELY, each read:
1. `ruff check .` → **All checks passed!** (after fixing 7×E501 + 1 unused import in the new files).
2. `mypy core agents eval ops scheduler scripts` → **Success: no issues found in 185 source files**.
3. argless `mypy` → **Found 69 errors in 20 files (checked 375 source files)** — exactly the
   pinned tests/-baseline; my two new test files did NOT shift it (finding-0029 footprint intact).
4. `python -m ops.type_gate` → **Tier-2 membership OK / Bare-ignore scan OK**.
5. `pytest -q` → **1123 passed, 9 skipped in 1023.55s** — zero failures, no live-test flakes; the
   oracle test is among the 9 skips (correct: no store projected in this worktree's empty data/).
   (Ran ~17min because a concurrent second `pytest` was sharing the box.)

Committed on the worktree branch: **1585150** `feat(bp-035): ReferenceView …`. NOT merged, NOT
pushed, NO blessing flip — the orchestrator reviews the diff, re-runs the gate (where the oracle
MEASURES, not skips, against the projected main store), and merges + flips `in-progress →
complete`.

Note: `docs/findings/finding-0081.md` transiently vanished while untracked (a concurrent process
cleaned the worktree); recreated identically and committed — it is now tracked and safe.

**Reported fidelity (Item 3, measured via a temporary symlink of the main 100MB store into the
worktree data/, removed after): doc→doc full-path recall 227/228 = 0.996** — the note's stale
hand-demo was 0/16 = 0.000. Expanded surface (bare finding-/dn- prose) 0.763 = the residual
precision-gating gap; precision 0.991; doc→code recall 1.000.
