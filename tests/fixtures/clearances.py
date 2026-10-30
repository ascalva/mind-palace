"""Test-only clearance minting (dn-vector-membership-store A3.4).

Production code holds clearances only through the authorities pinned by
tests/integrity/test_clearance_holders.py. Tests are the verifier: they may mint any clearance, so
a test can state exactly which classes it reads.
"""

from __future__ import annotations

from core.kernel import clearance as cl
from core.kernel.provenance import Provenance


def grant(*classes: Provenance) -> cl.Clearance[Provenance]:
    """A clearance over exactly `classes`, minted for a test."""
    return cl._mint(classes, "test")
