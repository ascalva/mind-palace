"""The levers.toml overlay precedence (config/loader.py): defaults ← levers ← local.

This is the link that makes an executed knob take effect: ops/apply.py writes levers.toml, and
the loader must overlay it onto the committed defaults. The owner's hand-authored local.toml is
overlaid LAST, so a human override always wins over a loop-tuned knob — human authority supreme,
the §14 ceiling.
"""

from __future__ import annotations

from config import loader
from config.loader import load_config


def test_levers_overlay_changes_the_effective_knob(tmp_path, monkeypatch):
    levers = tmp_path / "levers.toml"
    levers.write_text("[dreaming]\nsimilarity_threshold = 0.71\n")
    monkeypatch.setattr(loader, "LEVERS_OVERLAY", levers)
    monkeypatch.setattr(loader, "_LOCAL", tmp_path / "absent-local.toml")
    cfg = load_config()                                  # default path → overlays apply
    assert cfg.dreaming.similarity_threshold == 0.71
    assert cfg.dreaming.min_cluster_size == 2            # untouched default preserved


def test_human_local_toml_wins_over_a_loop_tuned_knob(tmp_path, monkeypatch):
    levers = tmp_path / "levers.toml"
    levers.write_text("[dreaming]\nsimilarity_threshold = 0.71\n")
    local = tmp_path / "local.toml"
    local.write_text("[dreaming]\nsimilarity_threshold = 0.60\n")
    monkeypatch.setattr(loader, "LEVERS_OVERLAY", levers)
    monkeypatch.setattr(loader, "_LOCAL", local)
    cfg = load_config()
    assert cfg.dreaming.similarity_threshold == 0.60     # local.toml (human) overrides the lever


def test_no_overlays_yields_committed_defaults(tmp_path, monkeypatch):
    monkeypatch.setattr(loader, "LEVERS_OVERLAY", tmp_path / "absent-levers.toml")
    monkeypatch.setattr(loader, "_LOCAL", tmp_path / "absent-local.toml")
    cfg = load_config()
    assert cfg.dreaming.similarity_threshold == 0.62     # the shipped default
    assert cfg.selfmod.enabled is False                  # master switch off by default
