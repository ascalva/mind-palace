# ── Family 1 boundary (labelings & information-flow) · symbols in docs/NOTATION.md ──
# OBJECT:    the clearance lattice — a capability C ⊆ P (the provenance classes a read may return)
#            and the records a read under C produces: Row[L], Occupancy[L], PlaneHit[L]
#            (dn-vector-membership-store Amendment A3).
# INVARIANT: no record of a class c ∉ C is constructible by a read under C. Sealed constructors
#            demand the private mint AND re-check the class against the clearance; the label L is
#            the class set at the TYPE level (a union of `Provenance` Literals, covariant), so a
#            mis-flow — observed rows into a mirror-only consumer — is a mypy error at authorship.
# ENFORCED:  structural (sealed mint + runtime re-check: the MirrorView move generalized from MR to
#            every clearance) + static (mypy: the subset lattice of classes IS the subtype lattice
#            of Literal unions) + guard (tests/integrity: the clearance-holder allowlist, the
#            noninterference property, the mypy negative test).
"""Clearances: who may read which provenance classes, as values AND as types (A3, owner ruling
2026-10-29: "accessible records without the correct permission should be unrepresentable, and also
enforced by the type system").

**A clearance is a capability, not a filter argument.** Before A3 every read took a free
`provenances=` set, so the firewall held only as long as each call site passed the right set — "a
simple condition". A `Clearance[L]` can be minted only by an authority, every read requires one (no
default, no `None`), and every record a read returns is constructed through a sealed constructor
that re-checks its class against the clearance it was read under.

The pieces, and the pattern each one is:

* **Object-capability minting (no ambient authority).** `_mint` and `_MINT` are module-private.
  The named grants below (`MIRROR_READ` … `MAINTENANCE_READ`) and the query engine's admitted-scope
  mint (`core/query.py`, where admission IS the permission) are the only authorities;
  `tests/integrity/test_clearance_holders.py` pins which modules may import which grant — the way
  the import firewall pins the network allowlist.
* **Information-flow labels as phantom types.** `L` ranges over unions of `Literal[Provenance.X]`.
  Because a union of literals is a subtype of another exactly when its members are a subset, the
  subset lattice of classes IS mypy's subtype lattice — no parallel tag hierarchy to keep in sync.
  The label is covariant, so `Row[Literal[AUTHORED_SOLO]]` flows into a `Row[MirrorClass]` sink
  and `Row[Literal[OBSERVED]]` does not (measured on mypy 2.2.0).
* **Sealed constructors / smart constructors.** `Row`, `Occupancy` and `PlaneHit` demand the
  private mint and a clearance that admits the record's class. Records are immutable; `narrow` is
  the only checked way from a broad label to a narrow one ("parse, don't validate").

Why slotted classes rather than frozen dataclasses: a frozen dataclass synthesizes `__replace__`
(3.13+), which takes the labelled field as a PARAMETER, so mypy rejects the covariant label and the
lattice collapses to invariance (measured: the subset flows were rejected). Read-only properties
keep the label covariant.

The binary `Authored`/`Derived` shadow in `core.kernel.provenance` is this lattice's two-point
quotient (bp-009 §11 recorded binary grain as a default because the classes have no ORDER; the set
lattice needs none — G8).

Pure kernel module: stdlib + the provenance and scope vocabulary only; no store, no I/O.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping, Sequence
from types import MappingProxyType
from typing import Any, Literal, NoReturn, cast, final

from core.kernel.provenance import MIRROR_READABLE, Provenance
from core.kernel.scope import Stratum

# The label `L` (a PEP 695 parameter on each class below) is a set of provenance classes at the type
# level. It appears only in read-only (return) positions, so mypy infers it COVARIANT: a record
# readable under a narrower clearance is readable under any wider one, never the reverse.
# tests/unit/test_clearance.py pins that inference — if a refactor puts `L` in a parameter position,
# the lattice collapses to invariance and those tests go red.

type MirrorClass = Literal[Provenance.AUTHORED_SOLO, Provenance.AUTHORED_DIALOGUE]
type DialogueClass = Literal[Provenance.AUTHORED_DIALOGUE, Provenance.OBSERVED]
type CuratedClass = Literal[Provenance.CURATED]
type CodeClass = Literal[Provenance.CODE]
type ObservedClass = Literal[Provenance.OBSERVED]


class ClearanceViolation(PermissionError):
    """A record whose class the clearance does not admit was about to be constructed. Raised, never
    filtered: reaching this means a read path asked for something it was not cleared for, which is
    a bug to see, not a row to drop quietly."""


class ClearanceForgery(TypeError):
    """A sealed constructor was called without the private mint — someone outside the authorities
    tried to manufacture a clearance or a record."""


@final
class _Mint:
    """The private token every sealed constructor demands. One instance (`_MINT`), module-private:
    holding it is what "being an authority" means at runtime."""

    __slots__ = ()


_MINT = _Mint()


def _require_mint(mint: object) -> None:
    if mint is not _MINT:
        raise ClearanceForgery("clearances and cleared records are minted only by an authority "
                               "(core.kernel.clearance)")


def _class_of(value: object) -> Provenance | None:
    try:
        return Provenance(str(value))
    except ValueError:
        return None


@final
class Clearance[L: Provenance]:
    """The capability to read records of exactly `classes`. Immutable; minted only by authorities.

    `authority` names who minted it ("mirror", "query:search", "maintenance:…") so a read can be
    attributed in logs and tests. Equality is by `classes` alone: two authorities that grant the
    same classes grant the same reads."""

    __slots__ = ("_authority", "_classes")
    _authority: str
    _classes: frozenset[Provenance]

    def __init__(self, classes: Iterable[Provenance | str], authority: str, *,
                 mint: _Mint) -> None:
        _require_mint(mint)
        object.__setattr__(self, "_classes", frozenset(Provenance(str(c)) for c in classes))
        object.__setattr__(self, "_authority", authority)

    def __setattr__(self, name: str, value: object) -> NoReturn:
        raise AttributeError("a Clearance is immutable")

    @property
    def classes(self) -> frozenset[Provenance]:
        return self._classes

    @property
    def authority(self) -> str:
        return self._authority

    def admits(self, provenance: object) -> bool:
        """Is a record of this class readable under this clearance? Accepts a `Provenance` or its
        string value; anything that is not a class at all is not admitted (fail closed)."""
        cls = _class_of(provenance)
        return cls is not None and cls in self.classes

    def __contains__(self, provenance: object) -> bool:
        return self.admits(provenance)

    def __iter__(self) -> Iterator[Provenance]:
        return iter(sorted(self.classes))

    def __len__(self) -> int:
        return len(self.classes)

    def meet(self, other: Clearance[Provenance]) -> Clearance[L]:
        """Delegation can only narrow: the intersection, still labelled `L` (a subset of this
        clearance's classes is admitted by any type this clearance's label admits)."""
        return Clearance(self.classes & other.classes, f"{self.authority}∧{other.authority}",
                         mint=_MINT)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Clearance) and other.classes == self.classes

    def __hash__(self) -> int:
        return hash(self.classes)

    def __repr__(self) -> str:
        return f"Clearance({sorted(c.value for c in self.classes)}, by {self.authority!r})"


def _mint(classes: Iterable[Provenance | str], authority: str) -> Clearance[Provenance]:
    """The private mint, top-labelled. Callers outside this module are pinned by the holder
    allowlist (the query engine mints from an ADMITTED query's scope; nothing else should)."""
    return Clearance(classes, authority, mint=_MINT)


# ── The named grants ───────────────────────────────────────────────────────────────────────────
# Each grant's runtime classes equal the members of its label (tests/unit/test_clearance.py checks
# every pair, so a grant cannot say one thing to the checker and another to the store).

#: The mirror: the owner's own words (MIRROR_READABLE). The firewall's definition, and the safest
#: read the system has — freely importable.
MIRROR_READ: Clearance[MirrorClass] = Clearance(MIRROR_READABLE, "mirror", mint=_MINT)
#: Deliberate, non-default grants (dn-external-grounding; dn-cross-strata-dreamer XS-a).
CURATED_READ: Clearance[CuratedClass] = Clearance({Provenance.CURATED}, "curated", mint=_MINT)
CODE_READ: Clearance[CodeClass] = Clearance({Provenance.CODE}, "code", mint=_MINT)
DIALOGUE_READ: Clearance[DialogueClass] = Clearance(
    {Provenance.AUTHORED_DIALOGUE, Provenance.OBSERVED}, "dialogue", mint=_MINT)
OBSERVED_READ: Clearance[ObservedClass] = Clearance({Provenance.OBSERVED}, "observed", mint=_MINT)
#: Every class — structural maintenance only (migration, gauges, census, compaction, rekeying).
#: Never an agent's and never the mirror's; its importers are pinned by the holder allowlist.
MAINTENANCE_READ: Clearance[Provenance] = Clearance(tuple(Provenance), "maintenance", mint=_MINT)


# ── Strata → classes (moved from core/query.py `_PROVENANCES`, so every mint reads one table) ──

STRATUM_CLASSES: Mapping[Stratum, frozenset[Provenance]] = {
    Stratum.MIRROR: MIRROR_READABLE,
    Stratum.MIRROR_AUTHORED: MIRROR_READABLE,
    Stratum.CURATED: frozenset({Provenance.CURATED}),
    Stratum.INTERPRETED: frozenset({Provenance.INTERPRETED}),
    Stratum.OBSERVED: frozenset({Provenance.OBSERVED}),
    Stratum.DIALOGUE: frozenset({Provenance.OBSERVED, Provenance.AUTHORED_DIALOGUE}),
    Stratum.DIALOGUE_TRANSCRIPT: frozenset({Provenance.OBSERVED, Provenance.AUTHORED_DIALOGUE}),
    Stratum.REFERENCE: frozenset({Provenance.CODE}),
    Stratum.REFERENCE_REPO: frozenset({Provenance.CODE}),
}


def classes_of(strata: Iterable[Stratum]) -> frozenset[Provenance]:
    """The provenance classes a set of strata names (a stratum with no stored rows names none)."""
    out: set[Provenance] = set()
    for s in strata:
        out |= STRATUM_CLASSES.get(s, frozenset())
    return frozenset(out)


# ── Cleared records ────────────────────────────────────────────────────────────────────────────

@final
class Row[L: Provenance](Mapping[str, Any]):
    """A store row read under a clearance: the mapping shape every consumer reads, labelled with
    the classes it may hold and immutable by construction — a `Mapping` has no mutators at all, so
    a cleared row cannot be edited or relabelled in place (there is nothing to refuse; the
    operation does not exist). Built only by a store holding the private mint, and only when the
    clearance admits the row's `provenance`. A copy (`dict(row)`, `{**row}`) is a plain dict and
    carries no label: whoever builds a new value answers for it."""

    __slots__ = ("_fields",)
    _fields: Mapping[str, Any]

    def __init__(self, clearance: Clearance[L], fields: Mapping[str, Any], *,
                 mint: _Mint) -> None:
        _require_mint(mint)
        if not clearance.admits(fields.get("provenance")):
            raise ClearanceViolation(
                f"a {fields.get('provenance')!r} row is not readable under {clearance!r}")
        object.__setattr__(self, "_fields", MappingProxyType(dict(fields)))

    def __setattr__(self, name: str, value: object) -> NoReturn:
        raise AttributeError("a cleared Row is immutable")

    def __getitem__(self, key: str) -> Any:
        return self._fields[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._fields)

    def __len__(self) -> int:
        return len(self._fields)

    @property
    def provenance(self) -> L:
        return cast(L, Provenance(str(self._fields["provenance"])))  # admitted at construction

    def __repr__(self) -> str:
        return f"Row({dict(self._fields)!r})"

    def __reduce__(self) -> tuple[type[dict[str, Any]], tuple[dict[str, Any]]]:
        return (dict, (dict(self._fields),))   # pickles/copies as a plain, unlabelled dict


@final
class Occupancy[L: Provenance]:
    """One cleared occupancy (A3.2): atom `atom_id` sits in version `(source_path, digest)` of a
    document of class `provenance`, at `chunk_index`. Constructed only under a clearance that
    admits the class, by a holder of the private mint (the plane)."""

    __slots__ = ("_atom_id", "_chunk_index", "_current", "_digest", "_provenance",
                 "_source_path", "_title")
    _atom_id: str
    _chunk_index: int
    _current: bool
    _digest: str
    _provenance: Provenance
    _source_path: str
    _title: str

    def __init__(self, clearance: Clearance[L], *, atom_id: str, source_path: str,
                 digest: str, chunk_index: int, title: str, provenance: Provenance | str,
                 current: bool, mint: _Mint) -> None:
        _require_mint(mint)
        if not clearance.admits(provenance):
            raise ClearanceViolation(
                f"a {provenance!r} occupancy is not readable under {clearance!r}")
        set_ = object.__setattr__
        set_(self, "_atom_id", atom_id)
        set_(self, "_source_path", source_path)
        set_(self, "_digest", digest)
        set_(self, "_chunk_index", int(chunk_index))
        set_(self, "_title", title)
        set_(self, "_provenance", Provenance(str(provenance)))
        set_(self, "_current", bool(current))

    def __setattr__(self, name: str, value: object) -> NoReturn:
        raise AttributeError("an Occupancy is immutable")

    @property
    def atom_id(self) -> str:
        return self._atom_id

    @property
    def source_path(self) -> str:
        return self._source_path

    @property
    def digest(self) -> str:
        return self._digest

    @property
    def chunk_index(self) -> int:
        return self._chunk_index

    @property
    def title(self) -> str:
        return self._title

    @property
    def provenance(self) -> L:
        return cast(L, self._provenance)     # admitted at construction

    @property
    def current(self) -> bool:
        return self._current

    def _key(self) -> tuple[str, str, str, int, str, str, bool]:
        return (self.atom_id, self.source_path, self.digest, self.chunk_index, self.title,
                self._provenance.value, self.current)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Occupancy) and other._key() == self._key()

    def __hash__(self) -> int:
        return hash(self._key())

    def __repr__(self) -> str:
        return (f"Occupancy({self.source_path}@{self.digest[:8]}#{self.chunk_index} "
                f"{self._provenance.value} atom={self.atom_id[:16]} "
                f"{'current' if self.current else 'superseded'})")


@final
class PlaneHit[L: Provenance]:
    """One search hit on the shared plane: an atom's text and distance plus the occupancies the
    clearance admits. Exists only with at least one cleared occupancy — an atom no cleared document
    holds is not a hit, whatever the ANN prefilter cache said."""

    __slots__ = ("_atom_id", "_distance", "_occupancies", "_text", "_vector")
    _atom_id: str
    _distance: float | None
    _occupancies: tuple[Occupancy[L], ...]
    _text: str
    _vector: Sequence[float] | None

    def __init__(self, clearance: Clearance[L], *, atom_id: str, text: str,
                 distance: float | None, vector: Sequence[float] | None,
                 occupancies: Sequence[Occupancy[L]], mint: _Mint) -> None:
        _require_mint(mint)
        if not occupancies:
            raise ClearanceViolation(f"atom {atom_id[:16]} has no occupancy readable under "
                                     f"{clearance!r}; it cannot be a hit")
        for occ in occupancies:
            if occ.atom_id != atom_id or not clearance.admits(occ.provenance):
                raise ClearanceViolation(f"{occ!r} does not belong to this cleared hit")
        set_ = object.__setattr__
        set_(self, "_atom_id", atom_id)
        set_(self, "_text", text)
        set_(self, "_distance", distance)
        set_(self, "_vector", vector)
        set_(self, "_occupancies", tuple(occupancies))

    def __setattr__(self, name: str, value: object) -> NoReturn:
        raise AttributeError("a PlaneHit is immutable")

    @property
    def atom_id(self) -> str:
        return self._atom_id

    @property
    def text(self) -> str:
        return self._text

    @property
    def distance(self) -> float | None:
        return self._distance

    @property
    def vector(self) -> Sequence[float] | None:
        return self._vector

    @property
    def occupancies(self) -> tuple[Occupancy[L], ...]:
        return self._occupancies

    def __repr__(self) -> str:
        return (f"PlaneHit(atom={self.atom_id[:16]} d={self.distance} "
                f"occupancies={len(self.occupancies)})")


# ── Narrowing: the only checked way from a broad label to a narrow one ─────────────────────────

def narrow_row[L: Provenance](row: Row[Provenance], to: Clearance[L]) -> Row[L] | None:
    """`row` relabelled under the narrower clearance `to`, or None when `to` does not admit it."""
    if not to.admits(row.get("provenance")):
        return None
    return Row(to, row, mint=_MINT)


def narrow_hit[L: Provenance](hit: PlaneHit[Provenance],
               to: Clearance[L]) -> PlaneHit[L] | None:
    """`hit` with only the occupancies `to` admits, or None when none remain."""
    kept = [Occupancy(to, atom_id=o.atom_id, source_path=o.source_path, digest=o.digest,
                      chunk_index=o.chunk_index, title=o.title, provenance=o.provenance,
                      current=o.current, mint=_MINT)
            for o in hit.occupancies if to.admits(o.provenance)]
    if not kept:
        return None
    return PlaneHit(to, atom_id=hit.atom_id, text=hit.text, distance=hit.distance,
                    vector=hit.vector, occupancies=kept, mint=_MINT)
