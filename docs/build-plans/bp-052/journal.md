# bp-052 journal — the velocity measurement pair (RotationReport + alive/stale)

## 2026-07-16 — builder session START (delegated, worktree `agent-a96c5ec76b8c85de3`)

Branch `worktree-agent-a96c5ec76b8c85de3`. Read in full: CONSTITUTION, CLAUDE.md, CONVENTIONS,
plan.md, the ratified `dn-velocity-instruments` (§2.1–§2.2, §2.4), `core/temporal_view.py`,
`core/temporal/complex.py`, `core/complex/hodge.py`, and `temporal-retrieval-algebra` §2.5 (A7).

**Frame settled from grounding:**
- (a) RotationReport lives in `core/temporal_view.py`, mirroring `CoherenceReport`'s two-anchor
  shape: `_restrict`-to-common (already module-level here), then `harmonic_basis(A_cite)` from
  `core/complex/hodge` on each restricted complex. Key geometry decision: both restricted complexes
  share the SAME node ordering (`_restrict` sorts common nodes identically), so their harmonic
  bases are keyed by comparable integer edge pairs. Principal angles come from the SVD of
  `Qaᵀ Qb` where each basis is zero-embedded into the UNION edge space (over common nodes). Zeros
  preserve orthonormality ⇒ singular values are cos θ_i. Identical snapshots ⇒ same restricted
  complex ⇒ `Qa == Qb` (harmonic_basis is deterministic) ⇒ `QaᵀQb = I` ⇒ all angles 0. β₁=0 at
  either anchor ⇒ empty report, angles `()`, reason recorded (honest seam).
- (b) `core/velocity_view.py` is a thin PURE-FUNCTION module (non-goal §9: no store surface, no
  model, no spine). It takes two `WeightedBackbone`s (anchor + interpreter_version + node-aligned
  weighted `A`) as DATA — the production consumer (DD-1) assembles them from `build.py`'s
  `cosine_adjacency`; wiring is out of scope. `Δw = w_b − w_a` on the COMMON edges (X1: birth/death
  are separate axes), decomposed with `hodge.hodge_decompose` over the common-restriction structural
  backbone (v1 is combinatorial ⇒ the projectors key on structure, not weights). A7 guard:
  interpreter_version mismatch across the window ⇒ empty report, reason recorded, emit nothing.
- Both `Inv` (no clock division). Both read-only, deterministic, model-free. Consume `hodge.py` +
  `temporal/complex.py` PUBLIC surface only; never touch `core/complex/**` (isolation invariant).

**Substrate confirmed:** `hodge.harmonic_basis(A)` returns `(n_edges, β₁)` orthonormal (deterministic
dense SVD null space); `hodge.hodge_decompose(c, A)` returns `HodgeParts(gradient, curl, harmonic)`,
mutually orthogonal, keyed on `edge_index(A)` (structure only, weight-independent). `edge_index` row
order == the sorted `(i,j)` upper-triangle == `_restrict`'s `.edges` order. mypy baseline (argless) =
**69** before any change; `scipy-stubs` installed so sparse ops are typed — mirror hodge.py patterns.

**Scope reminder:** plan.md is NOT in my write_scope (status flip is the orchestrator's job). My four
write surfaces + this journal + findings only.

Next: Item 1 (RotationReport) → Item 2 (alive/stale) → green gate.

## 2026-07-16 — Item 1 COMPLETE (RotationReport) — `test_rotation_report.py` green (6 passed)

Extended `core/temporal_view.py`: `RotationReport` (pinned §6 shape), the module-level
`_principal_angles` helper (union-edge-space zero-embedding + `Qaᵀ Qb` SVD), `TemporalView.rotation_to`
(mirrors `coherence_to`: `_restrict`-to-common → `harmonic_basis` on each), and `open_rotation`
(mirrors `open_coherence`). Import added: `edge_index, harmonic_basis` from `core.complex.hodge`
(the safe direction — `temporal/complex.py` already imports hodge; `core/complex` never imports back).

Falsifier clauses proven as tests: identical snapshots ⇒ angles ≈0 (< 1e-6); β₁=0 at either/both
anchors ⇒ empty report, `principal_angles == ()`, reason recorded; reported angles == independent
`scipy.linalg.subspace_angles` on the same embedded bases (atol 1e-9, genuine nonzero rotation on the
twisted-square pair); determinism run-to-run (byte-identical tuples); partial node overlap restricts to
common (n_common counts the intersection only). No store used in tests — `TemporalView(_complex=…)`
constructed directly over hand-built `CitationComplex` fixtures.

Next: Item 2 — `core/velocity_view.py` alive/stale energy.

## 2026-07-16 — Item 2 COMPLETE (alive/stale energy) — `test_alive_stale.py` green (7 passed)

New `core/velocity_view.py`: `WeightedBackbone` (anchor + interpreter_version + node-aligned weighted
`A`), `AliveStaleReport` (pinned §6 shape EXACTLY), private `_weighted_edges`/`_common_restriction`
(X1 common-edge restriction + `Δw = w_b − w_a`), and public `alive_stale_energy`. Decomposes `Δw`
with `hodge.hodge_decompose` over the binary structural common backbone (v1 combinatorial ⇒ projectors
key on structure, weight-independent), reporting `‖P_harm‖`/`‖P_grad‖`/`‖P_curl‖`. A7 guard fires
FIRST: interpreter-version mismatch ⇒ empty report, `interpreter_version="va→vb"`, reason recorded,
zero energies (the apophenia leak refused). Honest seam also on no-common-edges and β₁=0.

Falsifier clauses proven as tests: gradient-only Δw (`∂₁ᵀx`) ⇒ harmonic_energy < 1e-9 (curl ≡ 0 on a
4-cycle); β₁=0 ⇒ void reading with reason; three Hodge parts mutually orthogonal + report energies ==
independent `hodge_decompose` norms on a triangle+hole fixture (curl AND harmonic both live); version
boundary ⇒ empty; common restriction keeps only both-present edges (X1); no-common-nodes empty;
determinism.

**GREEN GATE — all 5 legs pass (run separately, each read):**
- `uv run ruff check .` → All checks passed
- `uv run mypy core agents eval ops scheduler scripts` → Success, no issues (202 files)
- `uv run mypy` (argless) → **69 errors** (matches the pin; my +3 checked files added none)
- `uv run python -m ops.type_gate` → Tier-2 membership OK, bare-ignore scan OK
- `uv run pytest -q -m 'not live'` → **1300 passed, 10 skipped, 9 deselected**

Note on ruff: line-length is 100; the many multibyte glyphs (₁ Δ ‖ β → ≥ § — ×) forced several
docstring/comment reflows — no logic touched. No live/podman legs relevant (deterministic, model-free,
no sandbox). No findings needed: `hodge.py`'s public projector surface exposed exactly what (b) needs
(`hodge_decompose` + `harmonic_basis`), so §10 stop-and-raise did not trigger; §4 reconciliation was a
no-op. Isolation intact: `core/complex` untouched, consumed only via its public surface.

Both items complete. Ready for orchestrator to flip status + merge.
