"""ops/ci_witness.py — verdict mapping (pure; no network in tests)."""

from ops.ci_witness import verdict


def test_verdict_mapping():
    assert verdict(None) == "absent"
    assert verdict({"status": "running", "id": 1}) == "pending"
    assert verdict({"status": "pending", "id": 1}) == "pending"
    assert verdict({"status": "success", "id": 1}) == "green"
    # 'manual' = automatic jobs done, only manual gates remain (semantic-release): green
    assert verdict({"status": "manual", "id": 1}) == "green"
    assert verdict({"status": "failed", "id": 1}) == "red"
    assert verdict({"status": "canceled", "id": 1}) == "red"


def test_rotation_expiry_is_future_iso_date():
    from datetime import date

    from ops.ci_witness import rotation_expiry
    v = rotation_expiry()
    assert date.fromisoformat(v) > date.today()
