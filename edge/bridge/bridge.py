"""The research-airlock bridge (Zone B) — the ONLY component that touches S3 (§16).

It carries de-identified criteria OUT (handoff → S3 `requests/`) and public literature back
IN (S3 `results/` → handoff), and does nothing else. Critically:

  * **It has no vault handle.** It is constructed with a handoff directory and an S3 client —
    not the vault path, not any store. The private corpus is structurally unreachable here
    (Invariant 2): network and private data never share a component.
  * **It is a dumb pipe.** It never parses the criteria or the papers; it moves opaque JSON
    bytes. So even a bug here cannot leak corpus content — there is no corpus to leak, and the
    outbound bytes are whatever the sealed core already de-identified.
  * **`core` never imports this module** (the static import-firewall enforces it). The core
    reaches the bridge only through files on disk.

Lifecycle of one request:
    1. core writes `handoff/requests/<id>.json` (de-identified criteria).
    2. bridge PUTs it to `s3://bucket/requests/<id>.json`, records it pending (`handoff/sent/`).
    3. cloud Lambda fetches public literature, writes `s3://bucket/results/<id>.json`.
    4. bridge GETs results for pending ids, writes `handoff/results/<id>.json`, clears pending.
    5. core reads `handoff/results/<id>.json` and ranks inside the walls.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

from edge.bridge.protocol import S3Client, request_key, result_id_from_key

REQUESTS = "requests"
RESULTS = "results"
SENT = "sent"          # local marker dir: requests PUT to S3, awaiting a result


@dataclass
class ResearchBridge:
    handoff: Path
    s3: S3Client
    bucket: str
    requests_prefix: str = "requests/"
    results_prefix: str = "results/"

    def __post_init__(self) -> None:
        self.requests_dir = self.handoff / REQUESTS
        self.results_dir = self.handoff / RESULTS
        self.sent_dir = self.handoff / SENT
        for d in (self.requests_dir, self.results_dir, self.sent_dir):
            d.mkdir(parents=True, exist_ok=True)

    # --- outbound: de-identified criteria → S3 requests/ -------------------------------
    def push_requests(self) -> list[str]:
        """PUT every pending criteria request to S3 `requests/`. Returns pushed ids."""
        pushed: list[str] = []
        for req_file in sorted(self.requests_dir.glob("*.json")):
            request_id = req_file.stem
            body = req_file.read_bytes()  # opaque to the bridge — already de-identified
            self.s3.put_object(
                Bucket=self.bucket, Key=request_key(self.requests_prefix, request_id), Body=body
            )
            # Mark pending and consume the local request so it isn't pushed twice.
            (self.sent_dir / req_file.name).write_bytes(body)
            req_file.unlink(missing_ok=True)
            pushed.append(request_id)
        return pushed

    # --- inbound: S3 results/ → public-literature handoff -------------------------------
    def pull_results(self) -> list[str]:
        """GET any finished literature results for pending ids; write them to the handoff."""
        pending = {p.stem for p in self.sent_dir.glob("*.json")}
        if not pending:
            return []
        listing = self.s3.list_objects_v2(Bucket=self.bucket, Prefix=self.results_prefix)
        pulled: list[str] = []
        for obj in listing.get("Contents", []):
            rid = result_id_from_key(self.results_prefix, obj.get("Key", ""))
            if rid is None or rid not in pending:
                continue
            resp = self.s3.get_object(Bucket=self.bucket, Key=obj["Key"])
            body = resp["Body"].read()
            tmp = self.results_dir / f"{rid}.json.tmp"
            tmp.write_bytes(body)
            tmp.replace(self.results_dir / f"{rid}.json")  # atomic; core never reads partial
            (self.sent_dir / f"{rid}.json").unlink(missing_ok=True)  # no longer pending
            pulled.append(rid)
        return pulled

    def sync_once(self) -> tuple[int, int]:
        """One push + pull cycle. Returns (#pushed, #pulled)."""
        pushed = self.push_requests()
        pulled = self.pull_results()
        return len(pushed), len(pulled)

    def run(self, *, poll_interval_s: float = 5.0, max_cycles: int | None = None) -> None:
        cycles = 0
        while max_cycles is None or cycles < max_cycles:
            self.sync_once()
            cycles += 1
            time.sleep(poll_interval_s)


def build_bridge(config=None) -> ResearchBridge:
    """Wire a real bridge from config. boto3 is imported LAZILY here so importing this module
    (e.g. in tests with a fake S3 client) never requires boto3 — and so `boto3` never appears
    in the sealed core's dependency surface."""
    import boto3  # Zone-B only; never importable from core (import-firewall enforced)

    from config.loader import get_config

    cfg = config or get_config()
    al = cfg.airlock
    if not al.s3_bucket:
        raise RuntimeError(
            "airlock.s3_bucket is unset — run `terraform apply` (cloud/terraform/airlock) "
            "and copy the `airlock_bucket` output into config."
        )
    session = boto3.Session(profile_name=al.aws_profile or None, region_name=al.s3_region)
    return ResearchBridge(
        handoff=al.handoff_dir,
        s3=session.client("s3"),
        bucket=al.s3_bucket,
        requests_prefix=al.requests_prefix,
        results_prefix=al.results_prefix,
    )
