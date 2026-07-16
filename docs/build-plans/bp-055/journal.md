# bp-055 (certified-cuts) — builder journal

Builder contract. Writable: `core/temporal/spine.py`, `tests/unit/test_cuts.py`,
`tests/integrity/test_cut_soundness.py`, this journal, new `docs/findings/`.

## Status: COMPLETE (pending orchestrator's real-stores integrity leg on main)

## Worktree hygiene (done)
- `git merge --ff-only main` → already up to date (fresh off `b3e11ce`, waves 1+2 merged).
- Dep check PASS: `core/temporal/spine.py` has bp-053's `frontier`@545, `p`@608, `n_s`@678,
  `class Spine`@485. Dependency present.

## Design decisions (grounded)

### D1 — the spine CANNOT import `scheduler` (circular). Trough fact is INJECTED.
`scheduler/*` imports `core` widely (budget/cron/interface/router/supervisor/vault_sync). So
`core/temporal/spine.py` importing `scheduler.JobQueue` would be a cycle. Therefore the
trough-quiescence certificate takes the scheduler's OWN quiescence FACT as injected data
(`TroughState`, built by the caller from `scheduler.JobQueue.counts()`), never fabricated. This
honors "never fake a certificate — comes from the scheduler's own state": the caller passes the
real counts; a `None` trough or a non-quiescent one ⇒ REFUSAL.

### D2 — the scheduler DOES expose a readable quiescence fact → NO §10 parking.
`scheduler/queue.py` `JobQueue.counts()` / `depth()` / `list(RUNNING)` are a clean read of the
single-writer queue state. Quiescent ⇔ no QUEUED and no RUNNING jobs. So the §10 stop-and-raise
("no readable quiescence fact → park trough, file 0095") does NOT fire; all THREE certificates
ship. (0095 is instead used for D3 below.)

### D3 — stratum→certificate map (spec-fidelity resolution, finding-0095).
The note §2.4 names the three certificates and "a full cross-strata cut composes commit ∧
trough-empty ∧ handoff-empty" but under-specifies the exact per-stratum map. Resolved, grounded:
- `mirror` (versions/catalog = repo-backed corpus) → {COMMIT} (ratified `_CUT_CLOCKS`, scope.py:450).
- `ops` (runledger/attestations) + `interpreted` (edges/derived) → {TROUGH, HANDOFF}: core stores
  written by scheduler jobs that can incorporate in-flight edge observations; a cut across the
  core↔edge boundary needs both.
- `eval` → {TROUGH}: internal jobs, no edge dependency.
The FULL cut (all four strata) composes exactly {COMMIT, TROUGH, HANDOFF} — matches the note.
Filed finding-0095 (spec-fidelity, RESOLVED) for orchestrator/cross-strata-dreamer visibility.

### D4 — frontier is per-CHAIN (`"<store>:<chain-key>"`), not bare store.
The pin comment says "(store, position) pairs"; the correct str key is `Spine.frontier()`'s
`"<store>:<chain-key>"` (per-DOC for versions). Bare store would collapse per-doc chains and lose
soundness. `CertifiedCut.frontier = tuple(sorted(spine.frontier-over-strata))` honors the pinned
TYPE (`tuple[tuple[str,int],...]`) while keeping per-chain resolution.

### D5 — down-set is frontier-bounded (NOT auto-closed); crossing_edges is the non-vacuous tooth.
`downset` = {chained e : chain∈frontier ∧ pos≤frontier} ∪ {chain-less e : e ≼ some seed event}.
NOT closed over chained events — else `crossing_edges` (which checks down-closure) is vacuous.
An HONEST cut's frontier is already closed → `crossing_edges == []`. A CORRUPTED cut (a chain's
frontier moved past an event referencing a not-included cross-chain event) is NOT closed → the
crossing is found. Chain-less SOURCES (catalog) ride in as predecessors so a real full cut stays
clean; chain-less SINKS (eval) are correctly never pulled in.
Crossing test flags only edges whose EXCLUDED source is IN the cut's covered domain (its chain is
in the frontier) — an edge exiting the cut's strata is out-of-scope (§2.7 GC-N8), not a crossing.

## Done

### Item 1 — CertifiedCut + certificates + composition (spine.py + test_cuts.py) — CLOSED
Additive to spine.py (bp-053 code untouched): `Certificate` enum, `CutCertificateError`,
`TroughState`, `CutSources`, `CertifiedCut` (frozen/Hashable), `_STRATUM_CERTIFICATES`,
`_HANDOFF_SUBDIRS`, `Spine._cut_sources` field threaded through derive/finalize/restrict, and
`Spine.cut_at` / `_source_certificate` / `_handoff_listing`. `tests/unit/test_cuts.py` (17 tests):
composition per strata, all refusals (absent/non-quiescent/non-empty/unknown), evidence-from-
observable provenance, hashing + ride-in-`Scope.cut` (with a control proving the SLICE rule fires).
Falsifiers verified: a cut without its needed certificate REFUSES; the certificate carries its
observable (trough_id / commit SHA / handoff hash), never wall-time.

### Item 2 — the soundness tooth (spine.py + test_cut_soundness.py) — CLOSED (real-stores half deferred)
`Spine.downset` (frontier-bounded, chain-less-source-closed) + `Spine.crossing_edges` (the §2.4
falsifier, in-scope-only per §2.7). `tests/integrity/test_cut_soundness.py` (6 tests): honest cut
→ `crossing_edges == []`; CORRUPTED cut (frontier moved past a referenced event) → DETECTED
`("versions:docX:1","runledger:claim:1")`; out-of-scope edge is not a crossing; chain-less
SOURCE rides in / SINK excluded. Two real-stores legs run TRIVIALLY in this worktree (data/ absent)
— the ORCHESTRATOR runs them on main against the live corpus (the real crossing search). Falsifier
verified on fakes; the live falsifier is the orchestrator's leg.

## Gate (all 5 legs green, this worktree)
- ruff check . → All checks passed
- mypy core agents eval ops scheduler scripts → 0 errors (205 files)
- argless mypy → EXACTLY 69 errors (my test files added 0)
- ops.type_gate → OK
- pytest -q -m 'not live' → 1395 passed, 10 skipped, 9 deselected
- test_cuts.py → 17 passed; test_cut_soundness.py → 6 passed

## Findings filed
- finding-0095 (spec-fidelity, RESOLVED): the stratum→certificate map (D3) + the §10 trough
  contingency resolved without a park (the scheduler exposes `JobQueue.counts()`).

## No parked decisions. No design/math/direction findings (nothing to route to the orchestrator
## beyond the resolved spec-fidelity finding).
