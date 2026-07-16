"""`build_dreamer` wires the A2 structural-snapshot store (bp-045, dn-evaluation-harness §3 E5).

Catalog row 6 was "built, unwired — SnapshotStore not passed by `build_dreamer`". This proves the
wiring, and — the whole-plan falsifier — that it is invisible to the live path: Phase-7 `dream()`
writes NO structural snapshot (it has no step-10), while `dream_v2`'s step-10 now fires through the
wired store. Construction is side-effect-free (no live model until a chat call; the fake synth means
none is made), so this is a wiring + behaviour check, not a live integration test.
"""

from __future__ import annotations

import dataclasses
from typing import Any, cast

from config.loader import get_config, load_config
from core.dreaming import build_dreamer
from core.provenance import Provenance
from core.stores.vectorstore import VectorStore

# The same planted shape the R0/R1 + dream_v2 tests use (two clusters + a bridge + an outlier), so
# every lens fires deterministically and dream_v2 produces at least one candidate.
ROWS = [
    {"digest": "dA1", "title": "A1", "provenance": "authored-solo", "vector": [1.0, 0.0, 0.0],
     "text": "alpha one"},
    {"digest": "dA2", "title": "A2", "provenance": "authored-solo", "vector": [0.97, 0.03, 0.0],
     "text": "alpha two"},
    {"digest": "dB1", "title": "B1", "provenance": "authored-solo", "vector": [0.0, 1.0, 0.0],
     "text": "beta one"},
    {"digest": "dB2", "title": "B2", "provenance": "authored-solo", "vector": [0.0, 0.97, 0.03],
     "text": "beta two"},
    {"digest": "dG1", "title": "G1", "provenance": "authored-solo", "vector": [0.7, 0.7, 0.0],
     "text": "the bridge"},
    {"digest": "dZ1", "title": "Z1", "provenance": "authored-solo", "vector": [0.0, 0.0, 1.0],
     "text": "outlier"},
]


class _RowSource:
    def __init__(self, rows: list[dict[str, Any]]):
        self._rows = rows

    def all_rows(self, *, provenances=None) -> list[dict[str, Any]]:
        if provenances is None:
            return list(self._rows)
        allowed = {Provenance(p).value for p in provenances}
        return [r for r in self._rows if r.get("provenance") in allowed]


class _CountingSynth:
    """Echoes the [[titles]] in the evidence (grounded ⇒ self-check passes); no live model."""

    def __call__(self, messages) -> str:
        import re
        content = messages[-1]["content"] if messages else ""
        titles = re.findall(r"\[\[([^\]]+)\]\]", content)
        cites = " ".join(f"[[{t}]]" for t in dict.fromkeys(titles))
        return f"A structural pattern connects {cites}."


def _cfg_in(tmp_path):
    cfg = get_config()
    paths = dataclasses.replace(
        cfg.paths,
        raw_store=tmp_path / "raw",
        vector_store=tmp_path / "v.lance",
        derived_store=tmp_path / "derived.sqlite",
        vault_catalog=tmp_path / "catalog.sqlite",
        attestation_store=tmp_path / "attestations.sqlite",
    )
    vault = dataclasses.replace(cfg.vault, path=tmp_path / "vault")
    return dataclasses.replace(cfg, paths=paths, vault=vault)


def test_build_dreamer_wires_the_snapshot_store(tmp_path):
    """The core claim: build_dreamer passes a SnapshotStore at the configured path (row 6)."""
    cfg = _cfg_in(tmp_path)
    dreamer = build_dreamer(cfg)
    assert dreamer.snapshots is not None
    expected = cfg.paths.derived_store.parent / "structural.duckdb"
    assert dreamer.snapshots.path == expected
    assert dreamer.snapshots.count() == 0     # fresh — no run has written yet


def test_phase7_writes_no_snapshot_but_dream_v2_does(tmp_path):
    """Through build_dreamer's wired store: Phase-7 dream() writes NO structural row (the whole-plan
    falsifier — it has no step-10), while dream_v2's step-10 fires and records exactly one."""
    dreamer = build_dreamer(_cfg_in(tmp_path))
    # keep build_dreamer's WIRED snapshots; swap in deterministic data + the fake synth (no model).
    dreamer = dataclasses.replace(dreamer, store=cast(VectorStore, _RowSource(ROWS)),
                                  synthesize=_CountingSynth())
    snaps = dreamer.snapshots
    assert snaps is not None

    before = snaps.count()
    dreamer.dream()                                     # Phase-7 (v1) — no step-10
    assert snaps.count() == before, "Phase-7 dream() must not write a structural snapshot"

    on = dataclasses.replace(load_config(),
                             dream_rnd=dataclasses.replace(load_config().dream_rnd, enabled=True))
    dreamer.dream_v2(config=on)                          # topological (v2) — step-10 fires
    assert snaps.count() == before + 1, "dream_v2 step-10 should record exactly one snapshot"
