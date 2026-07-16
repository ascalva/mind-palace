"""The tuning manifest: model + loader + resolved-manifest fingerprint (bp-047 Item 15).

Verifies the note §2.6 invariants: a manifest loads; a missing `autonomy` resolves to `"propose"`;
a key naming an unregistered lever raises at load (fail-closed); `autonomy = "auto"` is rejected as
E3b; and `resolved_fingerprint()` is stable under TOML reorderings but moves when a policy changes.
POLICY-ONLY is asserted structurally — the manifest exposes no live lever value.
"""

from __future__ import annotations

import pytest

from eval.harness.tuning import (
    DEFAULT_AUTONOMY,
    AutoModeNotSupported,
    LeverPolicy,
    TuningManifest,
    UnregisteredLever,
    load_manifest,
)
from ops.levers import LEVERS


def _write(tmp_path, text: str):
    p = tmp_path / "tuning.toml"
    p.write_text(text, encoding="utf-8")
    return p


# --- loads + covers the whole registry -------------------------------------------------------
def test_shipped_manifest_loads_and_covers_every_lever():
    manifest = load_manifest()  # config/tuning.toml
    assert set(manifest.policies) == set(LEVERS)
    for name in LEVERS:
        pol = manifest.policy(name)
        assert pol.autonomy == "propose"
        assert pol.subsystem == "dreaming"
        assert pol.objective == "f9_composite"


def test_missing_file_resolves_every_lever_to_default_policy(tmp_path):
    manifest = load_manifest(tmp_path / "does_not_exist.toml")
    assert set(manifest.policies) == set(LEVERS)
    for name, lever in LEVERS.items():
        pol = manifest.policy(name)
        assert pol.autonomy == DEFAULT_AUTONOMY == "propose"
        assert pol.subsystem == lever.section  # defaults to the lever's own section


def test_absent_autonomy_resolves_to_propose(tmp_path):
    path = _write(tmp_path, "[tuning.dream_similarity_threshold]\nsubsystem = 'dreaming'\n")
    manifest = load_manifest(path)
    assert manifest.policy("dream_similarity_threshold").autonomy == "propose"


# --- POLICY-ONLY: range is derived from the registry, never declared -------------------------
def test_range_is_derived_from_the_registry_not_the_manifest(tmp_path):
    path = _write(tmp_path, "[tuning.dream_similarity_threshold]\nautonomy = 'propose'\n")
    pol = load_manifest(path).policy("dream_similarity_threshold")
    lever = LEVERS["dream_similarity_threshold"]
    assert pol.range == (lever.lo, lever.hi)
    # POLICY-ONLY: the manifest exposes no live lever value field to shadow local.toml.
    assert not hasattr(pol, "value")
    assert "value" not in LeverPolicy.__dataclass_fields__


# --- fail-closed: an unregistered lever raises at load ---------------------------------------
def test_unregistered_lever_raises_at_load(tmp_path):
    path = _write(tmp_path, "[tuning.not_a_real_lever]\nautonomy = 'propose'\n")
    with pytest.raises(UnregisteredLever):
        load_manifest(path)


def test_fixed_point_key_cannot_load_silently(tmp_path):
    # A never-tunable fixed point (no lever constructor) must not be silently accepted — falsifier.
    path = _write(tmp_path, "[tuning.golden_set]\nautonomy = 'propose'\n")
    with pytest.raises(UnregisteredLever):
        load_manifest(path)


# --- E3b out of scope: auto is rejected, auto fields are unknown keys -------------------------
def test_auto_autonomy_is_rejected_as_e3b(tmp_path):
    path = _write(tmp_path, "[tuning.dream_similarity_threshold]\nautonomy = 'auto'\n")
    with pytest.raises(AutoModeNotSupported) as exc:
        load_manifest(path)
    assert "E3b" in str(exc.value)


def test_auto_mode_fields_are_unknown_keys(tmp_path):
    path = _write(
        tmp_path,
        "[tuning.dream_similarity_threshold]\nautonomy = 'propose'\nauto_band = [0.6, 0.7]\n",
    )
    with pytest.raises(ValueError, match="unknown manifest key"):
        load_manifest(path)


def test_unknown_autonomy_value_is_rejected(tmp_path):
    path = _write(tmp_path, "[tuning.dream_similarity_threshold]\nautonomy = 'yolo'\n")
    with pytest.raises(ValueError, match="unknown autonomy"):
        load_manifest(path)


# --- fingerprint: order-insensitive, policy-sensitive ----------------------------------------
def _two_levers(order_ab: bool) -> str:
    a = "[tuning.dream_similarity_threshold]\nautonomy = 'propose'\nobjective = 'f9_composite'\n"
    b = "[tuning.dream_max_clusters]\nautonomy = 'propose'\nobjective = 'f9_composite'\n"
    return (a + "\n" + b) if order_ab else (b + "\n" + a)


def test_fingerprint_is_stable_across_toml_reorderings(tmp_path):
    fp_ab = load_manifest(_write(tmp_path, _two_levers(True))).resolved_fingerprint()
    other = tmp_path / "other.toml"
    other.write_text(_two_levers(False), encoding="utf-8")
    fp_ba = load_manifest(other).resolved_fingerprint()
    assert fp_ab == fp_ba  # falsifier: fingerprint must NOT depend on TOML key order


def test_fingerprint_changes_when_a_policy_value_changes(tmp_path):
    base = _write(tmp_path, "[tuning.dream_similarity_threshold]\nobjective = 'f9_composite'\n")
    fp_base = load_manifest(base).resolved_fingerprint()
    changed = tmp_path / "changed.toml"
    changed.write_text(
        "[tuning.dream_similarity_threshold]\nobjective = 'structural_axes'\n", encoding="utf-8"
    )
    fp_changed = load_manifest(changed).resolved_fingerprint()
    assert fp_base != fp_changed


def test_fingerprint_is_a_sha256_hexdigest(tmp_path):
    fp = load_manifest().resolved_fingerprint()
    assert len(fp) == 64 and all(c in "0123456789abcdef" for c in fp)


def test_resolved_covers_registry_with_derived_range_and_kind():
    resolved = TuningManifest(load_manifest().policies).resolved()
    assert set(resolved) == set(LEVERS)
    entry = resolved["dream_min_cluster_size"]
    lever = LEVERS["dream_min_cluster_size"]
    assert entry["range"] == [lever.lo, lever.hi]
    assert entry["kind"] == lever.kind.value
