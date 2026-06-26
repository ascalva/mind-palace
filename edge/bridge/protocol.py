"""Airlock wire layout (BUILD-SPEC §16). Mirrored, not imported, by the sealed core.

The bridge is a **dumb pipe**: it shuttles opaque JSON between the filesystem handoff and S3
and never interprets the payloads (it can read neither the vault nor the de-identified
criteria's meaning — it just moves bytes). The only thing it needs to agree on with the core
and the cloud fetcher is the key layout, kept here so an edit can't silently drift it:

    handoff/requests/<id>.json   <->   s3://<bucket>/requests/<id>.json   (outbound)
    handoff/results/<id>.json    <->   s3://<bucket>/results/<id>.json    (inbound)

Outbound is the firewall direction: the bridge only ever PUTs whatever the core placed in
`requests/`, which by construction is de-identified criteria (the corpus cannot reach here —
this component has no vault handle and `core` never imports it; Invariant 2 & 11).
"""

from __future__ import annotations

from typing import Protocol


class S3Client(Protocol):
    """The minimal S3 surface the bridge needs — satisfied by a boto3 client or a fake.

    Deliberately tiny: no delete, no bucket admin. The bridge can PUT requests and GET
    results and nothing else; cleanup is handled by the bucket lifecycle, not the bridge,
    so the bridge's IAM stays least-privilege (Invariant: tight IAM)."""

    def put_object(self, *, Bucket: str, Key: str, Body: bytes) -> object: ...
    def get_object(self, *, Bucket: str, Key: str) -> dict: ...
    def list_objects_v2(self, *, Bucket: str, Prefix: str) -> dict: ...


def request_key(prefix: str, request_id: str) -> str:
    return f"{prefix}{request_id}.json"


def result_id_from_key(prefix: str, key: str) -> str | None:
    """`results/abc.json` -> `abc`; None if the key isn't a result object."""
    if not key.startswith(prefix) or not key.endswith(".json"):
        return None
    return key[len(prefix):-len(".json")] or None
