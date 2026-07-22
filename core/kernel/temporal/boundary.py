"""The supersession coboundary `δ_D` and the `δ_D² = 0` check — dn-temporal-retrieval-algebra
Result 1 H0 (bp-032 Item 6).

The D-arrows are the version/supersession chains from `VersionStore` — a note edited over time is
`v1 ▸ v2 ▸ v3 …`, and supersession is a **strict partial order** on the versions (H0). The order
complex (nerve) of that poset carries the simplicial coboundary `δ_D`, and `δ_D² = 0` is the
defining cochain identity — it holds EXACTLY when the relation is a genuine strict partial order
(acyclic). A cycle is not a tolerated input: it means the assembled relation is not a poset (a data
defect, or a rename that forked a chain — the bp-031 gap): the build raises (stop-and-raise, §10).

These D-arrows are `E_disp` — **directed and acyclic** — and are kept STRICTLY separate from the
undirected citation backbone `A_cite` (`complex.py`, `E_geom`): A5 forbids a single `L₁` over the
union. This module builds the coboundary of the *order* structure; it never touches `A_cite`.

Zone A: takes chain data (a pure fixture, or the chains the outer acquisition seam read); no write
handle, no model, no network. **Inner (bp-089, S1′):** the store-reading wrapper
`supersession_poset` relocated to `core/temporal/acquire.py` (inner-ring promotion) — this module
now COMPUTES, it does not acquire; it holds no `VersionStore` import.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import scipy.sparse as sp

# A poset element is a versioned document identity: (doc_id, version_seq).
Element = tuple[str, int]


class SupersessionCycleError(ValueError):
    """The assembled supersession relation contains a cycle — it is NOT a strict partial order, so
    `δ_D² = 0` is undefined (H0 violated). Raised at assembly, never silently tolerated (§10)."""


@dataclass(frozen=True)
class SupersessionPoset:
    """The strict partial order on document versions, with its order-complex simplices up to
    dimension 2 (enough for `δ_D²`). `elements` is the sorted 0-cell list; `relation` is the
    transitive closure as `(a, b)` strict-less pairs; `pairs`/`triples` are the comparable chains
    (1- and 2-simplices), each stored in poset order (least element first)."""

    elements: tuple[Element, ...]
    relation: frozenset[tuple[Element, Element]]
    pairs: tuple[tuple[Element, Element], ...]
    triples: tuple[tuple[Element, Element, Element], ...]

    @property
    def n_elements(self) -> int:
        return len(self.elements)


def _transitive_closure(
    pairs: set[tuple[Element, Element]],
) -> set[tuple[Element, Element]]:
    """Reachability closure of the strict-less relation. Small (per-doc chains) — a plain
    fixpoint is ample and deterministic."""
    reach = set(pairs)
    changed = True
    while changed:
        changed = False
        for a, b in list(reach):
            for c, d in list(reach):
                if b == c and (a, d) not in reach:
                    reach.add((a, d))
                    changed = True
    return reach


def poset_from_pairs(
    elements: set[Element], less_pairs: set[tuple[Element, Element]]
) -> SupersessionPoset:
    """Build the poset (and its order complex up to dim 2) from raw strict-less pairs. Takes the
    transitive closure (H2) and RAISES `SupersessionCycleError` if the closure makes any element
    strictly precede itself — i.e. the relation is not acyclic (H0 violated)."""
    closure = _transitive_closure(set(less_pairs))
    for a, b in closure:
        if a == b:
            raise SupersessionCycleError(
                f"supersession relation is not a strict partial order: {a!r} precedes itself "
                "(a cycle) — H0 violated (a data defect, or a rename that forked a chain)."
            )
    elems = tuple(sorted(elements))
    # 1-simplices: comparable pairs (a < b), poset order.
    pairs = tuple(sorted((a, b) for (a, b) in closure))
    # 2-simplices: chains a < b < c (all three comparabilities in the closure).
    less: set[tuple[Element, Element]] = set(closure)
    triples: list[tuple[Element, Element, Element]] = []
    for a, b in pairs:
        for c in elems:
            if (b, c) in less and (a, c) in less:
                triples.append((a, b, c))
    return SupersessionPoset(
        elements=elems, relation=frozenset(closure), pairs=pairs, triples=tuple(sorted(triples))
    )


def poset_from_chains(chains: dict[str, list[int]]) -> SupersessionPoset:
    """Assemble the poset from per-document version chains: `{doc_id: [seq, …]}` (as returned by
    `VersionStore.history`/`supersessions`). Each chain is a total order within its doc; docs are
    mutually incomparable. This is the pure, store-free core `supersession_poset` delegates to."""
    elements: set[Element] = set()
    less_pairs: set[tuple[Element, Element]] = set()
    for doc_id, seqs in chains.items():
        ordered = sorted(seqs)
        for s in ordered:
            elements.add((doc_id, s))
        for i, s_i in enumerate(ordered):
            for s_j in ordered[i + 1:]:
                less_pairs.add(((doc_id, s_i), (doc_id, s_j)))
    return poset_from_pairs(elements, less_pairs)


def coboundary_0(poset: SupersessionPoset) -> sp.csr_matrix:
    """`δ_D⁰ : C⁰ → C¹`, shape `(n_pairs, n_elements)`. `(δ⁰f)([a<b]) = f(b) − f(a)` — the signed
    incidence of the order complex's 1-simplices."""
    elem_idx = {e: i for i, e in enumerate(poset.elements)}
    n_pairs = len(poset.pairs)
    n_elems = poset.n_elements
    if n_pairs == 0:
        return sp.csr_matrix((0, n_elems))
    rows = np.empty(2 * n_pairs, dtype=np.int64)
    cols = np.empty(2 * n_pairs, dtype=np.int64)
    data = np.empty(2 * n_pairs, dtype=np.float64)
    for p, (a, b) in enumerate(poset.pairs):
        rows[2 * p], cols[2 * p], data[2 * p] = p, elem_idx[a], -1.0
        rows[2 * p + 1], cols[2 * p + 1], data[2 * p + 1] = p, elem_idx[b], 1.0
    return sp.csr_matrix((data, (rows, cols)), shape=(n_pairs, n_elems))


def coboundary_1(poset: SupersessionPoset) -> sp.csr_matrix:
    """`δ_D¹ : C¹ → C²`, shape `(n_triples, n_pairs)`. `(δ¹g)([a<b<c]) = g([b,c]) − g([a,c]) +
    g([a,b])` — the alternating sum over a 2-simplex's faces."""
    pair_idx = {p: i for i, p in enumerate(poset.pairs)}
    n_triples = len(poset.triples)
    n_pairs = len(poset.pairs)
    if n_triples == 0:
        return sp.csr_matrix((0, n_pairs))
    rows = np.empty(3 * n_triples, dtype=np.int64)
    cols = np.empty(3 * n_triples, dtype=np.int64)
    data = np.empty(3 * n_triples, dtype=np.float64)
    for t, (a, b, c) in enumerate(poset.triples):
        rows[3 * t], cols[3 * t], data[3 * t] = t, pair_idx[(b, c)], 1.0
        rows[3 * t + 1], cols[3 * t + 1], data[3 * t + 1] = t, pair_idx[(a, c)], -1.0
        rows[3 * t + 2], cols[3 * t + 2], data[3 * t + 2] = t, pair_idx[(a, b)], 1.0
    return sp.csr_matrix((data, (rows, cols)), shape=(n_triples, n_pairs))


def delta_D_squared(poset: SupersessionPoset) -> sp.csr_matrix:
    """`δ_D¹ ∘ δ_D⁰ : C⁰ → C²` — zero by the cochain identity when (and only when) the relation is a
    genuine strict partial order (H0). The Item-6 falsifier asserts this is the zero matrix."""
    m: sp.csr_matrix = (coboundary_1(poset) @ coboundary_0(poset)).tocsr()
    return m


def delta_D_squared_is_zero(poset: SupersessionPoset) -> bool:
    """`δ_D² == 0` to numerical zero (Result 1 H0). True for any valid poset; a False here on an
    acyclic fixture signals an assembly bug in the coboundary signs."""
    m = delta_D_squared(poset)
    return m.nnz == 0 or bool(np.allclose(m.toarray(), 0.0))
