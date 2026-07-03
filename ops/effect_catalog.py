# ── Family 1 boundary (labelings & information-flow) · symbols in docs/NOTATION.md ──
# OBJECT:    the effector catalog — the reviewed registry of every hand the layer can express,
#            each carrying the §8 audit metadata that admitted it (hands-and-the-effector-layer.md
#            §8; the SKILL-mining pipeline, docs/design-notes/skill-mining-pipeline.md).
# INVARIANT: a hand is EXPRESSIBLE iff it is cataloged (get_actuator is fail-closed); every entry
#            declares the reversibility class that sets w(β) and a sandbox exec profile; the acting
#            classes are cataloged but UNREACHABLE in the wired system (EffectView ceiling ε=0).
# ENFORCED:  structural — get_actuator/get_entry raise on an uncataloged name; the audit fields are
#            required, so a half-audited hand cannot be added silently.
"""The effector catalog + the SKILL-mining pipeline as data (Track G, item G4).

The catalog is the SINGLE source of truth for the hands the effector layer can express. Each
entry is the recorded outcome of the §8 security audit run as a **repeatable process** (the
SKILL-mining pipeline, `docs/design-notes/skill-mining-pipeline.md`):

    read the source as untrusted → re-implement NATIVELY (never import third-party skill code)
      → classify reversibility (this sets w(β)) → mint SCOPE, not a credential
      → assign the §11 sandbox exec profile → attest proposal + approval → catalog + property-test.

Adding a hand is therefore a reviewed diff to `_CATALOG` below — the lever-registry move applied
to the effector layer: the gate (`ops/effect_gate`) *consumes* this registry but does not own it,
so a proposal can only ever target a hand that has been through the audit (`get_actuator` raises on
anything else, exactly like `get_lever`).

Why the acting classes are here yet still safe. `draft_reply` / `calendar_hold` / `stage_file`
(REVERSIBLE, β small) and `send_email` (IRREVERSIBLE, β = ∞) are cataloged so G5/G6 can reference
them — but a cataloged hand is not a *reachable* hand. Three independent structural facts keep
them off:

  * the wired sensing surface admits effects at ceiling ε = SENSING (`core.sensing.SensingHandoff`
    → `EffectView.admit(..., ceiling=SENSING)`), so a non-sensing effect raises before it reaches
    any handoff (the §4 filtration as a type);
  * an `Effect` of a non-sensing class is unconstructable without an approval reference covering
    w(β) (`ops.effects.Effect.__post_init__`); and
  * the gate denies unless a matching, unexpired, per-action scoped capability was minted
    (`ops.effect_gate.effect_gate_admits`) — no ambient authority exists to fire one.

So cataloging a hand records that it *passed the audit*; enabling it is a separate, deliberate act
(raising ε past its class once its property tests are green — §4).
"""

from __future__ import annotations

from dataclasses import dataclass

from ops.effects import ReversibilityClass

# A generous ceiling on one param VALUE for hands whose payload is real content (a drafted body,
# a staged file) rather than a query term. It is hygiene layered on the per-actuator key allowlist,
# never the security boundary (the boundary is: params are DATA to a reviewed native actuator, and
# the actuator resolves fail-closed). Sensing keeps the tight 256-char default.
_CONTENT_PARAM_CHARS = 8 * 1024
_FILE_PARAM_CHARS = 64 * 1024


@dataclass(frozen=True)
class ActuatorSpec:
    """One registered hand — exactly what the GATE needs to decide about it: its name, its
    reversibility class (which sets w(β)), the capability scope it requires, and the CLOSED set of
    param keys it accepts. `max_param_chars` caps one param value (per-actuator, so a draft body is
    not forced through the sensing-sized 256-char hole). The richer audit metadata lives on
    `CatalogEntry`, which wraps this — the gate does not need to know a hand's sandbox profile to
    decide, only its class and scope."""

    name: str
    reversibility: ReversibilityClass
    scope: str                      # the ScopedCapability.scope this actuator requires
    param_keys: frozenset[str]      # closed allowlist; unknown keys are refused, not ignored
    description: str = ""
    max_param_chars: int = 256      # per-actuator value cap (sensing = 256; content hands larger)


@dataclass(frozen=True)
class CatalogEntry:
    """The audited catalog record for one hand: its gate-facing `spec` plus the §8 audit evidence.

    `sandbox_profile` names the §11 powerless exec profile the hand runs under (a label the
    pipeline doc defines — the type carries the reference, not the enforcement). `source` records
    where the capability was mined from (an ecosystem `SKILL.md`, or "native"), treated as
    untrusted and re-implemented. `audited` is True only when every step of the §8 checklist has
    been walked — a required field, so a half-audited hand cannot be added without saying so."""

    spec: ActuatorSpec
    sandbox_profile: str            # the §11 exec profile (e.g. "net-off", "egress:sense_fetch")
    source: str = "native"          # the mined SKILL.md, or "native"; the source is untrusted
    audited: bool = False           # every §8 step walked (read→reimplement→classify→…→test)
    notes: str = ""


# --- The catalog: every hand the layer can express, each with its audit record -----------------
#
# ROLLOUT ORDER (§4 filtration): sensing (β = 0) is live-adjacent (flag-off); the acting classes
# below are cataloged (audited) but reachable only by raising ε past their class — "you do not get
# a class until the one below is solid". Widening this table is a visible, reviewable diff.

_CATALOG: tuple[CatalogEntry, ...] = (
    # ---- class 1: read-only sensing (β = 0) — G3, live-adjacent, flag-off --------------------
    CatalogEntry(
        spec=ActuatorSpec(
            name="sense_fetch",
            reversibility=ReversibilityClass.SENSING,
            scope="sense:fetch",
            param_keys=frozenset({"upstream", "terms"}),
            description="read-only HTTPS GET against a named, edge-allowlisted upstream (β = 0).",
        ),
        sandbox_profile="egress:sense_fetch",   # https-only, no-redirect, size-capped, no creds
        source="native",
        audited=True,
        notes="G3. Resolves a NAME to a URL only inside Zone B; core type cannot hold an address.",
    ),
    # ---- class 2: reversible writes (β small) — G5, propose/stage, owner can undo -------------
    CatalogEntry(
        spec=ActuatorSpec(
            name="draft_reply",
            reversibility=ReversibilityClass.REVERSIBLE,
            scope="draft:reply",
            param_keys=frozenset({"to", "subject", "body"}),
            description="stage a DRAFT reply (never sent); reversible — the owner deletes it.",
            max_param_chars=_CONTENT_PARAM_CHARS,
        ),
        sandbox_profile="net-off:stage-local",  # writes a local draft file; no network at all
        source="native",
        audited=True,
        notes="G5. Body tailored core-side via a MirrorView (authored-only); output is a proposal.",
    ),
    CatalogEntry(
        spec=ActuatorSpec(
            name="calendar_hold",
            reversibility=ReversibilityClass.REVERSIBLE,
            scope="calendar:hold",
            param_keys=frozenset({"title", "start", "end", "notes"}),
            description="stage a TENTATIVE calendar hold (not published); reversible.",
            max_param_chars=_CONTENT_PARAM_CHARS,
        ),
        sandbox_profile="net-off:stage-local",
        source="native",
        audited=True,
        notes="G5. Materializes an .ics-style hold into the staging dir; rollback unlinks it.",
    ),
    CatalogEntry(
        spec=ActuatorSpec(
            name="stage_file",
            reversibility=ReversibilityClass.REVERSIBLE,
            scope="file:stage",
            param_keys=frozenset({"name", "content"}),
            description="stage a file into the drafts area (not committed anywhere); reversible.",
            max_param_chars=_FILE_PARAM_CHARS,
        ),
        sandbox_profile="net-off:stage-local",
        source="native",
        audited=True,
        notes="G5. A staged artifact the owner reviews; rollback removes it. No egress.",
    ),
    # ---- class 3: irreversible / external (β = ∞) — G6, full gate + JIT scoped credential -----
    CatalogEntry(
        spec=ActuatorSpec(
            name="send_email",
            reversibility=ReversibilityClass.IRREVERSIBLE,
            scope="send:email",
            param_keys=frozenset({"to", "subject", "body"}),
            description="SEND an email — no undo. Full gate; JIT scoped credential; attested.",
            max_param_chars=_CONTENT_PARAM_CHARS,
        ),
        sandbox_profile="egress:smtp",          # edge-side send transport; not enabled
        source="native",
        audited=True,
        notes="G6. The credential is minted per-action at send time and never held; attested.",
    ),
)

CATALOG: dict[str, CatalogEntry] = {e.spec.name: e for e in _CATALOG}
# The gate-facing registry — the specs alone, keyed by name. Derived from the catalog so there is
# exactly ONE source of truth; `ops/effect_gate` imports this and `get_actuator` from here.
ACTUATORS: dict[str, ActuatorSpec] = {name: e.spec for name, e in CATALOG.items()}


def get_actuator(name: str) -> ActuatorSpec:
    """Look up a cataloged hand's gate-facing spec. Raises (fail-closed) if `name` is not in the
    catalog — a proposal can only ever target a hand that passed the §8 audit."""
    try:
        return ACTUATORS[name]
    except KeyError:
        raise KeyError(f"unknown actuator {name!r}; cataloged: {sorted(ACTUATORS)}") from None


def get_entry(name: str) -> CatalogEntry:
    """Look up a cataloged hand's full audit record. Fail-closed on an uncataloged name."""
    try:
        return CATALOG[name]
    except KeyError:
        raise KeyError(f"unknown actuator {name!r}; cataloged: {sorted(CATALOG)}") from None


def actuators_for(reversibility: ReversibilityClass) -> tuple[CatalogEntry, ...]:
    """Every cataloged hand of a given reversibility class (the §4 filtration slice) — the reviewed
    contents of Effects at exactly this blast-radius band, for the catalog + rollout gate."""
    return tuple(e for e in _CATALOG if e.spec.reversibility is reversibility)
