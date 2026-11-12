"""The stress battery (eval/stress_battery.py) on a small instance: it works on clones, leaves
its source as it was, and keeps every query's text and every item's content out of its record."""

from __future__ import annotations

import json
from pathlib import Path

from core.attestation import Attestation, AttestationStore
from core.kernel.ingest.chunk import Chunk
from core.stores.lexical import LexicalStore
from eval import stress_battery


def _instance(root: Path) -> Path:
    data = root / "data"
    lexical = LexicalStore(data / "lexical.sqlite")
    for i in range(6):
        lexical.land(source_path=f"corpus/s/{i}", digest=f"d{i}", provenance="observed",
                     title=f"quokka title {i}", chunks=[Chunk(0, f"quokka words of item {i}")])
    lexical.close()
    ledger = AttestationStore(data / "attestations.sqlite")
    for i in range(8):
        ledger.append(Attestation.create(timestamp=f"2026-11-11T00:00:0{i}", agent_role="corpus",
                                         action="capture", constitution_fingerprint="F",
                                         input_hashes=[f"h{i}"], output_hashes=[f"h{i}"]))
    ledger.close()
    return data


def test_the_battery_reads_clones_and_keeps_texts_out_of_its_record(tmp_path: Path) -> None:
    data = _instance(tmp_path)
    before = {p.name: (p.stat().st_size, p.stat().st_mtime_ns) for p in data.iterdir()}
    out = tmp_path / "record.json"
    stress_battery.run(stress_battery.parse([
        "--source", str(data), "--scratch", str(tmp_path / "scratch"), "--out", str(out),
        "--parts", "keyword,ledger,concurrent,stratum,cut,mask", "--passes", "1", "--fresh", "0",
        "--draw", "3", "--paths", "3", "--concurrent-delay", "0"]))
    record = json.loads(out.read_text())
    assert set(record["parts"]) == {"keyword", "ledger", "concurrent", "stratum", "cut", "mask"}
    assert set(record["prepare"]) == {"lexical.sqlite", "attestations.sqlite"}
    assert all(p["migrated"] for p in record["prepare"].values())
    keyword = record["parts"]["keyword"]
    assert set(keyword["shapes"]) == {"free-class", "free-all", "paths-scores", "paths-search"}
    assert all(r["stable"] for rows in keyword["shapes"].values() for r in rows.values())
    assert record["parts"]["ledger"]["records"] == 8
    concurrent = record["parts"]["concurrent"]
    assert "error" not in concurrent["first"] and "error" not in concurrent["second"]
    for part in ("stratum", "cut", "mask"):
        assert record["parts"][part]["status"].startswith("not run")
    assert "quokka" not in out.read_text()                  # no title, no text, no answer
    assert {p.name: (p.stat().st_size, p.stat().st_mtime_ns) for p in data.iterdir()} == before


def test_the_battery_caps_blas_at_four_threads_and_keeps_fewer() -> None:
    assert [stress_battery._cap_threads(v) for v in (None, "8", "4", "2", "0", "x")] == \
        ["4", "4", "4", "2", "4", "4"]
