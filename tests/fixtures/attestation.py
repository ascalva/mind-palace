"""Attestation test helpers — an append-only store + a fixed-fingerprint attestor.

A fixed fingerprint makes chain assertions independent of the live Constitution text, so a test
can assert `chain.constitution_fingerprints() == {TEST_FINGERPRINT}` without coupling to the
real CONSTITUTION.md.
"""

from __future__ import annotations

from pathlib import Path

from core.attestation import AttestationStore, StoreAttestor

TEST_FINGERPRINT = "F-test-constitution"


def attestor_with_store(
    tmp_path: Path, *, fingerprint: str = TEST_FINGERPRINT
) -> tuple[AttestationStore, StoreAttestor]:
    """Return (store, attestor) sharing one append-only store under ``tmp_path``."""
    store = AttestationStore(tmp_path / "attestations.sqlite")
    return store, StoreAttestor(store, fingerprint=lambda: fingerprint)
