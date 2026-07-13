---
type: finding
id: finding-0067
status: routed
created: 2026-07-13
updated: 2026-07-13
links:
  - docs/findings/finding-0066.md
  - ops/lifecycle/launcher.py
ftype: direction
origin_plan: orchestrator
route: orchestrator
resolution: null
---

# What user/role should own the running daemon? (privilege model — the owner's capture request)

## What

Surfaced by the bp-026 migration (owner asked to capture it, 2026-07-13). Today the daemon is a
**user-level LaunchAgent** (`~/Library/LaunchAgents/com.mind-palace.palace.plist`, `gui/$(uid)`
domain) running as the **owner's own user** — which is why daemon control needs no `sudo`. The
question: should it stay that way, run under `sudo`/root, or run as a **dedicated low-privilege
OS service user** the owner controls via a privileged path (deploy process unchanged)?

## The read (from the 2026-07-13 discussion)

- **`sudo`/root for the daemon itself is wrong** — backwards from least-privilege. The daemon is
  the *sealed core*; it should hold **less** privilege than the owner, not more. Root would be a
  regression (it carries vault + Keychain access; a bug in it as root is catastrophic).
- **A dedicated low-privilege service user (`_mindpalace`) is the constitutionally-aligned
  direction.** It turns the "sealed core" boundary from a *code convention* into an
  **OS-enforced** one — exactly what Invariant 1 asks ("enforce structurally, not by
  convention"). A daemon compromise is then contained to the service user's scope (its `data/`,
  its vault, its scoped Keychain items) instead of the owner's whole account.
- **The real trade-off:** a service-user daemon typically becomes a *system-domain*
  LaunchDaemon, and then start/stop needs elevated privilege (`sudo`) — deliberately, a gate on
  casually stopping a privileged service. So: user-agent (no sudo, owner controls, weaker
  isolation) vs service-user daemon (privileged control plane, OS-enforced isolation). The
  **deploy process stays conceptually the same** (ship code → restart); only the restart moves
  to the privileged control plane.
- **macOS friction (why this is a design pass, not a quick change):** Keychain access from a
  non-login service account, the vault path under `~/.mind-palace`, and the GUI-domain features
  (the vault file watcher) all need rework to move off the owner's user.

## Why it matters

The sealed-core boundary (Invariant 1) is currently enforced by code + store separation, not by
the OS. Moving the daemon to a least-privilege service user would make that boundary real at the
OS layer — a genuine hardening aligned with the constitution's "structural, not convention"
ethos. For a single-user personal machine the current user-agent is a reasonable pragmatic
baseline; the service-user model is a deliberate improvement to weigh, not an obvious win.

## Re-entry condition

Design-note-worthy (it touches Invariant 1). The next /triage or a `/capture` opens the design
question: user-agent vs dedicated service user vs system daemon; the Keychain/vault/GUI-domain
rework; and the privileged control plane (folding in finding-0066's `palace down/up`). Not
urgent; the current model is safe on a single-user machine. On owner appetite → a design note.

## Routing

`direction` → orchestrator (security architecture; the owner's explicit capture). Non-blocking.
