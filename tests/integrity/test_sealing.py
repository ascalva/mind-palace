"""Invariant 1: the sealed core has no network egress, enforced structurally."""

import socket

import pytest

from core import sealing
from core.sealing import SealedCoreEgressError, is_egress_allowed


def test_loopback_and_unix_allowed():
    assert is_egress_allowed(socket.AF_INET, ("127.0.0.1", 11434))   # Ollama channel
    assert is_egress_allowed(socket.AF_INET, ("localhost", 80))
    assert is_egress_allowed(socket.AF_INET6, ("::1", 80, 0, 0))
    if hasattr(socket, "AF_UNIX"):
        assert is_egress_allowed(socket.AF_UNIX, "/tmp/x.sock")


def test_external_denied():
    # RFC 5737 TEST-NET-1 — guaranteed non-routable; never actually contacted.
    assert not is_egress_allowed(socket.AF_INET, ("192.0.2.1", 80))
    # A non-literal hostname: resolving it is itself egress, so we refuse.
    assert not is_egress_allowed(socket.AF_INET, ("example.com", 443))


def test_seal_blocks_external_connect():
    sealing.seal()
    assert sealing.is_sealed()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        with pytest.raises(SealedCoreEgressError):
            s.connect(("192.0.2.1", 80))
    finally:
        s.close()


def test_seal_allows_loopback_connect():
    sealing.seal()
    # The guard must PERMIT loopback (the OS may still refuse a dead port — that is not
    # a SealedCoreEgressError).
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.2)
    try:
        s.connect(("127.0.0.1", 1))
    except SealedCoreEgressError:  # pragma: no cover - would be a guard bug
        pytest.fail("egress guard wrongly blocked loopback")
    except OSError:
        pass  # refused / timed out — the guard let it through, which is the point
    finally:
        s.close()
