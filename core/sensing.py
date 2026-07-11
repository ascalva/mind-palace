# ── Family 1 boundary (labelings & information-flow) · symbols in docs/NOTATION.md ──
# OBJECT:    the sensing surface — de-identified requests OUT, observed-tier data IN
#            (hands-and-the-effector-layer.md §2–§3; the β=0 origin of the Track-G filtration).
# INVARIANT: a sense request carries no note content and no URL (unrepresentable); a sensed
#            observation lands as `observed` provenance ONLY (unforgeable — to_row has no
#            provenance parameter) and can never enter a MirrorView (I6 partition).
# ENFORCED:  structural + runtime guard — the types have no field for the wrong flow;
#            assert_clean re-scrubs at emit; ObservedView/MirrorView partition the tiers.
"""Core side of the sensing handoff (Track G, item G3 — read-only hands, β = 0).

Sensing hands are just new sensors: sandboxed fetch → de-identified request → `observed`-tier
view. This module is the sealed-core half of that path; the fetch itself lives in
`edge/effectors/sensing.py` (Zone B), which never imports this module — the wire shapes below
are **mirrored, not imported**, exactly like the research airlock (edge/bridge/protocol.py):

    <handoff>/requests/<id>.json       = de-identified sense request  (core writes → edge serves)
    <handoff>/observations/<id>.json   = the sensed result            (edge writes → core reads)

Two boundaries, both structural:

  * **Outbound** — `SenseRequest` is the only thing that crosses toward the network, and it
    cannot carry note content or an address: `terms` pass the SAME conservative scrubber as
    airlock criteria (`core.research.criteria.clean_term` — one policy, one implementation),
    and `upstream` is a short NAME into the edge-side reviewed allowlist, shaped so a URL,
    host, or path is unrepresentable. Even a reasoner steered by poisoned content cannot
    express "fetch attacker.com" here — there is no field that can hold it (the
    confused-deputy answer, made structural).
  * **Inbound** — a `SensedObservation` is third-party exhaust. `to_row()` stamps provenance
    `observed` with NO parameter (the DerivedStore move: a sensing result physically cannot
    claim to be authored), and the only typed container for these rows is `ObservedView`,
    whose constructor refuses anything else. `MirrorView` refuses `observed` rows (I6), so
    the two views PARTITION the tiers: sensing output provably cannot reach the authored
    mirror or the §15 baselines. The Track-D correlator is the intended consumer of
    `ObservedView`; until it lands, the view is the seam it will read.

The result type deliberately has **no actuator field** (§3): an observation cannot be replayed
or confused into an action — data comes back, effects never do.

Dispatch through `SensingHandoff.emit` requires an `Effect`, and admission is the construction
of an `EffectView` at ceiling SENSING (ε = 0): a reversible or irreversible effect offered to
this surface raises before anything touches the handoff — the §4 filtration enforced by type,
not review.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from config.loader import Config
from core.provenance import Provenance
from core.research.criteria import DeidentificationError, clean_term
from ops.effects import Effect, EffectView, ReversibilityClass

REQUESTS = "requests"
OBSERVATIONS = "observations"

_MAX_TERMS = 12  # a focused sense query, not an exfil channel (matches the airlock bound)

# An upstream is a short lowercase NAME — a key into the edge-side allowlist table. No dots,
# no slashes, no scheme: a hostname, URL, or path literally does not match the shape.
_UPSTREAM_NAME = re.compile(r"^[a-z][a-z0-9-]{0,31}$")
# Actuator names are code identifiers from the ops registry (sense_fetch, ...).
_ACTUATOR_NAME = re.compile(r"^[a-z][a-z0-9_]{0,31}$")


def _utcnow() -> str:
    return datetime.now(UTC).replace(tzinfo=None).isoformat(timespec="seconds")


def _atomic_write_json(path: Path, obj: dict[str, Any]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj), encoding="utf-8")
    tmp.replace(path)  # the effector never reads a partial request


class EffectorsDisabled(RuntimeError):
    """`[effectors] enabled` is false — the sensing surface refuses to build (fail-closed)."""


@dataclass(frozen=True)
class SenseRequest:
    """The de-identified sense request — the ONLY thing that crosses toward the effector.

    By construction it carries no note content and no address: a registered actuator name, a
    short upstream NAME (resolved to a URL only inside the edge zone, against the owner's
    reviewed allowlist), and scrubbed topical terms. `to_request()` is the exact wire payload."""

    actuator: str
    upstream: str
    terms: tuple[str, ...] = ()
    id: str = field(default_factory=lambda: uuid4().hex)

    def assert_clean(self) -> None:
        """Re-validate at the trust boundary (defense in depth) — a hand-built request cannot
        bypass the scrubber on its way out. Raises `DeidentificationError` on any violation."""
        if not _ACTUATOR_NAME.match(self.actuator):
            raise DeidentificationError(f"malformed actuator name: {self.actuator!r}")
        if not _UPSTREAM_NAME.match(self.upstream):
            raise DeidentificationError(
                f"upstream must be a short allowlist NAME, not an address: {self.upstream!r}"
            )
        if len(self.terms) > _MAX_TERMS:
            raise DeidentificationError(f"too many terms ({len(self.terms)} > {_MAX_TERMS})")
        for t in self.terms:
            clean_term(t)  # the shared conservative scrubber — raises on doubt

    def to_request(self) -> dict[str, Any]:
        """The outbound wire payload — de-identified fields only, no corpus content."""
        return {
            "id": self.id,
            "actuator": self.actuator,
            "upstream": self.upstream,
            "terms": list(self.terms),
        }


def sense_request(
    actuator: str, upstream: str, terms: list[str] | tuple[str, ...] = ()
) -> SenseRequest:
    """Build a `SenseRequest` from proposed (possibly model-suggested) inputs, conservatively:
    un-cleanable terms are dropped; malformed actuator/upstream names raise. Unlike the airlock
    builder, an EMPTY term list is legal — many sensors (weather, a status endpoint) take no
    query at all — but if terms were proposed and none survive scrubbing, that is a refusal,
    not a silent downgrade to an unqueried fetch."""
    seen: dict[str, None] = {}
    for raw in terms:
        try:
            seen.setdefault(clean_term(raw), None)
        except DeidentificationError:
            continue  # drop the unsafe term, keep going (conservative)
    if terms and not seen:
        raise DeidentificationError("no usable de-identified terms remained")
    request = SenseRequest(actuator=actuator, upstream=upstream, terms=tuple(seen)[:_MAX_TERMS])
    request.assert_clean()  # belt and suspenders (also validates the names)
    return request


@dataclass(frozen=True)
class SensedObservation:
    """One sensed result — third-party exhaust, observed-tier by construction.

    Deliberately has NO actuator field (§3): a sensing result cannot express or be confused
    into an action, the same way `ResearchCriteria` cannot carry a note. `error` is the
    effector's honest refusal/failure note ("" = a real body came back)."""

    request_id: str
    upstream: str
    ts: str
    body: str
    error: str = ""

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> SensedObservation:
        return cls(
            request_id=str(d.get("request_id", "")),
            upstream=str(d.get("upstream", "")),
            ts=str(d.get("ts", "")),
            body=str(d.get("body", "")),
            error=str(d.get("error", "")),
        )

    def to_row(self) -> dict[str, Any]:
        """The observed-tier row. Provenance is HARDCODED — there is no parameter, so no caller
        can launder a sensed result into an authored (or any other) class; the only way this
        data enters a store or view is wearing `observed` (I5's unforgeability, reflected)."""
        return {
            "id": f"obs-{self.request_id}",
            "text": self.body,
            "provenance": Provenance.OBSERVED.value,
            "source": f"sense:{self.upstream}",
            "ts": self.ts,
            "error": self.error,
        }


class NonObservedRowError(ValueError):
    """A row whose provenance is not `observed` was offered to an ObservedView."""


@dataclass(frozen=True)
class ObservedView:
    """The observed-tier projection — the assistant-tier read boundary, dual to `MirrorView`.

    Every contained row is guaranteed `provenance == observed`; the type itself is the proof,
    so the Track-D correlator (this view's intended consumer) inherits "I read exhaust, never
    the owner's ground truth" — and conversely `MirrorView` refuses these same rows, so the
    two views PARTITION the tiers with no representable overlap (Invariant 6, both directions).
    """

    _rows: tuple[dict[str, Any], ...] = ()

    def __post_init__(self) -> None:
        bad = [r.get("provenance") for r in self._rows
               if r.get("provenance") != Provenance.OBSERVED.value]
        if bad:
            raise NonObservedRowError(
                f"ObservedView would hold non-observed rows (provenance {bad!r}); only "
                f"{Provenance.OBSERVED.value!r} is admissible — authored/curated/interpreted "
                f"data does not belong in the assistant tier's exhaust view"
            )

    @classmethod
    def from_observations(
        cls, observations: list[SensedObservation] | tuple[SensedObservation, ...]
    ) -> ObservedView:
        """The sanctioned constructor: rows minted by `to_row()` (observed-stamped, no
        parameter); `__post_init__` re-checks, so even a buggy caller cannot smuggle a
        differently-labeled row past the type (fail-closed)."""
        return cls(_rows=tuple(o.to_row() for o in observations))

    def rows(self) -> list[dict[str, Any]]:
        """The observed rows (a fresh list; the view is immutable)."""
        return list(self._rows)

    def __len__(self) -> int:
        return len(self._rows)


@dataclass
class SensingHandoff:
    """Core-side handoff for sensing (airlock-shaped). The sealed core never opens a socket:
    it writes a clean request into the handoff and later reads the observation back; the edge
    effector is the only thing that touches the network, and it never reads the vault."""

    handoff: Path

    def __post_init__(self) -> None:
        self.requests_dir = self.handoff / REQUESTS
        self.observations_dir = self.handoff / OBSERVATIONS
        self.requests_dir.mkdir(parents=True, exist_ok=True)
        self.observations_dir.mkdir(parents=True, exist_ok=True)

    def emit(self, request: SenseRequest, effect: Effect) -> str:
        """Write one sense request to the handoff. Returns the request id.

        Admission IS the construction of an `EffectView` at ceiling SENSING (ε = 0): an effect
        of any acting class raises `CeilingExceededError` here, before anything reaches the
        handoff — this surface can express read-only sensing and nothing else (§4 filtration).
        The request is re-scrubbed at the boundary (`assert_clean`), mirroring the airlock."""
        EffectView.admit((effect,), ceiling=ReversibilityClass.SENSING)
        if effect.actuator != request.actuator:
            raise ValueError(
                f"effect actuator {effect.actuator!r} does not match request "
                f"actuator {request.actuator!r} — one effect authorizes one request"
            )
        request.assert_clean()
        payload = request.to_request()
        payload["ts"] = _utcnow()
        _atomic_write_json(self.requests_dir / f"{request.id}.json", payload)
        return request.id

    def collect(self, *, consume: bool = True) -> list[SensedObservation]:
        """Read every available observation (and by default consume the files). The returned
        objects are observed-tier by construction — hand them to `ObservedView`, never to a
        mirror path (which would refuse them anyway; that refusal is tested, not assumed)."""
        out: list[SensedObservation] = []
        for path in sorted(self.observations_dir.glob("*.json")):
            try:
                obj = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            out.append(SensedObservation.from_dict(obj))
            if consume:
                path.unlink(missing_ok=True)
        return out


def build_sensing_handoff(config: Config | None = None) -> SensingHandoff:
    """Wire the core-side sensing handoff. REFUSES (fail-closed) unless `[effectors] enabled`
    — the whole Track-G surface is OFF by default; a fresh clone cannot emit a sense request
    until the owner deliberately turns the flag on."""
    from config.loader import get_config

    cfg = config or get_config()
    if not cfg.effectors.enabled:
        raise EffectorsDisabled("[effectors] enabled is false — the sensing surface is off")
    return SensingHandoff(handoff=cfg.effectors.handoff_dir)
