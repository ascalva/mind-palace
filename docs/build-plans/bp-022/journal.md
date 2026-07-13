# bp-022 journal

## 2026-07-12 — Item 5 closed (the THREAD lens) — all three items done, gate next

**Status line:** All three items (4, 6, 5) committed on
`worktree-agent-ac750d8bf5c2a3bd1`. Only the full plan gate (ruff + mypy ×2 +
type_gate + pytest, verbatim) remains before handing back to the orchestrator.

**Completed:**
- Item 5 — `thread_interpreter` + registration (commit `d0fedc0`).
  `core/dreaming/interpreters.py`: `THREAD = "thread"` constant; `thread_interpreter`
  follows §6(b) exactly — `harmonic_basis(kx.A)` for the basis/β₁, honest-seam
  short-circuit on `beta1 == 0` BEFORE any hole pairing (verified as the FIRST
  statement in the function body, matching the plan's pinned step order), then
  `long_lived_holes(ctx.distances, min_persistence=cfg.thread_min_persistence)`
  persistence-ranked (the function's own sort order, reused, not re-sorted), capped
  at `min(len(holes), beta1)`. Witness digests via `kx.nodes[v] for v in
  hole.vertices` (the corrected attribute name — see the earlier journal entry's
  note that the graduation note said `.witness`; the real field is `.vertices`).
  Flow: cycle edges = pairs of witness vertices present in `edge_index(kx.A)` (a
  non-edge pair inside a witness carries no harmonic-basis row and is excluded, not
  zero-padded); flow = max over harmonic columns of mean `|basis[edge_row, col]|`
  over those edges. Registered in `STRUCTURAL_INTERPRETERS[THREAD]`. Module
  docstring extended (§4's cross-ref).
  - **Acceptance test** (`tests/unit/test_thread_lens.py`, new file, 6 tests):
    planted 6-note ring at σ=0.3 (β₁=1, verified independently against
    `harmonic_basis` before writing assertions — exactly the 6 perimeter edges, no
    chords) yields exactly ONE THREAD claim, `support == the six witness digests`,
    `data["persistence"] == 1.0` (the hole's own lifetime), `data["witness"] ==
    list(support)`. A dense near-identical clique (β₁=0, asserted via
    `harmonic_basis(...).shape[1] == 0` before the interpreter call, so the
    falsifier fixture is verified, not assumed) yields ZERO claims —
    `test_thread_lens_yields_zero_claims_on_beta1_zero_even_with_holes_below_scale`.
    Support-subset-of-witness invariant checked directly. Determinism: two
    independently-built `StructuralContext`s over the same view yield identical
    claims. Routing-class check: no claim's statement contains "contradiction".
  - **Panel integration** (`tests/integration/test_structural_panel.py`, 3 new tests
    added to the existing 3, all 6 green): THREAD fires alongside `hole`/`theme`/
    `bridge` at σ=0.3 (ring edges intact, β₁=1) —
    `test_thread_lens_fires_alongside_existing_lenses_when_ring_edges_are_intact`.
    At the corpus DEFAULT σ=0.62 (where the ring has ZERO σ-edges, since 0.62 >
    every ring-pair's cosine similarity — checked by hand earlier), THREAD is
    silent while `hole` still fires (hole reads the unthresholded distance matrix,
    not the σ-skeleton) — `test_thread_lens_absent_at_default_sigma_where_ring_has_no_edges`
    — which ALSO is exactly why the three ORIGINAL panel tests (which run at
    default σ, unmodified) stay green: THREAD contributes nothing there, so nothing
    about their assertions changes. Whole-panel determinism re-checked with THREAD
    registered.
  - `uv run ruff check` on all three touched/new files → clean (one auto-fixed
    import-order nit in the new test file via `ruff check --fix`, no logic
    changed by the fix).
  - `uv run mypy core agents eval ops scheduler scripts` → Success, 169 files.
  - `uv run mypy` (argless) → **Found 69 errors in 20 files** (checked 337 source
    files — one more than the Item 6 checkpoint's 336, from the new
    `test_thread_lens.py`; the ERROR COUNT is unchanged from the pinned baseline).
  - `uv run pytest -q tests/unit/test_thread_lens.py
    tests/integration/test_structural_panel.py` → 12 passed (6 + 6).

**In-flight:** None — all three plan items are implemented, tested, and committed.
Next is the full verbatim gate from the builder brief (ruff + mypy×2 + type_gate +
pytest across the whole repo), which has NOT yet been run in full (only targeted
subsets so far, all green). The sibling builder bp-018 may be running a
live/podman-marked full-suite pass concurrently in its own worktree — per the
brief's flake note, `tests/e2e/test_scheduler_live.py::test_supervisor_dispatches_a_real_job`
may need a re-run if it comes back DONE+empty-text under contention.

**Next action:** Run the full gate verbatim:
```
uv run ruff check . \
  && uv run mypy core agents eval ops scheduler scripts \
  && uv run mypy \
  && uv run python -m ops.type_gate \
  && uv run pytest -q
```
Journal the tails (especially the argless-mypy "Found N errors" line — must stay
69) and the pytest summary counts. If the known e2e flake fires, re-run just that
one test before treating it as a real failure. Then write the FINISH report back
to the orchestrator per the builder brief's required shape; leave `status:
in-progress` (orchestrator's job to merge/seal).

**Open questions:** none new; nothing parked. No findings filed this session — no
codebase/spec-fidelity ambiguity was hit that needed resolving-and-annotating, and
no design/math/direction question arose that needed routing. (The one naming
correction — `Hole.witness` vs the real `.vertices` — was caught and self-corrected
against the actual code per Q3's own citation, not a spec defect: the design note
and plan both cite `topology.py:29-43` / the plan's own §6(b) pseudocode uses
"witness digests" only as a descriptive local-variable name, never asserting an
attribute called `.witness` exists. Only the PRIOR journal entry's prose overstated
it; corrected in-place there.)

**Context-manifest delta:** No files read beyond what the Item 6 entry already
listed, plus this item's own target files (already in write_scope). Confirmed via
scratch script (not written to the repo) that `edge_index` on the ring's adjacency
at σ=0.3 gives exactly the 6 perimeter pairs, and that summing `|basis[e, 0]|` over
those 6 rows gives a uniform 0.408 flow (as expected for a symmetric hexagon's
single harmonic mode) — sanity-checked before trusting the `flow` field's shape.

## 2026-07-12 — Item 6 closed (degree-1 temporal invariants)

**Status line:** Items 4 and 6 committed on this worktree branch
(`worktree-agent-ac750d8bf5c2a3bd1`). Only Item 5 (the THREAD lens) remains before
the full gate.

**Completed:**
- **Side-effect audit (pre-Item-6, per build-plan skill §7):** enumerated
  `core/complex/temporal.py`'s live side-effecting surface before writing any
  falsifier-demo test: `SnapshotStore.__post_init__` (mkdir + DDL on the real path),
  `.write` (INSERT), and `open_snapshot_store` (constructs a store pointed at the
  LIVE `data/derived.sqlite`-sibling file). All three are mocked/skipped by
  construction — every test uses a `tmp_path`-scoped `SnapshotStore(...)` directly;
  `open_snapshot_store()` is never called. The pre-existing-store-file heal test
  builds its OLD-schema fixture with a raw `duckdb.connect` + hand-written old DDL
  (no `dim_ker_l1`/`harmonic_persistence_total` columns), never by importing
  pre-change module code (there is none to import — same module, tested via a
  hand-built fixture file standing in for "before this plan").
- Item 6 — degree-1 invariants (commit `833172c`). `core/complex/temporal.py`:
  `StructuralSnapshot` gains `dim_ker_l1: int | None` and
  `harmonic_persistence_total: float | None` (additive, both default `None`).
  `compute_snapshot` gains a `thread_min_persistence: float = 0.15` keyword; computes
  `dim_ker_l1 = harmonic_basis(kx.A).shape[1]` (β₁ at σ, bp-021's kernel — the parked
  "snapshot β₁ source" decision, kernel not ripser) and
  `harmonic_persistence_total = sum(lifetime for holes >= thread_min_persistence)`,
  both gated on `distances is not None` (the exact `h1`-guard pattern, never
  fabricated). `SnapshotStore.__post_init__`'s DDL gains two `ALTER TABLE ... ADD
  COLUMN IF NOT EXISTS` statements (idempotent); `write`'s INSERT and
  `trajectory()`'s allowed-metric set both extended.
  - **Acceptance test** (`tests/unit/test_temporal.py`, 6 new tests, 10 total in file,
    all green): planted 6-note ring at σ=0.3 (verified by hand via a scratch script
    first — no chords, β₁=1 exactly, matching `harmonic_basis` independently of
    `long_lived_holes`) recovers `dim_ker_l1==1` and
    `harmonic_persistence_total==pytest.approx(1.0)` (the ring hole's own
    birth=0.5/death=1.5 lifetime) — determinism re-checked via a second call, byte
    (value) identical. `distances=None` degrades both new fields to `None`
    (`test_degree1_invariants_degrade_to_none_like_persistence_h1`). Degenerate n=0
    complex: honest `None`/`0`/`0.0` per the `distances` presence, no fabrication
    (`test_degree1_invariants_honest_on_degenerate_empty_complex`).
  - **The pre-existing-store-file heal**
    (`test_preexisting_store_file_heals_additively_on_open`): built a fixture file
    with the OLD 11-column DDL (hand-written, matching the file's pre-bp-022 schema
    verbatim) + one row, then opened it through the CURRENT `SnapshotStore` — old row
    reads back `None` for both new columns (not fabricated), old `persistence_h1`
    data intact, new row after the heal carries real values, and a second reopen is
    idempotent (no duplicate-column error). This is Item 6's "touches stored data?
    yes" dry-run proof (plan §7) — the live snapshot store is never touched by this
    session.
  - **`structural_axes()` byte-identical** (`test_structural_axes_byte_identical_to_before_bp022`):
    asserts the exact two-key dict is unchanged AND that varying the new fields
    (`None`→`None`, or large values) does not move the axes at all — the §3
    drift-contract risk, pinned by test as the plan requires.
  - `uv run ruff check` on all touched files: clean (two E501 line-length fixes
    applied along the way — comments shortened, no logic change).
  - `uv run mypy core agents eval ops scheduler scripts` → Success, 169 files.
  - `uv run mypy` (argless, the pinned tail) → **Found 69 errors in 20 files** —
    unchanged from the pre-session baseline; new test file does not shift it.
  - `uv run pytest -q tests/unit/test_temporal.py tests/unit/test_hodge.py` → 52
    passed (10 + 42, no cross-contamination from bp-021's hodge tests).
- Commits: `d513d76` (Item 4, config), `833172c` (Item 6, temporal). Both carry the
  Co-Authored-By trailer (substantially agent-authored code).

**In-flight:** Starting Item 5 — the `thread_interpreter` lens + registration.
Depends on Items 4 (done) and bp-021 (satisfied). This is the last item; after it,
the full plan gate runs.

**Next action:** Implement `core/dreaming/interpreters.py`'s `thread_interpreter`
per plan §6(b) exactly: `THREAD = "thread"` constant, honest-seam order (β₁==0 short-
circuits BEFORE hole pairing — this is the L-b falsifier's first clause), holes from
`long_lived_holes(ctx.distances, min_persistence=cfg.thread_min_persistence)`,
persistence-ranked, up to `min(len(holes), beta1)`, witness digests via
`ctx.complex.nodes[i] for i in hole.vertices` (NOTE: the field is `.vertices`, not
`.witness` — see the correction noted in the prior journal entry below), flow =
max over harmonic columns of mean |h[e]| on witness-cycle edges present in the
σ-skeleton (need `edge_index` from `hodge.py` to map witness-cycle node pairs to
harmonic-basis row indices — only pairs that are actual σ-edges count, per §6(b)'s
"present in the σ-skeleton" clause). Register in `STRUCTURAL_INTERPRETERS`. Then
`tests/unit/test_thread_lens.py` (planted β₁=1 ring → exactly one THREAD claim,
support == witness digests, persistence in data; filled/acyclic corpus β₁=0 → ZERO
claims even with holes below scale present — the L-b falsifier verbatim) and
`tests/integration/test_structural_panel.py` extension (THREAD claims alongside
existing lenses, all existing panel tests green unchanged, determinism: two runs
identical claims).

**Open questions:** none new.

**Context-manifest delta:** Confirmed via scratch script (not written to the repo —
Bash heredoc per the scope-guard note) that a 6-note ring at σ=0.3 gives exactly 6
edges (the hexagon perimeter, no chords) and β₁=1, independently cross-checked
against `long_lived_holes` on the same view's unthresholded distance matrix — birth
0.5/death 1.5/lifetime 1.0, matching `dim_ker_l1` exactly. This fixture is reused for
Item 5's THREAD-lens acceptance test (same ring, same σ).

## 2026-07-12 — builder session start + Item 4 closed

**Status line:** Builder contract active; plan flipped `ready → in-progress`;
`.claude/state/active-plan` = `bp-022`. Item 4 (config constant) done, gate green on
touched surfaces. Baseline `uv run mypy` (argless) reconfirmed at **Found 69 errors**
pre-change (matches the pinned baseline — my new test files must not shift it).

**Completed:**
- Item 4 — the config constant. `config/loader.py`: `DreamRnDConfig` gains
  `thread_min_persistence: float` (sibling of `hole_min_persistence`, same comment
  style), parsed via the same bare `rnd["thread_min_persistence"]` pattern as its
  sibling (§6(a) pin). `config/defaults.toml`: `thread_min_persistence = 0.15` added
  beside `hole_min_persistence` under `[dream_rnd]`.
  - **Acceptance test:** ran a scratch script (Bash heredoc, per the scope-guard note —
    scratch never goes through Write) confirming `load_config().dream_rnd.thread_min_persistence
    == 0.15` from defaults, AND that a minimal `local.toml` overlaying an unrelated
    section (`[secrets]`) does NOT crash the loader and still yields `0.15` — the
    house default-merge (`defaults ← levers.toml ← local.toml`, shallow per-section
    overlay in `_overlay`) means a `local.toml` missing this key inherits cleanly from
    `defaults.toml`. Falsifier avoided by construction: the bare-index parse only
    crashes if `defaults.toml` itself lacked the key, which it now doesn't.
  - `uv run pytest -q tests/ -k config` → 6 passed, 895 deselected.
  - `uv run mypy core agents eval ops scheduler scripts` → Success, no issues (169
    files) — the two touched files carry no new mypy surface.
  - No commit yet — will commit Item 4 + Item 6 together if Item 6 lands clean next
    (both touch config/temporal; separable if needed), OR standalone if Item 5 takes
    a while. (Superseded below if committed separately.)

**In-flight:** Starting Item 6 (temporal invariants) next per the plan's parallelizable
note (Item 4 ∥ Item 6-prep), then Item 5 (the THREAD lens), which depends on both.

**Next action:** Read `core/complex/temporal.py`'s existing `h1`/`distances=None` guard
pattern (already read in setup) and add `dim_ker_l1` / `harmonic_persistence_total`
fields to `StructuralSnapshot` + `compute_snapshot`, then the DuckDB on-open ALTER
in `SnapshotStore.__post_init__`, then extend `trajectory()`'s allowed-metric set.
Byte-identical `structural_axes()` output is enforced by a dedicated test (§3 risk).

**Open questions:** none new. Pre-existing note from graduation: journal's own text
said `Hole.witness`; the actual field (`core/complex/topology.py`) is `Hole.vertices`
— a naming slip in the graduation note, not a spec defect (the plan's §6(b) pseudocode
also says "witness digests" as a local variable name, which is fine — it's the
journal's earlier prose that overstated the attribute name). No finding needed; noted
here for the fresh-agent test so nobody greps for a nonexistent `.witness` attribute.

**Context-manifest delta:** Also read (beyond the manifest) `core/complex/build.py`
(`ReasoningComplex.nodes`/`idx`/`titles` — needed for Item 5's witness-digest mapping)
and `tests/unit/test_complex.py` (style precedent, confirmed). Read `tests/unit/test_hodge.py`
in full for the §6(f) harness — `dim_ker_l1_at_sigma` / `ripser_alive_h1_count` are the
reusable cross-check functions Item 6's acceptance test may want, though Item 6 needs
`compute_snapshot`'s kernel-at-σ approach specifically (harness is for cross-validation,
not the snapshot computation itself).

## 2026-07-12 — minted at graduation (orchestrator, Fable/xhigh)

Plan created `proposed` by /graduate over the ratified `dn-edge-dynamics` (Lane A,
L-b/L-c). Grounding verified in-session: registry-only wiring (`collect_claims`
iterates `STRUCTURAL_INTERPRETERS`; dreamer.py needs no edit — Q1); `Hole.witness`
carries the carrying cycle (Q3 — no new cycle extraction); DuckDB additive column heal
(Q4); the `structural_axes` drift contract identified as a consumed surface that must
NOT change (§3 risk — pinned by test in Item 6). Honest-seam order pinned: β₁ = 0
short-circuits before hole pairing. No code written. Awaiting the owner's
`proposed → ready` hand edit; depends on bp-021.

---

## 2026-07-12 — ORCHESTRATOR RECOVERY + SCRUTINY: builder died at the usage limit mid-gate; work complete, verdict PASS

**Status:** the builder completed all items (config `d513d76`, temporal `833172c`, THREAD
lens `d0fedc0`, journal checkpoints through "all items done, gate next") and died on the
org usage limit during its final gate re-run, before journaling tails or reporting.
Recovery per the bp-016 precedent: the orchestrator completes the tail in this worktree.

- **`git merge main` clean (`1405711`)** — main had moved 18a13cd→95d1d51 (finding-0051,
  release.yml node fix, **v1.4.0 release commit-back**, bp-018 merge+seal, bp-019 spawn
  amendments); zero overlap with this plan's diff.
- **Scrutiny (full diff 18a13cd..a67bf1a): PASS.** §6(a) config exactly additive (one
  TOML line, one dataclass field, one loader line); §6(b) lens: honest seam FIRST
  (β₁==0 returns [] before any hole pairing — the pinned order), support ⊆ witness by
  construction, gap-family routing (no contradiction vocabulary — pinned by test),
  claims capped at min(len(holes), β₁), flow over σ-skeleton edges among witness
  vertices (the implementable reading of the pin — Hole.vertices is an unordered set,
  consecutive-pair cycle edges are not recoverable; noted, not a deviation); §6(c)
  snapshot fields additive degrade-to-None, `structural_axes()` return byte-identical
  (the consumed drift contract — pinned by test_structural_axes_byte_identical_to_
  before_bp022); §6(d) DuckDB ADD COLUMN IF NOT EXISTS heal, idempotent, trajectory
  allow-list extended. Scope: 9 files, all in write_scope; plan.md diff = status flip
  only. Falsifier coverage verified by test-name sweep (L-b both clauses, L-c, honest
  degradation, panel determinism). No findings.
- **Gate re-run (orchestrator, post-merge):** IN FLIGHT (background b5agraijk; the
  builder's own first full run had one live-flake re-run in progress when it died —
  the class is catalogued, 0046/0048).

**Next action:** on gate green — merge to main (sequenced after bp-019's warnings-fix
addendum lands or independently, one merge at a time), push, witness `check`, seal
(cost.actual: sonnet ~210,223 tok / 155 calls / ~36 min = 0.84× of 250k).

**Gate CLOSED (orchestrator, 2026-07-12):** full five-part gate on this worktree
post-main-merge: ruff clean · mypy scoped clean (170 files) · **argless mypy = 69 =
baseline** (340 files) · type_gate OK · pytest **926 passed / 8 skipped / 0 failed**
(611 s, uncontended — zero flakes). Folding main again (bp-019 + its seal landed
mid-gate; disjoint scopes), then merging to main; final combined-tree gate runs on main.
