"""A handoff file the core will trust: written whole by a rename, and readable and writable by the
account that runs the edge reader alone (dn-ingress-language §E2).

The core reads a dialogue handoff only when no account but the daemon's could have written it: its
directory and the file the daemon's own, writable by no other account, the file of one link
(`core/ingest/files.py`). The edge readers run as the daemon's subprocesses, under its account, so
writing the file `0600` in a directory made `0700` gives the core a file it will read whatever the
umask, and gives no other account a window to open the file for writing before the rename.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

FILE_MODE, DIR_MODE = 0o600, 0o700


def write_json(path: Path, doc: object) -> None:
    """Write `doc` to `path` as JSON: a `0600` temporary file beside it, then a rename."""
    path.parent.mkdir(mode=DIR_MODE, parents=True, exist_ok=True)
    tmp = path.with_suffix(".part")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, FILE_MODE)
    try:
        os.fchmod(fd, FILE_MODE)             # a file left from an earlier run keeps its old mode
        data = memoryview(json.dumps(doc).encode("utf-8"))
        while data:
            data = data[os.write(fd, data):]
    finally:
        os.close(fd)
    os.replace(tmp, path)
