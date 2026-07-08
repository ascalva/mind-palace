---
type: finding
id: finding-0020
status: open
created: 2026-07-06
updated: 2026-07-06
links:
  - CHANGELOG.md
  - README.md
  - docs/archive/PROGRESS-phases-0-10.md
  - docs/audits/corpus-state-audit-2026-07-verification.md
ftype: discovery
origin_plan: orchestrator
route: orchestrator
resolution: null
---

# finding-0020 — The tracking record overclaims operational reality: built/deployed subsystems are logged as "complete / live / wired"

## What
The terse tracking surfaces — the root `CHANGELOG.md` one-liners, the Phase-10 /
`docs/archive/PROGRESS-phases-0-10.md` roll-up, `README.md`, and several stale status
lines — log **built-but-unwired** subsystems as "complete / live / wired," conflating
*built/deployed* with *wired-into-the-live-loop*. Code-verified instances (2026-07-06
verification):

- **"Phase 8 Complete" / "research airlock (live)"** (`CHANGELOG.md:58`,
  `archive:1015`) — but the airlock has no live driver (finding-0019).
- **"Completed Vault Production Setup … to access cloud"** (`CHANGELOG.md:39`) — but
  nothing on the daemon consumes Vault, and the bridge itself still uses a static SSO
  profile, not Vault-minted creds (`archive:855`: "wiring it to mint from Vault … is
  Phase 5 work, not done here").
- **"WIRED ceiling ε = SENSING"** (`docs/PROGRESS.md:1085-1087`) — but no effector is
  wired at any tier (finding-0011).
- **Drift gauge A1 "the keystone … COMPLETE"** (`docs/PROGRESS.md:78`) — but the gauge
  is inert live; only the boot-time Constitution-fingerprint conjunct runs
  (finding-0015).
- **"The base build (Phases 0–10) is complete and running"** (`README.md:32`) — true of
  the build, but `palace start` drives exactly six job kinds; the whole "advanced layer"
  (airlock driver, effectors, self-mod loop, Vault runtime-auth consumer, correlator,
  `dream_v2`, attestation *signing*) is built-behind-flag or deployed-but-undriven.

The current `docs/PROGRESS.md` is itself honest and self-correcting (it concedes most of
these — e.g. `:267` "no live driver", the WIRING-AUDIT sections). The overclaim lives in
the terse CHANGELOG/README summaries and the archive Phase-10 roll-up.

## Why it matters
A reader (human or agent) relying on the CHANGELOG/README to know "what is live" will
materially overestimate the running system. Across the corpus, "complete" consistently
means *built/deployed*, not *wired* — but the summary surfaces do not carry that
distinction, so the gap is invisible unless one traces call chains in code.

## Re-entry condition
The tracking headline (README / CHANGELOG summary, or a dedicated "wiring board") should
carry an explicit **built vs. deployed vs. wired** distinction — which subsystems run on
`palace start`, which are built-behind-a-flag, which are deployed-but-undriven. Owner
rules on whether to annotate the summaries or maintain a wiring board.

## Routing
`discovery` (direction) → orchestrator. A tracking-record accuracy defect; the same
class as findings 0011 / 0015, generalized. Owner decides the annotation form.
