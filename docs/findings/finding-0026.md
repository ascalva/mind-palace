---
type: finding
id: finding-0026
status: routed
ftype: discovery
origin_plan: null            # surfaced in owner–chat design review, 2026-07-10
route: orchestrator
created: 2026-07-10
updated: 2026-07-10
links:
  - docs/research/security-planes.md                     # the spec whose code plane this finding shows unenforced
  - docs/design-notes/type-system-as-core-audit.md       # the design note proposed as the remedy
resolution: null
---

# finding-0026 — The code plane is assigned to the type system, but no type checker runs

> **Triage 2026-07-10 (/triage):** open → routed (orchestrator). Design-changing discovery →
> **promotion proposed: ratify `type-system-as-core-audit.md`** (already drafted, committed
> `38ccc85`, `warrant: finding-0026` in its front-matter — the three-place P/P′/warrant link
> is in place). Batched for the owner at `owner-questions.md` **oq-0012**; flips to
> `promoted` on ratification, after which `/graduate` can decompose the note's B-items.
> Declining leaves the code plane enforcement-free as `security-planes.md` currently
> (mis)states it. Re-entry per oq-0012's park condition.

## What

`security-planes.md` composes three planes: types enforce the **code plane**,
provenance labels enforce the **data plane**, object capabilities enforce the
**boundary**. The data plane and the boundary are enforced by code that runs.
The code plane is enforced by nothing.

Verified against the repository, 2026-07-10:

- `pyproject.toml` declares no `[tool.mypy]` section. The `dev` optional
  dependency group is `pytest`, `ruff`, `hypothesis` — no type checker is
  installed.
- No standalone checker config exists anywhere in the tree: a recursive glob
  for `**/mypy*` (excluding `.venv`, `.git`, `.jj`, `node_modules`) returns no
  matches. There is no `mypy.ini`, `.mypy.ini`, or `setup.cfg`.
- `[tool.ruff.lint]` selects `E, F, I, B, UP`. Ruff is a linter, not a type
  checker; none of these rule families check type consistency across call
  boundaries.
- Static analysis *does* exist and is wired: `ops/import_lint.py` is an
  AST-based import-graph firewall, asserted in `tests/test_import_firewall.py`.
  Its module docstring states the design intent explicitly — the runtime egress
  guard is promoted to a **static tier**, "provable without running, by reading
  the AST," as the discharge the formal-properties catalog asks of I2.

The last point is the sharp one. The project already accepts, implements, and
depends on the argument that a runtime invariant should be promoted to a static
proof over the AST. That argument was applied to the import graph (I2) and to
no other invariant. The type system is the general instrument for exactly that
promotion, and it is absent.

## Why it matters

Two of the three invariants slated for lightweight TLA+/Alloy + Hypothesis
treatment — **label monotonicity** and **capability non-amplification** — have
static shadows a type checker enforces continuously, at authorship time, at zero
runtime cost (companion note §2.4). Those shadows are currently unenforced.

Consequently every builder session mutates `core/` under a weaker code-plane
guarantee than the three-plane security composition assumes. The gap is not
theoretical: it is the difference between an invariant the machine checks on
every run and one that holds because reviewers were attentive.

Note also the asymmetry in what the sealed core already proves. `import_lint`
guarantees the core cannot *name* a networked zone. Nothing guarantees the core's
own interfaces are mutually consistent — a weaker property, checkable by cheaper
means, currently unchecked.

## Re-entry condition

Not parked; no re-entry condition applies. The finding is actionable now and
routes to the companion design note, whose B-items carry the work and the
falsifiers.

## Routing

`design` → orchestrator. This is a design-changing `discovery`: it proposes
`docs/design-notes/type-system-as-core-audit.md` as a conservative extension of
`security-planes.md` (supplying the enforcement mechanism its code plane names
but does not provide), warrant-linked to this finding. On acceptance of that
note this finding flips to `promoted` (§11).

The finding does **not** by itself license a build plan. It licenses the note;
the note's V-items and B-items license the plan.
