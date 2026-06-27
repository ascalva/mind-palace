"""The Zone-B bridge — the only component that touches S3 (§16, Invariant 2 & 11).

Tested with a fake in-memory S3 client (no boto3, no network). Pins: outbound criteria reach
S3 requests/ as opaque bytes; inbound results reach the handoff; the bridge has no vault
handle; results for unknown ids are ignored.
"""

from __future__ import annotations

import io
from pathlib import Path

from edge.bridge.bridge import ResearchBridge


class FakeS3:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}

    def put_object(self, *, Bucket, Key, Body, **kw):
        self.objects[Key] = Body
        return {}

    def get_object(self, *, Bucket, Key):
        return {"Body": io.BytesIO(self.objects[Key])}

    def list_objects_v2(self, *, Bucket, Prefix):
        contents = [{"Key": k} for k in self.objects if k.startswith(Prefix)]
        return {"Contents": contents}


def _bridge(tmp_path: Path, s3: FakeS3) -> ResearchBridge:
    return ResearchBridge(handoff=tmp_path, s3=s3, bucket="b")


def test_push_sends_requests_to_s3_unchanged(tmp_path: Path):
    s3 = FakeS3()
    bridge = _bridge(tmp_path, s3)
    payload = b'{"id": "r1", "topic": "migraine", "terms": ["migraine"]}'
    (tmp_path / "requests" / "r1.json").write_bytes(payload)

    pushed = bridge.push_requests()
    assert pushed == ["r1"]
    assert s3.objects["requests/r1.json"] == payload     # opaque, byte-for-byte
    assert not (tmp_path / "requests" / "r1.json").exists()  # consumed
    assert (tmp_path / "sent" / "r1.json").exists()          # now pending a result


def test_pull_brings_results_into_handoff(tmp_path: Path):
    s3 = FakeS3()
    bridge = _bridge(tmp_path, s3)
    # r1 is pending (pushed earlier).
    (tmp_path / "sent" / "r1.json").write_bytes(b"{}")
    s3.objects["results/r1.json"] = b'{"criteria_id": "r1", "papers": []}'

    pulled = bridge.pull_results()
    assert pulled == ["r1"]
    assert (tmp_path / "results" / "r1.json").read_bytes() == b'{"criteria_id": "r1", "papers": []}'
    assert not (tmp_path / "sent" / "r1.json").exists()  # no longer pending


def test_pull_ignores_results_for_unknown_ids(tmp_path: Path):
    s3 = FakeS3()
    bridge = _bridge(tmp_path, s3)
    s3.objects["results/stranger.json"] = b"{}"   # not in our pending set
    assert bridge.pull_results() == []
    assert not (tmp_path / "results" / "stranger.json").exists()


def test_full_cycle(tmp_path: Path):
    s3 = FakeS3()
    bridge = _bridge(tmp_path, s3)
    (tmp_path / "requests" / "r9.json").write_bytes(b'{"id":"r9"}')
    pushed, pulled = bridge.sync_once()
    assert (pushed, pulled) == (1, 0)         # request sent, no result yet
    s3.objects["results/r9.json"] = b'{"criteria_id":"r9","papers":[]}'
    pushed, pulled = bridge.sync_once()
    assert (pushed, pulled) == (0, 1)         # result retrieved


def test_bridge_has_no_vault_handle(tmp_path: Path):
    # Structural: the bridge is constructed with only a handoff dir + S3 client. Network and
    # private data never share a component (Invariant 2). The bridge DOES use boto3 (it is the
    # edge) — what it must never have is a path to the vault/corpus.
    bridge = _bridge(tmp_path, FakeS3())
    assert not hasattr(bridge, "vault")
    assert not hasattr(bridge, "store")
    assert set(vars(bridge)) <= {
        "handoff", "s3", "bucket", "requests_prefix", "results_prefix",
        "requests_dir", "results_dir", "sent_dir",
    }
