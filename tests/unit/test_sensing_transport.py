"""The constrained-fetch transport guards (Track G item G3, Zone B).

The real `UrllibTransport` is the sensing hand's only network reach; its guards are what keep a
read-only sensor from becoming an exfil channel. The non-https refusal is a PURE check (it
raises before any socket work), so it is unit-testable offline — the redirect refusal and the
size cap need a live server and are exercised by the edge smoke path, not here.
"""

from __future__ import annotations

import pytest

from edge.effectors.sensing import TransportError, UrllibTransport


def test_non_https_url_is_refused_before_any_fetch():
    # http:// (and file://, ftp://, ...) is refused at the scheme check — no socket is opened.
    transport = UrllibTransport()
    for bad in ("http://api.example/x", "file:///etc/passwd", "ftp://host/x"):
        with pytest.raises(TransportError, match="non-https"):
            transport.get(bad, timeout_s=1.0, max_bytes=1024)
