"""A hosted decision model's client, run as a process of its own: requests in, typed answers out.

The edge's one way to a hosted System One model (TypeSafe's API, `POST /v1/systemone`). It runs
as its own process, as the corpus readers do (`scripts/corpus.py` starts `python -m
edge.corpus.<source>`): the caller writes its requests to a file, this process sends them and
writes the answers to another, so the process that reads stores never holds a connection to the
network and this one never opens a store.

What leaves the machine is exactly what the caller wrote. The caller decides what may be sent; the
evaluation harness (`eval/decision_integrators.py`) writes only public benchmark text. Nothing
here reads a store or a vault.

**The key** is read from the macOS Keychain when the process starts (generic password, service
`TYPESAFE_API_KEY`, the current account), held in memory, sent only in the `Authorization`
header, and never printed, logged or written.

**The meter.** Each answer's `usage.input_tokens` is priced at `--price` dollars per million
input tokens (output tokens are free) and added to the ledger file the caller names, under a lock,
before the next request starts. Once the ledger's total reaches `--stop-usd`, no further request is
sent; the process writes what it has and exits 3, with the requests it did not send counted. At
most `--workers` requests are in flight, so the overshoot is bounded by that many requests.

**Failures are errors, never answers.** A 429 or a 5xx is retried with exponential backoff,
honouring `Retry-After`; any other failure, or retries exhausted, is written as that request's
error and the caller counts it.

    uv run python -m edge.systemone --requests R.jsonl --responses S.jsonl --ledger L.json \\
        --stop-usd 1.50 [--price 0.042] [--workers 4]

A request line is `{"key": ..., "payload": {...}}`; a response line is `{"key": ...,
"response": {...}, "seconds": ...}` or `{"key": ..., "error": "..."}`.
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ENDPOINT = "https://api.typesafe.ai/v1/systemone"
RETRYABLE = (429, 500, 502, 503, 504)
STOPPED = 3  # exit status: the ledger reached the stop before every request was sent


class SystemOneError(RuntimeError):
    """A request that failed: refused by the API, or retries exhausted."""


def keychain_key(service: str = "TYPESAFE_API_KEY") -> str:
    """The API key from the macOS login Keychain. Raises if it is absent; never prints it."""
    account = os.environ.get("USER") or getpass.getuser()
    out = subprocess.run(
        ["security", "find-generic-password", "-s", service, "-a", account, "-w"],
        capture_output=True, text=True, timeout=30,
    )
    key = out.stdout.strip()
    if out.returncode != 0 or not key:
        raise SystemOneError(f"no Keychain item for service {service}")
    return key


Transport = Callable[[dict[str, Any]], tuple[int, dict[str, Any], dict[str, str]]]


@dataclass
class Client:
    """Posts one request at a time; retries what the API marks as transient."""

    key: str = field(repr=False)
    endpoint: str = ENDPOINT
    timeout_s: float = 120.0
    retries: int = 6
    transport: Transport | None = field(default=None, repr=False)

    def _post(self, payload: dict[str, Any]) -> tuple[int, dict[str, Any], dict[str, str]]:
        if self.transport is not None:
            return self.transport(payload)
        req = urllib.request.Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.key}"},
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                return resp.status, json.loads(resp.read()), dict(resp.headers.items())
        except urllib.error.HTTPError as e:
            body = e.read()
            try:
                parsed = json.loads(body)
            except ValueError:
                parsed = {"detail": body[:500].decode("utf-8", "replace")}
            return e.code, parsed if isinstance(parsed, dict) else {"detail": parsed}, dict(
                e.headers.items() if e.headers else {})

    def ask(self, payload: dict[str, Any]) -> dict[str, Any]:
        delay = 2.0
        for attempt in range(self.retries):
            try:
                status, body, headers = self._post(payload)
            except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
                if attempt == self.retries - 1:
                    raise SystemOneError(f"connection failed: {e}") from e
                time.sleep(delay)
                delay = min(delay * 2, 120.0)
                continue
            if status == 200:
                return body
            if status not in RETRYABLE or attempt == self.retries - 1:
                raise SystemOneError(f"HTTP {status}: {json.dumps(body)[:500]}")
            after = headers.get("Retry-After", headers.get("retry-after", ""))
            wait = float(after) if after.replace(".", "", 1).isdigit() else delay
            time.sleep(min(max(wait, delay), 300.0))
            delay = min(delay * 2, 120.0)
        raise SystemOneError("retries exhausted")


class Ledger:
    """The running cost, kept in a file across runs; every update is written before it returns."""

    def __init__(self, path: Path, price_per_mtok: float, stop_usd: float) -> None:
        self.path = path
        self.price = price_per_mtok
        self.stop = stop_usd
        self.lock = threading.Lock()
        data: dict[str, Any] = json.loads(path.read_text()) if path.exists() else {}
        self.input_tokens = int(data.get("input_tokens", 0))
        self.output_tokens = int(data.get("output_tokens", 0))
        self.requests = int(data.get("requests", 0))
        self.runs: list[dict[str, Any]] = list(data.get("runs", []))

    @property
    def usd(self) -> float:
        return self.input_tokens * self.price / 1e6

    def open(self) -> bool:
        with self.lock:
            return self.usd < self.stop

    def charge(self, usage: dict[str, Any]) -> None:
        with self.lock:
            self.input_tokens += int(usage.get("input_tokens") or 0)
            self.output_tokens += int(usage.get("output_tokens") or 0)
            self.requests += 1
            self._write()

    def _write(self) -> None:
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps({
            "price_per_mtok": self.price, "stop_usd": self.stop,
            "input_tokens": self.input_tokens, "output_tokens": self.output_tokens,
            "requests": self.requests, "usd": round(self.usd, 6), "runs": self.runs,
        }, indent=1))
        tmp.replace(self.path)

    def close_run(self, entry: dict[str, Any]) -> None:
        with self.lock:
            self.runs.append(entry)
            self._write()


def run(requests: list[dict[str, Any]], client: Client, ledger: Ledger,
        workers: int) -> tuple[list[dict[str, Any]], int]:
    """Send every request while the ledger is open; return the response lines and the number
    left unsent because the ledger reached its stop."""
    out: list[dict[str, Any]] = []
    lock = threading.Lock()
    unsent = 0

    def one(line: dict[str, Any]) -> None:
        nonlocal unsent
        if not ledger.open():
            with lock:
                unsent += 1
            return
        t0 = time.monotonic()
        try:
            resp = client.ask(line["payload"])
        except SystemOneError as e:
            row: dict[str, Any] = {"key": line["key"], "error": str(e)}
        else:
            ledger.charge(resp.get("usage") or {})
            row = {"key": line["key"], "response": resp,
                   "seconds": round(time.monotonic() - t0, 4)}
        with lock:
            out.append(row)

    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        list(pool.map(one, requests))
    return out, unsent


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0] if __doc__ else None)
    ap.add_argument("--requests", type=Path, required=True)
    ap.add_argument("--responses", type=Path, required=True)
    ap.add_argument("--ledger", type=Path, required=True)
    ap.add_argument("--stop-usd", type=float, required=True)
    ap.add_argument("--price", type=float, default=0.042, help="dollars per million input tokens")
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args(argv)
    requests = [json.loads(line) for line in a.requests.read_text().splitlines() if line.strip()]
    ledger = Ledger(a.ledger, a.price, a.stop_usd)
    started = datetime.now(UTC).isoformat(timespec="seconds")
    before = ledger.input_tokens
    rows, unsent = run(requests, Client(key=keychain_key()), ledger, a.workers)
    with a.responses.open("a") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")
    errors = sum(1 for r in rows if "error" in r)
    ledger.close_run({"started": started, "requests": len(requests), "sent": len(rows),
                      "errors": errors, "unsent": unsent,
                      "input_tokens": ledger.input_tokens - before})
    print(f"sent {len(rows)} of {len(requests)}, {errors} errors, {unsent} unsent; "
          f"ledger ${ledger.usd:.4f} of ${a.stop_usd:.2f}", file=sys.stderr)
    return STOPPED if unsent else 0


if __name__ == "__main__":
    raise SystemExit(main())
