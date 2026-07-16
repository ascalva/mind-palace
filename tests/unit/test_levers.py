"""The lever registry — the bounded-knob writable surface (BUILD-SPEC §14; Invariant 5).

The load-bearing test is `test_proposed_change_cannot_express_code_or_infra`: it asserts
STRUCTURALLY that a self-modification can only ever be a knob change, because the value object
has no field that could carry a path/diff/command. That is the owner's Phase-10 ceiling encoded
as a type, not a runtime check.
"""

from __future__ import annotations

import dataclasses

import pytest

from config.loader import get_config
from ops.levers import LEVERS, Lever, LeverKind, ProposedChange, get_lever


def test_in_bounds_and_out_of_bounds():
    lever = LEVERS["dream_similarity_threshold"]  # bounds [0.55, 0.75]
    assert lever.in_bounds(0.62)
    assert lever.in_bounds(0.55) and lever.in_bounds(0.75)   # inclusive
    assert not lever.in_bounds(0.54)
    assert not lever.in_bounds(0.76)


def test_int_lever_coerces_to_whole_number():
    lever = LEVERS["dream_min_cluster_size"]
    assert lever.coerce(3.0) == 3 and isinstance(lever.coerce(3.0), int)
    assert lever.coerce(2.6) == 3   # rounds


def test_validate_is_fail_closed_outside_bounds():
    lever = LEVERS["dream_near_dup_threshold"]   # [0.90, 0.99]
    assert lever.validate(0.93) == 0.93
    with pytest.raises(ValueError, match="outside hard bounds"):
        lever.validate(0.80)   # never silently clamps — refuses


def test_unknown_lever_is_refused():
    with pytest.raises(KeyError, match="unknown lever"):
        get_lever("rm_-rf_slash")


def test_proposed_change_cannot_express_code_or_infra():
    # The structural firewall: a ProposedChange is (lever-name, numeric-target, rationale) and
    # NOTHING else. No field can carry a file path, a diff, a shell command, code, or a TF plan,
    # so a code/infra change is not a proposal the loop can even construct (cf. ResearchCriteria
    # having no field that can carry note content). If someone later adds such a field, this fails.
    fields = {f.name for f in dataclasses.fields(ProposedChange)}
    assert fields == {"lever", "target", "rationale"}
    forbidden = {"path", "file", "diff", "command", "cmd", "code", "script", "patch", "tf", "sql"}
    assert fields & forbidden == set()


def test_resolve_validates_bounds_before_the_ledger():
    # An out-of-range proposal raises at resolve() — it never reaches the ledger as PROPOSED.
    with pytest.raises(ValueError):
        ProposedChange(lever="dream_similarity_threshold", target=0.95).resolve()
    lever, value = ProposedChange(lever="dream_similarity_threshold", target=0.66).resolve()
    assert lever.name == "dream_similarity_threshold" and value == 0.66


def test_every_lever_points_at_a_real_numeric_config_knob():
    # Each lever names an existing (section.key) on the live Config, and that value is numeric —
    # guards against a typo'd lever and proves the surface is config knobs, not arbitrary attrs.
    cfg = get_config()
    for lever in LEVERS.values():
        section = getattr(cfg, lever.section)
        value = getattr(section, lever.key)
        assert isinstance(value, (int, float)) and not isinstance(value, bool)
        assert lever.kind in (LeverKind.FLOAT, LeverKind.INT)
        assert lever.lo <= lever.hi


def test_registry_keys_match_lever_names():
    for name, lever in LEVERS.items():
        assert isinstance(lever, Lever) and lever.name == name


def test_registry_has_five_levers_including_dream_rnd_sigma():
    # bp-046 widened the registry 4 -> 5: the four [dreaming] levers PLUS dream_rnd_sigma — the σ
    # knob the SHADOW dream_v2 lane actually reads (core/dreaming/shadow.py), so a sweep can move
    # what the runner computes, not just the eval-store key.
    assert len(LEVERS) == 5
    sigma = get_lever("dream_rnd_sigma")
    assert sigma.section == "dream_rnd" and sigma.key == "sigma"
    assert sigma.kind is LeverKind.FLOAT
    assert (sigma.lo, sigma.hi) == (0.55, 0.75)
    # distinct from the live-path σ lever (finding-0087's fork): different section, different name.
    assert get_lever("dream_similarity_threshold").section == "dreaming"


def test_dream_rnd_sigma_bounds_are_fail_closed():
    # out of [0.55, 0.75] is refused, never silently clamped (falsifier: bounds admit a value >hi).
    with pytest.raises(ValueError, match="outside hard bounds"):
        get_lever("dream_rnd_sigma").validate(0.80)
    assert get_lever("dream_rnd_sigma").validate(0.62) == 0.62
