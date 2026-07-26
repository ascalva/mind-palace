---
type: finding
id: finding-0218
status: open
created: 2026-07-26
updated: 2026-07-26
links:
  - ops/effect_catalog.py                              # ActuatorSpec — no identity/disclosure field
  - ops/effects.py                                     # ReversibilityClass — the single (resource) axis
  - docs/design-notes/hands-and-the-effector-layer.md  # draft — §3 type / §8 audit, the amendment target
  - docs/design-notes/world-facing-agency.md           # dn-world-facing-agency §2.3/§2.6 — the bright line this blocks
  - docs/findings/finding-0011.md                      # tier NONE, nothing wired — why the direction is safe today
ftype: design
origin_plan: orchestrator          # design-tier session authoring dn-world-facing-agency
route: orchestrator
resolution: null
---

# Actor identity is inexpressible in the effect catalog type — the non-impersonation bright line cannot be structurally enforced

## What

`ops/effect_catalog.py`'s `ActuatorSpec` carries `name`, `reversibility`, `scope`, `param_keys`,
`description`, `max_param_chars`; `CatalogEntry` adds `sandbox_profile`, `source`, `audited`,
`notes`. **No field anywhere in the type represents *as whom* an act is performed.** The class-3
hand `send_email` declares `param_keys=frozenset({"to", "subject", "body"})` — there is no `from`,
no sender identity, no disclosure marker; `sandbox_profile="egress:smtp"` pins *transport*, not
*identity*. So the distinction `dn-world-facing-agency` §2.3 draws as a bright line — "acting as
the system's own disclosed identity" vs "acting under the owner's identity (impersonation)" — is
not representable in the catalog's type system. The catalog's own contract is "a hand is
expressible iff it is cataloged"; identity is not part of what a catalog entry can express, so
impersonation is neither expressible **nor excludable** at this layer. "Excluded by kind" requires
the kind to exist in the type.

A sibling insufficiency in the same spec, owned by the design note rather than this finding
(`dn-world-facing-agency` §2.6): the single `ReversibilityClass` axis conflates resource
reversibility with relationship reversibility — a deletable-after-send message is honestly
REVERSIBLE ("the owner can undo") by the class-2 wording and would inherit the weaker gate.

## Why it matters

Today the direction of the gap is safe: no live entry point constructs any effector, `[effectors]
enabled = false`, max reachable tier NONE (finding-0011 — still true at this HEAD). But the owner
ruled the effector ceiling UP (autopilot ruling 2, 2026-07-26), so wiring is now intent, not
hypothesis. When the first class-2/3 hand wires, the most consequential safety property of a
world-facing act — *whose identity it goes out under* — would rest on convention and reviewer
memory, which is precisely what this project bans (`structural-enforcement`: a property is only
real when a test/ratchet proves it; the write_scope footgun was found 3× before it was enforced).
The bright line must be load-bearing in the type **before** ε moves, or we ship finding-0109's
shape: a ratified line the machinery quietly cannot hold.

## Re-entry condition

`dn-world-facing-agency` reaches ratification review → a plan whose `write_scope` includes
`docs/design-notes/hands-and-the-effector-layer.md` (draft, A8 agent-writable) amends its §3 type
and §8 audit with **both** axes (actor identity pinned to the system's own identity — the NN-12
pattern transposed — and `social_reversibility`, gate-at-the-stricter-axis), and the
`ops/effects.py`/`ops/effect_catalog.py` change lands with a property test asserting no cataloged
hand can express an owner-identity act (the F4 ratchet named in the design note). This finding
closes when that test is green — not when the wording lands.

## Routing

`design` → orchestrator. Design-changing discovery bearing on a draft design note
(`hands-and-the-effector-layer.md`) and on the wiring preconditions for the ruled ε raise; no
owner input needed beyond the `dn-world-facing-agency` ratification it feeds — batch there rather
than as a separate oq.
