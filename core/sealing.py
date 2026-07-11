"""Structural network-egress guard for Zone A (the sealed core).

Invariant 1 (BUILD-SPEC §3): the sealed core has zero network egress, enforced
*structurally*, not by convention. The ideal enforcement is OS-level — a separate
network namespace with `--network=none`, or a `pf` anchor denying outbound for the
core's uid — and that is the deployment-time hardening layer (see docs/runbook.md).

On bare macOS during development we cannot hand the core a Linux netns, so this module
is the in-process structural layer: a fail-closed guard, installed process-wide, that
intercepts every socket `connect`/`connect_ex` and permits ONLY loopback destinations
(127.0.0.0/8, ::1) plus AF_UNIX. The single legitimate "egress" the core makes is to
the local Ollama model server on 127.0.0.1 (BUILD-SPEC §5, §7) — a loopback IPC
channel, not egress to the outside world. Any attempt to reach a non-loopback address
raises SealedCoreEgressError before a packet leaves.

Defense in depth: neither layer alone is the whole story (a native extension opening
its own socket could bypass a Python-level guard), but the guard fails closed, is
process-wide, and is verifiable in tests — and it composes with the OS-level layer at
deployment. The guard is installed by the core runtime entrypoint (`core.runtime`),
never as an import side effect.

DNS note: resolving a hostname is itself egress (it leaks intent to a resolver). The
only host the core dials is an IP literal (127.0.0.1), so name resolution is never
required inside the walls — we therefore refuse to connect to any non-loopback or
non-literal host rather than resolve it.
"""

from __future__ import annotations

import ipaddress
import socket
from typing import Any


class SealedCoreEgressError(RuntimeError):
    """Raised when sealed-core code attempts to connect to a non-loopback address."""


def _host_is_loopback(host: str) -> bool:
    """True if `host` is the loopback interface, WITHOUT performing name resolution."""
    if host in ("localhost", "localhost.", ""):
        # Empty host == loopback for connect(); "localhost" is trusted without a DNS hit.
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        # A non-literal hostname (anything but "localhost"): resolving it is itself
        # egress, so we refuse rather than look it up. Fail closed.
        return False


def is_egress_allowed(family: int, address: Any) -> bool:
    """Pure decision: may a socket of `family` connect to `address`?

    AF_UNIX (local IPC) is always allowed. AF_INET/AF_INET6 are allowed only to a
    loopback host. Everything else is denied. Side-effect free, so it is unit-testable
    without touching a real socket.
    """
    if hasattr(socket, "AF_UNIX") and family == socket.AF_UNIX:
        return True
    if family in (socket.AF_INET, socket.AF_INET6):
        # address is (host, port) for INET, (host, port, flowinfo, scope_id) for INET6.
        if not isinstance(address, tuple) or not address:
            return False
        return _host_is_loopback(str(address[0]))
    return False  # unknown family — deny


_INSTALLED = False
# Capture the originals at import, before any wrapping, so seal() is idempotent and the
# guard always delegates to the real implementation for permitted (loopback) connects.
_real_connect = socket.socket.connect
_real_connect_ex = socket.socket.connect_ex


def _guarded_connect(self: socket.socket, address: Any) -> None:
    if not is_egress_allowed(self.family, address):
        raise SealedCoreEgressError(
            f"sealed core blocked egress to {address!r} (family={self.family!r}); "
            "only loopback is permitted"
        )
    return _real_connect(self, address)


def _guarded_connect_ex(self: socket.socket, address: Any) -> int:
    if not is_egress_allowed(self.family, address):
        raise SealedCoreEgressError(
            f"sealed core blocked egress to {address!r} (family={self.family!r}); "
            "only loopback is permitted"
        )
    return _real_connect_ex(self, address)


def seal() -> None:
    """Install the process-wide egress guard. Idempotent.

    Call once at core-process startup, before any work. After this returns, any
    connect() to a non-loopback address raises SealedCoreEgressError.
    """
    global _INSTALLED
    if _INSTALLED:
        return
    # warrant(T3): deliberate process-wide monkeypatch — THE egress guard (Invariant 1).
    # The guard accepts a looser address type than _socket's overload set, hence the
    # `assignment` code alongside `method-assign`.
    socket.socket.connect = _guarded_connect  # type: ignore[method-assign, assignment]
    socket.socket.connect_ex = _guarded_connect_ex  # type: ignore[method-assign, assignment]
    _INSTALLED = True


def is_sealed() -> bool:
    return _INSTALLED


def assert_sealed() -> None:
    if not _INSTALLED:
        raise SealedCoreEgressError("sealed core is not sealed; call core.sealing.seal() first")
