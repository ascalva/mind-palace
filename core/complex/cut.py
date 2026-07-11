"""Min-cut-to-authored + conductance — the alignment detector (companion III §3.5; H6/A2).

The same "distance against ground" move as the drift gauge, on the graph:

  * **conductance** Φ(S) = w(∂S) / min(vol S, vol S̄) — how sealed-off a community is from the
    rest of the mirror. A community whose conductance is *falling over time* is becoming an echo
    chamber (Cheeger: ½λ₂ ≤ Φ ≤ √(2λ₂) ties it to the spectral family). The A2 axis is the
    *worst* (minimum) community conductance.
  * **grounding cut** — for an interpreted artifact, the min cut (= max flow) separating it from
    the authored leaves through its derivation refs. Multi-path support through many refs ⇒ a
    large cut; everything funnelled through one weak parent ⇒ a small one. Adding an authored
    support edge can never lower it (monotone — capacities only ever increase).

Exact, deterministic, model-free. Max-flow uses `scipy.sparse.csgraph.maximum_flow`, which needs
integer capacities: unit-weight refs are integers already; fractional weights are fixed-point
scaled (documented at the constant). These feed the drift gauge's additive structural axes
(`eval/drift.py`, the A2 extension) — detection only, nothing here alters anything.
"""

from __future__ import annotations

import numpy as np
import scipy.sparse as sp
from scipy.sparse.csgraph import maximum_flow

from core.complex.balance import signed_spectrum
from core.complex.build import ReasoningComplex
from core.complex.spectral import spectral_labels

# Fixed-point scale for fractional capacities (maximum_flow is integer-only). 1024 keeps ~3
# decimal digits of weight resolution — far finer than the unit-weight refs used today.
_CAPACITY_SCALE = 1024


def conductance(A: sp.csr_matrix, S: set[int] | frozenset[int]) -> float:
    """Φ(S) = w(∂S) / min(vol S, vol S̄) over the weighted adjacency. 0 ⇔ S is disconnected from
    the rest; 1-ish ⇔ S is not a community at all. Degenerate S (empty / everything / zero
    volume) returns 0.0 — maximally sealed, the conservative reading for an alignment detector."""
    A = A.tocsr()
    n = A.shape[0]
    members = np.zeros(n, dtype=bool)
    members[list(S)] = True
    if not members.any() or members.all():
        return 0.0
    vol_s = float(A[members].sum())
    vol_rest = float(A[~members].sum())
    if vol_s == 0.0 or vol_rest == 0.0:
        return 0.0
    boundary = float(A[members][:, ~members].sum())
    return boundary / min(vol_s, vol_rest)


def min_conductance(A: sp.csr_matrix, labels: np.ndarray | None = None) -> float:
    """The worst (minimum) community conductance over a partition — the A2 echo-chamber axis.
    `labels` defaults to the deterministic spectral partition. Communities of size < 2 are
    skipped (a singleton is not a chamber). No community ⇒ 1.0 (nothing sealed off, healthy)."""
    A = A.tocsr()
    if A.shape[0] < 2:
        return 1.0
    if labels is None:
        labels = spectral_labels(A)
    phis = []
    for lab in np.unique(labels):
        S = set(np.where(labels == lab)[0].tolist())
        if len(S) >= 2 and len(S) < A.shape[0]:
            phis.append(conductance(A, S))
    return float(min(phis)) if phis else 1.0


def grounding_cut(refs_of: dict[str, tuple[str, ...]], artifact: str,
                  authored: set[str]) -> float:
    """The min cut separating `artifact` from the authored leaves through the derivation refs
    (`refs_of`: artifact id -> its derived_from refs; a ref is either another artifact id or an
    authored digest). Unit capacity per ref edge — the cut counts how many refs must be severed
    to disconnect the artifact from ground. 0 ⇔ ungrounded (no path to an authored leaf).

    Monotone in support: adding a ref (an authored support edge) only ever adds capacity, so the
    cut never decreases — the metamorphic property the A2 detector rests on."""
    # Collect the reachable node set (artifact + interpreted ancestors + authored leaves touched).
    nodes: dict[str, int] = {}

    def _idx(name: str) -> int:
        if name not in nodes:
            nodes[name] = len(nodes)
        return nodes[name]

    src = _idx(artifact)
    sink = _idx("__authored__")                 # supersink for every authored leaf
    edges: list[tuple[int, int, int]] = []
    stack, seen = [artifact], {artifact}
    while stack:
        a = stack.pop()
        for ref in refs_of.get(a, ()):
            if ref in authored:
                edges.append((_idx(a), sink, _CAPACITY_SCALE))
            else:
                edges.append((_idx(a), _idx(ref), _CAPACITY_SCALE))
                if ref not in seen:
                    seen.add(ref)
                    stack.append(ref)
    if not edges:
        return 0.0
    n = len(nodes)
    cap = sp.lil_matrix((n, n), dtype=np.int32)
    for u, v, c in edges:
        cap[u, v] = cap[u, v] + c               # parallel refs accumulate capacity
    flow = maximum_flow(cap.tocsr(), src, sink)  # type: ignore[arg-type]  # warrant: scipy accepts csr_matrix at runtime; stubs over-narrow to csr_array (T3)
    return float(flow.flow_value) / _CAPACITY_SCALE


def alignment_snapshot(kx: ReasoningComplex) -> dict[str, float]:
    """The A2 structural axes for the drift profile, computed on one complex snapshot:

      * `frustration`      — λ_min(L̄) of the signed adjacency (rising = growing dissonance);
      * `min_conductance`  — worst community conductance (falling = an echo chamber forming).

    Detection only; the caller (a snapshot writer / the drift harness) feeds these into
    `eval.drift.Profile` — `Axis` is additive, so this is a data change, not a rewrite (A2)."""
    return {
        "frustration": signed_spectrum(kx.A_signed),
        "min_conductance": min_conductance(kx.A),
    }
