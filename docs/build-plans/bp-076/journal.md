# bp-076 — journal

## 2026-07-19 — minted at graduation (orchestrator, session-36, o@h)

Graduated from `dn-ouroboros-principal` (ratified `216623b`) — the trust-boundary
companion to bp-075's mechanical exhaust lane. Owner bumped the session to
opus@high for this one specifically (it touches load-bearing infra and a trust
boundary).

Grounding done at graduation (§3): the launchd control surface is hardcoded
`gui/{getuid}` across `launcher.py` (`:110-121`) behind an already-injectable
runner (`test_lifecycle_control.py` uses a fake) — so domain is parameterizable,
not a rewrite. The lifecycle control tests pin the exact gui incantations
(`:61,67`) → CARRIED in write_scope per the findings-0071/0072 retrofit rule.

The crux resolved at graduation (§3 Q2): a system LaunchDaemon can't be
controlled by a non-root user, so control commands run via `sudo launchctl
system/<label>` — consistent with the note's own threat model (§2: sudo is the
sanctioned, deliberate, logged owner-escape). Pinned inline so the builder
doesn't invent a control model; a deeper objection is a stop-and-raise.

The self-configuring ratchet (§3 Q4): `stat(vault).st_uid == uid(ouroboros)`
gates skip-vs-enforce, so the ownership flip IS the migration's acceptance and
the vanishing skip is the witness — no manual test flip (finding-0105 shape).

BUILDER DISCIPLINE (loud): this build performs NO migration step. Every mutating
act is owner-run from Item 4's runbook. The builder writes code + docs + tests
that SUPPORT and PROVE the move; it never creates a user, chowns, or touches
launchd/keychain/Syncthing. Est. 220k (a big, careful plan — larger than a
papercut; if it doesn't fit one session, file spec-defect and re-graduate).

Status: `proposed`. Awaiting the owner's `palace bless bp-076` + hand commit.

## 2026-07-20 — RE-GRADUATION REQUIRED before build (delegated design agent, fable)

`dn-ouroboros-principal` — the note this plan was graduated from — is being
superseded by `dn-plane-principals` (draft filed 2026-07-20, warrant
finding-0116): the owner generalized the 2-principal model to FOUR users, one
per plane (`ascalva` human / `ouroboros-work` workflow / `ouroboros` core /
`ouroboros-edge` network-facing, created now as forward-provision).

**This plan must be re-graduated against `dn-plane-principals` BEFORE it
builds** — its runbook/verifier/ratchet were sized for 2 users and would, as
graduated, chown exhaust `ouroboros`-write-only and silently break report
delivery (exactly finding-0116). Material deltas the re-graduation carries:

1. Four role accounts, not one; shared group `palace` (ascalva + ouroboros-work).
2. `exhaust/reports/` owned by `ouroboros-work` (finding-0116 resolution);
   system-emission subdirs stay `ouroboros`.
3. Cockpit launches the orchestrator via `sudo -u ouroboros-work -H claude …`
   (cockpit.sh:73 changes); builders inherit the uid; sudoers NOPASSWD
   descending grant; §3 must ground Claude Code's credential storage
   (keychain vs apiKeyHelper/env) for the service user — the sharpest edge.
4. pf anchor: block off-host egress for uid `ouroboros` (+ `pass on lo0` for
   local model serving — verify against the running daemon); edge-only sockets.
5. Shared-repo mechanics: setgid dirs, `core.sharedRepository=group`, umask 002.
6. `data/` runtime substrate ownership (daemon writes inside the repo tree —
   chown vs relocate; new grounding item).
7. Ambassador relocation to `ouroboros-edge` via the handoff-dir airlock
   (launcher.py:150,227-228) — or explicit deferral; the USER is created
   unconditionally either way.
8. Ratchets extended per-plane (vault unreadable from work AND edge postures;
   egress refused from core posture); the stat().st_uid skip-gate carries over
   per-path.

Not touched here: plan.md (re-graduation is the orchestrator's; blessing the
owner's). This entry only parks the build with its re-entry condition.
