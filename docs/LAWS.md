# The laws ledger

One row per algebraic law the palace's code relies on: what it says, which known structure it
instantiates, where the code holds it, how strong the claim is, which test would catch it false,
and which Lean declarations state it. The schema, discipline and seed are
`docs/design-notes/dn-mathematical-foundations.md` §2.2; the labels are the claim ladder of
`docs/design-notes/dn-research-register.md` §2.3.1, used as given. The ledger indexes and never
restates: proofs live in the design notes and in `formal/`, enforcement lives in the tests it
names.

How to read a row:

- **statement**: the law in one clause, with its arithmetic domain in parentheses.
- **structure**: the known structure the law instantiates (the note's §2.1 and §2.3), or `—` with
  the reason none is named.
- **anchor**: `file::symbol` at HEAD. A bare file means its module header.
- **label**: the claim about the code, on its Python evidence. A falsifier reading `GAP` caps it
  at Conjecture, and the arrow names the unit that is to close it. Labels upgrade only as tests
  land (the note's §3, MF-2).
- **falsifier**: the pytest node id that would catch the law false, or `GAP`.
- **formal**: the Lean declarations that state the law, as `file::name` under `formal/Palace/`, or
  `—`. They state it over exact arithmetic, or over binary64 where marked L3 (the note's
  Amendment A1). `formal/check.sh` holds every one to zero `sorry` and the three standard axioms.
  A Lean proof is about a model of the code, so it does not move the label.

The cross-reference is two-sided. Each declaration cited here carries its law id in bold at the
head of its docstring, and every law id so marked in `formal/` has a row here that cites at least
one declaration. `scripts/check_laws_xref.py` checks both directions, inside `formal/check.sh`.

## I. Memberships

`core/stores/memberships.py`. Pure ℤ, Bool and strings, with no floats anywhere, so every law
here holds exactly (the note's §2.3.1).

| law | statement | structure | anchor | label | falsifier | formal |
|---|---|---|---|---|---|---|
| MEM-1 | M is keyed by `(path, blob_sha, layer, chunk_index)`; its atom projection is a multiset; `n_doc ≤ n_occ` (exact, ℤ) | finite partial function on coordinate space; the atom projection is a multiset | `core/stores/memberships.py::_DDL` | Definition + Proposition | `tests/unit/test_memberships.py::test_a_blob_with_two_identical_windows_stores_two_membership_rows` | `Memberships.lean::count_atoms`, `Memberships.lean::nDoc_le_nOcc` |
| MEM-2 | the version fibers partition M: `Σ\|fiber\| = \|M\|` (exact, ℤ) | partition into fibers, each a word ordered by `chunk_index` | `core/stores/memberships.py::MembershipStore.fiber` | Proposition | `tests/unit/test_memberships.py::test_fiber_sizes_sum_to_the_membership_count` | `Memberships.lean::sum_card_fiber`, `Memberships.lean::disjoint_fiber`, `Memberships.lean::fiber_nonempty` |
| MEM-3 | slot runs are the adjacent-collapse run-length encoding; `\|edges\| = \|runs\| − 1`; a revert stays visible (exact, ℤ) | run-length encoding of a word | `core/stores/memberships.py::MembershipStore.slot_runs` | Proposition + Claim | `tests/unit/test_memberships.py::test_per_slot_edges_equal_runs_minus_one_and_a_revert_is_not_collapsed` | `Memberships.lean::length_runs`, `Memberships.lean::length_edges`, `Memberships.lean::length_edges_eq_changes`, `Memberships.lean::fst_ne_snd_of_mem_edges`, `Memberships.lean::runs_revert` |
| MEM-4 | re-landing is idempotent by reconciliation, never by short-circuit: currency follows each path's newest landing, reverts included; the C1 law (exact, ℤ) | idempotence held by reconciliation | `core/stores/memberships.py::MembershipStore.write_fiber` | Claim | `tests/unit/test_memberships.py::test_a_lander_that_short_circuits_on_an_existing_fiber_leaves_b_current` | `Memberships.lean::Coherent.land` |
| MEM-5 | currency selects one fiber per path; `current_any(v) ⇔ n_doc(v, t) > 0` (exact, ℤ and Bool) | one fiber chosen per path; the support map into 𝒫(atoms), whose image is the store's one Boolean structure | `core/stores/memberships.py::MembershipStore.reconcile_currency` | Claim | `tests/unit/test_memberships.py::test_current_any_is_equivalent_to_a_positive_current_document_count` | `Memberships.lean::Coherent.blob_eq`, `Memberships.lean::currentAny_iff` |
| MEM-6 | `\|V\|` only grows, except across a purge, the one logged decrement, which tombstones M rather than deleting it (exact, ℤ) | a monotone count with one logged decrement | `core/stores/memberships.py::purge_atom` | Claim | `tests/unit/test_memberships.py::test_the_vector_plane_never_shrinks_except_across_a_purge`, `tests/unit/test_memberships.py::test_purge_is_the_only_vector_removal_and_it_leaves_a_recorded_hole` | — |
| MEM-7 | chain fibers ⊆ version fibers, strictly iff an off-chain fiber exists; a side branch's atoms sit on no run (exact, ℤ) | inclusion of finite sets | `core/stores/memberships.py::MembershipStore.slot_runs` | Claim | `tests/unit/test_memberships.py::test_a_side_branch_fiber_is_a_member_of_m_but_sits_on_no_chain` | — |
| MEM-8 | presence is typed by geometry: atoms are keyed by `content_id` × `(model, dim)`, so a change of embedder invalidates reuse (exact, strings) | a relation keyed by a product | `core/stores/memberships.py::MembershipStore.known_atoms` | Claim | `tests/unit/test_memberships.py::test_reuse_is_invalidated_by_a_change_of_embedder` | — |
| MEM-9 | an atom's coverage lies within its slot's span, strictly for nested symbols; a shell's span is the whole file (exact, ℤ) | containment of integer intervals | `core/stores/memberships.py::Membership` | Proposition + Claim | `tests/unit/test_memberships.py::test_slot_coordinates_are_the_declared_extent_not_the_atoms_text_coverage` | — |
| MEM-10 | a crash's orphans are observable and invisible to default search; re-landing adopts them with zero embeds (exact, ℤ and Bool) | — (an operational law; none named) | `core/stores/memberships.py::MembershipStore.orphan_atom_ids` | Claim | `tests/unit/test_memberships.py::test_a_crash_between_the_vector_insert_and_the_fiber_write_repairs_on_reland` | — |
| MEM-11 | the kernel never imports the store; memberships enter it as data, through `RowSource` (exact: a fact of the import graph) | the layered import order of the inner and outer rings | `core/stores/memberships.py` | Claim (structural) | `tests/unit/test_memberships.py::test_the_membership_store_is_never_imported_by_the_kernel` | — |

## II. Laplacian, balance and spectral

`core/kernel/complex/laplacian.py`, `core/kernel/complex/balance.py`, `core/complex/spectral.py`.

| law | statement | structure | anchor | label | falsifier | formal |
|---|---|---|---|---|---|---|
| LAP-1 | `L·1 = 0` for `L = D − A` (exact weights: exact; float64: `allclose` at 1e-8; two summation routes agree within `4·eps·max` for rows of at most four nonzero weights, refuted at eight, Amendment A1) | the graph Laplacian `D − A`, with `1` in its kernel | `core/kernel/complex/laplacian.py::laplacian` | Proposition | `tests/unit/test_complex.py::test_laplacian_spectra`, `tests/unit/test_graph_boundary.py::test_dense_laplacian_equals_the_direct_construction` | `Laplacian.lean::lap_mulVec_one`; L3: `Roundoff.lean::agreement`, `FloatModel.lean::val_evalF_agreement`, refuted at eight: `Roundoff.lean::lap1_fails` |
| LAP-2 | `xᵀLx = Σ w(x_u − x_v)² ≥ 0` for symmetric `A ≥ 0`, so `L` is PSD; `L̄` is PSD through its signed identity, for symmetric `A` of any sign (exact over ℝ; the float64 tolerance is set by the MF-2 falsifier) | a PSD quadratic form, the Dirichlet energy; `L̄` is the `q = ½` magnetic fiber | `core/kernel/complex/laplacian.py::laplacian`, `core/kernel/complex/laplacian.py::signed_laplacian` | Conjecture → Prop at MF-2 | GAP: PSD is never asserted directly | `Laplacian.lean::dotProduct_lap_nonneg`, `Laplacian.lean::posSemidef_lap`, `Laplacian.lean::dotProduct_signedLap_nonneg`, `Laplacian.lean::posSemidef_lap_adjMatrix` |
| LAP-3 | `dim ker L` is the number of connected components of the support, for symmetric `A ≥ 0` (exact over ℝ; the code's float64 nullity is never counted) | Mathlib's components-equal-nullity theorem for `SimpleGraph.lapMatrix`, carried to weights through the support | `core/kernel/complex/laplacian.py::laplacian` | Conjecture (cited) | GAP: the nullity is never counted → MF-2 | `Laplacian.lean::card_components_eq_nullity`, `Laplacian.lean::card_components_eq_nullity_adjMatrix` |
| LAP-4 | `Spec(L_sym) ⊆ [0, 2]` for `A ≥ 0`; `D^{−1/2} := 0` at degree 0, so an isolated vertex has an identity row (float64, ε = 1e-9) | the normalized Laplacian `D^{−1/2} L D^{−1/2}` | `core/kernel/complex/laplacian.py::laplacian_sym` | Proposition + Definition | `tests/unit/test_complex.py::test_laplacian_spectra`; the degree-0 convention, pointwise → MF-2 | `Spectral.lean::lapSym_eigenvalue_mem_Icc`, `Spectral.lean::lapSym_mulVec_single_of_degree_eq_zero` |
| LAP-5 | on a connected support, `λ_min(L̄) = 0` iff the signed graph is balanced (Hou, Kunegis); the code reads the maximum over components (float64, ε = 1e-6 in the property test; `is_balanced` ships `tol = 1e-8`) | balance of a signed graph; `L̄` is the `q = ½` magnetic fiber | `core/kernel/complex/balance.py::signed_spectrum` | Claim (cited) | `tests/property/test_complex_properties.py::test_balanced_signed_graph_has_no_frustration`; the converse on one instance: `tests/property/test_complex_properties.py::test_planted_frustrated_triangle_is_enumerated` | `Balance.lean::zero_energy_iff_balanced` |
| LAP-6 | a triangle is frustrated iff it carries an odd number of negative edges (exact, ℤ/2 parity) | the ℤ/2 parity of a cycle's sign product | `core/kernel/complex/balance.py::frustrated_triangles` | Proposition | `tests/property/test_complex_properties.py::test_balanced_signed_graph_has_no_frustration`, `tests/property/test_complex_properties.py::test_planted_frustrated_triangle_is_enumerated` | `Balance.lean::not_balanced_triangle_iff`, `Balance.lean::not_balanced_triangle_iff_odd` |
| SPC-1 | clustering is deterministic (a fixed ARPACK start vector, k-means seed 0), and at least 90% stable under noise of 1e-3 (float64, scoped to the platform) | — (an implementation contract on spectral clustering) | `core/complex/spectral.py::diffusion_cluster_notes` | Hypothesis | `tests/property/test_complex_properties.py::test_diffusion_clustering_is_deterministic`, `tests/property/test_complex_properties.py::test_spectral_clustering_is_stable_under_small_perturbation` | — |
| SPC-2 | components are clustered independently and never merged: distinct components get disjoint labels (exact, sets) | the block-diagonal `L` of a disjoint union | `core/complex/spectral.py::spectral_labels` | Conjecture → Claim at MF-2 | GAP: behavioral only, through `tests/unit/test_complex.py::test_diffusion_clusterer_recovers_two_themes` | — |

## III. Cut and conductance

`core/complex/cut.py`, `core/graph/conductance.py`.

| law | statement | structure | anchor | label | falsifier | formal |
|---|---|---|---|---|---|---|
| CUT-1 | `Φ(S) = w(∂S) / min(vol S, vol S̄) ∈ [0, 1]` for symmetric `A ≥ 0`; a degenerate `S` gives 0.0 and no qualifying community gives 1.0, opposite alarms (float64; over ℚ in `formal/`) | graph conductance, the ratio Cheeger's constant minimizes | `core/complex/cut.py::conductance`, `core/complex/cut.py::min_conductance` | Definition + Conjecture → Prop at MF-3 | GAP: untested → MF-3 | `Cut.lean::conductance_mem_Icc`, `Cut.lean::conductance_eq_zero_iff` |
| CUT-2 | Cheeger: `½λ₂ ≤ h ≤ √(2λ₂)` with `λ₂` of `L_sym` and `h` the minimum over all cuts, which the partition minimum bounds above; computed nowhere (over ℝ) | the Cheeger inequality | `core/complex/cut.py` | Remark | none owed: nothing depends on it | — |
| CUT-3 | `grounding_cut` is an integer max-flow, monotone in its capacities, bottlenecked by the chain (dyadic ℚ: capacities scaled by 2¹⁰, exact in float64) | max-flow min-cut over integer capacities | `core/complex/cut.py::grounding_cut` | Proposition (cites max-flow min-cut) | `tests/property/test_structural_interpreters.py::test_adding_authored_support_never_lowers_the_grounding_cut` | — |
| CND-1 | `R_eff = L⁺ᵢᵢ + L⁺ⱼⱼ − 2L⁺ᵢⱼ ≥ 0` within a component; `∞` across components (float64 at rtol 1e-10; `∞` exact) | effective resistance through the Moore–Penrose pseudoinverse `L⁺` | `core/graph/conductance.py::_r_eff_matrix` | Definition + Claim | `tests/unit/test_conductance.py::test_disconnected_pair_r_eff_is_infinite_not_connected_within_grid`, `tests/unit/test_graph_boundary.py::test_r_eff_values_invariant_under_the_laplacian_route` | `Spectral.lean::rEff_lapPinv_nonneg` |
| CND-2 | a rise in conductance needs a weight-increased edge (float64, ε = 1e-9; over ℝ in `formal/`); attribution is leave-one-out, and an empty attribution does not mean the rise is spurious | Rayleigh's monotonicity law, through Thomson's principle | `core/graph/conductance.py::reconnection_scan` | Claim (cited) | `tests/unit/test_conductance.py::test_rayleigh_monotonicity_on_synthetic_graph` | `Rayleigh.lean::rEff_anti`, `Rayleigh.lean::resistance_anti`, `Rayleigh.lean::effConductance_mono`, `Rayleigh.lean::exists_increased_of_rise` |
| CND-3 | every profile carries the degeneracy diagnostic `corr(R_eff, 1/d_A + 1/d_B)`; at 0.9 or above, authority passes to finite `t` (float64) | — (a diagnostic; none named) | `core/graph/conductance.py::_degeneracy_diag` | Claim | `tests/unit/test_conductance.py::test_every_profile_carries_a_degeneracy_diagnostic` | — |
| CND-4 | `d_t² = Σ e^{−2tλ_k}(φ_k[i] − φ_k[j])²` over the combinatorial `L`; a reading is the σ × t grid (float64; in `formal/`, over ℝ, `d_t` is a metric that separates every two vertices and does not grow with `t` for symmetric `A ≥ 0`) | the heat semigroup `e^{−tL}` and its diffusion distance | `core/graph/conductance.py::_diffusion_distances` | Proposition + Definition | `tests/unit/test_conductance.py::test_never_one_scalar_the_profile_is_sigma_by_t` | `Heat.lean::heat_add`, `Heat.lean::diffusionDist_eq`, `Heat.lean::diffusionDist_triangle`, `Heat.lean::diffusionDist_eq_zero_iff`, `Heat.lean::diffusionDist_antitone` |
| CND-5 | `w = cos^α · exp(s_lat·a_lat − s_seq·a_seq)`; the signs are law, and the magnitudes ship at 0, so `w = cos` (IEEE-exact) | a change of measure (CN-4) | `core/graph/conductance.py::churn_weight` | Definition + Claim | `tests/unit/test_conductance.py::test_ast_scan_no_path_inverts_the_churn_signs` | — |
| CND-6 | `χ_s = chain / N_s ∈ (0, 1]` for `window=None`, the only wired call; `None` at `N_s = 0` (ℚ-valued, one float64 division: `= 1.0` iff the chain spans, for `N_s < 2⁵⁴`, Amendment A1) | a ratio of integers, rounded once | `core/graph/conductance.py::chi_s` | Proposition | `tests/unit/test_conductance.py::test_depth_budget_no_chain_exceeds_n_s_on_the_real_spine`, `tests/unit/test_conductance.py::test_chi_s_is_one_iff_totally_ordered`; the windowed law → MF-3 | L3: `Roundoff.lean::rn_div_eq_one_iff`, `Roundoff.lean::rn_div_le_one`, `Roundoff.lean::rn_div_pos`, `FloatModel.lean::toFloat_div_beq_one`, `FloatModel.lean::toFloat_div_le_one`, fails at 2⁵⁴: `Roundoff.lean::rn_div_two_pow_54` |

## IV. Curvature

`core/kernel/complex/curvature.py`: Forman, not Ollivier (the note's §2.3.3).

| law | statement | structure | anchor | label | falsifier | formal |
|---|---|---|---|---|---|---|
| CRV-1 | `Ric_F(u, v) = 4 − deg u − deg v + 3·\|△(u, v)\|` on the binarized support, the declared augmented variant (exact, ℤ) | augmented Forman–Ricci curvature | `core/kernel/complex/curvature.py::forman` | Definition | exercised by CRV-2's test | `Curvature.lean::forman` |
| CRV-2 | two `m`-cliques and one bridge: `Ric_F(bridge) = 4 − 2m`, the strict unique minimum, negative exactly from `m = 3` (exact, ℤ) | augmented Forman–Ricci curvature on a planted bridge | `tests/property/test_structural_interpreters.py::test_planted_bridge_is_negative_and_clique_edges_positive` | Proposition | `tests/property/test_structural_interpreters.py::test_planted_bridge_is_negative_and_clique_edges_positive` | `Curvature.lean::forman_bridge`, `Curvature.lean::forman_bridge_lt`, `Curvature.lean::forman_bridge_neg_iff`, `Curvature.lean::forman_pos` |
| CRV-3 | `most_negative_edges` emits the edges with `κ ≤ 0`, else only those at the minimum, in `(κ, i, j)` order, capped at `top_k` (κ is integer-valued float64, so `==` is exact) | a selection under the lexicographic order on `(κ, i, j)` | `core/kernel/complex/curvature.py::most_negative_edges` | Definition | GAP: untested, though the Dreamer consumes it → MF-3 | `Curvature.lean::kappa_nonpos`, `Curvature.lean::kappa_min`, `Curvature.lean::mostNegative_pairwise`, `Curvature.lean::length_mostNegative`, `Curvature.lean::mostNegative_prefix` |
| CRV-4 | Ollivier–Ricci over W₁ is deliberately absent; Forman is the floor (no arithmetic: an absence) | Ollivier–Ricci curvature, built on Wasserstein W₁ distances, which Mathlib lacks (issue #48) | `core/kernel/complex/curvature.py` | Observation | none owed: the absence is stated in the code | — |

## Outside the ledger, for now

`formal/` also states laws that have no ledger family yet: the clock laws (`Clock.lean`), the
shared prose plane (`Plane.lean`) and the capability-scope algebra (`Scope.lean`). They are
indexed in `formal/README.md` under their home notes' names. Their rows need family prefixes,
which are the owner's to adjudicate.
