"""The landing log: the catalog's past (dn-temporal-snapshot §3.2, stage SN-1).

The catalog is rewritten in place, so on its own it holds no past: which digest a path held
when, and whether it was active. This log is that past. It lives in the catalog's own file, and
only the catalog's writing methods append to it, in the transaction of the row each writes, so the
key and its log rows land together and no caller can write one without the other (ING-7's order
is unchanged: the key last, now two rows of one transaction). The catalog is the fold of the log,
and the state of a path at a past position is the same fold of a prefix (SNP-5).

**Chains.** A chain is an append order with an integer id that is never changed and is given
once while the log's tables stand (a rollback that drops them begins the ids again,
dn-temporal-snapshot §12), and it holds one provenance class, which is its label in
`landing_chains`. A relabel of a class rewrites that label and no row of the log, so it moves no
position and breaks no hash; after a merge a class has two chains and the read of a class is the
union of its chains' reads. A path's events stay in the chain that holds its last event; a path
that changes class leaves its chain with a `leave` row and lands in a chain of its new class.

**Rows.** `genesis` and `horizon` open a chain (§8: the positions before a horizon are under
it); `store` is a landing; `retire` the tombstone of an identity no other active path holds;
`move` a tombstone that leaves the identity at another path (the second half of a rename), or
the identity a re-key takes off a path; `leave` the row that closes a path in a chain when the
path takes another class. A row's `commitment` is SHA-256 over a random salt and the canonical
JSON of its fields, and its `hash` is SHA-256 over the previous row's hash and the commitment, so
a purge can empty a row and keep the chain (SNP-9). `closed_at` is the position of the path's
next event in the chain, written after the row and a function of the rows (SNP-5).

**The key of a path.** A row names its path also by `path_key`, a keyed hash, which is what a
read by path seeks on and the one name a purged row keeps, so a hole still shadows the path's
earlier versions (§6.1). Its key is derived from two halves: the chain's 32 random bytes in the
file, and the instance's landing-log secret, which is never in the file: it is read from the
environment (`get_secret`, Keychain-backed in the owner's setup, the instance's own item under a
named instance). Whatever appends a row, or seeks a path's rows by their key, needs the secret:
the genesis, a `record` or a `tombstone` that changes the map, a re-key, `remove`, and the two
reads by path. Without it they refuse, loudly, before anything is written; no row is ever
written unkeyed. A relabel and a purge by digest need none: they append no row, and the purge
finds its rows by the digest, by the names they carry and by the keys the emptied rows keep. A
secret that is not the one a chain was written with is refused as well, by the chain's
`key_check`, so a chain is never keyed two ways.

Nothing reads the log yet: the reads below are the ones the later stages build on.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import sqlite3
from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

# The Keychain/env item the instance's landing-log secret is read from (a named instance reads
# `<id>.landing-log-key`, `InstanceConfig.secret`): 32 random bytes or more, as hex digits.
LANDING_LOG_KEY = "landing-log-key"

KINDS = ("genesis", "store", "retire", "move", "leave", "horizon")

DDL = """
CREATE TABLE IF NOT EXISTS landing_chains (
    chain     INTEGER PRIMARY KEY,  -- the chain's id: never reused, never changed
    class     TEXT    NOT NULL,     -- the provenance class it holds now; a relabel rewrites this
    secret    BLOB    NOT NULL,     -- 32 random bytes: the chain's half of the key of path_key
    key_check BLOB    NOT NULL      -- hmac-sha256(the chain's key, 'key check')
);
CREATE TABLE IF NOT EXISTS landings (
    chain       INTEGER NOT NULL,   -- landing_chains.chain
    seq         INTEGER NOT NULL,   -- the position in the chain, from 1, never given twice
    kind        TEXT    NOT NULL,   -- genesis | store | retire | move | leave | horizon
    path_key    BLOB,               -- hmac-sha256(the chain's key, source_path): kept by a hole
    source_path TEXT,               -- NULL once purged
    doc_id      TEXT,               -- the identity the event belongs to; NULL once purged
    version     INTEGER,            -- the version number, where the place keeps a chain
    digest      TEXT,               -- a store's digest; NULL for every other kind, and once purged
    title       TEXT,               -- a store's title; NULL once purged
    att_head    INTEGER,            -- the head of att when the row was written; NULL before SN-2
    horizon     INTEGER,            -- a horizon row: the position it declares; NULL otherwise
    salt        BLOB,               -- 16 random bytes; NULL once purged
    commitment  BLOB    NOT NULL,   -- sha256(salt, the row's fields): what the chain digests
    hash        BLOB    NOT NULL,   -- sha256(the previous row's hash, commitment)
    closed_at   INTEGER,            -- the seq of the path's next event; NULL while it is the last
    at          TEXT,               -- wall bookmark: lookup only, never an order; NULL once purged
    PRIMARY KEY (chain, seq)
) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS landings_path ON landings (chain, path_key, seq)
    WHERE path_key IS NOT NULL;
CREATE INDEX IF NOT EXISTS landings_doc ON landings (chain, doc_id, seq)
    WHERE doc_id IS NOT NULL AND doc_id <> source_path;
CREATE INDEX IF NOT EXISTS landings_closed ON landings (chain, closed_at)
    WHERE closed_at IS NOT NULL;
"""

_ZERO = bytes(32)
_COLUMNS = ("chain, seq, kind, path_key, source_path, doc_id, version, digest, title, att_head, "
            "horizon, salt, commitment, hash, closed_at, at")
_INSERT = f"INSERT INTO landings ({_COLUMNS}) VALUES ({', '.join('?' * 16)})"
# What a purge empties in a row (§6.1): the path, the identity, the digest, the title, the salt
# and the bookmark. The position, the kind, the key, the version, the closing stamp, the
# commitment and the hash stay.
_EMPTY = "source_path = NULL, doc_id = NULL, digest = NULL, title = NULL, salt = NULL, at = NULL"
_BATCH = 5000                       # genesis rows written a statement


class LandingLogKeyMissing(RuntimeError):
    """The landing log's secret is not in the environment, or is not 32 bytes of hex. Raised before
    anything is written: the log is never keyed without it."""


class LandingLogKeyMismatch(RuntimeError):
    """The secret in the environment is not the one a chain was written with. Raised before
    anything is written: a chain is never keyed two ways."""


def _now() -> str:
    return datetime.now(UTC).replace(tzinfo=None).isoformat(timespec="seconds")


def _mac(key: bytes, message: bytes) -> bytes:
    return hmac.new(key, message, hashlib.sha256).digest()


def parse_key(value: str, name: str = LANDING_LOG_KEY) -> bytes:
    """The secret as bytes: at least 32 of them, written as hex digits. The value is never put
    in a message."""
    try:
        raw = bytes.fromhex(value.strip())
    except ValueError:
        raise LandingLogKeyMissing(f"get_secret({name!r}) is not hex digits; the landing log "
                                   "takes 32 random bytes as 64 hex digits") from None
    if len(raw) < 32:
        raise LandingLogKeyMissing(f"get_secret({name!r}) is {len(raw)} bytes; the landing log "
                                   "takes 32 random bytes or more")
    return raw


def landing_log_key() -> bytes:
    """The instance's landing-log secret, from the environment (`get_secret`, the instance's own
    item: `landing-log-key`, or `<id>.landing-log-key` for a named instance). Raises
    `LandingLogKeyMissing` when it is absent: place it before the catalog is written."""
    from core.kernel.config import get_config, get_secret

    name = get_config().instance.secret(LANDING_LOG_KEY)
    value = get_secret(name)
    if not value:
        raise LandingLogKeyMissing(
            f"the landing log needs its secret at get_secret({name!r}): 32 random bytes as 64 "
            "hex digits (`openssl rand -hex 32`), placed in the Keychain and the environment "
            "(scripts/run_with_secrets.sh); nothing was written")
    return parse_key(value, name)


def commitment(salt: bytes, fields: Mapping[str, object]) -> bytes:
    """SHA-256 over the salt followed by the canonical JSON of the row's fields: keys sorted, no
    white space, UTF-8 (§3.2)."""
    canonical = json.dumps(fields, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(salt + canonical.encode("utf-8")).digest()


def chain_hash(previous: bytes, commit: bytes) -> bytes:
    """SHA-256 over the previous row's hash followed by this row's commitment; the first row's
    previous hash is 32 zero bytes."""
    return hashlib.sha256(previous + commit).digest()


@dataclass(frozen=True)
class Landing:
    """One row of the log. A row a purge emptied keeps its position, its kind, its key, its
    version, its closing stamp, its commitment and its hash, and nothing else: it is a hole."""

    chain: int
    seq: int
    kind: str
    path_key: bytes | None
    source_path: str | None
    doc_id: str | None
    version: int | None
    digest: str | None
    title: str | None
    att_head: int | None
    horizon: int | None
    salt: bytes | None
    commitment: bytes
    hash: bytes
    closed_at: int | None
    at: str | None

    @property
    def hole(self) -> bool:
        """The row was emptied by a purge: its content is gone, its position stays. A row is
        told a hole by its salt; `verify` fails a row without its salt that keeps any of the
        content a purge empties (`content`)."""
        return self.salt is None

    def content(self) -> dict[str, object]:
        """The fields a purge empties beside the salt (§6.1): the path, the identity, the digest,
        the title and the bookmark."""
        return {"source_path": self.source_path, "doc_id": self.doc_id, "digest": self.digest,
                "title": self.title, "at": self.at}

    def fields(self) -> dict[str, object]:
        """The fields the commitment covers (§3.2): every column but the key, the salt, the
        commitment, the hash and the closing stamp."""
        return {"chain": self.chain, "seq": self.seq, "kind": self.kind,
                "source_path": self.source_path, "doc_id": self.doc_id,
                "version": self.version, "digest": self.digest, "title": self.title,
                "att_head": self.att_head, "horizon": self.horizon, "at": self.at}


@dataclass(frozen=True)
class ChainCheck:
    """What `verify` found on one chain: the rows it read, the commitments it recomputed (the
    rows that still have their salt), and the first position at which a commitment or a hash
    does not hold, with what failed there, or `None`."""

    chain: int
    rows: int
    commitments: int
    failed_at: int | None = None
    why: str = ""

    @property
    def ok(self) -> bool:
        return self.failed_at is None and self.rows > 0


@dataclass(frozen=True)
class Prior:
    """A path's catalog row before a write: what the log compares against and carries."""

    digest: str
    title: str
    provenance: str
    active: bool
    doc_id: str


def _landing(r: Sequence[Any]) -> Landing:
    return Landing(*r)


class _Block:
    """One chain's genesis block: its rows committed to and hashed in order, and written a batch
    at a time, so a catalog of any size is read once and held in memory a batch at most."""

    def __init__(self, conn: sqlite3.Connection, chain: int, key: bytes) -> None:
        self.conn, self.chain, self.key, self.at = conn, chain, key, _now()
        self.seq = self.written = 0
        self.previous = _ZERO
        self.rows: list[tuple[Any, ...]] = []

    def add(self, kind: str, path: str | None = None, doc_id: str | None = None,
            digest: str | None = None, title: str | None = None, *,
            horizon: int | None = None, closed_at: int | None = None) -> None:
        self.seq += 1
        salt = secrets.token_bytes(16)
        commit = commitment(salt, {"chain": self.chain, "seq": self.seq, "kind": kind,
                                   "source_path": path, "doc_id": doc_id, "version": None,
                                   "digest": digest, "title": title, "att_head": None,
                                   "horizon": horizon, "at": self.at})
        self.previous = chain_hash(self.previous, commit)
        path_key = None if path is None else _mac(self.key, path.encode("utf-8"))
        self.rows.append((self.chain, self.seq, kind, path_key, path, doc_id, None, digest, title,
                          None, horizon, salt, commit, self.previous, closed_at, self.at))
        if len(self.rows) >= _BATCH:
            self.flush()

    def flush(self) -> int:
        """Write the rows held; returns every row the block has written."""
        self.conn.executemany(_INSERT, self.rows)
        self.written += len(self.rows)
        self.rows.clear()
        return self.written


def cut_position(cut: Mapping[int, int] | int, chain: int, chains: Sequence[int]) -> int:
    """A chain's position in a cut over a class. A cut is one position a chain; a bare integer is
    accepted for a class with one chain. A chain the cut does not name is read at its empty
    prefix."""
    if isinstance(cut, int):
        if len(chains) != 1:
            raise ValueError(f"a cut over {len(chains)} chains is one position a chain")
        return cut
    return int(cut.get(chain, 0))


class LandingLog:
    """The log's rows in the catalog's connection. The catalog calls the writing half inside the
    transaction of its own row; nothing here commits."""

    def __init__(self, conn: sqlite3.Connection, key: Callable[[], bytes]) -> None:
        self._conn = conn
        self._key_source = key
        self._key: bytes | None = None
        self._chain_keys: dict[int, bytes] = {}

    # the schema and the genesis ---------------------------------------------------------------

    def create(self) -> None:
        self._conn.executescript(DDL)

    def has_chains(self) -> bool:
        return self._conn.execute("SELECT 1 FROM landing_chains LIMIT 1").fetchone() is not None

    def genesis(self) -> int:
        """Each class the catalog holds gets a chain: a `genesis` row, then the catalog's rows of
        the class in path order, an active path as one `store` and a tombstoned path as a `store`
        of the digest it held followed by its tombstone (a `move` where another active path holds
        its identity, a `retire` otherwise), then a `horizon` row whose horizon is its own
        position. The order inside the block is not history, so the positions before the horizon
        are under it (§8). Returns the rows written."""
        written = 0
        classes = [str(r[0]) for r in self._conn.execute(
            "SELECT DISTINCT provenance FROM vault_files ORDER BY provenance")]
        held = {str(r[0]) for r in self._conn.execute(
            "SELECT DISTINCT doc_id FROM vault_files WHERE active = 1 AND doc_id IS NOT NULL")}
        for cls in classes:
            block = _Block(self._conn, *self._new_chain(cls))
            block.add("genesis")
            for path, digest, title, active, doc_id in self._conn.execute(
                    "SELECT source_path, digest, title, active, doc_id FROM vault_files "
                    "WHERE provenance = ? ORDER BY source_path", [cls]).fetchall():
                doc = str(doc_id) if doc_id is not None else str(path)
                if active:
                    block.add("store", path, doc, digest, title)
                else:
                    block.add("store", path, doc, digest, title, closed_at=block.seq + 2)
                    block.add("move" if doc in held else "retire", path, doc)
            block.add("horizon", horizon=block.seq + 1)
            written += block.flush()
        return written

    # keys -----------------------------------------------------------------------------------

    def _instance_key(self) -> bytes:
        if self._key is None:
            self._key = self._key_source()
        return self._key

    def _chain_key(self, chain: int) -> bytes:
        key = self._chain_keys.get(chain)
        if key is None:
            row = self._conn.execute(
                "SELECT secret, key_check FROM landing_chains WHERE chain = ?", [chain]).fetchone()
            if row is None:
                raise KeyError(f"no landing chain {chain}")
            key = _mac(self._instance_key(), b"landing chain\x00" + bytes(row[0]))
            if not hmac.compare_digest(_mac(key, b"key check"), bytes(row[1])):
                raise LandingLogKeyMismatch(
                    f"the landing-log secret is not the one chain {chain} was written with; "
                    "nothing was written")
            self._chain_keys[chain] = key
        return key

    def path_key(self, chain: int, path: str) -> bytes:
        """The key a row of `path` carries in `chain`."""
        return _mac(self._chain_key(chain), path.encode("utf-8"))

    def _new_chain(self, cls: str) -> tuple[int, bytes]:
        secret = secrets.token_bytes(32)
        key = _mac(self._instance_key(), b"landing chain\x00" + secret)
        chain = int(self._conn.execute(
            "SELECT coalesce(max(chain), 0) + 1 FROM landing_chains").fetchone()[0])
        self._conn.execute(
            "INSERT INTO landing_chains (chain, class, secret, key_check) VALUES (?, ?, ?, ?)",
            [chain, cls, secret, _mac(key, b"key check")])
        self._chain_keys[chain] = key
        return chain, key

    def _open_chain(self, cls: str) -> int:
        """A class that first appears after the genesis opens its chain at its first landing: a
        `genesis` and a `horizon`, and nothing between."""
        chain, _ = self._new_chain(cls)
        self._append(chain, "genesis")
        self._append(chain, "horizon", horizon=2)
        return chain

    # appending ------------------------------------------------------------------------------

    def _append(self, chain: int, kind: str, *, path: str | None = None,
                doc_id: str | None = None, version: int | None = None,
                digest: str | None = None, title: str | None = None,
                horizon: int | None = None) -> int:
        last = self._conn.execute(
            "SELECT seq, hash FROM landings WHERE chain = ? ORDER BY seq DESC LIMIT 1",
            [chain]).fetchone()
        seq = 1 if last is None else int(last[0]) + 1
        previous = _ZERO if last is None else bytes(last[1])
        at = _now()
        salt = secrets.token_bytes(16)
        commit = commitment(salt, {"chain": chain, "seq": seq, "kind": kind, "source_path": path,
                                   "doc_id": doc_id, "version": version, "digest": digest,
                                   "title": title, "att_head": None, "horizon": horizon,
                                   "at": at})
        path_key = None
        if path is not None:
            path_key = self.path_key(chain, path)
            # the path's previous event in the chain is closed at this one (§3.2); the statement
            # names the key index, since the planner takes the primary key and walks the chain
            self._conn.execute(
                "UPDATE landings INDEXED BY landings_path SET closed_at = ? "
                "WHERE chain = ? AND path_key = ? AND closed_at IS NULL", [seq, chain, path_key])
        self._conn.execute(_INSERT, [chain, seq, kind, path_key, path, doc_id, version, digest,
                                     title, None, horizon, salt, commit,
                                     chain_hash(previous, commit), None, at])
        return seq

    def _class_of(self, chain: int) -> str:
        return str(self._conn.execute(
            "SELECT class FROM landing_chains WHERE chain = ?", [chain]).fetchone()[0])

    def _locate(self, path: str, cls: str | None) -> tuple[Landing | None, list[int]]:
        """The path's last event in the chain that holds its present, the one chain where the
        path's last event is not a `leave`, with the chains seen to hold only a `leave` of it. The
        chains of `cls`, the class the catalog gives the path, are asked first; a path the
        catalog does not hold is looked for in every chain."""
        first = self.chains(cls) if cls is not None else []
        left: list[int] = []
        for chain in [*first, *(c for c in self.all_chains() if c not in first)]:
            row = self._seek(chain, path)
            if row is None:
                continue
            if row.kind != "leave":
                return row, left
            left.append(chain)
        return None, left

    def _target(self, cls: str, left: Sequence[int]) -> int:
        """The chain a landing goes to when the path's present is in no chain of its class: a
        chain of the class the path left, else the newest chain of the class, opened if the class
        has none (§3.2)."""
        chains = self.chains(cls)
        back = [c for c in chains if c in left]
        if back:
            return back[-1]
        return chains[-1] if chains else self._open_chain(cls)

    def store(self, path: str, cls: str, doc_id: str, version: int | None, digest: str,
              title: str, prior: Prior | None) -> None:
        """A landing of `path` (`record`): a `store` in the chain that holds the path's last event,
        after a `move` when the landing changes the identity the path holds, or after a `leave`
        of the path's chain when it changes the path's class."""
        current, left = self._locate(path, prior.provenance if prior is not None else None)
        if current is not None and self._class_of(current.chain) == cls:
            target = current.chain
            if current.kind == "store" and not current.hole and current.doc_id != doc_id:
                self._append(target, "move", path=path, doc_id=current.doc_id)
        else:
            target = self._target(cls, left)
            if current is not None:
                self._append(current.chain, "leave", path=path,
                             doc_id=current.doc_id or (prior.doc_id if prior else None))
        self._append(target, "store", path=path, doc_id=doc_id, version=version, digest=digest,
                     title=title)

    def tombstone(self, path: str, prior: Prior, kind: str) -> None:
        """A tombstone of an active path (`tombstone`): a `retire`, or a `move` when another
        active path holds the identity."""
        current, left = self._locate(path, prior.provenance)
        chain = current.chain if current is not None else self._target(prior.provenance, left)
        self._append(chain, kind, path=path, doc_id=prior.doc_id)

    def rekey(self, path: str, prior: Prior, doc_id: str) -> None:
        """The owner-gated re-key of a path's identity (`migrate_rekey_doc_id`): a `move` of the
        identity it held, then the path under the new one, a `store` of what it holds when it is
        active and a `retire` when it is tombstoned."""
        current, left = self._locate(path, prior.provenance)
        chain = current.chain if current is not None else self._target(prior.provenance, left)
        self._append(chain, "move", path=path, doc_id=prior.doc_id)
        if prior.active:
            version = current.version if current is not None and current.kind == "store" else None
            self._append(chain, "store", path=path, doc_id=doc_id, version=version,
                         digest=prior.digest, title=prior.title)
        else:
            self._append(chain, "retire", path=path, doc_id=doc_id)

    def relabel(self, old: str, new: str) -> None:
        """A whole-class relabel rewrites the label of the class's chains and no row (§3.1)."""
        self._conn.execute("UPDATE landing_chains SET class = ? WHERE class = ?", [new, old])

    def empty_path(self, path: str) -> int:
        """`remove`: every row of the path emptied as §6.1 says, its key and position kept."""
        n = 0
        for chain in self.all_chains():
            n += self._conn.execute(
                f"UPDATE landings INDEXED BY landings_path SET {_EMPTY} "
                "WHERE chain = ? AND path_key = ? AND salt IS NOT NULL",
                [chain, self.path_key(chain, path)]).rowcount
        return n

    def empty_digest(self, digest: str) -> int:
        """`remove_digest`: every row of the digest emptied as §6.1 says, its key and position
        kept. Another version of the same path is not touched, so while a `store` of the path
        keeps its content the path's other rows keep its name, and the hole stays tied to it. A
        path whose every `store`, in every chain, is then a hole has its other rows emptied as
        well, its `retire`, `move` and `leave`: no row then names it, or the identity and the
        date its tombstone carried. A path's rows are found by the names they carry and by the
        keys the emptied rows keep, so the purge needs no secret; the rows of the digest and the
        names are read by a walk of the log, which has no index by digest or by name. Returns
        the rows emptied."""
        hit = [(int(c), bytes(k), str(p)) for c, k, p in self._conn.execute(
            "SELECT chain, path_key, source_path FROM landings WHERE digest = ? "
            "AND path_key IS NOT NULL AND source_path IS NOT NULL", [digest])]
        n = self._conn.execute(
            f"UPDATE landings SET {_EMPTY} WHERE digest = ?", [digest]).rowcount
        paths = sorted({p for _, _, p in hit})
        if not paths:
            return n
        keys: dict[str, set[tuple[int, bytes]]] = {p: set() for p in paths}
        for c, k, p in hit:
            keys[p].add((c, k))
        for c, k, p in self._conn.execute(
                "SELECT DISTINCT chain, path_key, source_path FROM landings WHERE path_key IS NOT "
                f"NULL AND source_path IN ({', '.join('?' * len(paths))})", paths):
            keys[str(p)].add((int(c), bytes(k)))
        for path in paths:
            if any(self._conn.execute(
                    "SELECT 1 FROM landings INDEXED BY landings_path WHERE chain = ? AND "
                    "path_key = ? AND kind = 'store' AND salt IS NOT NULL LIMIT 1",
                    [c, k]).fetchone() for c, k in keys[path]):
                continue                    # a version of the path keeps its content
            for c, k in sorted(keys[path]):
                n += self._conn.execute(
                    f"UPDATE landings INDEXED BY landings_path SET {_EMPTY} "
                    "WHERE chain = ? AND path_key = ? AND salt IS NOT NULL", [c, k]).rowcount
        return n

    # reads ----------------------------------------------------------------------------------

    def all_chains(self) -> list[int]:
        return [int(r[0]) for r in self._conn.execute(
            "SELECT chain FROM landing_chains ORDER BY chain")]

    def chains(self, cls: str) -> list[int]:
        """The chains that hold `cls` now, oldest first."""
        return [int(r[0]) for r in self._conn.execute(
            "SELECT chain FROM landing_chains WHERE class = ? ORDER BY chain", [str(cls)])]

    def head(self, chain: int) -> int:
        """The chain's last position: the head cut on it."""
        row = self._conn.execute("SELECT max(seq) FROM landings WHERE chain = ?",
                                 [chain]).fetchone()
        return int(row[0]) if row is not None and row[0] is not None else 0

    def read_at(self, chain: int, c: int) -> list[Landing]:
        """The prefix of the chain at `c`: the rows with `seq ≤ c`, in order."""
        return [_landing(r) for r in self._conn.execute(
            f"SELECT {_COLUMNS} FROM landings WHERE chain = ? AND seq <= ? ORDER BY seq",
            [chain, c])]

    def read_between(self, chain: int, a: int, b: int) -> list[Landing]:
        """The rows after `a` and up to `b`, in order."""
        return [_landing(r) for r in self._conn.execute(
            f"SELECT {_COLUMNS} FROM landings WHERE chain = ? AND seq > ? AND seq <= ? "
            "ORDER BY seq", [chain, a, b])]

    def _seek(self, chain: int, path: str, c: int | None = None) -> Landing | None:
        """The path's last event in the chain at or under `c` (the head when `None`): one seek on
        `landings_path`, which the statement names."""
        row = self._conn.execute(
            f"SELECT {_COLUMNS} FROM landings INDEXED BY landings_path "
            "WHERE chain = ? AND path_key = ? AND seq <= ? ORDER BY seq DESC LIMIT 1",
            [chain, self.path_key(chain, path), (1 << 62) if c is None else c]).fetchone()
        return _landing(row) if row is not None else None

    def state_at(self, cls: str, path: str, c: Mapping[int, int] | int) -> Landing | None:
        """The path's last event at or under the cut over the class's chains: a `store`, a
        `retire`, a `move`, a `leave`, a hole (a row a purge emptied, with its position and no
        name), or nothing. A path has events in two chains of one class only after it changed
        class and the two classes were merged; then the event that is not a `leave` is the
        path's at the cut, and among two such the later chain's, a rule of the prefix alone."""
        chains = self.chains(cls)
        found = [r for chain in chains
                 if (r := self._seek(chain, path, cut_position(c, chain, chains))) is not None]
        staying = [r for r in found if r.kind != "leave"] or found
        return staying[-1] if staying else None

    def history_at(self, cls: str, path: str, c: Mapping[int, int] | int) -> list[Landing]:
        """The path's `store` rows at or under the cut over the class's chains, a hole where a
        version was purged. In one chain they are oldest first. A path has events in two chains
        of one class only after it changed class and the two classes were merged by a relabel;
        then the chains it had left at the cut come first, by chain id, and the chain that holds
        its present last. That is a rule of the prefixes alone, not the order the versions
        landed in, which no position across two chains records: the order can differ from it,
        and across the chains the read at an earlier cut need not be a prefix of the read at a
        later one. Chain by chain it is (SNP-2)."""
        chains = self.chains(cls)
        parts: list[tuple[bool, int, list[Landing]]] = []
        for chain in chains:
            rows = [_landing(r) for r in self._conn.execute(
                f"SELECT {_COLUMNS} FROM landings INDEXED BY landings_path "
                "WHERE chain = ? AND path_key = ? AND seq <= ? ORDER BY seq",
                [chain, self.path_key(chain, path), cut_position(c, chain, chains)])]
            if rows:
                parts.append((rows[-1].kind != "leave", chain,
                              [r for r in rows if r.kind == "store"]))
        return [r for _, _, stores in sorted(parts, key=lambda p: (p[0], p[1])) for r in stores]

    def heads_at(self, cls: str, c: Mapping[int, int] | int) -> list[Landing]:
        """Every head of the class at the cut: the `store` rows with `seq ≤ c` whose closing
        stamp is absent or above `c`, over the class's chains (§4.2), a hole returned as a hole
        with its position and no name."""
        chains = self.chains(cls)
        out: list[Landing] = []
        for chain in chains:
            pos = cut_position(c, chain, chains)
            out.extend(_landing(r) for r in self._conn.execute(
                f"SELECT {_COLUMNS} FROM landings WHERE chain = ? AND seq <= ? "
                "AND kind = 'store' AND (closed_at IS NULL OR closed_at > ?) ORDER BY seq",
                [chain, pos, pos]))
        return out

    def rows(self, chain: int) -> Iterator[Landing]:
        """Every row of the chain, in order."""
        for r in self._conn.execute(
                f"SELECT {_COLUMNS} FROM landings WHERE chain = ? ORDER BY seq", [chain]):
            yield _landing(r)

    def verify(self, chain: int) -> ChainCheck:
        """The chain's hashes recomputed from its first row, and the commitment of every row that
        still has its salt (SNP-9); a row without its salt is a hole, and it must keep none of
        the content a purge empties (§6.1), since nothing else can be checked of it. The first
        position where one of these fails, or none."""
        previous = _ZERO
        n = checked = 0
        for row in self.rows(chain):
            n += 1
            if row.seq != n:
                return ChainCheck(chain, n, checked, n, "a position is missing")
            if row.salt is None:
                if any(v is not None for v in row.content().values()):
                    return ChainCheck(chain, n, checked, row.seq, "a hole keeps content")
            else:
                checked += 1
                if not hmac.compare_digest(commitment(row.salt, row.fields()), row.commitment):
                    return ChainCheck(chain, n, checked, row.seq, "the commitment")
            if not hmac.compare_digest(chain_hash(previous, row.commitment), row.hash):
                return ChainCheck(chain, n, checked, row.seq, "the hash")
            previous = row.hash
        return ChainCheck(chain, n, checked)
