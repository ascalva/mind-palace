"""Self-modification writes only its own instance's levers file (DI-2, #25).

Under a named overlay the loader stopped reading `config/levers.toml`, yet the loop still wrote it:
a named instance tuning a knob would have changed Ouroboros's configuration at its next restart.
Each instance now has its own levers file (`InstanceConfig.levers`): Ouroboros's is
`config/levers.toml` as before, a named instance's `instances/<id>/levers.toml`. Its loader reads
it under its overlay, its loop writes it, and a loop pointed anywhere else refuses.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from core.kernel.config import loader
from ops.apply import read_overlay
from ops.ledger import ProposalLedger
from ops.levers import ProposedChange
from ops.selfmod import ForeignLevers, SelfModLoop, ValidationResult, build_loop

GOOD = lambda lever, value: ValidationResult(True, True, {"v": value})   # noqa: E731
SIGMA = ProposedChange(lever="dream_similarity_threshold", target=0.66, rationale="tighten")


def _isolated(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(loader, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(loader, "_CONFIG_DIR", tmp_path / "config")
    monkeypatch.setattr(loader, "_INSTANCE_OVERLAY", tmp_path / "config" / "ouroboros.toml")
    monkeypatch.setattr(loader, "_LEGACY_OVERLAY", tmp_path / "config" / "local.toml")
    monkeypatch.setattr(loader, "LEVERS_OVERLAY", tmp_path / "config" / "levers.toml")
    monkeypatch.delenv(loader.OVERLAY_ENV, raising=False)
    loader.get_config.cache_clear()


def _bench(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, extra: str = "") -> loader.Config:
    overlay = tmp_path / "bench.toml"
    overlay.write_text('[instance]\nid = "bench"\n[selfmod]\nenabled = true\n' + extra)
    monkeypatch.setenv(loader.OVERLAY_ENV, str(overlay))
    loader.get_config.cache_clear()
    return loader.get_config()


def test_a_named_instance_tunes_its_own_levers_and_reads_them(monkeypatch, tmp_path) -> None:
    _isolated(monkeypatch, tmp_path)
    cfg = _bench(monkeypatch, tmp_path)
    own = tmp_path / "instances" / "bench" / "levers.toml"
    loop = build_loop(GOOD, config=cfg, ledger=ProposalLedger(tmp_path / "ledger.sqlite"))
    assert loop.overlay_path == cfg.instance.levers == own

    p = loop.propose(SIGMA)
    loop.approve(p.id)
    loop.execute_and_validate(p.id)
    assert read_overlay(own) == {"dreaming": {"similarity_threshold": 0.66}}
    assert not loader.LEVERS_OVERLAY.exists()            # Ouroboros's levers file is untouched
    assert loader.get_config().dreaming.similarity_threshold == 0.66   # its own loader reads it

    monkeypatch.delenv(loader.OVERLAY_ENV)               # control: Ouroboros does not see it
    loader.get_config.cache_clear()
    assert loader.get_config().dreaming.similarity_threshold == 0.62


def test_the_named_overlay_still_wins_over_its_levers(monkeypatch, tmp_path) -> None:
    """The precedence Ouroboros has, defaults ← levers ← the hand overlay, holds for a named
    instance too: a human value in its overlay beats a loop-tuned one."""
    _isolated(monkeypatch, tmp_path)
    own = tmp_path / "instances" / "bench" / "levers.toml"
    own.parent.mkdir(parents=True)
    own.write_text("[dreaming]\nsimilarity_threshold = 0.66\nmax_clusters = 6\n")
    cfg = _bench(monkeypatch, tmp_path, "[dreaming]\nsimilarity_threshold = 0.7\n")
    assert cfg.dreaming.similarity_threshold == 0.7 and cfg.dreaming.max_clusters == 6


def test_a_named_instances_loop_refuses_another_levers_file(monkeypatch, tmp_path) -> None:
    """Constructed by hand, the loop defaults to Ouroboros's levers file; for a named instance
    that is another individual's state, so every step refuses before writing."""
    _isolated(monkeypatch, tmp_path)
    cfg = _bench(monkeypatch, tmp_path)
    ouroboros_levers = tmp_path / "config" / "levers.toml"
    loop = SelfModLoop(config=cfg, ledger=ProposalLedger(tmp_path / "ledger.sqlite"),
                       validator=GOOD, overlay_path=ouroboros_levers)
    with pytest.raises(ForeignLevers):
        loop.propose(SIGMA)
    assert not ouroboros_levers.exists()


def test_control_ouroboros_keeps_config_levers(monkeypatch, tmp_path) -> None:
    _isolated(monkeypatch, tmp_path)
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "ouroboros.toml").write_text("[selfmod]\nenabled = true\n")
    cfg = loader.get_config()
    loop = build_loop(GOOD, config=cfg, ledger=ProposalLedger(tmp_path / "ledger.sqlite"))
    assert loop.overlay_path == cfg.instance.levers == loader.LEVERS_OVERLAY
    assert loop.propose(SIGMA).current_value == 0.62      # the guard leaves Ouroboros's loop be
