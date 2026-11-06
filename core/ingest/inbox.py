"""The Ambassador's inbox as a source: the inbox's own record, and its capture (dn-ingress-language
§E13).

The owner reaches the Ambassador through the interface handoff: the gateway writes a request, the
core inbox (`core/interface.py`) asks the Ambassador for a reply, writes the response and removes
the request. Before it writes the response, the inbox keeps the exchange here, in its own record:
one file a request, named by the gateway's id, holding the owner's text as the request file held
it and the reply the inbox sends, each in a field of its own. The directory is the daemon's
account's alone (`0700`, each record `0600`), and nothing but `Record.write` writes it.

The palace's table reads the record as the source `inbox` (`core/ingest/table.py`): the text is the
owner's (`authored-dialogue`) and the reply is not (`observed`), by the field each was written
into, so no script, no model and no field a model writes decides a label (ING-13). The library
script `capture_inbox` stores both under the role `inbox`, which only the daemon's own jobs speak,
and the one writer lands the plan with the key last (ING-7, ING-16). A record both of whose items
have landed is removed (`readers.PalaceView.landed`), so the raw store is the bytes' one home and a
run reads only what is pending.
"""

from __future__ import annotations

import contextlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from core.ingest.files import check_dir
from core.ingest.table import INBOX, MAX_ITEM_BYTES, REQUEST_ID, inbox_dir

SCRIPT = "capture_inbox"            # the library script (`ingress/capture_inbox.palace`)
DIR_MODE, FILE_MODE = 0o700, 0o600


@dataclass(frozen=True)
class Exchange:
    """What the inbox keeps of one request: its id, its conversation, the owner's text as the
    request file held it, the reply the inbox sends, and the request's time."""

    id: str
    conversation: str
    text: str
    reply: str
    at: str


class Record:
    """The inbox's own record, written by the inbox alone: one file an exchange, in a directory of
    the daemon's account's that no other account may write."""

    def __init__(self, root: Path) -> None:
        self.root = root

    @classmethod
    def of(cls, cfg: Any) -> Record:
        return cls(inbox_dir(cfg))

    def write(self, ex: Exchange) -> Path:
        """Keep one exchange: its record written whole, by a rename, under its id. The same
        request kept twice (a crash before the inbox removed it) is the same record again."""
        if not REQUEST_ID.fullmatch(ex.id):
            raise ValueError(f"not a request id: {ex.id!r}")
        for what, text in (("text", ex.text), ("reply", ex.reply)):
            if len(text.encode("utf-8")) > MAX_ITEM_BYTES:
                raise ValueError(f"the {what} is more than an item holds ({MAX_ITEM_BYTES} bytes)")
        self._ensure()
        doc = {"id": ex.id, "conversation": ex.conversation, "at": ex.at, "text": ex.text,
               "reply": ex.reply}
        path = self.root / f"{ex.id}.json"
        tmp = self.root / f".{ex.id}.json.tmp"          # not a record's name: never read as one
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, FILE_MODE)
        try:
            os.fchmod(fd, FILE_MODE)
            data = memoryview(json.dumps(doc, ensure_ascii=False).encode("utf-8"))
            while data:
                data = data[os.write(fd, data):]
            os.fsync(fd)
        finally:
            os.close(fd)
        try:
            os.replace(tmp, path)                       # a rename: the record is whole or absent
        except OSError:
            with contextlib.suppress(OSError):
                tmp.unlink()
            raise
        return path

    def _ensure(self) -> None:
        """Make the directory, the daemon's alone, and refuse one that is not (a symlink, another
        account's, or one another account may write)."""
        if not os.path.lexists(self.root):
            self.root.parent.mkdir(parents=True, exist_ok=True)
            self.root.mkdir(mode=DIR_MODE)
            os.chmod(self.root, DIR_MODE)
        why = check_dir(self.root)
        if why is not None:
            raise PermissionError(f"the inbox's record: {why}")


def land(cfg: Any, *, stores: Any) -> dict[str, Any]:
    """The inbox's capture: the library script `capture_inbox` under the role `inbox`, evaluated
    and landed by the one writer as the daemon's own job, the records it landed whole removed.
    Returns what `ingress.perform` returns, the receipt's detail."""
    from core.ingest import ingress

    return ingress.run_library(cfg, SCRIPT, role=INBOX, stores=stores, refresh=False)
