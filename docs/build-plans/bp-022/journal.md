# bp-022 journal

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
