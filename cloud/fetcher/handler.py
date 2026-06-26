"""Cloud fetcher Lambda entrypoint (BUILD-SPEC §16, step 3).

Triggered by an S3 PUT into `requests/`. Reads the de-identified criteria, performs broad
public aggregation, writes the public-literature corpus to `results/<id>.json`. It runs in
Zone C (the public cloud) and is scoped by IAM to exactly `GetObject requests/*` +
`PutObject results/*` + logs — nothing else (least privilege; see cloud/terraform/airlock).

`handle_event` takes an injected S3 client and fetch callable so the whole flow is testable
without boto3 or the network; `lambda_handler` wires the real ones.
"""

from __future__ import annotations

import json
import urllib.parse
from collections.abc import Callable
from datetime import UTC, datetime

from aggregate import aggregate
from sources import Fetch, http_fetch

RESULTS_PREFIX = "results/"


def _utcnow() -> str:
    return datetime.now(UTC).replace(tzinfo=None).isoformat(timespec="seconds")


def process_request(criteria: dict, fetch: Fetch) -> dict:
    """Pure: criteria -> results payload (no S3). The unit-testable core of the fetcher."""
    result = aggregate(criteria, fetch)
    result["ts"] = _utcnow()
    return result


def handle_event(event: dict, s3, fetch: Fetch) -> list[str]:
    """Process every S3 record in the trigger event. Returns the result keys written."""
    written: list[str] = []
    for record in event.get("Records", []):
        s3rec = record.get("s3", {})
        bucket = s3rec.get("bucket", {}).get("name")
        key = urllib.parse.unquote_plus(s3rec.get("object", {}).get("key", ""))
        if not bucket or not key.endswith(".json"):
            continue
        obj = s3.get_object(Bucket=bucket, Key=key)
        criteria = json.loads(obj["Body"].read())
        result = process_request(criteria, fetch)
        result_key = f"{RESULTS_PREFIX}{result.get('criteria_id') or criteria.get('id', '')}.json"
        s3.put_object(
            Bucket=bucket, Key=result_key,
            Body=json.dumps(result).encode("utf-8"),
            ContentType="application/json",
        )
        written.append(result_key)
    return written


def lambda_handler(event: dict, context: object) -> dict:  # AWS entrypoint
    import boto3  # provided by the Lambda runtime

    fetch: Callable[[str], bytes] = http_fetch
    written = handle_event(event, boto3.client("s3"), fetch)
    return {"written": written}
