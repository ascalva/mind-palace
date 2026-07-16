"""The tuning manifest — a per-lever POLICY overlay on the closed lever registry (dn-evaluation-
harness §2.6, the manifest half of E3a).

`config/tuning.toml` names, per registered lever (`ops/levers.LEVERS`), a small policy record:
which subsystem it belongs to (informational grouping), its autonomy mode, and an optional default
sweep objective. It is deliberately NOT a value source: a lever's admissible range and kind are
DERIVED from its `Lever` (the single source of truth), and its live value is read from the config /
overlay chain — the manifest never re-declares either, so it can never shadow `config/local.toml`
(the human's value channel always wins; note §2.6 "subordinate to local.toml").

Two structural properties the loader enforces (both fail-closed):
  * a manifest key MUST name a lever registered in `ops/levers.py` — an unregistered key raises at
    load (the note's "hard-fails on unknown keys" backstop; a never-tunable fixed point has no
    lever constructor and thus cannot be named);
  * `autonomy = "auto"` (the unattended E3b mode) is RESERVED in the schema but REJECTED here — this
    plan (E3a) implements only the attended `"propose"` path. `auto`-only fields (`auto_band`,
    `auto_max_step`, `auto_cooldown_runs`) are likewise unknown keys and raise.

`resolved_fingerprint()` is the canonical sha256 of the fully-resolved manifest (note §2.1's
`config_fingerprint`): order-insensitive (a sorted-key JSON of the resolved policy over every
registered lever), so reordering the TOML leaves it unchanged, while any policy or registry-bound
change moves it. E3a-1's sweep engine consumes this as its config-identity key component.
"""

from __future__ import annotations

import hashlib
import json
import tomllib
from dataclasses import dataclass
from pathlib import Path

from ops.levers import LEVERS, Lever

# The canonical on-disk manifest (a sibling of config/local.toml, but policy-only).
MANIFEST_PATH = Path(__file__).resolve().parents[2] / "config" / "tuning.toml"

# The two autonomy modes (note §2.6). E3a accepts only PROPOSE; AUTO is reserved for E3b.
AUTONOMY_PROPOSE = "propose"
AUTONOMY_AUTO = "auto"
DEFAULT_AUTONOMY = AUTONOMY_PROPOSE  # the value when the field is absent (note §2.6)

# The keys a per-lever policy table may carry in E3a. Anything else — including the reserved
# auto-mode fields — is an unknown key and fails closed at load (note §2.6 backstop).
_POLICY_KEYS = frozenset({"subsystem", "autonomy", "objective"})


class UnregisteredLever(KeyError):
    """A manifest key names a lever not in `ops/levers.LEVERS` (fail-closed; a fixed point or a
    typo). A never-tunable fixed point has no lever constructor and can never be named here."""


class AutoModeNotSupported(NotImplementedError):
    """`autonomy = "auto"` — the unattended mode — is E3b, out of scope in E3a. The schema reserves
    the field; this plan accepts only `"propose"`."""


@dataclass(frozen=True)
class LeverPolicy:
    """The resolved policy for one lever. POLICY ONLY — carries no live value; range/kind are read
    from the lever registry on demand, never stored here (single source of truth)."""

    lever: str
    subsystem: str
    autonomy: str
    objective: str | None = None

    @property
    def registry(self) -> Lever:
        return LEVERS[self.lever]

    @property
    def range(self) -> tuple[float, float]:
        """[lo, hi] DERIVED from the lever registry — never declared in the manifest."""
        lev = self.registry
        return (lev.lo, lev.hi)


def _parse_policy(name: str, body: dict[str, object]) -> LeverPolicy:
    """Resolve one `[tuning.<name>]` table into a LeverPolicy, fail-closed on any surprise."""
    lever = LEVERS[name]  # caller guarantees name is registered
    unknown = set(body) - _POLICY_KEYS
    if unknown:
        raise ValueError(
            f"lever {name!r}: unknown manifest key(s) {sorted(unknown)}; "
            f"allowed in E3a: {sorted(_POLICY_KEYS)} "
            f"(auto-mode fields are E3b, out of scope)"
        )
    autonomy = str(body.get("autonomy", DEFAULT_AUTONOMY))
    if autonomy == AUTONOMY_AUTO:
        raise AutoModeNotSupported(
            f"lever {name!r}: autonomy='auto' is the E3b unattended mode (out of scope in E3a); "
            f"only '{AUTONOMY_PROPOSE}' is accepted here"
        )
    if autonomy != AUTONOMY_PROPOSE:
        raise ValueError(
            f"lever {name!r}: unknown autonomy {autonomy!r}; expected '{AUTONOMY_PROPOSE}'"
        )
    subsystem = str(body.get("subsystem", lever.section))
    obj = body.get("objective")
    objective = str(obj) if obj is not None else None
    return LeverPolicy(lever=name, subsystem=subsystem, autonomy=autonomy, objective=objective)


@dataclass(frozen=True)
class TuningManifest:
    """The resolved per-lever policy overlay over the WHOLE registry. Every registered lever has a
    policy (defaulting to `propose` / the lever's own section when the TOML omits it), so the
    manifest is a complete, order-independent picture of the tuning surface."""

    policies: dict[str, LeverPolicy]

    def policy(self, lever: str) -> LeverPolicy:
        """The resolved policy for `lever` (raises `UnregisteredLever` for an unknown name)."""
        try:
            return self.policies[lever]
        except KeyError:
            raise UnregisteredLever(
                f"unknown lever {lever!r}; registered: {sorted(LEVERS)}"
            ) from None

    def resolved(self) -> dict[str, dict[str, object]]:
        """The canonical resolved manifest: every registered lever → its policy PLUS the
        registry-derived structural facts (kind, [lo, hi]). Sorted, value-free, fingerprint-ready.
        This is POLICY + structure, never a live lever value — so it can never shadow local.toml."""
        out: dict[str, dict[str, object]] = {}
        for name in sorted(self.policies):
            p = self.policies[name]
            lev = LEVERS[name]
            out[name] = {
                "subsystem": p.subsystem,
                "autonomy": p.autonomy,
                "objective": p.objective,
                "kind": lev.kind.value,
                "range": [lev.lo, lev.hi],
            }
        return out

    def resolved_fingerprint(self) -> str:
        """sha256 of the canonical resolved manifest (note §2.1 `config_fingerprint`).

        Canonical form = sorted-key, whitespace-free JSON of `resolved()`. Order-insensitive (a
        TOML reorder leaves it unchanged); moves iff a policy value or a registry bound changes."""
        canonical = json.dumps(
            self.resolved(), sort_keys=True, separators=(",", ":"), ensure_ascii=True
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def load_manifest(path: Path | None = None) -> TuningManifest:
    """Parse `config/tuning.toml` into a validated `TuningManifest` over `ops.levers.LEVERS`.

    A missing file is legal — every lever resolves to its default policy (`autonomy='propose'`). A
    `[tuning.<name>]` table naming an unregistered lever raises `UnregisteredLever` (fail-closed);
    `autonomy='auto'` raises `AutoModeNotSupported`; any other unknown key raises `ValueError`."""
    src = path or MANIFEST_PATH
    raw = tomllib.loads(src.read_text(encoding="utf-8")) if src.exists() else {}
    tuning = raw.get("tuning", {})
    if not isinstance(tuning, dict):
        raise ValueError("config/tuning.toml: [tuning] must be a table of per-lever policies")

    policies: dict[str, LeverPolicy] = {}
    for name, body in tuning.items():
        if name not in LEVERS:
            raise UnregisteredLever(
                f"manifest names lever {name!r}, which is not registered in ops/levers.py; "
                f"registered: {sorted(LEVERS)} (a fixed point has no lever and cannot be named)"
            )
        if not isinstance(body, dict):
            raise ValueError(f"lever {name!r}: [tuning.{name}] must be a table")
        policies[name] = _parse_policy(name, body)

    # Fill every registered lever the TOML omits with its default policy, so the resolved manifest
    # (and its fingerprint) covers the whole registry — a complete, order-independent identity.
    for name, lever in LEVERS.items():
        policies.setdefault(
            name,
            LeverPolicy(
                lever=name, subsystem=lever.section, autonomy=DEFAULT_AUTONOMY, objective=None
            ),
        )
    return TuningManifest(policies=policies)
