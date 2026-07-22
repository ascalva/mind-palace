"""The integrator's pure gauge instruments — `IntegrationReport` + `CoverageGauge` (bp-089, S1′).

The inner-ring promotion (dn-inner-outer-core §2.6b) splits the pure, store-free accounting objects
OFF `core/integrator.py` — which keeps the `ledger: sqlite3.Connection` handle and its acquisition
API (`Integrator`, `build_integrator`, `coverage_gauge`) and therefore stays OUTER. These two
dataclasses touch no store, no sqlite, no network: they are the C-coverage / resolution-parity math
(bp-071 §1), computed from already-read counts. `integrator.py` re-imports them for its own use — a
genuine use, not an alias shim (they have no external importer).

Byte-identical: the classes are relocated verbatim; no field, property, or method changed.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class IntegrationReport:
    """TOTAL accounting of one `integrate` pass — the resolution-parity gauge's substrate (§1):
    every integrable L1 event is resolved into an edge or NAMED as unresolvable; nothing is
    silently dropped. `is_fully_accounted` is the parity check (bp-069 `ChatSyncReport` sibling)."""

    sessions_processed: int = 0
    sessions_skipped: int = 0                     # unchanged digest — no re-integration
    edges_minted: int = 0
    commit_events: int = 0
    commit_resolved: int = 0
    write_events: int = 0                         # file/doc events → direct edges (always resolve)
    non_integrable: int = 0                       # prompt/response/tool_use/ratify — no endpoint
    unresolved: dict[str, int] = field(default_factory=dict)   # reason → count (NAMED, not dropped)

    def name_unresolved(self, reason: str) -> None:
        self.unresolved[reason] = self.unresolved.get(reason, 0) + 1

    @property
    def integrable_events(self) -> int:
        """Events that name an endpoint (commit + write) — the parity/coverage denominator."""
        return self.commit_events + self.write_events

    @property
    def coverage(self) -> float:
        """C-coverage (§1): the fraction of integrable D-events that produced a C-edge — honest
        partial coverage (a write always resolves; a commit resolves iff its sha is in the ledger).
        """
        n = self.integrable_events
        return (self.write_events + self.commit_resolved) / n if n else 0.0

    def is_fully_accounted(self) -> bool:
        """Parity: every commit event is either resolved or NAMED unresolvable — no silent drop
        (writes resolve by construction; non-integrable events name no endpoint)."""
        return self.commit_events == self.commit_resolved + sum(self.unresolved.values())


@dataclass(frozen=True)
class CoverageGauge:
    """The C-coverage instrument (§1) as a STANDING view over the L1 + edge stores — honest partial
    coverage of the proven-edge fabric, for the daemon surface and Δ's consumption. `integrable` =
    L1 events that name an endpoint (commit + write kinds); `witnessed` = those with a C-edge;
    `unwitnessed` = the remainder (unresolved commits — NAMED at pass time, edge-less by design)."""

    integrable: int
    witnessed: int

    @property
    def unwitnessed(self) -> int:
        return self.integrable - self.witnessed

    @property
    def coverage(self) -> float:
        return self.witnessed / self.integrable if self.integrable else 0.0
