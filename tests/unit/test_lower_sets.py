"""The clock's cuts and scope's refinement-closed strata are one structure (`docs/LAWS.md` §IX,
BRG-4): the lower sets of a reachability preorder.

On the clock, a set of events is a cut when no generator edge reads into it from outside, the check
`Spine.crossing_edges` makes of a certified cut; BRG-4 says that is exactly a down-set of `≼`, the
reachability `Spine.order` reports. On scope, `StratumScope.of` closes a set of strata under
refinement; BRG-4 says the closed sets are exactly the sets no refinement step reads into from
outside, with the steps (`_REFINES`, the excluded `exhaust ⊂ dialogue` aside) as the generators.
Both families are closed under `∩` and `∪`, the lattice of lower sets. Every subset is checked:
there are 2⁷ sets of events below and 2¹⁵ sets of strata.
"""

from __future__ import annotations

import itertools
import random
from collections.abc import Collection, Iterable
from pathlib import Path

from core.kernel.scope import _EXCLUDED_REFINEMENTS, _REFINES, Stratum, StratumScope
from core.stores.runledger import RunLedger
from core.stores.versions import VersionStore
from core.temporal.spine import Order, Spine, SpineSources

_MEM = Path(":memory:")


def _no_edge_reads_in(D: Collection[str], edges: Iterable[tuple[str, str]]) -> bool:
    """No generator edge `a → b` with `b ∈ D` and `a ∉ D`: the clock's cut check."""
    return not any(b in D and a not in D for a, b in edges)


def _subsets(items: list[str]) -> Iterable[frozenset[str]]:
    return (frozenset(c) for r in range(len(items) + 1) for c in itertools.combinations(items, r))


# ── the clock: cuts are the down-sets of ≼ ──────────────────────────────────────────────────────

def _spine() -> Spine:
    """Two documents of two versions each, and a run whose two claims cite one version of each:
    version chains (g1), the run before its claims (g3), and claims after what they cite (g2)."""
    vs = VersionStore(_MEM)
    for doc in ("docA", "docB"):
        vs.record(doc, f"{doc}-1")
        vs.record(doc, f"{doc}-2")
    led = RunLedger(_MEM)
    run_id = led.start_run(pipeline="dream_v2", config_fingerprint="cf", corpus_digest="cd",
                           node_count=1, edge_count=0, duration_s=0.1, spectral_stats={})
    led.add_claim(run_id, kind="tension", confidence=0.5, support=("docA-1",), surface_text="t1",
                  polarity="-")
    led.add_claim(run_id, kind="theme", confidence=0.5, support=("docB-2",), surface_text="t2",
                  polarity="+")
    return Spine.derive(SpineSources(versions=vs, ledger=led))


def _is_down_set(spine: Spine, D: frozenset[str], events: list[str]) -> bool:
    return all(a in D for b in D for a in events if spine.order(a, b) is Order.BEFORE)


def test_a_set_of_events_is_a_cut_iff_it_is_a_down_set_of_the_order():
    """BRG-4, the clock: for every set of events, no generator edge reads into it from outside iff
    it is a down-set of `≼`; and the down-sets are closed under `∩` and `∪`."""
    spine = _spine()
    events = sorted(e.event_id for e in spine.events())
    edges = [(e.src, e.dst) for e in spine.generators()]
    assert len(events) == 7 and {e.gen for e in spine.generators()} == {"g1", "g2", "g3"}
    cuts = []
    for D in _subsets(events):
        is_cut = _no_edge_reads_in(D, edges)
        assert is_cut == _is_down_set(spine, D, events), sorted(D)
        if is_cut:
            cuts.append(D)
    assert len(cuts) < 2 ** len(events)                       # the order is not discrete
    closed = set(cuts)
    assert all(a & b in closed and a | b in closed for a, b in itertools.product(cuts, repeat=2))


def test_the_cut_check_rejects_a_set_missing_a_cited_version():
    """Control: a claim without the version it cites is not a down-set, and the generator edge from
    that version reads into it."""
    spine = _spine()
    events = sorted(e.event_id for e in spine.events())
    edges = [(e.src, e.dst) for e in spine.generators()]
    claim = next(e.dst for e in spine.generators() if e.gen == "g2")
    D = frozenset({claim})
    assert not _no_edge_reads_in(D, edges)
    assert not _is_down_set(spine, D, events)


# ── scope: the closed sets of strata are the cuts of the refinement steps ───────────────────────

STRATA = sorted(s.value for s in Stratum)
STEPS = [(child.value, parent.value) for child, parent in _REFINES.items()
         if child not in _EXCLUDED_REFINEMENTS]


def _closed(X: Iterable[str]) -> frozenset[str]:
    return frozenset(s.value for s in StratumScope.of(*(Stratum(x) for x in X)).strata)


def test_the_refinement_closed_sets_of_strata_are_the_cuts_of_the_refinement_steps():
    """BRG-4, scope: every set `StratumScope.of` returns has no refinement step reading into it
    from outside, and every set with none is returned unchanged; so the closed sets are exactly the
    cuts, and they are closed under `∩` and `∪` (on a fixed sample of pairs: there are 11,520)."""
    closed = set()
    for X in _subsets(STRATA):
        S = _closed(X)
        assert X <= S and _no_edge_reads_in(S, STEPS), sorted(X)
        assert (_closed(X) == X) == _no_edge_reads_in(X, STEPS), sorted(X)
        closed.add(S)
    assert len(closed) == 11_520                              # 3 · 3 · 5 · 2⁸, as counted below
    sample = random.Random(0).sample(sorted(closed, key=sorted), 400)
    assert all(a & b in closed and a | b in closed for a, b in itertools.product(sample, repeat=2))


def test_the_count_of_closed_sets_follows_the_forest():
    """The 11,520 above, from the forest: `mirror` and `reference` each have one refinement (3
    choices: neither, the refinement alone, both), `dialogue` two (5: any of the four sets of its
    refinements without it, or all three), and the eight others stand alone, `exhaust` among them
    because no closure adds it."""
    children: dict[str, list[str]] = {}
    for child, parent in STEPS:
        children.setdefault(parent, []).append(child)
    assert {p: len(c) for p, c in children.items()} == {"mirror": 1, "reference": 1, "dialogue": 2}
    alone = [s for s in STRATA if s not in children and all(s != c for c, _ in STEPS)]
    assert len(alone) == 8 and "exhaust" in alone
    assert 3 * 3 * 5 * 2 ** len(alone) == 11_520


def test_the_closure_check_rejects_an_upward_closure():
    """Control: an upward closure, where a refinement pulls in its parent and not the reverse,
    leaves `{mirror}` as it is, and the step from `mirror_authored` reads into it; the downward
    closure adds `mirror_authored`."""
    def upward(X: Iterable[str]) -> frozenset[str]:
        return frozenset(X) | {parent for child, parent in STEPS if child in X}
    assert not _no_edge_reads_in(upward({"mirror"}), STEPS)
    assert _no_edge_reads_in(_closed({"mirror"}), STEPS)
