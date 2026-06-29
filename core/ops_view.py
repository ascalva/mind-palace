"""The operational-introspection read scope (Track B / B3; nervous-system-and-ambassador.md §4).

The Ambassador has a SECOND reading scope beyond the authored mirror: the system's own
operational state — the attestation chain (what it has done), the proposal ledger (what
self-modifications are pending/decided), and the drift gauge (is it healthy). This is the one
role permitted to *read the audit layer to narrate it* — and it still cannot *write* to it.

Read-only, the MirrorView move: an `OpsView` captures ONLY the *read* methods of those stores
as bound callables. It holds no reference to a mutator on its public surface — `approve`,
`deny`, `append`, `mark_*`, `propose` are simply not attributes of this type, so the Ambassador
cannot reach them through the view (asserted in tests/integrity/test_ops_view.py). Python can't
make reach-through-`__self__` *impossible* the way a copied immutable tuple can (MirrorView), so
the honest assurance tier here is **static (typed read Protocols) + guard (the no-mutator
integrity test)** — strictly weaker than MirrorView's structural guarantee, and labelled as such.

It also renders its state in **plain language** (`narrate`) — never the internal nouns (tier
names, "synthesis job", credentials, accessors) the authoritative note §4 forbids. That plain
register is the conversational surface of "what have you been doing?" and "is the system
healthy?", and the backing for the Ambassador's effort narration.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:  # annotations only — NO runtime import, so core/ gains no edge to ops/ or eval/
    from core.attestation.record import Attestation
    from eval.drift import DriftReport
    from ops.ledger import Proposal


class AttestationReader(Protocol):
    """The read surface of the append-only attestation store (no `append`)."""

    def all(self) -> list[Any]: ...
    def by_role(self, role: str) -> list[Any]: ...
    def count(self) -> int: ...


class ProposalReader(Protocol):
    """The read surface of the proposal ledger (no `approve`/`deny`/`mark_*`)."""

    def all(self) -> list[Any]: ...
    def pending(self) -> list[Any]: ...


@dataclass(frozen=True)
class OpsSnapshot:
    """A plain, model-free summary of operational state — the data the status path renders."""

    attestation_count: int
    recent_actions: tuple[tuple[str, str, str], ...]   # (role, action, timestamp), newest first
    pending_proposals: int
    drift_within_tolerance: bool | None                # None = not measured this session
    constitution_intact: bool | None


@dataclass(frozen=True)
class OpsView:
    """Read-only introspection over attestations + the proposal ledger + the drift gauge.

    Construct with `OpsView.over(...)`; the fields are bound READ callables only — there is no
    mutator on this type's surface (B3's read-only guarantee)."""

    _all_attestations: Callable[[], list[Attestation]]
    _attestations_by_role: Callable[[str], list[Attestation]]
    _attestation_count: Callable[[], int]
    _all_proposals: Callable[[], list[Proposal]]
    _pending_proposals: Callable[[], list[Proposal]]
    # Optional: a bound drift reading. Computing live drift runs the golden set (needs the
    # embedder), so the per-chat path usually passes a cached reading or None — never blocking
    # a conversational turn on a heavy measurement.
    _drift: Callable[[], DriftReport] | None = None

    @classmethod
    def over(cls, attestations: AttestationReader, ledger: ProposalReader, *,
             drift: Callable[[], DriftReport] | None = None) -> OpsView:
        """Bind the read methods of the live stores. The returned view exposes those and only
        those — the stores' mutators are unreachable through it."""
        return cls(
            _all_attestations=attestations.all,
            _attestations_by_role=attestations.by_role,
            _attestation_count=attestations.count,
            _all_proposals=ledger.all,
            _pending_proposals=ledger.pending,
            _drift=drift,
        )

    # --- reads -------------------------------------------------------------------------------
    def attestation_count(self) -> int:
        return self._attestation_count()

    def recent_actions(self, limit: int = 5) -> list[tuple[str, str, str]]:
        """The most recent (role, action, timestamp) triples, newest first."""
        atts = sorted(self._all_attestations(), key=lambda a: a.timestamp, reverse=True)
        return [(a.agent_role, a.action, a.timestamp) for a in atts[:limit]]

    def actions_by_role(self, role: str) -> list[tuple[str, str]]:
        return [(a.action, a.timestamp) for a in self._attestations_by_role(role)]

    def pending_proposals(self) -> list[Proposal]:
        return list(self._pending_proposals())

    def all_proposals(self) -> list[Proposal]:
        return list(self._all_proposals())

    def drift_report(self) -> DriftReport | None:
        return self._drift() if self._drift is not None else None

    def snapshot(self) -> OpsSnapshot:
        report = self.drift_report()
        return OpsSnapshot(
            attestation_count=self.attestation_count(),
            recent_actions=tuple(self.recent_actions()),
            pending_proposals=len(self.pending_proposals()),
            drift_within_tolerance=None if report is None else report.within_tolerance,
            constitution_intact=None if report is None else report.constitution_intact,
        )

    # --- plain-language narration (no internal nouns — authoritative note §4) -----------------
    def narrate(self) -> str:
        """A plain-English status summary for "what have you been doing / are you healthy".
        Deliberately avoids tier names, job/queue nouns, credentials — the *shape* of the work,
        never the plumbing."""
        snap = self.snapshot()
        parts: list[str] = []
        if snap.attestation_count == 0:
            parts.append("I haven't recorded any activity yet.")
        else:
            actions = _humanize_actions(snap.recent_actions)
            parts.append(
                f"I've logged {snap.attestation_count} action"
                f"{'s' if snap.attestation_count != 1 else ''} so far"
                + (f" — most recently {actions}." if actions else ".")
            )
        if snap.pending_proposals:
            parts.append(
                f"There {'is' if snap.pending_proposals == 1 else 'are'} "
                f"{snap.pending_proposals} change{'s' if snap.pending_proposals != 1 else ''} "
                "waiting on your approval."
            )
        else:
            parts.append("Nothing is waiting on your approval.")
        parts.append(_narrate_health(snap))
        return " ".join(parts)


# Map internal action verbs to plain phrases — never expose the raw verb if it reads as plumbing.
_ACTION_WORDS = {
    "ingest_note": "took in a note",
    "capture": "saved something you told me",
    "read": "looked something up for you",
    "propose": "lined up some work to do",
    "dream_pass": "looked for patterns across your notes",
    "curate_finding": "tidied up your notes",
}


def _humanize_actions(recent: tuple[tuple[str, str, str], ...]) -> str:
    if not recent:
        return ""
    phrases: list[str] = []
    for _role, action, _ts in recent[:3]:
        phrases.append(_ACTION_WORDS.get(action, "did some background work"))
    # de-duplicate consecutive identical phrases for readability
    deduped: list[str] = []
    for p in phrases:
        if not deduped or deduped[-1] != p:
            deduped.append(p)
    return ", ".join(deduped)


def _narrate_health(snap: OpsSnapshot) -> str:
    if snap.constitution_intact is False:
        return "Something at my core looks off — I'd want you to take a look."
    if snap.drift_within_tolerance is None:
        return "I haven't taken a health reading this session."
    if snap.drift_within_tolerance:
        return "Everything looks healthy."
    return "I've drifted a little further than I'd like — worth a look when you have a moment."
