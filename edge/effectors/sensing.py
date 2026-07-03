"""The read-only sensing effector (Zone B) — Track G item G3, blast radius β = 0.

The one generic sensing hand: it serves `sense_fetch` requests from the filesystem handoff
with a **constrained HTTPS GET** and writes the result back as an observation. Critically:

  * **It never imports core** (nor ops, nor scheduler). Like the monitor and the bridge, the
    wire shapes are mirrored, not imported — the sealed core and this networked process agree
    on a JSON layout, never on a Python import (Invariant 2: network and private data never
    share a component; this process has no vault handle to leak).
  * **It resolves NAMES, not addresses.** A request carries `upstream`, a short name; the URL
    comes from this effector's own reviewed allowlist (`upstreams`, from config — empty by
    default, so every fetch is refused until the owner writes one in). The core-side request
    type cannot even represent a URL, so a steered reasoner cannot aim this hand anywhere the
    owner didn't pre-approve (the confused-deputy answer, both halves).
  * **The fetch profile is powerless**: https only, no redirects (a redirect off the
    allowlisted host is an exfil vector, so 3xx is refused outright), a hard response-size
    cap (refused, not truncated — truncation would silently alter data), a timeout, no auth
    headers, no cookies. It returns DATA; it cannot perform an action (§2: sensing hands are
    just new sensors).
  * **Refusals are honest.** A request it will not serve (unknown upstream, non-https
    allowlist entry, oversized/failed response) still produces an observation file — with
    `error` set and an empty body — so the core sees the refusal instead of a silent gap.

Wire layout (mirrored by core/sensing.py):

    <handoff>/requests/<id>.json      {"id", "actuator", "upstream", "terms", "ts"}
    <handoff>/observations/<id>.json  {"request_id", "upstream", "ts", "body", "error"}

OFF by default: `enabled=False` on the dataclass and `[effectors] enabled=false` in config —
`build_sensing_effector` refuses, and even a directly-constructed instance refuses to run.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

REQUESTS = "requests"
OBSERVATIONS = "observations"

_USER_AGENT = "mind-palace-sensing/0"


class EffectorsDisabled(RuntimeError):
    """The sensing effector is off (`enabled=False` / `[effectors] enabled=false`)."""


class TransportError(RuntimeError):
    """The constrained fetch refused or failed (non-https, redirect, oversize, network error)."""


class Transport(Protocol):
    """The minimal fetch surface the effector needs — satisfied by `UrllibTransport` or a test
    fake. Deliberately tiny: GET only, byte-capped, no sessions, no auth — the whole authority
    of a sensing hand is 'read this one allowlisted thing'."""

    def get(self, url: str, *, timeout_s: float, max_bytes: int) -> bytes: ...


class _RefuseRedirects(urllib.request.HTTPRedirectHandler):
    """3xx is refused outright: a redirect can point off the allowlisted host, and following
    it would turn a reviewed egress into an open one."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001, ANN201
        raise TransportError(f"redirect refused ({code} -> {newurl!r})")


@dataclass
class UrllibTransport:
    """The real constrained fetch (stdlib-only, like the cloud fetcher). https-only, redirects
    refused, size-capped read — refuses rather than truncates on oversize."""

    def get(self, url: str, *, timeout_s: float, max_bytes: int) -> bytes:
        if urllib.parse.urlsplit(url).scheme != "https":
            raise TransportError(f"non-https egress refused: {url!r}")
        opener = urllib.request.build_opener(_RefuseRedirects())
        req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
        try:
            with opener.open(req, timeout=timeout_s) as resp:
                body = resp.read(max_bytes + 1)
        except (urllib.error.URLError, OSError, TimeoutError) as e:
            raise TransportError(f"fetch failed: {e}") from e
        if len(body) > max_bytes:
            raise TransportError(f"response exceeds {max_bytes} bytes — refused, not truncated")
        return body


def build_url(base: str, terms: list[str]) -> str:
    """v0 query convention: append the scrubbed terms as one `q=` parameter. The base URL is
    the owner's reviewed allowlist entry; terms are the only request-derived content in it."""
    if not terms:
        return base
    query = urllib.parse.urlencode({"q": " ".join(terms)})
    return f"{base}{'&' if '?' in base else '?'}{query}"


def _utcnow() -> str:
    return datetime.now(UTC).replace(tzinfo=None).isoformat(timespec="seconds")


def _atomic_write_json(path: Path, obj: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj), encoding="utf-8")
    tmp.replace(path)  # core never reads a partial observation


@dataclass
class SensingEffector:
    """Serves pending sense requests from the handoff, one constrained fetch each.

    `upstreams` (name -> https base URL) is the reviewed allowlist — the ONLY place a URL
    exists in the whole sensing path. Empty (the default) means every request is refused:
    fail-closed until the owner deliberately writes an entry."""

    handoff: Path
    upstreams: Mapping[str, str] = field(default_factory=dict)
    transport: Transport = field(default_factory=UrllibTransport)
    enabled: bool = False
    timeout_s: float = 20.0
    max_bytes: int = 512 * 1024

    def __post_init__(self) -> None:
        self.requests_dir = self.handoff / REQUESTS
        self.observations_dir = self.handoff / OBSERVATIONS
        self.requests_dir.mkdir(parents=True, exist_ok=True)
        self.observations_dir.mkdir(parents=True, exist_ok=True)

    def run_once(self) -> list[str]:
        """Serve every pending request (fetch or honest refusal), consuming each request file
        after its observation is written. Returns the served request ids. Refuses entirely
        (fail-closed) unless `enabled`."""
        if not self.enabled:
            raise EffectorsDisabled("sensing effector is disabled — [effectors] enabled=false")
        served: list[str] = []
        for req_file in sorted(self.requests_dir.glob("*.json")):
            try:
                req = json.loads(req_file.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue  # partial/corrupt request; the atomic-write core side makes this rare
            request_id = str(req.get("id") or req_file.stem)
            upstream = str(req.get("upstream", ""))
            terms = [str(t) for t in req.get("terms", [])]
            body, error = self._serve(upstream, terms)
            _atomic_write_json(
                self.observations_dir / f"{request_id}.json",
                {
                    "request_id": request_id,
                    "upstream": upstream,
                    "ts": _utcnow(),
                    "body": body,
                    "error": error,
                },
            )
            req_file.unlink(missing_ok=True)  # observation is durably written first
            served.append(request_id)
        return served

    def _serve(self, upstream: str, terms: list[str]) -> tuple[str, str]:
        """One constrained fetch → (body, error). Never raises for a per-request problem —
        the refusal goes back to the core as an error observation instead."""
        base = self.upstreams.get(upstream)
        if base is None:
            return "", f"upstream {upstream!r} is not allowlisted"
        if urllib.parse.urlsplit(base).scheme != "https":
            # A misconfigured allowlist entry is refused at use, not honored (fail-closed).
            return "", f"allowlist entry for {upstream!r} is not https"
        try:
            raw = self.transport.get(
                build_url(base, terms), timeout_s=self.timeout_s, max_bytes=self.max_bytes
            )
        except TransportError as e:
            return "", str(e)
        return raw.decode("utf-8", errors="replace"), ""


def build_sensing_effector(config: object | None = None) -> SensingEffector:
    """Wire the effector from config (lazy import, mirroring `build_bridge` — edge stays
    import-light and never pulls config at module load). REFUSES unless `[effectors] enabled`."""
    from config.loader import get_config

    cfg = config or get_config()
    if not cfg.effectors.enabled:
        raise EffectorsDisabled("[effectors] enabled is false — the sensing effector is off")
    return SensingEffector(
        handoff=cfg.effectors.handoff_dir,
        upstreams=dict(cfg.effectors.upstreams),
        enabled=True,
        timeout_s=cfg.effectors.timeout_s,
        max_bytes=cfg.effectors.max_response_kb * 1024,
    )
