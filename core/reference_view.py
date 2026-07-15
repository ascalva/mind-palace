# ── Family 1 boundary (labelings & information-flow) · symbols in docs/NOTATION.md ──
# OBJECT:    The §2.3 reference read surface — a deterministic, commit-anchored read window
#            over the Lane-1 reference graph (`core/stores/reference_edges.py`). The archetype
#            client of dn-core-query-protocol: "the simplest well-typed client — no model, no
#            cross-stratum budget, no firewall composition, no hallucination surface" (§2.3).
# INVARIANT: read-only + in-core. The view binds ONLY the store's read closures; no mutator
#            (`add_batch`) and no connection (`_conn`) is reachable through it (Inv 4 flavor:
#            reports data, takes no action). An in-core reader is not a plane crossing (§2.4
#            item 5: "In-core clients are unaffected") — this imports nothing from the network
#            edge and holds no vault handle.
# ENFORCED:  static (the frozen dataclass exposes read methods and only read methods) + guard
#            (tests/unit/test_reference_view.py asserts no `add_batch`/`_conn` is an attribute).
"""`ReferenceView` — the deterministic "who cites this?" read window (dn-core-query-protocol §2.3).

The Lane-1 reference-edge store (`reference_edges.sqlite`, ~272k edges incl. ~75k doc→doc) is
FED by the code sensor but has been **agent-unreachable**: `all(target_ref=…)` has zero callers
outside the store's own docstring (finding-0059/0061 — the reference graph is built but nobody
reads it). This module is the first reader: a typed read window in the mould of `OpsView`
(`core/ops_view.py`) — bind the store's readers as closures, expose reads and only reads.

**Commit-anchored (the §3 Q1 decision).** Reference edges are per-commit: `commit_sha` is part
of edge identity, so `store.all(target_ref=X)` returns rows across ALL history (~272k). The
"current" citation set is the edges at ONE anchor commit — so `ReferenceView.over(store, *,
commit=…)` filters to that anchor, and `open_reference_view` resolves the default to the active
run's `commit_sha` (`RunLedger.last()`), falling back to git HEAD (`git_state`), matching the
§2.6 oracle's "at HEAD." The rejected alternative — union across all history — returns stale
historical citations and is never the answer to "who cites this *now*."

**Fiber-scoped (F) for free (§3 Q2).** The note types `F` = citations/warrants (these edges),
`D` = supersession (a DIFFERENT store — `versions`/`core/temporal/boundary.py`). The reference
store holds ONLY `F` edges, so `E = {F}` is automatic here: the type simply cannot name `D`.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from core.stores.reference_edges import ReferenceEdge, open_reference_edge_store

if TYPE_CHECKING:  # annotations only — the factory imports the config/ledger lazily at runtime
    from config.loader import Config
    from core.stores.reference_edges import ReferenceEdgeStore


@dataclass(frozen=True)
class ReferenceView:
    """A deterministic, fiber-scoped (F), commit-anchored read window over the reference graph.

    Construct with `ReferenceView.over(store, commit=…)`; the fields are bound READ closures
    only — the store's `add_batch`/`_conn` are unreachable through this type's surface (§2.1
    scope: the type names reads, never a mutator). Read-only + in-core (Inv 4/Inv 2)."""

    # bound at .over(): the store's read closures, already filtered to the anchor commit.
    _edges_to: Callable[[str], list[ReferenceEdge]]    # references TO a ref (who cites it)
    _edges_from: Callable[[str], list[ReferenceEdge]]  # references FROM a ref (what it cites)
    commit: str                                        # the anchor commit these reads are scoped to

    @classmethod
    def over(cls, store: ReferenceEdgeStore, *, commit: str) -> ReferenceView:
        """Bind the store's read methods, filtered to `commit`. The returned view exposes those
        reads and only those — the store's mutators are unreachable through it (mirrors
        `OpsView.over`). Edges are per-commit (§3 Q1), so BOTH closures drop any row whose
        `commit_sha` differs from the anchor — the stale-union bug is structurally excluded."""

        def edges_to(ref: str) -> list[ReferenceEdge]:
            return [e for e in store.all(target_ref=ref) if e.commit_sha == commit]

        def edges_from(ref: str) -> list[ReferenceEdge]:
            return [e for e in store.all(source_ref=ref) if e.commit_sha == commit]

        return cls(_edges_to=edges_to, _edges_from=edges_from, commit=commit)

    # --- reads -----------------------------------------------------------------------------------
    def references_to(self, ref: str) -> list[ReferenceEdge]:
        """"Who cites this doc/symbol" — edges whose `target_ref == ref`, at the anchor commit."""
        return self._edges_to(ref)

    def references_from(self, ref: str) -> list[ReferenceEdge]:
        """"What this doc/symbol cites" — edges whose `source_ref == ref`, at the anchor commit."""
        return self._edges_from(ref)

    def connected_set(self, ref: str, *, depth: int = 1) -> set[str]:
        """The §2.3 "connected set over fibers F": a bounded, cycle-safe BFS over
        `references_to ∪ references_from` from `ref`, expanding `depth` hops, returning the set of
        reached OTHER refs (self-excluded — the §11 pinned default; noisy self-inclusion rejected).

        A neighbour of node X is the far endpoint of any edge touching X: `references_from(X)`
        contributes its `target_ref`s, `references_to(X)` its `source_ref`s. `visited` (seeded
        with `ref`) makes cycles terminate and keeps `ref` out of the result; `depth ≤ 0` → ∅."""
        visited = {ref}
        reached: set[str] = set()
        frontier = {ref}
        for _hop in range(max(depth, 0)):
            nxt: set[str] = set()
            for node in frontier:
                neighbours = ({e.target_ref for e in self._edges_from(node)}
                              | {e.source_ref for e in self._edges_to(node)})
                for n in neighbours:
                    if n not in visited:
                        visited.add(n)
                        reached.add(n)
                        nxt.add(n)
            frontier = nxt
            if not frontier:
                break
        return reached


def _resolve_default_commit(cfg: Config) -> str:
    """The §3 Q1 anchor: the active run's `commit_sha` (`RunLedger.last()`), else git HEAD
    (`git_state`). The rejected alternatives (union-across-history, max(created_at)) are recorded
    in plan §11. Resolved OFF the store — no `latest_commit()` helper added to the store (§11)."""
    from config.loader import REPO_ROOT
    from ops.lifecycle.runs import git_state, open_run_ledger

    ledger = open_run_ledger(cfg)
    try:
        last = ledger.last()
    finally:
        ledger.close()
    if last is not None and last.commit_sha and last.commit_sha != "unknown":
        return last.commit_sha
    sha, _dirty = git_state(REPO_ROOT)
    return sha


def open_reference_view(config: Config | None = None, *,
                        commit: str | None = None) -> ReferenceView:
    """Factory: open the live reference store read-only and bind a `ReferenceView` anchored at
    `commit` — defaulting (§3 Q1) to the active run's `commit_sha` (`RunLedger.last()`), else git
    HEAD (`git_state`). The store is the same `open_reference_edge_store` the sensor writes; this
    view only ever calls its readers."""
    from config.loader import get_config

    cfg = config or get_config()
    anchor = commit if commit is not None else _resolve_default_commit(cfg)
    store = open_reference_edge_store(cfg)
    return ReferenceView.over(store, commit=anchor)
