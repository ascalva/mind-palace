---
type: finding
id: finding-0161
status: routed           # open → routed → resolved | promoted
created: 2026-07-22
updated: 2026-07-22
links:
  - docs/design-notes/code-ingest-pipeline.md          # §2.7 the default-OFF / owner-visible posture
  - docs/findings/finding-0159.md                      # the ON switch is part of finishing (bp-098)
  - docs/findings/finding-0146.md                      # code is a first-class semantic source
  - config/defaults.toml                               # where the shipped default lives
  - config/local.toml                                  # where this instance opts in today
ftype: direction         # a design-default philosophy call — owner's
origin_plan: orchestrator
route: orchestrator      # → owner-questions.md (oq-0034); owner input required
resolution: null
---

# Should code-ingest be ON by default (defaults.toml), not opt-in per-instance (local.toml)?

## What

Today `[code_ingest].enabled` ships **false** in `config/defaults.toml`; this Mac opts in via
`config/local.toml` (`enabled = true`, 2026-07-22), the same shape as `[secrets]`/`[backup]`. The
owner questions that placement (2026-07-22): **maybe code-ingest should default ON for mind-palace
itself**, because:

- **It is NOT a security issue.** `secrets`/`backup` gate real security/credential surfaces, so
  off-by-default is a firewall. Code-ingest's gate is mere fail-safe conservatism (don't auto-run
  a heavy embed) — a resource/politeness default, not a safety one. So the "ship OFF" reflex that
  bp-098/finding-0159 applied uniformly may be miscalibrated for THIS capability.
- **The Ouroboros is about self-consumption.** The founding frame ([[ouroboros-naming]]) is a
  system that mines/consumes itself — the palace as a self-map ("mining my own brain",
  [[owner-background-self-mapping]]). Code is a first-class semantic source (finding-0146). A
  system whose whole point is to eat its own tail arguably SHOULD ingest its own code by default,
  not as a per-machine opt-in. "On" would be the philosophically native posture.

## Why it matters

The default encodes what mind-palace *is*. If the Ouroboros self-consumption thesis is load-bearing,
burying code-ingest behind a per-instance opt-in understates it. Conversely, a wrong default is
heavy and silent (finding-0150's lesson): flipping it in `defaults.toml` changes behavior for
*every* consumer of the default, not just this Mac.

## The crux to deliberate — FRAMEWORK default vs INSTANCE posture

`defaults.toml` is the **framework**'s shipped default; `local.toml` is **this instance**'s posture.
[[ouroboros-naming]] already draws exactly this line: *mind-palace = the framework; the LIVE
system (daemon + evolving corpus) = Ouroboros.* The self-consumption philosophy is an **instance**
property (Ouroboros, this deployment) — which `local.toml` already expresses. Flipping
`defaults.toml` asserts it for **every clone and CI run**, which is a different (stronger) claim.

Technical considerations for the deliberation (recorded neutrally, both directions):
- **Default-ON auto-seeds on first housekeeping.** The `enabled` gate drives the INCREMENTAL sync;
  on a cold store "incremental" embeds everything (= the full seed). So `defaults.toml` ON means a
  fresh clone / CI would fire a heavy first embed unbidden at its first housekeeping tick — the
  exact heavy-op-from-a-flag the §2.7 owner-visible-seed rule was written to avoid. (The deliberate
  `palace code-seed` stays separate either way; the question is only the housekeeping gate.)
- **CI / fresh clones usually can't and shouldn't.** No Ollama in CI, no daemon; a default that
  assumes a live embedder + running daemon is wrong for the framework's non-instance consumers.
- **Middle paths exist** (for the owner to weigh, not decide here): (a) keep `defaults.toml` OFF but
  make the LIVE-instance default ON explicit/documented (status quo, just named); (b) default ON but
  keep the first SEED deliberate and gate the housekeeping auto-embed on "daemon + embedder present"
  (default-on-when-runnable); (c) a distinct "this is the Ouroboros instance" marker that flips a
  set of instance-native defaults together, code-ingest among them.

## Re-entry condition

Owner deliberates (oq-0034). Until answered: **status quo stands** — `defaults.toml` OFF, this
instance ON via `local.toml` (already live). No behavior change is blocked on this; the deploy +
seed proceed under the current local.toml opt-in. If the owner rules default-ON, that is a
`defaults.toml` edit (framework default) warrant-linked here, with the auto-seed-on-cold-store
consideration addressed (likely middle-path (b)).

## Routing

`direction` (design-default philosophy) → **orchestrator → owner-questions.md (oq-0034)**. Owner's
call; not a build or a security fix. A default-ON ruling promotes to a dn-code-ingest-pipeline §2.7
amendment (the owner-visible-seed rule would need the cold-store auto-embed caveat).
