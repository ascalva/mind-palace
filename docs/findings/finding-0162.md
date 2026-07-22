---
type: finding
id: finding-0162
status: routed           # open → routed → resolved | promoted
created: 2026-07-22
updated: 2026-07-22
links:
  - config/defaults.toml                               # the misnamed file
  - core/kernel/config/loader.py                       # _DEFAULTS constant + the overlay chain
  - docs/findings/finding-0161.md                      # the thread this continues (defaults ≠ neutral)
ftype: direction         # a config-architecture / naming call — owner's
origin_plan: orchestrator
route: orchestrator      # owner input required (naming + whether the framework/instance split is real)
resolution: null
---

# `defaults.toml` is misnamed — it instantiates Ouroboros; rename to `ouroboros.toml`?

## What

Owner observation (2026-07-22, continuing finding-0161): `config/defaults.toml` does not hold
neutral framework *defaults* — it holds the concrete values that **instantiate this Ouroboros**:
`[planes]` names the `/var/ouroboros*` principal accounts, the model lineup is this box's M2 Max
(qwen3.5:2b/9b, qwen3.6:27b/35b-a3b), the paths (`~/.mind-palace/*`) and `us-east-1` are this
deployment's. Proposal: **rename `defaults.toml` → `ouroboros.toml`** so the name tells the truth.

## Why it matters

Names encode intent. Calling it "defaults" perpetuates the framework-vs-instance fiction that
finding-0161 already exposed — a would-be neutral base that in reality is Ouroboros's own config.
`ouroboros.toml` makes the layering honest: **ouroboros.toml** = the committed instance config;
**local.toml** = per-machine deltas + security-gated opt-ins; **levers.toml** = the self-mod loop's
machine-tuned knobs. The rename is small; the clarity is not.

## The deeper question it forces (for the owner)

Is the **mind-palace (framework) / Ouroboros (instance)** split ([[ouroboros-naming]]) *real* at the
config layer, or aspirational?
- **If real** — extract two files: a genuine framework-defaults (generic, safe, what a hypothetical
  other instance inherits) and `ouroboros.toml` (this deployment's instantiation, overlaying it).
  More structure; honors reusability that may never be used (YAGNI risk).
- **If aspirational / "this is just Ouroboros"** — collapse the fiction: rename to `ouroboros.toml`
  and own that this repo's committed config IS Ouroboros's. A fresh third-party instance would fork
  it to their own `<name>.toml`. Simpler; matches reality today.
The owner's lean (finding-0161 + this) points at the second. Recorded, not decided.

## Blast radius (why it's a deliberate refactor, not a drive-by)

`git mv` + update: `core/kernel/config/loader.py` `_DEFAULTS` (+ any `config/loader.py` shim), the
new `test_code_ingest_default_on` path load, `test_config_split.py` / other tests referencing the
name, doc/comment references (runbook, design notes), and a full green-gate pass. The loader is what
the **daemon reads at startup** — a rename that breaks config resolution takes the whole daemon down,
not just one feature.

## Re-entry condition / recommended sequencing

**Do NOT bundle this with the imminent code-ingest deploy.** That deploy already couples the φ_code
1.1.0 re-projection + the first code seed; adding a startup-config rename multiplies the failure
surface (a rename bug = daemon won't start). Recommended order: (1) deploy code-ingest, confirm it
runs + seeds; (2) THEN do the rename as an isolated change — full test pass + a dry `palace status`
(config loads) before it goes near a deploy. Until then: status quo (`defaults.toml`) stands; nothing
is blocked. Owner decides timing + which of the two structures above.

## Routing

`direction` (config-architecture + naming) → **orchestrator → owner**. A rename-only ruling is a
mechanical refactor (own plan/session); a "split framework vs instance" ruling is a small design
note. Warrant-link whichever here.
