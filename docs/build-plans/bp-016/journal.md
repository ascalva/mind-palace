# BP-016 — Build journal

Alive while the plan is `in-progress`; sealed by `/triage` on completion.
Fresh-agent test (§9): a session given only `plan.md` + this journal + the
write-scope files must continue without re-asking anything already answered.

---

## Markers

## Owner-step ledger (Item 11 — maintained from day one)

| Step | Status | Re-entry |
|---|---|---|
| (a) fine-grained PAT → Keychain `github-api` | OWED | authenticated polling + dispatch |
| (b) origin re-point + `git push origin --tags` + parity check | OWED | gates Item 10 |
| (c) mirror reversal/retirement (GitLab side) | OWED | GitLab-lane deletion (note parked #3) |
| (d) secret-scanning + push-protection toggles | OWED | — (any time) |

SSH key setup is DONE (verified 2026-07-11): `~/.ssh/id_ed25519.pub` registered on GitHub
as both Authentication key (`ssh -T git@github.com` authenticates) and Signing key
(signed history renders Verified on the mirror).
