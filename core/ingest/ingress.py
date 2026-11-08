"""The ingress: a command as a request, the daemon as the one writer (dn-ingress D3, D5, D7).

A surface that speaks a command (`do …`) compiles it under the grant of the **role** it speaks
for, and, if admitted, writes a **request** into its spool, a per-role directory under the
interface handoff directory (`cfg.interface.handoff_dir`; the daemon makes and owns the
spools, and only a role's own writers may write its spool, §5). The daemon drains the
spools each tick (`scheduler/ingress.py`), enqueues one job per request as the kind the command
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
copy (`stage`), so a writer's later change to its file changes nothing. The identities the ingress
mints for turns live under `dialogue/ingress/<role>/`, so no role's command can name the owner's
turns or another role's.

This module is core: it opens no queue and no store on its own, and imports no scheduler. The
scheduler's `drain_spool` and `ingress_handler` are the daemon's side; `perform` is the landing of
the commands the ingress lands itself, given the components the daemon holds.
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

from core.ingest.files import check_dir, daemon_uid, read_bounded, real_dir, written_by_one
from core.kernel.clearance import classes_of
from core.kernel.config import Config, get_config
from core.query import AMBASSADOR, AMBASSADOR_OVERLAY, OPERATOR, Grant
from core.sentence import ast
from core.sentence.plan import Plan
from core.sentence.types import IllScopedSentence, Sort

SPOOL = "ingress"
LEGACY_SPOOL = "door"       # the first form's spool directory, adopted into `SPOOL`

# The roles the ingress knows and the grant each speaks under (dn-ingress D3, §8): the agents'
# surface holds the Ambassador's grant, the owner's CLI the operator's. A role nothing writes for
# is not listed: a spool directory is a grant, and an idle grant is a hole.
_ROLE_GRANTS: dict[str, str] = {"ambassador": "ambassador", "cli": "operator"}
# The roles only the daemon's own jobs speak, and the grant each speaks under. No spool belongs to
# one, so no surface can speak it: the inbox's capture (dn-ingress-language §E13) runs under the
# Ambassador's grant, the least the ingress gives, and its role opens one source and writes one
# prefix (`core/ingest/table.py`).
# The open corpus's runner (dn-corpus-instance §3.2) speaks the corpus role under the same grant:
# its role opens the corpus streams and writes `corpus/` in the observed place alone.
_DAEMON_ROLES: dict[str, str] = {"inbox": "ambassador", "corpus": "ambassador"}
# The roles whose spool the palace group may write: the agents run under their own account
# (plane-principals), and the Ambassador's grant is the least the ingress gives. The operator's
# spool is the owner's account's alone.
_SHARED_ROLES: frozenset[str] = frozenset({"ambassador"})

_RID = re.compile(r"[0-9a-f]{16}")                      # a request id: the file's name
MAX_SENTENCE_BYTES = 32 * 1024      # a command longer than this is refused at the surface
MAX_REQUEST_BYTES = 64 * 1024       # a request file larger than this is rejected by the daemon
MAX_SPOOLED = 256                   # a surface refuses to add to a spool already this deep
SCAN_MAX = 4096                     # the entries of a spool the drain lists a tick
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


def grant_for(role: str) -> Grant:
    """The grant a role speaks under at the ingress, a spool's or one of the daemon's own jobs'.
    An unknown role is refused, never defaulted."""
    kind = _ROLE_GRANTS.get(role) or _DAEMON_ROLES.get(role)
    if kind == "operator":
        return OPERATOR
    if kind == "ambassador":
        return AMBASSADOR_OVERLAY if get_config().query.hypotheticals else AMBASSADOR
    raise IllScopedSentence(f"the ingress knows no role {role!r}; one of "
                            f"{', '.join(sorted({*_ROLE_GRANTS, *_DAEMON_ROLES}))}")


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
    """What the ingress reports: the request, its role, its kind, its state (`spooled`, `queued`,
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
    """The roles the ingress knows, in the order the drain serves them."""
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
    if not real_dir(root):
        return
    # the agents may write their spool only through a dedicated group (the handoff directory's,
    # which the spools inherit); under a group every account is in, it is the owner's alone
    shared = _group_name(os.stat(root).st_gid) not in _EVERYONE_GROUPS
    for role in roles():
        _make_dir(root / role, _mode(role, shared_group=shared))
        if not real_dir(root / role):
            continue
        for sub in _INNER:
            _make_dir(root / role / sub, _mode(role, sub, shared_group=shared))


_FILE = re.compile(r"[0-9a-f]{16}\.json")


def _adopt_legacy(cfg: Config, report: Report | None) -> None:
    """Take over what the first form's spool (`door/<role>/`) holds, so no request is lost and
    none runs twice: its receipts first (an id seen stays seen, and a surface waiting on one finds
    it), then the daemon's staged copies and the rejected files, the pending requests last. Only a
    regular file named as a request id moves, by rename (atomic, same filesystem); a name already
    present in the new spool is left where it is.

    Nothing is taken over that the drain would not trust where it lands (the security audit of
    2026-11-06): the legacy root, each role's spool and each of its directories must pass the
    steady-state checks (`check_dir`, `_check_group` for the agents' spool), and each file is read
    through its descriptor first, the daemon's own files (a receipt, a staged copy, a rejected
    file) as `written_by_one`, a pending request as the drain reads one (`_request_untrusted`).
    `data/handoff` is writable by its group, so an account in it could replace the whole `door/`
    tree with directories and files of its own: a planted receipt adopted would make a chosen id
    read as already landed, with the planter's detail. Anything that fails stays where it is and
    is reported once."""
    old, new = Path(cfg.interface.handoff_dir) / LEGACY_SPOOL, spool_root(cfg)
    if not os.path.lexists(old) or not real_dir(new):
        return
    why = check_dir(old)
    if why is not None:
        _warn_once(report, f"legacy:{old}",
                   f"ingress: the first form's spool is not adopted: {why}")
        return
    for role in roles():
        spool, shared = old / role, role in _SHARED_ROLES
        if not os.path.lexists(spool):
            continue
        why = check_dir(spool, group_writes=shared) or (_check_group(spool) if shared else None)
        if why is not None:
            _warn_once(report, f"legacy:{spool}", f"ingress: {spool} is not adopted: {why}")
            continue
        for sub in (*_INNER[::-1], ""):      # rejected, receipts, queued, then the requests
            src, dst = spool / sub, new / role / sub
            if not os.path.lexists(src) or not real_dir(dst):
                continue
            if sub and (why := check_dir(src)) is not None:
                _warn_once(report, f"legacy:{src}", f"ingress: {src} is not adopted: {why}")
                continue
            try:
                with os.scandir(src) as it:
                    names = [e.name for e in it if _FILE.fullmatch(e.name)]
            except OSError:
                continue
            for name in sorted(names):
                try:
                    _, st = read_bounded(src / name, MAX_REQUEST_BYTES)   # no link, regular, capped
                    why = written_by_one(st) if sub else _request_untrusted(st, role)
                    if why is None and os.path.lexists(dst / name):
                        why = f"{dst / name} exists"
                    if why is not None:
                        _warn_once(report, f"legacy:{src / name}",
                                   f"ingress: {src / name} not adopted: {why}")
                        continue
                    os.rename(src / name, dst / name)
                except (OSError, ValueError) as e:
                    _warn_once(report, f"legacy:{src / name}",
                               f"ingress: {src / name} not adopted ({type(e).__name__}: {e})")


def ensure_spools(cfg: Config, *, report: Report | None = None) -> list[str]:
    """The daemon's own making of the spools, each with its mode, and the roles whose spools are
    sound to drain: the root, the role's spool and its three subdirectories each pass
    `check_dir`. A role that does not is reported once and not drained; the others are."""
    try:
        _make_spools(cfg)
    except OSError as e:
        _warn_once(report, f"make:{spool_root(cfg)}",
                   f"ingress: cannot make the spools ({type(e).__name__}: {e})")
    root = spool_root(cfg)
    why = check_dir(root, group_writes=False)
    if why is not None:
        _warn_once(report, f"bad:{why}", f"ingress: nothing is drained: {why}")
        return []
    _adopt_legacy(cfg, report)
    healthy = []
    for role in roles():
        why = (check_dir(root / role, group_writes=role in _SHARED_ROLES)
               or (_check_group(root / role) if role in _SHARED_ROLES else None)
               or next((w for sub in _INNER
                        if (w := check_dir(root / role / sub, group_writes=False))), None))
        if why is None:
            healthy.append(role)
        else:
            _warn_once(report, f"bad:{why}", f"ingress: the {role} spool is not drained: {why}")
    return healthy


def _atomic_write_json(path: Path, obj: Mapping[str, Any]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(dict(obj), ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)                       # a rename is atomic; the daemon never reads a partial


# ── the kinds ──────────────────────────────────────────────────────────────────────────────────

SCRIPT_KIND = "script"
# The ingress's own kinds: a job that names a request staged in `queued/` (dn-ingress-language §E7).
INGRESS_KINDS: frozenset[str] = frozenset({SCRIPT_KIND})


def kind_of(do: ast.Do) -> tuple[str, dict[str, Any]]:
    """The queue kind a request takes, and the kind's usual payload: a bare call of a library
    script the table maps to one of the queue's own coalescing kinds is that kind, so it coalesces
    with the watcher's and the heartbeat's rows; every other request is a `script` job that names
    its staged copy (dn-ingress-language §E7)."""
    from core.ingest.table import COALESCING
    from core.sentence.script import CallScript

    r = do.request
    if isinstance(r, CallScript) and not r.args and not r.kwargs and r.name in COALESCING:
        return (COALESCING[r.name], {})
    return (SCRIPT_KIND, {})


def lane_of(do: ast.Do) -> str:
    """The quota lane a request counts against: the library scripts the table marks interactive
    (a capture) are interactive, so a role's syncs never hold its captures; the rest are bulk."""
    from core.ingest.table import INTERACTIVE
    from core.sentence.script import CallScript

    r = do.request
    return "interactive" if isinstance(r, CallScript) and r.name in INTERACTIVE else "bulk"


# ── the spool ──────────────────────────────────────────────────────────────────────────────────


def write_request(cfg: Config, *, role: str, plan: Plan) -> Receipt:
    """Spool a compiled request for `role`. The plan was compiled under `grant_for(role)` and
    checked under the role by the surface (the first check); the daemon compiles it again under
    the spool's grant (the second). A request for a spool already `MAX_SPOOLED` deep is refused
    here, before anything is written."""
    if plan.sort is not Sort.EVENT or not isinstance(plan.term, ast.Do):
        raise ValueError(f"not a request: {plan.sentence!r}")
    if role not in _ROLE_GRANTS:
        raise IllScopedSentence(f"the ingress knows no role {role!r}")
    if len(plan.sentence.encode("utf-8")) > MAX_SENTENCE_BYTES:
        raise ValueError(f"a request is at most {MAX_SENTENCE_BYTES} bytes")
    kind, _ = kind_of(plan.term)
    spool = spool_root(cfg) / role
    if not os.path.lexists(spool):
        handoff = Path(cfg.interface.handoff_dir)
        handoff.mkdir(parents=True, exist_ok=True)
        if handoff.stat().st_uid != os.getuid():
            raise PermissionError("the ingress's spools are the daemon's to make, and it has not "
                                  "made them yet: start the daemon")
        _make_spools(cfg)           # the daemon's own account: what the daemon would make
    if not real_dir(spool):
        raise PermissionError(f"{spool} is not a directory; the ingress's spools are")
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
                    _warn_once(say, f"flood:{d}", f"ingress: {d} holds more than {SCAN_MAX} "
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


def _request_untrusted(st: os.stat_result, role: str) -> str | None:
    """Why a request file, by its descriptor's `stat`, is not one the drain trusts, or `None`: one
    link (a writer keeping a second name could change it after the check), and, in a spool only the
    daemon's account writes (the operator's), written by that account."""
    if st.st_nlink != 1:
        return f"{st.st_nlink} links; a request has one"
    if role not in _SHARED_ROLES and st.st_uid != daemon_uid():
        return f"written by uid {st.st_uid}; the {role} spool is the daemon account's alone"
    return None


def _load_request(f: Path, role: str, say: Report, cfg: Config | None = None) -> Request | None:
    """A request as the daemon trusts it: read through `read_bounded` (a regular file under the
    cap, no link followed, nothing blocked on), with one link (a writer keeping a second name could
    change it after the check), written, in the operator's spool, by the daemon's own account;
    JSON of an object whose id is sixteen hex digits and is the file's name, with a sentence.
    Anything else is rejected: moved aside, reported, never read again."""
    try:
        data, st = read_bounded(f, MAX_REQUEST_BYTES)
        why = _request_untrusted(st, role)
        if why is not None:
            raise ValueError(why)
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
        say(f"ingress: {f} rejected ({why}); moved to {dest}")
    except OSError as e:
        _warn_once(say, f"stuck:{f}", f"ingress: {f} rejected ({why}) and could not be moved: {e}")
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
        raise IllScopedSentence(f"the ingress knows no role {role!r}")
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
    data, _ = read_bounded(_queued_path(cfg, role, rid), MAX_REQUEST_BYTES)
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
        data, _ = read_bounded(path, MAX_REQUEST_BYTES)
    except (OSError, ValueError):
        return None
    doc = json.loads(data.decode("utf-8"))
    return Receipt(str(doc["request"]), str(doc["role"]), str(doc["kind"]), str(doc["state"]),
                   doc.get("job"), dict(doc.get("detail") or {}))


def prune(cfg: Config, *, now: float | None = None, max_age_s: float = PRUNE_AFTER_S) -> int:
    """Remove what the ingress keeps only for a while: receipts and rejected files older than
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


# ── the landing: a script, evaluated and written ─────────────────────────────────────────────


def build_stores(cfg: Config, enqueue: Callable[..., int] | None = None) -> Any:
    """The stores the writer lands into, opened by the daemon, the one writer. The lexical index
    is opened under `[embedding] lazy` alone (dn-two-phase-ingestion D6), so an instance that
    embeds synchronously writes nothing it did not write before."""
    from core.attestation import build_attestor
    from core.ingest.embed import build_embedder
    from core.ingest.writer import Stores
    from core.kernel.stores.rawstore import RawStore
    from core.stores.catalog import VaultCatalog
    from core.stores.edges import open_edge_store
    from core.stores.lexical import open_lexical_store
    from core.stores.vectorstore import open_vector_store
    from core.stores.versions import open_version_store

    return Stores(raw=RawStore(cfg.paths.raw_store), plane=open_vector_store(cfg),
                  embedder=build_embedder(cfg), catalog=VaultCatalog(cfg.paths.vault_catalog),
                  versions=open_version_store(cfg), attestor=build_attestor(cfg),
                  edges=open_edge_store(cfg), enqueue=enqueue,
                  lexical=open_lexical_store(cfg) if cfg.embedding.lazy else None)


def reader(cfg: Config, role: str) -> Callable[[str], list[Any]]:
    """A nested sentence's evaluation, under the role's grant: the read half, whose hits come back
    as records whose strings are observed (dn-ingress-language §E11)."""
    def read(sentence: str) -> list[Any]:
        from dataclasses import fields as dc_fields

        from core.query import QueryEngine
        from core.sentence.execute import execute
        from core.sentence.grammar import is_request
        from core.sentence.interpret import OBSERVED, Origin, OStr, Record, ScriptError
        from core.sentence.plan import compile_sentence
        from core.sentence.universe import build

        if is_request(sentence):           # refused before it is compiled: it is not a reading
            raise ScriptError("a nested sentence reads; a request does not nest")
        plan = compile_sentence(sentence, grant_for(role), role=role)
        if plan.sort is Sort.EVENT:
            raise ScriptError("a nested sentence reads; a request does not nest")
        engine = QueryEngine(cfg)
        answer = execute(plan, build(engine, plan))
        out = []
        for h in answer.hits:
            origin = Origin("entry", "hit", str(getattr(h, "ref", "")),
                            str(getattr(h, "title", "")))
            rec: dict[str, Any] = {}
            for f in dc_fields(h):
                if f.name in ("provenance", "detail"):
                    continue                # a script reads no label (§E3), nor what holds one
                v = getattr(h, f.name)
                rec[f.name] = OStr(v, OBSERVED, origin) if isinstance(v, str) else v
            out.append(Record(rec))
        return out
    return read


def resolve(do: ast.Do, library: Callable[[str], Any] | None = None) -> tuple[Any, list[Any],
                                                                               dict[str, Any], str]:
    """The script a request runs, with its arguments: a library script's, or the inline one."""
    from core.sentence.script import CallScript, load

    r = do.request
    if isinstance(r, CallScript):
        return ((library or load)(r.name), [a.value for a in r.args],
                {k: v.value for k, v in r.kwargs}, r.name)
    return (r.script, [], {}, "")


MAX_RECEIPT_EFFECTS = 200     # the effects a receipt lists by name; the rest are counted


def perform(do: ast.Do, cfg: Config, role: str, *, stores: Any,
            library: Callable[[str], Any] | None = None, view: Any = None,
            budget: int | None = None, request: str | None = None,
            refresh: bool = False, batch: bool = False,
            lazy: bool | None = None) -> dict[str, Any]:
    """Run a request under the one writer: evaluate its script under the role (reading the
    palace, writing nothing) into a plan, then land the plan, each effect by the writer's rules
    (dn-ingress-language §E5). `request` is the request's id, so the jobs its plan starts start
    once however often it runs; `refresh` runs a structured source's edge reader before its
    first read, which only the daemon's own syncs and the owner's CLI ask for; `batch` lands a
    plan of fresh stores on distinct paths a stage at a time (`Writer.land_batch`, the bulk path
    of dn-corpus-instance §5.2); `lazy` lands each store complete without its plane rows, which
    the embed drain derives from the raw store (`Writer.lazy`, dn-two-phase-ingestion), and is
    the instance's `[embedding] lazy` unless the caller says otherwise. Returns what the receipt
    says: each effect's outcome, counted by status, those that changed or were refused named, and
    the work charged (§E10)."""
    from core.ingest.readers import PalaceView
    from core.ingest.table import build_table
    from core.ingest.writer import Writer
    from core.sentence.interpret import Evaluator, Meter
    from core.sentence.script import load

    table = build_table(cfg)
    script, args, kwargs, name = resolve(do, library)
    meter = Meter(budget if budget is not None else table.roles[role].budget)
    v = view if view is not None else PalaceView(table, role, stores.catalog,
                                                 query=reader(cfg, role), refresh=refresh)
    plan = Evaluator(v, role, meter, library=library or load).run(script, args, kwargs, name=name)
    reads = frozenset().union(*(classes_of(s.sigma.strata) for s in grant_for(role).scopes))
    writer = Writer(table, role, stores, has=v.has, meter=meter, request=request, reads=reads,
                    batch=batch, lazy=bool(cfg.embedding.lazy) if lazy is None else lazy)
    outcomes = writer.land(plan)
    if hasattr(v, "landed"):
        v.landed(outcomes)
    counts: dict[str, int] = {}
    for o in outcomes:
        counts[o.status] = counts.get(o.status, 0) + 1
    named = [o.to_dict() for o in outcomes if o.status != "unchanged"]
    out = {"effects": counts, "changed": named[:MAX_RECEIPT_EFFECTS],
           "more": max(0, len(named) - MAX_RECEIPT_EFFECTS), "work": meter.used}
    if writer.timing:
        out["timing"] = {k: round(v, 3) for k, v in writer.timing.items()}
    return out


def run_library(cfg: Config, name: str, kwargs: Mapping[str, Any] | None = None, *,
                role: str = "cli", stores: Any = None, refresh: bool = True,
                batch: bool = False, lazy: bool | None = None) -> dict[str, Any]:
    """A library script run in this process, as the owner's CLI and scripts run one behind the
    live-daemon guard: compiled and admitted under the role's grant as a request is, then
    evaluated and landed by the writer, its structured sources refreshed first (unless
    `refresh` is off), a plan of fresh stores a stage at a time when `batch` is on, lazily
    when `lazy` says so (the instance's `[embedding] lazy` when it says nothing)."""
    from core.sentence.plan import compile_sentence
    from core.sentence.script import quote

    def lit(v: Any) -> str:
        if isinstance(v, str):
            return quote(v)
        if v is None or isinstance(v, bool):
            return "none" if v is None else str(v).lower()
        return str(v)

    args = ", ".join(f"{k}: {lit(v)}" for k, v in (kwargs or {}).items())
    text = f"do {name}({args})" if args else f"do {name}"
    plan = compile_sentence(text, grant_for(role), role=role)
    assert isinstance(plan.term, ast.Do)
    return perform(plan.term, cfg, role, stores=stores if stores is not None else build_stores(cfg),
                   refresh=refresh, batch=batch, lazy=lazy)
