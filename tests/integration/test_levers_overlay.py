"""The levers.toml overlay precedence (config/loader.py): defaults ← levers ← ouroboros.

This is the link that makes an executed knob take effect: ops/apply.py writes levers.toml, and
the loader must overlay it onto the committed defaults. The owner's hand-authored ouroboros.toml is
overlaid LAST, so a human override always wins over a loop-tuned knob — human authority supreme,
the §14 ceiling.

Every test here drives the DEFAULT `load_config()` path, so each one redirects all three
machine-state paths into `tmp_path`: the two overlays plus `_LEGACY_OVERLAY` (bp-123's migration
guard). The legacy redirect is what keeps these hermetic — without it the assertions would depend
on whether the machine running pytest still has a pre-rename `config/local.toml` lying around.
"""

from __future__ import annotations

# bp-067: the loader lives in core.config now; patch its globals THERE (a re-export facade can't
# carry a monkeypatch across the module boundary — finding-0104).
from core.kernel.config import load_config, loader


def _isolate(monkeypatch, tmp_path):
    """Point the loader's legacy-overlay probe at an absent tmp_path file. bp-123's guard refuses
    to load while a real `config/local.toml` is present, and that is a property of the MACHINE, not
    of the case under test."""
    monkeypatch.setattr(loader, "_LEGACY_OVERLAY", tmp_path / "absent-legacy.toml")


def test_levers_overlay_changes_the_effective_knob(tmp_path, monkeypatch):
    levers = tmp_path / "levers.toml"
    levers.write_text("[dreaming]\nsimilarity_threshold = 0.71\n")
    monkeypatch.setattr(loader, "LEVERS_OVERLAY", levers)
    monkeypatch.setattr(loader, "_INSTANCE_OVERLAY", tmp_path / "absent-ouroboros.toml")
    _isolate(monkeypatch, tmp_path)
    cfg = load_config()                                  # default path → overlays apply
    assert cfg.dreaming.similarity_threshold == 0.71
    assert cfg.dreaming.min_cluster_size == 2            # untouched default preserved


def test_human_overlay_wins_over_a_loop_tuned_knob(tmp_path, monkeypatch):
    levers = tmp_path / "levers.toml"
    levers.write_text("[dreaming]\nsimilarity_threshold = 0.71\n")
    overlay = tmp_path / "ouroboros.toml"
    overlay.write_text("[dreaming]\nsimilarity_threshold = 0.60\n")
    monkeypatch.setattr(loader, "LEVERS_OVERLAY", levers)
    monkeypatch.setattr(loader, "_INSTANCE_OVERLAY", overlay)
    _isolate(monkeypatch, tmp_path)
    cfg = load_config()
    assert cfg.dreaming.similarity_threshold == 0.60     # ouroboros.toml (human) beats the lever


def test_no_overlays_yields_committed_defaults(tmp_path, monkeypatch):
    monkeypatch.setattr(loader, "LEVERS_OVERLAY", tmp_path / "absent-levers.toml")
    monkeypatch.setattr(loader, "_INSTANCE_OVERLAY", tmp_path / "absent-ouroboros.toml")
    _isolate(monkeypatch, tmp_path)
    cfg = load_config()
    assert cfg.dreaming.similarity_threshold == 0.62     # the shipped default
    assert cfg.selfmod.enabled is False                  # master switch off by default
