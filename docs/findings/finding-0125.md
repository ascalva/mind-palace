---
type: finding
id: finding-0125
status: routed
created: 2026-07-20
updated: 2026-07-26
links:
  - docs/design-notes/plane-principals.md         # the four-plane model; §3.2 workflow principal
  - docs/findings/finding-0120.md                 # the setup-token OAuth resolution that caused this
  - scripts/orchestrator-launch.sh                # :24,:29,:59 — launches the role session under the token
  - .claude/state/resume-brief.md                 # MODEL TIER: "fable ONLY for design/gates"
re_entry: >
  An owner decision on how the workflow plane accesses the fable tier: (a) HYBRID — keep
  ouroboros-work as the default/build principal, launch the orchestrator pane as ascalva for the
  (minority) fable design/gate sessions; (b) FULL REVERT — run the orchestrator as ascalva again,
  giving up the plane's model-isolation win; (c) FIX THE AUTH — find a headless credential for the
  role account that carries fable entitlement (needs investigation; may not be possible with
  `claude setup-token`). Recommendation: (a). Blocking: any fable design/gate pass under the role
  account (e.g. the inner/outer-core graduation, dn-decision-routing) is stalled until resolved.
ftype: direction
origin_plan: null
route: orchestrator
resolution: routed → owner (oq-0042); primary question answered by the hybrid, two residuals live
---

# The workflow-plane `setup-token` auth silently removes fable-tier access — design/gate passes can't run on fable under `ouroboros-work`

> **Triage 2026-07-26 (session-52) — batched to `oq-0042`.** The chosen hybrid is fully built and the
> default swapped (`scripts/orchestrator-launch.sh:35` `PLANE="${PLANE:-ascalva}"`, banner citing this
> finding at `:86`), and fable access via the human plane is confirmed in practice
> (`dn-integrator-densification:32`, a real Fable pass under the new default). So the **primary**
> question is answered. Two residuals are live:
> 1. option 3 (a fable-capable *headless* credential) is undecided — so the workflow-plane isolation
>    bp-078 delivered is **dormant by default**, one flag away (`PLANE=workflow`);
> 2. **ratified** `dn-plane-principals:160` still asserts *"the interactive orchestrator session runs
>    as `ouroboros-work`"*, which the tree no longer does — unannotated, and `grep finding-0125`
>    across `docs/design-notes/` returns zero hits.

## What
Surfaced 2026-07-20 (session-38, right after the workflow plane went live). The orchestrator pane now
runs as the role account **`ouroboros-work`**, authenticated headlessly via `CLAUDE_CODE_OAUTH_TOKEN`
from `claude setup-token` (the finding-0120 resolution), launched `claude --model opus[1m]`. In this
session **`/model` does not list the fable model** (Opus/Sonnet/Haiku are present). Empirically
confirmed by the owner: the SAME account via a normal interactive `/login` session as **`ascalva`**
DOES list fable. So the delta is the **auth path**, not a plan/rollout change — the `setup-token`
credential carries a narrower model entitlement than the interactive subscription login.

## Why it matters
This project's model-tier discipline reserves **fable for design/gate work specifically** (resume
brief MODEL TIER; "fable ONLY for design/gates — PRE-TASK FLAG"). The workflow-plane migration —
whose whole point was to run agents as a constrained principal — **silently dropped the tier the
design work depends on.** Concretely:
- Any fable design/gate pass driven from the role-account orchestrator (the **inner/outer-core**
  graduation into `dn-inner-outer-core`, `dn-decision-routing`, future gate passes) cannot get fable.
- **Prior "fable" subagents likely ran on Opus, not fable.** A subagent cannot exceed the main
  session's model access; the Agent-tool `model: "fable"` enum is accepted-values, not a capability
  grant. This affects at least the CORE-plane secret-bootstrap design pass
  (`dn-headless-daemon-secret-bootstrap`, drafted this session) — it should be re-examined as an
  Opus product, not the fable treatment it was reported as.

## Root cause
finding-0120 resolved the *auth* question (keychain dead-end → `setup-token` OAuth, which correctly
KEEPS subscription billing) but did not price in a **capability** cost: the resulting headless token
exposes a smaller model set than an interactive login. The two credentials are not equivalent in
model entitlement. This was not caught because the migration verified auth (a commit signs, a prompt
answers `ok`) but never verified *which models* the role session could reach.

## Options (an owner decision — routed to orchestrator)
1. **HYBRID (recommended).** Keep `ouroboros-work` as the default + build principal (the bulk of
   sessions, where the isolation win matters). Launch the orchestrator pane as **ascalva** for the
   minority fable design/gate sessions. Matches the existing tier rule; preserves the plane. An
   ascalva session needs NO wrapper — it has its own login credential (fable) + global git signing.
   Optionally add a `PLANE=ascalva` bypass flag to `orchestrator-launch.sh` for a one-switch flip.
2. **FULL REVERT.** Run the orchestrator as ascalva again — regains fable, gives up the plane's
   "even an ascalva-login process is a different principal" model isolation. Loses today's win.
3. **FIX THE AUTH.** Find a headless credential for the role account that carries fable entitlement.
   Needs investigation; may be a hard `setup-token` limitation. Highest-effort, best-if-possible.

## Recommendation
Option 1 (hybrid). It costs nothing structural, keeps the workflow plane for what it's good at, and
routes fable work to ascalva — which is exactly where the tier discipline already says design/gate
work is deliberate and owner-adjacent. Amends `dn-plane-principals` §3.2's implicit assumption that
the role principal is model-equivalent to the human login.

## Update — 2026-07-20 (owner chose the hybrid; toggle BUILT)
Owner: "let's make it a toggle, in case we can get a better workflow in the future." Built a `PLANE`
toggle: `scripts/orchestrator-launch.sh` gains a `PLANE=ascalva` branch (plain login launch as the
invoking user; no OAuth-token/askpass injection — the login has its own credential + global signing),
and `scripts/cockpit.sh` threads it (`PLANE=ascalva scripts/cockpit.sh` launches the orchestrator pane
in fable mode, pinning NO model so it inherits the global fable default). Default stays `workflow`
(ouroboros-work, isolated). Routing verified with stubbed `claude`/`sudo`; shellcheck clean.
**DEFAULT SWAPPED (owner, same session):** "swap the default, ascalva is the default, not sure how
often I will use ouroboros-work if fable isn't working there." So `PLANE` now defaults to **ascalva**
(human login, fable) and **`PLANE=workflow` is the opt-in** for the isolated ouroboros-work principal.
Consequence to name honestly: the workflow-plane isolation (bp-078 — the orchestrator AND every builder
it spawns by uid inheritance run as the constrained role account) is now **DORMANT by default**; it is
one flag away but no longer the common path. This is a deliberate operational deviation from
`dn-plane-principals` §3.2 (which assumes the orchestrator runs as ouroboros-work) — warranted by the
fable gap, and it makes **option 3 (get fable working under the role account)** the real fix that would
let the isolated plane become the default again. Adopt on the next cockpit restart (plain
`scripts/cockpit.sh` now = ascalva). Status stays `open` until the owner confirms a fable session
launches and until option 3 is decided.
**Residual (separate follow-up):** prior "fable" subagents ran on Opus — re-examine
`dn-headless-daemon-secret-bootstrap` (the CORE-plane secret-bootstrap draft) as an Opus product, not
the fable treatment it was reported as, before ratifying it. Track C left open: `option 3 — fix the
auth so the role account itself gets fable` remains the "better workflow in the future" the toggle
hedges for.
