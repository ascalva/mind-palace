"""The door: a command as a request, the daemon as the one writer (dn-ingest-door D3, D5, D7).

A surface that speaks a command (`do …`) compiles it under the grant of the **role** it speaks
for, and, if admitted, writes a **request** into its spool, a per-role directory under the
interface handoff directory (`cfg.interface.handoff_dir`; the daemon makes and owns the
spools, and only a role's own writers may write its spool, §5). The daemon drains the
spools each tick (`scheduler/door.py`), enqueues one job per request as the kind the command
compiles to, and binds the **role to the spool the request came from**: the filesystem is the
authenticator, no field of the request names a role. The job's payload is the request id and
the sentence's digest (and, for today's kinds, their usual payload), so `queue.sqlite` never
holds corpus text; the text stays in the request file, whose name is its id. The handler
compiles the sentence **again** under the spool's grant, the second check, the one that counts,
performs the command under the one writer, and writes the **receipt** beside the request:
`spooled`, then `queued` with the job id, then `landed` with what landed, or `refused` with why.
A receipt names the request, never the sentence: the text has one home.

What the daemon trusts of a spool is bounded (two security reviews of 2026-11-05, §9 of the
note). The spools are the daemon's: it makes the root (`0755`, nobody else adds an entry), the
operator's spool (`0700`, the owner's account alone writes it) and the agents' spool (`3770`, the
group writes, the sticky bit keeps one writer from moving another's file), and the `queued/`,
`receipts/` and `rejected/` beneath each (the daemon's alone). It drains only a spool whose every
directory is a real directory, owned by its own account and writable by no one it should not be.
A request is read through a file descriptor that follows no link and blocks on nothing: a regular
file with one link, under the size cap, whose id is sixteen hex digits and its name, written, in
the operator's spool, by the daemon's own account. Anything else is moved to `rejected/` and
reported, never re-read and never allowed to stop the drain; the daemon then works from its own
copy (`stage`), so a writer's later change to its file changes nothing. The identities the door
mints for turns live under `dialogue/door/<role>/`, so no role's command can name the owner's
turns or another role's.

This module is core: it opens no queue and no store on its own, and imports no scheduler. The
scheduler's `drain_spool` and `door_handler` are the daemon's side; `perform` is the landing of
the commands the door lands itself, given the components the daemon holds.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from core.kernel.config import Config, get_config
from core.query import AMBASSADOR, AMBASSADOR_OVERLAY, OPERATOR, Grant
from core.sentence import ast
from core.sentence.plan import Plan
from core.sentence.types import IllScopedSentence, Sort

SPOOL = "door"

# The roles the door knows and the grant each speaks under (dn-ingest-door D3, §8): the agents'
# surface holds the Ambassador's grant, the owner's CLI the operator's. A role nothing writes for
# is not listed: a spool directory is a grant, and an idle grant is a hole.
_ROLE_GRANTS: dict[str, str] = {"ambassador": "ambassador", "cli": "operator"}
# The roles whose spool the palace group may write: the agents run under their own account
# (plane-principals), and the Ambassador's grant is the least the door gives. The operator's
# spool is the owner's account's alone.
_SHARED_ROLES: frozenset[str] = frozenset({"ambassador"})

_RID = re.compile(r"[0-9a-f]{16}")                      # a request id: the file's name
_NAME = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.\-]*")      # a conversation or turn name: no path
MAX_SENTENCE_BYTES = 32 * 1024      # a command longer than this is refused at the surface
MAX_REQUEST_BYTES = 64 * 1024       # a request file larger than this is rejected by the daemon
MAX_SPOOLED = 256                   # a surface refuses to add to a spool already this deep
SCAN_MAX = 4096                     # the entries of a spool the drain lists a tick
RELATE_PAIRS_MAX = 50               # `relate pairs <n>` above this is refused (a model call a pair)
PRUNE_AFTER_S = 7 * 24 * 3600       # receipts, rejected files and failed copies are kept a week
ROOT_MODE = 0o755                   # the spool root: the daemon adds every entry
SHARED_MODE = 0o3770                # the agents' spool: the group writes, the sticky bit guards
PRIVATE_MODE = 0o700                # the operator's spool: the owner's account alone
SHARED_INNER_MODE = 0o2750          # the agents' `receipts/`: the group reads its receipts
PRIVATE_INNER_MODE = 0o700          # every `queued/` and `rejected/`, and the operator's receipts
_EVERYONE_GROUPS = frozenset({"staff", "everyone", "users"})   # never the agents' spool's group
_INNER = ("queued", "receipts", "rejected")


class Busy(RuntimeError):
    """The role's spool, or its share of the queue, is full: refused now, not queued for later."""


class UnsupportedCommand(NotImplementedError):
    """Well-typed and admitted, but this build has no landing for it yet; the message says
    which step wires it."""


def grant_for(role: str) -> Grant:
    """The grant a role speaks under at the door. An unknown role is refused, never defaulted."""
    kind = _ROLE_GRANTS.get(role)
    if kind == "operator":
        return OPERATOR
    if kind == "ambassador":
        return AMBASSADOR_OVERLAY if get_config().query.hypotheticals else AMBASSADOR
    raise IllScopedSentence(f"the door knows no role {role!r}; one of "
                            f"{', '.join(sorted(_ROLE_GRANTS))}")


@dataclass(frozen=True)
class Request:
    """A command as spooled: its id, the role of the spool it sits in, the sentence, the time."""

    id: str
    role: str
    sentence: str
    at: str

    @property
    def digest(self) -> str:
        """The sentence's digest: what the queue carries, and what the handler checks the queued
        file against before it lands (the review's finding 7)."""
        return sentence_digest(self.sentence)


def sentence_digest(sentence: str) -> str:
    return hashlib.sha256(sentence.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Receipt:
    """What the door reports: the request, its role, its kind, its state (`spooled`, `queued`,
    `landed`, `refused`, `failed`), the job id once enqueued, and what landed or why not. The
    sentence is not repeated here: the request file holds it, the receipt names it."""

    request: str
    role: str
    kind: str
    state: str
    job: int | None = None
    detail: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {"request": self.request, "role": self.role, "kind": self.kind,
                               "state": self.state}
        if self.job is not None:
            out["job"] = self.job
        if self.detail:
            out["detail"] = dict(self.detail)
        return out


def _utcnow() -> str:
    return datetime.now(UTC).replace(tzinfo=None).isoformat(timespec="seconds")


def spool_root(cfg: Config) -> Path:
    return Path(cfg.interface.handoff_dir) / SPOOL


Report = Callable[[str], None]
_WARNED: set[str] = set()


def _warn_once(say: Report | None, key: str, message: str) -> None:
    """A misconfigured spool is reported once a process, not once a tick."""
    if say is not None and key not in _WARNED:
        _WARNED.add(key)
        say(message)


def roles() -> tuple[str, ...]:
    """The roles the door knows, in the order the drain serves them."""
    return tuple(sorted(_ROLE_GRANTS))


def _mode(role: str | None, sub: str = "", *, shared_group: bool = True) -> int:
    """A spool directory's mode: the root, a role's spool, or one of its subdirectories. Only the
    agents' spool is the group's to write and only their receipts the group's to read, and only
    when the group is a dedicated one (`shared_group`); a staged request (`queued/`) and a
    rejected file are the daemon's alone, so no writer reads another's text or writes into them."""
    if role is None:
        return ROOT_MODE
    shared = role in _SHARED_ROLES and shared_group
    if sub:
        return SHARED_INNER_MODE if shared and sub == "receipts" else PRIVATE_INNER_MODE
    return SHARED_MODE if shared else PRIVATE_MODE


def _group_name(gid: int) -> str:
    import grp

    try:
        return grp.getgrgid(gid).gr_name
    except KeyError:
        return str(gid)


def _make_dir(d: Path, mode: int) -> None:
    """Make one directory with its mode (without the setgid bit where it is not the maker's to
    set). An existing entry is left as it is, a symlink included: the health check judges it."""
    if os.path.lexists(d):
        return
    d.mkdir()
    for m in (mode, mode & ~stat.S_ISGID, mode & 0o777):
        try:
            os.chmod(d, m)
            return
        except OSError:
            continue


def _check_dir(d: Path, *, group_writes: bool) -> str | None:
    """Why the daemon will not drain through `d`, or `None`: a real directory (a symlink is not
    one), owned by the daemon's own account, writable by no other, and by the group only where
    the group writes."""
    try:
        st = os.lstat(d)
    except OSError as e:
        return f"{d}: {type(e).__name__}"
    if not stat.S_ISDIR(st.st_mode):
        return f"{d} is not a directory (a symlink is never followed)"
    if st.st_uid != os.getuid():
        return f"{d} is owned by uid {st.st_uid}, not the daemon's {os.getuid()}"
    if st.st_mode & stat.S_IWOTH or (st.st_mode & stat.S_IWGRP and not group_writes):
        return f"{d} is writable by {'others' if st.st_mode & stat.S_IWOTH else 'its group'}"
    return None


def _real_dir(d: Path) -> bool:
    try:
        return stat.S_ISDIR(os.lstat(d).st_mode)
    except OSError:
        return False


def _check_group(d: Path) -> str | None:
    """Why a group-writable spool's group will not do, or `None`: it must be the handoff
    directory's group, the one the owner gave the agents' writers, and never a group every local
    account is in. A spool the group cannot write needs no group."""
    try:
        st, parent = os.lstat(d), os.stat(d.parent.parent)
    except OSError as e:
        return f"{d}: {type(e).__name__}"
    if not st.st_mode & stat.S_IWGRP:
        return None
    name = _group_name(st.st_gid)
    if st.st_gid != parent.st_gid:
        return f"{d}'s group {name} is not the handoff directory's"
    if name in _EVERYONE_GROUPS:
        return f"{d}'s group {name} holds every local account"
    return None


def _make_spools(cfg: Config) -> None:
    """Make what is missing, and nothing beneath an entry that is not a real directory: a
    symlink in a spool's place is never made into, so nothing is created where it points."""
    root = spool_root(cfg)
    root.parent.mkdir(parents=True, exist_ok=True)      # the interface handoff directory
    _make_dir(root, ROOT_MODE)
    if not _real_dir(root):
        return
    # the agents may write their spool only through a dedicated group (the handoff directory's,
    # which the spools inherit); under a group every account is in, it is the owner's alone
    shared = _group_name(os.stat(root).st_gid) not in _EVERYONE_GROUPS
    for role in roles():
        _make_dir(root / role, _mode(role, shared_group=shared))
        if not _real_dir(root / role):
            continue
        for sub in _INNER:
            _make_dir(root / role / sub, _mode(role, sub, shared_group=shared))


def ensure_spools(cfg: Config, *, report: Report | None = None) -> list[str]:
    """The daemon's own making of the spools, each with its mode, and the roles whose spools are
    sound to drain: the root, the role's spool and its three subdirectories each pass
    `_check_dir`. A role that does not is reported once and not drained; the others are."""
    try:
        _make_spools(cfg)
    except OSError as e:
        _warn_once(report, f"make:{spool_root(cfg)}",
                   f"door: cannot make the spools ({type(e).__name__}: {e})")
    root = spool_root(cfg)
    why = _check_dir(root, group_writes=False)
    if why is not None:
        _warn_once(report, f"bad:{why}", f"door: nothing is drained: {why}")
        return []
    healthy = []
    for role in roles():
        why = (_check_dir(root / role, group_writes=role in _SHARED_ROLES)
               or (_check_group(root / role) if role in _SHARED_ROLES else None)
               or next((w for sub in _INNER
                        if (w := _check_dir(root / role / sub, group_writes=False))), None))
        if why is None:
            healthy.append(role)
        else:
            _warn_once(report, f"bad:{why}", f"door: the {role} spool is not drained: {why}")
    return healthy


def _atomic_write_json(path: Path, obj: Mapping[str, Any]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(dict(obj), ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)                       # a rename is atomic; the daemon never reads a partial


def _read_bounded(path: Path, cap: int) -> tuple[bytes, os.stat_result]:
    """A file's bytes through a descriptor that follows no link and blocks on nothing: a regular
    file under `cap` bytes, read to at most `cap + 1`. Raises on anything else."""
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode):
            raise ValueError("not a regular file")
        if st.st_size > cap:
            raise ValueError(f"{st.st_size} bytes, over the cap of {cap}")
        chunks, n = [], 0
        while n <= cap:
            chunk = os.read(fd, cap + 1 - n)
            if not chunk:
                break
            chunks.append(chunk)
            n += len(chunk)
        data = b"".join(chunks)
        if len(data) > cap:
            raise ValueError(f"grew past the cap of {cap} while read")
        return data, st
    finally:
        os.close(fd)


# ── the kinds ──────────────────────────────────────────────────────────────────────────────────

# The commands the door lands itself (`perform`), as the kinds the daemon registers for it.
DOOR_KINDS: frozenset[str] = frozenset({"ingest", "capture", "link", "relate", "code_observe"})


def kind_of(command: ast.Command) -> tuple[str, dict[str, Any]]:
    """The queue kind a command compiles to, and the kind's usual payload (dn-ingest-door D5):
    today's kinds stay the queue's kinds, so their tiers, priorities, coalescing and the orphan
    sweep keep their meaning; the door's own kinds carry the request id, added by the drain. A
    command whose atom this build would ignore is refused by name, never landed as less than it
    said (the review's finding 14)."""
    match command:
        case ast.Sync(lane=lane):
            return ({"vault": "vault_sync", "chat": "chat_sync", "code": "code_sync",
                     "dialogue": "dialogue_sync"}[lane], {})
        case ast.Dream():
            return ("dream", {})
        case ast.Curate():
            return ("curate", {})
        case ast.Research():
            raise UnsupportedCommand("research rides the airlock with de-identified criteria; the "
                                     "door's request for it is wired in DO-3b (dn-ingest-door §4)")
        case ast.Ingest(source=src):
            match src.kind:
                case ast.SourceKind.NOTE | ast.SourceKind.TURN | ast.SourceKind.DOC:
                    return ("ingest", {})
                case ast.SourceKind.PAPER:
                    raise UnsupportedCommand("a paper's manifest ingest is an owner script today "
                                             "(scripts/curate_local.py); the door's landing for it "
                                             "is wired in DO-3b")
                case ast.SourceKind.CODE:
                    if src.atom:
                        raise UnsupportedCommand("a commit's backfill rides code_backfill; the "
                                                 "door's request for one commit is wired in DO-3b")
                    return ("code_sync", {})
                case ast.SourceKind.TRANSCRIPT:
                    if src.atom:
                        raise UnsupportedCommand("one session's transcript rides chat_sync, which "
                                                 "syncs every session; the door's request for one "
                                                 "session is wired in DO-3b")
                    return ("chat_sync", {})
        case ast.Observe(commit=commit):
            if commit:
                raise UnsupportedCommand("the code sensor observes the head; the door's request "
                                         "for one commit is wired in DO-3b")
            return ("code_observe", {})
        case ast.RelatePass():
            return ("relate", {})
        case ast.Link():
            return ("link", {})
        case ast.Capture():
            return ("capture", {})
    raise UnsupportedCommand(f"no kind for {command!r}")  # pragma: no cover


# ── the spool ──────────────────────────────────────────────────────────────────────────────────


def write_request(cfg: Config, *, role: str, plan: Plan) -> Receipt:
    """Spool a compiled command for `role`. The plan was compiled under `grant_for(role)` by the
    surface (the first check); the daemon compiles it again under the spool's grant (the second).
    A command this build cannot land, one the landing would refuse, and one for a spool already
    `MAX_SPOOLED` deep are refused here, before anything is written."""
    if plan.sort is not Sort.EVENT or not isinstance(plan.term, ast.Do):
        raise ValueError(f"not a command: {plan.sentence!r}")
    if role not in _ROLE_GRANTS:
        raise IllScopedSentence(f"the door knows no role {role!r}")
    if len(plan.sentence.encode("utf-8")) > MAX_SENTENCE_BYTES:
        raise ValueError(f"a command is at most {MAX_SENTENCE_BYTES} bytes")
    check_command(plan.term.command, role)
    kind, _ = kind_of(plan.term.command)
    spool = spool_root(cfg) / role
    if not os.path.lexists(spool):
        handoff = Path(cfg.interface.handoff_dir)
        handoff.mkdir(parents=True, exist_ok=True)
        if handoff.stat().st_uid != os.getuid():
            raise PermissionError("the door's spools are the daemon's to make, and it has not "
                                  "made them yet: start the daemon")
        _make_spools(cfg)           # the daemon's own account: what the daemon would make
    if not _real_dir(spool):
        raise PermissionError(f"{spool} is not a directory; the door's spools are")
    depth = sum(1 for e in os.scandir(spool) if e.name.endswith(".json"))
    if depth >= MAX_SPOOLED:
        raise Busy(f"the {role} spool holds {depth} requests; the daemon drains it each tick")
    at = _utcnow()
    rid = hashlib.sha256(
        "\x00".join([role, plan.sentence, at, os.urandom(8).hex()]).encode()).hexdigest()[:16]
    doc = {"id": rid, "sentence": plan.sentence, "at": at}
    size = len(json.dumps(doc, ensure_ascii=False).encode("utf-8"))
    if size > MAX_REQUEST_BYTES:     # escaping grows a text: the file is what the daemon reads
        raise ValueError(f"a command's request is at most {MAX_REQUEST_BYTES} bytes as written; "
                         f"this one is {size}")
    _atomic_write_json(spool / f"{rid}.json", doc)
    return Receipt(rid, role, kind, "spooled")


def waiting(cfg: Config, healthy: list[str]) -> list[str]:
    """The sound roles whose spool holds a request file: what the drain looks at before it reads
    the queue, so an idle tick costs a directory listing per role and nothing more."""
    out = []
    for role in healthy:
        with os.scandir(spool_root(cfg) / role) as it:
            if any(e.name.endswith(".json") for e in it):
                out.append(role)
    return out


def _request_names(d: Path, say: Report) -> list[tuple[int, str]]:
    """A spool's request files as (mtime, name), unread: at most `SCAN_MAX` a tick, so a flood
    costs a bounded listing (the excess is reported once and served on later ticks)."""
    out: list[tuple[int, str]] = []
    try:
        with os.scandir(d) as it:
            for e in it:
                if not e.name.endswith(".json"):
                    continue
                if len(out) >= SCAN_MAX:
                    _warn_once(say, f"flood:{d}", f"door: {d} holds more than {SCAN_MAX} "
                                                  "requests; they are served a slice a tick")
                    break
                try:
                    out.append((e.stat(follow_symlinks=False).st_mtime_ns, e.name))
                except OSError:
                    continue
    except OSError:
        return []
    return sorted(out)


def pending(cfg: Config, healthy: list[str], *, limit: int = 64, per_role: int = 32,
            report: Report | None = None) -> list[tuple[Path, Request]]:
    """The requests waiting in the sound spools, oldest first within a role, at most `per_role`
    of a role and `limit` in all. The role is the spool directory's name, never a field of the
    file: the filesystem is the authenticator. A file the daemon does not trust
    (`_load_request`) is moved to `rejected/` and reported."""
    say: Report = report or (lambda _m: None)
    out: list[tuple[Path, Request]] = []
    for role in healthy:
        spool, taken = spool_root(cfg) / role, 0
        for _, name in _request_names(spool, say):
            if len(out) >= limit or taken >= per_role:
                break
            request = _load_request(spool / name, role, say, cfg)
            if request is not None:
                out.append((spool / name, request))
                taken += 1
    return out


def _load_request(f: Path, role: str, say: Report, cfg: Config | None = None) -> Request | None:
    """A request as the daemon trusts it: read through `_read_bounded` (a regular file under the
    cap, no link followed, nothing blocked on), with one link (a writer keeping a second name could
    change it after the check), written, in the operator's spool, by the daemon's own account;
    JSON of an object whose id is sixteen hex digits and is the file's name, with a sentence.
    Anything else is rejected: moved aside, reported, never read again."""
    try:
        data, st = _read_bounded(f, MAX_REQUEST_BYTES)
        if st.st_nlink != 1:
            raise ValueError(f"{st.st_nlink} links; a request has one")
        if role not in _SHARED_ROLES and st.st_uid != os.getuid():
            raise ValueError(f"written by uid {st.st_uid}; the {role} spool is the daemon "
                             "account's alone")
        doc = json.loads(data.decode("utf-8"))
        if not isinstance(doc, dict):
            raise ValueError("not an object")
        rid, sentence = doc.get("id"), doc.get("sentence")
        if not (isinstance(rid, str) and _RID.fullmatch(rid) and rid == f.stem):
            raise ValueError("the id is not the file's name")
        if not isinstance(sentence, str):
            raise ValueError("no sentence")
        return Request(rid, role, sentence, str(doc.get("at") or ""))
    except Exception as e:                      # a foreign file must never stop the daemon
        reject(f, say, f"{type(e).__name__}: {e}", cfg=cfg, role=role)
        return None


def reject(f: Path, say: Report, why: str, *, cfg: Config | None = None,
           role: str | None = None) -> None:
    """Move a request file the daemon will not act on to its spool's `rejected/` (the daemon's
    alone), under a name no earlier rejection holds, and say so; a file the daemon cannot move
    is reported once, not every tick. A file whose name is a request id no receipt names yet is
    receipted as refused, so its writer learns why: a seen id's receipt is never overwritten."""
    dest = f.parent / "rejected" / f.name
    n = 0
    while os.path.lexists(dest) and n < 100:
        n += 1
        dest = f.parent / "rejected" / f"{f.name}.{n}"
    try:
        f.replace(dest)
        say(f"door: {f} rejected ({why}); moved to {dest}")
    except OSError as e:
        _warn_once(say, f"stuck:{f}", f"door: {f} rejected ({why}) and could not be moved: {e}")
    rid = f.name.removesuffix(".json")
    if cfg is not None and role in _ROLE_GRANTS and _RID.fullmatch(rid) \
            and read_receipt(cfg, role, rid) is None:
        try:
            write_receipt(cfg, Receipt(rid, role, "", "refused", detail={"reason": why}))
        except OSError:
            pass


def seen(cfg: Config, role: str, rid: str) -> bool:
    """Whether a request id was drained before: a receipt names it, in any state but `failed`.
    An id is minted once, so a request file bearing a seen id is a replay (or the leftover of a
    crash after its receipt), and is rejected before it can enqueue a second job or overwrite the
    first one's receipt. A failed request may be spooled again."""
    receipt = read_receipt(cfg, role, rid)
    return receipt is not None and receipt.state != "failed"


def _queued_path(cfg: Config, role: str, rid: str) -> Path:
    if role not in _ROLE_GRANTS:
        raise IllScopedSentence(f"the door knows no role {role!r}")
    if not _RID.fullmatch(rid):
        raise IllScopedSentence(f"not a request id: {rid!r}")
    return spool_root(cfg) / role / "queued" / f"{rid}.json"


def stage(cfg: Config, request: Request) -> Path:
    """The daemon's own copy of a validated request, in `queued/`, which only the daemon writes:
    the job names it, and the writer's file is no longer read."""
    path = _queued_path(cfg, request.role, request.id)
    _atomic_write_json(path, {"id": request.id, "sentence": request.sentence, "at": request.at})
    return path


def read_request(cfg: Config, role: str, rid: str) -> Request:
    """A staged request, by the role of its spool and its id; both are checked before either
    names a path, the file is read as `_load_request` reads, and its id must be its name."""
    data, _ = _read_bounded(_queued_path(cfg, role, rid), MAX_REQUEST_BYTES)
    doc = json.loads(data.decode("utf-8"))
    if (not isinstance(doc, dict) or doc.get("id") != rid
            or not isinstance(doc.get("sentence"), str)):
        raise IllScopedSentence(f"the queued request {rid} is not the request it names")
    return Request(rid, role, str(doc["sentence"]), str(doc.get("at") or ""))


def discard_queued(cfg: Config, role: str, rid: str) -> None:
    """Remove a staged request once its receipt is terminal: the text's one home was the request
    file, and a landed or refused command needs it no more. A failed one stays (a week), for the
    operator to spool again."""
    _queued_path(cfg, role, rid).unlink(missing_ok=True)


def write_receipt(cfg: Config, receipt: Receipt) -> Path:
    if receipt.role not in _ROLE_GRANTS or not _RID.fullmatch(receipt.request):
        raise IllScopedSentence(f"no receipt for {receipt.request!r} of role {receipt.role!r}")
    path = spool_root(cfg) / receipt.role / "receipts" / f"{receipt.request}.json"
    _atomic_write_json(path, receipt.to_dict())
    return path


def read_receipt(cfg: Config, role: str, rid: str) -> Receipt | None:
    if role not in _ROLE_GRANTS or not _RID.fullmatch(rid):
        return None
    path = spool_root(cfg) / role / "receipts" / f"{rid}.json"
    try:
        data, _ = _read_bounded(path, MAX_REQUEST_BYTES)
    except (OSError, ValueError):
        return None
    doc = json.loads(data.decode("utf-8"))
    return Receipt(str(doc["request"]), str(doc["role"]), str(doc["kind"]), str(doc["state"]),
                   doc.get("job"), dict(doc.get("detail") or {}))


def prune(cfg: Config, *, now: float | None = None, max_age_s: float = PRUNE_AFTER_S) -> int:
    """Remove what the door keeps only for a while: receipts and rejected files older than
    `max_age_s`, and the staged copies of failed requests, or of requests no receipt names, as
    old. A staged copy whose job may still run is never removed, and only regular files are
    touched. Returns how many were removed."""
    cutoff = (now if now is not None else time.time()) - max_age_s
    removed = 0
    for role in roles():
        base = spool_root(cfg) / role
        for sub in ("queued", "receipts", "rejected"):    # a copy is judged by its receipt first
            d = base / sub
            if not d.is_dir() or d.is_symlink():
                continue
            with os.scandir(d) as it:
                old = [e for e in it if e.is_file(follow_symlinks=False)
                       and e.stat(follow_symlinks=False).st_mtime < cutoff]
            for e in old:
                if sub == "queued":
                    receipt = read_receipt(cfg, role, Path(e.name).stem)
                    if receipt is not None and receipt.state != "failed":
                        continue          # its job may still run; an orphan copy goes too
                try:
                    Path(e.path).unlink(missing_ok=True)
                    removed += 1
                except OSError:
                    continue
    return removed


# ── the landing ────────────────────────────────────────────────────────────────────────────────


@dataclass
class Landers:
    """What the door lands with, built by the daemon once: each is a callable or `None`, and a
    missing one is built from the config on first use. Injectable, so the landing is tested with
    fakes and no store."""

    vault_sync: Any = None          # `VaultSync`: `sync_one(path)`, `in_scope(path)`
    capture: Any = None             # `DialogueCapture`: `capture_turn(...)`
    edges: Any = None               # the relation edge store: `all()`, `add(...)`
    curated: Callable[[list[Path]], Any] | None = None   # paths → a `CuratedReport`
    relate: Callable[[int | None], Any] | None = None    # pairs → a `RelateReport`


def perform(command: ast.Command, cfg: Config, landers: Landers | None = None,
            *, role: str = "cli") -> dict[str, Any]:
    """Land a command the door lands itself, under the one writer, and say what landed. The
    provenance of what lands is fixed by the kind: a turn and a capture are observed, a link is
    interpreted, a note is the owner's projection, a doc is curated; no word of the sentence
    decides it (dn-ingest-door D1, D8). `role` is the spool the request came from: the identities
    the door mints for turns are namespaced by it."""
    L = landers if landers is not None else Landers()
    check_command(command, role)
    match command:
        case ast.Ingest(source=src) if src.kind is ast.SourceKind.NOTE:
            # contained by the resolved vault, named as the rescan names it (under the vault's
            # path as configured), so a symlink on the vault's path never forks a note's identity
            configured = Path(str(cfg.ingestion.vault.path)).expanduser()
            vault = configured.resolve()
            target = Path(src.atom).expanduser()
            target = (target if target.is_absolute() else configured / target).resolve()
            if vault not in target.parents:
                raise IllScopedSentence(f"ingest note: {src.atom!r} is outside the vault; the "
                                        "door ingests the owner's notes from the vault only")
            path = configured / target.relative_to(vault)
            if L.vault_sync is None:
                from core.ingest.sync import build_vault_sync
                L.vault_sync = build_vault_sync(cfg)
            # the vault's own scope (its pattern and the excluded directories: `.recycle`, `bak`,
            # the assets) binds a single note as it binds the rescan (the review's finding 8)
            if not L.vault_sync.in_scope(path):
                raise IllScopedSentence(f"ingest note: {src.atom!r} is outside the vault's scope "
                                        "(its note pattern and excluded directories)")
            outcome = L.vault_sync.sync_one(path)
            entry = L.vault_sync.catalog.get(str(path))
            digest = entry.digest if entry is not None else ""
            return {"path": str(path), "outcome": str(getattr(outcome, "value", outcome)),
                    "digest": digest,
                    "attestations": _attestations_of(getattr(L.vault_sync, "attestor", None),
                                                     digest, "ingest_note")}
        case ast.Ingest(source=src) if src.kind is ast.SourceKind.TURN:
            return _capture(L, cfg, src.text, src.atom, src.turn, role)
        case ast.Capture(text=text, conversation=conv):
            turn = hashlib.sha256(text.encode()).hexdigest()[:16]
            return _capture(L, cfg, text, conv or "captures", turn, role)
        case ast.Ingest(source=src) if src.kind is ast.SourceKind.DOC:
            from core.ingest.curated import curated_sources
            from core.kernel.config import REPO_ROOT
            root = Path(REPO_ROOT).resolve()
            path = (root / src.atom).resolve()
            if root not in path.parents:
                raise IllScopedSentence(f"ingest doc: {src.atom!r} is outside the repository")
            # the allow-list is read on every call, never once per lander (the review's finding 1)
            if path not in set(curated_sources(root)):
                raise IllScopedSentence(f"ingest doc: {src.atom!r} is not a curated source "
                                        "(the Constitution, the Conventions, docs/)")
            if L.curated is None:
                L.curated = _curated_lander(cfg, root)
            report = L.curated([path])
            return {"path": str(path), "report": str(report)}
        case ast.Link(a=a, b=b, relation=relation):
            from core.relations import RELATIONS
            if relation not in RELATIONS:
                raise ValueError(f"link: relation must be one of {list(RELATIONS)}")
            if L.edges is None:
                from core.stores.edges import open_edge_store
                L.edges = open_edge_store(cfg)
            from core.query import QueryEngine
            engine = QueryEngine(cfg)
            notes, _, _ = engine.note_graph()
            da, db = (notes[engine.index_of(notes, t)]["digest"] for t in (a, b))
            # D8: an interpreted link never overwrites an authored edge on the pair (the edge
            # store's key has no provenance, the audit's defect 3), so the pair is refused here
            for e in L.edges.all():
                if {e.u, e.v} == {da, db} and e.rel_type == relation \
                        and str(getattr(e, "provenance", "")) != "interpreted":
                    raise IllScopedSentence(
                        f"link: an authored {relation} edge already holds {a!r} and {b!r}; the "
                        "door never overwrites the owner's edge")
            sign, factor = RELATIONS[relation]
            L.edges.add(da, db, sign=sign, rel_type=relation, w=factor, provenance="interpreted")
            return {"linked": [a, b], "relation": relation, "provenance": "interpreted"}
        case ast.RelatePass(pairs=pairs):
            if L.relate is None:
                from core.relations import build_relation_detector
                L.relate = lambda n: build_relation_detector(
                    cfg, max_pairs=24 if n is None else n).run()
            return {"report": str(L.relate(pairs))}
    raise UnsupportedCommand(f"the door does not land {ast.describe_command(command)!r} itself; "
                             "its kind's own handler does, or DO-3b wires it")


def check_command(command: ast.Command, role: str) -> None:
    """What the door refuses of a well-typed, admitted command, at the surface (so the speaker
    hears it at once), at the drain and again at the landing: a turn's names that carry a path,
    and a relation pass over the cap."""
    match command:
        case ast.Ingest(source=src) if src.kind is ast.SourceKind.TURN:
            turn_ref(role, src.atom, src.turn)
        case ast.Capture(conversation=conv) if conv:
            turn_ref(role, conv, "0")
        case ast.RelatePass(pairs=pairs) if pairs is not None and pairs > RELATE_PAIRS_MAX:
            raise IllScopedSentence(f"relate: at most {RELATE_PAIRS_MAX} pairs a pass, one "
                                    f"model call each; {pairs} asked")


def turn_ref(role: str, conversation: str, turn: str) -> str:
    """The identity of a turn the door mints: under `dialogue/door/<role>/`, a namespace no
    other writer uses, so a command never names the owner's turns (`dialogue/<source>/<chat>/`)
    or another role's (the review's finding 2). The names carry no path."""
    for label, value in (("conversation", conversation), ("turn", turn)):
        if not _NAME.fullmatch(value):
            raise IllScopedSentence(f"{label} {value!r}: a name is letters, digits, `_`, `.` and "
                                    "`-`, never a path; the door's turns live under "
                                    "dialogue/door/<role>/")
    return f"door/{role}/{conversation}"


def _capture(L: Landers, cfg: Config, text: str, conversation: str, turn: str,
             role: str) -> dict[str, Any]:
    namespace = turn_ref(role, conversation, turn)
    if L.capture is None:
        from core.ingest.dialogue import build_dialogue_capture
        L.capture = build_dialogue_capture(cfg)
    digest, created = L.capture.capture_turn(text, conversation=namespace, turn_id=turn,
                                             role="assistant")          # observed, always
    return {"ref": f"dialogue/{namespace}/{turn}", "digest": digest, "created": created,
            "provenance": "observed",
            "attestations": _attestations_of(getattr(L.capture, "attestor", None), digest,
                                             "capture")}


def _attestations_of(attestor: Any, digest: str, action: str) -> list[str]:
    """The ids of the attestations of `action` that produced `digest`: the receipt's witnesses,
    which `witness "<id>"` dereferences (DOR-6). They are the record of the bytes landed, so
    when the same bytes landed before, by the same action, the earlier record is the witness.
    Empty without an attestor's store or a digest."""
    from core.ingest.landing import attested_by

    return attested_by(attestor, action, digest)


def _curated_lander(cfg: Config, root: Path) -> Callable[[list[Path]], Any]:
    from core.attestation import build_attestor
    from core.ingest.curated import ingest_curated
    from core.ingest.embed import build_embedder
    from core.kernel.stores.rawstore import RawStore
    from core.stores.catalog import VaultCatalog
    from core.stores.vectorstore import open_vector_store

    raw, store = RawStore(cfg.paths.raw_store), open_vector_store(cfg)
    embedder, catalog, attestor = build_embedder(cfg), VaultCatalog(cfg.paths.vault_catalog), \
        build_attestor(cfg)
    return lambda paths: ingest_curated(paths, raw, store, embedder, catalog, repo_root=root,
                                        attestor=attestor)
