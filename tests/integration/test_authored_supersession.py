"""Owner-declared authored-historical supersession store — Item 8 / 8f (the-edge-model §4a).

A K₀↔K₀ supersession across two authored DOCUMENTS: a dispositional edge type, **owner-declared
only** — and the store enforces that STRUCTURALLY. `record()` requires and verifies an
`OwnerDeclaration` at its own boundary, so a machine / scheduler / dreamer caller is REFUSED there,
not merely "not currently wired to call it". Append-only; `superseded()` is the active-projection
filter. Deterministic; no model, no network.
"""

from __future__ import annotations

import inspect

import pytest

from core.stores.authored_supersession import (
    AuthoredSupersessionStore,
    MachineAuthorityRefused,
    OwnerDeclaration,
    owner_declaration,
)


def _store(tmp_path) -> AuthoredSupersessionStore:
    return AuthoredSupersessionStore(tmp_path / "sup.sqlite")


def test_records_an_owner_declared_supersession(tmp_path):
    sup = _store(tmp_path)
    rec = sup.record("digA", "digB", declaration=owner_declaration(), note="B revises A")
    assert (rec.superseded, rec.superseding) == ("digA", "digB")
    assert sup.superseded() == {"digA"}          # active-projection filter excludes the earlier
    assert sup.count() == 1 and sup.all()[0].note == "B revises A"


def test_rerecording_the_same_pair_is_idempotent(tmp_path):
    sup = _store(tmp_path)
    sup.record("digA", "digB", declaration=owner_declaration())
    sup.record("digA", "digB", declaration=owner_declaration())
    assert sup.count() == 1


# --- the structural fail-closed guarantee (8f acceptance: the store REFUSES machine authority) ---

def test_a_machine_caller_is_refused_at_the_store_boundary(tmp_path):
    # Simulate a dreamer / scheduler caller: it holds a reference to the store but presents no valid
    # owner authority. The store REJECTS the write at its OWN boundary — so the guarantee survives a
    # careless future caller (a shared helper / batch tool / refactor routing a machine call through
    # a once-owner-only path), NOT merely "no machine path is currently wired to call it".
    sup = _store(tmp_path)
    for forged in (None, object(), "owner", 42):
        with pytest.raises(MachineAuthorityRefused):
            sup.record("digA", "digB", declaration=forged)   # type: ignore[arg-type]
    assert sup.count() == 0                                    # nothing machine-authored got in


def test_owner_declaration_cannot_be_forged(tmp_path):
    # Construction-guarded: only owner_declaration() mints a valid capability, so importing the
    # module is not enough to fabricate owner authority.
    with pytest.raises(MachineAuthorityRefused):
        OwnerDeclaration()                        # no token
    with pytest.raises(MachineAuthorityRefused):
        OwnerDeclaration(object())                # wrong token
    # even a bypass-constructed instance (skips __post_init__) is rejected by the store's own token
    # check — the store VERIFIES, it does not merely trust the type.
    sup = _store(tmp_path)
    ghost = object.__new__(OwnerDeclaration)
    with pytest.raises(MachineAuthorityRefused):
        sup.record("digA", "digB", declaration=ghost)        # type: ignore[arg-type]


def test_the_owner_path_writes_successfully(tmp_path):
    # The positive control: a genuine owner_declaration() DOES write — the boundary refuses machine
    # authority, not all authority.
    sup = _store(tmp_path)
    sup.record("digA", "digB", declaration=owner_declaration())
    assert sup.superseded() == {"digA"}


def test_store_is_append_only(tmp_path):
    sup = _store(tmp_path)
    assert not any(hasattr(sup, m) for m in ("delete", "update", "remove", "reset"))


def test_balance_math_has_no_handle_to_this_store():
    # E_disp (the-edge-model §4): like the version + claim-op stores, this dispositional store is
    # structurally unreachable from the balance math — build_complex takes no such handle.
    from core.complex.build import build_complex
    assert "supersession" not in " ".join(inspect.signature(build_complex).parameters)
