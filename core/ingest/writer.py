"""The ingress's one writer: it lands a plan effect by effect, each by the rules of
dn-ingress-language §E4 (R2 to R8), in the first form's order with the key last (ING-7, ING-16).

A store lands as the first form's landers landed: the raw object, the plane's chunk-level
amendment, the version chain where the place keeps one, the attestation, and last the catalog's
digest, the idempotence key the UNCHANGED check reads (for every place, the key counts only while
the plane holds the rows: the third review's finding 2). An effect the rules refuse lands nothing
and the rest of the plan lands; the outcome says which rule refused it. Before the first effect
lands, the plan is priced (§E10): its writes, each store the UNCHANGED check would not skip and
each other effect, and its embeds, the distinct atoms the plane does not hold, are charged to the
budget, so a plan that would overrun it is refused before anything is paid.

Each rule is a theorem's hypothesis in `formal/Palace/Script.lean`: R4 and R8 give the firewall
(ING-14, `firewall_store`, `owned_by_source`), R3 confinement (ING-15), R5 and R6 fixed labels and
identities that move only with their bytes (ING-17), R7 retire as reconciliation. The writer is
stricter than the model in places, each written where it is checked: content under any label but
the observed one is an item's whole content under its item's title; an identity read off an item
is the one it declares, and no path takes one another path of its source still holds; a held
identity moves with its label; a role retires only the labels the table gives it; a job runs once
a request, inside its role's share of the queue.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any

from core.ingest.index import index_amendment
from core.ingest.landing import attest_once, attested_by, record_version_if_new
from core.ingest.table import Table
from core.kernel.clearance import CURATED_READ, MIRROR_READ, OBSERVED_READ, Clearance
from core.kernel.ingest.logseq import _decode, parse_text
from core.kernel.ingest.pipeline import derive_chunks, ingest_note
from core.kernel.provenance import Provenance
from core.sentence.interpret import (
    OBSERVED,
    Effect,
    LinkEff,
    Meter,
    RetireEff,
    RunEff,
    ScriptError,
    StoreEff,
)
from core.stores.plane import atom_id as plane_atom_id

# The clearance under which the writer asks the plane whether it holds a label's rows.
_HOLDS: dict[str, Clearance[Provenance]] = {
    Provenance.AUTHORED_SOLO.value: MIRROR_READ,
    Provenance.AUTHORED_DIALOGUE.value: MIRROR_READ,
    Provenance.OBSERVED.value: OBSERVED_READ,
    Provenance.CURATED.value: CURATED_READ,
}


@dataclass
class Stores:
    """What the writer lands into; each injectable, so the writer is tested with fakes."""

    raw: Any
    plane: Any
    embedder: Any
    catalog: Any
    versions: Any | None = None
    attestor: Any | None = None
    edges: Any | None = None
    # a job's start: (kind, its arguments, *, role, request) -> the job's id; raises the ingress's
    # `Busy` past the role's share of the queue
    enqueue: Callable[..., int] | None = None


@dataclass(frozen=True)
class Outcome:
    """What one effect did: landed, unchanged, retired, linked, queued, or refused with the rule."""

    effect: str
    path: str
    status: str
    why: str = ""
    digest: str = ""
    attestations: tuple[str, ...] = ()
    job: int | None = None

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {"effect": self.effect, "path": self.path, "status": self.status}
        for k in ("why", "digest"):
            if getattr(self, k):
                out[k] = getattr(self, k)
        if self.attestations:
            out["attestations"] = list(self.attestations)
        if self.job is not None:
            out["job"] = self.job
        return out


class Refused(Exception):
    def __init__(self, rule: str, why: str) -> None:
        super().__init__(f"{rule}: {why}")
        self.rule = rule
        self.why = why


@dataclass
class Writer:
    table: Table
    role: str
    stores: Stores
    has: Callable[[str], bool]
    meter: Meter | None = None
    request: str | None = None          # the request a plan came from: its jobs start once
    # The classes the role's grant reads. The price counts an atom as held only when one of these
    # holds it, so a script's charge carries nothing of a class its role cannot read (`knownIn`,
    # `formal/Palace/Plane.lean`); none given, every atom is charged as new, the bound's top.
    reads: frozenset[Provenance] = frozenset()
    max_chars: int = 1200
    overlap_chars: int = 150
    landed: list[Outcome] = field(default_factory=list)
    started: set[str] = field(default_factory=set)

    def land(self, plan: Sequence[Effect]) -> list[Outcome]:
        self.price(plan)
        out = []
        for e in plan:
            o = self.one(e)
            self.landed.append(o)
            out.append(o)
        return out

    def price(self, plan: Sequence[Effect]) -> tuple[int, int]:
        """The plan's cost, counted before any of it is paid: its writes, each store the UNCHANGED
        check would not skip (a store the rules will refuse is counted too: the price is a bound)
        and each retire, link and run; and its embeds, the distinct atoms its stores would add
        that the plane does not hold (ING-5). Charged to the budget; returns the two counts.

        [banner: correction] It asked `known_atoms`, which answers for every class, so the charge
        a receipt reports told the script's role whether an atom exists in a class it cannot read
        (the formal audit; `known_eq`, `Witness.known_interferes`). It asks for the role's own
        classes now (`known_atoms_in`), so an atom only another class holds is charged as new: the
        price stays a bound, and the land itself still reuses the atom."""
        if self.meter is None:
            return (0, 0)
        writes = sum(1 for e in plan if not (isinstance(e, StoreEff) and self.unchanged(e)))
        self.meter.charge("write", writes)
        ids: set[str] = set()
        chunked: set[str] = set()                 # the same bytes stored twice are chunked once
        for e in plan:
            if isinstance(e, StoreEff) and not e.content.oversize \
                    and e.content.digest not in chunked:
                chunked.add(e.content.digest)
                ids |= {plane_atom_id(c.text)
                        for c in derive_chunks(e.content.data, max_chars=self.max_chars,
                                               overlap_chars=self.overlap_chars)}
        new = len(ids - set(self.stores.plane.known_atoms_in(sorted(ids), self.reads))) \
            if ids else 0
        self.meter.charge("embed", new)
        return (writes, new)

    def unchanged(self, e: StoreEff) -> bool:
        """The UNCHANGED check: the path holds these bytes, active, under the same label, and the
        plane holds their rows at this path, current. The invariant it keeps is that an active key
        implies current rows: a retire that died after its plane step and before its tombstone
        leaves the key active over retired rows, and the same bytes stored again must land."""
        if e.content.oversize:
            return False
        prev = self.stores.catalog.get(e.path)
        return (prev is not None and prev.active and prev.digest == e.content.digest
                and str(prev.provenance) == e.content.label
                and self.holds(e.path, e.content.data, e.content.label, e.content.digest))

    def one(self, e: Effect) -> Outcome:
        try:
            match e:
                case StoreEff():
                    return self.store(e)
                case RetireEff():
                    return self.retire(e)
                case LinkEff():
                    return self.link(e)
                case RunEff():
                    return self.run(e)
        except (Refused, ScriptError) as r:
            # a rule refused it, or the palace could not check it (a source that cannot be read
            # just now): the effect lands nothing and the plan goes on
            path = getattr(e, "path", getattr(e, "job", ""))
            why = f"{r.rule}: {r.why}" if isinstance(r, Refused) else f"R1: not checked: {r}"
            return Outcome(type(e).__name__.removesuffix("Eff").lower(), str(path), "refused",
                           why=why)
        raise TypeError(f"not an effect: {e!r}")  # pragma: no cover

    # store -------------------------------------------------------------------------------

    def store(self, e: StoreEff) -> Outcome:
        place = self.table.places.get(e.place)
        if place is None:
            raise Refused("R1", f"no place {e.place!r}")
        c, path, label = e.content, e.path, e.content.label
        if c.oversize:
            raise Refused("R1", f"{path!r} is {c.oversize} bytes, more than an item may have; "
                                "it stays as it was")
        if label != OBSERVED:
            # only an item's own bytes carry its label, under its own title (§E3): no script
            # composes the text or the title of a row it does not own the label of
            if c.origin is None or c.origin.kind != "item":
                raise Refused("R2", f"{label} content is an item's own bytes")
            if e.title != (c.origin.title or path):
                raise Refused("R2", f"a {label} row is titled by its item, not by a script")
        if label not in place.accepts:
            raise Refused("R2", f"{e.place!r} takes {', '.join(sorted(place.accepts))}, "
                                f"not {label}")
        if not self.table.may_write(self.role, e.place, path):
            raise Refused("R3", f"the role {self.role!r} does not write {path!r} in {e.place!r}")
        item = c.origin if c.origin is not None and c.origin.kind == "item" else None
        if item is not None and item.path != path:
            raise Refused("R4", f"content from {item.path!r} lands only there, not at {path!r}")
        owner = self.table.owner(path)
        if owner is not None and (item is None or item.of != owner.name):
            raise Refused("R8", f"{path!r} belongs to the source {owner.name!r}, and takes only "
                                "its items")
        catalog = self.stores.catalog
        prev = catalog.get(path)
        if prev is not None and str(prev.provenance) != label:
            raise Refused("R5", f"{path!r} holds {prev.provenance}; a {label} store never "
                                "replaces it")
        doc_id = self.identity(e, prev) if prev is None else None
        digest = c.digest
        if self.unchanged(e):
            return Outcome("store", path, "unchanged", digest=digest)
        parsed = parse_text(_decode(c.data), source_path=path, title=e.title, raw_bytes=c.data)
        record = ingest_note(parsed, self.stores.raw, provenance=Provenance(label),
                             max_chars=self.max_chars, overlap_chars=self.overlap_chars)
        index_amendment(record, [], self.stores.embedder, self.stores.plane)
        appended = False
        versions = self.stores.versions
        if place.versions and versions is not None:
            doc = catalog.doc_id_for(path) if prev is not None else (doc_id or path)
            rename = prev is None and any(other != path for other in catalog.paths_for(doc))
            if rename:                         # a rename is a version event (bp-031)
                versions.record(doc, record.digest)
                appended = True
            else:
                appended = record_version_if_new(versions, doc, record.digest) is not None
        attest_once(self.stores.attestor, agent_role=self.role, action=place.action,
                    digest=record.digest, event=appended)
        catalog.record(path, record.digest, e.title, provenance=Provenance(label),
                       doc_id=doc_id)                                       # the key, last
        return Outcome("store", path, "landed", digest=record.digest,
                       attestations=tuple(attested_by(self.stores.attestor, place.action,
                                                      record.digest)))

    def identity(self, e: StoreEff, prev: Any) -> str | None:
        """R6: a new path's identity is its own, one read off the item it stores, or one held at
        a path its source no longer has, with the same bytes. `None` is the path's own."""
        n, c = e.naming, e.content
        match n.kind:
            case "own":
                return None
            case "prop":
                if n.origin is None or c.origin is None or n.origin.kind != "id" \
                        or (n.origin.of, n.origin.path) != (c.origin.of, c.origin.path):
                    raise Refused("R6", "an identity read off an item is the one it declares, "
                                        "and names only that item")
                value = (n.value or "").strip()
                if not value or value == e.path:
                    return None                 # a blank declaration names no identity
                for q in self.stores.catalog.paths_for(value):
                    other = self.stores.catalog.get(q) if q != e.path else None
                    if other is not None and other.active and self.has(q):
                        raise Refused("R6", f"the identity {value!r} is {q!r}'s, which its "
                                            "source still has; two paths share no identity")
                return value
            case "held":
                q = n.value or ""
                held = self.stores.catalog.get(q)
                if held is None or held.digest != c.digest:
                    raise Refused("R6", f"{q!r} does not hold these bytes; an identity moves "
                                        "only with its bytes")
                if str(held.provenance) != c.label:
                    raise Refused("R6", f"{q!r} holds {held.provenance}; an identity moves only "
                                        "with its label")
                owner = self.table.owner(q)
                if owner is None or c.origin is None or c.origin.kind != "item" \
                        or owner.name != c.origin.of:
                    raise Refused("R6", f"{q!r} is not a path of the source these bytes came "
                                        "from; an identity moves only within its source")
                if self.has(q):
                    raise Refused("R6", f"{q!r} is still in its source; its identity stays")
                return str(self.stores.catalog.doc_id_for(q))
            case "named":
                if n.value == e.path:
                    return None
                raise Refused("R6", "a composed identity names nothing; an identity is the "
                                    "path's own, its item's, or a vanished path's")
        raise Refused("R6", f"unknown naming {n.kind!r}")  # pragma: no cover

    def holds(self, path: str, data: bytes, label: str, digest: str) -> bool:
        """Whether the plane holds a version's rows at `path`, current: an empty one has none to
        hold. (It asked `has_digest`, which a retired version's rows still answer.)"""
        if not derive_chunks(data, max_chars=self.max_chars, overlap_chars=self.overlap_chars):
            return True
        clearance = _HOLDS.get(label)
        return clearance is not None and self.stores.plane.holds_current(path, digest,
                                                                         clearance=clearance)

    # retire, link, run -------------------------------------------------------------------

    def retire(self, e: RetireEff) -> Outcome:
        place = self.table.places.get(e.place)
        if place is None:
            raise Refused("R1", f"no place {e.place!r}")
        if not self.table.may_retire(self.role, e.place, e.path):
            raise Refused("R3", f"the role {self.role!r} does not write {e.path!r} in "
                                f"{e.place!r}")
        prev = self.stores.catalog.get(e.path)
        if prev is None or not prev.active:
            raise Refused("R7", f"nothing active at {e.path!r}")
        if str(prev.provenance) not in place.accepts:
            raise Refused("R7", f"{e.path!r} is not in {e.place!r}")
        if str(prev.provenance) not in self.table.roles[self.role].retires:
            raise Refused("R7", f"the role {self.role!r} does not retire {prev.provenance} rows")
        if self.table.owner(e.path) is not None and self.has(e.path):
            raise Refused("R7", f"{e.path!r} is still in its source; retire only reconciles")
        self.stores.plane.delete_source(e.path)
        self.stores.catalog.tombstone(e.path)                    # the key, last (ING-7)
        return Outcome("retire", e.path, "retired")

    def link(self, e: LinkEff) -> Outcome:
        edges = self.stores.edges
        if edges is None:
            raise Refused("R1", "no relation store is open")
        if e.relation not in self.table.relations:
            raise Refused("R2", f"a relation is one of {', '.join(self.table.relations)}")
        for x in edges.all():
            if {x.u, x.v} == {e.a_digest, e.b_digest} and x.rel_type == e.relation \
                    and str(getattr(x, "provenance", "")) != "interpreted":
                raise Refused("R5", f"an authored {e.relation} edge holds {e.a!r} and {e.b!r}; "
                                    "an interpreted one never replaces it")
        sign, factor = self.table.relations[e.relation]
        edges.add(e.a_digest, e.b_digest, sign=sign, rel_type=e.relation, w=factor,
                  provenance="interpreted")
        return Outcome("link", f"{e.a} → {e.b}", "linked")

    def run(self, e: RunEff) -> Outcome:
        job = self.table.jobs.get(e.job)
        if job is None:
            raise Refused("R1", f"no job {e.job!r}")
        if e.job in self.started:
            raise Refused("R1", f"the plan starts {e.job} already; a request starts a job once")
        args: dict[str, Any] = {}
        for k, v in e.args:
            if k not in job.args:
                raise Refused("R1", f"{e.job} takes {', '.join(job.args) or 'no arguments'}")
            if not isinstance(v, int) or isinstance(v, bool) or not 0 <= v <= job.args[k]:
                raise Refused("R1", f"{e.job} {k}: an integer from 0 to {job.args[k]}")
            args[k] = v
        if self.stores.enqueue is None:
            raise Refused("R1", "no queue is open")
        from core.ingest.ingress import Busy

        try:
            job_id = self.stores.enqueue(job.kind, args, role=self.role, request=self.request)
        except Busy as b:
            raise Refused("R1", str(b)) from None
        self.started.add(e.job)
        return Outcome("run", e.job, "queued", job=job_id)
