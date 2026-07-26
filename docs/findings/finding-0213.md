---
type: finding
id: finding-0213
status: routed
created: 2026-07-26
updated: 2026-07-26
links:
  - scripts/verify_planes.py                          # check_pf_anchor — the false green
  - ops/network/ouroboros-egress.pf.conf              # the header that conflates persistence with evaluation
  - docs/design-notes/plane-principals.md             # §3.4/§3.5 — the anchor's design home
  - docs/findings/finding-0190.md                     # the chain this anchor is the last guard against
  - docs/findings/finding-0011.md                     # the same defect class: a record claiming an unwired guard
  - docs/inbox/owner-questions.md                     # oq-0046 — the ruling being enacted when this surfaced
ftype: spec-fidelity
origin_plan: orchestrator
route: orchestrator
resolution: null
---

# `check_pf_anchor` reports PASS on a pf anchor that enforces nothing — three independent false-green paths

## What

Surfaced live while the owner enacted oq-0046 (loading the core-egress pf anchor). `check_pf_anchor`
(`scripts/verify_planes.py:270-291`) decides its verdict **entirely** from
`pfctl -a mind-palace/ouroboros -sr` (`:108-112`) — i.e. from whether the sub-anchor *contains* the
two expected rules, in the right order. Rules can be **loaded and listed while enforcing nothing**, so
there are three states in which the check reports **PASS** and the guarantee is absent:

1. **⚑ pf is DISABLED.** Measured on this machine right now: `sudo pfctl -s info` → `Status: Disabled`.
   macOS ships pf off and says so in its own config: *"PF will not be automatically enabled, however.
   Instead, each component which utilizes PF is responsible for enabling and disabling PF via -E and
   -X"* (`/etc/pf.conf`). A loaded anchor under a disabled pf blocks nothing, and `-sr` still lists it.
2. **The anchor is loaded but not REFERENCED.** pf evaluates a sub-anchor only where the main ruleset
   dispatches to it. `/etc/pf.conf` on this machine is stock — it carries the `com.apple` anchor points
   and **no `mind-palace` lines** (verified). So `pfctl -a mind-palace/ouroboros -f …` alone produces
   rules that are present, listable, and never consulted.
3. **pf is enabled now but not after reboot.** `/etc/pf.conf` is auto-loaded at boot; **pf is not
   auto-enabled**. So `pfctl -E` today, reboot tomorrow, and the check still says PASS while the guard
   is gone — the worst of the three, because nothing changed in the repo to explain it.

The check's own docstring shows the author reasoned about exactly this hazard and still missed the
axis: *"`pfctl -sr` needs root — unreadable ⇒ SKIP (**not a false green**)"* (`:272-273`). Unreadability
was handled; unenforcement was not.

**Secondary, and how this was found — a doc defect in the same area.**
`ops/network/ouroboros-egress.pf.conf`'s header presents the two `/etc/pf.conf` lines as being for
persistence: *"and a loader line is added to /etc/pf.conf so it survives a reload / reboot"*. That
undersells them. They are what makes the anchor **evaluated at all** (path 2 above). A reader who
performs only the documented `INSTALL` first step — `pfctl -a mind-palace/ouroboros -f …` — and then
the documented `VERIFY` step — `pfctl -a mind-palace/ouroboros -sr`, which *"shows exactly the two
rules below"* — gets a green verification for a guard that is doing nothing. The document walks the
reader into the false green.

## Why it matters

This is the **finding-0011 class landing on the one unconditional guard in the stack.** Non-negotiable
#1 demands structural enforcement, and the pf anchor is the only mechanism in the core-egress story
that does not depend on Python: `hvac` being uninstalled is a packaging accident, and
`core/sealing.py:16-17` concedes that a native extension bypasses its socket monkeypatch. finding-0190
names the anchor as the last line. So a checker that greens it while it is inert converts *"the one
guard that cannot be bypassed by a bug"* into *"a guard we believe in because a script said so."*

Direction of the error is **unsafe**: it over-reports protection. That is the opposite of finding-0011,
whose inaccuracy was at least conservative.

It also lands at the worst moment — the owner is enacting oq-0046 *now*, on the strength of a check
that would have confirmed success regardless.

Mitigating today, and only by luck: nothing runs as the `ouroboros` uid yet (no
`/Library/LaunchDaemons/com.mind-palace.*`; the daemon runs as `ascalva`), so the anchor is a no-op in
every state. The exposure arrives with oq-0041's core-plane migration — i.e. exactly when the check
starts being load-bearing.

## Re-entry condition

`check_pf_anchor` verifies **enforcement**, not presence. Three additive probes, cheap and all
read-only:

- **pf status** — `pfctl -s info` must report `Status: Enabled`, else FAIL (not SKIP: a disabled pf is
  a positive disproof, not an unreadable one).
- **anchor reachability** — the main ruleset (`pfctl -sr`) must contain a dispatch to
  `mind-palace/ouroboros`, else FAIL.
- **boot persistence** — `/etc/pf.conf` must carry both the `anchor` and `load anchor` lines; and
  because pf still will not auto-enable, either a boot-time enabler exists or the check reports the
  residual honestly rather than silently.

Plus the doc fix: the conf header states that the `/etc/pf.conf` lines are required for the anchor to
be **evaluated**, not merely to persist, and its `VERIFY` block includes the status and dispatch checks
so the documented happy path cannot produce a false green.

Closes when a disabled pf, an unreferenced anchor, and a missing loader line each make the check FAIL,
proven by driving all three states.

## Routing

`spec-fidelity` → orchestrator. The verdict-vs-reality gap is the orchestrator's to route, and the fix
spans `scripts/verify_planes.py` plus a doc header — **no plan currently owns either path**, so per
finding-0209 this is a fresh orphan the moment it is filed. It needs a small scoped plan, not a
hand-off note. Pair it with oq-0046's enactment: the owner is loading the anchor now, and the check
should be able to tell him whether it worked.
