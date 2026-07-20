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
