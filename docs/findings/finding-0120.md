---
type: finding
id: finding-0120
status: open
created: 2026-07-20
updated: 2026-07-20
links:
  - docs/design-notes/plane-principals.md          # §3.2 cost 1 — the credential bootstrap
  - docs/build-plans/bp-078/plan.md                # Q9 (§3), Item 6 STOP-gate, §10, §11
  - docs/runbooks/plane-migration.md               # where the STOP-gate lands
re_entry: null
ftype: direction
origin_plan: bp-078
route: orchestrator
resolution: null
---

# Q9 spike — the Claude Code credential for `ouroboros-work` can only be settled by an owner-run bootstrap, not by an agent

## What
bp-078 §3 Q9 designates the storage + reload behavior of Claude Code's OAuth
credential under `sudo -u ouroboros-work -H` a legitimate **spike**: the code does
not settle where the credential lands, and the runbook cannot pin the mitigation
without an empirical observation.

During the build I attempted the honest, non-secret grounding the plan invites —
observe *whether* `~/.claude/.credentials.json` exists and *whether* a
`Claude Code-credentials` Keychain item is present (metadata only, no secret value
read). The Claude Code auto-mode guardrail **denied** the probe as credential-store
scanning (non-negotiable #10, "secrets are never read by a model / logged"). I did
not work around it — and the denial is itself the load-bearing answer:

> A service user's credential store is not agent-reachable, by design. The empirical
> bootstrap — authenticate `claude` once as `ouroboros-work`, then observe where the
> credential lands and whether the cockpit pane relaunch re-reads it with the login
> keychain **locked** — is inherently an **owner-run** step. No agent can (or should)
> perform or verify it.

What I *can* ground from documented behavior (Claude Code on macOS, knowledge cutoff
2026-01): the OAuth credential is kept in the **login Keychain** (generic-password
service `Claude Code-credentials`) or, on Keychain-less platforms, in
`~/.claude/.credentials.json`; Claude Code also honors an **`apiKeyHelper`** script
and the **`ANTHROPIC_API_KEY`** environment variable for non-interactive auth. This
is enough to pin the runbook's mitigation *order* but NOT to assert which one holds
under a locked role-account keychain — that is the empirical unknown.

## Why it matters
This is the sharpest recurring-friction risk of the whole plane migration (§3.2
cost 1): if the `ouroboros-work` keychain is locked at cockpit-pane launch, the
orchestrator agent fails to authenticate and the daily flow breaks. The runbook
must therefore carry a **BOOTSTRAP-AND-VERIFY STOP-gate** with a decided mitigation,
and the decision needs the owner's live observation. Item 6's runbook pins the gate
with the §3.2 preference order — (a) a `security unlock-keychain -u ouroboros-work …`
line in the cockpit wrapper before the `sudo -u ouroboros-work -H claude …` launch,
else (b) an `apiKeyHelper` / `ANTHROPIC_API_KEY` path that bypasses the keychain —
but which branch is taken is resolved only at the owner's bootstrap.

## Re-entry condition
The owner performs the Item 6 credential-bootstrap STOP-gate during the live
migration: authenticate `claude` once as `ouroboros-work`, lock the keychain, relaunch
the cockpit pane, and record which mitigation (a or b) makes the relaunch succeed.
That observation resolves this finding (and, if it contradicts BOTH mitigations, is
the §10 stop-and-raise that re-opens the design, not a path for an agent to invent).

## Routing
`direction` → the orchestrator. The build delivered everything authoring can: the
runbook STOP-gate, the mitigation order, and the verifier's credential-resolution
check (which degrades to a skip until the owner has bootstrapped). No code change can
settle it; the empirical bootstrap is the owner's. Parked in bp-078 §11.
