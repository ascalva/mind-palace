"""Core side of the research-airlock handoff (§16, Invariant 2 & 11).

The sealed core never speaks S3, never opens a socket. It writes a **de-identified criteria**
request into a shared handoff directory and later reads a **public-literature** result back —
exactly mirroring the §12 interface handoff. The Zone-B bridge is the only component that
moves these files to/from S3; it never reads the vault, and this module never imports it.

    airlock/requests/<id>.json   = de-identified criteria  (core writes → bridge PUTs to S3)
    airlock/results/<id>.json    = public literature corpus (bridge GETs from S3 → core reads)

The outbound direction is the firewall: `emit()` accepts a `ResearchCriteria` and serializes
**only** `to_request()` (de-identified terms + filters), after re-asserting it is clean. There
is no code path here that writes note content outbound — the corpus cannot cross.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from config.loader import Config
from core.research.criteria import Paper, ResearchCriteria

REQUESTS = "requests"
RESULTS = "results"


def _utcnow() -> str:
    return datetime.now(UTC).replace(tzinfo=None).isoformat(timespec="seconds")


def _atomic_write_json(path: Path, obj: dict[str, Any]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj), encoding="utf-8")
    tmp.replace(path)  # the bridge never reads a partial request


@dataclass(frozen=True)
class ResearchResult:
    """A parsed public-literature result file. Public data — never the mirror."""

    criteria_id: str
    papers: tuple[Paper, ...]
    sources_queried: tuple[str, ...]
    ts: str

    @classmethod
    def from_dict(cls, obj: dict[str, Any]) -> ResearchResult:
        return cls(
            criteria_id=str(obj.get("criteria_id") or obj.get("id", "")),
            papers=tuple(Paper.from_dict(p) for p in obj.get("papers", [])),
            sources_queried=tuple(obj.get("sources_queried", [])),
            ts=str(obj.get("ts", "")),
        )


@dataclass
class ResearchAirlock:
    handoff: Path

    def __post_init__(self) -> None:
        self.requests_dir = self.handoff / REQUESTS
        self.results_dir = self.handoff / RESULTS
        self.requests_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)

    def emit(self, criteria: ResearchCriteria) -> str:
        """Write a de-identified criteria request to the handoff. Returns the request id.

        The ONLY thing serialized is `criteria.to_request()` — de-identified terms + filters.
        `assert_clean()` re-validates here so nothing un-scrubbed can leave even if the
        criteria object was built by hand (defense in depth at the trust boundary)."""
        criteria.assert_clean()
        payload = criteria.to_request()
        payload["ts"] = _utcnow()
        _atomic_write_json(self.requests_dir / f"{criteria.id}.json", payload)
        return criteria.id

    def collect_one(self, criteria_id: str, *, consume: bool = True) -> ResearchResult | None:
        """Read (and by default consume) the literature result for one criteria id."""
        path = self.results_dir / f"{criteria_id}.json"
        if not path.exists():
            return None
        try:
            obj = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        if consume:
            path.unlink(missing_ok=True)
        return ResearchResult.from_dict(obj)

    def collect(self, *, consume: bool = True) -> list[ResearchResult]:
        """Read every available literature result. The core ranks these inside the walls."""
        out: list[ResearchResult] = []
        for path in sorted(self.results_dir.glob("*.json")):
            try:
                obj = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            out.append(ResearchResult.from_dict(obj))
            if consume:
                path.unlink(missing_ok=True)
        return out


def build_airlock(config: Config | None = None) -> ResearchAirlock:
    """Wire the core-side airlock against the configured handoff directory."""
    from config.loader import get_config

    cfg = config or get_config()
    return ResearchAirlock(handoff=cfg.airlock.handoff_dir)
