"""The forecast ledger: append-only, hash-chained, with the pre-registration as its genesis.

`docs/design-notes/dn-market-forecast-experiment.md` D5. One JSON object per line:

    {"seq": 3, "kind": "forecast", "body": {...}, "recorded_at": "...",
     "prev": "<hash>", "hash": "<hash>"}

`hash` is the sha256 of the canonical JSON of the line without `hash`, and `prev` is the previous
line's `hash` (64 zeros for the first). `verify` recomputes the chain, so an edited, dropped or
reordered line fails it. The first record is the `protocol` (D6): the bar is written before any
forecast and cannot move without a visible amendment later in the chain.

The ledger's own clock stamps `recorded_at`, and it alone decides "before": a forecast carries no
timestamp of its own, so an arm cannot backdate one. A forecast is refused when its question is
unknown, closed, resolved or voided, when its arm is not in the protocol, when `p` is not a
probability, or when the arm already forecast that question in that round.

Machinery, not corpus (BL-4 in `dn-scored-beliefs-and-earned-entitlement`): nothing under
`core/` imports this module, and no dreamer can read a score.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import math
import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path

GENESIS_PREV = "0" * 64

KINDS = ("protocol", "question", "forecast", "resolution", "void")

# The arms of D4. `NULL` is the harness check (a copy of M); KNOWN-EDGE and ORACLE are derived by
# the scorer from resolutions and are never recorded.
ARMS = frozenset({"M", "NULL", "W", "P", "F", "L", "I", "D"})


class Family(StrEnum):
    EVENT = "event"
    VOLATILITY = "volatility"
    STRUCTURE = "structure"
    DIRECTION = "direction"


class LedgerError(ValueError):
    """A record the ledger refuses. Nothing was written."""


class LedgerCorrupt(RuntimeError):
    """The file does not verify: a line was edited, dropped, reordered or is not a record."""


def utc_now() -> datetime:
    return datetime.now(UTC)


def _aware(value: datetime, what: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise LedgerError(f"{what} must carry a timezone, got a naive datetime: {value!r}")
    return value.astimezone(UTC)


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat()


@dataclass(frozen=True)
class Comparison:
    """`arm` improves on `baseline` on `family`: the statistic is Brier(baseline) - Brier(arm)."""

    family: Family
    baseline: str
    arm: str

    def body(self) -> dict[str, object]:
        return {"family": self.family.value, "baseline": self.baseline, "arm": self.arm}

    @classmethod
    def parse(cls, raw: object) -> Comparison:
        body = _mapping(raw, "comparison")
        return cls(_family(body), _str(body, "baseline"), _str(body, "arm"))


@dataclass(frozen=True)
class Protocol:
    """The pre-registration (D6). The scorer reads every number from here, never from defaults."""

    name: str
    primary: Comparison
    secondary: tuple[Comparison, ...] = ()
    arms: tuple[str, ...] = ("M", "NULL", "W", "P")
    delta: float = 0.02
    alpha: float = 0.05
    power: float = 0.80
    log_clip: float = 0.001
    bootstrap: int = 10_000
    seed: int = 20261105
    n_clusters: int | None = None          # fixed by an amendment after the blinded pilot
    selection: Mapping[str, object] = field(default_factory=dict)
    notes: str = ""

    def __post_init__(self) -> None:
        unknown = set(self.arms) - ARMS
        if unknown:
            raise LedgerError(f"arms not in D4: {sorted(unknown)}")
        for c in (self.primary, *self.secondary):
            if c.baseline not in self.arms or c.arm not in self.arms:
                raise LedgerError(f"comparison {c} names an arm the protocol does not register")
        if not self.delta > 0:
            raise LedgerError("delta must be positive")
        if not 0 < self.alpha < 1 or not 0 < self.power < 1:
            raise LedgerError("alpha and power must lie in (0, 1)")
        if not 0 < self.log_clip < 0.5:
            raise LedgerError("log_clip must lie in (0, 0.5)")
        if self.bootstrap < 1000:
            raise LedgerError("bootstrap needs at least 1000 resamples")
        if self.n_clusters is not None and self.n_clusters < 2:
            raise LedgerError("n_clusters must be at least 2")

    def body(self) -> dict[str, object]:
        return {
            "name": self.name,
            "primary": self.primary.body(),
            "secondary": [c.body() for c in self.secondary],
            "arms": list(self.arms),
            "delta": self.delta,
            "alpha": self.alpha,
            "power": self.power,
            "log_clip": self.log_clip,
            "bootstrap": self.bootstrap,
            "seed": self.seed,
            "n_clusters": self.n_clusters,
            "selection": dict(self.selection),
            "notes": self.notes,
        }

    @classmethod
    def parse(cls, raw: object) -> Protocol:
        body = _mapping(raw, "protocol")
        secondary = body.get("secondary", [])
        arms = body.get("arms", [])
        n_clusters = body.get("n_clusters")
        if not isinstance(secondary, list) or not isinstance(arms, list):
            raise LedgerCorrupt("protocol: secondary and arms must be lists")
        if n_clusters is not None and not isinstance(n_clusters, int):
            raise LedgerCorrupt("protocol: n_clusters must be an integer or null")
        return cls(
            name=_str(body, "name"),
            primary=Comparison.parse(body.get("primary")),
            secondary=tuple(Comparison.parse(c) for c in secondary),
            arms=tuple(str(a) for a in arms),
            delta=_float(body, "delta"),
            alpha=_float(body, "alpha"),
            power=_float(body, "power"),
            log_clip=_float(body, "log_clip"),
            bootstrap=_int(body, "bootstrap"),
            seed=_int(body, "seed"),
            n_clusters=n_clusters,
            selection=_mapping(body.get("selection", {}), "selection"),
            notes=_str(body, "notes"),
        )


@dataclass(frozen=True)
class Question:
    """A yes/no question with its source's own resolution text, close time and event cluster."""

    qid: str
    family: Family
    source: str
    text: str
    resolution_text: str
    closes_at: datetime
    cluster: str
    universe: str = "equities"

    def body(self) -> dict[str, object]:
        return {
            "qid": self.qid,
            "family": self.family.value,
            "source": self.source,
            "text": self.text,
            "resolution_text": self.resolution_text,
            "closes_at": _iso(self.closes_at),
            "cluster": self.cluster,
            "universe": self.universe,
        }

    @classmethod
    def parse(cls, raw: object) -> Question:
        body = _mapping(raw, "question")
        return cls(
            qid=_str(body, "qid"),
            family=_family(body),
            source=_str(body, "source"),
            text=_str(body, "text"),
            resolution_text=_str(body, "resolution_text"),
            closes_at=_dt(body, "closes_at"),
            cluster=_str(body, "cluster"),
            universe=_str(body, "universe"),
        )


@dataclass(frozen=True)
class Forecast:
    """One arm's probability that `qid` resolves yes, in round `round`. No timestamp: the ledger
    stamps it. `sigma` is what the arm could see; `evidence` the refs it used (note ids, query
    sentences with their trace digests)."""

    qid: str
    arm: str
    round: str
    p: float
    sigma: tuple[str, ...] = ()
    evidence: tuple[str, ...] = ()
    model: str | None = None

    def body(self) -> dict[str, object]:
        return {
            "qid": self.qid,
            "arm": self.arm,
            "round": self.round,
            "p": self.p,
            "sigma": list(self.sigma),
            "evidence": list(self.evidence),
            "model": self.model,
        }

    @classmethod
    def parse(cls, raw: object) -> Forecast:
        body = _mapping(raw, "forecast")
        model = body.get("model")
        if model is not None and not isinstance(model, str):
            raise LedgerCorrupt("forecast: model must be a string or null")
        return cls(
            qid=_str(body, "qid"),
            arm=_str(body, "arm"),
            round=_str(body, "round"),
            p=_float(body, "p"),
            sigma=_strs(body, "sigma"),
            evidence=_strs(body, "evidence"),
            model=model,
        )


@dataclass(frozen=True)
class Resolution:
    """How `qid` resolved, when the source says it did, and where that was read."""

    qid: str
    outcome: int
    resolved_at: datetime
    source_ref: str

    def body(self) -> dict[str, object]:
        return {
            "qid": self.qid,
            "outcome": self.outcome,
            "resolved_at": _iso(self.resolved_at),
            "source_ref": self.source_ref,
        }

    @classmethod
    def parse(cls, raw: object) -> Resolution:
        body = _mapping(raw, "resolution")
        return cls(
            qid=_str(body, "qid"),
            outcome=_int(body, "outcome"),
            resolved_at=_dt(body, "resolved_at"),
            source_ref=_str(body, "source_ref"),
        )


@dataclass(frozen=True)
class Void:
    """A question the source cancelled or annulled: excluded from every score."""

    qid: str
    reason: str

    def body(self) -> dict[str, object]:
        return {"qid": self.qid, "reason": self.reason}

    @classmethod
    def parse(cls, raw: object) -> Void:
        body = _mapping(raw, "void")
        return cls(qid=_str(body, "qid"), reason=_str(body, "reason"))


@dataclass(frozen=True)
class Entry:
    """One verified line of the ledger."""

    seq: int
    kind: str
    body: Mapping[str, object]
    recorded_at: datetime
    prev: str
    hash: str


@dataclass(frozen=True)
class Head:
    seq: int
    hash: str
    counts: Mapping[str, int]


@dataclass
class State:
    """What the verified chain says, for the refusals and for the scorer."""

    protocol: Protocol | None = None
    questions: dict[str, Question] = field(default_factory=dict)
    resolutions: dict[str, Resolution] = field(default_factory=dict)
    voids: dict[str, Void] = field(default_factory=dict)
    forecast_keys: set[tuple[str, str, str]] = field(default_factory=set)


def canonical(payload: Mapping[str, object]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def line_hash(seq: int, kind: str, body: Mapping[str, object], recorded_at: str, prev: str) -> str:
    payload = {"seq": seq, "kind": kind, "body": body, "recorded_at": recorded_at, "prev": prev}
    return hashlib.sha256(canonical(payload)).hexdigest()


def parse_lines(lines: list[str]) -> list[Entry]:
    """Parse and verify every line, in order. Raises `LedgerCorrupt` at the first bad one."""
    entries: list[Entry] = []
    prev = GENESIS_PREV
    for number, text in enumerate(lines):
        if not text.strip():
            raise LedgerCorrupt(f"line {number}: empty")
        try:
            raw = json.loads(text)
        except json.JSONDecodeError as exc:
            raise LedgerCorrupt(f"line {number}: not JSON ({exc})") from exc
        line = _mapping(raw, f"line {number}")
        seq, kind = line.get("seq"), line.get("kind")
        body, recorded, prev_seen, digest = (
            line.get("body"), line.get("recorded_at"), line.get("prev"), line.get("hash"))
        if seq != number:
            raise LedgerCorrupt(f"line {number}: seq {seq!r} out of order")
        if kind not in KINDS:
            raise LedgerCorrupt(f"line {number}: unknown kind {kind!r}")
        if not isinstance(body, dict) or not isinstance(recorded, str):
            raise LedgerCorrupt(f"line {number}: body or recorded_at malformed")
        if prev_seen != prev:
            raise LedgerCorrupt(f"line {number}: prev does not name line {number - 1}'s hash")
        expected = line_hash(number, str(kind), body, recorded, prev)
        if digest != expected:
            raise LedgerCorrupt(f"line {number}: hash mismatch (the line was edited)")
        try:
            at = datetime.fromisoformat(recorded)
        except ValueError as exc:
            raise LedgerCorrupt(f"line {number}: recorded_at is not ISO 8601") from exc
        entries.append(Entry(number, str(kind), body, at, prev, expected))
        prev = expected
    return entries


def replay(entries: list[Entry]) -> State:
    """The state a verified chain describes. The genesis must be a protocol."""
    state = State()
    for entry in entries:
        if entry.seq == 0 and entry.kind != "protocol":
            raise LedgerCorrupt("the genesis record must be the protocol")
        _apply(state, entry.kind, entry.body)
    return state


Record = Protocol | Question | Forecast | Resolution | Void

# Once a forecast exists these protocol fields are the bar, and an amendment may not move them.
_FROZEN = ("primary", "delta", "alpha", "power", "log_clip", "bootstrap", "seed")


def _kind(record: Record) -> str:
    if isinstance(record, Protocol):
        return "protocol"
    if isinstance(record, Question):
        return "question"
    if isinstance(record, Forecast):
        return "forecast"
    if isinstance(record, Resolution):
        return "resolution"
    return "void"


def _apply(state: State, kind: str, body: Mapping[str, object]) -> None:
    """Advance the state by one verified record (the step `replay` takes per line)."""
    if kind == "protocol":
        state.protocol = Protocol.parse(body)
    elif kind == "question":
        q = Question.parse(body)
        state.questions[q.qid] = q
    elif kind == "forecast":
        f = Forecast.parse(body)
        state.forecast_keys.add((f.qid, f.arm, f.round))
    elif kind == "resolution":
        r = Resolution.parse(body)
        state.resolutions[r.qid] = r
    elif kind == "void":
        v = Void.parse(body)
        state.voids[v.qid] = v


class Ledger:
    """One experiment's ledger file. One writer at a time: an exclusive lock around each write,
    and the whole chain verified under it before anything is appended."""

    def __init__(self, path: Path, clock: Callable[[], datetime] = utc_now) -> None:
        self.path = path
        self._clock = clock

    # -- reading ----------------------------------------------------------------------------

    def entries(self) -> list[Entry]:
        if not self.path.exists():
            return []
        return parse_lines(self.path.read_text(encoding="utf-8").splitlines())

    def state(self) -> State:
        return replay(self.entries())

    def verify(self) -> Head:
        entries = self.entries()
        replay(entries)
        counts = {kind: sum(1 for e in entries if e.kind == kind) for kind in KINDS}
        if not entries:
            return Head(-1, GENESIS_PREV, counts)
        return Head(entries[-1].seq, entries[-1].hash, counts)

    # -- writing ----------------------------------------------------------------------------

    def register(self, protocol: Protocol) -> Entry:
        """The genesis. Refused on a ledger that already has records."""
        return self._append([protocol], genesis=True)[0]

    def amend(self, protocol: Protocol) -> Entry:
        """A later protocol record: visible in the chain, never a rewrite of the first. Once a
        forecast exists it may add arms and secondary comparisons, fix `n_clusters` once, and
        change the selection or the notes; the statistical bar stays where it was."""
        if not self.entries():
            raise LedgerError("nothing to amend: register the protocol first")
        return self._append([protocol])[0]

    def add_question(self, question: Question) -> Entry:
        return self._append([question])[0]

    def add_forecast(self, forecast: Forecast) -> Entry:
        return self._append([forecast])[0]

    def resolve(self, resolution: Resolution) -> Entry:
        return self._append([resolution])[0]

    def void(self, void: Void) -> Entry:
        return self._append([void])[0]

    def extend(self, records: list[Record]) -> list[Entry]:
        """Several records under one lock, all or nothing: each is checked against the state the
        ones before it leave, and if any is refused nothing is written. A round lands this way."""
        return self._append(records)

    # -- refusals ---------------------------------------------------------------------------

    def _check(self, state: State, now: datetime, record: Record) -> None:
        if isinstance(record, Protocol):
            self._check_protocol(state, record)
            return
        if state.protocol is None:
            raise LedgerError("register the protocol before any other record")
        if isinstance(record, Question):
            if record.qid in state.questions:
                raise LedgerError(f"question {record.qid!r} is already registered")
            if _aware(record.closes_at, "closes_at") <= now:
                raise LedgerError(f"question {record.qid!r} closed before it was registered")
        elif isinstance(record, Forecast):
            self._check_forecast(state, state.protocol, now, record)
        elif isinstance(record, Resolution):
            self._check_open(state, record.qid)
            if isinstance(record.outcome, bool) or record.outcome not in (0, 1):
                raise LedgerError(f"outcome must be 0 or 1, got {record.outcome!r}")
            _aware(record.resolved_at, "resolved_at")
        else:
            self._check_open(state, record.qid)

    @staticmethod
    def _check_protocol(state: State, new: Protocol) -> None:
        old = state.protocol
        if old is None or not state.forecast_keys:
            return
        moved = [name for name in _FROZEN if getattr(old, name) != getattr(new, name)]
        if moved:
            raise LedgerError(f"forecasts exist: the amendment may not move {', '.join(moved)}")
        if not set(old.arms) <= set(new.arms):
            raise LedgerError("forecasts exist: an amendment may add arms, never remove one")
        if not set(old.secondary) <= set(new.secondary):
            raise LedgerError("forecasts exist: an amendment may add comparisons, never drop one")
        if old.n_clusters is not None and new.n_clusters != old.n_clusters:
            raise LedgerError("n_clusters is already fixed")

    def _check_forecast(self, state: State, protocol: Protocol, now: datetime,
                        f: Forecast) -> None:
        if f.arm not in protocol.arms:
            raise LedgerError(f"arm {f.arm!r} is not registered in the protocol")
        if (isinstance(f.p, bool) or not isinstance(f.p, float | int)
                or not math.isfinite(f.p) or not 0.0 <= f.p <= 1.0):
            raise LedgerError(f"p must be a probability, got {f.p!r}")
        if not f.round:
            raise LedgerError("a forecast names its round")
        self._check_open(state, f.qid)
        question = state.questions[f.qid]
        if question.closes_at <= now:
            raise LedgerError(f"question {f.qid!r} closed at {_iso(question.closes_at)}")
        if (f.qid, f.arm, f.round) in state.forecast_keys:
            raise LedgerError(f"arm {f.arm!r} already forecast {f.qid!r} in round {f.round!r}")

    @staticmethod
    def _check_open(state: State, qid: str) -> None:
        if qid not in state.questions:
            raise LedgerError(f"unknown question {qid!r}")
        if qid in state.resolutions:
            raise LedgerError(f"question {qid!r} is already resolved")
        if qid in state.voids:
            raise LedgerError(f"question {qid!r} was voided")

    # -- the append -------------------------------------------------------------------------

    def _append(self, records: list[Record], *, genesis: bool = False) -> list[Entry]:
        if not records:
            return []
        now = _aware(self._clock(), "the ledger clock")
        recorded = _iso(now)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a+", encoding="utf-8") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                handle.seek(0)
                entries = parse_lines(handle.read().splitlines())
                state = replay(entries)
                if genesis and entries:
                    raise LedgerError("the ledger already has a protocol; amend it instead")
                seq = len(entries)
                prev = entries[-1].hash if entries else GENESIS_PREV
                lines: list[str] = []
                out: list[Entry] = []
                for record in records:
                    if seq == 0 and not isinstance(record, Protocol):
                        raise LedgerError("register the protocol before any other record")
                    self._check(state, now, record)
                    kind = _kind(record)
                    # Round-trip through JSON so the hash covers exactly what is stored.
                    body = json.loads(canonical(record.body()))
                    digest = line_hash(seq, kind, body, recorded, prev)
                    lines.append(canonical({"seq": seq, "kind": kind, "body": body,
                                            "recorded_at": recorded, "prev": prev,
                                            "hash": digest}).decode())
                    out.append(Entry(seq, kind, body, now, prev, digest))
                    _apply(state, kind, body)
                    seq, prev = seq + 1, digest
                handle.write("".join(line + "\n" for line in lines))
                handle.flush()
                os.fsync(handle.fileno())
                return out
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


# -- parsing helpers (the file is data; every field is checked, never trusted) ------------------

def _mapping(raw: object, what: str) -> Mapping[str, object]:
    if not isinstance(raw, dict):
        raise LedgerCorrupt(f"{what}: expected an object")
    return raw


def _str(body: Mapping[str, object], key: str) -> str:
    value = body.get(key)
    if not isinstance(value, str):
        raise LedgerCorrupt(f"{key}: expected a string")
    return value


def _family(body: Mapping[str, object]) -> Family:
    value = _str(body, "family")
    try:
        return Family(value)
    except ValueError as exc:
        raise LedgerCorrupt(f"family: unknown value {value!r}") from exc


def _float(body: Mapping[str, object], key: str) -> float:
    value = body.get(key)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise LedgerCorrupt(f"{key}: expected a number")
    return float(value)


def _int(body: Mapping[str, object], key: str) -> int:
    value = body.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise LedgerCorrupt(f"{key}: expected an integer")
    return value


def _strs(body: Mapping[str, object], key: str) -> tuple[str, ...]:
    value = body.get(key, [])
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        raise LedgerCorrupt(f"{key}: expected a list of strings")
    return tuple(str(v) for v in value)


def _dt(body: Mapping[str, object], key: str) -> datetime:
    value = _str(body, key)
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise LedgerCorrupt(f"{key}: not ISO 8601") from exc
    if parsed.tzinfo is None:
        raise LedgerCorrupt(f"{key}: naive datetime")
    return parsed
