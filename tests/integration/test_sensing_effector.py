"""The read-only sensing effector (Zone B) — Track G item G3.

These exercise the edge-side hand end to end with a FAKE transport (no real network — the
constrained-fetch profile itself is unit-checked separately). They pin: it resolves NAMES
against its reviewed allowlist (never a request-supplied URL); an empty allowlist refuses
everything; the disabled flag refuses everything; refusals come back as honest error
observations, not silent gaps; and it never imports the private zones (asserted separately in
tests/integrity/test_sensing_firewall.py, not here).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from edge.effectors.sensing import (
    EffectorsDisabled,
    SensingEffector,
    TransportError,
    build_url,
)


class FakeTransport:
    """Records the URL it was asked to fetch and returns a canned body (or raises)."""

    def __init__(self, body: bytes = b"OK", raises: Exception | None = None):
        self.body = body
        self.raises = raises
        self.calls: list[str] = []

    def get(self, url: str, *, timeout_s: float, max_bytes: int) -> bytes:
        self.calls.append(url)
        if self.raises is not None:
            raise self.raises
        return self.body


def _write_request(handoff: Path, rid: str, upstream: str, terms=()):
    d = handoff / "requests"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{rid}.json").write_text(json.dumps({
        "id": rid, "actuator": "sense_fetch", "upstream": upstream, "terms": list(terms),
        "ts": "2026-07-03T00:00:00",
    }))


def _read_observation(handoff: Path, rid: str) -> dict[str, Any]:
    return json.loads((handoff / "observations" / f"{rid}.json").read_text())


def test_serves_a_request_by_resolving_the_upstream_name(tmp_path: Path):
    transport = FakeTransport(body=b"{\"rain\": 0.1}")
    eff = SensingEffector(
        handoff=tmp_path,
        upstreams={"open-meteo": "https://api.example/v1/forecast"},
        transport=transport,
        enabled=True,
    )
    _write_request(tmp_path, "r1", "open-meteo", ["rain"])
    served = eff.run_once()

    assert served == ["r1"]
    # The URL came from the ALLOWLIST, with the scrubbed term appended — never from the request.
    assert transport.calls == ["https://api.example/v1/forecast?q=rain"]
    obs = _read_observation(tmp_path, "r1")
    assert obs["body"] == "{\"rain\": 0.1}"
    assert obs["error"] == ""
    # The request file is consumed after the observation is durably written.
    assert not list((tmp_path / "requests").glob("*.json"))


def test_unknown_upstream_is_an_honest_refusal_not_a_silent_gap(tmp_path: Path):
    transport = FakeTransport()
    eff = SensingEffector(handoff=tmp_path, upstreams={}, transport=transport, enabled=True)
    _write_request(tmp_path, "r2", "not-allowlisted", [])
    served = eff.run_once()

    assert served == ["r2"]
    assert transport.calls == []                       # nothing fetched
    obs = _read_observation(tmp_path, "r2")
    assert obs["body"] == ""
    assert "not allowlisted" in obs["error"]           # the core sees the refusal


def test_empty_allowlist_refuses_every_request(tmp_path: Path):
    # Fail-closed by default: an effector with no upstreams fetches nothing, whatever comes in.
    transport = FakeTransport()
    eff = SensingEffector(handoff=tmp_path, upstreams={}, transport=transport, enabled=True)
    _write_request(tmp_path, "r3", "anything", ["x"])
    eff.run_once()
    assert transport.calls == []
    assert _read_observation(tmp_path, "r3")["error"]


def test_non_https_allowlist_entry_is_refused_at_use(tmp_path: Path):
    # A misconfigured (http) allowlist entry is refused when used, not honored.
    transport = FakeTransport()
    eff = SensingEffector(
        handoff=tmp_path,
        upstreams={"insecure": "http://api.example/x"},
        transport=transport,
        enabled=True,
    )
    _write_request(tmp_path, "r4", "insecure", [])
    eff.run_once()
    assert transport.calls == []
    assert "https" in _read_observation(tmp_path, "r4")["error"]


def test_transport_failure_becomes_an_error_observation(tmp_path: Path):
    transport = FakeTransport(raises=TransportError("response exceeds 512 bytes — refused"))
    eff = SensingEffector(
        handoff=tmp_path,
        upstreams={"big": "https://api.example/big"},
        transport=transport,
        enabled=True,
    )
    _write_request(tmp_path, "r5", "big", [])
    eff.run_once()
    obs = _read_observation(tmp_path, "r5")
    assert obs["body"] == ""
    assert "refused" in obs["error"]


def test_disabled_effector_refuses_to_run(tmp_path: Path):
    eff = SensingEffector(handoff=tmp_path, upstreams={"x": "https://a.example"}, enabled=False)
    _write_request(tmp_path, "r6", "x", [])
    with pytest.raises(EffectorsDisabled):
        eff.run_once()


def test_build_url_appends_terms_as_a_single_query():
    assert build_url("https://a.example/x", []) == "https://a.example/x"
    assert build_url("https://a.example/x", ["rain snow"]) == "https://a.example/x?q=rain+snow"
    # Preserves an existing query string with '&'.
    assert build_url("https://a.example/x?lat=1", ["rain"]) == "https://a.example/x?lat=1&q=rain"
